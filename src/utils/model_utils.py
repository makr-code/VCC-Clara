"""
Utility-Funktionen für Modell-Management und Ollama-Integration
"""

import os
import json
import shutil
import subprocess
import requests
from pathlib import Path
from typing import Dict, Any, Optional
import logging
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

logger = logging.getLogger(__name__)

def save_model_for_ollama(
    model_path: str, 
    ollama_output_path: str, 
    model_name: str,
    base_model: Optional[str] = None
):
    """
    Konvertiere ein trainiertes LoRA/QLoRA Modell für Ollama.
    
    Args:
        model_path: Pfad zum trainierten Modell
        ollama_output_path: Ausgabepfad für Ollama-Modell
        model_name: Name des Ollama-Modells
        base_model: Basis-Modell (falls nicht in config)
    """
    
    logger.info(f"Konvertiere Modell für Ollama: {model_path}")
    
    model_path = Path(model_path)
    ollama_output_path = Path(ollama_output_path)
    ollama_output_path.mkdir(parents=True, exist_ok=True)
    
    try:
        # LoRA-Modell und Basis-Modell laden
        if base_model is None:
            # Versuche Base-Model aus adapter_config.json zu lesen
            adapter_config_path = model_path / "adapter_config.json"
            if adapter_config_path.exists():
                with open(adapter_config_path, 'r') as f:
                    adapter_config = json.load(f)
                    base_model = adapter_config.get("base_model_name_or_path")
        
        if base_model is None:
            raise ValueError("Base model nicht gefunden. Bitte explizit angeben.")
        
        logger.info(f"Lade Basis-Modell: {base_model}")
        
        # Basis-Modell laden
        tokenizer = AutoTokenizer.from_pretrained(base_model)
        base_model_obj = AutoModelForCausalLM.from_pretrained(
            base_model,
            torch_dtype=torch.float16,
            device_map="auto"
        )
        
        # LoRA-Adapter laden und mergen
        logger.info("Merge LoRA-Adapter mit Basis-Modell...")
        model = PeftModel.from_pretrained(base_model_obj, model_path)
        merged_model = model.merge_and_unload()
        
        # Merged Modell speichern
        merged_path = ollama_output_path / "merged_model"
        merged_path.mkdir(exist_ok=True)
        
        merged_model.save_pretrained(merged_path, safe_serialization=True)
        tokenizer.save_pretrained(merged_path)
        
        logger.info(f"Merged Modell gespeichert in: {merged_path}")
        
        # Modelfile für Ollama erstellen
        create_ollama_modelfile(merged_path, ollama_output_path, model_name)
        
        # Modell in Ollama importieren
        import_to_ollama(ollama_output_path / "Modelfile", model_name)
        
        logger.info(f"Modell erfolgreich in Ollama importiert als: {model_name}")
        
    except Exception as e:
        logger.error(f"Fehler bei Ollama-Konvertierung: {e}")
        raise

def create_ollama_modelfile(
    model_path: Path, 
    output_path: Path, 
    model_name: str,
    template: Optional[str] = None,
    system_message: Optional[str] = None
):
    """
    Erstelle ein Modelfile für Ollama.
    
    Args:
        model_path: Pfad zum merged Modell
        output_path: Ausgabepfad für Modelfile
        model_name: Name des Modells
        template: Custom Template für Chat
        system_message: System-Nachricht für das Modell
    """
    
    if template is None:
        template = """{{ if .System }}<|system|>
{{ .System }}<|end|>
{{ end }}{{ if .Prompt }}<|user|>
{{ .Prompt }}<|end|>
{{ end }}<|assistant|>
{{ .Response }}<|end|>"""
    
    if system_message is None:
        system_message = """Sie sind CLARA (Cognitive Legal and Administrative Reasoning Assistant), ein spezialisierter KI-Assistent für deutsche Verwaltung und Rechtsfragen. 
Sie helfen bei:
- Behördlichen Verfahren und Anträgen
- Rechtlichen Grundlagen und Vorschriften
- Verwaltungsabläufen und Zuständigkeiten
- Formellen Anforderungen und Fristen

Antworten Sie präzise, sachlich und unter Berücksichtigung deutscher Rechtsgrundlagen."""
    
    modelfile_content = f"""FROM {model_path}

TEMPLATE \"\"\"{template}\"\"\"

SYSTEM \"\"\"{system_message}\"\"\"

PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER top_k 40
PARAMETER num_ctx 2048
PARAMETER stop "<|end|>"
PARAMETER stop "<|user|>"
PARAMETER stop "<|system|>"
"""
    
    modelfile_path = output_path / "Modelfile"
    with open(modelfile_path, 'w', encoding='utf-8') as f:
        f.write(modelfile_content)
    
    logger.info(f"Modelfile erstellt: {modelfile_path}")

