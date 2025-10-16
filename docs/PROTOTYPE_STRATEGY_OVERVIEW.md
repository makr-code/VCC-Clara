# CLARA Prototype Strategie & Funktionsübersicht

Datum: 2025-09-18  
Status: Konsolidierte technische Zusammenfassung (Prototyp Phase) – aktualisiert mit Routing v0.1.3 (Audit, Histogramme, Lifespan)

Diese Datei bietet eine verdichtete, architektur- und strategieorientierte Übersicht über den aktuellen Stand des CLARA Prototyps basierend auf Quell-Code (`scripts/`) und bestehender Dokumentation (`docs/`). Ziel ist es, Entscheidungsträgern, Entwicklern und Forschern einen klaren Blick auf Kernkomponenten, Datenflüsse, Risiken und nächste Schritte zu geben.

---
## 1. Ziele & Leitprinzipien
- Kontinuierliches domänenspezifisches Lernen (Verwaltung / Recht) ohne Downtime
- Speicher- und Kosten-Effizienz mittels LoRA/QLoRA/DoRA statt Full-Finetuning
- Modularität: One Base – Many Adapters (Hot-Swap & Versionierung)
- Sichere, nachvollziehbare Datenverwendung (Qualitätsfilter, Hashing, Registry)
- Skalierbare Verarbeitung großer Dokumentenmengen (Batch + Streaming)
- Reproduzierbarkeit durch Revision/Commit-Pinning und Environment-Freeze

---
## 2. Systemische Hauptkomponenten
| Komponente | Rolle | Quelle |
|------------|------|--------|
| API / Serving Layer | REST-Interface & Adapter-Hot-Swap (Fake/Future vLLM), Lifespan-Init | `clara_serve_vllm.py` |
| Training Pipeline | Initiales LoRA/QLoRA Feintuning | `clara_train_lora.py`, `clara_train_qlora.py` |
| Kontinuierliches Lernen | Live Feedback → Mini-LoRA Updates | `clara_continuous_learning.py` |
| Multi-Adapter Strategie | Versionierung, Auswahl, Kombination, Routing Heuristik | `MULTI_ADAPTER_STRATEGY.md`, `router_strategy.md` |
| Batch Processing | Intelligente, duplikat-sichere Dokumentaufbereitung | `intelligent_batch_processor.py`, `smart_batch_processor*.py` |
| Adapter Registry & Metadata | Nachvollziehbarkeit & Governance | `metadata/adapter_registry.json` |
| Veritas Integration | Rechtsdomänen-spezifische Pipelines | `veritas_*`, `VERITAS_INTEGRATION.md` |
| Monitoring & Metriken | Training / Inferenz / Qualität + Histogramme + Audit | `monitor_training.py`, `monitor_archive_processing.py`, `src/utils/metrics.py`, `src/utils/audit.py` |

---
## 3. Architektur – High Level Datenfluss
```
[ Rohdaten / Archive ]
        ↓ (Extraktion + Normalisierung)
  Batch / Smart Processor  ──►  Trainingskorpus ─┐
                                                │ (Initial Fine-Tuning)
                                   LoRA/QLoRA Training Scripts ─► Adapter Artefakte
                                                │                    │
                                        Adapter Registry <──────────┘
                                                │
                                    vLLM / Serving Engine (Base + Adapters)
                                                │
                                  Nutzerinteraktion / Domain-Abfragen
                                                │
                                     Feedback (Bewertung, Korrektur)
                                                │
                            Continuous LoRA Learning (Mini-Batches)
                                                │
                                        Aktualisierte Adapter-Version
```

---
## 4. Trainingspipeline (Initial Fine-Tuning)
Quelle: `clara_train_lora.py`

### Ablauf
1. Konfiguration laden (`configs/*_config.yaml`)
2. Basismodell mit Retry- & Fallback-Logik laden (Flash Attention / Netzwerkfehler → Ersatzmodell)
3. Tokenizer Normalisierung (Pad Token Sicherung)
4. Datensatz: JSONL oder Processor (`VerwaltungsDataProcessor`)
5. Tokenisierung mit konsistentem Padding (`max_length`, labels = input_ids)
6. Split (optional Validation)
7. LoRA-Konfiguration anwenden (`r`, `alpha`, `dropout`, `target_modules`)
8. Training mit speichereffizientem Custom-Trainer (Cache-Leerung alle 100 Steps)
9. Checkpoint/Resume Handling (Manuell + automatisch)
10. Optional: Ollama Export (`save_model_for_ollama`)

### Resilienz-Merkmale
- Netzwerk-Retries und exponentieller Backoff
- Fallback Modell (DiscoLM) bei Inkompatibilitäten
- GPU Memory Safe Guards (FP16 + low_cpu_mem_usage)

---
## 5. Kontinuierliches Lernen (Online LoRA Updates)
Quelle: `clara_continuous_learning.py` + `CONTINUOUS_LEARNING.md`

