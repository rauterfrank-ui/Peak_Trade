"""Post-no-pass metric materialization path activation binding ratification v0.

Deterministic materialization of versioned bindings (strategy_version=v3) for
trend_following, bollinger_bands, and momentum_1h addressing the
PATH_PRESENT_BUT_NOT_EXECUTED failure class. Reuses sparse-signal v2 research
bindings unchanged (no parameter rescue) and adds explicit metric materialization
path activation refs for later separate offline evaluation.

Binding ratification only — no economic evaluation, no runtime, no authority effect.
Operator GO: GO_POST_NO_PASS_METRIC_MATERIALIZATION_PATH_ACTIVATION_BINDING_RATIFICATION_V0
"""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.backtest.economic_viability_evidence_v1 import (
    ARTIFACT_FILENAME,
    ECONOMIC_VIABILITY_EVIDENCE_LAYER_VERSION,
)
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
from src.research.post_no_pass_sparse_signal_zero_trade_versioned_binding_completion_v0 import (
    CONFIG_REL_PATH as SPARSE_V2_BINDING_COMPLETION_REL,
    RESEARCH_CANDIDATES,
    STRATEGY_VERSION as SPARSE_V2_STRATEGY_VERSION,
)

PACKAGE_MARKER = "POST_NO_PASS_METRIC_MATERIALIZATION_PATH_ACTIVATION_BINDING_RATIFICATION_V0=true"

SCHEMA_VERSION = "post_no_pass_metric_materialization_path_activation_binding_ratification.v0"
COMPLETION_ID = "post_no_pass_metric_materialization_path_activation_binding_ratification_v0"
CONFIG_REL_PATH = "config/research/post_no_pass_metric_materialization_path_activation_binding_ratification_v0.json"
GOVERNANCE_REL_PATH = (
    "docs/governance/POST_NO_PASS_METRIC_MATERIALIZATION_PATH_ACTIVATION_BINDING_RATIFICATION_V0.md"
)
PARENT_SCOPE_DEFINITION_REL = (
    "config/research/"
    "post_no_pass_metric_materialization_diagnostics_derived_next_research_scope_definition_v0.json"
)
CANONICAL_SERIALIZATION_VERSION = "research_binding_completion_canonical_json_v1"

CONFIRM_GO = "GO_POST_NO_PASS_METRIC_MATERIALIZATION_PATH_ACTIVATION_BINDING_RATIFICATION_V0"
NEXT_EXECUTION_GO = (
    "GO_POST_NO_PASS_METRIC_MATERIALIZATION_PATH_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0"
)
NEXT_CANONICAL_STEP = "REQUEST_OPERATOR_GO_FOR_POST_NO_PASS_METRIC_MATERIALIZATION_PATH_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0"
SCOPE_CLASSIFICATION = "POST_NO_PASS_METRIC_MATERIALIZATION_PATH_ACTIVATION_BINDING_RATIFICATION_V0"
PROCESS_CLASSIFICATION = "METRIC_MATERIALIZATION_PATH_ACTIVATION_BINDING_RATIFICATION_ONLY_V0"
BINDING_CLASS = "METRIC_MATERIALIZATION_PATH_ACTIVATION_RESEARCH_V0"
STRATEGY_VERSION = "v3"
SPARSE_V2_FAILED_STRATEGY_VERSION = "v2"
PRIMARY_CAUSE = "PATH_PRESENT_BUT_NOT_EXECUTED"
FAILED_CANDIDATE_VERDICT = "EXECUTION_FAILED_FAIL_CLOSED"

BASELINE_HEAD = "61c6b7dbbd2e4bf97c57c1ae08679c2f1aa2e4f4"
BASELINE_PR = "4886"
PARENT_SCOPE_ID = (
    "POST_NO_PASS_METRIC_MATERIALIZATION_DIAGNOSTICS_DERIVED_NEXT_RESEARCH_SCOPE_DEFINITION_V0"
)

