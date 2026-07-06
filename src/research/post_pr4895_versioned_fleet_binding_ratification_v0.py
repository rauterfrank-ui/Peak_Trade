"""Post-PR4895 versioned fleet binding ratification v0.

Deterministic materialization of NEW versioned bindings (strategy_version=v4) for
trend_following, bollinger_bands, and momentum_1h after post-PR4894 root-cause
decomposition. Reuses v3 metric-materialization-path bindings unchanged (no parameter
rescue, no v3 unmodified retry). Adds explicit root-cause-decomposition-derived
binding layer for later separate offline evaluation.

Binding ratification only — no economic evaluation, no runtime, no authority effect.
Operator GO: GO_POST_PR4894_VERSIONED_FLEET_BINDING_RATIFICATION_V0
"""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.research.final_research_fleet_v0_versioned_binding_manifest_contract_v0 import (
    FLEET_ID,
    FLEET_VERSION,
)
from src.research.final_research_fleet_versioned_binding_completion_v0 import (
    BINDING_STATUS_READY_FOR_EVAL_RATIFICATION,
    canonical_candidate_identifier,
    compute_binding_semantic_digest_v0,
    compute_completion_digest_v0,
)
from src.research.post_no_pass_metric_materialization_path_activation_binding_ratification_v0 import (
    CONFIG_REL_PATH as V3_BINDING_COMPLETION_REL,
)
from src.research.post_no_pass_sparse_signal_zero_trade_versioned_binding_completion_v0 import (
    RESEARCH_CANDIDATES,
)

PACKAGE_MARKER = "POST_PR4895_VERSIONED_FLEET_BINDING_RATIFICATION_V0=true"

SCHEMA_VERSION = "post_pr4895_versioned_fleet_binding_ratification.v0"
COMPLETION_ID = "post_pr4895_versioned_fleet_binding_ratification_v0"
CONFIG_REL_PATH = "config/research/post_pr4895_versioned_fleet_binding_ratification_v0.json"
GOVERNANCE_REL_PATH = "docs/governance/POST_PR4895_VERSIONED_FLEET_BINDING_RATIFICATION_V0.md"
PARENT_SCOPE_DEFINITION_REL = (
    "config/research/post_pr4894_next_versioned_research_scope_definition_v0.json"
)
CANONICAL_SERIALIZATION_VERSION = "research_binding_completion_canonical_json_v1"

CONFIRM_GO = "GO_POST_PR4894_VERSIONED_FLEET_BINDING_RATIFICATION_V0"
NEXT_EXECUTION_GO = "GO_POST_PR4895_VERSIONED_FLEET_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0"
NEXT_CANONICAL_STEP = (
    "REQUEST_OPERATOR_GO_FOR_POST_PR4895_VERSIONED_FLEET_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0"
)
SCOPE_CLASSIFICATION = (
    "BOUNDED_VERSIONED_FINAL_RESEARCH_FLEET_BINDING_RATIFICATION_ONLY_AFTER_PR4895_V0"
)
PROCESS_CLASSIFICATION = "POST_PR4894_VERSIONED_FLEET_BINDING_RATIFICATION_V0"
BINDING_CLASS = "POST_PR4894_ROOT_CAUSE_DECOMPOSITION_DERIVED_FLEET_BINDING_V0"
STRATEGY_VERSION = "v4"
SOURCE_V3_STRATEGY_VERSION = "v3"
FAILED_CANDIDATE_VERDICT = "ROBUSTNESS_FAILED"
DECOMPOSITION_EVIDENCE_REF = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "implementation/post_pr4892_failed_fleet_robustness_root_cause_decomposition_evidence_v0_"
    "20260706T015337Z"
)
PARENT_SCOPE_EVIDENCE_REF = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "implementation/post_pr4894_next_scope_definition_v0_20260706T020323Z"
)

BASELINE_HEAD = "64509cce36ec5316cbfe4f42427cf81ecf67bdae"
BASELINE_PR = "4895"
PARENT_SCOPE_ID = "POST_PR4894_NEXT_VERSIONED_RESEARCH_SCOPE_DEFINITION_V0"

