#!/usr/bin/env python3
"""
CLARA Continuous Learning - Kontinuierliche LoRA Verbesserung zur Laufzeit
Online Learning System für CLARA mit Live-Updates
"""

import argparse
import json
import time
import torch
import yaml
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import queue  # Queue ist jetzt im queue-Modul
from dataclasses import dataclass
import threading
import queue
import logging
from collections import deque

# Add parent directory to path
import sys
script_dir = Path(__file__).parent
project_root = script_dir.parent
sys.path.insert(0, str(project_root))

from transformers import (
    AutoTokenizer, 
    AutoModelForCausalLM, 
    TrainingArguments, 
    Trainer,
    DataCollatorForLanguageModeling
)
from peft import LoraConfig, get_peft_model, PeftModel
from datasets import Dataset
from src.utils.logger import setup_logger
from src.utils.metrics import get_metrics_exporter
from src.utils.content_filter import get_content_filter

@dataclass
class LiveSample:
    """Live Training Sample für kontinuierliches Lernen"""
    text: str
    timestamp: float
    feedback_score: float = 0.0  # -1 bis 1 (negativ, neutral, positiv)
    source: str = "live"
    importance: int = 1  # 1-5

class LiveLearningBuffer:
    """Puffer für Live-Learning Samples mit Qualitäts-Filterung"""
    
    def __init__(self, max_size: int = 500, quality_threshold: float = 0.0):
        self.samples = deque(maxlen=max_size)
        self.quality_threshold = quality_threshold
        self.lock = threading.Lock()
        
    def add_sample(self, text: str, feedback_score: float = 0.0, 
                   source: str = "live", importance: int = 1):
        """Fügt Sample mit Qualitätsbewertung hinzu"""
        with self.lock:
            sample = LiveSample(
                text=text,
                timestamp=time.time(),
                feedback_score=feedback_score,
                source=source,
                importance=importance
            )
            
            # Nur qualitativ hochwertige Samples hinzufügen
            if feedback_score >= self.quality_threshold:
                self.samples.append(sample)
                return True
            return False
    
    def get_quality_batch(self, batch_size: int = 50) -> List[LiveSample]:
        """Holt die besten Samples für Training"""
        with self.lock:
            if len(self.samples) < batch_size:
                return []
            
            # Sortiere nach Qualität und Wichtigkeit
            sorted_samples = sorted(
                self.samples, 
                key=lambda x: (x.feedback_score * x.importance, -x.timestamp),
                reverse=True
            )
            
            # Nimm die besten Samples
            batch = sorted_samples[:batch_size]
            
            # Entferne verwendete Samples
            for sample in batch:
                try:
                    self.samples.remove(sample)
                except ValueError:
                    pass
            
            return batch
    
    def get_stats(self) -> Dict:
        """Buffer-Statistiken"""
        with self.lock:
            if not self.samples:
                return {'count': 0, 'avg_quality': 0.0}
            
            qualities = [s.feedback_score for s in self.samples]
            sources = [s.source for s in self.samples]
            
            return {
                'count': len(self.samples),
                'avg_quality': sum(qualities) / len(qualities),
                'quality_range': (min(qualities), max(qualities)),
                'sources': list(set(sources)),
                'buffer_usage': len(self.samples) / self.samples.maxlen
            }

