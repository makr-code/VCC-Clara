#!/usr/bin/env python3
"""
CLARA Import Helper
Löst Import-Probleme und stellt sichere Importe bereit
"""

import sys
import os
from pathlib import Path
from typing import Optional, Any

def setup_clara_path():
    """Fügt CLARA-Pfade zum Python-Path hinzu"""
    
    # Aktuelles Script-Verzeichnis
    script_dir = Path(__file__).parent
    
    # Projekt-Root (verwLLM)
    project_root = script_dir.parent
    
    # Füge Pfade hinzu wenn nicht vorhanden
    paths_to_add = [str(project_root), str(script_dir)]
    
    for path in paths_to_add:
        if path not in sys.path:
            sys.path.insert(0, path)

def safe_import(module_name: str, class_names: list = None, fallback_error: bool = True) -> Any:
    """Sicherer Import mit Fallback-Strategien"""
    
    setup_clara_path()
    
    if class_names is None:
        class_names = []
    
    # Import-Versuche in verschiedenen Kontexten
    import_attempts = [
        f"scripts.{module_name}",
        module_name,
        f"..{module_name}",
    ]
    
    for attempt in import_attempts:
        try:
            module = __import__(attempt, fromlist=class_names)
            
            if class_names:
                # Gebe Dict mit Klassen zurück
                result = {}
                for class_name in class_names:
                    try:
                        result[class_name] = getattr(module, class_name)
                    except AttributeError:
                        if fallback_error:
                            raise ImportError(f"Klasse {class_name} nicht in {attempt} gefunden")
                        result[class_name] = None
                return result
            else:
                # Gebe Modul zurück
                return module
                
        except ImportError:
            continue
    
    # Alle Versuche fehlgeschlagen
    if fallback_error:
        raise ImportError(f"Modul {module_name} konnte nicht importiert werden")
    
    return None

def get_continuous_trainer():
    """Importiert ContinuousLoRATrainer sicher"""
    try:
        classes = safe_import("continuous_learning", ["ContinuousLoRATrainer", "LiveSample"])
        return classes["ContinuousLoRATrainer"], classes["LiveSample"]
    except ImportError:
        return None, None

def get_veritas_integration():
    """Importiert Veritas Integration sicher"""
    try:
        classes = safe_import("veritas_integration", ["ClaraClient", "VeritasClaraIntegration"])
        return classes["ClaraClient"], classes["VeritasClaraIntegration"]
    except ImportError:
        return None, None

def check_dependencies():
    """Prüft alle wichtigen Dependencies"""
    
    deps_status = {
        "torch": False,
        "transformers": False,
        "peft": False,
        "fastapi": False,
        "uvicorn": False,
        "datasets": False,
        "yaml": False
    }
    
    for dep in deps_status:
        try:
            if dep == "yaml":
                import yaml
            else:
                __import__(dep)
            deps_status[dep] = True
        except ImportError:
            pass
    
    return deps_status

def diagnose_import_issues():
    """Diagnostiziert Import-Probleme und gibt Lösungsvorschläge"""
    
    print("🔍 CLARA Import-Diagnose")
    print("=" * 40)
    
    # Python-Version
    print(f"🐍 Python-Version: {sys.version}")
    print(f"📁 Script-Verzeichnis: {Path(__file__).parent}")
    print(f"📂 Arbeitsverzeichnis: {os.getcwd()}")
    
    # Python-Path
    print(f"\n📚 Python-Path ({len(sys.path)} Einträge):")
    for i, path in enumerate(sys.path[:5]):  # Erste 5 anzeigen
        print(f"   {i}: {path}")
    if len(sys.path) > 5:
        print(f"   ... und {len(sys.path) - 5} weitere")
    
    # Dependencies prüfen
    print(f"\n📦 Dependencies:")
    deps = check_dependencies()
    for dep, status in deps.items():
        status_icon = "✅" if status else "❌"
        print(f"   {status_icon} {dep}")
    
    # CLARA Module prüfen
    print(f"\n🤖 CLARA Module:")
    
    # ContinuousLoRATrainer
    trainer_class, sample_class = get_continuous_trainer()
    trainer_status = "✅" if trainer_class else "❌"
    print(f"   {trainer_status} ContinuousLoRATrainer")
    
    # Veritas Integration
    client_class, integration_class = get_veritas_integration()
    veritas_status = "✅" if client_class else "❌"
    print(f"   {veritas_status} VeritasClaraIntegration")
    
    # Lösungsvorschläge
    print(f"\n💡 Lösungsvorschläge:")
    
    missing_deps = [dep for dep, status in deps.items() if not status]
    if missing_deps:
        print(f"   📦 Installiere fehlende Dependencies:")
        print(f"      pip install {' '.join(missing_deps)}")
    
    if not trainer_class:
        print(f"   🔧 ContinuousLoRATrainer:")
        print(f"      - Stelle sicher dass continuous_learning.py existiert")
        print(f"      - Prüfe auf Syntax-Fehler in der Datei")
    
    if not client_class:
        print(f"   🔧 VeritasClaraIntegration:")
        print(f"      - Stelle sicher dass veritas_integration.py existiert")
        print(f"      - Prüfe FastAPI Dependencies")
    
    # Status-Zusammenfassung
    all_good = all(deps.values()) and trainer_class and client_class
    if all_good:
        print(f"\n🎉 Alle Imports funktionieren korrekt!")
    else:
        print(f"\n⚠️  Einige Imports haben Probleme - siehe Lösungsvorschläge oben")
    
    return all_good

if __name__ == "__main__":
    diagnose_import_issues()
