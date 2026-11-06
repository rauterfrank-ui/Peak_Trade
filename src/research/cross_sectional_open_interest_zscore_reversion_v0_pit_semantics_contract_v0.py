"""Point-in-time semantics contract for OKX open-interest z-score reversion v0.

Registers machine-readable PIT binding for cross_sectional_open_interest_zscore_reversion/v0.
Research-only; no runtime or authority effect.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.research.pit_futures_universe_manifest_v1 import compute_sha256_digest

PACKAGE_MARKER = "CROSS_SECTIONAL_OPEN_INTEREST_ZSCORE_REVERSION_V0_PIT_SEMANTICS_CONTRACT_V0=true"
CONTRACT_VERSION = "cross_sectional_open_interest_zscore_reversion_v0_pit_semantics_contract.v0"
RESEARCH_SCOPE = "cross_sectional_open_interest_zscore_reversion/v0"

SOURCE_ENDPOINT = "/api/v5/rubik/stat/contracts/open-interest-history"
SOURCE_OWNER = "okx_historical_open_interest_public_fetch_v0"
SOURCE_SCHEMA_VERSION = "okx_rubik_open_interest_history.v0"
VENUE = "OKX"
INSTRUMENT_TYPE = "linear_usdt_perpetual_swap"
OPEN_INTEREST_UNIT = "okx_native_contract_count"
BAR_INTERVAL = "PT1H"
OI_OBSERVATION_CADENCE = "PT1H"
SIGNAL_LAG_BARS = 1
STALE_THRESHOLD_BARS = 1
OPEN_INTEREST_LEVEL_DEFINITION = "point_in_time_open_interest_level_at_lagged_observation"
ZSCORE_NORMALIZATION = "population_std_cross_sectional_at_epoch"
ZERO_DISPERSION_POLICY = "fail_closed_flat_no_fallback"

FEATURE_TIME_LESS_THAN_OR_EQUAL_TO_ALLOWED_DECISION_TIME = True
INGESTION_TIME_IS_NOT_EVENT_TIME = True
NO_LOOKAHEAD = True
NO_SURVIVORSHIP_BIAS = True
NO_FUTURE_UNIVERSE_MEMBERSHIP_LEAKAGE = True
NO_SILENT_FORWARD_FILL = True
NO_INTERPOLATION = True
FINALIZED_BAR_ONLY = True


@dataclass(frozen=True)
class PitOpenInterestZscoreSemanticsContractV0:
    contract_version: str
    research_scope: str
    venue: str
    instrument_type: str
    source_endpoint: str
    source_owner: str
    source_schema_version: str
    open_interest_unit: str
    open_interest_level_definition: str
    zscore_normalization: str
    zero_dispersion_policy: str
    bar_interval: str
    oi_observation_cadence: str
    event_time_semantics: str
    availability_time_semantics: str
    signal_lag_bars: int
    stale_threshold_bars: int
    finalized_bar_only: bool
    duplicate_resolution: str
    missing_observation_handling: str
    stale_instrument_policy: str
    invalid_observation_policy: str
    listing_handling: str
    delisting_handling: str
    contract_replacement_handling: str
    no_lookahead: bool
    no_survivorship_bias: bool
    no_silent_forward_fill: bool
    no_interpolation: bool
    semantic_digest: str


def build_pit_open_interest_zscore_semantics_contract_v0() -> (
    PitOpenInterestZscoreSemanticsContractV0
):
    payload = {
        "contract_version": CONTRACT_VERSION,
        "research_scope": RESEARCH_SCOPE,
        "venue": VENUE,
        "instrument_type": INSTRUMENT_TYPE,
        "source_endpoint": SOURCE_ENDPOINT,
        "source_owner": SOURCE_OWNER,
        "source_schema_version": SOURCE_SCHEMA_VERSION,
        "open_interest_unit": OPEN_INTEREST_UNIT,
        "open_interest_level_definition": OPEN_INTEREST_LEVEL_DEFINITION,
        "zscore_normalization": ZSCORE_NORMALIZATION,
        "zero_dispersion_policy": ZERO_DISPERSION_POLICY,
        "bar_interval": BAR_INTERVAL,
        "oi_observation_cadence": OI_OBSERVATION_CADENCE,
        "event_time_semantics": "okx_oi_snapshot_timestamp_utc_at_or_before_bar_close",
        "availability_time_semantics": (
            "observation_time_utc_plus_signal_lag_bars_conservative_lag_no_lookahead"
        ),
        "signal_lag_bars": SIGNAL_LAG_BARS,
        "stale_threshold_bars": STALE_THRESHOLD_BARS,
        "finalized_bar_only": FINALIZED_BAR_ONLY,
        "duplicate_resolution": "latest_observation_timestamp_wins_stable_sort",
        "missing_observation_handling": "explicit_none_fail_closed_no_zero_fallback",
        "stale_instrument_policy": "exclude_when_staleness_exceeds_threshold_bars",
        "invalid_observation_policy": "exclude_non_finite_force_flat_at_selection",
        "listing_handling": "exclude_until_first_valid_oi_post_list_time",
        "delisting_handling": "force_flat_via_lifecycle_mask",
        "contract_replacement_handling": "lifecycle_registry_fail_closed_exclude_transition",
        "no_lookahead": NO_LOOKAHEAD,
        "no_survivorship_bias": NO_SURVIVORSHIP_BIAS,
        "no_silent_forward_fill": NO_SILENT_FORWARD_FILL,
        "no_interpolation": NO_INTERPOLATION,
    }
    digest = compute_sha256_digest(payload)
    return PitOpenInterestZscoreSemanticsContractV0(semantic_digest=digest, **payload)


def pit_semantics_contract_to_dict(
    contract: PitOpenInterestZscoreSemanticsContractV0,
) -> dict[str, object]:
    return {
        "contract_version": contract.contract_version,
        "research_scope": contract.research_scope,
        "venue": contract.venue,
        "instrument_type": contract.instrument_type,
        "source_endpoint": contract.source_endpoint,
        "source_owner": contract.source_owner,
        "source_schema_version": contract.source_schema_version,
        "open_interest_unit": contract.open_interest_unit,
        "open_interest_level_definition": contract.open_interest_level_definition,
        "zscore_normalization": contract.zscore_normalization,
        "zero_dispersion_policy": contract.zero_dispersion_policy,
        "bar_interval": contract.bar_interval,
        "oi_observation_cadence": contract.oi_observation_cadence,
        "event_time_semantics": contract.event_time_semantics,
        "availability_time_semantics": contract.availability_time_semantics,
        "signal_lag_bars": contract.signal_lag_bars,
        "stale_threshold_bars": contract.stale_threshold_bars,
        "finalized_bar_only": contract.finalized_bar_only,
        "duplicate_resolution": contract.duplicate_resolution,
        "missing_observation_handling": contract.missing_observation_handling,
        "stale_instrument_policy": contract.stale_instrument_policy,
        "invalid_observation_policy": contract.invalid_observation_policy,
        "listing_handling": contract.listing_handling,
        "delisting_handling": contract.delisting_handling,
        "contract_replacement_handling": contract.contract_replacement_handling,
        "feature_time_less_than_or_equal_to_allowed_decision_time": (
            FEATURE_TIME_LESS_THAN_OR_EQUAL_TO_ALLOWED_DECISION_TIME
        ),
        "ingestion_time_is_not_event_time": INGESTION_TIME_IS_NOT_EVENT_TIME,
        "no_lookahead": contract.no_lookahead,
        "no_survivorship_bias": contract.no_survivorship_bias,
        "no_silent_forward_fill": contract.no_silent_forward_fill,
        "no_interpolation": contract.no_interpolation,
        "semantic_digest": contract.semantic_digest,
    }
