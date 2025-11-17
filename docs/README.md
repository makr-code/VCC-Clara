# CLARA - Cognitive Legal and Administrative Reasoning Assistant

---

## 🔔 Documentation Status Notice

**⚠️ Documentation Consolidation in Progress**

The CLARA documentation is undergoing consolidation and updates. For the latest status:

- **[Documentation Consolidation Summary](./DOCUMENTATION_CONSOLIDATION_SUMMARY.md)** - Overview and action plan
- **[Documentation Inventory](./DOCUMENTATION_INVENTORY.md)** - Complete inventory of all docs
- **[Gap Analysis](./GAP_ANALYSIS.md)** - Implementation vs documentation gaps
- **[Documentation TODO](./DOCUMENTATION_TODO.md)** - 107 tasks to improve documentation

Some documentation may be outdated or contain inaccuracies. When in doubt, verify against the actual code implementation.

---

```
## 🚀 Schnellstart

### 1. Daten vorbereiten
```bash
python scripts/prepare_data.py --input data/raw/verwaltung_texte.txt --output data/processed/
```

### 2. Optimales Modell wählen (NEU!)
```bash
# Automatische Modell-Empfehlung für Ihre Hardware
python scripts/model_selector.py --vram 16 --language deutsch
```

### 3. LoRA Training starten
```bash
python scripts/clara_train_lora.py --config configs/leo_lora_config.yaml    # Deutsch (empfohlen)
# oder
python scripts/train_qlora.py --config configs/qlora_config.yaml      # Für weniger VRAM
``` █████╗ ██████╗  █████╗ 
██╔════╝██║     ██╔══██╗██╔══██╗██╔══██╗
██║     ██║     ███████║██████╔╝███████║
██║     ██║     ██╔══██║██╔══██╗██╔══██║
╚██████╗███████╗██║  ██║██║  ██║██║  ██║
 ╚═════╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝
```

CLARA ist ein spezialisiertes LoRA/QLoRA Training-System für Large Language Models (LLMs), optimiert für deutsche Verwaltungs- und Rechtsanwendungen. Als Teil des veritas/covina Ökosystems ermöglicht CLARA das effiziente Fine-Tuning von LLMs mit geringem Speicherverbrauch.

> Migration (2025-09): Das frühere Standard-Quellverzeichnis `Y:\veritas\data` wurde konsolidiert zu `Y:\data`. Alle Dokumentationen und Skripte verwenden jetzt `Y:\data` als Default. Falls Ihr Datenbestand noch im alten Pfad liegt, können Sie entweder `--input "Y:\veritas\data"` explizit angeben oder eine Kopie (nicht verschieben) nach `Y:\data` erstellen. Alternativ setzen Sie die Umgebungsvariable `CLARA_DATA_DIR`.

## 🚀 Features

- **LoRA Training**: Effizientes Fine-Tuning mit geringem Speicherverbrauch
- **QLoRA Training**: Quantisiertes Training für noch geringeren Speicherverbrauch
- **Multi-Format Support**: PDF, Word, Markdown, JSON, CSV, TXT
- **Ollama Integration**: Nahtlose Integration mit Ollama für lokales Hosting
- **Verwaltungsfokus**: Speziell angepasst für deutsche Verwaltungs- und Rechtsterminologie
- **GPU-Optimiert**: Unterstützung für CUDA und ROCm
- **Intelligente PDF-Extraktion**: OCR-fähige Textextraktion aus Behördendokumenten
- **Batch-Processing**: Parallel-Verarbeitung großer Dokumentenbestände

## 📋 Voraussetzungen

- Python 3.8+
- CUDA-fähige GPU (empfohlen) oder CPU
- Mindestens 16GB RAM (32GB empfohlen)
- Ollama installiert

## 🛠️ Installation

1. **Repository klonen und Setup ausführen:**
```bash
git clone <repository-url>
cd verwLLM
pip install -r requirements.txt
```

2. **Ollama installieren:**
```bash
# Folgen Sie den Anweisungen auf https://ollama.ai/
```

3. **Umgebung konfigurieren:**
```bash
cp .env.example .env
# Bearbeiten Sie .env mit Ihren Einstellungen
```

