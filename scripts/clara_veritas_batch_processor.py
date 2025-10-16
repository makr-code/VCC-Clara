"""
CLARA Veritas Batch Processor
Ursprünglich optimiert für das frühere Verzeichnis Y:\\veritas\\data\\ (jetzt migriert auf Y:\\data\\)
Verarbeitet große Mengen von Rechtsdokumenten intelligent

Hinweis Migration:
    Standard-Eingabepfad ist nun Y:\\data\\ (überschreibbar via ENV CLARA_DATA_DIR oder --input Argument)
"""

import argparse
import json
import time
import sys
import os
import yaml
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import hashlib
from datetime import datetime

# Add parent directory to path
script_dir = Path(__file__).parent
project_root = script_dir.parent
sys.path.insert(0, str(project_root))

from src.utils.logger import setup_logger

@dataclass
class BatchProcessingStats:
    """Statistiken für Batch-Verarbeitung"""
    total_files: int = 0
    processed_files: int = 0
    skipped_files: int = 0
    error_files: int = 0
    duplicates_found: int = 0
    total_texts: int = 0
    processing_time: float = 0.0
    files_per_second: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_files": self.total_files,
            "processed_files": self.processed_files,
            "skipped_files": self.skipped_files,
            "error_files": self.error_files,
            "duplicates_found": self.duplicates_found,
            "total_texts": self.total_texts,
            "processing_time": self.processing_time,
            "files_per_second": self.files_per_second,
            "completion_rate": self.processed_files / max(self.total_files, 1) * 100
        }

