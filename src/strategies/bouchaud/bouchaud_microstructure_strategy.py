# src/strategies/bouchaud/bouchaud_microstructure_strategy.py
"""
Bouchaud Microstructure Strategy – Research-Only (OHLCV-Proxy)
===============================================================

Research-Strategie inspiriert von Jean-Philippe Bouchauds Markt-Mikrostruktur;
`generate_signals` liefert deterministische 0/1-Signale aus OHLCV (Proxy) oder
optional aus Bid/Ask-Größen, sobald diese Spalten vorhanden sind.

⚠️ RESEARCH-ONLY – NICHT FÜR LIVE-TRADING FREIGEGEBEN ⚠️
Echte Tick-/L2-Logik ist hier nicht abgebildet; die Signale dienen Pipeline-
 und Backtest-Tests mit Standard-OHLCV.

Diese Strategie ist ausschließlich für:
- Offline-Backtests und Research-Pipelines
- Akademische Experimente

Hintergrund (Bouchaud Microstructure-Konzepte):
- Orderbuch-Imbalance: Verhältnis von Bid/Ask-Volumen als Preisdruckindikator
- Trade-Signs: Kauf-/Verkaufssignale aus Trades (Lee-Ready etc.)
- Propagator-Modelle: Wie Trades den Preis beeinflussen
- Metaorder-Splitting: Erkennung institutioneller Orderflows

Voraussetzungen für echte Implementierung:
- Tick-by-Tick Marktdaten (Trades + Quotes)
- Orderbuch-Snapshots (L2/L3 Daten)
- Niedrige Latenz für sinnvolle Signale

Warnung:
- Diese Strategie ergibt nur Sinn mit Hochfrequenz-/Tick-Daten
- OHLCV-Daten (1m/1h/1d) sind NICHT ausreichend
- Implementierung erfordert erheblichen Research-Aufwand

Referenzen:
- "Trades, Quotes and Prices" (Bouchaud, Bonart, Donier, Gould)
- "Price Impact" (Bouchaud et al.)
- "More Statistical Properties of Order Books" (Bouchaud et al.)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd

from ..base import BaseStrategy, StrategyMetadata


# =============================================================================
# CONFIG
# =============================================================================


@dataclass
class BouchaudMicrostructureConfig:
    """
    Konfiguration für Bouchaud Microstructure Strategy.

    Hinweis: Diese Felder sind Platzhalter für zukünftige Implementierung.
    Die Strategie benötigt Tick-/Orderbuch-Daten, die in Peak_Trade
    aktuell nicht standardmäßig verfügbar sind.

    Attributes:
        use_orderbook_imbalance: Nutze Orderbuch-Imbalance als Feature
        use_trade_signs: Nutze Trade-Sign-Korrelationen
        lookback_ticks: Anzahl historischer Ticks für Berechnung
        min_liquidity_filter: Minimale Liquidität (Bid+Ask Volume)
        imbalance_threshold: Schwelle für Imbalance-Signal
        propagator_decay: Decay-Parameter für Propagator-Modell
    """

    use_orderbook_imbalance: bool = True
    use_trade_signs: bool = True
    lookback_ticks: int = 100
    min_liquidity_filter: float = 1000.0
    imbalance_threshold: float = 0.3
    propagator_decay: float = 0.5

    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert Config zu Dictionary."""
        return {
            "use_orderbook_imbalance": self.use_orderbook_imbalance,
            "use_trade_signs": self.use_trade_signs,
            "lookback_ticks": self.lookback_ticks,
            "min_liquidity_filter": self.min_liquidity_filter,
            "imbalance_threshold": self.imbalance_threshold,
            "propagator_decay": self.propagator_decay,
        }


# =============================================================================
# STRATEGY
# =============================================================================


