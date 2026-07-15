"""Baseline execution implementation contract tests for trend_following v2."""

from __future__ import annotations

import ast
import inspect
from copy import deepcopy
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.research.final_research_fleet_offline_economic_evaluation_execution_v0 import (
    CandidateExecutionResultV0,
    CandidateTerminalStatus,
)
from src.research.trend_following_v2_offline_economic_evaluation_authorization_ratification_v0 import (
    materialize_offline_economic_evaluation_authorization_ratification_v0,
)
from src.research.trend_following_v2_offline_economic_evaluation_execution_v0 import (
    AUTHORITY_EFFECT,
    BASELINE_EXECUTION_GO_TOKEN,
    BASELINE_EXECUTION_IMPLEMENTATION_GO_TOKEN,
    CANONICAL_BASELINE_BACKTEST_OWNER,
    CANONICAL_BASELINE_ENTRY_POINT,
    ENTRY_POINT_DISPATCH_REGISTRY,
    RATIFIED_BINDING_DIGEST,
    RATIFIED_DATASET_DIGEST,
    REASON_BASELINE_BACKTEST_OWNER_INVOKED,
    REASON_BINDING_DIGEST_MISMATCH,
    REASON_DATASET_DIGEST_MISMATCH,
    REASON_GO_TOKEN_INVALID,
    REASON_GO_TOKEN_MISSING,
    REASON_IMPLEMENTATION_GO_DOES_NOT_AUTHORIZE_BASELINE_EXECUTION,
    ROUNDTRIP_COST_BPS,
    RUNNER_SCRIPT,
    RUNTIME_EFFECT,
    run_baseline_offline_economic_evaluation_v0,
    validate_baseline_execution_go_token_v0,
    validate_baseline_execution_implementation_go_token_v0,
    verify_actual_baseline_backtest_call_present_in_production_source_v0,
)
from src.research.trend_following_v2_versioned_research_binding_v0 import (
    STRATEGY_ID,
    STRATEGY_VERSION,
    materialize_versioned_research_binding_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
_IMPL_GO = BASELINE_EXECUTION_IMPLEMENTATION_GO_TOKEN
_BASELINE_EXEC_GO = BASELINE_EXECUTION_GO_TOKEN
RUNNER_MODULE = REPO_ROOT / RUNNER_SCRIPT
STAGING_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "datasets/admissible_futures/pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_v1/"
    "extended_chronological_v1"
)
FORBIDDEN_RUNTIME_IMPORT_PREFIXES = (
    "src.execution",
    "src.scheduler",
    "src.broker",
    "src.orders",
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


class TestBaselineEntryPointMaterialized:
    def test_entry_point_importable(self) -> None:
        assert run_baseline_offline_economic_evaluation_v0 is not None
        assert CANONICAL_BASELINE_ENTRY_POINT.endswith(
            "run_baseline_offline_economic_evaluation_v0"
        )

    def test_actual_baseline_backtest_call_present_in_production_source(self) -> None:
        assert verify_actual_baseline_backtest_call_present_in_production_source_v0() is True

    def test_baseline_function_source_contains_canonical_backtest_owner(self) -> None:
        source = inspect.getsource(run_baseline_offline_economic_evaluation_v0)
        assert "_run_candidate_with_runtime_config_v0(" in source
        assert CANONICAL_BASELINE_BACKTEST_OWNER.endswith("_run_candidate_with_runtime_config_v0")


class TestBaselineGoTokenRegistration:
    def test_implementation_go_token_accepted(self) -> None:
        ok, reasons = validate_baseline_execution_implementation_go_token_v0(_IMPL_GO)
        assert ok is True
        assert reasons == ()

    def test_baseline_execution_go_token_registered_in_dispatch_registry(self) -> None:
        assert ENTRY_POINT_DISPATCH_REGISTRY[_BASELINE_EXEC_GO] == "BASELINE_EXECUTION_V0"
        assert ENTRY_POINT_DISPATCH_REGISTRY[_IMPL_GO] == "BASELINE_EXECUTION_IMPLEMENTATION_V0"


class TestImplementationGoAuthorizationBoundary:
    def test_implementation_go_does_not_authorize_baseline_execution(
        self,
        authorization_ratification: dict,
        complete_binding: dict,
    ) -> None:
        result = run_baseline_offline_economic_evaluation_v0(
            go_token=_IMPL_GO,
            repo_root=REPO_ROOT,
            authorization_ratification=authorization_ratification,
            versioned_binding=complete_binding,
            invoke_baseline_owner=True,
            staging_root=STAGING_ROOT,
        )
        assert result.executed is False
        assert result.blocked is True
        assert REASON_GO_TOKEN_INVALID in result.reason_codes
        assert REASON_IMPLEMENTATION_GO_DOES_NOT_AUTHORIZE_BASELINE_EXECUTION in result.reason_codes

    def test_baseline_execution_go_reaches_wiring_only_stop(
        self,
        authorization_ratification: dict,
        complete_binding: dict,
    ) -> None:
        result = run_baseline_offline_economic_evaluation_v0(
            go_token=_BASELINE_EXEC_GO,
            repo_root=REPO_ROOT,
            authorization_ratification=authorization_ratification,
            versioned_binding=complete_binding,
        )
        assert result.executed is False
        assert result.blocked is False
        assert result.wiring_verified is True
        assert result.canonical_owner == CANONICAL_BASELINE_BACKTEST_OWNER
        assert result.baseline_backtest_owner_call_count == 0


class TestHappyPathCanonicalBacktestOwnerInvocation:
    def test_valid_bindings_invoke_canonical_backtest_owner_exactly_once(
        self,
        authorization_ratification: dict,
        complete_binding: dict,
        tmp_path: Path,
    ) -> None:
        metrics = MagicMock(evaluation_instrument_id="okx:linear_perpetual:ETH:USDT:USDT:perp")
        backtest_result = CandidateExecutionResultV0(
            strategy_id=STRATEGY_ID,
            strategy_version=STRATEGY_VERSION,
            canonical_candidate_identifier="trend_following/v2",
            config_path=str(tmp_path / "config.json"),
            output_dir=str(tmp_path / "output"),
            run_id="test-run",
            terminal_status=CandidateTerminalStatus.INCONCLUSIVE,
            economic_validity_result="BLOCKED",
            economic_validity_offline_gate_pass=False,
            evidence_status="",
            manifest_verify_rc=0,
            reason_codes=(),
            stage_return_codes={"economic_viability_runner": 0},
            runner_execution_success=False,
        )
        backtest_spy = MagicMock(return_value=backtest_result)
        config_path = tmp_path / "step31f_trend_following_v2_economic_evaluation_v1.json"
        config_path.write_text("{}", encoding="utf-8")

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
                backtest_spy,
            ),
        ):
            result = run_baseline_offline_economic_evaluation_v0(
                go_token=_BASELINE_EXEC_GO,
                repo_root=REPO_ROOT,
                authorization_ratification=authorization_ratification,
                versioned_binding=complete_binding,
                staging_root=STAGING_ROOT,
                scratch_root=tmp_path,
                invoke_baseline_owner=True,
            )

        assert result.blocked is True
        assert result.executed is False
        assert result.actual_baseline_backtest_call_present is True
        assert result.baseline_backtest_owner_call_count == 1
        assert result.baseline_backtest_owner_invoked is True
        assert result.economic_evaluation_executed is False
        assert REASON_BASELINE_BACKTEST_OWNER_INVOKED in result.reason_codes
        assert "BASELINE_OWNER_RUN_FAILED" in result.reason_codes
        backtest_spy.assert_called_once()
        _, kwargs = backtest_spy.call_args
        assert kwargs["strategy_id"] == STRATEGY_ID
        assert kwargs["strategy_version"] == STRATEGY_VERSION
        assert kwargs["config_path"] == config_path
        assert not Path(kwargs["output_dir"]).exists()


