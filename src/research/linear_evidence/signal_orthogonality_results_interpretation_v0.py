"""Offline interpretation consumer for manifest-verified signal orthogonality diagnostics.

Diagnostic-only: consumes productive PR5180 orthogonality evidence; emits
interpretation artifacts without strategy, signal-selection, or runtime authority.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.research.linear_evidence.signal_matrix_productive_contract_v0 import (
    RATIFIED_FLEET_SIGNAL_IDS,
)
from src.research.linear_evidence.signal_orthogonality import (
    REASON_DUPLICATE_SIGNAL,
    REASON_HIGH_PAIRWISE_CORRELATION,
    REASON_INSUFFICIENT_DATA,
    REASON_INSUFFICIENT_OVERLAP,
    REASON_NEAR_DUPLICATE_SIGNAL,
    REASON_RANK_DEFICIENT_FEATURE_MATRIX,
    SCOPE_POLICY_VERSION,
)

INTERPRETATION_SCOPE_VERSION = "offline_productive_signal_orthogonality_results_interpretation.v0"
AUTHORITY_EFFECT = "NONE"
RUNTIME_EFFECT = "NONE"
PROMOTION_EFFECT = "NONE"
ACTIVE_SET_EFFECT = "NONE"

INTERPRETATION_CLASS_DISTINCT_INFORMATION_SUPPORTED = "DISTINCT_INFORMATION_SUPPORTED"
INTERPRETATION_CLASS_PARTIAL_REDUNDANCY_SUPPORTED = "PARTIAL_REDUNDANCY_SUPPORTED"
INTERPRETATION_CLASS_STRONG_REDUNDANCY_SUPPORTED = "STRONG_REDUNDANCY_SUPPORTED"
INTERPRETATION_CLASS_REGIME_DEPENDENT_RELATION = "REGIME_DEPENDENT_RELATION"
INTERPRETATION_CLASS_TIME_UNSTABLE_RELATION = "TIME_UNSTABLE_RELATION"
INTERPRETATION_CLASS_INCONCLUSIVE_INSUFFICIENT_DATA = "INCONCLUSIVE_INSUFFICIENT_DATA"
INTERPRETATION_CLASS_INCONCLUSIVE_NUMERICAL_INSTABILITY = "INCONCLUSIVE_NUMERICAL_INSTABILITY"
INTERPRETATION_CLASS_INCONCLUSIVE_MISSING_DIAGNOSTIC = "INCONCLUSIVE_MISSING_DIAGNOSTIC"

INTERPRETATION_CLASSES: frozenset[str] = frozenset(
    {
        INTERPRETATION_CLASS_DISTINCT_INFORMATION_SUPPORTED,
        INTERPRETATION_CLASS_PARTIAL_REDUNDANCY_SUPPORTED,
        INTERPRETATION_CLASS_STRONG_REDUNDANCY_SUPPORTED,
        INTERPRETATION_CLASS_REGIME_DEPENDENT_RELATION,
        INTERPRETATION_CLASS_TIME_UNSTABLE_RELATION,
        INTERPRETATION_CLASS_INCONCLUSIVE_INSUFFICIENT_DATA,
        INTERPRETATION_CLASS_INCONCLUSIVE_NUMERICAL_INSTABILITY,
        INTERPRETATION_CLASS_INCONCLUSIVE_MISSING_DIAGNOSTIC,
    }
)

ALLOWED_PAIR_STATUSES: frozenset[str] = frozenset({"OK", "BLOCKED", "INDICATIVE"})

REQUIRED_PRODUCTIVE_FILES: tuple[str, ...] = (
    "input_binding.json",
    "signal_summary.json",
    "pairwise_correlations.json",
    "matrix_diagnostics.json",
    "rolling_stability.json",
    "diagnostic_policy.json",
)

KNOWN_MATRIX_REASON_CODES: frozenset[str] = frozenset(
    {
        REASON_RANK_DEFICIENT_FEATURE_MATRIX,
        "HIGH_CONDITION_NUMBER",
        "SIGNAL_REDUNDANCY_REPORTED",
        "INSUFFICIENT_SAMPLE_COUNT",
        "PRODUCTIVE_BINDING_GAP",
    }
)

KNOWN_PAIR_REASON_CODES: frozenset[str] = frozenset(
    {
        REASON_DUPLICATE_SIGNAL,
        REASON_NEAR_DUPLICATE_SIGNAL,
        REASON_HIGH_PAIRWISE_CORRELATION,
        REASON_INSUFFICIENT_OVERLAP,
        REASON_INSUFFICIENT_DATA,
    }
)


class InterpretationValidationError(ValueError):
    """Fail-closed validation error for orthogonality interpretation inputs."""


def _stable_digest(parts: object) -> str:
    payload = json.dumps(parts, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _pair_key(signal_a: str, signal_b: str) -> tuple[str, str]:
    left, right = sorted((signal_a, signal_b))
    return left, right


def _validate_known_signal(name: str) -> None:
    if name not in RATIFIED_FLEET_SIGNAL_IDS:
        raise InterpretationValidationError(f"UNKNOWN_SIGNAL:{name}")


def _validate_known_signal_version(name: str, version: str | None) -> None:
    if version is None:
        return
    if version not in {"v1"}:
        raise InterpretationValidationError(f"UNKNOWN_SIGNAL_VERSION:{name}:{version}")


def _validate_pair_record(record: Mapping[str, Any]) -> None:
    required = (
        "signal_a",
        "signal_b",
        "sample_count",
        "overlap_count",
        "pearson_correlation",
        "absolute_pearson_correlation",
        "status",
        "reason_codes",
    )
    for key in required:
        if key not in record:
            raise InterpretationValidationError(f"MISSING_REQUIRED_FIELD:pairwise.{key}")
    _validate_known_signal(str(record["signal_a"]))
    _validate_known_signal(str(record["signal_b"]))
    status = str(record["status"])
    if status not in ALLOWED_PAIR_STATUSES:
        raise InterpretationValidationError(f"UNKNOWN_PAIR_STATUS:{status}")
    for code in record["reason_codes"]:
        if str(code) not in KNOWN_PAIR_REASON_CODES:
            raise InterpretationValidationError(f"UNKNOWN_PAIR_REASON_CODE:{code}")


def load_productive_orthogonality_evidence(bundle_dir: Path) -> dict[str, Any]:
    """Load required productive orthogonality JSON artifacts from a bundle directory."""
    root = bundle_dir.expanduser().resolve()
    if not root.is_dir():
        raise InterpretationValidationError(f"BUNDLE_DIR_MISSING:{root}")

    loaded: dict[str, Any] = {}
    for name in REQUIRED_PRODUCTIVE_FILES:
        path = root / name
        if not path.is_file():
            raise InterpretationValidationError(f"MISSING_PRODUCTIVE_FILE:{name}")
        loaded[name.removesuffix(".json")] = _read_json(path)

    input_binding = loaded["input_binding"]
    signal_summary = loaded["signal_summary"]
    bound_digest = str(input_binding.get("source_csv_digest", ""))
    summary_digest = str(signal_summary.get("input_digest", ""))
    if not bound_digest or not summary_digest:
        raise InterpretationValidationError("MISSING_REQUIRED_FIELD:input_digest")
    if bound_digest != summary_digest:
        raise InterpretationValidationError("INPUT_DIGEST_MISMATCH")

    pairwise = loaded["pairwise_correlations"]
    if not isinstance(pairwise, list):
        raise InterpretationValidationError("MISSING_REQUIRED_FIELD:pairwise_correlations")
    feature_count = len(input_binding.get("features", []))
    expected_pairs = feature_count * (feature_count - 1) // 2
    if expected_pairs and len(pairwise) != expected_pairs:
        raise InterpretationValidationError("PAIR_COUNT_MISMATCH")
    for record in pairwise:
        _validate_pair_record(record)

    matrix_reasons = loaded["matrix_diagnostics"].get("reason_codes", [])
    for code in matrix_reasons:
        if str(code) not in KNOWN_MATRIX_REASON_CODES:
            raise InterpretationValidationError(f"UNKNOWN_MATRIX_REASON_CODE:{code}")

    return loaded


def _unstable_pair_keys(rolling: Mapping[str, Any]) -> set[tuple[str, str]]:
    keys: set[tuple[str, str]] = set()
    for entry in rolling.get("unstable_pairs", []):
        keys.add(_pair_key(str(entry["signal_a"]), str(entry["signal_b"])))
    return keys


def _has_regime_slices(loaded: Mapping[str, Any]) -> bool:
    return "regime_slices" in loaded or "regime_stability" in loaded


def classify_pairwise_interpretation(
    pair_record: Mapping[str, Any],
    *,
    rolling_stability: Mapping[str, Any],
    matrix_diagnostics: Mapping[str, Any],
    signal_count_after_filter: int,
    diagnostic_policy: Mapping[str, Any],
    regime_slices_present: bool,
) -> dict[str, Any]:
    """Assign exactly one interpretation class to a pairwise record."""
    signal_a = str(pair_record["signal_a"])
    signal_b = str(pair_record["signal_b"])
    reason_codes = [str(code) for code in pair_record["reason_codes"]]
    status = str(pair_record["status"])
    pair = _pair_key(signal_a, signal_b)

    if pair in _unstable_pair_keys(rolling_stability):
        interpretation_class = INTERPRETATION_CLASS_TIME_UNSTABLE_RELATION
        class_reason = "rolling_stability_unstable_pair"
    elif regime_slices_present:
        interpretation_class = INTERPRETATION_CLASS_REGIME_DEPENDENT_RELATION
        class_reason = "regime_slice_output_present"
    elif REASON_DUPLICATE_SIGNAL in reason_codes or REASON_NEAR_DUPLICATE_SIGNAL in reason_codes:
        interpretation_class = INTERPRETATION_CLASS_STRONG_REDUNDANCY_SUPPORTED
        class_reason = "duplicate_or_near_duplicate_reason_code"
    elif REASON_HIGH_PAIRWISE_CORRELATION in reason_codes:
        interpretation_class = INTERPRETATION_CLASS_STRONG_REDUNDANCY_SUPPORTED
        class_reason = "high_pairwise_correlation_reason_code"
    elif status == "BLOCKED" and (
        REASON_INSUFFICIENT_OVERLAP in reason_codes or REASON_INSUFFICIENT_DATA in reason_codes
    ):
        interpretation_class = INTERPRETATION_CLASS_INCONCLUSIVE_INSUFFICIENT_DATA
        class_reason = "blocked_insufficient_overlap_or_data"
    elif status == "INDICATIVE":
        interpretation_class = INTERPRETATION_CLASS_INCONCLUSIVE_INSUFFICIENT_DATA
        class_reason = "indicative_insufficient_sample"
    else:
        rank = int(matrix_diagnostics.get("rank", 0))
        computed = bool(matrix_diagnostics.get("computed", False))
        condition_number = matrix_diagnostics.get("condition_number")
        threshold = float(diagnostic_policy["condition_number_threshold"])
        matrix_reasons = {str(code) for code in matrix_diagnostics.get("reason_codes", [])}
        if computed and rank < signal_count_after_filter:
            interpretation_class = INTERPRETATION_CLASS_INCONCLUSIVE_NUMERICAL_INSTABILITY
            class_reason = "matrix_rank_deficient"
        elif "HIGH_CONDITION_NUMBER" in matrix_reasons or (
            computed and condition_number is not None and float(condition_number) > threshold
        ):
            interpretation_class = INTERPRETATION_CLASS_INCONCLUSIVE_NUMERICAL_INSTABILITY
            class_reason = "high_condition_number"
        elif (
            pair_record.get("spearman_correlation") is not None
            and abs(float(pair_record["spearman_correlation"]))
            >= float(diagnostic_policy["correlation_threshold"])
            and REASON_HIGH_PAIRWISE_CORRELATION not in reason_codes
        ):
            interpretation_class = INTERPRETATION_CLASS_PARTIAL_REDUNDANCY_SUPPORTED
            class_reason = "spearman_exceeds_ratified_correlation_threshold_without_pearson_flag"
        elif status == "OK":
            interpretation_class = INTERPRETATION_CLASS_DISTINCT_INFORMATION_SUPPORTED
            class_reason = "ok_status_without_redundancy_reason_codes"
        else:
            interpretation_class = INTERPRETATION_CLASS_INCONCLUSIVE_MISSING_DIAGNOSTIC
            class_reason = "no_applicable_interpretation_rule"

    if interpretation_class not in INTERPRETATION_CLASSES:
        raise InterpretationValidationError(f"NON_EXCLUSIVE_CLASS:{interpretation_class}")

    return {
        "signal_a": signal_a,
        "signal_b": signal_b,
        "interpretation_class": interpretation_class,
        "class_reason": class_reason,
        "status": status,
        "reason_codes": reason_codes,
        "pearson_correlation": pair_record["pearson_correlation"],
        "absolute_pearson_correlation": pair_record["absolute_pearson_correlation"],
        "spearman_correlation": pair_record.get("spearman_correlation"),
        "overlap_count": pair_record["overlap_count"],
        "sample_count": pair_record["sample_count"],
    }


def _parse_signal_versions_from_knowns(
    knowns: Sequence[str],
) -> dict[str, str]:
    pattern = re.compile(
        rf"({'|'.join(RATIFIED_FLEET_SIGNAL_IDS)})/v(\d+)",
    )
    parsed: dict[str, str] = {}
    for item in knowns:
        for match in pattern.finditer(str(item)):
            parsed[match.group(1)] = f"v{match.group(2)}"
    return parsed


def _resolve_signal_versions(
    input_binding: Mapping[str, Any],
    *,
    signal_matrix_knowns: Sequence[str] | None = None,
) -> dict[str, str]:
    versions: dict[str, str] = {}
    parsed = _parse_signal_versions_from_knowns(signal_matrix_knowns or ())
    for signal in input_binding.get("features", []):
        name = str(signal)
        _validate_known_signal(name)
        version = parsed.get(name)
        _validate_known_signal_version(name, version)
        versions[name] = version if version is not None else "MISSING_DATA"
    return versions


def build_signal_incremental_information_summary(
    *,
    matrix_diagnostics: Mapping[str, Any],
    signal_names: Sequence[str],
) -> dict[str, Any]:
    vif_scores = matrix_diagnostics.get("vif_scores", {})
    coefficients = matrix_diagnostics.get("coefficients", {})
    if not isinstance(vif_scores, dict):
        vif_scores = {}

    per_signal: list[dict[str, Any]] = []
    for name in sorted(signal_names):
        _validate_known_signal(name)
        vif = vif_scores.get(name)
        per_signal.append(
            {
                "signal": name,
                "vif_score": vif,
                "target_coefficient": coefficients.get(name)
                if isinstance(coefficients, dict)
                else "NOT_COMPUTED",
                "incremental_target_information": "NOT_COMPUTED",
                "incremental_target_information_reason": "diagnostic_only_no_target_fit",
            }
        )

    finite_vif = [
        (entry["signal"], float(entry["vif_score"]))
        for entry in per_signal
        if entry["vif_score"] is not None
    ]
    if finite_vif:
        lowest_vif = min(finite_vif, key=lambda item: (item[1], item[0]))
        vif_leader = {
            "signal": lowest_vif[0],
            "vif_score": lowest_vif[1],
            "interpretation_note": (
                "lowest_vif_among_signals_multivariate_collinearity_proxy_not_target_incremental"
            ),
        }
    else:
        vif_leader = "NOT_COMPUTED"

    return {
        "per_signal": per_signal,
        "lowest_vif_signal": vif_leader,
        "partial_correlation_diagnostics": "NOT_COMPUTED",
        "ablation_diagnostics": "NOT_COMPUTED",
        "target_conditioned_incremental_information": "NOT_COMPUTED",
    }


def build_stability_and_limitations(
    *,
    loaded: Mapping[str, Any],
    pairwise_interpretations: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    rolling = loaded["rolling_stability"]
    matrix = loaded["matrix_diagnostics"]
    summary = loaded["signal_summary"]
    limitations: list[str] = []

    if not _has_regime_slices(loaded):
        limitations.append("regime_slices:NOT_APPLICABLE_WITH_REASON:not_in_productive_bundle")

    if (
        build_signal_incremental_information_summary(
            matrix_diagnostics=matrix,
            signal_names=loaded["input_binding"]["features"],
        )["partial_correlation_diagnostics"]
        == "NOT_COMPUTED"
    ):
        limitations.append("partial_correlation:NOT_COMPUTED")

    if (
        build_signal_incremental_information_summary(
            matrix_diagnostics=matrix,
            signal_names=loaded["input_binding"]["features"],
        )["target_conditioned_incremental_information"]
        == "NOT_COMPUTED"
    ):
        limitations.append("target_conditioned_incremental:NOT_COMPUTED")

    spearman_pearson_divergence_pairs = [
        {
            "signal_a": item["signal_a"],
            "signal_b": item["signal_b"],
            "pearson_correlation": item["pearson_correlation"],
            "spearman_correlation": item["spearman_correlation"],
            "absolute_pearson_correlation": item["absolute_pearson_correlation"],
        }
        for item in pairwise_interpretations
        if item.get("spearman_correlation") is not None
        and abs(float(item["spearman_correlation"])) > abs(float(item["pearson_correlation"])) + 0.1
    ]
    if spearman_pearson_divergence_pairs:
        limitations.append("spearman_pearson_divergence_observed_without_linear_redundancy_flag")

    sample_count = int(summary.get("pair_count", 0))
    if loaded["pairwise_correlations"]:
        sample_count = int(loaded["pairwise_correlations"][0].get("sample_count", 0))
    if sample_count < int(loaded["diagnostic_policy"]["min_samples"]):
        limitations.append("sample_count_below_policy_minimum")

    return {
        "rolling_stability_status": rolling.get("status", "MISSING_DATA"),
        "time_slice_count": rolling.get("time_slice_count", 0),
        "stable_pair_count": len(rolling.get("stable_pairs", [])),
        "unstable_pair_count": len(rolling.get("unstable_pairs", [])),
        "regime_stability": "NOT_APPLICABLE_WITH_REASON:not_in_productive_bundle",
        "numerical_stability_status": (
            "STABLE"
            if matrix.get("computed")
            and int(matrix.get("rank", 0)) >= int(summary.get("signal_count_after_filter", 0))
            and float(matrix.get("condition_number", float("inf")))
            <= float(loaded["diagnostic_policy"]["condition_number_threshold"])
            else "LIMITED"
        ),
        "sample_sufficiency_status": (
            "SUFFICIENT"
            if sample_count >= int(loaded["diagnostic_policy"]["min_samples"])
            else "INSUFFICIENT"
        ),
        "limitations": limitations,
        "spearman_pearson_divergence_pairs": spearman_pearson_divergence_pairs,
    }


def build_interpretation_policy_resolution(
    diagnostic_policy: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "diagnostic_policy_version": diagnostic_policy.get("version", SCOPE_POLICY_VERSION),
        "interpretation_scope_version": INTERPRETATION_SCOPE_VERSION,
        "threshold_policy_status": "NOT_RATIFIED",
        "threshold_policy_note": (
            "Ratified diagnostic thresholds exist for computation; no separate "
            "interpretation-class threshold ratification beyond diagnostic reason codes."
        ),
        "numeric_results_reported_without_binary_policy_claim": True,
        "ratified_diagnostic_thresholds_consumed": {
            "correlation_threshold": diagnostic_policy["correlation_threshold"],
            "condition_number_threshold": diagnostic_policy["condition_number_threshold"],
            "min_samples": diagnostic_policy["min_samples"],
            "rolling_stability_instability_threshold": diagnostic_policy[
                "rolling_stability_instability_threshold"
            ],
        },
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
    }


def build_authority_boundary_assertions() -> dict[str, Any]:
    return {
        "offline_only": True,
        "diagnostic_only": True,
        "no_strategy_selection_change": True,
        "no_signal_selection_change": True,
        "no_automatic_signal_removal": True,
        "no_automatic_signal_replacement": True,
        "no_automatic_signal_downweighting": True,
        "no_active_set_replacement_authority": True,
        "no_economic_pass_claim": True,
        "new_orthogonality_fit_executed": False,
        "new_market_data_evaluation_executed": False,
        "economic_evaluation_executed": False,
        "strategy_selection_changed": False,
        "signal_selection_changed": False,
        "signal_removal_executed": False,
        "signal_replacement_executed": False,
        "signal_weighting_changed": False,
        "parameters_changed": False,
        "economic_policy_changed": False,
        "economic_pass_claim_created": False,
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
        "promotion_effect": PROMOTION_EFFECT,
        "active_set_effect": ACTIVE_SET_EFFECT,
    }


@dataclass(frozen=True)
class ProductiveEvidenceInventory:
    bundle_dir: Path
    source_bundle: str
    output_digest: str
    input_digest: str
    signal_names: tuple[str, ...]
    signal_versions: dict[str, str]
    sample_count: int
    feature_count: int
    time_range: str
    dataset_binding: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "bundle_dir": str(self.bundle_dir),
            "source_bundle": self.source_bundle,
            "output_digest": self.output_digest,
            "input_digest": self.input_digest,
            "signal_names": list(self.signal_names),
            "signal_versions": dict(self.signal_versions),
            "sample_count": self.sample_count,
            "feature_count": self.feature_count,
            "time_range": self.time_range,
            "dataset_binding": self.dataset_binding,
        }


def build_productive_evidence_inventory(
    bundle_dir: Path,
    loaded: Mapping[str, Any],
    *,
    signal_matrix_knowns: Sequence[str] | None = None,
    time_range: str = "MISSING_DATA",
    dataset_binding: str = "MISSING_DATA",
) -> ProductiveEvidenceInventory:
    input_binding = loaded["input_binding"]
    summary = loaded["signal_summary"]
    signal_names = tuple(str(name) for name in input_binding["features"])
    for name in signal_names:
        _validate_known_signal(name)
    sample_count = 0
    if loaded["pairwise_correlations"]:
        sample_count = int(loaded["pairwise_correlations"][0]["sample_count"])
    return ProductiveEvidenceInventory(
        bundle_dir=bundle_dir,
        source_bundle=str(input_binding.get("source_bundle", "MISSING_DATA")),
        output_digest=str(summary.get("output_digest", "MISSING_DATA")),
        input_digest=str(summary.get("input_digest", "MISSING_DATA")),
        signal_names=signal_names,
        signal_versions=_resolve_signal_versions(
            input_binding,
            signal_matrix_knowns=signal_matrix_knowns,
        ),
        sample_count=sample_count,
        feature_count=int(summary.get("signal_count_after_filter", len(signal_names))),
        time_range=time_range,
        dataset_binding=dataset_binding,
    )


def build_orthogonality_interpretation_artifacts_v0(
    bundle_dir: Path,
    *,
    signal_matrix_knowns: Sequence[str] | None = None,
    time_range: str = "MISSING_DATA",
    dataset_binding: str = "MISSING_DATA",
) -> dict[str, Any]:
    """Build deterministic interpretation artifacts from productive orthogonality evidence."""
    loaded = load_productive_orthogonality_evidence(bundle_dir)
    diagnostic_policy = loaded["diagnostic_policy"]
    signal_count = int(loaded["signal_summary"]["signal_count_after_filter"])
    regime_present = _has_regime_slices(loaded)

    pairwise_interpretations = [
        classify_pairwise_interpretation(
            record,
            rolling_stability=loaded["rolling_stability"],
            matrix_diagnostics=loaded["matrix_diagnostics"],
            signal_count_after_filter=signal_count,
            diagnostic_policy=diagnostic_policy,
            regime_slices_present=regime_present,
        )
        for record in loaded["pairwise_correlations"]
    ]

    class_counts = {name: 0 for name in sorted(INTERPRETATION_CLASSES)}
    for item in pairwise_interpretations:
        class_counts[item["interpretation_class"]] += 1

    inventory = build_productive_evidence_inventory(
        bundle_dir,
        loaded,
        signal_matrix_knowns=signal_matrix_knowns,
        time_range=time_range,
        dataset_binding=dataset_binding,
    )

    incremental_summary = build_signal_incremental_information_summary(
        matrix_diagnostics=loaded["matrix_diagnostics"],
        signal_names=inventory.signal_names,
    )
    stability = build_stability_and_limitations(
        loaded=loaded,
        pairwise_interpretations=pairwise_interpretations,
    )

    sorted_by_redundancy = sorted(
        pairwise_interpretations,
        key=lambda item: (
            -float(item["absolute_pearson_correlation"]),
            item["signal_a"],
            item["signal_b"],
        ),
    )
    strongest_redundancy = sorted_by_redundancy[0] if sorted_by_redundancy else "MISSING_DATA"

    primary_interpretation = {
        "q1_strongest_observed_redundancy": strongest_redundancy,
        "q2_strongest_supported_incremental_information": incremental_summary["lowest_vif_signal"],
        "q3_full_interchangeability_proven": False,
        "q3_interchangeability_status": "UNKNOWN_NOT_PROVEN",
        "q4_time_and_regime_stability": {
            "time_slices_stable": stability["unstable_pair_count"] == 0,
            "regime_slices": "NOT_APPLICABLE_WITH_REASON:not_in_productive_bundle",
        },
        "q5_key_limitations": stability["limitations"],
        "q6_signal_removal_replacement_downweighting_allowed": False,
        "q7_next_offline_diagnostic_recommendation": (
            "Compute rank-monotonic redundancy diagnostics (Spearman-conditioned partial "
            "overlap) for pairs with spearman_pearson_divergence; add target-conditioned "
            "incremental information only if an admissible offline target binding exists."
        ),
    }

    output_digest = _stable_digest(
        {
            "pairwise_interpretations": pairwise_interpretations,
            "incremental_summary": incremental_summary,
            "stability": stability,
            "inventory": inventory.to_dict(),
            "primary_interpretation": primary_interpretation,
        }
    )

    return {
        "interpretation_scope_version": INTERPRETATION_SCOPE_VERSION,
        "productive_evidence_inventory": inventory.to_dict(),
        "interpretation_policy_resolution": build_interpretation_policy_resolution(
            diagnostic_policy
        ),
        "pairwise_interpretation": pairwise_interpretations,
        "signal_incremental_information_summary": incremental_summary,
        "stability_and_limitations": stability,
        "authority_boundary_assertions": build_authority_boundary_assertions(),
        "class_counts": class_counts,
        "primary_interpretation": primary_interpretation,
        "output_digest": output_digest,
        "source_output_digest": inventory.output_digest,
        "source_input_digest": inventory.input_digest,
    }


__all__ = [
    "INTERPRETATION_CLASSES",
    "INTERPRETATION_SCOPE_VERSION",
    "InterpretationValidationError",
    "build_authority_boundary_assertions",
    "build_interpretation_policy_resolution",
    "build_orthogonality_interpretation_artifacts_v0",
    "build_productive_evidence_inventory",
    "build_signal_incremental_information_summary",
    "build_stability_and_limitations",
    "classify_pairwise_interpretation",
    "load_productive_orthogonality_evidence",
]
