#!/usr/bin/env python3
"""U5B: bounded Kraken Futures public market-data-only probe (urllib, one-shot, no auth).

Explicit manual CLI with confirm token. Public GET allowlist from U5 charter only.
Not broker, orders, scheduler, daemon, dashboard wiring, readmodel write, or truth-GO.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple
from urllib import error, parse, request

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

CONFIRM_TOKEN = "CONFIRM_VIEW_ONLY_PUBLIC_MARKET_DATA_PROBE_V1"
PROVIDER_ID = "kraken_futures_public_market_data_only"
DEFAULT_HOST = "https://futures.kraken.com"
REST_BASE_URL = f"{DEFAULT_HOST}/derivatives/api/v3"
SOURCE_STAGE = "market_data_view_only"

ALLOWED_PUBLIC_GET_PATHS: frozenset[str] = frozenset(
    {
        "/derivatives/api/v3/instruments",
        "/derivatives/api/v3/tickers",
    }
)
PUBLIC_ENDPOINT_ORDER: Tuple[str, ...] = (
    "/derivatives/api/v3/instruments",
    "/derivatives/api/v3/tickers",
)

FORBIDDEN_PATH_SUBSTRINGS: Tuple[str, ...] = (
    "sendorder",
    "cancelorder",
    "cancelallorders",
    "accounts",
    "openpositions",
    "openorders",
)

FORBIDDEN_HOST_NETLOCS: frozenset[str] = frozenset({"api.kraken.com"})

MAX_TIMEOUT_SECONDS = 15.0
MAX_RESPONSE_BYTES_DEFAULT = 1_048_576

_INELIGIBLE_SPOT_SYMBOL_EXACT: frozenset[str] = frozenset(
    {"BTC/USD", "BTC-USD", "ETH/USD", "BTC/EUR"}
)

_FUTURES_TYPE_MARKERS: Tuple[str, ...] = (
    "futures",
    "perpetual",
    "flexible_futures",
    "fixed_income",
)


PublicGetFetcher = Callable[[str, float, int], Tuple[int, bytes]]


def _die(msg: str, code: int = 2) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def _utc_now_z() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def is_ineligible_spot_symbol(symbol: str) -> bool:
    """Reject slash-pair spot symbols as futures truth (U5 charter)."""
    s = (symbol or "").strip()
    if not s:
        return True
    if s in _INELIGIBLE_SPOT_SYMBOL_EXACT:
        return True
    if "/" in s:
        return True
    return False


def is_futures_eligible_instrument(inst: Mapping[str, Any]) -> bool:
    symbol = str(inst.get("symbol") or "")
    if is_ineligible_spot_symbol(symbol):
        return False
    inst_type = str(inst.get("type") or inst.get("contract_type") or "").lower()
    if any(marker in inst_type for marker in _FUTURES_TYPE_MARKERS):
        return True
    if symbol.startswith(("PF_", "PI_", "FF_")):
        return True
    return False


def validate_probe_url(url: str, *, rest_base_url: str = REST_BASE_URL) -> List[str]:
    """Fail-closed URL policy; returns reasons (empty = allowed)."""
    reasons: List[str] = []
    parsed = parse.urlparse(url)
    if parsed.scheme != "https":
        reasons.append("FORBIDDEN_PROVIDER_SCHEME")
    if parsed.netloc in FORBIDDEN_HOST_NETLOCS:
        reasons.append("FORBIDDEN_PROVIDER_HOST")
    if parsed.netloc != "futures.kraken.com":
        reasons.append("FORBIDDEN_PROVIDER_HOST")
    path = parsed.path or ""
    path_lower = path.lower()
    for frag in FORBIDDEN_PATH_SUBSTRINGS:
        if frag in path_lower:
            reasons.append("FORBIDDEN_ENDPOINT_PATH")
            break
    if path not in ALLOWED_PUBLIC_GET_PATHS:
        reasons.append("ENDPOINT_NOT_IN_ALLOWLIST")
    base = rest_base_url.rstrip("/")
    if not url.startswith(base):
        reasons.append("URL_OUTSIDE_REST_BASE")
    return reasons


def _read_body_capped(resp: Any, max_response_bytes: int) -> bytes:
    out = bytearray()
    while len(out) <= max_response_bytes:
        chunk = resp.read(min(65536, max(0, max_response_bytes - len(out) + 1)))
        if not chunk:
            break
        out.extend(chunk)
        if len(out) > max_response_bytes:
            raise ValueError("ERR: HTTP response body exceeds max_response_bytes")
    return bytes(out)


def kraken_futures_public_fetch_v1(
    url: str, *, timeout_seconds: float, max_response_bytes: int
) -> Tuple[int, bytes]:
    """One public GET to allowlisted Kraken Futures endpoint. Tests patch this."""
    reasons = validate_probe_url(url)
    if reasons:
        raise ValueError(f"ERR: url blocked: {reasons[0]}")
    bounded_timeout = min(float(timeout_seconds), MAX_TIMEOUT_SECONDS)
    req = request.Request(
        url, method="GET", headers={"User-Agent": "PeakTradeKrakenFuturesPublicProbe/1"}
    )
    try:
        with request.urlopen(req, timeout=bounded_timeout) as resp:
            code = int(getattr(resp, "status", resp.getcode()))
            return code, _read_body_capped(resp, max_response_bytes)
    except error.HTTPError as exc:
        return int(exc.code), _read_body_capped(exc, max_response_bytes)
    except (error.URLError, TimeoutError, OSError, ValueError) as exc:
        raise ValueError(f"fetch failed: {exc}") from exc


def _sanitize_instrument_sample(inst: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "symbol": str(inst.get("symbol") or ""),
        "type": str(inst.get("type") or ""),
        "tradeable": bool(inst.get("tradeable", False)),
        "futures_eligible": is_futures_eligible_instrument(inst),
    }


def parse_instruments_payload(body: Mapping[str, Any]) -> Dict[str, Any]:
    instruments = body.get("instruments")
    if not isinstance(instruments, list):
        raise ValueError("instruments response missing instruments[]")
    total = len(instruments)
    futures_only = 0
    samples: List[Dict[str, Any]] = []
    for inst in instruments:
        if not isinstance(inst, Mapping):
            continue
        if is_futures_eligible_instrument(inst):
            futures_only += 1
            if len(samples) < 5:
                samples.append(_sanitize_instrument_sample(inst))
    return {
        "instruments_count": total,
        "futures_only_count": futures_only,
        "sample_instruments": samples,
    }


def parse_tickers_payload(body: Mapping[str, Any]) -> Dict[str, Any]:
    tickers = body.get("tickers")
    if not isinstance(tickers, list):
        raise ValueError("tickers response missing tickers[]")
    return {"tickers_count": len(tickers)}


def build_top20_candidate_preview(
    instruments: Sequence[Mapping[str, Any]], *, limit: int = 20
) -> List[Dict[str, Any]]:
    """Preview only — not selected, not signal, not truth-go."""
    eligible = [
        inst
        for inst in instruments
        if isinstance(inst, Mapping) and is_futures_eligible_instrument(inst)
    ]
    eligible_sorted = sorted(eligible, key=lambda x: str(x.get("symbol") or ""))
    preview: List[Dict[str, Any]] = []
    for rank, inst in enumerate(eligible_sorted[:limit], start=1):
        preview.append(
            {
                "rank": rank,
                "symbol": str(inst.get("symbol") or ""),
                "preview_only": True,
                "not_selected": True,
                "not_signal": True,
                "not_truth_go": True,
                "not_tradable_authority": True,
            }
        )
    return preview


def build_probe_report(
    *,
    fetched_at: str,
    endpoint_results: Mapping[str, Mapping[str, Any]],
    instruments_raw: Optional[Sequence[Mapping[str, Any]]] = None,
) -> Dict[str, Any]:
    inst_parsed = endpoint_results.get("/derivatives/api/v3/instruments", {})
    tick_parsed = endpoint_results.get("/derivatives/api/v3/tickers", {})
    preview: List[Dict[str, Any]] = []
    if instruments_raw is not None:
        preview = build_top20_candidate_preview(instruments_raw)
    return {
        "schema": "kraken_futures_public_market_data_probe_report_v1",
        "provider": "kraken_futures",
        "provider_id": PROVIDER_ID,
        "source_stage": SOURCE_STAGE,
        "endpoint_provenance": {
            "host": DEFAULT_HOST,
            "rest_base_url": REST_BASE_URL,
            "allowed_public_get_paths": sorted(ALLOWED_PUBLIC_GET_PATHS),
        },
        "fetched_at": fetched_at,
        "auth_used": False,
        "no_orders": True,
        "no_secrets": True,
        "no_live_authorization": True,
        "no_preflight_lift": True,
        "no_truth_go": True,
        "no_selected_tradable_future": True,
        "observability_truth_allowed": False,
        "readmodel_write_executed": False,
        "dashboard_wiring_executed": False,
        "instruments_count": inst_parsed.get("instruments_count", 0),
        "futures_only_count": inst_parsed.get("futures_only_count", 0),
        "sample_instruments": inst_parsed.get("sample_instruments", []),
        "tickers_count": tick_parsed.get("tickers_count", 0),
        "top20_candidate_preview": preview,
        "top20_candidate_preview_note": (
            "preview only, not selected, not signal, not truth-go, not tradable authority"
        ),
        "markers": {
            "VIEW_ONLY": True,
            "MARKET_DATA_ONLY": True,
            "NOT_TRADING": True,
            "NOT_LIVE_AUTHORIZATION": True,
            "NOT_TRUTH_GO": True,
            "NOT_SELECTED_TRADABLE_FUTURE": True,
        },
    }


def run_probe(
    *,
    confirm: str,
    timeout_seconds: float,
    max_response_bytes: int,
    fetched_at: Optional[str] = None,
    fetcher: PublicGetFetcher = kraken_futures_public_fetch_v1,
    output_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    if confirm != CONFIRM_TOKEN:
        _die("ERR: confirm token required for network probe")
    if timeout_seconds <= 0 or timeout_seconds > MAX_TIMEOUT_SECONDS:
        _die(f"ERR: timeout_seconds must be in (0, {MAX_TIMEOUT_SECONDS}]")
    if max_response_bytes <= 0 or max_response_bytes > MAX_RESPONSE_BYTES_DEFAULT:
        _die("ERR: max_response_bytes out of allowed bounds")

    at = fetched_at or _utc_now_z()
    endpoint_results: Dict[str, Mapping[str, Any]] = {}
    instruments_raw: Optional[List[Mapping[str, Any]]] = None

    for ep in PUBLIC_ENDPOINT_ORDER:
        suffix = ep.split("/derivatives/api/v3", 1)[-1]
        url = f"{REST_BASE_URL.rstrip('/')}{suffix}"
        block = validate_probe_url(url)
        if block:
            _die(f"ERR: {block[0]}")
        status, raw = fetcher(url, timeout_seconds, max_response_bytes)
        if status < 200 or status >= 300:
            _die(f"ERR: HTTP {status} from {ep}")
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            _die(f"ERR: invalid JSON from {ep}: {exc}")
        if not isinstance(payload, Mapping):
            _die(f"ERR: expected JSON object from {ep}")
        if ep.endswith("/instruments"):
            parsed = parse_instruments_payload(payload)
            raw_list = payload.get("instruments")
            if isinstance(raw_list, list):
                instruments_raw = [x for x in raw_list if isinstance(x, Mapping)]
            endpoint_results[ep] = parsed
        else:
            endpoint_results[ep] = parse_tickers_payload(payload)

    report = build_probe_report(
        fetched_at=at,
        endpoint_results=endpoint_results,
        instruments_raw=instruments_raw,
    )

    out_json = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if output_dir is not None:
        output_dir.mkdir(parents=True, exist_ok=True)
        out_path = output_dir / "kraken_futures_public_market_data_probe_report.v1.json"
        out_path.write_text(out_json, encoding="utf-8")
    else:
        print(out_json, end="")

    _emit_machine_lines(report)
    return report


def _emit_machine_lines(report: Mapping[str, Any]) -> None:
    markers = report.get("markers") or {}
    lines = [
        "VIEW_ONLY=true",
        "MARKET_DATA_ONLY=true",
        "NOT_TRADING=true",
        "NOT_LIVE_AUTHORIZATION=true",
        "NOT_TRUTH_GO=true",
        "NOT_SELECTED_TRADABLE_FUTURE=true",
        f"PROVIDER_ID={PROVIDER_ID}",
        f"SOURCE_STAGE={SOURCE_STAGE}",
        f"AUTH_USED=false",
        f"INSTRUMENTS_COUNT={report.get('instruments_count', 0)}",
        f"FUTURES_ONLY_COUNT={report.get('futures_only_count', 0)}",
        f"TICKERS_COUNT={report.get('tickers_count', 0)}",
        "READMODEL_WRITE_EXECUTED=false",
        "DASHBOARD_WIRING_EXECUTED=false",
        "PROBE_EXECUTED=true",
    ]
    for key, val in sorted(markers.items()):
        lines.append(f"{key}={str(val).lower()}")
    for line in lines:
        print(line)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="U5B Kraken Futures public market-data-only one-shot probe (no auth)."
    )
    parser.add_argument(
        "--confirm-view-only-public-market-data-probe",
        required=True,
        choices=[CONFIRM_TOKEN],
        help=f"Must be {CONFIRM_TOKEN!r}.",
    )
    parser.add_argument("--timeout-seconds", type=float, default=10.0)
    parser.add_argument("--max-response-bytes", type=int, default=262144)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Optional durable output directory; default prints JSON to stdout.",
    )
    parser.add_argument(
        "--fetched-at-utc",
        default=None,
        help="Override timestamp for tests/operators (ISO-8601 UTC).",
    )
    ns = parser.parse_args(argv)
    try:
        run_probe(
            confirm=ns.confirm_view_only_public_market_data_probe,
            timeout_seconds=ns.timeout_seconds,
            max_response_bytes=ns.max_response_bytes,
            fetched_at=ns.fetched_at_utc,
            output_dir=ns.output_dir,
        )
    except SystemExit as exc:
        code = int(exc.code) if isinstance(exc.code, int) else 2
        return code
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
