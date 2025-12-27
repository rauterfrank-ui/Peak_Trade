# src/core/regime.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Dict, Any

import numpy as np
import pandas as pd

from .peak_config import PeakConfig

TrendRegime = Literal["TREND_UP", "TREND_DOWN", "RANGE", "UNKNOWN"]
VolRegime = Literal["LOW_VOL", "HIGH_VOL", "UNKNOWN"]


@dataclass
class RegimeConfig:
    """
    Konfigurationsparameter für die Regime-Erkennung.

    Idee:
    - TrendScore: gleitende Rendite über `trend_window`
      - > +trend_threshold  => TREND_UP
      - < -trend_threshold  => TREND_DOWN
      - sonst               => RANGE

    - VolScore: gleitende Standardabweichung der Renditen über `vol_window`
      - > vol_threshold     => HIGH_VOL
      - sonst               => LOW_VOL
    """

    price_col: str = "close"

    trend_window: int = 50
    trend_threshold: float = 0.002  # ~0.2% über trend_window

    vol_window: int = 50
    vol_threshold: float = 0.02  # ~2% Volatilität

    def to_dict(self) -> Dict[str, Any]:
        return {
            "price_col": self.price_col,
            "trend_window": self.trend_window,
            "trend_threshold": self.trend_threshold,
            "vol_window": self.vol_window,
            "vol_threshold": self.vol_threshold,
        }


def build_regime_config_from_config(
    cfg: PeakConfig,
    section: str = "regime",
) -> RegimeConfig:
    """
    Baut eine RegimeConfig aus der TOML-Config.

    Erwartete Struktur in config.toml:

    [regime]
    price_col = "close"
    trend_window = 50
    trend_threshold = 0.002
    vol_window = 50
    vol_threshold = 0.02
    """
    price_col = cfg.get(f"{section}.price_col", "close")

    trend_window = int(cfg.get(f"{section}.trend_window", 50))
    trend_threshold = float(cfg.get(f"{section}.trend_threshold", 0.002))

    vol_window = int(cfg.get(f"{section}.vol_window", 50))
    vol_threshold = float(cfg.get(f"{section}.vol_threshold", 0.02))

    return RegimeConfig(
        price_col=price_col,
        trend_window=trend_window,
        trend_threshold=trend_threshold,
        vol_window=vol_window,
        vol_threshold=vol_threshold,
    )


def _compute_returns(price: pd.Series) -> pd.Series:
    return price.astype(float).pct_change().fillna(0.0)


def compute_trend_score(
    price: pd.Series,
    window: int,
) -> pd.Series:
    """
    Einfache Trend-Metrik: gleitende durchschnittliche Rendite über 'window'.
    Positive Werte = Aufwärtstrend, negative = Abwärtstrend.
    """
    returns = _compute_returns(price)
    return returns.rolling(window, min_periods=1).mean()


def compute_vol_score(
    price: pd.Series,
    window: int,
) -> pd.Series:
    """
    Einfache Volatilitäts-Metrik: gleitende Standardabweichung der Renditen.
    """
    returns = _compute_returns(price)
    return returns.rolling(window, min_periods=1).std(ddof=0)


def label_trend_regime(
    data: pd.DataFrame,
    cfg: RegimeConfig,
) -> pd.Series:
    """
    Labelt pro Zeitstempel ein Trend-Regime: TREND_UP / TREND_DOWN / RANGE.
    """
    if cfg.price_col not in data.columns:
        raise KeyError(
            f"Spalte {cfg.price_col!r} nicht im DataFrame. Vorhandene Spalten: {list(data.columns)}"
        )

    price = data[cfg.price_col].astype(float)
    trend_score = compute_trend_score(price, window=cfg.trend_window)

    labels = pd.Series("RANGE", index=data.index, dtype="object")

    labels = labels.mask(trend_score > cfg.trend_threshold, "TREND_UP")
    labels = labels.mask(trend_score < -cfg.trend_threshold, "TREND_DOWN")

    labels = labels.fillna("UNKNOWN")
    labels.name = "trend_regime"
    return labels.astype("string")


def label_vol_regime(
    data: pd.DataFrame,
    cfg: RegimeConfig,
) -> pd.Series:
    """
    Labelt pro Zeitstempel ein Vol-Regime: LOW_VOL / HIGH_VOL.
    """
    if cfg.price_col not in data.columns:
        raise KeyError(
            f"Spalte {cfg.price_col!r} nicht im DataFrame. Vorhandene Spalten: {list(data.columns)}"
        )

    price = data[cfg.price_col].astype(float)
    vol_score = compute_vol_score(price, window=cfg.vol_window)

    labels = pd.Series("LOW_VOL", index=data.index, dtype="object")
    labels = labels.mask(vol_score > cfg.vol_threshold, "HIGH_VOL")

    labels = labels.fillna("UNKNOWN")
    labels.name = "vol_regime"
    return labels.astype("string")


def label_combined_regime(
    trend_labels: pd.Series,
    vol_labels: pd.Series,
) -> pd.Series:
    """
    Kombiniert Trend- und Vol-Regime zu einem String-Label pro Zeitstempel.
    Beispiel: TREND_UP_HIGH_VOL, RANGE_LOW_VOL, ...
    """
    trend = trend_labels.astype("string").fillna("UNKNOWN")
    vol = vol_labels.astype("string").fillna("UNKNOWN")

    combined = trend + "_" + vol
    combined.name = "regime"
    return combined.astype("string")


def summarize_regime_distribution(
    combined_regime: pd.Series,
) -> Dict[str, float]:
    """
    Berechnet die Verteilung der kombinierten Regime als Anteile (0..1).
    """
    if combined_regime.empty:
        return {}

    counts = combined_regime.value_counts(dropna=False)
    total = counts.sum()
    dist = (counts / total).to_dict()

    # alle Werte in float konvertieren
    return {str(k): float(v) for k, v in dist.items()}
