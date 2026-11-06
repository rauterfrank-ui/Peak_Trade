# src/strategies/gatheral_cont/vol_regime_overlay_strategy.py
"""
Vol Regime Overlay Strategy – Research-Only (OHLCV Vol-Regime-Proxy)
====================================================================

Research-Strategie inspiriert von Jim Gatheral und Rama Cont: deterministische
0/1-Signale aus realized Volatility (Close-Returns) und rollierenden Quantilen
— kein Rough-Vol- oder Hurst-Schätzer, sondern ein schlanker Pipeline-Slice.

⚠️ RESEARCH-ONLY – NICHT FÜR LIVE-TRADING FREIGEGEBEN ⚠️

Geeignet für:
- Offline-Backtests und Research-Pipelines
- Akademische Experimente mit Vol-/Regime-Labels

Hintergrund (Gatheral & Cont Konzepte):

Gatheral – Volatilitätsmodellierung:
- SVI (Stochastic Volatility Inspired) Parametrisierung
- Rough Volatility: Hurst-Exponent H ≈ 0.1 für realized vol
- Vol-of-Vol-Dynamik und Mean-Reversion

Cont – Marktdynamik:
- Stilisierte Fakten von Asset-Returns
- Fat Tails, Volatility Clustering
- Regime-Switching in Finanzmärkten

Anwendung als Meta-Layer:
- Diese Strategie erzeugt KEINE eigenen Entry/Exit-Signale
- Sie fungiert als Filter/Scaler für bestehende Strategien
- Beispiel: Position-Sizing basierend auf Vol-Regime
- Beispiel: Strategy-Switching bei Regime-Wechsel

Warnung:
- Rough-Vol-Kalibrierung ist rechenintensiv
- Regime-Detection hat inherente Verzögerung
- Nur für explorative Research-Analysen verwenden

Referenzen:
- "The Volatility Surface" (Gatheral)
- "Volatility is Rough" (Gatheral et al.)
- "Empirical Properties of Asset Returns" (Cont)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

import pandas as pd

from ..base import BaseStrategy, StrategyMetadata


# =============================================================================
# CONFIG
# =============================================================================


@dataclass
class VolRegimeOverlayConfig:
    """
    Konfiguration für Vol Regime Overlay Strategy.

    Diese Config definiert Parameter für ein Volatilitäts-Budget-
    und Regime-Overlay-System nach Gatheral & Cont.

    Attributes:
        day_vol_budget: Tägliches Volatilitäts-Budget (z.B. 0.02 = 2% Tages-Vol)
        max_intraday_dd: Maximaler Intraday-Drawdown bevor Positionen reduziert werden
        regime_lookback_bars: Anzahl Bars für Regime-Bestimmung
        high_vol_threshold: Schwelle für High-Vol-Regime (Percentile)
        low_vol_threshold: Schwelle für Low-Vol-Regime (Percentile)
        use_rough_vol: Ob Rough-Vol-Schätzer verwendet wird (rechenintensiv)
        hurst_lookback: Lookback für Hurst-Exponent-Schätzung
        vol_target_scaling: Ob Vol-Target-Scaling aktiviert ist
    """

    day_vol_budget: float = 0.02
    max_intraday_dd: float = 0.01
    regime_lookback_bars: int = 100
    high_vol_threshold: float = 0.75
    low_vol_threshold: float = 0.25
    use_rough_vol: bool = False
    hurst_lookback: int = 252
    vol_target_scaling: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert Config zu Dictionary."""
        return {
            "day_vol_budget": self.day_vol_budget,
            "max_intraday_dd": self.max_intraday_dd,
            "regime_lookback_bars": self.regime_lookback_bars,
            "high_vol_threshold": self.high_vol_threshold,
            "low_vol_threshold": self.low_vol_threshold,
            "use_rough_vol": self.use_rough_vol,
            "hurst_lookback": self.hurst_lookback,
            "vol_target_scaling": self.vol_target_scaling,
        }


# =============================================================================
# STRATEGY
# =============================================================================


