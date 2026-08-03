"""Unit and integration tests for CAPABILITY_O2 launcher / supervision."""

from __future__ import annotations

import json
import os
import shutil
import signal
import time
from pathlib import Path

import pytest

from src.ops.canonical_local_launcher_and_process_supervision_v1.constants_v1 import (
    CAPABILITY_ID,
    MODE_DASHBOARD_ONLY,
    SAFETY_INVARIANTS,
    SETSID_CLI_REQUIRED,
    SUPERVISION_BACKEND,
)
from src.ops.canonical_local_launcher_and_process_supervision_v1.errors_v1 import (
    CanonicalLauncherError,
    ConflictingWriterError,
    DuplicateSessionError,
    ModeUnauthorizedError,
    ProcessIdentityMismatchError,
)
from src.ops.canonical_local_launcher_and_process_supervision_v1.lifecycle_v1 import (
    CanonicalLocalLauncherV1,
    LauncherPathsV1,
    compute_config_digest_v1,
)
from src.ops.canonical_local_launcher_and_process_supervision_v1.models_v1 import (
    ProcessIdentityV1,
)
from src.ops.canonical_local_launcher_and_process_supervision_v1.process_group_v1 import (
    assert_no_setsid_cli_dependency,
)
from src.ops.canonical_local_launcher_and_process_supervision_v1.process_identity_v1 import (
    capture_process_identity,
    process_alive,
    verify_process_identity,
)
from src.ops.canonical_local_launcher_and_process_supervision_v1.single_writer_v1 import (
    LauncherSingleWriterV1,
)
from src.ops.canonical_runtime_environment_contract_v1.constants_v1 import (
    ENVIRONMENT_POLICY_ID,
)


@pytest.fixture()
def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


