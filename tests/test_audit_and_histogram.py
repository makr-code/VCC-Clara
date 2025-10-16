import json
import os
from pathlib import Path

import pytest

from src.utils.router import AdapterRouter
from src.utils.metrics import get_metrics_exporter

# Audit Logging import optional falls fehlende Module ignorieren
try:
    from src.utils.audit import _AUDIT_PATH  # type: ignore
except Exception:  # pragma: no cover
    _AUDIT_PATH = Path("audit/audit_log.jsonl")


def test_routing_audit_and_histogram(tmp_path):
    # Registry vorbereiten
    reg_dir = tmp_path / "metadata"
    reg_dir.mkdir()
    (reg_dir / "adapter_registry.json").write_text(
        json.dumps({
            "adapters": [
                {"id": "steuerrecht-lora", "domain": ["steuerrecht"], "method": "lora", "base_model_hash": "x", "created": "t", "dataset_ref": "d", "metrics": {"domain_score": 0.9, "ppl_dev": 6.5}, "adapter_checksum": "c"}
            ]
        }),
        encoding="utf-8",
    )

    # Setze Audit Pfad in temporäres Verzeichnis
    audit_dir = tmp_path / "audit"
    audit_dir.mkdir()
    audit_file = audit_dir / "audit_log.jsonl"
    # Monkeypatch global Pfad falls vorhanden
    import src.utils.audit as audit_mod  # type: ignore
    audit_mod._AUDIT_PATH = audit_file  # type: ignore

    router = AdapterRouter(registry_path=str(reg_dir / "adapter_registry.json"))
    exp = get_metrics_exporter()
    before_snap = exp.snapshot()

    router.route("Frage zum Steuerrecht")

    after_snap = exp.snapshot()

    # Histogram Einträge sollten zugenommen haben
    hist_latency_after = after_snap["histograms"].get("routing_decision_seconds_hist", {})
    assert hist_latency_after.get("count", 0) >= 1

    hist_conf_after = after_snap["histograms"].get("routing_confidence_hist", {})
    assert hist_conf_after.get("count", 0) >= 1

    # Audit Datei existiert und enthält mindestens einen Eintrag
    assert audit_file.exists()
    lines = audit_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) >= 1
    rec = json.loads(lines[0])
    assert rec.get("type") == "routing_event"
    assert rec.get("adapter_id").startswith("steuerrecht-lora")


@pytest.mark.skipif("FASTAPI_SKIP_SERVING_TEST" in os.environ, reason="Serving Audit Test übersprungen via ENV")
def test_serving_audit_histogram_fake_mode(tmp_path):
    # Fake Mode generiert nur Audit Eintrag bei generate
    # Setup minimaler Basismodelpfad
    model_dir = tmp_path / "model"
    model_dir.mkdir()
    (model_dir / "config.json").write_text("{}", encoding="utf-8")
    os.environ["CLARA_BASE_MODEL"] = str(model_dir)

    # Registry + Pfad patchen
    reg_dir = tmp_path / "metadata"
    reg_dir.mkdir()
    reg_file = reg_dir / "adapter_registry.json"
    reg_file.write_text(json.dumps({"adapters": []}), encoding="utf-8")

    # Audit Datei temporär
    audit_dir = tmp_path / "audit"
    audit_dir.mkdir()
    audit_file = audit_dir / "audit_log.jsonl"
    import src.utils.audit as audit_mod  # type: ignore
    audit_mod._AUDIT_PATH = audit_file  # type: ignore

    try:
        from scripts import clara_serve_vllm as serve_mod  # type: ignore
    except Exception:
        pytest.skip("Serving Modul nicht importierbar")

    serve_mod.REGISTRY_PATH = reg_file  # type: ignore

    # TestClient nur falls fastapi verfügbar
    try:
        from fastapi.testclient import TestClient  # type: ignore
    except Exception:
        pytest.skip("fastapi fehlt")

    client = TestClient(serve_mod.app)

    resp = client.post("/generate", json={"prompt": "Hallo Welt", "route": False})
    assert resp.status_code == 200

    # Audit Eintrag vorhanden
    if audit_file.exists():
        lines = audit_file.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) >= 1
        last = json.loads(lines[-1])
        assert last.get("type") == "serving_event"
