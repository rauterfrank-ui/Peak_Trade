# tests/live/test_testnet_cross_process_stop_contract_v0.py
"""
Offline-Vertrag: Cross-Process-Stop-Semantik für Testnet-Orchestrator.

Kein Testnet-Start, kein Netzwerk — nur tmp_path, PeakConfig und CLI-Funktionen.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from argparse import Namespace
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.core.peak_config import PeakConfig
from src.live.run_logging import LiveRunMetadata
from src.live.testnet_orchestrator import (
    PersistedRunStopNotApplicableError,
    RunInfo,
    RunNotFoundError,
    RunState,
    TestnetOrchestrator,
)


def _write_meta(run_dir: Path, md: LiveRunMetadata) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "meta.json").write_text(json.dumps(md.to_dict()), encoding="utf-8")


def _load_cli_module():
    root = Path(__file__).resolve().parents[2]
    path = root / "scripts" / "testnet_orchestrator_cli.py"
    spec = importlib.util.spec_from_file_location("_testnet_orchestrator_cli", path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["_testnet_orchestrator_cli"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_stop_run_in_memory_still_stops_same_process_run(tmp_path: Path) -> None:
    """In-Prozess: ``stop_run`` beendet einen Eintrag in ``_runs`` wie bisher."""

    class _DummySession:
        def __init__(self) -> None:
            self.stop_called = False

        def stop(self) -> None:
            self.stop_called = True

    run_id = "testnet_cross_stop_mem_v0"
    base = tmp_path / "runs"
    cfg = PeakConfig(
        raw={
            "environment": {"mode": "testnet"},
            "shadow_paper_logging": {"base_dir": str(base), "enabled": True},
        }
    )
    orch = TestnetOrchestrator(cfg)
    sess = _DummySession()
    orch._runs[run_id] = RunInfo(
        run_id=run_id,
        mode="testnet",
        strategy_name="ma_crossover",
        symbol="BTC/EUR",
        timeframe="1m",
        state=RunState.RUNNING,
        started_at=datetime(2026, 5, 15, tzinfo=timezone.utc),
        session=sess,
        status_source="in_memory",
    )

    orch.stop_run(run_id)

    assert sess.stop_called
    assert orch._runs[run_id].state == RunState.STOPPED
    assert orch._runs[run_id].stopped_at is not None


def test_stop_run_persisted_only_running_raises_stale_classification(tmp_path: Path) -> None:
    """Nur ``meta.json`` (running): keine Ausnahme „nicht gefunden“, sondern Persistenz-Klasse."""
    run_id = "testnet_cross_stop_stale_v0"
    base = tmp_path / "runs"
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
    assert "stop_classification=stale_persisted_running" in str(ei.value)
    assert "persisted_only=True" in str(ei.value)
    assert "process_stopped=False" in str(ei.value)


def test_stop_run_persisted_only_already_stopped_classification(tmp_path: Path) -> None:
    """Persistiert mit ``ended_at``: ebenfalls kein In-Prozess-Stopp möglich."""
    run_id = "testnet_cross_stop_done_v0"
    base = tmp_path / "runs"
    _write_meta(
        base / run_id,
        LiveRunMetadata(
            run_id=run_id,
            mode="testnet",
            strategy_name="ma_crossover",
            symbol="BTC/EUR",
            timeframe="1m",
            started_at=datetime(2026, 5, 15, tzinfo=timezone.utc),
            ended_at=datetime(2026, 5, 15, 12, 0, 0, tzinfo=timezone.utc),
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

    assert ei.value.classification == "persisted_only_already_stopped"


def test_stop_run_missing_run_id_still_not_found(tmp_path: Path) -> None:
    base = tmp_path / "empty"
    base.mkdir()
    cfg = PeakConfig(raw={"shadow_paper_logging": {"base_dir": str(base), "enabled": True}})
    orch = TestnetOrchestrator(cfg)
    with pytest.raises(RunNotFoundError, match="nicht gefunden"):
        orch.stop_run("does_not_exist_cross_stop_v0")


def test_cmd_stop_messages_distinguish_paths(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """CLI: unterscheidbare Ausgaben für in-memory vs persisted-only vs nicht gefunden."""
    cli = _load_cli_module()
    base = tmp_path / "runs"
    run_stale = "testnet_cli_stale_v0"
    run_mem = "testnet_cli_mem_v0"
    _write_meta(
        base / run_stale,
        LiveRunMetadata(
            run_id=run_stale,
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

    assert cli.cmd_stop(Namespace(all=False, run_id=run_stale), orch) == 2
    err = capsys.readouterr().err
    assert "stop_classification=stale_persisted_running" in err
    assert "persisted_only=True" in err
    assert "process_stopped=False" in err

    class _S:
        def stop(self) -> None:
            pass

    orch._runs[run_mem] = RunInfo(
        run_id=run_mem,
        mode="testnet",
        strategy_name="ma_crossover",
        symbol="BTC/EUR",
        timeframe="1m",
        state=RunState.RUNNING,
        started_at=datetime(2026, 5, 15, tzinfo=timezone.utc),
        session=_S(),
        status_source="in_memory",
    )
    assert cli.cmd_stop(Namespace(all=False, run_id=run_mem), orch) == 0
    out = capsys.readouterr().out
    assert "✅ Run gestoppt (in_memory)" in out

    assert cli.cmd_stop(Namespace(all=False, run_id="missing_cli_v0"), orch) == 1
    err_nf = capsys.readouterr().err
    assert "❌ Fehler" in err_nf
    assert "Run-ID nicht gefunden" in err_nf
