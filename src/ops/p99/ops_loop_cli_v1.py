from __future__ import annotations

import argparse
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from src.ops.p98 import P98OpsLoopContextV1, run_ops_loop_orchestrator_v1


def _utc_ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _write_text(p: Path, s: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(s, encoding="utf-8")


def _sha256_file(p: Path) -> str:
    out = subprocess.check_output(["shasum", "-a", "256", str(p)], text=True).split()[0]
    return out


def _build_sha256sums_txt(evi: Path) -> None:
    files = sorted(evi.rglob("*"), key=lambda x: str(x))
    lines = []
    for f in files:
        if f.is_file() and f.name != "SHA256SUMS.txt":
            rel = f.relative_to(evi)
            sha = subprocess.check_output(["shasum", "-a", "256", str(f)], text=True).split()[0]
            lines.append(f"{sha}  {rel}\n")
    _write_text(evi / "SHA256SUMS.txt", "".join(lines))


def _bundle_dir(evi: Path) -> Path:
    root = _repo_root()
    bundle = evi.parent / f"{evi.name}.bundle.tgz"
    try:
        rel = evi.relative_to(root)
        subprocess.check_call(
            ["tar", "-czf", str(bundle), str(rel)],
            cwd=str(root),
        )
    except ValueError:
        subprocess.check_call(
            ["tar", "-czf", str(bundle), "-C", str(evi.parent), evi.name],
        )
    _write_text(
        Path(str(bundle) + ".sha256"),
        _sha256_file(bundle) + "  " + str(bundle) + "\n",
    )
    return bundle


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="p99_ops_loop_cli_v1", add_help=True)
    ap.add_argument("--mode", default=os.environ.get("MODE", "shadow"))
    ap.add_argument(
        "--max-age-sec",
        type=int,
        default=int(os.environ.get("MAX_AGE_SEC", "900")),
    )
    ap.add_argument(
        "--min-ticks",
        type=int,
        default=int(os.environ.get("MIN_TICKS", "2")),
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        default=(os.environ.get("DRY_RUN") == "YES"),
    )
    ap.add_argument("--out-dir", default=os.environ.get("OUT_DIR"))
    ap.add_argument("--evi", default=os.environ.get("EVI_OVERRIDE"))
    ap.add_argument("--ts", default=os.environ.get("TS_OVERRIDE"))
    ap.add_argument(
        "--out-ops",
        default=os.environ.get("OUT_OPS_OVERRIDE"),
        help="Override base dir for pins (e.g. for tests)",
    )
    args = ap.parse_args(argv)

    if args.mode not in ("paper", "shadow"):
        raise SystemExit("mode must be paper|shadow (live/record not supported)")

    ts = args.ts or _utc_ts()
    root = _repo_root()
    evi = Path(args.evi) if args.evi else (root / "out" / "ops" / f"p99_ops_loop_run_{ts}")
    out_dir = Path(args.out_dir) if args.out_dir else None
    out_ops = Path(args.out_ops) if args.out_ops else (root / "out" / "ops")

    ctx = P98OpsLoopContextV1(
        out_dir=out_dir,
        mode=args.mode,
        max_age_sec=args.max_age_sec,
        min_ticks=args.min_ticks,
        dry_run=args.dry_run,
    )
    report = run_ops_loop_orchestrator_v1(ctx)

    # Evidence pack (json + manifest + sha256 + bundle + pin)
    _write_text(evi / "report.json", json.dumps(report, indent=2, sort_keys=True) + "\n")
    _write_text(
        evi / "manifest.json",
        json.dumps({"files": ["report.json"]}, indent=2) + "\n",
    )
    _build_sha256sums_txt(evi)
    bundle = _bundle_dir(evi)

    main_head = subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=str(root),
        text=True,
    ).strip()
    pin = out_ops / f"P99_OPS_LOOP_DONE_{ts}.txt"
    pin_body = (
        "P99_OPS_LOOP_DONE OK\n"
        f"timestamp_utc={ts}\n"
        f"main_head={main_head}\n"
        f"evi={evi}\n"
        f"bundle={bundle}\n"
        f"bundle_sha256={_sha256_file(bundle)}\n"
    )
    _write_text(pin, pin_body)
    _write_text(
        Path(str(pin) + ".sha256"),
        _sha256_file(pin) + "  " + str(pin) + "\n",
    )

    print(f"P99_OK evi={evi} pin={pin}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