class VeritasBatchProcessor:
    """Hauptklasse für Veritas Batch-Processing"""
    
    def __init__(self, config_path: str):
        """Initialisiert den Batch-Processor mit Konfiguration"""
        self.logger = setup_logger(__name__)
        self.config = self._load_config(config_path)
        self.stats = BatchProcessingStats()
        self.duplicate_cache = set()
        self.error_files = []
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Lädt Konfiguration aus YAML-Datei"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            self.logger.error(f"Fehler beim Laden der Konfiguration: {e}")
            raise
    
    def _get_content_hash(self, text: str) -> str:
        """Erstellt Hash für Duplikatserkennung"""
        # Normalisiere Text für bessere Duplikatserkennung
        normalized = ' '.join(text.split()).lower()
        return hashlib.md5(normalized.encode()).hexdigest()
    
    def _is_duplicate(self, text: str) -> bool:
        """Prüft ob Text ein Duplikat ist"""
        dup_config = self.config.get('batch_processing', {}).get('duplicate_detection', {})
        if not dup_config.get('enabled', True):
            return False
            
        content_hash = self._get_content_hash(text)
        if content_hash in self.duplicate_cache:
            return True
        
        self.duplicate_cache.add(content_hash)
        return False
    
    def _assess_text_quality(self, text: str) -> float:
        """Bewertet Textqualität (vereinfachte Version)"""
        if not text or len(text.strip()) < 10:
            return 0.0
        
        # Einfache Qualitätskriterien
        score = 0.5  # Basis-Score
        
        # Länge bewerten
        length = len(text)
        if 50 <= length <= 10000:
            score += 0.2
        elif length > 10000:
            score += 0.1
        
        # Deutsche Rechtsbegriffe erkennen
        legal_terms = ['gesetz', 'artikel', 'absatz', 'paragraph', 'urteil', 
                      'beschluss', 'verwaltung', 'behörde', 'antrag', 'bescheid']
        found_terms = sum(1 for term in legal_terms if term in text.lower())
        score += min(found_terms * 0.05, 0.3)
        
        # Struktur bewerten (Großbuchstaben, Zahlen, Interpunktion)
        if any(c.isupper() for c in text):
            score += 0.1
        if any(c.isdigit() for c in text):
            score += 0.1
        if any(c in '.,;:!?' for c in text):
            score += 0.1
        
        return min(score, 1.0)
    
    def _extract_text_from_file(self, file_path: Path) -> List[str]:
        """Extrahiert Text aus verschiedenen Dateiformaten"""
        try:
            ext = file_path.suffix.lower()
            
            if ext in ['.txt', '.md', '.markdown']:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                return [content] if content.strip() else []
                
            elif ext == '.json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        # Extrahiere Text-Felder
                        texts = []
                        for key, value in data.items():
                            if isinstance(value, str) and len(value) > 20:
                                texts.append(value)
                        return texts
                    elif isinstance(data, list):
                        return [str(item) for item in data if isinstance(item, str)]
                    else:
                        return [str(data)]
                        
            elif ext == '.jsonl':
                texts = []
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            item = json.loads(line.strip())
                            if isinstance(item, dict):
                                # Suche nach Text-Feldern
                                for key in ['text', 'content', 'message', 'description']:
                                    if key in item and isinstance(item[key], str):
                                        texts.append(item[key])
                                        break
                            elif isinstance(item, str):
                                texts.append(item)
                        except json.JSONDecodeError:
                            continue
                return texts
                
            elif ext == '.csv':
                import pandas as pd
                try:
                    df = pd.read_csv(file_path, encoding='utf-8', errors='ignore')
                    texts = []
                    for col in df.columns:
                        if df[col].dtype == 'object':  # Text-Spalten
                            texts.extend(df[col].dropna().astype(str).tolist())
                    return [t for t in texts if len(t) > 20]
                except Exception:
                    return []
                    
            else:
                self.logger.warning(f"Ununterstütztes Format: {ext} für {file_path}")
                return []
                
        except Exception as e:
            self.logger.error(f"Fehler beim Extrahieren von {file_path}: {e}")
            return []
    
    def _process_single_file(self, file_path: Path) -> Dict[str, Any]:
        """Verarbeitet eine einzelne Datei"""
        result = {
            'file_path': str(file_path),
            'success': False,
            'texts': [],
            'error': None,
            'duplicates_removed': 0
        }
        
        try:
            # Text extrahieren
            raw_texts = self._extract_text_from_file(file_path)
            
            if not raw_texts:
                result['error'] = "Keine Texte extrahiert"
                return result
            
            # Qualitätsfilterung und Duplikatsprüfung
            quality_config = self.config.get('batch_processing', {}).get('quality_filtering', {})
            min_score = quality_config.get('min_score', 0.6)
            
            processed_texts = []
            duplicates_count = 0
            
            for text in raw_texts:
                # Längenprüfung
                if len(text) < quality_config.get('min_text_length', 50):
                    continue
                if len(text) > quality_config.get('max_text_length', 50000):
                    continue
                
                # Qualitätsprüfung
                if quality_config.get('ai_scoring', True):
                    quality_score = self._assess_text_quality(text)
                    if quality_score < min_score:
                        continue
                
                # Duplikatsprüfung
                if self._is_duplicate(text):
                    duplicates_count += 1
                    continue
                
                processed_texts.append(text)
            
            result['texts'] = processed_texts
            result['duplicates_removed'] = duplicates_count
            result['success'] = True
            
        except Exception as e:
            result['error'] = str(e)
            self.logger.error(f"Fehler bei Datei {file_path}: {e}")
        
        return result
    
    def _find_all_files(self, input_dir: Path) -> List[Path]:
        """Findet alle verarbeitbaren Dateien"""
        self.logger.info(f"Suche nach Dateien in: {input_dir}")
        
        supported_formats = []
        batch_config = self.config.get('batch_processing', {})
        format_config = batch_config.get('supported_formats', {
            'text': ['.txt', '.md'],
            'structured': ['.json', '.jsonl'],
            'documents': ['.pdf', '.docx']
        })
        for format_group in format_config.values():
            supported_formats.extend(format_group)
        
        all_files = []
        for ext in supported_formats:
            pattern = f"**/*{ext}"
            files = list(input_dir.glob(pattern))
            all_files.extend(files)
        
        # Größenfilterung
        max_size = self.config.get('batch_processing', {}).get('max_file_size_mb', 100) * 1024 * 1024
        filtered_files = []
        
        for file_path in all_files:
            try:
                if file_path.stat().st_size <= max_size:
                    filtered_files.append(file_path)
                else:
                    self.logger.warning(f"Datei zu groß: {file_path} "
                                      f"({file_path.stat().st_size / 1024 / 1024:.1f}MB)")
            except Exception as e:
                self.logger.warning(f"Fehler beim Prüfen von {file_path}: {e}")
        
        self.logger.info(f"Gefunden: {len(filtered_files)} verarbeitbare Dateien")
        return filtered_files
    
    def process_batch(self, input_path: str, output_path: str) -> BatchProcessingStats:
        """Hauptmethode für Batch-Verarbeitung"""
        start_time = time.time()
        
        # Pfade vorbereiten
        input_dir = Path(input_path)
        output_dir = Path(output_path)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"🚀 Starte Veritas Batch-Processing")
        self.logger.info(f"📁 Input: {input_dir}")
        self.logger.info(f"📁 Output: {output_dir}")
        
        # Alle Dateien finden
        all_files = self._find_all_files(input_dir)
        self.stats.total_files = len(all_files)
        
        if not all_files:
            self.logger.warning("❌ Keine verarbeitbaren Dateien gefunden!")
            return self.stats
        
        # Parallel verarbeiten
        num_workers = self.config.get('batch_processing', {}).get('parallel_workers', 4)
        chunk_size = self.config.get('batch_processing', {}).get('chunk_size', 1000)
        
        self.logger.info(f"⚙️ Verwende {num_workers} Prozesse mit Chunk-Größe {chunk_size}")
        
        all_processed_texts = []
        processed_count = 0
        
        # Verarbeitung in Chunks
        for i in range(0, len(all_files), chunk_size):
            chunk_files = all_files[i:i + chunk_size]
            
            self.logger.info(f"📦 Verarbeite Chunk {i//chunk_size + 1}: "
                           f"{len(chunk_files)} Dateien")
            
            # Parallel verarbeiten
            with ProcessPoolExecutor(max_workers=min(num_workers, len(chunk_files))) as executor:
                results = list(executor.map(self._process_single_file, chunk_files))
            
            # Ergebnisse sammeln
            for result in results:
                if result['success']:
                    all_processed_texts.extend(result['texts'])
                    self.stats.processed_files += 1
                    self.stats.duplicates_found += result['duplicates_removed']
                else:
                    self.stats.error_files += 1
                    self.error_files.append({
                        'file': result['file_path'],
                        'error': result['error']
                    })
            
            processed_count += len(chunk_files)
            progress = processed_count / len(all_files) * 100
            self.logger.info(f"📊 Fortschritt: {progress:.1f}% "
                           f"({processed_count}/{len(all_files)} Dateien)")
        
        # Statistiken berechnen
        self.stats.total_texts = len(all_processed_texts)
        self.stats.processing_time = time.time() - start_time
        self.stats.files_per_second = self.stats.processed_files / max(self.stats.processing_time, 1)
        
        # Output speichern
        timestamp = int(time.time())
        output_file = output_dir / f"veritas_batch_processed_{timestamp}.jsonl"
        
        self.logger.info(f"💾 Speichere {len(all_processed_texts)} Texte in: {output_file}")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            for text in all_processed_texts:
                json.dump({"text": text}, f, ensure_ascii=False)
                f.write('\n')
        
        # Statistiken speichern
        stats_file = output_dir / f"veritas_batch_stats_{timestamp}.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(self.stats.to_dict(), f, indent=2, ensure_ascii=False)
        
        # Fehler-Log speichern
        if self.error_files:
            error_file = output_dir / f"veritas_batch_errors_{timestamp}.json"
            with open(error_file, 'w', encoding='utf-8') as f:
                json.dump(self.error_files, f, indent=2, ensure_ascii=False)
        
        # Abschlussbericht
        self._print_summary()
        
        return self.stats
    
    def _print_summary(self):
        """Druckt Zusammenfassung der Verarbeitung"""
        self.logger.info("="*60)
        self.logger.info("📊 VERITAS BATCH-PROCESSING ABGESCHLOSSEN")
        self.logger.info("="*60)
        self.logger.info(f"📁 Dateien gesamt: {self.stats.total_files}")
        self.logger.info(f"✅ Erfolgreich verarbeitet: {self.stats.processed_files}")
        self.logger.info(f"❌ Fehler: {self.stats.error_files}")
        self.logger.info(f"🔄 Duplikate entfernt: {self.stats.duplicates_found}")
        self.logger.info(f"📝 Texte extrahiert: {self.stats.total_texts}")
        self.logger.info(f"⏱️ Verarbeitungszeit: {self.stats.processing_time:.2f} Sekunden")
        self.logger.info(f"🚀 Geschwindigkeit: {self.stats.files_per_second:.2f} Dateien/Sekunde")
        self.logger.info(f"✨ Erfolgsrate: {self.stats.processed_files/max(self.stats.total_files,1)*100:.1f}%")
        self.logger.info("="*60)

