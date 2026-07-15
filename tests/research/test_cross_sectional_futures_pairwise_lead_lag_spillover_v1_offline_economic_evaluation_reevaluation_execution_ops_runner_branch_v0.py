"""Ops-runner branch contract tests for pairwise spillover reevaluation execution v0."""

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
    REEVALUATION_EXECUTION_CONFIRM_GO,
    REEVALUATION_EXECUTION_IMPLEMENTATION_CONFIRM_GO,
    run_reevaluation_execution_v0,
)
from src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_evaluation_authorization_ratification_v0 import (
    materialize_offline_economic_evaluation_authorization_ratification_v0,
)
from src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_evaluation_execution_v0 import (
    AUTHORITY_EFFECT,
    DISPATCH_IMPLEMENTATION_GO_TOKEN,
    ENTRY_POINT_DISPATCH_REGISTRY,
    EXECUTION_GO_TOKEN,
    IMPLEMENTATION_GO_TOKEN,
    IMPLEMENTATION_REPAIR_GO_TOKEN,
    REASON_GO_TOKEN_INVALID,
    REASON_GO_TOKEN_MISSING,
    REEVALUATION_EXECUTION_GO_TOKEN,
    REEVALUATION_EXECUTION_IMPLEMENTATION_GO_TOKEN,
    RUNNER_SCRIPT,
    RUNTIME_EFFECT,
    validate_entry_point_go_token_v0,
    validate_reevaluation_execution_go_token_v0,
)
from src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_versioned_hypothesis_binding_v0 import (
    materialize_versioned_hypothesis_binding_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNNER_MODULE = REPO_ROOT / RUNNER_SCRIPT
_REEVAL_EXEC_GO = REEVALUATION_EXECUTION_GO_TOKEN
_SIMILAR_NON_IDENTICAL_GO = REEVALUATION_EXECUTION_IMPLEMENTATION_GO_TOKEN


@pytest.fixture(name="complete_binding")
def fixture_complete_binding() -> dict:
    return materialize_versioned_hypothesis_binding_v0()


@pytest.fixture(name="authorization_ratification")
def fixture_authorization_ratification() -> dict:
    return materialize_offline_economic_evaluation_authorization_ratification_v0()


class TestOpsRunnerReevaluationExecutionTokenAcceptance:
    def test_exact_reevaluation_execution_go_token_accepted_by_ops_runner(self) -> None:
        assert _REEVAL_EXEC_GO in ALLOWED_CONFIRM_GO_TOKENS

    def test_exact_token_registered_in_dispatch_registry(self) -> None:
        assert ENTRY_POINT_DISPATCH_REGISTRY[_REEVAL_EXEC_GO] == "REEVALUATION_EXECUTION_V0"

    def test_harness_dispatch_branch_equals_reevaluation_execution_v0(self) -> None:
        ok, branch = validate_entry_point_go_token_v0(_REEVAL_EXEC_GO)
        assert ok is True
        assert branch == "REEVALUATION_EXECUTION_V0"

    def test_runner_subprocess_accepts_exact_reevaluation_execution_go_token(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            proc = subprocess.run(
                [
                    sys.executable,
                    str(RUNNER_MODULE),
                    "--confirm",
                    _REEVAL_EXEC_GO,
                    "--primary-worktree",
                    str(REPO_ROOT),
                    "--durable-evidence-root",
                    tmp,
                ],
                capture_output=True,
                text=True,
                check=False,
            )
        assert proc.returncode == 0, proc.stderr
        payload = json.loads(proc.stdout)
        assert payload["go_token_forwarded"] == _REEVAL_EXEC_GO
        assert payload["harness_dispatch_branch"] == "REEVALUATION_EXECUTION_V0"
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

        def _capture_dispatch(*, go_token: str, **kwargs):  # type: ignore[no-untyped-def]
            forwarded_tokens.append(go_token)
            from src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_evaluation_execution_v0 import (
                run_offline_economic_evaluation_execution_dispatch_v0,
            )

            return run_offline_economic_evaluation_execution_dispatch_v0(
                go_token=go_token,
                **kwargs,
            )

        def _capture_full_evaluation(*, go_token: str, **kwargs):  # type: ignore[no-untyped-def]
            forwarded_tokens.append(go_token)
            from src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_evaluation_execution_v0 import (
                run_full_offline_economic_evaluation_v0,
            )

            return run_full_offline_economic_evaluation_v0(
                go_token=go_token,
                **kwargs,
            )

        with tempfile.TemporaryDirectory() as tmp:
            with (
                patch(
                    "scripts.ops.run_cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_evaluation_execution_v0.run_offline_economic_evaluation_execution_dispatch_v0",
                    side_effect=_capture_dispatch,
                ),
                patch(
                    "scripts.ops.run_cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_evaluation_execution_v0.run_full_offline_economic_evaluation_v0",
                    side_effect=_capture_full_evaluation,
                ),
                patch(
                    "scripts.ops.run_cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_evaluation_execution_v0.retention.finalize_durable_bundle_manifest",
                    return_value=(0, ""),
                ),
            ):
                result = run_reevaluation_execution_v0(
                    confirm=_REEVAL_EXEC_GO,
                    durable_evidence_root=Path(tmp),
                    primary_worktree=REPO_ROOT,
                    staging_root=REPO_ROOT,
                )
        assert forwarded_tokens == [_REEVAL_EXEC_GO, _REEVAL_EXEC_GO]
        assert result["go_token_forwarded"] == _REEVAL_EXEC_GO
        assert result["economic_evaluation_executed"] is False


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

    def test_missing_go_token_rejected_by_harness_validator(self) -> None:
        ok, reasons = validate_reevaluation_execution_go_token_v0(None)
        assert ok is False
        assert REASON_GO_TOKEN_MISSING in reasons

    def test_unknown_go_token_rejected_by_harness_validator(self) -> None:
        ok, reasons = validate_reevaluation_execution_go_token_v0("INVALID_GO_TOKEN")
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
            REEVALUATION_EXECUTION_IMPLEMENTATION_GO_TOKEN,
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

    def test_reevaluation_implementation_token_constant_unchanged(self) -> None:
        assert (
            REEVALUATION_EXECUTION_IMPLEMENTATION_CONFIRM_GO
            == REEVALUATION_EXECUTION_IMPLEMENTATION_GO_TOKEN
        )


class TestNoDuplicatedEvaluationLogic:
    def test_runner_delegates_to_harness_without_local_baseline_logic(self) -> None:
        source = RUNNER_MODULE.read_text(encoding="utf-8")
        assert "run_baseline_offline_economic_evaluation_v0" not in source
        assert "run_walk_forward_evaluation_v0" not in source
        assert "run_monte_carlo_evaluation_v0" not in source
        assert "run_stress_evaluation_v0" not in source

    def test_reevaluation_branch_calls_existing_harness_callables(self) -> None:
        source = RUNNER_MODULE.read_text(encoding="utf-8")
        assert "def run_reevaluation_execution_v0(" in source
        assert "run_offline_economic_evaluation_execution_dispatch_v0(" in source
        assert "run_full_offline_economic_evaluation_v0(" in source

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

    def test_orders_not_enabled_in_runner_result(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            proc = subprocess.run(
                [
                    sys.executable,
                    str(RUNNER_MODULE),
                    "--confirm",
                    _REEVAL_EXEC_GO,
                    "--primary-worktree",
                    str(REPO_ROOT),
                    "--durable-evidence-root",
                    tmp,
                ],
                capture_output=True,
                text=True,
                check=False,
            )
        payload = json.loads(proc.stdout)
        assert payload["runtime_effect"] == "NONE"
        assert payload["authority_effect"] == "NONE"
        assert payload["economic_evaluation_executed"] is False
