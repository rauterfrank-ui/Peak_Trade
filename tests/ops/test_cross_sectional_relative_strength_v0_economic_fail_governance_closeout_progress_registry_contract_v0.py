"""Contract tests for CS relative-strength v0 economic FAIL governance closeout registry."""

from __future__ import annotations

import re

from tests.ops.runbook_progress_registry_contract_helpers_v1 import (
    authoritative_field_value,
    read_registry,
)

CLOSEOUT_SECTION_PREFIX = "#### CROSS_SECTIONAL_RELATIVE_STRENGTH_V0_OFFLINE_ECONOMIC_EVALUATION_FAIL_GOVERNANCE_CLOSEOUT_V0"
RESEARCH_LINE_PREFIX = (
    "#### RUNBOOK_RESEARCH_LINE — Cross-Sectional Relative Strength Non-Bitcoin Perpetuals v0"
)
TERMINAL_NEXT_STEP = "NO_FURTHER_CROSS_SECTIONAL_RELATIVE_STRENGTH_V0_ACTION_TERMINAL_FAIL"
GLOBAL_NEXT_STEP = "OPERATOR_INPUT_REQUIRED_FOR_NEW_RESEARCH_SCOPE_DEFINITION_V0"
OPERATOR_GO = "GO_OFFLINE_ECONOMIC_EVALUATION_CROSS_SECTIONAL_RELATIVE_STRENGTH_V0"
HYPOTHESIS_ID = "CROSS_SECTIONAL_RELATIVE_STRENGTH_NON_BITCOIN_PERPETUALS_V0"
EVALUATION_EVIDENCE_REF = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/research/"
    "cs_relative_strength_offline_economic_evaluation_v0_20260704T184808Z"
)
REASON_CODES = (
    "METRIC_MISSING:single_trade_profit_contribution;MONTE_CARLO_FAILED;"
    "NET_EXPECTANCY_BELOW_THRESHOLD;OUT_OF_SAMPLE_FAILED;PROFIT_FACTOR_BELOW_THRESHOLD;"
    "REGIME_DOMINANCE_EXCEEDED;TRADE_COUNT_BELOW_THRESHOLD"
)


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


class TestAuthoritativeEconomicFailCloseout:
    def test_global_hold_remains_active(self) -> None:
        assert authoritative_field_value("NO_NEW_CANDIDATE_HOLD") == "ACTIVE"

    def test_offline_evaluation_complete_fail_registered(self) -> None:
        assert (
            authoritative_field_value(
                "CROSS_SECTIONAL_RELATIVE_STRENGTH_V0_OFFLINE_ECONOMIC_EVALUATION_STATUS"
            )
            == "COMPLETE_FAIL"
        )
        assert authoritative_field_value("CROSS_SECTIONAL_RELATIVE_STRENGTH_V0_STATUS") == (
            "COMPLETE_FAIL"
        )
        assert (
            authoritative_field_value(
                "CROSS_SECTIONAL_RELATIVE_STRENGTH_V0_ECONOMIC_EVALUATION_EXECUTED"
            )
            == "true"
        )
        assert (
            authoritative_field_value(
                "CROSS_SECTIONAL_RELATIVE_STRENGTH_V0_HISTORICAL_ECONOMIC_RESULT"
            )
            == "FAIL"
        )

    def test_terminal_gates_and_promotion_remain_blocked(self) -> None:
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
        assert authoritative_field_value("ECONOMIC_VALIDITY_OFFLINE_GATE_PASS") == "false"
        assert authoritative_field_value("PROMOTION_ELIGIBLE") == "false"
        assert authoritative_field_value("RUNTIME_REWIRE_ADMISSIBLE") == "false"

    def test_no_automatic_next_evaluation_or_runtime(self) -> None:
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
            authoritative_field_value("CROSS_SECTIONAL_RELATIVE_STRENGTH_V0_RE_EVALUATION_ALLOWED")
            == "false"
        )

    def test_negative_evidence_and_reason_codes_preserved(self) -> None:
        assert (
            authoritative_field_value(
                "CROSS_SECTIONAL_RELATIVE_STRENGTH_V0_ECONOMIC_EVALUATION_REASON_CODES"
            )
            == REASON_CODES
        )
        assert authoritative_field_value("CROSS_SECTIONAL_RELATIVE_STRENGTH_V0_TRADE_COUNT") == "1"
        assert (
            authoritative_field_value("CROSS_SECTIONAL_RELATIVE_STRENGTH_V0_NET_RETURN")
            == "-0.00589"
        )
        assert (
            authoritative_field_value(
                "CROSS_SECTIONAL_RELATIVE_STRENGTH_V0_POLICY_OR_THRESHOLD_CHANGED"
            )
            == "false"
        )
        assert (
            authoritative_field_value("CROSS_SECTIONAL_RELATIVE_STRENGTH_V0_BINDING_CHANGED")
            == "false"
        )

    def test_durable_evidence_path_and_manifest_verify(self) -> None:
        ref = authoritative_field_value(
            "CROSS_SECTIONAL_RELATIVE_STRENGTH_V0_OFFLINE_ECONOMIC_EVALUATION_EVIDENCE_REF"
        )
        assert EVALUATION_EVIDENCE_REF in ref
        assert "MANIFEST_VERIFY_RC=0" in ref
        assert (
            authoritative_field_value("CROSS_SECTIONAL_RELATIVE_STRENGTH_V0_MANIFEST_VERIFY_RC")
            == "0"
        )
        durable_path = authoritative_field_value(
            "CROSS_SECTIONAL_RELATIVE_STRENGTH_V0_DURABLE_EVIDENCE_PATH"
        )
        assert EVALUATION_EVIDENCE_REF in durable_path


