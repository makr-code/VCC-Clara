# SICHERE BATCH-VERARBEITUNG - SCHNELLREFERENZ

## 🔒 SICHERHEITSGARANTIE
**ALLE Batch-Prozessoren in CLARA garantieren:**
- Original-Dateien werden NIEMALS geändert, verschoben oder gelöscht
- Nur SQLite-Datenbank verfolgt Verarbeitungsstatus
- 100% sichere Datei-Verarbeitung

## 📋 VERFÜGBARE BATCH-PROZESSOREN

### 1. Smart Batch Processor (EMPFOHLEN)
**Datei:** `scripts/smart_batch_processor.py`
**Besonderheiten:** SQLite-basierte sichere Verfolgung, Multiprocessing

```powershell
# Basis-Verarbeitung
python smart_batch_processor.py "Y:\data" "Y:\verwLLM\data\processed"

# Mit Optionen
python smart_batch_processor.py "Y:\data" "Y:\verwLLM\data\processed" --max-files 100 --remove-duplicates

# Datenbank-Management
python smart_batch_processor.py --db-stats
python smart_batch_processor.py --clear-db
```

### 2. Veritas Batch Processor
**Datei:** `scripts/veritas_batch_processor.py`
**Besonderheiten:** YAML-Konfiguration, PDF/Word-Support, GUI

```powershell
# YAML-basierte Verarbeitung
python veritas_batch_processor.py --config configs/veritas_batch_config.yaml

# Windows GUI (falls verfügbar)
python veritas_batch_processor.py --gui
```

### 3. Standard Batch Processor
**Datei:** `scripts/batch_process_data.py`
**Besonderheiten:** Einfache Verarbeitung, named parameters

```powershell
# Named parameters
python batch_process_data.py --input "Y:\data" --output "Y:\verwLLM\data\processed"
```

## 🚀 EMPFOHLENER WORKFLOW

### Schritt 1: Sichere Verarbeitung mit Smart Batch Processor
```powershell
cd Y:\verwLLM\scripts
python smart_batch_processor.py "Y:\data" "Y:\verwLLM\data\processed" --remove-duplicates
```

### Schritt 2: Datenbank-Status prüfen
```powershell
python smart_batch_processor.py --db-stats
```

### Schritt 3: Training vorbereiten
```powershell
cd Y:\verwLLM
python scripts/prepare_data.py "data\processed\batch_processed_*.jsonl" "data\training_batches\batch_001.jsonl"
```

### Schritt 4: LoRA Training starten
```powershell
python scripts/clara_train_lora.py --config configs/lora_config.yaml
```

## 🔧 PARAMETER-OPTIONEN

### Smart Batch Processor Parameter
- `--model-name`: Tokenizer-Modell (Standard: microsoft/DialoGPT-medium)
- `--max-length`: Maximale Sequenzlänge (Standard: 1024)
- `--max-files`: Maximale Dateienanzahl (Standard: unbegrenzt)
- `--max-file-size`: Maximale Dateigröße in MB (Standard: 50)
- `--num-processes`: Parallele Prozesse (Standard: 4)
- `--remove-duplicates`: Duplikate entfernen
- `--force-reprocess`: Alle Dateien neu verarbeiten
- `--db-stats`: Datenbank-Statistiken anzeigen
- `--clear-db`: Datenbank zurücksetzen

### Veritas Batch Processor Parameter
- `--config`: YAML-Konfigurationsdatei
- `--input-dir`: Input-Verzeichnis (überschreibt YAML)
- `--output-dir`: Output-Verzeichnis (überschreibt YAML)
- `--batch-size`: Batch-Größe (überschreibt YAML)
- `--gui`: Windows GUI starten

### Standard Batch Processor Parameter
- `--input`: Input-Verzeichnis
- `--output`: Output-Verzeichnis
- `--batch-size`: Batch-Größe
- `--model-name`: Tokenizer-Modell

## 📊 DATENBANK-MANAGEMENT

### Statistiken anzeigen
```powershell
python smart_batch_processor.py --db-stats
```

### Datenbank zurücksetzen (bei Problemen)
```powershell
python smart_batch_processor.py --clear-db
```

### Datenbank-Datei direkt verwalten
```powershell
python safe_processing_db.py --stats
python safe_processing_db.py --export "backup.json"
python safe_processing_db.py --clear
```

## ⚠️ FEHLERBEHEBUNG

### Problem: Import-Fehler bei safe_processing_db
**Lösung:** Stelle sicher, dass `safe_processing_db.py` im `scripts/` Verzeichnis ist

### Problem: "Datei bereits verarbeitet"
**Lösung:** 
```powershell
python smart_batch_processor.py --force-reprocess "input" "output"
```

### Problem: Zu viele Dateien
**Lösung:**
```powershell
python smart_batch_processor.py "input" "output" --max-files 1000
```

### Problem: Große Dateien
**Lösung:**
```powershell
python smart_batch_processor.py "input" "output" --max-file-size 100
```

## 📁 TYPISCHE PFADE

### Input-Verzeichnisse
- `Y:\data` - Hauptdatenverzeichnis (Migration: früher `Y:\veritas\data`)
- `Y:\verwLLM\data\test_batch` - Test-Dateien

### Output-Verzeichnisse  
- `Y:\verwLLM\data\processed` - Verarbeitete Daten
- `Y:\verwLLM\data\training_batches` - Training-bereite Batches

### Konfigurationen
- `Y:\verwLLM\configs\veritas_batch_config.yaml` - Veritas Batch Config
- `Y:\verwLLM\configs\lora_config.yaml` - LoRA Training Config

## 🎯 BEST PRACTICES

1. **Immer Smart Batch Processor verwenden** für maximale Sicherheit
2. **Kleine Test-Runs** vor großen Verarbeitungen
3. **Regelmäßige Datenbank-Statistiken** prüfen
4. **Duplikate entfernen** für bessere Datenqualität
5. **Backup der Datenbank** vor großen Änderungen

## 🔄 KONTINUIERLICHER WORKFLOW

```powershell
# 1. Neue Dateien verarbeiten
python smart_batch_processor.py "Y:\data" "Y:\verwLLM\data\processed" --remove-duplicates

# 2. Status prüfen
python smart_batch_processor.py --db-stats

# 3. Training-Batch erstellen
python prepare_data.py "data\processed\batch_processed_*.jsonl" "data\training_batches\batch_001.jsonl"

# 4. Training starten
python clara_train_lora.py --config configs/lora_config.yaml
```

Dies garantiert sichere, effiziente Verarbeitung ohne Risiko für Original-Dateien!
