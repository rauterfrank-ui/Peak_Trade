"""Unit tests for ``build_run_session_observation`` (cockpit aggregate only)."""

from __future__ import annotations

from typing import Any, Dict

from src.ops.run_session_observation import (
    READER_SCHEMA_VERSION,
    build_run_session_observation,
)


def _base(**over: Any) -> Dict[str, Any]:
    run_state: Dict[str, Any] = {
        "status": "idle",
        "active": False,
        "session_active": False,
        "last_run_status": "unknown",
        "generated_at": "2026-01-01T00:00:00+00:00",
        "freshness_status": "ok",
    }
    session_end_mismatch_state: Dict[str, Any] = {
        "status": "no_signal",
        "summary": "no_signal",
        "blocked_next_session": False,
        "data_source": "none",
    }
    stale_state: Dict[str, Any] = {
        "summary": "unknown",
        "balance": "unknown",
        "position": "unknown",
        "order": "unknown",
        "exposure": "unknown",
    }
    operator_state: Dict[str, Any] = {
        "disabled": False,
        "enabled": True,
        "armed": True,
        "blocked": False,
        "kill_switch_active": False,
    }
    base = {
        "run_state": run_state,
        "session_end_mismatch_state": session_end_mismatch_state,
        "stale_state": stale_state,
        "operator_state": operator_state,
    }
    base.update(over)
    return base


def test_nominal_idle_no_signal() -> None:
    out = build_run_session_observation(**_base())
    assert out["status"] == "nominal"
    assert out["data_source"] == "cockpit_payload_aggregate"
    assert out["reader_schema_version"] == READER_SCHEMA_VERSION
    assert "guarantee" in out["summary"].lower() or "observation" in out["summary"].lower()


def test_attention_mismatch_signal() -> None:
    b = _base()
    b["session_end_mismatch_state"]["status"] = "mismatch_signal"
    b["session_end_mismatch_state"]["blocked_next_session"] = True
    out = build_run_session_observation(**b)
    assert out["status"] == "attention"


def test_attention_blocked_next_only() -> None:
    b = _base()
    b["session_end_mismatch_state"]["status"] = "aligned"
    b["session_end_mismatch_state"]["blocked_next_session"] = True
    out = build_run_session_observation(**b)
    assert out["status"] == "attention"


def test_caution_ambiguous() -> None:
    b = _base()
    b["session_end_mismatch_state"]["status"] = "ambiguous"
    out = build_run_session_observation(**b)
    assert out["status"] == "caution"


def test_degraded_stale_summary() -> None:
    b = _base()
    b["stale_state"]["summary"] = "stale"
    out = build_run_session_observation(**b)
    assert out["status"] == "degraded"


def test_degraded_run_freshness_warn() -> None:
    b = _base()
    b["run_state"]["freshness_status"] = "warn"
    out = build_run_session_observation(**b)
    assert out["status"] == "degraded"


def test_attention_priority_over_stale() -> None:
    b = _base()
    b["stale_state"]["summary"] = "stale"
    b["session_end_mismatch_state"]["status"] = "mismatch_signal"
    out = build_run_session_observation(**b)
    assert out["status"] == "attention"


def test_caution_active_with_no_signal() -> None:
    b = _base()
    b["run_state"]["session_active"] = True
    b["run_state"]["status"] = "active"
    b["run_state"]["active"] = True
    b["session_end_mismatch_state"]["status"] = "no_signal"
    out = build_run_session_observation(**b)
    assert out["status"] == "caution"


def test_unknown_missing_run_state() -> None:
    out = build_run_session_observation(
        run_state=None,  # type: ignore[arg-type]
        session_end_mismatch_state={"status": "no_signal"},
    )
    assert out["status"] == "unknown"
    assert out.get("observation_reason") == "missing_required_state_dict"


def test_operator_blocked_with_active_session_note() -> None:
    b = _base()
    b["run_state"]["session_active"] = True
    b["run_state"]["status"] = "active"
    b["operator_state"]["blocked"] = True
    out = build_run_session_observation(**b)
    notes = out.get("consistency_notes") or []
    assert any("operator_state" in n for n in notes)


def test_caution_unknown_sem_while_active() -> None:
    b = _base()
    b["run_state"]["session_active"] = True
    b["run_state"]["status"] = "active"
    b["session_end_mismatch_state"]["status"] = "unknown"
    out = build_run_session_observation(**b)
    assert out["status"] == "caution"
