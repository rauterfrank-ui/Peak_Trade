#!/usr/bin/env python3
"""OKX → futures_producer_packet_governed.v1 offline public producer.

Public REST only. No private API, orders, runtime, or Truth-GO.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

_REPO_ROOT = Path(__file__).resolve().parents[2]
for _p in (_REPO_ROOT, _REPO_ROOT / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from scripts.ops.primary_evidence_retention_v0 import finalize_durable_bundle_manifest
from scripts.ops.u2c_packet_shape_v1 import flat_row_to_nested_packet
from src.ops.okx_captured_at_freshness_policy_v1 import (
    classify_freshness_v1,
    load_freshness_policy_v1,
    utc_now_iso,
)
from src.ops.okx_min_notional_mapping_v1 import (
    FORMULA_ID,
    MAPPING_RATIFICATION_ID,
    MIN_NOTIONAL_KIND,
    load_mapping_ratification_v1,
    map_okx_linear_swap_min_notional_v1,
)
from src.ops.okx_public_market_data_client_v1 import (
    OkxPublicMarketDataClientV1,
    OkxPublicCaptureEnvelopeV1,
)

PRODUCER_ID = "okx_to_futures_producer_packet_governed_v1"
GOVERNED_SCHEMA_NAME = "futures_producer_packet_governed.v1"
GOVERNED_SOURCE_KIND = "governed_metadata_snapshot"
VENUE = "okx"
SOURCE_STAGE = "paper"
MARKET_DATA_SOURCE_STAGE = "market_data_view_only"
TOP_N = 20
CONFIRM_TOKEN = "CONFIRM_OKX_TO_FUTURES_PRODUCER_PACKET_GOVERNED_V1"


def _die(msg: str, code: int = 2) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def _git_sha() -> str:
    head = _REPO_ROOT / ".git" / "HEAD"
    try:
        raw = head.read_text(encoding="utf-8").strip()
        if raw.startswith("ref:"):
            ref = raw.split(" ", 1)[1].strip()
            return (_REPO_ROOT / ".git" / ref).read_text(encoding="utf-8").strip()[:40]
        return raw[:40]
    except OSError:
        return "UNKNOWN"


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            try:
                os.unlink(tmp_name)
            except OSError:
                pass


def _payload_data(envelope: OkxPublicCaptureEnvelopeV1) -> list[dict[str, Any]]:
    payload = json.loads(envelope.raw_body_utf8)
    data = payload.get("data")
    if not isinstance(data, list):
        raise ValueError("OKX data must be list")
    return [dict(x) for x in data if isinstance(x, dict)]


def _base_asset(inst: Mapping[str, Any]) -> str:
    uly = str(inst.get("uly") or "")
    if "-" in uly:
        return uly.split("-", 1)[0].upper()
    inst_id = str(inst.get("instId") or "")
    if "-" in inst_id:
        return inst_id.split("-", 1)[0].upper()
    return str(inst.get("baseCcy") or "").upper()


def _is_btc(inst: Mapping[str, Any]) -> bool:
    parts = [
        str(inst.get("instId") or "").upper(),
        str(inst.get("uly") or "").upper(),
        _base_asset(inst),
        str(inst.get("ctValCcy") or "").upper(),
    ]
    for part in parts:
        tokens = part.replace("_", "-").split("-")
        if any(t in {"BTC", "XBT", "WBTC", "TBTC"} for t in tokens if t):
            return True
    return False


def _dec_or_none(value: Any) -> Optional[Decimal]:
    if value is None or value == "":
        return None
    if isinstance(value, float):
        return None
    try:
        parsed = Decimal(str(value))
    except Exception:  # noqa: BLE001
        return None
    return parsed


def build_okx_governed_bundle_v1(
    *,
    archive_root: Path,
    venue: str = VENUE,
    market_type: str = "swap",
    settle_ccy: str = "USDT",
    exclude_underlying: str = "BTC",
    client: OkxPublicMarketDataClientV1 | None = None,
    confirm: str,
) -> dict[str, Any]:
    if confirm != CONFIRM_TOKEN:
        _die("ERR: confirm token required")
    if venue.lower() not in {"okx", "okx_europe_eea"}:
        _die("ERR: venue must be okx")
    if market_type.lower() not in {"swap", "perpetual", "futures"}:
        _die("ERR: market-type must be swap/perpetual/futures")
    if settle_ccy.upper() != "USDT":
        _die("ERR: settle-ccy must be USDT for this ratification")
    if exclude_underlying.upper() != "BTC":
        _die("ERR: exclude-underlying must be BTC for this path")

    load_mapping_ratification_v1(repo_root=_REPO_ROOT)
    freshness_policy = load_freshness_policy_v1(repo_root=_REPO_ROOT)
    archive_root = archive_root.expanduser().resolve()
    archive_root.mkdir(parents=True, exist_ok=True)
    http = client or OkxPublicMarketDataClientV1()

    instruments_env = http.get_json("/api/v5/public/instruments", {"instType": "SWAP"})
    mark_env = http.get_json("/api/v5/public/mark-price", {"instType": "SWAP"})
    tickers_env = http.get_json("/api/v5/market/tickers", {"instType": "SWAP"})

    instruments = _payload_data(instruments_env)
    marks = {str(r.get("instId")): r for r in _payload_data(mark_env) if r.get("instId")}
    tickers = {str(r.get("instId")): r for r in _payload_data(tickers_env) if r.get("instId")}

    as_of = utc_now_iso()
    mark_freshness = classify_freshness_v1(
        reference_at=mark_env.captured_at,
        as_of=as_of,
        source_type="reference_mark_price",
        policy=freshness_policy,
    )
    mark_is_fresh = mark_freshness[0] == "fresh"

    exclusion_counts: dict[str, int] = {}
    eligible_rows: list[dict[str, Any]] = []
    mapping_rows: list[dict[str, Any]] = []

    for inst in instruments:
        inst_id = str(inst.get("instId") or "")
        reasons: list[str] = []
        if str(inst.get("instType") or "").upper() != "SWAP":
            reasons.append("NON_SWAP")
        if str(inst.get("state") or "").lower() != "live":
            reasons.append("NOT_LIVE")
        if str(inst.get("settleCcy") or "").upper() != "USDT":
            reasons.append("NON_USDT_SETTLE")
        if str(inst.get("ctType") or "").lower() != "linear":
            reasons.append("NON_LINEAR_OR_INVERSE")
        if _is_btc(inst):
            reasons.append("BTC_EXCLUDED")
        if not inst_id:
            reasons.append("MISSING_INST_ID")
        mark = marks.get(inst_id)
        if mark is None:
            reasons.append("MISSING_MARK_PRICE")
        if reasons:
            for r in reasons:
                exclusion_counts[r] = exclusion_counts.get(r, 0) + 1
            continue

        assert mark is not None
        mapping = map_okx_linear_swap_min_notional_v1(
            instrument=inst,
            reference_price=mark.get("markPx"),
            reference_price_captured_at=mark_env.captured_at,
            raw_capture_digest=instruments_env.raw_payload_digest,
            reference_price_fresh=mark_is_fresh,
        )
        mapping_rows.append({"instId": inst_id, **mapping.to_json_dict()})
        if not mapping.eligible or mapping.computed_min_notional is None:
            for r in mapping.reason_codes or ("MAPPING_INELIGIBLE",):
                exclusion_counts[r] = exclusion_counts.get(r, 0) + 1
            continue

        tick = tickers.get(inst_id) or {}
        vol24h = _dec_or_none(tick.get("volCcy24h")) or _dec_or_none(tick.get("vol24h"))
        last = _dec_or_none(tick.get("last"))
        mark_px = _dec_or_none(mark.get("markPx"))
        bid = _dec_or_none(tick.get("bidPx"))
        ask = _dec_or_none(tick.get("askPx"))
        funding = _dec_or_none(tick.get("fundingRate"))
        oi = _dec_or_none(tick.get("openInterest") or tick.get("oi"))
        spread = None
        if bid is not None and ask is not None:
            spread = ask - bid

        base = _base_asset(inst)
        min_qty = _dec_or_none(inst.get("minSz"))
        tick_sz = _dec_or_none(inst.get("tickSz"))
        lot_sz = _dec_or_none(inst.get("lotSz"))
        ct_val = _dec_or_none(inst.get("ctVal"))
        lever = _dec_or_none(inst.get("lever"))

        row: dict[str, Any] = {
            "provider": "okx",
            "exchange": "okx",
            "instrument_id": inst_id,
            "symbol": inst_id,
            "provider_instrument_id": inst_id,
            "contract_type": "perpetual",
            "market_type": "perpetual",
            "base_currency": base,
            "quote_currency": "USDT",
            "expiry": None,
            "active": True,
            "provider_tradable_display_only": True,
            "tick_size": float(tick_sz) if tick_sz is not None else None,
            "contract_size": float(ct_val) if ct_val is not None else None,
            "min_qty": float(min_qty) if min_qty is not None else None,
            "min_qty_source": "okx_instruments.minSz",
            "min_notional": float(Decimal(mapping.computed_min_notional)),
            "min_notional_kind": MIN_NOTIONAL_KIND,
            "min_notional_mapping": mapping.to_json_dict(),
            "margin_asset": "USDT",
            "settlement_asset": "USDT",
            "margin_asset_source": "okx_instruments.settleCcy",
            "settlement_asset_source": "okx_instruments.settleCcy",
            "max_leverage": float(lever) if lever is not None else None,
            "leverage_bounds_source": "okx_instruments.lever",
            "lot_size": float(lot_sz) if lot_sz is not None else None,
            "ct_val": mapping.ct_val,
            "ct_val_ccy": mapping.ct_val_ccy,
            "ct_type": mapping.ct_type,
            "last_price": float(last) if last is not None else None,
            "mark_price": float(mark_px) if mark_px is not None else None,
            "index_price": None,
            "display_price": float(mark_px) if mark_px is not None else None,
            "display_price_source": "markPx",
            "vol24h": float(vol24h) if vol24h is not None else None,
            "bid": float(bid) if bid is not None else None,
            "ask": float(ask) if ask is not None else None,
            "spread": float(spread) if spread is not None else None,
            "funding_rate": float(funding) if funding is not None else None,
            "open_interest": float(oi) if oi is not None else None,
            "fetched_at": instruments_env.captured_at,
            "captured_at": instruments_env.captured_at,
            "effective_at": mark_env.effective_at or mark_env.captured_at,
            "missing_fields": [],
            "market_data_missing_fields": [],
            "instrument_missing_fields": [],
            "missing_provider_metadata": [],
            "degraded_fields": [],
            "not_selected": True,
            "not_signal": True,
            "not_truth_go": True,
            "not_tradable_authority": True,
        }
        # Fill market-data missing markers without inventing values.
        md_missing: list[str] = []
        if row["vol24h"] is None:
            md_missing.append("vol24h")
        if row["bid"] is None or row["ask"] is None:
            md_missing.append("bid_ask")
        if row["funding_rate"] is None:
            md_missing.append("funding_rate")
        if row["open_interest"] is None:
            md_missing.append("open_interest")
        if row["last_price"] is None:
            md_missing.append("last_price")
        row["market_data_missing_fields"] = md_missing
        row["missing_fields"] = list(md_missing)
        eligible_rows.append(row)

    if not eligible_rows:
        _die("ERR: no eligible OKX instruments after filters/mapping")

    # Deterministic ranking: vol24h desc, symbol asc; missing vol sorts last.
    def _rank_key(row: Mapping[str, Any]) -> tuple[int, float, str]:
        vol = row.get("vol24h")
        has = 1 if isinstance(vol, (int, float)) and vol > 0 else 0
        vol_sort = float(vol) if has else -1.0
        return (-has, -vol_sort, str(row.get("symbol") or ""))

    ranked = sorted(eligible_rows, key=_rank_key)
    for idx, row in enumerate(ranked, start=1):
        row["rank"] = idx

    top20 = ranked[:TOP_N]
    selected = top20[0]
    bundle_id = (
        f"okx_governed_{datetime.now(tz=timezone.utc).strftime('%Y%m%dT%H%M%SZ')}_"
        f"{instruments_env.raw_payload_digest[:12]}"
    )
    staging = archive_root / "governed_metadata" / f".tmp_{bundle_id}"
    final_dir = archive_root / "governed_metadata" / bundle_id
    if final_dir.exists():
        _die(f"ERR: bundle already exists (idempotent refuse): {final_dir}")
    if staging.exists():
        # Incomplete prior attempt — remove staging only.
        for path in sorted(staging.rglob("*"), reverse=True):
            if path.is_file():
                path.unlink()
            elif path.is_dir():
                path.rmdir()
        staging.rmdir()
    staging.mkdir(parents=True, exist_ok=True)

    raw_instruments_path = staging / "raw_okx_instruments_swap.json"
    raw_mark_path = staging / "raw_okx_mark_price_swap.json"
    raw_tickers_path = staging / "raw_okx_tickers_swap.json"
    _atomic_write_text(raw_instruments_path, instruments_env.raw_body_utf8)
    _atomic_write_text(raw_mark_path, mark_env.raw_body_utf8)
    _atomic_write_text(raw_tickers_path, tickers_env.raw_body_utf8)

    capture_meta = {
        "schema": "okx_public_capture_provenance_v1",
        "producer_id": PRODUCER_ID,
        "git_sha": _git_sha(),
        "instruments": instruments_env.to_json_dict() | {"raw_body_utf8": None},
        "mark_price": mark_env.to_json_dict() | {"raw_body_utf8": None},
        "tickers": tickers_env.to_json_dict() | {"raw_body_utf8": None},
        "instruments_digest": instruments_env.raw_payload_digest,
        "mark_price_digest": mark_env.raw_payload_digest,
        "tickers_digest": tickers_env.raw_payload_digest,
        "mapping_ratification_id": MAPPING_RATIFICATION_ID,
        "formula_id": FORMULA_ID,
        "exclusion_counts": exclusion_counts,
        "eligible_count": len(ranked),
    }
    # Strip huge body from envelope dump already nulled.
    for key in ("instruments", "mark_price", "tickers"):
        capture_meta[key].pop("raw_body_utf8", None)
    _atomic_write_text(
        staging / "capture_provenance_v1.json",
        json.dumps(capture_meta, indent=2) + "\n",
    )
    _atomic_write_text(
        staging / "min_notional_mapping_table_v1.json",
        json.dumps(
            {
                "schema": "okx_min_notional_mapping_table_v1",
                "min_notional_kind": MIN_NOTIONAL_KIND,
                "formula_id": FORMULA_ID,
                "rows": mapping_rows,
            },
            indent=2,
        )
        + "\n",
    )

    nested_packets: list[dict[str, Any]] = []
    for row in ranked:
        nested = flat_row_to_nested_packet(
            row,
            candidate_id=f"c-{row['symbol']}",
            source_universe_size=len(ranked),
            rank=int(row["rank"]),
            selected_top_n=TOP_N,
        )
        # Attach typed mapping provenance without weakening known flags.
        nested["instrument"]["min_notional_provenance"] = row["min_notional_mapping"]
        nested["instrument"]["min_notional_kind"] = MIN_NOTIONAL_KIND
        nested["instrument"]["provider_instrument_id"] = row["provider_instrument_id"]
        nested["candidate"]["provider_instrument_id"] = row["provider_instrument_id"]
        nested_packets.append(nested)

    metadata_table = {
        "schema": "metadata_table_snapshot.v1",
        "schema_version": 1,
        "bundle_id": bundle_id,
        "venue": "okx",
        "row_count": len(ranked),
        "rows": [
            {
                "instrument_id": p["candidate"]["instrument_id"],
                "provider_instrument_id": p["candidate"].get("provider_instrument_id"),
                "symbol": p["candidate"]["symbol"],
                "market_type": p["candidate"]["market_type"],
                "exchange": p["candidate"]["exchange"],
                "base_currency": p["candidate"]["base_currency"],
                "quote_currency": p["candidate"]["quote_currency"],
                "instrument_complete": p["instrument"]["complete"],
                "min_notional_known": p["instrument"]["min_notional_known"],
                "min_notional_kind": p["instrument"].get("min_notional_kind"),
                "min_notional_provenance": p["instrument"].get("min_notional_provenance"),
                "provenance_complete": p["provenance"]["complete"],
            }
            for p in nested_packets
        ],
    }
    metadata_table_path = staging / "metadata_table_snapshot.v1.json"
    _atomic_write_text(metadata_table_path, json.dumps(metadata_table, indent=2) + "\n")

    evidence_links = [
        str(raw_instruments_path.resolve()),
        str(raw_mark_path.resolve()),
        str(raw_tickers_path.resolve()),
        str((staging / "capture_provenance_v1.json").resolve()),
        str((staging / "min_notional_mapping_table_v1.json").resolve()),
    ]
    governed_doc = {
        "schema_name": GOVERNED_SCHEMA_NAME,
        "schema_version": 1,
        "bundle_id": bundle_id,
        "source_kind": GOVERNED_SOURCE_KIND,
        "producer_id": PRODUCER_ID,
        "provider": "okx",
        "generated_at": as_of,
        "source_run_id": bundle_id,
        "source_stage": SOURCE_STAGE,
        "source_stage_reason": "okx_public_official_metadata_mapped_non_authorizing",
        "market_data_source_stage": MARKET_DATA_SOURCE_STAGE,
        "fixture_only": False,
        "observability_truth_allowed": False,
        "non_authorizing": True,
        "real_metadata_source_marked": True,
        "GOVERNED_SNAPSHOT_ACCEPTED_FOR_INTAKE": True,
        "git_sha": _git_sha(),
        "metadata_table_ref": str(metadata_table_path.resolve()),
        "metadata_refresh_utc": instruments_env.captured_at,
        "evidence_links": evidence_links,
        "selected_candidate_id": f"c-{selected['symbol']}",
        "universe": {
            "conceptual_size": len(instruments),
            "eligible_packet_count": len(nested_packets),
            "excluded_counts": exclusion_counts,
            "notes": "OKX public official SWAP linear USDT non-BTC mapped bundle",
        },
        "ranking": {
            "selected_top_n": TOP_N,
            "ranking_basis": "vol24h_desc_symbol_tiebreak",
            "notes": "non-authorizing liquidity ranking from OKX public tickers",
        },
        "selected_future": {
            "candidate_id": f"c-{selected['symbol']}",
            "symbol": selected["symbol"],
            "provider_instrument_id": selected["provider_instrument_id"],
            "exchange": "okx",
            "notes": "top-ranked eligible OKX instrument",
        },
        "packets": nested_packets,
        "min_notional_policy": {
            "direct_field_available": False,
            "mapping_authorized": True,
            "min_notional_kind": MIN_NOTIONAL_KIND,
            "formula_id": FORMULA_ID,
            "mapping_ratification_id": MAPPING_RATIFICATION_ID,
        },
        "captured_at_policy": {
            "captured_at": instruments_env.captured_at,
            "effective_at": mark_env.effective_at or mark_env.captured_at,
            "policy_ratification_id": "okx_captured_at_freshness_policy_ratification_v1",
        },
    }
    governed_path = staging / "futures_producer_packet_governed.v1.json"
    _atomic_write_text(governed_path, json.dumps(governed_doc, indent=2) + "\n")

    readme = f"""# OKX governed metadata bundle `{bundle_id}`

