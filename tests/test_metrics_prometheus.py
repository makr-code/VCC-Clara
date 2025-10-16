from src.utils.metrics import get_metrics_exporter


def test_prometheus_format_basic():
    exp = get_metrics_exporter()
    exp.inc("routing_requests_total")
    exp.observe("routing_decision_seconds", 0.012)
    exp.observe_histogram("routing_decision_seconds_hist", 0.012, buckets=[0.01,0.02,0.05])
    snap = exp.snapshot()
    text = exp._prometheus_format(snap)  # type: ignore
    assert "clara_routing_requests_total" in text
    assert "clara_routing_decision_seconds_sum" in text
    assert "clara_routing_decision_seconds_hist_bucket" in text
