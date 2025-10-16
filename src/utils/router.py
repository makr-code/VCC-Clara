"""Phase 1 Adapter Routing

Minimaler Heuristik-basierter Router basierend auf dem in docs/router_strategy.md beschriebenen Konzept.

Funktionen:
- Laden der Adapter Registry
- Heuristische Domain Pattern Erkennung
- Scoring (nur Keyword Hit + optional metric domain_score)
- Confidence Abschätzung (Differenz der Top Scores)
- Fallback auf Default Adapter (konfigurierbar)

Diese erste Version enthält KEINE Embeddings, KEIN Exploration/Bandit.
"""
from __future__ import annotations

import json
import time
import re
import hashlib
import os
import random
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Optional, Any

try:
    from pydantic import BaseModel
except ImportError:  # Fallback falls pydantic nicht installiert ist
    class BaseModel:  # type: ignore
        pass

# ---------------------------------------------------------------------------
# Datenmodelle
# ---------------------------------------------------------------------------
class RoutingResult(BaseModel):  # type: ignore
    adapter_id: str
    confidence: float
    rationale: Dict[str, Any]
    fallback: bool = False


@dataclass
class HeuristicRule:
    adapter_id: str
    patterns: List[str]  # Regex oder einfache Keywords (lower-case)
    weight: float = 1.0

    def score_prompt(self, prompt_lc: str) -> float:
        score = 0.0
        for p in self.patterns:
            if re.search(r"\b" + re.escape(p) + r"\b", prompt_lc):
                score += self.weight
        return score


