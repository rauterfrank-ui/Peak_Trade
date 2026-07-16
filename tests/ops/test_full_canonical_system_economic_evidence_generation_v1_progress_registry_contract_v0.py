"""Progress registry contract for FULL_CANONICAL_SYSTEM evidence generation v1."""

from __future__ import annotations

import re

from tests.ops.runbook_progress_registry_contract_helpers_v1 import (
    authoritative_field_value,
    read_registry,
)

CLOSEOUT_SECTION_PREFIX = (
    "#### FULL_CANONICAL_SYSTEM_ECONOMIC_EVIDENCE_GENERATION_V1_BINDING_RATIFICATION_V0"
)
GO_TOKEN = "GO_FULL_CANONICAL_SYSTEM_ECONOMIC_EVIDENCE_GENERATION_V1_BINDING_RATIFICATION_V1"
NEXT_STEP = "SEPARATE_OPERATOR_GO_FOR_FULL_CANONICAL_SYSTEM_ECONOMIC_BASELINE_EXECUTION"
EVIDENCE_CLASS = "BOLLINGER_BANDS_V2_FULL_CANONICAL_SYSTEM_ECONOMIC_EVIDENCE_V1"
BINDING_ID = "bollinger_bands_v2_full_canonical_system_economic_binding_v1"
BINDING_DIGEST = "b0b51de225a7e282263c1b00091ccb457612f74df0e817d8dd03efc7af837320"


def _field_value(text: str, field: str) -> str:
    match = re.search(rf"\| `{re.escape(field)}` \| `([^`]*)` \|", text)
    assert match, f"missing registry field: {field}"
    return match.group(1)


def _closeout_section(text: str) -> str:
    start = text.index(CLOSEOUT_SECTION_PREFIX)
    end = text.index("\n---\n\n## PR #4629 Evidence-Drift", start)
    return text[start:end]


class TestFullCanonicalSystemEconomicEvidenceGenerationV1ProgressRegistry:
    def test_authoritative_ratified_not_executed_state(self) -> None:
        assert (
            authoritative_field_value("CURRENT_STATE")
            == "FULL_CANONICAL_SYSTEM_ECONOMIC_EVIDENCE_GENERATION_V1_BINDING_RATIFIED_NOT_EXECUTED"
        )
        assert (
            authoritative_field_value("NEW_ECONOMIC_EVIDENCE_GENERATION_STATUS")
            == "BINDING_RATIFIED_NOT_EXECUTED"
        )
        assert authoritative_field_value("SELECTED_EVIDENCE_CLASS") == EVIDENCE_CLASS
        assert authoritative_field_value("SELECTED_BINDING_ID") == BINDING_ID
        assert authoritative_field_value("SELECTED_BINDING_DIGEST") == BINDING_DIGEST
        assert authoritative_field_value("PR5240_CLOSEOUT_COMPLETE") == "true"
        assert (
            authoritative_field_value("STEP29M_BINDING_ADMISSIBILITY_INVENTORY_COMPLETE") == "true"
        )
        assert authoritative_field_value("NEW_EVIDENCE_CLASS_RATIFIED") == "true"
        assert authoritative_field_value("NEW_VERSIONED_ECONOMIC_BINDING_RATIFIED") == "true"
        assert (
            authoritative_field_value("FULL_CANONICAL_SYSTEM_ECONOMIC_EVIDENCE_GENERATION_V1")
            == "true"
        )

    def test_next_step_requires_separate_execution_go(self) -> None:
        assert authoritative_field_value("NEXT_STEP") == NEXT_STEP
        assert authoritative_field_value("NEXT_CANONICAL_STEP") == NEXT_STEP
        assert authoritative_field_value("NEXT_CANONICAL_ACTION") == NEXT_STEP
        assert authoritative_field_value("GLOBAL_RUNBOOK_NEXT_STEP") == NEXT_STEP

    def test_evaluation_and_runtime_remain_blocked(self) -> None:
        assert authoritative_field_value("ECONOMIC_EVALUATION_AUTHORIZED") == "false"
        assert authoritative_field_value("ECONOMIC_EVALUATION_EXECUTED") == "false"
        assert authoritative_field_value("ECONOMIC_VALIDITY_OFFLINE_GATE_PASS") == "false"
        assert authoritative_field_value("RUNTIME_REWIRE_ADMISSIBLE") == "false"
        assert authoritative_field_value("PROMOTION_ELIGIBLE") == "false"
        assert authoritative_field_value("RUNTIME_EFFECT") == "NONE"
        assert authoritative_field_value("AUTHORITY_EFFECT") == "NONE"
        assert authoritative_field_value("STEP29M_PASS_ADMISSIBLE_BINDING_PRESENT") == "false"
        assert authoritative_field_value("NO_NEW_CANDIDATE_HOLD") == "ACTIVE"
        assert authoritative_field_value("NEW_CANDIDATES_RATIFIED") == "false"
        assert authoritative_field_value("CURRENT_ADMISSIBLE_NEXT_SCOPE") == "NONE"

    def test_closeout_section_fields(self) -> None:
        section = _closeout_section(read_registry())
        assert _field_value(section, "GO_TOKEN") == GO_TOKEN
        assert _field_value(section, "SELECTED_EVIDENCE_CLASS") == EVIDENCE_CLASS
        assert _field_value(section, "SELECTED_BINDING_ID") == BINDING_ID
        assert _field_value(section, "SELECTED_BINDING_DIGEST") == BINDING_DIGEST
        assert _field_value(section, "ECONOMIC_EVALUATION_EXECUTED") == "false"
        assert _field_value(section, "RUNTIME_EFFECT") == "NONE"
        assert _field_value(section, "AUTHORITY_EFFECT") == "NONE"
        assert _field_value(section, "NEXT_STEP") == NEXT_STEP
        assert (
            _field_value(section, "NEXT_OPERATOR_GO")
            == "GO_FULL_CANONICAL_SYSTEM_ECONOMIC_BASELINE_EXECUTION_V1"
        )
