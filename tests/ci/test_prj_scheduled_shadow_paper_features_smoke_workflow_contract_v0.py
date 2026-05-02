"""Contract tests for the PR-J scheduled shadow/paper features smoke workflow.

These tests parse the workflow YAML as a static contract only.
They never dispatch the workflow and never touch secrets or providers.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

yaml = pytest.importorskip("yaml")

WORKFLOW = Path(".github/workflows/prj-scheduled-shadow-paper-features-smoke.yml")


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
    data = _workflow()
    assert data.get("name") == "PR-J / Scheduled Shadow+Paper Features Smoke"


def test_workflow_has_dispatch_and_schedule_triggers() -> None:
    triggers = _trigger_section(_workflow())

    assert "workflow_dispatch" in triggers

    schedule = triggers.get("schedule")
    assert isinstance(schedule, list)
    assert len(schedule) >= 1
    assert any(isinstance(entry, dict) and "cron" in entry for entry in schedule)


def test_workflow_gate_var_scheduling_and_dispatch_in_source() -> None:
    text = _workflow_text()
    assert "vars.PT_PRJ_FEATURES_SMOKE_ENABLED" in text
    assert "PT_PRJ_FEATURES_SMOKE_ENABLED" in text
    assert "workflow_dispatch" in text


def test_workflow_permissions_are_read_only_contents() -> None:
    data = _workflow()
    permissions = data.get("permissions")

    assert permissions != "write-all"
    assert isinstance(permissions, dict)
    assert permissions.get("contents") == "read"

    forbidden_write_scopes = (
        "actions",
        "checks",
        "deployments",
        "issues",
        "packages",
        "pull-requests",
        "repository-projects",
        "security-events",
        "statuses",
    )
    for scope in forbidden_write_scopes:
        assert permissions.get(scope) != "write"


def test_workflow_has_non_writing_contents_permissions_only() -> None:
    text = _workflow_text()
    lowered = text.lower()
    assert "contents: write" not in lowered


def test_workflow_dispatch_boolean_like_inputs_default_false() -> None:
    wd = _trigger_section(_workflow()).get("workflow_dispatch")
    assert isinstance(wd, dict)
    inputs = wd.get("inputs")
    assert isinstance(inputs, dict)

    bool_like_keys = (
        "enabled",
        "armed",
        "confirm_present",
        "allow_double_play",
        "allow_dynamic_leverage",
    )
    for key in bool_like_keys:
        spec = inputs.get(key)
        assert isinstance(spec, dict), key
        assert spec.get("default") == "false", key


def test_workflow_has_cancel_in_progress_concurrency() -> None:
    data = _workflow()
    conc = data.get("concurrency")
    assert isinstance(conc, dict)
    assert conc.get("cancel-in-progress") is True


def test_workflow_does_not_reference_github_secrets() -> None:
    assert "${{ secrets." not in _workflow_text()


def test_workflow_run_surface_is_prj_smoke_script_only() -> None:
    assert "./scripts/ci/prj_features_smoke_and_evidence.sh" in _workflow_text()


def test_workflow_avoids_obvious_live_order_execution_provider_terms() -> None:
    lowered = _workflow_text().lower()

    forbidden = (
        "live_authorization",
        "place_order",
        "submit_order",
        "exchange_order",
        "testnet_order",
        "${{ secrets.",
        "armed=true",
        "live_enabled=true",
        "confirm_token_env",
    )

    for term in forbidden:
        assert term not in lowered


def test_workflow_avoids_peak_trade_live_literal_true() -> None:
    lowered = _workflow_text().lower()
    assert "peak_trade_live_enabled: true" not in lowered
    assert "peak_trade_live_armed: true" not in lowered


def test_workflow_jobs_have_reasonable_timeouts() -> None:
    jobs = _jobs(_workflow())
    assert len(jobs) >= 1
    for job_body in jobs.values():
        assert isinstance(job_body, dict)
        timeout = job_body.get("timeout-minutes")
        assert isinstance(timeout, int)
        assert 1 <= timeout <= 180


def test_workflow_uploads_smoke_artifacts_without_readiness_claim() -> None:
    text = _workflow_text()

    assert "actions/upload-artifact@v4" in text
    assert "out/ops/prj_smoke" in text
    assert "out/ops/evidence_packs" in text

    lowered = text.lower()
    assert "futures_ready" not in lowered
    assert "live_ready" not in lowered
    assert "gate_passed" not in lowered
