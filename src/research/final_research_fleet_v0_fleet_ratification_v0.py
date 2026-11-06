"""Final Research Fleet v0 fleet ratification record.

Deterministic fleet-level ratification envelope referencing versioned candidate
bindings, binding completion, and offline evaluation scope ratification.
Research-only; no economic evaluation execution or authority effect.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

from src.research.final_research_fleet_offline_economic_evaluation_scope_ratification_v0 import (
    AUTHORITY_EFFECT as SCOPE_AUTHORITY_EFFECT,
    CONFIG_REL_PATH as SCOPE_CONFIG_REL_PATH,
    ECONOMIC_EVALUATION_AUTHORIZED,
    ECONOMIC_EVALUATION_SCOPE_RATIFIED,
    FINAL_RESEARCH_FLEET_BINDING_READY,
    NEW_CANDIDATES_RATIFIED,
    OFFLINE_ECONOMIC_EVALUATION_SCOPE_RATIFIED,
    ORDER_EFFECT as SCOPE_ORDER_EFFECT,
    RUNTIME_EFFECT as SCOPE_RUNTIME_EFFECT,
    materialize_final_research_fleet_offline_economic_evaluation_scope_ratification_v0,
    validate_final_research_fleet_offline_economic_evaluation_scope_ratification_v0,
    ValidationVerdict as ScopeValidationVerdict,
)
from src.research.final_research_fleet_v0_versioned_binding_manifest_contract_v0 import (
    FLEET_CANDIDATES,
    FLEET_ID,
    FLEET_VERSION,
    OPERATOR_RATIFICATION_REF,
)
from src.research.final_research_fleet_versioned_binding_completion_v0 import (
    AUTHORITY_EFFECT as BINDING_AUTHORITY_EFFECT,
    COMPLETION_ID,
    CONFIG_REL_PATH as BINDING_CONFIG_REL_PATH,
    ORDER_EFFECT as BINDING_ORDER_EFFECT,
    RUNTIME_EFFECT as BINDING_RUNTIME_EFFECT,
    canonical_candidate_identifier,
    validate_final_research_fleet_versioned_binding_completion_v0,
    ValidationVerdict as BindingValidationVerdict,
)

PACKAGE_MARKER = "FINAL_RESEARCH_FLEET_V0_FLEET_RATIFICATION_V0=true"
SCHEMA_VERSION = "final_research_fleet_v0_fleet_ratification.v0"
RATIFICATION_ID = "final_research_fleet_v0_fleet_ratification_v0"
CONFIG_REL_PATH = "config/research/final_research_fleet_v0_fleet_ratification_v0.json"

OPERATOR_FLEET_RATIFICATION_REF = (
    "bounded_final_research_fleet_versioned_bindings_and_offline_evaluation_scope_"
    "ratification_v0_20260703T123000Z"
)

NEXT_CANONICAL_STEP = "EXECUTE_BOUNDED_FINAL_RESEARCH_FLEET_OFFLINE_ECONOMIC_EVALUATION_V0"


class ValidationVerdict(str, Enum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class FleetRatificationValidationResultV0:
    verdict: ValidationVerdict
    valid: bool
    fail_reasons: tuple[str, ...]


def _stable_digest(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def compute_implementation_digest_v0() -> str:
    return _stable_digest(
        {
            "module": "final_research_fleet_v0_fleet_ratification_v0",
            "schema_version": SCHEMA_VERSION,
        }
    )


def compute_fleet_ratification_digest_v0(record: Mapping[str, Any]) -> str:
    body = dict(record)
    body.pop("fleet_ratification_digest", None)
    return hashlib.sha256(
        json.dumps(body, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest()


def materialize_final_research_fleet_v0_fleet_ratification_v0(
    *,
    repo_root: Path,
    fleet_binding_completion: Mapping[str, Any],
) -> dict[str, Any]:
    binding_validation = validate_final_research_fleet_versioned_binding_completion_v0(
        fleet_binding_completion,
        repo_root=repo_root,
        require_ready_for_eval=True,
    )
    if binding_validation.verdict != BindingValidationVerdict.ACCEPTED:
        raise ValueError(f"binding_completion_invalid:{binding_validation.fail_reasons}")

    scope_ratification = (
        materialize_final_research_fleet_offline_economic_evaluation_scope_ratification_v0(
            repo_root=repo_root,
            fleet_binding_completion=fleet_binding_completion,
        )
    )
    scope_validation = (
        validate_final_research_fleet_offline_economic_evaluation_scope_ratification_v0(
            scope_ratification,
            repo_root=repo_root,
            expected_fleet_binding_completion=fleet_binding_completion,
        )
    )
    if scope_validation.verdict != ScopeValidationVerdict.ACCEPTED:
        raise ValueError(f"scope_ratification_invalid:{scope_validation.fail_reasons}")

    candidate_records = []
    for strategy_id, strategy_version in FLEET_CANDIDATES:
        candidate = next(
            item
            for item in fleet_binding_completion["candidates"]
            if item["strategy_id"] == strategy_id and item["strategy_version"] == strategy_version
        )
        candidate_records.append(
            {
                "canonical_candidate_identifier": canonical_candidate_identifier(
                    strategy_id, strategy_version
                ),
                "strategy_id": strategy_id,
                "strategy_version": strategy_version,
                "binding_semantic_digest": candidate["binding_semantic_digest"],
                "binding_status": candidate["binding_status"],
                "ratification_status": "BINDINGS_RATIFIED",
                "ratified": True,
                "operator_ratification_ref": OPERATOR_RATIFICATION_REF,
                "source_config_ref": candidate["source_config_ref"],
                "reason_codes": list(candidate.get("reason_codes") or []),
            }
        )

    record: dict[str, Any] = {
        "artifact_kind": "final_research_fleet_v0_fleet_ratification",
        "schema_version": SCHEMA_VERSION,
        "ratification_id": RATIFICATION_ID,
        "fleet_id": FLEET_ID,
        "fleet_version": FLEET_VERSION,
        "operator_fleet_ratification_ref": OPERATOR_FLEET_RATIFICATION_REF,
        "fleet_binding_completion_ref": BINDING_CONFIG_REL_PATH,
        "fleet_binding_completion_digest": fleet_binding_completion["completion_digest"],
        "offline_evaluation_scope_ref": SCOPE_CONFIG_REL_PATH,
        "offline_evaluation_scope_digest": scope_ratification["ratification_digest"],
        "candidate_ratification_records": candidate_records,
        "final_research_fleet_binding_ready": FINAL_RESEARCH_FLEET_BINDING_READY,
        "new_candidates_ratified": NEW_CANDIDATES_RATIFIED,
        "offline_economic_evaluation_scope_ratified": OFFLINE_ECONOMIC_EVALUATION_SCOPE_RATIFIED,
        "economic_evaluation_scope_ratified": ECONOMIC_EVALUATION_SCOPE_RATIFIED,
        "economic_evaluation_authorized": ECONOMIC_EVALUATION_AUTHORIZED,
        "economic_evaluation_executed": False,
        "economic_validity_offline_gate_pass": False,
        "runtime_rewire_admissible": False,
        "promotion_eligible": False,
        "next_canonical_step": NEXT_CANONICAL_STEP,
        "authority_effect": BINDING_AUTHORITY_EFFECT,
        "runtime_effect": BINDING_RUNTIME_EFFECT,
        "order_effect": BINDING_ORDER_EFFECT,
        "scope_authority_effect": SCOPE_AUTHORITY_EFFECT,
        "scope_runtime_effect": SCOPE_RUNTIME_EFFECT,
        "scope_order_effect": SCOPE_ORDER_EFFECT,
        "system_constraints": {
            "futures_only": True,
            "bitcoin_direction_allowed": False,
            "spot_allowed": False,
            "synthetic_spot_allowed": False,
        },
        "binding_completion_id": COMPLETION_ID,
        "implementation_digest": compute_implementation_digest_v0(),
        "non_authorizing": True,
        "research_binding_only": True,
    }
    record["fleet_ratification_digest"] = compute_fleet_ratification_digest_v0(record)
    return record


def validate_final_research_fleet_v0_fleet_ratification_v0(
    record: Mapping[str, Any],
    *,
    fleet_binding_completion: Mapping[str, Any],
    scope_ratification: Mapping[str, Any],
) -> FleetRatificationValidationResultV0:
    reasons: list[str] = []
    if record.get("schema_version") != SCHEMA_VERSION:
        reasons.append("UNKNOWN_SCHEMA_VERSION")
    if record.get("fleet_binding_completion_digest") != fleet_binding_completion.get(
        "completion_digest"
    ):
        reasons.append("FLEET_BINDING_COMPLETION_DIGEST_MISMATCH")
    if record.get("offline_evaluation_scope_digest") != scope_ratification.get(
        "ratification_digest"
    ):
        reasons.append("OFFLINE_EVALUATION_SCOPE_DIGEST_MISMATCH")
    if record.get("final_research_fleet_binding_ready") is not True:
        reasons.append("FINAL_RESEARCH_FLEET_BINDING_READY_FALSE")
    if record.get("new_candidates_ratified") is not True:
        reasons.append("NEW_CANDIDATES_RATIFIED_FALSE")
    if record.get("economic_evaluation_scope_ratified") is not True:
        reasons.append("ECONOMIC_EVALUATION_SCOPE_RATIFIED_FALSE")
    if record.get("economic_evaluation_authorized") is not False:
        reasons.append("ECONOMIC_EVALUATION_AUTHORIZED_MUST_BE_FALSE")
    if record.get("economic_evaluation_executed") is not False:
        reasons.append("ECONOMIC_EVALUATION_EXECUTED_MUST_BE_FALSE")
    if len(record.get("candidate_ratification_records") or []) != len(FLEET_CANDIDATES):
        reasons.append("CANDIDATE_COUNT_MISMATCH")
    expected_digest = compute_fleet_ratification_digest_v0(record)
    if record.get("fleet_ratification_digest") != expected_digest:
        reasons.append("WRONG_FLEET_RATIFICATION_DIGEST")
    if reasons:
        return FleetRatificationValidationResultV0(
            verdict=ValidationVerdict.REJECTED,
            valid=False,
            fail_reasons=tuple(dict.fromkeys(reasons)),
        )
    return FleetRatificationValidationResultV0(
        verdict=ValidationVerdict.ACCEPTED,
        valid=True,
        fail_reasons=(),
    )


def serialize_fleet_ratification_artifact_json_v0(record: Mapping[str, Any]) -> str:
    return json.dumps(dict(record), indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def write_fleet_ratification_artifact_v0(
    repo_root: Path,
    *,
    fleet_binding_completion: Mapping[str, Any],
) -> Path:
    record = materialize_final_research_fleet_v0_fleet_ratification_v0(
        repo_root=repo_root,
        fleet_binding_completion=fleet_binding_completion,
    )
    scope_ratification = (
        materialize_final_research_fleet_offline_economic_evaluation_scope_ratification_v0(
            repo_root=repo_root,
            fleet_binding_completion=fleet_binding_completion,
        )
    )
    validation = validate_final_research_fleet_v0_fleet_ratification_v0(
        record,
        fleet_binding_completion=fleet_binding_completion,
        scope_ratification=scope_ratification,
    )
    if validation.verdict != ValidationVerdict.ACCEPTED:
        raise ValueError(f"fleet_ratification_validation_failed:{validation.fail_reasons}")
    config_path = repo_root / CONFIG_REL_PATH
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(serialize_fleet_ratification_artifact_json_v0(record), encoding="utf-8")
    return config_path
