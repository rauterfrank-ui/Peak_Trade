"""O2 technical supervision: simulated faults and disposable local workers only."""

import asyncio
import json
import os
from pathlib import Path
import signal
import subprocess
import time
from unittest.mock import MagicMock

import pytest

from src.ops.canonical_local_launcher_and_process_supervision_v1 import watch_v1 as watch
from src.ops.canonical_local_launcher_and_process_supervision_v1.errors_v1 import (
    CanonicalLauncherError,
)
from src.ops.canonical_local_launcher_and_process_supervision_v1.lifecycle_v1 import (
    CanonicalLocalLauncherV1,
    LauncherPathsV1,
    compute_config_digest_v1,
    resolve_repository_sha,
)
from src.ops.canonical_local_launcher_and_process_supervision_v1.models_v1 import (
    SessionRecordV1,
    ProcessIdentityV1,
)
from src.ops.canonical_local_launcher_and_process_supervision_v1.process_identity_v1 import (
    process_alive,
)
from src.ops.canonical_local_launcher_and_process_supervision_v1.single_writer_v1 import (
    LauncherSingleWriterV1,
)

REPO = Path(__file__).resolve().parents[2]


class Clock:
    now = 0.0

    def time(self):
        return self.now

    def sleep(self, seconds):
        self.now += seconds


def _launcher(tmp_path):
    cfg = tmp_path / "config.json"
    cfg.write_text('{"mode":"dashboard-only"}')
    launcher = CanonicalLocalLauncherV1(
        LauncherPathsV1(REPO, tmp_path / "state", tmp_path / "logs", tmp_path / "evidence")
    )
    return launcher, cfg


@pytest.fixture
def seeded(tmp_path):
    launcher, cfg = _launcher(tmp_path)
    root = launcher.registry.session_dir("test-watch")
    record = SessionRecordV1(
        schema_version="test",
        capability_id="test",
        session_id="test-watch",
        mode="dashboard-only",
        lifecycle_state="RUNNING",
        repository_sha=resolve_repository_sha(REPO),
        config_digest=compute_config_digest_v1(cfg),
        config_path=str(cfg),
        supervisor_identity="test",
        supervision_backend="repository_owned_supervisor",
        supervisor_instance_id="test",
        process_identity=ProcessIdentityV1(99_999_999, 99_999_999, "synthetic-epoch"),
        log_root=str(tmp_path / "logs"),
        state_root=str(tmp_path / "state"),
        evidence_root=str(tmp_path / "evidence"),
        heartbeat_path=str(root / "heartbeat_v1.json"),
        created_at_unix=1,
        updated_at_unix=1,
    )
    launcher.registry.write_session(record)
    return launcher, cfg, record


def _run(launcher, *, restart=True, **kwargs):
    clock = Clock()
    return watch.watch_registered_session_v1(
        launcher,
        session_id="test-watch",
        duration_seconds=1,
        interval_seconds=1,
        restart_on_failure=restart,
        time_fn=clock.time,
        sleep_fn=clock.sleep,
        **kwargs,
    )


def _faults(monkeypatch, launcher, reason="PROCESS_DEAD"):
    ready = False
    calls = []

    def health(*args, **kwargs):
        nonlocal ready
        result = {"healthy": ready, "reason_code": "HEALTHY" if ready else reason}
        ready = False
        return result

    def restart(session_id, **kwargs):
        nonlocal ready
        calls.append(kwargs)
        current = launcher.registry.require_session(session_id)
        assert kwargs["expected_process_identity"] == current.process_identity
        ready = True
        return {"ok": True}

    monkeypatch.setattr(launcher, "health", health)
    monkeypatch.setattr(launcher, "restart", restart)
    return calls


def test_restart_budget_survives_monitor_reinvocation(seeded, monkeypatch):
    launcher, _, _ = seeded
    calls = _faults(monkeypatch, launcher)
    for expected in range(1, 4):
        assert _run(launcher)["restart_attempts"] == expected
    exhausted = _run(launcher)
    assert exhausted["reason_code"] == "PROCESS_WATCH_RESTART_LIMIT" and len(calls) == 3
    path = launcher.registry.session_dir("test-watch") / watch.WATCH_STATE_FILENAME
    assert json.loads(path.read_text())["restart_attempts"] == 3


def test_restart_is_opt_in(seeded, monkeypatch):
    launcher, _, _ = seeded
    calls = _faults(monkeypatch, launcher)
    result = _run(launcher, restart=False)
    assert not result["ok"] and result["owner_action_required"] and not calls