class VolRegimeOverlayStrategy(BaseStrategy):
    """
    Vol Regime Overlay Strategy – Research-Only mit OHLCV-Vol-Regime-Proxy.

    ⚠️ RESEARCH-ONLY – NICHT FÜR LIVE-TRADING FREIGEGEBEN ⚠️

    ``generate_signals`` liefert 0/1: **1** = Vol nicht über dem rollierenden
    High-Vol-Quantil (Research-„Risk-on“-Proxy), **0** = darüber oder bei
    Drawdown-Breach (optional). Regime-Labels: ``low_vol`` / ``normal`` /
    ``high_vol`` relativ zu denselben Quantilen.

    Vollständige Rough-Vol-/Meta-Layer-Integration bleibt späterer Research
    vorbehalten.

    Attributes:
        cfg: VolRegimeOverlayConfig mit Strategie-Parametern

    Example:
        >>> strategy = VolRegimeOverlayStrategy()
        >>> signals = strategy.generate_signals(df)  # pd.Series int 0/1
    """

    KEY = "vol_regime_overlay"

    # Research-only Konstanten
    IS_LIVE_READY = False
    ALLOWED_ENVIRONMENTS = ["offline_backtest", "research"]
    TIER = "r_and_d"

    def __init__(
        self,
        day_vol_budget: float = 0.02,
        max_intraday_dd: float = 0.01,
        regime_lookback_bars: int = 100,
        high_vol_threshold: float = 0.75,
        low_vol_threshold: float = 0.25,
        use_rough_vol: bool = False,
        hurst_lookback: int = 252,
        vol_target_scaling: bool = True,
        config: Optional[Dict[str, Any]] = None,
        metadata: Optional[StrategyMetadata] = None,
    ) -> None:
        """
        Initialisiert Vol Regime Overlay Strategy.

        Args:
            day_vol_budget: Tägliches Vol-Budget (z.B. 0.02 = 2%)
            max_intraday_dd: Maximaler Intraday-Drawdown
            regime_lookback_bars: Lookback für Regime-Bestimmung
            high_vol_threshold: Schwelle für High-Vol-Regime
            low_vol_threshold: Schwelle für Low-Vol-Regime
            use_rough_vol: Ob Rough-Vol-Schätzer verwendet wird
            hurst_lookback: Lookback für Hurst-Exponent
            vol_target_scaling: Ob Vol-Target-Scaling aktiv
            config: Optional Config-Dict
            metadata: Optional StrategyMetadata
        """
        # Config zusammenbauen
        initial_config = {
            "day_vol_budget": day_vol_budget,
            "max_intraday_dd": max_intraday_dd,
            "regime_lookback_bars": regime_lookback_bars,
            "high_vol_threshold": high_vol_threshold,
            "low_vol_threshold": low_vol_threshold,
            "use_rough_vol": use_rough_vol,
            "hurst_lookback": hurst_lookback,
            "vol_target_scaling": vol_target_scaling,
        }

        if config:
            initial_config.update(config)

        # Research-only Metadata
        if metadata is None:
            metadata = StrategyMetadata(
                name="Vol Regime Overlay v0 (Gatheral & Cont, Research)",
                description=(
                    "Vol-/Regime-Layer basierend auf Gatheral & Cont. "
                    "⚠️ RESEARCH-ONLY – Signale sind OHLCV realized-vol/Quantil-Proxy, "
                    "keine Live-Freigabe. Meta-Sizing mit bestehenden Strategien optional."
                ),
                version="0.1.0-ohlcv-proxy",
                author="Peak_Trade Research",
                regime="meta_risk_layer",
                tags=["research", "gatheral", "cont", "rough_vol", "regime", "meta_layer"],
            )

        super().__init__(config=initial_config, metadata=metadata)

        # Config-Objekt erstellen
        self.cfg = VolRegimeOverlayConfig(
            day_vol_budget=self.config.get("day_vol_budget", day_vol_budget),
            max_intraday_dd=self.config.get("max_intraday_dd", max_intraday_dd),
            regime_lookback_bars=self.config.get("regime_lookback_bars", regime_lookback_bars),
            high_vol_threshold=self.config.get("high_vol_threshold", high_vol_threshold),
            low_vol_threshold=self.config.get("low_vol_threshold", low_vol_threshold),
            use_rough_vol=self.config.get("use_rough_vol", use_rough_vol),
            hurst_lookback=self.config.get("hurst_lookback", hurst_lookback),
            vol_target_scaling=self.config.get("vol_target_scaling", vol_target_scaling),
        )

    @classmethod
    def from_config(
        cls,
        cfg: Any,
        section: str = "strategy.vol_regime_overlay",
    ) -> "VolRegimeOverlayStrategy":
        """
        Fabrikmethode für Config-basierte Instanziierung.

        Args:
            cfg: Config-Objekt (PeakConfig)
            section: Dotted-Path zum Config-Abschnitt

        Returns:
            VolRegimeOverlayStrategy-Instanz
        """
        return cls(
            day_vol_budget=cfg.get(f"{section}.day_vol_budget", 0.02),
            max_intraday_dd=cfg.get(f"{section}.max_intraday_dd", 0.01),
            regime_lookback_bars=cfg.get(f"{section}.regime_lookback_bars", 100),
            high_vol_threshold=cfg.get(f"{section}.high_vol_threshold", 0.75),
            low_vol_threshold=cfg.get(f"{section}.low_vol_threshold", 0.25),
            use_rough_vol=cfg.get(f"{section}.use_rough_vol", False),
            hurst_lookback=cfg.get(f"{section}.hurst_lookback", 252),
            vol_target_scaling=cfg.get(f"{section}.vol_target_scaling", True),
        )

    def _rolling_lookback(self, n: int) -> int:
        """Effektives Lookback-Fenster (mindestens 10 Bars, wie validate)."""
        cap = self.cfg.hurst_lookback if self.cfg.use_rough_vol else self.cfg.regime_lookback_bars
        return max(10, min(int(cap), n))

    def _realized_vol_and_quantiles(
        self, close: pd.Series
    ) -> tuple[pd.Series, pd.Series, pd.Series, int]:
        """Rolling std der Returns plus rollierende Quantile von rv."""
        n = len(close)
        lb = self._rolling_lookback(n)
        rets = close.astype(float).pct_change()
        rv = rets.rolling(window=lb, min_periods=10).std()
        low_q = rv.rolling(window=lb, min_periods=10).quantile(self.cfg.low_vol_threshold)
        high_q = rv.rolling(window=lb, min_periods=10).quantile(self.cfg.high_vol_threshold)
        return rv, low_q, high_q, lb

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generiert deterministische 0/1-Signale (Research Vol-Regime-Proxy).

        Logik:
        - Realized Vol = rollierende Std der Close-Returns.
        - **0**, wenn ``rv`` über dem rollierenden ``high_vol_threshold``-Quantil liegt
          (hohe Vol relativ zur Historie), sonst **1**.
        - Zusätzlich **0**, wenn Drawdown vom laufenden Hoch ``> max_intraday_dd``.

        Args:
            data: DataFrame mit Spalte ``close``

        Returns:
            ``pd.Series`` int 0/1; ``attrs['is_research_stub'] == False``

        Raises:
            ValueError: Wenn ``close`` fehlt
        """
        if "close" not in data.columns:
            raise ValueError(f"Spalte 'close' nicht in DataFrame. Verfügbar: {list(data.columns)}")
        if len(data) == 0:
            empty = pd.Series([], dtype=int)
            empty.attrs["is_research_stub"] = False
            return empty

        close = data["close"]
        if len(close) < 10:
            z = pd.Series(0, index=data.index, dtype=int)
            z.attrs["is_research_stub"] = False
            z.attrs["lookback_effective"] = self._rolling_lookback(len(close))
            return z

        rv, _low_q, high_q, lb = self._realized_vol_and_quantiles(close)
        # Risk-off wenn Vol über High-Vol-Quantil
        base = (rv <= high_q).fillna(False)
        c = close.astype(float)
        dd = 1.0 - c / c.cummax()
        dd_breach = dd > float(self.cfg.max_intraday_dd)
        signals = (base & ~dd_breach).astype(int)
        signals.index = data.index
        signals.attrs["is_research_stub"] = False
        signals.attrs["lookback_effective"] = lb
        return signals

    def get_regime_state(self, data: pd.DataFrame) -> str:
        """
        Letzter Bar: ``low_vol`` / ``normal`` / ``high_vol`` relativ zu Quantilen.

        Args:
            data: DataFrame mit ``close``

        Returns:
            Regime-String (bei zu wenig Daten: ``normal``).
        """
        if "close" not in data.columns or len(data) < 10:
            return "normal"
        close = data["close"]
        rv, low_q, high_q, _lb = self._realized_vol_and_quantiles(close)
        rvi, lqi, hqi = rv.iloc[-1], low_q.iloc[-1], high_q.iloc[-1]
        if pd.isna(rvi) or pd.isna(lqi) or pd.isna(hqi):
            return "normal"
        if rvi < lqi:
            return "low_vol"
        if rvi > hqi:
            return "high_vol"
        return "normal"

    def get_position_scalar(self, data: pd.DataFrame) -> float:
        """
        Letztes Signal als Sizing-Skalar ``0.0`` oder ``1.0`` (ggf. mit Vol-Budget).

        Args:
            data: DataFrame mit ``close``

        Returns:
            Skalar in [0.0, 1.0]
        """
        sig = self.generate_signals(data)
        if len(sig) == 0:
            return 0.0
        last = float(sig.iloc[-1])
        if not self.cfg.vol_target_scaling:
            return last
        return min(1.0, last * float(self.cfg.day_vol_budget) / 0.02)

    def validate(self) -> None:
        """Validiert Parameter."""
        if self.cfg.day_vol_budget <= 0:
            raise ValueError(f"day_vol_budget ({self.cfg.day_vol_budget}) muss > 0 sein")
        if self.cfg.max_intraday_dd <= 0:
            raise ValueError(f"max_intraday_dd ({self.cfg.max_intraday_dd}) muss > 0 sein")
        if self.cfg.regime_lookback_bars < 10:
            raise ValueError(
                f"regime_lookback_bars ({self.cfg.regime_lookback_bars}) muss >= 10 sein"
            )
        if not 0 < self.cfg.low_vol_threshold < self.cfg.high_vol_threshold < 1:
            raise ValueError(
                f"Thresholds müssen: 0 < low ({self.cfg.low_vol_threshold}) "
                f"< high ({self.cfg.high_vol_threshold}) < 1 sein"
            )

    def __repr__(self) -> str:
        return (
            f"<VolRegimeOverlayStrategy("
            f"vol_budget={self.cfg.day_vol_budget:.1%}, "
            f"max_dd={self.cfg.max_intraday_dd:.1%}, "
            f"regime_lookback={self.cfg.regime_lookback_bars}bars) "
            f"[research OHLCV vol proxy]>"
        )
