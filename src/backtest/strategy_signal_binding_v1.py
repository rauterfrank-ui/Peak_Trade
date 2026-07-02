"""
Strategy signal binding v1 for STEP 29M economic evaluation wiring.

Fail-closed execution and validation of configured registered strategy signals
before BacktestEngine ingestion. Separates canonical strategy signal series from
MV2 decision replay diagnostics.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping, Optional, Sequence

import pandas as pd

from src.strategies import load_strategy
from src.strategies.breakout_confirmation_v1 import (
    CONFIRMATION_EPOCHS_V1,
    generate_confirmed_breakout_signals_v1,
)
from src.strategies.composite import CompositeStrategy
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

# External binding schema for strategies without class-level parameter_schema (macd v1).
_EXTERNAL_PARAMETER_SCHEMA_V1: dict[str, dict[str, Any]] = {
    "macd": {
        "fast_ema": 12,
        "slow_ema": 26,
        "signal_ema": 9,
    },
    "vol_regime_filter": {
        "vol_window": 20,
        "vol_method": "atr",
        "min_bars": 30,
        "lookback_percentile": 100,
        "regime_mode": False,
        "invert": False,
        "vol_percentile_low": None,
        "vol_percentile_high": None,
        "min_vol": None,
        "max_vol": None,
        "low_vol_threshold": None,
        "high_vol_threshold": None,
        "atr_threshold": None,
    },
}

COMPOSITE_STRATEGY_ID = "composite"
COMPOSITE_BINDING_TYPE_FILTER_GATED_SIGNAL_V1 = "filter_gated_signal_v1"
COMPOSITE_BINDING_TYPE_CONFIRMED_FILTER_GATED_SIGNAL_V1 = "confirmed_filter_gated_signal_v1"
COMPOSITION_RULE_SIGNAL_TIMES_FILTER_MASK = "signal_times_filter_mask"
COMPOSITION_RULE_CONFIRMED_SIGNAL_TIMES_FILTER_MASK = "confirmed_signal_times_filter_mask"
_ALLOWED_COMPOSITE_BINDING_TYPES = frozenset(
    {
        COMPOSITE_BINDING_TYPE_FILTER_GATED_SIGNAL_V1,
        COMPOSITE_BINDING_TYPE_CONFIRMED_FILTER_GATED_SIGNAL_V1,
    }
)
_ALLOWED_COMPOSITION_RULES = frozenset(
    {
        COMPOSITION_RULE_SIGNAL_TIMES_FILTER_MASK,
        COMPOSITION_RULE_CONFIRMED_SIGNAL_TIMES_FILTER_MASK,
    }
)
_COMPOSITE_TYPE_TO_COMPOSITION_RULE = {
    COMPOSITE_BINDING_TYPE_FILTER_GATED_SIGNAL_V1: COMPOSITION_RULE_SIGNAL_TIMES_FILTER_MASK,
    COMPOSITE_BINDING_TYPE_CONFIRMED_FILTER_GATED_SIGNAL_V1: (
        COMPOSITION_RULE_CONFIRMED_SIGNAL_TIMES_FILTER_MASK
    ),
}
_ALLOWED_COMPOSITE_SIGNAL_OWNERS = frozenset(
    {"breakout_donchian", "macd", "ma_crossover", "rsi_reversion"}
)
_ALLOWED_COMPOSITE_FILTER_OWNERS = frozenset({"vol_regime_filter"})
_LONG_ONLY_ASYMMETRIC_SIGNAL_OWNERS = frozenset({"trend_following"})
_FORBIDDEN_BINDING_IDENTITY_SUBSTRINGS = frozenset(
    {"btc", "xbt", "bitcoin", "spot", "synthetic_spot"}
)
_COMPOSITE_BINDING_TOP_LEVEL_KEYS = frozenset(
    {
        "composite_type",
        "composition_rule",
        "signal_strategy_id",
        "filter_strategy_id",
        "signal_strategy_params",
        "filter_strategy_params",
        "aggregation",
        "signal_threshold",
        "confirmation_epochs",
        "binding_semantic_digest",
        "required_warmup_rows",
    }
)
_COMPOSITE_IMPLICIT_SELECTION_KEYS = frozenset(
    {"signal_strategy_candidates", "filter_strategy_candidates", "components", "strategies"}
)

# Evaluation/config metadata allowed in configured params but not strategy logic schema.
_EVALUATION_ONLY_STRATEGY_PARAMS_V1: dict[str, frozenset[str]] = {
    "ma_crossover": frozenset({"price_col"}),
    "rsi_reversion": frozenset({"price_col"}),
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
    external = _EXTERNAL_PARAMETER_SCHEMA_V1.get(strategy_id)
    if external is not None:
        return tuple(external.keys())
    try:
        spec = get_strategy_spec(strategy_id)
    except KeyError:
        return ()
    schema = getattr(spec.cls, "parameter_schema", None)
    if not schema:
        return ()
    return tuple(param.name for param in schema)


def _schema_defaults(strategy_id: str) -> dict[str, Any]:
    external = _EXTERNAL_PARAMETER_SCHEMA_V1.get(strategy_id)
    if external is not None:
        return dict(external)
    try:
        spec = get_strategy_spec(strategy_id)
    except KeyError:
        return {}
    schema = getattr(spec.cls, "parameter_schema", None)
    if not schema:
        return {}
    return {param.name: param.default for param in schema}


@dataclass(frozen=True)
class CompositeStrategyBindingV1:
    composite_type: str
    composition_rule: str
    signal_strategy_id: str
    filter_strategy_id: str
    signal_strategy_params: Mapping[str, Any]
    filter_strategy_params: Mapping[str, Any]
    aggregation: str
    signal_threshold: float
    binding_semantic_digest: str
    required_warmup_rows: int
    signal_effective_params: Mapping[str, Any]
    filter_effective_params: Mapping[str, Any]
    signal_params_digest: str
    filter_params_digest: str
    confirmation_epochs: Optional[int] = None

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "composite_type": self.composite_type,
            "composition_rule": self.composition_rule,
            "signal_strategy_id": self.signal_strategy_id,
            "filter_strategy_id": self.filter_strategy_id,
            "signal_strategy_params": dict(self.signal_strategy_params),
            "filter_strategy_params": dict(self.filter_strategy_params),
            "aggregation": self.aggregation,
            "signal_threshold": self.signal_threshold,
            "binding_semantic_digest": self.binding_semantic_digest,
            "required_warmup_rows": self.required_warmup_rows,
            "signal_effective_params": dict(self.signal_effective_params),
            "filter_effective_params": dict(self.filter_effective_params),
            "signal_params_digest": self.signal_params_digest,
            "filter_params_digest": self.filter_params_digest,
        }
        if self.confirmation_epochs is not None:
            payload["confirmation_epochs"] = self.confirmation_epochs
        return payload


def _reject_forbidden_binding_identity(value: str, *, field_name: str) -> None:
    lowered = value.lower()
    for token in _FORBIDDEN_BINDING_IDENTITY_SUBSTRINGS:
        if token in lowered:
            raise StrategySignalBindingError(f"binding_identity_forbidden:{field_name}:{value}")


def _require_mapping(value: Any, *, field_name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise StrategySignalBindingError(f"composite_binding_field_not_mapping:{field_name}")
    return value


def _validate_composite_binding_params_deterministic(
    params: Mapping[str, Any], *, owner: str
) -> None:
    for key, value in params.items():
        if isinstance(value, (dict, list, set)):
            raise StrategySignalBindingError(f"composite_binding_param_non_scalar:{owner}:{key}")
        if isinstance(value, float) and not math.isfinite(value):
            raise StrategySignalBindingError(f"composite_binding_param_non_finite:{owner}:{key}")


def compute_composite_binding_semantic_digest_v1(binding_payload: Mapping[str, Any]) -> str:
    return _stable_digest(
        {
            "owner": STRATEGY_SIGNAL_BINDING_OWNER,
            "binding_version": STRATEGY_SIGNAL_BINDING_LAYER_VERSION,
            "binding_payload": binding_payload,
        }
    )


def parse_composite_strategy_binding_v1(
    configured_params: Mapping[str, Any],
) -> CompositeStrategyBindingV1:
    """Parse and validate declarative composite binding config (fail-closed)."""
    for key in configured_params:
        if key in _COMPOSITE_IMPLICIT_SELECTION_KEYS:
            raise StrategySignalBindingError(f"composite_implicit_selection_forbidden:{key}")
        if key not in _COMPOSITE_BINDING_TOP_LEVEL_KEYS:
            raise StrategySignalBindingError(f"unknown_composite_binding_param:{key}")

    composite_type = str(configured_params.get("composite_type", "")).strip()
    _fail_closed(
        composite_type not in _ALLOWED_COMPOSITE_BINDING_TYPES,
        f"unknown_composite_type:{composite_type or 'missing'}",
    )

    composition_rule = str(configured_params.get("composition_rule", "")).strip()
    _fail_closed(
        composition_rule not in _ALLOWED_COMPOSITION_RULES,
        f"unknown_composition_rule:{composition_rule or 'missing'}",
    )
    expected_rule = _COMPOSITE_TYPE_TO_COMPOSITION_RULE.get(composite_type)
    _fail_closed(
        expected_rule is None or composition_rule != expected_rule,
        f"composite_type_composition_rule_mismatch:{composite_type}:{composition_rule}",
    )

    confirmation_epochs: Optional[int] = None
    if composite_type == COMPOSITE_BINDING_TYPE_CONFIRMED_FILTER_GATED_SIGNAL_V1:
        if "confirmation_epochs" not in configured_params:
            raise StrategySignalBindingError("composite_confirmation_epochs_missing")
        raw_epochs = configured_params["confirmation_epochs"]
        if isinstance(raw_epochs, bool) or not isinstance(raw_epochs, int):
            raise StrategySignalBindingError("composite_confirmation_epochs_not_integer")
        if raw_epochs != CONFIRMATION_EPOCHS_V1:
            raise StrategySignalBindingError("composite_confirmation_epochs_not_allowed")
        confirmation_epochs = CONFIRMATION_EPOCHS_V1
    elif "confirmation_epochs" in configured_params:
        raise StrategySignalBindingError("composite_confirmation_epochs_not_allowed_for_type")

    signal_strategy_id = str(configured_params.get("signal_strategy_id", "")).strip()
    filter_strategy_id = str(configured_params.get("filter_strategy_id", "")).strip()
    _fail_closed(not signal_strategy_id, "composite_signal_strategy_id_missing")
    _fail_closed(not filter_strategy_id, "composite_filter_strategy_id_missing")
    _reject_forbidden_binding_identity(signal_strategy_id, field_name="signal_strategy_id")
    _reject_forbidden_binding_identity(filter_strategy_id, field_name="filter_strategy_id")

    signal_resolution = resolve_strategy_id(signal_strategy_id)
    filter_resolution = resolve_strategy_id(filter_strategy_id)
    canonical_signal_id = signal_resolution.canonical_strategy_id
    canonical_filter_id = filter_resolution.canonical_strategy_id

    if composite_type == COMPOSITE_BINDING_TYPE_CONFIRMED_FILTER_GATED_SIGNAL_V1:
        _fail_closed(
            canonical_signal_id != "breakout_donchian",
            f"confirmed_composite_signal_owner_not_allowed:{canonical_signal_id}",
        )
    else:
        _fail_closed(
            canonical_signal_id not in _ALLOWED_COMPOSITE_SIGNAL_OWNERS,
            f"composite_signal_owner_not_allowed:{canonical_signal_id}",
        )
    _fail_closed(
        canonical_filter_id not in _ALLOWED_COMPOSITE_FILTER_OWNERS,
        f"composite_filter_owner_not_allowed:{canonical_filter_id}",
    )
    _fail_closed(
        canonical_signal_id in _LONG_ONLY_ASYMMETRIC_SIGNAL_OWNERS,
        f"composite_signal_owner_long_only_asymmetric:{canonical_signal_id}",
    )

    signal_params = _require_mapping(
        configured_params.get("signal_strategy_params"),
        field_name="signal_strategy_params",
    )
    filter_params = _require_mapping(
        configured_params.get("filter_strategy_params"),
        field_name="filter_strategy_params",
    )
    _validate_composite_binding_params_deterministic(
        signal_params,
        owner="signal_strategy_params",
    )
    _validate_composite_binding_params_deterministic(
        filter_params,
        owner="filter_strategy_params",
    )

    signal_binding_params = project_strategy_params_for_binding_v1(
        canonical_signal_id,
        signal_params,
    )
    filter_binding_params = project_strategy_params_for_binding_v1(
        canonical_filter_id,
        filter_params,
    )
    signal_effective, signal_digest = resolve_effective_strategy_params_v1(
        canonical_signal_id,
        signal_binding_params,
    )
    filter_effective, filter_digest = resolve_effective_strategy_params_v1(
        canonical_filter_id,
        filter_binding_params,
    )

    if canonical_filter_id == "vol_regime_filter":
        if filter_effective.get("regime_mode") is True:
            raise StrategySignalBindingError(
                "vol_regime_filter_regime_mode_not_allowed_in_filter_binding"
            )
        for required in ("vol_percentile_low", "vol_percentile_high"):
            if required not in filter_params:
                raise StrategySignalBindingError(f"filter_strategy_param_missing:{required}")

    aggregation = str(configured_params.get("aggregation", "")).strip().lower()
    _fail_closed(not aggregation, "composite_aggregation_missing")
    if "signal_threshold" not in configured_params:
        raise StrategySignalBindingError("composite_signal_threshold_missing")
    signal_threshold = float(configured_params["signal_threshold"])
    if not math.isfinite(signal_threshold):
        raise StrategySignalBindingError("composite_signal_threshold_non_finite")

    signal_warmup = compute_required_warmup_rows_v1(canonical_signal_id, signal_effective)
    filter_warmup = compute_required_warmup_rows_v1(canonical_filter_id, filter_effective)
    required_warmup_rows = max(signal_warmup, filter_warmup)
    if confirmation_epochs is not None:
        required_warmup_rows = max(required_warmup_rows, signal_warmup + confirmation_epochs)

    if "required_warmup_rows" in configured_params:
        declared_warmup = configured_params["required_warmup_rows"]
        if isinstance(declared_warmup, bool) or not isinstance(declared_warmup, int):
            raise StrategySignalBindingError("composite_required_warmup_not_integer")
        if declared_warmup != required_warmup_rows:
            raise StrategySignalBindingError("composite_required_warmup_mismatch")

    semantic_payload = {
        "composite_type": composite_type,
        "composition_rule": composition_rule,
        "signal_strategy_id": canonical_signal_id,
        "filter_strategy_id": canonical_filter_id,
        "signal_strategy_params": dict(signal_params),
        "filter_strategy_params": dict(filter_params),
        "signal_effective_params": signal_effective,
        "filter_effective_params": filter_effective,
        "aggregation": aggregation,
        "signal_threshold": signal_threshold,
        "required_warmup_rows": required_warmup_rows,
    }
    if confirmation_epochs is not None:
        semantic_payload["confirmation_epochs"] = confirmation_epochs
    binding_semantic_digest = compute_composite_binding_semantic_digest_v1(semantic_payload)

    expected_digest = configured_params.get("binding_semantic_digest")
    if expected_digest is not None:
        if str(expected_digest) != binding_semantic_digest:
            raise StrategySignalBindingError("composite_binding_semantic_digest_mismatch")

    return CompositeStrategyBindingV1(
        composite_type=composite_type,
        composition_rule=composition_rule,
        signal_strategy_id=canonical_signal_id,
        filter_strategy_id=canonical_filter_id,
        signal_strategy_params=dict(signal_params),
        filter_strategy_params=dict(filter_params),
        aggregation=aggregation,
        signal_threshold=signal_threshold,
        binding_semantic_digest=binding_semantic_digest,
        required_warmup_rows=required_warmup_rows,
        signal_effective_params=signal_effective,
        filter_effective_params=filter_effective,
        signal_params_digest=signal_digest,
        filter_params_digest=filter_digest,
        confirmation_epochs=confirmation_epochs,
    )


def _instantiate_bound_strategy_v1(
    strategy_id: str,
    effective_params: Mapping[str, Any],
):
    spec = get_strategy_spec(strategy_id)
    return spec.cls(config=dict(effective_params))


def _apply_composite_threshold_and_filter_v1(
    *,
    signal_values: pd.Series,
    signal_threshold: float,
    filter_strategy,
    bars: pd.DataFrame,
) -> pd.Series:
    aggregated = signal_values.astype(float)
    final_signals = pd.Series(0, index=bars.index, dtype=int)
    final_signals = final_signals.where(~(aggregated > signal_threshold), 1)
    final_signals = final_signals.where(~(aggregated < -signal_threshold), -1)
    filter_mask = filter_strategy.generate_signals(bars)
    return (final_signals * filter_mask).astype(int)


def execute_composite_strategy_signal_series_v1(
    bars: pd.DataFrame,
    *,
    configured_params: Mapping[str, Any],
    configured_strategy_id: str = COMPOSITE_STRATEGY_ID,
) -> StrategySignalBindingResultV1:
    """Execute filter-gated composite binding via canonical strategy owners."""
    binding = parse_composite_strategy_binding_v1(configured_params)
    filter_strategy = _instantiate_bound_strategy_v1(
        binding.filter_strategy_id,
        binding.filter_effective_params,
    )
    if binding.composite_type == COMPOSITE_BINDING_TYPE_CONFIRMED_FILTER_GATED_SIGNAL_V1:
        confirmed_signals = generate_confirmed_breakout_signals_v1(
            bars,
            lookback=int(binding.signal_effective_params["lookback"]),
            price_col=str(binding.signal_effective_params["price_col"]),
            confirmation_epochs=CONFIRMATION_EPOCHS_V1,
        )
        raw_signals = _apply_composite_threshold_and_filter_v1(
            signal_values=confirmed_signals,
            signal_threshold=binding.signal_threshold,
            filter_strategy=filter_strategy,
            bars=bars,
        )
    else:
        signal_strategy = _instantiate_bound_strategy_v1(
            binding.signal_strategy_id,
            binding.signal_effective_params,
        )
        composite = CompositeStrategy(
            strategies=[(signal_strategy, 1.0)],
            aggregation=binding.aggregation,
            signal_threshold=binding.signal_threshold,
            filter_strategy=filter_strategy,
        )
        raw_signals = composite.generate_signals(bars)
    if not isinstance(raw_signals, pd.Series):
        raise StrategySignalBindingError("composite_signal_not_series")

    composite_params_digest = _stable_digest(
        {
            "strategy_id": COMPOSITE_STRATEGY_ID,
            "binding_semantic_digest": binding.binding_semantic_digest,
            "owner": STRATEGY_SIGNAL_BINDING_OWNER,
        }
    )
    validated_signals, provenance = validate_strategy_signal_contract_v1(
        raw_signals,
        bars_index=bars.index,
        strategy_id=COMPOSITE_STRATEGY_ID,
        strategy_params_digest=composite_params_digest,
    )
    entry = get_strategy_registry_entry(COMPOSITE_STRATEGY_ID)
    provenance = StrategySignalProvenanceV1(
        configured_strategy_id=configured_strategy_id,
        executed_strategy_id=COMPOSITE_STRATEGY_ID,
        strategy_version=entry.strategy_version,
        strategy_owner=entry.implementation_ref,
        configured_strategy_params=dict(configured_params),
        effective_strategy_params={
            "composite_binding": binding.to_dict(),
            "binding_semantic_digest": binding.binding_semantic_digest,
            "required_warmup_rows": binding.required_warmup_rows,
        },
        strategy_params_digest=composite_params_digest,
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


def compute_required_warmup_rows_v1(
    strategy_id: str,
    effective_params: Mapping[str, Any],
) -> int:
    """Deterministic warmup row count for registered strategy parameter contracts."""
    if strategy_id == "macd":
        slow = int(effective_params["slow_ema"])
        signal = int(effective_params["signal_ema"])
        fast = int(effective_params["fast_ema"])
        if fast <= 0 or slow <= 0 or signal <= 0 or fast >= slow:
            raise StrategySignalBindingError("macd_warmup_param_invariant_failed")
        return slow + signal - 1
    if strategy_id == "ma_crossover":
        return int(effective_params["slow_window"])
    if strategy_id == "breakout_donchian":
        if "lookback" not in effective_params:
            raise StrategySignalBindingError("breakout_donchian_lookback_missing")
        lookback_raw = effective_params["lookback"]
        if isinstance(lookback_raw, bool) or not isinstance(lookback_raw, int):
            raise StrategySignalBindingError("breakout_donchian_lookback_not_integer")
        if lookback_raw < 2:
            raise StrategySignalBindingError("breakout_donchian_lookback_below_minimum")
        return lookback_raw
    if strategy_id == "rsi_reversion":
        return int(effective_params["rsi_window"])
    if strategy_id == "vol_regime_filter":
        return max(
            int(effective_params["vol_window"]),
            int(effective_params["min_bars"]),
            int(effective_params["lookback_percentile"]),
        )
    if strategy_id == COMPOSITE_STRATEGY_ID:
        raise StrategySignalBindingError("composite_warmup_requires_binding_context")
    raise StrategySignalBindingError(f"required_warmup_rows_unbound:{strategy_id}")


def compute_composite_required_warmup_rows_v1(
    configured_params: Mapping[str, Any],
) -> int:
    binding = parse_composite_strategy_binding_v1(configured_params)
    return binding.required_warmup_rows


def project_strategy_params_for_binding_v1(
    strategy_id: str,
    configured_params: Mapping[str, Any],
) -> dict[str, Any]:
    """Project configured evaluation params to strategy-logic params for binding."""
    evaluation_only = _EVALUATION_ONLY_STRATEGY_PARAMS_V1.get(strategy_id, frozenset())
    aliases = _CANONICAL_PARAM_ALIASES_V1.get(strategy_id, {})
    allowed_input_keys = (
        set(_schema_param_names(strategy_id)) | set(aliases.keys()) | evaluation_only
    )

    for key in configured_params:
        _fail_closed(key not in allowed_input_keys, f"unknown_strategy_param:{key}")

    return {key: value for key, value in configured_params.items() if key not in evaluation_only}


def _validate_macd_parameter_invariants_v1(effective_params: Mapping[str, Any]) -> None:
    fast = int(effective_params["fast_ema"])
    slow = int(effective_params["slow_ema"])
    signal = int(effective_params["signal_ema"])
    _fail_closed(fast <= 0, "macd_fast_ema_non_positive")
    _fail_closed(slow <= 0, "macd_slow_ema_non_positive")
    _fail_closed(signal <= 0, "macd_signal_ema_non_positive")
    _fail_closed(fast >= slow, "macd_fast_ema_not_lt_slow_ema")


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
    if strategy_id == "macd":
        _validate_macd_parameter_invariants_v1(effective)
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

    if canonical_id == COMPOSITE_STRATEGY_ID:
        if not configured_params:
            composite_cfg = collect_configured_strategy_params_v1(cfg, strategy_id)
            if composite_cfg:
                configured_params = composite_cfg
        return execute_composite_strategy_signal_series_v1(
            bars,
            configured_params=configured_params,
            configured_strategy_id=strategy_id,
        )

    binding_params = project_strategy_params_for_binding_v1(
        canonical_id,
        configured_params,
    )
    effective_params, params_digest = resolve_effective_strategy_params_v1(
        canonical_id,
        binding_params,
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
