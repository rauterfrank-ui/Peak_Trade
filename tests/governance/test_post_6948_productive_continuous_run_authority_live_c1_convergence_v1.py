"""Post-6948 productive continuous-run authority / Live-C1 convergence tests."""

from __future__ import annotations

import json
from pathlib import Path

from src.governance.post_6948_productive_continuous_run_authority_live_c1_convergence_v1 import (
    BASELINE_ORIGIN_MAIN_SHA,
    CANONICAL_CONTINUOUS_AUTHORITY_OWNER,
    DECISION_CONFIG,
    LIVE_C1_GET_OWNER_GO,
    NORMATIVE_SPEC,
    RUNTIME_OWNER_GO_TOKEN,
    WORKPACKAGE_ID,
    build_convergence_report_v1,
    build_owner_decision_schema_v1,
    prove_continuous_module_pins_fail_closed_v1,
    prove_continuous_policy_admission_layer_v1,
    prove_live_c1_get_standing_v1,
)

REPO = Path(__file__).resolve().parents[2]


def test_paths_and_decision_record() -> None:
    assert (REPO / NORMATIVE_SPEC).is_file()
    assert (REPO / DECISION_CONFIG).is_file()
    decision = json.loads((REPO / DECISION_CONFIG).read_text(encoding="utf-8"))
    assert decision["owner_decision_required"] is True
    assert decision["productive_continuous_runtime_executed"] is False
    assert decision["baseline_sha"] == BASELINE_ORIGIN_MAIN_SHA


def test_module_pins_and_runtime_go_standing() -> None:
    pins = prove_continuous_module_pins_fail_closed_v1()
    assert pins["S6_CONTINUOUS_RUN_AUTHORIZED_PIN_FALSE"] is True
    assert pins["S6_RUNTIME_OWNER_GO_NOT_CONSUMED"] is True


def test_continuous_policy_admission_on_repo() -> None:
    layer = prove_continuous_policy_admission_layer_v1(repo_root=REPO)
    assert layer["policy_owner"] == CANONICAL_CONTINUOUS_AUTHORITY_OWNER
    assert layer["policy_authorized"] is True
    assert layer["standing_continuous_run_authorized"] is True
    assert layer["continuous_runtime_admission_granted"] is True
    assert layer["external_effect_authorized_by_policy"] is False


def test_live_c1_get_defined_not_consumed() -> None:
    live = prove_live_c1_get_standing_v1()
    assert live["fresh_c1_get_owner_go"] == LIVE_C1_GET_OWNER_GO
    assert live["fresh_c1_get_owner_go_status"] == "DEFINED_NOT_CONSUMED"


def test_convergence_report_blocks_productive_execution() -> None:
    report = build_convergence_report_v1(repo_root=REPO, baseline_sha=BASELINE_ORIGIN_MAIN_SHA)
    assert report["EXISTING_AUTHORITY_SUFFICIENT"] is False
    assert report["OWNER_DECISION_REQUIRED"] is True
    assert RUNTIME_OWNER_GO_TOKEN in report["EARLIEST_MISSING_JOIN_OR_GATE"]
    assert report["PRODUCTIVE_RUNTIME_EXECUTED"] is False
    assert report["VENUE_POST_COUNT"] == 0
    assert len(report["PRODUCTIVE_CONTINUOUS_CAUSAL_PATH"]) >= 8


def test_owner_decision_schema_tokens() -> None:
    schema = build_owner_decision_schema_v1()
    tokens = {t["token"] for t in schema["tokens_to_scope_and_consume"]}
    assert RUNTIME_OWNER_GO_TOKEN in tokens
    assert LIVE_C1_GET_OWNER_GO in tokens
    assert "CONSUME_EXISTING_ACTUAL_VENUE_POST_OWNER_GO" in schema["must_not_imply"]


def test_orchestrator_script_exists() -> None:
    assert (
        REPO
        / "scripts/ops/run_post_6948_productive_continuous_run_authority_live_c1_convergence_v1.py"
    ).is_file()


def test_workpackage_id_stable() -> None:
    assert WORKPACKAGE_ID == "POST_6948_PRODUCTIVE_CONTINUOUS_RUN_AUTHORITY_LIVE_C1_CONVERGENCE_V1"
