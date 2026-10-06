"""Canonical geometry volatility authority v1.

Sole productive σ owner for Golden Geometry Engine and geometry consumers.
Typed G17 carrier only; fail-closed; explicit instrument identity required.
Ranking and feature-regime volatility must not enter this boundary.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from trading.master_v2.canonical_market_context_v1 import CanonicalMarketContextV1
from trading.master_v2.canonical_volatility_binding_and_provenance_transport_v1 import (
    CanonicalVolatilityBindingError,
    adapt_validated_typed_estimate_to_legacy_float_v1,
    assert_typed_metadata_preserved_until_boundary_v1,
    compute_typed_estimate_digest_v1,
    validate_typed_estimate_for_cmc_binding_v1,
)
from trading.master_v2.canonical_volatility_estimate_feature_contract_v1 import OUTPUT_UNIT
from trading.master_v2.canonical_volatility_estimate_typed_consumption_contract_v1 import (
    CANONICAL_ESTIMATOR,
    CanonicalVolatilityEstimateV1,
)

GEOMETRY_VOLATILITY_OWNER = "trading.master_v2.canonical_geometry_volatility_v1"
GEOMETRY_VOLATILITY_UNIT = OUTPUT_UNIT


class CanonicalGeometryVolatilityErrorCode(str, Enum):
    BLANK_INSTRUMENT_ID = "BLANK_INSTRUMENT_ID"
    INSTRUMENT_ID_MISMATCH = "INSTRUMENT_ID_MISMATCH"
    MISSING_TYPED_ESTIMATE = "MISSING_TYPED_ESTIMATE"
    LEGACY_FLOAT_MISMATCH = "LEGACY_FLOAT_MISMATCH"
    INVALID_TYPED_ESTIMATE = "INVALID_TYPED_ESTIMATE"
    INCOMPATIBLE_VOLATILITY_REPRESENTATION = "INCOMPATIBLE_VOLATILITY_REPRESENTATION"


class CanonicalGeometryVolatilityError(ValueError):
    def __init__(self, code: CanonicalGeometryVolatilityErrorCode, message: str) -> None:
        self.code = code
        super().__init__(f"{code.value}:{message}")


def _raise(code: CanonicalGeometryVolatilityErrorCode, message: str) -> None:
    raise CanonicalGeometryVolatilityError(code, message)


@dataclass(frozen=True)
class CanonicalGeometryVolatilityV1:
    value: float
    unit: str
    instrument_id: str
    source_digest: str
    as_of_event_time: datetime
    typed_estimate_digest: str
    estimator: str


def _normalized_instrument_id(raw: str) -> str:
    return str(raw or "").strip()


def _assert_geometry_typed_semantics(estimate: CanonicalVolatilityEstimateV1) -> None:
    if str(estimate.unit) != GEOMETRY_VOLATILITY_UNIT:
        _raise(
            CanonicalGeometryVolatilityErrorCode.INCOMPATIBLE_VOLATILITY_REPRESENTATION,
            f"unit_must_be_{GEOMETRY_VOLATILITY_UNIT}",
        )
    if str(estimate.estimator) != CANONICAL_ESTIMATOR:
        _raise(
            CanonicalGeometryVolatilityErrorCode.INCOMPATIBLE_VOLATILITY_REPRESENTATION,
            "estimator_must_be_population_log_return",
        )


def resolve_canonical_geometry_volatility_v1(
    context: CanonicalMarketContextV1,
    *,
    bound_instrument_id: str | None = None,
) -> CanonicalGeometryVolatilityV1:
    """Resolve typed G17 geometry σ for the bound instrument; no legacy float fallback."""
    if not isinstance(context, CanonicalMarketContextV1):
        _raise(
            CanonicalGeometryVolatilityErrorCode.INVALID_TYPED_ESTIMATE,
            "context_not_canonical_market_context_v1",
        )

    effective_bound = _normalized_instrument_id(
        bound_instrument_id if bound_instrument_id is not None else context.instrument_id
    )
    if not effective_bound:
        _raise(
            CanonicalGeometryVolatilityErrorCode.BLANK_INSTRUMENT_ID,
            "productive_geometry_requires_non_blank_instrument_id",
        )

    cmc_id = _normalized_instrument_id(context.instrument_id)
    if cmc_id != effective_bound:
        _raise(
            CanonicalGeometryVolatilityErrorCode.INSTRUMENT_ID_MISMATCH,
            f"cmc_instrument_id={cmc_id!r}:bound={effective_bound!r}",
        )

    typed_estimate = context.canonical_volatility_estimate
    if typed_estimate is None:
        _raise(
            CanonicalGeometryVolatilityErrorCode.MISSING_TYPED_ESTIMATE,
            "geometry_volatility_requires_g17_typed_estimate",
        )

    try:
        assert_typed_metadata_preserved_until_boundary_v1(typed_estimate)
        validated = validate_typed_estimate_for_cmc_binding_v1(typed_estimate)
    except CanonicalVolatilityBindingError as exc:
        _raise(
            CanonicalGeometryVolatilityErrorCode.INVALID_TYPED_ESTIMATE,
            str(exc),
        )

    _assert_geometry_typed_semantics(validated)

    legacy = adapt_validated_typed_estimate_to_legacy_float_v1(
        validated,
        already_validated=True,
    )
    if float(context.volatility_estimate) != float(legacy):
        _raise(
            CanonicalGeometryVolatilityErrorCode.LEGACY_FLOAT_MISMATCH,
            "cmc_float_does_not_match_typed_geometry_adaptation",
        )

    return CanonicalGeometryVolatilityV1(
        value=float(legacy),
        unit=str(validated.unit),
        instrument_id=effective_bound,
        source_digest=str(validated.source_digest),
        as_of_event_time=validated.as_of_event_time,
        typed_estimate_digest=compute_typed_estimate_digest_v1(validated),
        estimator=str(validated.estimator),
    )


__all__ = [
    "CanonicalGeometryVolatilityError",
    "CanonicalGeometryVolatilityErrorCode",
    "CanonicalGeometryVolatilityV1",
    "GEOMETRY_VOLATILITY_OWNER",
    "GEOMETRY_VOLATILITY_UNIT",
    "resolve_canonical_geometry_volatility_v1",
]
