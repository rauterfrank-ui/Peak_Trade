"""Contract tests for momentum_1h v2 offline economic evaluation authorization."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from src.research.momentum_1h_v2_offline_economic_evaluation_authorization_ratification_v0 import (
    AUTHORIZATION_SCOPE,
    AUTHORIZATION_STATUS,
    AUTHORIZATION_VERSION,
    BINDING_GENERATION,
    CANDIDATE_SPECIFIC_AUTHORIZATION,
    CONFIG_REL_PATH,
    ECONOMIC_RESULT,
    EXPECTED_BINDING_DIGEST,
    GLOBAL_HOLD_RELAXED,
    GO_TOKEN,
    GOVERNANCE_REL_PATH,
    NEXT_OPERATOR_GO,
    NO_NEW_CANDIDATE_HOLD_AFTER,
    NO_NEW_CANDIDATE_HOLD_BEFORE,
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
from src.research.momentum_1h_v2_versioned_research_binding_v0 import (
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
    "materialize_momentum_1h_v2_offline_economic_evaluation_authorization_ratification_v0.py"
)
VERSIONED_BINDING_CONFIG = REPO_ROOT / VERSIONED_BINDING_CONFIG_REL_PATH
AUTHORIZATION_CONFIG = REPO_ROOT / CONFIG_REL_PATH


@pytest.fixture(name="complete_ratification")
def fixture_complete_ratification() -> dict:
    return materialize_offline_economic_evaluation_authorization_ratification_v0()


@pytest.fixture(name="versioned_binding")
def fixture_versioned_binding() -> dict:
    return materialize_versioned_research_binding_v0(repo_root=REPO_ROOT)


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
        assert complete_ratification["authorization_status"] == AUTHORIZATION_STATUS
        assert complete_ratification["strategy_id"] == STRATEGY_ID
        assert complete_ratification["strategy_version"] == STRATEGY_VERSION
        assert complete_ratification["strategy_archetype"] == STRATEGY_ARCHETYPE
        assert complete_ratification["excluded_failed_binding"] == REPLACES_FAILED_BINDING
        assert complete_ratification["binding_generation"] == BINDING_GENERATION
        assert complete_ratification["binding_digest"] == EXPECTED_BINDING_DIGEST

    def test_dataset_digest_bound(self, complete_ratification: dict) -> None:
        assert complete_ratification["dataset_digest"] == PANEL_DATA_DIGEST

    def test_authorization_without_execution(self, complete_ratification: dict) -> None:
        assert complete_ratification["economic_evaluation_executed"] is False
        assert complete_ratification["economic_result"] == ECONOMIC_RESULT
        assert (
            complete_ratification["economic_evaluation_authorized_for_separate_execution"] is True
        )
        assert complete_ratification["parameter_optimization_allowed"] is False
        assert complete_ratification["threshold_reduction_allowed"] is False
        assert complete_ratification["policy_rescue_allowed"] is False
        assert complete_ratification["orders_allowed"] is False
        assert complete_ratification["live_authorized"] is False

    def test_hold_semantics_preserved(self, complete_ratification: dict) -> None:
        assert complete_ratification["no_new_candidate_hold_before"] == NO_NEW_CANDIDATE_HOLD_BEFORE
        assert complete_ratification["no_new_candidate_hold_after"] == NO_NEW_CANDIDATE_HOLD_AFTER
        assert complete_ratification["global_hold_relaxed"] is GLOBAL_HOLD_RELAXED
        assert complete_ratification["candidate_specific_authorization"] is (
            CANDIDATE_SPECIFIC_AUTHORIZATION
        )
        assert complete_ratification["trend_following_v2_retry_admissible"] is False


class TestRepoSurfaceContracts:
    def test_materializer_exists(self) -> None:
        assert MATERIALIZER_PATH.is_file()

    def test_versioned_binding_config_when_present(self) -> None:
        if not VERSIONED_BINDING_CONFIG.is_file():
            pytest.skip("versioned binding config not materialized yet")
        payload = json.loads(VERSIONED_BINDING_CONFIG.read_text(encoding="utf-8"))
        assert payload["research_scope"] == RESEARCH_SCOPE
        assert payload["binding_digest"] == payload["binding"]["binding_semantic_digest"]
        assert payload["binding_digest"] == EXPECTED_BINDING_DIGEST

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
        assert GO_TOKEN in body
        assert "momentum_1h&#47;v2" in body
        assert "Keine Offline-Economic-Evaluation" in body
        assert "NO_NEW_CANDIDATE_HOLD_AFTER" in body


class TestVersionedBindingMaterialization:
    def test_versioned_binding_complete(self) -> None:
        binding = materialize_versioned_research_binding_v0(repo_root=REPO_ROOT)
        assert binding["research_scope"] == RESEARCH_SCOPE
        assert binding["binding_ratified"] is True
        assert binding["economic_evaluation_executed"] is False
        assert binding["unchanged_retry_allowed"] is False
        assert binding["binding_digest"] == EXPECTED_BINDING_DIGEST

    def test_validation_accepts_materialized_ratification(
        self,
        complete_ratification: dict,
        versioned_binding: dict,
    ) -> None:
        verdict, reasons = validate_offline_economic_evaluation_authorization_ratification_v0(
            complete_ratification,
            go_token=GO_TOKEN,
            expected_binding=versioned_binding,
        )
        assert verdict is RatificationValidationVerdict.ACCEPTED_COMPLETE
        assert reasons == ()


class TestNegativeFailClosedMatrix:
    def _validate_mutated(
        self,
        ratification: dict,
        *,
        versioned_binding: dict,
        expected_reason: str,
    ) -> None:
        verdict, reasons = validate_offline_economic_evaluation_authorization_ratification_v0(
            ratification,
            go_token=GO_TOKEN,
            expected_binding=versioned_binding,
        )
        assert verdict is RatificationValidationVerdict.REJECTED_INCOMPLETE
        assert expected_reason in reasons

    def test_exact_candidate_accepted(
        self,
        complete_ratification: dict,
        versioned_binding: dict,
    ) -> None:
        verdict, reasons = validate_offline_economic_evaluation_authorization_ratification_v0(
            complete_ratification,
            go_token=GO_TOKEN,
            expected_binding=versioned_binding,
        )
        assert verdict is RatificationValidationVerdict.ACCEPTED_COMPLETE
        assert reasons == ()

    def test_missing_strategy_version_blocked(
        self,
        complete_ratification: dict,
        versioned_binding: dict,
    ) -> None:
        mutated = deepcopy(complete_ratification)
        mutated["strategy_version"] = ""
        self._validate_mutated(
            mutated,
            versioned_binding=versioned_binding,
            expected_reason="STRATEGY_VERSION_MISSING",
        )

    def test_wrong_strategy_version_blocked(
        self,
        complete_ratification: dict,
        versioned_binding: dict,
    ) -> None:
        mutated = deepcopy(complete_ratification)
        mutated["strategy_version"] = "v1"
        self._validate_mutated(
            mutated,
            versioned_binding=versioned_binding,
            expected_reason="STRATEGY_VERSION_MISMATCH",
        )

    def test_wrong_binding_generation_blocked(
        self,
        complete_ratification: dict,
        versioned_binding: dict,
    ) -> None:
        mutated = deepcopy(complete_ratification)
        mutated["binding_generation"] = "pre_pr4921"
        self._validate_mutated(
            mutated,
            versioned_binding=versioned_binding,
            expected_reason="BINDING_GENERATION_MISMATCH",
        )

    def test_invalid_binding_digest_blocked(
        self,
        complete_ratification: dict,
        versioned_binding: dict,
    ) -> None:
        mutated = deepcopy(complete_ratification)
        mutated["binding_digest"] = "0" * 64
        self._validate_mutated(
            mutated,
            versioned_binding=versioned_binding,
            expected_reason="BINDING_DIGEST_INVALID",
        )

    def test_missing_discovery_source_blocked(
        self,
        complete_ratification: dict,
        versioned_binding: dict,
    ) -> None:
        mutated = deepcopy(complete_ratification)
        refs = deepcopy(mutated["canonical_references"])
        refs["source_evidence"]["discovery_evidence_dir"] = ""
        mutated["canonical_references"] = refs
        self._validate_mutated(
            mutated,
            versioned_binding=versioned_binding,
            expected_reason="SOURCE_EVIDENCE_DISCOVERY_EVIDENCE_DIR_MISSING",
        )

    def test_runtime_scope_blocked(
        self,
        complete_ratification: dict,
        versioned_binding: dict,
    ) -> None:
        mutated = deepcopy(complete_ratification)
        mutated["authorization_scope"] = "OFFLINE_ECONOMIC_EVALUATION_AND_RUNTIME"
        self._validate_mutated(
            mutated,
            versioned_binding=versioned_binding,
            expected_reason="AUTHORIZATION_SCOPE_RUNTIME_FORBIDDEN",
        )

    def test_evaluation_executed_claim_blocked(
        self,
        complete_ratification: dict,
        versioned_binding: dict,
    ) -> None:
        mutated = deepcopy(complete_ratification)
        mutated["economic_evaluation_executed"] = True
        self._validate_mutated(
            mutated,
            versioned_binding=versioned_binding,
            expected_reason="ECONOMIC_EVALUATION_EXECUTED_MUST_BE_FALSE",
        )

    def test_economic_pass_claim_blocked(
        self,
        complete_ratification: dict,
        versioned_binding: dict,
    ) -> None:
        mutated = deepcopy(complete_ratification)
        mutated["economic_result"] = "PASS"
        self._validate_mutated(
            mutated,
            versioned_binding=versioned_binding,
            expected_reason="ECONOMIC_RESULT_MUST_BE_NOT_EVALUATED",
        )

    def test_orders_allowed_blocked(
        self,
        complete_ratification: dict,
        versioned_binding: dict,
    ) -> None:
        mutated = deepcopy(complete_ratification)
        mutated["orders_allowed"] = True
        self._validate_mutated(
            mutated,
            versioned_binding=versioned_binding,
            expected_reason="ORDERS_ALLOWED_FORBIDDEN",
        )

    def test_live_authorized_blocked(
        self,
        complete_ratification: dict,
        versioned_binding: dict,
    ) -> None:
        mutated = deepcopy(complete_ratification)
        mutated["live_authorized"] = True
        self._validate_mutated(
            mutated,
            versioned_binding=versioned_binding,
            expected_reason="LIVE_AUTHORIZED_FORBIDDEN",
        )

    def test_global_hold_relaxed_blocked(
        self,
        complete_ratification: dict,
        versioned_binding: dict,
    ) -> None:
        mutated = deepcopy(complete_ratification)
        mutated["global_hold_relaxed"] = True
        mutated["no_new_candidate_hold_after"] = "REVOKED"
        self._validate_mutated(
            mutated,
            versioned_binding=versioned_binding,
            expected_reason="NO_NEW_CANDIDATE_HOLD_RELAXED",
        )

    def test_trend_following_v2_retry_blocked(
        self,
        complete_ratification: dict,
        versioned_binding: dict,
    ) -> None:
        mutated = deepcopy(complete_ratification)
        mutated["trend_following_v2_retry_admissible"] = True
        self._validate_mutated(
            mutated,
            versioned_binding=versioned_binding,
            expected_reason="TREND_FOLLOWING_V2_RETRY_ADMISSIBLE_FORBIDDEN",
        )

    def test_execution_without_separate_go_blocked(
        self,
        complete_ratification: dict,
        versioned_binding: dict,
    ) -> None:
        mutated = deepcopy(complete_ratification)
        refs = deepcopy(mutated["canonical_references"])
        refs["offline_evaluation_entry_point"]["execution_authorized_in_this_scope"] = True
        mutated["canonical_references"] = refs
        self._validate_mutated(
            mutated,
            versioned_binding=versioned_binding,
            expected_reason="EXECUTION_AUTHORIZED_IN_THIS_SCOPE_FORBIDDEN",
        )

    def test_separate_execution_go_required(
        self,
        complete_ratification: dict,
    ) -> None:
        entry = complete_ratification["canonical_references"]["offline_evaluation_entry_point"]
        assert entry["status"] == "PENDING_SEPARATE_EXECUTION_SCOPE"
        assert entry["execution_authorized_in_this_scope"] is False
        assert complete_ratification["next_operator_go"] == NEXT_OPERATOR_GO
