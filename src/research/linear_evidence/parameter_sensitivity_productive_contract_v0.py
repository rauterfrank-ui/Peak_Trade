"""Operator-ratified productive normative contract for offline parameter sensitivity v0.

Offline-only, authority-neutral contract owner. No IO, runtime, trading logic, or solver
duplication. Materializer execution remains a separate scope.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from math import isfinite
from pathlib import Path
from typing import Any, Mapping, Sequence

import pandas as pd

from src.backtest.parameter_sensitivity_v1 import (
    PARAMETER_SENSITIVITY_OWNER,
    ParameterSensitivityError,
    ParameterSensitivityGridV1,
    load_parameter_grid_v1,
)
from src.backtest.strategy_signal_binding_v1 import (
    _EVALUATION_ONLY_STRATEGY_PARAMS_V1,
    _EXTERNAL_PARAMETER_SCHEMA_V1,
)
from src.research.final_research_fleet_v0_versioned_binding_manifest_contract_v0 import (
    FLEET_CANDIDATES,
    load_step31f_evaluation_config_v0,
)
from src.research.linear_evidence.factor_exposure_productive_contract_v0 import (
    AUTHORITY_EFFECT,
    RUNTIME_EFFECT,
    stable_digest_v0,
)
from src.research.linear_evidence.sensitivity import (
    ParameterGridSpecV1,
    ParameterSensitivityInputV1,
)
from src.research.linear_evidence.signal_matrix_productive_contract_v0 import (
    DECISION_TIME_KEY,
    EXPECTED_FLEET_SIGNAL_ORDER,
    FEATURE_TIME_KEY,
    INSTRUMENT_ID_KEY,
    RATIFIED_BINDING_SOURCE,
    RATIFIED_FLEET_SIGNAL_IDS,
    compute_signal_matrix_digest_v0,
)

PACKAGE_MARKER = "OFFLINE_PARAMETER_SENSITIVITY_PRODUCTIVE_CONTRACT_V0=true"

BINDING_CONTRACT_VERSION = "offline_parameter_sensitivity_binding_v0"
GRID_CONTRACT_VERSION = "offline_parameter_sensitivity_grid_join_v0"
PROVENANCE_CONTRACT_VERSION = "offline_parameter_sensitivity_provenance_v0"

ALLOWED_CALIBRATABLE_PARAMETERS: tuple[str, ...] = ("fee_bps", "slippage_bps")
DIAGNOSTIC_ONLY_PARAMETERS: frozenset[str] = frozenset({"signal_scale"})
FLEET_STRATEGY_IDS: frozenset[str] = frozenset(sid for sid, _ in FLEET_CANDIDATES)

PARAMETER_CLASS_CONSTITUTIONAL_CORE = "CONSTITUTIONAL_CORE"
PARAMETER_CLASS_EXPLICITLY_CALIBRATABLE = "EXPLICITLY_CALIBRATABLE_RESEARCH_PARAMETER"
PARAMETER_CLASS_DIAGNOSTIC_ONLY = "DIAGNOSTIC_ONLY"
PARAMETER_CLASS_UNKNOWN = "UNKNOWN"


class ProductiveBindingRejectionReason(str, Enum):
    BINDING_DIGEST_MISMATCH = "BINDING_DIGEST_MISMATCH"
    SIGNAL_MATRIX_DIGEST_MISMATCH = "SIGNAL_MATRIX_DIGEST_MISMATCH"
    MISSING_FLEET_BINDING = "MISSING_FLEET_BINDING"
    MISSING_SIGNAL_MATRIX = "MISSING_SIGNAL_MATRIX"
    UNKNOWN_PARAMETER = "UNKNOWN_PARAMETER"
    CONSTITUTIONAL_PARAMETER_VARIATION_REQUESTED = "CONSTITUTIONAL_PARAMETER_VARIATION_REQUESTED"
    DIAGNOSTIC_ONLY_PARAMETER_VARIATION_REQUESTED = "DIAGNOSTIC_ONLY_PARAMETER_VARIATION_REQUESTED"
    UNDECLARED_PARAMETER_RANGE = "UNDECLARED_PARAMETER_RANGE"
    GRID_SPEC_INVALID = "GRID_SPEC_INVALID"
    TARGET_BINDING_MISSING = "TARGET_BINDING_MISSING"
    FEATURE_LEAKAGE_DETECTED = "FEATURE_LEAKAGE_DETECTED"
    NON_FINITE_FEATURE_VALUE = "NON_FINITE_FEATURE_VALUE"
    NON_FINITE_TARGET = "NON_FINITE_TARGET"
    PARAMETER_NOT_IN_ALLOWED_SURFACE = "PARAMETER_NOT_IN_ALLOWED_SURFACE"


@dataclass(frozen=True)
class ParameterClassificationRowV0:
    strategy_name: str
    parameter_name: str
    parameter_class: str
    baseline_value: Any
    mutation_allowed: bool
    sensitivity_variation_allowed: bool


@dataclass(frozen=True)
class ParameterSensitivityProductiveBindingV0:
    contract_version: str = BINDING_CONTRACT_VERSION
    binding_source_path: str = RATIFIED_BINDING_SOURCE
    binding_digest: str = ""
    signal_matrix_digest: str = ""
    strategy_id: str = ""
    strategy_version: str = "v1"
    baseline_fee_bps: float = 0.0
    baseline_slippage_bps: float = 0.0
    grid_id: str = ""
    grid_digest: str = ""
    authority_effect: str = AUTHORITY_EFFECT
    runtime_effect: str = RUNTIME_EFFECT

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract_version": self.contract_version,
            "binding_source_path": self.binding_source_path,
            "binding_digest": self.binding_digest,
            "signal_matrix_digest": self.signal_matrix_digest,
            "strategy_id": self.strategy_id,
            "strategy_version": self.strategy_version,
            "baseline_fee_bps": self.baseline_fee_bps,
            "baseline_slippage_bps": self.baseline_slippage_bps,
            "grid_id": self.grid_id,
            "grid_digest": self.grid_digest,
            "authority_effect": self.authority_effect,
            "runtime_effect": self.runtime_effect,
        }


@dataclass(frozen=True)
class ProductiveBindingRejectedRowV0:
    instrument_id: str
    decision_time: str
    reason: ProductiveBindingRejectionReason


@dataclass(frozen=True)
class ProductiveBindingValidationResultV0:
    admissible_records: tuple[ParameterSensitivityInputV1, ...]
    rejected: tuple[ProductiveBindingRejectedRowV0, ...]
    row_count_before_filter: int
    row_count_after_filter: int
    dropped_rows_by_reason: dict[str, int]
    binding: ParameterSensitivityProductiveBindingV0
    grid: ParameterSensitivityGridV1
    grid_specs: tuple[ParameterGridSpecV1, ...]
    authority_effect: str = AUTHORITY_EFFECT
    runtime_effect: str = RUNTIME_EFFECT


@dataclass(frozen=True)
class ParameterSensitivityProductiveProvenanceV0:
    contract_version: str = PROVENANCE_CONTRACT_VERSION
    binding_source_path: str = RATIFIED_BINDING_SOURCE
    binding_digest: str = ""
    signal_matrix_digest: str = ""
    grid_digest: str = ""
    strategy_id: str = ""
    strategy_version: str = "v1"
    parameter_names: tuple[str, ...] = ALLOWED_CALIBRATABLE_PARAMETERS
    row_count_before_filter: int = 0
    row_count_after_filter: int = 0
    dropped_rows_by_reason: dict[str, int] = field(default_factory=dict)
    implementation_digest: str = ""
    grid_owner: str = PARAMETER_SENSITIVITY_OWNER
    authority_effect: str = AUTHORITY_EFFECT
    runtime_effect: str = RUNTIME_EFFECT

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract_version": self.contract_version,
            "binding_source_path": self.binding_source_path,
            "binding_digest": self.binding_digest,
            "signal_matrix_digest": self.signal_matrix_digest,
            "grid_digest": self.grid_digest,
            "strategy_id": self.strategy_id,
            "strategy_version": self.strategy_version,
            "parameter_names": list(self.parameter_names),
            "row_count_before_filter": self.row_count_before_filter,
            "row_count_after_filter": self.row_count_after_filter,
            "dropped_rows_by_reason": dict(self.dropped_rows_by_reason),
            "implementation_digest": self.implementation_digest,
            "grid_owner": self.grid_owner,
            "authority_effect": self.authority_effect,
            "runtime_effect": self.runtime_effect,
        }


def classify_fleet_parameters_v0() -> tuple[ParameterClassificationRowV0, ...]:
    rows: list[ParameterClassificationRowV0] = []
    calibratable_names = frozenset(ALLOWED_CALIBRATABLE_PARAMETERS)
    for strategy_id in sorted(FLEET_STRATEGY_IDS):
        schema = _EXTERNAL_PARAMETER_SCHEMA_V1.get(strategy_id, {})
        eval_only = _EVALUATION_ONLY_STRATEGY_PARAMS_V1.get(strategy_id, frozenset())
        for name, default in schema.items():
            if name in eval_only:
                pclass = PARAMETER_CLASS_DIAGNOSTIC_ONLY
            else:
                pclass = PARAMETER_CLASS_CONSTITUTIONAL_CORE
            rows.append(
                ParameterClassificationRowV0(
                    strategy_name=strategy_id,
                    parameter_name=name,
                    parameter_class=pclass,
                    baseline_value=default,
                    mutation_allowed=False,
                    sensitivity_variation_allowed=False,
                )
            )
        for name in calibratable_names:
            rows.append(
                ParameterClassificationRowV0(
                    strategy_name=strategy_id,
                    parameter_name=name,
                    parameter_class=PARAMETER_CLASS_EXPLICITLY_CALIBRATABLE,
                    baseline_value=None,
                    mutation_allowed=True,
                    sensitivity_variation_allowed=True,
                )
            )
    rows.append(
        ParameterClassificationRowV0(
            strategy_name="fleet_aggregate",
            parameter_name="signal_scale",
            parameter_class=PARAMETER_CLASS_DIAGNOSTIC_ONLY,
            baseline_value=1.0,
            mutation_allowed=False,
            sensitivity_variation_allowed=False,
        )
    )
    return tuple(rows)


def validate_parameter_variation_allowed_v0(parameter_name: str) -> str | None:
    if parameter_name in DIAGNOSTIC_ONLY_PARAMETERS:
        return ProductiveBindingRejectionReason.DIAGNOSTIC_ONLY_PARAMETER_VARIATION_REQUESTED.value
    if parameter_name not in ALLOWED_CALIBRATABLE_PARAMETERS:
        for strategy_id in FLEET_STRATEGY_IDS:
            schema = _EXTERNAL_PARAMETER_SCHEMA_V1.get(strategy_id, {})
            if parameter_name in schema:
                return ProductiveBindingRejectionReason.CONSTITUTIONAL_PARAMETER_VARIATION_REQUESTED.value
        return ProductiveBindingRejectionReason.UNKNOWN_PARAMETER.value
    return None


def validate_binding_digest_v0(
    *,
    expected_digest: str,
    actual_digest: str,
) -> str | None:
    if not expected_digest or not actual_digest:
        return ProductiveBindingRejectionReason.MISSING_FLEET_BINDING.value
    if expected_digest != actual_digest:
        return ProductiveBindingRejectionReason.BINDING_DIGEST_MISMATCH.value
    return None


def validate_signal_matrix_digest_v0(
    *,
    expected_digest: str | None,
    actual_digest: str,
    rows: Sequence[Mapping[str, Any]],
) -> str | None:
    if not rows:
        return ProductiveBindingRejectionReason.MISSING_SIGNAL_MATRIX.value
    computed = compute_signal_matrix_digest_v0(rows)
    if expected_digest is not None and expected_digest != computed:
        return ProductiveBindingRejectionReason.SIGNAL_MATRIX_DIGEST_MISMATCH.value
    if actual_digest != computed:
        return ProductiveBindingRejectionReason.SIGNAL_MATRIX_DIGEST_MISMATCH.value
    return None


def resolve_baseline_cost_params_v0(cfg: Mapping[str, Any]) -> tuple[float, float]:
    backtest = cfg.get("backtest", {})
    if not isinstance(backtest, Mapping):
        raise ValueError(ProductiveBindingRejectionReason.TARGET_BINDING_MISSING.value)
    fee_bps = backtest.get("fee_bps")
    slippage_bps = backtest.get("slippage_bps")
    if fee_bps is None or slippage_bps is None:
        raise ValueError(ProductiveBindingRejectionReason.TARGET_BINDING_MISSING.value)
    return float(fee_bps), float(slippage_bps)


def load_productive_parameter_grid_v0(
    *,
    repo_root: Path,
    strategy_id: str,
    strategy_version: str = "v1",
    data_digest: str,
    instrument_id: str = "okx:linear_perpetual:ETH:USDT:USDT:perp",
) -> ParameterSensitivityGridV1:
    cfg = load_step31f_evaluation_config_v0(repo_root, strategy_id)
    timestamps = pd.date_range("2024-05-30T20:00:00Z", periods=32, freq="1h", tz="UTC")
    bars = pd.DataFrame(
        {
            "open": [100.0] * len(timestamps),
            "high": [101.0] * len(timestamps),
            "low": [99.0] * len(timestamps),
            "close": [100.0] * len(timestamps),
            "volume": [1000.0] * len(timestamps),
        },
        index=timestamps,
    )
    try:
        return load_parameter_grid_v1(
            cfg,
            strategy_id=strategy_id,
            strategy_version=strategy_version,
            bars=bars,
            data_digest=data_digest,
            instrument_id=instrument_id,
        )
    except ParameterSensitivityError as exc:
        raise ValueError(
            f"{ProductiveBindingRejectionReason.GRID_SPEC_INVALID.value}:{exc}"
        ) from exc


def build_parameter_grid_specs_v0(
    grid: ParameterSensitivityGridV1,
) -> tuple[ParameterGridSpecV1, ...]:
    specs: list[ParameterGridSpecV1] = []
    for index, name in enumerate(grid.parameter_names):
        if name not in ALLOWED_CALIBRATABLE_PARAMETERS:
            raise ValueError(
                ProductiveBindingRejectionReason.PARAMETER_NOT_IN_ALLOWED_SURFACE.value
            )
        values = grid.parameter_values[index]
        specs.append(
            ParameterGridSpecV1(
                parameter_name=name,
                scaled_feature_name=name,
                parameter_values=tuple(float(value) for value in values),
            )
        )
    return tuple(specs)


def _diagnostic_target_from_signals(row: Mapping[str, Any]) -> float:
    values = [float(row[name]) for name in EXPECTED_FLEET_SIGNAL_ORDER]
    return sum(values) / len(values)


def materialize_productive_sensitivity_row_v0(
    row: Mapping[str, Any],
    *,
    baseline_fee_bps: float,
    baseline_slippage_bps: float,
) -> tuple[ParameterSensitivityInputV1 | None, str | None]:
    instrument_id = str(row.get(INSTRUMENT_ID_KEY, ""))
    decision_time = str(row.get(DECISION_TIME_KEY, ""))
    feature_time = str(row.get(FEATURE_TIME_KEY, ""))
    if not instrument_id or not decision_time or not feature_time:
        return None, ProductiveBindingRejectionReason.TARGET_BINDING_MISSING.value
    if feature_time >= decision_time:
        return None, ProductiveBindingRejectionReason.FEATURE_LEAKAGE_DETECTED.value
    features: dict[str, float] = {
        "fee_bps": float(baseline_fee_bps),
        "slippage_bps": float(baseline_slippage_bps),
    }
    for name in EXPECTED_FLEET_SIGNAL_ORDER:
        if name not in row:
            return None, ProductiveBindingRejectionReason.TARGET_BINDING_MISSING.value
        value = float(row[name])
        if not isfinite(value):
            return None, ProductiveBindingRejectionReason.NON_FINITE_FEATURE_VALUE.value
        features[name] = value
    target = _diagnostic_target_from_signals(row)
    if not isfinite(target):
        return None, ProductiveBindingRejectionReason.NON_FINITE_TARGET.value
    return (
        ParameterSensitivityInputV1(
            instrument_id=instrument_id,
            decision_time=decision_time,
            feature_availability_time=feature_time,
            target=target,
            features=features,
        ),
        None,
    )


def validate_productive_binding_batch_v0(
    *,
    signal_matrix_rows: Sequence[Mapping[str, Any]],
    binding_completion: Mapping[str, Any],
    repo_root: Path,
    strategy_id: str = "trend_following",
    expected_binding_digest: str | None = None,
    expected_signal_matrix_digest: str | None = None,
) -> ProductiveBindingValidationResultV0:
    binding_digest = str(binding_completion.get("completion_digest", ""))
    digest_reason = validate_binding_digest_v0(
        expected_digest=expected_binding_digest or binding_digest,
        actual_digest=binding_digest,
    )
    if digest_reason is not None:
        raise ValueError(digest_reason)

    signal_matrix_digest = compute_signal_matrix_digest_v0(signal_matrix_rows)
    matrix_reason = validate_signal_matrix_digest_v0(
        expected_digest=expected_signal_matrix_digest,
        actual_digest=signal_matrix_digest,
        rows=signal_matrix_rows,
    )
    if matrix_reason is not None:
        raise ValueError(matrix_reason)

    shared = binding_completion.get("shared_bindings", {})
    dataset_binding = shared.get("dataset_binding", {}) if isinstance(shared, Mapping) else {}
    data_digest = str(dataset_binding.get("data_digest", ""))

    cfg = load_step31f_evaluation_config_v0(repo_root, strategy_id)
    baseline_fee_bps, baseline_slippage_bps = resolve_baseline_cost_params_v0(cfg)
    grid = load_productive_parameter_grid_v0(
        repo_root=repo_root,
        strategy_id=strategy_id,
        data_digest=data_digest,
    )
    grid_specs = build_parameter_grid_specs_v0(grid)

    candidates = {
        str(item.get("strategy_id", "")): item
        for item in binding_completion.get("candidates", [])
        if isinstance(item, Mapping)
    }
    if strategy_id not in candidates:
        raise ValueError(ProductiveBindingRejectionReason.MISSING_FLEET_BINDING.value)
    strategy_version = str(candidates[strategy_id].get("strategy_version", "v1"))

    binding = ParameterSensitivityProductiveBindingV0(
        binding_digest=binding_digest,
        signal_matrix_digest=signal_matrix_digest,
        strategy_id=strategy_id,
        strategy_version=strategy_version,
        baseline_fee_bps=baseline_fee_bps,
        baseline_slippage_bps=baseline_slippage_bps,
        grid_id=grid.grid_id,
        grid_digest=grid.grid_digest,
    )

    rejected: list[ProductiveBindingRejectedRowV0] = []
    dropped: dict[str, int] = {}
    admissible: list[ParameterSensitivityInputV1] = []
    ordered_rows = sorted(
        signal_matrix_rows,
        key=lambda row: (
            str(row.get(INSTRUMENT_ID_KEY, "")),
            str(row.get(DECISION_TIME_KEY, "")),
        ),
    )
    for row in ordered_rows:
        record, reason = materialize_productive_sensitivity_row_v0(
            row,
            baseline_fee_bps=baseline_fee_bps,
            baseline_slippage_bps=baseline_slippage_bps,
        )
        if record is None:
            rejected.append(
                ProductiveBindingRejectedRowV0(
                    instrument_id=str(row.get(INSTRUMENT_ID_KEY, "")),
                    decision_time=str(row.get(DECISION_TIME_KEY, "")),
                    reason=ProductiveBindingRejectionReason(reason or "TARGET_BINDING_MISSING"),
                )
            )
            key = reason or ProductiveBindingRejectionReason.TARGET_BINDING_MISSING.value
            dropped[key] = dropped.get(key, 0) + 1
            continue
        admissible.append(record)

    return ProductiveBindingValidationResultV0(
        admissible_records=tuple(admissible),
        rejected=tuple(rejected),
        row_count_before_filter=len(signal_matrix_rows),
        row_count_after_filter=len(admissible),
        dropped_rows_by_reason=dropped,
        binding=binding,
        grid=grid,
        grid_specs=grid_specs,
    )


def validate_fleet_candidate_set_v0(strategy_ids: Sequence[str]) -> None:
    requested = set(strategy_ids)
    if requested != set(RATIFIED_FLEET_SIGNAL_IDS):
        raise ValueError(ProductiveBindingRejectionReason.MISSING_FLEET_BINDING.value)
