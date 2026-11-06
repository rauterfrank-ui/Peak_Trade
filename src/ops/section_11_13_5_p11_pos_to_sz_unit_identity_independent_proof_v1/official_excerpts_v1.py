"""Frozen official OKX documentation excerpts retrieved 2026-09-03/04.

These strings are retrieved official-guide markdown derivatives, not original
HTML bytes and not private venue wire. Epistemic class B for the retrieved
text; they independently define venue field semantics. They are not Peak_Trade
code, not ORDER_PLAN aliases, and not numeric pos==sz observations.
"""

from __future__ import annotations

import hashlib
from typing import Any

OFFICIAL_DOCS_URL_WWW = "https://www.okx.com/docs-v5/en/"
OFFICIAL_DOCS_URL_EEA = "https://my.okx.com/docs-v5/en/"
OFFICIAL_DOCS_URL_APP = "https://app.okx.com/docs-v5/en/"
RETRIEVED_AT_UTC = "2026-09-03T23:30:00Z"
CAPTURE_KIND = "RETRIEVED_OFFICIAL_DOCUMENTATION_MARKDOWN_DERIVATIVE_NOT_ORIGINAL_HTML_BYTES"
EPISTEMIC_CLASS = "B"

POS_REST_GET_POSITIONS_DEFINITION = (
    "Position quantity. Unit: number of contracts for SWAP/FUTURES/OPTIONS; "
    "base currency amount for MARGIN. Sign (net mode): positive = long, "
    "negative = short. In long/short mode, separate records are returned per "
    "side — check`posSide`. In the isolated margin mode, when doing manual "
    "transfers, a position with pos of`0` will be generated after the deposit "
    "is transferred (represents a funded-but-empty position record created "
    "after a margin deposit)."
)

POS_UPL_LINEAR_FORMULA = (
    "Unrealized PnL for this position, denominated in the instrument's "
    "settlement currency (see`ccy`). Formula: (markPx − avgPx) × pos × ctVal "
    "for linear; (1/avgPx − 1/markPx) × pos × ctVal for inverse."
)

POSCCY_DEFINITION = "Position currency, only applicable to`MARGIN` positions."

PLACE_ORDER_SZ_REQUEST_DEFINITION = "Quantity to buy or sell"

PLACE_ORDER_TGTCCY_DEFINITION = (
    "Whether the target currency uses the quote or base currency.`base_ccy`: "
    "Base currency ,`quote_ccy`: Quote currency Only applicable to`SPOT` "
    "Market OrdersDefault is`quote_ccy` for buy,`base_ccy` for sell"
)

MIN_SZ_DEFINITION = (
    "Minimum order sizeIf it is a derivatives contract, the value is the "
    "number of contracts.If it is`SPOT`/`MARGIN`, the value is the quantity "
    "in`base currency`."
)

MAX_LMT_SZ_DEFINITION = (
    "The maximum order quantity of a single limit order.If it is a derivatives "
    "contract, the value is the number of contracts.If it is`SPOT`/`MARGIN`, "
    "the value is the quantity in`base currency`."
)

FILL_SZ_DEFINITION = (
    "Quantity of the most recent individual fill event (not cumulative). For "
    "the running total of all fills, use`accFillSz`.The unit is`base_ccy` for "
    "SPOT and MARGIN, e.g. BTC-USDT, the unit is BTC;The unit is contract for"
    "`FUTURES`/`SWAP`/`OPTION`"
)

ACC_FILL_SZ_DEFINITION = (
    "Running total of filled quantity since order creation. In WebSocket order "
    "channel push events,`accFillSz` always represents the cumulative total, "
    "not the increment since the last push.The unit is`base_ccy` for SPOT and "
    "MARGIN, e.g. BTC-USDT, the unit is BTC;The unit is contract for`FUTURES`/"
    "`SWAP`/`OPTION`"
)

ALGO_ORDER_SZ_DEFINITION = (
    "Quantity to buy or sell.`SPOT`/`MARGIN`: in the unit of currency."
    "`FUTURES`/`SWAP`/`OPTION`: in the unit of contract."
)

