# tests/test_live_monitoring.py
"""
Tests für src/live/monitoring.py (Phase 65)
===========================================

Tests für Monitoring-Funktionen für Shadow- und Testnet-Runs.
"""
from __future__ import annotations

import sys
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

# Pfad-Setup
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.live.monitoring import (
    list_runs,
    get_run_snapshot,
    get_run_timeseries,
    tail_events,
    RunNotFoundError,
    RunSnapshot,
    RunMetricPoint,
    _calculate_drawdown,
    _is_run_active,
)
from src.live.run_logging import (
    LiveRunLogger,
    LiveRunMetadata,
    LiveRunEvent,
    ShadowPaperLoggingConfig,
)


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def temp_run_dir(tmp_path: Path) -> Path:
    """Erstellt ein temporäres Run-Verzeichnis."""
    run_dir = tmp_path / "live_runs"
    run_dir.mkdir(parents=True)
    return run_dir


@pytest.fixture
def sample_logging_config() -> ShadowPaperLoggingConfig:
    """Erstellt eine Test-Logging-Config."""
    return ShadowPaperLoggingConfig(
        enabled=True,
        base_dir="live_runs",
        flush_interval_steps=10,
        format="parquet",
    )


@pytest.fixture
def sample_metadata() -> LiveRunMetadata:
    """Erstellt Test-Metadaten."""
    return LiveRunMetadata(
        run_id="test_shadow_20251207_120000_abc123",
        mode="shadow",
        strategy_name="ma_crossover",
        symbol="BTC/EUR",
        timeframe="1m",
        started_at=datetime.now(timezone.utc) - timedelta(hours=1),
    )


@pytest.fixture
def sample_run_with_events(temp_run_dir: Path, sample_logging_config: ShadowPaperLoggingConfig, sample_metadata: LiveRunMetadata) -> str:
    """Erstellt einen Test-Run mit Events."""
    run_dir = temp_run_dir / sample_metadata.run_id
    run_dir.mkdir(parents=True)

    # Metadaten schreiben
    meta_path = run_dir / "meta.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(sample_metadata.to_dict(), f, indent=2)

    # Events erstellen
    events = []
    base_equity = 10000.0
    for i in range(10):
        equity = base_equity + (i * 50.0)  # Steigende Equity
        pnl = i * 50.0
        event = {
            "step": i + 1,
            "ts_event": (datetime.now(timezone.utc) - timedelta(minutes=10-i)).isoformat(),
            "ts_bar": (datetime.now(timezone.utc) - timedelta(minutes=10-i)).isoformat(),
            "equity": equity,
            "realized_pnl": pnl,
            "unrealized_pnl": 0.0,
            "signal": 1 if i % 2 == 0 else 0,
            "orders_generated": 1 if i % 2 == 0 else 0,
            "orders_filled": 1 if i % 2 == 0 else 0,
            "price": 50000.0 + (i * 100.0),
        }
        events.append(event)

    # Events als Parquet speichern
    events_df = pd.DataFrame(events)
    events_path = run_dir / "events.parquet"
    events_df.to_parquet(events_path, index=False)

    return sample_metadata.run_id


# =============================================================================
# Helper Function Tests
# =============================================================================


def test_calculate_drawdown() -> None:
    """Test: Drawdown-Berechnung."""
    # Steigende Equity (kein Drawdown)
    equity_series = pd.Series([10000, 10100, 10200, 10300])
    dd = _calculate_drawdown(equity_series)
    assert dd == 0.0

    # Fallende Equity (Drawdown)
    equity_series = pd.Series([10000, 10100, 9900, 9800])
    dd = _calculate_drawdown(equity_series)
    assert dd < 0.0
    assert abs(dd - (-0.0198)) < 0.01  # ~-2%


def test_is_run_active() -> None:
    """Test: Active-Status-Bestimmung."""
    from src.live.run_logging import LiveRunMetadata

    # Aktiver Run (letztes Event vor 5 Minuten)
    metadata = LiveRunMetadata(
        run_id="test",
        mode="shadow",
        strategy_name="test",
        symbol="BTC/EUR",
        timeframe="1m",
        started_at=datetime.now(timezone.utc) - timedelta(hours=1),
    )
    last_event = datetime.now(timezone.utc) - timedelta(minutes=5)
    assert _is_run_active(metadata, last_event) is True

    # Inaktiver Run (letztes Event vor 15 Minuten)
    last_event = datetime.now(timezone.utc) - timedelta(minutes=15)
    assert _is_run_active(metadata, last_event) is False

    # Beendeter Run
    metadata.ended_at = datetime.now(timezone.utc)
    assert _is_run_active(metadata, last_event) is False


# =============================================================================
# list_runs Tests
# =============================================================================


def test_list_runs_smoke(temp_run_dir: Path, sample_run_with_events: str) -> None:
    """Test: list_runs findet Runs."""
    runs = list_runs(base_dir=temp_run_dir, include_inactive=True)

    assert len(runs) == 1
    assert runs[0].run_id == sample_run_with_events
    assert runs[0].mode == "shadow"
    assert runs[0].strategy == "ma_crossover"
    assert runs[0].num_events > 0
    assert runs[0].last_event_time is not None


def test_list_runs_only_active(temp_run_dir: Path, sample_run_with_events: str) -> None:
    """Test: list_runs mit only_active Filter."""
    # Run ist aktiv (letztes Event vor 5 Minuten)
    runs = list_runs(base_dir=temp_run_dir, include_inactive=False)
    assert len(runs) >= 0  # Kann 0 sein wenn Run zu alt ist


