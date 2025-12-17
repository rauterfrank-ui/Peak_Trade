# src/live/broker_base.py
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from datetime import datetime
from typing import Any

import pandas as pd

from .orders import LiveExecutionReport, LiveOrderRequest


class BaseBrokerClient(ABC):
    """
    Abstraktes Broker-Interface.

    In diesem Skeleton gibt es noch keine echten Broker-Implementierungen.
    """

    @abstractmethod
    def submit_orders(self, orders: Sequence[LiveOrderRequest]) -> list[LiveExecutionReport]:
        """
        Nimmt eine Liste von Orders entgegen und gibt Execution-Reports zurück.

        In einem echten Adapter würde hier der API-Call zum Broker stattfinden.
        """
        raise NotImplementedError

    def fetch_positions(self) -> pd.DataFrame:
        """
        Optional: Offene Positionen. Im Skeleton: leeres DataFrame.
        """
        return pd.DataFrame(columns=["symbol", "quantity", "avg_price"])

    def close(self) -> None:
        """
        Optional: Aufräumen/Session schließen.
        """
        return None


class DryRunBroker(BaseBrokerClient):
    """
    Einfacher Broker, der Orders nur loggt und keine echten Trades ausführt.
    """

    def __init__(self, log_to_console: bool = True) -> None:
        self.log_to_console = log_to_console

    def submit_orders(self, orders: Sequence[LiveOrderRequest]) -> list[LiveExecutionReport]:
        reports: list[LiveExecutionReport] = []

        for order in orders:
            if self.log_to_console:
                print(
                    f"[DRY-RUN] {order.side} {order.symbol} "
                    f"qty={order.quantity!r} notional={order.notional!r} "
                    f"(strategy={order.strategy_key}, run={order.run_name})"
                )

            ts = datetime.utcnow().isoformat(timespec="seconds") + "Z"
            reports.append(
                LiveExecutionReport(
                    client_order_id=order.client_order_id,
                    status="ACKNOWLEDGED",
                    filled_quantity=0.0,
                    avg_price=None,
                    ts=ts,
                    message="Dry-run only – keine echte Order gesendet.",
                    extra={"mode": "dry_run"},
                )
            )

        return reports


