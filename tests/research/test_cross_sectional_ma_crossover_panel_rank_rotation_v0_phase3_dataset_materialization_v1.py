"""Contract tests for CS MA-crossover panel rank-rotation v0 Phase 3 dataset materialization."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
_OKX_SCRIPT = _REPO_ROOT / "scripts/ops/materialize_okx_production_lifecycle_and_pt1h_panel_v1.py"
_GO = "GO_BOUNDED_OKX_PRODUCTION_LIFECYCLE_SOURCE_REGISTRATION_AND_PT1H_PANEL_OHLCV_INGEST_V0"

from src.research.cross_sectional_ma_crossover_panel_rank_rotation_v0_phase3_dataset_materialization_v1 import (  # noqa: E402
    OPERATOR_GO_PHASE3,
    PANEL_ID,
    ValidationVerdictEnum,
    materialize_phase3_dataset_materialization_closeout_v1,
    validate_phase3_dataset_materialization_closeout_v1,
    verify_bitcoin_absent_v1,
)


def _load_okx_mod():
    spec = importlib.util.spec_from_file_location(
        "materialize_okx_production_lifecycle_and_pt1h_panel_v1", _OKX_SCRIPT
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _live_inst(base: str) -> dict[str, str]:
    return {
        "instId": f"{base}-USDT-SWAP",
        "instType": "SWAP",
        "settleCcy": "USDT",
        "ctType": "linear",
        "baseCcy": base,
        "state": "live",
        "listTime": "1609459200000",
        "expTime": "",
    }


def _mock_fetcher(instruments: list[dict[str, str]]):
    from datetime import datetime, timedelta, timezone

    end_dt = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0) - timedelta(
        hours=1
    )
    ts_start = int((end_dt - timedelta(hours=5)).timestamp() * 1000)

    def _fetch(url: str, *, timeout_seconds: float, max_response_bytes: int, headers=None):
        path = url.split("?", 1)[0].split(".com", 1)[-1]
        if path.endswith("/public/instruments"):
            payload = {"code": "0", "data": instruments}
            return 200, json.dumps(payload).encode(), {}
        if path.endswith("/history-candles"):
            rows = [
                [str(ts_start + i * 3_600_000), "1", "2", "0.5", "1.5", "10", "0", "0", "1"]
                for i in range(5)
            ]
            return 200, json.dumps({"code": "0", "data": rows}).encode(), {}
        raise ValueError(path)

    return _fetch


class TestPhase3DatasetMaterializationCloseout:
    def test_bitcoin_negative_check(self) -> None:
        ok, blocked = verify_bitcoin_absent_v1(
            ["okx:linear_perpetual:ETH:USDT:USDT:perp", "okx:linear_perpetual:BTC:USDT:USDT:perp"]
        )
        assert ok is False
        assert blocked

    def test_closeout_from_mock_materialization(self, tmp_path: Path) -> None:
        okx_mod = _load_okx_mod()
        instruments = [_live_inst(base) for base in ("ETH", "SOL", "ADA", "DOT", "LINK", "AVAX")]
        staging = tmp_path / "staging" / "v2"
        archive = tmp_path / "archive"
        okx_mod.run_materialization(
            confirm=_GO,
            target_staging_root=staging,
            durable_evidence_root=archive,
            staging_window_days=1,
            fetcher=_mock_fetcher(instruments),
        )
        evidence_dirs = list(
            (archive / "planning").glob(
                "bounded_okx_production_lifecycle_source_registration_and_pt1h_panel_ohlcv_ingest_v0_*"
            )
        )
        assert evidence_dirs
        closeout = materialize_phase3_dataset_materialization_closeout_v1(
            repo_root=_REPO_ROOT,
            durable_archive_root=archive,
            okx_materialization_evidence_dir=evidence_dirs[0],
            panel_staging_root=staging,
            operator="test-operator",
            pre_head="abc123",
        )
        validation = validate_phase3_dataset_materialization_closeout_v1(closeout)
        assert validation.verdict == ValidationVerdictEnum.ACCEPTED
        assert closeout["dataset_materialized"] is True
        assert closeout["dataset_id"] == PANEL_ID
        assert closeout["bitcoin_present"] is False
        assert closeout["operator_go_token"] == OPERATOR_GO_PHASE3
        assert closeout["economic_evaluation_executed"] is False
        assert closeout["instrument_count"] >= 5
