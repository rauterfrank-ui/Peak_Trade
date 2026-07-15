"""Dispatch implementation contract tests for pairwise spillover v1 execution v0."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

import pytest

from src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_evaluation_authorization_ratification_v0 import (
    materialize_offline_economic_evaluation_authorization_ratification_v0,
)
from src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_evaluation_execution_v0 import (
    AUTHORITY_EFFECT,
    BOUND_PORTFOLIO_BINDING_STATUS,
    DISPATCH_IMPLEMENTATION_GO_TOKEN,
    EXECUTION_GO_TOKEN,
    IMPLEMENTATION_GO_TOKEN,
    PORTFOLIO_BINDING_REQUIRED_FIELDS,
    RATIFIED_BINDING_DIGEST,
    RATIFIED_DATASET_DIGEST,
    RATIFIED_UNIVERSE_DIGEST,
    REASON_BINDING_DIGEST_MISMATCH,
    REASON_DATASET_DIGEST_MISMATCH,
    REASON_ECONOMIC_EVALUATION_BLOCKED,
    REASON_ECONOMIC_EXECUTION_FORBIDDEN,
    REASON_GO_TOKEN_INVALID,
    REASON_PORTFOLIO_BINDING_DIGEST_MISMATCH,
    REASON_PORTFOLIO_BINDING_PENDING,
    REASON_UNIVERSE_DIGEST_MISMATCH,
    RUNNER_SCRIPT,
    RUNTIME_EFFECT,
    dispatch_result_to_dict,
    materialize_dispatch_contract_v0,
    materialize_portfolio_binding_contract_v0,
    run_baseline_offline_economic_evaluation_v0,
    run_full_offline_economic_evaluation_v0,
    run_offline_economic_evaluation_execution_dispatch_v0,
    validate_entry_point_go_token_v0,
    validate_portfolio_bindings_for_execution_dispatch_v0,
    verify_ratified_digests_v0,
)
from src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_score_and_ranking_contract_v0 import (
    materialize_score_and_ranking_contract_v0,
)
from src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_versioned_hypothesis_binding_v0 import (
    materialize_versioned_hypothesis_binding_v0,
)
from tests.research.fixtures.cross_sectional_relative_strength_v0.staging_builder import (
    write_bound_period_staging_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNNER_MODULE = REPO_ROOT / RUNNER_SCRIPT
_EXEC_GO = EXECUTION_GO_TOKEN
_INFRA_GO = IMPLEMENTATION_GO_TOKEN
_DISPATCH_IMPL_GO = DISPATCH_IMPLEMENTATION_GO_TOKEN
PY310_STAGING = pytest.mark.skipif(
    sys.version_info < (3, 10),
    reason="panel staging loader requires Python 3.10+ zip(strict=True)",
)


@pytest.fixture(name="complete_binding")
def fixture_complete_binding() -> dict:
    return materialize_versioned_hypothesis_binding_v0()


@pytest.fixture(name="authorization_ratification")
def fixture_authorization_ratification() -> dict:
    return materialize_offline_economic_evaluation_authorization_ratification_v0()


@pytest.fixture(name="bound_staging")
def fixture_bound_staging() -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="cs_pairwise_spillover_dispatch_v0_"))
    staging = write_bound_period_staging_v0(tmp)
    lifecycle = staging / "lifecycle"
    lifecycle.mkdir(parents=True, exist_ok=True)
    lifecycle.joinpath("SOURCE_REGISTRATION.json").write_text(
        '{"source_snapshot_ref":"test:fixture","source_snapshot_digest":"'
        + "a" * 64
        + '","registered":true}\n',
        encoding="utf-8",
    )
    return staging


def _bound_portfolio_binding(field: str, *, digest: str) -> dict[str, str]:
    return {
        "ref": field,
        "status": BOUND_PORTFOLIO_BINDING_STATUS,
        "binding_digest": digest,
    }


def _binding_with_bound_portfolio(complete_binding: dict) -> dict:
    bound = deepcopy(complete_binding)
    pending = deepcopy(bound["pending_implementation_bindings"])
    for index, field in enumerate(PORTFOLIO_BINDING_REQUIRED_FIELDS):
        pending[field] = _bound_portfolio_binding(field, digest=f"{index:064d}")
    bound["pending_implementation_bindings"] = pending
    return bound


class TestEntryPointDispatchRegistry:
    def test_execution_go_accepted_by_entry_point(self) -> None:
        ok, branch = validate_entry_point_go_token_v0(_EXEC_GO)
        assert ok is True
        assert branch == "EXECUTION_V0"

    def test_dispatch_implementation_go_accepted_by_entry_point(self) -> None:
        ok, branch = validate_entry_point_go_token_v0(_DISPATCH_IMPL_GO)
        assert ok is True
        assert branch == "DISPATCH_IMPLEMENTATION_V0"

    def test_implementation_go_accepted_by_entry_point(self) -> None:
        ok, branch = validate_entry_point_go_token_v0(_INFRA_GO)
        assert ok is True
        assert branch == "IMPLEMENTATION_V0"


class TestPortfolioBindingFailClosed:
    def test_missing_portfolio_binding_fails_closed(self, complete_binding: dict) -> None:
        stale = deepcopy(complete_binding)
        stale["pending_implementation_bindings"] = {}
        ok, reasons = validate_portfolio_bindings_for_execution_dispatch_v0(stale)
        assert ok is False
        assert any("MISSING_PORTFOLIO_BINDING" in reason for reason in reasons)

    def test_pending_portfolio_binding_fails_closed(self, complete_binding: dict) -> None:
        ok, reasons = validate_portfolio_bindings_for_execution_dispatch_v0(complete_binding)
        assert ok is False
        assert any(REASON_PORTFOLIO_BINDING_PENDING in reason for reason in reasons)

    def test_invalid_portfolio_binding_digest_rejected(self, complete_binding: dict) -> None:
        bound = _binding_with_bound_portfolio(complete_binding)
        contract = materialize_score_and_ranking_contract_v0(bound)
        ranking = dict(contract["ranking_contract"])
        for field in PORTFOLIO_BINDING_REQUIRED_FIELDS:
            ranking[f"{field}_binding_status"] = BOUND_PORTFOLIO_BINDING_STATUS
        contract = {**contract, "ranking_contract": ranking}
        field = PORTFOLIO_BINDING_REQUIRED_FIELDS[0]
        ok, reasons = validate_portfolio_bindings_for_execution_dispatch_v0(
            bound,
            contract,
            expected_portfolio_binding_digests={field: "f" * 64},
        )
        assert ok is False
        assert f"{REASON_PORTFOLIO_BINDING_DIGEST_MISMATCH}:{field}" in reasons

    def test_no_implicit_portfolio_defaults(self, complete_binding: dict) -> None:
        contract = materialize_portfolio_binding_contract_v0(complete_binding, repo_root=REPO_ROOT)
        assert contract["implicit_defaults_forbidden"] is True
        assert contract["portfolio_bindings_valid"] is False


class TestDigestBindingDuringDispatch:
    def test_binding_digest_mismatch_rejected(self, complete_binding: dict) -> None:
        stale = deepcopy(complete_binding)
        stale["binding_digest"] = "f" * 64
        ok, reasons = verify_ratified_digests_v0(
            stale,
            expected_binding_digest=RATIFIED_BINDING_DIGEST,
        )
        assert ok is False
        assert REASON_BINDING_DIGEST_MISMATCH in reasons

    def test_dataset_digest_mismatch_rejected(self, complete_binding: dict) -> None:
        stale = deepcopy(complete_binding)
        stale["dataset_digest"] = "f" * 64
        ok, reasons = verify_ratified_digests_v0(
            stale,
            expected_dataset_digest=RATIFIED_DATASET_DIGEST,
        )
        assert ok is False
        assert REASON_DATASET_DIGEST_MISMATCH in reasons

    def test_universe_digest_mismatch_rejected(self, complete_binding: dict) -> None:
        stale = deepcopy(complete_binding)
        stale["binding"]["pit_universe_binding"]["universe_digest"] = "f" * 64
        ok, reasons = verify_ratified_digests_v0(
            stale,
            expected_universe_digest=RATIFIED_UNIVERSE_DIGEST,
        )
        assert ok is False
        assert REASON_UNIVERSE_DIGEST_MISMATCH in reasons

    def test_semantic_binding_fields_unchanged(self, complete_binding: dict) -> None:
        roundtrip = materialize_versioned_hypothesis_binding_v0()
        assert roundtrip["binding_digest"] == complete_binding["binding_digest"]
        assert roundtrip["dataset_digest"] == complete_binding["dataset_digest"]
        assert roundtrip["score_family_policy"] == complete_binding["score_family_policy"]


class TestDispatchWithoutEvaluation:
    def test_implementation_go_cannot_execute_evaluation(self) -> None:
        result = run_full_offline_economic_evaluation_v0(go_token=_INFRA_GO)
        assert result.executed is False
        assert REASON_GO_TOKEN_INVALID in result.reason_codes

    def test_execution_dispatch_blocked_on_pending_portfolio_bindings(
        self,
        authorization_ratification: dict,
        complete_binding: dict,
    ) -> None:
        dispatch = run_offline_economic_evaluation_execution_dispatch_v0(
            repo_root=REPO_ROOT,
            authorization_ratification=authorization_ratification,
            go_token=_EXEC_GO,
            versioned_binding=complete_binding,
            verify_source_manifests=False,
            materialize_dataset=False,
        )
        assert dispatch.economic_evaluation_executed is False
        assert dispatch.baseline_executed is False
        assert dispatch.robustness_executed is False
        assert dispatch.dispatch_accepted is False
        assert any(REASON_PORTFOLIO_BINDING_PENDING in item for item in dispatch.reason_codes)

    def test_full_evaluation_routes_to_dispatch_and_fails_closed(
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
        assert any(REASON_PORTFOLIO_BINDING_PENDING in item for item in result.reason_codes)

    def test_baseline_not_executed_during_dispatch_scope(
        self,
        authorization_ratification: dict,
        complete_binding: dict,
    ) -> None:
        result = run_baseline_offline_economic_evaluation_v0(
            go_token=_EXEC_GO,
            repo_root=REPO_ROOT,
            authorization_ratification=authorization_ratification,
            versioned_binding=complete_binding,
        )
        assert result.executed is False
        assert any(REASON_PORTFOLIO_BINDING_PENDING in item for item in result.reason_codes)

    def test_bound_portfolio_still_blocks_evaluation_until_separate_authorization(
        self,
        authorization_ratification: dict,
        complete_binding: dict,
    ) -> None:
        from src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_evaluation_execution_v0 import (
            ExecutionDispatchTerminalStatus,
            OfflineEconomicEvaluationDispatchResultV0,
        )

        accepted_dispatch = OfflineEconomicEvaluationDispatchResultV0(
            status=ExecutionDispatchTerminalStatus.DISPATCH_PRECHECK_PASSED_STOPPED_BEFORE_EVALUATION,
            dispatch_accepted=True,
            precheck_passed=True,
            portfolio_bindings_valid=True,
            source_manifests_verified=True,
            bound_dataset_materialized=True,
            dataset_period_match=True,
            panel_data_digest="a" * 64,
            reason_codes=(),
            baseline_executed=False,
            robustness_executed=False,
            economic_evaluation_executed=False,
            authority_effect=AUTHORITY_EFFECT,
            runtime_effect=RUNTIME_EFFECT,
            dispatcher_owner="test.dispatch",
            baseline_phase_owner="test.baseline",
            robustness_phase_owner="test.robustness",
        )
        with patch(
            "src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_"
            "economic_evaluation_execution_v0.run_offline_economic_evaluation_execution_dispatch_v0",
            return_value=accepted_dispatch,
        ):
            result = run_full_offline_economic_evaluation_v0(
                go_token=_EXEC_GO,
                repo_root=REPO_ROOT,
                authorization_ratification=authorization_ratification,
                versioned_binding=complete_binding,
                verify_source_manifests=False,
                materialize_dataset=False,
            )
        assert result.executed is False
        assert REASON_ECONOMIC_EVALUATION_BLOCKED in result.reason_codes


class TestRunnerEntryPoint:
    def test_execution_go_accepted_by_canonical_runner(self) -> None:
        proc = subprocess.run(
            [
                sys.executable,
                str(RUNNER_MODULE),
                "--confirm",
                _EXEC_GO,
                "--primary-worktree",
                str(REPO_ROOT),
            ],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        assert proc.returncode == 0
        assert "full_economic_evaluation_not_authorized_in_implementation_runner" not in proc.stderr
        payload = json.loads(proc.stdout)
        assert payload["economic_evaluation_executed"] is False
        assert payload["baseline_executed"] is False
        assert payload["robustness_executed"] is False

    @PY310_STAGING
    def test_implementation_go_still_runs_infrastructure_only(self) -> None:
        proc = subprocess.run(
            [
                sys.executable,
                str(RUNNER_MODULE),
                "--confirm",
                _INFRA_GO,
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


class TestImportBoundary:
    FORBIDDEN_RUNTIME_IMPORT_PREFIXES = (
        "src.execution",
        "src.scheduler",
        "src.broker",
    )

    def test_no_runtime_imports_in_harness(self) -> None:
        source = (
            REPO_ROOT
            / "src/research/cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_"
            "economic_evaluation_execution_v0.py"
        ).read_text(encoding="utf-8")
        for prefix in self.FORBIDDEN_RUNTIME_IMPORT_PREFIXES:
            assert prefix not in source

    def test_no_runtime_imports_in_runner(self) -> None:
        source = RUNNER_MODULE.read_text(encoding="utf-8")
        for prefix in self.FORBIDDEN_RUNTIME_IMPORT_PREFIXES:
            assert prefix not in source

    def test_no_runtime_or_authority_effect(self) -> None:
        assert AUTHORITY_EFFECT == "NONE"
        assert RUNTIME_EFFECT == "NONE"


class TestDeterministicDispatchOutputs:
    def test_repeated_fixture_execution_produces_identical_normalized_outputs(
        self,
        authorization_ratification: dict,
        complete_binding: dict,
    ) -> None:
        kwargs = {
            "repo_root": REPO_ROOT,
            "authorization_ratification": authorization_ratification,
            "go_token": _EXEC_GO,
            "versioned_binding": complete_binding,
            "verify_source_manifests": False,
            "materialize_dataset": False,
        }
        first = dispatch_result_to_dict(
            run_offline_economic_evaluation_execution_dispatch_v0(**kwargs)
        )
        second = dispatch_result_to_dict(
            run_offline_economic_evaluation_execution_dispatch_v0(**kwargs)
        )
        assert first == second

    def test_canonical_dispatcher_invoked_exactly_once(self) -> None:
        with patch(
            "src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_"
            "economic_evaluation_execution_v0.run_offline_economic_evaluation_execution_dispatch_v0"
        ) as mocked:
            mocked.return_value = run_offline_economic_evaluation_execution_dispatch_v0(
                repo_root=REPO_ROOT,
                authorization_ratification=materialize_offline_economic_evaluation_authorization_ratification_v0(),
                go_token=_EXEC_GO,
                versioned_binding=materialize_versioned_hypothesis_binding_v0(),
                verify_source_manifests=False,
                materialize_dataset=False,
            )
            run_full_offline_economic_evaluation_v0(
                go_token=_EXEC_GO,
                repo_root=REPO_ROOT,
                authorization_ratification=materialize_offline_economic_evaluation_authorization_ratification_v0(),
                versioned_binding=materialize_versioned_hypothesis_binding_v0(),
                verify_source_manifests=False,
                materialize_dataset=False,
            )
            assert mocked.call_count == 1


class TestDispatchContractMaterialization:
    def test_dispatch_contract_exports_required_owners(self) -> None:
        contract = materialize_dispatch_contract_v0()
        assert contract["economic_evaluation_executed"] is False
        assert contract["baseline_executed"] is False
        assert contract["robustness_executed"] is False
        assert contract["execution_go_token"] == _EXEC_GO
        assert contract["dispatch_implementation_go_token"] == _DISPATCH_IMPL_GO

    def test_implementation_dry_run_still_rejects_execution_go(
        self,
        bound_staging: Path,
        authorization_ratification: dict,
        complete_binding: dict,
    ) -> None:
        from src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_evaluation_execution_v0 import (
            run_full_evaluation_entrypoint_dry_run_v1,
        )
        from tests.research.fixtures.cross_sectional_relative_strength_v0.fixture_builder import (
            build_synthetic_panel_series_v0,
        )

        panel = build_synthetic_panel_series_v0()
        result = run_full_evaluation_entrypoint_dry_run_v1(
            repo_root=REPO_ROOT,
            authorization_ratification=authorization_ratification,
            staging_root=bound_staging,
            panel_series=panel,
            versioned_binding=complete_binding,
            go_token=_EXEC_GO,
        )
        assert result.economic_evaluation_executed is False
        assert REASON_ECONOMIC_EXECUTION_FORBIDDEN in result.reason_codes
