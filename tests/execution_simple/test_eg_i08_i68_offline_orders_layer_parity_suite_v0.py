# tests/execution_simple/test_eg_i08_i68_offline_orders_layer_parity_suite_v0.py
"""
Offline Orders-Layer Parity Suite V0 — I08 vs I68 Paper (EG-I08-I68).

Evidence-only harness. Does NOT claim SUPERSEDED_PROVEN.
Does NOT mutate production logic. No network / credentials / live / testnet.

Suite ID: EG_I08_I68_OFFLINE_ORDERS_LAYER_PARITY_SUITE_V0
"""

from __future__ import annotations

import ast
import importlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

import pytest

from src.execution_simple.adapters.simulated import SimulatedBrokerAdapter
from src.execution_simple.gates import PriceSanityGate
from src.execution_simple.pipeline import ExecutionPipeline
from src.execution_simple.types import ExecutionContext, ExecutionMode, OrderSide
from src.orders.base import OrderRequest
from src.orders.paper import PaperMarketContext, PaperOrderExecutor

SUITE_ID = "EG_I08_I68_OFFLINE_ORDERS_LAYER_PARITY_SUITE_V0"
REPO_ROOT = Path(__file__).resolve().parents[2]
FIXED_TS = datetime(2026, 8, 12, 19, 0, 0, tzinfo=timezone.utc)
MID = 100.0
QTY = 1.0
SLIPPAGE_BPS = 2.0
FEE_BPS = 10.0
SYMBOL = "BTC-USD"

CAPABILITY_ORDER: List[str] = [
    "order_intent_input_normalization",
    "order_request_model",
    "side_semantics",
    "order_type_semantics",
    "quantity_semantics",
    "price_semantics_market_fill",
    "client_order_identifiers",
    "submit_result_ack_mapping",
    "reject_error_mapping",
    "cancel_intent_result",
    "status_state_mapping",
    "partial_fill_representation",
    "terminal_state_handling",
    "idempotency_retry_semantics",
    "fee_representation",
    "mg_i08_type_coupling_risk_layer",
]


@dataclass(frozen=True)
class ParityObservation:
    capability: str
    classification: str
    notes: str = ""


def _i08_pipeline() -> ExecutionPipeline:
    return ExecutionPipeline(
        gates=[PriceSanityGate()],
        adapter=SimulatedBrokerAdapter(slippage_bps=SLIPPAGE_BPS, fee_bps=FEE_BPS),
    )


def _i08_context(*, price: float = MID) -> ExecutionContext:
    return ExecutionContext(
        mode=ExecutionMode.PAPER,
        ts=FIXED_TS,
        symbol=SYMBOL,
        price=price,
        tags=set(),
    )


def _i68_executor(*, prices: Dict[str, float] | None = None) -> PaperOrderExecutor:
    ctx = PaperMarketContext(
        prices=prices if prices is not None else {SYMBOL: MID},
        fee_bps=FEE_BPS,
        slippage_bps=SLIPPAGE_BPS,
        base_currency="USD",
    )
    return PaperOrderExecutor(ctx)


def _expected_market_fill_price(side: str) -> float:
    slip = SLIPPAGE_BPS / 10000.0
    if side == "buy":
        return MID * (1.0 + slip)
    return MID * (1.0 - slip)


def _count(observations: Dict[str, ParityObservation]) -> Dict[str, int]:
    counts = {
        "SAME": 0,
        "SEMANTICALLY_EQUIVALENT": 0,
        "PARTIAL_OVERLAP": 0,
        "BEHAVIORAL_DIFFERENCE": 0,
        "TYPE_OR_CONTRACT_DIFFERENCE": 0,
        "NOT_EXERCISED": 0,
    }
    for cap in CAPABILITY_ORDER:
        cls = observations[cap].classification
        assert cls in counts, cls
        counts[cls] += 1
    return counts


