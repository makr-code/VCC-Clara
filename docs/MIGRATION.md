# MIGRATION: Datenverzeichnis `Y:\\veritas\\data` → `Y:\\data`

Datum: 2025-09
Status: ABGESCHLOSSEN

## Hintergrund
Das ursprüngliche Quellverzeichnis für Rechts- und Verwaltungsdokumente lautete `Y:\veritas\data`. Zur Vereinheitlichung und klareren Trennung zwischen Anwendungscode und Rohdaten wurde das Standardverzeichnis auf `Y:\data` migriert.

## Ziele der Migration
- Vereinfachte Pfadangaben in Skripten und Dokumentation
- Klarer, neutraler Daten-Root für mehrere Projekte (nicht nur "veritas")
- Minimierung von Hardcodings in zukünftigen Erweiterungen
- Einheitliche Nutzung durch ENV Override `CLARA_DATA_DIR`

## Auswirkungen
| Bereich | Vorher | Nachher |
|--------|--------|---------|
| Standard-Input-Pfad | `Y:\veritas\data` | `Y:\data` |
| Batch-Skripte | Veritas-spezifische Beispiele | Generische Beispiele |
| Dokumentation | Mehrfacher Verweis auf `Y:\veritas\data` | Aktualisiert auf `Y:\data` |
| ENV Override | (teilweise) | Konsistent unterstützt |

## Was müssen Sie tun?
1. Prüfen Sie, ob Ihr Datenbestand bereits unter `Y:\data` liegt.
2. Falls die Daten noch unter `Y:\veritas\data` liegen:
   - Option A: Weiterhin mit `--input "Y:\veritas\data"` arbeiten (voll kompatibel)
   - Option B: Dateien KOPIEREN (nicht verschieben) nach `Y:\data`
   - Option C: Temporär `CLARA_DATA_DIR=Y:\veritas\data` setzen
3. Batch- oder Automationsskripte anpassen, falls sie alte Pfade hardcodiert verwenden.

## ENV Override Beispiele
PowerShell:
```
$env:CLARA_DATA_DIR = 'Y:\data'
```
CMD:
```
set CLARA_DATA_DIR=Y:\data
```

## Validierung
Nach erfolgreicher Migration können Sie mit einem erneuten Lauf der Batch-Processor prüfen:
```
python scripts/smart_batch_processor.py "Y:\data" "data/processed" --db-stats
```

## Häufige Fragen (FAQ)
**Kann ich `Y:\veritas\data` weiter verwenden?**
Ja, über explizites `--input` oder `CLARA_DATA_DIR`.

**Warum nicht automatisch verschieben?**
Weil das Projekt strikte Unveränderbarkeit der Original-Dateien garantiert.

**Was passiert mit bereits verarbeiteten Dateien in der Datenbank?**
Dateisignaturen basieren auf Inhalt/Hash; Pfadänderungen ohne Kopie könnten als "neu" erscheinen, falls absolute Pfade gespeichert werden. In aktuellen Skripten liegt Fokus auf Inhalt – prüfen Sie `--db-stats`.

**Muss ich die Datenbank zurücksetzen?**
Nur wenn Sie bewusst alle Dateien erneut verarbeiten wollen (`--clear-db`).

## Nacharbeiten / Technische Schulden
- Prüfen, ob irgendwo noch Inline-Kommentare mit altem Pfad bestehen (nur historische Abschnitte erlaubt)
- Evtl. Alias-Hinweis in zukünftiger GUI ergänzen

## Abschluss
Die Migration ist abgeschlossen. Neue Dokumentation, Skripte und Beispiele nutzen `Y:\data`. Historische Erwähnungen von `Y:\veritas\data` bleiben nur zu Referenzzwecken bestehen.

---
Bei Rückfragen: interner Issue-Tracker oder Maintainer-Team.
