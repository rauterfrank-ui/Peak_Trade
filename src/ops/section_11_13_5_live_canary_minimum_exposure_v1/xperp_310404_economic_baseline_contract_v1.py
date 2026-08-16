"""GET-only economic-baseline contract for live EEA XPerp 310404.

Preparation only. Does not execute network, funding, or orders.
Must not inherit BTC-USDT-SWAP or Demo BTC-USD_UM_XPERP-310328.
"""

from __future__ import annotations

from typing import Any

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    CANARY_INSTRUMENT,
    CANARY_INST_TYPE,
    DEFAULT_INSTRUMENT_ID,
    DEFAULT_INST_TYPE,
    DEFAULT_RULE_TYPE,
    DEFAULT_TD_MODE,
    DEMO_XPERP_INSTRUMENT_ID,
    HISTORICAL_REJECTED_SWAP_INSTRUMENT_ID,
    LIVE_AUTHORIZED,
    PRODUCT_RULE_TYPE,
    SETTLEMENT_ACCOUNT_TRUTH,
)


def live_eea_xperp_310404_economic_baseline_contract_v1() -> dict[str, Any]:
    """Static GET-only baseline definition. Productive refresh required before execute."""
    return {
        "DOCUMENT_CLASS": "SECTION_11_13_5_EEA_XPERP_310404_ECONOMIC_BASELINE_CONTRACT_V1",
        "DOCUMENT_ROLE": "PREPARATION_ONLY_NON_ACTIVATING",
        "INHERITED_FROM_BTC_USDT_SWAP": False,
        "INHERITED_FROM_DEMO_310328": False,
        "CANARY_INSTRUMENT": CANARY_INSTRUMENT,
        "CANARY_INST_TYPE": CANARY_INST_TYPE,
        "PRODUCT_RULE_TYPE": PRODUCT_RULE_TYPE,
        "SETTLEMENT_ACCOUNT_TRUTH": SETTLEMENT_ACCOUNT_TRUTH,
        "PUBLIC_API_SETTLE_CCY_NOTE": "USD_PUBLIC_VS_USDC_ACCOUNT_TRUTH",
        "instrument_identity": DEFAULT_INSTRUMENT_ID,
        "inst_type": DEFAULT_INST_TYPE,
        "rule_type": DEFAULT_RULE_TYPE,
        "state": "live",
        "account_instruments_visibility": True,
        "ui_visible": True,
        "minSz": "1",
        "lotSz": "1",
        "tickSz": "0.1",
        "ctVal": "0.0001",
        "ctValCcy": "BTC",
        "minimum_exposure_quantity": "1",
        "notional_formula": "qty * ctVal * last",
        "mark_last_price_source": "GET /api/v5/market/ticker?instId=BTC-USD_UM_XPERP-310404",
        "public_instruments_query": (
            "/api/v5/public/instruments?instType=FUTURES&instId=BTC-USD_UM_XPERP-310404"
        ),
        "required_margin_equity_estimate_status": "UNPROVEN_TOTAL_EQ_ZERO_AT_BINDING_PASS",
        "posMode_compatibility": "net_mode_proven",
        "tdMode_compatibility": "cross_unproven_for_live_xperp_post",
        "td_mode_default": DEFAULT_TD_MODE,
        "no_open_orders_precondition": True,
        "no_open_position_precondition": True,
        "rejected_swap_instrument": HISTORICAL_REJECTED_SWAP_INSTRUMENT_ID,
        "rejected_demo_instrument": DEMO_XPERP_INSTRUMENT_ID,
        "productive_get_refresh_required_before_execute": True,
        "funding_required_before_execute": True,
        "LIVE_AUTHORIZED": LIVE_AUTHORIZED,
        "EXECUTED": False,
        "ORDER_EFFECT": "NONE",
    }
