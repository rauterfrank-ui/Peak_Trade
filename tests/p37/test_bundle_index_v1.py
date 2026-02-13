"""Tests for P37 bundle index v1."""

from __future__ import annotations

from pathlib import Path

from src.backtest.p37.bundle_index_v1 import (
    BundleIndexV1,
    read_bundle_index_v1,
    write_bundle_index_v1,
)


def test_index_json_roundtrip(tmp_path: Path) -> None:
    idx = BundleIndexV1(version=1, entries=[])
    p = tmp_path / "index.json"
    write_bundle_index_v1(p, idx)
    out = read_bundle_index_v1(p)
    assert out.version == 1
    assert out.entries == []
