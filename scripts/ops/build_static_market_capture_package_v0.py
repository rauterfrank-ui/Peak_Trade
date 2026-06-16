#!/usr/bin/env python3
"""Gate-A static market capture package builder: operator raw JSON → /tmp-local package layout (no network).

Not live capture, REST, long-lived streaming transports, scheduler, daemon, broker, exchange, orders,
or Shadow Mode.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Tuple

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

CONFIRM_TOKEN = "NO_NETWORK_NO_BROKER_NO_EXCHANGE_NO_ORDERS"

RAW_SCHEMA = "operator_supplied_static_market_snapshot_raw_v0"
RAW_SOURCE = "operator_supplied_export_static"

CAPTURED_SCHEMA = "captured_realistic_snapshot_observation_input_v0"
CAPTURED_ENVELOPE_SOURCE = "operator_supplied_static"

PKG_MANIFEST_SCHEMA = "market_capture_package_manifest_v0"
PKG_MANIFEST_SOURCE = "operator_supplied_static_capture_package"

OBSERVER_MANIFEST_SCHEMA = "supervised_timed_observer_input_manifest_v0"
OBSERVER_MANIFEST_SOURCE = "operator_supplied_static_manifest"

CLOSEOUT_BASENAME = "CAPTURE_PACKAGE_CLOSEOUT.md"

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

_PAYLOAD_KEY_REJECT: Tuple[str, ...] = (
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
)

_SAFE_PKG_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,254}$")


def _die(msg: str, code: int = 2) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def _glob_pattern_chars(path_str: str) -> bool:
    return any(ch in path_str for ch in "*?[]")


def _path_is_inside(child: Path, parent: Path) -> bool:
    """True if resolved child equals parent or sits under parent."""
    c = child.resolve()
    p = parent.resolve()
    try:
        c.relative_to(p)
        return True
    except ValueError:
        return False


def _scan_structure_forbidden(node: Any) -> None:
    if isinstance(node, Mapping):
        for key, val in node.items():
            lk = str(key).lower()
            for frag in _FORBIDDEN_SUBSTRINGS:
                if frag in lk:
                    _die(f"ERR: forbidden substring {frag!r} in JSON key {key!r}")
            _scan_structure_forbidden(val)
    elif isinstance(node, list):
        for item in node:
            _scan_structure_forbidden(item)
    elif isinstance(node, str):
        lv = node.lower()
        for frag in _FORBIDDEN_SUBSTRINGS:
            if frag in lv:
                _die(f"ERR: forbidden substring {frag!r} in JSON string payload")
    elif node is None or isinstance(node, (int, float, bool)):
        return


def _require_safe_package_id(pkg: str) -> None:
    if not pkg.strip() or pkg != pkg.strip():
        _die("ERR: package-id must be non-empty trimmed")
    if ".." in pkg or "/" in pkg or "\\" in pkg:
        _die("ERR: package-id contains unsafe path separators")
    if _SAFE_PKG_ID_RE.match(pkg) is None:
        _die("ERR: package-id must match ^[A-Za-z0-9][A-Za-z0-9._-]{0,254}$ (no slashes or '..')")


def _canonical_json_bytes(obj: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"
    ).encode("utf-8")


def _dec_str_mid_spread(bid_s: str, ask_s: str) -> Tuple[str, str]:
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


def _reject_payload_keys(payload: Mapping[str, str]) -> None:
    for key in payload:
        lk = key.lower()
        for frag in _PAYLOAD_KEY_REJECT:
            if frag in lk:
                _die(f"ERR: forbidden normalized payload key pattern {frag!r} in {key!r}")


def _normalized_snapshot(
    seq: int, raw_snap: Mapping[str, Any], symbol_override: str
) -> Dict[str, Any]:
    try:
        sym = raw_snap["symbol"]
        ot = raw_snap["observed_at_utc"]
        bid = raw_snap["bid"]
        ask = raw_snap["ask"]
        lst = raw_snap["last"]
        vol = raw_snap["volume"]
    except KeyError as e:
        raise ValueError(f"raw snapshot missing field {e.args[0]}") from None
    if (
        not str(sym).strip()
        or not str(ot).strip()
        or bid is None
        or ask is None
        or lst is None
        or vol is None
    ):
        raise ValueError("raw snapshot missing required trimmed fields")

    sym_out = symbol_override.strip()
    if not sym_out:
        raise ValueError("symbol override empty")

    mid_opt = raw_snap.get("mid")
    spr_opt = raw_snap.get("spread_bps")

    bid_s = str(bid).strip()
    ask_s = str(ask).strip()
    lst_s = str(lst).strip()

    mid_s = str(mid_opt).strip() if mid_opt is not None and str(mid_opt).strip() else None
    spr_s = str(spr_opt).strip() if spr_opt is not None and str(spr_opt).strip() else None
    if mid_s is None or spr_s is None:
        computed_mid, computed_spr = _dec_str_mid_spread(bid_s, ask_s)
        mid_s = mid_s or computed_mid
        spr_s = spr_s or computed_spr

    payload: Dict[str, str] = {
        "bid": bid_s,
        "ask": ask_s,
        "last": lst_s,
        "mid": mid_s,
        "spread_bps": spr_s,
        "volume": str(vol).strip(),
        "source_state": "operator_supplied_static",
        "sequence": str(seq),
    }
    optional_keys = ("latency_ms", "book_depth_hint", "volatility_hint")
    for ok in optional_keys:
        if ok in raw_snap and raw_snap[ok] is not None:
            payload[ok] = str(raw_snap[ok])

    _reject_payload_keys(payload)

    return {
        "symbol": sym_out,
        "observed_at_utc": str(ot),
        "payload": payload,
    }


def _validate_raw_contract(raw_obj: Mapping[str, Any]) -> List[Mapping[str, Any]]:
    if raw_obj.get("schema") != RAW_SCHEMA:
        _die(f"ERR: raw schema must be {RAW_SCHEMA!r}")
    if raw_obj.get("source") != RAW_SOURCE:
        _die(f"ERR: raw source must be {RAW_SOURCE!r}")
    snaps_raw = raw_obj.get("snapshots")
    if not isinstance(snaps_raw, list):
        _die("ERR: snapshots must be a JSON array")
    if len(snaps_raw) != 3:
        _die(f"ERR: raw snapshot count must be exactly 3 for v0, got {len(snaps_raw)}")
    out_snaps: List[Mapping[str, Any]] = []
    for item in snaps_raw:
        if not isinstance(item, Mapping):
            _die("ERR: each raw snapshot must be an object")
        out_snaps.append(item)
    return out_snaps


def _write_closeout(
    *,
    path: Path,
    package_root: Path,
    raw_sha256: str,
    norm_sha256: str,
    supervised_cmd_hint: str,
) -> None:
    lines = [
        "# Capture Package Closeout — Static Gate A v0",
        "",
        "## Paths",
        "",
        f"- package root: `{package_root}`",
        f"- raw: `{package_root}/raw/operator_market_snapshot_raw.json`",
        (f"- normalized: `{package_root}/normalized/captured_realistic_snapshots.json`"),
        f"- capture manifest: `{package_root}/manifest/capture_manifest.json`",
        f"- supervised timed manifest: `{package_root}/manifest/supervised_timed_manifest.json`",
        "",
        "## Integrity",
        "",
        f"- raw_sha256: `{raw_sha256}`",
        f"- normalized_sha256: `{norm_sha256}`",
        "- snapshot count: 3",
        "- forbidden key substring scan status: PASSED",
        "",
        "## Provenance guardrails",
        "",
        "- redacted: true",
        "- contains_credentials: false",
        "- contains_orders: false",
        "- contains_fills: false",
        "- network_allowed: false (builder)",
        "",
        "## Operational boundaries",
        "",
        "- runtime: forbidden",
        "- scheduler: forbidden",
        "- daemon: forbidden",
        "- broker/exchange/order paths: forbidden",
        "- Shadow Mode/Testnet/Live: not authorized by this artifact",
        "",
        "## Next suggested command (manual only)",
        "",
        supervised_cmd_hint,
        "",
        "## Machine-readable final lines",
        "",
        "VERDICT=MARKET_CAPTURE_PACKAGE_V0_CREATED_NOT_APPROVED",
        "DECISION=not_approved",
        "REPO_CHANGED=false",
        "NETWORK_ALLOWED=false",
        "PUBLIC_REST_CAPTURE_ALLOWED=false",
        "PRIVATE_EXCHANGE_CAPTURE_ALLOWED=false",
        "BROKER_CAPTURE_ALLOWED=false",
        "MARKET_CAPTURE_PACKAGE_CREATED=true",
        "MARKET_CAPTURE_PACKAGE_CONTRACT_DESIGNED=true",
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
    path.write_text("\n".join(lines), encoding="utf-8")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Build a Gate-A operator-static market capture package under output-dir/package-id "
            "(no network, no REST, purely local)."
        ),
    )
    parser.add_argument("--raw-input-file", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--package-id", required=True)
    parser.add_argument(
        "--confirm-no-network",
        required=True,
        choices=[CONFIRM_TOKEN],
        help=f"Must equal {CONFIRM_TOKEN!r}",
    )
    parser.add_argument(
        "--symbol",
        default="STATIC-MARKET-CAPTURE",
        help="Symbol written into normalized captured-realistic envelopes (default: STATIC-MARKET-CAPTURE).",
    )
    parser.add_argument(
        "--captured-at-utc",
        default="2026-01-01T00:00:00Z",
        help="Captured-at timestamp inserted into normalized provenance (default: 2026-01-01T00:00:00Z).",
    )
    parser.add_argument(
        "--cadence-seconds",
        type=int,
        default=60,
        help="Cadence_seconds for supervised timed bridge manifest metadata (default: 60).",
    )

    ns = parser.parse_args(argv)

    pkg_id = str(ns.package_id)
    _require_safe_package_id(pkg_id)

    captured_at = str(ns.captured_at_utc).strip()
    if not captured_at:
        _die("ERR: --captured-at-utc empty")
    sym_override = str(ns.symbol)

    cad = ns.cadence_seconds
    if not isinstance(cad, int) or cad < 0:
        _die("ERR: --cadence-seconds must be int >= 0")

    raw_path = ns.raw_input_file.expanduser()
    rp_s = raw_path.as_posix()
    if _glob_pattern_chars(rp_s):
        _die("ERR: raw path must not contain glob characters *, ?, [, ]")

    raw_path_res = raw_path.resolve()
    if raw_path_res.is_dir():
        _die("ERR: raw-input-file must not be a directory")
    if not raw_path_res.is_file():
        _die(f"ERR: raw-input-file not found at {raw_path_res}")

    out_base = ns.output_dir.expanduser().resolve()

    repo_res = _REPO_ROOT.resolve()
    if out_base == repo_res or _path_is_inside(out_base, repo_res):
        _die(
            "ERR: --output-dir must not be inside Peak_Trade repository root (no writes to repo subtree)"
        )

    pkg_root = (out_base / pkg_id).resolve()
    try:
        pkg_root.relative_to(out_base.resolve())
    except ValueError:
        _die("ERR: package root escaped output-dir unexpectedly")

    if pkg_root.exists():
        _die(f"ERR: package root already exists: {pkg_root}")

    raw_bytes = raw_path_res.read_bytes()
    raw_sha = hashlib.sha256(raw_bytes).hexdigest()

    try:
        raw_obj = json.loads(raw_bytes.decode("utf-8"))
    except json.JSONDecodeError as e:
        _die(f"ERR: invalid JSON raw input {e}")

    if not isinstance(raw_obj, dict):
        _die("ERR: raw input must be a JSON object")

    _scan_structure_forbidden(raw_obj)
    raw_snaps = _validate_raw_contract(raw_obj)

    try:
        norm_snaps_list = []
        for i, rs in enumerate(raw_snaps, start=1):
            norm_snaps_list.append(_normalized_snapshot(i, rs, sym_override))

        normalized_body: Dict[str, Any] = {
            "schema": CAPTURED_SCHEMA,
            "source": CAPTURED_ENVELOPE_SOURCE,
            "provenance": {
                "captured_by": "operator",
                "captured_at_utc": captured_at,
                "redacted": True,
                "network_fetch_during_test": False,
                "contains_credentials": False,
                "contains_orders": False,
                "contains_fills": False,
                "source_class": RAW_SOURCE,
                "capture_method": "gate_a_no_network_static_package",
                "raw_sha256": raw_sha,
            },
            "snapshots": norm_snaps_list,
        }

        canonical_norm_bytes = _canonical_json_bytes(normalized_body)
        norm_sha = hashlib.sha256(canonical_norm_bytes).hexdigest()

        raw_rel = Path("raw/operator_market_snapshot_raw.json").as_posix()
        normalized_rel = Path("normalized/captured_realistic_snapshots.json").as_posix()
        supervised_rel = Path("manifest/supervised_timed_manifest.json").as_posix()

        capture_manifest: Dict[str, Any] = {
            "schema": PKG_MANIFEST_SCHEMA,
            "source": PKG_MANIFEST_SOURCE,
            "network_allowed": False,
            "raw_file": raw_rel,
            "normalized_file": normalized_rel,
            "supervised_timed_manifest_file": supervised_rel,
            "raw_sha256": raw_sha,
            "normalized_sha256": norm_sha,
            "snapshot_count": 3,
            "redacted": True,
            "contains_credentials": False,
            "contains_orders": False,
            "contains_fills": False,
        }
        canon_capture = _canonical_json_bytes(capture_manifest)

        supervised_abs_normalized = pkg_root.joinpath(normalized_rel).resolve()
        observer_manifest = {
            "schema": OBSERVER_MANIFEST_SCHEMA,
            "source": OBSERVER_MANIFEST_SOURCE,
            "cadence_seconds": cad,
            "max_observations": 3,
            "inputs": [
                {
                    "sequence": 1,
                    "input_file": str(supervised_abs_normalized),
                    "expected_schema": CAPTURED_SCHEMA,
                }
            ],
        }
        canon_supervised = _canonical_json_bytes(observer_manifest)

        raw_dir = pkg_root / "raw"
        norm_dir = pkg_root / "normalized"
        m_dir = pkg_root / "manifest"
        for d in (raw_dir, norm_dir, m_dir):
            d.mkdir(parents=True, exist_ok=False)

        raw_written = raw_dir / "operator_market_snapshot_raw.json"
        shutil.copyfile(raw_path_res, raw_written)
        raw_written.resolve().relative_to(pkg_root.resolve())

        (norm_dir / "captured_realistic_snapshots.json").write_bytes(canonical_norm_bytes)
        capture_path = m_dir / "capture_manifest.json"
        capture_path.write_bytes(canon_capture)
        supervised_path = m_dir / "supervised_timed_manifest.json"
        supervised_path.write_bytes(canon_supervised)

        supervised_cmd = (
            f"python3 scripts/ops/run_shadow_observation_supervised_timed_v0.py \\\n"
            f'  --input-manifest "{supervised_path}" \\\n'
            f'  --output-dir "<explicit /tmp observation evidence dir>" \\\n'
            '  --run-id "<explicit safe run id>" \\\n'
            "  --confirm-no-runtime NO_RUNTIME_NO_SCHEDULER_NO_BROKER_NO_ORDERS"
        )

        _write_closeout(
            path=pkg_root / CLOSEOUT_BASENAME,
            package_root=pkg_root,
            raw_sha256=raw_sha,
            norm_sha256=norm_sha,
            supervised_cmd_hint=supervised_cmd,
        )

        for mf in capture_path, supervised_path, raw_written:
            mf.resolve().relative_to(pkg_root)

    except (OSError, ValueError) as e:
        shutil.rmtree(pkg_root, ignore_errors=True)
        _die(f"ERR: capture package build failure: {e}")

    mr = (
        "VERDICT=MARKET_CAPTURE_PACKAGE_V0_CREATED_NOT_APPROVED",
        "DECISION=not_approved",
        "REPO_CHANGED=false",
        "NETWORK_ALLOWED=false",
        "PUBLIC_REST_CAPTURE_ALLOWED=false",
        "PRIVATE_EXCHANGE_CAPTURE_ALLOWED=false",
        "BROKER_CAPTURE_ALLOWED=false",
        "MARKET_CAPTURE_PACKAGE_CREATED=true",
        "MARKET_CAPTURE_PACKAGE_CONTRACT_DESIGNED=true",
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
    )
    for line in mr:
        print(line)
    print(f"CLOSEOUT_WRITTEN={pkg_root.joinpath(CLOSEOUT_BASENAME)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
