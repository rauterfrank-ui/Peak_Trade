"""Contract tests for CS relative-strength v0 scope definition and binding ratification registry closeout."""

from __future__ import annotations

import re

from tests.ops.runbook_progress_registry_contract_helpers_v1 import (
    authoritative_field_value,
    read_registry,
)

CLOSEOUT_SECTION_PREFIX = "#### CROSS_SECTIONAL_RELATIVE_STRENGTH_V0_RESEARCH_SCOPE_DEFINITION_AND_BINDING_RATIFICATION_V0"
RESEARCH_LINE_PREFIX = (
    "#### RUNBOOK_RESEARCH_LINE — Cross-Sectional Relative Strength Non-Bitcoin Perpetuals v0"
)
NEXT_CANONICAL_STEP = "AWAIT_OPERATOR_OFFLINE_EVALUATION_GO_CROSS_SECTIONAL_RELATIVE_STRENGTH_V0"
OPERATOR_GO = "GO_NEW_RESEARCH_SCOPE_CROSS_SECTIONAL_RELATIVE_STRENGTH_NON_BITCOIN_PERPETUALS_V0"
STRATEGY_TARGET = "cross_sectional_relative_strength&#47;v0"
HYPOTHESIS_ID = "CROSS_SECTIONAL_RELATIVE_STRENGTH_NON_BITCOIN_PERPETUALS_V0"


def _field_value(text: str, field: str) -> str:
    match = re.search(rf"\| `{re.escape(field)}` \| `([^`]*)` \|", text)
    assert match, f"missing registry field: {field}"
    return match.group(1)


def _closeout_section(text: str) -> str:
    start = text.index(CLOSEOUT_SECTION_PREFIX)
    end = text.index("\n---\n\n## PR #4629 Evidence-Drift", start)
    return text[start:end]


def _research_line_section(text: str) -> str:
    start = text.index(RESEARCH_LINE_PREFIX)
    end = text.index(
        "\n#### RUNBOOK_RESEARCH_LINE — Cross-Sectional Funding Rate Carry Non-Bitcoin Perpetuals v0",
        start,
    )
    return text[start:end]


class TestAuthoritativeScopeBindingRatification:
    def test_global_hold_remains_active_with_scoped_exception(self) -> None:
        assert authoritative_field_value("NO_NEW_CANDIDATE_HOLD") == "ACTIVE"
        assert (
            authoritative_field_value(
                "CROSS_SECTIONAL_RELATIVE_STRENGTH_V0_NO_NEW_CANDIDATE_HOLD_EXCEPTION"
            )
            == "true"
        )
        assert (
            authoritative_field_value(
                "CROSS_SECTIONAL_RELATIVE_STRENGTH_V0_NO_NEW_CANDIDATE_HOLD_EXCEPTION_GO_TOKEN"
            )
            == OPERATOR_GO
        )

    def test_scope_definition_and_binding_ratified_without_evaluation(self) -> None:
        assert (
            authoritative_field_value(
                "CROSS_SECTIONAL_RELATIVE_STRENGTH_V0_RESEARCH_SCOPE_DEFINITION_RATIFIED"
            )
            == "true"
        )
        assert (
            authoritative_field_value(
                "CROSS_SECTIONAL_RELATIVE_STRENGTH_V0_BINDING_RATIFICATION_COMPLETE"
            )
            == "true"
        )
        assert (
            authoritative_field_value(
                "CROSS_SECTIONAL_RELATIVE_STRENGTH_V0_ALL_REQUIRED_BINDINGS_RATIFIED"
            )
            == "true"
        )
        assert (
            authoritative_field_value(
                "CROSS_SECTIONAL_RELATIVE_STRENGTH_V0_OFFLINE_ECONOMIC_EVALUATION_SCOPE_RATIFIED"
            )
            == "true"
        )
        assert authoritative_field_value("NEW_CANDIDATES_RATIFIED") == "false"
        assert authoritative_field_value("ECONOMIC_EVALUATION_AUTHORIZED") == "false"
        assert (
            authoritative_field_value(
                "CROSS_SECTIONAL_RELATIVE_STRENGTH_V0_ECONOMIC_EVALUATION_AUTHORIZED"
            )
            == "false"
        )
        assert (
            authoritative_field_value(
                "CROSS_SECTIONAL_RELATIVE_STRENGTH_V0_ECONOMIC_EVALUATION_EXECUTED"
            )
            == "false"
        )

    def test_terminal_gates_and_runtime_remain_blocked(self) -> None:
        assert authoritative_field_value("ECONOMIC_VALIDITY_OFFLINE_GATE_PASS") == "false"
        assert authoritative_field_value("RUNTIME_REWIRE_ADMISSIBLE") == "false"
        assert authoritative_field_value("PROMOTION_ELIGIBLE") == "false"
        assert (
            authoritative_field_value(
                "CROSS_SECTIONAL_RELATIVE_STRENGTH_V0_NO_EVALUATION_UNTIL_SCOPE_RATIFIED"
            )
            == "true"
        )

    def test_scoped_admissible_next_scope_without_global_candidate_ratification(self) -> None:
        assert authoritative_field_value("CURRENT_ADMISSIBLE_NEXT_SCOPE") == STRATEGY_TARGET
        assert authoritative_field_value("CURRENT_ADMISSIBLE_NEXT_SCOPE_GO_TOKEN") == OPERATOR_GO
        assert authoritative_field_value("NEXT_CANONICAL_STEP") == NEXT_CANONICAL_STEP
        assert authoritative_field_value("NEXT_CANONICAL_ACTION") == NEXT_CANONICAL_STEP
        assert authoritative_field_value("GLOBAL_RUNBOOK_NEXT_STEP") == NEXT_CANONICAL_STEP

    def test_futures_only_and_exclusions(self) -> None:
        assert (
            authoritative_field_value("CROSS_SECTIONAL_RELATIVE_STRENGTH_V0_FUTURES_ONLY") == "true"
        )
        assert (
            authoritative_field_value(
                "CROSS_SECTIONAL_RELATIVE_STRENGTH_V0_BITCOIN_DIRECTION_ALLOWED"
            )
            == "false"
        )
        assert (
            authoritative_field_value("CROSS_SECTIONAL_RELATIVE_STRENGTH_V0_HYPOTHESIS_ID")
            == HYPOTHESIS_ID
        )
        assert (
            authoritative_field_value(
                "CROSS_SECTIONAL_RELATIVE_STRENGTH_V0_RETRY_UNCHANGED_BINDING_ALLOWED"
            )
            == "false"
        )


