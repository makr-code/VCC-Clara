# CLARA Multi-Adapter Strategie (LoRA / QLoRA / DoRA)

Datum: 2025-09-18
Status: Entwurf (Phase 1)

## Ziel
Mehrere domänenspezifische Adapters (Steuerrecht, Sozialrecht, Verwaltungsverfahren etc.) effizient trainieren, versionieren und zur Laufzeit dynamisch auswählen oder kombinieren – ohne das Basismodell mehrfach zu duplizieren.

## Adapter-Typen
| Typ | Beschreibung | Speicher | Vorteil | Einsatz |
|-----|--------------|----------|---------|---------|
| LoRA | Low-Rank Delta auf FP16/FP32 Base | Gering | Stabil, etabliert | Standard-Finetuning |
| QLoRA | LoRA auf quant. (4/8-bit) Base | Sehr gering | Spart VRAM | Kleine GPUs |
| DoRA | Rank-Decomposition Variation | Mittel | Potentielle Qualitätsgewinne | Experimente |

## Grundprinzipien
1. One Base – Many Adapters
2. Adapter sind unverändert speicherbar (keine Merge-Verluste)
3. Klare Metadaten (Hash, Domain, Metriken)
4. Laufzeit-Auswahl (Hot-Swap) via Engine (vLLM empfohlen)
5. Reproduzierbarkeit durch Registry & deterministische Builds

## Verzeichnisstruktur (Ziel)
```
models/
  base/
    leo_base/              # Unverändertes Basismodell
  adapters/
    steuerrecht/lora-r16-v1/
    sozialrecht/qlora-r32-v1/
    verfahren/dora-r8-v1/
  composites/
    7f3a2c_steuer+verfahren/   # Gemergter Adapter (optional)
metadata/
  adapter_registry.json
scripts/
  clara_train_adapter.py
  build_composite.py
  export_ollama_variant.py
  list_adapters.py
  clara_serve_vllm.py (optional)
```

## Adapter Registry (Beispiel Eintrag)
```json
{
  "id": "steuerrecht-lora-r16-v1",
  "domain": ["steuerrecht"],
  "method": "lora",
  "rank": 16,
  "base_model_hash": "abc123",
  "tokenizer_hash": "def456",
  "created": "2025-09-18T12:30:00Z",
  "metrics": {"ppl_dev": 7.1, "domain_score": 0.83},
  "dataset_ref": "data/training_batches/steuer_202509.jsonl"
}
```

## Trainingsablauf (Adapter)
1. Base-Modell herunterladen / lokal bereitstellen
2. Trainingsdatensatz (domänenspezifisch) vorbereiten
3. Skript `clara_train_adapter.py` aufrufen:
```
python scripts/clara_train_adapter.py \
  --base models/base/leo_base \
  --domain steuerrecht \
  --method lora \
  --rank 16 \
  --batch-size 64 \
  --dataset data/training_batches/steuer_batch.jsonl \
  --out-dir models/adapters/steuerrecht/lora-r16-v1
```
4. Registry Update: Eintrag hinzufügen / aktualisieren
5. Evaluations-Metriken speichern

## Composite (Option)
Möglich, mehrere Adapter zu einem Zwischenmodell zu verschmelzen.
```
python scripts/build_composite.py \
  --adapters steuerrecht-lora-r16-v1 verfahren-dora-r8-v1 \
  --strategy additive \
  --out models/composites/
```
Strategien:
- additive (Standard Summation)
- weighted (Gewichtete Kombination: `--weights 0.7 0.3`)
- sequential (nacheinander anwenden, experimentell)

## Laufzeit (vLLM Ansatz)
- Start: `clara_serve_vllm.py` lädt Base
- Adapter registrieren: `POST /load_adapter`
- Aktivieren: `POST /activate_adapter {adapter_id}`
- Generieren: `POST /generate {prompt, adapter_id(optional)}`
- Routing-Schicht (optional): Klassifiziert Prompt → wählt Adapter

## Ollama Kompatibilität
- Export einzelner oder gemergter Varianten über `export_ollama_variant.py`
- Multi-Adapter Hot-Swap direkt in Ollama derzeit nicht praktikabel → vLLM bevorzugt

## Metadaten & Governance
| Aspekt | Feld | Zweck |
|--------|------|------|
| Reproduzierbarkeit | base_model_hash | Sicherstellt gleiche Ausgangslage |
| Integrität | adapter_checksum | Prüfsumme Verfälschungsschutz |
| Audit | dataset_ref | Nachvollziehbarkeit Training |
| Qualität | metrics | Vergleich & Regressionen |
| Lizenz | license | Compliance |

## Risiken / Edge Cases
| Risiko | Beschreibung | Mitigation |
|--------|--------------|-----------|
| Layer-Konflikt | Zwei Adapter ändern gleiche Module | Composite-Validierung + Warnungen |
| Qualitätsverlust Merge | Additives Mischen verschlechtert Stil | Weighted Strategie + Evaluation |
| Speicherfragmentierung | Viele LoRA Layer gleichzeitig | LRU Deaktivierung + Monitoring |
| Versionsdrift | Base Update invalidiert Adapter | Hash-Check beim Laden |
| QLoRA / LoRA Mix | Unterschiedliche Präzisionspfade | Einheitliche Baseline je Variante |
| DoRA Reifegrad | Experimentell, API Änderungen | Feature Flag + isolierte Tests |

## Evaluationsidee
- Perplexity (Dev-Set pro Domäne)
- Domänenspezifischer QA-Score (z.B. Retrieval + Answer Correctness)
- Stil-Kohärenz (Embedding Distance gegen Basiskorpus)

## Schrittweiser Implementierungsplan
| Phase | Inhalt | Deliverables |
|-------|--------|-------------|
| 1 | Registry + Verzeichnis-Konvention | `adapter_registry.json`, Doku |
| 2 | Vereinheitlichtes Trainingsskript | `clara_train_adapter.py` |
| 3 | vLLM Serving Minimal | `clara_serve_vllm.py` (Base + Load/Activate) |
| 4 | Composite Builder | `build_composite.py` + Tests |
| 5 | Export Ollama Varianten | `export_ollama_variant.py` |
| 6 | Routing + Klassifikation | `router_service.py` + Adapter Auswahl |
| 7 | Evaluation Suite | `clara_evaluate_adapter.py` |
| 8 | Monitoring & Metriken | Logs + JSON Reports |

## Nächste Schritte (konkret)
1. Leeres `adapter_registry.json` anlegen mit Schema-Kommentar
2. `clara_train_adapter.py` Skeleton erstellen (CLI + PEFT Config Auswahl)
3. Minimal `clara_serve_vllm.py` (nur Base + Health Endpoint)
4. LoRA Hot-Swap testen (lokal) → dann QLoRA Variante
5. Doku Abschnitt in `README.md` verlinken

---
*Dieser Entwurf dient als technische Ausgangsbasis. Nach Abnahme können wir sofort die Skeleton-Skripte anlegen und iterativ ausbauen.*
