"""CLARA Content / Safety Filter (leichtgewichtig)

Ziele:
  - Schnelle Heuristiken bevor Live-Samples in den Continuous-Learning-Puffer gelangen
  - Erkennung einfacher Prompt-Injection-Muster
  - Grobe PII-Heuristik (E-Mails, Telefonnummern, IBAN, Personalausweis rudimentär)
  - Konfigurierbare Schwellen & einfache Scoring-Rückgabe

Nicht-Ziele:
  - Vollständige Moderation oder rechtliche PII-Garantie
  - ML-basierte Klassifikation

Verwendung:
    from src.utils.content_filter import ContentFilter
    cf = ContentFilter()
    result = cf.assess(text)
    if result.accept:
        buffer.add(...)

Ergebnisstruktur (dataclass FilterResult):
  - accept: bool (True = darf rein)
  - reasons: List[str] (getriggerte Regeln)
  - score: float (0-1 Qualitätsschätzer, aktuell = 1 - penalties kumulativ begrenzt)
  - metadata: Dict[str, Any]

Erweiterbar für zukünftige ML-Modelle.
"""
from __future__ import annotations
import re
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Pattern


@dataclass
class FilterResult:
    accept: bool
    reasons: List[str]
    score: float
    metadata: Dict[str, Any]


class ContentFilter:
    def __init__(self,
                 enable_injection: bool = True,
                 enable_pii: bool = True,
                 min_length: int = 8,
                 max_length: int = 8000,
                 max_penalty: float = 0.8):
        self.enable_injection = enable_injection
        self.enable_pii = enable_pii
        self.min_length = min_length
        self.max_length = max_length
        self.max_penalty = max_penalty

        # Injection Muster (einfach)
        self.injection_patterns: List[Pattern[str]] = [
            re.compile(r"(?i)ignore\s+previous\s+instructions"),
            re.compile(r"(?i)disregard\s+all\s+prior"),
            re.compile(r"(?i)system\s*:\s*"),
            re.compile(r"(?i)you\s+are\s+now\s+.*model"),
        ]

        # PII Muster (rudimentär)
        self.pii_patterns: Dict[str, Pattern[str]] = {
            "email": re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
            "phone": re.compile(r"\b(?:\+\d{1,3}[ -]?)?(?:\d[ -]?){8,14}\b"),
            "iban": re.compile(r"\b[A-Z]{2}[0-9A-Z]{13,30}\b"),
        }

    def assess(self, text: str) -> FilterResult:
        reasons: List[str] = []
        penalty = 0.0
        meta: Dict[str, Any] = {}

        length = len(text)
        meta["length"] = length
        if length < self.min_length:
            reasons.append("too_short")
            penalty += 0.2
        if length > self.max_length:
            reasons.append("too_long")
            penalty += 0.5

        if self.enable_injection:
            inj_hits = []
            for pat in self.injection_patterns:
                if pat.search(text):
                    inj_hits.append(pat.pattern)
            if inj_hits:
                reasons.append("prompt_injection")
                meta["injection_hits"] = inj_hits
                penalty += 0.4

        if self.enable_pii:
            pii_hits = {}
            for name, pat in self.pii_patterns.items():
                matches = pat.findall(text)
                if matches:
                    pii_hits[name] = matches[:5]
            if pii_hits:
                reasons.append("pii_detected")
                meta["pii_hits"] = pii_hits
                penalty += 0.3

        # Begrenzen
        if penalty > self.max_penalty:
            penalty = self.max_penalty

        score = round(1.0 - penalty, 4)
        accept = "prompt_injection" not in reasons and score >= 0.4
        return FilterResult(accept=accept, reasons=reasons, score=score, metadata=meta)


_global_filter: Optional[ContentFilter] = None


def get_content_filter() -> ContentFilter:
    global _global_filter
    if _global_filter is None:
        _global_filter = ContentFilter()
    return _global_filter
