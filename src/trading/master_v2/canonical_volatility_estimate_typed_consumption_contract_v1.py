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
CANONICAL_ESTIMATOR_VERSION = "population_std_ddof_0/v1"
CANONICAL_DDOF = contract.DDOF
CANONICAL_ANNUALIZED = contract.OUTPUT_ANNUALIZED
CANONICAL_BAR_DURATION = contract.BAR_INTERVAL
MINIMUM_PRICE_OBSERVATIONS = contract.WARMUP_REQUIRED_PRICE_COUNT
MINIMUM_RETURN_OBSERVATIONS = contract.WARMUP_REQUIRED_RETURN_COUNT
SUPPORTED_CONTRACT_VERSION = contract.CONTRACT_VERSION
CANONICAL_PROVENANCE = "CANONICAL_MATERIALIZER_V1"
CANONICAL_DATA_QUALITY_TRUSTED = "TRUSTED"
NO_FALLBACK_IDENTITY = "NONE"

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
    ESTIMATOR_VERSION_MISMATCH = "ESTIMATOR_VERSION_MISMATCH"
    INSUFFICIENT_OBSERVATIONS = "INSUFFICIENT_OBSERVATIONS"
    EVENT_TIME_INVALID = "EVENT_TIME_INVALID"
    EVENT_TIME_ORDERING_INVALID = "EVENT_TIME_ORDERING_INVALID"
    FALLBACK_PROHIBITED = "FALLBACK_PROHIBITED"
    UNKNOWN_FALLBACK_IDENTITY = "UNKNOWN_FALLBACK_IDENTITY"
    SOURCE_DIGEST_INVALID = "SOURCE_DIGEST_INVALID"
    CONFIG_DIGEST_INVALID = "CONFIG_DIGEST_INVALID"
    CONTRACT_VERSION_UNSUPPORTED = "CONTRACT_VERSION_UNSUPPORTED"
    WARMUP_INCOMPLETE = "WARMUP_INCOMPLETE"
    UNKNOWN_PROVENANCE = "UNKNOWN_PROVENANCE"
    IMPLICIT_FALLBACK_REJECTED = "IMPLICIT_FALLBACK_REJECTED"
    DATA_QUALITY_INVALID = "DATA_QUALITY_INVALID"


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
    """Immutable typed carrier for a validated canonical volatility estimate.

    Also exposed as ``VolatilityEstimateV1`` for the hot-path closure contract.
    """

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
    estimator_version: str = CANONICAL_ESTIMATOR_VERSION
    minimum_observation_count: int = MINIMUM_RETURN_OBSERVATIONS
    bar_duration: str = CANONICAL_BAR_DURATION
    oldest_observation_event_time: datetime | None = None
    config_digest: str = ""
    fallback_identity: str = NO_FALLBACK_IDENTITY
    provenance: str = CANONICAL_PROVENANCE
    data_quality: str = CANONICAL_DATA_QUALITY_TRUSTED

    def to_dict(self) -> dict[str, Any]:
        oldest = self.oldest_observation_event_time
        return {
            "value": self.value,
            "unit": self.unit,
            "bar_interval_seconds": self.bar_interval_seconds,
            "lookback_bars": self.lookback_bars,
            "horizon_seconds": self.horizon_seconds,
            "annualized": self.annualized,
            "estimator": self.estimator,
            "estimator_version": self.estimator_version,
            "observation_count": self.observation_count,
            "minimum_observation_count": self.minimum_observation_count,
            "bar_duration": self.bar_duration,
            "as_of_event_time": self.as_of_event_time.isoformat(),
            "oldest_observation_event_time": (None if oldest is None else oldest.isoformat()),
            "fallback_used": self.fallback_used,
            "fallback_identity": self.fallback_identity,
            "source_digest": self.source_digest,
            "config_digest": self.config_digest,
            "provenance": self.provenance,
            "data_quality": self.data_quality,
            "contract_version": self.contract_version,
        }


