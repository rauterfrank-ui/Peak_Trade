#!/usr/bin/env python3
import argparse
import os
import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def run(cmd: list[str], env: dict[str, str]) -> int:
    p = subprocess.run(cmd, env=env)
    return int(p.returncode)

def main() -> int:
    parser = argparse.ArgumentParser(
        prog="pipeline_cli.py",
        description="Unified pipeline CLI (offline-first): research / live_ops (no-live) / risk",
    )
    parser.add_argument("--run-id", default=None, help="Run id for evidence pack directory naming")
    parser.add_argument("--artifacts-dir", default=None, help="Artifacts base dir (forwarded before subcommand where supported)")
    parser.add_argument("--sandbox", action="store_true", help="Set PEAKTRADE_SANDBOX=1 for the subprocess")
    sub = parser.add_subparsers(dest="cmd", required=True)

    # research passthrough
    p_r = sub.add_parser("research", help="Delegate to scripts/research_cli.py")
    p_r.add_argument("args", nargs=argparse.REMAINDER, help="Args forwarded to research_cli.py (prefix with --)")

    # live ops passthrough (no-live)
    p_l = sub.add_parser("live_ops", help="Delegate to scripts/live_ops.py (NO-LIVE)")
    p_l.add_argument("args", nargs=argparse.REMAINDER, help="Args forwarded to live_ops.py (prefix with --)")

    # risk passthrough
    p_k = sub.add_parser("risk", help="Delegate to scripts/risk_cli.py")
    p_k.add_argument("args", nargs=argparse.REMAINDER, help="Args forwarded to risk_cli.py (prefix with --)")

    args = parser.parse_args()

    env = os.environ.copy()
    if args.sandbox:
        env["PEAKTRADE_SANDBOX"] = "1"

    run_id = args.run_id
    if run_id:
        env["PEAKTRADE_RUN_ID"] = run_id  # optional convention for downstream tools
    # Pass --run-id through explicitly where supported.
    if args.cmd == "research":
        cmd = [sys.executable, str(ROOT/"scripts"/"research_cli.py")]
        if run_id:
            cmd += ["--run-id", run_id]
        cmd += args.args
        return run(cmd, env)

    if args.cmd == "live_ops":
        cmd = [sys.executable, str(ROOT/"scripts"/"live_ops.py")]
        if run_id:
            cmd += ["--run-id", run_id]
        cmd += args.args
        return run(cmd, env)

    if args.cmd == "risk":
        cmd = [sys.executable, str(ROOT/"scripts"/"risk_cli.py")]
        if run_id:
            cmd += ["--run-id", run_id]
        if getattr(args, "artifacts_dir", None):
            cmd += ["--artifacts-dir", args.artifacts_dir]
        cmd += args.args
        return run(cmd, env)

    return 2

if __name__ == "__main__":
    raise SystemExit(main())
