"""Persist-lock for canonical delayed-zero persist and P7/P9 closeout."""

from __future__ import annotations

from pathlib import Path

from src.ops.section_11_13_5_g12_canonical_delayed_zero_persist_and_pending_related_observations_v1.constants_v1 import (
    CANONICAL_EVIDENCE_RUN_ID,
    EVALUATOR_PROVENANCE_SHA256,
    EXPECTED_ORIGIN_MAIN_SHA,
    G12_STATUS_CLOSED,
    NEXT_OWNER_GO_IF_G12_CLOSED,
    OWNER_GO,
    P7_OBSERVATION_IDENTITY,
    P9_OBSERVATION_IDENTITY,
    PREDECESSOR_SLICE,
    PROVEN_POS_ID,
    RECORDED_ZERO_OBSERVATION_IDENTITY,
    THIS_SLICE,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.evidence_v1 import (
    verify_manifest_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
SPEC = (
    REPO_ROOT
    / "docs/ops/specs/G12_CANONICAL_DELAYED_ZERO_PERSIST_AND_PENDING_RELATED_OBSERVATIONS_V1.md"
)
MOT = REPO_ROOT / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md"
ATLAS_CATALOG = REPO_ROOT / "docs/system_atlas/entities/catalog.yaml"
ATLAS_AUTHORITY = REPO_ROOT / "docs/system_atlas/ATLAS_AUTHORITY_AND_USAGE.md"
ATLAS_RUNTIME_RELATIONS = REPO_ROOT / "docs/system_atlas/relations/runtime.yaml"
EVIDENCE = (
    REPO_ROOT
    / "evidence/ops"
    / "section_11_13_5_g12_canonical_delayed_zero_persist_and_pending_related_observations_v1"
    / CANONICAL_EVIDENCE_RUN_ID
)
HEADING = "### 11.13.5 G12_CANONICAL_DELAYED_ZERO_PERSIST_AND_PENDING_RELATED_OBSERVATIONS"
LADDER_HEADING = "## 11.14 Live order and economic evidence ladder"
DELAYED_HEADING = "### 11.13.5 G12_DELAYED_POSID_ZERO_ROW_FULL_CONJUNCTION_PROOF_CONTRACT"


def test_runbook_slice_closes_g12_only_via_full_conjunction() -> None:
    text = MASTER_RUNBOOK.read_text(encoding="utf-8")
    start = text.find(HEADING)
    end = text.find(LADDER_HEADING, start)
    delayed = text.find(DELAYED_HEADING)
    assert delayed >= 0
    assert start > delayed
    assert end > start
    section = text[start:end]
    predecessor = text[delayed:start]
    assert f"OWNER_GO={OWNER_GO}" in section
    assert f"THIS_SLICE={THIS_SLICE}" in section
    assert f"PREDECESSOR_SLICE={PREDECESSOR_SLICE}" in section
    assert f"EXPECTED_ORIGIN_MAIN_SHA={EXPECTED_ORIGIN_MAIN_SHA}" in section
    assert f"G12_STATUS={G12_STATUS_CLOSED}" in section
    assert "TARGET_POSITION_ZERO_PROVEN=true" in section
    assert "LIVE_FLATTEN_PROVABILITY_PROVEN=true" in section
    assert "FULL_G12_CONJUNCTION_CURRENTLY_PROVEN=true" in section
    assert "EMPTY_DATA_IS_ZERO=false" in section
    assert "P9_EMPTY_DATA_IS_NOT_TARGET_ZERO=true" in section
    assert "POST_PERFORMED=false" in section
    assert "SECTION_11_14_AUTHORIZED=false" in section
    assert f"NEXT_OWNER_GO_REQUIRED={NEXT_OWNER_GO_IF_G12_CLOSED}" in section
    assert "DELAYED_CONTRACT_TEXT_REWRITTEN=false" in section
    assert "CHOICE_B_EVALUATOR_REWRITTEN=false" in section
    assert f"PROVEN_POS_ID={PROVEN_POS_ID}" in section
    assert f"P5_ZERO_OBSERVATION_IDENTITY={RECORDED_ZERO_OBSERVATION_IDENTITY}" in section
    assert f"P7_OBSERVATION_IDENTITY={P7_OBSERVATION_IDENTITY}" in section
    assert f"P9_OBSERVATION_IDENTITY={P9_OBSERVATION_IDENTITY}" in section
    assert f"EVALUATOR_PROVENANCE_SHA256={EVALUATOR_PROVENANCE_SHA256}" in section
    assert "G12_STATUS=OPEN_LIVE_FLATTEN_PROVABILITY_UNPROVEN" in predecessor
    assert "TARGET_POSITION_ZERO_PROVEN=false" in predecessor


def test_spec_mot_and_evidence_exist() -> None:
    spec = SPEC.read_text(encoding="utf-8")
    assert (
        "DOCS_TOKEN_G12_CANONICAL_DELAYED_ZERO_PERSIST_AND_PENDING_RELATED_OBSERVATIONS_V1" in spec
    )
    assert "SECTION_11_14_AUTHORIZED=false" in spec
    mot = MOT.read_text(encoding="utf-8")
    assert "G12_CANONICAL_DELAYED_ZERO_PERSIST_AND_PENDING_RELATED_OBSERVATIONS" in mot
    assert "G12_CANONICAL_DELAYED_ZERO_PERSIST_AND_PENDING_RELATED_OBSERVATIONS_V1.md" in mot
    assert EVIDENCE.is_dir()
    verified = verify_manifest_v1(EVIDENCE)
    assert int(verified.get("MANIFEST_VERIFY_RC", 1)) == 0


def test_atlas_new_slice_is_navigation_only() -> None:
    catalog = ATLAS_CATALOG.read_text(encoding="utf-8")
    authority = ATLAS_AUTHORITY.read_text(encoding="utf-8")
    relations = ATLAS_RUNTIME_RELATIONS.read_text(encoding="utf-8")
    assert "ATLAS_AUTHORITY=NONE" in authority
    assert (
        "id: PHASE:g12_canonical_delayed_zero_persist_and_pending_related_observations" in catalog
    )
    assert (
        "id: RUNTIME_COMPONENT:g12_canonical_delayed_zero_persist_and_pending_related_observations_v1"
        in catalog
    )
    assert "Does not execute section 11.14" in catalog
    assert "ATLAS_AUTHORITY=NONE" in catalog
    start = relations.find("id: REL:r_g12_canonical_persist_consumes_delayed_conjunction_evaluator")
    assert start >= 0
    block = relations[start : start + 900]
    assert (
        "target: RUNTIME_COMPONENT:g12_delayed_posid_zero_row_full_conjunction_proof_contract_v1"
        in block
    )
    assert "GATE:flatten_execute_authority" not in block
    assert "ATLAS_AUTHORITY=NONE" in block
