"""Unit tests for ``build_safety_posture_observation`` (cockpit aggregate only)."""

from __future__ import annotations

from typing import Any, Dict

import pytest

from src.ops.safety_posture_observation import (
    READER_SCHEMA_VERSION,
    build_safety_posture_observation,
)


def _base(
    **over: Any,
) -> Dict[str, Any]:
    policy_state: Dict[str, Any] = {
        "action": "TRADE_READY",
        "blocked": False,
        "summary": "armed",
        "kill_switch_active": False,
    }
    guard_state: Dict[str, Any] = {
        "no_trade_baseline": "reference",
        "deny_by_default": "active",
        "treasury_separation": "enforced",
    }
    incident_state: Dict[str, Any] = {
        "status": "normal",
        "blocked": False,
        "kill_switch_active": False,
        "degraded": False,
        "requires_operator_attention": False,
        "summary": "normal",
        "incident_stop_invoked": False,
        "entry_permitted": True,
    }
    operator_state: Dict[str, Any] = {
        "disabled": False,
        "enabled": True,
        "armed": True,
        "blocked": False,
        "kill_switch_active": False,
    }
    system_state: Dict[str, Any] = {
        "mode": "truth_first_ops_cockpit_v3",
        "execution_model": "guarded_execution",
        "config_load_status": "loaded",
        "environment": "paper",
        "gating_posture_observation": "armed",
    }
    stale_state: Dict[str, Any] = {"summary": "ok"}
    dependencies_state: Dict[str, Any] = {"summary": "ok"}
    base = {
        "policy_state": policy_state,
        "guard_state": guard_state,
        "incident_state": incident_state,
        "operator_state": operator_state,
        "system_state": system_state,
        "stale_state": stale_state,
        "dependencies_state": dependencies_state,
    }
    base.update(over)
    return base


def test_nominal_aggregate() -> None:
    b = _base()
    out = build_safety_posture_observation(**b)
    assert out["status"] == "nominal"
    assert out["data_source"] == "cockpit_payload_aggregate"
    assert out["reader_schema_version"] == READER_SCHEMA_VERSION
    assert "approval" not in out["summary"].lower()
    assert "contributing_signals" in out


def test_blocking_from_kill_switch() -> None:
    b = _base()
    b["policy_state"]["kill_switch_active"] = True
    b["incident_state"]["kill_switch_active"] = True
    b["operator_state"]["kill_switch_active"] = True
    out = build_safety_posture_observation(**b)
    assert out["status"] == "blocking"


def test_blocking_from_policy_blocked() -> None:
    b = _base()
    b["policy_state"]["blocked"] = True
    b["policy_state"]["summary"] = "blocked"
    b["incident_state"]["entry_permitted"] = False
    out = build_safety_posture_observation(**b)
    assert out["status"] == "blocking"


def test_degraded_from_incident_degraded() -> None:
    b = _base()
    b["incident_state"]["degraded"] = True
    b["incident_state"]["requires_operator_attention"] = True
    b["incident_state"]["summary"] = "degraded"
    out = build_safety_posture_observation(**b)
    assert out["status"] == "degraded"


def test_degraded_from_stale_summary() -> None:
    b = _base()
    b["stale_state"]["summary"] = "stale"
    out = build_safety_posture_observation(**b)
    assert out["status"] == "degraded"


def test_degraded_from_dependencies_degraded() -> None:
    b = _base()
    b["dependencies_state"]["summary"] = "degraded"
    out = build_safety_posture_observation(**b)
    assert out["status"] == "degraded"


def test_caution_from_incident_stop_only() -> None:
    b = _base()
    b["incident_state"]["incident_stop_invoked"] = True
    out = build_safety_posture_observation(**b)
    assert out["status"] == "caution"


def test_caution_from_requires_operator_attention_without_degraded() -> None:
    b = _base()
    b["incident_state"]["requires_operator_attention"] = True
    b["incident_state"]["summary"] = "attention"
    out = build_safety_posture_observation(**b)
    assert out["status"] == "caution"


def test_blocking_priority_over_degraded() -> None:
    b = _base()
    b["policy_state"]["blocked"] = True
    b["incident_state"]["degraded"] = True
    b["stale_state"]["summary"] = "stale"
    out = build_safety_posture_observation(**b)
    assert out["status"] == "blocking"


def test_entry_permitted_mismatch_note() -> None:
    b = _base()
    b["policy_state"]["blocked"] = False
    b["incident_state"]["entry_permitted"] = False
    out = build_safety_posture_observation(**b)
    notes = out.get("consistency_notes") or []
    assert any("entry_permitted" in n for n in notes)


def test_gating_mirror_mismatch_note() -> None:
    b = _base()
    b["system_state"]["gating_posture_observation"] = "blocked"
    out = build_safety_posture_observation(**b)
    notes = out.get("consistency_notes") or []
    assert any("gating_posture_observation" in n for n in notes)


def test_unknown_when_required_dict_missing() -> None:
    out = build_safety_posture_observation(
        policy_state=None,  # type: ignore[arg-type]
        guard_state={},
        incident_state={},
        operator_state={},
        system_state={},
    )
    assert out["status"] == "unknown"
    assert out.get("observation_reason") == "missing_required_state_dict"


def test_kill_switch_mismatch_note() -> None:
    b = _base()
    b["policy_state"]["kill_switch_active"] = True
    b["incident_state"]["kill_switch_active"] = False
    out = build_safety_posture_observation(**b)
    assert out["status"] == "blocking"
    notes = out.get("consistency_notes") or []
    assert any("kill_switch_active differs" in n for n in notes)


@pytest.mark.parametrize(
    "entry_val",
    [None, "maybe"],
)
def test_non_boolean_entry_permitted_handled(entry_val: Any) -> None:
    b = _base()
    b["incident_state"]["entry_permitted"] = entry_val
    out = build_safety_posture_observation(**b)
    assert out["status"] == "nominal"
    if entry_val == "maybe":
        notes = out.get("consistency_notes") or []
        assert any("not interpretable" in n for n in notes)
