from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from src.reporting.trigger_training_report import TriggerOutcome, TriggerTrainingEvent


@dataclass
class TriggerTrainingHookConfig:
    """Konfiguration für Trigger-Training-Hooks.

    Diese v0-Config ist bewusst einfach gehalten und soll es erlauben,
    aus Signals/Actions/Prices reproduzierbar TriggerTrainingEvents zu generieren.
    """

    lookahead_bars: int = 20
    #: Ab dieser Reaktionszeit in Sekunden gilt eine ansonsten "korrekte" Aktion als LATE.
    late_threshold_s: float = 5.0
    #: Schwelle für "Pain Points": bei pnl_after_bars > pain_threshold werden Missed/Late Events getaggt.
    pain_threshold: float = 0.0


def _compute_pnl_after_bars(
    prices: pd.DataFrame,
    ts: pd.Timestamp,
    *,
    symbol: str | None,
    lookahead_bars: int,
    recommended_action: str,
) -> float:
    """Berechnet eine einfache PnL nach lookahead_bars Bars ab ts.

    Erwartete Struktur von prices:
      - Index: DatetimeIndex ODER Spalte 'timestamp'
      - Spalte 'close'
      - optional: Spalte 'symbol', um nach Symbol zu filtern
    """
    if prices is None or prices.empty or "close" not in prices.columns:
        return 0.0

    df = prices

    # Optional nach Symbol filtern, falls Spalte vorhanden
    if symbol is not None and "symbol" in df.columns:
        df = df[df["symbol"] == symbol]
    if df.empty:
        return 0.0

    # Index auf Timestamp bringen
    if not isinstance(df.index, pd.DatetimeIndex):
        if "timestamp" in df.columns:
            df = df.copy()
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df = df.set_index("timestamp").sort_index()
        else:
            return 0.0
    else:
        df = df.sort_index()

    if df.empty:
        return 0.0

    # Position für Signalzeitpunkt finden
    idx_pos = df.index.searchsorted(ts)
    if idx_pos == len(df.index):
        # Signal liegt nach dem letzten Preis -> fallback: letzte Zeile
        idx_pos = len(df.index) - 1

    future_pos = min(idx_pos + lookahead_bars, len(df.index) - 1)

    price_entry = float(df["close"].iloc[idx_pos])
    price_future = float(df["close"].iloc[future_pos])

    # Einfache Richtungslogik basierend auf recommended_action
    ra = (recommended_action or "").upper()
    direction = 0.0
    if "ENTER_LONG" in ra or "OPEN_LONG" in ra:
        direction = 1.0
    elif "ENTER_SHORT" in ra or "OPEN_SHORT" in ra:
        direction = -1.0

    if direction == 0.0:
        # Für Exits/Neutralität kein PnL-Blick, v0.
        return 0.0

    return (price_future - price_entry) * direction


def _classify_outcome(
    recommended_action: str,
    user_action: str | None,
    reaction_delay_s: float | None,
    *,
    late_threshold_s: float,
) -> TriggerOutcome:
    """Klassifiziert das Outcome (HIT, MISSED, LATE, FOMO, RULE_BREAK, OTHER)."""
    rec = (recommended_action or "").upper()
    act = (user_action or "").upper()

    if not rec:
        return TriggerOutcome.OTHER

    # Keine Aktion -> MISSED
    if not act:
        return TriggerOutcome.MISSED

    # sehr simple Heuristiken für FOMO / Regelbruch
    if "FOMO" in act:
        return TriggerOutcome.FOMO
    if "RULE_BREAK" in act or "OVERSIZE" in act or "OVERSIZED" in act:
        return TriggerOutcome.RULE_BREAK

    # Timing-basierte Klassifikation
    if reaction_delay_s is not None and reaction_delay_s > late_threshold_s:
        return TriggerOutcome.LATE

    return TriggerOutcome.HIT


