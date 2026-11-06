"""Reevaluation execution implementation contract tests for pairwise spillover v1."""

from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.ops.run_cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_evaluation_execution_v0 import (
    ALLOWED_CONFIRM_GO_TOKENS,
)
from src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_evaluation_authorization_ratification_v0 import (
    materialize_offline_economic_evaluation_authorization_ratification_v0,
)
from src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_evaluation_execution_v0 import (
    AUTHORITY_EFFECT,
    BASELINE_EVALUATOR_OWNER,
    CANONICAL_FULL_EVALUATION_CALLABLE,
    ENTRY_POINT_DISPATCH_REGISTRY,
    EXECUTION_GO_TOKEN,
    HARNESS_OWNER,
    RATIFIED_BINDING_DIGEST,
    REASON_GO_TOKEN_INVALID,
    REASON_GO_TOKEN_MISSING,
    REASON_REEVALUATION_EXECUTION_WIRING_VERIFIED,
    REASON_REEVALUATION_GO_REQUIRED,
    REEVALUATION_EXECUTION_GO_TOKEN,
    REEVALUATION_EXECUTION_IMPLEMENTATION_GO_TOKEN,
    RUNNER_SCRIPT,
    RUNTIME_EFFECT,
    build_cryptographic_identity_comparison,
    materialize_execution_contract_v0,
    run_full_offline_economic_evaluation_v0,
    validate_entry_point_go_token_v0,
    validate_evaluation_dispatch_go_token_v0,
    validate_execution_go_token_v0,
    validate_reevaluation_execution_go_token_v0,
    validate_reevaluation_execution_implementation_go_token_v0,
)
from src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_versioned_hypothesis_binding_v0 import (
    materialize_versioned_hypothesis_binding_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
_EXEC_GO = EXECUTION_GO_TOKEN
_REEVAL_EXEC_GO = REEVALUATION_EXECUTION_GO_TOKEN
_REEVAL_IMPL_GO = REEVALUATION_EXECUTION_IMPLEMENTATION_GO_TOKEN
EXECUTION_MODULE = (
    REPO_ROOT / "src/research/"
    "cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_"
    "evaluation_execution_v0.py"
)
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


class TestReevaluationGoTokenRegistration:
    def test_reevaluation_execution_go_token_accepted(self) -> None:
        ok, reasons = validate_reevaluation_execution_go_token_v0(_REEVAL_EXEC_GO)
        assert ok is True
        assert reasons == ()

    def test_reevaluation_execution_go_token_registered_in_allowed_tokens(self) -> None:
        assert _REEVAL_IMPL_GO in ALLOWED_CONFIRM_GO_TOKENS
        assert _REEVAL_EXEC_GO in ALLOWED_CONFIRM_GO_TOKENS

    def test_reevaluation_execution_go_token_registered_in_dispatch_registry(self) -> None:
        assert ENTRY_POINT_DISPATCH_REGISTRY[_REEVAL_EXEC_GO] == "REEVALUATION_EXECUTION_V0"
        assert (
            ENTRY_POINT_DISPATCH_REGISTRY[_REEVAL_IMPL_GO]
            == "REEVALUATION_EXECUTION_IMPLEMENTATION_V0"
        )

    def test_reevaluation_dispatch_selects_explicit_reevaluation_branch(self) -> None:
        ok, branch = validate_entry_point_go_token_v0(_REEVAL_EXEC_GO)
        assert ok is True
        assert branch == "REEVALUATION_EXECUTION_V0"


class TestReevaluationBranchWiring:
    def test_reevaluation_branch_reuses_canonical_evaluation_owner(
        self,
        authorization_ratification: dict,
        complete_binding: dict,
    ) -> None:
        result = run_full_offline_economic_evaluation_v0(
            go_token=_REEVAL_EXEC_GO,
            repo_root=REPO_ROOT,
            authorization_ratification=authorization_ratification,
            versioned_binding=complete_binding,
            verify_source_manifests=False,
            materialize_dataset=False,
        )
        assert result.canonical_owner == f"{HARNESS_OWNER}.{CANONICAL_FULL_EVALUATION_CALLABLE}"

    def test_reevaluation_branch_can_pass_required_reevaluation_stop(
        self,
        authorization_ratification: dict,
        complete_binding: dict,
    ) -> None:
        result = run_full_offline_economic_evaluation_v0(
            go_token=_REEVAL_EXEC_GO,
            repo_root=REPO_ROOT,
            authorization_ratification=authorization_ratification,
            versioned_binding=complete_binding,
            verify_source_manifests=False,
            materialize_dataset=False,
        )
        assert result.executed is False
        assert result.blocked is False
        assert result.wiring_verified is True
        assert REASON_REEVALUATION_GO_REQUIRED not in result.reason_codes
        assert REASON_REEVALUATION_EXECUTION_WIRING_VERIFIED in result.reason_codes

    def test_normal_execution_go_does_not_gain_reevaluation_authority(
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
        assert REASON_REEVALUATION_GO_REQUIRED in result.reason_codes
        assert REASON_REEVALUATION_EXECUTION_WIRING_VERIFIED not in result.reason_codes


class TestGoTokenRejection:
    def test_unknown_go_token_rejected(self) -> None:
        ok, reasons = validate_reevaluation_execution_go_token_v0("INVALID_GO_TOKEN")
        assert ok is False
        assert REASON_GO_TOKEN_INVALID in reasons

        ok_dispatch, dispatch_reasons = validate_evaluation_dispatch_go_token_v0("INVALID_GO_TOKEN")
        assert ok_dispatch is False
        assert REASON_GO_TOKEN_INVALID in dispatch_reasons

    def test_missing_go_token_rejected(self) -> None:
        ok, reasons = validate_reevaluation_execution_implementation_go_token_v0(None)
        assert ok is False
        assert REASON_GO_TOKEN_MISSING in reasons

        ok_exec, exec_reasons = validate_execution_go_token_v0(None)
        assert ok_exec is False
        assert REASON_GO_TOKEN_MISSING in exec_reasons


class TestOfflineBoundaryAndBindingInvariants:
    def test_offline_boundary_preserved(
        self,
        authorization_ratification: dict,
    ) -> None:
        assert authorization_ratification.get("offline_only") is True

    def test_no_binding_semantic_change(self, complete_binding: dict) -> None:
        second = materialize_versioned_hypothesis_binding_v0()
        assert complete_binding == second

    def test_no_binding_digest_change(self) -> None:
        identity = build_cryptographic_identity_comparison(REPO_ROOT)
        assert identity["CRYPTOGRAPHIC_BINDING_IDENTITY_CHANGED"] is False
        assert identity["binding_digest"] == RATIFIED_BINDING_DIGEST

    def test_economic_evaluation_not_executed_in_implementation_tests(
        self,
        authorization_ratification: dict,
        complete_binding: dict,
    ) -> None:
        result = run_full_offline_economic_evaluation_v0(
            go_token=_REEVAL_EXEC_GO,
            repo_root=REPO_ROOT,
            authorization_ratification=authorization_ratification,
            versioned_binding=complete_binding,
            verify_source_manifests=False,
            materialize_dataset=False,
        )
        assert result.executed is False

    def test_runtime_effect_none(self) -> None:
        assert RUNTIME_EFFECT == "NONE"

    def test_authority_effect_none(self) -> None:
        assert AUTHORITY_EFFECT == "NONE"


class TestImportBoundary:
    def test_no_runtime_import_boundary_violation(self) -> None:
        source = EXECUTION_MODULE.read_text(encoding="utf-8")
        for prefix in FORBIDDEN_RUNTIME_IMPORT_PREFIXES:
            assert prefix not in source

    def test_no_order_adapter_import_boundary_violation(self) -> None:
        source = RUNNER_MODULE.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imports = {
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module
        }
        assert not any(item.startswith("src.execution") for item in imports)

    def test_no_scheduler_import_boundary_violation(self) -> None:
        source = RUNNER_MODULE.read_text(encoding="utf-8")
        assert "src.scheduler" not in source


class TestEntryPointContract:
    def test_entry_point_contract_exports_reevaluation_tokens(self) -> None:
        contract = materialize_execution_contract_v0()
        assert contract["reevaluation_execution_go_token"] == _REEVAL_EXEC_GO
        assert contract["reevaluation_execution_implementation_go_token"] == _REEVAL_IMPL_GO
        assert contract["entry_point_status"] == "REEVALUATION_EXECUTION_WIRING_V0"
        assert contract["baseline_evaluator_owner"] == BASELINE_EVALUATOR_OWNER

    def test_runner_accepts_reevaluation_implementation_go_token(self) -> None:
        ok, branch = validate_entry_point_go_token_v0(_REEVAL_IMPL_GO)
        assert ok is True
        assert branch == "REEVALUATION_EXECUTION_IMPLEMENTATION_V0"
        assert _REEVAL_IMPL_GO in ALLOWED_CONFIRM_GO_TOKENS
