"""Contract tests for ehlers_cycle_filter/v1 offline economic evaluation scope ratification v0."""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCOPE_CONFIG = (
    REPO_ROOT
    / "config/research/ehlers_cycle_filter_v1_offline_economic_evaluation_scope_ratification_v0.json"
)
BINDING_CONFIG = (
    REPO_ROOT / "config/research/ehlers_cycle_filter_v1_versioned_research_binding_v0.json"
)
GOVERNANCE_DOC = (
    REPO_ROOT
    / "docs/governance/EHLERS_CYCLE_FILTER_V1_OFFLINE_ECONOMIC_EVALUATION_SCOPE_RATIFICATION_V0.md"
)
SOURCE_EVIDENCE_SUFFIX = "discover_and_rank_new_distinct_futures_research_scope_or_evidence_class_read_only_v0_20260710T104236Z"


class TestEhlersCycleFilterV1OfflineEconomicEvaluationScopeRatificationV0Contract:
    def test_scope_ratification_config_gates(self) -> None:
        payload = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        assert payload["candidate_id"] == "ehlers_cycle_filter/v1"
        assert payload["hypothesis_id"] == "EHLERS_DSP_CYCLE_BANDPASS_NON_BITCOIN_FUTURES_V1"
        assert payload["signal_family"] == "DSP_CYCLE_BANDPASS"
        assert payload["futures_only"] is True
        assert payload["bitcoin_direction_allowed"] is False
        assert payload["offline_economic_evaluation_scope_ratified"] is True
        assert payload["economic_evaluation_executed"] is False
        assert payload["economic_evaluation_authorized"] is False
        assert payload["parameter_search_forbidden"] is True
        assert payload["material_difference_confirmed"] is True
        assert payload["prior_evidence_exclusion_pass"] is True
        assert payload["runtime_effect"] == "NONE"
        assert payload["authority_effect"] == "NONE"
        assert SOURCE_EVIDENCE_SUFFIX in payload["source_ratification_evidence_ref"]

    def test_versioned_binding_complete(self) -> None:
        payload = json.loads(BINDING_CONFIG.read_text(encoding="utf-8"))
        assert payload["candidate_id"] == "ehlers_cycle_filter/v1"
        assert payload["binding"]["binding_status"]["overall_binding_status"] == "COMPLETE"
        assert payload["economic_evaluation_executed"] is True
        assert payload["economic_evaluation_status"] == "COMPLETE_INCONCLUSIVE"
        assert payload["trading_logic_mutated"] is False
        assert (
            payload["binding"]["prior_evidence_exclusion"]["prior_evidence_exclusion_pass"] is True
        )

    def test_governance_doc_non_authorizing(self) -> None:
        text = GOVERNANCE_DOC.read_text(encoding="utf-8")
        assert "LIVE_AUTHORIZED: false" in text
        assert "ORDERS_ALLOWED: false" in text
        assert "ECONOMIC_EVALUATION_EXECUTED` | `false`" in text
        assert "ehlers_cycle_filter" in text
