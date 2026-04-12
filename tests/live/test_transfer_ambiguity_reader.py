"""Unit tests for transfer_ambiguity_reader (local signals only, read-only)."""

from __future__ import annotations

from src.live.transfer_ambiguity_reader import (
    READER_SCHEMA_VERSION,
    RUNBOOK_REF,
    build_transfer_ambiguity_state,
)


def _exposure(**kwargs: object) -> dict:
    base = {
        "summary": "no_live_context",
        "treasury_separation": "enforced",
        "risk_status": "unknown",
    }
    base.update(kwargs)
    return base


def test_no_signal_when_insufficient_and_treasury_unknown() -> None:
    out = build_transfer_ambiguity_state(
        guard_state={"treasury_separation": "unknown"},
        stale_state={"balance": "unknown"},
        balance_semantics_state={"balance_semantic_state": None},
        exposure_state=_exposure(),
    )
    assert out["status"] == "no_signal"
    assert out["summary"] == "insufficient_local_signals"
    assert out["operator_attention_hint"] is False
    assert out["runbook_ref"] == RUNBOOK_REF
    assert out["reader_schema_version"] == READER_SCHEMA_VERSION
    assert "not broker" not in out["summary"].lower()


def test_ok_when_local_unremarkable_and_treasury_enforced() -> None:
    out = build_transfer_ambiguity_state(
        guard_state={"treasury_separation": "enforced"},
        stale_state={"balance": "ok"},
        balance_semantics_state={"balance_semantic_state": "balance_semantics_clear"},
        exposure_state=_exposure(stale=False),
    )
    assert out["status"] == "ok"
    assert "broker_transfer_truth_not_observed" in out["summary"]
    assert out["operator_attention_hint"] is False


def test_warning_on_balance_stale_warn() -> None:
    out = build_transfer_ambiguity_state(
        guard_state={"treasury_separation": "enforced"},
        stale_state={"balance": "warn"},
        balance_semantics_state={"balance_semantic_state": "balance_semantics_clear"},
        exposure_state=_exposure(stale=False),
    )
    assert out["status"] == "warning"
    assert out["operator_attention_hint"] is True
    assert "balance_stale_not_ok" in out["observation_reason"]


def test_warning_on_exposure_snapshot_stale() -> None:
    out = build_transfer_ambiguity_state(
        guard_state={"treasury_separation": "enforced"},
        stale_state={"balance": "ok"},
        balance_semantics_state={"balance_semantic_state": "balance_semantics_clear"},
        exposure_state=_exposure(stale=True),
    )
    assert out["status"] == "warning"
    assert "exposure_snapshot_stale" in out["observation_reason"]


def test_unknown_when_semantics_missing_but_treasury_enforced() -> None:
    out = build_transfer_ambiguity_state(
        guard_state={"treasury_separation": "enforced"},
        stale_state={"balance": "unknown"},
        balance_semantics_state={"balance_semantic_state": None},
        exposure_state=_exposure(),
    )
    assert out["status"] == "unknown"
    assert "ambiguous_or_partial" in out["summary"]
    assert out["operator_attention_hint"] is True
