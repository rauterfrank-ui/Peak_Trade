from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, Iterable, List, Mapping, Optional, Union, Literal


@dataclass(frozen=True)
class Money:
    """
    Money value (amount + currency).

    Slice 2 uses a single quote currency for accounting; this type exists to
    make currency explicit at the edges and in exports when needed.
    """

    amount: Decimal
    currency: str

    def to_dict(self) -> Dict[str, Any]:
        return {"amount": str(self.amount), "currency": self.currency}


@dataclass(frozen=True)
class Account:
    """
    Account balance in quote currency.

    In Slice 2, the engine internally stores balances as Dict[str, Decimal] for
    performance and deterministic exports; this domain object is a thin,
    explicit representation for snapshots/typing.
    """

    name: str
    balance: Decimal

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "balance": str(self.balance)}


@dataclass(frozen=True)
class QuantizationPolicy:
    """
    Deterministic rounding/quantization policy.

    Contract:
    - NEVER accept float inputs (convert at ingestion)
    - ALWAYS quantize after arithmetic that can introduce repeating decimals
    """

    qty_quant: Decimal = Decimal("0.00000001")
    price_quant: Decimal = Decimal("0.00000001")
    money_quant: Decimal = Decimal("0.00000001")
    rounding: str = ROUND_HALF_UP


@dataclass(frozen=True)
class Posting:
    """
    One posting in a double-entry journal entry.

    Convention:
    - amount is in QUOTE currency (single-currency Slice 2)
    - amount > 0: debit
    - amount < 0: credit
    """

    account: str
    amount: Decimal

    def to_dict(self) -> Dict[str, Any]:
        return {"account": self.account, "amount": str(self.amount)}


@dataclass(frozen=True)
class JournalEntry:
    """
    Double-entry journal entry. Sum(postings.amount) == 0 must hold.

    ts_sim is used for deterministic ordering; ts_utc is explicitly ignored.
    """

    entry_id: str
    ts_sim: int
    event_id: str
    symbol: str
    kind: str  # e.g. "FILL"
    postings: List[Posting]
    meta: Dict[str, Any] = field(default_factory=dict)

    def postings_sum(self) -> Decimal:
        return sum((p.amount for p in self.postings), Decimal("0"))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "ts_sim": self.ts_sim,
            "event_id": self.event_id,
            "symbol": self.symbol,
            "kind": self.kind,
            "postings": [p.to_dict() for p in self.postings],
            "meta": dict(self.meta),
        }


@dataclass
class Position:
    """
    Deterministic position state for a symbol using weighted-average cost (WAC).

    - quantity: signed base units (positive=long, negative=short)
    - avg_cost: quote per base unit (always >= 0)
    - realized_pnl: accumulated realized PnL in quote currency (fees excluded; fees are tracked separately)
    - fees: accumulated fees in quote currency
    """

    symbol: str
    quantity: Decimal = Decimal("0")
    avg_cost: Decimal = Decimal("0")
    realized_pnl: Decimal = Decimal("0")
    fees: Decimal = Decimal("0")

    def is_flat(self) -> bool:
        return self.quantity == 0

    def inventory_cost_balance(self) -> Decimal:
        """
        Signed inventory cost in quote currency.

        For shorts, this is negative (credit balance).
        """
        if self.quantity == 0 or self.avg_cost == 0:
            return Decimal("0")
        return self.avg_cost * self.quantity

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "quantity": str(self.quantity),
            "avg_cost": str(self.avg_cost),
            "realized_pnl": str(self.realized_pnl),
            "fees": str(self.fees),
        }


@dataclass(frozen=True)
class ValuationSnapshot:
    """
    Deterministic valuation snapshot at a point in time.
    """

    ts_sim: int
    quote_currency: str
    cash: Decimal
    positions: List[Dict[str, Any]]
    realized_pnl: Decimal
    unrealized_pnl: Decimal
    equity: Decimal
    meta: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ts_sim": self.ts_sim,
            "quote_currency": self.quote_currency,
            "cash": str(self.cash),
            "positions": list(self.positions),
            "realized_pnl": str(self.realized_pnl),
            "unrealized_pnl": str(self.unrealized_pnl),
            "equity": str(self.equity),
            "meta": dict(self.meta),
        }


