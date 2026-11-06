"""Contract tests for trend_following v2 offline economic evaluation execution infrastructure v0."""

from __future__ import annotations

import ast
from copy import deepcopy
from pathlib import Path

import pytest

from src.research.trend_following_v2_offline_economic_evaluation_authorization_ratification_v0 import (
    materialize_offline_economic_evaluation_authorization_ratification_v0,
)
from src.research.trend_following_v2_offline_economic_evaluation_execution_v0 import (
    AUTHORITY_EFFECT,
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
    entrypoint_result_to_dict,
    load_ops_evaluation_config_v0,
    materialize_execution_contract_v0,
    run_contract_smoke_evaluation_v0,
    run_full_evaluation_entrypoint_dry_run_v1,
    run_full_offline_economic_evaluation_v0,
    validate_entry_point_go_token_v0,
    validate_execution_go_token_v0,
    validate_infrastructure_go_token_v0,
    verify_execution_start_state_v0,
    verify_ratified_digests_v0,
)
from src.research.trend_following_v2_versioned_research_binding_v0 import (
    materialize_versioned_research_binding_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
EXECUTION_MODULE = (
    REPO_ROOT / "src/research/trend_following_v2_offline_economic_evaluation_execution_v0.py"
)
RUNNER_MODULE = REPO_ROOT / RUNNER_SCRIPT
MATERIALIZER_MODULE = (
    REPO_ROOT
    / "scripts/ops/materialize_trend_following_v2_offline_economic_evaluation_execution_infrastructure_v0.py"
)
FORBIDDEN_RUNTIME_IMPORT_PREFIXES = (
    "src.execution",
    "src.scheduler",
    "src.broker",
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


class TestCanonicalEntryPointExists:
    def test_harness_module_exists(self) -> None:
        assert EXECUTION_MODULE.is_file()

    def test_runner_module_exists(self) -> None:
        assert RUNNER_MODULE.is_file()

    def test_materializer_module_exists(self) -> None:
        assert MATERIALIZER_MODULE.is_file()

    def test_import_is_side_effect_free(self) -> None:
        tree = ast.parse(EXECUTION_MODULE.read_text(encoding="utf-8"))
        for node in tree.body:
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
                pytest.fail("module import must not invoke call expressions at top level")


class TestGoTokenEnforcement:
    def test_infrastructure_go_token_accepted(self) -> None:
        ok, reasons = validate_infrastructure_go_token_v0(INFRASTRUCTURE_GO_TOKEN)
        assert ok, reasons

    def test_execution_go_token_accepted(self) -> None:
        ok, reasons = validate_execution_go_token_v0(EXECUTION_GO_TOKEN)
        assert ok, reasons

    def test_wrong_go_token_rejected(self) -> None:
        ok, reasons = validate_infrastructure_go_token_v0("GO_WRONG_TOKEN")
        assert not ok
        assert REASON_GO_TOKEN_INVALID in reasons

    def test_entry_point_dispatch(self) -> None:
        ok, branch = validate_entry_point_go_token_v0(INFRASTRUCTURE_GO_TOKEN)
        assert ok and branch == "INFRASTRUCTURE_V0"
        ok, branch = validate_entry_point_go_token_v0(EXECUTION_GO_TOKEN)
        assert ok and branch == "EXECUTION_V0"


class TestOfflineBoundary:
    def test_no_runtime_authority_effect_constants(self) -> None:
        assert AUTHORITY_EFFECT == "NONE"
        assert RUNTIME_EFFECT == "NONE"

    def test_futures_only_and_bitcoin_excluded(self, complete_binding: dict) -> None:
        instrument_binding = complete_binding["binding"]["instrument_binding"]
        assert instrument_binding["futures_only"] is True
        assert instrument_binding["bitcoin_direction_allowed"] is False


class TestDigestBinding:
    def test_binding_digest_matches_ratified(self, complete_binding: dict) -> None:
        assert complete_binding["binding_digest"] == RATIFIED_BINDING_DIGEST

    def test_dataset_digest_matches_ratified(self, complete_binding: dict) -> None:
        assert complete_binding["dataset_digest"] == RATIFIED_DATASET_DIGEST

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


class TestAuthorizationAndBindingValidation:
    def test_start_state_verification_accepts_ratified_bindings(
        self,
        authorization_ratification: dict,
        complete_binding: dict,
    ) -> None:
        result = verify_execution_start_state_v0(
            repo_root=REPO_ROOT,
            authorization_ratification=authorization_ratification,
            versioned_binding=complete_binding,
        )
        assert result.valid is True
        assert result.fail_reasons == ()

    def test_ops_config_binding_digest_matches(
        self,
        complete_binding: dict,
    ) -> None:
        cfg = load_ops_evaluation_config_v0(REPO_ROOT)
        assert cfg["binding_digest"] == complete_binding["binding_digest"]


class TestContractSmokeAndDryRun:
    def test_contract_smoke_no_economic_execution(
        self,
        authorization_ratification: dict,
        complete_binding: dict,
    ) -> None:
        result = run_contract_smoke_evaluation_v0(
            repo_root=REPO_ROOT,
            versioned_binding=complete_binding,
            authorization_ratification=authorization_ratification,
        )
        assert result.economic_evaluation_executed is False
        assert result.authority_effect == "NONE"
        assert result.execution_infrastructure_complete is True

    def test_full_evaluation_entrypoint_dry_run_stops_before_execution(
        self,
        authorization_ratification: dict,
        complete_binding: dict,
    ) -> None:
        result = run_full_evaluation_entrypoint_dry_run_v1(
            repo_root=REPO_ROOT,
            authorization_ratification=authorization_ratification,
            versioned_binding=complete_binding,
            go_token=INFRASTRUCTURE_GO_TOKEN,
        )
        assert result.economic_evaluation_executed is False
        assert result.dry_run_stopped_before_execution is True
        assert result.precheck_passed is True

    def test_execution_go_rejected_in_infrastructure_dry_run(
        self,
        authorization_ratification: dict,
        complete_binding: dict,
    ) -> None:
        result = run_full_evaluation_entrypoint_dry_run_v1(
            repo_root=REPO_ROOT,
            authorization_ratification=authorization_ratification,
            versioned_binding=complete_binding,
            go_token=EXECUTION_GO_TOKEN,
        )
        assert result.precheck_passed is False
        assert REASON_ECONOMIC_EXECUTION_FORBIDDEN in result.reason_codes


class TestNoExecutionDuringInfrastructure:
    def test_full_evaluation_blocked_without_execution_go(self) -> None:
        result = run_full_offline_economic_evaluation_v0(
            go_token=INFRASTRUCTURE_GO_TOKEN,
            repo_root=REPO_ROOT,
        )
        assert result.executed is False
        assert result.blocked is True

    def test_full_evaluation_wiring_verified_with_execution_go(
        self,
        authorization_ratification: dict,
        complete_binding: dict,
    ) -> None:
        result = run_full_offline_economic_evaluation_v0(
            go_token=EXECUTION_GO_TOKEN,
            repo_root=REPO_ROOT,
            authorization_ratification=authorization_ratification,
            versioned_binding=complete_binding,
        )
        assert result.executed is False
        assert result.blocked is False
        assert result.wiring_verified is True
        assert REASON_DISPATCH_PRECHECK_PASSED_STOPPED_BEFORE_EVALUATION in result.reason_codes


class TestMaterializationContract:
    def test_execution_contract_materialization(self) -> None:
        contract = materialize_execution_contract_v0()
        assert contract["economic_evaluation_executed"] is False
        assert contract["binding_digest"] == RATIFIED_BINDING_DIGEST
        assert contract["entry_point_status"] == "EXECUTION_DISPATCH_WIRING_V0"

    def test_entrypoint_result_roundtrip(
        self,
        authorization_ratification: dict,
        complete_binding: dict,
    ) -> None:
        result = run_full_evaluation_entrypoint_dry_run_v1(
            repo_root=REPO_ROOT,
            authorization_ratification=authorization_ratification,
            versioned_binding=complete_binding,
            go_token=INFRASTRUCTURE_GO_TOKEN,
        )
        payload = entrypoint_result_to_dict(result)
        assert payload["economic_evaluation_executed"] is False
        assert payload["precheck_passed"] is True


class TestImportBoundary:
    def test_no_forbidden_runtime_imports(self) -> None:
        source = EXECUTION_MODULE.read_text(encoding="utf-8")
        for prefix in FORBIDDEN_RUNTIME_IMPORT_PREFIXES:
            assert prefix not in source

    def test_runner_has_no_forbidden_runtime_imports(self) -> None:
        source = RUNNER_MODULE.read_text(encoding="utf-8")
        for prefix in FORBIDDEN_RUNTIME_IMPORT_PREFIXES:
            assert prefix not in source
