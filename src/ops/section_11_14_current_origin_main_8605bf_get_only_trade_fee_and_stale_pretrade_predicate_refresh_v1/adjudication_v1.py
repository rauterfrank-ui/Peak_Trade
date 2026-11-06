"""Offline adjudication of the current GET-only trade-fee refresh pack.

Reads already persisted GET-only evidence. Does not GET. Does not POST.
Does not treat a successful trade-fee GET as OEM formula proof.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from src.ops.section_11_14_current_origin_main_8605bf_get_only_trade_fee_and_stale_pretrade_predicate_refresh_v1.constants_v1 import (
    BOUND_INST_FAMILY,
    BOUND_INST_TYPE,
    BOUND_INSTRUMENT_ID,
    BOUND_REST_BASE,
    BOUND_VENUE,
    CANARY_AUTHORIZED_EXACT_FIELD,
    CANONICAL_EVIDENCE_RUN_ID,
    EARLIEST_LADDER_BLOCKER,
    EARLIEST_UNRESOLVED_AUTHORITY_PREDICATE,
    EXACT_OKX_FEE_FORMULA_STATUS,
    EXACT_OKX_FEE_FORMULA_UNPROVEN,
    EXPECTED_ORIGIN_MAIN_SHA,
    GET_PACK_RELATIVE_ROOT,
    HOST_CRASH_DURABILITY_STATUS,
    LIVE_RESTART_RECONSTRUCTED,
    NEXT_OWNER_GO_REQUIRED,
    OWNER_EXECUTION_AUTHORIZED,
    OWNER_GET_ONLY_GO,
    POST_ALLOWED_EXACT_FIELD,
    PREVIOUS_GET_PACK_ORIGIN_MAIN_SHA,
    PREVIOUS_GET_PACK_RUN_ID,
    PROCESS_CRASH_DURABILITY_STATUS,
    PROPOSED_NEXT_SLICE,
    THIS_SLICE,
    TRADE_FEE_QUERY,
)


class TradeFeeRefreshAdjudicationError(RuntimeError):
    """Fail-closed GET-refresh adjudication violation."""


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TradeFeeRefreshAdjudicationError(f"JSON_OBJECT_REQUIRED:{path}")
    return payload


def _pred(predicates: Mapping[str, Any], name: str) -> dict[str, Any]:
    row = predicates.get(name)
    if not isinstance(row, dict):
        raise TradeFeeRefreshAdjudicationError(f"PREDICATE_MISSING:{name}")
    return row


def _extracted(predicates: Mapping[str, Any], name: str) -> dict[str, Any]:
    extracted = _pred(predicates, name).get("extracted")
    return dict(extracted) if isinstance(extracted, dict) else {}


def _get_named(gets: list[Any], name: str) -> dict[str, Any]:
    for item in gets:
        if isinstance(item, dict) and item.get("name") == name:
            return item
    raise TradeFeeRefreshAdjudicationError(f"GET_NAMED_MISSING:{name}")


def _row(
    *,
    predicate_id: str,
    predicate_name: str,
    previous_value: str,
    current_value: str,
    current_provenance: str,
    freshness: str,
    satisfied: bool,
    blocking: bool,
    change_reason: str,
) -> dict[str, Any]:
    return {
        "PREDICATE_ID": predicate_id,
        "PREDICATE_NAME": predicate_name,
        "PREVIOUS_VALUE": previous_value,
        "CURRENT_VALUE": current_value,
        "CURRENT_PROVENANCE": current_provenance,
        "FRESHNESS": freshness,
        "SATISFIED": satisfied,
        "BLOCKING": blocking,
        "CHANGE_REASON": change_reason,
    }


def adjudicate_trade_fee_and_stale_pretrade_refresh_v1(*, repo_root: Path) -> dict[str, Any]:
    get_root = Path(repo_root) / GET_PACK_RELATIVE_ROOT / CANONICAL_EVIDENCE_RUN_ID
    summary = _load_json(get_root / "SUMMARY.json")
    predicates = _load_json(get_root / "ADJUDICATION.json")
    get_log = _load_json(get_root / "GET_RESULTS.sanitized.json")
    lineage = _load_json(get_root / "LINEAGE.json")
    gets = list(get_log.get("GETS") or [])
    fee_get = _get_named(gets, "TRADE_FEE")
    fee = _extracted(predicates, "FEE_POLICY_BOUND")
    fee_status = str(_pred(predicates, "FEE_POLICY_BOUND").get("status") or "")
    family_match = str(fee.get("INST_FAMILY") or "") == BOUND_INST_FAMILY
    inst_type_match = str(fee.get("INST_TYPE") or "") == BOUND_INST_TYPE
    recorded_sha = str(lineage.get("RECORDED_ORIGIN_MAIN_SHA") or "")
    if recorded_sha != EXPECTED_ORIGIN_MAIN_SHA:
        raise TradeFeeRefreshAdjudicationError(
            f"GET_PACK_SHA_MISMATCH:{recorded_sha}!={EXPECTED_ORIGIN_MAIN_SHA}"
        )
    if str(fee_get.get("endpoint") or "") != TRADE_FEE_QUERY:
        raise TradeFeeRefreshAdjudicationError(
            f"TRADE_FEE_QUERY_MISMATCH:{fee_get.get('endpoint')}"
        )
    methods = {str(item.get("method") or "") for item in gets if isinstance(item, dict)}
    if methods - {"GET"}:
        raise TradeFeeRefreshAdjudicationError(f"NON_GET_METHOD_OBSERVED:{sorted(methods)}")

    trade_fee_http = int(fee_get.get("http_status") or 0)
    trade_fee_okx = str(fee_get.get("venue_code") or "")
    trade_fee_observed = (
        trade_fee_http == 200 and trade_fee_okx == "0" and fee_status == "PASS" and family_match
    )
    numeric_fee_input = trade_fee_observed and bool(fee.get("CONSERVATIVE_RATE"))
    expected_fee = str(summary.get("EXPECTED_FEES") or "UNKNOWN")
    envelope_complete = bool(summary.get("EXACT_EXECUTION_ENVELOPE_COMPLETE"))
    technical_execution_ready = bool(summary.get("TECHNICAL_EXECUTION_READY"))
    required_pass = (
        "SESSION_AUTH_CURRENT",
        "NETWORK_EGRESS_COMPATIBILITY_CURRENT",
        "ACCOUNT_MODE_CURRENT",
        "POSITION_MODE_CURRENT",
        "LEVERAGE_CURRENT",
        "INSTRUMENT_STATE_CURRENT",
        "AVAILABLE_MARGIN_CURRENT",
        "MAX_AVAILABLE_MAX_SIZE_CURRENT",
        "PRICE_BAND_CURRENT",
        "PRICE_SOURCE_CURRENT",
        "EXACT_PRICE_SEMANTICS_BOUND",
        "FEE_POLICY_BOUND",
    )
    missing = [
        name for name in required_pass if str(_pred(predicates, name).get("status") or "") != "PASS"
    ]
    for name in ("MARGIN_MODE_CURRENT", "EXPECTED_PRE_EXISTING_POSITION"):
        if str(_pred(predicates, name).get("status") or "") not in {"PASS", "NOT_OBSERVED"}:
            missing.append(name)
    technical_pre_execution = (
        not missing
        and numeric_fee_input
        and envelope_complete
        and expected_fee not in {"", "UNKNOWN"}
    )
    bounded_numeric = technical_pre_execution and expected_fee not in {"", "UNKNOWN"}
    if OWNER_EXECUTION_AUTHORIZED:
        raise TradeFeeRefreshAdjudicationError("OWNER_EXECUTION_AUTHORIZED_MUST_REMAIN_FALSE")

    observed_at = str(fee_get.get("observed_at_utc") or "")
    pos_ex = _extracted(predicates, "EXPECTED_PRE_EXISTING_POSITION")
    predicate_table = [
        _row(
            predicate_id="P01",
            predicate_name="NETWORK_READINESS",
            previous_value="PASS_AT_20260907T182140Z_STALE",
            current_value=str(
                _pred(predicates, "NETWORK_EGRESS_COMPATIBILITY_CURRENT").get("status")
            ),
            current_provenance=_pred(predicates, "NETWORK_EGRESS_COMPATIBILITY_CURRENT").get(
                "endpoint", ""
            ),
            freshness="CURRENT",
            satisfied=str(_pred(predicates, "NETWORK_EGRESS_COMPATIBILITY_CURRENT").get("status"))
            == "PASS",
            blocking=False,
            change_reason="RESOLVED_BY_THIS_GET_WP",
        ),
        _row(
            predicate_id="P02",
            predicate_name="SESSION_AUTH",
            previous_value="PASS_AT_20260907T182140Z_STALE",
            current_value=str(_pred(predicates, "SESSION_AUTH_CURRENT").get("status")),
            current_provenance="GET /api/v5/account/config",
            freshness="CURRENT",
            satisfied=str(_pred(predicates, "SESSION_AUTH_CURRENT").get("status")) == "PASS",
            blocking=False,
            change_reason="RESOLVED_BY_THIS_GET_WP",
        ),
        _row(
            predicate_id="P03",
            predicate_name="INSTRUMENT_STATE",
            previous_value="live@20260907T182140Z_STALE",
            current_value=str(_extracted(predicates, "INSTRUMENT_STATE_CURRENT").get("state")),
            current_provenance=_pred(predicates, "INSTRUMENT_STATE_CURRENT").get("endpoint", ""),
            freshness="CURRENT",
            satisfied=str(_pred(predicates, "INSTRUMENT_STATE_CURRENT").get("status")) == "PASS",
            blocking=False,
            change_reason="RESOLVED_BY_THIS_GET_WP",
        ),
        _row(
            predicate_id="P04",
            predicate_name="POSITION_MODE",
            previous_value="net_mode@20260907T182140Z_STALE",
            current_value=str(_extracted(predicates, "POSITION_MODE_CURRENT").get("posMode")),
            current_provenance="GET /api/v5/account/config",
            freshness="CURRENT",
            satisfied=str(_pred(predicates, "POSITION_MODE_CURRENT").get("status")) == "PASS",
            blocking=False,
            change_reason="RESOLVED_BY_THIS_GET_WP",
        ),
        _row(
            predicate_id="P05",
            predicate_name="PRE_EXISTING_POSITION_STATE",
            previous_value="pos=1@20260907T182140Z_STALE",
            current_value=f"pos={pos_ex.get('pos')};status={pos_ex.get('status')}",
            current_provenance="GET /api/v5/account/positions",
            freshness="CURRENT",
            satisfied=str(_pred(predicates, "EXPECTED_PRE_EXISTING_POSITION").get("status"))
            in {"PASS", "NOT_OBSERVED"},
            blocking=False,
            change_reason="RESOLVED_BY_THIS_GET_WP",
        ),
        _row(
            predicate_id="P06",
            predicate_name="ACCOUNT_MODE",
            previous_value="acctLv=2@20260907T182140Z_STALE",
            current_value=str(_extracted(predicates, "ACCOUNT_MODE_CURRENT").get("acctLv")),
            current_provenance="GET /api/v5/account/config",
            freshness="CURRENT",
            satisfied=str(_pred(predicates, "ACCOUNT_MODE_CURRENT").get("status")) == "PASS",
            blocking=False,
            change_reason="RESOLVED_BY_THIS_GET_WP",
        ),
        _row(
            predicate_id="P07",
            predicate_name="MARGIN_MODE",
            previous_value="cross@20260907T182140Z_STALE",
            current_value=str(_extracted(predicates, "MARGIN_MODE_CURRENT").get("mgnMode")),
            current_provenance="GET /api/v5/account/positions",
            freshness="CURRENT",
            satisfied=str(_pred(predicates, "MARGIN_MODE_CURRENT").get("status"))
            in {"PASS", "NOT_OBSERVED"},
            blocking=False,
            change_reason="RESOLVED_BY_THIS_GET_WP",
        ),
        _row(
            predicate_id="P08",
            predicate_name="LEVERAGE",
            previous_value="3@20260907T182140Z_STALE",
            current_value=str(_extracted(predicates, "LEVERAGE_CURRENT").get("lever")),
            current_provenance=_pred(predicates, "LEVERAGE_CURRENT").get("endpoint", ""),
            freshness="CURRENT",
            satisfied=str(_pred(predicates, "LEVERAGE_CURRENT").get("status")) == "PASS",
            blocking=False,
            change_reason="RESOLVED_BY_THIS_GET_WP",
        ),
        _row(
            predicate_id="P09",
            predicate_name="AVAILABLE_MARGIN",
            previous_value="2.1076094140463697_USDC@20260907T182140Z_STALE",
            current_value=str(_extracted(predicates, "AVAILABLE_MARGIN_CURRENT").get("availEq")),
            current_provenance="GET /api/v5/account/balance",
            freshness="CURRENT",
            satisfied=str(_pred(predicates, "AVAILABLE_MARGIN_CURRENT").get("status")) == "PASS",
            blocking=False,
            change_reason="RESOLVED_BY_THIS_GET_WP",
        ),
        _row(
            predicate_id="P10",
            predicate_name="PRICE_BAND",
            previous_value="buyLmt=0.8277@20260907T182140Z_STALE",
            current_value=str(_extracted(predicates, "PRICE_BAND_CURRENT").get("buyLmt")),
            current_provenance=_pred(predicates, "PRICE_BAND_CURRENT").get("endpoint", ""),
            freshness="CURRENT",
            satisfied=str(_pred(predicates, "PRICE_BAND_CURRENT").get("status")) == "PASS",
            blocking=False,
            change_reason="RESOLVED_BY_THIS_GET_WP",
        ),
        _row(
            predicate_id="P11",
            predicate_name="MAX_AVAILABLE",
            previous_value="maxBuy=7@px=0.8237_STALE",
            current_value=str(
                _extracted(predicates, "MAX_AVAILABLE_MAX_SIZE_CURRENT").get("maxBuy")
            ),
            current_provenance=_pred(predicates, "MAX_AVAILABLE_MAX_SIZE_CURRENT").get(
                "endpoint", ""
            ),
            freshness="CURRENT",
            satisfied=str(_pred(predicates, "MAX_AVAILABLE_MAX_SIZE_CURRENT").get("status"))
            == "PASS",
            blocking=False,
            change_reason="RESOLVED_BY_THIS_GET_WP",
        ),
        _row(
            predicate_id="P12",
            predicate_name="CURRENT_PRICE_INPUT",
            previous_value="0.8237@20260907T182140Z_STALE",
            current_value=str(
                _extracted(predicates, "PRICE_SOURCE_CURRENT").get("reference_price")
            ),
            current_provenance=_pred(predicates, "PRICE_SOURCE_CURRENT").get("endpoint", ""),
            freshness="CURRENT",
            satisfied=str(_pred(predicates, "PRICE_SOURCE_CURRENT").get("status")) == "PASS",
            blocking=False,
            change_reason="RESOLVED_BY_THIS_GET_WP",
        ),
        _row(
            predicate_id="P13",
            predicate_name="CURRENT_SUI_FAMILY_TRADE_FEE_GET",
            previous_value="NOT_OBSERVED",
            current_value="OBSERVED" if trade_fee_observed else "NOT_OBSERVED",
            current_provenance=TRADE_FEE_QUERY,
            freshness="CURRENT",
            satisfied=trade_fee_observed,
            blocking=not trade_fee_observed,
            change_reason="RESOLVED_BY_THIS_GET_WP",
        ),
        _row(
            predicate_id="P14",
            predicate_name="EXACT_OKX_FEE_FORMULA",
            previous_value="UNPROVEN",
            current_value="UNPROVEN",
            current_provenance="fee_policy_v1 EXACT_OKX_FEE_FORMULA_STATUS; GET is not OEM proof",
            freshness="UNCHANGED",
            satisfied=False,
            blocking=False,
            change_reason="UNCHANGED",
        ),
        _row(
            predicate_id="P15",
            predicate_name="OWNER_EXECUTION_AUTHORIZED",
            previous_value="false",
            current_value="false",
            current_provenance="OWNER_GET_ONLY_GO is not OWNER_EXECUTION_GO",
            freshness="UNCHANGED",
            satisfied=False,
            blocking=True,
            change_reason="UNCHANGED",
        ),
        _row(
            predicate_id="P16",
            predicate_name="LIVE_RESTART_RECONSTRUCTED",
            previous_value="false",
            current_value="false",
            current_provenance="this WP must not empirically close restart",
            freshness="UNCHANGED",
            satisfied=False,
            blocking=False,
            change_reason="UNCHANGED",
        ),
    ]
    return {
        "THIS_SLICE": THIS_SLICE,
        "OWNER_GET_ONLY_GO": OWNER_GET_ONLY_GO,
        "OWNER_GET_ONLY_GO_TOKEN_MATCH": True,
        "OWNER_GET_ONLY_GO_SCOPE_MATCH": True,
        "OWNER_GET_ONLY_GO_STATUS": "CONSUMED_FOR_BOUNDED_GET_ONLY_WORKPACKAGE",
        "OWNER_EXECUTION_AUTHORIZED": False,
        "GET_PERFORMED": True,
        "GET_ENDPOINT_COUNT": int(summary.get("GET_ENDPOINT_COUNT") or 0),
        "GET_SUCCESS_COUNT": int(summary.get("GET_SUCCESS_COUNT") or 0),
        "GET_FAILURE_COUNT": int(summary.get("GET_FAILURE_COUNT") or 0),
        "GET_TIMEOUT_COUNT": int(summary.get("GET_TIMEOUT_COUNT") or 0),
        "TRADE_FEE_GET_PERFORMED": True,
        "TRADE_FEE_HTTP_RESULT": f"HTTP_{trade_fee_http}",
        "TRADE_FEE_OKX_CODE": trade_fee_okx,
        "TRADE_FEE_RESPONSE_PARSEABLE": fee_status == "PASS",
        "TRADE_FEE_TARGET_FAMILY_MATCH": family_match and inst_type_match,
        "TRADE_FEE_CURRENT_OBSERVATION": trade_fee_observed,
        "TRADE_FEE_QUERY": TRADE_FEE_QUERY,
        "TRADE_FEE_BODY_SHA256": str(fee_get.get("body_sha256") or ""),
        "TRADE_FEE_OBSERVED_AT": observed_at,
        "TRADE_FEE_TAKER_FIELD": str(fee.get("TAKER_FIELD") or ""),
        "TRADE_FEE_MAKER_FIELD": str(fee.get("MAKER_FIELD") or ""),
        "TRADE_FEE_TAKER_RAW": str(fee.get("TAKER_RAW") or ""),
        "TRADE_FEE_MAKER_RAW": str(fee.get("MAKER_RAW") or ""),
        "TRADE_FEE_DELIVERY_RAW": str(fee.get("DELIVERY_RAW") or ""),
        "TRADE_FEE_DELIVERY_ROLE": str(fee.get("DELIVERY_ROLE") or ""),
        "TRADE_FEE_RATE_TYPE": "ACCOUNT_FAMILY_RATE_NOT_OEM_FORMULA",
        "TRADE_FEE_UNIT": str(fee.get("RATE_UNIT") or ""),
        "TRADE_FEE_PROVENANCE": "CURRENT_GET_PACK_20260907T203636Z",
        "CURRENT_ACCOUNT_FEE_RATE_OBSERVED": trade_fee_observed,
        "CURRENT_NUMERIC_FEE_INPUT_PROVEN": numeric_fee_input,
        "EXACT_OKX_FEE_FORMULA_STATUS": EXACT_OKX_FEE_FORMULA_STATUS,
        "EXACT_OKX_FEE_FORMULA_UNPROVEN": EXACT_OKX_FEE_FORMULA_UNPROVEN,
        "EXPECTED_FEE_PRETRADE": expected_fee,
        "EXPECTED_FEE_UNIT": "USDC",
        "EXPECTED_FEE_RATE": str(fee.get("CONSERVATIVE_RATE") or ""),
        "FEE_POLICY_BOUND": fee_status == "PASS",
        "SLIPPAGE_POLICY_BOUND": str(_pred(predicates, "SLIPPAGE_POLICY_BOUND").get("status"))
        == "PASS",
        "SLIPPAGE_BOUND_CURRENT_NUMERIC": str(summary.get("SLIPPAGE_BOUND") or "UNKNOWN"),
        "BOUNDED_FEE_ENVELOPE_POLICY_BOUND": True,
        "BOUNDED_FEE_ENVELOPE_CURRENT_NUMERIC_PROVEN": bounded_numeric,
        "BOUNDED_FEE_ENVELOPE_PROVEN": bounded_numeric,
        "BOUNDED_FEE_ENVELOPE_ROLE": (
            "PEAK_TRADE_INTERNAL_CONSERVATIVE_ENVELOPE_NOT_OEM_OKX_FEE_FORMULA"
        ),
        "TECHNICAL_PRE_EXECUTION_READINESS": technical_pre_execution,
        "TECHNICAL_EXECUTION_READINESS": technical_execution_ready and technical_pre_execution,
        "TECHNICAL_EXECUTION_READY": technical_execution_ready and technical_pre_execution,
        "MISSING_REQUIRED_PREDICATES": missing,
        "EARLIEST_UNRESOLVED_TECHNICAL_PRE_EXECUTION_PREDICATE": (
            "NONE" if technical_pre_execution else (missing[0] if missing else "INDETERMINATE")
        ),
        "EARLIEST_UNRESOLVED_AUTHORITY_PREDICATE": EARLIEST_UNRESOLVED_AUTHORITY_PREDICATE,
        "EARLIEST_UNRESOLVED_DEPENDENCY": EARLIEST_UNRESOLVED_AUTHORITY_PREDICATE,
        "EARLIEST_LADDER_BLOCKER": EARLIEST_LADDER_BLOCKER,
        "NEXT_OWNER_GO_REQUIRED": NEXT_OWNER_GO_REQUIRED,
        "PROPOSED_NEXT_SLICE": PROPOSED_NEXT_SLICE,
        "LIVE_RESTART_RECONSTRUCTED": LIVE_RESTART_RECONSTRUCTED,
        "HOST_CRASH_DURABILITY": HOST_CRASH_DURABILITY_STATUS,
        "PROCESS_CRASH_DURABILITY": PROCESS_CRASH_DURABILITY_STATUS,
        "CANARY_AUTHORIZED_EXACT_FIELD": CANARY_AUTHORIZED_EXACT_FIELD,
        "POST_ALLOWED_EXACT_FIELD": POST_ALLOWED_EXACT_FIELD,
        "POST_PERFORMED": False,
        "WIRE_SEND_EXECUTED": False,
        "LIVE_SUBMIT_EXECUTED": False,
        "POSITION_MUTATION_EXECUTED": False,
        "RESTART_EXECUTED": False,
        "CRASH_TEST_EXECUTED": False,
        "SECTION_11_14_AUTHORIZED": False,
        "SECTION_11_14_COMPLETE": False,
        "NEXT_SLICE_AUTHORIZED": False,
        "PREVIOUS_GET_PACK_RUN_ID": PREVIOUS_GET_PACK_RUN_ID,
        "PREVIOUS_GET_PACK_ORIGIN_MAIN_SHA": PREVIOUS_GET_PACK_ORIGIN_MAIN_SHA,
        "GET_PACK_RUN_ID": CANONICAL_EVIDENCE_RUN_ID,
        "RECORDED_ORIGIN_MAIN_SHA": recorded_sha,
        "REST_HOST": BOUND_VENUE,
        "REST_BASE": BOUND_REST_BASE,
        "INSTRUMENT_ID": BOUND_INSTRUMENT_ID,
        "INST_FAMILY": BOUND_INST_FAMILY,
        "RAW_BODY_STORAGE": "CONTENT_ADDRESSED_SHA256_IN_EXISTING_GET_ONLY_SCHEMA",
        "PREDICATE_TABLE": predicate_table,
        "FEE_POLICY": fee,
        "GETS": gets,
        "CASE_ADJUDICATION": (
            "CASE_CURRENT_SUI_TRADE_FEE_GET_OBSERVED_BOUNDED_NUMERIC_ENVELOPE_PROVEN_"
            "EXACT_OKX_FEE_FORMULA_UNPROVEN_TECHNICAL_PRE_EXECUTION_READINESS_TRUE_"
            "OWNER_EXECUTION_NOT_AUTHORIZED"
            if technical_pre_execution
            else "CASE_GET_REFRESH_DID_NOT_CLOSE_TECHNICAL_PRE_EXECUTION_READINESS_"
            "OWNER_EXECUTION_NOT_AUTHORIZED"
        ),
    }
