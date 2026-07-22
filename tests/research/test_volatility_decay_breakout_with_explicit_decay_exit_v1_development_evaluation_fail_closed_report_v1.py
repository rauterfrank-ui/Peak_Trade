"""Pre-execution evidence-surface contract for VDBX development evaluation — terminal FAIL_CLOSED."""

from __future__ import annotations

import json
from pathlib import Path

from src.research.volatility_decay_breakout_with_explicit_decay_exit_v1_development_evaluation_v1.constants_v1 import (
    EVIDENCE_REL_PATH,
    HYPOTHESIS_ID,
)
from src.research.volatility_decay_breakout_with_explicit_decay_exit_v1_development_evaluation_v1.guards_v1 import (
    read_run_counters,
)

REPO = Path(__file__).resolve().parents[2]
EVIDENCE = REPO / EVIDENCE_REL_PATH
README = EVIDENCE / "README.md"
SUMMARY = EVIDENCE / "summary.json"
CLAIM = EVIDENCE / "run_slot_claim.json"
REGISTRY = EVIDENCE / "registry.json"
FAIL = EVIDENCE / "fail_closed_report.json"


def test_terminal_unpairable_entry_fail_closed_consumed_run_slot() -> None:
    before = read_run_counters(REPO)
    assert README.is_file()
    assert SUMMARY.is_file()
    assert CLAIM.is_file()
    assert REGISTRY.is_file()
    assert FAIL.is_file()
    text = README.read_text(encoding="utf-8")
    assert (
        "DOCS_TOKEN_EVALUATE_VOLATILITY_DECAY_BREAKOUT_WITH_EXPLICIT_DECAY_EXIT_DEVELOPMENT_V1"
        in text
    )
    assert "FAIL_CLOSED_UNPAIRABLE_ENTRY_NO_EXIT" in text
    assert (
        HYPOTHESIS_ID.split("_NON_")[0] in text or "VOLATILITY_DECAY_BREAKOUT_WITH_EXPLICIT" in text
    )
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    claim = json.loads(CLAIM.read_text(encoding="utf-8"))
    assert summary["status"] == "FAIL_CLOSED"
    assert "UNPAIRABLE_ENTRY_NO_EXIT" in summary["reason"]
    assert summary["budget_consumed"] is True
    assert summary["evaluation_executed"] is False
    assert summary["runner_started"] is True
    assert summary["holdout_accessed"] is False
    assert summary["retry_forbidden"] is True
    assert summary["second_pnl_truth_created"] is False
    assert claim["evaluation_run_count"] == 1
    assert claim["runner_start_count"] == 1
    assert claim["retry_forbidden"] is True
    assert before["contract_development_run_count"] == 1
    assert before["contract_runner_start_count"] == 1
    assert read_run_counters(REPO) == before


def test_binding_exit_semantics_forbid_evaluator_reconstruction() -> None:
    binding = json.loads(
        (
            REPO / "config/research/"
            "volatility_decay_breakout_with_explicit_decay_exit_v1_development_evaluation_"
            "entry_point_binding_v1.json"
        ).read_text(encoding="utf-8")
    )
    assert binding["development_evaluation_authorized"] is True
    assert binding["development_run_count"] == 1
    assert binding["runner_start_count"] == 1
    assert binding["productive_pnl_evaluator_duplicated"] is False
    assert (
        binding["exit_semantics"][
            "evaluator_side_reconstruction_of_missing_strategy_exits_forbidden"
        ]
        is True
    )
    assert "UNPAIRABLE_ENTRY_NO_EXIT" in binding["status"]
