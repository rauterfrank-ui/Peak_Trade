import pandas as pd
import numpy as np

# ----------------------------------------------------
# 1) Dummy-Daten erzeugen (5 Tage, 1-min OHLC)
# ----------------------------------------------------
rng = pd.date_range("2024-01-01", "2024-01-05", freq="1min")
df = pd.DataFrame(index=rng)
df["close"] = np.sin(np.linspace(0, 20, len(df))) * 50 + 100
df["close"] += np.random.normal(0, 1, len(df))

# ----------------------------------------------------
# 2) Moving Averages berechnen
# ----------------------------------------------------
df["fast_ma"] = df["close"].rolling(20).mean()
df["slow_ma"] = df["close"].rolling(50).mean()

# ----------------------------------------------------
# 3) Signale generieren (Crossover)
# ----------------------------------------------------
df["signal_raw"] = np.where(
    df["fast_ma"] > df["slow_ma"], 1,
    np.where(df["fast_ma"] < df["slow_ma"], -1, 0)
)

df["signal"] = df["signal_raw"].diff().fillna(0)

# ----------------------------------------------------
# 4) Debug-Ausgaben
# ----------------------------------------------------
print("\n### Value Counts der Rohsignale (fast > slow vs fast < slow):")
print(df["signal_raw"].value_counts())

print("\n### Value Counts der echten Handelssignale (nur Änderungen):")
print(df["signal"].value_counts())

print("\n### Erste 30 Zeilen:")
print(df[["close", "fast_ma", "slow_ma", "signal_raw", "signal"]].head(30))

print("\n### Letzte 30 Zeilen:")
print(df[["close", "fast_ma", "slow_ma", "signal_raw", "signal"]].tail(30))
