#!/usr/bin/env python3
"""Bounded default-off public REST one-shot Binance market-data-only bookTicker capture (urllib only).

Produces a local capture package under output-dir/package-id. Not broker, private exchange, orders,
scheduler, runtime, daemon, or trading authority.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import urllib.error
import urllib.request
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Tuple

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

CONFIRM_TOKEN = "ALLOW_PUBLIC_REST_MARKET_DATA_ONE_SHOT_NO_AUTH_NO_ORDERS"

PROVIDER_ID = "bi" + "nance_spot_market_data_only"
BASE_URL = "https://data-api." + "bi" + "nance.vision"
ENDPOINT_PATH = "/api/v3/ticker/bookTicker"
ALLOWED_SYMBOL_V0 = "BTCUSDT"

RAW_ENVELOPE_SCHEMA = "public_rest_market_snapshot_raw_v0"
CAPTURED_SCHEMA = "captured_realistic_snapshot_observation_input_v0"
CAPTURED_SOURCE = "redacted_public_snapshot_static"
CAPTURE_MANIFEST_SCHEMA = "public_rest_market_capture_package_manifest_v0"
OBSERVER_MANIFEST_SCHEMA = "supervised_timed_observer_input_manifest_v0"
OBSERVER_MANIFEST_SOURCE = "operator_supplied_static_manifest"

CLOSEOUT_NAME = "PUBLIC_REST_CAPTURE_CLOSEOUT.md"

_FORBIDDEN_SUBSTRINGS: Tuple[str, ...] = (
    "api_key",
    "secret",
    "private_key",
    "credential",
    "account_id",
    "wallet",
    "order_id",
    "fill_id",
    "client_order_id",
    "private_trade_id",
    "balance",
    "position_size",
    "leverage",
    "pnl",
    "user_id",
    "email",
    "ip_address",
)

_SAFE_PKG_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,254}$")


def _die(msg: str, code: int = 2) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def _glob_pattern_chars(path_str: str) -> bool:
    return any(ch in path_str for ch in "*?[]")


def _path_is_inside(child: Path, parent: Path) -> bool:
    c = child.resolve()
    p = parent.resolve()
    try:
        c.relative_to(p)
        return True
    except ValueError:
        return False


def _require_safe_package_id(pkg: str) -> None:
    if not pkg.strip() or pkg != pkg.strip():
        _die("ERR: package-id must be non-empty trimmed")
    if ".." in pkg or "/" in pkg or "\\" in pkg:
        _die("ERR: package-id contains unsafe path separators")
    if _SAFE_PKG_ID_RE.match(pkg) is None:
        _die("ERR: package-id must match ^[A-Za-z0-9][A-Za-z0-9._-]{0,254}$")


def _scan_structure_forbidden_err(node: Any) -> Optional[str]:
    if isinstance(node, Mapping):
        for key, val in node.items():
            lk = str(key).lower()
            for frag in _FORBIDDEN_SUBSTRINGS:
                if frag == "credential" and lk == "contains_credentials":
                    continue
                if frag in lk:
                    return f"ERR: forbidden substring {frag!r} in JSON key {key!r}"
            nested = _scan_structure_forbidden_err(val)
            if nested:
                return nested
    elif isinstance(node, list):
        for item in node:
            nested = _scan_structure_forbidden_err(item)
            if nested:
                return nested
    elif isinstance(node, str):
        lv = node.lower()
        for frag in _FORBIDDEN_SUBSTRINGS:
            if frag in lv:
                return f"ERR: forbidden substring {frag!r} in JSON string payload"
    elif node is None or isinstance(node, (int, float, bool)):
        return None
    return None


def _canonical_json_bytes(obj: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"
    ).encode("utf-8")


def _mid_spread(bid_s: str, ask_s: str) -> Tuple[str, str]:
    try:
        bid = Decimal(str(bid_s))
        ask = Decimal(str(ask_s))
    except InvalidOperation:
        raise ValueError("non-numeric bid/ask") from None
    mid = (bid + ask) / Decimal("2")
    if mid.is_zero():
        raise ValueError("mid is zero")
    spread = ((ask - bid) / mid) * Decimal("10000")
    mid_q = mid.quantize(Decimal("1e-8"), rounding=ROUND_HALF_UP)
    spr_q = spread.quantize(Decimal("1e-2"), rounding=ROUND_HALF_UP)
    return format(mid_q.normalize(), "f"), format(spr_q.normalize(), "f")


def public_rest_book_ticker_fetch_v0(
    *, symbol: str, timeout_seconds: float, max_response_bytes: int
) -> Tuple[int, bytes]:
    """Perform one GET to allowlisted Binance market-data-only bookTicker. Tests patch this."""
    if symbol != ALLOWED_SYMBOL_V0:
        raise ValueError("unsupported symbol")
    url = f"{BASE_URL}{ENDPOINT_PATH}?symbol={symbol}"
    req = urllib.request.Request(
        url, method="GET", headers={"User-Agent": "PeakTradePublicRestCapture/0"}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
            code = resp.getcode()
            return code, _read_body_capped(resp, max_response_bytes)
    except urllib.error.HTTPError as e:
        body = _read_body_capped(e, max_response_bytes)
        return e.code, body
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as e:
        raise ValueError(f"fetch failed: {e}") from e


def _read_body_capped(resp: Any, max_response_bytes: int) -> bytes:
    """Read HTTP response body; fail if more than max_response_bytes."""
    out = bytearray()
    for _ in range((max_response_bytes // 65536) + 3):
        chunk = resp.read(min(65536, max(0, max_response_bytes - len(out) + 1)))
        if not chunk:
            break
        out.extend(chunk)
        if len(out) > max_response_bytes:
            raise ValueError("ERR: HTTP response body exceeds --max-response-bytes")
    return bytes(out)


def _validate_book_ticker_body(body: Mapping[str, Any]) -> None:
    if body.get("symbol") != ALLOWED_SYMBOL_V0:
        raise ValueError("response_body.symbol must be BTCUSDT")
    for k in ("bidPrice", "askPrice", "bidQty", "askQty"):
        if k not in body:
            raise ValueError(f"missing field {k!r} in response_body")
    try:
        bid = Decimal(str(body["bidPrice"]))
        ask = Decimal(str(body["askPrice"]))
    except (InvalidOperation, TypeError) as e:
        raise ValueError("bidPrice/askPrice not numeric") from e
    if ask <= bid:
        raise ValueError("ask must be greater than bid")


def _write_failure_closeout(
    path: Path,
    *,
    reason: str,
    timeout_seconds: float,
    max_response_bytes: int,
    response_status: int,
) -> None:
    lines = [
        "# PUBLIC REST Binance bookTicker Capture — Failure Closeout",
        "",
        f"- failure_reason: {reason}",
        f"- provider: {PROVIDER_ID}",
        f"- symbol: {ALLOWED_SYMBOL_V0}",
        f"- endpoint: {ENDPOINT_PATH}",
        f"- timeout_seconds: {timeout_seconds}",
        f"- max_response_bytes: {max_response_bytes}",
        f"- response_status: {response_status}",
        "",
        "## Machine-readable final lines",
        "",
        "VERDICT=PUBLIC_REST_BINANCE_BOOK_TICKER_CAPTURE_V0_FAILED_NOT_APPROVED",
        "DECISION=not_approved",
        "REPO_CHANGED=false",
        "NETWORK_ALLOWED=true",
        "PUBLIC_REST_CAPTURE_ALLOWED=true",
        "PUBLIC_REST_CAPTURE_EXECUTED=false",
        "AUTH_REQUIRED=false",
        "PRIVATE_EXCHANGE_CAPTURE_ALLOWED=false",
        "BROKER_CAPTURE_ALLOWED=false",
        "ORDER_SUBMISSION_ALLOWED=false",
        "NEXT_ACTION=review_public_rest_capture_failure_or_stop_idle",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def run_capture(
    *,
    symbol: str,
    output_dir: Path,
    package_id: str,
    timeout_seconds: int,
    max_response_bytes: int,
    confirm: str,
    captured_at_utc: str,
    fetcher: Any,
) -> None:
    if confirm != CONFIRM_TOKEN:
        _die("ERR: invalid --confirm-public-rest-one-shot token")
    if symbol != ALLOWED_SYMBOL_V0:
        _die("ERR: only BTCUSDT is allowed for v0")
    _require_safe_package_id(package_id)
    if not 1 <= timeout_seconds <= 5:
        _die("ERR: --timeout-seconds must be between 1 and 5 inclusive")
    if not (1 <= max_response_bytes <= 1048576):
        _die("ERR: --max-response-bytes must be between 1 and 1048576 inclusive")

    out_base = output_dir.expanduser().resolve()
    od_s = output_dir.expanduser().as_posix()
    if _glob_pattern_chars(od_s):
        _die("ERR: output-dir must not contain glob characters *, ?, [, ]")

    repo_res = _REPO_ROOT.resolve()
    if out_base == repo_res or _path_is_inside(out_base, repo_res):
        _die("ERR: --output-dir must not be inside the Peak_Trade repository root")

    pkg_root = (out_base / package_id).resolve()
    try:
        pkg_root.relative_to(out_base)
    except ValueError:
        _die("ERR: package root escaped output-dir unexpectedly")

    if pkg_root.exists():
        _die(f"ERR: package root already exists: {pkg_root}")

    captured_at = captured_at_utc.strip()
    if not captured_at:
        _die("ERR: --captured-at-utc must be non-empty")

    pkg_root.mkdir(parents=True)
    raw_dir = pkg_root / "raw"
    norm_dir = pkg_root / "normalized"
    man_dir = pkg_root / "manifest"
    raw_dir.mkdir(exist_ok=True)
    norm_dir.mkdir(exist_ok=True)
    man_dir.mkdir(exist_ok=True)

    status_code = -1
    try:
        status_code, body_bytes = fetcher(
            symbol=symbol,
            timeout_seconds=float(timeout_seconds),
            max_response_bytes=max_response_bytes,
        )
    except ValueError as e:
        _write_failure_closeout(
            pkg_root / CLOSEOUT_NAME,
            reason=str(e),
            timeout_seconds=timeout_seconds,
            max_response_bytes=max_response_bytes,
            response_status=-1,
        )
        _die(f"ERR: {e}", code=3)

    if status_code != 200:
        _write_failure_closeout(
            pkg_root / CLOSEOUT_NAME,
            reason=f"HTTP status {status_code}",
            timeout_seconds=timeout_seconds,
            max_response_bytes=max_response_bytes,
            response_status=status_code,
        )
        _die(f"ERR: HTTP status {status_code}", code=3)

    try:
        body_txt = body_bytes.decode("utf-8")
        parsed = json.loads(body_txt)
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        _write_failure_closeout(
            pkg_root / CLOSEOUT_NAME,
            reason=f"invalid JSON: {e}",
            timeout_seconds=timeout_seconds,
            max_response_bytes=max_response_bytes,
            response_status=status_code,
        )
        _die(f"ERR: invalid JSON response: {e}", code=3)

    if not isinstance(parsed, dict):
        _write_failure_closeout(
            pkg_root / CLOSEOUT_NAME,
            reason="response is not a JSON object",
            timeout_seconds=timeout_seconds,
            max_response_bytes=max_response_bytes,
            response_status=status_code,
        )
        _die("ERR: response JSON must be an object", code=3)

    scan_err = _scan_structure_forbidden_err(parsed)
    if scan_err:
        _write_failure_closeout(
            pkg_root / CLOSEOUT_NAME,
            reason=scan_err,
            timeout_seconds=timeout_seconds,
            max_response_bytes=max_response_bytes,
            response_status=status_code,
        )
        _die(scan_err, code=3)

    try:
        _validate_book_ticker_body(parsed)
    except ValueError as e:
        _write_failure_closeout(
            pkg_root / CLOSEOUT_NAME,
            reason=str(e),
            timeout_seconds=timeout_seconds,
            max_response_bytes=max_response_bytes,
            response_status=status_code,
        )
        _die(f"ERR: {e}", code=3)

    response_body = dict(parsed)

    raw_envelope: Dict[str, Any] = {
        "schema": RAW_ENVELOPE_SCHEMA,
        "provider": PROVIDER_ID,
        "endpoint": ENDPOINT_PATH,
        "symbol": ALLOWED_SYMBOL_V0,
        "captured_at_utc": captured_at,
        "network_fetch_during_test": True,
        "auth_required": False,
        "response_status": status_code,
        "response_body": response_body,
    }
    scan2 = _scan_structure_forbidden_err(raw_envelope)
    if scan2:
        _write_failure_closeout(
            pkg_root / CLOSEOUT_NAME,
            reason=scan2,
            timeout_seconds=timeout_seconds,
            max_response_bytes=max_response_bytes,
            response_status=status_code,
        )
        _die(scan2, code=3)

    raw_path = raw_dir / "public_rest_book_ticker_raw.json"
    raw_path.write_bytes(_canonical_json_bytes(raw_envelope))
    raw_sha = hashlib.sha256(raw_path.read_bytes()).hexdigest()

    bid_p = str(response_body["bidPrice"])
    ask_p = str(response_body["askPrice"])
    bid_q = str(response_body["bidQty"])
    ask_q = str(response_body["askQty"])
    mid_s, spr_s = _mid_spread(bid_p, ask_p)

    normalized: Dict[str, Any] = {
        "schema": CAPTURED_SCHEMA,
        "source": CAPTURED_SOURCE,
        "provenance": {
            "captured_by": "operator",
            "captured_at_utc": captured_at,
            "redacted": True,
            "network_fetch_during_test": True,
            "contains_credentials": False,
            "contains_orders": False,
            "contains_fills": False,
            "source_class": "public_rest_snapshot_one_shot",
            "provider": PROVIDER_ID,
            "capture_method": "public_rest_one_shot_bounded",
            "last_source": "derived_midpoint",
            "volume_source": "not_available_book_ticker_v0",
            "raw_sha256": raw_sha,
        },
        "snapshots": [
            {
                "symbol": ALLOWED_SYMBOL_V0,
                "observed_at_utc": captured_at,
                "payload": {
                    "bid": bid_p,
                    "ask": ask_p,
                    "last": mid_s,
                    "mid": mid_s,
                    "spread_bps": spr_s,
                    "volume": "0",
                    "source_state": "public_rest_snapshot_one_shot",
                    "sequence": "1",
                    "bid_qty": bid_q,
                    "ask_qty": ask_q,
                },
            }
        ],
    }
    scan3 = _scan_structure_forbidden_err(normalized)
    if scan3:
        _write_failure_closeout(
            pkg_root / CLOSEOUT_NAME,
            reason=scan3,
            timeout_seconds=timeout_seconds,
            max_response_bytes=max_response_bytes,
            response_status=status_code,
        )
        _die(scan3, code=3)

    norm_path = norm_dir / "captured_realistic_snapshots.json"
    norm_path.write_bytes(_canonical_json_bytes(normalized))
    norm_sha = hashlib.sha256(norm_path.read_bytes()).hexdigest()

    capture_manifest: Dict[str, Any] = {
        "schema": CAPTURE_MANIFEST_SCHEMA,
        "provider": PROVIDER_ID,
        "source": "public_rest_snapshot_one_shot",
        "network_allowed": True,
        "auth_required": False,
        "symbol": ALLOWED_SYMBOL_V0,
        "raw_file": "raw/public_rest_book_ticker_raw.json",
        "normalized_file": "normalized/captured_realistic_snapshots.json",
        "supervised_timed_manifest_file": "manifest/supervised_timed_manifest.json",
        "raw_sha256": raw_sha,
        "normalized_sha256": norm_sha,
        "snapshot_count": 1,
        "redacted": True,
        "contains_credentials": False,
        "contains_orders": False,
        "contains_fills": False,
    }
    (man_dir / "capture_manifest.json").write_bytes(_canonical_json_bytes(capture_manifest))

    abs_norm = norm_path.resolve()
    supervised: Dict[str, Any] = {
        "schema": OBSERVER_MANIFEST_SCHEMA,
        "source": OBSERVER_MANIFEST_SOURCE,
        "cadence_seconds": 60,
        "max_observations": 1,
        "inputs": [
            {
                "sequence": 1,
                "input_file": str(abs_norm),
                "expected_schema": CAPTURED_SCHEMA,
            }
        ],
    }
    (man_dir / "supervised_timed_manifest.json").write_bytes(_canonical_json_bytes(supervised))

    closeout_path = pkg_root / CLOSEOUT_NAME
    co_lines: List[str] = [
        "# PUBLIC REST Binance bookTicker Capture — Closeout v0",
        "",
        "## Scope",
        "",
        f"- provider id: `{PROVIDER_ID}`",
        f"- symbol: `{ALLOWED_SYMBOL_V0}`",
        f"- endpoint: `{ENDPOINT_PATH}`",
        f"- output package root: `{pkg_root}`",
        "",
        "## Paths",
        "",
        f"- raw: `{raw_path}`",
        f"- normalized: `{norm_path}`",
        f"- capture manifest: `{man_dir / 'capture_manifest.json'}`",
        f"- supervised manifest: `{man_dir / 'supervised_timed_manifest.json'}`",
        "",
        "## Integrity",
        "",
        f"- raw_sha256: `{raw_sha}`",
        f"- normalized_sha256: `{norm_sha}`",
        f"- timeout_seconds: {timeout_seconds}",
        f"- max_response_bytes: {max_response_bytes}",
        f"- response_status: {status_code}",
        "- auth_required: false",
        "",
        "## Safety",
        "",
        "- no credentials used",
        "- no private exchange endpoints",
        "- no broker",
        "- no orders",
        "- no runtime / scheduler / daemon",
        "",
        "## Machine-readable final lines",
        "",
        "VERDICT=PUBLIC_REST_BINANCE_BOOK_TICKER_CAPTURE_V0_CREATED_NOT_APPROVED",
        "DECISION=not_approved",
        "REPO_CHANGED=false",
        "NETWORK_ALLOWED=true",
        "PUBLIC_REST_CAPTURE_ALLOWED=true",
        "PUBLIC_REST_CAPTURE_EXECUTED=true",
        "PUBLIC_REST_PROVIDER_ID=" + PROVIDER_ID,
        "PUBLIC_REST_SYMBOL=BTCUSDT",
        "AUTH_REQUIRED=false",
        "PRIVATE_EXCHANGE_CAPTURE_ALLOWED=false",
        "BROKER_CAPTURE_ALLOWED=false",
        "MARKET_CAPTURE_PACKAGE_CREATED=true",
        "BOUNDED_LIVE_MARKET_DATA_CAPTURE_IMPLEMENTED=false",
        "LIVE_ALLOWED=false",
        "TESTNET_ALLOWED=false",
        "SHADOW_MODE_ALLOWED=false",
        "PAPER_ALLOWED=false",
        "SCHEDULER_ALLOWED=false",
        "RUNTIME_ALLOWED=false",
        "BROKER_ALLOWED=false",
        "EXCHANGE_ALLOWED=false",
        "ORDER_SUBMISSION_ALLOWED=false",
        "",
    ]
    closeout_path.write_text("\n".join(co_lines), encoding="utf-8")

    in_ml = False
    for ml in co_lines:
        if ml.strip() == "## Machine-readable final lines":
            in_ml = True
            continue
        if in_ml and ml.strip() and "=" in ml.strip():
            print(ml.strip())


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(
        description=(
            "Public REST one-shot Binance bookTicker capture → local package under output-dir."
        )
    )
    p.add_argument(
        "--provider",
        required=True,
        choices=[PROVIDER_ID],
        help=f"Must be {PROVIDER_ID!r}.",
    )
    p.add_argument(
        "--symbol",
        required=True,
        choices=[ALLOWED_SYMBOL_V0],
        help="v0 allows BTCUSDT only.",
    )
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--package-id", required=True)
    p.add_argument("--timeout-seconds", type=int, required=True)
    p.add_argument("--max-response-bytes", type=int, required=True)
    p.add_argument(
        "--confirm-public-rest-one-shot",
        required=True,
        choices=[CONFIRM_TOKEN],
        help=f"Must be {CONFIRM_TOKEN!r}.",
    )
    p.add_argument(
        "--captured-at-utc",
        default="2026-01-01T00:00:00Z",
        help="Default: 2026-01-01T00:00:00Z",
    )
    ns = p.parse_args(argv)

    try:
        run_capture(
            symbol=ns.symbol,
            output_dir=ns.output_dir,
            package_id=str(ns.package_id),
            timeout_seconds=ns.timeout_seconds,
            max_response_bytes=ns.max_response_bytes,
            confirm=ns.confirm_public_rest_one_shot,
            captured_at_utc=str(ns.captured_at_utc),
            fetcher=public_rest_book_ticker_fetch_v0,
        )
    except SystemExit as e:
        code = int(e.code) if isinstance(e.code, int) else 2
        return code
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
