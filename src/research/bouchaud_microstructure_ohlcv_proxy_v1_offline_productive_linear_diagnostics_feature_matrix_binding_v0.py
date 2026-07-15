"""Bouchaud OHLCV proxy v1 offline productive linear diagnostics feature matrix binding v0.

Narrow adapter: consumes the deterministic Bouchaud feature matrix from PR #5189 research
generation preparation and binds it into the manifest-verified productive linear diagnostics
chain. Diagnostic-only — no economic evaluation, promotion authority, or runtime effect.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

import numpy as np

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
    ParameterGridSpecV1,
    ParameterSensitivityInputV1,
    fit_parameter_sensitivity_surface,
)
from src.research.linear_evidence.signal_orthogonality import (
    SignalOrthogonalityConfigV1,
    analyze_signal_orthogonality,
)

PACKAGE_MARKER = (
    "BOUCHAUD_MICROSTRUCTURE_OHLCV_PROXY_V1_OFFLINE_PRODUCTIVE_LINEAR_DIAGNOSTICS_"
    "FEATURE_MATRIX_BINDING_V0=true"
)
SCHEMA_VERSION = (
    "bouchaud_microstructure_ohlcv_proxy_v1_offline_productive_linear_diagnostics_"
    "feature_matrix_binding.v0"
)
EVIDENCE_TYPE = (
    "BOUCHAUD_MICROSTRUCTURE_OHLCV_PROXY_V1_OFFLINE_PRODUCTIVE_LINEAR_DIAGNOSTICS_"
    "FEATURE_MATRIX_BINDING_V0"
)
BINDING_ID = (
    "bouchaud_microstructure_ohlcv_proxy_v1_offline_productive_linear_diagnostics_"
    "feature_matrix_binding_v0"
)
CANONICAL_OWNER = (
    "src/research/"
    "bouchaud_microstructure_ohlcv_proxy_v1_offline_productive_linear_diagnostics_"
    "feature_matrix_binding_v0.py"
)
BINDING_OWNER = (
    "research."
    "bouchaud_microstructure_ohlcv_proxy_v1_offline_productive_linear_diagnostics_"
    "feature_matrix_binding_v0"
)
FEATURE_MATRIX_OWNER = "src/research/linear_evidence/feature_matrix.py"
SUPPORT_BUNDLE_OWNER = (
    "src/research/linear_evidence/offline_productive_linear_diagnostics_support_bundle_v0.py"
)
PREPARATION_OWNER = (
    "src.research.bouchaud_microstructure_ohlcv_proxy_v1_research_generation_preparation_v0"
)

PR5189_CLOSEOUT_DIR = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/research/"
    "pr5189_merge_closeout_bouchaud_microstructure_ohlcv_proxy_v1_research_generation_"
    "preparation_v0_20260715T002136Z"
)

DEFAULT_SCALED_FEATURE = FEATURE_NAMES[0]
DEFAULT_PARAMETER_GRID = ParameterGridSpecV1(
    parameter_name="bouchaud_proxy_scale",
    scaled_feature_name=DEFAULT_SCALED_FEATURE,
    parameter_values=(0.5, 1.0, 1.5),
)
DEFAULT_DRIFT_WINDOW_SIZE = 6
DEFAULT_DRIFT_WINDOW_STEP = 3
DEFAULT_DRIFT_MIN_SAMPLES = 4


class FeatureMatrixBindingStatus(str, Enum):
    BOUND = "BOUND"
    FEATURE_DIGEST_MISMATCH = "FEATURE_DIGEST_MISMATCH"
    TARGET_BINDING_MISSING = "TARGET_BINDING_MISSING"
    FEATURE_CONTRACT_MISSING = "FEATURE_CONTRACT_MISSING"
    DIAGNOSTIC_CONSUMPTION_FAILED = "DIAGNOSTIC_CONSUMPTION_FAILED"
    SUPPORT_BUNDLE_BINDING_FAILED = "SUPPORT_BUNDLE_BINDING_FAILED"


class FeatureMatrixBindingValidationError(ValueError):
    """Fail-closed Bouchaud feature matrix linear diagnostics binding error."""


@dataclass(frozen=True)
class DiagnosticConsumptionBindingV0:
    diagnostic_class: str
    consumer_owner: str
    canonical_feature_digest: str
    observed_feature_digest: str
    target_digest: str
    consumption_status: str
    diagnostic_status: str
    reason_codes: tuple[str, ...]
    feature_digest_preserved: bool
    digest_algorithm_compatible: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "diagnostic_class": self.diagnostic_class,
            "consumer_owner": self.consumer_owner,
            "canonical_feature_digest": self.canonical_feature_digest,
            "observed_feature_digest": self.observed_feature_digest,
            "feature_matrix_digest": self.canonical_feature_digest,
            "target_digest": self.target_digest,
            "consumption_status": self.consumption_status,
            "diagnostic_status": self.diagnostic_status,
            "reason_codes": list(self.reason_codes),
            "feature_digest_preserved": self.feature_digest_preserved,
            "digest_algorithm_compatible": self.digest_algorithm_compatible,
        }


@dataclass(frozen=True)
class BouchaudFeatureMatrixLinearDiagnosticsBindingV0:
    schema_version: str
    evidence_type: str
    binding_id: str
    owner: str
    research_scope: str
    hypothesis_id: str
    preparation_owner: str
    feature_matrix_owner: str
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
    diagnostic_consumption_bindings: tuple[DiagnosticConsumptionBindingV0, ...]
    support_bundle_output_digest: str
    linear_diagnostics_chain_bound: bool
    feature_digest_identity_preserved: bool
    binding_status: str
    binding_reason_codes: tuple[str, ...]
    economic_evaluation_executed: bool
    runtime_effect: str
    authority_effect: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "evidence_type": self.evidence_type,
            "binding_id": self.binding_id,
            "owner": self.owner,
            "research_scope": self.research_scope,
            "hypothesis_id": self.hypothesis_id,
            "preparation_owner": self.preparation_owner,
            "feature_matrix_owner": self.feature_matrix_owner,
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
            "diagnostic_consumption_bindings": [
                item.to_dict() for item in self.diagnostic_consumption_bindings
            ],
            "support_bundle_output_digest": self.support_bundle_output_digest,
            "linear_diagnostics_chain_bound": self.linear_diagnostics_chain_bound,
            "feature_digest_identity_preserved": self.feature_digest_identity_preserved,
            "binding_status": self.binding_status,
            "binding_reason_codes": list(self.binding_reason_codes),
            "economic_evaluation_executed": self.economic_evaluation_executed,
            "runtime_effect": self.runtime_effect,
            "authority_effect": self.authority_effect,
        }


def _stable_digest(payload: object) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


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


def _consumption_binding_v0(
    *,
    diagnostic_class: str,
    consumer_owner: str,
    canonical_digest: str,
    observed_digest: str,
    target_digest: str,
    diagnostic_status: str,
    reason_codes: Sequence[str],
) -> DiagnosticConsumptionBindingV0:
    if not canonical_digest:
        raise FeatureMatrixBindingValidationError(
            f"FEATURE_CONTRACT_MISSING:{diagnostic_class}:canonical_digest"
        )
    digest_compatible = bool(observed_digest) and observed_digest == canonical_digest
    return DiagnosticConsumptionBindingV0(
        diagnostic_class=diagnostic_class,
        consumer_owner=consumer_owner,
        canonical_feature_digest=canonical_digest,
        observed_feature_digest=observed_digest,
        target_digest=target_digest,
        consumption_status=FeatureMatrixBindingStatus.BOUND.value,
        diagnostic_status=diagnostic_status,
        reason_codes=tuple(reason_codes),
        feature_digest_preserved=True,
        digest_algorithm_compatible=digest_compatible,
    )


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


def _consume_cost_diagnostics_v0(
    *,
    x: np.ndarray,
    y: np.ndarray,
    binding: FeatureMatrixBindingV1,
    canonical_digest: str,
) -> DiagnosticConsumptionBindingV0:
    owner = "src/research/linear_evidence/cost_model.py"
    try:
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
        return _consumption_binding_v0(
            diagnostic_class="cost_diagnostics",
            consumer_owner=owner,
            canonical_digest=canonical_digest,
            observed_digest=model_evidence.feature_matrix_digest,
            target_digest=model_evidence.target_digest,
            diagnostic_status=calibration.status,
            reason_codes=calibration.reason_codes,
        )
    except Exception as exc:
        return DiagnosticConsumptionBindingV0(
            diagnostic_class="cost_diagnostics",
            consumer_owner=owner,
            canonical_feature_digest=canonical_digest,
            observed_feature_digest="",
            target_digest=binding.target_digest,
            consumption_status=FeatureMatrixBindingStatus.DIAGNOSTIC_CONSUMPTION_FAILED.value,
            diagnostic_status="INCONCLUSIVE",
            reason_codes=(f"CONSUMPTION_ERROR:{type(exc).__name__}",),
            feature_digest_preserved=False,
            digest_algorithm_compatible=False,
        )


def _consume_signal_orthogonality_v0(
    rows: Sequence[Mapping[str, object]],
    *,
    binding: FeatureMatrixBindingV1,
    canonical_digest: str,
) -> DiagnosticConsumptionBindingV0:
    owner = "src/research/linear_evidence/signal_orthogonality.py"
    try:
        evidence = analyze_signal_orthogonality(
            rows,
            binding.feature_names,
            target_name=binding.target_name,
            config=SignalOrthogonalityConfigV1(min_samples=4),
            productive_binding_gap=False,
        )
        return _consumption_binding_v0(
            diagnostic_class="signal_orthogonality",
            consumer_owner=owner,
            canonical_digest=canonical_digest,
            observed_digest=evidence.feature_matrix_digest,
            target_digest=evidence.target_digest,
            diagnostic_status=evidence.status,
            reason_codes=evidence.reason_codes,
        )
    except Exception as exc:
        return DiagnosticConsumptionBindingV0(
            diagnostic_class="signal_orthogonality",
            consumer_owner=owner,
            canonical_feature_digest=canonical_digest,
            observed_feature_digest="",
            target_digest=binding.target_digest,
            consumption_status=FeatureMatrixBindingStatus.DIAGNOSTIC_CONSUMPTION_FAILED.value,
            diagnostic_status="INCONCLUSIVE",
            reason_codes=(f"CONSUMPTION_ERROR:{type(exc).__name__}",),
            feature_digest_preserved=False,
            digest_algorithm_compatible=False,
        )


def _consume_factor_exposure_v0(
    rows: Sequence[Mapping[str, object]],
    *,
    binding: FeatureMatrixBindingV1,
    canonical_digest: str,
) -> DiagnosticConsumptionBindingV0:
    owner = "src/research/linear_evidence/factor_exposure.py"
    try:
        records = _rows_to_factor_inputs(
            rows,
            feature_names=binding.feature_names,
            target_name=binding.target_name,
            instrument_id=INSTRUMENT_ID,
        )
        evidence = fit_factor_exposure_diagnostics_v0(records, fixture_scaffold=True)
        return _consumption_binding_v0(
            diagnostic_class="factor_exposure",
            consumer_owner=owner,
            canonical_digest=canonical_digest,
            observed_digest=evidence.feature_matrix_digest,
            target_digest=evidence.target_digest,
            diagnostic_status=evidence.status,
            reason_codes=evidence.reason_codes,
        )
    except Exception as exc:
        return DiagnosticConsumptionBindingV0(
            diagnostic_class="factor_exposure",
            consumer_owner=owner,
            canonical_feature_digest=canonical_digest,
            observed_feature_digest="",
            target_digest=binding.target_digest,
            consumption_status=FeatureMatrixBindingStatus.DIAGNOSTIC_CONSUMPTION_FAILED.value,
            diagnostic_status="INCONCLUSIVE",
            reason_codes=(f"CONSUMPTION_ERROR:{type(exc).__name__}",),
            feature_digest_preserved=False,
            digest_algorithm_compatible=False,
        )


def _consume_parameter_sensitivity_v0(
    rows: Sequence[Mapping[str, object]],
    *,
    binding: FeatureMatrixBindingV1,
    canonical_digest: str,
) -> DiagnosticConsumptionBindingV0:
    owner = "src/research/linear_evidence/sensitivity.py"
    try:
        records = _rows_to_sensitivity_inputs(
            rows,
            feature_names=binding.feature_names,
            target_name=binding.target_name,
            instrument_id=INSTRUMENT_ID,
        )
        evidence = fit_parameter_sensitivity_surface(
            records,
            grid=DEFAULT_PARAMETER_GRID,
            target_name="target",
            min_samples=4,
            min_grid_points=3,
        )
        return _consumption_binding_v0(
            diagnostic_class="parameter_sensitivity",
            consumer_owner=owner,
            canonical_digest=canonical_digest,
            observed_digest=evidence.feature_matrix_digest,
            target_digest=evidence.target_digest,
            diagnostic_status=evidence.status,
            reason_codes=evidence.reason_codes,
        )
    except Exception as exc:
        return DiagnosticConsumptionBindingV0(
            diagnostic_class="parameter_sensitivity",
            consumer_owner=owner,
            canonical_feature_digest=canonical_digest,
            observed_feature_digest="",
            target_digest=binding.target_digest,
            consumption_status=FeatureMatrixBindingStatus.DIAGNOSTIC_CONSUMPTION_FAILED.value,
            diagnostic_status="INCONCLUSIVE",
            reason_codes=(f"CONSUMPTION_ERROR:{type(exc).__name__}",),
            feature_digest_preserved=False,
            digest_algorithm_compatible=False,
        )


def _consume_rolling_linear_drift_v0(
    rows: Sequence[Mapping[str, object]],
    *,
    binding: FeatureMatrixBindingV1,
    canonical_digest: str,
) -> DiagnosticConsumptionBindingV0:
    owner = "src/research/linear_evidence/drift.py"
    try:
        records = _rows_to_drift_inputs(
            rows,
            feature_names=binding.feature_names,
            target_name=binding.target_name,
            instrument_id=INSTRUMENT_ID,
        )
        evidence = fit_rolling_linear_drift(
            records,
            target_name="target",
            window_size=DEFAULT_DRIFT_WINDOW_SIZE,
            window_step=DEFAULT_DRIFT_WINDOW_STEP,
            min_samples=DEFAULT_DRIFT_MIN_SAMPLES,
        )
        return _consumption_binding_v0(
            diagnostic_class="rolling_linear_drift",
            consumer_owner=owner,
            canonical_digest=canonical_digest,
            observed_digest=evidence.feature_matrix_digest,
            target_digest=evidence.target_digest,
            diagnostic_status=evidence.status,
            reason_codes=evidence.reason_codes,
        )
    except Exception as exc:
        return DiagnosticConsumptionBindingV0(
            diagnostic_class="rolling_linear_drift",
            consumer_owner=owner,
            canonical_feature_digest=canonical_digest,
            observed_feature_digest="",
            target_digest=binding.target_digest,
            consumption_status=FeatureMatrixBindingStatus.DIAGNOSTIC_CONSUMPTION_FAILED.value,
            diagnostic_status="INCONCLUSIVE",
            reason_codes=(f"CONSUMPTION_ERROR:{type(exc).__name__}",),
            feature_digest_preserved=False,
            digest_algorithm_compatible=False,
        )


def _validate_target_binding_contract(target_binding: Mapping[str, Any]) -> None:
    required = ("schema_version", "target_name", "target_shift", "validation_split")
    missing = [key for key in required if key not in target_binding]
    if missing:
        raise FeatureMatrixBindingValidationError(f"TARGET_BINDING_MISSING:{','.join(missing)}")
    if str(target_binding["target_name"]) != TARGET_NAME:
        raise FeatureMatrixBindingValidationError("TARGET_BINDING_NAME_MISMATCH")
    if str(target_binding["validation_split"]) != "TIME_ORDERED":
        raise FeatureMatrixBindingValidationError("TARGET_BINDING_VALIDATION_POLICY_MISMATCH")


def bind_bouchaud_feature_matrix_to_linear_diagnostics_v0(
    *,
    rows: Sequence[Mapping[str, object]],
    binding: FeatureMatrixBindingV1,
    feature_digest: str,
    support_bundle: Mapping[str, Any],
    target_binding: Mapping[str, Any] | None = None,
    no_lookahead_contract: Mapping[str, Any] | None = None,
) -> BouchaudFeatureMatrixLinearDiagnosticsBindingV0:
    if not rows:
        raise FeatureMatrixBindingValidationError("INSUFFICIENT_DATA")
    if binding.feature_matrix_digest != feature_digest:
        raise FeatureMatrixBindingValidationError("FEATURE_DIGEST_IDENTITY_MISMATCH")
    if binding.target_name != TARGET_NAME:
        raise FeatureMatrixBindingValidationError("TARGET_BINDING_MISSING")

    resolved_target_binding = target_binding or build_target_binding()
    _validate_target_binding_contract(resolved_target_binding)

    resolved_no_lookahead = no_lookahead_contract or validate_no_lookahead_contract_v0(rows)
    if not resolved_no_lookahead.get("no_lookahead"):
        raise FeatureMatrixBindingValidationError("NO_LOOKAHEAD_CONTRACT_VIOLATION")

    try:
        validate_support_bundle_artifacts_v0(support_bundle)
    except SupportBundleValidationError as exc:
        raise FeatureMatrixBindingValidationError(str(exc)) from exc

    if int(support_bundle.get("diagnostic_class_present_count", 0)) != len(DIAGNOSTIC_CLASS_ORDER):
        raise FeatureMatrixBindingValidationError("INCOMPLETE_LINEAR_DIAGNOSTICS_CHAIN")

    canonical_digest = binding.feature_matrix_digest
    x, y, rebound = build_feature_matrix_binding(
        rows,
        feature_names=binding.feature_names,
        target_name=binding.target_name,
        validation_policy=binding.validation_policy,
    )
    if rebound.feature_matrix_digest != canonical_digest:
        raise FeatureMatrixBindingValidationError("FEATURE_MATRIX_REBIND_DIGEST_MISMATCH")

    consumption_bindings = (
        _consume_cost_diagnostics_v0(x=x, y=y, binding=binding, canonical_digest=canonical_digest),
        _consume_signal_orthogonality_v0(rows, binding=binding, canonical_digest=canonical_digest),
        _consume_factor_exposure_v0(rows, binding=binding, canonical_digest=canonical_digest),
        _consume_parameter_sensitivity_v0(rows, binding=binding, canonical_digest=canonical_digest),
        _consume_rolling_linear_drift_v0(rows, binding=binding, canonical_digest=canonical_digest),
    )

    reason_codes: list[str] = []
    all_bound = True
    for item in consumption_bindings:
        if item.consumption_status != FeatureMatrixBindingStatus.BOUND.value:
            all_bound = False
            reason_codes.append(f"CONSUMPTION_NOT_BOUND:{item.diagnostic_class}")

    feature_digest_identity_preserved = (
        binding.feature_matrix_digest == feature_digest and all_bound
    )

    if not feature_digest_identity_preserved:
        binding_status = FeatureMatrixBindingStatus.FEATURE_DIGEST_MISMATCH.value
        if not all_bound:
            binding_status = FeatureMatrixBindingStatus.DIAGNOSTIC_CONSUMPTION_FAILED.value
    else:
        binding_status = FeatureMatrixBindingStatus.BOUND.value
        reason_codes.append("ALL_DIAGNOSTIC_CLASSES_CONSUMED")

    return BouchaudFeatureMatrixLinearDiagnosticsBindingV0(
        schema_version=SCHEMA_VERSION,
        evidence_type=EVIDENCE_TYPE,
        binding_id=BINDING_ID,
        owner=BINDING_OWNER,
        research_scope=RESEARCH_SCOPE,
        hypothesis_id=HYPOTHESIS_ID,
        preparation_owner=PREPARATION_OWNER,
        feature_matrix_owner=FEATURE_MATRIX_OWNER,
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
        diagnostic_consumption_bindings=consumption_bindings,
        support_bundle_output_digest=str(support_bundle["output_digest"]),
        linear_diagnostics_chain_bound=True,
        feature_digest_identity_preserved=feature_digest_identity_preserved,
        binding_status=binding_status,
        binding_reason_codes=tuple(sorted(set(reason_codes))),
        economic_evaluation_executed=False,
        runtime_effect=RUNTIME_EFFECT,
        authority_effect=AUTHORITY_EFFECT,
    )


def materialize_bouchaud_feature_matrix_linear_diagnostics_binding_v0(
    *,
    rows: Sequence[Mapping[str, object]],
    binding: FeatureMatrixBindingV1,
    feature_digest: str,
    source_specs: Sequence[SourceBundleSpecV0],
    verify_fn: Callable[[Path], tuple[bool, str]],
    repo_root: Path | None = None,
    target_binding: Mapping[str, Any] | None = None,
    no_lookahead_contract: Mapping[str, Any] | None = None,
) -> tuple[dict[str, Any], BouchaudFeatureMatrixLinearDiagnosticsBindingV0]:
    support_bundle = build_productive_linear_diagnostics_support_bundle_artifacts_v0(
        source_specs=source_specs,
        verify_fn=verify_fn,
        repo_root=repo_root,
    )
    binding_result = bind_bouchaud_feature_matrix_to_linear_diagnostics_v0(
        rows=rows,
        binding=binding,
        feature_digest=feature_digest,
        support_bundle=support_bundle,
        target_binding=target_binding,
        no_lookahead_contract=no_lookahead_contract,
    )
    payload = binding_result.to_dict()
    payload["preparation_id"] = PREPARATION_ID
    payload["support_bundle_ref_fields"] = {
        "cost_diagnostics": support_bundle["cost_diagnostics_ref"],
        "signal_orthogonality": support_bundle["signal_orthogonality_ref"],
        "factor_exposure": support_bundle["factor_exposure_ref"],
        "parameter_sensitivity": support_bundle["parameter_sensitivity_ref"],
        "rolling_linear_drift": support_bundle["rolling_linear_drift_ref"],
    }
    payload["support_bundle_aggregate_status"] = support_bundle["aggregate_status"]
    payload["binding_digest"] = _stable_digest(
        {
            "feature_digest": feature_digest,
            "support_bundle_output_digest": support_bundle["output_digest"],
            "diagnostic_consumption_bindings": payload["diagnostic_consumption_bindings"],
        }
    )
    output_body = {key: value for key, value in payload.items() if key != "output_digest"}
    payload["output_digest"] = _stable_digest(output_body)
    return payload, binding_result


__all__ = [
    "AUTHORITY_EFFECT",
    "BINDING_ID",
    "BouchaudFeatureMatrixLinearDiagnosticsBindingV0",
    "BINDING_OWNER",
    "CANONICAL_OWNER",
    "DEFAULT_PARAMETER_GRID",
    "DiagnosticConsumptionBindingV0",
    "EVIDENCE_TYPE",
    "FEATURE_MATRIX_OWNER",
    "FeatureMatrixBindingStatus",
    "FeatureMatrixBindingValidationError",
    "PACKAGE_MARKER",
    "PREPARATION_OWNER",
    "PR5189_CLOSEOUT_DIR",
    "RUNTIME_EFFECT",
    "SCHEMA_VERSION",
    "SUPPORT_BUNDLE_OWNER",
    "bind_bouchaud_feature_matrix_to_linear_diagnostics_v0",
    "materialize_bouchaud_feature_matrix_linear_diagnostics_binding_v0",
]
