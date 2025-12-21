# src/reporting/execution_reports.py
"""
Peak_Trade: Execution Reporting (Phase 16D)
===========================================

Bietet Datenstrukturen und Funktionen zur Auswertung von Order-/Execution-Daten
aus Backtests mit der ExecutionPipeline.

Hauptkomponenten:
- ExecutionStats: Aggregierte Kennzahlen fuer Execution-Daten
- from_execution_logs(): Erzeugt ExecutionStats aus Engine-Logs
- from_execution_results(): Erzeugt ExecutionStats aus OrderExecutionResult-Liste
- from_backtest_result(): Erzeugt ExecutionStats aus BacktestResult

WICHTIG: Paper-only. Alle Daten stammen aus simulierten Backtests.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Sequence, TYPE_CHECKING

if TYPE_CHECKING:
    from src.orders.base import OrderExecutionResult
    from src.backtest.result import BacktestResult


@dataclass
class ExecutionStats:
    """
    Aggregierte Statistiken fuer Execution-Daten aus Backtests.

    Attributes:
        n_orders: Gesamtzahl der Orders
        n_fills: Anzahl ausgefuehrter Orders (Fills)
        n_rejected: Anzahl abgelehnter Orders
        fill_rate: Anteil ausgefuehrter Orders (0.0 - 1.0)

        total_fees: Summe aller Fees (EUR)
        avg_fee_per_order: Durchschnittliche Fee pro Order
        avg_fee_per_fill: Durchschnittliche Fee pro Fill
        fee_rate_bps: Durchschnittliche Fee-Rate in Basispunkten

        total_notional: Gesamtes Handelsvolumen (Notional)
        avg_trade_notional: Durchschnittliches Notional pro Trade
        max_trade_notional: Maximales Notional eines einzelnen Trades
        min_trade_notional: Minimales Notional eines einzelnen Trades

        avg_slippage_bps: Durchschnittliche Slippage in Basispunkten
        max_slippage_bps: Maximale Slippage in Basispunkten
        total_slippage: Gesamte Slippage (absolut, EUR)

        n_buys: Anzahl Kauf-Orders
        n_sells: Anzahl Verkauf-Orders
        buy_volume: Kauf-Volumen (Notional)
        sell_volume: Verkauf-Volumen (Notional)

        avg_holding_period_hours: Durchschnittliche Haltedauer (Stunden)
        hit_rate: Anteil gewinnender Trades (falls PnL verfuegbar)
        n_winning_trades: Anzahl gewinnender Trades
        n_losing_trades: Anzahl verlierender Trades

        first_trade_time: Zeitpunkt des ersten Trades
        last_trade_time: Zeitpunkt des letzten Trades
        trading_period_days: Gesamte Handelsperiode in Tagen
    """

    # Order-Counts
    n_orders: int = 0
    n_fills: int = 0
    n_rejected: int = 0
    fill_rate: float = 0.0

    # Fees
    total_fees: float = 0.0
    avg_fee_per_order: float = 0.0
    avg_fee_per_fill: float = 0.0
    fee_rate_bps: float = 0.0

    # Notional / Volume
    total_notional: float = 0.0
    avg_trade_notional: float = 0.0
    max_trade_notional: float = 0.0
    min_trade_notional: float = 0.0

    # Slippage
    avg_slippage_bps: float = 0.0
    max_slippage_bps: float = 0.0
    total_slippage: float = 0.0

    # Buy/Sell Split
    n_buys: int = 0
    n_sells: int = 0
    buy_volume: float = 0.0
    sell_volume: float = 0.0

    # Holding Period & PnL
    avg_holding_period_hours: float = 0.0
    hit_rate: float = 0.0
    n_winning_trades: int = 0
    n_losing_trades: int = 0

    # Timestamps
    first_trade_time: Optional[datetime] = None
    last_trade_time: Optional[datetime] = None
    trading_period_days: float = 0.0

    # Metadata
    symbol: Optional[str] = None
    run_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Berechnet abgeleitete Metriken nach Initialisierung."""
        # Fill-Rate berechnen falls nicht gesetzt
        if self.n_orders > 0 and self.fill_rate == 0.0:
            self.fill_rate = self.n_fills / self.n_orders

        # Avg Fees berechnen
        if self.n_orders > 0 and self.avg_fee_per_order == 0.0:
            self.avg_fee_per_order = self.total_fees / self.n_orders
        if self.n_fills > 0 and self.avg_fee_per_fill == 0.0:
            self.avg_fee_per_fill = self.total_fees / self.n_fills

        # Fee-Rate in bps berechnen
        if self.total_notional > 0 and self.fee_rate_bps == 0.0:
            self.fee_rate_bps = (self.total_fees / self.total_notional) * 10_000

        # Trading Period berechnen
        if self.first_trade_time and self.last_trade_time:
            delta = self.last_trade_time - self.first_trade_time
            self.trading_period_days = delta.total_seconds() / (24 * 3600)

    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert ExecutionStats zu einem Dictionary."""
        return {
            "n_orders": self.n_orders,
            "n_fills": self.n_fills,
            "n_rejected": self.n_rejected,
            "fill_rate": self.fill_rate,
            "total_fees": self.total_fees,
            "avg_fee_per_order": self.avg_fee_per_order,
            "avg_fee_per_fill": self.avg_fee_per_fill,
            "fee_rate_bps": self.fee_rate_bps,
            "total_notional": self.total_notional,
            "avg_trade_notional": self.avg_trade_notional,
            "max_trade_notional": self.max_trade_notional,
            "min_trade_notional": self.min_trade_notional,
            "avg_slippage_bps": self.avg_slippage_bps,
            "max_slippage_bps": self.max_slippage_bps,
            "total_slippage": self.total_slippage,
            "n_buys": self.n_buys,
            "n_sells": self.n_sells,
            "buy_volume": self.buy_volume,
            "sell_volume": self.sell_volume,
            "avg_holding_period_hours": self.avg_holding_period_hours,
            "hit_rate": self.hit_rate,
            "n_winning_trades": self.n_winning_trades,
            "n_losing_trades": self.n_losing_trades,
            "first_trade_time": self.first_trade_time.isoformat()
            if self.first_trade_time
            else None,
            "last_trade_time": self.last_trade_time.isoformat() if self.last_trade_time else None,
            "trading_period_days": self.trading_period_days,
            "symbol": self.symbol,
            "run_id": self.run_id,
        }


def from_execution_logs(logs: List[Dict[str, Any]]) -> ExecutionStats:
    """
    Erzeugt ExecutionStats aus Execution-Logs der BacktestEngine.

    Die Logs stammen von BacktestEngine.get_execution_logs() und enthalten
    aggregierte Daten pro Run (z.B. total_orders, filled_orders, total_fees).

    Args:
        logs: Liste von Log-Dictionaries aus get_execution_logs()

    Returns:
        ExecutionStats mit aggregierten Metriken ueber alle Logs

    Example:
        >>> engine = BacktestEngine(use_execution_pipeline=True, log_executions=True)
        >>> result = engine.run_realistic(...)
        >>> logs = engine.get_execution_logs()
        >>> stats = from_execution_logs(logs)
        >>> print(f"Fill-Rate: {stats.fill_rate:.1%}")
    """
    if not logs:
        return ExecutionStats()

    # Aggregiere ueber alle Logs
    total_orders = 0
    total_fills = 0
    total_rejected = 0
    total_fees = 0.0
    total_notional = 0.0

    first_time: Optional[datetime] = None
    last_time: Optional[datetime] = None
    symbol: Optional[str] = None
    run_id: Optional[str] = None

    for log in logs:
        total_orders += log.get("total_orders", 0)
        total_fills += log.get("filled_orders", 0)
        total_rejected += log.get("rejected_orders", 0)
        total_fees += log.get("total_fees", 0.0)
        total_notional += log.get("total_notional", 0.0)

        # Symbol und Run-ID vom ersten Log nehmen
        if symbol is None:
            symbol = log.get("symbol")
        if run_id is None:
            run_id = log.get("run_id")

        # Timestamps parsen wenn vorhanden
        ts_str = log.get("timestamp")
        if ts_str:
            try:
                if isinstance(ts_str, str):
                    ts = datetime.fromisoformat(ts_str)
                else:
                    ts = ts_str
                if first_time is None or ts < first_time:
                    first_time = ts
                if last_time is None or ts > last_time:
                    last_time = ts
            except (ValueError, TypeError):
                pass

    # Fill-Rate berechnen
    fill_rate = total_fills / total_orders if total_orders > 0 else 0.0

    # Avg Notional
    avg_notional = total_notional / total_fills if total_fills > 0 else 0.0

    # Fee-Rate in bps
    fee_rate_bps = (total_fees / total_notional * 10_000) if total_notional > 0 else 0.0

    return ExecutionStats(
        n_orders=total_orders,
        n_fills=total_fills,
        n_rejected=total_rejected,
        fill_rate=fill_rate,
        total_fees=total_fees,
        avg_fee_per_order=total_fees / total_orders if total_orders > 0 else 0.0,
        avg_fee_per_fill=total_fees / total_fills if total_fills > 0 else 0.0,
        fee_rate_bps=fee_rate_bps,
        total_notional=total_notional,
        avg_trade_notional=avg_notional,
        symbol=symbol,
        run_id=run_id,
        first_trade_time=first_time,
        last_trade_time=last_time,
    )


def from_execution_results(
    results: Sequence["OrderExecutionResult"],
    reference_prices: Optional[Dict[str, float]] = None,
) -> ExecutionStats:
    """
    Erzeugt ExecutionStats aus einer Liste von OrderExecutionResult.

    Diese Funktion bietet detailliertere Auswertung als from_execution_logs(),
    da sie Zugriff auf die einzelnen Fills und deren Details hat.

    Args:
        results: Liste von OrderExecutionResult aus BacktestEngine.execution_results
        reference_prices: Optionale Referenzpreise fuer Slippage-Berechnung
                         (Dict[symbol, price]). Falls nicht angegeben, wird
                         der Request-Preis aus metadata verwendet (falls vorhanden).

    Returns:
        ExecutionStats mit detaillierten Metriken

    Example:
        >>> engine = BacktestEngine(use_execution_pipeline=True)
        >>> result = engine.run_realistic(...)
        >>> stats = from_execution_results(engine.execution_results)
        >>> print(f"Avg Slippage: {stats.avg_slippage_bps:.2f} bps")
    """
    if not results:
        return ExecutionStats()

    # Counters
    n_orders = len(results)
    n_fills = 0
    n_rejected = 0
    n_buys = 0
    n_sells = 0

    # Aggregates
    total_fees = 0.0
    total_notional = 0.0
    buy_volume = 0.0
    sell_volume = 0.0

    # Slippage tracking
    slippages_bps: List[float] = []
    total_slippage = 0.0

    # Notional tracking
    notionals: List[float] = []

    # Timestamps
    timestamps: List[datetime] = []

    # Symbol (nehme ersten gefundenen)
    symbol: Optional[str] = None

    for result in results:
        req = result.request
        if symbol is None:
            symbol = req.symbol

        if result.is_filled and result.fill:
            n_fills += 1
            fill = result.fill

            # Buy/Sell counts
            if fill.side == "buy":
                n_buys += 1
            else:
                n_sells += 1

            # Notional
            notional = fill.quantity * fill.price
            notionals.append(notional)
            total_notional += notional

            if fill.side == "buy":
                buy_volume += notional
            else:
                sell_volume += notional

            # Fees
            if fill.fee:
                total_fees += fill.fee

            # Timestamps
            if fill.timestamp:
                timestamps.append(fill.timestamp)

            # Slippage berechnen
            # Versuche Referenzpreis aus verschiedenen Quellen zu bekommen
            ref_price: Optional[float] = None

            # 1. Aus reference_prices Dict
            if reference_prices and req.symbol in reference_prices:
                ref_price = reference_prices[req.symbol]

            # 2. Aus Request metadata (signal_price)
            if ref_price is None:
                ref_price = req.metadata.get("signal_price")

            # 3. Aus Result metadata
            if ref_price is None:
                ref_price = result.metadata.get("reference_price")

            # Slippage in bps berechnen
            if ref_price and ref_price > 0:
                if fill.side == "buy":
                    # Bei Kauf: positiver Slippage = schlechter (hoeher bezahlt)
                    slip_bps = (fill.price - ref_price) / ref_price * 10_000
                else:
                    # Bei Verkauf: negativer Slippage = schlechter (niedriger verkauft)
                    slip_bps = (ref_price - fill.price) / ref_price * 10_000
                slippages_bps.append(slip_bps)
                total_slippage += abs(slip_bps * notional / 10_000)

        elif result.is_rejected:
            n_rejected += 1

    # Statistiken berechnen
    fill_rate = n_fills / n_orders if n_orders > 0 else 0.0
    avg_fee_per_order = total_fees / n_orders if n_orders > 0 else 0.0
    avg_fee_per_fill = total_fees / n_fills if n_fills > 0 else 0.0
    fee_rate_bps = (total_fees / total_notional * 10_000) if total_notional > 0 else 0.0

    avg_notional = sum(notionals) / len(notionals) if notionals else 0.0
    max_notional = max(notionals) if notionals else 0.0
    min_notional = min(notionals) if notionals else 0.0

    avg_slippage = sum(slippages_bps) / len(slippages_bps) if slippages_bps else 0.0
    max_slippage = max(slippages_bps) if slippages_bps else 0.0

    first_time = min(timestamps) if timestamps else None
    last_time = max(timestamps) if timestamps else None

    return ExecutionStats(
        n_orders=n_orders,
        n_fills=n_fills,
        n_rejected=n_rejected,
        fill_rate=fill_rate,
        total_fees=total_fees,
        avg_fee_per_order=avg_fee_per_order,
        avg_fee_per_fill=avg_fee_per_fill,
        fee_rate_bps=fee_rate_bps,
        total_notional=total_notional,
        avg_trade_notional=avg_notional,
        max_trade_notional=max_notional,
        min_trade_notional=min_notional,
        avg_slippage_bps=avg_slippage,
        max_slippage_bps=max_slippage,
        total_slippage=total_slippage,
        n_buys=n_buys,
        n_sells=n_sells,
        buy_volume=buy_volume,
        sell_volume=sell_volume,
        symbol=symbol,
        first_trade_time=first_time,
        last_trade_time=last_time,
    )


def from_backtest_result(
    result: "BacktestResult",
    execution_results: Optional[Sequence["OrderExecutionResult"]] = None,
) -> ExecutionStats:
    """
    Erzeugt ExecutionStats aus einem BacktestResult.

    Kombiniert Daten aus result.stats (Order-Layer Stats) mit optionalen
    detaillierten Execution-Results und Trade-Daten.

    Args:
        result: BacktestResult aus BacktestEngine.run_realistic()
        execution_results: Optionale Liste von OrderExecutionResult fuer
                          detaillierte Analyse. Falls nicht angegeben,
                          werden nur die aggregierten Stats verwendet.

    Returns:
        ExecutionStats mit kombinierten Metriken

    Example:
        >>> engine = BacktestEngine(use_execution_pipeline=True)
        >>> result = engine.run_realistic(...)
        >>> stats = from_backtest_result(result, engine.execution_results)
    """
    stats_dict = result.stats or {}
    metadata = result.metadata or {}

    # Basis-Stats aus result.stats
    n_orders = stats_dict.get("total_orders", 0)
    n_fills = stats_dict.get("filled_orders", 0)
    n_rejected = stats_dict.get("rejected_orders", 0)
    total_fees = stats_dict.get("total_fees", 0.0)
    total_notional = stats_dict.get("total_notional", 0.0)

    fill_rate = n_fills / n_orders if n_orders > 0 else 0.0

    # Trade-basierte Stats
    n_trades = stats_dict.get("total_trades", 0)
    win_rate = stats_dict.get("win_rate", 0.0)
    n_winning = int(n_trades * win_rate) if n_trades > 0 else 0
    n_losing = n_trades - n_winning

    # Wenn execution_results vorhanden, detailliertere Stats berechnen
    if execution_results:
        detailed_stats = from_execution_results(execution_results)
        # Uebernehme detaillierte Werte
        return ExecutionStats(
            n_orders=n_orders or detailed_stats.n_orders,
            n_fills=n_fills or detailed_stats.n_fills,
            n_rejected=n_rejected or detailed_stats.n_rejected,
            fill_rate=fill_rate or detailed_stats.fill_rate,
            total_fees=total_fees or detailed_stats.total_fees,
            avg_fee_per_order=detailed_stats.avg_fee_per_order,
            avg_fee_per_fill=detailed_stats.avg_fee_per_fill,
            fee_rate_bps=detailed_stats.fee_rate_bps,
            total_notional=total_notional or detailed_stats.total_notional,
            avg_trade_notional=detailed_stats.avg_trade_notional,
            max_trade_notional=detailed_stats.max_trade_notional,
            min_trade_notional=detailed_stats.min_trade_notional,
            avg_slippage_bps=detailed_stats.avg_slippage_bps,
            max_slippage_bps=detailed_stats.max_slippage_bps,
            total_slippage=detailed_stats.total_slippage,
            n_buys=detailed_stats.n_buys,
            n_sells=detailed_stats.n_sells,
            buy_volume=detailed_stats.buy_volume,
            sell_volume=detailed_stats.sell_volume,
            hit_rate=win_rate,
            n_winning_trades=n_winning,
            n_losing_trades=n_losing,
            symbol=metadata.get("symbol"),
            run_id=metadata.get("run_id"),
            first_trade_time=detailed_stats.first_trade_time,
            last_trade_time=detailed_stats.last_trade_time,
        )

    # Ohne execution_results: nur aggregierte Stats
    return ExecutionStats(
        n_orders=n_orders,
        n_fills=n_fills,
        n_rejected=n_rejected,
        fill_rate=fill_rate,
        total_fees=total_fees,
        avg_fee_per_order=total_fees / n_orders if n_orders > 0 else 0.0,
        avg_fee_per_fill=total_fees / n_fills if n_fills > 0 else 0.0,
        fee_rate_bps=(total_fees / total_notional * 10_000) if total_notional > 0 else 0.0,
        total_notional=total_notional,
        avg_trade_notional=total_notional / n_fills if n_fills > 0 else 0.0,
        hit_rate=win_rate,
        n_winning_trades=n_winning,
        n_losing_trades=n_losing,
        symbol=metadata.get("symbol"),
        run_id=metadata.get("run_id"),
    )


def format_execution_stats(
    stats: ExecutionStats,
    title: str = "Execution Statistics",
    include_slippage: bool = True,
    include_buy_sell: bool = True,
    include_timestamps: bool = False,
) -> str:
    """
    Formatiert ExecutionStats als lesbaren String fuer Konsolen-Output.

    Args:
        stats: ExecutionStats-Objekt
        title: Titel fuer den Output
        include_slippage: Slippage-Details einbeziehen
        include_buy_sell: Buy/Sell-Aufschluesselung einbeziehen
        include_timestamps: Zeitstempel einbeziehen

    Returns:
        Formatierter String

    Example:
        >>> stats = from_execution_logs(logs)
        >>> print(format_execution_stats(stats))
    """
    lines = [
        f"===== {title} =====",
        "",
        "[Orders & Fills]",
        f"  Orders:           {stats.n_orders:>8}",
        f"  Fills:            {stats.n_fills:>8}",
        f"  Rejected:         {stats.n_rejected:>8}",
        f"  Fill-Rate:        {stats.fill_rate:>8.1%}",
        "",
        "[Fees]",
        f"  Total Fees:       {stats.total_fees:>12.2f} EUR",
        f"  Avg Fee/Order:    {stats.avg_fee_per_order:>12.4f} EUR",
        f"  Avg Fee/Fill:     {stats.avg_fee_per_fill:>12.4f} EUR",
        f"  Fee-Rate:         {stats.fee_rate_bps:>12.2f} bps",
        "",
        "[Volume]",
        f"  Total Notional:   {stats.total_notional:>12.2f} EUR",
        f"  Avg Trade Size:   {stats.avg_trade_notional:>12.2f} EUR",
    ]

    if stats.max_trade_notional > 0:
        lines.append(f"  Max Trade Size:   {stats.max_trade_notional:>12.2f} EUR")
        lines.append(f"  Min Trade Size:   {stats.min_trade_notional:>12.2f} EUR")

    if include_slippage and (stats.avg_slippage_bps != 0 or stats.total_slippage > 0):
        lines.extend(
            [
                "",
                "[Slippage]",
                f"  Avg Slippage:     {stats.avg_slippage_bps:>12.2f} bps",
                f"  Max Slippage:     {stats.max_slippage_bps:>12.2f} bps",
                f"  Total Slippage:   {stats.total_slippage:>12.2f} EUR",
            ]
        )

    if include_buy_sell and (stats.n_buys > 0 or stats.n_sells > 0):
        lines.extend(
            [
                "",
                "[Buy/Sell Split]",
                f"  Buys:             {stats.n_buys:>8} ({stats.buy_volume:,.2f} EUR)",
                f"  Sells:            {stats.n_sells:>8} ({stats.sell_volume:,.2f} EUR)",
            ]
        )

    if stats.hit_rate > 0 or stats.n_winning_trades > 0:
        lines.extend(
            [
                "",
                "[Performance]",
                f"  Hit-Rate:         {stats.hit_rate:>8.1%}",
                f"  Winning Trades:   {stats.n_winning_trades:>8}",
                f"  Losing Trades:    {stats.n_losing_trades:>8}",
            ]
        )

    if include_timestamps and stats.first_trade_time:
        lines.extend(
            [
                "",
                "[Timestamps]",
                f"  First Trade:      {stats.first_trade_time}",
                f"  Last Trade:       {stats.last_trade_time}",
                f"  Trading Period:   {stats.trading_period_days:.1f} days",
            ]
        )

    if stats.symbol:
        lines.extend(
            [
                "",
                f"[Symbol: {stats.symbol}]",
            ]
        )

    if stats.run_id:
        lines.append(f"[Run-ID: {stats.run_id}]")

    lines.append("")

    return "\n".join(lines)
