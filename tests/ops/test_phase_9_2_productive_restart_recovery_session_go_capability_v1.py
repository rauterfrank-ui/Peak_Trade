"""Tests for PHASE_9_2_PRODUCTIVE_RESTART_RECOVERY_SESSION_GO_CAPABILITY_V1."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from src.ops.phase_9_2_productive_public_md_restart_recovery_network_entrypoint_v1.constants_v1 import (
    PRODUCTIVE_NETWORK_SESSION_EXECUTION_ALLOWED,
    TARGET_SESSION_ID as ENTRYPOINT_SESSION_ID,
)
from src.ops.phase_9_2_productive_public_md_restart_recovery_network_entrypoint_v1.orchestrator_v1 import (
    evaluate_productive_session_start_gates_v1,
    reject_productive_session_start_v1,
)
from src.ops.phase_9_2_productive_restart_recovery_session_go_capability_v1.constants_v1 import (
    ACTIVATION_STATUS_ACTIVE,
    ACTIVATION_STATUS_INACTIVE,
    ACTIVATION_STATUS_REVOKED,
    CAPABILITY_ID,
    TARGET_ENTRYPOINT_ID,
    TARGET_ENTRYPOINT_PATH,
    TARGET_SESSION_ID,
)
from src.ops.phase_9_2_productive_restart_recovery_session_go_capability_v1.contract_v1 import (
    SessionGoContractError,
    build_session_go_authority_v1,
    parse_session_go_authority_v1,
)
from src.ops.phase_9_2_productive_restart_recovery_session_go_capability_v1.digest_v1 import (
    write_json_atomic_v1,
)
from src.ops.phase_9_2_productive_restart_recovery_session_go_capability_v1.gate_v1 import (
    evaluate_session_go_gate_v1,
)
from src.ops.phase_9_2_productive_restart_recovery_session_go_capability_v1.parity_v1 import (
    prove_phase92_session_go_parity_v1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.config_v1 import (
    load_activation_config_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CLI = (
    REPO_ROOT / "scripts/ops/run_phase_9_2_productive_restart_recovery_session_go_capability_v1.py"
)
ENTRYPOINT_CLI = (
    REPO_ROOT
    / "scripts/ops/run_phase_9_2_productive_public_md_restart_recovery_network_entrypoint_v1.py"
)
NOW = 1_700_000_000.0
SHA = "0cc5c91583733e37ccc2f4b3ad8696ec76b0c5d5"


def _cfg() -> str:
    return str(
        load_activation_config_v1(
            config_path=REPO_ROOT
            / "config/runtime/single_future_stateful_no_order_runtime_activation_v1.json"
        ).config_digest
    )


def _active_go(**overrides):
    payload = build_session_go_authority_v1(
        session_go_id="sgo_test_active_v1",
        expected_repository_sha=overrides.pop("expected_repository_sha", SHA),
        expected_config_digest=overrides.pop("expected_config_digest", _cfg()),
        issued_at=overrides.pop("issued_at", NOW - 10),
        not_before=overrides.pop("not_before", NOW - 5),
        expires_at=overrides.pop("expires_at", NOW + 3600),
        activation_status=overrides.pop("activation_status", ACTIVATION_STATUS_ACTIVE),
        session_id=overrides.pop("session_id", TARGET_SESSION_ID),
        entrypoint_id=overrides.pop("entrypoint_id", TARGET_ENTRYPOINT_ID),
        entrypoint_path=overrides.pop("entrypoint_path", TARGET_ENTRYPOINT_PATH),
        network_session_execution_authorized_by_this_go=overrides.pop(
            "network_session_execution_authorized_by_this_go", True
        ),
        fixture_non_authoritative=overrides.pop("fixture_non_authoritative", False),
    ).to_dict()
    if overrides:
        payload.update(overrides)
        payload["session_go_digest"] = ""
        return parse_session_go_authority_v1(payload)
    return parse_session_go_authority_v1(payload)


def test_01_capability_constants_and_preflight() -> None:
    assert CAPABILITY_ID.endswith("SESSION_GO_CAPABILITY_V1")
    assert TARGET_SESSION_ID == ENTRYPOINT_SESSION_ID
    assert PRODUCTIVE_NETWORK_SESSION_EXECUTION_ALLOWED is False
    proc = subprocess.run(
        [sys.executable, str(CLI), "preflight"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["ok"] is True
    assert payload["session_started"] is False
    assert payload["authorization_consumed"] is False
    assert payload["network_request_count"] == 0


def test_02_schema_parse_and_digest() -> None:
    auth = _active_go()
    assert auth.session_go_digest
    assert len(auth.session_go_digest) == 64
    assert auth.entrypoint_path == TARGET_ENTRYPOINT_PATH
    assert auth.entrypoint_id == TARGET_ENTRYPOINT_ID


def test_03_missing_session_go_fails_closed() -> None:
    result = evaluate_session_go_gate_v1(
        expected_repository_sha=SHA,
        expected_config_digest=_cfg(),
        now_unix=NOW,
        owner_go=True,
        owner_session_go=True,
    )
    assert result.ok is False
    assert "SESSION_GO_MISSING" in result.blockers
    assert result.session_started is False
    assert result.authorization_consumed is False
    assert result.network_request_count == 0
    assert result.side_effects_occurred is False


def test_04_inactive_session_go_fails_closed() -> None:
    auth = _active_go(activation_status=ACTIVATION_STATUS_INACTIVE)
    result = evaluate_session_go_gate_v1(
        expected_repository_sha=SHA,
        expected_config_digest=_cfg(),
        now_unix=NOW,
        owner_go=True,
        owner_session_go=True,
        session_go_payload=auth,
        authorization_present=True,
        confirm_token_present=True,
    )
    assert result.ok is False
    assert "SESSION_GO_INACTIVE" in result.blockers


def test_05_expired_session_go_fails_closed() -> None:
    auth = _active_go(expires_at=NOW - 1)
    result = evaluate_session_go_gate_v1(
        expected_repository_sha=SHA,
        expected_config_digest=_cfg(),
        now_unix=NOW,
        owner_go=True,
        owner_session_go=True,
        session_go_payload=auth,
        authorization_present=True,
        confirm_token_present=True,
    )
    assert result.ok is False
    assert "SESSION_GO_EXPIRED" in result.blockers


def test_06_revoked_session_go_fails_closed() -> None:
    auth = _active_go(activation_status=ACTIVATION_STATUS_REVOKED)
    result = evaluate_session_go_gate_v1(
        expected_repository_sha=SHA,
        expected_config_digest=_cfg(),
        now_unix=NOW,
        owner_go=True,
        owner_session_go=True,
        session_go_payload=auth,
        authorization_present=True,
        confirm_token_present=True,
    )
    assert result.ok is False
    assert "SESSION_GO_REVOKED" in result.blockers


def test_07_sha_mismatch_fails_closed() -> None:
    auth = _active_go()
    result = evaluate_session_go_gate_v1(
        expected_repository_sha="deadbeef" * 5,
        expected_config_digest=_cfg(),
        now_unix=NOW,
        owner_go=True,
        owner_session_go=True,
        session_go_payload=auth,
        authorization_present=True,
        confirm_token_present=True,
    )
    assert result.ok is False
    assert "SESSION_GO_REPOSITORY_SHA_MISMATCH" in result.blockers


def test_08_config_digest_mismatch_fails_closed() -> None:
    auth = _active_go()
    result = evaluate_session_go_gate_v1(
        expected_repository_sha=SHA,
        expected_config_digest="0" * 64,
        now_unix=NOW,
        owner_go=True,
        owner_session_go=True,
        session_go_payload=auth,
        authorization_present=True,
        confirm_token_present=True,
    )
    assert result.ok is False
    assert "SESSION_GO_CONFIG_DIGEST_MISMATCH" in result.blockers


def test_09_session_id_mismatch_fails_closed() -> None:
    auth = _active_go(session_id="wrong_session")
    result = evaluate_session_go_gate_v1(
        expected_repository_sha=SHA,
        expected_config_digest=_cfg(),
        now_unix=NOW,
        owner_go=True,
        owner_session_go=True,
        session_go_payload=auth,
        authorization_present=True,
        confirm_token_present=True,
    )
    assert result.ok is False
    assert "SESSION_GO_SESSION_ID_MISMATCH" in result.blockers


def test_10_entrypoint_mismatch_fails_closed() -> None:
    auth = _active_go(entrypoint_path="scripts/ops/not_the_entrypoint.py")
    result = evaluate_session_go_gate_v1(
        expected_repository_sha=SHA,
        expected_config_digest=_cfg(),
        now_unix=NOW,
        owner_go=True,
        owner_session_go=True,
        session_go_payload=auth,
        authorization_present=True,
        confirm_token_present=True,
    )
    assert result.ok is False
    assert "SESSION_GO_ENTRYPOINT_PATH_MISMATCH" in result.blockers


def test_11_owner_go_without_session_go_fails_closed() -> None:
    auth = _active_go()
    result = evaluate_session_go_gate_v1(
        expected_repository_sha=SHA,
        expected_config_digest=_cfg(),
        now_unix=NOW,
        owner_go=True,
        owner_session_go=False,
        session_go_payload=auth,
        authorization_present=True,
        confirm_token_present=True,
    )
    assert result.ok is False
    assert "OWNER_SESSION_GO_REQUIRED" in result.blockers


def test_12_session_go_without_authorization_fails_closed() -> None:
    auth = _active_go()
    result = evaluate_session_go_gate_v1(
        expected_repository_sha=SHA,
        expected_config_digest=_cfg(),
        now_unix=NOW,
        owner_go=True,
        owner_session_go=True,
        session_go_payload=auth,
        authorization_present=False,
        confirm_token_present=True,
    )
    assert result.ok is False
    assert result.session_go_authority_satisfied is True
    assert "SESSION_GO_VALID_BUT_AUTHORIZATION_REQUIRED" in result.blockers
    assert result.authorization_consumed is False
    assert result.session_lock_acquired is False
    assert result.session_started is False
    assert result.network_request_count == 0


def test_13_full_unlock_permits_without_side_effects() -> None:
    auth = _active_go()
    result = evaluate_session_go_gate_v1(
        expected_repository_sha=SHA,
        expected_config_digest=_cfg(),
        now_unix=NOW,
        owner_go=True,
        owner_session_go=True,
        session_go_payload=auth,
        authorization_present=True,
        confirm_token_present=True,
    )
    assert result.ok is True
    assert result.productive_session_execution_permitted is True
    assert result.authorization_may_proceed is True
    assert result.lock_may_proceed is True
    assert result.network_may_proceed is True
    assert result.session_start_may_proceed is True
    assert result.authorization_consumed is False
    assert result.session_lock_acquired is False
    assert result.session_started is False
    assert result.network_request_count == 0
    assert result.side_effects_occurred is False


def test_14_entrypoint_consumer_missing_session_go() -> None:
    gate = evaluate_productive_session_start_gates_v1(
        expected_repository_sha=SHA,
        expected_config_digest=_cfg(),
        now_unix=NOW,
        owner_go=True,
        owner_session_go=True,
        use_real_network=True,
        environ={},
    )
    assert gate["ok"] is False
    assert "SESSION_GO_MISSING" in gate["blockers"]
    assert gate["session_started"] is False
    assert gate["authorization_consumed"] is False
    assert gate["network_request_count"] == 0


def test_15_entrypoint_consumer_owner_go_alone_insufficient(tmp_path: Path) -> None:
    auth = _active_go()
    path = tmp_path / "session_go.json"
    write_json_atomic_v1(path, auth.to_dict())
    gate = reject_productive_session_start_v1(
        use_real_network=True,
        environ={},
        expected_repository_sha=SHA,
        expected_config_digest=_cfg(),
        now_unix=NOW,
        owner_go=True,
        owner_session_go=False,
        session_go_path=path,
        authorization_present=True,
        confirm_token_present=True,
    )
    assert gate["ok"] is False
    assert "OWNER_SESSION_GO_REQUIRED" in gate["blockers"]
    assert gate["session_started"] is False


def test_16_entrypoint_cli_fail_closed_without_session_go() -> None:
    proc = subprocess.run(
        [sys.executable, str(ENTRYPOINT_CLI), "productive-session", "--real-network"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 2
    payload = json.loads(proc.stdout)
    assert payload["ok"] is False
    assert payload["network_session_started"] is False
    assert payload["session_started"] is False
    assert payload["authorization_consumed"] is False
    assert payload["network_request_count"] == 0


def test_17_entrypoint_cli_unlock_evaluation_no_side_effects(tmp_path: Path) -> None:
    import time

    now = float(time.time())
    auth = _active_go(
        expected_repository_sha=_live_sha(),
        issued_at=now - 10,
        not_before=now - 5,
        expires_at=now + 3600,
    )
    path = tmp_path / "session_go.json"
    write_json_atomic_v1(path, auth.to_dict())
    proc = subprocess.run(
        [
            sys.executable,
            str(ENTRYPOINT_CLI),
            "productive-session",
            "--session-go-file",
            str(path),
            "--owner-go",
            "--owner-session-go",
            "--authorization-present",
            "--confirm-token-present",
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["productive_session_execution_permitted"] is True
    assert payload["session_started"] is False
    assert payload["authorization_consumed"] is False
    assert payload["network_request_count"] == 0
    assert payload["network_session_started"] is False


def _live_sha() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=str(REPO_ROOT), text=True
    ).strip()


def test_18_parity() -> None:
    parity = prove_phase92_session_go_parity_v1()
    assert parity["ok"] is True
    assert parity["GOLDEN_VECTOR_PARITY_PASS"] is True
    assert parity["CALL_ORDER_PARITY_PROVEN"] is True
    assert parity["INPUT_OUTPUT_PARITY_PROVEN"] is True
    assert parity["RISK_PARITY_PROVEN"] is True
    assert parity["SAFETY_PARITY_PROVEN"] is True
    assert parity["EXIT_PRECEDENCE_PARITY_PROVEN"] is True
    assert parity["CORE_LOGIC_CHANGED"] is False


def test_19_permanent_enable_flag_remains_false() -> None:
    cfg = json.loads(
        (
            REPO_ROOT
            / "config/ops/phase_9_2_productive_public_md_restart_recovery_network_entrypoint_v1.json"
        ).read_text(encoding="utf-8")
    )
    assert cfg["productive_network_session_execution_authorized"] is False
    assert cfg["session_go_authority_capability_id"] == CAPABILITY_ID
    assert PRODUCTIVE_NETWORK_SESSION_EXECUTION_ALLOWED is False


def test_20_public_md_only_required() -> None:
    with pytest.raises(SessionGoContractError, match="PUBLIC_MD_ONLY"):
        parse_session_go_authority_v1(
            {
                **_active_go().to_dict(),
                "public_md_only": False,
                "session_go_digest": "",
            }
        )
