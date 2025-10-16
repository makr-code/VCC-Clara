"""
Ollama-Konvertierungsskript
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path to import src modules
script_dir = Path(__file__).parent
project_root = script_dir.parent
sys.path.insert(0, str(project_root))

from src.utils.model_utils import save_model_for_ollama, list_ollama_models
from src.utils.logger import setup_logger

def main(args):
    """Hauptfunktion für Ollama-Konvertierung."""
    
    logger = setup_logger(__name__)
    
    if args.list:
        logger.info("Verfügbare Ollama-Modelle:")
        list_ollama_models()
        return
    
    if not args.model:
        logger.error("Modell-Pfad muss angegeben werden (--model)")
        return
    
    model_path = Path(args.model)
    if not model_path.exists():
        logger.error(f"Modell-Pfad nicht gefunden: {model_path}")
        return
    
    logger.info(f"Konvertiere Modell für Ollama: {model_path}")
    
    try:
        save_model_for_ollama(
            model_path=str(model_path),
            ollama_output_path=args.output,
            model_name=args.name,
            base_model=args.base_model
        )
        
        logger.info(f"Konvertierung erfolgreich! Modell verfügbar als: {args.name}")
        logger.info("Testen Sie das Modell mit: ollama run " + args.name)
        
    except Exception as e:
        logger.error(f"Konvertierung fehlgeschlagen: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Konvertiere trainiertes Modell für Ollama")
    parser.add_argument("--model", type=str, help="Pfad zum trainierten Modell")
    parser.add_argument("--output", type=str, default="ollama_models/",
                       help="Ausgabeverzeichnis für Ollama-Modell")
    parser.add_argument("--name", type=str, default="verwllm",
                       help="Name für das Ollama-Modell")
    parser.add_argument("--base-model", type=str,
                       help="Basis-Modell (falls nicht automatisch erkannt)")
    parser.add_argument("--list", action="store_true",
                       help="Liste verfügbare Ollama-Modelle auf")
    
    args = parser.parse_args()
    main(args)
