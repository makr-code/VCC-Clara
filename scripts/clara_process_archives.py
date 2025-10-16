#!/usr/bin/env python3
"""
CLARA Archive Processing Tool
Verarbeitet Archive und extrahiert Trainingsdaten
"""

import sys
import argparse
from pathlib import Path

# Projekt-Root zum Python-Pfad hinzufügen
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data.archive_processor import ArchiveProcessor, process_archive_directory
from src.data.data_processor import VerwaltungsDataProcessor

def main():
    parser = argparse.ArgumentParser(description="CLARA Archive Processing Tool")
    parser.add_argument("--input", required=True, help="Eingabe-Verzeichnis mit Archiven oder einzelnes Archiv")
    parser.add_argument("--output", required=True, help="Ausgabe-Verzeichnis für verarbeitete Daten")
    parser.add_argument("--batch-size", type=int, default=1000, help="Anzahl Texte pro Batch-Datei")
    parser.add_argument("--file-types", nargs="+", default=[".txt", ".md", ".pdf", ".docx", ".json"], 
                       help="Unterstützte Dateitypen")
    parser.add_argument("--extract-here", action="store_true", default=True,
                       help="Archive am gleichen Ort entpacken (Standard)")
    parser.add_argument("--use-temp", action="store_true", 
                       help="Temporäres Verzeichnis für Extraktion verwenden")
    parser.add_argument("--temp-dir", help="Temporäres Verzeichnis für Extraktion")
    parser.add_argument("--keep-extracted", action="store_true", default=True,
                       help="Entpackte Dateien nach Verarbeitung behalten (Standard)")
    parser.add_argument("--max-files", type=int, help="Maximale Anzahl Dateien pro Archiv")
    parser.add_argument("--list-archives", action="store_true", help="Nur Archive auflisten, nicht verarbeiten")
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    if not input_path.exists():
        print(f"❌ Eingabepfad nicht gefunden: {input_path}")
        return 1
    
    # Archive Processor initialisieren
    archive_proc = ArchiveProcessor(
        temp_base_dir=args.temp_dir if args.use_temp else None,
        cleanup_on_exit=not args.keep_extracted
    )
    
    # Unterstützte Formate anzeigen
    print("🗜️  CLARA ARCHIVE PROCESSOR")
    print("=" * 50)
    print("Unterstützte Archive:")
    for ext in archive_proc.archive_handlers.keys():
        print(f"  ✅ {ext}")
    print()
    
    try:
        if input_path.is_file():
            # Einzelnes Archiv verarbeiten
            if not archive_proc.is_archive(input_path):
                print(f"❌ Datei ist kein unterstütztes Archiv: {input_path}")
                return 1
            
            # Archiv-Informationen anzeigen
            info = archive_proc.get_archive_info(input_path)
            print(f"📦 Archiv-Informationen:")
            print(f"   📄 Name: {info['name']}")
            print(f"   📏 Größe: {info['size_mb']:.1f} MB")
            print(f"   📊 Typ: {info['type']}")
            print(f"   📂 Dateien: {info['files_count']}")
            print(f"   📐 Geschätzte Größe: {info['estimated_size_mb']:.1f} MB")
            print()
            
            if args.list_archives:
                return 0
            
            # Verarbeitung
            # Für Archive-Verarbeitung brauchen wir einen einfachen Document Processor
            class SimpleDocumentProcessor:
                def load_and_process(self, file_path):
                    """Lädt und verarbeitet eine Datei"""
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read().strip()
                            if content:
                                return [content]
                    except Exception as e:
                        print(f"⚠️ Fehler beim Lesen von {file_path}: {e}")
                    return []
            
            document_proc = SimpleDocumentProcessor()
            
            print("🚀 Starte Archiv-Verarbeitung...")
            
            # Bestimme Extraktionsverzeichnis
            extract_to = None
            if args.use_temp and args.temp_dir:
                extract_to = Path(args.temp_dir) / f"{input_path.stem}_extracted"
            
            texts = archive_proc.extract_and_process_archive(
                input_path, 
                document_proc,
                file_extensions=args.file_types,
                max_files=args.max_files
            )
            
            # Texte in Batches speichern
            output_path.mkdir(parents=True, exist_ok=True)
            
            batch_files = []
            for batch_num, batch_start in enumerate(range(0, len(texts), args.batch_size), 1):
                batch_texts = texts[batch_start:batch_start + args.batch_size]
                
                batch_file = output_path / f"archive_{input_path.stem}_batch_{batch_num:03d}.jsonl"
                
                import json
                from datetime import datetime
                
                with open(batch_file, 'w', encoding='utf-8') as f:
                    for text in batch_texts:
                        json_entry = {
                            "text": text,
                            "source": f"archive_{input_path.name}",
                            "timestamp": datetime.now().isoformat()
                        }
                        f.write(json.dumps(json_entry, ensure_ascii=False) + '\\n')
                
                batch_files.append(str(batch_file))
                print(f"📄 Batch {batch_num}: {len(batch_texts)} Texte → {batch_file.name}")
            
            print(f"\\n🎉 Verarbeitung abgeschlossen!")
            print(f"   📊 {len(texts)} Texte extrahiert")
            print(f"   📦 {len(batch_files)} Batch-Dateien erstellt")
            
        else:
            # Verzeichnis mit Archiven verarbeiten
            archives = []
            for pattern in ['*.zip', '*.tar', '*.tar.gz', '*.rar', '*.7z', '*.gz', '*.bz2', '*.xz']:
                archives.extend(input_path.glob(pattern))
            
            if not archives:
                print(f"❌ Keine Archive in {input_path} gefunden")
                return 1
            
            print(f"📂 Gefunden: {len(archives)} Archive in {input_path}")
            
            if args.list_archives:
                print("\\n📋 Archive-Liste:")
                for i, archive in enumerate(archives, 1):
                    info = archive_proc.get_archive_info(archive)
                    print(f"  {i:2d}. {archive.name}")
                    print(f"      📏 {info['size_mb']:.1f} MB | 📂 {info['files_count']} Dateien | 📊 {info['type']}")
                return 0
            
            # Alle Archive verarbeiten
            # Für Archive-Verarbeitung brauchen wir einen einfachen Document Processor
            class SimpleDocumentProcessor:
                def load_and_process(self, file_path):
                    """Lädt und verarbeitet eine Datei"""
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read().strip()
                            if content:
                                return [content]
                    except Exception as e:
                        print(f"⚠️ Fehler beim Lesen von {file_path}: {e}")
                    return []
            
            document_proc = SimpleDocumentProcessor()
            
            batch_files = archive_proc.batch_process_archives(
                input_path,
                document_proc,
                output_path,
                batch_size=args.batch_size,
                file_extensions=args.file_types
            )
            
            print(f"\\n🎉 Verarbeitung abgeschlossen!")
            print(f"   📦 {len(archives)} Archive verarbeitet")
            print(f"   📄 {len(batch_files)} Batch-Dateien erstellt")
            print(f"   📂 Ausgabe: {output_path}")
    
    except Exception as e:
        print(f"❌ Fehler: {e}")
        return 1
    
    finally:
        # Aufräumen
        archive_proc.cleanup_all_temp_dirs()
    
    return 0

if __name__ == "__main__":
    exit(main())
