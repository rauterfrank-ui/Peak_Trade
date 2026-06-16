#!/usr/bin/env python3
"""No-network bridge: public REST capture package → supervised-observer-compatible package."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Tuple

CONFIRM_TOKEN = "NO_NETWORK_NO_BROKER_NO_EXCHANGE_NO_ORDERS"

CAPTURE_MANIFEST_SCHEMA_EXPECTED = "public_rest_market_capture_package_manifest_v0"
CAPTURE_SOURCE_EXPECTED = "public_rest_snapshot_one_shot"
PROVIDER_EXPECTED = "binance_spot_market_data_only"
SYMBOL_EXPECTED = "BTCUSDT"
NORMALIZED_REL = Path("normalized/captured_realistic_snapshots.json")
MANIFEST_REL = Path("manifest/capture_manifest.json")

CAPTURED_SCHEMA = "captured_realistic_snapshot_observation_input_v0"
CAPTURED_BRIDGE_SOURCE = "operator_supplied_static"

BRIDGE_MANIFEST_SCHEMA = "public_rest_capture_package_to_supervised_input_bridge_manifest_v0"
BRIDGE_MANIFEST_SOURCE = "public_rest_capture_package_to_supervised_input_bridge_v0"

OBSERVER_MANIFEST_SCHEMA = "supervised_timed_observer_input_manifest_v0"
OBSERVER_MANIFEST_SOURCE = "operator_supplied_static_manifest"

BRIDGE_EXPANSION_METHOD = "deterministic_duplicate_for_supervised_observer_min_count_v0"
CLOSEOUT_NAME = "PUBLIC_REST_TO_SUPERVISED_OBSERVER_BRIDGE_CLOSEOUT.md"

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

_SAFE_BRIDGE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,254}$")


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


def _require_safe_bridge_id(bid: str) -> None:
    if not bid.strip() or bid != bid.strip():
        _die("ERR: bridge-id must be non-empty trimmed")
    if ".." in bid or "/" in bid or "\\" in bid:
        _die("ERR: bridge-id contains unsafe path separators")
    if _SAFE_BRIDGE_ID_RE.match(bid) is None:
        _die("ERR: bridge-id must match ^[A-Za-z0-9][A-Za-z0-9._-]{0,254}$")


def _scan_structure_forbidden(node: Any) -> Optional[str]:
    if isinstance(node, Mapping):
        for key, val in node.items():
            lk = str(key).lower()
            for frag in _FORBIDDEN_SUBSTRINGS:
                if frag == "credential" and lk == "contains_credentials":
                    continue
                if frag in lk:
                    return f"ERR: forbidden substring {frag!r} in JSON key {key!r}"
            nested = _scan_structure_forbidden(val)
            if nested:
                return nested
    elif isinstance(node, list):
        for item in node:
            nested = _scan_structure_forbidden(item)
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


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def _load_json_dict(path: Path) -> Dict[str, Any]:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as e:
        raise ValueError(f"cannot read {path}: {e}") from e
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"invalid JSON in {path}: {e}") from e
    if not isinstance(parsed, dict):
        raise ValueError(f"{path} root must be a JSON object")
    return dict(parsed)


def _validate_upstream_capture_manifest(man: Mapping[str, Any]) -> None:
    if man.get("schema") != CAPTURE_MANIFEST_SCHEMA_EXPECTED:
        raise ValueError("capture_manifest.schema mismatch")
    if man.get("provider") != PROVIDER_EXPECTED:
        raise ValueError("capture_manifest.provider mismatch")
    if man.get("source") != CAPTURE_SOURCE_EXPECTED:
        raise ValueError("capture_manifest.source mismatch")
    if man.get("network_allowed") is not True:
        raise ValueError("capture_manifest.network_allowed must be true")
    if man.get("auth_required") is not False:
        raise ValueError("capture_manifest.auth_required must be false")
    if man.get("symbol") != SYMBOL_EXPECTED:
        raise ValueError("capture_manifest.symbol mismatch")
    if man.get("normalized_file") != "normalized/captured_realistic_snapshots.json":
        raise ValueError("capture_manifest.normalized_file mismatch")
    if man.get("snapshot_count") != 1:
        raise ValueError("capture_manifest.snapshot_count must be 1")
    if man.get("contains_credentials") is not False:
        raise ValueError("capture_manifest.contains_credentials must be false")
    if man.get("contains_orders") is not False:
        raise ValueError("capture_manifest.contains_orders must be false")
    if man.get("contains_fills") is not False:
        raise ValueError("capture_manifest.contains_fills must be false")
    if "normalized_sha256" not in man or not str(man.get("normalized_sha256")):
        raise ValueError("capture_manifest.normalized_sha256 missing")


def _validate_upstream_normalized(
    raw: Dict[str, Any], *, expected_sha: str, norm_path: Path
) -> Tuple[Mapping[str, Any], Mapping[str, str]]:
    scan = _scan_structure_forbidden(raw)
    if scan:
        raise ValueError(scan)

    if raw.get("schema") != CAPTURED_SCHEMA:
        raise ValueError("normalized schema mismatch")
    if raw.get("source") != "redacted_public_snapshot_static":
        raise ValueError("normalized.source mismatch")
    prov = raw.get("provenance")
    if not isinstance(prov, dict):
        raise ValueError("normalized.provenance missing")
    if prov.get("network_fetch_during_test") is not True:
        raise ValueError("normalized provenance.network_fetch_during_test must be true")
    if prov.get("contains_credentials") is not False:
        raise ValueError("normalized provenance.contains_credentials must be false")
    if prov.get("contains_orders") is not False:
        raise ValueError("normalized provenance.contains_orders must be false")
    if prov.get("contains_fills") is not False:
        raise ValueError("normalized provenance.contains_fills must be false")
    if prov.get("source_class") != "public_rest_snapshot_one_shot":
        raise ValueError("normalized provenance.source_class mismatch")
    if prov.get("provider") != PROVIDER_EXPECTED:
        raise ValueError("normalized provenance.provider mismatch")
    shots = raw.get("snapshots")
    if not isinstance(shots, list) or len(shots) != 1:
        raise ValueError("normalized.snapshots must contain exactly one snapshot")

    disc = _sha256_file(norm_path)
    if disc != expected_sha:
        raise ValueError("normalized_sha256 does not match file hash")

    snap0 = shots[0]
    if not isinstance(snap0, dict):
        raise ValueError("snapshot must be object")
    payload = snap0.get("payload")
    if not isinstance(payload, dict):
        raise ValueError("snapshot.payload must be object")
    for k in (
        "bid",
        "ask",
        "last",
        "mid",
        "spread_bps",
        "volume",
        "source_state",
        "sequence",
    ):
        if k not in payload:
            raise ValueError(f"upstream payload missing {k!r}")

    return prov, payload


def _bridge_normalized(
    *,
    upstream_prov: Mapping[str, Any],
    upstream_payload: Mapping[str, str],
    upstream_capture_manifest_sha256: str,
    upstream_normalized_sha256: str,
    symbol: str,
    observed_at_utc: str,
) -> Dict[str, Any]:
    base_bid = str(upstream_payload["bid"]).strip()
    base_ask = str(upstream_payload["ask"]).strip()
    base_last = str(upstream_payload["last"]).strip()
    base_mid = str(upstream_payload["mid"]).strip()
    base_spr = str(upstream_payload["spread_bps"]).strip()
    base_vol = str(upstream_payload["volume"]).strip()

    snaps: List[Dict[str, Any]] = []
    for idx in (1, 2, 3):
        s = str(idx)
        pl: Dict[str, str] = {
            "bid": base_bid,
            "ask": base_ask,
            "last": base_last,
            "mid": base_mid,
            "spread_bps": base_spr,
            "volume": base_vol,
            "source_state": "public_rest_snapshot_one_shot_bridge_static",
            "sequence": s,
            "bridge_expansion_index": s,
            "bridge_source_snapshot_count": "1",
            "bridge_expanded_snapshot_count": "3",
            "bridge_expansion_method": BRIDGE_EXPANSION_METHOD,
        }
        snaps.append(
            {
                "symbol": symbol,
                "observed_at_utc": observed_at_utc,
                "payload": pl,
            }
        )

    prov_out: Dict[str, Any] = {
        "captured_by": "operator",
        "captured_at_utc": upstream_prov.get("captured_at_utc"),
        "redacted": True,
        "network_fetch_during_test": False,
        "contains_credentials": False,
        "contains_orders": False,
        "contains_fills": False,
        "upstream_network_fetch_during_test": True,
        "upstream_source_class": CAPTURE_SOURCE_EXPECTED,
        "upstream_provider": PROVIDER_EXPECTED,
        "bridge_generated": True,
        "bridge_schema": "public_rest_capture_package_to_supervised_input_bridge_v0",
        "bridge_reason": "supervised_observer_min_snapshot_count_compatibility",
        "upstream_normalized_sha256": upstream_normalized_sha256,
        "upstream_capture_manifest_sha256": upstream_capture_manifest_sha256,
    }

    out: Dict[str, Any] = {
        "schema": CAPTURED_SCHEMA,
        "source": CAPTURED_BRIDGE_SOURCE,
        "provenance": prov_out,
        "snapshots": snaps,
    }
    scan = _scan_structure_forbidden(out)
    if scan:
        raise ValueError(scan)
    return out


def run_bridge(
    *,
    capture_package_dir: Path,
    output_dir: Path,
    bridge_id: str,
    confirm: str,
    cadence_seconds: int,
) -> None:
    if confirm != CONFIRM_TOKEN:
        _die(f"ERR: --confirm-no-network must be {CONFIRM_TOKEN!r}")
    _require_safe_bridge_id(bridge_id)

    cap_root = capture_package_dir.resolve()
    if not cap_root.exists():
        _die(f"ERR: capture-package-dir not found: {cap_root}")
    if not cap_root.is_dir():
        _die("ERR: capture-package-dir must be a directory")

    out_base = output_dir.resolve()
    if _glob_pattern_chars(str(out_base)):
        _die("ERR: output-dir must not contain glob metacharacters")
    bridge_root = out_base / bridge_id
    if bridge_root.exists():
        _die(f"ERR: bridge output path already exists: {bridge_root}")

    manifest_src = cap_root / MANIFEST_REL
    norm_src = cap_root / NORMALIZED_REL
    if not manifest_src.is_file():
        _die(f"ERR: missing {MANIFEST_REL}")
    if not norm_src.is_file():
        _die(f"ERR: missing {NORMALIZED_REL}")

    man = _load_json_dict(manifest_src)
    try:
        _validate_upstream_capture_manifest(man)
    except ValueError as e:
        _die(f"ERR: {e}")

    expected_norm_sha = str(man["normalized_sha256"])
    norm_obj = _load_json_dict(norm_src)
    try:
        prov_u, pay_u = _validate_upstream_normalized(
            norm_obj, expected_sha=expected_norm_sha, norm_path=norm_src
        )
    except ValueError as e:
        _die(f"ERR: {e}")

    snap0 = norm_obj["snapshots"][0]
    if not isinstance(snap0, dict):
        _die("ERR: upstream snapshot must be object")
    sym = str(snap0.get("symbol", "")).strip()
    if sym != SYMBOL_EXPECTED:
        _die("ERR: upstream snapshot symbol mismatch")
    obs_at = str(snap0.get("observed_at_utc", "")).strip()
    if not obs_at:
        _die("ERR: upstream snapshot.observed_at_utc empty")
    ot = str(prov_u.get("captured_at_utc", ""))
    if not ot.strip():
        _die("ERR: upstream provenance.captured_at_utc empty")

    out_base.mkdir(parents=True, exist_ok=True)
    bridge_root.mkdir(parents=False)
    src_dir = bridge_root / "source"
    norm_dir = bridge_root / "normalized"
    man_dir = bridge_root / "manifest"
    src_dir.mkdir()
    norm_dir.mkdir()
    man_dir.mkdir()

    shutil.copyfile(manifest_src, src_dir / "capture_manifest.json")
    shutil.copyfile(norm_src, src_dir / "captured_realistic_snapshots.json")

    upstream_cm_sha = _sha256_file(manifest_src)
    upstream_nm_sha = _sha256_file(norm_src)

    bridge_obj = _bridge_normalized(
        upstream_prov=prov_u,
        upstream_payload=pay_u,
        upstream_capture_manifest_sha256=upstream_cm_sha,
        upstream_normalized_sha256=upstream_nm_sha,
        symbol=sym,
        observed_at_utc=obs_at,
    )
    bridge_norm_path = norm_dir / "captured_realistic_snapshots_bridge.json"
    bridge_norm_path.write_bytes(_canonical_json_bytes(bridge_obj))
    bridge_nm_sha = _sha256_file(bridge_norm_path)

    if not _path_is_inside(bridge_norm_path, bridge_root):
        _die("ERR: internal error: bridge normalized path escaped root")

    bridge_manifest: Dict[str, Any] = {
        "schema": BRIDGE_MANIFEST_SCHEMA,
        "source": BRIDGE_MANIFEST_SOURCE,
        "network_allowed": False,
        "upstream_network_fetch_during_test": True,
        "provider": PROVIDER_EXPECTED,
        "symbol": SYMBOL_EXPECTED,
        "upstream_snapshot_count": 1,
        "bridge_snapshot_count": 3,
        "bridge_expansion_method": BRIDGE_EXPANSION_METHOD,
        "upstream_capture_manifest_sha256": upstream_cm_sha,
        "upstream_normalized_sha256": upstream_nm_sha,
        "bridge_normalized_sha256": bridge_nm_sha,
        "supervised_timed_manifest_file": "manifest/supervised_timed_manifest.json",
    }
    raws = man.get("raw_sha256")
    if raws is not None and str(raws).strip():
        bridge_manifest["upstream_raw_sha256"] = str(raws)

    (man_dir / "bridge_manifest.json").write_bytes(_canonical_json_bytes(bridge_manifest))

    abs_bridge_norm = bridge_norm_path.resolve()
    if not abs_bridge_norm.is_file():
        _die("ERR: bridge normalized output missing")
    supervised: Dict[str, Any] = {
        "schema": OBSERVER_MANIFEST_SCHEMA,
        "source": OBSERVER_MANIFEST_SOURCE,
        "cadence_seconds": int(cadence_seconds),
        "max_observations": 3,
        "inputs": [
            {
                "sequence": 1,
                "input_file": str(abs_bridge_norm),
                "expected_schema": CAPTURED_SCHEMA,
            }
        ],
    }
    (man_dir / "supervised_timed_manifest.json").write_bytes(_canonical_json_bytes(supervised))

    co_path = bridge_root / CLOSEOUT_NAME
    co_lines: List[str] = [
        "# PUBLIC REST to Supervised Observer Bridge — Closeout v0",
        "",
        "## Paths",
        "",
        f"- source capture package dir: `{cap_root}`",
        f"- bridge package root: `{bridge_root.resolve()}`",
        f"- source capture manifest: `{manifest_src}`",
        f"- source normalized path: `{norm_src}`",
        f"- bridge normalized path: `{bridge_norm_path}`",
        f"- bridge manifest path: `{man_dir / 'bridge_manifest.json'}`",
        f"- supervised manifest path: `{man_dir / 'supervised_timed_manifest.json'}`",
        "",
        "## Integrity",
        "",
        f"- upstream_capture_manifest_sha256: `{upstream_cm_sha}`",
        f"- upstream_normalized_sha256: `{upstream_nm_sha}`",
        f"- bridge_normalized_sha256: `{bridge_nm_sha}`",
        f"- upstream_snapshot_count: 1",
        f"- bridge_snapshot_count: 3",
        f"- expansion_method: `{BRIDGE_EXPANSION_METHOD}`",
        "",
        "## Network / authority boundaries",
        "",
        "- bridge execution: no network calls",
        "- upstream capture may have used network; bridge step does not repeat network access",
        "- private exchange capture: not allowed",
        "- broker capture: not allowed",
        "- order submission: not allowed",
        "- runtime / scheduler / daemon: not started",
        "- Testnet / Live: not used",
        "",
        "## Machine-readable final lines",
        "",
        "VERDICT=PUBLIC_REST_TO_SUPERVISED_OBSERVER_BRIDGE_V0_CREATED_NOT_APPROVED",
        "DECISION=not_approved",
        "REPO_CHANGED=false",
        "NETWORK_ALLOWED=false",
        "PUBLIC_REST_CAPTURE_EXECUTED=false",
        "PUBLIC_REST_TO_SUPERVISED_OBSERVER_COMPATIBILITY_BRIDGE_CREATED=true",
        "UPSTREAM_NETWORK_FETCH_DURING_TEST=true",
        "BRIDGE_NETWORK_FETCH_DURING_TEST=false",
        "UPSTREAM_SNAPSHOT_COUNT=1",
        "BRIDGE_SNAPSHOT_COUNT=3",
        "PUBLIC_REST_PROVIDER_ID=" + PROVIDER_EXPECTED,
        "PUBLIC_REST_SYMBOL=BTCUSDT",
        "PRIVATE_EXCHANGE_CAPTURE_ALLOWED=false",
        "BROKER_CAPTURE_ALLOWED=false",
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
    co_path.write_text("\n".join(co_lines), encoding="utf-8")

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
            "Build a no-network supervised-observer compatibility bridge package from a "
            "public REST capture package."
        )
    )
    p.add_argument("--capture-package-dir", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--bridge-id", required=True)
    p.add_argument(
        "--confirm-no-network",
        required=True,
        choices=[CONFIRM_TOKEN],
        help=f"Must be {CONFIRM_TOKEN!r}.",
    )
    p.add_argument(
        "--cadence-seconds",
        type=int,
        default=60,
        help="cadence_seconds for supervised manifest (default: 60).",
    )
    ns = p.parse_args(argv)

    try:
        run_bridge(
            capture_package_dir=ns.capture_package_dir,
            output_dir=ns.output_dir,
            bridge_id=str(ns.bridge_id),
            confirm=str(ns.confirm_no_network),
            cadence_seconds=int(ns.cadence_seconds),
        )
    except SystemExit as e:
        code = int(e.code) if isinstance(e.code, int) else 2
        return code
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
