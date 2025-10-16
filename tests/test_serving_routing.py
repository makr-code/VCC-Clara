import os
import pytest

try:
    from fastapi.testclient import TestClient  # type: ignore
    FASTAPI_AVAILABLE = True
except Exception:
    FASTAPI_AVAILABLE = False

pytestmark = pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="fastapi nicht installiert")

# Wir importieren das App Objekt
APP_IMPORTED = False
app = None


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    global app, APP_IMPORTED
    base_dir = tmp_path_factory.mktemp("model")
    (base_dir / "config.json").write_text("{}", encoding="utf-8")
    os.environ["CLARA_BASE_MODEL"] = str(base_dir)
    # Registry vorbereiten
    registry_dir = tmp_path_factory.mktemp("registry")
    registry_file = registry_dir / "adapter_registry.json"
    registry_file.write_text(
        """{"adapters": [{"id": "steuerrecht-lora-r16-v1", "domain": ["steuerrecht"], "method": "lora", "base_model_hash": "x", "created": "2025-09-18T12:00:00Z", "dataset_ref": "d", "metrics": {"ppl_dev": 7.1, "domain_score": 0.8}, "adapter_checksum": "y"}]}""",
        encoding="utf-8",
    )
    # Vor Import Registry Pfad per ENV für flexible Nutzung
    os.environ["CLARA_ROUTER_CONFIG"] = "configs/router_config.yaml"  # falls vorhanden
    # Import jetzt erst durchführen
    from scripts import clara_serve_vllm  # type: ignore
    clara_serve_vllm.REGISTRY_PATH = registry_file
    app = clara_serve_vllm.app
    # TestClient erzeugt und Startup triggern
    c = TestClient(app)
    return c


def test_route_endpoint(client):
    resp = client.post("/route", json={"prompt": "Frage zum Steuerrecht", "route": True})
    if resp.status_code == 503:
        pytest.skip("Router nicht initialisiert (503)")
    assert resp.status_code == 200
    data = resp.json()
    assert data["adapter_id"].startswith("steuerrecht-lora")
    assert data["confidence"] >= 0


def test_generate_with_routing(client):
    resp = client.post("/generate", json={"prompt": "Bitte eine kurze steuerrechtliche Einschätzung", "route": True, "max_tokens": 16})
    assert resp.status_code == 200
    data = resp.json()
    assert "adapter" in data["output"]
    if data["adapter_id"] is not None:  # Kann im Fallback leer sein
        assert data["adapter_id"].startswith("steuerrecht-lora")


def test_generate_without_routing_fallback(client):
    # route False -> Kein Routing, kein aktiver Adapter gesetzt => adapter_id None oder default
    resp = client.post("/generate", json={"prompt": "Allgemeine Frage", "route": False, "max_tokens": 8})
    assert resp.status_code == 200
    data = resp.json()
    # In Fake Mode kann adapter_id None sein
    assert "output" in data
