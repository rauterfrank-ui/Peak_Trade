"""Unit tests for ``build_health_drift_observation`` (cockpit aggregate only)."""

from __future__ import annotations

from typing import Any, Dict

from src.ops.health_drift_observation import (
    READER_SCHEMA_VERSION,
    build_health_drift_observation,
)


def _base(**over: Any) -> Dict[str, Any]:
    evidence_state: Dict[str, Any] = {
        "summary": "ok",
        "freshness_status": "ok",
        "audit_trail": "intact",
        "last_verified_utc": "2026-01-01T00:00:00+00:00",
    }
    dependencies_state: Dict[str, Any] = {
        "summary": "ok",
        "telemetry": "ok",
        "exchange": "ok",
        "degraded": [],
    }
    stale_state: Dict[str, Any] = {
        "summary": "ok",
        "balance": "ok",
        "position": "ok",
        "order": "ok",
        "exposure": "ok",
    }
    base = {
        "truth_status": "ok",
        "freshness_status": "ok",
        "source_coverage_status": "ok",
        "critical_flags": [],
        "unknown_flags": [],
        "evidence_state": evidence_state,
        "dependencies_state": dependencies_state,
        "stale_state": stale_state,
    }
    base.update(over)
    return base


def test_nominal() -> None:
    out = build_health_drift_observation(**_base())
    assert out["status"] == "nominal"
    assert out["data_source"] == "cockpit_payload_aggregate"
    assert out["reader_schema_version"] == READER_SCHEMA_VERSION
    assert "guarantee" in out["summary"].lower() or "observation" in out["summary"].lower()


def test_degraded_truth_critical() -> None:
    b = _base(truth_status="critical")
    out = build_health_drift_observation(**b)
    assert out["status"] == "degraded"


def test_degraded_stale_summary() -> None:
    b = _base()
    b["stale_state"]["summary"] = "stale"
    out = build_health_drift_observation(**b)
    assert out["status"] == "degraded"


def test_degraded_dependencies_degraded() -> None:
    b = _base()
    b["dependencies_state"]["summary"] = "degraded"
    out = build_health_drift_observation(**b)
    assert out["status"] == "degraded"


def test_degraded_audit_broken() -> None:
    b = _base()
    b["evidence_state"]["audit_trail"] = "broken"
    out = build_health_drift_observation(**b)
    assert out["status"] == "degraded"


def test_caution_truth_warn() -> None:
    b = _base(truth_status="warn")
    out = build_health_drift_observation(**b)
    assert out["status"] == "caution"


def test_caution_critical_flags() -> None:
    b = _base(critical_flags=["stale_sources"])
    out = build_health_drift_observation(**b)
    assert out["status"] == "caution"


def test_degraded_priority_over_caution() -> None:
    b = _base()
    b["truth_status"] = "critical"
    b["critical_flags"] = ["stale_sources"]
    out = build_health_drift_observation(**b)
    assert out["status"] == "degraded"


def test_unknown_missing_evidence() -> None:
    out = build_health_drift_observation(
        truth_status="ok",
        freshness_status="ok",
        source_coverage_status="ok",
        critical_flags=[],
        unknown_flags=[],
        evidence_state=None,  # type: ignore[arg-type]
        dependencies_state=_base()["dependencies_state"],
        stale_state=_base()["stale_state"],
    )
    assert out["status"] == "unknown"


def test_consistency_note_nested_mismatch() -> None:
    b = _base()
    b["executive_summary"] = {
        "truth_status": {"level": "warn", "label": "x", "detail": "y"},
        "freshness_status": {"level": "ok", "label": "a", "detail": "b"},
    }
    out = build_health_drift_observation(**b)
    notes = out.get("consistency_notes") or []
    assert any("executive_summary.truth_status" in n for n in notes)
