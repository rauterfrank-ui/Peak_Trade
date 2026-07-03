"""Contract tests for final research fleet binding and scope ratification progress registry closeout v0."""

from __future__ import annotations

import re

from tests.ops.runbook_progress_registry_contract_helpers_v1 import (
    authoritative_field_value,
    read_registry,
)

CLOSEOUT_SECTION_PREFIX = (
    "#### FINAL_RESEARCH_FLEET_VERSIONED_BINDINGS_AND_OFFLINE_EVALUATION_SCOPE_RATIFICATION_V0"
)
NEXT_CANONICAL_STEP = "EXECUTE_BOUNDED_FINAL_RESEARCH_FLEET_OFFLINE_ECONOMIC_EVALUATION_V0"
FINAL_RESEARCH_FLEET = "trend_following,bollinger_bands,momentum_1h"


def _field_value(text: str, field: str) -> str:
    match = re.search(rf"\| `{re.escape(field)}` \| `([^`]*)` \|", text)
    assert match, f"missing registry field: {field}"
    return match.group(1)


def _closeout_section(text: str) -> str:
    start = text.index(CLOSEOUT_SECTION_PREFIX)
    end = text.index(
        "\n#### RUNBOOK_V4_4_RESEARCH_GOVERNANCE_PROGRESS_REGISTRY_RECONCILIATION_V0", start
    )
    return text[start:end]


def test_authoritative_binding_and_scope_flags_pass() -> None:
    assert authoritative_field_value("FINAL_RESEARCH_FLEET_BINDING_READY") == "true"
    assert authoritative_field_value("NEW_CANDIDATES_RATIFIED") == "true"
    assert authoritative_field_value("ECONOMIC_EVALUATION_SCOPE_RATIFIED") == "true"
    assert authoritative_field_value("ECONOMIC_EVALUATION_AUTHORIZED") == "false"
    assert authoritative_field_value("ECONOMIC_VALIDITY_OFFLINE_GATE_PASS") == "false"
    assert authoritative_field_value("PROMOTION_ELIGIBLE") == "false"
    assert authoritative_field_value("RUNTIME_REWIRE_ADMISSIBLE") == "false"


def test_authoritative_next_step_offline_evaluation() -> None:
    assert authoritative_field_value("NEXT_CANONICAL_STEP") == NEXT_CANONICAL_STEP
    assert authoritative_field_value("NEXT_CANONICAL_ACTION") == NEXT_CANONICAL_STEP
    assert authoritative_field_value("GLOBAL_RUNBOOK_NEXT_STEP") == NEXT_CANONICAL_STEP


def test_fleet_selection_unchanged() -> None:
    assert authoritative_field_value("FINAL_RESEARCH_FLEET") == FINAL_RESEARCH_FLEET
    assert authoritative_field_value("NO_NEW_CANDIDATE_HOLD") == "REVOKED"
    assert authoritative_field_value("MULTI_CANDIDATE_RESEARCH_FLEET_ALLOWED") == "true"


def test_closeout_section_records_pass_without_authority_effect() -> None:
    section = _closeout_section(read_registry())
    assert _field_value(section, "STATUS") == "COMPLETE"
    assert _field_value(section, "FINAL_RESEARCH_FLEET_BINDING_READY") == "true"
    assert _field_value(section, "NEW_CANDIDATES_RATIFIED") == "true"
    assert _field_value(section, "ECONOMIC_EVALUATION_SCOPE_RATIFIED") == "true"
    assert _field_value(section, "ECONOMIC_EVALUATION_AUTHORIZED") == "false"
    assert _field_value(section, "ECONOMIC_EVALUATION_EXECUTED") == "false"
    assert _field_value(section, "HISTORICAL_NEGATIVE_EVIDENCE_MUTATED") == "false"
    assert _field_value(section, "NEXT_CANONICAL_STEP") == NEXT_CANONICAL_STEP
    assert _field_value(section, "RUNTIME_EFFECT") == "NONE"
    assert _field_value(section, "AUTHORITY_EFFECT") == "NONE"
