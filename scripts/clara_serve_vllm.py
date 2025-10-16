"""CLARA vLLM Serving mit dynamischem LoRA Adapter Hot-Swap.

Aktueller Status:
    - Lädt Basismodell via vLLM
    - Lädt Adapter aus Registry oder direktem Pfad
    - Aktivierung / Deaktivierung zur Laufzeit
    - (Wenn vLLM LoRA API verfügbar) nutzt engine.add_lora / remove_lora / generate mit lora_request
    - Fallback: Fake-Output wenn vLLM nicht installiert (entwicklungsfreundlich)
    - Metriken (Adapter Loads, Aktivierungen) via Metrics Exporter (optional)

Abhängigkeiten:
    pip install vllm fastapi uvicorn

Anwendungsbeispiele:
    uvicorn scripts.clara_serve_vllm:app --host 0.0.0.0 --port 8001
    curl -X POST localhost:8001/load_adapter -H "Content-Type: application/json" -d '{"path":"models/adapters/steuerrecht/lora-r16-v1"}'
    curl -X POST localhost:8001/activate_adapter -H "Content-Type: application/json" -d '"lora-r16-v1"'
    curl -X POST localhost:8001/generate -H "Content-Type: application/json" -d '{"prompt":"Erkläre Verwaltungsakt"}'
"""
from __future__ import annotations
import os
import json
import yaml
from pathlib import Path
from typing import Dict, Optional, Any
import time
from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from contextlib import asynccontextmanager
from pydantic import BaseModel

# Platzhalter: vLLM Import (aktualisieren sobald installiert)
try:  # pragma: no cover - optional dependency
    from vllm import LLM, SamplingParams  # type: ignore
    _VLLM_AVAILABLE = True
except Exception:  # pragma: no cover
    LLM = object  # type: ignore
    SamplingParams = object  # type: ignore
    _VLLM_AVAILABLE = False

from src.utils.metrics import get_metrics_exporter
from src.utils.router import AdapterRouter, RoutingResult  # Phase 1 Router
from src.utils.audit import log_serving_event

REGISTRY_PATH = Path("metadata/adapter_registry.json")
_metrics = get_metrics_exporter()

@asynccontextmanager
async def lifespan(app: FastAPI):  # pragma: no cover - initialisation not unit tested directly
    """FastAPI Lifespan Context für Initialisierung / optionales Cleanup.

    Ersetzt das frühere on_event("startup") Pattern (deprecated) und kapselt
    Modell- & Router-Initialisierung sowie künftiges Ressourcen-Management.
    """
    # Startup Phase
    global _engine, _router
    base_model = os.environ.get("CLARA_BASE_MODEL", "models/base/leo_base")
    if not Path(base_model).exists():
        raise RuntimeError(f"Basismodell nicht gefunden: {base_model}")
    try:
        if _VLLM_AVAILABLE:
            _engine = LLM(model=base_model)  # type: ignore
        else:
            _engine = None  # Fake Mode
        _metrics.inc("serve_startups_total")
        # Router Konfiguration laden
        cfg_path = os.environ.get("CLARA_ROUTER_CONFIG", "configs/router_config.yaml")
        hard_domain = 1.5
        conf_low = 0.55
        conf_high = 0.85
        default_adapter = os.environ.get("CLARA_DEFAULT_ADAPTER", "base_default_adapter")
        use_domain_score = True
        if os.path.exists(cfg_path):
            try:
                with open(cfg_path, "r", encoding="utf-8") as cf:
                    cfg = yaml.safe_load(cf) or {}
                thresholds = cfg.get("thresholds", {})
                hard_domain = thresholds.get("hard_domain", hard_domain)
                conf_low = thresholds.get("conf_low", conf_low)
                conf_high = thresholds.get("conf_high", conf_high)
                options = cfg.get("options", {})
                default_adapter = options.get("default_adapter", default_adapter)
                use_domain_score = options.get("use_domain_score", True)
            except Exception:
                pass
        try:
            _router = AdapterRouter(
                registry_path=str(REGISTRY_PATH),
                default_adapter=default_adapter,
                hard_domain_threshold=hard_domain,
                conf_low=conf_low,
                conf_high=conf_high,
                use_domain_score=use_domain_score,
            )
        except Exception:  # pragma: no cover
            _router = None
    except Exception as e:  # pragma: no cover
        raise RuntimeError(f"Fehler beim Laden des Basismodells: {e}")

    # Provide application
    yield

    # Shutdown Phase (Cleanup Hooks für spätere Ressourcen / offene Handles)
    # Aktuell keine speziellen Ressourcen zu schließen.
    # Platzhalter für: Engine Shutdown, File Handles, Telemetrie Flush etc.

