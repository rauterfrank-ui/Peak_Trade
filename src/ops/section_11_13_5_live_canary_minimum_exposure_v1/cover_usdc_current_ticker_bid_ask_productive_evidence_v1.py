"""§11.13.5.Z2H current ticker bid/ask public GET evidence.

GET-only productive evidence for the remaining COVER_USDC slippage spread
instance. Does not instantiate SLIPPAGE_RESERVE numerically, COVER_USDC, FX,
rounding, monetary base, MMR, or a numeric funding amount. Does not treat
ticker last/markPx as a mark-price substitute. Does not authorize Live,
Testnet, orders, funding, scaling, or Multi-Future.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import parse_qs, urlsplit

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    AUTHORIZATION_SCOPE,
    CLAIMS_FILENAME,
    DEFAULT_INSTRUMENT_ID,
    DEFAULT_INST_TYPE,
    LIVE_AUTHORIZED,
    REDACTION_FILENAME,
    REUSED_BINDING_REST_HOST,
    SUMMARY_FILENAME,
    TESTNET_AUTHORIZED,
    USER_AGENT_CANARY,
    ZERO_WRITE_FILENAME,
    assert_live_canary_instrument_binding_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.cover_usdc_current_markpx_productive_evidence_v1 import (
    MARKPX_OKX_DELIVERY_FEE_OPERAND_STATUS,
    MARKPX_TERM_STATUS,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.exact_formula_body_v1 import (
    MM_LIQ_BUFFER_STATUS,
    SLIPPAGE_RESERVE_STATUS,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.evidence_v1 import (
    verify_manifest_v1,
    write_json_v1,
    write_manifest_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.formula_term_instance_binding_v1 import (
    B08_EXACT_FORMULA_BODY_STATUS,
    CONSERVATIVE_RATE_0_0003_STATUS,
    COVER_USDC_STATUS,
    CTVAL_BOUND_CCY,
    CTVAL_BOUND_VALUE,
    CTVAL_DELIVERY_FEE_OPERAND_STATUS,
    EXACT_OKX_FEE_FORMULA_STATUS,
    EXCHANGE_TRUTH_CHANGED,
    FX_STATUS,
    MONETARY_BASE_STATUS,
    NORMAL_EXPIRY_RATE_0_0001_STATUS,
    NUMERIC_FUNDING_AMOUNT,
    NUMERIC_FUNDING_AMOUNT_PRODUCED,
    OKX_POSITION_VALUE_ALGEBRA_STATUS,
    QTY_BOUND_VALUE,
    QTY_LIMIT,
    ROUNDING_STATUS,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.http_client_v1 import (
    LiveCanaryHttpRequestV1,
    LiveCanaryHttpResponseV1,
    LiveCanaryTransportV1,
    assert_no_demo_simulation_headers_v1,
    extract_canary_http_response_evidence_v1,
    parse_json_object_v1,
    safe_response_headers_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.position_value_fx_rounding_chain_v1 import (
    MULTI_FUTURE_AUTHORIZED,
    SCALING_AUTHORIZED,
    TICK_SZ_IS_NOT_USDC_PRECISION,
    USD_USDC_CONVERSION_APPLIED,
    USD_USDC_PARITY_ASSUMED,
)

OWNER_GO = (
    "OWNER_GO_REQUIRED_FOR_PRODUCTIVE_EVIDENCE_TO_RESOLVE_REMAINING_UNPROVEN_"
    "COVER_USDC_TERMS_AFTER_CURRENT_MARKPX_BEFORE_FUNDING"
)
AUTHORIZED_SCOPE = "CURRENT_TICKER_BID_ASK_PUBLIC_GET_EVIDENCE_ONLY"
BID_ASK_TERM_STATUS = "OBSERVED_NOT_NORMATIVELY_BOUND"
BID_ASK_ROLE = "CURRENT_PUBLIC_TICKER_BID_ASK_OBSERVATION_NOT_SLIPPAGE_RESERVE"
SLIPPAGE_RESERVE_INSTANCE_STATUS = "OBSERVED_SPREAD_NOT_NORMATIVELY_BOUND_RESERVE_UNINSTANTIATED"
SLIPPAGE_RESERVE_NUMERIC_STATUS = "UNINSTANTIATED"
NEXT_CANONICAL_POINTER = (
    "OWNER_GO_REQUIRED_FOR_PRODUCTIVE_EVIDENCE_TO_RESOLVE_REMAINING_UNPROVEN_"
    "COVER_USDC_TERMS_AFTER_CURRENT_TICKER_BID_ASK_BEFORE_FUNDING"
)
TICKER_ENDPOINT = "/api/v5/market/ticker"
TICKER_QUERY_PATH = f"{TICKER_ENDPOINT}?instId={DEFAULT_INSTRUMENT_ID}"
EVIDENCE_DIRNAME = "section_11_13_5_z2h_current_ticker_bid_ask_public_get_v1"
HISTORICAL_L_PACK_BID_PX = "63043.4"
HISTORICAL_L_PACK_ASK_PX = "63043.5"
HISTORICAL_S_PACK_BID_PX = "62985.9"
HISTORICAL_S_PACK_ASK_PX = "62986"
Z2G_MARKPX_CURRENT_VALUE = "64495.3"
TICK_SZ_INSTRUMENT_METADATA = "0.1"
TICK_SZ_ROLE = "CANONICAL_INSTRUMENT_METADATA_NOT_USDC_PRECISION_NOT_FETCHED_THIS_STEP"

EVIDENCE_SURFACE_CLASSIFICATION: dict[str, Any] = {
    "ENDPOINT": TICKER_QUERY_PATH,
    "HOST": REUSED_BINDING_REST_HOST,
    "METHOD": "GET",
    "AUTHENTICATION_REQUIREMENT": "NONE_PUBLIC",
    "READ_ONLY": True,
    "TERM_CAN_INSTANTIATE": "SLIPPAGE_BID_ASK_CURRENT_VALUE_OBSERVATIONAL",
    "TERM_CANNOT_PROVE": (
        "SLIPPAGE_RESERVE_NUMERIC;MONETARY_BASE;FX;ROUNDING;"
        "EXACT_OKX_FEE_FORMULA;POSITION_VALUE_ALGEBRA;"
        "MARKPX_OKX_DELIVERY_FEE_OPERAND;MM_LIQ_BUFFER;COVER_USDC"
    ),
    "TIMESTAMP_REQUIREMENTS": (
        "CAPTURE_PROVIDER_TS_AND_RECEIVE_TS;NO_TTL_INVENTED;HISTORICAL_L_S_PACK_NOT_SUBSTITUTED"
    ),
    "INSTRUMENT_BINDING": DEFAULT_INSTRUMENT_ID,
    "ACCOUNT_BINDING": "NONE_PUBLIC_ENDPOINT",
    "FIELD_NORMATIVE_STATUS": (
        "OBSERVATIONAL_CURRENT_BID_ASK_NOT_SLIPPAGE_RESERVE_NOT_MARKPX_SUBSTITUTE"
    ),
}


class CoverUsdcCurrentTickerBidAskEvidenceError(RuntimeError):
    """Fail-closed current ticker bid/ask public-GET evidence violation."""


@dataclass(frozen=True)
class CurrentTickerBidAskPublicGetEvidenceV1:
    bid_ask_term_status: str
    bid_px_current_value: str
    ask_px_current_value: str
    bid_ask_role: str
    slippage_reserve_instance_status: str
    slippage_reserve_numeric_status: str
    provider_ts_ms: str
    receive_ts_unix: str
    historical_bid_ask_is_not_current: bool
    historical_l_or_s_pack_substituted: bool
    ticker_markpx_substituted: bool
    qty_term_status: str
    ctval_term_status: str
    ctval_bound_value: str
    ctval_bound_ccy: str
    ctval_delivery_fee_operand_status: str
    markpx_term_status: str
    markpx_current_value: str
    markpx_okx_delivery_fee_operand_status: str
    tick_sz_instrument_metadata: str
    tick_sz_role: str
    tick_sz_is_not_usdc_precision: bool
    monetary_base_status: str
    fx_status: str
    rounding_status: str
    exact_okx_fee_formula_status: str
    position_value_algebra_status: str
    mm_liq_buffer_instance_status: str
    normal_expiry_rate_0_0001_status: str
    conservative_rate_0_0003_status: str
    b08_internal_algebra_status: str
    cover_usdc_status: str
    numeric_funding_amount: str
    numeric_funding_amount_produced: bool
    exchange_truth_changed: bool
    instrument_id: str
    host: str
    endpoint: str
    method: str
    authentication_requirement: str
    evidence_read_only: bool
    http_status: int
    okx_code: str
    get_request_count: int
    post_count: int
    owner_go: str
    authorization_scope: str
    live_authorized: bool
    testnet_authorized: bool
    scaling_authorized: bool
    multi_future_authorized: bool
    order_effect: str
    funding_executed: bool
    next_canonical_pointer: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "BID_ASK_TERM_STATUS": self.bid_ask_term_status,
            "BID_PX_CURRENT_VALUE": self.bid_px_current_value,
            "ASK_PX_CURRENT_VALUE": self.ask_px_current_value,
            "BID_ASK_ROLE": self.bid_ask_role,
            "SLIPPAGE_RESERVE_INSTANCE_STATUS": self.slippage_reserve_instance_status,
            "SLIPPAGE_RESERVE_NUMERIC_STATUS": self.slippage_reserve_numeric_status,
            "PROVIDER_TS_MS": self.provider_ts_ms,
            "RECEIVE_TS_UNIX": self.receive_ts_unix,
            "HISTORICAL_BID_ASK_IS_NOT_CURRENT": self.historical_bid_ask_is_not_current,
            "HISTORICAL_L_OR_S_PACK_SUBSTITUTED": (self.historical_l_or_s_pack_substituted),
            "TICKER_MARKPX_SUBSTITUTED": self.ticker_markpx_substituted,
            "QTY_TERM_STATUS": self.qty_term_status,
            "CTVAL_TERM_STATUS": self.ctval_term_status,
            "CTVAL_BOUND_VALUE": self.ctval_bound_value,
            "CTVAL_BOUND_CCY": self.ctval_bound_ccy,
            "CTVAL_DELIVERY_FEE_OPERAND_STATUS": (self.ctval_delivery_fee_operand_status),
            "MARKPX_TERM_STATUS": self.markpx_term_status,
            "MARKPX_CURRENT_VALUE": self.markpx_current_value,
            "MARKPX_OKX_DELIVERY_FEE_OPERAND_STATUS": (self.markpx_okx_delivery_fee_operand_status),
            "TICK_SZ_INSTRUMENT_METADATA": self.tick_sz_instrument_metadata,
            "TICK_SZ_ROLE": self.tick_sz_role,
            "TICK_SZ_IS_NOT_USDC_PRECISION": self.tick_sz_is_not_usdc_precision,
            "MONETARY_BASE_STATUS": self.monetary_base_status,
            "FX_STATUS": self.fx_status,
            "ROUNDING_STATUS": self.rounding_status,
            "EXACT_OKX_FEE_FORMULA_STATUS": self.exact_okx_fee_formula_status,
            "POSITION_VALUE_ALGEBRA_STATUS": self.position_value_algebra_status,
            "MM_LIQ_BUFFER_INSTANCE_STATUS": self.mm_liq_buffer_instance_status,
            "NORMAL_EXPIRY_RATE_0_0001_STATUS": self.normal_expiry_rate_0_0001_status,
            "CONSERVATIVE_RATE_0_0003_STATUS": self.conservative_rate_0_0003_status,
            "B08_INTERNAL_ALGEBRA_STATUS": self.b08_internal_algebra_status,
            "COVER_USDC_STATUS": self.cover_usdc_status,
            "NUMERIC_FUNDING_AMOUNT": self.numeric_funding_amount,
            "NUMERIC_FUNDING_AMOUNT_PRODUCED": self.numeric_funding_amount_produced,
            "EXCHANGE_TRUTH_CHANGED": self.exchange_truth_changed,
            "INSTRUMENT_ID": self.instrument_id,
            "HOST": self.host,
            "ENDPOINT": self.endpoint,
            "METHOD": self.method,
            "AUTHENTICATION_REQUIREMENT": self.authentication_requirement,
            "EVIDENCE_READ_ONLY": self.evidence_read_only,
            "HTTP_STATUS": self.http_status,
            "OKX_CODE": self.okx_code,
            "GET_REQUEST_COUNT": self.get_request_count,
            "POST_COUNT": self.post_count,
            "OWNER_GO": self.owner_go,
            "AUTHORIZATION_SCOPE": self.authorization_scope,
            "LIVE_AUTHORIZED": self.live_authorized,
            "TESTNET_AUTHORIZED": self.testnet_authorized,
            "SCALING_AUTHORIZED": self.scaling_authorized,
            "MULTI_FUTURE_AUTHORIZED": self.multi_future_authorized,
            "ORDER_EFFECT": self.order_effect,
            "FUNDING_EXECUTED": self.funding_executed,
            "NEXT_CANONICAL_POINTER": self.next_canonical_pointer,
        }


def classify_current_ticker_bid_ask_evidence_surface_v1() -> dict[str, Any]:
    return dict(EVIDENCE_SURFACE_CLASSIFICATION)


def _require_positive_decimal(raw: str | None, *, field: str) -> Decimal:
    text = str(raw or "").strip()
    if not text:
        raise CoverUsdcCurrentTickerBidAskEvidenceError(f"MISSING_TICKER_FIELD:{field}")
    try:
        value = Decimal(text)
    except (InvalidOperation, TypeError) as exc:
        raise CoverUsdcCurrentTickerBidAskEvidenceError(f"INVALID_TICKER_FIELD:{field}") from exc
    if value <= 0:
        raise CoverUsdcCurrentTickerBidAskEvidenceError(f"NON_POSITIVE_TICKER_FIELD:{field}")
    return value


def _assert_ticker_query(endpoint: str, *, instrument_id: str) -> None:
    parts = urlsplit(str(endpoint or "").strip())
    path = parts.path or str(endpoint or "").strip().split("?", 1)[0]
    if path != TICKER_ENDPOINT:
        raise CoverUsdcCurrentTickerBidAskEvidenceError(f"ENDPOINT_NOT_TICKER:{endpoint}")
    query = parse_qs(parts.query, keep_blank_values=True)
    inst_id = (query.get("instId") or [""])[0]
    if inst_id != instrument_id:
        raise CoverUsdcCurrentTickerBidAskEvidenceError(f"INSTRUMENT_BINDING_MISMATCH:{inst_id}")
    extra = set(query) - {"instId"}
    if extra:
        raise CoverUsdcCurrentTickerBidAskEvidenceError(f"UNEXPECTED_QUERY_PARAM:{sorted(extra)}")


def extract_current_bid_ask_from_public_ticker_payload_v1(
    payload: Mapping[str, Any],
    *,
    expected_instrument_id: str,
) -> tuple[str, str, str]:
    """Return (bidPx, askPx, provider ts ms). No last/markPx substitution."""
    code = str(payload.get("code") or "")
    if code != "0":
        raise CoverUsdcCurrentTickerBidAskEvidenceError(f"OKX_CODE_NOT_SUCCESS:{code}")
    data = payload.get("data")
    if not isinstance(data, list) or not data:
        raise CoverUsdcCurrentTickerBidAskEvidenceError("PUBLIC_TICKER_RESPONSE_EMPTY")
    if len(data) != 1:
        raise CoverUsdcCurrentTickerBidAskEvidenceError("PUBLIC_TICKER_ROW_COUNT_NOT_ONE")
    row = data[0]
    if not isinstance(row, Mapping):
        raise CoverUsdcCurrentTickerBidAskEvidenceError("PUBLIC_TICKER_ROW_INVALID")
    returned_inst = str(row.get("instId") or "").strip()
    if returned_inst != expected_instrument_id:
        raise CoverUsdcCurrentTickerBidAskEvidenceError(
            f"VENUE_INSTRUMENT_RESPONSE_MISMATCH:{returned_inst}"
        )
    if "bidPx" not in row:
        raise CoverUsdcCurrentTickerBidAskEvidenceError("REQUIRED_PRICE_FIELD_MISSING:bidPx")
    if "askPx" not in row:
        raise CoverUsdcCurrentTickerBidAskEvidenceError("REQUIRED_PRICE_FIELD_MISSING:askPx")
    raw_bid = row.get("bidPx")
    raw_ask = row.get("askPx")
    if raw_bid is None or str(raw_bid).strip() == "":
        raise CoverUsdcCurrentTickerBidAskEvidenceError("REQUIRED_PRICE_FIELD_MISSING:bidPx")
    if raw_ask is None or str(raw_ask).strip() == "":
        raise CoverUsdcCurrentTickerBidAskEvidenceError("REQUIRED_PRICE_FIELD_MISSING:askPx")
    bid_text = str(raw_bid).strip()
    ask_text = str(raw_ask).strip()
    bid_value = _require_positive_decimal(bid_text, field="bidPx")
    ask_value = _require_positive_decimal(ask_text, field="askPx")
    if ask_value < bid_value:
        raise CoverUsdcCurrentTickerBidAskEvidenceError("CROSSED_BOOK_ASK_LT_BID")
    raw_ts = row.get("ts")
    if raw_ts is None or str(raw_ts).strip() == "":
        raise CoverUsdcCurrentTickerBidAskEvidenceError("MARKET_DATA_TIMESTAMP_MISSING")
    ts_text = str(raw_ts).strip()
    try:
        ts_ms = int(ts_text)
    except (TypeError, ValueError) as exc:
        raise CoverUsdcCurrentTickerBidAskEvidenceError(
            "MARKET_DATA_TIMESTAMP_UNPARSEABLE"
        ) from exc
    if ts_ms <= 0:
        raise CoverUsdcCurrentTickerBidAskEvidenceError("MARKET_DATA_TIMESTAMP_MISSING")
    return bid_text, ask_text, ts_text


def adjudicate_current_ticker_bid_ask_public_get_v1(
    *,
    bid_px_current_value: str,
    ask_px_current_value: str,
    provider_ts_ms: str,
    receive_ts_unix: str,
    instrument_id: str,
    host: str,
    endpoint: str,
    http_status: int,
    okx_code: str,
    get_request_count: int,
    post_count: int,
    owner_go: str,
    substitute_historical_bid_ask: bool = False,
    substitute_ticker_markpx: bool = False,
    instantiate_slippage_reserve_numeric: bool = False,
    instantiate_cover_usdc: bool = False,
    invent_monetary_base: bool = False,
    apply_usd_usdc_conversion: bool = False,
    assume_usd_equals_usdc: bool = False,
    apply_rounding: bool = False,
    produce_numeric_funding_amount: bool = False,
    collect_mmr: bool = False,
    live_authorized: bool = False,
    testnet_authorized: bool = False,
    scaling_authorized: bool = False,
    multi_future_authorized: bool = False,
) -> CurrentTickerBidAskPublicGetEvidenceV1:
    if owner_go != OWNER_GO:
        raise CoverUsdcCurrentTickerBidAskEvidenceError(f"OWNER_GO_MISMATCH:{owner_go}")
    if substitute_historical_bid_ask:
        raise CoverUsdcCurrentTickerBidAskEvidenceError("HISTORICAL_BID_ASK_IS_NOT_CURRENT")
    if substitute_ticker_markpx:
        raise CoverUsdcCurrentTickerBidAskEvidenceError("TICKER_MARKPX_IS_NOT_MARK_PRICE_GET")
    if instantiate_slippage_reserve_numeric:
        raise CoverUsdcCurrentTickerBidAskEvidenceError(
            "SLIPPAGE_RESERVE_NUMERIC_REMAINS_UNINSTANTIATED"
        )
    if instantiate_cover_usdc:
        raise CoverUsdcCurrentTickerBidAskEvidenceError("COVER_USDC_REMAINS_UNINSTANTIATED")
    if invent_monetary_base:
        raise CoverUsdcCurrentTickerBidAskEvidenceError("MONETARY_BASE_REMAINS_UNPROVEN")
    if apply_usd_usdc_conversion or assume_usd_equals_usdc or USD_USDC_PARITY_ASSUMED:
        raise CoverUsdcCurrentTickerBidAskEvidenceError("USD_USDC_CONVERSION_UNPROVEN")
    if apply_rounding:
        raise CoverUsdcCurrentTickerBidAskEvidenceError("USDC_ROUNDING_PRECISION_UNPROVEN")
    if produce_numeric_funding_amount or NUMERIC_FUNDING_AMOUNT_PRODUCED:
        raise CoverUsdcCurrentTickerBidAskEvidenceError("NUMERIC_FUNDING_AMOUNT_REMAINS_UNPROVEN")
    if collect_mmr:
        raise CoverUsdcCurrentTickerBidAskEvidenceError("MMR_NOT_IN_THIS_GET_SCOPE")
    if live_authorized or LIVE_AUTHORIZED:
        raise CoverUsdcCurrentTickerBidAskEvidenceError("LIVE_NOT_AUTHORIZED")
    if testnet_authorized or TESTNET_AUTHORIZED:
        raise CoverUsdcCurrentTickerBidAskEvidenceError("TESTNET_NOT_AUTHORIZED")
    if scaling_authorized or SCALING_AUTHORIZED:
        raise CoverUsdcCurrentTickerBidAskEvidenceError("SCALING_NOT_AUTHORIZED")
    if multi_future_authorized or MULTI_FUTURE_AUTHORIZED:
        raise CoverUsdcCurrentTickerBidAskEvidenceError("MULTI_FUTURE_NOT_AUTHORIZED")
    if post_count != 0:
        raise CoverUsdcCurrentTickerBidAskEvidenceError("POST_NOT_AUTHORIZED")
    if get_request_count != 1:
        raise CoverUsdcCurrentTickerBidAskEvidenceError("GET_REQUEST_COUNT_NOT_ONE")
    if int(http_status) != 200:
        raise CoverUsdcCurrentTickerBidAskEvidenceError(f"HTTP_STATUS_NOT_200:{http_status}")
    if str(okx_code) != "0":
        raise CoverUsdcCurrentTickerBidAskEvidenceError(f"OKX_CODE_NOT_SUCCESS:{okx_code}")
    if host != REUSED_BINDING_REST_HOST:
        raise CoverUsdcCurrentTickerBidAskEvidenceError(f"HOST_MISMATCH:{host}")
    iid = str(instrument_id or "").strip()
    assert_live_canary_instrument_binding_v1(instrument_id=iid, inst_type=DEFAULT_INST_TYPE)
    _assert_ticker_query(endpoint, instrument_id=iid)
    bid_value = _require_positive_decimal(bid_px_current_value, field="bidPx")
    ask_value = _require_positive_decimal(ask_px_current_value, field="askPx")
    if ask_value < bid_value:
        raise CoverUsdcCurrentTickerBidAskEvidenceError("CROSSED_BOOK_ASK_LT_BID")
    _require_positive_decimal(str(provider_ts_ms).strip(), field="ts")
    if USD_USDC_CONVERSION_APPLIED:
        raise CoverUsdcCurrentTickerBidAskEvidenceError("USD_USDC_CONVERSION_UNPROVEN")
    if not TICK_SZ_IS_NOT_USDC_PRECISION:
        raise CoverUsdcCurrentTickerBidAskEvidenceError("TICK_SZ_IS_NOT_USDC_PRECISION")
    return CurrentTickerBidAskPublicGetEvidenceV1(
        bid_ask_term_status=BID_ASK_TERM_STATUS,
        bid_px_current_value=str(bid_px_current_value).strip(),
        ask_px_current_value=str(ask_px_current_value).strip(),
        bid_ask_role=BID_ASK_ROLE,
        slippage_reserve_instance_status=SLIPPAGE_RESERVE_INSTANCE_STATUS,
        slippage_reserve_numeric_status=SLIPPAGE_RESERVE_NUMERIC_STATUS,
        provider_ts_ms=str(provider_ts_ms).strip(),
        receive_ts_unix=str(receive_ts_unix),
        historical_bid_ask_is_not_current=True,
        historical_l_or_s_pack_substituted=False,
        ticker_markpx_substituted=False,
        qty_term_status="PROVEN",
        ctval_term_status="PROVEN",
        ctval_bound_value=CTVAL_BOUND_VALUE,
        ctval_bound_ccy=CTVAL_BOUND_CCY,
        ctval_delivery_fee_operand_status=CTVAL_DELIVERY_FEE_OPERAND_STATUS,
        markpx_term_status=MARKPX_TERM_STATUS,
        markpx_current_value=Z2G_MARKPX_CURRENT_VALUE,
        markpx_okx_delivery_fee_operand_status=MARKPX_OKX_DELIVERY_FEE_OPERAND_STATUS,
        tick_sz_instrument_metadata=TICK_SZ_INSTRUMENT_METADATA,
        tick_sz_role=TICK_SZ_ROLE,
        tick_sz_is_not_usdc_precision=True,
        monetary_base_status=MONETARY_BASE_STATUS,
        fx_status=FX_STATUS,
        rounding_status=ROUNDING_STATUS,
        exact_okx_fee_formula_status=EXACT_OKX_FEE_FORMULA_STATUS,
        position_value_algebra_status=OKX_POSITION_VALUE_ALGEBRA_STATUS,
        mm_liq_buffer_instance_status=MM_LIQ_BUFFER_STATUS,
        normal_expiry_rate_0_0001_status=NORMAL_EXPIRY_RATE_0_0001_STATUS,
        conservative_rate_0_0003_status=CONSERVATIVE_RATE_0_0003_STATUS,
        b08_internal_algebra_status=B08_EXACT_FORMULA_BODY_STATUS,
        cover_usdc_status=COVER_USDC_STATUS,
        numeric_funding_amount=NUMERIC_FUNDING_AMOUNT,
        numeric_funding_amount_produced=False,
        exchange_truth_changed=EXCHANGE_TRUTH_CHANGED,
        instrument_id=iid,
        host=host,
        endpoint=endpoint,
        method="GET",
        authentication_requirement="NONE_PUBLIC",
        evidence_read_only=True,
        http_status=int(http_status),
        okx_code=str(okx_code),
        get_request_count=int(get_request_count),
        post_count=int(post_count),
        owner_go=OWNER_GO,
        authorization_scope=AUTHORIZED_SCOPE,
        live_authorized=False,
        testnet_authorized=False,
        scaling_authorized=False,
        multi_future_authorized=False,
        order_effect="NONE",
        funding_executed=False,
        next_canonical_pointer=NEXT_CANONICAL_POINTER,
    )


def collect_current_ticker_bid_ask_public_get_v1(
    *,
    transport: LiveCanaryTransportV1,
    receive_ts_unix: str,
    owner_go: str = OWNER_GO,
    instrument_id: str = DEFAULT_INSTRUMENT_ID,
    rest_host: str = REUSED_BINDING_REST_HOST,
    timeout_seconds: float = 10.0,
) -> tuple[CurrentTickerBidAskPublicGetEvidenceV1, dict[str, Any], LiveCanaryHttpResponseV1]:
    """Execute exactly one public ticker GET and adjudicate observationally."""
    if owner_go != OWNER_GO:
        raise CoverUsdcCurrentTickerBidAskEvidenceError(f"OWNER_GO_MISMATCH:{owner_go}")
    assert_live_canary_instrument_binding_v1(instrument_id=instrument_id)
    endpoint = f"{TICKER_ENDPOINT}?instId={instrument_id}"
    _assert_ticker_query(endpoint, instrument_id=instrument_id)
    if rest_host != REUSED_BINDING_REST_HOST:
        raise CoverUsdcCurrentTickerBidAskEvidenceError(f"HOST_MISMATCH:{rest_host}")
    headers = {"User-Agent": USER_AGENT_CANARY, "Accept": "application/json"}
    assert_no_demo_simulation_headers_v1(headers)
    request = LiveCanaryHttpRequestV1(
        method="GET",
        url=f"https://{rest_host}{endpoint}",
        host=rest_host,
        endpoint=endpoint,
        headers=headers,
        timeout_seconds=timeout_seconds,
        body_text="",
    )
    response = transport.send(request)
    if response.method != "GET":
        raise CoverUsdcCurrentTickerBidAskEvidenceError("TRANSPORT_RETURNED_NON_GET")
    http_evidence = extract_canary_http_response_evidence_v1(
        status_code=response.status_code,
        body_bytes=response.body_bytes,
        headers=response.response_headers_safe,
        redirect_followed=response.redirect_followed,
        redirect_status=response.redirect_status,
        redirect_location=response.redirect_location,
    )
    payload = parse_json_object_v1(response.body_bytes)
    bid_text, ask_text, ts_text = extract_current_bid_ask_from_public_ticker_payload_v1(
        payload,
        expected_instrument_id=instrument_id,
    )
    adjudication = adjudicate_current_ticker_bid_ask_public_get_v1(
        bid_px_current_value=bid_text,
        ask_px_current_value=ask_text,
        provider_ts_ms=ts_text,
        receive_ts_unix=receive_ts_unix,
        instrument_id=instrument_id,
        host=rest_host,
        endpoint=endpoint,
        http_status=response.status_code,
        okx_code=str(payload.get("code") or ""),
        get_request_count=1,
        post_count=0,
        owner_go=owner_go,
    )
    snapshot = {
        "DOCUMENT_CLASS": "SECTION_11_13_5_Z2H_CURRENT_TICKER_BID_ASK_PUBLIC_GET_EVIDENCE_V1",
        "DOCUMENT_ROLE": "GET_ONLY_FRESH_EVIDENCE_NON_SSOT_NOT_COVER_USDC",
        "OWNER_GO": OWNER_GO,
        "OWNER_GO_SCOPE": AUTHORIZED_SCOPE,
        "METHOD": "GET",
        "POST_COUNT": 0,
        "GET_REQUEST_COUNT": 1,
        "HOST": rest_host,
        "CANARY_INSTRUMENT": instrument_id,
        "ENDPOINT": endpoint,
        "AUTHENTICATION_REQUIREMENT": "NONE_PUBLIC",
        "EVIDENCE_READ_ONLY": True,
        "SECRET_VALUES_INCLUDED": False,
        "classification": classify_current_ticker_bid_ask_evidence_surface_v1(),
        "http_evidence": http_evidence,
        "response_headers_safe": safe_response_headers_v1(response.response_headers_safe),
        "payload": payload,
        "adjudication": adjudication.to_dict(),
        "QTY_BOUND_VALUE": QTY_BOUND_VALUE,
        "QTY_LIMIT": str(QTY_LIMIT),
        "AUTHORIZATION_SCOPE_CANARY": AUTHORIZATION_SCOPE,
        "B08_INTERNAL_ALGEBRA_STATUS": B08_EXACT_FORMULA_BODY_STATUS,
        "Z2E_SLIPPAGE_RESERVE_STATUS": SLIPPAGE_RESERVE_STATUS,
        "HISTORICAL_L_PACK_BID_PX": HISTORICAL_L_PACK_BID_PX,
        "HISTORICAL_L_PACK_ASK_PX": HISTORICAL_L_PACK_ASK_PX,
        "HISTORICAL_S_PACK_BID_PX": HISTORICAL_S_PACK_BID_PX,
        "HISTORICAL_S_PACK_ASK_PX": HISTORICAL_S_PACK_ASK_PX,
        "HISTORICAL_BID_ASK_IS_NOT_CURRENT": True,
        "Z2G_MARKPX_CURRENT_VALUE": Z2G_MARKPX_CURRENT_VALUE,
        "TICKER_MARKPX_NOT_USED_AS_MARK_PRICE": True,
        "NO_INSTRUMENTS_GET_THIS_STEP": True,
        "NO_POSITION_TIERS_GET_THIS_STEP": True,
    }
    return adjudication, snapshot, response


def persist_current_ticker_bid_ask_public_get_evidence_v1(
    *,
    evidence_root: str | Path,
    run_id: str,
    bound_origin_main_sha: str,
    adjudication: CurrentTickerBidAskPublicGetEvidenceV1,
    snapshot: Mapping[str, Any],
) -> dict[str, Any]:
    root = Path(evidence_root)
    root.mkdir(parents=True, exist_ok=True)
    claims = {
        "DOCUMENT_CLASS": "SECTION_11_13_5_Z2H_CURRENT_TICKER_BID_ASK_PUBLIC_GET_EVIDENCE_V1",
        "DOCUMENT_ROLE": "DERIVED_NON_SSOT",
        "OWNER_GO": OWNER_GO,
        "OWNER_GO_STATUS": "CONSUMED",
        "OWNER_GO_SCOPE": AUTHORIZED_SCOPE,
        "BOUND_ORIGIN_MAIN_SHA": bound_origin_main_sha,
        "RUN_ID": run_id,
        "GET_EXECUTED": True,
        "GET_COUNT": 1,
        "POST_COUNT": 0,
        "LIVE_AUTHORIZED": False,
        "TESTNET_AUTHORIZED": False,
        "ORDER_EXECUTED": False,
        "FUNDING_EXECUTED": False,
        "COVER_USDC_STATUS": COVER_USDC_STATUS,
        "NUMERIC_FUNDING_AMOUNT_PRODUCED": False,
        "BID_ASK_TERM_STATUS": adjudication.bid_ask_term_status,
        "BID_PX_CURRENT_VALUE": adjudication.bid_px_current_value,
        "ASK_PX_CURRENT_VALUE": adjudication.ask_px_current_value,
        "SLIPPAGE_RESERVE_INSTANCE_STATUS": (adjudication.slippage_reserve_instance_status),
        "SLIPPAGE_RESERVE_NUMERIC_STATUS": (adjudication.slippage_reserve_numeric_status),
        "MONETARY_BASE_STATUS": adjudication.monetary_base_status,
        "FX_STATUS": adjudication.fx_status,
        "ROUNDING_STATUS": adjudication.rounding_status,
        "EXACT_OKX_FEE_FORMULA_STATUS": adjudication.exact_okx_fee_formula_status,
        "POSITION_VALUE_ALGEBRA_STATUS": adjudication.position_value_algebra_status,
        "MARKPX_OKX_DELIVERY_FEE_OPERAND_STATUS": (
            adjudication.markpx_okx_delivery_fee_operand_status
        ),
        "SECRET_VALUES_INCLUDED": False,
        **adjudication.to_dict(),
    }
    summary = {
        "DOCUMENT_CLASS": "SECTION_11_13_5_Z2H_CURRENT_TICKER_BID_ASK_PUBLIC_GET_EVIDENCE_V1",
        "DOCUMENT_ROLE": "DERIVED_NON_SSOT",
        "OWNER_GO": OWNER_GO,
        "OWNER_GO_STATUS": "CONSUMED",
        "BOUND_ORIGIN_MAIN_SHA": bound_origin_main_sha,
        "RUN_ID": run_id,
        "HOST": adjudication.host,
        "CANARY_INSTRUMENT": adjudication.instrument_id,
        "METHOD": "GET",
        "GET_REQUEST_COUNT": 1,
        "POST_COUNT": 0,
        "HTTP_STATUS": adjudication.http_status,
        "OKX_CODE": adjudication.okx_code,
        "BID_ASK_TERM_STATUS": adjudication.bid_ask_term_status,
        "BID_PX_CURRENT_VALUE": adjudication.bid_px_current_value,
        "ASK_PX_CURRENT_VALUE": adjudication.ask_px_current_value,
        "SLIPPAGE_RESERVE_NUMERIC_STATUS": (adjudication.slippage_reserve_numeric_status),
        "COVER_USDC_STATUS": COVER_USDC_STATUS,
        "NUMERIC_FUNDING_AMOUNT_PRODUCED": False,
        "FUNDING_EXECUTED": False,
        "LIVE_AUTHORIZED": False,
        "SECRET_VALUES_INCLUDED": False,
        "ok": True,
    }
    zero_write = {
        "GET_COUNT": 1,
        "POST_COUNT": 0,
        "PUT_COUNT": 0,
        "PATCH_COUNT": 0,
        "DELETE_COUNT": 0,
        "RETRY_EXECUTED": False,
        "ORDER_EXECUTED": False,
        "SET_LEVERAGE_EXECUTED": False,
        "FUNDING_EXECUTED": False,
    }
    write_json_v1(root / "GET_SNAPSHOT.sanitized.json", dict(snapshot))
    write_json_v1(root / CLAIMS_FILENAME, claims)
    write_json_v1(root / SUMMARY_FILENAME, summary)
    write_json_v1(root / ZERO_WRITE_FILENAME, zero_write)
    persistence = {
        "ok": True,
        "evidence_root": str(root),
        "RUN_ID": run_id,
        "GET_EXECUTED": True,
        "POST_COUNT": 0,
        "COVER_USDC_STATUS": COVER_USDC_STATUS,
        "BID_PX_CURRENT_VALUE": adjudication.bid_px_current_value,
        "ASK_PX_CURRENT_VALUE": adjudication.ask_px_current_value,
        "SECRET_VALUES_INCLUDED": False,
    }
    write_json_v1(
        root / REDACTION_FILENAME,
        {"REDACTION_CHECK_PASS": True, "SECRET_VALUE_PERSISTED": False},
    )
    write_json_v1(root / "PERSISTENCE_RESULT.json", persistence)
    files = (
        "GET_SNAPSHOT.sanitized.json",
        CLAIMS_FILENAME,
        SUMMARY_FILENAME,
        ZERO_WRITE_FILENAME,
        REDACTION_FILENAME,
        "PERSISTENCE_RESULT.json",
    )
    write_manifest_v1(root, files)
    verify = verify_manifest_v1(root)
    if verify["MANIFEST_VERIFY_RC"] != 0:
        raise CoverUsdcCurrentTickerBidAskEvidenceError(f"MANIFEST_VERIFY_FAIL:{verify['errors']}")
    return {**persistence, "MANIFEST_VERIFY_RC": 0}


def encode_fixture_ticker_payload_v1(
    *,
    instrument_id: str,
    bid_px: str,
    ask_px: str,
    ts_ms: str,
    code: str = "0",
    mark_px: str | None = None,
) -> bytes:
    row: dict[str, Any] = {
        "instId": instrument_id,
        "bidPx": bid_px,
        "askPx": ask_px,
        "ts": ts_ms,
    }
    if mark_px is not None:
        row["markPx"] = mark_px
    payload = {"code": code, "msg": "", "data": [row]}
    return json.dumps(payload, separators=(",", ":")).encode("utf-8")


__all__ = (
    "AUTHORIZED_SCOPE",
    "BID_ASK_TERM_STATUS",
    "COVER_USDC_STATUS",
    "CoverUsdcCurrentTickerBidAskEvidenceError",
    "CurrentTickerBidAskPublicGetEvidenceV1",
    "EVIDENCE_DIRNAME",
    "EVIDENCE_SURFACE_CLASSIFICATION",
    "NEXT_CANONICAL_POINTER",
    "OWNER_GO",
    "SLIPPAGE_RESERVE_INSTANCE_STATUS",
    "SLIPPAGE_RESERVE_NUMERIC_STATUS",
    "TICKER_QUERY_PATH",
    "adjudicate_current_ticker_bid_ask_public_get_v1",
    "classify_current_ticker_bid_ask_evidence_surface_v1",
    "collect_current_ticker_bid_ask_public_get_v1",
    "encode_fixture_ticker_payload_v1",
    "extract_current_bid_ask_from_public_ticker_payload_v1",
    "persist_current_ticker_bid_ask_public_get_evidence_v1",
)
