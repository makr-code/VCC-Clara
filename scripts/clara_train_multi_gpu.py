#!/usr/bin/env python3
"""
Multi-GPU LoRA Training Script für CLARA
Unterstützt Data Parallel und Distributed Data Parallel
"""

import os
import torch
import torch.distributed as dist
from torch.nn.parallel import DistributedDataParallel as DDP
import argparse
from pathlib import Path

# Projekt-Root zum Python-Pfad hinzufügen
project_root = Path(__file__).parent.parent
import sys
sys.path.insert(0, str(project_root))

# Import-Funktionen direkt definieren
import yaml
import logging
from transformers import (
    AutoModelForCausalLM, 
    AutoTokenizer, 
    BitsAndBytesConfig,
    LlamaTokenizer
)
from peft import LoraConfig, get_peft_model, TaskType
from datasets import load_dataset

def setup_logger(name):
    """Logger Setup"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(name)

def load_config(config_path):
    """Konfiguration laden"""
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def prepare_model_and_tokenizer(config):
    """Modell und Tokenizer vorbereiten"""
    model_name = config['model']['name']
    
    # Tokenizer laden
    tokenizer = AutoTokenizer.from_pretrained(
        model_name,
        trust_remote_code=True,
        use_fast=False
    )
    
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    # Quantization Config
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=config['model'].get('load_in_4bit', True),
        bnb_4bit_quant_type=config['model'].get('bnb_4bit_quant_type', 'nf4'),
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=config['model'].get('bnb_4bit_use_double_quant', True),
    )
    
    # Modell laden
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        quantization_config=bnb_config,
        device_map={"": torch.cuda.current_device()},
        trust_remote_code=True,
        torch_dtype=torch.float16,
    )
    
    # LoRA Konfiguration
    lora_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=config['lora']['r'],
        lora_alpha=config['lora']['alpha'],
        lora_dropout=config['lora']['dropout'],
        target_modules=config['lora']['target_modules'],
        bias=config['lora'].get('bias', 'none'),
    )
    
    # LoRA anwenden
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()
    
    return model, tokenizer

def prepare_dataset(config, tokenizer):
    """Dataset vorbereiten"""
    # Lokales Dataset laden
    data_path = config['data']['train_file']
    dataset = load_dataset('json', data_files=data_path, split='train')
    
    def tokenize_function(examples):
        return tokenizer(
            examples['text'],
            truncation=True,
            padding=False,
            max_length=config['data']['max_length'],
            return_overflowing_tokens=False,
        )
    
    # Tokenization
    tokenized_dataset = dataset.map(
        tokenize_function,
        batched=True,
        remove_columns=dataset.column_names,
    )
    
    # Train/Eval Split
    if config['data'].get('validation_split', 0) > 0:
        split_dataset = tokenized_dataset.train_test_split(
            test_size=config['data']['validation_split']
        )
        return split_dataset['train'], split_dataset['test']
    else:
        return tokenized_dataset, None
from transformers import TrainingArguments, Trainer, DataCollatorForLanguageModeling

def setup_distributed():
    """Setup für Distributed Training"""
    if 'RANK' in os.environ and 'WORLD_SIZE' in os.environ:
        rank = int(os.environ['RANK'])
        world_size = int(os.environ['WORLD_SIZE'])
        local_rank = int(os.environ['LOCAL_RANK'])
        
        # Initialize the process group
        dist.init_process_group(
            backend='nccl',
            rank=rank,
            world_size=world_size
        )
        
        # Set device
        torch.cuda.set_device(local_rank)
        
        return rank, world_size, local_rank
    else:
        return 0, 1, 0

def cleanup_distributed():
    """Cleanup nach Distributed Training"""
    if dist.is_initialized():
        dist.destroy_process_group()

class MultiGPUTrainer(Trainer):
    """Erweiterte Trainer-Klasse für Multi-GPU Optimierungen"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.gpu_count = torch.cuda.device_count()
        
    def training_step(self, model, inputs, num_items_in_batch=None):
        """Training Step mit Multi-GPU Speicher-Management"""
        result = super().training_step(model, inputs, num_items_in_batch)
        
        # Regelmäßige Speicher-Bereinigung auf allen GPUs
        if self.state.global_step % 100 == 0:
            for i in range(self.gpu_count):
                with torch.cuda.device(i):
                    torch.cuda.empty_cache()
        
        return result
    
    def log(self, logs):
        """Erweiterte Logging-Funktion für Multi-GPU"""
        # GPU-Speicher-Stats hinzufügen
        if self.gpu_count > 1:
            for i in range(self.gpu_count):
                memory_used = torch.cuda.memory_allocated(i) / 1024**3
                memory_total = torch.cuda.get_device_properties(i).total_memory / 1024**3
                logs[f'gpu_{i}_memory_gb'] = f"{memory_used:.1f}/{memory_total:.1f}"
        
        super().log(logs)

