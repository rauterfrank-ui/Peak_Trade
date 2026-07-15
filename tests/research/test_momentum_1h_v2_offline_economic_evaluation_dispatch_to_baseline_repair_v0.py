"""Dispatch-to-baseline orchestration repair contract tests for momentum_1h/v2."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.research.final_research_fleet_offline_economic_evaluation_execution_v0 import (
    CandidateExecutionResultV0,
    CandidateTerminalStatus,
    REASON_CANDIDATE_RUN_FAILED,
)
from src.research.momentum_1h_v2_offline_economic_evaluation_authorization_ratification_v0 import (
    materialize_offline_economic_evaluation_authorization_ratification_v0,
)
from src.research.momentum_1h_v2_offline_economic_evaluation_execution_v0 import (
    BASELINE_EXECUTION_GO_TOKEN,
    EXECUTION_GO_TOKEN,
    INFRASTRUCTURE_GO_TOKEN,
    REASON_BASELINE_BACKTEST_OWNER_INVOKED,
    REASON_BASELINE_CALLABLE_WIRING_ONLY_ACKNOWLEDGED,
    REASON_BASELINE_WIRING_VERIFIED,
    REASON_DISPATCH_PRECHECK_PASSED_STOPPED_BEFORE_EVALUATION,
    REASON_GO_TOKEN_INVALID,
    CANONICAL_BASELINE_BACKTEST_OWNER,
    PhaseExecutionBlockedResultV0,
    run_baseline_offline_economic_evaluation_v0,
    run_full_offline_economic_evaluation_v0,
    run_offline_economic_evaluation_execution_dispatch_v0,
)
from src.research.momentum_1h_v2_versioned_research_binding_v0 import (
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


def _wiring_only_baseline_result(*, owner_ref: str) -> PhaseExecutionBlockedResultV0:
    return PhaseExecutionBlockedResultV0(
        phase="BASELINE",
        executed=False,
        blocked=False,
        wiring_verified=True,
        canonical_owner=owner_ref,
        actual_baseline_backtest_call_present=False,
        baseline_backtest_owner_call_count=0,
        reason_codes=(
            REASON_BASELINE_WIRING_VERIFIED,
            REASON_BASELINE_CALLABLE_WIRING_ONLY_ACKNOWLEDGED,
        ),
        authority_effect="OFFLINE_EVALUATION_AUTHORIZATION_ONLY",
        runtime_effect="NONE",
        economic_evaluation_executed=False,
    )


def _owner_invoked_baseline_result(*, owner_ref: str) -> PhaseExecutionBlockedResultV0:
    return PhaseExecutionBlockedResultV0(
        phase="BASELINE",
        executed=False,
        blocked=True,
        wiring_verified=True,
        canonical_owner=owner_ref,
        actual_baseline_backtest_call_present=True,
        baseline_backtest_owner_call_count=1,
        baseline_backtest_owner_invoked=True,
        backtest_engine_entered=True,
        backtest_engine_completed=False,
        economic_evidence_persisted=False,
        reason_codes=(REASON_BASELINE_BACKTEST_OWNER_INVOKED, REASON_CANDIDATE_RUN_FAILED),
        authority_effect="OFFLINE_EVALUATION_AUTHORIZATION_ONLY",
        runtime_effect="NONE",
        economic_evaluation_executed=False,
    )


class TestPositiveOrchestrationContract:
    def test_dispatch_accepted_chains_to_baseline_once(
        self,
        authorization_ratification: dict,
        complete_binding: dict,
    ) -> None:
        owner_ref = CANONICAL_BASELINE_BACKTEST_OWNER
        with patch(
            "src.research.momentum_1h_v2_offline_economic_evaluation_execution_v0."
            "run_baseline_offline_economic_evaluation_v0",
            return_value=_wiring_only_baseline_result(owner_ref=owner_ref),
        ) as baseline_spy:
            result = run_full_offline_economic_evaluation_v0(
                go_token=EXECUTION_GO_TOKEN,
                repo_root=REPO_ROOT,
                authorization_ratification=authorization_ratification,
                versioned_binding=complete_binding,
            )

        baseline_spy.assert_called_once()
        call_kwargs = baseline_spy.call_args.kwargs
        assert call_kwargs["go_token"] == EXECUTION_GO_TOKEN
        assert call_kwargs["invoke_baseline_owner"] is True
        assert call_kwargs["orchestrated_from_full_evaluation"] is True
        assert call_kwargs["staging_root"] == STAGING_ROOT
        assert result.wiring_verified is True
        assert result.canonical_owner == owner_ref
        assert REASON_DISPATCH_PRECHECK_PASSED_STOPPED_BEFORE_EVALUATION not in result.reason_codes
        assert result.economic_evaluation_executed is False

    def test_baseline_result_propagates_owner_invocation_fields(
        self,
        authorization_ratification: dict,
        complete_binding: dict,
    ) -> None:
        owner_ref = CANONICAL_BASELINE_BACKTEST_OWNER
        with patch(
            "src.research.momentum_1h_v2_offline_economic_evaluation_execution_v0."
            "run_baseline_offline_economic_evaluation_v0",
            return_value=_owner_invoked_baseline_result(owner_ref=owner_ref),
        ):
            result = run_full_offline_economic_evaluation_v0(
                go_token=EXECUTION_GO_TOKEN,
                repo_root=REPO_ROOT,
                authorization_ratification=authorization_ratification,
                versioned_binding=complete_binding,
            )

        assert result.baseline_backtest_owner_call_count == 1
        assert result.baseline_backtest_owner_invoked is True
        assert result.actual_baseline_backtest_call_present is True
        assert result.economic_evaluation_executed is False

    def test_orchestrated_baseline_accepts_execution_go_token(
        self,
        authorization_ratification: dict,
        complete_binding: dict,
        tmp_path: Path,
    ) -> None:
        metrics = MagicMock(evaluation_instrument_id="okx:linear_perpetual:ETH:USDT:USDT:perp")
        config_path = tmp_path / "step31f_momentum_1h_v2_economic_evaluation_v1.json"
        config_path.write_text("{}", encoding="utf-8")
        owner_ref = CANONICAL_BASELINE_BACKTEST_OWNER
        failed_result = CandidateExecutionResultV0(
            strategy_id=STRATEGY_ID,
            strategy_version=STRATEGY_VERSION,
            canonical_candidate_identifier="momentum_1h/v2",
            config_path=str(config_path),
            output_dir=str(tmp_path / "baseline_candidate_output"),
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
        with (
            patch(
                "src.research.momentum_1h_v2_offline_economic_evaluation_execution_v0."
                "compute_sparse_signal_density_metrics_v0",
                return_value=metrics,
            ),
            patch(
                "src.research.momentum_1h_v2_offline_economic_evaluation_execution_v0."
                "build_sparse_signal_runtime_step31f_config_v0",
                return_value=config_path,
            ),
            patch(
                "src.research.momentum_1h_v2_offline_economic_evaluation_execution_v0."
                "_run_candidate_with_runtime_config_v0",
                return_value=failed_result,
            ) as owner_spy,
        ):
            result = run_baseline_offline_economic_evaluation_v0(
                go_token=EXECUTION_GO_TOKEN,
                repo_root=REPO_ROOT,
                authorization_ratification=authorization_ratification,
                versioned_binding=complete_binding,
                staging_root=STAGING_ROOT,
                scratch_root=tmp_path,
                invoke_baseline_owner=True,
                orchestrated_from_full_evaluation=True,
            )

        owner_spy.assert_called_once()
        assert result.canonical_owner == owner_ref
        assert result.baseline_backtest_owner_call_count == 1
        assert result.economic_evaluation_executed is False


class TestNegativeFailClosedContract:
    def test_dispatch_rejection_does_not_call_baseline(
        self,
        authorization_ratification: dict,
        complete_binding: dict,
    ) -> None:
        with (
            patch(
                "src.research.momentum_1h_v2_offline_economic_evaluation_execution_v0."
                "run_offline_economic_evaluation_execution_dispatch_v0",
                return_value=MagicMock(
                    dispatch_accepted=False,
                    precheck_passed=False,
                    reason_codes=(REASON_GO_TOKEN_INVALID,),
                ),
            ),
            patch(
                "src.research.momentum_1h_v2_offline_economic_evaluation_execution_v0."
                "run_baseline_offline_economic_evaluation_v0",
            ) as baseline_spy,
        ):
            result = run_full_offline_economic_evaluation_v0(
                go_token=EXECUTION_GO_TOKEN,
                repo_root=REPO_ROOT,
                authorization_ratification=authorization_ratification,
                versioned_binding=complete_binding,
            )

        baseline_spy.assert_not_called()
        assert result.blocked is True

    def test_invalid_go_token_blocks_before_baseline(self) -> None:
        with patch(
            "src.research.momentum_1h_v2_offline_economic_evaluation_execution_v0."
            "run_baseline_offline_economic_evaluation_v0",
        ) as baseline_spy:
            result = run_full_offline_economic_evaluation_v0(
                go_token=INFRASTRUCTURE_GO_TOKEN,
                repo_root=REPO_ROOT,
            )

        baseline_spy.assert_not_called()
        assert result.blocked is True
        assert REASON_GO_TOKEN_INVALID in result.reason_codes

    def test_baseline_go_token_still_rejected_without_orchestration_flag(
        self,
        authorization_ratification: dict,
        complete_binding: dict,
    ) -> None:
        result = run_baseline_offline_economic_evaluation_v0(
            go_token=EXECUTION_GO_TOKEN,
            repo_root=REPO_ROOT,
            authorization_ratification=authorization_ratification,
            versioned_binding=complete_binding,
            staging_root=STAGING_ROOT,
            invoke_baseline_owner=False,
            orchestrated_from_full_evaluation=False,
        )
        assert result.blocked is True
        assert REASON_GO_TOKEN_INVALID in result.reason_codes

    def test_baseline_execution_go_token_still_valid_direct_path(
        self,
        authorization_ratification: dict,
        complete_binding: dict,
    ) -> None:
        result = run_baseline_offline_economic_evaluation_v0(
            go_token=BASELINE_EXECUTION_GO_TOKEN,
            repo_root=REPO_ROOT,
            authorization_ratification=authorization_ratification,
            versioned_binding=complete_binding,
            invoke_baseline_owner=False,
        )
        assert result.blocked is False
        assert result.wiring_verified is True

    def test_dispatch_precheck_terminal_reason_not_emitted_after_accepted_dispatch(
        self,
        authorization_ratification: dict,
        complete_binding: dict,
    ) -> None:
        dispatch = run_offline_economic_evaluation_execution_dispatch_v0(
            repo_root=REPO_ROOT,
            authorization_ratification=authorization_ratification,
            go_token=EXECUTION_GO_TOKEN,
            versioned_binding=complete_binding,
            verify_source_manifests=False,
        )
        assert dispatch.dispatch_accepted is True

        with patch(
            "src.research.momentum_1h_v2_offline_economic_evaluation_execution_v0."
            "run_baseline_offline_economic_evaluation_v0",
            return_value=_wiring_only_baseline_result(owner_ref=CANONICAL_BASELINE_BACKTEST_OWNER),
        ):
            result = run_full_offline_economic_evaluation_v0(
                go_token=EXECUTION_GO_TOKEN,
                repo_root=REPO_ROOT,
                authorization_ratification=authorization_ratification,
                versioned_binding=complete_binding,
                verify_source_manifests=False,
            )

        assert REASON_DISPATCH_PRECHECK_PASSED_STOPPED_BEFORE_EVALUATION not in result.reason_codes
