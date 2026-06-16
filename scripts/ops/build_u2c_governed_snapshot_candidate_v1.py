#!/usr/bin/env python3
"""U2C: build governed snapshot candidate bundle from U5D validation (nested U2B packet shape).

Emits futures_producer_packet_governed.v1.json with nested FuturesProducerPacket entries,
metadata table artifacts, and MANIFEST_VERIFY.log containing MANIFEST_VERIFY_RC=0.

Not loader write, readmodel write, dashboard wiring, truth-GO, or trading.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.ops.primary_evidence_retention_v0 import finalize_durable_bundle_manifest
from scripts.ops.u2c_packet_shape_v1 import (
    CANDIDATE_VALIDATION_ALLOWED_MISSING_PROVIDER_METADATA,
    flat_row_to_nested_packet,
    summarize_instrument_completeness,
)

CONFIRM_TOKEN = "CONFIRM_U2C_GOVERNED_SNAPSHOT_CANDIDATE_BUILD_V1"
GOVERNED_SCHEMA_NAME = "futures_producer_packet_governed.v1"
GOVERNED_SOURCE_KIND = "governed_metadata_snapshot"
PRODUCER_ID = "u2c_governed_snapshot_candidate_build_v1"
SOURCE_STAGE = "paper"
SOURCE_STAGE_REASON = "public_view_only_market_data_packaged_for_paper_stage_candidate"
MARKET_DATA_SOURCE_STAGE = "market_data_view_only"
TOP_N = 20


def _die(msg: str, code: int = 2) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def _load_u5d(path: Path) -> Mapping[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        _die(f"ERR: cannot read U5D validation JSON {path}: {exc}")
    if not isinstance(data, dict):
        _die(f"ERR: U5D validation root must be object: {path}")
    if data.get("schema") != "u5d_u2c_candidate_validation_v1":
        _die("ERR: expected schema u5d_u2c_candidate_validation_v1")
    return data


def _rank_lookup(top20: Sequence[Mapping[str, Any]]) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for item in top20:
        sym = str(item.get("symbol") or "")
        rank = item.get("rank")
        if sym and isinstance(rank, int):
            out[sym] = rank
    return out


def build_governed_snapshot_candidate_bundle(
    *,
    confirm: str,
    u5d_validation_path: Path,
    output_dir: Path,
    archive_root: Path,
    bundle_id: str,
    evidence_links: Optional[Sequence[str]] = None,
) -> Dict[str, Any]:
    if confirm != CONFIRM_TOKEN:
        _die("ERR: confirm token required for governed snapshot candidate build")

    u5d = _load_u5d(u5d_validation_path)
    packet_rows = u5d.get("packet_candidates") or []
    top20_raw = u5d.get("top20_ranking_candidate") or []
    if not isinstance(packet_rows, list) or not packet_rows:
        _die("ERR: packet_candidates missing or empty in U5D validation")

    output_dir = output_dir.expanduser().resolve()
    archive_root = archive_root.expanduser().resolve()
    try:
        output_dir.relative_to(archive_root)
    except ValueError:
        _die("ERR: output_dir must be under archive_root")

    output_dir.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    fetched_at = str(u5d.get("fetched_at") or generated_at)
    rank_by_symbol = _rank_lookup(top20_raw)
    universe_size = len(packet_rows)

    nested_packets: List[Dict[str, Any]] = []
    for row in packet_rows:
        if not isinstance(row, Mapping):
            continue
        symbol = str(row.get("symbol") or "")
        if not symbol:
            continue
        nested_packets.append(
            flat_row_to_nested_packet(
                row,
                candidate_id=f"c-{symbol}",
                source_universe_size=universe_size,
                rank=rank_by_symbol.get(symbol),
                selected_top_n=TOP_N,
            )
        )

    if not nested_packets:
        _die("ERR: no nested packets produced")

    metadata_table_path = output_dir / "metadata_table.v1.json"
    metadata_rows = [
        {
            "instrument_id": p["candidate"]["instrument_id"],
            "symbol": p["candidate"]["symbol"],
            "market_type": p["candidate"]["market_type"],
            "exchange": p["candidate"]["exchange"],
            "base_currency": p["candidate"]["base_currency"],
            "quote_currency": p["candidate"]["quote_currency"],
            "instrument_complete": p["instrument"]["complete"],
            "provenance_complete": p["provenance"]["complete"],
        }
        for p in nested_packets
    ]
    metadata_table_path.write_text(
        json.dumps(
            {
                "schema": "metadata_table.v1",
                "bundle_id": bundle_id,
                "row_count": len(metadata_rows),
                "rows": metadata_rows,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    metadata_table_ref_path = output_dir / "metadata_table_ref.v1.json"
    metadata_table_ref_path.write_text(
        json.dumps(
            {
                "schema": "metadata_table_ref.v1",
                "bundle_id": bundle_id,
                "metadata_table_ref": str(metadata_table_path.resolve()),
                "row_count": len(metadata_rows),
                "source_stage": SOURCE_STAGE,
                "market_data_source_stage": MARKET_DATA_SOURCE_STAGE,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    links: List[str] = []
    if evidence_links:
        links.extend(str(p) for p in evidence_links)
    input_paths = u5d.get("input_paths") or {}
    if isinstance(input_paths, dict):
        for key in ("probe_report", "raw_instruments", "raw_tickers"):
            val = input_paths.get(key)
            if isinstance(val, str) and val.strip():
                links.append(val.strip())
    links.append(str(u5d_validation_path.resolve()))
    # stable dedupe
    seen: set[str] = set()
    deduped_links: List[str] = []
    for link in links:
        if link not in seen:
            seen.add(link)
            deduped_links.append(link)

    evidence_links_path = output_dir / "evidence_links.v1.json"
    evidence_links_path.write_text(
        json.dumps(
            {
                "schema": "evidence_links.v1",
                "bundle_id": bundle_id,
                "source_stage": SOURCE_STAGE,
                "market_data_source_stage": MARKET_DATA_SOURCE_STAGE,
                "evidence_links": deduped_links,
                "input_checksums": u5d.get("input_checksums") or {},
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    top20_path = output_dir / "top20_ranking_candidate.v1.json"
    top20_path.write_text(
        json.dumps(
            {
                "schema": "top20_ranking_candidate.v1",
                "bundle_id": bundle_id,
                "candidate_count": len(top20_raw),
                "ranking_basis": "vol24h_desc",
                "candidates": list(top20_raw),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    completeness_summary = summarize_instrument_completeness(nested_packets)

    governed_path = output_dir / "futures_producer_packet_governed.v1.json"
    governed_doc: Dict[str, Any] = {
        "schema_name": GOVERNED_SCHEMA_NAME,
        "schema_version": 1,
        "bundle_id": bundle_id,
        "source_kind": GOVERNED_SOURCE_KIND,
        "producer_id": PRODUCER_ID,
        "provider": u5d.get("provider") or "kraken_futures",
        "generated_at": generated_at,
        "source_run_id": bundle_id,
        "source_stage": SOURCE_STAGE,
        "source_stage_reason": SOURCE_STAGE_REASON,
        "market_data_source_stage": MARKET_DATA_SOURCE_STAGE,
        "fixture_only": False,
        "observability_truth_allowed": False,
        "non_authorizing": True,
        "real_metadata_source_marked": True,
        "candidate_phase": True,
        "u2b_candidate_validation_only": True,
        "instrument_completeness_mode": "candidate_validation",
        "missing_provider_metadata_policy": {
            "allowed_missing_provider_metadata": sorted(
                CANDIDATE_VALIDATION_ALLOWED_MISSING_PROVIDER_METADATA
            ),
            "reason": "kraken_public_instruments_view_missing_min_notional",
            "not_loader_write_eligible": True,
            "not_observability_truth": True,
        },
        "instrument_completeness_summary": completeness_summary,
        "GOVERNED_SNAPSHOT_ACCEPTED_FOR_INTAKE": False,
        "metadata_table_ref": str(metadata_table_path.resolve()),
        "metadata_refresh_utc": fetched_at,
        "evidence_links": deduped_links,
        "candidate_packet_count": len(nested_packets),
        "selected_candidate_id": None,
        "universe": {
            "conceptual_size": universe_size,
            "eligible_packet_count": len(nested_packets),
            "notes": "U2c governed snapshot candidate bundle — nested U2B packet shape",
        },
        "ranking": {
            "selected_top_n": TOP_N,
            "ranking_basis": "vol24h_desc",
            "notes": "non-authorizing candidate ranking",
            "u5b_alphabetical_preview_not_used": True,
        },
        "selected_future": {
            "candidate_id": None,
            "symbol": None,
            "notes": "no selected tradable future — candidate bundle only",
        },
        "packets": nested_packets,
    }
    governed_path.write_text(json.dumps(governed_doc, indent=2) + "\n", encoding="utf-8")

    safety_flags_path = output_dir / "candidate_safety_flags.v1.json"
    safety_flags_path.write_text(
        json.dumps(
            {
                "schema": "candidate_safety_flags.v1",
                "CANDIDATE_BUNDLE_ONLY": True,
                "GOVERNED_SNAPSHOT_ACCEPTED_FOR_INTAKE": False,
                "SNAPSHOT_INTAKE_EXECUTED": False,
                "LOADER_RUN_EXECUTED": False,
                "READMODEL_WRITE_EXECUTED": False,
                "DASHBOARD_WIRING_EXECUTED": False,
                "TRUTH_GO_GRANTED": False,
                "LIVE_AUTHORIZED": False,
                "PREFLIGHT_LIFT_AUTHORIZED": False,
                "SELECTED_TRADABLE_FUTURE_CREATED": False,
                "NOT_TRADING": True,
                "NOT_TRUTH_GO": True,
                "NOT_SELECTED_TRADABLE_FUTURE": True,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    manifest_rc, manifest_msg = finalize_durable_bundle_manifest(output_dir)
    if manifest_rc != 0:
        _die(f"ERR: bundle manifest finalize failed rc={manifest_rc} msg={manifest_msg}")

    summary = {
        "bundle_id": bundle_id,
        "output_dir": str(output_dir),
        "candidate_packet_count": len(nested_packets),
        "top20_candidate_count": len(top20_raw),
        "manifest_verify_rc": manifest_rc,
        "nested_packet_shape": True,
        "instrument_completeness_summary": completeness_summary,
        "source_stage": SOURCE_STAGE,
        "market_data_source_stage": MARKET_DATA_SOURCE_STAGE,
    }
    (output_dir / "build_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    return summary


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build U2C governed snapshot candidate bundle (nested U2B packet shape)."
    )
    parser.add_argument("--u5d-validation", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--archive-root", type=Path, required=True)
    parser.add_argument("--bundle-id", type=str, required=True)
    parser.add_argument("--evidence-link", action="append", default=[])
    parser.add_argument(
        "--confirm-governed-snapshot-candidate-build",
        required=True,
        choices=[CONFIRM_TOKEN],
    )
    ns = parser.parse_args(argv)
    try:
        build_governed_snapshot_candidate_bundle(
            confirm=ns.confirm_governed_snapshot_candidate_build,
            u5d_validation_path=ns.u5d_validation,
            output_dir=ns.output_dir,
            archive_root=ns.archive_root,
            bundle_id=ns.bundle_id,
            evidence_links=tuple(ns.evidence_link),
        )
    except SystemExit as exc:
        return int(exc.code) if isinstance(exc.code, int) else 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
