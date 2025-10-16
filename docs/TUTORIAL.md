# CLARA - Komplette Anleitung 2025
*Cognitive Legal and Administrative Reasoning Assistant*

## 🚀 Schnellstart-Anleitung

### 1. Umgebung vorbereiten

```bash
# Abhängigkeiten installieren
pip install -r requirements.txt

# Python-Umgebung konfigurieren (automatisch)
# CLARA erkennt automatisch Ihre Hardware und optimiert die Konfiguration
```

### 2. CLARA API starten (NEU! 🎉)

```bash
# Kontinuierliche Lern-API starten
python scripts/clara_api.py

# API läuft auf: http://localhost:8000
# Dokumentation: http://localhost:8000/docs
```

### 3. Kontinuierliches Lernen mit Feedback (NEU! 🔄)

**Einzelfeedback senden:**
```bash
curl -X POST "http://localhost:8000/feedback" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Wie beantrage ich Elterngeld?",
    "response": "Sie müssen das Formular bei der Elterngeldstelle...",
    "rating": 4,
    "user_correction": "Zusätzlich sind folgende Unterlagen nötig..."
  }'
```

**Batch-Feedback für große Mengen:**
```bash
curl -X POST "http://localhost:8000/feedback/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "feedback_items": [
      {
        "question": "Frage 1",
        "response": "Antwort 1", 
        "rating": 5
      },
      {
        "question": "Frage 2",
        "response": "Antwort 2",
        "rating": 3,
        "user_correction": "Korrektur..."
      }
    ]
  }'
```

### 4. Veritas Integration (NEU! 🏛️)

```python
# Veritas-App erweitern
from scripts.veritas_integration import VeritasClaraIntegration

# Integration starten
clara = VeritasClaraIntegration()

# Automatisches Batch-Processing bei vielen Feedbacks
clara.send_batch_feedback_from_csv("user_feedback.csv")
```

### 5. Traditionelles Training (falls gewünscht)

**Für kleinere GPU (< 12GB VRAM):**
```bash
python scripts/clara_train_lora.py --config configs/lora_config.yaml
```

**Für sehr kleine GPU (< 8GB VRAM) - QLoRA verwenden:**
```bash
python scripts/train_qlora.py --config configs/qlora_config.yaml
```

**Multi-GPU Training (NEU! 🚀):**
```bash
python scripts/clara_train_multi_gpu.py --config configs/multi_gpu_config.yaml
```

### 6. Sichere Batch-Verarbeitung (NEU! 🔒)

**SICHERHEITSGARANTIE: Alle Batch-Prozessoren ändern NIEMALS Original-Dateien!**

#### Option A: Smart Batch-Processor (EMPFOHLEN - SQLite-basiert)
```bash
# Sichere Verarbeitung mit Datei-Verfolgung
python scripts/smart_batch_processor.py "Y:\data\" "data/processed/" --remove-duplicates

# Datenbank-Status prüfen
python scripts/smart_batch_processor.py --db-stats

# Datenbank zurücksetzen (bei Bedarf)
python scripts/smart_batch_processor.py --clear-db
```

#### Option B: Veritas Batch-Processor (PDF/Word-Support)
```bash
# Migration: Ursprünglich für `Y:\veritas\data` optimiert – neuer Standardpfad ist `Y:\data` (Override via ENV `CLARA_DATA_DIR`)
start_veritas_batch.bat

# Oder direkt:
python scripts/veritas_batch_processor.py --input "Y:\data\" --output "data/veritas_processed/" --config "configs/veritas_batch_config.yaml"
```

#### Option C: Standard Batch-Processor (Einfach)
```bash
# Named parameters
python scripts/batch_process_data.py --input "Y:\data\" --output "data/processed/"
```

**Unterschiede:**
- **Smart-Processor**: SQLite-Datenbank, sichere Verfolgung, Multiprocessing
- **Veritas-Processor**: PDF/Word-Support, YAML-Konfiguration, GUI verfügbar
- **Standard-Processor**: Einfachste Option, nur Text/Markdown

**Alle Prozessoren garantieren: Keine Änderung der Original-Dateien!**

### 7. Modell in Ollama integrieren

```bash
# Trainiertes Modell für Ollama konvertieren
python scripts/convert_to_ollama.py --model models/lora_outputs/checkpoint-XXX --name clara-v1

# Modell testen
ollama run clara-v1 "Was ist ein Verwaltungsakt?"
```

## 🔄 Kontinuierliches Lernen - Das Herzstück von CLARA

### Live-Lernen während der Nutzung

**CLARA lernt automatisch aus jeder Interaktion:**

