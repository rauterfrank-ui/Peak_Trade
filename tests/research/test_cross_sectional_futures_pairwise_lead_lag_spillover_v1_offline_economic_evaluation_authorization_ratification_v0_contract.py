"""Contract tests for pairwise spillover v1 offline economic evaluation authorization."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_evaluation_authorization_ratification_v0 import (
    AUTHORIZATION_SCOPE,
    AUTHORIZATION_VERSION,
    CONFIG_REL_PATH,
    GO_TOKEN,
    GOVERNANCE_REL_PATH,
    RATIFIED_HYPOTHESIS_BINDING_DIGEST,
    RESEARCH_SCOPE,
    RatificationMaterializationVerdict,
    RatificationValidationVerdict,
    compute_ranking_contract_digest_v0,
    compute_score_contract_digest_v0,
    materialize_and_validate_authorization_ratification_v0,
    materialize_offline_economic_evaluation_authorization_ratification_v0,
    materializer_to_binder_roundtrip_v0,
    validate_go_token_v0,
    validate_offline_economic_evaluation_authorization_ratification_v0,
    validate_ratification_rejections_v0,
)
from src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_score_and_ranking_contract_v0 import (
    materialize_score_and_ranking_contract_v0,
)
from src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_versioned_hypothesis_binding_v0 import (
    materialize_versioned_hypothesis_binding_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
GOVERNANCE_DOC = REPO_ROOT / GOVERNANCE_REL_PATH
MATERIALIZER_PATH = (
    REPO_ROOT / "scripts/research/"
    "materialize_cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_"
    "evaluation_authorization_ratification_v0.py"
)
FORBIDDEN_RUNTIME_IMPORT_PREFIXES = (
    "src.execution",
    "src.scheduler",
    "src.broker",
)


@pytest.fixture(name="complete_ratification")
def fixture_complete_ratification() -> dict:
    return materialize_offline_economic_evaluation_authorization_ratification_v0()


class TestAuthorizationRatificationMaterialization:
    def test_materialization_complete(self) -> None:
        result = materialize_and_validate_authorization_ratification_v0(go_token=GO_TOKEN)
        assert result.verdict == RatificationMaterializationVerdict.COMPLETE
        assert result.validation_verdict == RatificationValidationVerdict.ACCEPTED_COMPLETE
        assert result.fail_reasons == ()

    def test_deterministic_double_materialization(self) -> None:
        first = materialize_offline_economic_evaluation_authorization_ratification_v0()
        second = materialize_offline_economic_evaluation_authorization_ratification_v0()
        assert first == second

    def test_materializer_to_binder_roundtrip_pass(self, complete_ratification: dict) -> None:
        roundtrip = materializer_to_binder_roundtrip_v0(complete_ratification)
        assert roundtrip["materializer_to_binder_roundtrip_pass"] is True


class TestGoTokenEnforcement:
    def test_correct_go_token_accepted(self) -> None:
        ok, reasons = validate_go_token_v0(GO_TOKEN)
        assert ok, reasons

    def test_missing_go_token_rejected(self) -> None:
        ok, reasons = validate_go_token_v0(None)
        assert not ok
        assert "GO_TOKEN_MISSING" in reasons

    def test_wrong_go_token_rejected(self) -> None:
        ok, reasons = validate_go_token_v0("GO_WRONG_TOKEN")
        assert not ok
        assert "GO_TOKEN_INVALID" in reasons

    def test_validation_requires_go_token(self, complete_ratification: dict) -> None:
        verdict, reasons = validate_offline_economic_evaluation_authorization_ratification_v0(
            complete_ratification, go_token="GO_WRONG_TOKEN"
        )
        assert verdict is RatificationValidationVerdict.REJECTED_INCOMPLETE
        assert "GO_TOKEN_INVALID" in reasons


class TestScopeAndVersionBinding:
    def test_scope_id_and_version_bound(self, complete_ratification: dict) -> None:
        assert complete_ratification["scope_id"] == RESEARCH_SCOPE
        assert complete_ratification["authorization_scope"] == AUTHORIZATION_SCOPE
        assert complete_ratification["authorization_version"] == AUTHORIZATION_VERSION

    def test_scope_id_mismatch_rejected(self, complete_ratification: dict) -> None:
        rejected, reasons = validate_ratification_rejections_v0(
            complete_ratification,
            mutated_field="scope_id",
            mutated_value="wrong/scope",
        )
        assert rejected
        assert "SCOPE_ID_MISMATCH" in reasons


class TestCanonicalReferenceRequirements:
    def test_hypothesis_binding_reference_required(self, complete_ratification: dict) -> None:
        refs = complete_ratification["canonical_references"]["hypothesis_binding"]
        assert refs["binding_digest"] == RATIFIED_HYPOTHESIS_BINDING_DIGEST
        assert refs["mutated"] is False

    def test_score_contract_reference_required(self, complete_ratification: dict) -> None:
        refs = complete_ratification["canonical_references"]["score_and_ranking_contract"]
        assert refs["score_contract_digest"] == compute_score_contract_digest_v0()
        assert refs["mutated"] is False

    def test_ranking_contract_reference_required(self, complete_ratification: dict) -> None:
        refs = complete_ratification["canonical_references"]["score_and_ranking_contract"]
        assert refs["ranking_contract_digest"] == compute_ranking_contract_digest_v0()

    def test_missing_hypothesis_reference_rejected(self, complete_ratification: dict) -> None:
        rejected, reasons = validate_ratification_rejections_v0(
            complete_ratification,
            mutated_field="canonical.hypothesis_binding",
            mutated_value=None,
        )
        assert rejected
        assert "HYPOTHESIS_BINDING_REFERENCE_MISSING" in reasons


class TestDigestIdentityProtection:
    def test_dataset_and_universe_digests_match(self, complete_ratification: dict) -> None:
        binding = materialize_versioned_hypothesis_binding_v0()
        assert complete_ratification["dataset_digest"] == binding["dataset_digest"]
        assert complete_ratification["universe_digest"] == binding["universe_digest"]

    def test_hypothesis_score_ranking_digests_unchanged(self, complete_ratification: dict) -> None:
        binding = materialize_versioned_hypothesis_binding_v0()
        contract = materialize_score_and_ranking_contract_v0(binding)
        assert complete_ratification["hypothesis_binding_digest"] == binding["binding_digest"]
        assert (
            complete_ratification["score_and_ranking_contract_digest"]
            == contract["contract_digest"]
        )

    def test_stale_hypothesis_digest_rejected(self, complete_ratification: dict) -> None:
        rejected, reasons = validate_ratification_rejections_v0(
            complete_ratification,
            mutated_field="hypothesis_binding_digest",
            mutated_value="0" * 64,
        )
        assert rejected
        assert "HYPOTHESIS_BINDING_DIGEST_MISMATCH" in reasons

    def test_stale_dataset_digest_rejected(self, complete_ratification: dict) -> None:
        rejected, reasons = validate_ratification_rejections_v0(
            complete_ratification,
            mutated_field="dataset_digest",
            mutated_value="0" * 64,
        )
        assert rejected
        assert "DATASET_DIGEST_MISMATCH" in reasons


class TestBoundaryConstraints:
    def test_futures_only_and_bitcoin_excluded(self, complete_ratification: dict) -> None:
        assert complete_ratification["futures_only"] is True
        assert complete_ratification["bitcoin_direction_allowed"] is False
        refs = complete_ratification["canonical_references"]["hypothesis_binding"]
        assert refs["futures_only"] is True
        assert refs["bitcoin_excluded"] is True

    def test_economic_evaluation_not_executed(self, complete_ratification: dict) -> None:
        assert complete_ratification["economic_evaluation_executed"] is False
        assert (
            complete_ratification["economic_evaluation_authorized_for_separate_execution"] is True
        )

    def test_parameter_optimization_forbidden(self, complete_ratification: dict) -> None:
        assert complete_ratification["parameter_optimization_allowed"] is False

    def test_threshold_reduction_forbidden(self, complete_ratification: dict) -> None:
        assert complete_ratification["threshold_reduction_allowed"] is False

    def test_policy_rescue_forbidden(self, complete_ratification: dict) -> None:
        assert complete_ratification["policy_rescue_allowed"] is False

    def test_runtime_authority_order_effects_none(self, complete_ratification: dict) -> None:
        assert complete_ratification["runtime_effect"] == "NONE"
        assert complete_ratification["authority_effect"] == "NONE"
        assert complete_ratification["order_effect"] == "NONE"
        assert complete_ratification["live_authorized"] is False
        assert complete_ratification["orders_allowed"] is False

    def test_parameter_optimization_violation_rejected(self, complete_ratification: dict) -> None:
        rejected, reasons = validate_ratification_rejections_v0(
            complete_ratification,
            mutated_field="parameter_optimization_allowed",
            mutated_value=True,
        )
        assert rejected
        assert "PARAMETER_OPTIMIZATION_ALLOWED_VIOLATION" in reasons


class TestGovernanceArtifacts:
    def test_governance_doc_exists(self) -> None:
        assert GOVERNANCE_DOC.is_file()

    def test_config_path_bound(self) -> None:
        assert (REPO_ROOT / CONFIG_REL_PATH).is_file()

    def test_materializer_exists(self) -> None:
        assert MATERIALIZER_PATH.is_file()

    def test_no_forbidden_runtime_imports(self) -> None:
        source = (REPO_ROOT / CONFIG_REL_PATH).read_text(encoding="utf-8")
        for prefix in FORBIDDEN_RUNTIME_IMPORT_PREFIXES:
            assert prefix not in source

    def test_existing_hypothesis_and_score_contract_tests_remain_importable(self) -> None:
        from tests.research import (  # noqa: F401
            test_cross_sectional_futures_pairwise_lead_lag_spillover_v1_score_and_ranking_contract_v0_contract,
            test_cross_sectional_futures_pairwise_lead_lag_spillover_v1_versioned_hypothesis_binding_v0_contract,
        )

        assert (
            test_cross_sectional_futures_pairwise_lead_lag_spillover_v1_versioned_hypothesis_binding_v0_contract
            is not None
        )
        assert (
            test_cross_sectional_futures_pairwise_lead_lag_spillover_v1_score_and_ranking_contract_v0_contract
            is not None
        )
