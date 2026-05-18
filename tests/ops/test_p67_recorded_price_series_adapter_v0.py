"""Tests for P67 recorded price series adapter v0 (local JSON → simple returns, no network)."""

from __future__ import annotations

import json
import math
import re
import subprocess
import sys
from pathlib import Path

import pytest

from src.ops.p67.recorded_price_series_v0 import (
    load_simple_returns_from_recorded_price_source,
    validate_recorded_price_source_path,
)
from src.ops.p67.shadow_session_scheduler_v1 import P67RunContextV1, run_shadow_session_scheduler_v1

REPO_ROOT = Path(__file__).resolve().parents[2]
_ADAPTER = REPO_ROOT / "src" / "ops" / "p67" / "recorded_price_series_v0.py"
_SHADOW_LOOP = REPO_ROOT / "scripts" / "ops" / "run_shadow_loop_v1.sh"


def _write_book_ticker_mids(src: Path, n: int) -> None:
    rows = []
    for i in range(n):
        bid = f"{100 + i}.00"
        ask = f"{100 + i}.50"
        rows.append({"bidPrice": bid, "askPrice": ask, "symbol": "BTCUSDT"})
    src.mkdir(parents=True, exist_ok=True)
    (src / "mids.json").write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")


def test_adapter_extracts_mids_and_returns(tmp_path: Path) -> None:
    _write_book_ticker_mids(tmp_path, 61)
    returns, _ = load_simple_returns_from_recorded_price_source(tmp_path)
    assert len(returns) == 60
    assert all(math.isfinite(r) for r in returns)
    assert returns[0] > 0  # price increases each step


def test_adapter_rejects_missing_path() -> None:
    ok, err = validate_recorded_price_source_path("/tmp/peak_trade_nonexistent_dir_xyz_12345")
    assert ok is None
    assert err and "does not exist" in err


def test_adapter_rejects_repo_path(tmp_path: Path) -> None:
    inside = REPO_ROOT / "peak_trade_forbidden_recorded_src"
    inside.mkdir(exist_ok=True)
    try:
        ok, err = validate_recorded_price_source_path(str(inside.resolve()))
        assert ok is None
        assert err and "repository" in err.lower()
    finally:
        inside.rmdir()


def test_adapter_rejects_nonfinite_mid(tmp_path: Path) -> None:
    rows = []
    for i in range(61):
        if i == 30:
            rows.append({"bidPrice": "nan", "askPrice": "131.0"})
        else:
            bid = f"{100 + i}.00"
            ask = f"{100 + i}.50"
            rows.append({"bidPrice": bid, "askPrice": ask})
    tmp_path.mkdir(parents=True, exist_ok=True)
    (tmp_path / "mids.json").write_text(json.dumps(rows), encoding="utf-8")
    with pytest.raises(ValueError, match="non-finite"):
        load_simple_returns_from_recorded_price_source(tmp_path)


def test_adapter_has_no_network_import_patterns() -> None:
    text = _ADAPTER.read_text(encoding="utf-8")
    banned = re.compile(
        r"(?m)^\s*(?:from\s+(requests|httpx|websocket|websockets|aiohttp|ccxt)\b"
        r"|import\s+(requests|httpx|websocket|websockets|aiohttp|ccxt)\b"
        r"|from\s+urllib\.request\b"
        r"|import\s+urllib\.request\b)",
    )
    assert banned.search(text) is None


def test_p67_uses_adapter_when_recorded_source_set(tmp_path: Path) -> None:
    gate = tmp_path / "gate"
    _write_book_ticker_mids(gate, 61)
    out = run_shadow_session_scheduler_v1(
        P67RunContextV1(
            mode="shadow",
            iterations=1,
            interval_seconds=0.0,
            recorded_price_source=gate,
        ),
    )
    assert out["meta"]["recorded_price_source_used"] is True
    assert out["meta"]["recorded_price_series_count"] == 60
    assert out["meta"]["recorded_price_source_path"] == str(gate.resolve())


def test_p67_default_prices_when_no_source(tmp_path: Path) -> None:
    out = run_shadow_session_scheduler_v1(
        P67RunContextV1(
            mode="shadow",
            iterations=1,
            interval_seconds=0.0,
            out_dir=tmp_path,
            run_id="ndef",
        ),
    )
    assert out["meta"]["recorded_price_source_used"] is False
    assert out["meta"]["recorded_price_source_path"] is None
    assert out["meta"]["recorded_price_series_count"] is None


def test_cli_accepts_recorded_price_source() -> None:
    out = subprocess.run(
        [
            sys.executable,
            "-m",
            "src.ops.p67.shadow_session_scheduler_cli_v1",
            "--help",
        ],
        cwd=str(REPO_ROOT),
        check=True,
        capture_output=True,
        text=True,
    )
    assert "--recorded-price-source" in out.stdout


def test_run_shadow_loop_passes_recorded_source_env() -> None:
    text = _SHADOW_LOOP.read_text(encoding="utf-8")
    assert "RECORDED_PRICE_SOURCE" in text
    assert "--recorded-price-source" in text
