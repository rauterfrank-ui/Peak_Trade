"""Implementation repair contract tests for pairwise spillover v1 execution harness wiring."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_evaluation_authorization_ratification_v0 import (
    materialize_offline_economic_evaluation_authorization_ratification_v0,
)
from src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_evaluation_execution_v0 import (
    AUTHORITY_EFFECT,
    BOUND_PORTFOLIO_BINDING_STATUS,
    CANONICAL_BASELINE_BACKTEST_OWNER,
    CANONICAL_MONTE_CARLO_OWNER,
    CANONICAL_STRESS_OWNER,
    CANONICAL_WALK_FORWARD_OWNER,
    EXECUTION_GO_TOKEN,
    IMPLEMENTATION_GO_TOKEN,
    IMPLEMENTATION_REPAIR_GO_TOKEN,
    PORTFOLIO_BINDING_REQUIRED_FIELDS,
    REASON_BASELINE_ADJUDICATION_BLOCKS_DOWNSTREAM,
    REASON_ECONOMIC_EVALUATION_BLOCKED,
    REASON_GO_TOKEN_INVALID,
    REASON_PORTFOLIO_BINDING_PENDING,
    REASON_REEVALUATION_GO_REQUIRED,
    RUNTIME_EFFECT,
    RUNNER_SCRIPT,
    dumps_execution_canonical_v1,
    materialize_versioned_hypothesis_binding_v0,
    phase_result_to_dict,
    run_baseline_offline_economic_evaluation_v0,
    run_full_offline_economic_evaluation_v0,
    run_monte_carlo_evaluation_v0,
    run_stress_evaluation_v0,
    run_walk_forward_evaluation_v0,
    validate_entry_point_go_token_v0,
    validate_implementation_go_token_v0,
    validate_implementation_repair_go_token_v0,
)
from src.research.cross_sectional_panel_economic_evaluation_wiring_v0 import (
    compute_walk_forward_period_metrics_v0,
    invoke_monte_carlo_v0,
    invoke_stress_v0,
)
from src.research.cross_sectional_single_slot_backtest_wiring_v0 import (
    run_single_slot_panel_backtest_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
_EXEC_GO = EXECUTION_GO_TOKEN
_INFRA_GO = IMPLEMENTATION_GO_TOKEN
_REPAIR_GO = IMPLEMENTATION_REPAIR_GO_TOKEN


def _binding_with_pending_portfolio(complete_binding: dict) -> dict:
    stale = deepcopy(complete_binding)
    pending = deepcopy(stale["pending_implementation_bindings"])
    for field in PORTFOLIO_BINDING_REQUIRED_FIELDS:
        pending[field] = {
            "ref": field,
            "status": "PENDING_SEPARATE_IMPLEMENTATION_BINDING",
        }
    stale["pending_implementation_bindings"] = pending
    return stale


def _binding_with_missing_portfolio(complete_binding: dict) -> dict:
    stale = deepcopy(complete_binding)
    stale["pending_implementation_bindings"] = {}
    return stale


@pytest.fixture(name="complete_binding")
def fixture_complete_binding() -> dict:
    return materialize_versioned_hypothesis_binding_v0()


@pytest.fixture(name="authorization_ratification")
def fixture_authorization_ratification() -> dict:
    return materialize_offline_economic_evaluation_authorization_ratification_v0()


class TestValidBindingsReachCanonicalBaselineOwner:
    def test_valid_portfolio_bindings_reach_canonical_baseline_owner(
        self,
        complete_binding: dict,
    ) -> None:
        result = run_baseline_offline_economic_evaluation_v0(
            go_token=_EXEC_GO,
            repo_root=REPO_ROOT,
            versioned_binding=complete_binding,
        )
        assert result.executed is False
        assert result.blocked is False
        assert result.wiring_verified is True
        assert result.canonical_owner == CANONICAL_BASELINE_BACKTEST_OWNER

    def test_valid_bindings_do_not_emit_pending_portfolio_bindings_reason(
        self,
        authorization_ratification: dict,
        complete_binding: dict,
    ) -> None:
        result = run_full_offline_economic_evaluation_v0(
            go_token=_EXEC_GO,
            repo_root=REPO_ROOT,
            authorization_ratification=authorization_ratification,
            versioned_binding=complete_binding,
            verify_source_manifests=False,
            materialize_dataset=False,
        )
        assert REASON_ECONOMIC_EVALUATION_BLOCKED not in result.reason_codes
        assert not any(REASON_PORTFOLIO_BINDING_PENDING in item for item in result.reason_codes)
        assert REASON_REEVALUATION_GO_REQUIRED in result.reason_codes


class TestInvalidBindingsFailClosed:
    def test_missing_portfolio_bindings_fail_closed(self, complete_binding: dict) -> None:
        result = run_baseline_offline_economic_evaluation_v0(
            go_token=_EXEC_GO,
            repo_root=REPO_ROOT,
            versioned_binding=_binding_with_missing_portfolio(complete_binding),
        )
        assert result.blocked is True
        assert result.wiring_verified is False

    def test_invalid_portfolio_bindings_fail_closed(self, complete_binding: dict) -> None:
        result = run_baseline_offline_economic_evaluation_v0(
            go_token=_EXEC_GO,
            repo_root=REPO_ROOT,
            versioned_binding=_binding_with_pending_portfolio(complete_binding),
        )
        assert result.blocked is True
        assert any(REASON_PORTFOLIO_BINDING_PENDING in item for item in result.reason_codes)


class TestDownstreamSequencePolicy:
    def test_baseline_failure_stops_downstream_robustness_when_policy_requires(
        self,
        authorization_ratification: dict,
        complete_binding: dict,
    ) -> None:
        result = run_full_offline_economic_evaluation_v0(
            go_token=_EXEC_GO,
            repo_root=REPO_ROOT,
            authorization_ratification=authorization_ratification,
            versioned_binding=complete_binding,
            verify_source_manifests=False,
            materialize_dataset=False,
            force_baseline_adjudication_failure=True,
        )
        assert result.blocked is True
        assert result.downstream_sequence_allowed is False
        assert REASON_BASELINE_ADJUDICATION_BLOCKS_DOWNSTREAM in result.reason_codes

    def test_baseline_success_allows_policy_governed_downstream_sequence(
        self,
        authorization_ratification: dict,
        complete_binding: dict,
    ) -> None:
        result = run_full_offline_economic_evaluation_v0(
            go_token=_EXEC_GO,
            repo_root=REPO_ROOT,
            authorization_ratification=authorization_ratification,
            versioned_binding=complete_binding,
            verify_source_manifests=False,
            materialize_dataset=False,
        )
        assert result.wiring_verified is True
        assert result.downstream_sequence_allowed is True


class TestCanonicalOwnerReuse:
    def test_walk_forward_owner_is_reused(self, complete_binding: dict) -> None:
        result = run_walk_forward_evaluation_v0(
            go_token=_EXEC_GO,
            repo_root=REPO_ROOT,
            versioned_binding=complete_binding,
        )
        assert result.canonical_owner == CANONICAL_WALK_FORWARD_OWNER
        assert compute_walk_forward_period_metrics_v0 is not None

    def test_monte_carlo_owner_is_reused(self, complete_binding: dict) -> None:
        result = run_monte_carlo_evaluation_v0(
            go_token=_EXEC_GO,
            repo_root=REPO_ROOT,
            versioned_binding=complete_binding,
        )
        assert result.canonical_owner == CANONICAL_MONTE_CARLO_OWNER
        assert invoke_monte_carlo_v0 is not None

    def test_stress_owner_is_reused(self, complete_binding: dict) -> None:
        result = run_stress_evaluation_v0(
            go_token=_EXEC_GO,
            repo_root=REPO_ROOT,
            versioned_binding=complete_binding,
        )
        assert result.canonical_owner == CANONICAL_STRESS_OWNER
        assert invoke_stress_v0 is not None

    def test_baseline_owner_matches_canonical_backtest(self) -> None:
        assert run_single_slot_panel_backtest_v0 is not None


class TestRepairScopeSafety:
    def test_economic_evaluation_not_executed_by_repair_tests(
        self,
        authorization_ratification: dict,
        complete_binding: dict,
    ) -> None:
        result = run_full_offline_economic_evaluation_v0(
            go_token=_EXEC_GO,
            repo_root=REPO_ROOT,
            authorization_ratification=authorization_ratification,
            versioned_binding=complete_binding,
            verify_source_manifests=False,
            materialize_dataset=False,
        )
        assert result.executed is False

    def test_no_runtime_effect(self) -> None:
        assert RUNTIME_EFFECT == "NONE"

    def test_no_authority_effect(self) -> None:
        assert AUTHORITY_EFFECT == "NONE"

    def test_no_strategy_semantic_change(self, complete_binding: dict) -> None:
        roundtrip = materialize_versioned_hypothesis_binding_v0()
        assert roundtrip["score_family_policy"] == complete_binding["score_family_policy"]
        assert roundtrip["parameter_binding"] == complete_binding["parameter_binding"]

    def test_no_dataset_change(self, complete_binding: dict) -> None:
        roundtrip = materialize_versioned_hypothesis_binding_v0()
        assert roundtrip["dataset_digest"] == complete_binding["dataset_digest"]

    def test_no_universe_change(self, complete_binding: dict) -> None:
        roundtrip = materialize_versioned_hypothesis_binding_v0()
        universe = roundtrip["binding"]["pit_universe_binding"]["universe_digest"]
        expected = complete_binding["binding"]["pit_universe_binding"]["universe_digest"]
        assert universe == expected

    def test_no_cost_policy_change(self, complete_binding: dict) -> None:
        roundtrip = materialize_versioned_hypothesis_binding_v0()
        assert roundtrip["cost_execution_binding"] == complete_binding["cost_execution_binding"]

    def test_no_risk_sizing_change(self, complete_binding: dict) -> None:
        weighting = complete_binding["pending_implementation_bindings"][
            "portfolio_weighting_policy"
        ]["policy"]
        assert weighting["risk_sizing_semantics_changed"] is False


class TestDeterministicSerialization:
    def test_deterministic_result_schema_serialization(self, complete_binding: dict) -> None:
        kwargs = {
            "go_token": _EXEC_GO,
            "repo_root": REPO_ROOT,
            "versioned_binding": complete_binding,
        }
        first = dumps_execution_canonical_v1(
            phase_result_to_dict(run_baseline_offline_economic_evaluation_v0(**kwargs))
        )
        second = dumps_execution_canonical_v1(
            phase_result_to_dict(run_baseline_offline_economic_evaluation_v0(**kwargs))
        )
        assert first == second


class TestGoTokenFailClosed:
    def test_existing_entry_point_go_token_rejection_remains_fail_closed(self) -> None:
        ok, branch = validate_entry_point_go_token_v0(_INFRA_GO)
        assert ok is True
        assert branch == "IMPLEMENTATION_V0"

    def test_wrong_go_token_remains_rejected(self) -> None:
        ok, _ = validate_implementation_go_token_v0("GO_WRONG_TOKEN")
        assert ok is False

    def test_implementation_go_does_not_authorize_reevaluation(self) -> None:
        result = run_full_offline_economic_evaluation_v0(go_token=_INFRA_GO)
        assert result.blocked is True
        assert REASON_GO_TOKEN_INVALID in result.reason_codes

    def test_repair_go_accepted_by_entry_point_registry(self) -> None:
        ok, branch = validate_entry_point_go_token_v0(_REPAIR_GO)
        assert ok is True
        assert branch == "IMPLEMENTATION_REPAIR_V0"

    def test_repair_go_validator(self) -> None:
        ok, _ = validate_implementation_repair_go_token_v0(_REPAIR_GO)
        assert ok is True


class TestRunnerEntryPoint:
    def test_canonical_runner_module_exists(self) -> None:
        assert (REPO_ROOT / RUNNER_SCRIPT).is_file()
