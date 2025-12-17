"""
Peak_Trade RSI Strategy
========================
RSI-basierte Mean-Reversion-Strategie.

Konzept:
- Long-Entry: RSI kreuzt oversold von unten
- Exit: RSI kreuzt overbought von unten
- RSI = Relative Strength Index
"""


import pandas as pd


def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """
    Berechnet RSI (Relative Strength Index).

    Args:
        prices: Close-Preise
        period: RSI-Periode

    Returns:
        RSI-Werte (0-100)
    """
    # Preisänderungen
    delta = prices.diff()

    # Gewinne und Verluste trennen
    gains = delta.where(delta > 0, 0)
    losses = -delta.where(delta < 0, 0)

    # Exponentieller Moving Average
    avg_gains = gains.ewm(span=period, adjust=False).mean()
    avg_losses = losses.ewm(span=period, adjust=False).mean()

    # RS = Average Gain / Average Loss
    rs = avg_gains / avg_losses

    # RSI = 100 - (100 / (1 + RS))
    rsi = 100 - (100 / (1 + rs))

    return rsi



def generate_signals(df: pd.DataFrame, params: dict) -> pd.Series:
    """
    Generiert RSI-basierte Signale.

    Args:
        df: OHLCV-DataFrame
        params: Dict mit 'rsi_period', 'oversold', 'overbought'

    Returns:
        Series mit Signalen (1 = Long, 0 = Neutral, -1 = Exit)
    """
    # Parameter
    rsi_period = params.get('rsi_period', 14)
    oversold = params.get('oversold', 30)
    overbought = params.get('overbought', 70)

    # RSI berechnen
    rsi = calculate_rsi(df['close'], period=rsi_period)

    # Signale initialisieren
    signals = pd.Series(0, index=df.index, dtype=int)

    # Entry: RSI kreuzt oversold-Level von unten
    cross_oversold = (rsi.shift(1) < oversold) & (rsi >= oversold)
    signals[cross_oversold] = 1

    # Exit: RSI kreuzt overbought-Level von unten
    cross_overbought = (rsi.shift(1) < overbought) & (rsi >= overbought)
    signals[cross_overbought] = -1

    return signals


def add_rsi_indicators(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    """Fügt RSI-Indikatoren hinzu."""
    df = df.copy()

    rsi_period = params.get('rsi_period', 14)
    df['rsi'] = calculate_rsi(df['close'], period=rsi_period)

    return df
