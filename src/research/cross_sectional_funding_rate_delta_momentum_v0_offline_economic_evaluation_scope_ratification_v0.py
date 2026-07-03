"""Cross-sectional funding-rate delta momentum v0 offline economic evaluation scope ratification v0.

Deterministic, fail-closed ratification of bounded offline-only economic evaluation
scope for cross_sectional_funding_rate_delta_momentum/v0. Does not execute evaluation.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

from src.backtest.economic_validity_policy_v1 import ECONOMIC_VALIDITY_POLICY_VERSION
from src.research.cross_sectional_funding_rate_delta_momentum_v0_versioned_research_binding_v0 import (
    AUTHORITY_EFFECT,
    CONFIG_REL_PATH,
    ORDER_EFFECT,
    RUNTIME_EFFECT,
    STRATEGY_ID,
    STRATEGY_VERSION,
    compute_implementation_digest_v0,
    materialize_versioned_research_binding_v0,
)
from src.research.cross_sectional_funding_rate_delta_momentum_ranking_semantics_binding_validator_v0 import (
    ValidationVerdict,
    validate_funding_rate_delta_momentum_ranking_semantics_binding_v0,
)

PACKAGE_MARKER = "CROSS_SECTIONAL_FUNDING_RATE_DELTA_MOMENTUM_V0_OFFLINE_ECONOMIC_EVALUATION_SCOPE_RATIFICATION_V0=true"

SCHEMA_VERSION = "cross_sectional_funding_rate_delta_momentum_v0_offline_economic_evaluation_scope_ratification.v0"
RATIFICATION_ID = "cross_sectional_funding_rate_delta_momentum_v0_offline_economic_evaluation_scope_ratification_v0"
RATIFICATION_VERSION = "v0"
CANONICAL_SERIALIZATION_VERSION = "research_scope_ratification_canonical_json_v1"

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
    "RUNTIME_REWIRE",
    "ORDERS",
    "LIVE",
    "POLICY_THRESHOLD_RETROFIT",
    "DATASET_SUBSTITUTION",
    "PERIOD_BINDING_SUBSTITUTION",
    "PARAMETER_SEARCH",
    "IMPLICIT_ZERO_COST",
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


def materialize_funding_delta_momentum_offline_economic_evaluation_scope_ratification_v0(
    *,
    repo_root: Path,
    versioned_binding: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    envelope = dict(versioned_binding or materialize_versioned_research_binding_v0())
    binding = envelope["binding"]
    validation = validate_funding_rate_delta_momentum_ranking_semantics_binding_v0(binding)
    if not validation.valid or validation.verdict != ValidationVerdict.ACCEPTED_COMPLETE:
        raise ValueError("versioned_binding_not_accepted_complete")

    body: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "ratification_id": RATIFICATION_ID,
        "ratification_version": RATIFICATION_VERSION,
        "strategy_id": STRATEGY_ID,
        "strategy_version": STRATEGY_VERSION,
        "go_token": "GO_BOUNDED_CROSS_SECTIONAL_FUNDING_RATE_DELTA_MOMENTUM_V0_OFFLINE_ECONOMIC_EVALUATION_SCOPE_V0",
        "scope_id": "BOUNDED_CROSS_SECTIONAL_FUNDING_RATE_DELTA_MOMENTUM_V0_OFFLINE_ECONOMIC_EVALUATION_SCOPE_V0",
        "hypothesis_class": "CROSS_SECTIONAL_FUNDING_RATE_DELTA_MOMENTUM_NON_BITCOIN_PERPETUALS_V0",
        "candidate_id": f"{STRATEGY_ID}/{STRATEGY_VERSION}",
        "candidate_binding_ref": CONFIG_REL_PATH,
        "binding_digest": envelope["binding_digest"],
        "config_digest": envelope["config_digest"],
        "data_digest": envelope["data_digest"],
        "implementation_digest": compute_implementation_digest_v0(),
        "parameter_binding": envelope["parameter_binding"],
        "panel_dataset_binding": envelope["panel_dataset_binding"],
        "period_binding": envelope["period_binding"],
        "instrument_binding": envelope["instrument_binding"],
        "cost_execution_binding": envelope["cost_execution_binding"],
        "economic_policy_binding": envelope["economic_policy_binding"],
        "fee_model_binding": envelope["cost_execution_binding"]["fee_model_binding"],
        "slippage_model_binding": envelope["cost_execution_binding"]["slippage_model_binding"],
        "funding_model_binding": envelope["cost_execution_binding"]["funding_model_binding"],
        "execution_model_binding": envelope["cost_execution_binding"]["execution_model_binding"],
        "economic_validity_policy_version": ECONOMIC_VALIDITY_POLICY_VERSION,
        "allowed_evaluation_stages": list(ALLOWED_EVALUATION_STAGES),
        "prohibited_actions": list(PROHIBITED_ACTIONS),
        "offline_economic_evaluation_scope_ratified": OFFLINE_ECONOMIC_EVALUATION_SCOPE_RATIFIED,
        "economic_evaluation_authorized": ECONOMIC_EVALUATION_AUTHORIZED,
        "economic_evaluation_executed": ECONOMIC_EVALUATION_EXECUTED,
        "futures_only": FUTURES_ONLY,
        "bitcoin_direction_allowed": BITCOIN_DIRECTION_ALLOWED,
        "spot_allowed": False,
        "synthetic_spot_allowed": False,
        "runtime_rewire": False,
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
        "order_effect": ORDER_EFFECT,
        "evaluation_authorization_status": "SCOPE_RATIFIED_AWAITING_CANONICAL_EXECUTION",
        "economic_validity_status": "NOT_EVALUATED",
        "reason_codes": [],
        "canonical_serialization_version": CANONICAL_SERIALIZATION_VERSION,
    }
    body["ratification_digest"] = _stable_digest(
        {k: v for k, v in body.items() if k != "ratification_digest"}
    )
    return body


def validate_funding_delta_momentum_offline_economic_evaluation_scope_ratification_v0(
    ratification: Mapping[str, Any],
    *,
    expected_binding: Mapping[str, Any] | None = None,
) -> RatificationValidationResultV0:
    reasons: list[str] = []
    if ratification.get("schema_version") != SCHEMA_VERSION:
        reasons.append("UNKNOWN_SCHEMA_VERSION")
    if ratification.get("offline_economic_evaluation_scope_ratified") is not True:
        reasons.append("SCOPE_NOT_RATIFIED")
    if ratification.get("economic_evaluation_executed") is not False:
        reasons.append("EVALUATION_ALREADY_EXECUTED")
    if ratification.get("authority_effect") != "NONE":
        reasons.append("AUTHORITY_EFFECT_NOT_NONE")
    if ratification.get("runtime_effect") != "NONE":
        reasons.append("RUNTIME_EFFECT_NOT_NONE")
    if ratification.get("futures_only") is not True:
        reasons.append("FUTURES_ONLY_VIOLATION")
    if ratification.get("bitcoin_direction_allowed") is not False:
        reasons.append("BITCOIN_DIRECTION_VIOLATION")

    if expected_binding is not None:
        if ratification.get("binding_digest") != expected_binding.get("binding_digest"):
            reasons.append("BINDING_DIGEST_MISMATCH")
        if ratification.get("data_digest") != expected_binding.get("data_digest"):
            reasons.append("DATA_DIGEST_MISMATCH")

    verdict = ValidationVerdictEnum.ACCEPTED if not reasons else ValidationVerdictEnum.REJECTED
    return RatificationValidationResultV0(verdict=verdict, fail_reasons=tuple(reasons))
