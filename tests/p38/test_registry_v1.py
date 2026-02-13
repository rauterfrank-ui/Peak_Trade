"""Tests for P38 bundle registry v1."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from src.backtest.p35.bundle_v1 import write_report_bundle_v1
from src.backtest.p36.tarball_v1 import write_bundle_tarball_v1
from src.backtest.p38.registry_v1 import (
    BundleRegistryV1,
    RegistryError,
    build_registry_v1,
    read_registry_v1,
    verify_registry_v1,
    write_registry_v1,
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


def test_empty_roundtrip(tmp_path: Path) -> None:
    reg = BundleRegistryV1(schema_version=1, entries=[])
    p = tmp_path / "registry.json"
    write_registry_v1(p, reg)
    out = read_registry_v1(p)
    assert out.schema_version == 1
    assert out.entries == []
    verify_registry_v1(p)


def test_verify_fails_on_bad_order(tmp_path: Path) -> None:
    p = tmp_path / "registry.json"
    p.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "entries": [
                    {
                        "bundle_id": "b",
                        "kind": "k",
                        "ref_path": "p",
                        "sha256": "a" * 64,
                    },
                    {
                        "bundle_id": "a",
                        "kind": "k",
                        "ref_path": "p",
                        "sha256": "b" * 64,
                    },
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    with pytest.raises(RegistryError):
        verify_registry_v1(p)


def test_build_rejects_unknown_input(tmp_path: Path) -> None:
    bad = tmp_path / "x.txt"
    bad.write_text("nope", encoding="utf-8")
    with pytest.raises(RegistryError):
        build_registry_v1([bad])


def test_build_single_dir_bundle(tmp_path: Path) -> None:
    d = tmp_path / "b1"
    write_report_bundle_v1(d, _sample_report_dict(), include_metrics_summary=False)
    reg = build_registry_v1([d])
    assert len(reg.entries) == 1
    assert reg.entries[0].kind == "dir_bundle"
    assert reg.entries[0].bundle_id == "b1"


def test_build_single_tarball(tmp_path: Path) -> None:
    d = tmp_path / "b2"
    write_report_bundle_v1(d, _sample_report_dict(), include_metrics_summary=False)
    tgz = tmp_path / "b2.tgz"
    write_bundle_tarball_v1(d, tgz)
    reg = build_registry_v1([tgz])
    assert len(reg.entries) == 1
    assert reg.entries[0].kind == "tarball"
    assert reg.entries[0].bundle_id == "b2"
