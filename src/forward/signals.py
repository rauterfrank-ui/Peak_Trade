# src/forward/signals.py
from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import pandas as pd


@dataclass
class ForwardSignal:
    """
    Standard-Record für ein Forward-/Paper-Trading-Signal.

    Interpretation:
    - generated_at: Zeitpunkt der Signalerzeugung (UTC-ISO).
    - as_of: Zeitpunkt, auf den sich das Signal bezieht (z.B. letzte Bar im Datensatz).
    - strategy_key: Name/Key der Strategie (z.B. 'ma_crossover', 'idea.RsiKeltnerStrategy', ...).
    - run_name: Name dieses Signal-Runs (z.B. 'forward_daily_2025-12-04').
    - symbol: Markt/Symbol, z.B. 'BTC/EUR'.
    - direction: -1 = Short, 0 = Flat, +1 = Long (oder wie von der Strategie geliefert).
    - size_hint: optionaler Größen-Hinweis (z.B. 1.0 = volle Standardgröße, 0.5 = halbe Größe).
    - comment: Freitext-Kommentar.
    - extra: beliebige Zusatzinfos (z.B. Roh-Signalwert, Confidence, Regime, etc.).
    """

    generated_at: str
    as_of: str
    strategy_key: str
    run_name: str
    symbol: str
    direction: float

    size_hint: float | None = None
    comment: str | None = None
    extra: dict[str, Any] | None = None


FORWARD_SIGNALS_COLUMNS: Sequence[str] = [
    "generated_at",
    "as_of",
    "strategy_key",
    "run_name",
    "symbol",
    "direction",
    "size_hint",
    "comment",
    "extra_json",
]


def signals_to_dataframe(signals: Iterable[ForwardSignal]) -> pd.DataFrame:
    """
    Wandelt eine Liste von ForwardSignal in ein DataFrame mit bekannten Spalten um.
    """
    rows: list[dict[str, Any]] = []
    for sig in signals:
        d = asdict(sig)
        extra = d.pop("extra", None)
        d["extra_json"] = None
        if extra is not None:
            # Lazy Import (um Abhängigkeit zu minimieren)
            import json

            d["extra_json"] = json.dumps(extra, ensure_ascii=False)
        rows.append(d)

    if not rows:
        return pd.DataFrame(columns=list(FORWARD_SIGNALS_COLUMNS))

    df = pd.DataFrame(rows)
    # Spaltenreihenfolge erzwingen
    for col in FORWARD_SIGNALS_COLUMNS:
        if col not in df.columns:
            df[col] = None
    df = df[list(FORWARD_SIGNALS_COLUMNS)]
    return df


def save_signals_to_csv(signals: Iterable[ForwardSignal], path: Path | str) -> pd.DataFrame:
    """
    Speichert eine Liste von ForwardSignal als CSV und gibt das DataFrame zurück.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df = signals_to_dataframe(list(signals))
    df.to_csv(path, index=False)
    return df


def load_signals_csv(path: Path | str) -> pd.DataFrame:
    """
    Lädt eine Forward-Signal-CSV, die von save_signals_to_csv erzeugt wurde.

    Mindest-Spalten:
    - symbol
    - direction
    - as_of
    - strategy_key
    - run_name
    """
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Signals-CSV nicht gefunden: {path}")

    df = pd.read_csv(path)
    required = {"symbol", "direction", "as_of", "strategy_key", "run_name"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Signals-CSV fehlt Spalten: {missing}")

    return df
