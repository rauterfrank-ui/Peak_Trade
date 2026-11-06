"""Cross-sectional MA-crossover panel rank-rotation v0 binding ratification v0."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

from src.research.cross_sectional_ma_crossover_panel_rank_rotation_v0_ranking_semantics_binding_validator_v0 import (
    ValidationVerdict,
    validate_ma_crossover_panel_rank_rotation_ranking_semantics_binding_v0,
)
from src.research.cross_sectional_ma_crossover_panel_rank_rotation_v0_versioned_research_binding_v0 import (
    AUTHORITY_EFFECT,
    CONFIG_REL_PATH as VERSIONED_BINDING_CONFIG_REL_PATH,
    OPERATOR_GO_BINDING_RATIFICATION,
    OPERATOR_GO_ECONOMIC_EVALUATION,
    ORDER_EFFECT,
    RUNTIME_EFFECT,
    SOURCE_CLOSEOUT_BUNDLE,
    STRATEGY_ID,
    STRATEGY_VERSION,
    materialize_versioned_research_binding_v0,
)

PACKAGE_MARKER = "CROSS_SECTIONAL_MA_CROSSOVER_PANEL_RANK_ROTATION_V0_BINDING_RATIFICATION_V0=true"
SCHEMA_VERSION = "cross_sectional_ma_crossover_panel_rank_rotation_v0_binding_ratification.v0"
RATIFICATION_ID = "cross_sectional_ma_crossover_panel_rank_rotation_v0_binding_ratification_v0"
CONFIG_REL_PATH = (
    "config/research/"
    "cross_sectional_ma_crossover_panel_rank_rotation_v0_binding_ratification_v0.json"
)

SCOPE_CLASSIFICATION = (
    "BOUNDED_FUTURES_ONLY_VERSIONED_BINDING_RATIFICATION_V0_NO_EVAL_NO_RUNTIME_AUTHORITY"
)
RESEARCH_SCOPE_DEFINITION_RATIFIED = True
BINDING_RATIFIED = True
ALL_REQUIRED_BINDINGS_RATIFIED = True
OFFLINE_ECONOMIC_EVALUATION_SCOPE_RATIFIED = True
ECONOMIC_EVALUATION_AUTHORIZED = False
ECONOMIC_EVALUATION_EXECUTED = False
DATASET_MATERIALIZED = True


class ValidationVerdictEnum(str, Enum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class BindingRatificationValidationResultV0:
    verdict: ValidationVerdictEnum
    fail_reasons: tuple[str, ...]


def _stable_digest(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def serialize_ratification_canonical_v0(obj: Mapping[str, Any]) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str) + "\n"


def materialize_binding_ratification_v0(*, repo_root: Path) -> dict[str, Any]:
    versioned_binding = materialize_versioned_research_binding_v0()
    ranking_binding = versioned_binding["binding"]
    validation = validate_ma_crossover_panel_rank_rotation_ranking_semantics_binding_v0(
        ranking_binding
    )
    if validation.verdict != ValidationVerdict.ACCEPTED_COMPLETE:
        raise ValueError(f"BINDING_VALIDATION_FAILED:{validation.fail_reasons}")

    body: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "ratification_id": RATIFICATION_ID,
        "scope_classification": SCOPE_CLASSIFICATION,
        "strategy_id": STRATEGY_ID,
        "strategy_version": STRATEGY_VERSION,
        "research_scope": f"{STRATEGY_ID}/{STRATEGY_VERSION}",
        "operator_go_token": OPERATOR_GO_BINDING_RATIFICATION,
        "operator_go_token_economic_evaluation": OPERATOR_GO_ECONOMIC_EVALUATION,
        "research_scope_definition_ratified": RESEARCH_SCOPE_DEFINITION_RATIFIED,
        "binding_ratified": BINDING_RATIFIED,
        "all_required_bindings_ratified": ALL_REQUIRED_BINDINGS_RATIFIED,
        "offline_economic_evaluation_scope_ratified": OFFLINE_ECONOMIC_EVALUATION_SCOPE_RATIFIED,
        "dataset_materialized": DATASET_MATERIALIZED,
        "economic_evaluation_authorized": ECONOMIC_EVALUATION_AUTHORIZED,
        "economic_evaluation_executed": ECONOMIC_EVALUATION_EXECUTED,
        "candidate_binding_ref": VERSIONED_BINDING_CONFIG_REL_PATH,
        "binding_digest": versioned_binding["binding_digest"],
        "config_digest": versioned_binding["config_digest"],
        "data_digest": versioned_binding["data_digest"],
        "implementation_digest": versioned_binding["implementation_digest"],
        "material_difference_digest": versioned_binding["material_difference_digest"],
        "source_closeout_bundle_ref": SOURCE_CLOSEOUT_BUNDLE,
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
        "order_effect": ORDER_EFFECT,
        "next_action": (
            "AWAIT_OPERATOR_OFFLINE_ECONOMIC_EVALUATION_GO_CROSS_SECTIONAL_MA_CROSSOVER_PANEL_RANK_ROTATION_V0"
        ),
        "versioned_binding": versioned_binding,
    }
    body["ratification_digest"] = _stable_digest(
        {k: v for k, v in body.items() if k not in {"ratification_digest", "versioned_binding"}}
    )
    return body


def validate_binding_ratification_v0(
    ratification: Mapping[str, Any],
) -> BindingRatificationValidationResultV0:
    fail_reasons: list[str] = []
    if ratification.get("schema_version") != SCHEMA_VERSION:
        fail_reasons.append("INVALID_SCHEMA_VERSION")
    if ratification.get("binding_ratified") is not True:
        fail_reasons.append("BINDING_NOT_RATIFIED")
    if ratification.get("all_required_bindings_ratified") is not True:
        fail_reasons.append("REQUIRED_BINDINGS_INCOMPLETE")
    if ratification.get("economic_evaluation_executed") is not False:
        fail_reasons.append("ECONOMIC_EVALUATION_MUST_NOT_BE_EXECUTED")
    if ratification.get("operator_go_token") != OPERATOR_GO_BINDING_RATIFICATION:
        fail_reasons.append("OPERATOR_GO_MISMATCH")
    envelope = ratification.get("versioned_binding", {})
    if envelope.get("validation_verdict") != ValidationVerdict.ACCEPTED_COMPLETE.value:
        fail_reasons.append("VERSIONED_BINDING_VALIDATION_NOT_COMPLETE")
    if fail_reasons:
        return BindingRatificationValidationResultV0(
            verdict=ValidationVerdictEnum.REJECTED,
            fail_reasons=tuple(fail_reasons),
        )
    return BindingRatificationValidationResultV0(
        verdict=ValidationVerdictEnum.ACCEPTED,
        fail_reasons=(),
    )