1. **Benutzer stellt Frage** → CLARA antwortet
2. **Feedback wird gesammelt** → Rating + Korrekturen 
3. **Automatisches Training** → Modell wird besser
4. **Verbesserte Antworten** → Höhere Qualität

**Live-Demo starten:**
```bash
python scripts/live_demo.py
```

### Kontinuierliches Training konfigurieren

```yaml
# In configs/continuous_config.yaml
continuous_learning:
  buffer_size: 100          # Warte auf 100 Feedbacks
  training_interval: 3600   # Trainiere alle Stunde
  auto_save: true          # Speichere Checkpoints
  quality_threshold: 0.6   # Mindest-Rating für Training
```

## 📊 Batch-Processing für große Datenmengen

### Veritas-Batch-Processing (Empfohlen für Rechtsdokumente)

**Für das Y:\data\ Verzeichnis (früher Y:\veritas\data):**

```bash
# Einfachste Option: Windows Batch-Script
start_veritas_batch.bat
# → Option 2 wählen (Standard-Verarbeitung)

# Direkt mit Python:
python scripts/veritas_batch_processor.py \
  --input "Y:\data\" \
  --output "data/veritas_processed/" \
  --config "configs/veritas_batch_config.yaml"

# Dry-Run (nur Analyse):
python scripts/veritas_batch_processor.py \
  --input "Y:\data\" \
  --config "configs/veritas_batch_config.yaml" \
  --dry-run
```

### Smart-Batch-Processing (Allgemein mit Cache)

**Für beliebige Verzeichnisse mit Text/Markdown:**

```bash
# Syntax: INPUT_DIR OUTPUT_DIR [Optionen]
python scripts/smart_batch_processor.py "Y:\data\" "data/processed/" --remove-duplicates --num-processes 8

# Mit erweiterten Optionen:
python scripts/smart_batch_processor.py "Y:\data\" "data/processed/" \
  --max-file-size 100 \
  --max-files 50000 \
  --remove-duplicates \
  --force-reprocess

# Cache-Verwaltung:
python scripts/smart_batch_processor.py --cache-stats  # Zeige Statistiken
python scripts/smart_batch_processor.py --clear-cache  # Cache löschen
```

### Legacy Batch-Processing

**Für einfache Fälle:**

```bash
# Standard Batch-Processing
python scripts/batch_process_data.py \
  --input "Y:\data\" \
  --output "data/batch_processed/" \
  --num-processes 12 \
  --max-files 100000
```

### Batch-Processor Vergleich

| Feature | Veritas-Processor | Smart-Processor | Legacy-Processor |
|---------|-------------------|-----------------|------------------|
| **Dateiformate** | PDF, Word, Markdown, JSON, CSV | Text, Markdown | Text, JSON, CSV |
| **Konfiguration** | YAML-Datei | Kommandozeilen-Parameter | Kommandozeilen-Parameter |
| **Rechtsspezifisch** | ✅ Ja (Zitate, Struktur) | ❌ Nein | ❌ Nein |
| **Cache-System** | ❌ Nein | ✅ Ja (intelligent) | ❌ Nein |
| **Duplikatserkennung** | ✅ Content-Hash | ✅ Set-basiert | ✅ Set-basiert |
| **Qualitätsfilterung** | ✅ KI-basiert | ❌ Größe-basiert | ❌ Länge-basiert |
| **Multi-Processing** | ✅ Chunk-basiert | ✅ Batch-basiert | ✅ File-basiert |
| **Windows GUI** | ✅ start_veritas_batch.bat | ❌ Nein | ❌ Nein |
| **Parameter-Syntax** | `--input --output --config` | `INPUT_DIR OUTPUT_DIR` | `--input --output` |
| **Empfohlen für** | Y:\data\ (Migration) | Cache-intensive Projekte | Einfache Projekte |

### Empfehlung:

- **🏛️ Rechtsdokumente**: Verwenden Sie den **Veritas-Processor**
- **🔄 Wiederholte Verarbeitung**: Verwenden Sie den **Smart-Processor**  
- **� Einmalige Verarbeitung**: Verwenden Sie den **Legacy-Processor**

```bash
# Automatische Archiv-Extraktion
python scripts/process_archives.py \
  --input archives/ \
  --output data/extracted/ \
  --recursive \
  --formats zip,tar,rar,7z
```

### Monitoring

```bash
# Live-Monitoring des Batch-Processing
python scripts/monitor_archive_processing.py

# Training-Status überwachen
python scripts/quick_status.py
```

## 📋 API-Endpunkte (CLARA REST API)

