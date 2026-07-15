"""Dispatch implementation contract tests for trend_following v2 execution v0."""

from __future__ import annotations

import json
import subprocess
import sys
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

import pytest

from src.research.trend_following_v2_offline_economic_evaluation_authorization_ratification_v0 import (
    materialize_offline_economic_evaluation_authorization_ratification_v0,
)
from src.research.trend_following_v2_offline_economic_evaluation_execution_v0 import (
    AUTHORITY_EFFECT,
    DISPATCH_IMPLEMENTATION_GO_TOKEN,
    EXECUTION_GO_TOKEN,
    INFRASTRUCTURE_GO_TOKEN,
    RATIFIED_BINDING_DIGEST,
    RATIFIED_DATASET_DIGEST,
    REASON_BINDING_DIGEST_MISMATCH,
    REASON_DATASET_DIGEST_MISMATCH,
    REASON_DISPATCH_PRECHECK_PASSED_STOPPED_BEFORE_EVALUATION,
    REASON_ECONOMIC_EXECUTION_FORBIDDEN,
    REASON_GO_TOKEN_INVALID,
    RUNNER_SCRIPT,
    RUNTIME_EFFECT,
    dispatch_result_to_dict,
    materialize_dispatch_contract_v0,
    run_full_evaluation_entrypoint_dry_run_v1,
    run_full_offline_economic_evaluation_v0,
    run_offline_economic_evaluation_execution_dispatch_v0,
    validate_entry_point_go_token_v0,
    verify_ratified_digests_v0,
)
from src.research.trend_following_v2_versioned_research_binding_v0 import (
    materialize_versioned_research_binding_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNNER_MODULE = REPO_ROOT / RUNNER_SCRIPT
MATERIALIZER_MODULE = (
    REPO_ROOT / "scripts/ops/materialize_trend_following_v2_offline_economic_evaluation_execution_"
    "dispatch_implementation_v0.py"
)
_EXEC_GO = EXECUTION_GO_TOKEN
_INFRA_GO = INFRASTRUCTURE_GO_TOKEN
_DISPATCH_IMPL_GO = DISPATCH_IMPLEMENTATION_GO_TOKEN


@pytest.fixture(name="complete_binding")
def fixture_complete_binding() -> dict:
    return materialize_versioned_research_binding_v0(repo_root=REPO_ROOT)


@pytest.fixture(name="authorization_ratification")
def fixture_authorization_ratification(complete_binding: dict) -> dict:
    return materialize_offline_economic_evaluation_authorization_ratification_v0(
        repo_root=REPO_ROOT,
        versioned_binding=complete_binding,
    )


class TestEntryPointDispatchRegistry:
    def test_execution_go_accepted_by_entry_point(self) -> None:
        ok, branch = validate_entry_point_go_token_v0(_EXEC_GO)
        assert ok is True
        assert branch == "EXECUTION_V0"

    def test_dispatch_implementation_go_accepted_by_entry_point(self) -> None:
        ok, branch = validate_entry_point_go_token_v0(_DISPATCH_IMPL_GO)
        assert ok is True
        assert branch == "DISPATCH_IMPLEMENTATION_V0"

    def test_infrastructure_go_accepted_by_entry_point(self) -> None:
        ok, branch = validate_entry_point_go_token_v0(_INFRA_GO)
        assert ok is True
        assert branch == "INFRASTRUCTURE_V0"


class TestDigestBindingDuringDispatch:
    def test_binding_digest_mismatch_rejected(self, complete_binding: dict) -> None:
        stale = deepcopy(complete_binding)
        stale["binding_digest"] = "f" * 64
        ok, reasons = verify_ratified_digests_v0(stale)
        assert ok is False
        assert REASON_BINDING_DIGEST_MISMATCH in reasons

    def test_dataset_digest_mismatch_rejected(self, complete_binding: dict) -> None:
        stale = deepcopy(complete_binding)
        stale["dataset_digest"] = "f" * 64
        ok, reasons = verify_ratified_digests_v0(stale)
        assert ok is False
        assert REASON_DATASET_DIGEST_MISMATCH in reasons


class TestDispatchWithoutEvaluation:
    def test_infrastructure_go_cannot_execute_evaluation(self) -> None:
        result = run_full_offline_economic_evaluation_v0(go_token=_INFRA_GO, repo_root=REPO_ROOT)
        assert result.executed is False
        assert REASON_GO_TOKEN_INVALID in result.reason_codes

    def test_execution_dispatch_accepted_without_evaluation(
        self,
        authorization_ratification: dict,
        complete_binding: dict,
    ) -> None:
        dispatch = run_offline_economic_evaluation_execution_dispatch_v0(
            repo_root=REPO_ROOT,
            authorization_ratification=authorization_ratification,
            go_token=_EXEC_GO,
            versioned_binding=complete_binding,
            verify_source_manifests=True,
        )
        assert dispatch.economic_evaluation_executed is False
        assert dispatch.baseline_executed is False
        assert dispatch.robustness_executed is False
        assert dispatch.dispatch_accepted is True

    def test_full_evaluation_routes_to_dispatch(
        self,
        authorization_ratification: dict,
        complete_binding: dict,
    ) -> None:
        result = run_full_offline_economic_evaluation_v0(
            go_token=_EXEC_GO,
            repo_root=REPO_ROOT,
            authorization_ratification=authorization_ratification,
            versioned_binding=complete_binding,
            verify_source_manifests=True,
        )
        assert result.executed is False
        assert result.blocked is False
        assert result.wiring_verified is True
        assert REASON_DISPATCH_PRECHECK_PASSED_STOPPED_BEFORE_EVALUATION in result.reason_codes

    def test_implementation_dry_run_rejects_execution_go(
        self,
        authorization_ratification: dict,
        complete_binding: dict,
    ) -> None:
        result = run_full_evaluation_entrypoint_dry_run_v1(
            repo_root=REPO_ROOT,
            authorization_ratification=authorization_ratification,
            versioned_binding=complete_binding,
            go_token=_EXEC_GO,
        )
        assert result.economic_evaluation_executed is False
        assert REASON_ECONOMIC_EXECUTION_FORBIDDEN in result.reason_codes


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
            "verify_source_manifests": True,
        }
        first = dispatch_result_to_dict(
            run_offline_economic_evaluation_execution_dispatch_v0(**kwargs)
        )
        second = dispatch_result_to_dict(
            run_offline_economic_evaluation_execution_dispatch_v0(**kwargs)
        )
        assert first == second

    def test_canonical_dispatcher_invoked_exactly_once(
        self,
        authorization_ratification: dict,
        complete_binding: dict,
    ) -> None:
        with patch(
            "src.research.trend_following_v2_offline_economic_evaluation_execution_v0."
            "run_offline_economic_evaluation_execution_dispatch_v0"
        ) as mocked:
            mocked.return_value = run_offline_economic_evaluation_execution_dispatch_v0(
                repo_root=REPO_ROOT,
                authorization_ratification=authorization_ratification,
                go_token=_EXEC_GO,
                versioned_binding=complete_binding,
                verify_source_manifests=True,
            )
            run_full_offline_economic_evaluation_v0(
                go_token=_EXEC_GO,
                repo_root=REPO_ROOT,
                authorization_ratification=authorization_ratification,
                versioned_binding=complete_binding,
                verify_source_manifests=True,
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
        assert contract["entry_point_status"] == "EXECUTION_DISPATCH_WIRING_V0"


class TestRunnerAndMaterializerExist:
    def test_runner_module_exists(self) -> None:
        assert RUNNER_MODULE.is_file()

    def test_materializer_module_exists(self) -> None:
        assert MATERIALIZER_MODULE.is_file()

    def test_dispatch_implementation_go_accepted_by_runner(self) -> None:
        proc = subprocess.run(
            [
                sys.executable,
                str(RUNNER_MODULE),
                "--confirm",
                _DISPATCH_IMPL_GO,
                "--primary-worktree",
                str(REPO_ROOT),
            ],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        assert proc.returncode == 0, proc.stderr
        payload = json.loads(proc.stdout)
        assert payload["verdict"] == "EXECUTION_DISPATCH_IMPLEMENTATION_COMPLETE"
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
            / "src/research/trend_following_v2_offline_economic_evaluation_execution_v0.py"
        ).read_text(encoding="utf-8")
        for prefix in self.FORBIDDEN_RUNTIME_IMPORT_PREFIXES:
            assert prefix not in source

    def test_no_runtime_or_authority_effect(self) -> None:
        assert AUTHORITY_EFFECT == "NONE"
        assert RUNTIME_EFFECT == "NONE"
