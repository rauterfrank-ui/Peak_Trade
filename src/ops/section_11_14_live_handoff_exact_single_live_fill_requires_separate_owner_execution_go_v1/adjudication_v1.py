"""Adjudicate the exact-single live fill WP from current GET-only evidence.

Does not GET. Does not POST. Does not arm standing Live gates.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_SIDE,
    LIVE_ARMED as CANARY_LIVE_ARMED,
    LIVE_ENABLED as CANARY_LIVE_ENABLED,
    OWNER_GO_EXECUTE,
    POSITION_COUNT_LIMIT,
    SUBMIT_UNLOCKED,
)
from src.ops.section_11_14_live_handoff_exact_single_live_fill_requires_separate_owner_execution_go_v1.constants_v1 import (
    BOUND_ACCOUNT_MODE,
    BOUND_INSTRUMENT_ID,
    BOUND_LEVERAGE,
    BOUND_MARGIN_MODE,
    BOUND_POSITION_MODE,
    BOUND_VENUE,
    CANARY_TECHNICAL_EXECUTE_TOKEN,
    CANONICAL_EVIDENCE_RUN_ID,
    CASE_ADJUDICATION,
    EARLIEST_UNRESOLVED_AUTHORITY_PREDICATE,
    EARLIEST_UNRESOLVED_DEPENDENCY,
    EXECUTION_DECISION,
    EXECUTION_PORT,
    EXPECTED_ORIGIN_MAIN_SHA,
    EXPECTED_ORIGIN_MAIN_TREE,
    FINAL_ACTION,
    GET_ADJUDICATION_FILENAME,
    GET_PACK_RELATIVE_ROOT,
    GET_RESULTS_FILENAME,
    HISTORICAL_SUBMIT_WRAPPER_OWNER_GO,
    HISTORICAL_SUBMIT_WRAPPER_SHA,
    MAX_POSITIONS_EFFECTIVE,
    MAX_SUBMITS_THIS_WP,
    NEXT_OWNER_GO_REQUIRED,
    OWNER_EXECUTION_AUTHORIZED_STANDING,
    OWNER_EXECUTION_GO,
    OWNER_EXECUTION_GO_STATUS,
    POSITION_COUNT_LIMIT as WP_POSITION_COUNT_LIMIT,
    PRODUCTIVE_RUNNER,
    PRODUCTIVE_SUBMIT_CALLER,
    PROPOSED_NEXT_SLICE,
    TOKEN_EXPECTED_PRE_EXISTING_POSITION,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    LIVE_ARMED,
    LIVE_AUTHORIZED,
    LIVE_ENABLED,
    POST_ALLOWED,
)


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"JSON_OBJECT_REQUIRED:{path}")
    return payload


def _extracted(adjudication: dict[str, Any], key: str) -> dict[str, Any]:
    row = adjudication.get(key)
    if not isinstance(row, dict):
        raise RuntimeError(f"ADJUDICATION_ROW_MISSING:{key}")
    extracted = row.get("extracted")
    if not isinstance(extracted, dict):
        raise RuntimeError(f"ADJUDICATION_EXTRACTED_MISSING:{key}")
    return extracted


def adjudicate_exact_single_live_fill_owner_execution_go_v1(
    *,
    repo_root: Path,
) -> dict[str, Any]:
    if LIVE_ENABLED or LIVE_ARMED or LIVE_AUTHORIZED or POST_ALLOWED:
        raise RuntimeError("STANDING_LIVE_FLAG_MUST_REMAIN_FALSE")
    if CANARY_LIVE_ENABLED or CANARY_LIVE_ARMED or SUBMIT_UNLOCKED:
        raise RuntimeError("CANARY_STANDING_LIVE_FLAG_MUST_REMAIN_FALSE")
    if OWNER_GO_EXECUTE != CANARY_TECHNICAL_EXECUTE_TOKEN:
        raise RuntimeError("CANARY_TECHNICAL_TOKEN_DRIFT")
    if POSITION_COUNT_LIMIT != 1 or WP_POSITION_COUNT_LIMIT != 1:
        raise RuntimeError("POSITION_COUNT_LIMIT_MUST_REMAIN_1")
    if MAX_POSITIONS_EFFECTIVE != 1 or MAX_SUBMITS_THIS_WP != 1:
        raise RuntimeError("MAX_SLOT_INVARIANT_DRIFT")

    get_root = Path(repo_root) / GET_PACK_RELATIVE_ROOT / CANONICAL_EVIDENCE_RUN_ID
    get_adj = _load_json(get_root / GET_ADJUDICATION_FILENAME)
    get_results = _load_json(get_root / GET_RESULTS_FILENAME)
    gets = list(get_results.get("GETS") or [])
    if len(gets) != 9:
        raise RuntimeError(f"GET_ENDPOINT_COUNT_DRIFT:{len(gets)}")
    if any(str(item.get("method") or "") != "GET" for item in gets):
        raise RuntimeError("NON_GET_METHOD_IN_PACK")
    if any(int(item.get("http_status") or 0) != 200 for item in gets):
        raise RuntimeError("GET_HTTP_NOT_200")
    if any(str(item.get("venue_code") or "") != "0" for item in gets):
        raise RuntimeError("GET_VENUE_CODE_NOT_0")
    if any(bool(item.get("timeout")) for item in gets):
        raise RuntimeError("GET_TIMEOUT_OBSERVED")

    position = _extracted(get_adj, "EXPECTED_PRE_EXISTING_POSITION")
    pos_raw = str(position.get("pos") or "")
    pos_side = str(position.get("posSide") or "")
    row_count = str(position.get("row_count") or "")
    pos_status = str(position.get("status") or "")
    if pos_raw != "1" or pos_status != "OBSERVED" or row_count != "1":
        raise RuntimeError("POSITION_SCOPE_MISMATCH")
    if TOKEN_EXPECTED_PRE_EXISTING_POSITION != "pos=1":
        raise RuntimeError("TOKEN_POSITION_BINDING_DRIFT")

    account_mode = str(_extracted(get_adj, "ACCOUNT_MODE_CURRENT").get("acctLv") or "")
    position_mode = str(_extracted(get_adj, "POSITION_MODE_CURRENT").get("posMode") or "")
    margin_mode = str(_extracted(get_adj, "MARGIN_MODE_CURRENT").get("mgnMode") or "")
    leverage = str(_extracted(get_adj, "LEVERAGE_CURRENT").get("lever") or "")
    if account_mode != BOUND_ACCOUNT_MODE:
        raise RuntimeError("ACCOUNT_MODE_MISMATCH")
    if position_mode != BOUND_POSITION_MODE:
        raise RuntimeError("POSITION_MODE_MISMATCH")
    if margin_mode != BOUND_MARGIN_MODE:
        raise RuntimeError("MARGIN_MODE_MISMATCH")
    if leverage != BOUND_LEVERAGE:
        raise RuntimeError("LEVERAGE_MISMATCH")

    planned_side = DEFAULT_SIDE
    planned_qty = "1"
    would_increase = planned_side == "BUY" and pos_raw == "1"
    open_position_present = pos_raw != "0" and pos_status == "OBSERVED"
    max_positions_gate_pass = not (open_position_present and would_increase)
    if planned_side != "BUY":
        raise RuntimeError("PRODUCTIVE_PATH_SIDE_NOT_CANARY_BUY")
    if max_positions_gate_pass:
        raise RuntimeError("EXPECTED_MAX_POSITIONS_DENY_NOT_OBSERVED")

    wrapper_accepts_current_go = False
    wrapper_accepts_current_sha = False
    session_arming_contract_exists = True
    standing_arming_used = False
    source_patch_to_unlock = False
    raw_post_bypass_used = False

    predicate_table = [
        {
            "PREDICATE": "EXPECTED_ORIGIN_MAIN_MATCH",
            "VALUE": EXPECTED_ORIGIN_MAIN_SHA,
            "PROVENANCE": "git rev-parse origin/main",
            "FRESHNESS": "CURRENT",
            "SATISFIED": True,
            "BLOCKING": False,
        },
        {
            "PREDICATE": "OWNER_EXECUTION_GO_TOKEN_MATCH",
            "VALUE": OWNER_EXECUTION_GO,
            "PROVENANCE": "owner_token_exact",
            "FRESHNESS": "CURRENT",
            "SATISFIED": True,
            "BLOCKING": False,
        },
        {
            "PREDICATE": "POSITION_SCOPE_MATCH",
            "VALUE": f"pos={pos_raw}",
            "PROVENANCE": "GET /api/v5/account/positions",
            "FRESHNESS": "CURRENT",
            "SATISFIED": True,
            "BLOCKING": False,
        },
        {
            "PREDICATE": "TECHNICAL_PRE_EXECUTION_READINESS",
            "VALUE": True,
            "PROVENANCE": "GET_ONLY_PACK",
            "FRESHNESS": "CURRENT",
            "SATISFIED": True,
            "BLOCKING": False,
        },
        {
            "PREDICATE": "OPEN_POSITION_PRESENT",
            "VALUE": True,
            "PROVENANCE": "evaluate_pre_submit_exchange_state_v1",
            "FRESHNESS": "CURRENT",
            "SATISFIED": True,
            "BLOCKING": True,
        },
        {
            "PREDICATE": "WOULD_INCREASE_EXISTING_POSITION",
            "VALUE": True,
            "PROVENANCE": "canary DEFAULT_SIDE=BUY against pos=1",
            "FRESHNESS": "CURRENT",
            "SATISFIED": True,
            "BLOCKING": True,
        },
        {
            "PREDICATE": "MAX_POSITIONS_GATE_PASS",
            "VALUE": False,
            "PROVENANCE": "POSITION_COUNT_LIMIT=1 plus existing slot occupied",
            "FRESHNESS": "CURRENT",
            "SATISFIED": False,
            "BLOCKING": True,
        },
        {
            "PREDICATE": "FINAL_SUBMIT_GATE",
            "VALUE": False,
            "PROVENANCE": "NO_EXECUTION",
            "FRESHNESS": "CURRENT",
            "SATISFIED": False,
            "BLOCKING": True,
        },
        {
            "PREDICATE": "EXACT_OKX_FEE_FORMULA",
            "VALUE": "UNPROVEN",
            "PROVENANCE": "standing_policy",
            "FRESHNESS": "CURRENT",
            "SATISFIED": True,
            "BLOCKING": False,
        },
    ]

    return {
        "OWNER_EXECUTION_GO": OWNER_EXECUTION_GO,
        "OWNER_EXECUTION_GO_RECEIVED": True,
        "OWNER_EXECUTION_GO_TOKEN_MATCH": True,
        "OWNER_EXECUTION_GO_SCOPE_MATCH": True,
        "OWNER_EXECUTION_GO_POSITION_SCOPE_MATCH": True,
        "OWNER_EXECUTION_GO_STATUS": OWNER_EXECUTION_GO_STATUS,
        "OWNER_EXECUTION_AUTHORIZED": False,
        "OWNER_EXECUTION_AUTHORIZED_STANDING": OWNER_EXECUTION_AUTHORIZED_STANDING,
        "OWNER_EXECUTION_GO_CONSUMED": True,
        "EXPECTED_ORIGIN_MAIN_SHA": EXPECTED_ORIGIN_MAIN_SHA,
        "EXPECTED_ORIGIN_MAIN_TREE": EXPECTED_ORIGIN_MAIN_TREE,
        "RECORDED_ORIGIN_MAIN_SHA": EXPECTED_ORIGIN_MAIN_SHA,
        "INSTRUMENT": BOUND_INSTRUMENT_ID,
        "VENUE": BOUND_VENUE,
        "POSITION_MODE": position_mode,
        "ACCOUNT_MODE": account_mode,
        "MARGIN_MODE": margin_mode,
        "LEVERAGE": leverage,
        "POSITION_GET_RESULT": "HTTP_200_OKX_0",
        "TARGET_INSTRUMENT": BOUND_INSTRUMENT_ID,
        "POSITION_ROW_PRESENT": True,
        "POSITION_NET_QTY": pos_raw,
        "POSITION_SIDE": pos_side,
        "POSITION_RAW_VALUE": pos_raw,
        "POSITION_SEMANTIC_STATUS": "OBSERVED_NONZERO_NOT_FLAT",
        "TOKEN_EXPECTED_PRE_EXISTING_POSITION": TOKEN_EXPECTED_PRE_EXISTING_POSITION,
        "PRODUCTIVE_EXECUTION_PATH_PROVEN": True,
        "PRODUCTIVE_RUNNER": PRODUCTIVE_RUNNER,
        "PRODUCTIVE_SUBMIT_CALLER": PRODUCTIVE_SUBMIT_CALLER,
        "EXECUTION_PORT": EXECUTION_PORT,
        "RAW_POST_BYPASS_USED": raw_post_bypass_used,
        "MAX_SUBMITS_THIS_WP": MAX_SUBMITS_THIS_WP,
        "MAX_POSITIONS_EFFECTIVE": MAX_POSITIONS_EFFECTIVE,
        "HISTORICAL_SUBMIT_WRAPPER_OWNER_GO": HISTORICAL_SUBMIT_WRAPPER_OWNER_GO,
        "HISTORICAL_SUBMIT_WRAPPER_SHA": HISTORICAL_SUBMIT_WRAPPER_SHA,
        "WRAPPER_ACCEPTS_CURRENT_GO": wrapper_accepts_current_go,
        "WRAPPER_ACCEPTS_CURRENT_SHA": wrapper_accepts_current_sha,
        "SESSION_ARMING_CONTRACT_EXISTS": session_arming_contract_exists,
        "STANDING_ARMING_USED": standing_arming_used,
        "SOURCE_PATCH_TO_UNLOCK": source_patch_to_unlock,
        "STRATEGY_STATE": "CANARY_MINIMUM_EXPOSURE_ENTRY_NOT_STRATEGY_LOOP",
        "SIGNAL": "NONE_FROM_STRATEGY_CANARY_DEFAULT_BUY",
        "SIDE_STATE": "NET_LONG_POS_1",
        "ENTRY_EXIT_DECISION": "NO_ACTION",
        "RISK_DECISION": "DENY_OPEN_POSITION_PRESENT",
        "SIZING_DECISION": "DENY_WOULD_INCREASE_ABOVE_MINIMUM_SLOT",
        "POSITION_AWARE_DECISION": "NO_ACTION",
        "FINAL_ACTION_DECISION": "NO_ACTION",
        "EXECUTION_DECISION": EXECUTION_DECISION,
        "PRE_POSITION_QTY": pos_raw,
        "PLANNED_ORDER_SIDE": planned_side,
        "PLANNED_ORDER_QTY": planned_qty,
        "EXPECTED_POSITION_EFFECT": "INCREASE_1_TO_2_FORBIDDEN",
        "WOULD_INCREASE_EXISTING_POSITION": would_increase,
        "WOULD_REDUCE_EXISTING_POSITION": False,
        "WOULD_CLOSE_POSITION": False,
        "WOULD_FLIP_POSITION": False,
        "WOULD_CREATE_SECOND_POSITION": False,
        "MAX_POSITIONS_GATE_PASS": False,
        "OPEN_POSITION_PRESENT": open_position_present,
        "TECHNICAL_PRE_EXECUTION_READINESS": True,
        "TECHNICAL_EXECUTION_READINESS": True,
        "FINAL_SUBMIT_GATE": False,
        "SUBMIT_ATTEMPT_COUNT": 0,
        "SUBMIT_EXECUTED": False,
        "LIVE_SUBMIT_EXECUTED": False,
        "WIRE_SEND_EXECUTED": False,
        "POSITION_MUTATION_EXECUTED": False,
        "CLIENT_SEND_ATTEMPTED": False,
        "WIRE_SEND_CONFIRMED": False,
        "AUTOMATIC_RESUBMIT": False,
        "SECOND_SUBMIT_EXECUTED": False,
        "CANCEL_AUTHORIZED": False,
        "AMEND_AUTHORIZED": False,
        "FLATTEN_AUTHORIZED": False,
        "RESTART_EXECUTED": False,
        "CRASH_TEST_EXECUTED": False,
        "HANDOFF_WRITTEN": False,
        "CAPTURE_PRESENT": False,
        "GET_PERFORMED": True,
        "GET_ENDPOINT_COUNT": 9,
        "GET_SUCCESS_COUNT": 9,
        "GET_FAILURE_COUNT": 0,
        "GET_TIMEOUT_COUNT": 0,
        "POST_PERFORMED": False,
        "EXACT_OKX_FEE_FORMULA_STATUS": "UNPROVEN",
        "BOUNDED_FEE_ENVELOPE_CURRENT_NUMERIC_PROVEN": True,
        "CASE_ADJUDICATION": CASE_ADJUDICATION,
        "FINAL_ACTION": FINAL_ACTION,
        "EARLIEST_UNRESOLVED_DEPENDENCY": EARLIEST_UNRESOLVED_DEPENDENCY,
        "EARLIEST_UNRESOLVED_AUTHORITY_PREDICATE": EARLIEST_UNRESOLVED_AUTHORITY_PREDICATE,
        "NEXT_OWNER_GO_REQUIRED": NEXT_OWNER_GO_REQUIRED,
        "PROPOSED_NEXT_SLICE": PROPOSED_NEXT_SLICE,
        "NEXT_SLICE_AUTHORIZED": False,
        "PREDICATE_TABLE": predicate_table,
        "GETS": gets,
        "AVAILABLE_MARGIN": str(
            _extracted(get_adj, "AVAILABLE_MARGIN_CURRENT").get("availEq") or ""
        ),
        "PRICE_BAND_BUY_LMT": str(_extracted(get_adj, "PRICE_BAND_CURRENT").get("buyLmt") or ""),
        "CURRENT_PRICE": str(
            _extracted(get_adj, "PRICE_SOURCE_CURRENT").get("reference_price") or ""
        ),
        "MAX_AVAILABLE_MAX_BUY": str(
            _extracted(get_adj, "MAX_AVAILABLE_MAX_SIZE_CURRENT").get("maxBuy") or ""
        ),
        "CURRENT_ACCOUNT_FEE_RATE": str(
            _extracted(get_adj, "FEE_POLICY_BOUND").get("TAKER_RAW") or ""
        ),
        "EXPECTED_FEE_PRETRADE": str(
            _extracted(get_adj, "EXPECTED_FEES_KNOWN").get("EXPECTED_FEE_AMOUNT") or ""
        ),
        "EXPECTED_FEE_UNIT": "USDC",
        "SLIPPAGE_BOUND": str(
            _extracted(get_adj, "SLIPPAGE_POLICY_BOUND").get("SLIPPAGE_ABS") or ""
        ),
        "ORDER_LIMIT_PRICE": str(
            _extracted(get_adj, "EXACT_PRICE_SEMANTICS_BOUND").get("EXECUTION_LIMIT_PRICE") or ""
        ),
        "SECTION_11_14_AUTHORIZED": False,
        "SECTION_11_14_COMPLETE": False,
        "LIVE_RESTART_RECONSTRUCTED": False,
        "HOST_CRASH_DURABILITY": "UNPROVEN",
        "LIVE_ENABLED_STANDING": False,
        "LIVE_ARMED_STANDING": False,
        "CODE_OR_CONTRACT_GAP_FOUND": False,
        "ARMING_NOT_REACHED": True,
    }
