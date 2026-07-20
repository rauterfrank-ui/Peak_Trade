"""Technical canonical wiring authorization bound to economic boundary guard v1."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from src.governance.economic_diagnostic_optimization_boundary_v0 import (
    TECHNICAL_WIRING_AUTHORIZATION_ID,
    TECHNICAL_WIRING_AUTH_VERSION,
    TECHNICAL_WIRING_SCOPE_CLASS,
    build_boundary_report,
    forbidden_surface_changed_count,
    load_contract,
    load_technical_wiring_authorization,
    validate_technical_wiring_authorization,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
AUTH_PATH = REPO_ROOT / "config/governance/technical_canonical_wiring_authorization_v1.json"

AUTHORIZED_TECHNICAL_WIRING_FIXTURE = [
    "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py",
    "src/trading/master_v2/canonical_core_runtime_integration_bridge_v0.py",
    "src/trading/master_v2/integrated_vs_scenario_replay_full_system_parity_harness_v0.py",
    "src/backtest/mv2_research_wiring_v1.py",
    "tests/trading/master_v2/test_canonical_replay_input_builder_ssot_contract_v1.py",
]

AUTHORIZED_STRATEGY_SUITABILITY_AGREEMENT_FIXTURE = [
    "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py",
    "src/trading/master_v2/strategy_suitability_agreement_material_v1.py",
    "src/trading/master_v2/suitability_binding_v1.py",
    "src/backtest/mv2_research_wiring_v1.py",
    "src/backtest/strategy_signal_suitability_agreement_adapter_v1.py",
    "tests/trading/master_v2/test_strategy_suitability_agreement_consumer_contract_v1.py",
    "tests/trading/master_v2/test_strategy_suitability_agreement_static_contract_v1.py",
    "tests/backtest/test_strategy_signal_suitability_agreement_adapter_v1.py",
]

AUTHORIZED_SLICE4_LEGACY_BOUNDARY_CLOSEOUT_FIXTURE = [
    "src/trading/master_v2/evaluate_double_play_authority_boundary_v0.py",
    "src/trading/master_v2/offline_double_play_scenario_replay_v0.py",
    "src/ops/double_play/specialists.py",
    "tests/trading/master_v2/test_runtime_backtest_parity_and_legacy_boundary_closeout_v1.py",
    "config/governance/technical_canonical_wiring_authorization_v1.json",
]

AUTHORIZED_CANONICAL_ARCHITECTURE_DRIFT_GUARD_FIXTURE = [
    "tests/trading/master_v2/_canonical_architecture_drift_guard_helpers_v1.py",
    "tests/trading/master_v2/test_canonical_architecture_drift_guard_v1.py",
    "config/governance/technical_canonical_wiring_authorization_v1.json",
]

AUTHORIZED_SURFACE_P_REGISTRY_STATUS_CONTRACT_FIXTURE = [
    "tests/trading/master_v2/test_surface_p_full_bar_sequence_4_way_parity_completion_contract_v0.py",
    "tests/trading/master_v2/test_surface_p_offline_complete_runtime_bridge_bound_not_activated_contract_v0.py",
    "tests/trading/master_v2/test_surface_p_boundary_path_bar_sequence_4_way_parity_extension_contract_v0.py",
    "tests/trading/master_v2/test_runtime_bridge_pre_activation_gate_assessment_contract_v0.py",
    "tests/trading/master_v2/test_scope_event_generator_scenario_replay_binding_parity_rewire_contract_v0.py",
    "tests/trading/master_v2/test_reversal_preparation_scenario_replay_binding_parity_rewire_contract_v0.py",
    "tests/trading/master_v2/test_flat_before_opposite_side_scenario_replay_binding_parity_rewire_contract_v0.py",
    "tests/trading/master_v2/test_survival_suitability_scenario_replay_binding_parity_rewire_contract_v0.py",
    "tests/test_full_canonical_system_backtest_parity_gap_assessment_v0.py",
    "config/governance/technical_canonical_wiring_authorization_v1.json",
]


def _load_auth() -> dict:
    payload = json.loads(AUTH_PATH.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


class TestTechnicalCanonicalWiringAuthorizationContractV1:
    def test_authorization_contract_exists_and_is_versioned(self) -> None:
        assert AUTH_PATH.is_file()
        auth = load_technical_wiring_authorization(REPO_ROOT)
        assert auth is not None
        valid, reasons = validate_technical_wiring_authorization(auth)
        assert valid is True
        assert reasons == ()
        assert auth["contract_version"] == TECHNICAL_WIRING_AUTH_VERSION
        assert auth["authorized_scope_class"] == TECHNICAL_WIRING_SCOPE_CLASS
        assert auth["authorization_token"] == TECHNICAL_WIRING_AUTHORIZATION_ID
        assert auth["pr_specific_exception"] is False
        assert auth["branch_specific_exception"] is False
        assert auth["broad_master_v2_grant"] is False

    def test_bound_from_boundary_contract(self) -> None:
        contract = load_contract(REPO_ROOT)
        assert (
            contract["technical_canonical_wiring_authorization"]
            == "config/governance/technical_canonical_wiring_authorization_v1.json"
        )
        assert contract["immutable_flags"]["MASTER_V2_MUTATION_ALLOWED"] is False

    def test_authorization_not_token_alone(self) -> None:
        token_only = {
            "authorization_token": TECHNICAL_WIRING_AUTHORIZATION_ID,
            "contract_version": TECHNICAL_WIRING_AUTH_VERSION,
        }
        valid, reasons = validate_technical_wiring_authorization(token_only)
        assert valid is False
        assert "TECHNICAL_CANONICAL_WIRING_AUTHORIZATION_INVALID" in reasons


class TestTechnicalCanonicalWiringAuthorizationNegativeV1:
    def test_unauthorized_master_v2_mutation_fails(self) -> None:
        report = build_boundary_report(
            ["src/trading/master_v2/directional_assessment_v1.py"],
            repo_root=REPO_ROOT,
        )
        assert report.admissible is False
        assert report.fail_closed is True
        assert report.master_v2_changed is True
        assert report.technical_wiring_authorization_applied is False
        assert "FORBIDDEN_MUTATION_SURFACE_MATCH" in report.reason_codes

    def test_unauthorized_double_play_composition_fails(self) -> None:
        report = build_boundary_report(
            ["src/trading/master_v2/double_play_composition.py"],
            repo_root=REPO_ROOT,
        )
        assert report.admissible is False
        assert report.double_play_changed is True
        assert "FORBIDDEN_MUTATION_SURFACE_MATCH" in report.reason_codes

    def test_unauthorized_runtime_promotion_authority_surface_fails(self) -> None:
        report = build_boundary_report(
            ["src/trading/master_v2/staged_execution_enablement_v1.py"],
            repo_root=REPO_ROOT,
        )
        assert report.admissible is False
        assert report.promotion_runtime_authority_changed is True
        assert "FORBIDDEN_MUTATION_SURFACE_MATCH" in report.reason_codes

    def test_missing_authorization_contract_fails_for_forbidden_diff(self) -> None:
        report = build_boundary_report(
            AUTHORIZED_TECHNICAL_WIRING_FIXTURE,
            repo_root=REPO_ROOT,
            skip_technical_wiring_authorization=True,
        )
        assert report.admissible is False
        assert report.fail_closed is True
        assert "FORBIDDEN_MUTATION_SURFACE_MATCH" in report.reason_codes
        assert "TECHNICAL_CANONICAL_WIRING_AUTHORIZATION_MISSING" in report.reason_codes

    def test_wrong_token_fails(self) -> None:
        auth = _load_auth()
        auth["authorization_token"] = "WRONG_TOKEN"
        valid, reasons = validate_technical_wiring_authorization(auth)
        assert valid is False
        assert "TECHNICAL_WIRING_TOKEN_MISMATCH" in reasons
        report = build_boundary_report(
            AUTHORIZED_TECHNICAL_WIRING_FIXTURE,
            repo_root=REPO_ROOT,
            technical_wiring_authorization=auth,
        )
        assert report.admissible is False
        assert "TECHNICAL_CANONICAL_WIRING_AUTHORIZATION_INVALID" in report.reason_codes

    def test_wrong_scope_id_fails(self) -> None:
        auth = _load_auth()
        auth["scope_id"] = "WRONG_SCOPE"
        valid, reasons = validate_technical_wiring_authorization(auth)
        assert valid is False
        assert "TECHNICAL_WIRING_SCOPE_ID_MISMATCH" in reasons
        report = build_boundary_report(
            AUTHORIZED_TECHNICAL_WIRING_FIXTURE,
            repo_root=REPO_ROOT,
            technical_wiring_authorization=auth,
        )
        assert report.admissible is False

    def test_unauthorized_extra_file_fails(self) -> None:
        changed = [
            *AUTHORIZED_TECHNICAL_WIRING_FIXTURE,
            "src/trading/master_v2/double_play_composition.py",
        ]
        report = build_boundary_report(changed, repo_root=REPO_ROOT)
        assert report.admissible is False
        assert report.fail_closed is True
        assert report.technical_wiring_authorization_applied is False
        assert "TECHNICAL_CANONICAL_WIRING_UNAUTHORIZED_PATH" in report.reason_codes
        assert "FORBIDDEN_MUTATION_SURFACE_MATCH" in report.reason_codes

    @pytest.mark.parametrize(
        "effect_key",
        [
            "RUNTIME_EFFECT",
            "AUTHORITY_EFFECT",
            "ORDER_EFFECT",
            "CREDENTIAL_EFFECT",
            "SCHEDULER_EFFECT",
        ],
    )
    def test_authority_runtime_order_credential_scheduler_effect_fails(
        self, effect_key: str
    ) -> None:
        auth = copy.deepcopy(_load_auth())
        auth["forbidden_effects"][effect_key] = "PRESENT"
        auth["required_semantic_invariants"][effect_key] = "PRESENT"
        valid, reasons = validate_technical_wiring_authorization(auth)
        assert valid is False
        assert "TECHNICAL_CANONICAL_WIRING_EFFECT_FORBIDDEN" in reasons
        report = build_boundary_report(
            AUTHORIZED_TECHNICAL_WIRING_FIXTURE,
            repo_root=REPO_ROOT,
            technical_wiring_authorization=auth,
        )
        assert report.admissible is False

    def test_pr_or_branch_hardcode_in_authorization_contract_fails(self) -> None:
        auth = copy.deepcopy(_load_auth())
        auth["notes"] = ["exception for PR #5226 on branch cursor/canonical-replay-v1"]
        valid, reasons = validate_technical_wiring_authorization(auth)
        assert valid is False
        assert "TECHNICAL_WIRING_PR_OR_BRANCH_HARDCODE" in reasons

    def test_broad_master_v2_grant_fails(self) -> None:
        auth = copy.deepcopy(_load_auth())
        auth["allowed_paths"] = ["src/trading/master_v2/"]
        auth["broad_master_v2_grant"] = True
        valid, reasons = validate_technical_wiring_authorization(auth)
        assert valid is False
        assert "TECHNICAL_WIRING_BROAD_MASTER_V2_GRANT" in reasons or (
            "TECHNICAL_WIRING_FLAG_NOT_FALSE:broad_master_v2_grant" in reasons
        )

    def test_research_plus_forbidden_core_without_matching_auth_fails(self) -> None:
        changed = [
            "src/research/linear_evidence/cost_model.py",
            "src/trading/master_v2/directional_assessment_v1.py",
        ]
        report = build_boundary_report(changed, repo_root=REPO_ROOT)
        assert report.admissible is False
        assert report.fail_closed is True
        assert report.master_v2_changed is True
        assert "FORBIDDEN_MUTATION_SURFACE_MATCH" in report.reason_codes


class TestTechnicalCanonicalWiringAuthorizationPositiveV1:
    def test_authorized_technical_builder_consolidation_fixture_passes(self) -> None:
        report = build_boundary_report(
            AUTHORIZED_TECHNICAL_WIRING_FIXTURE,
            repo_root=REPO_ROOT,
        )
        assert report.admissible is True
        assert report.fail_closed is False
        assert report.technical_wiring_authorization_applied is True
        assert report.technical_wiring_authorization_version == TECHNICAL_WIRING_AUTH_VERSION
        assert "TECHNICAL_CANONICAL_WIRING_AUTHORIZED" in report.reason_codes
        assert forbidden_surface_changed_count(report) == 0
        assert report.canonical_trading_semantics_changed is False
        assert report.master_v2_changed is False
        assert report.promotion_runtime_authority_changed is False
        assert report.risk_sizing_changed is False
        assert report.safety_killswitch_reconciliation_changed is False
        # Forbidden matches remain visible for audit, but are authorized.
        assert len(report.forbidden_surface_matches) >= 1

    def test_authorized_strategy_suitability_agreement_fixture_passes(self) -> None:
        report = build_boundary_report(
            AUTHORIZED_STRATEGY_SUITABILITY_AGREEMENT_FIXTURE,
            repo_root=REPO_ROOT,
        )
        assert report.admissible is True
        assert report.fail_closed is False
        assert report.technical_wiring_authorization_applied is True
        assert "TECHNICAL_CANONICAL_WIRING_AUTHORIZED" in report.reason_codes
        assert forbidden_surface_changed_count(report) == 0
        assert report.canonical_trading_semantics_changed is False
        assert report.promotion_runtime_authority_changed is False
        assert report.risk_sizing_changed is False
        assert report.safety_killswitch_reconciliation_changed is False

    def test_authorized_slice4_legacy_boundary_closeout_fixture_passes(self) -> None:
        report = build_boundary_report(
            AUTHORIZED_SLICE4_LEGACY_BOUNDARY_CLOSEOUT_FIXTURE,
            repo_root=REPO_ROOT,
        )
        assert report.admissible is True
        assert report.fail_closed is False
        assert report.technical_wiring_authorization_applied is True
        assert "TECHNICAL_CANONICAL_WIRING_AUTHORIZED" in report.reason_codes
        assert forbidden_surface_changed_count(report) == 0
        assert report.canonical_trading_semantics_changed is False
        assert report.promotion_runtime_authority_changed is False
        assert report.risk_sizing_changed is False
        assert report.safety_killswitch_reconciliation_changed is False

    def test_authorized_canonical_architecture_drift_guard_fixture_passes(self) -> None:
        report = build_boundary_report(
            AUTHORIZED_CANONICAL_ARCHITECTURE_DRIFT_GUARD_FIXTURE,
            repo_root=REPO_ROOT,
        )
        assert report.admissible is True
        assert report.fail_closed is False
        assert report.technical_wiring_authorization_applied is True
        assert "TECHNICAL_CANONICAL_WIRING_AUTHORIZED" in report.reason_codes
        assert forbidden_surface_changed_count(report) == 0
        assert report.canonical_trading_semantics_changed is False
        assert report.promotion_runtime_authority_changed is False
        assert report.risk_sizing_changed is False
        assert report.safety_killswitch_reconciliation_changed is False

    def test_authorized_surface_p_registry_status_contract_fixture_passes(self) -> None:
        report = build_boundary_report(
            AUTHORIZED_SURFACE_P_REGISTRY_STATUS_CONTRACT_FIXTURE,
            repo_root=REPO_ROOT,
        )
        assert report.admissible is True
        assert report.fail_closed is False
        assert report.technical_wiring_authorization_applied is True
        assert "TECHNICAL_CANONICAL_WIRING_AUTHORIZED" in report.reason_codes
        assert forbidden_surface_changed_count(report) == 0
        assert report.canonical_trading_semantics_changed is False
        assert report.promotion_runtime_authority_changed is False
        assert report.risk_sizing_changed is False
        assert report.safety_killswitch_reconciliation_changed is False

    def test_existing_allowed_research_surfaces_still_pass(self) -> None:
        report = build_boundary_report(
            [
                "src/research/linear_evidence/cost_model.py",
                "scripts/research/offline_linear_cost_model_diagnostics_v0.py",
            ],
            repo_root=REPO_ROOT,
        )
        assert report.admissible is True
        assert report.technical_wiring_authorization_applied is False
        assert "ALLOWED_OPTIMIZATION_SURFACE_ONLY" in report.reason_codes

    def test_authorization_not_bound_to_pr_or_branch(self) -> None:
        auth = _load_auth()
        serialized = json.dumps(auth, sort_keys=True)
        assert "5226" not in serialized
        assert "PR #" not in serialized.upper()
        assert "cursor/" not in serialized
        report = build_boundary_report(
            AUTHORIZED_TECHNICAL_WIRING_FIXTURE,
            repo_root=REPO_ROOT,
        )
        assert report.admissible is True
        assert report.technical_wiring_authorization_applied is True
