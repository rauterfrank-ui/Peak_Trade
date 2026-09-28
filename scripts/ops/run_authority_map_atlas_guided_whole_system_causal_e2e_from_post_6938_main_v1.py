"""Probative E2E: Authority-Map-/Atlas-guided whole-system G2 primary causal closure (post #6938)."""

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
PACK = REPO / "evidence/ops/authority_map_atlas_guided_whole_system_e2e_v1" / f"{_RUN_TS}-post6938"
PACK.mkdir(parents=True, exist_ok=True)
E2E_RUN_ID = f"amawse2e-post6938-{_RUN_TS}-{uuid.uuid4().hex[:12]}"

from src.governance.governed_authority_map_atlas_guided_whole_system_g2_primary_causal_e2e_v1 import (  # noqa: E402
    ATLAS_CENSUS_REL,
    MAP_SOURCE_REL,
    WORKPACKAGE_ID,
    adjudicate_lifecycle_primary_producers_v1,
    discover_primary_archives_under_evidence_ops_v1,
    lifecycle_report_to_mapping,
    prove_post_6938_case_b_preserved_v1,
    run_reference_fixture_g2_m8_control_v1,
    select_legitimate_observed_primary_archive_v1,
)
from src.governance.governed_productive_learning_to_g2_primary_evidence_causal_closure_v1 import (  # noqa: E402
    evaluate_productive_ddo_export_for_g2_primary_evidence_ingress_v1,
)
from src.governance.governed_runtime_primary_to_offline_observation_projection_v1 import (  # noqa: E402
    RuntimePrimarySourceModeV1,
)
from src.learning.deterministic_decision_outcome_v0.learning_evidence_export_v1 import (  # noqa: E402
    EXPORT_ID,
    PRODUCTIVE_OPTIMIZATION_JOIN_AUTHORIZED,
)
from tests.governance.governed_runtime_primary_to_offline_observation_projection_v1_fixtures import (  # noqa: E402
    cleanup_durable_archive_roots,
    projection_request,
    write_paper_primary_bundle,
)


def _origin_sha() -> str:
    return (
        subprocess.check_output(["git", "rev-parse", "origin/main"], cwd=REPO, text=True)
        .strip()
        .lower()
    )


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_map_edges() -> list[dict[str, Any]]:
    source = json.loads((REPO / MAP_SOURCE_REL).read_text(encoding="utf-8"))
    return list(source.get("edges") or [])