### Feedback-Endpoints

**Einzelfeedback:**
```http
POST /feedback
{
  "question": "Wie beantrage ich Kindergeld?",
  "response": "Sie müssen Formular KG1 ausfüllen...",
  "rating": 4,
  "user_correction": "Zusätzlich benötigen Sie eine Geburtsurkunde"
}
```

**Batch-Feedback:**
```http
POST /feedback/batch
{
  "feedback_items": [...],
  "batch_metadata": {
    "source": "veritas_app",
    "timestamp": "2025-08-31T10:00:00Z"
  }
}
```

### Veritas-Integration

**Frage an CLARA senden:**
```http
POST /veritas/ask
{
  "question": "Rechtliche Frage...",
  "context": "Zusätzlicher Kontext..."
}
```

**Batch-Verarbeitung für Veritas:**
```http
POST /veritas/batch_feedback
{
  "feedback_items": [...],
  "auto_train": true
}
```

### Status-Endpoints

**API-Gesundheit:**
```http
GET /health
```

**Training-Status:**
```http
GET /status/training
```

**Kontinuierliches Lernen Status:**
```http
GET /status/learning
```

## 🎯 Produktions-Deployment

### CLARA in Veritas integrieren

1. **API starten:**
```bash
# Produktions-Modus
python scripts/clara_api.py --port 8000 --host 0.0.0.0
```

2. **In Veritas-App (Y:\veritas\veritas_app.py):**
```python
from scripts.veritas_integration import VeritasClaraIntegration

# Integration einrichten
clara = VeritasClaraIntegration()

# Bei jeder Benutzer-Interaktion
def handle_user_question(question, ai_response, user_rating):
    clara.send_feedback(
        question=question,
        response=ai_response,
        rating=user_rating
    )

# Batch-Import existierender Daten
clara.import_feedback_from_csv("historical_feedback.csv")
```

### Automatisierte Workflows

**Kontinuierliches Batch-Processing:**
```bash
# Windows Task Scheduler / Cron
python scripts/clara_continuous_learning.py --daemon --interval 3600
```

**Automatisches Resume (NEU! 🔄):**
```bash
# Training wird automatisch fortgesetzt bei Unterbrechung
python scripts/resume_training.py --auto-resume
```

## 🛠️ Erweiterte Konfiguration

### 🤖 Modell-Auswahl

**CLARA unterstützt verschiedene Basismodelle - automatische Auswahl:**

```bash
# Alle verfügbaren Modelle anzeigen
python scripts/model_selector.py --list

# Optimales Modell für Ihre Hardware finden
python scripts/model_selector.py --vram 16 --language deutsch

# Automatische Konfiguration generieren
python scripts/model_selector.py --generate-config "LeoLM/leo-hessianai-7b" --method lora
```

### 🏆 Empfohlene Modelle für deutsche Verwaltung

| Modell | VRAM | Sprache | Empfehlung | Anwendung |
|--------|------|---------|------------|-----------|
| **LeoLM/leo-hessianai-7b** | 16GB | 🇩🇪 | ⭐⭐⭐⭐⭐ | **Beste Wahl für Verwaltung** |
| **DiscoResearch/DiscoLM-German-7b-v1** | 16GB | 🇩🇪 | ⭐⭐⭐⭐⭐ | **Deutsche Konversation** |
| **microsoft/DialoGPT-medium** | 4GB | 🇺🇸 | ⭐⭐⭐ | **Tests/schwache Hardware** |

### Kontinuierliches Lernen konfigurieren

```yaml
# configs/continuous_config.yaml
continuous_learning:
  enabled: true
  buffer_size: 50               # Training nach 50 Feedbacks
  training_interval: 1800       # Oder alle 30 Minuten
  quality_filter:
    min_rating: 3               # Nur Feedbacks >= 3 Sterne
    min_text_length: 10         # Mindestlänge
  auto_save_checkpoints: true
  
# Feedback-Verarbeitung
feedback:
  duplicate_detection: true     # Verhindert doppelte Feedbacks
  intelligent_filtering: true   # KI-basierte Qualitätsprüfung
  batch_processing: 
    enabled: true
    max_batch_size: 1000
    auto_process_threshold: 100
```

### Batch-Processing optimieren

```yaml
# configs/batch_config.yaml
batch_processing:
  parallel_workers: 8           # CPU-Kerne nutzen
  memory_optimization: true     # Für große Dateien
  duplicate_detection:
    method: "content_hash"      # Intelligente Duplikatserkennung
    cache_size: 10000
  quality_filtering:
    enabled: true
    ai_scoring: true           # KI bewertet Textqualität
    min_score: 0.6
```

