"""Contract tests for FULL_CANONICAL_SYSTEM_ECONOMIC_EVIDENCE_GENERATION_V1 ratification."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from src.research.full_canonical_system_economic_evidence_generation_v1 import (
    BINDING_CONFIG_REL_PATH,
    BINDING_ID,
    CANONICAL_CHAIN_COMPONENTS,
    EVIDENCE_CLASS_CONFIG_REL_PATH,
    EVIDENCE_CLASS_ID,
    EVIDENCE_GENERATION_ID,
    EXPECTED_SOURCE_BINDING_SEMANTIC_DIGEST,
    GO_TOKEN,
    GOVERNANCE_REL_PATH,
    NEXT_STEP,
    RATIFICATION_CONFIG_REL_PATH,
    REPLACES_FAILED_BINDING,
    RESEARCH_SCOPE,
    EvidenceClassStatus,
    MaterializationVerdict,
    ValidationVerdict,
    build_digest_dependency_graph_v0,
    build_evidence_class_contract_v0,
    build_field_classification_v0,
    materialize_and_validate_binding_ratification_v0,
    materialize_binding_ratification_v0,
    materialize_versioned_binding_v1,
    materializer_to_binder_roundtrip_v0,
    reject_partial_pipeline_binding_v0,
    reject_terminal_negative_unchanged_retry_v0,
    validate_binding_ratification_v0,
    validate_evidence_class_contract_v0,
    validate_versioned_binding_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
TERMINAL_CLOSEOUT = (
    REPO_ROOT
    / "config/research/step29m_full_canonical_offline_baseline_terminal_negative_evidence_closeout_v0.json"
)


@pytest.fixture(name="ratification")
def fixture_ratification() -> dict:
    return materialize_binding_ratification_v0(repo_root=REPO_ROOT)


class TestEvidenceClassContract:
    def test_valid_contract_accepted(self) -> None:
        contract = build_evidence_class_contract_v0()
        result = validate_evidence_class_contract_v0(contract)
        assert result.verdict == ValidationVerdict.ACCEPTED
        assert result.fail_reasons == ()
        assert contract["status"] == EvidenceClassStatus.RATIFIED_NOT_EXECUTED.value
        assert contract["evidence_class_id"] == EVIDENCE_CLASS_ID

    def test_pre_evaluation_pass_status_forbidden(self) -> None:
        contract = build_evidence_class_contract_v0()
        contract["status"] = "ECONOMICALLY_VIABLE_OFFLINE"
        result = validate_evidence_class_contract_v0(contract)
        assert result.verdict == ValidationVerdict.REJECTED
        assert "EVIDENCE_CLASS_STATUS_MUST_BE_RATIFIED_NOT_EXECUTED" in result.fail_reasons


class TestPartialAndRawSignalRejection:
    def test_partial_pipeline_rejected(self, ratification: dict) -> None:
        binding = deepcopy(ratification["versioned_binding"])
        binding["partial_pipeline"] = True
        chain = deepcopy(binding["canonical_chain_binding"])
        chain["components"] = chain["components"][:3]
        binding["canonical_chain_binding"] = chain
        result = reject_partial_pipeline_binding_v0(binding)
        assert result.verdict == ValidationVerdict.REJECTED
        assert "PARTIAL_PIPELINE_BINDING_FORBIDDEN" in result.fail_reasons
        assert "PARTIAL_PIPELINE_CHAIN_INCOMPLETE" in result.fail_reasons

    def test_raw_signal_only_rejected(self, ratification: dict) -> None:
        binding = deepcopy(ratification["versioned_binding"])
        binding["raw_signal_only"] = True
        result = reject_partial_pipeline_binding_v0(binding)
        assert result.verdict == ValidationVerdict.REJECTED
        assert "RAW_SIGNAL_ONLY_BINDING_FORBIDDEN" in result.fail_reasons


class TestTerminalNegativeRetryBlock:
    def test_terminal_negative_same_surface_rejected(self) -> None:
        registry = json.loads(TERMINAL_CLOSEOUT.read_text(encoding="utf-8"))
        result = reject_terminal_negative_unchanged_retry_v0(
            candidate_id="bollinger_bands/v1",
            binding_semantic_digest="unused",
            terminal_registry=registry,
        )
        assert result.verdict == ValidationVerdict.REJECTED
        assert "TERMINAL_NEGATIVE_BINDING_RETRY_FORBIDDEN" in result.fail_reasons

    def test_selected_v2_not_terminal_retry(self, ratification: dict) -> None:
        assert ratification["terminal_negative_binding_retry"] is False
        assert ratification["candidate_id"] == RESEARCH_SCOPE
        assert ratification["versioned_binding"]["excluded_failed_binding"] == (
            REPLACES_FAILED_BINDING
        )


class TestMaterializerBinderDeterminism:
    def test_materializer_to_binder_roundtrip_pass(self, ratification: dict) -> None:
        roundtrip = materializer_to_binder_roundtrip_v0(ratification, repo_root=REPO_ROOT)
        assert roundtrip["materializer_to_binder_roundtrip_pass"] is True
        assert roundtrip["deterministic_materialization"] is True
        assert roundtrip["second_materialization_diff_empty"] is True

    def test_second_materialization_identical(self) -> None:
        first = materialize_binding_ratification_v0(repo_root=REPO_ROOT)
        second = materialize_binding_ratification_v0(repo_root=REPO_ROOT)
        assert first == second


class TestFullCanonicalBindingInvariants:
    def test_futures_only_and_bitcoin_excluded(self, ratification: dict) -> None:
        binding = ratification["versioned_binding"]
        assert binding["futures_only"] is True
        assert binding["bitcoin_excluded"] is True
        assert binding["bitcoin_direction_allowed"] is False

    def test_realistic_costs_and_robustness_contracts_bound(self, ratification: dict) -> None:
        binding = ratification["versioned_binding"]
        assert binding["fee_model_version"]
        assert binding["slippage_model_version"]
        assert binding["funding_model_version"]
        assert binding["spread_model_version"]
        assert binding["execution_model_version"]
        for field in ("walk_forward_contract", "monte_carlo_contract", "stress_contract"):
            assert binding[field]["execution_status"] == "BOUND_NOT_EXECUTED"

    def test_full_canonical_chain_bound(self, ratification: dict) -> None:
        chain = ratification["versioned_binding"]["canonical_chain_binding"]
        assert chain["full_canonical_chain_bound"] is True
        components = {row["component"] for row in chain["components"]}
        assert components == set(CANONICAL_CHAIN_COMPONENTS)

    def test_evaluation_and_promotion_remain_false(self, ratification: dict) -> None:
        binding = ratification["versioned_binding"]
        assert binding["economic_evaluation_executed"] is False
        assert binding["economic_evaluation_authorized"] is False
        assert binding["promotion_eligible"] is False
        assert binding["runtime_rewire_admissible"] is False
        assert binding["authority_effect"] == "NONE"
        assert binding["runtime_effect"] == "NONE"
        assert ratification["economic_evaluation_executed"] is False
        assert ratification["authority_effect"] == "NONE"
        assert ratification["runtime_effect"] == "NONE"

    def test_source_digest_and_identity(self, ratification: dict) -> None:
        binding = ratification["versioned_binding"]
        assert binding["source_binding_semantic_digest"] == (
            EXPECTED_SOURCE_BINDING_SEMANTIC_DIGEST
        )
        assert binding["binding_id"] == BINDING_ID
        assert binding["evidence_generation_id"] == EVIDENCE_GENERATION_ID
        assert binding["evidence_class_id"] == EVIDENCE_CLASS_ID
        assert ratification["go_token"] == GO_TOKEN
        assert ratification["next_step"] == NEXT_STEP


class TestDigestGraphAndRepoSurfaces:
    def test_digest_dependency_graph_complete(self, ratification: dict) -> None:
        graph = build_digest_dependency_graph_v0(ratification["versioned_binding"])
        assert graph["transitive_digest_chain_complete"] is True
        classification = build_field_classification_v0(ratification["versioned_binding"])
        assert classification["unexpected_change_count"] == 0
        assert classification["unclassified_changed_field_count"] == 0

    def test_repo_configs_match_materializer(self, ratification: dict) -> None:
        for rel in (
            EVIDENCE_CLASS_CONFIG_REL_PATH,
            BINDING_CONFIG_REL_PATH,
            RATIFICATION_CONFIG_REL_PATH,
            GOVERNANCE_REL_PATH,
        ):
            assert (REPO_ROOT / rel).is_file(), rel
        on_disk = json.loads((REPO_ROOT / RATIFICATION_CONFIG_REL_PATH).read_text(encoding="utf-8"))
        assert on_disk["binding_digest"] == ratification["binding_digest"]
        assert on_disk["ratification_digest"] == ratification["ratification_digest"]
        assert on_disk["evidence_class_id"] == EVIDENCE_CLASS_ID

    def test_materialize_and_validate_complete(self) -> None:
        result = materialize_and_validate_binding_ratification_v0(repo_root=REPO_ROOT)
        assert result.verdict == MaterializationVerdict.COMPLETE
        assert result.validation_verdict == ValidationVerdict.ACCEPTED
        assert result.fail_reasons == ()

    def test_binding_validator_rejects_missing_chain(self) -> None:
        binding = materialize_versioned_binding_v1(repo_root=REPO_ROOT)
        binding = deepcopy(binding)
        binding["canonical_chain_binding"] = {"full_canonical_chain_bound": False}
        result = validate_versioned_binding_v1(binding)
        assert result.verdict == ValidationVerdict.REJECTED
        assert "FULL_CANONICAL_CHAIN_NOT_BOUND" in result.fail_reasons

    def test_ratification_validator_roundtrip(self, ratification: dict) -> None:
        result = validate_binding_ratification_v0(ratification)
        assert result.verdict == ValidationVerdict.ACCEPTED
