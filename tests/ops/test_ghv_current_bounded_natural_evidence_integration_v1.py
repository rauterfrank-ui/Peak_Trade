"""GHV + bounded CURRENT Natural Evidence integration (offline forensic only)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.ghv_current_bounded_natural_evidence_forensic_adapter_v1 import (
    BOUNDED_DEFAULT_MAX_CYCLES,
    BOUNDED_DEFAULT_MAX_RUN_DURATION_SECONDS,
    CLASSIFICATION_FACT,
    COMBINED_REPORT_FILENAME,
    DISPOSITION_HOLD_CLOSED,
    GHV_AUTHORITY,
    WORK_PACKAGE_ID,
    build_bounded_natural_evidence_launcher_argv_v1,
    build_combined_bounded_natural_evidence_report_v1,
    detect_safety_violations_v1,
    explain_hold_closed_cycles_v1,
    materialize_ghv_forensic_artifacts_v1,
    persist_combined_report_v1,
)
from src.ops.full_core_live_path_composition_root_v1.pre_external_convergence_runtime_duration_transparency_v1 import (
    MAX_RUN_DURATION_SECONDS_SCOPE,
    build_pre_external_convergence_runtime_duration_transparency_v1,
    merge_duration_transparency_into_report_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _minimal_current_report(*, hold_cycles: int = 2) -> dict:
    summaries = [
        {"cycle_index": i, "s5_disposition": DISPOSITION_HOLD_CLOSED, "c1_venue_event_time": 1.0}
        for i in range(1, hold_cycles + 1)
    ]
    base = {
        "BASELINE_SHA": "82edee5d68843d61946eb4bd93c1d15d30fe8dac",
        "CYCLE_COUNT": hold_cycles,
        "S5_CYCLE_SUMMARIES": summaries,
        "NATURAL_ENTER_OBSERVED": "false",
        "PRE_EXTERNAL_REACHED": "false",
        "POST_COUNT": 0,
        "EXTERNAL_EFFECT_COUNT": 0,
        "PERMIT_CREATED": "false",
        "TERMINAL_DISPOSITION": DISPOSITION_HOLD_CLOSED,
    }
    duration = build_pre_external_convergence_runtime_duration_transparency_v1(
        launcher_monotonic_origin=0.0,
        preflight_monotonic_end=1.0,
        sequencer_elapsed_monotonic_seconds=10.0,
        post_sequencer_monotonic_end=11.0,
        report_monotonic_end=12.0,
    )
    return merge_duration_transparency_into_report_v1(base, duration)


def test_product_bounded_defaults_unchanged() -> None:
    assert BOUNDED_DEFAULT_MAX_CYCLES == 4
    assert BOUNDED_DEFAULT_MAX_RUN_DURATION_SECONDS == 180.0


def test_launcher_argv_includes_ghv_forensic_flags(tmp_path: Path) -> None:
    argv = build_bounded_natural_evidence_launcher_argv_v1(
        repo_root=REPO_ROOT,
        launcher_script=REPO_ROOT
        / "scripts/ops/run_current_productive_policy_governed_live_c1_pre_external_convergence_v1.py",
        evidence_root=tmp_path / "evidence",
        lane_state_root=tmp_path / "lane",
        productivity_root=tmp_path / "prod",
    )
    assert "--max-cycles" in argv and "4" in argv
    assert "--max-run-duration-seconds" in argv and "180.0" in argv
    assert "--enable-golden-happy-vector-forensic-observability-v1" in argv
    assert "--enable-ghv-pre-external-runtime-flight-recorder-v1" in argv


def test_hold_closed_explanation_fact_without_ghv_ledger(tmp_path: Path) -> None:
    report = _minimal_current_report(hold_cycles=2)
    (tmp_path / "PRE_EXTERNAL_CONVERGENCE_REPORT.json").write_text(
        json.dumps(report, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    explanations = explain_hold_closed_cycles_v1(
        cycle_summaries=report["S5_CYCLE_SUMMARIES"],
        evidence_root=tmp_path,
    )
    facts = [e for e in explanations if e.classification == CLASSIFICATION_FACT]
    assert len(facts) == 2
    assert all(e.s5_disposition == DISPOSITION_HOLD_CLOSED for e in facts)


def test_combined_report_offline_without_flight_record(tmp_path: Path) -> None:
    report = _minimal_current_report(hold_cycles=3)
    (tmp_path / "PRE_EXTERNAL_CONVERGENCE_REPORT.json").write_text(
        json.dumps(report, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    ghv = materialize_ghv_forensic_artifacts_v1(evidence_root=tmp_path)
    assert ghv.attempted is False
    assert ghv.status == "SKIPPED"

    combined = build_combined_bounded_natural_evidence_report_v1(
        evidence_root=tmp_path,
        repo_root=REPO_ROOT,
        runtime_started=False,
        runtime_completed=False,
        ghv=ghv,
        current_report=report,
    )
    assert combined["work_package"] == WORK_PACKAGE_ID
    assert combined["GHV_AUTHORITY"] == GHV_AUTHORITY
    assert combined["GHV_CAUSAL_CHAIN_STATUS"] == "GHV_SKIPPED_NO_FLIGHT_RECORD"
    assert combined["CYCLES_EXECUTED"] == 3
    assert combined["NATURAL_ENTER_OBSERVED"] is False
    assert combined["MAX_RUN_DURATION_SECONDS_SCOPE"] == MAX_RUN_DURATION_SECONDS_SCOPE
    assert combined["POST_COUNT"] == 0
    assert combined["SAFETY_VIOLATIONS"] == []
    path = persist_combined_report_v1(evidence_root=tmp_path, report=combined)
    assert path.name == COMBINED_REPORT_FILENAME


def test_safety_violation_detects_unexpected_post() -> None:
    violations = detect_safety_violations_v1({"POST_COUNT": 1, "EXTERNAL_EFFECT_COUNT": 0})
    assert "UNEXPECTED_POST_COUNT_GT_ZERO" in violations


@pytest.mark.skipif(
    not (
        REPO_ROOT / "evidence/research/k1_bounded_get_only_natural_enter_witness_v1/"
        "20261007T004808Z_witness_v1/bounded_run/PRE_EXTERNAL_CONVERGENCE_REPORT.json"
    ).is_file(),
    reason="K1 bounded witness evidence not present",
)
def test_combined_report_from_historical_k1_witness_readonly() -> None:
    evidence = (
        REPO_ROOT / "evidence/research/k1_bounded_get_only_natural_enter_witness_v1/"
        "20261007T004808Z_witness_v1/bounded_run"
    )
    ghv = materialize_ghv_forensic_artifacts_v1(evidence_root=evidence)
    combined = build_combined_bounded_natural_evidence_report_v1(
        evidence_root=evidence,
        repo_root=REPO_ROOT,
        runtime_started=True,
        runtime_completed=True,
        ghv=ghv,
    )
    assert combined["NATURAL_ENTER_OBSERVED"] is True
    assert combined["PRE_EXTERNAL_REACHED"] is True