### LoRA vs QLoRA - Wann was verwenden?

| Methode | GPU Memory | Training Zeit | Qualität | Empfehlung |
|---------|------------|---------------|----------|------------|
| **LoRA** | 12-24GB | Schneller | Höher | RTX 3090/4090, A100 |
| **QLoRA** | 6-12GB | Langsamer | Gut | RTX 3070/4070, Consumer GPUs |

### Wichtige Parameter anpassen

**In `configs/lora_config.yaml` oder `configs/qlora_config.yaml`:**

```yaml
# Speicherverbrauch reduzieren
training:
  batch_size: 1                    # Reduzieren bei GPU Memory Problemen
  gradient_accumulation_steps: 16  # Erhöhen um effektive Batch Size beizubehalten

# Qualität verbessern
lora:
  r: 32          # Höher = bessere Qualität, mehr Memory
  alpha: 64      # Meist 2*r

# Trainingszeit anpassen
training:
  num_epochs: 5  # Mehr Epochen für bessere Qualität
```

## 🔧 Problembehandlung 2025

### Häufige Probleme und Lösungen:

**API startet nicht:**
```bash
# Port prüfen
netstat -tulpn | grep :8000

# Fallback-Modus verwenden
python scripts/clara_api.py --fallback-mode
```

**Kontinuierliches Lernen funktioniert nicht:**
```bash
# Status prüfen
curl http://localhost:8000/status/learning

# Manuell neustarten
curl -X POST http://localhost:8000/admin/restart-learning
```

**Batch-Processing zu langsam:**
```bash
# Mehr Prozesse verwenden
python scripts/smart_batch_processor.py --workers 16

# Nur kleine Dateien verarbeiten
python scripts/smart_batch_processor.py --max-file-size 10MB
```

**Training bricht ab - Resume verwenden:**
```bash
# Automatisches Resume (Standard)
python scripts/clara_train_lora.py --config configs/lora_config.yaml

# Manuelles Resume von spezifischem Checkpoint
python scripts/resume_training.py --checkpoint models/lora_outputs/checkpoint-1500
```

**Veritas-Integration Probleme:**
```python
# Verbindung testen
from scripts.veritas_integration import VeritasClaraIntegration
clara = VeritasClaraIntegration()
print(clara.test_connection())

# Batch-Feedback debuggen
clara.send_batch_feedback([...], debug=True)
```

### Performance-Monitoring

```bash
# Live-Status aller Komponenten
python scripts/quick_status.py --live

# Detaillierte API-Statistiken
curl http://localhost:8000/stats/detailed

# Training-Performance
python scripts/monitor_training.py --dashboard
```

## 📚 Beispiele und Use Cases

### 1. Veritas-App Integration

**Komplette Integration in bestehende App:**
```python
# In Y:\veritas\veritas_app.py
from scripts.veritas_integration import VeritasClaraIntegration

class VeritasApp:
    def __init__(self):
        self.clara = VeritasClaraIntegration()
        
    def handle_user_question(self, question):
        # CLARA fragen
        response = self.clara.ask_question(question)
        
        # Benutzer-Feedback sammeln
        rating = self.get_user_rating(response)
        correction = self.get_user_correction()
        
        # Automatisches Lernen
        self.clara.send_feedback(
            question=question,
            response=response,
            rating=rating,
            user_correction=correction
        )
        
        return response
```

### 2. Batch-Import historischer Daten

**CSV-Import:**
```python
import pandas as pd
from scripts.veritas_integration import VeritasClaraIntegration

# Historische Daten laden
df = pd.read_csv("historical_qa_data.csv")

# Batch-Import
clara = VeritasClaraIntegration()
clara.import_dataframe(df, 
    question_col="question",
    answer_col="answer", 
    rating_col="user_rating"
)
```

### 3. Live-Demo mit kontinuierlichem Lernen

```bash
# Interaktive Demo starten
python scripts/live_demo.py

# Demo zeigt:
# - Echtzeit-Fragen und Antworten
# - Live-Feedback-Integration  
# - Kontinuierliches Modell-Update
# - Performance-Verbesserung sichtbar
```

### 4. Enterprise-Setup

**Produktions-Setup für große Organisation:**
```bash
# 1. Multi-GPU Training für bessere Performance
python scripts/clara_train_multi_gpu.py --config configs/enterprise_config.yaml

# 2. Distributed API mit Load Balancing
python scripts/clara_api.py --distributed --replicas 4

# 3. Automatisierte Batch-Jobs
python scripts/batch_trainer.py --schedule daily --auto-cleanup
```

