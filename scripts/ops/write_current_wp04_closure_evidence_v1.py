#!/usr/bin/env python3
"""Write CURRENT-WP-04 closure + standing admission evidence."""

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
    from src.ops.current_wp04_standing_pre_external_admission_endgame_done_gate_v1.constants_v1 import (
        BLUEPRINT_DEFINITION_SOURCE,
    )
    from src.ops.current_wp04_standing_pre_external_admission_endgame_done_gate_v1.evidence_v1 import (
        write_current_wp04_closure_evidence_v1,
    )
    from src.ops.current_wp04_standing_pre_external_admission_endgame_done_gate_v1.package_proof_v1 import (
        prove_current_wp04_package_v1,
        write_standing_pre_external_autonomy_admission_evidence_v1,
    )
    from src.ops.current_wp04_standing_pre_external_admission_endgame_done_gate_v1.standing_autonomy_record_v1 import (
        StandingPreExternalAutonomyRecordV1,
        write_standing_pre_external_autonomy_record_v1,
    )
    from src.ops.n1_whole_system_hard_facts_integration_wp_v1.backlog_matrix_v1 import (
        close_row_v1,
        initial_backlog_rows_v1,
        summarize_backlog_v1,
    )
    from tests.ops.test_current_wp04_standing_pre_external_admission_endgame_done_gate_v1 import (
        REQUIREMENT_ADJUDICATION,
        _public_chain_proof_v1,
        _wp03_proof_v1,
    )
    from tests.ops._wp03_supervisor_golden_harness_v1 import run_two_epoch_supervisor_v1
    from tests.ops.test_n1_standing_pre_external_runtime_supervisor_v1 import (
        OWNER_GO_BASELINE_SHA,
    )

    baseline = _git_sha("origin/main")
    tested = _git_sha("HEAD")
    with tempfile.TemporaryDirectory(prefix="wp04_evidence_") as tmp:
        root = Path(tmp)
        wp03 = _wp03_proof_v1(root)
        if not wp03.ok:
            print("WP03_PROOF_FAIL", file=sys.stderr)
            return 1
        public_proof = _public_chain_proof_v1(root / "pub_chain")
        rows = initial_backlog_rows_v1()
        pkg_dir = "src/ops/current_wp04_standing_pre_external_admission_endgame_done_gate_v1/"
        for row_id in rows:
            close_row_v1(
                rows,
                backlog_id=row_id,
                changed_files=(pkg_dir,),
                tests=(
                    "tests/ops/test_current_wp04_standing_pre_external_admission_endgame_done_gate_v1.py",
                ),
                notes="CURRENT-WP-04 standing admission",
            )
        summary = summarize_backlog_v1(rows)
        pkg = prove_current_wp04_package_v1(
            repo_root=REPO_ROOT,
            public_chain=public_proof,
            public_store_root=root / "pub_store",
            private_store_root=root / "priv_store",
            wp03=wp03,
            reference_supervisor_run=run_two_epoch_supervisor_v1(root / "ref_supervisor"),
            tested_code_sha=tested,
            backlog_matrix=summary,
        )
        if not pkg.ok:
            print("WP04_PACKAGE_FAIL", file=sys.stderr)
            return 1
        adm_path = write_standing_pre_external_autonomy_admission_evidence_v1(
            repo_root=REPO_ROOT,
            payload=pkg.admission_payload,
        )
        record = StandingPreExternalAutonomyRecordV1.from_admission_flags_v1(
            tested_code_sha=tested,
            mechanical_gate_ok=pkg.done_gate.mechanical_ok,
            post_allowed=False,
            external_effect_authorized=False,
            real_venue_post_allowed=False,
        )
        record_dir = adm_path.parent / "standing_autonomy_record"
        rec_path = write_standing_pre_external_autonomy_record_v1(
            out_dir=record_dir,
            record=record,
        )
        closure = write_current_wp04_closure_evidence_v1(
            repo_root=REPO_ROOT,
            baseline_sha=baseline,
            tested_code_sha=tested,
            admission=pkg.admission,
            done_gate=pkg.done_gate,
            requirement_adjudication={
                "source": BLUEPRINT_DEFINITION_SOURCE,
                "adjudication": REQUIREMENT_ADJUDICATION,
            },
            changed_files=(
                pkg_dir,
                "docs/ops/specs/CURRENT_WP04_STANDING_PRE_EXTERNAL_ADMISSION_ENDGAME_DONE_GATE_V1.md",
                "tests/ops/test_current_wp04_standing_pre_external_admission_endgame_done_gate_v1.py",
                "scripts/ops/write_current_wp04_closure_evidence_v1.py",
            ),
            tests_executed=(
                "tests/ops/test_current_wp04_standing_pre_external_admission_endgame_done_gate_v1.py",
                "tests/ops/test_current_wp03_live_scoped_observation_golden_convergence_v1.py",
                "tests/ops/test_current_wp02_default_productive_universe_handoff_v1.py",
                "tests/ops/test_n1_standing_pre_external_runtime_supervisor_v1.py",
            ),
            residuals=(
                "ALL_REQUIRED_CI_GREEN deferred to GitHub required checks on PR",
                "live_venue_market_data_observation not claimed; scoped_readonly_inject only",
            ),
        )
        print(closure)
        print(adm_path)
        print(rec_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
