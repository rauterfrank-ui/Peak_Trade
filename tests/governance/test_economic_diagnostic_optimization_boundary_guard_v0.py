"""Guard tests for economic/diagnostic optimization boundary v0."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.governance.economic_diagnostic_optimization_boundary_v0 import (
    CONTRACT_VERSION,
    PACKAGE_MARKER,
    build_boundary_report,
    export_canonical_owner_inventory,
    forbidden_surface_changed_count,
    load_contract,
    load_owner_map,
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


class TestEconomicDiagnosticOptimizationBoundaryGuardNegativeV0:
    @pytest.mark.parametrize(
        ("changed_files", "expected_flag"),
        [
            (["src/trading/master_v2/double_play_state.py"], "master_v2_changed"),
            (["src/trading/master_v2/directional_assessment_v1.py"], "bull_bear_changed"),
            (["src/trading/master_v2/double_play_composition.py"], "double_play_changed"),
            (
                [
                    "src/trading/master_v2/double_play_entry_exit_policy_v0.py",
                    "src/trading/master_v2/reversal_preparation_scenario_binding_adapter_v0.py",
                ],
                "scope_entry_exit_reversal_changed",
            ),
            (["src/governance/capital_risk_sizing_v1.py"], "risk_sizing_changed"),
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
            ["src/trading/master_v2/double_play_state.py"],
            repo_root=REPO_ROOT,
        )
        payload = report.to_dict()
        contract = load_contract(REPO_ROOT)
        for field in contract["boundary_report_required_fields"]:
            assert field in payload
        json.dumps(payload)
