"""P115: Execution session runner v1 (mocks-only)."""

from __future__ import annotations

import json
import os
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, List

from src.execution.adapters.base_v1 import OrderIntentV1
from src.execution.router.router_v1 import (
    ExecutionRouterContextV1,
    build_execution_router_v1,
)


@dataclass(frozen=True)
class ExecutionSessionContextV1:
    mode: str = "shadow"
    dry_run: bool = True
    out_base: str = "out/ops/execution_sessions"
    ts_utc: str | None = None

    adapters: tuple[str, ...] = ("mock", "coinbase", "okx", "bybit")
    intents: tuple[str, ...] = ("place_order", "cancel_all")

    market: str = "BTC-USD"
    side: str = "buy"
    qty: float = 0.01

    deny_vars: tuple[str, ...] = (
        "LIVE",
        "RECORD",
        "TRADING_ENABLE",
        "EXECUTION_ENABLE",
        "PT_ARMED",
        "PT_CONFIRM",
        "PT_CONFIRM_MERGE",
        "PT_LIVE",
        "PT_TRADE",
    )
    secret_vars: tuple[str, ...] = (
        "API_KEY",
        "KRAKEN_API_KEY",
        "BINANCE_API_KEY",
        "COINBASE_API_KEY",
        "OKX_API_KEY",
        "BYBIT_API_KEY",
        "API_SECRET",
        "KRAKEN_API_SECRET",
        "BINANCE_API_SECRET",
        "COINBASE_API_SECRET",
        "OKX_API_SECRET",
        "BYBIT_API_SECRET",
    )


def _utc_ts() -> str:
    return time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())


def _repo_root() -> Path:
    try:
        out = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
        return Path(out)
    except Exception:
        return Path.cwd()


def _shasum_file(path: Path) -> str:
    out = subprocess.check_output(["shasum", "-a", "256", str(path)], text=True).strip()
    return out.split()[0]


def _write_sha256sums(evi_dir: Path, rel_files: List[str]) -> None:
    lines = []
    for rel in rel_files:
        p = evi_dir / rel
        h = _shasum_file(p)
        lines.append(f"{h}  {rel}")
    (evi_dir / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _bundle_dir(evi_dir: Path) -> Path:
    parent = evi_dir.parent
    bundle = parent / f"{evi_dir.name}.bundle.tgz"
    subprocess.check_call(["tar", "-C", str(parent), "-czf", str(bundle), evi_dir.name])
    sha = _shasum_file(bundle)
    (bundle.with_suffix(bundle.suffix + ".sha256")).write_text(
        f"{sha}  {bundle.name}\n", encoding="utf-8"
    )
    return bundle


def _pin(repo_root: Path, evi_dir: Path, bundle: Path, ts: str) -> Path:
    pin_dir = repo_root / "out" / "ops"
    pin_dir.mkdir(parents=True, exist_ok=True)
    pin = pin_dir / f"EXECUTION_SESSION_DONE_{ts}.txt"
    main_head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()

    content = "\n".join(
        [
            "EXECUTION_SESSION_DONE OK",
            f"timestamp_utc={ts}",
            f"main_head={main_head}",
            f"evi={evi_dir}",
            f"bundle={bundle}",
            f"bundle_sha256={_shasum_file(bundle)}",
            "",
        ]
    )
    pin.write_text(content, encoding="utf-8")
    sha = _shasum_file(pin)
    (pin.with_suffix(".txt.sha256")).write_text(f"{sha}  {pin.name}\n", encoding="utf-8")
    return pin


def _guard(ctx: ExecutionSessionContextV1) -> None:
    if ctx.mode not in ("shadow", "paper"):
        raise SystemExit("P115_GUARD_FAIL: invalid_mode")
    if ctx.dry_run is not True:
        raise SystemExit("P115_GUARD_FAIL: dry_run_must_be_true")
    for k in ctx.deny_vars:
        if os.environ.get(k):
            raise SystemExit(f"P115_GUARD_FAIL: deny_var_set {k}")
    for k in ctx.secret_vars:
        if os.environ.get(k):
            raise SystemExit(f"P115_GUARD_FAIL: secret_var_set {k}")


def run_execution_session_v1(ctx: ExecutionSessionContextV1) -> dict[str, Any]:
    _guard(ctx)
    repo_root = _repo_root()
    ts = ctx.ts_utc or _utc_ts()

    out_base = Path(ctx.out_base)
    evi_dir = (
        (out_base / f"run_{ts}")
        if out_base.is_absolute()
        else (repo_root / ctx.out_base / f"run_{ts}")
    )
    evi_dir.mkdir(parents=True, exist_ok=True)

    steps: List[dict[str, Any]] = []
    ok = True

    for adapter_name in ctx.adapters:
        router_ctx = ExecutionRouterContextV1(
            mode=ctx.mode,
            adapter_name=adapter_name,
            dry_run=ctx.dry_run,
        )
        router = build_execution_router_v1(router_ctx)

        for intent in ctx.intents:
            try:
                if intent == "place_order":
                    intent_obj = OrderIntentV1(
                        symbol=ctx.market,
                        side=ctx.side,
                        qty=ctx.qty,
                        order_type="market",
                        client_id=f"p115_{adapter_name}_{ts}",
                    )
                    res = router.place_order(intent_obj)
                    steps.append(
                        {
                            "adapter": adapter_name,
                            "intent": intent,
                            "ok": bool(res.ok),
                            "message": res.message,
                        }
                    )
                    ok = ok and bool(res.ok)
                elif intent == "cancel_all":
                    n = router.cancel_all(symbol=None)
                    steps.append(
                        {
                            "adapter": adapter_name,
                            "intent": intent,
                            "ok": True,
                            "canceled": int(n),
                        }
                    )
                else:
                    steps.append(
                        {
                            "adapter": adapter_name,
                            "intent": intent,
                            "ok": False,
                            "message": "unknown_intent",
                        }
                    )
                    ok = False
            except Exception as e:
                steps.append(
                    {
                        "adapter": adapter_name,
                        "intent": intent,
                        "ok": False,
                        "error": repr(e),
                    }
                )
                ok = False

    report = {
        "meta": {"ok": ok, "mode": ctx.mode, "dry_run": ctx.dry_run, "ts_utc": ts},
        "steps": steps,
    }

    (evi_dir / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    manifest = {"files": ["report.json"]}
    (evi_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    _write_sha256sums(evi_dir, ["report.json", "manifest.json"])

    bundle = _bundle_dir(evi_dir)
    pin = _pin(repo_root, evi_dir, bundle, ts)

    return {
        "ok": ok,
        "ts_utc": ts,
        "evi_dir": str(evi_dir),
        "bundle": str(bundle),
        "pin": str(pin),
    }
