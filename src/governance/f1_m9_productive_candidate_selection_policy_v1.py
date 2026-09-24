"""Owner-bound F1/M9 prospective productive candidate selection policy v1.

Defines deterministic selection semantics only. Does not execute campaigns,
select candidates, authorize productive apply, or mutate productive values.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, Mapping, Sequence

from src.governance.m9_volatility_numeric_max_age_numeric_productive_target_v1 import (
    OPTIMIZATION_SURFACE_ID,
    POLICY_CONSUMER_MODULE,
    SOURCE_CANDIDATE_PARAMETER,
    TARGET_POLICY_PARAMETER,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256, is_valid_sha256_hex
from src.research.canonical_volatility_numeric_max_age_parameter_research_execution_v1.constants_v1 import (
    ALTERNATIVE_HYPOTHESIS_H1,
    BASELINE_CANDIDATE_ID,
    HOLDOUT_FRACTION,
    MAX_COVERAGE_REDUCTION_VS_BASELINE,
    MAX_NEIGHBORHOOD_SENSITIVITY,
    MAX_STALE_REJECTION_RATE,
    MAX_WALK_FORWARD_INSTABILITY,
    MINIMUM_EVIDENCE_COUNT,
    MINIMUM_REGIME_COUNT,
    MINIMUM_SESSION_COUNT,
    NULL_HYPOTHESIS_H0,
    OPERATOR_BOUND_CANDIDATE_MAX_AGE_SECONDS,
    RESEARCH_CONCLUSION_INSUFFICIENT,
    RESEARCH_CONCLUSION_NO_ROBUST,
    RESEARCH_CONCLUSION_REGION_PENDING,
    RESEARCH_QUESTION,
    WALK_FORWARD_FOLDS,
)
from trading.master_v2.canonical_volatility_numeric_max_age_parameter_research_design_and_evidence_accumulation_contract_v1 import (
    PREREGISTERED_REJECTION_CRITERIA,
    PREREGISTERED_ROBUSTNESS_REQUIREMENTS,
    PREREGISTERED_SELECTION_CRITERIA,
)

SCHEMA_VERSION: Final[str] = "f1_m9_productive_candidate_selection_policy/v1"
WORKPACKAGE_ID: Final[str] = (
    "F1_M9_PRODUCTIVE_CANDIDATE_SELECTION_POLICY_AND_PROSPECTIVE_CAMPAIGN_V1"
)
OWNER_SELECTION_POLICY_ID: Final[str] = (
    "f1_m9_volatility_numeric_max_age_productive_candidate_selection_policy_v1"
)
NORMATIVE_SPEC: Final[str] = (
    "docs/ops/specs/F1_M9_PRODUCTIVE_CANDIDATE_SELECTION_POLICY_AND_PROSPECTIVE_CAMPAIGN_NORMATIVE_V1.md"
)
POLICY_CONFIG: Final[str] = "config/governance/f1_m9_productive_candidate_selection_policy_v1.json"
POLICY_DECISION_CONFIG: Final[str] = (
    "config/governance/f1_m9_productive_candidate_selection_policy_v1_decision_v1.json"
)

BOUND_ORIGIN_MAIN_SHA: Final[str] = "16fdb6a6b1f87d8e68874c9a35c296f285d9d2f8"
DISCRETE_BOUNDS_CONFIG: Final[str] = (
    "config/governance/optimizable_envelope/volatility_numeric_max_age_discrete_bounds_v1.json"
)
ALLOWED_POLICY_DOMAIN_CONFIG: Final[str] = (
    "config/governance/optimizable_envelope/volatility_numeric_max_age_allowed_policy_domain_v1.json"
)
RISK_CONSTRAINTS_CONFIG: Final[str] = (
    "config/governance/optimizable_envelope/volatility_numeric_max_age_risk_constraints_v1.json"
)
RESEARCH_EXECUTION_SPEC: Final[str] = (
    "docs/ops/specs/"
    "MASTER_V2_CANONICAL_VOLATILITY_NUMERIC_MAX_AGE_PARAMETER_RESEARCH_EXECUTION_V1.md"
)
RESEARCH_EVALUATOR_MODULE: Final[str] = (
    "research.canonical_volatility_numeric_max_age_parameter_research_execution_v1.evaluator_v1"
)

CANDIDATE_SELECTION_AUTHORITY: Final[str] = "F1_M9_SCOPED_RESEARCH_TO_PROPOSAL_SELECTION_ONLY"
FORBIDDEN_AUTHORITIES: Final[tuple[str, ...]] = (
    "TRADING_DECISION_AUTHORITY",
    "PROMOTION_AUTHORITY",
    "PRODUCTIVE_APPLY_AUTHORITY",
    "DIRECT_PRODUCTIVE_WRITE_AUTHORITY",
)

HISTORICAL_COUNTERFACTUAL_CAMPAIGN_ID: Final[str] = (
    "cv_maxage_productive_evidence_campaign_v1_f5e3f95105cd847f"
)
HISTORICAL_PREREGISTRATION_CONFIG: Final[str] = (
    "config/research/canonical_volatility_numeric_max_age_productive_evidence_session_"
    "preregistration_r1_active_v1.json"
)
HISTORICAL_PREREGISTRATION_DIGEST: Final[str] = (
    "59769afb0da30b4f00282dcb13c0c8f7cd45c9c65a944b7bc1b42b4565f80b75"
)

SELECTION_RULE_ID: Final[str] = "F1_M9_ROBUST_REGION_UNIQUE_SURVIVOR_POINT_V1"
TIE_RULE_ID: Final[str] = "F1_M9_NO_SELECTION_ON_NON_UNIQUE_SURVIVOR_V1"
NO_SELECTION_RULE_ID: Final[str] = "F1_M9_FAIL_CLOSED_NO_SELECTION_V1"

OUTCOME_NO_SELECTION: Final[str] = "NO_SELECTION"
OUTCOME_SELECTED: Final[str] = "SELECTED_GOVERNED_CANDIDATE_PROPOSAL_ONLY"


@dataclass(frozen=True, slots=True)
class F1M9SelectionPolicyResolutionV1:
    owner_selection_policy_resolved: bool
    owner_selection_policy_id: str
    owner_selection_policy_digest: str
    admissible_parameter_space_resolved: bool
    objective_semantics_resolved: bool
    evidence_requirements_resolved: bool
    oos_requirement_resolved: bool
    robustness_requirement_resolved: bool
    economic_requirement_resolved: bool
    failure_evidence_requirement_resolved: bool
    tie_rule_resolved: bool
    no_selection_rule_resolved: bool
    f1_m9_scoped_candidate_selection_policy_created: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "admissible_parameter_space_resolved": self.admissible_parameter_space_resolved,
            "economic_requirement_resolved": self.economic_requirement_resolved,
            "evidence_requirements_resolved": self.evidence_requirements_resolved,
            "f1_m9_scoped_candidate_selection_policy_created": (
                self.f1_m9_scoped_candidate_selection_policy_created
            ),
            "failure_evidence_requirement_resolved": self.failure_evidence_requirement_resolved,
            "no_selection_rule_resolved": self.no_selection_rule_resolved,
            "objective_semantics_resolved": self.objective_semantics_resolved,
            "oos_requirement_resolved": self.oos_requirement_resolved,
            "owner_selection_policy_digest": self.owner_selection_policy_digest,
            "owner_selection_policy_id": self.owner_selection_policy_id,
            "owner_selection_policy_resolved": self.owner_selection_policy_resolved,
            "robustness_requirement_resolved": self.robustness_requirement_resolved,
            "tie_rule_resolved": self.tie_rule_resolved,
        }


def _repo_root(repo_root: Path | None) -> Path:
    return repo_root or Path(__file__).resolve().parents[2]


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"CONFIG_NOT_MAPPING:{path}")
    return payload


def policy_body_for_digest(payload: Mapping[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in payload.items() if k != "owner_selection_policy_digest"}


def compute_owner_selection_policy_digest(payload: Mapping[str, Any]) -> str:
    return compute_content_sha256(policy_body_for_digest(payload))


def build_owner_selection_policy_v1(*, repo_root: Path | None = None) -> dict[str, Any]:
    root = _repo_root(repo_root)
    discrete = _load_json(root / DISCRETE_BOUNDS_CONFIG)
    domain = _load_json(root / ALLOWED_POLICY_DOMAIN_CONFIG)
    grid = list(discrete.get("candidate_max_age_seconds") or [])
    domain_grid = list(domain.get("candidate_max_age_seconds") or [])
    if grid != domain_grid or tuple(grid) != OPERATOR_BOUND_CANDIDATE_MAX_AGE_SECONDS:
        raise ValueError("F1_M9_CANDIDATE_DOMAIN_DRIFT")

    body: dict[str, Any] = {
        "artifact_class": "F1_M9_PRODUCTIVE_CANDIDATE_SELECTION_POLICY_V1",
        "schema_version": SCHEMA_VERSION,
        "workpackage_id": WORKPACKAGE_ID,
        "owner_selection_policy_id": OWNER_SELECTION_POLICY_ID,
        "bound_origin_main_sha": BOUND_ORIGIN_MAIN_SHA,
        "surface_id": OPTIMIZATION_SURFACE_ID,
        "parameter_ids": {
            "source_candidate_parameter": SOURCE_CANDIDATE_PARAMETER,
            "target_policy_parameter": TARGET_POLICY_PARAMETER,
        },
        "target_consumer_module": POLICY_CONSUMER_MODULE,
        "candidate_selection_authority": CANDIDATE_SELECTION_AUTHORITY,
        "forbidden_authorities": list(FORBIDDEN_AUTHORITIES),
        "trading_decision_authority": "NONE",
        "optimization_trading_decision_authority": "NONE",
        "optimization_promotion_authority": "NONE",
        "productive_apply_authority": "NONE",
        "direct_productive_write_authority": "NONE",
        "admissible_parameter_space": {
            "bind_discrete_bounds_config": DISCRETE_BOUNDS_CONFIG,
            "bind_allowed_policy_domain_config": ALLOWED_POLICY_DOMAIN_CONFIG,
            "bind_risk_constraints_config": RISK_CONSTRAINTS_CONFIG,
            "candidate_max_age_seconds": grid,
            "age_unit": "SECONDS",
            "age_reference_clock": "MARKET_EVENT_TIME",
            "bound_semantics": "DISCRETE_CANDIDATE_SET_ONLY",
            "continuous_range_allowed": False,
            "interpolation_allowed": False,
            "extension_allowed": False,
            "implicit_defaults_allowed": False,
            "productive_policy_literal_allowed": False,
            "baseline_candidate_id": BASELINE_CANDIDATE_ID,
            "boundary_handling": "OUT_OF_DOMAIN_ARGUMENTS_REJECTED_FAIL_CLOSED",
        },
        "objective_semantics": {
            "decision_objective_class": "MV2_DOUBLE_PLAY_STALE_EXPOSURE_ROBUSTNESS_AND_DECISION_QUALITY",
            "forbidden_objectives": [
                "BEST_SHARPE_ALONE",
                "BEST_PNL_ALONE",
                "BEST_TRADE_COUNT_ALONE",
                "SINGLE_METRIC_MAXIMIZATION",
            ],
            "research_question": RESEARCH_QUESTION,
            "null_hypothesis_h0": NULL_HYPOTHESIS_H0,
            "alternative_hypothesis_h1": ALTERNATIVE_HYPOTHESIS_H1,
            "preregistered_selection_criteria": list(PREREGISTERED_SELECTION_CRITERIA),
            "preregistered_rejection_criteria": list(PREREGISTERED_REJECTION_CRITERIA),
            "interpretation": (
                "Select at most one grid point only if prospective evidence demonstrates "
                "robust stale-exposure reduction and non-degraded decision quality versus "
                "the unresolved baseline under preregistered multi-session, multi-regime, "
                "OOS, robustness, economic, and failure-evidence gates."
            ),
        },
        "evidence_requirements": {
            "minimum_real_evidence": True,
            "synthetic_or_fixture_decision_evidence_forbidden": True,
            "minimum_session_count": MINIMUM_SESSION_COUNT,
            "minimum_regime_count": MINIMUM_REGIME_COUNT,
            "minimum_evidence_count": MINIMUM_EVIDENCE_COUNT,
            "require_walk_forward_folds": WALK_FORWARD_FOLDS,
            "require_final_holdout_fraction": HOLDOUT_FRACTION,
            "require_regime_coverage": True,
            "require_session_coverage": True,
            "require_failure_evidence_on_rejection": True,
            "require_economic_metrics_on_decision_records": True,
            "preregistered_robustness_requirements": list(PREREGISTERED_ROBUSTNESS_REQUIREMENTS),
            "research_execution_evaluator_module": RESEARCH_EVALUATOR_MODULE,
            "research_execution_spec": RESEARCH_EXECUTION_SPEC,
            "missing_evidence_behavior": OUTCOME_NO_SELECTION,
            "contamination_rules": {
                "pre_preregistration_evidence_decision_forbidden": True,
                "historical_counterfactual_campaign_decision_forbidden": True,
                "historical_counterfactual_campaign_id": HISTORICAL_COUNTERFACTUAL_CAMPAIGN_ID,
                "historical_preregistration_digest": HISTORICAL_PREREGISTRATION_DIGEST,
                "lineage_mismatch_behavior": OUTCOME_NO_SELECTION,
                "stale_or_incomplete_campaign_behavior": OUTCOME_NO_SELECTION,
            },
        },
        "oos_requirement": {
            "holdout_fraction": HOLDOUT_FRACTION,
            "walk_forward_folds": WALK_FORWARD_FOLDS,
            "holdout_degradation_triggers_no_selection": True,
            "in_sample_only_selection_forbidden": True,
        },
        "robustness_requirement": {
            "max_walk_forward_instability": MAX_WALK_FORWARD_INSTABILITY,
            "max_neighborhood_sensitivity": MAX_NEIGHBORHOOD_SENSITIVITY,
            "max_coverage_reduction_vs_baseline": MAX_COVERAGE_REDUCTION_VS_BASELINE,
            "max_stale_rejection_rate": MAX_STALE_REJECTION_RATE,
            "robustness_failure_triggers_no_selection": True,
        },
        "economic_requirement": {
            "require_net_pnl_after_costs_non_degraded_vs_baseline_on_holdout": True,
            "cost_ignoring_selection_forbidden": True,
            "drawdown_ignoring_selection_forbidden": True,
            "economic_failure_triggers_no_selection": True,
        },
        "failure_evidence_requirement": {
            "rejection_matrix_required": True,
            "rejection_reasons_required_on_fail": True,
            "insufficient_power_triggers_no_selection": True,
        },
        "selection_rule": {
            "selection_rule_id": SELECTION_RULE_ID,
            "deterministic": True,
            "inputs": [
                "prospective_campaign_research_conclusion",
                "rejection_matrix",
                "longest_contiguous_robust_region_seconds",
            ],
            "algorithm_steps": [
                "REQUIRE research_conclusion == ROBUST_CANDIDATE_REGION_IDENTIFIED_PENDING_OWNER_RATIFICATION",
                "BUILD survivors = grid points with apply_rejection_criteria_v1.rejected == false",
                "INTERSECT survivors with longest_contiguous_robust_region from conclusion",
                "IF intersection cardinality == 1 THEN SELECTED else NO_SELECTION",
            ],
            "forbidden_shortcuts": [
                "ARRAY_ORDER",
                "CANDIDATE_ID_LEXICOGRAPHIC",
                "MIN_THRESHOLD",
                "MAX_THRESHOLD",
                "SHARPE_MAX",
                "PNL_MAX",
            ],
            "outcome_classes": [OUTCOME_SELECTED, OUTCOME_NO_SELECTION],
            "selected_outcome_is_proposal_only": True,
        },
        "tie_rule": {
            "tie_rule_id": TIE_RULE_ID,
            "unresolved_tie_behavior": OUTCOME_NO_SELECTION,
            "tie_definition": "intersection_cardinality_not_equal_to_one",
            "silent_tie_break_forbidden": True,
        },
        "no_selection_rule": {
            "no_selection_rule_id": NO_SELECTION_RULE_ID,
            "fail_closed_conditions": [
                "INSUFFICIENT_EVIDENCE",
                "OOS_HOLDOUT_FAILURE",
                "ROBUSTNESS_FAILURE",
                "ECONOMIC_FAILURE",
                "RISK_CONSTRAINT_VIOLATION",
                "CONTAMINATION",
                "UNRESOLVED_TIE",
                "MISSING_REQUIRED_REGIME_OR_SESSION",
                "STALE_OR_INCOMPLETE_CAMPAIGN",
                "LINEAGE_OR_PREREGISTRATION_MISMATCH",
                "RESEARCH_CONCLUSION_NOT_REGION_PENDING",
            ],
            "default_outcome": OUTCOME_NO_SELECTION,
        },
        "historical_evidence_classification": {
            "counterfactual_campaign_id": HISTORICAL_COUNTERFACTUAL_CAMPAIGN_ID,
            "counterfactual_only": True,
            "permitted_use": "RESEARCH_CONTEXT_ONLY",
            "decision_making_use_forbidden": True,
        },
    }
    body["owner_selection_policy_digest"] = compute_owner_selection_policy_digest(body)
    return body


def verify_owner_selection_policy_v1(
    payload: Mapping[str, Any], *, repo_root: Path | None = None
) -> None:
    root = _repo_root(repo_root)
    stored = str(payload.get("owner_selection_policy_digest") or "")
    if not is_valid_sha256_hex(stored):
        raise ValueError("OWNER_SELECTION_POLICY_DIGEST_INVALID")
    recomputed = compute_owner_selection_policy_digest(payload)
    if recomputed != stored:
        raise ValueError("OWNER_SELECTION_POLICY_DIGEST_MISMATCH")
    expected = build_owner_selection_policy_v1(repo_root=root)
    if policy_body_for_digest(expected) != policy_body_for_digest(dict(payload)):
        raise ValueError("OWNER_SELECTION_POLICY_BODY_DRIFT")


def load_owner_selection_policy_v1(*, repo_root: Path | None = None) -> dict[str, Any]:
    root = _repo_root(repo_root)
    payload = _load_json(root / POLICY_CONFIG)
    verify_owner_selection_policy_v1(payload, repo_root=root)
    return payload


def _longest_contiguous_region(values: Sequence[int], *, domain: Sequence[int]) -> list[int]:
    accepted = set(values)
    runs: list[list[int]] = []
    current: list[int] = []
    for value in domain:
        if value in accepted:
            current.append(value)
        elif current:
            runs.append(current)
            current = []
    if current:
        runs.append(current)
    if not runs:
        return []
    return max(runs, key=len)


def apply_f1_m9_selection_rule_v1(
    *,
    research_conclusion: str,
    robust_candidate_region: Sequence[int] | None,
    rejection_matrix: Sequence[Mapping[str, Any]],
    candidate_domain_seconds: Sequence[int] | None = None,
) -> dict[str, Any]:
    """Pure deterministic selection rule (proposal-only). Never writes productive state."""
    domain = tuple(candidate_domain_seconds or OPERATOR_BOUND_CANDIDATE_MAX_AGE_SECONDS)
    if research_conclusion != RESEARCH_CONCLUSION_REGION_PENDING:
        return {
            "outcome": OUTCOME_NO_SELECTION,
            "selected_max_age_seconds": None,
            "selected_candidate_id": None,
            "reason_codes": ["RESEARCH_CONCLUSION_NOT_ELIGIBLE"],
            "productive_authorization": False,
            "owner_apply_record_materialization": False,
            "productive_apply": False,
        }

    survivors: set[int] = set()
    for row in rejection_matrix:
        if row.get("candidate_id") == BASELINE_CANDIDATE_ID:
            continue
        if row.get("rejected") is True:
            continue
        cand_id = str(row.get("candidate_id") or "")
        if not cand_id.startswith("CANDIDATE_") or not cand_id.endswith("_S"):
            continue
        try:
            seconds = int(cand_id.removeprefix("CANDIDATE_").removesuffix("_S"))
        except ValueError:
            continue
        if seconds in domain:
            survivors.add(seconds)

    region = list(robust_candidate_region or [])
    if not region:
        region = _longest_contiguous_region(sorted(survivors), domain=domain)
    intersection = sorted(s for s in survivors if s in set(region))
    if len(intersection) != 1:
        return {
            "outcome": OUTCOME_NO_SELECTION,
            "selected_max_age_seconds": None,
            "selected_candidate_id": None,
            "reason_codes": ["UNIQUE_SURVIVOR_NOT_ESTABLISHED"],
            "productive_authorization": False,
            "owner_apply_record_materialization": False,
            "productive_apply": False,
        }
    seconds = intersection[0]
    return {
        "outcome": OUTCOME_SELECTED,
        "selected_max_age_seconds": seconds,
        "selected_candidate_id": f"CANDIDATE_{seconds}_S",
        "reason_codes": ["UNIQUE_ROBUST_REGION_SURVIVOR"],
        "productive_authorization": False,
        "owner_apply_record_materialization": False,
        "productive_apply": False,
    }


def resolve_f1_m9_selection_policy_v1(
    *, repo_root: Path | None = None
) -> F1M9SelectionPolicyResolutionV1:
    root = _repo_root(repo_root)
    path = root / POLICY_CONFIG
    if not path.is_file():
        return F1M9SelectionPolicyResolutionV1(
            owner_selection_policy_resolved=False,
            owner_selection_policy_id=OWNER_SELECTION_POLICY_ID,
            owner_selection_policy_digest="",
            admissible_parameter_space_resolved=False,
            objective_semantics_resolved=False,
            evidence_requirements_resolved=False,
            oos_requirement_resolved=False,
            robustness_requirement_resolved=False,
            economic_requirement_resolved=False,
            failure_evidence_requirement_resolved=False,
            tie_rule_resolved=False,
            no_selection_rule_resolved=False,
            f1_m9_scoped_candidate_selection_policy_created=False,
        )
    policy = load_owner_selection_policy_v1(repo_root=root)
    digest = str(policy["owner_selection_policy_digest"])
    return F1M9SelectionPolicyResolutionV1(
        owner_selection_policy_resolved=True,
        owner_selection_policy_id=str(policy["owner_selection_policy_id"]),
        owner_selection_policy_digest=digest,
        admissible_parameter_space_resolved=True,
        objective_semantics_resolved=True,
        evidence_requirements_resolved=True,
        oos_requirement_resolved=True,
        robustness_requirement_resolved=True,
        economic_requirement_resolved=True,
        failure_evidence_requirement_resolved=True,
        tie_rule_resolved=True,
        no_selection_rule_resolved=True,
        f1_m9_scoped_candidate_selection_policy_created=True,
    )


__all__ = [
    "CANDIDATE_SELECTION_AUTHORITY",
    "HISTORICAL_COUNTERFACTUAL_CAMPAIGN_ID",
    "HISTORICAL_PREREGISTRATION_DIGEST",
    "NO_SELECTION_RULE_ID",
    "NORMATIVE_SPEC",
    "OUTCOME_NO_SELECTION",
    "OUTCOME_SELECTED",
    "OWNER_SELECTION_POLICY_ID",
    "POLICY_CONFIG",
    "POLICY_DECISION_CONFIG",
    "SCHEMA_VERSION",
    "SELECTION_RULE_ID",
    "TIE_RULE_ID",
    "WORKPACKAGE_ID",
    "F1M9SelectionPolicyResolutionV1",
    "apply_f1_m9_selection_rule_v1",
    "build_owner_selection_policy_v1",
    "compute_owner_selection_policy_digest",
    "load_owner_selection_policy_v1",
    "policy_body_for_digest",
    "resolve_f1_m9_selection_policy_v1",
    "verify_owner_selection_policy_v1",
]