| Element | Beschreibung |
|---------|--------------|
| Live Buffer | Deque mit Qualitätsfilter (`quality_threshold`) |
| Sample Ranking | Sortierung nach `feedback_score * importance` |
| Batch Trigger | Mindestanzahl + Intervall (`train_interval`) |
| Mini-Training | 1 Epoch, sehr niedrige LR (`1e-6` bis `5e-6`), kleine Batches |
| Persistenz | Adapter-Inkrementelles Speichern nach jedem Mini-Zyklus |
| Metriken | `model_updates`, `successful_trainings`, Ø Sample Qualität |

### Sicherheits-/Qualitätsmechanismen
- Negative oder unter Schwelle liegende Bewertungen werden verworfen
- Importance moduliert Impact starker Ausreißer
- Kein Warmup / Minimale Overfitting-Risiken durch niedrige LR

### Erweiterungspotential
- A/B Vergleich von Adapterständen
- Weighted Replay von stabilen High-Quality Batches
- Drift Detection (Qualitätssenkung → Rollback)

---
## 6. Multi-Adapter Strategie
Quelle: `MULTI_ADAPTER_STRATEGY.md`

| Ziel | Umsetzung |
|------|-----------|
| Parallele Domänen | Verzeichnisstruktur `models/adapters/<domain>/<method>-rX-vY` |
| Reproduzierbarkeit | `base_model_hash`, `tokenizer_hash` in Registry |
| Governance | Einheitliche JSON Schema-Einträge |
| Kombination | `build_composite.py` (additive / weighted / sequential) |
| Serving | vLLM Hot-Swap (zukünftige Implementierung) |

### Adapter Registry Minimalfeld (Beispiel)
```
{
  "id": "steuerrecht-lora-r16-v1",
  "domain": ["steuerrecht"],
  "method": "lora",
  "rank": 16,
  "base_model_hash": "abc123",
  "metrics": {"ppl_dev": 7.1},
  "dataset_ref": "data/training_batches/steuer_202509.jsonl"
}
```

### Risiken & Mitigation
| Risiko | Wirkung | Gegenmaßnahme |
|--------|---------|---------------|
| Layer-Konflikt Merge | Qualitätsverlust | Merge Validierung + Evaluations-Report |
| Versionsdrift Base | Adapter unbrauchbar | Hash-Prüfung beim Laden |
| Speicherfragmentierung | VRAM Peaks | LRU Deaktivierung/Entladen inaktive Adapter |
| Inhomogene Präzision | Instabilität | Einheitliche Baseline (FP16 vs 4bit) |

---
## 7. Batch Processing & Datenqualität
Quelle: `intelligent_batch_processor.py`, `smart_batch_processor*.py`

### Kernfunktionen
- Duplikaterkennung per SHA-256 + Metadatenvergleich
- SQLite Cache (`processed_files`) mit Hash / Größe / mtime
- Automatisches Entfernen veralteter Einträge (Cleanup)
- Unterschied zwischen neuen vs. bereits verarbeiteten Dateien

### Nutzen
- Verhindert redundante Tokenisierung & Kosten
- Ermöglicht inkrementelle Daten-Pipelines
- Basis für Auditierbarkeit (Zeitstempel, Batch-Zuordnung)

### Erweiterungsideen
- Qualitäts-Scoring (Lesbarkeit, Länge, Domain-Relevanz)
- Adaptive Chunking für sehr große Dateien
- Format-spezifische Parser (PDF Layout, Tabellen Extraktion)

---
## 8. Serving & Inferenz (vLLM Skeleton + Lifespan)
Quelle: `clara_serve_vllm.py`

| Endpoint | Funktion | Status |
|----------|----------|--------|
| GET /health | Liveness Check | Implementiert |
| GET /status | Adapter & Base Modell Übersicht | Implementiert |
| POST /load_adapter | Adapter registrieren (Pfad / Registry) | Basis (Stub) |
| POST /activate_adapter | Aktiven Adapter setzen | Basis |
| POST /generate | Textgenerierung (+ optional Routing) | Fake Output / Simulation |
| POST /deactivate_adapter | Adapter deaktivieren | Implementiert |
| POST /route | Nur Routing Entscheidung | Implementiert |

### Aktuelle Erweiterungen (Stand 0.1.3)
- Lifespan Context (statt deprecated startup event)
- Heuristik Prompt Routing (AdapterRouter Phase 1)
- Latenz & Confidence Metriken (Summary + Histogramm)
- Audit Logging (Routing + Serving Events)

### Geplante Erweiterungen
- Direkter Aufruf `LLM.generate()` mit `lora_request`
- Streaming Output (SSE / WebSocket)
- Embedding Similarity Layer (Phase 2 Rest)
- Exploration / Bandit Routing (Phase 3)
- Metrik-Export für Prometheus (native Histogram Mapping)