Producer: `{PRODUCER_ID}`
Venue: okx (public REST only)
Schema: `{GOVERNED_SCHEMA_NAME}`
Git SHA: `{_git_sha()}`

## Captures
- instruments digest: `{instruments_env.raw_payload_digest}`
- mark-price digest: `{mark_env.raw_payload_digest}`
- tickers digest: `{tickers_env.raw_payload_digest}`

## Mapping
- kind: `{MIN_NOTIONAL_KIND}`
- formula: `{FORMULA_ID}`
- ratification: `{MAPPING_RATIFICATION_ID}`

Non-authorizing. No orders. No runtime activation. No Truth-GO.
"""
    _atomic_write_text(staging / "README.md", readme)

    manifest_rc, manifest_msg = finalize_durable_bundle_manifest(staging)
    if manifest_rc != 0:
        _die(f"ERR: manifest finalize failed rc={manifest_rc} msg={manifest_msg}")

    # Atomic finalize: rename staging → final only after MANIFEST_VERIFY_RC=0.
    os.replace(staging, final_dir)
    # Rewrite absolute paths that pointed at staging.
    governed_final = final_dir / "futures_producer_packet_governed.v1.json"
    metadata_final = final_dir / "metadata_table_snapshot.v1.json"
    doc = json.loads(governed_final.read_text(encoding="utf-8"))
    doc["metadata_table_ref"] = str(metadata_final.resolve())
    doc["evidence_links"] = [
        str((final_dir / name).resolve())
        for name in (
            "raw_okx_instruments_swap.json",
            "raw_okx_mark_price_swap.json",
            "raw_okx_tickers_swap.json",
            "capture_provenance_v1.json",
            "min_notional_mapping_table_v1.json",
        )
    ]
    _atomic_write_text(governed_final, json.dumps(doc, indent=2) + "\n")
    # Re-finalize manifest after path rewrite.
    manifest_rc, manifest_msg = finalize_durable_bundle_manifest(final_dir)
    if manifest_rc != 0:
        _die(f"ERR: final manifest verify failed rc={manifest_rc} msg={manifest_msg}")

    summary = {
        "producer_id": PRODUCER_ID,
        "bundle_id": bundle_id,
        "bundle_dir": str(final_dir),
        "governed_packet_path": str(governed_final),
        "metadata_table_path": str(metadata_final),
        "manifest_verify_rc": manifest_rc,
        "eligible_count": len(ranked),
        "selected_symbol": selected["symbol"],
        "selected_venue": "okx",
        "exclusion_counts": exclusion_counts,
        "instruments_digest": instruments_env.raw_payload_digest,
        "mark_price_digest": mark_env.raw_payload_digest,
        "git_sha": _git_sha(),
        "non_authorizing": True,
        "authenticated_fetch": False,
    }
    _atomic_write_text(final_dir / "producer_summary.json", json.dumps(summary, indent=2) + "\n")
    # Final manifest again to include summary.
    manifest_rc, manifest_msg = finalize_durable_bundle_manifest(final_dir)
    summary["manifest_verify_rc"] = manifest_rc
    summary["manifest_verify_message"] = manifest_msg
    print(json.dumps(summary, indent=2))
    return summary


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="OKX public → governed futures producer packet")
    parser.add_argument("--archive-root", type=Path, required=True)
    parser.add_argument("--venue", default="okx")
    parser.add_argument("--market-type", default="swap")
    parser.add_argument("--settle-ccy", default="USDT")
    parser.add_argument("--exclude-underlying", default="BTC")
    parser.add_argument(
        "--confirm-okx-governed-producer",
        required=True,
        choices=[CONFIRM_TOKEN],
    )
    ns = parser.parse_args(argv)
    try:
        build_okx_governed_bundle_v1(
            archive_root=ns.archive_root,
            venue=ns.venue,
            market_type=ns.market_type,
            settle_ccy=ns.settle_ccy,
            exclude_underlying=ns.exclude_underlying,
            confirm=ns.confirm_okx_governed_producer,
        )
    except SystemExit as exc:
        return int(exc.code) if isinstance(exc.code, int) else 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
