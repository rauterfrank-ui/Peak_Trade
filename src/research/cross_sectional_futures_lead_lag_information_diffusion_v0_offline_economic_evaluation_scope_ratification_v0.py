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
