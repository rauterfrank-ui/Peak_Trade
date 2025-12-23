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

import sys
from pathlib import Path

# Ensure src is in path (für standalone Ausführung)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import argparse
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Tuple

import pandas as pd

from src.trigger_training.hooks import (
    TriggerTrainingHookConfig,
    build_trigger_training_events_from_dfs,
)
from src.trigger_training.session_data_store import (
    load_session_data,
    session_exists,
    list_session_ids,
)
from src.trigger_training.reaction_stats import (
    TriggerReactionConfig,
    compute_reaction_records,
    summarize_reaction_records,
    reaction_records_to_df,
    reaction_summary_to_dict,
)
from src.execution.metrics.execution_latency import (
    create_latency_timestamps_from_trades_and_signals,
    compute_latency_measures,
    summarize_latency,
    latency_measures_to_df,
    latency_summary_to_dict,
)
from src.reporting.offline_paper_trade_integration import (
    OfflinePaperTradeReportConfig,
    generate_reports_for_offline_paper_trade,
)


# ============================================================================
# Szenario-Matrix für Trigger-Training
# ============================================================================


class ReactionType(str, Enum):
    """Art der Trader-Reaktion auf ein Signal."""

    EXECUTED_FAST = "executed_fast"
    EXECUTED_SLOW = "executed_slow"
    MISSED = "missed"
    SKIPPED = "skipped"


class OutcomeType(str, Enum):
    """Markt-Outcome nach dem Signal."""

    FAVORABLE = "favorable"
    ADVERSE = "adverse"
    NEUTRAL = "neutral"


@dataclass(frozen=True)
class TriggerScenarioDef:
    """Definition eines Trigger-Training-Szenarios."""

    scenario_id: str
    label: str
    reaction_type: ReactionType
    outcome_type: OutcomeType
    psych_tags: list[str]


SCENARIO_MATRIX: list[TriggerScenarioDef] = [
    TriggerScenarioDef(
        scenario_id="DISC_EXEC_GOOD",
        label="Disziplinierter schneller Entry, gutes Signal",
        reaction_type=ReactionType.EXECUTED_FAST,
        outcome_type=OutcomeType.FAVORABLE,
        psych_tags=["DISCIPLINE", "TRUST_SYSTEM"],
    ),
    TriggerScenarioDef(
        scenario_id="TOO_SLOW_ENTRY",
        label="Zu später Entry, Markt schon gelaufen",
        reaction_type=ReactionType.EXECUTED_SLOW,
        outcome_type=OutcomeType.ADVERSE,
        psych_tags=["HESITATION", "TOO_SLOW"],
    ),
    TriggerScenarioDef(
        scenario_id="MISSED_OPPORTUNITY",
        label="Verpasstes Signal, Markt läuft in Signalrichtung",
        reaction_type=ReactionType.MISSED,
        outcome_type=OutcomeType.FAVORABLE,
        psych_tags=["FOMO", "REGRET"],
    ),
    TriggerScenarioDef(
        scenario_id="DISC_EXEC_GOOD_SHORT",
        label="Disziplinierter Short-Entry, Markt läuft mit",
        reaction_type=ReactionType.EXECUTED_FAST,
        outcome_type=OutcomeType.FAVORABLE,
        psych_tags=["DISCIPLINE", "CONFIDENCE"],
    ),
    TriggerScenarioDef(
        scenario_id="DISCIPLINED_SKIP",
        label="Bewusst geskippt, Markt läuft dagegen",
        reaction_type=ReactionType.SKIPPED,
        outcome_type=OutcomeType.ADVERSE,
        psych_tags=["DISCIPLINE", "RISK_AVERSION_OK"],
    ),
]

# Lookup-Map: (reaction_type, outcome_type) -> TriggerScenarioDef
SCENARIO_BY_KEY = {(s.reaction_type, s.outcome_type): s for s in SCENARIO_MATRIX}


# ============================================================================
# CLI & Helper Functions
# ============================================================================


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


