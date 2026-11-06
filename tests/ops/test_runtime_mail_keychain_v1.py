"""Mail-only keychain setup with all OS/SMTP effects mocked."""

import json
from pathlib import Path
import ssl
from subprocess import CompletedProcess
from unittest.mock import MagicMock

import pytest

from src.ops.runtime_health_recovery_and_failure_injection_closure_v1 import (
    email_keychain_v1 as keychain,
)
from src.ops.runtime_health_recovery_and_failure_injection_closure_v1.runtime_recovery_email_v1 import (
    build_recovery_email_channel_v1,
)


@pytest.fixture
def config(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text(
        json.dumps(
            {
                "enabled": True,
                "smtp_host": "mail.gmx.net",
                "smtp_port": 587,
                "smtp_user": "mail@example.invalid",
                "from_address": "mail@example.invalid",
                "to_addresses": ["mail@example.invalid"],
                "password_env_var": "PEAKTRADE_TEST_SMTP_PASSWORD",
            }
        )
    )
    return path


def _mac_terminal(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _: "")
    monkeypatch.setattr(keychain.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(keychain.os, "isatty", lambda _: True)


def test_read_is_scoped_and_captured_without_logging(monkeypatch, capsys):
    _mac_terminal(monkeypatch)
    calls = []

    def run(argv, **kwargs):
        calls.append((argv, kwargs))
        return CompletedProcess(argv, 0, b"synthetic-secret\n", b"")

    monkeypatch.setattr(keychain.subprocess, "run", run)
    assert keychain.read_mail_keychain_password_v1("mail@example.invalid") == "synthetic-secret"
    assert calls[0][0][-1] == "-w" and calls[0][1]["capture_output"]
    assert keychain.MAIL_KEYCHAIN_SERVICE in calls[0][0]
    assert "synthetic-secret" not in str(calls) + capsys.readouterr().out


def test_non_macos_does_not_touch_store(monkeypatch):
    monkeypatch.setattr(keychain.platform, "system", lambda: "Linux")
    monkeypatch.setattr(
        keychain.subprocess, "run", lambda *a, **k: pytest.fail("unexpected store access")
    )
    assert keychain.read_mail_keychain_password_v1("mail@example.invalid") == ""


def test_setup_requires_users_terminal(config, monkeypatch):
    _mac_terminal(monkeypatch)
    monkeypatch.setattr(keychain.os, "isatty", lambda _: False)
    with pytest.raises(RuntimeError, match="REQUIRES_USER_TERMINAL"):
        keychain.provision_mail_keychain_v1(config)


def test_setup_saves_only_service_reference_and_checks_smtp(config, monkeypatch, capsys):
    _mac_terminal(monkeypatch)
    calls = []

    def run(argv, **kwargs):
        calls.append((argv, kwargs))
        if "add-generic-password" in argv:
            assert argv[-1] == "-w"
            assert "capture_output" not in kwargs
            return CompletedProcess(argv, 0)
        if argv[-1] == "-w":
            return CompletedProcess(argv, 0, b"synthetic-secret\n", b"")
        return CompletedProcess(argv, 44, b"", b"")

    monkeypatch.setattr(keychain.subprocess, "run", run)
    server = MagicMock()
    server.__enter__.return_value = server
    monkeypatch.setattr(keychain.smtplib, "SMTP", lambda *a, **k: server)
    assert keychain.provision_mail_keychain_v1(config)
    cfg = json.loads(config.read_text())
    assert cfg["password_source"] == "macos_keychain"
    assert cfg["keychain_service"] == keychain.MAIL_KEYCHAIN_SERVICE
    assert config.stat().st_mode & 0o777 == 0o600
    assert "synthetic-secret" not in config.read_text() + capsys.readouterr().out + str(calls)
    assert server.starttls.call_args.kwargs["context"].verify_mode == ssl.CERT_REQUIRED
    server.login.assert_called_once_with("mail@example.invalid", "synthetic-secret")
    server.send_message.assert_not_called()
    assert all("-A" not in argv and "-U" not in argv for argv, _ in calls)


def test_cancelled_prompt_preserves_settings(config, monkeypatch):
    _mac_terminal(monkeypatch)
    before = config.read_bytes()
    monkeypatch.setattr(
        keychain.subprocess, "run", lambda argv, **k: CompletedProcess(argv, 1, b"", b"")
    )
    assert not keychain.provision_mail_keychain_v1(config)
    assert config.read_bytes() == before


def test_unexpected_provider_is_rejected_before_password_prompt(config, monkeypatch):
    _mac_terminal(monkeypatch)
    cfg = json.loads(config.read_text())
    cfg["smtp_host"] = "foreign.invalid"
    config.write_text(json.dumps(cfg))
    monkeypatch.setattr(
        keychain.subprocess, "run", lambda *a, **k: pytest.fail("unexpected prompt")
    )
    with pytest.raises(ValueError, match="GMX_BINDING_UNPROVEN"):
        keychain.provision_mail_keychain_v1(config)


def test_mail_channel_reads_only_fixed_keychain_service(config, monkeypatch):
    cfg = json.loads(config.read_text())
    cfg.update(password_source="macos_keychain", keychain_service=keychain.MAIL_KEYCHAIN_SERVICE)
    config.write_text(json.dumps(cfg))
    monkeypatch.setattr(
        keychain, "read_mail_keychain_password_v1", lambda account: "synthetic-secret"
    )
    assert build_recovery_email_channel_v1(config).is_enabled()
    cfg["keychain_service"] = "foreign-service"
    config.write_text(json.dumps(cfg))
    with pytest.raises(ValueError, match="SERVICE_UNPROVEN"):
        build_recovery_email_channel_v1(config)
