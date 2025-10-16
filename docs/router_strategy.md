# Prompt & Adapter Routing Strategie

Version: 0.1.5  
Status: Phase 1 abgeschlossen; Phase 2 erweitert (Latenz, Confidence, Histogramme, Audit, Lifespan, Embedding Similarity). Exploration (einfaches ε-Greedy) initial umgesetzt.

## Ziel
Automatische Auswahl (und optional Sequenzierung) von LoRA/QLoRA Adaptern zur Beantwortung von Nutzeranfragen mit optimaler Domänenabdeckung, Qualität und Latenz – unter Wahrung von Sicherheits- und Ressourcenrestriktionen.

## High-Level Prinzipien
1. **Safety First**: Vor Routing läuft Content Filter (bereits vorhanden – `ContentFilter.assess`). Blockiert harte Verstöße, downgrades bei Risiko.
2. **Deterministisch vor Stochastic**: Erst regelbasierte schnelle Klassifikatoren (Keywords / Pattern), dann statistische / Embedding Ähnlichkeit, dann optional LLM Meta-Router.
3. **Kostenadaptive Tiefe**: Je nach Anfragekomplexität kann die Routing-Pipeline nach Stufe 1 oder 2 abbrechen.
4. **Fail-Safe Fallback**: Wenn Unsicherheit > Threshold → Default-Adapter (Baseline / Generalist) + Logging für spätere Re-Label / Training.
5. **Exploratives Lernen**: Konfidenz-Zone (Graubereich) kann A/B Routing auslösen (z.B. 10% Traffic für Kandidat B) zur Evaluationsdatensammlung.

## Komponentenübersicht
| Komponente | Rolle | Quelle |
|------------|-------|--------|
| Adapter Registry | Metadaten & verfügbare Adapter (Domäne, Metriken, Ranks) | `metadata/adapter_registry.json` |
| Content Filter | Sicherheit & PII/Injection Screening | `src/utils/content_filter.py` |
| Embedding Backend (optional) | Semantische Ähnlichkeitsbewertung Anfrage ↔ Domänenanker | `src/utils/embeddings.py` (Dummy oder sentence-transformers) |
| Heuristik Klassifikator | Schnelle Pattern / Keyword Domänenzuordnung | Neu (Regelset) |
| Scoring Engine | Vereinheitlicht Feature -> Score je Adapter | Neu |
| Decision Policy | Wählt Adapter, Confidence, Fallback, Multi-Adapter Optionen | Neu |
| Metrics Exporter | Logging von Routing-Events & Outcomes | `src/utils/metrics.py` |

## Datenflüsse
```
User Prompt
  ↓ (1) Safety Filter
  [reject|sanitize|pass]
  ↓ (2) Heuristik Routing (Keywords / Regexp / Fast map)
  ↓ (3) Embedding Similarity (optional, falls unsicher)
  ↓ (4) Adapter Score Aggregation
  ↓ (5) Decision Policy
  ↓ (6) Serving Layer (clara_serve_vllm / Adapter Hot-Swap)
  ↓ Antwort + Metrics Logging
```

## Adapter Feature Modell
Jeder Adapter i erhält Feature-Vektor F_i:
- f_dom_sim: Semantische Ähnlichkeit (0..1) zwischen Prompt und Adapter-Domänenbeschreibung
- f_kw_hit: Binär/Zählung gewichteter Keyword-Treffer
- f_prior_quality: Normalisierte Qualitätsmetrik (z.B. 1 / perplexity_dev oder domain_score)
- f_freshness: Recency Faktor (z.B. exp(-Δt / τ))
- f_usage_load: Negative Last (1 - normierte aktuelle Aktivität) zur Load-Balancing Komponente
- f_risk: Sicherheits-/Compliance Abschlag (0..1; aus Filter Kontext)

Gesamtscore S_i:
```
S_i = w_kw*f_kw_hit + w_sim*f_dom_sim + w_quality*f_prior_quality
      + w_fresh*f_freshness + w_load*f_usage_load - w_risk*f_risk
```
Gewichte initial heuristisch, später per Bayesian Optimization / Bandit lernbar.

## Regelbasierte Heuristik (Stufe 1)
Beispiele (Domain → Pattern → Adapter-ID Mapping):
- "vergaberecht", "vob", "gwb" → adapter: `public_procurement_lora`
- "bauordnung", "brandschutz" → adapter: `building_code_lora`
- "personalakte", "arbeitsvertrag" → adapter: `hr_lora`
- "haushaltssatzung", "doppik", "kameralistik" → adapter: `finance_admin_lora`
- "datenschutz", "dsgvo", "privacy" → adapter: `privacy_compliance_lora`

