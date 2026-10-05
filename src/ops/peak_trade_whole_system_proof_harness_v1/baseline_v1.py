"""Repository baseline capture for proof runs."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from src.ops.peak_trade_whole_system_proof_harness_v1.constants_v1 import (
    BASELINE_ORIGIN_MAIN_SHA,
)


def _run(cmd: list[str], cwd: Path) -> str:
    return subprocess.check_output(cmd, cwd=cwd, text=True).strip()


def capture_baseline_v1(repo: Path) -> dict[str, Any]:
    origin_main = _run(["git", "rev-parse", "origin/main"], repo)
    head = _run(["git", "rev-parse", "HEAD"], repo)
    tree = _run(["git", "rev-parse", f"{origin_main}^{{tree}}"], repo)
    status = _run(["git", "status", "--porcelain"], repo)
    tracked_dirty = [line for line in status.splitlines() if line and not line.startswith("??")]
    drift = origin_main != BASELINE_ORIGIN_MAIN_SHA
    return {
        "BASELINE_SHA": BASELINE_ORIGIN_MAIN_SHA,
        "ORIGIN_MAIN_SHA": origin_main,
        "BASELINE_DRIFT": drift,
        "LOCAL_HEAD": head,
        "BASELINE_TREE": tree,
        "TRACKED_WORKTREE_CLEAN": len(tracked_dirty) == 0,
        "TRACKED_DIRTY_LINES": tracked_dirty,
    }
