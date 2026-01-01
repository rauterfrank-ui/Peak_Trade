"""
Execution Contracts & Stable Types (WP0E - Phase 0 Foundation)

This module defines the core data types and protocols for the live execution system.
These types are STABLE and form the contract between execution components.

Design Goals:
- Deterministic serialization (repr/json)
- Type-safe (mypy/ruff compatible)
- No cyclic imports
- Minimal dependencies (dataclasses/enums only)
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, Dict, Any, List
import json


# ============================================================================
# Order State Machine Types
# ============================================================================


class OrderState(str, Enum):
    """Order lifecycle states (deterministic state machine)"""

    CREATED = "CREATED"  # Order object created, not yet submitted
    SUBMITTED = "SUBMITTED"  # Sent to exchange, awaiting acknowledgment
    ACKNOWLEDGED = "ACKNOWLEDGED"  # Exchange confirmed receipt
    PARTIALLY_FILLED = "PARTIALLY_FILLED"  # Some fills received
    FILLED = "FILLED"  # Fully filled
    CANCELLED = "CANCELLED"  # User or system cancelled
    REJECTED = "REJECTED"  # Exchange rejected
    EXPIRED = "EXPIRED"  # Time-in-force expired
    FAILED = "FAILED"  # System/network failure

    def is_terminal(self) -> bool:
        """Check if this state is terminal (no further transitions)"""
        return self in {
            OrderState.FILLED,
            OrderState.CANCELLED,
            OrderState.REJECTED,
            OrderState.EXPIRED,
            OrderState.FAILED,
        }

    def is_active(self) -> bool:
        """Check if order is active (can still receive fills)"""
        return self in {
            OrderState.SUBMITTED,
            OrderState.ACKNOWLEDGED,
            OrderState.PARTIALLY_FILLED,
        }


class OrderSide(str, Enum):
    """Order side (BUY or SELL)"""

    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    """Order type"""

    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"


class TimeInForce(str, Enum):
    """Time-in-force specification"""

    GTC = "GTC"  # Good Till Cancelled
    IOC = "IOC"  # Immediate Or Cancel
    FOK = "FOK"  # Fill Or Kill
    DAY = "DAY"  # Day order


# ============================================================================
# Core Order Type
# ============================================================================


@dataclass
class Order:
    """
    Core order representation (immutable after creation).

    Design:
    - Use Decimal for amounts/prices (no float precision issues)
    - client_order_id is our stable identifier
    - exchange_order_id is assigned by exchange after ACK
    """

    # Identity
    client_order_id: str
    exchange_order_id: Optional[str] = None

    # Order specification
    symbol: str = ""
    side: OrderSide = OrderSide.BUY
    order_type: OrderType = OrderType.MARKET
    quantity: Decimal = Decimal("0")
    price: Optional[Decimal] = None  # None for MARKET orders
    time_in_force: TimeInForce = TimeInForce.GTC

    # State & metadata
    state: OrderState = OrderState.CREATED
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    # Strategy context
    strategy_id: Optional[str] = None
    session_id: Optional[str] = None

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Deterministic dict conversion (for JSON/logging)"""
        d = asdict(self)
        # Convert Decimal to string for JSON compatibility
        d["quantity"] = str(self.quantity)
        if self.price is not None:
            d["price"] = str(self.price)
        # Convert datetime to ISO string
        d["created_at"] = self.created_at.isoformat()
        d["updated_at"] = self.updated_at.isoformat()
        return d

    def to_json(self) -> str:
        """Deterministic JSON serialization"""
        return json.dumps(self.to_dict(), sort_keys=True)

    def __repr__(self) -> str:
        """Deterministic repr (stable for tests)"""
        return (
            f"Order(client_order_id={self.client_order_id!r}, "
            f"symbol={self.symbol!r}, side={self.side.value}, "
            f"quantity={self.quantity}, state={self.state.value})"
        )


# ============================================================================
# Fill Type
# ============================================================================


