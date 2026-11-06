"""Contract tests for CS MA-crossover panel rank-rotation v0 Phase 3 registry closeout."""

from __future__ import annotations

import re

from tests.ops.runbook_progress_registry_contract_helpers_v1 import (
    authoritative_field_value,
    read_registry,
)

CLOSEOUT_SECTION_PREFIX = (
    "#### CROSS_SECTIONAL_MA_CROSSOVER_PANEL_RANK_ROTATION_V0_PHASE3_DATASET_MATERIALIZATION_V1"
)
PHASE3_GO = "GO_BOUNDED_OKX_PRODUCTION_LIFECYCLE_SOURCE_REGISTRATION_AND_PT1H_PANEL_OHLCV_INGEST_V0"


def _field_value(text: str, field: str) -> str:
    match = re.search(rf"\| `{re.escape(field)}` \| `([^`]*)` \|", text)
    assert match, f"missing registry field: {field}"
    return match.group(1)


def _closeout_section(text: str) -> str:
    start = text.index(CLOSEOUT_SECTION_PREFIX)
    end = text.index("\n---\n\n## PR #4629 Evidence-Drift", start)
    return text[start:end]


class TestCrossSectionalMaCrossoverPanelRankRotationV0Phase3DatasetMaterializationRegistry:
    def test_current_scope_dataset_materialized_without_eval(self) -> None:
        assert (
            authoritative_field_value(
                "CROSS_SECTIONAL_MA_CROSSOVER_PANEL_RANK_ROTATION_V0_DATASET_MATERIALIZED"
            )
            == "true"
        )
        assert (
            authoritative_field_value(
                "CROSS_SECTIONAL_MA_CROSSOVER_PANEL_RANK_ROTATION_V0_BINDING_RATIFIED"
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
                "CROSS_SECTIONAL_MA_CROSSOVER_PANEL_RANK_ROTATION_V0_PHASE3_GO_TOKEN_CONSUMED"
            )
            == "true"
        )


class TestPhase3CloseoutSection:
    def test_closeout_records_dataset_without_authority_effect(self) -> None:
        section = _closeout_section(read_registry())
        assert _field_value(section, "STATUS") == "COMPLETE"
        assert _field_value(section, "GO_TOKEN") == PHASE3_GO
        assert _field_value(section, "GO_TOKEN_CONSUMED") == "true"
        assert _field_value(section, "DATASET_MATERIALIZED") == "true"
        assert _field_value(section, "ECONOMIC_EVALUATION_EXECUTED") == "false"
        assert _field_value(section, "BITCOIN_PRESENT") == "false"
        assert _field_value(section, "NEXT_CANONICAL_STEP") == (
            "VERSIONED_BINDING_RATIFICATION_REQUIRES_SEPARATE_OPERATOR_GO"
        )
        assert _field_value(section, "RUNTIME_EFFECT") == "NONE"
        assert _field_value(section, "AUTHORITY_EFFECT") == "NONE"
