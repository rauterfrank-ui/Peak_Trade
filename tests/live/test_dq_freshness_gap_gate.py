"""Tests for Data Quality Freshness/Gap Hard Gate."""

from __future__ import annotations


def test_dq_gate_fails_closed_when_monitors_unavailable(monkeypatch):
    """When both quality_monitor and run_live_quality_checks unavailable → FAIL."""
    import importlib

    # Force run_live_quality_checks import to fail (QualityMonitor doesn't exist)
    import src.data.shadow.live_quality_checks as lqc

    monkeypatch.delattr(lqc, "run_live_quality_checks", raising=False)

    mod = importlib.import_module("src.live.data_quality_gate")
    d = mod.evaluate_data_quality(asof_utc="2026-02-19T00:00:00Z", context={})

    assert d.gate_id == "dq_freshness_gap"
    assert d.status == "FAIL"
    assert "quality_monitor_unavailable" in d.reasons
    assert "live_quality_checks_unavailable" in d.reasons


def test_dq_gate_passes_if_live_checks_ok(monkeypatch):
    """When run_live_quality_checks exists and returns True → PASS."""
    monkeypatch.setattr(
        "src.data.shadow.live_quality_checks.run_live_quality_checks",
        lambda *, asof_utc, context: (True, {"asof_utc": asof_utc}),
    )

    import importlib

    mod = importlib.import_module("src.live.data_quality_gate")
    d = mod.evaluate_data_quality(asof_utc="2026-02-19T00:00:00Z", context={})
    assert d.status == "PASS"
