#!/usr/bin/env python3
"""P7 — Paper Trading Operator CLI: reconcile | run-paper | run-shadow."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def root_dir() -> Path:
    return Path(__file__).resolve().parents[2]


def runpy(script: Path, *args: str) -> int:
    """Run a Python script via runpy; return exit code."""
    import runpy

    argv = [str(script), *args]
    sys.argv = argv
    try:
        runpy.run_path(str(script), run_name="__main__")
        return 0
    except SystemExit as e:
        return e.code if isinstance(e.code, int) else 1


def cmd_reconcile(args: argparse.Namespace) -> int:
    """Run P7 reconciliation checks on a shadow session outdir."""
    root = root_dir()
    recon = root / "scripts" / "aiops" / "run_p7_reconcile.py"
    if not recon.is_file():
        print(f"missing {recon}", file=sys.stderr)
        return 1
    outdir = (root / args.outdir).resolve() if not Path(args.outdir).is_absolute() else Path(args.outdir)
    cmd = [sys.executable, str(recon), str(outdir)]
    if args.spec:
        spec = (root / args.spec).resolve() if not Path(args.spec).is_absolute() else Path(args.spec)
        cmd.extend(["--spec", str(spec)])
    return subprocess.run(cmd, cwd=str(root)).returncode


def cmd_run_paper(args: argparse.Namespace) -> int:
    """Run paper trading session (standalone)."""
    root = root_dir()
    runner = root / "scripts" / "aiops" / "run_paper_trading_session.py"
    if not runner.is_file():
        print(f"missing {runner}", file=sys.stderr)
        return 1
    spec = (root / args.spec).resolve() if not Path(args.spec).is_absolute() else Path(args.spec)
    cmd = [sys.executable, str(runner), "--spec", str(spec)]
    if args.run_id:
        cmd.extend(["--run-id", str(args.run_id)])
    if args.outdir:
        outdir = (root / args.outdir).resolve() if not Path(args.outdir).is_absolute() else Path(args.outdir)
        cmd.extend(["--outdir", str(outdir)])
    cmd.extend(["--evidence", str(args.evidence)])
    return subprocess.run(cmd, cwd=str(root)).returncode


def cmd_run_shadow(args: argparse.Namespace) -> int:
    """Run shadow session with P7 enabled."""
    root = root_dir()
    runner = root / "scripts" / "aiops" / "run_shadow_session.py"
    if not runner.is_file():
        print(f"missing {runner}", file=sys.stderr)
        return 1
    spec = (root / args.spec).resolve() if not Path(args.spec).is_absolute() else Path(args.spec)
    outdir = (root / args.outdir).resolve() if not Path(args.outdir).is_absolute() else Path(args.outdir)
    cmd = [
        sys.executable,
        str(runner),
        "--spec",
        str(spec),
        "--run-id",
        str(args.run_id),
        "--outdir",
        str(outdir),
        "--p7-enable",
        "1",
        "--p7-evidence",
        str(args.p7_evidence),
    ]
    return subprocess.run(cmd, cwd=str(root)).returncode


def main() -> int:
    p = argparse.ArgumentParser(prog="p7_ctl", description="P7 Paper Trading Operator CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("reconcile", help="run P7 reconciliation checks on shadow outdir")
    sp.add_argument("outdir", type=str, help="Shadow session output dir")
    sp.add_argument("--spec", type=str, default="", help="P7 spec for expected vs actual")
    sp.set_defaults(func=cmd_reconcile)

    sp = sub.add_parser("run-paper", help="run paper trading session (standalone)")
    sp.add_argument("--spec", type=str, required=True, help="Paper run spec JSON")
    sp.add_argument("--run-id", type=str, default="", help="Deterministic run id")
    sp.add_argument("--outdir", type=str, default="", help="Override output dir")
    sp.add_argument("--evidence", type=int, default=1, help="Write evidence manifest (1 default)")
    sp.set_defaults(func=cmd_run_paper)

    sp = sub.add_parser("run-shadow", help="run shadow session with P7 enabled")
    sp.add_argument("--spec", type=str, required=True, help="Shadow session spec JSON")
    sp.add_argument("--run-id", type=str, default="p7_ctl", help="Run id")
    sp.add_argument("--outdir", type=str, required=True, help="Output dir")
    sp.add_argument("--p7-evidence", type=int, default=1, help="Write P7 evidence manifest")
    sp.set_defaults(func=cmd_run_shadow)

    args = p.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
