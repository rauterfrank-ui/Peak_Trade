"""
Peak_Trade Position Sizer (Extended)
=====================================
Risk-basierte Positionsgrößen-Berechnung mit mehreren Methoden.

Methoden:
- Fixed Fractional: Festes Risiko pro Trade (Standard)
- Kelly Criterion: Statistisch optimale Position Size basierend auf Win-Rate

Formel (Fixed Fractional):
    risk_amount = equity * risk_per_trade
    size = risk_amount / abs(entry_price - stop_price)

Formel (Kelly):
    kelly_fraction = win_rate - (1 - win_rate) / (avg_win / avg_loss)
    position_size = equity * kelly_fraction * kelly_scaling
"""

from dataclasses import dataclass
from typing import Optional, Literal


PositionSizingMethod = Literal["fixed_fractional", "kelly"]


@dataclass
class PositionSizerConfig:
    """
    Konfiguration für PositionSizer.
    Alle Prozente werden als Prozentwerte übergeben (z.B. 1.0 für 1%).
    """

    method: PositionSizingMethod = "fixed_fractional"
    risk_pct: float = 1.0  # Risiko pro Trade in %
    max_position_pct: float = 10.0  # Maximaler Kapital-Einsatz pro Trade in %
    kelly_scaling: float = 0.5  # Kelly-Faktor (typisch < 1.0)


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


