#!/usr/bin/env python3
"""Write CURRENT-WP-03 closure evidence from offline golden convergence proof."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _git_sha(ref: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "rev-parse", ref],
        check=True,
        capture_output=True,
        text=True,
    )
    return proc.stdout.strip()


def main() -> int:
    from src.ops.current_wp03_live_scoped_observation_golden_convergence_v1.convergence_proof_v1 import (
        prove_wp03_golden_convergence_v1,
    )
    from src.ops.current_wp03_live_scoped_observation_golden_convergence_v1.evidence_v1 import (
        write_current_wp03_closure_evidence_v1,
    )
    from tests.ops._wp03_supervisor_golden_harness_v1 import (
        run_hold_supervisor_v1,
        run_natural_long_supervisor_v1,
        run_natural_short_supervisor_v1,
        run_two_epoch_supervisor_v1,
    )
    from tests.ops.test_n1_standing_pre_external_runtime_supervisor_v1 import (
        OWNER_GO_BASELINE_SHA,
    )

    baseline = _git_sha("origin/main")
    tested = _git_sha("HEAD")
    with tempfile.TemporaryDirectory(prefix="wp03_evidence_") as tmp:
        root = Path(tmp)
        proof = prove_wp03_golden_convergence_v1(
            long_result=run_natural_long_supervisor_v1(root / "long"),
            short_result=run_natural_short_supervisor_v1(root / "short"),
            hold_result=run_hold_supervisor_v1(root / "hold"),
            two_epoch_result=run_two_epoch_supervisor_v1(root / "two_epoch"),
        )
        if not proof.ok:
            print("WP03_PROOF_FAIL", file=sys.stderr)
            return 1
        path = write_current_wp03_closure_evidence_v1(
            repo_root=REPO_ROOT,
            baseline_sha=baseline,
            tested_code_sha=tested,
            proof=proof,
            requirement_adjudication={
                "source": "Peak_Trade_CURRENT_REMAINING_ENDGAME_IMPLEMENTATION_BLUEPRINT_V1.md",
                "WP03": "CURRENT-WP-03",
            },
            changed_files=(
                "src/ops/current_wp03_live_scoped_observation_golden_convergence_v1/",
                "docs/ops/specs/CURRENT_WP03_LIVE_SCOPED_OBSERVATION_GOLDEN_CONVERGENCE_V1.md",
                "tests/ops/test_current_wp03_live_scoped_observation_golden_convergence_v1.py",
                "tests/ops/_wp03_supervisor_golden_harness_v1.py",
                "scripts/ops/write_current_wp03_closure_evidence_v1.py",
            ),
            tests_executed=(
                "tests/ops/test_current_wp03_live_scoped_observation_golden_convergence_v1.py",
                "tests/ops/test_n1_standing_pre_external_runtime_supervisor_v1.py",
                "tests/ops/test_current_wp02_default_productive_universe_handoff_v1.py",
            ),
            residuals=(
                "live_venue_market_data_observation not claimed; scoped_readonly_inject only",
            ),
        )
        print(path)
        print(f"OWNER_GO_BASELINE_FOR_TESTS={OWNER_GO_BASELINE_SHA}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
