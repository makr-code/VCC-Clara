# CLARA Batch-Processing Quick Reference

## 🚀 Sofort-Verwendung

### Für Y:\data\ (Empfohlen)
```cmd
# Windows: Einfach doppelklicken
start_veritas_batch.bat
```

## 📋 Kommandozeilen-Syntax

### 1. Veritas-Processor (Rechtsdokumente)
```bash
# Standard-Syntax
python scripts/veritas_batch_processor.py --input "PFAD" --output "OUTPUT" --config "CONFIG"

# Beispiele:
python scripts/veritas_batch_processor.py --input "Y:\data\" --output "data/veritas_processed/" --config "configs/veritas_batch_config.yaml"

python scripts/veritas_batch_processor.py --input "Y:\data\" --config "configs/veritas_batch_config.yaml" --dry-run
```

### 2. Smart-Processor (mit Cache)
```bash
# Standard-Syntax (positionelle Parameter!)
python scripts/smart_batch_processor.py "INPUT_DIR" "OUTPUT_DIR" [Optionen]

# Beispiele:
python scripts/smart_batch_processor.py "Y:\data\" "data/processed/" --remove-duplicates --num-processes 8

python scripts/smart_batch_processor.py "data/test_batch/" "data/smart_output/" --max-files 1000

# Cache-Verwaltung:
python scripts/smart_batch_processor.py --cache-stats
python scripts/smart_batch_processor.py --clear-cache
```

### 3. Legacy-Processor (einfach)
```bash
# Standard-Syntax
python scripts/batch_process_data.py --input "PFAD" --output "OUTPUT" [Optionen]

# Beispiele:
python scripts/batch_process_data.py --input "Y:\data\" --output "data/batch_processed/" --num-processes 12

python scripts/batch_process_data.py --input "data/test/" --output "data/out/" --remove-duplicates
```

## ⚠️ Häufige Fehler vermeiden

### ❌ FALSCH (Smart-Processor):
```bash
python scripts/smart_batch_processor.py --input "Y:\data\" --output "data/processed/"
# Fehler: unrecognized arguments: --input
```

### ✅ RICHTIG (Smart-Processor):
```bash
python scripts/smart_batch_processor.py "Y:\data\" "data/processed/"
# Positionelle Parameter verwenden!
```

### ❌ FALSCH (Veritas-Processor):
```bash
python scripts/veritas_batch_processor.py --input "Y:\data\" --output "data/processed/"
# Fehler: No such file or directory: 'configs/veritas_batch_config.yaml'
```

### ✅ RICHTIG (Veritas-Processor):
```bash
python scripts/veritas_batch_processor.py --input "Y:\data\" --output "data/processed/" --config "configs/veritas_batch_config.yaml"
# Konfigurationsdatei angeben!
```

## 🎯 Für Y:\data\ empfohlen:

```bash
# Option 1: Windows Batch-Script (am einfachsten)
start_veritas_batch.bat

# Option 2: Direkt mit Python (für Experten)
python scripts/veritas_batch_processor.py --input "Y:\data\" --output "data/veritas_processed/" --config "configs/veritas_batch_config.yaml"

# Option 3: Smart-Processor mit Cache (bei wiederholter Verarbeitung)
python scripts/smart_batch_processor.py "Y:\data\" "data/smart_processed/" --remove-duplicates --num-processes 8
```

## 📊 Nach der Verarbeitung:

```bash
# Training starten mit verarbeiteten Daten
python scripts/clara_train_lora.py --config configs/veritas_config.yaml

# API mit kontinuierlichem Lernen starten
python scripts/clara_api.py

# Status prüfen
python scripts/quick_status.py
```

---
**💡 Tipp**: Starten Sie immer mit einem Dry-Run bei großen Datenmengen!

> Migration: Frühere Dokumentation und Beispiele verwendeten `Y:\veritas\data`. Dieses Verzeichnis wurde konsolidiert zu `Y:\data`. Falls Ihr Altbestand noch unter dem alten Pfad liegt, können Sie den Processor weiterhin mit `--input "Y:\veritas\data"` aufrufen oder die Daten unverändert (nur kopieren, nicht verschieben) nach `Y:\data` replizieren.
