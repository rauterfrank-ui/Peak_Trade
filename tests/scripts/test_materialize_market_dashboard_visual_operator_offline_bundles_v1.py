"""Unit tests for the market visual operator offline bundle materializer.

The synthetic panel below is a MATERIALIZER UNIT INPUT that mimics the panel schema only.
It is NOT a market display fixture and makes no production data claims. Tests assert
Bitcoin filtering and deterministic output.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

_MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / "scripts"
    / "ops"
    / "materialize_market_dashboard_visual_operator_offline_bundles_v1.py"
)
_spec = importlib.util.spec_from_file_location("_mat_market_visual_operator_v1", _MODULE_PATH)
assert _spec and _spec.loader
mat = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mat)


def _synthetic_panel() -> list[dict[str, object]]:
    """MATERIALIZER UNIT INPUT ONLY — not a market display fixture."""
    records: list[dict[str, object]] = []
    instruments = [
        "okx:linear_perpetual:ETH:USDT:USDT:perp",
        "okx:linear_perpetual:ADA:USDT:USDT:perp",
        "okx:linear_perpetual:BTC:USDT:USDT:perp",  # must be filtered
        "okx:linear_perpetual:XBT:USDT:USDT:perp",  # must be filtered
    ]
    for inst in instruments:
        for i in range(4):
            records.append(
                {
                    "instrument_id": inst,
                    "timestamp_utc": f"2024-05-25T{i:02d}:00:00Z",
                    "open": "1.0",
                    "high": "1.5",
                    "low": "0.5",
                    "close": str(1.0 + i),
                    "volume": str(1000 + i),
                    "is_final": True,
                }
            )
    return records


@pytest.fixture()
def panel_path(tmp_path: Path) -> Path:
    path = tmp_path / "normalized_panel_bars.json"
    path.write_text(json.dumps(_synthetic_panel()), encoding="utf-8")
    return path


def test_bitcoin_instruments_filtered(tmp_path: Path, panel_path: Path) -> None:
    out = tmp_path / "bundles"
    result = mat.materialize(out, panel_path=panel_path, economic_dir=tmp_path / "missing")
    futures = json.loads((out / "futures_ohlcv" / "futures_ohlcv.json").read_text("utf-8"))
    symbols = set(futures["series"].keys())
    assert symbols == {"ETHUSDT", "ADAUSDT"}
    assert "BTCUSDT" not in symbols
    assert "XBTUSDT" not in symbols
    assert result["symbol_count"] == 2


def test_deterministic_output(tmp_path: Path, panel_path: Path) -> None:
    out_a = tmp_path / "a"
    out_b = tmp_path / "b"
    mat.materialize(out_a, panel_path=panel_path, economic_dir=tmp_path / "missing")
    mat.materialize(out_b, panel_path=panel_path, economic_dir=tmp_path / "missing")
    for rel in (
        "futures_ohlcv/futures_ohlcv.json",
        "ranking_funnel/ranking_funnel.json",
        "f5_dashboard/dashboard.json",
    ):
        assert (out_a / rel).read_text("utf-8") == (out_b / rel).read_text("utf-8")


def test_readmodel_ids_and_non_authorizing(tmp_path: Path, panel_path: Path) -> None:
    out = tmp_path / "bundles"
    mat.materialize(out, panel_path=panel_path, economic_dir=tmp_path / "missing")
    futures = json.loads((out / "futures_ohlcv" / "futures_ohlcv.json").read_text("utf-8"))
    ranking = json.loads((out / "ranking_funnel" / "ranking_funnel.json").read_text("utf-8"))
    assert futures["readmodel_id"] == "market_futures_ohlcv_readmodel.v0"
    assert ranking["readmodel_id"] == "market_ranking_funnel_readmodel.v0"
    assert futures["non_authorizing"] is True
    assert ranking["non_authorizing"] is True
    assert futures["stale"] is False
    # Ranking is volume-ranked descending: highest last-bar volume gets rank 1.
    selected = ranking["stages"]["selected"]
    assert selected[0]["rank"] == 1
    assert all(0.0 <= row["display_score"] <= 1.0 for row in selected)


def test_economic_binding_marks_missing_provenance_honestly(
    tmp_path: Path, panel_path: Path
) -> None:
    out = tmp_path / "bundles"
    mat.materialize(out, panel_path=panel_path, economic_dir=tmp_path / "no_evidence_here")
    binding = json.loads((out / "economic_evidence_binding.json").read_text("utf-8"))
    assert binding["provenance_status"] == "provenance_missing"
    for entry in binding["files"].values():
        assert entry["status"] == "provenance_missing"
        assert entry["sha256"] is None


def test_manifest_written(tmp_path: Path, panel_path: Path) -> None:
    out = tmp_path / "bundles"
    mat.materialize(out, panel_path=panel_path, economic_dir=tmp_path / "missing")
    manifest = (out / "MANIFEST.sha256").read_text("utf-8")
    assert "futures_ohlcv/futures_ohlcv.json" in manifest
    assert "ranking_funnel/ranking_funnel.json" in manifest
