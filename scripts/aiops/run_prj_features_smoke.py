from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict

_repo_root = Path(__file__).resolve().parents[2]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from src.live.operator_context import OperatorWiringInput, build_live_context_from_operator


def _b(name: str, default: bool = False) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return v.lower() in ("1", "true", "yes", "y", "on")


def _f(name: str, default: float) -> float:
    v = os.getenv(name)
    if v is None:
        return default
    return float(v)


def _run(cmd: list[str]) -> None:
    subprocess.check_call(cmd)


def main() -> int:
    os.chdir(_repo_root)

    run_id = (
        os.getenv("PT_RUN_ID", "").strip()
        or subprocess.check_output(
            [
                "python3",
                "-c",
                "import datetime;print(datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ'))",
            ]
        )
        .decode()
        .strip()
    )

    out_base = Path("out/ops/prj_smoke") / run_id
    shadow_out = out_base / "shadow"
    paper_out = out_base / "paper"
    out_base.mkdir(parents=True, exist_ok=True)

    # Operator wiring -> context (feature flags)
    switch_score = _f("PT_SWITCH_SCORE", -1.0)
    strength = _f("PT_STRENGTH", 1.0)

    inp = OperatorWiringInput(
        enabled=_b("PT_ENABLED", False),
        armed=_b("PT_ARMED", False),
        confirm_token_present=_b("PT_CONFIRM_PRESENT", False),
        allow_double_play=_b("PT_ALLOW_DOUBLE_PLAY", False),
        allow_dynamic_leverage=_b("PT_ALLOW_DYNAMIC_LEVERAGE", False),
        strength=strength,
        switch_gate={
            "score": switch_score,
            "state": {"active": "bull", "hold_remaining": 0, "cooldown_remaining": 0},
            "cfg": {"hysteresis": 0.1, "min_hold_steps": 3, "cooldown_steps": 3},
        },
        dynamic_leverage_cfg={"min_leverage": 1.0, "max_leverage": 50.0, "gamma": 2.0},
    )
    ctx = build_live_context_from_operator(inp=inp)

    # Write context for auditability (artifact)
    (out_base / "operator_context.json").write_text(
        json.dumps(ctx, indent=2, sort_keys=True), encoding="utf-8"
    )

    # Run shadow session (fixture spec) — p7_enable=0 to avoid duplicate paper run
    shadow_spec = Path("tests/fixtures/p6/shadow_session_min_v0.json")
    shadow_out.mkdir(parents=True, exist_ok=True)
    _run(
        [
            "python3",
            "scripts/aiops/run_shadow_session.py",
            "--spec",
            str(shadow_spec),
            "--outdir",
            str(shadow_out),
            "--run-id",
            run_id,
            "--evidence",
            "1",
            "--dry-run",
            "--p7-enable",
            "0",
        ]
    )

    # Run paper session (fixture spec)
    paper_spec = Path("tests/fixtures/p7/paper_run_min_v0.json")
    paper_out.mkdir(parents=True, exist_ok=True)
    _run(
        [
            "python3",
            "scripts/aiops/run_paper_trading_session.py",
            "--spec",
            str(paper_spec),
            "--outdir",
            str(paper_out),
            "--run-id",
            run_id,
            "--evidence",
            "1",
        ]
    )

    # Produce compact summary (artifact)
    summary: Dict[str, Any] = {
        "run_id": run_id,
        "features": ctx.get("_features_activation_details", {}),
        "double_play_enabled": bool(ctx.get("double_play_enabled", False)),
        "dynamic_leverage_enabled": bool(ctx.get("dynamic_leverage_enabled", False)),
        "strength": strength,
        "switch_score": switch_score,
        "outputs": {
            "shadow_dir": str(shadow_out),
            "paper_dir": str(paper_out),
            "operator_context": str(out_base / "operator_context.json"),
        },
    }
    (out_base / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8"
    )

    print(str(out_base))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
