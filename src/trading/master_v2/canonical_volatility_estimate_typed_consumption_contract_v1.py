"""Canonical volatility estimate typed consumption contract v1.

Typed carrier and fail-closed legacy-float adapter over the ratified
``canonical_volatility_estimate_feature_contract/v1`` and the existing
canonical materializer. Pure offline capability: no runtime wiring, no
trading-logic mutation, no parameter change, no hot-path binding.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping, Sequence

import pandas as pd

from src.trading.master_v2 import canonical_volatility_estimate_feature_contract_v1 as contract
from src.trading.master_v2 import canonical_volatility_estimate_materializer_v1 as materializer

PACKAGE_MARKER = "MASTER_V2_CANONICAL_VOLATILITY_ESTIMATE_TYPED_CONSUMPTION_CONTRACT_V1=true"

TYPED_CARRIER_OWNER = (
    "trading.master_v2.canonical_volatility_estimate_typed_consumption_contract_v1"
)
LEGACY_ADAPTER_OWNER = TYPED_CARRIER_OWNER
CAPABILITY_ID = "MASTER_V2_CANONICAL_VOLATILITY_ESTIMATE_TYPED_CONSUMPTION_CONTRACT_V1"
CAPABILITY_VERSION = "canonical_volatility_estimate_typed_consumption_contract/v1"

# Reuse ratified semantics / estimator owners — no parallel authority.
SEMANTICS_OWNER = contract.CONTRACT_OWNER
ESTIMATOR_OWNER = materializer.MATERIALIZER_OWNER

CANONICAL_UNIT = contract.OUTPUT_UNIT
CANONICAL_BAR_INTERVAL = contract.BAR_INTERVAL
CANONICAL_BAR_INTERVAL_SECONDS = materializer.BAR_INTERVAL_SECONDS
CANONICAL_LOOKBACK_BARS = contract.LOOKBACK_BARS
CANONICAL_HORIZON = contract.WINDOW_DURATION
CANONICAL_HORIZON_SECONDS = 3600
CANONICAL_ESTIMATOR = "POPULATION_STANDARD_DEVIATION_OF_LOG_RETURNS"
CANONICAL_DDOF = contract.DDOF
CANONICAL_ANNUALIZED = contract.OUTPUT_ANNUALIZED
MINIMUM_PRICE_OBSERVATIONS = contract.WARMUP_REQUIRED_PRICE_COUNT
MINIMUM_RETURN_OBSERVATIONS = contract.WARMUP_REQUIRED_RETURN_COUNT
SUPPORTED_CONTRACT_VERSION = contract.CONTRACT_VERSION

IMPLICIT_DEFAULT_ALLOWED = False
MV2_FALLBACK_0_2_ADMISSIBLE = False
WARMUP_BEHAVIOR = "NULL_FAIL_CLOSED"
RUNTIME_EFFECT = False
TRADING_LOGIC_EFFECT = False
PARAMETER_EFFECT = False
LIVE_AUTHORIZATION = False

# Explicit open remaining gaps after typed consumption + C1 binding (C2 closes G1/G2).
OPEN_HOT_PATH_GAPS: tuple[str, ...] = (
    "G3_UNTYPED_EXISTING_HOT_PATH_FLOAT",
    "G4_COMPETING_PRODUCERS_DIFFERENT_SCALING",
    "G5_PANEL_1H_REUSES_PT1M_LOOKBACK",
    "G6_MATERIALIZER_NOT_WIRED_TO_DOUBLE_PLAY",
    "G7_SEPARATE_SURVIVAL_AND_SUITABILITY_VOL_CONCEPTS",
    "G8_LEGACY_PATH_NOT_YET_GLOBALLY_ENFORCED",
    "G9_FUTURES_PROFILE_PRIMARY_METRIC_OQ001_OPEN",
)

# Non-alias surfaces — must not be treated as the canonical estimate.
NON_ALIAS_VOLATILITY_SURFACES: tuple[str, ...] = (
    "volatility_survival_ratio",
    "FuturesVolatilityProfile.realized_volatility",
    "volatility_profile_present",
    "regime analytics annualized volatility",
    "wallclock feature_regime_pipeline volatility",
    "research panel 1h volatility",
    "ATR",
)


class CanonicalVolatilityTypedConsumptionErrorCode(str, Enum):
    MISSING_VALUE = "MISSING_VALUE"
    NON_FINITE_VALUE = "NON_FINITE_VALUE"
    NEGATIVE_VALUE = "NEGATIVE_VALUE"
    UNIT_MISMATCH = "UNIT_MISMATCH"
    BAR_INTERVAL_MISMATCH = "BAR_INTERVAL_MISMATCH"
    LOOKBACK_MISMATCH = "LOOKBACK_MISMATCH"
    HORIZON_MISMATCH = "HORIZON_MISMATCH"
    ANNUALIZATION_MISMATCH = "ANNUALIZATION_MISMATCH"
    ESTIMATOR_MISMATCH = "ESTIMATOR_MISMATCH"
    INSUFFICIENT_OBSERVATIONS = "INSUFFICIENT_OBSERVATIONS"
    EVENT_TIME_INVALID = "EVENT_TIME_INVALID"
    FALLBACK_PROHIBITED = "FALLBACK_PROHIBITED"
    SOURCE_DIGEST_INVALID = "SOURCE_DIGEST_INVALID"
    CONTRACT_VERSION_UNSUPPORTED = "CONTRACT_VERSION_UNSUPPORTED"
    WARMUP_INCOMPLETE = "WARMUP_INCOMPLETE"
    UNKNOWN_PROVENANCE = "UNKNOWN_PROVENANCE"
    IMPLICIT_FALLBACK_REJECTED = "IMPLICIT_FALLBACK_REJECTED"


class CanonicalVolatilityTypedConsumptionError(ValueError):
    """Fail-closed typed consumption / adapter error with diagnostic code."""

    def __init__(
        self,
        code: CanonicalVolatilityTypedConsumptionErrorCode,
        message: str,
    ) -> None:
        self.code = code
        super().__init__(f"{code.value}:{message}")


@dataclass(frozen=True)
class CanonicalVolatilityEstimateV1:
    """Immutable typed carrier for a validated canonical volatility estimate."""

    value: float
    unit: str
    bar_interval_seconds: int
    lookback_bars: int
    horizon_seconds: int
    annualized: bool
    estimator: str
    observation_count: int
    as_of_event_time: datetime
    fallback_used: bool
    source_digest: str
    contract_version: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "value": self.value,
            "unit": self.unit,
            "bar_interval_seconds": self.bar_interval_seconds,
            "lookback_bars": self.lookback_bars,
            "horizon_seconds": self.horizon_seconds,
            "annualized": self.annualized,
            "estimator": self.estimator,
            "observation_count": self.observation_count,
            "as_of_event_time": self.as_of_event_time.isoformat(),
            "fallback_used": self.fallback_used,
            "source_digest": self.source_digest,
            "contract_version": self.contract_version,
        }


def _raise(
    code: CanonicalVolatilityTypedConsumptionErrorCode,
    message: str,
) -> None:
    raise CanonicalVolatilityTypedConsumptionError(code, message)


def compute_source_digest_v1(
    *,
    value: float,
    unit: str,
    bar_interval_seconds: int,
    lookback_bars: int,
    horizon_seconds: int,
    annualized: bool,
    estimator: str,
    observation_count: int,
    as_of_event_time: datetime,
    fallback_used: bool,
    contract_version: str,
    mark_prices: Sequence[float] | None = None,
) -> str:
    """Deterministic SHA-256 digest over carrier provenance fields (+ optional prices)."""
    payload: dict[str, Any] = {
        "annualized": annualized,
        "as_of_event_time": as_of_event_time.astimezone(timezone.utc).isoformat(),
        "bar_interval_seconds": bar_interval_seconds,
        "contract_version": contract_version,
        "estimator": estimator,
        "fallback_used": fallback_used,
        "horizon_seconds": horizon_seconds,
        "lookback_bars": lookback_bars,
        "observation_count": observation_count,
        "unit": unit,
        "value": value,
    }
    if mark_prices is not None:
        payload["mark_prices"] = [float(x) for x in mark_prices]
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def validate_canonical_volatility_estimate_v1(
    estimate: CanonicalVolatilityEstimateV1,
) -> CanonicalVolatilityEstimateV1:
    """Fail-closed validation of a typed canonical volatility estimate."""
    if estimate.value is None:  # type: ignore[comparison-overlap]
        _raise(
            CanonicalVolatilityTypedConsumptionErrorCode.MISSING_VALUE,
            "value_is_none",
        )
    if isinstance(estimate.value, bool) or not isinstance(estimate.value, (int, float)):
        _raise(
            CanonicalVolatilityTypedConsumptionErrorCode.MISSING_VALUE,
            f"value_type_invalid:{type(estimate.value).__name__}",
        )
    value = float(estimate.value)
    if not math.isfinite(value):
        _raise(
            CanonicalVolatilityTypedConsumptionErrorCode.NON_FINITE_VALUE,
            f"value={value!r}",
        )
    if value < 0.0:
        _raise(
            CanonicalVolatilityTypedConsumptionErrorCode.NEGATIVE_VALUE,
            f"value={value!r}",
        )
    if estimate.unit != CANONICAL_UNIT:
        _raise(
            CanonicalVolatilityTypedConsumptionErrorCode.UNIT_MISMATCH,
            f"expected={CANONICAL_UNIT!r}:actual={estimate.unit!r}",
        )
    if estimate.bar_interval_seconds != CANONICAL_BAR_INTERVAL_SECONDS:
        _raise(
            CanonicalVolatilityTypedConsumptionErrorCode.BAR_INTERVAL_MISMATCH,
            f"expected={CANONICAL_BAR_INTERVAL_SECONDS}:actual={estimate.bar_interval_seconds}",
        )
    if estimate.lookback_bars != CANONICAL_LOOKBACK_BARS:
        _raise(
            CanonicalVolatilityTypedConsumptionErrorCode.LOOKBACK_MISMATCH,
            f"expected={CANONICAL_LOOKBACK_BARS}:actual={estimate.lookback_bars}",
        )
    if estimate.horizon_seconds != CANONICAL_HORIZON_SECONDS:
        _raise(
            CanonicalVolatilityTypedConsumptionErrorCode.HORIZON_MISMATCH,
            f"expected={CANONICAL_HORIZON_SECONDS}:actual={estimate.horizon_seconds}",
        )
    if estimate.annualized is not CANONICAL_ANNUALIZED:
        _raise(
            CanonicalVolatilityTypedConsumptionErrorCode.ANNUALIZATION_MISMATCH,
            f"expected={CANONICAL_ANNUALIZED}:actual={estimate.annualized}",
        )
    if estimate.estimator != CANONICAL_ESTIMATOR:
        _raise(
            CanonicalVolatilityTypedConsumptionErrorCode.ESTIMATOR_MISMATCH,
            f"expected={CANONICAL_ESTIMATOR!r}:actual={estimate.estimator!r}",
        )
    if int(estimate.observation_count) < MINIMUM_RETURN_OBSERVATIONS:
        _raise(
            CanonicalVolatilityTypedConsumptionErrorCode.INSUFFICIENT_OBSERVATIONS,
            f"observation_count={estimate.observation_count}:minimum={MINIMUM_RETURN_OBSERVATIONS}",
        )
    as_of = estimate.as_of_event_time
    if not isinstance(as_of, datetime) or as_of.tzinfo is None:
        _raise(
            CanonicalVolatilityTypedConsumptionErrorCode.EVENT_TIME_INVALID,
            "as_of_event_time_must_be_timezone_aware",
        )
    if estimate.fallback_used is not False:
        _raise(
            CanonicalVolatilityTypedConsumptionErrorCode.FALLBACK_PROHIBITED,
            f"fallback_used={estimate.fallback_used!r}",
        )
    digest = estimate.source_digest
    if not isinstance(digest, str) or not digest.strip():
        _raise(
            CanonicalVolatilityTypedConsumptionErrorCode.SOURCE_DIGEST_INVALID,
            "source_digest_empty",
        )
    if estimate.contract_version != SUPPORTED_CONTRACT_VERSION:
        _raise(
            CanonicalVolatilityTypedConsumptionErrorCode.CONTRACT_VERSION_UNSUPPORTED,
            f"expected={SUPPORTED_CONTRACT_VERSION!r}:actual={estimate.contract_version!r}",
        )
    return estimate


def build_canonical_volatility_estimate_v1(
    *,
    value: float | None,
    unit: str = CANONICAL_UNIT,
    bar_interval_seconds: int = CANONICAL_BAR_INTERVAL_SECONDS,
    lookback_bars: int = CANONICAL_LOOKBACK_BARS,
    horizon_seconds: int = CANONICAL_HORIZON_SECONDS,
    annualized: bool = CANONICAL_ANNUALIZED,
    estimator: str = CANONICAL_ESTIMATOR,
    observation_count: int,
    as_of_event_time: datetime,
    fallback_used: bool = False,
    source_digest: str | None = None,
    contract_version: str = SUPPORTED_CONTRACT_VERSION,
    mark_prices: Sequence[float] | None = None,
) -> CanonicalVolatilityEstimateV1:
    """Factory that constructs and fail-closed validates a typed estimate."""
    if value is None:
        _raise(
            CanonicalVolatilityTypedConsumptionErrorCode.MISSING_VALUE,
            "value_is_none",
        )
    if fallback_used:
        _raise(
            CanonicalVolatilityTypedConsumptionErrorCode.FALLBACK_PROHIBITED,
            "fallback_used_true_rejected_at_factory",
        )
    digest = source_digest
    if digest is None:
        digest = compute_source_digest_v1(
            value=float(value),
            unit=unit,
            bar_interval_seconds=bar_interval_seconds,
            lookback_bars=lookback_bars,
            horizon_seconds=horizon_seconds,
            annualized=annualized,
            estimator=estimator,
            observation_count=observation_count,
            as_of_event_time=as_of_event_time,
            fallback_used=False,
            contract_version=contract_version,
            mark_prices=mark_prices,
        )
    estimate = CanonicalVolatilityEstimateV1(
        value=float(value),
        unit=unit,
        bar_interval_seconds=bar_interval_seconds,
        lookback_bars=lookback_bars,
        horizon_seconds=horizon_seconds,
        annualized=annualized,
        estimator=estimator,
        observation_count=int(observation_count),
        as_of_event_time=as_of_event_time,
        fallback_used=False,
        source_digest=digest,
        contract_version=contract_version,
    )
    return validate_canonical_volatility_estimate_v1(estimate)


def materialize_typed_canonical_volatility_estimate_v1(
    mark_prices: pd.Series,
    *,
    is_final: pd.Series | None = None,
    as_of_event_time: datetime | None = None,
) -> CanonicalVolatilityEstimateV1:
    """Pure boundary: mark prices → existing materializer → typed carrier.

    Reuses ``compute_canonical_volatility_estimate_from_mark_prices_v1``.
    Does not treat runtime cycle or poll count as market/observation time.
    """
    volatility = materializer.compute_canonical_volatility_estimate_from_mark_prices_v1(
        mark_prices,
        is_final=is_final,
    )
    valid = volatility.dropna()
    if valid.empty:
        _raise(
            CanonicalVolatilityTypedConsumptionErrorCode.WARMUP_INCOMPLETE,
            "no_valid_volatility_after_materialization",
        )
    last_ts = valid.index[-1]
    value = float(valid.iloc[-1])
    if as_of_event_time is None:
        ts = pd.Timestamp(last_ts)
        if ts.tzinfo is None:
            ts = ts.tz_localize("UTC")
        else:
            ts = ts.tz_convert("UTC")
        as_of = ts.to_pydatetime()
    else:
        as_of = as_of_event_time

    ordered = mark_prices.sort_index().astype(float)
    # observation_count = number of log-return observations contributing to the estimate
    # at the selected bar (= lookback when valid).
    observation_count = MINIMUM_RETURN_OBSERVATIONS
    prices_for_digest = ordered.loc[:last_ts].astype(float).tolist()
    if len(prices_for_digest) < MINIMUM_PRICE_OBSERVATIONS:
        _raise(
            CanonicalVolatilityTypedConsumptionErrorCode.INSUFFICIENT_OBSERVATIONS,
            f"price_observations={len(prices_for_digest)}:minimum={MINIMUM_PRICE_OBSERVATIONS}",
        )

    return build_canonical_volatility_estimate_v1(
        value=value,
        observation_count=observation_count,
        as_of_event_time=as_of,
        mark_prices=prices_for_digest[-MINIMUM_PRICE_OBSERVATIONS:],
    )


def adapt_canonical_volatility_estimate_to_legacy_float_v1(
    estimate: CanonicalVolatilityEstimateV1 | None,
) -> float:
    """Fail-closed adapter: typed estimate → legacy float consumer value.

    Performs no substitution. Rejects None, fallback, wrong unit/horizon,
    annualized inputs, insufficient observations, and unsupported versions.
    Does not invent 0.2 / 0.02 / 1.0.
    """
    if estimate is None:
        _raise(
            CanonicalVolatilityTypedConsumptionErrorCode.MISSING_VALUE,
            "estimate_is_none_no_substitution",
        )
    validated = validate_canonical_volatility_estimate_v1(estimate)
    # Numeric equality with legacy fallback constants is allowed only when the
    # estimate is fully provenance-valid (fallback_used=false already enforced).
    return float(validated.value)


def reject_implicit_legacy_float_input_v1(
    *,
    raw_value: float | None,
    provenance: Mapping[str, Any] | None,
) -> None:
    """Reject silent / unproven legacy float inputs on the new contract path.

    The numeric values 0.2, 0.02, and 1.0 are not globally banned. Their use as
    silent, unproven, or fallback-based contract input is rejected.
    """
    if provenance is None:
        _raise(
            CanonicalVolatilityTypedConsumptionErrorCode.UNKNOWN_PROVENANCE,
            "provenance_missing",
        )
    if raw_value is None:
        _raise(
            CanonicalVolatilityTypedConsumptionErrorCode.MISSING_VALUE,
            "raw_value_none_no_substitution",
        )
    if provenance.get("fallback_used") is True:
        _raise(
            CanonicalVolatilityTypedConsumptionErrorCode.FALLBACK_PROHIBITED,
            "fallback_used_in_provenance",
        )
    if provenance.get("implicit_default") is True:
        _raise(
            CanonicalVolatilityTypedConsumptionErrorCode.IMPLICIT_FALLBACK_REJECTED,
            "implicit_default_true",
        )
    if provenance.get("typed_estimate") is not True:
        # Unproven bare floats (including 0.2 / 0.02 / 1.0) are rejected.
        _raise(
            CanonicalVolatilityTypedConsumptionErrorCode.UNKNOWN_PROVENANCE,
            f"untyped_legacy_float_rejected:value={raw_value!r}",
        )


def assert_capability_non_goals_v1() -> dict[str, Any]:
    """Machine-readable non-goals / authority boundary for this capability."""
    return {
        "capability_id": CAPABILITY_ID,
        "capability_version": CAPABILITY_VERSION,
        "semantics_owner": SEMANTICS_OWNER,
        "estimator_owner": ESTIMATOR_OWNER,
        "typed_carrier_owner": TYPED_CARRIER_OWNER,
        "legacy_adapter_owner": LEGACY_ADAPTER_OWNER,
        "canonical_unit": CANONICAL_UNIT,
        "canonical_horizon": CANONICAL_HORIZON,
        "canonical_estimator": CANONICAL_ESTIMATOR,
        "observation_requirement": {
            "minimum_price_observations": MINIMUM_PRICE_OBSERVATIONS,
            "minimum_return_observations": MINIMUM_RETURN_OBSERVATIONS,
        },
        "unknown_behavior": "FAIL_CLOSED",
        "fallback_policy": "REJECT_FALLBACK_USED_AND_IMPLICIT_DEFAULTS",
        "non_goals": [
            "runtime_wiring",
            "hot_path_binding",
            "parameter_change",
            "trading_logic_change",
            "composition_change",
            "entry_exit_change",
            "survival_change",
            "suitability_change",
            "closing_open_hot_path_gaps",
            "aliasing_non_canonical_volatility_surfaces",
        ],
        "non_alias_surfaces": list(NON_ALIAS_VOLATILITY_SURFACES),
        "open_hot_path_gaps": list(OPEN_HOT_PATH_GAPS),
        "runtime_effect": RUNTIME_EFFECT,
        "trading_logic_effect": TRADING_LOGIC_EFFECT,
        "parameter_effect": PARAMETER_EFFECT,
        "live_authorization": LIVE_AUTHORIZATION,
        "implicit_default_allowed": IMPLICIT_DEFAULT_ALLOWED,
        "mv2_fallback_0_2_admissible": MV2_FALLBACK_0_2_ADMISSIBLE,
        "warmup_behavior": WARMUP_BEHAVIOR,
        "package_marker": PACKAGE_MARKER,
    }


def with_mutated_field_for_tests_v1(
    estimate: CanonicalVolatilityEstimateV1,
    **changes: Any,
) -> CanonicalVolatilityEstimateV1:
    """Test helper: produce a replaced carrier without re-validating."""
    return replace(estimate, **changes)


__all__ = [
    "CANONICAL_ANNUALIZED",
    "CANONICAL_BAR_INTERVAL",
    "CANONICAL_BAR_INTERVAL_SECONDS",
    "CANONICAL_DDOF",
    "CANONICAL_ESTIMATOR",
    "CANONICAL_HORIZON",
    "CANONICAL_HORIZON_SECONDS",
    "CANONICAL_LOOKBACK_BARS",
    "CANONICAL_UNIT",
    "CAPABILITY_ID",
    "CAPABILITY_VERSION",
    "CanonicalVolatilityEstimateV1",
    "CanonicalVolatilityTypedConsumptionError",
    "CanonicalVolatilityTypedConsumptionErrorCode",
    "ESTIMATOR_OWNER",
    "IMPLICIT_DEFAULT_ALLOWED",
    "LEGACY_ADAPTER_OWNER",
    "LIVE_AUTHORIZATION",
    "MINIMUM_PRICE_OBSERVATIONS",
    "MINIMUM_RETURN_OBSERVATIONS",
    "MV2_FALLBACK_0_2_ADMISSIBLE",
    "NON_ALIAS_VOLATILITY_SURFACES",
    "OPEN_HOT_PATH_GAPS",
    "PACKAGE_MARKER",
    "PARAMETER_EFFECT",
    "RUNTIME_EFFECT",
    "SEMANTICS_OWNER",
    "SUPPORTED_CONTRACT_VERSION",
    "TRADING_LOGIC_EFFECT",
    "TYPED_CARRIER_OWNER",
    "WARMUP_BEHAVIOR",
    "adapt_canonical_volatility_estimate_to_legacy_float_v1",
    "assert_capability_non_goals_v1",
    "build_canonical_volatility_estimate_v1",
    "compute_source_digest_v1",
    "materialize_typed_canonical_volatility_estimate_v1",
    "reject_implicit_legacy_float_input_v1",
    "validate_canonical_volatility_estimate_v1",
    "with_mutated_field_for_tests_v1",
]
