"""Tests for Step-4 productive real-network session activation binding."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.confirm_token_v1 import (
    compute_confirm_token_binding_sha256,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.constants_v1 import (
    ACTIVATION_CAPABILITY_ID,
    FAULT_SESSION_ALLOWED,
    NETWORK_SESSION_ALLOWED,
    PRODUCTIVE_NETWORK_SESSION_EXECUTION_AUTHORIZED,
    PRODUCTIVE_STEP_4_SESSION_PATH_RUNTIME_REACHABLE,
    RATE_LIMIT_RECONNECT_LADDER_STEP_CLOSED,
    SESSION_SCOPE,
    TARGET_SESSION_ID,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.digest_v1 import (
    write_json_atomic_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.parity_v1 import (
    prove_phase92_rate_limit_reconnect_wallclock_binding_parity_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.productive_executor_v1 import (
    execute_productive_rate_limit_reconnect_session_activation_v1,
    execute_productive_rate_limit_reconnect_session_wiring_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.session_go_v1 import (
    build_session_go_authority_v1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.config_v1 import (
    load_activation_config_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CLI = (
    REPO_ROOT
    / "scripts/ops/run_phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.py"
)
NOW = 1_700_000_000.0
TOKEN = "GO_PSO_SESSION_PREREG_V1_ACTIVATION_BINDING_TEST_TOKEN_9F2A7C"
AUTH_ID = "auth_activation_binding_test_v1"
AUTH_DIGEST = "a" * 64


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


def _issue_sgo(path: Path, *, sha: str, cfg: str, network: bool = True) -> None:
    auth = build_session_go_authority_v1(
        session_go_id="sgo_test_rl_activation_binding_v1",
        expected_repository_sha=sha,
        expected_config_digest=cfg,
        issued_at=NOW,
        not_before=NOW,
        expires_at=NOW + 3600,
        network_session_execution_authorized_by_this_go=network,
        fixture_non_authoritative=False,
    )
    write_json_atomic_v1(path, auth.to_dict())


def _binding(sha: str) -> str:
    return compute_confirm_token_binding_sha256(
        session_id=TARGET_SESSION_ID,
        scope_digest=SESSION_SCOPE,
        expires_at=NOW + 3600,
        repository_sha=sha,
        confirm_token=TOKEN,
    )


def _base_kwargs(tmp_path: Path, *, sha: str, cfg: str) -> dict[str, Any]:
    sgo = tmp_path / "sgo.json"
    _issue_sgo(sgo, sha=sha, cfg=cfg)
    return {
        "expected_repository_sha": sha,
        "expected_config_digest": cfg,
        "now_unix": NOW,
        "owner_go": True,
        "owner_session_go": True,
        "session_go_path": sgo,
        "authorization_present": True,
        "request_real_network": True,
        "network_session_allowed": True,
        "authorization_id": AUTH_ID,
        "authorization_digest": AUTH_DIGEST,
        "authorization_repository_sha": sha,
        "authorization_config_digest": cfg,
        "confirm_token_binding_sha256": _binding(sha),
        "confirm_token_in_memory": TOKEN,
        "confirm_token_expires_at": NOW + 3600,
        "persistence_root": tmp_path / "persist",
        "execute": True,
        "session_request": {"session_id": TARGET_SESSION_ID, "instrument": "ETH-USD"},
    }


def test_activation_constants_remain_fail_closed() -> None:
    assert NETWORK_SESSION_ALLOWED is False
    assert FAULT_SESSION_ALLOWED is False
    assert PRODUCTIVE_NETWORK_SESSION_EXECUTION_AUTHORIZED is False
    assert RATE_LIMIT_RECONNECT_LADDER_STEP_CLOSED is False
    assert PRODUCTIVE_STEP_4_SESSION_PATH_RUNTIME_REACHABLE is True
    assert ACTIVATION_CAPABILITY_ID.endswith("ACTIVATION_BINDING_V1")


def test_a_no_request_real_network_no_runner_no_consume(tmp_path: Path) -> None:
    sha, cfg = _sha(), _cfg()
    kwargs = _base_kwargs(tmp_path, sha=sha, cfg=cfg)
    kwargs["request_real_network"] = False
    calls: list[Any] = []

    def runner(**_kwargs: Any) -> dict[str, Any]:
        calls.append(1)
        return {"ok": True}

    result = execute_productive_rate_limit_reconnect_session_activation_v1(
        **kwargs, wallclock_runner=runner
    )
    assert result.wallclock_runner_invoked is False
    assert result.authorization_consumed is False
    assert result.confirm_token_consumed is False
    assert result.network_request_count == 0
    assert calls == []
    assert "REQUEST_REAL_NETWORK_REQUIRED" in result.blockers


def test_b_network_session_allowed_false_fail_closed(tmp_path: Path) -> None:
    sha, cfg = _sha(), _cfg()
    kwargs = _base_kwargs(tmp_path, sha=sha, cfg=cfg)
    kwargs["network_session_allowed"] = False
    calls: list[Any] = []

    def runner(**_kwargs: Any) -> dict[str, Any]:
        calls.append(1)
        return {"ok": True}

    result = execute_productive_rate_limit_reconnect_session_activation_v1(
        **kwargs, wallclock_runner=runner
    )
    assert result.ok is False
    assert "NETWORK_SESSION_ALLOWED_REQUIRED" in result.blockers
    assert result.wallclock_runner_invoked is False
    assert calls == []


def test_c_missing_owner_go_fail_closed(tmp_path: Path) -> None:
    sha, cfg = _sha(), _cfg()
    kwargs = _base_kwargs(tmp_path, sha=sha, cfg=cfg)
    kwargs["owner_go"] = False
    calls: list[Any] = []

    def runner(**_kwargs: Any) -> dict[str, Any]:
        calls.append(1)
        return {"ok": True}

    result = execute_productive_rate_limit_reconnect_session_activation_v1(
        **kwargs, wallclock_runner=runner
    )
    assert result.ok is False
    assert "OWNER_GO_REQUIRED" in result.blockers
    assert result.wallclock_runner_invoked is False
    assert calls == []


def test_d_invalid_authorization_no_consume_no_runner(tmp_path: Path) -> None:
    sha, cfg = _sha(), _cfg()
    kwargs = _base_kwargs(tmp_path, sha=sha, cfg=cfg)
    kwargs["authorization_id"] = ""
    calls: list[Any] = []

    def runner(**_kwargs: Any) -> dict[str, Any]:
        calls.append(1)
        return {"ok": True}

    result = execute_productive_rate_limit_reconnect_session_activation_v1(
        **kwargs, wallclock_runner=runner
    )
    assert result.ok is False
    assert result.authorization_consumed is False
    assert result.confirm_token_consumed is False
    assert result.wallclock_runner_invoked is False
    assert calls == []


def test_e_sha_config_scope_mismatch_fail_closed(tmp_path: Path) -> None:
    sha, cfg = _sha(), _cfg()
    kwargs = _base_kwargs(tmp_path, sha=sha, cfg=cfg)
    kwargs["authorization_repository_sha"] = "0" * 40
    calls: list[Any] = []

    def runner(**_kwargs: Any) -> dict[str, Any]:
        calls.append(1)
        return {"ok": True}

    bad_sha = execute_productive_rate_limit_reconnect_session_activation_v1(
        **kwargs, wallclock_runner=runner
    )
    assert bad_sha.ok is False
    assert "AUTHORIZATION_SHA_MISMATCH" in bad_sha.blockers
    assert bad_sha.wallclock_runner_invoked is False

    kwargs = _base_kwargs(tmp_path / "cfg", sha=sha, cfg=cfg)
    kwargs["authorization_config_digest"] = "deadbeef"
    bad_cfg = execute_productive_rate_limit_reconnect_session_activation_v1(
        **kwargs, wallclock_runner=runner
    )
    assert bad_cfg.ok is False
    assert "AUTHORIZATION_CONFIG_MISMATCH" in bad_cfg.blockers

    kwargs = _base_kwargs(tmp_path / "scope", sha=sha, cfg=cfg)
    kwargs["authorization_scope"] = "WRONG_SCOPE"
    bad_scope = execute_productive_rate_limit_reconnect_session_activation_v1(
        **kwargs, wallclock_runner=runner
    )
    assert bad_scope.ok is False
    assert "AUTHORIZATION_SCOPE_MISMATCH" in bad_scope.blockers
    assert calls == []


def test_f_invalid_confirm_token_no_partial_consume(tmp_path: Path) -> None:
    sha, cfg = _sha(), _cfg()
    kwargs = _base_kwargs(tmp_path, sha=sha, cfg=cfg)
    kwargs["confirm_token_in_memory"] = "GO_PSO_SESSION_PREREG_V1_WRONG_TOKEN_XXXXXXXXXXXX"
    calls: list[Any] = []

    def runner(**_kwargs: Any) -> dict[str, Any]:
        calls.append(1)
        return {"ok": True}

    result = execute_productive_rate_limit_reconnect_session_activation_v1(
        **kwargs, wallclock_runner=runner
    )
    assert result.ok is False
    assert result.authorization_consumed is False
    assert result.confirm_token_consumed is False
    assert result.wallclock_runner_invoked is False
    assert calls == []


def test_g_private_credential_live_testnet_scope_fail_closed(tmp_path: Path) -> None:
    sha, cfg = _sha(), _cfg()
    calls: list[Any] = []

    def runner(**_kwargs: Any) -> dict[str, Any]:
        calls.append(1)
        return {"ok": True}

    for flag in (
        "private_endpoint_access_allowed",
        "exchange_credential_use_allowed",
        "live_trading_allowed",
        "testnet_allowed",
        "real_capital_movement_allowed",
    ):
        kwargs = _base_kwargs(tmp_path / flag, sha=sha, cfg=cfg)
        kwargs[flag] = True
        result = execute_productive_rate_limit_reconnect_session_activation_v1(
            **kwargs, wallclock_runner=runner
        )
        assert result.ok is False
        assert result.wallclock_runner_invoked is False
    assert calls == []


def test_h_full_gate_pass_injected_runner_consumes_once(tmp_path: Path) -> None:
    sha, cfg = _sha(), _cfg()
    kwargs = _base_kwargs(tmp_path, sha=sha, cfg=cfg)
    seen: list[dict[str, Any]] = []

    def runner(*, session_request: dict[str, Any]) -> dict[str, Any]:
        seen.append(dict(session_request))
        return {"ok": True, "network_opened": False}

    result = execute_productive_rate_limit_reconnect_session_activation_v1(
        **kwargs, wallclock_runner=runner
    )
    assert result.ok is True
    assert result.authorization_consumed is True
    assert result.confirm_token_consumed is True
    assert result.wallclock_runner_invoked is True
    assert result.wallclock_runner_invocation_count == 1
    assert len(seen) == 1
    assert seen[0] == {"session_id": TARGET_SESSION_ID, "instrument": "ETH-USD"}
    assert result.network_session_started is False
    assert result.network_request_count == 0
    assert result.ladder_step_remains_open is True


def test_i_runner_throws_before_start_no_false_pass(tmp_path: Path) -> None:
    sha, cfg = _sha(), _cfg()
    kwargs = _base_kwargs(tmp_path, sha=sha, cfg=cfg)
    calls = {"n": 0}

    def runner(**_kwargs: Any) -> dict[str, Any]:
        calls["n"] += 1
        raise RuntimeError("INJECTED_PRE_START_FAILURE")

    result = execute_productive_rate_limit_reconnect_session_activation_v1(
        **kwargs, wallclock_runner=runner
    )
    assert result.ok is False
    assert any("RUNNER_EXCEPTION" in b for b in result.blockers)
    assert result.claims.get("PASS_EVIDENCE") is False
    assert calls["n"] == 1
    assert result.wallclock_runner_invocation_count == 1


def test_j_runner_negative_evidence_keeps_ladder_open(tmp_path: Path) -> None:
    sha, cfg = _sha(), _cfg()
    kwargs = _base_kwargs(tmp_path, sha=sha, cfg=cfg)

    def runner(**_kwargs: Any) -> dict[str, Any]:
        return {"ok": False, "terminal_verdict": "FAIL", "session_pass": False}

    result = execute_productive_rate_limit_reconnect_session_activation_v1(
        **kwargs, wallclock_runner=runner
    )
    assert result.ok is False
    assert "RUNNER_NEGATIVE_SESSION_EVIDENCE" in result.blockers
    assert result.ladder_step_remains_open is True
    assert result.claims.get("RATE_LIMIT_RECONNECT_LADDER_STEP_CLOSED") is False
    assert result.claims.get("PASS_EVIDENCE") is False


def test_k_token_secrecy_no_plaintext_in_result_or_argv(tmp_path: Path) -> None:
    sha, cfg = _sha(), _cfg()
    kwargs = _base_kwargs(tmp_path, sha=sha, cfg=cfg)
    argv = ["execute-productive-session", "--execute", "--confirm-token", TOKEN]

    def runner(**_kwargs: Any) -> dict[str, Any]:
        return {"ok": True}

    refused = execute_productive_rate_limit_reconnect_session_activation_v1(
        **kwargs, wallclock_runner=runner, argv=argv
    )
    assert refused.ok is False
    assert "CONFIRM_TOKEN_IN_ARGV_FORBIDDEN" in refused.blockers
    blob = json.dumps(refused.to_dict())
    assert TOKEN not in blob

    ok = execute_productive_rate_limit_reconnect_session_activation_v1(
        **kwargs, wallclock_runner=runner, argv=["--execute"]
    )
    assert ok.ok is True
    blob_ok = json.dumps(ok.to_dict())
    assert TOKEN not in blob_ok
    assert "confirm_token" not in blob_ok or "[REDACTED]" in blob_ok or TOKEN not in blob_ok


def test_l_call_graph_parity_owners_unchanged() -> None:
    parity = prove_phase92_rate_limit_reconnect_wallclock_binding_parity_v1()
    assert parity.get("ok") is True
    # Existing owners remain referenced; activation adds no parallel fault/retry policy.
    from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.constants_v1 import (
        EEA_TRANSPORT_OWNER,
        PACING_POLICY_OWNER,
        SESSION_RUNTIME_OWNER,
        STALENESS_OWNER,
    )

    assert "public_md_rate_limit_policy_v1" in PACING_POLICY_OWNER
    assert "eea_public_md_transport_v1" in EEA_TRANSPORT_OWNER
    assert "session_runtime_v1" in SESSION_RUNTIME_OWNER
    assert "heartbeat_staleness_v1" in STALENESS_OWNER


def test_wiring_still_binds_without_invoke_and_marks_path_reachable(tmp_path: Path) -> None:
    sha, cfg = _sha(), _cfg()
    sgo = tmp_path / "sgo.json"
    _issue_sgo(sgo, sha=sha, cfg=cfg)
    result = execute_productive_rate_limit_reconnect_session_wiring_v1(
        expected_repository_sha=sha,
        expected_config_digest=cfg,
        now_unix=NOW,
        owner_go=True,
        owner_session_go=True,
        session_go_path=sgo,
        authorization_present=True,
        confirm_token_present_flag=True,
        execute=True,
        allow_real_network=False,
    )
    assert result.ok is True
    assert result.wallclock_runner_invoked is False
    assert result.productive_step_4_session_path_runtime_reachable is True
    assert result.productive_call_graph_complete is True
    assert result.ready_for_productive_session_execution is True
    assert "run_productive_wallclock_session_v1" in result.call_graph


def test_cli_request_real_network_does_not_start_session(tmp_path: Path) -> None:
    import time

    sha, cfg = _sha(), _cfg()
    sgo = tmp_path / "sgo.json"
    now = float(time.time())
    auth = build_session_go_authority_v1(
        session_go_id="sgo_test_rl_activation_cli_v1",
        expected_repository_sha=sha,
        expected_config_digest=cfg,
        issued_at=now,
        not_before=now,
        expires_at=now + 3600,
        network_session_execution_authorized_by_this_go=True,
        fixture_non_authoritative=False,
    )
    write_json_atomic_v1(sgo, auth.to_dict())
    refused = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "execute-productive-session",
            "--execute",
            "--owner-go",
            "--owner-session-go",
            "--authorization-present",
            "--confirm-token-present",
            "--session-go-file",
            str(sgo),
            "--request-real-network",
            "--network-session-allowed",
            "--expected-repository-sha",
            sha,
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert refused.returncode == 2
    payload = json.loads(refused.stdout)
    assert payload.get("network_session_started") is False
    assert payload.get("wallclock_runner_invoked") is False
    assert TOKEN not in refused.stdout
