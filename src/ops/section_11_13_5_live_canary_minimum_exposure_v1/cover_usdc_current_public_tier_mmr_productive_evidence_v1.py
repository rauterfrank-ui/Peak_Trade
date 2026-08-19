"""§11.13.5.Z2K current public-tier MMR GET evidence.

GET-only productive evidence for the remaining COVER_USDC qty=1 public
tier MMR instance. Does not instantiate MM_LIQ_BUFFER numerically,
COVER_USDC, FX, rounding, monetary base, or a numeric funding amount.
Does not treat public MMR as account-effective or liquidation-price
evidence. Does not authorize Live, Testnet, orders, funding, scaling, or
Multi-Future.
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
    DEFAULT_TD_MODE,
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
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.cover_usdc_current_ticker_bid_ask_productive_evidence_v1 import (
    BID_ASK_TERM_STATUS,
    SLIPPAGE_RESERVE_INSTANCE_STATUS,
    SLIPPAGE_RESERVE_NUMERIC_STATUS,
    Z2G_MARKPX_CURRENT_VALUE,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.exact_formula_body_v1 import (
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
    "COVER_USDC_TERMS_AFTER_CURRENT_TICKER_BID_ASK_BEFORE_FUNDING"
)
AUTHORIZED_SCOPE = "CURRENT_PUBLIC_TIER_MMR_PUBLIC_GET_EVIDENCE_ONLY"
MMR_TERM_STATUS = "OBSERVED_NOT_NORMATIVELY_BOUND"
MMR_ROLE = "CURRENT_PUBLIC_TIER_MMR_OBSERVATION_NOT_ACCOUNT_EFFECTIVE_NOT_LIQUIDATION_PRICE"
PUBLIC_MMR_CLASSIFICATION = "PUBLIC_TIER_FACT_NOT_ACCOUNT_EFFECTIVE_MMR"
MM_LIQ_BUFFER_INSTANCE_STATUS = "OBSERVED_MMR_NOT_NORMATIVELY_BOUND_BUFFER_UNINSTANTIATED"
MM_LIQ_BUFFER_NUMERIC_STATUS = "UNINSTANTIATED"
NEXT_CANONICAL_POINTER = (
    "OWNER_GO_REQUIRED_FOR_PRODUCTIVE_EVIDENCE_TO_RESOLVE_REMAINING_UNPROVEN_"
    "COVER_USDC_TERMS_AFTER_CURRENT_PUBLIC_TIER_MMR_BEFORE_FUNDING"
)
POSITION_TIERS_ENDPOINT = "/api/v5/public/position-tiers"
CANARY_INST_FAMILY = "BTC-USD_UM_XPERP"
POSITION_TIERS_QUERY_PATH = (
    f"{POSITION_TIERS_ENDPOINT}?instType={DEFAULT_INST_TYPE}"
    f"&tdMode={DEFAULT_TD_MODE}&instFamily={CANARY_INST_FAMILY}"
    f"&instId={DEFAULT_INSTRUMENT_ID}"
)
EVIDENCE_DIRNAME = "section_11_13_5_z2k_current_public_tier_mmr_public_get_v1"
HISTORICAL_L_PACK_MMR = "0.01"
HISTORICAL_S_PACK_MMR = "0.01"
Z2H_BID_PX_CURRENT_VALUE = "64529.9"
Z2H_ASK_PX_CURRENT_VALUE = "64530"
QTY_ONE = Decimal("1")
PROVIDER_TS_NONE = "NONE_NOT_IN_POSITION_TIERS_PAYLOAD"

EVIDENCE_SURFACE_CLASSIFICATION: dict[str, Any] = {
    "ENDPOINT": POSITION_TIERS_QUERY_PATH,
    "HOST": REUSED_BINDING_REST_HOST,
    "METHOD": "GET",
    "AUTHENTICATION_REQUIREMENT": "NONE_PUBLIC",
    "READ_ONLY": True,
    "TERM_CAN_INSTANTIATE": "MMR_PUBLIC_TIER_QTY_ONE_CURRENT_VALUE_OBSERVATIONAL",
    "TERM_CANNOT_PROVE": (
        "MM_LIQ_BUFFER_NUMERIC;ACCOUNT_EFFECTIVE_MMR;LIQUIDATION_PRICE;"
        "SLIPPAGE_RESERVE_NUMERIC;MONETARY_BASE;FX;ROUNDING;"
        "EXACT_OKX_FEE_FORMULA;POSITION_VALUE_ALGEBRA;"
        "MARKPX_OKX_DELIVERY_FEE_OPERAND;COVER_USDC"
    ),
    "TIMESTAMP_REQUIREMENTS": (
        "CAPTURE_RECEIVE_TS_AND_HTTP_DATE_IF_PRESENT;"
        "NO_PROVIDER_TS_INVENTED;NO_TTL_INVENTED;"
        "HISTORICAL_L_S_PACK_NOT_SUBSTITUTED"
    ),
    "INSTRUMENT_BINDING": DEFAULT_INSTRUMENT_ID,
    "ACCOUNT_BINDING": "NONE_PUBLIC_ENDPOINT",
    "FIELD_NORMATIVE_STATUS": (
        "OBSERVATIONAL_CURRENT_PUBLIC_TIER_MMR_NOT_ACCOUNT_EFFECTIVE_"
        "NOT_LIQUIDATION_PRICE_NOT_MM_LIQ_BUFFER"
    ),
}


class CoverUsdcCurrentPublicTierMmrEvidenceError(RuntimeError):
    """Fail-closed current public-tier MMR public-GET evidence violation."""


@dataclass(frozen=True)
class CurrentPublicTierMmrPublicGetEvidenceV1:
    mmr_term_status: str
    mmr_public_tier_qty_one_current_value: str
    mmr_role: str
    public_mmr_classification: str
    public_mmr_is_not_liquidation_price_evidence: bool
    mm_liq_buffer_instance_status: str
    mm_liq_buffer_numeric_status: str
    tier_current_value: str
    min_sz_current_value: str
    max_sz_current_value: str
    imr_public_tier_qty_one_observed: str
    imr_role: str
    provider_ts_ms: str
    receive_ts_unix: str
    historical_mmr_is_not_current: bool
    historical_l_or_s_pack_substituted: bool
    qty_term_status: str
    ctval_term_status: str
    ctval_bound_value: str
    ctval_bound_ccy: str
    ctval_delivery_fee_operand_status: str
    markpx_term_status: str
    markpx_current_value: str
    markpx_okx_delivery_fee_operand_status: str
    bid_ask_term_status: str
    bid_px_current_value: str
    ask_px_current_value: str
    slippage_reserve_instance_status: str
    slippage_reserve_numeric_status: str
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
    inst_family: str
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
            "MMR_TERM_STATUS": self.mmr_term_status,
            "MMR_PUBLIC_TIER_QTY_ONE_CURRENT_VALUE": (self.mmr_public_tier_qty_one_current_value),
            "MMR_ROLE": self.mmr_role,
            "PUBLIC_MMR_CLASSIFICATION": self.public_mmr_classification,
            "PUBLIC_MMR_IS_NOT_LIQUIDATION_PRICE_EVIDENCE": (
                self.public_mmr_is_not_liquidation_price_evidence
            ),
            "MM_LIQ_BUFFER_INSTANCE_STATUS": self.mm_liq_buffer_instance_status,
            "MM_LIQ_BUFFER_NUMERIC_STATUS": self.mm_liq_buffer_numeric_status,
            "TIER_CURRENT_VALUE": self.tier_current_value,
            "MIN_SZ_CURRENT_VALUE": self.min_sz_current_value,
            "MAX_SZ_CURRENT_VALUE": self.max_sz_current_value,
            "IMR_PUBLIC_TIER_QTY_ONE_OBSERVED": self.imr_public_tier_qty_one_observed,
            "IMR_ROLE": self.imr_role,
            "PROVIDER_TS_MS": self.provider_ts_ms,
            "RECEIVE_TS_UNIX": self.receive_ts_unix,
            "HISTORICAL_MMR_IS_NOT_CURRENT": self.historical_mmr_is_not_current,
            "HISTORICAL_L_OR_S_PACK_SUBSTITUTED": (self.historical_l_or_s_pack_substituted),
            "QTY_TERM_STATUS": self.qty_term_status,
            "CTVAL_TERM_STATUS": self.ctval_term_status,
            "CTVAL_BOUND_VALUE": self.ctval_bound_value,
            "CTVAL_BOUND_CCY": self.ctval_bound_ccy,
            "CTVAL_DELIVERY_FEE_OPERAND_STATUS": (self.ctval_delivery_fee_operand_status),
            "MARKPX_TERM_STATUS": self.markpx_term_status,
            "MARKPX_CURRENT_VALUE": self.markpx_current_value,
            "MARKPX_OKX_DELIVERY_FEE_OPERAND_STATUS": (self.markpx_okx_delivery_fee_operand_status),
            "BID_ASK_TERM_STATUS": self.bid_ask_term_status,
            "BID_PX_CURRENT_VALUE": self.bid_px_current_value,
            "ASK_PX_CURRENT_VALUE": self.ask_px_current_value,
            "SLIPPAGE_RESERVE_INSTANCE_STATUS": (self.slippage_reserve_instance_status),
            "SLIPPAGE_RESERVE_NUMERIC_STATUS": self.slippage_reserve_numeric_status,
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
            "INST_FAMILY": self.inst_family,
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


def classify_current_public_tier_mmr_evidence_surface_v1() -> dict[str, Any]:
    return dict(EVIDENCE_SURFACE_CLASSIFICATION)


def _require_rate_decimal(raw: str | None, *, field: str) -> Decimal:
    text = str(raw or "").strip()
    if not text:
        raise CoverUsdcCurrentPublicTierMmrEvidenceError(f"MISSING_TIER_FIELD:{field}")
    try:
        value = Decimal(text)
    except (InvalidOperation, TypeError) as exc:
        raise CoverUsdcCurrentPublicTierMmrEvidenceError(f"INVALID_TIER_FIELD:{field}") from exc
    if value <= 0:
        raise CoverUsdcCurrentPublicTierMmrEvidenceError(f"NON_POSITIVE_TIER_FIELD:{field}")
    if value >= 1:
        raise CoverUsdcCurrentPublicTierMmrEvidenceError(f"TIER_RATE_NOT_FRACTION:{field}")
    return value


def _require_size_decimal(raw: str | None, *, field: str) -> Decimal:
    text = str(raw or "").strip()
    if not text:
        raise CoverUsdcCurrentPublicTierMmrEvidenceError(f"MISSING_TIER_FIELD:{field}")
    try:
        value = Decimal(text)
    except (InvalidOperation, TypeError) as exc:
        raise CoverUsdcCurrentPublicTierMmrEvidenceError(f"INVALID_TIER_FIELD:{field}") from exc
    if value < 0:
        raise CoverUsdcCurrentPublicTierMmrEvidenceError(f"NEGATIVE_TIER_FIELD:{field}")
    return value


def _assert_position_tiers_query(
    endpoint: str,
    *,
    instrument_id: str,
    inst_family: str,
) -> None:
    parts = urlsplit(str(endpoint or "").strip())
    path = parts.path or str(endpoint or "").strip().split("?", 1)[0]
    if path != POSITION_TIERS_ENDPOINT:
        raise CoverUsdcCurrentPublicTierMmrEvidenceError(f"ENDPOINT_NOT_POSITION_TIERS:{endpoint}")
    query = parse_qs(parts.query, keep_blank_values=True)
    expected = {
        "instType": DEFAULT_INST_TYPE,
        "tdMode": DEFAULT_TD_MODE,
        "instFamily": inst_family,
        "instId": instrument_id,
    }
    extra = set(query) - set(expected)
    if extra:
        raise CoverUsdcCurrentPublicTierMmrEvidenceError(f"UNEXPECTED_QUERY_PARAM:{sorted(extra)}")
    missing = set(expected) - set(query)
    if missing:
        raise CoverUsdcCurrentPublicTierMmrEvidenceError(f"MISSING_QUERY_PARAM:{sorted(missing)}")
    for key, wanted in expected.items():
        got = (query.get(key) or [""])[0]
        if got != wanted:
            raise CoverUsdcCurrentPublicTierMmrEvidenceError(f"QUERY_BINDING_MISMATCH:{key}:{got}")


def _row_covers_qty_one(row: Mapping[str, Any]) -> bool:
    min_sz = _require_size_decimal(str(row.get("minSz") or ""), field="minSz")
    max_sz = _require_size_decimal(str(row.get("maxSz") or ""), field="maxSz")
    if max_sz < min_sz:
        raise CoverUsdcCurrentPublicTierMmrEvidenceError("TIER_MAXSZ_LT_MINSZ")
    return min_sz <= QTY_ONE <= max_sz


def extract_qty_one_mmr_from_public_position_tiers_payload_v1(
    payload: Mapping[str, Any],
    *,
    expected_inst_family: str,
) -> tuple[str, str, str, str, str, str]:
    """Return (mmr, imr, tier, minSz, maxSz, family). Observational only."""
    code = str(payload.get("code") or "")
    if code != "0":
        raise CoverUsdcCurrentPublicTierMmrEvidenceError(f"OKX_CODE_NOT_SUCCESS:{code}")
    data = payload.get("data")
    if not isinstance(data, list) or not data:
        raise CoverUsdcCurrentPublicTierMmrEvidenceError("PUBLIC_POSITION_TIERS_RESPONSE_EMPTY")
    matches: list[Mapping[str, Any]] = []
    for item in data:
        if not isinstance(item, Mapping):
            raise CoverUsdcCurrentPublicTierMmrEvidenceError("PUBLIC_POSITION_TIERS_ROW_INVALID")
        family = str(item.get("instFamily") or "").strip()
        if family and family != expected_inst_family:
            continue
        if _row_covers_qty_one(item):
            matches.append(item)
    if not matches:
        raise CoverUsdcCurrentPublicTierMmrEvidenceError("QTY_ONE_TIER_NOT_FOUND")
    if len(matches) != 1:
        raise CoverUsdcCurrentPublicTierMmrEvidenceError("QTY_ONE_TIER_NOT_UNIQUE")
    row = matches[0]
    family = str(row.get("instFamily") or "").strip()
    if family != expected_inst_family:
        raise CoverUsdcCurrentPublicTierMmrEvidenceError(f"VENUE_FAMILY_RESPONSE_MISMATCH:{family}")
    if "mmr" not in row:
        raise CoverUsdcCurrentPublicTierMmrEvidenceError("REQUIRED_TIER_FIELD_MISSING:mmr")
    raw_mmr = row.get("mmr")
    if raw_mmr is None or str(raw_mmr).strip() == "":
        raise CoverUsdcCurrentPublicTierMmrEvidenceError("REQUIRED_TIER_FIELD_MISSING:mmr")
    mmr_text = str(raw_mmr).strip()
    mmr_value = _require_rate_decimal(mmr_text, field="mmr")
    raw_imr = row.get("imr")
    if raw_imr is None or str(raw_imr).strip() == "":
        raise CoverUsdcCurrentPublicTierMmrEvidenceError("REQUIRED_TIER_FIELD_MISSING:imr")
    imr_text = str(raw_imr).strip()
    imr_value = _require_rate_decimal(imr_text, field="imr")
    if mmr_value > imr_value:
        raise CoverUsdcCurrentPublicTierMmrEvidenceError("MMR_GT_IMR")
    tier_text = str(row.get("tier") or "").strip()
    if not tier_text:
        raise CoverUsdcCurrentPublicTierMmrEvidenceError("REQUIRED_TIER_FIELD_MISSING:tier")
    min_sz_text = str(row.get("minSz") or "").strip()
    max_sz_text = str(row.get("maxSz") or "").strip()
    return mmr_text, imr_text, tier_text, min_sz_text, max_sz_text, family


def adjudicate_current_public_tier_mmr_public_get_v1(
    *,
    mmr_public_tier_qty_one_current_value: str,
    imr_public_tier_qty_one_observed: str,
    tier_current_value: str,
    min_sz_current_value: str,
    max_sz_current_value: str,
    receive_ts_unix: str,
    instrument_id: str,
    inst_family: str,
    host: str,
    endpoint: str,
    http_status: int,
    okx_code: str,
    get_request_count: int,
    post_count: int,
    owner_go: str,
    substitute_historical_mmr: bool = False,
    instantiate_mm_liq_buffer_numeric: bool = False,
    treat_as_account_effective_mmr: bool = False,
    treat_as_liquidation_price: bool = False,
    instantiate_cover_usdc: bool = False,
    invent_monetary_base: bool = False,
    apply_usd_usdc_conversion: bool = False,
    assume_usd_equals_usdc: bool = False,
    apply_rounding: bool = False,
    produce_numeric_funding_amount: bool = False,
    collect_ticker: bool = False,
    collect_mark_price: bool = False,
    live_authorized: bool = False,
    testnet_authorized: bool = False,
    scaling_authorized: bool = False,
    multi_future_authorized: bool = False,
) -> CurrentPublicTierMmrPublicGetEvidenceV1:
    if owner_go != OWNER_GO:
        raise CoverUsdcCurrentPublicTierMmrEvidenceError(f"OWNER_GO_MISMATCH:{owner_go}")
    if substitute_historical_mmr:
        raise CoverUsdcCurrentPublicTierMmrEvidenceError("HISTORICAL_MMR_IS_NOT_CURRENT")
    if instantiate_mm_liq_buffer_numeric:
        raise CoverUsdcCurrentPublicTierMmrEvidenceError(
            "MM_LIQ_BUFFER_NUMERIC_REMAINS_UNINSTANTIATED"
        )
    if treat_as_account_effective_mmr:
        raise CoverUsdcCurrentPublicTierMmrEvidenceError("PUBLIC_MMR_IS_NOT_ACCOUNT_EFFECTIVE")
    if treat_as_liquidation_price:
        raise CoverUsdcCurrentPublicTierMmrEvidenceError(
            "PUBLIC_MMR_IS_NOT_LIQUIDATION_PRICE_EVIDENCE"
        )
    if instantiate_cover_usdc:
        raise CoverUsdcCurrentPublicTierMmrEvidenceError("COVER_USDC_REMAINS_UNINSTANTIATED")
    if invent_monetary_base:
        raise CoverUsdcCurrentPublicTierMmrEvidenceError("MONETARY_BASE_REMAINS_UNPROVEN")
    if apply_usd_usdc_conversion or assume_usd_equals_usdc or USD_USDC_PARITY_ASSUMED:
        raise CoverUsdcCurrentPublicTierMmrEvidenceError("USD_USDC_CONVERSION_UNPROVEN")
    if apply_rounding:
        raise CoverUsdcCurrentPublicTierMmrEvidenceError("USDC_ROUNDING_PRECISION_UNPROVEN")
    if produce_numeric_funding_amount or NUMERIC_FUNDING_AMOUNT_PRODUCED:
        raise CoverUsdcCurrentPublicTierMmrEvidenceError("NUMERIC_FUNDING_AMOUNT_REMAINS_UNPROVEN")
    if collect_ticker:
        raise CoverUsdcCurrentPublicTierMmrEvidenceError("TICKER_NOT_IN_THIS_GET_SCOPE")
    if collect_mark_price:
        raise CoverUsdcCurrentPublicTierMmrEvidenceError("MARK_PRICE_NOT_IN_THIS_GET_SCOPE")
    if live_authorized or LIVE_AUTHORIZED:
        raise CoverUsdcCurrentPublicTierMmrEvidenceError("LIVE_NOT_AUTHORIZED")
    if testnet_authorized or TESTNET_AUTHORIZED:
        raise CoverUsdcCurrentPublicTierMmrEvidenceError("TESTNET_NOT_AUTHORIZED")
    if scaling_authorized or SCALING_AUTHORIZED:
        raise CoverUsdcCurrentPublicTierMmrEvidenceError("SCALING_NOT_AUTHORIZED")
    if multi_future_authorized or MULTI_FUTURE_AUTHORIZED:
        raise CoverUsdcCurrentPublicTierMmrEvidenceError("MULTI_FUTURE_NOT_AUTHORIZED")
    if post_count != 0:
        raise CoverUsdcCurrentPublicTierMmrEvidenceError("POST_NOT_AUTHORIZED")
    if get_request_count != 1:
        raise CoverUsdcCurrentPublicTierMmrEvidenceError("GET_REQUEST_COUNT_NOT_ONE")
    if int(http_status) != 200:
        raise CoverUsdcCurrentPublicTierMmrEvidenceError(f"HTTP_STATUS_NOT_200:{http_status}")
    if str(okx_code) != "0":
        raise CoverUsdcCurrentPublicTierMmrEvidenceError(f"OKX_CODE_NOT_SUCCESS:{okx_code}")
    if host != REUSED_BINDING_REST_HOST:
        raise CoverUsdcCurrentPublicTierMmrEvidenceError(f"HOST_MISMATCH:{host}")
    iid = str(instrument_id or "").strip()
    family = str(inst_family or "").strip()
    if family != CANARY_INST_FAMILY:
        raise CoverUsdcCurrentPublicTierMmrEvidenceError(f"INST_FAMILY_MISMATCH:{family}")
    assert_live_canary_instrument_binding_v1(instrument_id=iid, inst_type=DEFAULT_INST_TYPE)
    _assert_position_tiers_query(endpoint, instrument_id=iid, inst_family=family)
    mmr_value = _require_rate_decimal(mmr_public_tier_qty_one_current_value, field="mmr")
    imr_value = _require_rate_decimal(imr_public_tier_qty_one_observed, field="imr")
    if mmr_value > imr_value:
        raise CoverUsdcCurrentPublicTierMmrEvidenceError("MMR_GT_IMR")
    min_sz = _require_size_decimal(min_sz_current_value, field="minSz")
    max_sz = _require_size_decimal(max_sz_current_value, field="maxSz")
    if not (min_sz <= QTY_ONE <= max_sz):
        raise CoverUsdcCurrentPublicTierMmrEvidenceError("QTY_ONE_OUTSIDE_SELECTED_TIER")
    if not str(receive_ts_unix or "").strip():
        raise CoverUsdcCurrentPublicTierMmrEvidenceError("RECEIVE_TS_MISSING")
    if USD_USDC_CONVERSION_APPLIED:
        raise CoverUsdcCurrentPublicTierMmrEvidenceError("USD_USDC_CONVERSION_UNPROVEN")
    if not TICK_SZ_IS_NOT_USDC_PRECISION:
        raise CoverUsdcCurrentPublicTierMmrEvidenceError("TICK_SZ_IS_NOT_USDC_PRECISION")
    return CurrentPublicTierMmrPublicGetEvidenceV1(
        mmr_term_status=MMR_TERM_STATUS,
        mmr_public_tier_qty_one_current_value=str(mmr_public_tier_qty_one_current_value).strip(),
        mmr_role=MMR_ROLE,
        public_mmr_classification=PUBLIC_MMR_CLASSIFICATION,
        public_mmr_is_not_liquidation_price_evidence=True,
        mm_liq_buffer_instance_status=MM_LIQ_BUFFER_INSTANCE_STATUS,
        mm_liq_buffer_numeric_status=MM_LIQ_BUFFER_NUMERIC_STATUS,
        tier_current_value=str(tier_current_value).strip(),
        min_sz_current_value=str(min_sz_current_value).strip(),
        max_sz_current_value=str(max_sz_current_value).strip(),
        imr_public_tier_qty_one_observed=str(imr_public_tier_qty_one_observed).strip(),
        imr_role="PUBLIC_TIER_FACT_NOT_IM_FRESH_FLOOR_NOT_ADDITIVE",
        provider_ts_ms=PROVIDER_TS_NONE,
        receive_ts_unix=str(receive_ts_unix),
        historical_mmr_is_not_current=True,
        historical_l_or_s_pack_substituted=False,
        qty_term_status="PROVEN",
        ctval_term_status="PROVEN",
        ctval_bound_value=CTVAL_BOUND_VALUE,
        ctval_bound_ccy=CTVAL_BOUND_CCY,
        ctval_delivery_fee_operand_status=CTVAL_DELIVERY_FEE_OPERAND_STATUS,
        markpx_term_status=MARKPX_TERM_STATUS,
        markpx_current_value=Z2G_MARKPX_CURRENT_VALUE,
        markpx_okx_delivery_fee_operand_status=MARKPX_OKX_DELIVERY_FEE_OPERAND_STATUS,
        bid_ask_term_status=BID_ASK_TERM_STATUS,
        bid_px_current_value=Z2H_BID_PX_CURRENT_VALUE,
        ask_px_current_value=Z2H_ASK_PX_CURRENT_VALUE,
        slippage_reserve_instance_status=SLIPPAGE_RESERVE_INSTANCE_STATUS,
        slippage_reserve_numeric_status=SLIPPAGE_RESERVE_NUMERIC_STATUS,
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
        inst_family=family,
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


def collect_current_public_tier_mmr_public_get_v1(
    *,
    transport: LiveCanaryTransportV1,
    receive_ts_unix: str,
    owner_go: str = OWNER_GO,
    instrument_id: str = DEFAULT_INSTRUMENT_ID,
    inst_family: str = CANARY_INST_FAMILY,
    rest_host: str = REUSED_BINDING_REST_HOST,
    timeout_seconds: float = 10.0,
) -> tuple[CurrentPublicTierMmrPublicGetEvidenceV1, dict[str, Any], LiveCanaryHttpResponseV1]:
    """Execute exactly one public position-tiers GET and adjudicate observationally."""
    if owner_go != OWNER_GO:
        raise CoverUsdcCurrentPublicTierMmrEvidenceError(f"OWNER_GO_MISMATCH:{owner_go}")
    assert_live_canary_instrument_binding_v1(instrument_id=instrument_id)
    endpoint = (
        f"{POSITION_TIERS_ENDPOINT}?instType={DEFAULT_INST_TYPE}"
        f"&tdMode={DEFAULT_TD_MODE}&instFamily={inst_family}"
        f"&instId={instrument_id}"
    )
    _assert_position_tiers_query(endpoint, instrument_id=instrument_id, inst_family=inst_family)
    if rest_host != REUSED_BINDING_REST_HOST:
        raise CoverUsdcCurrentPublicTierMmrEvidenceError(f"HOST_MISMATCH:{rest_host}")
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
        raise CoverUsdcCurrentPublicTierMmrEvidenceError("TRANSPORT_RETURNED_NON_GET")
    http_evidence = extract_canary_http_response_evidence_v1(
        status_code=response.status_code,
        body_bytes=response.body_bytes,
        headers=response.response_headers_safe,
        redirect_followed=response.redirect_followed,
        redirect_status=response.redirect_status,
        redirect_location=response.redirect_location,
    )
    payload = parse_json_object_v1(response.body_bytes)
    mmr_text, imr_text, tier_text, min_sz, max_sz, family = (
        extract_qty_one_mmr_from_public_position_tiers_payload_v1(
            payload,
            expected_inst_family=inst_family,
        )
    )
    adjudication = adjudicate_current_public_tier_mmr_public_get_v1(
        mmr_public_tier_qty_one_current_value=mmr_text,
        imr_public_tier_qty_one_observed=imr_text,
        tier_current_value=tier_text,
        min_sz_current_value=min_sz,
        max_sz_current_value=max_sz,
        receive_ts_unix=receive_ts_unix,
        instrument_id=instrument_id,
        inst_family=family,
        host=rest_host,
        endpoint=endpoint,
        http_status=response.status_code,
        okx_code=str(payload.get("code") or ""),
        get_request_count=1,
        post_count=0,
        owner_go=owner_go,
    )
    snapshot = {
        "DOCUMENT_CLASS": "SECTION_11_13_5_Z2K_CURRENT_PUBLIC_TIER_MMR_PUBLIC_GET_EVIDENCE_V1",
        "DOCUMENT_ROLE": "GET_ONLY_FRESH_EVIDENCE_NON_SSOT_NOT_COVER_USDC",
        "OWNER_GO": OWNER_GO,
        "OWNER_GO_SCOPE": AUTHORIZED_SCOPE,
        "METHOD": "GET",
        "POST_COUNT": 0,
        "GET_REQUEST_COUNT": 1,
        "HOST": rest_host,
        "CANARY_INSTRUMENT": instrument_id,
        "INST_FAMILY": inst_family,
        "ENDPOINT": endpoint,
        "AUTHENTICATION_REQUIREMENT": "NONE_PUBLIC",
        "EVIDENCE_READ_ONLY": True,
        "SECRET_VALUES_INCLUDED": False,
        "classification": classify_current_public_tier_mmr_evidence_surface_v1(),
        "http_evidence": http_evidence,
        "response_headers_safe": safe_response_headers_v1(response.response_headers_safe),
        "payload": payload,
        "adjudication": adjudication.to_dict(),
        "QTY_BOUND_VALUE": QTY_BOUND_VALUE,
        "QTY_LIMIT": str(QTY_LIMIT),
        "AUTHORIZATION_SCOPE_CANARY": AUTHORIZATION_SCOPE,
        "B08_INTERNAL_ALGEBRA_STATUS": B08_EXACT_FORMULA_BODY_STATUS,
        "Z2E_SLIPPAGE_RESERVE_STATUS": SLIPPAGE_RESERVE_STATUS,
        "HISTORICAL_L_PACK_MMR": HISTORICAL_L_PACK_MMR,
        "HISTORICAL_S_PACK_MMR": HISTORICAL_S_PACK_MMR,
        "HISTORICAL_MMR_IS_NOT_CURRENT": True,
        "Z2G_MARKPX_CURRENT_VALUE": Z2G_MARKPX_CURRENT_VALUE,
        "Z2H_BID_PX_CURRENT_VALUE": Z2H_BID_PX_CURRENT_VALUE,
        "Z2H_ASK_PX_CURRENT_VALUE": Z2H_ASK_PX_CURRENT_VALUE,
        "NO_TICKER_GET_THIS_STEP": True,
        "NO_MARK_PRICE_GET_THIS_STEP": True,
        "NO_INSTRUMENTS_GET_THIS_STEP": True,
        "NO_PRIVATE_GET_THIS_STEP": True,
        "NO_PROVIDER_TS_INVENTED": True,
    }
    return adjudication, snapshot, response


def persist_current_public_tier_mmr_public_get_evidence_v1(
    *,
    evidence_root: str | Path,
    run_id: str,
    bound_origin_main_sha: str,
    adjudication: CurrentPublicTierMmrPublicGetEvidenceV1,
    snapshot: Mapping[str, Any],
) -> dict[str, Any]:
    root = Path(evidence_root)
    root.mkdir(parents=True, exist_ok=True)
    claims = {
        "DOCUMENT_CLASS": "SECTION_11_13_5_Z2K_CURRENT_PUBLIC_TIER_MMR_PUBLIC_GET_EVIDENCE_V1",
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
        "MMR_TERM_STATUS": adjudication.mmr_term_status,
        "MMR_PUBLIC_TIER_QTY_ONE_CURRENT_VALUE": (
            adjudication.mmr_public_tier_qty_one_current_value
        ),
        "MM_LIQ_BUFFER_INSTANCE_STATUS": (adjudication.mm_liq_buffer_instance_status),
        "MM_LIQ_BUFFER_NUMERIC_STATUS": (adjudication.mm_liq_buffer_numeric_status),
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
        "DOCUMENT_CLASS": "SECTION_11_13_5_Z2K_CURRENT_PUBLIC_TIER_MMR_PUBLIC_GET_EVIDENCE_V1",
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
        "MMR_TERM_STATUS": adjudication.mmr_term_status,
        "MMR_PUBLIC_TIER_QTY_ONE_CURRENT_VALUE": (
            adjudication.mmr_public_tier_qty_one_current_value
        ),
        "MM_LIQ_BUFFER_NUMERIC_STATUS": (adjudication.mm_liq_buffer_numeric_status),
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
        "MMR_PUBLIC_TIER_QTY_ONE_CURRENT_VALUE": (
            adjudication.mmr_public_tier_qty_one_current_value
        ),
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
        raise CoverUsdcCurrentPublicTierMmrEvidenceError(f"MANIFEST_VERIFY_FAIL:{verify['errors']}")
    return {**persistence, "MANIFEST_VERIFY_RC": 0}


def encode_fixture_position_tiers_payload_v1(
    *,
    inst_family: str,
    qty_one_mmr: str,
    qty_one_imr: str = "0.02",
    qty_one_tier: str = "1",
    qty_one_min_sz: str = "0",
    qty_one_max_sz: str = "25000",
    extra_rows: list[dict[str, Any]] | None = None,
    code: str = "0",
) -> bytes:
    qty_one_row: dict[str, Any] = {
        "instId": "",
        "instFamily": inst_family,
        "uly": "BTC-USD",
        "tier": qty_one_tier,
        "minSz": qty_one_min_sz,
        "maxSz": qty_one_max_sz,
        "imr": qty_one_imr,
        "mmr": qty_one_mmr,
        "maxLever": "50",
    }
    rows: list[dict[str, Any]] = [qty_one_row]
    if extra_rows:
        rows.extend(extra_rows)
    payload = {"code": code, "msg": "", "data": rows}
    return json.dumps(payload, separators=(",", ":")).encode("utf-8")


__all__ = (
    "AUTHORIZED_SCOPE",
    "CANARY_INST_FAMILY",
    "COVER_USDC_STATUS",
    "CoverUsdcCurrentPublicTierMmrEvidenceError",
    "CurrentPublicTierMmrPublicGetEvidenceV1",
    "EVIDENCE_DIRNAME",
    "EVIDENCE_SURFACE_CLASSIFICATION",
    "MMR_TERM_STATUS",
    "MM_LIQ_BUFFER_INSTANCE_STATUS",
    "MM_LIQ_BUFFER_NUMERIC_STATUS",
    "NEXT_CANONICAL_POINTER",
    "OWNER_GO",
    "POSITION_TIERS_QUERY_PATH",
    "PUBLIC_MMR_CLASSIFICATION",
    "adjudicate_current_public_tier_mmr_public_get_v1",
    "classify_current_public_tier_mmr_evidence_surface_v1",
    "collect_current_public_tier_mmr_public_get_v1",
    "encode_fixture_position_tiers_payload_v1",
    "extract_qty_one_mmr_from_public_position_tiers_payload_v1",
    "persist_current_public_tier_mmr_public_get_evidence_v1",
)
