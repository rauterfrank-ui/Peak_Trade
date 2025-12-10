"""
Unit-Tests für session_data_store.py

Testet das Speichern und Laden von vollständigen Session-Rohdaten.
"""
import pandas as pd
import pytest
from pathlib import Path
import tempfile

from src.trigger_training.session_data_store import (
    save_session_data,
    load_session_data,
    list_session_ids,
    session_exists,
    SessionMetadata,
)


@pytest.fixture
def temp_sessions_dir(tmp_path):
    """Temporäres Verzeichnis für Test-Sessions."""
    return tmp_path / "test_sessions"


@pytest.fixture
def sample_session_data():
    """Generiert Sample-Daten für eine Test-Session."""
    # Prices
    start_ts = pd.Timestamp("2025-01-01T00:00:00Z")
    periods = 10
    idx = pd.date_range(start_ts, periods=periods, freq="1min", tz="UTC")
    prices_df = pd.DataFrame({
        "timestamp": idx,
        "symbol": "BTCEUR",
        "close": 30000.0 + pd.Series(range(periods)) * 10.0,
    })
    
    # Signals
    signals_df = pd.DataFrame({
        "signal_id": [1, 2],
        "timestamp": [idx[2], idx[7]],
        "symbol": ["BTCEUR", "BTCEUR"],
        "signal_state": [1, -1],
        "recommended_action": ["ENTER_LONG", "ENTER_SHORT"],
    })
    
    # Actions
    actions_df = pd.DataFrame({
        "signal_id": [1, 2],
        "timestamp": [idx[2] + pd.Timedelta(seconds=2), idx[7] + pd.Timedelta(seconds=5)],
        "user_action": ["EXECUTED", "EXECUTED"],
        "note": ["Quick execution", "Delayed execution"],
    })
    
    # Trades
    trades_df = pd.DataFrame({
        "timestamp": [idx[2], idx[7]],
        "price": [30020.0, 30070.0],
        "qty": [0.01, -0.01],
        "pnl": [50.0, -20.0],
        "fees": [0.1, 0.1],
    })
    
    return {
        "prices": prices_df,
        "signals": signals_df,
        "actions": actions_df,
        "trades": trades_df,
        "start_ts": start_ts,
        "end_ts": idx[-1],
    }


def test_save_and_load_session_data(temp_sessions_dir, sample_session_data):
    """Test: Speichern und Laden einer Session."""
    session_id = "TEST_SESSION_001"
    
    # Speichern
    session_dir = save_session_data(
        session_id=session_id,
        prices_df=sample_session_data["prices"],
        signals_df=sample_session_data["signals"],
        actions_df=sample_session_data["actions"],
        trades_df=sample_session_data["trades"],
        start_ts=sample_session_data["start_ts"],
        end_ts=sample_session_data["end_ts"],
        symbol="BTCEUR",
        timeframe="1m",
        strategy="test_strategy",
        base_dir=temp_sessions_dir,
    )
    
    assert session_dir.exists()
    assert (session_dir / "prices.parquet").exists()
    assert (session_dir / "signals.parquet").exists()
    assert (session_dir / "actions.parquet").exists()
    assert (session_dir / "trades.parquet").exists()
    assert (session_dir / "meta.json").exists()
    
    # Laden
    loaded_data = load_session_data(session_id, base_dir=temp_sessions_dir)
    
    assert "prices" in loaded_data
    assert "signals" in loaded_data
    assert "actions" in loaded_data
    assert "trades" in loaded_data
    assert "meta" in loaded_data
    
    # Vergleiche DataFrames
    pd.testing.assert_frame_equal(loaded_data["prices"], sample_session_data["prices"])
    pd.testing.assert_frame_equal(loaded_data["signals"], sample_session_data["signals"])
    pd.testing.assert_frame_equal(loaded_data["actions"], sample_session_data["actions"])
    pd.testing.assert_frame_equal(loaded_data["trades"], sample_session_data["trades"])
    
    # Prüfe Metadaten
    meta = loaded_data["meta"]
    assert meta.session_id == session_id
    assert meta.symbol == "BTCEUR"
    assert meta.timeframe == "1m"
    assert meta.strategy == "test_strategy"
    assert meta.n_signals == 2
    assert meta.n_trades == 2
    assert abs(meta.total_pnl - 30.0) < 0.01  # 50 - 20 = 30


