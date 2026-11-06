"""Shared out-of-order event contract."""

from __future__ import annotations

from typing import Any

from src.ops.canonical_public_md_and_ohlcv_transport_reconciliation_v1.constants_v1 import (
    SAFETY_INVARIANTS,
)


class OutOfOrderContractErrorV1(ValueError):
    """Fail-closed out-of-order handling violation."""


def out_of_order_contract_v1() -> dict[str, Any]:
    return {
        "out_of_order_must_be_explicitly_classified": True,
        "out_of_order_must_not_silently_mutate_finalized_truth": True,
        "reuses_distinct_market_observation_acceptor": True,
        "invariant": SAFETY_INVARIANTS["OUT_OF_ORDER_MUST_BE_CLASSIFIED"],
    }


def classify_or_reject_out_of_order_v1(
    *,
    classification: str,
    finalized: bool,
    attempted_silent_mutation: bool,
) -> dict[str, Any]:
    token = str(classification).lower()
    if token != "out_of_order":
        raise OutOfOrderContractErrorV1(f"NOT_OUT_OF_ORDER:{classification}")
    if finalized and attempted_silent_mutation:
        raise OutOfOrderContractErrorV1("OUT_OF_ORDER_SILENT_FINALIZED_MUTATION_FORBIDDEN")
    return {
        "classification": "out_of_order",
        "finalized_truth_mutated": False,
        "explicit": True,
    }
