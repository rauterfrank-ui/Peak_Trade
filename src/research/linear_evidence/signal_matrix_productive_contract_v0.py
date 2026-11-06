"""Operator-ratified productive normative contract for offline signal matrix join v0.

Offline-only, authority-neutral contract owner for final research fleet signal
matrix productive input join. No IO, runtime, trading logic, or strategy
duplication.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, Sequence

from src.research.linear_evidence.factor_exposure_productive_contract_v0 import (
    AUTHORITY_EFFECT,
    RUNTIME_EFFECT,
    stable_digest_v0,
)

PACKAGE_MARKER = "OFFLINE_SIGNAL_MATRIX_PRODUCTIVE_CONTRACT_V0=true"

JOIN_CONTRACT_VERSION = "offline_final_research_fleet_signal_matrix_join_v0"
BINDING_CONTRACT_VERSION = "offline_final_research_fleet_signal_matrix_binding_v0"
PROVENANCE_CONTRACT_VERSION = "offline_final_research_fleet_signal_matrix_provenance_v0"

RATIFIED_BINDING_SOURCE = (
    "config/research/final_research_fleet_versioned_binding_completion_v0.json"
)
RATIFIED_FLEET_SIGNAL_IDS: tuple[str, ...] = (
    "bollinger_bands",
    "momentum_1h",
    "trend_following",
)
EXPECTED_FLEET_SIGNAL_ORDER: tuple[str, ...] = tuple(sorted(RATIFIED_FLEET_SIGNAL_IDS))
DECISION_TIME_KEY = "decision_time"
FEATURE_TIME_KEY = "feature_time"
INSTRUMENT_ID_KEY = "instrument_id"
ROW_GRAIN = "instrument_id + decision_time"
TIMESTAMP_SEMANTICS = "utc_bar_close_exclusive_end"
BAR_GRANULARITY = "PT1H"
SIGNAL_VALUE_DOMAIN = "integer_discrete_-1_0_1_as_float"
ALLOWED_SIGNAL_VALUES: frozenset[int] = frozenset({-1, 0, 1})


class ProductiveSignalJoinRejectionReason(str, Enum):
    UNKNOWN_SIGNAL = "UNKNOWN_SIGNAL"
    EXTRA_SIGNAL = "EXTRA_SIGNAL"
    MISSING_SIGNAL_SOURCE = "MISSING_SIGNAL_SOURCE"
    UNFINALIZED_BAR = "UNFINALIZED_BAR"
    LOOKAHEAD_DETECTED = "LOOKAHEAD_DETECTED"
    DUPLICATE_TIMESTAMP = "DUPLICATE_TIMESTAMP"
    OUT_OF_ORDER_TIMESTAMP = "OUT_OF_ORDER_TIMESTAMP"
    WARMUP_EXCLUDED = "WARMUP_EXCLUDED"
    MISSING_SIGNAL_VALUE = "MISSING_SIGNAL_VALUE"
    NON_FINITE_SIGNAL_VALUE = "NON_FINITE_SIGNAL_VALUE"
    INVALID_SIGNAL_ENCODING = "INVALID_SIGNAL_ENCODING"
    INSTRUMENT_NOT_IN_BINDING = "INSTRUMENT_NOT_IN_BINDING"
    OUTSIDE_COVERAGE_PERIOD = "OUTSIDE_COVERAGE_PERIOD"
    INNER_JOIN_MISS = "INNER_JOIN_MISS"
    STRATEGY_EXECUTION_FAILED = "STRATEGY_EXECUTION_FAILED"


@dataclass(frozen=True)
class SignalMatrixJoinContractV0:
    contract_version: str = JOIN_CONTRACT_VERSION
    row_grain: str = ROW_GRAIN
    primary_join_key: str = INSTRUMENT_ID_KEY
    secondary_join_key: str = DECISION_TIME_KEY
    feature_time_key: str = FEATURE_TIME_KEY
    signal_column_order: tuple[str, ...] = EXPECTED_FLEET_SIGNAL_ORDER
    validation_policy: str = "TIME_ORDERED"
    finalized_bar_only: bool = True
    no_lookahead: bool = True
    forward_fill_allowed: bool = False
    backfill_allowed: bool = False
    synthetic_signal_allowed: bool = False
    fixture_signal_allowed: bool = False


@dataclass(frozen=True)
class SignalMatrixBindingV0:
    contract_version: str = BINDING_CONTRACT_VERSION
    binding_source_path: str = RATIFIED_BINDING_SOURCE
    binding_digest: str = ""
    strategy_bindings: tuple[Mapping[str, Any], ...] = ()
    signal_column_order: tuple[str, ...] = EXPECTED_FLEET_SIGNAL_ORDER
    instrument_ids: tuple[str, ...] = ()
    coverage_period_start_utc: str = ""
    coverage_period_end_utc: str = ""
    dataset_id: str = ""
    dataset_digest: str = ""
    panel_dataset_digest: str = ""
    finalized_bar_only: bool = True
    no_lookahead: bool = True
    authority_effect: str = AUTHORITY_EFFECT
    runtime_effect: str = RUNTIME_EFFECT

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract_version": self.contract_version,
            "binding_source_path": self.binding_source_path,
            "binding_digest": self.binding_digest,
            "strategy_bindings": [dict(item) for item in self.strategy_bindings],
            "signal_column_order": list(self.signal_column_order),
            "instrument_ids": list(self.instrument_ids),
            "coverage_period_start_utc": self.coverage_period_start_utc,
            "coverage_period_end_utc": self.coverage_period_end_utc,
            "dataset_id": self.dataset_id,
            "dataset_digest": self.dataset_digest,
            "panel_dataset_digest": self.panel_dataset_digest,
            "finalized_bar_only": self.finalized_bar_only,
            "no_lookahead": self.no_lookahead,
            "authority_effect": self.authority_effect,
            "runtime_effect": self.runtime_effect,
        }


@dataclass(frozen=True)
class SignalMatrixProductiveProvenanceV0:
    contract_version: str = PROVENANCE_CONTRACT_VERSION
    binding_source_path: str = RATIFIED_BINDING_SOURCE
    binding_digest: str = ""
    strategy_ids: tuple[str, ...] = EXPECTED_FLEET_SIGNAL_ORDER
    strategy_versions: tuple[str, ...] = ("v1", "v1", "v1")
    parameter_config_digests: dict[str, str] = field(default_factory=dict)
    dataset_id: str = ""
    dataset_digest: str = ""
    panel_dataset_digest: str = ""
    instrument_ids: tuple[str, ...] = ()
    instrument_universe_digest: str = ""
    coverage_period_start_utc: str = ""
    coverage_period_end_utc: str = ""
    row_count_before_join: int = 0
    row_count_after_join: int = 0
    dropped_rows_by_reason: dict[str, int] = field(default_factory=dict)
    per_signal_null_count: dict[str, int] = field(default_factory=dict)
    per_signal_warmup_exclusion_count: dict[str, int] = field(default_factory=dict)
    finalized_bar_only: bool = True
    no_lookahead: bool = True
    signal_matrix_digest: str = ""
    implementation_digest: str = ""
    join_contract_version: str = JOIN_CONTRACT_VERSION
    authority_effect: str = AUTHORITY_EFFECT
    runtime_effect: str = RUNTIME_EFFECT

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract_version": self.contract_version,
            "binding_source_path": self.binding_source_path,
            "binding_digest": self.binding_digest,
            "strategy_ids": list(self.strategy_ids),
            "strategy_versions": list(self.strategy_versions),
            "parameter_config_digests": dict(self.parameter_config_digests),
            "dataset_id": self.dataset_id,
            "dataset_digest": self.dataset_digest,
            "panel_dataset_digest": self.panel_dataset_digest,
            "instrument_ids": list(self.instrument_ids),
            "instrument_universe_digest": self.instrument_universe_digest,
            "coverage_period_start_utc": self.coverage_period_start_utc,
            "coverage_period_end_utc": self.coverage_period_end_utc,
            "row_count_before_join": self.row_count_before_join,
            "row_count_after_join": self.row_count_after_join,
            "dropped_rows_by_reason": dict(self.dropped_rows_by_reason),
            "per_signal_null_count": dict(self.per_signal_null_count),
            "per_signal_warmup_exclusion_count": dict(self.per_signal_warmup_exclusion_count),
            "finalized_bar_only": self.finalized_bar_only,
            "no_lookahead": self.no_lookahead,
            "signal_matrix_digest": self.signal_matrix_digest,
            "implementation_digest": self.implementation_digest,
            "join_contract_version": self.join_contract_version,
            "authority_effect": self.authority_effect,
            "runtime_effect": self.runtime_effect,
        }


def compute_warmup_rows_v0(strategy_id: str, parameter_binding: Mapping[str, Any]) -> int:
    if strategy_id == "trend_following":
        adx_period = int(parameter_binding["adx_period"])
        if parameter_binding.get("use_ma_filter"):
            return max(adx_period, int(parameter_binding["ma_period"]))
        return adx_period
    if strategy_id == "bollinger_bands":
        return int(parameter_binding["bb_period"])
    if strategy_id == "momentum_1h":
        return int(parameter_binding["lookback_period"])
    raise ValueError(ProductiveSignalJoinRejectionReason.UNKNOWN_SIGNAL.value)


def validate_requested_signal_set_v0(signal_ids: Sequence[str]) -> tuple[str, ...]:
    requested = tuple(sorted(str(name) for name in signal_ids))
    if not requested:
        raise ValueError(ProductiveSignalJoinRejectionReason.MISSING_SIGNAL_SOURCE.value)
    unknown = set(requested) - set(RATIFIED_FLEET_SIGNAL_IDS)
    if unknown:
        raise ValueError(ProductiveSignalJoinRejectionReason.UNKNOWN_SIGNAL.value)
    extra = set(requested) - set(RATIFIED_FLEET_SIGNAL_IDS)
    if extra:
        raise ValueError(ProductiveSignalJoinRejectionReason.EXTRA_SIGNAL.value)
    if set(requested) != set(RATIFIED_FLEET_SIGNAL_IDS):
        raise ValueError(ProductiveSignalJoinRejectionReason.EXTRA_SIGNAL.value)
    return EXPECTED_FLEET_SIGNAL_ORDER


def compute_signal_matrix_digest_v0(rows: Sequence[Mapping[str, Any]]) -> str:
    payload = [
        {
            "instrument_id": row.get(INSTRUMENT_ID_KEY),
            DECISION_TIME_KEY: row.get(DECISION_TIME_KEY),
            FEATURE_TIME_KEY: row.get(FEATURE_TIME_KEY),
            **{name: row.get(name) for name in EXPECTED_FLEET_SIGNAL_ORDER},
        }
        for row in rows
    ]
    return stable_digest_v0(
        {
            "contract": JOIN_CONTRACT_VERSION,
            "signal_column_order": list(EXPECTED_FLEET_SIGNAL_ORDER),
            "rows": payload,
        }
    )


def compute_instrument_universe_digest_v0(instrument_ids: Sequence[str]) -> str:
    unique_sorted = sorted({str(value) for value in instrument_ids if str(value)})
    return stable_digest_v0(
        {
            "contract": "offline_signal_matrix_instrument_universe_v0",
            "instrument_ids": unique_sorted,
        }
    )


__all__ = [
    "ALLOWED_SIGNAL_VALUES",
    "AUTHORITY_EFFECT",
    "BAR_GRANULARITY",
    "BINDING_CONTRACT_VERSION",
    "DECISION_TIME_KEY",
    "EXPECTED_FLEET_SIGNAL_ORDER",
    "FEATURE_TIME_KEY",
    "INSTRUMENT_ID_KEY",
    "JOIN_CONTRACT_VERSION",
    "PACKAGE_MARKER",
    "PROVENANCE_CONTRACT_VERSION",
    "RATIFIED_BINDING_SOURCE",
    "RATIFIED_FLEET_SIGNAL_IDS",
    "RUNTIME_EFFECT",
    "SIGNAL_VALUE_DOMAIN",
    "TIMESTAMP_SEMANTICS",
    "ProductiveSignalJoinRejectionReason",
    "SignalMatrixBindingV0",
    "SignalMatrixJoinContractV0",
    "SignalMatrixProductiveProvenanceV0",
    "compute_instrument_universe_digest_v0",
    "compute_signal_matrix_digest_v0",
    "compute_warmup_rows_v0",
    "validate_requested_signal_set_v0",
]
