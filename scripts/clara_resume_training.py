#!/usr/bin/env python3
"""
CLARA Training Resume Utility
Hilfstool zum Verwalten und Fortsetzen von unterbrochenen Trainings
"""

import json
import argparse
from pathlib import Path
from datetime import datetime
import yaml

def list_checkpoints(output_dir):
    """Listet alle verfügbaren Checkpoints auf"""
    output_path = Path(output_dir)
    
    if not output_path.exists():
        print(f"❌ Output-Verzeichnis nicht gefunden: {output_dir}")
        return []
    
    # Suche nach Checkpoint-Ordnern
    checkpoints = []
    for checkpoint_dir in output_path.iterdir():
        if checkpoint_dir.is_dir() and checkpoint_dir.name.startswith('checkpoint-'):
            try:
                step_num = int(checkpoint_dir.name.split('-')[1])
                
                # Trainer State prüfen
                trainer_state_file = checkpoint_dir / "trainer_state.json"
                if trainer_state_file.exists():
                    with open(trainer_state_file, 'r') as f:
                        state = json.load(f)
                    
                    checkpoints.append({
                        'path': str(checkpoint_dir),
                        'step': step_num,
                        'epoch': state.get('epoch', 0),
                        'global_step': state.get('global_step', 0),
                        'train_loss': None,
                        'timestamp': checkpoint_dir.stat().st_mtime
                    })
                    
                    # Letzten Loss aus History holen
                    if 'log_history' in state and state['log_history']:
                        for log_entry in reversed(state['log_history']):
                            if 'train_loss' in log_entry:
                                checkpoints[-1]['train_loss'] = log_entry['train_loss']
                                break
                else:
                    checkpoints.append({
                        'path': str(checkpoint_dir),
                        'step': step_num,
                        'epoch': 0,
                        'global_step': step_num,
                        'train_loss': None,
                        'timestamp': checkpoint_dir.stat().st_mtime
                    })
            except (ValueError, json.JSONDecodeError):
                continue
    
    # Nach Step-Nummer sortieren
    checkpoints.sort(key=lambda x: x['step'])
    return checkpoints

def show_checkpoint_info(checkpoint_path):
    """Zeigt detaillierte Informationen über einen Checkpoint"""
    checkpoint_dir = Path(checkpoint_path)
    
    if not checkpoint_dir.exists():
        print(f"❌ Checkpoint nicht gefunden: {checkpoint_path}")
        return
    
    print(f"📁 Checkpoint: {checkpoint_dir.name}")
    print(f"📍 Pfad: {checkpoint_path}")
    
    # Trainer State analysieren
    trainer_state_file = checkpoint_dir / "trainer_state.json"
    if trainer_state_file.exists():
        with open(trainer_state_file, 'r') as f:
            state = json.load(f)
        
        print(f"🔄 Epoch: {state.get('epoch', 'N/A'):.3f}")
        print(f"👣 Global Step: {state.get('global_step', 'N/A')}")
        print(f"📊 Total FLOPs: {state.get('total_flos', 'N/A')}")
        
        # Training History
        if 'log_history' in state and state['log_history']:
            recent_logs = state['log_history'][-5:]  # Letzte 5 Einträge
            print(f"\n📈 Letzte Training-Logs:")
            
            for i, log in enumerate(recent_logs):
                step = log.get('step', 'N/A')
                loss = log.get('train_loss', 'N/A')
                lr = log.get('learning_rate', 'N/A')
                
                if loss != 'N/A':
                    loss = f"{loss:.6f}"
                if lr != 'N/A':
                    lr = f"{lr:.2e}"
                
                print(f"  Step {step}: Loss={loss}, LR={lr}")
    
    # Modell-Dateien prüfen
    model_files = ['pytorch_model.bin', 'adapter_model.bin', 'adapter_config.json']
    print(f"\n📦 Modell-Dateien:")
    for file_name in model_files:
        file_path = checkpoint_dir / file_name
        if file_path.exists():
            size_mb = file_path.stat().st_size / 1024 / 1024
            print(f"  ✅ {file_name} ({size_mb:.1f} MB)")
        else:
            print(f"  ❌ {file_name}")