Trefferverfahren:
1. Tokenisiere / lowercase
2. Pattern Scan (Regex / Wortlisten)
3. Score = Anzahl gewichteter Domänen-Treffer / Normalisierung
4. Falls Score > HARD_DOMAIN_THRESHOLD → Sofort-Route Adapter
5. Sonst weiter zu Ähnlichkeitsebene

## Semantische Ähnlichkeit (Stufe 2 – Implementiert v0.1.4)
- Domain Anchor Text (derzeit: einfache Konkatenation der `domain`-Liste aus Registry) → Embedding.
- Prompt + Anchors werden gemeinsam eingebettet; Cosine Similarity pro Adapter.
- Naive additive Fusion: combined_score = heuristic_score + embedding_sim
- Confidence leichte Anhebung: +0.05 * embedding_sim (geclamped 1.0)
- Fallback auf DummyEmbeddingBackend, falls `sentence-transformers` nicht installiert.
- Aktivierung via Env: `CLARA_ROUTER_ENABLE_EMBEDDINGS=1`
- Künftige Verbesserungen: Gewichtetes Linear Model / Lernbare Fusion / Adaptive Normalisierung.

## Bandit / Exploration (Stufe 3 – Initial v0.1.5)
- Aktivierung über Env: `CLARA_ROUTER_ENABLE_EXPLORATION=1`
- Parameter: `CLARA_ROUTER_EPSILON_START` (Default 0.1), `CLARA_ROUTER_EPSILON_MIN` (noch nicht genutzt – Platzhalter für Decay)
- Trigger-Bedingung: Graubereich `conf_low < confidence < conf_high` und mehrere Kandidaten
- Aktion: Mit Wahrscheinlichkeit ε wird ein alternativer Kandidat (Top-2 bevorzugt) statt des Best-Scores gewählt
- Rationale Felder: `exploration: true`, `epsilon: <wert>`, `details.explore_alt` (ursprüngliche Top-Alternative)
- Geplant: adaptives Decay (Traffic-basiert), Reward-gestützte Selection, Off-Policy Logging

## Confidence Berechnung
```
conf = softmax_margin = sigmoid( (S_best - S_next) / temp )
```
- temp (Temperatur) reduziert mit Datenmenge.
- Rückgabe an Client: adapter_id, confidence, rationale (Top Features).

## Multi-Adapter Sequenzierung (Future)
- Für komplexe Prompts → Pipeline: Erst domain_extraction_adapter, dann specialized_adapter.
- Oder Weighted Ensemble (n Antworten → Ranking → beste Antwort selektiert). Achtung Latenz & Kosten.

## Entscheidungsmatrix
| Bedingung | Aktion |
|-----------|--------|
| Safety Reject | Abbruch + Hinweis |
| Heuristik Hard Match | Direkt Adapter A |
| High Similarity Gap | Adapter Top-1 |
| Unsicherheit Mittel | Exploration Bandit möglich |
| Unsicherheit Hoch | Fallback Base Adapter |

## Schnittstellen (API Sketch)
Geplanter Modul: `src/utils/router.py`
```
class RoutingResult(BaseModel):
    adapter_id: str
    confidence: float
    rationale: dict
    explored: bool = False
    fallback: bool = False

class AdapterRouter:
    def __init__(self, registry_path: str, embeddings: Optional[EmbeddingBackend]=None, config: RouterConfig=None): ...
    def route(self, prompt: str) -> RoutingResult: ...
    def update_feedback(self, prompt: str, adapter_id: str, reward: float): ...  # für Bandit
```

## Metriken
Aktueller Stand: Summary + zusätzlich manuelle Histogramme (Buckets konfiguriert im Code – einfache kumulative Zählung). Histogramme dienen besserer Latenz- und Confidence-Verteilungsanalyse für spätere adaptives Routing / SLO Tracking.

| Name | Typ | Beschreibung |
|------|-----|--------------|
| routing_requests_total | counter | Anzahl Routing Requests |
| routing_decision_seconds | summary | Latenz pro Routingvorgang (Mittel / Quantile) |
| routing_decision_seconds_hist | histogram | Bucketisierte Routing-Latenz (manuelle Buckets) |
| routing_confidence | summary | Confidence Verteilung |
| routing_confidence_hist | histogram | Confidence Bucket Verteilung (0–1) |
| routing_fallback_total | counter | Fallback Auslösungen |
| routing_confidence_fallback_total | counter | Fallback wegen Mindestconfidence |
| routing_adapter_selected_total | counter | Auswahl eines spezifischen Adapters (aggregiert) |
| serve_generate_requests_total | counter | Anzahl Generierungsaufrufe |
| serve_generate_latency_seconds | summary | End-to-End Latenz /generate |
| serve_generate_latency_seconds_hist | histogram | Bucketisierte Serving Latenz |
| serve_generate_tokens | summary | Tokenanzahl der Antwort |

