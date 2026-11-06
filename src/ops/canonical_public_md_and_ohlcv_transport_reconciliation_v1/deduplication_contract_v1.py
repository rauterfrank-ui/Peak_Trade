"""Shared deduplication contract for authoritative public-MD bars."""

from __future__ import annotations

from typing import Any, Mapping

from src.ops.canonical_public_md_and_ohlcv_transport_reconciliation_v1.constants_v1 import (
    SAFETY_INVARIANTS,
)


def deduplication_contract_v1() -> dict[str, Any]:
    return {
        "duplicate_events_do_not_advance_authoritative_state": True,
        "reuses_distinct_market_observation_acceptor": True,
        "transport_only_duplicate_is_non_advancing": True,
        "invariant": SAFETY_INVARIANTS["DUPLICATE_DOES_NOT_ADVANCE_AUTHORITATIVE_STATE"],
    }


def should_advance_authoritative_state_v1(*, classification: str) -> bool:
    return str(classification).lower() == "distinct"


def apply_dedup_gate_v1(*, classification: str, mutate: bool) -> dict[str, Any]:
    advance = should_advance_authoritative_state_v1(classification=classification)
    if mutate and not advance:
        raise ValueError("DUPLICATE_MUST_NOT_ADVANCE_AUTHORITATIVE_STATE")
    return {
        "classification": classification,
        "advance_allowed": advance,
        "state_mutated": bool(mutate and advance),
    }