def load_data_for_session(
    session_id: str,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.Timestamp, pd.Timestamp]:
    """
    Lädt Session-Daten aus dem Session Data Store oder generiert Demo-Daten.

    Workflow:
      1. Prüft, ob session_id im Store existiert (live_runs/sessions/<session_id>/)
      2. Falls ja: Lädt echte Daten aus dem Store
      3. Falls nein: Generiert synthetische Demo-Daten für Testing

    Returns
    -------
    Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.Timestamp, pd.Timestamp]
        trades_df, signals_df, actions_df, prices_df, start_ts, end_ts

    Erwartete Schemas:
    ------------------
    prices_df:
        - timestamp (datetime): Zeitstempel
        - close (float): Close-Preis
        - optional: symbol, open, high, low, volume

    signals_df:
        - signal_id (int): Eindeutige Signal-ID
        - timestamp (datetime): Signal-Zeitstempel
        - symbol (str): Trading-Symbol
        - signal_state (int): Signal-Zustand (-1/0/1 für SHORT/FLAT/LONG)
        - recommended_action (str): Empfohlene Action (z.B. "ENTER_LONG")

    actions_df:
        - signal_id (int): Referenz zu signals_df
        - timestamp (datetime): Action-Zeitstempel
        - user_action (str): User-Reaktion (z.B. "EXECUTED", "SKIPPED")
        - note (str): Optionale Notiz

    trades_df:
        - timestamp (datetime): Trade-Zeitstempel
        - price (float): Fill-Preis
        - qty (float): Menge (signed: positiv=long, negativ=short)
        - pnl (float): Profit/Loss
        - fees (float): Gebühren
    """
    # Versuch 1: Echte Daten aus dem Store laden
    if session_exists(session_id):
        print(f"[LOAD] Lade echte Session-Daten aus Store: {session_id}")
        data = load_session_data(session_id)

        trades_df = data["trades"]
        signals_df = data["signals"]
        actions_df = data["actions"]
        prices_df = data["prices"]
        meta = data["meta"]

        start_ts = pd.Timestamp(meta.start_ts)
        end_ts = pd.Timestamp(meta.end_ts)

        print(f"[LOAD] Erfolgreich: {len(signals_df)} Signale, {len(trades_df)} Trades")
        return trades_df, signals_df, actions_df, prices_df, start_ts, end_ts

    # Versuch 2: Demo-Daten generieren
    print(f"[LOAD] Session '{session_id}' nicht im Store gefunden.")
    available = list_session_ids()
    if available:
        print(f"[LOAD] Verfügbare Sessions: {', '.join(available[:5])}...")
    else:
        print(f"[LOAD] Keine Sessions im Store vorhanden.")
    print(f"[LOAD] Generiere synthetische Demo-Daten für Testing...")

    return _generate_demo_data()


