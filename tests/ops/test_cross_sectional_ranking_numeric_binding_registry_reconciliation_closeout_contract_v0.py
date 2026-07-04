"""Contract tests for cross-sectional numeric binding registry reconciliation closeout v0.

Verifies governance metadata reflects PR #4771 numeric materialization and upstream
policy decision class A without authorizing economic evaluation or runtime rewire.
"""

from __future__ import annotations

import re

from src.governance.runbook_progress_registry_v1 import (
    duplicate_current_owner_fields,
    load_runbook_progress_registry_v1,
)
from tests.ops.runbook_progress_registry_contract_helpers_v1 import (
    PROGRESS_REGISTRY,
    authoritative_field_value,
    global_summary_section,
    load_registry,
    read_registry,
)

NEXT_STEP = "BOUNDED_CROSS_SECTIONAL_UNIVERSE_MANIFEST_BINDING_READ_ONLY_REASSESSMENT_V0"
POLICY_DECISION_CLASS = "EXISTING_CONTRACTS_COMPLETE_NO_NEW_POLICY_REQUIRED"
MATERIALIZATION_PR = "4771"
MATERIALIZATION_MERGE_COMMIT = "ef6214b56dd2294f45ca6c2fe55f05c3e09518c0"
POLICY_DECISION_EVIDENCE = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/planning/"
    "bounded_cross_sectional_ranking_semantics_numeric_binding_policy_decision_read_only_v0_"
    "20260703T022401Z"
)
MATERIALIZATION_EVIDENCE = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/planning/"
    "bounded_cross_sectional_ranking_semantics_versioned_binding_materialization_pr4771_"
    "squash_merge_and_post_merge_closeout_v1_20260703T000410Z"
)
CROSS_SECTIONAL_SECTION_PREFIX = (
    "#### RUNBOOK_RESEARCH_LINE — Cross-Sectional Relative Strength Non-Bitcoin Perpetuals v0"
)


def _field_value(text: str, field: str) -> str:
    match = re.search(rf"\| `{re.escape(field)}` \| `([^`]*)` \|", text)
    assert match, f"missing registry field: {field}"
    return match.group(1)


def _cross_sectional_section(text: str) -> str:
    start = text.index(CROSS_SECTIONAL_SECTION_PREFIX)
    end = text.index(
        "\n#### RUNBOOK_RESEARCH_LINE — Composite Breakout Confirmation Vol-Gated Donchian v1",
        start,
    )
    return text[start:end]


class TestAuthoritativeNumericBindingReconciliation:
    def test_numeric_values_bound_true(self) -> None:
        assert authoritative_field_value("NUMERIC_VALUES_BOUND") == "true"
        assert (
            authoritative_field_value("CROSS_SECTIONAL_RANKING_SEMANTICS_NUMERIC_VALUES_BOUND")
            == "true"
        )

    def test_numeric_policy_decision_class_complete(self) -> None:
        assert authoritative_field_value("NUMERIC_POLICY_DECISION_CLASS") == POLICY_DECISION_CLASS
        assert authoritative_field_value("NUMERIC_POLICY_OWNER_REQUIRED") == "false"
        assert authoritative_field_value("CROSS_SECTIONAL_RANKING_NUMERIC_SEMANTICS_STATUS") == (
            "COMPLETE"
        )

    def test_materialization_source_pr4771_verified(self) -> None:
        assert authoritative_field_value("NUMERIC_MATERIALIZATION_SOURCE_PR") == MATERIALIZATION_PR
        assert authoritative_field_value("NUMERIC_MATERIALIZATION_STATUS") == "BOUND_AND_VALIDATED"
        assert authoritative_field_value("NUMERIC_MATERIALIZATION_EVIDENCE_STATUS") == "VERIFIED"
        assert (
            authoritative_field_value(
                "CROSS_SECTIONAL_RANKING_SEMANTICS_NUMERIC_MATERIALIZATION_PR"
            )
            == MATERIALIZATION_PR
        )
        assert (
            authoritative_field_value(
                "CROSS_SECTIONAL_RANKING_SEMANTICS_NUMERIC_MATERIALIZATION_MERGE_COMMIT"
            )
            == MATERIALIZATION_MERGE_COMMIT
        )

    def test_binding_ratified_complete(self) -> None:
        assert authoritative_field_value("CROSS_SECTIONAL_RANKING_SEMANTICS_BINDING_RATIFIED") == (
            "true"
        )
        assert (
            authoritative_field_value("CROSS_SECTIONAL_RANKING_SEMANTICS_OVERALL_BINDING_STATUS")
            == "COMPLETE"
        )

    def test_pit_universe_manifest_ref_bound_after_scope_ratification(self) -> None:
        assert authoritative_field_value("PIT_UNIVERSE_MANIFEST_REF_STATUS") == "BOUND"
        assert (
            authoritative_field_value("CROSS_SECTIONAL_RANKING_SEMANTICS_OVERALL_BINDING_STATUS")
            == "COMPLETE"
        )

    def test_economic_and_runtime_remain_blocked(self) -> None:
        assert authoritative_field_value("ECONOMIC_EVALUATION_AUTHORIZED") == "false"
        assert authoritative_field_value("ECONOMIC_VALIDITY_OFFLINE_GATE_PASS") == "false"
        assert authoritative_field_value("RUNTIME_REWIRE_ADMISSIBLE") == "false"
        assert (
            authoritative_field_value("CURRENT_BLOCKING_POLICY")
            == "ECONOMIC_VALIDITY_OFFLINE_GATE_FAIL"
        )

    def test_next_canonical_step_terminal_fail_no_auto_evaluation(self) -> None:
        assert authoritative_field_value("GLOBAL_RUNBOOK_NEXT_STEP") == (
            "OPERATOR_INPUT_REQUIRED_FOR_NEW_RESEARCH_SCOPE_DEFINITION_V0"
        )
        assert authoritative_field_value("HYPOTHESIS_SUBSTRAND_NEXT_STEP") == (
            "NO_FURTHER_CROSS_SECTIONAL_RELATIVE_STRENGTH_V0_ACTION_TERMINAL_FAIL"
        )
        assert authoritative_field_value("HYPOTHESIS_SUBSTRAND_NEXT_STEP_READ_ONLY") == "true"