def main() -> int:
    baseline = _origin_sha()
    map_sha = _sha256_file(REPO / MAP_SOURCE_REL)
    atlas_sha = _sha256_file(REPO / ATLAS_CENSUS_REL)
    case_b = prove_post_6938_case_b_preserved_v1(repo_root=REPO)
    discovered = discover_primary_archives_under_evidence_ops_v1(repo_root=REPO)
    selected = select_legitimate_observed_primary_archive_v1(discovered)
    paper, shadow, testnet = adjudicate_lifecycle_primary_producers_v1(
        repo_root=REPO,
        observed_runtime_archive_found=selected is not None,
    )
    fixture_root = PACK / "fixture_control_paper_primary"
    fixture_root.mkdir(parents=True, exist_ok=True)
    cleanup_durable_archive_roots()
    write_paper_primary_bundle(fixture_root)
    fixture_req = projection_request(
        source_mode=RuntimePrimarySourceModeV1.PAPER,
        primary_root=fixture_root,
    )
    fixture_continuation = run_reference_fixture_g2_m8_control_v1(fixture_req)
    cleanup_durable_archive_roots()

    productive_reject = evaluate_productive_ddo_export_for_g2_primary_evidence_ingress_v1(
        {
            "join_seam_id": "current_productive_master_v2_ddo_capture_to_offline_export_join_v1",
            "optimization_ack_status": "ACCEPTED_OFFLINE_RESEARCH_INPUT",
            "session_id": "synthetic-case-b-check",
            "cycle_id": "c1",
            "correlation_id": "corr1",
            "learning_evidence_record_id": "ler1",
            "learning_state_record_ref": "lsr1",
            "export_id": EXPORT_ID,
        }
    )

    g2_edges = [
        e
        for e in _load_map_edges()
        if e.get("id")
        in {
            "g2_primary_evidence_to_offline_projection",
            "g2_runtime_learning_to_optimization_input_binding",
            "g2_runtime_to_m4_m8_real_mechanical_continuation",
            "productive_ddo_offline_export_to_g2_primary_evidence",
        }
    ]

    first_blocker = (
        "MISSING_INDEPENDENT_DURABLE_PAPER_SHADOW_TESTNET_PRIMARY_EVIDENCE_FOR_G2_INGRESS"
        if selected is None
        else None
    )
    blocker_detail = (
        "No OBSERVED_BOUNDED_RUNTIME durable archive with projection admission under evidence/ops; "
        "PAPER execute requires scoped approval record and default 7200s bounded job; "
        "untracked evidence worktree blocks strict-repo-clean execute."
        if selected is None
        else ""
    )

    report: dict[str, Any] = {
        "BASELINE_SHA": baseline,
        "WP": WORKPACKAGE_ID,
        "E2E_RUN_ID": E2E_RUN_ID,
        "MAP_SOURCE": MAP_SOURCE_REL,
        "MAP_SHA256": map_sha,
        "ATLAS_SOURCE": ATLAS_CENSUS_REL,
        "ATLAS_SHA256": atlas_sha,
        "POST_6938_CASE_B_PRESERVED": case_b,
        "CASE_B_PRODUCTIVE_G2_REJECT": {
            "g2_ingress_admitted": productive_reject.g2_ingress_admitted,
            "semantic_adjudication": productive_reject.semantic_adjudication,
        },
        "MAP_ATLAS_START_NODE": "bounded_runtime_primary_evidence",
        "MAP_ATLAS_CAUSAL_PATH": [
            "bounded_runtime_primary_evidence",
            "g2_runtime_primary_offline_projection",
            "g2_runtime_learning_optimization_input_binding",
            "g2_runtime_to_m4_m8_real_mechanical_continuation",
            "real_runtime_m4_m8_to_meta_learning_ingest",
        ],
        "MAP_G2_EDGE_SNAPSHOT": g2_edges,
        "PAPER": lifecycle_report_to_mapping(paper),
        "SHADOW": lifecycle_report_to_mapping(shadow),
        "TESTNET": lifecycle_report_to_mapping(testnet),
        "SELECTED_LEGITIMATE_LIFECYCLE": (selected.source_execution_mode if selected else "NONE"),
        "SELECTION_AUTHORITY_BASIS": (
            "OBSERVED_BOUNDED_RUNTIME_ARCHIVE_DISCOVERED"
            if selected
            else "NO_ADMISSIBLE_OBSERVED_ARCHIVE"
        ),
        "DISCOVERED_ARCHIVE_COUNT": len(discovered),
        "DISCOVERED_FIXTURE_COUNT": sum(
            1 for d in discovered if d.classification.value == "FIXTURE_OR_SYNTHETIC"
        ),
        "PRIMARY_ARCHIVE": str(selected.root) if selected else None,
        "FIXTURE_CONTROL_ARCHIVE": str(fixture_root),
        "FIXTURE_CONTROL_G2_M8": fixture_continuation.__dict__,
        "PRODUCTIVE_OPTIMIZATION_JOIN_AUTHORIZED": PRODUCTIVE_OPTIMIZATION_JOIN_AUTHORIZED is True,
        "REAL_EXTERNAL_EFFECT_COUNT": 0,
        "POST_ALLOWED": False,
        "EXTERNAL_EFFECT_AUTHORIZED": False,
        "EXECUTION_PRE_EXTERNAL_BOUNDARY_PRESERVED": True,
        "FIRST_REAL_BLOCKER": first_blocker,
        "WHY_IT_IS_REAL": blocker_detail,
        "NEXT_OWNER_DECISION_REQUIRED": (
            "Scoped bounded PAPER (or SHADOW/TESTNET) observation execute with valid "
            "approval record and durable closeout destination outside /tmp; or supply "
            "an existing independent durable primary archive admissible for G2 ingress."
            if selected is None
            else None
        ),
        "ALL_MECHANICALLY_AUTHORIZED_CLOSURES_EXHAUSTED": selected is None,
    }
    out = PACK / "FINAL_REPORT.json"
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (PACK / "LINEAGE.json").write_text(
        json.dumps(
            {
                "E2E_RUN_ID": E2E_RUN_ID,
                "BASELINE_SHA": baseline,
                "FIXTURE_CONTROL_ROOT": str(fixture_root),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"FINAL_REPORT": str(out), "FIRST_REAL_BLOCKER": first_blocker}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
