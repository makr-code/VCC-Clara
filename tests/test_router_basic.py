import json
from pathlib import Path
from src.utils.router import AdapterRouter

REGISTRY_FIXTURE = {
    "_schema_version": "0.2.0",
    "adapters": [
        {
            "id": " steuerrecht-lora-r16-v1 ".strip(),
            "domain": ["steuerrecht"],
            "method": "lora",
            "rank": 16,
            "quantization": None,
            "base_model_hash": "hash-base",
            "created": "2025-09-18T12:00:00Z",
            "dataset_ref": "data/x.jsonl",
            "metrics": {"ppl_dev": 7.1, "domain_score": 0.83},
            "adapter_checksum": "abc",
        },
        {
            "id": "arbeitsrecht-lora-r16-v1",
            "domain": ["arbeitsrecht"],
            "method": "lora",
            "rank": 16,
            "quantization": None,
            "base_model_hash": "hash-base",
            "created": "2025-09-18T12:00:00Z",
            "dataset_ref": "data/y.jsonl",
            "metrics": {"ppl_dev": 6.5, "domain_score": 0.65},
            "adapter_checksum": "def",
        },
    ],
}


def write_registry(tmp_path: Path):
    reg = tmp_path / "metadata"
    reg.mkdir()
    with (reg / "adapter_registry.json").open("w", encoding="utf-8") as f:
        json.dump(REGISTRY_FIXTURE, f)
    return reg / "adapter_registry.json"


def test_router_direct_match(tmp_path):
    registry_path = write_registry(tmp_path)
    router = AdapterRouter(registry_path=registry_path, default_adapter="base-general")
    prompt = "Eine Frage zum Steuerrecht und zur Veranlagung"  # enthält 'steuerrecht'
    result = router.route(prompt)
    assert not result.fallback
    assert "steuerrecht" in result.rationale["details"]["patterns"]
    assert result.adapter_id.startswith("steuerrecht-lora")


def test_router_fallback_no_match(tmp_path):
    registry_path = write_registry(tmp_path)
    router = AdapterRouter(registry_path=registry_path, default_adapter="base-general")
    prompt = "Astronomie und Quantenphysik"  # keine Domain im Fixture
    result = router.route(prompt)
    assert result.fallback
    assert result.adapter_id == "base-general"


def test_low_confidence_triggers_fallback(tmp_path, monkeypatch):
    registry_path = write_registry(tmp_path)
    router = AdapterRouter(registry_path=registry_path, default_adapter="base-general", conf_low=0.9)

    # Prompt mit zwei Domains -> nahe Scores -> geringe Margin -> niedrige Confidence
    # Wichtig: Beide Domains müssen exakt als Token vorkommen, damit der Regex mit Wortgrenzen matched.
    prompt = "Fragen zu Steuerrecht und Arbeitsrecht"  # trifft 'steuerrecht' und 'arbeitsrecht'
    result = router.route(prompt)
    assert result.fallback
    assert result.rationale["reason"] == "low_confidence"


def test_prompt_hash_stable():
    h1 = AdapterRouter.prompt_hash("Test Prompt")
    h2 = AdapterRouter.prompt_hash("Test Prompt")
    assert h1 == h2
    assert len(h1) == 16
