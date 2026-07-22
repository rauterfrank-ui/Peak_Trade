"""Contract test for VDB v1 fail-closed development-evaluation evidence surfaces."""

from __future__ import annotations

import json
from pathlib import Path

from src.research.volatility_decay_breakout_v1_development_evaluation_v1.guards_v1 import (
    read_run_counters,
)

REPO = Path(__file__).resolve().parents[2]
EVIDENCE = REPO / "docs/evidence/evaluate_volatility_decay_breakout_development_v1"
REPORT = EVIDENCE / "fail_closed_report.json"
SUMMARY = EVIDENCE / "summary.json"
CLAIM = EVIDENCE / "run_slot_claim.json"
REGISTRY = EVIDENCE / "registry.json"


def test_historical_panel_boundary_fail_closed_report_preserved() -> None:
    """Prior panel-boundary-not-materialized attempt remains archival and did not itself consume the slot."""
    payload = json.loads(REPORT.read_text(encoding="utf-8"))
    assert payload["status"] == "FAIL_CLOSED"
    assert (
        payload["verdict"] == "AUTHORIZED_PANEL_EXECUTION_BOUNDARY_NOT_MATERIALIZED_IN_THIS_SLICE"
    )
    assert payload["evaluation_executed"] is False
    assert payload["holdout_accessed"] is False
    assert payload["development_dataset_opened_in_process"] is False
    assert payload["run_count_after"] == 0
    assert payload["runner_start_count_after"] == 0
    assert payload["summary_json_written"] is False
    assert payload["registry_json_written"] is False
    assert payload["run_slot_claim_written"] is False
    assert payload["retry_attempted"] is False
    assert payload["second_pnl_truth_created"] is False
    assert payload["productive_pnl_evaluator_invoked"] is False


def test_terminal_productive_pnl_overflow_fail_closed_consumed_run_slot() -> None:
    before = read_run_counters(REPO)
    assert SUMMARY.is_file()
    assert CLAIM.is_file()
    assert REGISTRY.is_file()
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    claim = json.loads(CLAIM.read_text(encoding="utf-8"))
    assert summary["status"] == "FAIL_CLOSED"
    assert "OverflowError" in summary["reason"]
    assert summary["budget_consumed"] is True
    assert summary["evaluation_executed"] is False
    assert summary["runner_started"] is True
    assert summary["holdout_accessed"] is False
    assert summary["retry_forbidden"] is True
    assert claim["evaluation_run_count"] == 1
    assert claim["runner_start_count"] == 1
    assert claim["retry_forbidden"] is True
    assert before["contract_development_run_count"] == 1
    assert before["contract_runner_start_count"] == 1
    assert read_run_counters(REPO) == before


def test_terminal_stdout_matches_productive_pnl_overflow_fail_closed() -> None:
    stdout = json.loads((EVIDENCE / "run_stdout.txt").read_text(encoding="utf-8"))
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    assert stdout["status"] == "FAIL_CLOSED"
    assert stdout["reason"] == summary["reason"]
    assert stdout["evaluation_executed"] is False
    timing = (EVIDENCE / "run_timing.txt").read_text(encoding="utf-8")
    assert "start_utc=2026-07-22T16:22:43Z" in timing
    assert "end_utc=2026-07-22T16:23:05Z" in timing
