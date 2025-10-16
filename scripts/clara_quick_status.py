#!/usr/bin/env python3
"""
CLARA Quick Status - Schneller Training-Status Check
"""

import subprocess
import json
import psutil
import torch
import yaml
from pathlib import Path
from datetime import datetime, timedelta
from datasets import load_dataset

def calculate_training_time_estimate(config_path):
    """Berechnet Trainingszeit-Schätzungen basierend auf Konfiguration"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # Dataset-Größe ermitteln
        data_path = config['data']['train_file']
        if Path(data_path).exists():
            dataset = load_dataset('json', data_files=data_path, split='train')
            total_samples = len(dataset)
        else:
            total_samples = 10000  # Fallback-Schätzung
        
        # Training-Parameter
        batch_size = config['training']['batch_size']
        gradient_acc_steps = config['training']['gradient_accumulation_steps']
        num_epochs = config['training']['num_epochs']
        max_length = config['data']['max_length']
        
        # Effektive Batch-Größe
        effective_batch_size = batch_size * gradient_acc_steps
        
        # Steps pro Epoch
        steps_per_epoch = total_samples // effective_batch_size
        total_steps = steps_per_epoch * num_epochs
        
        # GPU-spezifische Geschwindigkeitsschätzungen (Samples/Sekunde)
        gpu_speeds = {
            'RTX 3060': {'7B': 2.5, '13B': 1.2},  # Mit LoRA
            'RTX 4090': {'7B': 8.0, '13B': 4.0},
            'RTX 3080': {'7B': 4.5, '13B': 2.0},
            'A100': {'7B': 15.0, '13B': 8.0},
            'default': {'7B': 2.0, '13B': 1.0}
        }
        
        # GPU erkennen
        try:
            result = subprocess.run(['nvidia-smi', '--query-gpu=name', '--format=csv,noheader'], 
                                  capture_output=True, text=True)
            gpu_name = result.stdout.strip()
            
            # GPU-Typ bestimmen
            if 'RTX 3060' in gpu_name:
                gpu_type = 'RTX 3060'
            elif 'RTX 4090' in gpu_name:
                gpu_type = 'RTX 4090'
            elif 'RTX 3080' in gpu_name:
                gpu_type = 'RTX 3080'
            elif 'A100' in gpu_name:
                gpu_type = 'A100'
            else:
                gpu_type = 'default'
        except:
            gpu_type = 'default'
            gpu_name = 'Unbekannt'
        
        # Modell-Größe schätzen (basierend auf Namen)
        model_name = config['model'].get('name', config['model'].get('base_model', '')).lower()
        if '7b' in model_name:
            model_size = '7B'
        elif '13b' in model_name:
            model_size = '13B'
        else:
            model_size = '7B'  # Default
        
        # Geschwindigkeit abrufen
        speed = gpu_speeds[gpu_type][model_size]
        
        # Zeit pro Sample (in Sekunden)
        # Berücksichtigt Sequenzlänge (längere Sequenzen = langsamer)
        sequence_factor = max_length / 512  # Basis: 512 Token
        time_per_sample = sequence_factor / speed
        
        # LoRA-Faktor (LoRA ist schneller als Full Fine-tuning)
        lora_factor = 0.7  # 30% schneller mit LoRA
        time_per_sample *= lora_factor
        
        # Multi-GPU Faktor (falls konfiguriert)
        multi_gpu_factor = 1.0
        if 'multi_gpu' in config_path or 'ddp' in str(config).lower():
            # Schätze GPU-Anzahl aus Konfiguration oder System
            try:
                gpu_count = torch.cuda.device_count() if torch.cuda.is_available() else 1
                if gpu_count > 1:
                    # Nicht-lineare Skalierung (Kommunikations-Overhead)
                    if gpu_count == 2:
                        multi_gpu_factor = 0.55  # ~1.8x speedup
                    elif gpu_count == 4:
                        multi_gpu_factor = 0.30  # ~3.3x speedup
                    else:
                        multi_gpu_factor = 0.25  # ~4x speedup
            except:
                pass
        
        time_per_sample *= multi_gpu_factor
        
        # Gesamtzeit berechnen
        total_time_seconds = total_samples * num_epochs * time_per_sample
        
        # Zeit pro Epoch
        time_per_epoch_seconds = total_samples * time_per_sample
        
        return {
            'total_samples': total_samples,
            'steps_per_epoch': steps_per_epoch,
            'total_steps': total_steps,
            'effective_batch_size': effective_batch_size,
            'gpu_name': gpu_name,
            'gpu_type': gpu_type,
            'model_size': model_size,
            'speed_samples_per_sec': speed,
            'time_per_epoch': time_per_epoch_seconds,
            'total_time': total_time_seconds,
            'num_epochs': num_epochs
        }
    
    except Exception as e:
        return {'error': str(e)}

def format_time_estimate(seconds):
    """Formatiert Sekunden in lesbares Format"""
    if seconds < 60:
        return f"{seconds:.0f} Sekunden"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f} Minuten"
    elif seconds < 86400:
        hours = seconds / 3600
        return f"{hours:.1f} Stunden"
    else:
        days = seconds / 86400
        hours_remainder = (seconds % 86400) / 3600
        if days >= 7:
            weeks = days / 7
            return f"{weeks:.1f} Wochen"
        elif hours_remainder > 0.5:
            return f"{days:.0f} Tage {hours_remainder:.0f}h"
        else:
            return f"{days:.1f} Tage"

def quick_status():
    print("🚀 CLARA TRAINING - QUICK STATUS")
    print("=" * 70)
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # GPU Status
    try:
        result = subprocess.run([
            'nvidia-smi', '--query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu',
            '--format=csv,noheader,nounits'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            stats = result.stdout.strip().split(', ')
            gpu_util = float(stats[0])
            memory_used = float(stats[1])
            memory_total = float(stats[2])
            temp = float(stats[3])
            memory_percent = (memory_used / memory_total) * 100
            
            # Status-Emoji
            if gpu_util > 80:
                status_icon = "✅ AKTIV"
            elif gpu_util > 20:
                status_icon = "🟡 LÄUFT"
            else:
                status_icon = "🔴 INAKTIV"
            
            print(f"🎮 GPU: {gpu_util:.1f}% | {memory_used:.0f}/{memory_total:.0f}MB ({memory_percent:.1f}%) | {temp:.1f}°C | {status_icon}")
        else:
            print("❌ GPU Status nicht verfügbar")
    except:
        print("❌ nvidia-smi nicht verfügbar")
    
    print()
    
    # System Status
    cpu_percent = psutil.cpu_percent()
    memory = psutil.virtual_memory()
    print(f"💻 System: CPU {cpu_percent:.1f}% | RAM {memory.percent:.1f}% ({memory.used//1024//1024:.0f}/{memory.total//1024//1024:.0f}MB)")
    
    print()
    
    # Trainingszeit-Schätzungen
    print("⏱️  TRAININGSZEIT-SCHÄTZUNGEN:")
    
    # Verschiedene Konfigurationen prüfen
    config_files = [
        ('configs/leo_cuda_config.yaml', 'Leo CUDA'),
        ('configs/rtx3060_config.yaml', 'RTX 3060'),
        ('configs/minimal_config.yaml', 'Minimal'),
        ('configs/multi_gpu_config.yaml', 'Multi-GPU'),
        ('configs/qlora_config.yaml', 'QLoRA')
    ]
    
    found_configs = []
    for config_path, config_name in config_files:
        if Path(config_path).exists():
            found_configs.append((config_path, config_name))
    
    if found_configs:
        for config_path, config_name in found_configs[:3]:  # Maximal 3 zeigen
            estimate = calculate_training_time_estimate(config_path)
            
            if 'error' not in estimate:
                # Speicher-Schätzung
                memory_status = "?"
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config = yaml.safe_load(f)
                    
                    batch_size = config['training']['batch_size']
                    max_length = config['data']['max_length']
                    
                    # Grobe Speicherschätzung (MB)
                    base_memory = 8000 if estimate['model_size'] == '7B' else 15000
                    batch_memory = batch_size * max_length * 0.002
                    total_memory = base_memory + batch_memory
                    
                    if total_memory > 12000:
                        memory_status = f"⚠️{total_memory:.0f}MB"
                    elif total_memory > 10000:
                        memory_status = f"🟡{total_memory:.0f}MB"
                    else:
                        memory_status = f"✅{total_memory:.0f}MB"
                except:
                    memory_status = "?"
                
                print(f"  📋 {config_name:10}: {estimate['total_samples']:,} Samples x{estimate['num_epochs']}E | "
                      f"Batch {estimate['effective_batch_size']} | {estimate['speed_samples_per_sec']:.1f}S/s | "
                      f"Epoch: {format_time_estimate(estimate['time_per_epoch'])} | "
                      f"Total: {format_time_estimate(estimate['total_time'])} | {memory_status}")
            else:
                print(f"  ❌ {config_name}: {estimate['error']}")
    else:
        print("  ⚠️  Keine Konfigurationsdateien gefunden")
    
    print()
    
    # Aktuelle Training-Geschwindigkeit (falls Training läuft)
    training_dir = Path("models/clara_leo_cuda_outputs")
    if training_dir.exists():
        files = list(training_dir.glob("*"))
        trainer_state = training_dir / "trainer_state.json"
        
        if trainer_state.exists():
            try:
                with open(trainer_state, 'r') as f:
                    state = json.load(f)
                
                current_step = state.get('global_step', 0)
                current_epoch = state.get('epoch', 0)
                
                # Basis-Info
                print(f"📁 Training: {len(files)} Dateien | Epoch {current_epoch:.2f} | Step {current_step}")
                
                # Training-Fortschritt analysieren
                if 'log_history' in state and len(state['log_history']) > 1:
                    recent_logs = state['log_history'][-5:]  # Letzte 5 Einträge
                    
                    if len(recent_logs) >= 2:
                        first_log = recent_logs[0]
                        last_log = recent_logs[-1]
                        
                        step_diff = last_log.get('step', 0) - first_log.get('step', 0)
                        
                        # Geschwindigkeit und verbleibende Zeit
                        progress_info = ""
                        if 'train_runtime' in last_log and 'train_runtime' in first_log:
                            time_diff = last_log['train_runtime'] - first_log['train_runtime']
                            if time_diff > 0:
                                steps_per_second = step_diff / time_diff
                                progress_info += f" | {steps_per_second:.2f} Steps/s"
                                
                                # Verbleibende Zeit
                                try:
                                    config_path = 'configs/leo_cuda_config.yaml'
                                    if Path(config_path).exists():
                                        estimate = calculate_training_time_estimate(config_path)
                                        if 'error' not in estimate:
                                            remaining_steps = estimate['total_steps'] - current_step
                                            if remaining_steps > 0:
                                                remaining_time = remaining_steps / steps_per_second
                                                progress_percent = (current_step/estimate['total_steps']*100)
                                                progress_info += f" | {progress_percent:.1f}% | ETA: {format_time_estimate(remaining_time)}"
                                except:
                                    pass
                        
                        # Loss-Info
                        if 'train_loss' in recent_logs[-1]:
                            current_loss = recent_logs[-1]['train_loss']
                            loss_info = f" | Loss: {current_loss:.6f}"
                            
                            # Loss-Trend
                            if len(recent_logs) >= 3:
                                prev_loss = recent_logs[-3]['train_loss']
                                loss_change = current_loss - prev_loss
                                trend = "📈" if loss_change > 0 else "📉"
                                loss_info += f" {trend}{loss_change:+.6f}"
                            
                            progress_info += loss_info
                        
                        if progress_info:
                            print(f"� Fortschritt:{progress_info}")
                        
            except Exception as e:
                print(f"� Training: {len(files)} Dateien | ⚠️ State-Datei nicht lesbar")
        else:
            print(f"📁 Training: {len(files)} Dateien | ⏳ Logs noch nicht verfügbar")
    else:
        print("📁 Training: ⏳ Verzeichnis noch nicht erstellt")
    
    print()
    
    # Python Processes - kompakt
    python_processes = []
    for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
        try:
            if proc.info['name'] == 'python.exe':
                memory_mb = proc.info['memory_info'].rss / 1024 / 1024
                python_processes.append(f"PID{proc.info['pid']}:{memory_mb:.0f}MB")
        except:
            pass
    
    if python_processes:
        print(f"🐍 Python: {' | '.join(python_processes[:4])}")  # Max 4 Prozesse
    
    print("=" * 70)

if __name__ == "__main__":
    quick_status()
