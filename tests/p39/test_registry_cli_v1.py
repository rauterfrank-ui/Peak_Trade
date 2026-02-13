"""Tests for P39 registry CLI v1."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from src.backtest.p35.bundle_v1 import write_report_bundle_v1
from src.backtest.p36.tarball_v1 import write_bundle_tarball_v1
from src.backtest.p37.bundle_index_v1 import (
    BundleIndexEntryV1,
    BundleIndexV1,
    write_bundle_index_v1,
)
from src.backtest.p38.registry_v1 import (
    BundleRegistryV1,
    RegistryEntryV1,
    write_registry_v1,
)
from src.ops.p39.registry_cli_v1 import EXIT_OK, EXIT_VERIFY_FAILED, build_parser, main


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


def test_parser_smoke() -> None:
    p = build_parser()
    ns = p.parse_args(["verify", "--bundle-dir", "/tmp/x"])
    assert ns.cmd == "verify"
    assert ns.bundle_dir == "/tmp/x"


def test_verify_bundle_dir_ok(tmp_path: Path) -> None:
    write_report_bundle_v1(tmp_path, _sample_report_dict(), include_metrics_summary=True)
    rc = main(["verify", "--bundle-dir", str(tmp_path)])
    assert rc == EXIT_OK


def test_verify_bundle_dir_tamper_fails(tmp_path: Path) -> None:
    write_report_bundle_v1(tmp_path, _sample_report_dict(), include_metrics_summary=True)
    rp = tmp_path / "report.json"
    d = json.loads(rp.read_text(encoding="utf-8"))
    d["equity"] = [999.0, 999.0]
    rp.write_text(json.dumps(d, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    rc = main(["verify", "--bundle-dir", str(tmp_path)])
    assert rc == EXIT_VERIFY_FAILED


def test_verify_tarball_ok(tmp_path: Path) -> None:
    bundle_dir = tmp_path / "bundle"
    bundle_dir.mkdir()
    write_report_bundle_v1(bundle_dir, _sample_report_dict(), include_metrics_summary=True)
    tar_path = tmp_path / "bundle.tgz"
    write_bundle_tarball_v1(bundle_dir, tar_path)
    rc = main(["verify", "--tarball", str(tar_path)])
    assert rc == EXIT_OK


def test_verify_registry_ok(tmp_path: Path) -> None:
    reg = BundleRegistryV1(
        schema_version=1,
        entries=[
            RegistryEntryV1(
                bundle_id="a",
                kind="dir_bundle",
                ref_path="a",
                sha256="0" * 64,
            ),
        ],
    )
    p = tmp_path / "registry.json"
    write_registry_v1(p, reg)
    rc = main(["verify", "--registry", str(p)])
    assert rc == EXIT_OK


def test_list_registry_stable_order(tmp_path: Path) -> None:
    reg = BundleRegistryV1(
        schema_version=1,
        entries=[
            RegistryEntryV1(
                bundle_id="second",
                kind="dir_bundle",
                ref_path="b/second",
                sha256="0" * 64,
            ),
            RegistryEntryV1(
                bundle_id="first",
                kind="dir_bundle",
                ref_path="a/first",
                sha256="0" * 64,
            ),
        ],
    )
    p = tmp_path / "registry.json"
    write_registry_v1(p, reg)
    rc = main(["list", "--registry", str(p)])
    assert rc == EXIT_OK


def test_show_index_entry(tmp_path: Path) -> None:
    idx = BundleIndexV1(
        version=1,
        entries=[
            BundleIndexEntryV1(
                kind="dir_bundle",
                relpath="x/bundle_a.tgz",
                sha256="0" * 64,
                bytes=1,
                report_schema_version=1,
            ),
        ],
    )
    p = tmp_path / "index.json"
    write_bundle_index_v1(p, idx)
    rc = main(["--json", "show", "--index", str(p), "--key", "x/bundle_a.tgz"])
    assert rc == EXIT_OK
