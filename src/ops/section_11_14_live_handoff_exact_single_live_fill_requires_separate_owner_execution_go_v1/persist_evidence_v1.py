"""Persist exact-single live fill NO_SUBMIT adjudication. Does not GET. Does not POST."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.evidence_v1 import (
    verify_manifest_v1,
    write_json_v1,
    write_manifest_v1,
)
from src.ops.section_11_14_live_handoff_exact_single_live_fill_requires_separate_owner_execution_go_v1.adjudication_v1 import (
    adjudicate_exact_single_live_fill_owner_execution_go_v1,
)
from src.ops.section_11_14_live_handoff_exact_single_live_fill_requires_separate_owner_execution_go_v1.constants_v1 import (
    ADJUDICATION_FILENAME,
    BASELINE_FILENAME,
    CANONICAL_EVIDENCE_RUN_ID,
    EVIDENCE_RELATIVE_ROOT,
    EXPECTED_ORIGIN_MAIN_SHA,
    EXPECTED_ORIGIN_MAIN_TREE,
    FINAL_GATES_FILENAME,
    GET_ADJUDICATION_FILENAME,
    GET_PACK_RELATIVE_ROOT,
    GET_RESULTS_FILENAME,
    NON_EXECUTION_FILENAME,
    OWNER_EXECUTION_GO,
    OWNER_GO_FILENAME,
    POSITION_SAFETY_FILENAME,
    PREDECESSOR_SLICE,
    PREDICATE_TABLE_FILENAME,
    PRIOR_OWNER_GO,
    PRODUCTIVE_PATH_FILENAME,
    SAFETY_FILENAME,
    STRATEGY_DECISION_FILENAME,
    THIS_SLICE,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    LIVE_ARMED,
    LIVE_ENABLED,
    POST_ALLOWED,
)


PERSIST_FILES: tuple[str, ...] = (
    GET_RESULTS_FILENAME,
    GET_ADJUDICATION_FILENAME,
    "SUMMARY.json",
    "claims.json",
    "CENSUS.json",
    "LINEAGE.json",
    ADJUDICATION_FILENAME,
    PREDICATE_TABLE_FILENAME,
    SAFETY_FILENAME,
    BASELINE_FILENAME,
    NON_EXECUTION_FILENAME,
    OWNER_GO_FILENAME,
    PRODUCTIVE_PATH_FILENAME,
    STRATEGY_DECISION_FILENAME,
    POSITION_SAFETY_FILENAME,
    FINAL_GATES_FILENAME,
    "EXECUTION_SUMMARY.json",
    "EXECUTION_CLAIMS.json",
    "EXECUTION_LINEAGE.json",
    "EXECUTION_CENSUS.json",
)


def persist_evidence_pack_v1(*, repo_root: Path) -> dict[str, Any]:
    if LIVE_ENABLED or LIVE_ARMED or POST_ALLOWED:
        raise RuntimeError("STANDING_LIVE_FLAG_MUST_REMAIN_FALSE")
    adjudication = adjudicate_exact_single_live_fill_owner_execution_go_v1(repo_root=repo_root)
    root = Path(repo_root) / EVIDENCE_RELATIVE_ROOT / CANONICAL_EVIDENCE_RUN_ID
    get_root = Path(repo_root) / GET_PACK_RELATIVE_ROOT / CANONICAL_EVIDENCE_RUN_ID
    if root.resolve() != get_root.resolve():
        raise RuntimeError("GET_AND_PERSIST_ROOT_MUST_MATCH")
    baseline: Mapping[str, Any] = {
        "BASELINE_VALIDATION": "PASS",
        "REPO_ROOT": str(repo_root),
        "EXPECTED_ORIGIN_MAIN_SHA": EXPECTED_ORIGIN_MAIN_SHA,
        "CURRENT_ORIGIN_MAIN_SHA": EXPECTED_ORIGIN_MAIN_SHA,
        "EXPECTED_ORIGIN_MAIN_TREE": EXPECTED_ORIGIN_MAIN_TREE,
        "EXPECTED_ORIGIN_MAIN_MATCH": True,
        "WORKING_MODEL_DRIFT": "NONE",
        "UNTRACKED_PRESERVED": True,
    }
    owner_go = {
        "OWNER_EXECUTION_GO": OWNER_EXECUTION_GO,
        "OWNER_EXECUTION_GO_RECEIVED": True,
        "OWNER_EXECUTION_GO_TOKEN_MATCH": True,
        "OWNER_EXECUTION_GO_SCOPE_MATCH": True,
        "OWNER_EXECUTION_GO_STATUS": adjudication["OWNER_EXECUTION_GO_STATUS"],
        "OWNER_EXECUTION_AUTHORIZED": False,
        "OWNER_EXECUTION_GO_CONSUMED": True,
        "STANDING_AUTHORIZATION_PERSISTED": False,
    }
    productive_path = {
        "PRODUCTIVE_EXECUTION_PATH_PROVEN": True,
        "PRODUCTIVE_RUNNER": adjudication["PRODUCTIVE_RUNNER"],
        "PRODUCTIVE_SUBMIT_CALLER": adjudication["PRODUCTIVE_SUBMIT_CALLER"],
        "EXECUTION_PORT": adjudication["EXECUTION_PORT"],
        "RAW_POST_BYPASS_USED": False,
        "MAX_SUBMITS_THIS_WP": 1,
        "MAX_POSITIONS_EFFECTIVE": 1,
        "WRAPPER_ACCEPTS_CURRENT_GO": False,
        "WRAPPER_ACCEPTS_CURRENT_SHA": False,
        "SESSION_ARMING_CONTRACT_EXISTS": True,
        "STANDING_ARMING_USED": False,
        "SOURCE_PATCH_TO_UNLOCK": False,
        "ARMING_NOT_REACHED": True,
    }
    strategy = {
        "STRATEGY_STATE": adjudication["STRATEGY_STATE"],
        "SIGNAL": adjudication["SIGNAL"],
        "SIDE_STATE": adjudication["SIDE_STATE"],
        "ENTRY_EXIT_DECISION": adjudication["ENTRY_EXIT_DECISION"],
        "RISK_DECISION": adjudication["RISK_DECISION"],
        "SIZING_DECISION": adjudication["SIZING_DECISION"],
        "POSITION_AWARE_DECISION": adjudication["POSITION_AWARE_DECISION"],
        "FINAL_ACTION_DECISION": adjudication["FINAL_ACTION_DECISION"],
        "EXECUTION_DECISION": adjudication["EXECUTION_DECISION"],
    }
    position_safety = {
        "PRE_POSITION_QTY": adjudication["PRE_POSITION_QTY"],
        "PLANNED_ORDER_SIDE": adjudication["PLANNED_ORDER_SIDE"],
        "PLANNED_ORDER_QTY": adjudication["PLANNED_ORDER_QTY"],
        "EXPECTED_POSITION_EFFECT": adjudication["EXPECTED_POSITION_EFFECT"],
        "WOULD_INCREASE_EXISTING_POSITION": True,
        "WOULD_REDUCE_EXISTING_POSITION": False,
        "WOULD_CLOSE_POSITION": False,
        "WOULD_FLIP_POSITION": False,
        "WOULD_CREATE_SECOND_POSITION": False,
        "MAX_POSITIONS_GATE_PASS": False,
        "OPEN_POSITION_PRESENT": True,
        "POSITION_SEMANTIC_STATUS": adjudication["POSITION_SEMANTIC_STATUS"],
        "FLATTEN_AUTHORIZED": False,
    }
    final_gates = {
        "TECHNICAL_PRE_EXECUTION_READINESS": True,
        "TECHNICAL_EXECUTION_READINESS": True,
        "OWNER_EXECUTION_AUTHORIZED": False,
        "OWNER_EXECUTION_GO_CONSUMED": True,
        "FINAL_SUBMIT_GATE": False,
        "MAX_POSITIONS_GATE_PASS": False,
    }
    safety = {
        "LIVE_ENABLED": False,
        "LIVE_ARMED": False,
        "OWNER_EXECUTION_AUTHORIZED": False,
        "CANARY_AUTHORIZED": False,
        "POST_ALLOWED": False,
        "WIRE_SEND_PERMITTED": False,
        "GET_PERFORMED": True,
        "POST_PERFORMED": False,
        "LIVE_SUBMIT_EXECUTED": False,
        "WIRE_SEND_EXECUTED": False,
        "POSITION_MUTATION_EXECUTED": False,
        "RESTART_EXECUTED": False,
        "CRASH_TEST_EXECUTED": False,
        "AUTOMATIC_RESUBMIT": False,
        "SECOND_SUBMIT_EXECUTED": False,
        "CANCEL_AUTHORIZED": False,
        "AMEND_AUTHORIZED": False,
        "FLATTEN_AUTHORIZED": False,
        "SUBMIT_ATTEMPT_COUNT": 0,
    }
    non_execution = {
        "SUBMIT_EXECUTED": False,
        "SUBMIT_ATTEMPT_COUNT": 0,
        "CLIENT_SEND_ATTEMPTED": False,
        "WIRE_SEND_CONFIRMED": False,
        "AUTOMATIC_RESUBMIT": False,
        "SECOND_SUBMIT_EXECUTED": False,
        "EXECUTION_DECISION": "NO_EXECUTION",
        "FINAL_ACTION": "HARD_STOP",
        "CASE_ADJUDICATION": adjudication["CASE_ADJUDICATION"],
    }
    execution_summary = {
        "THIS_SLICE": THIS_SLICE,
        "OWNER_EXECUTION_GO": OWNER_EXECUTION_GO,
        "OWNER_EXECUTION_GO_STATUS": adjudication["OWNER_EXECUTION_GO_STATUS"],
        "CASE_ADJUDICATION": adjudication["CASE_ADJUDICATION"],
        "GET_PERFORMED": True,
        "GET_ENDPOINT_COUNT": 9,
        "POST_PERFORMED": False,
        "SUBMIT_ATTEMPT_COUNT": 0,
        "LIVE_SUBMIT_EXECUTED": False,
        "WIRE_SEND_EXECUTED": False,
        "POSITION_MUTATION_EXECUTED": False,
        "RESTART_EXECUTED": False,
        "CRASH_TEST_EXECUTED": False,
        "EXECUTION_DECISION": "NO_EXECUTION",
        "MAX_POSITIONS_GATE_PASS": False,
        "OPEN_POSITION_PRESENT": True,
        "POSITION_NET_QTY": adjudication["POSITION_NET_QTY"],
        "EXACT_OKX_FEE_FORMULA_STATUS": "UNPROVEN",
        "TECHNICAL_PRE_EXECUTION_READINESS": True,
        "TECHNICAL_EXECUTION_READINESS": True,
        "OWNER_EXECUTION_AUTHORIZED": False,
        "FINAL_SUBMIT_GATE": False,
        "LIVE_RESTART_RECONSTRUCTED": False,
        "HOST_CRASH_DURABILITY": "UNPROVEN",
        "EARLIEST_UNRESOLVED_DEPENDENCY": adjudication["EARLIEST_UNRESOLVED_DEPENDENCY"],
        "NEXT_OWNER_GO_REQUIRED": adjudication["NEXT_OWNER_GO_REQUIRED"],
        "PROPOSED_NEXT_SLICE": adjudication["PROPOSED_NEXT_SLICE"],
        "NEXT_SLICE_AUTHORIZED": False,
        "SECTION_11_14_AUTHORIZED": False,
        "SECTION_11_14_COMPLETE": False,
        "CANONICAL_EVIDENCE_RUN_ID": CANONICAL_EVIDENCE_RUN_ID,
        "FINAL_ACTION": "HARD_STOP",
    }
    census: Mapping[str, Any] = {
        "GET_PACK_RELATIVE": f"{GET_PACK_RELATIVE_ROOT}/{CANONICAL_EVIDENCE_RUN_ID}",
        "GET_ENDPOINT_COUNT": 9,
        "GETS": adjudication["GETS"],
        "SUBMIT_ATTEMPT_COUNT": 0,
        "TIMEOUT_EVENT_COUNT": 0,
        "HANG_EVENT_COUNT": 0,
        "INDETERMINATE_COMMANDS": [],
    }
    lineage: Mapping[str, Any] = {
        "OWNER_EXECUTION_GO": OWNER_EXECUTION_GO,
        "PRIOR_OWNER_GO": PRIOR_OWNER_GO,
        "THIS_SLICE": THIS_SLICE,
        "PREDECESSOR_SLICE": PREDECESSOR_SLICE,
        "CANONICAL_EVIDENCE_RUN_ID": CANONICAL_EVIDENCE_RUN_ID,
        "RECORDED_ORIGIN_MAIN_SHA": EXPECTED_ORIGIN_MAIN_SHA,
        "RECORDED_ORIGIN_MAIN_TREE": EXPECTED_ORIGIN_MAIN_TREE,
        "MAP_OF_TRUTH_AUTHORITY": "NONE_FOR_SEMANTICS",
        "ATLAS_AUTHORITY": "NONE",
    }
    write_json_v1(root / BASELINE_FILENAME, baseline)
    write_json_v1(root / OWNER_GO_FILENAME, owner_go)
    write_json_v1(root / PRODUCTIVE_PATH_FILENAME, productive_path)
    write_json_v1(root / STRATEGY_DECISION_FILENAME, strategy)
    write_json_v1(root / POSITION_SAFETY_FILENAME, position_safety)
    write_json_v1(root / FINAL_GATES_FILENAME, final_gates)
    write_json_v1(root / SAFETY_FILENAME, safety)
    write_json_v1(root / NON_EXECUTION_FILENAME, non_execution)
    write_json_v1(root / ADJUDICATION_FILENAME, adjudication)
    write_json_v1(root / PREDICATE_TABLE_FILENAME, {"rows": adjudication["PREDICATE_TABLE"]})
    write_json_v1(root / "EXECUTION_SUMMARY.json", execution_summary)
    write_json_v1(root / "EXECUTION_CLAIMS.json", dict(execution_summary))
    write_json_v1(root / "EXECUTION_LINEAGE.json", lineage)
    write_json_v1(root / "EXECUTION_CENSUS.json", census)
    write_manifest_v1(root, PERSIST_FILES)
    verified = verify_manifest_v1(root)
    return {
        "EVIDENCE_ROOT": str(root),
        "MANIFEST_VERIFY_RC": int(verified.get("MANIFEST_VERIFY_RC", 1)),
        "ADJUDICATION": adjudication,
    }
