"""Contract tests for trend_following v2 offline economic evaluation authorization."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.research.trend_following_v2_offline_economic_evaluation_authorization_ratification_v0 import (
    AUTHORIZATION_SCOPE,
    AUTHORIZATION_VERSION,
    CONFIG_REL_PATH,
    GO_TOKEN,
    GOVERNANCE_REL_PATH,
    PANEL_DATA_DIGEST,
    RESEARCH_SCOPE,
    REPLACES_FAILED_BINDING,
    RatificationMaterializationVerdict,
    RatificationValidationVerdict,
    materialize_and_validate_authorization_ratification_v0,
    materialize_offline_economic_evaluation_authorization_ratification_v0,
    materializer_to_binder_roundtrip_v0,
    validate_go_token_v0,
    validate_offline_economic_evaluation_authorization_ratification_v0,
)
from src.research.trend_following_v2_versioned_research_binding_v0 import (
    CONFIG_REL_PATH as VERSIONED_BINDING_CONFIG_REL_PATH,
    STRATEGY_ARCHETYPE,
    STRATEGY_ID,
    STRATEGY_VERSION,
    materialize_versioned_research_binding_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
GOVERNANCE_DOC = REPO_ROOT / GOVERNANCE_REL_PATH
MATERIALIZER_PATH = (
    REPO_ROOT / "scripts/research/"
    "materialize_trend_following_v2_offline_economic_evaluation_authorization_ratification_v0.py"
)
VERSIONED_BINDING_CONFIG = REPO_ROOT / VERSIONED_BINDING_CONFIG_REL_PATH
AUTHORIZATION_CONFIG = REPO_ROOT / CONFIG_REL_PATH


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


class TestScopeAndBindingIdentity:
    def test_scope_and_strategy_identity(self, complete_ratification: dict) -> None:
        assert complete_ratification["scope_id"] == RESEARCH_SCOPE
        assert complete_ratification["authorization_scope"] == AUTHORIZATION_SCOPE
        assert complete_ratification["authorization_version"] == AUTHORIZATION_VERSION
        assert complete_ratification["strategy_id"] == STRATEGY_ID
        assert complete_ratification["strategy_version"] == STRATEGY_VERSION
        assert complete_ratification["strategy_archetype"] == STRATEGY_ARCHETYPE
        assert complete_ratification["excluded_failed_binding"] == REPLACES_FAILED_BINDING

    def test_dataset_digest_bound(self, complete_ratification: dict) -> None:
        assert complete_ratification["dataset_digest"] == PANEL_DATA_DIGEST

    def test_authorization_without_execution(self, complete_ratification: dict) -> None:
        assert complete_ratification["economic_evaluation_executed"] is False
        assert (
            complete_ratification["economic_evaluation_authorized_for_separate_execution"] is True
        )
        assert complete_ratification["parameter_optimization_allowed"] is False
        assert complete_ratification["threshold_reduction_allowed"] is False
        assert complete_ratification["policy_rescue_allowed"] is False


class TestRepoSurfaceContracts:
    def test_materializer_exists(self) -> None:
        assert MATERIALIZER_PATH.is_file()

    def test_versioned_binding_config_when_present(self) -> None:
        if not VERSIONED_BINDING_CONFIG.is_file():
            pytest.skip("versioned binding config not materialized yet")
        payload = json.loads(VERSIONED_BINDING_CONFIG.read_text(encoding="utf-8"))
        assert payload["research_scope"] == RESEARCH_SCOPE
        assert payload["binding_digest"] == payload["binding"]["binding_semantic_digest"]

    def test_authorization_config_when_present(self) -> None:
        if not AUTHORIZATION_CONFIG.is_file():
            pytest.skip("authorization config not materialized yet")
        payload = json.loads(AUTHORIZATION_CONFIG.read_text(encoding="utf-8"))
        assert payload["go_token"] == GO_TOKEN
        assert payload["binding_digest"] == payload["authorization_binding_digest"]

    def test_governance_doc_when_present(self) -> None:
        if not GOVERNANCE_DOC.is_file():
            pytest.skip("governance doc not materialized yet")
        body = GOVERNANCE_DOC.read_text(encoding="utf-8")
        assert "GO_TREND_FOLLOWING_V2_OFFLINE_ECONOMIC_EVALUATION_AUTHORIZATION_V0" in body
        assert "trend_following&#47;v2" in body
        assert "Keine Offline-Economic-Evaluation" in body


class TestVersionedBindingMaterialization:
    def test_versioned_binding_complete(self) -> None:
        binding = materialize_versioned_research_binding_v0(repo_root=REPO_ROOT)
        assert binding["research_scope"] == RESEARCH_SCOPE
        assert binding["binding_ratified"] is True
        assert binding["economic_evaluation_executed"] is False
        assert binding["unchanged_retry_allowed"] is False

    def test_validation_accepts_materialized_ratification(
        self, complete_ratification: dict
    ) -> None:
        versioned_binding = materialize_versioned_research_binding_v0(repo_root=REPO_ROOT)
        verdict, reasons = validate_offline_economic_evaluation_authorization_ratification_v0(
            complete_ratification,
            go_token=GO_TOKEN,
            expected_binding=versioned_binding,
        )
        assert verdict is RatificationValidationVerdict.ACCEPTED_COMPLETE
        assert reasons == ()
