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

AUTH-005-style classification (Non-Authority / research safety closeout):
- CATEGORY=RESEARCH_STRATEGY_INTENT
- PRIMARY_ROLE=STRATEGY_INTENT (Long/Flat 0/1 only; no Short vocabulary)
- AUTHORITY=NON_AUTHORITY
- LIVE_READY=false · EXECUTION_ELIGIBLE=false · CANONICAL_BOUND=false
- PROXY_DATA_RISK=HIGH (OHLCV / optional size columns — not true tick/L2 microstructure)
- Does not own Master V2 / Double Play / Dynamic Scope / Agreement / Risk / Sizing
- Propagator / trade-sign config knobs are unused in the productive signal path

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
- OHLCV-Daten (1m/1h/1d) sind NICHT ausreichend (explicit OHLCV proxy)
- Implementierung erfordert erheblichen Research-Aufwand
- Invalid/insufficient inputs yield Flat (0) — no forward-fill or imputed books

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

    @staticmethod
    def _flat_signals(index: pd.Index, **attrs: Any) -> pd.Series:
        """Research-safe Neutral/Flat output (Long/Flat vocabulary only)."""
        signals = pd.Series(0, index=index, dtype=int)
        signals.attrs["is_research_stub"] = False
        for key, value in attrs.items():
            signals.attrs[key] = value
        return signals

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generiert deterministische 0/1-Signale (Research-Proxy).

        Priorität der Eingaben:
        1. ``bid_size`` + ``ask_size`` (wenn ``use_orderbook_imbalance``): Imbalance [-1, 1]
        2. ``open``, ``high``, ``low``, ``close``: Bar-Druck in [-1, 1]
        3. nur ``close``: Close > gleitendes Mittel über ``lookback_ticks`` Bars

        In (1) und (2) wird die rollende Mittelwert-Serie mit ``imbalance_threshold``
        verglichen; in (3) entsteht direkt 0/1 ohne dieselbe Schwelle.

        Research input contract:
        - Missing ``close`` → ``ValueError`` (existing fail-closed contract)
        - Empty frame → empty series
        - ``len < lookback_ticks`` / non-finite prices / negative or non-finite
          volume (when column present) / OHLC inconsistency / bad index → Flat
        - Zero-range candles remain division-safe (existing ``+1e-12`` / fillna path)
        - Output vocabulary is exclusively Long/Flat ``{0,1}`` (no Short)
        - Does not claim true order-book / tick microstructure

        Args:
            data: DataFrame mit mindestens Spalte ``close``

        Returns:
            ``pd.Series`` int 0/1, Index wie ``data``; ``attrs['is_research_stub'] == False``

        Raises:
            ValueError: Wenn ``close`` fehlt
        """
        if "close" not in data.columns:
            raise ValueError(f"Spalte 'close' nicht in DataFrame. Verfügbar: {list(data.columns)}")
        if len(data) == 0:
            empty = pd.Series([], dtype=int)
            empty.attrs["is_research_stub"] = False
            return empty

        lookback = int(self.cfg.lookback_ticks)
        if len(data) < lookback:
            return self._flat_signals(
                data.index,
                insufficient_history=True,
                lookback_effective=lookback,
            )

        if not data.index.is_unique or not data.index.is_monotonic_increasing:
            return self._flat_signals(
                data.index,
                invalid_input=True,
                invalid_reason="index_not_unique_or_not_monotonic_increasing",
                lookback_effective=lookback,
            )

        close = pd.to_numeric(data["close"], errors="coerce")
        close_arr = close.to_numpy(dtype=float, copy=False)
        if not np.isfinite(close_arr).all():
            return self._flat_signals(
                data.index,
                invalid_input=True,
                invalid_reason="non_finite_close",
                lookback_effective=lookback,
            )

        if "volume" in data.columns:
            volume = pd.to_numeric(data["volume"], errors="coerce")
            vol_arr = volume.to_numpy(dtype=float, copy=False)
            if (not np.isfinite(vol_arr).all()) or bool(np.any(vol_arr < 0.0)):
                return self._flat_signals(
                    data.index,
                    invalid_input=True,
                    invalid_reason="invalid_volume",
                    lookback_effective=lookback,
                )

        lb = max(1, min(lookback, len(data)))

        if (
            self.cfg.use_orderbook_imbalance
            and "bid_size" in data.columns
            and "ask_size" in data.columns
        ):
            b = pd.to_numeric(data["bid_size"], errors="coerce")
            a = pd.to_numeric(data["ask_size"], errors="coerce")
            b_arr = b.to_numpy(dtype=float, copy=False)
            a_arr = a.to_numpy(dtype=float, copy=False)
            if (not np.isfinite(b_arr).all()) or (not np.isfinite(a_arr).all()):
                return self._flat_signals(
                    data.index,
                    invalid_input=True,
                    invalid_reason="non_finite_bid_ask_size",
                    lookback_effective=lb,
                )
            denom = b + a
            raw = np.where(denom.to_numpy() > 1e-15, (b - a).to_numpy() / denom.to_numpy(), 0.0)
            pressure = pd.Series(raw, index=data.index)
            roll = pressure.rolling(window=lb, min_periods=1).mean()
            signals = (roll > float(self.cfg.imbalance_threshold)).astype(int)
        elif all(c in data.columns for c in ("open", "high", "low")):
            open_ = pd.to_numeric(data["open"], errors="coerce")
            high = pd.to_numeric(data["high"], errors="coerce")
            low = pd.to_numeric(data["low"], errors="coerce")
            ohlc = pd.concat([open_, high, low, close], axis=1)
            ohlc_arr = ohlc.to_numpy(dtype=float, copy=False)
            if not np.isfinite(ohlc_arr).all():
                return self._flat_signals(
                    data.index,
                    invalid_input=True,
                    invalid_reason="non_finite_ohlc",
                    lookback_effective=lb,
                )
            if bool(np.any(high.to_numpy(dtype=float) < low.to_numpy(dtype=float))):
                return self._flat_signals(
                    data.index,
                    invalid_input=True,
                    invalid_reason="high_lt_low",
                    lookback_effective=lb,
                )
            # Zero-range candles: replace 0 span with NaN then epsilon — no ZeroDivision
            hl = (high - low).replace(0, np.nan)
            pressure = ((close - open_) / (hl + 1e-12)).clip(-1.0, 1.0).fillna(0.0)
            roll = pressure.rolling(window=lb, min_periods=1).mean()
            signals = (roll > float(self.cfg.imbalance_threshold)).astype(int)
        else:
            rolling_mean = close.rolling(window=lb, min_periods=1).mean()
            signals = (close > rolling_mean).astype(int)

        signals.index = data.index
        signals.attrs["is_research_stub"] = False
        signals.attrs["lookback_effective"] = lb
        signals.attrs["proxy_data_risk"] = "HIGH"
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
