# vLLM Installation & Setup (GPU / Revisions-Pinning)

Datum: 2025-09-18  
Status: Initiale Fassung

Diese Anleitung beschreibt eine reproduzierbare Installation von vLLM für den Einsatz mit CLARA Multi-Adapter Serving (LoRA/QLoRA/DoRA). Sie folgt den aktuellen Best Practices der offiziellen Dokumentation und erweitert sie um Commit-Pinning, Windows/WSL2 Hinweise und Integritätsprüfungen.

---
## 1. Ziel & Prinzipien
- Reproduzierbare Builds (Pin auf spezifische vLLM Revision)
- Sichere GPU Nutzung (korrekte CUDA / Treiber Kompatibilität)
- Saubere Isolation (venv oder Conda)
- Testbare Minimal-Inferenz vor Adapter-Integration

---
## 2. Voraussetzungen
| Komponente | Empfehlung | Prüfen |
|-----------|------------|--------|
| NVIDIA Treiber | Aktuell (>= 535.xx) | `nvidia-smi` (WSL/Host) |
| CUDA Toolkit (optional) | 12.x (nicht zwingend, Wheels beinhalten Runtime) | `nvcc --version` |
| Python | 3.10 / 3.11 | `python --version` |
| VRAM | >= 12 GB (mehr für große Modelle) | `nvidia-smi` |
| Disk | Genug für Base Modell + Adapter | Explorer/`dir` |

Unter Windows empfehlenswert: WSL2 (Ubuntu) für stabileren PyTorch / vLLM GPU Support.

---
## 3. Umgebung anlegen
### Option A: Python venv
```bash
python -m venv .venv
source .venv/bin/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install --upgrade pip wheel setuptools
```
### Option B: Conda
```bash
conda create -n clara-vllm python=3.11 -y
conda activate clara-vllm
```

---
## 4. Commit / Release Pinning
Es gibt zwei gängige Wege für kontrollierte Versionierung:

### 4.1 PyPI Version pinnen (einfach)
```bash
pip install "vllm==0.6.1"  # Beispielversion prüfen
```

### 4.2 Spezifische Git-Revision (feingranular)
```bash
pip install --no-deps git+https://github.com/vllm-project/vllm.git@<COMMIT_HASH>
# Danach abhängigkeiten
pip install -r https://raw.githubusercontent.com/vllm-project/vllm/<COMMIT_HASH>/requirements.txt
```
Hinweis: `<COMMIT_HASH>` aus `git log` oder Release-Tag ersetzen.

### 4.3 Lokales Clone + Editable (für Entwicklungsanpassungen)
```bash
git clone https://github.com/vllm-project/vllm.git
cd vllm
git checkout <COMMIT_HASH>
pip install -e .
```

---
## 5. PyTorch & CUDA Kompatibilität
Installiere zuerst kompatibles PyTorch (falls nicht bereits im Wheel enthalten):
```bash
pip install torch --index-url https://download.pytorch.org/whl/cu121
```
(Variante je nach CUDA Version anpassen: `cu118`, `cu121`, etc.)

Teste GPU:
```bash
python - <<'PY'
import torch
print('CUDA verfügbar:', torch.cuda.is_available())
print('Geräte:', torch.cuda.device_count())
print('Name[0]:', torch.cuda.get_device_name(0) if torch.cuda.device_count() else 'n/a')
PY
```

---
## 6. vLLM Installation (Beispiel Workflow)
```bash
# 1. Umgebung aktivieren
source .venv/bin/activate

# 2. PyTorch installieren (angepasst an GPU)
pip install torch --index-url https://download.pytorch.org/whl/cu121

# 3. vLLM (Release) installieren
pip install vllm==0.6.1

# 4. Optional: FastAPI + Uvicorn für Serving-Schicht
pip install fastapi uvicorn

# 5. (Optional) PEFT + Transformers für Adapter
pip install peft transformers accelerate bitsandbytes safetensors
```

Integritäts-Check (Versionen inspizieren):
```bash
python - <<'PY'
import vllm, torch, transformers, peft
print('vLLM:', vllm.__version__)
print('Torch:', torch.__version__)
print('Transformers:', transformers.__version__)
print('PEFT:', peft.__version__)
PY
```

---
## 7. Minimaler Test (Base Inferenz)
```bash
python - <<'PY'
from vllm import LLM, SamplingParams
llm = LLM(model="facebook/opt-125m")  # Kleines Testmodell
sp = SamplingParams(max_tokens=32)
outputs = llm.generate(["Hallo, gib mir einen kurzen Verwaltungstext:"], sp)
print(outputs[0].outputs[0].text)
PY
```
Wenn das funktioniert → GPU & Scheduler OK.

---
## 8. Adapter-Test (zukünftiger Schritt)
Sobald LoRA/QLoRA Adapter trainiert:
1. Adapter-Verzeichnis prüfen (`models/adapters/<domain>/...`)
2. Über `clara_serve_vllm.py` Endpunkt `/load_adapter` registrieren (nach Implementierung realer Loader-Aufrufe)
3. `/activate_adapter` aufrufen
4. `/generate` mit Prompt testen

> Aktuell sind LoRA-Hooks im Skeleton nur Platzhalter – an vLLM Version anpassen.

---
## 9. Reproduzierbarkeit sichern
- Datei `metadata/vllm_environment_lock.json` anlegen (optional) mit:
  - Python Version
  - Pip Freeze Ergebnis
  - GPU Infos (`nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv`)
- Hash der Adapter (siehe `adapter_registry.json`) pflegen

Beispiel Automatisierung (Snippet):
```bash
pip freeze > metadata/pip_freeze_vllm.txt
nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv > metadata/gpu_info.txt
python - <<'PY'
import json, platform, torch
meta = {
  'python': platform.python_version(),
  'torch': torch.__version__,
}
open('metadata/vllm_environment_lock.json','w').write(json.dumps(meta, indent=2))
PY
```

---
## 10. Häufige Probleme
| Problem | Ursache | Lösung |
|---------|---------|--------|
| `CUDA driver mismatch` | Treiber zu alt | NVIDIA Treiber updaten |
| `torch.cuda.is_available()==False` | Falsche Umgebung/WSL GPU nicht durchgereicht | WSL2 + `wsl --update`, korrekter Treiber |
| Out of Memory | Modell zu groß | Kleinere Modellvariante / KV-Cache Reduktion |
| Sehr langsame Ladezeit | Disk/Netzwerk-Bottleneck | Vorab HF Cache (HF_HOME setzen) |
| Inkompatible Adapter | Base Hash mismatch | Registry prüfen + neu trainieren |

---
## 11. Optional: Commit-Pinning Skript
Erstelle Skript `scripts/install_vllm_pinned.ps1` (Beispiel):
```powershell
param(
  [string]$Commit = "<COMMIT_HASH>",
  [string]$EnvName = "clara-vllm"
)
python -m venv .venv
. .\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install --no-deps git+https://github.com/vllm-project/vllm.git@$Commit
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/vllm-project/vllm/$Commit/requirements.txt" -OutFile requirements_vllm.txt
pip install -r requirements_vllm.txt
pip install fastapi uvicorn peft transformers accelerate bitsandbytes safetensors
```

---
## 12. Nächste Schritte
- Implementiere LoRA Load/Unload Hooks in `clara_serve_vllm.py`
- `clara_train_adapter.py` hinzufügen (einheitliches Training)
- Integrationstests (Base + Adapter) automatisieren
- Monitoring (Tokens/s, Latenz, VRAM) ergänzen

---
*Ende der Anleitung – bei Änderungen an vLLM Version diese Datei aktualisieren.*
