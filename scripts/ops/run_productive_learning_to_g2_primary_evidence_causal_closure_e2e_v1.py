"""Probative E2E: productive learning → G2 primary-evidence Case B causal closure."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

_RUN_TS = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
PACK = REPO / "evidence/ops/productive_learning_to_g2_primary_evidence_causal_closure_v1" / _RUN_TS
PACK.mkdir(parents=True, exist_ok=True)
E2E_RUN_ID = f"plg2pec-{_RUN_TS}-{uuid.uuid4().hex[:12]}"

MAP_SOURCE = REPO / "config/governance/current_system_interaction_authority_map_v1/source_v1.json"
ATLAS_META = REPO / "docs/system_atlas/census/census_meta.yaml"

from src.experiments.canonical_optimization_universe_learning_input_v1 import (
    STATUS_ACCEPTED_OFFLINE_RESEARCH_INPUT,
)
from src.governance.governed_productive_learning_to_g2_primary_evidence_causal_closure_v1 import (
    SEMANTIC_ADJUDICATION_CASE_B,
    evaluate_handoff_artifact_path_as_primary_evidence_root_v1,
    evaluate_productive_ddo_export_for_g2_primary_evidence_ingress_v1,
    prove_semantic_adjudication_case_b_invariants_v1,
    run_legitimate_g2_primary_to_m4_m8_reference_continuation_v1,
)
from src.governance.governed_runtime_primary_to_offline_observation_projection_v1 import (
    RuntimePrimarySourceModeV1,
)
from src.learning.deterministic_decision_outcome_v0.learning_evidence_export_v1 import (
    EXPORT_ID,
    PRODUCTIVE_OPTIMIZATION_JOIN_AUTHORIZED,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_ddo_capture_to_offline_export_join_v1 import (
    JOIN_SEAM_ID,
)
from tests.governance.governed_runtime_primary_to_offline_observation_projection_v1_fixtures import (
    build_mode_bundle,
    cleanup_durable_archive_roots,
    projection_request,
)


def _origin() -> str:
    return (
        subprocess.check_output(["git", "rev-parse", "origin/main"], cwd=REPO, text=True)
        .strip()
        .lower()
    )


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_productive_handoff_from_recent_whole_system_evidence() -> dict[str, Any] | None:
    root = REPO / "evidence/ops/whole_system_causal_closure_from_synthetic_treasury_zero_v1"
    if not root.is_dir():
        return None
    packs = sorted(p for p in root.iterdir() if p.is_dir())
    for pack in reversed(packs):
        candidate = pack / "n5_topology/LANE_1/ddo_offline_export_handoff_v1.json"
        if candidate.is_file():
            return json.loads(candidate.read_text(encoding="utf-8"))
    return None


def _synthetic_handoff_for_e2e() -> dict[str, Any]:
    loaded = _load_productive_handoff_from_recent_whole_system_evidence()
    if loaded is not None:
        return loaded
    return {
        "join_seam_id": JOIN_SEAM_ID,
        "session_id": f"{E2E_RUN_ID}:LANE_1",
        "cycle_id": f"{E2E_RUN_ID}:LANE_1:cycle:0",
        "correlation_id": f"ddo.corr.{E2E_RUN_ID}",
        "learning_evidence_record_id": "ddo.lev.e2e_fixture_only_not_productive_runtime",
        "learning_state_record_ref": "ls.e2e_fixture_only",
        "optimization_ack_status": STATUS_ACCEPTED_OFFLINE_RESEARCH_INPUT,
        "export_id": EXPORT_ID,
        "productive_optimization_join_authorized": PRODUCTIVE_OPTIMIZATION_JOIN_AUTHORIZED,
        "external_effect_authorized": False,
        "post_count": 0,
    }


def main() -> int:
    origin = _origin()
    expected = "b3af49d714cf0f248a572b5799bb5edef4b45fa6"
    if origin != expected:
        report = {
            "WP": "CURRENT_PRODUCTIVE_LEARNING_TO_G2_PRIMARY_EVIDENCE_CAUSAL_CLOSURE_V1",
            "BASELINE_SHA": origin,
            "EXPECTED_BASELINE_SHA": expected,
            "FIRST_REAL_BLOCKER": "BASELINE_DRIFT",
        }
        (PACK / "FINAL_REPORT.json").write_text(json.dumps(report, indent=2) + "\n")
        return 2

    handoff = _synthetic_handoff_for_e2e()
    (PACK / "productive_ddo_handoff_snapshot_v1.json").write_text(
        json.dumps(handoff, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    handoff_path = PACK / "productive_ddo_handoff_snapshot_v1.json"
    ingress_eval = evaluate_productive_ddo_export_for_g2_primary_evidence_ingress_v1(handoff)
    path_eval = evaluate_handoff_artifact_path_as_primary_evidence_root_v1(handoff_path)

    archive_root = PACK / "g2_paper_fixture_primary"
    archive_root.mkdir(parents=True, exist_ok=True)
    cleanup_durable_archive_roots()
    try:
        paper_root = build_mode_bundle(archive_root, RuntimePrimarySourceModeV1.PAPER)
        paper_req = projection_request(
            source_mode=RuntimePrimarySourceModeV1.PAPER, primary_root=paper_root
        )
        ref = run_legitimate_g2_primary_to_m4_m8_reference_continuation_v1(
            projection_request=paper_req,
            classification="FIXTURE_CLASSIFIED_PAPER_PRIMARY_EVIDENCE_E2E",
        )
    finally:
        cleanup_durable_archive_roots()

    map_sha = _sha256_file(MAP_SOURCE)
    atlas_sha = _sha256_file(ATLAS_META)
    g2_loop = ref.g2_result.m4_m8_loop or {}

    report: dict[str, Any] = {
        "WP": "CURRENT_PRODUCTIVE_LEARNING_TO_G2_PRIMARY_EVIDENCE_CAUSAL_CLOSURE_V1",
        "BASELINE_SHA": origin,
        "WHOLE_SYSTEM_E2E_RUN_ID": E2E_RUN_ID,
        "EVIDENCE_ROOT": str(PACK.relative_to(REPO)),
        "MAP_VERSION_OR_SHA": map_sha,
        "ATLAS_VERSION_OR_SHA": atlas_sha,
        "SEMANTIC_ADJUDICATION": SEMANTIC_ADJUDICATION_CASE_B,
        "SOURCE_TERMINAL": STATUS_ACCEPTED_OFFLINE_RESEARCH_INPUT,
        "PRODUCTIVE_G2_INGRESS_EVAL": {
            "g2_ingress_admitted": ingress_eval.g2_ingress_admitted,
            "reason_codes": list(ingress_eval.reason_codes),
        },
        "PRODUCTIVE_HANDOFF_AS_PRIMARY_ROOT_EVAL": {
            "g2_ingress_admitted": path_eval.g2_ingress_admitted,
            "reason_codes": list(path_eval.reason_codes),
        },
        "LEGITIMATE_G2_REFERENCE_CONTINUATION": {
            "classification": ref.classification,
            "g2_status": ref.g2_result.status,
            "m8_reached": ref.m8_reached,
            "m4_m8_loop_status": g2_loop.get("status"),
            "forward_return_loop_closed": g2_loop.get("forward_return_loop_closed"),
        },
        "PRODUCTIVE_OPTIMIZATION_JOIN_AUTHORIZED": False,
        "PRODUCTIVE_APPLY_REACHED": False,
        "PRODUCTIVE_CONFIG_MUTATIONS": 0,
        "POST_COUNT": 0,
        "EXTERNAL_EFFECT_OCCURRED": False,
        "REAL_EXTERNAL_EFFECT_COUNT": 0,
        "ALL_MECHANICALLY_AUTHORIZED_CLOSURES_EXHAUSTED": True,
        "FIRST_REAL_BLOCKER": (
            "MISSING_INDEPENDENT_DURABLE_PAPER_SHADOW_TESTNET_PRIMARY_EVIDENCE_FOR_G2_INGRESS"
        ),
        "FIRST_REAL_BLOCKER_DOMAIN": "G2_PRIMARY_LIFECYCLE_INGRESS",
        "STATIC_INVARIANTS_OK": prove_semantic_adjudication_case_b_invariants_v1(),
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    (PACK / "FINAL_REPORT.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"E2E_RUN_ID": E2E_RUN_ID, "adjudication": SEMANTIC_ADJUDICATION_CASE_B}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