@dataclass
class Fill:
    """
    Represents a partial or complete fill of an order.

    Design:
    - Multiple fills can reference the same order (partial fills)
    - fill_id is exchange-provided unique identifier
    """

    fill_id: str
    client_order_id: str
    exchange_order_id: str

    # Fill details
    symbol: str
    side: OrderSide
    quantity: Decimal
    price: Decimal
    fee: Decimal = Decimal("0")
    fee_currency: str = "USD"

    # Timestamp
    filled_at: datetime = field(default_factory=datetime.utcnow)

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Deterministic dict conversion"""
        d = asdict(self)
        d["quantity"] = str(self.quantity)
        d["price"] = str(self.price)
        d["fee"] = str(self.fee)
        d["filled_at"] = self.filled_at.isoformat()
        return d

    def to_json(self) -> str:
        """Deterministic JSON serialization"""
        return json.dumps(self.to_dict(), sort_keys=True)

    def __repr__(self) -> str:
        """Deterministic repr"""
        return (
            f"Fill(fill_id={self.fill_id!r}, "
            f"client_order_id={self.client_order_id!r}, "
            f"quantity={self.quantity}, price={self.price})"
        )


# ============================================================================
# Ledger Entry Type
# ============================================================================


@dataclass
class LedgerEntry:
    """
    Append-only ledger entry (audit trail).

    Design:
    - Immutable after creation
    - Every state change creates a new entry
    - Deterministic ordering via timestamp + sequence
    """

    entry_id: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    sequence: int = 0

    # What happened
    event_type: str = ""  # e.g., "ORDER_SUBMITTED", "FILL_RECEIVED"
    client_order_id: str = ""

    # State snapshot
    old_state: Optional[OrderState] = None
    new_state: Optional[OrderState] = None

    # Context
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Deterministic dict conversion"""
        d = asdict(self)
        d["timestamp"] = self.timestamp.isoformat()
        if self.old_state:
            d["old_state"] = self.old_state.value
        if self.new_state:
            d["new_state"] = self.new_state.value
        return d

    def to_json(self) -> str:
        """Deterministic JSON serialization"""
        return json.dumps(self.to_dict(), sort_keys=True)

    def __repr__(self) -> str:
        """Deterministic repr"""
        return (
            f"LedgerEntry(entry_id={self.entry_id!r}, "
            f"event_type={self.event_type!r}, "
            f"sequence={self.sequence})"
        )


# ============================================================================
# Reconciliation Types
# ============================================================================


@dataclass
class ReconDiff:
    """
    Represents a divergence between local and exchange state.

    Design:
    - Used by reconciliation module to track differences
    - Severity: INFO, WARN, ERROR, CRITICAL
    """

    diff_id: str
    timestamp: datetime = field(default_factory=datetime.utcnow)

    # What diverged
    client_order_id: str = ""
    exchange_order_id: Optional[str] = None

    # Divergence details
    local_state: Optional[OrderState] = None
    exchange_state: Optional[str] = None
    severity: str = "WARN"  # INFO, WARN, ERROR, CRITICAL
    diff_type: str = "UNKNOWN"  # POSITION, CASH, ORDER, FILL

    # Description
    description: str = ""
    details: Dict[str, Any] = field(default_factory=dict)

    # Resolution
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    resolution_action: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Deterministic dict conversion"""
        d = asdict(self)
        d["timestamp"] = self.timestamp.isoformat()
        if self.local_state:
            d["local_state"] = self.local_state.value
        if self.resolved_at:
            d["resolved_at"] = self.resolved_at.isoformat()
        return d

    def to_json(self) -> str:
        """Deterministic JSON serialization"""
        return json.dumps(self.to_dict(), sort_keys=True)

    def __repr__(self) -> str:
        """Deterministic repr"""
        return (
            f"ReconDiff(diff_id={self.diff_id!r}, "
            f"severity={self.severity}, resolved={self.resolved})"
        )


@dataclass
class ReconSummary:
    """
    Structured summary of reconciliation run.

    Design:
    - Aggregated counts by diff_type and severity
    - Top-N diffs for observability
    - Deterministic ordering (stable sort by severity, timestamp, diff_id)
    - WP0D Observability: Enables audit trail and alerting

    Phase 0: SIM/PAPER only (no live exchange data)
    """

    run_id: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    session_id: str = ""
    strategy_id: str = ""

    # Aggregate counts
    total_diffs: int = 0
    counts_by_severity: Dict[str, int] = field(default_factory=dict)
    counts_by_type: Dict[str, int] = field(default_factory=dict)

    # Top-N diffs (for audit emission)
    top_diffs: List[ReconDiff] = field(default_factory=list)

    # Summary flags
    has_critical: bool = False
    has_fail: bool = False
    max_severity: str = "INFO"

    def to_dict(self) -> Dict[str, Any]:
        """Deterministic dict conversion"""
        return {
            "run_id": self.run_id,
            "timestamp": self.timestamp.isoformat(),
            "session_id": self.session_id,
            "strategy_id": self.strategy_id,
            "total_diffs": self.total_diffs,
            "counts_by_severity": dict(sorted(self.counts_by_severity.items())),
            "counts_by_type": dict(sorted(self.counts_by_type.items())),
            "top_diffs": [d.to_dict() for d in self.top_diffs],
            "has_critical": self.has_critical,
            "has_fail": self.has_fail,
            "max_severity": self.max_severity,
        }

    def to_json(self) -> str:
        """Deterministic JSON serialization"""
        return json.dumps(self.to_dict(), sort_keys=True, indent=2)

    def __repr__(self) -> str:
        """Deterministic repr"""
        return (
            f"ReconSummary(run_id={self.run_id!r}, "
            f"total_diffs={self.total_diffs}, max_severity={self.max_severity})"
        )


# ============================================================================
# Risk Decision Type
# ============================================================================


class RiskDecision(str, Enum):
    """
    Risk layer decision (returned by risk_hook).

    Design:
    - ALLOW: proceed with order
    - BLOCK: reject order (e.g., limit exceeded)
    - PAUSE: temporarily halt trading (e.g., market conditions)
    """

    ALLOW = "ALLOW"
    BLOCK = "BLOCK"
    PAUSE = "PAUSE"


@dataclass
class RiskResult:
    """
    Risk evaluation result (returned by risk_hook).

    Design:
    - decision: ALLOW/BLOCK/PAUSE
    - reason: human-readable explanation
    - metadata: structured data (limits, metrics, etc.)
    """

    decision: RiskDecision
    reason: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Deterministic dict conversion"""
        return {
            "decision": self.decision.value,
            "reason": self.reason,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
        }

    def to_json(self) -> str:
        """Deterministic JSON serialization"""
        return json.dumps(self.to_dict(), sort_keys=True)

    def __repr__(self) -> str:
        """Deterministic repr"""
        return f"RiskResult(decision={self.decision.value}, reason={self.reason!r})"


