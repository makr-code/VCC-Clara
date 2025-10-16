#!/usr/bin/env python3
"""
KORRIGIERTER Batch-Processor mit Datei-Verfolgung
GARANTIE: Ändert NIEMALS Original-Dateien!
KORRIGIERT: Verwendet korrekte PDF-Textextraktion statt binäre Datei-Lesung
"""

import argparse
import json
import time
import sys
import os
import hashlib
import sqlite3
import re
from pathlib import Path
from typing import List, Iterator, Set, Dict
from transformers import AutoTokenizer
import multiprocessing as mp
from functools import partial
from datetime import datetime

# Add parent directory to path to import src modules
script_dir = Path(__file__).parent
project_root = script_dir.parent
sys.path.insert(0, str(project_root))

# Import der sicheren Datenbank - VOLLSTÄNDIGE SQLITE IMPLEMENTIERUNG
class SafeProcessingDatabase:
    """
    Sichere SQLite-Datenbank zur Verfolgung verarbeiteter Dateien
    GARANTIE: Verhindert doppelte Verarbeitung und verfolgt Fortschritt
    """
    
    def __init__(self, db_path="data/processing_database.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """Initialisiert die SQLite-Datenbank mit erforderlichen Tabellen"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS processed_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT UNIQUE NOT NULL,
                    file_size INTEGER,
                    file_hash TEXT,
                    processed_at TEXT DEFAULT (datetime('now')),
                    text_count INTEGER DEFAULT 0,
                    quality_score REAL DEFAULT 0.0
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_file_path ON processed_files(file_path)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_processed_at ON processed_files(processed_at)
            """)
            conn.commit()
    
    def is_file_processed(self, file_path: Path) -> bool:
        """Prüft, ob eine Datei bereits verarbeitet wurde"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT 1 FROM processed_files WHERE file_path = ?",
                (str(file_path),)
            )
            return cursor.fetchone() is not None
    
    def mark_file_processed(self, file_path: Path, text_count: int = 0, quality_score: float = 0.0):
        """Markiert eine Datei als verarbeitet"""
        file_size = file_path.stat().st_size if file_path.exists() else 0
        file_hash = self._calculate_file_hash(file_path)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO processed_files 
                (file_path, file_size, file_hash, text_count, quality_score)
                VALUES (?, ?, ?, ?, ?)
            """, (str(file_path), file_size, file_hash, text_count, quality_score))
            conn.commit()
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Berechnet SHA256-Hash einer Datei für Integrität"""
        try:
            hash_sha256 = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception:
            return "unknown"
    
    def get_processing_stats(self) -> Dict:
        """Gibt Verarbeitungsstatistiken zurück"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total_files,
                    SUM(text_count) as total_texts,
                    AVG(quality_score) as avg_quality,
                    MIN(processed_at) as first_processed,
                    MAX(processed_at) as last_processed
                FROM processed_files
            """)
            row = cursor.fetchone()
            if row:
                return {
                    'total_files': row[0],
                    'total_texts': row[1] or 0,
                    'avg_quality': row[2] or 0.0,
                    'first_processed': row[3],
                    'last_processed': row[4]
                }
            return {}

# KORRIGIERT: Importiere VerwaltungsDataProcessor
try:
    from src.data.data_processor import VerwaltungsDataProcessor
    try:
        from src.utils.logging_utils import setup_logger
    except ImportError:
        import logging
        def setup_logger(name):
            logging.basicConfig(level=logging.INFO)
            return logging.getLogger(name)
    IMPORTS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Import-Warnung: {e}")
    IMPORTS_AVAILABLE = False
    # Fallback für Logger
    import logging
    def setup_logger(name):
        logging.basicConfig(level=logging.INFO)
        return logging.getLogger(name)

