"""Deterministic round-trip economic ledger for simulated portfolio observability."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Mapping, Sequence

ROUND_TRIP_LEDGER_SCHEMA_ID = "CURRENT_SIMULATED_ECONOMIC_ROUND_TRIP_LEDGER_V1"
ROUND_TRIP_LEDGER_SCHEMA_VERSION = "v1"
NOT_EMITTED = "NOT_EMITTED"


@dataclass(frozen=True)
class SimulatedEconomicsObservabilityContextV1:
    """Optional per-epoch metadata; does not affect simulated fill economics."""

    epoch_id: str = ""
    timestamp: str = ""
    entry_decision: str = ""
    terminal_decision: str = ""
    terminal_reason: str = ""
    strategy_ref: str = ""
    market_regime_at_entry: str = ""
    volatility_context_at_entry: str = ""


def _dec_str(value: Decimal | str | None) -> str:
    if value is None:
        return "0"
    return str(value)


def _field_or_not_emitted(value: str) -> str:
    text = str(value or "").strip()
    return text if text else NOT_EMITTED


@dataclass
class _ActiveLifecycleLedgerStateV1:
    round_trip_id: int
    entry_epoch_id: str
    entry_timestamp: str
    entry_decision: str
    strategy_ref: str
    market_regime_at_entry: str
    volatility_context_at_entry: str
    entry_price: Decimal
    initial_abs_quantity: Decimal
    max_abs_quantity: Decimal
    fill_count: int = 0
    reduction_count: int = 0
    last_abs_quantity: Decimal = Decimal("0")
    gross_realized_pnl: Decimal = Decimal("0")
    fees: Decimal = Decimal("0")
    slippage: Decimal = Decimal("0")
    funding: Decimal = Decimal("0")
    direction: str = ""


@dataclass
class SimulatedRoundTripLedgerCollectorV1:
    """In-memory collector; append-only during portfolio processing."""

    schema_id: str = ROUND_TRIP_LEDGER_SCHEMA_ID
    schema_version: str = ROUND_TRIP_LEDGER_SCHEMA_VERSION
    rows: list[dict[str, Any]] = field(default_factory=list)
    _active: _ActiveLifecycleLedgerStateV1 | None = None
    _next_id: int = 1

    def on_lifecycle_open(
        self,
        *,
        context: SimulatedEconomicsObservabilityContextV1 | None,
        entry_price: Decimal,
        abs_quantity: Decimal,
        direction: str,
    ) -> None:
        ctx = context or SimulatedEconomicsObservabilityContextV1()
        self._active = _ActiveLifecycleLedgerStateV1(
            round_trip_id=self._next_id,
            entry_epoch_id=_field_or_not_emitted(ctx.epoch_id),
            entry_timestamp=_field_or_not_emitted(ctx.timestamp),
            entry_decision=_field_or_not_emitted(ctx.entry_decision),
            strategy_ref=_field_or_not_emitted(ctx.strategy_ref),
            market_regime_at_entry=_field_or_not_emitted(ctx.market_regime_at_entry),
            volatility_context_at_entry=_field_or_not_emitted(ctx.volatility_context_at_entry),
            entry_price=entry_price,
            initial_abs_quantity=abs_quantity,
            max_abs_quantity=abs_quantity,
            last_abs_quantity=abs_quantity,
            direction=direction,
        )

    def on_lifecycle_fill(
        self,
        *,
        abs_quantity: Decimal,
        lifecycle_leg_pnl_delta: Decimal,
        lifecycle_fees_delta: Decimal,
        lifecycle_slippage_delta: Decimal,
    ) -> None:
        active = self._active
        if active is None:
            return
        active.fill_count += 1
        if abs_quantity < active.last_abs_quantity and abs_quantity > 0:
            active.reduction_count += 1
        if abs_quantity > active.max_abs_quantity:
            active.max_abs_quantity = abs_quantity
        active.last_abs_quantity = abs_quantity
        active.gross_realized_pnl += lifecycle_leg_pnl_delta
        active.fees += lifecycle_fees_delta
        active.slippage += lifecycle_slippage_delta

    def on_lifecycle_funding(self, *, funding_delta: Decimal) -> None:
        if self._active is not None:
            self._active.funding += funding_delta

    def on_lifecycle_complete(
        self,
        *,
        context: SimulatedEconomicsObservabilityContextV1 | None,
        exit_price: Decimal,
        lifecycle_leg_pnl: Decimal,
        lifecycle_fees: Decimal,
        lifecycle_slippage: Decimal,
        lifecycle_funding: Decimal,
    ) -> None:
        active = self._active
        if active is None:
            return
        ctx = context or SimulatedEconomicsObservabilityContextV1()
        gross = lifecycle_leg_pnl
        fees = lifecycle_fees
        slip = lifecycle_slippage
        funding = lifecycle_funding
        net = gross - fees - slip - funding
        entry_notional = active.initial_abs_quantity * active.entry_price
        self.rows.append(
            {
                "round_trip_id": active.round_trip_id,
                "entry_epoch_id": active.entry_epoch_id,
                "exit_epoch_id": _field_or_not_emitted(ctx.epoch_id),
                "entry_timestamp": active.entry_timestamp,
                "exit_timestamp": _field_or_not_emitted(ctx.timestamp),
                "direction": active.direction,
                "strategy_ref": active.strategy_ref,
                "entry_price": _dec_str(active.entry_price),
                "exit_price": _dec_str(exit_price),
                "initial_quantity": _dec_str(active.initial_abs_quantity),
                "max_abs_quantity": _dec_str(active.max_abs_quantity),
                "entry_notional": _dec_str(entry_notional),
                "fill_count": active.fill_count,
                "reduction_count": active.reduction_count,
                "gross_realized_pnl": _dec_str(gross),
                "fees": _dec_str(fees),
                "slippage": _dec_str(slip),
                "funding": _dec_str(funding),
                "net_pnl": _dec_str(net),
                "entry_decision": active.entry_decision,
                "terminal_decision": _field_or_not_emitted(
                    ctx.terminal_decision or ctx.entry_decision
                ),
                "terminal_reason": _field_or_not_emitted(ctx.terminal_reason),
                "market_regime_at_entry": active.market_regime_at_entry,
                "volatility_context_at_entry": active.volatility_context_at_entry,
            }
        )
        self._next_id += 1
        self._active = None

    def open_position_economics_snapshot(
        self,
        *,
        portfolio_state: Mapping[str, Any],
    ) -> dict[str, Any] | None:
        if self._active is None:
            return None
        return {
            "economics_class": "OPEN_POSITION_ECONOMICS",
            "round_trip_in_progress_id": self._active.round_trip_id,
            "entry_epoch_id": self._active.entry_epoch_id,
            "direction": self._active.direction,
            "max_abs_quantity": _dec_str(self._active.max_abs_quantity),
            "in_lifecycle_gross_realized_pnl": _dec_str(self._active.gross_realized_pnl),
            "in_lifecycle_fees": _dec_str(self._active.fees),
            "in_lifecycle_slippage": _dec_str(self._active.slippage),
            "in_lifecycle_funding": _dec_str(self._active.funding),
            "portfolio_unrealized_pnl": portfolio_state.get("unrealized_pnl", "0"),
        }


def ledger_document_from_collector_v1(
    collector: SimulatedRoundTripLedgerCollectorV1,
    *,
    bindings: Mapping[str, str],
    open_position_economics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    doc = {
        "schema_id": collector.schema_id,
        "schema_version": collector.schema_version,
        "bindings": dict(bindings),
        "completed_round_trips": list(collector.rows),
        "open_position_economics": open_position_economics,
    }
    payload = json.dumps(doc, sort_keys=True, separators=(",", ":"))
    doc["content_digest_sha256"] = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return doc


def ledger_content_digest_v1(document: Mapping[str, Any]) -> str:
    without = {k: v for k, v in document.items() if k != "content_digest_sha256"}
    payload = json.dumps(without, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def reconcile_ledger_against_portfolio_v1(
    *,
    collector: SimulatedRoundTripLedgerCollectorV1,
    portfolio_completed_trade_count: int,
    portfolio_realized_pnl: Decimal,
    portfolio_cumulative_fees: Decimal,
    portfolio_cumulative_slippage: Decimal,
    portfolio_cumulative_funding: Decimal,
    portfolio_has_open_exposure: bool,
    open_lifecycle_fees: Decimal = Decimal("0"),
    open_lifecycle_slippage: Decimal = Decimal("0"),
    open_lifecycle_funding: Decimal = Decimal("0"),
    open_lifecycle_gross: Decimal = Decimal("0"),
) -> tuple[bool, list[str]]:
    """Reconcile completed round-trip ledger rows against portfolio accounting."""
    blockers: list[str] = []
    rows = collector.rows
    if len(rows) != portfolio_completed_trade_count:
        blockers.append(
            f"ROUND_TRIP_COUNT_MISMATCH:ledger={len(rows)}:portfolio={portfolio_completed_trade_count}"
        )

    def _sum_field(key: str) -> Decimal:
        total = Decimal("0")
        for row in rows:
            total += Decimal(str(row.get(key) or "0"))
        return total

    ledger_gross = _sum_field("gross_realized_pnl")
    ledger_fees = _sum_field("fees")
    ledger_slip = _sum_field("slippage")
    ledger_funding = _sum_field("funding")
    ledger_net = _sum_field("net_pnl")

    if portfolio_has_open_exposure:
        expected_gross = portfolio_realized_pnl - open_lifecycle_gross
        expected_fees = portfolio_cumulative_fees - open_lifecycle_fees
        expected_slip = portfolio_cumulative_slippage - open_lifecycle_slippage
        expected_funding = portfolio_cumulative_funding - open_lifecycle_funding
    else:
        expected_gross = portfolio_realized_pnl
        expected_fees = portfolio_cumulative_fees
        expected_slip = portfolio_cumulative_slippage
        expected_funding = portfolio_cumulative_funding

    if ledger_gross != expected_gross:
        blockers.append(f"GROSS_PNL_MISMATCH:ledger={ledger_gross}:expected={expected_gross}")
    if ledger_fees != expected_fees:
        blockers.append(f"FEES_MISMATCH:ledger={ledger_fees}:expected={expected_fees}")
    if ledger_slip != expected_slip:
        blockers.append(f"SLIPPAGE_MISMATCH:ledger={ledger_slip}:expected={expected_slip}")
    if ledger_funding != expected_funding:
        blockers.append(f"FUNDING_MISMATCH:ledger={ledger_funding}:expected={expected_funding}")

    expected_net = ledger_gross - ledger_fees - ledger_slip - ledger_funding
    if ledger_net != expected_net:
        blockers.append(f"NET_PNL_INTERNAL_MISMATCH:ledger={ledger_net}:expected={expected_net}")

    return (len(blockers) == 0, blockers)


def ledger_totals_v1(collector: SimulatedRoundTripLedgerCollectorV1) -> dict[str, str]:
    totals = {
        "completed_round_trip_count": str(len(collector.rows)),
        "gross_pnl": "0",
        "fees": "0",
        "slippage": "0",
        "funding": "0",
        "net_pnl": "0",
    }
    gross = fees = slip = funding = net = Decimal("0")
    for row in collector.rows:
        gross += Decimal(str(row.get("gross_realized_pnl") or "0"))
        fees += Decimal(str(row.get("fees") or "0"))
        slip += Decimal(str(row.get("slippage") or "0"))
        funding += Decimal(str(row.get("funding") or "0"))
        net += Decimal(str(row.get("net_pnl") or "0"))
    totals["gross_pnl"] = str(gross)
    totals["fees"] = str(fees)
    totals["slippage"] = str(slip)
    totals["funding"] = str(funding)
    totals["net_pnl"] = str(net)
    return totals