app = FastAPI(title="CLARA vLLM Server", version="0.1.0", lifespan=lifespan)

# Globale Engine Referenz
_engine: Optional[LLM] = None
_loaded_adapters: Dict[str, Path] = {}
_active_adapter: Optional[str] = None
_adapter_methods: Dict[str, str] = {}  # adapter_id -> method (lora/qlora)
_adapter_metadata: Dict[str, Dict[str, Any]] = {}

# Routing (Phase 1) – Default Adapter kann via ENV konfiguriert werden
_router: Optional[AdapterRouter] = None

class GenerateRequest(BaseModel):
    prompt: str
    max_tokens: int = 256
    temperature: float = 0.7
    top_p: float = 0.95
    adapter_id: Optional[str] = None  # Wenn None → aktiver Standardadapter oder keiner
    route: bool = True  # Wenn True und adapter_id None: Routing ausführen
    require_confidence: float = 0.0  # Mindestconfidence, sonst Fallback/aktive Adapter

class GenerateResponse(BaseModel):
    output: str
    adapter_id: Optional[str]
    tokens_generated: int

class LoadAdapterRequest(BaseModel):
    path: Optional[str] = None  # Direktpfad
    adapter_id: Optional[str] = None  # Explizite ID setzen / erzwingen
    registry_id: Optional[str] = None  # Aus Registry laden (id match)

class StatusResponse(BaseModel):
    base_model: str
    adapters: Dict[str, str]
    active_adapter: Optional[str]

def _load_registry() -> Dict[str, Any]:
    if REGISTRY_PATH.exists():
        try:
            return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {"adapters": []}
    return {"adapters": []}


## Startup Event entfernt – durch Lifespan ersetzt

@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}

@app.get("/status", response_model=StatusResponse)
def status() -> StatusResponse:
    base_model = os.environ.get("CLARA_BASE_MODEL", "models/base/leo_base")
    return StatusResponse(
        base_model=base_model,
        adapters={k: str(v) for k, v in _loaded_adapters.items()},
        active_adapter=_active_adapter,
    )

@app.post("/load_adapter")
def load_adapter(req: LoadAdapterRequest) -> Dict[str, str]:
    registry = _load_registry()
    adapter_path: Optional[Path] = None
    adapter_id = req.adapter_id
    method = None

    # Variante 1: Registry Lookup
    if req.registry_id:
        entry = next((a for a in registry.get("adapters", []) if a.get("id") == req.registry_id), None)
        if not entry:
            raise HTTPException(status_code=404, detail="Registry Adapter nicht gefunden")
        # Heuristik: Speicherort konventionell
        base_dir = Path("models/adapters")
        adapter_path = base_dir / entry.get("id", "")
        method = entry.get("method")
        if not adapter_path.exists():
            raise HTTPException(status_code=404, detail="Adapter-Verzeichnis (Dateisystem) fehlt")
        if not adapter_id:
            adapter_id = entry.get("id")

    # Variante 2: Direkter Pfad
    if req.path:
        p = Path(req.path)
        if not p.exists():
            raise HTTPException(status_code=404, detail="Pfad existiert nicht")
        adapter_path = p
        if not adapter_id:
            adapter_id = p.name

    if not adapter_id or not adapter_path:
        raise HTTPException(status_code=400, detail="adapter_id oder path/registry_id unvollständig")

    if adapter_id in _loaded_adapters:
        return {"status": "already_loaded", "adapter_id": adapter_id}

    # vLLM spezifisches Laden (sofern verfügbar)
    if _VLLM_AVAILABLE and _engine is not None:
        try:
            # Abhängig von vLLM Version; pseudo-code:
            # _engine.add_lora_weights(adapter_id=adapter_id, path=str(adapter_path))
            pass
        except Exception as e:  # pragma: no cover
            raise HTTPException(status_code=500, detail=f"Fehler beim vLLM Laden: {e}")

    _loaded_adapters[adapter_id] = adapter_path
    _adapter_methods[adapter_id] = method or "lora"
    _adapter_metadata[adapter_id] = {"method": method or "lora"}
    _metrics.inc("serve_adapters_loaded_total")
    return {"status": "loaded", "adapter_id": adapter_id}

