"""
Archive-Verarbeitungsmodul für CLARA
Erweitert die Datenverarbeitung um umfassende Archive-Unterstützung
"""

import json
import zipfile
import tarfile
import gzip
import bz2
import lzma
import tempfile
import shutil
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Generator
import logging
from datetime import datetime
import hashlib

# Optionale Archive-Handler
try:
    import rarfile
    RAR_AVAILABLE = True
except ImportError:
    RAR_AVAILABLE = False

try:
    import py7zr
    SEVENZ_AVAILABLE = True
except ImportError:
    SEVENZ_AVAILABLE = False

class ArchiveProcessor:
    """Verarbeitung von Archive-Dateien für CLARA Training"""
    
    def __init__(self, temp_base_dir: Optional[str] = None, cleanup_on_exit: bool = True):
        self.logger = logging.getLogger(__name__)
        self.temp_base_dir = Path(temp_base_dir) if temp_base_dir else Path(tempfile.gettempdir()) / "clara_archives"
        self.cleanup_on_exit = cleanup_on_exit
        self.temp_dirs = []
        
        # Stelle sicher, dass Basis-Temp-Verzeichnis existiert
        self.temp_base_dir.mkdir(parents=True, exist_ok=True)
        
        # Unterstützte Archive mit ihren Handlern
        self.archive_handlers = {
            '.zip': self._extract_zip,
            '.tar': self._extract_tar,
            '.tar.gz': self._extract_tar,
            '.tar.bz2': self._extract_tar,
            '.tar.xz': self._extract_tar,
            '.tgz': self._extract_tar,
            '.tbz2': self._extract_tar,
            '.gz': self._extract_gzip,
            '.bz2': self._extract_bz2,
            '.xz': self._extract_xz,
        }
        
        # Füge optionale Handler hinzu
        if RAR_AVAILABLE:
            self.archive_handlers['.rar'] = self._extract_rar
        
        if SEVENZ_AVAILABLE:
            self.archive_handlers['.7z'] = self._extract_7z
        
        self.logger.info(f"Archive Processor initialisiert mit {len(self.archive_handlers)} unterstützten Formaten")
    
    def is_archive(self, file_path: Union[str, Path]) -> bool:
        """Prüft, ob eine Datei ein unterstütztes Archiv ist"""
        file_path = Path(file_path)
        
        # Prüfe auf bekannte Archive-Endungen
        for ext in self.archive_handlers.keys():
            if file_path.name.lower().endswith(ext.lower()):
                return True
        
        return False
    
    def get_archive_info(self, archive_path: Union[str, Path]) -> Dict[str, Any]:
        """Sammelt Informationen über ein Archiv"""
        archive_path = Path(archive_path)
        
        if not archive_path.exists():
            raise FileNotFoundError(f"Archiv nicht gefunden: {archive_path}")
        
        info = {
            'path': str(archive_path),
            'name': archive_path.name,
            'size_mb': archive_path.stat().st_size / (1024 * 1024),
            'type': self._get_archive_type(archive_path),
            'supported': self.is_archive(archive_path),
            'files_count': 0,
            'estimated_size_mb': 0
        }
        
        # Versuche Archiv-Inhalt zu analysieren
        try:
            if info['type'] == 'zip':
                with zipfile.ZipFile(archive_path, 'r') as zf:
                    info['files_count'] = len(zf.namelist())
                    info['estimated_size_mb'] = sum(zf.getinfo(name).file_size for name in zf.namelist()) / (1024 * 1024)
            elif info['type'].startswith('tar'):
                with tarfile.open(archive_path, 'r') as tf:
                    members = tf.getmembers()
                    info['files_count'] = len([m for m in members if m.isfile()])
                    info['estimated_size_mb'] = sum(m.size for m in members if m.isfile()) / (1024 * 1024)
        except Exception as e:
            self.logger.warning(f"Konnte Archiv-Info nicht ermitteln für {archive_path}: {e}")
        
        return info
    
    def extract_archive(self, archive_path: Union[str, Path], 
                       extract_to: Optional[Union[str, Path]] = None,
                       preserve_structure: bool = True,
                       file_filter: Optional[callable] = None) -> Path:
        """
        Extrahiert ein Archiv
        
        Args:
            archive_path: Pfad zum Archiv
            extract_to: Zielverzeichnis (None = temporäres Verzeichnis)
            preserve_structure: Ordnerstruktur beibehalten
            file_filter: Funktion zum Filtern von Dateien (filename -> bool)
            
        Returns:
            Pfad zum extrahierten Verzeichnis
        """
        archive_path = Path(archive_path)
        
        if not self.is_archive(archive_path):
            raise ValueError(f"Nicht unterstütztes Archiv-Format: {archive_path}")
        
        # Zielverzeichnis bestimmen - standardmäßig neben dem Archiv
        if extract_to is None:
            extract_to = archive_path.parent / f"{archive_path.stem}_extracted"
        else:
            extract_to = Path(extract_to)
        
        extract_to.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"Extrahiere {archive_path.name} nach {extract_to}")
        
        # Passenden Handler finden und ausführen
        archive_type = self._get_archive_type(archive_path)
        
        for ext, handler in self.archive_handlers.items():
            if archive_path.name.lower().endswith(ext.lower()):
                handler(archive_path, extract_to, preserve_structure, file_filter)
                break
        else:
            raise ValueError(f"Kein Handler für Archiv-Typ: {archive_type}")
        
        # Prüfe Extraktion
        if not any(extract_to.iterdir()):
            raise RuntimeError(f"Archiv-Extraktion fehlgeschlagen: {archive_path}")
        
        extracted_files = list(extract_to.rglob("*"))
        file_count = len([f for f in extracted_files if f.is_file()])
        
        self.logger.info(f"✅ {file_count} Dateien aus {archive_path.name} extrahiert")
        
        return extract_to
    
    def extract_and_process_archive(self, archive_path: Union[str, Path],
                                   document_processor,
                                   file_extensions: Optional[List[str]] = None,
                                   max_files: Optional[int] = None) -> List[str]:
        """
        Extrahiert Archiv und verarbeitet die Dokumente
        
        Args:
            archive_path: Pfad zum Archiv
            document_processor: DataProcessor Instanz
            file_extensions: Erlaubte Dateierweiterungen (None = alle)
            max_files: Maximale Anzahl zu verarbeitender Dateien
            
        Returns:
            Liste der verarbeiteten Texte
        """
        archive_path = Path(archive_path)
        
        # Archiv extrahieren
        extract_dir = self.extract_archive(archive_path)
        
        try:
            # Alle relevanten Dateien finden
            all_files = []
            for pattern in ['**/*'] if not file_extensions else [f'**/*{ext}' for ext in file_extensions]:
                all_files.extend(extract_dir.glob(pattern))
            
            # Nur Dateien, keine Verzeichnisse
            document_files = [f for f in all_files if f.is_file()]
            
            # Nach Erweiterungen filtern
            if file_extensions:
                document_files = [f for f in document_files if f.suffix.lower() in [ext.lower() for ext in file_extensions]]
            
            # Limitieren
            if max_files:
                document_files = document_files[:max_files]
            
            self.logger.info(f"Verarbeite {len(document_files)} Dateien aus Archiv")
            
            # Dateien verarbeiten
            texts = []
            for doc_file in document_files:
                try:
                    if hasattr(document_processor, 'load_and_process'):
                        # Neue DataProcessor-API
                        file_texts = document_processor.load_and_process(str(doc_file))
                        texts.extend(file_texts)
                    else:
                        # Fallback für ältere APIs
                        with open(doc_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                            if content.strip():
                                texts.append(content)
                
                except Exception as e:
                    self.logger.warning(f"Fehler beim Verarbeiten von {doc_file}: {e}")
                    continue
            
            self.logger.info(f"✅ {len(texts)} Texte aus Archiv verarbeitet")
            return texts
            
        finally:
            # Aufräumen nur bei temporären Verzeichnissen
            if (self.cleanup_on_exit and 
                extract_dir in [Path(td) for td in self.temp_dirs]):
                self._cleanup_temp_dir(extract_dir)
            else:
                self.logger.info(f"📂 Extrahierte Dateien bleiben in: {extract_dir}")
    
    def batch_process_archives(self, archive_dir: Union[str, Path],
                              document_processor,
                              output_dir: Union[str, Path],
                              batch_size: int = 1000,
                              file_extensions: Optional[List[str]] = None) -> List[str]:
        """
        Verarbeitet alle Archive in einem Verzeichnis
        
        Args:
            archive_dir: Verzeichnis mit Archiven
            document_processor: DataProcessor Instanz
            output_dir: Ausgabeverzeichnis für verarbeitete Daten
            batch_size: Anzahl Texte pro Batch-Datei
            file_extensions: Erlaubte Dateierweiterungen
            
        Returns:
            Liste der erstellten Batch-Dateien
        """
        archive_dir = Path(archive_dir)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Alle Archive finden
        archives = []
        for pattern in ['*.zip', '*.tar', '*.tar.gz', '*.rar', '*.7z', '*.gz', '*.bz2', '*.xz']:
            archives.extend(archive_dir.glob(pattern))
        
        if not archives:
            self.logger.warning(f"Keine Archive in {archive_dir} gefunden")
            return []
        
        self.logger.info(f"Gefunden: {len(archives)} Archive")
        
        # Archive verarbeiten
        all_texts = []
        for i, archive in enumerate(archives, 1):
            self.logger.info(f"📦 Verarbeite Archiv {i}/{len(archives)}: {archive.name}")
            
            try:
                texts = self.extract_and_process_archive(
                    archive, document_processor, file_extensions
                )
                all_texts.extend(texts)
                
                self.logger.info(f"✅ {len(texts)} Texte aus {archive.name}")
                
            except Exception as e:
                self.logger.error(f"❌ Fehler bei {archive.name}: {e}")
                continue
        
        # Texte in Batches aufteilen und speichern
        batch_files = []
        for batch_num, batch_start in enumerate(range(0, len(all_texts), batch_size), 1):
            batch_texts = all_texts[batch_start:batch_start + batch_size]
            
            batch_file = output_dir / f"archive_batch_{batch_num:03d}.jsonl"
            with open(batch_file, 'w', encoding='utf-8') as f:
                for text in batch_texts:
                    json_entry = {
                        "text": text,
                        "source": "archive_processing",
                        "timestamp": datetime.now().isoformat()
                    }
                    f.write(json.dumps(json_entry, ensure_ascii=False) + '\n')
            
            batch_files.append(str(batch_file))
            self.logger.info(f"📄 Batch {batch_num}: {len(batch_texts)} Texte → {batch_file.name}")
        
        self.logger.info(f"🎉 {len(archives)} Archive → {len(all_texts)} Texte → {len(batch_files)} Batches")
        return batch_files
    
    # Private Methoden für verschiedene Archive-Typen
    
    def _get_archive_type(self, archive_path: Path) -> str:
        """Bestimmt den Archiv-Typ basierend auf der Dateiendung"""
        name_lower = archive_path.name.lower()
        
        if name_lower.endswith('.tar.gz') or name_lower.endswith('.tgz'):
            return 'tar.gz'
        elif name_lower.endswith('.tar.bz2') or name_lower.endswith('.tbz2'):
            return 'tar.bz2'
        elif name_lower.endswith('.tar.xz'):
            return 'tar.xz'
        elif name_lower.endswith('.tar'):
            return 'tar'
        elif name_lower.endswith('.zip'):
            return 'zip'
        elif name_lower.endswith('.rar'):
            return 'rar'
        elif name_lower.endswith('.7z'):
            return '7z'
        elif name_lower.endswith('.gz'):
            return 'gz'
        elif name_lower.endswith('.bz2'):
            return 'bz2'
        elif name_lower.endswith('.xz'):
            return 'xz'
        else:
            return 'unknown'
    
    def _create_temp_dir(self, prefix: str = "clara_temp") -> Path:
        """Erstellt ein temporäres Verzeichnis"""
        temp_dir = self.temp_base_dir / f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.getpid()}"
        temp_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dirs.append(str(temp_dir))
        return temp_dir
    
    def _extract_zip(self, archive_path: Path, extract_to: Path, preserve_structure: bool, file_filter: Optional[callable]):
        """Extrahiert ZIP-Archive"""
        with zipfile.ZipFile(archive_path, 'r') as zf:
            for member in zf.namelist():
                if file_filter and not file_filter(member):
                    continue
                
                try:
                    if preserve_structure:
                        zf.extract(member, extract_to)
                    else:
                        # Flache Struktur - nur Dateinamen
                        member_path = Path(member)
                        if not member.endswith('/'):  # Keine Verzeichnisse
                            target_path = extract_to / member_path.name
                            with zf.open(member) as source, open(target_path, 'wb') as target:
                                shutil.copyfileobj(source, target)
                except Exception as e:
                    self.logger.warning(f"Fehler beim Extrahieren von {member}: {e}")
    
    def _extract_tar(self, archive_path: Path, extract_to: Path, preserve_structure: bool, file_filter: Optional[callable]):
        """Extrahiert TAR-Archive (alle Varianten)"""
        with tarfile.open(archive_path, 'r') as tf:
            for member in tf.getmembers():
                if not member.isfile():
                    continue
                
                if file_filter and not file_filter(member.name):
                    continue
                
                try:
                    if preserve_structure:
                        tf.extract(member, extract_to)
                    else:
                        # Flache Struktur
                        member_path = Path(member.name)
                        target_path = extract_to / member_path.name
                        with tf.extractfile(member) as source, open(target_path, 'wb') as target:
                            shutil.copyfileobj(source, target)
                except Exception as e:
                    self.logger.warning(f"Fehler beim Extrahieren von {member.name}: {e}")
    
    def _extract_rar(self, archive_path: Path, extract_to: Path, preserve_structure: bool, file_filter: Optional[callable]):
        """Extrahiert RAR-Archive"""
        if not RAR_AVAILABLE:
            raise RuntimeError("rarfile-Bibliothek nicht verfügbar")
        
        with rarfile.RarFile(archive_path, 'r') as rf:
            for member in rf.namelist():
                if file_filter and not file_filter(member):
                    continue
                
                try:
                    if preserve_structure:
                        rf.extract(member, extract_to)
                    else:
                        # Flache Struktur
                        member_path = Path(member)
                        if not member.endswith('/'):
                            target_path = extract_to / member_path.name
                            with rf.open(member) as source, open(target_path, 'wb') as target:
                                shutil.copyfileobj(source, target)
                except Exception as e:
                    self.logger.warning(f"Fehler beim Extrahieren von {member}: {e}")
    
    def _extract_7z(self, archive_path: Path, extract_to: Path, preserve_structure: bool, file_filter: Optional[callable]):
        """Extrahiert 7Z-Archive"""
        if not SEVENZ_AVAILABLE:
            raise RuntimeError("py7zr-Bibliothek nicht verfügbar")
        
        with py7zr.SevenZipFile(archive_path, 'r') as szf:
            if preserve_structure:
                szf.extractall(extract_to)
            else:
                # Für flache Struktur müssen wir jeden File einzeln extrahieren
                for info in szf.list():
                    if not info.is_dir and (not file_filter or file_filter(info.filename)):
                        try:
                            content = szf.read([info.filename])
                            if info.filename in content:
                                target_path = extract_to / Path(info.filename).name
                                with open(target_path, 'wb') as f:
                                    f.write(content[info.filename].getvalue())
                        except Exception as e:
                            self.logger.warning(f"Fehler beim Extrahieren von {info.filename}: {e}")
    
    def _extract_gzip(self, archive_path: Path, extract_to: Path, preserve_structure: bool, file_filter: Optional[callable]):
        """Extrahiert GZIP-Dateien"""
        output_name = archive_path.stem  # Entferne .gz
        target_path = extract_to / output_name
        
        with gzip.open(archive_path, 'rb') as gzf, open(target_path, 'wb') as outf:
            shutil.copyfileobj(gzf, outf)
    
    def _extract_bz2(self, archive_path: Path, extract_to: Path, preserve_structure: bool, file_filter: Optional[callable]):
        """Extrahiert BZ2-Dateien"""
        output_name = archive_path.stem  # Entferne .bz2
        target_path = extract_to / output_name
        
        with bz2.open(archive_path, 'rb') as bzf, open(target_path, 'wb') as outf:
            shutil.copyfileobj(bzf, outf)
    
    def _extract_xz(self, archive_path: Path, extract_to: Path, preserve_structure: bool, file_filter: Optional[callable]):
        """Extrahiert XZ-Dateien"""
        output_name = archive_path.stem  # Entferne .xz
        target_path = extract_to / output_name
        
        with lzma.open(archive_path, 'rb') as xzf, open(target_path, 'wb') as outf:
            shutil.copyfileobj(xzf, outf)
    
    def _cleanup_temp_dir(self, temp_dir: Path):
        """Räumt temporäres Verzeichnis auf"""
        try:
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
                self.logger.debug(f"Temporäres Verzeichnis aufgeräumt: {temp_dir}")
                if str(temp_dir) in self.temp_dirs:
                    self.temp_dirs.remove(str(temp_dir))
        except Exception as e:
            self.logger.warning(f"Konnte temporäres Verzeichnis nicht aufräumen {temp_dir}: {e}")
    
    def cleanup_all_temp_dirs(self):
        """Räumt alle temporären Verzeichnisse auf"""
        for temp_dir in self.temp_dirs[:]:  # Kopie der Liste
            self._cleanup_temp_dir(Path(temp_dir))
    
    def __del__(self):
        """Automatisches Aufräumen beim Zerstören der Instanz"""
        if self.cleanup_on_exit:
            self.cleanup_all_temp_dirs()