# Hot-path closure alias — single productive typed carrier (no parallel type).
VolatilityEstimateV1 = CanonicalVolatilityEstimateV1


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
    if estimate.estimator_version != CANONICAL_ESTIMATOR_VERSION:
        _raise(
            CanonicalVolatilityTypedConsumptionErrorCode.ESTIMATOR_VERSION_MISMATCH,
            f"expected={CANONICAL_ESTIMATOR_VERSION!r}:actual={estimate.estimator_version!r}",
        )
    if int(estimate.minimum_observation_count) != MINIMUM_RETURN_OBSERVATIONS:
        _raise(
            CanonicalVolatilityTypedConsumptionErrorCode.INSUFFICIENT_OBSERVATIONS,
            (
                f"minimum_observation_count={estimate.minimum_observation_count}"
                f":expected={MINIMUM_RETURN_OBSERVATIONS}"
            ),
        )
    if int(estimate.observation_count) < MINIMUM_RETURN_OBSERVATIONS:
        _raise(
            CanonicalVolatilityTypedConsumptionErrorCode.INSUFFICIENT_OBSERVATIONS,
            f"observation_count={estimate.observation_count}:minimum={MINIMUM_RETURN_OBSERVATIONS}",
        )
    if estimate.bar_duration != CANONICAL_BAR_DURATION:
        _raise(
            CanonicalVolatilityTypedConsumptionErrorCode.BAR_INTERVAL_MISMATCH,
            f"expected={CANONICAL_BAR_DURATION!r}:actual={estimate.bar_duration!r}",
        )
    as_of = estimate.as_of_event_time
    if not isinstance(as_of, datetime) or as_of.tzinfo is None:
        _raise(
            CanonicalVolatilityTypedConsumptionErrorCode.EVENT_TIME_INVALID,
            "as_of_event_time_must_be_timezone_aware",
        )
    oldest = estimate.oldest_observation_event_time
    if oldest is None or not isinstance(oldest, datetime) or oldest.tzinfo is None:
        _raise(
            CanonicalVolatilityTypedConsumptionErrorCode.EVENT_TIME_INVALID,
            "oldest_observation_event_time_must_be_timezone_aware",
        )
    if oldest.astimezone(timezone.utc) > as_of.astimezone(timezone.utc):
        _raise(
            CanonicalVolatilityTypedConsumptionErrorCode.EVENT_TIME_ORDERING_INVALID,
            "oldest_observation_event_time_after_as_of_event_time",
        )
    if estimate.fallback_used is not False:
        _raise(
            CanonicalVolatilityTypedConsumptionErrorCode.FALLBACK_PROHIBITED,
            f"fallback_used={estimate.fallback_used!r}",
        )
    if estimate.fallback_identity != NO_FALLBACK_IDENTITY:
        _raise(
            CanonicalVolatilityTypedConsumptionErrorCode.UNKNOWN_FALLBACK_IDENTITY,
            f"fallback_identity={estimate.fallback_identity!r}",
        )
    digest = estimate.source_digest
    if not isinstance(digest, str) or not digest.strip():
        _raise(
            CanonicalVolatilityTypedConsumptionErrorCode.SOURCE_DIGEST_INVALID,
            "source_digest_empty",
        )
    config_digest = estimate.config_digest
    if (
        not isinstance(config_digest, str)
        or len(config_digest) != 64
        or any(c not in "0123456789abcdef" for c in config_digest)
    ):
        _raise(
            CanonicalVolatilityTypedConsumptionErrorCode.CONFIG_DIGEST_INVALID,
            "config_digest_must_be_64_char_lowercase_sha256",
        )
    if estimate.provenance != CANONICAL_PROVENANCE:
        _raise(
            CanonicalVolatilityTypedConsumptionErrorCode.UNKNOWN_PROVENANCE,
            f"provenance={estimate.provenance!r}",
        )
    if estimate.data_quality != CANONICAL_DATA_QUALITY_TRUSTED:
        _raise(
            CanonicalVolatilityTypedConsumptionErrorCode.DATA_QUALITY_INVALID,
            f"data_quality={estimate.data_quality!r}",
        )
    if estimate.contract_version != SUPPORTED_CONTRACT_VERSION:
        _raise(
            CanonicalVolatilityTypedConsumptionErrorCode.CONTRACT_VERSION_UNSUPPORTED,
            f"expected={SUPPORTED_CONTRACT_VERSION!r}:actual={estimate.contract_version!r}",
        )
    return estimate


def resolve_canonical_config_digest_v1(*, root: Any = None) -> str:
    """Deterministic digest of the ratified feature-contract config (single owner)."""
    from pathlib import Path

    cfg_root = None if root is None else Path(root)
    payload = contract.load_contract_config_v1(cfg_root)
    return contract.compute_contract_digest_v1(payload)


