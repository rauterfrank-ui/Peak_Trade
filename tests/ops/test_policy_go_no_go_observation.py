"""Unit tests for ``build_policy_go_no_go_observation``."""

from __future__ import annotations

from src.ops.policy_go_no_go_observation import (
    READER_SCHEMA_VERSION,
    build_policy_go_no_go_observation,
)


def _base_op() -> dict:
    return {
        "disabled": False,
        "enabled": True,
        "armed": True,
        "dry_run": True,
        "blocked": False,
        "kill_switch_active": False,
    }


def test_policy_go_no_go_missing_policy_returns_unknown() -> None:
    out = build_policy_go_no_go_observation(
        policy_state=None,  # type: ignore[arg-type]
        incident_state={},
        operator_state={},
    )
    assert out["status"] == "unknown"
    assert out["observation_reason"] == "missing_required_state_dict"
    assert out["reader_schema_version"] == READER_SCHEMA_VERSION


def test_policy_go_no_go_blocking_when_blocked() -> None:
    out = build_policy_go_no_go_observation(
        policy_state={
            "action": "NO_TRADE",
            "blocked": True,
            "summary": "blocked",
            "kill_switch_active": False,
        },
        incident_state={
            "status": "blocked",
            "summary": "blocked",
            "degraded": False,
            "requires_operator_attention": True,
            "kill_switch_active": False,
            "entry_permitted": False,
        },
        operator_state=_base_op(),
    )
    assert out["status"] == "blocking"
    assert "not a live go decision" in out["summary"].lower()
    assert "policy_state.blocked" in out["contributing_signals"]


def test_policy_go_no_go_blocking_kill_switch_any() -> None:
    out = build_policy_go_no_go_observation(
        policy_state={
            "action": "TRADE_READY",
            "blocked": False,
            "summary": "armed",
            "kill_switch_active": False,
        },
        incident_state={
            "status": "normal",
            "summary": "normal",
            "degraded": False,
            "requires_operator_attention": False,
            "kill_switch_active": True,
            "entry_permitted": True,
        },
        operator_state=_base_op(),
    )
    assert out["status"] == "blocking"
    assert "incident_state.kill_switch_active" in out["contributing_signals"]


def test_policy_go_no_go_degraded_incident_not_blocked_policy() -> None:
    out = build_policy_go_no_go_observation(
        policy_state={
            "action": "TRADE_READY",
            "blocked": False,
            "summary": "armed",
            "kill_switch_active": False,
        },
        incident_state={
            "status": "normal",
            "summary": "degraded",
            "degraded": True,
            "requires_operator_attention": False,
            "kill_switch_active": False,
            "entry_permitted": True,
        },
        operator_state=_base_op(),
    )
    assert out["status"] == "degraded"
    assert "incident_state.degraded" in out["contributing_signals"]


def test_policy_go_no_go_caution_requires_attention() -> None:
    out = build_policy_go_no_go_observation(
        policy_state={
            "action": "TRADE_READY",
            "blocked": False,
            "summary": "armed",
            "kill_switch_active": False,
        },
        incident_state={
            "status": "normal",
            "summary": "normal",
            "degraded": False,
            "requires_operator_attention": True,
            "kill_switch_active": False,
            "entry_permitted": True,
        },
        operator_state=_base_op(),
    )
    assert out["status"] == "caution"
    assert "incident_state.requires_operator_attention" in out["contributing_signals"]


def test_policy_go_no_go_nominal() -> None:
    out = build_policy_go_no_go_observation(
        policy_state={
            "action": "TRADE_READY",
            "blocked": False,
            "summary": "armed",
            "kill_switch_active": False,
        },
        incident_state={
            "status": "normal",
            "summary": "normal",
            "degraded": False,
            "requires_operator_attention": False,
            "kill_switch_active": False,
            "entry_permitted": True,
        },
        operator_state=_base_op(),
    )
    assert out["status"] == "nominal"
    assert "not an approval" in out["summary"].lower()
    assert "policy_state.action" in out["contributing_signals"]


def test_policy_go_no_go_kill_switch_mismatch_note() -> None:
    out = build_policy_go_no_go_observation(
        policy_state={
            "action": "TRADE_READY",
            "blocked": False,
            "summary": "armed",
            "kill_switch_active": False,
        },
        incident_state={
            "status": "normal",
            "summary": "normal",
            "degraded": False,
            "requires_operator_attention": False,
            "kill_switch_active": True,
            "entry_permitted": True,
        },
        operator_state=_base_op(),
    )
    assert any("kill_switch_active differs" in n for n in out["consistency_notes"])
    assert out["status"] == "blocking"


def test_policy_go_no_go_entry_permitted_mismatch_note() -> None:
    out = build_policy_go_no_go_observation(
        policy_state={
            "action": "TRADE_READY",
            "blocked": False,
            "summary": "armed",
            "kill_switch_active": False,
        },
        incident_state={
            "status": "normal",
            "summary": "normal",
            "degraded": False,
            "requires_operator_attention": False,
            "kill_switch_active": False,
            "entry_permitted": False,
        },
        operator_state=_base_op(),
    )
    assert any("entry_permitted does not align" in n for n in out["consistency_notes"])


def test_policy_go_no_go_unexpected_action_caution() -> None:
    out = build_policy_go_no_go_observation(
        policy_state={
            "action": "HOLD",
            "blocked": False,
            "summary": "armed",
            "kill_switch_active": False,
        },
        incident_state={
            "status": "normal",
            "summary": "normal",
            "degraded": False,
            "requires_operator_attention": False,
            "kill_switch_active": False,
            "entry_permitted": True,
        },
        operator_state=_base_op(),
    )
    assert out["status"] == "caution"
    assert out.get("observation_reason") == "unexpected_policy_action_label"
