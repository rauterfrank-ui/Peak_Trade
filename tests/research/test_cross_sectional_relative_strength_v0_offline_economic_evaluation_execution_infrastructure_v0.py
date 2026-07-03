"""Contract and integration tests for cross-sectional execution infrastructure v0."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from src.research.cross_sectional_panel_economic_evaluation_wiring_v0 import (
    wire_robustness_stages_v0,
)
from src.research.cross_sectional_ranking_semantics_binding_validator_v0 import (
    ValidationVerdict,
    validate_cross_sectional_ranking_semantics_binding_v0,
)
from src.research.cross_sectional_relative_strength_v0_bound_panel_dataset_materialization_v0 import (
    MaterializationTerminalStatus,
    compute_bound_panel_data_digest_v0,
    materialize_bound_panel_dataset_v0,
    verify_panel_covers_period_binding_v0,
)
from src.research.cross_sectional_relative_strength_v0_offline_economic_evaluation_execution_v0 import (
    AUTHORITY_EFFECT,
    INFRASTRUCTURE_GO_TOKEN,
    RUNTIME_EFFECT,
    load_ops_evaluation_config_v0,
    materialize_infrastructure_summary_v0,
    run_contract_smoke_evaluation_v0,
    verify_execution_start_state_v0,
    verify_foreign_dataset_rejected_v0,
)
from src.research.cross_sectional_relative_strength_v0_offline_economic_evaluation_scope_ratification_v0 import (
    materialize_cross_sectional_offline_economic_evaluation_scope_ratification_v0,
)
from src.research.cross_sectional_relative_strength_v0_versioned_research_binding_v0 import (
    materialize_and_validate_versioned_research_binding_v0,
    materialize_versioned_research_binding_v0,
)
from src.research.cross_sectional_single_slot_backtest_wiring_v0 import (
    MAX_POSITIONS,
    run_single_slot_panel_backtest_v0,
)
from src.research.cross_sectional_single_slot_research_orchestrator_v0 import (
    default_operator_binding_v0,
    run_cross_sectional_single_slot_orchestrator_v0,
)
from tests.research.fixtures.cross_sectional_relative_strength_v0.fixture_builder import (
    build_synthetic_panel_series_v0,
)
from tests.research.fixtures.cross_sectional_relative_strength_v0.staging_builder import (
    write_bound_period_staging_v0,
    write_foreign_2026_staging_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
ARCHIVE_ROOT = Path("/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z")
FOREIGN_DATASET_ROOT = (
    ARCHIVE_ROOT / "datasets/admissible_futures/pit_okx_linear_usdt_non_bitcoin_pt1h_panel/v1"
)


@pytest.fixture(name="complete_binding")
def fixture_complete_binding() -> dict:
    return materialize_versioned_research_binding_v0()


@pytest.fixture(name="scope_ratification")
def fixture_scope_ratification(complete_binding: dict) -> dict:
    return materialize_cross_sectional_offline_economic_evaluation_scope_ratification_v0(
        repo_root=REPO_ROOT,
        versioned_binding=complete_binding,
    )


@pytest.fixture(name="bound_staging")
def fixture_bound_staging() -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="cs_rs_bound_staging_"))
    return write_bound_period_staging_v0(tmp)


def test_infrastructure_go_token_constant() -> None:
    assert (
        INFRASTRUCTURE_GO_TOKEN
        == "GO_BOUNDED_CROSS_SECTIONAL_RELATIVE_STRENGTH_V0_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_INFRASTRUCTURE_COMPLETION_V0"
    )


def test_no_runtime_authority_effect_constants() -> None:
    assert AUTHORITY_EFFECT == "NONE"
    assert RUNTIME_EFFECT == "NONE"


def test_binding_materialization_complete_accepted() -> None:
    result = materialize_and_validate_versioned_research_binding_v0()
    assert result.validation_verdict == ValidationVerdict.ACCEPTED_COMPLETE


def test_futures_only_and_bitcoin_exclusion(complete_binding: dict) -> None:
    constraints = complete_binding["system_constraints"]
    assert constraints["futures_only"] is True
    assert constraints["bitcoin_direction_allowed"] is False


def test_missing_binding_fail_closed() -> None:
    binding = default_operator_binding_v0()
    binding["numeric_bindings"].pop("lookback_N")
    with pytest.raises(ValueError):
        run_cross_sectional_single_slot_orchestrator_v0(
            binding=binding,
            panel_series=build_synthetic_panel_series_v0(),
        )


def test_foreign_2026_dataset_rejected(bound_staging: Path, complete_binding: dict) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        foreign = write_foreign_2026_staging_v0(Path(tmp))
        result = materialize_bound_panel_dataset_v0(
            foreign,
            period_binding=complete_binding["period_binding"],
        )
        assert result.status is MaterializationTerminalStatus.BOUND_DATA_UNAVAILABLE_FAIL_CLOSED


def test_archive_2026_panel_rejected_if_present(complete_binding: dict) -> None:
    if not FOREIGN_DATASET_ROOT.is_dir():
        pytest.skip("foreign dataset archive not present")
    rejected, _ = verify_foreign_dataset_rejected_v0(
        FOREIGN_DATASET_ROOT,
        period_binding=complete_binding["period_binding"],
    )
    assert rejected is True


def test_bound_staging_materialization_deterministic_digest(
    bound_staging: Path,
    complete_binding: dict,
) -> None:
    first = materialize_bound_panel_dataset_v0(
        bound_staging,
        period_binding=complete_binding["period_binding"],
    )
    second = materialize_bound_panel_dataset_v0(
        bound_staging,
        period_binding=complete_binding["period_binding"],
    )
    assert first.status is MaterializationTerminalStatus.DATASET_MATERIALIZATION_COMPLETE
    assert first.panel_data_digest == second.panel_data_digest
    assert first.idempotent_digest_stable is True


def test_period_coverage_validation(bound_staging: Path, complete_binding: dict) -> None:
    from src.research.pit_futures_cross_sectional_research_data_digest_period_split_materialization_v0 import (
        load_panel_series_from_staging,
    )

    panel_series, _ = load_panel_series_from_staging(bound_staging)
    ok, reasons = verify_panel_covers_period_binding_v0(
        panel_series,
        period_binding=complete_binding["period_binding"],
    )
    assert ok is True
    assert reasons == ()


def test_panel_wiring_uses_stats_owner(complete_binding: dict) -> None:
    panel = build_synthetic_panel_series_v0()
    orch = run_cross_sectional_single_slot_orchestrator_v0(
        binding=default_operator_binding_v0(),
        panel_series=panel,
    )
    backtest = run_single_slot_panel_backtest_v0(
        orch,
        panel,
        cost_execution_binding=complete_binding["cost_execution_binding"],
    )
    assert "total_return" in backtest.stats
    assert backtest.roundtrip_cost_bps > 0
    assert MAX_POSITIONS == 1


def test_no_implicit_zero_cost(complete_binding: dict) -> None:
    cost = complete_binding["cost_execution_binding"]
    assert cost["fee_model_binding"]["fee_bps_per_side"] > 0
    assert cost["slippage_model_binding"]["slippage_bps_per_side"] > 0
    assert cost["execution_model_binding"]["roundtrip_cost_bps"] > 0


def test_parameter_search_forbidden(complete_binding: dict) -> None:
    assert complete_binding["parameter_binding"]["parameter_search_forbidden"] is True


def test_walk_forward_period_split_no_leakage(complete_binding: dict) -> None:
    panel = build_synthetic_panel_series_v0()
    orch = run_cross_sectional_single_slot_orchestrator_v0(
        binding=default_operator_binding_v0(),
        panel_series=panel,
    )
    backtest = run_single_slot_panel_backtest_v0(
        orch,
        panel,
        cost_execution_binding=complete_binding["cost_execution_binding"],
    )
    robustness = wire_robustness_stages_v0(
        backtest,
        period_binding=complete_binding["period_binding"],
        economic_policy_binding=complete_binding["economic_policy_binding"],
    )
    names = [item.period_name for item in robustness.walk_forward_results]
    assert names == ["training", "validation", "out_of_sample"]


def test_monte_carlo_and_stress_invoke_existing_owners(complete_binding: dict) -> None:
    panel = build_synthetic_panel_series_v0()
    orch = run_cross_sectional_single_slot_orchestrator_v0(
        binding=default_operator_binding_v0(),
        panel_series=panel,
    )
    backtest = run_single_slot_panel_backtest_v0(
        orch,
        panel,
        cost_execution_binding=complete_binding["cost_execution_binding"],
    )
    robustness = wire_robustness_stages_v0(
        backtest,
        period_binding=complete_binding["period_binding"],
        economic_policy_binding=complete_binding["economic_policy_binding"],
    )
    assert robustness.monte_carlo_summary["runs"] == 64
    assert robustness.stress_results["baseline_metrics"] is not None


def test_ops_config_loads(complete_binding: dict) -> None:
    cfg = load_ops_evaluation_config_v0(REPO_ROOT)
    assert cfg["strategy_id"] == "cross_sectional_relative_strength"
    assert cfg["binding_digest"] == complete_binding["binding_digest"]


def test_start_state_verification_accepts_ratified_binding(
    scope_ratification: dict,
    complete_binding: dict,
) -> None:
    result = verify_execution_start_state_v0(
        repo_root=REPO_ROOT,
        ratification=scope_ratification,
        versioned_binding=complete_binding,
    )
    assert result.valid is True
    assert result.fail_reasons == ()


def test_contract_smoke_evaluation_produces_wiring_outputs(
    bound_staging: Path,
    complete_binding: dict,
) -> None:
    panel = build_synthetic_panel_series_v0()
    readiness = run_contract_smoke_evaluation_v0(
        panel_series=panel,
        versioned_binding=complete_binding,
        staging_root=bound_staging,
    )
    assert readiness.execution_infrastructure_complete is True
    assert readiness.panel_wiring_complete is True
    assert readiness.bound_dataset_materialized is True
    assert readiness.economic_evaluation_executed is False
    assert readiness.smoke_trade_count is not None


def test_infrastructure_summary_flags_no_economic_evaluation(
    scope_ratification: dict,
    complete_binding: dict,
    bound_staging: Path,
) -> None:
    panel = build_synthetic_panel_series_v0()
    readiness = run_contract_smoke_evaluation_v0(
        panel_series=panel,
        versioned_binding=complete_binding,
        staging_root=bound_staging,
    )
    summary = materialize_infrastructure_summary_v0(
        ratification=scope_ratification,
        readiness=readiness,
        origin_main_sha="ce59011e1ba5057ad4cfc53b6c7bb115456f67cd",
        execution_bundle_dir="/tmp/cs_rs_infra",
    )
    assert summary["economic_evaluation_executed"] is False
    assert summary["economic_classification"] == "NONE"


def test_execution_path_has_no_runtime_imports() -> None:
    modules = [
        "src.research.cross_sectional_relative_strength_v0_offline_economic_evaluation_execution_v0",
        "src.research.cross_sectional_single_slot_backtest_wiring_v0",
        "src.research.cross_sectional_panel_economic_evaluation_wiring_v0",
    ]
    forbidden = ("src.execution", "src.governance.live", "src.scheduler")
    for module_name in modules:
        module = __import__(module_name, fromlist=["__doc__"])
        source = Path(module.__file__).read_text(encoding="utf-8")
        for token in forbidden:
            assert token not in source


def test_digest_helper_stable_on_fixture_panel() -> None:
    panel = build_synthetic_panel_series_v0()
    first = compute_bound_panel_data_digest_v0(panel)
    second = compute_bound_panel_data_digest_v0(panel)
    assert first == second
    assert len(first) == 64
