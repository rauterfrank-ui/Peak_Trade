"""Offline mail service tests: durable retry windows and queue isolation."""

import asyncio
import json
import smtplib
from unittest.mock import MagicMock

from src.ops.runtime_health_recovery_and_failure_injection_closure_v1 import (
    runtime_mail_worker_v1 as worker,
)
from src.ops.runtime_health_recovery_and_failure_injection_closure_v1 import (
    runtime_recovery_email_v1 as mail,
)
from tests.ops.test_runtime_recovery_email_v1 import _channel, _fault_and_recovery


def test_only_explicit_roots_no_symlink_escape(tmp_path):
    allowed, outside = tmp_path / "allowed", tmp_path / "outside"
    _fault_and_recovery(allowed / "run")
    _fault_and_recovery(outside)
    (allowed / "escape").symlink_to(outside, target_is_directory=True)
    assert worker.discover_notice_roots_v1([allowed]) == [allowed / "run"]


def test_bad_queue_does_not_block_good_queue(tmp_path):
    _fault_and_recovery(tmp_path / "good")
    bad = tmp_path / "bad"
    bad.mkdir()
    (bad / worker.EVENTS_FILENAME).write_text("invalid json\n")
    channel = _channel()
    calls = []

    async def dispatch(event):
        calls.append(event)
        return True

    channel.dispatch = dispatch
    settings = {"mail_config_path": str(tmp_path / "unused"), "source_roots": [str(tmp_path)]}
    result = asyncio.run(
        worker.process_mail_worker_batch_v1(settings, channel_factory=lambda _: channel)
    )
    assert result["queue_errors"] == 1
    assert result["transport_accepted"] == 2
    assert len(calls) == 2
    asyncio.run(worker.process_mail_worker_batch_v1(settings, channel_factory=lambda _: channel))
    assert len(calls) == 2  # Receipts survive fresh worker batches.


def test_transient_exhaustion_renews_only_after_cooldown(tmp_path):
    _fault_and_recovery(tmp_path)
    channel = _channel()
    clock = [1000.0]
    calls = []

    async def dispatch(event):
        calls.append(event)
        channel.last_failure_retryable = True
        return False

    channel.dispatch = dispatch

    def batch():
        return asyncio.run(
            mail.process_runtime_recovery_emails_v1(
                evidence_root=tmp_path,
                channel=channel,
                deliver=True,
                retry_cooldown_seconds=600,
                now_fn=lambda: clock[0],
            )
        )

    for _ in range(3):
        batch()
    assert len(calls) == 6
    assert len(batch()["exhausted"]) == 2
    clock[0] = 1599
    batch()
    assert len(calls) == 6
    clock[0] = 1600
    batch()
    assert len(calls) == 8
    receipts = list((tmp_path / "runtime_recovery_email_delivery_v1").glob("*/*.json"))
    for receipt in receipts:
        state = json.loads(receipt.read_text())
        assert state["attempts"] == 1
        assert state["total_attempts"] == 4
        assert state["retry_windows"] == 1


def test_auth_failure_does_not_renew_after_time_passes(tmp_path):
    _fault_and_recovery(tmp_path)
    channel = _channel()
    calls = []

    async def dispatch(event):
        calls.append(event)
        channel.last_failure_retryable = False
        return False

    channel.dispatch = dispatch
    for now in (0, 60, 120, 10000):
        asyncio.run(
            mail.process_runtime_recovery_emails_v1(
                evidence_root=tmp_path,
                channel=channel,
                deliver=True,
                retry_cooldown_seconds=600,
                now_fn=lambda: now,
            )
        )
    assert len(calls) == 6


def test_smtp_transient_vs_auth(monkeypatch):
    channel = _channel()
    from src.risk_layer.alerting.channels import email_channel

    smtp = MagicMock()
    monkeypatch.setattr(email_channel.smtplib, "SMTP", smtp)
    event = MagicMock()
    monkeypatch.setattr(channel, "_build_message", lambda _: "synthetic")
    for error, retryable in [
        (smtplib.SMTPDataError(451, b"temporary"), True),
        (smtplib.SMTPAuthenticationError(535, b"auth"), False),
        (TimeoutError(), True),
    ]:
        smtp.side_effect = error
        assert asyncio.run(channel.send(event)) is False
        assert channel.last_failure_retryable is retryable


def test_service_install_uses_canonical_python_and_no_secret(tmp_path, monkeypatch):
    from datetime import datetime, timezone
    import plistlib
    from types import SimpleNamespace
    from pathlib import Path
    from src.ops.canonical_local_launcher_and_process_supervision_v1 import (
        mail_service_v1 as service,
    )

    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.setattr(service.sys, "platform", "darwin")
    repo = tmp_path / "repo"
    (repo / "scripts").mkdir(parents=True)
    (repo / "scripts/pt").write_text("synthetic launcher")
    cfg = service.default_recovery_email_config_path_v1()
    cfg.parent.mkdir(parents=True)
    cfg.write_text("{}")
    calls = []

    def run(args, **kwargs):
        calls.append(args)
        return SimpleNamespace(returncode=0, stdout=b"state = spawn scheduled\n")

    monkeypatch.setattr(service.subprocess, "run", run)
    result = service.mail_service_v1(repo, "install")
    payload = plistlib.loads(Path(result["plist"]).read_bytes())
    assert payload["ProgramArguments"][:2] == [str(repo / "scripts/pt"), "-m"]
    assert payload["KeepAlive"] is True
    assert payload["RunAtLoad"] is True
    assert payload["ThrottleInterval"] == 60
    assert "EnvironmentVariables" not in payload
    assert calls[0][1] == "bootstrap"
    settings = json.loads((cfg.parent / "runtime_mail_worker_v1.json").read_text())
    assert settings["source_roots"] == [
        str(repo / ".runtime/canonical_local_launcher_v1"),
        str(repo / "runtime/current_productive"),
    ]
    assert result["ok"] is False  # Installed alone is not fresh worker readiness.
    assert result["process_identity_bound"] is False
    service.write_json(
        Path(settings["state_root"]) / "status.json",
        {
            "observed_at_utc": datetime.now(timezone.utc).isoformat(),
            "pid": 42,
            "status": "READY",
        },
    )
    stale_process = service.mail_service_v1(repo, "status")
    assert stale_process["heartbeat_fresh"] is True
    assert stale_process["ok"] is False
    monkeypatch.setattr(
        service.subprocess,
        "run",
        lambda *a, **k: SimpleNamespace(returncode=0, stdout=b"\tpid = 42\n"),
    )
    assert service.mail_service_v1(repo, "status")["ok"] is True
