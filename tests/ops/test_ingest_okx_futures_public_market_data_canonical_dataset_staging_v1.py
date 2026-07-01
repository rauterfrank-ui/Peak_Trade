from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional, Tuple

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRIPT = (
    _REPO_ROOT / "scripts/ops/ingest_okx_futures_public_market_data_canonical_dataset_staging_v1.py"
)

_GO_TOKEN = "GO_OKX_FUTURES_MARKET_DATA_INGESTION_AND_CANONICAL_DATASET_STAGING_V1"
_NATIVE = "ETH-USDT-SWAP"

_FORBIDDEN_IMPORTS_IN_SCRIPT = (
    "import requests",
    "import httpx",
    "import aiohttp",
    "import ccxt",
    "create_order",
    "place_order",
    "send_order",
    "src.execution",
    "src.live",
    "src.scheduler",
)


def _load_mod() -> Any:
    spec = importlib.util.spec_from_file_location("_okx_ingest", _SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _run(args: List[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(_SCRIPT), *args],
        cwd=cwd or _REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def _instruments_ok() -> bytes:
    payload = {
        "code": "0",
        "data": [
            {
                "instId": _NATIVE,
                "instType": "SWAP",
                "baseCcy": "ETH",
                "settleCcy": "USDT",
                "ctVal": "0.1",
                "ctValCcy": "ETH",
                "tickSz": "0.01",
                "lotSz": "1",
                "minSz": "1",
                "state": "live",
                "listTime": "1609459200000",
                "expTime": "",
            }
        ],
    }
    return json.dumps(payload).encode("utf-8")


def _candle_rows(ts_start: int, count: int, *, fields: int = 9) -> bytes:
    rows = []
    for i in range(count):
        ts = str(ts_start + i * 60_000)
        if fields >= 9:
            rows.append([ts, "100", "101", "99", "100.5", "1000", "0", "0", "1"])
        else:
            rows.append([ts, "100", "101", "99", "100.5", "1"])
    return json.dumps({"code": "0", "data": rows}).encode("utf-8")


def _funding_rows(ts_start: int, count: int) -> bytes:
    rows = []
    for i in range(count):
        rows.append(
            {
                "instId": _NATIVE,
                "fundingRate": "0.0001",
                "fundingTime": str(ts_start + i * 28_800_000),
                "realizedRate": "0.0001",
            }
        )
    return json.dumps({"code": "0", "data": rows}).encode("utf-8")


def _mock_fetcher_full() -> Callable[..., Tuple[int, bytes, Dict[str, str]]]:
    from datetime import datetime, timedelta, timezone

    end_dt = datetime.now(timezone.utc).replace(second=0, microsecond=0) - timedelta(minutes=1)
    ts_start = int((end_dt - timedelta(hours=2)).timestamp() * 1000)
    state: Dict[str, int] = {"ohlcv": 0, "mark": 0, "index": 0, "funding": 0}

    def _fetch(
        url: str,
        *,
        timeout_seconds: float,
        max_response_bytes: int,
        headers: Optional[Mapping[str, str]] = None,
    ) -> Tuple[int, bytes, Dict[str, str]]:
        if headers and any(k.upper().startswith("OK-ACCESS") for k in headers):
            raise ValueError("auth forbidden")
        path = url.split("?", 1)[0].split(".com", 1)[-1]
        if path.endswith("/public/instruments"):
            return 200, _instruments_ok(), {}
        if path.endswith("/history-candles"):
            state["ohlcv"] += 1
            if state["ohlcv"] > 1:
                return 200, json.dumps({"code": "0", "data": []}).encode(), {}
            return 200, _candle_rows(ts_start, 5), {}
        if path.endswith("/history-mark-price-candles"):
            state["mark"] += 1
            if state["mark"] > 1:
                return 200, json.dumps({"code": "0", "data": []}).encode(), {}
            return 200, _candle_rows(ts_start, 5, fields=6), {}
        if path.endswith("/history-index-candles"):
            state["index"] += 1
            if state["index"] > 1:
                return 200, json.dumps({"code": "0", "data": []}).encode(), {}
            assert "instId=ETH-USDT" in url
            return 200, _candle_rows(ts_start, 5, fields=6), {}
        if path.endswith("/funding-rate-history"):
            state["funding"] += 1
            if state["funding"] > 1:
                return 200, json.dumps({"code": "0", "data": []}).encode(), {}
            return 200, _funding_rows(ts_start, 3), {}
        raise ValueError(f"unexpected url: {url}")

    return _fetch


class TestStaticContracts:
    def test_script_has_no_forbidden_imports_or_auth(self) -> None:
        text = _SCRIPT.read_text(encoding="utf-8")
        for token in _FORBIDDEN_IMPORTS_IN_SCRIPT:
            assert token not in text

    def test_public_endpoint_allowlist_excludes_private_paths(self) -> None:
        mod = _load_mod()
        for path in (
            "/api/v5/trade/order",
            "/api/v5/account/balance",
            "/api/v5/asset/currencies",
        ):
            url = f"https://www.okx.com{path}"
            reasons = mod.validate_public_get_url(url)
            assert reasons, url

    def test_allowed_public_endpoints_pass_validation(self) -> None:
        mod = _load_mod()
        for path in mod.ALLOWED_PUBLIC_GET_PATHS:
            url = f"https://www.okx.com{path}?instId=ETH-USDT-SWAP"
            assert mod.validate_public_get_url(url) == []

    def test_btc_spot_instrument_rejected(self) -> None:
        mod = _load_mod()
        with pytest.raises(mod.IngestionError):
            mod.validate_eth_usdt_swap_instrument(
                {"instId": "BTC-USDT-SWAP", "instType": "SWAP", "baseCcy": "BTC"}
            )

    def test_eth_swap_instrument_mapping(self) -> None:
        mod = _load_mod()
        meta = mod.validate_eth_usdt_swap_instrument(
            {
                "instId": _NATIVE,
                "instType": "SWAP",
                "baseCcy": "ETH",
                "settleCcy": "USDT",
                "listTime": "1609459200000",
            }
        )
        assert meta["canonical_instrument_id"] == "inst-eth-usdt-perp"

    def test_historical_bid_ask_not_available(self) -> None:
        mod = _load_mod()
        cap = mod.probe_historical_bid_ask_capability(
            fetcher=_mock_fetcher_full(),
            rate_limiter=mod.RateLimiter(),
            timeout_seconds=5.0,
            max_response_bytes=1_000_000,
        )
        assert cap["historical_public_bid_ask_available"] is False
        assert cap["synthetic_bid_ask_forbidden"] is True

    def test_auth_header_forbidden_on_fetch(self) -> None:
        mod = _load_mod()
        url = "https://www.okx.com/api/v5/public/instruments?instType=SWAP"
        with pytest.raises(mod.IngestionError, match="auth_header_forbidden"):
            mod.okx_public_fetch_v1(
                url,
                timeout_seconds=5.0,
                max_response_bytes=1_000_000,
                headers={"OK-ACCESS-KEY": "x"},
            )


class TestRunIngestionMocked:
    def test_schema_incomplete_without_historical_bid_ask(self, tmp_path: Path) -> None:
        mod = _load_mod()
        target = tmp_path / "datasets/admissible_futures/inst-eth-usdt-perp/v1"
        evidence = tmp_path / "evidence"
        result = mod.run_ingestion(
            confirm=_GO_TOKEN,
            target_dataset_root=target,
            durable_evidence_root=evidence,
            staging_window_days=1,
            fetcher=_mock_fetcher_full(),
        )
        assert result["verdict"] == "OKX_DATA_ACQUIRED_SCHEMA_INCOMPLETE"
        assert result["real_admissible_futures_dataset_found"] is False
        assert not target.exists()
        assert result["availability_matrix"]["best_bid"]["available"] is False
        assert result["manifest_verify_rc"] == 0

    def test_skip_network_offline_path(self, tmp_path: Path) -> None:
        mod = _load_mod()
        target = tmp_path / "target/v1"
        evidence = tmp_path / "evidence"
        result = mod.run_ingestion(
            confirm=_GO_TOKEN,
            target_dataset_root=target,
            durable_evidence_root=evidence,
            skip_network=True,
        )
        assert result["verdict"] == "OKX_DATA_ACQUIRED_SCHEMA_INCOMPLETE"

    def test_confirm_token_required(self, tmp_path: Path) -> None:
        mod = _load_mod()
        with pytest.raises(SystemExit):
            mod.run_ingestion(
                confirm="WRONG",
                target_dataset_root=tmp_path / "t",
                durable_evidence_root=tmp_path / "e",
                skip_network=True,
            )

    def test_existing_target_fail_closed(self, tmp_path: Path) -> None:
        mod = _load_mod()
        target = tmp_path / "existing/v1"
        target.mkdir(parents=True)
        with pytest.raises(SystemExit):
            mod.run_ingestion(
                confirm=_GO_TOKEN,
                target_dataset_root=target,
                durable_evidence_root=tmp_path / "e",
                skip_network=True,
            )


class TestCli:
    def test_cli_skip_network(self, tmp_path: Path) -> None:
        target = tmp_path / "datasets/admissible_futures/inst-eth-usdt-perp/v1"
        evidence = tmp_path / "archive"
        proc = _run(
            [
                "--confirm-go-token",
                _GO_TOKEN,
                "--target-dataset-root",
                str(target),
                "--durable-evidence-root",
                str(evidence),
                "--skip-network",
            ]
        )
        assert proc.returncode == 0
        assert "VERDICT=OKX_DATA_ACQUIRED_SCHEMA_INCOMPLETE" in proc.stdout