## 📊 Projektstruktur

```
verwLLM/
├── src/                    # Hauptquellcode
│   ├── training/          # Training-Module
│   ├── data/             # Datenverarbeitung
│   └── utils/            # Hilfsfunktionen
├── data/                  # Trainingsdaten
│   ├── raw/              # Rohdaten
│   ├── processed/        # Verarbeitete Daten
│   └── examples/         # Beispieldaten
├── models/               # Gespeicherte Modelle
├── configs/              # Konfigurationsdateien
├── scripts/              # Ausführbare Skripte
└── notebooks/            # Jupyter Notebooks
```

## 🎯 Integration mit veritas/covina

CLARA fügt sich nahtlos in das bestehende Ökosystem ein:
- **veritas**: Datenquelle und Wissensmanagement
- **covina**: Workflow-Integration und Benutzeroberfläche  
- **CLARA**: KI-gestütztes Reasoning und Textverständnis

## 🎯 Schnellstart

### 1. Daten vorbereiten
```bash
python scripts/prepare_data.py --input data/raw/verwaltung_texte.txt --output data/processed/
```

### 2. LoRA Training starten
```bash
python scripts/clara_train_lora.py --config configs/lora_config.yaml
```

### 3. QLoRA Training starten
```bash
python scripts/train_qlora.py --config configs/qlora_config.yaml
```

### 4. Modell in Ollama konvertieren
```bash
python scripts/convert_to_ollama.py --model models/lora_model --output ollama_model
```

## ⚙️ Konfiguration

Bearbeiten Sie die Konfigurationsdateien in `configs/`:
- `lora_config.yaml`: LoRA-spezifische Einstellungen für CLARA
- `qlora_config.yaml`: QLoRA-spezifische Einstellungen für CLARA
- `veritas_config.yaml`: Optimiert für große veritas-Datenverzeichnisse

### Pfadsteuerung

Sie können das Quell-Datenverzeichnis über eine Umgebungsvariable überschreiben:
```
PowerShell:
$env:CLARA_DATA_DIR = 'Y:\data'

CMD:
set CLARA_DATA_DIR=Y:\data
```
Alle Skripte, die einen Standard-Eingabepfad nutzen, prüfen zuerst `CLARA_DATA_DIR`.

## 📈 Monitoring

Das Training kann über Tensorboard überwacht werden:
```bash
tensorboard --logdir logs/
```

### 🧪 Runtime Metriken & Prometheus Export

CLARA stellt nun einen leichten Metrik-Exporter bereit:

- Counter, Gauges, Summaries (count/sum/avg) und Histogramme (manuell definierte Buckets)
- Audit Events (separat) für Routing & Serving Entscheidungen (`audit/audit_log.jsonl`)
- FastAPI Endpoint `/metrics` im Server (`clara_serve_vllm.py`) gibt Prometheus kompatiblen Plaintext zurück.

Beispiel Start (Fake-Modus ohne vLLM):
```bash
uvicorn scripts.clara_serve_vllm:app --host 0.0.0.0 --port 8001
```
Abruf der Metriken:
```bash
curl http://localhost:8001/metrics
```
Beispielauszug:
```
# TYPE clara_routing_requests_total counter
clara_routing_requests_total 12
# TYPE clara_routing_decision_seconds_sum gauge
clara_routing_decision_seconds_sum 0.143
clara_routing_decision_seconds_count 12
clara_routing_decision_seconds_avg 0.0119
clara_routing_decision_seconds_hist_bucket{le="0.01"} 5
clara_routing_decision_seconds_hist_bucket{le="0.02"} 11
clara_routing_decision_seconds_hist_bucket{le="0.05"} 12
clara_routing_decision_seconds_hist_sum 0.143
clara_routing_decision_seconds_hist_count 12
```

Prometheus `scrape_config` Beispiel:
```yaml
scrape_configs:
	- job_name: clara
		static_configs:
			- targets: ["clara-host:8001"]
		metrics_path: /metrics
```

Hinweise:
- Histogram Buckets sind aktuell statisch im Code (`observe_histogram`) hinterlegt.
- Für Produktion wird empfohlen, einen dedizierten Prometheus Aggregator oder Pushgateway nur bei Bedarf zu nutzen.
- Audit Log Rotation & Datenschutz-Konfiguration folgen in späterer Version.

