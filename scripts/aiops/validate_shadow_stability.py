#!/usr/bin/env python3
"""Validate shadow session stability: compare core artifacts across N runs.

Usage:
  python scripts/aiops/validate_shadow_stability.py --runs out/ops/shadow_runs --latest 3
  python scripts/aiops/validate_shadow_stability.py --runs out/ops/shadow_runs --latest 3 --artifact shadow_session_result.json
"""
import argparse
import hashlib
from pathlib import Path


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--runs",
        required=True,
        help="Path containing shadow runs (e.g. out/ops/shadow_runs)",
    )
    ap.add_argument(
        "--latest",
        type=int,
        default=3,
        help="How many most recent runs to compare",
    )
    ap.add_argument(
        "--artifact",
        default="shadow_session_result.json",
        help="Core artifact to compare",
    )
    args = ap.parse_args()

    runs_dir = Path(args.runs)
    if not runs_dir.exists():
        raise SystemExit(f"missing runs dir: {runs_dir}")

    run_dirs = sorted(
        [p for p in runs_dir.iterdir() if p.is_dir()], key=lambda p: p.name
    )
    if len(run_dirs) < args.latest:
        raise SystemExit(f"need >= {args.latest} runs, found {len(run_dirs)}")

    pick = run_dirs[-args.latest:]
    targets = []
    for d in pick:
        f = d / args.artifact
        if not f.exists():
            raise SystemExit(f"missing artifact in run {d.name}: {f}")
        targets.append(f)

    hashes = [sha256_file(t) for t in targets]
    ok = all(h == hashes[0] for h in hashes)
    if not ok:
        pairs = "\n".join([f"{t}: {h}" for t, h in zip(targets, hashes)])
        raise SystemExit(f"SHADOW_STABILITY_FAIL\n{pairs}")

    print("SHADOW_STABILITY_OK")
    for t, h in zip(targets, hashes):
        print(f"{t} {h}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
