"""Contract tests for the paper-tests-audit-evidence workflow.

These tests parse the workflow YAML as a static contract only.
They never dispatch workflows, never access secret values, and never run scripts.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest

yaml = pytest.importorskip("yaml")

WORKFLOW = Path(".github/workflows/paper_tests_audit_evidence.yml")

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
    data = _workflow()
    assert data.get("name") == "paper-tests-audit-evidence"


def test_workflow_dispatch_only_without_active_schedule() -> None:
    triggers = _trigger_section(_workflow())

    assert "workflow_dispatch" in triggers
    assert "schedule" not in triggers


def test_workflow_dispatch_scope_input_matches_audit_contract() -> None:
    wd = _trigger_section(_workflow()).get("workflow_dispatch")
    assert isinstance(wd, dict)
    inputs = wd.get("inputs")
    assert isinstance(inputs, dict)

    scope_spec = inputs.get("scope")
    assert isinstance(scope_spec, dict)
    assert scope_spec.get("default") == "execution"

    choices = scope_spec.get("options")
    assert isinstance(choices, list)
    assert "execution" in choices
    assert "full" in choices


def test_workflow_allows_audit_execution_semantics_in_source() -> None:
    """Regression guard: these strings are legitimate offline audit paths."""
    text = _workflow_text()
    assert "tests/execution" in text
    assert "pytest" in text.lower()


def test_workflow_permissions_are_contents_read_only() -> None:
    data = _workflow()
    permissions = data.get("permissions")

    assert permissions != "write-all"
    assert isinstance(permissions, dict)
    assert permissions == {"contents": "read"}

    lowered = _workflow_text().lower()
    assert "contents: write" not in lowered


def test_workflow_actions_scope_not_granted_write() -> None:
    """Orchestration workflows may use actions:write; this audit workflow does not."""
    permissions = _workflow().get("permissions")
    assert isinstance(permissions, dict)
    assert permissions.get("actions") != "write"


def test_workflow_has_cancel_in_progress_concurrency() -> None:
    data = _workflow()
    conc = data.get("concurrency")
    assert isinstance(conc, dict)
    assert conc.get("cancel-in-progress") is True


def test_workflow_jobs_have_defensive_live_env_and_timeouts() -> None:
    jobs = _jobs(_workflow())
    assert len(jobs) >= 1

    for job_body in jobs.values():
        assert isinstance(job_body, dict)

        timeout = job_body.get("timeout-minutes")
        assert isinstance(timeout, int)
        assert 15 <= timeout <= 90

        env = job_body.get("env")
        assert isinstance(env, dict)
        assert env.get("PEAK_TRADE_TESTNET_ONLY") == "false"
        assert env.get("PEAK_TRADE_LIVE_ENABLED") == "false"
        assert env.get("PEAK_TRADE_LIVE_ARMED") == "false"
        assert env.get("PT_DRY_RUN") == "1"


def test_workflow_avoids_peak_trade_live_literal_true() -> None:
    lowered = _workflow_text().lower()
    assert "peak_trade_live_enabled: true" not in lowered
    assert "peak_trade_live_armed: true" not in lowered


def test_workflow_guardrails_script_present() -> None:
    assert "bash scripts/ci/scheduled_guardrails.sh" in _workflow_text()


def test_workflow_only_uses_allowlisted_secrets() -> None:
    assert _secret_names_in_text(_workflow_text()) == _ALLOWED_SECRETS


def test_workflow_lists_expected_guardrail_secret_placeholders() -> None:
    text = _workflow_text()
    assert "${{ secrets.PT_RCLONE_CONF_B64 }}" in text
    assert "${{ secrets.PT_EXPORT_REMOTE }}" in text
    assert "${{ secrets.PT_EXPORT_PREFIX }}" in text


def test_workflow_schedule_gate_vars_present_in_guardrail_env() -> None:
    text = _workflow_text()
    assert "vars.PT_SCHEDULED_PAPER_TESTS_ENABLED" in text
    assert "vars.PT_SCHEDULED_EXPORT_VERIFY_ENABLED" in text


def test_workflow_uploads_audit_evidence_without_readiness_claims() -> None:
    text = _workflow_text()

    assert "actions/upload-artifact@v4" in text
    assert "out/ops/gh_paper_tests_audit" in text

    lowered = text.lower()
    assert "live_ready" not in lowered
    assert "futures_ready" not in lowered
    assert "gate_passed" not in lowered
