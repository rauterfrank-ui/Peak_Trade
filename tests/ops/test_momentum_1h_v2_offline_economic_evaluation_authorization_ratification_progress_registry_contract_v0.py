"""Contract tests for momentum_1h/v2 authorization ratification progress registry."""

from __future__ import annotations

import re

from tests.ops.runbook_progress_registry_contract_helpers_v1 import read_registry

CLOSEOUT_SECTION_PREFIX = (
    "#### MOMENTUM_1H_V2_OFFLINE_ECONOMIC_EVALUATION_AUTHORIZATION_RATIFICATION_V0"
)
OPERATOR_GO = "GO_MOMENTUM_1H_V2_OFFLINE_ECONOMIC_EVALUATION_AUTHORIZATION_RATIFICATION_V0"
STRATEGY_TARGET = "momentum_1h&#47;v2"
BINDING_DIGEST = "366f7aeb21d781a2531d477ef32943c04d5edb262b7be9e540bbfcfc2528985f"


def _field_value(text: str, field: str) -> str:
    match = re.search(rf"\| `{re.escape(field)}` \| `([^`]*)` \|", text)
    assert match, f"missing registry field: {field}"
    return match.group(1)


def _closeout_section(text: str) -> str:
    start = text.index(CLOSEOUT_SECTION_PREFIX)
    end = text.index("\n---\n\n## PR #4629 Evidence-Drift", start)
    return text[start:end]


class TestMomentum1hV2AuthorizationRatificationProgressRegistry:
    def test_global_hold_remains_active(self) -> None:
        text = read_registry()
        assert _field_value(text, "NO_NEW_CANDIDATE_HOLD") == "ACTIVE"
        assert _field_value(text, "MOMENTUM_1H_V2_GLOBAL_HOLD_RELAXED") == "false"
        assert _field_value(text, "MOMENTUM_1H_V2_CANDIDATE_SPECIFIC_AUTHORIZATION") == "true"

    def test_authorization_ratified_without_evaluation(self) -> None:
        text = read_registry()
        assert (
            _field_value(
                text,
                "MOMENTUM_1H_V2_OFFLINE_ECONOMIC_EVALUATION_AUTHORIZATION_STATUS",
            )
            == "RATIFIED"
        )
        assert _field_value(text, "MOMENTUM_1H_V2_OFFLINE_ECONOMIC_EVALUATION_EXECUTED") == "false"
        assert _field_value(text, "MOMENTUM_1H_V2_ECONOMIC_RESULT") == "NOT_EVALUATED"
        assert _field_value(text, "ECONOMIC_EVALUATION_AUTHORIZED") == "false"
        assert _field_value(text, "MOMENTUM_1H_V2_ECONOMIC_EVALUATION_AUTHORIZED") == "false"

    def test_trend_following_v2_terminal_state_unchanged(self) -> None:
        text = read_registry()
        assert _field_value(text, "TREND_FOLLOWING_V2_HISTORICAL_ECONOMIC_RESULT") == "FAIL"
        assert (
            _field_value(text, "TREND_FOLLOWING_V2_UNCHANGED_BINDING_RETRY_ADMISSIBLE") == "false"
        )
        assert (
            _field_value(text, "TREND_FOLLOWING_V2_NEXT_ADMISSIBLE_SCOPE")
            == "NONE_WITHOUT_NEW_OPERATOR_RATIFICATION"
        )

    def test_runtime_and_promotion_blocked(self) -> None:
        text = read_registry()
        assert _field_value(text, "MOMENTUM_1H_V2_PROMOTION_ELIGIBLE") == "false"
        assert _field_value(text, "MOMENTUM_1H_V2_RUNTIME_REWIRE_ADMISSIBLE") == "false"
        assert _field_value(text, "MOMENTUM_1H_V2_ROBUSTNESS_ADMISSIBLE") == "false"
        assert _field_value(text, "MOMENTUM_1H_V2_ECONOMIC_VALIDITY_OFFLINE_GATE_PASS") == "false"

    def test_closeout_section_fields(self) -> None:
        section = _closeout_section(read_registry())
        assert _field_value(section, "GO_TOKEN") == OPERATOR_GO
        assert _field_value(section, "RESEARCH_SCOPE") == STRATEGY_TARGET
        assert _field_value(section, "BINDING_DIGEST") == BINDING_DIGEST
        assert _field_value(section, "AUTHORIZATION_STATUS") == "RATIFIED"
        assert _field_value(section, "ECONOMIC_EVALUATION_EXECUTED") == "false"
        assert _field_value(section, "ECONOMIC_RESULT") == "NOT_EVALUATED"
        assert _field_value(section, "NO_NEW_CANDIDATE_HOLD_BEFORE") == "ACTIVE"
        assert _field_value(section, "NO_NEW_CANDIDATE_HOLD_AFTER") == "ACTIVE"
        assert _field_value(section, "GLOBAL_HOLD_RELAXED") == "false"
        assert _field_value(section, "TREND_FOLLOWING_V2_RETRY_ADMISSIBLE") == "false"
        assert _field_value(section, "RUNTIME_EFFECT") == "NONE"
        assert _field_value(section, "AUTHORITY_EFFECT") == "OFFLINE_EVALUATION_AUTHORIZATION_ONLY"
