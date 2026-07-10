"""Contract tests for el_karoui_vol_model/v1 offline economic evaluation scope ratification v0."""

from __future__ import annotations

import json
from pathlib import Path

from src.research.el_karoui_vol_model_v1_offline_economic_evaluation_scope_ratification_v0 import (
    DATASET_DIGEST,
    GOVERNANCE_REL_PATH,
    HYPOTHESIS_ID,
    MATERIAL_DIFFERENCE_CONFIG_REL_PATH,
    NEXT_GO_TOKEN,
    OPERATOR_GO_TOKEN,
    RESEARCH_SCOPE,
    SCOPE_RATIFICATION_CONFIG_REL_PATH,
    SIGNAL_FAMILY,
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
PR5087_CLOSEOUT_SUFFIX = (
    "pr5087_merge_closeout_ehlers_cycle_filter_v1_terminal_inconclusive_registration_and_"
    "distinct_scope_decision_v0_20260710T124722Z"
)


class TestElKarouiVolModelV1OfflineEconomicEvaluationScopeRatificationV0Contract:
    def test_scope_ratification_config_gates(self) -> None:
        payload = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        assert payload["candidate_id"] == RESEARCH_SCOPE
        assert payload["hypothesis_id"] == HYPOTHESIS_ID
        assert payload["signal_family"] == SIGNAL_FAMILY
        assert payload["futures_only"] is True
        assert payload["bitcoin_direction_allowed"] is False
        assert payload["bitcoin_present"] is False
        assert payload["offline_economic_evaluation_scope_ratified"] is True
        assert payload["economic_evaluation_executed"] is True
        assert payload["economic_evaluation_status"] == "COMPLETE_INCONCLUSIVE"
        assert payload["economic_evaluation_authorized"] is False
        assert payload["baseline_verdict"] == "INCONCLUSIVE"
        assert payload["unchanged_retry_blocked"] is True
        assert payload["promotion_admissible"] is False
        assert payload["parameter_search_forbidden"] is True
        assert payload["material_difference_confirmed"] is True
        assert payload["prior_evidence_exclusion_pass"] is True
        assert payload["runtime_effect"] == "NONE"
        assert payload["authority_effect"] == "NONE"
        assert (
            payload["next_go_token"] == "NEW_DISTINCT_RESEARCH_SCOPE_OR_NEW_EVIDENCE_CLASS_REQUIRED"
        )
        assert PR5087_CLOSEOUT_SUFFIX in payload["source_ratification_evidence_ref"]

    def test_versioned_binding_complete(self) -> None:
        payload = json.loads(BINDING_CONFIG.read_text(encoding="utf-8"))
        assert payload["candidate_id"] == RESEARCH_SCOPE
        assert payload["binding_ratified"] is True
        assert payload["binding"]["binding_status"]["overall_binding_status"] == "COMPLETE"
        assert payload["economic_evaluation_executed"] is True
        assert payload["economic_evaluation_status"] == "COMPLETE_INCONCLUSIVE"
        assert payload["baseline_verdict"] == "INCONCLUSIVE"
        assert payload["terminal_inconclusive_evidence_for_unchanged_binding"] is True
        assert payload["unchanged_retry_blocked"] is True
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

    def test_material_difference_contract(self) -> None:
        payload = json.loads(MATERIAL_DIFFERENCE_CONFIG.read_text(encoding="utf-8"))
        assert payload["material_difference_confirmed"] is True
        assert payload["material_difference_vs_ehlers_cycle_filter_v1_confirmed"] is True
        assert payload["baseline_scope"] == "ehlers_cycle_filter/v1"
        assert payload["signal_family"] == SIGNAL_FAMILY

    def test_governance_doc_non_authorizing(self) -> None:
        text = GOVERNANCE_DOC.read_text(encoding="utf-8")
        assert "LIVE_AUTHORIZED: false" in text
        assert "ORDERS_ALLOWED: false" in text
        assert "ECONOMIC_EVALUATION_EXECUTED` | `false`" in text
        assert "el_karoui_vol_model" in text
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
        assert committed_scope["economic_evaluation_executed"] is True
        assert versioned_binding["go_token"] == OPERATOR_GO_TOKEN
