"""
LoRA Training Script für Verwaltungs-LLM
Dieses Skript implementiert LoRA (Low-Rank Adaptation) Training für deutsche Verwaltungstexte.
"""

import os
import json
import torch
import argparse
import yaml
import sys
import time
from datetime import datetime
from pathlib import Path

from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling,
)
from peft import LoraConfig, get_peft_model, TaskType
from datasets import load_dataset

# Wandb optional halten – standardmäßig deaktivieren, wenn nicht ausdrücklich aktiviert
WANDB_AVAILABLE = False
wandb = None
if os.environ.get("WANDB_DISABLED", "").lower() not in ("true", "1", "yes"):
    try:  # Import erst versuchen, wenn nicht explizit deaktiviert
        import wandb  # type: ignore
        WANDB_AVAILABLE = True
    except ImportError:
        WANDB_AVAILABLE = False
        wandb = None

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

def setup_lora_config(config: dict) -> LoraConfig:
    """Erstelle LoRA-Konfiguration."""
    return LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=config['lora']['r'],
        lora_alpha=config['lora']['alpha'],
        lora_dropout=config['lora']['dropout'],
        target_modules=config['lora']['target_modules'],
        bias="none",
    )

def prepare_model_and_tokenizer(config: dict):
    """Lade und bereite Modell und Tokenizer vor."""
    logger = setup_logger(__name__)
    
    # Modell-Parameter extrahieren
    model_config = config['model']
    base_model = model_config['base_model']
    
    # Sichere Revision verwenden falls verfügbar
    revision = model_config.get('revision', None)
    trust_remote_code = model_config.get('trust_remote_code', True)
    
    # Retry-Mechanismus für robuste Downloads
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            logger.info(f"Lade Modell: {base_model} (Versuch {retry_count + 1}/{max_retries})")
            
            # Tokenizer laden mit Retry
            tokenizer = AutoTokenizer.from_pretrained(
                base_model,
                trust_remote_code=trust_remote_code,
                revision=revision
            )
            
            # Padding token setzen falls nicht vorhanden
            if tokenizer.pad_token is None:
                tokenizer.pad_token = tokenizer.eos_token
            
            # Modell laden mit Meta-Device-Behandlung
            model = AutoModelForCausalLM.from_pretrained(
                base_model,
                dtype=torch.float16 if config['training']['fp16'] else torch.float32,
                device_map=None,  # Kein automatisches Device-Mapping
                trust_remote_code=trust_remote_code,
                revision=revision,
                low_cpu_mem_usage=True  # Reduziert RAM-Verbrauch beim Laden
            )
            
            # Modell explizit auf GPU verschieben falls verfügbar
            if torch.cuda.is_available():
                logger.info("Verschiebe Modell auf GPU...")
                try:
                    model = model.cuda()
                except RuntimeError as cuda_error:
                    if "meta tensor" in str(cuda_error).lower():
                        logger.warning("Meta-Tensor erkannt, verwende to_empty()...")
                        model = model.to_empty(device="cuda")
                    else:
                        raise cuda_error
            
            # Erfolg! Schleife verlassen
            break
            
        except Exception as e:
            retry_count += 1
            error_msg = str(e)
            
            if "flash_attn" in error_msg.lower() or "flash attention" in error_msg.lower():
                logger.warning(f"Flash Attention nicht verfügbar: {e}")
                logger.info("Verwende alternatives Modell ohne Flash Attention...")
                
                # Fallback auf DiscoLM oder anderes Modell
                fallback_model = "DiscoResearch/DiscoLM-German-7b-v1"
                logger.info(f"Fallback auf: {fallback_model}")
                
                # Tokenizer für Fallback-Modell
                tokenizer = AutoTokenizer.from_pretrained(
                    fallback_model,
                    trust_remote_code=False
                )
                
                if tokenizer.pad_token is None:
                    tokenizer.pad_token = tokenizer.eos_token
                
                model = AutoModelForCausalLM.from_pretrained(
                    fallback_model,
                    dtype=torch.float16 if config['training']['fp16'] else torch.float32,
                    device_map="auto" if torch.cuda.is_available() else None,
                    trust_remote_code=False,
                    low_cpu_mem_usage=True
                )
                base_model = fallback_model
                break
                
            elif "IncompleteRead" in error_msg or "ChunkedEncodingError" in error_msg or "ProtocolError" in error_msg:
                logger.warning(f"Netzwerk-Fehler beim Download (Versuch {retry_count}/{max_retries}): {error_msg[:100]}...")
                if retry_count < max_retries:
                    wait_time = 2 ** retry_count  # Exponentieller Backoff: 2, 4, 8 Sekunden
                    logger.info(f"Warte {wait_time} Sekunden vor erneutem Versuch...")
                    time.sleep(wait_time)
                else:
                    logger.error("Maximale Anzahl Wiederholungen erreicht. Verwende Fallback-Modell.")
                    # Fallback zu kleinerem/robusterem Modell
                    fallback_model = "DiscoResearch/DiscoLM-German-7b-v1"
                    logger.info(f"Fallback auf robusteres Modell: {fallback_model}")
                    
                    tokenizer = AutoTokenizer.from_pretrained(fallback_model, trust_remote_code=False)
                    if tokenizer.pad_token is None:
                        tokenizer.pad_token = tokenizer.eos_token
                    
                    model = AutoModelForCausalLM.from_pretrained(
                        fallback_model,
                        dtype=torch.float16 if config['training']['fp16'] else torch.float32,
                        device_map="auto" if torch.cuda.is_available() else None,
                        trust_remote_code=False,
                        low_cpu_mem_usage=True
                    )
                    base_model = fallback_model
                    break
            else:
                logger.error(f"Unbekannter Fehler: {e}")
                raise e
    
    # LoRA-Konfiguration anwenden
    lora_config = setup_lora_config(config)
    model = get_peft_model(model, lora_config)
    
    logger.info(f"Modell geladen: {base_model}")
    logger.info(f"Trainierbare Parameter: {model.num_parameters()}")
    
    return model, tokenizer

