"""
Unit-Test für die Loader-Funktion des Offline-Trigger-Training-Drills.

Testet, dass load_data_for_session():
  1. Echte Daten aus dem Session Data Store lädt (wenn vorhanden)
  2. Auf synthetische Demo-Daten zurückfällt (wenn nicht gefunden)
  3. Alle erwarteten Szenarien abdeckt:
     - Schnelle Ausführung
     - Zu späte Ausführung
     - Verpasster Trade (keine Action)
     - Rechtzeitig ausgeführtes Signal
     - Bewusst übersprungenes Signal (SKIPPED)
"""

import sys
from pathlib import Path

import pandas as pd
import pytest

# Import der Funktion aus dem Drill-Skript
# Füge scripts/ zum Path hinzu
repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root / "scripts"))

from run_offline_trigger_training_drill_example import load_data_for_session

# Import für echte Session-Tests
from src.trigger_training.session_data_store import (
    save_session_data,
    DEFAULT_SESSIONS_BASE_DIR,
)


def test_load_data_for_session_demo_shapes_and_scenarios():
    """
    Test: Demo-Daten haben korrekte Shapes und decken alle Szenarien ab.
    """
    # Lade Demo-Daten
    trades_df, signals_df, actions_df, prices_df, start_ts, end_ts = load_data_for_session(
        session_id="test_session_demo"
    )

    # --- Basic type checks ---
    assert isinstance(prices_df, pd.DataFrame), "prices_df muss DataFrame sein"
    assert isinstance(signals_df, pd.DataFrame), "signals_df muss DataFrame sein"
    assert isinstance(actions_df, pd.DataFrame), "actions_df muss DataFrame sein"
    assert isinstance(trades_df, pd.DataFrame), "trades_df muss DataFrame sein"
    assert isinstance(start_ts, pd.Timestamp), "start_ts muss Timestamp sein"
    assert isinstance(end_ts, pd.Timestamp), "end_ts muss Timestamp sein"

    # --- Prices: 60 Minuten synthetisch ---
    assert len(prices_df) == 60, "Erwarte 60 Preis-Bars (1 Stunde bei 1m)"
    assert "timestamp" in prices_df.columns
    assert "close" in prices_df.columns

    # --- Signals: genau 5 Demo-Signale ---
    assert len(signals_df) == 5, "Erwarte exakt 5 Demo-Signale"
    assert "signal_id" in signals_df.columns
    assert "timestamp" in signals_df.columns
    assert "signal_state" in signals_df.columns
    assert "recommended_action" in signals_df.columns

    # --- Actions: verschiedene Szenarien abgedeckt ---
    # Erwartete Szenarien:
    # - Signal 1: EXECUTED (schnell, 2s)
    # - Signal 2: EXECUTED (spät, 12s)
    # - Signal 3: MISSED (keine Action)
    # - Signal 4: EXECUTED (rechtzeitig, 3s)
    # - Signal 5: SKIPPED (bewusst übersprungen)

    assert "signal_id" in actions_df.columns
    assert "user_action" in actions_df.columns
    assert len(actions_df) == 4, "Erwarte 4 Actions (Signal 3 ist MISSED)"

    # Prüfe vorhandene Action-Typen
    user_actions = set(actions_df["user_action"].str.upper())
    assert "EXECUTED" in user_actions, "Muss mindestens 1 EXECUTED-Action haben"
    assert "SKIPPED" in user_actions, "Muss mindestens 1 SKIPPED-Action haben"

    # Zähle EXECUTED-Actions (sollte 3 sein: Signal 1, 2, 4)
    executed_count = (actions_df["user_action"].str.upper() == "EXECUTED").sum()
    assert executed_count == 3, f"Erwarte 3 EXECUTED-Actions, habe {executed_count}"

    # Zähle SKIPPED-Actions (sollte 1 sein: Signal 5)
    skipped_count = (actions_df["user_action"].str.upper() == "SKIPPED").sum()
    assert skipped_count == 1, f"Erwarte 1 SKIPPED-Action, habe {skipped_count}"

    # Verpasste Signals: Signal 3 hat keine zugehörige Action
    signal_ids = set(signals_df["signal_id"])
    action_signal_ids = set(actions_df["signal_id"])
    missed_signal_ids = signal_ids - action_signal_ids
    assert len(missed_signal_ids) == 1, "Erwarte exakt 1 verpasstes Signal"
    assert 3 in missed_signal_ids, "Signal 3 sollte verpasst sein"

    # --- Trades: nur für EXECUTED-Actions ---
    # Erwarte 3 Trades (für Signale 1, 2, 4)
    assert len(trades_df) == 3, f"Erwarte 3 Trades, habe {len(trades_df)}"

    # Prüfe Trade-Schema
    assert "timestamp" in trades_df.columns
    assert "pnl" in trades_df.columns
    assert "fees" in trades_df.columns

    print("✅ test_load_data_for_session_demo_shapes_and_scenarios passed")


