#!/usr/bin/env python3
"""
CLARA Incremental Training Manager
Ermöglicht Training in mehreren Schritten/Paketen für große Datensätze
"""

import os
import json
import yaml
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import logging

class CLARAIncrementalTrainer:
    def __init__(self, base_config_path: str, output_base_dir: str = "models/clara_incremental"):
        self.base_config_path = Path(base_config_path)
        self.output_base_dir = Path(output_base_dir)
        self.output_base_dir.mkdir(parents=True, exist_ok=True)
        
        # Logging setup
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Training history
        self.training_history = []
        self.history_file = self.output_base_dir / "training_history.json"
        
        # Load base config
        with open(self.base_config_path, 'r', encoding='utf-8') as f:
            self.base_config = yaml.safe_load(f)
    
    def prepare_data_batches(self, data_dir: str, batch_size: int = 1000) -> List[str]:
        """
        Teilt große Datensätze in trainierbare Batches auf
        
        Args:
            data_dir: Verzeichnis mit Trainingsdaten
            batch_size: Anzahl Dokumente pro Batch
            
        Returns:
            Liste der Batch-Dateien
        """
        data_path = Path(data_dir)
        batch_files = []
        
        if not data_path.exists():
            raise FileNotFoundError(f"Datenverzeichnis nicht gefunden: {data_dir}")
        
        # Sammle alle Daten-Dateien
        all_files = []
        for pattern in ['*.jsonl', '*.json', '*.txt', '*.md']:
            all_files.extend(data_path.glob(pattern))
        
        self.logger.info(f"Gefundene Dateien: {len(all_files)}")
        
        # Erstelle Batches
        batch_dir = self.output_base_dir / "data_batches"
        batch_dir.mkdir(exist_ok=True)
        
        if len(all_files) == 1 and all_files[0].suffix == '.jsonl':
            # Große JSONL-Datei in Chunks aufteilen
            batch_files = self._split_jsonl_file(all_files[0], batch_dir, batch_size)
        else:
            # Mehrere Dateien in Batches gruppieren
            batch_files = self._group_files_into_batches(all_files, batch_dir, batch_size)
        
        self.logger.info(f"Erstellt {len(batch_files)} Batches")
        return batch_files
    
    def _split_jsonl_file(self, jsonl_file: Path, batch_dir: Path, batch_size: int) -> List[str]:
        """Teilt große JSONL-Datei in kleinere Batches"""
        batch_files = []
        current_batch = []
        batch_num = 1
        
        self.logger.info(f"Teile {jsonl_file.name} in Batches mit je {batch_size} Einträgen")
        
        with open(jsonl_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                current_batch.append(line.strip())
                
                if len(current_batch) >= batch_size:
                    # Batch speichern
                    batch_file = batch_dir / f"batch_{batch_num:04d}.jsonl"
                    with open(batch_file, 'w', encoding='utf-8') as batch_f:
                        for entry in current_batch:
                            batch_f.write(entry + '\\n')
                    
                    batch_files.append(str(batch_file))
                    self.logger.info(f"Batch {batch_num} erstellt: {len(current_batch)} Einträge")
                    
                    current_batch = []
                    batch_num += 1
                
                # Progress-Info alle 10000 Zeilen
                if line_num % 10000 == 0:
                    self.logger.info(f"Verarbeitet: {line_num} Zeilen")
        
        # Letzten Batch speichern falls vorhanden
        if current_batch:
            batch_file = batch_dir / f"batch_{batch_num:04d}.jsonl"
            with open(batch_file, 'w', encoding='utf-8') as batch_f:
                for entry in current_batch:
                    batch_f.write(entry + '\\n')
            batch_files.append(str(batch_file))
            self.logger.info(f"Finaler Batch {batch_num} erstellt: {len(current_batch)} Einträge")
        
        return batch_files
    
    def _group_files_into_batches(self, files: List[Path], batch_dir: Path, batch_size: int) -> List[str]:
        """Gruppiert mehrere Dateien in Batches"""
        batch_files = []
        
        # Für einfache Implementierung: jede Datei = ein Batch
        # In Zukunft könnte man Dateien nach Größe kombinieren
        for i, file_path in enumerate(files, 1):
            batch_file = batch_dir / f"batch_{i:04d}_{file_path.stem}.jsonl"
            
            # Kopiere/konvertiere Datei zu JSONL
            if file_path.suffix == '.jsonl':
                shutil.copy2(file_path, batch_file)
            else:
                # Konvertiere zu JSONL
                with open(file_path, 'r', encoding='utf-8') as src:
                    content = src.read()
                with open(batch_file, 'w', encoding='utf-8') as dst:
                    json_entry = {"text": content}
                    dst.write(json.dumps(json_entry, ensure_ascii=False) + '\n')
            
            batch_files.append(str(batch_file))
        
        return batch_files
    
    def create_incremental_config(self, batch_file: str, step_num: int, 
                                  previous_model_path: Optional[str] = None) -> str:
        """
        Erstellt Konfiguration für einen Trainingsschritt
        
        Args:
            batch_file: Pfad zur Batch-Datei
            step_num: Schritt-Nummer
            previous_model_path: Pfad zum vorherigen Modell (für Fortsetzung)
            
        Returns:
            Pfad zur Konfigurationsdatei
        """
        config = self.base_config.copy()
        
        # Daten-Konfiguration anpassen
        config['data']['train_file'] = batch_file
        
        # Output-Verzeichnis für diesen Schritt
        step_output_dir = self.output_base_dir / f"step_{step_num:04d}"
        config['training']['output_dir'] = str(step_output_dir)
        
        # Modell-Pfad anpassen für Fortsetzung
        if previous_model_path and step_num > 1:
            # Lade vorheriges Modell als Basis
            config['model']['base_model'] = previous_model_path
            config['model']['is_checkpoint'] = True
        
        # Training-Parameter für inkrementelles Training anpassen
        if step_num > 1:
            # Niedrigere Learning Rate für spätere Schritte
            original_lr = float(config['training']['learning_rate'])
            config['training']['learning_rate'] = original_lr * 0.5
            
            # Weniger Epochen für Fortsetzung
            config['training']['num_epochs'] = max(1, config['training']['num_epochs'] // 2)
        
        # Konfiguration speichern
        config_file = self.output_base_dir / f"config_step_{step_num:04d}.yaml"
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
        
        return str(config_file)
    
    def run_incremental_training(self, data_dir: str, batch_size: int = 1000,
                                max_steps: Optional[int] = None) -> Dict:
        """
        Führt komplettes inkrementelles Training durch
        
        Args:
            data_dir: Verzeichnis mit Trainingsdaten
            batch_size: Anzahl Dokumente pro Batch
            max_steps: Maximale Anzahl Schritte (None = alle)
            
        Returns:
            Training-Zusammenfassung
        """
        self.logger.info("🚀 Starte inkrementelles CLARA Training")
        
        # 1. Daten in Batches aufteilen
        batch_files = self.prepare_data_batches(data_dir, batch_size)
        
        if max_steps:
            batch_files = batch_files[:max_steps]
        
        # 2. Training-Schritte durchführen
        training_summary = {
            'start_time': datetime.now().isoformat(),
            'total_batches': len(batch_files),
            'completed_steps': 0,
            'step_results': []
        }
        
        previous_model_path = None
        
        for step_num, batch_file in enumerate(batch_files, 1):
            self.logger.info(f"\\n📊 Schritt {step_num}/{len(batch_files)}: {Path(batch_file).name}")
            
            # Konfiguration für diesen Schritt erstellen
            config_file = self.create_incremental_config(
                batch_file, step_num, previous_model_path
            )
            
            # Training-Schritt ausführen
            step_result = self._run_training_step(config_file, step_num)
            training_summary['step_results'].append(step_result)
            
            if step_result['success']:
                training_summary['completed_steps'] += 1
                previous_model_path = step_result['output_dir']
                self.logger.info(f"✅ Schritt {step_num} erfolgreich")
            else:
                self.logger.error(f"❌ Schritt {step_num} fehlgeschlagen: {step_result['error']}")
                break
        
        training_summary['end_time'] = datetime.now().isoformat()
        training_summary['final_model'] = previous_model_path
        
        # Zusammenfassung speichern
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(training_summary, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"\\n🎉 Training abgeschlossen: {training_summary['completed_steps']}/{training_summary['total_batches']} Schritte")
        return training_summary
    
    def _run_training_step(self, config_file: str, step_num: int) -> Dict:
        """Führt einen einzelnen Training-Schritt aus"""
        import subprocess
        
        try:
            # Training-Skript ausführen (angepasster Name mit Prefix)
            cmd = f"python scripts/clara_train_lora.py --config {config_file}"
            
            self.logger.info(f"Führe aus: {cmd}")
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, cwd="."
            )
            
            if result.returncode == 0:
                # Erfolgreich - Output-Verzeichnis finden
                with open(config_file, 'r') as f:
                    config = yaml.safe_load(f)
                output_dir = config['training']['output_dir']
                
                return {
                    'step': step_num,
                    'success': True,
                    'output_dir': output_dir,
                    'config_file': config_file,
                    'stdout': result.stdout[-1000:],  # Letzte 1000 Zeichen
                }
            else:
                return {
                    'step': step_num,
                    'success': False,
                    'error': result.stderr,
                    'config_file': config_file,
                }
                
        except Exception as e:
            return {
                'step': step_num,
                'success': False,
                'error': str(e),
                'config_file': config_file,
            }
    
    def resume_training(self, from_step: int) -> Dict:
        """Setzt unterbrochenes Training fort"""
        self.logger.info(f"Setze Training ab Schritt {from_step} fort")
        
        # Lade Training-History
        if self.history_file.exists():
            with open(self.history_file, 'r') as f:
                history = json.load(f)
        else:
            raise FileNotFoundError("Keine Training-History gefunden")
        
        # Finde letztes erfolgreiches Modell
        last_successful_model = None
        for step_result in history['step_results']:
            if step_result['success'] and step_result['step'] < from_step:
                last_successful_model = step_result['output_dir']
        
        if not last_successful_model:
            raise ValueError(f"Kein erfolgreiches Modell vor Schritt {from_step} gefunden")
        
        self.logger.info(f"Setze Training fort von: {last_successful_model}")
        
        # Implementierung für Fortsetzung...
        # (Vereinfacht für Beispiel)
        return {"resumed": True, "from_model": last_successful_model}


def main():
    """Beispiel für inkrementelles Training"""
    
    # Trainer initialisieren
    trainer = CLARAIncrementalTrainer(
        base_config_path="configs/leo_cuda_config.yaml",
        output_base_dir="models/clara_incremental"
    )
    
    # Großen Datensatz in Schritten trainieren
    # Beispiel (alt): Y:\veritas\data in 1000er Batches
    # Neuer Standard-Datenpfad: Y:\data
    summary = trainer.run_incremental_training(
        data_dir="data/veritas_processed",
        batch_size=500,  # 500 Dokumente pro Batch
        max_steps=5      # Nur erste 5 Schritte für Test
    )
    
    print("\\n📊 TRAINING ZUSAMMENFASSUNG:")
    print(f"Abgeschlossene Schritte: {summary['completed_steps']}/{summary['total_batches']}")
    if summary['final_model']:
        print(f"Finales Modell: {summary['final_model']}")


if __name__ == "__main__":
    main()
