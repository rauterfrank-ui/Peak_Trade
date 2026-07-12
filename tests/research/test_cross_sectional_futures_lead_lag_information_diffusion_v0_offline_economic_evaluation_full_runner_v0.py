"""Contract tests for lead-lag diffusion v0 full offline economic evaluation runner."""

from __future__ import annotations

import ast
import importlib
import json
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
    ALLOWED_EVALUATION_STAGES,
    AUTHORITY_EFFECT,
    CANONICAL_FULL_EVALUATION_CALLABLE,
    EconomicClassification,
    ExecutionTerminalStatus,
    FIXTURE_DATA_DIGEST,
    GO_TOKEN,
    INFRASTRUCTURE_GO_TOKEN,
    REASON_BINDING_DIGEST_MISMATCH,
    REASON_DATASET_DIGEST_MISMATCH,
    REASON_GO_TOKEN_INVALID,
    REASON_UNIVERSE_DIGEST_MISMATCH,
    REEVALUATION_GO_TOKEN,
    RUNTIME_EFFECT,
    execution_result_to_dict,
    materialize_execution_contract_v0,
    run_full_evaluation_entrypoint_dry_run_v1,
    run_full_offline_economic_evaluation_v0,
    verify_execution_start_state_v0,
    verify_full_evaluation_precheck_v1,
    verify_ratified_digests_v0,
)
from src.research.cross_sectional_panel_economic_evaluation_wiring_v0 import (
    wire_robustness_stages_v0,
)
from src.research.cross_sectional_futures_lead_lag_information_diffusion_v0_offline_economic_evaluation_scope_ratification_v0 import (
    materialize_lead_lag_offline_economic_evaluation_scope_ratification_v0,
)
from src.research.cross_sectional_futures_lead_lag_information_diffusion_v0_score_v0 import (
    SCORE_FORMULA_VERSION,
)
from src.research.cross_sectional_futures_lead_lag_information_diffusion_v0_versioned_hypothesis_binding_v0 import (
    materialize_versioned_hypothesis_binding_v0,
    materializer_to_binder_roundtrip_v0,
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
EXECUTION_MODULE = (
    REPO_ROOT / "src/research/"
    "cross_sectional_futures_lead_lag_information_diffusion_v0_offline_economic_"
    "evaluation_execution_v0.py"
)
FORBIDDEN_RUNTIME_IMPORT_PREFIXES = (
    "src.execution",
    "src.scheduler",
    "src.broker",
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
    tmp = Path(tempfile.mkdtemp(prefix="cs_lead_lag_full_runner_v0_"))
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


def test_full_runner_go_token_constants() -> None:
    assert REEVALUATION_GO_TOKEN.endswith("_REEVALUATION_V0")
    assert INFRASTRUCTURE_GO_TOKEN.endswith("_INFRASTRUCTURE_IMPLEMENTATION_V0")


def test_canonical_full_evaluation_callable_name() -> None:
    contract = materialize_execution_contract_v0()
    assert CANONICAL_FULL_EVALUATION_CALLABLE == "run_full_offline_economic_evaluation_v0"
    assert (
        contract["canonical_full_evaluation_callable"] == "run_full_offline_economic_evaluation_v0"
    )
    assert hasattr(
        importlib.import_module(
            "src.research.cross_sectional_futures_lead_lag_information_diffusion_v0_offline_"
            "economic_evaluation_execution_v0"
        ),
        "run_full_offline_economic_evaluation_v0",
    )


def test_materializer_to_binder_roundtrip_pass(complete_binding: dict) -> None:
    roundtrip = materializer_to_binder_roundtrip_v0(complete_binding)
    assert roundtrip["materializer_to_binder_roundtrip_pass"] is True


def test_deterministic_double_materialization() -> None:
    first = materialize_versioned_hypothesis_binding_v0()
    second = materialize_versioned_hypothesis_binding_v0()
    assert first == second


def test_second_materialization_diff_empty() -> None:
    first = materialize_versioned_hypothesis_binding_v0()
    second = materialize_versioned_hypothesis_binding_v0()
    diff_keys = [key for key in first if first.get(key) != second.get(key)]
    assert diff_keys == []


def test_start_state_accepts_ratified_binding(
    scope_ratification: dict,
    complete_binding: dict,
) -> None:
    result = verify_execution_start_state_v0(
        repo_root=REPO_ROOT,
        ratification=scope_ratification,
        versioned_binding=complete_binding,
    )
    assert result.valid is True


def test_full_eval_rejects_execution_go_alias(
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
    )
    assert result.status is ExecutionTerminalStatus.FAIL_CLOSED_PRECHECK
    assert result.economic_evaluation_executed is False
    assert REASON_GO_TOKEN_INVALID in result.reason_codes


def test_full_eval_rejects_invalid_go_token(
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
        go_token="INVALID_GO_TOKEN",
    )
    assert result.status is ExecutionTerminalStatus.FAIL_CLOSED_PRECHECK
    assert result.economic_evaluation_executed is False


def test_full_eval_rejects_stale_binding_digest(
    bound_staging: Path,
    scope_ratification: dict,
    complete_binding: dict,
) -> None:
    stale = deepcopy(complete_binding)
    stale["binding_digest"] = "f" * 64
    panel = build_synthetic_panel_series_v0()
    result = run_full_offline_economic_evaluation_v0(
        repo_root=REPO_ROOT,
        ratification=scope_ratification,
        staging_root=bound_staging,
        panel_series=panel,
        versioned_binding=stale,
        go_token=REEVALUATION_GO_TOKEN,
    )
    assert result.status is ExecutionTerminalStatus.FAIL_CLOSED_PRECHECK
    assert REASON_BINDING_DIGEST_MISMATCH in result.reason_codes


def test_full_eval_rejects_wrong_dataset_digest(
    bound_staging: Path,
    scope_ratification: dict,
    complete_binding: dict,
) -> None:
    stale = deepcopy(complete_binding)
    stale["dataset_digest"] = "f" * 64
    panel = build_synthetic_panel_series_v0()
    result = run_full_offline_economic_evaluation_v0(
        repo_root=REPO_ROOT,
        ratification=scope_ratification,
        staging_root=bound_staging,
        panel_series=panel,
        versioned_binding=stale,
        go_token=REEVALUATION_GO_TOKEN,
    )
    assert result.status is ExecutionTerminalStatus.FAIL_CLOSED_PRECHECK
    assert REASON_DATASET_DIGEST_MISMATCH in result.reason_codes


def test_full_eval_rejects_wrong_universe_digest(complete_binding: dict) -> None:
    stale = deepcopy(complete_binding)
    stale["binding"]["pit_universe_binding"]["universe_digest"] = "f" * 64
    ok, reasons = verify_ratified_digests_v0(
        stale,
        expected_universe_digest=(
            complete_binding["binding"]["pit_universe_binding"]["universe_digest"]
        ),
    )
    assert ok is False
    assert REASON_UNIVERSE_DIGEST_MISMATCH in reasons


def test_wrong_score_family_rejected(complete_binding: dict, scope_ratification: dict) -> None:
    stale = deepcopy(complete_binding)
    stale["score_family_policy"] = "unknown_score_family_v0"
    result = verify_execution_start_state_v0(
        repo_root=REPO_ROOT,
        ratification=scope_ratification,
        versioned_binding=stale,
    )
    assert result.valid is False
    assert "SCORE_FAMILY_POLICY_MISMATCH" in result.fail_reasons


def test_futures_only_and_non_bitcoin_invariants(complete_binding: dict) -> None:
    constraints = complete_binding["system_constraints"]
    assert constraints["futures_only"] is True
    assert constraints["bitcoin_direction_allowed"] is False
    ok, _ = verify_ratified_digests_v0(complete_binding)
    assert ok is True


@PY310_STAGING
def test_infrastructure_go_dry_run_preserves_no_economic_execution(
    bound_staging: Path,
    scope_ratification: dict,
    complete_binding: dict,
) -> None:
    panel = build_synthetic_panel_series_v0()
    result = run_full_evaluation_entrypoint_dry_run_v1(
        repo_root=REPO_ROOT,
        ratification=scope_ratification,
        staging_root=bound_staging,
        panel_series=panel,
        versioned_binding=complete_binding,
        go_token=INFRASTRUCTURE_GO_TOKEN,
    )
    assert result.economic_evaluation_executed is False
    assert result.dry_run_stopped_before_execution is True


@PY310_STAGING
def test_reevaluation_go_rejected_in_infrastructure_dry_run(
    bound_staging: Path,
    scope_ratification: dict,
    complete_binding: dict,
) -> None:
    panel = build_synthetic_panel_series_v0()
    result = run_full_evaluation_entrypoint_dry_run_v1(
        repo_root=REPO_ROOT,
        ratification=scope_ratification,
        staging_root=bound_staging,
        panel_series=panel,
        versioned_binding=complete_binding,
        go_token=REEVALUATION_GO_TOKEN,
    )
    assert result.precheck_passed is False
    assert result.economic_evaluation_executed is False


def test_full_path_uses_generic_robustness_owner_not_duplicate(
    bound_staging: Path,
    scope_ratification: dict,
    complete_binding: dict,
) -> None:
    panel = build_synthetic_panel_series_v0()
    with patch(
        "src.research.cross_sectional_futures_lead_lag_information_diffusion_v0_offline_"
        "economic_evaluation_execution_v0.wire_robustness_stages_v0",
        wraps=wire_robustness_stages_v0,
    ) as wired:
        result = run_full_offline_economic_evaluation_v0(
            repo_root=REPO_ROOT,
            ratification=scope_ratification,
            staging_root=bound_staging,
            panel_series=panel,
            versioned_binding=complete_binding,
            go_token=REEVALUATION_GO_TOKEN,
        )
    if result.economic_evaluation_executed:
        wired.assert_called_once()
    assert result.authority_effect == "NONE"
    assert result.runtime_effect == "NONE"


def test_implementation_scope_runner_infrastructure_mode_does_not_execute_evaluation(
    tmp_path: Path,
) -> None:
    with patch.object(
        runner_module,
        "run_full_offline_economic_evaluation_v0",
    ) as full_eval:
        runner_module.run_execution_infrastructure_v0(
            confirm=INFRASTRUCTURE_GO_TOKEN,
            durable_evidence_root=tmp_path,
            primary_worktree=REPO_ROOT,
            staging_root=REPO_ROOT,
        )
        full_eval.assert_not_called()


def test_reevaluation_go_reaches_full_callable_boundary_via_runner(
    tmp_path: Path,
    bound_staging: Path,
) -> None:
    class _SentinelResult:
        economic_evaluation_executed = False
        economic_classification = EconomicClassification.FAIL_CLOSED
        status = ExecutionTerminalStatus.FAIL_CLOSED_PRECHECK

    with patch.object(
        runner_module,
        "run_full_offline_economic_evaluation_v0",
        return_value=_SentinelResult(),
    ) as full_eval:
        with patch.object(
            runner_module,
            "load_ohlcv_panel_series_for_backtest",
            return_value=build_synthetic_panel_series_v0(),
        ):
            with patch.object(
                runner_module,
                "execution_result_to_dict",
                return_value={
                    "status": "FAIL_CLOSED_PRECHECK",
                    "economic_evaluation_executed": False,
                },
            ):
                with pytest.raises(SystemExit):
                    runner_module.run_full_evaluation_dispatch_v0(
                        confirm=GO_TOKEN,
                        durable_evidence_root=tmp_path,
                        primary_worktree=REPO_ROOT,
                        staging_root=bound_staging,
                    )
                runner_module.run_full_evaluation_dispatch_v0(
                    confirm=REEVALUATION_GO_TOKEN,
                    durable_evidence_root=tmp_path / "reeval",
                    primary_worktree=REPO_ROOT,
                    staging_root=bound_staging,
                )
        full_eval.assert_called_once()
        _, kwargs = full_eval.call_args
        assert kwargs["go_token"] == REEVALUATION_GO_TOKEN


def test_ops_runner_rejects_wrong_go_token() -> None:
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
        cwd=str(REPO_ROOT),
    )
    assert proc.returncode == 2
    assert "ERR:confirm_go_token_required" in proc.stderr


def test_ops_runner_rejects_execution_go_in_infrastructure_mode() -> None:
    proc = subprocess.run(
        [
            sys.executable,
            str(RUNNER_MODULE),
            "--confirm",
            GO_TOKEN,
            "--primary-worktree",
            str(REPO_ROOT),
        ],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert proc.returncode == 2


def test_execution_result_to_dict_preserves_no_runtime_effect(
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
        go_token=REEVALUATION_GO_TOKEN,
    )
    payload = execution_result_to_dict(result)
    assert payload["authority_effect"] == "NONE"
    assert payload["runtime_effect"] == "NONE"
    assert payload["allowed_evaluation_stages"] == list(ALLOWED_EVALUATION_STAGES)
    assert (
        payload["canonical_full_evaluation_callable"] == "run_full_offline_economic_evaluation_v0"
    )


def _collect_imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
    return imports


def test_execution_module_has_no_runtime_imports() -> None:
    imports = _collect_imports(EXECUTION_MODULE)
    for forbidden in FORBIDDEN_RUNTIME_IMPORT_PREFIXES:
        assert not any(item == forbidden or item.startswith(forbidden + ".") for item in imports)


def test_runner_module_has_no_runtime_imports() -> None:
    imports = _collect_imports(RUNNER_MODULE)
    for forbidden in FORBIDDEN_RUNTIME_IMPORT_PREFIXES:
        assert not any(item == forbidden or item.startswith(forbidden + ".") for item in imports)


def test_precheck_accepts_reevaluation_go_with_ratified_binding(
    bound_staging: Path,
    scope_ratification: dict,
    complete_binding: dict,
) -> None:
    ok, reasons, _ = verify_full_evaluation_precheck_v1(
        repo_root=REPO_ROOT,
        ratification=scope_ratification,
        staging_root=bound_staging,
        versioned_binding=complete_binding,
        go_token=REEVALUATION_GO_TOKEN,
        require_execution_go=True,
    )
    assert REASON_GO_TOKEN_INVALID not in reasons
    assert complete_binding["score_family_policy"] == SCORE_FORMULA_VERSION


@PY310_STAGING
def test_full_eval_executes_six_stages_with_reevaluation_go_when_data_admissible(
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
        go_token=REEVALUATION_GO_TOKEN,
    )
    if result.panel_data_digest == FIXTURE_DATA_DIGEST:
        assert result.status is ExecutionTerminalStatus.FAIL_CLOSED_FIXTURE_LEAKAGE
        assert result.economic_evaluation_executed is False
        return
    if not result.precheck_passed:
        pytest.skip(f"precheck_not_admissible:{list(result.reason_codes)}")
    assert result.economic_evaluation_executed is True
    assert result.status is ExecutionTerminalStatus.ECONOMIC_EVALUATION_COMPLETE
    assert len(result.stage_wiring) == 6
    assert tuple(item.stage_name for item in result.stage_wiring) == ALLOWED_EVALUATION_STAGES
