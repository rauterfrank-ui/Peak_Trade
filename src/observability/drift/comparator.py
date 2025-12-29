"""
Drift Comparator - WP1C (Phase 1 Shadow Trading)

Compares shadow trading signals/fills against backtest expectations.
"""

import logging
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class SignalEvent:
    """
    Signal event (buy/sell signal).

    Attributes:
        timestamp_ms: Event timestamp in milliseconds
        symbol: Symbol
        signal_type: Signal type ("BUY" or "SELL")
        quantity: Quantity signaled
        price: Price at signal
        metadata: Additional metadata
    """

    timestamp_ms: int
    symbol: str
    signal_type: str  # "BUY" | "SELL"
    quantity: Decimal
    price: Decimal
    metadata: Dict = field(default_factory=dict)


@dataclass
class DriftMetrics:
    """
    Drift metrics for comparing shadow vs backtest.

    Attributes:
        total_signals_shadow: Total signals from shadow
        total_signals_backtest: Total signals from backtest
        matched_signals: Signals that match (within tolerance)
        divergent_signals: Signals that diverge
        match_rate: Match rate (0.0 - 1.0)
        avg_price_divergence: Average price divergence (%)
        avg_quantity_divergence: Average quantity divergence (%)
        details: Additional details
    """

    total_signals_shadow: int = 0
    total_signals_backtest: int = 0
    matched_signals: int = 0
    divergent_signals: int = 0
    match_rate: float = 0.0
    avg_price_divergence: float = 0.0
    avg_quantity_divergence: float = 0.0
    details: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert to dict."""
        return {
            "total_signals_shadow": self.total_signals_shadow,
            "total_signals_backtest": self.total_signals_backtest,
            "matched_signals": self.matched_signals,
            "divergent_signals": self.divergent_signals,
            "match_rate": self.match_rate,
            "avg_price_divergence": self.avg_price_divergence,
            "avg_quantity_divergence": self.avg_quantity_divergence,
            "details": self.details,
        }


class DriftComparator:
    """
    Compares shadow trading against backtest expectations.

    Detects drift in:
    - Signal timing
    - Signal prices
    - Signal quantities
    - Fill execution

    Usage:
        >>> comparator = DriftComparator(price_tolerance_pct=1.0)
        >>> metrics = comparator.compare_signals(shadow_signals, backtest_signals)
        >>> if metrics.match_rate < 0.95:
        ...     alert("High drift detected!")
    """

    def __init__(
        self,
        price_tolerance_pct: float = 1.0,  # 1% price tolerance
        quantity_tolerance_pct: float = 5.0,  # 5% quantity tolerance
        time_tolerance_ms: int = 5000,  # 5 second time tolerance
    ):
        """
        Initialize drift comparator.

        Args:
            price_tolerance_pct: Price tolerance in percent
            quantity_tolerance_pct: Quantity tolerance in percent
            time_tolerance_ms: Time tolerance in milliseconds
        """
        self.price_tolerance_pct = price_tolerance_pct
        self.quantity_tolerance_pct = quantity_tolerance_pct
        self.time_tolerance_ms = time_tolerance_ms

    def compare_signals(
        self,
        shadow_signals: List[SignalEvent],
        backtest_signals: List[SignalEvent],
    ) -> DriftMetrics:
        """
        Compare shadow signals against backtest signals.

        Args:
            shadow_signals: Signals from shadow trading
            backtest_signals: Expected signals from backtest

        Returns:
            DriftMetrics
        """
        metrics = DriftMetrics(
            total_signals_shadow=len(shadow_signals),
            total_signals_backtest=len(backtest_signals),
        )

        # Build index of backtest signals for matching
        backtest_index = self._build_signal_index(backtest_signals)

        # Match shadow signals against backtest
        price_divergences = []
        quantity_divergences = []

        for shadow_signal in shadow_signals:
            match = self._find_matching_signal(shadow_signal, backtest_index)

            if match:
                metrics.matched_signals += 1

                # Calculate divergences
                price_div = self._calculate_price_divergence(
                    shadow_signal.price, match.price
                )
                qty_div = self._calculate_quantity_divergence(
                    shadow_signal.quantity, match.quantity
                )

                price_divergences.append(price_div)
                quantity_divergences.append(qty_div)
            else:
                metrics.divergent_signals += 1
                logger.debug(
                    f"Divergent signal: {shadow_signal.symbol} "
                    f"{shadow_signal.signal_type} @ {shadow_signal.timestamp_ms}"
                )

        # Calculate aggregate metrics
        if metrics.total_signals_shadow > 0:
            metrics.match_rate = (
                metrics.matched_signals / metrics.total_signals_shadow
            )

        if price_divergences:
            metrics.avg_price_divergence = sum(price_divergences) / len(
                price_divergences
            )

        if quantity_divergences:
            metrics.avg_quantity_divergence = sum(quantity_divergences) / len(
                quantity_divergences
            )

        # Additional details
        metrics.details = {
            "shadow_symbols": list(set(s.symbol for s in shadow_signals)),
            "backtest_symbols": list(set(s.symbol for s in backtest_signals)),
        }

        return metrics

    def _build_signal_index(
        self, signals: List[SignalEvent]
    ) -> Dict[str, List[SignalEvent]]:
        """
        Build index of signals by symbol.

        Args:
            signals: List of signals

        Returns:
            Dict mapping symbol to list of signals
        """
        index: Dict[str, List[SignalEvent]] = {}

        for signal in signals:
            if signal.symbol not in index:
                index[signal.symbol] = []
            index[signal.symbol].append(signal)

        return index

    def _find_matching_signal(
        self,
        shadow_signal: SignalEvent,
        backtest_index: Dict[str, List[SignalEvent]],
    ) -> Optional[SignalEvent]:
        """
        Find matching backtest signal for shadow signal.

        Args:
            shadow_signal: Shadow signal to match
            backtest_index: Index of backtest signals

        Returns:
            Matching signal or None
        """
        if shadow_signal.symbol not in backtest_index:
            return None

        candidates = backtest_index[shadow_signal.symbol]

        for candidate in candidates:
            # Check signal type match
            if candidate.signal_type != shadow_signal.signal_type:
                continue

            # Check time tolerance
            time_diff = abs(shadow_signal.timestamp_ms - candidate.timestamp_ms)
            if time_diff > self.time_tolerance_ms:
                continue

            # Check price tolerance
            price_div = self._calculate_price_divergence(
                shadow_signal.price, candidate.price
            )
            if abs(price_div) > self.price_tolerance_pct:
                continue

            # Check quantity tolerance
            qty_div = self._calculate_quantity_divergence(
                shadow_signal.quantity, candidate.quantity
            )
            if abs(qty_div) > self.quantity_tolerance_pct:
                continue

            # Match found
            return candidate

        return None

    def _calculate_price_divergence(
        self, shadow_price: Decimal, backtest_price: Decimal
    ) -> float:
        """
        Calculate price divergence in percent.

        Args:
            shadow_price: Shadow price
            backtest_price: Backtest price

        Returns:
            Divergence in percent
        """
        if backtest_price == 0:
            return 0.0

        return float((shadow_price - backtest_price) / backtest_price * 100)

    def _calculate_quantity_divergence(
        self, shadow_qty: Decimal, backtest_qty: Decimal
    ) -> float:
        """
        Calculate quantity divergence in percent.

        Args:
            shadow_qty: Shadow quantity
            backtest_qty: Backtest quantity

        Returns:
            Divergence in percent
        """
        if backtest_qty == 0:
            return 0.0

        return float((shadow_qty - backtest_qty) / backtest_qty * 100)
