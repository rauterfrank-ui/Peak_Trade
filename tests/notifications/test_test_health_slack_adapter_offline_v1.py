"""Offline regression for the fail-closed test-health Slack adapter."""

from __future__ import annotations

import ast
import datetime as dt
import os
from pathlib import Path
from unittest.mock import patch

from src.notifications.base import Alert, Notifier
from src.notifications.slack import (
    EXTERNAL_EFFECT_AUTHORIZED,
    SlackNotifier,
    send_test_health_slack_notification,
    send_test_health_slack_notification_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
ADAPTER_FILES = (
    REPO_ROOT / "src" / "notifications" / "__init__.py",
    REPO_ROOT / "src" / "notifications" / "base.py",
    REPO_ROOT / "src" / "notifications" / "slack.py",
)
FORBIDDEN_SOURCE_MARKERS = (
    "src.risk_layer",
    "src.execution",
    "src.live",
    "src.trading",
    "src.notifications.console",
    "src.notifications.file",
    "src.notifications.combined",
    "urllib",
    "urlopen",
    "requests",
    "http.client",
    "httpx",
    "socket",
)


def test_both_surfaces_are_importable() -> None:
    alert = Alert(
        level="warning",
        source="test_health",
        message="local only",
        timestamp=dt.datetime(2025, 12, 10, 14, 30, 0),
    )
    notifier = SlackNotifier(webhook_url=None)

    assert isinstance(notifier, Notifier)
    assert callable(send_test_health_slack_notification)
    assert callable(send_test_health_slack_notification_v1)
    assert alert.message == "local only"
    assert EXTERNAL_EFFECT_AUTHORIZED is False


@patch("urllib.request.urlopen")
def test_missing_or_empty_webhook_performs_no_delivery(mock_urlopen) -> None:
    with patch.dict(os.environ, {}, clear=True):
        send_test_health_slack_notification_v1(
            message="status",
            webhook_env_var="PEAK_TRADE_SLACK_WEBHOOK_TESTHEALTH",
        )
        send_test_health_slack_notification(
            profile_name="daily_quick",
            health_score=10.0,
            failed_checks=1,
            passed_checks=0,
            violations=[],
            report_path="reports/test_health/offline",
            webhook_env_var="PEAK_TRADE_SLACK_WEBHOOK_TESTHEALTH",
        )
        SlackNotifier(webhook_url=None).send(
            Alert(
                level="info",
                source="test_health",
                message="quiet",
                timestamp=dt.datetime(2025, 12, 10, 14, 30, 0),
            )
        )

    with patch.dict(os.environ, {"PEAK_TRADE_SLACK_WEBHOOK_TESTHEALTH": ""}):
        send_test_health_slack_notification_v1(
            message="status",
            webhook_env_var="PEAK_TRADE_SLACK_WEBHOOK_TESTHEALTH",
        )

    assert mock_urlopen.called is False


@patch("urllib.request.urlopen")
def test_configured_webhook_alone_has_no_external_effect(mock_urlopen) -> None:
    secret = "https://hooks.slack.com/services/OFFLINE/TOKEN/VALUE"
    with patch.dict(os.environ, {"PEAK_TRADE_SLACK_WEBHOOK_TESTHEALTH": secret}):
        send_test_health_slack_notification_v1(
            message="[Peak_Trade · TestHealth v1] Status: FAILED",
            webhook_env_var="PEAK_TRADE_SLACK_WEBHOOK_TESTHEALTH",
        )
        send_test_health_slack_notification(
            profile_name="weekly_core",
            health_score=40.0,
            failed_checks=2,
            passed_checks=1,
            violations=[],
            report_path="reports/test_health/offline",
            webhook_env_var="PEAK_TRADE_SLACK_WEBHOOK_TESTHEALTH",
        )
        SlackNotifier(webhook_url=secret).send(
            Alert(
                level="critical",
                source="test_health",
                message="closed",
                timestamp=dt.datetime(2025, 12, 10, 14, 30, 0),
            )
        )

    assert mock_urlopen.called is False


def test_formatter_and_delivery_errors_stay_contained(capsys) -> None:
    notifier = SlackNotifier(webhook_url="https://hooks.slack.com/services/SECRET/PATH")
    alert = Alert(
        level="warning",
        source="test_health",
        message="stable",
        timestamp=dt.datetime(2025, 12, 10, 14, 30, 0),
    )
    alert.timestamp = None  # type: ignore[assignment]

    notifier.send(alert)
    send_test_health_slack_notification_v1(
        message="status",
        webhook_env_var="PEAK_TRADE_SLACK_WEBHOOK_TESTHEALTH",
    )

    captured = capsys.readouterr()
    assert "SECRET" not in captured.out
    assert "hooks.slack.com" not in captured.out
    assert "fehlgeschlagen" in captured.out


def test_runner_contract_and_report_builder_stay_unmodified() -> None:
    runner = (REPO_ROOT / "src" / "ops" / "test_health_runner.py").read_text(encoding="utf-8")
    assert "def _build_slack_message_v1(" in runner
    assert "send_test_health_slack_notification_v1(" in runner
    assert "webhook_env_var=webhook_env_var" in runner
    assert "src.risk_layer" not in runner[runner.find("def _send_slack_notification_if_needed") :]


def test_adapter_source_has_no_foreign_or_transport_links() -> None:
    package_init = (REPO_ROOT / "src" / "notifications" / "__init__.py").read_text(encoding="utf-8")
    init_tree = ast.parse(package_init)
    assert not any(isinstance(node, (ast.Import, ast.ImportFrom)) for node in init_tree.body)

    combined = "\n".join(path.read_text(encoding="utf-8").lower() for path in ADAPTER_FILES)
    present = [marker for marker in FORBIDDEN_SOURCE_MARKERS if marker in combined]
    assert present == []

    base_tree = ast.parse(
        (REPO_ROOT / "src" / "notifications" / "base.py").read_text(encoding="utf-8")
    )
    assigned: set[str] = set()
    for node in base_tree.body:
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            assigned.add(node.name)
        elif isinstance(node, ast.Assign):
            assigned.update(target.id for target in node.targets if isinstance(target, ast.Name))
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            assigned.add(node.target.id)
    assert assigned == {"Alert", "Notifier"}
