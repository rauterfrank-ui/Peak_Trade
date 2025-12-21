#!/usr/bin/env python3
"""
Erstellt eine Demo-Session im Session Data Store für Trigger-Training-Tests.

Verwendung:
    python scripts/create_demo_trigger_training_session.py

Erzeugt:
    live_runs/sessions/DEMO_SESSION_001/
        - prices.parquet
        - signals.parquet
        - actions.parquet
        - trades.parquet
        - meta.json
"""

from __future__ import annotations

import sys
from pathlib import Path

# Python-Path anpassen
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd

from src.trigger_training.session_data_store import save_session_data


def create_demo_session():
    """Erstellt eine Demo-Session mit realistischen Trigger-Training-Szenarien."""

    print("[CREATE] Erstelle Demo-Session DEMO_SESSION_001...")

    # --- 1) Preis-Zeitreihe (1 Stunde bei 1min) ---
    start_ts = pd.Timestamp("2025-01-15T10:00:00Z")
    periods = 60
    idx = pd.date_range(start_ts, periods=periods, freq="1min", tz="UTC")

    # Realistischere Preisbewegung: Random Walk
    import numpy as np

    np.random.seed(42)
    returns = np.random.randn(periods) * 0.001  # 0.1% Volatilität pro Minute
    price_series = 30000.0 * (1 + returns).cumprod()

    prices_df = pd.DataFrame(
        {
            "timestamp": idx,
            "symbol": "BTCEUR",
            "close": price_series,
            "open": price_series * (1 + np.random.randn(periods) * 0.0002),
            "high": price_series * (1 + abs(np.random.randn(periods)) * 0.0003),
            "low": price_series * (1 - abs(np.random.randn(periods)) * 0.0003),
            "volume": 100.0 + np.random.rand(periods) * 50.0,
        }
    )

    end_ts = idx[-1]

    # --- 2) Signals (6 realistische Signale) ---
    signal_times = [idx[i] for i in [8, 18, 28, 38, 45, 52]]
    signal_prices = [prices_df.iloc[i]["close"] for i in [8, 18, 28, 38, 45, 52]]

    signals_df = pd.DataFrame(
        {
            "signal_id": [1, 2, 3, 4, 5, 6],
            "timestamp": signal_times,
            "symbol": ["BTCEUR"] * 6,
            "signal_state": [1, -1, 1, 1, -1, 1],  # LONG/SHORT/LONG/LONG/SHORT/LONG
            "recommended_action": [
                "ENTER_LONG",
                "ENTER_SHORT",
                "ENTER_LONG",
                "ENTER_LONG",
                "ENTER_SHORT",
                "ENTER_LONG",
            ],
        }
    )

    # --- 3) Actions (verschiedene User-Reaktionen) ---
    # Signal 1: Schnelle perfekte Ausführung (1s)
    # Signal 2: Zu späte Ausführung (15s)
    # Signal 3: Verpasst (keine Action)
    # Signal 4: Rechtzeitige Ausführung (4s)
    # Signal 5: Bewusst übersprungen (SKIPPED)
    # Signal 6: FOMO-Execution nach langem Zögern (20s)

    actions_rows = [
        # (signal_id, offset_s, user_action, note)
        (1, 1.0, "EXECUTED", "Perfekt! Signal sofort erkannt und ausgeführt."),
        (2, 15.0, "EXECUTED", "Zu spät reagiert - Einstiegspunkt verpasst."),
        # Signal 3: MISSED - keine Action
        (4, 4.0, "EXECUTED", "Gute Reaktionszeit, solides Setup."),
        (5, 0.0, "SKIPPED", "Setup unsicher, lieber warten."),
        (6, 20.0, "EXECUTED", "FOMO! Nach langem Zögern doch eingestiegen."),
    ]

    actions_records = []
    for sid, offset_s, user_action, note in actions_rows:
        sig_row = signals_df.loc[signals_df["signal_id"] == sid].iloc[0]
        action_ts = sig_row["timestamp"] + pd.Timedelta(seconds=offset_s)
        actions_records.append(
            {
                "signal_id": sid,
                "timestamp": action_ts,
                "user_action": user_action,
                "note": note,
            }
        )

    actions_df = pd.DataFrame.from_records(actions_records)

    # --- 4) Trades (für EXECUTED-Actions) ---
    trade_rows = []
    for _, act in actions_df.iterrows():
        if not act["user_action"].startswith("EXECUTED"):
            continue

        sig = signals_df.loc[signals_df["signal_id"] == act["signal_id"]].iloc[0]
        ts = act["timestamp"]

        # Finde Preis zum Trade-Zeitpunkt
        price_idx = prices_df["timestamp"].searchsorted(ts)
        if price_idx >= len(prices_df):
            price_idx = len(prices_df) - 1
        trade_price = prices_df.iloc[price_idx]["close"]

        # Simuliere PnL basierend auf Timing
        direction = 1 if sig["signal_state"] > 0 else -1
        qty = 0.01 * direction

        # Delay-basierte PnL-Penalty
        delay_s = (act["timestamp"] - sig["timestamp"]).total_seconds()
        if delay_s < 5:
            pnl = direction * 25.0  # Gute Ausführung
        elif delay_s < 10:
            pnl = direction * 10.0  # OK Ausführung
        else:
            pnl = direction * -5.0  # Schlechte Ausführung (zu spät)

        fees = abs(qty * trade_price) * 0.001  # 0.1% Gebühren

        trade_rows.append(
            {
                "timestamp": ts,
                "price": float(trade_price),
                "qty": qty,
                "pnl": pnl,
                "fees": fees,
            }
        )

    trades_df = (
        pd.DataFrame.from_records(trade_rows)
        if trade_rows
        else pd.DataFrame(columns=["timestamp", "price", "qty", "pnl", "fees"])
    )

    # --- 5) Speichern ---
    session_dir = save_session_data(
        session_id="DEMO_SESSION_001",
        prices_df=prices_df,
        signals_df=signals_df,
        actions_df=actions_df,
        trades_df=trades_df,
        start_ts=start_ts,
        end_ts=end_ts,
        symbol="BTCEUR",
        timeframe="1m",
        environment="offline_paper_trade",
        strategy="demo_ma_crossover",
        extra_meta={
            "drill_type": "trigger_training_demo",
            "note": "Demo-Session mit 6 Signalen und verschiedenen Reaktionsmustern",
        },
    )

    print(f"[CREATE] Erfolgreich gespeichert in: {session_dir}")
    print(f"[CREATE] - {len(prices_df)} Preis-Bars")
    print(f"[CREATE] - {len(signals_df)} Signale")
    print(f"[CREATE] - {len(actions_df)} Actions")
    print(f"[CREATE] - {len(trades_df)} Trades")
    print(f"[CREATE] - Total PnL: {trades_df['pnl'].sum():.2f}")
    print()
    print("[USAGE] Verwende diese Session mit:")
    print(
        "  python scripts/run_offline_trigger_training_drill_example.py --session-id DEMO_SESSION_001"
    )


if __name__ == "__main__":
    create_demo_session()
