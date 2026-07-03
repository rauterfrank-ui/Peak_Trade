"""Contract tests for materialize_pit_futures_universe_manifest_production_v1 ops script."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRIPT = _REPO_ROOT / "scripts/ops/materialize_pit_futures_universe_manifest_production_v1.py"
_LIFECYCLE_SCRIPT = (
    _REPO_ROOT / "scripts/ops/materialize_okx_production_lifecycle_and_pt1h_panel_v1.py"
)
_GO = "GO_BOUNDED_PIT_FUTURES_UNIVERSE_MANIFEST_PRODUCTION_MATERIALIZATION_V0"
_LIFECYCLE_GO = (
    "GO_BOUNDED_OKX_PRODUCTION_LIFECYCLE_SOURCE_REGISTRATION_AND_PT1H_PANEL_OHLCV_INGEST_V0"
)


def _load_mod(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
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
    ts_start = int((end_dt - timedelta(hours=30)).timestamp() * 1000)

    def _fetch(url: str, *, timeout_seconds: float, max_response_bytes: int = 0, headers=None):
        path = url.split("?", 1)[0].split(".com", 1)[-1]
        if path.endswith("/public/instruments"):
            payload = {"code": "0", "data": instruments}
            return 200, json.dumps(payload).encode(), {}
        if path.endswith("/history-candles"):
            rows = [
                [str(ts_start + i * 3_600_000), "1", "2", "0.5", "1.5", "10", "0", "0", "1"]
                for i in range(30)
            ]
            return 200, json.dumps({"code": "0", "data": rows}).encode(), {}
        raise ValueError(path)

    return _fetch


class TestProductionManifestOpsMaterialization:
    def test_end_to_end_from_lifecycle_staging(self, tmp_path: Path) -> None:
        lifecycle_mod = _load_mod(
            "materialize_okx_production_lifecycle_and_pt1h_panel_v1", _LIFECYCLE_SCRIPT
        )
        manifest_mod = _load_mod("materialize_pit_futures_universe_manifest_production_v1", _SCRIPT)
        instruments = [_live_inst(base) for base in ("ETH", "SOL", "ADA", "DOT", "LINK", "AVAX")]
        staging = tmp_path / "staging" / "pit_okx_pt1h_panel" / "v1"
        evidence = tmp_path / "evidence"
        lifecycle_mod.run_materialization(
            confirm=_LIFECYCLE_GO,
            target_staging_root=staging,
            durable_evidence_root=evidence,
            staging_window_days=1,
            fetcher=_mock_fetcher(instruments),
        )
        result = manifest_mod.run_materialization(
            confirm=_GO,
            staging_root=staging,
            durable_evidence_root=evidence,
            generated_at="2026-07-03T04:00:00Z",
        )
        assert result["eligible_instrument_count"] >= 5
        manifest_path = staging / "universe" / "pit_futures_universe_manifest_v1.json"
        assert manifest_path.is_file()
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert manifest["universe_policy_id"] == result["universe_policy_id"]
        assert manifest["futures_only"] is True
        assert manifest["bitcoin_direction_allowed"] is False
