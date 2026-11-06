# tests/live/test_testnet_status_persisted_artifacts_contract_v0.py
"""
Offline-Vertrag: Status zu Testnet-Runs aus persistiertem ``meta.json``.

Kein Testnet-Start, kein Netzwerk, kein Broker — nur tmp_path + PeakConfig.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.core.peak_config import PeakConfig
from src.live.run_logging import LiveRunMetadata
from src.live.testnet_orchestrator import (
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


def test_get_status_resolves_persisted_testnet_run_from_meta_json(tmp_path: Path) -> None:
    run_id = "testnet_persisted_contract_v0_001"
    base = tmp_path / "run_logs"
    _write_meta(
        base / run_id,
        LiveRunMetadata(
            run_id=run_id,
            mode="testnet",
            strategy_name="ma_crossover",
            symbol="BTC/EUR",
            timeframe="1m",
            started_at=datetime(2026, 5, 15, 7, 28, 38, tzinfo=timezone.utc),
        ),
    )

    cfg = PeakConfig(
        raw={
            "environment": {"mode": "testnet"},
            "shadow_paper_logging": {"base_dir": str(base), "enabled": True},
        }
    )
    orch = TestnetOrchestrator(cfg)
    assert orch.get_status().__class__ is list
    assert len(orch._runs) == 0

    st = orch.get_status(run_id)
    assert st.run_id == run_id
    assert st.status_source == "persisted"
    assert st.mode == "testnet"
    assert st.strategy_name == "ma_crossover"
    assert st.to_dict()["status_source"] == "persisted"


def test_get_status_missing_run_id_raises(tmp_path: Path) -> None:
    base = tmp_path / "empty_runs"
    base.mkdir()
    cfg = PeakConfig(
        raw={
            "shadow_paper_logging": {"base_dir": str(base), "enabled": True},
        }
    )
    orch = TestnetOrchestrator(cfg)
    with pytest.raises(RunNotFoundError, match="nicht gefunden"):
        orch.get_status("does_not_exist_000")


def test_in_memory_run_takes_precedence_over_persisted_meta(tmp_path: Path) -> None:
    """Gleicher Prozess: Eintrag in ``_runs`` gewinnt; Quelle wird als in_memory markiert."""
    run_id = "testnet_precedence_contract_v0_002"
    base = tmp_path / "both"
    _write_meta(
        base / run_id,
        LiveRunMetadata(
            run_id=run_id,
            mode="testnet",
            strategy_name="from_disk",
            symbol="ETH/EUR",
            timeframe="5m",
            started_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        ),
    )
    cfg = PeakConfig(
        raw={
            "shadow_paper_logging": {"base_dir": str(base), "enabled": True},
        }
    )
    orch = TestnetOrchestrator(cfg)

    memory_started = datetime(2026, 6, 1, tzinfo=timezone.utc)
    orch._runs[run_id] = RunInfo(
        run_id=run_id,
        mode="testnet",
        strategy_name="from_memory",
        symbol="BTC/EUR",
        timeframe="1m",
        state=RunState.RUNNING,
        started_at=memory_started,
        status_source="in_memory",
    )

    st = orch.get_status(run_id)
    assert st.strategy_name == "from_memory"
    assert st.symbol == "BTC/EUR"
    assert st.timeframe == "1m"
    assert st.status_source == "in_memory"


def test_paper_mode_meta_is_not_loaded_as_orchestrator_run(tmp_path: Path) -> None:
    """Nur Modi shadow/testnet sind für die Persistenz-Rekonstruktion zulässig."""
    run_id = "paper_meta_ignored_003"
    base = tmp_path / "paperish"
    _write_meta(
        base / run_id,
        LiveRunMetadata(
            run_id=run_id,
            mode="paper",
            strategy_name="x",
            symbol="BTC/EUR",
            timeframe="1m",
        ),
    )
    cfg = PeakConfig(raw={"shadow_paper_logging": {"base_dir": str(base), "enabled": True}})
    orch = TestnetOrchestrator(cfg)
    with pytest.raises(RunNotFoundError):
        orch.get_status(run_id)