@pytest.mark.parametrize(
    "reason",
    [
        "PROCESS_IDENTITY_UNPROVEN",
        "HEARTBEAT_BINDING_UNPROVEN",
        "HEARTBEAT_CLOCK_OR_TIME_UNPROVEN",
        "HEARTBEAT_SCHEMA_UNPROVEN",
    ],
)
def test_unknown_identity_is_never_signalled(seeded, monkeypatch, reason):
    launcher, _, _ = seeded
    calls = _faults(monkeypatch, launcher, reason)
    assert _run(launcher)["reason_code"] == reason
    assert not calls


@pytest.mark.parametrize("kind", ["config", "revision"])
def test_changed_binding_prevents_restart(seeded, monkeypatch, kind):
    launcher, cfg, record = seeded
    if kind == "config":
        cfg.write_text('{"mode":"dashboard-only","changed":true}')
    else:
        record.repository_sha = "f" * 40
        launcher.registry.write_session(record)
    calls = _faults(monkeypatch, launcher)
    assert _run(launcher)["reason_code"] == (
        "PROCESS_WATCH_CONFIG_CHANGED" if kind == "config" else "PROCESS_WATCH_REVISION_CHANGED"
    )
    assert not calls


def test_operator_stop_is_honored(seeded, monkeypatch):
    launcher, _, record = seeded
    record.lifecycle_state = "STOPPED"
    launcher.registry.write_session(record)
    calls = _faults(monkeypatch, launcher)
    assert _run(launcher)["reason_code"] == "PROCESS_WATCH_SESSION_NOT_RUNNING"
    assert not calls


def test_different_registered_epoch_cannot_be_stopped(seeded):
    launcher, _, _ = seeded
    with pytest.raises(CanonicalLauncherError, match="WATCH_OBSERVATION_SUPERSEDED"):
        launcher.stop(
            "test-watch",
            expected_process_identity=ProcessIdentityV1(88_888_888, 88_888_888, "different"),
        )
    assert launcher.registry.require_session("test-watch").lifecycle_state == "RUNNING"


@pytest.mark.parametrize("healthy", [True, False])
def test_interrupted_restart_requires_ready_current_worker_or_owner(seeded, monkeypatch, healthy):
    launcher, _, _ = seeded
    _faults(monkeypatch, launcher)
    _run(launcher)
    path = launcher.registry.session_dir("test-watch") / watch.WATCH_STATE_FILENAME
    state = json.loads(path.read_text())
    state["in_progress"] = True
    watch._save_watch_state_v1(path, state)
    monkeypatch.setattr(
        launcher, "health", lambda *a, **k: {"healthy": healthy, "reason_code": "PROCESS_DEAD"}
    )
    monkeypatch.setattr(
        launcher, "restart", lambda *a, **k: pytest.fail("uncertain restart must not repeat")
    )
    result = _run(launcher)
    assert result["restart_attempts"] == 1
    assert result["reason_code"] == (
        "PROCESS_WATCH_BOUND_REACHED" if healthy else "PROCESS_WATCH_RESTART_OUTCOME_UNCERTAIN"
    )
    assert json.loads(path.read_text())["in_progress"] is (not healthy)


def test_corrupt_restart_budget_is_preserved(seeded, monkeypatch):
    launcher, _, _ = seeded
    calls = _faults(monkeypatch, launcher)
    path = launcher.registry.session_dir("test-watch") / watch.WATCH_STATE_FILENAME
    path.write_text('{"restart_attempts":-10}')
    assert _run(launcher)["reason_code"] == "PROCESS_WATCH_STATE_UNPROVEN"
    assert path.read_text() == '{"restart_attempts":-10}' and not calls


def test_missing_restart_budget_cannot_reset_old_attempts(seeded, monkeypatch):
    launcher, _, _ = seeded
    calls = _faults(monkeypatch, launcher)
    _run(launcher)
    (launcher.registry.session_dir("test-watch") / watch.WATCH_STATE_FILENAME).unlink()
    assert _run(launcher)["reason_code"] == "PROCESS_WATCH_STATE_MISSING"
    assert len(calls) == 1


def test_interrupted_restart_in_stopped_state_is_not_an_owner_stop(seeded, monkeypatch):
    launcher, _, record = seeded
    _faults(monkeypatch, launcher)
    _run(launcher)
    path = launcher.registry.session_dir("test-watch") / watch.WATCH_STATE_FILENAME
    state = json.loads(path.read_text())
    state["in_progress"] = True
    watch._save_watch_state_v1(path, state)
    record.lifecycle_state = "STOPPED"
    launcher.registry.write_session(record)
    assert _run(launcher)["reason_code"] == "PROCESS_WATCH_RESTART_OUTCOME_UNCERTAIN"