def main():
    """Hauptfunktion"""
    parser = argparse.ArgumentParser(description="CLARA Veritas Batch Processor")
    parser.add_argument("--config", type=str, 
                       default="../configs/veritas_batch_config.yaml",
                       help="Pfad zur Batch-Konfiguration")
    # Neuer Standard: Globales Datenverzeichnis Y:\data\  (überschreibbar per --input oder ENV CLARA_DATA_DIR)
    default_data_dir = os.environ.get("CLARA_DATA_DIR", "Y:\\data\\")
    parser.add_argument("--input", type=str,
                       default=default_data_dir,
                       help="Eingabe-Verzeichnis (Standard: Y:\\data\\ oder ENV CLARA_DATA_DIR)")
    parser.add_argument("--output", type=str,
                       default="data/veritas_processed/",
                       help="Ausgabe-Verzeichnis")
    parser.add_argument("--dry-run", action="store_true",
                       help="Nur Analyse ohne Verarbeitung")
    
    args = parser.parse_args()
    
    # Processor initialisieren
    try:
        processor = VeritasBatchProcessor(args.config)
        
        if args.dry_run:
            processor.logger.info("🔍 DRY-RUN Modus - Nur Analyse")
            input_dir = Path(args.input)
            files = processor._find_all_files(input_dir)
            processor.logger.info(f"📊 Würde {len(files)} Dateien verarbeiten")
        else:
            # Vollständige Verarbeitung
            stats = processor.process_batch(args.input, args.output)
            
            # Erfolgsmeldung
            if stats.processed_files > 0:
                processor.logger.info(f"🎉 Batch-Processing erfolgreich abgeschlossen!")
                processor.logger.info(f"📄 Output bereit für CLARA-Training")
                processor.logger.info(f"🚀 Nächster Schritt: python scripts/clara_train_lora.py --config configs/veritas_config.yaml")
            else:
                processor.logger.error("❌ Keine Dateien erfolgreich verarbeitet")
                
    except Exception as e:
        logging.error(f"❌ Kritischer Fehler: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
