"""Post-PR4940 final research fleet negative evidence terminalization and next material research boundary v0.

Deterministic, fail-closed validation of post-PR4939 current-state binding and next
admissible boundary definition. No economic evaluation, no binding retry, no runtime
or order effect.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

PACKAGE_MARKER = (
    "POST_PR4940_FINAL_RESEARCH_FLEET_NEGATIVE_EVIDENCE_TERMINALIZATION_AND_"
    "NEXT_MATERIAL_RESEARCH_BOUNDARY_V0=true"
)

SCHEMA_VERSION = (
    "post_pr4940_final_research_fleet_negative_evidence_terminalization_and_"
    "next_material_research_boundary.v0"
)
SCOPE_ID = (
    "POST_PR4940_FINAL_RESEARCH_FLEET_NEGATIVE_EVIDENCE_TERMINALIZATION_AND_"
    "NEXT_MATERIAL_RESEARCH_BOUNDARY_V0"
)
CONFIG_REL_PATH = (
    "config/research/post_pr4940_final_research_fleet_negative_evidence_terminalization_"
    "and_next_material_research_boundary_v0.json"
)
GO_TOKEN = (
    "GO_PR4940_FINAL_FLEET_TERMINALIZATION_AND_NEXT_MATERIAL_RESEARCH_BOUNDARY_"
    "NO_EVAL_NO_RUNTIME_AUTHORITY_V0"
)
PROCESS_CLASSIFICATION = (
    "POST_PR4940_FINAL_RESEARCH_FLEET_NEGATIVE_EVIDENCE_TERMINALIZATION_AND_"
    "NEXT_MATERIAL_RESEARCH_BOUNDARY_NO_EVAL_V0"
)
SCOPE_CLASSIFICATION = (
    "FINAL_RESEARCH_FLEET_NEGATIVE_EVIDENCE_TERMINALIZATION_AND_NEXT_MATERIAL_RESEARCH_"
    "BOUNDARY_NO_EVAL_NO_RUNTIME_AUTHORITY_V0"
)
VERDICT = "NEGATIVE_EVIDENCE_TERMINALIZED_CURRENT_STATE_BOUND"
NEXT_ADMISSIBLE_BOUNDARY = (
    "MATERIAL_DIFFERENT_OFFLINE_ONLY_RESEARCH_SCOPE_DISCOVERY_OR_RATIFICATION_ONLY_NO_EVAL"
)
POST_MERGE_HEAD = "543d792d5cf78b382ed7cf29d9bf356274116447"
FINAL_RESEARCH_FLEET = ("trend_following", "bollinger_bands", "momentum_1h")
EXPECTED_CANDIDATE_RESULTS = {
    "trend_following": "FAIL",
    "bollinger_bands": "FAIL",
    "momentum_1h": "FAIL",
}

REQUIRED_CONTRACT_FLAGS: tuple[tuple[str, Any], ...] = (
    ("scope_definition_only", True),
    ("current_state_binding_only", True),
    ("offline_only", True),
    ("economic_evaluation_authorized", False),
    ("economic_evaluation_executed", False),
    ("evaluation_executed", False),
    ("runtime_authority_touched", False),
    ("promotion_granted", False),
    ("unchanged_retry_allowed", False),
    ("negative_evidence_terminal_for_unchanged_bindings", True),
    ("economic_validity_offline_gate_pass", False),
    ("runtime_rewire_admissible", False),
    ("live_authorized", False),
    ("no_runtime_authority", True),
    ("next_admissible_boundary_placeholder_only", True),
)


@dataclass(frozen=True)
class BoundaryValidationResultV0:
    valid: bool
    reasons: tuple[str, ...]


def validate_boundary_config_v0(
    config: Mapping[str, Any],
    *,
    repo_root: Path | None = None,
) -> BoundaryValidationResultV0:
    reasons: list[str] = []

    if config.get("scope_id") != SCOPE_ID:
        reasons.append("UNEXPECTED_SCOPE_ID")
    if config.get("go_token") != GO_TOKEN:
        reasons.append("UNEXPECTED_GO_TOKEN")
    if config.get("verdict") != VERDICT:
        reasons.append("UNEXPECTED_VERDICT")
    if config.get("process_classification") != PROCESS_CLASSIFICATION:
        reasons.append("UNEXPECTED_PROCESS_CLASSIFICATION")
    if config.get("scope_classification") != SCOPE_CLASSIFICATION:
        reasons.append("UNEXPECTED_SCOPE_CLASSIFICATION")
    if config.get("next_admissible_boundary") != NEXT_ADMISSIBLE_BOUNDARY:
        reasons.append("UNEXPECTED_NEXT_ADMISSIBLE_BOUNDARY")
    if config.get("post_merge_head") != POST_MERGE_HEAD:
        reasons.append("UNEXPECTED_POST_MERGE_HEAD")
    if config.get("aggregate_fleet_verdict") != "FLEET_ECONOMIC_VALIDITY_FAIL":
        reasons.append("UNEXPECTED_AGGREGATE_FLEET_VERDICT")

    candidate_results = config.get("candidate_results", {})
    if candidate_results != EXPECTED_CANDIDATE_RESULTS:
        reasons.append("CANDIDATE_RESULTS_MISMATCH")

    fleet = config.get("final_research_fleet", [])
    if list(fleet) != list(FINAL_RESEARCH_FLEET):
        reasons.append("FINAL_RESEARCH_FLEET_MISMATCH")

    for field, expected in REQUIRED_CONTRACT_FLAGS:
        if config.get(field) is not expected:
            reasons.append(f"CONTRACT_FLAG_MISMATCH:{field}")

    exclusions = config.get("terminal_failed_binding_exclusions", [])
    if not isinstance(exclusions, list) or len(exclusions) != 3:
        reasons.append("TERMINAL_FAILED_BINDING_EXCLUSIONS_COUNT_MISMATCH")
    else:
        for entry in exclusions:
            if entry.get("retry_unchanged_binding_allowed") is not False:
                reasons.append(
                    f"RETRY_ALLOWED_FOR_TERMINAL_BINDING:{entry.get('canonical_candidate_identifier')}"
                )
            if entry.get("terminal_verdict") != "FAIL":
                reasons.append(
                    f"UNEXPECTED_TERMINAL_VERDICT:{entry.get('canonical_candidate_identifier')}"
                )

    blocked = set(config.get("blocked_actions", []))
    for forbidden in (
        "THRESHOLD_LOWERING",
        "RESULT_RESCUE",
        "PARAMETER_RESCUE",
        "UNCHANGED_BINDING_RETRY",
        "EVALUATION_EXECUTION_IN_THIS_SCOPE",
        "RUNTIME_REWIRE",
        "LIVE",
        "ORDERS",
    ):
        if forbidden not in blocked:
            reasons.append(f"MISSING_BLOCKED_ACTION:{forbidden}")

    if repo_root is not None:
        config_path = repo_root / CONFIG_REL_PATH
        if not config_path.is_file():
            reasons.append("CONFIG_OWNER_MISSING")

    return BoundaryValidationResultV0(valid=not reasons, reasons=tuple(reasons))


def load_boundary_config_v0(repo_root: Path) -> dict[str, Any]:
    payload = json.loads((repo_root / CONFIG_REL_PATH).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"not_object:{CONFIG_REL_PATH}")
    return payload


__all__ = [
    "CONFIG_REL_PATH",
    "EXPECTED_CANDIDATE_RESULTS",
    "FINAL_RESEARCH_FLEET",
    "GO_TOKEN",
    "NEXT_ADMISSIBLE_BOUNDARY",
    "POST_MERGE_HEAD",
    "PROCESS_CLASSIFICATION",
    "SCOPE_CLASSIFICATION",
    "SCOPE_ID",
    "VERDICT",
    "BoundaryValidationResultV0",
    "load_boundary_config_v0",
    "validate_boundary_config_v0",
]
