"""Cross-sectional funding-rate delta momentum v0 offline evaluation scope ratification v0."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

from src.backtest.economic_validity_policy_v1 import ECONOMIC_VALIDITY_POLICY_VERSION
from src.research.cross_sectional_funding_rate_delta_momentum_ranking_semantics_binding_validator_v0 import (
    ValidationVerdict,
    validate_funding_rate_delta_momentum_ranking_semantics_binding_v0,
)
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

PACKAGE_MARKER = (
    "CROSS_SECTIONAL_FUNDING_RATE_DELTA_MOMENTUM_V0_OFFLINE_ECONOMIC_EVALUATION_"
    "SCOPE_RATIFICATION_V0=true"
)
SCHEMA_VERSION = "cross_sectional_funding_rate_delta_momentum_v0_offline_economic_evaluation_scope_ratification.v0"
RATIFICATION_ID = (
    "cross_sectional_funding_rate_delta_momentum_v0_offline_evaluation_infrastructure_scope_v0"
)
RATIFICATION_VERSION = "v0"

OFFLINE_EVALUATION_INFRASTRUCTURE_SCOPE_RATIFIED = True
ECONOMIC_EVALUATION_AUTHORIZED = False
ECONOMIC_EVALUATION_EXECUTED = False


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


def materialize_funding_delta_momentum_offline_evaluation_scope_ratification_v0(
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
        "offline_evaluation_infrastructure_scope_ratified": True,
        "economic_evaluation_authorized": False,
        "economic_evaluation_executed": False,
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
        "order_effect": ORDER_EFFECT,
        "futures_only": True,
        "bitcoin_direction_allowed": False,
    }
    body["ratification_digest"] = _stable_digest(body)
    return body


def validate_funding_delta_momentum_offline_evaluation_scope_ratification_v0(
    ratification: Mapping[str, Any],
    *,
    expected_binding: Mapping[str, Any] | None = None,
) -> RatificationValidationResultV0:
    reasons: list[str] = []
    envelope = dict(expected_binding or {})
    if ratification.get("economic_evaluation_authorized") is not False:
        reasons.append("ECONOMIC_EVALUATION_AUTHORIZED_MUST_BE_FALSE")
    if ratification.get("economic_evaluation_executed") is not False:
        reasons.append("ECONOMIC_EVALUATION_EXECUTED_MUST_BE_FALSE")
    if envelope and ratification.get("binding_digest") != envelope.get("binding_digest"):
        reasons.append("BINDING_DIGEST_MISMATCH")
    if ratification.get("economic_policy_binding", {}).get(
        "economic_validity_policy_version"
    ) not in (None, ECONOMIC_VALIDITY_POLICY_VERSION):
        reasons.append("ECONOMIC_POLICY_VERSION_MISMATCH")
    if reasons:
        return RatificationValidationResultV0(
            verdict=ValidationVerdictEnum.REJECTED,
            fail_reasons=tuple(reasons),
        )
    return RatificationValidationResultV0(verdict=ValidationVerdictEnum.ACCEPTED, fail_reasons=())
