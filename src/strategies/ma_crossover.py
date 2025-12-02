import pandas as pd
import numpy as np
from typing import Dict


def generate_signals(df: pd.DataFrame, params: Dict) -> pd.Series:
    """
    MA-Crossover-Strategie: State-Signal (1=long, 0=flat)
    kompatibel mit BacktestEngine.run_realistic.
    """
    df = df.copy()
    
    # Parameter + Validierung
    fast = params.get("fast_period", 10)
    slow = params.get("slow_period", 30)

    if fast >= slow:
        raise ValueError(f"fast_period ({fast}) muss < slow_period ({slow}) sein")
    if fast < 2 or slow < 2:
        raise ValueError("MA-Perioden müssen >= 2 sein")
    if len(df) < slow:
        raise ValueError(f"Brauche mind. {slow} Bars, habe nur {len(df)}")

    # MAs berechnen
    df["fast_ma"] = df["close"].rolling(fast, min_periods=fast).mean()
    df["slow_ma"] = df["close"].rolling(slow, min_periods=slow).mean()

    # Crossover über Differenz
    ma_diff = df["fast_ma"] - df["slow_ma"]
    cross_up = (ma_diff > 0) & (ma_diff.shift(1) <= 0)
    cross_down = (ma_diff < 0) & (ma_diff.shift(1) >= 0)

    # Event-Signale
    events = pd.Series(0, index=df.index, dtype=int)
    events[cross_up] = 1
    events[cross_down] = -1

    # Event → State (1=long, 0=flat)
    # -1 = Exit → 0
    state = events.replace({-1: 0})
    # Initiale Nullen nicht wegfüllen, nur "im Trade bleiben"
    state = state.replace(0, pd.NA).ffill().fillna(0).astype(int)

    return state