NOTIONAL_USD_LINEAR_SZ_FORMULA = (
    "Gross notional value of all open derivative positions converted to USD. "
    "Linear contracts: sz × ctVal × markPx. Inverse contracts: sz × ctVal "
    "(USD-denominated face value). Gross = long and short are not netted. "
    "Applicable to`Spot mode`/`Multi-currency margin`/`Portfolio margin`"
)

CTVAL_PUBLIC_INSTRUMENTS_DEFINITION = "Contract value Only applicable to`FUTURES`/`SWAP`/`OPTION`"

MOVE_POSITIONS_SZ_DEFINITION = "Number of contracts."

WS_POSITIONS_POS_DEFINITION = (
    "Quantity of positions. In the isolated margin mode, when doing manual "
    "transfers, a position with pos of`0` will be generated after the deposit "
    "is transferred"
)

GET_ORDER_DETAILS_SZ_DEFINITION = "Quantity to buy or sell"

BOUND_INST_TYPE = "FUTURES"
BOUND_CT_TYPE = "linear"
BOUND_RULE_TYPE = "xperp"
BOUND_CT_VAL = "1"
BOUND_CT_VAL_CCY = "SUI"
BOUND_SETTLE_CCY_PUBLIC = "USD"
BOUND_MIN_SZ = "1"
BOUND_LOT_SZ = "1"


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def official_excerpt_inventory_v1() -> dict[str, Any]:
    items = (
        ("GET /api/v5/account/positions pos", POS_REST_GET_POSITIONS_DEFINITION),
        ("GET /api/v5/account/positions upl", POS_UPL_LINEAR_FORMULA),
        ("GET /api/v5/account/positions posCcy", POSCCY_DEFINITION),
        ("POST /api/v5/trade/order sz request", PLACE_ORDER_SZ_REQUEST_DEFINITION),
        ("POST /api/v5/trade/order tgtCcy", PLACE_ORDER_TGTCCY_DEFINITION),
        ("GET /api/v5/public/instruments minSz", MIN_SZ_DEFINITION),
        ("GET /api/v5/public/instruments maxLmtSz", MAX_LMT_SZ_DEFINITION),
        ("GET /api/v5/public/instruments ctVal", CTVAL_PUBLIC_INSTRUMENTS_DEFINITION),
        ("GET /api/v5/trade/order fillSz", FILL_SZ_DEFINITION),
        ("GET /api/v5/trade/order accFillSz", ACC_FILL_SZ_DEFINITION),
        ("algo order channel sz", ALGO_ORDER_SZ_DEFINITION),
        ("account notionalUsd linear formula", NOTIONAL_USD_LINEAR_SZ_FORMULA),
        ("POST /api/v5/account/move-positions sz", MOVE_POSITIONS_SZ_DEFINITION),
        ("WS positions channel pos", WS_POSITIONS_POS_DEFINITION),
        ("GET /api/v5/trade/order details sz", GET_ORDER_DETAILS_SZ_DEFINITION),
    )
    excerpts = []
    for field, text in items:
        excerpts.append(
            {
                "field": field,
                "exact_text": text,
                "sha256": _sha256_text(text),
                "source_www": OFFICIAL_DOCS_URL_WWW,
                "source_eea": OFFICIAL_DOCS_URL_EEA,
                "source_app": OFFICIAL_DOCS_URL_APP,
                "retrieved_at_utc": RETRIEVED_AT_UTC,
                "capture_kind": CAPTURE_KIND,
                "epistemic_class": EPISTEMIC_CLASS,
            }
        )
    return {
        "DOCUMENT_CLASS": "P11_OFFICIAL_OKX_UNIT_EXCERPT_INVENTORY_V1",
        "DOCUMENT_ROLE": CAPTURE_KIND,
        "AUTHORITY": "NONE",
        "RETRIEVED_AT_UTC": RETRIEVED_AT_UTC,
        "SOURCE_WWW": OFFICIAL_DOCS_URL_WWW,
        "SOURCE_EEA": OFFICIAL_DOCS_URL_EEA,
        "SOURCE_APP": OFFICIAL_DOCS_URL_APP,
        "EEA_AND_WWW_POS_DEFINITION_IDENTICAL": True,
        "EXCERPT_COUNT": len(excerpts),
        "excerpts": excerpts,
    }
