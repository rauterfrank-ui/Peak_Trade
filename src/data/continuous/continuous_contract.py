"""
Continuous Contract Builder (Offline-First)
===========================================

Ziel:
- Deterministisches Building von Continuous-Contract OHLCV-Zeitreihen
  aus mehreren Einzelkontrakten.

MVP:
- Adjustment: NONE (stitch) und BACK_ADJUST (klassischer Offset-Adjust)
- Keine Vendor-Integration, keine Live-Calls.

Input/Output:
- Input pro Kontrakt: OHLCV DataFrame (DatetimeIndex, tz-aware, UTC empfohlen)
- Output: OHLCV DataFrame (stitch/adjust), deterministisch sortiert.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import pandas as pd

from src.data.contracts import validate_ohlcv


class AdjustmentMethod(str, Enum):
    NONE = "NONE"
    BACK_ADJUST = "BACK_ADJUST"
    RATIO_ADJUST = "RATIO_ADJUST"  # reserved (not implemented in MVP)


@dataclass(frozen=True, slots=True)
class ContinuousSegment:
    """
    Definiert, welcher Kontrakt in welchem Zeitfenster verwendet wird.

    Zeitfenster ist inklusiv: [start_ts, end_ts]
    """

    contract_symbol: str
    start_ts: pd.Timestamp
    end_ts: pd.Timestamp


def _ensure_utc_index(df: pd.DataFrame) -> pd.DataFrame:
    if not isinstance(df.index, pd.DatetimeIndex):
        raise ValueError("Expected DatetimeIndex for OHLCV frame.")
    if df.index.tz is None:
        raise ValueError("Expected timezone-aware index (UTC recommended).")
    if str(df.index.tz) != "UTC":
        df = df.copy()
        df.index = df.index.tz_convert("UTC")
    return df


def _apply_price_offset(df: pd.DataFrame, offset: float) -> pd.DataFrame:
    if offset == 0.0:
        return df
    out = df.copy()
    for col in ("open", "high", "low", "close"):
        out[col] = out[col] + float(offset)
    return out


def build_continuous_contract(
    contract_frames: Dict[str, pd.DataFrame],
    segments: Sequence[ContinuousSegment],
    *,
    adjustment: AdjustmentMethod = AdjustmentMethod.NONE,
    validate: bool = True,
) -> pd.DataFrame:
    """
    Baut einen Continuous-Contract OHLCV-Frame aus Segmenten.

    Args:
        contract_frames: Mapping contract_symbol -> OHLCV DataFrame
        segments: ordered Segmente (chronologisch, nicht überlappend)
        adjustment: NONE oder BACK_ADJUST (RATIO_ADJUST not implemented)
        validate: Wenn True: validate_ohlcv pro Segment + Ergebnis
    """
    if adjustment == AdjustmentMethod.RATIO_ADJUST:
        raise NotImplementedError("RATIO_ADJUST is reserved; not implemented in MVP.")

    if not segments:
        raise ValueError("segments must not be empty.")

    # Extract segment frames in order (and normalize index).
    seg_frames: List[pd.DataFrame] = []
    seg_symbols: List[str] = []
    for seg in segments:
        if seg.contract_symbol not in contract_frames:
            raise KeyError(f"Missing contract frame for {seg.contract_symbol!r}")
        df = contract_frames[seg.contract_symbol]
        df = _ensure_utc_index(df)
        if validate:
            validate_ohlcv(df, strict=True, require_tz=True, allow_partial_nans=True)
        # Slice window
        part = df.loc[seg.start_ts : seg.end_ts].copy()
        part = part.sort_index()
        if part.empty:
            raise ValueError(
                f"Empty segment slice for {seg.contract_symbol} [{seg.start_ts}..{seg.end_ts}]"
            )
        seg_frames.append(part)
        seg_symbols.append(seg.contract_symbol)

    # Simple overlap/ordering sanity: end < next start is OK; end == next start allowed (rare).
    for i in range(len(segments) - 1):
        if segments[i].end_ts > segments[i + 1].start_ts:
            raise ValueError("segments overlap or are not ordered chronologically.")

    offsets: List[float] = [0.0 for _ in seg_frames]
    if adjustment == AdjustmentMethod.BACK_ADJUST:
        # Back-adjust historical segments to match the most recent segment.
        offsets[-1] = 0.0
        for i in range(len(seg_frames) - 2, -1, -1):
            old_close = float(seg_frames[i].iloc[-1]["close"])
            new_close = float(seg_frames[i + 1].iloc[0]["close"])
            offsets[i] = (new_close + offsets[i + 1]) - old_close

    stitched: List[pd.DataFrame] = []
    for df, off in zip(seg_frames, offsets):
        stitched.append(_apply_price_offset(df, off))

    out = pd.concat(stitched, axis=0)
    out = out[~out.index.duplicated(keep="last")]
    out = out.sort_index()

    if validate:
        validate_ohlcv(out, strict=True, require_tz=True, allow_partial_nans=True)

    return out


def sha256_of_ohlcv_frame(df: pd.DataFrame) -> str:
    """
    Deterministischer Hash eines OHLCV Frames.

    Stabilisiert:
    - Index: ISO8601 UTC strings
    - Floats: gerundet auf 12 Dezimalstellen
    """
    df = _ensure_utc_index(df)
    df = df.sort_index()
    required_cols = ["open", "high", "low", "close", "volume"]
    payload = {
        "columns": required_cols,
        "index": [ts.isoformat() for ts in df.index],
        "data": [],
    }
    for _, row in df[required_cols].iterrows():
        row_out = []
        for v in row.tolist():
            if v is None:
                row_out.append(None)
                continue
            fv = float(v)
            if math.isnan(fv):
                row_out.append(None)
            else:
                row_out.append(round(fv, 12))
        payload["data"].append(row_out)

    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )
    return sha256(raw).hexdigest()


__all__ = [
    "AdjustmentMethod",
    "ContinuousSegment",
    "build_continuous_contract",
    "sha256_of_ohlcv_frame",
]
