from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from src.ops.common import to_jsonable_v1
from src.ops.p64 import P64RunContextV1, run_online_readiness_runner_v1


@dataclass(frozen=True)
class P71GateContextV1:
    mode: str  # paper|shadow only
    run_id: str
    out_dir: Optional[Path] = None
    allow_bull_strategies: Optional[list[str]] = None
    allow_bear_strategies: Optional[list[str]] = None


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_online_readiness_health_gate_v1(
    prices: list[float],
    ctx: P71GateContextV1,
) -> Dict[str, Any]:
    if ctx.mode not in ("paper", "shadow"):
        raise PermissionError("P71: only paper/shadow allowed (live/record hard-blocked)")

    p64_ctx = P64RunContextV1(
        mode=ctx.mode,
        run_id=ctx.run_id,
        out_dir=ctx.out_dir,
        allow_bull_strategies=ctx.allow_bull_strategies,
        allow_bear_strategies=ctx.allow_bear_strategies,
    )

    out = run_online_readiness_runner_v1(prices, p64_ctx)
    out = to_jsonable_v1(out)

    switch = out.get("p63", {}).get("switch", {})
    routing = switch.get("routing", {})
    ai_mode = routing.get("ai_mode", "disabled")
    allowed = routing.get("allowed_strategies", [])
    if isinstance(allowed, tuple):
        allowed = list(allowed)
    regime = switch.get("regime")
    if hasattr(regime, "value"):
        regime = regime.value

    checks: list[dict[str, Any]] = []

    checks.append(
        {
            "id": "mode_paper_shadow_only",
            "ok": ctx.mode in ("paper", "shadow"),
            "detail": {"mode": ctx.mode},
        }
    )
    checks.append(
        {
            "id": "ai_mode_never_live_record",
            "ok": ai_mode in ("disabled", "shadow"),
            "detail": {"ai_mode": ai_mode},
        }
    )
    checks.append(
        {
            "id": "deny_by_default_or_allowlist",
            "ok": (ai_mode == "disabled" and len(allowed) == 0)
            or (ai_mode == "shadow" and len(allowed) > 0),
            "detail": {"ai_mode": ai_mode, "allowed_strategies": allowed},
        }
    )

    ok = all(c["ok"] for c in checks)
    report = {
        "meta": {
            "p71_version": "v1",
            "run_id": ctx.run_id,
            "mode": ctx.mode,
        },
        "checks": checks,
        "overall_ok": ok,
        "regime": regime,
        "routing": routing,
        "p64": out,
    }

    if ctx.out_dir:
        out_dir = Path(ctx.out_dir)
        _write_json(out_dir / "p71_health_gate_report.json", report)
        _write_json(
            out_dir / "p71_health_gate_manifest.json",
            {
                "files": ["p71_health_gate_report.json"],
                "run_id": ctx.run_id,
                "version": "p71_gate_v1",
            },
        )

    return report
