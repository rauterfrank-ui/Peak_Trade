"""Contract tests for CS MA-crossover panel rank-rotation v0 research scope ratification v1."""

from __future__ import annotations

import json
from pathlib import Path

from src.research.cross_sectional_ma_crossover_panel_rank_rotation_v0_research_scope_ratification_v1 import (
    FAST_WINDOW,
    OPERATOR_GO_SCOPE_RATIFICATION,
    PHASE3_GO_TOKEN_TO_REGISTER_ONLY,
    RECOMMENDED_SCOPE_ID,
    SLOW_WINDOW,
    STRATEGY_ID,
    STRATEGY_VERSION,
    TERMINAL_UNDERLYING_CONFIG_DIGEST,
    TERMINAL_UNDERLYING_DATASET_DIGEST,
    TERMINAL_UNDERLYING_SIGNAL_BINDING,
    UNDERLYING_SIGNAL_BINDING,
    ValidationVerdictEnum,
    materialize_ma_crossover_panel_rank_rotation_research_scope_ratification_v1,
    validate_ma_crossover_panel_rank_rotation_research_scope_ratification_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
GOVERNANCE_DOC = (
    REPO_ROOT / "docs/research/"
    "CROSS_SECTIONAL_MA_CROSSOVER_PANEL_RANK_ROTATION_V0_RESEARCH_SCOPE_RATIFICATION.md"
)
SCOPE_CONFIG = (
    REPO_ROOT / "config/research/"
    "cross_sectional_ma_crossover_panel_rank_rotation_v0_research_scope_ratification_v1.json"
)
PANEL_BINDING_CONFIG = (
    REPO_ROOT / "config/research/"
    "cross_sectional_ma_crossover_panel_rank_rotation_v0_panel_universe_dataset_binding_v0.json"
)
MATERIAL_DIFFERENCE_CONFIG = (
    REPO_ROOT / "config/research/"
    "cross_sectional_ma_crossover_panel_rank_rotation_v0_material_difference_and_non_claim_contract_v0.json"
)
UNCHANGED_RETRY_CONFIG = (
    REPO_ROOT / "config/research/"
    "cross_sectional_ma_crossover_panel_rank_rotation_v0_unchanged_retry_and_near_duplicate_block_v0.json"
)
PHASE3_CONFIG = (
    REPO_ROOT / "config/research/"
    "cross_sectional_ma_crossover_panel_rank_rotation_v0_phase3_precondition_contract_v0.json"
)


class TestCrossSectionalMaCrossoverPanelRankRotationV0ResearchScopeRatificationV1:
    def test_ratification_materializes_with_required_fields(self) -> None:
        ratification = materialize_ma_crossover_panel_rank_rotation_research_scope_ratification_v1(
            repo_root=REPO_ROOT,
        )
        validation = validate_ma_crossover_panel_rank_rotation_research_scope_ratification_v1(
            ratification
        )
        assert validation.verdict == ValidationVerdictEnum.ACCEPTED
        assert ratification["recommended_scope_id"] == RECOMMENDED_SCOPE_ID
        assert ratification["operator_go_token"] == OPERATOR_GO_SCOPE_RATIFICATION
        assert ratification["strategy_id"] == STRATEGY_ID
        assert ratification["strategy_version"] == STRATEGY_VERSION
        assert ratification["underlying_signal_binding"] == UNDERLYING_SIGNAL_BINDING
        assert ratification["research_scope_definition_ratified"] is True
        assert ratification["research_scope_ratified"] is True
        assert ratification["binding_ratified"] is False
        assert ratification["dataset_materialized"] is False
        assert ratification["single_instrument_evidence"] == "TERMINAL_NEGATIVE"
        assert ratification["panel_archetype_evidence"] == "NOT_PREVIOUSLY_EXECUTED"
        assert ratification["unchanged_single_instrument_retry_blocked"] is True
        assert ratification["material_difference_confirmed"] is True
        assert ratification["signal_family_material_difference"] is False
        assert ratification["economic_evaluation_executed"] is False
        assert ratification["fast_window"] == FAST_WINDOW
        assert ratification["slow_window"] == SLOW_WINDOW
        assert ratification["phase3_go_token_to_register_only"] == PHASE3_GO_TOKEN_TO_REGISTER_ONLY
        assert (
            TERMINAL_UNDERLYING_SIGNAL_BINDING in ratification["terminal_failed_binding_exclusions"]
        )

    def test_governance_doc_exists_and_states_no_eval(self) -> None:
        text = GOVERNANCE_DOC.read_text(encoding="utf-8")
        assert RECOMMENDED_SCOPE_ID in text
        assert "TERMINAL_NEGATIVE" in text
        assert "NOT_PREVIOUSLY_EXECUTED" in text
        assert "DATASET_MATERIALIZED" in text
        assert "ma_crossover" in text.lower()
        assert "panel" in text.lower()

    def test_no_runtime_authority_in_ratification(self) -> None:
        ratification = materialize_ma_crossover_panel_rank_rotation_research_scope_ratification_v1(
            repo_root=REPO_ROOT,
        )
        assert ratification["authority_effect"] == "NONE"
        assert ratification["runtime_effect"] == "NONE"
        assert ratification["order_effect"] == "NONE"
        assert ratification["no_credentials"] is True
        assert ratification["no_live"] is True
        assert "DATASET_MATERIALIZATION" in ratification["prohibited_actions"]
        assert "NETWORK_INGEST" in ratification["prohibited_actions"]

    def test_scope_config_reflects_post_phase3_dataset_materialization(self) -> None:
        config = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        assert config["strategy_id"] == STRATEGY_ID
        assert config["dataset_materialized"] is True
        assert config["panel_staging_root"].endswith("pit_okx_linear_usdt_non_bitcoin_pt1h_panel/v2")
        assert config["phase3_precondition_contract"]["dataset_materialized"] is True

    def test_panel_binding_contract_futures_only_and_bitcoin_block(self) -> None:
        panel = json.loads(PANEL_BINDING_CONFIG.read_text(encoding="utf-8"))
        assert panel["futures_only"] is True
        assert panel["bitcoin_direction_allowed"] is False
        assert panel["spot_allowed"] is False
        assert panel["synthetic_spot_allowed"] is False
        assert panel["min_instruments"] == 5
        assert panel["selection_policy"] == "TOP1_BY_CANONICAL_MA_CROSSOVER_SCORE"

    def test_terminal_negative_underlying_digests_bound(self) -> None:
        unchanged = json.loads(UNCHANGED_RETRY_CONFIG.read_text(encoding="utf-8"))
        assert unchanged["terminal_underlying_signal_binding"] == TERMINAL_UNDERLYING_SIGNAL_BINDING
        assert unchanged["terminal_underlying_config_digest"] == TERMINAL_UNDERLYING_CONFIG_DIGEST
        assert unchanged["terminal_underlying_dataset_digest"] == TERMINAL_UNDERLYING_DATASET_DIGEST
        assert unchanged["unchanged_single_instrument_retry_blocked"] is True

    def test_material_difference_contract_and_phase3_post_materialization_boundary(self) -> None:
        material = json.loads(MATERIAL_DIFFERENCE_CONFIG.read_text(encoding="utf-8"))
        phase3 = json.loads(PHASE3_CONFIG.read_text(encoding="utf-8"))
        assert material["signal_family_material_difference"] is False
        assert material["single_instrument_evidence"] == "TERMINAL_NEGATIVE"
        assert phase3["dataset_materialization_authorized"] is True
        assert phase3["dataset_materialized"] is True
        assert phase3["economic_evaluation_authorized"] is False
        assert phase3["phase3_go_token_to_register_only"] == PHASE3_GO_TOKEN_TO_REGISTER_ONLY
        assert phase3["phase3_go_token_consumed"] is True
