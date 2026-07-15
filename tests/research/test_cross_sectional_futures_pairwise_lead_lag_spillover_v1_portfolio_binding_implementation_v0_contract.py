"""Contract tests for pairwise spillover v1 portfolio binding implementation v0."""

from __future__ import annotations

import json
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

import pytest

from src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_evaluation_execution_v0 import (
    EXECUTION_GO_TOKEN,
    IMPLEMENTATION_GO_TOKEN,
    load_authorization_ratification_v0,
    load_versioned_hypothesis_binding_v0,
    materialize_portfolio_binding_contract_v0,
    run_baseline_offline_economic_evaluation_v0,
    run_full_offline_economic_evaluation_v0,
    run_offline_economic_evaluation_execution_dispatch_v0,
    validate_implementation_go_token_v0,
)
from src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_portfolio_binding_v0 import (
    AGGREGATION_POLICY_VERSION,
    BOUND_PORTFOLIO_BINDING_STATUS,
    PORTFOLIO_BINDING_REQUIRED_FIELDS,
    PRE_PORTFOLIO_BINDING_DIGEST,
    REASON_BITCOIN_INSTRUMENT_SELECTION_FORBIDDEN,
    REASON_NONDETERMINISTIC_SELECTION_FORBIDDEN,
    REASON_PORTFOLIO_BINDING_DIGEST_MISMATCH,
    REASON_PORTFOLIO_POLICY_NOT_BOUND,
    REASON_PORTFOLIO_POLICY_VERSION_UNKNOWN,
    build_aggregation_policy_v0,
    build_exit_policy_v0,
    build_holding_policy_v0,
    build_portfolio_implementation_bindings_v0,
    build_portfolio_policy_contracts_v0,
    build_selection_policy_v0,
    build_portfolio_weighting_policy_v0,
    compute_aggregation_policy_digest_v0,
    validate_portfolio_implementation_bindings_v0,
)
from src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_score_and_ranking_contract_v0 import (
    materialize_and_validate_score_and_ranking_contract_v0,
    materialize_score_and_ranking_contract_v0,
)
from src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_versioned_hypothesis_binding_v0 import (
    materialize_and_validate_versioned_hypothesis_binding_v0,
    materialize_versioned_hypothesis_binding_v0,
    materializer_to_binder_roundtrip_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNNER = (
    REPO_ROOT / "scripts/ops/run_cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_"
    "economic_evaluation_execution_v0.py"
)


class TestPortfolioPolicyMaterialization:
    def test_all_five_policies_bound(self) -> None:
        bindings = build_portfolio_implementation_bindings_v0()
        for field in PORTFOLIO_BINDING_REQUIRED_FIELDS:
            assert bindings[field]["status"] == BOUND_PORTFOLIO_BINDING_STATUS
            assert bindings[field]["policy"]

    def test_portfolio_bindings_validator_pass(self) -> None:
        ok, reasons = validate_portfolio_implementation_bindings_v0(
            build_portfolio_implementation_bindings_v0()
        )
        assert ok, reasons

    def test_deterministic_double_materialization(self) -> None:
        first = build_portfolio_implementation_bindings_v0()
        second = build_portfolio_implementation_bindings_v0()
        assert first == second

    def test_hypothesis_binding_complete_after_portfolio_binding(self) -> None:
        result = materialize_and_validate_versioned_hypothesis_binding_v0()
        assert result.validation_verdict.value == "ACCEPTED_COMPLETE"
        envelope = result.binding
        assert envelope["binding_digest"] != PRE_PORTFOLIO_BINDING_DIGEST
        assert envelope["pre_ratified_binding_digest"] == PRE_PORTFOLIO_BINDING_DIGEST

    def test_score_ranking_contract_complete(self) -> None:
        result = materialize_and_validate_score_and_ranking_contract_v0()
        assert result.validation_verdict.value == "ACCEPTED_COMPLETE"

    def test_materializer_to_binder_roundtrip_pass(self) -> None:
        envelope = materialize_versioned_hypothesis_binding_v0()
        roundtrip = materializer_to_binder_roundtrip_v0(envelope)
        assert roundtrip["materializer_to_binder_roundtrip_pass"] is True


class TestPortfolioPolicyFailClosed:
    def test_missing_policy_blocks(self) -> None:
        bindings = build_portfolio_implementation_bindings_v0()
        stale = deepcopy(bindings)
        del stale["selection_policy"]
        ok, reasons = validate_portfolio_implementation_bindings_v0(stale)
        assert not ok
        assert any("MISSING_PORTFOLIO_POLICY" in item for item in reasons)

    def test_unknown_policy_version_blocks(self) -> None:
        bindings = build_portfolio_implementation_bindings_v0()
        stale = deepcopy(bindings)
        stale["selection_policy"] = deepcopy(stale["selection_policy"])
        stale["selection_policy"]["policy"] = deepcopy(stale["selection_policy"]["policy"])
        stale["selection_policy"]["policy"]["policy_version"] = "unknown.v99"
        ok, reasons = validate_portfolio_implementation_bindings_v0(stale)
        assert not ok
        assert any(REASON_PORTFOLIO_POLICY_VERSION_UNKNOWN in item for item in reasons)

    def test_invalid_digest_blocks(self) -> None:
        bindings = build_portfolio_implementation_bindings_v0()
        stale = deepcopy(bindings)
        stale["holding_policy"] = deepcopy(stale["holding_policy"])
        stale["holding_policy"]["binding_digest"] = "f" * 64
        ok, reasons = validate_portfolio_implementation_bindings_v0(stale)
        assert not ok
        assert any(REASON_PORTFOLIO_BINDING_DIGEST_MISMATCH in item for item in reasons)

    def test_bitcoin_selection_forbidden(self) -> None:
        policy = build_selection_policy_v0()
        stale = deepcopy(policy)
        stale["bitcoin_instruments_forbidden"] = False
        from src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_portfolio_binding_v0 import (
            validate_selection_policy_v0,
        )

        ok, reasons = validate_selection_policy_v0(stale)
        assert not ok
        assert REASON_BITCOIN_INSTRUMENT_SELECTION_FORBIDDEN in reasons

    def test_nondeterministic_selection_forbidden(self) -> None:
        policy = build_selection_policy_v0()
        stale = deepcopy(policy)
        stale["nondeterministic_selection_forbidden"] = False
        from src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_portfolio_binding_v0 import (
            validate_selection_policy_v0,
        )

        ok, reasons = validate_selection_policy_v0(stale)
        assert not ok
        assert REASON_NONDETERMINISTIC_SELECTION_FORBIDDEN in reasons

    def test_missing_tie_break_blocks(self) -> None:
        policy = build_selection_policy_v0()
        stale = deepcopy(policy)
        stale["deterministic_tie_break"] = ""
        from src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_portfolio_binding_v0 import (
            validate_selection_policy_v0,
        )

        ok, reasons = validate_selection_policy_v0(stale)
        assert not ok
        assert "MISSING_DETERMINISTIC_TIE_BREAK" in reasons


class TestExposureInvariants:
    def test_weight_sum_and_exposure_invariants(self) -> None:
        weighting = build_portfolio_weighting_policy_v0()
        assert weighting["weight_sum_invariant"] == 1.0
        assert weighting["gross_exposure_cap"] == 1.0
        assert weighting["net_exposure_bounds"] == {"min": -1.0, "max": 1.0}
        assert weighting["risk_sizing_semantics_changed"] is False


class TestExecutionDispatchReadiness:
    def test_materialized_dispatch_accepts_portfolio_bindings(self) -> None:
        from src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_evaluation_authorization_ratification_v0 import (
            materialize_offline_economic_evaluation_authorization_ratification_v0,
        )

        binding = materialize_versioned_hypothesis_binding_v0()
        auth = materialize_offline_economic_evaluation_authorization_ratification_v0()
        dispatch = run_offline_economic_evaluation_execution_dispatch_v0(
            repo_root=REPO_ROOT,
            authorization_ratification=auth,
            go_token=EXECUTION_GO_TOKEN,
            versioned_binding=binding,
            verify_source_manifests=False,
            materialize_dataset=False,
        )
        assert dispatch.portfolio_bindings_valid is True
        assert not any(REASON_PORTFOLIO_POLICY_NOT_BOUND in item for item in dispatch.reason_codes)

    def test_implementation_go_still_blocks_evaluation(self) -> None:
        ok, _ = validate_implementation_go_token_v0(EXECUTION_GO_TOKEN)
        assert ok is False
        result = run_full_offline_economic_evaluation_v0(go_token=IMPLEMENTATION_GO_TOKEN)
        assert result.executed is False

    def test_baseline_still_blocked_pending_separate_authorization(self) -> None:
        binding = materialize_versioned_hypothesis_binding_v0()
        result = run_baseline_offline_economic_evaluation_v0(
            go_token=EXECUTION_GO_TOKEN,
            repo_root=REPO_ROOT,
            versioned_binding=binding,
        )
        assert result.executed is False

    def test_portfolio_contract_reports_complete(self) -> None:
        binding = materialize_versioned_hypothesis_binding_v0()
        contract = materialize_portfolio_binding_contract_v0(binding)
        assert contract["portfolio_bindings_valid"] is True
        assert contract["reason_codes"] == []


class TestProductionPathRunner:
    def test_canonical_runner_accepts_execution_go_without_evaluation(self) -> None:
        proc = subprocess.run(
            [
                sys.executable,
                str(RUNNER),
                "--confirm",
                EXECUTION_GO_TOKEN,
                "--primary-worktree",
                str(REPO_ROOT),
            ],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        assert proc.returncode == 0
        payload = json.loads(proc.stdout)
        assert payload["economic_evaluation_executed"] is False
        assert payload["baseline_executed"] is False


class TestAggregationPolicySemantics:
    def test_aggregation_uses_instrument_net_semantics(self) -> None:
        policy = build_aggregation_policy_v0()
        assert policy["schema_version"] == AGGREGATION_POLICY_VERSION
        assert policy["net_semantics"] == "inbound_sum_minus_outbound_sum"
        assert policy["partial_pairwise_coverage_policy"] == (
            "include_instrument_with_partial_incident_pairs"
        )

    def test_aggregation_digest_stable(self) -> None:
        first = compute_aggregation_policy_digest_v0()
        second = compute_aggregation_policy_digest_v0()
        assert first == second


class TestPolicyContractsBundle:
    def test_portfolio_policy_contracts_complete(self) -> None:
        contracts = build_portfolio_policy_contracts_v0()
        for field in PORTFOLIO_BINDING_REQUIRED_FIELDS:
            assert field in contracts