def main():
    parser = argparse.ArgumentParser(description="Multi-GPU LoRA Training für CLARA")
    parser.add_argument("--config", type=str, required=True, help="Pfad zur Konfigurationsdatei")
    parser.add_argument("--local_rank", type=int, default=-1, help="Lokaler Rank für DDP")
    args = parser.parse_args()
    
    # Distributed Setup
    rank, world_size, local_rank = setup_distributed()
    
    # Logger nur auf Hauptprozess
    logger = setup_logger(__name__) if rank == 0 else None
    
    try:
        # Konfiguration laden
        config = load_config(args.config)
        
        if rank == 0:
            logger.info(f"🚀 Starte Multi-GPU LoRA Training...")
            logger.info(f"🎮 GPUs verfügbar: {torch.cuda.device_count()}")
            logger.info(f"🌐 World Size: {world_size}, Rank: {rank}")
        
        # GPU-Status ausgeben
        if rank == 0:
            for i in range(torch.cuda.device_count()):
                gpu_name = torch.cuda.get_device_name(i)
                gpu_memory = torch.cuda.get_device_properties(i).total_memory / 1024**3
                logger.info(f"   GPU {i}: {gpu_name} ({gpu_memory:.1f} GB)")
        
        # Modell und Tokenizer vorbereiten
        model, tokenizer = prepare_model_and_tokenizer(config)
        
        # Dataset vorbereiten
        train_dataset, eval_dataset = prepare_dataset(config, tokenizer)
        
        # Data Collator
        data_collator = DataCollatorForLanguageModeling(
            tokenizer=tokenizer,
            mlm=False,
        )
        
        # Training Arguments für Multi-GPU
        output_dir = Path(config['training']['output_dir']) / f"multi_gpu_lora_{rank}"
        
        training_args = TrainingArguments(
            output_dir=str(output_dir),
            overwrite_output_dir=True,
            num_train_epochs=config['training']['num_epochs'],
            per_device_train_batch_size=config['training']['batch_size'],
            per_device_eval_batch_size=config['training']['eval_batch_size'],
            gradient_accumulation_steps=config['training']['gradient_accumulation_steps'],
            learning_rate=float(config['training']['learning_rate']),
            weight_decay=float(config['training']['weight_decay']),
            warmup_steps=config['training']['warmup_steps'],
            logging_steps=config['training']['logging_steps'],
            save_steps=config['training']['save_steps'],
            eval_steps=config['training']['eval_steps'] if eval_dataset else None,
            eval_strategy="steps" if eval_dataset else "no",
            save_total_limit=config['training']['save_total_limit'],
            fp16=config['training']['fp16'],
            dataloader_pin_memory=config['training'].get('dataloader_pin_memory', True),
            dataloader_num_workers=config['training']['dataloader_num_workers'],
            group_by_length=config['training'].get('group_by_length', True),
            remove_unused_columns=False,
            
            # Multi-GPU spezifische Parameter
            ddp_backend=config['training'].get('ddp_backend', 'nccl'),
            ddp_find_unused_parameters=config['training'].get('ddp_find_unused_parameters', False),
            local_rank=local_rank,
            
            # Logging nur auf Hauptprozess
            disable_tqdm=rank != 0,
            report_to="wandb" if config.get('wandb', {}).get('enabled', False) and rank == 0 else None,
        )
        
        # Trainer erstellen
        trainer = MultiGPUTrainer(
            model=model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=eval_dataset,
            data_collator=data_collator,
            processing_class=tokenizer,
        )
        
        # Training starten
        if rank == 0:
            logger.info("🎯 Training wird gestartet...")
        
        trainer.train()
        
        # Modell speichern (nur Hauptprozess)
        if rank == 0:
            logger.info("💾 Speichere finales Modell...")
            trainer.save_model()
            tokenizer.save_pretrained(output_dir)
            logger.info("✅ Multi-GPU Training abgeschlossen!")
    
    except Exception as e:
        if rank == 0:
            logger.error(f"❌ Fehler beim Training: {e}")
        raise e
    
    finally:
        # Cleanup
        cleanup_distributed()

if __name__ == "__main__":
    main()
