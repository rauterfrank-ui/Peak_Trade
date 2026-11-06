"""Offline tests for Step-5 governed prolonged natural-market session execution.

No real DNS/socket/HTTP. No auth/token issuance or consumption. No secrets.
"""

from __future__ import annotations

import json
import socket
import subprocess
from pathlib import Path
from typing import Any, Mapping

import pytest

from src.ops.phase_9_2_step_5_governed_productive_real_network_prolonged_natural_market_session_execution_v1.authorization_gate_v1 import (
    validate_execution_authorization_artifact_v1,
)
from src.ops.phase_9_2_step_5_governed_productive_real_network_prolonged_natural_market_session_execution_v1.confirm_token_path_v1 import (
    reject_confirm_token_argv_v1,
    reject_confirm_token_env_fallback_v1,
)
from src.ops.phase_9_2_step_5_governed_productive_real_network_prolonged_natural_market_session_execution_v1.constants_v1 import (
    AUTHORIZATION_CONSUMPTION_ALLOWED,
    BINDING_CLI_PATH,
    CAPABILITY_ID,
    CONFIRM_TOKEN_CONSUMPTION_ALLOWED,
    MINIMUM_SUCCESSFUL_WALLCLOCK_SECONDS,
    NETWORK_SESSION_ALLOWED,
    PLANNED_SESSION_DURATION_SECONDS,
    PRODUCTIVE_ENTRYPOINT_PATH,
    REAL_NETWORK_REQUESTS_ALLOWED,
    SESSION_EXECUTION_SIDE_EFFECTS_AUTHORIZED,
    TERMINAL_CLASSES,
)
from src.ops.phase_9_2_step_5_governed_productive_real_network_prolonged_natural_market_session_execution_v1.contract_bindings_v1 import (
    load_execution_contract_bundle_v1,
)
from src.ops.phase_9_2_step_5_governed_productive_real_network_prolonged_natural_market_session_execution_v1.digest_v1 import (
    sha256_canonical_v1,
)
from src.ops.phase_9_2_step_5_governed_productive_real_network_prolonged_natural_market_session_execution_v1.evidence_v1 import (
    claims_match_telemetry_v1,
    materialize_terminal_evidence_v1,
    verify_session_manifest_v1,
)
from src.ops.phase_9_2_step_5_governed_productive_real_network_prolonged_natural_market_session_execution_v1.failure_injection_v1 import (
    run_step5_execution_failure_injection_v1,
)
from src.ops.phase_9_2_step_5_governed_productive_real_network_prolonged_natural_market_session_execution_v1.governed_session_execution_v1 import (
    assemble_execution_request_v1,
    execute_governed_step5_session_v1,
    prove_step5_execution_implementation_v1,
    request_real_network_offline_fail_closed_v1,
)
from src.ops.phase_9_2_step_5_governed_productive_real_network_prolonged_natural_market_session_execution_v1.hidden_pty_handoff_v1 import (
    fingerprint_only_v1,
    validate_confirm_token_binding_v1,
)
from src.ops.phase_9_2_step_5_governed_productive_real_network_prolonged_natural_market_session_execution_v1.network_boundary_v1 import (
    prove_public_md_get_only_boundary_v1,
)
from src.ops.phase_9_2_step_5_governed_productive_real_network_prolonged_natural_market_session_execution_v1.prolonged_executor_v1 import (
    run_bounded_prolonged_public_md_executor_v1,
)
from src.ops.phase_9_2_step_5_governed_productive_real_network_prolonged_natural_market_session_execution_v1.terminal_classification_v1 import (
    classify_terminal_v1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.config_v1 import (
    load_activation_config_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
BINDING_CLI = REPO_ROOT / BINDING_CLI_PATH
EXEC_CLI = REPO_ROOT / PRODUCTIVE_ENTRYPOINT_PATH
TOKEN = "PTCONFIRMv1_STEP5EXECTEST" + ("A" * 16)
NOW = 1_700_000_000.0


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


def _block_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def _blocked(*_a: Any, **_k: Any) -> None:
        raise AssertionError("REAL_NETWORK_FORBIDDEN_IN_TESTS")

    monkeypatch.setattr(socket, "create_connection", _blocked)
    monkeypatch.setattr(socket.socket, "connect", _blocked)
    monkeypatch.setattr(socket, "getaddrinfo", _blocked)


def _ok_body(ts: str = "1700000000000") -> bytes:
    return json.dumps({"code": "0", "data": [{"ts": ts, "last": "1"}]}).encode("utf-8")


class _FakeClock:
    def __init__(self, start: float = 0.0) -> None:
        self.t = float(start)

    def __call__(self) -> float:
        return self.t

    def advance(self, seconds: float) -> None:
        self.t += float(seconds)


def test_constants_fail_closed() -> None:
    assert NETWORK_SESSION_ALLOWED is False
    assert REAL_NETWORK_REQUESTS_ALLOWED is False
    assert AUTHORIZATION_CONSUMPTION_ALLOWED is False
    assert CONFIRM_TOKEN_CONSUMPTION_ALLOWED is False
    assert SESSION_EXECUTION_SIDE_EFFECTS_AUTHORIZED is False
    assert PLANNED_SESSION_DURATION_SECONDS == 7200
    assert MINIMUM_SUCCESSFUL_WALLCLOCK_SECONDS == 7200
    assert CAPABILITY_ID.endswith("SESSION_EXECUTION_CAPABILITY_V1")
    assert set(TERMINAL_CLASSES) >= {
        "PASS",
        "HARD_STOP",
        "INTERRUPTED",
        "STALE_DATA_STOP",
        "RATE_LIMIT_EXHAUSTED",
        "RECONNECT_EXHAUSTED",
        "NETWORK_FAILURE",
        "CONTRACT_MISMATCH",
        "AUTHORIZATION_FAILURE",
        "CONFIRM_TOKEN_FAILURE",
        "EVIDENCE_FAILURE",
        "DISK_BOUND_FAILURE",
    }


def test_binding_cli_unchanged_and_real_network_forbidden(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _block_network(monkeypatch)
    assert BINDING_CLI.is_file()
    assert EXEC_CLI.is_file()
    assert BINDING_CLI.resolve() != EXEC_CLI.resolve()
    # Binding CLI must remain binding-only: --request-real-network refused outside gate.
    gate = subprocess.run(
        [str(BINDING_CLI), "preflight", "--request-real-network"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert gate.returncode != 0
    payload = json.loads(gate.stdout)
    assert payload.get("network_session_started") is False
    assert any("REAL_NETWORK" in b for b in payload.get("blockers") or [])
    # Binding CLI must not expose execute-governed-session.
    help_proc = subprocess.run(
        [str(BINDING_CLI), "--help"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert "execute-governed-session" not in (help_proc.stdout + help_proc.stderr)


def test_execution_cli_surface_and_offline_commands(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _block_network(monkeypatch)
    for command, expect_rc in (
        ("preflight", 0),
        ("assemble-execution-request", 0),
        ("request-real-network", 2),
        ("execute-governed-session", 2),
    ):
        proc = subprocess.run(
            [str(EXEC_CLI), command],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc.returncode == expect_rc, (command, proc.stdout, proc.stderr)
        payload = json.loads(proc.stdout)
        assert (
            payload.get("network_session_started") in (False, None)
            or payload.get("claims", {}).get("NETWORK_SESSION_STARTED") is False
        )


def test_implementation_proof_and_contract_digests(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _block_network(monkeypatch)
    bundle = load_execution_contract_bundle_v1(repo_root=REPO_ROOT)
    assert bundle["planned_session_duration_seconds"] == 7200
    assert bundle["minimum_successful_wallclock_seconds"] == 7200
    assert float(bundle["pacing"]["minimum_interval_seconds"]) > 0
    proof = prove_step5_execution_implementation_v1(
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
        repo_root=REPO_ROOT,
    )
    assert proof.ok
    assert proof.claims["PUBLIC_MD_GET_ONLY_BOUNDARY_PROVEN"] is True
    assert proof.claims["NETWORK_SESSION_STARTED"] is False
    assert proof.claims["AUTHORIZATION_CONSUMED"] is False


def test_network_execution_without_authorization_hard_stops(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _block_network(monkeypatch)
    bundle = load_execution_contract_bundle_v1(repo_root=REPO_ROOT)
    result = execute_governed_step5_session_v1(
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
        expected_session_contract_digest=bundle["session_contract_digest"],
        expected_binding_config_digest=bundle["binding_config_digest"],
        authorization_id="",
        authorization_digest="",
        confirm_token_binding_sha256=fingerprint_only_v1(TOKEN),
        persistence_root=tmp_path / "p",
        evidence_root=tmp_path / "e",
        now_unix=NOW,
        confirm_token_plaintext=TOKEN,
        repo_root=REPO_ROOT,
    )
    assert result.ok is False
    assert result.network_session_started is False
    assert any("AUTHORIZATION" in b for b in result.blockers)


def test_wrong_sha_contract_config_scope_expiry_reuse(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _block_network(monkeypatch)
    fi = run_step5_execution_failure_injection_v1(
        repository_sha=_sha(),
        config_digest=_cfg(),
        persistence_root=tmp_path / "fi",
        repo_root=REPO_ROOT,
        now_unix=NOW,
    )
    assert fi["ok"] is True
    for name in (
        "wrong_sha",
        "wrong_contract_digest",
        "wrong_config_digest",
        "wrong_scope",
        "expired_authorization",
        "reused_authorization",
        "missing_confirm_token",
        "wrong_confirm_token_digest",
        "confirm_token_argv_rejected",
        "confirm_token_env_rejected",
        "request_real_network_fail_closed",
    ):
        assert fi["cases"][name]["ok"] is False
        assert fi["cases"][name]["network_session_started"] is False


def test_confirm_token_plaintext_never_in_evidence_or_logs(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _block_network(monkeypatch)
    bundle = load_execution_contract_bundle_v1(repo_root=REPO_ROOT)
    result = execute_governed_step5_session_v1(
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
        expected_session_contract_digest=bundle["session_contract_digest"],
        expected_binding_config_digest=bundle["binding_config_digest"],
        authorization_id="auth_x",
        authorization_digest="digest_x",
        confirm_token_binding_sha256=fingerprint_only_v1(TOKEN),
        persistence_root=tmp_path / "p",
        evidence_root=tmp_path / "e",
        now_unix=NOW,
        confirm_token_plaintext=TOKEN,
        authorization_expires_at=NOW + 100,
        repo_root=REPO_ROOT,
    )
    blob = json.dumps(result.to_dict(), sort_keys=True)
    assert TOKEN not in blob
    assert result.claims.get("CONFIRM_TOKEN_PLAINTEXT_EXPOSED") is False
    assert reject_confirm_token_argv_v1(["--confirm-token", TOKEN])
    assert reject_confirm_token_env_fallback_v1({"PEAK_TRADE_PSO_CONFIRM_TOKEN": TOKEN})


def test_get_only_and_private_endpoint_and_auth_header_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _block_network(monkeypatch)
    boundary = prove_public_md_get_only_boundary_v1()
    assert boundary["ok"] is True
    assert boundary["PUBLIC_MD_GET_ONLY"] is True
    assert boundary["PRIVATE_ENDPOINT_REACHABLE"] is False
    assert boundary["AUTH_HEADER_REACHABLE"] is False
    assert boundary["ORDER_SUBMIT_PATH_REACHABLE"] is False
    assert boundary["EXCHANGE_CREDENTIAL_PATH_REACHABLE"] is False
    assert boundary["REAL_EXECUTION_ADAPTER_CONSTRUCTED"] is False


def test_monotone_duration_pacing_retry_backoff_429_reconnect_heartbeat_stale_interrupt(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _block_network(monkeypatch)
    bundle = load_execution_contract_bundle_v1(repo_root=REPO_ROOT)
    pacing = dict(bundle["pacing"])
    clock = _FakeClock(0.0)
    sleeps: list[float] = []

    def sleep_fn(seconds: float) -> None:
        assert float(seconds) > 0
        sleeps.append(float(seconds))
        clock.advance(float(seconds))

    n = {"i": 0}

    def fetcher(
        url: str, method: str, headers: Mapping[str, str], timeout: float
    ) -> tuple[int, bytes, Mapping[str, str]]:
        assert method == "GET"
        assert "Authorization" not in headers
        assert "OK-ACCESS-KEY" not in headers
        n["i"] += 1
        if n["i"] == 1:
            return 429, b"{}", {"Retry-After": "2"}
        return 200, _ok_body(ts=str(1700000000000 + n["i"])), {"Content-Type": "application/json"}

    # Accelerate duration: planned 8s with min interval from contract, fake clock
    result = run_bounded_prolonged_public_md_executor_v1(
        pacing=pacing,
        planned_session_duration_seconds=8,
        minimum_successful_wallclock_seconds=8,
        evidence_root=tmp_path / "ev1",
        persistence_root=tmp_path / "pers1",
        fetcher=fetcher,
        allow_real_network=False,
        monotonic_clock=clock,
        sleep_fn=sleep_fn,
        force_max_cycles=20,
    )
    assert result.telemetry.request_count > 0
    assert result.telemetry.distinct_observation_count > 0
    assert result.telemetry.session_monotonic_wallclock_seconds >= 8
    assert all(s > 0 for s in sleeps)
    assert result.claims["ZERO_INTERVAL_BURST"] is False
    assert result.claims["PACING_BOUND"] is True
    assert result.claims["RETRY_BOUND"] is True
    assert result.claims["BACKOFF_BOUND"] is True
    assert result.claims["RECONNECT_BOUND"] is True
    assert result.claims["HEARTBEAT_BOUND"] is True

    # Staleness stop
    clock2 = _FakeClock(0.0)
    stale = run_bounded_prolonged_public_md_executor_v1(
        pacing=pacing,
        planned_session_duration_seconds=100,
        minimum_successful_wallclock_seconds=100,
        evidence_root=tmp_path / "ev_stale",
        persistence_root=tmp_path / "pers_stale",
        fetcher=lambda *_a, **_k: (200, _ok_body(), {}),
        monotonic_clock=clock2,
        sleep_fn=lambda s: clock2.advance(s),
        force_max_cycles=10,
        stale_receive_lag_seconds=float(pacing["staleness_budget_seconds"]) + 1.0,
    )
    assert stale.terminal_class == "STALE_DATA_STOP"

    # Interrupt
    clock3 = _FakeClock(0.0)
    flag = {"n": 0}

    def interrupt_after_first() -> bool:
        flag["n"] += 1
        return flag["n"] > 1

    interrupted_run = run_bounded_prolonged_public_md_executor_v1(
        pacing=pacing,
        planned_session_duration_seconds=100,
        minimum_successful_wallclock_seconds=100,
        evidence_root=tmp_path / "ev_int",
        persistence_root=tmp_path / "pers_int",
        fetcher=lambda *_a, **_k: (200, _ok_body(ts=str(flag["n"])), {}),
        monotonic_clock=clock3,
        sleep_fn=lambda s: clock3.advance(s),
        interrupt_check=interrupt_after_first,
        force_max_cycles=10,
    )
    assert interrupted_run.terminal_class == "INTERRUPTED"


def test_session_lock_and_duplicate_observation(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _block_network(monkeypatch)
    bundle = load_execution_contract_bundle_v1(repo_root=REPO_ROOT)
    pacing = dict(bundle["pacing"])
    clock = _FakeClock(0.0)

    def fetcher_dup(
        url: str, method: str, headers: Mapping[str, str], timeout: float
    ) -> tuple[int, bytes, Mapping[str, str]]:
        return 200, _ok_body(ts="same"), {}

    result = run_bounded_prolonged_public_md_executor_v1(
        pacing=pacing,
        planned_session_duration_seconds=6,
        minimum_successful_wallclock_seconds=6,
        evidence_root=tmp_path / "ev",
        persistence_root=tmp_path / "pers",
        fetcher=fetcher_dup,
        monotonic_clock=clock,
        sleep_fn=lambda s: clock.advance(s),
        force_max_cycles=5,
    )
    assert result.telemetry.duplicate_observation_count >= 1
    assert result.telemetry.distinct_observation_count == 1

    # second concurrent lock should fail
    from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.session_lock_v1 import (
        SessionLockError,
        SessionLockV1,
    )

    lock_path = tmp_path / "pers" / "locks"
    # after release, re-acquire works; hold one and try second
    held = SessionLockV1(
        lock_path=lock_path / "phase_9_2_step5_prolonged_natural_market_session_lock_v1.lock",
        session_id="s1",
        owner="t",
    )
    held.acquire()
    other = SessionLockV1(
        lock_path=lock_path / "phase_9_2_step5_prolonged_natural_market_session_lock_v1.lock",
        session_id="s2",
        owner="t2",
    )
    with pytest.raises(SessionLockError):
        other.acquire()
    held.release()


def test_minimum_duration_verifier_and_pass_criteria() -> None:
    tel = {
        "network_session_started": True,
        "session_monotonic_wallclock_seconds": 7200.0,
        "request_count": 10,
        "distinct_observation_count": 5,
        "order_side_effect_occurred": False,
        "credential_access_occurred": False,
        "private_endpoint_access_occurred": False,
        "auth_header_transmitted": False,
    }
    ok = classify_terminal_v1(
        proposed_terminal="PASS",
        telemetry=tel,
        evidence_verified=True,
        claims_match_telemetry=True,
    )
    assert ok["pass_eligible"] is True
    assert ok["terminal_class"] == "PASS"

    short = dict(tel)
    short["session_monotonic_wallclock_seconds"] = 100.0
    bad = classify_terminal_v1(
        proposed_terminal="PASS",
        telemetry=short,
        evidence_verified=True,
        claims_match_telemetry=True,
    )
    assert bad["pass_eligible"] is False
    assert bad["terminal_class"] == "HARD_STOP"


def test_disk_bounds_manifest_claims_idempotent_evidence(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _block_network(monkeypatch)
    summary = materialize_terminal_evidence_v1(
        repository_sha=_sha(),
        evidence_root=tmp_path / "docs_evidence",
        repo_root=REPO_ROOT,
    )
    assert summary["ok"] is True
    assert summary["network_session_started"] is False
    assert summary["authorization_consumed"] is False
    manifest = json.loads(
        (tmp_path / "docs_evidence" / "fixtures" / "manifest_v1.json").read_text(encoding="utf-8")
    )
    verified = verify_session_manifest_v1(manifest)
    assert verified["ok"] is True
    # idempotent rematerialize
    summary2 = materialize_terminal_evidence_v1(
        repository_sha=_sha(),
        evidence_root=tmp_path / "docs_evidence",
        repo_root=REPO_ROOT,
    )
    assert summary2["ok"] is True
    match = claims_match_telemetry_v1(
        claims={
            "REQUEST_COUNT": 0,
            "DISTINCT_OBSERVATION_COUNT": 0,
            "NETWORK_SESSION_STARTED": False,
            "ORDER_SIDE_EFFECT_OCCURRED": False,
            "CREDENTIAL_ACCESS_OCCURRED": False,
            "PRIVATE_ENDPOINT_ACCESS_OCCURRED": False,
            "AUTH_HEADER_TRANSMITTED": False,
        },
        telemetry={
            "request_count": 0,
            "distinct_observation_count": 0,
            "network_session_started": False,
        },
    )
    assert match["ok"] is True


def test_assemble_execution_request_binds_contract(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _block_network(monkeypatch)
    assembled = assemble_execution_request_v1(
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
        repo_root=REPO_ROOT,
    )
    assert assembled["ok"] is True
    req = assembled["session_request"]
    assert req["planned_session_duration_seconds"] == 7200
    assert req["session_contract_digest"] == assembled["session_contract_digest"]
    assert "pacing" in req


def test_auth_and_token_digest_helpers(monkeypatch: pytest.MonkeyPatch) -> None:
    _block_network(monkeypatch)
    bundle = load_execution_contract_bundle_v1(repo_root=REPO_ROOT)
    auth = validate_execution_authorization_artifact_v1(
        authorization_id="a1",
        authorization_digest="d1",
        expected_repository_sha=_sha(),
        expected_session_contract_digest=bundle["session_contract_digest"],
        expected_binding_config_digest=bundle["binding_config_digest"],
        authorization_expires_at=NOW + 10,
        now_unix=NOW,
        evidence_root="/tmp/e",
        authorization_evidence_root="/tmp/e",
    )
    assert auth["ok"] is True
    token = validate_confirm_token_binding_v1(
        confirm_token_plaintext=TOKEN,
        expected_binding_sha256=fingerprint_only_v1(TOKEN),
        expected_repository_sha=_sha(),
        expected_session_contract_digest=bundle["session_contract_digest"],
        expected_binding_config_digest=bundle["binding_config_digest"],
        expires_at=NOW + 10,
        now_unix=NOW,
    )
    assert token["ok"] is True
    bad = validate_confirm_token_binding_v1(
        confirm_token_plaintext=TOKEN,
        expected_binding_sha256="00" * 32,
        expected_repository_sha=_sha(),
        expected_session_contract_digest=bundle["session_contract_digest"],
        expected_binding_config_digest=bundle["binding_config_digest"],
        expires_at=NOW + 10,
        now_unix=NOW,
    )
    assert bad["ok"] is False


def test_request_real_network_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    _block_network(monkeypatch)
    result = request_real_network_offline_fail_closed_v1(
        expected_repository_sha=_sha(),
        expected_config_digest=_cfg(),
        repo_root=REPO_ROOT,
    )
    assert result.ok is False
    assert result.network_session_started is False
    assert any("REAL_NETWORK" in b for b in result.blockers)


def test_no_secrets_in_package_sources() -> None:
    root = (
        REPO_ROOT / "src/ops/phase_9_2_step_5_governed_productive_real_network_"
        "prolonged_natural_market_session_execution_v1"
    )
    forbidden = ("BEGIN PRIVATE KEY", "OK-ACCESS-KEY", "api_secret", "password=")
    for path in root.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        for needle in forbidden:
            assert needle not in text