class TestBindingAndCostContracts:
    def test_roundtrip_cost_bps_unchanged(self, complete_binding: dict) -> None:
        execution_model = complete_binding["binding"]["execution_model_binding"]
        assert execution_model["roundtrip_cost_bps"] == ROUNDTRIP_COST_BPS
        assert ROUNDTRIP_COST_BPS == 40.0

    def test_binding_digest_mismatch_blocks_before_backtest(
        self,
        authorization_ratification: dict,
        complete_binding: dict,
    ) -> None:
        stale = deepcopy(complete_binding)
        stale["binding_digest"] = "f" * 64
        result = run_baseline_offline_economic_evaluation_v0(
            go_token=_BASELINE_EXEC_GO,
            repo_root=REPO_ROOT,
            authorization_ratification=authorization_ratification,
            versioned_binding=stale,
            invoke_baseline_owner=True,
            staging_root=STAGING_ROOT,
        )
        assert result.blocked is True
        assert REASON_BINDING_DIGEST_MISMATCH in result.reason_codes

    def test_dataset_digest_mismatch_blocks_before_backtest(
        self,
        authorization_ratification: dict,
        complete_binding: dict,
    ) -> None:
        stale = deepcopy(complete_binding)
        stale["dataset_digest"] = "f" * 64
        result = run_baseline_offline_economic_evaluation_v0(
            go_token=_BASELINE_EXEC_GO,
            repo_root=REPO_ROOT,
            authorization_ratification=authorization_ratification,
            versioned_binding=stale,
            invoke_baseline_owner=True,
            staging_root=STAGING_ROOT,
        )
        assert result.blocked is True
        assert REASON_DATASET_DIGEST_MISMATCH in result.reason_codes

    def test_ratified_digests_match_fixture(self, complete_binding: dict) -> None:
        assert complete_binding["binding_digest"] == RATIFIED_BINDING_DIGEST
        assert complete_binding["dataset_digest"] == RATIFIED_DATASET_DIGEST