def prepare_dataset(config: dict, tokenizer):
    """Bereite Datensatz für Training vor."""
    from src.data.data_processor import VerwaltungsDataProcessor
    
    # Einfache Tokenisierungsfunktion für Training
    def tokenize_function(examples):
        """Tokenisierungsfunktion mit korrektem Padding/Truncation für Training."""
        # Text tokenisieren mit Padding und Truncation
        model_inputs = tokenizer(
            examples["text"],
            truncation=True,
            padding="max_length",  # Wichtig: Alle Sequenzen auf gleiche Länge
            max_length=config['data']['max_length'],
            return_tensors=None,  # Noch keine Tensoren, Dataset macht das später
        )
        
        # Labels für Causal LM setzen (gleich input_ids)
        model_inputs["labels"] = model_inputs["input_ids"].copy()
        
        return model_inputs
    
    # Daten laden (ohne Tokenisierung)
    data_path = Path(config['data']['train_file'])
    texts = []
    
    if data_path.suffix.lower() == '.jsonl':
        with open(data_path, 'r', encoding='utf-8') as f:
            for line in f:
                data = json.loads(line.strip())
                if 'text' in data:
                    texts.append(data['text'])
    else:
        # Fallback auf VerwaltungsDataProcessor ohne Tokenisierung
        processor = VerwaltungsDataProcessor(tokenizer, config['data']['max_length'])
        temp_dataset = processor.load_and_process(config['data']['train_file'])
        # Extrahiere Texte vor Tokenisierung
        texts = [tokenizer.decode(item['input_ids'], skip_special_tokens=True) for item in temp_dataset]
    
    # Dataset mit korrekter Tokenisierung erstellen
    from datasets import Dataset
    dataset = Dataset.from_dict({"text": texts})
    
    # Tokenisierung mit korrekten Parametern
    dataset = dataset.map(
        tokenize_function,
        batched=True,
        remove_columns=["text"]
    )
    
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
    """Hauptfunktion für LoRA Training."""
    # Konfiguration laden
    config = load_config(args.config)

    # CLI-Flag oder Config können Wandb vollständig deaktivieren
    disable_wandb_flag = getattr(args, "disable_wandb", False)
    if (not config.get('wandb', {}).get('enabled', False)) or disable_wandb_flag:
        # Setzt offizielle Deaktivierungs-Variable bevor irgendetwas initialisiert
        os.environ['WANDB_DISABLED'] = 'true'
        # Sicherstellen, dass Trainer kein Reporting versucht
        if 'wandb' in config:
            config['wandb']['enabled'] = False
    
    
    # CUDA-Speicher-Optimierungen setzen (Windows-kompatibel)
    if torch.cuda.is_available():
        # Leere CUDA-Cache vor Training
        torch.cuda.empty_cache()
        # Speicher-Fragmentierung minimieren
        torch.backends.cudnn.benchmark = True
    
    # Logger einrichten
    logger = setup_logger(__name__)
    logger.info("Starte LoRA Training...")
    
    # GPU-Speicher Status
    if torch.cuda.is_available():
        gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
        logger.info(f"GPU: {torch.cuda.get_device_name(0)} ({gpu_memory:.1f} GB)")
    
    # W&B vollständig unterdrücken falls deaktiviert
    if config.get('wandb', {}).get('enabled', False) and not os.environ.get('WANDB_DISABLED'):
        if WANDB_AVAILABLE:
            try:
                wandb.init(
                    project=config['wandb']['project'],
                    name=f"lora_training_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    config=config
                )
            except Exception as e:
                logger.warning(f"W&B Initialisierung fehlgeschlagen -> fahre ohne fort: {e}")
        else:
            logger.warning("W&B konfiguriert aber nicht installiert – fahre ohne Monitoring fort.")
    else:
        logger.info("W&B deaktiviert (kein Tracking).")
    
    # Modell und Tokenizer vorbereiten
    model, tokenizer = prepare_model_and_tokenizer(config)
    
    # Datensatz vorbereiten
    train_dataset, eval_dataset = prepare_dataset(config, tokenizer)
    
    # Data Collator - einfach, da Daten bereits gepaddet sind
    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=False,
        pad_to_multiple_of=None,  # Nicht nötig, da bereits gepaddet
    )
    
    # Training Arguments mit korrigierten Parametern
    output_dir = Path(config['training']['output_dir']) / f"lora_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    training_args = TrainingArguments(
        output_dir=str(output_dir),
        overwrite_output_dir=True,
        num_train_epochs=config['training']['num_epochs'],
        per_device_train_batch_size=config['training']['batch_size'],
        per_device_eval_batch_size=config['training']['eval_batch_size'],
        gradient_accumulation_steps=config['training']['gradient_accumulation_steps'],
        learning_rate=float(config['training']['learning_rate']),  # Explizite Typ-Konvertierung
        weight_decay=float(config['training']['weight_decay']),    # Explizite Typ-Konvertierung
        warmup_steps=config['training']['warmup_steps'],
        logging_steps=config['training']['logging_steps'],
        save_steps=config['training']['save_steps'],
        eval_steps=config['training']['eval_steps'] if eval_dataset else None,
        eval_strategy="steps" if eval_dataset else "no",  # Korrigiert: evaluation_strategy -> eval_strategy
        save_total_limit=config['training']['save_total_limit'],
        fp16=config['training']['fp16'],
        dataloader_pin_memory=False,
        remove_unused_columns=False,  # Wichtig für Meta-Device-Modelle
        report_to=("wandb" if (config.get('wandb', {}).get('enabled', False) and not os.environ.get('WANDB_DISABLED')) else None),
    )
    
    # Trainer erstellen mit aktualisierter API
    class MemoryOptimizedTrainer(Trainer):
        """Trainer mit Speicher-Optimierungen für begrenzte GPU-Ressourcen."""
        
        def training_step(self, model, inputs, num_items_in_batch=None):
            """Training Step mit regelmäßiger Speicher-Bereinigung."""
            # Normaler Training Step
            result = super().training_step(model, inputs, num_items_in_batch)
            
            # Alle 100 Steps CUDA-Cache leeren
            if self.state.global_step % 100 == 0:
                torch.cuda.empty_cache()
            
            return result
    
    trainer = MemoryOptimizedTrainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        data_collator=data_collator,
        processing_class=tokenizer,  # Neu: processing_class statt tokenizer
    )
    
    # Training starten
    logger.info("Training wird gestartet...")
    
    # Resume-Funktionalität: Prüfe auf CLI-Argument oder automatisches Resume
    resume_from_checkpoint = None
    
    if args.resume:
        # Manuell spezifizierter Checkpoint
        resume_from_checkpoint = args.resume
        logger.info(f"🔄 Resume von spezifiziertem Checkpoint: {resume_from_checkpoint}")
    elif not args.no_resume and output_dir.exists():
        # Automatisches Resume (Standard): Suche nach Checkpoint-Ordnern
        checkpoint_dirs = [d for d in output_dir.iterdir() if d.is_dir() and d.name.startswith('checkpoint-')]
        if checkpoint_dirs:
            # Neuesten Checkpoint finden (höchste Nummer)
            latest_checkpoint = max(checkpoint_dirs, key=lambda x: int(x.name.split('-')[1]))
            resume_from_checkpoint = str(latest_checkpoint)
            logger.info(f"🔄 Automatisches Resume von: {resume_from_checkpoint}")
            logger.info(f"   (Verwende --no-resume um neues Training zu starten)")
        else:
            logger.info("🆕 Neues Training gestartet (keine Checkpoints gefunden)")
    elif args.no_resume:
        logger.info("🆕 Neues Training gestartet (Resume deaktiviert)")
    else:
        logger.info("🆕 Neues Training gestartet")
    
    # Training mit oder ohne Resume (mit Fehler-Fallback)
    try:
        trainer.train(resume_from_checkpoint=resume_from_checkpoint)
    except NameError as e:
        # Spezifischer Fehler aus Flash/Rotary Implementierung -> Fallback auf anderes Modell
        if 'apply_rotary_emb_func' in str(e):
            logger.warning("Fehler 'apply_rotary_emb_func' – falle auf DiscoResearch/DiscoLM-German-7b-v1 zurück.")
            config['model']['base_model'] = 'DiscoResearch/DiscoLM-German-7b-v1'
            model, tokenizer = prepare_model_and_tokenizer(config)
            # Trainer neu aufbauen (Dataset & Args wiederverwenden)
            trainer = MemoryOptimizedTrainer(
                model=model,
                args=training_args,
                train_dataset=train_dataset,
                eval_dataset=eval_dataset,
                data_collator=data_collator,
                processing_class=tokenizer,
            )
            trainer.train(resume_from_checkpoint=None)
        else:
            raise
    
    # Modell speichern
    logger.info("Speichere finales Modell...")
    trainer.save_model()
    tokenizer.save_pretrained(output_dir)
    
    # Für Ollama konvertieren
    if config.get('ollama', {}).get('convert', False):
        logger.info("Konvertiere Modell für Ollama...")
        save_model_for_ollama(
            model_path=output_dir,
            ollama_output_path=config['ollama']['output_path'],
            model_name=config['ollama']['model_name']
        )
    
    logger.info("Training abgeschlossen!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LoRA Training für Verwaltungs-LLM")
    parser.add_argument(
        "--config", 
        type=str, 
        default="configs/lora_config.yaml",
        help="Pfad zur Konfigurationsdatei"
    )
    parser.add_argument(
        "--resume", 
        type=str, 
        default=None,
        help="Pfad zu einem spezifischen Checkpoint zum Fortsetzen"
    )
    parser.add_argument(
        "--no-resume", 
        action="store_true",
        help="Deaktiviert automatisches Resume von letztem Checkpoint"
    )
    
    parser.add_argument(
        "--disable-wandb",
        action="store_true",
        help="Erzwingt vollständige Deaktivierung von Weights & Biases Tracking"
    )

    args = parser.parse_args()
    main(args)
