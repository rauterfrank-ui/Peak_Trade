"""Tests for P36 report bundle tarball v1."""

from __future__ import annotations

import tarfile
from pathlib import Path
from typing import Any

import pytest

from src.backtest.p35.bundle_v1 import write_report_bundle_v1
from src.backtest.p36.tarball_v1 import (
    TarballBundleError,
    read_bundle_tarball_v1,
    verify_bundle_tarball_v1,
    write_bundle_tarball_v1,
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


def test_roundtrip_tarball(tmp_path: Path) -> None:
    bundle_dir = tmp_path / "bundle"
    tar_path = tmp_path / "bundle.tgz"
    write_report_bundle_v1(bundle_dir, _sample_report_dict(), include_metrics_summary=True)
    write_bundle_tarball_v1(bundle_dir, tar_path)

    out_dir = tmp_path / "out"
    read_bundle_tarball_v1(tar_path, out_dir)
    verify_bundle_tarball_v1(tar_path)
    assert (out_dir / "report.json").exists()
    assert (out_dir / "manifest.json").exists()


def test_reject_unexpected_member(tmp_path: Path) -> None:
    tar_path = tmp_path / "bad.tgz"
    with tarfile.open(tar_path, "w:gz") as tf:
        p = tmp_path / "x.txt"
        p.write_text("x", encoding="utf-8")
        tf.add(p, arcname="evil.txt", recursive=False)
    with pytest.raises(TarballBundleError):
        verify_bundle_tarball_v1(tar_path)


def test_reject_traversal_member(tmp_path: Path) -> None:
    tar_path = tmp_path / "bad2.tgz"
    with tarfile.open(tar_path, "w:gz") as tf:
        p = tmp_path / "x.txt"
        p.write_text("x", encoding="utf-8")
        tf.add(p, arcname="../report.json", recursive=False)
    with pytest.raises(TarballBundleError):
        verify_bundle_tarball_v1(tar_path)


def test_tamper_detected(tmp_path: Path) -> None:
    bundle_dir = tmp_path / "bundle"
    tar_path = tmp_path / "bundle.tgz"
    write_report_bundle_v1(bundle_dir, _sample_report_dict(), include_metrics_summary=False)
    (bundle_dir / "report.json").write_text('{"schema_version": 1}\n', encoding="utf-8")
    write_bundle_tarball_v1(bundle_dir, tar_path)
    with pytest.raises(TarballBundleError):
        verify_bundle_tarball_v1(tar_path)
