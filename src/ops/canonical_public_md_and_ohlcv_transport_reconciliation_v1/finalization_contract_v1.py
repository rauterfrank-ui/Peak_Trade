"""Shared finalization contract for authoritative bars."""

from __future__ import annotations

from typing import Any

from src.ops.canonical_public_md_and_ohlcv_transport_reconciliation_v1.bar_state_contract_v1 import (
    BarStateContractErrorV1,
    assert_transition_allowed_v1,
    normalize_bar_state_v1,
)
from src.ops.canonical_public_md_and_ohlcv_transport_reconciliation_v1.constants_v1 import (
    BAR_STATE_FINALIZED,
    BAR_STATE_IN_PROGRESS,
)


def finalization_contract_v1() -> dict[str, Any]:
    return {
        "finalized_immutable_unless_correction_contract": True,
        "duplicate_finalization_forbidden": True,
        "finalize_requires_in_progress": True,
        "finalize_binds_bar_close_time": True,
    }


def assert_can_finalize_v1(*, current_state: str, already_finalized: bool) -> None:
    if already_finalized:
        raise BarStateContractErrorV1("DUPLICATE_FINALIZATION_FORBIDDEN")
    state = normalize_bar_state_v1(current_state)
    if state != BAR_STATE_IN_PROGRESS:
        raise BarStateContractErrorV1(f"FINALIZE_REQUIRES_IN_PROGRESS:{state}")
    assert_transition_allowed_v1(
        from_state=BAR_STATE_IN_PROGRESS,
        to_state=BAR_STATE_FINALIZED,
        via_correction=False,
    )
