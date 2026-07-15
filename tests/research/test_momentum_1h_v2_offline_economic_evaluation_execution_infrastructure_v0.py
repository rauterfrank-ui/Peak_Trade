"""Contract tests for momentum 1h v2 offline economic evaluation execution infrastructure v0."""

from __future__ import annotations

import ast
from copy import deepcopy
from pathlib import Path

from unittest.mock import patch

import pytest

from src.research.momentum_1h_v2_offline_economic_evaluation_authorization_ratification_v0 import (
    materialize_offline_economic_evaluation_authorization_ratification_v0,
)
from src.research.momentum_1h_v2_offline_economic_evaluation_execution_v0 import (
    AUTHORITY_EFFECT,
    EXECUTION_GO_TOKEN,
    INFRASTRUCTURE_GO_TOKEN,
    RATIFIED_BINDING_DIGEST,
    RATIFIED_DATASET_DIGEST,
    REASON_BINDING_DIGEST_MISMATCH,
    REASON_DATASET_DIGEST_MISMATCH,
    REASON_BASELINE_CALLABLE_WIRING_ONLY_ACKNOWLEDGED,
    REASON_BASELINE_WIRING_VERIFIED,
    REASON_DISPATCH_PRECHECK_PASSED_STOPPED_BEFORE_EVALUATION,
    REASON_ECONOMIC_EXECUTION_FORBIDDEN,
    REASON_GO_TOKEN_INVALID,
    RUNNER_SCRIPT,
    RUNTIME_EFFECT,
    PhaseExecutionBlockedResultV0,
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
from src.research.momentum_1h_v2_versioned_research_binding_v0 import (
    materialize_versioned_research_binding_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
EXECUTION_MODULE = (
    REPO_ROOT / "src/research/momentum_1h_v2_offline_economic_evaluation_execution_v0.py"
)
RUNNER_MODULE = REPO_ROOT / RUNNER_SCRIPT
MATERIALIZER_MODULE = None  # not required for momentum v2 infrastructure repair scope
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

    def test_materializer_module_not_required_in_repair_scope(self) -> None:
        assert MATERIALIZER_MODULE is None

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
        assert AUTHORITY_EFFECT == "OFFLINE_EVALUATION_AUTHORIZATION_ONLY"
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
        assert result.authority_effect == "OFFLINE_EVALUATION_AUTHORIZATION_ONLY"
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

    def test_full_evaluation_chains_to_baseline_after_dispatch_accepted(
        self,
        authorization_ratification: dict,
        complete_binding: dict,
    ) -> None:
        owner_ref = (
            "versioned_final_fleet_bindings_offline_economic_evaluation_v0."
            "_run_candidate_with_runtime_config_v0"
        )
        baseline_result = PhaseExecutionBlockedResultV0(
            phase="BASELINE",
            executed=False,
            blocked=False,
            wiring_verified=True,
            canonical_owner=owner_ref,
            reason_codes=(
                REASON_BASELINE_WIRING_VERIFIED,
                REASON_BASELINE_CALLABLE_WIRING_ONLY_ACKNOWLEDGED,
            ),
            authority_effect="OFFLINE_EVALUATION_AUTHORIZATION_ONLY",
            runtime_effect="NONE",
            economic_evaluation_executed=False,
        )
        with patch(
            "src.research.momentum_1h_v2_offline_economic_evaluation_execution_v0."
            "run_baseline_offline_economic_evaluation_v0",
            return_value=baseline_result,
        ) as baseline_spy:
            result = run_full_offline_economic_evaluation_v0(
                go_token=EXECUTION_GO_TOKEN,
                repo_root=REPO_ROOT,
                authorization_ratification=authorization_ratification,
                versioned_binding=complete_binding,
            )

        baseline_spy.assert_called_once()
        assert result.blocked is False
        assert result.wiring_verified is True
        assert result.canonical_owner == owner_ref
        assert REASON_DISPATCH_PRECHECK_PASSED_STOPPED_BEFORE_EVALUATION not in result.reason_codes


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


class TestMomentumV2CandidateIdentity:
    def test_candidate_identity_exact(self) -> None:
        from src.research.momentum_1h_v2_versioned_research_binding_v0 import (
            RESEARCH_SCOPE,
            BINDING_GENERATION,
            EXPECTED_BINDING_DIGEST,
        )

        assert RESEARCH_SCOPE == "momentum_1h/v2"
        assert BINDING_GENERATION == "post_pr4921"
        assert RATIFIED_BINDING_DIGEST == EXPECTED_BINDING_DIGEST

    def test_no_v1_fallback_imports(self) -> None:
        source = EXECUTION_MODULE.read_text(encoding="utf-8")
        assert "momentum_1h_v1_offline_economic_evaluation_execution_v0" not in source
        assert "run_momentum_1h_execution_v0" not in source

    def test_no_trend_following_v2_fallback_imports(self) -> None:
        tree = ast.parse(EXECUTION_MODULE.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert (
                        "trend_following_v2_offline_economic_evaluation_execution_v0"
                        not in alias.name
                    )
            elif isinstance(node, ast.ImportFrom) and node.module:
                assert (
                    "trend_following_v2_offline_economic_evaluation_execution_v0" not in node.module
                )


class TestMandatoryBoundaryBinding:
    def test_mandatory_boundary_state_files_bound(self) -> None:
        from src.research.momentum_1h_v2_offline_economic_evaluation_execution_v0 import (
            build_mandatory_boundary_binding_proof_v0,
        )

        proof = build_mandatory_boundary_binding_proof_v0(repo_root=REPO_ROOT)
        assert proof["all_gates_bound"] is True
        assert proof["capital_risk_sizing_gate_bound"] is True
        assert proof["canonical_order_intent_gate_bound"] is True
        assert proof["safety_kernel_gate_bound"] is True
        assert proof["killswitch_gate_bound"] is True
        assert proof["reconciliation_gate_bound"] is True


class TestInfrastructureRepairGoToken:
    def test_infrastructure_repair_go_token(self) -> None:
        from src.research.momentum_1h_v2_offline_economic_evaluation_execution_v0 import (
            INFRASTRUCTURE_GO_TOKEN,
        )

        assert INFRASTRUCTURE_GO_TOKEN == (
            "GO_MOMENTUM_1H_V2_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_INFRASTRUCTURE_REPAIR_V0"
        )
