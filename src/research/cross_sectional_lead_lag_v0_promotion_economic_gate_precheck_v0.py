"""Lead-lag v0 promotion economic gate precheck v0.

Offline-only narrow adapter binding Step 5 research-eval decision parity evidence
to the canonical promotion_economic_gate_v1 owner. Reuses the real production gate
path without executing economic evaluation or granting promotion authority.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, replace
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.backtest.economic_validity_policy_v1 import canonical_economic_validity_policy_v1
from src.governance.promotion_loop.promotion_economic_gate_v1 import (
    AUTHORITY_EFFECT_NONE,
    FAIL_STATUS,
    PASS_STATUS,
    PROMOTION_ECONOMIC_GATE_POLICY_OWNER,
    PROMOTION_ECONOMIC_GATE_POLICY_VERSION,
    REASON_CONFIDENCE_SCORE_ONLY,
    REASON_ECONOMIC_EVIDENCE_INADMISSIBLE,
    REASON_ECONOMIC_EVIDENCE_MISSING,
    REASON_ECONOMIC_VALIDITY_NOT_PROVEN,
    REASON_REQUIRED_INPUT_MISSING,
    REASON_REQUIRED_STATUS_UNKNOWN,
    PromotionEconomicGateInputV1,
    PromotionEconomicGateResultV1,
    canonical_promotion_economic_gate_policy_v1,
    evaluate_promotion_economic_gate_v1,
    promotion_economic_gate_schema_v1,
)
from src.research.cross_sectional_futures_lead_lag_information_diffusion_v0_versioned_hypothesis_binding_v0 import (
    RESEARCH_SCOPE,
    STRATEGY_ID,
    STRATEGY_VERSION,
)

PACKAGE_MARKER = "CROSS_SECTIONAL_LEAD_LAG_V0_PROMOTION_ECONOMIC_GATE_PRECHECK_V0=true"
CONTRACT_VERSION = "v0"
CONTRACT_OWNER = "research.cross_sectional_lead_lag_v0_promotion_economic_gate_precheck_v0"
CONTRACT_MODULE = "src/research/cross_sectional_lead_lag_v0_promotion_economic_gate_precheck_v0.py"

OPERATOR_GO = "GO_CROSS_SECTIONAL_LEAD_LAG_V0_PROMOTION_ECONOMIC_GATE_PRECHECK_V0"
ALLOWED_OPERATOR_GOS: frozenset[str] = frozenset({OPERATOR_GO})

CANONICAL_PROMOTION_GATE_OWNER = PROMOTION_ECONOMIC_GATE_POLICY_OWNER
CANONICAL_PROMOTION_GATE_POLICY_VERSION = PROMOTION_ECONOMIC_GATE_POLICY_VERSION
CANONICAL_PROMOTION_GATE_CALLABLE = (
    "governance.promotion_loop.promotion_economic_gate_v1.evaluate_promotion_economic_gate_v1"
)

DEFAULT_SOURCE_CLOSEOUT_REF = (
    "research/pr5140_merge_closeout_cross_sectional_lead_lag_v0_research_eval_decision_"
    "parity_contract_suite_v0_20260713T010633Z"
)
OFFLINE_EVALUATION_TIMESTAMP = "2026-07-13T01:06:33Z"

CONFIG_REL_PATH = (
    "config/research/cross_sectional_lead_lag_v0_promotion_economic_gate_precheck_v0.json"
)

REQUIRED_GATE_RESULT_FIELDS: tuple[str, ...] = (
    "gate_result_id",
    "gate_policy_id",
    "gate_policy_version",
    "promotion_candidate_status",
    "eligible_for_promotion_candidate",
    "blocking_reasons",
    "reason_codes",
    "evaluated_evidence_refs",
    "evaluation_timestamp",
    "evaluation_digest",
    "authority_effect",
    "runtime_effect",
    "economic_validity_pass",
    "robustness_pass",
    "evidence_admissible",
    "safety_policy_pass",
)

NEGATIVE_PATH_CASES: tuple[str, ...] = (
    "missing_economic_evidence",
    "inadmissible_evidence",
    "economic_gate_fail",
    "missing_robustness_evidence",
    "malformed_evidence",
    "unsupported_status",
    "legacy_confidence_only_bypass",
    "direct_promotion_pass_overclaim",
    "nondeterministic_repeated_execution",
)


class PrecheckTerminalStatus(str, Enum):
    PRECHECK_COMPLETE = "PRECHECK_COMPLETE"
    FAIL_CLOSED = "FAIL_CLOSED"


@dataclass(frozen=True)
class LeadLagPromotionGatePrecheckContextV0:
    source_closeout_ref: str
    research_eval_decision_parity_suite_pass: bool
    strategy_id: str
    strategy_version: str
    candidate_id: str
    config_digest: str
    implementation_digest: str
    evidence_manifest_digest: str
    economic_viability_evidence_ref: str = ""
    economic_validity_status: str = FAIL_STATUS
    economic_validity_proven: bool = False
    profitability_claim_allowed: bool = False
    economic_validity_offline_gate_pass: bool = False
    robustness_status: str = FAIL_STATUS
    data_admissibility_status: str = PASS_STATUS
    evidence_admissibility_status: str = FAIL_STATUS
    evidence_admissible: bool = False
    policy_threshold_status: str = FAIL_STATUS
    walk_forward_status: str = FAIL_STATUS
    out_of_sample_status: str = FAIL_STATUS
    monte_carlo_status: str = FAIL_STATUS
    stress_status: str = FAIL_STATUS
    parameter_sensitivity_status: str = FAIL_STATUS
    reproducibility_status: str = PASS_STATUS
    digest_binding_status: str = PASS_STATUS
    manifest_binding_status: str = PASS_STATUS
    safety_policy_status: str = PASS_STATUS
    futures_only: bool = True
    bitcoin_direction_allowed: bool = False
    promotion_basis_confidence_only: bool = False
    promotion_basis_in_sample_profit_only: bool = False
    zero_cost_evidence: bool = False


@dataclass(frozen=True)
class LeadLagPromotionGatePrecheckResultV0:
    status: PrecheckTerminalStatus
    precheck_complete: bool
    promotion_economic_gate_v1_real_owner_executed: bool
    structural_gate_input_binding_pass: bool
    gate_decision_field_parity_pass: bool
    gate_reason_code_parity_pass: bool
    gate_decision_order_parity_pass: bool
    deterministic_double_execution_pass: bool
    negative_path_fail_closed_pass: bool
    legacy_confidence_only_bypass_reachable: bool
    economic_evaluation_executed: bool
    economic_validity_offline_gate_pass: bool
    eligible_for_promotion_candidate: bool
    system_economic_evidence_admissible: bool
    gate_result: PromotionEconomicGateResultV1
    normalized_gate_result: dict[str, Any]
    input_binding: dict[str, Any]
    reason_codes: tuple[str, ...] = ()
    authority_effect: str = AUTHORITY_EFFECT_NONE
    runtime_effect: str = AUTHORITY_EFFECT_NONE


def _stable_digest(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def extract_binding_gate_fields_v0(versioned_binding: Mapping[str, Any]) -> dict[str, str]:
    return {
        "strategy_id": str(versioned_binding.get("strategy_id", STRATEGY_ID)),
        "strategy_version": str(versioned_binding.get("strategy_version", STRATEGY_VERSION)),
        "candidate_id": str(versioned_binding.get("research_scope", RESEARCH_SCOPE)),
        "config_digest": str(versioned_binding.get("config_digest", "")),
        "implementation_digest": str(versioned_binding.get("implementation_digest", "")),
        "evidence_manifest_digest": str(versioned_binding.get("binding_digest", "")),
    }


def build_lead_lag_promotion_gate_precheck_context_v0(
    *,
    versioned_binding: Mapping[str, Any],
    source_closeout_ref: str = DEFAULT_SOURCE_CLOSEOUT_REF,
    research_eval_decision_parity_suite_pass: bool = True,
    overrides: Mapping[str, Any] | None = None,
) -> LeadLagPromotionGatePrecheckContextV0:
    fields = extract_binding_gate_fields_v0(versioned_binding)
    evidence_ref = source_closeout_ref if research_eval_decision_parity_suite_pass else ""
    base = LeadLagPromotionGatePrecheckContextV0(
        source_closeout_ref=source_closeout_ref,
        research_eval_decision_parity_suite_pass=research_eval_decision_parity_suite_pass,
        strategy_id=fields["strategy_id"],
        strategy_version=fields["strategy_version"],
        candidate_id=fields["candidate_id"],
        config_digest=fields["config_digest"],
        implementation_digest=fields["implementation_digest"],
        evidence_manifest_digest=fields["evidence_manifest_digest"],
        economic_viability_evidence_ref=evidence_ref,
        reproducibility_status=PASS_STATUS
        if research_eval_decision_parity_suite_pass
        else FAIL_STATUS,
    )
    if overrides:
        return replace(base, **dict(overrides))
    return base


def build_promotion_gate_input_v0(
    ctx: LeadLagPromotionGatePrecheckContextV0,
) -> PromotionEconomicGateInputV1:
    economic_policy = canonical_economic_validity_policy_v1()
    return PromotionEconomicGateInputV1(
        strategy_id=ctx.strategy_id,
        strategy_version=ctx.strategy_version,
        candidate_id=ctx.candidate_id,
        economic_viability_evidence_ref=ctx.economic_viability_evidence_ref,
        economic_validity_status=ctx.economic_validity_status,
        economic_validity_proven=ctx.economic_validity_proven,
        profitability_claim_allowed=ctx.profitability_claim_allowed,
        economic_validity_offline_gate_pass=ctx.economic_validity_offline_gate_pass,
        robustness_status=ctx.robustness_status,
        data_admissibility_status=ctx.data_admissibility_status,
        evidence_admissibility_status=ctx.evidence_admissibility_status,
        evidence_admissible=ctx.evidence_admissible,
        policy_threshold_status=ctx.policy_threshold_status,
        walk_forward_status=ctx.walk_forward_status,
        out_of_sample_status=ctx.out_of_sample_status,
        monte_carlo_status=ctx.monte_carlo_status,
        stress_status=ctx.stress_status,
        parameter_sensitivity_status=ctx.parameter_sensitivity_status,
        reproducibility_status=ctx.reproducibility_status,
        digest_binding_status=ctx.digest_binding_status,
        manifest_binding_status=ctx.manifest_binding_status,
        safety_policy_status=ctx.safety_policy_status,
        futures_only=ctx.futures_only,
        bitcoin_direction_allowed=ctx.bitcoin_direction_allowed,
        config_digest=ctx.config_digest,
        implementation_digest=ctx.implementation_digest,
        policy_digest=economic_policy.policy_digest(),
        evidence_manifest_digest=ctx.evidence_manifest_digest,
        promotion_basis_confidence_only=ctx.promotion_basis_confidence_only,
        promotion_basis_in_sample_profit_only=ctx.promotion_basis_in_sample_profit_only,
        zero_cost_evidence=ctx.zero_cost_evidence,
    )


def validate_structural_gate_input_binding_v0(
    ctx: LeadLagPromotionGatePrecheckContextV0,
) -> tuple[bool, tuple[str, ...]]:
    reason_codes: list[str] = []
    required_text = (
        ("strategy_id", ctx.strategy_id),
        ("strategy_version", ctx.strategy_version),
        ("candidate_id", ctx.candidate_id),
        ("config_digest", ctx.config_digest),
        ("implementation_digest", ctx.implementation_digest),
        ("evidence_manifest_digest", ctx.evidence_manifest_digest),
    )
    for field_name, value in required_text:
        if not str(value).strip():
            reason_codes.append(f"{REASON_REQUIRED_INPUT_MISSING}:{field_name}")
    if ctx.bitcoin_direction_allowed:
        reason_codes.append("bitcoin_direction_forbidden")
    if not ctx.futures_only:
        reason_codes.append("futures_only_required")
    if ctx.research_eval_decision_parity_suite_pass and not ctx.source_closeout_ref.strip():
        reason_codes.append("source_closeout_ref_missing")
    return not reason_codes, tuple(reason_codes)


def normalize_gate_result_v0(result: PromotionEconomicGateResultV1) -> dict[str, Any]:
    payload = result.to_dict()
    payload["reason_codes"] = list(result.reason_codes)
    payload["blocking_reasons"] = list(result.blocking_reasons)
    payload["evaluated_evidence_refs"] = list(result.evaluated_evidence_refs)
    payload["evidence_refs"] = list(result.evidence_refs)
    return payload


def gate_decision_field_parity_ok_v0(result: PromotionEconomicGateResultV1) -> bool:
    normalized = normalize_gate_result_v0(result)
    return all(field in normalized for field in REQUIRED_GATE_RESULT_FIELDS)


def gate_reason_code_parity_ok_v0(
    *,
    result: PromotionEconomicGateResultV1,
    expected_subset: Sequence[str] | None = None,
) -> bool:
    if result.reason_codes != tuple(sorted(set(result.reason_codes))):
        return False
    if expected_subset is not None:
        return all(code in result.reason_codes for code in expected_subset)
    return True


def gate_decision_order_parity_ok_v0(result: PromotionEconomicGateResultV1) -> bool:
    return list(result.reason_codes) == sorted(result.reason_codes)


def evaluate_promotion_gate_from_context_v0(
    ctx: LeadLagPromotionGatePrecheckContextV0,
    *,
    evaluation_timestamp: str = OFFLINE_EVALUATION_TIMESTAMP,
) -> PromotionEconomicGateResultV1:
    gate_policy = canonical_promotion_economic_gate_policy_v1()
    input_data = build_promotion_gate_input_v0(ctx)
    return evaluate_promotion_economic_gate_v1(
        policy=gate_policy,
        input_data=input_data,
        evaluation_timestamp=evaluation_timestamp,
        expected_policy_digest=input_data.policy_digest,
    )


def evaluate_negative_path_case_v0(
    case_name: str,
    *,
    versioned_binding: Mapping[str, Any],
) -> dict[str, Any]:
    overrides_map: dict[str, Mapping[str, Any]] = {
        "missing_economic_evidence": {"economic_viability_evidence_ref": ""},
        "inadmissible_evidence": {
            "evidence_admissible": False,
            "evidence_admissibility_status": FAIL_STATUS,
        },
        "economic_gate_fail": {
            "economic_validity_status": FAIL_STATUS,
            "economic_validity_proven": False,
            "economic_validity_offline_gate_pass": False,
        },
        "missing_robustness_evidence": {
            "walk_forward_status": "",
            "robustness_status": FAIL_STATUS,
        },
        "malformed_evidence": {
            "config_digest": "not-a-valid-digest",
            "evidence_manifest_digest": "bad",
        },
        "unsupported_status": {"economic_validity_status": "MAYBE"},
        "legacy_confidence_only_bypass": {
            "promotion_basis_confidence_only": True,
            "economic_validity_status": PASS_STATUS,
            "economic_validity_proven": True,
            "profitability_claim_allowed": True,
            "robustness_status": PASS_STATUS,
            "evidence_admissibility_status": PASS_STATUS,
            "evidence_admissible": True,
            "policy_threshold_status": PASS_STATUS,
            "walk_forward_status": PASS_STATUS,
            "out_of_sample_status": PASS_STATUS,
            "monte_carlo_status": PASS_STATUS,
            "stress_status": PASS_STATUS,
            "parameter_sensitivity_status": PASS_STATUS,
        },
        "direct_promotion_pass_overclaim": {
            "economic_validity_status": PASS_STATUS,
            "economic_validity_proven": True,
            "profitability_claim_allowed": True,
            "robustness_status": PASS_STATUS,
            "evidence_admissibility_status": FAIL_STATUS,
            "evidence_admissible": False,
            "policy_threshold_status": PASS_STATUS,
            "walk_forward_status": PASS_STATUS,
            "out_of_sample_status": PASS_STATUS,
            "monte_carlo_status": PASS_STATUS,
            "stress_status": PASS_STATUS,
            "parameter_sensitivity_status": PASS_STATUS,
            "economic_validity_offline_gate_pass": False,
        },
    }
    if case_name == "nondeterministic_repeated_execution":
        ctx = build_lead_lag_promotion_gate_precheck_context_v0(
            versioned_binding=versioned_binding,
        )
        first = evaluate_promotion_gate_from_context_v0(ctx)
        second = evaluate_promotion_gate_from_context_v0(ctx)
        deterministic = (
            first.evaluation_digest == second.evaluation_digest
            and first.promotion_candidate_status == second.promotion_candidate_status
            and first.reason_codes == second.reason_codes
        )
        return {
            "case": case_name,
            "fail_closed": not deterministic or not first.eligible_for_promotion_candidate,
            "eligible_for_promotion_candidate": first.eligible_for_promotion_candidate,
            "deterministic": deterministic,
            "reason_codes": list(first.reason_codes),
        }

    ctx = build_lead_lag_promotion_gate_precheck_context_v0(
        versioned_binding=versioned_binding,
        overrides=overrides_map.get(case_name, {}),
    )
    gate_result = evaluate_promotion_gate_from_context_v0(ctx)
    fail_closed = not gate_result.eligible_for_promotion_candidate
    expected_reasons: dict[str, tuple[str, ...]] = {
        "missing_economic_evidence": (REASON_ECONOMIC_EVIDENCE_MISSING,),
        "inadmissible_evidence": (REASON_ECONOMIC_EVIDENCE_INADMISSIBLE,),
        "economic_gate_fail": (REASON_ECONOMIC_VALIDITY_NOT_PROVEN,),
        "missing_robustness_evidence": (
            f"{REASON_REQUIRED_INPUT_MISSING}:walk_forward_status",
            f"{REASON_REQUIRED_STATUS_UNKNOWN}:robustness_status",
        ),
        "malformed_evidence": tuple(),
        "unsupported_status": (f"{REASON_REQUIRED_STATUS_UNKNOWN}:economic_validity_status",),
        "legacy_confidence_only_bypass": (REASON_CONFIDENCE_SCORE_ONLY,),
        "direct_promotion_pass_overclaim": tuple(),
    }
    expected = expected_reasons.get(case_name, tuple())
    reason_ok = all(code in gate_result.reason_codes for code in expected) if expected else True
    if case_name == "direct_promotion_pass_overclaim":
        fail_closed = not gate_result.eligible_for_promotion_candidate
        reason_ok = not gate_result.economic_validity_pass or fail_closed
    return {
        "case": case_name,
        "fail_closed": fail_closed and reason_ok,
        "eligible_for_promotion_candidate": gate_result.eligible_for_promotion_candidate,
        "economic_validity_pass": gate_result.economic_validity_pass,
        "reason_codes": list(gate_result.reason_codes),
        "expected_reason_subset_present": reason_ok,
    }


def evaluate_negative_path_matrix_v0(
    *,
    versioned_binding: Mapping[str, Any],
) -> dict[str, Any]:
    matrix: dict[str, Any] = {}
    all_pass = True
    for case_name in NEGATIVE_PATH_CASES:
        item = evaluate_negative_path_case_v0(case_name, versioned_binding=versioned_binding)
        matrix[case_name] = item
        if not item.get("fail_closed"):
            all_pass = False
    return {
        "schema_version": "negative_path_matrix.v0",
        "cases": matrix,
        "negative_path_fail_closed_pass": all_pass,
    }


def evaluate_deterministic_double_execution_v0(
    *,
    versioned_binding: Mapping[str, Any],
    source_closeout_ref: str = DEFAULT_SOURCE_CLOSEOUT_REF,
    research_eval_decision_parity_suite_pass: bool = True,
) -> tuple[bool, dict[str, Any]]:
    ctx = build_lead_lag_promotion_gate_precheck_context_v0(
        versioned_binding=versioned_binding,
        source_closeout_ref=source_closeout_ref,
        research_eval_decision_parity_suite_pass=research_eval_decision_parity_suite_pass,
    )
    first = evaluate_promotion_gate_from_context_v0(ctx)
    second = evaluate_promotion_gate_from_context_v0(ctx)
    first_norm = normalize_gate_result_v0(first)
    second_norm = normalize_gate_result_v0(second)
    comparable_keys = (
        "promotion_candidate_status",
        "eligible_for_promotion_candidate",
        "reason_codes",
        "evaluation_digest",
        "economic_validity_pass",
        "robustness_pass",
        "evidence_admissible",
    )
    parity = all(first_norm[key] == second_norm[key] for key in comparable_keys)
    return parity, {
        "first_evaluation_digest": first.evaluation_digest,
        "second_evaluation_digest": second.evaluation_digest,
        "parity": parity,
    }


def evaluate_lead_lag_promotion_economic_gate_precheck_v0(
    *,
    versioned_binding: Mapping[str, Any],
    source_closeout_ref: str = DEFAULT_SOURCE_CLOSEOUT_REF,
    research_eval_decision_parity_suite_pass: bool = True,
) -> LeadLagPromotionGatePrecheckResultV0:
    ctx = build_lead_lag_promotion_gate_precheck_context_v0(
        versioned_binding=versioned_binding,
        source_closeout_ref=source_closeout_ref,
        research_eval_decision_parity_suite_pass=research_eval_decision_parity_suite_pass,
    )
    structural_ok, structural_reasons = validate_structural_gate_input_binding_v0(ctx)
    gate_result = evaluate_promotion_gate_from_context_v0(ctx)
    normalized = normalize_gate_result_v0(gate_result)
    field_parity = gate_decision_field_parity_ok_v0(gate_result)
    reason_parity = gate_reason_code_parity_ok_v0(result=gate_result)
    order_parity = gate_decision_order_parity_ok_v0(gate_result)
    deterministic_ok, deterministic_payload = evaluate_deterministic_double_execution_v0(
        versioned_binding=versioned_binding,
        source_closeout_ref=source_closeout_ref,
        research_eval_decision_parity_suite_pass=research_eval_decision_parity_suite_pass,
    )
    negative_matrix = evaluate_negative_path_matrix_v0(versioned_binding=versioned_binding)
    negative_ok = bool(negative_matrix["negative_path_fail_closed_pass"])
    confidence_ctx = build_lead_lag_promotion_gate_precheck_context_v0(
        versioned_binding=versioned_binding,
        overrides={"promotion_basis_confidence_only": True},
    )
    confidence_result = evaluate_promotion_gate_from_context_v0(confidence_ctx)
    legacy_confidence_reachable = (
        confidence_result.eligible_for_promotion_candidate
        and REASON_CONFIDENCE_SCORE_ONLY not in confidence_result.reason_codes
    )

    reason_codes: list[str] = list(structural_reasons)
    if not field_parity:
        reason_codes.append("gate_decision_field_parity_failed")
    if not reason_parity:
        reason_codes.append("gate_reason_code_parity_failed")
    if not order_parity:
        reason_codes.append("gate_decision_order_parity_failed")
    if not deterministic_ok:
        reason_codes.append("deterministic_double_execution_failed")
    if not negative_ok:
        reason_codes.append("negative_path_fail_closed_failed")

    precheck_complete = (
        structural_ok
        and field_parity
        and reason_parity
        and order_parity
        and deterministic_ok
        and negative_ok
        and not legacy_confidence_reachable
        and not gate_result.eligible_for_promotion_candidate
        and not gate_result.economic_validity_pass
    )

    input_binding = {
        "strategy_id": ctx.strategy_id,
        "strategy_version": ctx.strategy_version,
        "candidate_id": ctx.candidate_id,
        "source_closeout_ref": ctx.source_closeout_ref,
        "research_eval_decision_parity_suite_pass": ctx.research_eval_decision_parity_suite_pass,
        "config_digest": ctx.config_digest,
        "implementation_digest": ctx.implementation_digest,
        "evidence_manifest_digest": ctx.evidence_manifest_digest,
        "economic_viability_evidence_ref": ctx.economic_viability_evidence_ref,
        "system_economic_evidence_admissible": False,
        "economic_evaluation_executed": False,
        "deterministic_execution": deterministic_payload,
    }

    return LeadLagPromotionGatePrecheckResultV0(
        status=(
            PrecheckTerminalStatus.PRECHECK_COMPLETE
            if precheck_complete
            else PrecheckTerminalStatus.FAIL_CLOSED
        ),
        precheck_complete=precheck_complete,
        promotion_economic_gate_v1_real_owner_executed=True,
        structural_gate_input_binding_pass=structural_ok,
        gate_decision_field_parity_pass=field_parity,
        gate_reason_code_parity_pass=reason_parity,
        gate_decision_order_parity_pass=order_parity,
        deterministic_double_execution_pass=deterministic_ok,
        negative_path_fail_closed_pass=negative_ok,
        legacy_confidence_only_bypass_reachable=legacy_confidence_reachable,
        economic_evaluation_executed=False,
        economic_validity_offline_gate_pass=gate_result.economic_validity_pass,
        eligible_for_promotion_candidate=gate_result.eligible_for_promotion_candidate,
        system_economic_evidence_admissible=False,
        gate_result=gate_result,
        normalized_gate_result=normalized,
        input_binding=input_binding,
        reason_codes=tuple(reason_codes),
        authority_effect=AUTHORITY_EFFECT_NONE,
        runtime_effect=AUTHORITY_EFFECT_NONE,
    )


def materialize_promotion_gate_precheck_contract_v0() -> dict[str, Any]:
    return {
        "schema_version": "promotion_gate_precheck_contract.v0",
        "contract_version": CONTRACT_VERSION,
        "contract_owner": CONTRACT_OWNER,
        "contract_module": CONTRACT_MODULE,
        "operator_go": OPERATOR_GO,
        "allowed_operator_gos": sorted(ALLOWED_OPERATOR_GOS),
        "canonical_promotion_gate_owner": CANONICAL_PROMOTION_GATE_OWNER,
        "canonical_promotion_gate_policy_version": CANONICAL_PROMOTION_GATE_POLICY_VERSION,
        "canonical_promotion_gate_callable": CANONICAL_PROMOTION_GATE_CALLABLE,
        "promotion_gate_schema": promotion_economic_gate_schema_v1(),
        "required_gate_result_fields": list(REQUIRED_GATE_RESULT_FIELDS),
        "negative_path_cases": list(NEGATIVE_PATH_CASES),
        "default_source_closeout_ref": DEFAULT_SOURCE_CLOSEOUT_REF,
        "offline_only": True,
        "economic_evaluation_executed": False,
        "system_economic_evidence_admissible": False,
        "full_canonical_chain_wired": False,
        "backtest_runtime_decision_parity_pass": False,
        "authority_effect": AUTHORITY_EFFECT_NONE,
        "runtime_effect": AUTHORITY_EFFECT_NONE,
        "reuse_decision": "REUSE_WITH_NARROW_ADAPTER",
    }


def load_precheck_config_v0(repo_root: Path) -> dict[str, Any]:
    path = repo_root / CONFIG_REL_PATH
    if not path.is_file():
        return materialize_promotion_gate_precheck_contract_v0()
    return json.loads(path.read_text(encoding="utf-8"))


def precheck_result_to_dict(result: LeadLagPromotionGatePrecheckResultV0) -> dict[str, Any]:
    return {
        "status": result.status.value,
        "precheck_complete": result.precheck_complete,
        "promotion_economic_gate_v1_real_owner_executed": (
            result.promotion_economic_gate_v1_real_owner_executed
        ),
        "structural_gate_input_binding_pass": result.structural_gate_input_binding_pass,
        "gate_decision_field_parity_pass": result.gate_decision_field_parity_pass,
        "gate_reason_code_parity_pass": result.gate_reason_code_parity_pass,
        "gate_decision_order_parity_pass": result.gate_decision_order_parity_pass,
        "deterministic_double_execution_pass": result.deterministic_double_execution_pass,
        "negative_path_fail_closed_pass": result.negative_path_fail_closed_pass,
        "legacy_confidence_only_bypass_reachable": result.legacy_confidence_only_bypass_reachable,
        "economic_evaluation_executed": result.economic_evaluation_executed,
        "economic_validity_offline_gate_pass": result.economic_validity_offline_gate_pass,
        "eligible_for_promotion_candidate": result.eligible_for_promotion_candidate,
        "system_economic_evidence_admissible": result.system_economic_evidence_admissible,
        "normalized_gate_result": result.normalized_gate_result,
        "input_binding": result.input_binding,
        "reason_codes": list(result.reason_codes),
        "authority_effect": result.authority_effect,
        "runtime_effect": result.runtime_effect,
    }


def build_input_binding_matrix_v0(
    *,
    versioned_binding: Mapping[str, Any],
) -> dict[str, Any]:
    ctx = build_lead_lag_promotion_gate_precheck_context_v0(versioned_binding=versioned_binding)
    structural_ok, structural_reasons = validate_structural_gate_input_binding_v0(ctx)
    gate_input = build_promotion_gate_input_v0(ctx)
    return {
        "schema_version": "input_binding_matrix.v0",
        "structural_gate_input_binding_pass": structural_ok,
        "structural_reason_codes": list(structural_reasons),
        "binding_fields": extract_binding_gate_fields_v0(versioned_binding),
        "gate_input_evaluation_dict": gate_input.to_evaluation_dict(),
    }


def run_promotion_economic_gate_precheck_dispatch_v0(
    *,
    repo_root: Path,
    versioned_binding: Mapping[str, Any] | None = None,
    source_closeout_ref: str = DEFAULT_SOURCE_CLOSEOUT_REF,
    research_eval_decision_parity_suite_pass: bool = True,
    operator_go: str = OPERATOR_GO,
) -> dict[str, Any]:
    if operator_go not in ALLOWED_OPERATOR_GOS:
        return {
            "dispatch_rc": 1,
            "promotion_economic_gate_precheck_complete": False,
            "reason_codes": ["unsupported_operator_go"],
        }
    from src.research.cross_sectional_futures_lead_lag_information_diffusion_v0_offline_economic_evaluation_execution_v0 import (
        load_versioned_hypothesis_binding_v0,
    )

    envelope = dict(versioned_binding or load_versioned_hypothesis_binding_v0(repo_root))
    result = evaluate_lead_lag_promotion_economic_gate_precheck_v0(
        versioned_binding=envelope,
        source_closeout_ref=source_closeout_ref,
        research_eval_decision_parity_suite_pass=research_eval_decision_parity_suite_pass,
    )
    contract = materialize_promotion_gate_precheck_contract_v0()
    return {
        "dispatch_rc": 0 if result.precheck_complete else 1,
        "operator_go": operator_go,
        "promotion_economic_gate_precheck_complete": result.precheck_complete,
        "promotion_economic_gate_v1_real_owner_executed": (
            result.promotion_economic_gate_v1_real_owner_executed
        ),
        "structural_gate_input_binding_pass": result.structural_gate_input_binding_pass,
        "gate_decision_field_parity_pass": result.gate_decision_field_parity_pass,
        "gate_reason_code_parity_pass": result.gate_reason_code_parity_pass,
        "gate_decision_order_parity_pass": result.gate_decision_order_parity_pass,
        "deterministic_double_execution_pass": result.deterministic_double_execution_pass,
        "negative_path_fail_closed_pass": result.negative_path_fail_closed_pass,
        "legacy_confidence_only_bypass_reachable": result.legacy_confidence_only_bypass_reachable,
        "economic_evaluation_executed": False,
        "economic_validity_offline_gate_pass": result.economic_validity_offline_gate_pass,
        "eligible_for_promotion_candidate": result.eligible_for_promotion_candidate,
        "system_economic_evidence_admissible": False,
        "full_canonical_chain_wired": False,
        "backtest_runtime_decision_parity_pass": False,
        "precheck": precheck_result_to_dict(result),
        "input_binding_matrix": build_input_binding_matrix_v0(versioned_binding=envelope),
        "negative_path_matrix": evaluate_negative_path_matrix_v0(versioned_binding=envelope),
        "contract": contract,
        "authority_effect": AUTHORITY_EFFECT_NONE,
        "runtime_effect": AUTHORITY_EFFECT_NONE,
    }
