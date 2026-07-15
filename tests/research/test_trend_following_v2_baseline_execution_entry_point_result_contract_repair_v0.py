"""Contract repair tests for trend_following v2 baseline entry-point result semantics."""

from __future__ import annotations

import inspect
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.backtest.economic_viability_evidence_v1 import ARTIFACT_FILENAME
from src.research.final_research_fleet_offline_economic_evaluation_execution_v0 import (
    CandidateExecutionResultV0,
    CandidateTerminalStatus,
    REASON_CANDIDATE_RUN_FAILED,
)
from src.research.trend_following_v2_offline_economic_evaluation_authorization_ratification_v0 import (
    materialize_offline_economic_evaluation_authorization_ratification_v0,
)
from src.research.trend_following_v2_offline_economic_evaluation_execution_v0 import (
    BASELINE_EXECUTION_GO_TOKEN,
    REASON_BASELINE_BACKTEST_OWNER_INVOKED,
    REASON_BASELINE_CALLABLE_WIRING_ONLY_ACKNOWLEDGED,
    REASON_BASELINE_CANONICAL_EVIDENCE_MISSING,
    REASON_BASELINE_ECONOMIC_EVALUATION_COMPLETE,
    REASON_BASELINE_OWNER_RUN_FAILED,
    REASON_BASELINE_WIRING_VERIFIED,
    run_baseline_offline_economic_evaluation_v0,
)
from src.research.trend_following_v2_versioned_research_binding_v0 import (
    STRATEGY_ID,
    STRATEGY_VERSION,
    materialize_versioned_research_binding_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
STAGING_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "datasets/admissible_futures/pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_v1/"
    "extended_chronological_v1"
)


@pytest.fixture(name="complete_binding")
def fixture_complete_binding() -> dict:
    return materialize_versioned_research_binding_v0(repo_root=REPO_ROOT)


@pytest.fixture(name="authorization_ratification")
def fixture_authorization_ratification(complete_binding: dict) -> dict:
    return materialize_offline_economic_evaluation_authorization_ratification_v0(
        repo_root=REPO_ROOT,
        versioned_binding=complete_binding,
    )


def _failed_candidate_result(*, config_path: Path, output_dir: Path) -> CandidateExecutionResultV0:
    return CandidateExecutionResultV0(
        strategy_id=STRATEGY_ID,
        strategy_version=STRATEGY_VERSION,
        canonical_candidate_identifier="trend_following/v2",
        config_path=str(config_path),
        output_dir=str(output_dir),
        run_id="",
        terminal_status=CandidateTerminalStatus.INCONCLUSIVE,
        economic_validity_result="BLOCKED",
        economic_validity_offline_gate_pass=False,
        evidence_status="",
        manifest_verify_rc=1,
        reason_codes=(REASON_CANDIDATE_RUN_FAILED,),
        stage_return_codes={"economic_viability_runner": 1},
        runner_execution_success=False,
    )


def _successful_candidate_result(
    *, config_path: Path, output_dir: Path
) -> CandidateExecutionResultV0:
    return CandidateExecutionResultV0(
        strategy_id=STRATEGY_ID,
        strategy_version=STRATEGY_VERSION,
        canonical_candidate_identifier="trend_following/v2",
        config_path=str(config_path),
        output_dir=str(output_dir),
        run_id="test-run",
        terminal_status=CandidateTerminalStatus.INCONCLUSIVE,
        economic_validity_result="BLOCKED",
        economic_validity_offline_gate_pass=False,
        evidence_status="RESEARCH_ONLY",
        manifest_verify_rc=0,
        reason_codes=(),
        stage_return_codes={"economic_viability_runner": 0},
        runner_execution_success=True,
    )


