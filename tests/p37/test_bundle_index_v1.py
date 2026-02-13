"""Tests for P37 bundle index v1."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from src.backtest.p35.bundle_v1 import write_report_bundle_v1
from src.backtest.p36.tarball_v1 import read_bundle_tarball_v1, write_bundle_tarball_v1
from src.backtest.p37.bundle_index_v1 import (
    BundleIndexV1,
    IndexIntegrityError,
    index_bundles_v1,
    read_bundle_index_v1,
    verify_bundle_index_v1,
    write_bundle_index_v1,
)


def _sample_report_dict() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "fills": [
            {
                "order_id": "o1",
                "side": "BUY",
                "qty": 1.0,
                "price": 100.0,
                "fee": 0.1,
                "symbol": "MOCK",
            }
        ],
        "state": {
            "cash": 999.9,
            "positions_qty": {"MOCK": 1.0},
            "avg_cost": {"MOCK": 100.0},
            "realized_pnl": 0.0,
        },
        "equity": [1000.0, 1000.0],
        "metrics": {
            "total_return": 0.0,
            "max_drawdown": 0.0,
            "sharpe": 0.0,
            "n_steps": 2.0,
        },
    }


def test_index_json_roundtrip(tmp_path: Path) -> None:
    idx = BundleIndexV1(version=1, entries=[])
    p = tmp_path / "index.json"
    write_bundle_index_v1(p, idx)
    out = read_bundle_index_v1(p)
    assert out.version == 1
    assert out.entries == []


def test_index_empty_ok(tmp_path: Path) -> None:
    idx = index_bundles_v1([], base_dir=tmp_path)
    assert idx.entries == []
    verify_bundle_index_v1(idx, base_dir=tmp_path)


def test_index_single_dir_bundle(tmp_path: Path) -> None:
    d = tmp_path / "b1"
    write_report_bundle_v1(d, _sample_report_dict(), include_metrics_summary=True)
    idx = index_bundles_v1([d], base_dir=tmp_path)
    assert len(idx.entries) == 1
    assert idx.entries[0].kind == "dir_bundle"
    verify_bundle_index_v1(idx, base_dir=tmp_path)


def test_index_single_tarball(tmp_path: Path) -> None:
    d = tmp_path / "b2"
    write_report_bundle_v1(d, _sample_report_dict(), include_metrics_summary=True)
    tgz = tmp_path / "b2.tgz"
    write_bundle_tarball_v1(d, tgz)
    out_dir = tmp_path / "extract"
    out_dir.mkdir()
    read_bundle_tarball_v1(tgz, out_dir)
    idx = index_bundles_v1([tgz], base_dir=tmp_path)
    assert len(idx.entries) == 1
    assert idx.entries[0].kind == "tarball"
    verify_bundle_index_v1(idx, base_dir=tmp_path)


def test_index_duplicate_relpath_rejected(tmp_path: Path) -> None:
    d1 = tmp_path / "dup"
    d2 = tmp_path / "dup2"
    write_report_bundle_v1(d1, _sample_report_dict(), include_metrics_summary=False)
    write_report_bundle_v1(d2, _sample_report_dict(), include_metrics_summary=False)

    idx1 = index_bundles_v1([d1], base_dir=tmp_path)
    dup = idx1.entries[0]
    idx = BundleIndexV1(version=1, entries=[dup, dup])
    with pytest.raises(IndexIntegrityError):
        verify_bundle_index_v1(idx, base_dir=tmp_path)


def test_verify_detects_tampered_manifest(tmp_path: Path) -> None:
    d = tmp_path / "b3"
    write_report_bundle_v1(d, _sample_report_dict(), include_metrics_summary=False)
    idx = index_bundles_v1([d], base_dir=tmp_path)
    verify_bundle_index_v1(idx, base_dir=tmp_path)

    mf = d / "manifest.json"
    mf.write_text(mf.read_text(encoding="utf-8") + " ", encoding="utf-8")

    with pytest.raises(IndexIntegrityError):
        verify_bundle_index_v1(idx, base_dir=tmp_path)
