"""Actual baseline execution owner implementation contract tests for pairwise spillover v1."""

from __future__ import annotations

import ast
import inspect
from copy import deepcopy
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_evaluation_authorization_ratification_v0 import (
    materialize_offline_economic_evaluation_authorization_ratification_v0,
)
from src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_evaluation_execution_v0 import (
    AUTHORITY_EFFECT,
    CANONICAL_BASELINE_BACKTEST_OWNER,
    ENTRY_POINT_DISPATCH_REGISTRY,
    REASON_BASELINE_BACKTEST_OWNER_INVOKED,
    REASON_BINDING_DIGEST_MISMATCH,
    REASON_DATASET_DIGEST_MISMATCH,
    REASON_GO_TOKEN_INVALID,
    REASON_GO_TOKEN_MISSING,
    REASON_IMPLEMENTATION_GO_DOES_NOT_AUTHORIZE_BASELINE_EXECUTION,
    REEVALUATION_BASELINE_ACTUAL_EXECUTION_OWNER_IMPLEMENTATION_GO_TOKEN,
    REEVALUATION_BASELINE_EXECUTION_GO_TOKEN,
    REEVALUATION_BASELINE_EXECUTION_IMPLEMENTATION_GO_TOKEN,
    RATIFIED_BINDING_DIGEST,
    RATIFIED_DATASET_DIGEST,
    RUNNER_SCRIPT,
    RUNTIME_EFFECT,
    run_baseline_offline_economic_evaluation_v0,
    validate_reevaluation_baseline_actual_execution_owner_implementation_go_token_v0,
    validate_reevaluation_baseline_execution_go_token_v0,
    verify_actual_baseline_backtest_call_present_in_production_source_v0,
)
from src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_versioned_hypothesis_binding_v0 import (
    materialize_versioned_hypothesis_binding_v0,
)
from tests.research.fixtures.cross_sectional_relative_strength_v0.fixture_builder import (
    build_synthetic_panel_series_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
_IMPL_GO = REEVALUATION_BASELINE_ACTUAL_EXECUTION_OWNER_IMPLEMENTATION_GO_TOKEN
_BASELINE_EXEC_GO = REEVALUATION_BASELINE_EXECUTION_GO_TOKEN
_BASELINE_IMPL_GO = REEVALUATION_BASELINE_EXECUTION_IMPLEMENTATION_GO_TOKEN
RUNNER_MODULE = REPO_ROOT / RUNNER_SCRIPT
FORBIDDEN_RUNTIME_IMPORT_PREFIXES = (
    "src.execution",
    "src.scheduler",
    "src.broker",
    "src.orders",
)


@pytest.fixture(name="complete_binding")
def fixture_complete_binding() -> dict:
    return materialize_versioned_hypothesis_binding_v0()


@pytest.fixture(name="authorization_ratification")
def fixture_authorization_ratification() -> dict:
    return materialize_offline_economic_evaluation_authorization_ratification_v0()


@pytest.fixture(name="panel_series")
def fixture_panel_series():
    return build_synthetic_panel_series_v0(bar_count=40, end="2024-06-01T02:00:00Z")


class TestProductionCallPathPresence:
    def test_actual_baseline_backtest_call_present_in_production_source(self) -> None:
        assert verify_actual_baseline_backtest_call_present_in_production_source_v0() is True

    def test_baseline_function_source_contains_canonical_backtest_owner(self) -> None:
        source = inspect.getsource(run_baseline_offline_economic_evaluation_v0)
        assert "run_single_slot_panel_backtest_v0(" in source
        assert CANONICAL_BASELINE_BACKTEST_OWNER.endswith("run_single_slot_panel_backtest_v0")


class TestHappyPathCanonicalBacktestOwnerInvocation:
    def test_valid_bindings_invoke_canonical_backtest_owner_exactly_once(
        self,
        authorization_ratification: dict,
        complete_binding: dict,
        panel_series,
    ) -> None:
        backtest_spy = MagicMock(return_value=MagicMock(trade_count=0, net_return=0.0, stats={}))
        with patch(
            "src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_evaluation_execution_v0.run_single_slot_panel_backtest_v0",
            backtest_spy,
        ):
            result = run_baseline_offline_economic_evaluation_v0(
                go_token=_BASELINE_EXEC_GO,
                repo_root=REPO_ROOT,
                authorization_ratification=authorization_ratification,
                versioned_binding=complete_binding,
                panel_series=panel_series,
                verify_source_manifests=False,
                materialize_dataset=False,
            )
        assert result.blocked is False
        assert result.executed is False
        assert result.actual_baseline_backtest_call_present is True
        assert result.baseline_backtest_owner_call_count == 1
        assert REASON_BASELINE_BACKTEST_OWNER_INVOKED in result.reason_codes
        backtest_spy.assert_called_once()
        _, kwargs = backtest_spy.call_args
        from src.research.cross_sectional_cost_execution_binding_normalization_v0 import (
            normalize_cost_execution_binding_for_backtest_v0,
        )

        assert kwargs["cost_execution_binding"] == normalize_cost_execution_binding_for_backtest_v0(
            complete_binding["cost_execution_binding"]
        )
        orchestrator_arg, panel_arg = backtest_spy.call_args[0]
        assert orchestrator_arg.score_formula_version == complete_binding["score_family_policy"]
        assert panel_arg == panel_series

    def test_exception_from_backtest_owner_does_not_retry(
        self,
        authorization_ratification: dict,
        complete_binding: dict,
        panel_series,
    ) -> None:
        backtest_spy = MagicMock(side_effect=RuntimeError("backtest_failure"))
        with patch(
            "src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_evaluation_execution_v0.run_single_slot_panel_backtest_v0",
            backtest_spy,
        ):
            result = run_baseline_offline_economic_evaluation_v0(
                go_token=_BASELINE_EXEC_GO,
                repo_root=REPO_ROOT,
                authorization_ratification=authorization_ratification,
                versioned_binding=complete_binding,
                panel_series=panel_series,
                verify_source_manifests=False,
                materialize_dataset=False,
            )
        assert result.blocked is True
        backtest_spy.assert_called_once()


class TestGoTokenGate:
    def test_actual_execution_owner_implementation_go_registered(self) -> None:
        ok, _ = validate_reevaluation_baseline_actual_execution_owner_implementation_go_token_v0(
            _IMPL_GO
        )
        assert ok is True
        assert (
            ENTRY_POINT_DISPATCH_REGISTRY[_IMPL_GO]
            == "REEVALUATION_BASELINE_ACTUAL_EXECUTION_OWNER_IMPLEMENTATION_V0"
        )

    def test_implementation_go_tokens_do_not_authorize_baseline_execution(
        self,
        authorization_ratification: dict,
        complete_binding: dict,
        panel_series,
    ) -> None:
        for token in (_IMPL_GO, _BASELINE_IMPL_GO):
            result = run_baseline_offline_economic_evaluation_v0(
                go_token=token,
                repo_root=REPO_ROOT,
                authorization_ratification=authorization_ratification,
                versioned_binding=complete_binding,
                panel_series=panel_series,
            )
            assert result.blocked is True
            assert result.actual_baseline_backtest_call_present is False
            assert REASON_GO_TOKEN_INVALID in result.reason_codes
            assert (
                REASON_IMPLEMENTATION_GO_DOES_NOT_AUTHORIZE_BASELINE_EXECUTION
                in result.reason_codes
            )

    def test_missing_go_token_fail_closed(self) -> None:
        ok, reasons = validate_reevaluation_baseline_execution_go_token_v0(None)
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

    def test_baseline_execution_go_without_panel_series_remains_wiring_only(
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
        assert result.blocked is False
        assert result.wiring_verified is True
        assert result.actual_baseline_backtest_call_present is False
        assert result.baseline_backtest_owner_call_count == 0


class TestDigestAndBindingGates:
    def test_wrong_binding_digest_blocks_before_backtest_call(
        self,
        authorization_ratification: dict,
        complete_binding: dict,
        panel_series,
    ) -> None:
        stale = deepcopy(complete_binding)
        stale["binding_digest"] = "f" * 64
        backtest_spy = MagicMock()
        with patch(
            "src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_evaluation_execution_v0.run_single_slot_panel_backtest_v0",
            backtest_spy,
        ):
            result = run_baseline_offline_economic_evaluation_v0(
                go_token=_BASELINE_EXEC_GO,
                repo_root=REPO_ROOT,
                authorization_ratification=authorization_ratification,
                versioned_binding=stale,
                panel_series=panel_series,
            )
        assert result.blocked is True
        assert REASON_BINDING_DIGEST_MISMATCH in result.reason_codes
        backtest_spy.assert_not_called()

    def test_wrong_dataset_digest_blocks_before_backtest_call(
        self,
        authorization_ratification: dict,
        complete_binding: dict,
        panel_series,
    ) -> None:
        stale = deepcopy(complete_binding)
        stale["dataset_digest"] = "f" * 64
        backtest_spy = MagicMock()
        with patch(
            "src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_evaluation_execution_v0.run_single_slot_panel_backtest_v0",
            backtest_spy,
        ):
            result = run_baseline_offline_economic_evaluation_v0(
                go_token=_BASELINE_EXEC_GO,
                repo_root=REPO_ROOT,
                authorization_ratification=authorization_ratification,
                versioned_binding=stale,
                panel_series=panel_series,
            )
        assert result.blocked is True
        assert REASON_DATASET_DIGEST_MISMATCH in result.reason_codes
        backtest_spy.assert_not_called()

    def test_correct_binding_reaches_canonical_call_with_panel_series(
        self,
        authorization_ratification: dict,
        complete_binding: dict,
        panel_series,
    ) -> None:
        assert complete_binding["binding_digest"] == RATIFIED_BINDING_DIGEST
        assert complete_binding["dataset_digest"] == RATIFIED_DATASET_DIGEST
        backtest_spy = MagicMock(return_value=MagicMock(trade_count=0, net_return=0.0, stats={}))
        with patch(
            "src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_evaluation_execution_v0.run_single_slot_panel_backtest_v0",
            backtest_spy,
        ):
            result = run_baseline_offline_economic_evaluation_v0(
                go_token=_BASELINE_EXEC_GO,
                repo_root=REPO_ROOT,
                authorization_ratification=authorization_ratification,
                versioned_binding=complete_binding,
                panel_series=panel_series,
            )
        assert result.actual_baseline_backtest_call_present is True
        backtest_spy.assert_called_once()


class TestOfflineBoundary:
    def test_futures_only_constraint_preserved(self, complete_binding: dict) -> None:
        assert complete_binding["system_constraints"]["futures_only"] is True

    def test_bitcoin_direction_forbidden(self, complete_binding: dict) -> None:
        assert complete_binding["system_constraints"]["bitcoin_direction_allowed"] is False

    def test_spot_and_synthetic_spot_forbidden(self, complete_binding: dict) -> None:
        pairwise = complete_binding["pairwise_hypothesis_contract"]
        assert pairwise["spot_allowed"] is False
        assert pairwise["synthetic_spot_allowed"] is False

    def test_no_runtime_import_boundary_violation(self) -> None:
        source = (REPO_ROOT / RUNNER_SCRIPT).read_text(encoding="utf-8")
        tree = ast.parse(source)
        imports = {
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module
        }
        assert not any(
            item.startswith(prefix)
            for item in imports
            for prefix in FORBIDDEN_RUNTIME_IMPORT_PREFIXES
        )

    def test_runtime_and_authority_effect_none(self) -> None:
        assert RUNTIME_EFFECT == "NONE"
        assert AUTHORITY_EFFECT == "NONE"


class TestResultContract:
    def test_implementation_verification_marks_call_present_without_economic_execution(
        self,
        authorization_ratification: dict,
        complete_binding: dict,
        panel_series,
    ) -> None:
        backtest_spy = MagicMock(return_value=MagicMock(trade_count=0, net_return=0.0, stats={}))
        with patch(
            "src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_evaluation_execution_v0.run_single_slot_panel_backtest_v0",
            backtest_spy,
        ):
            result = run_baseline_offline_economic_evaluation_v0(
                go_token=_BASELINE_EXEC_GO,
                repo_root=REPO_ROOT,
                authorization_ratification=authorization_ratification,
                versioned_binding=complete_binding,
                panel_series=panel_series,
            )
        assert result.actual_baseline_backtest_call_present is True
        assert result.executed is False
        assert result.baseline_backtest_owner_call_count == 1
        assert "net_return" not in str(result.reason_codes)
        assert "sharpe" not in str(result.reason_codes)
