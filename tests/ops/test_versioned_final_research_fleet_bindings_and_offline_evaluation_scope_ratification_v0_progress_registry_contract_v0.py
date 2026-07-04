"""Contract tests for post-PR4822 versioned final research fleet bindings ratification v0."""

from __future__ import annotations

import re

from src.governance.runbook_progress_registry_v1 import (
    duplicate_current_owner_fields,
    load_runbook_progress_registry_v1,
)
from tests.ops.runbook_progress_registry_contract_helpers_v1 import (
    authoritative_field_value,
    global_summary_section,
    read_registry,
)

CLOSEOUT_SECTION_PREFIX = (
    "#### VERSIONED_FINAL_RESEARCH_FLEET_BINDINGS_AND_OFFLINE_EVALUATION_SCOPE_RATIFICATION_V0"
)
GLOBAL_NEXT_STEP = "OPERATOR_INPUT_REQUIRED_FOR_NEW_RESEARCH_SCOPE_DEFINITION_V0"
CURRENT_GLOBAL_NEXT_STEP = (
    "OPERATOR_DECISION_REQUIRED_UNMODIFIED_BINDING_REEXECUTION_BLOCKED_V0"
)
CS_TERMINAL_NEXT_STEP = "NO_FURTHER_CROSS_SECTIONAL_RELATIVE_STRENGTH_V0_ACTION_TERMINAL_FAIL"
FINAL_RESEARCH_FLEET = "trend_following,bollinger_bands,momentum_1h"


def _field_value(text: str, field: str) -> str:
    match = re.search(rf"\| `{re.escape(field)}` \| `([^`]*)` \|", text)
    assert match, f"missing registry field: {field}"
    return match.group(1)


def _closeout_section(text: str) -> str:
    start = text.index(CLOSEOUT_SECTION_PREFIX)
    end = text.index("\n---\n\n## PR #4629 Evidence-Drift", start)
    return text[start:end]


class TestVersionedFinalResearchFleetBindingsAuthoritativeState:
    def test_fleet_binding_and_scope_ratification_flags(self) -> None:
        assert authoritative_field_value("FINAL_RESEARCH_FLEET") == FINAL_RESEARCH_FLEET
        assert authoritative_field_value("FINAL_RESEARCH_FLEET_BINDING_READY") == "true"
        assert authoritative_field_value("NEW_CANDIDATES_RATIFIED") == "true"
        assert authoritative_field_value("OFFLINE_ECONOMIC_EVALUATION_SCOPE_RATIFIED") == "true"
        assert authoritative_field_value("ECONOMIC_EVALUATION_SCOPE_RATIFIED") == "true"
        assert authoritative_field_value("ECONOMIC_EVALUATION_AUTHORIZED") == "false"
        assert authoritative_field_value("ECONOMIC_VALIDITY_OFFLINE_GATE_PASS") == "false"
        assert authoritative_field_value("RUNTIME_REWIRE_ADMISSIBLE") == "false"

    def test_pr4822_governance_invariants_preserved(self) -> None:
        assert authoritative_field_value("NO_NEW_CANDIDATE_HOLD") == "ACTIVE"
        assert authoritative_field_value("NEXT_CANONICAL_STEP") == CURRENT_GLOBAL_NEXT_STEP
        assert authoritative_field_value("GLOBAL_RUNBOOK_NEXT_STEP") == CURRENT_GLOBAL_NEXT_STEP
        assert authoritative_field_value("HYPOTHESIS_SUBSTRAND_NEXT_STEP") == CS_TERMINAL_NEXT_STEP
        assert (
            authoritative_field_value(
                "NO_FURTHER_CROSS_SECTIONAL_RELATIVE_STRENGTH_V0_ACTION_TERMINAL_FAIL"
            )
            == "true"
        )

    def test_cs_v0_terminal_fail_unchanged(self) -> None:
        assert (
            authoritative_field_value(
                "CROSS_SECTIONAL_RELATIVE_STRENGTH_V0_OFFLINE_ECONOMIC_EVALUATION_STATUS"
            )
            == "COMPLETE_FAIL"
        )
        assert (
            authoritative_field_value(
                "CROSS_SECTIONAL_RELATIVE_STRENGTH_V0_ECONOMIC_VALIDITY_OFFLINE_GATE_PASS"
            )
            == "false"
        )
        assert (
            authoritative_field_value(
                "CROSS_SECTIONAL_RELATIVE_STRENGTH_V0_PROMOTION_CANDIDATE_ELIGIBLE"
            )
            == "false"
        )
        assert (
            authoritative_field_value(
                "CROSS_SECTIONAL_RELATIVE_STRENGTH_V0_RUNTIME_REWIRE_ADMISSIBLE"
            )
            == "false"
        )
        assert (
            authoritative_field_value("CROSS_SECTIONAL_RELATIVE_STRENGTH_V0_RE_EVALUATION_ALLOWED")
            == "false"
        )

    def test_futures_only_no_bitcoin_direction(self) -> None:
        assert (
            authoritative_field_value("CROSS_SECTIONAL_RELATIVE_STRENGTH_V0_FUTURES_ONLY") == "true"
        )
        assert (
            authoritative_field_value(
                "CROSS_SECTIONAL_RELATIVE_STRENGTH_V0_BITCOIN_DIRECTION_ALLOWED"
            )
            == "false"
        )


