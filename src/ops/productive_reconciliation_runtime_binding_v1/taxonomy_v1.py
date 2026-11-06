"""Fail-closed reconciliation state taxonomy for productive runtime binding."""

from __future__ import annotations

from enum import Enum


class ProductiveReconciliationClass(str, Enum):
    MATCH = "MATCH"
    RECOVERABLE_DRIFT = "RECOVERABLE_DRIFT"
    UNRECOVERABLE_DRIFT = "UNRECOVERABLE_DRIFT"
    MISSING_TRUTH = "MISSING_TRUTH"
    STALE_SOURCE = "STALE_SOURCE"
    DUPLICATE_STATE = "DUPLICATE_STATE"
    CONFLICTING_WRITER = "CONFLICTING_WRITER"


HARD_STOP_CLASSES = frozenset(
    {
        ProductiveReconciliationClass.UNRECOVERABLE_DRIFT,
        ProductiveReconciliationClass.MISSING_TRUTH,
        ProductiveReconciliationClass.STALE_SOURCE,
        ProductiveReconciliationClass.DUPLICATE_STATE,
        ProductiveReconciliationClass.CONFLICTING_WRITER,
    }
)

ALPHA_SAFE_CLASSES = frozenset(
    {
        ProductiveReconciliationClass.MATCH,
    }
)
