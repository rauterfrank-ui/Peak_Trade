"""Reevaluation baseline execution implementation contract tests for pairwise spillover v1."""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.ops.run_cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_evaluation_execution_v0 import (
    ALLOWED_CONFIRM_GO_TOKENS,
    REEVALUATION_BASELINE_EXECUTION_IMPLEMENTATION_CONFIRM_GO,
)
from src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_evaluation_authorization_ratification_v0 import (
    materialize_offline_economic_evaluation_authorization_ratification_v0,
)
from src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_evaluation_execution_v0 import (
    AUTHORITY_EFFECT,
    CANONICAL_BASELINE_BACKTEST_OWNER,
    ENTRY_POINT_DISPATCH_REGISTRY,
    REASON_DATASET_DIGEST_NOT_VERIFIED,
    REASON_GO_TOKEN_INVALID,
    REASON_GO_TOKEN_MISSING,
    REASON_IMPLEMENTATION_GO_DOES_NOT_AUTHORIZE_BASELINE_EXECUTION,
    REASON_PYTHON_VERSION_TOO_LOW,
    REASON_REEVALUATION_BASELINE_PREFLIGHT_IMPLEMENTATION_COMPLETE,
    REEVALUATION_BASELINE_EXECUTION_GO_TOKEN,
    REEVALUATION_BASELINE_EXECUTION_IMPLEMENTATION_GO_TOKEN,
    RUNNER_SCRIPT,
    RUNTIME_EFFECT,
    RATIFIED_BINDING_DIGEST,
    build_cryptographic_identity_comparison,
    materialize_go_token_and_dispatch_contract_v0,
    run_baseline_offline_economic_evaluation_v0,
    run_reevaluation_baseline_execution_preflight_v0,
    validate_entry_point_go_token_v0,
    validate_reevaluation_baseline_execution_go_token_v0,
    validate_reevaluation_baseline_execution_implementation_go_token_v0,
)
from src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_versioned_hypothesis_binding_v0 import (
    materialize_versioned_hypothesis_binding_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
_IMPL_GO = REEVALUATION_BASELINE_EXECUTION_IMPLEMENTATION_GO_TOKEN
_BASELINE_EXEC_GO = REEVALUATION_BASELINE_EXECUTION_GO_TOKEN
RUNNER_MODULE = REPO_ROOT / RUNNER_SCRIPT
STAGING_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "datasets/admissible_futures/pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_v1/v1"
)
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


class TestBaselineGoTokenRegistration:
    def test_implementation_go_token_accepted(self) -> None:
        ok, reasons = validate_reevaluation_baseline_execution_implementation_go_token_v0(_IMPL_GO)
        assert ok is True
        assert reasons == ()

    def test_baseline_execution_go_token_registered_in_dispatch_registry(self) -> None:
        assert (
            ENTRY_POINT_DISPATCH_REGISTRY[_BASELINE_EXEC_GO] == "REEVALUATION_BASELINE_EXECUTION_V0"
        )
        assert (
            ENTRY_POINT_DISPATCH_REGISTRY[_IMPL_GO]
            == "REEVALUATION_BASELINE_EXECUTION_IMPLEMENTATION_V0"
        )

    def test_implementation_go_in_runner_allowed_confirm_tokens(self) -> None:
        assert _IMPL_GO in ALLOWED_CONFIRM_GO_TOKENS

    def test_baseline_execution_go_in_runner_allowed_confirm_tokens(self) -> None:
        assert _BASELINE_EXEC_GO in ALLOWED_CONFIRM_GO_TOKENS

    def test_baseline_execution_go_separately_gated(self) -> None:
        contract = materialize_go_token_and_dispatch_contract_v0()
        assert contract["baseline_execution_go_separately_gated"] is True
        assert contract["implementation_go_authorizes_baseline_execution"] is False


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
        )
        assert result.executed is False
        assert result.blocked is True
        assert REASON_GO_TOKEN_INVALID in result.reason_codes

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


