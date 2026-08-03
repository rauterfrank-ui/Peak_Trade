"""Shared bar quality / finalization state contract."""

from __future__ import annotations

from typing import Any

from src.ops.canonical_public_md_and_ohlcv_transport_reconciliation_v1.constants_v1 import (
    BAR_STATE_CORRECTED,
    BAR_STATE_FINALIZED,
    BAR_STATE_IN_PROGRESS,
    BAR_STATE_MISSING,
    BAR_STATE_STALE,
    BAR_STATES,
)


class BarStateContractErrorV1(ValueError):
    """Fail-closed bar-state violation."""


def normalize_bar_state_v1(raw: str) -> str:
    token = str(raw or "").strip().upper()
    # Accept compact aliases used in envelopes.
    aliases = {
        "IN_PROGRESS": BAR_STATE_IN_PROGRESS,
        "IN_PROGRESS_BAR": BAR_STATE_IN_PROGRESS,
        "FINALIZED": BAR_STATE_FINALIZED,
        "FINALIZED_BAR": BAR_STATE_FINALIZED,
        "CORRECTED": BAR_STATE_CORRECTED,
        "CORRECTED_BAR": BAR_STATE_CORRECTED,
        "MISSING": BAR_STATE_MISSING,
        "MISSING_BAR": BAR_STATE_MISSING,
        "STALE": BAR_STATE_STALE,
        "STALE_BAR": BAR_STATE_STALE,
    }
    if token not in aliases:
        raise BarStateContractErrorV1(f"UNKNOWN_BAR_STATE:{raw}")
    return aliases[token]


def bar_state_contract_v1() -> dict[str, Any]:
    return {
        "states": sorted(BAR_STATES),
        "in_progress_can_update": True,
        "finalized_immutable_unless_correction": True,
        "correction_increments_revision": True,
        "missing_is_explicit": True,
        "stale_is_explicit": True,
        "silent_gap_fill_forbidden": True,
        "fabricated_live_state_forbidden": True,
    }


def assert_transition_allowed_v1(*, from_state: str, to_state: str, via_correction: bool) -> None:
    src = normalize_bar_state_v1(from_state)
    dst = normalize_bar_state_v1(to_state)
    if src == dst:
        return
    if src == BAR_STATE_IN_PROGRESS and dst in {
        BAR_STATE_IN_PROGRESS,
        BAR_STATE_FINALIZED,
        BAR_STATE_STALE,
        BAR_STATE_MISSING,
    }:
        return
    if src == BAR_STATE_FINALIZED and dst == BAR_STATE_CORRECTED and via_correction:
        return
    if src == BAR_STATE_CORRECTED and dst == BAR_STATE_CORRECTED and via_correction:
        return
    if src == BAR_STATE_MISSING and dst in {BAR_STATE_IN_PROGRESS, BAR_STATE_STALE}:
        return
    if src == BAR_STATE_STALE and dst in {
        BAR_STATE_IN_PROGRESS,
        BAR_STATE_MISSING,
        BAR_STATE_STALE,
    }:
        return
    raise BarStateContractErrorV1(f"ILLEGAL_BAR_STATE_TRANSITION:{src}->{dst}")
