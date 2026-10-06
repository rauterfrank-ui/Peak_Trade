#!/usr/bin/env python3
"""Thin authority/config wrapper → same GHV PRE_EXTERNAL entrypoint (Testnet Observation v1).

Binds scoped Owner-GO, isolated state roots, and Demo GET-only transport mode only.
Does not introduce a second orchestration spine.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
GHV_ENTRY = (
    REPO_ROOT
    / "scripts/ops/run_current_productive_policy_governed_live_c1_pre_external_convergence_v1.py"
)


def _main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "GHV Full-System Testnet Observation PRE_EXTERNAL binding wrapper "
            "(same GHV entrypoint, scoped Demo observation transport)"
        )
    )
    parser.add_argument(
        "--state-base-root",
        type=Path,
        required=True,
        help="Base directory; isolated ghv_full_system_testnet_observation_v1 roots are derived",
    )
    parser.add_argument(
        "--full-system-testnet-observation-owner-go",
        required=True,
        help="Scoped Owner-GO token for FULL_SYSTEM_TESTNET_OBSERVATION_PRE_EXTERNAL_V1",
    )
    parser.add_argument(
        "ghv_args", nargs=argparse.REMAINDER, help="Additional args forwarded to GHV"
    )
    args = parser.parse_args()

    from src.ops.full_core_live_path_composition_root_v1.ghv_full_system_testnet_observation_pre_external_v1.governance_v1 import (
        assert_full_system_testnet_observation_owner_go_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.ghv_full_system_testnet_observation_pre_external_v1.state_roots_v1 import (
        derive_ghv_testnet_observation_state_roots_v1,
    )

    assert_full_system_testnet_observation_owner_go_v1(
        args.full_system_testnet_observation_owner_go
    )
    roots = derive_ghv_testnet_observation_state_roots_v1(args.state_base_root)

    cmd = [
        sys.executable,
        str(GHV_ENTRY),
        "--evidence-root",
        str(roots.evidence_root),
        "--lane-state-root",
        str(roots.lane_state_root),
        "--productivity-root",
        str(roots.productivity_root),
        "--private-account-transport-mode",
        "ghv_full_system_testnet_observation_v1",
        "--full-system-testnet-observation-owner-go",
        str(args.full_system_testnet_observation_owner_go),
    ]
    extra = list(args.ghv_args or [])
    if extra and extra[0] == "--":
        extra = extra[1:]
    cmd.extend(extra)
    completed = subprocess.run(cmd, cwd=str(REPO_ROOT), check=False)
    return int(completed.returncode)


if __name__ == "__main__":
    raise SystemExit(_main())