class TestBaselinePreflightBehavior:
    def test_preflight_without_dataset_materialization_passes_wiring(
        self,
        authorization_ratification: dict,
        complete_binding: dict,
    ) -> None:
        result = run_reevaluation_baseline_execution_preflight_v0(
            go_token=_IMPL_GO,
            repo_root=REPO_ROOT,
            authorization_ratification=authorization_ratification,
            versioned_binding=complete_binding,
            verify_source_manifests=False,
            materialize_dataset=False,
        )
        assert result.implementation_wiring_verified is True
        assert result.preflight_passed is True
        assert result.baseline_executed is False
        assert result.economic_evaluation_executed is False
        assert result.dataset_digest_repaired is False
        assert REASON_IMPLEMENTATION_GO_DOES_NOT_AUTHORIZE_BASELINE_EXECUTION in result.reason_codes
        assert REASON_REEVALUATION_BASELINE_PREFLIGHT_IMPLEMENTATION_COMPLETE in result.reason_codes

    @pytest.mark.skipif(
        not STAGING_ROOT.is_dir(),
        reason="staging_root_unavailable",
    )
    def test_dataset_digest_verified_after_reconciliation_repair(
        self,
        authorization_ratification: dict,
        complete_binding: dict,
    ) -> None:
        result = run_reevaluation_baseline_execution_preflight_v0(
            go_token=_IMPL_GO,
            repo_root=REPO_ROOT,
            authorization_ratification=authorization_ratification,
            versioned_binding=complete_binding,
            staging_root=STAGING_ROOT,
            verify_source_manifests=True,
            materialize_dataset=True,
        )
        assert result.bound_dataset_materialized is True
        assert result.dataset_digest_verified is True
        assert result.dataset_digest_repaired is True
        assert result.baseline_executed is False
        assert result.economic_evaluation_executed is False
        assert REASON_DATASET_DIGEST_NOT_VERIFIED not in result.reason_codes

    @pytest.mark.skipif(
        not STAGING_ROOT.is_dir(),
        reason="staging_root_unavailable",
    )
    def test_stale_dataset_digest_rejected_by_preflight(
        self,
        authorization_ratification: dict,
        complete_binding: dict,
    ) -> None:
        identity_patch = {
            "same_dataset": True,
            "same_universe": True,
            "same_strategy_parameters": True,
            "same_cost_policy": True,
            "same_risk_sizing_semantics": True,
        }
        with (
            patch(
                "src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_evaluation_execution_v0.build_identity_invariant_contract_v0",
                return_value=identity_patch,
            ),
            patch(
                "src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_evaluation_execution_v0.RATIFIED_DATASET_DIGEST",
                "f" * 64,
            ),
        ):
            result = run_reevaluation_baseline_execution_preflight_v0(
                go_token=_IMPL_GO,
                repo_root=REPO_ROOT,
                authorization_ratification=authorization_ratification,
                versioned_binding=complete_binding,
                staging_root=STAGING_ROOT,
                verify_source_manifests=True,
                materialize_dataset=True,
            )
        assert result.dataset_digest_verified is False
        assert result.dataset_digest_repaired is False
        assert REASON_DATASET_DIGEST_NOT_VERIFIED in result.reason_codes


class TestPythonVersionGate:
    def test_python_version_too_low_blocks(self) -> None:
        with patch(
            "src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_evaluation_execution_v0.sys.version_info",
            type("VI", (), {"major": 3, "minor": 9, "micro": 6})(),
        ):
            from src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_evaluation_execution_v0 import (
                verify_python_version_for_baseline_preflight_v0,
            )

            ok, _version = verify_python_version_for_baseline_preflight_v0()
            assert ok is False

        result = run_reevaluation_baseline_execution_preflight_v0(
            go_token=_IMPL_GO,
            repo_root=REPO_ROOT,
            authorization_ratification=materialize_offline_economic_evaluation_authorization_ratification_v0(),
            versioned_binding=materialize_versioned_hypothesis_binding_v0(),
            verify_source_manifests=False,
            materialize_dataset=False,
        )
        if sys.version_info < (3, 10):
            assert REASON_PYTHON_VERSION_TOO_LOW in result.reason_codes


class TestGoTokenRejection:
    def test_unknown_go_token_rejected(self) -> None:
        ok, reasons = validate_reevaluation_baseline_execution_implementation_go_token_v0(
            "INVALID_GO_TOKEN"
        )
        assert ok is False
        assert REASON_GO_TOKEN_INVALID in reasons

        ok_baseline, baseline_reasons = validate_reevaluation_baseline_execution_go_token_v0(
            "INVALID_GO_TOKEN"
        )
        assert ok_baseline is False
        assert REASON_GO_TOKEN_INVALID in baseline_reasons

    def test_missing_go_token_rejected(self) -> None:
        ok, reasons = validate_reevaluation_baseline_execution_implementation_go_token_v0(None)
        assert ok is False
        assert REASON_GO_TOKEN_MISSING in reasons


class TestOfflineBoundaryAndBindingInvariants:
    def test_offline_boundary_preserved(
        self,
        authorization_ratification: dict,
    ) -> None:
        assert authorization_ratification.get("offline_only") is True

    def test_no_binding_digest_change(self) -> None:
        identity = build_cryptographic_identity_comparison(REPO_ROOT)
        assert identity["CRYPTOGRAPHIC_BINDING_IDENTITY_CHANGED"] is False
        assert identity["binding_digest"] == RATIFIED_BINDING_DIGEST

    def test_runtime_effect_none(self) -> None:
        assert RUNTIME_EFFECT == "NONE"

    def test_authority_effect_none(self) -> None:
        assert AUTHORITY_EFFECT == "NONE"


class TestImportBoundary:
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


class TestRunnerBranch:
    def test_runner_accepts_implementation_go_token(self) -> None:
        ok, branch = validate_entry_point_go_token_v0(_IMPL_GO)
        assert ok is True
        assert branch == "REEVALUATION_BASELINE_EXECUTION_IMPLEMENTATION_V0"

    def test_unknown_token_rejected_by_subprocess(self) -> None:
        proc = subprocess.run(
            [
                sys.executable,
                str(RUNNER_MODULE),
                "--confirm",
                "INVALID_GO_TOKEN",
                "--primary-worktree",
                str(REPO_ROOT),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc.returncode == 2
        assert "ERR:confirm_go_token_required" in proc.stderr