class ContinuousLoRATrainer:
    """Kontinuierlicher LoRA-Trainer für Live-Learning"""
    
    def __init__(self, config_path: str):
        self.config = self._load_config(config_path)
        self.logger = setup_logger(__name__)
        
        # Live Learning Buffer
        self.buffer = LiveLearningBuffer(
            max_size=self.config.get('continuous', {}).get('buffer_size', 500),
            quality_threshold=self.config.get('continuous', {}).get('quality_threshold', 0.0)
        )
        
        # Modell-Komponenten
        self.tokenizer = None
        self.model = None
        self.trainer = None
        
        # Training-State
        self.is_training = False
        self.training_thread = None
        self.learning_active = True
        
        # Metriken (lokal) + Exporter
        self.metrics = {
            'total_live_samples': 0,
            'successful_trainings': 0,
            'failed_trainings': 0,
            'model_updates': 0,
            'last_update': None,
            'avg_sample_quality': 0.0
        }
        self.metrics_exporter = get_metrics_exporter()
        if os.environ.get("CLARA_METRICS_HTTP") == "1":
            try:
                port = int(os.environ.get("CLARA_METRICS_PORT", "9310"))
                self.metrics_exporter.start_http(port=port)
                self.logger.info(f"📡 Metrics Endpoint aktiv (Port {port})")
            except Exception as e:  # pragma: no cover
                self.logger.warning(f"Konnte Metrics Endpoint nicht starten: {e}")
        
    self._initialize_model()
    self.content_filter = get_content_filter()
    
    def _load_config(self, config_path: str) -> Dict:
        """Lädt Konfiguration"""
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # Kontinuierliches Lernen Defaults
        if 'continuous' not in config:
            config['continuous'] = {
                'enabled': True,
                'buffer_size': 500,
                'quality_threshold': 0.0,
                'train_interval': 300,  # 5 Minuten
                'min_batch_size': 20,
                'learning_rate': 5e-6,  # Sehr niedrig für kontinuierliches Lernen
                'max_epochs': 1
            }
        
        return config
    
    def _initialize_model(self):
        """Initialisiert oder lädt existierendes Modell"""
        self.logger.info("🚀 Initialisiere kontinuierliches LoRA-Learning...")
        
        model_name = self.config['model'].get('name', self.config['model'].get('base_model'))
        output_dir = Path(self.config['training']['output_dir'])
        
        # Tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        
        # Prüfe auf existierendes LoRA-Modell
        if output_dir.exists() and (output_dir / "adapter_config.json").exists():
            self.logger.info(f"📦 Lade existierendes LoRA-Modell: {output_dir}")
            
            base_model = AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype=torch.float16,
                device_map="auto",
                low_cpu_mem_usage=True
            )
            
            self.model = PeftModel.from_pretrained(base_model, output_dir)
            self.model.train()  # Wichtig: Training-Modus für kontinuierliches Lernen
        else:
            self.logger.info("🆕 Erstelle neues LoRA-Modell für kontinuierliches Lernen...")
            
            base_model = AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype=torch.float16,
                device_map="auto",
                low_cpu_mem_usage=True
            )
            
            lora_config = LoraConfig(
                task_type="CAUSAL_LM",
                r=self.config['lora']['r'],
                lora_alpha=self.config['lora']['alpha'],
                lora_dropout=self.config['lora']['dropout'],
                target_modules=self.config['lora']['target_modules'],
                inference_mode=False  # Wichtig: Erlaube Training zur Laufzeit
            )
            
            self.model = get_peft_model(base_model, lora_config)
        
        self.logger.info("✅ Modell für kontinuierliches Lernen bereit")
    
    def start_continuous_learning(self):
        """Startet kontinuierliches Lernen im Hintergrund"""
        if self.training_thread is None or not self.training_thread.is_alive():
            self.learning_active = True
            self.training_thread = threading.Thread(target=self._continuous_learning_loop)
            self.training_thread.daemon = True
            self.training_thread.start()
            self.logger.info("🔄 Kontinuierliches Lernen gestartet")
    
    def stop_continuous_learning(self):
        """Stoppt kontinuierliches Lernen"""
        self.learning_active = False
        if self.training_thread and self.training_thread.is_alive():
            self.training_thread.join(timeout=15)
        self.logger.info("⏹️  Kontinuierliches Lernen gestoppt")
    
    def _continuous_learning_loop(self):
        """Haupt-Loop für kontinuierliches Lernen"""
        self.logger.info("🔄 Kontinuierliches Lernen aktiv")
        
        train_interval = self.config['continuous']['train_interval']
        min_batch_size = self.config['continuous']['min_batch_size']
        
        while self.learning_active:
            try:
                # Prüfe auf verfügbare Samples
                batch = self.buffer.get_quality_batch(min_batch_size)
                
                if len(batch) >= min_batch_size:
                    self.logger.info(f"🎯 Starte Live-Training mit {len(batch)} Samples")
                    success = self._perform_live_training(batch)
                    
                    if success:
                        self.metrics['successful_trainings'] += 1
                        self.metrics['model_updates'] += 1
                        self.metrics['last_update'] = datetime.now()
                        self.metrics_exporter.inc("live_training_runs_total")
                        self.metrics_exporter.set("live_buffer_size", self.buffer.get_stats()['count'])
                    else:
                        self.metrics['failed_trainings'] += 1
                        self.metrics_exporter.inc("live_training_failures_total")
                
                # Warte bis zum nächsten Training-Zyklus
                time.sleep(train_interval)
                
            except Exception as e:
                self.logger.error(f"Fehler im kontinuierlichen Lernen: {e}")
                time.sleep(30)
    
    def _perform_live_training(self, samples: List[LiveSample]) -> bool:
        """Führt Live-Training mit Samples durch"""
        try:
            if self.is_training:
                self.logger.warning("Training bereits aktiv, überspringe...")
                return False
            
            self.is_training = True
            
            # Erstelle Dataset
            texts = [sample.text for sample in samples]
            weights = [sample.feedback_score * sample.importance for sample in samples]
            
            dataset = Dataset.from_dict({
                "text": texts,
                "weight": weights
            })
            
            # Tokenisierung
            def tokenize_function(examples):
                tokenized = self.tokenizer(
                    examples["text"],
                    truncation=True,
                    padding="max_length",
                    max_length=self.config['data']['max_length'],
                    return_tensors=None
                )
                tokenized["labels"] = tokenized["input_ids"].copy()
                return tokenized
            
            tokenized_dataset = dataset.map(tokenize_function, batched=True)
            
            # Training Arguments für Live-Learning
            training_args = TrainingArguments(
                output_dir=self.config['training']['output_dir'],
                num_train_epochs=self.config['continuous']['max_epochs'],
                per_device_train_batch_size=2,  # Sehr kleine Batches
                gradient_accumulation_steps=2,
                learning_rate=self.config['continuous']['learning_rate'],
                weight_decay=0.001,  # Geringe Regularisierung
                warmup_steps=0,  # Kein Warmup für Live-Learning
                logging_steps=10,
                save_steps=1000,  # Seltener speichern
                save_total_limit=2,
                fp16=True,
                dataloader_pin_memory=False,
                remove_unused_columns=False,
                report_to=None,
                overwrite_output_dir=False,
                load_best_model_at_end=False  # Behalte letztes Modell
            )
            
            # Data Collator
            data_collator = DataCollatorForLanguageModeling(
                tokenizer=self.tokenizer,
                mlm=False
            )
            
            # Live Trainer
            trainer = Trainer(
                model=self.model,
                args=training_args,
                train_dataset=tokenized_dataset,
                data_collator=data_collator,
                processing_class=self.tokenizer
            )
            
            # Training durchführen
            start_time = time.time()
            trainer.train()
            duration = time.time() - start_time
            
            # Modell speichern (inkrementell)
            trainer.save_model()
            
            self.metrics['total_live_samples'] += len(samples)
            self.metrics['avg_sample_quality'] = sum(s.feedback_score for s in samples) / len(samples)
            
            self.logger.info(f"✅ Live-Training erfolgreich: {len(samples)} Samples verarbeitet")
            self.metrics_exporter.observe("live_training_duration_seconds", duration)
            self.metrics_exporter.inc("live_training_samples_total", len(samples))
            self.metrics_exporter.set("live_buffer_size", self.buffer.get_stats()['count'])
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler beim Live-Training: {e}")
            self.metrics_exporter.inc("live_training_failures_total")
            return False
        finally:
            self.is_training = False
    
    def add_feedback_sample(self, text: str, feedback_score: float, 
                           source: str = "user", importance: int = 1):
        """Fügt Sample mit Feedback hinzu"""
        # Safety / Qualitätsfilter anwenden
        filter_result = self.content_filter.assess(text)
        if not filter_result.accept:
            self.logger.debug(f"Sample verworfen (Filter): reasons={filter_result.reasons} score={filter_result.score}")
            return False

        success = self.buffer.add_sample(text, feedback_score, source, importance)
        if success:
            self.logger.debug(f"Feedback-Sample hinzugefügt: {text[:50]}... (Score: {feedback_score})")
            self.metrics_exporter.inc("live_samples_total")
            self.metrics_exporter.set("live_buffer_size", self.buffer.get_stats()['count'])
        return success
    
    def process_conversation(self, user_input: str, model_output: str, user_rating: int):
        """Verarbeitet Konversation mit Nutzerbewertung"""
        # Konvertiere Rating (1-5) zu Feedback-Score (-1 bis 1)
        feedback_score = (user_rating - 3) / 2  # 1->-1, 3->0, 5->1
        
        # Erstelle Training-Text aus Konversation
        training_text = f"Human: {user_input}\nAssistant: {model_output}"
        
        return self.add_feedback_sample(
            training_text, 
            feedback_score, 
            source="conversation", 
            importance=max(1, abs(user_rating - 3))  # Extreme Bewertungen sind wichtiger
        )
    
    def get_live_stats(self) -> Dict:
        """Live-Statistiken"""
        buffer_stats = self.buffer.get_stats()
        
        return {
            'continuous_learning': {
                'active': self.learning_active,
                'currently_training': self.is_training,
                'thread_alive': self.training_thread.is_alive() if self.training_thread else False
            },
            'buffer': buffer_stats,
            'metrics': self.metrics,
            'model_info': {
                'trainable_params': self.model.num_parameters() if hasattr(self.model, 'num_parameters') else 'unknown',
                'adapter_loaded': isinstance(self.model, PeftModel)
            }
        }
    
    def generate_with_live_model(self, prompt: str, max_length: int = 150) -> str:
        """Generiert Text mit kontinuierlich verbessertem Modell"""
        self.model.eval()
        
        inputs = self.tokenizer(prompt, return_tensors="pt")
        inputs = {k: v.to(self.model.device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_length=len(inputs['input_ids'][0]) + max_length,
                do_sample=True,
                temperature=0.7,
                top_p=0.9,
                pad_token_id=self.tokenizer.eos_token_id
            )
        
        generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        return generated_text[len(prompt):].strip()

def main():
    parser = argparse.ArgumentParser(description="CLARA Continuous Learning System")
    parser.add_argument("--config", default="configs/leo_cuda_config.yaml")
    parser.add_argument("--interactive", action="store_true", help="Interaktiver Modus")
    parser.add_argument("--stats", action="store_true", help="Zeige Live-Statistiken")
    parser.add_argument("--demo", action="store_true", help="Demo-Modus")
    
    args = parser.parse_args()
    
    trainer = ContinuousLoRATrainer(args.config)
    
    try:
        if args.stats:
            stats = trainer.get_live_stats()
            print("📊 CONTINUOUS LEARNING STATISTIKEN")
            print("=" * 50)
            print(f"🔄 Kontinuierliches Lernen: {'✅ Aktiv' if stats['continuous_learning']['active'] else '❌ Inaktiv'}")
            print(f"🎯 Aktuell Training: {'✅ Ja' if stats['continuous_learning']['currently_training'] else '❌ Nein'}")
            print(f"📦 Buffer: {stats['buffer']['count']} Samples (Ø Qualität: {stats['buffer'].get('avg_quality', 0):.2f})")
            print(f"📈 Erfolgreiche Trainings: {stats['metrics']['successful_trainings']}")
            print(f"🔄 Modell-Updates: {stats['metrics']['model_updates']}")
            print(f"📊 Live-Samples total: {stats['metrics']['total_live_samples']}")
            
        elif args.demo:
            print("🚀 CLARA Continuous Learning Demo")
            trainer.start_continuous_learning()
            
            # Demo-Samples hinzufügen
            demo_samples = [
                ("Das Verwaltungsverfahren ist ein wichtiger Bestandteil des deutschen Rechts.", 0.8),
                ("Bescheide müssen ordnungsgemäß zugestellt werden.", 0.6),
                ("Diese Antwort ist völlig falsch und unbrauchbar.", -0.8),
                ("Eine sehr hilfreiche und präzise Erklärung der Rechtslage.", 1.0)
            ]
            
            for text, score in demo_samples:
                trainer.add_feedback_sample(text, score, "demo", 3)
                time.sleep(1)
            
            print(f"✅ {len(demo_samples)} Demo-Samples hinzugefügt")
            
            # Warte auf Training
            time.sleep(10)
            
            stats = trainer.get_live_stats()
            print(f"📊 Buffer: {stats['buffer']['count']} Samples")
            
        elif args.interactive:
            print("🤖 CLARA Continuous Learning - Interaktiv")
            print("Kommandos: feedback <text> <score>, generate <prompt>, stats, quit")
            
            trainer.start_continuous_learning()
            
            while True:
                try:
                    cmd = input("\n> ").strip()
                    
                    if cmd.startswith("feedback "):
                        parts = cmd.split(" ", 2)
                        if len(parts) >= 3:
                            text, score_str = parts[1], parts[2]
                            try:
                                score = float(score_str)
                                success = trainer.add_feedback_sample(text, score, "interactive", 2)
                                print("✅ Feedback hinzugefügt" if success else "❌ Qualität zu niedrig")
                            except ValueError:
                                print("❌ Ungültige Bewertung")
                    
                    elif cmd.startswith("generate "):
                        prompt = cmd[9:]
                        response = trainer.generate_with_live_model(prompt)
                        print(f"🤖: {response}")
                    
                    elif cmd == "stats":
                        stats = trainer.get_live_stats()
                        print(f"Buffer: {stats['buffer']['count']} | Updates: {stats['metrics']['model_updates']} | "
                              f"Trainings: {stats['metrics']['successful_trainings']}")
                    
                    elif cmd in ["quit", "exit"]:
                        break
                    
                    else:
                        print("Verfügbare Kommandos: feedback <text> <score>, generate <prompt>, stats, quit")
                
                except KeyboardInterrupt:
                    break
        
        else:
            print("🚀 CLARA Continuous Learning läuft im Hintergrund")
            trainer.start_continuous_learning()
            
            try:
                while True:
                    time.sleep(60)
                    stats = trainer.get_live_stats()
                    if stats['continuous_learning']['active']:
                        print(f"📊 Updates: {stats['metrics']['model_updates']} | "
                              f"Buffer: {stats['buffer']['count']} | "
                              f"Qualität: {stats['buffer'].get('avg_quality', 0):.2f}")
            except KeyboardInterrupt:
                pass
    
    finally:
        trainer.stop_continuous_learning()
        print("👋 Continuous Learning gestoppt")

if __name__ == "__main__":
    main()