class TestOutputDirectoryLifecycleContract:
    def test_production_source_does_not_pre_create_baseline_output_dir(self) -> None:
        source = inspect.getsource(run_baseline_offline_economic_evaluation_v0)
        assert "baseline_candidate_output" in source
        assert "output_dir.mkdir" not in source

    def test_output_dir_does_not_exist_before_owner_call(
        self,
        authorization_ratification: dict,
        complete_binding: dict,
        tmp_path: Path,
    ) -> None:
        metrics = MagicMock(evaluation_instrument_id="okx:linear_perpetual:ETH:USDT:USDT:perp")
        config_path = tmp_path / "step31f_trend_following_v2_economic_evaluation_v1.json"
        config_path.write_text("{}", encoding="utf-8")
        observed_exists: list[bool] = []

        def owner_side_effect(**kwargs: object) -> CandidateExecutionResultV0:
            observed_exists.append(Path(str(kwargs["output_dir"])).exists())
            return _failed_candidate_result(
                config_path=config_path,
                output_dir=Path(str(kwargs["output_dir"])),
            )

        with (
            patch(
                "src.research.trend_following_v2_offline_economic_evaluation_execution_v0."
                "compute_sparse_signal_density_metrics_v0",
                return_value=metrics,
            ),
            patch(
                "src.research.trend_following_v2_offline_economic_evaluation_execution_v0."
                "build_sparse_signal_runtime_step31f_config_v0",
                return_value=config_path,
            ),
            patch(
                "src.research.trend_following_v2_offline_economic_evaluation_execution_v0."
                "_run_candidate_with_runtime_config_v0",
                side_effect=owner_side_effect,
            ) as owner_spy,
        ):
            result = run_baseline_offline_economic_evaluation_v0(
                go_token=BASELINE_EXECUTION_GO_TOKEN,
                repo_root=REPO_ROOT,
                authorization_ratification=authorization_ratification,
                versioned_binding=complete_binding,
                staging_root=STAGING_ROOT,
                scratch_root=tmp_path,
                invoke_baseline_owner=True,
            )

        owner_spy.assert_called_once()
        assert observed_exists == [False]
        assert result.blocked is True
        assert result.economic_evaluation_executed is False


