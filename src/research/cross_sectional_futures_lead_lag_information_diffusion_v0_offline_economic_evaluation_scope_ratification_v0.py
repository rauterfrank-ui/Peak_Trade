"""Cross-sectional lead-lag diffusion v0 offline economic evaluation scope ratification v0.

Deterministic, fail-closed ratification of bounded offline-only economic evaluation
scope for cross_sectional_futures_lead_lag_information_diffusion/v0. Does not execute
evaluation.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

from src.backtest.economic_validity_policy_v1 import ECONOMIC_VALIDITY_POLICY_VERSION
from src.research.cross_sectional_futures_lead_lag_information_diffusion_v0_versioned_hypothesis_binding_v0 import (
    AUTHORITY_EFFECT,
    CONFIG_REL_PATH as VERSIONED_BINDING_CONFIG_REL_PATH,
    ORDER_EFFECT,
    RESEARCH_HYPOTHESIS_ID,
    RUNTIME_EFFECT,
    STRATEGY_ID,
    STRATEGY_VERSION,
    BindingValidationVerdict,
    compute_implementation_digest_v0,
    materialize_versioned_hypothesis_binding_v0,
    validate_versioned_hypothesis_binding_v0,
)

PACKAGE_MARKER = (
    "CROSS_SECTIONAL_FUTURES_LEAD_LAG_INFORMATION_DIFFUSION_V0_OFFLINE_ECONOMIC_"
    "EVALUATION_SCOPE_RATIFICATION_V0=true"
)

SCHEMA_VERSION = (
    "cross_sectional_futures_lead_lag_information_diffusion_v0_offline_economic_"
    "evaluation_scope_ratification.v0"
)
RATIFICATION_ID = (
    "cross_sectional_futures_lead_lag_information_diffusion_v0_offline_economic_"
    "evaluation_scope_ratification_v0"
)
RATIFICATION_VERSION = "v0"
CANONICAL_SERIALIZATION_VERSION = "research_scope_ratification_canonical_json_v1"
SCOPE_CLASSIFICATION = "BOUNDED_FUTURES_ONLY_RESEARCH_SCOPE_DEFINITION_AND_BINDING_RATIFICATION_V0"
RECOMMENDED_SCOPE_ID = (
    "CROSS_SECTIONAL_FUTURES_LEAD_LAG_INFORMATION_DIFFUSION_V0_OFFLINE_ECONOMIC_"
    "EVALUATION_EXECUTION_INFRASTRUCTURE_V0"
)
OPERATOR_GO_RATIFICATION_PREP = (
    "GO_CROSS_SECTIONAL_FUTURES_LEAD_LAG_INFORMATION_DIFFUSION_V0_OFFLINE_ECONOMIC_"
    "EVALUATION_EXECUTION_INFRASTRUCTURE_IMPLEMENTATION_V0"
)
CONFIG_REL_PATH = (
    "config/research/"
    "cross_sectional_futures_lead_lag_information_diffusion_v0_offline_economic_"
    "evaluation_scope_ratification_v0.json"
)
RUNNER_BINDING_REF = (
    "scripts/ops/"
    "run_cross_sectional_futures_lead_lag_information_diffusion_v0_offline_economic_"
    "evaluation_execution_v0.py"
)
HARNESS_BINDING_REF = (
    "src/research/"
    "cross_sectional_futures_lead_lag_information_diffusion_v0_offline_economic_"
    "evaluation_execution_v0.py"
)

OFFLINE_ECONOMIC_EVALUATION_SCOPE_RATIFIED = True
ECONOMIC_EVALUATION_AUTHORIZED = False
ECONOMIC_EVALUATION_EXECUTED = False
FUTURES_ONLY = True
BITCOIN_DIRECTION_ALLOWED = False

REASON_ECONOMIC_EVALUATION_NOT_AUTHORIZED = "ECONOMIC_EVALUATION_NOT_AUTHORIZED"
REASON_OFFLINE_BOUNDARY_VIOLATION = "OFFLINE_BOUNDARY_VIOLATION"
REASON_STORED_ECONOMIC_EVALUATION_AUTHORIZED_VIOLATION = (
    "STORED_ECONOMIC_EVALUATION_AUTHORIZED_VIOLATION"
)
REASON_SCOPE_RATIFICATION_MISMATCH = "SCOPE_RATIFICATION_MISMATCH"
REASON_BINDING_DIGEST_MISMATCH = "BINDING_DIGEST_MISMATCH"
REASON_DATASET_DIGEST_MISMATCH = "DATASET_DIGEST_MISMATCH"
REASON_UNIVERSE_DIGEST_MISMATCH = "UNIVERSE_DIGEST_MISMATCH"
REASON_IMPLEMENTATION_DIGEST_MISMATCH = "IMPLEMENTATION_DIGEST_MISMATCH"
REASON_CONFIG_DIGEST_MISMATCH = "CONFIG_DIGEST_MISMATCH"
REASON_FULL_CANONICAL_PARITY_NOT_PROVEN = "FULL_CANONICAL_PARITY_NOT_PROVEN"
REASON_BACKTEST_RUNTIME_DECISION_PARITY_FAIL = "BACKTEST_RUNTIME_DECISION_PARITY_FAIL"

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
    "ORDERS",
    "CANCELS",
    "CREDENTIALS",
    "ARMING",
    "CANDIDATE_PROMOTION",
    "POLICY_THRESHOLD_RETROFIT",
    "DATASET_SUBSTITUTION",
    "PERIOD_BINDING_SUBSTITUTION",
    "PARAMETER_SEARCH",
    "IMPLICIT_ZERO_COST",
    "FAILED_BINDING_RETRY",
    "TERMINAL_FAILED_BINDING_UNCHANGED_RETRY",
)


class ValidationVerdictEnum(str, Enum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class RatificationValidationResultV0:
    verdict: ValidationVerdictEnum
    fail_reasons: tuple[str, ...]


@dataclass(frozen=True)
class InvocationBoundAuthorizationResultV0:
    authorized: bool
    economic_evaluation_authorized: bool
    reason_codes: tuple[str, ...]


def _stable_digest(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def serialize_ratification_canonical_v0(obj: Mapping[str, Any]) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)


def validate_lead_lag_offline_economic_evaluation_scope_ratification_v0(
    ratification: Mapping[str, Any],
    *,
    expected_binding: Mapping[str, Any] | None = None,
) -> RatificationValidationResultV0:
    reasons: list[str] = []
    envelope = dict(expected_binding or materialize_versioned_hypothesis_binding_v0())
    validation_verdict, fail_reasons = validate_versioned_hypothesis_binding_v0(envelope)
    if validation_verdict is not BindingValidationVerdict.ACCEPTED_COMPLETE:
        reasons.extend(fail_reasons)

    if ratification.get("binding_digest") != envelope.get("binding_digest"):
        reasons.append("BINDING_DIGEST_MISMATCH")
    if ratification.get("hypothesis_id") != envelope.get("hypothesis_id"):
        reasons.append("HYPOTHESIS_ID_MISMATCH")
    if ratification.get("futures_only") is not True:
        reasons.append("FUTURES_ONLY_VIOLATION")
    if ratification.get("bitcoin_direction_allowed") is not False:
        reasons.append("BITCOIN_DIRECTION_VIOLATION")
    if ratification.get("economic_evaluation_executed") is not False:
        reasons.append("ECONOMIC_EVALUATION_EXECUTED_VIOLATION")
    if ratification.get("economic_evaluation_authorized") is not False:
        reasons.append("ECONOMIC_EVALUATION_AUTHORIZED_VIOLATION")

    unique = tuple(dict.fromkeys(reasons))
    if unique:
        return RatificationValidationResultV0(
            verdict=ValidationVerdictEnum.REJECTED,
            fail_reasons=unique,
        )
    return RatificationValidationResultV0(verdict=ValidationVerdictEnum.ACCEPTED, fail_reasons=())


def evaluate_invocation_bound_economic_evaluation_authorization_v0(
    *,
    ratification: Mapping[str, Any],
    versioned_binding: Mapping[str, Any],
    go_token: str | None,
    allowed_execution_go_tokens: frozenset[str],
    ops_config: Mapping[str, Any],
    full_chain_wired: bool,
    parity_pass: bool,
) -> InvocationBoundAuthorizationResultV0:
    """Derive fail-closed invocation-bound execution authorization.

    Persisted scope ratification remains ``economic_evaluation_authorized=false`` by default.
    A separately confirmed execution GO elevates authorization only when all canonical
    co-requisites are satisfied for this invocation. No runtime or authority effect.
    """
    reasons: list[str] = []

    if ratification.get("economic_evaluation_authorized") is not False:
        reasons.append(REASON_STORED_ECONOMIC_EVALUATION_AUTHORIZED_VIOLATION)

    if not go_token or go_token not in allowed_execution_go_tokens:
        reasons.append(REASON_ECONOMIC_EVALUATION_NOT_AUTHORIZED)

    for field_name in ("strategy_id", "strategy_version", "hypothesis_id"):
        if ratification.get(field_name) != versioned_binding.get(field_name):
            reasons.append(REASON_SCOPE_RATIFICATION_MISMATCH)

    if ratification.get("binding_digest") != versioned_binding.get("binding_digest"):
        reasons.append(REASON_BINDING_DIGEST_MISMATCH)

    expected_dataset_digest = str(
        ops_config.get("cross_sectional_evaluation_binding_v1", {})
        .get("dataset_binding", {})
        .get("dataset_digest", versioned_binding.get("dataset_digest", ""))
    )
    if str(versioned_binding.get("dataset_digest", "")) != expected_dataset_digest:
        reasons.append(REASON_DATASET_DIGEST_MISMATCH)

    universe_digest = str(
        versioned_binding.get("binding", {})
        .get("pit_universe_binding", {})
        .get("universe_digest", "")
    )
    expected_universe_digest = str(
        ops_config.get("cross_sectional_evaluation_binding_v1", {})
        .get("instrument_universe_binding", {})
        .get("universe_digest", ratification.get("universe_digest", ""))
    )
    if universe_digest != expected_universe_digest:
        reasons.append(REASON_UNIVERSE_DIGEST_MISMATCH)

    expected_implementation_digest = str(ops_config.get("implementation_digest", ""))
    binding_implementation_digest = str(
        versioned_binding.get("binding", {})
        .get("digest_bindings", {})
        .get("implementation_digest", {})
        .get("value", versioned_binding.get("implementation_digest", ""))
    )
    ratification_implementation_digest = str(ratification.get("implementation_digest", ""))
    if expected_implementation_digest and (
        binding_implementation_digest != expected_implementation_digest
        or ratification_implementation_digest != expected_implementation_digest
    ):
        reasons.append(REASON_IMPLEMENTATION_DIGEST_MISMATCH)

    expected_config_digest = str(ops_config.get("config_digest", ""))
    binding_config_digest = str(versioned_binding.get("config_digest", ""))
    if expected_config_digest and binding_config_digest != expected_config_digest:
        reasons.append(REASON_CONFIG_DIGEST_MISMATCH)

    constraints = versioned_binding.get("system_constraints", {})
    if constraints.get("futures_only") is not True or ratification.get("futures_only") is not True:
        reasons.append("FUTURES_ONLY_VIOLATION")
    if (
        constraints.get("bitcoin_direction_allowed") is not False
        or ratification.get("bitcoin_direction_allowed") is not False
    ):
        reasons.append("BITCOIN_DIRECTION_VIOLATION")

    for effect_field, expected in (
        ("runtime_effect", RUNTIME_EFFECT),
        ("authority_effect", AUTHORITY_EFFECT),
        ("order_effect", ORDER_EFFECT),
    ):
        if (
            ratification.get(effect_field) != expected
            or versioned_binding.get(effect_field) != expected
        ):
            reasons.append(REASON_OFFLINE_BOUNDARY_VIOLATION)

    if not full_chain_wired:
        reasons.append(REASON_FULL_CANONICAL_PARITY_NOT_PROVEN)
    if not parity_pass:
        reasons.append(REASON_BACKTEST_RUNTIME_DECISION_PARITY_FAIL)

    unique = tuple(dict.fromkeys(reasons))
    authorized = not unique
    return InvocationBoundAuthorizationResultV0(
        authorized=authorized,
        economic_evaluation_authorized=authorized,
        reason_codes=unique,
    )


def materialize_invocation_bound_authorization_contract_v0() -> dict[str, Any]:
    return {
        "schema_version": (
            "cross_sectional_futures_lead_lag_information_diffusion_v0_invocation_bound_"
            "economic_evaluation_authorization.v0"
        ),
        "authorization_model": "INVOCATION_BOUND_FAIL_CLOSED",
        "persisted_economic_evaluation_authorized_default": ECONOMIC_EVALUATION_AUTHORIZED,
        "invocation_elevates_authorization": True,
        "runtime_effect": RUNTIME_EFFECT,
        "authority_effect": AUTHORITY_EFFECT,
        "order_effect": ORDER_EFFECT,
        "required_co_requisites": [
            "ALLOWED_EXECUTION_GO_TOKEN",
            "PERSISTED_ECONOMIC_EVALUATION_AUTHORIZED_FALSE",
            "SCOPE_RATIFICATION_BINDING_IDENTITY",
            "RATIFIED_DIGEST_BINDINGS",
            "FUTURES_ONLY",
            "BITCOIN_EXCLUDED",
            "OFFLINE_BOUNDARY_ENFORCED",
            "FULL_CANONICAL_CHAIN_WIRED",
            "BACKTEST_RUNTIME_DECISION_PARITY_PASS",
        ],
    }


def materialize_lead_lag_offline_economic_evaluation_scope_ratification_v0(
    *,
    repo_root: Path,
    versioned_binding: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    envelope = dict(versioned_binding or materialize_versioned_hypothesis_binding_v0())
    body: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "ratification_id": RATIFICATION_ID,
        "ratification_version": RATIFICATION_VERSION,
        "scope_classification": SCOPE_CLASSIFICATION,
        "recommended_scope_id": RECOMMENDED_SCOPE_ID,
        "operator_go_ratification_prep": OPERATOR_GO_RATIFICATION_PREP,
        "strategy_id": STRATEGY_ID,
        "strategy_version": STRATEGY_VERSION,
        "hypothesis_id": envelope["hypothesis_id"],
        "score_family_policy": envelope["score_family_policy"],
        "binding_digest": envelope["binding_digest"],
        "dataset_digest": envelope["dataset_digest"],
        "universe_digest": envelope["binding"]["pit_universe_binding"]["universe_digest"],
        "implementation_digest": compute_implementation_digest_v0(),
        "versioned_binding_config": VERSIONED_BINDING_CONFIG_REL_PATH,
        "runner_binding_ref": RUNNER_BINDING_REF,
        "harness_binding_ref": HARNESS_BINDING_REF,
        "offline_economic_evaluation_scope_ratified": OFFLINE_ECONOMIC_EVALUATION_SCOPE_RATIFIED,
        "economic_evaluation_authorized": ECONOMIC_EVALUATION_AUTHORIZED,
        "economic_evaluation_executed": ECONOMIC_EVALUATION_EXECUTED,
        "futures_only": FUTURES_ONLY,
        "bitcoin_direction_allowed": BITCOIN_DIRECTION_ALLOWED,
        "allowed_evaluation_stages": list(ALLOWED_EVALUATION_STAGES),
        "prohibited_actions": list(PROHIBITED_ACTIONS),
        "economic_validity_policy_version": ECONOMIC_VALIDITY_POLICY_VERSION,
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
        "order_effect": ORDER_EFFECT,
        "canonical_serialization_version": CANONICAL_SERIALIZATION_VERSION,
    }
    body["ratification_digest"] = _stable_digest(body)
    return body
