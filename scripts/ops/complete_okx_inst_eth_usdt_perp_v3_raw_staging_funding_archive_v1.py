#!/usr/bin/env python3
"""Complete ETH-USDT-SWAP raw staging funding via OKX historical CDN archive.

Mechanical wrapper around okx_historical_funding_archive_* owners.
Does not re-fetch OHLCV/mark/index. Re-finalizes existing .tmp staging.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.ops import (
    ingest_okx_futures_public_market_data_canonical_dataset_staging_v1 as okx_ingest,
)
from src.research.okx_historical_funding_archive_ingest_for_materialized_panel_v0 import (
    fetch_panel_archive_month_v0,
    ingest_archive_bytes_for_instrument_v0,
    _default_http_fetcher,
)
from src.research.okx_historical_funding_archive_ingest_v0 import (
    ArchiveAccessGuardV0,
    archive_events_to_rest_compatible_rows_v0,
    compute_required_month_buckets_v0,
)

CONFIRM_GO = "GO_CURRENT_V3_FUNDING_ARCHIVE_COMPLETION_AND_QUALIFICATION_V1"
VENUE_SYMBOL = "ETH-USDT-SWAP"
NATIVE_INSTRUMENT_ID = "ETH-USDT-SWAP"


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _write_funding_raw_pages(raw_dir: Path, rows: List[Dict[str, str]]) -> int:
    raw_dir.mkdir(parents=True, exist_ok=True)
    for old in raw_dir.glob("funding_p*.json"):
        old.unlink()
    page_size = 300
    page = 0
    for i in range(0, len(rows), page_size):
        chunk = rows[i : i + page_size]
        body = json.dumps({"code": "0", "msg": "", "data": chunk}, separators=(",", ":")).encode(
            "utf-8"
        )
        digest = _sha256_bytes(body)
        path = raw_dir / f"funding_p{page:04d}_{digest[:16]}.json"
        path.write_bytes(body)
        page += 1
    return page


def run_completion_v1(
    *,
    confirm_go: str,
    raw_staging_root: Path,
    target_staging_root: Path,
    durable_evidence_root: Path,
    enforce_settlement_interval: bool = False,
) -> Dict[str, Any]:
    if confirm_go != CONFIRM_GO:
        raise SystemExit(f"ERR:confirm_go_required:{CONFIRM_GO}")
    if not raw_staging_root.is_dir():
        raise SystemExit(f"ERR:raw_staging_missing:{raw_staging_root}")
    config_path = raw_staging_root / "INGESTION_CONFIG.json"
    if not config_path.is_file():
        raise SystemExit(f"ERR:ingestion_config_missing:{config_path}")
    ingestion_config = json.loads(config_path.read_text(encoding="utf-8"))
    data_period = ingestion_config["data_period"]
    start_utc = str(data_period["start_utc"])
    end_utc = str(data_period["end_utc"])
    end_exclusive = end_utc  # filter uses exclusive end semantics in panel ingest

    dq_path = raw_staging_root / "DATA_QUALITY_REPORT.json"
    if dq_path.is_file():
        dq = json.loads(dq_path.read_text(encoding="utf-8"))
        series = dq.get("series_row_counts") or {}
    else:
        series = {"ohlcv": 0, "mark": 0, "index": 0, "funding": 0}

    ohlcv_rows = int(series.get("ohlcv", 0))
    mark_rows = int(series.get("mark", 0))
    index_rows = int(series.get("index", 0))
    if ohlcv_rows < 3_000_000:
        raise SystemExit(f"ERR:ohlcv_row_count_unexpected:{ohlcv_rows}")

    months = compute_required_month_buckets_v0(
        period_start_utc=start_utc,
        period_end_exclusive_utc=end_exclusive,
    )
    cache_dir = durable_evidence_root / "funding_archive_cache" / VENUE_SYMBOL
    guard = ArchiveAccessGuardV0(
        max_instruments=1,
        max_months=len(months) + 2,
        max_http_requests=max(120, len(months) + 10),
        max_total_bytes=512_000_000,
        max_runtime_seconds=3600,
    )
    guard.instruments_used = 1
    all_events = []
    fetch_records: List[Dict[str, Any]] = []
    last_mono = 0.0
    missing_months: List[str] = []

    for month in months:
        month_reason = guard.check_months()
        if month_reason:
            raise SystemExit(f"ERR:fetch_guard_months:{month_reason}")
        guard.months_used += 1
        zip_bytes, record, last_mono, fail = fetch_panel_archive_month_v0(
            venue_symbol=VENUE_SYMBOL,
            month=month,
            archive_dir=cache_dir,
            guard=guard,
            probe_dir=None,
            fetcher=_default_http_fetcher,
            last_fetch_monotonic=last_mono,
        )
        fetch_records.append(
            {
                "month": month,
                "http_status": record.http_status,
                "byte_count": record.byte_count,
                "sha256": record.sha256,
                "reason_code": record.reason_code,
                "parse_status": record.parse_status,
            }
        )
        if zip_bytes is None:
            missing_months.append(month)
            continue
        events, _report, parse_fail = ingest_archive_bytes_for_instrument_v0(
            zip_bytes,
            venue_symbol=VENUE_SYMBOL,
            period_start_utc=start_utc,
            period_end_exclusive_utc=end_exclusive,
            enforce_settlement_interval=enforce_settlement_interval,
        )
        if parse_fail:
            raise SystemExit(f"ERR:archive_parse:{month}:{parse_fail}")
        all_events.extend(events)

    rest_rows = archive_events_to_rest_compatible_rows_v0(tuple(all_events))
    dedup: Dict[int, Dict[str, str]] = {}
    for row in rest_rows:
        dedup[int(row["fundingTime"])] = row
    merged = [dedup[k] for k in sorted(dedup)]
    if not merged:
        raise SystemExit("ERR:no_funding_events_after_archive_ingest")

    funding_start_ms = int(merged[0]["fundingTime"])
    funding_end_ms = int(merged[-1]["fundingTime"])
    pages = _write_funding_raw_pages(raw_staging_root / "raw", merged)
    funding_rows = len(merged)

    instrument_binding = json.loads((raw_staging_root / "INSTRUMENT_BINDING.json").read_text())
    instrument_metadata = dict(instrument_binding.get("instrument_metadata") or {})
    instrument_metadata.setdefault("instId", NATIVE_INSTRUMENT_ID)

    bid_ask = json.loads(
        (raw_staging_root / "reports" / "BID_ASK_CAPABILITY.json").read_text(encoding="utf-8")
    )
    domain_decision = json.loads(
        (raw_staging_root / "reports" / "DOMAIN_DECISION.json").read_text(encoding="utf-8")
    )
    request_log: list[Any] = []

    binding = okx_ingest.OkxFuturesIngestInstrumentBindingV1(
        native_instrument_id=str(instrument_binding["native_instrument_id"]),
        canonical_instrument_id=str(instrument_binding["canonical_instrument_id"]),
        selection_id=str(instrument_binding.get("selection_id") or ""),
        selection_integrity_digest=str(instrument_binding.get("selection_integrity_digest") or ""),
    )

    matrix = okx_ingest.build_availability_matrix(
        ohlcv_rows=ohlcv_rows,
        mark_rows=mark_rows,
        index_rows=index_rows,
        funding_rows=funding_rows,
        bid_ask_capability=bid_ask,
        start_utc=start_utc,
        end_utc=end_utc,
    )
    schema_complete = okx_ingest.all_required_series_available(
        matrix, dataset_profile="economic_research_v1"
    )
    verdict = okx_ingest.classify_verdict(schema_complete=schema_complete, integrity_pass=True)

    ts_slug = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    if target_staging_root.exists():
        raise SystemExit(f"ERR:target_staging_exists:{target_staging_root}")

    result = okx_ingest._finalize_reports(
        tmp_root=raw_staging_root,
        target_dataset_root=target_staging_root,
        durable_evidence_root=durable_evidence_root,
        ts_slug=ts_slug,
        instrument_metadata=instrument_metadata,
        request_log=request_log,
        availability_matrix=matrix,
        verdict=verdict,
        start_utc=start_utc,
        end_utc=end_utc,
        staging_window_days=int(ingestion_config.get("staging_window_days", 0)),
        series_counts={
            "ohlcv": ohlcv_rows,
            "mark": mark_rows,
            "index": index_rows,
            "funding": funding_rows,
        },
        bid_ask_capability=bid_ask,
        domain_decision=domain_decision,
        ingest_binding=binding,
        okx_index_candle_inst_id=str(
            instrument_binding.get("okx_index_candle_inst_id") or "ETH-USDT"
        ),
    )
    result["funding_archive_completion_v1"] = {
        "months_requested": len(months),
        "months_missing_http": missing_months,
        "funding_pages_written": pages,
        "funding_record_count": funding_rows,
        "funding_start_ms": funding_start_ms,
        "funding_end_ms": funding_end_ms,
        "fetch_records_sample": fetch_records[:5],
    }
    okx_ingest._emit_machine_lines(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirm-go", required=True)
    parser.add_argument("--raw-staging-root", type=Path, required=True)
    parser.add_argument("--target-staging-root", type=Path, required=True)
    parser.add_argument("--durable-evidence-root", type=Path, required=True)
    ns = parser.parse_args()
    run_completion_v1(
        confirm_go=ns.confirm_go,
        raw_staging_root=ns.raw_staging_root.expanduser().resolve(),
        target_staging_root=ns.target_staging_root.expanduser().resolve(),
        durable_evidence_root=ns.durable_evidence_root.expanduser().resolve(),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