def build_trigger_training_events_from_dfs(
    signals: pd.DataFrame,
    actions: pd.DataFrame | None,
    prices: pd.DataFrame | None,
    config: TriggerTrainingHookConfig | None = None,
) -> list[TriggerTrainingEvent]:
    """Erzeugt TriggerTrainingEvent-Objekte aus Signals-, Actions- und Price-DataFrames.

    V0-Schema (bewusst einfach, damit die Pipeline es leicht befüllen kann):

    signals:
        - Spalten:
            - 'signal_id' (optional, int; wenn fehlt, wird aus Index erzeugt)
            - 'timestamp' (datetime64/pandas.Timestamp)
            - 'symbol' (str)
            - 'signal_state' (int, z.B. -1/0/1)
            - 'recommended_action' (str, z.B. 'ENTER_LONG', 'EXIT_LONG', ...)
    actions:
        - Spalten:
            - 'signal_id' (entsprechend signals.signal_id)
            - 'timestamp' (Zeitpunkt der User-Aktion)
            - 'user_action' (str; frei, z.B. 'EXECUTED', 'SKIPPED', 'EXECUTED_FOMO')
            - optional: 'note' (str)
        - Wenn mehrere Aktionen pro signal_id vorkommen, wird v0 die erste pro Signal verwenden.
    prices:
        - Index: DatetimeIndex ODER Spalte 'timestamp' (datetime)
        - Spalten:
            - 'close'
            - optional 'symbol'

    Rückgabe:
        Liste von TriggerTrainingEvent-Objekten (geeignet für build_trigger_training_report).
    """
    if config is None:
        config = TriggerTrainingHookConfig()

    if signals is None or signals.empty:
        return []

    s_df = signals.copy()

    # signal_id sicherstellen
    if "signal_id" not in s_df.columns:
        s_df = s_df.reset_index().rename(columns={"index": "signal_id"})

    a_df: pd.DataFrame | None
    if actions is not None and not actions.empty:
        a_df = actions.copy()
        if "signal_id" not in a_df.columns:
            # Ohne signal_id können wir nicht sauber joinen -> v0 ignoriert Actions
            a_df = None
        else:
            a_df["timestamp"] = pd.to_datetime(a_df["timestamp"])
            # erste Aktion pro signal_id
            a_df = (
                a_df.sort_values("timestamp")
                .groupby("signal_id", as_index=False)
                .first()
            )
    else:
        a_df = None

    # Merge Signals + Actions
    if a_df is not None:
        merged = s_df.merge(a_df, on="signal_id", how="left", suffixes=("_sig", "_act"))
    else:
        merged = s_df.copy()
        merged["timestamp_act"] = pd.NaT
        merged["user_action"] = None
        merged["note"] = None

    events: list[TriggerTrainingEvent] = []

    for _, row in merged.iterrows():
        # Signal-Basis
        ts_signal = pd.to_datetime(
            row["timestamp_sig"] if "timestamp_sig" in row else row["timestamp"]
        )
        symbol = row.get("symbol", "") or ""
        signal_state = int(row.get("signal_state", 0))
        recommended_action = str(row.get("recommended_action", "") or "")

        # Action-Teil
        ts_action_val = row.get("timestamp_act", None)
        if pd.isna(ts_action_val):
            ts_action = None
        else:
            ts_action = pd.to_datetime(ts_action_val)

        user_action_val = row.get("user_action", None)
        if pd.isna(user_action_val):
            user_action = None
        else:
            user_action = str(user_action_val)

        # Reaktionszeit
        if ts_action is not None:
            reaction_delay_s: float | None = (ts_action - ts_signal).total_seconds()
        else:
            reaction_delay_s = None

        # Outcome-Klassifikation
        outcome = _classify_outcome(
            recommended_action=recommended_action,
            user_action=user_action,
            reaction_delay_s=reaction_delay_s,
            late_threshold_s=config.late_threshold_s,
        )

        # PnL-Betrachtung
        pnl_after = 0.0
        if prices is not None:
            pnl_after = _compute_pnl_after_bars(
                prices=prices,
                ts=ts_signal,
                symbol=symbol,
                lookahead_bars=config.lookahead_bars,
                recommended_action=recommended_action,
            )

        # Tags: Kombiniere aus DataFrame (falls vorhanden) und automatisch generierte Tags
        tags: list[str] = []

        # Tags aus DataFrame übernehmen (z.B. scenario_psych_tags)
        tags_from_df = row.get("scenario_psych_tags", "")
        if tags_from_df and not pd.isna(tags_from_df):
            tags_list = [t.strip() for t in str(tags_from_df).split(",") if t.strip()]
            tags.extend(tags_list)

        # Automatisch generierte Tags basierend auf Outcome
        if outcome == TriggerOutcome.MISSED and pnl_after > config.pain_threshold:
            tags.append("missed_opportunity")
        if outcome == TriggerOutcome.LATE and pnl_after > config.pain_threshold:
            tags.append("late_entry")
        if outcome == TriggerOutcome.HIT:
            tags.append("rule_follow")

        note_val = row.get("note", "")
        if pd.isna(note_val):
            note_val = ""

        events.append(
            TriggerTrainingEvent(
                timestamp=ts_signal,
                symbol=symbol,
                signal_state=signal_state,
                recommended_action=recommended_action,
                user_action=user_action or "",
                outcome=outcome,
                reaction_delay_s=reaction_delay_s or 0.0,
                pnl_after_bars=float(pnl_after),
                tags=tags,
                note=str(note_val),
            )
        )

    return events
