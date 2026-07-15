"""Contract tests for lead-lag v0 terminal insufficient sample and pairwise spillover v1 scope ratification v0."""

from __future__ import annotations

import json
from pathlib import Path

from src.research.cross_sectional_futures_lead_lag_information_diffusion_v0_terminal_insufficient_sample_and_distinct_futures_research_scope_ratification_v0 import (
    BASELINE_VERDICT,
    BINDING_DIGEST,
    CANONICAL_EVALUATION_DIR,
    CANONICAL_EVALUATION_TIMESTAMP,
    GOVERNANCE_REL_PATH,
    IMPLEMENTATION_DIGEST,
    OPERATOR_DECISION,
    OPERATOR_GO_TOKEN,
    PAIRWISE_SCOPE_RATIFICATION_CONFIG_REL_PATH,
    PRIMARY_CAUSE_CLASS,
    REGISTRATION_ID,
    RESEARCH_SCOPE,
    SECONDARY_CAUSE_CLASS,
    SELECTED_DISTINCT_HYPOTHESIS_FAMILY,
    SELECTED_DISTINCT_MATERIAL_DIFFERENCE_PRIMARY,
    SELECTED_DISTINCT_SCOPE,
    SELECTED_DISTINCT_SCORE_FAMILY_POLICY,
    TERMINAL_FAILURE_CLASS,
    TERMINAL_STATUS,
    TERMINAL_VERDICT,
    TRADE_COUNT,
    apply_versioned_binding_registration_fields,
    compute_registration_digest,
    is_exact_binding_retry_blocked,
    is_materially_distinct_scope_admissible,
    materialize_registration_config,
    validate_registration_preconditions,
)
from src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_research_scope_ratification_v0 import (
    HYPOTHESIS_FAMILY,
    SCORE_FAMILY_POLICY,
    ValidationVerdictEnum as PairwiseValidationVerdict,
    materialize_pairwise_spillover_research_scope_ratification_v0,
    validate_pairwise_spillover_research_scope_ratification_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRATION_CONFIG = (
    REPO_ROOT / "config/research/"
    "cross_sectional_futures_lead_lag_information_diffusion_v0_terminal_insufficient_sample_and_"
    "distinct_futures_research_scope_ratification_v0.json"
)
PAIRWISE_SCOPE_CONFIG = REPO_ROOT / PAIRWISE_SCOPE_RATIFICATION_CONFIG_REL_PATH
GOVERNANCE_DOC = REPO_ROOT / GOVERNANCE_REL_PATH
LEAD_LAG_BINDING_PATH = (
    REPO_ROOT
    / "config/research/cross_sectional_futures_lead_lag_information_diffusion_v0_versioned_hypothesis_binding_v0.json"
)
FORBIDDEN_RUNTIME_IMPORT_PREFIXES = (
    "src.execution",
    "src.scheduler",
    "src.broker",
)


class TestTerminalInsufficientSampleRegistrationModule:
    def test_preconditions_and_deterministic_registration_digest(self) -> None:
        canonical = validate_registration_preconditions()
        first = materialize_registration_config(canonical=canonical)
        second = materialize_registration_config(canonical=canonical)
        assert first == second
        assert first["registration_digest"] == compute_registration_digest(first)
        assert first["operator_decision"] == OPERATOR_DECISION

    def test_no_runtime_or_scheduler_imports(self) -> None:
        module_path = (
            REPO_ROOT / "src/research/"
            "cross_sectional_futures_lead_lag_information_diffusion_v0_terminal_insufficient_sample_and_"
            "distinct_futures_research_scope_ratification_v0.py"
        )
        source = module_path.read_text(encoding="utf-8")
        for prefix in FORBIDDEN_RUNTIME_IMPORT_PREFIXES:
            assert prefix not in source


class TestExactBindingRetryGuard:
    def test_exact_binding_retry_rejected(self) -> None:
        assert is_exact_binding_retry_blocked(
            research_scope=RESEARCH_SCOPE,
            binding_digest=BINDING_DIGEST,
            implementation_digest=IMPLEMENTATION_DIGEST,
        )

    def test_distinct_scope_admissible(self) -> None:
        assert is_materially_distinct_scope_admissible(SELECTED_DISTINCT_SCOPE)
        assert not is_materially_distinct_scope_admissible(RESEARCH_SCOPE)


class TestTerminalInsufficientSampleRegistrationConfig:
    def test_config_exists_and_required_fields(self) -> None:
        assert REGISTRATION_CONFIG.is_file()
        payload = json.loads(REGISTRATION_CONFIG.read_text(encoding="utf-8"))
        assert payload["artifact_kind"] == REGISTRATION_ID
        assert payload["go_token"] == OPERATOR_GO_TOKEN
        assert payload["operator_decision"] == OPERATOR_DECISION
        assert payload["research_scope"] == RESEARCH_SCOPE
        assert payload["binding_digest"] == BINDING_DIGEST
        assert payload["implementation_digest"] == IMPLEMENTATION_DIGEST
        assert payload["terminal_status"] == TERMINAL_STATUS
        assert payload["terminal_failure_class"] == TERMINAL_FAILURE_CLASS
        assert payload["terminal_verdict"] == TERMINAL_VERDICT
        assert payload["baseline_verdict"] == BASELINE_VERDICT
        assert payload["primary_cause_class"] == PRIMARY_CAUSE_CLASS
        assert payload["secondary_cause_class"] == SECONDARY_CAUSE_CLASS
        assert payload["unchanged_retry_blocked"] is True
        assert payload["policy_rescue_allowed"] is False
        assert payload["negative_evidence_preserved"] is True
        assert payload["selected_distinct_scope"] == SELECTED_DISTINCT_SCOPE
        assert payload["material_difference_proven"] is True
        assert payload["distinct_scope_ratified"] is True
        assert payload["trade_count"] == TRADE_COUNT
        assert payload["economic_evaluation_executed"] is True
        assert str(CANONICAL_EVALUATION_DIR) in payload["canonical_evaluation_bundle"]
        assert payload["registration_digest"] == compute_registration_digest(payload)

    def test_no_economic_evaluation_authority_in_this_slice(self) -> None:
        payload = json.loads(REGISTRATION_CONFIG.read_text(encoding="utf-8"))
        assert payload["authority_effect"] == "NONE"
        assert payload["runtime_effect"] == "NONE"
        assert payload["no_economic_reevaluation"] is True
        assert payload["no_parameter_change"] is True
        assert payload["no_policy_rescue"] is True


class TestPairwiseSpilloverScopeRatificationConfig:
    def test_pairwise_scope_ratification_config(self) -> None:
        assert PAIRWISE_SCOPE_CONFIG.is_file()
        payload = json.loads(PAIRWISE_SCOPE_CONFIG.read_text(encoding="utf-8"))
        ratification = materialize_pairwise_spillover_research_scope_ratification_v0(
            repo_root=REPO_ROOT
        )
        validation = validate_pairwise_spillover_research_scope_ratification_v0(payload)
        assert validation.verdict == PairwiseValidationVerdict.ACCEPTED
        assert payload["research_scope_definition_ratified"] is True
        assert payload["binding_ratified"] is False
        assert payload["economic_evaluation_executed"] is False
        assert payload["economic_evaluation_authorized"] is False
        assert payload["implementation_authorized"] is False
        assert payload["new_binding_required"] is True
        assert payload["existing_binding_reused"] is False
        assert payload["research_only"] is True
        assert payload["futures_only"] is True
        assert payload["bitcoin_direction_allowed"] is False
        assert payload["hypothesis_family"] == HYPOTHESIS_FAMILY
        assert payload["score_family_policy"] == SCORE_FAMILY_POLICY
        assert (
            payload["material_difference_primary"] == SELECTED_DISTINCT_MATERIAL_DIFFERENCE_PRIMARY
        )
        assert payload["ratification_digest"] == ratification["ratification_digest"]


class TestLeadLagVersionedBindingTerminalFields:
    def test_binding_terminal_insufficient_sample(self) -> None:
        binding = json.loads(LEAD_LAG_BINDING_PATH.read_text(encoding="utf-8"))
        registration = json.loads(REGISTRATION_CONFIG.read_text(encoding="utf-8"))
        assert binding["economic_evaluation_executed"] is True
        assert binding["unchanged_retry_blocked"] is True
        assert binding["terminal_status"] == TERMINAL_STATUS
        assert binding["terminal_verdict"] == TERMINAL_VERDICT
        assert binding["trade_count"] == TRADE_COUNT
        assert binding["primary_failure_class"] == PRIMARY_CAUSE_CLASS
        assert binding["secondary_failure_class"] == SECONDARY_CAUSE_CLASS
        assert binding["negative_evidence_preserved"] is True
        assert binding["policy_rescue_allowed"] is False
        assert binding["canonical_evaluation_timestamp"] == CANONICAL_EVALUATION_TIMESTAMP
        assert binding["selected_distinct_scope"] == SELECTED_DISTINCT_SCOPE
        assert binding["binding_digest_at_terminal_registration"] == BINDING_DIGEST
        assert (
            apply_versioned_binding_registration_fields(binding, registration)["baseline_verdict"]
            == BASELINE_VERDICT
        )


class TestDistinctScopeIdentity:
    def test_new_scope_identity_fields(self) -> None:
        registration = json.loads(REGISTRATION_CONFIG.read_text(encoding="utf-8"))
        assert (
            registration["selected_distinct_hypothesis_family"]
            == SELECTED_DISTINCT_HYPOTHESIS_FAMILY
        )
        assert (
            registration["selected_distinct_score_family_policy"]
            == SELECTED_DISTINCT_SCORE_FAMILY_POLICY
        )
        assert registration["new_binding_required"] is True
        assert registration["existing_binding_reused"] is False
        assert registration["new_hypothesis_id"] is True


class TestGovernanceDoc:
    def test_governance_doc_present(self) -> None:
        assert GOVERNANCE_DOC.is_file()
        body = GOVERNANCE_DOC.read_text(encoding="utf-8")
        assert OPERATOR_GO_TOKEN in body
        assert (
            SELECTED_DISTINCT_SCOPE.replace("/", "&#47;") in body or SELECTED_DISTINCT_SCOPE in body
        )
