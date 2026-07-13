"""Repair contract tests for lead-lag entry-point guard and dispatch v0."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.ops import (
    run_cross_sectional_futures_lead_lag_information_diffusion_v0_offline_economic_evaluation_execution_v0 as runner_module,
)
from src.research.cross_sectional_futures_lead_lag_information_diffusion_v0_offline_economic_evaluation_execution_v0 import (
    BLOCK_REASON_FULL_CANONICAL_PARITY_NOT_PROVEN,
    GO_TOKEN,
    INFRASTRUCTURE_GO_TOKEN,
    REASON_BACKTEST_RUNTIME_DECISION_PARITY_FAIL,
    REASON_DISPATCH_NOT_SUCCESSFUL,
    REASON_ENTRY_POINT_GO_TOKEN_UNKNOWN,
    REASON_FULL_CANONICAL_PARITY_NOT_PROVEN,
    REASON_RUNNER_ENVELOPE_REQUIRED,
    REEVALUATION_GO_TOKEN,
    ExecutionTerminalStatus,
    materialize_preexecution_fail_closed_block_v0,
    materialize_runner_envelope_v0,
    resolve_identity_operator_go_v0,
    run_full_offline_economic_evaluation_v0,
    verify_full_evaluation_precheck_v1,
)
from src.research.cross_sectional_futures_lead_lag_information_diffusion_v0_offline_economic_evaluation_scope_ratification_v0 import (
    materialize_lead_lag_offline_economic_evaluation_scope_ratification_v0,
)
from src.research.cross_sectional_futures_lead_lag_information_diffusion_v0_versioned_hypothesis_binding_v0 import (
    materialize_versioned_hypothesis_binding_v0,
)
from tests.research.fixtures.cross_sectional_relative_strength_v0.fixture_builder import (
    build_synthetic_panel_series_v0,
)
from tests.research.fixtures.cross_sectional_relative_strength_v0.staging_builder import (
    write_bound_period_staging_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNNER_MODULE = (
    REPO_ROOT / "scripts/ops/"
    "run_cross_sectional_futures_lead_lag_information_diffusion_v0_offline_economic_"
    "evaluation_execution_v0.py"
)
PY310_STAGING = pytest.mark.skipif(
    sys.version_info < (3, 10),
    reason="panel staging loader requires Python 3.10+ zip(strict=True)",
)


@pytest.fixture(name="complete_binding")
def fixture_complete_binding() -> dict:
    return materialize_versioned_hypothesis_binding_v0()


@pytest.fixture(name="scope_ratification")
def fixture_scope_ratification(complete_binding: dict) -> dict:
    return materialize_lead_lag_offline_economic_evaluation_scope_ratification_v0(
        repo_root=REPO_ROOT,
        versioned_binding=complete_binding,
    )


@pytest.fixture(name="bound_staging")
def fixture_bound_staging() -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="cs_lead_lag_guard_repair_v0_"))
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


def _make_envelope(*, go_token: str, parity: bool) -> object:
    return materialize_runner_envelope_v0(
        requested_operator_go=go_token,
        dispatched_operator_go=resolve_identity_operator_go_v0(go_token),
        dispatch_rc=0,
        preexecution_parity_guard_pass=parity,
        full_canonical_chain_wired=parity,
        backtest_runtime_decision_parity_pass=parity,
    )


def test_requested_execution_go_not_rewritten_to_reevaluation() -> None:
    assert resolve_identity_operator_go_v0(GO_TOKEN) == GO_TOKEN
    assert resolve_identity_operator_go_v0(GO_TOKEN) != REEVALUATION_GO_TOKEN


def test_unknown_go_token_blocked_before_entry_point_dispatch() -> None:
    proc = subprocess.run(
        [
            sys.executable,
            str(RUNNER_MODULE),
            "--confirm",
            "GO_UNKNOWN_TOKEN",
            "--primary-worktree",
            str(REPO_ROOT),
        ],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert proc.returncode == 2
    assert "ERR:confirm_go_token_required" in proc.stderr


@PY310_STAGING
def test_full_canonical_chain_wired_false_blocks_before_evaluation(
    bound_staging: Path,
    scope_ratification: dict,
    complete_binding: dict,
) -> None:
    envelope = _make_envelope(go_token=GO_TOKEN, parity=False)
    ok, reasons, materialization = verify_full_evaluation_precheck_v1(
        repo_root=REPO_ROOT,
        ratification=scope_ratification,
        staging_root=bound_staging,
        versioned_binding=complete_binding,
        go_token=GO_TOKEN,
        require_execution_go=True,
        runner_envelope=envelope,
        materialize_dataset=False,
    )
    assert ok is False
    assert REASON_FULL_CANONICAL_PARITY_NOT_PROVEN in reasons
    assert materialization is None


@PY310_STAGING
def test_backtest_runtime_decision_parity_false_blocks_before_evaluation(
    bound_staging: Path,
    scope_ratification: dict,
    complete_binding: dict,
) -> None:
    envelope = materialize_runner_envelope_v0(
        requested_operator_go=GO_TOKEN,
        dispatched_operator_go=GO_TOKEN,
        dispatch_rc=0,
        preexecution_parity_guard_pass=False,
        full_canonical_chain_wired=True,
        backtest_runtime_decision_parity_pass=False,
    )
    with patch(
        "src.research.cross_sectional_futures_lead_lag_information_diffusion_v0_offline_"
        "economic_evaluation_execution_v0.load_evaluation_path_parity_status_v0",
        return_value=(True, False),
    ):
        ok, reasons, materialization = verify_full_evaluation_precheck_v1(
            repo_root=REPO_ROOT,
            ratification=scope_ratification,
            staging_root=bound_staging,
            versioned_binding=complete_binding,
            go_token=GO_TOKEN,
            require_execution_go=True,
            runner_envelope=envelope,
            materialize_dataset=False,
        )
    assert ok is False
    assert REASON_BACKTEST_RUNTIME_DECISION_PARITY_FAIL in reasons
    assert materialization is None


@PY310_STAGING
def test_parity_true_and_valid_go_passes_precheck_without_evaluation(
    bound_staging: Path,
    scope_ratification: dict,
    complete_binding: dict,
) -> None:
    envelope = _make_envelope(go_token=GO_TOKEN, parity=True)
    with (
        patch(
            "src.research.cross_sectional_futures_lead_lag_information_diffusion_v0_offline_"
            "economic_evaluation_execution_v0.load_evaluation_path_parity_status_v0",
            return_value=(True, True),
        ),
        patch(
            "src.research.cross_sectional_futures_lead_lag_information_diffusion_v0_offline_"
            "economic_evaluation_execution_v0.verify_panel_staging_source_manifests_v1",
            return_value=(True, 0, ()),
        ),
    ):
        ok, reasons, materialization = verify_full_evaluation_precheck_v1(
            repo_root=REPO_ROOT,
            ratification=scope_ratification,
            staging_root=bound_staging,
            versioned_binding=complete_binding,
            go_token=GO_TOKEN,
            require_execution_go=True,
            runner_envelope=envelope,
            materialize_dataset=False,
        )
    assert ok is True
    assert reasons == ()
    assert materialization is None


def test_direct_execution_owner_call_without_envelope_blocked(
    bound_staging: Path,
    scope_ratification: dict,
    complete_binding: dict,
) -> None:
    panel = build_synthetic_panel_series_v0()
    result = run_full_offline_economic_evaluation_v0(
        repo_root=REPO_ROOT,
        ratification=scope_ratification,
        staging_root=bound_staging,
        panel_series=panel,
        versioned_binding=complete_binding,
        go_token=GO_TOKEN,
        runner_envelope=None,
    )
    assert result.status is ExecutionTerminalStatus.FAIL_CLOSED_PRECHECK
    assert result.economic_evaluation_executed is False
    assert REASON_RUNNER_ENVELOPE_REQUIRED in result.reason_codes


def test_direct_runner_call_without_dispatch_success_blocked(
    bound_staging: Path,
    scope_ratification: dict,
    complete_binding: dict,
) -> None:
    envelope = materialize_runner_envelope_v0(
        requested_operator_go=GO_TOKEN,
        dispatched_operator_go=GO_TOKEN,
        dispatch_rc=2,
        preexecution_parity_guard_pass=False,
        full_canonical_chain_wired=False,
        backtest_runtime_decision_parity_pass=False,
    )
    panel = build_synthetic_panel_series_v0()
    result = run_full_offline_economic_evaluation_v0(
        repo_root=REPO_ROOT,
        ratification=scope_ratification,
        staging_root=bound_staging,
        panel_series=panel,
        versioned_binding=complete_binding,
        go_token=GO_TOKEN,
        runner_envelope=envelope,
    )
    assert result.economic_evaluation_executed is False
    assert REASON_DISPATCH_NOT_SUCCESSFUL in result.reason_codes


@PY310_STAGING
def test_ops_runner_execution_go_dispatch_blocks_before_evaluation(tmp_path: Path) -> None:
    with pytest.raises(SystemExit) as exc:
        runner_module.run_bounded_full_evaluation_dispatch_v0(
            confirm=GO_TOKEN,
            durable_evidence_root=tmp_path,
            primary_worktree=REPO_ROOT,
            staging_root=REPO_ROOT,
        )
    assert exc.value.code == 1
    bundles = list(tmp_path.glob("research/*execution_v0_*"))
    assert bundles
    block_text = (bundles[0] / "PREEXECUTION_BLOCK.txt").read_text(encoding="utf-8")
    assert "EVALUATION_EXECUTED=False" in block_text
    assert "BLOCK_REASON=FULL_CANONICAL_PARITY_NOT_PROVEN" in block_text


@PY310_STAGING
def test_ops_runner_cli_execution_go_blocks_without_reevaluation_rewrite() -> None:
    proc = subprocess.run(
        [
            sys.executable,
            str(RUNNER_MODULE),
            "--confirm",
            GO_TOKEN,
            "--primary-worktree",
            str(REPO_ROOT),
            "--durable-evidence-root",
            tempfile.mkdtemp(prefix="cs_lead_lag_cli_guard_"),
        ],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert proc.returncode == 1
    assert "EVALUATION_EXECUTED=false" in proc.stderr
    assert REEVALUATION_GO_TOKEN not in proc.stderr


def test_preexecution_block_contract_fields() -> None:
    block = materialize_preexecution_fail_closed_block_v0()
    assert block["EVALUATION_EXECUTED"] is False
    assert block["SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE"] is False
    assert block["PROMOTION_ADMISSIBLE"] is False
    assert block["RUNTIME_REWIRE_ADMISSIBLE"] is False
    assert block["PREEXECUTION_PARITY_GUARD_PASS"] is False
    assert block["BLOCK_REASON"] == BLOCK_REASON_FULL_CANONICAL_PARITY_NOT_PROVEN


def test_entry_point_registry_rejects_unregistered_go_token(
    bound_staging: Path,
    scope_ratification: dict,
    complete_binding: dict,
) -> None:
    envelope = _make_envelope(go_token=GO_TOKEN, parity=True)
    ok, reasons, _ = verify_full_evaluation_precheck_v1(
        repo_root=REPO_ROOT,
        ratification=scope_ratification,
        staging_root=bound_staging,
        versioned_binding=complete_binding,
        go_token="GO_UNREGISTERED",
        require_execution_go=True,
        runner_envelope=envelope,
        materialize_dataset=False,
    )
    assert ok is False
    assert REASON_ENTRY_POINT_GO_TOKEN_UNKNOWN in reasons


def test_infrastructure_go_path_remains_compatible(
    bound_staging: Path,
    scope_ratification: dict,
    complete_binding: dict,
) -> None:
    infra_go = INFRASTRUCTURE_GO_TOKEN
    ok, reasons, _ = verify_full_evaluation_precheck_v1(
        repo_root=REPO_ROOT,
        ratification=scope_ratification,
        staging_root=bound_staging,
        versioned_binding=complete_binding,
        go_token=infra_go,
        require_execution_go=False,
        materialize_dataset=False,
    )
    assert "GO_TOKEN_INVALID" not in reasons


def test_futures_only_and_no_bitcoin_invariants_unchanged(complete_binding: dict) -> None:
    constraints = complete_binding["system_constraints"]
    assert constraints["futures_only"] is True
    assert constraints["bitcoin_direction_allowed"] is False


def test_guard_runs_before_dataset_materialization_on_parity_fail(
    bound_staging: Path,
    scope_ratification: dict,
    complete_binding: dict,
) -> None:
    envelope = _make_envelope(go_token=GO_TOKEN, parity=True)
    with (
        patch(
            "src.research.cross_sectional_futures_lead_lag_information_diffusion_v0_offline_"
            "economic_evaluation_execution_v0.load_evaluation_path_parity_status_v0",
            return_value=(False, False),
        ),
        patch(
            "src.research.cross_sectional_futures_lead_lag_information_diffusion_v0_offline_"
            "economic_evaluation_execution_v0.materialize_bound_panel_dataset_v0",
        ) as materialize,
    ):
        ok, reasons, materialization = verify_full_evaluation_precheck_v1(
            repo_root=REPO_ROOT,
            ratification=scope_ratification,
            staging_root=bound_staging,
            versioned_binding=complete_binding,
            go_token=GO_TOKEN,
            require_execution_go=True,
            runner_envelope=envelope,
            materialize_dataset=True,
        )
    assert ok is False
    assert REASON_FULL_CANONICAL_PARITY_NOT_PROVEN in reasons
    assert materialization is None
    materialize.assert_not_called()


def test_productive_entry_point_dispatch_to_guard_path(
    tmp_path: Path,
    bound_staging: Path,
) -> None:
    with patch.object(
        runner_module,
        "run_full_offline_economic_evaluation_v0",
    ) as full_eval:
        with pytest.raises(SystemExit):
            runner_module.run_bounded_full_evaluation_dispatch_v0(
                confirm=GO_TOKEN,
                durable_evidence_root=tmp_path,
                primary_worktree=REPO_ROOT,
                staging_root=bound_staging,
            )
        full_eval.assert_not_called()