# ============================================================================
# Validation Helpers
# ============================================================================


def validate_order(order: Order) -> bool:
    """
    Basic order validation (sanity checks).

    Returns True if order is valid, False otherwise.
    """
    if not order.client_order_id:
        return False
    if not order.symbol:
        return False
    if order.quantity <= 0:
        return False
    if order.order_type == OrderType.LIMIT and order.price is None:
        return False
    if order.price is not None and order.price <= 0:
        return False
    return True


def serialize_contracts_snapshot() -> Dict[str, Any]:
    """
    Generate deterministic snapshot of all contract types (for evidence).

    Used by tests to verify serialization stability.
    """
    sample_order = Order(
        client_order_id="test_order_001",
        symbol="BTC-EUR",
        side=OrderSide.BUY,
        quantity=Decimal("0.001"),
        price=Decimal("50000.00"),
        state=OrderState.CREATED,
    )

    sample_fill = Fill(
        fill_id="fill_001",
        client_order_id="test_order_001",
        exchange_order_id="exch_001",
        symbol="BTC-EUR",
        side=OrderSide.BUY,
        quantity=Decimal("0.001"),
        price=Decimal("50000.00"),
    )

    sample_ledger_entry = LedgerEntry(
        entry_id="ledger_001",
        sequence=1,
        event_type="ORDER_CREATED",
        client_order_id="test_order_001",
        old_state=None,
        new_state=OrderState.CREATED,
    )

    sample_recon_diff = ReconDiff(
        diff_id="diff_001",
        client_order_id="test_order_001",
        local_state=OrderState.FILLED,
        exchange_state="PARTIALLY_FILLED",
        severity="WARN",
        description="Fill quantity mismatch",
    )

    sample_risk_result = RiskResult(
        decision=RiskDecision.ALLOW,
        reason="All limits OK",
    )

    return {
        "order": sample_order.to_dict(),
        "fill": sample_fill.to_dict(),
        "ledger_entry": sample_ledger_entry.to_dict(),
        "recon_diff": sample_recon_diff.to_dict(),
        "risk_result": sample_risk_result.to_dict(),
    }
