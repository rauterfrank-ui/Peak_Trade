"""Ops-runner branch contract tests for pairwise spillover reevaluation baseline execution v0."""

from __future__ import annotations

import ast
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.ops.run_cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_evaluation_execution_v0 import (
    ALLOWED_CONFIRM_GO_TOKENS,
    IMPLEMENTATION_REPAIR_CONFIRM_GO,
    REEVALUATION_BASELINE_EXECUTION_CONFIRM_GO,
    REEVALUATION_BASELINE_EXECUTION_IMPLEMENTATION_CONFIRM_GO,
    REEVALUATION_EXECUTION_CONFIRM_GO,
    REEVALUATION_EXECUTION_IMPLEMENTATION_CONFIRM_GO,
    run_reevaluation_baseline_execution_v0,
)
from src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_evaluation_authorization_ratification_v0 import (
    materialize_offline_economic_evaluation_authorization_ratification_v0,
)
from src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_evaluation_execution_v0 import (
    AUTHORITY_EFFECT,
    CANONICAL_BASELINE_BACKTEST_OWNER,
    DISPATCH_IMPLEMENTATION_GO_TOKEN,
    ENTRY_POINT_DISPATCH_REGISTRY,
    EXECUTION_GO_TOKEN,
    IMPLEMENTATION_GO_TOKEN,
    IMPLEMENTATION_REPAIR_GO_TOKEN,
    REASON_DATASET_DIGEST_NOT_VERIFIED,
    REASON_GO_TOKEN_INVALID,
    REASON_GO_TOKEN_MISSING,
    REEVALUATION_BASELINE_EXECUTION_GO_TOKEN,
    REEVALUATION_BASELINE_EXECUTION_IMPLEMENTATION_GO_TOKEN,
    RUNNER_SCRIPT,
    RUNTIME_EFFECT,
    validate_entry_point_go_token_v0,
    validate_reevaluation_baseline_execution_go_token_v0,
)
from src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_versioned_hypothesis_binding_v0 import (
    materialize_versioned_hypothesis_binding_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNNER_MODULE = REPO_ROOT / RUNNER_SCRIPT
_BASELINE_EXEC_GO = REEVALUATION_BASELINE_EXECUTION_GO_TOKEN
_SIMILAR_NON_IDENTICAL_GO = REEVALUATION_BASELINE_EXECUTION_IMPLEMENTATION_GO_TOKEN
STAGING_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "datasets/admissible_futures/pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_v1/v1"
)


@pytest.fixture(name="complete_binding")
def fixture_complete_binding() -> dict:
    return materialize_versioned_hypothesis_binding_v0()


@pytest.fixture(name="authorization_ratification")
def fixture_authorization_ratification() -> dict:
    return materialize_offline_economic_evaluation_authorization_ratification_v0()


