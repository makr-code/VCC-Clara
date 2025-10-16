# CLARA - Verfügbare Basismodelle und Empfehlungen

## 🎯 Empfohlene Modelle für deutsche Verwaltung/Recht

### **Top-Empfehlungen:**

| Modell | Größe | VRAM | Sprache | Empfehlung | Anwendung |
|--------|-------|------|---------|------------|-----------|
| **LeoLM/leo-hessianai-7b** | 7B | 16GB | 🇩🇪 Deutsch | ⭐⭐⭐⭐⭐ | **Beste Wahl für deutsche Verwaltung** |
| **DiscoResearch/DiscoLM-German-7b-v1** | 7B | 16GB | 🇩🇪 Deutsch | ⭐⭐⭐⭐⭐ | **Speziell für deutsche Texte** |
| **microsoft/DialoGPT-medium** | 355M | 4GB | 🇺🇸 Englisch | ⭐⭐⭐ | **Für Tests und kleine GPUs** |
| **meta-llama/Llama-2-7b-chat-hf** | 7B | 16GB | 🇺🇸 Englisch | ⭐⭐⭐⭐ | **Stabil, gut für Experimente** |
| **mistralai/Mistral-7B-Instruct-v0.2** | 7B | 16GB | 🇺🇸 Englisch | ⭐⭐⭐⭐ | **Sehr gut für Instruktionen** |

## 📋 Vollständige Modell-Übersicht

```python
# CLARA Basismodell-Konfigurationen
CLARA_BASE_MODELS = {
    # Deutsche Modelle (EMPFOHLEN für Verwaltung)
    "deutsche_modelle": {
        "LeoLM/leo-hessianai-7b": {
            "name": "LeoLM 7B",
            "size": "7B",
            "vram_requirement": "16GB",
            "language": "Deutsch",
            "specialization": "Deutsche Sprache, Reasoning",
            "recommendation": 5,
            "use_case": "Verwaltung, Recht, formelle Texte",
            "lora_config": "configs/leo_lora_config.yaml",
            "qlora_config": "configs/leo_qlora_config.yaml"
        },
        "DiscoResearch/DiscoLM-German-7b-v1": {
            "name": "DiscoLM German 7B",
            "size": "7B", 
            "vram_requirement": "16GB",
            "language": "Deutsch",
            "specialization": "Deutsche Konversation",
            "recommendation": 5,
            "use_case": "Behördenkommunikation, FAQ",
            "lora_config": "configs/disco_lora_config.yaml",
            "qlora_config": "configs/disco_qlora_config.yaml"
        },
        "malteos/hermeo-7b": {
            "name": "Hermeo 7B",
            "size": "7B",
            "vram_requirement": "16GB", 
            "language": "Deutsch",
            "specialization": "Deutsche Instruktionsbefolgung",
            "recommendation": 4,
            "use_case": "Strukturierte Verwaltungsaufgaben"
        }
    },
    
    # Englische Modelle (Fallback/Experimente)
    "englische_modelle": {
        "meta-llama/Llama-2-7b-chat-hf": {
            "name": "Llama 2 Chat 7B",
            "size": "7B",
            "vram_requirement": "16GB",
            "language": "Englisch",
            "specialization": "Chat, Instruktionen",
            "recommendation": 4,
            "use_case": "Experimente, internationale Texte",
            "lora_config": "configs/llama_lora_config.yaml"
        },
        "mistralai/Mistral-7B-Instruct-v0.2": {
            "name": "Mistral 7B Instruct",
            "size": "7B",
            "vram_requirement": "16GB",
            "language": "Englisch", 
            "specialization": "Instruktionsbefolgung",
            "recommendation": 4,
            "use_case": "Strukturierte Aufgaben",
            "lora_config": "configs/mistral_lora_config.yaml"
        },
        "microsoft/DialoGPT-medium": {
            "name": "DialoGPT Medium",
            "size": "355M",
            "vram_requirement": "4GB",
            "language": "Englisch",
            "specialization": "Dialog",
            "recommendation": 3,
            "use_case": "Tests, schwache Hardware",
            "lora_config": "configs/lora_config.yaml"  # Standard
        }
    },
    
    # Große Modelle (für starke Hardware)
    "grosse_modelle": {
        "LeoLM/leo-hessianai-13b": {
            "name": "LeoLM 13B", 
            "size": "13B",
            "vram_requirement": "26GB",
            "language": "Deutsch",
            "specialization": "Erweiterte deutsche Sprachverarbeitung",
            "recommendation": 5,
            "use_case": "Komplexe Rechtsfragen, A100 Hardware",
            "note": "Nur für starke Hardware"
        },
        "meta-llama/Llama-2-13b-chat-hf": {
            "name": "Llama 2 Chat 13B",
            "size": "13B", 
            "vram_requirement": "26GB",
            "language": "Englisch",
            "specialization": "Erweiterte Konversation",
            "recommendation": 4,
            "use_case": "Komplexe Aufgaben, A100 Hardware"
        }
    },
    
    # Kleine Modelle (für schwache Hardware)
    "kleine_modelle": {
        "microsoft/DialoGPT-small": {
            "name": "DialoGPT Small",
            "size": "117M",
            "vram_requirement": "2GB", 
            "language": "Englisch",
            "specialization": "Einfache Dialoge",
            "recommendation": 2,
            "use_case": "Prototyping, sehr schwache Hardware"
        },
        "distilbert-base-german-cased": {
            "name": "DistilBERT German",
            "size": "135M",
            "vram_requirement": "2GB",
            "language": "Deutsch", 
            "specialization": "Textverständnis",
            "recommendation": 3,
            "use_case": "Klassifikation, Embedding"
        }
    }
}
```

## 🏆 Empfehlungen nach Anwendungsfall

### **Für Y:\veritas\data\ (Ihre Anwendung):**
1. **LeoLM/leo-hessianai-7b** - Deutsche Verwaltungssprache ⭐⭐⭐⭐⭐
2. **DiscoResearch/DiscoLM-German-7b-v1** - Deutsche Konversation ⭐⭐⭐⭐⭐

### **Für Tests/Entwicklung:**
1. **microsoft/DialoGPT-medium** - Schnell, wenig VRAM ⭐⭐⭐

### **Für Production (starke Hardware):**
1. **LeoLM/leo-hessianai-13b** - Beste Qualität ⭐⭐⭐⭐⭐

## 🔄 Modell-Wechsel

**CLARA ist modular - ein Training, mehrere Modelle:**

```bash
# Verschiedene Basismodelle mit gleichen Daten
python scripts/clara_train_lora.py --config configs/leo_lora_config.yaml      # Deutsch
python scripts/clara_train_lora.py --config configs/disco_lora_config.yaml    # Deutsch
python scripts/clara_train_lora.py --config configs/mistral_lora_config.yaml  # Englisch

# Alle Modelle in Ollama verfügbar als:
ollama run clara-leo      # Deutsche Verwaltung
ollama run clara-disco    # Deutsche Konversation  
ollama run clara-mistral  # Englische Instruktionen
```

## 💾 VRAM-Anforderungen

| GPU | VRAM | Empfohlenes Modell | Training-Methode |
|-----|------|-------------------|------------------|
| RTX 3060 | 12GB | DialoGPT-medium | LoRA |
| RTX 3070 | 8GB | LeoLM-7b | QLoRA |
| RTX 3080 | 10GB | LeoLM-7b | QLoRA |
| RTX 3090 | 24GB | LeoLM-7b | LoRA |
| RTX 4090 | 24GB | LeoLM-13b | LoRA |
| A100 | 40GB | LeoLM-13b | LoRA |
