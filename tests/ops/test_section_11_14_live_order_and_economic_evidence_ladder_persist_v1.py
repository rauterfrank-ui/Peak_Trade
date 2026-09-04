"""Persist-lock for the offline §11.14 evidence-ladder surface."""

from __future__ import annotations

from pathlib import Path

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.evidence_v1 import (
    verify_manifest_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    CANONICAL_EVIDENCE_RUN_ID,
    CANONICAL_OFFLINE_SLICE_HEADING,
    CANONICAL_SECTION_HEADING,
    EARLIEST_UNRESOLVED_DEPENDENCY,
    EXPECTED_ORIGIN_MAIN_SHA,
    LADDER_FIELDS,
    MANDATORY_LIVE_METRICS,
    NEXT_OWNER_GO_REQUIRED,
    OWNER_GO,
    PREDECESSOR_SLICE,
    THIS_SLICE,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
SPEC = (
    REPO_ROOT
    / "docs/ops/specs/SECTION_11_14_LIVE_ORDER_AND_ECONOMIC_EVIDENCE_LADDER_OFFLINE_SURFACE_V1.md"
)
MOT = REPO_ROOT / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md"
ATLAS_CATALOG = REPO_ROOT / "docs/system_atlas/entities/catalog.yaml"
ATLAS_AUTHORITY = REPO_ROOT / "docs/system_atlas/ATLAS_AUTHORITY_AND_USAGE.md"
ATLAS_RUNTIME_RELATIONS = REPO_ROOT / "docs/system_atlas/relations/runtime.yaml"
EVIDENCE = (
    REPO_ROOT
    / "evidence/ops"
    / "section_11_14_live_order_and_economic_evidence_ladder_v1"
    / CANONICAL_EVIDENCE_RUN_ID
)
G12_HEADING = "### 11.13.5 G12_CANONICAL_DELAYED_ZERO_PERSIST_AND_PENDING_RELATED_OBSERVATIONS"
HEADING_11_15 = "## 11.15 Full-autonomy observability and audit trail"


def test_runbook_offline_slice_does_not_complete_section_11_14() -> None:
    text = MASTER_RUNBOOK.read_text(encoding="utf-8")
    start = text.find(CANONICAL_OFFLINE_SLICE_HEADING)
    ladder = text.find(CANONICAL_SECTION_HEADING)
    g12 = text.find(G12_HEADING)
    end = text.find(HEADING_11_15, start)
    assert ladder >= 0
    assert g12 >= 0
    assert start > ladder
    assert start > g12
    assert end > start
    section = text[start:end]
    assert f"OWNER_GO={OWNER_GO}" in section
    assert f"THIS_SLICE={THIS_SLICE}" in section
    assert f"PREDECESSOR_SLICE={PREDECESSOR_SLICE}" in section
    assert f"EXPECTED_ORIGIN_MAIN_SHA={EXPECTED_ORIGIN_MAIN_SHA}" in section
    assert "SECTION_11_14_AUTHORIZED=false" in section
    assert "SECTION_11_14_COMPLETE=false" in section
    assert "SECTION_11_14_OFFLINE_SURFACE_BOUND=true" in section
    assert "LIVE_EXECUTION_CODE_EXISTS=false" in section
    assert "LIVE_EXECUTION_PATH_REACHABLE=false" in section
    assert "LIVE_PRIVATE_READ_ONLY_PROVEN=false" in section
    assert "LIVE_ORDER_PLAN_OBSERVED=false" in section
    assert "LIVE_SUBMIT_ACK_OBSERVED=false" in section
    assert "LIVE_FILL_OBSERVED=false" in section
    assert "LIVE_FEE_OBSERVED=false" in section
    assert "LIVE_POSITION_RECONCILED=false" in section
    assert "LIVE_ACCOUNTING_RECONSTRUCTED=false" in section
    assert "LIVE_RESTART_RECONSTRUCTED=false" in section
    assert "LIVE_AUTONOMOUS_RECOVERY_OBSERVED=false" in section
    assert "LIVE_END_TO_END_EVIDENCE_PROVEN=false" in section
    assert "POST_PERFORMED=false" in section
    assert "GET_PERFORMED=false" in section
    assert "COLLECTOR_ACTIVATED=false" in section
    assert f"EARLIEST_UNRESOLVED_DEPENDENCY={EARLIEST_UNRESOLVED_DEPENDENCY}" in section
    assert f"NEXT_OWNER_GO_REQUIRED={NEXT_OWNER_GO_REQUIRED}" in section
    assert "G12_STATUS=CLOSED_LIVE_FLATTEN_PROVABILITY_PROVEN" in section
    assert "MANDATORY_LIVE_METRIC_COUNT=20" in section
    assert "PRIOR_CENSUS_REPORTED_METRIC_COUNT=19" in section
    for field_name in LADDER_FIELDS:
        assert field_name in section
    for metric_name in MANDATORY_LIVE_METRICS:
        assert metric_name in section
    original = text[ladder:start]
    assert "No Testnet, fixture or simulated result may satisfy a Live evidence field." in original


def test_spec_mot_atlas_and_evidence_exist() -> None:
    spec = SPEC.read_text(encoding="utf-8")
    assert (
        "DOCS_TOKEN_SECTION_11_14_LIVE_ORDER_AND_ECONOMIC_EVIDENCE_LADDER_OFFLINE_SURFACE_V1"
        in spec
    )
    assert "SECTION_11_14_AUTHORIZED=false" in spec
    mot = MOT.read_text(encoding="utf-8")
    assert "11.14 OFFLINE_EVIDENCE_LADDER_SURFACE" in mot
    assert "SECTION_11_14_LIVE_ORDER_AND_ECONOMIC_EVIDENCE_LADDER_OFFLINE_SURFACE_V1.md" in mot
    catalog = ATLAS_CATALOG.read_text(encoding="utf-8")
    authority = ATLAS_AUTHORITY.read_text(encoding="utf-8")
    relations = ATLAS_RUNTIME_RELATIONS.read_text(encoding="utf-8")
    assert "ATLAS_AUTHORITY=NONE" in authority
    assert "id: PHASE:section_11_14_offline_evidence_ladder_surface" in catalog
    assert (
        "id: RUNTIME_COMPONENT:section_11_14_live_order_and_economic_evidence_ladder_v1" in catalog
    )
    assert "Does not collect Live evidence" in catalog
    assert "ATLAS_AUTHORITY=NONE" in catalog
    start = relations.find("id: REL:r_section_11_14_offline_surface_follows_g12_closeout")
    assert start >= 0
    block = relations[start : start + 900]
    assert (
        "target: RUNTIME_COMPONENT:g12_canonical_delayed_zero_persist_and_pending_related_observations_v1"
        in block
    )
    assert "ATLAS_AUTHORITY=NONE" in block
    assert EVIDENCE.is_dir()
    verified = verify_manifest_v1(EVIDENCE)
    assert int(verified.get("MANIFEST_VERIFY_RC", 1)) == 0
