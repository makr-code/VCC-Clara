from pathlib import Path
import json
from src.utils.router import AdapterRouter
from src.utils.metrics import get_metrics_exporter

def test_router_records_latency_and_confidence(tmp_path):
    # Temporäre Registry mit einem Adapter
    reg_dir = tmp_path / "metadata"
    reg_dir.mkdir()
    (reg_dir / "adapter_registry.json").write_text(
        json.dumps({"adapters": [{"id": "steuerrecht-lora", "domain": ["steuerrecht"], "method": "lora", "base_model_hash": "x", "created": "x", "dataset_ref": "d", "metrics": {"domain_score": 0.7, "ppl_dev": 7.0}, "adapter_checksum": "y"}]}),
        encoding="utf-8",
    )
    router = AdapterRouter(registry_path=str(reg_dir / "adapter_registry.json"))
    exp = get_metrics_exporter()
    before = exp.snapshot()
    router.route("Frage zum Steuerrecht und mehr")
    after = exp.snapshot()
    # Prüfe, dass Observes zugenommen haben
    assert after["summaries"].get("routing_decision_seconds", {}).get("count", 0) >= before["summaries"].get("routing_decision_seconds", {}).get("count", 0) + 1
    assert after["summaries"].get("routing_confidence", {}).get("count", 0) >= before["summaries"].get("routing_confidence", {}).get("count", 0) + 1
