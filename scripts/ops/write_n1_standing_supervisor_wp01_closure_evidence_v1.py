#!/usr/bin/env python3
"""Regenerate WP-01 standing supervisor closure evidence (offline inject, >=2 cycles)."""

from __future__ import annotations

import json
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
    from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
        EXTERNAL_EFFECT_AUTHORIZED,
        POST_ALLOWED,
        REAL_VENUE_POST_ALLOWED,
    )
    from src.ops.n1_standing_pre_external_runtime_supervisor_v1.constants_v1 import (
        TRANSPORT_SCOPE_OFFLINE_INJECT,
    )
    from src.ops.n1_standing_pre_external_runtime_supervisor_v1.evidence_v1 import (
        write_standing_supervisor_closure_evidence_v1,
    )
    from tests.ops._n1_standing_supervisor_offline_inject_harness_v1 import (
        OWNER_GO_BASELINE_SHA,
        run_offline_inject_supervisor_session_v1,
    )

    tested_sha = _git_sha("HEAD")
    baseline_sha = _git_sha("origin/main")

    with tempfile.TemporaryDirectory(prefix="n1_standing_wp01_evidence_") as tmp:
        result = run_offline_inject_supervisor_session_v1(
            repo_root=REPO_ROOT,
            session_root=Path(tmp),
            origin_main_sha=OWNER_GO_BASELINE_SHA,
            max_cycles=2,
        )

    ok = (
        result.ok
        and result.trace.governed_cycle_count >= 2
        and result.trace.accepted_c1_count == result.trace.governed_cycle_count == 2
        and result.trace.post_count == 0
        and result.owner_go_consumed
        and result.authority_invariants_ok
        and result.trace.recovery_completed
        and not POST_ALLOWED
        and not EXTERNAL_EFFECT_AUTHORIZED
        and not REAL_VENUE_POST_ALLOWED
    )

    ev_path = write_standing_supervisor_closure_evidence_v1(
        repo_root=REPO_ROOT,
        tested_code_sha=tested_sha,
        baseline_sha=baseline_sha,
        trace=result.trace,
        ok=ok,
        owner_go_consumed=result.owner_go_consumed,
        authority_invariants_ok=result.authority_invariants_ok,
        transport_scope=TRANSPORT_SCOPE_OFFLINE_INJECT,
        launcher_invoked_supervisor=True,
        post_allowed=False,
        external_effect_authorized=False,
        real_venue_post_allowed=False,
        continuous_admission_granted=result.trace.continuous_admission_granted,
    )
    print(json.dumps({"evidence_path": str(ev_path), "ok": ok, "TESTED_CODE_SHA": tested_sha}))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
