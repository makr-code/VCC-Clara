#!/usr/bin/env python3
"""Unified Adapter Training Script (LoRA / QLoRA / DoRA placeholder)

Ziel:
- Vereinheitlichtes Interface für Adapter-Training
- Abstraktion über bestehende `train_lora.py` Logik
- Erweiterbar für QLoRA (4/8-bit) und zukünftige Varianten

Beispielaufrufe:

LoRA:
  python scripts/train_adapter.py \
    --base-model mistralai/Mistral-7B-Instruct-v0.2 \
    --method lora --rank 16 \
    --dataset data/training_batches/steuer_202509.jsonl \
    --out-dir models/adapters/steuerrecht/lora-r16-v1

QLoRA (4bit):
  python scripts/train_adapter.py \
    --base-model mistralai/Mistral-7B-Instruct-v0.2 \
    --method qlora --rank 32 --quantization 4bit \
    --dataset data/training_batches/steuer_202509.jsonl \
    --out-dir models/adapters/steuerrecht/qlora-r32-v1

TODO / Erweiterungen:
- DoRA Implementation (Rank-Decomposition Variation)
- Evaluation Hook nach Training
- Registry Auto-Update (write entry in metadata/adapter_registry.json)
- HF Hub Push Option
"""
from __future__ import annotations
import argparse
import os
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

import torch
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling,
)
from datasets import Dataset
from peft import LoraConfig, get_peft_model, TaskType
from src.utils.metrics import get_metrics_exporter

# Lokale Module
import sys
script_dir = Path(__file__).parent
project_root = script_dir.parent
sys.path.insert(0, str(project_root))
try:
    from src.utils.logger import setup_logger
except Exception:
    import logging
    def setup_logger(name: str):
        logging.basicConfig(level=logging.INFO)
        return logging.getLogger(name)

LOGGER = setup_logger(__name__)

# ------------------------- Argument Parsing -------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Unified Adapter Training (LoRA / QLoRA)")
    p.add_argument("--base-model", required=True, help="HF Modellname oder lokaler Pfad")
    p.add_argument("--dataset", required=True, help="Pfad zu JSONL oder Text-Datei")
    p.add_argument("--out-dir", required=True, help="Zielverzeichnis für Adapter")
    p.add_argument("--method", choices=["lora", "qlora", "dora"], default="lora")
    p.add_argument("--rank", type=int, default=16, help="LoRA Rank")
    p.add_argument("--lora-alpha", type=int, default=32)
    p.add_argument("--lora-dropout", type=float, default=0.05)
    p.add_argument("--target-modules", nargs="*", default=["q_proj", "v_proj"],
                   help="Ziel-Module für LoRA Injektion")
    p.add_argument("--max-length", type=int, default=1024)
    p.add_argument("--batch-size", type=int, default=2)
    p.add_argument("--eval-split", type=float, default=0.0)
    p.add_argument("--learning-rate", type=float, default=2e-4)
    p.add_argument("--weight-decay", type=float, default=0.01)
    p.add_argument("--warmup-steps", type=int, default=50)
    p.add_argument("--gradient-accumulation", type=int, default=8)
    p.add_argument("--num-epochs", type=float, default=1.0)
    p.add_argument("--logging-steps", type=int, default=25)
    p.add_argument("--save-steps", type=int, default=200)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--fp16", action="store_true")
    p.add_argument("--bf16", action="store_true")
    p.add_argument("--quantization", choices=["4bit", "8bit", "none"], default="none",
                   help="Quantisierungspfad für QLoRA")
    p.add_argument("--resume", type=str, default=None, help="Checkpoint Pfad")
    p.add_argument("--no-resume", action="store_true")
    p.add_argument("--push-registry", action="store_true", help="Automatisch Registry aktualisieren")
    p.add_argument("--registry-path", type=str, default="metadata/adapter_registry.json")
    p.add_argument("--domain", nargs="+", default=None, help="Domänen-Tags für Registry")
    p.add_argument("--notes", type=str, default=None)
    p.add_argument("--eval-after", action="store_true", help="Nach Training einfache Perplexity Eval")
    return p

# ------------------------- Dataset Handling -------------------------

def load_texts(dataset_path: Path) -> List[str]:
    texts: List[str] = []
    if dataset_path.suffix.lower() == ".jsonl":
        for line in dataset_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                if isinstance(obj, dict) and "text" in obj:
                    texts.append(obj["text"])
            except json.JSONDecodeError:
                continue
    else:
        # Jede Zeile als eigener Eintrag
        texts = [l.strip() for l in dataset_path.read_text(encoding="utf-8").splitlines() if l.strip()]
    return texts

# ------------------------- Tokenisierung -------------------------