class TestOwnerReturnContract:
    def test_failed_owner_return_is_fail_closed(
        self,
        authorization_ratification: dict,
        complete_binding: dict,
        tmp_path: Path,
    ) -> None:
        metrics = MagicMock(evaluation_instrument_id="okx:linear_perpetual:ETH:USDT:USDT:perp")
        config_path = tmp_path / "step31f_trend_following_v2_economic_evaluation_v1.json"
        config_path.write_text("{}", encoding="utf-8")
        output_dir = tmp_path / "baseline_candidate_output"

        with (
            patch(
                "src.research.trend_following_v2_offline_economic_evaluation_execution_v0."
                "compute_sparse_signal_density_metrics_v0",
                return_value=metrics,
            ),
            patch(
                "src.research.trend_following_v2_offline_economic_evaluation_execution_v0."
                "build_sparse_signal_runtime_step31f_config_v0",
                return_value=config_path,
            ),
            patch(
                "src.research.trend_following_v2_offline_economic_evaluation_execution_v0."
                "_run_candidate_with_runtime_config_v0",
                return_value=_failed_candidate_result(
                    config_path=config_path, output_dir=output_dir
                ),
            ) as owner_spy,
        ):
            result = run_baseline_offline_economic_evaluation_v0(
                go_token=BASELINE_EXECUTION_GO_TOKEN,
                repo_root=REPO_ROOT,
                authorization_ratification=authorization_ratification,
                versioned_binding=complete_binding,
                staging_root=STAGING_ROOT,
                scratch_root=tmp_path,
                invoke_baseline_owner=True,
            )

        owner_spy.assert_called_once()
        assert result.baseline_backtest_owner_call_count == 1
        assert result.baseline_backtest_owner_invoked is True
        assert result.backtest_engine_completed is False
        assert result.economic_evidence_persisted is False
        assert result.economic_evaluation_executed is False
        assert result.executed is False
        assert REASON_BASELINE_OWNER_RUN_FAILED in result.reason_codes
        assert REASON_CANDIDATE_RUN_FAILED in result.reason_codes

    def test_successful_owner_without_evidence_remains_fail_closed(
        self,
        authorization_ratification: dict,
        complete_binding: dict,
        tmp_path: Path,
    ) -> None:
        metrics = MagicMock(evaluation_instrument_id="okx:linear_perpetual:ETH:USDT:USDT:perp")
        config_path = tmp_path / "step31f_trend_following_v2_economic_evaluation_v1.json"
        config_path.write_text("{}", encoding="utf-8")
        output_dir = tmp_path / "baseline_candidate_output"

        with (
            patch(
                "src.research.trend_following_v2_offline_economic_evaluation_execution_v0."
                "compute_sparse_signal_density_metrics_v0",
                return_value=metrics,
            ),
            patch(
                "src.research.trend_following_v2_offline_economic_evaluation_execution_v0."
                "build_sparse_signal_runtime_step31f_config_v0",
                return_value=config_path,
            ),
            patch(
                "src.research.trend_following_v2_offline_economic_evaluation_execution_v0."
                "_run_candidate_with_runtime_config_v0",
                return_value=_successful_candidate_result(
                    config_path=config_path,
                    output_dir=output_dir,
                ),
            ),
        ):
            result = run_baseline_offline_economic_evaluation_v0(
                go_token=BASELINE_EXECUTION_GO_TOKEN,
                repo_root=REPO_ROOT,
                authorization_ratification=authorization_ratification,
                versioned_binding=complete_binding,
                staging_root=STAGING_ROOT,
                scratch_root=tmp_path,
                invoke_baseline_owner=True,
            )

        assert result.blocked is True
        assert result.backtest_engine_completed is True
        assert result.economic_evidence_persisted is False
        assert result.economic_evaluation_executed is False
        assert REASON_BASELINE_CANONICAL_EVIDENCE_MISSING in result.reason_codes

    def test_successful_owner_with_canonical_evidence_completes_evaluation(
        self,
        authorization_ratification: dict,
        complete_binding: dict,
        tmp_path: Path,
    ) -> None:
        metrics = MagicMock(evaluation_instrument_id="okx:linear_perpetual:ETH:USDT:USDT:perp")
        config_path = tmp_path / "step31f_trend_following_v2_economic_evaluation_v1.json"
        config_path.write_text("{}", encoding="utf-8")
        output_dir = tmp_path / "baseline_candidate_output"
        output_dir.mkdir()
        (output_dir / ARTIFACT_FILENAME).write_text("{}", encoding="utf-8")

        with (
            patch(
                "src.research.trend_following_v2_offline_economic_evaluation_execution_v0."
                "compute_sparse_signal_density_metrics_v0",
                return_value=metrics,
            ),
            patch(
                "src.research.trend_following_v2_offline_economic_evaluation_execution_v0."
                "build_sparse_signal_runtime_step31f_config_v0",
                return_value=config_path,
            ),
            patch(
                "src.research.trend_following_v2_offline_economic_evaluation_execution_v0."
                "_run_candidate_with_runtime_config_v0",
                return_value=_successful_candidate_result(
                    config_path=config_path,
                    output_dir=output_dir,
                ),
            ) as owner_spy,
        ):
            result = run_baseline_offline_economic_evaluation_v0(
                go_token=BASELINE_EXECUTION_GO_TOKEN,
                repo_root=REPO_ROOT,
                authorization_ratification=authorization_ratification,
                versioned_binding=complete_binding,
                staging_root=STAGING_ROOT,
                scratch_root=tmp_path,
                invoke_baseline_owner=True,
            )

        owner_spy.assert_called_once()
        assert result.blocked is False
        assert result.executed is True
        assert result.economic_evaluation_executed is True
        assert result.economic_evidence_persisted is True
        assert REASON_BASELINE_ECONOMIC_EVALUATION_COMPLETE in result.reason_codes


class TestWiringOnlyPathUnchanged:
    def test_wiring_only_path_is_not_economic_evaluation(
        self,
        authorization_ratification: dict,
        complete_binding: dict,
    ) -> None:
        result = run_baseline_offline_economic_evaluation_v0(
            go_token=BASELINE_EXECUTION_GO_TOKEN,
            repo_root=REPO_ROOT,
            authorization_ratification=authorization_ratification,
            versioned_binding=complete_binding,
        )
        assert result.baseline_backtest_owner_call_count == 0
        assert result.economic_evaluation_executed is False
        assert REASON_BASELINE_WIRING_VERIFIED in result.reason_codes
        assert REASON_BASELINE_CALLABLE_WIRING_ONLY_ACKNOWLEDGED in result.reason_codes