# =============================================================================
# EXEC_SLICE2: Deterministic Ledger/Accounting (FIFO lots)
# =============================================================================

# Public aliases (explicit at the type level).
InstrumentId = str
Currency = str


@dataclass(frozen=True)
class DecimalPolicy:
    """
    Centralized deterministic Decimal quantization policy for Slice2.

    Contract:
    - All qty/price/money values MUST be Decimals (floats forbidden at ingestion).
    - All values MUST be quantized via this policy for deterministic results.
    """

    QTY_QUANT: Decimal = Decimal("0.00000001")
    PRICE_QUANT: Decimal = Decimal("0.00000001")
    MONEY_QUANT: Decimal = Decimal("0.00000001")
    ROUNDING: str = ROUND_HALF_UP

    @staticmethod
    def default() -> "DecimalPolicy":
        return DecimalPolicy()

    def quantize_qty(self, v: Decimal) -> Decimal:
        return v.quantize(self.QTY_QUANT, rounding=self.ROUNDING)

    def quantize_price(self, v: Decimal) -> Decimal:
        return v.quantize(self.PRICE_QUANT, rounding=self.ROUNDING)

    def quantize_money(self, v: Decimal) -> Decimal:
        return v.quantize(self.MONEY_QUANT, rounding=self.ROUNDING)


@dataclass(frozen=True)
class FillEvent:
    ts_utc: str  # ISO8601 UTC with trailing "Z"
    seq: int
    instrument: InstrumentId
    side: Literal["BUY", "SELL"]
    qty: Decimal
    price: Decimal
    fee: Decimal = Decimal("0")
    fee_ccy: Currency = "USD"
    trade_id: Optional[str] = None


@dataclass(frozen=True)
class MarkEvent:
    ts_utc: str  # ISO8601 UTC with trailing "Z"
    seq: int
    instrument: InstrumentId
    price: Decimal


LedgerEvent = Union[FillEvent, MarkEvent]


@dataclass
class PositionLot:
    qty_signed: Decimal
    price: Decimal
    ts_utc: str
    seq: int


@dataclass
class PositionState:
    lots: List[PositionLot] = field(default_factory=list)
    last_mark_price: Optional[Decimal] = None

    @property
    def qty_signed(self) -> Decimal:
        return sum((lot.qty_signed for lot in self.lots), Decimal("0"))

    @property
    def avg_price(self) -> Optional[Decimal]:
        qty = self.qty_signed
        if qty == 0:
            return None
        qty_abs = qty.copy_abs()
        cost_abs = sum(((lot.qty_signed.copy_abs() * lot.price) for lot in self.lots), Decimal("0"))
        if qty_abs == 0:
            return None
        return cost_abs / qty_abs


@dataclass
class AccountState:
    cash_by_ccy: Dict[Currency, Decimal] = field(default_factory=dict)
    positions: Dict[InstrumentId, PositionState] = field(default_factory=dict)
    realized_pnl_by_ccy: Dict[Currency, Decimal] = field(default_factory=dict)
    fees_by_ccy: Dict[Currency, Decimal] = field(default_factory=dict)


@dataclass(frozen=True)
class LedgerEntry:
    ts_utc: str
    seq: int
    kind: str
    instrument: Optional[InstrumentId]
    fields: Dict[str, Any]


@dataclass(frozen=True)
class LedgerSnapshot:
    ts_utc_last: str
    seq_last: int
    account: AccountState
    # Computed at snapshot-time (deterministic, derived from account state + marks).
    unrealized_pnl_by_ccy: Dict[Currency, Decimal] = field(default_factory=dict)
    equity_by_ccy: Dict[Currency, Decimal] = field(default_factory=dict)
    # Optional: stable-material inputs used for hashing/forensics.
    hash_inputs: Optional[Dict[str, Any]] = None