def test_operator_stop_between_restart_stop_and_start_prevents_start(seeded, monkeypatch):
    launcher, _, _ = seeded
    actual_start = launcher.start

    def changed(*args, **kwargs):
        launcher.stop("test-watch")
        return actual_start(*args, **kwargs)

    monkeypatch.setattr(launcher, "start", changed)
    with pytest.raises(CanonicalLauncherError, match="RESTART_STOP_STATE_SUPERSEDED"):
        launcher.restart("test-watch")
    assert launcher.registry.require_session("test-watch").lifecycle_state == "STOPPED"


@pytest.mark.parametrize("lifecycle", ["FAILED", "OWNER_LOCKED", "STARTING"])
def test_failed_or_locked_session_requires_action(seeded, monkeypatch, lifecycle):
    launcher, _, record = seeded
    record.lifecycle_state = lifecycle
    launcher.registry.write_session(record)
    calls = _faults(monkeypatch, launcher)
    result = _run(launcher)
    assert result["owner_action_required"] and not result["ok"] and not calls


def test_duplicate_monitor_cannot_spend_restart_budget(seeded, monkeypatch):
    launcher, _, _ = seeded
    calls = _faults(monkeypatch, launcher)
    with LauncherSingleWriterV1(
        launcher.registry.session_dir("test-watch") / "process_watch_exclusion_v1"
    ):
        with pytest.raises(CanonicalLauncherError, match="WRITER_CONFLICT"):
            _run(launcher)
    assert not calls


@pytest.mark.parametrize(
    "field,value",
    [
        ("ts_unix", float("inf")),
        ("ts_unix", "broken"),
        ("ts_unix", time.time() + 10000),
        ("session_id", "foreign"),
        ("pid", 1),
        ("pgid", True),
    ],
)
def test_health_does_not_accept_unbound_or_invalid_heartbeat(seeded, monkeypatch, field, value):
    launcher, _, record = seeded
    monkeypatch.setattr(launcher, "status", lambda _: {"process_alive": True, "identity_ok": True})
    heartbeat = {
        "ts_unix": time.time(),
        "session_id": "test-watch",
        "pid": 99_999_999,
        "pgid": 99_999_999,
        "healthy": True,
    }
    heartbeat[field] = value
    Path(record.heartbeat_path).write_text(json.dumps(heartbeat))
    assert not launcher.health("test-watch")["healthy"]


def test_watch_cli_dispatch_and_failure_exit(seeded, monkeypatch, capsys):
    from src.ops.canonical_local_launcher_and_process_supervision_v1 import cli_v1

    launcher, _, _ = seeded
    monkeypatch.setattr(cli_v1, "CanonicalLocalLauncherV1", lambda _: launcher)
    seen = []

    def capture(*args, **kwargs):
        seen.append(kwargs)
        return {"ok": False, "reason_code": "PROCESS_WATCH_RESTART_LIMIT"}

    monkeypatch.setattr(watch, "watch_registered_session_v1", capture)
    rc = cli_v1.dispatch(
        [
            "watch",
            "--session-id",
            "test-watch",
            "--duration-seconds",
            "3",
            "--interval-seconds",
            "1",
            "--restart-on-failure",
        ]
    )
    assert rc == 1 and seen[0]["restart_on_failure"]
    assert "PROCESS_WATCH_RESTART_LIMIT" in capsys.readouterr().out


@pytest.fixture
def real_worker(tmp_path):
    launcher, cfg = _launcher(tmp_path)
    started = launcher.start(session_id="test-watch", config_path=cfg)
    original_pid = started["session"]["process_identity"]["pid"]
    try:
        yield launcher, cfg, original_pid
    finally:
        if process_alive(original_pid):
            os.kill(original_pid, signal.SIGCONT)
        launcher.stop("test-watch", graceful_timeout_seconds=0.5)