class TestVersionedFinalResearchFleetBindingsCloseoutSection:
    def test_closeout_records_ratification_without_evaluation_execution(self) -> None:
        section = _closeout_section(read_registry())
        assert _field_value(section, "STATUS") == "COMPLETE"
        assert (
            _field_value(section, "SCOPE_CLASSIFICATION")
            == "BOUNDED_VERSIONED_FINAL_RESEARCH_FLEET_BINDINGS_AND_OFFLINE_EVALUATION_SCOPE_RATIFICATION_V0"
        )
        assert _field_value(section, "FINAL_RESEARCH_FLEET_BINDING_READY") == "true"
        assert _field_value(section, "NEW_CANDIDATES_RATIFIED") == "true"
        assert _field_value(section, "OFFLINE_ECONOMIC_EVALUATION_SCOPE_RATIFIED") == "true"
        assert _field_value(section, "ECONOMIC_EVALUATION_AUTHORIZED") == "false"
        assert _field_value(section, "ECONOMIC_EVALUATION_EXECUTED") == "false"
        assert _field_value(section, "HISTORICAL_NEGATIVE_EVIDENCE_MUTATED") == "false"
        assert _field_value(section, "NEXT_CANONICAL_STEP") == GLOBAL_NEXT_STEP
        assert _field_value(section, "NO_NEW_CANDIDATE_HOLD") == "ACTIVE"
        assert (
            _field_value(section, "CROSS_SECTIONAL_RELATIVE_STRENGTH_V0_STATUS") == "COMPLETE_FAIL"
        )
        assert _field_value(
            section, "CROSS_SECTIONAL_RELATIVE_STRENGTH_V0_TERMINAL_FAIL_PRESERVED"
        ) == ("true")
        assert _field_value(section, "RUNTIME_EFFECT") == "NONE"
        assert _field_value(section, "AUTHORITY_EFFECT") == "NONE"


class TestRegistryResolverIntegrity:
    def test_no_duplicate_conflicting_authoritative_current_owners(self) -> None:
        registry = load_runbook_progress_registry_v1()
        ambiguous = duplicate_current_owner_fields(
            registry,
            fields=(
                "NEXT_CANONICAL_STEP",
                "FINAL_RESEARCH_FLEET_BINDING_READY",
                "NEW_CANDIDATES_RATIFIED",
                "OFFLINE_ECONOMIC_EVALUATION_SCOPE_RATIFIED",
            ),
        )
        assert ambiguous == {}

    def test_global_summary_reflects_ratified_state(self) -> None:
        summary = global_summary_section()
        assert _field_value(summary, "NEW_CANDIDATES_RATIFIED") == "true"
        assert _field_value(summary, "OFFLINE_ECONOMIC_EVALUATION_SCOPE_RATIFIED") == "true"
        assert (
            _field_value(
                summary,
                "VERSIONED_FINAL_RESEARCH_FLEET_BINDINGS_AND_OFFLINE_EVALUATION_SCOPE_RATIFICATION_V0_STATUS",
            )
            == "COMPLETE"
        )
