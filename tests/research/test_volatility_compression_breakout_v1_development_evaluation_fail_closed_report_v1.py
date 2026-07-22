"""Contract test for VCB v1 fail-closed development-evaluation evidence (no runner)."""

from __future__ import annotations

import json
from pathlib import Path

from src.research.volatility_compression_breakout_v1_development_evaluation_v1.guards_v1 import (
    read_run_counters,
)

REPO = Path(__file__).resolve().parents[2]
EVIDENCE = REPO / "docs/evidence/evaluate_volatility_compression_breakout_development_v1"
REPORT = EVIDENCE / "fail_closed_report.json"


def test_fail_closed_report_present_and_non_consuming() -> None:
    before = read_run_counters(REPO)
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
    assert not (EVIDENCE / "summary.json").exists()
    assert not (EVIDENCE / "run_slot_claim.json").exists()
    assert read_run_counters(REPO) == before
    assert before["contract_development_run_count"] == 0
    assert before["contract_runner_start_count"] == 0
