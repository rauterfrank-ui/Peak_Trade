"""Contract tests for CS MA-crossover panel rank-rotation v0 binding ratification registry."""

from __future__ import annotations

import re

from tests.ops.runbook_progress_registry_contract_helpers_v1 import (
    authoritative_field_value,
    read_registry,
)

CLOSEOUT_SECTION_PREFIX = (
    "#### CROSS_SECTIONAL_MA_CROSSOVER_PANEL_RANK_ROTATION_V0_VERSIONED_BINDING_RATIFICATION_V1"
)
BINDING_GO = "GO_VERSIONED_CROSS_SECTIONAL_MA_CROSSOVER_PANEL_RANK_ROTATION_V0_BINDING_RATIFICATION"
ECONOMIC_EVAL_GO = "GO_CROSS_SECTIONAL_MA_CROSSOVER_PANEL_RANK_ROTATION_V0_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0"


def _field_value(text: str, field: str) -> str:
    match = re.search(rf"\| `{re.escape(field)}` \| `([^`]*)` \|", text)
    assert match, f"missing registry field: {field}"
    return match.group(1)


def _closeout_section(text: str) -> str:
    start = text.index(CLOSEOUT_SECTION_PREFIX)
    end = text.index("\n---\n\n## PR #4629 Evidence-Drift", start)
    return text[start:end]


class TestCrossSectionalMaCrossoverPanelRankRotationV0BindingRatificationRegistry:
    def test_binding_ratified_without_evaluation(self) -> None:
        assert (
            authoritative_field_value(
                "CROSS_SECTIONAL_MA_CROSSOVER_PANEL_RANK_ROTATION_V0_BINDING_RATIFIED"
            )
            == "true"
        )
        assert (
            authoritative_field_value(
                "CROSS_SECTIONAL_MA_CROSSOVER_PANEL_RANK_ROTATION_V0_ALL_REQUIRED_BINDINGS_RATIFIED"
            )
            == "true"
        )
        assert (
            authoritative_field_value(
                "CROSS_SECTIONAL_MA_CROSSOVER_PANEL_RANK_ROTATION_V0_ECONOMIC_EVALUATION_EXECUTED"
            )
            == "false"
        )
        assert (
            authoritative_field_value(
                "CROSS_SECTIONAL_MA_CROSSOVER_PANEL_RANK_ROTATION_V0_ECONOMIC_EVALUATION_AUTHORIZED"
            )
            == "false"
        )
        assert authoritative_field_value("PR5078_CLOSEOUT_REGISTERED") == "true"
        assert authoritative_field_value("LAST_VERIFIED_PR") == "5078"

    def test_next_step_requires_separate_economic_eval_go(self) -> None:
        assert authoritative_field_value("NEXT_STEP") == (
            "AWAIT_OPERATOR_OFFLINE_ECONOMIC_EVALUATION_GO_CROSS_SECTIONAL_MA_CROSSOVER_PANEL_RANK_ROTATION_V0"
        )
        assert (
            authoritative_field_value(
                "CROSS_SECTIONAL_MA_CROSSOVER_PANEL_RANK_ROTATION_V0_ECONOMIC_EVALUATION_GO_TOKEN"
            )
            == ECONOMIC_EVAL_GO
        )


class TestBindingRatificationCloseoutSection:
    def test_closeout_records_binding_without_authority_effect(self) -> None:
        section = _closeout_section(read_registry())
        assert _field_value(section, "STATUS") == "COMPLETE"
        assert _field_value(section, "GO_TOKEN") == BINDING_GO
        assert _field_value(section, "GO_TOKEN_CONSUMED") == "true"
        assert _field_value(section, "BINDING_RATIFIED") == "true"
        assert _field_value(section, "ALL_REQUIRED_BINDINGS_RATIFIED") == "true"
        assert _field_value(section, "DATASET_MATERIALIZED") == "true"
        assert _field_value(section, "ECONOMIC_EVALUATION_EXECUTED") == "false"
        assert _field_value(section, "BITCOIN_PRESENT") == "false"
        assert _field_value(section, "NEXT_CANONICAL_STEP") == (
            "AWAIT_OPERATOR_OFFLINE_ECONOMIC_EVALUATION_GO_CROSS_SECTIONAL_MA_CROSSOVER_PANEL_RANK_ROTATION_V0"
        )
        assert _field_value(section, "RUNTIME_EFFECT") == "NONE"
        assert _field_value(section, "AUTHORITY_EFFECT") == "NONE"