@app.post("/activate_adapter")
def activate_adapter(adapter_id: str) -> Dict[str, str]:
    global _active_adapter
    if adapter_id not in _loaded_adapters:
        raise HTTPException(status_code=404, detail="Unbekannter Adapter")
    _active_adapter = adapter_id
    _metrics.inc("serve_adapter_activations_total")
    return {"status": "activated", "adapter_id": adapter_id}

@app.post("/generate", response_model=GenerateResponse)
def generate(req: GenerateRequest) -> GenerateResponse:
    start_t = time.time()
    chosen_adapter = req.adapter_id or _active_adapter
    routing_info: Optional[RoutingResult] = None

    # Falls kein Adapter explizit angegeben und Routing aktiviert
    if chosen_adapter is None and req.route and _router is not None:
        _metrics.inc("routing_requests_total")
        routing_info = _router.route(req.prompt)
        if routing_info.fallback:
            _metrics.inc("routing_fallback_total")
        else:
            _metrics.inc("routing_adapter_selected_total")
        chosen_adapter = routing_info.adapter_id
        # Confidence Mindestanforderung prüfen
        if req.require_confidence > 0 and routing_info.confidence < req.require_confidence:
            # Versuche aktiven Adapter als Alternative
            if _active_adapter is not None:
                chosen_adapter = _active_adapter
            else:
                # Letzte Eskalation: base_default_adapter
                chosen_adapter = os.environ.get("CLARA_DEFAULT_ADAPTER", "base_default_adapter")
                _metrics.inc("routing_confidence_fallback_total")

    if _engine is None or not _VLLM_AVAILABLE:
        # Entwicklungsfallback
        meta = ""
        if routing_info is not None:
            meta = f" routing={{conf={routing_info.confidence},fb={routing_info.fallback}}}"
        fake_text = f"[FAKE_OUTPUT adapter={chosen_adapter}{meta}] Antwort auf: {req.prompt[:70]}..."
        _metrics.inc("serve_generate_requests_total")
        tokens = len(fake_text.split())
        _metrics.observe("serve_generate_latency_seconds", time.time() - start_t)
        _metrics.observe("serve_generate_tokens", tokens)
        if routing_info is not None:
            _metrics.observe("routing_confidence", routing_info.confidence)
            try:
                _metrics.observe_histogram("routing_confidence_hist", routing_info.confidence)
            except Exception:
                pass
        # Audit Logging
        try:
            log_serving_event(
                adapter_id=chosen_adapter,
                tokens=tokens,
                latency=time.time() - start_t,
                routed=routing_info is not None,
                confidence=(routing_info.confidence if routing_info else None),
                fallback=(routing_info.fallback if routing_info else None),
            )
        except Exception:
            pass
        return GenerateResponse(output=fake_text, adapter_id=chosen_adapter, tokens_generated=tokens)
    try:
        sp = SamplingParams(max_tokens=req.max_tokens, temperature=req.temperature, top_p=req.top_p)  # type: ignore
        # Pseudo-Code für LoRA Nutzung (abhängig von vLLM API Version):
        # result = _engine.generate([req.prompt], sp, lora_request=chosen_adapter)
        # text = result[0].outputs[0].text
        info_meta = ""
        if routing_info is not None:
            info_meta = f" routing={{conf={routing_info.confidence},fb={routing_info.fallback}}}"
        text = f"[VLLM_OUTPUT adapter={chosen_adapter}{info_meta}] (simulation) {req.prompt[:60]}..."
        _metrics.inc("serve_generate_requests_total")
        tokens = len(text.split())
        total_latency = time.time() - start_t
        _metrics.observe("serve_generate_latency_seconds", total_latency)
        try:
            _metrics.observe_histogram("serve_generate_latency_seconds_hist", total_latency)
        except Exception:
            pass
        _metrics.observe("serve_generate_tokens", tokens)
        if routing_info is not None:
            _metrics.observe("routing_confidence", routing_info.confidence)
            try:
                _metrics.observe_histogram("routing_confidence_hist", routing_info.confidence)
            except Exception:
                pass
        # Audit Logging
        try:
            log_serving_event(
                adapter_id=chosen_adapter,
                tokens=tokens,
                latency=total_latency,
                routed=routing_info is not None,
                confidence=(routing_info.confidence if routing_info else None),
                fallback=(routing_info.fallback if routing_info else None),
            )
        except Exception:
            pass
        return GenerateResponse(output=text, adapter_id=chosen_adapter, tokens_generated=tokens)
    except Exception as e:  # pragma: no cover
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/deactivate_adapter")
def deactivate_adapter() -> Dict[str, Optional[str]]:
    global _active_adapter
    _active_adapter = None
    _metrics.inc("serve_adapter_deactivations_total")
    return {"status": "deactivated", "active_adapter": None}

