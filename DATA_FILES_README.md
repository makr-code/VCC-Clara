# Clara Data Files

Große Datendateien (>100MB) werden nicht in Git eingecheckt.

## Ausgeschlossene Dateien

- `data/processed/*.jsonl` - Verarbeitete Batch-Daten
- `data/raw/large_files/` - Große Rohdaten

## Daten-Management

1. **Lokale Datenverarbeitung**
   - Alle `.jsonl` Dateien in `data/processed/` bleiben lokal
   - Fügen Sie große Dateien zu `.gitignore` hinzu

2. **Backup-Strategie**
   - Verwenden Sie externe Speicherlösungen (OneDrive, Dropbox, etc.)
   - Oder nutzen Sie Git LFS für große Dateien

3. **Datenwiederherstellung**
   - Dokumentieren Sie den Datenursprung
   - Verwenden Sie reproduzierbare Skripte zur Datengenerierung

**Hinweis:** Diese Beschränkung gilt nur für Git. Lokal können Sie beliebig große Dateien verwenden.
