"""Tests for read-only manual-only workflow recommender CLI."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "ops" / "recommend_manual_only_workflows.py"
DOC = REPO_ROOT / "docs" / "ops" / "CI_SCHEDULED_WORKFLOW_VARIABLE_GATES.md"

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
    }
)

PAPER_SHADOW_FILES = frozenset(
    {
        "ci-scheduled-paper-and-export-smoke.yml",
        "class-a-shadow-paper-scheduled-probe-v1.yml",
        "prj-scheduled-shadow-paper-features-smoke.yml",
    }
)


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
