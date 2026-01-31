#!/usr/bin/env python3
"""
Build Continuous Contract (Offline-First)
========================================

Dieses Script baut aus OHLCV-Dateien je Kontrakt (Parquet) einen Continuous Contract.

NO-LIVE: Keine Live-Feeds, keine Broker-Orders.

Input-Konvention (MVP):
- `--input-dir`: enthält `{CONTRACT_SYMBOL}.parquet`
- `--segments-json`: JSON Liste von Segmenten:
  [
    {"contract_symbol":"NQH2026","start_ts":"2026-01-01T00:00:00Z","end_ts":"2026-01-15T23:00:00Z"},
    ...
  ]
Output:
- `--output-parquet`: Continuous OHLCV Parquet
- stdout: sha256 hash des Outputs
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from src.data.continuous.continuous_contract import (
    AdjustmentMethod,
    ContinuousSegment,
    build_continuous_contract,
    sha256_of_ohlcv_frame,
)


def _load_segments(path: Path) -> list[ContinuousSegment]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError("segments json must be a list")
    segs: list[ContinuousSegment] = []
    for item in raw:
        segs.append(
            ContinuousSegment(
                contract_symbol=item["contract_symbol"],
                start_ts=pd.Timestamp(item["start_ts"]),
                end_ts=pd.Timestamp(item["end_ts"]),
            )
        )
    return segs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input-dir", required=True, help="Directory with {SYMBOL}.parquet OHLCV files")
    ap.add_argument("--segments-json", required=True, help="JSON file describing segments")
    ap.add_argument("--output-parquet", required=True, help="Output parquet path")
    ap.add_argument(
        "--adjustment",
        default="NONE",
        choices=[m.value for m in AdjustmentMethod if m != AdjustmentMethod.RATIO_ADJUST],
        help="Adjustment method (MVP: NONE, BACK_ADJUST)",
    )
    args = ap.parse_args()

    input_dir = Path(args.input_dir)
    seg_path = Path(args.segments_json)
    out_path = Path(args.output_parquet)

    segments = _load_segments(seg_path)
    symbols = sorted({s.contract_symbol for s in segments})

    frames: dict[str, pd.DataFrame] = {}
    for sym in symbols:
        fp = input_dir / f"{sym}.parquet"
        if not fp.exists():
            raise FileNotFoundError(f"Missing input parquet for contract: {sym} at {fp}")
        frames[sym] = pd.read_parquet(fp)

    out = build_continuous_contract(frames, segments, adjustment=AdjustmentMethod(args.adjustment))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(out_path)

    digest = sha256_of_ohlcv_frame(out)
    print(digest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
