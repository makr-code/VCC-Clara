#!/usr/bin/env python3
"""
CLARA Training Monitor - Echtzeit-Dashboard
Überwacht GPU, Training-Progress und Systemmetriken
"""

import time
import json
import subprocess
import psutil
import torch
from datetime import datetime
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from collections import deque
import threading
import os

class CLARAMonitor:
    def __init__(self, training_dir="models/clara_leo_cuda_outputs", refresh_interval=5):
        self.training_dir = Path(training_dir)
        self.refresh_interval = refresh_interval
        self.metrics_history = {
            'timestamp': deque(maxlen=100),
            'gpu_util': deque(maxlen=100),
            'gpu_memory': deque(maxlen=100),
            'gpu_temp': deque(maxlen=100),
            'cpu_percent': deque(maxlen=100),
            'ram_percent': deque(maxlen=100),
            'training_loss': deque(maxlen=100),
            'learning_rate': deque(maxlen=100)
        }
        self.is_monitoring = True
        
    def get_gpu_stats(self):
        """Holt GPU-Statistiken via nvidia-smi"""
        try:
            result = subprocess.run([
                'nvidia-smi', '--query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu',
                '--format=csv,noheader,nounits'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                stats = result.stdout.strip().split(', ')
                return {
                    'gpu_util': float(stats[0]),
                    'memory_used': float(stats[1]),
                    'memory_total': float(stats[2]),
                    'temperature': float(stats[3])
                }
        except Exception as e:
            print(f"GPU Stats Error: {e}")
        return None
    
    def get_training_logs(self):
        """Liest Training-Logs für Loss und Learning Rate"""
        log_file = self.training_dir / "trainer_state.json"
        if log_file.exists():
            try:
                with open(log_file, 'r') as f:
                    state = json.load(f)
                
                if 'log_history' in state and state['log_history']:
                    latest = state['log_history'][-1]
                    return {
                        'loss': latest.get('train_loss', None),
                        'learning_rate': latest.get('learning_rate', None),
                        'epoch': latest.get('epoch', None),
                        'step': latest.get('step', None)
                    }
            except Exception as e:
                print(f"Training Logs Error: {e}")
        return None
    
    def collect_metrics(self):
        """Sammelt alle Metriken"""
        timestamp = datetime.now()
        
        # GPU Stats
        gpu_stats = self.get_gpu_stats()
        if gpu_stats:
            gpu_util = gpu_stats['gpu_util']
            gpu_memory_percent = (gpu_stats['memory_used'] / gpu_stats['memory_total']) * 100
            gpu_temp = gpu_stats['temperature']
        else:
            gpu_util = gpu_memory_percent = gpu_temp = 0
        
        # System Stats
        cpu_percent = psutil.cpu_percent()
        ram_percent = psutil.virtual_memory().percent
        
        # Training Stats
        training_stats = self.get_training_logs()
        training_loss = training_stats['loss'] if training_stats else None
        learning_rate = training_stats['learning_rate'] if training_stats else None
        
        # Zu Historie hinzufügen
        self.metrics_history['timestamp'].append(timestamp)
        self.metrics_history['gpu_util'].append(gpu_util)
        self.metrics_history['gpu_memory'].append(gpu_memory_percent)
        self.metrics_history['gpu_temp'].append(gpu_temp)
        self.metrics_history['cpu_percent'].append(cpu_percent)
        self.metrics_history['ram_percent'].append(ram_percent)
        self.metrics_history['training_loss'].append(training_loss)
        self.metrics_history['learning_rate'].append(learning_rate)
        
        return {
            'timestamp': timestamp,
            'gpu_util': gpu_util,
            'gpu_memory_percent': gpu_memory_percent,
            'gpu_temp': gpu_temp,
            'cpu_percent': cpu_percent,
            'ram_percent': ram_percent,
            'training_loss': training_loss,
            'learning_rate': learning_rate,
            'training_stats': training_stats
        }
    
    def print_status(self, metrics):
        """Druckt aktuellen Status"""
        os.system('cls' if os.name == 'nt' else 'clear')
        
        print("🚀 CLARA TRAINING MONITOR")
        print("=" * 60)
        print(f"⏰ Zeit: {metrics['timestamp'].strftime('%H:%M:%S')}")
        print()
        
        # GPU Status
        print("🎮 GPU STATUS:")
        print(f"  📊 Auslastung: {metrics['gpu_util']:.1f}%")
        print(f"  💾 Speicher: {metrics['gpu_memory_percent']:.1f}%")
        print(f"  🌡️  Temperatur: {metrics['gpu_temp']:.1f}°C")
        
        # System Status
        print("\n💻 SYSTEM:")
        print(f"  🔥 CPU: {metrics['cpu_percent']:.1f}%")
        print(f"  🧠 RAM: {metrics['ram_percent']:.1f}%")
        
        # Training Status
        print("\n🎯 TRAINING:")
        if metrics['training_stats']:
            stats = metrics['training_stats']
            if stats['loss']:
                print(f"  📉 Loss: {stats['loss']:.6f}")
            if stats['learning_rate']:
                print(f"  📈 Learning Rate: {stats['learning_rate']:.2e}")
            if stats['epoch']:
                print(f"  🔄 Epoch: {stats['epoch']:.2f}")
            if stats['step']:
                print(f"  👣 Step: {stats['step']}")
        else:
            print("  ⏳ Warten auf Training-Logs...")
        
        # Status Bars
        print("\n" + "─" * 60)
        print("📊 GPU AUSLASTUNG:")
        self.print_progress_bar(metrics['gpu_util'], 100, "GPU")
        print("\n💾 GPU SPEICHER:")
        self.print_progress_bar(metrics['gpu_memory_percent'], 100, "MEM")
        
        # Warnung bei kritischen Werten
        warnings = []
        if metrics['gpu_temp'] > 80:
            warnings.append("🚨 GPU Temperatur hoch!")
        if metrics['gpu_memory_percent'] > 90:
            warnings.append("⚠️  GPU Speicher fast voll!")
        if metrics['cpu_percent'] > 90:
            warnings.append("⚠️  CPU Auslastung hoch!")
        
        if warnings:
            print("\n" + "🚨 WARNUNGEN:")
            for warning in warnings:
                print(f"  {warning}")
        
        print(f"\n⏭️  Nächstes Update in {self.refresh_interval}s...")
    
    def print_progress_bar(self, value, max_value, label, length=40):
        """Druckt eine Fortschrittsleiste"""
        percent = (value / max_value) * 100
        filled = int(length * percent / 100)
        bar = "█" * filled + "░" * (length - filled)
        print(f"{label}: |{bar}| {percent:.1f}%")
    
    def save_metrics_log(self, metrics):
        """Speichert Metriken in Log-Datei"""
        log_file = "monitoring_log.jsonl"
        with open(log_file, 'a') as f:
            # Konvertiere datetime zu string für JSON
            log_entry = metrics.copy()
            log_entry['timestamp'] = metrics['timestamp'].isoformat()
            f.write(json.dumps(log_entry) + '\n')
    
    def monitoring_loop(self):
        """Haupt-Monitoring-Schleife"""
        print("🚀 CLARA Training Monitor gestartet...")
        print("💡 Drücken Sie Ctrl+C zum Beenden")
        
        try:
            while self.is_monitoring:
                metrics = self.collect_metrics()
                self.print_status(metrics)
                self.save_metrics_log(metrics)
                time.sleep(self.refresh_interval)
                
        except KeyboardInterrupt:
            print("\n\n🛑 Monitoring gestoppt.")
            self.is_monitoring = False
    
    def generate_summary_report(self):
        """Erstellt einen Zusammenfassungsbericht"""
        if not self.metrics_history['timestamp']:
            print("Keine Daten für Bericht verfügbar.")
            return
        
        print("\n" + "="*60)
        print("📊 TRAINING SESSION SUMMARY")
        print("="*60)
        
        # Zeitraum
        start_time = self.metrics_history['timestamp'][0]
        end_time = self.metrics_history['timestamp'][-1]
        duration = end_time - start_time
        
        print(f"⏰ Zeitraum: {start_time.strftime('%H:%M:%S')} - {end_time.strftime('%H:%M:%S')}")
        print(f"⌛ Dauer: {duration}")
        
        # GPU Statistiken
        gpu_utils = [x for x in self.metrics_history['gpu_util'] if x > 0]
        if gpu_utils:
            print(f"\n🎮 GPU Performance:")
            print(f"  📊 Durchschnittliche Auslastung: {sum(gpu_utils)/len(gpu_utils):.1f}%")
            print(f"  📊 Maximale Auslastung: {max(gpu_utils):.1f}%")
        
        # Training Progress
        losses = [x for x in self.metrics_history['training_loss'] if x is not None]
        if len(losses) > 1:
            print(f"\n🎯 Training Progress:")
            print(f"  📉 Start Loss: {losses[0]:.6f}")
            print(f"  📉 Ende Loss: {losses[-1]:.6f}")
            print(f"  📈 Verbesserung: {((losses[0] - losses[-1])/losses[0]*100):.2f}%")

def main():
    # Training-Verzeichnis aus Config lesen
    training_dir = "models/clara_leo_cuda_outputs"
    
    monitor = CLARAMonitor(training_dir=training_dir, refresh_interval=5)
    
    try:
        monitor.monitoring_loop()
    finally:
        monitor.generate_summary_report()

if __name__ == "__main__":
    main()