METRIC_MATERIALIZATION_PATH_REF = "scripts/ops/run_economic_viability_evidence_evaluation_v1.py"
METRIC_MATERIALIZATION_CONTRACT_REF = (
    "src/backtest/economic_viability_evidence_v1.py#economic_viability_evidence_v1"
)
MATERIALIZED_METRIC_SCHEMA_REF = f"{ARTIFACT_FILENAME}#{ECONOMIC_VIABILITY_EVIDENCE_LAYER_VERSION}"
PATH_ACTIVATION_BINDING_ID = "metric_materialization_path_activation_research_v0"
PATH_ACTIVATION_STATUS = "PATH_ACTIVATED_BOUND_NOT_EXECUTED"

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
PARAMETER_RESCUE_ALLOWED = False
THRESHOLD_LOWERING_ALLOWED = False
PATH_ACTIVATION_BINDING_RATIFIED = True

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
    "metric_materialization_path_ref",
    "metric_materialization_contract_ref",
    "materialized_metric_schema_ref",
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
            "module": "post_no_pass_metric_materialization_path_activation_binding_ratification_v0",
            "binding_class": BINDING_CLASS,
            "strategy_version": STRATEGY_VERSION,
            "schema_version": SCHEMA_VERSION,
            "path_activation_binding_id": PATH_ACTIVATION_BINDING_ID,
        }
    )


def build_metric_materialization_path_binding_v0() -> dict[str, Any]:
    return {
        "activation_status": PATH_ACTIVATION_STATUS,
        "artifact_filename": ARTIFACT_FILENAME,
        "binding_class": BINDING_CLASS,
        "contract_layer_version": ECONOMIC_VIABILITY_EVIDENCE_LAYER_VERSION,
        "execution_authorized_in_this_scope": False,
        "materialization_path_activation": True,
        "materialized_metric_schema_ref": MATERIALIZED_METRIC_SCHEMA_REF,
        "metric_materialization_contract_ref": METRIC_MATERIALIZATION_CONTRACT_REF,
        "metric_materialization_path_ref": METRIC_MATERIALIZATION_PATH_REF,
        "path_activation_binding_id": PATH_ACTIVATION_BINDING_ID,
        "path_activation_binding_version": "v0",
        "primary_cause_addressed": PRIMARY_CAUSE,
        "required_materialized_fields": [
            "trade_count",
            "net_return",
            "sharpe",
            "profit_factor",
            "walk_forward_results",
            "monte_carlo_results",
            "stress_results",
            "economic_validity_verdict",
        ],
        "runner_owner": METRIC_MATERIALIZATION_PATH_REF,
    }


def _load_sparse_v2_candidate(
    sparse_v2_completion: Mapping[str, Any],
    strategy_id: str,
) -> dict[str, Any]:
    for candidate in sparse_v2_completion.get("candidates", ()):
        if isinstance(candidate, Mapping) and candidate.get("strategy_id") == strategy_id:
            return dict(candidate)
    raise KeyError(f"missing sparse_v2 candidate: {strategy_id}")