def build_dataset(tokenizer, texts: List[str], max_length: int, eval_split: float, seed: int):
    from math import floor
    dataset = Dataset.from_dict({"text": texts})

    def tokenize(batch):
        model_inputs = tokenizer(
            batch["text"],
            truncation=True,
            padding="max_length",
            max_length=max_length,
            return_tensors=None,
        )
        model_inputs["labels"] = model_inputs["input_ids"].copy()
        return model_inputs

    tokenized = dataset.map(tokenize, batched=True, remove_columns=["text"])  # type: ignore

    if eval_split > 0:
        eval_size = max(1, floor(len(tokenized) * eval_split))
        train_size = len(tokenized) - eval_size
        split = tokenized.train_test_split(test_size=eval_size, train_size=train_size, seed=seed)
        return split["train"], split["test"]
    return tokenized, None

# ------------------------- Model Loading -------------------------

def load_model_and_tokenizer(args) -> tuple:
    tokenizer = AutoTokenizer.from_pretrained(args.base_model, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    dtype = torch.float16 if args.fp16 else (torch.bfloat16 if args.bf16 else torch.float32)

    quantization_cfg = None
    load_kwargs = dict(trust_remote_code=True, low_cpu_mem_usage=True)

    if args.method == "qlora" and args.quantization in ("4bit", "8bit"):
        try:
            from transformers import BitsAndBytesConfig  # type: ignore
            quantization_cfg = BitsAndBytesConfig(
                load_in_4bit=args.quantization == "4bit",
                load_in_8bit=args.quantization == "8bit",
                bnb_4bit_compute_dtype=torch.bfloat16 if args.bf16 else torch.float16,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4",
            )
            load_kwargs.update({
                "quantization_config": quantization_cfg,
                "device_map": "auto"
            })
        except ImportError:
            LOGGER.warning("bitsandbytes nicht verfügbar – lade Modell ohne Quantisierung.")
    else:
        load_kwargs.update({
            "torch_dtype": dtype,
            "device_map": "auto" if torch.cuda.is_available() else None
        })

    model = AutoModelForCausalLM.from_pretrained(args.base_model, **load_kwargs)

    lora_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=args.rank,
        lora_alpha=args.lora_alpha,
        lora_dropout=args.lora_dropout,
        target_modules=args.target_modules,
        bias="none",
    )
    model = get_peft_model(model, lora_config)
    return model, tokenizer

# ------------------------- Trainer Wrapper -------------------------

def build_trainer(model, tokenizer, train_ds, eval_ds, args, output_dir: Path) -> Trainer:
    data_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)
    training_args = TrainingArguments(
        output_dir=str(output_dir),
        overwrite_output_dir=True,
        num_train_epochs=args.num_epochs,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        gradient_accumulation_steps=args.gradient_accumulation,
        learning_rate=args.learning_rate,
        weight_decay=args.weight_decay,
        warmup_steps=args.warmup_steps,
        logging_steps=args.logging_steps,
        save_steps=args.save_steps,
        save_total_limit=3,
        seed=args.seed,
        fp16=args.fp16,
        bf16=args.bf16,
        dataloader_pin_memory=False,
        remove_unused_columns=False,
        report_to=None,
        eval_strategy="steps" if eval_ds is not None else "no",
        eval_steps=args.save_steps if eval_ds is not None else None,
    )

    class MemoryOptimizedTrainer(Trainer):
        def training_step(self, model, inputs, num_items_in_batch=None):  # type: ignore
            result = super().training_step(model, inputs, num_items_in_batch)
            if self.state.global_step % 100 == 0:
                torch.cuda.empty_cache()
            return result

    trainer = MemoryOptimizedTrainer(
        model=model,
        args=training_args,
        train_dataset=train_ds,
        eval_dataset=eval_ds,
        data_collator=data_collator,
        processing_class=tokenizer,
    )
    return trainer

# ------------------------- Registry Update -------------------------

def sha256_dir(path: Path) -> str:
    import hashlib
    h = hashlib.sha256()
    for p in sorted(path.rglob("*")):
        if p.is_file():
            h.update(p.name.encode())
            h.update(str(p.stat().st_size).encode())
    return h.hexdigest()

def update_registry(args, output_dir: Path):
    registry_path = Path(args.registry_path)
    if not registry_path.exists():
        LOGGER.warning("Registry Datei nicht gefunden – erstelle neue.")
        registry = {"_schema_version": "0.2.0", "adapters": []}
    else:
        registry = json.loads(registry_path.read_text(encoding="utf-8"))

    base_hash = f"<hash:{args.base_model}>"  # Placeholder – könnte lokaler Directory Hash sein
    adapter_checksum = sha256_dir(output_dir)

    entry = {
        "id": output_dir.name,
        "domain": args.domain or ["unspecified"],
        "method": args.method,
        "rank": args.rank,
        "quantization": None if args.method == "lora" else args.quantization,
        "base_model_hash": base_hash,
        "tokenizer_hash": "<tokenizer-hash>",
        "created": datetime.utcnow().isoformat() + "Z",
        "dataset_ref": args.dataset,
        "metrics": {},
        "license": "internal",
        "adapter_checksum": adapter_checksum,
        "notes": args.notes or "auto-generated entry"
    }

    # Entferne existierenden Eintrag mit gleicher ID
    registry["adapters"] = [a for a in registry.get("adapters", []) if a.get("id") != entry["id"]]
    registry["adapters"].append(entry)

    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(json.dumps(registry, indent=2, ensure_ascii=False), encoding="utf-8")
    LOGGER.info(f"Registry aktualisiert: {registry_path}")

