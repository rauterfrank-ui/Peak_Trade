#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def run(cmd: list[str], *, check: bool = False) -> tuple[int, str, str]:
    proc = subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check and proc.returncode != 0:
        raise RuntimeError(
            f"command failed rc={proc.returncode}: {' '.join(cmd)}\n"
            f"stdout:\n{proc.stdout}\n\nstderr:\n{proc.stderr}"
        )
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def lines(text: str) -> list[str]:
    return [x for x in text.splitlines() if x.strip()]


def main() -> int:
    rc, branch, _ = run(["git", "branch", "--show-current"], check=True)
    rc, head, _ = run(["git", "rev-parse", "HEAD"], check=True)
    rc, origin_main, _ = run(["git", "rev-parse", "origin/main"], check=True)
    rc, status_short, _ = run(["git", "status", "--short"], check=True)
    rc, stash_list, _ = run(["git", "stash", "list"], check=False)
    rc, ahead_behind, _ = run(
        ["git", "rev-list", "--left-right", "--count", "origin/main...HEAD"],
        check=True,
    )

    behind, ahead = [int(x) for x in ahead_behind.split()]

    findings: list[str] = []
    verdict = "PASS"

    if status_short:
        verdict = "FAIL"
        findings.append("WORKTREE_NOT_CLEAN")

    if branch == "main" and (ahead != 0 or behind != 0):
        verdict = "FAIL"
        findings.append("MAIN_DIVERGED_FROM_ORIGIN_MAIN")

    if stash_list:
        findings.append("STASH_PRESENT_WARN_ONLY")

    payload = {
        "verdict": verdict,
        "branch": branch,
        "head": head,
        "origin_main": origin_main,
        "ahead_origin_main": ahead,
        "behind_origin_main": behind,
        "worktree_clean": not bool(status_short),
        "stash_entries": len(lines(stash_list)),
        "findings": findings,
    }

    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
