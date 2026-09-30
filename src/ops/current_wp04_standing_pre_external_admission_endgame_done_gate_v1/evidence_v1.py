"""CURRENT-WP-04 closure evidence writer."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from src.ops.current_wp04_standing_pre_external_admission_endgame_done_gate_v1.constants_v1 import (
    BLUEPRINT_DEFINITION_SOURCE,
    EVIDENCE_ROOT_RELATIVE,
    WORK_PACKAGE_ID,
)
from src.ops.current_wp04_standing_pre_external_admission_endgame_done_gate_v1.done_gate_v1 import (
    CurrentN1EndgameDoneGateV1,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    POST_ALLOWED,
    REAL_VENUE_POST_ALLOWED,
)
from src.ops.hard_facts_system_closure_v1.authority_proof_v1 import (
    prove_hard_facts_authority_invariants_v1,
)
from src.ops.n1_whole_system_hard_facts_integration_wp_v1.pre_external_autonomy_admission_v1 import (
    PreExternalAutonomyAdmissionV1,
)


def _utc_stamp_v1() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def write_current_wp04_closure_evidence_v1(
    *,
    repo_root: Path,
    baseline_sha: str,
    tested_code_sha: str,
    admission: PreExternalAutonomyAdmissionV1,
    done_gate: CurrentN1EndgameDoneGateV1,
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
        "artifact_kind": "CURRENT_WP04_CLOSURE_V1",
        "work_package_id": WORK_PACKAGE_ID,
        "utc_timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "BASE_SHA": baseline_sha,
        "TESTED_CODE_SHA": tested_code_sha,
        "WP04_DEFINITION_SOURCE": BLUEPRINT_DEFINITION_SOURCE,
        "WP04_ID": "CURRENT-WP-04",
        "WP04_TITLE": "Standing PRE_EXTERNAL Admission and Endgame Done Gate",
        "requirement_adjudication": dict(requirement_adjudication),
        "changed_files": list(changed_files),
        "tests_executed": list(tests_executed),
        "CURRENT_N1_ENDGAME_DONE_GATE": done_gate.as_dict_v1(),
        "ENDGAME_IMPLEMENTATION_COMPLETE": done_gate.ok,
        "MECHANICAL_ENDGAME_GATE_OK": done_gate.mechanical_ok,
        "admission_ok": admission.ok,
        "POST_COUNT": admission.post_count,
        "POST_ALLOWED": POST_ALLOWED is True,
        "EXTERNAL_EFFECT_AUTHORIZED": EXTERNAL_EFFECT_AUTHORIZED is True,
        "REAL_VENUE_POST_ALLOWED": REAL_VENUE_POST_ALLOWED is True,
        "authority_invariants_ok": auth.ok is True,
        "contract_reachability_proof": {
            "producer_consumer": "wp01_supervisor→wp02_handoff→wp03_golden→wp04_admission",
            "runtime_reachable": done_gate.RUNTIME_SUPERVISOR_CLOSED,
        },
        "fail_closed_proof": {
            "post_count_zero": admission.post_count == 0,
            "safety_pins_false": not (
                POST_ALLOWED or EXTERNAL_EFFECT_AUTHORIZED or REAL_VENUE_POST_ALLOWED
            ),
        },
        "known_residuals": list(residuals),
        "WP05_NOT_STARTED": True,
        "ok": done_gate.mechanical_ok and admission.ok,
    }
    path = out_dir / "CURRENT_WP04_CLOSURE_V1.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path
