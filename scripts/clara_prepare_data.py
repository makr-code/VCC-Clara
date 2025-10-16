"""
Datenvorbereitungsskript für Verwaltungstexte
"""

import argparse
import json
import sys
from pathlib import Path
from transformers import AutoTokenizer

# Add parent directory to path to import src modules
script_dir = Path(__file__).parent
project_root = script_dir.parent
sys.path.insert(0, str(project_root))

from src.data.data_processor import VerwaltungsDataProcessor
from src.utils.logger import setup_logger

def main(args):
    """Hauptfunktion für Datenvorbereitung."""
    
    logger = setup_logger(__name__)
    logger.info("Starte Datenvorbereitung...")
    
    # Tokenizer laden
    tokenizer = AutoTokenizer.from_pretrained(args.model_name)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    # Data Processor erstellen
    processor = VerwaltungsDataProcessor(
        tokenizer=tokenizer,
        max_length=args.max_length
    )
    
    # Input-Pfad prüfen
    input_path = Path(args.input)
    if not input_path.exists():
        # Beispieldaten erstellen wenn Input nicht existiert
        logger.info(f"Input-Pfad {input_path} nicht gefunden. Erstelle Beispieldaten...")
        input_path.parent.mkdir(parents=True, exist_ok=True)
        processor.create_sample_data(str(input_path), args.num_samples)
    
    # Prüfe ob es ein Verzeichnis ist
    if input_path.is_dir():
        logger.info(f"Verarbeite alle Dateien aus Verzeichnis: {input_path}")
        logger.info("Dies kann bei vielen Dateien einige Zeit dauern...")
    else:
        logger.info(f"Verarbeite einzelne Datei: {input_path}")
    
    # Daten verarbeiten
    logger.info(f"Starte Datenverarbeitung...")
    dataset = processor.load_and_process(str(input_path))
    
    # Output-Verzeichnis erstellen
    output_path = Path(args.output)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Dataset speichern
    output_file = output_path / "verwaltung_train.jsonl"
    
    # Als JSONL speichern
    with open(output_file, 'w', encoding='utf-8') as f:
        for item in dataset:
            # Text rekonstruieren für bessere Lesbarkeit
            text = tokenizer.decode(item['input_ids'], skip_special_tokens=True)
            json.dump({"text": text}, f, ensure_ascii=False)
            f.write('\n')
    
    logger.info(f"Verarbeitete Daten gespeichert in: {output_file}")
    logger.info(f"Anzahl Samples: {len(dataset)}")
    
    # Statistiken
    total_tokens = sum(len(item['input_ids']) for item in dataset)
    avg_tokens = total_tokens / len(dataset)
    
    logger.info(f"Durchschnittliche Token-Länge: {avg_tokens:.1f}")
    logger.info(f"Gesamtanzahl Token: {total_tokens}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Datenvorbereitung für VerwLLM")
    parser.add_argument("--input", type=str, default="data/raw/verwaltung_texte.txt",
                       help="Pfad zur Input-Datei")
    parser.add_argument("--output", type=str, default="data/processed/",
                       help="Ausgabeverzeichnis")
    parser.add_argument("--model-name", type=str, default="microsoft/DialoGPT-medium",
                       help="Name des Basis-Modells für Tokenizer")
    parser.add_argument("--max-length", type=int, default=512,
                       help="Maximale Sequenzlänge")
    parser.add_argument("--num-samples", type=int, default=100,
                       help="Anzahl Beispieldaten falls Input nicht existiert")
    
    args = parser.parse_args()
    main(args)