class TestCloseoutSection:
    def test_closeout_records_fail_without_authority_effect(self) -> None:
        section = _closeout_section(read_registry())
        assert _field_value(section, "STATUS") == "COMPLETE"
        assert _field_value(section, "SCOPE_CLASSIFICATION") == (
            "BOUNDED_FUTURES_ONLY_OFFLINE_ECONOMIC_EVALUATION_FAIL_GOVERNANCE_CLOSEOUT_V0"
        )
        assert _field_value(section, "GO_TOKEN") == OPERATOR_GO
        assert _field_value(section, "GO_TOKEN_CONSUMED") == "true"
        assert _field_value(section, "OFFLINE_ECONOMIC_EVALUATION_STATUS") == "COMPLETE_FAIL"
        assert _field_value(section, "HISTORICAL_ECONOMIC_RESULT") == "FAIL"
        assert _field_value(section, "ECONOMIC_VALIDITY_OFFLINE_GATE_PASS") == "false"
        assert _field_value(section, "PROMOTION_CANDIDATE_ELIGIBLE") == "false"
        assert _field_value(section, "NO_NEW_CANDIDATE_HOLD") == "ACTIVE"
        assert _field_value(section, "HISTORICAL_NEGATIVE_EVIDENCE_MUTATED") == "false"
        assert _field_value(section, "NEXT_CANONICAL_STEP") == TERMINAL_NEXT_STEP
        assert _field_value(section, "RUNTIME_EFFECT") == "NONE"
        assert _field_value(section, "AUTHORITY_EFFECT") == "NONE"
        assert EVALUATION_EVIDENCE_REF in _field_value(
            section, "OFFLINE_ECONOMIC_EVALUATION_EVIDENCE_REF"
        )


class TestResearchLineConsistency:
    def test_research_line_matches_authoritative_fail_state(self) -> None:
        section = _research_line_section(read_registry())
        assert _field_value(section, "STATUS") == "COMPLETE_FAIL"
        assert _field_value(section, "ECONOMIC_EVALUATION_STATUS") == "COMPLETE_FAIL"
        assert _field_value(section, "HISTORICAL_ECONOMIC_RESULT") == "FAIL"
        assert _field_value(section, "ECONOMIC_EVALUATION_EXECUTED") == "true"
        assert _field_value(section, "ECONOMIC_EVALUATION_AUTHORIZED") == "false"
        assert _field_value(section, "PROMOTION_ELIGIBLE") == "false"
        assert _field_value(section, "PROMOTION_CANDIDATE_ELIGIBLE") == "false"
        assert _field_value(section, "RUNTIME_REWIRE_ADMISSIBLE") == "false"
        assert _field_value(section, "RE_EVALUATION_ALLOWED") == "false"
        assert _field_value(section, "NO_NEW_CANDIDATE_HOLD") == "ACTIVE"
        assert _field_value(section, "NEXT_CANONICAL_STEP") == TERMINAL_NEXT_STEP
        assert _field_value(section, "HYPOTHESIS_ID") == HYPOTHESIS_ID
        assert _field_value(section, "ECONOMIC_EVALUATION_REASON_CODES") == REASON_CODES
        assert EVALUATION_EVIDENCE_REF in _field_value(
            section, "OFFLINE_ECONOMIC_EVALUATION_EVIDENCE_REF"
        )
