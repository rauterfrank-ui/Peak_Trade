"""Final Research Fleet offline economic evaluation scope ratification v0.

Deterministic, fail-closed ratification of a bounded offline-only economic
evaluation scope for trend_following/v1, bollinger_bands/v1, and momentum_1h/v1.

Ratifies evaluation contract, shared policies, admissible evaluation stages, and
fail-closed execution boundaries only. Does not execute economic evaluation,
backtest, walk-forward, Monte Carlo, stress, or parameter sensitivity.

ECONOMIC_EVALUATION_AUTHORIZED=true at scope level authorizes a later separate
offline execution GO only. ECONOMIC_EVALUATION_EXECUTED remains false.
"""

from __future__ import annotations

import hashlib
import json
import re
from copy import deepcopy
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.backtest.economic_validity_policy_v1 import ECONOMIC_VALIDITY_POLICY_VERSION
from src.research.final_research_fleet_v0_versioned_binding_manifest_contract_v0 import (
    FLEET_CANDIDATES,
    FLEET_ID,
    FLEET_VERSION,
    OPERATOR_RATIFICATION_REF,
    STEP31F_CONFIG_PATHS,
    load_step31f_evaluation_config_v0,
)
from src.research.final_research_fleet_versioned_binding_completion_v0 import (
    COMPLETION_ID,
    FAILED_HISTORICAL_CANDIDATES,
    ValidationVerdict as BindingValidationVerdict,
    canonical_candidate_identifier,
    compute_binding_semantic_digest_v0,
    validate_final_research_fleet_versioned_binding_completion_v0,
)

PACKAGE_MARKER = "FINAL_RESEARCH_FLEET_OFFLINE_ECONOMIC_EVALUATION_SCOPE_RATIFICATION_V0=true"

SCHEMA_VERSION = "final_research_fleet_offline_economic_evaluation_scope_ratification.v0"
RATIFICATION_ID = "final_research_fleet_offline_economic_evaluation_scope_ratification_v0"
RATIFICATION_VERSION = "v0"
CANONICAL_SERIALIZATION_VERSION = "research_scope_ratification_canonical_json_v1"

OPERATOR_SCOPE_RATIFICATION_REF = (
    "bounded_final_research_fleet_offline_economic_evaluation_scope_ratification_v0_"
    "20260703T050000Z"
)

AUTHORITY_EFFECT = "NONE"
RUNTIME_EFFECT = "NONE"
ORDER_EFFECT = "NONE"

FINAL_RESEARCH_FLEET_BINDING_READY = True
OFFLINE_ECONOMIC_EVALUATION_SCOPE_RATIFIED = True
ECONOMIC_EVALUATION_AUTHORIZED = True
ECONOMIC_EVALUATION_EXECUTED = False
ECONOMIC_VALIDITY_OFFLINE_GATE_PASS = False
RUNTIME_REWIRE_ADMISSIBLE = False
ALLOWED_AFTER_THIS_RATIFICATION = True

EVALUATION_AUTHORIZATION_STATUS = "AUTHORIZED_PENDING_SEPARATE_OFFLINE_EXECUTION_GO"
ECONOMIC_VALIDITY_STATUS = "NOT_EVALUATED"

EVIDENCE_SCHEMA_REF = "economic_viability_evidence_schema_v1.json"
EVIDENCE_MANIFEST_POLICY = "scripts.ops.primary_evidence_retention_v0"

FUTURES_ONLY = True
BITCOIN_DIRECTION_ALLOWED = False
SPOT_ALLOWED = False
SYNTHETIC_SPOT_ALLOWED = False

ALLOWED_EVALUATION_STAGES: tuple[str, ...] = (
    "OFFLINE_BACKTEST",
    "WALK_FORWARD",
    "MONTE_CARLO",
    "STRESS",
    "PARAMETER_SENSITIVITY",
    "ECONOMIC_VIABILITY_EVIDENCE_MATERIALIZATION",
)

PROHIBITED_ACTIONS: tuple[str, ...] = (
    "ECONOMIC_EVALUATION_EXECUTION",
    "BACKTEST_EXECUTION",
    "WALK_FORWARD_EXECUTION",
    "MONTE_CARLO_EXECUTION",
    "STRESS_EXECUTION",
    "PARAMETER_SENSITIVITY_EXECUTION",
    "RUNTIME_REWIRE",
    "RUNTIME",
    "SCHEDULER",
    "SHADOW",
    "PAPER",
    "TESTNET",
    "CANARY",
    "LIVE",
    "ADAPTER_SUBMISSION",
    "NETWORK_ORDER_PATH",
    "ORDERS",
    "CANCELS",
    "CREDENTIALS",
    "ARMING",
    "OPERATOR_LIMIT_CHANGE",
    "CORE_SYSTEM_CHANGE",
    "CANONICAL_TRADING_LOGIC_CHANGE",
    "MASTER_V2_CHANGE",
    "DOUBLE_PLAY_CHANGE",
    "SCOPE_LOGIC_CHANGE",
    "ENTRY_EXIT_REVERSAL_CHANGE",
    "RISK_SIZING_CHANGE",
    "SAFETY_KERNEL_CHANGE",
    "RECONCILIATION_CHANGE",
    "POLICY_THRESHOLD_RETROFIT",
    "FAILED_BINDING_RETRY",
    "CROSS_CANDIDATE_THRESHOLD_ABATEMENT",
    "IMPLICIT_ZERO_COST",
    "OUT_OF_SAMPLE_PARAMETER_OPTIMIZATION",
    "TRAINING_VALIDATION_OOS_LEAKAGE",
    "ECONOMIC_VALIDITY_WITHOUT_MANIFEST_EVIDENCE",
    "FLEET_AGGREGATION_CANDIDATE_FAILURE_MASKING",
)

