"""Offline productive linear diagnostics economic evidence consumer binding v0.

Narrow adapter: consumes manifest-verified support bundle artifacts and binds
all five diagnostic references into the canonical EconomicViabilityEvidenceV1
support-ref contract. Diagnostic-only — no economic evaluation, promotion
authority, or runtime effect.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, replace
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from src.backtest.economic_viability_evidence_v1 import (
    ECONOMIC_VIABILITY_EVIDENCE_OWNER,
    EconomicViabilityEvidenceV1,
)
from src.research.linear_evidence.offline_productive_linear_diagnostics_support_bundle_v0 import (
    AUTHORITY_EFFECT,
    DIAGNOSTIC_CLASS_ORDER,
    EconomicViabilitySupportStatus,
    RUNTIME_EFFECT,
    SourceBundleSpecV0,
    SupportAggregateStatus,
    SupportBundleValidationError,
    build_productive_linear_diagnostics_support_bundle_artifacts_v0,
    validate_support_bundle_artifacts_v0,
)

CONSUMER_BINDING_SCHEMA_VERSION = (
    "offline_productive_linear_diagnostics_economic_evidence_consumer_binding.v0"
)
CONSUMER_BINDING_EVIDENCE_TYPE = (
    "OFFLINE_PRODUCTIVE_LINEAR_DIAGNOSTICS_ECONOMIC_EVIDENCE_CONSUMER_BINDING_V0"
)
CONSUMER_BINDING_OWNER = (
    "research.linear_evidence."
    "offline_productive_linear_diagnostics_economic_evidence_consumer_binding_v0"
)
ECONOMIC_VIABILITY_EVIDENCE_CONSUMER_TARGET = ECONOMIC_VIABILITY_EVIDENCE_OWNER

_REF_FIELD_BY_CLASS: dict[str, str] = {
    "cost_diagnostics": "cost_diagnostics_ref",
    "signal_orthogonality": "signal_orthogonality_ref",
    "factor_exposure": "factor_exposure_ref",
    "parameter_sensitivity": "parameter_sensitivity_ref",
    "rolling_linear_drift": "rolling_linear_drift_ref",
}

_RUNBOOK_REF_FIELD_BY_CLASS: dict[str, str] = {
    "cost_diagnostics": "cost_model_calibration_ref",
    "signal_orthogonality": "signal_orthogonality_ref",
    "factor_exposure": "factor_exposure_ref",
    "parameter_sensitivity": "parameter_sensitivity_ref",
    "rolling_linear_drift": "rolling_linear_drift_ref",
}

_CLASS_BLOCKING_REASON_CODE: dict[tuple[str, str], str] = {
    ("cost_diagnostics", "RANK_DEFICIENT_BLOCKED"): "COST_DIAGNOSTICS_RANK_DEFICIENT",
    ("factor_exposure", "RANK_DEFICIENT_BLOCKED"): "FACTOR_EXPOSURE_RANK_DEFICIENT",
    (
        "rolling_linear_drift",
        "BLOCK_DRIFT_EXCEEDS_POLICY",
    ): "ROLLING_LINEAR_DRIFT_EXCEEDS_POLICY",
}


class EconomicEvidenceAdmissibility(str, Enum):
    BLOCKED_SOURCE_DIAGNOSTICS_PRESENT = "BLOCKED_SOURCE_DIAGNOSTICS_PRESENT"
    WARN_SOURCE_DIAGNOSTICS_PRESENT = "WARN_SOURCE_DIAGNOSTICS_PRESENT"
    DIAGNOSTIC_SUPPORT_REFERENCE_READY = "DIAGNOSTIC_SUPPORT_REFERENCE_READY"
    INSUFFICIENT_SOURCE_BINDING = "INSUFFICIENT_SOURCE_BINDING"
    INSUFFICIENT_OR_UNVERIFIED_SOURCE_EVIDENCE = "INSUFFICIENT_OR_UNVERIFIED_SOURCE_EVIDENCE"


class LinearDiagnosticsConsumerBindingError(ValueError):
    """Fail-closed linear diagnostics economic evidence consumer binding error."""


@dataclass(frozen=True)
class LinearDiagnosticsEconomicEvidenceConsumerBindingV0:
    schema_version: str
    owner: str
    economic_viability_evidence_consumer_target: str
    linear_diagnostics_referenced: bool
    linear_diagnostic_class_count: int
    cost_model_calibration_ref: str
    signal_orthogonality_ref: str
    factor_exposure_ref: str
    parameter_sensitivity_ref: str
    rolling_linear_drift_ref: str
    cost_diagnostics_status: str
    signal_orthogonality_status: str
    factor_exposure_status: str
    parameter_sensitivity_status: str
    rolling_linear_drift_status: str
    aggregate_status: str
    aggregate_reason_codes: tuple[str, ...]
    economic_viability_support_status: str
    linear_diagnostics_status: str
    linear_diagnostics_reason_codes: tuple[str, ...]
    economic_evidence_admissibility: str
    support_bundle_output_digest: str
    economic_pass_authority: bool
    promotion_pass_authority: bool
    strategy_selection_authority: bool
    runtime_effect: str
    authority_effect: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "owner": self.owner,
            "economic_viability_evidence_consumer_target": self.economic_viability_evidence_consumer_target,
            "linear_diagnostics_referenced": self.linear_diagnostics_referenced,
            "linear_diagnostic_class_count": self.linear_diagnostic_class_count,
            "cost_model_calibration_ref": self.cost_model_calibration_ref,
            "signal_orthogonality_ref": self.signal_orthogonality_ref,
            "factor_exposure_ref": self.factor_exposure_ref,
            "parameter_sensitivity_ref": self.parameter_sensitivity_ref,
            "rolling_linear_drift_ref": self.rolling_linear_drift_ref,
            "cost_diagnostics_status": self.cost_diagnostics_status,
            "signal_orthogonality_status": self.signal_orthogonality_status,
            "factor_exposure_status": self.factor_exposure_status,
            "parameter_sensitivity_status": self.parameter_sensitivity_status,
            "rolling_linear_drift_status": self.rolling_linear_drift_status,
            "aggregate_status": self.aggregate_status,
            "aggregate_reason_codes": list(self.aggregate_reason_codes),
            "economic_viability_support_status": self.economic_viability_support_status,
            "linear_diagnostics_status": self.linear_diagnostics_status,
            "linear_diagnostics_reason_codes": list(self.linear_diagnostics_reason_codes),
            "economic_evidence_admissibility": self.economic_evidence_admissibility,
            "support_bundle_output_digest": self.support_bundle_output_digest,
            "economic_pass_authority": self.economic_pass_authority,
            "promotion_pass_authority": self.promotion_pass_authority,
            "strategy_selection_authority": self.strategy_selection_authority,
            "runtime_effect": self.runtime_effect,
            "authority_effect": self.authority_effect,
        }


def _stable_digest(payload: object) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _normalize_reason_codes(reasons: Sequence[str]) -> tuple[str, ...]:
    return tuple(sorted({str(item) for item in reasons if str(item)}))


def classify_economic_evidence_admissibility_v0(
    economic_viability_support_status: str,
    *,
    aggregate_status: str,
) -> str:
    if aggregate_status == SupportAggregateStatus.INSUFFICIENT_OR_UNVERIFIED_SOURCE_EVIDENCE.value:
        return EconomicEvidenceAdmissibility.INSUFFICIENT_OR_UNVERIFIED_SOURCE_EVIDENCE.value
    if (
        economic_viability_support_status
        == EconomicViabilitySupportStatus.BLOCKED_SOURCE_DIAGNOSTICS_PRESENT.value
    ):
        return EconomicEvidenceAdmissibility.BLOCKED_SOURCE_DIAGNOSTICS_PRESENT.value
    if (
        economic_viability_support_status
        == EconomicViabilitySupportStatus.WARN_SOURCE_DIAGNOSTICS_PRESENT.value
    ):
        return EconomicEvidenceAdmissibility.WARN_SOURCE_DIAGNOSTICS_PRESENT.value
    if (
        economic_viability_support_status
        == EconomicViabilitySupportStatus.DIAGNOSTIC_SUPPORT_REFERENCE_READY.value
    ):
        return EconomicEvidenceAdmissibility.DIAGNOSTIC_SUPPORT_REFERENCE_READY.value
    return EconomicEvidenceAdmissibility.INSUFFICIENT_SOURCE_BINDING.value


def derive_linear_diagnostics_reason_codes_v0(
    *,
    source_statuses: Mapping[str, str],
    aggregate_reason_codes: Sequence[str],
) -> tuple[str, ...]:
    derived: list[str] = []
    for diagnostic_class, source_status in source_statuses.items():
        mapped = _CLASS_BLOCKING_REASON_CODE.get((diagnostic_class, source_status))
        if mapped:
            derived.append(mapped)
    derived.extend(str(code) for code in aggregate_reason_codes)
    return _normalize_reason_codes(derived)


def _verify_source_refs(
    support_bundle: Mapping[str, Any],
    *,
    verify_fn: Callable[[Path], tuple[bool, str]],
) -> None:
    for diagnostic_class in DIAGNOSTIC_CLASS_ORDER:
        ref_field = _REF_FIELD_BY_CLASS[diagnostic_class]
        ref_value = support_bundle.get(ref_field)
        if not isinstance(ref_value, str) or not ref_value:
            raise LinearDiagnosticsConsumerBindingError(
                f"MISSING_DIAGNOSTIC_REF:{diagnostic_class}"
            )
        bundle = Path(ref_value).expanduser().resolve()
        if not bundle.is_dir():
            raise LinearDiagnosticsConsumerBindingError(
                f"SOURCE_BUNDLE_MISSING:{diagnostic_class}:{bundle}"
            )
        ok, message = verify_fn(bundle)
        if not ok:
            raise LinearDiagnosticsConsumerBindingError(
                f"SOURCE_MANIFEST_VERIFY_FAILED:{diagnostic_class}:{message}"
            )


def _assert_no_contradictory_source_statuses(
    source_statuses: Mapping[str, str],
    *,
    expected_source_statuses: Mapping[str, str] | None,
) -> None:
    if expected_source_statuses is None:
        return
    for diagnostic_class, expected_status in expected_source_statuses.items():
        if diagnostic_class not in DIAGNOSTIC_CLASS_ORDER:
            raise LinearDiagnosticsConsumerBindingError(
                f"UNKNOWN_DIAGNOSTIC_CLASS:{diagnostic_class}"
            )
        actual_status = source_statuses.get(diagnostic_class)
        if actual_status != expected_status:
            raise LinearDiagnosticsConsumerBindingError(
                f"CONTRADICTORY_SOURCE_STATUS:{diagnostic_class}:"
                f"expected={expected_status}:actual={actual_status}"
            )


def bind_linear_diagnostics_economic_evidence_consumer_v0(
    *,
    support_bundle: Mapping[str, Any],
    verify_fn: Callable[[Path], tuple[bool, str]] | None = None,
    expected_source_statuses: Mapping[str, str] | None = None,
) -> LinearDiagnosticsEconomicEvidenceConsumerBindingV0:
    try:
        validate_support_bundle_artifacts_v0(support_bundle)
    except SupportBundleValidationError as exc:
        raise LinearDiagnosticsConsumerBindingError(str(exc)) from exc

    if verify_fn is not None:
        _verify_source_refs(support_bundle, verify_fn=verify_fn)

    source_statuses = support_bundle["source_statuses"]
    if not isinstance(source_statuses, Mapping):
        raise LinearDiagnosticsConsumerBindingError("SOURCE_STATUSES_NOT_MAPPING")

    for diagnostic_class in DIAGNOSTIC_CLASS_ORDER:
        if diagnostic_class not in source_statuses:
            raise LinearDiagnosticsConsumerBindingError(f"MISSING_SOURCE_STATUS:{diagnostic_class}")
        ref_field = _REF_FIELD_BY_CLASS[diagnostic_class]
        if not support_bundle.get(ref_field):
            raise LinearDiagnosticsConsumerBindingError(
                f"MISSING_DIAGNOSTIC_REF:{diagnostic_class}"
            )

    _assert_no_contradictory_source_statuses(
        source_statuses,
        expected_source_statuses=expected_source_statuses,
    )

    aggregate_status = str(support_bundle["aggregate_status"])
    aggregate_reason_codes = tuple(str(code) for code in support_bundle["aggregate_reason_codes"])
    economic_viability_support_status = str(support_bundle["economic_viability_support_status"])
    linear_diagnostics_status = aggregate_status
    linear_diagnostics_reason_codes = derive_linear_diagnostics_reason_codes_v0(
        source_statuses=source_statuses,
        aggregate_reason_codes=aggregate_reason_codes,
    )
    economic_evidence_admissibility = classify_economic_evidence_admissibility_v0(
        economic_viability_support_status,
        aggregate_status=aggregate_status,
    )

    runbook_refs = {
        runbook_field: str(support_bundle[_REF_FIELD_BY_CLASS[diagnostic_class]])
        for diagnostic_class, runbook_field in _RUNBOOK_REF_FIELD_BY_CLASS.items()
    }

    return LinearDiagnosticsEconomicEvidenceConsumerBindingV0(
        schema_version=CONSUMER_BINDING_SCHEMA_VERSION,
        owner=CONSUMER_BINDING_OWNER,
        economic_viability_evidence_consumer_target=ECONOMIC_VIABILITY_EVIDENCE_CONSUMER_TARGET,
        linear_diagnostics_referenced=True,
        linear_diagnostic_class_count=int(support_bundle["diagnostic_class_present_count"]),
        cost_model_calibration_ref=runbook_refs["cost_model_calibration_ref"],
        signal_orthogonality_ref=runbook_refs["signal_orthogonality_ref"],
        factor_exposure_ref=runbook_refs["factor_exposure_ref"],
        parameter_sensitivity_ref=runbook_refs["parameter_sensitivity_ref"],
        rolling_linear_drift_ref=runbook_refs["rolling_linear_drift_ref"],
        cost_diagnostics_status=str(source_statuses["cost_diagnostics"]),
        signal_orthogonality_status=str(source_statuses["signal_orthogonality"]),
        factor_exposure_status=str(source_statuses["factor_exposure"]),
        parameter_sensitivity_status=str(source_statuses["parameter_sensitivity"]),
        rolling_linear_drift_status=str(source_statuses["rolling_linear_drift"]),
        aggregate_status=aggregate_status,
        aggregate_reason_codes=aggregate_reason_codes,
        economic_viability_support_status=economic_viability_support_status,
        linear_diagnostics_status=linear_diagnostics_status,
        linear_diagnostics_reason_codes=linear_diagnostics_reason_codes,
        economic_evidence_admissibility=economic_evidence_admissibility,
        support_bundle_output_digest=str(support_bundle["output_digest"]),
        economic_pass_authority=False,
        promotion_pass_authority=False,
        strategy_selection_authority=False,
        runtime_effect=RUNTIME_EFFECT,
        authority_effect=AUTHORITY_EFFECT,
    )


def materialize_linear_diagnostics_economic_evidence_consumer_binding_v0(
    *,
    source_specs: Sequence[SourceBundleSpecV0],
    verify_fn: Callable[[Path], tuple[bool, str]],
    repo_root: Path | None = None,
    expected_source_statuses: Mapping[str, str] | None = None,
) -> tuple[dict[str, Any], LinearDiagnosticsEconomicEvidenceConsumerBindingV0]:
    support_bundle = build_productive_linear_diagnostics_support_bundle_artifacts_v0(
        source_specs=source_specs,
        verify_fn=verify_fn,
        repo_root=repo_root,
    )
    binding = bind_linear_diagnostics_economic_evidence_consumer_v0(
        support_bundle=support_bundle,
        verify_fn=verify_fn,
        expected_source_statuses=expected_source_statuses,
    )
    payload = binding.to_dict()
    payload["consumer_binding_digest"] = _stable_digest(payload)
    return support_bundle, binding


def apply_linear_diagnostics_refs_to_economic_viability_evidence_v0(
    evidence: EconomicViabilityEvidenceV1,
    binding: LinearDiagnosticsEconomicEvidenceConsumerBindingV0,
) -> EconomicViabilityEvidenceV1:
    """Return evidence with optional factor_exposure_ref bound when absent.

    Does not mutate status, reason_codes, or economic validity fields.
    """
    if evidence.factor_exposure_ref is not None:
        if evidence.factor_exposure_ref != binding.factor_exposure_ref:
            raise LinearDiagnosticsConsumerBindingError("FACTOR_EXPOSURE_REF_CONTRADICTS_EVIDENCE")
        return evidence
    return replace(evidence, factor_exposure_ref=binding.factor_exposure_ref)


__all__ = [
    "AUTHORITY_EFFECT",
    "CONSUMER_BINDING_EVIDENCE_TYPE",
    "CONSUMER_BINDING_OWNER",
    "CONSUMER_BINDING_SCHEMA_VERSION",
    "ECONOMIC_VIABILITY_EVIDENCE_CONSUMER_TARGET",
    "EconomicEvidenceAdmissibility",
    "LinearDiagnosticsConsumerBindingError",
    "LinearDiagnosticsEconomicEvidenceConsumerBindingV0",
    "RUNTIME_EFFECT",
    "apply_linear_diagnostics_refs_to_economic_viability_evidence_v0",
    "bind_linear_diagnostics_economic_evidence_consumer_v0",
    "classify_economic_evidence_admissibility_v0",
    "derive_linear_diagnostics_reason_codes_v0",
    "materialize_linear_diagnostics_economic_evidence_consumer_binding_v0",
]
