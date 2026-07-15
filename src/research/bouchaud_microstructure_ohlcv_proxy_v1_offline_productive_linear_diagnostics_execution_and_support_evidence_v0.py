"""Bouchaud OHLCV proxy v1 offline productive linear diagnostics execution and support evidence v0.

Deterministic execution slice: materializes the Bouchaud feature matrix through the PR #5190
adapter path, runs all five productive linear diagnostic classes, and aggregates manifest-verified
support evidence. Diagnostic-only — no economic evaluation, promotion authority, or runtime effect.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, is_dataclass
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

import numpy as np

from src.research.bouchaud_microstructure_ohlcv_proxy_v1_offline_productive_linear_diagnostics_feature_matrix_binding_v0 import (
    CANONICAL_OWNER as PR5190_ADAPTER_OWNER,
    DEFAULT_PARAMETER_GRID,
    FeatureMatrixBindingStatus,
    FeatureMatrixBindingValidationError,
    bind_bouchaud_feature_matrix_to_linear_diagnostics_v0,
)
from src.research.bouchaud_microstructure_ohlcv_proxy_v1_research_generation_preparation_v0 import (
    DATASET_DIGEST,
    DATASET_ID,
    FEATURE_NAMES,
    HYPOTHESIS_ID,
    INSTRUMENT_ID,
    PREPARATION_ID,
    RESEARCH_SCOPE,
    TARGET_NAME,
    build_target_binding,
    validate_no_lookahead_contract_v0,
)
from src.research.linear_evidence.contracts import FeatureMatrixBindingV1
from src.research.linear_evidence.cost_model import build_cost_model_calibration_evidence
from src.research.linear_evidence.drift import RollingLinearDriftInputV1, fit_rolling_linear_drift
from src.research.linear_evidence.factor_exposure import (
    FactorExposureInputV1,
    fit_factor_exposure_diagnostics_v0,
)
from src.research.linear_evidence.feature_matrix import build_feature_matrix_binding
from src.research.linear_evidence.fitters import fit_ols_lstsq
from src.research.linear_evidence.offline_productive_linear_diagnostics_support_bundle_v0 import (
    AUTHORITY_EFFECT,
    DIAGNOSTIC_CLASS_ORDER,
    RUNTIME_EFFECT,
    SourceBundleSpecV0,
    SupportBundleValidationError,
    build_productive_linear_diagnostics_support_bundle_artifacts_v0,
    validate_support_bundle_artifacts_v0,
)
from src.research.linear_evidence.sensitivity import (
    ParameterSensitivityInputV1,
    fit_parameter_sensitivity_surface,
)
from src.research.linear_evidence.signal_orthogonality import (
    SignalOrthogonalityConfigV1,
    analyze_signal_orthogonality,
)

PACKAGE_MARKER = (
    "BOUCHAUD_MICROSTRUCTURE_OHLCV_PROXY_V1_OFFLINE_PRODUCTIVE_LINEAR_DIAGNOSTICS_"
    "EXECUTION_AND_SUPPORT_EVIDENCE_V0=true"
)
SCHEMA_VERSION = (
    "bouchaud_microstructure_ohlcv_proxy_v1_offline_productive_linear_diagnostics_"
    "execution_and_support_evidence.v0"
)
EVIDENCE_TYPE = (
    "BOUCHAUD_MICROSTRUCTURE_OHLCV_PROXY_V1_OFFLINE_PRODUCTIVE_LINEAR_DIAGNOSTICS_"
    "EXECUTION_AND_SUPPORT_EVIDENCE_V0"
)
EXECUTION_ID = (
    "bouchaud_microstructure_ohlcv_proxy_v1_offline_productive_linear_diagnostics_"
    "execution_and_support_evidence_v0"
)
CANONICAL_OWNER = (
    "src/research/"
    "bouchaud_microstructure_ohlcv_proxy_v1_offline_productive_linear_diagnostics_"
    "execution_and_support_evidence_v0.py"
)
EXECUTION_OWNER = (
    "research."
    "bouchaud_microstructure_ohlcv_proxy_v1_offline_productive_linear_diagnostics_"
    "execution_and_support_evidence_v0"
)
FEATURE_MATRIX_OWNER = (
    "src/research/linear_evidence/feature_matrix.py::build_feature_matrix_binding"
)
FEATURE_DIGEST_OWNER = (
    "src/research/bouchaud_microstructure_ohlcv_proxy_v1_research_generation_preparation_v0.py"
    "::materialize_and_validate_feature_matrix_v0"
)
SUPPORT_BUNDLE_OWNER = (
    "src/research/linear_evidence/offline_productive_linear_diagnostics_support_bundle_v0.py"
)
CANONICAL_FEATURE_DIGEST = "6a29ebbba64e6f732e4cedd601025c4f4259d0b0c842669ea4c8da3abc0d84b0"

DEFAULT_DRIFT_WINDOW_SIZE = 6
DEFAULT_DRIFT_WINDOW_STEP = 3
DEFAULT_DRIFT_MIN_SAMPLES = 4

PR5189_IMPLEMENTATION_DIR = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/research/"
    "bouchaud_microstructure_ohlcv_proxy_v1_research_generation_preparation_v0_20260715T001201Z"
)
PR5189_CLOSEOUT_DIR = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/research/"
    "pr5189_merge_closeout_bouchaud_microstructure_ohlcv_proxy_v1_research_generation_"
    "preparation_v0_20260715T002136Z"
)
PR5190_IMPLEMENTATION_DIR = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/research/"
    "bouchaud_microstructure_ohlcv_proxy_v1_offline_productive_linear_diagnostics_"
    "feature_matrix_binding_v0_20260715T002940Z"
)
PR5190_CLOSEOUT_DIR = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/research/"
    "pr5190_merge_closeout_bouchaud_microstructure_ohlcv_proxy_v1_offline_productive_linear_"
    "diagnostics_feature_matrix_binding_v0_20260715T003858Z"
)


class ExecutionStatus(str, Enum):
    COMPLETE = "COMPLETE"
    FEATURE_DIGEST_MISMATCH = "FEATURE_DIGEST_MISMATCH"
    TARGET_BINDING_MISSING = "TARGET_BINDING_MISSING"
    FEATURE_CONTRACT_MISSING = "FEATURE_CONTRACT_MISSING"
    DIAGNOSTIC_EXECUTION_FAILED = "DIAGNOSTIC_EXECUTION_FAILED"
    SUPPORT_BUNDLE_BINDING_FAILED = "SUPPORT_BUNDLE_BINDING_FAILED"


class ExecutionValidationError(ValueError):
    """Fail-closed Bouchaud linear diagnostics execution error."""


@dataclass(frozen=True)
class DiagnosticClassExecutionV0:
    diagnostic_class: str
    consumer_owner: str
    status: str
    reason_codes: tuple[str, ...]
    authority_effect: str
    runtime_effect: str
    feature_matrix_digest: str
    target_digest: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "diagnostic_class": self.diagnostic_class,
            "consumer_owner": self.consumer_owner,
            "status": self.status,
            "reason_codes": list(self.reason_codes),
            "authority_effect": self.authority_effect,
            "runtime_effect": self.runtime_effect,
            "feature_matrix_digest": self.feature_matrix_digest,
            "target_digest": self.target_digest,
        }


@dataclass(frozen=True)
class BouchaudLinearDiagnosticsExecutionV0:
    schema_version: str
    evidence_type: str
    execution_id: str
    owner: str
    research_scope: str
    hypothesis_id: str
    pr5190_adapter_owner: str
    feature_matrix_owner: str
    feature_digest_owner: str
    support_bundle_owner: str
    dataset_id: str
    dataset_digest: str
    instrument_id: str
    feature_names: tuple[str, ...]
    target_name: str
    feature_digest: str
    target_digest: str
    feature_matrix_binding: Mapping[str, Any]
    target_binding: Mapping[str, Any]
    no_lookahead_contract: Mapping[str, Any]
    diagnostic_class_executions: tuple[DiagnosticClassExecutionV0, ...]
    diagnostic_payloads: Mapping[str, Any]
    productive_support_bundle: Mapping[str, Any]
    pr5190_binding_status: str
    execution_status: str
    execution_reason_codes: tuple[str, ...]
    economic_evaluation_executed: bool
    runtime_effect: str
    authority_effect: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "evidence_type": self.evidence_type,
            "execution_id": self.execution_id,
            "owner": self.owner,
            "research_scope": self.research_scope,
            "hypothesis_id": self.hypothesis_id,
            "pr5190_adapter_owner": self.pr5190_adapter_owner,
            "feature_matrix_owner": self.feature_matrix_owner,
            "feature_digest_owner": self.feature_digest_owner,
            "support_bundle_owner": self.support_bundle_owner,
            "dataset_id": self.dataset_id,
            "dataset_digest": self.dataset_digest,
            "instrument_id": self.instrument_id,
            "feature_names": list(self.feature_names),
            "target_name": self.target_name,
            "feature_digest": self.feature_digest,
            "target_digest": self.target_digest,
            "feature_matrix_binding": dict(self.feature_matrix_binding),
            "target_binding": dict(self.target_binding),
            "no_lookahead_contract": dict(self.no_lookahead_contract),
            "diagnostic_class_executions": [
                item.to_dict() for item in self.diagnostic_class_executions
            ],
            "diagnostic_payloads": dict(self.diagnostic_payloads),
            "productive_support_bundle": dict(self.productive_support_bundle),
            "pr5190_binding_status": self.pr5190_binding_status,
            "execution_status": self.execution_status,
            "execution_reason_codes": list(self.execution_reason_codes),
            "economic_evaluation_executed": self.economic_evaluation_executed,
            "runtime_effect": self.runtime_effect,
            "authority_effect": self.authority_effect,
        }


def _stable_digest(payload: object) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _serialize_evidence(obj: object) -> dict[str, Any]:
    if hasattr(obj, "to_dict") and callable(obj.to_dict):
        payload = obj.to_dict()
        if isinstance(payload, dict):
            return payload
    if is_dataclass(obj):
        return asdict(obj)
    raise ExecutionValidationError(f"UNSUPPORTED_EVIDENCE_TYPE:{type(obj).__name__}")


def _feature_matrix_binding_to_dict(binding: FeatureMatrixBindingV1) -> dict[str, Any]:
    return {
        "target_name": binding.target_name,
        "feature_names": list(binding.feature_names),
        "n_samples": binding.n_samples,
        "n_features": binding.n_features,
        "feature_matrix_digest": binding.feature_matrix_digest,
        "target_digest": binding.target_digest,
        "validation_policy": binding.validation_policy,
        "time_range": dict(binding.time_range),
        "row_count_before_filter": binding.row_count_before_filter,
        "row_count_after_filter": binding.row_count_after_filter,
        "dropped_rows_by_reason": dict(binding.dropped_rows_by_reason),
        "status": binding.status,
        "reason_codes": list(binding.reason_codes),
    }


def _feature_availability_time_before(decision_time: str) -> str:
    parsed = datetime.fromisoformat(decision_time.replace("Z", "+00:00")).astimezone(timezone.utc)
    earlier = parsed - timedelta(minutes=1)
    return earlier.strftime("%Y-%m-%dT%H:%M:%SZ")


def _rows_to_drift_inputs(
    rows: Sequence[Mapping[str, object]],
    *,
    feature_names: Sequence[str],
    target_name: str,
    instrument_id: str,
) -> tuple[RollingLinearDriftInputV1, ...]:
    records: list[RollingLinearDriftInputV1] = []
    for row in rows:
        decision_time = str(row["decision_time"])
        features = {name: float(row[name]) for name in feature_names}
        records.append(
            RollingLinearDriftInputV1(
                instrument_id=instrument_id,
                decision_time=decision_time,
                feature_availability_time=_feature_availability_time_before(decision_time),
                target=float(row[target_name]),
                features=features,
            )
        )
    return tuple(records)


def _rows_to_sensitivity_inputs(
    rows: Sequence[Mapping[str, object]],
    *,
    feature_names: Sequence[str],
    target_name: str,
    instrument_id: str,
) -> tuple[ParameterSensitivityInputV1, ...]:
    records: list[ParameterSensitivityInputV1] = []
    for row in rows:
        decision_time = str(row["decision_time"])
        features = {name: float(row[name]) for name in feature_names}
        records.append(
            ParameterSensitivityInputV1(
                instrument_id=instrument_id,
                decision_time=decision_time,
                feature_availability_time=_feature_availability_time_before(decision_time),
                target=float(row[target_name]),
                features=features,
            )
        )
    return tuple(records)


def _rows_to_factor_inputs(
    rows: Sequence[Mapping[str, object]],
    *,
    feature_names: Sequence[str],
    target_name: str,
    instrument_id: str,
) -> tuple[FactorExposureInputV1, ...]:
    records: list[FactorExposureInputV1] = []
    for idx, row in enumerate(rows, start=1):
        decision_time = str(row["decision_time"])
        feature_time = _feature_availability_time_before(decision_time)
        features = {name: float(row[name]) for name in feature_names}
        records.append(
            FactorExposureInputV1(
                instrument_id=instrument_id,
                timestamp=idx,
                target_return=float(row[target_name]),
                factor_values=features,
                decision_time=decision_time,
                factor_time=feature_time,
            )
        )
    return tuple(records)


def _execution_record(
    *,
    diagnostic_class: str,
    consumer_owner: str,
    evidence: object,
) -> tuple[DiagnosticClassExecutionV0, dict[str, Any]]:
    payload = _serialize_evidence(evidence)
    status = str(payload.get("status", "INCONCLUSIVE"))
    reason_codes_raw = payload.get("reason_codes", [])
    reason_codes = tuple(str(item) for item in reason_codes_raw) if reason_codes_raw else ()
    execution = DiagnosticClassExecutionV0(
        diagnostic_class=diagnostic_class,
        consumer_owner=consumer_owner,
        status=status,
        reason_codes=reason_codes,
        authority_effect=str(payload.get("authority_effect", AUTHORITY_EFFECT)),
        runtime_effect=str(payload.get("runtime_effect", RUNTIME_EFFECT)),
        feature_matrix_digest=str(payload.get("feature_matrix_digest", "")),
        target_digest=str(payload.get("target_digest", "")),
    )
    payload["authority_effect"] = execution.authority_effect
    payload["runtime_effect"] = execution.runtime_effect
    return execution, payload


def execute_bouchaud_diagnostic_payloads_v0(
    *,
    rows: Sequence[Mapping[str, object]],
    binding: FeatureMatrixBindingV1,
    canonical_digest: str,
) -> tuple[dict[str, dict[str, Any]], tuple[DiagnosticClassExecutionV0, ...]]:
    if binding.feature_matrix_digest != canonical_digest:
        raise ExecutionValidationError("FEATURE_DIGEST_IDENTITY_MISMATCH")

    x, y, rebound = build_feature_matrix_binding(
        rows,
        feature_names=binding.feature_names,
        target_name=binding.target_name,
        validation_policy=binding.validation_policy,
    )
    if rebound.feature_matrix_digest != canonical_digest:
        raise ExecutionValidationError("FEATURE_MATRIX_REBIND_DIGEST_MISMATCH")

    payloads: dict[str, dict[str, Any]] = {}
    executions: list[DiagnosticClassExecutionV0] = []

    cost_owner = "src/research/linear_evidence/cost_model.py"
    model_evidence = fit_ols_lstsq(
        x,
        y,
        binding,
        instrument_universe_digest=_stable_digest({"instrument_id": INSTRUMENT_ID}),
    )
    predicted = np.asarray(
        [
            sum(
                model_evidence.coefficients.get(name, 0.0) * float(x[i, j])
                for j, name in enumerate(binding.feature_names)
            )
            + model_evidence.coefficients.get("intercept", 0.0)
            for i in range(x.shape[0])
        ],
        dtype=float,
    )
    calibration = build_cost_model_calibration_evidence(
        model_evidence,
        observed_target_bps=y * 10_000.0,
        predicted_target_bps=predicted * 10_000.0,
    )
    cost_execution, cost_payload = _execution_record(
        diagnostic_class="cost_diagnostics",
        consumer_owner=cost_owner,
        evidence=calibration,
    )
    payloads["cost_diagnostics"] = cost_payload
    executions.append(cost_execution)

    ortho_owner = "src/research/linear_evidence/signal_orthogonality.py"
    ortho_evidence = analyze_signal_orthogonality(
        rows,
        binding.feature_names,
        target_name=binding.target_name,
        config=SignalOrthogonalityConfigV1(min_samples=4),
        productive_binding_gap=False,
    )
    ortho_execution, ortho_payload = _execution_record(
        diagnostic_class="signal_orthogonality",
        consumer_owner=ortho_owner,
        evidence=ortho_evidence,
    )
    payloads["signal_orthogonality"] = ortho_payload
    executions.append(ortho_execution)

    factor_owner = "src/research/linear_evidence/factor_exposure.py"
    factor_records = _rows_to_factor_inputs(
        rows,
        feature_names=binding.feature_names,
        target_name=binding.target_name,
        instrument_id=INSTRUMENT_ID,
    )
    factor_evidence = fit_factor_exposure_diagnostics_v0(factor_records, fixture_scaffold=True)
    factor_execution, factor_payload = _execution_record(
        diagnostic_class="factor_exposure",
        consumer_owner=factor_owner,
        evidence=factor_evidence,
    )
    payloads["factor_exposure"] = factor_payload
    executions.append(factor_execution)

    sensitivity_owner = "src/research/linear_evidence/sensitivity.py"
    sensitivity_records = _rows_to_sensitivity_inputs(
        rows,
        feature_names=binding.feature_names,
        target_name=binding.target_name,
        instrument_id=INSTRUMENT_ID,
    )
    sensitivity_evidence = fit_parameter_sensitivity_surface(
        sensitivity_records,
        grid=DEFAULT_PARAMETER_GRID,
        target_name="target",
        min_samples=4,
        min_grid_points=3,
    )
    sensitivity_execution, sensitivity_payload = _execution_record(
        diagnostic_class="parameter_sensitivity",
        consumer_owner=sensitivity_owner,
        evidence=sensitivity_evidence,
    )
    payloads["parameter_sensitivity"] = sensitivity_payload
    executions.append(sensitivity_execution)

    drift_owner = "src/research/linear_evidence/drift.py"
    drift_records = _rows_to_drift_inputs(
        rows,
        feature_names=binding.feature_names,
        target_name=binding.target_name,
        instrument_id=INSTRUMENT_ID,
    )
    drift_evidence = fit_rolling_linear_drift(
        drift_records,
        target_name="target",
        window_size=DEFAULT_DRIFT_WINDOW_SIZE,
        window_step=DEFAULT_DRIFT_WINDOW_STEP,
        min_samples=DEFAULT_DRIFT_MIN_SAMPLES,
    )
    drift_execution, drift_payload = _execution_record(
        diagnostic_class="rolling_linear_drift",
        consumer_owner=drift_owner,
        evidence=drift_evidence,
    )
    payloads["rolling_linear_drift"] = drift_payload
    executions.append(drift_execution)

    if set(payloads) != set(DIAGNOSTIC_CLASS_ORDER):
        raise ExecutionValidationError("DIAGNOSTIC_CLASS_INVENTORY_MISMATCH")

    return payloads, tuple(executions)


def materialize_bouchaud_linear_diagnostics_execution_and_support_evidence_v0(
    *,
    rows: Sequence[Mapping[str, object]],
    binding: FeatureMatrixBindingV1,
    feature_digest: str,
    source_specs: Sequence[SourceBundleSpecV0],
    verify_fn: Callable[[Path], tuple[bool, str]],
    repo_root: Path | None = None,
    target_binding: Mapping[str, Any] | None = None,
    no_lookahead_contract: Mapping[str, Any] | None = None,
) -> tuple[dict[str, Any], BouchaudLinearDiagnosticsExecutionV0]:
    if feature_digest != CANONICAL_FEATURE_DIGEST:
        raise ExecutionValidationError("CANONICAL_FEATURE_DIGEST_MISMATCH")
    if binding.feature_matrix_digest != feature_digest:
        raise ExecutionValidationError("FEATURE_DIGEST_BINDING_MISMATCH")

    resolved_target_binding = target_binding or build_target_binding()
    if str(resolved_target_binding.get("target_name")) != TARGET_NAME:
        raise ExecutionValidationError("TARGET_BINDING_MISSING")

    resolved_no_lookahead = no_lookahead_contract or validate_no_lookahead_contract_v0(rows)
    if not resolved_no_lookahead.get("no_lookahead"):
        raise ExecutionValidationError("NO_LOOKAHEAD_CONTRACT_VIOLATION")

    support_bundle = build_productive_linear_diagnostics_support_bundle_artifacts_v0(
        source_specs=source_specs,
        verify_fn=verify_fn,
        repo_root=repo_root,
    )
    try:
        validate_support_bundle_artifacts_v0(support_bundle)
    except SupportBundleValidationError as exc:
        raise ExecutionValidationError(str(exc)) from exc

    diagnostic_payloads, diagnostic_executions = execute_bouchaud_diagnostic_payloads_v0(
        rows=rows,
        binding=binding,
        canonical_digest=feature_digest,
    )

    pr5190_binding = bind_bouchaud_feature_matrix_to_linear_diagnostics_v0(
        rows=rows,
        binding=binding,
        feature_digest=feature_digest,
        support_bundle=support_bundle,
        target_binding=resolved_target_binding,
        no_lookahead_contract=resolved_no_lookahead,
    )

    reason_codes: list[str] = []
    all_complete = True
    for item in diagnostic_executions:
        if item.authority_effect != AUTHORITY_EFFECT or item.runtime_effect != RUNTIME_EFFECT:
            all_complete = False
            reason_codes.append(f"AUTHORITY_BOUNDARY_VIOLATION:{item.diagnostic_class}")
    if pr5190_binding.binding_status != FeatureMatrixBindingStatus.BOUND.value:
        all_complete = False
        reason_codes.append(f"PR5190_BINDING_NOT_BOUND:{pr5190_binding.binding_status}")
    if len(diagnostic_executions) != len(DIAGNOSTIC_CLASS_ORDER):
        all_complete = False
        reason_codes.append("INCOMPLETE_DIAGNOSTIC_CLASS_EXECUTION")
    else:
        reason_codes.append("ALL_DIAGNOSTIC_CLASSES_EXECUTED")

    execution_status = (
        ExecutionStatus.COMPLETE.value
        if all_complete
        else ExecutionStatus.DIAGNOSTIC_EXECUTION_FAILED.value
    )

    result = BouchaudLinearDiagnosticsExecutionV0(
        schema_version=SCHEMA_VERSION,
        evidence_type=EVIDENCE_TYPE,
        execution_id=EXECUTION_ID,
        owner=EXECUTION_OWNER,
        research_scope=RESEARCH_SCOPE,
        hypothesis_id=HYPOTHESIS_ID,
        pr5190_adapter_owner=PR5190_ADAPTER_OWNER,
        feature_matrix_owner=FEATURE_MATRIX_OWNER,
        feature_digest_owner=FEATURE_DIGEST_OWNER,
        support_bundle_owner=SUPPORT_BUNDLE_OWNER,
        dataset_id=DATASET_ID,
        dataset_digest=DATASET_DIGEST,
        instrument_id=INSTRUMENT_ID,
        feature_names=tuple(binding.feature_names),
        target_name=binding.target_name,
        feature_digest=feature_digest,
        target_digest=binding.target_digest,
        feature_matrix_binding=_feature_matrix_binding_to_dict(binding),
        target_binding=dict(resolved_target_binding),
        no_lookahead_contract=dict(resolved_no_lookahead),
        diagnostic_class_executions=diagnostic_executions,
        diagnostic_payloads=diagnostic_payloads,
        productive_support_bundle=support_bundle,
        pr5190_binding_status=pr5190_binding.binding_status,
        execution_status=execution_status,
        execution_reason_codes=tuple(sorted(set(reason_codes))),
        economic_evaluation_executed=False,
        runtime_effect=RUNTIME_EFFECT,
        authority_effect=AUTHORITY_EFFECT,
    )

    payload = result.to_dict()
    payload["preparation_id"] = PREPARATION_ID
    payload["output_digest"] = _stable_digest(
        {
            "feature_digest": feature_digest,
            "support_bundle_output_digest": support_bundle["output_digest"],
            "diagnostic_class_executions": payload["diagnostic_class_executions"],
            "pr5190_binding_status": pr5190_binding.binding_status,
        }
    )
    return payload, result


__all__ = [
    "AUTHORITY_EFFECT",
    "CANONICAL_FEATURE_DIGEST",
    "CANONICAL_OWNER",
    "BouchaudLinearDiagnosticsExecutionV0",
    "DiagnosticClassExecutionV0",
    "EVIDENCE_TYPE",
    "EXECUTION_ID",
    "EXECUTION_OWNER",
    "ExecutionStatus",
    "ExecutionValidationError",
    "FEATURE_DIGEST_OWNER",
    "FEATURE_MATRIX_OWNER",
    "PACKAGE_MARKER",
    "PR5189_CLOSEOUT_DIR",
    "PR5189_IMPLEMENTATION_DIR",
    "PR5190_ADAPTER_OWNER",
    "PR5190_CLOSEOUT_DIR",
    "PR5190_IMPLEMENTATION_DIR",
    "RUNTIME_EFFECT",
    "SCHEMA_VERSION",
    "SUPPORT_BUNDLE_OWNER",
    "execute_bouchaud_diagnostic_payloads_v0",
    "materialize_bouchaud_linear_diagnostics_execution_and_support_evidence_v0",
]
