"""Repair contract tests for lead-lag v0 invocation-bound execution authorization."""

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
    AUTHORITY_EFFECT,
    GO_TOKEN,
    REASON_BACKTEST_RUNTIME_DECISION_PARITY_FAIL,
    REASON_BINDING_DIGEST_MISMATCH,
    REASON_DATASET_DIGEST_MISMATCH,
    REASON_ECONOMIC_EVALUATION_NOT_AUTHORIZED,
    REASON_FULL_CANONICAL_PARITY_NOT_PROVEN,
    REASON_GO_TOKEN_INVALID,
    REASON_UNIVERSE_DIGEST_MISMATCH,
    RUNTIME_EFFECT,
    materialize_runner_envelope_v0,
    resolve_identity_operator_go_v0,
    verify_full_evaluation_precheck_v1,
)
from src.research.cross_sectional_futures_lead_lag_information_diffusion_v0_offline_economic_evaluation_scope_ratification_v0 import (
    ECONOMIC_EVALUATION_AUTHORIZED,
    REASON_CONFIG_DIGEST_MISMATCH,
    REASON_IMPLEMENTATION_DIGEST_MISMATCH,
    REASON_OFFLINE_BOUNDARY_VIOLATION,
    REASON_SCOPE_RATIFICATION_MISMATCH,
    evaluate_invocation_bound_economic_evaluation_authorization_v0,
    materialize_invocation_bound_authorization_contract_v0,
    materialize_lead_lag_offline_economic_evaluation_scope_ratification_v0,
)
from src.research.cross_sectional_futures_lead_lag_information_diffusion_v0_versioned_hypothesis_binding_v0 import (
    materialize_versioned_hypothesis_binding_v0,
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


def _dispatch_boundary_evaluation_result():
    from src.research.cross_sectional_futures_lead_lag_information_diffusion_v0_offline_economic_evaluation_execution_v0 import (
        AUTHORITY_EFFECT,
        EconomicClassification,
        ExecutionTerminalStatus,
        FullEconomicEvaluationResultV0,
        RUNTIME_EFFECT,
    )

    return FullEconomicEvaluationResultV0(
        status=ExecutionTerminalStatus.FAIL_CLOSED_PRECHECK,
        precheck_passed=True,
        bound_dataset_materialized=False,
        dataset_period_match=False,
        panel_data_digest="0" * 64,
        data_digest_is_fixture=False,
        stage_wiring=(),
        backtest=None,
        robustness=None,
        robustness_metrics=None,
        economic_viability_evidence={},
        economic_classification=EconomicClassification.FAIL_CLOSED,
        economic_validity_offline_gate_pass=False,
        promotion_candidate_eligible=False,
        economic_evaluation_executed=False,
        reason_codes=(),
        authority_effect=AUTHORITY_EFFECT,
        runtime_effect=RUNTIME_EFFECT,
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
    tmp = Path(tempfile.mkdtemp(prefix="cs_lead_lag_auth_repair_v0_"))
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


def _load_ops_config() -> dict:
    from src.research.cross_sectional_futures_lead_lag_information_diffusion_v0_offline_economic_evaluation_execution_v0 import (
        load_ops_evaluation_config_v0,
    )

    return load_ops_evaluation_config_v0(REPO_ROOT)


def _allowed_tokens() -> frozenset[str]:
    from src.research.cross_sectional_futures_lead_lag_information_diffusion_v0_offline_economic_evaluation_execution_v0 import (
        ALLOWED_FULL_EVALUATION_GO_TOKENS,
    )

    return ALLOWED_FULL_EVALUATION_GO_TOKENS


def _make_envelope(*, go_token: str, parity: bool) -> object:
    return materialize_runner_envelope_v0(
        requested_operator_go=go_token,
        dispatched_operator_go=resolve_identity_operator_go_v0(go_token),
        dispatch_rc=0,
        preexecution_parity_guard_pass=parity,
        full_canonical_chain_wired=parity,
        backtest_runtime_decision_parity_pass=parity,
    )


def test_persisted_authorization_default_remains_false(scope_ratification: dict) -> None:
    assert ECONOMIC_EVALUATION_AUTHORIZED is False
    assert scope_ratification["economic_evaluation_authorized"] is False


def test_invocation_contract_declares_invocation_bound_model() -> None:
    contract = materialize_invocation_bound_authorization_contract_v0()
    assert contract["authorization_model"] == "INVOCATION_BOUND_FAIL_CLOSED"
    assert contract["persisted_economic_evaluation_authorized_default"] is False
    assert contract["invocation_elevates_authorization"] is True


def test_valid_execution_go_authorizes_invocation(
    scope_ratification: dict,
    complete_binding: dict,
) -> None:
    result = evaluate_invocation_bound_economic_evaluation_authorization_v0(
        ratification=scope_ratification,
        versioned_binding=complete_binding,
        go_token=GO_TOKEN,
        allowed_execution_go_tokens=_allowed_tokens(),
        ops_config=_load_ops_config(),
        full_chain_wired=True,
        parity_pass=True,
    )
    assert result.authorized is True
    assert result.economic_evaluation_authorized is True
    assert result.reason_codes == ()


def test_missing_execution_go_blocks(scope_ratification: dict, complete_binding: dict) -> None:
    result = evaluate_invocation_bound_economic_evaluation_authorization_v0(
        ratification=scope_ratification,
        versioned_binding=complete_binding,
        go_token=None,
        allowed_execution_go_tokens=_allowed_tokens(),
        ops_config=_load_ops_config(),
        full_chain_wired=True,
        parity_pass=True,
    )
    assert result.authorized is False
    assert REASON_ECONOMIC_EVALUATION_NOT_AUTHORIZED in result.reason_codes


def test_wrong_execution_go_blocks(scope_ratification: dict, complete_binding: dict) -> None:
    result = evaluate_invocation_bound_economic_evaluation_authorization_v0(
        ratification=scope_ratification,
        versioned_binding=complete_binding,
        go_token="GO_WRONG_TOKEN",
        allowed_execution_go_tokens=_allowed_tokens(),
        ops_config=_load_ops_config(),
        full_chain_wired=True,
        parity_pass=True,
    )
    assert result.authorized is False
    assert REASON_ECONOMIC_EVALUATION_NOT_AUTHORIZED in result.reason_codes


def test_scope_ratification_mismatch_blocks(
    scope_ratification: dict,
    complete_binding: dict,
) -> None:
    stale = deepcopy(scope_ratification)
    stale["hypothesis_id"] = "WRONG_HYPOTHESIS"
    result = evaluate_invocation_bound_economic_evaluation_authorization_v0(
        ratification=stale,
        versioned_binding=complete_binding,
        go_token=GO_TOKEN,
        allowed_execution_go_tokens=_allowed_tokens(),
        ops_config=_load_ops_config(),
        full_chain_wired=True,
        parity_pass=True,
    )
    assert result.authorized is False
    assert REASON_SCOPE_RATIFICATION_MISMATCH in result.reason_codes


def test_binding_digest_mismatch_blocks(
    scope_ratification: dict,
    complete_binding: dict,
) -> None:
    stale = deepcopy(complete_binding)
    stale["binding_digest"] = "f" * 64
    result = evaluate_invocation_bound_economic_evaluation_authorization_v0(
        ratification=scope_ratification,
        versioned_binding=stale,
        go_token=GO_TOKEN,
        allowed_execution_go_tokens=_allowed_tokens(),
        ops_config=_load_ops_config(),
        full_chain_wired=True,
        parity_pass=True,
    )
    assert result.authorized is False
    assert REASON_BINDING_DIGEST_MISMATCH in result.reason_codes


def test_dataset_digest_mismatch_blocks(
    scope_ratification: dict,
    complete_binding: dict,
) -> None:
    stale = deepcopy(complete_binding)
    stale["dataset_digest"] = "f" * 64
    result = evaluate_invocation_bound_economic_evaluation_authorization_v0(
        ratification=scope_ratification,
        versioned_binding=stale,
        go_token=GO_TOKEN,
        allowed_execution_go_tokens=_allowed_tokens(),
        ops_config=_load_ops_config(),
        full_chain_wired=True,
        parity_pass=True,
    )
    assert result.authorized is False
    assert REASON_DATASET_DIGEST_MISMATCH in result.reason_codes


def test_universe_digest_mismatch_blocks(
    scope_ratification: dict,
    complete_binding: dict,
) -> None:
    stale = deepcopy(complete_binding)
    stale["binding"]["pit_universe_binding"]["universe_digest"] = "f" * 64
    result = evaluate_invocation_bound_economic_evaluation_authorization_v0(
        ratification=scope_ratification,
        versioned_binding=stale,
        go_token=GO_TOKEN,
        allowed_execution_go_tokens=_allowed_tokens(),
        ops_config=_load_ops_config(),
        full_chain_wired=True,
        parity_pass=True,
    )
    assert result.authorized is False
    assert REASON_UNIVERSE_DIGEST_MISMATCH in result.reason_codes


def test_implementation_digest_mismatch_blocks(
    scope_ratification: dict,
    complete_binding: dict,
) -> None:
    ops = deepcopy(_load_ops_config())
    ops["implementation_digest"] = "f" * 64
    result = evaluate_invocation_bound_economic_evaluation_authorization_v0(
        ratification=scope_ratification,
        versioned_binding=complete_binding,
        go_token=GO_TOKEN,
        allowed_execution_go_tokens=_allowed_tokens(),
        ops_config=ops,
        full_chain_wired=True,
        parity_pass=True,
    )
    assert result.authorized is False
    assert REASON_IMPLEMENTATION_DIGEST_MISMATCH in result.reason_codes


def test_config_digest_mismatch_blocks(
    scope_ratification: dict,
    complete_binding: dict,
) -> None:
    ops = deepcopy(_load_ops_config())
    ops["config_digest"] = "f" * 64
    result = evaluate_invocation_bound_economic_evaluation_authorization_v0(
        ratification=scope_ratification,
        versioned_binding=complete_binding,
        go_token=GO_TOKEN,
        allowed_execution_go_tokens=_allowed_tokens(),
        ops_config=ops,
        full_chain_wired=True,
        parity_pass=True,
    )
    assert result.authorized is False
    assert REASON_CONFIG_DIGEST_MISMATCH in result.reason_codes


def test_bitcoin_presence_blocks(scope_ratification: dict, complete_binding: dict) -> None:
    stale = deepcopy(complete_binding)
    stale["system_constraints"]["bitcoin_direction_allowed"] = True
    result = evaluate_invocation_bound_economic_evaluation_authorization_v0(
        ratification=scope_ratification,
        versioned_binding=stale,
        go_token=GO_TOKEN,
        allowed_execution_go_tokens=_allowed_tokens(),
        ops_config=_load_ops_config(),
        full_chain_wired=True,
        parity_pass=True,
    )
    assert result.authorized is False
    assert "BITCOIN_DIRECTION_VIOLATION" in result.reason_codes


def test_non_futures_scope_blocks(scope_ratification: dict, complete_binding: dict) -> None:
    stale = deepcopy(complete_binding)
    stale["system_constraints"]["futures_only"] = False
    result = evaluate_invocation_bound_economic_evaluation_authorization_v0(
        ratification=scope_ratification,
        versioned_binding=stale,
        go_token=GO_TOKEN,
        allowed_execution_go_tokens=_allowed_tokens(),
        ops_config=_load_ops_config(),
        full_chain_wired=True,
        parity_pass=True,
    )
    assert result.authorized is False
    assert "FUTURES_ONLY_VIOLATION" in result.reason_codes


def test_offline_boundary_violation_blocks(
    scope_ratification: dict,
    complete_binding: dict,
) -> None:
    stale = deepcopy(scope_ratification)
    stale["runtime_effect"] = "LIVE"
    result = evaluate_invocation_bound_economic_evaluation_authorization_v0(
        ratification=stale,
        versioned_binding=complete_binding,
        go_token=GO_TOKEN,
        allowed_execution_go_tokens=_allowed_tokens(),
        ops_config=_load_ops_config(),
        full_chain_wired=True,
        parity_pass=True,
    )
    assert result.authorized is False
    assert REASON_OFFLINE_BOUNDARY_VIOLATION in result.reason_codes


def test_full_canonical_chain_required(
    scope_ratification: dict,
    complete_binding: dict,
) -> None:
    result = evaluate_invocation_bound_economic_evaluation_authorization_v0(
        ratification=scope_ratification,
        versioned_binding=complete_binding,
        go_token=GO_TOKEN,
        allowed_execution_go_tokens=_allowed_tokens(),
        ops_config=_load_ops_config(),
        full_chain_wired=False,
        parity_pass=True,
    )
    assert result.authorized is False
    assert REASON_FULL_CANONICAL_PARITY_NOT_PROVEN in result.reason_codes


def test_backtest_runtime_parity_required(
    scope_ratification: dict,
    complete_binding: dict,
) -> None:
    result = evaluate_invocation_bound_economic_evaluation_authorization_v0(
        ratification=scope_ratification,
        versioned_binding=complete_binding,
        go_token=GO_TOKEN,
        allowed_execution_go_tokens=_allowed_tokens(),
        ops_config=_load_ops_config(),
        full_chain_wired=True,
        parity_pass=False,
    )
    assert result.authorized is False
    assert REASON_BACKTEST_RUNTIME_DECISION_PARITY_FAIL in result.reason_codes


@PY310_STAGING
def test_production_precheck_authorizes_valid_execution_go_without_evaluation(
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
        ok, reasons, _ = verify_full_evaluation_precheck_v1(
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
    assert REASON_ECONOMIC_EVALUATION_NOT_AUTHORIZED not in reasons


@PY310_STAGING
def test_production_precheck_blocks_missing_go(
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
        go_token=None,
        require_execution_go=True,
        runner_envelope=envelope,
        materialize_dataset=False,
    )
    assert ok is False
    assert REASON_ECONOMIC_EVALUATION_NOT_AUTHORIZED in reasons


@PY310_STAGING
def test_production_precheck_blocks_wrong_go(
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
        go_token="GO_WRONG_TOKEN",
        require_execution_go=True,
        runner_envelope=envelope,
        materialize_dataset=False,
    )
    assert ok is False
    assert REASON_GO_TOKEN_INVALID in reasons
    assert REASON_ECONOMIC_EVALUATION_NOT_AUTHORIZED in reasons


@PY310_STAGING
def test_production_runner_reaches_dispatch_boundary_without_economic_execution(
    bound_staging: Path,
) -> None:
    with (
        patch.object(
            runner_module,
            "run_full_offline_economic_evaluation_v0",
            return_value=_dispatch_boundary_evaluation_result(),
        ) as full_eval,
        patch(
            "src.research.cross_sectional_futures_lead_lag_information_diffusion_v0_offline_"
            "economic_evaluation_execution_v0.verify_panel_staging_source_manifests_v1",
            return_value=(True, 0, ()),
        ),
        patch(
            "src.research.cross_sectional_futures_lead_lag_information_diffusion_v0_offline_"
            "economic_evaluation_execution_v0.load_ohlcv_panel_series_for_backtest",
            return_value=(),
        ),
    ):
        runner_module.run_bounded_full_evaluation_dispatch_v0(
            confirm=GO_TOKEN,
            durable_evidence_root=Path(tempfile.mkdtemp(prefix="cs_lead_lag_auth_dispatch_")),
            primary_worktree=REPO_ROOT,
            staging_root=bound_staging,
        )
        full_eval.assert_called_once()
        assert full_eval.call_args.kwargs["go_token"] == GO_TOKEN


def test_repair_preserves_no_runtime_or_authority_effect() -> None:
    assert RUNTIME_EFFECT == "NONE"
    assert AUTHORITY_EFFECT == "NONE"


def test_runner_cli_wrong_go_still_fail_closed() -> None:
    proc = subprocess.run(
        [
            sys.executable,
            str(RUNNER_MODULE),
            "--confirm",
            "GO_WRONG_TOKEN",
            "--primary-worktree",
            str(REPO_ROOT),
        ],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert proc.returncode == 2
    assert "ERR:confirm_go_token_required" in proc.stderr
