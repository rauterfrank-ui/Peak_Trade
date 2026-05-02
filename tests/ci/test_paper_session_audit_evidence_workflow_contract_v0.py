"""Contract tests for the paper-session-audit-evidence workflow.

These tests parse the workflow YAML as a static contract only.
They never dispatch workflows, never access secret values, and never run scripts.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest

yaml = pytest.importorskip("yaml")

WORKFLOW = Path(".github/workflows/paper_session_audit_evidence.yml")

_ALLOWED_SECRETS = frozenset(
    {
        "PT_RCLONE_CONF_B64",
        "PT_EXPORT_REMOTE",
        "PT_EXPORT_PREFIX",
    }
)

_SECRETS_TOKEN_RE = re.compile(r"\$\{\{\s*secrets\.([A-Za-z0-9_]+)\s*\}\}")


def _workflow() -> dict[str, Any]:
    assert WORKFLOW.exists()
    data = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def _workflow_text() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def _trigger_section(data: dict[str, Any]) -> dict[str, Any]:
    """GitHub workflows use `on:` which PyYAML 1.1 may parse as bool key True."""
    triggers = data.get("on")
    if triggers is None:
        triggers = data.get(True)
    assert isinstance(triggers, dict)
    return triggers


def _jobs(data: dict[str, Any]) -> dict[str, Any]:
    jobs = data.get("jobs")
    assert isinstance(jobs, dict)
    return jobs


def _secret_names_in_text(text: str) -> set[str]:
    return set(_SECRETS_TOKEN_RE.findall(text))


def test_workflow_exists_parseable_and_named() -> None:
    assert _workflow().get("name") == "paper-session-audit-evidence"


def test_workflow_dispatch_only_without_active_schedule() -> None:
    triggers = _trigger_section(_workflow())

    assert "workflow_dispatch" in triggers
    assert "schedule" not in triggers


def test_workflow_dispatch_has_session_inputs() -> None:
    wd = _trigger_section(_workflow()).get("workflow_dispatch")
    assert isinstance(wd, dict)
    inputs = wd.get("inputs")
    assert isinstance(inputs, dict)

    spec = inputs.get("spec")
    assert isinstance(spec, dict)
    assert "tests/fixtures/p7/paper_run_min_v0.json" in str(spec.get("default", ""))

    run_id_spec = inputs.get("run_id")
    assert isinstance(run_id_spec, dict)
    assert run_id_spec.get("default") == "ci_smoke"


def test_workflow_permissions_allow_actions_write_and_contents_read() -> None:
    data = _workflow()
    permissions = data.get("permissions")

    assert permissions != "write-all"
    assert isinstance(permissions, dict)
    assert permissions.get("contents") == "read"
    assert permissions.get("actions") == "write"
    assert set(permissions.keys()) <= {"contents", "actions"}

    lowered = _workflow_text().lower()
    assert "contents: write" not in lowered

    extra_write_scopes = (
        "checks",
        "deployments",
        "issues",
        "packages",
        "pull-requests",
        "repository-projects",
        "security-events",
        "statuses",
    )
    for scope in extra_write_scopes:
        assert permissions.get(scope) != "write"


def test_workflow_has_cancel_in_progress_concurrency() -> None:
    data = _workflow()
    conc = data.get("concurrency")
    assert isinstance(conc, dict)
    assert conc.get("cancel-in-progress") is True


def test_workflow_only_uses_allowlisted_secrets() -> None:
    assert _secret_names_in_text(_workflow_text()) == _ALLOWED_SECRETS


def test_workflow_lists_expected_guardrail_secret_placeholders() -> None:
    text = _workflow_text()
    assert "${{ secrets.PT_RCLONE_CONF_B64 }}" in text
    assert "${{ secrets.PT_EXPORT_REMOTE }}" in text
    assert "${{ secrets.PT_EXPORT_PREFIX }}" in text


def test_workflow_has_guardrails_and_scheduled_vars() -> None:
    text = _workflow_text()
    assert "bash scripts/ci/scheduled_guardrails.sh" in text
    assert "vars.PT_SCHEDULED_PAPER_TESTS_ENABLED" in text
    assert "vars.PT_SCHEDULED_EXPORT_VERIFY_ENABLED" in text


def test_workflow_jobs_have_defensive_env_and_evidence_flag() -> None:
    jobs = _jobs(_workflow())
    assert len(jobs) >= 1

    for job_body in jobs.values():
        assert isinstance(job_body, dict)

        timeout = job_body.get("timeout-minutes")
        assert isinstance(timeout, int)
        assert 25 <= timeout <= 90

        env = job_body.get("env")
        assert isinstance(env, dict)
        assert env.get("PEAK_TRADE_TESTNET_ONLY") == "false"
        assert env.get("PEAK_TRADE_LIVE_ENABLED") == "false"
        assert env.get("PEAK_TRADE_LIVE_ARMED") == "false"
        assert env.get("PT_DRY_RUN") == "1"
        assert env.get("PT_EVIDENCE_INCLUDE_DECISION") == "1"


def test_workflow_avoids_peak_trade_live_literal_true() -> None:
    lowered = _workflow_text().lower()
    assert "peak_trade_live_enabled: true" not in lowered
    assert "peak_trade_live_armed: true" not in lowered


def test_workflow_runs_paper_session_runner_for_audit_evidence() -> None:
    assert "scripts/aiops/run_paper_trading_session.py" in _workflow_text()


def test_workflow_uploads_session_audit_evidence_without_readiness_claims() -> None:
    text = _workflow_text()

    assert "actions/upload-artifact@v4" in text
    assert "out/ops/gh_paper_session_audit" in text

    lowered = text.lower()
    assert "live_ready" not in lowered
    assert "futures_ready" not in lowered
    assert "gate_passed" not in lowered
