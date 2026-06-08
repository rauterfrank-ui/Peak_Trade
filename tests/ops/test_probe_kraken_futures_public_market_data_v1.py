from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional, Tuple

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRIPT = _REPO_ROOT / "scripts/ops/probe_kraken_futures_public_market_data_v1.py"

_CONFIRM = "CONFIRM_VIEW_ONLY_PUBLIC_MARKET_DATA_PROBE_V1"
_PROVIDER = "kraken_futures_public_market_data_only"

_FORBIDDEN_IN_PROBE_SCRIPT = (
    "import requests",
    "import httpx",
    "import aiohttp",
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
    spec = importlib.util.spec_from_file_location("_kf_probe", _SCRIPT)
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


def _instruments_body(**overrides: Any) -> Dict[str, Any]:
    base: Dict[str, Any] = {
        "result": "success",
        "instruments": [
            {"symbol": "PF_XBTUSD", "type": "flexible_futures", "tradeable": True},
            {"symbol": "PF_ETHUSD", "type": "flexible_futures", "tradeable": True},
            {"symbol": "BTC/USD", "type": "spot", "tradeable": False},
        ],
    }
    base.update(overrides)
    return base


def _tickers_body(**overrides: Any) -> Dict[str, Any]:
    base: Dict[str, Any] = {
        "result": "success",
        "tickers": [
            {"symbol": "PF_XBTUSD", "markPrice": 100000.0, "bid": 99990.0, "ask": 100010.0},
            {"symbol": "PF_ETHUSD", "markPrice": 3500.0, "bid": 3499.0, "ask": 3501.0},
        ],
    }
    base.update(overrides)
    return base


def _mock_fetcher_ok() -> Callable[[str, float, int], Tuple[int, bytes]]:
    responses: Dict[str, Tuple[int, bytes]] = {
        "/derivatives/api/v3/instruments": (
            200,
            json.dumps(_instruments_body()).encode("utf-8"),
        ),
        "/derivatives/api/v3/tickers": (
            200,
            json.dumps(_tickers_body()).encode("utf-8"),
        ),
    }

    def _fetch(url: str, timeout_seconds: float, max_response_bytes: int) -> Tuple[int, bytes]:
        for ep, payload in responses.items():
            if url.endswith(ep.split("/derivatives/api/v3", 1)[-1]):
                raw = payload[1]
                if len(raw) > max_response_bytes:
                    raise ValueError("ERR: HTTP response body exceeds max_response_bytes")
                return payload
        raise ValueError(f"unexpected url: {url}")

    return _fetch


@pytest.fixture
def mod() -> Any:
    return _load_mod()


def test_script_has_no_forbidden_imports_or_patterns() -> None:
    text = _SCRIPT.read_text(encoding="utf-8")
    for frag in _FORBIDDEN_IN_PROBE_SCRIPT:
        assert frag not in text, f"forbidden fragment: {frag!r}"


def test_requires_exact_confirm_token() -> None:
    cp = _run(
        [
            "--confirm-view-only-public-market-data-probe",
            "WRONG",
            "--timeout-seconds",
            "5",
            "--max-response-bytes",
            "8192",
        ]
    )
    assert cp.returncode != 0


def test_validate_probe_url_rejects_spot_host(mod: Any) -> None:
    reasons = mod.validate_probe_url("https://api.kraken.com/derivatives/api/v3/instruments")
    assert "FORBIDDEN_PROVIDER_HOST" in reasons


def test_validate_probe_url_rejects_order_endpoint(mod: Any) -> None:
    reasons = mod.validate_probe_url("https://futures.kraken.com/derivatives/api/v3/sendorder")
    assert "FORBIDDEN_ENDPOINT_PATH" in reasons


def test_validate_probe_url_rejects_private_accounts(mod: Any) -> None:
    reasons = mod.validate_probe_url("https://futures.kraken.com/derivatives/api/v3/accounts")
    assert reasons


def test_validate_probe_url_allows_instruments(mod: Any) -> None:
    assert mod.validate_probe_url("https://futures.kraken.com/derivatives/api/v3/instruments") == []


def test_is_ineligible_spot_symbol_rejects_btc_slash(mod: Any) -> None:
    assert mod.is_ineligible_spot_symbol("BTC/USD") is True
    assert mod.is_ineligible_spot_symbol("PF_XBTUSD") is False


def test_run_probe_mocked_success(mod: Any, capsys: pytest.CaptureFixture[str]) -> None:
    report = mod.run_probe(
        confirm=_CONFIRM,
        timeout_seconds=5.0,
        max_response_bytes=65536,
        fetched_at="2026-06-08T20:00:00Z",
        fetcher=_mock_fetcher_ok(),
    )
    assert report["provider"] == "kraken_futures"
    assert report["provider_id"] == _PROVIDER
    assert report["source_stage"] == "market_data_view_only"
    assert report["auth_used"] is False
    assert report["instruments_count"] == 3
    assert report["futures_only_count"] == 2
    assert report["tickers_count"] == 2
    assert report["readmodel_write_executed"] is False
    assert report["dashboard_wiring_executed"] is False
    assert report["no_truth_go"] is True
    assert report["no_selected_tradable_future"] is True
    preview = report["top20_candidate_preview"]
    assert preview
    assert all(p["preview_only"] and p["not_selected"] for p in preview)
    out = capsys.readouterr().out
    assert "VIEW_ONLY=true" in out
    assert "MARKET_DATA_ONLY=true" in out
    assert "NOT_TRADING=true" in out
    assert "NOT_LIVE_AUTHORIZATION=true" in out


def test_run_probe_rejects_http_error(mod: Any) -> None:
    def _fetch_fail(url: str, timeout_seconds: float, max_response_bytes: int) -> Tuple[int, bytes]:
        return 503, b"{}"

    with pytest.raises(SystemExit):
        mod.run_probe(
            confirm=_CONFIRM,
            timeout_seconds=5.0,
            max_response_bytes=8192,
            fetched_at="2026-06-08T20:00:00Z",
            fetcher=_fetch_fail,
        )


def test_kraken_fetch_blocks_forbidden_host(mod: Any) -> None:
    with pytest.raises(ValueError, match="FORBIDDEN_PROVIDER_HOST"):
        mod.kraken_futures_public_fetch_v1(
            "https://api.kraken.com/derivatives/api/v3/instruments",
            timeout_seconds=3.0,
            max_response_bytes=8192,
        )


def test_build_probe_report_markers(mod: Any) -> None:
    report = mod.build_probe_report(
        fetched_at="2026-06-08T20:00:00Z",
        endpoint_results={
            "/derivatives/api/v3/instruments": {
                "instruments_count": 1,
                "futures_only_count": 1,
                "sample_instruments": [],
            },
            "/derivatives/api/v3/tickers": {"tickers_count": 1},
        },
    )
    assert report["markers"]["NOT_TRUTH_GO"] is True
    assert report["observability_truth_allowed"] is False


def test_cli_mocked_via_output_dir(
    mod: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    mock_fetch = _mock_fetcher_ok()
    real_run_probe = mod.run_probe

    def _run_probe_mocked(**kwargs: Any) -> Dict[str, Any]:
        kwargs["fetcher"] = mock_fetch
        return real_run_probe(**kwargs)

    monkeypatch.setattr(mod, "run_probe", _run_probe_mocked)
    code = mod.main(
        [
            "--confirm-view-only-public-market-data-probe",
            _CONFIRM,
            "--timeout-seconds",
            "5",
            "--max-response-bytes",
            "65536",
            "--output-dir",
            str(tmp_path),
            "--fetched-at-utc",
            "2026-06-08T20:00:00Z",
        ]
    )
    assert code == 0
    out_file = tmp_path / "kraken_futures_public_market_data_probe_report.v1.json"
    assert out_file.is_file()
    payload = json.loads(out_file.read_text(encoding="utf-8"))
    assert payload["provider_id"] == _PROVIDER
