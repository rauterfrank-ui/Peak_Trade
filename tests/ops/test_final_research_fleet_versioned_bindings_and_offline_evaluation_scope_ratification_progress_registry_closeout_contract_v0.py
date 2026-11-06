"""Contract tests for historical final research fleet binding closeout snapshot v0."""

from __future__ import annotations

import re

from tests.ops.runbook_progress_registry_contract_helpers_v1 import read_registry

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


def test_historical_closeout_section_records_pass_without_authority_effect() -> None:
    section = _closeout_section(read_registry())
    assert _field_value(section, "STATUS") == "COMPLETE"
    assert _field_value(section, "FINAL_RESEARCH_FLEET") == FINAL_RESEARCH_FLEET
    assert _field_value(section, "FINAL_RESEARCH_FLEET_BINDING_READY") == "true"
    assert _field_value(section, "NEW_CANDIDATES_RATIFIED") == "true"
    assert _field_value(section, "ECONOMIC_EVALUATION_SCOPE_RATIFIED") == "true"
    assert _field_value(section, "ECONOMIC_EVALUATION_AUTHORIZED") == "false"
    assert _field_value(section, "ECONOMIC_EVALUATION_EXECUTED") == "false"
    assert _field_value(section, "HISTORICAL_NEGATIVE_EVIDENCE_MUTATED") == "false"
    assert _field_value(section, "NEXT_CANONICAL_STEP") == NEXT_CANONICAL_STEP
    assert _field_value(section, "RUNTIME_EFFECT") == "NONE"
    assert _field_value(section, "AUTHORITY_EFFECT") == "NONE"
