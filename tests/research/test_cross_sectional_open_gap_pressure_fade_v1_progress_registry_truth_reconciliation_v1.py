"""Progress-registry truth reconciliation for Open Gap Pressure Fade terminal state."""

from __future__ import annotations

import json
from pathlib import Path

from tests.ops.runbook_progress_registry_contract_helpers_v1 import read_registry

REPO = Path(__file__).resolve().parents[2]
PROGRAM = REPO / "config/research/cross_sectional_open_gap_pressure_fade_research_program_v1.json"
BACKLOG = REPO / "config/research/cross_sectional_open_gap_pressure_fade_hypothesis_backlog_v1.json"
BINDING = (
    REPO
    / "config/research/cross_sectional_open_gap_pressure_fade_v1_strategy_implementation_binding_v1.json"
)
SUMMARY = (
    REPO
    / "docs/evidence/evaluate_cross_sectional_open_gap_pressure_fade_development_v1/summary.json"
)
NEXT = (
    "NEW_DISTINCT_RESEARCH_PROGRAM_OR_FULL_CANONICAL_SYSTEM_BINDING_OR_OTHER_EVIDENCE_CLASS"
    "_REQUIRES_OPERATOR_RATIFICATION"
)
RECON_HEADING = (
    "### CROSS_SECTIONAL_OPEN_GAP_PRESSURE_FADE_V1_PROGRESS_REGISTRY_TRUTH_RECONCILIATION_V1"
)
IMPL_HEADING = "### CROSS_SECTIONAL_OPEN_GAP_PRESSURE_FADE_V1_STRATEGY_IMPLEMENTATION_ONLY_V1"
EVAL_HEADING = (
    "### CROSS_SECTIONAL_OPEN_GAP_PRESSURE_FADE_V1_BOUNDED_DEVELOPMENT_EVALUATION_EXECUTION_V1"
)
SECTION_SEP = "\n### "


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _recon_section(text: str) -> str:
    return text.split(RECON_HEADING, 1)[1].split(SECTION_SEP, 1)[0]


def test_progress_registry_records_terminal_open_gap_truth() -> None:
    text = read_registry()
    assert RECON_HEADING in text
    assert IMPL_HEADING in text
    assert EVAL_HEADING in text
    recon = _recon_section(text)
    assert "PR #5495 MERGED" in recon
    assert "PR #5496 MERGED" in recon
    assert "DEVELOPMENT_FAIL" in recon
    assert "DEVELOPMENT_RUN_COUNT=1" in recon
    assert "DEVELOPMENT_SLOT_CONSUMED=true" in recon
    assert NEXT in recon
    assert "no new hypothesis selected" in recon.lower()
    assert "Next admissible GO: separate implementation or bounded DEVELOPMENT" not in recon
    assert "DEVELOPMENT_RUN_COUNT=0" not in recon


def test_ssot_and_evidence_identifiers_match_registry_facts() -> None:
    program = _load(PROGRAM)
    backlog = _load(BACKLOG)
    binding = _load(BINDING)
    summary = _load(SUMMARY)

    assert program["strategy_implementation_present"] is True
    assert program["implementation_pr"] == 5495
    assert program["development_pr"] == 5496
    assert program["development_run_count"] == 1
    assert program["development_result"] == "DEVELOPMENT_FAIL"
    assert program["run_slot_consumed"] is True
    assert program["evaluation_authorized"] is False
    assert program["retry_allowed"] is False
    assert program["next_eligible"] == "NONE"
    assert program["next_canonical_step"] == NEXT
    assert program["status"] == "PROGRAM_CLOSED_NO_FURTHER_RESEARCH"
    assert (
        program["promotion_and_economic_gate_policy"]["economic_validity_offline_gate_pass"]
        is False
    )

    assert backlog["status"] == "LANE_CLOSED_NO_FURTHER_RESEARCH"
    assert backlog["development_run_count"] == 1
    assert backlog["next_eligible"] == "NONE"
    assert backlog["retry_allowed"] is False
    assert backlog["evaluation_authorized"] is False
    terminal = backlog["terminal_hypotheses"][0]
    assert terminal["implementation_pr"] == 5495
    assert terminal["development_pr"] == 5496
    assert terminal["status"] == "TERMINAL_FAIL"

    assert binding["development_run_count"] == 1
    assert binding["development_evaluation_executed"] is True
    assert binding["evaluation_authorized"] is False

    assert summary["development_result"] == "DEVELOPMENT_FAIL"
    assert summary["development_run_count_after"] == 1
    assert summary["holdout_accessed"] is False
    assert summary["retry_forbidden"] is True
    assert summary["promotion_eligible"] is False
    assert summary["economic_gate_open"] is False
    assert summary["hypothesis_id"] == (
        "CROSS_SECTIONAL_OPEN_GAP_PRESSURE_FADE_NON_BITCOIN_PERPETUALS_V1"
    )


def test_open_gap_is_not_next_implementation_candidate() -> None:
    program = _load(PROGRAM)
    backlog = _load(BACKLOG)
    assert program["next_eligible"] == "NONE"
    assert backlog["next_eligible"] == "NONE"
    assert program["implementation_authorized"] is False
    assert backlog["implementation_authorized"] is False
    text = read_registry()
    recon = _recon_section(text)
    assert "no new hypothesis selected" in recon.lower()
    assert "Open Gap Pressure Fade as next implementation" not in text
