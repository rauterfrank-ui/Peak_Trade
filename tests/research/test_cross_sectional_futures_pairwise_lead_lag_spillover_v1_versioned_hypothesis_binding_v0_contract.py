"""Contract tests for cross_sectional_futures_pairwise_lead_lag_spillover v1 hypothesis binding."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from src.research.cross_sectional_futures_lead_lag_information_diffusion_v0_versioned_hypothesis_binding_v0 import (
    SCORE_FAMILY_POLICY as LEAD_LAG_V0_SCORE_FAMILY,
    materialize_versioned_hypothesis_binding_v0 as materialize_prior_lead_lag_v0,
)
from src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_portfolio_binding_v0 import (
    BOUND_PORTFOLIO_BINDING_STATUS,
)
from src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_versioned_hypothesis_binding_v0 import (
    CONFIG_REL_PATH,
    GOVERNANCE_REL_PATH,
    PAIR_DEFINITION,
    PRIOR_LEAD_LAG_BINDING_DIGEST,
    PRIOR_LEAD_LAG_SCORE_FAMILY,
    RATIFIED_NORMALIZED_PANEL_DIGEST,
    RATIFIED_SEMANTIC_DATA_DIGEST,
    RESEARCH_SCOPE,
    SCORE_FAMILY_POLICY,
    materialize_and_validate_versioned_hypothesis_binding_v0,
    materialize_versioned_hypothesis_binding_v0,
    materializer_to_binder_roundtrip_v0,
    validate_pairwise_contract_rejections_v0,
    validate_prior_lead_lag_not_reused_unchanged_v0,
    validate_score_family_policy_v0,
    validate_versioned_hypothesis_binding_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPO_ROOT / CONFIG_REL_PATH
GOVERNANCE_DOC = REPO_ROOT / GOVERNANCE_REL_PATH
MATERIALIZER_PATH = (
    REPO_ROOT / "scripts/research/"
    "materialize_cross_sectional_futures_pairwise_lead_lag_spillover_v1_versioned_hypothesis_binding_v0.py"
)
FORBIDDEN_RUNTIME_IMPORT_PREFIXES = (
    "src.execution",
    "src.scheduler",
    "src.broker",
)


class TestHypothesisBindingMaterialization:
    def test_materialization_complete(self) -> None:
        result = materialize_and_validate_versioned_hypothesis_binding_v0()
        assert result.verdict.value == "COMPLETE"
        assert result.validation_verdict.value == "ACCEPTED_COMPLETE"
        assert result.fail_reasons == ()

    def test_deterministic_double_materialization(self) -> None:
        first = materialize_versioned_hypothesis_binding_v0()
        second = materialize_versioned_hypothesis_binding_v0()
        assert first == second

    def test_materializer_to_binder_roundtrip_pass(self) -> None:
        envelope = materialize_versioned_hypothesis_binding_v0()
        roundtrip = materializer_to_binder_roundtrip_v0(envelope)
        assert roundtrip["materializer_to_binder_roundtrip_pass"] is True


class TestMaterialDifference:
    def test_distinct_from_prior_lead_lag_v0(self) -> None:
        envelope = materialize_versioned_hypothesis_binding_v0()
        prior = materialize_prior_lead_lag_v0()
        material = envelope["material_difference_from_prior"]
        assert material["prior_lead_lag_score_family"] == PRIOR_LEAD_LAG_SCORE_FAMILY
        assert material["new_score_family_policy"] == SCORE_FAMILY_POLICY
        assert material["material_difference_proven"] is True
        assert material["negative_evidence_preserved"] is True
        assert envelope["binding_digest"] != prior["binding_digest"]
        assert envelope["binding_digest"] != PRIOR_LEAD_LAG_BINDING_DIGEST
        assert envelope["binding_digest"] != prior["binding_digest"]

    def test_prior_lead_lag_binding_not_reused_unchanged(self) -> None:
        envelope = materialize_versioned_hypothesis_binding_v0()
        ok, reasons = validate_prior_lead_lag_not_reused_unchanged_v0(envelope)
        assert ok, reasons

    def test_negative_evidence_preserved(self) -> None:
        envelope = materialize_versioned_hypothesis_binding_v0()
        protection = envelope["distinctness_and_negative_evidence_protection"]
        assert protection["prior_scope_status"] == "TERMINAL_INSUFFICIENT_SAMPLE"
        assert protection["negative_evidence_preserved"] is True
        assert protection["policy_rescue"] is False
        assert protection["unchanged_retry"] is False


class TestScoreFamilyPolicy:
    def test_unknown_score_family_rejected(self) -> None:
        ok, reasons = validate_score_family_policy_v0("unknown_score_family_v99")
        assert not ok
        assert "UNKNOWN_SCORE_FAMILY" in reasons

    def test_lead_lag_v0_score_family_rejected(self) -> None:
        ok, reasons = validate_score_family_policy_v0(LEAD_LAG_V0_SCORE_FAMILY)
        assert not ok
        assert "UNKNOWN_SCORE_FAMILY" in reasons
        assert "LEAD_LAG_V0_SCORE_FAMILY_REUSED" in reasons

    def test_canonical_score_family_accepted(self) -> None:
        ok, reasons = validate_score_family_policy_v0(SCORE_FAMILY_POLICY)
        assert ok, reasons


class TestRequiredBindingFields:
    def test_futures_only_bitcoin_spot_rejected_semantics(self) -> None:
        envelope = materialize_versioned_hypothesis_binding_v0()
        pairwise = envelope["pairwise_hypothesis_contract"]
        constraints = envelope["system_constraints"]
        assert constraints["futures_only"] is True
        assert constraints["bitcoin_present"] is False
        assert pairwise["bitcoin_direction_allowed"] is False
        assert pairwise["spot_allowed"] is False
        assert pairwise["synthetic_spot_allowed"] is False

    def test_pairwise_graph_semantics_bound(self) -> None:
        envelope = materialize_versioned_hypothesis_binding_v0()
        assert envelope["score_family_policy"] == SCORE_FAMILY_POLICY
        assert envelope["research_scope"] == RESEARCH_SCOPE
        assert envelope["parameter_binding"]["pair_definition"] == PAIR_DEFINITION
        assert envelope["parameter_binding"]["graph_output"] == (
            "directed_weighted_pairwise_spillover_graph"
        )
        assert envelope["pairwise_hypothesis_contract"][
            "panel_median_benchmark_semantics_forbidden"
        ]

    def test_dataset_universe_period_digests_bound(self) -> None:
        envelope = materialize_versioned_hypothesis_binding_v0()
        assert envelope["dataset_digest"] == RATIFIED_SEMANTIC_DATA_DIGEST
        assert envelope["panel_dataset_binding"]["normalized_panel_digest"] == (
            RATIFIED_NORMALIZED_PANEL_DIGEST
        )
        assert envelope["universe_digest"] == (
            "d57738dc7e80520c17e49c406a22f8de15216c2e48e56d91b3757359ebb552a1"
        )
        assert envelope["period_binding_digest"]
        assert envelope["binding"]["digest_bindings"]["period_binding_digest"]["value"]

    def test_portfolio_implementation_fields_bound(self) -> None:
        envelope = materialize_versioned_hypothesis_binding_v0()
        pending = envelope["pending_implementation_bindings"]
        for field in (
            "aggregation_policy",
            "selection_policy",
            "holding_policy",
            "exit_policy",
            "portfolio_weighting_policy",
        ):
            assert pending[field]["status"] == BOUND_PORTFOLIO_BINDING_STATUS
            assert pending[field]["binding_digest"]
            assert pending[field]["policy"]

    def test_no_economic_evaluation(self) -> None:
        envelope = materialize_versioned_hypothesis_binding_v0()
        assert envelope["economic_evaluation_executed"] is False
        assert envelope["runtime_effect"] == "NONE"
        assert envelope["authority_effect"] == "NONE"


class TestPitContractRejections:
    def test_feature_time_gte_decision_rejected(self) -> None:
        envelope = materialize_versioned_hypothesis_binding_v0()
        rejected, reasons = validate_pairwise_contract_rejections_v0(
            envelope, mutated_field="pit.feature_time_lt_decision_time", mutated_value=False
        )
        assert rejected
        assert "FEATURE_TIME_ORDERING_VIOLATION" in reasons

    def test_target_time_lte_decision_rejected(self) -> None:
        envelope = materialize_versioned_hypothesis_binding_v0()
        rejected, reasons = validate_pairwise_contract_rejections_v0(
            envelope, mutated_field="pit.target_time_gt_decision_time", mutated_value=False
        )
        assert rejected
        assert "TARGET_TIME_ORDERING_VIOLATION" in reasons

    def test_unfinalized_bars_rejected(self) -> None:
        envelope = materialize_versioned_hypothesis_binding_v0()
        rejected, reasons = validate_pairwise_contract_rejections_v0(
            envelope, mutated_field="pit.unfinalized_bars_forbidden", mutated_value=False
        )
        assert rejected
        assert "UNFINALIZED_BARS_ALLOWED" in reasons

    def test_self_pair_forbidden(self) -> None:
        envelope = materialize_versioned_hypothesis_binding_v0()
        assert envelope["pairwise_hypothesis_contract"]["self_pair_i_equals_j_forbidden"] is True

    def test_undirected_ambiguity_forbidden(self) -> None:
        envelope = materialize_versioned_hypothesis_binding_v0()
        assert (
            envelope["pairwise_hypothesis_contract"][
                "undirected_or_unordered_pair_ambiguity_forbidden"
            ]
            is True
        )


class TestBindingDigestGuards:
    def test_lead_lag_v0_binding_digest_reuse_rejected(self) -> None:
        envelope = materialize_versioned_hypothesis_binding_v0()
        stale = deepcopy(envelope)
        stale["binding_digest"] = PRIOR_LEAD_LAG_BINDING_DIGEST
        stale["binding"]["digest_bindings"]["binding_digest"]["value"] = (
            PRIOR_LEAD_LAG_BINDING_DIGEST
        )
        verdict, reasons = validate_versioned_hypothesis_binding_v0(stale)
        assert verdict.value == "REJECTED_INCOMPLETE"
        assert "PRIOR_LEAD_LAG_BINDING_DIGEST_REUSED" in reasons

    def test_missing_dataset_binding_rejected(self) -> None:
        envelope = materialize_versioned_hypothesis_binding_v0()
        stale = deepcopy(envelope)
        stale["binding"]["digest_bindings"]["data_digest"] = {"status": "BOUND"}
        verdict, reasons = validate_versioned_hypothesis_binding_v0(stale)
        assert verdict.value == "REJECTED_INCOMPLETE"
        assert "MISSING_DATASET_BINDING" in reasons


class TestRepoArtifacts:
    def test_config_exists_when_materialized(self) -> None:
        if not CONFIG_PATH.is_file():
            pytest.skip("config not yet materialized in repo")
        payload = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        materialized = materialize_versioned_hypothesis_binding_v0()
        assert payload["binding_digest"] == materialized["binding_digest"]
        assert payload["research_scope"] == RESEARCH_SCOPE

    def test_no_runtime_imports(self) -> None:
        module_path = (
            REPO_ROOT / "src/research/"
            "cross_sectional_futures_pairwise_lead_lag_spillover_v1_versioned_hypothesis_binding_v0.py"
        )
        source = module_path.read_text(encoding="utf-8")
        for prefix in FORBIDDEN_RUNTIME_IMPORT_PREFIXES:
            assert prefix not in source

    def test_materializer_exists(self) -> None:
        assert MATERIALIZER_PATH.is_file()

    def test_governance_doc_exists_when_materialized(self) -> None:
        if not GOVERNANCE_DOC.is_file():
            pytest.skip("governance doc not yet materialized in repo")
        text = GOVERNANCE_DOC.read_text(encoding="utf-8")
        assert "pairwise_spillover_graph_v1" in text
        assert "portfolio_binding_scope" in text or "BOUND" in text
