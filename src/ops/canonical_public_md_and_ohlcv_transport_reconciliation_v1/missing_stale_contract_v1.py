"""Shared missing-bar and stale-bar contracts."""

from __future__ import annotations

from typing import Any

from src.ops.canonical_public_md_and_ohlcv_transport_reconciliation_v1.bar_state_contract_v1 import (
    BarStateContractErrorV1,
    normalize_bar_state_v1,
)
from src.ops.canonical_public_md_and_ohlcv_transport_reconciliation_v1.constants_v1 import (
    BAR_STATE_MISSING,
    BAR_STATE_STALE,
)


def missing_bar_contract_v1() -> dict[str, Any]:
    return {
        "missing_is_explicit_state": True,
        "silent_gap_fill_forbidden": True,
        "fabricated_live_state_forbidden": True,
        "expected_missing_source_semantics_deferred_to_o5": True,
    }


def stale_bar_contract_v1() -> dict[str, Any]:
    return {
        "stale_is_explicit_state": True,
        "stale_does_not_imply_finalized": True,
        "dashboard_chrome_deferred_to_o5": True,
    }


def mark_missing_bar_v1(*, fabricate_fill: bool = False) -> str:
    if fabricate_fill:
        raise BarStateContractErrorV1("SILENT_GAP_FILL_FORBIDDEN")
    return normalize_bar_state_v1(BAR_STATE_MISSING)


def mark_stale_bar_v1(*, fabricate_live: bool = False) -> str:
    if fabricate_live:
        raise BarStateContractErrorV1("FABRICATED_LIVE_STATE_FORBIDDEN")
    return normalize_bar_state_v1(BAR_STATE_STALE)