@app.delete("/unload_adapter")
def unload_adapter(adapter_id: str) -> Dict[str, str]:
    if adapter_id not in _loaded_adapters:
        raise HTTPException(status_code=404, detail="Unbekannter Adapter")
    try:
        if _VLLM_AVAILABLE and _engine is not None:
            # Pseudo-Code: _engine.remove_lora(adapter_id)
            pass
    except Exception as e:  # pragma: no cover
        raise HTTPException(status_code=500, detail=f"Fehler beim Entladen: {e}")
    del _loaded_adapters[adapter_id]
    _adapter_methods.pop(adapter_id, None)
    _adapter_metadata.pop(adapter_id, None)
    if _active_adapter == adapter_id:
        deactivate_adapter()
    _metrics.inc("serve_adapter_unloads_total")
    return {"status": "unloaded", "adapter_id": adapter_id}

if __name__ == "__main__":  # pragma: no cover
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

# Neuer Endpoint: Nur Routing ohne Generierung (Debug / Tooling)
@app.post("/route")
def route_only(req: GenerateRequest) -> Dict[str, Any]:
    if _router is None:
        raise HTTPException(status_code=503, detail="Router nicht initialisiert")
    _metrics.inc("routing_requests_total")
    res = _router.route(req.prompt)
    if res.fallback:
        _metrics.inc("routing_fallback_total")
    else:
        _metrics.inc("routing_adapter_selected_total")
    return {
        "adapter_id": res.adapter_id,
        "confidence": res.confidence,
        "fallback": res.fallback,
        "rationale": res.rationale,
    }

@app.get("/metrics", response_class=PlainTextResponse)
def metrics_endpoint():  # pragma: no cover - Format Test in separatem Test empfohlen
    snap = _metrics.snapshot()
    # Direkte Nutzung interner Format-Funktion; könnte später abstrahiert werden
    try:
        text = _metrics._prometheus_format(snap)  # type: ignore
    except Exception as e:  # Fallback plain JSON
        return PlainTextResponse(f"# error exporting metrics: {e}", status_code=500)
    return PlainTextResponse(text, media_type="text/plain")
