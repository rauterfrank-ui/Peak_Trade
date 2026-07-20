#!/usr/bin/env python3
"""Materialize sealed long-panel OKX PT1H raw pages into MV2 research bars.

NON-AUTHORITATIVE. External archive only. Does not mutate git/productive code.
Reuses PT1H research volatility materialization from
``panel_sequential_signal_density_research_adapter_v0``.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd

_REPO = Path(__file__).resolve().parents[3]
for p in (_REPO, _REPO / "src"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from src.research.panel_sequential_signal_density_research_adapter_v0 import (  # noqa: E402
    _materialize_research_panel_volatility_estimate_columns_v0,
)

DEFAULT_ARCHIVE = Path(
    "/var/folders/j7/823by_lx7jl026wrk5jpnkmh0000gn/T/peak_trade_data_archive/"
    "sealed_lifecycle_long_panel_v1_d884a000_20260720T1832Z/"
    "longer_chronological_pit/chrono_3y_v1"
)
EXPECTED_MANIFEST_SHA256 = "f4c616c556ff3f2500bb5deff2070c5ee9c4b6a5d5d6ca5da3dc7aca1e8a3e56"
EXPECTED_CONTENT_HASH = "7bcda794ae2a355c6f36b2ea04703f39078063458f52034add44bec5644206bb"
EXPECTED_REGISTRY_DIGEST = "ddcdec738ff5661f3e2f6bd3dcc97a1bcddbf0b9254faa344b318558f1dbe289"


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _member_scratch_name(canonical_id: str) -> str:
    return canonical_id.replace(":", "_")


def _load_raw_ohlcv_pages(raw_dir: Path) -> pd.DataFrame:
    pages = sorted(raw_dir.glob("page_*.json"))
    if not pages:
        raise FileNotFoundError(f"no_pages:{raw_dir}")
    rows: list[dict[str, Any]] = []
    for page in pages:
        payload = _load_json(page)
        if str(payload.get("code")) != "0":
            raise ValueError(f"okx_page_error:{page.name}:{payload.get('code')}")
        for item in payload.get("data") or []:
            # OKX candle: ts,o,h,l,c,vol,volCcy,volCcyQuote,confirm
            ts_ms = int(item[0])
            confirm = str(item[8]) if len(item) > 8 else "1"
            if confirm != "1":
                continue
            rows.append(
                {
                    "timestamp": pd.Timestamp(ts_ms, unit="ms", tz="UTC"),
                    "open": float(item[1]),
                    "high": float(item[2]),
                    "low": float(item[3]),
                    "close": float(item[4]),
                    "volume": float(item[5]),
                }
            )
    if not rows:
        raise ValueError(f"empty_ohlcv:{raw_dir}")
    frame = pd.DataFrame(rows).drop_duplicates(subset=["timestamp"], keep="last")
    frame = frame.sort_values("timestamp").set_index("timestamp")
    if frame.index.has_duplicates:
        raise ValueError(f"duplicate_timestamps_after_dedupe:{raw_dir}")
    return frame


def _clip_common_panel(frame: pd.DataFrame, start: str, end: str) -> pd.DataFrame:
    start_ts = pd.Timestamp(start)
    end_ts = pd.Timestamp(end)
    out = frame.loc[(frame.index >= start_ts) & (frame.index <= end_ts)]
    if out.empty:
        raise ValueError("empty_after_common_panel_clip")
    return out


def _to_mv2_bars(ohlcv: pd.DataFrame) -> pd.DataFrame:
    bars = ohlcv.copy()
    # Sealed acquisition is public OHLCV-only; mark/index default to close with
    # explicit research note. Funding was not acquired → 0.0 (funding PnL not claimed).
    bars["mark_price"] = bars["close"].astype(float)
    bars["index_price"] = bars["close"].astype(float)
    bars["funding_rate"] = 0.0
    bars["is_final"] = True
    bars = _materialize_research_panel_volatility_estimate_columns_v0(bars)
    return bars


def materialize(
    archive_root: Path,
    *,
    force: bool = False,
) -> dict[str, Any]:
    manifest_path = (
        archive_root / "manifests" / "sealed_lifecycle_v1" / "sealed_lifecycle_manifest.json"
    )
    readiness_path = archive_root / "logs" / "bounded_long_panel_acquisition_readiness.json"
    acq_path = archive_root / "logs" / "bounded_long_panel_acquisition_summary.json"

    manifest_sha = _sha256_file(manifest_path)
    if manifest_sha != EXPECTED_MANIFEST_SHA256:
        raise ValueError(f"sealed_manifest_sha_mismatch:{manifest_sha}")
    manifest = _load_json(manifest_path)
    if manifest.get("content_hash") != EXPECTED_CONTENT_HASH:
        raise ValueError("content_hash_mismatch")
    if manifest.get("production_registry_digest") != EXPECTED_REGISTRY_DIGEST:
        raise ValueError("registry_digest_mismatch")
    if int(manifest.get("instrument_count_long_panel_included") or 0) != 65:
        raise ValueError("instrument_count_mismatch")
    if not bool(manifest.get("btc_excluded")) or not bool(manifest.get("spot_excluded")):
        raise ValueError("btc_or_spot_not_excluded")
    if str(manifest.get("frequency")) != "PT1H":
        raise ValueError("frequency_not_pt1h")

    readiness = _load_json(readiness_path)
    if not bool(readiness.get("economic_reevaluation_ready")):
        raise ValueError("economic_reevaluation_not_ready")
    if int(readiness.get("gaps_found", -1)) != 0:
        raise ValueError("gaps_found_nonzero")
    if int(readiness.get("duplicates_found", -1)) != 0:
        raise ValueError("duplicates_found_nonzero")
    if int(readiness.get("ordering_errors", -1)) != 0:
        raise ValueError("ordering_errors_nonzero")

    acq = _load_json(acq_path)
    # Archive summary historically stamped ready=false while readiness=true;
    # integrity fields below are authoritative for this materialization.
    if int(acq.get("gaps_found", -1)) != 0 or int(acq.get("duplicates_found", -1)) != 0:
        raise ValueError("acquisition_integrity_fail")
    if int(acq.get("ordering_errors", -1)) != 0:
        raise ValueError("acquisition_ordering_fail")
    if int(acq.get("instrument_count_acquired") or 0) != 65:
        raise ValueError("acquired_count_mismatch")

    common_start = str(manifest["common_panel_start"])
    common_end = str(manifest["common_panel_end"])
    included = [
        inst
        for inst in manifest.get("instruments") or []
        if str(inst.get("inclusion_decision")) == "INCLUDE_LONG_PANEL"
    ]
    if len(included) != 65:
        raise ValueError(f"included_len_mismatch:{len(included)}")

    out_root = archive_root / "normalized" / "mv2_research_bars_v1"
    out_root.mkdir(parents=True, exist_ok=True)
    member_digests: dict[str, str] = {}
    total_bars = 0
    for inst in sorted(included, key=lambda x: str(x["canonical_instrument_id"])):
        native = str(inst["native_instrument_id"])
        canonical = str(inst["canonical_instrument_id"])
        if "BTC" in canonical.upper() or "BTC" in native.upper():
            raise ValueError(f"btc_leaked:{canonical}")
        raw_dir = archive_root / "raw" / "ohlcv_pt1h" / native
        ohlcv = _load_raw_ohlcv_pages(raw_dir)
        clipped = _clip_common_panel(ohlcv, common_start, common_end)
        # ordering / gap checks on clipped panel
        deltas = clipped.index.to_series().diff().dropna().dt.total_seconds()
        if (deltas <= 0).any():
            raise ValueError(f"non_monotonic:{native}")
        bad_gaps = deltas[deltas != 3600.0]
        # Allow only the first diff absence; interior must be hourly contiguous.
        if len(bad_gaps) > 0:
            raise ValueError(f"non_hourly_or_gap:{native}:{bad_gaps.head(3).to_dict()}")
        bars = _to_mv2_bars(clipped)
        scratch_name = _member_scratch_name(canonical)
        out_dir = out_root / scratch_name
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "bars.parquet"
        if out_path.exists() and not force:
            existing = pd.read_parquet(out_path)
            if len(existing) != len(bars):
                raise ValueError(f"existing_bars_len_mismatch:{canonical}")
        else:
            bars.to_parquet(out_path)
        digest = _sha256_file(out_path)
        member_digests[canonical] = digest
        total_bars += int(len(bars))
        print(
            json.dumps(
                {
                    "phase": "materialize_member",
                    "instrument": native,
                    "bars": int(len(bars)),
                    "sha256": digest,
                }
            ),
            flush=True,
        )

    summary = {
        "schema_version": "sealed_long_panel_mv2_bars_materialization.v1",
        "archive_root_basename": archive_root.name,
        "sealed_manifest_sha256": manifest_sha,
        "content_hash": EXPECTED_CONTENT_HASH,
        "production_registry_digest": EXPECTED_REGISTRY_DIGEST,
        "instrument_count": 65,
        "common_panel_start": common_start,
        "common_panel_end": common_end,
        "total_bars_clipped": total_bars,
        "bars_root": str(out_root),
        "member_bar_sha256": member_digests,
        "mark_price_source": "close_proxy_public_ohlcv_only",
        "funding_rate_source": "not_acquired_set_zero",
        "volatility_materialization": (
            "panel_sequential_signal_density_research_adapter_v0."
            "_materialize_research_panel_volatility_estimate_columns_v0"
        ),
        "economic_reevaluation_ready_readiness_json": True,
        "acquisition_summary_ready_flag": bool(acq.get("economic_reevaluation_ready")),
        "readiness_vs_summary_note": (
            "readiness.json=true is authoritative; archive acquisition_summary "
            "ready flag may be false (metadata inconsistency, integrity fields match)"
        ),
        "live_authorized": False,
        "orders": False,
        "promotion_eligible": False,
        "economic_gate_opened": False,
    }
    summary_path = out_root / "materialization_summary.json"
    payload = json.dumps(summary, indent=2, sort_keys=True) + "\n"
    summary_path.write_text(payload, encoding="utf-8")
    summary["materialization_summary_sha256"] = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def main() -> int:
    args = [a for a in sys.argv[1:] if a != "--force"]
    force = "--force" in sys.argv
    archive = Path(args[0]) if args else DEFAULT_ARCHIVE
    summary = materialize(archive, force=force)
    print(json.dumps({"ok": True, "summary": summary}, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
