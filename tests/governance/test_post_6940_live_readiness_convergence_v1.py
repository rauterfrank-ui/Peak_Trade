"""Tests for post-6940 live-readiness convergence owner v1."""

from __future__ import annotations

import json
from pathlib import Path

from src.governance.post_6940_live_readiness_convergence_v1 import (
    DECISION_CONFIG,
    NORMATIVE_SPEC,
    WORKPACKAGE_ID,
    build_convergence_report_v1,
    prove_standing_external_effect_fail_closed_v1,
    readjudicate_historical_blockers_v1,
)

REPO = Path(__file__).resolve().parents[2]


def test_workpackage_and_decision_paths_exist() -> None:
    assert (REPO / NORMATIVE_SPEC).is_file()
    assert (REPO / DECISION_CONFIG).is_file()
    decision = json.loads((REPO / DECISION_CONFIG).read_text(encoding="utf-8"))
    assert decision["paper_status"] == "PARKED"
    assert decision["first_real_blocker"] == "EXTERNAL_EFFECT_AUTHORIZATION"


def test_standing_external_effect_flags_fail_closed() -> None:
    flags = prove_standing_external_effect_fail_closed_v1()
    assert flags["EXTERNAL_EFFECT_AUTHORIZED"] is False
    assert flags["POST_ALLOWED"] is False
    assert flags["REAL_VENUE_POST_ALLOWED"] is False


def test_convergence_report_identifies_external_effect_blocker() -> None:
    treasury = {
        "PRE_EXTERNAL_REACHED": True,
        "ALL_IMMEDIATE_MECHANICAL_CLOSURES_EXHAUSTED": True,
        "ADMISSION_RESULT": {"enter_live_status": "FAIL"},
        "EXECUTION_BRANCH_FIRST_UNCLOSED_EDGE": "intent_to_execution",
        "EXECUTION_BRANCH_BLOCKER_CLASS": "EXTERNAL_EFFECT_AUTHORITY",
        "FIRST_REAL_BLOCKER": "OWNER_GO_REQUIRED_FOR_VENUE_POST_AND_PRODUCTIVE_APPLY_PROMOTION",
    }
    report = build_convergence_report_v1(
        repo_root=REPO,
        baseline_sha="ad99257a7e0922192ca32d27f0acf029e9efae83",
        treasury_report=treasury,
        map_sha256="abc",
        atlas_sha256="def",
        e2e_run_id="test-run",
        evidence_root="evidence/ops/test",
    )
    assert report["PAPER_STATUS"] == "PARKED"
    assert report["FIRST_REAL_BLOCKER"] == "EXTERNAL_EFFECT_AUTHORIZATION"
    assert report["ACTUAL_LIVE_EXTERNAL_EFFECT_AUTHORIZED"] is False
    blockers = readjudicate_historical_blockers_v1(treasury_report=treasury)
    assert blockers["paper_g2_learning_branch"] == "PARKED_NOT_ON_LIVE_READINESS_WP"


def test_orchestrator_script_exists() -> None:
    assert (
        REPO / "scripts/ops/run_post_6940_authority_map_atlas_live_readiness_convergence_v1.py"
    ).is_file()


def test_workpackage_id_stable() -> None:
    assert WORKPACKAGE_ID == ("POST_6940_AUTHORITY_MAP_ATLAS_GUIDED_LIVE_READINESS_CONVERGENCE_V1")
