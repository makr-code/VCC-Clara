"""
QLoRA Training Script für Verwaltungs-LLM
Dieses Skript implementiert QLoRA (Quantized LoRA) Training mit 4-bit Quantisierung.
"""

import os
import json
import torch
import argparse
import yaml
import sys
from datetime import datetime
from pathlib import Path

from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling,
    BitsAndBytesConfig,
)
from peft import LoraConfig, get_peft_model, TaskType, prepare_model_for_kbit_training
from datasets import load_dataset
import wandb

# Add parent directory to path to import src modules
script_dir = Path(__file__).parent
project_root = script_dir.parent
sys.path.insert(0, str(project_root))

from src.data.data_processor import VerwaltungsDataProcessor
from src.utils.logger import setup_logger
from src.utils.model_utils import save_model_for_ollama

def load_config(config_path: str) -> dict:
    """Lade Konfiguration aus YAML-Datei."""
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def setup_bnb_config(config: dict) -> BitsAndBytesConfig:
    """Erstelle BitsAndBytes-Konfiguration für Quantisierung."""
    return BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_use_double_quant=config['qlora']['double_quant'],
        bnb_4bit_quant_type=config['qlora']['quant_type'],
        bnb_4bit_compute_dtype=getattr(torch, config['qlora']['compute_dtype']),
    )

def setup_lora_config(config: dict) -> LoraConfig:
    """Erstelle LoRA-Konfiguration für QLoRA."""
    return LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=config['lora']['r'],
        lora_alpha=config['lora']['alpha'],
        lora_dropout=config['lora']['dropout'],
        target_modules=config['lora']['target_modules'],
        bias="none",
    )

def prepare_model_and_tokenizer(config: dict):
    """Lade und bereite quantisiertes Modell und Tokenizer vor."""
    logger = setup_logger(__name__)
    
    # BitsAndBytes-Konfiguration
    bnb_config = setup_bnb_config(config)
    
    # Tokenizer laden
    tokenizer = AutoTokenizer.from_pretrained(
        config['model']['base_model'],
        trust_remote_code=True
    )
    
    # Padding token setzen falls nicht vorhanden
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    # Quantisiertes Modell laden
    model = AutoModelForCausalLM.from_pretrained(
        config['model']['base_model'],
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
        torch_dtype=getattr(torch, config['qlora']['compute_dtype']),
    )
    
    # Modell für k-bit Training vorbereiten
    model = prepare_model_for_kbit_training(model)
    
    # LoRA-Konfiguration anwenden
    lora_config = setup_lora_config(config)
    model = get_peft_model(model, lora_config)
    
    logger.info(f"Quantisiertes Modell geladen: {config['model']['base_model']}")
    logger.info(f"Trainierbare Parameter: {model.num_parameters()}")
    
    return model, tokenizer

def prepare_dataset(config: dict, tokenizer):
    """Bereite Datensatz für Training vor."""
    processor = VerwaltungsDataProcessor(
        tokenizer=tokenizer,
        max_length=config['data']['max_length']
    )
    
    # Daten laden und verarbeiten
    dataset = processor.load_and_process(config['data']['train_file'])
    
    # Train/Validation Split
    if config['data']['validation_split'] > 0:
        dataset = dataset.train_test_split(
            test_size=config['data']['validation_split'],
            seed=config['training']['seed']
        )
        train_dataset = dataset['train']
        eval_dataset = dataset['test']
    else:
        train_dataset = dataset
        eval_dataset = None
    
    return train_dataset, eval_dataset

def main(args):
    """Hauptfunktion für QLoRA Training."""
    # Konfiguration laden
    config = load_config(args.config)
    
    # Logger einrichten
    logger = setup_logger(__name__)
    logger.info("Starte QLoRA Training...")
    
    # CUDA Memory Management für QLoRA
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        logger.info(f"CUDA verfügbar: {torch.cuda.get_device_name()}")
        logger.info(f"CUDA Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
    
    # Wandb initialisieren falls konfiguriert
    if config.get('wandb', {}).get('enabled', False):
        wandb.init(
            project=config['wandb']['project'],
            name=f"qlora_training_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            config=config
        )
    
    # Modell und Tokenizer vorbereiten
    model, tokenizer = prepare_model_and_tokenizer(config)
    
    # Memory-efficient training settings
    model.config.use_cache = False
    model.gradient_checkpointing_enable()
    
    # Datensatz vorbereiten
    train_dataset, eval_dataset = prepare_dataset(config, tokenizer)
    
    # Data Collator
    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=False,
    )
    
    # Training Arguments für QLoRA
    output_dir = Path(config['training']['output_dir']) / f"qlora_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    training_args = TrainingArguments(
        output_dir=str(output_dir),
        overwrite_output_dir=True,
        num_train_epochs=config['training']['num_epochs'],
        per_device_train_batch_size=config['training']['batch_size'],
        per_device_eval_batch_size=config['training']['eval_batch_size'],
        gradient_accumulation_steps=config['training']['gradient_accumulation_steps'],
        learning_rate=config['training']['learning_rate'],
        weight_decay=config['training']['weight_decay'],
        warmup_steps=config['training']['warmup_steps'],
        logging_steps=config['training']['logging_steps'],
        save_steps=config['training']['save_steps'],
        eval_steps=config['training']['eval_steps'] if eval_dataset else None,
        eval_strategy="steps" if eval_dataset else "no",  # Korrigiert: evaluation_strategy -> eval_strategy
        save_total_limit=config['training']['save_total_limit'],
        bf16=config['training']['bf16'],
        fp16=False,  # BF16 wird für QLoRA empfohlen
        gradient_checkpointing=True,
        dataloader_pin_memory=False,
        optim="paged_adamw_32bit",  # Memory-efficient optimizer
        lr_scheduler_type="cosine",
        report_to="wandb" if config.get('wandb', {}).get('enabled', False) else None,
        ddp_find_unused_parameters=False,
    )
    
    # Trainer erstellen
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        data_collator=data_collator,
        tokenizer=tokenizer,
    )
    
    # Training starten
    logger.info("QLoRA Training wird gestartet...")
    trainer.train()
    
    # Modell speichern
    logger.info("Speichere finales QLoRA Modell...")
    trainer.save_model()
    tokenizer.save_pretrained(output_dir)
    
    # Für Ollama konvertieren
    if config.get('ollama', {}).get('convert', False):
        logger.info("Konvertiere QLoRA Modell für Ollama...")
        save_model_for_ollama(
            model_path=output_dir,
            ollama_output_path=config['ollama']['output_path'],
            model_name=config['ollama']['model_name']
        )
    
    logger.info("QLoRA Training abgeschlossen!")
    
    # Memory cleanup
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="QLoRA Training für Verwaltungs-LLM")
    parser.add_argument(
        "--config", 
        type=str, 
        default="configs/qlora_config.yaml",
        help="Pfad zur Konfigurationsdatei"
    )
    
    args = parser.parse_args()
    main(args)
