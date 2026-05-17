from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional, Tuple

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRIPT = _REPO_ROOT / "scripts/ops/capture_public_rest_binance_book_ticker_v0.py"

_CONFIRM = "ALLOW_PUBLIC_REST_MARKET_DATA_ONE_SHOT_NO_AUTH_NO_ORDERS"
_PROVIDER = "binance_spot_market_data_only"

_FORBIDDEN_IN_CAPTURE_SCRIPT = (
    "import requests",
    "import httpx",
    "import aiohttp",
    "websocket",
    "import socket",
    "from socket",
    "import subprocess",
    "subprocess.",
    "time.sleep",
    "while True",
    "src.execution",
    "src.live",
    "src.scheduler",
    "src.runtime",
    "import ccxt",
    "click",
    "typer",
    "create_order",
    "place_order",
    "send_order",
    "submit_order",
    "cancel_order",
)


def _load_mod() -> Any:
    spec = importlib.util.spec_from_file_location("_cap_rest", _SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _run(args: List[str], *, cwd: Optional[Path] = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(_SCRIPT), *args],
        cwd=cwd or _REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def _book_response(**overrides: Any) -> Dict[str, Any]:
    base: Dict[str, Any] = {
        "symbol": "BTCUSDT",
        "bidPrice": "100.00",
        "bidQty": "1.0",
        "askPrice": "100.10",
        "askQty": "2.0",
    }
    base.update(overrides)
    return base


def _mock_fetch_ok(
    body: Optional[Mapping[str, Any]] = None, *, status: int = 200
) -> Callable[..., Tuple[int, bytes]]:
    payload = body or _book_response()

    def _inner(
        *, symbol: str, timeout_seconds: float, max_response_bytes: int
    ) -> Tuple[int, bytes]:
        raw = json.dumps(payload).encode("utf-8")
        if len(raw) > max_response_bytes:
            raise ValueError("ERR: HTTP response body exceeds --max-response-bytes")
        return status, raw

    return _inner


@pytest.fixture
def mod() -> Any:
    return _load_mod()


@pytest.fixture
def isolated_out(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_requires_provider(isolated_out: Path) -> None:
    cp = _run(
        [
            "--symbol",
            "BTCUSDT",
            "--output-dir",
            str(isolated_out),
            "--package-id",
            "p.v0",
            "--timeout-seconds",
            "3",
            "--max-response-bytes",
            "8192",
            "--confirm-public-rest-one-shot",
            _CONFIRM,
        ]
    )
    assert cp.returncode != 0
    assert "provider" in ((cp.stderr or "") + (cp.stdout or "")).lower()


def test_requires_symbol(isolated_out: Path) -> None:
    cp = _run(
        [
            "--provider",
            _PROVIDER,
            "--output-dir",
            str(isolated_out),
            "--package-id",
            "p.v0",
            "--timeout-seconds",
            "3",
            "--max-response-bytes",
            "8192",
            "--confirm-public-rest-one-shot",
            _CONFIRM,
        ]
    )
    assert cp.returncode != 0


def test_requires_output_dir(isolated_out: Path) -> None:
    cp = _run(
        [
            "--provider",
            _PROVIDER,
            "--symbol",
            "BTCUSDT",
            "--package-id",
            "p.v0",
            "--timeout-seconds",
            "3",
            "--max-response-bytes",
            "8192",
            "--confirm-public-rest-one-shot",
            _CONFIRM,
        ]
    )
    assert cp.returncode != 0


def test_requires_package_id(isolated_out: Path) -> None:
    cp = _run(
        [
            "--provider",
            _PROVIDER,
            "--symbol",
            "BTCUSDT",
            "--output-dir",
            str(isolated_out),
            "--timeout-seconds",
            "3",
            "--max-response-bytes",
            "8192",
            "--confirm-public-rest-one-shot",
            _CONFIRM,
        ]
    )
    assert cp.returncode != 0


def test_requires_timeout_seconds(isolated_out: Path) -> None:
    cp = _run(
        [
            "--provider",
            _PROVIDER,
            "--symbol",
            "BTCUSDT",
            "--output-dir",
            str(isolated_out),
            "--package-id",
            "p.v0",
            "--max-response-bytes",
            "8192",
            "--confirm-public-rest-one-shot",
            _CONFIRM,
        ]
    )
    assert cp.returncode != 0


def test_requires_max_response_bytes(isolated_out: Path) -> None:
    cp = _run(
        [
            "--provider",
            _PROVIDER,
            "--symbol",
            "BTCUSDT",
            "--output-dir",
            str(isolated_out),
            "--package-id",
            "p.v0",
            "--timeout-seconds",
            "3",
            "--confirm-public-rest-one-shot",
            _CONFIRM,
        ]
    )
    assert cp.returncode != 0


def test_requires_exact_confirm_token(isolated_out: Path) -> None:
    cp = _run(
        [
            "--provider",
            _PROVIDER,
            "--symbol",
            "BTCUSDT",
            "--output-dir",
            str(isolated_out),
            "--package-id",
            "p.v0",
            "--timeout-seconds",
            "3",
            "--max-response-bytes",
            "8192",
            "--confirm-public-rest-one-shot",
            "WRONG",
        ]
    )
    assert cp.returncode != 0


def test_rejects_wrong_provider(isolated_out: Path) -> None:
    cp = _run(
        [
            "--provider",
            "other",
            "--symbol",
            "BTCUSDT",
            "--output-dir",
            str(isolated_out),
            "--package-id",
            "p.v0",
            "--timeout-seconds",
            "3",
            "--max-response-bytes",
            "8192",
            "--confirm-public-rest-one-shot",
            _CONFIRM,
        ]
    )
    assert cp.returncode != 0


def test_rejects_unsupported_symbol_via_api(mod: Any, isolated_out: Path) -> None:
    with pytest.raises(SystemExit):
        mod.run_capture(
            symbol="ETHUSDT",
            output_dir=isolated_out,
            package_id="pkg.sym",
            timeout_seconds=3,
            max_response_bytes=8192,
            confirm=_CONFIRM,
            captured_at_utc="2026-01-01T00:00:00Z",
            fetcher=_mock_fetch_ok(),
        )


def test_rejects_timeout_over_five(isolated_out: Path) -> None:
    cp = _run(
        [
            "--provider",
            _PROVIDER,
            "--symbol",
            "BTCUSDT",
            "--output-dir",
            str(isolated_out),
            "--package-id",
            "p.v0",
            "--timeout-seconds",
            "9",
            "--max-response-bytes",
            "8192",
            "--confirm-public-rest-one-shot",
            _CONFIRM,
        ]
    )
    assert cp.returncode != 0
    assert "timeout" in (cp.stderr or "").lower()


def test_rejects_max_response_bytes_over_cap(isolated_out: Path) -> None:
    cp = _run(
        [
            "--provider",
            _PROVIDER,
            "--symbol",
            "BTCUSDT",
            "--output-dir",
            str(isolated_out),
            "--package-id",
            "p.v0",
            "--timeout-seconds",
            "3",
            "--max-response-bytes",
            "2097152",
            "--confirm-public-rest-one-shot",
            _CONFIRM,
        ]
    )
    assert cp.returncode != 0


def test_rejects_unsafe_package_id(isolated_out: Path) -> None:
    cp = _run(
        [
            "--provider",
            _PROVIDER,
            "--symbol",
            "BTCUSDT",
            "--output-dir",
            str(isolated_out),
            "--package-id",
            "../evil",
            "--timeout-seconds",
            "3",
            "--max-response-bytes",
            "8192",
            "--confirm-public-rest-one-shot",
            _CONFIRM,
        ]
    )
    assert cp.returncode != 0


def test_rejects_oversized_response(mod: Any, isolated_out: Path) -> None:
    def fetch_big(
        *, symbol: str, timeout_seconds: float, max_response_bytes: int
    ) -> Tuple[int, bytes]:
        raise ValueError("ERR: HTTP response body exceeds --max-response-bytes")

    with pytest.raises(SystemExit):
        mod.run_capture(
            symbol="BTCUSDT",
            output_dir=isolated_out,
            package_id="pkg.big",
            timeout_seconds=3,
            max_response_bytes=100,
            confirm=_CONFIRM,
            captured_at_utc="2026-01-01T00:00:00Z",
            fetcher=fetch_big,
        )


def test_rejects_invalid_json_response(mod: Any, isolated_out: Path) -> None:
    def bad_fetch(
        *, symbol: str, timeout_seconds: float, max_response_bytes: int
    ) -> Tuple[int, bytes]:
        return 200, b"not-json{"

    with pytest.raises(SystemExit):
        mod.run_capture(
            symbol="BTCUSDT",
            output_dir=isolated_out,
            package_id="pkg.badjson",
            timeout_seconds=3,
            max_response_bytes=8192,
            confirm=_CONFIRM,
            captured_at_utc="2026-01-01T00:00:00Z",
            fetcher=bad_fetch,
        )


def test_rejects_missing_bid_ask_fields(mod: Any, isolated_out: Path) -> None:
    incomplete = {"symbol": "BTCUSDT", "bidPrice": "1", "askPrice": "2"}

    with pytest.raises(SystemExit):
        mod.run_capture(
            symbol="BTCUSDT",
            output_dir=isolated_out,
            package_id="pkg.miss",
            timeout_seconds=3,
            max_response_bytes=8192,
            confirm=_CONFIRM,
            captured_at_utc="2026-01-01T00:00:00Z",
            fetcher=_mock_fetch_ok(body=incomplete),
        )


def test_rejects_ask_not_greater_than_bid(mod: Any, isolated_out: Path) -> None:
    with pytest.raises(SystemExit):
        mod.run_capture(
            symbol="BTCUSDT",
            output_dir=isolated_out,
            package_id="pkg.spread",
            timeout_seconds=3,
            max_response_bytes=8192,
            confirm=_CONFIRM,
            captured_at_utc="2026-01-01T00:00:00Z",
            fetcher=_mock_fetch_ok(body=_book_response(bidPrice="100.10", askPrice="100.00")),
        )


def test_rejects_forbidden_nested_key(mod: Any, isolated_out: Path) -> None:
    bad = _book_response()
    bad["api_key"] = "leak"

    with pytest.raises(SystemExit):
        mod.run_capture(
            symbol="BTCUSDT",
            output_dir=isolated_out,
            package_id="pkg.forbid",
            timeout_seconds=3,
            max_response_bytes=8192,
            confirm=_CONFIRM,
            captured_at_utc="2026-01-01T00:00:00Z",
            fetcher=_mock_fetch_ok(body=bad),
        )


def test_happy_path_writes_package_layout(
    mod: Any, isolated_out: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    mod.run_capture(
        symbol="BTCUSDT",
        output_dir=isolated_out,
        package_id="pkg.ok",
        timeout_seconds=3,
        max_response_bytes=8192,
        confirm=_CONFIRM,
        captured_at_utc="2026-05-17T12:00:00Z",
        fetcher=_mock_fetch_ok(),
    )
    root = isolated_out / "pkg.ok"
    raw_p = root / "raw" / "public_rest_book_ticker_raw.json"
    norm_p = root / "normalized" / "captured_realistic_snapshots.json"
    cap_p = root / "manifest" / "capture_manifest.json"
    sup_p = root / "manifest" / "supervised_timed_manifest.json"
    co_p = root / "PUBLIC_REST_CAPTURE_CLOSEOUT.md"
    assert (
        raw_p.is_file()
        and norm_p.is_file()
        and cap_p.is_file()
        and sup_p.is_file()
        and co_p.is_file()
    )

    raw_obj = json.loads(raw_p.read_text(encoding="utf-8"))
    assert raw_obj["schema"] == "public_rest_market_snapshot_raw_v0"
    assert raw_obj["provider"] == _PROVIDER

    norm_obj = json.loads(norm_p.read_text(encoding="utf-8"))
    assert norm_obj["schema"] == "captured_realistic_snapshot_observation_input_v0"
    assert norm_obj["source"] == "redacted_public_snapshot_static"
    assert len(norm_obj["snapshots"]) == 1
    pl = norm_obj["snapshots"][0]["payload"]
    assert pl["source_state"] == "public_rest_snapshot_one_shot"
    assert pl["volume"] == "0"
    assert pl["bid_qty"] == "1.0"
    assert pl["ask_qty"] == "2.0"

    cap = json.loads(cap_p.read_text(encoding="utf-8"))
    rh = hashlib.sha256(raw_p.read_bytes()).hexdigest()
    nh = hashlib.sha256(norm_p.read_bytes()).hexdigest()
    assert cap["raw_sha256"] == rh
    assert cap["normalized_sha256"] == nh
    assert cap["snapshot_count"] == 1

    sup = json.loads(sup_p.read_text(encoding="utf-8"))
    assert sup["max_observations"] == 1
    inp = sup["inputs"][0]["input_file"]
    assert Path(inp).is_absolute()
    assert Path(inp) == norm_p.resolve()

    txt = co_p.read_text(encoding="utf-8")
    assert "VERDICT=PUBLIC_REST_BINANCE_BOOK_TICKER_CAPTURE_V0_CREATED_NOT_APPROVED" in txt
    assert "ORDER_SUBMISSION_ALLOWED=false" in txt

    out = capsys.readouterr().out
    assert "VERDICT=PUBLIC_REST_BINANCE_BOOK_TICKER_CAPTURE_V0_CREATED_NOT_APPROVED" in out


def test_forbidden_tokens_not_present_in_new_script() -> None:
    text = _SCRIPT.read_text(encoding="utf-8")
    for frag in _FORBIDDEN_IN_CAPTURE_SCRIPT:
        assert frag not in text


def test_repo_root_has_no_accidental_public_rest_raw_artifact_at_repo_root() -> None:
    assert not (_REPO_ROOT / "raw" / "public_rest_book_ticker_raw.json").exists()


def test_failure_closeout_machine_lines(mod: Any, isolated_out: Path) -> None:
    def bad_fetch(
        *, symbol: str, timeout_seconds: float, max_response_bytes: int
    ) -> Tuple[int, bytes]:
        return 503, b"{}"

    with pytest.raises(SystemExit):
        mod.run_capture(
            symbol="BTCUSDT",
            output_dir=isolated_out,
            package_id="pkg.fail503",
            timeout_seconds=3,
            max_response_bytes=8192,
            confirm=_CONFIRM,
            captured_at_utc="2026-01-01T00:00:00Z",
            fetcher=bad_fetch,
        )
    fail_co = isolated_out / "pkg.fail503" / "PUBLIC_REST_CAPTURE_CLOSEOUT.md"
    assert fail_co.is_file()
    fb = fail_co.read_text(encoding="utf-8")
    assert "VERDICT=PUBLIC_REST_BINANCE_BOOK_TICKER_CAPTURE_V0_FAILED_NOT_APPROVED" in fb
    assert "NEXT_ACTION=review_public_rest_capture_failure_or_stop_idle" in fb
