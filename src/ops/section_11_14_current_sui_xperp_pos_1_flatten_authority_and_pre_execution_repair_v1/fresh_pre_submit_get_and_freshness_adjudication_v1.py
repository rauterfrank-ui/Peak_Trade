"""§11.14 Fresh Pre-Submit GET and freshness adjudication.

Executes only the GETs the current receipt producer actually requires as
fresh observations. Does not rebuild a Flatten SELL envelope. Does not
reprice. Does not HMAC-sign a POST. Does not attach a receipt. Does not
consume a lease. Does not HTTP POST. Does not invoke productive inner.send.
"""

from __future__ import annotations

import hashlib
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INSTRUMENT_ID,
    REUSED_BINDING_REST_HOST,
    REQUIRED_SECRETREF_URI,
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
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.order_plan_v1 import (
    extract_instrument_constraints_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.position_observation_freshness_contract_v1 import (
    POSITION_OBSERVATION_FRESHNESS_MAX_AGE_MS,
    PRE_SEND_EVIDENCE_KIND,
    PositionObservationFreshnessEvidenceV1,
    default_local_monotonic_ms_v1,
    evaluate_position_observation_freshness_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.pre_submit_state_v1 import (
    classify_target_position_state_v1,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.constants_v1 import (
    BOUND_FROZEN_ENVELOPE_ID,
    BOUND_FROZEN_EVIDENCE_RELATIVE,
    BOUND_ORIGIN_MAIN_SHA,
    DEFAULT_VAULT_RELATIVE,
    ENDPOINT_PATH_ALLOWLIST,
    EXPECTED_VENUE_NATIVE_BODY,
    FLATTEN_HTTP_ENDPOINT,
    FORBIDDEN_EXACT_POST_PATHS,
    INSTRUMENT_ID,
    METHOD_ALLOWLIST,
    NETWORK_SESSION_CANNOT_AUTHORIZE_WIRE_SEND_IN_THIS_REPAIR,
    PATH_ACCOUNT_POSITIONS,
    PATH_MARKET_TICKER,
    PATH_ORDERS_PENDING,
    PATH_PUBLIC_INSTRUMENTS,
    PATH_PUBLIC_PRICE_LIMIT,
    PRIVATE_ENDPOINT_PATHS,
    PUBLIC_ENDPOINT_PATHS,
    REST_SCHEME_HOST,
    USER_AGENT,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.envelope_v1 import (
    FlattenSellEnvelopeError,
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
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.get_only_preflight_v1 import (
    evaluate_pending_order_gate_v1,
)
from src.ops.section_11_14_live_handoff_current_origin_main_bound_get_only_pretrade_readiness_v1.orchestrator_v1 import (
    build_get_only_auth_headers_v1,
    extract_pre_existing_position_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    CANARY_AUTHORIZED,
    LIVE_ARMED,
    LIVE_ENABLED,
    POST_ALLOWED,
    SECTION_11_14_RUNTIME_EXECUTION_AUTHORIZED,
)

THIS_SLICE = "11.14.FRESH_PRE_SUBMIT_GET_AND_FRESHNESS_ADJUDICATION"
PREDECESSOR_SLICE = "11.14.FLATTEN_PRE_SEND_RECEIPT_AUTHORITY_AND_BINDING"
OWNER_GO = "FRESH_PRE_SUBMIT_GET"
EXPECTED_ORIGIN_MAIN_SHA = "74bd47f7e4d33760eb7c8830d6e318c1113e2729"
FROZEN_LIMIT_PX = str(EXPECTED_VENUE_NATIVE_BODY["px"])
FROZEN_ENVELOPE_ID = BOUND_FROZEN_ENVELOPE_ID

GET_CONTRACT_CANDIDATES: tuple[str, ...] = (
    PATH_ACCOUNT_POSITIONS,
    PATH_ORDERS_PENDING,
    PATH_MARKET_TICKER,
    PATH_PUBLIC_INSTRUMENTS,
    PATH_PUBLIC_PRICE_LIMIT,
    "/api/v5/account/config",
    "/api/v5/account/balance",
    "/api/v5/account/leverage-info",
    "/api/v5/account/max-size",
    "/api/v5/account/trade-fee",
    "/api/v5/public/mark-price",
    "/api/v5/market/books",
)

REQUIRED_FRESH_GETS: tuple[tuple[str, str, str], ...] = (
    (
        "POSITIONS",
        PATH_ACCOUNT_POSITIONS,
        "PRIVATE",
    ),
    (
        "TICKER",
        f"{PATH_MARKET_TICKER}?instId={INSTRUMENT_ID}",
        "PUBLIC",
    ),
    (
        "ORDERS_PENDING",
        PATH_ORDERS_PENDING,
        "PRIVATE",
    ),
    (
        "INSTRUMENTS",
        public_instruments_query_path_v1(instrument_id=INSTRUMENT_ID),
        "PUBLIC",
    ),
)

HeaderProvider = Callable[[str], Mapping[str, str]]


class FreshPreSubmitGetError(RuntimeError):
    """Fail-closed Fresh Pre-Submit GET violation."""


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
        raise FreshPreSubmitGetError(f"STANDING_LIVE_FLAG_MUST_REMAIN_FALSE:{raised}")
    return flags


def prove_get_path_cannot_post_v1(*, client: FlattenGetOnlyHttpClientV1) -> str:
    """Hard-fail any POST attempt on the GET-only client before wire."""
    try:
        client.post(endpoint=FLATTEN_HTTP_ENDPOINT)
    except FlattenGetOnlyHttpError as exc:
        text = str(exc)
        if "HTTP_METHOD_HARD_BLOCK_BEFORE_WIRE:POST" not in text:
            raise FreshPreSubmitGetError(f"POST_HARD_BLOCK_TEXT_DRIFT:{text}") from exc
        return text
    raise FreshPreSubmitGetError("GET_CLIENT_POST_DID_NOT_HARD_BLOCK")


def prove_place_order_get_is_blocked_v1(*, client: FlattenGetOnlyHttpClientV1) -> str:
    try:
        client.get(endpoint=FLATTEN_HTTP_ENDPOINT)
    except FlattenGetOnlyHttpError as exc:
        text = str(exc)
        if "MUTATION_ENDPOINT_HARD_BLOCK" not in text:
            raise FreshPreSubmitGetError(f"PLACE_ORDER_GET_BLOCK_TEXT_DRIFT:{text}") from exc
        return text
    raise FreshPreSubmitGetError("PLACE_ORDER_GET_DID_NOT_HARD_BLOCK")


def adjudicate_auth_session_contract_v1(*, vault_file: Path | str | None = None) -> dict[str, Any]:
    """Revalidate GET-only host/session/credential scope. Never logs secrets."""
    flags = assert_standing_live_flags_remain_false_v1()
    host = str(REUSED_BINDING_REST_HOST or "").strip()
    rest = str(REST_SCHEME_HOST or "").strip()
    methods = tuple(METHOD_ALLOWLIST)
    vault_path = Path(vault_file) if vault_file is not None else Path(DEFAULT_VAULT_RELATIVE)
    vault_exists = vault_path.is_file()
    if host != "eea.okx.com":
        raise FreshPreSubmitGetError(f"HOST_NOT_PRODUCTION_EEA:{host}")
    if rest != "https://eea.okx.com":
        raise FreshPreSubmitGetError(f"REST_BASE_NOT_PRODUCTION_EEA:{rest}")
    if methods != ("GET",):
        raise FreshPreSubmitGetError(f"METHOD_ALLOWLIST_DRIFT:{methods}")
    if FLATTEN_HTTP_ENDPOINT not in FORBIDDEN_EXACT_POST_PATHS:
        raise FreshPreSubmitGetError("PLACE_ORDER_NOT_IN_FORBIDDEN_EXACT_POST_PATHS")
    if PATH_ACCOUNT_POSITIONS not in ENDPOINT_PATH_ALLOWLIST:
        raise FreshPreSubmitGetError("POSITIONS_PATH_NOT_ALLOWLISTED")
    if PATH_ORDERS_PENDING not in ENDPOINT_PATH_ALLOWLIST:
        raise FreshPreSubmitGetError("ORDERS_PENDING_PATH_NOT_ALLOWLISTED")
    if PATH_MARKET_TICKER not in ENDPOINT_PATH_ALLOWLIST:
        raise FreshPreSubmitGetError("TICKER_PATH_NOT_ALLOWLISTED")
    signer_forbids_post = True
    try:
        build_get_only_auth_headers_v1(handle=object(), url="https://eea.okx.com/x", method="POST")
        signer_forbids_post = False
    except Exception as exc:  # noqa: BLE001
        if "GET_ONLY_SIGNER_METHOD_FORBIDDEN:POST" not in str(exc):
            signer_forbids_post = "GET_ONLY_SIGNER_METHOD_FORBIDDEN" in str(exc)
    if signer_forbids_post is not True:
        raise FreshPreSubmitGetError("GET_ONLY_SIGNER_DOES_NOT_FORBID_POST")
    return {
        "HOST": host,
        "REST_SCHEME_HOST": rest,
        "METHOD_ALLOWLIST": list(methods),
        "VAULT_EXISTS": vault_exists,
        "VAULT_PATH_REDACTED": True,
        "CREDENTIAL_VALUES_LOGGED": False,
        "GET_ONLY_SIGNER_FORBIDS_POST": True,
        "NETWORK_SESSION_CANNOT_AUTHORIZE_WIRE_SEND": (
            NETWORK_SESSION_CANNOT_AUTHORIZE_WIRE_SEND_IN_THIS_REPAIR is True
        ),
        "NETWORK_SESSION_ORIGIN_MAIN_SHA": BOUND_ORIGIN_MAIN_SHA,
        "NETWORK_SESSION_SHA_EQUALS_CURRENT_ORIGIN_MAIN": (
            BOUND_ORIGIN_MAIN_SHA == EXPECTED_ORIGIN_MAIN_SHA
        ),
        "GET_AUTH_CLASS": "SECRETREF_GET_ONLY_HMAC_FOR_GET_NOT_POST",
        "POST_AUTHORITY": False,
        "WIRE_SEND_AUTHORITY": False,
        "STANDING_FLAGS": flags,
        "AUTH_SESSION_CONTRACT_SATISFIED": vault_exists,
    }


def required_fresh_get_contract_v1() -> dict[str, Any]:
    return {
        "GET_CONTRACT_CANDIDATE_COUNT": len(GET_CONTRACT_CANDIDATES),
        "GET_CONTRACT_CANDIDATES": list(GET_CONTRACT_CANDIDATES),
        "GET_CONTRACT_STATUS": "DEFINED",
        "REQUIRED_FRESH_GET_COUNT": len(REQUIRED_FRESH_GETS),
        "REQUIRED_FRESH_GET_ENDPOINTS": [item[1] for item in REQUIRED_FRESH_GETS],
        "POSITION_FRESHNESS_CONTRACT": (
            "GET /api/v5/account/positions unfiltered; "
            "classify_target_position_state_v1; "
            f"EMPTY_DATA_IS_NOT_ZERO; ABSENT_TARGET_ROW_IS_NOT_ZERO; "
            f"LOCAL_MONOTONIC_MS max-age={POSITION_OBSERVATION_FRESHNESS_MAX_AGE_MS}"
        ),
        "QUOTE_FRESHNESS_CONTRACT": (
            "GET /api/v5/market/ticker?instId="
            f"{INSTRUMENT_ID}; bidPx/askPx/ts; "
            f"QUOTE_FRESHNESS_5000MS threshold_ms={FRESHNESS_THRESHOLD_MS}; "
            "SELL selects BID; tickSz from public/instruments"
        ),
        "OTHER_FRESHNESS_INPUTS": (
            "GET /api/v5/trade/orders-pending contemporaneous "
            "(no TTL; None=OPEN_ORDER_STATE_UNAVAILABLE; "
            "data=[] code=0 means zero pending rows); "
            "GET /api/v5/public/instruments tickSz identity "
            "(no TTL freshness predicate)"
        ),
        "NOT_REQUIRED_BY_RECEIPT_PRODUCER": [
            PATH_PUBLIC_PRICE_LIMIT,
            "/api/v5/account/config",
            "/api/v5/account/balance",
            "/api/v5/account/leverage-info",
            "/api/v5/account/max-size",
            "/api/v5/account/trade-fee",
            "/api/v5/public/mark-price",
            "/api/v5/market/books",
        ],
        "PRE_SUBMIT_FRESH_GET_REQUIRED": True,
        "ENVELOPE_REBUILD_FORBIDDEN": True,
        "REPRICE_FORBIDDEN": True,
    }


def _one_get(
    *,
    client: FlattenGetOnlyHttpClientV1,
    name: str,
    endpoint: str,
    headers: Mapping[str, str] | None,
) -> dict[str, Any]:
    observed = utc_now_iso_v1()
    received_ms = default_local_monotonic_ms_v1()
    path = endpoint_path_v1(endpoint)
    try:
        response = client.get(endpoint=endpoint, headers=headers)
        received_ms = default_local_monotonic_ms_v1()
    except FlattenGetOnlyHttpError as exc:
        timeout = "INDETERMINATE_TIMEOUT" in str(exc)
        return {
            "name": name,
            "endpoint": endpoint,
            "observed_at_utc": observed,
            "response_received_monotonic_ms": received_ms,
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
        "name": name,
        "endpoint": endpoint,
        "observed_at_utc": observed,
        "response_received_monotonic_ms": received_ms,
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
        raise FreshPreSubmitGetError(f"PRIVATE_HEADER_PROVIDER_REQUIRED:{path}")
    return header_provider(f"{rest_base.rstrip('/')}{endpoint}")


def _public_get_record(attempt: Mapping[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in attempt.items() if k != "payload"}


def classify_envelope_freshness_v1(
    *,
    price_permit_issued: bool,
    computed_limit_px: str,
    frozen_limit_px: str,
    quote_freshness_valid: bool,
    reject_reasons: tuple[str, ...],
) -> str:
    if not quote_freshness_valid:
        if "STALE_QUOTE" in reject_reasons:
            return "REPRICE_REQUIRED"
        return "INDETERMINATE"
    if not price_permit_issued or not computed_limit_px:
        return "INDETERMINATE"
    if str(computed_limit_px).strip() != str(frozen_limit_px).strip():
        return "REPRICE_REQUIRED"
    return "VALID_WITH_FRESH_GET"


def run_fresh_pre_submit_gets_v1(
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
    """Execute the four required Fresh GETs. Never rebuilds envelope. Never POSTs."""
    flags = assert_standing_live_flags_remain_false_v1()
    sha = str(origin_main_sha or "").strip().lower()
    if len(sha) != 40 or any(ch not in "0123456789abcdef" for ch in sha):
        raise FreshPreSubmitGetError("ORIGIN_MAIN_SHA_REQUIRED")
    if rest_host != REUSED_BINDING_REST_HOST:
        raise FreshPreSubmitGetError(f"REST_HOST_NOT_PRODUCTION_EEA:{rest_host}")
    if INSTRUMENT_ID != DEFAULT_INSTRUMENT_ID:
        raise FreshPreSubmitGetError("INSTRUMENT_BINDING_DRIFT")
    session = adjudicate_auth_session_contract_v1(vault_file=vault_file)
    contract = required_fresh_get_contract_v1()
    client = FlattenGetOnlyHttpClientV1(transport=transport, rest_base=rest_base)
    post_block = prove_get_path_cannot_post_v1(client=client)
    place_order_block = prove_place_order_get_is_blocked_v1(client=client)

    gets: list[dict[str, Any]] = []
    payloads: dict[str, Any] = {}
    for name, endpoint, _auth_class in REQUIRED_FRESH_GETS:
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

    methods_used = {str(item.get("method") or "") for item in gets}
    if methods_used - {"GET"}:
        raise FreshPreSubmitGetError("NON_GET_METHOD_RECORDED")
    if client.counters.write_request_count != 0:
        raise FreshPreSubmitGetError("WRITE_REQUEST_COUNT_NONZERO")

    tick_sz = ""
    inst_payload = payloads.get("INSTRUMENTS")
    inst_attempt = next(item for item in gets if item["name"] == "INSTRUMENTS")
    if inst_payload and inst_attempt.get("http_status") == 200:
        try:
            constraints = extract_instrument_constraints_v1(
                instruments_payload=inst_payload,
                instrument_id=INSTRUMENT_ID,
            )
            tick_sz = str(constraints.get("tickSz") or "")
        except Exception as exc:  # noqa: BLE001
            inst_attempt["extract_error"] = str(exc)

    quotes: dict[str, str] = {}
    ticker_attempt = next(item for item in gets if item["name"] == "TICKER")
    ticker_payload = payloads.get("TICKER")
    if ticker_payload and ticker_attempt.get("http_status") == 200:
        try:
            quotes = extract_flatten_ticker_quotes_v1(ticker_payload=ticker_payload)
        except FlattenSellEnvelopeError as exc:
            ticker_attempt["extract_error"] = str(exc)

    pos_attempt = next(item for item in gets if item["name"] == "POSITIONS")
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

    pending_attempt = next(item for item in gets if item["name"] == "ORDERS_PENDING")
    pending_payload = payloads.get("ORDERS_PENDING")
    pending_gate = evaluate_pending_order_gate_v1(
        payload=pending_payload if isinstance(pending_payload, Mapping) else None,
        instrument_id=INSTRUMENT_ID,
    )

    eval_ts_ms = str(int(time.time() * 1000))
    eval_mono_ms = default_local_monotonic_ms_v1()
    decision_id = f"{THIS_SLICE}:{sha[:12]}"
    price_decision = evaluate_canary_flatten_limit_price_contract_v1(
        FlattenPriceInputV1(
            flatten_side="SELL",
            observed_signed_pos=str(classified.signed_pos or extracted_pos.get("pos") or ""),
            bid=quotes.get("bidPx"),
            ask=quotes.get("askPx"),
            quote_timestamp_ms=quotes.get("ts"),
            evaluation_timestamp_ms=eval_ts_ms,
            tick_sz=tick_sz or None,
            freshness_threshold_ms=str(FRESHNESS_THRESHOLD_MS),
        )
    )
    computed_limit = str(price_decision.limit_price or "")
    quote_freshness_valid = (
        price_decision.permit_issued is True and "STALE_QUOTE" not in price_decision.reject_reasons
    )
    if not price_decision.permit_issued:
        quote_freshness_valid = "STALE_QUOTE" not in price_decision.reject_reasons and (
            "FRESHNESS_UNKNOWN" not in price_decision.reject_reasons
            and "MALFORMED_TIMESTAMP" not in price_decision.reject_reasons
            and "FUTURE_TIMESTAMP" not in price_decision.reject_reasons
            and "FRESHNESS_THRESHOLD_NOT_CANONICAL" not in price_decision.reject_reasons
        )
        if "STALE_QUOTE" in price_decision.reject_reasons:
            quote_freshness_valid = False

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

    envelope_status = classify_envelope_freshness_v1(
        price_permit_issued=bool(price_decision.permit_issued),
        computed_limit_px=computed_limit,
        frozen_limit_px=FROZEN_LIMIT_PX,
        quote_freshness_valid=bool(
            quotes.get("bidPx")
            and "STALE_QUOTE" not in price_decision.reject_reasons
            and price_decision.permit_issued
        ),
        reject_reasons=price_decision.reject_reasons,
    )

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
                pending_payload if isinstance(pending_payload, Mapping) else None
            ),
            price_input=FlattenPriceInputV1(
                flatten_side="SELL",
                observed_signed_pos=str(classified.signed_pos or extracted_pos.get("pos") or ""),
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
        raise FreshPreSubmitGetError("PRODUCER_ALLOWED_TRUE_WITHOUT_REPRICE_OR_ATTACH_AUTHORITY")

    first_deny_after = "RECEIPT_MISSING"
    if envelope_status == "REPRICE_REQUIRED":
        first_deny_after = "ENVELOPE_REPRICE_OR_FRESHNESS_AT_SEND"
    elif producer.reasons:
        first_deny_after = str(producer.reasons[0])

    next_owner = (
        "ENVELOPE_REPRICE_OR_FRESHNESS_AT_SEND"
        if envelope_status == "REPRICE_REQUIRED"
        else "ENVELOPE_REPRICE_OR_FRESHNESS_AT_SEND"
    )
    if envelope_status == "VALID_WITH_FRESH_GET":
        next_owner = "ENVELOPE_REPRICE_OR_FRESHNESS_AT_SEND"

    get_success = sum(
        1 for item in gets if item.get("http_status") == 200 and item.get("venue_code") == "0"
    )
    get_timeout = sum(1 for item in gets if item.get("timeout"))
    position_observed = classified.state == "TARGET_POSITION_NONZERO_PROVEN"
    quote_observed = bool(quotes.get("bidPx") and quotes.get("askPx") and quotes.get("ts"))

    summary = {
        "SCHEMA_VERSION": "section_11_14_fresh_pre_submit_get_and_freshness_adjudication.v1",
        "THIS_SLICE": THIS_SLICE,
        "PREDECESSOR_SLICE": PREDECESSOR_SLICE,
        "OWNER_GO": OWNER_GO,
        "CURRENT_ORIGIN_MAIN_SHA": sha,
        "CURRENT_ORIGIN_MAIN_TREE": str(origin_main_tree or ""),
        "EXPECTED_ORIGIN_MAIN_SHA": EXPECTED_ORIGIN_MAIN_SHA,
        "BOUND_ENVELOPE_ORIGIN_MAIN_SHA": BOUND_ORIGIN_MAIN_SHA,
        "BOUND_FROZEN_ENVELOPE_ID": FROZEN_ENVELOPE_ID,
        "FROZEN_LIMIT_PX": FROZEN_LIMIT_PX,
        "FROZEN_EVIDENCE_RELATIVE": BOUND_FROZEN_EVIDENCE_RELATIVE,
        "GET_CONTRACT_STATUS": "DEFINED",
        "GET_CONTRACT_CANDIDATE_COUNT": contract["GET_CONTRACT_CANDIDATE_COUNT"],
        "REQUIRED_FRESH_GET_COUNT": contract["REQUIRED_FRESH_GET_COUNT"],
        "REQUIRED_FRESH_GET_ENDPOINTS": contract["REQUIRED_FRESH_GET_ENDPOINTS"],
        "GET_TARGETS_ADJUDICATED": True,
        "POSITION_FRESHNESS_CONTRACT": contract["POSITION_FRESHNESS_CONTRACT"],
        "QUOTE_FRESHNESS_CONTRACT": contract["QUOTE_FRESHNESS_CONTRACT"],
        "OTHER_FRESHNESS_INPUTS": contract["OTHER_FRESHNESS_INPUTS"],
        "AUTH_SESSION_CONTRACT_SATISFIED": bool(session["AUTH_SESSION_CONTRACT_SATISFIED"]),
        "READ_ONLY_NETWORK_GUARD_ACTIVE": True,
        "POST_HARD_BLOCK": post_block,
        "PLACE_ORDER_GET_HARD_BLOCK": place_order_block,
        "GET_EXECUTED": True,
        "GET_CALL_COUNT": len(gets),
        "GET_SUCCESS_COUNT": get_success,
        "GET_TIMEOUT_COUNT": get_timeout,
        "GET_ONLY_ENDPOINT_ALLOWLIST": list(ENDPOINT_PATH_ALLOWLIST),
        "CURRENT_POSITION_STATE": classified.state,
        "CURRENT_POSITION_REASON": classified.reason,
        "CURRENT_POSITION": (
            f"instId={INSTRUMENT_ID},pos={extracted_pos.get('pos') or classified.signed_pos or 'NONE'},"
            f"posSide={extracted_pos.get('posSide') or 'UNKNOWN'},mgnMode={mgn_mode or 'UNKNOWN'}"
        ),
        "POSITION_OBSERVED": position_observed,
        "POSITION_VALUE": classified.signed_pos or extracted_pos.get("pos") or "NONE",
        "POSITION_FRESHNESS_VALID": bool(pos_freshness.allowed),
        "POSITION_FRESHNESS_REASON": pos_freshness.reject_reason,
        "POSITION_FRESHNESS_AGE_MS": pos_freshness.age_ms,
        "QUOTE_OBSERVED": quote_observed,
        "QUOTE_BID": quotes.get("bidPx") or "NONE",
        "QUOTE_ASK": quotes.get("askPx") or "NONE",
        "QUOTE_LAST": quotes.get("last") or "NONE",
        "QUOTE_TS_MS": quotes.get("ts") or "NONE",
        "QUOTE_TICK_SZ": tick_sz or "NONE",
        "COMPUTED_LIMIT_PX": computed_limit or "NONE",
        "PRICE_PERMIT_ISSUED": bool(price_decision.permit_issued),
        "PRICE_REJECT_REASONS": list(price_decision.reject_reasons),
        "QUOTE_FRESHNESS_VALID": bool(
            quote_observed
            and price_decision.permit_issued
            and "STALE_QUOTE" not in price_decision.reject_reasons
        ),
        "ENVELOPE_FRESHNESS_STATUS": envelope_status,
        "PENDING_ORDER_GATE": pending_gate,
        "RECEIPT_PRODUCER_EVALUATED": True,
        "RECEIPT_MINTED": False,
        "RECEIPT_ALLOWED": bool(producer.allowed),
        "RECEIPT_BOUND": False,
        "RECEIPT_ATTACHED": False,
        "RECEIPT_IDENTIFIER": producer.gate_digest if producer.gate_digest else "NONE",
        "PRODUCER_REASONS": list(producer.reasons),
        "PRODUCER_AUDIT_DECISIONS": [list(item) for item in producer.audit_decisions],
        "FIRST_DENY_BEFORE": "RECEIPT_MISSING",
        "FIRST_DENY_AFTER_FRESH_GET": first_deny_after,
        "CURRENT_CANONICAL_BOUNDARY_AFTER": "RECEIPT_MISSING",
        "EARLIEST_UNRESOLVED_RUNTIME_GATE_AFTER": (
            "ENVELOPE_REPRICE_OR_FRESHNESS_AT_SEND"
            if envelope_status == "REPRICE_REQUIRED"
            else "FLATTEN_PRE_SEND_GATE_RECEIPT"
        ),
        "NEXT_RUNTIME_BLOCKER": (
            "ENVELOPE_REPRICE_OR_FRESHNESS_AT_SEND"
            if envelope_status != "UNDEFINED"
            else "FLATTEN_PRE_SEND_GATE_RECEIPT"
        ),
        "NEXT_OWNER_AUTHORITY_REQUIRED": next_owner,
        "WORK_BLOCKED_BY_OPEN_GATE_ORDER": envelope_status
        in {"REPRICE_REQUIRED", "VALID_WITH_FRESH_GET", "INDETERMINATE"},
        "OPEN_GATE_ORDER_BLOCKER": "ENVELOPE_REPRICE_OR_FRESHNESS_AT_SEND",
        "REPRICE_EXECUTED": False,
        "HMAC_EXECUTED": False,
        "HMAC_HEADER_GENERATED": False,
        "LEASE_CONSUMED": False,
        "HTTP_POST_EXECUTED": False,
        "PRODUCTIVE_URLLIB_POST_EXECUTED": False,
        "WIRE_SEND_EXECUTED": False,
        "DURABLE_CONSUMED": False,
        "POSITION_MUTATION": False,
        "ENVELOPE_REBUILT": False,
        "STANDING_FLAGS": flags,
        "SESSION_AUTH": {
            k: v
            for k, v in session.items()
            if k
            not in {
                "VAULT_EXISTS",
            }
            or True
        },
        "FINAL_STATUS": (
            "FRESH_GET_COMPLETE_REPRICE_AUTHORITY_REQUIRED"
            if envelope_status == "REPRICE_REQUIRED"
            else "FRESH_GET_COMPLETE_NEXT_GATE_DENIED"
        ),
    }

    non_execution = {
        "REPRICE_EXECUTED": False,
        "HMAC_EXECUTED": False,
        "HMAC_HEADER_GENERATED": False,
        "LEASE_CONSUMED": False,
        "HTTP_POST_EXECUTED": False,
        "PRODUCTIVE_URLLIB_POST_EXECUTED": False,
        "WIRE_SEND_EXECUTED": False,
        "DURABLE_CONSUMED": False,
        "POSITION_MUTATION": False,
        "RECEIPT_ATTACHED": False,
        "RECEIPT_MINTED": False,
        "ENVELOPE_REBUILT": False,
        "METHODS_USED": sorted(methods_used),
        "WRITE_REQUEST_COUNT": client.counters.write_request_count,
    }
    claims = {
        "GET_ONLY": True,
        "MUTATION_VERBS_IMPOSSIBLE": True,
        "ENVELOPE_NOT_REBUILT": True,
        "REPRICE_NOT_EXECUTED": True,
        "RECEIPT_NOT_ATTACHED": True,
        "POST_HMAC_NOT_GENERATED": True,
    }
    adjudication = {
        "GET_CONTRACT_STATUS": "DEFINED",
        "GET_TARGETS_ADJUDICATED": True,
        "ENVELOPE_FRESHNESS_STATUS": envelope_status,
        "RECEIPT_MINTED": False,
        "RECEIPT_ATTACHED": False,
        "FIRST_DENY_AFTER_FRESH_GET": first_deny_after,
        "NEXT_OWNER_AUTHORITY_REQUIRED": next_owner,
        "OPEN_GATE_ORDER_BLOCKER": "ENVELOPE_REPRICE_OR_FRESHNESS_AT_SEND",
        "FINAL_STATUS": summary["FINAL_STATUS"],
    }
    lineage = {
        "origin_main_sha": sha,
        "predecessor_slice": PREDECESSOR_SLICE,
        "this_slice": THIS_SLICE,
        "owner_go": OWNER_GO,
        "historical_reuse": False,
        "frozen_envelope_id": FROZEN_ENVELOPE_ID,
        "frozen_origin_main_sha": BOUND_ORIGIN_MAIN_SHA,
    }
    persist_meta: dict[str, Any] = {}
    if persist_root is not None:
        persist_meta = persist_fresh_pre_submit_get_evidence_v1(
            persist_root=persist_root,
            summary=summary,
            claims=claims,
            adjudication=adjudication,
            gets={"GETS": gets},
            census=contract,
            lineage=lineage,
            non_execution=non_execution,
            session=session,
        )
        summary["MANIFEST_VERIFY_RC"] = persist_meta.get("MANIFEST_VERIFY_RC")
        summary["EVIDENCE_ROOT"] = persist_meta.get("persist_root")
    assert_no_plaintext_in_payload_v1(summary)
    return {
        **summary,
        "GETS": gets,
        "PERSIST": persist_meta,
        "CLIENT_COUNTERS": client.counters.to_dict(),
        "PENDING_ATTEMPT_TIMEOUT": bool(pending_attempt.get("timeout")),
        "CONTRACT": contract,
    }


def persist_fresh_pre_submit_get_evidence_v1(
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
    }
    for name, payload in files.items():
        assert_no_plaintext_in_payload_v1(payload)
        write_json_v1(root / name, payload)
    rels = tuple(sorted(files))
    write_manifest_v1(root, rels)
    verified = verify_manifest_v1(root)
    if int(verified.get("MANIFEST_VERIFY_RC", 1)) != 0:
        raise FreshPreSubmitGetError("MANIFEST_VERIFY_FAILED")
    return {
        "persist_root": str(root),
        "MANIFEST_VERIFY_RC": 0,
        "files": list(rels),
    }


def execute_fresh_pre_submit_gets_v1(
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
        raise FreshPreSubmitGetError("AUTH_SESSION_CONTRACT_NOT_SATISFIED")
    try:
        vault = build_file_secretref_vault_backend_v1(vault_file=vault_path)
        handle = resolve_and_load_live_canary_secretref_ephemeral_v1(
            secret_reference=secret_reference,
            vault_backend=vault,
        )

        def header_provider(url: str) -> Mapping[str, str]:
            return build_get_only_auth_headers_v1(handle=handle, url=url, method="GET")

        return run_fresh_pre_submit_gets_v1(
            origin_main_sha=origin_main_sha,
            origin_main_tree=origin_main_tree,
            transport=transport or UrllibFlattenGetOnlyTransportV1(),
            header_provider=header_provider,
            persist_root=persist_root,
            vault_file=vault_path,
        )
    except LiveCanaryCredentialError as exc:
        raise FreshPreSubmitGetError(f"CREDENTIAL_RESOLVE_FAILED:{exc}") from exc
    finally:
        if handle is not None:
            release_live_canary_ephemeral_material_v1(handle)