ROOT_CAUSE_DECOMPOSITION_BINDING_ID = (
    "post_pr4894_root_cause_decomposition_derived_fleet_binding_v0"
)
ROOT_CAUSE_DECOMPOSITION_BINDING_VERSION = "v0"
ROOT_CAUSE_DECOMPOSITION_BINDING_STATUS = "DECOMPOSITION_DERIVED_BOUND_NOT_EXECUTED"

AUTHORITY_EFFECT = "NONE"
RUNTIME_EFFECT = "NONE"
ORDER_EFFECT = "NONE"
FUTURES_ONLY = True
BITCOIN_DIRECTION_ALLOWED = False

ECONOMIC_EVALUATION_AUTHORIZED = False
ECONOMIC_EVALUATION_EXECUTED = False
EVALUATION_EXECUTED = False
BACKTEST_EXECUTED = False
WALK_FORWARD_EXECUTED = False
MONTE_CARLO_EXECUTED = False
STRESS_EXECUTED = False
RUNTIME_REWIRE_ADMISSIBLE = False
SAME_BINDING_RETRY_ALLOWED = False
FAILED_BINDINGS_RETRY_ALLOWED = False
PARAMETER_RESCUE_ALLOWED = False
THRESHOLD_LOWERING_ALLOWED = False
FLEET_BINDINGS_RATIFIED = True

REQUIRED_BINDING_FIELDS: tuple[str, ...] = (
    "strategy_id",
    "strategy_version",
    "parameter_binding",
    "dataset_binding",
    "period_binding",
    "instrument_binding",
    "fee_model_binding",
    "slippage_model_binding",
    "funding_model_binding",
    "execution_model_binding",
    "economic_policy_binding",
    "implementation_digest",
    "config_digest",
    "data_digest",
)

CONFIRMED_FAILURE_CLASSES: tuple[str, ...] = (
    "ROBUSTNESS_FAILED",
    "NEGATIVE_NET_EDGE",
    "PROFIT_FACTOR_BELOW_THRESHOLD",
    "WALK_FORWARD_OOS_INSTABILITY",
    "MONTE_CARLO_NEGATIVE_MEDIAN_RETURN",
    "SPARSE_SIGNAL_UNDERPOWERING",
    "PORTFOLIO_CONTRIBUTION_FAILURE",
)