FORBIDDEN_INSTRUMENT_TOKENS = frozenset(
    {"btc", "xbt", "bitcoin", "spot", "synthetic_spot", "synthetic-spot"}
)
_ABSOLUTE_PATH_PATTERN = re.compile(r"(^/|^\\\\|^[A-Za-z]:[/\\\\])")

REASON_UNKNOWN_SCHEMA_VERSION = "UNKNOWN_SCHEMA_VERSION"
REASON_RATIFICATION_NOT_OBJECT = "RATIFICATION_NOT_OBJECT"
REASON_MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
REASON_EFFECT_NOT_NONE = "AUTHORITY_RUNTIME_ORDER_EFFECT_NOT_NONE"
REASON_BINDING_COMPLETION_INVALID = "FLEET_BINDING_COMPLETION_INVALID"
REASON_BINDING_NOT_READY = "BINDING_NOT_READY_FOR_EVALUATION_RATIFICATION"
REASON_MISSING_CANDIDATE = "MISSING_FLEET_CANDIDATE"
REASON_EXTRA_CANDIDATE = "EXTRA_FLEET_CANDIDATE"
REASON_DUPLICATE_CANDIDATE = "DUPLICATE_FLEET_CANDIDATE"
REASON_FAILED_HISTORICAL_CANDIDATE = "FAILED_HISTORICAL_CANDIDATE_EXCLUDED"
REASON_FLEET_BINDING_DIGEST_MISMATCH = "FLEET_BINDING_DIGEST_MISMATCH"
REASON_POLICY_DRIFT = "COMMON_POLICY_DRIFT"
REASON_ECONOMIC_POLICY_MISMATCH = "ECONOMIC_POLICY_MISMATCH"
REASON_SHARED_BINDING_MISMATCH = "SHARED_BINDING_MISMATCH"
REASON_FUTURES_ONLY_VIOLATION = "FUTURES_ONLY_VIOLATION"
REASON_SPOT_BINDING = "SPOT_BINDING_REJECTED"
REASON_SYNTHETIC_SPOT_BINDING = "SYNTHETIC_SPOT_BINDING_REJECTED"
REASON_BITCOIN_DIRECTION_BINDING = "BITCOIN_DIRECTION_BINDING_REJECTED"
REASON_BITCOIN_INSTRUMENT_PRESENT = "BITCOIN_INSTRUMENT_PRESENT"
REASON_ZERO_FEE = "ZERO_FEE_REJECTED"
REASON_ZERO_SLIPPAGE = "ZERO_SLIPPAGE_REJECTED"
REASON_INCOMPLETE_PERIOD_SPLIT = "INCOMPLETE_PERIOD_SPLIT"
REASON_EVALUATION_ALREADY_EXECUTED = "ECONOMIC_EVALUATION_ALREADY_EXECUTED"
REASON_EVALUATION_NOT_AUTHORIZED = "ECONOMIC_EVALUATION_NOT_AUTHORIZED"
REASON_SCOPE_NOT_RATIFIED = "OFFLINE_ECONOMIC_EVALUATION_SCOPE_NOT_RATIFIED"
REASON_WRONG_RATIFICATION_DIGEST = "WRONG_RATIFICATION_DIGEST"
REASON_WRONG_SEMANTIC_DIGEST = "WRONG_SEMANTIC_DIGEST"
REASON_WRONG_CONFIG_DIGEST = "WRONG_CONFIG_DIGEST"
REASON_WRONG_IMPLEMENTATION_DIGEST = "WRONG_IMPLEMENTATION_DIGEST"
REASON_NON_CANONICAL_SERIALIZATION = "NON_CANONICAL_SERIALIZATION"
REASON_BINDING_REPAIR_REJECTED = "BINDING_REPAIR_REJECTED"
REASON_FORBIDDEN_STAGE_IN_RATIFICATION = "FORBIDDEN_EVALUATION_STAGE_EXECUTED_IN_RATIFICATION"
REASON_PROHIBITED_ACTION_VIOLATION = "PROHIBITED_ACTION_VIOLATION"

