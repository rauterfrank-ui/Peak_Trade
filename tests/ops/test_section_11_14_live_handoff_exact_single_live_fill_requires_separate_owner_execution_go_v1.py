"""Exact-single live fill Owner Execution GO tests. No live network. No POST."""

from __future__ import annotations

from pathlib import Path

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.evidence_v1 import (
    verify_manifest_v1,
)
from src.ops.section_11_14_live_handoff_exact_single_live_fill_requires_separate_owner_execution_go_v1.adjudication_v1 import (
    adjudicate_exact_single_live_fill_owner_execution_go_v1,
)
from src.ops.section_11_14_live_handoff_exact_single_live_fill_requires_separate_owner_execution_go_v1.constants_v1 import (
    CANONICAL_EVIDENCE_RUN_ID,
    CASE_ADJUDICATION,
    EVIDENCE_RELATIVE_ROOT,
    EXPECTED_ORIGIN_MAIN_SHA,
    OWNER_EXECUTION_GO,
    OWNER_EXECUTION_GO_STATUS,
)
from src.ops.section_11_14_live_handoff_exact_single_live_fill_requires_separate_owner_execution_go_v1.persist_evidence_v1 import (
    persist_evidence_pack_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    LIVE_ARMED,
    LIVE_ENABLED,
    POST_ALLOWED,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_exact_single_live_fill_adjudication_is_consumed_no_submit() -> None:
    result = adjudicate_exact_single_live_fill_owner_execution_go_v1(repo_root=REPO_ROOT)
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert POST_ALLOWED is False
    assert result["OWNER_EXECUTION_GO"] == OWNER_EXECUTION_GO
    assert result["OWNER_EXECUTION_GO_TOKEN_MATCH"] is True
    assert result["OWNER_EXECUTION_GO_SCOPE_MATCH"] is True
    assert result["OWNER_EXECUTION_GO_STATUS"] == OWNER_EXECUTION_GO_STATUS
    assert result["OWNER_EXECUTION_AUTHORIZED"] is False
    assert result["RECORDED_ORIGIN_MAIN_SHA"] == EXPECTED_ORIGIN_MAIN_SHA
    assert result["POSITION_NET_QTY"] == "1"
    assert result["POSITION_SEMANTIC_STATUS"] == "OBSERVED_NONZERO_NOT_FLAT"
    assert result["WOULD_INCREASE_EXISTING_POSITION"] is True
    assert result["WOULD_CREATE_SECOND_POSITION"] is False
    assert result["MAX_POSITIONS_GATE_PASS"] is False
    assert result["OPEN_POSITION_PRESENT"] is True
    assert result["EXECUTION_DECISION"] == "NO_EXECUTION"
    assert result["FINAL_SUBMIT_GATE"] is False
    assert result["SUBMIT_ATTEMPT_COUNT"] == 0
    assert result["LIVE_SUBMIT_EXECUTED"] is False
    assert result["WIRE_SEND_EXECUTED"] is False
    assert result["POST_PERFORMED"] is False
    assert result["AUTOMATIC_RESUBMIT"] is False
    assert result["SECOND_SUBMIT_EXECUTED"] is False
    assert result["FLATTEN_AUTHORIZED"] is False
    assert result["RESTART_EXECUTED"] is False
    assert result["CRASH_TEST_EXECUTED"] is False
    assert result["GET_PERFORMED"] is True
    assert result["GET_ENDPOINT_COUNT"] == 9
    assert result["CASE_ADJUDICATION"] == CASE_ADJUDICATION
    assert result["FINAL_ACTION"] == "HARD_STOP"
    assert result["EXACT_OKX_FEE_FORMULA_STATUS"] == "UNPROVEN"
    assert result["STANDING_ARMING_USED"] is False
    assert result["SOURCE_PATCH_TO_UNLOCK"] is False
    assert result["RAW_POST_BYPASS_USED"] is False
    assert result["ARMING_NOT_REACHED"] is True


def test_exact_single_live_fill_does_not_normalize_pos_1_to_flat() -> None:
    result = adjudicate_exact_single_live_fill_owner_execution_go_v1(repo_root=REPO_ROOT)
    assert result["POSITION_NET_QTY"] != "0"
    assert result["POSITION_SEMANTIC_STATUS"] != "FLAT"
    assert result["POSITION_SEMANTIC_STATUS"] != "ZERO_POSITION"
    assert result["POSITION_SEMANTIC_STATUS"] != "NO_POSITION"
    assert result["ENTRY_EXIT_DECISION"] == "NO_ACTION"
    assert result["EXPECTED_POSITION_EFFECT"] == "INCREASE_1_TO_2_FORBIDDEN"


def test_exact_single_live_fill_persist_manifest_and_non_execution() -> None:
    persisted = persist_evidence_pack_v1(repo_root=REPO_ROOT)
    assert int(persisted["MANIFEST_VERIFY_RC"]) == 0
    overlay = REPO_ROOT / EVIDENCE_RELATIVE_ROOT / CANONICAL_EVIDENCE_RUN_ID
    assert int(verify_manifest_v1(overlay).get("MANIFEST_VERIFY_RC", 1)) == 0
    safety = (overlay / "SAFETY.json").read_text(encoding="utf-8")
    assert '"OWNER_EXECUTION_AUTHORIZED": false' in safety
    assert '"POST_PERFORMED": false' in safety
    assert '"GET_PERFORMED": true' in safety
    assert '"SUBMIT_ATTEMPT_COUNT": 0' in safety
    summary = (overlay / "EXECUTION_SUMMARY.json").read_text(encoding="utf-8")
    assert '"EXECUTION_DECISION": "NO_EXECUTION"' in summary
    assert '"OWNER_EXECUTION_GO_STATUS": "CONSUMED_NO_SUBMIT"' in summary
    assert '"LIVE_SUBMIT_EXECUTED": false' in summary
    non_execution = (overlay / "NON_EXECUTION.json").read_text(encoding="utf-8")
    assert '"AUTOMATIC_RESUBMIT": false' in non_execution
    assert '"SECOND_SUBMIT_EXECUTED": false' in non_execution
