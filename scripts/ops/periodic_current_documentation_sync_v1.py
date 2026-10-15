#!/usr/bin/env python3
"""Periodic CURRENT documentation sync analysis (OWNER_DOC_SYNC_GO gates mutations).

AUTHORITY=NONE — does not modify trading semantics or grant governance authority.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _run(cmd: list[str], *, cwd: Path) -> tuple[int, str]:
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    out = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode, out


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Analyze documentation/atlas/map currency against CURRENT baseline.",
    )
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--baseline-sha", type=str, default="origin/main")
    parser.add_argument(
        "--report-json",
        type=Path,
        default=None,
        help="Write machine-readable report (always allowed).",
    )
    args = parser.parse_args()
    repo = args.repo_root.resolve()
    owner_go = os.environ.get("OWNER_DOC_SYNC_GO", "").strip().lower() in ("1", "true", "yes")

    checks: list[dict[str, object]] = []

    rc, out = _run([sys.executable, "scripts/ops/validate_system_atlas_v1.py"], cwd=repo)
    checks.append({"check": "atlas_validate", "exit_code": rc, "blocking": rc != 0})

    rc2, out2 = _run(
        [sys.executable, "scripts/ops/current_law_impact_map_v1.py", "generate", "--check"],
        cwd=repo,
    )
    checks.append({"check": "law_map_generate_check", "exit_code": rc2})

    rc3, out3 = _run(
        [
            sys.executable,
            "scripts/ops/current_system_interaction_authority_map_v1.py",
            "validate",
            "--diff-base",
            str(args.baseline_sha),
        ],
        cwd=repo,
    )
    checks.append({"check": "interaction_map_currency", "exit_code": rc3, "blocking": rc3 != 0})

    report = {
        "schema_version": "periodic_current_documentation_sync_report.v1",
        "authority": "NONE",
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "baseline_sha_ref": args.baseline_sha,
        "OWNER_DOC_SYNC_GO": owner_go,
        "mutation_performed": False,
        "checks": checks,
        "note": "Analysis-only unless OWNER_DOC_SYNC_GO=true authorizes future write steps.",
    }

    if args.report_json:
        args.report_json.parent.mkdir(parents=True, exist_ok=True)
        args.report_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

    print(json.dumps(report, sort_keys=True))
    if not owner_go:
        print(
            "OWNER_DOC_SYNC_GO=false — analysis only; no documentation mutations.", file=sys.stderr
        )
    blocking = any(c.get("blocking") and c.get("exit_code") not in (0, None) for c in checks)
    return 1 if blocking else 0


if __name__ == "__main__":
    raise SystemExit(main())
