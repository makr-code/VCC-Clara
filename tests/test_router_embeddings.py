import json
import os
from pathlib import Path

from src.utils.router import AdapterRouter


def build_registry(tmp_path: Path):
    data = {
        "adapters": [
            {"id": "steuerrecht-lora", "domain": ["steuerrecht"], "metrics": {"domain_score": 0.8}},
            {"id": "datenschutz-lora", "domain": ["datenschutz"], "metrics": {"domain_score": 0.7}},
        ]
    }
    reg = tmp_path / "adapter_registry.json"
    reg.write_text(json.dumps(data), encoding="utf-8")
    return reg


def test_embedding_similarity_activation(tmp_path, monkeypatch):
    reg = build_registry(tmp_path)
    # Force enable embeddings but monkeypatch backend to deterministic small dummy
    from src.utils import embeddings as emb_mod
    class SmallDummy(emb_mod.DummyEmbeddingBackend):
        def __init__(self):
            super().__init__(dim=8)
    monkeypatch.setenv("CLARA_ROUTER_ENABLE_EMBEDDINGS", "1")
    router = AdapterRouter(registry_path=str(reg), enable_embeddings=True, embedding_backend=SmallDummy())
    res = router.route("Frage zum Datenschutz und Verarbeitung personenbezogener Daten")
    # Sollte einer der definierten Adapter oder eine statische Regel sein (privacy_compliance_lora aufgrund Keywords)
    assert res.adapter_id in ("steuerrecht-lora", "datenschutz-lora", "privacy_compliance_lora")
    # Embedding Flag & Sim vorhanden
    assert res.rationale.get("details", {}).get("embedding_sim") is not None or res.rationale.get("embedding_used") or res.rationale.get("details", {}).get("combined_score") is not None


def test_embedding_disabled_fallback_to_heuristic(tmp_path, monkeypatch):
    reg = build_registry(tmp_path)
    monkeypatch.delenv("CLARA_ROUTER_ENABLE_EMBEDDINGS", raising=False)
    router = AdapterRouter(registry_path=str(reg), enable_embeddings=False)
    res = router.route("Frage zum Steuerrecht")
    assert res.adapter_id.startswith("steuerrecht") or res.fallback is False
    # Keine Embedding Felder erwartet
    assert not res.rationale.get("details", {}).get("embedding_sim")
