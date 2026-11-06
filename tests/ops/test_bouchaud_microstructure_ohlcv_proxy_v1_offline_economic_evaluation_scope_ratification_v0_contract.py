"""Contract tests for bouchaud OHLCV proxy v1 offline economic evaluation scope ratification v0."""

from __future__ import annotations

import json
from pathlib import Path

from src.research.bouchaud_microstructure_ohlcv_proxy_v1_offline_economic_evaluation_scope_ratification_v0 import (
    DATASET_DIGEST,
    DATA_PERIOD,
    NEXT_GO_TOKEN,
    HYPOTHESIS_ID,
    INSTRUMENT_ID,
    MATERIAL_DIFFERENCE_CONFIG_REL_PATH,
    NEXT_GO_TOKEN,
    PRIOR_BINDING_DIGEST,
    PRIOR_CONFIG_DIGEST,
    PRIOR_IMPLEMENTATION_DIGEST,
    RESEARCH_SCOPE,
    SCOPE_RATIFICATION_CONFIG_REL_PATH,
    SIGNAL_FAMILY,
    VERSIONED_BINDING_CONFIG_REL_PATH,
    materialize_scope_ratification_v0,
    materialize_versioned_research_binding_v0,
    load_committed_evaluation_config_v1,
    load_committed_material_difference_v0,
    load_committed_scope_separation_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SCOPE_CONFIG = REPO_ROOT / SCOPE_RATIFICATION_CONFIG_REL_PATH
BINDING_CONFIG = REPO_ROOT / VERSIONED_BINDING_CONFIG_REL_PATH
MATERIAL_DIFFERENCE_CONFIG = REPO_ROOT / MATERIAL_DIFFERENCE_CONFIG_REL_PATH
PR5097_CLOSEOUT_SUFFIX = (
    "pr5097_merge_closeout_bouchaud_microstructure_ohlcv_proxy_v1_step29m_single_instrument_"
    "offline_evaluation_adapter_implementation_v0_20260710T172226Z"
)


class TestBouchaudMicrostructureOhlcvProxyV1OfflineEconomicEvaluationScopeRatificationV0Contract:
    def test_scope_ratification_config_gates(self) -> None:
        payload = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        assert payload["candidate_id"] == RESEARCH_SCOPE
        assert payload["research_scope"] == RESEARCH_SCOPE
        assert payload["hypothesis_id"] == HYPOTHESIS_ID
        assert payload["signal_family"] == SIGNAL_FAMILY
        assert payload["instrument_id"] == INSTRUMENT_ID
        assert payload["data_period"] == DATA_PERIOD
        assert payload["data_digest"] == DATASET_DIGEST
        assert payload["proxy_semantics"] is True
        assert payload["true_tick_l2_microstructure"] is False
        assert payload["data_class"] == "FINALIZED_OHLCV_BARS"
        assert payload["tick_l2_status"] == "NOT_IMPLEMENTED_DATA_CAPABILITY_MISSING"
        assert payload["offline_economic_evaluation_scope_ratified"] is True
        assert payload["offline_only"] is True
        assert payload["single_instrument_only"] is True
        assert payload["economic_evaluation_executed"] is False
        assert payload["economic_evaluation_authorized"] is False
        assert payload["evaluation_execution_authorized"] is False
        assert payload["evaluation_infrastructure_ready"] is True
        assert payload["parameter_search_forbidden"] is True
        assert payload["material_difference_confirmed"] is True
        assert payload["runtime_effect"] == "NONE"
        assert payload["authority_effect"] == "NONE"
        assert payload["next_go_token"] == NEXT_GO_TOKEN
        assert payload["go_token"] == NEXT_GO_TOKEN
        assert payload["prior_config_digest"] == PRIOR_CONFIG_DIGEST
        assert payload["prior_implementation_digest"] == PRIOR_IMPLEMENTATION_DIGEST
        assert payload["prior_binding_digest"] == PRIOR_BINDING_DIGEST
        assert PR5097_CLOSEOUT_SUFFIX in payload["source_ratification_evidence_ref"]
        assert (
            "run_bouchaud_microstructure_ohlcv_proxy_v1_bound_offline_economic_baseline_evaluation_v0.py"
            in payload["canonical_evaluation_runner"]
        )

    def test_versioned_binding_complete(self) -> None:
        payload = json.loads(BINDING_CONFIG.read_text(encoding="utf-8"))
        assert payload["candidate_id"] == RESEARCH_SCOPE
        assert payload["binding_ratified"] is True
        assert payload["binding"]["binding_status"]["overall_binding_status"] == "COMPLETE"
        assert payload["economic_evaluation_executed"] is False
        assert payload["evaluation_authorized"] is False
        assert payload["evaluation_infrastructure_ready"] is True
        assert payload["proxy_semantics"] is True
        assert payload["true_tick_l2_microstructure"] is False
        assert payload["trading_logic_mutated"] is False
        assert payload["material_difference_proven"] is True
        refs = payload["binding"]["external_bindings"]
        assert refs["evaluation_runner_ref"]["status"] == "BOUND"
        assert refs["invocation_wrapper_ref"]["status"] == "BOUND"
        assert refs["scope_ratification_config_ref"]["status"] == "BOUND"

    def test_materializers_match_committed_ratification_core(self) -> None:
        evaluation_config = load_committed_evaluation_config_v1(REPO_ROOT)
        material_difference = load_committed_material_difference_v0(REPO_ROOT)
        scope_separation = load_committed_scope_separation_v0(REPO_ROOT)
        versioned_binding = materialize_versioned_research_binding_v0(
            REPO_ROOT,
            material_difference=material_difference,
            evaluation_config=evaluation_config,
        )
        scope_ratification = materialize_scope_ratification_v0(
            versioned_binding,
            material_difference,
            scope_separation,
        )
        committed_binding = json.loads(BINDING_CONFIG.read_text(encoding="utf-8"))
        committed_scope = json.loads(SCOPE_CONFIG.read_text(encoding="utf-8"))
        assert committed_binding["binding_digest"] == versioned_binding["binding_digest"]
        assert committed_binding["binding"]["dataset_binding"]["dataset_digest"] == DATASET_DIGEST
        assert committed_scope["binding_digest"] == scope_ratification["binding_digest"]
        assert committed_scope["economic_evaluation_executed"] is False
        assert committed_scope["config_digest"] == PRIOR_CONFIG_DIGEST

    def test_deterministic_repeated_materialization(self) -> None:
        evaluation_config = load_committed_evaluation_config_v1(REPO_ROOT)
        material_difference = load_committed_material_difference_v0(REPO_ROOT)
        scope_separation = load_committed_scope_separation_v0(REPO_ROOT)
        first_binding = materialize_versioned_research_binding_v0(
            REPO_ROOT,
            material_difference=material_difference,
            evaluation_config=evaluation_config,
        )
        second_binding = materialize_versioned_research_binding_v0(
            REPO_ROOT,
            material_difference=material_difference,
            evaluation_config=evaluation_config,
        )
        first_scope = materialize_scope_ratification_v0(
            first_binding,
            material_difference,
            scope_separation,
        )
        second_scope = materialize_scope_ratification_v0(
            second_binding,
            material_difference,
            scope_separation,
        )
        assert first_binding == second_binding
        assert first_scope == second_scope

    def test_stale_config_digest_rejected_by_materializer_change(self) -> None:
        evaluation_config = load_committed_evaluation_config_v1(REPO_ROOT)
        material_difference = load_committed_material_difference_v0(REPO_ROOT)
        versioned_binding = materialize_versioned_research_binding_v0(
            REPO_ROOT,
            material_difference=material_difference,
            evaluation_config=evaluation_config,
        )
        tampered = dict(evaluation_config)
        tampered["backtest"] = dict(evaluation_config["backtest"])
        tampered["backtest"]["initial_cash"] = 99999.0
        with_tamper = materialize_versioned_research_binding_v0(
            REPO_ROOT,
            material_difference=material_difference,
            evaluation_config=tampered,
        )
        assert (
            versioned_binding["binding"]["digest_bindings"]["config_digest"]["value"]
            != with_tamper["binding"]["digest_bindings"]["config_digest"]["value"]
        )
