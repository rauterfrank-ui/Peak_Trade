#!/usr/bin/env python3
"""Test-only child for the CURRENT full-system offline E2E crash segments.

Re-anchors the kill-switch state root to the isolated per-test root (never the
canonical root) in-process, then runs the unchanged offline E2E crash worker.
"""

from __future__ import annotations

import argparse
import runpy
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.ops.gates import risk_gate  # noqa: E402

WORKER_SCRIPT = (
    _REPO_ROOT / "scripts" / "ops" / "run_current_full_system_offline_e2e_crash_worker_v1.py"
)


def offline_e2e_kill_switch_root_v1(state_root: Path) -> Path:
    return (state_root.parent / f"{state_root.name}__kill_switch").resolve()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state-root", required=True)
    args = parser.parse_args()
    risk_gate._KILL_SWITCH_STATE_ROOT = offline_e2e_kill_switch_root_v1(Path(args.state_root))
    sys.argv = [str(WORKER_SCRIPT)]
    runpy.run_path(str(WORKER_SCRIPT), run_name="__main__")


if __name__ == "__main__":
    main()
