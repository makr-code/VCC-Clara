"""
CLARA Modell-Auswahl und Konfigurationsgenerator
Hilft bei der Auswahl des besten Basismodells für Ihre Hardware und Anwendung.
"""

import argparse
import yaml
from pathlib import Path

# Modell-Konfigurationen (aus docs/MODELS.md)
CLARA_BASE_MODELS = {
    "deutsche_modelle": {
        "LeoLM/leo-hessianai-7b": {
            "name": "LeoLM 7B",
            "size": "7B",
            "vram_requirement": 16,
            "language": "Deutsch",
            "specialization": "Deutsche Sprache, Reasoning",
            "recommendation": 5,
            "use_case": "Verwaltung, Recht, formelle Texte",
            "config_template": "leo_lora_config.yaml"
        },
        "DiscoResearch/DiscoLM-German-7b-v1": {
            "name": "DiscoLM German 7B",
            "size": "7B", 
            "vram_requirement": 16,
            "language": "Deutsch",
            "specialization": "Deutsche Konversation",
            "recommendation": 5,
            "use_case": "Behördenkommunikation, FAQ",
            "config_template": "disco_lora_config.yaml"
        }
    },
    "englische_modelle": {
        "microsoft/DialoGPT-medium": {
            "name": "DialoGPT Medium",
            "size": "355M",
            "vram_requirement": 4,
            "language": "Englisch",
            "specialization": "Dialog",
            "recommendation": 3,
            "use_case": "Tests, schwache Hardware",
            "config_template": "lora_config.yaml"
        },
        "meta-llama/Llama-2-7b-chat-hf": {
            "name": "Llama 2 Chat 7B",
            "size": "7B",
            "vram_requirement": 16,
            "language": "Englisch",
            "specialization": "Chat, Instruktionen",
            "recommendation": 4,
            "use_case": "Experimente, internationale Texte"
        }
    }
}

def recommend_model(vram_gb: int, language: str = "deutsch", use_case: str = "verwaltung"):
    """
    Empfehle das beste Modell basierend auf Hardware und Anforderungen.
    
    Args:
        vram_gb: Verfügbares VRAM in GB
        language: Gewünschte Sprache ("deutsch" oder "englisch")
        use_case: Anwendungsfall
        
    Returns:
        tuple: (model_id, model_info, training_method)
    """
    
    recommendations = []
    
    # Alle Modelle durchgehen
    for category, models in CLARA_BASE_MODELS.items():
        for model_id, info in models.items():
            # VRAM-Anforderung prüfen
            if info["vram_requirement"] <= vram_gb:
                # Sprache prüfen
                lang_match = (
                    (language == "deutsch" and info["language"] == "Deutsch") or
                    (language == "englisch" and info["language"] == "Englisch") or
                    language == "egal"
                )
                
                if lang_match:
                    # Training-Methode bestimmen
                    if vram_gb >= info["vram_requirement"] * 1.5:  # Komfortable Marge
                        training_method = "LoRA"
                    else:
                        training_method = "QLoRA"
                    
                    recommendations.append({
                        "model_id": model_id,
                        "info": info,
                        "training_method": training_method,
                        "score": info["recommendation"]
                    })
    
    # Nach Empfehlungsscore sortieren
    recommendations.sort(key=lambda x: x["score"], reverse=True)
    
    if recommendations:
        best = recommendations[0]
        return best["model_id"], best["info"], best["training_method"], recommendations
    else:
        return None, None, None, []

