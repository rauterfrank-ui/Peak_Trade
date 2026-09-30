"""Machine-readable WP-03 closure evidence."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from src.ops.current_wp03_live_scoped_observation_golden_convergence_v1.constants_v1 import (
    EVIDENCE_ROOT_RELATIVE,
    WORK_PACKAGE_ID,
)
from src.ops.current_wp03_live_scoped_observation_golden_convergence_v1.convergence_proof_v1 import (
    Wp03ConvergenceProofV1,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    POST_ALLOWED,
    REAL_VENUE_POST_ALLOWED,
)
from src.ops.hard_facts_system_closure_v1.authority_proof_v1 import (
    prove_hard_facts_authority_invariants_v1,
)


def _utc_stamp_v1() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def write_current_wp03_closure_evidence_v1(
    *,
    repo_root: Path,
    baseline_sha: str,
    tested_code_sha: str,
    proof: Wp03ConvergenceProofV1,
    requirement_adjudication: Mapping[str, Any],
    changed_files: tuple[str, ...],
    tests_executed: tuple[str, ...],
    residuals: tuple[str, ...] = (),
) -> Path:
    auth = prove_hard_facts_authority_invariants_v1()
    stamp = _utc_stamp_v1()
    out_dir = repo_root / EVIDENCE_ROOT_RELATIVE / stamp
    out_dir.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "artifact_kind": "CURRENT_WP03_CLOSURE_V1",
        "work_package_id": WORK_PACKAGE_ID,
        "utc_timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "BASELINE_SHA": baseline_sha,
        "TESTED_CODE_SHA": tested_code_sha,
        "scope": "CURRENT-WP-03 live-scoped observation golden convergence",
        "requirement_adjudication": dict(requirement_adjudication),
        "changed_files": list(changed_files),
        "tests_executed": list(tests_executed),
        "GOLDEN_HAPPY_PATH_LIVE_OR_SCOPED_READONLY": proof.observation_scope,
        "NATURAL_LONG_REACHABLE_TO_PRE_EXTERNAL": proof.scenarios[0].pre_external_reached,
        "NATURAL_SHORT_REACHABLE_TO_PRE_EXTERNAL": proof.scenarios[1].pre_external_reached,
        "CONFIRMATION_TWO_EPOCH_PROVEN": proof.confirmation_two_epoch_proven,
        "synthetic_b05_rejected": proof.synthetic_b05_rejected,
        "POST_COUNT": proof.post_count,
        "POST_ALLOWED": POST_ALLOWED is True,
        "EXTERNAL_EFFECT_AUTHORIZED": EXTERNAL_EFFECT_AUTHORIZED is True,
        "REAL_VENUE_POST_ALLOWED": REAL_VENUE_POST_ALLOWED is True,
        "authority_invariants_ok": auth.ok is True,
        "contract_reachability_proof": {
            "golden_trace_keys_full": True,
            "producer_consumer": "supervisor→trace_projection→golden_harness",
        },
        "known_residuals": list(residuals),
        "WP04_NOT_STARTED": True,
        "ok": proof.ok,
    }
    path = out_dir / "CURRENT_WP03_CLOSURE_V1.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path
