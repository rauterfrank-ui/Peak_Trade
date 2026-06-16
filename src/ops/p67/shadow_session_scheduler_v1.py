from __future__ import annotations

import json
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal, Mapping, Optional

from src.ops.common import to_jsonable_v1
from src.ops.p66.run_online_readiness_operator_entrypoint_v1 import (
    P66RunContextV1,
    run_online_readiness_operator_entrypoint_v1,
)
from .recorded_price_series_v0 import (
    load_simple_returns_from_recorded_price_source,
    validate_recorded_price_source_path,
)

ModeV1 = Literal["paper", "shadow"]

# Default prices for P66 (deterministic shadow/paper run)
_DEFAULT_PRICES: list[float] = [0.001] * 200


@dataclass(frozen=True)
class P67RunContextV1:
    mode: ModeV1 = "shadow"
    run_id: str = "p67"
    out_dir: Optional[Path] = None
    iterations: int = 1
    interval_seconds: float = 60.0
    recorded_price_source: Optional[Path] = None
    primary_evidence_enforce: bool = False
    scheduler_boundary_enforce: bool = False
    scheduler_preflight_status: Optional[Mapping[str, Any]] = None


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _maybe_assert_scheduler_boundary(ctx: P67RunContextV1) -> None:
    if not ctx.scheduler_boundary_enforce:
        return
    repo_root = _repo_root()
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    from scripts.ops.scheduler_start_boundary_guard_v0 import assert_scheduler_start_authorized

    assert_scheduler_start_authorized(
        preflight_status=ctx.scheduler_preflight_status,
        repo_root=repo_root if ctx.scheduler_preflight_status is None else None,
    )


def _maybe_finalize_primary_evidence(ctx: P67RunContextV1) -> None:
    if not ctx.primary_evidence_enforce:
        return
    if ctx.out_dir is None:
        raise RuntimeError("ERR: primary_evidence_enforce requires out_dir (non-authorizing §2a)")
    root = ctx.out_dir / f"p67_shadow_session_{ctx.run_id}"
    if not root.is_dir():
        raise RuntimeError(f"ERR: primary evidence root missing: {root}")
    repo_root = _repo_root()
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    from scripts.ops.primary_evidence_retention_v0 import finalize_primary_evidence_root

    ok, msg = finalize_primary_evidence_root(root)
    if not ok:
        raise RuntimeError(f"ERR: primary evidence finalize failed: {msg}")


def _utc_ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_shadow_session_scheduler_v1(ctx: P67RunContextV1) -> dict:
    """
    Safe-by-default scheduler:
    - only paper/shadow (deny live/record by construction)
    - runs P66 operator entrypoint N times with sleep interval
    - optional evidence write if ctx.out_dir set
    Returns dict-only boundary (jsonable).
    """
    _maybe_assert_scheduler_boundary(ctx)
    if ctx.mode not in ("paper", "shadow"):
        raise PermissionError(f"ERR: P67 only supports paper/shadow, got mode={ctx.mode!r}")
    if ctx.iterations < 1:
        raise ValueError("ERR: iterations must be >= 1")
    if ctx.interval_seconds < 0:
        raise ValueError("ERR: interval_seconds must be >= 0")

    recorded_price_source_used = False
    recorded_price_source_path: Optional[str] = None
    recorded_price_series_count: Optional[int] = None

    if ctx.recorded_price_source is not None:
        src_resolved, src_err = validate_recorded_price_source_path(str(ctx.recorded_price_source))
        if src_err or src_resolved is None:
            raise ValueError(src_err or "recorded price source validation failed")
        price_series, _mid_count = load_simple_returns_from_recorded_price_source(src_resolved)
        recorded_price_source_used = True
        recorded_price_source_path = str(src_resolved)
        recorded_price_series_count = len(price_series)
    else:
        price_series = list(_DEFAULT_PRICES)

    events: list[dict] = []
    base_out_dir = ctx.out_dir
    scheduler_meta = {
        "version": "p67_shadow_session_scheduler_v1",
        "run_id": ctx.run_id,
        "mode": ctx.mode,
        "iterations": ctx.iterations,
        "interval_seconds": ctx.interval_seconds,
        "ts_utc_start": _utc_ts(),
        "recorded_price_source_used": recorded_price_source_used,
        "recorded_price_source_path": recorded_price_source_path,
        "recorded_price_series_count": recorded_price_series_count,
    }

    for i in range(ctx.iterations):
        iter_ts = _utc_ts()
        iter_run_id = f"{ctx.run_id}_iter{i + 1:03d}_{iter_ts}"

        iter_out_dir = (
            (base_out_dir / f"p67_shadow_session_{iter_run_id}") if base_out_dir else None
        )
        p66_ctx = P66RunContextV1(
            mode=ctx.mode,
            run_id=iter_run_id,
            out_dir=iter_out_dir,
            loop=False,
            iterations=1,
            sleep_seconds=0.0,
        )
        out = run_online_readiness_operator_entrypoint_v1(price_series, p66_ctx)
        out_jsonable = to_jsonable_v1(out)

        event = {
            "i": i + 1,
            "iter_run_id": iter_run_id,
            "ts_utc": iter_ts,
            "p66": out_jsonable,
        }
        events.append(event)

        # optional scheduler-level evidence
        if base_out_dir:
            root = base_out_dir / f"p67_shadow_session_{ctx.run_id}"
            _write_json(root / "meta.json", scheduler_meta)
            _write_json(root / "events.json", events)
            _write_json(
                root / "manifest.json",
                {
                    "version": "p67_manifest_v1",
                    "run_id": ctx.run_id,
                    "files": ["meta.json", "events.json"],
                },
            )

        # sleep between iterations (not after last)
        if i + 1 < ctx.iterations and ctx.interval_seconds > 0:
            time.sleep(ctx.interval_seconds)

    scheduler_meta["ts_utc_end"] = _utc_ts()
    _maybe_finalize_primary_evidence(ctx)
    res = {"meta": scheduler_meta, "events": events}
    return to_jsonable_v1(res)