class TestOpsRunnerReevaluationBaselineExecutionTokenAcceptance:
    def test_exact_reevaluation_baseline_execution_go_token_accepted_by_ops_runner(self) -> None:
        assert _BASELINE_EXEC_GO in ALLOWED_CONFIRM_GO_TOKENS

    def test_exact_token_registered_in_dispatch_registry(self) -> None:
        assert (
            ENTRY_POINT_DISPATCH_REGISTRY[_BASELINE_EXEC_GO] == "REEVALUATION_BASELINE_EXECUTION_V0"
        )

    def test_harness_dispatch_branch_equals_reevaluation_baseline_execution_v0(self) -> None:
        ok, branch = validate_entry_point_go_token_v0(_BASELINE_EXEC_GO)
        assert ok is True
        assert branch == "REEVALUATION_BASELINE_EXECUTION_V0"

    @pytest.mark.skipif(
        not STAGING_ROOT.is_dir(),
        reason="staging_root_unavailable",
    )
    def test_runner_subprocess_accepts_exact_baseline_execution_go_token(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            proc = subprocess.run(
                [
                    sys.executable,
                    str(RUNNER_MODULE),
                    "--confirm",
                    _BASELINE_EXEC_GO,
                    "--primary-worktree",
                    str(REPO_ROOT),
                    "--durable-evidence-root",
                    tmp,
                    "--staging-root",
                    str(STAGING_ROOT),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
        assert proc.returncode == 0, proc.stderr
        payload = json.loads(proc.stdout)
        assert payload["go_token_forwarded"] == _BASELINE_EXEC_GO
        assert payload["harness_dispatch_branch"] == "REEVALUATION_BASELINE_EXECUTION_V0"
        assert payload["economic_evaluation_executed"] is False
        assert payload["baseline_executed"] is False
        assert payload["robustness_executed"] is False
        assert payload["runtime_effect"] == "NONE"
        assert payload["authority_effect"] == "NONE"

    def test_exact_token_forwarded_unchanged_to_harness(
        self,
        authorization_ratification: dict,
        complete_binding: dict,
    ) -> None:
        forwarded_tokens: list[str] = []
        baseline_calls = 0

        def _capture_baseline(*, go_token: str, **kwargs):  # type: ignore[no-untyped-def]
            nonlocal baseline_calls
            forwarded_tokens.append(go_token)
            baseline_calls += 1
            from src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_evaluation_execution_v0 import (
                run_baseline_offline_economic_evaluation_v0,
            )

            return run_baseline_offline_economic_evaluation_v0(
                go_token=go_token,
                **kwargs,
            )

        with tempfile.TemporaryDirectory() as tmp:
            with (
                patch(
                    "scripts.ops.run_cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_evaluation_execution_v0.run_baseline_offline_economic_evaluation_v0",
                    side_effect=_capture_baseline,
                ),
                patch(
                    "scripts.ops.run_cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_evaluation_execution_v0.run_reevaluation_baseline_execution_preflight_v0",
                ) as preflight_mock,
                patch(
                    "scripts.ops.run_cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_evaluation_execution_v0.retention.finalize_durable_bundle_manifest",
                    return_value=(0, ""),
                ),
            ):
                from src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_evaluation_execution_v0 import (
                    ReevaluationBaselineExecutionPreflightResultV0,
                )

                preflight_mock.return_value = ReevaluationBaselineExecutionPreflightResultV0(
                    preflight_passed=True,
                    blocked=False,
                    baseline_execution_admissible=True,
                    implementation_wiring_verified=False,
                    reason_codes=(),
                    python_version_ok=True,
                    python_version="3.11.0",
                    bound_dataset_materialized=True,
                    source_manifests_verified=True,
                    dataset_digest_verified=True,
                    portfolio_bindings_valid=True,
                    same_dataset=True,
                    same_universe=True,
                    same_strategy_parameters=True,
                    same_cost_policy=True,
                    same_risk_sizing_semantics=True,
                    panel_data_digest="18eccf85663ce292ef1bf0edce63d2dd44215405cf3d880850d2c8d8e413a591",
                    ratified_dataset_digest="18eccf85663ce292ef1bf0edce63d2dd44215405cf3d880850d2c8d8e413a591",
                    baseline_wiring_verified=True,
                    baseline_executed=False,
                    baseline_callable_wiring_only=True,
                    economic_evaluation_executed=False,
                    dataset_digest_repaired=True,
                    authority_effect=AUTHORITY_EFFECT,
                    runtime_effect=RUNTIME_EFFECT,
                )
                result = run_reevaluation_baseline_execution_v0(
                    confirm=_BASELINE_EXEC_GO,
                    durable_evidence_root=Path(tmp),
                    primary_worktree=REPO_ROOT,
                    staging_root=STAGING_ROOT,
                )
        assert forwarded_tokens == [_BASELINE_EXEC_GO]
        assert baseline_calls == 1
        assert result["go_token_forwarded"] == _BASELINE_EXEC_GO
        assert result["economic_evaluation_executed"] is False
        assert result["baseline_executed"] is False


class TestOpsRunnerNegativeTokenCases:
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

    def test_similar_but_non_identical_token_rejected_by_subprocess(self) -> None:
        proc = subprocess.run(
            [
                sys.executable,
                str(RUNNER_MODULE),
                "--confirm",
                _SIMILAR_NON_IDENTICAL_GO + "_EXTRA",
                "--primary-worktree",
                str(REPO_ROOT),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc.returncode == 2
        assert "ERR:confirm_go_token_required" in proc.stderr

    def test_implementation_go_token_does_not_dispatch_to_baseline_execution_branch(self) -> None:
        ok, branch = validate_entry_point_go_token_v0(_SIMILAR_NON_IDENTICAL_GO)
        assert ok is True
        assert branch == "REEVALUATION_BASELINE_EXECUTION_IMPLEMENTATION_V0"
        assert branch != "REEVALUATION_BASELINE_EXECUTION_V0"

    def test_missing_go_token_rejected_by_harness_validator(self) -> None:
        ok, reasons = validate_reevaluation_baseline_execution_go_token_v0(None)
        assert ok is False
        assert REASON_GO_TOKEN_MISSING in reasons

    def test_unknown_go_token_rejected_by_harness_validator(self) -> None:
        ok, reasons = validate_reevaluation_baseline_execution_go_token_v0("INVALID_GO_TOKEN")
        assert ok is False
        assert REASON_GO_TOKEN_INVALID in reasons


class TestLegacyTokenBehaviorUnchanged:
    @pytest.mark.parametrize(
        "token",
        [
            IMPLEMENTATION_GO_TOKEN,
            DISPATCH_IMPLEMENTATION_GO_TOKEN,
            EXECUTION_GO_TOKEN,
            IMPLEMENTATION_REPAIR_GO_TOKEN,
            REEVALUATION_EXECUTION_CONFIRM_GO,
            REEVALUATION_EXECUTION_IMPLEMENTATION_CONFIRM_GO,
            REEVALUATION_BASELINE_EXECUTION_IMPLEMENTATION_CONFIRM_GO,
        ],
    )
    def test_legacy_tokens_remain_allowed(self, token: str) -> None:
        assert token in ALLOWED_CONFIRM_GO_TOKENS

    def test_legacy_execution_token_still_maps_to_execution_branch(self) -> None:
        ok, branch = validate_entry_point_go_token_v0(EXECUTION_GO_TOKEN)
        assert ok is True
        assert branch == "EXECUTION_V0"

    def test_implementation_repair_token_constant_unchanged(self) -> None:
        assert IMPLEMENTATION_REPAIR_CONFIRM_GO == IMPLEMENTATION_REPAIR_GO_TOKEN


class TestDispatchReachesCanonicalBaselineOwner:
    def test_baseline_wiring_reaches_canonical_backtest_owner(
        self,
        authorization_ratification: dict,
        complete_binding: dict,
    ) -> None:
        from src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_evaluation_execution_v0 import (
            run_baseline_offline_economic_evaluation_v0,
        )

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


class TestPreflightAndDigestGating:
    @pytest.mark.skipif(
        not STAGING_ROOT.is_dir(),
        reason="staging_root_unavailable",
    )
    def test_valid_fixture_dataset_and_binding_digest_verified(
        self,
        authorization_ratification: dict,
        complete_binding: dict,
    ) -> None:
        from src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_evaluation_execution_v0 import (
            run_reevaluation_baseline_execution_preflight_v0,
        )

        result = run_reevaluation_baseline_execution_preflight_v0(
            go_token=_BASELINE_EXEC_GO,
            repo_root=REPO_ROOT,
            authorization_ratification=authorization_ratification,
            versioned_binding=complete_binding,
            staging_root=STAGING_ROOT,
            verify_source_manifests=True,
            materialize_dataset=True,
        )
        assert result.dataset_digest_verified is True
        assert result.bound_dataset_materialized is True
        assert result.source_manifests_verified is True
        assert result.baseline_executed is False
        assert result.economic_evaluation_executed is False

    @pytest.mark.skipif(
        not STAGING_ROOT.is_dir(),
        reason="staging_root_unavailable",
    )
    def test_preflight_failure_blocks_before_evaluation(
        self,
        authorization_ratification: dict,
        complete_binding: dict,
    ) -> None:
        from src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_evaluation_execution_v0 import (
            run_reevaluation_baseline_execution_preflight_v0,
        )

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
                go_token=_BASELINE_EXEC_GO,
                repo_root=REPO_ROOT,
                authorization_ratification=authorization_ratification,
                versioned_binding=complete_binding,
                staging_root=STAGING_ROOT,
                verify_source_manifests=True,
                materialize_dataset=True,
            )
        assert result.dataset_digest_verified is False
        assert REASON_DATASET_DIGEST_NOT_VERIFIED in result.reason_codes
        assert result.baseline_executed is False
        assert result.economic_evaluation_executed is False


class TestNoDuplicatedEvaluationLogic:
    def test_runner_delegates_to_harness_without_local_baseline_logic(self) -> None:
        source = RUNNER_MODULE.read_text(encoding="utf-8")
        assert "run_walk_forward_evaluation_v0" not in source
        assert "run_monte_carlo_evaluation_v0" not in source
        assert "run_stress_evaluation_v0" not in source

    def test_reevaluation_baseline_branch_calls_existing_harness_callables(self) -> None:
        source = RUNNER_MODULE.read_text(encoding="utf-8")
        assert "def run_reevaluation_baseline_execution_v0(" in source
        assert "run_reevaluation_baseline_execution_preflight_v0(" in source
        assert "run_baseline_offline_economic_evaluation_v0(" in source

    def test_no_runtime_import_boundary_violation(self) -> None:
        tree = ast.parse(RUNNER_MODULE.read_text(encoding="utf-8"))
        imports = {
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module
        }
        assert not any(item.startswith("src.execution") for item in imports)
        assert not any(item.startswith("src.scheduler") for item in imports)


class TestOfflineBoundaryInvariants:
    def test_runtime_effect_none(self) -> None:
        assert RUNTIME_EFFECT == "NONE"

    def test_authority_effect_none(self) -> None:
        assert AUTHORITY_EFFECT == "NONE"

    def test_orders_not_enabled_in_runner_result(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with (
                patch(
                    "scripts.ops.run_cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_evaluation_execution_v0.run_reevaluation_baseline_execution_preflight_v0",
                ) as preflight_mock,
                patch(
                    "scripts.ops.run_cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_evaluation_execution_v0.retention.finalize_durable_bundle_manifest",
                    return_value=(0, ""),
                ),
            ):
                from src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_evaluation_execution_v0 import (
                    ReevaluationBaselineExecutionPreflightResultV0,
                )

                preflight_mock.return_value = ReevaluationBaselineExecutionPreflightResultV0(
                    preflight_passed=True,
                    blocked=False,
                    baseline_execution_admissible=True,
                    implementation_wiring_verified=False,
                    reason_codes=(),
                    python_version_ok=True,
                    python_version="3.11.0",
                    bound_dataset_materialized=True,
                    source_manifests_verified=True,
                    dataset_digest_verified=True,
                    portfolio_bindings_valid=True,
                    same_dataset=True,
                    same_universe=True,
                    same_strategy_parameters=True,
                    same_cost_policy=True,
                    same_risk_sizing_semantics=True,
                    panel_data_digest="18eccf85663ce292ef1bf0edce63d2dd44215405cf3d880850d2c8d8e413a591",
                    ratified_dataset_digest="18eccf85663ce292ef1bf0edce63d2dd44215405cf3d880850d2c8d8e413a591",
                    baseline_wiring_verified=True,
                    baseline_executed=False,
                    baseline_callable_wiring_only=True,
                    economic_evaluation_executed=False,
                    dataset_digest_repaired=True,
                    authority_effect=AUTHORITY_EFFECT,
                    runtime_effect=RUNTIME_EFFECT,
                )
                result = run_reevaluation_baseline_execution_v0(
                    confirm=_BASELINE_EXEC_GO,
                    durable_evidence_root=Path(tmp),
                    primary_worktree=REPO_ROOT,
                    staging_root=REPO_ROOT,
                )
        assert result["runtime_effect"] == "NONE"
        assert result["authority_effect"] == "NONE"
        assert result["economic_evaluation_executed"] is False
        assert result["baseline_executed"] is False
