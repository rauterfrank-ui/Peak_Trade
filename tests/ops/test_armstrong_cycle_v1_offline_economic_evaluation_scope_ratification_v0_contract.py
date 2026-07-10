"""Contract tests for armstrong_cycle/v1 offline economic evaluation scope ratification v0."""

from __future__ import annotations

import json
from pathlib import Path

from src.research.armstrong_cycle_v1_offline_economic_evaluation_scope_ratification_v0 import (
    DATASET_DIGEST,
    GOVERNANCE_REL_PATH,
    HYPOTHESIS_ID,
    MATERIAL_DIFFERENCE_CONFIG_REL_PATH,
    NEXT_GO_TOKEN,
    OPERATOR_GO_TOKEN,
    RESEARCH_SCOPE,
    SCOPE_RATIFICATION_CONFIG_REL_PATH,
    SIGNAL_FAMILY,
    SOURCE_EVIDENCE_DIR,
    VERSIONED_BINDING_CONFIG_REL_PATH,
    materialize_evaluation_config_v1,
    materialize_material_difference_contract_v0,
    materialize_scope_ratification_v0,
    materialize_versioned_research_binding_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SCOPE_CONFIG = REPO_ROOT / SCOPE_RATIFICATION_CONFIG_REL_PATH
BINDING_CONFIG = REPO_ROOT / VERSIONED_BINDING_CONFIG_REL_PATH
GOVERNANCE_DOC = REPO_ROOT / GOVERNANCE_REL_PATH
MATERIAL_DIFFERENCE_CONFIG = REPO_ROOT / MATERIAL_DIFFERENCE_CONFIG_REL_PATH
SOURCE_EVIDENCE_SUFFIX = (
    "discover_and_rank_new_distinct_futures_research_scope_or_evidence_class_"
    "post_el_karoui_inconclusive_read_only_v0_20260710T151847Z"
)


class TestArmstrongCycleV1OfflineEconomicEvaluationScopeRatificationV0Contract:
    def test_scope_ratification_config_gates(self) -> None:
        payload = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        assert payload["candidate_id"] == RESEARCH_SCOPE
        assert payload["hypothesis_id"] == HYPOTHESIS_ID
        assert payload["signal_family"] == SIGNAL_FAMILY
        assert payload["futures_only"] is True
        assert payload["bitcoin_direction_allowed"] is False
        assert payload["bitcoin_present"] is False
        assert payload["offline_economic_evaluation_scope_ratified"] is True
        assert payload["economic_evaluation_executed"] is False
        assert payload["economic_evaluation_authorized"] is False
        assert payload["parameter_search_forbidden"] is True
        assert payload["material_difference_confirmed"] is True
        assert payload["prior_evidence_exclusion_pass"] is True
        assert payload["runtime_effect"] == "NONE"
        assert payload["authority_effect"] == "NONE"
        assert payload["next_go_token"] == NEXT_GO_TOKEN
        assert SOURCE_EVIDENCE_SUFFIX in payload["source_ratification_evidence_ref"]

    def test_versioned_binding_complete(self) -> None:
        payload = json.loads(BINDING_CONFIG.read_text(encoding="utf-8"))
        assert payload["candidate_id"] == RESEARCH_SCOPE
        assert payload["binding_ratified"] is True
        assert payload["binding"]["binding_status"]["overall_binding_status"] == "COMPLETE"
        assert payload["economic_evaluation_executed"] is False
        assert payload["trading_logic_mutated"] is False
        assert payload["material_difference_proven"] is True
        assert (
            payload["binding"]["prior_evidence_exclusion"]["prior_evidence_exclusion_pass"] is True
        )
        assert (
            "ehlers_cycle_filter/v1"
            in payload["binding"]["prior_evidence_exclusion"][
                "excluded_terminal_inconclusive_bindings"
            ]
        )
        assert (
            "el_karoui_vol_model/v1"
            in payload["binding"]["prior_evidence_exclusion"][
                "excluded_terminal_inconclusive_bindings"
            ]
        )
        calendar = payload["binding"]["calendar_binding"]
        assert calendar["timezone"] == "UTC"
        assert calendar["calendar_origin"] == "2015-10-01"
        assert calendar["no_lookahead"] is True

    def test_material_difference_contract(self) -> None:
        payload = json.loads(MATERIAL_DIFFERENCE_CONFIG.read_text(encoding="utf-8"))
        assert payload["material_difference_confirmed"] is True
        assert payload["material_difference_vs_ehlers_cycle_filter_v1_confirmed"] is True
        assert payload["material_difference_vs_el_karoui_vol_model_v1_confirmed"] is True
        assert payload["signal_family"] == SIGNAL_FAMILY

    def test_governance_doc_non_authorizing(self) -> None:
        text = GOVERNANCE_DOC.read_text(encoding="utf-8")
        assert "LIVE_AUTHORIZED: false" in text
        assert "ORDERS_ALLOWED: false" in text
        assert "ECONOMIC_EVALUATION_EXECUTED` | `false`" in text
        assert "armstrong_cycle" in text
        assert NEXT_GO_TOKEN in text

    def test_materializers_match_committed_ratification_core(self) -> None:
        evaluation_config = materialize_evaluation_config_v1(REPO_ROOT)
        material_difference = materialize_material_difference_contract_v0()
        versioned_binding = materialize_versioned_research_binding_v0(
            REPO_ROOT,
            material_difference=material_difference,
            evaluation_config=evaluation_config,
        )
        scope_ratification = materialize_scope_ratification_v0(
            versioned_binding,
            material_difference,
        )
        committed_binding = json.loads(BINDING_CONFIG.read_text(encoding="utf-8"))
        committed_scope = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        assert committed_binding["binding_digest"] == versioned_binding["binding_digest"]
        assert committed_binding["binding"]["dataset_binding"]["dataset_digest"] == DATASET_DIGEST
        assert (
            json.loads(MATERIAL_DIFFERENCE_CONFIG.read_text(encoding="utf-8"))
            == material_difference
        )
        assert committed_scope["binding_digest"] == scope_ratification["binding_digest"]
        assert committed_scope["economic_evaluation_executed"] is False
        assert versioned_binding["go_token"] == OPERATOR_GO_TOKEN

    def test_source_evidence_dir_referenced(self) -> None:
        payload = json.loads(BINDING_CONFIG.read_text(encoding="utf-8"))
        assert str(SOURCE_EVIDENCE_DIR) in payload["source_ratification_evidence_ref"]
