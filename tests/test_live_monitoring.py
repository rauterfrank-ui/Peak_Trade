# tests/test_live_monitoring.py
"""
Tests für src/live/monitoring.py (Phase 33)

Testet die Monitoring-Funktionen für Shadow-/Paper-Runs:
- LiveRunSnapshot Laden
- LiveRunTailRow Laden
- Config Laden
- Render-Funktionen
"""
from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
import pytest

from src.live.monitoring import (
    LiveMonitoringConfig,
    LiveRunSnapshot,
    LiveRunTailRow,
    load_live_monitoring_config,
    load_run_snapshot,
    load_run_tail,
    get_latest_run_dir,
    render_summary,
    render_tail,
    Colors,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def sample_metadata() -> Dict[str, Any]:
    """Sample Run-Metadaten."""
    return {
        "run_id": "20251204_180000_paper_ma_crossover_BTC-EUR_1m",
        "mode": "paper",
        "strategy_name": "ma_crossover",
        "symbol": "BTC/EUR",
        "timeframe": "1m",
        "started_at": "2025-12-04T18:00:00+00:00",
        "ended_at": None,
        "config_snapshot": {},
        "notes": "",
    }


@pytest.fixture
def sample_events_data() -> List[Dict[str, Any]]:
    """Sample Events als Liste von Dicts."""
    base_ts = datetime(2025, 12, 4, 18, 0, 0, tzinfo=timezone.utc)
    events = []

    for i in range(20):
        ts = base_ts.replace(minute=i)
        event = {
            "step": i + 1,
            "ts_bar": ts.isoformat(),
            "ts_event": ts.isoformat(),
            "price": 40000.0 + i * 10,
            "open": 40000.0 + i * 10,
            "high": 40050.0 + i * 10,
            "low": 39950.0 + i * 10,
            "close": 40000.0 + i * 10,
            "volume": 100.0,
            "position_size": 0.1 if i >= 5 else 0.0,
            "cash": 9000.0 if i >= 5 else 10000.0,
            "equity": 10000.0 + i * 5,
            "realized_pnl": 50.0 if i >= 10 else 0.0,
            "unrealized_pnl": 25.0 if i >= 5 else 0.0,
            "signal": 1 if i >= 5 else 0,
            "signal_changed": i == 5,
            "orders_generated": 1 if i == 5 else 0,
            "orders_filled": 1 if i == 5 else 0,
            "orders_rejected": 0,
            "orders_blocked": 1 if i == 15 else 0,
            "risk_allowed": i != 15,
            "risk_reasons": "max_total_exposure" if i == 15 else "",
        }
        events.append(event)

    return events


@pytest.fixture
def temp_run_dir(sample_metadata: Dict[str, Any], sample_events_data: List[Dict[str, Any]]) -> Path:
    """Erstellt ein temporäres Run-Verzeichnis mit Testdaten."""
    with tempfile.TemporaryDirectory() as tmpdir:
        run_dir = Path(tmpdir) / sample_metadata["run_id"]
        run_dir.mkdir(parents=True)

        # meta.json schreiben
        meta_path = run_dir / "meta.json"
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(sample_metadata, f)

        # events.parquet schreiben
        events_df = pd.DataFrame(sample_events_data)
        events_path = run_dir / "events.parquet"
        events_df.to_parquet(events_path, index=False)

        yield run_dir


@pytest.fixture
def temp_empty_run_dir(sample_metadata: Dict[str, Any]) -> Path:
    """Erstellt ein Run-Verzeichnis ohne Events."""
    with tempfile.TemporaryDirectory() as tmpdir:
        run_dir = Path(tmpdir) / sample_metadata["run_id"]
        run_dir.mkdir(parents=True)

        # Nur meta.json
        meta_path = run_dir / "meta.json"
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(sample_metadata, f)

        yield run_dir


@pytest.fixture
def temp_base_dir_with_runs(sample_metadata: Dict[str, Any], sample_events_data: List[Dict[str, Any]]) -> Path:
    """Erstellt Base-Dir mit mehreren Runs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)

        # Mehrere Runs anlegen
        run_ids = [
            "20251201_100000_paper_test_BTC-EUR_1m",
            "20251202_100000_paper_test_BTC-EUR_1m",
            "20251204_180000_paper_ma_crossover_BTC-EUR_1m",
        ]

        for run_id in run_ids:
            run_dir = base_dir / run_id
            run_dir.mkdir(parents=True)

            meta = sample_metadata.copy()
            meta["run_id"] = run_id

            with open(run_dir / "meta.json", "w", encoding="utf-8") as f:
                json.dump(meta, f)

            # Events für letzten Run
            if run_id == run_ids[-1]:
                events_df = pd.DataFrame(sample_events_data)
                events_df.to_parquet(run_dir / "events.parquet", index=False)

        yield base_dir


# =============================================================================
# Config Tests
# =============================================================================


class TestLiveMonitoringConfig:
    """Tests für LiveMonitoringConfig."""

    def test_default_values(self) -> None:
        """Test Default-Werte."""
        cfg = LiveMonitoringConfig()
        assert cfg.default_interval_seconds == 2.0
        assert cfg.default_tail_rows == 15
        assert cfg.use_colors is True

    def test_custom_values(self) -> None:
        """Test Custom-Werte."""
        cfg = LiveMonitoringConfig(
            default_interval_seconds=5.0,
            default_tail_rows=20,
            use_colors=False,
        )
        assert cfg.default_interval_seconds == 5.0
        assert cfg.default_tail_rows == 20
        assert cfg.use_colors is False

    def test_load_from_config(self) -> None:
        """Test Laden aus PeakConfig-artigem Objekt."""
        # Mock PeakConfig mit get()
        class MockConfig:
            def get(self, path: str, default: Any = None) -> Any:
                values = {
                    "live_monitoring.default_interval_seconds": 3.0,
                    "live_monitoring.default_tail_rows": 25,
                    "live_monitoring.use_colors": False,
                }
                return values.get(path, default)

        cfg = load_live_monitoring_config(MockConfig())
        assert cfg.default_interval_seconds == 3.0
        assert cfg.default_tail_rows == 25
        assert cfg.use_colors is False


# =============================================================================
# Snapshot Tests
# =============================================================================


class TestLoadRunSnapshot:
    """Tests für load_run_snapshot()."""

    def test_load_snapshot_basic(self, temp_run_dir: Path) -> None:
        """Test grundlegendes Snapshot-Laden."""
        snapshot = load_run_snapshot(temp_run_dir)

        assert snapshot.run_id == "20251204_180000_paper_ma_crossover_BTC-EUR_1m"
        assert snapshot.mode == "paper"
        assert snapshot.strategy_name == "ma_crossover"
        assert snapshot.symbol == "BTC/EUR"
        assert snapshot.timeframe == "1m"

    def test_load_snapshot_total_steps(self, temp_run_dir: Path) -> None:
        """Test Anzahl Steps."""
        snapshot = load_run_snapshot(temp_run_dir)
        assert snapshot.total_steps == 20

    def test_load_snapshot_total_orders(self, temp_run_dir: Path) -> None:
        """Test Anzahl Orders."""
        snapshot = load_run_snapshot(temp_run_dir)
        # Nur bei Step 5 wurde eine Order generiert
        assert snapshot.total_orders == 1

    def test_load_snapshot_blocked_orders(self, temp_run_dir: Path) -> None:
        """Test Anzahl blockierter Orders."""
        snapshot = load_run_snapshot(temp_run_dir)
        # Bei Step 15 wurde eine Order blockiert
        assert snapshot.total_blocked_orders == 1

    def test_load_snapshot_last_values(self, temp_run_dir: Path) -> None:
        """Test letzte Werte aus Events."""
        snapshot = load_run_snapshot(temp_run_dir)

        # Letzte Zeile (Step 20)
        assert snapshot.last_price is not None
        assert snapshot.last_price == pytest.approx(40190.0, rel=1e-2)  # 40000 + 19*10

        assert snapshot.equity is not None
        assert snapshot.equity == pytest.approx(10095.0, rel=1e-2)  # 10000 + 19*5

        assert snapshot.position_size is not None
        assert snapshot.position_size == pytest.approx(0.1, rel=1e-2)

    def test_load_snapshot_empty_events(self, temp_empty_run_dir: Path) -> None:
        """Test Snapshot ohne Events."""
        snapshot = load_run_snapshot(temp_empty_run_dir)

        assert snapshot.run_id == "20251204_180000_paper_ma_crossover_BTC-EUR_1m"
        assert snapshot.total_steps == 0
        assert snapshot.total_orders == 0
        assert snapshot.total_blocked_orders == 0
        assert snapshot.last_price is None
        assert snapshot.equity is None

    def test_load_snapshot_not_found(self, tmp_path: Path) -> None:
        """Test FileNotFoundError bei fehlendem Run."""
        with pytest.raises(FileNotFoundError):
            load_run_snapshot(tmp_path / "nonexistent")


# =============================================================================
# Tail Tests
# =============================================================================


class TestLoadRunTail:
    """Tests für load_run_tail()."""

    def test_load_tail_default(self, temp_run_dir: Path) -> None:
        """Test Tail mit Default-Anzahl."""
        tail = load_run_tail(temp_run_dir, n=15)
        assert len(tail) == 15

    def test_load_tail_all(self, temp_run_dir: Path) -> None:
        """Test Tail größer als Events."""
        tail = load_run_tail(temp_run_dir, n=50)
        assert len(tail) == 20  # Nur 20 Events vorhanden

    def test_load_tail_small(self, temp_run_dir: Path) -> None:
        """Test Tail mit kleiner Anzahl."""
        tail = load_run_tail(temp_run_dir, n=3)
        assert len(tail) == 3

    def test_load_tail_row_structure(self, temp_run_dir: Path) -> None:
        """Test TailRow-Struktur."""
        tail = load_run_tail(temp_run_dir, n=1)
        assert len(tail) == 1

        row = tail[0]
        assert isinstance(row, LiveRunTailRow)
        assert row.ts_bar is not None
        assert row.equity is not None
        assert isinstance(row.orders_count, int)
        assert isinstance(row.risk_allowed, bool)

    def test_load_tail_chronological_order(self, temp_run_dir: Path) -> None:
        """Test chronologische Reihenfolge."""
        tail = load_run_tail(temp_run_dir, n=5)

        # Prüfe dass Equity aufsteigend ist (in unseren Testdaten)
        equities = [r.equity for r in tail if r.equity is not None]
        assert equities == sorted(equities)

    def test_load_tail_risk_blocked(self, temp_run_dir: Path) -> None:
        """Test Risk-Blocked-Erkennung."""
        tail = load_run_tail(temp_run_dir, n=20)

        # Finde die blockierte Zeile (Step 15, Index 14)
        blocked_rows = [r for r in tail if not r.risk_allowed]
        assert len(blocked_rows) == 1
        assert blocked_rows[0].risk_reasons == "max_total_exposure"

    def test_load_tail_empty(self, temp_empty_run_dir: Path) -> None:
        """Test Tail ohne Events."""
        tail = load_run_tail(temp_empty_run_dir, n=10)
        assert len(tail) == 0


# =============================================================================
# Helper Tests
# =============================================================================


class TestGetLatestRunDir:
    """Tests für get_latest_run_dir()."""

    def test_latest_run(self, temp_base_dir_with_runs: Path) -> None:
        """Test neuesten Run finden."""
        latest = get_latest_run_dir(temp_base_dir_with_runs)
        assert latest is not None
        # Neuester Run (alphabetisch sortiert, reverse)
        assert latest.name == "20251204_180000_paper_ma_crossover_BTC-EUR_1m"

    def test_empty_base_dir(self, tmp_path: Path) -> None:
        """Test leeres Base-Dir."""
        latest = get_latest_run_dir(tmp_path)
        assert latest is None

    def test_nonexistent_base_dir(self, tmp_path: Path) -> None:
        """Test nicht existierendes Base-Dir."""
        latest = get_latest_run_dir(tmp_path / "nonexistent")
        assert latest is None


# =============================================================================
# Render Tests
# =============================================================================


class TestRenderSummary:
    """Tests für render_summary()."""

    def test_render_summary_basic(self, temp_run_dir: Path) -> None:
        """Test Summary-Rendering ohne Fehler."""
        snapshot = load_run_snapshot(temp_run_dir)
        output = render_summary(snapshot, use_colors=False)

        assert "RUN SUMMARY" in output
        assert snapshot.run_id in output
        assert snapshot.strategy_name in output
        assert snapshot.symbol in output

    def test_render_summary_with_colors(self, temp_run_dir: Path) -> None:
        """Test Summary-Rendering mit Farben."""
        snapshot = load_run_snapshot(temp_run_dir)
        output = render_summary(snapshot, use_colors=True)

        # ANSI-Codes sollten vorhanden sein
        assert "\033[" in output

    def test_render_summary_no_colors(self, temp_run_dir: Path) -> None:
        """Test Summary-Rendering ohne Farben."""
        snapshot = load_run_snapshot(temp_run_dir)
        output = render_summary(snapshot, use_colors=False)

        # Keine ANSI-Codes
        assert "\033[" not in output

    def test_render_summary_blocked_warning(self, temp_run_dir: Path) -> None:
        """Test Blocked-Orders-Warnung."""
        snapshot = load_run_snapshot(temp_run_dir)
        output = render_summary(snapshot, use_colors=False)

        # Blocked Orders vorhanden
        assert "blocked" in output.lower()
        assert "1" in output  # 1 blocked order


class TestRenderTail:
    """Tests für render_tail()."""

    def test_render_tail_basic(self, temp_run_dir: Path) -> None:
        """Test Tail-Rendering ohne Fehler."""
        tail = load_run_tail(temp_run_dir, n=5)
        output = render_tail(tail, use_colors=False)

        assert "EVENTS" in output
        assert "equity" in output.lower()

    def test_render_tail_with_colors(self, temp_run_dir: Path) -> None:
        """Test Tail-Rendering mit Farben."""
        tail = load_run_tail(temp_run_dir, n=5)
        output = render_tail(tail, use_colors=True)

        # ANSI-Codes sollten vorhanden sein
        assert "\033[" in output

    def test_render_tail_risk_indicator(self, temp_run_dir: Path) -> None:
        """Test Risk-Indikator im Tail."""
        tail = load_run_tail(temp_run_dir, n=20)
        output = render_tail(tail, use_colors=False)

        # BLOCK sollte erscheinen
        assert "BLOCK" in output or "block" in output.lower()

    def test_render_tail_empty(self) -> None:
        """Test leerer Tail."""
        output = render_tail([], use_colors=False)
        assert "0 EVENTS" in output


# =============================================================================
# Integration Tests
# =============================================================================


class TestMonitoringIntegration:
    """Integration Tests für das Monitoring-Modul."""

    def test_full_workflow(self, temp_run_dir: Path) -> None:
        """Test kompletter Workflow: Snapshot + Tail + Render."""
        # Snapshot laden
        snapshot = load_run_snapshot(temp_run_dir)
        assert snapshot.total_steps == 20

        # Tail laden
        tail = load_run_tail(temp_run_dir, n=10)
        assert len(tail) == 10

        # Rendern
        summary = render_summary(snapshot, use_colors=False)
        tail_output = render_tail(tail, use_colors=False)

        # Beide Outputs sollten valide sein
        assert len(summary) > 100
        assert len(tail_output) > 50

    def test_multiple_loads(self, temp_run_dir: Path) -> None:
        """Test mehrfaches Laden (Simulation von Refresh-Loop)."""
        for _ in range(5):
            snapshot = load_run_snapshot(temp_run_dir)
            tail = load_run_tail(temp_run_dir, n=5)

            assert snapshot.total_steps == 20
            assert len(tail) == 5
