"""Typed aged/fresh volatility comparison (canonical estimator only)."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Mapping, Optional, Sequence

import pandas as pd

from research.canonical_volatility_numeric_max_age_multi_session_natural_age_typed_volatility_and_actionable_strata_evidence_v1.constants_v1 import (
    AGED_ESTIMATE_MUTATION_FORBIDDEN,
    FRESH_ESTIMATE_MUST_USE_CANONICAL_ESTIMATOR,
    SCHEMA_TYPED_VOL_COMPARISON,
    STATIC_VOLATILITY_DEFAULT_FORBIDDEN,
    SYNTHETIC_VOLATILITY_VALUES_FORBIDDEN,
)
from research.canonical_volatility_numeric_max_age_multi_session_natural_age_typed_volatility_and_actionable_strata_evidence_v1.models_v1 import (
    MultiSessionTypedVolEvidenceError,
    sha256_hex_canonical,
)
from trading.master_v2.canonical_volatility_estimate_typed_consumption_contract_v1 import (
    CANONICAL_ANNUALIZED,
    CANONICAL_ESTIMATOR,
    CANONICAL_ESTIMATOR_VERSION,
    CANONICAL_HORIZON,
    CANONICAL_UNIT,
    CanonicalVolatilityEstimateV1,
    SUPPORTED_CONTRACT_VERSION,
    materialize_typed_canonical_volatility_estimate_v1,
    validate_canonical_volatility_estimate_v1,
)


def _reject_synthetic_literals_v1(*, value: float, source: str) -> None:
    if not SYNTHETIC_VOLATILITY_VALUES_FORBIDDEN:
        raise MultiSessionTypedVolEvidenceError("synthetic_vol_forbid_flag_drift")
    if not STATIC_VOLATILITY_DEFAULT_FORBIDDEN:
        raise MultiSessionTypedVolEvidenceError("static_vol_forbid_flag_drift")
    # Explicit rejection of the removed S03 scaffold constants.
    if abs(float(value) - 0.12) < 1e-15 and source == "scaffold_default":
        raise MultiSessionTypedVolEvidenceError("synthetic_volatility_scaffold_rejected")


def estimate_record_v1(estimate: CanonicalVolatilityEstimateV1) -> dict[str, Any]:
    validated = validate_canonical_volatility_estimate_v1(estimate)
    payload = {
        "VOLATILITY_CONTRACT_VERSION": validated.contract_version,
        "ESTIMATOR_ID": validated.estimator,
        "ESTIMATOR_VERSION": validated.estimator_version,
        "ESTIMATOR_SOURCE_DIGEST": validated.source_digest,
        "VALUE": float(validated.value),
        "UNIT": validated.unit,
        "HORIZON": CANONICAL_HORIZON,
        "HORIZON_SECONDS": int(validated.horizon_seconds),
        "ANNUALIZED": bool(validated.annualized),
        "OBSERVATION_COUNT": int(validated.observation_count),
        "AS_OF_EVENT_TIME": validated.as_of_event_time.astimezone(timezone.utc).isoformat(),
        "PRODUCED_AT_EVENT_TIME": validated.as_of_event_time.astimezone(timezone.utc).isoformat(),
        "SOURCE_WINDOW_START": (
            None
            if validated.oldest_observation_event_time is None
            else validated.oldest_observation_event_time.astimezone(timezone.utc).isoformat()
        ),
        "SOURCE_WINDOW_END": validated.as_of_event_time.astimezone(timezone.utc).isoformat(),
        "SOURCE_WINDOW_DIGEST": validated.source_digest,
        "FALLBACK_USED": bool(validated.fallback_used),
        "FALLBACK_REASON": validated.fallback_identity,
        "MARKET_CONTEXT_DIGEST": validated.config_digest,
        "estimate": validated.to_dict(),
    }
    payload["record_digest"] = sha256_hex_canonical(
        {k: v for k, v in payload.items() if k != "estimate"}
    )
    return payload


def assert_estimates_contract_compatible_v1(
    aged: CanonicalVolatilityEstimateV1,
    fresh: CanonicalVolatilityEstimateV1,
) -> None:
    a = validate_canonical_volatility_estimate_v1(aged)
    f = validate_canonical_volatility_estimate_v1(fresh)
    if a.unit != f.unit or a.unit != CANONICAL_UNIT:
        raise MultiSessionTypedVolEvidenceError("unit_mismatch_not_comparable")
    if a.horizon_seconds != f.horizon_seconds:
        raise MultiSessionTypedVolEvidenceError("horizon_mismatch_not_comparable")
    if a.annualized != f.annualized or a.annualized != CANONICAL_ANNUALIZED:
        raise MultiSessionTypedVolEvidenceError("annualization_mismatch_not_comparable")
    if a.estimator != f.estimator or a.estimator != CANONICAL_ESTIMATOR:
        raise MultiSessionTypedVolEvidenceError("estimator_mismatch_not_comparable")
    if a.estimator_version != f.estimator_version:
        raise MultiSessionTypedVolEvidenceError("estimator_version_mismatch_not_comparable")
    if a.contract_version != f.contract_version:
        raise MultiSessionTypedVolEvidenceError("contract_version_mismatch_not_comparable")


def clone_aged_estimate_immutable_v1(
    aged: CanonicalVolatilityEstimateV1,
) -> CanonicalVolatilityEstimateV1:
    """Return a validated copy; original must remain bitwise equal."""
    if not AGED_ESTIMATE_MUTATION_FORBIDDEN:
        raise MultiSessionTypedVolEvidenceError("aged_immutability_flag_drift")
    before = aged.to_dict()
    cloned = CanonicalVolatilityEstimateV1(**{**aged.__dict__})
    after = aged.to_dict()
    if before != after:
        raise MultiSessionTypedVolEvidenceError("aged_estimate_mutated")
    return validate_canonical_volatility_estimate_v1(cloned)


def materialize_fresh_estimate_from_mark_prices_v1(
    mark_prices: Sequence[float],
    *,
    event_times_utc: Sequence[datetime],
    as_of_event_time: datetime,
) -> CanonicalVolatilityEstimateV1:
    """Canonical materializer path only — no synthetic values."""
    if not FRESH_ESTIMATE_MUST_USE_CANONICAL_ESTIMATOR:
        raise MultiSessionTypedVolEvidenceError("canonical_estimator_flag_drift")
    if len(mark_prices) != len(event_times_utc):
        raise MultiSessionTypedVolEvidenceError("mark_price_event_time_length_mismatch")
    if len(mark_prices) < 2:
        raise MultiSessionTypedVolEvidenceError("insufficient_mark_prices_for_materializer")
    idx = pd.DatetimeIndex([pd.Timestamp(t) for t in event_times_utc])
    series = pd.Series([float(x) for x in mark_prices], index=idx, dtype=float)
    estimate = materialize_typed_canonical_volatility_estimate_v1(
        series,
        as_of_event_time=as_of_event_time.astimezone(timezone.utc),
    )
    _reject_synthetic_literals_v1(value=float(estimate.value), source="materializer")
    if estimate.estimator != CANONICAL_ESTIMATOR:
        raise MultiSessionTypedVolEvidenceError("non_canonical_estimator")
    if estimate.estimator_version != CANONICAL_ESTIMATOR_VERSION:
        raise MultiSessionTypedVolEvidenceError("non_canonical_estimator_version")
    if estimate.contract_version != SUPPORTED_CONTRACT_VERSION:
        raise MultiSessionTypedVolEvidenceError("unsupported_contract_version")
    return estimate


def build_typed_volatility_comparison_v1(
    *,
    session_id: str,
    market_sample_id: str,
    market_context_digest: str,
    aged_estimate: CanonicalVolatilityEstimateV1,
    fresh_estimate: Optional[CanonicalVolatilityEstimateV1],
    age_seconds: float,
    bindings: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build additive typed comparison record (no synthetic aged/fresh values)."""
    aged_copy = clone_aged_estimate_immutable_v1(aged_estimate)
    aged_rec = estimate_record_v1(aged_copy)
    status = "COMPARABLE"
    fresh_rec: Optional[dict[str, Any]] = None
    abs_drift = None
    rel_drift = None
    if fresh_estimate is None:
        status = "FRESH_ESTIMATE_UNAVAILABLE"
    else:
        assert_estimates_contract_compatible_v1(aged_copy, fresh_estimate)
        fresh_rec = estimate_record_v1(fresh_estimate)
        abs_drift = abs(float(fresh_estimate.value) - float(aged_copy.value))
        if float(aged_copy.value) == 0.0:
            rel_drift = None
        else:
            rel_drift = abs_drift / abs(float(aged_copy.value))
    payload: dict[str, Any] = {
        "schema": SCHEMA_TYPED_VOL_COMPARISON,
        "schema_version": "v1",
        "session_id": session_id,
        "market_sample_id": market_sample_id,
        "market_context_digest": market_context_digest,
        "age_seconds": float(age_seconds),
        "status": status,
        "AGED_ESTIMATE": aged_rec,
        "FRESH_ESTIMATE": fresh_rec,
        "absolute_drift": abs_drift,
        "relative_drift": rel_drift,
        "SYNTHETIC_VOLATILITY_VALUES_USED": False,
        "STATIC_VOLATILITY_DEFAULT_USED": False,
        "bindings": dict(bindings or {}),
    }
    payload["record_digest"] = sha256_hex_canonical(
        {k: v for k, v in payload.items() if k != "record_digest"}
    )
    # Prove aged immutability after comparison construction.
    if deepcopy(aged_estimate.to_dict()) != aged_estimate.to_dict():
        raise MultiSessionTypedVolEvidenceError("aged_estimate_deepcopy_drift")
    return payload