# ------------------------- Evaluation (Perplexity Light) -------------------------

def quick_perplexity(model, tokenizer, eval_ds) -> Optional[float]:
    if eval_ds is None or len(eval_ds) == 0:
        return None
    model.eval()
    import math
    losses = []
    for batch in eval_ds.select(range(min(32, len(eval_ds)))):  # Mini Sample
        with torch.no_grad():
            inputs = {"input_ids": torch.tensor([batch["input_ids"]]).to(model.device)}
            labels = inputs["input_ids"].clone()
            out = model(**inputs, labels=labels)
            losses.append(out.loss.item())
    if not losses:
        return None
    return math.exp(sum(losses) / len(losses))

# ------------------------- Main Flow -------------------------

def main():
    parser = build_parser()
    parser.add_argument("--metrics-http", action="store_true", help="Startet einfachen Prometheus Endpoint (Port 9310)")
    args = parser.parse_args()

    output_dir = Path(args.out_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    LOGGER.info("Lade Datensätze...")
    texts = load_texts(Path(args.dataset))
    train_ds, eval_ds = build_dataset(
        *load_model_and_tokenizer(args)[1:],  # nur tokenizer extrahieren? Falsch – refactor
        # Korrektur: wir brauchen tokenizer separat
    )

    # REFACTOR: Wir laden zunächst Model + Tokenizer, dann Dataset
    model, tokenizer = load_model_and_tokenizer(args)
    train_ds, eval_ds = build_dataset(tokenizer, texts, args.max_length, args.eval_split, args.seed)

    LOGGER.info(f"Train Samples: {len(train_ds)} | Eval: {len(eval_ds) if eval_ds else 0}")

    trainer = build_trainer(model, tokenizer, train_ds, eval_ds, args, output_dir)

    resume_cp = None
    if args.resume:
        resume_cp = args.resume
    elif not args.no_resume and any(p.name.startswith('checkpoint-') for p in output_dir.glob('*')):
        # Ältesten oder neuesten nehmen – wir wählen neuesten
        checkpoints = [p for p in output_dir.glob('checkpoint-*') if p.is_dir()]
        if checkpoints:
            resume_cp = str(max(checkpoints, key=lambda p: int(p.name.split('-')[1])))
            LOGGER.info(f"Resume von Checkpoint: {resume_cp}")

    LOGGER.info("Starte Training...")
    mx = get_metrics_exporter()
    if args.metrics_http:
        try:
            mx.start_http(port=9310)
            LOGGER.info("📡 Metrics Endpoint auf :9310 aktiv")
        except Exception as e:  # pragma: no cover
            LOGGER.warning(f"Konnte Metrics Endpoint nicht starten: {e}")
    train_start = time.time()
    mx.inc("adapter_training_runs_total")
    mx.set("adapter_train_dataset_size", len(train_ds))
    trainer.train(resume_from_checkpoint=resume_cp)
    train_duration = time.time() - train_start
    mx.observe("adapter_training_duration_seconds", train_duration)

    LOGGER.info("Speichere Adapter...")
    trainer.save_model()
    tokenizer.save_pretrained(output_dir)

    ppl = None
    if args.eval_after:
        LOGGER.info("Berechne schnelle Perplexity (Sample)...")
        ppl = quick_perplexity(model, tokenizer, eval_ds)
        if ppl:
            LOGGER.info(f"Sample Perplexity: {ppl:.2f}")
            mx.observe("adapter_sample_perplexity", float(ppl))

    if args.push_registry:
        update_registry(args, output_dir)
        if ppl is not None:
            # Patch metrics rein
            registry_path = Path(args.registry_path)
            registry = json.loads(registry_path.read_text(encoding='utf-8'))
            for a in registry.get('adapters', []):
                if a.get('id') == output_dir.name:
                    a.setdefault('metrics', {})['ppl_dev'] = ppl
            registry_path.write_text(json.dumps(registry, indent=2, ensure_ascii=False), encoding='utf-8')
            LOGGER.info("Registry mit Perplexity aktualisiert")
        mx.inc("adapter_registry_updates_total")

    LOGGER.info("Fertig.")
    mx.inc("adapter_training_completed_total")

if __name__ == "__main__":
    main()
