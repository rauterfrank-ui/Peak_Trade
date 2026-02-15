from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.ops.common import to_jsonable_v1
from src.ops.p61 import P61RunContextV1, run_online_readiness_v1


@dataclass(frozen=True)
class P62RunContextV1:
    """Context for P62 shadow session (paper/shadow only)."""

    mode: str  # "paper" | "shadow"
    run_id: str
    out_dir: Optional[Path] = None
    allow_bull_strategies: Optional[List[str]] = None
    allow_bear_strategies: Optional[List[str]] = None


def _derive_shadow_plan(p61_out: Dict[str, Any], ctx: P62RunContextV1) -> Dict[str, Any]:
    """Derive deterministic shadow session plan from P61 output."""
    routing = p61_out.get("switch", {}).get("routing", {})
    ai_mode = routing.get("ai_mode", "disabled")
    allowed_strategies = routing.get("allowed_strategies", [])
    reason = routing.get("reason", "deny_by_default")

    return {
        "ai_mode": ai_mode,
        "allowed_strategies": allowed_strategies,
        "rationale": reason,
        "run_id": ctx.run_id,
        "mode": ctx.mode,
        "note": "Shadow session plan — no execution. Deny-by-default preserved.",
    }


def _write_evidence_pack(out_dir: Path, out: Dict[str, Any], run_id: str) -> None:
    """Write P62 evidence pack (json-only boundary)."""
    out_dir = Path(out_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    meta = {"run_id": run_id, "ts_utc": ts, "version": "p62_evidence_pack_v1"}

    def _write(path: Path, data: Any) -> None:
        path.write_text(
            json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    _write(out_dir / "meta.json", meta)
    _write(out_dir / "readiness_report.json", out.get("report", {}))
    _write(out_dir / "shadow_plan.json", out.get("shadow_plan", {}))
    _write(out_dir / "switch.json", out.get("switch", {}))
    _write(
        out_dir / "manifest.json",
        {
            "version": "p62_evidence_pack_v1",
            "run_id": run_id,
            "files": ["meta.json", "readiness_report.json", "shadow_plan.json", "switch.json"],
        },
    )


def run_online_readiness_shadow_session_v1(
    prices: List[float], ctx: P62RunContextV1
) -> Dict[str, Any]:
    """
    Run P61 readiness, derive shadow session plan, optionally write evidence.

    - PermissionError for mode in {live, record}
    - No execution, no exchange connectivity
    - Evidence written only when out_dir is set
    """
    if ctx.mode in ("live", "record"):
        raise PermissionError(f"P62 only supports paper/shadow. mode={ctx.mode}")

    p61_ctx = P61RunContextV1(
        mode=ctx.mode,
        run_id=ctx.run_id,
        out_dir=ctx.out_dir,
        allow_bull_strategies=ctx.allow_bull_strategies or [],
        allow_bear_strategies=ctx.allow_bear_strategies or [],
    )
    p61_out = run_online_readiness_v1(prices, p61_ctx)

    shadow_plan = _derive_shadow_plan(p61_out, ctx)

    out = {
        "report": p61_out.get("report", {}),
        "switch": p61_out.get("switch", {}),
        "shadow_plan": shadow_plan,
        "meta": {
            "p62_run_id": ctx.run_id,
            "mode": ctx.mode,
            "evidence_written": bool(ctx.out_dir),
        },
    }

    if ctx.out_dir is not None:
        _write_evidence_pack(ctx.out_dir, out, ctx.run_id)

    return to_jsonable_v1(out)