def test_load_data_for_session_timing_scenarios():
    """
    Test: Prüfe, dass die Timing-Szenarien korrekt modelliert sind.
    """
    trades_df, signals_df, actions_df, prices_df, start_ts, end_ts = load_data_for_session(
        session_id="test_timing"
    )

    # Finde Signal 1 (schnelle Reaktion, 2s)
    sig1 = signals_df.loc[signals_df["signal_id"] == 1].iloc[0]
    act1 = actions_df.loc[actions_df["signal_id"] == 1].iloc[0]
    delay1 = (act1["timestamp"] - sig1["timestamp"]).total_seconds()
    assert 1.5 <= delay1 <= 2.5, f"Signal 1: Erwarte ~2s Delay, habe {delay1}s"

    # Finde Signal 2 (späte Reaktion, 12s)
    sig2 = signals_df.loc[signals_df["signal_id"] == 2].iloc[0]
    act2 = actions_df.loc[actions_df["signal_id"] == 2].iloc[0]
    delay2 = (act2["timestamp"] - sig2["timestamp"]).total_seconds()
    assert 11.5 <= delay2 <= 12.5, f"Signal 2: Erwarte ~12s Delay, habe {delay2}s"

    # Finde Signal 5 (SKIPPED, 0s Delay)
    sig5 = signals_df.loc[signals_df["signal_id"] == 5].iloc[0]
    act5 = actions_df.loc[actions_df["signal_id"] == 5].iloc[0]
    delay5 = (act5["timestamp"] - sig5["timestamp"]).total_seconds()
    assert abs(delay5) < 1.0, f"Signal 5: Erwarte ~0s Delay (SKIPPED), habe {delay5}s"

    print("✅ test_load_data_for_session_timing_scenarios passed")


def test_load_data_for_session_signal_directions():
    """
    Test: Prüfe, dass LONG und SHORT Signale vorhanden sind.
    """
    trades_df, signals_df, actions_df, prices_df, start_ts, end_ts = load_data_for_session(
        session_id="test_directions"
    )

    # Prüfe Signal States
    signal_states = signals_df["signal_state"].tolist()
    assert 1 in signal_states, "Muss mindestens 1 LONG Signal (state=1) haben"
    assert -1 in signal_states, "Muss mindestens 1 SHORT Signal (state=-1) haben"

    # Erwartete Verteilung: 3x LONG, 2x SHORT (gemäß Demo-Implementierung)
    long_count = (signals_df["signal_state"] == 1).sum()
    short_count = (signals_df["signal_state"] == -1).sum()
    assert long_count == 3, f"Erwarte 3 LONG Signale, habe {long_count}"
    assert short_count == 2, f"Erwarte 2 SHORT Signale, habe {short_count}"

    print("✅ test_load_data_for_session_signal_directions passed")


def test_load_real_session_from_store(tmp_path):
    """
    Test: Laden einer echten Session aus dem Session Data Store.
    """
    # Erstelle eine Test-Session im temporären Store
    session_id = "REAL_TEST_SESSION"
    start_ts = pd.Timestamp("2025-01-20T12:00:00Z")
    periods = 20
    idx = pd.date_range(start_ts, periods=periods, freq="1min", tz="UTC")
    
    prices_df = pd.DataFrame({
        "timestamp": idx,
        "symbol": "ETHEUR",
        "close": 2000.0 + pd.Series(range(periods)) * 5.0,
    })
    
    signals_df = pd.DataFrame({
        "signal_id": [101, 102, 103],
        "timestamp": [idx[3], idx[10], idx[17]],
        "symbol": ["ETHEUR", "ETHEUR", "ETHEUR"],
        "signal_state": [1, -1, 1],
        "recommended_action": ["ENTER_LONG", "ENTER_SHORT", "ENTER_LONG"],
    })
    
    actions_df = pd.DataFrame({
        "signal_id": [101, 102],
        "timestamp": [idx[3] + pd.Timedelta(seconds=3), idx[10] + pd.Timedelta(seconds=8)],
        "user_action": ["EXECUTED", "EXECUTED"],
        "note": ["Good timing", "Delayed entry"],
    })
    
    trades_df = pd.DataFrame({
        "timestamp": [idx[3], idx[10]],
        "price": [2015.0, 2050.0],
        "qty": [0.1, -0.1],
        "pnl": [100.0, -50.0],
        "fees": [1.0, 1.0],
    })
    
    # Speichere Session im temporären Verzeichnis
    # WICHTIG: Wir müssen temporär den DEFAULT_SESSIONS_BASE_DIR überschreiben
    # oder einen benutzerdefinierten Store-Pfad verwenden
    
    # Für diesen Test verwenden wir den echten Store, aber eine eindeutige Session-ID
    import uuid
    unique_session_id = f"TEST_{uuid.uuid4().hex[:8]}"
    
    save_session_data(
        session_id=unique_session_id,
        prices_df=prices_df,
        signals_df=signals_df,
        actions_df=actions_df,
        trades_df=trades_df,
        start_ts=start_ts,
        end_ts=idx[-1],
        symbol="ETHEUR",
        timeframe="1m",
        strategy="test_strategy",
    )
    
    try:
        # Lade die Session mit load_data_for_session()
        loaded_trades, loaded_signals, loaded_actions, loaded_prices, loaded_start, loaded_end = (
            load_data_for_session(unique_session_id)
        )
        
        # Vergleiche geladene Daten
        assert len(loaded_signals) == 3, f"Erwarte 3 Signale, habe {len(loaded_signals)}"
        assert len(loaded_trades) == 2, f"Erwarte 2 Trades, habe {len(loaded_trades)}"
        assert len(loaded_actions) == 2, f"Erwarte 2 Actions, habe {len(loaded_actions)}"
        assert len(loaded_prices) == 20, f"Erwarte 20 Preis-Bars, habe {len(loaded_prices)}"
        
        # Prüfe Signal-IDs
        assert set(loaded_signals["signal_id"]) == {101, 102, 103}
        
        # Prüfe Symbol
        assert loaded_signals["symbol"].iloc[0] == "ETHEUR"
        
        print(f"✅ test_load_real_session_from_store passed (Session: {unique_session_id})")
    
    finally:
        # Cleanup: Entferne Test-Session
        import shutil
        session_dir = DEFAULT_SESSIONS_BASE_DIR / unique_session_id
        if session_dir.exists():
            shutil.rmtree(session_dir)
