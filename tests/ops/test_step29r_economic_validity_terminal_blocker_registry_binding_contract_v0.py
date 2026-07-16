"""Contract tests for STEP29R economic-validity terminal blocker registry binding v0."""

from __future__ import annotations

import re
from pathlib import Path

from src.governance.runbook_progress_registry_v1 import (
    RegistryEntryClass,
    load_runbook_progress_registry_v1,
)
from tests.ops.runbook_progress_registry_contract_helpers_v1 import (
    PROGRESS_REGISTRY,
    authoritative_field_value,
    global_summary_section,
    load_registry,
    section_field_value,
    step_29r_section,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_EVIDENCE = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/planning/"
    "runbook_step29r_runtime_rewire_precondition_admissibility_assessment_read_only_v0_20260702T205033Z"
)
BINDING_EVIDENCE = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/planning/"
    "bounded_step29r_economic_validity_terminal_blocker_registry_binding_v0_20260702T210306Z"
)
BINDING_SECTION_PREFIX = "STEP29R_ECONOMIC_VALIDITY_TERMINAL_BLOCKER_REGISTRY_BINDING_V0"


def _field_value(text: str, field: str) -> str:
    match = re.search(rf"\| `{re.escape(field)}` \| `([^`]*)` \|", text)
    assert match, f"missing registry field: {field}"
    return match.group(1)


def _binding_section(text: str) -> str:
    start = text.index(f"#### {BINDING_SECTION_PREFIX}")
    end = text.index("\n---\n\n## PR #4629 Evidence-Drift", start)
    return text[start:end]


class TestTerminalBlockerAuthoritativeBinding:
    def test_runtime_rewire_status_blocked_by_economic_gate(self) -> None:
        assert (
            authoritative_field_value("RUNTIME_REWIRE_STATUS")
            == "BLOCKED_BY_ECONOMIC_VALIDITY_OFFLINE_GATE"
        )

    def test_runtime_rewire_deferred_true(self) -> None:
        assert authoritative_field_value("RUNTIME_REWIRE_DEFERRED") == "true"

    def test_step29r_runtime_rewire_not_admissible(self) -> None:
        assert authoritative_field_value("STEP29R_RUNTIME_REWIRE_ADMISSIBLE") == "false"

    def test_gate_status_fields_pass_fail_pass(self) -> None:
        assert authoritative_field_value("TRADING_LOGIC_COMPLETION_GATE_STATUS") == "PASS"
        assert authoritative_field_value("TRADING_LOGIC_COMPLETION_GATE_PASS") == "true"
        assert authoritative_field_value("ECONOMIC_VALIDITY_OFFLINE_GATE_STATUS") == "FAIL"
        assert authoritative_field_value("ECONOMIC_VALIDITY_OFFLINE_GATE_PASS") == "false"
        assert authoritative_field_value("INTENT_COMPATIBILITY_FIREWALL_GATE_STATUS") == "PASS"
        assert authoritative_field_value("INTENT_COMPATIBILITY_FIREWALL_PASS") == "true"

    def test_fleet_complete_no_pass_zero_viable_candidates(self) -> None:
        assert authoritative_field_value("STEP29M_FLEET_STATUS") == (
            "TERMINAL_FAIL_RESEARCH_GENERATION_CLOSED"
        )
        assert authoritative_field_value("ECONOMICALLY_VIABLE_CANDIDATE_COUNT") == "0"

    def test_no_new_candidate_hold_revoked(self) -> None:
        assert authoritative_field_value("NO_NEW_CANDIDATE_HOLD") == "ACTIVE"

    def test_next_canonical_action_fleet_binding_ratification(self) -> None:
        assert (
            authoritative_field_value("NEXT_CANONICAL_ACTION")
            == "AWAIT_SEPARATE_OPERATOR_GO_FOR_NEW_VERSIONED_FULL_CANONICAL_SYSTEM_ECONOMIC_BINDING_OR_NEW_EVIDENCE_CLASS_V0"
        )

    def test_next_runbook_step_remains_blocked(self) -> None:
        assert authoritative_field_value("NEXT_RUNBOOK_STEP_ADMISSIBLE") == "false"
        assert (
            authoritative_field_value("NEXT_RUNBOOK_STEP_BLOCK_REASON")
            == "STEP29M_NO_PASS_ADMISSIBLE_VERSIONED_SYSTEM_ECONOMIC_BINDING"
        )
        assert authoritative_field_value("CURRENT_ADMISSIBLE_IMPLEMENTATION_SCOPE") == "NONE"

    def test_complete_no_pass_not_reinterpreted(self) -> None:
        assert authoritative_field_value("COMPLETE_NO_PASS_NOT_REINTERPRETED_AS_PASS") == "true"


