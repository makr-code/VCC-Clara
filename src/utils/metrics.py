"""CLARA Metrics Exporter (leichtgewichtig)

Funktionen:
  - Counter: inc(name, value)
  - Gauge: set(name, value)
  - Summary-artig: observe(name, value) (count,sum,min,max,avg)
  - JSONL Event Log unter metrics/metrics.jsonl
  - Optional Prometheus kompatibler Endpoint (/metrics)

Thread-sicher, keine externen Dependencies.
"""
from __future__ import annotations
import json
import threading
import time
from pathlib import Path
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Dict, Any, Optional


class MetricsExporter:
    def __init__(self, jsonl_path: str = "metrics/metrics.jsonl", flush_interval: float = 10.0):
        self.path = Path(jsonl_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._counters: Dict[str, float] = {}
        self._gauges: Dict[str, float] = {}
        self._summaries: Dict[str, Dict[str, float]] = {}
        self._histograms: Dict[str, Dict[str, Any]] = {}
        self._running = True
        self._flush_thread = threading.Thread(target=self._flush_loop, daemon=True)
        self._flush_thread.start()
        self._http_server: Optional[HTTPServer] = None
        self._http_thread: Optional[threading.Thread] = None

    # ---------------- Primitive APIs ----------------
    def inc(self, name: str, value: float = 1.0):
        with self._lock:
            self._counters[name] = self._counters.get(name, 0.0) + value
            self._write_event({"type": "counter", "name": name, "delta": value})

    def set(self, name: str, value: float):
        with self._lock:
            self._gauges[name] = value
            self._write_event({"type": "gauge", "name": name, "value": value})

    def observe(self, name: str, value: float):
        with self._lock:
            s = self._summaries.setdefault(name, {"count": 0.0, "sum": 0.0, "min": value, "max": value})
            s["count"] += 1
            s["sum"] += value
            if value < s["min"]:
                s["min"] = value
            if value > s["max"]:
                s["max"] = value
            self._write_event({"type": "observe", "name": name, "value": value})
    def observe_histogram(self, name: str, value: float, buckets: Optional[list[float]] = None):
        if buckets is None:
            buckets = [0.005, 0.01, 0.02, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
        with self._lock:
            h = self._histograms.setdefault(name, {"buckets": buckets, "counts": [0 for _ in buckets], "sum": 0.0, "count": 0})
            # Finde Bucket Index
            for i, b in enumerate(h["buckets"]):
                if value <= b:
                    h["counts"][i] += 1
                    break
            else:
                # Overflow Bucket anhängen falls nötig
                if h["buckets"] and (len(h["counts"]) == len(h["buckets"])):
                    h["buckets"].append(float("inf"))
                    h["counts"].append(0)
                h["counts"][-1] += 1
            h["sum"] += value
            h["count"] += 1
            self._write_event({"type": "histogram", "name": name, "value": value})

    # ---------------- Persistence ----------------
    def _write_event(self, event: Dict[str, Any]):
        event["ts"] = time.time()
        try:
            with self.path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")
        except Exception:
            pass

    def snapshot(self) -> Dict[str, Any]:
        with self._lock:
            summaries = {k: {**v, "avg": (v["sum"] / v["count"]) if v["count"] else 0.0} for k, v in self._summaries.items()}
            return {
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
                "summaries": summaries,
                "histograms": {k: dict(v) for k, v in self._histograms.items()},
                "timestamp": time.time(),
            }

    # ---------------- Flush Loop (Platzhalter) ----------------
    def _flush_loop(self):
        while self._running:
            time.sleep( self._running and 10 or 10)
            # Erweiterbar (Rotation etc.)
            pass

    # ---------------- HTTP Export (Prometheus) ----------------
    def start_http(self, host: str = "0.0.0.0", port: int = 9310):
        if self._http_server:
            return
        exporter = self

        class Handler(BaseHTTPRequestHandler):  # type: ignore
            def do_GET(self_inner):  # noqa: N802
                if self_inner.path not in ("/metrics", "/"):
                    self_inner.send_response(404)
                    self_inner.end_headers()
                    return
                snap = exporter.snapshot()
                text = exporter._prometheus_format(snap)
                data = text.encode()
                self_inner.send_response(200)
                self_inner.send_header("Content-Type", "text/plain; version=0.0.4")
                self_inner.send_header("Content-Length", str(len(data)))
                self_inner.end_headers()
                self_inner.wfile.write(data)
            def log_message(self_inner, *args, **kwargs):  # noqa: A003
                return

        self._http_server = HTTPServer((host, port), Handler)
        self._http_thread = threading.Thread(target=self._http_server.serve_forever, daemon=True)
        self._http_thread.start()
        self._write_event({"type": "info", "msg": f"metrics_http_started:{host}:{port}"})

    def _prometheus_format(self, snap: Dict[str, Any]) -> str:
        lines = []
        for name, val in snap["counters"].items():
            metric = self._sanitize(name)
            lines.append(f"# TYPE clara_{metric} counter")
            lines.append(f"clara_{metric} {val}")
        for name, val in snap["gauges"].items():
            metric = self._sanitize(name)
            lines.append(f"# TYPE clara_{metric} gauge")
            lines.append(f"clara_{metric} {val}")
        for name, stat in snap["summaries"].items():
            metric = self._sanitize(name)
            lines.append(f"# TYPE clara_{metric}_sum gauge")
            lines.append(f"clara_{metric}_sum {stat['sum']}")
            lines.append(f"# TYPE clara_{metric}_count counter")
            lines.append(f"clara_{metric}_count {stat['count']}")
            lines.append(f"# TYPE clara_{metric}_avg gauge")
            lines.append(f"clara_{metric}_avg {stat['avg']}")
        for name, hist in snap.get("histograms", {}).items():
            metric = self._sanitize(name)
            buckets = hist.get("buckets", [])
            counts = hist.get("counts", [])
            cumulative = 0
            for b, c in zip(buckets, counts):
                cumulative += c
                b_label = b if b != float("inf") else "+Inf"
                lines.append(f"clara_{metric}_bucket{{le=\"{b_label}\"}} {cumulative}")
            lines.append(f"clara_{metric}_sum {hist.get('sum', 0.0)}")
            lines.append(f"clara_{metric}_count {hist.get('count', 0)}")
        return "\n".join(lines) + "\n"

    @staticmethod
    def _sanitize(name: str) -> str:
        return name.lower().replace(" ", "_").replace("-", "_")

    def stop(self):
        self._running = False
        if self._http_server:
            try:
                self._http_server.shutdown()
            except Exception:
                pass


_global_exporter: Optional[MetricsExporter] = None


def get_metrics_exporter() -> MetricsExporter:
    global _global_exporter
    if _global_exporter is None:
        _global_exporter = MetricsExporter()
    return _global_exporter
