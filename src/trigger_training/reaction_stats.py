"""
Trigger Reaction Stats – Operator-Geschwindigkeits-Metriken (v1)

Dieses Modul ermöglicht die Messung und Analyse von Trigger-Reaktionszeiten
im Offline Trigger Training. Es kategorisiert Reaktionen in:
  - IMPULSIVE: < impulsive_threshold_ms (z.B. < 300 ms)
  - ON_TIME: innerhalb normaler Range (z.B. 300 ms - 3 s)
  - LATE: > late_threshold_ms (z.B. > 3 s)
  - MISSED: keine Aktion erfolgt
  - SKIPPED: bewusst übersprungen (z.B. SKIPPED user_action)

Alle Metriken sind rein offline / paper / drill – keine Live-Order-Execution.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any

import pandas as pd
import numpy as np


class TriggerReactionCategory(str, Enum):
    """Kategorien der Trigger-Reaktionsgeschwindigkeit."""
    IMPULSIVE = "IMPULSIVE"     # Sehr schnelle Reaktion (< 200-300 ms)
    ON_TIME = "ON_TIME"         # Normale Reaktionszeit (0.3-3 s)
    LATE = "LATE"               # Zu späte Reaktion (> 3 s)
    MISSED = "MISSED"           # Keine Aktion erfolgt
    SKIPPED = "SKIPPED"         # Bewusst übersprungen


@dataclass
class TriggerReactionConfig:
    """Konfiguration für Trigger-Reaktions-Analyse.
    
    Attributes
    ----------
    impulsive_threshold_ms : int
        Schwellenwert für impulsive Reaktionen in Millisekunden (Default: 300)
    late_threshold_ms : int
        Schwellenwert für späte Reaktionen in Millisekunden (Default: 3000)
    consider_skipped : bool
        Ob SKIPPED-Actions als eigene Kategorie behandelt werden (Default: True)
    """
    impulsive_threshold_ms: int = 300
    late_threshold_ms: int = 3000
    consider_skipped: bool = True


@dataclass
class TriggerReactionRecord:
    """Ein einzelner Trigger-Reaktions-Datensatz.
    
    Attributes
    ----------
    signal_id : int
        Eindeutige Signal-ID
    session_id : str
        Session-Identifikator
    signal_timestamp : pd.Timestamp
        Zeitstempel des Signals
    first_action_timestamp : Optional[pd.Timestamp]
        Zeitstempel der ersten Aktion (None bei MISSED)
    reaction_ms : Optional[float]
        Reaktionszeit in Millisekunden (None bei MISSED)
    category : TriggerReactionCategory
        Reaktions-Kategorie
    signal_type : Optional[str]
        Signal-Typ (z.B. "ENTER_LONG", "ENTER_SHORT")
    user_action : Optional[str]
        User-Action (z.B. "EXECUTED", "SKIPPED")
    symbol : Optional[str]
        Trading-Symbol
    """
    signal_id: int
    session_id: str
    signal_timestamp: pd.Timestamp
    first_action_timestamp: Optional[pd.Timestamp]
    reaction_ms: Optional[float]
    category: TriggerReactionCategory
    signal_type: Optional[str] = None
    user_action: Optional[str] = None
    symbol: Optional[str] = None


@dataclass
class TriggerReactionSummary:
    """Aggregierte Trigger-Reaktions-Statistiken.
    
    Attributes
    ----------
    count_total : int
        Gesamtanzahl Signale
    count_impulsive : int
        Anzahl impulsiver Reaktionen
    count_on_time : int
        Anzahl rechtzeitiger Reaktionen
    count_late : int
        Anzahl später Reaktionen
    count_missed : int
        Anzahl verpasster Signale
    count_skipped : int
        Anzahl bewusst übersprungener Signale
    mean_reaction_ms : Optional[float]
        Durchschnittliche Reaktionszeit (nur mit Aktion)
    median_reaction_ms : Optional[float]
        Median Reaktionszeit (nur mit Aktion)
    std_reaction_ms : Optional[float]
        Standardabweichung Reaktionszeit (nur mit Aktion)
    p50_reaction_ms : Optional[float]
        50. Perzentil (Median) Reaktionszeit
    p90_reaction_ms : Optional[float]
        90. Perzentil Reaktionszeit
    p95_reaction_ms : Optional[float]
        95. Perzentil Reaktionszeit
    p99_reaction_ms : Optional[float]
        99. Perzentil Reaktionszeit
    min_reaction_ms : Optional[float]
        Minimale Reaktionszeit
    max_reaction_ms : Optional[float]
        Maximale Reaktionszeit
    """
    count_total: int = 0
    count_impulsive: int = 0
    count_on_time: int = 0
    count_late: int = 0
    count_missed: int = 0
    count_skipped: int = 0
    mean_reaction_ms: Optional[float] = None
    median_reaction_ms: Optional[float] = None
    std_reaction_ms: Optional[float] = None
    p50_reaction_ms: Optional[float] = None
    p90_reaction_ms: Optional[float] = None
    p95_reaction_ms: Optional[float] = None
    p99_reaction_ms: Optional[float] = None
    min_reaction_ms: Optional[float] = None
    max_reaction_ms: Optional[float] = None


def compute_reaction_records(
    signals_df: pd.DataFrame,
    actions_df: pd.DataFrame,
    config: Optional[TriggerReactionConfig] = None,
    session_id: str = "default",
) -> List[TriggerReactionRecord]:
    """Berechnet Trigger-Reaktions-Records aus Signals und Actions DataFrames.
    
    Diese Funktion matcht jedes Signal mit der ersten relevanten Aktion und
    kategorisiert die Reaktionsgeschwindigkeit.
    
    Parameters
    ----------
    signals_df : pd.DataFrame
        Signals DataFrame mit Spalten:
        - signal_id (int): Eindeutige Signal-ID
        - timestamp (datetime): Signal-Zeitstempel
        - recommended_action (str): Empfohlene Aktion
        - optional: symbol, signal_state
    actions_df : pd.DataFrame
        Actions DataFrame mit Spalten:
        - signal_id (int): Referenz zu signals_df
        - timestamp (datetime): Action-Zeitstempel
        - user_action (str): User-Reaktion (z.B. "EXECUTED", "SKIPPED")
    config : Optional[TriggerReactionConfig]
        Konfiguration (Default: TriggerReactionConfig())
    session_id : str
        Session-Identifikator (Default: "default")
    
    Returns
    -------
    List[TriggerReactionRecord]
        Liste von Reaktions-Records
    
    Notes
    -----
    - "Relevante" Aktionen = EXECUTED, SKIPPED (keine reinen Info-Events)
    - Zeitdifferenzen werden in Millisekunden berechnet
    - SKIPPED-Actions werden separat kategorisiert (falls config.consider_skipped=True)
    
    Examples
    --------
    >>> signals_df = pd.DataFrame({
    ...     "signal_id": [1, 2, 3],
    ...     "timestamp": pd.date_range("2025-01-01", periods=3, freq="1min"),
    ...     "recommended_action": ["ENTER_LONG", "ENTER_SHORT", "ENTER_LONG"]
    ... })
    >>> actions_df = pd.DataFrame({
    ...     "signal_id": [1, 2],
    ...     "timestamp": [
    ...         signals_df["timestamp"].iloc[0] + pd.Timedelta(milliseconds=100),
    ...         signals_df["timestamp"].iloc[1] + pd.Timedelta(seconds=5)
    ...     ],
    ...     "user_action": ["EXECUTED", "EXECUTED"]
    ... })
    >>> records = compute_reaction_records(signals_df, actions_df)
    >>> len(records)
    3
    >>> records[0].category
    <TriggerReactionCategory.IMPULSIVE: 'IMPULSIVE'>
    >>> records[2].category
    <TriggerReactionCategory.MISSED: 'MISSED'>
    """
    if config is None:
        config = TriggerReactionConfig()
    
    if signals_df.empty:
        return []
    
    # Kopie erstellen, um Original nicht zu verändern
    signals = signals_df.copy()
    signals["timestamp"] = pd.to_datetime(signals["timestamp"])
    
    # signal_id sicherstellen
    if "signal_id" not in signals.columns:
        signals = signals.reset_index().rename(columns={"index": "signal_id"})
    
    # Actions vorbereiten
    if actions_df.empty:
        actions = pd.DataFrame(columns=["signal_id", "timestamp", "user_action"])
    else:
        actions = actions_df.copy()
        actions["timestamp"] = pd.to_datetime(actions["timestamp"])
        
        # Erste relevante Aktion pro Signal
        # Sortiere nach timestamp und nimm erste Aktion
        actions = (
            actions.sort_values("timestamp")
            .groupby("signal_id", as_index=False)
            .first()
        )
    
    # Merge Signals + Actions
    merged = signals.merge(
        actions, 
        on="signal_id", 
        how="left", 
        suffixes=("_signal", "_action")
    )
    
    records: List[TriggerReactionRecord] = []
    
    for _, row in merged.iterrows():
        signal_id = int(row["signal_id"])
        
        # Timestamps extrahieren
        ts_signal = pd.to_datetime(
            row.get("timestamp_signal", row.get("timestamp"))
        )
        
        ts_action_val = row.get("timestamp_action")
        if pd.isna(ts_action_val):
            ts_action = None
        else:
            ts_action = pd.to_datetime(ts_action_val)
        
        # User-Action extrahieren
        user_action_val = row.get("user_action")
        if pd.isna(user_action_val):
            user_action = None
        else:
            user_action = str(user_action_val)
        
        # Reaktionszeit berechnen
        reaction_ms: Optional[float] = None
        if ts_action is not None:
            reaction_td = ts_action - ts_signal
            reaction_ms = reaction_td.total_seconds() * 1000.0
        
        # Kategorie bestimmen
        category = _determine_category(
            user_action=user_action,
            reaction_ms=reaction_ms,
            config=config,
        )
        
        # Optional: Symbol, Signal-Typ
        signal_type = row.get("recommended_action")
        if pd.isna(signal_type):
            signal_type = None
        else:
            signal_type = str(signal_type)
        
        symbol = row.get("symbol")
        if pd.isna(symbol):
            symbol = None
        else:
            symbol = str(symbol)
        
        records.append(
            TriggerReactionRecord(
                signal_id=signal_id,
                session_id=session_id,
                signal_timestamp=ts_signal,
                first_action_timestamp=ts_action,
                reaction_ms=reaction_ms,
                category=category,
                signal_type=signal_type,
                user_action=user_action,
                symbol=symbol,
            )
        )
    
    return records


def _determine_category(
    user_action: Optional[str],
    reaction_ms: Optional[float],
    config: TriggerReactionConfig,
) -> TriggerReactionCategory:
    """Bestimmt Reaktions-Kategorie basierend auf Aktion und Reaktionszeit.
    
    Parameters
    ----------
    user_action : Optional[str]
        User-Action String (z.B. "EXECUTED", "SKIPPED")
    reaction_ms : Optional[float]
        Reaktionszeit in Millisekunden
    config : TriggerReactionConfig
        Konfiguration mit Schwellenwerten
    
    Returns
    -------
    TriggerReactionCategory
        Kategorisierte Reaktion
    """
    # Keine Aktion -> MISSED
    if user_action is None or reaction_ms is None:
        return TriggerReactionCategory.MISSED
    
    # SKIPPED-Action
    if config.consider_skipped and "SKIPPED" in user_action.upper():
        return TriggerReactionCategory.SKIPPED
    
    # Geschwindigkeits-basierte Kategorisierung
    if reaction_ms < config.impulsive_threshold_ms:
        return TriggerReactionCategory.IMPULSIVE
    elif reaction_ms > config.late_threshold_ms:
        return TriggerReactionCategory.LATE
    else:
        return TriggerReactionCategory.ON_TIME


def summarize_reaction_records(
    records: List[TriggerReactionRecord]
) -> TriggerReactionSummary:
    """Aggregiert Reaktions-Records zu einer Summary-Statistik.
    
    Parameters
    ----------
    records : List[TriggerReactionRecord]
        Liste von Reaktions-Records
    
    Returns
    -------
    TriggerReactionSummary
        Aggregierte Statistiken
    
    Examples
    --------
    >>> records = [...]  # Liste von TriggerReactionRecord
    >>> summary = summarize_reaction_records(records)
    >>> summary.count_total
    100
    >>> summary.mean_reaction_ms
    1250.5
    """
    if not records:
        return TriggerReactionSummary()
    
    # Kategorie-Zählung
    count_impulsive = sum(1 for r in records if r.category == TriggerReactionCategory.IMPULSIVE)
    count_on_time = sum(1 for r in records if r.category == TriggerReactionCategory.ON_TIME)
    count_late = sum(1 for r in records if r.category == TriggerReactionCategory.LATE)
    count_missed = sum(1 for r in records if r.category == TriggerReactionCategory.MISSED)
    count_skipped = sum(1 for r in records if r.category == TriggerReactionCategory.SKIPPED)
    
    # Reaktionszeiten (nur nicht-None-Werte)
    reaction_times = [r.reaction_ms for r in records if r.reaction_ms is not None]
    
    # Statistiken berechnen
    mean_ms = None
    median_ms = None
    std_ms = None
    p50_ms = None
    p90_ms = None
    p95_ms = None
    p99_ms = None
    min_ms = None
    max_ms = None
    
    if reaction_times:
        arr = np.array(reaction_times)
        mean_ms = float(np.mean(arr))
        median_ms = float(np.median(arr))
        std_ms = float(np.std(arr))
        p50_ms = float(np.percentile(arr, 50))
        p90_ms = float(np.percentile(arr, 90))
        p95_ms = float(np.percentile(arr, 95))
        p99_ms = float(np.percentile(arr, 99))
        min_ms = float(np.min(arr))
        max_ms = float(np.max(arr))
    
    return TriggerReactionSummary(
        count_total=len(records),
        count_impulsive=count_impulsive,
        count_on_time=count_on_time,
        count_late=count_late,
        count_missed=count_missed,
        count_skipped=count_skipped,
        mean_reaction_ms=mean_ms,
        median_reaction_ms=median_ms,
        std_reaction_ms=std_ms,
        p50_reaction_ms=p50_ms,
        p90_reaction_ms=p90_ms,
        p95_reaction_ms=p95_ms,
        p99_reaction_ms=p99_ms,
        min_reaction_ms=min_ms,
        max_reaction_ms=max_ms,
    )


def reaction_records_to_df(
    records: List[TriggerReactionRecord]
) -> pd.DataFrame:
    """Konvertiert Reaktions-Records in ein pandas DataFrame.
    
    Parameters
    ----------
    records : List[TriggerReactionRecord]
        Liste von Reaktions-Records
    
    Returns
    -------
    pd.DataFrame
        DataFrame mit allen Record-Feldern
    
    Examples
    --------
    >>> df = reaction_records_to_df(records)
    >>> df.columns
    Index(['signal_id', 'session_id', 'signal_timestamp', ...])
    """
    if not records:
        return pd.DataFrame(columns=[
            "signal_id", "session_id", "signal_timestamp",
            "first_action_timestamp", "reaction_ms", "category",
            "signal_type", "user_action", "symbol"
        ])
    
    data = []
    for rec in records:
        data.append({
            "signal_id": rec.signal_id,
            "session_id": rec.session_id,
            "signal_timestamp": rec.signal_timestamp,
            "first_action_timestamp": rec.first_action_timestamp,
            "reaction_ms": rec.reaction_ms,
            "category": rec.category.value,
            "signal_type": rec.signal_type,
            "user_action": rec.user_action,
            "symbol": rec.symbol,
        })
    
    return pd.DataFrame(data)


def reaction_summary_to_dict(
    summary: TriggerReactionSummary
) -> Dict[str, Any]:
    """Konvertiert TriggerReactionSummary in ein Dictionary (für JSON/HTML).
    
    Parameters
    ----------
    summary : TriggerReactionSummary
        Summary-Objekt
    
    Returns
    -------
    Dict[str, Any]
        Dictionary mit allen Summary-Feldern
    """
    return {
        "count_total": summary.count_total,
        "count_impulsive": summary.count_impulsive,
        "count_on_time": summary.count_on_time,
        "count_late": summary.count_late,
        "count_missed": summary.count_missed,
        "count_skipped": summary.count_skipped,
        "mean_reaction_ms": summary.mean_reaction_ms,
        "median_reaction_ms": summary.median_reaction_ms,
        "std_reaction_ms": summary.std_reaction_ms,
        "p50_reaction_ms": summary.p50_reaction_ms,
        "p90_reaction_ms": summary.p90_reaction_ms,
        "p95_reaction_ms": summary.p95_reaction_ms,
        "p99_reaction_ms": summary.p99_reaction_ms,
        "min_reaction_ms": summary.min_reaction_ms,
        "max_reaction_ms": summary.max_reaction_ms,
    }