---
## 9. Monitoring & Telemetrie (Erweitert)
Aktuelle Mechanismen:
- `wandb` (optional) für Trainingsmetriken
- Periodische Logs (Memory / Steps / Checkpoints)
- Cache-Statistiken über CLI (`intelligent_batch_processor.py stats`)
- Custom Metrics Exporter (Counter, Summary, Histogram – manuell)
- Audit Log JSONL (Routing & Serving Events)

Empfohlene Ergänzungen:
- Prometheus kompatibler Export Endpoint
- Adapter Lade-/Aktivierungsereignisse detaillierter auditieren
- Drift & Regressions Detection (Confidence & Latenz Verteilungen)
- Embedding Similarity Scores protokollieren (Phase 2 Abschluss)

---
## 10. Reproduzierbarkeit & Environment
- vLLM Installation Guide mit Commit-Pinning (`VLLM_INSTALLATION.md`)
- Empfehlung: `metadata/vllm_environment_lock.json` + `pip_freeze_vllm.txt`
- Hashing von Basis- und Adaptermodellen vor Deployment
- Einheitliche Konfigurationsprofile (`configs/*.yaml`)

---
## 11. Roadmap (aus konsolidierten Quellen)
| Phase | Fokus | Relevanz für Prototyp |
|-------|-------|-----------------------|
| Phase 1 | Stabilisierung & Basis-LoRA | Abgeschlossen (Foundation gelegt) |
| Phase 2 | Routing Observability & Similarity | Teilweise (Heuristik + Audit + Histogramme) |
| Phase 3 | Exploration/Bandit + Feedback Loop | In Planung |
| Phase 4 | Multi-Adapter Sequenzierung / Ensemble | In Planung |
| Phase 5 | Plattform & Ecosystem | Langfristig |

---
## 12. Risikoanalyse (Querschnitt)
| Kategorie | Risiko | Auswirkung | Mitigation |
|-----------|--------|-----------|-----------|
| Daten | Schlechte Feedbackqualität | Modellverschlechterung | Striktere Filter / Human Review Sampling |
| Modell | Adapter Inkompatibel nach Base Update | Downtime / Neu-Training | Hash Gate + Canary Test |
| Performance | VRAM Engpass bei Multi-Adaptern | Latenz / OOM | Lazy Load + Entladung |
| Sicherheit | Ungeprüfte Eingaben im Continuous Learning | Datenvergiftung | Sanitization + Negativ-Listen |
| Governance | Fehlende Nachvollziehbarkeit | Audit Probleme | Vollständige Registry + Signaturen |
| Technisch | API Drift vLLM LoRA Hooks | Blockierte Integration | Versions-Pinning + Abstraktionslayer |

---
## 13. Empfohlene Sofort-Schritte (Aktualisiert)
1. Embedding Backend Auswahl & Integration in Routing (Similarity Layer aktivieren)
2. Exploration / Bandit Logik in Confidence Grauzone implementieren
3. Prometheus Export Mapping (Histogram Buckets adaptieren)
4. Feedback Persistenz (lightweight DB) + `update_feedback` API
5. Evaluation Suite für Routing Qualität (Golden Prompts)
6. Audit Log Rotation & DSGVO Redaktions-Konfiguration

---
## 14. Nächste Erweiterungen (kurzfristig)
| Feature | Nutzen | Aufwand |
|---------|--------|---------|
| Embedding Similarity Layer | Bessere Domänenzuordnung | Mittel |
| Exploration Routing | Datensammlung & Optimierung | Mittel |
| Weighted Adapter Merge | Qualität bei Composite Builds | Mittel |
| A/B Deployment Endpoint | Evaluierte Modell-Updates | Mittel |
| Evaluation Suite | Regressionsschutz | Hoch |
| Web Dashboard | Transparente Überwachung | Mittel |
| Prometheus Export | Produktionsüberwachung | Mittel |

---
## 15. Querverweise
| Bereich | Datei |
|--------|-------|
| Systemüberblick | `SYSTEM_OVERVIEW.md` |
| Roadmap | `ROADMAP.md` |
| Kontinuierliches Lernen | `CONTINUOUS_LEARNING.md` |
| Multi-Adapter Strategie | `MULTI_ADAPTER_STRATEGY.md` |
| Routing Strategie & Audit | `router_strategy.md` |
| vLLM Setup | `VLLM_INSTALLATION.md` |
| Batch Verarbeitung | `BATCH_PROCESSING_QUICK_REFERENCE.md` / `SAFE_BATCH_PROCESSING_GUIDE.md` |
| Veritas Domäne | `VERITAS_INTEGRATION.md` |
| Modelle & Varianten | `MODELS.md` |

---
*Dieses Dokument ist lebendig: Bei strukturellen Änderungen oder neuen Architekturentscheidungen bitte zuerst hier aktualisieren und anschließend in Detail-Dokumente verlinken.*