## 🏆 Best Practices

### Für optimale Ergebnisse:

1. **Feedback-Qualität:**
   - Sammeln Sie mindestens 1000 Feedbacks vor erstem Training
   - Nutzen Sie 1-5 Sterne Rating System
   - Fordern Sie konkrete Korrekturen ein

2. **Kontinuierliches Lernen:**
   - Starten Sie mit kleineren Buffer-Größen (50-100)
   - Überwachen Sie Training-Performance
   - Nutzen Sie automatische Qualitäts-Filter

3. **Batch-Processing:**
   - Verarbeiten Sie große Datenmengen über Nacht
   - Nutzen Sie Duplicate-Detection
   - Filtern Sie qualitativ schlechte Texte

4. **API-Integration:**
   - Implementieren Sie Retry-Logic
   - Nutzen Sie Batch-Endpoints für große Mengen
   - Überwachen Sie API-Health regelmäßig

### Performance-Optimierung:

```yaml
# Produktions-optimierte Konfiguration
production:
  api:
    workers: 8                    # Concurrent requests
    timeout: 30                   # Request timeout
    rate_limiting: 1000/hour      # Pro Benutzer
    
  training:
    auto_resume: true             # Bei Fehlern weitertrainieren
    checkpoint_interval: 500      # Häufige Backups
    gradient_accumulation: 16     # Memory-effizient
    
  monitoring:
    wandb_enabled: true          # Training-Metriken
    alert_on_failure: true       # Email-Benachrichtigungen
    performance_tracking: true   # API-Performance
```

## 📚 Weitere Ressourcen

### Dokumentation:
- **CLARA API Docs**: http://localhost:8000/docs (wenn API läuft)
- **Kontinuierliches Lernen**: `docs/CONTINUOUS_LEARNING.md`
- **Veritas Integration**: `docs/VERITAS_INTEGRATION.md`
- **Archive Processing**: `docs/ARCHIVE_PROCESSING.md`

### Wissenschaftliche Papers:
- [LoRA Paper](https://arxiv.org/abs/2106.09685)
- [QLoRA Paper](https://arxiv.org/abs/2305.14314)
- [Continuous Learning in NLP](https://arxiv.org/abs/2203.06875)

### Tools und Frameworks:
- [Ollama Dokumentation](https://ollama.ai/docs)
- [Transformers Dokumentation](https://huggingface.co/docs/transformers)
- [FastAPI Dokumentation](https://fastapi.tiangolo.com/)

## 🆘 Support und Community

### Bei Problemen:

1. **Logs überprüfen:**
   ```bash
   # API-Logs
   tail -f logs/clara_api.log
   
   # Training-Logs  
   tail -f logs/training.log
   
   # Batch-Processing-Logs
   tail -f logs/batch_processing.log
   ```

2. **Diagnostics ausführen:**
   ```bash
   python scripts/import_helper.py  # Import-Probleme diagnostizieren
   python scripts/quick_status.py   # System-Status prüfen
   ```

3. **Community-Ressourcen:**
   - GitHub Issues für Bugs
   - Discussions für Fragen
   - Wiki für Anleitungen
   - Examples-Ordner für Code-Beispiele

### Enterprise Support:

Für produktive Umgebungen mit:
- Custom Training für spezielle Domänen
- Performance-Optimierung
- Security-Audits
- 24/7 Support

Kontakt: support@clara-ai.de

---

## 🚀 Zusammenfassung - CLARA 2025

**CLARA ist mehr als nur LoRA-Training:**

✅ **Kontinuierliches Lernen** - Modell wird automatisch durch Feedback besser
✅ **REST API** - Einfache Integration in bestehende Apps
✅ **Batch-Processing** - Verarbeitung riesiger Datenmengen
✅ **Veritas-Integration** - Nahtlose Einbindung in Rechtssysteme  
✅ **Intelligente Filtering** - KI-basierte Qualitätskontrolle
✅ **Multi-GPU Support** - Schnelles Training auf mehreren GPUs
✅ **Automatisches Resume** - Training wird bei Unterbrechung fortgesetzt
✅ **Archive Processing** - Automatische Extraktion aus ZIP/TAR/RAR
✅ **Duplicate Detection** - Verhindert redundantes Training
✅ **Live-Monitoring** - Echtzeit-Überwachung aller Prozesse

**Starten Sie mit:**
```bash
git clone https://github.com/your-org/clara
cd clara
pip install -r requirements.txt
python scripts/clara_api.py
```

**Ihr KI-Assistent lernt ab sofort kontinuierlich und wird täglich besser! 🎉**
