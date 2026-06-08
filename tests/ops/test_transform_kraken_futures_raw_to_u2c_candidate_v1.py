from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, List

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRIPT = _REPO_ROOT / "scripts/ops/transform_kraken_futures_raw_to_u2c_candidate_v1.py"
_FIXTURES = _REPO_ROOT / "tests/fixtures/u5d_offline_transform_v1/minimal"
_CONFIRM = "CONFIRM_U5D_OFFLINE_TRANSFORM_VALIDATION_V1"

_FORBIDDEN_IN_SCRIPT = (
    "import requests",
    "import httpx",
    "import aiohttp",
    "urllib.request",
    "urllib.error",
    "websocket",
    "time.sleep",
    "while True",
    "src.execution",
    "src.live",
    "src.scheduler",
    "import ccxt",
    "create_order",
    "place_order",
    "send_order",
    "submit_order",
    "cancel_order",
)


def _load_mod() -> Any:
    spec = importlib.util.spec_from_file_location("_u5d_transform", _SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _run(args: List[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(_SCRIPT), *args],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.fixture
def mod() -> Any:
    return _load_mod()


@pytest.fixture
def fixture_paths(tmp_path: Path) -> dict[str, Path]:
    return {
        "instruments": _FIXTURES / "kraken_futures_instruments.raw.v1.json",
        "tickers": _FIXTURES / "kraken_futures_tickers.raw.v1.json",
        "probe": _FIXTURES / "kraken_futures_public_market_data_probe_report.v1.json",
        "output": tmp_path / "out",
    }


def test_script_has_no_forbidden_imports_or_patterns() -> None:
    text = _SCRIPT.read_text(encoding="utf-8")
    for frag in _FORBIDDEN_IN_SCRIPT:
        assert frag not in text, f"forbidden fragment: {frag!r}"


def test_cli_requires_exact_confirm_token(fixture_paths: dict[str, Path]) -> None:
    cp = _run(
        [
            "--raw-instruments",
            str(fixture_paths["instruments"]),
            "--raw-tickers",
            str(fixture_paths["tickers"]),
            "--probe-report",
            str(fixture_paths["probe"]),
            "--output-dir",
            str(fixture_paths["output"]),
            "--confirm-offline-transform-validation",
            "WRONG",
        ]
    )
    assert cp.returncode != 0


def test_run_offline_transform_validation_success(
    mod: Any, fixture_paths: dict[str, Path], capsys: pytest.CaptureFixture[str]
) -> None:
    artifact = mod.run_offline_transform_validation(
        confirm=_CONFIRM,
        raw_instruments=fixture_paths["instruments"],
        raw_tickers=fixture_paths["tickers"],
        probe_report=fixture_paths["probe"],
        output_dir=fixture_paths["output"],
    )
    assert artifact["schema"] == "u5d_u2c_candidate_validation_v1"
    assert artifact["source_stage"] == "market_data_view_only"
    assert artifact["provider"] == "kraken_futures"
    assert artifact["transform_validation_only"] is True
    assert artifact["GOVERNED_SNAPSHOT_ACCEPTED"] is False
    assert artifact["SNAPSHOT_INTAKE_EXECUTED"] is False
    assert artifact["LOADER_RUN_EXECUTED"] is False
    assert artifact["READMODEL_WRITE_EXECUTED"] is False
    assert artifact["DASHBOARD_WIRING_EXECUTED"] is False
    assert artifact["LIVE_AUTHORIZED"] is False
    assert artifact["PREFLIGHT_LIFT_AUTHORIZED"] is False
    assert artifact["selected_tradable_future_created"] is False

    join = artifact["join"]
    assert join["join_key"] == "symbol"
    assert join["instruments_eligible_count"] == 3
    assert join["matched_count"] == 3
    assert any(r["reason"] == "INELIGIBLE_SPOT_SYMBOL" for r in join["rejected_symbols"])
    assert any(r["reason"] == "EXPIRED_INSTRUMENT" for r in join["rejected_symbols"])
    assert any(o["symbol"] == "FI_LTCUSD_250131" for o in join["orphan_tickers"])

    top20 = artifact["top20_ranking_candidate"]
    assert len(top20) == 2
    assert top20[0]["symbol"] == "PF_ETHUSD"
    assert top20[1]["symbol"] == "PF_XBTUSD"
    assert all(t["not_alphabetical_preview"] for t in top20)
    assert artifact["ranking_notes"]["u5b_alphabetical_preview_not_reused"] is True

    eth = next(p for p in artifact["packet_candidates"] if p["symbol"] == "PF_ETHUSD")
    assert eth["display_price"] == 3500.0
    assert eth["display_price_source"] == "markPrice"
    assert "last_missing_markPrice_fallback" in eth["degraded_fields"]

    ada = next(p for p in artifact["packet_candidates"] if p["symbol"] == "PF_ADAUSD")
    assert ada["vol24h"] == 0.0
    assert "vol24h" in ada["missing_fields"]

    out_json = fixture_paths["output"] / "u5d_u2c_candidate_validation.v1.json"
    assert out_json.is_file()
    assert (fixture_paths["output"] / "transform_summary.md").is_file()

    out = capsys.readouterr().out
    assert "TRANSFORM_VALIDATION_ONLY=true" in out
    assert "NOT_TRADING=true" in out
    assert "GOVERNED_SNAPSHOT_ACCEPTED=false" in out


def test_slash_spot_symbols_rejected(
    mod: Any, fixture_paths: dict[str, Path], tmp_path: Path
) -> None:
    artifact = mod.run_offline_transform_validation(
        confirm=_CONFIRM,
        raw_instruments=fixture_paths["instruments"],
        raw_tickers=fixture_paths["tickers"],
        probe_report=fixture_paths["probe"],
        output_dir=tmp_path / "out2",
    )
    rejected = {r["symbol"]: r["reason"] for r in artifact["join"]["rejected_symbols"]}
    assert rejected.get("BTC/USD") == "INELIGIBLE_SPOT_SYMBOL"
    symbols = [p["symbol"] for p in artifact["packet_candidates"]]
    assert "BTC/USD" not in symbols


def test_top20_ranking_deterministic_by_vol24h(mod: Any) -> None:
    rows = [
        {"symbol": "PF_A", "active": True, "vol24h": 100.0},
        {"symbol": "PF_B", "active": True, "vol24h": 200.0},
        {"symbol": "PF_C", "active": True, "vol24h": 200.0},
    ]
    top = mod.build_top20_ranking_candidate(rows)
    assert [t["symbol"] for t in top] == ["PF_B", "PF_C", "PF_A"]


def test_missing_required_inputs_fail(
    mod: Any, fixture_paths: dict[str, Path], tmp_path: Path
) -> None:
    with pytest.raises(SystemExit):
        mod.run_offline_transform_validation(
            confirm=_CONFIRM,
            raw_instruments=tmp_path / "missing.json",
            raw_tickers=fixture_paths["tickers"],
            probe_report=fixture_paths["probe"],
            output_dir=tmp_path / "out3",
        )


def test_cli_end_to_end_writes_outputs(fixture_paths: dict[str, Path], tmp_path: Path) -> None:
    out_dir = tmp_path / "cli_out"
    cp = _run(
        [
            "--raw-instruments",
            str(fixture_paths["instruments"]),
            "--raw-tickers",
            str(fixture_paths["tickers"]),
            "--probe-report",
            str(fixture_paths["probe"]),
            "--output-dir",
            str(out_dir),
            "--confirm-offline-transform-validation",
            _CONFIRM,
        ]
    )
    assert cp.returncode == 0, cp.stderr
    payload = json.loads((out_dir / "u5d_u2c_candidate_validation.v1.json").read_text())
    assert payload["schema"] == "u5d_u2c_candidate_validation_v1"
    assert payload["selected_tradable_future_created"] is False
    assert "strategy_score" not in json.dumps(payload)
