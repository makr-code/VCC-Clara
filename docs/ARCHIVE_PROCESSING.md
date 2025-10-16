# CLARA Archive Processing Guide

## 🗜️ Archive-Verarbeitung für CLARA LLM Training

CLARA unterstützt jetzt die vollautomatische Verarbeitung von komprimierten Archiven für das Training. Diese Anleitung zeigt, wie Sie große Mengen von Dokumenten aus Archiven extrahieren und für das LoRA/QLoRA Training vorbereiten.

## 📦 Unterstützte Archive-Formate

- **ZIP** - Standard Windows-Archive
- **TAR/TAR.GZ** - Linux/Unix Archive mit und ohne Kompression
- **RAR** - WinRAR Archive
- **7Z** - 7-Zip Archive
- **GZIP** - Einzelne komprimierte Dateien
- **BZIP2** - Alternative Kompression
- **XZ** - Moderne Kompression

## 🚀 Schnellstart

### 1. Archive vorbereiten
```bash
# Archive ins Verzeichnis kopieren
mkdir data\archives
copy "C:\Ihre\Archive\*.zip" data\archives\
```

### 2. Archive scannen
```bash
python scripts\archive_manager.py --scan
```

### 3. Einzelnes Archiv verarbeiten
```bash
python scripts\process_archives.py --input data\archives\dokumente.zip --output data\archive_processed
```

### 4. Alle Archive verarbeiten
```bash
python scripts\archive_manager.py --generate-script
PowerShell -ExecutionPolicy Bypass -File process_archives_batch.ps1
```

## 🛠️ Detaillierte Verwendung

### Archive Manager
Der Archive Manager bietet eine Übersicht über alle Archive:

```bash
# Status und Übersicht anzeigen
python scripts\archive_manager.py --scan

# Bereits erstellte Batch-Dateien auflisten
python scripts\archive_manager.py --list-batches

# Verarbeitungsreihenfolge empfehlen
python scripts\archive_manager.py --recommend

# PowerShell-Script für automatische Verarbeitung erstellen
python scripts\archive_manager.py --generate-script
```

### Archive Processor
Direkte Verarbeitung von Archiven:

```bash
# Einzelnes Archiv verarbeiten
python scripts\process_archives.py --input pfad\zum\archiv.zip --output data\processed

# Optionen:
--batch-size 1000          # Texte pro Batch-Datei
--file-types .txt .md .pdf  # Unterstützte Dateitypen
--max-files 10000          # Maximum Dateien pro Archiv
--list-archives            # Nur Informationen anzeigen, nicht verarbeiten
```

### Processing Monitor
Überwachung laufender Verarbeitung:

```bash
# Monitor starten
python scripts\monitor_archive_processing.py

# Mit angepasstem Update-Intervall
python scripts\monitor_archive_processing.py --interval 60
```

## 📊 Typische Workflows

### Workflow 1: Kleine Archive (< 100 MB)
```bash
# 1. Archive ins Verzeichnis kopieren
copy "*.zip" data\archives\

# 2. Status prüfen
python scripts\archive_manager.py --scan

# 3. Alle kleine Archive automatisch verarbeiten
python scripts\archive_manager.py --generate-script
PowerShell -ExecutionPolicy Bypass -File process_archives_batch.ps1
```

### Workflow 2: Große Archive (> 1 GB)
```bash
# 1. Einzelnes großes Archiv testen
python scripts\process_archives.py --input data\archives\grosses_archiv.zip --list-archives

# 2. Monitor starten
python scripts\monitor_archive_processing.py

# 3. In separatem Terminal verarbeiten
python scripts\process_archives.py --input data\archives\grosses_archiv.zip --output data\archive_processed --batch-size 500
```

### Workflow 3: Inkrementelle Verarbeitung
```bash
# 1. Bereits verarbeitete Archive identifizieren
python scripts\archive_manager.py --scan

# 2. Nur neue Archive verarbeiten
python scripts\archive_manager.py --generate-script

# 3. Training mit neuen Batches
python scripts\incremental_trainer.py --data-dir data\archive_processed
```

## ⚙️ Konfiguration

### Extraktions-Verhalten
**Standard (empfohlen)**: Archive werden neben der Original-Datei entpackt
```bash
# Erstellt: dokumente_extracted/ neben dokumente.zip
python scripts\process_archives.py --input dokumente.zip --output processed
```

**Temporäre Verzeichnisse**: Für große Archive oder begrenzte Speicher
```bash
# Verwendet temporäres Verzeichnis
python scripts\process_archives.py --input archiv.zip --use-temp --temp-dir D:\temp --output processed
```

