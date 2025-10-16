# CLARA Training Resume - Anleitung

## 🔄 **Resume-Funktionalität ist jetzt Standard!**

### 📋 **Standardverhalten (Neu)**

Wenn Sie ein Training starten und Checkpoints vorhanden sind, wird **automatisch** vom letzten Checkpoint fortgesetzt:

```bash
# Startet automatisch Resume falls Checkpoints vorhanden
python scripts/clara_train_lora.py --config configs/leo_cuda_config.yaml
```

### 🆕 **Neues Training erzwingen**

Wenn Sie explizit ein **neues Training** starten möchten (Checkpoints ignorieren):

```bash
# Ignoriert vorhandene Checkpoints und startet neu
python scripts/clara_train_lora.py --config configs/leo_cuda_config.yaml --no-resume
```

### 🎯 **Spezifischen Checkpoint verwenden**

Um von einem bestimmten Checkpoint fortzusetzen:

```bash
# Resume von spezifischem Checkpoint
python scripts/clara_train_lora.py --config configs/leo_cuda_config.yaml --resume models/clara_leo_cuda_outputs/checkpoint-1000
```

### 🛠️ **Resume-Utility Commands**

**Checkpoints auflisten:**
```bash
python scripts/resume_training.py list
```

**Checkpoint-Details anzeigen:**
```bash
python scripts/resume_training.py info models/clara_leo_cuda_outputs/checkpoint-1000
```

**Training mit Resume starten:**
```bash
python scripts/resume_training.py resume --config configs/leo_cuda_config.yaml
```

**Training neu starten (ohne Resume):**
```bash
python scripts/resume_training.py resume --config configs/leo_cuda_config.yaml --no-resume
```

**Alte Checkpoints bereinigen:**
```bash
python scripts/resume_training.py cleanup --keep 3
```

### 📊 **Was wird gespeichert?**

Bei jedem Checkpoint werden gespeichert:
- **Modell-Gewichte** (LoRA Adapter)
- **Optimizer-Zustand** (Adam, etc.)
- **Learning Rate Scheduler**
- **Training-Fortschritt** (Step, Epoch)
- **Zufallszahlengenerator-Status**
- **Loss-History und Metriken**

### ⚡ **Quick-Status zeigt Resume-Info**

```bash
python scripts/quick_status.py
```

Zeigt jetzt auch:
- Anzahl verfügbarer Checkpoints
- Resume-Verfügbarkeit
- Training-Fortschritt mit ETA

### 🎮 **Beispiel-Workflow**

1. **Training starten:**
   ```bash
   python scripts/clara_train_lora.py --config configs/minimal_config.yaml
   ```

2. **Training unterbrechen** (Ctrl+C)

3. **Status prüfen:**
   ```bash
   python scripts/quick_status.py
   # Zeigt: "🔄 Resume verfügbar"
   ```

4. **Training fortsetzen:**
   ```bash
   python scripts/clara_train_lora.py --config configs/minimal_config.yaml
   # Automatisches Resume vom letzten Checkpoint!
   ```

### 💡 **Vorteile der neuen Resume-Logik**

- ✅ **Sicher**: Nie versehentlich Fortschritt verlieren
- ✅ **Intuitiv**: Resume ist Standard, wie in modernen Tools erwartet
- ✅ **Flexibel**: Explizite Kontrolle mit --no-resume
- ✅ **Transparent**: Klare Logging-Nachrichten
- ✅ **Robust**: Automatische Checkpoint-Erkennung

### 🚨 **Wichtige Hinweise**

- Checkpoints werden alle `save_steps` erstellt (siehe Config)
- Nur die neuesten `save_total_limit` Checkpoints werden behalten
- Resume funktioniert auch bei Konfigurationsänderungen (z.B. Batch-Size)
- Multi-GPU Training unterstützt ebenfalls Resume

Das macht CLARA Training viel benutzerfreundlicher! 🎉