# ---------------------------------------------------------------------------
# Router Implementierung
# ---------------------------------------------------------------------------
class AdapterRouter:
    def __init__(
        self,
        registry_path: str | Path = "metadata/adapter_registry.json",
        default_adapter: Optional[str] = None,
        hard_domain_threshold: float = 1.5,
        conf_high: float = 0.85,
        conf_low: float = 0.55,
        use_domain_score: bool = True,
        enable_embeddings: Optional[bool] = None,
        embedding_backend: Any = None,
    ) -> None:
        self.registry_path = Path(registry_path)
        self.default_adapter = default_adapter
        self.hard_domain_threshold = hard_domain_threshold
        self.conf_high = conf_high
        self.conf_low = conf_low
        self.use_domain_score = use_domain_score
        self._registry = self._load_registry()
        self.rules: List[HeuristicRule] = self._build_rules_from_registry()
        # Embedding Aktivierung (Umgebungsvariable steuert Default)
        if enable_embeddings is None:
            enable_embeddings = os.environ.get("CLARA_ROUTER_ENABLE_EMBEDDINGS", "0") in ("1", "true", "True")
        self._enable_embeddings = enable_embeddings
        self._embedding_backend = embedding_backend
        if self._enable_embeddings and self._embedding_backend is None:
            try:  # Lazy Import
                from src.utils.embeddings import SentenceTransformerEmbeddingBackend  # type: ignore
                self._embedding_backend = SentenceTransformerEmbeddingBackend()
            except Exception:  # pragma: no cover
                try:
                    from src.utils.embeddings import DummyEmbeddingBackend  # type: ignore
                    self._embedding_backend = DummyEmbeddingBackend()
                except Exception:
                    self._embedding_backend = None
        # Exploration Parameter (epsilon) – adaptiv oder statisch
        self._exploration_enabled = os.environ.get("CLARA_ROUTER_ENABLE_EXPLORATION", "0") in ("1", "true", "True")
        try:
            self._epsilon_start = float(os.environ.get("CLARA_ROUTER_EPSILON_START", 0.1))
            self._epsilon_min = float(os.environ.get("CLARA_ROUTER_EPSILON_MIN", 0.02))
        except ValueError:
            self._epsilon_start, self._epsilon_min = 0.1, 0.02
        # Einfaches statisches epsilon vorerst (kein Decay-Zähler implementiert)
        self._epsilon = self._epsilon_start

    # ------------------------- Registry Handling -------------------------
    def _load_registry(self) -> Dict[str, Any]:
        if not self.registry_path.exists():
            return {"adapters": []}
        try:
            with self.registry_path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"adapters": []}

    def _build_rules_from_registry(self) -> List[HeuristicRule]:
        rules: List[HeuristicRule] = []
        for entry in self._registry.get("adapters", []):
            adapter_id = entry.get("id")
            domains = entry.get("domain", [])
            if not adapter_id or not domains:
                continue
            # Jede Domain als Pattern (vereinfachte Heuristik)
            patterns = [d.lower() for d in domains]
            rules.append(HeuristicRule(adapter_id=adapter_id, patterns=patterns, weight=1.0))
        # Füge einige generische vordefinierte Regeln hinzu (falls gewünscht später konfigurierbar)
        static_rules = [
            HeuristicRule(adapter_id="privacy_compliance_lora", patterns=["dsgvo", "datenschutz", "privacy"], weight=1.2),
            HeuristicRule(adapter_id="public_procurement_lora", patterns=["vergabe", "gwb", "vob"], weight=1.1),
            HeuristicRule(adapter_id="finance_admin_lora", patterns=["haushalt", "kameralistik", "doppik"], weight=1.0),
        ]
        # Nur hinzufügen, falls Adapter nicht bereits in Registry-Regeln enthalten
        existing = {r.adapter_id for r in rules}
        for sr in static_rules:
            if sr.adapter_id not in existing:
                rules.append(sr)
        return rules

    # ----------------------------- Routing ------------------------------
    def route(self, prompt: str) -> RoutingResult:
        start_t = time.time()
        prompt_lc = prompt.lower()
        # 1. Heuristik Scores
        scored: List[tuple[str, float, Dict[str, Any]]] = []  # (adapter_id, score, feature_detail)
        for rule in self.rules:
            s = rule.score_prompt(prompt_lc)
            if s > 0:
                domain_score_feat = None
                if self.use_domain_score:
                    domain_score_feat = self._lookup_domain_metric(rule.adapter_id)
                    if domain_score_feat is not None:
                        # Leichte Gewichtung einfließen lassen
                        s += 0.3 * domain_score_feat
                scored.append(
                    (
                        rule.adapter_id,
                        s,
                        {
                            "heuristic_score": s,
                            "patterns": rule.patterns,
                            "domain_metric": domain_score_feat,
                        },
                    )
                )
        # 2. Wenn keine Treffer -> Fallback
        if not scored:
            result = self._fallback_result(reason="no_heuristic_match")
            latency = time.time() - start_t
            self._record_metrics(latency, result)
            self._audit(prompt, latency, result)
            return result

        # 3. Optional: Embedding Similarity (nur wenn mehrere Kandidaten)
        if self._enable_embeddings and self._embedding_backend and len(scored) > 1:
            try:
                # Domain Strings sammeln
                adapter_ids = [a for a, _, _ in scored]
                domains = []
                for aid in adapter_ids:
                    entry = next((e for e in self._registry.get("adapters", []) if e.get("id") == aid), {})
                    dom_list = entry.get("domain", [])
                    domains.append(" ".join(dom_list) if dom_list else aid)
                # Embeddings: erster ist Prompt
                from src.utils.embeddings import EmbeddingBackend  # type: ignore
                vecs = self._embedding_backend.embed([prompt] + domains)  # type: ignore
                q = vecs[0]
                import math
                def cos(a, b):
                    return sum(x*y for x, y in zip(a, b)) / ((math.sqrt(sum(x*x for x in a)) or 1.0) * (math.sqrt(sum(x*x for x in b)) or 1.0))
                sims = [cos(q, v) for v in vecs[1:]]
                enriched = []
                for (aid, score, detail), sim in zip(scored, sims):
                    combined = score + sim  # einfache additive Fusion
                    detail = {**detail, "embedding_sim": round(sim, 4), "combined_score": round(combined, 4)}
                    enriched.append((aid, combined, detail))
                scored = enriched
            except Exception:  # pragma: no cover
                pass

        # 4. Sortieren nach (ggf. kombiniertem) Score
        scored.sort(key=lambda x: x[1], reverse=True)
        best_id, best_score, best_detail = scored[0]
        second_score = scored[1][1] if len(scored) > 1 else 0.0

    # 5. Hard Domain Threshold (Sofortannahme)
        if best_score >= self.hard_domain_threshold:
            confidence = self._confidence(best_score, second_score)
            result = RoutingResult(
                adapter_id=best_id,
                confidence=confidence,
                rationale={
                    "reason": "hard_domain_threshold",
                    "best_score": best_score,
                    "second_score": second_score,
                    "details": best_detail,
                },
                fallback=False,
            )
            latency = time.time() - start_t
            self._record_metrics(latency, result)
            self._audit(prompt, latency, result)
            return result

        # 6. Confidence Einschätzung
        confidence = self._confidence(best_score, second_score)
        # leichte Confidence Anpassung bei Embedding Nutzung
        if self._enable_embeddings and len(scored) > 1:
            emb_sim = scored[0][2].get("embedding_sim")
            if isinstance(emb_sim, (int, float)):
                confidence = min(1.0, confidence + 0.05 * emb_sim)
        if confidence < self.conf_low:
            result = self._fallback_result(
                reason="low_confidence",
                extra={
                    "best_candidate": best_id,
                    "best_score": best_score,
                    "second_score": second_score,
                    "raw_scored": scored[:5],
                },
            )
            latency = time.time() - start_t
            self._record_metrics(latency, result)
            self._audit(prompt, latency, result)
            return result

        explored = False
        selected_id = best_id
        # 7. Exploration (nur wenn mehrere Kandidaten & im Graubereich)
        if (
            len(scored) > 1
            and self._exploration_enabled
            and self.conf_low < confidence < self.conf_high
        ):
            if random.random() < self._epsilon:
                # Wähle zufälligen anderen Kandidaten (Top-2 bevorzugt)
                alt_candidates = [c for c in scored[1:3] if c[0] != best_id] or scored[1:]
                if alt_candidates:
                    chosen = random.choice(alt_candidates)
                    selected_id = chosen[0]
                    explored = True
                    best_detail = {**best_detail, "explore_alt": selected_id}

        # 8. Normaler Return (selected_id statt best_id bei Exploration)
        result = RoutingResult(
            adapter_id=selected_id,
            confidence=confidence,
            rationale={
                "reason": "normal_selection",
                "best_score": best_score,
                "second_score": second_score,
                "details": best_detail,
                "embeddings": bool(self._enable_embeddings),
                "exploration": explored,
                "epsilon": round(self._epsilon, 4) if explored else None,
            },
            fallback=False,
        )
        latency = time.time() - start_t
        self._record_metrics(latency, result)
        self._audit(prompt, latency, result)
        return result

    # --------------------------- Hilfsfunktionen ------------------------
    def _confidence(self, best: float, second: float) -> float:
        if best <= 0:
            return 0.0
        margin = best - second
        # Einfache S-Kurve
        # Skalierung: wenn margin >= best -> sehr hohe Confidence
        raw = margin / max(best, 1e-6)
        # Begrenze Wert
        if raw <= 0:
            return 0.0
        if raw >= 1:
            return 0.99
        # Sigmoid Approx (vereinfachte Transformation)
        return round(1 / (1 + (2.71828 ** (-4 * (raw - 0.5)))), 4)

    def _fallback_result(self, reason: str, extra: Optional[Dict[str, Any]] = None) -> RoutingResult:
        adapter_id = self.default_adapter or "base_default_adapter"
        rationale = {"reason": reason}
        if extra:
            rationale.update(extra)
        return RoutingResult(
            adapter_id=adapter_id,
            confidence=0.0,
            rationale=rationale,
            fallback=True,
        )

    def _record_metrics(self, latency: float, result: RoutingResult) -> None:
        # Lazy Import um Zyklus zu vermeiden
        try:
            from src.utils.metrics import get_metrics_exporter  # noqa
        except Exception:
            return
        exp = get_metrics_exporter()
        exp.observe("routing_decision_seconds", latency)
        try:
            exp.observe_histogram("routing_decision_seconds_hist", latency)
        except Exception:
            pass
        exp.observe("routing_confidence", result.confidence)
        try:
            exp.observe_histogram("routing_confidence_hist", result.confidence)
        except Exception:
            pass
        if result.fallback:
            exp.inc("routing_fallback_total")

    def _audit(self, prompt: str, latency: float, result: RoutingResult) -> None:
        try:
            from src.utils.audit import log_routing_event
            log_routing_event(
                prompt_hash=self.prompt_hash(prompt),
                adapter_id=result.adapter_id,
                confidence=result.confidence,
                fallback=result.fallback,
                rationale=result.rationale,
                extra={"latency": latency},
            )
        except Exception:
            pass

    def _lookup_domain_metric(self, adapter_id: str) -> Optional[float]:
        for entry in self._registry.get("adapters", []):
            if entry.get("id") == adapter_id:
                metrics = entry.get("metrics", {})
                val = metrics.get("domain_score")
                if isinstance(val, (int, float)):
                    return float(val)
        return None

    # Utility für Logging Hash (DSGVO-schonend)
    @staticmethod
    def prompt_hash(prompt: str) -> str:
        return hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:16]


__all__ = ["AdapterRouter", "RoutingResult"]
