#!/usr/bin/env python3
from __future__ import annotations

"""
Offline Trigger-Training Drill – Example Script (v0)

Zweck:
  - Bestehende Offline-Paper-/Offline-Realtime-Session nutzen
  - Trigger-Training-Events aus Signals/Actions/Prices generieren
  - Offline-Paper-Report + Trigger-Training-Report erzeugen

Dieses Script ist bewusst generisch gehalten:
  -> Du musst nur die Funktion `load_data_for_session(...)` an deine
     bestehende Offline-Session-Pipeline anbinden (TODO-Block unten).
"""

import argparse
from datetime import datetime
from pathlib import Path
from typing import Tuple

import pandas as pd

from src.trigger_training.hooks import (
    TriggerTrainingHookConfig,
    build_trigger_training_events_from_dfs,
)
from src.reporting.offline_paper_trade_integration import (
    OfflinePaperTradeReportConfig,
    generate_reports_for_offline_paper_trade,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Offline Trigger-Training Drill – Reports erzeugen (Paper + Trigger)."
    )
    parser.add_argument(
        "--session-id",
        type=str,
        default=None,
        help="Optionale Session-ID. Wenn nicht gesetzt, wird eine basierend auf dem aktuellen Timestamp erzeugt.",
    )
    parser.add_argument(
        "--symbol",
        type=str,
        default="BTCEUR",
        help="Symbol für den Drill (nur Meta / Doku, beeinflusst keine Logik).",
    )
    parser.add_argument(
        "--timeframe",
        type=str,
        default="1m",
        help="Timeframe (nur Meta / Doku, beeinflusst keine Logik).",
    )
    parser.add_argument(
        "--environment",
        type=str,
        default="offline_paper_trade",
        help="Environment-Label für die Reports (z.B. offline_paper_trade, offline_realtime).",
    )
    parser.add_argument(
        "--reports-dir",
        type=str,
        default="reports/offline_paper_trade",
        help="Basis-Reports-Verzeichnis (Standard: reports/offline_paper_trade).",
    )
    return parser.parse_args()


def _default_session_id() -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"DRILL_TRIGGER_{ts}"