def _assert_process_recovery_reaches_mail_worker(launcher, monkeypatch):
    from src.ops.runtime_health_recovery_and_failure_injection_closure_v1.runtime_mail_worker_v1 import (
        process_mail_worker_batch_v1,
    )
    from tests.ops.test_runtime_recovery_email_v1 import _channel

    root = launcher.registry.session_dir("test-watch") / "process_watch_evidence_v1"
    notices = [
        json.loads(line)
        for line in (root / "runtime_liveness_events_v1.jsonl").read_text().splitlines()
    ]
    recovered = next(n for n in notices if n["notification_kind"] == "RECOVERED")
    fault = next(n for n in notices if n["event_id"] == recovered["extra"]["incident_id"])
    assert fault["notification_kind"] == "FAULT"
    assert recovered["extra"]["recovery_scope"] == "DASHBOARD_PROCESS_HEARTBEAT"
    smtp = MagicMock()
    smtp.__enter__.return_value = smtp
    monkeypatch.setattr(
        "src.risk_layer.alerting.channels.email_channel.smtplib.SMTP", lambda *a, **k: smtp
    )
    settings = {
        "mail_config_path": str(root / "unused"),
        "source_roots": [str(launcher.paths.state_root)],
    }
    result = asyncio.run(
        process_mail_worker_batch_v1(settings, channel_factory=lambda _: _channel())
    )
    assert result["transport_accepted"] == smtp.send_message.call_count == 2
    assert result["pending"] == result["exhausted"] == result["queue_errors"] == 0
    asyncio.run(process_mail_worker_batch_v1(settings, channel_factory=lambda _: _channel()))
    assert smtp.send_message.call_count == 2


def test_real_killed_worker_is_detected_and_restarted(real_worker, monkeypatch):
    launcher, _, pid = real_worker
    os.kill(pid, signal.SIGKILL)
    deadline = time.monotonic() + 3
    while process_alive(pid) and time.monotonic() < deadline:
        time.sleep(0.02)
    assert not process_alive(pid)
    result = watch.watch_registered_session_v1(
        launcher,
        session_id="test-watch",
        duration_seconds=1,
        interval_seconds=0.1,
        restart_on_failure=True,
    )
    assert result["restart_attempts"] == 1
    assert launcher.health("test-watch")["healthy"]
    assert launcher.registry.require_session("test-watch").process_identity.pid != pid
    _assert_process_recovery_reaches_mail_worker(launcher, monkeypatch)


def test_real_frozen_worker_is_fenced_and_restarted(real_worker, monkeypatch):
    launcher, _, pid = real_worker
    os.kill(pid, signal.SIGSTOP)
    record = launcher.registry.require_session("test-watch")
    heartbeat = json.loads(Path(record.heartbeat_path).read_text())
    heartbeat["ts_unix"] = time.time() - 60
    Path(record.heartbeat_path).write_text(json.dumps(heartbeat))
    result = watch.watch_registered_session_v1(
        launcher,
        session_id="test-watch",
        duration_seconds=1,
        interval_seconds=0.1,
        restart_on_failure=True,
    )
    assert result["restart_attempts"] == 1 and not process_alive(pid)
    assert launcher.health("test-watch")["healthy"]
    transitions = launcher.registry.transitions_path("test-watch").read_text()
    assert "STOP_ESCALATED" in transitions
    _assert_process_recovery_reaches_mail_worker(launcher, monkeypatch)


def test_changed_config_is_rejected_before_stopping_real_worker(real_worker):
    launcher, cfg, pid = real_worker
    cfg.write_text('{"mode":"dashboard-only","changed":true}')
    with pytest.raises(CanonicalLauncherError, match="CONFIG_DIGEST_MISMATCH"):
        launcher.restart("test-watch")
    assert process_alive(pid)
    assert launcher.registry.require_session("test-watch").process_identity.pid == pid


def test_packed_git_refs_resolve_without_loose_branch_file(tmp_path):
    for args in [
        ["init", "--quiet"],
        [
            "-c",
            "user.name=Offline Test",
            "-c",
            "user.email=offline@example.invalid",
            "commit",
            "--allow-empty",
            "-qm",
            "synthetic repository for resolver",
        ],
        ["pack-refs", "--all", "--prune"],
    ]:
        subprocess.run(["git", "-C", str(tmp_path), *args], check=True, capture_output=True)
    expected = subprocess.check_output(
        ["git", "-C", str(tmp_path), "rev-parse", "HEAD"], text=True
    ).strip()
    assert resolve_repository_sha(tmp_path) == expected


def test_provably_dead_launcher_lock_can_be_reclaimed(tmp_path):
    code = "from pathlib import Path; import os,sys; from src.ops.canonical_local_launcher_and_process_supervision_v1.single_writer_v1 import LauncherSingleWriterV1; LauncherSingleWriterV1(Path(sys.argv[1])).acquire(); os._exit(0)"
    import sys

    subprocess.run([sys.executable, "-c", code, str(tmp_path)], check=True, cwd=REPO)
    owner = LauncherSingleWriterV1(tmp_path)
    owner.acquire()
    try:
        assert len(list(tmp_path.glob("launcher_writer.lock.dead_process.*"))) == 1
    finally:
        owner.release()