class BouchaudMicrostructureStrategy(BaseStrategy):
    """
    Bouchaud Microstructure Strategy – Research-Only mit OHLCV-/Proxy-Signalen.

    ⚠️ RESEARCH-ONLY – NICHT FÜR LIVE-TRADING FREIGEGEBEN ⚠️

    `generate_signals` ist bewusst simpel und deterministisch:
    - Mit ``bid_size``/``ask_size``: rollende Orderbuch-Imbalance vs. Schwelle
    - Mit OHLC: Bar-Druck ``(close-open)/(high-low)`` (Proxy), rollend vs. Schwelle
    - Nur ``close``: Close vs. gleitendem Mittel (Lookback ``lookback_ticks``)

    Vollständige Tick-/L3-Logik bleibt späterer Research vorbehalten.

    Attributes:
        cfg: BouchaudMicrostructureConfig mit Strategie-Parametern

    Example:
        >>> strategy = BouchaudMicrostructureStrategy()
        >>> signals = strategy.generate_signals(df)  # pd.Series 0/1
    """

    KEY = "bouchaud_microstructure"

    # Research-only Konstanten
    IS_LIVE_READY = False
    ALLOWED_ENVIRONMENTS = ["offline_backtest", "research"]
    TIER = "r_and_d"

    def __init__(
        self,
        use_orderbook_imbalance: bool = True,
        use_trade_signs: bool = True,
        lookback_ticks: int = 100,
        min_liquidity_filter: float = 1000.0,
        imbalance_threshold: float = 0.3,
        propagator_decay: float = 0.5,
        config: Optional[Dict[str, Any]] = None,
        metadata: Optional[StrategyMetadata] = None,
    ) -> None:
        """
        Initialisiert Bouchaud Microstructure Strategy.

        Args:
            use_orderbook_imbalance: Nutze Orderbuch-Imbalance
            use_trade_signs: Nutze Trade-Sign-Korrelationen
            lookback_ticks: Anzahl historischer Ticks
            min_liquidity_filter: Minimale Liquiditätsschwelle
            imbalance_threshold: Schwelle für Imbalance-Signal
            propagator_decay: Decay-Parameter für Propagator
            config: Optional Config-Dict
            metadata: Optional StrategyMetadata
        """
        # Config zusammenbauen
        initial_config = {
            "use_orderbook_imbalance": use_orderbook_imbalance,
            "use_trade_signs": use_trade_signs,
            "lookback_ticks": lookback_ticks,
            "min_liquidity_filter": min_liquidity_filter,
            "imbalance_threshold": imbalance_threshold,
            "propagator_decay": propagator_decay,
        }

        if config:
            initial_config.update(config)

        # Research-only Metadata
        if metadata is None:
            metadata = StrategyMetadata(
                name="Bouchaud Microstructure v0 (Research)",
                description=(
                    "Microstructure-Strategie basierend auf Bouchauds Arbeiten. "
                    "⚠️ RESEARCH-ONLY – Signale sind OHLCV-/Proxy-Logik, keine Live-Freigabe. "
                    "Echte Tick-/L2-Features können später ergänzt werden."
                ),
                version="0.1.0-ohlcv-proxy",
                author="Peak_Trade Research",
                regime="microstructure",
                tags=["research", "bouchaud", "microstructure", "orderbook", "tick_data"],
            )

        super().__init__(config=initial_config, metadata=metadata)

        # Config-Objekt erstellen
        self.cfg = BouchaudMicrostructureConfig(
            use_orderbook_imbalance=self.config.get(
                "use_orderbook_imbalance", use_orderbook_imbalance
            ),
            use_trade_signs=self.config.get("use_trade_signs", use_trade_signs),
            lookback_ticks=self.config.get("lookback_ticks", lookback_ticks),
            min_liquidity_filter=self.config.get("min_liquidity_filter", min_liquidity_filter),
            imbalance_threshold=self.config.get("imbalance_threshold", imbalance_threshold),
            propagator_decay=self.config.get("propagator_decay", propagator_decay),
        )

    @classmethod
    def from_config(
        cls,
        cfg: Any,
        section: str = "strategy.bouchaud_microstructure",
    ) -> "BouchaudMicrostructureStrategy":
        """
        Fabrikmethode für Config-basierte Instanziierung.

        Args:
            cfg: Config-Objekt (PeakConfig)
            section: Dotted-Path zum Config-Abschnitt

        Returns:
            BouchaudMicrostructureStrategy-Instanz
        """
        return cls(
            use_orderbook_imbalance=cfg.get(f"{section}.use_orderbook_imbalance", True),
            use_trade_signs=cfg.get(f"{section}.use_trade_signs", True),
            lookback_ticks=cfg.get(f"{section}.lookback_ticks", 100),
            min_liquidity_filter=cfg.get(f"{section}.min_liquidity_filter", 1000.0),
            imbalance_threshold=cfg.get(f"{section}.imbalance_threshold", 0.3),
            propagator_decay=cfg.get(f"{section}.propagator_decay", 0.5),
        )

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generiert deterministische 0/1-Signale (Research-Proxy).

        Priorität der Eingaben:
        1. ``bid_size`` + ``ask_size`` (wenn ``use_orderbook_imbalance``): Imbalance [-1, 1]
        2. ``open``, ``high``, ``low``, ``close``: Bar-Druck in [-1, 1]
        3. nur ``close``: Close > gleitendes Mittel über ``lookback_ticks`` Bars

        In (1) und (2) wird die rollende Mittelwert-Serie mit ``imbalance_threshold``
        verglichen; in (3) entsteht direkt 0/1 ohne dieselbe Schwelle.

        Args:
            data: DataFrame mit mindestens Spalte ``close``

        Returns:
            ``pd.Series`` int 0/1, Index wie ``data``; ``attrs['is_research_stub'] == False``

        Raises:
            ValueError: Wenn ``close`` fehlt
        """
        if "close" not in data.columns:
            raise ValueError(
                f"Spalte 'close' nicht in DataFrame. Verfügbar: {list(data.columns)}"
            )
        if len(data) == 0:
            empty = pd.Series([], dtype=int)
            empty.attrs["is_research_stub"] = False
            return empty

        lb = max(1, min(int(self.cfg.lookback_ticks), len(data)))

        if (
            self.cfg.use_orderbook_imbalance
            and "bid_size" in data.columns
            and "ask_size" in data.columns
        ):
            b = data["bid_size"].astype(float)
            a = data["ask_size"].astype(float)
            denom = b + a
            raw = np.where(denom.to_numpy() > 1e-15, (b - a).to_numpy() / denom.to_numpy(), 0.0)
            pressure = pd.Series(raw, index=data.index)
            roll = pressure.rolling(window=lb, min_periods=1).mean()
            signals = (roll > float(self.cfg.imbalance_threshold)).astype(int)
        elif all(c in data.columns for c in ("open", "high", "low")):
            hl = (data["high"] - data["low"]).replace(0, np.nan)
            pressure = (
                ((data["close"] - data["open"]) / (hl + 1e-12)).clip(-1.0, 1.0).fillna(0.0)
            )
            roll = pressure.rolling(window=lb, min_periods=1).mean()
            signals = (roll > float(self.cfg.imbalance_threshold)).astype(int)
        else:
            close = data["close"].astype(float)
            rolling_mean = close.rolling(window=lb, min_periods=1).mean()
            signals = (close > rolling_mean).astype(int)

        signals.index = data.index
        signals.attrs["is_research_stub"] = False
        signals.attrs["lookback_effective"] = lb
        return signals

    def validate(self) -> None:
        """Validiert Parameter."""
        if self.cfg.lookback_ticks < 1:
            raise ValueError(f"lookback_ticks ({self.cfg.lookback_ticks}) muss >= 1 sein")
        if self.cfg.min_liquidity_filter < 0:
            raise ValueError(
                f"min_liquidity_filter ({self.cfg.min_liquidity_filter}) muss >= 0 sein"
            )
        if not -1 <= self.cfg.imbalance_threshold <= 1:
            raise ValueError(
                f"imbalance_threshold ({self.cfg.imbalance_threshold}) muss zwischen -1 und 1 sein"
            )

    def __repr__(self) -> str:
        return (
            f"<BouchaudMicrostructureStrategy("
            f"orderbook={self.cfg.use_orderbook_imbalance}, "
            f"trades={self.cfg.use_trade_signs}, "
            f"lookback={self.cfg.lookback_ticks}ticks) "
            f"[research OHLCV proxy]>"
        )