def resume_training(config_file, checkpoint_path=None, no_resume=False):
    """Startet Training mit Resume-Funktionalität"""
    cmd_parts = ["python", "scripts/clara_train_lora.py", "--config", config_file]
    
    if checkpoint_path:
        cmd_parts.extend(["--resume", checkpoint_path])
    
    if no_resume:
        cmd_parts.append("--no-resume")
    
    import subprocess
    print(f"🚀 Starte Training: {' '.join(cmd_parts)}")
    
    try:
        subprocess.run(cmd_parts, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Training fehlgeschlagen: {e}")
    except KeyboardInterrupt:
        print("\n⏹️  Training unterbrochen")

def cleanup_old_checkpoints(output_dir, keep_count=3):
    """Entfernt alte Checkpoints, behält nur die neuesten"""
    checkpoints = list_checkpoints(output_dir)
    
    if len(checkpoints) <= keep_count:
        print(f"ℹ️  Nur {len(checkpoints)} Checkpoints vorhanden, keine Bereinigung nötig")
        return
    
    # Älteste Checkpoints entfernen
    to_remove = checkpoints[:-keep_count]
    
    print(f"🧹 Entferne {len(to_remove)} alte Checkpoints (behalte {keep_count} neueste):")
    
    for checkpoint in to_remove:
        checkpoint_path = Path(checkpoint['path'])
        try:
            import shutil
            shutil.rmtree(checkpoint_path)
            print(f"  ✅ Entfernt: {checkpoint_path.name}")
        except Exception as e:
            print(f"  ❌ Fehler beim Entfernen von {checkpoint_path.name}: {e}")

def main():
    parser = argparse.ArgumentParser(description="CLARA Training Resume Utility")
    subparsers = parser.add_subparsers(dest='command', help='Verfügbare Kommandos')
    
    # List Command
    list_parser = subparsers.add_parser('list', help='Listet verfügbare Checkpoints auf')
    list_parser.add_argument('--output-dir', default='models/clara_leo_cuda_outputs', 
                           help='Output-Verzeichnis (default: models/clara_leo_cuda_outputs)')
    
    # Info Command
    info_parser = subparsers.add_parser('info', help='Zeigt Checkpoint-Details')
    info_parser.add_argument('checkpoint', help='Pfad zum Checkpoint')
    
    # Resume Command
    resume_parser = subparsers.add_parser('resume', help='Startet Training neu')
    resume_parser.add_argument('--config', default='configs/leo_cuda_config.yaml',
                              help='Konfigurationsdatei (default: configs/leo_cuda_config.yaml)')
    resume_parser.add_argument('--checkpoint', help='Spezifischer Checkpoint zum Fortsetzen')
    resume_parser.add_argument('--no-resume', action='store_true',
                              help='Deaktiviert automatisches Resume (startet neues Training)')
    
    # Cleanup Command
    cleanup_parser = subparsers.add_parser('cleanup', help='Entfernt alte Checkpoints')
    cleanup_parser.add_argument('--output-dir', default='models/clara_leo_cuda_outputs',
                               help='Output-Verzeichnis (default: models/clara_leo_cuda_outputs)')
    cleanup_parser.add_argument('--keep', type=int, default=3,
                               help='Anzahl neuester Checkpoints behalten (default: 3)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    if args.command == 'list':
        print("🔍 VERFÜGBARE CHECKPOINTS")
        print("=" * 50)
        
        checkpoints = list_checkpoints(args.output_dir)
        
        if not checkpoints:
            print("❌ Keine Checkpoints gefunden")
            return
        
        print(f"📁 Output-Dir: {args.output_dir}")
        print(f"📊 Gefunden: {len(checkpoints)} Checkpoints\n")
        
        for checkpoint in checkpoints:
            timestamp = datetime.fromtimestamp(checkpoint['timestamp'])
            loss_str = f"{checkpoint['train_loss']:.6f}" if checkpoint['train_loss'] else "N/A"
            
            print(f"📋 {Path(checkpoint['path']).name}")
            print(f"   Epoch: {checkpoint['epoch']:.3f} | Step: {checkpoint['global_step']} | Loss: {loss_str}")
            print(f"   Erstellt: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
            print()
    
    elif args.command == 'info':
        show_checkpoint_info(args.checkpoint)
    
    elif args.command == 'resume':
        resume_training(args.config, args.checkpoint, args.no_resume)
    
    elif args.command == 'cleanup':
        cleanup_old_checkpoints(args.output_dir, args.keep)

if __name__ == "__main__":
    main()
