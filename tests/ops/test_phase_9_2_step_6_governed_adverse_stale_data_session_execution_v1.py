"""Tests for PHASE_9_2_STEP_6_GOVERNED_ADVERSE_STALE_DATA_SESSION_EXECUTION_BINDING_V1."""

from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

from src.ops.phase_9_2_step_6_adverse_stale_data_session_continuation_v1.constants_v1 import (
    NETWORK_SESSION_ALLOWED as CONTINUATION_NETWORK_SESSION_ALLOWED,
)
from src.ops.phase_9_2_step_6_adverse_stale_data_session_continuation_v1.productive_executor_v1 import (
    run_step6_productive_executor_wiring_v1,
)
from src.ops.phase_9_2_step_6_governed_adverse_stale_data_session_execution_v1.constants_v1 import (
    MODE_GOVERNED_REAL_NETWORK_SESSION,
    MODE_PROVE_BINDING_ONLY,
    NETWORK_SESSION_ALLOWED,
    PHASE_9_2_STEP_6_STATUS,
    PRODUCTIVE_ENTRYPOINT_PATH,
    RUNTIME_OVERRIDE_KEY_STALE_CONTROL,
    RUNTIME_OVERRIDE_KEY_TRANSPORT_FAULT,
    SESSION_EXECUTED,
)
from src.ops.phase_9_2_step_6_governed_adverse_stale_data_session_execution_v1.failure_injection_v1 import (
    run_step6_execution_binding_failure_injection_v1,
)
from src.ops.phase_9_2_step_6_governed_adverse_stale_data_session_execution_v1.governed_session_execution_v1 import (
    evaluate_execution_mode_gate_v1,
    execute_governed_step6_session_offline_fail_closed_v1,
    prove_step6_execution_binding_v1,
    request_real_network_offline_fail_closed_v1,
)
from src.ops.phase_9_2_step_6_governed_adverse_stale_data_session_execution_v1.stale_control_binding_v1 import (
    bind_stale_control_into_runtime_overrides_v1,
    build_default_disabled_stale_control_v1,
    prove_stale_control_default_disabled_v1,
    prove_stale_injection_classifies_via_canonical_owner_v1,
    prove_step4_transport_fault_semantics_unchanged_v1,
    prove_wallclock_receive_path_binding_v1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.config_v1 import (
    load_activation_config_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CLI = REPO_ROOT / PRODUCTIVE_ENTRYPOINT_PATH
CONTINUATION_CLI = (
    REPO_ROOT / "scripts/ops/run_phase_9_2_step_6_adverse_stale_data_session_continuation_v1.py"
)


def _sha() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=str(REPO_ROOT), text=True
    ).strip()


def _cfg() -> str:
    return str(
        load_activation_config_v1(
            config_path=REPO_ROOT
            / "config/runtime/single_future_stateful_no_order_runtime_activation_v1.json"
        ).config_digest
    )


def test_default_disabled() -> None:
    proof = prove_stale_control_default_disabled_v1()
    assert proof["ok"] is True
    assert proof["STALE_CONTROL_DEFAULT_DISABLED"] is True
    assert NETWORK_SESSION_ALLOWED is False
    assert SESSION_EXECUTED is False
    assert PHASE_9_2_STEP_6_STATUS == "OPEN"


def test_binding_only_starts_no_network() -> None:
    result = prove_step6_execution_binding_v1(
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
        repo_root=REPO_ROOT,
    )
    assert result.ok is True
    assert result.network_session_started is False
    assert result.authorization_consumed is False
    assert result.confirm_token_consumed is False
    assert result.mode == MODE_PROVE_BINDING_ONLY
    assert result.claims["READY_FOR_SEPARATE_GOVERNED_SESSION_EXECUTION"] is True


def test_stale_control_productively_reachable() -> None:
    receive = prove_wallclock_receive_path_binding_v1()
    assert receive["ok"] is True
    assert receive["GOVERNED_STALE_CONTROL_PRODUCTIVELY_BOUND"] is True
    assert receive["WALLCLOCK_RECEIVE_PATH_BOUND"] is True
    overrides = bind_stale_control_into_runtime_overrides_v1()
    assert RUNTIME_OVERRIDE_KEY_STALE_CONTROL in overrides
    assert RUNTIME_OVERRIDE_KEY_STALE_CONTROL != RUNTIME_OVERRIDE_KEY_TRANSPORT_FAULT
    ctrl = build_default_disabled_stale_control_v1()
    assert ctrl.schedule.enabled is False


def test_stale_injection_classifies_via_canonical_owner() -> None:
    proof = prove_stale_injection_classifies_via_canonical_owner_v1()
    assert proof["ok"] is True
    assert proof["ALPHA_FAILS_CLOSED_ON_STALE"] is True
    assert proof["NO_FABRICATED_MARKET_OBSERVATION"] is True


def test_alpha_blocked_on_stale_and_protections() -> None:
    proof = prove_stale_injection_classifies_via_canonical_owner_v1()
    assert proof["ALPHA_FAILS_CLOSED_ON_STALE"] is True
    assert proof["NO_DUPLICATE_CONFIRMATION_ADVANCE"] is True
    binding = prove_step6_execution_binding_v1(
        expected_repository_sha=_sha(), expected_config_digest=_cfg(), repo_root=REPO_ROOT
    )
    assert binding.claims["EXIT_PROTECTION_PRESERVED"] is True
    assert binding.claims["RISK_PROTECTION_PRESERVED"] is True
    assert binding.claims["SAFETY_PROTECTION_PRESERVED"] is True
    assert binding.claims["NO_DUPLICATE_FILL"] is True


def test_missing_authorization_hard_stop() -> None:
    result = execute_governed_step6_session_offline_fail_closed_v1(
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
        authorization_id="",
        authorization_digest="",
        confirm_token_binding_sha256="a" * 64,
        getpass_fn=lambda _p: "token",
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_allowed=True,
        stdin_isatty=True,
    )
    assert result.ok is False
    assert result.network_session_started is False
    assert result.authorization_consumed is False
    assert any("AUTHORIZATION" in b for b in result.blockers)


def test_network_session_allowed_false_hard_stop() -> None:
    gate = evaluate_execution_mode_gate_v1(
        mode=MODE_GOVERNED_REAL_NETWORK_SESSION,
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_allowed=False,
        public_md_only=True,
        authorization_valid=True,
        confirm_token_valid=True,
        stdin_isatty=True,
    )
    assert gate["ok"] is False
    assert "NETWORK_SESSION_ALLOWED_FALSE" in gate["blockers"]


def test_non_tty_hard_stop_before_consumption() -> None:
    result = execute_governed_step6_session_offline_fail_closed_v1(
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
        authorization_id="auth_1",
        authorization_digest="b" * 64,
        confirm_token_binding_sha256="c" * 64,
        getpass_fn=lambda _p: "must-not-consume",
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_allowed=True,
        stdin_isatty=False,
    )
    assert result.ok is False
    assert result.authorization_consumed is False
    assert result.confirm_token_consumed is False
    assert result.network_session_started is False
    assert any("TTY" in b for b in result.blockers)


def test_invalid_confirm_hard_stop() -> None:
    expected = hashlib.sha256(b"expected-token").hexdigest()
    result = execute_governed_step6_session_offline_fail_closed_v1(
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
        authorization_id="auth_1",
        authorization_digest="d" * 64,
        confirm_token_binding_sha256=expected,
        getpass_fn=lambda _p: "wrong-token",
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_allowed=True,
        stdin_isatty=True,
    )
    assert result.ok is False
    assert result.confirm_token_consumed is False
    assert any("CONFIRM_TOKEN" in b for b in result.blockers)


def test_private_credential_order_unreachable() -> None:
    result = prove_step6_execution_binding_v1(
        expected_repository_sha=_sha(), expected_config_digest=_cfg(), repo_root=REPO_ROOT
    )
    assert result.claims["PRIVATE_ENDPOINT_REACHABLE"] is False
    assert result.claims["CREDENTIAL_PATH_REACHABLE"] is False
    assert result.claims["ORDER_SIDE_EFFECT_REACHABLE"] is False
    assert result.claims["PUBLIC_MD_ONLY_BOUNDARY_PRESERVED"] is True


def test_step4_transport_fault_unchanged() -> None:
    proof = prove_step4_transport_fault_semantics_unchanged_v1()
    assert proof["ok"] is True
    assert proof["STEP4_TRANSPORT_FAULT_SEMANTICS_CHANGED"] is False


def test_existing_step6_binding_proof_pass() -> None:
    assert CONTINUATION_NETWORK_SESSION_ALLOWED is False
    wiring = run_step6_productive_executor_wiring_v1(
        repository_sha=_sha(),
        config_digest=_cfg(),
        request_real_network=False,
        owner_go=True,
    )
    assert wiring.ok is True
    assert wiring.network_session_started is False
    proc = subprocess.run(
        [sys.executable, str(CONTINUATION_CLI), "prove-binding", "--json"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    assert '"ok": true' in proc.stdout.lower() or '"ok":true' in proc.stdout.replace(" ", "")


def test_failure_injection_matrix_pass() -> None:
    fi = run_step6_execution_binding_failure_injection_v1(
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
    )
    assert fi["ok"] is True
    assert fi["FAILURE_INJECTION_TESTS_PASS"] is True
    assert fi["network_session_started"] is False


def test_request_real_network_fail_closed() -> None:
    result = request_real_network_offline_fail_closed_v1(
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
        owner_go=True,
        operator_authorization_explicit=True,
        network_session_allowed=True,
        stdin_isatty=True,
    )
    assert result.ok is False
    assert result.network_session_started is False


def test_cli_prove_binding() -> None:
    proc = subprocess.run(
        [sys.executable, str(CLI), "prove-binding", "--json"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    assert "READY_FOR_SEPARATE_GOVERNED_SESSION_EXECUTION" in proc.stdout