class TestFuturesOnlyAndBitcoinExclusion:
    def test_futures_only_enforced(
        self,
        authorization_ratification: dict,
        complete_binding: dict,
    ) -> None:
        mutated = deepcopy(complete_binding)
        mutated["binding"]["instrument_binding"]["futures_only"] = False
        result = run_baseline_offline_economic_evaluation_v0(
            go_token=_BASELINE_EXEC_GO,
            repo_root=REPO_ROOT,
            authorization_ratification=authorization_ratification,
            versioned_binding=mutated,
        )
        assert result.blocked is True
        assert "FUTURES_ONLY_VIOLATION" in result.reason_codes

    def test_bitcoin_exclusion_enforced(
        self,
        authorization_ratification: dict,
        complete_binding: dict,
    ) -> None:
        mutated = deepcopy(complete_binding)
        mutated["binding"]["instrument_binding"]["bitcoin_direction_allowed"] = True
        result = run_baseline_offline_economic_evaluation_v0(
            go_token=_BASELINE_EXEC_GO,
            repo_root=REPO_ROOT,
            authorization_ratification=authorization_ratification,
            versioned_binding=mutated,
        )
        assert result.blocked is True
        assert "BITCOIN_DIRECTION_VIOLATION" in result.reason_codes


class TestGoTokenGate:
    def test_missing_go_token_fail_closed(self) -> None:
        ok, reasons = validate_baseline_execution_go_token_v0(None)
        assert ok is False
        assert REASON_GO_TOKEN_MISSING in reasons

    def test_wrong_go_token_fail_closed(self, complete_binding: dict) -> None:
        result = run_baseline_offline_economic_evaluation_v0(
            go_token="GO_WRONG_TOKEN",
            repo_root=REPO_ROOT,
            versioned_binding=complete_binding,
        )
        assert result.blocked is True
        assert REASON_GO_TOKEN_INVALID in result.reason_codes


class TestOfflineBoundary:
    def test_no_economic_evaluation_executed_in_implementation_scope(
        self,
        authorization_ratification: dict,
        complete_binding: dict,
    ) -> None:
        result = run_baseline_offline_economic_evaluation_v0(
            go_token=_BASELINE_EXEC_GO,
            repo_root=REPO_ROOT,
            authorization_ratification=authorization_ratification,
            versioned_binding=complete_binding,
        )
        assert result.executed is False

    def test_runtime_and_authority_effect_none(self) -> None:
        assert AUTHORITY_EFFECT == "NONE"
        assert RUNTIME_EFFECT == "NONE"

    def test_runner_has_no_forbidden_runtime_imports(self) -> None:
        tree = ast.parse(RUNNER_MODULE.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert not any(
                        alias.name.startswith(prefix)
                        for prefix in FORBIDDEN_RUNTIME_IMPORT_PREFIXES
                    )
            if isinstance(node, ast.ImportFrom) and node.module:
                assert not any(
                    node.module.startswith(prefix) for prefix in FORBIDDEN_RUNTIME_IMPORT_PREFIXES
                )