def load_data_for_session(session_id: str) -> Tuple[
    pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.Timestamp, pd.Timestamp
]:
    """
    Demo-Implementierung für eine Offline-Trigger-Training-Session.

    Diese Funktion erzeugt synthetische DataFrames, die exakt das Schema
    nachbilden, das deine echte Offline-Session liefern sollte.

    Du kannst diese Implementierung verwenden um:
      - das Script sofort zu testen
      - das erwartete Schema zu sehen
      - später 1:1 durch deine echte Pipeline-Anbindung zu ersetzen.
    """
    # --- 1) Preis-Zeitreihe (prices_df) -----------------------------
    start_ts = pd.Timestamp("2025-01-01T00:00:00Z")
    periods = 60  # 60 Minuten = 1h Drill
    idx = pd.date_range(start_ts, periods=periods, freq="1min", tz="UTC")

    close = 30000 + (idx.astype("int64") // 10**9 % 100) * 2.0  # leicht steigender/variierender Preis

    prices_df = pd.DataFrame(
        {
            "timestamp": idx,
            "symbol": "BTCEUR",
            "close": close,
        }
    )

    end_ts = prices_df["timestamp"].iloc[-1]

    # --- 2) Signals (signals_df) ------------------------------------
    # Wir setzen 5 Signale im Verlauf der Session
    signal_times = [
        prices_df["timestamp"].iloc[i]
        for i in [5, 15, 25, 35, 45]
    ]

    signals_df = pd.DataFrame(
        {
            "signal_id": [1, 2, 3, 4, 5],
            "timestamp": signal_times,
            "symbol": ["BTCEUR"] * 5,
            "signal_state": [1, 1, -1, 1, -1],  # LONG/LONG/SHORT/LONG/SHORT
            "recommended_action": [
                "ENTER_LONG",
                "ENTER_LONG",
                "ENTER_SHORT",
                "ENTER_LONG",
                "ENTER_SHORT",
            ],
        }
    )

    # --- 3) Actions (actions_df) ------------------------------------
    # Simuliert verschiedene Trader-Reaktionen auf Signale:
    actions_rows = [
        # signal_id, action_ts_offset_s, user_action, note
        # Szenario 1: Schnelle Ausführung (2s nach Signal)
        (1, 2.0, "EXECUTED", "Schnelle Reaktion, guter Fill."),
        # Szenario 2: Zu späte Ausführung (12s nach Signal)
        (2, 12.0, "EXECUTED", "Zu spät reagiert, Markt ist schon gelaufen."),
        # Szenario 3: signal_id 3 hat keine Action -> verpasster Trade (MISSED)
        # Szenario 4: Rechtzeitig ausgeführtes Signal (3s nach Signal)
        (4, 3.0, "EXECUTED", "Passt."),
        # Szenario 5: Bewusst übersprungenes Signal
        (5, 0.0, "SKIPPED", "Unsicherheit, Setup nicht vertraut."),
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

    # --- 4) Trades (trades_df) --------------------------------------
    # Sehr einfache PnL-Heuristik: wir „tun so", als wäre jede EXECUTED-Action ein Trade.
    trade_rows = []
    for _, act in actions_df.iterrows():
        if act["user_action"].startswith("EXECUTED"):
            sig = signals_df.loc[signals_df["signal_id"] == act["signal_id"]].iloc[0]
            ts = act["timestamp"]
            # Nehme den nächstliegenden Preis aus prices_df
            price_row = prices_df.iloc[(prices_df["timestamp"] - ts).abs().argsort().iloc[0]]
            direction = 1 if sig["signal_state"] > 0 else -1
            qty = 0.01 * direction
            # Dummy-PnL: zufällig leichte Gewinne/Verluste
            pnl = float(direction) * 10.0
            fees = 0.1

            trade_rows.append(
                {
                    "timestamp": ts,
                    "price": float(price_row["close"]),
                    "qty": qty,
                    "pnl": pnl,
                    "fees": fees,
                }
            )

    trades_df = pd.DataFrame.from_records(trade_rows) if trade_rows else pd.DataFrame(
        columns=["timestamp", "price", "qty", "pnl", "fees"]
    )

    return trades_df, signals_df, actions_df, prices_df, start_ts, end_ts


def main() -> None:
    args = parse_args()

    session_id = args.session_id or _default_session_id()
    symbol = args.symbol
    timeframe = args.timeframe
    environment = args.environment
    base_reports_dir = Path(args.reports_dir)

    print(f"[DRILL] Session-ID: {session_id}")
    print(f"[DRILL] Symbol:     {symbol}")
    print(f"[DRILL] Timeframe:  {timeframe}")
    print(f"[DRILL] Env:        {environment}")
    print(f"[DRILL] Reports:    {base_reports_dir}/<session_id>/...")

    # 1) Daten aus der Session holen (hier musst du anpassen!)
    (
        trades_df,
        signals_df,
        actions_df,
        prices_df,
        start_ts,
        end_ts,
    ) = load_data_for_session(session_id=session_id)

    # 2) Trigger-Events aus Signals/Actions/Prices generieren
    hook_cfg = TriggerTrainingHookConfig(
        lookahead_bars=20,
        late_threshold_s=5.0,
        pain_threshold=0.0,
    )

    print("[DRILL] Baue Trigger-Training-Events ...")
    trigger_events = build_trigger_training_events_from_dfs(
        signals=signals_df,
        actions=actions_df,
        prices=prices_df,
        config=hook_cfg,
    )
    print(f"[DRILL] {len(trigger_events)} Trigger-Events erzeugt.")

    # 3) Reports erzeugen (Offline-Paper + Trigger-Report)
    report_cfg = OfflinePaperTradeReportConfig(
        session_id=session_id,
        environment=environment,
        symbol=symbol,
        timeframe=timeframe,
        start_ts=start_ts,
        end_ts=end_ts,
        extra_meta={"strategy": "ma_crossover", "drill_mode": "trigger_training"},
        base_reports_dir=base_reports_dir,
    )

    print("[DRILL] Erzeuge Reports ...")
    result_paths = generate_reports_for_offline_paper_trade(
        trades=trades_df,
        report_config=report_cfg,
        trigger_events=trigger_events,
        session_meta_for_trigger={
            "session_id": session_id,
            "mode": "offline_trigger_training",
            "strategy": "ma_crossover",
            "symbol": symbol,
            "timeframe": timeframe,
        },
    )

    paper_report = result_paths.get("paper_report")
    trigger_report = result_paths.get("trigger_report")

    print("[DRILL] Fertig.")
    if paper_report:
        print(f"[REPORT] Offline-Paper-Report:   {paper_report}")
    if trigger_report:
        print(f"[REPORT] Trigger-Training-Report: {trigger_report}")
    if not trigger_report:
        print("[WARN] Kein Trigger-Report erzeugt (keine Trigger-Events?).")


if __name__ == "__main__":
    main()
