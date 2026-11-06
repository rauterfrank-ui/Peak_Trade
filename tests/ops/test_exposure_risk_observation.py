"""Unit tests for ``build_exposure_risk_observation`` (cockpit aggregate only)."""

from __future__ import annotations

from typing import Any, Dict

from src.ops.exposure_risk_observation import (
    READER_SCHEMA_VERSION,
    build_exposure_risk_observation,
)


def _base(**over: Any) -> Dict[str, Any]:
    exposure_state: Dict[str, Any] = {
        "summary": "no_live_context",
        "treasury_separation": "enforced",
        "risk_status": "unknown",
        "caps_configured": [],
    }
    transfer_ambiguity_state: Dict[str, Any] = {
        "status": "unknown",
        "summary": "ambiguous_or_partial_local_signals_transfer_truth_not_observed_here",
        "operator_attention_hint": False,
    }
    stale_state: Dict[str, Any] = {
        "summary": "unknown",
        "balance": "unknown",
        "position": "unknown",
        "order": "unknown",
        "exposure": "unknown",
    }
    guard_state: Dict[str, Any] = {
        "no_trade_baseline": "reference",
        "deny_by_default": "active",
        "treasury_separation": "enforced",
    }
    base = {
        "exposure_state": exposure_state,
        "transfer_ambiguity_state": transfer_ambiguity_state,
        "stale_state": stale_state,
        "guard_state": guard_state,
    }
    base.update(over)
    return base


def test_nominal_empty_local_surface() -> None:
    out = build_exposure_risk_observation(**_base())
    assert out["status"] == "nominal"
    assert out["data_source"] == "cockpit_payload_aggregate"
    assert out["reader_schema_version"] == READER_SCHEMA_VERSION


def test_degraded_risk_critical() -> None:
    b = _base()
    b["exposure_state"]["risk_status"] = "critical"
    out = build_exposure_risk_observation(**b)
    assert out["status"] == "degraded"


def test_degraded_transfer_warning() -> None:
    b = _base()
    b["transfer_ambiguity_state"]["status"] = "warning"
    out = build_exposure_risk_observation(**b)
    assert out["status"] == "degraded"


def test_degraded_exposure_stale() -> None:
    b = _base()
    b["exposure_state"]["stale"] = True
    out = build_exposure_risk_observation(**b)
    assert out["status"] == "degraded"


def test_degraded_stale_state_exposure() -> None:
    b = _base()
    b["stale_state"]["exposure"] = "stale"
    out = build_exposure_risk_observation(**b)
    assert out["status"] == "degraded"


def test_caution_risk_warn() -> None:
    b = _base()
    b["exposure_state"]["risk_status"] = "warn"
    out = build_exposure_risk_observation(**b)
    assert out["status"] == "caution"


def test_caution_operator_hint() -> None:
    b = _base()
    b["transfer_ambiguity_state"]["operator_attention_hint"] = True
    out = build_exposure_risk_observation(**b)
    assert out["status"] == "caution"


def test_degraded_priority_over_caution() -> None:
    b = _base()
    b["exposure_state"]["risk_status"] = "critical"
    b["transfer_ambiguity_state"]["operator_attention_hint"] = True
    out = build_exposure_risk_observation(**b)
    assert out["status"] == "degraded"


def test_unknown_missing_guard() -> None:
    out = build_exposure_risk_observation(
        exposure_state={},
        transfer_ambiguity_state={},
        stale_state={},
        guard_state=None,  # type: ignore[arg-type]
    )
    assert out["status"] == "unknown"


def test_treasury_mismatch_note() -> None:
    b = _base()
    b["exposure_state"]["treasury_separation"] = "unknown"
    out = build_exposure_risk_observation(**b)
    notes = out.get("consistency_notes") or []
    assert any("treasury_separation" in n for n in notes)
