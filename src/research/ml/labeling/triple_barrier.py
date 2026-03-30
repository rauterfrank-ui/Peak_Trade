# src/research/ml/labeling/triple_barrier.py
"""
Triple-Barrier Method – Research-Only
=====================================

Implementierung der Triple-Barrier-Labeling-Methode nach
Marcos López de Prado für ML-basiertes Trading.

⚠️ RESEARCH-ONLY – NICHT FÜR LIVE-TRADING ⚠️

Konzept:
- Horizontal Barriers: Take-Profit und Stop-Loss
- Vertical Barrier: Maximale Haltedauer (Time-Exit)
- Label = welche Barriere zuerst erreicht wird

Labels:
- +1: Take-Profit erreicht (profitable Trade)
- -1: Stop-Loss erreicht (verlustreicher Trade)
-  0: Vertical Barrier erreicht (Time-Exit / unentschieden)

Referenz:
- "Advances in Financial Machine Learning" (López de Prado), Chapter 3
"""

from __future__ import annotations

import logging
from typing import Optional, Tuple

import numpy as np
import pandas as pd
from pandas.tseries.frequencies import to_offset

logger = logging.getLogger(__name__)


def _tp_sl_levels(
    entry: float,
    take_profit: float,
    stop_loss: float,
    long_side: bool,
) -> Tuple[float, float]:
    """Gibt (oberes Preisniveau, unteres Preisniveau) für Long bzw. Short zurück."""
    if long_side:
        upper = entry * (1.0 + take_profit)
        lower = entry * (1.0 - stop_loss)
    else:
        # Short: Gewinn bei Preis unter Entry*(1-tp), Verlust bei über Entry*(1+sl)
        upper = entry * (1.0 + stop_loss)
        lower = entry * (1.0 - take_profit)
    return upper, lower


def _label_from_path(
    future_prices: pd.Series,
    upper: float,
    lower: float,
    long_side: bool,
) -> int:
    """
    Erstes Berühren einer Barriere auf Close-Pfad (barweise, zeitlich vorwärts).

    Bei Long: Close >= upper -> +1, Close <= lower -> -1.
    Bei Short: Close <= lower -> +1 (TP), Close >= upper -> -1 (SL).
    """
    for p in future_prices.astype(float):
        if not np.isfinite(p):
            continue
        if long_side:
            if p >= upper:
                return 1
            if p <= lower:
                return -1
        else:
            if p <= lower:
                return 1
            if p >= upper:
                return -1
    return 0


def compute_triple_barrier_labels(
    prices: pd.Series,
    signals: pd.Series,
    take_profit: Optional[float] = 0.02,
    stop_loss: Optional[float] = 0.01,
    vertical_barrier_bars: int = 20,
    side_prediction: bool = True,
) -> pd.Series:
    """
    Berechnet Triple-Barrier-Labels für Trading-Signale.

    Pro Eintritts-Bar (signals != 0): Eintrittspreis = Close an diesem Bar,
    dann Forward-Scan über die nächsten ``vertical_barrier_bars`` Bars (exkl. Entry-Bar).

    Args:
        prices: Preisserie (typisch: Close-Preise)
        signals: Basis-Strategie-Signale (+1 long, -1 short, 0 flat)
        take_profit: TP als relative Schwelle (z.B. 0.02 = 2 %)
        stop_loss: SL als relative Schwelle (z.B. 0.01 = 1 %)
        vertical_barrier_bars: Maximale Haltedauer in Bars (Forward-Fenster)
        side_prediction: Reserviert; bei False wird aktuell wie True behandelt

    Returns:
        Series mit Labels (+1 / 0 / -1) an Signal-Bars; an Bars ohne Signal ``pd.NA``
        (nullable Integer ``Int64``).
    """
    if take_profit is None:
        take_profit = 0.02
    if stop_loss is None:
        stop_loss = 0.01

    take_profit = float(take_profit)
    stop_loss = float(stop_loss)
    if take_profit < 0 or stop_loss < 0:
        raise ValueError("take_profit and stop_loss must be non-negative")

    if not side_prediction:
        logger.debug(
            "side_prediction=False: using same directional barriers as side_prediction=True"
        )

    prices = prices.astype(float)
    signals = signals.reindex(prices.index)

    labels: list[Optional[int]] = []
    n = len(prices)
    for i in range(n):
        sig = int(signals.iloc[i]) if pd.notna(signals.iloc[i]) else 0
        if sig == 0:
            labels.append(pd.NA)
            continue

        entry = float(prices.iloc[i])
        if not np.isfinite(entry) or entry <= 0:
            labels.append(pd.NA)
            continue

        long_side = sig > 0
        upper, lower = _tp_sl_levels(entry, take_profit, stop_loss, long_side)

        end = min(i + vertical_barrier_bars + 1, n)
        future = prices.iloc[i + 1 : end]
        if len(future) == 0:
            labels.append(0)
            continue

        labels.append(_label_from_path(future, upper, lower, long_side))

    return pd.Series(labels, index=prices.index, dtype="Int64")


def get_vertical_barrier(
    signal_times: pd.DatetimeIndex,
    max_holding_period: int,
    freq: str = "1h",
) -> pd.Series:
    """
    Berechnet Vertical Barriers (Time-Exits) als Zeitstempel pro Signal.

    ``max_holding_period`` * ``freq`` wird zu jedem Signalzeitpunkt addiert.
    """
    step = to_offset(freq) * max_holding_period
    ts = pd.DatetimeIndex(signal_times) + step
    return pd.Series(ts, index=signal_times, dtype="datetime64[ns]")


def get_horizontal_barriers(
    prices: pd.Series,
    events: pd.DataFrame,
    take_profit: float,
    stop_loss: float,
) -> Tuple[pd.Series, pd.Series]:
    """
    Berechnet horizontale Barriers (TP/SL-Preise) pro Event.

    Erwartet ``events`` mit Spalte ``entry`` (Eintrittspreis) und optional ``side``
    (+1 Long, -1 Short; Default Long).
    ``prices`` ist für API-Kompatibilität reserviert (z. B. Intrabar-Logik).
    """
    _ = prices
    if "entry" not in events.columns:
        raise ValueError("events must contain an 'entry' column")

    entry = events["entry"].astype(float)
    if "side" in events.columns:
        side = events["side"].fillna(1).astype(int)
    else:
        side = pd.Series(1, index=events.index, dtype=int)

    upper_list: list[float] = []
    lower_list: list[float] = []
    for e, s in zip(entry, side):
        if not np.isfinite(e) or e <= 0:
            upper_list.append(np.nan)
            lower_list.append(np.nan)
            continue
        u, lo = _tp_sl_levels(float(e), take_profit, stop_loss, long_side=int(s) > 0)
        upper_list.append(u)
        lower_list.append(lo)

    upper = pd.Series(upper_list, index=events.index, dtype=float)
    lower = pd.Series(lower_list, index=events.index, dtype=float)
    return upper, lower


def apply_pnl_stop_loss(
    prices: pd.Series,
    events: pd.DataFrame,
    max_loss: float,
) -> pd.Series:
    """
    Platzhalter für PnL-basierte Stop-Anpassung (Research-Erweiterung).

    Gibt aktuell überall ``NaT`` zurück, wenn keine ``exit_time``-Spalte gesetzt ist.
    ``prices`` und ``max_loss`` sind für künftige Logik reserviert.
    """
    _ = (prices, max_loss)
    if "exit_time" in events.columns:
        return pd.Series(events["exit_time"].values, index=events.index, dtype="datetime64[ns]")
    return pd.Series(pd.NaT, index=events.index, dtype="datetime64[ns]")
