"""§11.13.5 Branch-B documentary discriminator (acctLv=2).

Fail-closed, non-executing. Encodes official OKX V5 contract facts plus
already-captured live EEA ``GET /api/v5/account/config`` evidence.

Does not place orders, call OKX, unlock submit, or prove Rule C.

Official V5 (global): POST /api/v5/trade/order-precheck is documented as
applicable only to Multi-currency margin and Portfolio margin. EEA regional
V5 docs do not list this endpoint. This module never executes it.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Mapping

ENDPOINT_ORDER_PRECHECK = "/api/v5/trade/order-precheck"
ENDPOINT_ORDER_SUBMIT = "/api/v5/trade/order"
EEA_REST_HOST = "eea.okx.com"

PRECHECK_DEFAULT_ENABLED = False
PRECHECK_EXECUTION_AUTHORIZED = False
PRECHECK_CANNOT_CREATE_ORDER = True

ACCT_LV_SPOT = "1"
ACCT_LV_FUTURES = "2"
ACCT_LV_MULTI_CURRENCY = "3"
ACCT_LV_PORTFOLIO = "4"
DOCUMENTED_PRECHECK_APPLICABLE_ACCT_LV: frozenset[str] = frozenset(
    {ACCT_LV_MULTI_CURRENCY, ACCT_LV_PORTFOLIO}
)

LIVE_EEA_ACCT_LV_EVIDENCE_VALUE = "2"
LIVE_EEA_ACCT_LV_EVIDENCE_PATH = (
    "evidence/ops/section_11_13_5_post_k_cross_imr_leverage_get_bind_v1/"
    "20260816T033800Z/GET_SNAPSHOT.sanitized.json"
)
LIVE_EEA_ACCT_LV_EVIDENCE_UID = "856964404452495999"
LIVE_EEA_ACCT_LV_EVIDENCE_CLASS = "PROVEN_EXISTING_LIVE_EEA_GET_ACCOUNT_CONFIG"
LIVE_EEA_ACCT_LV_ENVIRONMENT = "LIVE_EEA"

ORDER_FIELD_NOTIONAL_USD = "notionalUsd"
LINEAR_NOTIONAL_ALGEBRA = "sz * ctVal * markPx"
DISCRIMINATION_CLASS = "THEORETICAL_DOCUMENTARY_ONLY"
NOT_OKX_RUNTIME_PROOF = True
RULE_C_STATUS = "UNPROVEN"
FACE_VALUE_CONFLICT_STATUS = "UNRESOLVED"
COVER_USDC_STATUS = "UNINSTANTIATED"

CANDIDATE_A_CT_VAL = Decimal("0.0001")
CANDIDATE_B_CT_VAL = Decimal("0.01")
DOCUMENTARY_SZ = Decimal("1")
EXPECTED_DISCRIMINATION_FACTOR = Decimal("100")

# Official OKX V5 request names for POST /api/v5/trade/order-precheck.
PRECHECK_REQUEST_FIELDS: tuple[str, ...] = (
    "instId",
    "tdMode",
    "side",
    "ordType",
    "sz",
    "px",
)
# Official OKX V5 response names from POST /api/v5/trade/order-precheck.
PRECHECK_RESPONSE_FIELDS: tuple[str, ...] = (
    "imr",
    "imrChg",
    "mmr",
    "mmrChg",
    "adjEq",
    "adjEqChg",
    "mgnRatio",
    "mgnRatioChg",
    "liqPxDiff",
)

SELECTED_PATH = "UNFILLED_ORDER_DOCUMENTARY_DISCRIMINATOR"


class OrderPrecheckExecutionForbiddenError(RuntimeError):
    """Raised when any execution of order-precheck is attempted."""


class UnsupportedAcctLvFailClosedError(RuntimeError):
    """Raised for missing/unknown account mode (fail-closed)."""


def normalize_acct_lv(acct_lv: object) -> str:
    if acct_lv is None:
        raise UnsupportedAcctLvFailClosedError("ACCT_LV_UNKNOWN")
    text = str(acct_lv).strip()
    if text not in {
        ACCT_LV_SPOT,
        ACCT_LV_FUTURES,
        ACCT_LV_MULTI_CURRENCY,
        ACCT_LV_PORTFOLIO,
    }:
        raise UnsupportedAcctLvFailClosedError(f"ACCT_LV_UNSUPPORTED:{text or '<empty>'}")
    return text


def supports_order_precheck(acct_lv: object) -> bool:
    """Official V5: precheck only for Multi-currency (3) and Portfolio (4)."""
    return normalize_acct_lv(acct_lv) in DOCUMENTED_PRECHECK_APPLICABLE_ACCT_LV


def order_precheck_documented_applicable(acct_lv: object) -> bool:
    return supports_order_precheck(acct_lv)


def order_precheck_execution_allowed(acct_lv: object | None = None) -> bool:
    del acct_lv
    return False


def refuse_order_precheck_execution_v1() -> None:
    raise OrderPrecheckExecutionForbiddenError(
        "ORDER_PRECHECK_EXECUTION_FORBIDDEN:"
        f"PRECHECK_EXECUTION_AUTHORIZED={PRECHECK_EXECUTION_AUTHORIZED}"
    )


def theoretical_linear_notional_usd(
    *,
    sz: Decimal | str,
    ct_val: Decimal | str,
    mark_px: Decimal | str,
) -> Decimal:
    """Documentary linear notional: sz × ctVal × markPx. Not OKX runtime proof."""
    return Decimal(str(sz)) * Decimal(str(ct_val)) * Decimal(str(mark_px))


def theoretical_candidate_notional_ratio(
    *,
    mark_px: Decimal | str,
    sz: Decimal | str = DOCUMENTARY_SZ,
) -> Decimal:
    notional_a = theoretical_linear_notional_usd(sz=sz, ct_val=CANDIDATE_A_CT_VAL, mark_px=mark_px)
    notional_b = theoretical_linear_notional_usd(sz=sz, ct_val=CANDIDATE_B_CT_VAL, mark_px=mark_px)
    if notional_a == 0:
        raise ZeroDivisionError("CANDIDATE_A_NOTIONAL_ZERO")
    return notional_b / notional_a


def unfilled_order_documentary_binding_v1() -> dict[str, object]:
    return {
        "SELECTED_PATH": SELECTED_PATH,
        "ORDER_OBJECT_FIELD": ORDER_FIELD_NOTIONAL_USD,
        "ORDER_FIELD_SEMANTICS": "ESTIMATED_NOTIONAL_VALUE_IN_USD_OF_ORDER",
        "LINEAR_NOTIONAL_ALGEBRA": LINEAR_NOTIONAL_ALGEBRA,
        "DISCRIMINATION_CLASS": DISCRIMINATION_CLASS,
        "NOT_OKX_RUNTIME_PROOF": NOT_OKX_RUNTIME_PROOF,
        "RULE_C_STATUS": RULE_C_STATUS,
        "FACE_VALUE_CONFLICT_STATUS": FACE_VALUE_CONFLICT_STATUS,
        "COVER_USDC_STATUS": COVER_USDC_STATUS,
        "SUBMIT_UNLOCKED": False,
        "LIVE_ARMED": False,
        "PRECHECK_DEFAULT_ENABLED": PRECHECK_DEFAULT_ENABLED,
        "PRECHECK_EXECUTION_AUTHORIZED": PRECHECK_EXECUTION_AUTHORIZED,
        "PRECHECK_CANNOT_CREATE_ORDER": PRECHECK_CANNOT_CREATE_ORDER,
        "ENDPOINT_ORDER_PRECHECK": ENDPOINT_ORDER_PRECHECK,
        "ENDPOINT_ORDER_SUBMIT": ENDPOINT_ORDER_SUBMIT,
        "ENDPOINTS_ISOLATED": ENDPOINT_ORDER_PRECHECK != ENDPOINT_ORDER_SUBMIT,
        "LIVE_EEA_ACCT_LV": LIVE_EEA_ACCT_LV_EVIDENCE_VALUE,
        "LIVE_EEA_ACCT_LV_EVIDENCE_CLASS": LIVE_EEA_ACCT_LV_EVIDENCE_CLASS,
        "LIVE_EEA_ACCT_LV_ENVIRONMENT": LIVE_EEA_ACCT_LV_ENVIRONMENT,
        "LIVE_EEA_ACCT_LV_EVIDENCE_PATH": LIVE_EEA_ACCT_LV_EVIDENCE_PATH,
        "ORDER_PRECHECK_APPLICABLE_FOR_LIVE_EEA_ACCT_LV_2": False,
        "CANDIDATE_A_CT_VAL": str(CANDIDATE_A_CT_VAL),
        "CANDIDATE_B_CT_VAL": str(CANDIDATE_B_CT_VAL),
        "EXPECTED_DISCRIMINATION_FACTOR": str(EXPECTED_DISCRIMINATION_FACTOR),
    }


def assert_no_submit_unlock_in_binding(binding: Mapping[str, object]) -> None:
    if binding.get("SUBMIT_UNLOCKED") is not False:
        raise RuntimeError("SUBMIT_UNLOCK_FORBIDDEN_IN_DOCUMENTARY_BINDING")
    if binding.get("PRECHECK_EXECUTION_AUTHORIZED") is not False:
        raise RuntimeError("PRECHECK_EXECUTION_FORBIDDEN_IN_DOCUMENTARY_BINDING")
    if binding.get("LIVE_ARMED") is not False:
        raise RuntimeError("LIVE_ARM_FORBIDDEN_IN_DOCUMENTARY_BINDING")
