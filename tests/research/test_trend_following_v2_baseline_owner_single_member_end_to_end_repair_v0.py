"""Single-member end-to-end repair contract for trend_following v2 baseline owner failure."""

from __future__ import annotations

import json
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pandas as pd
import pytest

from src.backtest import admissible_versioned_futures_dataset_v1 as ds
from src.backtest.economic_viability_evidence_v1 import (
    ARTIFACT_FILENAME,
    load_economic_viability_evidence_bundle_v1,
)
from src.backtest.parameter_sensitivity_v1 import (
    EvaluationStatus,
    MetricValueStatus,
    ParameterSensitivityGridV1,
    ParameterSensitivityPointV1,
    ParameterSensitivityResultV1,
    PipelineStatus,
)
from src.experiments.monte_carlo import MonteCarloSummaryResult
from src.governance.economic_diagnostic_optimization_boundary_v0 import build_boundary_report
from src.research.final_research_fleet_offline_economic_evaluation_execution_v0 import (
    REASON_CANDIDATE_RUN_FAILED,
)
from src.research.panel_sequential_signal_density_research_adapter_v0 import (
    _materialize_research_panel_volatility_estimate_columns_v0,
    materialize_panel_member_evaluation_dataset_v0,
    resolve_panel_staging_root,
)
from src.research.trend_following_v2_offline_economic_evaluation_authorization_ratification_v0 import (
    materialize_offline_economic_evaluation_authorization_ratification_v0,
)
from src.research.trend_following_v2_offline_economic_evaluation_execution_v0 import (
    BASELINE_EXECUTION_GO_TOKEN,
    CANONICAL_BASELINE_BACKTEST_OWNER,
    CANONICAL_BASELINE_ENTRY_POINT,
    REASON_BASELINE_OWNER_RUN_FAILED,
)
from src.research.trend_following_v2_versioned_research_binding_v0 import (
    materialize_versioned_research_binding_v0,
)
from src.research.versioned_final_fleet_bindings_offline_economic_evaluation_v0 import (
    _run_candidate_with_runtime_config_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
STAGING_ROOT = resolve_panel_staging_root()
RVN_PANEL_MEMBER_ID = "okx:linear_perpetual:RVN:USDT:USDT:perp"
TARGET_SINGLE_TEST_MAX_SECONDS = 10.0
TARGET_FILE_MAX_SECONDS = 20.0
BOUNDED_TEST_MARKER = "BOUNDED_ECONOMIC_ROBUSTNESS_STAGES_SKIPPED=true"
BOUNDED_PRIMARY_BACKTEST_BAR_LIMIT = 240


def _bounded_parameter_sensitivity_result_v0() -> ParameterSensitivityResultV1:
    grid = ParameterSensitivityGridV1(
        grid_id="bounded_test_grid_v0",
        grid_version="v0",
        strategy_id="trend_following",
        strategy_version="v2",
        canonical_trading_logic_version="bounded_test_v0",
        parameter_names=("fee_bps",),
        parameter_values=((10.0,),),
        combination_count=1,
        search_space_bounds={"fee_bps": {"min": 10.0, "max": 10.0}},
        seed=42,
        train_period="bounded_train",
        validation_period="bounded_validation",
        out_of_sample_period="bounded_oos",
        config_digest="bounded_config_digest",
        implementation_digest="bounded_implementation_digest",
        data_digest_or_explicit_missing="bounded_data_digest",
        grid_digest="bounded_grid_digest",
    )
    point = ParameterSensitivityPointV1(
        parameter_set_id="bounded_point_v0",
        parameter_values={"fee_bps": 10.0},
        evaluation_status=EvaluationStatus.EVALUATED,
        reason_codes=(),
        train_result_ref="bounded_train_ref",
        validation_result_ref="bounded_validation_ref",
        out_of_sample_result_ref="bounded_oos_ref",
        net_return=MetricValueStatus.COMPUTED,
        net_return_value=0.0,
        net_expectancy=MetricValueStatus.COMPUTED,
        net_expectancy_value=0.0,
        profit_factor=MetricValueStatus.COMPUTED,
        profit_factor_value=0.0,
        max_drawdown=MetricValueStatus.COMPUTED,
        max_drawdown_value=0.0,
        trade_count=MetricValueStatus.COMPUTED,
        trade_count_value=0.0,
        walk_forward_status="BOUNDED_NOT_RUN",
        monte_carlo_status="BOUNDED_NOT_RUN",
        stress_status="BOUNDED_NOT_RUN",
        cost_model_ref="bounded_cost_model_ref",
        funding_model_ref="bounded_funding_model_ref",
        config_digest="bounded_config_digest",
        implementation_digest="bounded_implementation_digest",
        data_digest="bounded_data_digest",
        result_digest="bounded_result_digest",
    )
    return ParameterSensitivityResultV1(
        contract_version="parameter_sensitivity.v1",
        owner="backtest.parameter_sensitivity_v1",
        pipeline_status=PipelineStatus.PIPELINE_PASS,
        parameter_robustness_policy_pass=True,
        parameter_robustness_policy_status="PASS",
        grid=grid,
        grid_digest=grid.grid_digest,
        result_digest="bounded_result_digest",
        combination_count=1,
        points=(point,),
        failed_point_count=0,
        blocked_point_count=0,
        seed=42,
        reason_codes=("bounded_test_fixture",),
        parameter_neighbor_degradation=0.0,
    )


@contextmanager
def bounded_economic_robustness_stage_patches_v0() -> Iterator[dict[str, Any]]:
    """Skip deep WF/MC/stress/sensitivity while preserving primary MV2 backtest wiring."""
    import src.backtest.economic_viability_evidence_v1 as ev_module

    original_build = ev_module.build_economic_viability_evidence_v1
    original_wiring = ev_module.mv2_wiring.run_mv2_research_backtest_wiring_v1
    stage_state = {
        BOUNDED_TEST_MARKER: True,
        "walk_forward_calls": 0,
        "monte_carlo_calls": 0,
        "parameter_sensitivity_calls": 0,
        "primary_backtest_preserved": True,
        "primary_backtest_bar_limit": BOUNDED_PRIMARY_BACKTEST_BAR_LIMIT,
    }

    def _bounded_primary_wiring(*args: Any, **kwargs: Any) -> Any:
        bars = kwargs.get("bars")
        if bars is None and args:
            bars = args[0]
        if isinstance(bars, pd.DataFrame) and len(bars) > BOUNDED_PRIMARY_BACKTEST_BAR_LIMIT:
            bounded_bars = bars.tail(BOUNDED_PRIMARY_BACKTEST_BAR_LIMIT)
            if "bars" in kwargs:
                kwargs = dict(kwargs)
                kwargs["bars"] = bounded_bars
                return original_wiring(*args, **kwargs)
            return original_wiring(bounded_bars, *args[1:], **kwargs)
        return original_wiring(*args, **kwargs)

    def _bounded_build(*, bars: pd.DataFrame, **kwargs: Any) -> Any:
        bounded_kwargs = dict(kwargs)
        bounded_kwargs["monte_carlo_runs"] = 0
        bounded_kwargs["walk_forward_train_bars"] = len(bars) + 1000
        bounded_kwargs["walk_forward_test_bars"] = 1
        bounded_kwargs["walk_forward_step_bars"] = 1
        return original_build(bars=bars, **bounded_kwargs)

    def _forbidden_walk_forward(*args: Any, **kwargs: Any) -> Any:
        stage_state["walk_forward_calls"] += 1
        raise AssertionError("walk_forward_must_not_run_in_bounded_test")

    def _forbidden_monte_carlo(*args: Any, **kwargs: Any) -> MonteCarloSummaryResult:
        stage_state["monte_carlo_calls"] += 1
        raise AssertionError("monte_carlo_must_not_run_in_bounded_test")

    def _bounded_parameter_sensitivity(**_kwargs: Any) -> ParameterSensitivityResultV1:
        stage_state["parameter_sensitivity_calls"] += 1
        return _bounded_parameter_sensitivity_result_v0()

    with (
        patch.object(
            ev_module,
            "build_economic_viability_evidence_v1",
            side_effect=_bounded_build,
        ),
        patch.object(
            ev_module.mv2_wiring,
            "run_mv2_research_backtest_wiring_v1",
            side_effect=_bounded_primary_wiring,
        ),
        patch.object(
            ev_module.mv2_wiring,
            "run_mv2_walk_forward_wiring_v1",
            side_effect=_forbidden_walk_forward,
        ),
        patch.object(
            ev_module.mv2_wiring,
            "bind_monte_carlo_analysis_v1",
            side_effect=_forbidden_monte_carlo,
        ),
        patch.object(
            ev_module,
            "run_parameter_sensitivity_v1",
            side_effect=_bounded_parameter_sensitivity,
        ),
    ):
        yield stage_state


@pytest.fixture(name="complete_binding")
def fixture_complete_binding() -> dict:
    return materialize_versioned_research_binding_v0(repo_root=REPO_ROOT)


@pytest.fixture(name="authorization_ratification")
def fixture_authorization_ratification(complete_binding: dict) -> dict:
    return materialize_offline_economic_evaluation_authorization_ratification_v0(
        repo_root=REPO_ROOT,
        versioned_binding=complete_binding,
    )


@pytest.mark.skipif(not STAGING_ROOT.is_dir(), reason="panel staging root unavailable")
class TestPreFixRootCauseContract:
    def test_panel_bars_without_volatility_estimate_fail_admissibility(
        self, tmp_path: Path
    ) -> None:
        narrow = materialize_panel_member_evaluation_dataset_v0(
            staging_root=STAGING_ROOT,
            instrument_id=RVN_PANEL_MEMBER_ID,
            output_root=tmp_path / "member",
        )
        frame = pd.read_parquet(narrow.bars_path)
        frame_without_vol = frame.drop(
            columns=[
                "volatility_estimate",
                "warmup_status",
                "volatility_estimate_contract_version",
            ]
        )
        manifest = json.loads(narrow.manifest_path.read_text(encoding="utf-8"))
        descriptor, provenance = (
            ds.load_dataset_admissibility_from_flat_economic_research_manifest_v1(
                manifest,
                manifest_path=str(narrow.manifest_path),
            )
        )
        profile_binding = ds.load_profile_binding_from_manifest(manifest)
        result = ds.evaluate_admissible_versioned_futures_dataset_v1(
            bars=frame_without_vol,
            descriptor=descriptor,
            provenance=provenance,
            instrument_id=manifest["instrument_id"],
            profile_binding=profile_binding,
        )
        assert result.admissibility_status is ds.AdmissibilityStatus.BLOCKED_REQUIRED_FIELD_MISSING
        assert "field_binding_column_missing:volatility_estimate" in result.reason_codes

    def test_volatility_materializer_restores_admissibility(self, tmp_path: Path) -> None:
        narrow = materialize_panel_member_evaluation_dataset_v0(
            staging_root=STAGING_ROOT,
            instrument_id=RVN_PANEL_MEMBER_ID,
            output_root=tmp_path / "member_vol",
        )
        frame = pd.read_parquet(narrow.bars_path)
        repaired = _materialize_research_panel_volatility_estimate_columns_v0(
            frame.drop(
                columns=[
                    "volatility_estimate",
                    "warmup_status",
                    "volatility_estimate_contract_version",
                ]
            )
        )
        assert "volatility_estimate" in repaired.columns
        manifest = json.loads(narrow.manifest_path.read_text(encoding="utf-8"))
        assert manifest["integrity_results"]["dataset_admissible"] is True


@pytest.mark.skipif(not STAGING_ROOT.is_dir(), reason="panel staging root unavailable")
class TestSingleMemberBaselineEndToEndRepair:
    def test_production_entry_point_single_member_zero_trade_result(
        self,
        authorization_ratification: dict,
        complete_binding: dict,
        tmp_path: Path,
    ) -> None:
        import src.research.trend_following_v2_offline_economic_evaluation_execution_v0 as harness

        real_owner = harness._run_candidate_with_runtime_config_v0
        with (
            bounded_economic_robustness_stage_patches_v0() as stage_state,
            patch.object(
                harness,
                "_run_candidate_with_runtime_config_v0",
                wraps=real_owner,
            ) as owner_spy,
        ):
            started = time.time()
            result = harness.run_baseline_offline_economic_evaluation_v0(
                go_token=BASELINE_EXECUTION_GO_TOKEN,
                repo_root=REPO_ROOT,
                authorization_ratification=authorization_ratification,
                versioned_binding=complete_binding,
                staging_root=STAGING_ROOT,
                scratch_root=tmp_path / "baseline_scratch",
                invoke_baseline_owner=True,
                panel_member_instrument_ids=(RVN_PANEL_MEMBER_ID,),
                skip_member_trade_count_backtest_v0=True,
            )
            elapsed = time.time() - started

        assert elapsed <= TARGET_SINGLE_TEST_MAX_SECONDS
        assert owner_spy.call_count == 1
        assert stage_state[BOUNDED_TEST_MARKER] is True
        assert stage_state["walk_forward_calls"] == 0
        assert stage_state["monte_carlo_calls"] == 0
        assert stage_state["parameter_sensitivity_calls"] >= 1
        assert result.baseline_backtest_owner_call_count == 1
        assert result.baseline_backtest_owner_invoked is True
        assert REASON_BASELINE_OWNER_RUN_FAILED not in result.reason_codes
        assert REASON_CANDIDATE_RUN_FAILED not in result.reason_codes
        assert result.backtest_engine_completed is True
        assert result.economic_evaluation_executed is True
        assert result.economic_evidence_persisted is True

        output_dir = tmp_path / "baseline_scratch" / "baseline_candidate_output"
        loaded = load_economic_viability_evidence_bundle_v1(output_dir)
        evidence = loaded.evidence
        assert (output_dir / ARTIFACT_FILENAME).is_file()
        assert evidence.trade_count.value == 0.0
        assert evidence.gross_return.value == 0.0
        assert evidence.net_return.value == 0.0
        assert evidence.max_drawdown.value == 0.0
        assert evidence.policy_threshold_status == "PASS"
        assert evidence.status.value in {"RESEARCH_ONLY", "PASS", "FAIL"}

    def test_wrong_runner_decoy_patch_does_not_replace_consumer_build(self) -> None:
        import scripts.ops.run_economic_viability_evidence_evaluation_v1 as runner
        import src.backtest.economic_viability_evidence_v1 as ev_module

        original = ev_module.build_economic_viability_evidence_v1

        def decoy_build(**_kwargs: Any) -> Any:
            raise AssertionError("runner_decoy_patch_must_not_replace_consumer_build")

        with patch.object(runner, "build_economic_viability_evidence_v1", decoy_build, create=True):
            with bounded_economic_robustness_stage_patches_v0():
                assert ev_module.build_economic_viability_evidence_v1 is not original
                assert ev_module.build_economic_viability_evidence_v1 is not decoy_build

    def test_owner_failure_provenance_captured_on_dataset_not_admissible(
        self,
        tmp_path: Path,
    ) -> None:
        from src.research.panel_sequential_signal_density_research_adapter_v0 import (
            build_sparse_signal_runtime_step31f_config_v0,
        )
        from src.research.trend_following_v2_versioned_research_binding_v0 import (
            STRATEGY_ID,
            STRATEGY_VERSION,
        )

        member_root = tmp_path / "broken_member"
        narrow = materialize_panel_member_evaluation_dataset_v0(
            staging_root=STAGING_ROOT,
            instrument_id=RVN_PANEL_MEMBER_ID,
            output_root=member_root,
        )
        _ = narrow
        config_path = build_sparse_signal_runtime_step31f_config_v0(
            repo_root=REPO_ROOT,
            strategy_id=STRATEGY_ID,
            staging_root=STAGING_ROOT,
            instrument_id=RVN_PANEL_MEMBER_ID,
            output_path=tmp_path / "broken_config.json",
        )
        binding = json.loads(config_path.read_text(encoding="utf-8"))[
            "real_admissible_futures_evaluation_binding_v1"
        ]
        broken_bars = pd.read_parquet(binding["dataset_path"]).drop(columns=["volatility_estimate"])
        broken_bars.to_parquet(binding["dataset_path"])
        output_dir = tmp_path / "broken_output"
        candidate = _run_candidate_with_runtime_config_v0(
            repo_root=REPO_ROOT,
            strategy_id=STRATEGY_ID,
            strategy_version=STRATEGY_VERSION,
            config_path=config_path,
            output_dir=output_dir,
        )
        assert candidate.runner_execution_success is False
        assert candidate.failure_provenance is not None
        assert candidate.failure_provenance["traceback_captured"] is True
        assert candidate.failure_provenance["exception_type"] in {
            "RunnerError",
            "ValueError",
        }
        assert "dataset_not_admissible" in candidate.failure_provenance["exception_message"]


class TestRepairScopeBoundaryGuard:
    def test_governance_boundary_guard_accepts_repair_scope(self) -> None:
        changed_files = [
            "config/governance/economic_diagnostic_optimization_boundary_canonical_owner_map_v0.json",
            "src/research/panel_sequential_signal_density_research_adapter_v0.py",
            "src/research/versioned_final_fleet_bindings_offline_economic_evaluation_v0.py",
            "src/research/final_research_fleet_offline_economic_evaluation_execution_v0.py",
            "src/research/trend_following_v2_offline_economic_evaluation_execution_v0.py",
            "tests/research/test_trend_following_v2_baseline_owner_single_member_end_to_end_repair_v0.py",
        ]
        report = build_boundary_report(changed_files, repo_root=REPO_ROOT)
        assert report.admissible is True
        assert report.impact_unknown is False

    def test_production_entry_and_backtest_owner_constants(self) -> None:
        assert CANONICAL_BASELINE_ENTRY_POINT.endswith(
            "run_baseline_offline_economic_evaluation_v0"
        )
        assert CANONICAL_BASELINE_BACKTEST_OWNER.endswith("_run_candidate_with_runtime_config_v0")