## Logging / Audit (Neu in 0.1.3)
- Strukturierte JSONL Ereignisse (`src/utils/audit.py`): `routing_event`, `serving_event`
- Felder (Routing): timestamp, event_id, prompt_hash, adapter_id, confidence, fallback, rationale (Top Features / Heuristik), buckets (optional)
- Felder (Serving): timestamp, adapter_id, tokens, latency, routed(ja/nein), confidence(optional), fallback(optional)
- Datenschutz: Nur Hash des Prompts + optional gekürzter Auszug (Konfig zukünftige Option)
- Geplanter Rollup: Rotation / Kompression > 30 Tage

Verwendung:
1. Post-Hoc Analyse von Fehlroutings
2. Trainingsdaten-Generierung (Feedback-Korrelation)
3. Regressions-Erkennung (Confidence Drift)

## Sicherheit & Missbrauchsvermeidung
- Adversarial Versuche (gezielte Pattern-Insertion) → Score Clipping & zusätzliche Injection Heuristik
- Rate Limiting optional je Mandant (kann in Serving Layer umgesetzt werden)

## Konfigurationsparameter (Draft `router_config.yaml`)
```
thresholds:
  hard_domain: 0.75
  conf_high: 0.85
  conf_low: 0.55
similarity:
  top_k: 3
  separation_margin: 0.12
exploration:
  epsilon_start: 0.1
  epsilon_min: 0.02
  decay_steps: 5000
weights:
  kw: 1.2
  sim: 1.4
  quality: 0.8
  freshness: 0.3
  load: 0.4
  risk: 1.5
```

## Inkrementelle Implementierungsphasen
1. (Erledigt) Phase 1: Heuristik + Registry Metric Scores, einfache Confidence, Fallback (AdapterRouter + Serving Integration).
2. (Erweitert) Phase 2: Latenz & Confidence (Summary + Histogram), Audit Logging, Serving Lifespan Migration, Embedding Similarity (naive Fusion).
3. (Initial) Phase 3: Exploration ε-greedy (ohne Feedback-Auswertung) – Bandit Basis vorbereitet.
4. Phase 4: Multi-Adapter Sequenzierung + Ensemble Experimente.
5. Phase 5: Gewicht-Lernen (Bayesian Optimization / Reinforcement Signal).

## Aktuelle Serving Integration & Lifespan (Update 0.1.3)
- FastAPI Lifespan Context ersetzt veraltete `@app.on_event('startup')` Initialisierung (robuster für künftige Ressourcenverwaltung).
- Endpoint `/generate`: Automatisches Routing, wenn kein `adapter_id` gesetzt und `route=true` (Default). Optional `require_confidence` zur Mindest-Confidence.
- Endpoint `/route`: Liefert nur Routing-Entscheidung (Debug / Analyse) ohne Text-Generierung.
- Metriken erweitert: Histogramme für Routing- & Serving-Latenz + Confidence.
- Audit Events für jede Routing- & Serving-Entscheidung (Analyse / Re-Labeling / Drift Erkennung).

## Teststrategie (Vorausblick für Task 10)
- Unit: Heuristik Matching → deterministische Patterns.
- Unit: Confidence Funktion → definierte Scoreabstände.
- Unit: Fallback bei leerem Registry / keiner Domain.
- Integration: End-to-End Routing → Serving Auswahl (Mock vLLM Hot-Swap).
- Property Based (später): Prompt Variation → Stabilität der Adapterwahl.

## Offene Punkte / Nächste Schritte nach 0.1.5
- Epsilon Decay / adaptives Scheduling
- Feedback Persistenz & Reward Normalisierung (`update_feedback` API)
- Lernbare Fusion (logistische Regression / leichte MLP) der Scores
- Exploration Logging → Offline Policy Evaluation (IPS / DR Metrics)
- Datenschutz: Redaktions-Level im Audit Log konfigurierbar
- Adaptive Histogram Buckets / quantile-driven Re-Binning
- Embedding Anchor Verbesserung (Beschreibung + Beispiele + adaptives Kürzen)

---
Changelog 0.1.5:
- Exploration ε-greedy (Graubereich) implementiert
- Router rationale erweitert (`exploration`, `epsilon`, `details.explore_alt`)
- Konfigurations-Umgebungsvariablen für Exploration integriert

---
Changelog 0.1.4:
- Embedding Similarity Stage aktiviert (optional via Env Flag)
- Additive Score Fusion + leichte Confidence-Bias
- Erweiterung `embeddings.py` um SentenceTransformerBackend
- Router rationale Felder: `embedding_sim`, `combined_score`, Flag `embeddings`

---
Diese Datei wird bei Umsetzung der Phasen aktualisiert. Nächster Schritt: Minimaler `AdapterRouter` Prototyp (Phase 1) + Tests (Task 10).
