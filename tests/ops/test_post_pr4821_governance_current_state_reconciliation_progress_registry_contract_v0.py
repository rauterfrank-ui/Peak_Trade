"""Contract tests for post-PR4821 governance current-state reconciliation v0."""

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

CLOSEOUT_SECTION_PREFIX = "#### POST_PR4821_GOVERNANCE_CURRENT_STATE_RECONCILIATION_V0"
GLOBAL_NEXT_STEP = "OPERATOR_INPUT_REQUIRED_FOR_NEW_RESEARCH_SCOPE_DEFINITION_V0"
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


class TestPostPr4821AuthoritativeGlobalState:
    def test_global_next_step_restored_after_pr4821_drift(self) -> None:
        assert authoritative_field_value("NEXT_CANONICAL_STEP") == GLOBAL_NEXT_STEP
        assert authoritative_field_value("NEXT_CANONICAL_ACTION") == GLOBAL_NEXT_STEP
        assert authoritative_field_value("GLOBAL_RUNBOOK_NEXT_STEP") == GLOBAL_NEXT_STEP

    def test_cs_v0_terminal_fail_remains_local_not_global(self) -> None:
        assert (
            authoritative_field_value("HYPOTHESIS_SUBSTRAND_NEXT_STEP") == CS_TERMINAL_NEXT_STEP
        )
        assert (
            authoritative_field_value("NO_FURTHER_CROSS_SECTIONAL_RELATIVE_STRENGTH_V0_ACTION_TERMINAL_FAIL")
            == "true"
        )
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

    def test_hold_active_is_global_pr4819_not_runbook_v4_4_revoked(self) -> None:
        assert authoritative_field_value("NO_NEW_CANDIDATE_HOLD") == "ACTIVE"
        assert authoritative_field_value("NO_NEW_CANDIDATE_HOLD_REINSTATE_RATIFIED") == "true"
        assert authoritative_field_value("CURRENT_ADMISSIBLE_NEXT_SCOPE") == "NONE"

    def test_final_research_fleet_state_unchanged(self) -> None:
        assert authoritative_field_value("FINAL_RESEARCH_FLEET") == FINAL_RESEARCH_FLEET
        assert authoritative_field_value("FINAL_RESEARCH_FLEET_BINDING_READY") == "true"
        assert authoritative_field_value("FINAL_RESEARCH_FLEET_OFFLINE_EVALUATION_COMPLETE") == (
            "true"
        )
        assert authoritative_field_value("NEW_CANDIDATES_RATIFIED") == "false"
        assert authoritative_field_value("ECONOMIC_EVALUATION_AUTHORIZED") == "false"
        assert authoritative_field_value("RUNTIME_REWIRE_ADMISSIBLE") == "false"

    def test_futures_only_and_bitcoin_direction_invariants(self) -> None:
        assert (
            authoritative_field_value("CROSS_SECTIONAL_RELATIVE_STRENGTH_V0_FUTURES_ONLY") == "true"
        )
        assert (
            authoritative_field_value("CROSS_SECTIONAL_RELATIVE_STRENGTH_V0_BITCOIN_DIRECTION_ALLOWED")
            == "false"
        )


class TestPostPr4821CloseoutSection:
    def test_closeout_records_reconciliation_without_evidence_mutation(self) -> None:
        section = _closeout_section(read_registry())
        assert _field_value(section, "STATUS") == "COMPLETE"
        assert _field_value(section, "DRIFT_CLASS") == (
            "PR4821_GLOBAL_NEXT_STEP_OVERWRITE_BY_CS_V0_TERMINAL_FAIL"
        )
        assert _field_value(section, "CORRECTED_GLOBAL_NEXT_CANONICAL_STEP") == GLOBAL_NEXT_STEP
        assert (
            _field_value(section, "PRIOR_GLOBAL_NEXT_CANONICAL_STEP_DRIFT_VALUE")
            == CS_TERMINAL_NEXT_STEP
        )
        assert _field_value(section, "HISTORICAL_NEGATIVE_EVIDENCE_MUTATED") == "false"
        assert _field_value(section, "RUNTIME_EFFECT") == "NONE"
        assert _field_value(section, "AUTHORITY_EFFECT") == "NONE"


class TestRegistryResolverIntegrity:
    def test_no_duplicate_conflicting_authoritative_current_owners(self) -> None:
        registry = load_runbook_progress_registry_v1()
        ambiguous = duplicate_current_owner_fields(
            registry,
            fields=(
                "NEXT_CANONICAL_STEP",
                "GLOBAL_RUNBOOK_NEXT_STEP",
                "NO_NEW_CANDIDATE_HOLD",
                "FINAL_RESEARCH_FLEET_BINDING_READY",
            ),
        )
        assert ambiguous == {}

    def test_global_summary_reflects_reconciled_state(self) -> None:
        summary = global_summary_section()
        assert _field_value(summary, "NEXT_CANONICAL_STEP") == GLOBAL_NEXT_STEP
        assert _field_value(summary, "NO_NEW_CANDIDATE_HOLD") == "ACTIVE"
        assert (
            _field_value(summary, "POST_PR4821_GOVERNANCE_CURRENT_STATE_RECONCILIATION_STATUS")
            == "COMPLETE"
        )
