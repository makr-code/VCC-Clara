#!/usr/bin/env python3
"""
CLARA Archive Manager
Verwaltet und überwacht Archive-Verarbeitung
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Projekt-Root zum Python-Pfad hinzufügen
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data.archive_processor import ArchiveProcessor

class ArchiveManager:
    def __init__(self, workspace_dir="Y:/verwLLM"):
        self.workspace = Path(workspace_dir)
        self.archive_proc = ArchiveProcessor()
        self.archives_dir = self.workspace / "data" / "archives"
        self.output_dir = self.workspace / "data" / "archive_processed"
        self.status_file = self.workspace / "archive_status.json"
        
        # Verzeichnisse erstellen
        self.archives_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def scan_archives(self, recursive=True):
        """Scannt alle Archive im Verzeichnis"""
        archives = []
        patterns = ['*.zip', '*.tar', '*.tar.gz', '*.rar', '*.7z', '*.gz', '*.bz2', '*.xz']
        
        for pattern in patterns:
            # Rekursiv oder nur im Hauptverzeichnis suchen
            search_pattern = f"**/{pattern}" if recursive else pattern
            for archive in self.archives_dir.glob(search_pattern):
                info = self.archive_proc.get_archive_info(archive)
                # Relativer Pfad für bessere Übersicht
                relative_path = archive.relative_to(self.archives_dir)
                archives.append({
                    'name': str(relative_path),
                    'path': str(archive),
                    'size_mb': info['size_mb'],
                    'files_count': info['files_count'],
                    'type': info['type'],
                    'estimated_size_mb': info['estimated_size_mb'],
                    'processed': self._is_processed(archive.name)
                })
        
        return sorted(archives, key=lambda x: x['size_mb'], reverse=True)
    
    def _is_processed(self, archive_name):
        """Prüft ob Archiv bereits verarbeitet wurde"""
        stem = Path(archive_name).stem
        pattern = f"archive_{stem}_batch_*.jsonl"
        return bool(list(self.output_dir.glob(pattern)))
    
    def get_processing_status(self):
        """Liefert Übersicht über Verarbeitungsstatus"""
        archives = self.scan_archives()
        
        total_archives = len(archives)
        processed = sum(1 for a in archives if a['processed'])
        unprocessed = total_archives - processed
        
        total_size_mb = sum(a['size_mb'] for a in archives)
        processed_size_mb = sum(a['size_mb'] for a in archives if a['processed'])
        unprocessed_size_mb = total_size_mb - processed_size_mb
        
        return {
            'total_archives': total_archives,
            'processed': processed,
            'unprocessed': unprocessed,
            'total_size_mb': total_size_mb,
            'processed_size_mb': processed_size_mb,
            'unprocessed_size_mb': unprocessed_size_mb,
            'archives': archives
        }
    
    def estimate_processing_time(self, size_mb):
        """Schätzt Verarbeitungszeit basierend auf Archivgröße"""
        # Schätzung: ~10MB/Minute für Archive
        minutes = size_mb / 10
        
        if minutes < 1:
            return f"{int(minutes * 60)} Sekunden"
        elif minutes < 60:
            return f"{int(minutes)} Minuten"
        else:
            hours = int(minutes // 60)
            mins = int(minutes % 60)
            return f"{hours}h {mins}m"
    
    def print_status_overview(self):
        """Zeigt detaillierten Status an"""
        status = self.get_processing_status()
        
        print("🗜️  CLARA ARCHIVE MANAGER")
        print("=" * 60)
        print()
        
        print("📊 ÜBERSICHT:")
        print(f"   📦 Archive gesamt: {status['total_archives']}")
        print(f"   ✅ Verarbeitet: {status['processed']}")
        print(f"   ⏳ Ausstehend: {status['unprocessed']}")
        print(f"   📏 Gesamtgröße: {status['total_size_mb']:.1f} MB")
        print(f"   🔄 Unverarbeitet: {status['unprocessed_size_mb']:.1f} MB")
        print()
        
        if status['unprocessed'] > 0:
            est_time = self.estimate_processing_time(status['unprocessed_size_mb'])
            print(f"⏱️  Geschätzte Verarbeitungszeit: {est_time}")
            print()
        
        print("📋 ARCHIVE DETAILS:")
        print("-" * 60)
        
        for i, archive in enumerate(status['archives'], 1):
            status_icon = "✅" if archive['processed'] else "⏳"
            est_time = self.estimate_processing_time(archive['size_mb'])
            
            print(f"{i:2d}. {status_icon} {archive['name']}")
            print(f"     📏 {archive['size_mb']:6.1f} MB | 📂 {archive['files_count']:4d} Dateien | ⏱️  {est_time}")
            print(f"     📊 {archive['type']} | 📐 ~{archive['estimated_size_mb']:.1f} MB extrahiert")
            print()
    
    def list_batch_files(self):
        """Listet alle erstellten Batch-Dateien auf"""
        batch_files = list(self.output_dir.glob("archive_*_batch_*.jsonl"))
        
        if not batch_files:
            print("📄 Keine Batch-Dateien gefunden")
            return
        
        print(f"📄 BATCH-DATEIEN ({len(batch_files)}):")
        print("-" * 60)
        
        # Nach Archiv-Namen gruppieren
        archives = {}
        for batch_file in batch_files:
            # Format: archive_<name>_batch_<num>.jsonl
            parts = batch_file.stem.split('_')
            if len(parts) >= 4 and parts[0] == 'archive' and parts[-2] == 'batch':
                archive_name = '_'.join(parts[1:-2])
                if archive_name not in archives:
                    archives[archive_name] = []
                archives[archive_name].append(batch_file)
        
        for archive_name, batches in sorted(archives.items()):
            print(f"📦 {archive_name}:")
            total_size = sum(f.stat().st_size for f in batches)
            print(f"   📄 {len(batches)} Batches | 📏 {total_size / 1024 / 1024:.1f} MB")
            
            for batch in sorted(batches):
                size_mb = batch.stat().st_size / 1024 / 1024
                print(f"     📝 {batch.name} ({size_mb:.1f} MB)")
            print()
    
    def recommend_processing_order(self):
        """Empfiehlt Reihenfolge für Verarbeitung"""
        status = self.get_processing_status()
        unprocessed = [a for a in status['archives'] if not a['processed']]
        
        if not unprocessed:
            print("✅ Alle Archive sind bereits verarbeitet!")
            return
        
        print("💡 EMPFOHLENE VERARBEITUNGSREIHENFOLGE:")
        print("-" * 60)
        
        # Sortiere nach Größe (kleinste zuerst für schnelle Erfolge)
        small_first = sorted(unprocessed, key=lambda x: x['size_mb'])
        
        print("🚀 Schnelle Erfolge (kleine Archive zuerst):")
        for i, archive in enumerate(small_first[:5], 1):
            est_time = self.estimate_processing_time(archive['size_mb'])
            print(f"  {i}. {archive['name']} ({archive['size_mb']:.1f} MB, ~{est_time})")
        
        print()
        
        # Sortiere nach geschätzter Anzahl Texte (potentiell wertvollste zuerst)
        value_first = sorted(unprocessed, key=lambda x: x['files_count'], reverse=True)
        
        print("💎 Wertvolle Archive (viele Dateien):")
        for i, archive in enumerate(value_first[:5], 1):
            est_time = self.estimate_processing_time(archive['size_mb'])
            print(f"  {i}. {archive['name']} ({archive['files_count']} Dateien, ~{est_time})")
    
    def generate_processing_script(self, archive_names=None):
        """Generiert PowerShell-Script für automatische Verarbeitung"""
        status = self.get_processing_status()
        
        if archive_names:
            archives = [a for a in status['archives'] if a['name'] in archive_names and not a['processed']]
        else:
            archives = [a for a in status['archives'] if not a['processed']]
        
        if not archives:
            print("❌ Keine unverarbeiteten Archive gefunden")
            return
        
        script_path = self.workspace / "process_archives_batch.ps1"
        
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write("# CLARA Archive Processing Script\\n")
            f.write(f"# Generiert am: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\\n")
            f.write(f"# Verarbeitet {len(archives)} Archive\\n\\n")
            
            f.write("$ErrorActionPreference = 'Continue'\\n")
            f.write("$startTime = Get-Date\\n\\n")
            
            for i, archive in enumerate(archives, 1):
                f.write(f"# Archive {i}/{len(archives)}: {archive['name']}\\n")
                f.write(f"Write-Host '🚀 Verarbeite Archive {i}/{len(archives)}: {archive['name']}' -ForegroundColor Green\\n")
                
                cmd = f"python scripts/process_archives.py --input data/archives/{archive['name']} --output data/archive_processed"
                f.write(f"{cmd}\\n")
                f.write("if ($LASTEXITCODE -ne 0) { Write-Host '❌ Fehler bei Verarbeitung' -ForegroundColor Red }\\n")
                f.write("Write-Host ''\\n\\n")
            
            f.write("$endTime = Get-Date\\n")
            f.write("$duration = $endTime - $startTime\\n")
            f.write("Write-Host '✅ Alle Archive verarbeitet in:' $duration.ToString() -ForegroundColor Green\\n")
        
        print(f"📝 PowerShell-Script erstellt: {script_path}")
        print("\\n🚀 Ausführen mit:")
        print(f"   PowerShell -ExecutionPolicy Bypass -File {script_path}")
        
        return str(script_path)

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="CLARA Archive Manager")
    parser.add_argument("--scan", action="store_true", help="Archive scannen und Status anzeigen")
    parser.add_argument("--list-batches", action="store_true", help="Batch-Dateien auflisten")
    parser.add_argument("--recommend", action="store_true", help="Verarbeitungsreihenfolge empfehlen")
    parser.add_argument("--generate-script", nargs='*', help="PowerShell-Script generieren (optional: Archive-Namen)")
    
    args = parser.parse_args()
    
    manager = ArchiveManager()
    
    if args.scan or (not any([args.list_batches, args.recommend, args.generate_script is not None])):
        manager.print_status_overview()
    
    if args.list_batches:
        print()
        manager.list_batch_files()
    
    if args.recommend:
        print()
        manager.recommend_processing_order()
    
    if args.generate_script is not None:
        print()
        manager.generate_processing_script(args.generate_script if args.generate_script else None)

if __name__ == "__main__":
    main()