def import_to_ollama(modelfile_path: Path, model_name: str):
    """
    Importiere Modell in Ollama.
    
    Args:
        modelfile_path: Pfad zum Modelfile
        model_name: Name für das Ollama-Modell
    """
    
    try:
        # Prüfe ob Ollama läuft
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code != 200:
            raise ConnectionError("Ollama ist nicht erreichbar")
        
        # Modell erstellen
        cmd = ["ollama", "create", model_name, "-f", str(modelfile_path)]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        logger.info(f"Ollama Import erfolgreich: {result.stdout}")
        
        # Modell testen
        test_ollama_model(model_name)
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Ollama Import fehlgeschlagen: {e.stderr}")
        raise
    except ConnectionError as e:
        logger.error(f"Ollama Verbindungsfehler: {e}")
        logger.info("Stellen Sie sicher, dass Ollama läuft: ollama serve")
        raise

def test_ollama_model(model_name: str, test_prompt: str = "Was ist ein Verwaltungsakt?"):
    """
    Teste das importierte Ollama-Modell.
    
    Args:
        model_name: Name des Ollama-Modells
        test_prompt: Test-Prompt
    """
    
    try:
        data = {
            "model": model_name,
            "prompt": test_prompt,
            "stream": False
        }
        
        response = requests.post(
            "http://localhost:11434/api/generate",
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"Modell-Test erfolgreich:")
            logger.info(f"Prompt: {test_prompt}")
            logger.info(f"Antwort: {result.get('response', '')[:200]}...")
        else:
            logger.error(f"Modell-Test fehlgeschlagen: {response.status_code}")
            
    except Exception as e:
        logger.error(f"Fehler beim Modell-Test: {e}")

def list_ollama_models():
    """Liste alle verfügbaren Ollama-Modelle auf."""
    try:
        response = requests.get("http://localhost:11434/api/tags")
        if response.status_code == 200:
            models = response.json().get("models", [])
            logger.info("Verfügbare Ollama-Modelle:")
            for model in models:
                logger.info(f"- {model['name']} ({model['size']})")
        else:
            logger.error("Konnte Ollama-Modelle nicht abrufen")
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Ollama-Modelle: {e}")

def delete_ollama_model(model_name: str):
    """Lösche ein Ollama-Modell."""
    try:
        cmd = ["ollama", "rm", model_name]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        logger.info(f"Modell {model_name} gelöscht: {result.stdout}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Fehler beim Löschen des Modells: {e.stderr}")

def get_model_info(model_path: str) -> Dict[str, Any]:
    """
    Hole Informationen über ein trainiertes Modell.
    
    Args:
        model_path: Pfad zum Modell
        
    Returns:
        Dict mit Modell-Informationen
    """
    
    model_path = Path(model_path)
    info = {
        "path": str(model_path),
        "exists": model_path.exists(),
        "files": [],
        "config": {},
        "adapter_config": {}
    }
    
    if model_path.exists():
        # Dateien auflisten
        info["files"] = [f.name for f in model_path.iterdir()]
        
        # Konfiguration laden
        config_path = model_path / "config.json"
        if config_path.exists():
            with open(config_path, 'r') as f:
                info["config"] = json.load(f)
        
        # Adapter-Konfiguration laden
        adapter_config_path = model_path / "adapter_config.json"
        if adapter_config_path.exists():
            with open(adapter_config_path, 'r') as f:
                info["adapter_config"] = json.load(f)
    
    return info

def cleanup_old_models(models_dir: str, keep_latest: int = 3):
    """
    Bereinige alte Modell-Checkpoints.
    
    Args:
        models_dir: Verzeichnis mit Modellen
        keep_latest: Anzahl der neuesten Modelle, die behalten werden sollen
    """
    
    models_dir = Path(models_dir)
    if not models_dir.exists():
        return
    
    # Alle Modell-Ordner finden und nach Änderungszeit sortieren
    model_dirs = [d for d in models_dir.iterdir() if d.is_dir()]
    model_dirs.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    
    # Alte Modelle löschen
    for old_model in model_dirs[keep_latest:]:
        logger.info(f"Lösche altes Modell: {old_model}")
        shutil.rmtree(old_model)

if __name__ == "__main__":
    # Beispiel-Verwendung
    list_ollama_models()
