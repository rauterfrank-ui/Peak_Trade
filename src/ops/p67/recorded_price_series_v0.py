"""v0: load simple return series from local recorded public REST JSON snapshots (no network).

Reads a bounded scan of ``*.json`` under an operator directory, extracts Binance-style
``bidPrice``/``askPrice`` (or captured ``bid``/``ask`` decimals), computes midpoints in file/name
order, then simple returns: (mid_i / mid_{i-1}) - 1.

Path hygiene mirrors recorded-public-rest gates: allowed under ``/tmp`` (``peak_trade_*`` or
``pytest`` prefix segments) or under ``tempfile.gettempdir()`` when it is not the filesystem
``/tmp``. Repository tree paths are rejected.
"""

from __future__ import annotations

import json
import math
import tempfile
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, List, Optional, Tuple

MAX_JSON_FILES_SCAN = 512
# SwitchLayerConfigV1.require_min_samples defaults to 60; needs len(returns) >= 60.
_MIN_MIDPOINTS = 61

_REPO_ROOT = Path(__file__).resolve().parents[3]


def _is_allowed_recorded_price_source_root(path: Path) -> bool:
    resolved = path.resolve()
    tmp_root = Path("/tmp").resolve()
    tempfile_root = Path(tempfile.gettempdir()).resolve()

    try:
        relative_to_tmp = resolved.relative_to(tmp_root)
    except ValueError:
        relative_to_tmp = None

    if relative_to_tmp is not None:
        if not relative_to_tmp.parts:
            return False
        top_segment = relative_to_tmp.parts[0].lower()
        return top_segment.startswith("peak_trade_") or top_segment.startswith("pytest")

    if tempfile_root == tmp_root:
        return False

    try:
        resolved.relative_to(tempfile_root)
    except ValueError:
        return False
    return True


def validate_recorded_price_source_path(path_str: str) -> Tuple[Optional[Path], Optional[str]]:
    trimmed = path_str.strip()
    if not trimmed:
        return None, "recorded price source path must be non-empty"
    if ".." in Path(trimmed).parts:
        return None, "recorded price source must not contain path traversal segments"

    probe = Path(trimmed).expanduser()
    if not probe.is_absolute():
        return None, "recorded price source must be an absolute path"
    try:
        resolved = probe.resolve(strict=True)
    except FileNotFoundError:
        return None, "recorded price source path does not exist"
    except (OSError, RuntimeError):
        return None, "recorded price source cannot be resolved safely"

    if not resolved.is_dir():
        return None, "recorded price source must be a directory"

    rr = _REPO_ROOT.resolve()
    if resolved == rr or resolved.is_relative_to(rr):
        return None, "recorded price source must not reside inside the repository tree"

    if ".git" in resolved.parts:
        return None, "recorded price source must not traverse a `.git` path segment"

    if not _is_allowed_recorded_price_source_root(resolved):
        return (
            None,
            "recorded price source must resolve under `/tmp` with a top-level segment starting "
            "with `peak_trade_` or `pytest`, or resolve under the process temporary directory "
            "(stdlib `tempfile`) when it is not the filesystem `/tmp`.",
        )

    return resolved, None


def _to_decimal(s: Any) -> Optional[Decimal]:
    if isinstance(s, (int, float)) and not isinstance(s, bool):
        try:
            return Decimal(str(s))
        except (InvalidOperation, ValueError, TypeError):
            return None
    if isinstance(s, str):
        try:
            return Decimal(s.strip())
        except (InvalidOperation, ValueError):
            return None
    return None


def _mid_from_mapping(obj: dict[str, Any]) -> Optional[float]:
    bp = obj.get("bidPrice")
    ap = obj.get("askPrice")
    if bp is not None and ap is not None:
        b = _to_decimal(bp)
        a = _to_decimal(ap)
        if b is None or a is None:
            return None
        if not b.is_finite() or not a.is_finite():
            raise ValueError("ERR: non-finite midpoint in recorded JSON")
        if b <= 0 or a <= 0 or a <= b:
            return None
        mid = (b + a) / Decimal("2")
        out = float(mid)
        if not math.isfinite(out):
            raise ValueError("ERR: non-finite midpoint in recorded JSON")
        return out

    bid = obj.get("bid")
    ask = obj.get("ask")
    if bid is not None and ask is not None:
        b = _to_decimal(bid)
        a = _to_decimal(ask)
        if b is None or a is None:
            return None
        if not b.is_finite() or not a.is_finite():
            raise ValueError("ERR: non-finite midpoint in recorded JSON")
        if b <= 0 or a <= 0 or a <= b:
            return None
        mid = (b + a) / Decimal("2")
        out = float(mid)
        if not math.isfinite(out):
            raise ValueError("ERR: non-finite midpoint in recorded JSON")
        return out

    return None


def _walk_collect_mids(obj: Any, mids: List[float]) -> None:
    if isinstance(obj, dict):
        mid = _mid_from_mapping(obj)
        if mid is not None:
            mids.append(mid)
            return
        for v in obj.values():
            _walk_collect_mids(v, mids)
    elif isinstance(obj, list):
        for item in obj:
            _walk_collect_mids(item, mids)


def _sorted_json_files(root: Path) -> List[Path]:
    paths = [p for p in root.rglob("*.json") if p.is_file()]
    paths.sort(key=lambda p: str(p))
    return paths[:MAX_JSON_FILES_SCAN]


def load_simple_returns_from_recorded_price_source(source_dir: Path) -> Tuple[List[float], int]:
    """Return (simple_returns, mid_count_used)."""
    files = _sorted_json_files(source_dir)
    if not files:
        raise ValueError("ERR: no JSON files found under recorded price source")

    mids: List[float] = []
    for fp in files:
        try:
            raw = fp.read_text(encoding="utf-8")
            data = json.loads(raw)
        except (OSError, json.JSONDecodeError) as e:
            raise ValueError(f"ERR: cannot read/parse JSON: {fp}: {e}") from e
        _walk_collect_mids(data, mids)

    if len(mids) < _MIN_MIDPOINTS:
        raise ValueError(
            f"ERR: need at least {_MIN_MIDPOINTS} bid/ask midpoints for returns series, "
            f"got {len(mids)}",
        )

    returns: List[float] = []
    for i in range(1, len(mids)):
        prev = mids[i - 1]
        cur = mids[i]
        if prev == 0.0:
            raise ValueError("ERR: zero midpoint in recorded series (division)")
        r = (cur / prev) - 1.0
        if not math.isfinite(r):
            raise ValueError("ERR: non-finite simple return in recorded series")
        returns.append(r)

    return returns, len(mids)
