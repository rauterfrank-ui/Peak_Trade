"""Contract test for VCB v1 fail-closed development-evaluation evidence surfaces."""

from __future__ import annotations

import json
from pathlib import Path

from src.research.volatility_compression_breakout_v1_development_evaluation_v1.guards_v1 import (
    read_run_counters,
)

REPO = Path(__file__).resolve().parents[2]
EVIDENCE = REPO / "docs/evidence/evaluate_volatility_compression_breakout_development_v1"
REPORT = EVIDENCE / "fail_closed_report.json"
SUMMARY = EVIDENCE / "summary.json"
CLAIM = EVIDENCE / "run_slot_claim.json"


def test_historical_unbound_evaluator_fail_closed_report_preserved() -> None:
    """Prior unbound-evaluator attempt remains archival and did not itself consume the slot."""
    payload = json.loads(REPORT.read_text(encoding="utf-8"))
    assert payload["status"] == "FAIL_CLOSED"
    assert payload["verdict"] == "PRODUCTIVE_EXIT_PNL_EVALUATOR_NOT_BOUND"
    assert payload["evaluation_executed"] is False
    assert payload["holdout_accessed"] is False
    assert payload["run_count_after"] == 0
    assert payload["runner_start_count_after"] == 0
    assert payload["summary_json_written"] is False
    assert payload["registry_json_written"] is False
    assert payload["run_slot_claim_written"] is False


def test_terminal_overflow_fail_closed_consumed_run_slot() -> None:
    before = read_run_counters(REPO)
    assert SUMMARY.is_file()
    assert CLAIM.is_file()
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