def build_canonical_volatility_estimate_v1(
    *,
    value: float | None,
    unit: str = CANONICAL_UNIT,
    bar_interval_seconds: int = CANONICAL_BAR_INTERVAL_SECONDS,
    lookback_bars: int = CANONICAL_LOOKBACK_BARS,
    horizon_seconds: int = CANONICAL_HORIZON_SECONDS,
    annualized: bool = CANONICAL_ANNUALIZED,
    estimator: str = CANONICAL_ESTIMATOR,
    estimator_version: str = CANONICAL_ESTIMATOR_VERSION,
    observation_count: int,
    minimum_observation_count: int = MINIMUM_RETURN_OBSERVATIONS,
    bar_duration: str = CANONICAL_BAR_DURATION,
    as_of_event_time: datetime,
    oldest_observation_event_time: datetime | None = None,
    fallback_used: bool = False,
    fallback_identity: str = NO_FALLBACK_IDENTITY,
    source_digest: str | None = None,
    config_digest: str | None = None,
    provenance: str = CANONICAL_PROVENANCE,
    data_quality: str = CANONICAL_DATA_QUALITY_TRUSTED,
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
    if fallback_identity != NO_FALLBACK_IDENTITY:
        _raise(
            CanonicalVolatilityTypedConsumptionErrorCode.UNKNOWN_FALLBACK_IDENTITY,
            "unknown_fallback_identity_rejected_at_factory",
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
    oldest = oldest_observation_event_time
    if oldest is None:
        # Closed PT60M window: as_of minus (lookback_bars) × PT1M.
        from datetime import timedelta

        oldest = as_of_event_time - timedelta(
            seconds=int(bar_interval_seconds) * int(lookback_bars)
        )
    cfg_digest = (
        config_digest if config_digest is not None else resolve_canonical_config_digest_v1()
    )
    estimate = CanonicalVolatilityEstimateV1(
        value=float(value),
        unit=unit,
        bar_interval_seconds=bar_interval_seconds,
        lookback_bars=lookback_bars,
        horizon_seconds=horizon_seconds,
        annualized=annualized,
        estimator=estimator,
        estimator_version=estimator_version,
        observation_count=int(observation_count),
        minimum_observation_count=int(minimum_observation_count),
        bar_duration=bar_duration,
        as_of_event_time=as_of_event_time,
        oldest_observation_event_time=oldest,
        fallback_used=False,
        fallback_identity=NO_FALLBACK_IDENTITY,
        source_digest=digest,
        config_digest=cfg_digest,
        provenance=provenance,
        data_quality=data_quality,
        contract_version=contract_version,
    )
    return validate_canonical_volatility_estimate_v1(estimate)


def derive_return_observation_count_from_closed_window_v1(
    mark_prices: pd.Series,
    *,
    as_of_index: Any,
) -> int:
    """Derive observation_count from the closed log-return window used by P1.

    Delegates to the materializer provenance helper — no parallel estimator.
    When a valid estimate exists, the trailing ``LOOKBACK_BARS`` finite returns
    are the contributing observations (not a blind constant hardcode).
    """
    return materializer.count_closed_return_observations_v1(
        mark_prices,
        as_of_index=as_of_index,
    )


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
    # observation_count provenance: closed return window actually used by P1.
    observation_count = derive_return_observation_count_from_closed_window_v1(
        ordered,
        as_of_index=last_ts,
    )
    prices_for_digest = ordered.loc[:last_ts].astype(float).tolist()
    if len(prices_for_digest) < MINIMUM_PRICE_OBSERVATIONS:
        _raise(
            CanonicalVolatilityTypedConsumptionErrorCode.INSUFFICIENT_OBSERVATIONS,
            f"price_observations={len(prices_for_digest)}:minimum={MINIMUM_PRICE_OBSERVATIONS}",
        )
    if observation_count < MINIMUM_RETURN_OBSERVATIONS:
        _raise(
            CanonicalVolatilityTypedConsumptionErrorCode.INSUFFICIENT_OBSERVATIONS,
            f"return_observations={observation_count}:minimum={MINIMUM_RETURN_OBSERVATIONS}",
        )

    window_prices = ordered.loc[:last_ts].iloc[-MINIMUM_PRICE_OBSERVATIONS:]
    oldest_ts = pd.Timestamp(window_prices.index[0])
    if oldest_ts.tzinfo is None:
        oldest_ts = oldest_ts.tz_localize("UTC")
    else:
        oldest_ts = oldest_ts.tz_convert("UTC")

    return build_canonical_volatility_estimate_v1(
        value=value,
        observation_count=observation_count,
        as_of_event_time=as_of,
        oldest_observation_event_time=oldest_ts.to_pydatetime(),
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
    "CANONICAL_BAR_DURATION",
    "CANONICAL_BAR_INTERVAL",
    "CANONICAL_BAR_INTERVAL_SECONDS",
    "CANONICAL_DATA_QUALITY_TRUSTED",
    "CANONICAL_DDOF",
    "CANONICAL_ESTIMATOR",
    "CANONICAL_ESTIMATOR_VERSION",
    "CANONICAL_HORIZON",
    "CANONICAL_HORIZON_SECONDS",
    "CANONICAL_LOOKBACK_BARS",
    "CANONICAL_PROVENANCE",
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
    "NO_FALLBACK_IDENTITY",
    "NON_ALIAS_VOLATILITY_SURFACES",
    "OPEN_HOT_PATH_GAPS",
    "PACKAGE_MARKER",
    "PARAMETER_EFFECT",
    "RUNTIME_EFFECT",
    "SEMANTICS_OWNER",
    "SUPPORTED_CONTRACT_VERSION",
    "TRADING_LOGIC_EFFECT",
    "TYPED_CARRIER_OWNER",
    "VolatilityEstimateV1",
    "WARMUP_BEHAVIOR",
    "adapt_canonical_volatility_estimate_to_legacy_float_v1",
    "assert_capability_non_goals_v1",
    "build_canonical_volatility_estimate_v1",
    "compute_source_digest_v1",
    "derive_return_observation_count_from_closed_window_v1",
    "materialize_typed_canonical_volatility_estimate_v1",
    "reject_implicit_legacy_float_input_v1",
    "resolve_canonical_config_digest_v1",
    "validate_canonical_volatility_estimate_v1",
    "with_mutated_field_for_tests_v1",
]
