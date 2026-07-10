"""Contract tests for CS MA-crossover panel rank-rotation v0 scope ratification registry closeout."""

from __future__ import annotations

import re

from tests.ops.runbook_progress_registry_contract_helpers_v1 import (
    authoritative_field_value,
    read_registry,
)

CLOSEOUT_SECTION_PREFIX = (
    "#### CROSS_SECTIONAL_MA_CROSSOVER_PANEL_RANK_ROTATION_V0_RESEARCH_SCOPE_RATIFICATION_V1"
)
OPERATOR_GO = (
    "GO_RATIFY_CROSS_SECTIONAL_MA_CROSSOVER_PANEL_RANK_ROTATION_V0_"
    "RESEARCH_SCOPE_NO_EVAL_NO_RUNTIME_AUTHORITY_V1"
)
STRATEGY_TARGET = "cross_sectional_ma_crossover_panel_rank_rotation&#47;v0"
PHASE3_GO = "GO_BOUNDED_OKX_PRODUCTION_LIFECYCLE_SOURCE_REGISTRATION_AND_PT1H_PANEL_OHLCV_INGEST_V0"


def _field_value(text: str, field: str) -> str:
    match = re.search(rf"\| `{re.escape(field)}` \| `([^`]*)` \|", text)
    assert match, f"missing registry field: {field}"
    return match.group(1)


def _closeout_section(text: str) -> str:
    start = text.index(CLOSEOUT_SECTION_PREFIX)
    end = text.index("\n---\n\n## PR #4629 Evidence-Drift", start)
    return text[start:end]


class TestCrossSectionalMaCrossoverPanelRankRotationV0ResearchScopeRatificationRegistry:
    def test_scope_definition_ratified_without_evaluation_or_dataset(self) -> None:
        assert (
            authoritative_field_value(
                "CROSS_SECTIONAL_MA_CROSSOVER_PANEL_RANK_ROTATION_V0_RESEARCH_SCOPE_DEFINITION_RATIFIED"
            )
            == "true"
        )
        assert (
            authoritative_field_value(
                "CROSS_SECTIONAL_MA_CROSSOVER_PANEL_RANK_ROTATION_V0_RESEARCH_SCOPE_RATIFIED"
            )
            == "true"
        )
        assert (
            authoritative_field_value(
                "CROSS_SECTIONAL_MA_CROSSOVER_PANEL_RANK_ROTATION_V0_BINDING_RATIFIED"
            )
            == "false"
        )
        assert (
            authoritative_field_value(
                "CROSS_SECTIONAL_MA_CROSSOVER_PANEL_RANK_ROTATION_V0_DATASET_MATERIALIZED"
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
                "CROSS_SECTIONAL_MA_CROSSOVER_PANEL_RANK_ROTATION_V0_SINGLE_INSTRUMENT_EVIDENCE"
            )
            == "TERMINAL_NEGATIVE"
        )
        assert (
            authoritative_field_value(
                "CROSS_SECTIONAL_MA_CROSSOVER_PANEL_RANK_ROTATION_V0_UNCHANGED_SINGLE_INSTRUMENT_RETRY_BLOCKED"
            )
            == "true"
        )

    def test_pr5075_pr5076_pr5077_closeout_registered(self) -> None:
        assert authoritative_field_value("PR5075_CLOSEOUT_REGISTERED") == "true"
        assert authoritative_field_value("PR5076_CLOSEOUT_REGISTERED") == "true"
        assert authoritative_field_value("LAST_VERIFIED_PR") == "5077"

    def test_current_research_scope_and_phase3_go_registered(self) -> None:
        assert authoritative_field_value("CURRENT_RESEARCH_SCOPE") == STRATEGY_TARGET
        assert (
            authoritative_field_value(
                "CROSS_SECTIONAL_MA_CROSSOVER_PANEL_RANK_ROTATION_V0_PHASE3_GO_TOKEN_TO_REGISTER_ONLY"
            )
            == PHASE3_GO
        )


class TestCloseoutSection:
    def test_closeout_records_pass_without_authority_effect(self) -> None:
        section = _closeout_section(read_registry())
        assert _field_value(section, "STATUS") == "COMPLETE"
        assert _field_value(section, "GO_TOKEN") == OPERATOR_GO
        assert (
            _field_value(section, "STRATEGY_ID")
            == "cross_sectional_ma_crossover_panel_rank_rotation"
        )
        assert _field_value(section, "STRATEGY_VERSION") == "v0"
        assert _field_value(section, "RESEARCH_SCOPE_RATIFIED") == "true"
        assert _field_value(section, "DATASET_MATERIALIZED") == "false"
        assert _field_value(section, "ECONOMIC_EVALUATION_EXECUTED") == "false"
        assert _field_value(section, "SINGLE_INSTRUMENT_EVIDENCE") == "TERMINAL_NEGATIVE"
        assert _field_value(section, "PANEL_ARCHETYPE_EVIDENCE") == "NOT_PREVIOUSLY_EXECUTED"
        assert _field_value(section, "MATERIAL_DIFFERENCE_CONFIRMED") == "true"
        assert _field_value(section, "NEXT_CANONICAL_STEP") == (
            "PHASE3_DATASET_MATERIALIZATION_REQUIRES_SEPARATE_GO"
        )
        assert _field_value(section, "RUNTIME_EFFECT") == "NONE"
        assert _field_value(section, "AUTHORITY_EFFECT") == "NONE"
