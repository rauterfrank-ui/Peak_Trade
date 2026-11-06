"""Shared correction + monotonic revision contract."""

from __future__ import annotations

from typing import Any

from src.ops.canonical_public_md_and_ohlcv_transport_reconciliation_v1.bar_state_contract_v1 import (
    BarStateContractErrorV1,
    normalize_bar_state_v1,
)
from src.ops.canonical_public_md_and_ohlcv_transport_reconciliation_v1.constants_v1 import (
    BAR_STATE_CORRECTED,
    BAR_STATE_FINALIZED,
)


class CorrectionRevisionContractErrorV1(ValueError):
    """Fail-closed correction/revision violation."""


def correction_contract_v1() -> dict[str, Any]:
    return {
        "correction_requires_finalized_or_corrected": True,
        "correction_increments_revision": True,
        "revision_monotonic_non_decreasing": True,
        "revision_starts_at_zero": True,
    }


def revision_contract_v1() -> dict[str, Any]:
    return correction_contract_v1()


def next_revision_v1(*, current_revision: int) -> int:
    if isinstance(current_revision, bool) or not isinstance(current_revision, int):
        raise CorrectionRevisionContractErrorV1("INVALID_REVISION_TYPE")
    if current_revision < 0:
        raise CorrectionRevisionContractErrorV1("INVALID_REVISION_NEGATIVE")
    return current_revision + 1


def assert_correction_allowed_v1(*, current_state: str, current_revision: int) -> int:
    state = normalize_bar_state_v1(current_state)
    if state not in {BAR_STATE_FINALIZED, BAR_STATE_CORRECTED}:
        raise BarStateContractErrorV1(f"CORRECTION_REQUIRES_FINALIZED_OR_CORRECTED:{state}")
    return next_revision_v1(current_revision=current_revision)
