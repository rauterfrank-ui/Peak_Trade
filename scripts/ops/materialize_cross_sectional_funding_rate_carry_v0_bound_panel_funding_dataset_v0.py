#!/usr/bin/env python3
"""Materialize bound funding panel dataset for funding-rate carry v0.

Reuses existing OHLCV staging from the admissible-futures archive path and
adds funding-rate history via OKX public endpoint pagination (no auth).
Performs backward-asof join (no look-ahead) from funding timestamps to PT1H
bar timestamps. Writes funding manifest and normalized panel bars with funding.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.ops.ingest_okx_futures_public_market_data_canonical_dataset_staging_v1 import (  # noqa: E402
    RateLimiter,
    paginate_funding_history,
)
from src.research.cross_sectional_funding_rate_carry_v0_offline_economic_evaluation_execution_v0 import (  # noqa: E402
    INFRASTRUCTURE_GO_TOKEN,
)
from src.research.cross_sectional_bounded_panel_fetch_v0 import (  # noqa: E402
    backward_asof_funding_lookup_v0,
)
from src.research.missing_funding_policy_v0 import (  # noqa: E402
    MISSING_REASON_NO_PRIOR_FUNDING,
    is_missing_funding_value_v0,
    resolve_funding_rate_or_missing_v0,
)
from src.research.pit_futures_cross_sectional_research_data_digest_period_split_materialization_v0 import (  # noqa: E402
    load_panel_series_from_staging,
)

CONFIRM_GO = INFRASTRUCTURE_GO_TOKEN
DEFAULT_STAGING_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "datasets/admissible_futures/"
    "pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_v1/v1"
)
FUNDING_MANIFEST_REL = Path("panel/panel_funding_dataset_manifest.json")
FUNDING_BARS_REL = Path("panel/normalized_panel_bars_with_funding.json")
RAW_FUNDING_DIR_REL = Path("raw/funding_history")


def _die(msg: str, code: int = 2) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def _stable_digest(payload: Any) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _utc_ts_to_ms(timestamp_utc: str) -> int:
    dt = datetime.strptime(timestamp_utc, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


def _load_existing_manifest(staging_root: Path) -> dict[str, Any] | None:
    path = staging_root / FUNDING_MANIFEST_REL
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _verify_existing_manifest(staging_root: Path) -> bool:
    manifest = _load_existing_manifest(staging_root)
    if manifest is None:
        return False
    bars_path = staging_root / FUNDING_BARS_REL
    if not bars_path.is_file():
        return False
    bars_payload = json.loads(bars_path.read_text(encoding="utf-8"))
    bars = bars_payload.get("bars")
    if not isinstance(bars, list):
        return False
    computed = _stable_digest(bars)
    return str(manifest.get("funding_panel_digest", "")) == computed and int(
        manifest.get("row_count_total", -1)
    ) == len(bars)


def _funding_asof_lookup(
    *,
    funding_rows: list[dict[str, Any]],
    bar_timestamp_ms: int,
) -> tuple[str | None, str | None]:
    """PIT backward-asof join; missing stays None (no synthetic zero fallback)."""
    rate = backward_asof_funding_lookup_v0(funding_rows, bar_timestamp_ms)
    if is_missing_funding_value_v0(rate):
        return resolve_funding_rate_or_missing_v0(raw_value=None), MISSING_REASON_NO_PRIOR_FUNDING
    return resolve_funding_rate_or_missing_v0(raw_value=rate), None


def _fetch_funding_for_instrument(
    *,
    native_instrument_id: str,
    start_ms: int,
    end_ms: int,
    raw_dir: Path,
) -> list[dict[str, Any]]:
    import scripts.ops.ingest_okx_futures_public_market_data_canonical_dataset_staging_v1 as ingest

    original_inst = ingest.NATIVE_INSTRUMENT_ID
    try:
        ingest.NATIVE_INSTRUMENT_ID = native_instrument_id
        return paginate_funding_history(
            fetcher=ingest.okx_public_fetch_v1,
            rate_limiter=RateLimiter(),
            timeout_seconds=15.0,
            max_response_bytes=ingest.MAX_RESPONSE_BYTES_HARD_CAP,
            raw_dir=raw_dir,
            request_log=[],
            start_ms=start_ms,
            end_ms=end_ms,
        )
    finally:
        ingest.NATIVE_INSTRUMENT_ID = original_inst


def materialize_bound_panel_funding_dataset_v0(
    *,
    confirm: str,
    staging_root: Path,
    skip_fetch: bool = False,
) -> dict[str, Any]:
    if confirm != CONFIRM_GO:
        _die(f"ERR: confirm_go_token_required:{CONFIRM_GO}")
    staging_root = staging_root.resolve()
    if not staging_root.is_dir():
        _die(f"ERR: missing_staging_root:{staging_root}")

    if _verify_existing_manifest(staging_root):
        manifest = _load_existing_manifest(staging_root) or {}
        return {
            "verdict": "BOUND_FUNDING_PANEL_READY_REUSED",
            "staging_root": str(staging_root),
            "manifest_verified": True,
            "skip_fetch": True,
            "row_count_total": int(manifest.get("row_count_total", 0)),
            "funding_panel_digest": str(manifest.get("funding_panel_digest", "")),
        }

    panel_series, panel_ref = load_panel_series_from_staging(staging_root)
    if not panel_series:
        _die("ERR: empty_panel_series")

    all_bars = [bar for series in panel_series for bar in series.bars]
    start_ms = min(_utc_ts_to_ms(bar.timestamp_utc) for bar in all_bars)
    end_ms = max(_utc_ts_to_ms(bar.timestamp_utc) for bar in all_bars)
    raw_dir = staging_root / RAW_FUNDING_DIR_REL
    raw_dir.mkdir(parents=True, exist_ok=True)

    funding_by_native: dict[str, list[dict[str, Any]]] = {}
    if not skip_fetch:
        for series in panel_series:
            funding_rows = _fetch_funding_for_instrument(
                native_instrument_id=series.native_instrument_id,
                start_ms=start_ms,
                end_ms=end_ms,
                raw_dir=raw_dir,
            )
            funding_by_native[series.native_instrument_id] = sorted(
                funding_rows, key=lambda item: int(str(item.get("fundingTime", "0")))
            )

    funding_rows_out: list[dict[str, Any]] = []
    missing_reasons: list[str] = []
    for series in panel_series:
        source_rows = funding_by_native.get(series.native_instrument_id, [])
        for bar in series.bars:
            ts_ms = _utc_ts_to_ms(bar.timestamp_utc)
            funding_rate, missing_reason = _funding_asof_lookup(
                funding_rows=source_rows,
                bar_timestamp_ms=ts_ms,
            )
            if missing_reason is not None:
                missing_reasons.append(
                    f"{series.instrument_id}@{bar.timestamp_utc}:{missing_reason}"
                )
            funding_rows_out.append(
                {
                    "instrument_id": series.instrument_id,
                    "native_instrument_id": series.native_instrument_id,
                    "timestamp_utc": bar.timestamp_utc,
                    "open": bar.open,
                    "high": bar.high,
                    "low": bar.low,
                    "close": bar.close,
                    "volume": bar.volume,
                    "funding_rate": funding_rate,
                    "missing_funding_reason": missing_reason,
                    "is_final": bar.is_final,
                }
            )

    funding_rows_out.sort(key=lambda row: (row["instrument_id"], row["timestamp_utc"]))
    funding_digest = _stable_digest(funding_rows_out)
    bars_path = staging_root / FUNDING_BARS_REL
    bars_path.write_text(
        json.dumps({"bars": funding_rows_out}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    manifest = {
        "schema_version": "pit_okx_pt1h_panel_funding_dataset_manifest_v1",
        "panel_id": "pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_v1",
        "dataset_extension": "with_funding_v1",
        "panel_ref": panel_ref,
        "instrument_ids": [s.instrument_id for s in panel_series],
        "native_instrument_ids": [s.native_instrument_id for s in panel_series],
        "row_count_total": len(funding_rows_out),
        "funding_panel_digest": funding_digest,
        "backward_asof_policy": "funding_time_lte_bar_timestamp_no_lookahead",
        "missing_funding_policy": "fail_closed_none_no_zero_fallback",
        "missing_funding_count": len(missing_reasons),
        "source_ohlcv_staging": str(staging_root),
        "fetched_from_okx_public": not skip_fetch,
    }
    manifest_path = staging_root / FUNDING_MANIFEST_REL
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    return {
        "verdict": "BOUND_FUNDING_PANEL_READY",
        "staging_root": str(staging_root),
        "manifest_path": str(manifest_path),
        "bars_path": str(bars_path),
        "manifest_verified": _verify_existing_manifest(staging_root),
        "row_count_total": len(funding_rows_out),
        "funding_panel_digest": funding_digest,
        "skip_fetch": skip_fetch,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirm", required=True)
    parser.add_argument("--staging-root", type=Path, default=DEFAULT_STAGING_ROOT)
    parser.add_argument("--skip-fetch", action="store_true")
    args = parser.parse_args()
    result = materialize_bound_panel_funding_dataset_v0(
        confirm=args.confirm,
        staging_root=args.staging_root,
        skip_fetch=args.skip_fetch,
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