class TestEvidenceCrosslinks:
    def test_policy_decision_evidence_ref_present(self) -> None:
        ref = authoritative_field_value(
            "CROSS_SECTIONAL_RANKING_SEMANTICS_NUMERIC_POLICY_DECISION_EVIDENCE_REF"
        )
        assert POLICY_DECISION_EVIDENCE in ref
        assert "MANIFEST_VERIFY_RC=0" in ref
        assert "POLICY_DECISION_CLASS=A" in ref

    def test_materialization_evidence_ref_present(self) -> None:
        ref = authoritative_field_value(
            "CROSS_SECTIONAL_RANKING_SEMANTICS_NUMERIC_MATERIALIZATION_EVIDENCE_REF"
        )
        assert MATERIALIZATION_EVIDENCE in ref
        assert "MANIFEST_VERIFY_RC=0" in ref
        assert "PR #4771" in ref


class TestCrossSectionalResearchLineConsistency:
    def test_research_line_matches_authoritative_numeric_state(self) -> None:
        text = read_registry()
        section = _cross_sectional_section(text)
        assert _field_value(section, "STATUS") == "COMPLETE_FAIL"
        assert (
            _field_value(section, "NEXT_CANONICAL_STEP")
            == "NO_FURTHER_CROSS_SECTIONAL_RELATIVE_STRENGTH_V0_ACTION_TERMINAL_FAIL"
        )
        assert _field_value(section, "NUMERIC_VALUES_BOUND") == "true"
        assert _field_value(section, "PIT_UNIVERSE_MANIFEST_REF_STATUS") == "BOUND"
        assert _field_value(section, "NUMERIC_MATERIALIZATION_SOURCE_PR") == MATERIALIZATION_PR
        assert _field_value(section, "NUMERIC_POLICY_DECISION_CLASS") == POLICY_DECISION_CLASS
        assert _field_value(section, "ECONOMIC_EVALUATION_AUTHORIZED") == "false"
        assert _field_value(section, "RUNTIME_REWIRE_ADMISSIBLE") == "false"


class TestRegistryResolverIntegrity:
    def test_no_duplicate_conflicting_authoritative_current_owners(self) -> None:
        registry = load_registry()
        watched = (
            "NUMERIC_VALUES_BOUND",
            "CROSS_SECTIONAL_RANKING_SEMANTICS_NUMERIC_VALUES_BOUND",
            "NUMERIC_POLICY_DECISION_CLASS",
            "GLOBAL_RUNBOOK_NEXT_STEP",
            "HYPOTHESIS_SUBSTRAND_NEXT_STEP",
            "PIT_UNIVERSE_MANIFEST_REF_STATUS",
            "ECONOMIC_EVALUATION_AUTHORIZED",
            "RUNTIME_REWIRE_ADMISSIBLE",
        )
        ambiguous = duplicate_current_owner_fields(registry, fields=watched)
        assert ambiguous == {}

    def test_registry_parser_loads(self) -> None:
        registry = load_runbook_progress_registry_v1(PROGRESS_REGISTRY)
        assert registry.authoritative_value("NUMERIC_VALUES_BOUND") == "true"


class TestGlobalSummaryBinding:
    def test_last_verified_origin_main_updated(self) -> None:
        summary = global_summary_section()
        assert _field_value(summary, "LAST_VERIFIED_ORIGIN_MAIN") == (
            "498263a376dac33dead91cfdb2278d23066c8dc5"
        )