def test_list_session_ids(temp_sessions_dir, sample_session_data):
    """Test: Liste alle Session-IDs auf."""
    # Erstelle mehrere Sessions
    session_ids = ["SESSION_A", "SESSION_B", "SESSION_C"]
    
    for sid in session_ids:
        save_session_data(
            session_id=sid,
            prices_df=sample_session_data["prices"],
            signals_df=sample_session_data["signals"],
            actions_df=sample_session_data["actions"],
            trades_df=sample_session_data["trades"],
            start_ts=sample_session_data["start_ts"],
            end_ts=sample_session_data["end_ts"],
            symbol="BTCEUR",
            base_dir=temp_sessions_dir,
        )
    
    # Liste Sessions auf
    listed_ids = list_session_ids(base_dir=temp_sessions_dir)
    
    assert len(listed_ids) == 3
    assert set(listed_ids) == set(session_ids)
    assert listed_ids == sorted(session_ids)  # Sollte alphabetisch sortiert sein


def test_session_exists(temp_sessions_dir, sample_session_data):
    """Test: Prüfe ob Session existiert."""
    session_id = "EXISTING_SESSION"
    
    # Vor dem Speichern: existiert nicht
    assert not session_exists(session_id, base_dir=temp_sessions_dir)
    
    # Speichern
    save_session_data(
        session_id=session_id,
        prices_df=sample_session_data["prices"],
        signals_df=sample_session_data["signals"],
        actions_df=sample_session_data["actions"],
        trades_df=sample_session_data["trades"],
        start_ts=sample_session_data["start_ts"],
        end_ts=sample_session_data["end_ts"],
        symbol="BTCEUR",
        base_dir=temp_sessions_dir,
    )
    
    # Nach dem Speichern: existiert
    assert session_exists(session_id, base_dir=temp_sessions_dir)
    assert not session_exists("NON_EXISTING", base_dir=temp_sessions_dir)


def test_load_nonexistent_session_raises_error(temp_sessions_dir):
    """Test: Laden einer nicht-existierenden Session wirft FileNotFoundError."""
    with pytest.raises(FileNotFoundError, match="Session 'GHOST_SESSION' nicht gefunden"):
        load_session_data("GHOST_SESSION", base_dir=temp_sessions_dir)


def test_save_session_with_extra_meta(temp_sessions_dir, sample_session_data):
    """Test: Speichern mit zusätzlichen Metadaten."""
    session_id = "META_TEST_SESSION"
    extra_meta = {
        "drill_type": "trigger_training",
        "operator": "test_user",
        "notes": "Test-Session mit extra Metadaten",
    }
    
    save_session_data(
        session_id=session_id,
        prices_df=sample_session_data["prices"],
        signals_df=sample_session_data["signals"],
        actions_df=sample_session_data["actions"],
        trades_df=sample_session_data["trades"],
        start_ts=sample_session_data["start_ts"],
        end_ts=sample_session_data["end_ts"],
        symbol="BTCEUR",
        extra_meta=extra_meta,
        base_dir=temp_sessions_dir,
    )
    
    loaded_data = load_session_data(session_id, base_dir=temp_sessions_dir)
    meta = loaded_data["meta"]
    
    assert meta.extra == extra_meta
    assert meta.extra["drill_type"] == "trigger_training"
    assert meta.extra["operator"] == "test_user"


def test_empty_dataframes(temp_sessions_dir):
    """Test: Speichern und Laden mit leeren DataFrames."""
    session_id = "EMPTY_SESSION"
    start_ts = pd.Timestamp("2025-01-01T00:00:00Z")
    end_ts = pd.Timestamp("2025-01-01T01:00:00Z")
    
    # Leere DataFrames mit korrektem Schema
    prices_df = pd.DataFrame(columns=["timestamp", "symbol", "close"])
    signals_df = pd.DataFrame(columns=["signal_id", "timestamp", "symbol", "signal_state", "recommended_action"])
    actions_df = pd.DataFrame(columns=["signal_id", "timestamp", "user_action", "note"])
    trades_df = pd.DataFrame(columns=["timestamp", "price", "qty", "pnl", "fees"])
    
    save_session_data(
        session_id=session_id,
        prices_df=prices_df,
        signals_df=signals_df,
        actions_df=actions_df,
        trades_df=trades_df,
        start_ts=start_ts,
        end_ts=end_ts,
        symbol="BTCEUR",
        base_dir=temp_sessions_dir,
    )
    
    loaded_data = load_session_data(session_id, base_dir=temp_sessions_dir)
    
    assert len(loaded_data["prices"]) == 0
    assert len(loaded_data["signals"]) == 0
    assert len(loaded_data["actions"]) == 0
    assert len(loaded_data["trades"]) == 0
    assert loaded_data["meta"].n_signals == 0
    assert loaded_data["meta"].n_trades == 0
    assert loaded_data["meta"].total_pnl == 0.0
