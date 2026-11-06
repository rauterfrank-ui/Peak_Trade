"""Unit tests for ``build_evidence_audit_observation`` (cockpit aggregate only)."""

from __future__ import annotations

from typing import Any, Dict

from src.ops.evidence_audit_observation import (
    READER_SCHEMA_VERSION,
    build_evidence_audit_observation,
)


def _evidence(**over: Any) -> Dict[str, Any]:
    base = {
        "summary": "ok",
        "freshness_status": "ok",
        "audit_trail": "intact",
        "last_verified_utc": "unknown",
        "source_freshness": {"fresh": 1, "stale": 0, "older": 0},
    }
    base.update(over)
    return base


def test_nominal_ok_snapshot() -> None:
    out = build_evidence_audit_observation(evidence_state=_evidence())
    assert out["status"] == "nominal"
    assert out["data_source"] == "cockpit_payload_aggregate"
    assert out["reader_schema_version"] == READER_SCHEMA_VERSION
    assert "health_drift_observation" in out["summary"]


def test_degraded_audit_broken() -> None:
    out = build_evidence_audit_observation(
        evidence_state=_evidence(audit_trail="broken"),
    )
    assert out["status"] == "degraded"


def test_degraded_freshness_critical() -> None:
    out = build_evidence_audit_observation(
        evidence_state=_evidence(freshness_status="critical"),
    )
    assert out["status"] == "degraded"


def test_degraded_summary_stale() -> None:
    out = build_evidence_audit_observation(
        evidence_state=_evidence(summary="stale"),
    )
    assert out["status"] == "degraded"


def test_caution_partial_summary() -> None:
    out = build_evidence_audit_observation(
        evidence_state=_evidence(summary="partial"),
    )
    assert out["status"] == "caution"


def test_caution_telemetry_evidence_warn() -> None:
    ev = _evidence()
    ev["telemetry_evidence"] = "warn"
    out = build_evidence_audit_observation(evidence_state=ev)
    assert out["status"] == "caution"


def test_caution_stale_dominant_source_freshness() -> None:
    out = build_evidence_audit_observation(
        evidence_state=_evidence(
            source_freshness={"fresh": 0, "stale": 3, "older": 0},
        ),
    )
    assert out["status"] == "caution"


def test_unknown_missing_evidence() -> None:
    out = build_evidence_audit_observation(
        evidence_state=None,  # type: ignore[arg-type]
    )
    assert out["status"] == "unknown"


def test_freshness_top_level_mismatch_note() -> None:
    out = build_evidence_audit_observation(
        evidence_state=_evidence(freshness_status="ok"),
        freshness_status="warn",
    )
    notes = out.get("consistency_notes") or []
    assert any("freshness_status" in n for n in notes)
