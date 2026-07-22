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


def test_panel_boundary_not_materialized_fail_closed_report_preserves_slot() -> None:
    """Authorized attempt fail-closed before panel open and did not consume the durable slot."""
    payload = json.loads(REPORT.read_text(encoding="utf-8"))
    assert payload["status"] == "FAIL_CLOSED"
    assert (
        payload["verdict"] == "AUTHORIZED_PANEL_EXECUTION_BOUNDARY_NOT_MATERIALIZED_IN_THIS_SLICE"
    )
    assert payload["evaluation_executed"] is False
    assert payload["holdout_accessed"] is False
    assert payload["development_dataset_opened_in_process"] is False
    assert payload["run_count_before"] == 0
    assert payload["run_count_after"] == 0
    assert payload["runner_start_count_before"] == 0
    assert payload["runner_start_count_after"] == 0
    assert payload["summary_json_written"] is False
    assert payload["registry_json_written"] is False
    assert payload["run_slot_claim_written"] is False
    assert payload["retry_attempted"] is False
    assert payload["second_pnl_truth_created"] is False
    assert payload["productive_pnl_evaluator_invoked"] is False
    assert not SUMMARY.exists()
    assert not CLAIM.exists()
    assert not REGISTRY.exists()
    counters = read_run_counters(REPO)
    assert counters["contract_development_run_count"] == 0
    assert counters["contract_runner_start_count"] == 0
    assert counters["program_development_run_count"] == 0
    assert counters["program_runner_start_count"] == 0


def test_fail_closed_stdout_artifacts_match_report() -> None:
    stdout = json.loads((EVIDENCE / "run_stdout.txt").read_text(encoding="utf-8"))
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    assert stdout["status"] == "FAIL_CLOSED"
    assert stdout["reason"] == report["verdict"]
    assert stdout["runner_started"] is False
    assert stdout["evaluation_executed"] is False
    assert stdout["development_dataset_loaded"] is False
    assert stdout["holdout_accessed"] is False
    timing = (EVIDENCE / "run_timing.txt").read_text(encoding="utf-8")
    assert "exit_code=2" in timing
    assert "base_sha=1a86f3b979c523733a39e85490624c0721e366b7" in timing