RATIFICATION_REQUIRED_FIELDS = (
    "schema_version",
    "ratification_id",
    "ratification_version",
    "fleet_binding_ref",
    "fleet_binding_digest",
    "candidate_refs",
    "candidate_binding_digests",
    "common_dataset_policy_ref",
    "common_period_policy_ref",
    "common_instrument_policy_ref",
    "fee_model_binding",
    "slippage_model_binding",
    "funding_model_binding",
    "execution_model_binding",
    "economic_policy_binding",
    "walk_forward_policy_binding",
    "monte_carlo_policy_binding",
    "stress_policy_binding",
    "parameter_sensitivity_policy_binding",
    "evidence_schema_ref",
    "evidence_manifest_policy",
    "allowed_evaluation_stages",
    "prohibited_actions",
    "evaluation_authorization_status",
    "economic_validity_status",
    "runtime_effect",
    "authority_effect",
    "implementation_digest",
    "config_digest",
    "semantic_digest",
    "reason_codes",
    "final_research_fleet_binding_ready",
    "offline_economic_evaluation_scope_ratified",
    "economic_evaluation_authorized",
    "economic_evaluation_executed",
    "economic_validity_offline_gate_pass",
    "runtime_rewire_admissible",
    "allowed_after_this_ratification",
    "order_effect",
    "futures_only",
    "bitcoin_direction_allowed",
    "spot_allowed",
    "synthetic_spot_allowed",
    "operator_scope_ratification_ref",
    "operator_fleet_binding_ratification_ref",
    "canonical_serialization_version",
    "ratification_digest",
)

SCOPE_INVARIANT_REASON_CODES: tuple[str, ...] = (
    "COMMON_ECONOMIC_VALIDITY_POLICY_FOR_ALL_CANDIDATES",
    "VERSIONED_COMPARABLE_COST_FUNDING_EXECUTION_BINDINGS",
    "NO_CANDIDATE_SPECIFIC_THRESHOLD_ABATEMENT",
    "NO_POST_HOC_POLICY_ADJUSTMENT_FOR_RESULT_RESCUE",
    "NO_UNCHANGED_RETRY_OF_FAILED_HISTORICAL_BINDINGS",
    "NO_OUT_OF_SAMPLE_PARAMETER_OPTIMIZATION",
    "NO_TRAINING_VALIDATION_OOS_LEAKAGE",
    "NO_IMPLICIT_ZERO_COST",
    "NO_ECONOMIC_VALIDITY_WITHOUT_MANIFEST_VERIFIED_NET_EVIDENCE",
    "INDEPENDENT_CANDIDATE_PASS_FAIL_INCONCLUSIVE",
    "FLEET_AGGREGATION_MUST_NOT_MASK_CANDIDATE_FAILURES",
    "FULL_POLICY_PASS_REQUIRED_FOR_ECONOMICALLY_VIABLE_OFFLINE",
    "OFFLINE_PASS_DOES_NOT_GRANT_RUNTIME_OR_ORDER_AUTHORITY",
    "RATIFICATION_DOES_NOT_EXECUTE_EVALUATION_STAGES",
)


