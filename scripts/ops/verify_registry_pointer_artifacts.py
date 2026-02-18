#!/usr/bin/env python3
"""Portable verifier: reads pointer, validates telemetry invariants (download optional)."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple

FALLBACK_CODE = "AUDIT_MANIFEST_NO_DECISION_CONTEXT"
VALID_ACTIONS = {"ALLOW", "NO_TRADE"}


def parse_pointer(path: Path) -> Dict[str, str]:
    d: Dict[str, str] = {}
    for ln in path.read_text(encoding="utf-8").splitlines():
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        if "=" in ln:
            k, v = ln.split("=", 1)
            d[k.strip()] = v.strip()
    return d


def run(cmd: List[str]) -> None:
    p = subprocess.run(cmd, check=False, text=True, capture_output=True)
    if p.returncode != 0:
        sys.stderr.write(p.stdout)
        sys.stderr.write(p.stderr)
        raise SystemExit(p.returncode)


def maybe_download(run_id: str, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / run_id
    target.mkdir(parents=True, exist_ok=True)
    run(["gh", "run", "download", run_id, "-D", str(target)])


def find_telemetry_summaries(root: Path) -> List[Path]:
    return sorted(root.rglob("telemetry_summary.json"))


def validate_summary(path: Path) -> Tuple[bool, str]:
    try:
        d = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        return False, f"json_load_error: {e}"
    policy = d.get("policy")
    if not isinstance(policy, dict) or not policy:
        return False, "policy missing/empty"
    action = policy.get("action")
    if action not in VALID_ACTIONS:
        return False, f"policy.action invalid: {action!r}"
    rc = policy.get("reason_codes")
    if not isinstance(rc, list):
        return False, f"policy.reason_codes not list: {type(rc).__name__}"
    if FALLBACK_CODE in rc:
        return False, "fallback code present in reason_codes"
    src = d.get("source")
    if src != "evidence_manifest":
        return False, f"source unexpected: {src!r} (expected 'evidence_manifest')"
    return True, "OK"


def write_sha256sums(pack_dir: Path) -> Path:
    sums = pack_dir / "SHA256SUMS.stable.txt"
    files = [p for p in pack_dir.rglob("*") if p.is_file() and p.name != sums.name]
    files_sorted = sorted([str(p.relative_to(pack_dir).as_posix()) for p in files])
    lines: List[str] = []
    for rel in files_sorted:
        p = pack_dir / rel
        sp = subprocess.run(
            ["shasum", "-a", "256", str(p)],
            capture_output=True,
            text=True,
            check=True,
        )
        h = sp.stdout.strip().split()[0]
        lines.append(f"{h}  {rel}")
    sums.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return sums


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("pointer", type=Path, help="docs/ops/registry/*.pointer")
    ap.add_argument(
        "--out-base",
        type=Path,
        default=Path("out/ops/gh_runs"),
        help="download base dir",
    )
    ap.add_argument(
        "--download",
        action="store_true",
        help="download artifacts via gh run download",
    )
    ap.add_argument(
        "--pack-out",
        type=Path,
        default=None,
        help="optional evidence pack output dir",
    )
    args = ap.parse_args()

    ptr = args.pointer
    if not ptr.exists():
        raise SystemExit(f"ERR: pointer not found: {ptr}")

    d = parse_pointer(ptr)
    run_id = d.get("run_id")
    if not run_id:
        raise SystemExit("ERR: pointer missing run_id=")

    artifacts_root = args.out_base / run_id
    if args.download or not artifacts_root.exists():
        if not args.download and not artifacts_root.exists():
            raise SystemExit(f"ERR: artifacts missing at {artifacts_root}. Re-run with --download.")
        maybe_download(run_id, args.out_base)

    summaries = find_telemetry_summaries(artifacts_root)
    if not summaries:
        raise SystemExit(f"ERR: no telemetry_summary.json found under {artifacts_root}")

    bad: List[Tuple[Path, str]] = []
    for s in summaries:
        ok, msg = validate_summary(s)
        if not ok:
            bad.append((s, msg))

    if bad:
        sys.stderr.write("FAIL: telemetry invariants violated\n")
        for p, msg in bad[:200]:
            sys.stderr.write(f"- {p}: {msg}\n")
        raise SystemExit(3)

    print(f"OK: {len(summaries)} telemetry_summary.json validated under {artifacts_root}")

    if args.pack_out:
        pack = args.pack_out
        pack.mkdir(parents=True, exist_ok=True)
        dest = pack / f"gh_run_{run_id}"
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(artifacts_root, dest)
        sums = write_sha256sums(pack)
        print(f"OK: wrote {sums}")


if __name__ == "__main__":
    main()