@pytest.fixture(autouse=True)
def _offline_only(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in (
        "OKX_API_KEY",
        "OKX_SECRET_KEY",
        "OKX_PASSPHRASE",
        "EXCHANGE_API_KEY",
        "LIVE_TRADING",
        "TESTNET_AUTHORIZED",
    ):
        monkeypatch.delenv(key, raising=False)


def test_eg_i08_i68_offline_orders_layer_parity_suite_v0() -> None:
    """Single deterministic offline suite run — evidence only; no SUPERSEDED claim."""
    observations: Dict[str, ParityObservation] = {}

    def record(capability: str, classification: str, notes: str = "") -> None:
        observations[capability] = ParityObservation(capability, classification, notes)

    # --- Market buy ---
    i08_buy = _i08_pipeline().execute(
        target_position=QTY,
        current_position=0.0,
        context=_i08_context(),
    )
    assert not i08_buy.blocked
    assert len(i08_buy.orders) == 1 and len(i08_buy.fills) == 1
    i68_buy = _i68_executor().execute_order(
        OrderRequest(symbol=SYMBOL, side="buy", quantity=QTY, order_type="market")
    )
    assert i68_buy.status == "filled" and i68_buy.fill is not None
    expected_buy = _expected_market_fill_price("buy")
    assert i08_buy.fills[0].price == pytest.approx(expected_buy)
    assert i68_buy.fill.price == pytest.approx(expected_buy)
    assert i08_buy.orders[0].side == OrderSide.BUY
    assert i68_buy.request.side == "buy"
    assert i08_buy.orders[0].quantity == QTY == i68_buy.fill.quantity
    assert i08_buy.orders[0].symbol == SYMBOL == i68_buy.fill.symbol

    # --- Market sell ---
    i08_sell = _i08_pipeline().execute(
        target_position=0.0,
        current_position=QTY,
        context=_i08_context(),
    )
    assert not i08_sell.blocked and len(i08_sell.fills) == 1
    i68_sell = _i68_executor().execute_order(
        OrderRequest(symbol=SYMBOL, side="sell", quantity=QTY, order_type="market")
    )
    assert i68_sell.status == "filled" and i68_sell.fill is not None
    expected_sell = _expected_market_fill_price("sell")
    assert i08_sell.fills[0].price == pytest.approx(expected_sell)
    assert i68_sell.fill.price == pytest.approx(expected_sell)
    assert i08_sell.orders[0].side == OrderSide.SELL
    assert i68_sell.request.side == "sell"

    # --- Fee numeric parity ---
    expected_fee = abs(QTY * expected_buy * (FEE_BPS / 10000.0))
    assert i08_buy.fills[0].fee == pytest.approx(expected_fee)
    assert i68_buy.fill.fee == pytest.approx(expected_fee)

    # --- Reject path behavioral difference ---
    i08_block = _i08_pipeline().execute(
        target_position=QTY,
        current_position=0.0,
        context=_i08_context(price=0.0),
    )
    assert i08_block.blocked and len(i08_block.fills) == 0
    i68_reject = _i68_executor(prices={}).execute_order(
        OrderRequest(symbol=SYMBOL, side="buy", quantity=QTY, order_type="market")
    )
    assert i68_reject.status == "rejected"
    assert i68_reject.reason is not None and "no_price_for_symbol" in i68_reject.reason

    # --- I68 limit exists; I08 pipeline always MARKET ---
    i68_limit = _i68_executor().execute_order(
        OrderRequest(
            symbol=SYMBOL,
            side="buy",
            quantity=QTY,
            order_type="limit",
            limit_price=MID,
        )
    )
    assert i68_limit.status == "filled"

    # --- MG-I08 type coupling (independent responsibility) ---
    adapters_path = REPO_ROOT / "src/risk_layer/adapters.py"
    risk_gate_path = REPO_ROOT / "src/risk_layer/risk_gate.py"
    adapters_src = adapters_path.read_text(encoding="utf-8")
    risk_gate_src = risk_gate_path.read_text(encoding="utf-8")
    assert "from src.execution_simple.types import" in adapters_src
    assert "from src.execution_simple.types import Order" in risk_gate_src
    risk_adapters = importlib.import_module("src.risk_layer.adapters")
    assert risk_adapters.Order.__module__ == "src.execution_simple.types"
    tree = ast.parse(adapters_src)
    imports = [
        n
        for n in ast.walk(tree)
        if isinstance(n, ast.ImportFrom) and (n.module or "").startswith("src.execution_simple")
    ]
    assert imports

    # --- Classification ledger (common-surface evidence) ---
    record(
        "order_intent_input_normalization",
        "TYPE_OR_CONTRACT_DIFFERENCE",
        "I08: position-delta→OrderIntent; I68: explicit OrderRequest",
    )
    record(
        "order_request_model",
        "TYPE_OR_CONTRACT_DIFFERENCE",
        "I08 Order/OrderIntent vs I68 OrderRequest overlapping fields only",
    )
    record(
        "side_semantics",
        "SEMANTICALLY_EQUIVALENT",
        "buy≡BUY / sell≡SELL after normalization",
    )
    record(
        "order_type_semantics",
        "PARTIAL_OVERLAP",
        "I08 pipeline emits MARKET only; I68 supports market+limit",
    )
    record(
        "quantity_semantics",
        "SAME",
        f"qty={QTY} both sides",
    )
    record(
        "price_semantics_market_fill",
        "SEMANTICALLY_EQUIVALENT",
        f"market buy/sell fill math matches under identical mid/slippage",
    )
    record(
        "client_order_identifiers",
        "NOT_EXERCISED",
        "I68 client_id unused by PaperOrderExecutor; I08 has no client_id",
    )
    record(
        "submit_result_ack_mapping",
        "PARTIAL_OVERLAP",
        "I08 ExecutionResult.fills[] vs I68 OrderExecutionResult(status, fill)",
    )
    record(
        "reject_error_mapping",
        "BEHAVIORAL_DIFFERENCE",
        "I08 gate-block reasons vs I68 reject reason strings; no shared taxonomy",
    )
    record(
        "cancel_intent_result",
        "NOT_EXERCISED",
        "No cancel API on I08 pipeline or I68 PaperOrderExecutor",
    )
    record(
        "status_state_mapping",
        "TYPE_OR_CONTRACT_DIFFERENCE",
        "I08 blocked flag vs I68 OrderStatus literals",
    )
    record(
        "partial_fill_representation",
        "NOT_EXERCISED",
        "Neither paper path emits partial fills",
    )
    record(
        "terminal_state_handling",
        "SEMANTICALLY_EQUIVALENT",
        "successful market path ends with one full fill on both surfaces",
    )
    record(
        "idempotency_retry_semantics",
        "NOT_EXERCISED",
        "No dedupe/retry semantics exercised on paper surfaces",
    )
    record(
        "fee_representation",
        "SEMANTICALLY_EQUIVALENT",
        f"numeric fee≈{expected_fee} under identical fee_bps",
    )
    record(
        "mg_i08_type_coupling_risk_layer",
        "SAME",
        "MG-I08-TYPE-COUPLING present: risk_layer→execution_simple.types.Order",
    )

    missing = [c for c in CAPABILITY_ORDER if c not in observations]
    assert not missing, f"incomplete parity ledger: {missing}"
    counts = _count(observations)

    # Evidence gates
    assert counts["SEMANTICALLY_EQUIVALENT"] >= 1
    assert counts["TYPE_OR_CONTRACT_DIFFERENCE"] >= 1
    assert counts["NOT_EXERCISED"] >= 1
    assert counts["BEHAVIORAL_DIFFERENCE"] >= 1
    assert counts["SAME"] + counts["SEMANTICALLY_EQUIVALENT"] < len(CAPABILITY_ORDER)

    # Explicit non-claims — suite PASS ≠ SUPERSEDED / full replacement
    functional_equivalence_common_surface = (
        counts["BEHAVIORAL_DIFFERENCE"] == 0
        and counts["TYPE_OR_CONTRACT_DIFFERENCE"] == 0
        and counts["NOT_EXERCISED"] == 0
        and counts["PARTIAL_OVERLAP"] == 0
    )
    # Observed differences ⇒ common-surface full equivalence NOT proven.
    assert functional_equivalence_common_surface is False

    suite_result = {
        "SUITE_ID": SUITE_ID,
        "COMMON_CAPABILITIES_EXERCISED_COUNT": len(CAPABILITY_ORDER),
        "COUNTS": counts,
        "LEDGER": {k: asdict(observations[k]) for k in CAPABILITY_ORDER},
        "FUNCTIONAL_EQUIVALENCE_COMMON_SURFACE_PROVEN": False,
        "FUNCTIONAL_REPLACEMENT_I08_BY_I68_PROVEN": False,
        "I08_INDEPENDENT_RESPONSIBILITY_REMAINS": True,
        "MG_I08_TYPE_COUPLING_PRESENT": True,
        "SUPERSEDED_I08_PROVEN": False,
        "NETWORK_EFFECT": "NONE",
        "RUNTIME_EXECUTION": False,
        "ORDER_EFFECT": "NONE",
    }
    # Stable JSON for forensic append consumers / debugging.
    assert json.loads(json.dumps(suite_result))["SUPERSEDED_I08_PROVEN"] is False
    assert suite_result["FUNCTIONAL_REPLACEMENT_I08_BY_I68_PROVEN"] is False
    assert suite_result["MG_I08_TYPE_COUPLING_PRESENT"] is True
    assert suite_result["I08_INDEPENDENT_RESPONSIBILITY_REMAINS"] is True
