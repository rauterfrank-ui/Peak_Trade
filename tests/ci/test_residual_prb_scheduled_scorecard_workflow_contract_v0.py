"""Static YAML contract for the five active scheduled PRB scorecard workflows.

Parses workflow YAML under `.github/workflows/` as UTF-8 text only. Never
dispatches workflows, never calls GitHub APIs, never reads secret values or
credential files, and never touches runtime, scheduler, exchange, or order
execution paths.

Non-authorizing visibility guard only — no workflow execution authority.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest

yaml = pytest.importorskip("yaml")

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_ROOT = REPO_ROOT / ".github" / "workflows"
VARIABLE_GATES_DOC = REPO_ROOT / "docs" / "ops" / "CI_SCHEDULED_WORKFLOW_VARIABLE_GATES.md"
CI_AUDIT_DOC = REPO_ROOT / "docs" / "ops" / "CI_AUDIT_KNOWN_ISSUES.md"

PRB_SCHEDULED_WORKFLOWS: dict[str, dict[str, str | bool]] = {
    "PRBC": {
        "workflow_file": "prbc-stability-gate.yml",
        "expected_cron": "57 2 * * *",
        "scorecard_script": "scripts/ci/stability_gate.py",
        "dispatch_has_inputs": False,
    },
    "PRBD": {
        "workflow_file": "prbd-live-readiness-scorecard.yml",
        "expected_cron": "7 3 * * *",
        "scorecard_script": "scripts/ci/live_readiness_scorecard.py",
        "dispatch_has_inputs": False,
    },
    "PRBE": {
        "workflow_file": "prbe-shadow-testnet-scorecard.yml",
        "expected_cron": "29 2 * * *",
        "scorecard_script": "scripts/ci/shadow_testnet_readiness_scorecard.py",
        "dispatch_has_inputs": False,
    },
    "PRBG": {
        "workflow_file": "prbg-execution-evidence.yml",
        "expected_cron": "19 2 * * *",
        "scorecard_script": "scripts/ci/execution_evidence_producer.py",
        "dispatch_has_inputs": True,
    },
    "PRBI": {
        "workflow_file": "prbi-live-pilot-scorecard.yml",
        "expected_cron": "39 2 * * *",
        "scorecard_script": "scripts/ci/live_pilot_scorecard.py",
        "dispatch_has_inputs": False,
    },
}

PRB_SECTION_HEADING = "## Residual PRB scheduled scorecard YAML contract v0"
GH_SCHEDULE_GOVERNANCE_HEADING = "## GH Schedule Governance Minimal RC v0"
PRB_DRIFT_GUARD_PACKAGE_MARKER = (
    "RESIDUAL_PRB_SCHEDULED_SCORECARD_DOCS_DRIFT_GUARD_IMPLEMENTED=true"
)
PRB_SCHEDULED_POSTURE_MARKER = "PRB_SCHEDULED_WORKFLOWS_POSTURE_CONFIRMED=true"
CI_AUDIT_PRB_ALIGNED_MARKER = "CI_AUDIT_PRB_SCHEDULED_POSTURE_ALIGNED=true"
VARIABLE_GATES_PRB_ALIGNED_MARKER = "VARIABLE_GATES_PRB_SCHEDULED_POSTURE_ALIGNED=true"
PRB_SCHEDULED_COUNT_5_MARKER = "PRB_SCHEDULED_COUNT_5_CONFIRMED=true"
GH_CI_MANUAL_ONLY_COUNT_8_MARKER = "GH_CI_MANUAL_ONLY_COUNT_8_PRESERVED=true"
GH_CI_DRIFT_GUARD_MARKER = "GH_CI_SCHEDULE_MANUAL_ONLY_DOCS_DRIFT_GUARD_IMPLEMENTED=true"
CANONICAL_RESIDUAL_ACTIVE_COUNT_LINE = "RESIDUAL_ACTIVE_SCHEDULE_COUNT=5"
CANONICAL_MANUAL_ONLY_COUNT_LINE = "RESIDUAL_MANUAL_ONLY_RESIDUAL_COUNT=8"
STALE_RESIDUAL_ACTIVE_COUNT_LINE = "RESIDUAL_ACTIVE_SCHEDULE_COUNT=6"
STALE_MANUAL_ONLY_COUNT_LINE = "RESIDUAL_MANUAL_ONLY_RESIDUAL_COUNT=7"

GH001_MANUAL_ONLY_FORMER_RESIDUAL = frozenset(
    {
        "ci.yml",
        "pro-prk-nightly-selfcheck.yml",
        "real-market-forward-evidence-smoke.yml",
        "audit.yml",
        "pru-required-checks-drift-detector.yml",
        "prcc-aws-export-smoke.yml",
        "prk-prj-status-report.yml",
        "prbj-testnet-exec-events.yml",
    }
)

_SECRETS_TOKEN_RE = re.compile(r"\$\{\{\s*secrets\.([A-Za-z0-9_]+)\s*\}\}")
_FORBIDDEN_PROMOTION_TOKENS = ("live_ready", "futures_ready", "gate_passed")
_FORBIDDEN_BRANCH_PROTECTION_TOKENS = (
    "branch-protection",
    "branch_protection",
    "updatebranchprotection",
    "required-checks",
    "required_checks",
)
_FORBIDDEN_RUNTIME_EXCHANGE_TOKENS = (
    "kraken",
    "testnet_api",
    "place_order",
    "cancel_order",
    "credentials.json",
    "operator.env",
)


def _workflow_path(prb_id: str) -> Path:
    spec = PRB_SCHEDULED_WORKFLOWS[prb_id]
    return WORKFLOW_ROOT / str(spec["workflow_file"])


def _load_workflow(prb_id: str) -> dict[str, Any]:
    path = _workflow_path(prb_id)
    assert path.is_file(), f"missing workflow file for {prb_id}: {path}"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def _workflow_text(prb_id: str) -> str:
    return _workflow_path(prb_id).read_text(encoding="utf-8")


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


def _schedule_cron_entries(triggers: dict[str, Any]) -> list[str]:
    schedule = triggers.get("schedule")
    assert schedule is not None, "schedule trigger missing"
    assert isinstance(schedule, list) and schedule, "schedule must be non-empty list"
    crons: list[str] = []
    for entry in schedule:
        assert isinstance(entry, dict), "schedule entry must be mapping"
        cron = entry.get("cron")
        assert isinstance(cron, str) and cron.strip(), "schedule cron must be non-empty string"
        crons.append(cron.strip())
    return crons


def _secret_names_in_text(text: str) -> set[str]:
    return set(_SECRETS_TOKEN_RE.findall(text))


def _prb_section(text: str) -> str:
    start = text.find(PRB_SECTION_HEADING)
    assert start != -1, f"missing {PRB_SECTION_HEADING}"
    end = text.find("\n## ", start + len(PRB_SECTION_HEADING))
    return text[start:] if end == -1 else text[start:end]


def _prb_machine_block(section: str) -> str:
    fence = section.find("```text")
    assert fence != -1, "PRB section missing machine block"
    end = section.find("```", fence + 7)
    assert end != -1
    return section[fence:end]


def _gh_schedule_governance_machine_block(text: str) -> str:
    start = text.find(GH_SCHEDULE_GOVERNANCE_HEADING)
    assert start != -1
    fence = text.find("```text", start)
    assert fence != -1
    end = text.find("```", fence + 7)
    assert end != -1
    return text[fence:end]


def _scheduled_workflow_files() -> frozenset[str]:
    return frozenset(str(spec["workflow_file"]) for spec in PRB_SCHEDULED_WORKFLOWS.values())


@pytest.mark.parametrize("prb_id", sorted(PRB_SCHEDULED_WORKFLOWS))
def test_prb_workflow_exists_parseable_and_has_active_schedule(prb_id: str) -> None:
    data = _load_workflow(prb_id)
    triggers = _trigger_section(data)
    crons = _schedule_cron_entries(triggers)
    expected_cron = str(PRB_SCHEDULED_WORKFLOWS[prb_id]["expected_cron"])
    assert expected_cron in crons

    text = _workflow_text(prb_id)
    assert re.search(r"^\s*schedule\s*:", text, re.MULTILINE), (
        "schedule block must be active in YAML"
    )
    assert not re.search(r"^\s*#\s*schedule\s*:", text, re.MULTILINE), (
        "schedule must not be commented out"
    )


@pytest.mark.parametrize("prb_id", sorted(PRB_SCHEDULED_WORKFLOWS))
def test_prb_workflow_dispatch_contract(prb_id: str) -> None:
    triggers = _trigger_section(_load_workflow(prb_id))
    assert "workflow_dispatch" in triggers

    dispatch = triggers["workflow_dispatch"]
    has_inputs = bool(PRB_SCHEDULED_WORKFLOWS[prb_id]["dispatch_has_inputs"])
    if has_inputs:
        assert isinstance(dispatch, dict)
        inputs = dispatch.get("inputs")
        assert isinstance(inputs, dict)
        assert "mock_profile" in inputs
        assert "input_path" in inputs
    else:
        assert dispatch == {} or dispatch is None


@pytest.mark.parametrize("prb_id", sorted(PRB_SCHEDULED_WORKFLOWS))
def test_prb_workflow_permissions_read_only(prb_id: str) -> None:
    data = _load_workflow(prb_id)
    permissions = data.get("permissions")
    assert permissions != "write-all"
    assert isinstance(permissions, dict)
    assert permissions.get("actions") == "read"
    assert permissions.get("contents") == "read"
    assert set(permissions.keys()) <= {"actions", "contents"}


@pytest.mark.parametrize("prb_id", sorted(PRB_SCHEDULED_WORKFLOWS))
def test_prb_workflow_has_cancel_in_progress_concurrency(prb_id: str) -> None:
    conc = _load_workflow(prb_id).get("concurrency")
    assert isinstance(conc, dict)
    assert conc.get("cancel-in-progress") is True


@pytest.mark.parametrize("prb_id", sorted(PRB_SCHEDULED_WORKFLOWS))
def test_prb_workflow_job_timeouts_bounded(prb_id: str) -> None:
    for job_body in _jobs(_load_workflow(prb_id)).values():
        assert isinstance(job_body, dict)
        timeout = job_body.get("timeout-minutes")
        assert isinstance(timeout, int)
        assert 1 <= timeout <= 15


@pytest.mark.parametrize("prb_id", sorted(PRB_SCHEDULED_WORKFLOWS))
def test_prb_workflow_no_pull_request_target(prb_id: str) -> None:
    triggers = _trigger_section(_load_workflow(prb_id))
    assert "pull_request_target" not in triggers
    assert not re.search(r"^\s*pull_request_target\s*:", _workflow_text(prb_id), re.MULTILINE)


@pytest.mark.parametrize("prb_id", sorted(PRB_SCHEDULED_WORKFLOWS))
def test_prb_workflow_no_secrets_or_credential_dependencies(prb_id: str) -> None:
    text = _workflow_text(prb_id)
    assert not _secret_names_in_text(text)
    assert "secrets." not in text.lower()
    assert "${{ github.token }}" in text or "GH_TOKEN: ${{ github.token }}" in text


@pytest.mark.parametrize("prb_id", sorted(PRB_SCHEDULED_WORKFLOWS))
def test_prb_workflow_scorecard_script_reference_stable(prb_id: str) -> None:
    script = str(PRB_SCHEDULED_WORKFLOWS[prb_id]["scorecard_script"])
    assert script in _workflow_text(prb_id)


@pytest.mark.parametrize("prb_id", sorted(PRB_SCHEDULED_WORKFLOWS))
def test_prb_workflow_avoids_promotion_and_branch_protection_tokens(prb_id: str) -> None:
    lowered = _workflow_text(prb_id).lower()
    for token in _FORBIDDEN_PROMOTION_TOKENS:
        assert token not in lowered
    for token in _FORBIDDEN_BRANCH_PROTECTION_TOKENS:
        assert token not in lowered


@pytest.mark.parametrize("prb_id", sorted(PRB_SCHEDULED_WORKFLOWS))
def test_prb_workflow_avoids_live_runtime_exchange_order_credential_steps(prb_id: str) -> None:
    lowered = _workflow_text(prb_id).lower()
    for token in _FORBIDDEN_RUNTIME_EXCHANGE_TOKENS:
        assert token not in lowered


@pytest.mark.parametrize("prb_id", sorted(PRB_SCHEDULED_WORKFLOWS))
def test_prb_workflow_artifact_retention_bounded(prb_id: str) -> None:
    text = _workflow_text(prb_id)
    if "retention-days:" not in text:
        pytest.skip("no upload-artifact retention in workflow")
    for match in re.finditer(r"retention-days:\s*(\d+)", text):
        assert int(match.group(1)) <= 14


def test_prbd_workflow_accepts_prk_schedule_or_dispatch_events() -> None:
    text = _workflow_text("PRBD")
    assert "prk-prj-status-report.yml" in text
    assert '.event=="schedule" or .event=="workflow_dispatch"' in text
    assert 'and .event=="schedule")' not in text


def test_prbg_workflow_dispatch_inputs_and_producer_script() -> None:
    text = _workflow_text("PRBG")
    assert "scripts/ci/execution_evidence_producer.py" in text
    triggers = _trigger_section(_load_workflow("PRBG"))
    dispatch = triggers["workflow_dispatch"]
    assert isinstance(dispatch, dict)
    inputs = dispatch.get("inputs")
    assert isinstance(inputs, dict)
    assert set(inputs) >= {"mock_profile", "input_path"}


def test_prb_scheduled_workflow_inventory_count() -> None:
    assert len(PRB_SCHEDULED_WORKFLOWS) == 5


def test_docs_owner_crosslinks_residual_prb_contract_test() -> None:
    test_path = "tests/ci/test_residual_prb_scheduled_scorecard_workflow_contract_v0.py"
    gates = VARIABLE_GATES_DOC.read_text(encoding="utf-8")
    audit = CI_AUDIT_DOC.read_text(encoding="utf-8")
    assert test_path in gates
    assert test_path in audit
    for prb_id in PRB_SCHEDULED_WORKFLOWS:
        assert str(PRB_SCHEDULED_WORKFLOWS[prb_id]["workflow_file"]) in gates


def test_prb_docs_drift_guard_package_marker_v0() -> None:
    assert PRB_DRIFT_GUARD_PACKAGE_MARKER in Path(__file__).read_text(encoding="utf-8")


@pytest.mark.parametrize("doc_path", [VARIABLE_GATES_DOC, CI_AUDIT_DOC])
def test_prb_scheduled_cron_table_matches_workflow_inventory(doc_path: Path) -> None:
    """Docs cron table must match PRB_SCHEDULED_WORKFLOWS constants."""
    text = doc_path.read_text(encoding="utf-8")
    for spec in PRB_SCHEDULED_WORKFLOWS.values():
        workflow_file = str(spec["workflow_file"])
        expected_cron = str(spec["expected_cron"])
        scorecard_script = str(spec["scorecard_script"])
        assert workflow_file in text
        assert expected_cron in text
        assert scorecard_script in text


@pytest.mark.parametrize("doc_path", [VARIABLE_GATES_DOC, CI_AUDIT_DOC])
def test_prb_docs_machine_block_markers_aligned(doc_path: Path) -> None:
    text = doc_path.read_text(encoding="utf-8")
    if doc_path == VARIABLE_GATES_DOC:
        block = _prb_machine_block(_prb_section(text))
    else:
        block = _gh_schedule_governance_machine_block(text)
    for marker in (
        PRB_DRIFT_GUARD_PACKAGE_MARKER,
        PRB_SCHEDULED_POSTURE_MARKER,
        CI_AUDIT_PRB_ALIGNED_MARKER,
        VARIABLE_GATES_PRB_ALIGNED_MARKER,
        PRB_SCHEDULED_COUNT_5_MARKER,
        GH_CI_MANUAL_ONLY_COUNT_8_MARKER,
        CANONICAL_RESIDUAL_ACTIVE_COUNT_LINE,
        CANONICAL_MANUAL_ONLY_COUNT_LINE,
        GH_CI_DRIFT_GUARD_MARKER,
    ):
        assert marker in block, f"missing {marker} in {doc_path.name}"
    assert STALE_RESIDUAL_ACTIVE_COUNT_LINE not in block
    assert STALE_MANUAL_ONLY_COUNT_LINE not in block


def test_prb_scheduled_posture_not_mixed_with_gh_ci_manual_only_inventory() -> None:
    """PRB scheduled chain must stay separate from the 8 manual-only GH-CI side."""
    gates_section = _prb_section(VARIABLE_GATES_DOC.read_text(encoding="utf-8"))
    audit = CI_AUDIT_DOC.read_text(encoding="utf-8")
    scheduled_files = _scheduled_workflow_files()
    for manual_only in GH001_MANUAL_ONLY_FORMER_RESIDUAL:
        assert manual_only not in scheduled_files
        assert f"| `{manual_only}` |" not in gates_section
        assert f"| `{manual_only}` |" not in audit
    for workflow_file in scheduled_files:
        assert workflow_file not in GH001_MANUAL_ONLY_FORMER_RESIDUAL


@pytest.mark.parametrize("prb_id", sorted(PRB_SCHEDULED_WORKFLOWS))
def test_prb_yaml_implemented_posture_requires_active_schedule_not_manual_only(
    prb_id: str,
) -> None:
    """Drift guard confirms YAML still has active schedule — no doc-only manual-only flip."""
    workflow_file = str(PRB_SCHEDULED_WORKFLOWS[prb_id]["workflow_file"])
    assert workflow_file not in GH001_MANUAL_ONLY_FORMER_RESIDUAL
    text = _workflow_text(prb_id)
    assert re.search(r"^\s*schedule\s*:", text, re.MULTILINE)
    assert "workflow_dispatch" in text