def _generate_demo_data() -> (
    Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.Timestamp, pd.Timestamp]
):
    """
    Generiert synthetische Demo-Daten für Testing.

    Diese Funktion erzeugt 5 Signale mit verschiedenen Szenarien:
      - Szenario 1: Schnelle Ausführung (2s nach Signal)
      - Szenario 2: Zu späte Ausführung (12s nach Signal)
      - Szenario 3: Verpasster Trade (keine Action)
      - Szenario 4: Rechtzeitig ausgeführtes Signal (3s nach Signal)
      - Szenario 5: Bewusst übersprungenes Signal (SKIPPED)
    """
    # --- 1) Preis-Zeitreihe (prices_df) -----------------------------
    start_ts = pd.Timestamp("2025-01-01T00:00:00Z")
    periods = 60  # 60 Minuten = 1h Drill
    idx = pd.date_range(start_ts, periods=periods, freq="1min", tz="UTC")

    close = (
        30000 + (idx.astype("int64") // 10**9 % 100) * 2.0
    )  # leicht steigender/variierender Preis

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
    signal_times = [prices_df["timestamp"].iloc[i] for i in [5, 15, 25, 35, 45]]

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

    # --- Szenario-Annotation hinzufügen ---
    signals_df["scenario_id"] = None
    signals_df["scenario_label"] = None
    signals_df["scenario_psych_tags"] = None

    def _set_scenario(
        signal_id: int,
        reaction_type: ReactionType,
        outcome_type: OutcomeType,
        default_id: str | None = None,
    ) -> None:
        """Setzt Szenario-Metadaten für ein bestimmtes Signal."""
        # Falls default_id angegeben, bevorzuge diesen
        if default_id is not None:
            scenario_def = next((s for s in SCENARIO_MATRIX if s.scenario_id == default_id), None)
        else:
            # Ansonsten: Lookup über (reaction_type, outcome_type)
            scenario_def = SCENARIO_BY_KEY.get((reaction_type, outcome_type))

        row_mask = signals_df["signal_id"] == signal_id
        if scenario_def is not None:
            signals_df.loc[row_mask, "scenario_id"] = scenario_def.scenario_id
            signals_df.loc[row_mask, "scenario_label"] = scenario_def.label
            signals_df.loc[row_mask, "scenario_psych_tags"] = ",".join(scenario_def.psych_tags)

    # Signal 1: Schnelle Ausführung (2s) -> EXECUTED_FAST & FAVORABLE (Long)
    # Trend-Following Setup
    _set_scenario(
        signal_id=1,
        reaction_type=ReactionType.EXECUTED_FAST,
        outcome_type=OutcomeType.FAVORABLE,
        default_id="DISC_EXEC_GOOD",
    )
    signals_df.loc[signals_df["signal_id"] == 1, "scenario_psych_tags"] = (
        "DISCIPLINE,TREND_FOLLOW,TRUST_SYSTEM"
    )

    # Signal 2: Zu späte Ausführung (12s) -> EXECUTED_SLOW & ADVERSE
    # Breakout Setup, aber zu spät (FOMO-Indikator)
    _set_scenario(
        signal_id=2,
        reaction_type=ReactionType.EXECUTED_SLOW,
        outcome_type=OutcomeType.ADVERSE,
    )
    signals_df.loc[signals_df["signal_id"] == 2, "scenario_psych_tags"] = (
        "HESITATION,BREAKOUT,TOO_SLOW,FOMO"
    )

    # Signal 3: Keine Action (verpasst) -> MISSED & FAVORABLE
    # Counter-Trend Setup, aus Angst verpasst
    _set_scenario(
        signal_id=3,
        reaction_type=ReactionType.MISSED,
        outcome_type=OutcomeType.FAVORABLE,
    )
    signals_df.loc[signals_df["signal_id"] == 3, "scenario_psych_tags"] = (
        "FEAR,REGRET,COUNTER_TREND,HESITATION"
    )

    # Signal 4: Rechtzeitige Ausführung (3s), Short-Signal -> EXECUTED_FAST & FAVORABLE
    # Exit-Setup (Take-Profit)
    _set_scenario(
        signal_id=4,
        reaction_type=ReactionType.EXECUTED_FAST,
        outcome_type=OutcomeType.FAVORABLE,
        default_id="DISC_EXEC_GOOD_SHORT",
    )
    signals_df.loc[signals_df["signal_id"] == 4, "scenario_psych_tags"] = (
        "DISCIPLINE,EXIT,CONFIDENCE,TAKE_PROFIT"
    )

    # Signal 5: Bewusst übersprungen -> SKIPPED & ADVERSE
    # Re-Entry Setup, aus Verlustangst geskippt
    _set_scenario(
        signal_id=5,
        reaction_type=ReactionType.SKIPPED,
        outcome_type=OutcomeType.ADVERSE,
    )
    signals_df.loc[signals_df["signal_id"] == 5, "scenario_psych_tags"] = (
        "DISCIPLINE,REENTRY,RISK_AVERSION_OK,SCALING"
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

    trades_df = (
        pd.DataFrame.from_records(trade_rows)
        if trade_rows
        else pd.DataFrame(columns=["timestamp", "price", "qty", "pnl", "fees"])
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

    # 2a) Trigger-Reaktions-Statistiken berechnen (NEU: v1)
    print("[DRILL] Berechne Trigger-Reaktions-Statistiken ...")
    reaction_cfg = TriggerReactionConfig(
        impulsive_threshold_ms=300,
        late_threshold_ms=3000,
        consider_skipped=True,
    )
    reaction_records = compute_reaction_records(
        signals_df=signals_df,
        actions_df=actions_df,
        config=reaction_cfg,
        session_id=session_id,
    )
    reaction_summary = summarize_reaction_records(reaction_records)
    reaction_records_df = reaction_records_to_df(reaction_records)
    print(
        f"[DRILL] Reaktions-Stats: {reaction_summary.count_total} Signale, "
        f"{reaction_summary.count_impulsive} impulsive, "
        f"{reaction_summary.count_on_time} on-time, "
        f"{reaction_summary.count_late} late, "
        f"{reaction_summary.count_missed} missed."
    )

    # 2b) Execution-Latenz-Statistiken berechnen (NEU: v1)
    print("[DRILL] Berechne Execution-Latenz-Statistiken ...")
    latency_timestamps = create_latency_timestamps_from_trades_and_signals(
        trades_df=trades_df,
        signals_df=signals_df,
        session_id=session_id,
    )
    latency_measures = [compute_latency_measures(ts) for ts in latency_timestamps]
    latency_summary = summarize_latency(latency_measures)
    latency_measures_df = latency_measures_to_df(latency_measures)
    if latency_summary.mean_trigger_delay_ms is not None:
        print(
            f"[DRILL] Latenz-Stats: {latency_summary.count_orders} Orders, "
            f"Avg Trigger-Delay: {latency_summary.mean_trigger_delay_ms:.1f} ms."
        )
    else:
        print(
            f"[DRILL] Latenz-Stats: {latency_summary.count_orders} Orders "
            f"(keine Signal-Timestamps vorhanden)."
        )

    # 2c) DataFrames in Session-Report-Ordner speichern
    session_report_dir = base_reports_dir / session_id
    session_report_dir.mkdir(parents=True, exist_ok=True)

    if not reaction_records_df.empty:
        csv_path = session_report_dir / "reaction_records.csv"
        reaction_records_df.to_csv(csv_path, index=False)
        print(f"[DRILL] Gespeichert: {csv_path}")

    if not latency_measures_df.empty:
        csv_path = session_report_dir / "latency_measures.csv"
        latency_measures_df.to_csv(csv_path, index=False)
        print(f"[DRILL] Gespeichert: {csv_path}")

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

    # 3) Reports erzeugen (Offline-Paper + Trigger-Report)
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
            # NEU: Speed-Metriken hinzufügen
            "reaction_summary": reaction_summary_to_dict(reaction_summary),
            "latency_summary": latency_summary_to_dict(latency_summary),
        },
    )

    paper_report = result_paths.get("paper_report")
    trigger_report = result_paths.get("trigger_report")

    print("[DRILL] Fertig.")
    if paper_report:
        print(f"[REPORT] Offline-Paper-Report:       {paper_report}")
    if trigger_report:
        print(f"[REPORT] Trigger-Training-Report:     {trigger_report}")
    if not trigger_report:
        print("[WARN] Kein Trigger-Report erzeugt (keine Trigger-Events?).")

    # NEU: Ausgabe der Speed-Metriken
    print("\n" + "=" * 70)
    print("📊 TRIGGER-GESCHWINDIGKEITS-METRIKEN")
    print("=" * 70)
    print(f"Total Signale:        {reaction_summary.count_total}")
    print(f"  - Impulsive:        {reaction_summary.count_impulsive}")
    print(f"  - On-Time:          {reaction_summary.count_on_time}")
    print(f"  - Late:             {reaction_summary.count_late}")
    print(f"  - Missed:           {reaction_summary.count_missed}")
    print(f"  - Skipped:          {reaction_summary.count_skipped}")
    if reaction_summary.mean_reaction_ms:
        print(f"Avg Reaktionszeit:    {reaction_summary.mean_reaction_ms:.1f} ms")
        print(f"Median Reaktionszeit: {reaction_summary.median_reaction_ms:.1f} ms")
        print(f"P90 Reaktionszeit:    {reaction_summary.p90_reaction_ms:.1f} ms")

    print("\n" + "=" * 70)
    print("⚡ EXECUTION-LATENZ-METRIKEN")
    print("=" * 70)
    print(f"Total Orders:         {latency_summary.count_orders}")
    if latency_summary.mean_trigger_delay_ms:
        print(f"Avg Trigger-Delay:    {latency_summary.mean_trigger_delay_ms:.1f} ms")
        print(f"Median Trigger-Delay: {latency_summary.median_trigger_delay_ms:.1f} ms")
    if latency_summary.mean_send_to_first_fill_ms:
        print(f"Avg Send-to-Fill:     {latency_summary.mean_send_to_first_fill_ms:.1f} ms")
        print(f"P90 Send-to-Fill:     {latency_summary.p90_send_to_first_fill_ms:.1f} ms")
    if latency_summary.mean_slippage:
        print(f"Avg Slippage:         {latency_summary.mean_slippage:.4f}")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
