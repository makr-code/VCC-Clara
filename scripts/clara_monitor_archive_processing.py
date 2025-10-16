#!/usr/bin/env python3
"""
CLARA Archive Processing Monitor
Überwacht laufende Archive-Verarbeitung in Echtzeit
"""

import time
import json
import psutil
from pathlib import Path
from datetime import datetime, timedelta
import sys

# Projekt-Root zum Python-Pfad hinzufügen
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class ArchiveProcessingMonitor:
    def __init__(self, workspace_dir="Y:/verwLLM"):
        self.workspace = Path(workspace_dir)
        self.output_dir = self.workspace / "data" / "archive_processed"
        self.monitor_file = self.workspace / "archive_monitor.json"
        self.start_time = datetime.now()
        
        self.last_file_count = 0
        self.last_total_size = 0
        self.processing_rate_history = []
    
    def get_current_stats(self):
        """Aktuelle Verarbeitungsstatistiken"""
        if not self.output_dir.exists():
            return {
                'files_count': 0,
                'total_size_mb': 0,
                'latest_file': None,
                'latest_timestamp': None
            }
        
        batch_files = list(self.output_dir.glob("archive_*_batch_*.jsonl"))
        
        if not batch_files:
            return {
                'files_count': 0,
                'total_size_mb': 0,
                'latest_file': None,
                'latest_timestamp': None
            }
        
        total_size = sum(f.stat().st_size for f in batch_files)
        total_size_mb = total_size / 1024 / 1024
        
        # Neueste Datei finden
        latest_file = max(batch_files, key=lambda f: f.stat().st_mtime)
        latest_timestamp = datetime.fromtimestamp(latest_file.stat().st_mtime)
        
        return {
            'files_count': len(batch_files),
            'total_size_mb': total_size_mb,
            'latest_file': latest_file.name,
            'latest_timestamp': latest_timestamp
        }
    
    def calculate_processing_rate(self, current_stats):
        """Berechnet Verarbeitungsgeschwindigkeit"""
        now = datetime.now()
        elapsed_seconds = (now - self.start_time).total_seconds()
        
        if elapsed_seconds < 60:  # Mindestens 1 Minute für sinnvolle Rate
            return None
        
        files_diff = current_stats['files_count'] - self.last_file_count
        size_diff = current_stats['total_size_mb'] - self.last_total_size
        
        if files_diff <= 0:
            return None
        
        # Rate pro Minute
        minutes_elapsed = elapsed_seconds / 60
        files_per_minute = files_diff / minutes_elapsed
        mb_per_minute = size_diff / minutes_elapsed
        
        self.last_file_count = current_stats['files_count']
        self.last_total_size = current_stats['total_size_mb']
        
        return {
            'files_per_minute': files_per_minute,
            'mb_per_minute': mb_per_minute,
            'elapsed_minutes': minutes_elapsed
        }
    
    def get_system_stats(self):
        """Systemressourcen-Statistiken"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        # GPU-Speicher wenn möglich
        gpu_memory = None
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu = gpus[0]
                gpu_memory = {
                    'used_mb': gpu.memoryUsed,
                    'total_mb': gpu.memoryTotal,
                    'percent': (gpu.memoryUsed / gpu.memoryTotal) * 100,
                    'temperature': gpu.temperature
                }
        except ImportError:
            pass
        
        return {
            'cpu_percent': cpu_percent,
            'memory_used_gb': memory.used / 1024 / 1024 / 1024,
            'memory_total_gb': memory.total / 1024 / 1024 / 1024,
            'memory_percent': memory.percent,
            'gpu_memory': gpu_memory
        }
    
    def check_for_errors(self):
        """Prüft auf Fehler in Log-Dateien"""
        errors = []
        
        # PowerShell-Logs prüfen
        for log_file in self.workspace.glob("*.log"):
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'error' in content.lower() or 'exception' in content.lower():
                        errors.append(f"Fehler in {log_file.name}")
            except:
                pass
        
        return errors
    
    def print_status(self, stats, rate, system_stats, errors):
        """Formatierte Status-Ausgabe"""
        # Terminal löschen
        import os
        os.system('cls' if os.name == 'nt' else 'clear')
        
        now = datetime.now()
        runtime = now - self.start_time
        
        print("🗜️  CLARA ARCHIVE PROCESSING MONITOR")
        print("=" * 60)
        print(f"🕐 Start: {self.start_time.strftime('%H:%M:%S')}")
        print(f"⏱️  Laufzeit: {str(runtime).split('.')[0]}")
        print(f"🔄 Update: {now.strftime('%H:%M:%S')}")
        print()
        
        # Verarbeitungsstatistiken
        print("📊 VERARBEITUNG:")
        print(f"   📄 Batch-Dateien: {stats['files_count']}")
        print(f"   📏 Gesamtgröße: {stats['total_size_mb']:.1f} MB")
        
        if stats['latest_file']:
            time_since = now - stats['latest_timestamp']
            print(f"   📝 Letzte Datei: {stats['latest_file']}")
            print(f"   ⏰ Vor: {str(time_since).split('.')[0]}")
        
        if rate:
            print(f"   🚀 Rate: {rate['files_per_minute']:.1f} Dateien/min")
            print(f"   📈 Durchsatz: {rate['mb_per_minute']:.1f} MB/min")
        
        print()
        
        # Systemstatistiken
        print("🖥️  SYSTEM:")
        print(f"   🧠 CPU: {system_stats['cpu_percent']:.1f}%")
        print(f"   💾 RAM: {system_stats['memory_used_gb']:.1f}/{system_stats['memory_total_gb']:.1f} GB ({system_stats['memory_percent']:.1f}%)")
        
        if system_stats['gpu_memory']:
            gpu = system_stats['gpu_memory']
            print(f"   🎮 GPU: {gpu['used_mb']}/{gpu['total_mb']} MB ({gpu['percent']:.1f}%)")
            if gpu['temperature']:
                print(f"   🌡️  GPU Temp: {gpu['temperature']}°C")
        
        print()
        
        # Fehler anzeigen
        if errors:
            print("⚠️  WARNUNGEN:")
            for error in errors:
                print(f"   ❌ {error}")
            print()
        
        # Fortschrittsbalken wenn Rate verfügbar
        if rate and rate['files_per_minute'] > 0:
            # Schätze verbleibende Zeit basierend auf typischer Archivgröße
            estimated_remaining = max(0, 100 - stats['files_count'])  # Grober Schätzwert
            if estimated_remaining > 0:
                eta_minutes = estimated_remaining / rate['files_per_minute']
                eta_time = now + timedelta(minutes=eta_minutes)
                print(f"📅 Geschätzte Fertigstellung: {eta_time.strftime('%H:%M:%S')}")
                print(f"⏳ ETA: {eta_minutes:.0f} Minuten")
        
        print()
        print("Drücke Ctrl+C zum Beenden...")
    
    def save_stats(self, stats, rate, system_stats):
        """Speichert Statistiken für später"""
        data = {
            'timestamp': datetime.now().isoformat(),
            'stats': stats,
            'rate': rate,
            'system': system_stats,
            'runtime_seconds': (datetime.now() - self.start_time).total_seconds()
        }
        
        # An Monitor-Datei anhängen
        with open(self.monitor_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(data, ensure_ascii=False) + '\\n')
    
    def monitor(self, update_interval=30):
        """Hauptüberwachungsschleife"""
        print("🚀 Archive Processing Monitor gestartet...")
        print(f"📂 Überwache: {self.output_dir}")
        print(f"⏱️  Update-Intervall: {update_interval} Sekunden")
        print()
        
        try:
            while True:
                stats = self.get_current_stats()
                rate = self.calculate_processing_rate(stats)
                system_stats = self.get_system_stats()
                errors = self.check_for_errors()
                
                self.print_status(stats, rate, system_stats, errors)
                self.save_stats(stats, rate, system_stats)
                
                time.sleep(update_interval)
                
        except KeyboardInterrupt:
            print("\\n\\n🛑 Monitor gestoppt")
            runtime = datetime.now() - self.start_time
            print(f"⏱️  Gesamte Laufzeit: {str(runtime).split('.')[0]}")
            
            # Finale Statistiken
            final_stats = self.get_current_stats()
            print(f"📊 Finale Statistiken:")
            print(f"   📄 {final_stats['files_count']} Batch-Dateien")
            print(f"   📏 {final_stats['total_size_mb']:.1f} MB verarbeitet")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="CLARA Archive Processing Monitor")
    parser.add_argument("--interval", type=int, default=30, help="Update-Intervall in Sekunden")
    parser.add_argument("--workspace", default="Y:/verwLLM", help="Workspace-Verzeichnis")
    
    args = parser.parse_args()
    
    monitor = ArchiveProcessingMonitor(args.workspace)
    monitor.monitor(args.interval)

if __name__ == "__main__":
    main()
