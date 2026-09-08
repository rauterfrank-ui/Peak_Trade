"""§11.14 Envelope reprice or freshness-at-send.

Rebuilds a Flatten SELL envelope from fresh GET-only producer inputs when
the frozen LIMIT is not quote-locked. Does not mint/bind/attach a receipt.
Does not HMAC-sign a POST. Does not consume a lease. Does not HTTP POST.
Does not invoke productive inner.send.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Callable, Mapping

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INST_FAMILY,
    DEFAULT_INSTRUMENT_ID,
    REQUIRED_SECRETREF_URI,
    REUSED_BINDING_REST_HOST,
    public_instruments_query_path_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.evidence_v1 import (
    verify_manifest_v1,
    write_json_v1,
    write_manifest_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_limit_price_contract_v1 import (
    FRESHNESS_THRESHOLD_MS,
    FlattenPriceInputV1,
    evaluate_canary_flatten_limit_price_contract_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_pre_send_gate_v1 import (
    FlattenPreSendGateInputV1,
    evaluate_flatten_pre_send_gate_v1,
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
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.position_observation_freshness_contract_v1 import (
    PRE_SEND_EVIDENCE_KIND,
    PositionObservationFreshnessEvidenceV1,
    default_local_monotonic_ms_v1,
    evaluate_position_observation_freshness_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.pre_submit_state_v1 import (
    classify_target_position_state_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.price_band_observation_v1 import (
    acquire_fresh_price_band_observation_from_payload_v1,
    public_price_limit_query_path_v1,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.constants_v1 import (
    BOUND_FROZEN_ENVELOPE_ID,
    BOUND_FROZEN_EVIDENCE_RELATIVE,
    BOUND_ORIGIN_MAIN_SHA,
    DEFAULT_VAULT_RELATIVE,
    EXPECTED_SIGNED_POSITION,
    EXPECTED_VENUE_NATIVE_BODY,
    FLATTEN_HTTP_ENDPOINT,
    INSTRUMENT_ID,
    MARGIN_MODE,
    ORDER_TYPE,
    PATH_ACCOUNT_MAX_SIZE,
    PATH_ACCOUNT_POSITIONS,
    PATH_MARKET_TICKER,
    PATH_ORDERS_PENDING,
    PATH_PUBLIC_INSTRUMENTS,
    PATH_PUBLIC_PRICE_LIMIT,
    POS_SIDE_OBSERVED,
    REST_SCHEME_HOST,
    TD_MODE,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.envelope_v1 import (
    FlattenSellEnvelopeError,
    build_flatten_sell_envelope_v1,
    extract_flatten_ticker_quotes_v1,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.fresh_pre_submit_get_and_freshness_adjudication_v1 import (
    _headers_for,
    _one_get,
    _public_get_record,
    adjudicate_auth_session_contract_v1,
    assert_standing_live_flags_remain_false_v1,
    classify_envelope_freshness_v1,
    prove_get_path_cannot_post_v1,
    prove_place_order_get_is_blocked_v1,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.get_only_http_v1 import (
    FlattenGetOnlyHttpClientV1,
    FlattenGetOnlyHttpError,
    FlattenGetOnlyTransportV1,
    UrllibFlattenGetOnlyTransportV1,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.get_only_preflight_v1 import (
    evaluate_pending_order_gate_v1,
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

THIS_SLICE = "11.14.ENVELOPE_REPRICE_OR_FRESHNESS_AT_SEND"
PREDECESSOR_SLICE = "11.14.FRESH_PRE_SUBMIT_GET_AND_FRESHNESS_ADJUDICATION"
OWNER_GO = "ENVELOPE_REPRICE_OR_FRESHNESS_AT_SEND"
EXPECTED_ORIGIN_MAIN_SHA = "8b1fa60b9256ad28656946ac08d271b35d9fe602"
FROZEN_LIMIT_PX = str(EXPECTED_VENUE_NATIVE_BODY["px"])
FROZEN_ENVELOPE_ID = BOUND_FROZEN_ENVELOPE_ID
ROUNDING_RULE = "SELL_ROUND_DOWN_TO_TICK"
PRICE_BAND_RULE = "LIMIT_PX_MUST_BE_GTE_FRESH_SELL_LMT"
REPRICE_ALGORITHM_SOURCE = (
    "evaluate_canary_flatten_limit_price_contract_v1+build_flatten_sell_envelope_v1"
)

HeaderProvider = Callable[[str], Mapping[str, str]]


class EnvelopeRepriceOrFreshnessAtSendError(RuntimeError):
    """Fail-closed envelope reprice / freshness-at-send violation."""


def required_reprice_get_contract_v1() -> dict[str, Any]:
    instruments_ep = public_instruments_query_path_v1(instrument_id=INSTRUMENT_ID)
    ticker_ep = f"{PATH_MARKET_TICKER}?instId={INSTRUMENT_ID}"
    band_ep = public_price_limit_query_path_v1(instrument_id=INSTRUMENT_ID)
    fee_ep = trade_fee_query_path_v1(inst_family=DEFAULT_INST_FAMILY)
    return {
        "GET_CONTRACT_STATUS": "DEFINED",
        "REPRICE_CONTRACT_STATUS": "DEFINED",
        "REPRICE_ALGORITHM_SOURCE": REPRICE_ALGORITHM_SOURCE,
        "ENVELOPE_PRODUCER": "build_flatten_sell_envelope_v1",
        "PRICE_CONTRACT": "evaluate_canary_flatten_limit_price_contract_v1",
        "ROUNDING_RULE": ROUNDING_RULE,
        "PRICE_BAND_RULE": PRICE_BAND_RULE,
        "FRESHNESS_THRESHOLD_MS": FRESHNESS_THRESHOLD_MS,
        "SIDE_QUOTE_RULE": "SELL_SELECTS_BID",
        "ENVELOPE_REBUILD_SEMANTICS": "FULL_REBUILD_NEW_IDENTITY_NO_IN_PLACE_MUTATION",
        "ALTERNATIVE_FRESHNESS_PREDICATE": "VALID_WITH_FRESH_GET_WHEN_COMPUTED_EQUALS_FROZEN",
        "ALWAYS_REQUIRED_GET_ENDPOINTS": [
            instruments_ep,
            ticker_ep,
            band_ep,
            PATH_ACCOUNT_POSITIONS,
            fee_ep,
            PATH_ORDERS_PENDING,
        ],
        "CONDITIONAL_GET_ENDPOINTS": [
            f"{PATH_ACCOUNT_MAX_SIZE}?instId={INSTRUMENT_ID}&tdMode={TD_MODE}&px=<computed_limit>"
        ],
        "ALWAYS_REQUIRED_GET_COUNT": 6,
        "CONDITIONAL_GET_COUNT": 1,
        "MAX_GET_CALL_COUNT": 7,
        "NOT_REQUIRED_BY_ENVELOPE_PRODUCER": [
            "/api/v5/account/config",
            "/api/v5/account/balance",
            "/api/v5/account/leverage-info",
            "/api/v5/public/mark-price",
            "/api/v5/market/books",
        ],
        "HISTORICAL_VALUES_REUSED_AS_FRESH": False,
        "RECEIPT_MINT_FORBIDDEN": True,
        "HMAC_POST_FORBIDDEN": True,
        "POST_FORBIDDEN": True,
        "WIRE_SEND_FORBIDDEN": True,
    }


def _do_get(
    *,
    client: FlattenGetOnlyHttpClientV1,
    name: str,
    endpoint: str,
    rest_base: str,
    header_provider: HeaderProvider | None,
    gets: list[dict[str, Any]],
    payloads: dict[str, Any],
) -> dict[str, Any]:
    attempt = _one_get(
        client=client,
        name=name,
        endpoint=endpoint,
        headers=_headers_for(
            endpoint=endpoint, rest_base=rest_base, header_provider=header_provider
        ),
    )
    gets.append(_public_get_record(attempt))
    payloads[name] = attempt.get("payload")
    return attempt


def run_envelope_reprice_or_freshness_at_send_v1(
    *,
    origin_main_sha: str,
    transport: FlattenGetOnlyTransportV1,
    header_provider: HeaderProvider | None = None,
    origin_main_tree: str = "",
    rest_host: str = REUSED_BINDING_REST_HOST,
    rest_base: str = REST_SCHEME_HOST,
    persist_root: Path | str | None = None,
    vault_file: Path | str | None = None,
) -> dict[str, Any]:
    """Fresh GET-only reprice/freshness. Rebuilds envelope. Never POSTs."""
    flags = assert_standing_live_flags_remain_false_v1()
    sha = str(origin_main_sha or "").strip().lower()
    if len(sha) != 40 or any(ch not in "0123456789abcdef" for ch in sha):
        raise EnvelopeRepriceOrFreshnessAtSendError("ORIGIN_MAIN_SHA_REQUIRED")
    if rest_host != REUSED_BINDING_REST_HOST:
        raise EnvelopeRepriceOrFreshnessAtSendError(f"REST_HOST_NOT_PRODUCTION_EEA:{rest_host}")
    if INSTRUMENT_ID != DEFAULT_INSTRUMENT_ID:
        raise EnvelopeRepriceOrFreshnessAtSendError("INSTRUMENT_BINDING_DRIFT")
    session = adjudicate_auth_session_contract_v1(vault_file=vault_file)
    contract = required_reprice_get_contract_v1()
    client = FlattenGetOnlyHttpClientV1(transport=transport, rest_base=rest_base)
    post_block = prove_get_path_cannot_post_v1(client=client)
    place_order_block = prove_place_order_get_is_blocked_v1(client=client)

    gets: list[dict[str, Any]] = []
    payloads: dict[str, Any] = {}
    envelope: dict[str, Any] | None = None
    envelope_error = ""
    rebuild_executed = False
    reprice_executed = False
    sell_lmt = ""
    max_sell = ""
    tick_sz = ""
    ct_val = ""
    flatten_px = ""
    fee_policy = None

    inst_ep = public_instruments_query_path_v1(instrument_id=INSTRUMENT_ID)
    ticker_ep = f"{PATH_MARKET_TICKER}?instId={INSTRUMENT_ID}"
    band_ep = public_price_limit_query_path_v1(instrument_id=INSTRUMENT_ID)
    fee_ep = trade_fee_query_path_v1(inst_family=DEFAULT_INST_FAMILY)

    inst_attempt = _do_get(
        client=client,
        name="INSTRUMENTS",
        endpoint=inst_ep,
        rest_base=rest_base,
        header_provider=header_provider,
        gets=gets,
        payloads=payloads,
    )
    ticker_attempt = _do_get(
        client=client,
        name="TICKER",
        endpoint=ticker_ep,
        rest_base=rest_base,
        header_provider=header_provider,
        gets=gets,
        payloads=payloads,
    )
    band_attempt = _do_get(
        client=client,
        name="PRICE_LIMIT",
        endpoint=band_ep,
        rest_base=rest_base,
        header_provider=header_provider,
        gets=gets,
        payloads=payloads,
    )
    pos_attempt = _do_get(
        client=client,
        name="POSITIONS",
        endpoint=PATH_ACCOUNT_POSITIONS,
        rest_base=rest_base,
        header_provider=header_provider,
        gets=gets,
        payloads=payloads,
    )
    fee_attempt = _do_get(
        client=client,
        name="TRADE_FEE",
        endpoint=fee_ep,
        rest_base=rest_base,
        header_provider=header_provider,
        gets=gets,
        payloads=payloads,
    )

    if inst_attempt.get("payload") and inst_attempt.get("http_status") == 200:
        try:
            constraints = extract_instrument_constraints_v1(
                instruments_payload=inst_attempt["payload"],
                instrument_id=INSTRUMENT_ID,
            )
            tick_sz = str(constraints.get("tickSz") or "")
            ct_val = str(constraints.get("ctVal") or "")
        except Exception as exc:  # noqa: BLE001
            envelope_error = envelope_error or str(exc)

    quotes: dict[str, str] = {}
    if ticker_attempt.get("payload") and ticker_attempt.get("http_status") == 200:
        try:
            quotes = extract_flatten_ticker_quotes_v1(ticker_payload=ticker_attempt["payload"])
        except FlattenSellEnvelopeError as exc:
            envelope_error = envelope_error or str(exc)

    decision_id = f"{THIS_SLICE}:{sha[:12]}"
    if band_attempt.get("payload") and band_attempt.get("http_status") == 200:
        try:
            band_obs = acquire_fresh_price_band_observation_from_payload_v1(
                pretrade_decision_id=decision_id,
                payload=band_attempt["payload"],
                instrument_id=INSTRUMENT_ID,
                observed_at_utc=str(band_attempt["observed_at_utc"]),
                endpoint=band_ep,
                http_status=int(band_attempt["http_status"] or 0),
                get_performed=True,
                rest_host=str(rest_host),
                auth_header_sent=False,
                historical_reuse=False,
                body_sha256=str(band_attempt["body_sha256"]),
            )
            sell_lmt = str(band_obs.sell_lmt_raw)
        except Exception as exc:  # noqa: BLE001
            envelope_error = envelope_error or str(exc)

    pos_payload = payloads.get("POSITIONS")
    classified = classify_target_position_state_v1(
        positions_payload=pos_payload if isinstance(pos_payload, Mapping) else None,
        instrument_id=INSTRUMENT_ID,
    )
    extracted_pos = {"status": "NOT_SAMPLED", "pos": "", "posSide": "", "row_count": ""}
    mgn_mode = ""
    if isinstance(pos_payload, Mapping):
        extracted_pos = extract_pre_existing_position_v1(
            payload=pos_payload, instrument_id=INSTRUMENT_ID
        )
        data = pos_payload.get("data")
        if isinstance(data, list):
            rows = [
                item
                for item in data
                if isinstance(item, Mapping) and str(item.get("instId") or "") == INSTRUMENT_ID
            ]
            if len(rows) == 1:
                mgn_mode = str(rows[0].get("mgnMode") or "")

    if fee_attempt.get("payload") and fee_attempt.get("http_status") == 200:
        try:
            fee_policy = bind_standing_fee_policy_from_trade_fee_payload_v1(
                payload=fee_attempt["payload"],
                instrument_id=INSTRUMENT_ID,
            )
        except StandingFeePolicyError as exc:
            envelope_error = envelope_error or str(exc)

    eval_ts_ms = str(int(time.time() * 1000))
    eval_mono_ms = default_local_monotonic_ms_v1()
    signed_pos = str(classified.signed_pos or extracted_pos.get("pos") or "")
    price_decision = evaluate_canary_flatten_limit_price_contract_v1(
        FlattenPriceInputV1(
            flatten_side="SELL",
            observed_signed_pos=signed_pos,
            bid=quotes.get("bidPx"),
            ask=quotes.get("askPx"),
            quote_timestamp_ms=quotes.get("ts"),
            evaluation_timestamp_ms=eval_ts_ms,
            tick_sz=tick_sz or None,
            freshness_threshold_ms=str(FRESHNESS_THRESHOLD_MS),
        )
    )
    flatten_px = str(price_decision.limit_price or "")
    if not price_decision.permit_issued:
        envelope_error = envelope_error or (
            "FLATTEN_LIMIT_PRICE_DENIED:" + ",".join(price_decision.reject_reasons)
        )

    if flatten_px:
        max_ep = account_max_size_query_path_v1(
            instrument_id=INSTRUMENT_ID,
            td_mode=TD_MODE,
            px=flatten_px,
            order_type=ORDER_TYPE,
        )
        max_attempt = _do_get(
            client=client,
            name="MAX_SIZE",
            endpoint=max_ep,
            rest_base=rest_base,
            header_provider=header_provider,
            gets=gets,
            payloads=payloads,
        )
        if max_attempt.get("payload") and max_attempt.get("http_status") == 200:
            try:
                max_obs = acquire_fresh_max_available_observation_from_payload_v1(
                    pretrade_decision_id=decision_id,
                    payload=max_attempt["payload"],
                    instrument_id=INSTRUMENT_ID,
                    td_mode=TD_MODE,
                    px_sent=flatten_px,
                    order_type=ORDER_TYPE,
                    observed_at_utc=str(max_attempt["observed_at_utc"]),
                    endpoint=max_ep,
                    http_status=int(max_attempt["http_status"] or 0),
                    get_performed=True,
                    rest_host=str(rest_host),
                    auth_header_sent=True,
                    historical_reuse=False,
                    body_sha256=str(max_attempt["body_sha256"]),
                )
                max_sell = str(max_obs.max_sell_raw)
            except Exception as exc:  # noqa: BLE001
                envelope_error = envelope_error or str(exc)

    pending_attempt = _do_get(
        client=client,
        name="ORDERS_PENDING",
        endpoint=PATH_ORDERS_PENDING,
        rest_base=rest_base,
        header_provider=header_provider,
        gets=gets,
        payloads=payloads,
    )
    pending_gate = evaluate_pending_order_gate_v1(
        payload=pending_attempt.get("payload")
        if isinstance(pending_attempt.get("payload"), Mapping)
        else payloads.get("ORDERS_PENDING")
        if isinstance(payloads.get("ORDERS_PENDING"), Mapping)
        else None,
        instrument_id=INSTRUMENT_ID,
    )

    methods_used = {str(item.get("method") or "") for item in gets}
    if methods_used - {"GET"}:
        raise EnvelopeRepriceOrFreshnessAtSendError("NON_GET_METHOD_RECORDED")
    if client.counters.write_request_count != 0:
        raise EnvelopeRepriceOrFreshnessAtSendError("WRITE_REQUEST_COUNT_NONZERO")
    if len(gets) > 7:
        raise EnvelopeRepriceOrFreshnessAtSendError(f"GET_CALL_COUNT_EXCEEDS_MAX:{len(gets)}")

    envelope_status = classify_envelope_freshness_v1(
        price_permit_issued=bool(price_decision.permit_issued),
        computed_limit_px=flatten_px,
        frozen_limit_px=FROZEN_LIMIT_PX,
        quote_freshness_valid=bool(
            quotes.get("bidPx")
            and "STALE_QUOTE" not in price_decision.reject_reasons
            and price_decision.permit_issued
        ),
        reject_reasons=price_decision.reject_reasons,
    )
    freshness_evidence = PositionObservationFreshnessEvidenceV1(
        response_received_monotonic_ms=pos_attempt.get("response_received_monotonic_ms"),
        decision_id=decision_id,
        evidence_kind=PRE_SEND_EVIDENCE_KIND,
        observation_get_identity=str(pos_attempt.get("body_sha256") or ""),
    )
    pos_freshness = evaluate_position_observation_freshness_v1(
        evidence=freshness_evidence,
        evaluation_monotonic_ms=eval_mono_ms,
        current_decision_id=decision_id,
    )

    pos_raw = str(extracted_pos.get("pos") or classified.signed_pos or "")
    pos_side = str(extracted_pos.get("posSide") or "")
    rebuild_allowed = (
        envelope_status == "REPRICE_REQUIRED"
        and not envelope_error
        and fee_policy is not None
        and flatten_px
        and max_sell
        and sell_lmt
        and pending_gate.get("PENDING_ORDER_GATE_PASS") is True
        and pos_raw == EXPECTED_SIGNED_POSITION
        and pos_side == POS_SIDE_OBSERVED
        and mgn_mode == MARGIN_MODE
    )
    if rebuild_allowed:
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
                evaluation_ts_ms=eval_ts_ms,
                tick_sz=tick_sz,
                sell_lmt=sell_lmt,
                max_sell=max_sell,
                max_sell_px_sent=flatten_px,
                ct_val=ct_val,
                fee_policy=fee_policy,
                pending_order_count=int(pending_gate.get("ACCOUNT_PENDING_ORDER_COUNT") or 0),
                pending_order_gate_pass=True,
            )
            rebuild_executed = True
            reprice_executed = True
        except FlattenSellEnvelopeError as exc:
            envelope_error = str(exc)
            envelope = None
            rebuild_executed = False
            reprice_executed = False

    if envelope is not None:
        new_px = str(envelope.get("LIMIT_PRICE") or "")
        if new_px != flatten_px:
            raise EnvelopeRepriceOrFreshnessAtSendError("REPRICED_LIMIT_NOT_QUOTE_LOCKED")
        if str(envelope.get("FLATTEN_ENVELOPE_ID") or "") == FROZEN_ENVELOPE_ID:
            raise EnvelopeRepriceOrFreshnessAtSendError("NEW_ENVELOPE_ID_COLLIDES_WITH_FROZEN")
        if envelope.get("SUBMIT_REACHABLE") is True:
            raise EnvelopeRepriceOrFreshnessAtSendError("SUBMIT_REACHABLE_MUST_REMAIN_FALSE")

    producer = evaluate_flatten_pre_send_gate_v1(
        FlattenPreSendGateInputV1(
            live_authorized=False,
            live_enabled=False,
            live_armed=False,
            flatten_live_wire_enabled=False,
            allow_productive_wire_send=False,
            flatten_execute_token=None,
            flatten_execute_purpose=None,
            flatten_execute_owner_go=None,
            positions_payload=pos_payload if isinstance(pos_payload, Mapping) else {},
            pending_orders_payload=(
                payloads.get("ORDERS_PENDING")
                if isinstance(payloads.get("ORDERS_PENDING"), Mapping)
                else None
            ),
            price_input=FlattenPriceInputV1(
                flatten_side="SELL",
                observed_signed_pos=signed_pos,
                bid=quotes.get("bidPx"),
                ask=quotes.get("askPx"),
                quote_timestamp_ms=quotes.get("ts"),
                evaluation_timestamp_ms=eval_ts_ms,
                tick_sz=tick_sz or None,
                freshness_threshold_ms=str(FRESHNESS_THRESHOLD_MS),
            ),
            owner_go=OWNER_GO,
            origin_main_sha=sha,
            flatten_pre_send_decision_id=decision_id,
            position_observation_freshness_evidence=freshness_evidence,
            monotonic_ms_clock=default_local_monotonic_ms_v1,
        )
    )
    if producer.allowed is True:
        raise EnvelopeRepriceOrFreshnessAtSendError(
            "PRODUCER_ALLOWED_TRUE_WITHOUT_RECEIPT_OR_SEND_AUTHORITY"
        )

    status_after = envelope_status
    if reprice_executed and envelope is not None:
        status_after = "VALID_WITH_FRESH_GET"
    elif envelope_status == "VALID_WITH_FRESH_GET":
        status_after = "VALID_WITH_FRESH_GET"

    get_success = sum(
        1 for item in gets if item.get("http_status") == 200 and item.get("venue_code") == "0"
    )
    get_timeout = sum(1 for item in gets if item.get("timeout"))
    quote_observed = bool(quotes.get("bidPx") and quotes.get("askPx") and quotes.get("ts"))
    new_envelope_id = str((envelope or {}).get("FLATTEN_ENVELOPE_ID") or "NONE")
    new_limit = str((envelope or {}).get("LIMIT_PRICE") or "NONE")

    next_owner = "RECEIPT_HMAC_VS_WIRE_SEND_AUTHORITY_ORDER"
    if envelope_status != "VALID_WITH_FRESH_GET" and not reprice_executed:
        next_owner = "ENVELOPE_REPRICE_OR_FRESHNESS_AT_SEND"
    earliest_after = (
        "RECEIPT_HMAC_VS_WIRE_SEND_AUTHORITY_ORDER"
        if status_after == "VALID_WITH_FRESH_GET"
        else "ENVELOPE_REPRICE_OR_FRESHNESS_AT_SEND"
    )
    final_status = (
        "ENVELOPE_REPRICED_FRESH_AT_SEND"
        if reprice_executed
        else (
            "ENVELOPE_FRESH_AT_SEND_NO_REPRICE"
            if envelope_status == "VALID_WITH_FRESH_GET"
            else "ENVELOPE_REPRICE_INCOMPLETE"
        )
    )

    summary = {
        "SCHEMA_VERSION": "section_11_14_envelope_reprice_or_freshness_at_send.v1",
        "THIS_SLICE": THIS_SLICE,
        "PREDECESSOR_SLICE": PREDECESSOR_SLICE,
        "OWNER_GO": OWNER_GO,
        "CURRENT_ORIGIN_MAIN_SHA": sha,
        "CURRENT_ORIGIN_MAIN_TREE": str(origin_main_tree or ""),
        "EXPECTED_ORIGIN_MAIN_SHA": EXPECTED_ORIGIN_MAIN_SHA,
        "BOUND_ENVELOPE_ORIGIN_MAIN_SHA": BOUND_ORIGIN_MAIN_SHA,
        "OLD_ENVELOPE_ID": FROZEN_ENVELOPE_ID,
        "OLD_LIMIT_PRICE": FROZEN_LIMIT_PX,
        "OLD_ENVELOPE_PROVENANCE": BOUND_FROZEN_EVIDENCE_RELATIVE,
        "FROZEN_EVIDENCE_RELATIVE": BOUND_FROZEN_EVIDENCE_RELATIVE,
        "REPRICE_CONTRACT_STATUS": "DEFINED",
        "REPRICE_ALGORITHM_SOURCE": REPRICE_ALGORITHM_SOURCE,
        "ROUNDING_RULE": ROUNDING_RULE,
        "PRICE_BAND_RULE": PRICE_BAND_RULE,
        "FRESH_GET_REQUIRED": True,
        "GET_CONTRACT_STATUS": "DEFINED",
        "ALWAYS_REQUIRED_GET_COUNT": contract["ALWAYS_REQUIRED_GET_COUNT"],
        "MAX_GET_CALL_COUNT": contract["MAX_GET_CALL_COUNT"],
        "ALWAYS_REQUIRED_GET_ENDPOINTS": contract["ALWAYS_REQUIRED_GET_ENDPOINTS"],
        "AUTH_SESSION_CONTRACT_SATISFIED": bool(session["AUTH_SESSION_CONTRACT_SATISFIED"]),
        "READ_ONLY_NETWORK_GUARD_ACTIVE": True,
        "NETWORK_MUTATION_GUARD": "ACTIVE",
        "POST_HARD_BLOCK": post_block,
        "PLACE_ORDER_GET_HARD_BLOCK": place_order_block,
        "GET_EXECUTED": True,
        "GET_CALL_COUNT": len(gets),
        "GET_SUCCESS_COUNT": get_success,
        "GET_TIMEOUT_COUNT": get_timeout,
        "CURRENT_POSITION_STATE": classified.state,
        "CURRENT_POSITION_REASON": classified.reason,
        "POSITION_VALUE": pos_raw or "NONE",
        "POSITION_FRESHNESS_VALID": bool(pos_freshness.allowed),
        "POSITION_FRESHNESS_REASON": pos_freshness.reject_reason,
        "QUOTE_OBSERVED": quote_observed,
        "QUOTE_BID": quotes.get("bidPx") or "NONE",
        "QUOTE_ASK": quotes.get("askPx") or "NONE",
        "QUOTE_LAST": quotes.get("last") or "NONE",
        "QUOTE_TS_MS": quotes.get("ts") or "NONE",
        "QUOTE_TICK_SZ": tick_sz or "NONE",
        "FRESH_REFERENCE_FIELD": "bidPx",
        "FRESH_REFERENCE_PRICE": quotes.get("bidPx") or "NONE",
        "FRESH_MARKET_OBSERVATION_TS": quotes.get("ts") or "NONE",
        "COMPUTED_LIMIT_PX": flatten_px or "NONE",
        "PRICE_PERMIT_ISSUED": bool(price_decision.permit_issued),
        "PRICE_REJECT_REASONS": list(price_decision.reject_reasons),
        "FRESH_SELL_LMT": sell_lmt or "NONE",
        "FRESH_MAX_SELL": max_sell or "NONE",
        "PENDING_ORDER_GATE": pending_gate,
        "ENVELOPE_FRESHNESS_STATUS": envelope_status,
        "ENVELOPE_FRESHNESS_STATUS_AFTER": status_after,
        "REPRICE_REQUIRED": envelope_status == "REPRICE_REQUIRED",
        "REPRICE_EXECUTED": reprice_executed,
        "ENVELOPE_REBUILD_EXECUTED": rebuild_executed,
        "ENVELOPE_REBUILT": rebuild_executed,
        "NEW_LIMIT_PRICE": new_limit,
        "NEW_ENVELOPE_ID": new_envelope_id,
        "NEW_ENVELOPE_PROVENANCE": (
            f"fresh_ticker_ts={quotes.get('ts') or 'NONE'};origin_main_sha={sha}"
            if rebuild_executed
            else "NONE"
        ),
        "ENVELOPE_ERROR": envelope_error or "",
        "HISTORICAL_VALUES_REUSED_AS_FRESH": False,
        "RECEIPT_PRODUCER_EVALUATED": True,
        "RECEIPT_MINTED": False,
        "RECEIPT_ALLOWED": bool(producer.allowed),
        "RECEIPT_BOUND": False,
        "RECEIPT_ATTACHED": False,
        "HMAC_EXECUTED": False,
        "HMAC_HEADER_GENERATED": False,
        "LEASE_CONSUMED": False,
        "HTTP_POST_EXECUTED": False,
        "PRODUCTIVE_URLLIB_POST_EXECUTED": False,
        "WIRE_SEND_EXECUTED": False,
        "DURABLE_CONSUMED": False,
        "POSITION_MUTATION": False,
        "FIRST_DENY": "RECEIPT_MISSING",
        "CURRENT_CANONICAL_BOUNDARY_AFTER": "RECEIPT_MISSING",
        "EARLIEST_UNRESOLVED_RUNTIME_GATE_AFTER": earliest_after,
        "NEXT_RUNTIME_BLOCKER": "RECEIPT_MISSING",
        "NEXT_OWNER_AUTHORITY_REQUIRED": next_owner,
        "OPEN_GATE_ORDER_BLOCKER": "RECEIPT_HMAC_VS_WIRE_SEND_AUTHORITY_ORDER",
        "OPEN_GATE_ORDER_POINTS": (
            "RECEIPT_HMAC_VS_WIRE_SEND_AUTHORITY_ORDER;DURABLE_CONSUME_SUCCESS_OBJECT"
        ),
        "STANDING_FLAGS": flags,
        "FINAL_STATUS": final_status,
        "FLATTEN_HTTP_ENDPOINT_UNTOUCHED": FLATTEN_HTTP_ENDPOINT,
        "PATHS_USED": [PATH_PUBLIC_INSTRUMENTS, PATH_MARKET_TICKER, PATH_PUBLIC_PRICE_LIMIT],
    }
    non_execution = {
        "RECEIPT_MINTED": False,
        "RECEIPT_BOUND": False,
        "RECEIPT_ATTACHED": False,
        "HMAC_EXECUTED": False,
        "HMAC_HEADER_GENERATED": False,
        "LEASE_CONSUMED": False,
        "HTTP_POST_EXECUTED": False,
        "PRODUCTIVE_URLLIB_POST_EXECUTED": False,
        "WIRE_SEND_EXECUTED": False,
        "DURABLE_CONSUMED": False,
        "POSITION_MUTATION": False,
        "METHODS_USED": sorted(methods_used),
        "WRITE_REQUEST_COUNT": client.counters.write_request_count,
        "REAL_POST_COUNT": 0,
    }
    claims = {
        "GET_ONLY": True,
        "MUTATION_VERBS_IMPOSSIBLE": True,
        "HISTORICAL_VALUES_NOT_REUSED_AS_FRESH": True,
        "RECEIPT_NOT_MINTED": True,
        "RECEIPT_NOT_ATTACHED": True,
        "POST_HMAC_NOT_GENERATED": True,
        "POST_NOT_EXECUTED": True,
        "WIRE_SEND_NOT_EXECUTED": True,
        "IN_PLACE_ENVELOPE_MUTATION": False,
    }
    adjudication = {
        "REPRICE_CONTRACT_STATUS": "DEFINED",
        "REPRICE_ALGORITHM_SOURCE": REPRICE_ALGORITHM_SOURCE,
        "ENVELOPE_FRESHNESS_STATUS": envelope_status,
        "ENVELOPE_FRESHNESS_STATUS_AFTER": status_after,
        "REPRICE_REQUIRED": envelope_status == "REPRICE_REQUIRED",
        "REPRICE_EXECUTED": reprice_executed,
        "ENVELOPE_REBUILD_EXECUTED": rebuild_executed,
        "OLD_ENVELOPE_ID": FROZEN_ENVELOPE_ID,
        "OLD_LIMIT_PRICE": FROZEN_LIMIT_PX,
        "NEW_ENVELOPE_ID": new_envelope_id,
        "NEW_LIMIT_PRICE": new_limit,
        "RECEIPT_MINTED": False,
        "RECEIPT_ATTACHED": False,
        "HTTP_POST_EXECUTED": False,
        "WIRE_SEND_EXECUTED": False,
        "CURRENT_CANONICAL_BOUNDARY_AFTER": "RECEIPT_MISSING",
        "EARLIEST_UNRESOLVED_RUNTIME_GATE_AFTER": earliest_after,
        "NEXT_OWNER_AUTHORITY_REQUIRED": next_owner,
        "FINAL_STATUS": final_status,
    }
    lineage = {
        "origin_main_sha": sha,
        "predecessor_slice": PREDECESSOR_SLICE,
        "this_slice": THIS_SLICE,
        "owner_go": OWNER_GO,
        "historical_reuse": False,
        "frozen_envelope_id": FROZEN_ENVELOPE_ID,
        "frozen_origin_main_sha": BOUND_ORIGIN_MAIN_SHA,
        "new_envelope_id": new_envelope_id if rebuild_executed else "NONE",
    }
    persist_meta: dict[str, Any] = {}
    if persist_root is not None:
        persist_meta = persist_envelope_reprice_evidence_v1(
            persist_root=persist_root,
            summary=summary,
            claims=claims,
            adjudication=adjudication,
            gets={"GETS": gets},
            census=contract,
            lineage=lineage,
            non_execution=non_execution,
            session=session,
            envelope=envelope,
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
        "CONTRACT": contract,
        "LIVE_ENABLED": LIVE_ENABLED,
        "LIVE_ARMED": LIVE_ARMED,
        "CANARY_AUTHORIZED": CANARY_AUTHORIZED,
        "POST_ALLOWED": POST_ALLOWED,
        "SECTION_11_14_RUNTIME_EXECUTION_AUTHORIZED": SECTION_11_14_RUNTIME_EXECUTION_AUTHORIZED,
    }


def persist_envelope_reprice_evidence_v1(
    *,
    persist_root: Path | str,
    summary: Mapping[str, Any],
    claims: Mapping[str, Any],
    adjudication: Mapping[str, Any],
    gets: Mapping[str, Any],
    census: Mapping[str, Any],
    lineage: Mapping[str, Any],
    non_execution: Mapping[str, Any],
    session: Mapping[str, Any],
    envelope: Mapping[str, Any] | None,
) -> dict[str, Any]:
    root = Path(persist_root)
    root.mkdir(parents=True, exist_ok=True)
    files: dict[str, Mapping[str, Any]] = {
        "SUMMARY.json": summary,
        "claims.json": claims,
        "ADJUDICATION.json": adjudication,
        "GET_RESULTS.sanitized.json": gets,
        "CENSUS.json": census,
        "LINEAGE.json": lineage,
        "NON_EXECUTION.json": non_execution,
        "SESSION.json": session,
        "FROZEN_ENVELOPE_REF.json": {
            "OLD_ENVELOPE_ID": FROZEN_ENVELOPE_ID,
            "OLD_LIMIT_PRICE": FROZEN_LIMIT_PX,
            "OLD_ENVELOPE_PROVENANCE": BOUND_FROZEN_EVIDENCE_RELATIVE,
            "BOUND_ORIGIN_MAIN_SHA": BOUND_ORIGIN_MAIN_SHA,
            "HISTORICAL_ONLY": True,
        },
    }
    if envelope is not None:
        files["FLATTEN_ENVELOPE.json"] = envelope
    for name, payload in files.items():
        assert_no_plaintext_in_payload_v1(payload)
        write_json_v1(root / name, payload)
    rels = tuple(sorted(files))
    write_manifest_v1(root, rels)
    verified = verify_manifest_v1(root)
    if int(verified.get("MANIFEST_VERIFY_RC", 1)) != 0:
        raise EnvelopeRepriceOrFreshnessAtSendError("MANIFEST_VERIFY_FAILED")
    return {
        "persist_root": str(root),
        "MANIFEST_VERIFY_RC": 0,
        "files": list(rels),
    }


def execute_envelope_reprice_or_freshness_at_send_v1(
    *,
    vault_file: Path | str,
    origin_main_sha: str,
    origin_main_tree: str = "",
    persist_root: Path | str | None = None,
    secret_reference: str = REQUIRED_SECRETREF_URI,
    transport: FlattenGetOnlyTransportV1 | None = None,
) -> dict[str, Any]:
    handle = None
    vault_path = Path(vault_file)
    session = adjudicate_auth_session_contract_v1(vault_file=vault_path)
    if session["AUTH_SESSION_CONTRACT_SATISFIED"] is not True:
        raise EnvelopeRepriceOrFreshnessAtSendError("AUTH_SESSION_CONTRACT_NOT_SATISFIED")
    try:
        vault = build_file_secretref_vault_backend_v1(vault_file=vault_path)
        handle = resolve_and_load_live_canary_secretref_ephemeral_v1(
            secret_reference=secret_reference,
            vault_backend=vault,
        )

        def header_provider(url: str) -> Mapping[str, str]:
            return build_get_only_auth_headers_v1(handle=handle, url=url, method="GET")

        return run_envelope_reprice_or_freshness_at_send_v1(
            origin_main_sha=origin_main_sha,
            origin_main_tree=origin_main_tree,
            transport=transport or UrllibFlattenGetOnlyTransportV1(),
            header_provider=header_provider,
            persist_root=persist_root,
            vault_file=vault_path,
        )
    except LiveCanaryCredentialError as exc:
        raise EnvelopeRepriceOrFreshnessAtSendError(f"CREDENTIAL_RESOLVE_FAILED:{exc}") from exc
    except FlattenGetOnlyHttpError as exc:
        raise EnvelopeRepriceOrFreshnessAtSendError(f"GET_ONLY_HTTP_FAILED:{exc}") from exc
    finally:
        if handle is not None:
            release_live_canary_ephemeral_material_v1(handle)