# Convenience-Funktionen

def process_archive_directory(archive_dir: str, output_dir: str, 
                            document_processor=None, batch_size: int = 1000) -> List[str]:
    """
    Vereinfachte Funktion zur Verarbeitung aller Archive in einem Verzeichnis
    
    Args:
        archive_dir: Verzeichnis mit Archiven
        output_dir: Ausgabeverzeichnis
        document_processor: Optional - DataProcessor Instanz
        batch_size: Texte pro Batch
        
    Returns:
        Liste der erstellten Batch-Dateien
    """
    if document_processor is None:
        # Importiere DataProcessor falls nicht übergeben
        from .data_processor import DataProcessor
        document_processor = DataProcessor()
    
    archive_proc = ArchiveProcessor()
    
    try:
        return archive_proc.batch_process_archives(
            archive_dir, document_processor, output_dir, batch_size
        )
    finally:
        archive_proc.cleanup_all_temp_dirs()


def extract_single_archive(archive_path: str, extract_to: str = None) -> str:
    """
    Vereinfachte Funktion zur Extraktion eines einzelnen Archivs
    
    Args:
        archive_path: Pfad zum Archiv
        extract_to: Zielverzeichnis (optional)
        
    Returns:
        Pfad zum extrahierten Verzeichnis
    """
    archive_proc = ArchiveProcessor()
    return str(archive_proc.extract_archive(archive_path, extract_to))


if __name__ == "__main__":
    # Test-Code
    import logging
    logging.basicConfig(level=logging.INFO)
    
    proc = ArchiveProcessor()
    
    # Teste verfügbare Archive-Formate
    print("🗜️  Unterstützte Archive-Formate:")
    for ext in proc.archive_handlers.keys():
        print(f"  ✅ {ext}")
    
    if not RAR_AVAILABLE:
        print("  ⚠️  .rar (rarfile-Bibliothek nicht installiert)")
    
    if not SEVENZ_AVAILABLE:
        print("  ⚠️  .7z (py7zr-Bibliothek nicht installiert)")