class ValidationVerdict(str, Enum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class ScopeRatificationValidationResultV0:
    verdict: ValidationVerdict
    valid: bool
    fail_reasons: tuple[str, ...]


def _stable_digest(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def compute_implementation_digest_v0() -> str:
    return _stable_digest(
        {
            "module": RATIFICATION_ID,
            "schema_version": SCHEMA_VERSION,
        }
    )


def dumps_ratification_canonical_v1(obj: Mapping[str, Any]) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str, ensure_ascii=False)


def compute_semantic_digest_v0(ratification_body: Mapping[str, Any]) -> str:
    payload = {
        "fleet_binding_digest": ratification_body.get("fleet_binding_digest"),
        "candidate_refs": ratification_body.get("candidate_refs"),
        "candidate_binding_digests": ratification_body.get("candidate_binding_digests"),
        "common_dataset_policy_ref": ratification_body.get("common_dataset_policy_ref"),
        "common_period_policy_ref": ratification_body.get("common_period_policy_ref"),
        "common_instrument_policy_ref": ratification_body.get("common_instrument_policy_ref"),
        "fee_model_binding": ratification_body.get("fee_model_binding"),
        "slippage_model_binding": ratification_body.get("slippage_model_binding"),
        "funding_model_binding": ratification_body.get("funding_model_binding"),
        "execution_model_binding": ratification_body.get("execution_model_binding"),
        "economic_policy_binding": ratification_body.get("economic_policy_binding"),
        "walk_forward_policy_binding": ratification_body.get("walk_forward_policy_binding"),
        "monte_carlo_policy_binding": ratification_body.get("monte_carlo_policy_binding"),
        "stress_policy_binding": ratification_body.get("stress_policy_binding"),
        "parameter_sensitivity_policy_binding": ratification_body.get(
            "parameter_sensitivity_policy_binding"
        ),
        "allowed_evaluation_stages": ratification_body.get("allowed_evaluation_stages"),
        "prohibited_actions": ratification_body.get("prohibited_actions"),
        "evaluation_authorization_status": ratification_body.get("evaluation_authorization_status"),
        "economic_validity_status": ratification_body.get("economic_validity_status"),
    }
    return _stable_digest(payload)


def compute_config_digest_v0(ratification_body: Mapping[str, Any]) -> str:
    payload = {
        "step31f_config_refs": [
            STEP31F_CONFIG_PATHS[strategy_id] for strategy_id, _ in FLEET_CANDIDATES
        ],
        "operator_scope_ratification_ref": ratification_body.get("operator_scope_ratification_ref"),
        "operator_fleet_binding_ratification_ref": ratification_body.get(
            "operator_fleet_binding_ratification_ref"
        ),
    }
    return _stable_digest(payload)


def compute_ratification_digest_v0(ratification_body: Mapping[str, Any]) -> str:
    body = dict(ratification_body)
    body.pop("ratification_digest", None)
    return hashlib.sha256(dumps_ratification_canonical_v1(body).encode("utf-8")).hexdigest()


def serialize_ratification_canonical_v0(ratification: Mapping[str, Any]) -> str:
    return dumps_ratification_canonical_v1(ratification) + "\n"


def _reject_repair_keys(obj: Mapping[str, Any], *, path: str, reasons: list[str]) -> None:
    for key in obj:
        if key in {"repair", "fallback", "auto_fix", "default_if_missing"}:
            reasons.append(f"{REASON_BINDING_REPAIR_REJECTED}:{path}.{key}")


def _contains_forbidden_token(value: str) -> bool:
    lowered = value.lower()
    return any(token in lowered for token in FORBIDDEN_INSTRUMENT_TOKENS)


def _validate_positive_cost(value: Any, *, field: str, reasons: list[str]) -> None:
    if not isinstance(value, (int, float)) or float(value) <= 0.0:
        reasons.append(f"{REASON_ZERO_FEE if 'fee' in field else REASON_ZERO_SLIPPAGE}:{field}")


def _validate_instrument_binding(binding: Mapping[str, Any], reasons: list[str]) -> None:
    if binding.get("futures_only") is not True:
        reasons.append(REASON_FUTURES_ONLY_VIOLATION)
    if binding.get("spot_allowed") is True:
        reasons.append(REASON_SPOT_BINDING)
    if binding.get("synthetic_spot_allowed") is True:
        reasons.append(REASON_SYNTHETIC_SPOT_BINDING)
    if binding.get("bitcoin_direction_allowed") is True:
        reasons.append(REASON_BITCOIN_DIRECTION_BINDING)
    for instrument_id in binding.get("eligible_instrument_ids", ()):
        if isinstance(instrument_id, str) and _contains_forbidden_token(instrument_id):
            reasons.append(f"{REASON_BITCOIN_INSTRUMENT_PRESENT}:{instrument_id}")


def _validate_materialized_period(field: Any, *, name: str, reasons: list[str]) -> None:
    if not isinstance(field, Mapping):
        reasons.append(f"{REASON_INCOMPLETE_PERIOD_SPLIT}:{name}")
        return
    if field.get("status") != "MATERIALIZED":
        reasons.append(f"{REASON_INCOMPLETE_PERIOD_SPLIT}:{name}")
        return
    for key in ("start", "end"):
        raw = field.get(key)
        if not isinstance(raw, str) or not raw.strip():
            reasons.append(f"{REASON_INCOMPLETE_PERIOD_SPLIT}:{name}.{key}")


def _extract_policy_binding(cfg: Mapping[str, Any], *path: str) -> Mapping[str, Any]:
    current: Any = cfg
    for segment in path:
        if not isinstance(current, Mapping):
            return {}
        current = current.get(segment)
    if isinstance(current, Mapping):
        return dict(current)
    return {}


def _build_common_policy_bindings(
    *,
    repo_root: Path,
    reference_candidate: Mapping[str, Any],
) -> dict[str, Any]:
    strategy_id = str(reference_candidate["strategy_id"])
    cfg = load_step31f_evaluation_config_v0(repo_root, strategy_id)
    economic_eval = cfg.get("economic_evaluation_v1")
    if not isinstance(economic_eval, Mapping):
        economic_eval = {}
    backtest = cfg.get("backtest")
    if not isinstance(backtest, Mapping):
        backtest = {}

    return {
        "common_dataset_policy_ref": dict(reference_candidate["dataset_binding"]),
        "common_period_policy_ref": dict(reference_candidate["period_binding"]),
        "common_instrument_policy_ref": dict(reference_candidate["instrument_binding"]),
        "fee_model_binding": dict(reference_candidate["fee_model_binding"]),
        "slippage_model_binding": dict(reference_candidate["slippage_model_binding"]),
        "funding_model_binding": dict(reference_candidate["funding_model_binding"]),
        "execution_model_binding": dict(reference_candidate["execution_model_binding"]),
        "economic_policy_binding": dict(reference_candidate["economic_policy_binding"]),
        "walk_forward_policy_binding": _extract_policy_binding(economic_eval, "walk_forward"),
        "monte_carlo_policy_binding": _extract_policy_binding(economic_eval, "monte_carlo"),
        "stress_policy_binding": _extract_policy_binding(economic_eval, "stress"),
        "parameter_sensitivity_policy_binding": _extract_policy_binding(
            backtest, "parameter_sensitivity"
        ),
    }


def _validate_common_policies_uniform(
    candidates: Sequence[Mapping[str, Any]],
    *,
    repo_root: Path,
    reasons: list[str],
) -> None:
    if not candidates:
        return
    reference = candidates[0]
    common = _build_common_policy_bindings(repo_root=repo_root, reference_candidate=reference)
    candidate_field_map = {
        "common_dataset_policy_ref": "dataset_binding",
        "common_period_policy_ref": "period_binding",
        "common_instrument_policy_ref": "instrument_binding",
        "fee_model_binding": "fee_model_binding",
        "slippage_model_binding": "slippage_model_binding",
        "funding_model_binding": "funding_model_binding",
        "execution_model_binding": "execution_model_binding",
        "economic_policy_binding": "economic_policy_binding",
    }
    for field, candidate_key in candidate_field_map.items():
        ref_value = common[field]
        for candidate in candidates[1:]:
            actual = candidate.get(candidate_key)
            if actual != ref_value:
                if candidate_key == "economic_policy_binding":
                    reasons.append(
                        f"{REASON_ECONOMIC_POLICY_MISMATCH}:{candidate.get('strategy_id')}"
                    )
                else:
                    reasons.append(
                        f"{REASON_SHARED_BINDING_MISMATCH}:{field}:{candidate.get('strategy_id')}"
                    )

    ref_cfg = load_step31f_evaluation_config_v0(repo_root, str(reference["strategy_id"]))
    for candidate in candidates:
        strategy_id = str(candidate["strategy_id"])
        cfg = load_step31f_evaluation_config_v0(repo_root, strategy_id)
        for policy_field, cfg_path in (
            ("walk_forward_policy_binding", ("economic_evaluation_v1", "walk_forward")),
            ("monte_carlo_policy_binding", ("economic_evaluation_v1", "monte_carlo")),
            ("stress_policy_binding", ("economic_evaluation_v1", "stress")),
            ("parameter_sensitivity_policy_binding", ("backtest", "parameter_sensitivity")),
        ):
            ref_policy = _extract_policy_binding(ref_cfg, *cfg_path)
            actual_policy = _extract_policy_binding(cfg, *cfg_path)
            if actual_policy != ref_policy:
                reasons.append(f"{REASON_POLICY_DRIFT}:{policy_field}:{strategy_id}")


def materialize_final_research_fleet_offline_economic_evaluation_scope_ratification_v0(
    *,
    repo_root: Path,
    fleet_binding_completion: Mapping[str, Any],
) -> dict[str, Any]:
    """Materialize scope ratification from a validated fleet binding completion."""
    binding_validation = validate_final_research_fleet_versioned_binding_completion_v0(
        fleet_binding_completion,
        repo_root=repo_root,
        require_ready_for_eval=True,
    )
    if binding_validation.verdict != BindingValidationVerdict.ACCEPTED:
        raise ValueError(f"{REASON_BINDING_COMPLETION_INVALID}:{binding_validation.fail_reasons}")

    candidates = list(fleet_binding_completion["candidates"])
    candidate_refs = [
        canonical_candidate_identifier(str(c["strategy_id"]), str(c["strategy_version"]))
        for c in candidates
    ]
    candidate_binding_digests = {
        ref: str(candidates[index]["binding_semantic_digest"])
        for index, ref in enumerate(candidate_refs)
    }

    common_policies = _build_common_policy_bindings(
        repo_root=repo_root,
        reference_candidate=candidates[0],
    )

    ratification_body: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "ratification_id": RATIFICATION_ID,
        "ratification_version": RATIFICATION_VERSION,
        "fleet_binding_ref": {
            "completion_id": COMPLETION_ID,
            "completion_digest": fleet_binding_completion["completion_digest"],
            "fleet_id": FLEET_ID,
            "fleet_version": FLEET_VERSION,
            "schema_version": fleet_binding_completion.get("schema_version"),
        },
        "fleet_binding_digest": fleet_binding_completion["completion_digest"],
        "candidate_refs": candidate_refs,
        "candidate_binding_digests": candidate_binding_digests,
        **common_policies,
        "evidence_schema_ref": EVIDENCE_SCHEMA_REF,
        "evidence_manifest_policy": EVIDENCE_MANIFEST_POLICY,
        "allowed_evaluation_stages": list(ALLOWED_EVALUATION_STAGES),
        "prohibited_actions": list(PROHIBITED_ACTIONS),
        "evaluation_authorization_status": EVALUATION_AUTHORIZATION_STATUS,
        "economic_validity_status": ECONOMIC_VALIDITY_STATUS,
        "runtime_effect": RUNTIME_EFFECT,
        "authority_effect": AUTHORITY_EFFECT,
        "order_effect": ORDER_EFFECT,
        "final_research_fleet_binding_ready": FINAL_RESEARCH_FLEET_BINDING_READY,
        "offline_economic_evaluation_scope_ratified": OFFLINE_ECONOMIC_EVALUATION_SCOPE_RATIFIED,
        "economic_evaluation_authorized": ECONOMIC_EVALUATION_AUTHORIZED,
        "economic_evaluation_executed": ECONOMIC_EVALUATION_EXECUTED,
        "economic_validity_offline_gate_pass": ECONOMIC_VALIDITY_OFFLINE_GATE_PASS,
        "runtime_rewire_admissible": RUNTIME_REWIRE_ADMISSIBLE,
        "allowed_after_this_ratification": ALLOWED_AFTER_THIS_RATIFICATION,
        "futures_only": FUTURES_ONLY,
        "bitcoin_direction_allowed": BITCOIN_DIRECTION_ALLOWED,
        "spot_allowed": SPOT_ALLOWED,
        "synthetic_spot_allowed": SYNTHETIC_SPOT_ALLOWED,
        "operator_scope_ratification_ref": OPERATOR_SCOPE_RATIFICATION_REF,
        "operator_fleet_binding_ratification_ref": OPERATOR_RATIFICATION_REF,
        "canonical_serialization_version": CANONICAL_SERIALIZATION_VERSION,
        "reason_codes": list(SCOPE_INVARIANT_REASON_CODES),
        "digest_semantics": {
            "ratification_digest": "RATIFICATION_BODY_CANONICAL_JSON_v0",
            "semantic_digest": "SCOPE_RATIFICATION_SEMANTIC_PAYLOAD_v0",
            "config_digest": "STEP31F_CONFIG_REFS_AND_OPERATOR_REFS_v0",
            "implementation_digest": "SCOPE_RATIFICATION_MODULE_REF_v0",
            "fleet_binding_digest": "FLEET_BINDING_COMPLETION_DIGEST_v0",
        },
        "economic_policy_version": ECONOMIC_VALIDITY_POLICY_VERSION,
        "evaluation_execution_performed": False,
        "evaluation_modules_invoked": [],
    }
    ratification_body["implementation_digest"] = compute_implementation_digest_v0()
    ratification_body["config_digest"] = compute_config_digest_v0(ratification_body)
    ratification_body["semantic_digest"] = compute_semantic_digest_v0(ratification_body)
    ratification_body["ratification_digest"] = compute_ratification_digest_v0(ratification_body)
    return ratification_body


