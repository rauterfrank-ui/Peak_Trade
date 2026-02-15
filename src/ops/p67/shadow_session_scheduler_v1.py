from __future__ import annotations

import json
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal, Optional

from src.ops.common import to_jsonable_v1
from src.ops.p66.run_online_readiness_operator_entrypoint_v1 import (
    P66RunContextV1,
    run_online_readiness_operator_entrypoint_v1,
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
    if ctx.mode not in ("paper", "shadow"):
        raise PermissionError(f"ERR: P67 only supports paper/shadow, got mode={ctx.mode!r}")
    if ctx.iterations < 1:
        raise ValueError("ERR: iterations must be >= 1")
    if ctx.interval_seconds < 0:
        raise ValueError("ERR: interval_seconds must be >= 0")

    events: list[dict] = []
    base_out_dir = ctx.out_dir
    scheduler_meta = {
        "version": "p67_shadow_session_scheduler_v1",
        "run_id": ctx.run_id,
        "mode": ctx.mode,
        "iterations": ctx.iterations,
        "interval_seconds": ctx.interval_seconds,
        "ts_utc_start": _utc_ts(),
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
        out = run_online_readiness_operator_entrypoint_v1(_DEFAULT_PRICES, p66_ctx)
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
    res = {"meta": scheduler_meta, "events": events}
    return to_jsonable_v1(res)