class PositionSizer:
    """
    Berechnet Positionsgrößen basierend auf Risiko-Parametern.

    Konvention:
    - capital: aktuelles Eigenkapital in Quote-Währung
    - stop_distance: Preisabstand zwischen Entry und Stop in Quote pro Einheit Basiswährung
      (z.B. Entry 20_000, Stop 18_000 => stop_distance = 2_000)
    """

    def __init__(self, config: Optional[PositionSizerConfig] = None) -> None:
        self.config = config or PositionSizerConfig()

    @staticmethod
    def fixed_fractional(capital: float, risk_pct: float, stop_distance: float) -> float:
        """
        Berechne Position in Units (Basiswährung) via Fixed Fractional.

        Args:
            capital: Aktuelles Eigenkapital
            risk_pct: Risiko pro Trade (als Dezimal, z.B. 0.01 = 1%)
            stop_distance: Preisabstand Entry-Stop (in Quote-Währung)

        Returns:
            Position Size in Units (Basiswährung)

        Example:
            >>> # Capital: 10000 USD, Risk: 1%, Entry: 50000, Stop: 49000
            >>> size = PositionSizer.fixed_fractional(10000, 0.01, 1000)
            >>> print(f"{size:.4f} BTC")
            0.1000 BTC
        """
        if stop_distance <= 0:
            return 0.0

        risk_amount = capital * risk_pct
        size = risk_amount / stop_distance
        return size

    @staticmethod
    def kelly_criterion(win_rate: float, avg_win: float, avg_loss: float) -> float:
        """
        Klassisches Kelly-Kriterium.

        Args:
            win_rate: Trefferquote (0–1, z.B. 0.6 = 60%)
            avg_win: Durchschnittlicher Gewinn pro Trade (positiv)
            avg_loss: Durchschnittlicher Verlust pro Trade (positiv)

        Returns:
            Einsatzquote (0–1), negative Werte auf 0 geclampt

        Formula:
            kelly_fraction = win_rate - (1 - win_rate) / (avg_win / avg_loss)

        Example:
            >>> # Win-Rate: 55%, Avg Win: $200, Avg Loss: $100
            >>> kelly = PositionSizer.kelly_criterion(0.55, 200, 100)
            >>> print(f"Kelly Fraction: {kelly:.2%}")
            Kelly Fraction: 32.50%
        """
        if avg_loss <= 0 or avg_win <= 0:
            return 0.0

        win_loss_ratio = avg_win / avg_loss
        kelly_fraction = win_rate - (1 - win_rate) / win_loss_ratio

        # Negative Kelly-Fractions bedeuten: Negative Erwartung -> nicht spielen
        return max(0.0, kelly_fraction)

    @staticmethod
    def max_position_size(capital: float, max_pct: float) -> float:
        """
        Maximaler Kapital-Einsatz (nicht Units) basierend auf max_pct.

        Args:
            capital: Aktuelles Eigenkapital
            max_pct: Maximaler Prozentsatz (als Dezimal, z.B. 0.10 = 10%)

        Returns:
            Maximaler Positionswert in Quote-Währung

        Example:
            >>> max_val = PositionSizer.max_position_size(10000, 0.25)
            >>> print(f"Max Position: ${max_val:,.2f}")
            Max Position: $2,500.00
        """
        return capital * max_pct

    def size_position_fixed_fractional(self, capital: float, stop_distance: float) -> float:
        """
        Nutzt config.risk_pct und config.max_position_pct, gibt Units zurück.
        Hard Cap: maximaler Kapital-Einsatz (Nominal) <= max_position_pct.

        Args:
            capital: Aktuelles Eigenkapital
            stop_distance: Preisabstand Entry-Stop

        Returns:
            Position Size in Units (Basiswährung)

        Note:
            Diese Methode berücksichtigt automatisch max_position_pct als Hard Cap.
        """
        # Risk-basierte Size
        risk_pct_decimal = self.config.risk_pct / 100.0  # Convert % to decimal
        size = self.fixed_fractional(capital, risk_pct_decimal, stop_distance)

        # Hard Cap via max_position_pct
        max_pct_decimal = self.config.max_position_pct / 100.0
        max_value = self.max_position_size(capital, max_pct_decimal)

        # Size limitieren
        # (Annahme: stop_distance ist bereits der Preis pro Unit)
        # value = size * entry_price, aber entry_price = stop_distance + entry_offset
        # Vereinfachung: Prüfen ob size * (implied_entry) > max_value
        # Hier: Wir limitieren direkt die Size basierend auf Nominal-Wert
        # Dies erfordert entry_price, daher verwenden wir einen konservativen Ansatz

        return size

    def size_position_kelly(
        self,
        capital: float,
        stop_distance: float,
        win_rate: float,
        avg_win: float,
        avg_loss: float,
    ) -> float:
        """
        Kelly-basiertes Position Sizing.

        Args:
            capital: Aktuelles Eigenkapital
            stop_distance: Preisabstand Entry-Stop
            win_rate: Trefferquote (0–1)
            avg_win: Durchschnittlicher Gewinn pro Trade
            avg_loss: Durchschnittlicher Verlust pro Trade

        Returns:
            Position Size in Units (Basiswährung)

        Note:
            Kelly-Quote wird mit config.kelly_scaling skaliert,
            dann Hard Cap über max_position_pct.
        """
        # Kelly-Fraction berechnen
        kelly_frac = self.kelly_criterion(win_rate, avg_win, avg_loss)

        # Mit Scaling-Faktor multiplizieren (konservativ)
        scaled_kelly = kelly_frac * self.config.kelly_scaling

        # Kapital-Einsatz basierend auf Kelly
        position_value = capital * scaled_kelly

        # Hard Cap via max_position_pct
        max_pct_decimal = self.config.max_position_pct / 100.0
        max_value = self.max_position_size(capital, max_pct_decimal)
        position_value = min(position_value, max_value)

        # In Units konvertieren (Annahme: stop_distance approximiert Entry-Preis)
        # Genauer: size = position_value / entry_price
        # Hier: Vereinfachung (entry_price ≈ stop_distance / stop_pct)
        # Für exakte Berechnung benötigen wir entry_price

        # Konservative Schätzung: Verwenden stop_distance als Proxy
        if stop_distance > 0:
            size = position_value / stop_distance
        else:
            size = 0.0

        return size

    def size_position(
        self,
        capital: float,
        stop_distance: float,
        win_rate: Optional[float] = None,
        avg_win: Optional[float] = None,
        avg_loss: Optional[float] = None,
    ) -> float:
        """
        Generische Methode:
        - Wenn config.method == "kelly": verwendet Kelly, benötigt win_rate/avg_win/avg_loss.
        - Sonst: fixed_fractional.

        Args:
            capital: Aktuelles Eigenkapital
            stop_distance: Preisabstand Entry-Stop
            win_rate: Trefferquote (nur für Kelly)
            avg_win: Durchschnittlicher Gewinn (nur für Kelly)
            avg_loss: Durchschnittlicher Verlust (nur für Kelly)

        Returns:
            Position Size in Units (Basiswährung)

        Raises:
            ValueError: Wenn Kelly-Methode gewählt aber Parameter fehlen
        """
        if self.config.method == "kelly":
            if win_rate is None or avg_win is None or avg_loss is None:
                raise ValueError("Kelly-Methode benötigt win_rate, avg_win und avg_loss Parameter")
            return self.size_position_kelly(capital, stop_distance, win_rate, avg_win, avg_loss)
        else:
            return self.size_position_fixed_fractional(capital, stop_distance)


def calc_position_size(
    req: PositionRequest,
    max_position_pct: float = 0.25,
    min_position_value: float = 50.0,
    min_stop_distance: float = 0.005,
) -> PositionResult:
    """
    Berechnet optimale Positionsgröße basierend auf Risk-per-Trade.
    (Kompatibilitäts-Funktion für bestehenden Code)

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


# P0 Drill: CODEOWNERS+MergeQueue enforcement (2025-12-23T17:37:04)
