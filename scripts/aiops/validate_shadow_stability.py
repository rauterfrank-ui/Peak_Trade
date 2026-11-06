#!/usr/bin/env python3
"""Validate shadow session stability: compare core artifacts across N runs.

Compares normalized content (volatile fields like run_id, asof_utc, paths are
redacted) so deterministic runs produce identical hashes.

Usage:
  python scripts/aiops/validate_shadow_stability.py --runs out/ops/shadow_runs --latest 3
  python scripts/aiops/validate_shadow_stability.py --runs out/ops/shadow_runs --latest 3 --artifact shadow_session_summary.json
"""

import argparse
import copy
import hashlib
import json
from pathlib import Path

VOLATILE_TOP_LEVEL_KEYS = {
    "run_id",
    "asof_utc",
    "created_utc",
    "updated_utc",
    "generated_utc",
}

VOLATILE_KEY_SUBSTRINGS = (
    "timestamp",
    "_ts",
    "_utc",
    "time_",
    "created",
    "updated",
)


def _strip_volatile(obj):
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if k in VOLATILE_TOP_LEVEL_KEYS:
                continue
            if any(sub in k for sub in VOLATILE_KEY_SUBSTRINGS):
                continue
            out[k] = _strip_volatile(v)
        return out
    if isinstance(obj, list):
        return [_strip_volatile(x) for x in obj]
    if isinstance(obj, str) and ("/" in obj or obj.startswith("/")):
        return "<path>"
    return obj


def _canonicalize_shadow_summary(payload: dict) -> dict:
    # Deep-strip volatile fields but keep semantics
    return _strip_volatile(copy.deepcopy(payload))


def _sha256_json_canonical(payload: dict) -> str:
    b = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )
    return hashlib.sha256(b).hexdigest()


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
        default="shadow_session_summary.json",
        help="Core artifact to compare (default: shadow_session_summary.json)",
    )
    args = ap.parse_args()

    runs_dir = Path(args.runs)
    if not runs_dir.exists():
        raise SystemExit(f"missing runs dir: {runs_dir}")

    run_dirs = sorted([p for p in runs_dir.iterdir() if p.is_dir()], key=lambda p: p.name)
    if len(run_dirs) < args.latest:
        raise SystemExit(f"need >= {args.latest} runs, found {len(run_dirs)}")

    pick = run_dirs[-args.latest :]
    targets = []
    for d in pick:
        f = d / args.artifact
        if not f.exists():
            raise SystemExit(f"missing artifact in run {d.name}: {f}")
        targets.append(f)

    # Use canonical JSON hash for shadow_session_summary.json (strips volatile keys + paths)
    use_canonical = args.artifact == "shadow_session_summary.json"
    hashes = []
    for t in targets:
        if use_canonical:
            payload = json.loads(t.read_text(encoding="utf-8"))
            canon = _canonicalize_shadow_summary(payload)
            hashes.append(_sha256_json_canonical(canon))
        else:
            hashes.append(sha256_file(t))
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