**Extrahierte Dateien behalten**:
```bash
# Extrahierte Dateien bleiben nach Verarbeitung (Standard)
python scripts\process_archives.py --input archiv.zip --keep-extracted --output processed

# Extrahierte Dateien löschen nach Verarbeitung
python scripts\process_archives.py --input archiv.zip --output processed
# (Automatisches Aufräumen nur bei --use-temp)
```

### Batch-Größen
- **Kleine Systeme (< 8GB RAM)**: 500-1000 Texte pro Batch
- **Mittlere Systeme (8-16GB RAM)**: 1000-2000 Texte pro Batch  
- **Große Systeme (> 16GB RAM)**: 2000-5000 Texte pro Batch

### Dateitypen
Standardmäßig unterstützt:
- `.txt` - Einfache Textdateien
- `.md` - Markdown-Dateien
- `.pdf` - PDF-Dokumente (erfordert PyPDF2)
- `.docx` - Word-Dokumente (erfordert python-docx)
- `.json` - JSON-Dateien

### Speicher-Management
```bash
# Archive am gleichen Ort entpacken (Standard, platzsparend)
python scripts\process_archives.py --input archiv.zip --output processed

# Temporäres Verzeichnis für große Archive (automatisches Aufräumen)
python scripts\process_archives.py --input archiv.zip --use-temp --temp-dir D:\temp --output processed

# Schnelle SSD für temporäre Extraktion
python scripts\process_archives.py --input archiv.zip --use-temp --temp-dir C:\temp\clara --output processed
```

## 🔧 Problembehandlung

### Häufige Probleme

**1. Archive nicht erkannt**
```bash
# Prüfen Sie unterstützte Formate
python -c "from src.data.archive_processor import ArchiveProcessor; print(list(ArchiveProcessor().archive_handlers.keys()))"
```

**2. Speicher-Probleme**
```bash
# Kleinere Batch-Größe verwenden
python scripts\process_archives.py --batch-size 100 --input archiv.zip --output processed
```

**3. RAR-Archive nicht unterstützt**
```bash
# RAR-Unterstützung installieren
pip install rarfile
# WinRAR muss installiert sein oder unrar-Tool verfügbar
```

**4. Langsame Verarbeitung**
```bash
# Monitoring aktivieren um Fortschritt zu verfolgen
python scripts\monitor_archive_processing.py --interval 10
```

### Performance-Optimierung

**SSD verwenden**
```bash
# Temporäres Verzeichnis auf SSD
python scripts\process_archives.py --temp-dir C:\temp\clara --input archiv.zip
```

**Parallele Verarbeitung**
```bash
# Mehrere Archive gleichzeitig (in separaten Terminals)
python scripts\process_archives.py --input archiv1.zip --output batch1 &
python scripts\process_archives.py --input archiv2.zip --output batch2 &
```

## 📈 Monitoring und Statistiken

### Verarbeitungsstatistiken
```bash
# Detaillierte Archive-Übersicht
python scripts\archive_manager.py --scan

# Monitor mit Echtzeit-Updates
python scripts\monitor_archive_processing.py
```

### Training-Integration
Nach der Archive-Verarbeitung können die Batch-Dateien direkt ins Training:

```bash
# Alle Archive-Batches für Training vorbereiten
python scripts\batch_trainer.py --input data\archive_processed --output data\training_batches

# Training mit Archive-Daten starten
python scripts\clara_train_lora.py --config configs\archive_training_config.yaml
```

## 🎯 Best Practices

1. **Kleine Archive zuerst** - Testen Sie mit kleinen Archiven
2. **Monitoring verwenden** - Überwachen Sie große Verarbeitungen
3. **Batch-Größen anpassen** - Je nach verfügbarem Speicher
4. **Temporäre Verzeichnisse** - Nutzen Sie schnelle SSDs
5. **Inkrementell arbeiten** - Verarbeiten Sie Archive schrittweise
6. **Backups machen** - Sichern Sie verarbeitete Daten

## 🔗 Weiterführende Schritte

Nach der Archive-Verarbeitung:

1. **Training vorbereiten**: `python scripts\batch_trainer.py`
2. **Konfiguration anpassen**: Editieren Sie `configs\archive_training_config.yaml`
3. **Training starten**: `python scripts\clara_train_lora.py`
4. **Modell konvertieren**: `python scripts\convert_to_ollama.py`

---

*Erstellt für CLARA - Cognitive Legal and Administrative Reasoning Assistant*