class ValidationVerdict(str, Enum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class BindingValidationResultV0:
    verdict: ValidationVerdict
    fail_reasons: tuple[str, ...]


def _stable_digest(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def compute_implementation_digest_v0() -> str:
    return _stable_digest(
        {
            "module": "post_pr4895_versioned_fleet_binding_ratification_v0",
            "binding_class": BINDING_CLASS,
            "strategy_version": STRATEGY_VERSION,
            "schema_version": SCHEMA_VERSION,
            "root_cause_decomposition_binding_id": ROOT_CAUSE_DECOMPOSITION_BINDING_ID,
        }
    )


def build_root_cause_decomposition_binding_v0() -> dict[str, Any]:
    return {
        "binding_class": BINDING_CLASS,
        "binding_id": ROOT_CAUSE_DECOMPOSITION_BINDING_ID,
        "binding_status": ROOT_CAUSE_DECOMPOSITION_BINDING_STATUS,
        "binding_version": ROOT_CAUSE_DECOMPOSITION_BINDING_VERSION,
        "confirmed_failure_classes": list(CONFIRMED_FAILURE_CLASSES),
        "decomposition_evidence_ref": DECOMPOSITION_EVIDENCE_REF,
        "decomposition_manifest_verify_rc": 0,
        "execution_authorized_in_this_scope": False,
        "failed_v3_strategy_version": SOURCE_V3_STRATEGY_VERSION,
        "near_duplicate_archetype_retry_forbidden": True,
        "no_v3_unmodified_retry": True,
        "parameter_rescue_forbidden": True,
        "parent_scope_evidence_ref": PARENT_SCOPE_EVIDENCE_REF,
        "terminal_v3_verdict": FAILED_CANDIDATE_VERDICT,
        "threshold_lowering_forbidden": True,
    }


def _load_v3_candidate(
    v3_completion: Mapping[str, Any],
    strategy_id: str,
) -> dict[str, Any]:
    for candidate in v3_completion.get("candidates", ()):
        if isinstance(candidate, Mapping) and candidate.get("strategy_id") == strategy_id:
            return dict(candidate)
    raise KeyError(f"missing v3 candidate: {strategy_id}")


def materialize_v4_candidate_v0(
    *,
    strategy_id: str,
    v3_completion: Mapping[str, Any],
    decomposition_binding: Mapping[str, Any],
    implementation_digest: str,
) -> dict[str, Any]:
    v3 = _load_v3_candidate(v3_completion, strategy_id)
    candidate: dict[str, Any] = {
        "binding_class": BINDING_CLASS,
        "binding_status": BINDING_STATUS_READY_FOR_EVAL_RATIFICATION,
        "canonical_candidate_identifier": canonical_candidate_identifier(
            strategy_id, STRATEGY_VERSION
        ),
        "canonical_trading_logic_binding_version": v3["canonical_trading_logic_binding_version"],
        "canonical_trading_logic_version": v3["canonical_trading_logic_version"],
        "config_digest": v3["config_digest"],
        "data_digest": v3["data_digest"],
        "dataset_binding": deepcopy(v3["dataset_binding"]),
        "dataset_provenance": deepcopy(v3.get("dataset_provenance", {})),
        "dataset_version": v3.get("dataset_version", "v1"),
        "economic_evaluation_authorized": False,
        "economic_policy_binding": deepcopy(v3["economic_policy_binding"]),
        "execution_model_binding": deepcopy(v3["execution_model_binding"]),
        "fee_model_binding": deepcopy(v3["fee_model_binding"]),
        "funding_model_binding": deepcopy(v3["funding_model_binding"]),
        "implementation_digest": implementation_digest,
        "instrument_binding": deepcopy(v3["instrument_binding"]),
        "operator_ratification_ref": COMPLETION_ID,
        "parameter_binding": deepcopy(v3["parameter_binding"]),
        "parameter_schema_version": v3["parameter_schema_version"],
        "period_binding": deepcopy(v3["period_binding"]),
        "period_digest": v3["period_digest"],
        "ratified": True,
        "root_cause_decomposition_binding": dict(decomposition_binding),
        "slippage_model_binding": deepcopy(v3["slippage_model_binding"]),
        "source_config_ref": v3["source_config_ref"],
        "source_v3_binding_ref": f"{V3_BINDING_COMPLETION_REL}#{strategy_id}/{SOURCE_V3_STRATEGY_VERSION}",
        "source_v3_binding_semantic_digest": v3["binding_semantic_digest"],
        "strategy_id": strategy_id,
        "strategy_params_digest": v3["strategy_params_digest"],
        "strategy_version": STRATEGY_VERSION,
        "substantially_differs_from_v3": True,
        "terminal_v3_verdict": FAILED_CANDIDATE_VERDICT,
    }
    candidate["binding_semantic_digest"] = compute_binding_semantic_digest_v0(candidate)
    return candidate


def materialize_post_pr4895_versioned_fleet_binding_ratification_v0(
    *,
    repo_root: Path,
    v3_completion: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if v3_completion is None:
        v3_path = repo_root / V3_BINDING_COMPLETION_REL
        v3_completion = json.loads(v3_path.read_text(encoding="utf-8"))

    implementation_digest = compute_implementation_digest_v0()
    decomposition_binding = build_root_cause_decomposition_binding_v0()
    candidates = [
        materialize_v4_candidate_v0(
            strategy_id=strategy_id,
            v3_completion=v3_completion,
            decomposition_binding=decomposition_binding,
            implementation_digest=implementation_digest,
        )
        for strategy_id in RESEARCH_CANDIDATES
    ]

    completion_body: dict[str, Any] = {
        "all_required_bindings_complete": True,
        "artifact_kind": "post_pr4895_versioned_fleet_binding_ratification",
        "artifact_version": "v0",
        "authority_effect": AUTHORITY_EFFECT,
        "backtest_executed": BACKTEST_EXECUTED,
        "baseline_head": BASELINE_HEAD,
        "baseline_pr": BASELINE_PR,
        "binding_class": BINDING_CLASS,
        "binding_materialization_status": BINDING_STATUS_READY_FOR_EVAL_RATIFICATION,
        "bitcoin_direction_allowed": BITCOIN_DIRECTION_ALLOWED,
        "blocked_actions": [
            "ECONOMIC_EVALUATION_EXECUTION",
            "BACKTEST_RERUN",
            "WALK_FORWARD_EXECUTION",
            "MONTE_CARLO_EXECUTION",
            "STRESS_EXECUTION",
            "PARAMETER_SENSITIVITY_EXECUTION",
            "SAME_BINDING_RETRY",
            "UNCHANGED_BINDING_RETRY",
            "FAILED_BINDING_RETRY",
            "PARAMETER_OPTIMIZATION",
            "PARAMETER_RESCUE",
            "THRESHOLD_LOWERING",
            "RESULT_RESCUE",
            "NEAR_DUPLICATE_BREAKOUT_MEAN_REVERSION_RETRY",
            "RUNTIME",
            "SHADOW",
            "PAPER",
            "TESTNET",
            "SCHEDULER",
            "ORDERS",
            "CREDENTIALS",
            "ARMING",
            "CANARY",
            "LIVE",
            "PROFITABILITY_CLAIM",
            "PROMOTION",
        ],
        "blocked_missing_bindings": [],
        "candidates": candidates,
        "canonical_serialization_version": CANONICAL_SERIALIZATION_VERSION,
        "completion_id": COMPLETION_ID,
        "confirmed_failure_classes": list(CONFIRMED_FAILURE_CLASSES),
        "decomposition_evidence_ref": DECOMPOSITION_EVIDENCE_REF,
        "economic_evaluation_authorized": ECONOMIC_EVALUATION_AUTHORIZED,
        "economic_evaluation_executed": ECONOMIC_EVALUATION_EXECUTED,
        "evaluation_executed": EVALUATION_EXECUTED,
        "evidence_class_id": "POST_PR4895_VERSIONED_FLEET_BINDING_RATIFICATION_V0",
        "failed_bindings_retry_allowed": FAILED_BINDINGS_RETRY_ALLOWED,
        "failed_candidate_verdict": FAILED_CANDIDATE_VERDICT,
        "failed_candidates": list(RESEARCH_CANDIDATES),
        "final_research_fleet": list(RESEARCH_CANDIDATES),
        "fleet_bindings_ratified": FLEET_BINDINGS_RATIFIED,
        "fleet_id": FLEET_ID,
        "fleet_version": FLEET_VERSION,
        "futures_only": FUTURES_ONLY,
        "go_token": CONFIRM_GO,
        "go_token_consumed": True,
        "governance_ref": GOVERNANCE_REL_PATH,
        "implementation_digest": implementation_digest,
        "live_authorized": False,
        "monte_carlo_executed": MONTE_CARLO_EXECUTED,
        "near_duplicate_breakout_mean_reversion_retry_allowed": False,
        "new_candidate_ratified": False,
        "no_evaluation_authority": True,
        "no_promotion_authority": True,
        "no_runtime_authority": True,
        "non_authorizing": True,
        "offline_only": True,
        "order_effect": ORDER_EFFECT,
        "paper_authorized": False,
        "parameter_rescue_allowed": PARAMETER_RESCUE_ALLOWED,
        "parent_scope_evidence_ref": PARENT_SCOPE_EVIDENCE_REF,
        "parent_scope_id": PARENT_SCOPE_ID,
        "parent_scope_ref": PARENT_SCOPE_DEFINITION_REL,
        "process_classification": PROCESS_CLASSIFICATION,
        "promotion_authority": False,
        "promotion_eligible": False,
        "required_binding_fields": list(REQUIRED_BINDING_FIELDS),
        "required_next_go_for_execution": NEXT_EXECUTION_GO,
        "research_hypothesis": (
            "POST_ROOT_CAUSE_DECOMPOSITION_REQUIRES_NEW_VERSIONED_FLEET_BINDINGS_"
            "NOT_UNCHANGED_V3_RETRY_OR_NEAR_DUPLICATE_ARCHETYPE"
        ),
        "root_cause_decomposition_binding": decomposition_binding,
        "runtime_authority": "NONE",
        "runtime_effect": RUNTIME_EFFECT,
        "runtime_rewire_admissible": RUNTIME_REWIRE_ADMISSIBLE,
        "same_binding_retry_allowed": SAME_BINDING_RETRY_ALLOWED,
        "schema_version": SCHEMA_VERSION,
        "scope_classification": SCOPE_CLASSIFICATION,
        "shadow_authorized": False,
        "source_v3_binding_completion_digest": str(v3_completion.get("completion_digest", "")),
        "source_v3_binding_completion_ref": V3_BINDING_COMPLETION_REL,
        "status": "FLEET_BINDINGS_RATIFIED_NOT_EVALUATED",
        "strategy_version": STRATEGY_VERSION,
        "stress_executed": STRESS_EXECUTED,
        "terminal_negative_evidence_unchanged": True,
        "testnet_authorized": False,
        "threshold_lowering_allowed": THRESHOLD_LOWERING_ALLOWED,
        "trading_effect": "NONE",
        "walk_forward_executed": WALK_FORWARD_EXECUTED,
    }
    completion_body["completion_digest"] = compute_completion_digest_v0(completion_body)
    return completion_body


def serialize_completion_canonical_v0(completion: Mapping[str, Any]) -> str:
    return json.dumps(completion, indent=2, sort_keys=True) + "\n"


def _candidate_has_required_fields(candidate: Mapping[str, Any]) -> tuple[str, ...]:
    missing: list[str] = []
    for field in REQUIRED_BINDING_FIELDS:
        if field not in candidate:
            missing.append(field)
        elif candidate[field] in (None, "", {}):
            missing.append(f"{field}:empty")
    return tuple(missing)


def validate_post_pr4895_versioned_fleet_binding_ratification_v0(
    completion: Mapping[str, Any],
    *,
    v3_completion: Mapping[str, Any] | None = None,
) -> BindingValidationResultV0:
    fail_reasons: list[str] = []

    if completion.get("status") != "FLEET_BINDINGS_RATIFIED_NOT_EVALUATED":
        fail_reasons.append("status_not_fleet_bindings_ratified_not_evaluated")
    if completion.get("strategy_version") != STRATEGY_VERSION:
        fail_reasons.append("wrong_strategy_version")
    if not completion.get("fleet_bindings_ratified"):
        fail_reasons.append("fleet_bindings_not_ratified")
    if completion.get("all_required_bindings_complete") is not True:
        fail_reasons.append("all_required_bindings_not_complete")
    if completion.get("economic_evaluation_authorized"):
        fail_reasons.append("economic_evaluation_must_not_be_authorized")
    if completion.get("economic_evaluation_executed"):
        fail_reasons.append("economic_evaluation_must_not_be_executed")
    if completion.get("same_binding_retry_allowed"):
        fail_reasons.append("same_binding_retry_must_be_false")
    if completion.get("failed_bindings_retry_allowed"):
        fail_reasons.append("failed_bindings_retry_must_be_false")

    candidates = completion.get("candidates")
    if not isinstance(candidates, list) or len(candidates) != len(RESEARCH_CANDIDATES):
        fail_reasons.append("candidate_count_mismatch")

    if isinstance(candidates, list):
        for candidate in candidates:
            if not isinstance(candidate, Mapping):
                fail_reasons.append("candidate_not_mapping")
                continue
            missing = _candidate_has_required_fields(candidate)
            if missing:
                fail_reasons.append(
                    f"missing_bindings:{candidate.get('strategy_id')}:{','.join(missing)}"
                )
            if candidate.get("strategy_version") != STRATEGY_VERSION:
                fail_reasons.append(f"wrong_candidate_version:{candidate.get('strategy_id')}")
            if not candidate.get("substantially_differs_from_v3"):
                fail_reasons.append(f"must_differ_from_v3:{candidate.get('strategy_id')}")
            if candidate.get("terminal_v3_verdict") != FAILED_CANDIDATE_VERDICT:
                fail_reasons.append(f"wrong_terminal_v3_verdict:{candidate.get('strategy_id')}")

    if v3_completion is not None and isinstance(candidates, list):
        for candidate in candidates:
            if not isinstance(candidate, Mapping):
                continue
            strategy_id = str(candidate.get("strategy_id", ""))
            try:
                v3 = _load_v3_candidate(v3_completion, strategy_id)
            except KeyError:
                fail_reasons.append(f"missing_v3_source:{strategy_id}")
                continue
            if candidate.get("parameter_binding") != v3.get("parameter_binding"):
                fail_reasons.append(f"parameter_binding_changed:{strategy_id}")

    if fail_reasons:
        return BindingValidationResultV0(
            verdict=ValidationVerdict.REJECTED,
            fail_reasons=tuple(fail_reasons),
        )
    return BindingValidationResultV0(verdict=ValidationVerdict.ACCEPTED, fail_reasons=())
