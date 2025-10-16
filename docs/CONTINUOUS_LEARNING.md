# 🔄 CLARA Continuous Learning System

## Übersicht

Das **CLARA Continuous Learning System** ermöglicht kontinuierliche LoRA-Verbesserung zur Laufzeit. Das Modell lernt live aus Nutzer-Feedback und verbessert sich automatisch während der Nutzung.

## 🎯 Funktionsweise

- **Qualitäts-Filterung**: Nur hochwertige Samples werden verwendet

### Architektur
```
Nutzer-Input → Modell-Antwort → Bewertung → Live-Buffer → Training → Verbessertes Modell
     ↑                                                                         ↓
     └─────────────────── Kontinuierlicher Kreislauf ──────────────────────────┘
```

## 🚀 Schnellstart

### 1. Basic Setup
```bash
python scripts/clara_continuous_learning.py --config configs/continuous_config.yaml
# (Altname nur zu historischen Zwecken entfernt)

# Live-Demo ausführen
python scripts/live_demo.py

# Mit Start-Script
./start_continuous_learning.bat    # Windows
./start_continuous_learning.ps1    # PowerShell
```

### 2. Interaktiver Modus
python scripts/clara_continuous_learning.py --config configs/continuous_config.yaml --interactive
# (Ehemaliger Skriptname entfernt)
```

- `quit` - Beenden

### 3. Live-Demo
```bash
python scripts/live_demo.py
```

- `status` - Live-Status

## ⚙️ Konfiguration

### continuous_config.yaml
```yaml
continuous:
  enabled: true
  buffer_size: 1000           # Max. Samples im Buffer
  quality_threshold: -0.5     # Mindestqualität
  min_batch_size: 25          # Min. Batch-Größe
  train_interval: 180         # Training-Intervall (Sekunden)
  learning_rate: 1e-6         # Sehr niedrige LR
  max_epochs: 1               # Ein Epoch pro Zyklus
```

- **Source**: Herkunft des Samples (user, demo, conversation)

## 🎮 Verwendung

### Programmatische Nutzung
```python
from scripts.continuous_learning import ContinuousLoRATrainer

# Trainer initialisieren
trainer = ContinuousLoRATrainer("configs/continuous_config.yaml")

# Kontinuierliches Lernen starten
trainer.start_continuous_learning()

# Feedback hinzufügen
trainer.add_feedback_sample(
    text="Das Verwaltungsverfahren ist wichtig.",
    feedback_score=0.8,
    source="user",
    importance=3
)

# Konversation verarbeiten
trainer.process_conversation(
    user_input="Was ist ein Verwaltungsakt?",
    model_output="Ein Verwaltungsakt ist...",
    user_rating=4  # 1-5 Sterne
)

# Text generieren
response = trainer.generate_with_live_model("Frage: Was ist...")

# Statistiken abrufen
stats = trainer.get_live_stats()
```

### API-Integration
```python
# Flask/FastAPI Beispiel
@app.route('/feedback', methods=['POST'])
def add_feedback():
    data = request.json
    success = trainer.add_feedback_sample(
        text=data['text'],
        feedback_score=data['score'],
        source='api',
        importance=data.get('importance', 1)
    )
    return {'success': success}

@app.route('/generate', methods=['POST'])
def generate_text():
    prompt = request.json['prompt']
    response = trainer.generate_with_live_model(prompt)
    return {'response': response}
```

## 📊 Monitoring

### Live-Statistiken
```python
stats = trainer.get_live_stats()
print(f"Buffer: {stats['buffer']['count']} Samples")
print(f"Updates: {stats['metrics']['model_updates']}")
print(f"Qualität: {stats['buffer']['avg_quality']:.2f}")
```

- **Performance**: Live-Sample Verarbeitung

## 🔧 Erweiterte Features

- **Error-Recovery**: Automatische Wiederherstellung bei Fehlern

- **Memory-Management**: Optimierte GPU-Nutzung

- **Multi-User**: Unterstützung für mehrere Nutzer

## 🎯 Best Practices

- **Balance halten**: Positive und negative Samples

- **Qualitäts-Schwelle**: -0.5 bis 0.0 empfohlen

- **Performance-Metrics**: Training-Erfolgsrate

## 🚨 Troubleshooting

### Häufige Probleme

**Buffer füllt sich nicht**
```bash
python scripts/clara_continuous_learning.py --stats
# (Altname entfernt)
# Senke quality_threshold in config
```

**Training startet nicht**
```bash
# Prüfe min_batch_size
# Reduziere train_interval
# Überprüfe GPU-Memory
```

**Modell verbessert sich nicht**
```bash
# Erhöhe learning_rate (vorsichtig)
# Prüfe Feedback-Qualität
# Verlängere max_epochs
```

### Debug-Modus
```bash
python scripts/clara_continuous_learning.py --config configs/continuous_config.yaml --verbose
# (Altname entfernt)

# Demo mit Debug-Output
python scripts/live_demo.py --debug
```

## 📈 Roadmap

- [ ] **Cloud-Integration**: Remote Training-Cluster

- **v1.3**: Performance-Optimierungen (geplant)

## 🤝 Beitrag leisten

Das Continuous Learning System ist darauf ausgelegt, erweitert zu werden:

1. **Neue Feedback-Quellen**: Integration weiterer Datenquellen
2. **Verbesserte Algorithmen**: Optimierte Learning-Strategien
3. **UI/UX**: Bessere Benutzeroberflächen
4. **Skalierung**: Multi-User und Cloud-Deployment
---

*🤖 CLARA lernt nie aus - und wird dabei immer besser!*