def smart_chunk_text(text: str, tokenizer=None, max_length: int = 1024, 
                    overlap_ratio: float = 0.15, min_chunk_size: int = 30) -> List[str]:
    """
    INTELLIGENTES CHUNKING mit Struktur-Erkennung für deutsche Verwaltungstexte
    
    Features:
    - Erkennt Paragrafen, Artikel, Überschriften
    - Sliding Window mit konfigurierbarer Überlappung
    - Qualitätsbewertung für jeden Chunk
    - Optimiert für LeoLM Tokenizer
    """
    
    def get_token_count(text_chunk):
        if tokenizer:
            return len(tokenizer.encode(text_chunk, add_special_tokens=False))
        else:
            # Fallback: Schätzung (ca. 4 Zeichen pro Token für Deutsch)
            return len(text_chunk) // 4
    
    # Preprocessing: Text säubern und normalisieren
    text = re.sub(r'\n+', '\n', text.strip())
    text = re.sub(r' +', ' ', text)
    
    if get_token_count(text) <= max_length:
        # Text passt bereits in einen Chunk
        return [text]
    
    chunks = []
    overlap_tokens = int(max_length * overlap_ratio)
    
    # Strukturbasiertes Chunking für Rechtsdokumente
    legal_patterns = [
        r'(?=§\s*\d+)',  # Paragrafen
        r'(?=Art\.\s*\d+)',  # Artikel
        r'(?=Artikel\s+\d+)',  # Artikel (ausgeschrieben)
        r'(?=\(\d+\))',  # Nummerierte Absätze
        r'(?=^\d+\.)',  # Nummerierte Listen
        r'(?=^[A-Z][^.!?]*:)',  # Überschriften mit Doppelpunkt
    ]
    
    # Versuche strukturbasierte Aufteilung
    for pattern in legal_patterns:
        parts = re.split(pattern, text, flags=re.MULTILINE)
        if len(parts) > 1:
            # Strukturierte Aufteilung gefunden
            current_chunk = ""
            
            for part in parts:
                if not part.strip():
                    continue
                    
                test_chunk = current_chunk + ("\n" if current_chunk else "") + part
                
                if get_token_count(test_chunk) <= max_length:
                    current_chunk = test_chunk
                else:
                    # Chunk ist voll - speichern und neuen beginnen
                    if current_chunk and get_token_count(current_chunk) >= min_chunk_size:
                        chunks.append(current_chunk)
                    
                    # Überlappung hinzufügen (letzten Teil des vorherigen Chunks)
                    if chunks and overlap_tokens > 0:
                        prev_tokens = tokenizer.encode(chunks[-1], add_special_tokens=False) if tokenizer else chunks[-1].split()
                        if len(prev_tokens) > overlap_tokens:
                            overlap_text = tokenizer.decode(prev_tokens[-overlap_tokens:]) if tokenizer else ' '.join(prev_tokens[-overlap_tokens:])
                            current_chunk = overlap_text + "\n" + part
                        else:
                            current_chunk = part
                    else:
                        current_chunk = part
            
            # Letzten Chunk hinzufügen
            if current_chunk and get_token_count(current_chunk) >= min_chunk_size:
                chunks.append(current_chunk)
            
            if chunks:
                return chunks
    
    # Fallback: Absatzbasierte Aufteilung
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    
    if len(paragraphs) > 1:
        current_chunk = ""
        
        for para in paragraphs:
            test_chunk = current_chunk + ("\n\n" if current_chunk else "") + para
            
            if get_token_count(test_chunk) <= max_length:
                current_chunk = test_chunk
            else:
                if current_chunk and get_token_count(current_chunk) >= min_chunk_size:
                    chunks.append(current_chunk)
                
                # Prüfe, ob einzelner Paragraph zu lang ist
                if get_token_count(para) > max_length:
                    # Satzbasierte Aufteilung des Paragraphs
                    sentences = re.split(r'(?<=[.!?])\s+(?=[A-ZÄÖÜ])', para)
                    chunk_text = ""
                    
                    for sent in sentences:
                        test_sent = chunk_text + (" " if chunk_text else "") + sent
                        if get_token_count(test_sent) <= max_length:
                            chunk_text = test_sent
                        else:
                            if chunk_text and get_token_count(chunk_text) >= min_chunk_size:
                                chunks.append(chunk_text)
                            chunk_text = sent
                    
                    if chunk_text and get_token_count(chunk_text) >= min_chunk_size:
                        current_chunk = chunk_text
                    else:
                        current_chunk = ""
                else:
                    current_chunk = para
        
        if current_chunk and get_token_count(current_chunk) >= min_chunk_size:
            chunks.append(current_chunk)
    
    # Letzte Option: Sliding Window mit fester Größe
    if not chunks:
        words = text.split()
        if not words:
            return []
        
        words_per_chunk = max_length // 4  # Grobe Schätzung für Deutsche Sprache
        
        for i in range(0, len(words), words_per_chunk - overlap_tokens // 4):
            chunk_words = words[i:i + words_per_chunk]
            chunk_text = ' '.join(chunk_words)
            
            if len(chunk_words) >= min_chunk_size // 4:  # Mindestgröße in Wörtern
                chunks.append(chunk_text)
    
    return chunks if chunks else [text]  # Fallback: Original-Text

def calculate_chunk_quality(text: str) -> float:
    """
    Bewertet die Qualität eines Text-Chunks für Training
    Returns: Score zwischen 0.0 (schlecht) und 1.0 (sehr gut)
    """
    if not text or not text.strip():
        return 0.0
    
    score = 0.5  # Basis-Score
    text_len = len(text.strip())
    
    # Längen-Bonus
    if 200 <= text_len <= 2000:
        score += 0.2
    elif 100 <= text_len <= 3000:
        score += 0.1
    
    # Verwaltungssprache-Bonus
    verwaltungs_keywords = [
        'verwaltung', 'behörde', 'antrag', 'bescheid', 'verordnung', 'gesetz',
        'paragraph', 'artikel', 'recht', 'rechtlich', 'zuständig', 'verfahren',
        'genehmigung', 'bewilligung', 'ordnung', 'bestimmung'
    ]
    
    text_lower = text.lower()
    keyword_count = sum(1 for kw in verwaltungs_keywords if kw in text_lower)
    score += min(0.3, keyword_count * 0.05)
    
    # Struktur-Bonus
    if re.search(r'§\s*\d+|Art\.\s*\d+|Artikel\s+\d+', text):
        score += 0.1
    if re.search(r'^\d+\.|\(\d+\)', text, re.MULTILINE):
        score += 0.05
    
    # Qualitäts-Abzüge
    if text_len < 30:
        score -= 0.2
    if text.count(' ') < 5:  # Weniger als 5 Wörter
        score -= 0.3
    
    return max(0.0, min(1.0, score))

def process_file_batch_corrected(file_batch, tokenizer_name="LeoLM/leo-hessianai-7b", max_length=1024):
    """
    KORRIGIERTE Verarbeitung eines Batches von Dateien mit korrekter Text-Extraktion.
    SICHERHEIT: Liest nur Dateien, ändert niemals Originale!
    KORRIGIERT: Verwendet VerwaltungsDataProcessor für PDF-Extraktion!
    """
    processing_stats = {
        'files_processed': 0,
        'chunks_created': 0,
        'total_tokens': 0,
        'avg_chunk_quality': 0.0,
        'processing_time': 0.0
    }
    
    start_time = time.time()
    
    # Tokenizer laden
    try:
        from transformers import AutoTokenizer
        tokenizer = AutoTokenizer.from_pretrained(tokenizer_name)
        print(f"✅ Tokenizer geladen: {tokenizer_name}")
    except Exception as e:
        print(f"⚠️ Tokenizer-Fallback: {e}")
        tokenizer = None
    
    # KORRIGIERT: VerwaltungsDataProcessor für Textextraktion
    data_processor = None
    if IMPORTS_AVAILABLE:
        try:
            # Erstelle einen Dummy-Tokenizer falls nicht verfügbar
            if not tokenizer:
                print("⚠️ Fallback: Erstelle Dummy-Tokenizer für DataProcessor")
                from transformers import AutoTokenizer
                dummy_tokenizer = AutoTokenizer.from_pretrained("LeoLM/leo-hessianai-7b")
                data_processor = VerwaltungsDataProcessor(dummy_tokenizer, max_length)
            else:
                data_processor = VerwaltungsDataProcessor(tokenizer, max_length)
            print("✅ VerwaltungsDataProcessor geladen")
        except Exception as e:
            print(f"⚠️ DataProcessor-Fallback: {e}")
            # Fallback: Einfache PDF-Extraktion mit PyPDF2/pdfplumber
            print("🔄 Versuche direkte PDF-Extraktion...")
            try:
                import PyPDF2
                import pdfplumber
                print("✅ PDF-Libraries verfügbar für Fallback")
            except ImportError as pdf_error:
                print(f"❌ PDF-Extraktion nicht verfügbar: {pdf_error}")
    
    def extract_pdf_fallback(pdf_path):
        """Fallback PDF-Extraktion wenn VerwaltungsDataProcessor nicht verfügbar"""
        try:
            import pdfplumber
            texts = []
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    text = page.extract_text()
                    if text and text.strip():
                        # Einfache Textbereinigung
                        clean_text = re.sub(r'\n+', '\n', text)
                        clean_text = re.sub(r' +', ' ', clean_text)
                        if len(clean_text.strip()) > 50:  # Nur substanzielle Seiten
                            texts.append(f"[Seite {page_num + 1}]\n{clean_text}")
            return texts
        except Exception as e:
            print(f"❌ PDF-Fallback fehlgeschlagen: {e}")
            return []
    
    def extract_html_fallback(html_path):
        """HTML/XHTML Textextraktion mit BeautifulSoup"""
        try:
            from bs4 import BeautifulSoup
            
            with open(html_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # HTML parsen
            soup = BeautifulSoup(content, 'html.parser')
            
            # Skripts und Styles entfernen
            for script in soup(["script", "style", "nav", "header", "footer"]):
                script.decompose()
            
            # Text extrahieren mit Struktur-Erhaltung
            texts = []
            
            # Titel extrahieren
            title = soup.find('title')
            if title and title.get_text().strip():
                texts.append(f"[Titel]\n{title.get_text().strip()}")
            
            # Hauptinhalt extrahieren (verschiedene Strategien)
            main_content = (
                soup.find('main') or 
                soup.find('article') or 
                soup.find('div', class_=re.compile(r'content|main|body', re.I)) or
                soup.find('body') or
                soup
            )
            
            if main_content:
                # Absätze und Überschriften strukturiert extrahieren
                for i, element in enumerate(main_content.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'div', 'section', 'article'])):
                    text = element.get_text().strip()
                    if len(text) > 30:  # Nur substanzielle Inhalte
                        # Tag-Info für bessere Strukturierung
                        if element.name.startswith('h'):
                            texts.append(f"[{element.name.upper()}]\n{text}")
                        else:
                            texts.append(text)
            
            # Fallback: Gesamter Text
            if not texts:
                text = soup.get_text()
                clean_text = re.sub(r'\n+', '\n', text)
                clean_text = re.sub(r' +', ' ', clean_text)
                if len(clean_text.strip()) > 50:
                    texts.append(clean_text.strip())
            
            return texts
            
        except Exception as e:
            print(f"❌ HTML-Extraktion fehlgeschlagen: {e}")
            return []
    
    def extract_xml_fallback(xml_path):
        """XML Textextraktion mit BeautifulSoup und lxml"""
        try:
            from bs4 import BeautifulSoup
            
            with open(xml_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # XML parsen (verschiedene Parser versuchen)
            parsers = ['xml', 'lxml', 'html.parser']
            soup = None
            
            for parser in parsers:
                try:
                    soup = BeautifulSoup(content, parser)
                    break
                except Exception:
                    continue
            
            if not soup:
                raise Exception("Kein XML-Parser verfügbar")
            
            texts = []
            
            # Strukturierte Extraktion basierend auf häufigen XML-Patterns
            text_elements = soup.find_all(text=True)
            current_text = []
            
            for text in text_elements:
                cleaned = text.strip()
                if cleaned and not cleaned.startswith('<?') and not cleaned.startswith('<!'):
                    # Sammle zusammenhängende Textblöcke
                    if len(cleaned) > 10:  # Mindestlänge für relevanten Text
                        current_text.append(cleaned)
                    
                    # Strukturpausen erkennen (neue Elemente)
                    if len(' '.join(current_text)) > 200:
                        combined_text = ' '.join(current_text).strip()
                        if len(combined_text) > 50:
                            texts.append(combined_text)
                        current_text = []
            
            # Letzten Block hinzufügen
            if current_text:
                combined_text = ' '.join(current_text).strip()
                if len(combined_text) > 50:
                    texts.append(combined_text)
            
            # Fallback: Alle Textelemente
            if not texts:
                all_text = soup.get_text()
                clean_text = re.sub(r'\n+', '\n', all_text)
                clean_text = re.sub(r' +', ' ', clean_text)
                if len(clean_text.strip()) > 50:
                    texts.append(clean_text.strip())
            
            return texts
            
        except Exception as e:
            print(f"❌ XML-Extraktion fehlgeschlagen: {e}")
            return []
    
    batch_texts = []
    quality_scores = []
    
    for file_path in file_batch:
        try:
            extracted_texts = []
            
            # ERWEITERT: Dateiformatspezifische Textextraktion
            file_ext = file_path.suffix.lower()
            
            if file_ext == '.pdf':
                if data_processor:
                    # Korrekte PDF-Textextraktion verwenden
                    extracted_texts = data_processor._load_pdf(file_path)
                else:
                    # Fallback PDF-Extraktion verwenden
                    print(f"🔄 Fallback PDF-Extraktion für: {file_path.name}")
                    extracted_texts = extract_pdf_fallback(file_path)
                    
            elif file_ext in ['.html', '.htm', '.xhtml']:
                # HTML/XHTML Extraktion
                print(f"🌐 HTML-Extraktion für: {file_path.name}")
                extracted_texts = extract_html_fallback(file_path)
                
            elif file_ext in ['.xml', '.xsd', '.rss', '.atom']:
                # XML Extraktion
                print(f"📄 XML-Extraktion für: {file_path.name}")
                extracted_texts = extract_xml_fallback(file_path)
                
            else:
                # Textdateien direkt lesen
                try:
                    content = file_path.read_text(encoding='utf-8', errors='ignore')
                    if content.strip():
                        extracted_texts = [content]
                except Exception as e:
                    print(f"❌ Textextraktion fehlgeschlagen für {file_path}: {e}")
                    continue
            
            # Verarbeitung der extrahierten Texte
            if extracted_texts:
                all_chunks = []
                for text in extracted_texts:
                    if text.strip():
                        # INTELLIGENTES CHUNKING verwenden
                        chunks = smart_chunk_text(
                            text, 
                            tokenizer=tokenizer, 
                            max_length=max_length,
                            overlap_ratio=0.15,  # 15% Überlappung für besseren Kontext
                            min_chunk_size=30    # Mindestgröße für bessere Qualität
                        )
                        all_chunks.extend(chunks)
                
                # Metadaten sammeln für bessere Statistiken
                file_chunks = len(all_chunks)
                processing_stats['files_processed'] += 1
                processing_stats['chunks_created'] += file_chunks
                
                # Chunk-Qualität bewerten
                for chunk in all_chunks:
                    quality = calculate_chunk_quality(chunk)
                    quality_scores.append(quality)
                    if tokenizer:
                        processing_stats['total_tokens'] += len(tokenizer.encode(chunk, add_special_tokens=False))
                
                batch_texts.extend(all_chunks)
                
                # Detaillierte Datei-Info
                total_text_len = sum(len(text) for text in extracted_texts)
                print(f"  📄 {file_path.name}: {total_text_len/1024:.1f}KB → {file_chunks} chunks")
                        
        except Exception as e:
            # Verbesserte Fehlerbehandlung
            print(f"❌ Fehler bei {file_path}: {type(e).__name__}: {e}")
            continue
    
    # Finale Statistiken
    processing_stats['processing_time'] = time.time() - start_time
    if quality_scores:
        processing_stats['avg_chunk_quality'] = sum(quality_scores) / len(quality_scores)
    
    # Performance-Info ausgeben
    if processing_stats['files_processed'] > 0:
        avg_chunks_per_file = processing_stats['chunks_created'] / processing_stats['files_processed']
        print(f"  📊 Performance: {avg_chunks_per_file:.1f} chunks/file, "
              f"Ø-Qualität: {processing_stats['avg_chunk_quality']:.2f}, "
              f"Zeit: {processing_stats['processing_time']:.2f}s")
    
    return batch_texts

def discover_files_atomically(base_path, extensions=['*.txt', '*.md', '*.markdown', '*.pdf', '*.docx', '*.html', '*.htm', '*.xhtml', '*.xml', '*.xsd', '*.rss', '*.atom', '*.zip', '*.tar', '*.tar.gz', '*.tgz', '*.tar.bz2', '*.tar.xz', '*.7z', '*.rar']):
    """
    Generator der Dateien rekursiv und sicher entdeckt
    Unterstützt sowohl flache als auch tief verschachtelte Verzeichnisstrukturen
    """
    logger = setup_logger(__name__)
    logger.info(f"📁 Durchsuche rekursiv Verzeichnis: {base_path}")
    
    try:
        if not base_path.exists():
            logger.error(f"❌ Verzeichnis nicht gefunden: {base_path}")
            return
        
        total_files_found = 0
        directories_scanned = 0
        
        def scan_directory_recursive(current_path, depth=0):
            """Rekursive Funktion zum Durchsuchen aller Verzeichnisebenen"""
            nonlocal total_files_found, directories_scanned
            
            try:
                directories_scanned += 1
                indent = "  " * depth
                logger.info(f"{indent}🔍 Durchsuche Ebene {depth}: {current_path.name}")
                
                # Schritt 1: Dateien im aktuellen Verzeichnis finden
                local_files = 0
                for ext in extensions:
                    try:
                        files = list(current_path.glob(ext))
                        if files:
                            logger.info(f"{indent}  📄 {ext}: {len(files)} Dateien")
                            local_files += len(files)
                            total_files_found += len(files)
                            
                            # PERFORMANCE-OPTIMIERUNG: Progress-Monitoring für große Verzeichnisse
                            if len(files) > 100:
                                logger.info(f"{indent}  ⚠️ Großes Verzeichnis erkannt ({len(files)} Dateien)")
                                for i, file_path in enumerate(files):
                                    if file_path.is_file():
                                        yield file_path
                                    # Progress-Update alle 50 Dateien
                                    if (i + 1) % 50 == 0:
                                        logger.info(f"{indent}    📊 Fortschritt: {i+1}/{len(files)} Dateien")
                            else:
                                for file_path in files:
                                    if file_path.is_file():
                                        yield file_path
                                    
                    except Exception as e:
                        logger.warning(f"{indent}⚠️ Fehler bei {ext}: {e}")
                        continue
                
                if local_files == 0:
                    logger.debug(f"{indent}  📭 Keine Dateien in {current_path.name}")
                
                # Schritt 2: Unterverzeichnisse rekursiv durchsuchen
                try:
                    subdirs = [d for d in current_path.iterdir() if d.is_dir()]
                    if subdirs:
                        logger.info(f"{indent}📂 {len(subdirs)} Unterverzeichnisse gefunden")
                        
                        for subdir in subdirs:
                            try:
                                # Rekursiver Aufruf für jedes Unterverzeichnis
                                yield from scan_directory_recursive(subdir, depth + 1)
                            except Exception as e:
                                logger.warning(f"{indent}⚠️ Fehler in Unterverzeichnis {subdir.name}: {e}")
                                continue
                    else:
                        logger.debug(f"{indent}📁 Keine Unterverzeichnisse in {current_path.name}")
                        
                except Exception as e:
                    logger.warning(f"{indent}⚠️ Fehler beim Lesen der Unterverzeichnisse: {e}")
                    
            except Exception as e:
                logger.error(f"{indent}❌ Kritischer Fehler in {current_path}: {e}")
        
        # Rekursive Suche starten
        yield from scan_directory_recursive(base_path)
        
        # Finale Statistiken
        logger.info(f"✅ Suche abgeschlossen: {total_files_found} Dateien in {directories_scanned} Verzeichnissen gefunden")
        
    except Exception as e:
        logger.error(f"❌ Kritischer Fehler beim rekursiven Durchsuchen: {e}")

def atomic_batch_process(input_dir, output_dir, model_name="LeoLM/leo-hessianai-7b", 
                        max_length=1024, max_files=None, max_file_size_mb=50,
                        file_extensions="txt,md,markdown,pdf,docx,html,htm,xhtml,xml,xsd,rss,atom",
                        overlap_ratio=0.15, min_chunk_size=30, quality_threshold=0.3):
    """
    STREAM-PROCESSING: Sofortige Verarbeitung beim Finden der ersten Datei
    """
    logger = setup_logger(__name__)
    
    # Pfade validieren
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    
    if not input_path.exists():
        logger.error(f"❌ Input-Verzeichnis nicht gefunden: {input_path}")
        return 0, 0
    
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Datenbank und Verarbeitung initialisieren
    db = SafeProcessingDatabase()
    
    # Dateierweiterungen parsen
    extensions = [f"*.{ext.strip()}" for ext in file_extensions.split(',')]
    logger.info(f"🔍 Stream-Processing für Formate: {extensions}")
    
    # STREAM-PROCESSING: Tokenizer und Processor vorab laden
    logger.info("🚀 Initialisiere Verarbeitung...")
    try:
        from transformers import AutoTokenizer
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        logger.info(f"✅ Tokenizer geladen: {model_name}")
    except Exception as e:
        logger.warning(f"⚠️ Tokenizer-Fallback: {e}")
        tokenizer = None
    
    # VerwaltungsDataProcessor laden
    data_processor = None
    if IMPORTS_AVAILABLE:
        try:
            if not tokenizer:
                dummy_tokenizer = AutoTokenizer.from_pretrained("LeoLM/leo-hessianai-7b")
                data_processor = VerwaltungsDataProcessor(dummy_tokenizer, max_length)
            else:
                data_processor = VerwaltungsDataProcessor(tokenizer, max_length)
            logger.info("✅ VerwaltungsDataProcessor geladen")
        except Exception as e:
            logger.warning(f"⚠️ DataProcessor-Fallback: {e}")
    
    # Fallback-Funktionen definieren
    def extract_pdf_fallback(pdf_path):
        try:
            import pdfplumber
            texts = []
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    text = page.extract_text()
                    if text and text.strip():
                        clean_text = re.sub(r'\n+', '\n', text)
                        clean_text = re.sub(r' +', ' ', clean_text)
                        if len(clean_text.strip()) > 50:
                            texts.append(f"[Seite {page_num + 1}]\n{clean_text}")
            return texts
        except Exception as e:
            logger.error(f"❌ PDF-Fallback fehlgeschlagen: {e}")
            return []
    
    def extract_html_fallback(html_path):
        try:
            from bs4 import BeautifulSoup
            with open(html_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            soup = BeautifulSoup(content, 'html.parser')
            for script in soup(["script", "style", "nav", "header", "footer"]):
                script.decompose()
            texts = []
            title = soup.find('title')
            if title and title.get_text().strip():
                texts.append(f"[Titel]\n{title.get_text().strip()}")
            main_content = (soup.find('main') or soup.find('article') or 
                          soup.find('div', class_=re.compile(r'content|main|body', re.I)) or
                          soup.find('body') or soup)
            if main_content:
                for element in main_content.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'div', 'section', 'article']):
                    text = element.get_text().strip()
                    if len(text) > 30:
                        if element.name.startswith('h'):
                            texts.append(f"[{element.name.upper()}]\n{text}")
                        else:
                            texts.append(text)
            if not texts:
                text = soup.get_text()
                clean_text = re.sub(r'\n+', '\n', text)
                clean_text = re.sub(r' +', ' ', clean_text)
                if len(clean_text.strip()) > 50:
                    texts.append(clean_text.strip())
            return texts
        except Exception as e:
            logger.error(f"❌ HTML-Extraktion fehlgeschlagen: {e}")
            return []
    
    def extract_xml_fallback(xml_path):
        try:
            from bs4 import BeautifulSoup
            with open(xml_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            parsers = ['xml', 'lxml', 'html.parser']
            soup = None
            for parser in parsers:
                try:
                    soup = BeautifulSoup(content, parser)
                    break
                except Exception:
                    continue
            if not soup:
                raise Exception("Kein XML-Parser verfügbar")
            texts = []
            text_elements = soup.find_all(string=True)
            current_text = []
            for text in text_elements:
                cleaned = text.strip()
                if cleaned and not cleaned.startswith('<?') and not cleaned.startswith('<!'):
                    if len(cleaned) > 10:
                        current_text.append(cleaned)
                    if len(' '.join(current_text)) > 200:
                        combined_text = ' '.join(current_text).strip()
                        if len(combined_text) > 50:
                            texts.append(combined_text)
                        current_text = []
            if current_text:
                combined_text = ' '.join(current_text).strip()
                if len(combined_text) > 50:
                    texts.append(combined_text)
            if not texts:
                all_text = soup.get_text()
                clean_text = re.sub(r'\n+', '\n', all_text)
                clean_text = re.sub(r' +', ' ', clean_text)
                if len(clean_text.strip()) > 50:
                    texts.append(clean_text.strip())
            return texts
        except Exception as e:
            logger.error(f"❌ XML-Extraktion fehlgeschlagen: {e}")
            return []
    
    def extract_archive_fallback(archive_path):
        """Archiv-Extraktion (ZIP, RAR, 7Z, TAR) mit rekursiver Verarbeitung"""
        try:
            import zipfile
            import tempfile
            import shutil
            
            # Unterstützte Archive-Formate
            archive_ext = archive_path.suffix.lower()
            extracted_texts = []
            
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Archive extrahieren basierend auf Format
                if archive_ext == '.zip':
                    try:
                        with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                            zip_ref.extractall(temp_path)
                            logger.info(f"📦 ZIP extrahiert: {len(zip_ref.namelist())} Dateien")
                    except Exception as e:
                        logger.error(f"❌ ZIP-Extraktion fehlgeschlagen: {e}")
                        return []
                
                elif archive_ext in ['.tar', '.tar.gz', '.tgz', '.tar.bz2', '.tar.xz']:
                    try:
                        import tarfile
                        with tarfile.open(archive_path, 'r:*') as tar_ref:
                            tar_ref.extractall(temp_path)
                            logger.info(f"📦 TAR extrahiert: {len(tar_ref.getnames())} Dateien")
                    except Exception as e:
                        logger.error(f"❌ TAR-Extraktion fehlgeschlagen: {e}")
                        return []
                
                elif archive_ext == '.7z':
                    try:
                        import py7zr
                        with py7zr.SevenZipFile(archive_path, mode='r') as z:
                            z.extractall(temp_path)
                            logger.info(f"📦 7Z extrahiert")
                    except ImportError:
                        logger.warning(f"⚠️ py7zr nicht verfügbar für .7z Dateien")
                        return []
                    except Exception as e:
                        logger.error(f"❌ 7Z-Extraktion fehlgeschlagen: {e}")
                        return []
                
                elif archive_ext == '.rar':
                    try:
                        import rarfile
                        with rarfile.RarFile(archive_path) as rar_ref:
                            rar_ref.extractall(temp_path)
                            logger.info(f"📦 RAR extrahiert: {len(rar_ref.namelist())} Dateien")
                    except ImportError:
                        logger.warning(f"⚠️ rarfile nicht verfügbar für .rar Dateien")
                        return []
                    except Exception as e:
                        logger.error(f"❌ RAR-Extraktion fehlgeschlagen: {e}")
                        return []
                
                else:
                    logger.warning(f"⚠️ Nicht unterstütztes Archivformat: {archive_ext}")
                    return []
                
                # Rekursiv alle extrahierten Dateien verarbeiten
                supported_extensions = ['.txt', '.md', '.markdown', '.pdf', '.html', '.htm', '.xhtml', '.xml', '.docx']
                
                for extracted_file in temp_path.rglob('*'):
                    if extracted_file.is_file() and extracted_file.suffix.lower() in supported_extensions:
                        try:
                            logger.debug(f"📄 Verarbeite aus Archiv: {extracted_file.name}")
                            
                            # Dateigröße prüfen (max 50MB pro Datei)
                            if extracted_file.stat().st_size > 50 * 1024 * 1024:
                                logger.warning(f"⚠️ Datei in Archiv zu groß: {extracted_file.name}")
                                continue
                            
                            # Je nach Dateityp verarbeiten
                            file_ext = extracted_file.suffix.lower()
                            file_texts = []
                            
                            if file_ext == '.pdf':
                                if data_processor:
                                    file_texts = data_processor._load_pdf(extracted_file)
                                else:
                                    file_texts = extract_pdf_fallback(extracted_file)
                            elif file_ext in ['.html', '.htm', '.xhtml']:
                                file_texts = extract_html_fallback(extracted_file)
                            elif file_ext == '.xml':
                                file_texts = extract_xml_fallback(extracted_file)
                            else:
                                # Text/Markdown Dateien
                                content = extracted_file.read_text(encoding='utf-8', errors='ignore')
                                if content.strip():
                                    file_texts = [content]
                            
                            # Archiv-Metadaten hinzufügen
                            for text in file_texts:
                                if text.strip():
                                    prefixed_text = f"[Archiv: {archive_path.name} → {extracted_file.name}]\n{text}"
                                    extracted_texts.append(prefixed_text)
                        
                        except Exception as e:
                            logger.warning(f"⚠️ Fehler bei Archiv-Datei {extracted_file.name}: {e}")
                            continue
                
                logger.info(f"📦 Aus Archiv extrahiert: {len(extracted_texts)} Texte")
                return extracted_texts
                
        except Exception as e:
            logger.error(f"❌ Archiv-Extraktion fehlgeschlagen: {e}")
            return []
    
    # Stream-Processing Statistiken
    start_time = time.time()
    processed_count = 0
    skipped_count = 0
    all_texts = []
    max_size_bytes = max_file_size_mb * 1024 * 1024
    
    # Output-Datei vorbereiten
    timestamp = int(time.time())
    output_file = output_path / f"batch_processed_{timestamp}.jsonl"
    
    logger.info(f"📁 Beginne Stream-Processing von: {input_path}")
    logger.info(f"📝 Output-Stream: {output_file}")
    
    # STREAM-PROCESSING: Sofortige Verarbeitung beim Finden
    with open(output_file, 'w', encoding='utf-8') as f:
        file_count = 0
        
        for file_path in discover_files_atomically(input_path, extensions):
            file_count += 1
            
            # Max-Files Grenze prüfen
            if max_files and processed_count >= max_files:
                logger.info(f"🛑 Max-Files Grenze erreicht: {max_files}")
                break
            
            try:
                # Dateigrößencheck
                if file_path.stat().st_size > max_size_bytes:
                    logger.warning(f"⚠️ Datei zu groß übersprungen: {file_path.name}")
                    continue
                
                # Bereits verarbeitet?
                if db.is_file_processed(file_path):
                    skipped_count += 1
                    logger.debug(f"⏭️ Bereits verarbeitet: {file_path.name}")
                    continue
                
                # SOFORTIGE VERARBEITUNG
                logger.info(f"⚡ Verarbeite sofort: {file_path.name}")
                
                # ERWEITERTE Textextraktion mit Archiv-Unterstützung
                extracted_texts = []
                file_ext = file_path.suffix.lower()
                
                if file_ext == '.pdf':
                    if data_processor:
                        extracted_texts = data_processor._load_pdf(file_path)
                    else:
                        logger.info(f"🔄 Fallback PDF-Extraktion für: {file_path.name}")
                        extracted_texts = extract_pdf_fallback(file_path)
                        
                elif file_ext in ['.html', '.htm', '.xhtml']:
                    logger.info(f"🌐 HTML-Extraktion für: {file_path.name}")
                    extracted_texts = extract_html_fallback(file_path)
                    
                elif file_ext in ['.xml', '.xsd', '.rss', '.atom']:
                    logger.info(f"📄 XML-Extraktion für: {file_path.name}")
                    extracted_texts = extract_xml_fallback(file_path)
                    
                elif file_ext in ['.zip', '.tar', '.tar.gz', '.tgz', '.tar.bz2', '.tar.xz', '.7z', '.rar']:
                    # ARCHIV-VERARBEITUNG
                    logger.info(f"📦 Archiv-Extraktion für: {file_path.name}")
                    extracted_texts = extract_archive_fallback(file_path)
                else:
                    # Textdateien
                    content = file_path.read_text(encoding='utf-8', errors='ignore')
                    if content.strip():
                        extracted_texts = [content]
                
                # Chunking und Qualitätsfilterung
                if extracted_texts:
                    file_chunks = 0
                    for text in extracted_texts:
                        if text.strip():
                            chunks = smart_chunk_text(
                                text, tokenizer=tokenizer, max_length=max_length,
                                overlap_ratio=overlap_ratio, min_chunk_size=min_chunk_size
                            )
                            
                            # Sofort in Datei schreiben (Stream)
                            for chunk in chunks:
                                quality = calculate_chunk_quality(chunk)
                                if quality >= quality_threshold:
                                    entry = {
                                        "text": chunk,
                                        "source": str(file_path.parent.name),
                                        "file": file_path.name,
                                        "quality": round(quality, 3),
                                        "processed_at": time.time()
                                    }
                                    f.write(json.dumps(entry, ensure_ascii=False) + '\n')
                                    f.flush()  # Sofort schreiben
                                    file_chunks += 1
                    
                    if file_chunks > 0:
                        processed_count += 1
                        db.mark_file_processed(file_path, text_count=file_chunks, quality_score=0.8)
                        logger.info(f"✅ {file_path.name}: {file_chunks} chunks → Stream")
                    
                    # Progress-Update alle 10 Dateien
                    if processed_count % 10 == 0:
                        elapsed = time.time() - start_time
                        logger.info(f"📊 Stream-Progress: {processed_count} Dateien, {elapsed:.1f}s")
                
            except Exception as e:
                logger.error(f"❌ Stream-Fehler bei {file_path}: {e}")
                continue
    
    elapsed_time = time.time() - start_time
    
    # Finale Statistiken
    logger.info("🎉 Stream-Processing abgeschlossen!")
    logger.info(f"✅ Verarbeitet: {processed_count:,} Dateien")
    logger.info(f"⏭️ Übersprungen: {skipped_count:,} Dateien")
    logger.info(f"⏱️ Gesamtzeit: {elapsed_time:.2f} Sekunden")
    if processed_count > 0:
        logger.info(f"⚡ Dateien pro Sekunde: {processed_count / elapsed_time:.2f}")
    logger.info(f"📁 Output-Stream: {output_file}")
    logger.info("🔒 SICHERHEIT: Keine Original-Dateien geändert!")
    
    # Datenbank-Statistiken
    try:
        stats = db.get_processing_stats()
        if stats and stats.get('total_files', 0) > 0:
            logger.info(f"� Datenbank-Statistiken: {stats['total_files']} Dateien verarbeitet")
    except Exception as e:
        logger.debug(f"Statistiken nicht verfügbar: {e}")
    
    return processed_count, skipped_count
    
    # Größenfilter anwenden
    max_size_bytes = max_file_size_mb * 1024 * 1024
    valid_files = []
    
    for file_path in all_files:
        try:
            if file_path.stat().st_size <= max_size_bytes:
                valid_files.append(file_path)
            else:
                logger.warning(f"⚠️ Datei zu groß übersprungen: {file_path.name} ({file_path.stat().st_size / 1024 / 1024:.1f}MB)")
        except Exception as e:
            logger.warning(f"⚠️ Fehler beim Prüfen von {file_path}: {e}")
    
    logger.info(f"✅ Gültige Dateien: {len(valid_files)}")
    
    # Bereits verarbeitete Dateien filtern
    unprocessed_files = []
    skipped_count = 0
    
    logger.info("🔍 Prüfe bereits verarbeitete Dateien...")
    for i, file_path in enumerate(valid_files):
        if db.is_file_processed(file_path):
            skipped_count += 1
            logger.debug(f"⏭️ Bereits verarbeitet: {file_path.name}")
        else:
            unprocessed_files.append(file_path)
        
        # Progress-Update alle 100 Dateien bei großen Mengen
        if len(valid_files) > 100 and (i + 1) % 100 == 0:
            logger.info(f"📊 Datei-Check: {i+1}/{len(valid_files)} geprüft")
    
    logger.info(f"🆕 Neue Dateien zu verarbeiten: {len(unprocessed_files)}")
    logger.info(f"⏭️ Bereits verarbeitet: {skipped_count}")
    
    if not unprocessed_files:
        logger.info("✅ Alle Dateien bereits verarbeitet!")
        return 0, skipped_count
    
    # OPTIMIERTE Batch-Verarbeitung mit Memory-Management
    start_time = time.time()
    batch_size = 50  # Verarbeite jeweils 50 Dateien
    
    logger.info(f"🚀 Starte Verarbeitung von {len(unprocessed_files)} Dateien in Batches à {batch_size}")
    
    all_texts = []
    processed_count = 0
    
    # Verarbeitung in kleineren Batches
    for i in range(0, len(unprocessed_files), batch_size):
        batch = unprocessed_files[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (len(unprocessed_files) + batch_size - 1) // batch_size
        
        logger.info(f"📦 Batch {batch_num}/{total_batches}: {len(batch)} Dateien")
        
        try:
            batch_texts = process_file_batch_corrected(
                batch,
                tokenizer_name=model_name,
                max_length=max_length
            )
            all_texts.extend(batch_texts)
            processed_count += len(batch)
            
            # Zwischenspeicherung alle 5 Batches
            if batch_num % 5 == 0:
                logger.info(f"💾 Zwischenspeicherung nach {processed_count} Dateien...")
                
        except Exception as e:
            logger.error(f"❌ Fehler in Batch {batch_num}: {e}")
            continue
    
    # Qualitätsfilter anwenden
    high_quality_texts = []
    for text in all_texts:
        quality = calculate_chunk_quality(text)
        if quality >= quality_threshold:
            high_quality_texts.append(text)
        else:
            logger.debug(f"🚫 Chunk mit niedriger Qualität gefiltert: {quality:.2f}")
    
    logger.info(f"✅ Hochwertige Chunks: {len(high_quality_texts)} von {len(all_texts)}")
    
    # Output speichern
    timestamp = int(time.time())
    output_file = output_path / f"batch_processed_{timestamp}.jsonl"
    
    processed_count = 0
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for text in high_quality_texts:
            entry = {
                "text": text,
                "source": str(input_dir),
                "processed_at": time.time()
            }
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
            processed_count += 1
    
    # Dateien als verarbeitet markieren
    for file_path in unprocessed_files:
        db.mark_file_processed(file_path, text_count=1, quality_score=0.7)  # Durchschnittswerte
    
    elapsed_time = time.time() - start_time
    
    # Finale Statistiken
    logger.info("🎉 Batch-Verarbeitung abgeschlossen!")
    logger.info(f"✅ Verarbeitet: {len(unprocessed_files):,} Dateien")
    logger.info(f"📝 Erstellt: {processed_count:,} hochwertige Texte")
    logger.info(f"⏭️ Übersprungen: {skipped_count:,} Dateien")
    logger.info(f"⏱️ Gesamtzeit: {elapsed_time:.2f} Sekunden")
    if len(unprocessed_files) > 0:
        logger.info(f"⚡ Dateien pro Sekunde: {len(unprocessed_files) / elapsed_time:.2f}")
    logger.info(f"📁 Output-Datei: {output_file}")
    logger.info("🔒 SICHERHEIT: Keine Original-Dateien geändert!")
    
    # Datenbank-Statistiken (optional)
    try:
        stats = db.get_processing_stats()
        if stats and stats.get('total_files', 0) > 0:
            logger.info(f"📊 Datenbank-Statistiken: {stats['total_files']} Dateien verarbeitet")
    except Exception as e:
        logger.debug(f"Statistiken nicht verfügbar: {e}")
    
    return len(unprocessed_files), skipped_count


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="KORRIGIERTE Atomare Batch-Verarbeitung mit sicherer Datei-Verfolgung")
    
    # Eindeutige CLI-Parameter  
    parser.add_argument("--input", "--input-dir", type=str, required=True,
                       help="Input-Verzeichnis (Pfad zu den zu verarbeitenden Dateien)")
    parser.add_argument("--output", "--output-dir", type=str, required=True,
                       help="Output-Verzeichnis (Pfad für die verarbeiteten Dateien)")
    
    # Verarbeitungsoptionen
    parser.add_argument("--model-name", type=str, default="LeoLM/leo-hessianai-7b",
                       help="Name des Basis-Modells für Tokenizer (Default: LeoLM - optimiert für deutsche Verwaltung)")
    parser.add_argument("--max-length", type=int, default=1024,
                       help="Maximale Sequenzlänge pro Chunk")
    parser.add_argument("--max-files", type=int, default=None,
                       help="Maximale Anzahl zu verarbeitender Dateien")
    parser.add_argument("--max-file-size", type=int, default=50,
                       help="Maximale Dateigröße in MB")
    parser.add_argument("--num-processes", type=int, default=4,
                       help="Anzahl paralleler Prozesse (derzeit nicht verwendet)")
    
    # NEUE Chunking-Optionen
    parser.add_argument("--overlap-ratio", type=float, default=0.15,
                       help="Überlappungsgrad zwischen Chunks (0.0-0.5, Default: 0.15)")
    parser.add_argument("--min-chunk-size", type=int, default=30,
                       help="Mindestgröße für Chunks in Tokens (Default: 30)")
    parser.add_argument("--quality-threshold", type=float, default=0.3,
                       help="Mindest-Qualitätsscore für Chunks (0.0-1.0, Default: 0.3)")
    
    # Erweiterte Dateiformate inklusive Archive
    parser.add_argument("--file-extensions", type=str, 
                       default="txt,md,markdown,pdf,docx,html,htm,xhtml,xml,xsd,rss,atom,zip,tar,tar.gz,tgz,tar.bz2,tar.xz,7z,rar",
                       help="Zu verarbeitende Dateierweiterungen (kommagetrennt, inklusive Archive)")
    
    args = parser.parse_args()
    
    print("🚀 KORRIGIERTE Atomare Batch-Verarbeitung gestartet")
    print(f"📂 Input: {args.input}")
    print(f"📁 Output: {args.output}")
    print(f"🤖 Modell: {args.model_name}")
    print(f"📏 Max-Length: {args.max_length}")
    print(f"📄 Dateiformate: {args.file_extensions}")
    print(f"🎯 Qualitäts-Schwelle: {args.quality_threshold}")
    print()
    
    processed, skipped = atomic_batch_process(
        input_dir=args.input,
        output_dir=args.output,
        model_name=args.model_name,
        max_length=args.max_length,
        max_files=args.max_files,
        max_file_size_mb=args.max_file_size,
        file_extensions=args.file_extensions,
        overlap_ratio=args.overlap_ratio,
        min_chunk_size=args.min_chunk_size,
        quality_threshold=args.quality_threshold
    )
    
    print()
    print("=" * 60)
    print(f"✅ FERTIG: {processed} Dateien verarbeitet, {skipped} übersprungen")
    print("🔒 Alle Original-Dateien unverändert!")
    print("=" * 60)
