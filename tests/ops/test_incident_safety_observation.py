"""Unit tests for ``build_incident_safety_observation`` (cockpit aggregate only)."""

from __future__ import annotations

from typing import Any, Dict

from src.ops.incident_safety_observation import (
    READER_SCHEMA_VERSION,
    build_incident_safety_observation,
)


def _base(**over: Any) -> Dict[str, Any]:
    incident_state: Dict[str, Any] = {
        "status": "normal",
        "summary": "normal",
        "blocked": False,
        "kill_switch_active": False,
        "degraded": False,
        "requires_operator_attention": False,
        "incident_stop_invoked": False,
        "entry_permitted": True,
        "operator_authoritative_state": "normal",
    }
    dependencies_state: Dict[str, Any] = {
        "summary": "ok",
        "exchange": "ok",
        "telemetry": "ok",
        "degraded": [],
    }
    policy_state: Dict[str, Any] = {"blocked": False, "summary": "ok"}
    operator_state: Dict[str, Any] = {"blocked": False}
    base = {
        "incident_state": incident_state,
        "dependencies_state": dependencies_state,
        "policy_state": policy_state,
        "operator_state": operator_state,
    }
    base.update(over)
    return base


def test_nominal_clear_snapshot() -> None:
    out = build_incident_safety_observation(**_base())
    assert out["status"] == "nominal"
    assert out["data_source"] == "cockpit_payload_aggregate"
    assert out["reader_schema_version"] == READER_SCHEMA_VERSION
    assert "safety_posture_observation" in out["summary"]


def test_degraded_kill_switch() -> None:
    b = _base()
    b["incident_state"]["kill_switch_active"] = True
    out = build_incident_safety_observation(**b)
    assert out["status"] == "degraded"


def test_degraded_dependency_summary() -> None:
    b = _base()
    b["dependencies_state"]["summary"] = "degraded"
    out = build_incident_safety_observation(**b)
    assert out["status"] == "degraded"


def test_degraded_degraded_list_nonempty() -> None:
    b = _base()
    b["dependencies_state"]["degraded"] = ["telemetry_path"]
    out = build_incident_safety_observation(**b)
    assert out["status"] == "degraded"


def test_caution_telemetry_warn() -> None:
    b = _base()
    b["dependencies_state"]["telemetry"] = "warn"
    out = build_incident_safety_observation(**b)
    assert out["status"] == "caution"


def test_caution_dep_partial() -> None:
    b = _base()
    b["dependencies_state"]["summary"] = "partial"
    out = build_incident_safety_observation(**b)
    assert out["status"] == "caution"


def test_unknown_missing_incident() -> None:
    out = build_incident_safety_observation(
        incident_state=None,  # type: ignore[arg-type]
        dependencies_state={"summary": "ok", "degraded": []},
    )
    assert out["status"] == "unknown"


def test_policy_entry_consistency_note() -> None:
    b = _base()
    b["policy_state"]["blocked"] = True
    b["incident_state"]["entry_permitted"] = True
    out = build_incident_safety_observation(**b)
    notes = out.get("consistency_notes") or []
    assert any("entry_permitted" in n for n in notes)


def test_policy_operator_blocked_consistency_note() -> None:
    b = _base()
    b["policy_state"]["blocked"] = True
    b["operator_state"]["blocked"] = False
    out = build_incident_safety_observation(**b)
    notes = out.get("consistency_notes") or []
    assert any("operator_state.blocked" in n for n in notes)