def materialize_path_activation_candidate_v0(
    *,
    strategy_id: str,
    sparse_v2_completion: Mapping[str, Any],
    path_binding: Mapping[str, Any],
    implementation_digest: str,
) -> dict[str, Any]:
    sparse_v2 = _load_sparse_v2_candidate(sparse_v2_completion, strategy_id)
    candidate: dict[str, Any] = {
        "binding_class": BINDING_CLASS,
        "binding_status": BINDING_STATUS_READY_FOR_EVAL_RATIFICATION,
        "canonical_candidate_identifier": canonical_candidate_identifier(
            strategy_id, STRATEGY_VERSION
        ),
        "canonical_trading_logic_binding_version": sparse_v2[
            "canonical_trading_logic_binding_version"
        ],
        "canonical_trading_logic_version": sparse_v2["canonical_trading_logic_version"],
        "config_digest": sparse_v2["config_digest"],
        "data_digest": sparse_v2["data_digest"],
        "dataset_binding": deepcopy(sparse_v2["dataset_binding"]),
        "dataset_provenance": deepcopy(sparse_v2.get("dataset_provenance", {})),
        "dataset_version": sparse_v2.get("dataset_version", "v1"),
        "economic_evaluation_authorized": False,
        "economic_policy_binding": deepcopy(sparse_v2["economic_policy_binding"]),
        "execution_model_binding": deepcopy(sparse_v2["execution_model_binding"]),
        "fee_model_binding": deepcopy(sparse_v2["fee_model_binding"]),
        "funding_model_binding": deepcopy(sparse_v2["funding_model_binding"]),
        "implementation_digest": implementation_digest,
        "instrument_binding": deepcopy(sparse_v2["instrument_binding"]),
        "materialized_metric_schema_ref": path_binding["materialized_metric_schema_ref"],
        "metric_materialization_contract_ref": path_binding["metric_materialization_contract_ref"],
        "metric_materialization_path_binding": dict(path_binding),
        "metric_materialization_path_ref": path_binding["metric_materialization_path_ref"],
        "operator_ratification_ref": COMPLETION_ID,
        "parameter_binding": deepcopy(sparse_v2["parameter_binding"]),
        "parameter_schema_version": sparse_v2["parameter_schema_version"],
        "path_activation_binding_id": PATH_ACTIVATION_BINDING_ID,
        "path_activation_status": PATH_ACTIVATION_STATUS,
        "period_binding": deepcopy(sparse_v2["period_binding"]),
        "period_digest": sparse_v2["period_digest"],
        "primary_cause_addressed": PRIMARY_CAUSE,
        "ratified": True,
        "slippage_model_binding": deepcopy(sparse_v2["slippage_model_binding"]),
        "source_sparse_v2_binding_ref": (
            f"{SPARSE_V2_BINDING_COMPLETION_REL}#{strategy_id}/{SPARSE_V2_STRATEGY_VERSION}"
        ),
        "source_sparse_v2_binding_semantic_digest": sparse_v2["binding_semantic_digest"],
        "source_config_ref": sparse_v2["source_config_ref"],
        "strategy_id": strategy_id,
        "strategy_params_digest": sparse_v2["strategy_params_digest"],
        "strategy_version": STRATEGY_VERSION,
        "substantially_differs_from_sparse_v2": True,
        "terminal_sparse_v2_verdict": FAILED_CANDIDATE_VERDICT,
    }
    candidate["binding_semantic_digest"] = compute_binding_semantic_digest_v0(candidate)
    return candidate


