import json
import os
from pathlib import Path

from src.utils.router import AdapterRouter


def build_registry(tmp_path: Path):
    data = {
        "adapters": [
            {"id": "adapter_a", "domain": ["alpha"], "metrics": {"domain_score": 0.5}},
            {"id": "adapter_b", "domain": ["beta"], "metrics": {"domain_score": 0.5}},
        ]
    }
    reg = tmp_path / "adapter_registry.json"
    reg.write_text(json.dumps(data), encoding="utf-8")
    return reg


def test_exploration_path(tmp_path, monkeypatch):
    reg = build_registry(tmp_path)
    # Erzwinge Exploration mit epsilon=1.0
    monkeypatch.setenv("CLARA_ROUTER_ENABLE_EXPLORATION", "1")
    monkeypatch.setenv("CLARA_ROUTER_EPSILON_START", "1.0")
    monkeypatch.setenv("CLARA_ROUTER_EPSILON_MIN", "1.0")
    router = AdapterRouter(registry_path=str(reg), enable_embeddings=False)

    # Prompt enthält beide Domain Tokens -> Scores nahe beieinander => Graubereich
    res = router.route("Alpha Beta Test Anfrage")
    assert res.rationale.get("exploration") is True
    assert res.rationale.get("epsilon") == 1.0
    # Adapter sollte einer der beiden sein
    assert res.adapter_id in ("adapter_a", "adapter_b")
