"""Terminal insufficient-sample registration and distinct futures research scope ratification.

Registers cross_sectional_futures_lead_lag_information_diffusion/v0 as terminal for the exact
unchanged binding after offline economic evaluation with zero trades and
INSUFFICIENT_TRADE_SAMPLE, blocks same-binding retry, and ratifies
cross_sectional_futures_pairwise_lead_lag_spillover/v1 as the materially distinct successor
scope. Offline-only; no economic evaluation execution in this slice.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

PACKAGE_MARKER = (
    "CROSS_SECTIONAL_FUTURES_LEAD_LAG_INFORMATION_DIFFUSION_V0_TERMINAL_INSUFFICIENT_SAMPLE_AND_"
    "DISTINCT_FUTURES_RESEARCH_SCOPE_RATIFICATION_V0=true"
)
SCHEMA_VERSION = (
    "cross_sectional_futures_lead_lag_information_diffusion_v0_terminal_insufficient_sample_and_"
    "distinct_futures_research_scope_ratification.v0"
)
REGISTRATION_ID = (
    "cross_sectional_futures_lead_lag_information_diffusion_v0_terminal_insufficient_sample_and_"
    "distinct_futures_research_scope_ratification_v0"
)
REGISTRATION_VERSION = "v0"
SCOPE_CLASSIFICATION = (
    "BOUNDED_FUTURES_ONLY_TERMINAL_INSUFFICIENT_SAMPLE_REGISTRATION_AND_"
    "DISTINCT_RESEARCH_SCOPE_RATIFICATION_V0"
)
OPERATOR_GO_TOKEN = (
    "GO_CROSS_SECTIONAL_FUTURES_LEAD_LAG_INFORMATION_DIFFUSION_V0_TERMINAL_INSUFFICIENT_SAMPLE_"
    "AND_DISTINCT_FUTURES_RESEARCH_SCOPE_RATIFICATION_V0"
)
OPERATOR_DECISION = "NEW_VERSIONED_RESEARCH_SCOPE"
CONFIG_REL_PATH = (
    "config/research/"
    "cross_sectional_futures_lead_lag_information_diffusion_v0_terminal_insufficient_sample_and_"
    "distinct_futures_research_scope_ratification_v0.json"
)
GOVERNANCE_REL_PATH = (
    "docs/governance/"
    "CROSS_SECTIONAL_FUTURES_LEAD_LAG_INFORMATION_DIFFUSION_V0_TERMINAL_INSUFFICIENT_SAMPLE_AND_"
    "DISTINCT_FUTURES_RESEARCH_SCOPE_RATIFICATION_V0.md"
)
VERSIONED_BINDING_CONFIG_REL_PATH = (
    "config/research/"
    "cross_sectional_futures_lead_lag_information_diffusion_v0_versioned_hypothesis_binding_v0.json"
)
PAIRWISE_SCOPE_RATIFICATION_CONFIG_REL_PATH = (
    "config/research/"
    "cross_sectional_futures_pairwise_lead_lag_spillover_v1_research_scope_ratification_v0.json"
)

STRATEGY_ID = "cross_sectional_futures_lead_lag_information_diffusion"
STRATEGY_VERSION = "v0"
RESEARCH_SCOPE = "cross_sectional_futures_lead_lag_information_diffusion/v0"
STRATEGY_BINDING = RESEARCH_SCOPE
HYPOTHESIS_ID = "CROSS_SECTIONAL_FUTURES_LEAD_LAG_INFORMATION_DIFFUSION_NON_BITCOIN_PERPETUALS_V0"
SCORE_FAMILY_POLICY = "panel_median_benchmark_lagged_return_diffusion_v0"

DURABLE_ARCHIVE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)
CANONICAL_EVALUATION_DIR = (
    DURABLE_ARCHIVE_ROOT
    / "research/cross_sectional_futures_lead_lag_information_diffusion_v0_offline_economic_"
    "evaluation_execution_v0_20260715T030542Z"
)
PR5197_CLOSEOUT_DIR = (
    DURABLE_ARCHIVE_ROOT
    / "research/pr5197_merge_closeout_cross_sectional_futures_lead_lag_information_diffusion_v0_"
    "offline_economic_evaluation_execution_authorization_ratification_repair_v0_20260715T030215Z"
)
OI_TERMINAL_RATIFICATION_DIR = (
    DURABLE_ARCHIVE_ROOT
    / "research/cross_sectional_open_interest_zscore_reversion_v0_terminal_insufficient_sample_"
    "operator_ratification_and_lead_lag_scope_ratification_v0_20260715T021447Z"
)

CANONICAL_EVALUATION_TIMESTAMP = "20260715T030542Z"
PRE_MERGE_ORIGIN_MAIN = "a84e93dcfc6e4f60542d89bf5a3efdf33e7a6633"

BINDING_DIGEST = "9e9ab5676d8859d819dad1aed1eaa78163529682492fcc333ead001841e414c1"
IMPLEMENTATION_DIGEST = "612b431acc3833ed364b66de58b06ce15268edb30e1c5d82db50258cedd6c949"
CONFIG_DIGEST = "f939aefbaf2a88bfc77b6c47eac86e8eeabcbfa0f0ca9ef7a804ecdf87464089"
DATA_DIGEST = "68919bd52faee69a14140e5b50607437997f09bfec1bcb4a6ae98b69227f4c78"
MATERIAL_DIFFERENCE_DIGEST = "96de4479dca452f40ad4292370801e3386169cf846b9f7b5320884c24a9163df"

PRIMARY_CAUSE_CLASS = "CANONICAL_POLICY_BLOCKED"
SECONDARY_CAUSE_CLASS = "INSUFFICIENT_DATA"
TERMINAL_STATUS = "TERMINAL_INSUFFICIENT_SAMPLE"
TERMINAL_FAILURE_CLASS = "INSUFFICIENT_TRADE_SAMPLE"
TERMINAL_VERDICT = "FAIL_ECONOMIC_VALIDITY_OFFLINE_INSUFFICIENT_TRADE_SAMPLE"
BASELINE_VERDICT = "FAIL"
NET_RETURN = 0.0
TRADE_COUNT = 0
POLICY_MINIMUM_TRADE_COUNT = 50
SAMPLE_SUFFICIENCY_STATUS = "INSUFFICIENT"

DIRECTIONAL_CANDIDATE_COUNT = 30
DIRECTIONAL_CONFIRMED_COUNT = 0
TRADES_OPENED_COUNT = 0
TOP_BLOCK_REASON_OBSERVE_ONLY_COUNT = 30
INSUFFICIENT_ELIGIBLE_MEMBERS_EPOCH_COUNT = 9
LEGACY_REFERENCE_TRADE_COUNT = 4

SELECTED_DISTINCT_SCOPE = "cross_sectional_futures_pairwise_lead_lag_spillover/v1"
SELECTED_DISTINCT_STRATEGY_ID = "cross_sectional_futures_pairwise_lead_lag_spillover"
SELECTED_DISTINCT_STRATEGY_VERSION = "v1"
SELECTED_DISTINCT_HYPOTHESIS_ID = (
    "CROSS_SECTIONAL_FUTURES_PAIRWISE_LEAD_LAG_SPILLOVER_NON_BITCOIN_PERPETUALS_V1"
)
SELECTED_DISTINCT_HYPOTHESIS_FAMILY = "pairwise_information_spillover_graph"
SELECTED_DISTINCT_SCORE_FAMILY_POLICY = "pairwise_leader_follower_spillover_v1"
SELECTED_DISTINCT_MATERIAL_DIFFERENCE_PRIMARY = (
    "dyadic_spillover_graph_vs_panel_median_lagged_return_diffusion"
)
SELECTED_DISTINCT_DATA_READINESS = "PASS_ON_EXISTING_PIT_OHLCV_PANEL"
SELECTED_DISTINCT_MATERIAL_DIFFERENCE_DIGEST = (
    "pending_future_binding_ratification_no_existing_binding_digest"
)

AUTHORITY_EFFECT = "NONE"
RUNTIME_EFFECT = "NONE"
NEXT_CANONICAL_STEP = (
    "GO_CROSS_SECTIONAL_FUTURES_PAIRWISE_LEAD_LAG_SPILLOVER_V1_CONTRACT_AND_"
    "DATASET_FEASIBILITY_READ_ONLY_V0"
)
NEXT_GO_TOKEN = NEXT_CANONICAL_STEP

REQUIRED_CANONICAL_EVIDENCE_FILES = (
    "final_report.txt",
    "EXECUTION_RESULT.json",
    "FULL_EVALUATION_RESULT.json",
    "sample_sufficiency.json",
    "binding_and_digest_inventory.json",
)


class RegistrationVerdict(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"


@dataclass(frozen=True)
class EvidenceBundleValidation:
    bundle_path: Path
    manifest_verify_rc: int
    manifest_digest: str


def serialize_canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def compute_registration_digest(payload: Mapping[str, Any]) -> str:
    body = {k: v for k, v in payload.items() if k != "registration_digest"}
    return hashlib.sha256(serialize_canonical_json(body).encode("utf-8")).hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"not_object:{path}")
    return data


def verify_manifest_sha256(bundle_dir: Path) -> int:
    manifest_path = bundle_dir / "MANIFEST.sha256"
    if not manifest_path.is_file():
        return 1
    result = subprocess.run(
        ["shasum", "-a", "256", "-c", "MANIFEST.sha256"],
        cwd=bundle_dir,
        capture_output=True,
        text=True,
        check=False,
    )
    return 0 if result.returncode == 0 else 1


def manifest_file_digest(bundle_dir: Path) -> str:
    manifest_path = bundle_dir / "MANIFEST.sha256"
    return hashlib.sha256(manifest_path.read_bytes()).hexdigest()


def validate_evidence_bundle(bundle_dir: Path) -> EvidenceBundleValidation:
    if not bundle_dir.is_dir():
        raise ValueError(f"missing_bundle_dir:{bundle_dir}")
    manifest_verify_rc = verify_manifest_sha256(bundle_dir)
    if manifest_verify_rc != 0:
        raise ValueError(f"manifest_verify_failed:{bundle_dir}")
    for name in REQUIRED_CANONICAL_EVIDENCE_FILES:
        if not (bundle_dir / name).is_file():
            raise ValueError(f"missing_required_evidence:{bundle_dir / name}")
    return EvidenceBundleValidation(
        bundle_path=bundle_dir,
        manifest_verify_rc=manifest_verify_rc,
        manifest_digest=manifest_file_digest(bundle_dir),
    )


def validate_registration_preconditions(
    *,
    canonical_dir: Path = CANONICAL_EVALUATION_DIR,
    pr5197_closeout_dir: Path = PR5197_CLOSEOUT_DIR,
    oi_terminal_ratification_dir: Path = OI_TERMINAL_RATIFICATION_DIR,
) -> EvidenceBundleValidation:
    for bundle_dir in (pr5197_closeout_dir, oi_terminal_ratification_dir):
        if verify_manifest_sha256(bundle_dir) != 0:
            raise ValueError(f"manifest_verify_failed:{bundle_dir}")
    canonical = validate_evidence_bundle(canonical_dir)
    binding_inventory = _load_json(canonical_dir / "binding_and_digest_inventory.json")
    if binding_inventory.get("binding_digest") != BINDING_DIGEST:
        raise ValueError("binding_digest_mismatch")
    if binding_inventory.get("implementation_digest") != IMPLEMENTATION_DIGEST:
        raise ValueError("implementation_digest_mismatch")
    sample = _load_json(canonical_dir / "sample_sufficiency.json")
    if int(sample.get("trade_count", -1)) != TRADE_COUNT:
        raise ValueError("trade_count_mismatch")
    if sample.get("sample_sufficiency_status") != SAMPLE_SUFFICIENCY_STATUS:
        raise ValueError("sample_sufficiency_status_mismatch")
    if sample.get("primary_failure_class") != PRIMARY_CAUSE_CLASS:
        raise ValueError("primary_failure_class_mismatch")
    execution = _load_json(canonical_dir / "EXECUTION_RESULT.json")
    evaluation = execution.get("evaluation", {})
    if int(evaluation.get("trade_count", -1)) != TRADE_COUNT:
        raise ValueError("performance_trade_count_mismatch")
    funnel = evaluation.get("canonical_decision_funnel", {})
    if int(funnel.get("directional_candidate_count", -1)) != DIRECTIONAL_CANDIDATE_COUNT:
        raise ValueError("directional_candidate_count_mismatch")
    if int(funnel.get("trades_opened_count", -1)) != TRADES_OPENED_COUNT:
        raise ValueError("trades_opened_count_mismatch")
    return canonical


def is_exact_binding_retry_blocked(
    *,
    research_scope: str,
    binding_digest: str,
    implementation_digest: str,
) -> bool:
    if research_scope != RESEARCH_SCOPE:
        return False
    return binding_digest == BINDING_DIGEST and implementation_digest == IMPLEMENTATION_DIGEST


def is_materially_distinct_scope_admissible(selected_scope: str) -> bool:
    if selected_scope == RESEARCH_SCOPE:
        return False
    return selected_scope == SELECTED_DISTINCT_SCOPE


def _metrics_from_canonical(canonical_dir: Path) -> dict[str, Any]:
    execution = _load_json(canonical_dir / "EXECUTION_RESULT.json")
    evaluation = execution.get("evaluation", {})
    sample = _load_json(canonical_dir / "sample_sufficiency.json")
    funnel = evaluation.get("canonical_decision_funnel", {})
    return {
        "net_return": evaluation.get("net_return", 0.0),
        "net_expectancy": evaluation.get("net_expectancy"),
        "profit_factor": evaluation.get("profit_factor", 0.0),
        "sharpe": evaluation.get("sharpe", 0.0),
        "max_drawdown": evaluation.get("max_drawdown", 0.0),
        "trade_count": evaluation.get("trade_count", 0),
        "sample_sufficiency_status": sample["sample_sufficiency_status"],
        "policy_minimum_trade_count": POLICY_MINIMUM_TRADE_COUNT,
        "directional_candidate_count": funnel.get("directional_candidate_count", 0),
        "directional_confirmed_count": funnel.get("directional_confirmed_count", 0),
        "trades_opened_count": funnel.get("trades_opened_count", 0),
        "top_block_reason_observe_only_count": TOP_BLOCK_REASON_OBSERVE_ONLY_COUNT,
        "insufficient_eligible_members_epoch_count": INSUFFICIENT_ELIGIBLE_MEMBERS_EPOCH_COUNT,
        "legacy_reference_trade_count": LEGACY_REFERENCE_TRADE_COUNT,
        "walk_forward_status": "EXECUTED_ZERO_TRADES",
        "monte_carlo_status": "EXECUTED_ZERO_TRADES",
        "stress_status": "EXECUTED_ZERO_TRADES",
    }


def build_distinct_scope_candidate_inventory() -> dict[str, Any]:
    return {
        "schema_version": "distinct_scope_candidate_inventory.v0",
        "candidates": [
            {
                "research_scope": RESEARCH_SCOPE,
                "status": "TERMINAL_INSUFFICIENT_SAMPLE_SOURCE_NOT_CANDIDATE",
                "rejected": True,
                "rejection_reason": "SOURCE_BINDING_TERMINAL_INSUFFICIENT_SAMPLE",
            },
            {
                "research_scope": RESEARCH_SCOPE,
                "candidate_type": "LAG_WINDOW_VARIANT",
                "status": "REJECTED",
                "rejected": True,
                "rejection_reason": "LAG_WINDOW_VARIANT_RETRY_FORBIDDEN",
            },
            {
                "research_scope": RESEARCH_SCOPE,
                "candidate_type": "THRESHOLD_RESCUE",
                "status": "REJECTED",
                "rejected": True,
                "rejection_reason": "THRESHOLD_OR_POLICY_RESCUE_FORBIDDEN",
            },
            {
                "research_scope": SELECTED_DISTINCT_SCOPE,
                "strategy_id": SELECTED_DISTINCT_STRATEGY_ID,
                "strategy_version": SELECTED_DISTINCT_STRATEGY_VERSION,
                "hypothesis_id": SELECTED_DISTINCT_HYPOTHESIS_ID,
                "hypothesis_family": SELECTED_DISTINCT_HYPOTHESIS_FAMILY,
                "status": "SELECTED",
                "rejected": False,
                "material_difference_proven": True,
                "greenfield_hypothesis": True,
            },
        ],
    }


def build_material_difference_matrix() -> dict[str, Any]:
    return {
        "schema_version": "material_difference_matrix.v0",
        "baseline_scope": RESEARCH_SCOPE,
        "selected_scope": SELECTED_DISTINCT_SCOPE,
        "material_difference_proven": True,
        "material_difference_primary": SELECTED_DISTINCT_MATERIAL_DIFFERENCE_PRIMARY,
        "material_difference_basis": "DISTINCT_HYPOTHESIS_FAMILY_AND_DISTINCT_SCORE_GRAPH_MECHANISM",
        "rows": [
            {
                "axis": "signal_mechanism",
                "baseline": "Panel-median-benchmark lagged return diffusion score",
                "selected": "Pairwise dyadic information spillover graph leader-follower score",
                "material_difference": True,
            },
            {
                "axis": "hypothesis_family",
                "baseline": "panel_median_lagged_return_diffusion",
                "selected": SELECTED_DISTINCT_HYPOTHESIS_FAMILY,
                "material_difference": True,
            },
            {
                "axis": "score_family_policy",
                "baseline": SCORE_FAMILY_POLICY,
                "selected": SELECTED_DISTINCT_SCORE_FAMILY_POLICY,
                "material_difference": True,
            },
            {
                "axis": "dataset_identity",
                "baseline": "pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_v1",
                "selected": "PASS_ON_EXISTING_PIT_OHLCV_PANEL",
                "material_difference": False,
                "note": "Same admissible PIT OHLCV panel; mechanism change is primary",
            },
            {
                "axis": "temporal_structure",
                "baseline": "Multi-lag log-return diffusion vs panel median",
                "selected": "Dyadic pairwise spillover graph over instrument pairs",
                "material_difference": True,
            },
            {
                "axis": "expected_trade_frequency",
                "baseline": "Sparse (observed trade_count=0 under unchanged binding)",
                "selected": "Distinct pairwise graph rebalance surface (not evaluated)",
                "material_difference": True,
            },
            {
                "axis": "duplicate_near_duplicate_risk",
                "baseline": "N/A",
                "selected": "LOW",
                "material_difference": True,
            },
        ],
    }


def build_exact_binding_retry_guard_report() -> dict[str, Any]:
    return {
        "schema_version": "exact_binding_retry_guard_report.v0",
        "research_scope": RESEARCH_SCOPE,
        "binding_digest": BINDING_DIGEST,
        "implementation_digest": IMPLEMENTATION_DIGEST,
        "unchanged_retry_blocked": True,
        "same_binding_retry_allowed": False,
        "policy_rescue_allowed": False,
        "negative_evidence_preserved": True,
        "exact_binding_retry_blocked": is_exact_binding_retry_blocked(
            research_scope=RESEARCH_SCOPE,
            binding_digest=BINDING_DIGEST,
            implementation_digest=IMPLEMENTATION_DIGEST,
        ),
        "distinct_scope_admissible": is_materially_distinct_scope_admissible(
            SELECTED_DISTINCT_SCOPE
        ),
        "blocked_retry_axes": [
            "UNCHANGED_BINDING_RETRY",
            "SAME_BINDING_RETRY",
            "LAG_WINDOW_VARIANT",
            "THRESHOLD_LOWERING",
            "POLICY_RESCUE",
            "POST_RESULT_PARAMETER_CHANGE",
            "LEAD_LAG_V0_PANEL_MEDIAN_RETRY",
        ],
    }


def build_retry_non_equivalence_proof() -> dict[str, Any]:
    return {
        "schema_version": "retry_non_equivalence_proof.v0",
        "baseline_scope": RESEARCH_SCOPE,
        "selected_scope": SELECTED_DISTINCT_SCOPE,
        "binding_digest_unchanged_retry_forbidden": True,
        "implementation_digest_unchanged_retry_forbidden": True,
        "hypothesis_family_differs": True,
        "score_family_differs": True,
        "score_formula_differs": True,
        "retry_non_equivalence_proven": True,
        "greenfield_hypothesis": True,
    }


def build_zero_trade_causal_classification() -> dict[str, Any]:
    return {
        "schema_version": "zero_trade_causal_classification.v0",
        "trade_count": TRADE_COUNT,
        "primary_causal_class": PRIMARY_CAUSE_CLASS,
        "secondary_causal_class": SECONDARY_CAUSE_CLASS,
        "implementation_or_binding_defect_primary": False,
        "no_canonical_market_opportunity_primary": False,
        "directional_candidate_count": DIRECTIONAL_CANDIDATE_COUNT,
        "directional_confirmed_count": DIRECTIONAL_CONFIRMED_COUNT,
        "trades_opened_count": TRADES_OPENED_COUNT,
        "top_block_reason_observe_only_count": TOP_BLOCK_REASON_OBSERVE_ONLY_COUNT,
        "insufficient_eligible_members_epoch_count": INSUFFICIENT_ELIGIBLE_MEMBERS_EPOCH_COUNT,
        "legacy_reference_trade_count": LEGACY_REFERENCE_TRADE_COUNT,
    }


def materialize_registration_config(
    *,
    canonical: EvidenceBundleValidation,
    registration_evidence_dir: Path | None = None,
) -> dict[str, Any]:
    metrics = _metrics_from_canonical(canonical.bundle_path)
    payload: dict[str, Any] = {
        "artifact_kind": REGISTRATION_ID,
        "artifact_version": REGISTRATION_VERSION,
        "schema_version": SCHEMA_VERSION,
        "scope_classification": SCOPE_CLASSIFICATION,
        "go_token": OPERATOR_GO_TOKEN,
        "operator_decision": OPERATOR_DECISION,
        "governance_ref": GOVERNANCE_REL_PATH,
        "binding_config_ref": VERSIONED_BINDING_CONFIG_REL_PATH,
        "pairwise_scope_ratification_config_ref": PAIRWISE_SCOPE_RATIFICATION_CONFIG_REL_PATH,
        "research_scope": RESEARCH_SCOPE,
        "strategy_id": STRATEGY_ID,
        "strategy_version": STRATEGY_VERSION,
        "strategy_binding": STRATEGY_BINDING,
        "hypothesis_id": HYPOTHESIS_ID,
        "score_family_policy": SCORE_FAMILY_POLICY,
        "binding_digest": BINDING_DIGEST,
        "implementation_digest": IMPLEMENTATION_DIGEST,
        "config_digest": CONFIG_DIGEST,
        "data_digest": DATA_DIGEST,
        "material_difference_digest": MATERIAL_DIFFERENCE_DIGEST,
        "canonical_evaluation_bundle": str(canonical.bundle_path),
        "canonical_evaluation_timestamp": CANONICAL_EVALUATION_TIMESTAMP,
        "canonical_manifest_digest": canonical.manifest_digest,
        "canonical_manifest_verify_rc": canonical.manifest_verify_rc,
        "pr5197_closeout_dir": str(PR5197_CLOSEOUT_DIR),
        "oi_terminal_ratification_dir": str(OI_TERMINAL_RATIFICATION_DIR),
        "primary_cause_class": PRIMARY_CAUSE_CLASS,
        "secondary_cause_class": SECONDARY_CAUSE_CLASS,
        "terminal_status": TERMINAL_STATUS,
        "terminal_failure_class": TERMINAL_FAILURE_CLASS,
        "terminal_verdict": TERMINAL_VERDICT,
        "baseline_verdict": BASELINE_VERDICT,
        "terminal_economic_decision": BASELINE_VERDICT,
        "economic_evaluation_executed": True,
        "implementation_defect_proven": False,
        "binding_defect_proven": False,
        "implementation_or_binding_defect_primary": False,
        "no_canonical_market_opportunity_primary": False,
        "net_return": metrics["net_return"],
        "trade_count": metrics["trade_count"],
        "policy_minimum_trade_count": metrics["policy_minimum_trade_count"],
        "sample_sufficiency_status": metrics["sample_sufficiency_status"],
        "directional_candidate_count": metrics["directional_candidate_count"],
        "directional_confirmed_count": metrics["directional_confirmed_count"],
        "trades_opened_count": metrics["trades_opened_count"],
        "top_block_reason_observe_only_count": metrics["top_block_reason_observe_only_count"],
        "insufficient_eligible_members_epoch_count": metrics[
            "insufficient_eligible_members_epoch_count"
        ],
        "legacy_reference_trade_count": metrics["legacy_reference_trade_count"],
        "walk_forward_status": metrics["walk_forward_status"],
        "monte_carlo_status": metrics["monte_carlo_status"],
        "stress_status": metrics["stress_status"],
        "economic_validity_offline_gate_pass": False,
        "retry_allowed_same_binding": False,
        "same_binding_retry_allowed": False,
        "unchanged_retry_blocked": True,
        "immutable_binding_retry_allowed": False,
        "policy_rescue_allowed": False,
        "negative_evidence_preserved": True,
        "terminal_negative_evidence_for_unchanged_binding": False,
        "terminal_insufficient_sample_evidence_for_unchanged_binding": True,
        "distinct_scope_required": True,
        "selected_distinct_scope": SELECTED_DISTINCT_SCOPE,
        "selected_distinct_strategy_id": SELECTED_DISTINCT_STRATEGY_ID,
        "selected_distinct_strategy_version": SELECTED_DISTINCT_STRATEGY_VERSION,
        "selected_distinct_hypothesis_id": SELECTED_DISTINCT_HYPOTHESIS_ID,
        "selected_distinct_hypothesis_family": SELECTED_DISTINCT_HYPOTHESIS_FAMILY,
        "selected_distinct_score_family_policy": SELECTED_DISTINCT_SCORE_FAMILY_POLICY,
        "selected_distinct_material_difference_primary": SELECTED_DISTINCT_MATERIAL_DIFFERENCE_PRIMARY,
        "selected_distinct_data_readiness": SELECTED_DISTINCT_DATA_READINESS,
        "selected_distinct_material_difference_digest": SELECTED_DISTINCT_MATERIAL_DIFFERENCE_DIGEST,
        "new_binding_required": True,
        "existing_binding_reused": False,
        "new_hypothesis_id": True,
        "material_difference_proven": True,
        "distinct_scope_ratified": True,
        "distinct_scope_candidate_inventory": build_distinct_scope_candidate_inventory(),
        "material_difference_matrix": build_material_difference_matrix(),
        "exact_binding_retry_guard_report": build_exact_binding_retry_guard_report(),
        "retry_non_equivalence_proof": build_retry_non_equivalence_proof(),
        "zero_trade_causal_classification": build_zero_trade_causal_classification(),
        "no_economic_reevaluation": True,
        "no_parameter_change": True,
        "no_policy_rescue": True,
        "no_runtime_or_promotion_action": True,
        "promotion_granted": False,
        "runtime_authority_touched": False,
        "offline_only": True,
        "research_only_successor": True,
        "futures_only": True,
        "bitcoin_direction_allowed": False,
        "spot_allowed": False,
        "synthetic_spot_allowed": False,
        "pre_merge_origin_main": PRE_MERGE_ORIGIN_MAIN,
        "durable_evidence_refs": "; ".join(
            [
                f"{canonical.bundle_path} (MANIFEST_VERIFY_RC=0)",
                f"{PR5197_CLOSEOUT_DIR} (MANIFEST_VERIFY_RC=0)",
                f"{OI_TERMINAL_RATIFICATION_DIR} (MANIFEST_VERIFY_RC=0)",
            ]
        ),
        "metrics": metrics,
        "status": "TERMINAL_INSUFFICIENT_SAMPLE_REGISTRATION_AND_DISTINCT_SCOPE_RATIFICATION_COMPLETE",
        "verdict": RegistrationVerdict.PASS.value,
        "next_canonical_step": NEXT_CANONICAL_STEP,
        "next_go_token": NEXT_GO_TOKEN,
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
    }
    if registration_evidence_dir is not None:
        payload["registration_evidence_dir"] = str(registration_evidence_dir)
    payload["registration_digest"] = compute_registration_digest(payload)
    return payload


def apply_versioned_binding_registration_fields(
    binding: Mapping[str, Any],
    registration: Mapping[str, Any],
) -> dict[str, Any]:
    updated = dict(binding)
    updated["economic_evaluation_executed"] = True
    updated["economic_evaluation_status"] = "COMPLETE_FAIL_INSUFFICIENT_SAMPLE"
    updated["economic_validity_offline_gate_pass"] = False
    updated["promotion_eligible"] = False
    updated["runtime_rewire_admissible"] = False
    updated["retry_unchanged_binding_allowed"] = False
    updated["re_evaluation_allowed"] = False
    updated["evaluation_authorized"] = False
    updated["economic_evaluation_authorized"] = False
    updated["policy_or_threshold_changed"] = False
    updated["binding_changed"] = False
    updated["historical_economic_result"] = BASELINE_VERDICT
    updated["trade_count"] = registration["trade_count"]
    updated["net_return"] = registration["net_return"]
    updated["baseline_verdict"] = BASELINE_VERDICT
    updated["terminal_verdict"] = TERMINAL_VERDICT
    updated["sample_sufficiency_status"] = registration["sample_sufficiency_status"]
    updated["terminal_negative_evidence_for_unchanged_binding"] = False
    updated["terminal_insufficient_sample_evidence_for_unchanged_binding"] = True
    updated["negative_evidence_preserved"] = True
    updated["terminal_status"] = TERMINAL_STATUS
    updated["primary_cause_class"] = PRIMARY_CAUSE_CLASS
    updated["secondary_cause_class"] = SECONDARY_CAUSE_CLASS
    updated["primary_failure_class"] = PRIMARY_CAUSE_CLASS
    updated["secondary_failure_class"] = SECONDARY_CAUSE_CLASS
    updated["canonical_evaluation_timestamp"] = CANONICAL_EVALUATION_TIMESTAMP
    updated["canonical_evaluation_bundle"] = registration["canonical_evaluation_bundle"]
    updated["economic_viability_evidence_ref"] = (
        f"{registration['canonical_evaluation_bundle']} (MANIFEST_VERIFY_RC=0)"
    )
    updated["economic_viability_evidence_manifest_digest"] = registration[
        "canonical_manifest_digest"
    ]
    updated["durable_evidence_refs"] = registration["durable_evidence_refs"]
    updated["terminal_failure_class"] = TERMINAL_FAILURE_CLASS
    updated["walk_forward_status"] = registration["walk_forward_status"]
    updated["monte_carlo_status"] = registration["monte_carlo_status"]
    updated["stress_status"] = registration["stress_status"]
    updated["unchanged_retry_blocked"] = True
    updated["policy_rescue_allowed"] = False
    updated["distinct_scope_required"] = True
    updated["selected_distinct_scope"] = SELECTED_DISTINCT_SCOPE
    updated["selected_distinct_scope_ratified"] = True
    updated["binding_digest_at_terminal_registration"] = BINDING_DIGEST
    updated["implementation_digest_at_terminal_registration"] = IMPLEMENTATION_DIGEST
    updated["directional_candidate_count"] = registration["directional_candidate_count"]
    updated["directional_confirmed_count"] = registration["directional_confirmed_count"]
    updated["trades_opened_count"] = registration["trades_opened_count"]
    return updated