class PaperBroker(BaseBrokerClient):
    """
    Einfacher Paper-Trade-Broker mit Cash- und Positionsfuehrung
    sowie konfigurierbaren Fees & Slippage.

    Annahmen:
    - Jede Order wird vollstaendig und sofort zum simulierten Fill-Preis ausgefuehrt.
    - Referenzpreis kommt aus order.extra["current_price"] (siehe preview_live_orders.py).
    - Slippage wird relativ zum Referenzpreis in bp angewendet.
    - Fees werden pro Trade vom Cash abgezogen.
    """

    def __init__(
        self,
        starting_cash: float,
        base_currency: str = "EUR",
        log_to_console: bool = True,
        fee_bps: float = 0.0,
        fee_min_per_order: float = 0.0,
        slippage_bps: float = 0.0,
    ) -> None:
        self.starting_cash = float(starting_cash)
        self.cash = float(starting_cash)
        self.base_currency = base_currency
        self.log_to_console = log_to_console

        self.fee_bps = float(fee_bps)
        self.fee_min_per_order = float(fee_min_per_order)
        self.slippage_bps = float(slippage_bps)

        # positions[symbol] = {
        #   "qty": float,
        #   "avg_price": float,
        #   "realized_pnl": float,
        #   "last_price": float | None,
        # }
        self.positions: dict[str, dict[str, float]] = {}

        # Liste von Trade-Records (fuer CSV-Export)
        self.trades: list[dict[str, Any]] = []

        # Aggregierte Metriken
        self.total_fees: float = 0.0

    def _determine_fill(
        self,
        order: LiveOrderRequest,
    ) -> tuple[float, float, float]:
        """
        Bestimmt Fill-Menge und -Preis fuer eine Order.

        Rueckgabe:
        - qty:        gefuellte Stueckzahl
        - fill_price: Preis nach Slippage
        - ref_price:  Referenzpreis (z.B. current_price)
        """
        extra = order.extra or {}
        ref_price = extra.get("current_price")
        if ref_price is None or float(ref_price) <= 0:
            raise ValueError(
                f"PaperBroker benoetigt 'current_price' in order.extra fuer Symbol {order.symbol!r}."
            )
        ref_price = float(ref_price)

        # Slippage in bp -> relativer Faktor
        fill_price = ref_price
        if self.slippage_bps and self.slippage_bps != 0.0:
            slip_factor = self.slippage_bps / 10000.0
            if order.side == "BUY":
                fill_price = ref_price * (1.0 + slip_factor)
            elif order.side == "SELL":
                fill_price = ref_price * (1.0 - slip_factor)
            else:
                raise ValueError(f"Unbekannte Order-Seite: {order.side!r}")

        # Menge bestimmen
        qty = None
        if order.quantity is not None:
            qty = float(order.quantity)
        elif order.notional is not None and fill_price > 0:
            qty = float(order.notional) / fill_price

        if qty is None or qty <= 0:
            raise ValueError(
                f"PaperBroker kann keine Fill-Menge ableiten (quantity/notional fehlen oder <= 0) "
                f"fuer Symbol {order.symbol!r}."
            )

        return qty, fill_price, ref_price

    def _compute_fee(self, notional: float) -> float:
        """
        Berechnet die Fee fuer einen Trade auf Basis von bp + Mindestfee.
        """
        variable_fee = abs(notional) * (self.fee_bps / 10000.0) if self.fee_bps != 0.0 else 0.0
        fee = max(variable_fee, self.fee_min_per_order) if self.fee_min_per_order > 0 else variable_fee
        return float(fee)

    def _apply_fill(
        self,
        order: LiveOrderRequest,
        qty: float,
        price: float,
        fee: float,
    ) -> float:
        """
        Wendet einen Fill auf Cash und Positionen an.
        Gibt den realisierten PnL (ohne Fees) aus diesem Trade zurueck.
        """
        symbol = order.symbol
        side = order.side

        if symbol not in self.positions:
            self.positions[symbol] = {
                "qty": 0.0,
                "avg_price": 0.0,
                "realized_pnl": 0.0,
                "last_price": price,
            }

        pos = self.positions[symbol]
        pos_qty = float(pos["qty"])
        avg_price = float(pos["avg_price"])
        realized_pnl = float(pos["realized_pnl"])

        notional = qty * price

        # Cash-Aenderung inkl. Fee
        if side == "BUY":
            # Kauf: Cash nimmt um Notional + Fee ab
            self.cash -= notional + fee
            trade_sign = +1.0  # Long-Anteil
        elif side == "SELL":
            # Verkauf: Cash nimmt um Notional (Brutto) zu, Fee wird abgezogen
            self.cash += notional - fee
            trade_sign = -1.0  # Short-Anteil
        else:
            raise ValueError(f"Unbekannte Order-Seite: {side!r}")

        effective_qty = qty * trade_sign  # >0 long, <0 short

        # Keine bestehende Position: neu eroeffnen
        if pos_qty == 0.0:
            pos_qty = effective_qty
            avg_price = price
            # realized_pnl unveraendert

        # Gleiche Richtung: Durchschnittspreis anpassen
        elif pos_qty * effective_qty > 0:
            total_qty = abs(pos_qty) + abs(effective_qty)
            avg_price = (abs(pos_qty) * avg_price + abs(effective_qty) * price) / total_qty
            pos_qty = pos_qty + effective_qty

        # Gegenrichtung: Position teilweise oder vollstaendig schliessen / flippen
        else:
            # pos_qty und effective_qty haben unterschiedliche Vorzeichen
            old_pos_qty = pos_qty
            closed_qty = min(abs(old_pos_qty), abs(effective_qty))
            # Vorzeichen der alten Position bestimmt PnL-Richtung
            sign_pos = 1.0 if old_pos_qty > 0 else -1.0
            realized_pnl += closed_qty * (price - avg_price) * sign_pos

            # Neue Positionsmenge bestimmen
            if abs(effective_qty) > abs(old_pos_qty):
                # komplett flippen
                remaining_qty = abs(effective_qty) - abs(old_pos_qty)
                pos_qty = remaining_qty * (1.0 if effective_qty > 0 else -1.0)
                avg_price = price
            elif abs(effective_qty) < abs(old_pos_qty):
                # Position teilweise reduziert, Richtung bleibt
                remaining_qty = abs(old_pos_qty) - closed_qty
                pos_qty = remaining_qty * (1.0 if old_pos_qty > 0 else -1.0)
                # avg_price bleibt unveraendert
            else:
                # exakte Schliessung
                pos_qty = 0.0
                avg_price = 0.0

        pos["qty"] = pos_qty
        pos["avg_price"] = avg_price
        pos["realized_pnl"] = realized_pnl
        pos["last_price"] = price

        return realized_pnl

    def submit_orders(self, orders: Sequence[LiveOrderRequest]) -> list[LiveExecutionReport]:
        reports: list[LiveExecutionReport] = []

        for order in orders:
            qty, fill_price, ref_price = self._determine_fill(order)
            notional = qty * fill_price
            fee = self._compute_fee(notional)
            self.total_fees += fee

            realized_pnl = self._apply_fill(order, qty, fill_price, fee)

            # Slippage-Metriken
            slippage_per_unit = fill_price - ref_price
            slippage_bps_actual = (
                (slippage_per_unit / ref_price) * 10000.0 if ref_price > 0 else 0.0
            )

            if self.log_to_console:
                print(
                    f"[PAPER] {order.side} {order.symbol} "
                    f"qty={qty:.8f} fill_price={fill_price:.8f} ref_price={ref_price:.8f} "
                    f"notional={notional:.2f} fee={fee:.4f} {self.base_currency} "
                    f"(strategy={order.strategy_key}, run={order.run_name}) "
                    f"realized_pnl={realized_pnl:.2f} {self.base_currency}"
                )

            ts = datetime.utcnow().isoformat(timespec="seconds") + "Z"

            # Trade-Record speichern
            self.trades.append(
                {
                    "ts": ts,
                    "symbol": order.symbol,
                    "side": order.side,
                    "quantity": qty,
                    "price": fill_price,
                    "ref_price": ref_price,
                    "slippage_per_unit": slippage_per_unit,
                    "slippage_bps": slippage_bps_actual,
                    "notional": notional,
                    "fee": fee,
                    "client_order_id": order.client_order_id,
                    "strategy_key": order.strategy_key,
                    "run_name": order.run_name,
                    "comment": order.comment,
                }
            )

            reports.append(
                LiveExecutionReport(
                    client_order_id=order.client_order_id,
                    status="FILLED",
                    filled_quantity=qty,
                    avg_price=fill_price,
                    ts=ts,
                    message="Paper trade – simulierte Ausfuehrung mit Fees & Slippage.",
                    extra={
                        "mode": "paper_trade",
                        "ref_price": ref_price,
                        "slippage_bps": slippage_bps_actual,
                        "fee": fee,
                    },
                )
            )

        return reports

    def get_positions_df(self) -> pd.DataFrame:
        """
        Gibt die aktuelle Positionsuebersicht als DataFrame zurueck.
        Spalten:
            symbol, quantity, avg_price, last_price,
            market_value, unrealized_pnl, realized_pnl
        """
        rows: list[dict[str, Any]] = []
        for symbol, pos in self.positions.items():
            qty = float(pos["qty"])
            avg_price = float(pos["avg_price"])
            last_price = pos.get("last_price")
            if last_price is not None:
                last_price = float(last_price)

            market_value = None
            unrealized_pnl = None
            if last_price is not None:
                market_value = qty * last_price
                if avg_price > 0:
                    unrealized_pnl = qty * (last_price - avg_price)
                else:
                    unrealized_pnl = 0.0

            rows.append(
                {
                    "symbol": symbol,
                    "quantity": qty,
                    "avg_price": avg_price if avg_price != 0 else None,
                    "last_price": last_price,
                    "market_value": market_value,
                    "unrealized_pnl": unrealized_pnl,
                    "realized_pnl": float(pos["realized_pnl"]),
                }
            )

        if not rows:
            return pd.DataFrame(
                columns=[
                    "symbol",
                    "quantity",
                    "avg_price",
                    "last_price",
                    "market_value",
                    "unrealized_pnl",
                    "realized_pnl",
                ]
            )

        return pd.DataFrame(rows)

    def get_trades_df(self) -> pd.DataFrame:
        """
        Gibt die Trade-Historie als DataFrame zurueck.
        """
        if not self.trades:
            return pd.DataFrame(
                columns=[
                    "ts",
                    "symbol",
                    "side",
                    "quantity",
                    "price",
                    "ref_price",
                    "slippage_per_unit",
                    "slippage_bps",
                    "notional",
                    "fee",
                    "client_order_id",
                    "strategy_key",
                    "run_name",
                    "comment",
                ]
            )
        return pd.DataFrame(self.trades)
