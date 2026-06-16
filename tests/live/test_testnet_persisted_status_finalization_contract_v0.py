# tests/live/test_testnet_persisted_status_finalization_contract_v0.py
"""
Offline-Vertrag: Finalisierung persistierter Testnet-Metadaten (meta.json / ended_at).

Kein Testnet-Start, kein Netzwerk — nur tmp_path, PeakConfig und Orchestrierungs-APIs.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.core.peak_config import PeakConfig
from src.live.run_logging import (
    LiveRunMetadata,
    create_run_logger_from_config,
    finalize_persisted_run_metadata_if_unfinished,
    load_run_metadata,
)
from src.live.testnet_orchestrator import (
    PersistedRunStopNotApplicableError,
    RunInfo,
    RunNotFoundError,
    RunState,
    TestnetOrchestrator,
)


def _write_meta(run_dir: Path, md: LiveRunMetadata) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "meta.json").write_text(
        json.dumps(md.to_dict()),
        encoding="utf-8",
    )


def test_synthetic_meta_finalized_offline_sets_ended_at(tmp_path: Path) -> None:
    run_id = "testnet_finalize_offline_v0"
    run_dir = tmp_path / "logs" / run_id
    _write_meta(
        run_dir,
        LiveRunMetadata(
            run_id=run_id,
            mode="testnet",
            strategy_name="ma_crossover",
            symbol="BTC/EUR",
            timeframe="1m",
            started_at=datetime(2026, 5, 15, 10, 0, 0, tzinfo=timezone.utc),
        ),
    )
    fake_end = datetime(2026, 5, 15, 11, 0, 0, tzinfo=timezone.utc)
    assert finalize_persisted_run_metadata_if_unfinished(run_dir, ended_at=fake_end) is True
    md = load_run_metadata(run_dir)
    assert md.ended_at == fake_end
    assert finalize_persisted_run_metadata_if_unfinished(run_dir) is False


def test_fresh_orchestrator_sees_non_running_persisted_after_finalization(
    tmp_path: Path,
) -> None:
    run_id = "testnet_finalize_fresh_orch_v0"
    base = tmp_path / "logs"
    _write_meta(
        base / run_id,
        LiveRunMetadata(
            run_id=run_id,
            mode="testnet",
            strategy_name="ma_crossover",
            symbol="BTC/EUR",
            timeframe="1m",
            started_at=datetime(2026, 5, 15, 9, 0, 0, tzinfo=timezone.utc),
        ),
    )
    assert finalize_persisted_run_metadata_if_unfinished(base / run_id) is True

    cfg = PeakConfig(
        raw={
            "environment": {"mode": "testnet"},
            "shadow_paper_logging": {"base_dir": str(base), "enabled": True},
        }
    )
    orch = TestnetOrchestrator(cfg)
    st = orch.get_status(run_id)
    assert st.status_source == "persisted"
    assert st.state == RunState.STOPPED
    assert st.stopped_at is not None


def test_in_memory_stop_with_run_logger_finalizes_meta(tmp_path: Path) -> None:
    run_id = "testnet_stop_with_logger_v0"
    base = tmp_path / "logs"
    cfg = PeakConfig(
        raw={
            "environment": {"mode": "testnet"},
            "shadow_paper_logging": {"base_dir": str(base), "enabled": True},
        }
    )
    run_logger = create_run_logger_from_config(
        cfg,
        mode="testnet",
        strategy_name="ma_crossover",
        symbol="BTC/EUR",
        timeframe="1m",
        run_id=run_id,
    )
    run_logger.initialize()

    class _Sess:
        def stop(self) -> None:
            pass

    orch = TestnetOrchestrator(cfg)
    orch._runs[run_id] = RunInfo(
        run_id=run_id,
        mode="testnet",
        strategy_name="ma_crossover",
        symbol="BTC/EUR",
        timeframe="1m",
        state=RunState.RUNNING,
        started_at=datetime(2026, 5, 15, tzinfo=timezone.utc),
        session=_Sess(),
        run_logger=run_logger,
        status_source="in_memory",
    )
    orch.stop_run(run_id)

    md = load_run_metadata(base / run_id)
    assert md.ended_at is not None


def test_in_memory_stop_without_logger_finalizes_orphan_meta(tmp_path: Path) -> None:
    run_id = "testnet_stop_orphan_meta_v0"
    base = tmp_path / "logs"
    _write_meta(
        base / run_id,
        LiveRunMetadata(
            run_id=run_id,
            mode="testnet",
            strategy_name="ma_crossover",
            symbol="BTC/EUR",
            timeframe="1m",
            started_at=datetime(2026, 5, 15, tzinfo=timezone.utc),
        ),
    )
    cfg = PeakConfig(
        raw={
            "environment": {"mode": "testnet"},
            "shadow_paper_logging": {"base_dir": str(base), "enabled": True},
        }
    )
    orch = TestnetOrchestrator(cfg)

    class _Sess:
        def stop(self) -> None:
            pass

    orch._runs[run_id] = RunInfo(
        run_id=run_id,
        mode="testnet",
        strategy_name="ma_crossover",
        symbol="BTC/EUR",
        timeframe="1m",
        state=RunState.RUNNING,
        started_at=datetime(2026, 5, 15, tzinfo=timezone.utc),
        session=_Sess(),
        run_logger=None,
        status_source="in_memory",
    )
    orch.stop_run(run_id)

    md = load_run_metadata(base / run_id)
    assert md.ended_at is not None
    assert orch._runs[run_id].state == RunState.STOPPED


def test_persisted_only_stop_still_classifies_without_process_stopped(
    tmp_path: Path,
) -> None:
    run_id = "testnet_finalize_cross_class_v0"
    base = tmp_path / "logs"
    _write_meta(
        base / run_id,
        LiveRunMetadata(
            run_id=run_id,
            mode="testnet",
            strategy_name="ma_crossover",
            symbol="BTC/EUR",
            timeframe="1m",
            started_at=datetime(2026, 5, 15, tzinfo=timezone.utc),
        ),
    )
    cfg = PeakConfig(
        raw={
            "environment": {"mode": "testnet"},
            "shadow_paper_logging": {"base_dir": str(base), "enabled": True},
        }
    )
    orch = TestnetOrchestrator(cfg)
    with pytest.raises(PersistedRunStopNotApplicableError) as ei:
        orch.stop_run(run_id)
    assert ei.value.classification == "stale_persisted_running"
    assert "process_stopped=False" in str(ei.value)


def test_missing_run_id_stop_still_not_found(tmp_path: Path) -> None:
    base = tmp_path / "empty"
    base.mkdir()
    cfg = PeakConfig(raw={"shadow_paper_logging": {"base_dir": str(base), "enabled": True}})
    orch = TestnetOrchestrator(cfg)
    with pytest.raises(RunNotFoundError, match="nicht gefunden"):
        orch.stop_run("missing_finalize_v0")
