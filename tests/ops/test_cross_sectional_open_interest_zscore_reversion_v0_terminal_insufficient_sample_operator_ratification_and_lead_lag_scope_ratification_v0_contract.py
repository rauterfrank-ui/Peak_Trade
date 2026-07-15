"""Contract tests for OI zscore terminal insufficient sample operator ratification and lead-lag scope ratification v0."""

from __future__ import annotations

import json
from pathlib import Path

from src.research.cross_sectional_futures_lead_lag_information_diffusion_v0_offline_economic_evaluation_scope_ratification_v0 import (
    CONFIG_REL_PATH as LEAD_LAG_SCOPE_CONFIG_REL_PATH,
    RUNNER_BINDING_REF,
    ValidationVerdictEnum as LeadLagValidationVerdict,
    materialize_lead_lag_offline_economic_evaluation_scope_ratification_v0,
    validate_lead_lag_offline_economic_evaluation_scope_ratification_v0,
)
from src.research.cross_sectional_open_interest_zscore_reversion_v0_terminal_insufficient_sample_and_distinct_futures_research_scope_ratification_v0 import (
    BASELINE_VERDICT,
    BINDING_DIGEST,
    CANONICAL_EVALUATION_DIR,
    CANONICAL_EVALUATION_TIMESTAMP,
    GOVERNANCE_REL_PATH,
    IMPLEMENTATION_DIGEST,
    OPERATOR_DECISION,
    OPERATOR_GO_TOKEN,
    REGISTRATION_ID,
    RESEARCH_SCOPE,
    SELECTED_DISTINCT_SCOPE,
    TERMINAL_FAILURE_CLASS,
    TERMINAL_STATUS,
    TRADE_COUNT,
    apply_versioned_binding_registration_fields,
    compute_registration_digest,
    is_exact_binding_retry_blocked,
    is_materially_distinct_scope_admissible,
    materialize_registration_config,
    validate_registration_preconditions,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRATION_CONFIG = (
    REPO_ROOT / "config/research/"
    "cross_sectional_open_interest_zscore_reversion_v0_terminal_insufficient_sample_and_"
    "distinct_futures_research_scope_ratification_v0.json"
)
LEAD_LAG_SCOPE_CONFIG = REPO_ROOT / LEAD_LAG_SCOPE_CONFIG_REL_PATH
GOVERNANCE_DOC = REPO_ROOT / GOVERNANCE_REL_PATH
OI_BINDING_PATH = (
    REPO_ROOT
    / "config/research/cross_sectional_open_interest_zscore_reversion_v0_versioned_hypothesis_binding_v0.json"
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
            "cross_sectional_open_interest_zscore_reversion_v0_terminal_insufficient_sample_and_"
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
        assert payload["baseline_verdict"] == BASELINE_VERDICT
        assert payload["unchanged_retry_blocked"] is True
        assert payload["selected_distinct_scope"] == SELECTED_DISTINCT_SCOPE
        assert payload["material_difference_proven"] is True
        assert payload["distinct_scope_ratified"] is True
        assert payload["trade_count"] == TRADE_COUNT
        assert str(CANONICAL_EVALUATION_DIR) in payload["canonical_evaluation_bundle"]
        assert payload["registration_digest"] == compute_registration_digest(payload)

    def test_no_economic_evaluation_authority(self) -> None:
        payload = json.loads(REGISTRATION_CONFIG.read_text(encoding="utf-8"))
        assert payload["authority_effect"] == "NONE"
        assert payload["runtime_effect"] == "NONE"
        assert payload["no_economic_reevaluation"] is True
        assert payload["no_parameter_change"] is True
        assert payload["no_policy_rescue"] is True


class TestLeadLagScopeRatificationConfig:
    def test_lead_lag_scope_ratification_config(self) -> None:
        assert LEAD_LAG_SCOPE_CONFIG.is_file()
        payload = json.loads(LEAD_LAG_SCOPE_CONFIG.read_text(encoding="utf-8"))
        ratification = materialize_lead_lag_offline_economic_evaluation_scope_ratification_v0(
            repo_root=REPO_ROOT
        )
        validation = validate_lead_lag_offline_economic_evaluation_scope_ratification_v0(payload)
        assert validation.verdict == LeadLagValidationVerdict.ACCEPTED
        assert payload["offline_economic_evaluation_scope_ratified"] is True
        assert payload["economic_evaluation_executed"] is False
        assert payload["economic_evaluation_authorized"] is False
        assert payload["futures_only"] is True
        assert payload["bitcoin_direction_allowed"] is False
        assert payload["runner_binding_ref"] == RUNNER_BINDING_REF
        assert payload["ratification_digest"] == ratification["ratification_digest"]


class TestOiZscoreVersionedBindingTerminalFields:
    def test_binding_terminal_insufficient_sample(self) -> None:
        binding = json.loads(OI_BINDING_PATH.read_text(encoding="utf-8"))
        registration = json.loads(REGISTRATION_CONFIG.read_text(encoding="utf-8"))
        assert binding["economic_evaluation_executed"] is True
        assert binding["unchanged_retry_blocked"] is True
        assert binding["terminal_status"] == TERMINAL_STATUS
        assert binding["trade_count"] == TRADE_COUNT
        assert binding["canonical_evaluation_timestamp"] == CANONICAL_EVALUATION_TIMESTAMP
        assert binding["selected_distinct_scope"] == SELECTED_DISTINCT_SCOPE
        assert apply_versioned_binding_registration_fields(binding, registration)[
            "baseline_verdict"
        ] == (BASELINE_VERDICT)


class TestGovernanceDoc:
    def test_governance_doc_present(self) -> None:
        assert GOVERNANCE_DOC.is_file()
        body = GOVERNANCE_DOC.read_text(encoding="utf-8")
        assert OPERATOR_GO_TOKEN in body
        assert (
            SELECTED_DISTINCT_SCOPE.replace("/", "&#47;") in body or SELECTED_DISTINCT_SCOPE in body
        )
