"""P86 — Combined online readiness + ingest gate (paper/shadow only)."""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.ops.common import to_jsonable_v1
from src.ops.p85.run_live_data_ingest_readiness_v1 import (
    P85ContextV1,
    run_live_data_ingest_readiness_v1,
)


@dataclass(frozen=True)
class P86RunContextV1:
    mode: str  # "paper" | "shadow"
    run_id: str
    out_dir: Path | None = None
    allow_bull_strategies: list[str] | None = None
    allow_bear_strategies: list[str] | None = None

    def validate(self) -> None:
        if self.mode not in ("paper", "shadow"):
            raise PermissionError(f"p86: mode_not_allowed: {self.mode}")
        if self.out_dir is None:
            raise ValueError("p86: out_dir required")
        s = str(self.out_dir)
        if not s.startswith("out/ops") and "out/ops" not in s:
            raise ValueError("p86: out_dir must be under out/ops/ (safety)")
        if not self.run_id:
            raise ValueError("p86: run_id required")


def _ensure_outdir(out_dir: Path | None) -> None:
    if out_dir is None:
        return
    out_dir.mkdir(parents=True, exist_ok=True)


def _run_p76_shell(ctx: P86RunContextV1) -> dict[str, Any]:
    """Invoke P76 go/no-go shell script."""
    if ctx.out_dir is None:
        return {"ready": False, "error": "no_out_dir"}
    p76_dir = ctx.out_dir / "p76"
    p76_dir.mkdir(parents=True, exist_ok=True)
    env = {
        "MODE": ctx.mode,
        "RUN_ID": f"{ctx.run_id}_p76",
        "OUT_DIR": str(p76_dir),
        "ITERATIONS": "1",
        "INTERVAL": "0",
    }
    try:
        r = subprocess.run(
            ["bash", "scripts/ops/online_readiness_go_no_go_v1.sh"],
            env={**__import__("os").environ, **env},
            capture_output=True,
            text=True,
            timeout=120,
            cwd=Path(__file__).resolve().parents[3],
        )
        ready = r.returncode == 0 and "P76_READY" in (r.stdout or "")
        return {
            "ready": ready,
            "returncode": r.returncode,
            "stdout": (r.stdout or "")[:500],
            "stderr": (r.stderr or "")[:500],
        }
    except Exception as e:
        return {"ready": False, "error": str(e)}


def run_online_readiness_plus_ingest_gate_v1(ctx: P86RunContextV1) -> dict[str, Any]:
    """
    Combined gate (paper/shadow only):
      - P85 live data ingest readiness
      - P76 go/no-go (P71->P72 chain via shell)
    """
    ctx.validate()
    _ensure_outdir(ctx.out_dir)

    # P85
    p85_out = str(ctx.out_dir / "p85") if ctx.out_dir else ""
    p85_ctx = P85ContextV1(
        mode=ctx.mode,
        run_id=f"{ctx.run_id}_p85",
        out_dir=p85_out,
    )
    p85 = run_live_data_ingest_readiness_v1(p85_ctx)

    # P76 (shell)
    p76 = _run_p76_shell(ctx)

    p85_ok = bool(p85.get("overall_ok", False))
    p76_ready = bool(p76.get("ready", False))
    overall_ok = p85_ok and p76_ready

    out: dict[str, Any] = {
        "meta": {"p86_run_id": ctx.run_id, "mode": ctx.mode},
        "overall_ok": overall_ok,
        "p85": p85,
        "p76": p76,
        "reasons": [],
    }
    if not p85_ok:
        out["reasons"].append("p85_not_ok")
    if not p76_ready:
        out["reasons"].append("p76_not_ready")

    if ctx.out_dir is not None:
        result = to_jsonable_v1(out)
        (ctx.out_dir / "P86_GATE_RESULT.json").write_text(
            json.dumps(result, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        (ctx.out_dir / "p86_result.json").write_text(
            json.dumps(result, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        manifest = {
            "version": "p86_plus_ingest_gate_v1",
            "run_id": ctx.run_id,
            "files": ["p86_result.json", "P86_GATE_RESULT.json"],
            "subdirs": ["p85", "p76"],
        }
        (ctx.out_dir / "manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True),
            encoding="utf-8",
        )

    return to_jsonable_v1(out)
