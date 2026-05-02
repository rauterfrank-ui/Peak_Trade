"""Contract tests for the shadow-paper-smoke workflow.

These tests parse the workflow YAML as a static contract only.
They never dispatch workflows, never access secret values, and never run scripts.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

yaml = pytest.importorskip("yaml")

WORKFLOW = Path(".github/workflows/shadow_paper_smoke.yml")


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


def test_workflow_exists_parseable_and_named() -> None:
    assert _workflow().get("name") == "shadow-paper-smoke"


def test_workflow_dispatch_only_without_active_schedule() -> None:
    triggers = _trigger_section(_workflow())

    assert "workflow_dispatch" in triggers
    assert "schedule" not in triggers


def test_workflow_dispatch_mode_input_supports_paper_and_shadow() -> None:
    wd = _trigger_section(_workflow()).get("workflow_dispatch")
    assert isinstance(wd, dict)
    inputs = wd.get("inputs")
    assert isinstance(inputs, dict)

    mode_spec = inputs.get("mode")
    assert isinstance(mode_spec, dict)
    assert mode_spec.get("default") == "paper"

    choices = mode_spec.get("options")
    assert isinstance(choices, list)
    assert "paper" in choices
    assert "shadow" in choices


def test_workflow_permissions_are_contents_read_only() -> None:
    data = _workflow()
    permissions = data.get("permissions")

    assert permissions != "write-all"
    assert isinstance(permissions, dict)
    assert permissions == {"contents": "read"}

    lowered = _workflow_text().lower()
    assert "contents: write" not in lowered
    assert permissions.get("actions") != "write"


def test_workflow_does_not_reference_github_secrets() -> None:
    assert "${{ secrets." not in _workflow_text()


def test_workflow_has_no_top_level_concurrency_block() -> None:
    assert _workflow().get("concurrency") is None


def test_workflow_does_not_bind_scheduled_export_guardrails_surface() -> None:
    """IST smoke workflow stays separate from scheduled paper/export orchestration."""
    text = _workflow_text()
    assert "scheduled_guardrails.sh" not in text
    assert "PT_SCHEDULED_PAPER_TESTS_ENABLED" not in text
    assert "PT_SCHEDULED_EXPORT_VERIFY_ENABLED" not in text


def test_workflow_contains_shadow_paper_smoke_semantics_and_allowed_strings() -> None:
    """Regression-friendly positives; do not forbid place_order / pytest / tests/execution."""
    text = _workflow_text()
    lowered = text.lower()

    assert "shadow" in lowered
    assert "paper" in lowered
    assert "smoke" in lowered

    assert "tests/execution" in text
    assert "pytest" in lowered
    assert "place_order" in lowered


def test_workflow_jobs_have_defensive_live_env_and_timeouts() -> None:
    jobs = _jobs(_workflow())
    assert len(jobs) >= 1

    for job_body in jobs.values():
        assert isinstance(job_body, dict)

        timeout = job_body.get("timeout-minutes")
        assert isinstance(timeout, int)
        assert 10 <= timeout <= 45

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


def test_workflow_uploads_evidence_without_readiness_claims() -> None:
    text = _workflow_text()

    assert "actions/upload-artifact@v4" in text
    assert "out/ops/gh_shadow_paper_smoke" in text

    lowered = text.lower()
    assert "live_ready" not in lowered
    assert "futures_ready" not in lowered
    assert "gate_passed" not in lowered