class TestCloseoutSection:
    def test_closeout_records_pass_without_authority_effect(self) -> None:
        section = _closeout_section(read_registry())
        assert _field_value(section, "STATUS") == "COMPLETE"
        assert _field_value(section, "SCOPE_CLASSIFICATION") == (
            "BOUNDED_FUTURES_ONLY_RESEARCH_SCOPE_DEFINITION_AND_BINDING_RATIFICATION_V0"
        )
        assert _field_value(section, "GO_TOKEN") == OPERATOR_GO
        assert _field_value(section, "GO_TOKEN_CONSUMED") == "true"
        assert _field_value(section, "STRATEGY_ID") == "cross_sectional_relative_strength"
        assert _field_value(section, "STRATEGY_VERSION") == "v0"
        assert _field_value(section, "ALL_REQUIRED_BINDINGS_RATIFIED") == "true"
        assert _field_value(section, "ECONOMIC_EVALUATION_AUTHORIZED") == "false"
        assert _field_value(section, "ECONOMIC_EVALUATION_EXECUTED") == "false"
        assert _field_value(section, "NO_NEW_CANDIDATE_HOLD") == "ACTIVE"
        assert _field_value(section, "NO_NEW_CANDIDATE_HOLD_EXCEPTION") == "true"
        assert _field_value(section, "HISTORICAL_NEGATIVE_EVIDENCE_MUTATED") == "false"
        assert _field_value(section, "NEXT_CANONICAL_STEP") == NEXT_CANONICAL_STEP
        assert _field_value(section, "RUNTIME_EFFECT") == "NONE"
        assert _field_value(section, "AUTHORITY_EFFECT") == "NONE"


class TestResearchLineConsistency:
    def test_research_line_matches_authoritative_state(self) -> None:
        section = _research_line_section(read_registry())
        assert _field_value(section, "STATUS") == "SCOPE_DEFINITION_AND_BINDING_RATIFIED"
        assert _field_value(section, "NEXT_CANONICAL_STEP") == NEXT_CANONICAL_STEP
        assert _field_value(section, "PIT_UNIVERSE_MANIFEST_REF_STATUS") == "BOUND"
        assert _field_value(section, "UNIVERSE_BINDING_STATUS") == "BOUND"
        assert _field_value(section, "DATASET_BINDING_STATUS") == "BOUND"
        assert _field_value(section, "PERIOD_BINDING_STATUS") == "BOUND"
        assert _field_value(section, "COST_MODEL_BINDING_STATUS") == "BOUND"
        assert _field_value(section, "DIGEST_BINDING_STATUS") == "BOUND"
        assert (
            _field_value(section, "CROSS_SECTIONAL_RANKING_SEMANTICS_OVERALL_BINDING_STATUS")
            == "COMPLETE"
        )
        assert _field_value(section, "CONCRETE_CANDIDATE_RATIFIED") == "true"
        assert _field_value(section, "ECONOMIC_EVALUATION_AUTHORIZED") == "false"
        assert _field_value(section, "BACKTEST_EXECUTION_ALLOWED") == "false"
        assert _field_value(section, "RUNTIME_REWIRE_ADMISSIBLE") == "false"
