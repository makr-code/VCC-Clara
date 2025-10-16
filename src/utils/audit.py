"""Audit Logging für Routing & Serving Ereignisse.

Funktionen:
  - log_routing_event(prompt_hash, adapter_id, confidence, fallback, rationale)
  - log_serving_event(adapter_id, tokens, latency, routed, extra)

Speichert JSONL unter audit/audit_log.jsonl. Fehlertolerant, thread-safe.
"""
from __future__ import annotations
import json
import threading
import time
from pathlib import Path
from typing import Any, Dict, Optional

_AUDIT_PATH = Path("audit/audit_log.jsonl")
_AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
_lock = threading.Lock()


def _write(record: Dict[str, Any]) -> None:
    record["ts"] = time.time()
    try:
        with _lock:
            with _AUDIT_PATH.open("a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception:
        pass


def log_routing_event(
    prompt_hash: str,
    adapter_id: str,
    confidence: float,
    fallback: bool,
    rationale: Dict[str, Any],
    phase: str = "routing",
    version: str = "v1",
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    rec = {
        "type": "routing_event",
        "phase": phase,
        "prompt_hash": prompt_hash,
        "adapter_id": adapter_id,
        "confidence": confidence,
        "fallback": fallback,
        "rationale": rationale,
        "version": version,
    }
    if extra:
        rec.update(extra)
    _write(rec)


def log_serving_event(
    adapter_id: Optional[str],
    tokens: int,
    latency: float,
    routed: bool,
    confidence: Optional[float] = None,
    fallback: Optional[bool] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    rec = {
        "type": "serving_event",
        "adapter_id": adapter_id,
        "tokens": tokens,
        "latency": latency,
        "routed": routed,
        "confidence": confidence,
        "fallback": fallback,
    }
    if extra:
        rec.update(extra)
    _write(rec)

__all__ = ["log_routing_event", "log_serving_event"]