def validate_final_research_fleet_offline_economic_evaluation_scope_ratification_v0(
    ratification: Any,
    *,
    repo_root: Path,
    expected_fleet_binding_completion: Mapping[str, Any] | None = None,
) -> ScopeRatificationValidationResultV0:
    reasons: list[str] = []
    if not isinstance(ratification, Mapping):
        return ScopeRatificationValidationResultV0(
            verdict=ValidationVerdict.REJECTED,
            valid=False,
            fail_reasons=(REASON_RATIFICATION_NOT_OBJECT,),
        )

    _reject_repair_keys(ratification, path="$", reasons=reasons)

    if ratification.get("schema_version") != SCHEMA_VERSION:
        reasons.append(REASON_UNKNOWN_SCHEMA_VERSION)

    for field in RATIFICATION_REQUIRED_FIELDS:
        if field not in ratification:
            reasons.append(f"{REASON_MISSING_REQUIRED_FIELD}:{field}")

    for effect_field, expected in (
        ("authority_effect", AUTHORITY_EFFECT),
        ("runtime_effect", RUNTIME_EFFECT),
        ("order_effect", ORDER_EFFECT),
    ):
        if ratification.get(effect_field) != expected:
            reasons.append(f"{REASON_EFFECT_NOT_NONE}:{effect_field}")

    status_checks = (
        ("final_research_fleet_binding_ready", FINAL_RESEARCH_FLEET_BINDING_READY),
        ("offline_economic_evaluation_scope_ratified", OFFLINE_ECONOMIC_EVALUATION_SCOPE_RATIFIED),
        ("economic_evaluation_authorized", ECONOMIC_EVALUATION_AUTHORIZED),
        ("economic_evaluation_executed", ECONOMIC_EVALUATION_EXECUTED),
        ("economic_validity_offline_gate_pass", ECONOMIC_VALIDITY_OFFLINE_GATE_PASS),
        ("runtime_rewire_admissible", RUNTIME_REWIRE_ADMISSIBLE),
        ("allowed_after_this_ratification", ALLOWED_AFTER_THIS_RATIFICATION),
        ("futures_only", FUTURES_ONLY),
        ("bitcoin_direction_allowed", BITCOIN_DIRECTION_ALLOWED),
        ("spot_allowed", SPOT_ALLOWED),
        ("synthetic_spot_allowed", SYNTHETIC_SPOT_ALLOWED),
    )
    for field, expected in status_checks:
        if ratification.get(field) is not expected:
            if field == "economic_evaluation_authorized" and ratification.get(field) is not True:
                reasons.append(REASON_EVALUATION_NOT_AUTHORIZED)
            elif field == "economic_evaluation_executed" and ratification.get(field) is not False:
                reasons.append(REASON_EVALUATION_ALREADY_EXECUTED)
            elif (
                field == "offline_economic_evaluation_scope_ratified"
                and ratification.get(field) is not True
            ):
                reasons.append(REASON_SCOPE_NOT_RATIFIED)
            elif field == "futures_only" and ratification.get(field) is not True:
                reasons.append(REASON_FUTURES_ONLY_VIOLATION)
            elif field == "bitcoin_direction_allowed" and ratification.get(field) is not False:
                reasons.append(REASON_BITCOIN_DIRECTION_BINDING)
            elif field == "spot_allowed" and ratification.get(field) is not False:
                reasons.append(REASON_SPOT_BINDING)
            elif field == "synthetic_spot_allowed" and ratification.get(field) is not False:
                reasons.append(REASON_SYNTHETIC_SPOT_BINDING)

    if ratification.get("evaluation_execution_performed") is True:
        reasons.append(REASON_EVALUATION_ALREADY_EXECUTED)
    invoked = ratification.get("evaluation_modules_invoked")
    if isinstance(invoked, list) and invoked:
        reasons.append(REASON_FORBIDDEN_STAGE_IN_RATIFICATION)

    if list(ratification.get("allowed_evaluation_stages") or []) != list(ALLOWED_EVALUATION_STAGES):
        reasons.append(REASON_POLICY_DRIFT + ":allowed_evaluation_stages")
    if list(ratification.get("prohibited_actions") or []) != list(PROHIBITED_ACTIONS):
        reasons.append(REASON_POLICY_DRIFT + ":prohibited_actions")

    candidate_refs = ratification.get("candidate_refs")
    if not isinstance(candidate_refs, list):
        reasons.append(f"{REASON_MISSING_REQUIRED_FIELD}:candidate_refs")
        candidate_refs = []

    expected_refs = [canonical_candidate_identifier(sid, ver) for sid, ver in FLEET_CANDIDATES]
    if sorted(candidate_refs) != sorted(expected_refs):
        if len(candidate_refs) != len(set(candidate_refs)):
            reasons.append(REASON_DUPLICATE_CANDIDATE)
        missing = sorted(set(expected_refs) - set(candidate_refs))
        for ref in missing:
            reasons.append(f"{REASON_MISSING_CANDIDATE}:{ref}")
        for ref in sorted(set(candidate_refs) - set(expected_refs)):
            sid = ref.split("/")[0]
            if (sid, ref.split("/")[1]) in FAILED_HISTORICAL_CANDIDATES:
                reasons.append(f"{REASON_FAILED_HISTORICAL_CANDIDATE}:{ref}")
            else:
                reasons.append(f"{REASON_EXTRA_CANDIDATE}:{ref}")

    binding_digests = ratification.get("candidate_binding_digests")
    if isinstance(binding_digests, Mapping):
        for ref in expected_refs:
            if ref not in binding_digests:
                reasons.append(f"{REASON_MISSING_REQUIRED_FIELD}:candidate_binding_digests.{ref}")

    fleet_binding_digest = ratification.get("fleet_binding_digest")
    fleet_binding_ref = ratification.get("fleet_binding_ref")
    if isinstance(fleet_binding_ref, Mapping):
        if fleet_binding_ref.get("completion_digest") != fleet_binding_digest:
            reasons.append(REASON_FLEET_BINDING_DIGEST_MISMATCH)
        if expected_fleet_binding_completion is not None:
            expected_digest = expected_fleet_binding_completion.get("completion_digest")
            if expected_digest != fleet_binding_digest:
                reasons.append(REASON_FLEET_BINDING_DIGEST_MISMATCH)

    fee = ratification.get("fee_model_binding")
    if isinstance(fee, Mapping):
        _validate_positive_cost(fee.get("fee_bps"), field="fee_bps", reasons=reasons)
    else:
        reasons.append(REASON_ZERO_FEE)

    slippage = ratification.get("slippage_model_binding")
    if isinstance(slippage, Mapping):
        _validate_positive_cost(slippage.get("slippage_bps"), field="slippage_bps", reasons=reasons)
    else:
        reasons.append(REASON_ZERO_SLIPPAGE)

    instrument = ratification.get("common_instrument_policy_ref")
    if isinstance(instrument, Mapping):
        _validate_instrument_binding(instrument, reasons=reasons)

    if expected_fleet_binding_completion is not None:
        for candidate in expected_fleet_binding_completion.get("candidates", ()):
            if not isinstance(candidate, Mapping):
                continue
            strategy_id = str(candidate.get("strategy_id", ""))
            ref = canonical_candidate_identifier(
                strategy_id, str(candidate.get("strategy_version", ""))
            )
            if isinstance(binding_digests, Mapping) and ref in binding_digests:
                expected_semantic = compute_binding_semantic_digest_v0(candidate)
                if binding_digests[ref] != expected_semantic:
                    reasons.append(f"{REASON_WRONG_SEMANTIC_DIGEST}:{ref}")

        _validate_common_policies_uniform(
            list(expected_fleet_binding_completion.get("candidates") or []),
            repo_root=repo_root,
            reasons=reasons,
        )
        for candidate in expected_fleet_binding_completion.get("candidates", ()):
            if isinstance(candidate, Mapping):
                _validate_materialized_period(
                    candidate.get("training_period"), name="training_period", reasons=reasons
                )
                _validate_materialized_period(
                    candidate.get("validation_period"), name="validation_period", reasons=reasons
                )
                _validate_materialized_period(
                    candidate.get("out_of_sample_period"),
                    name="out_of_sample_period",
                    reasons=reasons,
                )

    expected_ratification_digest = compute_ratification_digest_v0(ratification)
    if ratification.get("ratification_digest") != expected_ratification_digest:
        reasons.append(REASON_WRONG_RATIFICATION_DIGEST)

    expected_semantic = compute_semantic_digest_v0(ratification)
    if ratification.get("semantic_digest") != expected_semantic:
        reasons.append(REASON_WRONG_SEMANTIC_DIGEST)

    expected_config = compute_config_digest_v0(ratification)
    if ratification.get("config_digest") != expected_config:
        reasons.append(REASON_WRONG_CONFIG_DIGEST)

    expected_impl = compute_implementation_digest_v0()
    if ratification.get("implementation_digest") != expected_impl:
        reasons.append(REASON_WRONG_IMPLEMENTATION_DIGEST)

    canonical = dumps_ratification_canonical_v1(ratification)
    if canonical != dumps_ratification_canonical_v1(json.loads(canonical)):
        reasons.append(REASON_NON_CANONICAL_SERIALIZATION)
    if _ABSOLUTE_PATH_PATTERN.search(canonical):
        reasons.append(REASON_NON_CANONICAL_SERIALIZATION + ":absolute_path_in_ratification")

    unique_reasons = tuple(dict.fromkeys(reasons))
    if unique_reasons:
        return ScopeRatificationValidationResultV0(
            verdict=ValidationVerdict.REJECTED,
            valid=False,
            fail_reasons=unique_reasons,
        )
    return ScopeRatificationValidationResultV0(
        verdict=ValidationVerdict.ACCEPTED,
        valid=True,
        fail_reasons=(),
    )