def materialize_post_no_pass_metric_materialization_path_activation_binding_ratification_v0(
    *,
    repo_root: Path,
    sparse_v2_completion: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if sparse_v2_completion is None:
        sparse_v2_path = repo_root / SPARSE_V2_BINDING_COMPLETION_REL
        sparse_v2_completion = json.loads(sparse_v2_path.read_text(encoding="utf-8"))

    implementation_digest = compute_implementation_digest_v0()
    path_binding = build_metric_materialization_path_binding_v0()
    candidates = [
        materialize_path_activation_candidate_v0(
            strategy_id=strategy_id,
            sparse_v2_completion=sparse_v2_completion,
            path_binding=path_binding,
            implementation_digest=implementation_digest,
        )
        for strategy_id in RESEARCH_CANDIDATES
    ]

    completion_body: dict[str, Any] = {
        "artifact_kind": "post_no_pass_metric_materialization_path_activation_binding_ratification",
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
            "SAME_BINDING_RETRY",
            "UNCHANGED_BINDING_RETRY",
            "PARAMETER_OPTIMIZATION",
            "PARAMETER_RESCUE",
            "THRESHOLD_LOWERING",
            "RESULT_RESCUE",
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
        ],
        "candidates": candidates,
        "canonical_serialization_version": CANONICAL_SERIALIZATION_VERSION,
        "completion_id": COMPLETION_ID,
        "economic_evaluation_authorized": ECONOMIC_EVALUATION_AUTHORIZED,
        "economic_evaluation_executed": ECONOMIC_EVALUATION_EXECUTED,
        "evaluation_executed": EVALUATION_EXECUTED,
        "evidence_class_id": SCOPE_CLASSIFICATION,
        "failed_candidate_verdict": FAILED_CANDIDATE_VERDICT,
        "failed_candidates": list(RESEARCH_CANDIDATES),
        "fleet_id": FLEET_ID,
        "fleet_version": FLEET_VERSION,
        "futures_only": FUTURES_ONLY,
        "go_token": CONFIRM_GO,
        "go_token_consumed": True,
        "governance_ref": GOVERNANCE_REL_PATH,
        "implementation_digest": implementation_digest,
        "live_authorized": False,
        "metric_materialization_path_binding": path_binding,
        "monte_carlo_executed": MONTE_CARLO_EXECUTED,
        "no_evaluation_authority": True,
        "no_promotion_authority": True,
        "no_runtime_authority": True,
        "non_authorizing": True,
        "offline_only": True,
        "order_effect": ORDER_EFFECT,
        "parameter_rescue_allowed": PARAMETER_RESCUE_ALLOWED,
        "parent_scope_id": PARENT_SCOPE_ID,
        "parent_scope_ref": PARENT_SCOPE_DEFINITION_REL,
        "path_activation_binding_ratified": PATH_ACTIVATION_BINDING_RATIFIED,
        "primary_cause": PRIMARY_CAUSE,
        "process_classification": PROCESS_CLASSIFICATION,
        "promotion_eligible": False,
        "required_binding_fields": list(REQUIRED_BINDING_FIELDS),
        "required_next_go_for_execution": NEXT_EXECUTION_GO,
        "research_hypothesis": (
            "PATH_PRESENT_BUT_NOT_EXECUTED_REQUIRES_METRIC_MATERIALIZATION_PATH_ACTIVATION_BINDING_NOT_UNCHANGED_V2_RETRY"
        ),
        "runtime_effect": RUNTIME_EFFECT,
        "runtime_rewire_admissible": RUNTIME_REWIRE_ADMISSIBLE,
        "same_binding_retry_allowed": SAME_BINDING_RETRY_ALLOWED,
        "schema_version": SCHEMA_VERSION,
        "scope_classification": SCOPE_CLASSIFICATION,
        "source_sparse_v2_binding_completion_ref": SPARSE_V2_BINDING_COMPLETION_REL,
        "source_sparse_v2_binding_completion_digest": str(
            sparse_v2_completion.get("completion_digest", "")
        ),
        "status": "PATH_ACTIVATION_BINDING_RATIFICATION_COMPLETE_NOT_EXECUTED",
        "strategy_version": STRATEGY_VERSION,
        "stress_executed": STRESS_EXECUTED,
        "terminal_negative_evidence_unchanged": True,
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
    return tuple(missing)


def validate_post_no_pass_metric_materialization_path_activation_binding_ratification_v0(
    completion: Any,
    *,
    sparse_v2_completion: Mapping[str, Any] | None = None,
) -> BindingValidationResultV0:
    reasons: list[str] = []
    if not isinstance(completion, Mapping):
        return BindingValidationResultV0(
            verdict=ValidationVerdict.REJECTED,
            fail_reasons=("COMPLETION_NOT_OBJECT",),
        )

    if completion.get("schema_version") != SCHEMA_VERSION:
        reasons.append("SCHEMA_VERSION_MISMATCH")
    if completion.get("go_token") != CONFIRM_GO:
        reasons.append("GO_TOKEN_MISMATCH")
    if completion.get("path_activation_binding_ratified") is not True:
        reasons.append("PATH_ACTIVATION_BINDING_RATIFIED_MUST_BE_TRUE")
    if completion.get("economic_evaluation_authorized") is not False:
        reasons.append("ECONOMIC_EVALUATION_MUST_BE_FALSE")
    if completion.get("economic_evaluation_executed") is not False:
        reasons.append("ECONOMIC_EVALUATION_EXECUTED_MUST_BE_FALSE")
    if completion.get("evaluation_executed") is not False:
        reasons.append("EVALUATION_EXECUTED_MUST_BE_FALSE")
    if completion.get("backtest_executed") is not False:
        reasons.append("BACKTEST_EXECUTED_MUST_BE_FALSE")
    if completion.get("walk_forward_executed") is not False:
        reasons.append("WALK_FORWARD_EXECUTED_MUST_BE_FALSE")
    if completion.get("monte_carlo_executed") is not False:
        reasons.append("MONTE_CARLO_EXECUTED_MUST_BE_FALSE")
    if completion.get("stress_executed") is not False:
        reasons.append("STRESS_EXECUTED_MUST_BE_FALSE")
    if completion.get("runtime_rewire_admissible") is not False:
        reasons.append("RUNTIME_REWIRE_MUST_BE_FALSE")
    if completion.get("same_binding_retry_allowed") is not False:
        reasons.append("SAME_BINDING_RETRY_MUST_BE_FALSE")
    if completion.get("parameter_rescue_allowed") is not False:
        reasons.append("PARAMETER_RESCUE_MUST_BE_FALSE")
    if completion.get("primary_cause") != PRIMARY_CAUSE:
        reasons.append("PRIMARY_CAUSE_MISMATCH")

    expected_digest = compute_completion_digest_v0(completion)
    if completion.get("completion_digest") != expected_digest:
        reasons.append("COMPLETION_DIGEST_MISMATCH")

    candidates = completion.get("candidates")
    if not isinstance(candidates, list) or len(candidates) != len(RESEARCH_CANDIDATES):
        reasons.append("CANDIDATE_COUNT_MISMATCH")
    else:
        seen: set[str] = set()
        for candidate in candidates:
            if not isinstance(candidate, Mapping):
                reasons.append("CANDIDATE_NOT_OBJECT")
                continue
            strategy_id = str(candidate.get("strategy_id", ""))
            if strategy_id in seen:
                reasons.append(f"DUPLICATE_CANDIDATE:{strategy_id}")
            seen.add(strategy_id)
            if candidate.get("strategy_version") != STRATEGY_VERSION:
                reasons.append(f"WRONG_STRATEGY_VERSION:{strategy_id}")
            if candidate.get("substantially_differs_from_sparse_v2") is not True:
                reasons.append(f"SPARSE_V2_DELTA_REQUIRED:{strategy_id}")
            missing = _candidate_has_required_fields(candidate)
            if missing:
                reasons.append(f"MISSING_FIELDS:{strategy_id}:{','.join(missing)}")
            if candidate.get("metric_materialization_path_ref") != METRIC_MATERIALIZATION_PATH_REF:
                reasons.append(f"PATH_REF_MISMATCH:{strategy_id}")
            if (
                candidate.get("metric_materialization_contract_ref")
                != METRIC_MATERIALIZATION_CONTRACT_REF
            ):
                reasons.append(f"CONTRACT_REF_MISMATCH:{strategy_id}")
            if candidate.get("materialized_metric_schema_ref") != MATERIALIZED_METRIC_SCHEMA_REF:
                reasons.append(f"SCHEMA_REF_MISMATCH:{strategy_id}")
            expected_semantic = compute_binding_semantic_digest_v0(candidate)
            if candidate.get("binding_semantic_digest") != expected_semantic:
                reasons.append(f"BINDING_SEMANTIC_DIGEST_MISMATCH:{strategy_id}")

            if sparse_v2_completion is not None:
                sparse_v2 = _load_sparse_v2_candidate(sparse_v2_completion, strategy_id)
                if candidate.get("binding_semantic_digest") == sparse_v2.get(
                    "binding_semantic_digest"
                ):
                    reasons.append(f"UNCHANGED_SPARSE_V2_BINDING:{strategy_id}")

    if sparse_v2_completion is None and completion.get(
        "source_sparse_v2_binding_completion_digest"
    ):
        reasons.append("SPARSE_V2_COMPLETION_NOT_PROVIDED_FOR_CROSSCHECK")

    verdict = ValidationVerdict.ACCEPTED if not reasons else ValidationVerdict.REJECTED
    return BindingValidationResultV0(verdict=verdict, fail_reasons=tuple(reasons))
