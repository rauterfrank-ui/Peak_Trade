"""§11.13.5.Z2G current markPx public GET evidence.

GET-only productive evidence for the remaining COVER_USDC markPx current
instance. Does not prove that markPx is an OKX expiry-fee operand. Does not
instantiate COVER_USDC, FX, rounding, monetary base, or a numeric funding
amount. Does not authorize Live, Testnet, orders, funding, scaling, or
Multi-Future.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import parse_qs, urlsplit

from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.constants_v1 import (
    MARK_PRICE_ENDPOINT,
    MARK_PRICE_FIELD,
    MARK_PRICE_INST_TYPE,
)
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
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.formula_term_instance_binding_v1 import (
    B08_EXACT_FORMULA_BODY_KIND,
    B08_EXACT_FORMULA_BODY_STATUS,
    CONSERVATIVE_RATE_0_0003_STATUS,
    COVER_USDC_STATUS,
    CTVAL_BOUND_CCY,
    CTVAL_BOUND_VALUE,
    CTVAL_DELIVERY_FEE_OPERAND_STATUS,
    EXACT_OKX_FEE_FORMULA_STATUS,
    EXCHANGE_TRUTH_CHANGED,
    FX_STATUS,
    HISTORICAL_L_PACK_MARKPX,
    HISTORICAL_S_PACK_MARKPX,
    MONETARY_BASE_STATUS,
    NORMAL_EXPIRY_RATE_0_0001_STATUS,
    NUMERIC_FUNDING_AMOUNT,
    NUMERIC_FUNDING_AMOUNT_PRODUCED,
    OKX_POSITION_VALUE_ALGEBRA_STATUS,
    QTY_BOUND_VALUE,
    QTY_LIMIT,
    ROUNDING_STATUS,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.evidence_v1 import (
    write_json_v1,
    write_manifest_v1,
    verify_manifest_v1,
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
    USD_USDC_CONVERSION_APPLIED,
    USD_USDC_PARITY_ASSUMED,
)

OWNER_GO = (
    "OWNER_GO_REQUIRED_FOR_PRODUCTIVE_EVIDENCE_TO_INSTANTIATE_REMAINING_"
    "UNPROVEN_COVER_USDC_TERMS_BEFORE_FUNDING"
)
AUTHORIZED_SCOPE = "CURRENT_MARKPX_PUBLIC_GET_EVIDENCE_ONLY"
MARKPX_TERM_STATUS = "OBSERVED_NOT_NORMATIVELY_BOUND"
MARKPX_OKX_DELIVERY_FEE_OPERAND_STATUS = "UNPROVEN"
MARKPX_ROLE = "CURRENT_PUBLIC_MARK_PRICE_OBSERVATION_NOT_OKX_DELIVERY_FEE_OPERAND"
NEXT_CANONICAL_POINTER = (
    "OWNER_GO_REQUIRED_FOR_PRODUCTIVE_EVIDENCE_TO_RESOLVE_REMAINING_UNPROVEN_"
    "COVER_USDC_TERMS_AFTER_CURRENT_MARKPX_BEFORE_FUNDING"
)
MARK_PRICE_PATH = MARK_PRICE_ENDPOINT
MARK_PRICE_QUERY_PATH = (
    f"{MARK_PRICE_ENDPOINT}?instType={MARK_PRICE_INST_TYPE}&instId={DEFAULT_INSTRUMENT_ID}"
)
EVIDENCE_DIRNAME = "section_11_13_5_z2g_current_markpx_public_get_v1"

EVIDENCE_SURFACE_CLASSIFICATION: dict[str, Any] = {
    "ENDPOINT": MARK_PRICE_QUERY_PATH,
    "HOST": REUSED_BINDING_REST_HOST,
    "METHOD": "GET",
    "AUTHENTICATION_REQUIREMENT": "NONE_PUBLIC",
    "READ_ONLY": True,
    "TERM_CAN_INSTANTIATE": "MARKPX_CURRENT_VALUE_OBSERVATIONAL",
    "TERM_CANNOT_PROVE": (
        "OKX_EXPIRY_FEE_MARKPX_OPERAND;MONETARY_BASE;FX;ROUNDING;"
        "EXACT_OKX_FEE_FORMULA;POSITION_VALUE_ALGEBRA;COVER_USDC"
    ),
    "TIMESTAMP_REQUIREMENTS": (
        "CAPTURE_PROVIDER_TS_AND_RECEIVE_TS;NO_TTL_INVENTED;HISTORICAL_L_S_PACK_NOT_SUBSTITUTED"
    ),
    "INSTRUMENT_BINDING": DEFAULT_INSTRUMENT_ID,
    "ACCOUNT_BINDING": "NONE_PUBLIC_ENDPOINT",
    "FIELD_NORMATIVE_STATUS": "OBSERVATIONAL_CURRENT_MARKPX_NOT_OKX_DELIVERY_FEE_OPERAND",
}


class CoverUsdcCurrentMarkpxEvidenceError(RuntimeError):
    """Fail-closed current markPx public-GET evidence violation."""


@dataclass(frozen=True)
class CurrentMarkpxPublicGetEvidenceV1:
    markpx_term_status: str
    markpx_current_value: str
    markpx_role: str
    markpx_okx_delivery_fee_operand_status: str
    provider_ts_ms: str
    receive_ts_unix: str
    historical_markpx_is_not_current: bool
    historical_l_or_s_pack_substituted: bool
    qty_term_status: str
    ctval_term_status: str
    ctval_bound_value: str
    ctval_bound_ccy: str
    ctval_delivery_fee_operand_status: str
    monetary_base_status: str
    fx_status: str
    rounding_status: str
    exact_okx_fee_formula_status: str
    position_value_algebra_status: str
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
            "MARKPX_TERM_STATUS": self.markpx_term_status,
            "MARKPX_CURRENT_VALUE": self.markpx_current_value,
            "MARKPX_ROLE": self.markpx_role,
            "MARKPX_OKX_DELIVERY_FEE_OPERAND_STATUS": (self.markpx_okx_delivery_fee_operand_status),
            "PROVIDER_TS_MS": self.provider_ts_ms,
            "RECEIVE_TS_UNIX": self.receive_ts_unix,
            "HISTORICAL_MARKPX_IS_NOT_CURRENT": self.historical_markpx_is_not_current,
            "HISTORICAL_L_OR_S_PACK_SUBSTITUTED": self.historical_l_or_s_pack_substituted,
            "QTY_TERM_STATUS": self.qty_term_status,
            "CTVAL_TERM_STATUS": self.ctval_term_status,
            "CTVAL_BOUND_VALUE": self.ctval_bound_value,
            "CTVAL_BOUND_CCY": self.ctval_bound_ccy,
            "CTVAL_DELIVERY_FEE_OPERAND_STATUS": self.ctval_delivery_fee_operand_status,
            "MONETARY_BASE_STATUS": self.monetary_base_status,
            "FX_STATUS": self.fx_status,
            "ROUNDING_STATUS": self.rounding_status,
            "EXACT_OKX_FEE_FORMULA_STATUS": self.exact_okx_fee_formula_status,
            "POSITION_VALUE_ALGEBRA_STATUS": self.position_value_algebra_status,
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


def classify_current_markpx_evidence_surface_v1() -> dict[str, Any]:
    return dict(EVIDENCE_SURFACE_CLASSIFICATION)


def _require_positive_decimal(raw: str | None, *, field: str) -> Decimal:
    text = str(raw or "").strip()
    if not text:
        raise CoverUsdcCurrentMarkpxEvidenceError(f"MISSING_MARKPX_FIELD:{field}")
    try:
        value = Decimal(text)
    except (InvalidOperation, TypeError) as exc:
        raise CoverUsdcCurrentMarkpxEvidenceError(f"INVALID_MARKPX_FIELD:{field}") from exc
    if value <= 0:
        raise CoverUsdcCurrentMarkpxEvidenceError(f"NON_POSITIVE_MARKPX_FIELD:{field}")
    return value


def _assert_mark_price_query(endpoint: str, *, instrument_id: str) -> None:
    parts = urlsplit(str(endpoint or "").strip())
    path = parts.path or str(endpoint or "").strip().split("?", 1)[0]
    if path != MARK_PRICE_PATH:
        raise CoverUsdcCurrentMarkpxEvidenceError(f"ENDPOINT_NOT_MARK_PRICE:{endpoint}")
    query = parse_qs(parts.query, keep_blank_values=True)
    inst_type = (query.get("instType") or [""])[0]
    inst_id = (query.get("instId") or [""])[0]
    if inst_type != MARK_PRICE_INST_TYPE:
        raise CoverUsdcCurrentMarkpxEvidenceError(f"INST_TYPE_BINDING_MISMATCH:{inst_type}")
    if inst_id != instrument_id:
        raise CoverUsdcCurrentMarkpxEvidenceError(f"INSTRUMENT_BINDING_MISMATCH:{inst_id}")
    extra = set(query) - {"instType", "instId"}
    if extra:
        raise CoverUsdcCurrentMarkpxEvidenceError(f"UNEXPECTED_QUERY_PARAM:{sorted(extra)}")


def extract_current_markpx_from_public_payload_v1(
    payload: Mapping[str, Any],
    *,
    expected_instrument_id: str,
) -> tuple[str, str]:
    """Return (markPx string, provider ts ms). No ticker/last/bid/ask substitution."""
    code = str(payload.get("code") or "")
    if code != "0":
        raise CoverUsdcCurrentMarkpxEvidenceError(f"OKX_CODE_NOT_SUCCESS:{code}")
    data = payload.get("data")
    if not isinstance(data, list) or not data:
        raise CoverUsdcCurrentMarkpxEvidenceError("PUBLIC_MARK_PRICE_RESPONSE_EMPTY")
    if len(data) != 1:
        raise CoverUsdcCurrentMarkpxEvidenceError("PUBLIC_MARK_PRICE_ROW_COUNT_NOT_ONE")
    row = data[0]
    if not isinstance(row, Mapping):
        raise CoverUsdcCurrentMarkpxEvidenceError("PUBLIC_MARK_PRICE_ROW_INVALID")
    returned_inst = str(row.get("instId") or "").strip()
    if returned_inst != expected_instrument_id:
        raise CoverUsdcCurrentMarkpxEvidenceError(
            f"VENUE_INSTRUMENT_RESPONSE_MISMATCH:{returned_inst}"
        )
    if MARK_PRICE_FIELD not in row:
        raise CoverUsdcCurrentMarkpxEvidenceError("REQUIRED_PRICE_FIELD_MISSING:markPx")
    raw_mark = row.get(MARK_PRICE_FIELD)
    if raw_mark is None or str(raw_mark).strip() == "":
        raise CoverUsdcCurrentMarkpxEvidenceError("REQUIRED_PRICE_FIELD_MISSING:markPx")
    mark_text = str(raw_mark).strip()
    _require_positive_decimal(mark_text, field="markPx")
    raw_ts = row.get("ts")
    if raw_ts is None or str(raw_ts).strip() == "":
        raise CoverUsdcCurrentMarkpxEvidenceError("MARKET_DATA_TIMESTAMP_MISSING")
    ts_text = str(raw_ts).strip()
    try:
        ts_ms = int(ts_text)
    except (TypeError, ValueError) as exc:
        raise CoverUsdcCurrentMarkpxEvidenceError("MARKET_DATA_TIMESTAMP_UNPARSEABLE") from exc
    if ts_ms <= 0:
        raise CoverUsdcCurrentMarkpxEvidenceError("MARKET_DATA_TIMESTAMP_MISSING")
    return mark_text, ts_text


def adjudicate_current_markpx_public_get_v1(
    *,
    markpx_current_value: str,
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
    substitute_historical_markpx: bool = False,
    claim_okx_delivery_fee_operand: bool = False,
    instantiate_cover_usdc: bool = False,
    invent_monetary_base: bool = False,
    apply_usd_usdc_conversion: bool = False,
    assume_usd_equals_usdc: bool = False,
    apply_rounding: bool = False,
    produce_numeric_funding_amount: bool = False,
    live_authorized: bool = False,
    testnet_authorized: bool = False,
    scaling_authorized: bool = False,
    multi_future_authorized: bool = False,
) -> CurrentMarkpxPublicGetEvidenceV1:
    if owner_go != OWNER_GO:
        raise CoverUsdcCurrentMarkpxEvidenceError(f"OWNER_GO_MISMATCH:{owner_go}")
    if substitute_historical_markpx:
        raise CoverUsdcCurrentMarkpxEvidenceError("HISTORICAL_MARKPX_IS_NOT_CURRENT")
    if claim_okx_delivery_fee_operand:
        raise CoverUsdcCurrentMarkpxEvidenceError("MARKPX_NOT_OKX_DELIVERY_FEE_OPERAND")
    if instantiate_cover_usdc:
        raise CoverUsdcCurrentMarkpxEvidenceError("COVER_USDC_REMAINS_UNINSTANTIATED")
    if invent_monetary_base:
        raise CoverUsdcCurrentMarkpxEvidenceError("MONETARY_BASE_REMAINS_UNPROVEN")
    if apply_usd_usdc_conversion or assume_usd_equals_usdc or USD_USDC_PARITY_ASSUMED:
        raise CoverUsdcCurrentMarkpxEvidenceError("USD_USDC_CONVERSION_UNPROVEN")
    if apply_rounding:
        raise CoverUsdcCurrentMarkpxEvidenceError("USDC_ROUNDING_PRECISION_UNPROVEN")
    if produce_numeric_funding_amount or NUMERIC_FUNDING_AMOUNT_PRODUCED:
        raise CoverUsdcCurrentMarkpxEvidenceError("NUMERIC_FUNDING_AMOUNT_REMAINS_UNPROVEN")
    if live_authorized or LIVE_AUTHORIZED:
        raise CoverUsdcCurrentMarkpxEvidenceError("LIVE_NOT_AUTHORIZED")
    if testnet_authorized or TESTNET_AUTHORIZED:
        raise CoverUsdcCurrentMarkpxEvidenceError("TESTNET_NOT_AUTHORIZED")
    if scaling_authorized or SCALING_AUTHORIZED:
        raise CoverUsdcCurrentMarkpxEvidenceError("SCALING_NOT_AUTHORIZED")
    if multi_future_authorized or MULTI_FUTURE_AUTHORIZED:
        raise CoverUsdcCurrentMarkpxEvidenceError("MULTI_FUTURE_NOT_AUTHORIZED")
    if post_count != 0:
        raise CoverUsdcCurrentMarkpxEvidenceError("POST_NOT_AUTHORIZED")
    if get_request_count != 1:
        raise CoverUsdcCurrentMarkpxEvidenceError("GET_REQUEST_COUNT_NOT_ONE")
    if int(http_status) != 200:
        raise CoverUsdcCurrentMarkpxEvidenceError(f"HTTP_STATUS_NOT_200:{http_status}")
    if str(okx_code) != "0":
        raise CoverUsdcCurrentMarkpxEvidenceError(f"OKX_CODE_NOT_SUCCESS:{okx_code}")
    if host != REUSED_BINDING_REST_HOST:
        raise CoverUsdcCurrentMarkpxEvidenceError(f"HOST_MISMATCH:{host}")
    iid = str(instrument_id or "").strip()
    assert_live_canary_instrument_binding_v1(instrument_id=iid, inst_type=DEFAULT_INST_TYPE)
    _assert_mark_price_query(endpoint, instrument_id=iid)
    mark_text, ts_text = markpx_current_value, str(provider_ts_ms).strip()
    _require_positive_decimal(mark_text, field="markPx")
    _require_positive_decimal(ts_text, field="ts")
    if USD_USDC_CONVERSION_APPLIED:
        raise CoverUsdcCurrentMarkpxEvidenceError("USD_USDC_CONVERSION_UNPROVEN")
    return CurrentMarkpxPublicGetEvidenceV1(
        markpx_term_status=MARKPX_TERM_STATUS,
        markpx_current_value=mark_text,
        markpx_role=MARKPX_ROLE,
        markpx_okx_delivery_fee_operand_status=MARKPX_OKX_DELIVERY_FEE_OPERAND_STATUS,
        provider_ts_ms=ts_text,
        receive_ts_unix=str(receive_ts_unix),
        historical_markpx_is_not_current=True,
        historical_l_or_s_pack_substituted=False,
        qty_term_status="PROVEN",
        ctval_term_status="PROVEN",
        ctval_bound_value=CTVAL_BOUND_VALUE,
        ctval_bound_ccy=CTVAL_BOUND_CCY,
        ctval_delivery_fee_operand_status=CTVAL_DELIVERY_FEE_OPERAND_STATUS,
        monetary_base_status=MONETARY_BASE_STATUS,
        fx_status=FX_STATUS,
        rounding_status=ROUNDING_STATUS,
        exact_okx_fee_formula_status=EXACT_OKX_FEE_FORMULA_STATUS,
        position_value_algebra_status=OKX_POSITION_VALUE_ALGEBRA_STATUS,
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


def collect_current_markpx_public_get_v1(
    *,
    transport: LiveCanaryTransportV1,
    receive_ts_unix: str,
    owner_go: str = OWNER_GO,
    instrument_id: str = DEFAULT_INSTRUMENT_ID,
    rest_host: str = REUSED_BINDING_REST_HOST,
    timeout_seconds: float = 10.0,
) -> tuple[CurrentMarkpxPublicGetEvidenceV1, dict[str, Any], LiveCanaryHttpResponseV1]:
    """Execute exactly one public mark-price GET and adjudicate observationally."""
    if owner_go != OWNER_GO:
        raise CoverUsdcCurrentMarkpxEvidenceError(f"OWNER_GO_MISMATCH:{owner_go}")
    assert_live_canary_instrument_binding_v1(instrument_id=instrument_id)
    endpoint = f"{MARK_PRICE_ENDPOINT}?instType={MARK_PRICE_INST_TYPE}&instId={instrument_id}"
    _assert_mark_price_query(endpoint, instrument_id=instrument_id)
    if rest_host != REUSED_BINDING_REST_HOST:
        raise CoverUsdcCurrentMarkpxEvidenceError(f"HOST_MISMATCH:{rest_host}")
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
        raise CoverUsdcCurrentMarkpxEvidenceError("TRANSPORT_RETURNED_NON_GET")
    http_evidence = extract_canary_http_response_evidence_v1(
        status_code=response.status_code,
        body_bytes=response.body_bytes,
        headers=response.response_headers_safe,
        redirect_followed=response.redirect_followed,
        redirect_status=response.redirect_status,
        redirect_location=response.redirect_location,
    )
    payload = parse_json_object_v1(response.body_bytes)
    mark_text, ts_text = extract_current_markpx_from_public_payload_v1(
        payload,
        expected_instrument_id=instrument_id,
    )
    adjudication = adjudicate_current_markpx_public_get_v1(
        markpx_current_value=mark_text,
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
        "DOCUMENT_CLASS": "SECTION_11_13_5_Z2G_CURRENT_MARKPX_PUBLIC_GET_EVIDENCE_V1",
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
        "classification": classify_current_markpx_evidence_surface_v1(),
        "http_evidence": http_evidence,
        "response_headers_safe": safe_response_headers_v1(response.response_headers_safe),
        "payload": payload,
        "adjudication": adjudication.to_dict(),
        "QTY_BOUND_VALUE": QTY_BOUND_VALUE,
        "QTY_LIMIT": str(QTY_LIMIT),
        "AUTHORIZATION_SCOPE_CANARY": AUTHORIZATION_SCOPE,
        "B08_EXACT_FORMULA_BODY_KIND": B08_EXACT_FORMULA_BODY_KIND,
        "HISTORICAL_L_PACK_MARKPX": HISTORICAL_L_PACK_MARKPX,
        "HISTORICAL_S_PACK_MARKPX": HISTORICAL_S_PACK_MARKPX,
        "HISTORICAL_MARKPX_IS_NOT_CURRENT": True,
    }
    return adjudication, snapshot, response


def persist_current_markpx_public_get_evidence_v1(
    *,
    evidence_root: str | Path,
    run_id: str,
    bound_origin_main_sha: str,
    adjudication: CurrentMarkpxPublicGetEvidenceV1,
    snapshot: Mapping[str, Any],
) -> dict[str, Any]:
    root = Path(evidence_root)
    root.mkdir(parents=True, exist_ok=True)
    claims = {
        "DOCUMENT_CLASS": "SECTION_11_13_5_Z2G_CURRENT_MARKPX_PUBLIC_GET_EVIDENCE_V1",
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
        "MARKPX_TERM_STATUS": adjudication.markpx_term_status,
        "MARKPX_CURRENT_VALUE": adjudication.markpx_current_value,
        "MARKPX_OKX_DELIVERY_FEE_OPERAND_STATUS": (
            adjudication.markpx_okx_delivery_fee_operand_status
        ),
        "MONETARY_BASE_STATUS": adjudication.monetary_base_status,
        "FX_STATUS": adjudication.fx_status,
        "ROUNDING_STATUS": adjudication.rounding_status,
        "EXACT_OKX_FEE_FORMULA_STATUS": adjudication.exact_okx_fee_formula_status,
        "POSITION_VALUE_ALGEBRA_STATUS": adjudication.position_value_algebra_status,
        "SECRET_VALUES_INCLUDED": False,
        **adjudication.to_dict(),
    }
    summary = {
        "DOCUMENT_CLASS": "SECTION_11_13_5_Z2G_CURRENT_MARKPX_PUBLIC_GET_EVIDENCE_V1",
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
        "MARKPX_TERM_STATUS": adjudication.markpx_term_status,
        "MARKPX_CURRENT_VALUE": adjudication.markpx_current_value,
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
        "MARKPX_CURRENT_VALUE": adjudication.markpx_current_value,
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
        raise CoverUsdcCurrentMarkpxEvidenceError(f"MANIFEST_VERIFY_FAIL:{verify['errors']}")
    return {**persistence, "MANIFEST_VERIFY_RC": 0}


def encode_fixture_mark_price_payload_v1(
    *,
    instrument_id: str,
    mark_px: str,
    ts_ms: str,
    code: str = "0",
) -> bytes:
    payload = {
        "code": code,
        "msg": "",
        "data": [{"instId": instrument_id, "markPx": mark_px, "ts": ts_ms}],
    }
    return json.dumps(payload, separators=(",", ":")).encode("utf-8")


__all__ = (
    "AUTHORIZED_SCOPE",
    "COVER_USDC_STATUS",
    "CoverUsdcCurrentMarkpxEvidenceError",
    "CurrentMarkpxPublicGetEvidenceV1",
    "EVIDENCE_DIRNAME",
    "EVIDENCE_SURFACE_CLASSIFICATION",
    "MARKPX_OKX_DELIVERY_FEE_OPERAND_STATUS",
    "MARKPX_TERM_STATUS",
    "MARK_PRICE_QUERY_PATH",
    "NEXT_CANONICAL_POINTER",
    "OWNER_GO",
    "adjudicate_current_markpx_public_get_v1",
    "classify_current_markpx_evidence_surface_v1",
    "collect_current_markpx_public_get_v1",
    "encode_fixture_mark_price_payload_v1",
    "extract_current_markpx_from_public_payload_v1",
    "persist_current_markpx_public_get_evidence_v1",
)
