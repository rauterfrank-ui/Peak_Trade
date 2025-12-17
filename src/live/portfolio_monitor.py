# src/live/portfolio_monitor.py
"""
Peak_Trade: Live Portfolio Monitoring & Risk Bridge (Phase 48)
================================================================

Lesender Live-/Shadow-Portfolio-Monitor für Peak_Trade.

Features:
- Portfolio-Snapshot aus Exchange-Client/Broker
- Bridge zu LiveRiskLimits für Portfolio-Level Risk-Checks
- Read-only: Keine Trade-Trigger, keine Auto-Liquidation

Usage:
    from src.live.portfolio_monitor import (
        LivePortfolioMonitor,
        LivePositionSnapshot,
        LivePortfolioSnapshot,
    )
    from src.live.broker_base import BaseBrokerClient

    monitor = LivePortfolioMonitor(exchange_client)
    snapshot = monitor.snapshot()
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .broker_base import BaseBrokerClient
from .risk_limits import LiveRiskLimits

logger = logging.getLogger(__name__)


@dataclass
class LivePositionSnapshot:
    """
    Snapshot einer einzelnen Position.

    Attributes:
        symbol: Trading-Pair (z.B. "BTC/EUR")
        side: Position-Richtung ("long", "short" oder "flat")
        size: Positionsgröße in Units (z.B. 0.5 BTC)
        entry_price: Durchschnittlicher Entry-Preis (falls verfügbar)
        mark_price: Aktuelle Mark/Last-Price (falls verfügbar)
        notional: Abs(size) * mark_price (oder Fallback)
        unrealized_pnl: Unrealisierter PnL (falls verfügbar)
        realized_pnl: Realisierter PnL seit Tagesanfang/Session (falls verfügbar)
        leverage: Leverage (falls im System vorhanden, sonst None)
    """

    symbol: str
    side: str  # "long", "short" oder "flat"
    size: float  # Positionsgröße in Units
    entry_price: float | None = None
    mark_price: float | None = None
    notional: float = 0.0
    unrealized_pnl: float | None = None
    realized_pnl: float | None = None
    leverage: float | None = None

    def __post_init__(self) -> None:
        """Berechnet notional, falls mark_price vorhanden."""
        if self.notional == 0.0 and self.mark_price is not None and self.size != 0.0:
            self.notional = abs(self.size) * self.mark_price


@dataclass
class LivePortfolioSnapshot:
    """
    Snapshot des gesamten Live-Portfolios.

    Attributes:
        as_of: Zeitpunkt des Snapshots
        positions: Liste aller Positionen
        total_notional: Summe aller Positions-Notionals (abs)
        total_unrealized_pnl: Summe über alle Positions-PnL (falls verfügbar)
        total_realized_pnl: Tages-PnL oder Session-PnL
        symbol_notional: Map symbol -> notional
        num_open_positions: Anzahl offener Positionen
        equity: Equity (falls verfügbar)
        cash: Cash (falls verfügbar)
        margin_used: Margin verwendet (falls verfügbar)
    """

    as_of: datetime
    positions: list[LivePositionSnapshot] = field(default_factory=list)

    total_notional: float = 0.0
    total_unrealized_pnl: float = 0.0
    total_realized_pnl: float = 0.0

    symbol_notional: dict[str, float] = field(default_factory=dict)
    num_open_positions: int = 0

    equity: float | None = None
    cash: float | None = None
    margin_used: float | None = None

    def __post_init__(self) -> None:
        """Berechnet Aggregat-Werte aus positions."""
        self._compute_aggregates()

    def _compute_aggregates(self) -> None:
        """Berechnet Aggregat-Werte aus positions."""
        self.total_notional = 0.0
        self.total_unrealized_pnl = 0.0
        self.total_realized_pnl = 0.0
        self.symbol_notional = {}
        self.num_open_positions = 0

        for pos in self.positions:
            if pos.side != "flat" and abs(pos.size) > 1e-10:  # Ignoriere flache Positionen
                self.num_open_positions += 1
                self.total_notional += pos.notional
                self.symbol_notional.setdefault(pos.symbol, 0.0)
                self.symbol_notional[pos.symbol] += pos.notional

                if pos.unrealized_pnl is not None:
                    self.total_unrealized_pnl += pos.unrealized_pnl

                if pos.realized_pnl is not None:
                    self.total_realized_pnl += pos.realized_pnl


class LivePortfolioMonitor:
    """
    Monitor für Live-Portfolio-Snapshots.

    Liest aktuelle Positions- und Account-Daten vom Exchange-Client/Broker
    und baut einen LivePortfolioSnapshot.

    Attributes:
        _exchange_client: Exchange-Client oder Broker-Client
        _risk_limits: Optional LiveRiskLimits für Risk-Checks
    """

    def __init__(
        self,
        exchange_client: BaseBrokerClient,
        risk_limits: LiveRiskLimits | None = None,
    ) -> None:
        """
        Initialisiert den Portfolio-Monitor.

        Args:
            exchange_client: Exchange-Client oder Broker-Client
            risk_limits: Optional LiveRiskLimits für Risk-Checks
        """
        self._exchange_client = exchange_client
        self._risk_limits = risk_limits

    def snapshot(self) -> LivePortfolioSnapshot:
        """
        Liest aktuelle Positions- und ggf. Account-Daten vom exchange_client
        und baut einen LivePortfolioSnapshot.

        Returns:
            LivePortfolioSnapshot mit aktuellen Daten
        """
        as_of = datetime.utcnow()

        # Versuche, Positionen vom Exchange-Client zu holen
        positions_data = self._fetch_positions()

        # Konvertiere zu LivePositionSnapshot
        positions: list[LivePositionSnapshot] = []
        for pos_data in positions_data:
            pos = self._parse_position(pos_data)
            if pos:
                positions.append(pos)

        # Erstelle Snapshot
        snapshot = LivePortfolioSnapshot(
            as_of=as_of,
            positions=positions,
        )

        # Versuche, Account-Daten zu holen (optional)
        account_data = self._fetch_account_data()
        if account_data:
            snapshot.equity = account_data.get("equity")
            snapshot.cash = account_data.get("cash")
            snapshot.margin_used = account_data.get("margin_used")

        return snapshot

    def _fetch_positions(self) -> list[dict[str, Any]]:
        """
        Holt Positionen vom Exchange-Client.

        Returns:
            Liste von Position-Dicts
        """
        try:
            # Versuche fetch_positions() vom BaseBrokerClient
            if hasattr(self._exchange_client, "fetch_positions"):
                df = self._exchange_client.fetch_positions()
                if not df.empty:
                    return df.to_dict("records")
        except Exception as e:
            logger.warning(f"Fehler beim Abrufen von Positionen via fetch_positions(): {e}")

        # Fallback: Versuche positions-Attribut (z.B. PaperBroker)
        try:
            if hasattr(self._exchange_client, "positions"):
                positions_dict = self._exchange_client.positions
                if isinstance(positions_dict, dict):
                    return self._convert_positions_dict(positions_dict)
        except Exception as e:
            logger.warning(f"Fehler beim Abrufen von Positionen via positions-Attribut: {e}")

        # Keine Positionen gefunden
        logger.info("Keine Positionen vom Exchange-Client gefunden (leeres Portfolio)")
        return []

    def _convert_positions_dict(self, positions_dict: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Konvertiert positions-Dict (z.B. von PaperBroker) in Liste von Position-Dicts.

        Args:
            positions_dict: Dict {symbol -> {qty, avg_price, ...}}

        Returns:
            Liste von Position-Dicts
        """
        result: list[dict[str, Any]] = []
        for symbol, pos_data in positions_dict.items():
            qty = pos_data.get("qty", 0.0)
            if abs(qty) < 1e-10:  # Ignoriere flache Positionen
                continue

            side = "long" if qty > 0 else "short"
            avg_price = pos_data.get("avg_price", None)
            last_price = pos_data.get("last_price", None)
            realized_pnl = pos_data.get("realized_pnl", None)

            result.append({
                "symbol": symbol,
                "side": side,
                "size": abs(qty),
                "entry_price": avg_price,
                "mark_price": last_price,
                "realized_pnl": realized_pnl,
            })
        return result

    def _parse_position(self, pos_data: dict[str, Any]) -> LivePositionSnapshot | None:
        """
        Parst ein Position-Dict zu LivePositionSnapshot.

        Args:
            pos_data: Position-Dict mit keys wie symbol, side, size, etc.

        Returns:
            LivePositionSnapshot oder None bei Fehler
        """
        try:
            symbol = str(pos_data.get("symbol", ""))
            if not symbol:
                return None

            # Side bestimmen
            side = pos_data.get("side")
            raw_size = float(pos_data.get("size", pos_data.get("qty", 0.0)))

            if side is None or side not in ["long", "short", "flat"]:
                # Versuche aus size/qty abzuleiten
                if raw_size > 1e-10:
                    side = "long"
                elif raw_size < -1e-10:
                    side = "short"
                else:
                    side = "flat"

            size = abs(raw_size)

            # Preise
            entry_price = pos_data.get("entry_price", pos_data.get("avg_price"))
            if entry_price is not None:
                entry_price = float(entry_price)

            mark_price = pos_data.get("mark_price", pos_data.get("last_price", pos_data.get("current_price")))
            if mark_price is not None:
                mark_price = float(mark_price)

            # Notional berechnen
            notional = pos_data.get("notional", 0.0)
            if notional == 0.0 and mark_price is not None:
                notional = size * mark_price
            else:
                notional = float(notional) if notional else 0.0

            # PnL
            unrealized_pnl = pos_data.get("unrealized_pnl")
            if unrealized_pnl is not None:
                unrealized_pnl = float(unrealized_pnl)

            realized_pnl = pos_data.get("realized_pnl")
            if realized_pnl is not None:
                realized_pnl = float(realized_pnl)

            # Leverage
            leverage = pos_data.get("leverage")
            if leverage is not None:
                leverage = float(leverage)

            return LivePositionSnapshot(
                symbol=symbol,
                side=side,
                size=size,
                entry_price=entry_price,
                mark_price=mark_price,
                notional=notional,
                unrealized_pnl=unrealized_pnl,
                realized_pnl=realized_pnl,
                leverage=leverage,
            )
        except Exception as e:
            logger.warning(f"Fehler beim Parsen einer Position: {e}, data={pos_data}")
            return None

    def _fetch_account_data(self) -> dict[str, Any] | None:
        """
        Holt Account-Daten vom Exchange-Client (optional).

        Returns:
            Dict mit equity, cash, margin_used oder None
        """
        try:
            # Versuche fetch_balance() oder ähnliche Methode
            if hasattr(self._exchange_client, "fetch_balance"):
                balance = self._exchange_client.fetch_balance()
                if isinstance(balance, dict):
                    return {
                        "equity": balance.get("equity"),
                        "cash": balance.get("free", balance.get("cash")),
                        "margin_used": balance.get("used", balance.get("margin")),
                    }
        except Exception as e:
            logger.debug(f"Fehler beim Abrufen von Account-Daten: {e}")

        # Fallback: Versuche cash-Attribut (z.B. PaperBroker)
        try:
            if hasattr(self._exchange_client, "cash"):
                cash = self._exchange_client.cash
                if isinstance(cash, (int, float)):
                    return {"cash": float(cash)}
        except Exception as e:
            logger.debug(f"Fehler beim Abrufen von Cash via cash-Attribut: {e}")

        return None








