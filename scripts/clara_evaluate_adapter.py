#!/usr/bin/env python3
"""Evaluate Adapter Script

Funktionen:
- Lädt Basis + Adapter (PEFT)
- Berechnet einfache Perplexity auf bereitgestelltem Dataset (JSONL oder Text)
- Platzhalter für domänenspezifischen QA-Score (Hook)
- Optional: Schreibt Ergebnisse in Registry

Beispiel:
  python scripts/evaluate_adapter.py \
    --base-model mistralai/Mistral-7B-Instruct-v0.2 \
    --adapter-path models/adapters/steuerrecht/lora-r16-v1 \
    --dataset data/dev/steuerrecht_dev.jsonl \
    --registry-path metadata/adapter_registry.json \
    --update-registry
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
from typing import List, Optional
import sys

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel

# Logging fallback
try:
    from src.utils.logger import setup_logger
except Exception:
    import logging
    def setup_logger(name: str):
        logging.basicConfig(level=logging.INFO)
        return logging.getLogger(name)

LOGGER = setup_logger(__name__)

# ------------------ Helpers ------------------

def load_texts(path: Path, limit: Optional[int] = None) -> List[str]:
    texts: List[str] = []
    if path.suffix.lower() == '.jsonl':
        for line in path.read_text(encoding='utf-8').splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                if isinstance(obj, dict) and 'text' in obj:
                    texts.append(obj['text'])
            except json.JSONDecodeError:
                continue
    else:
        texts = [l.strip() for l in path.read_text(encoding='utf-8').splitlines() if l.strip()]
    if limit:
        texts = texts[:limit]
    return texts

# ------------------ Domain Score Placeholder ------------------

def domain_score_placeholder(generated: List[str], references: List[str]) -> float:
    """Sehr einfacher Platzhalter: inverser durchschnittlicher Längenunterschied.
    In Realität ersetzen durch: Retrieval + Antwort-Scoring / Klassifikator / Embedding Similarity.
    """
    if not generated or not references:
        return 0.0
    diffs = []
    for g, r in zip(generated, references):
        diffs.append(abs(len(g) - len(r)) / max(1, len(r)))
    avg = sum(diffs) / len(diffs)
    return max(0.0, 1.0 - min(1.0, avg))  # 0..1

# ------------------ Perplexity ------------------

def compute_perplexity(model, tokenizer, texts: List[str], max_samples: int = 64, max_length: int = 512) -> float:
    model.eval()
    losses = []
    device = next(model.parameters()).device
    for text in texts[:max_samples]:
        enc = tokenizer(text, truncation=True, max_length=max_length, return_tensors='pt')
        input_ids = enc['input_ids'].to(device)
        with torch.no_grad():
            out = model(input_ids=input_ids, labels=input_ids)
            losses.append(out.loss.item())
    return math.exp(sum(losses) / len(losses)) if losses else float('inf')

# ------------------ Registry Update ------------------

def update_registry(registry_path: Path, adapter_id: str, ppl: float, domain_score: float):
    if not registry_path.exists():
        LOGGER.warning("Registry nicht gefunden – überspringe Update")
        return
    data = json.loads(registry_path.read_text(encoding='utf-8'))
    updated = False
    for a in data.get('adapters', []):
        if a.get('id') == adapter_id:
            a.setdefault('metrics', {})['ppl_dev'] = round(ppl, 3)
            a['metrics']['domain_score'] = round(domain_score, 3)
            updated = True
            break
    if updated:
        registry_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')
        LOGGER.info("Registry aktualisiert (Evaluationsergebnisse gespeichert)")
    else:
        LOGGER.warning("Adapter ID nicht in Registry gefunden – kein Update")

# ------------------ Main ------------------

def parse_args():
    p = argparse.ArgumentParser(description="Evaluate Adapter (Perplexity + Domain Score Placeholder)")
    p.add_argument('--base-model', required=True)
    p.add_argument('--adapter-path', required=True)
    p.add_argument('--dataset', required=True)
    p.add_argument('--max-samples', type=int, default=64)
    p.add_argument('--max-length', type=int, default=512)
    p.add_argument('--update-registry', action='store_true')
    p.add_argument('--registry-path', default='metadata/adapter_registry.json')
    p.add_argument('--domain-score-limit', type=int, default=16, help='Anzahl Items für Domain Score Placeholder')
    return p.parse_args()

def main():
    args = parse_args()
    base_model = args.base_model
    adapter_path = Path(args.adapter_path)

    texts = load_texts(Path(args.dataset))
    if not texts:
        LOGGER.error('Keine Texte im Dataset gefunden.')
        return

    LOGGER.info(f"Lade Basis Modell: {base_model}")
    tokenizer = AutoTokenizer.from_pretrained(base_model, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    base = AutoModelForCausalLM.from_pretrained(base_model, torch_dtype=torch.float16 if torch.cuda.is_available() else None, device_map='auto' if torch.cuda.is_available() else None, low_cpu_mem_usage=True, trust_remote_code=True)

    LOGGER.info(f"Lade Adapter: {adapter_path}")
    model = PeftModel.from_pretrained(base, str(adapter_path))

    LOGGER.info("Berechne Perplexity...")
    ppl = compute_perplexity(model, tokenizer, texts, args.max_samples, args.max_length)
    LOGGER.info(f"Perplexity (Sample={min(len(texts), args.max_samples)}): {ppl:.2f}")

    domain_subset_ref = texts[:args.domain_score_limit]
    # Placeholder: Wir tun so als wären generierte Antworten identisch (oder modifizieren leicht)
    generated = [t[: max(10, int(len(t)*0.9))] for t in domain_subset_ref]
    domain_score = domain_score_placeholder(generated, domain_subset_ref)
    LOGGER.info(f"Domain Score (Placeholder): {domain_score:.3f}")

    if args.update_registry:
        update_registry(Path(args.registry_path), adapter_path.name, ppl, domain_score)

    summary = {
        'adapter': adapter_path.name,
        'perplexity': ppl,
        'domain_score_placeholder': domain_score,
        'samples_used': min(len(texts), args.max_samples)
    }
    print(json.dumps(summary, indent=2))

if __name__ == '__main__':
    main()