def generate_config(model_id: str, output_path: str, training_method: str = "lora"):
    """
    Generiere eine angepasste Konfigurationsdatei für das gewählte Modell.
    
    Args:
        model_id: Hugging Face Model ID
        output_path: Pfad für die neue Konfiguration
        training_method: "lora" oder "qlora"
    """
    
    # Basis-Template laden
    if training_method.lower() == "qlora":
        template_path = Path("configs/qlora_config.yaml")
    else:
        template_path = Path("configs/lora_config.yaml")
    
    with open(template_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # Modell anpassen
    config["model"]["base_model"] = model_id
    
    # Output-Pfad anpassen
    model_name = model_id.split("/")[-1].replace("-", "_")
    config["training"]["output_dir"] = f"models/clara_{model_name}_outputs"
    config["ollama"]["model_name"] = f"clara-{model_name.replace('_', '-')}"
    
    # Wandb-Projekt anpassen
    if config.get("wandb"):
        config["wandb"]["project"] = f"CLARA-{model_name}"
    
    # Speichern
    output_path = Path(output_path)
    with open(output_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
    
    print(f"Konfiguration erstellt: {output_path}")

def main():
    parser = argparse.ArgumentParser(description="CLARA Modell-Auswahl Assistent")
    parser.add_argument("--vram", type=int, help="Verfügbares VRAM in GB")
    parser.add_argument("--language", choices=["deutsch", "englisch", "egal"], 
                       default="deutsch", help="Gewünschte Sprache")
    parser.add_argument("--list", action="store_true", help="Alle verfügbaren Modelle auflisten")
    parser.add_argument("--generate-config", type=str, help="Generiere Config für spezifisches Modell")
    parser.add_argument("--output", type=str, help="Output-Pfad für generierte Config")
    parser.add_argument("--method", choices=["lora", "qlora"], default="lora", 
                       help="Training-Methode")
    
    args = parser.parse_args()
    
    if args.list:
        print("🤖 CLARA - Verfügbare Basismodelle:\n")
        
        for category, models in CLARA_BASE_MODELS.items():
            print(f"📁 {category.replace('_', ' ').title()}:")
            for model_id, info in models.items():
                stars = "⭐" * info["recommendation"]
                print(f"  • {info['name']} ({model_id})")
                print(f"    💾 VRAM: {info['vram_requirement']}GB | 🌍 {info['language']} | {stars}")
                print(f"    📋 {info['use_case']}\n")
        return
    
    if args.generate_config:
        if not args.output:
            model_name = args.generate_config.split("/")[-1].replace("-", "_")
            args.output = f"configs/custom_{model_name}_{args.method}_config.yaml"
        
        generate_config(args.generate_config, args.output, args.method)
        return
    
    if args.vram:
        print(f"🔍 Suche nach optimalen CLARA-Modell für {args.vram}GB VRAM...")
        print(f"🌍 Sprache: {args.language}")
        print()
        
        model_id, info, method, all_recs = recommend_model(args.vram, args.language)
        
        if model_id:
            print(f"🏆 EMPFEHLUNG:")
            print(f"   Modell: {info['name']} ({model_id})")
            print(f"   Methode: {method}")
            print(f"   VRAM: {info['vram_requirement']}GB (Sie haben {args.vram}GB)")
            print(f"   Spezialisierung: {info['specialization']}")
            print(f"   Bewertung: {'⭐' * info['recommendation']}")
            print()
            
            # Konfiguration generieren
            config_name = f"recommended_{method.lower()}_config.yaml"
            generate_config(model_id, config_name, method.lower())
            
            print(f"🚀 Zum Starten:")
            if method == "LoRA":
                print(f"   python scripts/clara_train_lora.py --config {config_name}")
            else:
                print(f"   python scripts/train_qlora.py --config {config_name}")
            
            if len(all_recs) > 1:
                print(f"\n📊 Weitere Optionen:")
                for rec in all_recs[1:4]:  # Zeige top 3 weitere
                    print(f"   • {rec['info']['name']} ({rec['training_method']}) - {'⭐' * rec['score']}")
        else:
            print(f"❌ Kein passendes Modell für {args.vram}GB VRAM gefunden.")
            print("   Versuchen Sie ein kleineres Modell oder QLoRA.")
    else:
        print("Nutzen Sie --help für Optionen oder --list für alle Modelle")

if __name__ == "__main__":
    main()
