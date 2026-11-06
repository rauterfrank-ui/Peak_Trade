"""GET-only economic-baseline contract for the current live EEA XPerp identity.

Preparation only. Does not execute network, funding, or orders.
Must not inherit BTC-USDT-SWAP or Demo BTC-USD_UM_XPERP-310328.
Historical BTC-USD_UM_XPERP-310404 snapshots remain isolated and are
not current SUI venue observations.
"""

from __future__ import annotations

from typing import Any

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    CANARY_INSTRUMENT,
    CANARY_INST_TYPE,
    DEFAULT_INST_FAMILY,
    DEFAULT_INSTRUMENT_ID,
    DEFAULT_INST_TYPE,
    DEFAULT_RULE_TYPE,
    DEFAULT_TD_MODE,
    DEMO_XPERP_INSTRUMENT_ID,
    HISTORICAL_REJECTED_SWAP_INSTRUMENT_ID,
    HISTORICAL_SUPERSEDED_CANONICAL_INSTRUMENT_ID,
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
        "tickSz": "0.0001",
        "ctVal": "1",
        "ctValCcy": "SUI",
        "ctMult": "1",
        "instFamily": DEFAULT_INST_FAMILY,
        "ctType": "linear",
        "expTime": "1933056000000",
        "ONE_CONTRACT_EQUALS_ONE_SUI": False,
        "EXCHANGE_POSITION_VALUE_STATUS": "UNPROVEN",
        "minimum_exposure_quantity": "1",
        "notional_formula": "qty * ctVal * markPx",
        "mark_last_price_source": (
            f"GET /api/v5/public/mark-price?instType=FUTURES&instId={DEFAULT_INSTRUMENT_ID}"
        ),
        "public_instruments_query": (
            f"/api/v5/public/instruments?instType=FUTURES&instId={DEFAULT_INSTRUMENT_ID}"
        ),
        "required_margin_equity_estimate_status": "UNPROVEN_TOTAL_EQ_ZERO_AT_POST_K_GET_BIND",
        "snapshot_theoretical_initial_margin_status": "HISTORICAL_BTC_SNAPSHOT_FLOOR_ONLY_NOT_CURRENT_SUI",
        "HISTORICAL_BTC_SNAPSHOT_ISOLATED": True,
        "HISTORICAL_BTC_SNAPSHOT_INSTRUMENT": HISTORICAL_SUPERSEDED_CANONICAL_INSTRUMENT_ID,
        "snapshot_mark_px": "63043.7",
        "snapshot_ct_val": "0.0001",
        "snapshot_qty": "1",
        "set_account_leverage": "3",
        "set_account_leverage_mgn_mode": "cross",
        "set_account_leverage_pos_side": "net",
        "snapshot_minimum_notional_estimate": "6.30437",
        "snapshot_theoretical_initial_margin_usdc": "2.101456666666666666666666667",
        "minimum_theoretical_initial_margin_proven": False,
        "HISTORICAL_BTC_MINIMUM_THEORETICAL_INITIAL_MARGIN_PROVEN": True,
        "snapshot_theoretical_funding_floor_proven": False,
        "HISTORICAL_BTC_SNAPSHOT_THEORETICAL_FUNDING_FLOOR_PROVEN": True,
        "canary_operational_minimum_proven": False,
        "recommended_bounded_canary_funding_amount_proven": False,
        "funding_amount_proven": False,
        "posMode_compatibility": "net_mode_proven",
        "tdMode_compatibility": "cross_get_proven_leverage_setting_no_live_post",
        "tdMode_live_post_proven": False,
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
