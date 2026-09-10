"""Guard tests for economic/diagnostic optimization boundary v0."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from src.governance.economic_diagnostic_optimization_boundary_v0 import (
    CONTRACT_VERSION,
    PACKAGE_MARKER,
    REASON_FORBIDDEN_SURFACE,
    REASON_IMPACT_UNKNOWN,
    REASON_TECHNICAL_WIRING_AUTHORIZED,
    REASON_TECHNICAL_WIRING_UNAUTHORIZED_PATH,
    build_boundary_report,
    export_canonical_owner_inventory,
    forbidden_surface_changed_count,
    load_contract,
    load_decommission_authorization,
    load_owner_map,
)
from src.governance.semantics_neutral_decommission_authorization_v1 import (
    DECOMMISSION_AUTH_VERSION,
    DECOMMISSION_MUTATION_PURPOSE,
    REASON_DECOMMISSION_AUTHORIZED,
    REASON_DECOMMISSION_SEMANTIC_CHANGE,
    compute_decommission_evidence_digest,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = REPO_ROOT / "config/governance/economic_diagnostic_optimization_boundary_v0.json"
OWNER_MAP_PATH = (
    REPO_ROOT
    / "config/governance/economic_diagnostic_optimization_boundary_canonical_owner_map_v0.json"
)
GOVERNANCE_DOC = (
    REPO_ROOT
    / "docs/governance/ECONOMIC_DIAGNOSTIC_OPTIMIZATION_BOUNDARY_AND_CANONICAL_TRADING_LOGIC_IMMUTABILITY_CONTRACT_V0.md"
)


REQUIRED_IMMUTABLE_FLAGS = {
    "ECONOMIC_AND_DIAGNOSTIC_OPTIMIZATION_ALLOWED": True,
    "CANONICAL_TRADING_LOGIC_MUTATION_ALLOWED": False,
    "MASTER_V2_MUTATION_ALLOWED": False,
    "BULL_BEAR_MUTATION_ALLOWED": False,
    "DOUBLE_PLAY_MUTATION_ALLOWED": False,
    "SCOPE_ENTRY_EXIT_REVERSAL_MUTATION_ALLOWED": False,
    "CAPITAL_RISK_SIZING_MUTATION_ALLOWED": False,
    "SAFETY_KERNEL_MUTATION_ALLOWED": False,
    "KILLSWITCH_MUTATION_ALLOWED": False,
    "RECONCILIATION_MUTATION_ALLOWED": False,
    "PROMOTION_AUTHORITY_MUTATION_ALLOWED": False,
    "RUNTIME_AUTHORITY_MUTATION_ALLOWED": False,
    "ECONOMIC_RESULT_MAY_NOT_JUSTIFY_CANONICAL_LOGIC_CHANGE": True,
    "NEGATIVE_RESULT_MAY_NOT_TRIGGER_CANONICAL_FILTER_RELAXATION": True,
    "LOW_TRADE_COUNT_MAY_NOT_TRIGGER_CANONICAL_LOGIC_RELAXATION": True,
    "POSITIVE_RESULT_MAY_NOT_BYPASS_ROBUSTNESS_SAFETY_OR_PROMOTION_GATES": True,
}


class TestEconomicDiagnosticOptimizationBoundaryContractV0:
    def test_contract_and_owner_map_exist(self) -> None:
        assert CONTRACT_PATH.is_file()
        assert OWNER_MAP_PATH.is_file()
        assert GOVERNANCE_DOC.is_file()

    def test_immutable_flags_bound(self) -> None:
        contract = load_contract(REPO_ROOT)
        assert contract["contract_version"] == CONTRACT_VERSION
        assert contract["parallel_ssot_created"] is False
        for flag, expected in REQUIRED_IMMUTABLE_FLAGS.items():
            assert contract["immutable_flags"][flag] is expected

    def test_allowed_and_forbidden_surfaces_bound(self) -> None:
        contract = load_contract(REPO_ROOT)
        owner_map = load_owner_map(REPO_ROOT)
        assert len(contract["allowed_optimization_surfaces"]) >= 15
        assert len(contract["forbidden_mutation_surface_categories"]) >= 10
        assert owner_map["no_path_guessing"] is True
        assert len(owner_map["forbidden_mutation_surfaces"]) >= 10
        assert len(owner_map["allowed_optimization_surfaces"]) >= 10

    def test_owner_map_resolves_from_existing_sources(self) -> None:
        owner_map = load_owner_map(REPO_ROOT)
        for source in owner_map["source_owners"]:
            assert (REPO_ROOT / source).is_file(), source

    def test_canonical_owner_inventory_exports(self) -> None:
        inventory = export_canonical_owner_inventory(REPO_ROOT)
        assert inventory["package_marker"] == PACKAGE_MARKER
        assert inventory["no_path_guessing"] is True
        assert inventory["canonical_governance_owner"].endswith(
            "PEAK_TRADE_IMPLEMENTATION_CONTRACT.md"
        )


class TestEconomicDiagnosticOptimizationBoundaryGuardPositiveV0:
    @pytest.mark.parametrize(
        "changed_files",
        [
            ["src/research/offline_linear_cost_diagnostic_row_materializer_v0.py"],
            [
                "src/research/linear_evidence/cost_model.py",
                "scripts/research/offline_linear_cost_model_diagnostics_v0.py",
            ],
            [
                "src/research/linear_evidence/feature_matrix.py",
                "src/research/linear_evidence/contracts.py",
            ],
            ["scripts/ops/primary_evidence_retention_v0.py"],
            [
                "config/governance/economic_diagnostic_optimization_boundary_v0.json",
                "tests/governance/test_economic_diagnostic_optimization_boundary_guard_v0.py",
            ],
            [
                "src/research/linear_evidence/signal_orthogonality.py",
                "scripts/research/offline_signal_orthogonality_diagnostics_v0.py",
                "scripts/research/classify_step29l2_offline_linear_evidence_status_after_pr5044_v0.py",
                "tests/research/test_offline_signal_orthogonality_diagnostics_v0.py",
                "tests/research/test_step29l2_import_boundary_classification_v0.py",
            ],
            [
                "src/research/cross_sectional_open_interest_zscore_reversion_v0_terminal_insufficient_sample_and_distinct_futures_research_scope_ratification_v0.py",
                "scripts/research/materialize_cross_sectional_open_interest_zscore_reversion_v0_terminal_insufficient_sample_operator_ratification_and_lead_lag_scope_ratification_v0.py",
            ],
            [
                "src/research/cross_sectional_futures_lead_lag_information_diffusion_v0_terminal_insufficient_sample_and_distinct_futures_research_scope_ratification_v0.py",
                "src/research/cross_sectional_futures_pairwise_lead_lag_spillover_v1_research_scope_ratification_v0.py",
                "scripts/research/materialize_cross_sectional_futures_lead_lag_information_diffusion_v0_terminal_insufficient_sample_operator_ratification_and_pairwise_spillover_scope_ratification_v0.py",
            ],
            [
                "src/research/cross_sectional_futures_pairwise_lead_lag_spillover_v1_versioned_hypothesis_binding_v0.py",
                "scripts/research/materialize_cross_sectional_futures_pairwise_lead_lag_spillover_v1_versioned_hypothesis_binding_v0.py",
                "tests/research/test_cross_sectional_futures_pairwise_lead_lag_spillover_v1_versioned_hypothesis_binding_v0_contract.py",
                "config/governance/economic_diagnostic_optimization_boundary_canonical_owner_map_v0.json",
            ],
            [
                "src/research/cross_sectional_futures_pairwise_lead_lag_spillover_v1_score_v0.py",
                "src/research/cross_sectional_futures_pairwise_lead_lag_spillover_v1_score_and_ranking_contract_v0.py",
                "scripts/research/materialize_cross_sectional_futures_pairwise_lead_lag_spillover_v1_score_and_ranking_contract_v0.py",
                "tests/research/test_cross_sectional_futures_pairwise_lead_lag_spillover_v1_score_and_ranking_contract_v0_contract.py",
                "config/governance/economic_diagnostic_optimization_boundary_canonical_owner_map_v0.json",
            ],
            [
                "src/research/cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_evaluation_authorization_ratification_v0.py",
                "scripts/research/materialize_cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_evaluation_authorization_ratification_v0.py",
                "tests/research/test_cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_evaluation_authorization_ratification_v0_contract.py",
                "config/governance/economic_diagnostic_optimization_boundary_canonical_owner_map_v0.json",
            ],
            [
                "src/research/trend_following_v2_versioned_research_binding_v0.py",
                "src/research/trend_following_v2_offline_economic_evaluation_authorization_ratification_v0.py",
                "scripts/research/materialize_trend_following_v2_offline_economic_evaluation_authorization_ratification_v0.py",
                "tests/research/test_trend_following_v2_offline_economic_evaluation_authorization_ratification_v0_contract.py",
                "config/governance/economic_diagnostic_optimization_boundary_canonical_owner_map_v0.json",
            ],
            [
                "src/research/momentum_1h_v2_versioned_research_binding_v0.py",
                "src/research/momentum_1h_v2_offline_economic_evaluation_authorization_ratification_v0.py",
                "scripts/research/materialize_momentum_1h_v2_offline_economic_evaluation_authorization_ratification_v0.py",
                "tests/research/test_momentum_1h_v2_offline_economic_evaluation_authorization_ratification_v0_contract.py",
                "config/governance/economic_diagnostic_optimization_boundary_canonical_owner_map_v0.json",
            ],
            [
                "src/research/trend_following_v2_offline_economic_evaluation_execution_v0.py",
                "scripts/ops/run_trend_following_v2_offline_economic_evaluation_execution_v0.py",
                "tests/research/test_trend_following_v2_offline_economic_evaluation_execution_infrastructure_v0.py",
                "config/ops/trend_following_v2_economic_evaluation_v1.json",
                "config/governance/economic_diagnostic_optimization_boundary_canonical_owner_map_v0.json",
            ],
            [
                "src/research/momentum_1h_v2_offline_economic_evaluation_execution_v0.py",
                "scripts/ops/run_momentum_1h_v2_offline_economic_evaluation_execution_v0.py",
                "tests/research/test_momentum_1h_v2_offline_economic_evaluation_execution_infrastructure_v0.py",
                "config/ops/momentum_1h_v2_economic_evaluation_v1.json",
                "config/governance/economic_diagnostic_optimization_boundary_canonical_owner_map_v0.json",
            ],
            [
                "src/research/momentum_1h_v2_offline_economic_evaluation_execution_v0.py",
                "scripts/ops/run_momentum_1h_v2_offline_economic_evaluation_execution_v0.py",
                "tests/research/test_momentum_1h_v2_offline_economic_evaluation_execution_infrastructure_v0.py",
                "tests/research/test_momentum_1h_v2_offline_economic_evaluation_dispatch_to_baseline_repair_v0.py",
                "config/governance/economic_diagnostic_optimization_boundary_canonical_owner_map_v0.json",
            ],
            [
                "src/research/momentum_1h_v2_offline_economic_evaluation_execution_authorization_supersession_v1.py",
                "scripts/research/materialize_momentum_1h_v2_offline_economic_evaluation_execution_authorization_supersession_v1.py",
                "src/research/momentum_1h_v2_offline_economic_evaluation_execution_v0.py",
                "scripts/ops/run_momentum_1h_v2_offline_economic_evaluation_execution_v0.py",
                "tests/research/test_momentum_1h_v2_execution_v1_token_binding_repair_v0.py",
                "tests/research/test_momentum_1h_v2_offline_economic_evaluation_execution_infrastructure_v0.py",
                "config/research/momentum_1h_v2_offline_economic_evaluation_execution_authorization_supersession_v1.json",
                "config/governance/economic_diagnostic_optimization_boundary_canonical_owner_map_v0.json",
            ],
            [
                "src/research/trend_following_v2_offline_economic_evaluation_execution_v0.py",
                "scripts/ops/run_trend_following_v2_offline_economic_evaluation_execution_v0.py",
                "scripts/ops/materialize_trend_following_v2_offline_economic_evaluation_execution_dispatch_implementation_v0.py",
                "tests/research/test_trend_following_v2_offline_economic_evaluation_execution_dispatch_implementation_v0.py",
                "config/governance/economic_diagnostic_optimization_boundary_canonical_owner_map_v0.json",
            ],
            [
                "src/research/trend_following_v2_offline_economic_evaluation_execution_v0.py",
                "scripts/ops/run_trend_following_v2_offline_economic_evaluation_execution_v0.py",
                "scripts/ops/materialize_trend_following_v2_offline_economic_evaluation_baseline_execution_implementation_v0.py",
                "tests/research/test_trend_following_v2_offline_economic_evaluation_baseline_execution_implementation_v0.py",
                "tests/research/test_trend_following_v2_baseline_execution_entry_point_result_contract_repair_v0.py",
                "config/governance/economic_diagnostic_optimization_boundary_canonical_owner_map_v0.json",
            ],
            [
                "src/research/cross_sectional_futures_lead_lag_information_diffusion_v0_offline_economic_evaluation_execution_v0.py",
                "tests/research/test_cross_sectional_futures_lead_lag_information_diffusion_v0_offline_economic_evaluation_execution_infrastructure_v0.py",
                "tests/research/test_cross_sectional_futures_lead_lag_information_diffusion_v0_offline_economic_evaluation_entry_point_guard_and_dispatch_repair_v0.py",
            ],
            [
                "src/research/cross_sectional_futures_lead_lag_information_diffusion_v0_offline_economic_evaluation_execution_v0.py",
                "src/research/cross_sectional_futures_lead_lag_information_diffusion_v0_offline_economic_evaluation_scope_ratification_v0.py",
                "tests/research/test_cross_sectional_futures_lead_lag_information_diffusion_v0_offline_economic_evaluation_execution_authorization_ratification_repair_v0.py",
                "tests/research/test_cross_sectional_futures_lead_lag_information_diffusion_v0_offline_economic_evaluation_full_runner_v0.py",
            ],
            [
                "src/research/cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_evaluation_execution_v0.py",
                "tests/research/test_cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_evaluation_reevaluation_baseline_actual_execution_owner_implementation_v0.py",
            ],
            [
                "src/research/cross_sectional_cost_execution_binding_normalization_v0.py",
                "src/research/cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_evaluation_execution_v0.py",
                "src/research/cross_sectional_futures_lead_lag_information_diffusion_v0_offline_economic_evaluation_execution_v0.py",
                "tests/research/test_cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_evaluation_reevaluation_baseline_execution_data_unavailable_repair_v0.py",
                "config/governance/economic_diagnostic_optimization_boundary_canonical_owner_map_v0.json",
            ],
            [
                "src/research/cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_evaluation_execution_v0.py",
                "scripts/ops/run_cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_evaluation_execution_v0.py",
                "config/ops/cross_sectional_futures_pairwise_lead_lag_spillover_v1_economic_evaluation_v1.json",
                "tests/research/test_cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_evaluation_execution_infrastructure_v0.py",
                "tests/research/test_cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_evaluation_execution_dispatch_implementation_v0.py",
            ],
            [
                "src/research/cross_sectional_futures_pairwise_lead_lag_spillover_v1_portfolio_binding_v0.py",
                "scripts/research/materialize_cross_sectional_futures_pairwise_lead_lag_spillover_v1_portfolio_binding_implementation_v0.py",
                "tests/research/test_cross_sectional_futures_pairwise_lead_lag_spillover_v1_portfolio_binding_implementation_v0_contract.py",
                "src/research/cross_sectional_futures_pairwise_lead_lag_spillover_v1_versioned_hypothesis_binding_v0.py",
                "src/research/cross_sectional_futures_pairwise_lead_lag_spillover_v1_score_and_ranking_contract_v0.py",
                "config/governance/economic_diagnostic_optimization_boundary_canonical_owner_map_v0.json",
            ],
            [
                "config/research/full_canonical_system_economic_evidence_generation_v1_offline_execution_result_v0.json",
                "tests/research/test_full_canonical_system_economic_evidence_generation_v1_offline_execution_result_v0_contract.py",
                "config/governance/economic_diagnostic_optimization_boundary_canonical_owner_map_v0.json",
            ],
        ],
    )
    def test_positive_cases_admissible(self, changed_files: list[str]) -> None:
        report = build_boundary_report(changed_files, repo_root=REPO_ROOT)
        assert report.admissible is True
        assert report.fail_closed is False
        assert forbidden_surface_changed_count(report) == 0
        assert report.canonical_trading_semantics_changed is False

    def test_pr5157_offline_signal_orthogonality_surfaces_classified(self) -> None:
        changed_files = [
            "src/research/linear_evidence/signal_orthogonality.py",
            "scripts/research/offline_signal_orthogonality_diagnostics_v0.py",
            "scripts/research/classify_step29l2_offline_linear_evidence_status_after_pr5044_v0.py",
            "tests/research/test_offline_signal_orthogonality_diagnostics_v0.py",
            "tests/research/test_step29l2_import_boundary_classification_v0.py",
        ]
        report = build_boundary_report(changed_files, repo_root=REPO_ROOT)
        assert report.admissible is True
        assert report.economic_or_diagnostic_only is True
        assert report.impact_unknown is False
        assert "ALLOWED_OPTIMIZATION_SURFACE_ONLY" in report.reason_codes
        assert forbidden_surface_changed_count(report) == 0
        assert report.master_v2_changed is False
        assert report.promotion_runtime_authority_changed is False
        assert report.risk_sizing_changed is False
        assert report.safety_killswitch_reconciliation_changed is False
        assert set(report.allowed_surface_classification) >= {
            "COST_MODEL_DIAGNOSTICS",
            "FEATURE_SCALING_OR_NUMERICAL_CONDITIONING_WITHOUT_TRADING_SEMANTIC_EFFECT",
            "REPORTING_AND_EVIDENCE_REPAIR",
        }

    def test_offline_productive_signal_orthogonality_results_interpretation_surfaces_classified(
        self,
    ) -> None:
        changed_files = [
            "src/research/linear_evidence/signal_orthogonality_results_interpretation_v0.py",
            "scripts/ops/materialize_offline_productive_signal_orthogonality_results_interpretation_v0.py",
            "tests/research/test_offline_productive_signal_orthogonality_results_interpretation_v0.py",
            "config/governance/economic_diagnostic_optimization_boundary_canonical_owner_map_v0.json",
        ]
        report = build_boundary_report(changed_files, repo_root=REPO_ROOT)
        assert report.admissible is True
        assert report.economic_or_diagnostic_only is True
        assert report.impact_unknown is False
        assert "ALLOWED_OPTIMIZATION_SURFACE_ONLY" in report.reason_codes
        assert forbidden_surface_changed_count(report) == 0
        assert set(report.allowed_surface_classification) >= {
            "COST_MODEL_DIAGNOSTICS",
            "FEATURE_SCALING_OR_NUMERICAL_CONDITIONING_WITHOUT_TRADING_SEMANTIC_EFFECT",
            "REPORTING_AND_EVIDENCE_REPAIR",
        }

    def test_offline_productive_factor_exposure_diagnostics_surfaces_classified(self) -> None:
        changed_files = [
            "src/research/linear_evidence/factor_exposure.py",
            "src/research/linear_evidence/offline_productive_factor_exposure_diagnostics_v0.py",
            "scripts/ops/materialize_offline_productive_factor_exposure_diagnostics_v0.py",
            "tests/research/test_offline_productive_factor_exposure_diagnostics_v0.py",
            "config/governance/economic_diagnostic_optimization_boundary_canonical_owner_map_v0.json",
        ]
        report = build_boundary_report(changed_files, repo_root=REPO_ROOT)
        assert report.admissible is True
        assert report.economic_or_diagnostic_only is True
        assert report.impact_unknown is False
        assert "ALLOWED_OPTIMIZATION_SURFACE_ONLY" in report.reason_codes
        assert forbidden_surface_changed_count(report) == 0
        assert set(report.allowed_surface_classification) >= {
            "COST_MODEL_DIAGNOSTICS",
            "FEATURE_SCALING_OR_NUMERICAL_CONDITIONING_WITHOUT_TRADING_SEMANTIC_EFFECT",
            "REPORTING_AND_EVIDENCE_REPAIR",
        }

    def test_factor_exposure_parity_surfaces_classified(self) -> None:
        changed_files = [
            "src/research/linear_evidence/factor_exposure.py",
            "scripts/research/offline_factor_exposure_diagnostics_v0.py",
            "tests/research/test_offline_factor_exposure_diagnostics_v0.py",
            "config/governance/economic_diagnostic_optimization_boundary_canonical_owner_map_v0.json",
        ]
        report = build_boundary_report(changed_files, repo_root=REPO_ROOT)
        assert report.admissible is True
        assert report.impact_unknown is False
        assert "ALLOWED_OPTIMIZATION_SURFACE_ONLY" in report.reason_codes
        assert forbidden_surface_changed_count(report) == 0

    def test_factor_exposure_productive_contract_surfaces_classified(self) -> None:
        changed_files = [
            "src/backtest/economic_viability_evidence_v1.py",
            "src/research/linear_evidence/factor_exposure.py",
            "src/research/linear_evidence/factor_exposure_productive_contract_v0.py",
            "tests/research/test_offline_factor_exposure_productive_contract_v0.py",
            "config/governance/economic_diagnostic_optimization_boundary_canonical_owner_map_v0.json",
        ]
        report = build_boundary_report(changed_files, repo_root=REPO_ROOT)
        assert report.admissible is True
        assert report.impact_unknown is False
        assert "ALLOWED_OPTIMIZATION_SURFACE_ONLY" in report.reason_codes
        assert forbidden_surface_changed_count(report) == 0
        assert set(report.allowed_surface_classification) >= {
            "COST_MODEL_DIAGNOSTICS",
            "FEATURE_SCALING_OR_NUMERICAL_CONDITIONING_WITHOUT_TRADING_SEMANTIC_EFFECT",
            "TARGET_BINDING_REPAIR",
        }

    def test_parameter_sensitivity_productive_binding_surfaces_classified(self) -> None:
        changed_files = [
            "src/research/linear_evidence/parameter_sensitivity_productive_contract_v0.py",
            "src/research/offline_parameter_sensitivity_productive_input_join_materializer_v0.py",
            "scripts/research/offline_parameter_sensitivity_productive_input_join_materializer_v0.py",
            "scripts/research/offline_parameter_sensitivity_surface_v0.py",
            "tests/research/test_offline_parameter_sensitivity_productive_contract_v0.py",
            "tests/research/test_offline_parameter_sensitivity_productive_input_join_materializer_v0.py",
            "tests/research/test_offline_parameter_sensitivity_surface_v0.py",
            "config/governance/economic_diagnostic_optimization_boundary_canonical_owner_map_v0.json",
        ]
        report = build_boundary_report(changed_files, repo_root=REPO_ROOT)
        assert report.admissible is True
        assert report.impact_unknown is False
        assert "ALLOWED_OPTIMIZATION_SURFACE_ONLY" in report.reason_codes
        assert forbidden_surface_changed_count(report) == 0
        assert set(report.allowed_surface_classification) >= {
            "DETERMINISTIC_MATERIALIZATION_REPAIR",
            "EXPLICITLY_CALIBRATABLE_RESEARCH_PARAMETERS_WITHIN_PREDECLARED_RANGES",
            "TARGET_BINDING_REPAIR",
            "WALK_FORWARD_MONTE_CARLO_STRESS_AND_PARAMETER_SENSITIVITY",
        }

    def test_parameter_sensitivity_model_spec_alignment_surfaces_classified(self) -> None:
        changed_files = [
            "src/research/linear_evidence/fitters.py",
            "src/research/linear_evidence/sensitivity.py",
            "tests/research/test_offline_parameter_sensitivity_model_spec_alignment_v0.py",
            "config/governance/economic_diagnostic_optimization_boundary_canonical_owner_map_v0.json",
        ]
        report = build_boundary_report(changed_files, repo_root=REPO_ROOT)
        assert report.admissible is True
        assert report.impact_unknown is False
        assert "ALLOWED_OPTIMIZATION_SURFACE_ONLY" in report.reason_codes
        assert forbidden_surface_changed_count(report) == 0
        assert set(report.allowed_surface_classification) >= {
            "COST_MODEL_DIAGNOSTICS",
            "EXPLICITLY_CALIBRATABLE_RESEARCH_PARAMETERS_WITHIN_PREDECLARED_RANGES",
            "TARGET_BINDING_REPAIR",
            "WALK_FORWARD_MONTE_CARLO_STRESS_AND_PARAMETER_SENSITIVITY",
        }

    def test_rolling_linear_drift_surfaces_classified(self) -> None:
        changed_files = [
            "src/research/linear_evidence/drift.py",
            "scripts/research/offline_rolling_linear_drift_diagnostics_v0.py",
            "tests/research/test_offline_rolling_linear_drift_diagnostics_v0.py",
            "config/governance/economic_diagnostic_optimization_boundary_canonical_owner_map_v0.json",
        ]
        report = build_boundary_report(changed_files, repo_root=REPO_ROOT)
        assert report.admissible is True
        assert report.impact_unknown is False
        assert "ALLOWED_OPTIMIZATION_SURFACE_ONLY" in report.reason_codes
        assert forbidden_surface_changed_count(report) == 0
        assert set(report.allowed_surface_classification) >= {
            "COST_MODEL_DIAGNOSTICS",
            "WALK_FORWARD_MONTE_CARLO_STRESS_AND_PARAMETER_SENSITIVITY",
        }

    def test_productive_rolling_linear_drift_surfaces_classified(self) -> None:
        changed_files = [
            "src/research/linear_evidence/offline_productive_rolling_linear_drift_diagnostics_v0.py",
            "scripts/ops/materialize_offline_productive_rolling_linear_drift_diagnostics_v0.py",
            "tests/research/test_offline_productive_rolling_linear_drift_diagnostics_v0.py",
            "config/governance/economic_diagnostic_optimization_boundary_canonical_owner_map_v0.json",
        ]
        report = build_boundary_report(changed_files, repo_root=REPO_ROOT)
        assert report.admissible is True
        assert report.impact_unknown is False
        assert "ALLOWED_OPTIMIZATION_SURFACE_ONLY" in report.reason_codes
        assert forbidden_surface_changed_count(report) == 0
        assert set(report.allowed_surface_classification) >= {
            "COST_MODEL_DIAGNOSTICS",
            "WALK_FORWARD_MONTE_CARLO_STRESS_AND_PARAMETER_SENSITIVITY",
            "REPORTING_AND_EVIDENCE_REPAIR",
        }

    def test_outlier_window_robustness_surfaces_classified(self) -> None:
        changed_files = [
            "src/research/linear_evidence/window_robustness.py",
            "scripts/research/offline_outlier_and_window_robustness_diagnostic_v0.py",
            "tests/research/test_offline_outlier_and_window_robustness_diagnostic_v0.py",
            "config/governance/economic_diagnostic_optimization_boundary_canonical_owner_map_v0.json",
        ]
        report = build_boundary_report(changed_files, repo_root=REPO_ROOT)
        assert report.admissible is True
        assert report.impact_unknown is False
        assert "ALLOWED_OPTIMIZATION_SURFACE_ONLY" in report.reason_codes
        assert forbidden_surface_changed_count(report) == 0
        assert set(report.allowed_surface_classification) >= {
            "COST_MODEL_DIAGNOSTICS",
            "WALK_FORWARD_MONTE_CARLO_STRESS_AND_PARAMETER_SENSITIVITY",
        }

    def test_mv2_engine_signal_source_binding_surfaces_classified(self) -> None:
        changed_files = [
            "src/backtest/mv2_research_wiring_v1.py",
            "src/backtest/strategy_signal_binding_v1.py",
            "tests/backtest/test_engine_signal_source_mv2_replay_binding_contract_v0.py",
            "tests/research/test_cross_sectional_lead_lag_v0_backtest_engine_mv2_replay_signal_parity_v0.py",
            "tests/research/test_cross_sectional_lead_lag_v0_research_eval_decision_parity_contract_suite_v0.py",
            "config/governance/economic_diagnostic_optimization_boundary_canonical_owner_map_v0.json",
        ]
        report = build_boundary_report(changed_files, repo_root=REPO_ROOT)
        assert report.admissible is True
        assert report.impact_unknown is False
        assert "ALLOWED_OPTIMIZATION_SURFACE_ONLY" in report.reason_codes
        assert forbidden_surface_changed_count(report) == 0
        assert set(report.allowed_surface_classification) == {
            "SIMULATED_FILL_BINDING_USING_EXISTING_CANONICAL_EXECUTION_OWNER",
        }


class TestEconomicDiagnosticOptimizationBoundaryGuardNegativeV0:
    @pytest.mark.parametrize(
        ("changed_files", "expected_flag"),
        [
            (["src/trading/master_v2/survival_assessment_v1.py"], "master_v2_changed"),
            (
                ["src/trading/master_v2/bull_bear_state_switch_scenario_binding_adapter_v0.py"],
                "bull_bear_changed",
            ),
            (["src/trading/master_v2/double_play_composition.py"], "double_play_changed"),
            (
                [
                    "src/trading/master_v2/double_play_entry_exit_policy_v0.py",
                    "src/trading/master_v2/reversal_preparation_scenario_binding_adapter_v0.py",
                ],
                "scope_entry_exit_reversal_changed",
            ),
            # capital_risk_sizing_v1.py is wiring-admitted; keep an unadmitted CAPITAL_RISK_SIZING path.
            (
                ["src/trading/master_v2/double_play_capital_slot.py"],
                "risk_sizing_changed",
            ),
            (
                [
                    "src/trading/master_v2/killswitch_boundary_backtest_state_file_binding_adapter_v0.py",
                    "src/trading/master_v2/reconciliation_boundary_backtest_state_file_binding_adapter_v0.py",
                ],
                "safety_killswitch_reconciliation_changed",
            ),
        ],
    )
    def test_negative_cases_block_forbidden_surfaces(
        self,
        changed_files: list[str],
        expected_flag: str,
    ) -> None:
        report = build_boundary_report(changed_files, repo_root=REPO_ROOT)
        assert report.admissible is False
        assert report.fail_closed is True
        assert forbidden_surface_changed_count(report) >= 1
        assert getattr(report, expected_flag) is True
        assert "FORBIDDEN_MUTATION_SURFACE_MATCH" in report.reason_codes

    def test_unknown_research_path_blocks(self) -> None:
        report = build_boundary_report(
            ["src/research/unknown_future_owner_module_v0.py"],
            repo_root=REPO_ROOT,
        )
        assert report.admissible is False
        assert report.impact_unknown is True
        assert "IMPACT_UNKNOWN_MUTATION_BLOCKED" in report.reason_codes

    def test_bouchaud_research_generation_preparation_surfaces_classified(self) -> None:
        changed_files = [
            "src/research/bouchaud_microstructure_ohlcv_proxy_v1_research_generation_preparation_v0.py",
            "scripts/research/materialize_bouchaud_microstructure_ohlcv_proxy_v1_research_generation_preparation_v0.py",
            "config/governance/economic_diagnostic_optimization_boundary_canonical_owner_map_v0.json",
        ]
        report = build_boundary_report(changed_files, repo_root=REPO_ROOT)
        assert report.admissible is True
        assert report.economic_or_diagnostic_only is True
        assert report.impact_unknown is False
        assert "ALLOWED_OPTIMIZATION_SURFACE_ONLY" in report.reason_codes
        assert forbidden_surface_changed_count(report) == 0
        assert set(report.allowed_surface_classification) >= {
            "TARGET_BINDING_REPAIR",
            "FEATURE_SCALING_OR_NUMERICAL_CONDITIONING_WITHOUT_TRADING_SEMANTIC_EFFECT",
            "DETERMINISTIC_MATERIALIZATION_REPAIR",
            "REPORTING_AND_EVIDENCE_REPAIR",
        }

    def test_no_directory_wide_research_exemption(self) -> None:
        report = build_boundary_report(
            ["src/research/unregistered_offline_diagnostic_owner_v0.py"],
            repo_root=REPO_ROOT,
        )
        assert report.admissible is False
        assert report.impact_unknown is True
        assert forbidden_surface_changed_count(report) == 0

    def test_boundary_report_serializes_required_fields(self) -> None:
        report = build_boundary_report(
            ["src/trading/master_v2/directional_assessment_v1.py"],
            repo_root=REPO_ROOT,
        )
        payload = report.to_dict()
        contract = load_contract(REPO_ROOT)
        for field in contract["boundary_report_required_fields"]:
            assert field in payload
        json.dumps(payload)


TEST_DIFF_BASE_SHA = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
_COMPOSITION_WIRING_PATH = "src/trading/master_v2/double_play_core_wiring_v1.py"
_COMPOSITION_UNGRANTED_MASTER_V2_PATH = "src/trading/master_v2/survival_assessment_v1.py"
_COMPOSITION_RESEARCH_A = "src/research/unknown_future_owner_module_v0.py"
_COMPOSITION_RESEARCH_B = "src/research/unregistered_offline_diagnostic_owner_v0.py"
_COMPOSITION_RESEARCH_C = "scripts/research/unknown_future_owner_materializer_v0.py"
_COMPOSITION_RESEARCH_D = "src/research/another_unregistered_owner_v0.py"


def _unified_diff(path: str, removed: list[str], added: list[str]) -> str:
    lines = [
        f"--- a/{path}",
        f"+++ b/{path}",
        f"@@ -1,{len(removed) or 1} +1,{len(added) or 1} @@",
    ]
    lines.extend(f"-{line}" for line in removed)
    lines.extend(f"+{line}" for line in added)
    return "\n".join(lines) + "\n"


def _decommission_shaped_diff(path: str) -> str:
    return _unified_diff(path, ['    "obsolete_noncanonical_literal"'], [])


def _wiring_behavior_diff(path: str) -> str:
    return _unified_diff(
        path,
        ['        "exchange": str(ccxt_cfg.get("exchange", "kraken")),'],
        [
            "        from src.exchange.operative_venue_boundary_v1 import assert_operative_ccxt_venue_id",
            "        exchange_id = assert_operative_ccxt_venue_id(exchange_id)",
        ],
    )


def _active_decommission_grant(
    allowed_paths: list[str],
    diffs: dict[str, str],
    *,
    surface_classes: list[str] | None = None,
) -> dict:
    auth = copy.deepcopy(load_decommission_authorization(REPO_ROOT))
    assert isinstance(auth, dict)
    auth["grant_active"] = True
    auth["allowed_paths"] = list(allowed_paths)
    auth["allowed_surface_classes"] = list(surface_classes or [])
    auth["authorized_evidence_digest"] = compute_decommission_evidence_digest(
        file_diffs=diffs,
        diff_base_sha=TEST_DIFF_BASE_SHA,
        paths=allowed_paths,
    )
    return auth


def _composed_report(
    changed: list[str],
    *,
    auth: dict | None = None,
    diffs: dict[str, str] | None = None,
    skip_decommission: bool = False,
    skip_technical_wiring: bool = False,
) -> object:
    return build_boundary_report(
        changed,
        repo_root=REPO_ROOT,
        decommission_authorization=auth,
        skip_decommission_authorization=skip_decommission,
        skip_technical_wiring_authorization=skip_technical_wiring,
        skip_owner_adjudication_authorization=True,
        skip_mapping_bind_authorization=True,
        skip_generator_fallback_authorization=True,
        skip_armed_identity_split_authorization=True,
        file_diffs=diffs,
        diff_base_sha=TEST_DIFF_BASE_SHA,
    )


class TestComposedDualAdmissionGuardV1:
    def test_case1_technical_wiring_without_unclassified_passes(self) -> None:
        report = _composed_report(
            [_COMPOSITION_WIRING_PATH],
            skip_decommission=True,
        )
        assert report.admissible is True
        assert report.fail_closed is False
        assert report.technical_wiring_authorization_applied is True
        assert report.semantics_neutral_decommission_authorization_applied is False
        assert REASON_TECHNICAL_WIRING_AUTHORIZED in report.reason_codes
        assert REASON_DECOMMISSION_AUTHORIZED not in report.reason_codes
        assert report.unclassified_touch_count == 0
        assert forbidden_surface_changed_count(report) == 0

    def test_case2_wiring_then_decommission_remaining_unclassified_passes(self) -> None:
        diffs = {_COMPOSITION_RESEARCH_A: _decommission_shaped_diff(_COMPOSITION_RESEARCH_A)}
        auth = _active_decommission_grant([_COMPOSITION_RESEARCH_A], diffs)
        report = _composed_report(
            [_COMPOSITION_WIRING_PATH, _COMPOSITION_RESEARCH_A],
            auth=auth,
            diffs=diffs,
        )
        assert report.admissible is True
        assert report.fail_closed is False
        assert report.technical_wiring_authorization_applied is True
        assert report.semantics_neutral_decommission_authorization_applied is True
        assert REASON_TECHNICAL_WIRING_AUTHORIZED in report.reason_codes
        assert REASON_DECOMMISSION_AUTHORIZED in report.reason_codes
        assert report.unclassified_touch_count == 0
        assert report.decommission_admission_count == 1

    def test_case3_wiring_with_remaining_unclassified_and_no_decommission_fails(self) -> None:
        report = _composed_report(
            [_COMPOSITION_WIRING_PATH, _COMPOSITION_RESEARCH_A],
            skip_decommission=True,
        )
        assert report.admissible is False
        assert report.fail_closed is True
        assert report.impact_unknown is True
        assert REASON_IMPACT_UNKNOWN in report.reason_codes
        assert report.technical_wiring_authorization_applied is True
        assert report.semantics_neutral_decommission_authorization_applied is False
        assert report.unclassified_touch_count == 1

    def test_case4_decommission_cannot_authorize_master_v2_wiring(self) -> None:
        diffs = {
            _COMPOSITION_UNGRANTED_MASTER_V2_PATH: _wiring_behavior_diff(
                _COMPOSITION_UNGRANTED_MASTER_V2_PATH
            )
        }
        auth = _active_decommission_grant(
            [_COMPOSITION_UNGRANTED_MASTER_V2_PATH],
            diffs,
            surface_classes=["MASTER_V2"],
        )
        report = _composed_report(
            [_COMPOSITION_UNGRANTED_MASTER_V2_PATH],
            auth=auth,
            diffs=diffs,
            skip_technical_wiring=True,
        )
        assert report.admissible is False
        assert report.fail_closed is True
        assert report.semantics_neutral_decommission_authorization_applied is False
        assert report.technical_wiring_authorization_applied is False
        assert REASON_FORBIDDEN_SURFACE in report.reason_codes
        assert (
            REASON_DECOMMISSION_SEMANTIC_CHANGE in report.reason_codes
            or REASON_DECOMMISSION_AUTHORIZED not in report.reason_codes
        )

    def test_case5_partial_technical_wiring_coverage_fails(self) -> None:
        report = _composed_report(
            [_COMPOSITION_WIRING_PATH, _COMPOSITION_UNGRANTED_MASTER_V2_PATH],
            skip_decommission=True,
        )
        assert report.admissible is False
        assert report.fail_closed is True
        assert report.technical_wiring_authorization_applied is False
        assert REASON_TECHNICAL_WIRING_UNAUTHORIZED_PATH in report.reason_codes
        assert forbidden_surface_changed_count(report) >= 1

    def test_case6_partial_decommission_coverage_of_unclassified_fails(self) -> None:
        diffs = {
            _COMPOSITION_RESEARCH_A: _decommission_shaped_diff(_COMPOSITION_RESEARCH_A),
            _COMPOSITION_RESEARCH_B: _decommission_shaped_diff(_COMPOSITION_RESEARCH_B),
        }
        auth = _active_decommission_grant([_COMPOSITION_RESEARCH_A], diffs)
        report = _composed_report(
            [_COMPOSITION_WIRING_PATH, _COMPOSITION_RESEARCH_A, _COMPOSITION_RESEARCH_B],
            auth=auth,
            diffs=diffs,
        )
        assert report.admissible is False
        assert report.fail_closed is True
        assert report.impact_unknown is True
        assert REASON_IMPACT_UNKNOWN in report.reason_codes
        assert report.technical_wiring_authorization_applied is True
        assert report.semantics_neutral_decommission_authorization_applied is False
        assert report.unclassified_touch_count == 1

    def test_case7_unknown_fourth_unclassified_path_fails(self) -> None:
        research_paths = [
            _COMPOSITION_RESEARCH_A,
            _COMPOSITION_RESEARCH_B,
            _COMPOSITION_RESEARCH_C,
        ]
        diffs = {path: _decommission_shaped_diff(path) for path in research_paths}
        auth = _active_decommission_grant(research_paths, diffs)
        report = _composed_report(
            [_COMPOSITION_WIRING_PATH, *research_paths, _COMPOSITION_RESEARCH_D],
            auth=auth,
            diffs=diffs,
        )
        assert report.admissible is False
        assert report.fail_closed is True
        assert report.impact_unknown is True
        assert REASON_IMPACT_UNKNOWN in report.reason_codes
        assert report.technical_wiring_authorization_applied is True
        assert report.semantics_neutral_decommission_authorization_applied is False
        assert report.unclassified_touch_count == 1

    def test_case8_dual_admission_preserves_both_verdict_contributions(self) -> None:
        diffs = {_COMPOSITION_RESEARCH_A: _decommission_shaped_diff(_COMPOSITION_RESEARCH_A)}
        auth = _active_decommission_grant([_COMPOSITION_RESEARCH_A], diffs)
        report = _composed_report(
            [_COMPOSITION_WIRING_PATH, _COMPOSITION_RESEARCH_A],
            auth=auth,
            diffs=diffs,
        )
        payload = report.to_dict()
        assert report.admissible is True
        assert report.technical_wiring_authorization_applied is True
        assert report.semantics_neutral_decommission_authorization_applied is True
        assert report.technical_wiring_authorization_version is not None
        assert report.semantics_neutral_decommission_authorization_version == (
            DECOMMISSION_AUTH_VERSION
        )
        assert (
            report.semantics_neutral_decommission_mutation_purpose_class
            == DECOMMISSION_MUTATION_PURPOSE
        )
        assert report.semantics_neutral_decommission_proven_predicates
        assert payload["technical_wiring_authorization_applied"] is True
        assert payload["semantics_neutral_decommission_authorization_applied"] is True
        assert REASON_TECHNICAL_WIRING_AUTHORIZED in payload["reason_codes"]
        assert REASON_DECOMMISSION_AUTHORIZED in payload["reason_codes"]
        wiring_index = payload["reason_codes"].index(REASON_TECHNICAL_WIRING_AUTHORIZED)
        decommission_index = payload["reason_codes"].index(REASON_DECOMMISSION_AUTHORIZED)
        assert wiring_index < decommission_index
        assert payload["unclassified_touch_count"] == 0
        assert payload["decommission_admission_count"] == 1

    def test_research_decommission_cannot_use_technical_wiring(self) -> None:
        report = _composed_report(
            [_COMPOSITION_RESEARCH_A],
            skip_decommission=True,
        )
        assert report.admissible is False
        assert report.technical_wiring_authorization_applied is False
        assert REASON_IMPACT_UNKNOWN in report.reason_codes
        assert REASON_TECHNICAL_WIRING_AUTHORIZED not in report.reason_codes

    def test_unknown_third_admission_class_remains_fail_closed(self) -> None:
        report = _composed_report(
            [_COMPOSITION_RESEARCH_D],
            skip_decommission=True,
            skip_technical_wiring=True,
        )
        assert report.admissible is False
        assert report.fail_closed is True
        assert report.impact_unknown is True
        assert report.technical_wiring_authorization_applied is False
        assert report.semantics_neutral_decommission_authorization_applied is False
        assert REASON_IMPACT_UNKNOWN in report.reason_codes
