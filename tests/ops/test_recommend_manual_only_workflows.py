"""Tests for read-only manual-only workflow recommender CLI."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.ops.recommend_manual_only_workflows import (
    RESIDUAL_SCHEDULE_WORKFLOW_FILES,
    WORKFLOWS_DIR,
    _parse_workflow_file,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "ops" / "recommend_manual_only_workflows.py"
DOC = REPO_ROOT / "docs" / "ops" / "CI_SCHEDULED_WORKFLOW_VARIABLE_GATES.md"
CI_AUDIT = REPO_ROOT / "docs" / "ops" / "CI_AUDIT_KNOWN_ISSUES.md"
OPDS1_HEADING = "## Post-Release Operator Package Decision Contract v0"

EXPECTED_INTENTS = frozenset(
    {
        "paper_shadow_evidence",
        "health_suite",
        "market_info_daily",
        "ops_hygiene",
        "security_audit",
        "docs_hygiene",
        "paper_test_evidence",
        "all",
        "residual_ci_ops",
        "residual_scorecard_chain",
        "residual_data_smoke",
        "residual_all",
    }
)

RESIDUAL_SCHEDULE_FILES = frozenset(
    {
        "audit.yml",
        "ci.yml",
        "prbc-stability-gate.yml",
        "prbd-live-readiness-scorecard.yml",
        "prbe-shadow-testnet-scorecard.yml",
        "prbg-execution-evidence.yml",
        "prbi-live-pilot-scorecard.yml",
        "prbj-testnet-exec-events.yml",
        "prcc-aws-export-smoke.yml",
        "prk-prj-status-report.yml",
        "pro-prk-nightly-selfcheck.yml",
        "pru-required-checks-drift-detector.yml",
        "real-market-forward-evidence-smoke.yml",
    }
)

# SLICE-GH-001: schedule removed; workflow_dispatch retained (recommender inventory unchanged).
GH001_MANUAL_ONLY_FORMER_RESIDUAL = frozenset({"pro-prk-nightly-selfcheck.yml"})
PRO_PRK_NIGHTLY_SELFCHECK_WORKFLOW = (
    REPO_ROOT / ".github" / "workflows" / "pro-prk-nightly-selfcheck.yml"
)

RESIDUAL_INVENTORY_COUNT = 13
RESIDUAL_ACTIVE_SCHEDULE_COUNT = 12
RESIDUAL_MANUAL_ONLY_COUNT = 1
RESIDUAL_ALL_INTENT_MISLEADING_PHRASE = "13 workflows with active schedule"

RESIDUAL_CI_OPS_FILES = frozenset({"ci.yml", "audit.yml", "pru-required-checks-drift-detector.yml"})

PAPER_SHADOW_FILES = frozenset(
    {
        "ci-scheduled-paper-and-export-smoke.yml",
        "class-a-shadow-paper-scheduled-probe-v1.yml",
        "prj-scheduled-shadow-paper-features-smoke.yml",
    }
)

RESIDUAL_ACTIVE_SCHEDULE_ALLOWLIST = (
    RESIDUAL_SCHEDULE_WORKFLOW_FILES - GH001_MANUAL_ONLY_FORMER_RESIDUAL
)


def _all_workflow_filenames() -> frozenset[str]:
    names: list[str] = []
    for pattern in ("*.yml", "*.yaml"):
        names.extend(p.name for p in WORKFLOWS_DIR.glob(pattern))
    return frozenset(names)


def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )


def test_list_intents_includes_all_expected() -> None:
    proc = _run_cli("--list-intents")
    assert proc.returncode == 0, proc.stderr
    for intent in EXPECTED_INTENTS:
        assert intent in proc.stdout


def test_paper_shadow_evidence_recommends_paper_shadow_workflows() -> None:
    proc = _run_cli("--intent", "paper_shadow_evidence", "--include-commands")
    assert proc.returncode == 0, proc.stderr
    out = proc.stdout
    for filename in PAPER_SHADOW_FILES:
        assert filename in out
    assert "gh workflow run" in out
    assert "Operator-GO" in out or "operator-GO" in out
    assert "does not run workflows" in out or "READ-ONLY" in out


def test_market_info_daily_includes_ai_cost_hint() -> None:
    proc = _run_cli("--intent", "market_info_daily", "--include-commands")
    assert proc.returncode == 0, proc.stderr
    lowered = proc.stdout.lower()
    assert "infostream" in lowered or "market" in lowered
    assert "ai" in lowered or "openai" in lowered or "skip_ai" in lowered


def test_json_mode_valid_and_contains_guard() -> None:
    proc = _run_cli("--intent", "market_info_daily", "--json", "--include-commands")
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["schedule_reactivation"] is False
    assert payload["executes_workflows"] is False
    assert payload["guard"]
    assert payload["recommendations"]


def test_doc_manual_only_section_no_auto_cron_reactivation() -> None:
    text = DOC.read_text(encoding="utf-8")
    assert "Manual-only workflow recommender after PR #3896" in text
    assert "does not" in text.lower() or "Does **not**" in text
    assert "separate PR" in text
    assert "operator-GO" in text or "Operator-GO" in text
    assert "separate PR" in text
    assert "Re-enabling cron" in text or "re-enabling cron" in text
    section_start = text.index("Manual-only workflow recommender after PR #3896")
    section = text[section_start : section_start + 2500].lower()
    assert "does **not**" in section or "does not" in section
    assert "re-enable" in section or "re-enabling" in section


@pytest.mark.parametrize("intent", ["paper_shadow_evidence", "health_suite"])
def test_recommender_does_not_invoke_gh(intent: str) -> None:
    """CLI must only print gh commands; subprocess list should be stdlib-only."""
    proc = _run_cli("--intent", intent, "--include-commands")
    assert proc.returncode == 0
    assert "gh workflow run" in proc.stdout


def test_residual_all_intent_label_inventory_split_v0() -> None:
    proc = _run_cli("--list-intents")
    assert proc.returncode == 0, proc.stderr
    lowered = proc.stdout.lower()
    assert RESIDUAL_ALL_INTENT_MISLEADING_PHRASE not in lowered
    assert "13 inventory" in lowered
    assert "12 active schedule" in lowered
    assert "manual-only" in lowered

    proc_json = _run_cli("--list-intents", "--json")
    assert proc_json.returncode == 0, proc_json.stderr
    payload = json.loads(proc_json.stdout)
    row = next(r for r in payload["intents"] if r["id"] == "residual_all")
    label = row["label"].lower()
    assert RESIDUAL_ALL_INTENT_MISLEADING_PHRASE not in label
    assert "13 inventory" in label
    assert "12 active schedule" in label
    assert "manual-only" in label
    assert payload["residual_schedule_count"] == RESIDUAL_INVENTORY_COUNT


def test_residual_all_json_covers_thirteen_without_duplicates() -> None:
    proc = _run_cli("--intent", "residual_all", "--json")
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    files = [r["workflow_file"].split("/")[-1] for r in payload["recommendations"]]
    assert len(files) == len(RESIDUAL_SCHEDULE_FILES)
    assert frozenset(files) == RESIDUAL_SCHEDULE_FILES
    assert payload["schedule_reactivation"] is False
    assert payload["executes_workflows"] is False
    assert payload["workflow_dispatch_executed"] is False
    active_count = 0
    manual_only_count = 0
    for rec in payload["recommendations"]:
        fname = rec["workflow_file"].split("/")[-1]
        assert rec["residual_scheduled_workflow"] is True
        if fname in GH001_MANUAL_ONLY_FORMER_RESIDUAL:
            assert rec["has_active_schedule"] is False
            manual_only_count += 1
        else:
            assert rec["has_active_schedule"] is True
            assert "warning" in rec
            active_count += 1
    assert len(files) == RESIDUAL_INVENTORY_COUNT
    assert active_count == RESIDUAL_ACTIVE_SCHEDULE_COUNT
    assert manual_only_count == RESIDUAL_MANUAL_ONLY_COUNT


def test_pro_prk_nightly_selfcheck_manual_only_yaml_shape() -> None:
    """GH-001: cron removed; dispatch retained."""
    text = PRO_PRK_NIGHTLY_SELFCHECK_WORKFLOW.read_text(encoding="utf-8")
    assert "workflow_dispatch" in text
    assert "schedule:" not in text


def test_residual_ci_ops_intent_count() -> None:
    proc = _run_cli("--intent", "residual_ci_ops", "--json")
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    files = {r["workflow_file"].split("/")[-1] for r in payload["recommendations"]}
    assert files == RESIDUAL_CI_OPS_FILES


def test_residual_scorecard_chain_includes_prbc_and_prk() -> None:
    proc = _run_cli("--intent", "residual_scorecard_chain", "--include-commands")
    assert proc.returncode == 0, proc.stderr
    for name in (
        "prbc-stability-gate.yml",
        "prk-prj-status-report.yml",
        "prbj-testnet-exec-events.yml",
    ):
        assert name in proc.stdout


def test_residual_data_smoke_single_workflow() -> None:
    proc = _run_cli("--intent", "residual_data_smoke", "--json")
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert len(payload["recommendations"]) == 1
    assert payload["recommendations"][0]["workflow_file"].endswith(
        "real-market-forward-evidence-smoke.yml"
    )


def test_residual_intents_listed_with_manual_only_intents() -> None:
    proc = _run_cli("--list-intents", "--json")
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    intent_ids = {row["id"] for row in payload["intents"]}
    for intent in (
        "residual_all",
        "residual_ci_ops",
        "residual_scorecard_chain",
        "residual_data_smoke",
    ):
        assert intent in intent_ids
    assert payload["residual_schedule_count"] == 13


def test_ci_audit_opds1_lists_manual_only_recommender_owner_v0() -> None:
    text = CI_AUDIT.read_text(encoding="utf-8")
    start = text.find(OPDS1_HEADING)
    assert start != -1
    end = text.find("## Master V2", start)
    section = text[start:end]
    assert "test_recommend_manual_only_workflows.py" in section
    assert "schedule_reactivation" not in section.lower() or "does not" in section.lower()


@pytest.mark.parametrize(
    "intent",
    [
        "paper_shadow_evidence",
        "health_suite",
        "market_info_daily",
        "ops_hygiene",
        "residual_all",
        "residual_ci_ops",
    ],
)
def test_recommender_json_never_sets_schedule_reactivation_opds1_guard(intent: str) -> None:
    """OPDS1: recommender must not auto-force micro-churn via schedule reactivation."""
    proc = _run_cli("--intent", intent, "--json")
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["schedule_reactivation"] is False
    assert payload["executes_workflows"] is False
    guard = payload.get("guard", "")
    lowered = guard.lower()
    assert "micro-churn" not in lowered
    assert "next pr" not in lowered or "does not" in lowered or "read-only" in lowered


def test_recommender_opds1_ci_audit_crosslink_reciprocal_v0() -> None:
    audit = CI_AUDIT.read_text(encoding="utf-8")
    assert "test_recommend_manual_only_workflows.py" in audit
    owner = Path(__file__).read_text(encoding="utf-8")
    assert "test_ci_audit_opds1_lists_manual_only_recommender_owner_v0" in owner


def test_residual_schedule_files_match_script_inventory_v0() -> None:
    """SSOT: test mirror must match recommender RESIDUAL_SCHEDULE_WORKFLOW_FILES."""
    assert RESIDUAL_SCHEDULE_FILES == frozenset(RESIDUAL_SCHEDULE_WORKFLOW_FILES)


def test_github_workflows_active_schedule_allowlist_drift_guard_v0() -> None:
    """Repo-wide: only GH residual allowlist workflows may have active on.schedule."""
    pytest.importorskip("yaml")
    on_disk = _all_workflow_filenames()
    missing_inventory = RESIDUAL_SCHEDULE_WORKFLOW_FILES - on_disk
    assert not missing_inventory, f"inventory workflow missing on disk: {sorted(missing_inventory)}"

    active: set[str] = set()
    for fname in sorted(on_disk):
        rec = _parse_workflow_file(fname)
        if rec.has_active_schedule:
            active.add(fname)

    allowlist = set(RESIDUAL_ACTIVE_SCHEDULE_ALLOWLIST)
    extra = active - allowlist
    missing_active = allowlist - active
    assert not extra, f"unexpected active schedule workflows: {sorted(extra)}"
    assert not missing_active, (
        f"allowlisted workflow lost active schedule (rename/remove?): {sorted(missing_active)}"
    )


def test_residual_active_schedule_allowlist_each_has_schedule_v0() -> None:
    """Each of the 12 residual cron workflows must still expose schedule in on block."""
    pytest.importorskip("yaml")
    for fname in sorted(RESIDUAL_ACTIVE_SCHEDULE_ALLOWLIST):
        rec = _parse_workflow_file(fname)
        assert rec.has_active_schedule, fname
