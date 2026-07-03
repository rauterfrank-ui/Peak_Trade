"""Contract tests for materialize_okx_production_lifecycle_and_pt1h_panel_v1."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRIPT = _REPO_ROOT / "scripts/ops/materialize_okx_production_lifecycle_and_pt1h_panel_v1.py"
_GO = "GO_BOUNDED_OKX_PRODUCTION_LIFECYCLE_SOURCE_REGISTRATION_AND_PT1H_PANEL_OHLCV_INGEST_V0"


def _load_mod():
    spec = importlib.util.spec_from_file_location(
        "materialize_okx_production_lifecycle_and_pt1h_panel_v1", _SCRIPT
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


class TestMaterializationOffline:
    def test_materialization_success_with_mock_fetcher(self, tmp_path: Path) -> None:
        mod = _load_mod()
        instruments = [_live_inst(base) for base in ("ETH", "SOL", "ADA", "DOT", "LINK", "AVAX")]
        target = tmp_path / "staging" / "pit_okx_pt1h_panel" / "v1"
        evidence = tmp_path / "evidence"
        result = mod.run_materialization(
            confirm=_GO,
            target_staging_root=target,
            durable_evidence_root=evidence,
            staging_window_days=1,
            fetcher=_mock_fetcher(instruments),
        )
        assert result["production_lifecycle_source_bound"] is True
        assert result["eligible_instrument_count"] >= 5
        assert result["panel_dataset_manifest_materialized"] is True
        assert result["manifest_verify_rc"] == 0
        assert (target / "panel/panel_dataset_manifest.json").is_file()
        assert (target / "lifecycle/registry_snapshot_v1.json").is_file()
