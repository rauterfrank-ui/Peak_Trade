"""Post-no-pass sparse signal zero trade offline economic evaluation scope ratification v0.

Ratifies offline evaluation contract for sparse-signal v2 fleet bindings only.
Does not execute backtest, walk-forward, Monte Carlo, stress, or parameter sensitivity.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

from src.backtest.economic_validity_policy_v1 import ECONOMIC_VALIDITY_POLICY_VERSION
from src.research.final_research_fleet_versioned_binding_completion_v0 import (
    canonical_candidate_identifier,
)
from src.research.panel_sequential_signal_density_research_adapter_v0 import ADAPTER_KIND
from src.research.post_no_pass_sparse_signal_zero_trade_versioned_binding_completion_v0 import (
    BINDING_CLASS,
    CONFIG_REL_PATH as SPARSE_BINDING_CONFIG_REL_PATH,
    PANEL_DATA_DIGEST,
    PANEL_STAGING_ROOT,
    RESEARCH_CANDIDATES,
    STRATEGY_VERSION,
    ValidationVerdict as BindingValidationVerdict,
    validate_post_no_pass_sparse_signal_zero_trade_versioned_binding_completion_v0,
)

PACKAGE_MARKER = (
    "POST_NO_PASS_SPARSE_SIGNAL_ZERO_TRADE_OFFLINE_ECONOMIC_EVALUATION_SCOPE_RATIFICATION_V0=true"
)

SCHEMA_VERSION = (
    "post_no_pass_sparse_signal_zero_trade_offline_economic_evaluation_scope_ratification.v0"
)
RATIFICATION_ID = (
    "post_no_pass_sparse_signal_zero_trade_offline_economic_evaluation_scope_ratification_v0"
)
RATIFICATION_VERSION = "v0"
CONFIG_REL_PATH = (
    "config/research/"
    "post_no_pass_sparse_signal_zero_trade_offline_economic_evaluation_scope_ratification_v0.json"
)
CANONICAL_SERIALIZATION_VERSION = "research_scope_ratification_canonical_json_v1"
SCOPE_CLASSIFICATION = (
    "POST_NO_PASS_SPARSE_SIGNAL_ZERO_TRADE_OFFLINE_ECONOMIC_EVALUATION_SCOPE_RATIFICATION_V0"
)

AUTHORITY_EFFECT = "NONE"
RUNTIME_EFFECT = "NONE"
ORDER_EFFECT = "NONE"
OFFLINE_ECONOMIC_EVALUATION_SCOPE_RATIFIED = True
ECONOMIC_EVALUATION_AUTHORIZED = False
ECONOMIC_EVALUATION_EXECUTED = False
EVALUATION_AUTHORIZATION_STATUS = "NOT_AUTHORIZED_PENDING_SEPARATE_OFFLINE_EXECUTION_GO"

REASON_RATIFICATION_NOT_OBJECT = "RATIFICATION_NOT_OBJECT"
REASON_SCHEMA_MISMATCH = "SCHEMA_VERSION_MISMATCH"
REASON_SCOPE_NOT_RATIFIED = "OFFLINE_ECONOMIC_EVALUATION_SCOPE_NOT_RATIFIED"
REASON_BINDING_DIGEST_MISMATCH = "FLEET_BINDING_DIGEST_MISMATCH"
REASON_CANDIDATE_SET_MISMATCH = "CANDIDATE_SET_MISMATCH"
REASON_EVALUATION_ALREADY_EXECUTED = "ECONOMIC_EVALUATION_ALREADY_EXECUTED"
REASON_WRONG_RATIFICATION_DIGEST = "WRONG_RATIFICATION_DIGEST"


class ValidationVerdictEnum(str, Enum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class ScopeRatificationValidationResultV0:
    verdict: ValidationVerdictEnum
    fail_reasons: tuple[str, ...]


def _stable_digest(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def compute_ratification_digest_v0(ratification: Mapping[str, Any]) -> str:
    body = {key: value for key, value in ratification.items() if key != "ratification_digest"}
    return _stable_digest(body)


def materialize_scope_ratification_v0(
    *,
    sparse_binding_completion: Mapping[str, Any],
) -> dict[str, Any]:
    candidate_refs = [
        canonical_candidate_identifier(strategy_id, STRATEGY_VERSION)
        for strategy_id in RESEARCH_CANDIDATES
    ]
    candidate_binding_digests = {
        str(item["canonical_candidate_identifier"]): str(item["binding_semantic_digest"])
        for item in sparse_binding_completion.get("candidates", ())
        if isinstance(item, Mapping)
    }
    first_candidate = sparse_binding_completion["candidates"][0]
    ratification_body: dict[str, Any] = {
        "allowed_after_this_ratification": False,
        "authority_effect": AUTHORITY_EFFECT,
        "binding_class": BINDING_CLASS,
        "candidate_binding_digests": candidate_binding_digests,
        "candidate_refs": candidate_refs,
        "common_dataset_policy_ref": first_candidate["dataset_binding"],
        "common_instrument_policy_ref": first_candidate["instrument_binding"],
        "common_period_policy_ref": first_candidate["period_binding"],
        "economic_evaluation_authorized": ECONOMIC_EVALUATION_AUTHORIZED,
        "economic_evaluation_executed": ECONOMIC_EVALUATION_EXECUTED,
        "economic_policy_binding": first_candidate["economic_policy_binding"],
        "economic_policy_version": ECONOMIC_VALIDITY_POLICY_VERSION,
        "evaluation_authorization_status": EVALUATION_AUTHORIZATION_STATUS,
        "evaluation_execution_performed": False,
        "evaluation_modules_invoked": [],
        "execution_model_binding": first_candidate["execution_model_binding"],
        "fee_model_binding": first_candidate["fee_model_binding"],
        "fleet_binding_digest": sparse_binding_completion["completion_digest"],
        "fleet_binding_ref": {
            "completion_digest": sparse_binding_completion["completion_digest"],
            "completion_id": sparse_binding_completion["completion_id"],
            "schema_version": sparse_binding_completion["schema_version"],
        },
        "funding_model_binding": first_candidate["funding_model_binding"],
        "futures_only": sparse_binding_completion["futures_only"],
        "implementation_digest": sparse_binding_completion["implementation_digest"],
        "offline_economic_evaluation_scope_ratified": OFFLINE_ECONOMIC_EVALUATION_SCOPE_RATIFIED,
        "order_effect": ORDER_EFFECT,
        "panel_data_digest": PANEL_DATA_DIGEST,
        "panel_staging_root": PANEL_STAGING_ROOT,
        "prohibited_actions": list(sparse_binding_completion.get("blocked_actions", ())),
        "ratification_class": "SPARSE_SIGNAL_ZERO_TRADE_V2",
        "ratification_id": RATIFICATION_ID,
        "ratification_version": RATIFICATION_VERSION,
        "ratified_scope_id": SCOPE_CLASSIFICATION,
        "required_adapter_kind": ADAPTER_KIND,
        "runtime_effect": RUNTIME_EFFECT,
        "runtime_rewire_admissible": False,
        "schema_version": SCHEMA_VERSION,
        "scope_classification": SCOPE_CLASSIFICATION,
        "slippage_model_binding": first_candidate["slippage_model_binding"],
        "sparse_binding_config_ref": SPARSE_BINDING_CONFIG_REL_PATH,
        "strategy_version": STRATEGY_VERSION,
    }
    ratification_body["ratification_digest"] = compute_ratification_digest_v0(ratification_body)
    return ratification_body


def serialize_scope_ratification_canonical_v0(ratification: Mapping[str, Any]) -> str:
    return json.dumps(ratification, indent=2, sort_keys=True) + "\n"


def validate_scope_ratification_v0(
    ratification: Any,
    *,
    sparse_binding_completion: Mapping[str, Any],
) -> ScopeRatificationValidationResultV0:
    reasons: list[str] = []
    if not isinstance(ratification, Mapping):
        return ScopeRatificationValidationResultV0(
            verdict=ValidationVerdictEnum.REJECTED,
            fail_reasons=(REASON_RATIFICATION_NOT_OBJECT,),
        )
    if ratification.get("schema_version") != SCHEMA_VERSION:
        reasons.append(REASON_SCHEMA_MISMATCH)
    if ratification.get("offline_economic_evaluation_scope_ratified") is not True:
        reasons.append(REASON_SCOPE_NOT_RATIFIED)
    if ratification.get("economic_evaluation_executed") is not False:
        reasons.append(REASON_EVALUATION_ALREADY_EXECUTED)
    if str(ratification.get("fleet_binding_digest", "")) != str(
        sparse_binding_completion.get("completion_digest", "")
    ):
        reasons.append(REASON_BINDING_DIGEST_MISMATCH)
    expected_refs = [
        canonical_candidate_identifier(strategy_id, STRATEGY_VERSION)
        for strategy_id in RESEARCH_CANDIDATES
    ]
    if sorted(ratification.get("candidate_refs") or []) != sorted(expected_refs):
        reasons.append(REASON_CANDIDATE_SET_MISMATCH)
    expected_digest = compute_ratification_digest_v0(ratification)
    if ratification.get("ratification_digest") != expected_digest:
        reasons.append(REASON_WRONG_RATIFICATION_DIGEST)
    binding_validation = (
        validate_post_no_pass_sparse_signal_zero_trade_versioned_binding_completion_v0(
            sparse_binding_completion
        )
    )
    if binding_validation.verdict != BindingValidationVerdict.ACCEPTED:
        reasons.extend(binding_validation.fail_reasons)
    if reasons:
        return ScopeRatificationValidationResultV0(
            verdict=ValidationVerdictEnum.REJECTED,
            fail_reasons=tuple(reasons),
        )
    return ScopeRatificationValidationResultV0(
        verdict=ValidationVerdictEnum.ACCEPTED,
        fail_reasons=(),
    )


def validate_scope_ratification_for_execution_v0(
    ratification: Mapping[str, Any],
    *,
    sparse_binding_completion: Mapping[str, Any],
) -> tuple[bool, tuple[str, ...]]:
    result = validate_scope_ratification_v0(
        ratification,
        sparse_binding_completion=sparse_binding_completion,
    )
    return result.verdict is ValidationVerdictEnum.ACCEPTED, result.fail_reasons


__all__ = [
    "CONFIG_REL_PATH",
    "SCOPE_CLASSIFICATION",
    "materialize_scope_ratification_v0",
    "validate_scope_ratification_for_execution_v0",
    "validate_scope_ratification_v0",
    "compute_ratification_digest_v0",
]
