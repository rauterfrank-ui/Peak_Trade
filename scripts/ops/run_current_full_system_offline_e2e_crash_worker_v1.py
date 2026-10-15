#!/usr/bin/env python3
"""Isolated-process worker for CURRENT full-system offline E2E crash segments."""

from __future__ import annotations

import os
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.ops.full_core_live_path_composition_root_v1.current_full_system_offline_e2e_integration_proof_v1 import (
    CRASH_POINT_ENV_VAR,
    run_offline_e2e_crash_worker_from_persisted_input_v1,
)


def main() -> int:
    state_raw = str(os.environ.get("PEAK_TRADE_OFFLINE_E2E_STATE_ROOT") or "").strip()
    if not state_raw:
        return 2
    return run_offline_e2e_crash_worker_from_persisted_input_v1(state_root=Path(state_raw))


if __name__ == "__main__":
    sys.exit(main())
