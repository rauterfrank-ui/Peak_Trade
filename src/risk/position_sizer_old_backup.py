"""
Peak_Trade Position Sizer
==========================
Risk-basierte Positionsgrößen-Berechnung.

Formel:
    risk_amount = equity * risk_per_trade
    size = risk_amount / abs(entry_price - stop_price)
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class PositionRequest:
    """Anfrage für Position-Sizing-Berechnung."""

    equity: float  # Aktuelles Kontovermögen
    entry_price: float  # Geplanter Entry-Preis
    stop_price: float  # Stop-Loss-Preis
    risk_per_trade: float  # z.B. 0.01 = 1%


@dataclass
class PositionResult:
    """Ergebnis der Position-Sizing-Berechnung."""

    size: float  # Anzahl Units (z.B. BTC)
    value: float  # Positionswert in USD
    risk_amount: float  # Risikobetrag in USD
    risk_percent: float  # Risiko in %
    stop_distance_percent: float  # Stop-Distanz in %
    rejected: bool = False
    reason: str = ""


def calc_position_size(
    req: PositionRequest,
    max_position_pct: float = 0.25,
    min_position_value: float = 50.0,
    min_stop_distance: float = 0.005,
) -> PositionResult:
    """
    Berechnet optimale Positionsgröße basierend auf Risk-per-Trade.

    Args:
        req: PositionRequest mit equity, entry, stop, risk
        max_position_pct: Max. Positionsgröße (% des Kontos)
        min_position_value: Min. Positionswert in USD
        min_stop_distance: Min. Stop-Distanz (%)

    Returns:
        PositionResult mit size, value, risk, oder rejected=True

    Validierungen:
        - Stop muss unter Entry liegen (Long)
        - Stop-Distanz >= min_stop_distance
        - Position <= max_position_pct
        - Position >= min_position_value

    Example:
        >>> req = PositionRequest(
        ...     equity=10000,
        ...     entry_price=50000,
        ...     stop_price=49000,
        ...     risk_per_trade=0.01
        ... )
        >>> result = calc_position_size(req)
        >>> print(f"Size: {result.size:.4f} BTC")
        Size: 0.1000 BTC
    """
    # 1. Validierung: Stop unter Entry
    if req.stop_price >= req.entry_price:
        return PositionResult(
            size=0,
            value=0,
            risk_amount=0,
            risk_percent=0,
            stop_distance_percent=0,
            rejected=True,
            reason="Stop-Loss muss unter Entry liegen (Long)",
        )

    # 2. Stop-Distanz berechnen
    stop_distance = abs(req.entry_price - req.stop_price)
    stop_distance_pct = stop_distance / req.entry_price

    if stop_distance_pct < min_stop_distance:
        return PositionResult(
            size=0,
            value=0,
            risk_amount=0,
            risk_percent=0,
            stop_distance_percent=stop_distance_pct,
            rejected=True,
            reason=f"Stop-Distanz {stop_distance_pct:.2%} < {min_stop_distance:.2%}",
        )

    # 3. Risk-Amount berechnen
    risk_amount = req.equity * req.risk_per_trade

    # 4. Position Size berechnen
    size = risk_amount / stop_distance
    value = size * req.entry_price

    # 5. Validierung: Position zu groß?
    max_value = req.equity * max_position_pct
    if value > max_value:
        return PositionResult(
            size=0,
            value=value,
            risk_amount=risk_amount,
            risk_percent=req.risk_per_trade,
            stop_distance_percent=stop_distance_pct,
            rejected=True,
            reason=f"Position {value:.2f} USD > {max_position_pct:.0%} Limit ({max_value:.2f} USD)",
        )

    # 6. Validierung: Position zu klein?
    if value < min_position_value:
        return PositionResult(
            size=0,
            value=value,
            risk_amount=risk_amount,
            risk_percent=req.risk_per_trade,
            stop_distance_percent=stop_distance_pct,
            rejected=True,
            reason=f"Position {value:.2f} USD < Min {min_position_value:.2f} USD",
        )

    # 7. Alles OK!
    return PositionResult(
        size=size,
        value=value,
        risk_amount=risk_amount,
        risk_percent=req.risk_per_trade,
        stop_distance_percent=stop_distance_pct,
        rejected=False,
        reason="OK",
    )
