"""Immediate candidate-input rejection before GGE; no waiting, transport or entry.

Consumes already supplied cycle inputs and the existing CMC/typed-volatility
eligibility decision. Does not fetch data, select another instrument, alter
positions, or certify general economic safety.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence

from trading.master_v2.canonical_market_context_v1 import (
    CanonicalMarketContextEligibilityV1,
)

CANDIDATE_REJECTED = "CANDIDATE_INPUT_REJECTED"
REQUIRED_CANDIDATE_FINALIZED_CLOSES = 100


def invalid_candidate_cycle_input_codes_v1(
    *, values: Mapping[str, object], finalized_closes: object
) -> tuple[str, ...]:
    """Reject absent/non-numeric/non-finite supplied inputs before conversion.

    New candidates require their full historical input before any evaluation.
    Zero volume/OI and negative funding are not treated as missing.
    """
    codes: list[str] = []

    def valid_number(value: object) -> bool:
        if value is None or isinstance(value, bool):
            return False
        try:
            return math.isfinite(float(value))
        except (TypeError, ValueError, OverflowError):
            return False

    for key, value in values.items():
        if not valid_number(value):
            codes.append(f"{key}_missing_or_invalid")
    if (
        not isinstance(finalized_closes, Sequence)
        or isinstance(finalized_closes, (str, bytes))
        or not finalized_closes
        or any(not valid_number(value) or float(value) <= 0 for value in finalized_closes)
    ):
        codes.append("finalized_closes_missing_or_invalid")
    elif len(finalized_closes) < REQUIRED_CANDIDATE_FINALIZED_CLOSES:
        codes.append("finalized_history_not_ready")
    return tuple(codes)


def finalized_candidate_candle_history_rejection_codes_v1(payload: object) -> tuple[str, ...]:
    """Validate a supplied 1m snapshot; never wait, fetch, trim or rewrite it.

    The most recent 100 finalized candles must already exist, be distinct and
    contiguous. An unfinished current candle is not historical evidence.
    """
    if not isinstance(payload, Mapping) or not isinstance(payload.get("data"), list):
        return ("finalized_history_not_ready",)
    timestamps: list[float] = []
    for row in payload["data"]:
        if not isinstance(row, Sequence) or isinstance(row, (str, bytes)) or len(row) < 9:
            continue
        if str(row[8]) != "1":
            continue
        try:
            timestamp, close = float(row[0]), float(row[4])
        except (ValueError, TypeError, OverflowError):
            return ("finalized_history_invalid",)
        if not math.isfinite(timestamp) or not math.isfinite(close) or min(timestamp, close) <= 0:
            return ("finalized_history_invalid",)
        timestamps.append(timestamp)
    if len(timestamps) < REQUIRED_CANDIDATE_FINALIZED_CLOSES:
        return ("finalized_history_not_ready",)
    if len(set(timestamps)) != len(timestamps):
        return ("finalized_history_duplicate",)
    recent = sorted(timestamps)[-REQUIRED_CANDIDATE_FINALIZED_CLOSES:]
    if any(right - left != 60_000.0 for left, right in zip(recent, recent[1:])):
        return ("finalized_history_gap",)
    return ()


def candidate_market_context_rejection_codes_v1(
    eligibility: CanonicalMarketContextEligibilityV1,
) -> tuple[str, ...]:
    """Use the canonical validator's verdict; there is no WAIT outcome."""
    if (
        eligibility.trading_decision_allowed
        and eligibility.scope_confirmation_allowed
        and eligibility.new_directional_exposure_allowed
        and not eligibility.block_reasons
    ):
        return ()
    codes = tuple(reason.name for reason in eligibility.block_reasons)
    return codes or ("canonical_market_context_not_eligible",)