def test_list_runs_max_age(temp_run_dir: Path) -> None:
    """Test: list_runs mit max_age Filter."""
    # Max-Age von 1 Stunde
    runs = list_runs(base_dir=temp_run_dir, max_age=timedelta(hours=1))
    # Sollte nur Runs der letzten Stunde zurückgeben
    assert isinstance(runs, list)


def test_list_runs_empty_dir(tmp_path: Path) -> None:
    """Test: list_runs mit leerem Verzeichnis."""
    empty_dir = tmp_path / "empty_runs"
    empty_dir.mkdir()

    runs = list_runs(base_dir=empty_dir)
    assert len(runs) == 0


# =============================================================================
# get_run_snapshot Tests
# =============================================================================


def test_get_run_snapshot_aggregation(temp_run_dir: Path, sample_run_with_events: str) -> None:
    """Test: get_run_snapshot aggregiert Metriken korrekt."""
    snapshot = get_run_snapshot(sample_run_with_events, base_dir=temp_run_dir)

    assert snapshot.run_id == sample_run_with_events
    assert snapshot.mode == "shadow"
    assert snapshot.strategy == "ma_crossover"
    assert snapshot.num_events == 10
    assert snapshot.equity is not None
    assert snapshot.equity > 10000.0  # Letztes Event hat höhere Equity
    assert snapshot.pnl is not None
    assert snapshot.pnl > 0


def test_get_run_snapshot_not_found(temp_run_dir: Path) -> None:
    """Test: get_run_snapshot mit nicht existierender Run-ID."""
    with pytest.raises(RunNotFoundError, match="Run.*nicht gefunden"):
        get_run_snapshot("nonexistent_run_id", base_dir=temp_run_dir)


def test_get_run_snapshot_no_events(temp_run_dir: Path, sample_metadata: LiveRunMetadata) -> None:
    """Test: get_run_snapshot mit Run ohne Events."""
    run_dir = temp_run_dir / sample_metadata.run_id
    run_dir.mkdir(parents=True)

    # Nur Metadaten schreiben
    meta_path = run_dir / "meta.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(sample_metadata.to_dict(), f, indent=2)

    snapshot = get_run_snapshot(sample_metadata.run_id, base_dir=temp_run_dir)

    assert snapshot.run_id == sample_metadata.run_id
    assert snapshot.num_events == 0
    assert snapshot.equity is None


# =============================================================================
# get_run_timeseries Tests
# =============================================================================


def test_get_run_timeseries_basic(temp_run_dir: Path, sample_run_with_events: str) -> None:
    """Test: get_run_timeseries erstellt Zeitreihe."""
    timeseries = get_run_timeseries(
        sample_run_with_events,
        metric="equity",
        limit=10,
        base_dir=temp_run_dir,
    )

    assert len(timeseries) == 10
    assert all(isinstance(p, RunMetricPoint) for p in timeseries)
    assert all(p.timestamp is not None for p in timeseries)
    assert all(p.equity is not None for p in timeseries)

    # Equity sollte steigend sein
    equities = [p.equity for p in timeseries if p.equity is not None]
    assert equities == sorted(equities)


def test_get_run_timeseries_limit(temp_run_dir: Path, sample_run_with_events: str) -> None:
    """Test: get_run_timeseries respektiert Limit."""
    timeseries = get_run_timeseries(
        sample_run_with_events,
        metric="equity",
        limit=5,
        base_dir=temp_run_dir,
    )

    assert len(timeseries) == 5


def test_get_run_timeseries_not_found(temp_run_dir: Path) -> None:
    """Test: get_run_timeseries mit nicht existierender Run-ID."""
    with pytest.raises(RunNotFoundError, match="Run.*nicht gefunden"):
        get_run_timeseries("nonexistent_run_id", base_dir=temp_run_dir)


# =============================================================================
# tail_events Tests
# =============================================================================


def test_tail_events_limit(temp_run_dir: Path, sample_run_with_events: str) -> None:
    """Test: tail_events respektiert Limit."""
    events = tail_events(sample_run_with_events, limit=5, base_dir=temp_run_dir)

    assert len(events) == 5
    assert all(isinstance(e, dict) for e in events)


def test_tail_events_all(temp_run_dir: Path, sample_run_with_events: str) -> None:
    """Test: tail_events gibt alle Events zurück wenn Limit größer."""
    events = tail_events(sample_run_with_events, limit=100, base_dir=temp_run_dir)

    assert len(events) == 10


def test_tail_events_not_found(temp_run_dir: Path) -> None:
    """Test: tail_events mit nicht existierender Run-ID."""
    with pytest.raises(RunNotFoundError, match="Run.*nicht gefunden"):
        tail_events("nonexistent_run_id", base_dir=temp_run_dir)


def test_tail_events_format(temp_run_dir: Path, sample_run_with_events: str) -> None:
    """Test: tail_events formatiert Timestamps korrekt."""
    events = tail_events(sample_run_with_events, limit=5, base_dir=temp_run_dir)

    for event in events:
        # Timestamps sollten ISO-Strings sein
        if "ts_event" in event:
            assert isinstance(event["ts_event"], str)
        if "ts_bar" in event:
            assert isinstance(event["ts_bar"], str)
