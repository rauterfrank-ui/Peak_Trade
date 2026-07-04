"""Contract tests for Runbook v4.4 research governance progress registry reconciliation v0.

Verifies fail-closed alignment between Runbook v4.4 governance posture and the
authoritative Registry-Metadaten fields without authorizing economic evaluation,
binding ratification, runtime rewire, or mutation of terminal negative evidence.
"""

from __future__ import annotations

import re
from pathlib import Path

from src.governance.runbook_progress_registry_v1 import (
    duplicate_current_owner_fields,
    load_runbook_progress_registry_v1,
)
from tests.ops.runbook_progress_registry_contract_helpers_v1 import (
    authoritative_field_value,
    global_summary_section,
    load_registry,
    read_registry,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK_V4_4 = (
    REPO_ROOT
    / "docs/governance/Peak_Trade_Kanonisches_Vollautonomie_Runbook_v4.4_current_state_multi_candidate_research_fleet.md"
)
RECONCILIATION_SECTION_PREFIX = (
    "#### RUNBOOK_V4_4_RESEARCH_GOVERNANCE_PROGRESS_REGISTRY_RECONCILIATION_V0"
)
TERMINAL_NEXT_STEP = "NO_FURTHER_CROSS_SECTIONAL_RELATIVE_STRENGTH_V0_ACTION_TERMINAL_FAIL"
GLOBAL_NEXT_STEP = "OPERATOR_INPUT_REQUIRED_FOR_NEW_RESEARCH_SCOPE_DEFINITION_V0"
OPERATOR_POLICY_DECISION = "NO_NEW_CANDIDATE_HOLD_REINSTATE"
FINAL_RESEARCH_FLEET = "trend_following,bollinger_bands,momentum_1h"


def _field_value(text: str, field: str) -> str:
    match = re.search(rf"\| `{re.escape(field)}` \| `([^`]*)` \|", text)
    assert match, f"missing registry field: {field}"
    return match.group(1)


def _reconciliation_section(text: str) -> str:
    start = text.index(RECONCILIATION_SECTION_PREFIX)
    end = text.index("\n#### STEP29R_ECONOMIC_VALIDITY_TERMINAL_BLOCKER_REGISTRY_BINDING_V0", start)
    return text[start:end]


class TestRunbookV44AuthoritativeGovernanceReconciliation:
    def test_no_new_candidate_hold_active_after_ratification(self) -> None:
        assert authoritative_field_value("NO_NEW_CANDIDATE_HOLD") == "ACTIVE"
        assert authoritative_field_value("NO_NEW_CANDIDATE_HOLD_REINSTATE_RATIFIED") == "true"
        assert authoritative_field_value("NO_NEW_CANDIDATE_HOLD_REGISTRY_DRIFT_CORRECTED") == "true"
        assert (
            authoritative_field_value("NO_NEW_CANDIDATE_HOLD_PRIOR_REGISTRY_DRIFT_VALUE")
            == "REVOKED"
        )

    def test_operator_policy_decision_hold_reinstate(self) -> None:
        assert authoritative_field_value("OPERATOR_POLICY_DECISION") == OPERATOR_POLICY_DECISION
        assert authoritative_field_value("MULTI_CANDIDATE_RESEARCH_FLEET_ALLOWED") == "false"
        assert authoritative_field_value("EXACTLY_ONE_CANDIDATE_LIMIT") == "false"
        assert authoritative_field_value("FINAL_RESEARCH_FLEET") == FINAL_RESEARCH_FLEET

    def test_binding_and_ratification_flags_pass_in_authoritative_metadata(self) -> None:
        assert authoritative_field_value("FINAL_RESEARCH_FLEET_BINDING_READY") == "true"
        assert authoritative_field_value("NEW_CANDIDATES_RATIFIED") == "false"
        assert authoritative_field_value("ECONOMIC_EVALUATION_SCOPE_RATIFIED") == "true"
        assert authoritative_field_value("ECONOMIC_EVALUATION_AUTHORIZED") == "false"

    def test_terminal_gates_and_promotion_remain_blocked(self) -> None:
        assert authoritative_field_value("ECONOMIC_VALIDITY_OFFLINE_GATE_PASS") == "false"
        assert authoritative_field_value("RUNTIME_REWIRE_ADMISSIBLE") == "false"
        assert authoritative_field_value("PROMOTION_ELIGIBLE") == "false"
        assert (
            authoritative_field_value("CURRENT_BLOCKING_POLICY")
            == "ECONOMIC_VALIDITY_OFFLINE_GATE_FAIL"
        )

    def test_next_canonical_step_terminal_fail_no_auto_evaluation(self) -> None:
        assert authoritative_field_value("NEXT_CANONICAL_STEP") == GLOBAL_NEXT_STEP
        assert authoritative_field_value("NEXT_CANONICAL_ACTION") == GLOBAL_NEXT_STEP
        assert authoritative_field_value("GLOBAL_RUNBOOK_NEXT_STEP") == GLOBAL_NEXT_STEP
        assert (
            authoritative_field_value("HYPOTHESIS_SUBSTRAND_NEXT_STEP") == TERMINAL_NEXT_STEP
        )
        assert (
            authoritative_field_value("NO_FURTHER_CROSS_SECTIONAL_RELATIVE_STRENGTH_V0_ACTION_TERMINAL_FAIL")
            == "true"
        )
        assert authoritative_field_value("CURRENT_ADMISSIBLE_NEXT_SCOPE") == "NONE"
        assert authoritative_field_value("CURRENT_ADMISSIBLE_NEXT_SCOPE_GO_TOKEN") == "NONE"
        assert (
            authoritative_field_value(
                "CROSS_SECTIONAL_RELATIVE_STRENGTH_V0_OFFLINE_ECONOMIC_EVALUATION_STATUS"
            )
            == "COMPLETE_FAIL"
        )

    def test_runbook_v4_4_source_bound(self) -> None:
        assert RUNBOOK_V4_4.is_file(), f"missing runbook v4.4 owner: {RUNBOOK_V4_4}"
        source = authoritative_field_value("RUNBOOK_V4_4_CANONICAL_SOURCE")
        assert source.endswith(
            "Peak_Trade_Kanonisches_Vollautonomie_Runbook_v4.4_current_state_multi_candidate_research_fleet.md"
        )
        body = RUNBOOK_V4_4.read_text(encoding="utf-8")
        assert "FINAL_RESEARCH_FLEET_STATUS=COMPLETE_NO_PASS" in body
        assert FINAL_RESEARCH_FLEET in body


class TestReconciliationCloseoutSection:
    def test_closeout_section_records_reconciliation_without_evidence_mutation(self) -> None:
        section = _reconciliation_section(read_registry())
        assert _field_value(section, "STATUS") == "COMPLETE"
        assert _field_value(section, "NO_NEW_CANDIDATE_HOLD") == "REVOKED"
        assert _field_value(section, "HISTORICAL_NEGATIVE_EVIDENCE_MUTATED") == "false"
        assert _field_value(section, "POLICY_OR_THRESHOLD_CHANGED") == "false"
        assert _field_value(section, "RETRY_UNCHANGED_BINDING_ALLOWED") == "false"
        assert _field_value(section, "RUNTIME_EFFECT") == "NONE"
        assert _field_value(section, "AUTHORITY_EFFECT") == "NONE"


class TestRegistryResolverIntegrity:
    def test_no_duplicate_conflicting_authoritative_current_owners(self) -> None:
        registry = load_registry()
        ambiguous = duplicate_current_owner_fields(
            registry,
            fields=(
                "NO_NEW_CANDIDATE_HOLD",
                "OPERATOR_POLICY_DECISION",
                "NEXT_CANONICAL_STEP",
                "FINAL_RESEARCH_FLEET_BINDING_READY",
            ),
        )
        assert ambiguous == {}

    def test_global_summary_reflects_hold_reinstatement(self) -> None:
        summary = global_summary_section()
        assert _field_value(summary, "NO_NEW_CANDIDATE_HOLD") == "ACTIVE"
        assert _field_value(summary, "FINAL_RESEARCH_FLEET_BINDING_READY") == "true"

    def test_registry_resolver_loads_without_error(self) -> None:
        registry = load_runbook_progress_registry_v1()
        assert registry.authoritative_value("NO_NEW_CANDIDATE_HOLD") == "ACTIVE"