@pytest.fixture()
def launcher_env(tmp_path: Path, repo_root: Path) -> tuple[CanonicalLocalLauncherV1, Path]:
    state_root = tmp_path / "state"
    log_root = tmp_path / "logs"
    evidence_root = tmp_path / "evidence"
    cfg = tmp_path / "config.json"
    cfg.write_text(
        json.dumps({"mode": "dashboard-only", "o2": True}, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    paths = LauncherPathsV1(
        repository_root=repo_root,
        state_root=state_root,
        log_root=log_root,
        evidence_root=evidence_root,
    )
    return CanonicalLocalLauncherV1(paths), cfg


def _start(launcher: CanonicalLocalLauncherV1, cfg: Path, **kwargs):
    defaults = {
        "mode": MODE_DASHBOARD_ONLY,
        "config_path": cfg,
        "repository_sha": "deadbeef" * 5,
    }
    defaults.update(kwargs)
    return launcher.start(**defaults)


def test_macos_portability_without_setsid_cli() -> None:
    assert SETSID_CLI_REQUIRED is False
    assert_no_setsid_cli_dependency()
    # Presence of setsid binary must not be required.
    _ = shutil.which("setsid")


def test_single_writer_conflict(tmp_path: Path) -> None:
    root = tmp_path / "reg"
    w1 = LauncherSingleWriterV1(root, session_id="a")
    w1.acquire()
    w2 = LauncherSingleWriterV1(root, session_id="b")
    with pytest.raises(ConflictingWriterError):
        w2.acquire()
    w1.release()
    w2.acquire()
    w2.release()


def test_clean_start_lifecycle_and_status_health(launcher_env) -> None:
    launcher, cfg = launcher_env
    started = _start(launcher, cfg, session_id="sess-clean")
    assert started["ok"] is True
    session = started["session"]
    assert session["lifecycle_state"] == "RUNNING"
    assert session["capability_id"] == CAPABILITY_ID
    assert session["supervision_backend"] == SUPERVISION_BACKEND
    assert session["safety_invariants"] == SAFETY_INVARIANTS
    assert session["o1_environment_policy_id"] == ENVIRONMENT_POLICY_ID

    status = launcher.status("sess-clean")
    assert status["process_alive"] is True
    assert status["identity_ok"] is True
    assert status["lifecycle_state"] == "RUNNING"

    health = launcher.health("sess-clean")
    assert health["healthy"] is True
    assert health["fresh_heartbeat"] is True

    stop = launcher.stop("sess-clean", graceful_timeout_seconds=2.0)
    assert stop["ok"] is True
    assert stop["stopped"] is True
    assert stop["escalated"] is False

    status_dead = launcher.status("sess-clean")
    assert status_dead["process_alive"] is False
    assert status_dead["lifecycle_state"] == "STOPPED"
    health_dead = launcher.health("sess-clean")
    assert health_dead["healthy"] is False


def test_duplicate_start_rejection(launcher_env) -> None:
    launcher, cfg = launcher_env
    _start(launcher, cfg, session_id="sess-a")
    with pytest.raises(DuplicateSessionError):
        _start(launcher, cfg, session_id="sess-b")
    launcher.stop("sess-a")


def test_caller_independent_lifetime(launcher_env) -> None:
    launcher, cfg = launcher_env
    started = _start(launcher, cfg, session_id="sess-detach")
    pid = int(started["session"]["process_identity"]["pid"])
    # Simulate caller exit: launcher object discarded; process must remain.
    del launcher
    assert process_alive(pid) is True
    # Re-attach via new launcher instance on same state root.
    # Reconstruct from fixture paths stored on session.
    paths = LauncherPathsV1(
        repository_root=Path(__file__).resolve().parents[2],
        state_root=Path(started["session"]["state_root"]),
        log_root=Path(started["session"]["log_root"]).parent,
        evidence_root=Path(started["session"]["evidence_root"]),
    )
    launcher2 = CanonicalLocalLauncherV1(paths)
    status = launcher2.status("sess-detach")
    assert status["process_alive"] is True
    launcher2.stop("sess-detach")


def test_pid_reuse_identity_mismatch_rejection(launcher_env) -> None:
    launcher, cfg = launcher_env
    started = _start(launcher, cfg, session_id="sess-id")
    identity = ProcessIdentityV1.from_dict(started["session"]["process_identity"])
    verify_process_identity(identity)
    forged = ProcessIdentityV1(
        pid=identity.pid,
        pgid=identity.pgid,
        process_start_identity="FORGED_START_IDENTITY",
        cmdline_fingerprint=identity.cmdline_fingerprint,
    )
    with pytest.raises(ProcessIdentityMismatchError):
        verify_process_identity(forged)
    launcher.stop("sess-id")


def test_stale_registry_recovery(launcher_env) -> None:
    launcher, cfg = launcher_env
    started = _start(launcher, cfg, session_id="sess-stale")
    identity = ProcessIdentityV1.from_dict(started["session"]["process_identity"])
    # Kill outside launcher to create stale registry.
    os.kill(identity.pid, signal.SIGKILL)
    deadline = time.time() + 2.0
    while time.time() < deadline and process_alive(identity.pid):
        time.sleep(0.05)
    assert process_alive(identity.pid) is False
    recovered = launcher.recover("sess-stale")
    assert recovered["action"] == "CLEARED_STALE_PID"
    assert recovered["session"]["lifecycle_state"] == "STOPPED"
    # Fresh start after recovery must succeed.
    started2 = _start(launcher, cfg, session_id="sess-stale-2")
    assert started2["session"]["lifecycle_state"] == "RUNNING"
    launcher.stop("sess-stale-2")


def test_process_group_stop(launcher_env) -> None:
    launcher, cfg = launcher_env
    started = _start(launcher, cfg, session_id="sess-pg")
    pid = int(started["session"]["process_identity"]["pid"])
    pgid = int(started["session"]["process_identity"]["pgid"])
    assert pid == pgid or pgid > 0
    stop = launcher.stop("sess-pg")
    assert stop["stopped"] is True
    assert process_alive(pid) is False


def test_graceful_stop_escalation(launcher_env) -> None:
    launcher, cfg = launcher_env
    started = _start(
        launcher,
        cfg,
        session_id="sess-escalate",
        force_ignore_sigterm_for_test=True,
    )
    stop = launcher.stop(
        "sess-escalate",
        graceful_timeout_seconds=0.3,
        kill_timeout_seconds=1.0,
    )
    assert stop["stopped"] is True
    assert stop["escalated"] is True


def test_restart_preserves_identity_binding(launcher_env) -> None:
    launcher, cfg = launcher_env
    digest = compute_config_digest_v1(cfg)
    started = _start(launcher, cfg, session_id="sess-restart", config_digest=digest)
    sha = started["session"]["repository_sha"]
    restarted = launcher.restart("sess-restart")
    assert restarted["ok"] is True
    new_session = restarted["start"]["session"]
    assert new_session["session_id"] == "sess-restart"
    assert new_session["repository_sha"] == sha
    assert new_session["config_digest"] == digest
    assert new_session["lifecycle_state"] == "RUNNING"
    launcher.stop("sess-restart")


def test_repository_config_identity_binding_mismatch(launcher_env) -> None:
    launcher, cfg = launcher_env
    _start(launcher, cfg, session_id="sess-bind", repository_sha="a" * 40)
    launcher.stop("sess-bind")
    with pytest.raises(CanonicalLauncherError) as excinfo:
        launcher.start(
            mode=MODE_DASHBOARD_ONLY,
            session_id="sess-bind",
            config_path=cfg,
            repository_sha="b" * 40,
        )
    assert excinfo.value.code == "REPOSITORY_OR_CONFIG_IDENTITY_MISMATCH"


def test_o1_preflight_consumption(launcher_env) -> None:
    launcher, cfg = launcher_env
    result = launcher.preflight(
        mode=MODE_DASHBOARD_ONLY,
        session_id="preflight-1",
        config_path=cfg,
        repository_sha="c" * 40,
    )
    assert result["ok"] is True
    assert result["o1_preflight"]["ok"] is True
    assert result["o1_preflight"]["environment_policy_id"] == ENVIRONMENT_POLICY_ID
    assert result["setsid_cli_required"] is False


def test_unauthorized_mode_fail_closed(launcher_env) -> None:
    launcher, cfg = launcher_env
    with pytest.raises(ModeUnauthorizedError):
        launcher.start(mode="future-live", config_path=cfg, session_id="nope")


def test_no_network_auth_token_order_credential_side_effects(launcher_env) -> None:
    launcher, cfg = launcher_env
    started = _start(launcher, cfg, session_id="sess-safe")
    inv = started["session"]["safety_invariants"]
    assert inv["NETWORK_SESSION_STARTED"] is False
    assert inv["AUTHORIZATION_CONSUMED"] is False
    assert inv["CONFIRM_TOKEN_MINTED"] is False
    assert inv["ORDERS_SUBMITTED"] is False
    assert inv["CREDENTIALS_USED"] is False
    assert inv["LEGACY_PATHS_DEAUTHORIZED"] is False
    marker = (
        Path(started["session"]["state_root"])
        / "canonical_local_launcher_v1"
        / "sessions"
        / "sess-safe"
        / "scaffold_worker_v1.marker"
    )
    # Wait for marker
    deadline = time.time() + 3.0
    while time.time() < deadline and not marker.is_file():
        time.sleep(0.05)
    assert marker.is_file()
    payload = json.loads(marker.read_text(encoding="utf-8"))
    assert payload["network_session_started"] is False
    assert payload["authorization_consumed"] is False
    assert payload["confirm_token_minted"] is False
    assert payload["orders_submitted"] is False
    assert payload["credentials_used"] is False
    launcher.stop("sess-safe")


def test_status_health_for_dead_process_after_external_kill(launcher_env) -> None:
    launcher, cfg = launcher_env
    started = _start(launcher, cfg, session_id="sess-dead")
    pid = int(started["session"]["process_identity"]["pid"])
    os.kill(pid, signal.SIGKILL)
    deadline = time.time() + 2.0
    while time.time() < deadline and process_alive(pid):
        time.sleep(0.05)
    status = launcher.status("sess-dead")
    assert status["identity_ok"] is False
    health = launcher.health("sess-dead")
    assert health["healthy"] is False
    launcher.recover("sess-dead")


def test_capture_identity_roundtrip_for_self() -> None:
    identity = capture_process_identity(os.getpid())
    assert identity.pid == os.getpid()
    verified = verify_process_identity(identity)
    assert verified.pid == identity.pid
