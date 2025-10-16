#!/usr/bin/env python3
"""
Intelligenter Batch-Processor mit Duplikatserkennung
Verfolgt bereits verarbeitete Dateien und vermeidet Wiederholung
"""

import hashlib
import json
import time
import sqlite3
from pathlib import Path
from typing import Set, Dict, Optional, List
from dataclasses import dataclass
from datetime import datetime

@dataclass
class FileRecord:
    """Record für verarbeitete Datei"""
    file_path: str
    file_hash: str
    size: int
    modified_time: float
    processed_time: float
    output_batch: str

class ProcessingCache:
    """Cache für verarbeitete Dateien mit SQLite Backend"""
    
    def __init__(self, cache_dir: Path = Path("data/.processing_cache")):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(exist_ok=True)
        self.db_path = self.cache_dir / "processing_cache.db"
        self._init_database()
    
    def _init_database(self):
        """Initialisiert SQLite-Datenbank"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS processed_files (
                    file_path TEXT PRIMARY KEY,
                    file_hash TEXT NOT NULL,
                    size INTEGER NOT NULL,
                    modified_time REAL NOT NULL,
                    processed_time REAL NOT NULL,
                    output_batch TEXT NOT NULL
                )
            """)
            
            # Index für bessere Performance
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_file_hash 
                ON processed_files(file_hash)
            """)
    
    def get_file_hash(self, file_path: Path) -> str:
        """Berechnet SHA-256 Hash einer Datei"""
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                # Datei in Chunks lesen für große Dateien
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            return sha256_hash.hexdigest()
        except Exception as e:
            # Fallback: Hash aus Pfad und Metadaten
            fallback_str = f"{file_path}_{file_path.stat().st_size}_{file_path.stat().st_mtime}"
            return hashlib.sha256(fallback_str.encode()).hexdigest()
    
    def is_file_processed(self, file_path: Path) -> tuple[bool, Optional[FileRecord]]:
        """
        Prüft ob Datei bereits verarbeitet wurde
        
        Returns:
            (is_processed, record): Tuple mit Status und Record falls vorhanden
        """
        try:
            stat = file_path.stat()
            current_hash = self.get_file_hash(file_path)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT file_hash, size, modified_time, processed_time, output_batch
                    FROM processed_files 
                    WHERE file_path = ?
                """, (str(file_path),))
                
                row = cursor.fetchone()
                
                if row is None:
                    return False, None
                
                stored_hash, stored_size, stored_mtime, processed_time, output_batch = row
                
                # Prüfe ob Datei sich geändert hat
                if (stored_hash == current_hash and 
                    stored_size == stat.st_size and 
                    abs(stored_mtime - stat.st_mtime) < 1.0):  # 1 Sekunde Toleranz
                    
                    record = FileRecord(
                        file_path=str(file_path),
                        file_hash=stored_hash,
                        size=stored_size,
                        modified_time=stored_mtime,
                        processed_time=processed_time,
                        output_batch=output_batch
                    )
                    return True, record
                else:
                    # Datei hat sich geändert, entferne alten Eintrag
                    conn.execute("DELETE FROM processed_files WHERE file_path = ?", (str(file_path),))
                    return False, None
                    
        except Exception as e:
            print(f"Fehler beim Prüfen von {file_path}: {e}")
            return False, None
    
    def mark_file_processed(self, file_path: Path, output_batch: str):
        """Markiert Datei als verarbeitet"""
        try:
            stat = file_path.stat()
            file_hash = self.get_file_hash(file_path)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO processed_files 
                    (file_path, file_hash, size, modified_time, processed_time, output_batch)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    str(file_path),
                    file_hash,
                    stat.st_size,
                    stat.st_mtime,
                    time.time(),
                    output_batch
                ))
        except Exception as e:
            print(f"Fehler beim Markieren von {file_path}: {e}")
    
    def get_stats(self) -> Dict:
        """Statistiken über verarbeitete Dateien"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT 
                        COUNT(*) as total_files,
                        COUNT(DISTINCT file_hash) as unique_files,
                        COUNT(DISTINCT output_batch) as batches,
                        MIN(processed_time) as first_processed,
                        MAX(processed_time) as last_processed,
                        SUM(size) as total_size
                    FROM processed_files
                """)
                
                row = cursor.fetchone()
                if row:
                    total, unique, batches, first, last, size = row
                    return {
                        'total_files': total or 0,
                        'unique_files': unique or 0,
                        'duplicate_files': (total or 0) - (unique or 0),
                        'total_batches': batches or 0,
                        'first_processed': datetime.fromtimestamp(first) if first else None,
                        'last_processed': datetime.fromtimestamp(last) if last else None,
                        'total_size_mb': (size or 0) / 1024 / 1024
                    }
        except Exception as e:
            print(f"Fehler beim Abrufen der Statistiken: {e}")
            
        return {}
    
    def clear_cache(self):
        """Löscht kompletten Cache"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM processed_files")
            print("✅ Processing-Cache gelöscht")
        except Exception as e:
            print(f"❌ Fehler beim Löschen des Cache: {e}")
    
    def remove_missing_files(self):
        """Entfernt Einträge für nicht mehr existierende Dateien"""
        removed_count = 0
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT file_path FROM processed_files")
                all_paths = [row[0] for row in cursor.fetchall()]
                
                for file_path_str in all_paths:
                    if not Path(file_path_str).exists():
                        conn.execute("DELETE FROM processed_files WHERE file_path = ?", (file_path_str,))
                        removed_count += 1
                        
            print(f"✅ {removed_count} nicht mehr existierende Dateien aus Cache entfernt")
        except Exception as e:
            print(f"❌ Fehler beim Bereinigen: {e}")
        
        return removed_count

def filter_new_files(file_paths: List[Path], cache: ProcessingCache) -> tuple[List[Path], List[FileRecord]]:
    """
    Filtert neue Dateien heraus, die noch nicht verarbeitet wurden
    
    Returns:
        (new_files, existing_records): Neue Dateien und bereits verarbeitete Records
    """
    new_files = []
    existing_records = []
    
    print(f"🔍 Prüfe {len(file_paths)} Dateien auf bereits verarbeitete...")
    
    for file_path in file_paths:
        is_processed, record = cache.is_file_processed(file_path)
        
        if is_processed and record:
            existing_records.append(record)
        else:
            new_files.append(file_path)
    
    print(f"📊 Ergebnis: {len(new_files)} neue, {len(existing_records)} bereits verarbeitet")
    
    return new_files, existing_records

def main():
    """Demo der intelligenten Duplikaterkennung"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Processing Cache Management")
    parser.add_argument("command", choices=['stats', 'clear', 'cleanup'], 
                       help="Aktion: stats, clear, cleanup")
    
    args = parser.parse_args()
    cache = ProcessingCache()
    
    if args.command == 'stats':
        print("📊 PROCESSING CACHE STATISTIKEN")
        print("=" * 40)
        
        stats = cache.get_stats()
        if stats:
            print(f"📁 Verarbeitete Dateien: {stats['total_files']:,}")
            print(f"🔗 Eindeutige Dateien: {stats['unique_files']:,}")
            print(f"📋 Duplikate: {stats['duplicate_files']:,}")
            print(f"📦 Batches: {stats['total_batches']:,}")
            print(f"💾 Gesamtgröße: {stats['total_size_mb']:.1f} MB")
            
            if stats['first_processed']:
                print(f"⏰ Erste Verarbeitung: {stats['first_processed']}")
            if stats['last_processed']:
                print(f"⏰ Letzte Verarbeitung: {stats['last_processed']}")
        else:
            print("❌ Keine Daten im Cache")
    
    elif args.command == 'clear':
        print("🗑️  Cache wird geleert...")
        cache.clear_cache()
    
    elif args.command == 'cleanup':
        print("🧹 Bereinige Cache von nicht existierenden Dateien...")
        removed = cache.remove_missing_files()

if __name__ == "__main__":
    main()