class TestEvidenceCrosslinks:
    def test_source_precondition_assessment_ref_present(self) -> None:
        ref = authoritative_field_value(
            "STEP29R_PRECONDITION_ADMISSIBILITY_ASSESSMENT_EVIDENCE_REF"
        )
        assert SOURCE_EVIDENCE in ref
        assert "MANIFEST_VERIFY_RC=0" in ref
        assert "NOT_ADMISSIBLE" in ref

    def test_binding_evidence_ref_present(self) -> None:
        ref = authoritative_field_value(
            "STEP29R_ECONOMIC_VALIDITY_TERMINAL_BLOCKER_REGISTRY_BINDING_EVIDENCE_REF"
        )
        assert BINDING_EVIDENCE in ref
        assert "MANIFEST_VERIFY_RC=0" in ref


class TestRuntimeResidualDocumentation:
    def test_legacy_bypass_documented_not_activated(self) -> None:
        assert authoritative_field_value("LEGACY_BYPASS_PATHS_FOUND") == "true"
        assert authoritative_field_value("LEGACY_BYPASS_PATHS_ACTIVATED") == "false"

    def test_no_canonical_order_intent_runtime_consumer(self) -> None:
        assert authoritative_field_value("CANONICAL_ORDER_INTENT_RUNTIME_CONSUMER") == "NONE"

    def test_safety_owners_offline_not_legacy_bound(self) -> None:
        assert (
            authoritative_field_value("SAFETY_RECONCILIATION_OWNERS_OFFLINE_NOT_LEGACY_BOUND")
            == "true"
        )

    def test_futures_only_partial_and_bitcoin_spot_residual_documented(self) -> None:
        assert authoritative_field_value("FUTURES_ONLY_RUNTIME_BOUNDARY_PASS") == "partial"
        assert authoritative_field_value("BITCOIN_SPOT_RUNTIME_PATHS_FOUND") == "true"
        assert (
            authoritative_field_value("BITCOIN_SPOT_RUNTIME_PATHS_REMEDIATION_DEFERRED") == "true"
        )


class TestBindingHistoricalSnapshot:
    def test_binding_section_is_historical_snapshot(self) -> None:
        text = PROGRESS_REGISTRY.read_text(encoding="utf-8")
        section = _binding_section(text)
        assert section_field_value(BINDING_SECTION_PREFIX, "REGISTRY_ENTRY_CLASS") == (
            RegistryEntryClass.HISTORICAL_STEP_SNAPSHOT.value
        )
        assert _field_value(section, "STATUS") == "COMPLETE"
        assert _field_value(section, "STEP29R_IMPLEMENTATION_AUTHORIZED") == "false"
        assert _field_value(section, "ECONOMIC_EVALUATION_PERFORMED") == "false"
        assert _field_value(section, "RUNTIME_MUTATION") == "false"


class TestStep29RSectionConsistency:
    def test_step29r_section_documents_blocked_runtime_rewire(self) -> None:
        section = step_29r_section()
        assert _field_value(section, "RUNTIME_REWIRE_STATUS") == (
            "BLOCKED_BY_ECONOMIC_VALIDITY_OFFLINE_GATE"
        )
        assert _field_value(section, "RUNTIME_REWIRE_DEFERRED") == "true"
        assert _field_value(section, "STEP29R_RUNTIME_REWIRE_ADMISSIBLE") == "false"
        assert _field_value(section, "RUNBOOK_STEP_29R_COMPLETE") == "false"
        assert _field_value(section, "RUNTIME_REWIRE_IMPLEMENTATION_ALLOWED") == "false"

    def test_no_duplicate_conflicting_authoritative_current_owners(self) -> None:
        registry = load_registry()
        from src.governance.runbook_progress_registry_v1 import duplicate_current_owner_fields

        watched = (
            "RUNTIME_REWIRE_STATUS",
            "RUNTIME_REWIRE_DEFERRED",
            "STEP29R_RUNTIME_REWIRE_ADMISSIBLE",
            "NEXT_CANONICAL_ACTION",
            "ECONOMICALLY_VIABLE_CANDIDATE_COUNT",
            "NEXT_REMEDIATION_SLICE",
        )
        ambiguous = duplicate_current_owner_fields(registry, fields=watched)
        assert ambiguous == {}


class TestGlobalSummaryBinding:
    def test_last_verified_origin_main_updated(self) -> None:
        summary = global_summary_section()
        assert _field_value(summary, "LAST_VERIFIED_ORIGIN_MAIN") == (
            "05c814a06eb5ef46b88495b9a392268b65c57246"
        )