def clone_ratification(ratification: Mapping[str, Any]) -> dict[str, Any]:
    return deepcopy(dict(ratification))


__all__ = [
    "ALLOWED_AFTER_THIS_RATIFICATION",
    "ALLOWED_EVALUATION_STAGES",
    "AUTHORITY_EFFECT",
    "CANONICAL_SERIALIZATION_VERSION",
    "ECONOMIC_EVALUATION_AUTHORIZED",
    "ECONOMIC_EVALUATION_EXECUTED",
    "ECONOMIC_VALIDITY_OFFLINE_GATE_PASS",
    "FINAL_RESEARCH_FLEET_BINDING_READY",
    "OFFLINE_ECONOMIC_EVALUATION_SCOPE_RATIFIED",
    "ORDER_EFFECT",
    "PROHIBITED_ACTIONS",
    "RATIFICATION_ID",
    "RATIFICATION_VERSION",
    "RUNTIME_EFFECT",
    "RUNTIME_REWIRE_ADMISSIBLE",
    "SCHEMA_VERSION",
    "ScopeRatificationValidationResultV0",
    "ValidationVerdict",
    "clone_ratification",
    "compute_ratification_digest_v0",
    "compute_semantic_digest_v0",
    "materialize_final_research_fleet_offline_economic_evaluation_scope_ratification_v0",
    "serialize_ratification_canonical_v0",
    "validate_final_research_fleet_offline_economic_evaluation_scope_ratification_v0",
]
