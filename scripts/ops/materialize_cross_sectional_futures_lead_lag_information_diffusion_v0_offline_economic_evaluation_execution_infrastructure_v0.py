#!/usr/bin/env python3
"""Materialize cross-sectional lead-lag diffusion v0 execution infrastructure v0.

Bounded infrastructure completion: start-state verification, entrypoint dry-run,
durable evidence bundle with MANIFEST.sha256. No economic evaluation execution.
Operator GO: GO_CROSS_SECTIONAL_FUTURES_LEAD_LAG_INFORMATION_DIFFUSION_V0_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_INFRASTRUCTURE_IMPLEMENTATION_V0
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.ops import (  # noqa: E402
    run_cross_sectional_futures_lead_lag_information_diffusion_v0_offline_economic_evaluation_execution_v0 as runner_module,
)
from src.research.cross_sectional_futures_lead_lag_information_diffusion_v0_offline_economic_evaluation_execution_v0 import (  # noqa: E402
    INFRASTRUCTURE_GO_TOKEN,
)

CONFIRM_GO = INFRASTRUCTURE_GO_TOKEN
DEFAULT_DURABLE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)
DEFAULT_STAGING_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "datasets/admissible_futures/pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_v1/v1"
)


def _die(msg: str, code: int = 2) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def run_materialization(
    *,
    confirm: str,
    durable_evidence_root: Path,
    primary_worktree: Path,
    staging_root: Path,
) -> dict[str, Any]:
    if confirm != CONFIRM_GO:
        _die(f"ERR:confirm_go_token_required:{CONFIRM_GO}")
    return runner_module.run_execution_infrastructure_v0(
        confirm=confirm,
        durable_evidence_root=durable_evidence_root,
        primary_worktree=primary_worktree,
        staging_root=staging_root,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirm", required=True)
    parser.add_argument("--durable-evidence-root", type=Path, default=DEFAULT_DURABLE_ROOT)
    parser.add_argument("--primary-worktree", type=Path, required=True)
    parser.add_argument("--staging-root", type=Path, default=DEFAULT_STAGING_ROOT)
    args = parser.parse_args()
    result = run_materialization(
        confirm=args.confirm,
        durable_evidence_root=args.durable_evidence_root,
        primary_worktree=args.primary_worktree,
        staging_root=args.staging_root,
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
