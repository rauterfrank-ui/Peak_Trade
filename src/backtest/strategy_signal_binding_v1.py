"""
Strategy signal binding v1 for STEP 29M economic evaluation wiring.

Fail-closed execution and validation of configured registered strategy signals
before BacktestEngine ingestion. Separates canonical strategy signal series from
MV2 decision replay diagnostics.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping, Optional, Sequence

import pandas as pd

from src.strategies import load_strategy
from src.strategies.registry import (
    get_strategy_registry_entry,
    get_strategy_spec,
    resolve_strategy_id,
)

STRATEGY_SIGNAL_BINDING_LAYER_VERSION = "v1"
STRATEGY_SIGNAL_BINDING_OWNER = "backtest.strategy_signal_binding_v1"
ENGINE_SIGNAL_SOURCE_CONFIGURED_STRATEGY = "configured_strategy_signal"
STRATEGY_SIGNAL_SOURCE_CANONICAL = "canonical_strategy_signal_series"
MV2_REPLAY_SIGNAL_SOURCE = "mv2_decision_replay_series"

_ALLOWED_SIGNAL_VALUES = frozenset({-1, 0, 1})

# Registered legacy aliases only — no invented translations.
_CANONICAL_PARAM_ALIASES_V1: dict[str, dict[str, str]] = {
    "ma_crossover": {
        "fast_period": "fast_window",
        "slow_period": "slow_window",
    },
}


class StrategySignalBindingError(ValueError):
    """Fail-closed strategy signal binding error."""


class StrategyExecutionStatus(str, Enum):
    EXECUTED = "EXECUTED"
    BLOCKED = "BLOCKED"


class SignalContractStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"


class SignalAlignmentStatus(str, Enum):
    ALIGNED = "ALIGNED"
    FAIL = "FAIL"


class AllFlatSignalReason(str, Enum):
    NONE = "NONE"
    LEGITIMATE_STRATEGY_OUTPUT = "LEGITIMATE_STRATEGY_OUTPUT"


@dataclass(frozen=True)
class StrategySignalProvenanceV1:
    configured_strategy_id: str
    executed_strategy_id: str
    strategy_version: str
    strategy_owner: str
    configured_strategy_params: Mapping[str, Any]
    effective_strategy_params: Mapping[str, Any]
    strategy_params_digest: str
    strategy_execution_status: StrategyExecutionStatus
    strategy_signal_source: str
    strategy_signal_digest: str
    strategy_signal_count: int
    strategy_nonzero_signal_count: int
    strategy_signal_transition_count: int
    engine_signal_source: str
    engine_signal_digest: str
    engine_input_nonzero_signal_count: int
    signal_alignment_status: SignalAlignmentStatus
    signal_contract_status: SignalContractStatus
    all_flat_signal_reason: AllFlatSignalReason

    def to_dict(self) -> dict[str, Any]:
        return {
            "configured_strategy_id": self.configured_strategy_id,
            "executed_strategy_id": self.executed_strategy_id,
            "strategy_version": self.strategy_version,
            "strategy_owner": self.strategy_owner,
            "configured_strategy_params": dict(self.configured_strategy_params),
            "effective_strategy_params": dict(self.effective_strategy_params),
            "strategy_params_digest": self.strategy_params_digest,
            "strategy_execution_status": self.strategy_execution_status.value,
            "strategy_signal_source": self.strategy_signal_source,
            "strategy_signal_digest": self.strategy_signal_digest,
            "strategy_signal_count": self.strategy_signal_count,
            "strategy_nonzero_signal_count": self.strategy_nonzero_signal_count,
            "strategy_signal_transition_count": self.strategy_signal_transition_count,
            "engine_signal_source": self.engine_signal_source,
            "engine_signal_digest": self.engine_signal_digest,
            "engine_input_nonzero_signal_count": self.engine_input_nonzero_signal_count,
            "signal_alignment_status": self.signal_alignment_status.value,
            "signal_contract_status": self.signal_contract_status.value,
            "all_flat_signal_reason": self.all_flat_signal_reason.value,
        }


@dataclass(frozen=True)
class StrategySignalBindingResultV1:
    signals: pd.Series
    provenance: StrategySignalProvenanceV1


def _stable_digest(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _fail_closed(condition: bool, reason: str) -> None:
    if condition:
        raise StrategySignalBindingError(reason)


def compute_strategy_signal_digest_v1(
    signals: pd.Series,
    *,
    strategy_id: str,
    strategy_params_digest: str,
) -> str:
    return _stable_digest(
        {
            "strategy_id": strategy_id,
            "strategy_params_digest": strategy_params_digest,
            "index_start": str(signals.index[0]) if len(signals) else "empty",
            "index_end": str(signals.index[-1]) if len(signals) else "empty",
            "row_count": len(signals),
            "values_digest": _stable_digest(signals.astype(int).tolist()),
            "owner": STRATEGY_SIGNAL_BINDING_OWNER,
        }
    )


def collect_configured_strategy_params_v1(
    cfg: Mapping[str, Any],
    strategy_id: str,
) -> dict[str, Any]:
    """Collect explicit strategy params from evaluation config only."""
    params: dict[str, Any] = {}
    eval_section = cfg.get("economic_evaluation_v1")
    if isinstance(eval_section, Mapping):
        raw = eval_section.get("strategy_params")
        if isinstance(raw, Mapping):
            params.update(dict(raw))
    strategy_section = cfg.get("strategy")
    if isinstance(strategy_section, Mapping):
        raw = strategy_section.get(strategy_id)
        if isinstance(raw, Mapping):
            params.update(dict(raw))
    strategies_section = cfg.get("strategies")
    if isinstance(strategies_section, Mapping):
        raw = strategies_section.get(strategy_id)
        if isinstance(raw, Mapping):
            defaults = raw.get("defaults")
            if isinstance(defaults, Mapping):
                for key, value in defaults.items():
                    params.setdefault(key, value)
    return params


def _schema_param_names(strategy_id: str) -> tuple[str, ...]:
    try:
        spec = get_strategy_spec(strategy_id)
    except KeyError:
        return ()
    schema = getattr(spec.cls, "parameter_schema", None)
    if not schema:
        return ()
    return tuple(param.name for param in schema)


def _schema_defaults(strategy_id: str) -> dict[str, Any]:
    try:
        spec = get_strategy_spec(strategy_id)
    except KeyError:
        return {}
    schema = getattr(spec.cls, "parameter_schema", None)
    if not schema:
        return {}
    return {param.name: param.default for param in schema}


def resolve_effective_strategy_params_v1(
    strategy_id: str,
    configured_params: Mapping[str, Any],
) -> tuple[dict[str, Any], str]:
    """Fail-closed parameter normalization using registered schema and aliases."""
    aliases = _CANONICAL_PARAM_ALIASES_V1.get(strategy_id, {})
    allowed_input_keys = set(_schema_param_names(strategy_id)) | set(aliases.keys())
    allowed_effective_keys = set(_schema_param_names(strategy_id))

    normalized_input: dict[str, Any] = {}
    for key, value in configured_params.items():
        _fail_closed(key not in allowed_input_keys, f"unknown_strategy_param:{key}")
        target = aliases.get(key, key)
        _fail_closed(
            target not in allowed_effective_keys,
            f"unknown_effective_strategy_param:{target}",
        )
        normalized_input[target] = value

    effective = dict(_schema_defaults(strategy_id))
    effective.update(normalized_input)
    digest = _stable_digest(
        {
            "strategy_id": strategy_id,
            "effective_strategy_params": effective,
            "owner": STRATEGY_SIGNAL_BINDING_OWNER,
        }
    )
    return effective, digest


def validate_strategy_signal_contract_v1(
    signals: pd.Series,
    *,
    bars_index: pd.Index,
    strategy_id: str,
    strategy_params_digest: str,
) -> tuple[pd.Series, StrategySignalProvenanceV1]:
    _fail_closed(len(signals) == 0, "strategy_signals_empty")
    _fail_closed(
        not isinstance(signals.index, pd.DatetimeIndex), "strategy_signals_index_not_datetime"
    )
    _fail_closed(not signals.index.is_monotonic_increasing, "strategy_signals_index_not_monotonic")
    _fail_closed(signals.index.has_duplicates, "strategy_signals_duplicate_timestamps")

    if not signals.index.equals(bars_index):
        _fail_closed(len(signals.index) != len(bars_index), "strategy_signal_index_length_mismatch")
        _fail_closed(not signals.index.equals(bars_index), "strategy_signal_index_mismatch")

    if signals.isna().any():
        raise StrategySignalBindingError("strategy_signals_contain_nan")

    int_signals = signals.astype(int)
    unique_values = {int(v) for v in int_signals.unique()}
    unknown = unique_values - _ALLOWED_SIGNAL_VALUES
    _fail_closed(bool(unknown), f"unknown_signal_encoding:{sorted(unknown)}")

    transition_count = int((int_signals.diff().fillna(0) != 0).sum())
    nonzero_count = int((int_signals != 0).sum())
    all_flat_reason = AllFlatSignalReason.NONE
    if nonzero_count == 0:
        all_flat_reason = AllFlatSignalReason.LEGITIMATE_STRATEGY_OUTPUT

    entry = get_strategy_registry_entry(strategy_id)
    signal_digest = compute_strategy_signal_digest_v1(
        int_signals,
        strategy_id=strategy_id,
        strategy_params_digest=strategy_params_digest,
    )
    provenance = StrategySignalProvenanceV1(
        configured_strategy_id=strategy_id,
        executed_strategy_id=strategy_id,
        strategy_version=entry.strategy_version,
        strategy_owner=entry.implementation_ref,
        configured_strategy_params={},
        effective_strategy_params={},
        strategy_params_digest=strategy_params_digest,
        strategy_execution_status=StrategyExecutionStatus.EXECUTED,
        strategy_signal_source=STRATEGY_SIGNAL_SOURCE_CANONICAL,
        strategy_signal_digest=signal_digest,
        strategy_signal_count=len(int_signals),
        strategy_nonzero_signal_count=nonzero_count,
        strategy_signal_transition_count=transition_count,
        engine_signal_source=ENGINE_SIGNAL_SOURCE_CONFIGURED_STRATEGY,
        engine_signal_digest=signal_digest,
        engine_input_nonzero_signal_count=nonzero_count,
        signal_alignment_status=SignalAlignmentStatus.ALIGNED,
        signal_contract_status=SignalContractStatus.PASS,
        all_flat_signal_reason=all_flat_reason,
    )
    return int_signals, provenance


def execute_configured_strategy_signal_series_v1(
    bars: pd.DataFrame,
    *,
    strategy_id: str,
    cfg: Mapping[str, Any],
) -> StrategySignalBindingResultV1:
    """Execute configured registered strategy exactly once; fail-closed on contract violations."""
    _fail_closed(bars.empty, "bars_empty")
    resolution = resolve_strategy_id(strategy_id)
    canonical_id = resolution.canonical_strategy_id
    configured_params = collect_configured_strategy_params_v1(cfg, canonical_id)
    effective_params, params_digest = resolve_effective_strategy_params_v1(
        canonical_id,
        configured_params,
    )

    strategy_fn = load_strategy(canonical_id)
    raw_signals = strategy_fn(bars, effective_params)
    if not isinstance(raw_signals, pd.Series):
        raise StrategySignalBindingError("strategy_signal_not_series")

    validated_signals, provenance = validate_strategy_signal_contract_v1(
        raw_signals,
        bars_index=bars.index,
        strategy_id=canonical_id,
        strategy_params_digest=params_digest,
    )
    provenance = StrategySignalProvenanceV1(
        configured_strategy_id=strategy_id,
        executed_strategy_id=canonical_id,
        strategy_version=provenance.strategy_version,
        strategy_owner=provenance.strategy_owner,
        configured_strategy_params=dict(configured_params),
        effective_strategy_params=effective_params,
        strategy_params_digest=params_digest,
        strategy_execution_status=StrategyExecutionStatus.EXECUTED,
        strategy_signal_source=STRATEGY_SIGNAL_SOURCE_CANONICAL,
        strategy_signal_digest=provenance.strategy_signal_digest,
        strategy_signal_count=provenance.strategy_signal_count,
        strategy_nonzero_signal_count=provenance.strategy_nonzero_signal_count,
        strategy_signal_transition_count=provenance.strategy_signal_transition_count,
        engine_signal_source=ENGINE_SIGNAL_SOURCE_CONFIGURED_STRATEGY,
        engine_signal_digest=provenance.strategy_signal_digest,
        engine_input_nonzero_signal_count=provenance.engine_input_nonzero_signal_count,
        signal_alignment_status=provenance.signal_alignment_status,
        signal_contract_status=provenance.signal_contract_status,
        all_flat_signal_reason=provenance.all_flat_signal_reason,
    )
    return StrategySignalBindingResultV1(signals=validated_signals, provenance=provenance)


def assert_engine_signal_provenance_consistency_v1(
    provenance: StrategySignalProvenanceV1,
) -> None:
    _fail_closed(
        provenance.strategy_execution_status is not StrategyExecutionStatus.EXECUTED,
        "configured_strategy_not_executed",
    )
    _fail_closed(
        provenance.engine_signal_source != ENGINE_SIGNAL_SOURCE_CONFIGURED_STRATEGY,
        "engine_signal_source_not_explicit",
    )
    _fail_closed(
        provenance.strategy_signal_digest != provenance.engine_signal_digest,
        "strategy_engine_signal_digest_mismatch",
    )
    _fail_closed(
        provenance.signal_contract_status is not SignalContractStatus.PASS,
        "signal_contract_not_pass",
    )
    _fail_closed(
        provenance.signal_alignment_status is not SignalAlignmentStatus.ALIGNED,
        "signal_alignment_not_pass",
    )
