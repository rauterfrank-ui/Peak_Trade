"""Offline productive linear diagnostics support bundle v0.

Deterministically aggregates manifest-verified productive linear diagnostics into
support evidence for later EconomicViabilityEvidenceV1 reference. Diagnostic-only:
no economic evaluation, promotion authority, strategy selection, or runtime effect.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

SCHEMA_VERSION = "offline_productive_linear_diagnostics_support_bundle.v0"
EVIDENCE_TYPE = "OFFLINE_PRODUCTIVE_LINEAR_DIAGNOSTICS_SUPPORT_BUNDLE_V0"
DIAGNOSTIC_EVIDENCE_ID = "offline_productive_linear_diagnostics_support_bundle_v0"
AUTHORITY_EFFECT = "NONE"
RUNTIME_EFFECT = "NONE"

ARCHIVE_ROOT = Path("/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z")

DEFAULT_COST_DIAGNOSTICS_BUNDLE = (
    ARCHIVE_ROOT / "research/offline_linear_cost_model_diagnostics_v0_20260714T125628Z"
)
DEFAULT_SIGNAL_ORTHOGONALITY_BUNDLE = (
    ARCHIVE_ROOT
    / "research/offline_productive_signal_orthogonality_results_interpretation_v0_20260714T213029Z"
)
DEFAULT_FACTOR_EXPOSURE_BUNDLE = (
    ARCHIVE_ROOT / "research/offline_productive_factor_exposure_diagnostics_v0_20260714T220739Z"
)
DEFAULT_PARAMETER_SENSITIVITY_BUNDLE = (
    ARCHIVE_ROOT
    / "research/offline_productive_parameter_sensitivity_diagnostics_v0_20260714T222747Z"
)
DEFAULT_ROLLING_LINEAR_DRIFT_BUNDLE = (
    ARCHIVE_ROOT
    / "research/offline_productive_rolling_linear_drift_diagnostics_v0_20260714T224214Z"
)

DIAGNOSTIC_CLASS_ORDER: tuple[str, ...] = (
    "cost_diagnostics",
    "signal_orthogonality",
    "factor_exposure",
    "parameter_sensitivity",
    "rolling_linear_drift",
)

PAIR_STATUS_PRECEDENCE: dict[str, int] = {
    "BLOCKED": 3,
    "INDICATIVE": 2,
    "OK": 1,
}

SOURCE_STATUS_PRECEDENCE: dict[str, int] = {
    "BLOCK_DRIFT_EXCEEDS_POLICY": 100,
    "RANK_DEFICIENT_BLOCKED": 90,
    "LEAKAGE_BLOCKED": 90,
    "FEATURE_LEAKAGE_BLOCKED": 90,
    "BLOCKED": 85,
    "ROBUSTNESS_FAILED": 70,
    "WARN_DRIFT_DETECTED": 60,
    "FRAGILE_PARAMETER_RESPONSE": 60,
    "INDICATIVE": 55,
    "INSUFFICIENT_DATA": 50,
    "INCONCLUSIVE": 40,
    "DIAGNOSTIC_ONLY": 10,
    "ROBUST_REGION_OBSERVED": 10,
    "PASS_STABLE": 10,
    "OK": 5,
}

BLOCKING_SOURCE_STATUSES: frozenset[str] = frozenset(
    {
        "RANK_DEFICIENT_BLOCKED",
        "BLOCK_DRIFT_EXCEEDS_POLICY",
        "LEAKAGE_BLOCKED",
        "FEATURE_LEAKAGE_BLOCKED",
        "BLOCKED",
        "TARGET_BINDING_MISSING",
        "FEATURE_BINDING_MISMATCH",
        "SOURCE_EVIDENCE_INVALID",
    }
)

WARN_SOURCE_STATUSES: frozenset[str] = frozenset(
    {
        "WARN_DRIFT_DETECTED",
        "FRAGILE_PARAMETER_RESPONSE",
        "ROBUSTNESS_FAILED",
        "INDICATIVE",
        "INSUFFICIENT_DATA",
        "INCONCLUSIVE",
        "INSUFFICIENT_WINDOWS",
        "WINDOW_SAMPLE_INSUFFICIENT",
    }
)

PASS_OR_INFORMATIONAL_SOURCE_STATUSES: frozenset[str] = frozenset(
    {
        "DIAGNOSTIC_ONLY",
        "ROBUST_REGION_OBSERVED",
        "PASS_STABLE",
        "OK",
    }
)


class SupportAggregateStatus(str, Enum):
    BLOCK_SUPPORT_EVIDENCE = "BLOCK_SUPPORT_EVIDENCE"
    WARN_SUPPORT_EVIDENCE = "WARN_SUPPORT_EVIDENCE"
    DIAGNOSTIC_SUPPORT_COMPLETE = "DIAGNOSTIC_SUPPORT_COMPLETE"
    INSUFFICIENT_OR_UNVERIFIED_SOURCE_EVIDENCE = "INSUFFICIENT_OR_UNVERIFIED_SOURCE_EVIDENCE"


class EconomicViabilitySupportStatus(str, Enum):
    BLOCKED_SOURCE_DIAGNOSTICS_PRESENT = "BLOCKED_SOURCE_DIAGNOSTICS_PRESENT"
    WARN_SOURCE_DIAGNOSTICS_PRESENT = "WARN_SOURCE_DIAGNOSTICS_PRESENT"
    DIAGNOSTIC_SUPPORT_REFERENCE_READY = "DIAGNOSTIC_SUPPORT_REFERENCE_READY"
    INSUFFICIENT_SOURCE_BINDING = "INSUFFICIENT_SOURCE_BINDING"


class SupportBundleValidationError(ValueError):
    """Fail-closed validation for productive linear diagnostics support bundle."""


@dataclass(frozen=True)
class SourceBundleSpecV0:
    diagnostic_class: str
    evidence_type: str
    bundle_path: Path
    status_artifact: str
    reason_artifact: str | None = None


@dataclass(frozen=True)
class SourceDiagnosticBindingV0:
    diagnostic_class: str
    evidence_type: str
    bundle_path: str
    manifest_digest: str
    implementation_digest: str | None
    source_status: str
    source_reason_codes: tuple[str, ...]
    manifest_verify_rc: int
    evidence_ref: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "diagnostic_class": self.diagnostic_class,
            "evidence_type": self.evidence_type,
            "bundle_path": self.bundle_path,
            "manifest_digest": self.manifest_digest,
            "implementation_digest": self.implementation_digest,
            "source_status": self.source_status,
            "source_reason_codes": list(self.source_reason_codes),
            "manifest_verify_rc": self.manifest_verify_rc,
            "evidence_ref": self.evidence_ref,
        }


DEFAULT_SOURCE_BUNDLE_SPECS: tuple[SourceBundleSpecV0, ...] = (
    SourceBundleSpecV0(
        diagnostic_class="cost_diagnostics",
        evidence_type="offline_linear_cost_model_diagnostics.v0",
        bundle_path=DEFAULT_COST_DIAGNOSTICS_BUNDLE,
        status_artifact="reason_codes.json",
        reason_artifact="reason_codes.json",
    ),
    SourceBundleSpecV0(
        diagnostic_class="signal_orthogonality",
        evidence_type="offline_productive_signal_orthogonality_results_interpretation.v0",
        bundle_path=DEFAULT_SIGNAL_ORTHOGONALITY_BUNDLE,
        status_artifact="pairwise_interpretation.json",
        reason_artifact="pairwise_interpretation.json",
    ),
    SourceBundleSpecV0(
        diagnostic_class="factor_exposure",
        evidence_type="offline_productive_factor_exposure_diagnostics.v0",
        bundle_path=DEFAULT_FACTOR_EXPOSURE_BUNDLE,
        status_artifact="failure_taxonomy.json",
        reason_artifact="failure_taxonomy.json",
    ),
    SourceBundleSpecV0(
        diagnostic_class="parameter_sensitivity",
        evidence_type="offline_productive_parameter_sensitivity_diagnostics.v0",
        bundle_path=DEFAULT_PARAMETER_SENSITIVITY_BUNDLE,
        status_artifact="final_report.txt",
        reason_artifact="parameter_sensitivity_results.json",
    ),
    SourceBundleSpecV0(
        diagnostic_class="rolling_linear_drift",
        evidence_type="offline_productive_rolling_linear_drift_diagnostics.v0",
        bundle_path=DEFAULT_ROLLING_LINEAR_DRIFT_BUNDLE,
        status_artifact="interpretation.json",
        reason_artifact="interpretation.json",
    ),
)


def _stable_digest(payload: object) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _manifest_file_digest(bundle: Path) -> str:
    manifest_path = bundle / "MANIFEST.sha256"
    if not manifest_path.is_file():
        raise SupportBundleValidationError(f"MISSING_MANIFEST:{bundle}")
    return hashlib.sha256(manifest_path.read_bytes()).hexdigest()


def _implementation_digest_from_owner_inventory(
    bundle: Path,
    *,
    repo_root: Path | None = None,
) -> str | None:
    inventory_path = bundle / "owner_inventory.json"
    if not inventory_path.is_file():
        return None
    inventory = _read_json(inventory_path)
    owner_rel = inventory.get("canonical_owner")
    if not isinstance(owner_rel, str) or not owner_rel:
        return None
    if repo_root is None:
        return _stable_digest({"canonical_owner": owner_rel})
    owner_path = repo_root / owner_rel
    if not owner_path.is_file():
        return _stable_digest({"canonical_owner": owner_rel, "owner_present": False})
    return hashlib.sha256(owner_path.read_bytes()).hexdigest()


def verify_bundle_manifest(path: Path, *, verify_fn: Callable[[Path], tuple[bool, str]]) -> int:
    ok, _ = verify_fn(path)
    return 0 if ok else 1


def _worst_status(statuses: Sequence[str]) -> str:
    if not statuses:
        return "INCONCLUSIVE"
    return max(statuses, key=lambda item: SOURCE_STATUS_PRECEDENCE.get(item, 0))


def _normalize_reason_codes(reasons: Sequence[str]) -> tuple[str, ...]:
    return tuple(sorted({str(item) for item in reasons if str(item)}))


def _extract_cost_status(bundle: Path) -> tuple[str, tuple[str, ...]]:
    reason_path = bundle / "reason_codes.json"
    if reason_path.is_file():
        payload = _read_json(reason_path)
        status = str(payload.get("status", "INCONCLUSIVE"))
        reasons = payload.get("reason_codes", [])
        if isinstance(reasons, list):
            return status, _normalize_reason_codes(reasons)
    evidence_path = bundle / "diagnostic_model_evidence.json"
    if evidence_path.is_file():
        payload = _read_json(evidence_path)
        status = str(payload.get("status", "INCONCLUSIVE"))
        reasons = payload.get("reason_codes", [])
        if isinstance(reasons, list):
            return status, _normalize_reason_codes(reasons)
    raise SupportBundleValidationError("MISSING_COST_STATUS_ARTIFACT")


def _extract_signal_orthogonality_status(bundle: Path) -> tuple[str, tuple[str, ...]]:
    pairwise_path = bundle / "pairwise_interpretation.json"
    if not pairwise_path.is_file():
        raise SupportBundleValidationError("MISSING_SIGNAL_ORTHOGONALITY_STATUS_ARTIFACT")
    records = _read_json(pairwise_path)
    if not isinstance(records, list) or not records:
        raise SupportBundleValidationError("EMPTY_SIGNAL_ORTHOGONALITY_PAIRWISE")
    pair_statuses = [str(item.get("status", "INCONCLUSIVE")) for item in records]
    aggregate_pair_status = max(
        pair_statuses,
        key=lambda item: PAIR_STATUS_PRECEDENCE.get(item, 0),
    )
    reasons: list[str] = []
    for record in records:
        record_reasons = record.get("reason_codes", [])
        if isinstance(record_reasons, list):
            reasons.extend(str(item) for item in record_reasons)
        interpretation_class = record.get("interpretation_class")
        if isinstance(interpretation_class, str) and interpretation_class:
            reasons.append(f"INTERPRETATION_CLASS:{interpretation_class}")
    return aggregate_pair_status, _normalize_reason_codes(reasons)


def _extract_factor_exposure_status(bundle: Path) -> tuple[str, tuple[str, ...]]:
    taxonomy_path = bundle / "failure_taxonomy.json"
    if not taxonomy_path.is_file():
        raise SupportBundleValidationError("MISSING_FACTOR_EXPOSURE_STATUS_ARTIFACT")
    payload = _read_json(taxonomy_path)
    observed_statuses = payload.get("observed_statuses", [])
    observed_reasons = payload.get("observed_reason_codes", [])
    if not isinstance(observed_statuses, list) or not observed_statuses:
        raise SupportBundleValidationError("EMPTY_FACTOR_EXPOSURE_OBSERVED_STATUSES")
    status = _worst_status(str(item) for item in observed_statuses)
    reasons = observed_reasons if isinstance(observed_reasons, list) else []
    return status, _normalize_reason_codes(str(item) for item in reasons)


def _parse_final_report_field(bundle: Path, field: str) -> str | None:
    report_path = bundle / "final_report.txt"
    if not report_path.is_file():
        return None
    prefix = f"{field}="
    for line in report_path.read_text(encoding="utf-8").splitlines():
        if line.startswith(prefix):
            return line[len(prefix) :]
    return None


def _extract_parameter_sensitivity_status(bundle: Path) -> tuple[str, tuple[str, ...]]:
    aggregate_status = _parse_final_report_field(bundle, "AGGREGATE_STATUS")
    if aggregate_status:
        results_path = bundle / "parameter_sensitivity_results.json"
        reasons: list[str] = []
        if results_path.is_file():
            payload = _read_json(results_path)
            if isinstance(payload, dict):
                for parameter_payload in payload.values():
                    if not isinstance(parameter_payload, dict):
                        continue
                    point_results = parameter_payload.get("point_results", [])
                    if isinstance(point_results, list):
                        for point in point_results:
                            point_reasons = point.get("reason_codes", [])
                            if isinstance(point_reasons, list):
                                reasons.extend(str(item) for item in point_reasons)
        return aggregate_status, _normalize_reason_codes(reasons)
    raise SupportBundleValidationError("MISSING_PARAMETER_SENSITIVITY_STATUS_ARTIFACT")


def _extract_rolling_linear_drift_status(bundle: Path) -> tuple[str, tuple[str, ...]]:
    interpretation_path = bundle / "interpretation.json"
    if interpretation_path.is_file():
        payload = _read_json(interpretation_path)
        status = _parse_final_report_field(bundle, "ROLLING_DRIFT_STATUS")
        if not status:
            status = str(payload.get("productive_status", payload.get("status", "INCONCLUSIVE")))
        reasons = payload.get("reason_codes", [])
        if isinstance(reasons, list):
            return status, _normalize_reason_codes(str(item) for item in reasons)
    final_status = _parse_final_report_field(bundle, "ROLLING_DRIFT_STATUS")
    if final_status:
        reason_field = _parse_final_report_field(bundle, "ROLLING_DRIFT_REASON_CODES")
        if reason_field:
            return final_status, _normalize_reason_codes(
                item.strip() for item in reason_field.split(",") if item.strip()
            )
        return final_status, ()
    raise SupportBundleValidationError("MISSING_ROLLING_LINEAR_DRIFT_STATUS_ARTIFACT")


_STATUS_EXTRACTORS: dict[str, Callable[[Path], tuple[str, tuple[str, ...]]]] = {
    "cost_diagnostics": _extract_cost_status,
    "signal_orthogonality": _extract_signal_orthogonality_status,
    "factor_exposure": _extract_factor_exposure_status,
    "parameter_sensitivity": _extract_parameter_sensitivity_status,
    "rolling_linear_drift": _extract_rolling_linear_drift_status,
}


def _classify_source_bucket(status: str) -> str:
    if status in BLOCKING_SOURCE_STATUSES:
        return "blocked"
    if status in WARN_SOURCE_STATUSES:
        return "warn"
    if status in PASS_OR_INFORMATIONAL_SOURCE_STATUSES:
        return "pass_or_informational"
    if status.startswith("BLOCK_"):
        return "blocked"
    if status.startswith("WARN_"):
        return "warn"
    if status.startswith("PASS_"):
        return "pass_or_informational"
    return "warn"


def classify_support_aggregate_status(
    bindings: Sequence[SourceDiagnosticBindingV0],
) -> tuple[str, tuple[str, ...]]:
    if not bindings:
        return (
            SupportAggregateStatus.INSUFFICIENT_OR_UNVERIFIED_SOURCE_EVIDENCE.value,
            ("NO_SOURCE_BINDINGS",),
        )
    if any(item.manifest_verify_rc != 0 for item in bindings):
        return (
            SupportAggregateStatus.INSUFFICIENT_OR_UNVERIFIED_SOURCE_EVIDENCE.value,
            ("SOURCE_MANIFEST_VERIFY_FAILED",),
        )
    if len(bindings) != len(DIAGNOSTIC_CLASS_ORDER):
        return (
            SupportAggregateStatus.INSUFFICIENT_OR_UNVERIFIED_SOURCE_EVIDENCE.value,
            ("INCOMPLETE_DIAGNOSTIC_CLASS_BINDING",),
        )

    reason_codes: list[str] = []
    blocked_count = 0
    warn_count = 0
    pass_count = 0
    for binding in bindings:
        bucket = _classify_source_bucket(binding.source_status)
        if bucket == "blocked":
            blocked_count += 1
            reason_codes.append(
                f"BLOCKED_SOURCE:{binding.diagnostic_class}:{binding.source_status}"
            )
        elif bucket == "warn":
            warn_count += 1
            reason_codes.append(f"WARN_SOURCE:{binding.diagnostic_class}:{binding.source_status}")
        else:
            pass_count += 1

    if blocked_count > 0:
        return (
            SupportAggregateStatus.BLOCK_SUPPORT_EVIDENCE.value,
            tuple(sorted(set(reason_codes))),
        )
    if warn_count > 0:
        return (
            SupportAggregateStatus.WARN_SUPPORT_EVIDENCE.value,
            tuple(sorted(set(reason_codes))),
        )
    return (
        SupportAggregateStatus.DIAGNOSTIC_SUPPORT_COMPLETE.value,
        tuple(sorted(set(reason_codes))) if reason_codes else ("ALL_SOURCE_CLASSES_INFORMATIONAL",),
    )


def classify_economic_viability_support_status(aggregate_status: str) -> str:
    if aggregate_status == SupportAggregateStatus.BLOCK_SUPPORT_EVIDENCE.value:
        return EconomicViabilitySupportStatus.BLOCKED_SOURCE_DIAGNOSTICS_PRESENT.value
    if aggregate_status == SupportAggregateStatus.WARN_SUPPORT_EVIDENCE.value:
        return EconomicViabilitySupportStatus.WARN_SOURCE_DIAGNOSTICS_PRESENT.value
    if aggregate_status == SupportAggregateStatus.DIAGNOSTIC_SUPPORT_COMPLETE.value:
        return EconomicViabilitySupportStatus.DIAGNOSTIC_SUPPORT_REFERENCE_READY.value
    return EconomicViabilitySupportStatus.INSUFFICIENT_SOURCE_BINDING.value


def build_interpretation_v0(
    *,
    bindings: Sequence[SourceDiagnosticBindingV0],
    aggregate_status: str,
    aggregate_reason_codes: Sequence[str],
) -> dict[str, Any]:
    per_class = {
        binding.diagnostic_class: {
            "source_status": binding.source_status,
            "source_reason_codes": list(binding.source_reason_codes),
            "manifest_verify_rc": binding.manifest_verify_rc,
        }
        for binding in bindings
    }
    return {
        "summary": (
            "Manifest-verified productive linear diagnostics aggregated as offline support "
            "evidence only. No economic evaluation, promotion authority, or strategy selection."
        ),
        "aggregate_status": aggregate_status,
        "aggregate_reason_codes": list(aggregate_reason_codes),
        "per_class_status": per_class,
        "blocked_classes": sorted(
            binding.diagnostic_class
            for binding in bindings
            if _classify_source_bucket(binding.source_status) == "blocked"
        ),
        "warn_classes": sorted(
            binding.diagnostic_class
            for binding in bindings
            if _classify_source_bucket(binding.source_status) == "warn"
        ),
        "informational_classes": sorted(
            binding.diagnostic_class
            for binding in bindings
            if _classify_source_bucket(binding.source_status) == "pass_or_informational"
        ),
        "economic_pass_claim_forbidden": True,
        "promotion_pass_claim_forbidden": True,
        "strategy_selection_claim_forbidden": True,
    }


def bind_source_diagnostic_v0(
    spec: SourceBundleSpecV0,
    *,
    verify_fn: Callable[[Path], tuple[bool, str]],
    repo_root: Path | None = None,
) -> SourceDiagnosticBindingV0:
    bundle = spec.bundle_path.expanduser().resolve()
    if not bundle.is_dir():
        raise SupportBundleValidationError(
            f"SOURCE_BUNDLE_MISSING:{spec.diagnostic_class}:{bundle}"
        )
    manifest_verify_rc = verify_bundle_manifest(bundle, verify_fn=verify_fn)
    if manifest_verify_rc != 0:
        raise SupportBundleValidationError(f"SOURCE_MANIFEST_VERIFY_FAILED:{spec.diagnostic_class}")

    extractor = _STATUS_EXTRACTORS[spec.diagnostic_class]
    source_status, source_reason_codes = extractor(bundle)
    return SourceDiagnosticBindingV0(
        diagnostic_class=spec.diagnostic_class,
        evidence_type=spec.evidence_type,
        bundle_path=str(bundle),
        manifest_digest=_manifest_file_digest(bundle),
        implementation_digest=_implementation_digest_from_owner_inventory(
            bundle,
            repo_root=repo_root,
        ),
        source_status=source_status,
        source_reason_codes=source_reason_codes,
        manifest_verify_rc=manifest_verify_rc,
        evidence_ref=spec.status_artifact,
    )


def build_source_status_matrix_v0(
    bindings: Sequence[SourceDiagnosticBindingV0],
) -> dict[str, Any]:
    rows = [binding.to_dict() for binding in bindings]
    blocked = sum(
        1 for item in bindings if _classify_source_bucket(item.source_status) == "blocked"
    )
    warn = sum(1 for item in bindings if _classify_source_bucket(item.source_status) == "warn")
    informational = sum(
        1
        for item in bindings
        if _classify_source_bucket(item.source_status) == "pass_or_informational"
    )
    return {
        "diagnostic_class_count": len(DIAGNOSTIC_CLASS_ORDER),
        "diagnostic_class_present_count": len(bindings),
        "diagnostic_class_blocked_count": blocked,
        "diagnostic_class_warn_count": warn,
        "diagnostic_class_pass_or_informational_count": informational,
        "rows": rows,
    }


def build_authority_boundary_v0() -> dict[str, Any]:
    return {
        "offline_only": True,
        "economic_evaluation_executed": False,
        "economic_validity_pass_created": False,
        "promotion_pass_created": False,
        "strategy_selection_changed": False,
        "parameter_optimization_executed": False,
        "parameter_default_changed": False,
        "cost_default_changed": False,
        "core_trading_semantics_changed": False,
        "economic_pass_authority": False,
        "promotion_pass_authority": False,
        "strategy_selection_authority": False,
        "runtime_effect": RUNTIME_EFFECT,
        "authority_effect": AUTHORITY_EFFECT,
        "support_evidence_only": True,
        "forbidden_claims": [
            "economic_validity_pass",
            "promotion_eligibility",
            "strategy_selection_authority",
            "profitability_proof",
        ],
    }


def build_productive_linear_diagnostics_support_bundle_artifacts_v0(
    *,
    source_specs: Sequence[SourceBundleSpecV0] = DEFAULT_SOURCE_BUNDLE_SPECS,
    verify_fn: Callable[[Path], tuple[bool, str]],
    repo_root: Path | None = None,
) -> dict[str, Any]:
    ordered_specs = sorted(
        source_specs, key=lambda item: DIAGNOSTIC_CLASS_ORDER.index(item.diagnostic_class)
    )
    bindings = [
        bind_source_diagnostic_v0(spec, verify_fn=verify_fn, repo_root=repo_root)
        for spec in ordered_specs
    ]
    aggregate_status, aggregate_reason_codes = classify_support_aggregate_status(bindings)
    economic_viability_support_status = classify_economic_viability_support_status(aggregate_status)
    status_matrix = build_source_status_matrix_v0(bindings)
    interpretation = build_interpretation_v0(
        bindings=bindings,
        aggregate_status=aggregate_status,
        aggregate_reason_codes=aggregate_reason_codes,
    )

    source_evidence_refs = [binding.bundle_path for binding in bindings]
    source_manifest_digests = {
        binding.diagnostic_class: binding.manifest_digest for binding in bindings
    }
    source_implementation_digests = {
        binding.diagnostic_class: binding.implementation_digest for binding in bindings
    }
    source_statuses = {binding.diagnostic_class: binding.source_status for binding in bindings}
    source_reason_codes = {
        binding.diagnostic_class: list(binding.source_reason_codes) for binding in bindings
    }

    config_payload = {
        "schema_version": SCHEMA_VERSION,
        "diagnostic_class_order": list(DIAGNOSTIC_CLASS_ORDER),
        "source_specs": [
            {
                "diagnostic_class": spec.diagnostic_class,
                "evidence_type": spec.evidence_type,
                "bundle_path": str(spec.bundle_path),
                "status_artifact": spec.status_artifact,
            }
            for spec in ordered_specs
        ],
    }
    config_digest = _stable_digest(config_payload)
    input_digest = _stable_digest(
        {
            "source_manifest_digests": source_manifest_digests,
            "source_statuses": source_statuses,
            "source_reason_codes": source_reason_codes,
        }
    )

    aggregate_contract = {
        "schema_version": SCHEMA_VERSION,
        "evidence_type": EVIDENCE_TYPE,
        "aggregate_status": aggregate_status,
        "aggregate_reason_codes": list(aggregate_reason_codes),
        "economic_viability_support_status": economic_viability_support_status,
        "diagnostic_class_count": status_matrix["diagnostic_class_count"],
        "diagnostic_class_present_count": status_matrix["diagnostic_class_present_count"],
        "diagnostic_class_blocked_count": status_matrix["diagnostic_class_blocked_count"],
        "diagnostic_class_warn_count": status_matrix["diagnostic_class_warn_count"],
        "diagnostic_class_pass_or_informational_count": status_matrix[
            "diagnostic_class_pass_or_informational_count"
        ],
    }
    output_digest = _stable_digest(
        {
            "aggregate_contract": aggregate_contract,
            "source_status_matrix": status_matrix,
            "interpretation": interpretation,
            "authority_boundary": build_authority_boundary_v0(),
        }
    )

    ref_by_class = {binding.diagnostic_class: binding.bundle_path for binding in bindings}
    return {
        "schema_version": SCHEMA_VERSION,
        "evidence_type": EVIDENCE_TYPE,
        "diagnostic_evidence_id": DIAGNOSTIC_EVIDENCE_ID,
        "source_evidence_refs": source_evidence_refs,
        "source_manifest_digests": source_manifest_digests,
        "source_implementation_digests": source_implementation_digests,
        "source_statuses": source_statuses,
        "source_reason_codes": source_reason_codes,
        "cost_diagnostics_ref": ref_by_class["cost_diagnostics"],
        "signal_orthogonality_ref": ref_by_class["signal_orthogonality"],
        "factor_exposure_ref": ref_by_class["factor_exposure"],
        "parameter_sensitivity_ref": ref_by_class["parameter_sensitivity"],
        "rolling_linear_drift_ref": ref_by_class["rolling_linear_drift"],
        "diagnostic_class_count": status_matrix["diagnostic_class_count"],
        "diagnostic_class_present_count": status_matrix["diagnostic_class_present_count"],
        "diagnostic_class_blocked_count": status_matrix["diagnostic_class_blocked_count"],
        "diagnostic_class_warn_count": status_matrix["diagnostic_class_warn_count"],
        "diagnostic_class_pass_or_informational_count": status_matrix[
            "diagnostic_class_pass_or_informational_count"
        ],
        "aggregate_status": aggregate_status,
        "aggregate_reason_codes": list(aggregate_reason_codes),
        "economic_viability_support_status": economic_viability_support_status,
        "economic_pass_authority": False,
        "promotion_pass_authority": False,
        "strategy_selection_authority": False,
        "runtime_effect": RUNTIME_EFFECT,
        "authority_effect": AUTHORITY_EFFECT,
        "interpretation": interpretation,
        "config_digest": config_digest,
        "input_digest": input_digest,
        "output_digest": output_digest,
        "source_status_matrix": status_matrix,
        "aggregate_contract": aggregate_contract,
        "authority_boundary": build_authority_boundary_v0(),
    }


_REQUIRED_ARTIFACT_KEYS: tuple[str, ...] = (
    "schema_version",
    "evidence_type",
    "source_evidence_refs",
    "source_manifest_digests",
    "source_implementation_digests",
    "source_statuses",
    "source_reason_codes",
    "cost_diagnostics_ref",
    "signal_orthogonality_ref",
    "factor_exposure_ref",
    "parameter_sensitivity_ref",
    "rolling_linear_drift_ref",
    "diagnostic_class_count",
    "diagnostic_class_present_count",
    "diagnostic_class_blocked_count",
    "diagnostic_class_warn_count",
    "diagnostic_class_pass_or_informational_count",
    "aggregate_status",
    "aggregate_reason_codes",
    "economic_viability_support_status",
    "economic_pass_authority",
    "promotion_pass_authority",
    "strategy_selection_authority",
    "runtime_effect",
    "authority_effect",
    "interpretation",
    "config_digest",
    "input_digest",
    "output_digest",
)


def validate_support_bundle_artifacts_v0(artifacts: Mapping[str, Any]) -> None:
    missing = [key for key in _REQUIRED_ARTIFACT_KEYS if key not in artifacts]
    if missing:
        raise SupportBundleValidationError(f"MISSING_REQUIRED_KEYS:{','.join(missing)}")

    if artifacts["schema_version"] != SCHEMA_VERSION:
        raise SupportBundleValidationError("SCHEMA_VERSION_MISMATCH")
    if artifacts["evidence_type"] != EVIDENCE_TYPE:
        raise SupportBundleValidationError("EVIDENCE_TYPE_MISMATCH")
    if artifacts["economic_pass_authority"] is not False:
        raise SupportBundleValidationError("ECONOMIC_PASS_AUTHORITY_FORBIDDEN")
    if artifacts["promotion_pass_authority"] is not False:
        raise SupportBundleValidationError("PROMOTION_PASS_AUTHORITY_FORBIDDEN")
    if artifacts["strategy_selection_authority"] is not False:
        raise SupportBundleValidationError("STRATEGY_SELECTION_AUTHORITY_FORBIDDEN")
    if artifacts["runtime_effect"] != RUNTIME_EFFECT:
        raise SupportBundleValidationError("RUNTIME_EFFECT_MISMATCH")
    if artifacts["authority_effect"] != AUTHORITY_EFFECT:
        raise SupportBundleValidationError("AUTHORITY_EFFECT_MISMATCH")

    expected_output_digest = _stable_digest(
        {
            "aggregate_contract": artifacts["aggregate_contract"],
            "source_status_matrix": artifacts["source_status_matrix"],
            "interpretation": artifacts["interpretation"],
            "authority_boundary": artifacts["authority_boundary"],
        }
    )
    if artifacts["output_digest"] != expected_output_digest:
        raise SupportBundleValidationError("OUTPUT_DIGEST_MISMATCH")

    aggregate_status = str(artifacts["aggregate_status"])
    allowed_aggregate = {item.value for item in SupportAggregateStatus}
    if aggregate_status not in allowed_aggregate:
        raise SupportBundleValidationError(f"UNKNOWN_AGGREGATE_STATUS:{aggregate_status}")

    rolling_status = artifacts["source_statuses"].get("rolling_linear_drift")
    if (
        rolling_status == "BLOCK_DRIFT_EXCEEDS_POLICY"
        and aggregate_status != SupportAggregateStatus.BLOCK_SUPPORT_EVIDENCE.value
    ):
        raise SupportBundleValidationError("ROLLING_DRIFT_BLOCK_NIVELLED")


__all__ = [
    "ARCHIVE_ROOT",
    "AUTHORITY_EFFECT",
    "DEFAULT_COST_DIAGNOSTICS_BUNDLE",
    "DEFAULT_FACTOR_EXPOSURE_BUNDLE",
    "DEFAULT_PARAMETER_SENSITIVITY_BUNDLE",
    "DEFAULT_ROLLING_LINEAR_DRIFT_BUNDLE",
    "DEFAULT_SIGNAL_ORTHOGONALITY_BUNDLE",
    "DEFAULT_SOURCE_BUNDLE_SPECS",
    "DIAGNOSTIC_CLASS_ORDER",
    "DIAGNOSTIC_EVIDENCE_ID",
    "EVIDENCE_TYPE",
    "EconomicViabilitySupportStatus",
    "RUNTIME_EFFECT",
    "SCHEMA_VERSION",
    "SourceBundleSpecV0",
    "SourceDiagnosticBindingV0",
    "SupportAggregateStatus",
    "SupportBundleValidationError",
    "bind_source_diagnostic_v0",
    "build_authority_boundary_v0",
    "build_interpretation_v0",
    "build_productive_linear_diagnostics_support_bundle_artifacts_v0",
    "build_source_status_matrix_v0",
    "classify_economic_viability_support_status",
    "classify_support_aggregate_status",
    "validate_support_bundle_artifacts_v0",
    "verify_bundle_manifest",
]
