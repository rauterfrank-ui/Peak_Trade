"""GET-only §11.14 flatten SELL preflight. Ten GETs. No POST. No Owner-GO consume."""

from __future__ import annotations

import hashlib
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INST_FAMILY,
    DEFAULT_INSTRUMENT_ID,
    REQUIRED_SECRETREF_URI,
    REUSED_BINDING_REST_HOST,
    public_instruments_query_path_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_limit_price_contract_v1 import (
    FlattenPriceInputV1,
    evaluate_canary_flatten_limit_price_contract_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.leverage_observation_v1 import (
    account_leverage_info_query_path_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.live_credential_ephemeral_v1 import (
    LiveCanaryCredentialError,
    assert_no_plaintext_in_payload_v1,
    build_file_secretref_vault_backend_v1,
    release_live_canary_ephemeral_material_v1,
    resolve_and_load_live_canary_secretref_ephemeral_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.max_available_observation_v1 import (
    account_max_size_query_path_v1,
    acquire_fresh_max_available_observation_from_payload_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.order_plan_v1 import (
    extract_instrument_constraints_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.pos_mode_observation_v1 import (
    account_config_query_path_v1,
    acquire_fresh_pos_mode_observation_from_payload_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.pre_submit_state_v1 import (
    LiveCanaryPreSubmitStateError,
    open_order_instruments_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.price_band_observation_v1 import (
    acquire_fresh_price_band_observation_from_payload_v1,
    public_price_limit_query_path_v1,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.constants_v1 import (
    ACCOUNT_MODE_REQUIRED,
    CAPABILITY_ID,
    ENDPOINT_PATH_ALLOWLIST,
    EXPECTED_SIGNED_POSITION,
    INSTRUMENT_ID,
    MARGIN_MODE,
    ORDER_TYPE,
    PATH_ACCOUNT_BALANCE,
    PATH_ACCOUNT_POSITIONS,
    PATH_MARKET_TICKER,
    PATH_ORDERS_PENDING,
    POS_MODE_REQUIRED,
    POS_SIDE_OBSERVED,
    PRIVATE_ENDPOINT_PATHS,
    PUBLIC_ENDPOINT_PATHS,
    REST_SCHEME_HOST,
    SCHEMA_VERSION,
    TD_MODE,
    THIS_SLICE,
    USER_AGENT,
    VENUE_REDUCE_ONLY_NO_FLIP,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.envelope_v1 import (
    FlattenSellEnvelopeError,
    build_flatten_sell_envelope_v1,
    extract_flatten_ticker_quotes_v1,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.get_only_http_v1 import (
    FlattenGetOnlyHttpClientV1,
    FlattenGetOnlyHttpError,
    FlattenGetOnlyTransportV1,
    UrllibFlattenGetOnlyTransportV1,
    endpoint_path_v1,
    parse_json_object_v1,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.persist_v1 import (
    persist_flatten_get_only_evidence_v1,
)
from src.ops.section_11_14_live_handoff_current_origin_main_bound_get_only_pretrade_readiness_v1.orchestrator_v1 import (
    build_get_only_auth_headers_v1,
    extract_pre_existing_position_v1,
)
from src.ops.section_11_14_live_handoff_standing_fee_slippage_and_exact_execution_envelope_v1.fee_policy_v1 import (
    StandingFeePolicyError,
    bind_standing_fee_policy_from_trade_fee_payload_v1,
    trade_fee_query_path_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    CANARY_AUTHORIZED,
    LIVE_ARMED,
    LIVE_ENABLED,
    POST_ALLOWED,
    SECTION_11_14_RUNTIME_EXECUTION_AUTHORIZED,
)


class FlattenGetOnlyPreflightError(RuntimeError):
    """Fail-closed flatten GET-only preflight violation."""


HeaderProvider = Callable[[str], Mapping[str, str]]


def utc_now_iso_v1() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def assert_standing_live_flags_remain_false_v1() -> dict[str, bool]:
    flags = {
        "LIVE_ENABLED": bool(LIVE_ENABLED),
        "LIVE_ARMED": bool(LIVE_ARMED),
        "CANARY_AUTHORIZED": bool(CANARY_AUTHORIZED),
        "SECTION_11_14_RUNTIME_EXECUTION_AUTHORIZED": bool(
            SECTION_11_14_RUNTIME_EXECUTION_AUTHORIZED
        ),
        "POST_ALLOWED": bool(POST_ALLOWED),
    }
    if any(flags.values()):
        raised = ",".join(name for name, value in flags.items() if value)
        raise FlattenGetOnlyPreflightError(f"STANDING_LIVE_FLAG_MUST_REMAIN_FALSE:{raised}")
    return flags


def _one_get(
    *,
    client: FlattenGetOnlyHttpClientV1,
    endpoint: str,
    headers: Mapping[str, str] | None,
) -> dict[str, Any]:
    observed = utc_now_iso_v1()
    path = endpoint_path_v1(endpoint)
    try:
        response = client.get(endpoint=endpoint, headers=headers)
    except FlattenGetOnlyHttpError as exc:
        timeout = "INDETERMINATE_TIMEOUT" in str(exc)
        return {
            "endpoint": endpoint,
            "observed_at_utc": observed,
            "http_status": None,
            "venue_code": "",
            "body_sha256": "",
            "payload": None,
            "error": str(exc),
            "timeout": timeout,
            "auth_header_sent": path in PRIVATE_ENDPOINT_PATHS,
            "method": "GET",
        }
    digest = hashlib.sha256(response.body_bytes).hexdigest()
    try:
        payload = parse_json_object_v1(response.body_bytes)
        venue_code = str(payload.get("code") or "")
        error = ""
    except FlattenGetOnlyHttpError as exc:
        payload = None
        venue_code = ""
        error = str(exc)
    return {
        "endpoint": endpoint,
        "observed_at_utc": observed,
        "http_status": int(response.status_code),
        "venue_code": venue_code,
        "body_sha256": digest,
        "payload": payload,
        "error": error,
        "timeout": False,
        "auth_header_sent": path in PRIVATE_ENDPOINT_PATHS,
        "method": "GET",
    }


def _headers_for(
    *,
    endpoint: str,
    rest_base: str,
    header_provider: HeaderProvider | None,
) -> Mapping[str, str] | None:
    path = endpoint_path_v1(endpoint)
    if path in PUBLIC_ENDPOINT_PATHS:
        return {"User-Agent": USER_AGENT}
    if header_provider is None:
        raise FlattenGetOnlyPreflightError(f"PRIVATE_HEADER_PROVIDER_REQUIRED:{path}")
    return header_provider(f"{rest_base.rstrip('/')}{endpoint}")


def evaluate_pending_order_gate_v1(
    *,
    payload: Mapping[str, Any] | None,
    instrument_id: str,
) -> dict[str, Any]:
    if payload is None:
        return {
            "PENDING_ORDERS_OBSERVED": False,
            "TARGET_INSTRUMENT_PENDING_ORDER_COUNT": "UNKNOWN",
            "PENDING_ORDER_COMPATIBLE_WITH_FLATTEN": "UNKNOWN",
            "PENDING_ORDER_GATE_PASS": False,
            "reason": "PENDING_PAYLOAD_MISSING",
        }
    try:
        instruments = open_order_instruments_v1(payload)
    except LiveCanaryPreSubmitStateError as exc:
        return {
            "PENDING_ORDERS_OBSERVED": False,
            "TARGET_INSTRUMENT_PENDING_ORDER_COUNT": "UNKNOWN",
            "PENDING_ORDER_COMPATIBLE_WITH_FLATTEN": "UNKNOWN",
            "PENDING_ORDER_GATE_PASS": False,
            "reason": str(exc),
        }
    target_count = sum(1 for inst in instruments if inst == instrument_id)
    empty_ok = str(payload.get("code") or "") == "0" and isinstance(payload.get("data"), list)
    compatible = len(instruments) == 0
    return {
        "PENDING_ORDERS_OBSERVED": True,
        "TARGET_INSTRUMENT_PENDING_ORDER_COUNT": target_count,
        "ACCOUNT_PENDING_ORDER_COUNT": len(instruments),
        "PENDING_ORDER_COMPATIBLE_WITH_FLATTEN": compatible,
        "PENDING_ORDER_GATE_PASS": compatible,
        "EMPTY_DATA_MEANS_ZERO_PENDING_ROWS": empty_ok and len(instruments) == 0,
        "reason": "" if compatible else "OPEN_ORDER_PRESENT",
    }


def run_flatten_get_only_preflight_v1(
    *,
    origin_main_sha: str,
    transport: FlattenGetOnlyTransportV1,
    header_provider: HeaderProvider | None = None,
    origin_main_tree: str = "",
    rest_host: str = REUSED_BINDING_REST_HOST,
    rest_base: str = REST_SCHEME_HOST,
    persist_root: Path | str | None = None,
) -> dict[str, Any]:
    """Mint a current Flatten SELL envelope from GET-only observations. No POST."""
    flags = assert_standing_live_flags_remain_false_v1()
    sha = str(origin_main_sha or "").strip().lower()
    if len(sha) != 40 or any(ch not in "0123456789abcdef" for ch in sha):
        raise FlattenGetOnlyPreflightError("ORIGIN_MAIN_SHA_REQUIRED")
    if rest_host != REUSED_BINDING_REST_HOST:
        raise FlattenGetOnlyPreflightError(f"REST_HOST_NOT_PRODUCTION_EEA:{rest_host}")
    if INSTRUMENT_ID != DEFAULT_INSTRUMENT_ID:
        raise FlattenGetOnlyPreflightError("INSTRUMENT_BINDING_DRIFT")
    client = FlattenGetOnlyHttpClientV1(transport=transport, rest_base=rest_base)
    gets: list[dict[str, Any]] = []
    decision = f"{CAPABILITY_ID}:{sha[:12]}"
    final_action = ""
    envelope: dict[str, Any] | None = None
    envelope_error = ""
    position_state = "UNKNOWN"
    pos_raw = ""
    pos_side = ""
    mgn_mode = ""

    def do_get(name: str, endpoint: str) -> dict[str, Any]:
        attempt = _one_get(
            client=client,
            endpoint=endpoint,
            headers=_headers_for(
                endpoint=endpoint, rest_base=rest_base, header_provider=header_provider
            ),
        )
        public = {k: v for k, v in attempt.items() if k != "payload"}
        public["name"] = name
        gets.append(public)
        return attempt

    inst_ep = public_instruments_query_path_v1(instrument_id=INSTRUMENT_ID)
    ticker_ep = f"{PATH_MARKET_TICKER}?instId={INSTRUMENT_ID}"
    band_ep = public_price_limit_query_path_v1(instrument_id=INSTRUMENT_ID)
    config_ep = account_config_query_path_v1()
    balance_ep = PATH_ACCOUNT_BALANCE
    positions_ep = PATH_ACCOUNT_POSITIONS
    leverage_ep = account_leverage_info_query_path_v1(
        instrument_id=INSTRUMENT_ID, mgn_mode=MARGIN_MODE
    )
    fee_ep = trade_fee_query_path_v1(inst_family=DEFAULT_INST_FAMILY)

    inst_attempt = do_get("INSTRUMENTS", inst_ep)
    ticker_attempt = do_get("TICKER", ticker_ep)
    band_attempt = do_get("PRICE_LIMIT", band_ep)
    config_attempt = do_get("ACCOUNT_CONFIG", config_ep)
    balance_attempt = do_get("BALANCE", balance_ep)
    pos_attempt = do_get("POSITIONS", positions_ep)

    tick_sz = ""
    ct_val = ""
    if inst_attempt.get("payload") and inst_attempt.get("http_status") == 200:
        try:
            constraints = extract_instrument_constraints_v1(
                instruments_payload=inst_attempt["payload"],
                instrument_id=INSTRUMENT_ID,
            )
            tick_sz = str(constraints.get("tickSz") or "")
            ct_val = str(constraints.get("ctVal") or "")
        except Exception as exc:  # noqa: BLE001
            envelope_error = str(exc)

    quotes: dict[str, str] = {}
    if ticker_attempt.get("payload") and ticker_attempt.get("http_status") == 200:
        try:
            quotes = extract_flatten_ticker_quotes_v1(ticker_payload=ticker_attempt["payload"])
        except FlattenSellEnvelopeError as exc:
            envelope_error = envelope_error or str(exc)

    sell_lmt = ""
    if band_attempt.get("payload") and band_attempt.get("http_status") == 200:
        try:
            band_obs = acquire_fresh_price_band_observation_from_payload_v1(
                pretrade_decision_id=decision,
                payload=band_attempt["payload"],
                instrument_id=INSTRUMENT_ID,
                observed_at_utc=str(band_attempt["observed_at_utc"]),
                endpoint=band_ep,
                http_status=int(band_attempt["http_status"] or 0),
                get_performed=True,
                rest_host=rest_host,
                auth_header_sent=False,
                historical_reuse=False,
                body_sha256=str(band_attempt["body_sha256"]),
            )
            sell_lmt = str(band_obs.sell_lmt_raw)
        except Exception as exc:  # noqa: BLE001
            envelope_error = envelope_error or str(exc)

    pos_mode = ""
    acct_lv = ""
    if config_attempt.get("payload") and config_attempt.get("http_status") == 200:
        try:
            cfg = acquire_fresh_pos_mode_observation_from_payload_v1(
                pretrade_decision_id=decision,
                payload=config_attempt["payload"],
                instrument_id=INSTRUMENT_ID,
                observed_at_utc=str(config_attempt["observed_at_utc"]),
                endpoint=config_ep,
                http_status=int(config_attempt["http_status"] or 0),
                get_performed=True,
                rest_host=rest_host,
                auth_header_sent=True,
                historical_reuse=False,
                body_sha256=str(config_attempt["body_sha256"]),
            )
            pos_mode = str(cfg.pos_mode_raw)
            acct_lv = str(cfg.acct_lv_raw) if hasattr(cfg, "acct_lv_raw") else ""
            data = (config_attempt["payload"] or {}).get("data") or []
            if isinstance(data, list) and data and isinstance(data[0], Mapping):
                acct_lv = str(data[0].get("acctLv") or acct_lv)
                pos_mode = str(data[0].get("posMode") or pos_mode)
        except Exception as exc:  # noqa: BLE001
            envelope_error = envelope_error or str(exc)

    if pos_attempt.get("payload") and pos_attempt.get("http_status") == 200:
        extracted = extract_pre_existing_position_v1(
            payload=pos_attempt["payload"], instrument_id=INSTRUMENT_ID
        )
        position_state = str(extracted.get("status") or "UNKNOWN")
        pos_raw = str(extracted.get("pos") or "")
        pos_side = str(extracted.get("posSide") or "")
        data = pos_attempt["payload"].get("data")
        if isinstance(data, list):
            rows = [
                item
                for item in data
                if isinstance(item, Mapping) and str(item.get("instId") or "") == INSTRUMENT_ID
            ]
            if len(rows) == 1:
                mgn_mode = str(rows[0].get("mgnMode") or "")

    if pos_raw != EXPECTED_SIGNED_POSITION:
        final_action = "HARD_STOP_POSITION_STATE_CHANGED_REQUIRES_NEW_ADJUDICATION"
    elif pos_side != POS_SIDE_OBSERVED or mgn_mode != MARGIN_MODE:
        final_action = "HARD_STOP_POSITION_STATE_CHANGED_REQUIRES_NEW_ADJUDICATION"
    elif pos_mode and pos_mode != POS_MODE_REQUIRED:
        final_action = "HARD_STOP_POSITION_STATE_CHANGED_REQUIRES_NEW_ADJUDICATION"
    elif acct_lv and acct_lv != ACCOUNT_MODE_REQUIRED:
        final_action = "HARD_STOP_POSITION_STATE_CHANGED_REQUIRES_NEW_ADJUDICATION"

    pending_gate = {
        "PENDING_ORDERS_OBSERVED": False,
        "TARGET_INSTRUMENT_PENDING_ORDER_COUNT": "UNKNOWN",
        "PENDING_ORDER_COMPATIBLE_WITH_FLATTEN": "UNKNOWN",
        "PENDING_ORDER_GATE_PASS": False,
        "reason": "NOT_SAMPLED",
    }
    max_sell = ""
    flatten_px = ""
    fee_policy = None
    if not final_action:
        do_get("LEVERAGE", leverage_ep)
        fee_attempt = do_get("TRADE_FEE", fee_ep)
        if fee_attempt.get("payload") and fee_attempt.get("http_status") == 200:
            try:
                fee_policy = bind_standing_fee_policy_from_trade_fee_payload_v1(
                    payload=fee_attempt["payload"],
                    instrument_id=INSTRUMENT_ID,
                )
            except StandingFeePolicyError as exc:
                envelope_error = envelope_error or str(exc)

        eval_ts = str(int(time.time() * 1000))
        try:
            px_decision = evaluate_canary_flatten_limit_price_contract_v1(
                FlattenPriceInputV1(
                    flatten_side="SELL",
                    observed_signed_pos=pos_raw,
                    bid=quotes.get("bidPx"),
                    ask=quotes.get("askPx"),
                    quote_timestamp_ms=quotes.get("ts"),
                    evaluation_timestamp_ms=eval_ts,
                    tick_sz=tick_sz,
                )
            )
            if px_decision.permit_issued and px_decision.permit is not None:
                flatten_px = px_decision.permit.limit_price
            else:
                envelope_error = envelope_error or (
                    "FLATTEN_LIMIT_PRICE_DENIED:" + ",".join(px_decision.reject_reasons)
                )
        except Exception as exc:  # noqa: BLE001
            envelope_error = envelope_error or str(exc)

        if flatten_px:
            max_ep = account_max_size_query_path_v1(
                instrument_id=INSTRUMENT_ID,
                td_mode=TD_MODE,
                px=flatten_px,
                order_type=ORDER_TYPE,
            )
            max_attempt = do_get("MAX_SIZE", max_ep)
            if max_attempt.get("payload") and max_attempt.get("http_status") == 200:
                try:
                    max_obs = acquire_fresh_max_available_observation_from_payload_v1(
                        pretrade_decision_id=decision,
                        payload=max_attempt["payload"],
                        instrument_id=INSTRUMENT_ID,
                        td_mode=TD_MODE,
                        px_sent=flatten_px,
                        order_type=ORDER_TYPE,
                        observed_at_utc=str(max_attempt["observed_at_utc"]),
                        endpoint=max_ep,
                        http_status=int(max_attempt["http_status"] or 0),
                        get_performed=True,
                        rest_host=rest_host,
                        auth_header_sent=True,
                        historical_reuse=False,
                        body_sha256=str(max_attempt["body_sha256"]),
                    )
                    max_sell = str(max_obs.max_sell_raw)
                except Exception as exc:  # noqa: BLE001
                    envelope_error = envelope_error or str(exc)

        pending_attempt = do_get("ORDERS_PENDING", PATH_ORDERS_PENDING)
        pending_gate = evaluate_pending_order_gate_v1(
            payload=pending_attempt.get("payload"),
            instrument_id=INSTRUMENT_ID,
        )

        if (
            not envelope_error
            and fee_policy is not None
            and flatten_px
            and max_sell
            and pending_gate.get("PENDING_ORDER_GATE_PASS") is True
        ):
            try:
                envelope = build_flatten_sell_envelope_v1(
                    origin_main_sha=sha,
                    signed_pos=pos_raw,
                    pos_side=pos_side,
                    margin_mode=mgn_mode,
                    bid=quotes.get("bidPx") or "",
                    ask=quotes.get("askPx") or "",
                    last=quotes.get("last") or "",
                    quote_ts_ms=quotes.get("ts") or "",
                    evaluation_ts_ms=eval_ts,
                    tick_sz=tick_sz,
                    sell_lmt=sell_lmt,
                    max_sell=max_sell,
                    max_sell_px_sent=flatten_px,
                    ct_val=ct_val,
                    fee_policy=fee_policy,
                    pending_order_count=int(pending_gate.get("ACCOUNT_PENDING_ORDER_COUNT") or 0),
                    pending_order_gate_pass=True,
                )
            except FlattenSellEnvelopeError as exc:
                envelope_error = str(exc)

    methods_used = {str(item.get("method") or "") for item in gets}
    if methods_used - {"GET"}:
        raise FlattenGetOnlyPreflightError("NON_GET_METHOD_RECORDED")
    post_performed = False
    get_success = sum(
        1 for item in gets if item.get("http_status") == 200 and item.get("venue_code") == "0"
    )
    get_timeout = sum(1 for item in gets if item.get("timeout"))
    summary = {
        "SCHEMA_VERSION": SCHEMA_VERSION,
        "THIS_SLICE": THIS_SLICE,
        "CAPABILITY_ID": CAPABILITY_ID,
        "CURRENT_ORIGIN_MAIN_SHA": sha,
        "CURRENT_ORIGIN_MAIN_TREE": str(origin_main_tree or ""),
        "CURRENT_POSITION": (
            f"instId={INSTRUMENT_ID},pos={pos_raw or 'UNKNOWN'},"
            f"posSide={pos_side or 'UNKNOWN'},mgnMode={mgn_mode or 'UNKNOWN'}"
        ),
        "CURRENT_POSITION_STATE": position_state,
        "CURRENT_POSITION_FLAT": pos_raw == "0",
        "CURRENT_BID": quotes.get("bidPx") or "",
        "CURRENT_ASK": quotes.get("askPx") or "",
        "CURRENT_LAST": quotes.get("last") or "",
        "CURRENT_QUOTE_TS": quotes.get("ts") or "",
        "CURRENT_SELL_LIMIT": flatten_px,
        "CURRENT_SELL_PRICE_LIMIT": sell_lmt,
        "CURRENT_MAX_SELL_AT_FLATTEN_PRICE": max_sell,
        "CURRENT_FEE_RATE": (fee_policy.conservative_rate if fee_policy is not None else ""),
        "CURRENT_EXPECTED_FEE": (
            ((envelope or {}).get("EXPECTED_FEE") or {}).get("FEE_AMOUNT_CONSERVATIVE")
            if envelope
            else ""
        ),
        "CURRENT_PENDING_ORDER_COUNT": pending_gate.get("ACCOUNT_PENDING_ORDER_COUNT", "UNKNOWN"),
        "FLATTEN_ENVELOPE_ID": (envelope or {}).get("FLATTEN_ENVELOPE_ID") or "",
        "FLATTEN_ORDER_ENVELOPE_CURRENT": envelope is not None,
        "FLATTEN_SIDE": (envelope or {}).get("SIDE") or "",
        "FLATTEN_QTY": (envelope or {}).get("QTY") or "",
        "FLATTEN_REDUCE_ONLY": (envelope or {}).get("REDUCE_ONLY"),
        "FLATTEN_LIMIT_PRICE": (envelope or {}).get("LIMIT_PRICE") or flatten_px,
        "FLATTEN_MAX_SELL": max_sell,
        "GET_ENDPOINT_COUNT": len(gets),
        "GET_SUCCESS_COUNT": get_success,
        "GET_TIMEOUT_COUNT": get_timeout,
        "GET_ONLY_ENDPOINT_ALLOWLIST": list(ENDPOINT_PATH_ALLOWLIST),
        "OWNER_GO_CONSUMED": False,
        "OWNER_GO_PARAMETER_PRESENT": False,
        "SESSION_ARMED": False,
        "POST_PERFORMED": post_performed,
        "WIRE_SEND_EXECUTED": False,
        "POSITION_MUTATION_EXECUTED": False,
        "FLATTEN_EXECUTED": False,
        "STANDING_FLAGS": flags,
        "VENUE_REDUCE_ONLY_NO_FLIP": VENUE_REDUCE_ONLY_NO_FLIP,
        "ENVELOPE_ERROR": envelope_error,
        "FINAL_ACTION": final_action,
        **pending_gate,
    }
    non_execution = {
        "POST_PERFORMED": False,
        "WIRE_SEND_EXECUTED": False,
        "POSITION_MUTATION_EXECUTED": False,
        "FLATTEN_EXECUTED": False,
        "OWNER_TOKEN_CONSUMED": False,
        "SESSION_ARMING": False,
        "METHODS_USED": sorted(methods_used),
    }
    claims = {
        "GET_ONLY": True,
        "MUTATION_VERBS_IMPOSSIBLE": True,
        "OWNER_GO_NOT_CONSUMED": True,
        "SESSION_NOT_ARMED": True,
        "CURRENT_SHA_RECORDED": True,
        "FLATTEN_SELL_ENVELOPE_DISTINCT_FROM_ENTRY_BUY": True,
    }
    adjudication = {
        "FINAL_ACTION": final_action
        or (
            "FLATTEN_GET_ONLY_PREFLIGHT_COMPLETE"
            if envelope is not None
            else "FLATTEN_GET_ONLY_PREFLIGHT_INCOMPLETE"
        ),
        "FLATTEN_AUTHORIZED": False,
        "OWNER_EXECUTION_AUTHORIZED": False,
    }
    summary["FINAL_ACTION"] = str(adjudication["FINAL_ACTION"])
    lineage = {
        "origin_main_sha": sha,
        "predecessor_slice": THIS_SLICE,
        "historical_reuse": False,
    }
    persist_meta: dict[str, Any] = {}
    if persist_root is not None:
        persist_meta = persist_flatten_get_only_evidence_v1(
            persist_root=persist_root,
            summary=summary,
            claims=claims,
            adjudication=adjudication,
            gets={"GETS": gets},
            envelope=envelope,
            lineage=lineage,
            non_execution=non_execution,
        )
        summary["MANIFEST_VERIFY_RC"] = persist_meta.get("MANIFEST_VERIFY_RC")
        summary["EVIDENCE_ROOT"] = persist_meta.get("persist_root")
    assert_no_plaintext_in_payload_v1(summary)
    return {
        **summary,
        "GETS": gets,
        "FLATTEN_ENVELOPE": envelope,
        "PERSIST": persist_meta,
        "CLIENT_COUNTERS": client.counters.to_dict(),
    }


def execute_flatten_get_only_preflight_v1(
    *,
    vault_file: Path | str,
    origin_main_sha: str,
    origin_main_tree: str = "",
    persist_root: Path | str | None = None,
    secret_reference: str = REQUIRED_SECRETREF_URI,
    transport: FlattenGetOnlyTransportV1 | None = None,
) -> dict[str, Any]:
    handle = None
    try:
        vault = build_file_secretref_vault_backend_v1(vault_file=vault_file)
        handle = resolve_and_load_live_canary_secretref_ephemeral_v1(
            secret_reference=secret_reference,
            vault_backend=vault,
        )

        def header_provider(url: str) -> Mapping[str, str]:
            return build_get_only_auth_headers_v1(handle=handle, url=url, method="GET")

        return run_flatten_get_only_preflight_v1(
            origin_main_sha=origin_main_sha,
            origin_main_tree=origin_main_tree,
            transport=transport or UrllibFlattenGetOnlyTransportV1(),
            header_provider=header_provider,
            persist_root=persist_root,
        )
    except LiveCanaryCredentialError as exc:
        raise FlattenGetOnlyPreflightError(f"CREDENTIAL_RESOLVE_FAILED:{exc}") from exc
    finally:
        if handle is not None:
            release_live_canary_ephemeral_material_v1(handle)