## 🤝 Beitragen

Beiträge sind willkommen! Bitte lesen Sie die [CONTRIBUTING.md](CONTRIBUTING.md) für Details.

## 📄 Lizenz

Dieses Projekt steht unter der MIT-Lizenz. Siehe [LICENSE](LICENSE) für Details.

## 🆘 Support

Bei Fragen oder Problemen öffnen Sie bitte ein Issue im Repository.

---

## 📚 Documentation Index

### 🔍 Documentation Status (2025-11-17)
- **[Documentation Consolidation Summary](./DOCUMENTATION_CONSOLIDATION_SUMMARY.md)** - Executive summary and action plan
- **[Documentation Inventory](./DOCUMENTATION_INVENTORY.md)** - Complete inventory of all 55 docs
- **[Gap Analysis](./GAP_ANALYSIS.md)** - Implementation coverage (68.4%)
- **[Documentation TODO](./DOCUMENTATION_TODO.md)** - 107 tasks in 6 phases

### 🏗️ Architecture & Design
- **[System Overview](./SYSTEM_OVERVIEW.md)** - Complete system description
- **[Self-Learning LoRA System Architecture](./SELF_LEARNING_LORA_SYSTEM_ARCHITECTURE.md)** - Detailed architecture
- **[Frontend Architecture](./FRONTEND_ARCHITECTURE.md)** - Frontend v2.0 architecture
- **[Security Framework](./SECURITY_FRAMEWORK.md)** - Security & authentication
- **[Architecture Refactoring Plan](./ARCHITECTURE_REFACTORING_PLAN.md)** - Clean code refactoring

### 📖 User Guides
- **[Tutorial](./TUTORIAL.md)** - Complete guide 2025
- **[Training System Quickstart](./TRAINING_SYSTEM_QUICKSTART.md)** - Quick training guide
- **[Batch Processing Quick Reference](./BATCH_PROCESSING_QUICK_REFERENCE.md)** - Batch processing
- **[Frontend Guide](./FRONTEND_GUIDE.md)** - **PRIMARY** - Complete frontend guide (consolidated)
- **[Frontend Features Quick Reference](./FRONTEND_FEATURES_QUICK_REFERENCE.md)** - Quick feature reference

### 🔧 Implementation
- **[Implementation Summary](./IMPLEMENTATION_SUMMARY.md)** - Core implementation status
- **[Dataset Management Service](./DATASET_MANAGEMENT_SERVICE.md)** - Dataset service v1.0.0

### ✨ Features
- **[Continuous Learning](./CONTINUOUS_LEARNING.md)** - Continuous learning system
- **[Veritas Integration](./VERITAS_INTEGRATION.md)** - Veritas integration
- **[UDS3 Integration](./UDS3_INTEGRATION_COMPLETE.md)** - UDS3 integration (OPTIONAL)
- **[UDS3 Status](./UDS3_STATUS.md)** - **NEW:** UDS3 availability and requirements
- **[Archive Processing](./ARCHIVE_PROCESSING.md)** - Archive processing guide

### 🔄 Migration & History
- **[Migration Guide](./MIGRATION_GUIDE.md)** - Clean architecture migration
- **[Phase Completion Reports](.)** - PHASE_1 through PHASE_6 completion reports
- **[Changelog](../CHANGELOG.md)** - Project changelog

### ⚙️ Configuration & Models
- **[Configuration Reference](./CONFIGURATION_REFERENCE.md)** - **NEW:** Complete config options guide
- **[Models](./MODELS.md)** - Available models and recommendations
- **[vLLM Installation](./VLLM_INSTALLATION.md)** - vLLM setup guide

### 🚀 Roadmap
- **[Roadmap](./ROADMAP.md)** - Development roadmap
- **[Prototype Strategy](./PROTOTYPE_STRATEGY_OVERVIEW.md)** - Prototype strategy

---

**Note:** Documentation is being consolidated. See [DOCUMENTATION_TODO.md](./DOCUMENTATION_TODO.md) for planned improvements.
