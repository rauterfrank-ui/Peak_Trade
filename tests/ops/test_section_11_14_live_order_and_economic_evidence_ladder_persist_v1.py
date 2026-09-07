"""Persist-lock for the §11.14 LIVE_EXECUTION_CODE_EXISTS adjudication."""

from __future__ import annotations

from pathlib import Path

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.evidence_v1 import (
    verify_manifest_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    CANONICAL_CODE_EXISTS_SLICE_HEADING,
    CANONICAL_EVIDENCE_RUN_ID,
    CANONICAL_OFFLINE_SLICE_HEADING,
    CANONICAL_PATH_REACHABLE_SLICE_HEADING,
    CANONICAL_PRIVATE_READ_ONLY_SLICE_HEADING,
    CANONICAL_ORDER_PLAN_OBSERVED_SLICE_HEADING,
    CANONICAL_SUBMIT_ACK_FORENSIC_SLICE_HEADING,
    CANONICAL_SUBMIT_ACK_PROOF_CRITERION_SLICE_HEADING,
    CANONICAL_SUBMIT_ACK_OBSERVED_ADJUDICATION_SLICE_HEADING,
    CANONICAL_FILL_OBSERVED_ADJUDICATION_SLICE_HEADING,
    CANONICAL_FEE_OBSERVED_ADJUDICATION_SLICE_HEADING,
    CANONICAL_POSITION_RECONCILED_ADJUDICATION_SLICE_HEADING,
    CANONICAL_ACCOUNTING_RECONSTRUCTED_ADJUDICATION_SLICE_HEADING,
    CANONICAL_RESTART_RECONSTRUCTED_ADJUDICATION_SLICE_HEADING,
    CANONICAL_RESTART_RECONSTRUCTED_EXHAUSTIVE_CENSUS_SLICE_HEADING,
    CANONICAL_RESTART_HANDOFF_OWNER_BIND_SLICE_HEADING,
    CANONICAL_REQUIRED_FIELD_CAPTURE_SEAM_SLICE_HEADING,
    CANONICAL_ARCHITECTURE_ADJUDICATION_SLICE_HEADING,
    CANONICAL_POS_SEMANTICS_CANONICAL_BINDING_SLICE_HEADING,
    CANONICAL_POS_PRODUCER_SEMANTICS_AND_CONTRACT_SLICE_HEADING,
    CANONICAL_COMPLETE_CAPTURE_SEAM_PROOF_SLICE_HEADING,
    CANONICAL_IMPLEMENTATION_SLICE_HEADING,
    CANONICAL_READER_BIND_SLICE_HEADING,
    CANONICAL_CONTEMPORANEOUS_OBSERVATION_SLICE_HEADING,
    CANONICAL_FUTURE_CAPTURE_WINDOW_SLICE_HEADING,
    CANONICAL_PRODUCTIVE_CAPTURE_OWNER_HOOK_BINDING_SLICE_HEADING,
    CANONICAL_CREATE_PRODUCTIVE_CAPTURE_OWNER_HOOK_SLICE_HEADING,
    CANONICAL_COMPLETE_CONTEMPORANEOUS_CAPTURE_SEAM_SLICE_HEADING,
    CANONICAL_PRODUCTIVE_HOOK_CALLER_BINDING_SLICE_HEADING,
    CANONICAL_COMPLETE_CAPTURE_SEAM_NO_BACKFILL_CONTRACT_SLICE_HEADING,
    CANONICAL_CONTEMPORANEOUS_CAPTURE_RUNTIME_SURFACE_SLICE_HEADING,
    CANONICAL_SECTION_HEADING,
    EARLIEST_UNRESOLVED_DEPENDENCY,
    EXPECTED_ORIGIN_MAIN_SHA,
    HISTORICAL_ACCOUNTING_RECONSTRUCTED_OWNER_GO,
    HISTORICAL_ACCOUNTING_RECONSTRUCTED_RUN_ID,
    HISTORICAL_ACCOUNTING_RECONSTRUCTED_SHA,
    HISTORICAL_FEE_OBSERVED_OWNER_GO,
    HISTORICAL_FEE_OBSERVED_RUN_ID,
    HISTORICAL_FEE_OBSERVED_SHA,
    HISTORICAL_POSITION_RECONCILED_OWNER_GO,
    HISTORICAL_POSITION_RECONCILED_RUN_ID,
    HISTORICAL_POSITION_RECONCILED_SHA,
    HISTORICAL_FILL_OBSERVED_OWNER_GO,
    HISTORICAL_FILL_OBSERVED_RUN_ID,
    HISTORICAL_FILL_OBSERVED_SHA,
    HISTORICAL_FORENSIC_ACK_OWNER_GO,
    HISTORICAL_FORENSIC_ACK_RUN_ID,
    HISTORICAL_IMPLEMENTATION_OWNER_GO,
    HISTORICAL_IMPLEMENTATION_RUN_ID,
    HISTORICAL_IMPLEMENTATION_SHA,
    HISTORICAL_READER_BIND_OWNER_GO,
    HISTORICAL_READER_BIND_RUN_ID,
    HISTORICAL_READER_BIND_SHA,
    HISTORICAL_PROOF_CRITERION_OWNER_GO,
    HISTORICAL_PROOF_CRITERION_RUN_ID,
    HISTORICAL_PROOF_CRITERION_SHA,
    HISTORICAL_RESTART_RECONSTRUCTED_OWNER_GO,
    HISTORICAL_RESTART_RECONSTRUCTED_RUN_ID,
    HISTORICAL_RESTART_RECONSTRUCTED_SHA,
    HISTORICAL_EXHAUSTIVE_CENSUS_OWNER_GO,
    HISTORICAL_EXHAUSTIVE_CENSUS_RUN_ID,
    HISTORICAL_EXHAUSTIVE_CENSUS_SHA,
    HISTORICAL_OWNER_BIND_OWNER_GO,
    HISTORICAL_OWNER_BIND_RUN_ID,
    HISTORICAL_OWNER_BIND_SHA,
    HISTORICAL_REQUIRED_FIELD_CAPTURE_SEAM_OWNER_GO,
    HISTORICAL_REQUIRED_FIELD_CAPTURE_SEAM_RUN_ID,
    HISTORICAL_REQUIRED_FIELD_CAPTURE_SEAM_SHA,
    HISTORICAL_ARCHITECTURE_ADJUDICATION_OWNER_GO,
    HISTORICAL_ARCHITECTURE_ADJUDICATION_RUN_ID,
    HISTORICAL_ARCHITECTURE_ADJUDICATION_SHA,
    HISTORICAL_POS_SEMANTICS_CANONICAL_BINDING_OWNER_GO,
    HISTORICAL_POS_SEMANTICS_CANONICAL_BINDING_RUN_ID,
    HISTORICAL_POS_SEMANTICS_CANONICAL_BINDING_SHA,
    HISTORICAL_POS_PRODUCER_SEMANTICS_AND_CONTRACT_OWNER_GO,
    HISTORICAL_POS_PRODUCER_SEMANTICS_AND_CONTRACT_RUN_ID,
    HISTORICAL_POS_PRODUCER_SEMANTICS_AND_CONTRACT_SHA,
    HISTORICAL_COMPLETE_CAPTURE_SEAM_PROOF_OWNER_GO,
    HISTORICAL_COMPLETE_CAPTURE_SEAM_PROOF_RUN_ID,
    HISTORICAL_COMPLETE_CAPTURE_SEAM_PROOF_SHA,
    HISTORICAL_CONTEMPORANEOUS_OBSERVATION_OWNER_GO,
    HISTORICAL_CONTEMPORANEOUS_OBSERVATION_RUN_ID,
    HISTORICAL_CONTEMPORANEOUS_OBSERVATION_SHA,
    HISTORICAL_FUTURE_CAPTURE_WINDOW_OWNER_GO,
    HISTORICAL_FUTURE_CAPTURE_WINDOW_RUN_ID,
    HISTORICAL_FUTURE_CAPTURE_WINDOW_SHA,
    HISTORICAL_PRODUCTIVE_CAPTURE_OWNER_HOOK_BINDING_OWNER_GO,
    HISTORICAL_PRODUCTIVE_CAPTURE_OWNER_HOOK_BINDING_RUN_ID,
    HISTORICAL_PRODUCTIVE_CAPTURE_OWNER_HOOK_BINDING_SHA,
    HISTORICAL_CREATE_PRODUCTIVE_CAPTURE_OWNER_HOOK_OWNER_GO,
    HISTORICAL_CREATE_PRODUCTIVE_CAPTURE_OWNER_HOOK_RUN_ID,
    HISTORICAL_CREATE_PRODUCTIVE_CAPTURE_OWNER_HOOK_SHA,
    HISTORICAL_COMPLETE_CONTEMPORANEOUS_CAPTURE_SEAM_OWNER_GO,
    HISTORICAL_COMPLETE_CONTEMPORANEOUS_CAPTURE_SEAM_RUN_ID,
    HISTORICAL_COMPLETE_CONTEMPORANEOUS_CAPTURE_SEAM_SHA,
    HISTORICAL_PRODUCTIVE_HOOK_CALLER_BINDING_OWNER_GO,
    HISTORICAL_PRODUCTIVE_HOOK_CALLER_BINDING_RUN_ID,
    HISTORICAL_PRODUCTIVE_HOOK_CALLER_BINDING_SHA,
    HISTORICAL_COMPLETE_CAPTURE_SEAM_NO_BACKFILL_CONTRACT_OWNER_GO,
    HISTORICAL_COMPLETE_CAPTURE_SEAM_NO_BACKFILL_CONTRACT_RUN_ID,
    HISTORICAL_COMPLETE_CAPTURE_SEAM_NO_BACKFILL_CONTRACT_SHA,
    HISTORICAL_CODE_EXISTS_OWNER_GO,
    HISTORICAL_CODE_EXISTS_RUN_ID,
    HISTORICAL_CODE_EXISTS_SHA,
    HISTORICAL_OFFLINE_SURFACE_OWNER_GO,
    HISTORICAL_OFFLINE_SURFACE_RUN_ID,
    HISTORICAL_OFFLINE_SURFACE_SHA,
    HISTORICAL_ORDER_PLAN_OWNER_GO,
    HISTORICAL_ORDER_PLAN_RUN_ID,
    HISTORICAL_ORDER_PLAN_SHA,
    HISTORICAL_PATH_REACHABLE_OWNER_GO,
    HISTORICAL_PATH_REACHABLE_RUN_ID,
    HISTORICAL_PATH_REACHABLE_SHA,
    HISTORICAL_PRIVATE_READ_ONLY_OWNER_GO,
    HISTORICAL_PRIVATE_READ_ONLY_RUN_ID,
    HISTORICAL_PRIVATE_READ_ONLY_SHA,
    HISTORICAL_SUBMIT_ACK_OBSERVED_OWNER_GO,
    HISTORICAL_SUBMIT_ACK_OBSERVED_RUN_ID,
    HISTORICAL_SUBMIT_ACK_OBSERVED_SHA,
    LADDER_FIELDS,
    LAST_CANONICALLY_CLOSED_STEP,
    NEXT_OWNER_GO_REQUIRED,
    OWNER_GO,
    PREDECESSOR_SLICE,
    THIS_SLICE,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
SPEC = REPO_ROOT / "docs/ops/specs/SECTION_11_14_LIVE_EXECUTION_CODE_EXISTS_ADJUDICATION_V1.md"
PATH_REACHABLE_SPEC = (
    REPO_ROOT / "docs/ops/specs/SECTION_11_14_LIVE_EXECUTION_PATH_REACHABLE_ADJUDICATION_V1.md"
)
PRIVATE_READ_ONLY_SPEC = (
    REPO_ROOT / "docs/ops/specs/SECTION_11_14_LIVE_PRIVATE_READ_ONLY_PROVEN_ADJUDICATION_V1.md"
)
ORDER_PLAN_SPEC = (
    REPO_ROOT / "docs/ops/specs/SECTION_11_14_LIVE_ORDER_PLAN_OBSERVED_ADJUDICATION_V1.md"
)
SUBMIT_ACK_FORENSIC_SPEC = (
    REPO_ROOT
    / "docs/ops/specs/SECTION_11_14_LIVE_SUBMIT_ACK_CONTRACT_AND_MUTATION_BOUNDARY_FORENSIC_ADJUDICATION_V1.md"
)
SUBMIT_ACK_PROOF_CRITERION_SPEC = (
    REPO_ROOT / "docs/ops/specs/SECTION_11_14_LIVE_SUBMIT_ACK_OBSERVED_PROOF_CRITERION_V1.md"
)
SUBMIT_ACK_OBSERVED_ADJUDICATION_SPEC = (
    REPO_ROOT / "docs/ops/specs/SECTION_11_14_LIVE_SUBMIT_ACK_OBSERVED_ADJUDICATION_V1.md"
)
FILL_OBSERVED_ADJUDICATION_SPEC = (
    REPO_ROOT / "docs/ops/specs/SECTION_11_14_LIVE_FILL_OBSERVED_ADJUDICATION_V1.md"
)
FEE_OBSERVED_ADJUDICATION_SPEC = (
    REPO_ROOT / "docs/ops/specs/SECTION_11_14_LIVE_FEE_OBSERVED_ADJUDICATION_V1.md"
)
POSITION_RECONCILED_ADJUDICATION_SPEC = (
    REPO_ROOT / "docs/ops/specs/SECTION_11_14_LIVE_POSITION_RECONCILED_ADJUDICATION_V1.md"
)
ACCOUNTING_RECONSTRUCTED_ADJUDICATION_SPEC = (
    REPO_ROOT / "docs/ops/specs/SECTION_11_14_LIVE_ACCOUNTING_RECONSTRUCTED_ADJUDICATION_V1.md"
)
RESTART_RECONSTRUCTED_ADJUDICATION_SPEC = (
    REPO_ROOT / "docs/ops/specs/SECTION_11_14_LIVE_RESTART_RECONSTRUCTED_ADJUDICATION_V1.md"
)
RESTART_RECONSTRUCTED_EXHAUSTIVE_CENSUS_SPEC = (
    REPO_ROOT
    / "docs/ops/specs/SECTION_11_14_LIVE_RESTART_RECONSTRUCTED_EXHAUSTIVE_OFFLINE_CENSUS_V1.md"
)
RESTART_HANDOFF_OWNER_BIND_SPEC = (
    REPO_ROOT
    / "docs/ops/specs/SECTION_11_14_LIVE_RESTART_HANDOFF_OWNER_BIND_AND_RETROACTIVE_SYNTHESIS_REFUSAL_V1.md"
)
REQUIRED_FIELD_CAPTURE_SEAM_SPEC = (
    REPO_ROOT
    / "docs/ops/specs/SECTION_11_14_LIVE_HANDOFF_REQUIRED_FIELD_CAPTURE_SEAM_POS_AND_OWNER_VACANCY_CONTRACT_V1.md"
)
ARCHITECTURE_ADJUDICATION_SPEC = (
    REPO_ROOT
    / "docs/ops/specs/SECTION_11_14_LIVE_DURABLE_PRE_RESTART_HANDOFF_OWNER_AND_CAPTURE_ARCHITECTURE_ADJUDICATION_V1.md"
)
POS_SEMANTICS_CANONICAL_BINDING_SPEC = (
    REPO_ROOT / "docs/ops/specs/SECTION_11_14_LIVE_HANDOFF_POS_SEMANTICS_CANONICAL_BINDING_V1.md"
)
POS_PRODUCER_SEMANTICS_AND_CONTRACT_SPEC = (
    REPO_ROOT
    / "docs/ops/specs/SECTION_11_14_LIVE_HANDOFF_POS_PRODUCER_SEMANTICS_AND_CONTRACT_V1.md"
)
COMPLETE_CAPTURE_SEAM_PROOF_SPEC = (
    REPO_ROOT / "docs/ops/specs/SECTION_11_14_LIVE_HANDOFF_COMPLETE_CAPTURE_SEAM_PROOF_V1.md"
)
IMPLEMENTATION_SPEC = (
    REPO_ROOT
    / "docs/ops/specs/SECTION_11_14_LIVE_HANDOFF_POS_PRODUCER_CAPTURE_RECORD_OWNER_AND_WRITER_IMPLEMENTATION_V1.md"
)
READER_BIND_SPEC = (
    REPO_ROOT
    / "docs/ops/specs/SECTION_11_14_LIVE_HANDOFF_RESTART_READER_PROVENANCE_AND_CONSUMER_BIND_V1.md"
)
OBSERVATION_SPEC = (
    REPO_ROOT
    / "docs/ops/specs/SECTION_11_14_LIVE_RESTART_RECONSTRUCTED_CONTEMPORANEOUS_PRE_RESTART_OBSERVATION_V1.md"
)
CAPTURE_WINDOW_SPEC = (
    REPO_ROOT
    / "docs/ops/specs/SECTION_11_14_LIVE_HANDOFF_FUTURE_AUTHORIZED_CONTEMPORANEOUS_CAPTURE_WINDOW_V1.md"
)
OWNER_HOOK_BINDING_SPEC = (
    REPO_ROOT
    / "docs/ops/specs/SECTION_11_14_LIVE_HANDOFF_PRODUCTIVE_CAPTURE_OWNER_AND_LIFECYCLE_HOOK_BINDING_V1.md"
)
CREATE_OWNER_HOOK_SPEC = (
    REPO_ROOT
    / "docs/ops/specs/SECTION_11_14_LIVE_HANDOFF_CREATE_PRODUCTIVE_CAPTURE_OWNER_AND_LIFECYCLE_HOOK_V1.md"
)
COMPLETE_CONTEMPORANEOUS_CAPTURE_SEAM_SPEC = (
    REPO_ROOT
    / "docs/ops/specs/SECTION_11_14_LIVE_HANDOFF_COMPLETE_CONTEMPORANEOUS_CAPTURE_SEAM_AND_REQUIRED_FIELD_PROVENANCE_V1.md"
)
PRODUCTIVE_HOOK_CALLER_BINDING_SPEC = (
    REPO_ROOT
    / "docs/ops/specs/SECTION_11_14_LIVE_HANDOFF_PRODUCTIVE_CAPTURE_HOOK_CALLER_BINDING_AND_OFFLINE_CALL_PATH_PROOF_V1.md"
)
COMPLETE_CAPTURE_SEAM_NO_BACKFILL_CONTRACT_SPEC = (
    REPO_ROOT
    / "docs/ops/specs/SECTION_11_14_LIVE_HANDOFF_COMPLETE_CAPTURE_SEAM_REQUIRED_FIELD_PROVENANCE_AND_NO_BACKFILL_CONTRACT_V1.md"
)
CONTEMPORANEOUS_CAPTURE_RUNTIME_SURFACE_SPEC = (
    REPO_ROOT
    / "docs/ops/specs/SECTION_11_14_LIVE_HANDOFF_CONTEMPORANEOUS_CAPTURE_RUNTIME_SURFACE_AND_NON_EXECUTION_AUTHORIZATION_BOUNDARY_V1.md"
)
HISTORICAL_SPEC = (
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
CODE_EXISTS_EVIDENCE = (
    REPO_ROOT
    / "evidence/ops"
    / "section_11_14_live_order_and_economic_evidence_ladder_v1"
    / HISTORICAL_CODE_EXISTS_RUN_ID
)
HISTORICAL_EVIDENCE = (
    REPO_ROOT
    / "evidence/ops"
    / "section_11_14_live_order_and_economic_evidence_ladder_v1"
    / HISTORICAL_OFFLINE_SURFACE_RUN_ID
)
PATH_REACHABLE_EVIDENCE = (
    REPO_ROOT
    / "evidence/ops"
    / "section_11_14_live_order_and_economic_evidence_ladder_v1"
    / HISTORICAL_PATH_REACHABLE_RUN_ID
)
PRIVATE_READ_ONLY_EVIDENCE = (
    REPO_ROOT
    / "evidence/ops"
    / "section_11_14_live_order_and_economic_evidence_ladder_v1"
    / HISTORICAL_PRIVATE_READ_ONLY_RUN_ID
)
ORDER_PLAN_EVIDENCE = (
    REPO_ROOT
    / "evidence/ops"
    / "section_11_14_live_order_and_economic_evidence_ladder_v1"
    / HISTORICAL_ORDER_PLAN_RUN_ID
)
FORENSIC_ACK_EVIDENCE = (
    REPO_ROOT
    / "evidence/ops"
    / "section_11_14_live_order_and_economic_evidence_ladder_v1"
    / HISTORICAL_FORENSIC_ACK_RUN_ID
)
PROOF_CRITERION_EVIDENCE = (
    REPO_ROOT
    / "evidence/ops"
    / "section_11_14_live_order_and_economic_evidence_ladder_v1"
    / HISTORICAL_PROOF_CRITERION_RUN_ID
)
SUBMIT_ACK_OBSERVED_EVIDENCE = (
    REPO_ROOT
    / "evidence/ops"
    / "section_11_14_live_order_and_economic_evidence_ladder_v1"
    / HISTORICAL_SUBMIT_ACK_OBSERVED_RUN_ID
)
FILL_OBSERVED_EVIDENCE = (
    REPO_ROOT
    / "evidence/ops"
    / "section_11_14_live_order_and_economic_evidence_ladder_v1"
    / HISTORICAL_FILL_OBSERVED_RUN_ID
)
FEE_OBSERVED_EVIDENCE = (
    REPO_ROOT
    / "evidence/ops"
    / "section_11_14_live_order_and_economic_evidence_ladder_v1"
    / HISTORICAL_FEE_OBSERVED_RUN_ID
)
POSITION_RECONCILED_EVIDENCE = (
    REPO_ROOT
    / "evidence/ops"
    / "section_11_14_live_order_and_economic_evidence_ladder_v1"
    / HISTORICAL_POSITION_RECONCILED_RUN_ID
)
ACCOUNTING_RECONSTRUCTED_EVIDENCE = (
    REPO_ROOT
    / "evidence/ops"
    / "section_11_14_live_order_and_economic_evidence_ladder_v1"
    / HISTORICAL_ACCOUNTING_RECONSTRUCTED_RUN_ID
)
HISTORICAL_RESTART_EVIDENCE = (
    REPO_ROOT
    / "evidence/ops"
    / "section_11_14_live_order_and_economic_evidence_ladder_v1"
    / HISTORICAL_RESTART_RECONSTRUCTED_RUN_ID
)
HISTORICAL_EXHAUSTIVE_EVIDENCE = (
    REPO_ROOT
    / "evidence/ops"
    / "section_11_14_live_order_and_economic_evidence_ladder_v1"
    / HISTORICAL_EXHAUSTIVE_CENSUS_RUN_ID
)
HISTORICAL_OWNER_BIND_EVIDENCE = (
    REPO_ROOT
    / "evidence/ops"
    / "section_11_14_live_order_and_economic_evidence_ladder_v1"
    / HISTORICAL_OWNER_BIND_RUN_ID
)
HISTORICAL_REQUIRED_FIELD_CAPTURE_SEAM_EVIDENCE = (
    REPO_ROOT
    / "evidence/ops"
    / "section_11_14_live_order_and_economic_evidence_ladder_v1"
    / HISTORICAL_REQUIRED_FIELD_CAPTURE_SEAM_RUN_ID
)
HISTORICAL_ARCHITECTURE_ADJUDICATION_EVIDENCE = (
    REPO_ROOT
    / "evidence/ops"
    / "section_11_14_live_order_and_economic_evidence_ladder_v1"
    / HISTORICAL_ARCHITECTURE_ADJUDICATION_RUN_ID
)
HISTORICAL_POS_SEMANTICS_CANONICAL_BINDING_EVIDENCE = (
    REPO_ROOT
    / "evidence/ops"
    / "section_11_14_live_order_and_economic_evidence_ladder_v1"
    / HISTORICAL_POS_SEMANTICS_CANONICAL_BINDING_RUN_ID
)
HISTORICAL_POS_PRODUCER_SEMANTICS_AND_CONTRACT_EVIDENCE = (
    REPO_ROOT
    / "evidence/ops"
    / "section_11_14_live_order_and_economic_evidence_ladder_v1"
    / HISTORICAL_POS_PRODUCER_SEMANTICS_AND_CONTRACT_RUN_ID
)
HISTORICAL_COMPLETE_CAPTURE_SEAM_PROOF_EVIDENCE = (
    REPO_ROOT
    / "evidence/ops"
    / "section_11_14_live_order_and_economic_evidence_ladder_v1"
    / HISTORICAL_COMPLETE_CAPTURE_SEAM_PROOF_RUN_ID
)
HISTORICAL_IMPLEMENTATION_EVIDENCE = (
    REPO_ROOT
    / "evidence/ops"
    / "section_11_14_live_order_and_economic_evidence_ladder_v1"
    / HISTORICAL_IMPLEMENTATION_RUN_ID
)
HISTORICAL_READER_BIND_EVIDENCE = (
    REPO_ROOT
    / "evidence/ops"
    / "section_11_14_live_order_and_economic_evidence_ladder_v1"
    / HISTORICAL_READER_BIND_RUN_ID
)
HISTORICAL_CONTEMPORANEOUS_OBSERVATION_EVIDENCE = (
    REPO_ROOT
    / "evidence/ops"
    / "section_11_14_live_order_and_economic_evidence_ladder_v1"
    / HISTORICAL_CONTEMPORANEOUS_OBSERVATION_RUN_ID
)
HISTORICAL_FUTURE_CAPTURE_WINDOW_EVIDENCE = (
    REPO_ROOT
    / "evidence/ops"
    / "section_11_14_live_order_and_economic_evidence_ladder_v1"
    / HISTORICAL_FUTURE_CAPTURE_WINDOW_RUN_ID
)
HISTORICAL_PRODUCTIVE_CAPTURE_OWNER_HOOK_BINDING_EVIDENCE = (
    REPO_ROOT
    / "evidence/ops"
    / "section_11_14_live_order_and_economic_evidence_ladder_v1"
    / HISTORICAL_PRODUCTIVE_CAPTURE_OWNER_HOOK_BINDING_RUN_ID
)
HISTORICAL_CREATE_PRODUCTIVE_CAPTURE_OWNER_HOOK_EVIDENCE = (
    REPO_ROOT
    / "evidence/ops"
    / "section_11_14_live_order_and_economic_evidence_ladder_v1"
    / HISTORICAL_CREATE_PRODUCTIVE_CAPTURE_OWNER_HOOK_RUN_ID
)
HISTORICAL_COMPLETE_CONTEMPORANEOUS_CAPTURE_SEAM_EVIDENCE = (
    REPO_ROOT
    / "evidence/ops"
    / "section_11_14_live_order_and_economic_evidence_ladder_v1"
    / HISTORICAL_COMPLETE_CONTEMPORANEOUS_CAPTURE_SEAM_RUN_ID
)
HISTORICAL_PRODUCTIVE_HOOK_CALLER_BINDING_EVIDENCE = (
    REPO_ROOT
    / "evidence/ops"
    / "section_11_14_live_order_and_economic_evidence_ladder_v1"
    / HISTORICAL_PRODUCTIVE_HOOK_CALLER_BINDING_RUN_ID
)
HISTORICAL_COMPLETE_CAPTURE_SEAM_NO_BACKFILL_CONTRACT_EVIDENCE = (
    REPO_ROOT
    / "evidence/ops"
    / "section_11_14_live_order_and_economic_evidence_ladder_v1"
    / HISTORICAL_COMPLETE_CAPTURE_SEAM_NO_BACKFILL_CONTRACT_RUN_ID
)
HEADING_11_15 = "## 11.15 Full-autonomy observability and audit trail"


def test_current_slice_constants_target_contemporaneous_capture_runtime_surface_and_non_execution_authorization_boundary() -> (
    None
):
    assert THIS_SLICE == (
        "11.14.LIVE_HANDOFF_CONTEMPORANEOUS_CAPTURE_RUNTIME_SURFACE_AND_"
        "NON_EXECUTION_AUTHORIZATION_BOUNDARY"
    )
    assert PREDECESSOR_SLICE == (
        "11.14.LIVE_HANDOFF_COMPLETE_CAPTURE_SEAM_REQUIRED_FIELD_PROVENANCE_AND_NO_BACKFILL_CONTRACT"
    )
    assert OWNER_GO.endswith(
        "CONTEMPORANEOUS_CAPTURE_RUNTIME_SURFACE_AND_NON_EXECUTION_AUTHORIZATION_BOUNDARY_V1"
    )
    assert EXPECTED_ORIGIN_MAIN_SHA == "f1ce2505cae738ee88d5ce65e2852fcd4a978cb4"
    assert EARLIEST_UNRESOLVED_DEPENDENCY == "LIVE_RESTART_RECONSTRUCTED"
    assert NEXT_OWNER_GO_REQUIRED == "OWNER_GO_FOR_LIVE_RESTART_RECONSTRUCTED"
    assert LAST_CANONICALLY_CLOSED_STEP == (
        "SECTION_11_14_LIVE_HANDOFF_CONTEMPORANEOUS_CAPTURE_RUNTIME_SURFACE_AND_"
        "NON_EXECUTION_AUTHORIZATION_BOUNDARY"
    )
    assert CANONICAL_EVIDENCE_RUN_ID == "20260907T160000Z"
    assert EVIDENCE.name == CANONICAL_EVIDENCE_RUN_ID


def test_runbook_historical_offline_slice_remains_false_for_that_consumed_go() -> None:
    text = MASTER_RUNBOOK.read_text(encoding="utf-8")
    start = text.find(CANONICAL_OFFLINE_SLICE_HEADING)
    ladder = text.find(CANONICAL_SECTION_HEADING)
    end = text.find(CANONICAL_CODE_EXISTS_SLICE_HEADING, start)
    assert ladder >= 0
    assert start > ladder
    assert end > start
    section = text[start:end]
    assert f"OWNER_GO={HISTORICAL_OFFLINE_SURFACE_OWNER_GO}" in section
    assert "THIS_SLICE=11.14.OFFLINE_EVIDENCE_LADDER_SURFACE" in section
    assert f"EXPECTED_ORIGIN_MAIN_SHA={HISTORICAL_OFFLINE_SURFACE_SHA}" in section
    assert "SECTION_11_14_AUTHORIZED=false" in section
    assert "SECTION_11_14_COMPLETE=false" in section
    assert "LIVE_EXECUTION_CODE_EXISTS=false" in section
    assert "LIVE_EXECUTION_PATH_REACHABLE=false" in section
    original = text[ladder:start]
    assert "No Testnet, fixture or simulated result may satisfy a Live evidence field." in original


def test_runbook_code_exists_slice_binds_true_without_later_fields() -> None:
    text = MASTER_RUNBOOK.read_text(encoding="utf-8")
    start = text.find(CANONICAL_CODE_EXISTS_SLICE_HEADING)
    end = text.find(CANONICAL_PATH_REACHABLE_SLICE_HEADING, start)
    if end < 0:
        end = text.find(HEADING_11_15, start)
    assert start >= 0
    assert end > start
    section = text[start:end]
    assert f"OWNER_GO={HISTORICAL_CODE_EXISTS_OWNER_GO}" in section
    assert "THIS_SLICE=11.14.LIVE_EXECUTION_CODE_EXISTS_ADJUDICATION" in section
    assert "PREDECESSOR_SLICE=11.14.OFFLINE_EVIDENCE_LADDER_SURFACE" in section
    assert f"EXPECTED_ORIGIN_MAIN_SHA={HISTORICAL_CODE_EXISTS_SHA}" in section
    assert "SECTION_11_14_AUTHORIZED=false" in section
    assert "SECTION_11_14_COMPLETE=false" in section
    assert "LIVE_EXECUTION_CODE_EXISTS=true" in section
    assert "LIVE_EXECUTION_PATH_REACHABLE=false" in section
    assert "LIVE_PRIVATE_READ_ONLY_PROVEN=false" in section
    assert "POST_PERFORMED=false" in section
    assert "GET_PERFORMED=false" in section
    assert "EARLIEST_UNRESOLVED_DEPENDENCY=LIVE_EXECUTION_PATH_REACHABLE" in section
    assert HISTORICAL_CODE_EXISTS_RUN_ID in section


def test_runbook_path_reachable_slice_binds_true_without_later_fields() -> None:
    text = MASTER_RUNBOOK.read_text(encoding="utf-8")
    start = text.find(CANONICAL_PATH_REACHABLE_SLICE_HEADING)
    end = text.find(CANONICAL_PRIVATE_READ_ONLY_SLICE_HEADING, start)
    if end < 0:
        end = text.find(HEADING_11_15, start)
    assert start >= 0
    assert end > start
    section = text[start:end]
    assert f"OWNER_GO={HISTORICAL_PATH_REACHABLE_OWNER_GO}" in section
    assert "THIS_SLICE=11.14.LIVE_EXECUTION_PATH_REACHABLE_ADJUDICATION" in section
    assert "PREDECESSOR_SLICE=11.14.LIVE_EXECUTION_CODE_EXISTS_ADJUDICATION" in section
    assert f"EXPECTED_ORIGIN_MAIN_SHA={HISTORICAL_PATH_REACHABLE_SHA}" in section
    assert "SECTION_11_14_AUTHORIZED=false" in section
    assert "SECTION_11_14_COMPLETE=false" in section
    assert "LIVE_EXECUTION_CODE_EXISTS=true" in section
    assert "LIVE_EXECUTION_PATH_REACHABLE=true" in section
    assert "LIVE_PRIVATE_READ_ONLY_PROVEN=false" in section
    assert "LIVE_ORDER_PLAN_OBSERVED=false" in section
    assert "POST_PERFORMED=false" in section
    assert "GET_PERFORMED=true" in section
    assert HISTORICAL_PATH_REACHABLE_RUN_ID in section


def test_runbook_private_read_only_slice_binds_true_without_later_fields() -> None:
    text = MASTER_RUNBOOK.read_text(encoding="utf-8")
    start = text.find(CANONICAL_PRIVATE_READ_ONLY_SLICE_HEADING)
    end = text.find(CANONICAL_ORDER_PLAN_OBSERVED_SLICE_HEADING, start)
    if end < 0:
        end = text.find(HEADING_11_15, start)
    assert start >= 0
    assert end > start
    section = text[start:end]
    assert f"OWNER_GO={HISTORICAL_PRIVATE_READ_ONLY_OWNER_GO}" in section
    assert "THIS_SLICE=11.14.LIVE_PRIVATE_READ_ONLY_PROVEN_ADJUDICATION" in section
    assert "PREDECESSOR_SLICE=11.14.LIVE_EXECUTION_PATH_REACHABLE_ADJUDICATION" in section
    assert f"EXPECTED_ORIGIN_MAIN_SHA={HISTORICAL_PRIVATE_READ_ONLY_SHA}" in section
    assert "SECTION_11_14_AUTHORIZED=false" in section
    assert "SECTION_11_14_COMPLETE=false" in section
    assert "LIVE_EXECUTION_CODE_EXISTS=true" in section
    assert "LIVE_EXECUTION_PATH_REACHABLE=true" in section
    assert "LIVE_PRIVATE_READ_ONLY_PROVEN=true" in section
    assert "LIVE_ORDER_PLAN_OBSERVED=false" in section
    assert "LIVE_SUBMIT_ACK_OBSERVED=false" in section
    assert "POST_PERFORMED=false" in section
    assert "GET_PERFORMED=true" in section
    assert "CREDENTIAL_USE=true" in section
    assert "EARLIEST_UNRESOLVED_DEPENDENCY=LIVE_ORDER_PLAN_OBSERVED" in section
    assert HISTORICAL_PRIVATE_READ_ONLY_RUN_ID in section
    for field_name in LADDER_FIELDS:
        assert field_name in section


def test_runbook_order_plan_observed_slice_binds_true_without_later_fields() -> None:
    text = MASTER_RUNBOOK.read_text(encoding="utf-8")
    start = text.find(CANONICAL_ORDER_PLAN_OBSERVED_SLICE_HEADING)
    end = text.find(CANONICAL_SUBMIT_ACK_FORENSIC_SLICE_HEADING, start)
    if end < 0:
        end = text.find(HEADING_11_15, start)
    assert start >= 0
    assert end > start
    section = text[start:end]
    assert HISTORICAL_ORDER_PLAN_OWNER_GO in section
    assert "THIS_SLICE=11.14.LIVE_ORDER_PLAN_OBSERVED_ADJUDICATION" in section
    assert "PREDECESSOR_SLICE=11.14.LIVE_PRIVATE_READ_ONLY_PROVEN_ADJUDICATION" in section
    assert f"EXPECTED_ORIGIN_MAIN_SHA={HISTORICAL_ORDER_PLAN_SHA}" in section
    assert "SECTION_11_14_AUTHORIZED=false" in section
    assert "SECTION_11_14_COMPLETE=false" in section
    assert "LIVE_EXECUTION_CODE_EXISTS=true" in section
    assert "LIVE_EXECUTION_PATH_REACHABLE=true" in section
    assert "LIVE_PRIVATE_READ_ONLY_PROVEN=true" in section
    assert "LIVE_ORDER_PLAN_OBSERVED=true" in section
    assert "LIVE_SUBMIT_ACK_OBSERVED=false" in section
    assert "POST_PERFORMED=false" in section
    assert "POST_USED=false" in section
    assert "SUBMIT_USED=false" in section
    assert "GET_PERFORMED=true" in section
    assert "CREDENTIAL_USE=true" in section
    assert "LIVE_GATE_ACTIVATION_USED=true" in section
    assert "LIVE_GATES_RETURNED_FAIL_CLOSED=true" in section
    assert "EARLIEST_UNRESOLVED_DEPENDENCY=LIVE_SUBMIT_ACK_OBSERVED" in section
    assert "NEXT_OWNER_GO_REQUIRED=OWNER_GO_FOR_EXACT_NEXT_MUTATION" in section
    assert HISTORICAL_ORDER_PLAN_RUN_ID in section
    for field_name in LADDER_FIELDS:
        assert field_name in section


def test_runbook_submit_ack_forensic_slice_binds_case_c_without_ack() -> None:
    text = MASTER_RUNBOOK.read_text(encoding="utf-8")
    start = text.find(CANONICAL_SUBMIT_ACK_FORENSIC_SLICE_HEADING)
    end = text.find(CANONICAL_SUBMIT_ACK_PROOF_CRITERION_SLICE_HEADING, start)
    if end < 0:
        end = text.find(HEADING_11_15, start)
    assert start >= 0
    assert end > start
    section = text[start:end]
    assert HISTORICAL_FORENSIC_ACK_OWNER_GO in section
    assert (
        "THIS_SLICE=11.14.LIVE_SUBMIT_ACK_CONTRACT_AND_MUTATION_BOUNDARY_FORENSIC_ADJUDICATION"
        in section
    )
    assert "PREDECESSOR_SLICE=11.14.LIVE_ORDER_PLAN_OBSERVED_ADJUDICATION" in section
    assert f"EXPECTED_ORIGIN_MAIN_SHA={HISTORICAL_PROOF_CRITERION_SHA}" in section
    assert "SECTION_11_14_AUTHORIZED=false" in section
    assert "SECTION_11_14_COMPLETE=false" in section
    assert "LIVE_ORDER_PLAN_OBSERVED=true" in section
    assert "LIVE_SUBMIT_ACK_OBSERVED=false" in section
    assert "CASE_ADJUDICATION=CASE_C_CANONICAL_SEMANTIC_GAP" in section
    assert "AUTHORIZED_PRODUCTIVE_SUBMIT_COUNT_MAX=1" in section
    assert "RETRY_DEFAULT=false" in section
    assert "SECOND_SUBMIT_DEFAULT=false" in section
    assert "POST_PERFORMED=false" in section
    assert "GET_PERFORMED=false" in section
    assert HISTORICAL_FORENSIC_ACK_RUN_ID in section
    for field_name in LADDER_FIELDS:
        assert field_name in section


def test_runbook_submit_ack_proof_criterion_slice_binds_case_a_without_ack() -> None:
    text = MASTER_RUNBOOK.read_text(encoding="utf-8")
    start = text.find(CANONICAL_SUBMIT_ACK_PROOF_CRITERION_SLICE_HEADING)
    end = text.find(CANONICAL_SUBMIT_ACK_OBSERVED_ADJUDICATION_SLICE_HEADING, start)
    if end < 0:
        end = text.find(HEADING_11_15, start)
    assert start >= 0
    assert end > start
    section = text[start:end]
    assert HISTORICAL_PROOF_CRITERION_OWNER_GO in section
    assert "THIS_SLICE=11.14.LIVE_SUBMIT_ACK_OBSERVED_PROOF_CRITERION" in section
    assert (
        "PREDECESSOR_SLICE=11.14.LIVE_SUBMIT_ACK_CONTRACT_AND_MUTATION_BOUNDARY_FORENSIC_ADJUDICATION"
        in section
    )
    assert f"EXPECTED_ORIGIN_MAIN_SHA={HISTORICAL_PROOF_CRITERION_SHA}" in section
    assert "SECTION_11_14_AUTHORIZED=false" in section
    assert "SECTION_11_14_COMPLETE=false" in section
    assert "LIVE_SUBMIT_ACK_OBSERVED=false" in section
    assert "CASE_ADJUDICATION=CASE_A_READY_FOR_EXACT_SINGLE_POST_OWNER_GO" in section
    assert "LIVE_SUBMIT_ACK_OBSERVED_PRODUCER_BOUND=true" in section
    assert "LIVE_SUBMIT_ACK_PROOF_CRITERION_BOUND=true" in section
    assert "HTTP_STATUS_REQUIRED=200" in section
    assert "TOP_LEVEL_CODE_REQUIRED=0" in section
    assert "EXACTLY_ONE_DATA_ROW_REQUIRED=true" in section
    assert "SCODE_0_REQUIRED=true" in section
    assert "NONEMPTY_ORDID_REQUIRED=true" in section
    assert "RETURNED_CLORDID_REQUIRED=true" in section
    assert "RETURNED_CLORDID_MUST_EQUAL_SENT=true" in section
    assert "READ_ONLY_RECON_IS_NOT_SYNCHRONOUS_ACK=true" in section
    assert "POST_PERFORMED=false" in section
    assert "NEXT_OWNER_GO_REQUIRED=OWNER_GO_FOR_EXACT_SINGLE_LIVE_SUBMIT_POST" in section
    assert HISTORICAL_PROOF_CRITERION_RUN_ID in section
    for field_name in LADDER_FIELDS:
        assert field_name in section


def test_runbook_submit_ack_observed_adjudication_slice_binds_ack_without_fill() -> None:
    text = MASTER_RUNBOOK.read_text(encoding="utf-8")
    start = text.find(CANONICAL_SUBMIT_ACK_OBSERVED_ADJUDICATION_SLICE_HEADING)
    end = text.find(CANONICAL_FILL_OBSERVED_ADJUDICATION_SLICE_HEADING, start)
    if end < 0:
        end = text.find(HEADING_11_15, start)
    assert start >= 0
    assert end > start
    section = text[start:end]
    assert HISTORICAL_SUBMIT_ACK_OBSERVED_OWNER_GO in section
    assert "THIS_SLICE=11.14.LIVE_SUBMIT_ACK_OBSERVED_ADJUDICATION" in section
    assert "PREDECESSOR_SLICE=11.14.LIVE_SUBMIT_ACK_OBSERVED_PROOF_CRITERION" in section
    assert f"EXPECTED_ORIGIN_MAIN_SHA={HISTORICAL_SUBMIT_ACK_OBSERVED_SHA}" in section
    assert "SECTION_11_14_AUTHORIZED=false" in section
    assert "SECTION_11_14_COMPLETE=false" in section
    assert "LIVE_SUBMIT_ACK_OBSERVED=true" in section
    assert "LIVE_FILL_OBSERVED=false" in section
    assert "CASE_ADJUDICATION=CASE_LIVE_SUBMIT_ACK_OBSERVED_FILL_INELIGIBLE" in section
    assert "POST_PERFORMED=true" in section
    assert "SUBMIT_COUNT=1" in section
    assert "RETRY_USED=false" in section
    assert "SECOND_SUBMIT_USED=false" in section
    assert "ACK_SOURCE_KIND=GOVERNED_CURRENT_LIVE_POST" in section
    assert "NEXT_OWNER_GO_REQUIRED=OWNER_GO_FOR_LIVE_FILL_OBSERVED" in section
    assert HISTORICAL_SUBMIT_ACK_OBSERVED_RUN_ID in section
    for field_name in LADDER_FIELDS:
        assert field_name in section


def test_runbook_fill_observed_adjudication_slice_binds_fill_without_fee() -> None:
    text = MASTER_RUNBOOK.read_text(encoding="utf-8")
    start = text.find(CANONICAL_FILL_OBSERVED_ADJUDICATION_SLICE_HEADING)
    end = text.find(CANONICAL_FEE_OBSERVED_ADJUDICATION_SLICE_HEADING, start)
    if end < 0:
        end = text.find(HEADING_11_15, start)
    assert start >= 0
    assert end > start
    section = text[start:end]
    assert HISTORICAL_FILL_OBSERVED_OWNER_GO in section
    assert "THIS_SLICE=11.14.LIVE_FILL_OBSERVED_ADJUDICATION" in section
    assert "PREDECESSOR_SLICE=11.14.LIVE_SUBMIT_ACK_OBSERVED_ADJUDICATION" in section
    assert f"EXPECTED_ORIGIN_MAIN_SHA={HISTORICAL_FILL_OBSERVED_SHA}" in section
    assert "SECTION_11_14_AUTHORIZED=false" in section
    assert "SECTION_11_14_COMPLETE=false" in section
    assert "LIVE_SUBMIT_ACK_OBSERVED=true" in section
    assert "LIVE_FILL_OBSERVED=true" in section
    assert "LIVE_FEE_OBSERVED=false" in section
    assert "FULL_FILL_OBSERVED=true" in section
    assert "PARTIAL_FILL_OBSERVED=false" in section
    assert "CASE_ADJUDICATION=CASE_LIVE_FILL_OBSERVED_FEE_INELIGIBLE" in section
    assert "POST_PERFORMED=false" in section
    assert "GET_PERFORMED=true" in section
    assert "RETRY_USED=false" in section
    assert "SECOND_SUBMIT_USED=false" in section
    assert "FILL_SOURCE_KIND=GOVERNED_CURRENT_PRIVATE_GET" in section
    assert "BOUND_ORDID=3893505043080286208" in section
    assert "NEXT_OWNER_GO_REQUIRED=OWNER_GO_FOR_LIVE_FEE_OBSERVED" in section
    assert HISTORICAL_FILL_OBSERVED_RUN_ID in section
    for field_name in LADDER_FIELDS:
        assert field_name in section


def test_runbook_fee_observed_adjudication_slice_binds_fee_without_position() -> None:
    text = MASTER_RUNBOOK.read_text(encoding="utf-8")
    start = text.find(CANONICAL_FEE_OBSERVED_ADJUDICATION_SLICE_HEADING)
    end = text.find(CANONICAL_POSITION_RECONCILED_ADJUDICATION_SLICE_HEADING, start)
    if end < 0:
        end = text.find(HEADING_11_15, start)
    assert start >= 0
    assert end > start
    section = text[start:end]
    assert HISTORICAL_FEE_OBSERVED_OWNER_GO in section
    assert "THIS_SLICE=11.14.LIVE_FEE_OBSERVED_ADJUDICATION" in section
    assert "PREDECESSOR_SLICE=11.14.LIVE_FILL_OBSERVED_ADJUDICATION" in section
    assert f"EXPECTED_ORIGIN_MAIN_SHA={HISTORICAL_FEE_OBSERVED_SHA}" in section
    assert "SECTION_11_14_AUTHORIZED=false" in section
    assert "SECTION_11_14_COMPLETE=false" in section
    assert "LIVE_FILL_OBSERVED=true" in section
    assert "LIVE_FEE_OBSERVED=true" in section
    assert "LIVE_POSITION_RECONCILED=false" in section
    assert "CASE_ADJUDICATION=CASE_LIVE_FEE_OBSERVED_POSITION_INELIGIBLE" in section
    assert "POST_PERFORMED=false" in section
    assert "GET_PERFORMED=true" in section
    assert "RETRY_USED=false" in section
    assert "SECOND_SUBMIT_USED=false" in section
    assert "FEE_SOURCE_KIND=GOVERNED_CURRENT_PRIVATE_GET" in section
    assert "BOUND_ORDID=3893505043080286208" in section
    assert "RAW_FEE_IF_OBSERVED=-0.000374" in section
    assert "RAW_FEE_CCY_IF_OBSERVED=USDC" in section
    assert "NEXT_OWNER_GO_REQUIRED=OWNER_GO_FOR_LIVE_POSITION_RECONCILED" in section
    assert HISTORICAL_FEE_OBSERVED_RUN_ID in section
    for field_name in LADDER_FIELDS:
        assert field_name in section


def test_runbook_position_reconciled_adjudication_slice_binds_position_without_accounting() -> None:
    text = MASTER_RUNBOOK.read_text(encoding="utf-8")
    start = text.find(CANONICAL_POSITION_RECONCILED_ADJUDICATION_SLICE_HEADING)
    end = text.find(CANONICAL_ACCOUNTING_RECONSTRUCTED_ADJUDICATION_SLICE_HEADING, start)
    if end < 0:
        end = text.find(HEADING_11_15, start)
    assert start >= 0
    assert end > start
    section = text[start:end]
    assert HISTORICAL_POSITION_RECONCILED_OWNER_GO in section
    assert "THIS_SLICE=11.14.LIVE_POSITION_RECONCILED_ADJUDICATION" in section
    assert "PREDECESSOR_SLICE=11.14.LIVE_FEE_OBSERVED_ADJUDICATION" in section
    assert f"EXPECTED_ORIGIN_MAIN_SHA={HISTORICAL_POSITION_RECONCILED_SHA}" in section
    assert "SECTION_11_14_AUTHORIZED=false" in section
    assert "SECTION_11_14_COMPLETE=false" in section
    assert "LIVE_FEE_OBSERVED=true" in section
    assert "LIVE_POSITION_RECONCILED=true" in section
    assert "LIVE_ACCOUNTING_RECONSTRUCTED=false" in section
    assert "CASE_ADJUDICATION=CASE_LIVE_POSITION_RECONCILED_ACCOUNTING_INELIGIBLE" in section
    assert "POST_PERFORMED=false" in section
    assert "GET_PERFORMED=true" in section
    assert "RETRY_USED=false" in section
    assert "SECOND_SUBMIT_USED=false" in section
    assert "POSITION_SOURCE_KIND=GOVERNED_CURRENT_PRIVATE_GET" in section
    assert "BOUND_ORDID=3893505043080286208" in section
    assert "RAW_POSITION_QTY_IF_OBSERVED=1" in section
    assert "RAW_POS_ID_IF_OBSERVED=3891385768441942017" in section
    assert "EMPTY_DATA_IS_ZERO=false" in section
    assert "NEXT_OWNER_GO_REQUIRED=OWNER_GO_FOR_LIVE_ACCOUNTING_RECONSTRUCTED" in section
    assert HISTORICAL_POSITION_RECONCILED_RUN_ID in section
    for field_name in LADDER_FIELDS:
        assert field_name in section


def test_runbook_accounting_reconstructed_adjudication_slice_binds_accounting_without_restart() -> (
    None
):
    text = MASTER_RUNBOOK.read_text(encoding="utf-8")
    start = text.find(CANONICAL_ACCOUNTING_RECONSTRUCTED_ADJUDICATION_SLICE_HEADING)
    end = text.find(CANONICAL_RESTART_RECONSTRUCTED_ADJUDICATION_SLICE_HEADING, start)
    if end < 0:
        end = text.find(HEADING_11_15, start)
    assert start >= 0
    assert end > start
    section = text[start:end]
    assert HISTORICAL_ACCOUNTING_RECONSTRUCTED_OWNER_GO in section
    assert "THIS_SLICE=11.14.LIVE_ACCOUNTING_RECONSTRUCTED_ADJUDICATION" in section
    assert "PREDECESSOR_SLICE=11.14.LIVE_POSITION_RECONCILED_ADJUDICATION" in section
    assert f"EXPECTED_ORIGIN_MAIN_SHA={HISTORICAL_ACCOUNTING_RECONSTRUCTED_SHA}" in section
    assert "SECTION_11_14_AUTHORIZED=false" in section
    assert "SECTION_11_14_COMPLETE=false" in section
    assert "LIVE_POSITION_RECONCILED=true" in section
    assert "LIVE_ACCOUNTING_RECONSTRUCTED=true" in section
    assert "LIVE_RESTART_RECONSTRUCTED=false" in section
    assert "CASE_ADJUDICATION=CASE_LIVE_ACCOUNTING_RECONSTRUCTED_RESTART_INELIGIBLE" in section
    assert "POST_PERFORMED=false" in section
    assert "GET_PERFORMED=false" in section
    assert "PRIVATE_GET_USED=false" in section
    assert "CREDENTIAL_USE=false" in section
    assert "RETRY_USED=false" in section
    assert "SECOND_SUBMIT_USED=false" in section
    assert "ACCOUNTING_SOURCE_KIND=GOVERNED_PERSISTED_IDENTITY_BOUND_LIVE_ECONOMIC_PATH" in section
    assert "BOUND_ORDID=3893505043080286208" in section
    assert "ACCOUNTING_RESULT=-0.000374" in section
    assert "ACCOUNTING_RESULT_UNIT=USDC" in section
    assert "ACCOUNTING_RESIDUAL=0" in section
    assert "ACCOUNTING_TOLERANCE_AUTHORITY=EXACT_DECIMAL_EQUALITY_NO_INVENTED_TOLERANCE" in section
    assert NEXT_OWNER_GO_REQUIRED == "OWNER_GO_FOR_LIVE_RESTART_RECONSTRUCTED"
    assert "NEXT_OWNER_GO_REQUIRED=OWNER_GO_FOR_LIVE_RESTART_RECONSTRUCTED" in section
    assert HISTORICAL_ACCOUNTING_RECONSTRUCTED_RUN_ID in section
    for field_name in LADDER_FIELDS:
        assert field_name in section


def test_runbook_restart_reconstructed_adjudication_slice_binds_fail_closed() -> None:
    text = MASTER_RUNBOOK.read_text(encoding="utf-8")
    start = text.find(CANONICAL_RESTART_RECONSTRUCTED_ADJUDICATION_SLICE_HEADING)
    end = text.find(CANONICAL_RESTART_RECONSTRUCTED_EXHAUSTIVE_CENSUS_SLICE_HEADING, start)
    if end < 0:
        end = text.find(HEADING_11_15, start)
    assert start >= 0
    assert end > start
    section = text[start:end]
    assert HISTORICAL_RESTART_RECONSTRUCTED_OWNER_GO in section
    assert "THIS_SLICE=11.14.LIVE_RESTART_RECONSTRUCTED_ADJUDICATION" in section
    assert "PREDECESSOR_SLICE=11.14.LIVE_ACCOUNTING_RECONSTRUCTED_ADJUDICATION" in section
    assert f"EXPECTED_ORIGIN_MAIN_SHA={HISTORICAL_RESTART_RECONSTRUCTED_SHA}" in section
    assert "SECTION_11_14_AUTHORIZED=false" in section
    assert "SECTION_11_14_COMPLETE=false" in section
    assert "LIVE_ACCOUNTING_RECONSTRUCTED=true" in section
    assert "LIVE_RESTART_RECONSTRUCTED=false" in section
    assert "LIVE_AUTONOMOUS_RECOVERY_OBSERVED=false" in section
    assert (
        "CASE_ADJUDICATION=CASE_LIVE_RESTART_RECONSTRUCTED_FAIL_CLOSED_MISSING_DURABLE_HANDOFF"
        in section
    )
    assert "POST_PERFORMED=false" in section
    assert "GET_PERFORMED=false" in section
    assert "PRIVATE_GET_USED=false" in section
    assert "CREDENTIAL_USE=false" in section
    assert "RESTART_EXECUTION=false" in section
    assert "EARLIEST_MISSING_FACT=DURABLE_LIVE_PRE_RESTART_HANDOFF" in section
    assert "NEXT_OWNER_GO_REQUIRED=OWNER_GO_FOR_LIVE_RESTART_RECONSTRUCTED" in section
    assert HISTORICAL_RESTART_RECONSTRUCTED_RUN_ID in section
    for field_name in LADDER_FIELDS:
        assert field_name in section


def test_runbook_restart_reconstructed_exhaustive_census_slice_binds_fail_closed() -> None:
    text = MASTER_RUNBOOK.read_text(encoding="utf-8")
    start = text.find(CANONICAL_RESTART_RECONSTRUCTED_EXHAUSTIVE_CENSUS_SLICE_HEADING)
    end = text.find(CANONICAL_RESTART_HANDOFF_OWNER_BIND_SLICE_HEADING, start)
    if end < 0:
        end = text.find(HEADING_11_15, start)
    assert start >= 0
    assert end > start
    section = text[start:end]
    assert HISTORICAL_EXHAUSTIVE_CENSUS_OWNER_GO in section
    assert "THIS_SLICE=11.14.LIVE_RESTART_RECONSTRUCTED_EXHAUSTIVE_OFFLINE_CENSUS" in section
    assert "PREDECESSOR_SLICE=11.14.LIVE_RESTART_RECONSTRUCTED_ADJUDICATION" in section
    assert f"EXPECTED_ORIGIN_MAIN_SHA={HISTORICAL_EXHAUSTIVE_CENSUS_SHA}" in section
    assert "SECTION_11_14_AUTHORIZED=false" in section
    assert "SECTION_11_14_COMPLETE=false" in section
    assert "LIVE_ACCOUNTING_RECONSTRUCTED=true" in section
    assert "LIVE_RESTART_RECONSTRUCTED=false" in section
    assert "LIVE_AUTONOMOUS_RECOVERY_OBSERVED=false" in section
    assert (
        "CASE_ADJUDICATION=CASE_LIVE_RESTART_RECONSTRUCTED_FAIL_CLOSED_MISSING_DURABLE_HANDOFF"
        in section
    )
    assert "CASE_B_NOT_PROVEN_CONTRACT_CLOSED=true" in section
    assert "POST_PERFORMED=false" in section
    assert "GET_PERFORMED=false" in section
    assert "PRIVATE_GET_USED=false" in section
    assert "CREDENTIAL_USE=false" in section
    assert "RESTART_EXECUTION=false" in section
    assert "EARLIEST_MISSING_FACT=DURABLE_LIVE_PRE_RESTART_HANDOFF" in section
    assert (
        "FUTURE_MINIMUM_OPERATION=PERSIST_IDENTITY_BOUND_PEAK_TRADE_DURABLE_PRE_RESTART_HANDOFF"
        in section
    )
    assert "RUNTIME_CHANGE_REQUIRES_SEPARATE_OWNER_SCOPE=true" in section
    assert NEXT_OWNER_GO_REQUIRED in section
    assert HISTORICAL_EXHAUSTIVE_CENSUS_RUN_ID in section
    for field_name in LADDER_FIELDS:
        assert field_name in section


def test_runbook_restart_handoff_owner_bind_slice_binds_owner_none() -> None:
    text = MASTER_RUNBOOK.read_text(encoding="utf-8")
    start = text.find(CANONICAL_RESTART_HANDOFF_OWNER_BIND_SLICE_HEADING)
    end = text.find(CANONICAL_REQUIRED_FIELD_CAPTURE_SEAM_SLICE_HEADING, start)
    if end < 0:
        end = text.find(HEADING_11_15, start)
    assert start >= 0
    assert end > start
    section = text[start:end]
    assert HISTORICAL_OWNER_BIND_OWNER_GO in section
    assert (
        "THIS_SLICE=11.14.LIVE_RESTART_HANDOFF_OWNER_BIND_AND_RETROACTIVE_SYNTHESIS_REFUSAL"
        in section
    )
    assert "PREDECESSOR_SLICE=11.14.LIVE_RESTART_RECONSTRUCTED_EXHAUSTIVE_OFFLINE_CENSUS" in section
    assert f"EXPECTED_ORIGIN_MAIN_SHA={HISTORICAL_OWNER_BIND_SHA}" in section
    assert "SECTION_11_14_AUTHORIZED=false" in section
    assert "SECTION_11_14_COMPLETE=false" in section
    assert "LIVE_ACCOUNTING_RECONSTRUCTED=true" in section
    assert "LIVE_RESTART_RECONSTRUCTED=false" in section
    assert "SECTION_11_14_LIVE_HANDOFF_OWNER_CURRENT=NONE" in section
    assert "SECTION_11_14_LIVE_HANDOFF_OWNER_BOUND=false" in section
    assert "SECTION_11_14_LIVE_HANDOFF_WRITER_PRESENT=false" in section
    assert "RETROACTIVE_HANDOFF_SYNTHESIS_ALLOWED=false" in section
    assert "ACCOUNTING_ONLY_IS_NOT_RESTART=true" in section
    assert "VENUE_GET_COPY_IS_NOT_CONTEMPORANEOUS_HANDOFF=true" in section
    assert "POST_HOC_IDENTITY_MATCH_DOES_NOT_PROVE_PRE_RESTART_CAPTURE=true" in section
    assert "HISTORICAL_LIVE_RESTART_HANDOFF_STATUS=UNPROVABLE_WITHOUT_CONTEMPORANEOUS_CAPTURE" in (
        section
    )
    assert "CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_HANDOFF_OBSERVED=false" in section
    assert "A1_WAL_AS_LIVE_HANDOFF_ALLOWED=false" in section
    assert "POST_PERFORMED=false" in section
    assert "GET_PERFORMED=false" in section
    assert "RESTART_EXECUTION=false" in section
    assert NEXT_OWNER_GO_REQUIRED in section
    assert HISTORICAL_OWNER_BIND_RUN_ID in section
    for field_name in LADDER_FIELDS:
        assert field_name in section


def test_runbook_required_field_capture_seam_slice_binds_pos_unproven() -> None:
    text = MASTER_RUNBOOK.read_text(encoding="utf-8")
    start = text.find(CANONICAL_REQUIRED_FIELD_CAPTURE_SEAM_SLICE_HEADING)
    end = text.find(CANONICAL_ARCHITECTURE_ADJUDICATION_SLICE_HEADING, start)
    if end < 0:
        end = text.find(HEADING_11_15, start)
    assert start >= 0
    assert end > start
    section = text[start:end]
    assert HISTORICAL_REQUIRED_FIELD_CAPTURE_SEAM_OWNER_GO in section
    assert (
        "THIS_SLICE=11.14.LIVE_HANDOFF_REQUIRED_FIELD_CAPTURE_SEAM_POS_AND_OWNER_VACANCY_CONTRACT"
        in section
    )
    assert (
        "PREDECESSOR_SLICE=11.14.LIVE_RESTART_HANDOFF_OWNER_BIND_AND_RETROACTIVE_SYNTHESIS_REFUSAL"
        in section
    )
    assert f"EXPECTED_ORIGIN_MAIN_SHA={HISTORICAL_REQUIRED_FIELD_CAPTURE_SEAM_SHA}" in section
    assert "SECTION_11_14_AUTHORIZED=false" in section
    assert "SECTION_11_14_COMPLETE=false" in section
    assert "LIVE_ACCOUNTING_RECONSTRUCTED=true" in section
    assert "LIVE_RESTART_RECONSTRUCTED=false" in section
    assert "POS_SEMANTICS=UNPROVEN" in section
    assert "COMPLETE_CAPTURE_SEAM=UNPROVEN" in section
    assert "EARLIEST_COMPLETE_HANDOFF_CAPTURE_MOMENT=NONE" in section
    assert "EARLIEST_COMPLETE_HANDOFF_CAPTURE_PROVEN=false" in section
    assert "SECTION_11_14_LIVE_HANDOFF_OWNER_CURRENT=NONE" in section
    assert "OWNER_VACANCY_CONTRACT_STATUS=BOUND_CAPTURE_SEAM_UNPROVEN" in section
    assert "NEW_OWNER_REQUIRED=true" in section
    assert "LATER_WRITER_CLAIMED_POSSIBLE=false" in section
    assert "PRODUCTIVE_WRITER_JOIN_CREATED=false" in section
    assert "PRODUCTIVE_READER_JOIN_CREATED=false" in section
    assert "RETROACTIVE_HANDOFF_SYNTHESIS_ALLOWED=false" in section
    assert "POST_PERFORMED=false" in section
    assert "GET_PERFORMED=false" in section
    assert "RESTART_EXECUTION=false" in section
    assert NEXT_OWNER_GO_REQUIRED in section
    assert HISTORICAL_REQUIRED_FIELD_CAPTURE_SEAM_RUN_ID in section
    for field_name in LADDER_FIELDS:
        assert field_name in section


def test_runbook_architecture_adjudication_slice_binds_fail_closed_dag() -> None:
    text = MASTER_RUNBOOK.read_text(encoding="utf-8")
    start = text.find(CANONICAL_ARCHITECTURE_ADJUDICATION_SLICE_HEADING)
    end = text.find(CANONICAL_POS_SEMANTICS_CANONICAL_BINDING_SLICE_HEADING, start)
    assert start >= 0
    assert end > start
    section = text[start:end]
    assert HISTORICAL_ARCHITECTURE_ADJUDICATION_OWNER_GO in section
    assert (
        "THIS_SLICE=11.14.LIVE_DURABLE_PRE_RESTART_HANDOFF_OWNER_AND_CAPTURE_ARCHITECTURE_ADJUDICATION"
        in section
    )
    assert (
        "PREDECESSOR_SLICE=11.14.LIVE_HANDOFF_REQUIRED_FIELD_CAPTURE_SEAM_POS_AND_OWNER_VACANCY_CONTRACT"
        in section
    )
    assert f"EXPECTED_ORIGIN_MAIN_SHA={HISTORICAL_ARCHITECTURE_ADJUDICATION_SHA}" in section
    assert "SECTION_11_14_AUTHORIZED=false" in section
    assert "SECTION_11_14_COMPLETE=false" in section
    assert "LIVE_ACCOUNTING_RECONSTRUCTED=true" in section
    assert "LIVE_RESTART_RECONSTRUCTED=false" in section
    assert "POS_SEMANTICS=UNPROVEN" in section
    assert "COMPLETE_CAPTURE_SEAM=UNPROVEN" in section
    assert "EARLIEST_COMPLETE_HANDOFF_CAPTURE_MOMENT=NONE" in section
    assert "EARLIEST_COMPLETE_HANDOFF_CAPTURE_PROVEN=false" in section
    assert "SECTION_11_14_LIVE_HANDOFF_OWNER_CURRENT=NONE" in section
    assert (
        "PROPOSED_FIRST_OWNER_ADJUDICATION=ELIGIBLE_AS_FIRST_LOGICAL_OWNER_ID_NOT_PRODUCTIVELY_BOUND"
        in section
    )
    assert "FIRST_OWNER_PRODUCTIVELY_BOUND=false" in section
    assert "ARCHITECTURE_ADJUDICATION_COMPLETE=true" in section
    assert "IMPLEMENTATION_AUTHORIZED=false" in section
    assert "STEP_29P_HANDOFF_RELATION=ORTHOGONAL_TO_SECTION_11_14_LIVE_CANARY_HANDOFF" in section
    assert "ADMISSION_TRUE=false" in section
    assert "SUPERVISOR_ACTIVATED=false" in section
    assert "RETROACTIVE_HANDOFF_SYNTHESIS_ALLOWED=false" in section
    assert "POST_PERFORMED=false" in section
    assert "GET_PERFORMED=false" in section
    assert "RESTART_EXECUTION=false" in section
    assert NEXT_OWNER_GO_REQUIRED in section
    assert HISTORICAL_ARCHITECTURE_ADJUDICATION_RUN_ID in section
    for field_name in LADDER_FIELDS:
        assert field_name in section


def test_runbook_pos_semantics_canonical_binding_slice_binds_gap_contract() -> None:
    text = MASTER_RUNBOOK.read_text(encoding="utf-8")
    start = text.find(CANONICAL_POS_SEMANTICS_CANONICAL_BINDING_SLICE_HEADING)
    end = text.find(CANONICAL_POS_PRODUCER_SEMANTICS_AND_CONTRACT_SLICE_HEADING, start)
    assert start >= 0
    assert end > start
    section = text[start:end]
    assert HISTORICAL_POS_SEMANTICS_CANONICAL_BINDING_OWNER_GO in section
    assert "THIS_SLICE=11.14.LIVE_HANDOFF_POS_SEMANTICS_CANONICAL_BINDING" in section
    assert (
        "PREDECESSOR_SLICE=11.14.LIVE_DURABLE_PRE_RESTART_HANDOFF_OWNER_AND_CAPTURE_ARCHITECTURE_ADJUDICATION"
        in section
    )
    assert f"EXPECTED_ORIGIN_MAIN_SHA={HISTORICAL_POS_SEMANTICS_CANONICAL_BINDING_SHA}" in section
    assert "SECTION_11_14_AUTHORIZED=false" in section
    assert "SECTION_11_14_COMPLETE=false" in section
    assert "LIVE_ACCOUNTING_RECONSTRUCTED=true" in section
    assert "LIVE_RESTART_RECONSTRUCTED=false" in section
    assert "POS_SEMANTICS=UNPROVEN" in section
    assert "POS_SEMANTICS_CAN_BE_BOUND_FROM_EXISTING_AUTHORITY=false" in section
    assert "NEW_CONTEMPORANEOUS_POS_PRODUCER_REQUIRED=true" in section
    assert "POS_ACCEPTABLE_PRODUCER_COUNT=0" in section
    assert "POS_UNPROVEN_PRODUCER_COUNT=0" in section
    assert "TOKEN_NAME_IDENTITY_IS_NOT_SEMANTIC_IDENTITY=true" in section
    assert "COMPLETE_CAPTURE_SEAM=UNPROVEN" in section
    assert "EARLIEST_COMPLETE_HANDOFF_CAPTURE_PROVEN=false" in section
    assert "COMPLETE_CAPTURE_SEAM_CAN_NOW_BE_ADJUDICATED=false" in section
    assert "OWNER_MINT_CAN_NOW_BE_ADJUDICATED=false" in section
    assert "WRITER_BIND_CAN_NOW_BE_ADJUDICATED=false" in section
    assert "READER_BIND_CAN_NOW_BE_ADJUDICATED=false" in section
    assert "LIVE_RESTART_RECONSTRUCTION_CAN_NOW_BE_ADJUDICATED=false" in section
    assert "SECTION_11_14_LIVE_HANDOFF_OWNER_CURRENT=NONE" in section
    assert "FIRST_OWNER_PRODUCTIVELY_BOUND=false" in section
    assert "IMPLEMENTATION_AUTHORIZED=false" in section
    assert "ADMISSION_TRUE=false" in section
    assert "SUPERVISOR_ACTIVATED=false" in section
    assert "RETROACTIVE_HANDOFF_SYNTHESIS_ALLOWED=false" in section
    assert "POST_PERFORMED=false" in section
    assert "GET_PERFORMED=false" in section
    assert "RESTART_EXECUTION=false" in section
    assert NEXT_OWNER_GO_REQUIRED in section
    assert HISTORICAL_POS_SEMANTICS_CANONICAL_BINDING_RUN_ID in section
    assert (
        "PROPOSED_NEXT_SLICE=SECTION_11_14_LIVE_HANDOFF_POS_PRODUCER_SEMANTICS_AND_CONTRACT_V1"
        in (section)
    )
    for field_name in LADDER_FIELDS:
        assert field_name in section


def test_runbook_pos_producer_semantics_and_contract_slice_binds_unique_meaning() -> None:
    text = MASTER_RUNBOOK.read_text(encoding="utf-8")
    start = text.find(CANONICAL_POS_PRODUCER_SEMANTICS_AND_CONTRACT_SLICE_HEADING)
    end = text.find(CANONICAL_COMPLETE_CAPTURE_SEAM_PROOF_SLICE_HEADING, start)
    if end < 0:
        end = text.find(HEADING_11_15, start)
    assert start >= 0
    assert end > start
    section = text[start:end]
    assert HISTORICAL_POS_PRODUCER_SEMANTICS_AND_CONTRACT_OWNER_GO in section
    assert "THIS_SLICE=11.14.LIVE_HANDOFF_POS_PRODUCER_SEMANTICS_AND_CONTRACT" in section
    assert "PREDECESSOR_SLICE=11.14.LIVE_HANDOFF_POS_SEMANTICS_CANONICAL_BINDING" in section
    assert f"EXPECTED_ORIGIN_MAIN_SHA={HISTORICAL_POS_PRODUCER_SEMANTICS_AND_CONTRACT_SHA}" in (
        section
    )
    assert "SECTION_11_14_AUTHORIZED=false" in section
    assert "SECTION_11_14_COMPLETE=false" in section
    assert "LIVE_ACCOUNTING_RECONSTRUCTED=true" in section
    assert "LIVE_RESTART_RECONSTRUCTED=false" in section
    assert "POS_SEMANTICS=PROVEN" in section
    assert "POS_SEMANTICS_CANONICALLY_BOUND=true" in section
    assert "POS_UNIT=VENUE_CONTRACT_COUNT_NUMBER_OF_CONTRACTS" in section
    assert "POS_SIGN_SEMANTICS=UNSIGNED_MAGNITUDE" in section
    assert "SELECTED_SEMANTIC_UNIQUE=true" in section
    assert "NEW_PRODUCER_CONTRACT_DEFINED=true" in section
    assert "NEW_PRODUCER_IMPLEMENTED=false" in section
    assert "PRODUCER_CONTRACT_COMPLETE=true" in section
    assert "COMPLETE_CAPTURE_SEAM=UNPROVEN" in section
    assert "COMPLETE_CAPTURE_SEAM_CAN_NOW_BE_ADJUDICATED=true" in section
    assert "OWNER_MINT_CAN_NOW_BE_ADJUDICATED=false" in section
    assert "WRITER_BIND_CAN_NOW_BE_ADJUDICATED=false" in section
    assert "READER_BIND_CAN_NOW_BE_ADJUDICATED=false" in section
    assert "LIVE_RESTART_RECONSTRUCTION_CAN_NOW_BE_ADJUDICATED=false" in section
    assert "SECTION_11_14_LIVE_HANDOFF_OWNER_CURRENT=NONE" in section
    assert "FIRST_OWNER_PRODUCTIVELY_BOUND=false" in section
    assert "IMPLEMENTATION_AUTHORIZED=false" in section
    assert "ADMISSION_TRUE=false" in section
    assert "SUPERVISOR_ACTIVATED=false" in section
    assert "RETROACTIVE_HANDOFF_SYNTHESIS_ALLOWED=false" in section
    assert "POST_PERFORMED=false" in section
    assert "GET_PERFORMED=false" in section
    assert "RESTART_EXECUTION=false" in section
    assert NEXT_OWNER_GO_REQUIRED in section
    assert HISTORICAL_POS_PRODUCER_SEMANTICS_AND_CONTRACT_RUN_ID in section
    assert (
        "PROPOSED_NEXT_SLICE=SECTION_11_14_LIVE_HANDOFF_COMPLETE_CAPTURE_SEAM_PROOF_V1" in section
    )
    for field_name in LADDER_FIELDS:
        assert field_name in section


def test_runbook_complete_capture_seam_proof_slice_remains_unproven_without_invention() -> None:
    text = MASTER_RUNBOOK.read_text(encoding="utf-8")
    start = text.find(CANONICAL_COMPLETE_CAPTURE_SEAM_PROOF_SLICE_HEADING)
    end = text.find(CANONICAL_IMPLEMENTATION_SLICE_HEADING, start)
    if end < 0:
        end = text.find(HEADING_11_15, start)
    assert start >= 0
    assert end > start
    section = text[start:end]
    assert HISTORICAL_COMPLETE_CAPTURE_SEAM_PROOF_OWNER_GO in section
    assert "THIS_SLICE=11.14.LIVE_HANDOFF_COMPLETE_CAPTURE_SEAM_PROOF" in section
    assert "PREDECESSOR_SLICE=11.14.LIVE_HANDOFF_POS_PRODUCER_SEMANTICS_AND_CONTRACT" in section
    assert f"EXPECTED_ORIGIN_MAIN_SHA={HISTORICAL_COMPLETE_CAPTURE_SEAM_PROOF_SHA}" in section
    assert "SECTION_11_14_AUTHORIZED=false" in section
    assert "SECTION_11_14_COMPLETE=false" in section
    assert "LIVE_ACCOUNTING_RECONSTRUCTED=true" in section
    assert "LIVE_RESTART_RECONSTRUCTED=false" in section
    assert "POS_SEMANTICS=PROVEN" in section
    assert "NEW_PRODUCER_IMPLEMENTED=false" in section
    assert "COMPLETE_CAPTURE_SEAM=UNPROVEN" in section
    assert "COMPLETE_CAPTURE_SEAM_PROOF_STATUS=CLOSED_UNPROVEN_NO_INVENTION" in section
    assert "CAPTURE_TRIGGER_STATUS=REQUIRED_WINDOW_BOUND_PRODUCTIVE_TRIGGER_UNBOUND" in section
    assert "STORAGE_OWNER_MINTED=false" in section
    assert "WRITER_BOUND=false" in section
    assert "READER_BOUND=false" in section
    assert "CAPTURE_SEAM_BOUND=false" in section
    assert "PRODUCTIVE_BINDING_PRESENT=false" in section
    assert "SECTION_11_14_LIVE_HANDOFF_OWNER_CURRENT=NONE" in section
    assert "IMPLEMENTATION_AUTHORIZED=false" in section
    assert "ADMISSION_TRUE=false" in section
    assert "SUPERVISOR_ACTIVATED=false" in section
    assert "RETROACTIVE_HANDOFF_SYNTHESIS_ALLOWED=false" in section
    assert "POST_PERFORMED=false" in section
    assert "GET_PERFORMED=false" in section
    assert "RESTART_EXECUTION=false" in section
    assert NEXT_OWNER_GO_REQUIRED in section
    assert HISTORICAL_COMPLETE_CAPTURE_SEAM_PROOF_RUN_ID in section
    assert (
        "PROPOSED_NEXT_SLICE=SECTION_11_14_LIVE_HANDOFF_POS_PRODUCER_CAPTURE_RECORD_OWNER_AND_WRITER_IMPLEMENTATION_V1"
        in section
    )
    for field_name in LADDER_FIELDS:
        assert field_name in section


def test_runbook_producer_owner_writer_implementation_slice_binds_s05_without_reader() -> None:
    text = MASTER_RUNBOOK.read_text(encoding="utf-8")
    start = text.find(CANONICAL_IMPLEMENTATION_SLICE_HEADING)
    end = text.find(CANONICAL_READER_BIND_SLICE_HEADING, start)
    if end < 0:
        end = text.find(HEADING_11_15, start)
    assert start >= 0
    assert end > start
    section = text[start:end]
    assert HISTORICAL_IMPLEMENTATION_OWNER_GO in section
    assert (
        "THIS_SLICE=11.14.LIVE_HANDOFF_POS_PRODUCER_CAPTURE_RECORD_OWNER_AND_WRITER_IMPLEMENTATION"
        in section
    )
    assert "PREDECESSOR_SLICE=11.14.LIVE_HANDOFF_COMPLETE_CAPTURE_SEAM_PROOF" in section
    assert f"EXPECTED_ORIGIN_MAIN_SHA={HISTORICAL_IMPLEMENTATION_SHA}" in section
    assert "SECTION_11_14_AUTHORIZED=false" in section
    assert "SECTION_11_14_COMPLETE=false" in section
    assert "LIVE_ACCOUNTING_RECONSTRUCTED=true" in section
    assert "LIVE_RESTART_RECONSTRUCTED=false" in section
    assert "POS_SEMANTICS=PROVEN" in section
    assert "NEW_PRODUCER_IMPLEMENTED=true" in section
    assert "PRODUCER_SEMANTICS_EXACT_S05_IMPLEMENTED=true" in section
    assert "STORAGE_OWNER_MINTED=true" in section
    assert "WRITER_BOUND=true" in section
    assert "READER_BOUND=false" in section
    assert "CAPTURE_SEAM_BOUND=false" in section
    assert "PRODUCTIVE_BINDING_PRESENT=false" in section
    assert "COMPLETE_CAPTURE_SEAM=UNPROVEN" in section
    assert "CAPTURE_TRIGGER_STATUS=REQUIRED_WINDOW_BOUND_PRODUCTIVE_TRIGGER_BOUND" in section
    assert "DURABLE_SUCCESS_ACK_BEFORE_MUTATION_SUCCESS_CLAIM=true" in section
    assert "PROCESS_RESTART_READABLE_HANDOFF_RECORD=true" in section
    assert "HOST_CRASH_DURABILITY=UNPROVEN" in section
    assert (
        "SECTION_11_14_LIVE_HANDOFF_OWNER_CURRENT=SECTION_11_14_LIVE_DURABLE_PRE_RESTART_HANDOFF_OWNER_V1"
        in section
    )
    assert "IMPLEMENTATION_AUTHORIZED=false" in section
    assert "ADMISSION_TRUE=false" in section
    assert "SUPERVISOR_ACTIVATED=false" in section
    assert "RETROACTIVE_HANDOFF_SYNTHESIS_ALLOWED=false" in section
    assert "POST_PERFORMED=false" in section
    assert "GET_PERFORMED=false" in section
    assert "RESTART_EXECUTION=false" in section
    assert NEXT_OWNER_GO_REQUIRED in section
    assert HISTORICAL_IMPLEMENTATION_RUN_ID in section
    assert (
        "PROPOSED_NEXT_SLICE=SECTION_11_14_LIVE_HANDOFF_RESTART_READER_PROVENANCE_AND_CONSUMER_BIND_V1"
        in section
    )
    for field_name in LADDER_FIELDS:
        assert field_name in section


def test_runbook_restart_reader_provenance_and_consumer_bind_slice_binds_reader_without_restart() -> (
    None
):
    text = MASTER_RUNBOOK.read_text(encoding="utf-8")
    start = text.find(CANONICAL_READER_BIND_SLICE_HEADING)
    end = text.find(CANONICAL_CONTEMPORANEOUS_OBSERVATION_SLICE_HEADING, start)
    assert start >= 0
    assert end > start
    section = text[start:end]
    assert HISTORICAL_READER_BIND_OWNER_GO in section
    assert "THIS_SLICE=11.14.LIVE_HANDOFF_RESTART_READER_PROVENANCE_AND_CONSUMER_BIND" in section
    assert (
        "PREDECESSOR_SLICE=11.14.LIVE_HANDOFF_POS_PRODUCER_CAPTURE_RECORD_OWNER_AND_WRITER_IMPLEMENTATION"
        in section
    )
    assert f"EXPECTED_ORIGIN_MAIN_SHA={HISTORICAL_READER_BIND_SHA}" in section
    assert "SECTION_11_14_AUTHORIZED=false" in section
    assert "SECTION_11_14_COMPLETE=false" in section
    assert "LIVE_ACCOUNTING_RECONSTRUCTED=true" in section
    assert "LIVE_RESTART_RECONSTRUCTED=false" in section
    assert "POS_SEMANTICS=PROVEN" in section
    assert "NEW_PRODUCER_IMPLEMENTED=true" in section
    assert "STORAGE_OWNER_MINTED=true" in section
    assert "WRITER_BOUND=true" in section
    assert "READER_BOUND=true" in section
    assert "RESTART_CONSUMER_BOUND=true" in section
    assert "PROVENANCE_VALIDATION=CONTRACT_PROVEN" in section
    assert "FRESHNESS_VALIDATION=PARTIAL" in section
    assert "PRODUCTIVE_BINDING_PRESENT=true" in section
    assert "COMPLETE_CAPTURE_SEAM=UNPROVEN" in section
    assert (
        "COMPLETE_CAPTURE_SEAM_MISSING_PREDICATES=PROVENANCE_VALIDATED_CONTEMPORANEOUS_NO_BACKFILL"
        in section
    )
    assert "HOST_CRASH_DURABILITY=UNPROVEN" in section
    assert "CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_HANDOFF_OBSERVED=false" in section
    assert (
        "SECTION_11_14_LIVE_HANDOFF_OWNER_CURRENT=SECTION_11_14_LIVE_DURABLE_PRE_RESTART_HANDOFF_OWNER_V1"
        in section
    )
    assert "IMPLEMENTATION_AUTHORIZED=false" in section
    assert "ADMISSION_TRUE=false" in section
    assert "SUPERVISOR_ACTIVATED=false" in section
    assert "RETROACTIVE_HANDOFF_SYNTHESIS_ALLOWED=false" in section
    assert "POST_PERFORMED=false" in section
    assert "GET_PERFORMED=false" in section
    assert "RESTART_EXECUTION=false" in section
    assert NEXT_OWNER_GO_REQUIRED in section
    assert HISTORICAL_READER_BIND_RUN_ID in section
    assert (
        "PROPOSED_NEXT_SLICE=SECTION_11_14_LIVE_RESTART_RECONSTRUCTED_CONTEMPORANEOUS_PRE_RESTART_OBSERVATION_V1"
        in section
    )
    for field_name in LADDER_FIELDS:
        assert field_name in section


def test_runbook_contemporaneous_pre_restart_observation_slice_closes_refute() -> None:
    text = MASTER_RUNBOOK.read_text(encoding="utf-8")
    start = text.find(CANONICAL_CONTEMPORANEOUS_OBSERVATION_SLICE_HEADING)
    end = text.find(CANONICAL_FUTURE_CAPTURE_WINDOW_SLICE_HEADING, start)
    assert start >= 0
    assert end > start
    section = text[start:end]
    assert HISTORICAL_CONTEMPORANEOUS_OBSERVATION_OWNER_GO in section
    assert (
        "THIS_SLICE=11.14.LIVE_RESTART_RECONSTRUCTED_CONTEMPORANEOUS_PRE_RESTART_OBSERVATION"
        in section
    )
    assert (
        "PREDECESSOR_SLICE=11.14.LIVE_HANDOFF_RESTART_READER_PROVENANCE_AND_CONSUMER_BIND"
        in section
    )
    assert f"EXPECTED_ORIGIN_MAIN_SHA={HISTORICAL_CONTEMPORANEOUS_OBSERVATION_SHA}" in section
    assert "SECTION_11_14_AUTHORIZED=false" in section
    assert "SECTION_11_14_COMPLETE=false" in section
    assert "LIVE_ACCOUNTING_RECONSTRUCTED=true" in section
    assert "LIVE_RESTART_RECONSTRUCTED=false" in section
    assert "POS_SEMANTICS=PROVEN" in section
    assert "NEW_PRODUCER_IMPLEMENTED=true" in section
    assert "STORAGE_OWNER_MINTED=true" in section
    assert "WRITER_BOUND=true" in section
    assert "READER_BOUND=true" in section
    assert "RESTART_CONSUMER_BOUND=true" in section
    assert "CAPTURE_TRIGGER_JOINED_TO_AUTHORIZED_RUNTIME=false" in section
    assert "AUTHORIZED_NON_LIVE_RUNTIME_SURFACE_PRESENT=false" in section
    assert "MINIMUM_SAFE_OBSERVATION_CLASS=READ_BACK_ONLY_NO_WRITE" in section
    assert "PRODUCTIVE_CAPTURE_WRITE_EXECUTED=false" in section
    assert "READ_BACK_EXECUTED=true" in section
    assert "READ_BACK_RESULT=MISSING_HANDOFF" in section
    assert "OBSERVATION_STATUS=CLOSED_REFUTED" in section
    assert (
        "CASE_ADJUDICATION=CASE_CONTEMPORANEOUS_PRE_RESTART_HANDOFF_OBSERVABILITY_REFUTED_NO_AUTHORIZED_NON_LIVE_SURFACE"
        in section
    )
    assert "COMPLETE_CAPTURE_SEAM=UNPROVEN" in section
    assert (
        "COMPLETE_CAPTURE_SEAM_MISSING_PREDICATES=PROVENANCE_VALIDATED_CONTEMPORANEOUS_NO_BACKFILL"
        in section
    )
    assert "HOST_CRASH_DURABILITY=UNPROVEN" in section
    assert "CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_HANDOFF_OBSERVED=false" in section
    assert (
        "SECTION_11_14_LIVE_HANDOFF_OWNER_CURRENT=SECTION_11_14_LIVE_DURABLE_PRE_RESTART_HANDOFF_OWNER_V1"
        in section
    )
    assert "IMPLEMENTATION_AUTHORIZED=false" in section
    assert "ADMISSION_TRUE=false" in section
    assert "SUPERVISOR_ACTIVATED=false" in section
    assert "RETROACTIVE_HANDOFF_SYNTHESIS_ALLOWED=false" in section
    assert "POST_PERFORMED=false" in section
    assert "GET_PERFORMED=false" in section
    assert "RESTART_EXECUTION=false" in section
    assert NEXT_OWNER_GO_REQUIRED in section
    assert HISTORICAL_CONTEMPORANEOUS_OBSERVATION_RUN_ID in section
    assert (
        "PROPOSED_NEXT_SLICE=SECTION_11_14_LIVE_HANDOFF_FUTURE_AUTHORIZED_CONTEMPORANEOUS_CAPTURE_WINDOW_V1"
        in section
    )
    for field_name in LADDER_FIELDS:
        assert field_name in section


def test_runbook_future_authorized_capture_window_slice_closes_without_runtime_join() -> None:
    text = MASTER_RUNBOOK.read_text(encoding="utf-8")
    start = text.find(CANONICAL_FUTURE_CAPTURE_WINDOW_SLICE_HEADING)
    end = text.find(CANONICAL_PRODUCTIVE_CAPTURE_OWNER_HOOK_BINDING_SLICE_HEADING, start)
    assert start >= 0
    assert end > start
    section = text[start:end]
    assert HISTORICAL_FUTURE_CAPTURE_WINDOW_OWNER_GO in section
    assert (
        "THIS_SLICE=11.14.LIVE_HANDOFF_FUTURE_AUTHORIZED_CONTEMPORANEOUS_CAPTURE_WINDOW" in section
    )
    assert (
        "PREDECESSOR_SLICE=11.14.LIVE_RESTART_RECONSTRUCTED_CONTEMPORANEOUS_PRE_RESTART_OBSERVATION"
        in section
    )
    assert f"EXPECTED_ORIGIN_MAIN_SHA={HISTORICAL_FUTURE_CAPTURE_WINDOW_SHA}" in section
    assert "SECTION_11_14_AUTHORIZED=false" in section
    assert "SECTION_11_14_COMPLETE=false" in section
    assert "LIVE_ACCOUNTING_RECONSTRUCTED=true" in section
    assert "LIVE_RESTART_RECONSTRUCTED=false" in section
    assert "POS_SEMANTICS=PROVEN" in section
    assert "NEW_PRODUCER_IMPLEMENTED=true" in section
    assert "STORAGE_OWNER_MINTED=true" in section
    assert "WRITER_BOUND=true" in section
    assert "READER_BOUND=true" in section
    assert "RESTART_CONSUMER_BOUND=true" in section
    assert "CAPTURE_TRIGGER_JOINED_TO_AUTHORIZED_RUNTIME=false" in section
    assert "PRODUCTIVE_CAPTURE_OWNER_STATUS=ABSENT" in section
    assert "PRODUCTIVE_CAPTURE_HOOK_STATUS=ABSENT" in section
    assert "CAPTURE_WINDOW_ORDERING=UNPROVEN" in section
    assert "MINIMUM_FUTURE_CAPTURE_WINDOW_SURFACE=UNPROVEN" in section
    assert "PRODUCTIVE_BINDING_ALLOWED_IN_THIS_WORKPACKAGE=false" in section
    assert "PRODUCTIVE_BINDING_IMPLEMENTED=false" in section
    assert "CURRENT_PRODUCTIVE_CALLER_COUNT_FOR_PRODUCER=0" in section
    assert "CURRENT_PRODUCTIVE_CALLER_COUNT_FOR_WRITER=0" in section
    assert "COMPLETE_CAPTURE_SEAM=UNPROVEN" in section
    assert (
        "COMPLETE_CAPTURE_SEAM_MISSING_PREDICATES=PROVENANCE_VALIDATED_CONTEMPORANEOUS_NO_BACKFILL"
        in section
    )
    assert "HOST_CRASH_DURABILITY=UNPROVEN" in section
    assert "CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_HANDOFF_OBSERVED=false" in section
    assert (
        "SECTION_11_14_LIVE_HANDOFF_OWNER_CURRENT=SECTION_11_14_LIVE_DURABLE_PRE_RESTART_HANDOFF_OWNER_V1"
        in section
    )
    assert "IMPLEMENTATION_AUTHORIZED=false" in section
    assert "ADMISSION_TRUE=false" in section
    assert "SUPERVISOR_ACTIVATED=false" in section
    assert "RETROACTIVE_HANDOFF_SYNTHESIS_ALLOWED=false" in section
    assert "POST_PERFORMED=false" in section
    assert "GET_PERFORMED=false" in section
    assert "RESTART_EXECUTION=false" in section
    assert NEXT_OWNER_GO_REQUIRED in section
    assert HISTORICAL_FUTURE_CAPTURE_WINDOW_RUN_ID in section
    assert (
        "PROPOSED_NEXT_SLICE=SECTION_11_14_LIVE_HANDOFF_PRODUCTIVE_CAPTURE_OWNER_HOOK_AND_FUTURE_IDENTITY_CONTRACT_V1"
        in section
    )
    for field_name in LADDER_FIELDS:
        assert field_name in section


def test_runbook_productive_capture_owner_and_lifecycle_hook_binding_slice_closes_case_b() -> None:
    text = MASTER_RUNBOOK.read_text(encoding="utf-8")
    start = text.find(CANONICAL_PRODUCTIVE_CAPTURE_OWNER_HOOK_BINDING_SLICE_HEADING)
    end = text.find(CANONICAL_CREATE_PRODUCTIVE_CAPTURE_OWNER_HOOK_SLICE_HEADING, start)
    assert start >= 0
    assert end > start
    section = text[start:end]
    assert HISTORICAL_PRODUCTIVE_CAPTURE_OWNER_HOOK_BINDING_OWNER_GO in section
    assert (
        "THIS_SLICE=11.14.LIVE_HANDOFF_PRODUCTIVE_CAPTURE_OWNER_AND_LIFECYCLE_HOOK_BINDING"
        in section
    )
    assert (
        "PREDECESSOR_SLICE=11.14.LIVE_HANDOFF_FUTURE_AUTHORIZED_CONTEMPORANEOUS_CAPTURE_WINDOW"
        in section
    )
    assert (
        f"EXPECTED_ORIGIN_MAIN_SHA={HISTORICAL_PRODUCTIVE_CAPTURE_OWNER_HOOK_BINDING_SHA}"
        in section
    )
    assert "SECTION_11_14_AUTHORIZED=false" in section
    assert "SECTION_11_14_COMPLETE=false" in section
    assert "LIVE_ACCOUNTING_RECONSTRUCTED=true" in section
    assert "LIVE_RESTART_RECONSTRUCTED=false" in section
    assert "POS_SEMANTICS=PROVEN" in section
    assert "NEW_PRODUCER_IMPLEMENTED=true" in section
    assert "STORAGE_OWNER_MINTED=true" in section
    assert "WRITER_BOUND=true" in section
    assert "READER_BOUND=true" in section
    assert "RESTART_CONSUMER_BOUND=true" in section
    assert "CAPTURE_TRIGGER_JOINED_TO_AUTHORIZED_RUNTIME=false" in section
    assert "PRODUCTIVE_CAPTURE_OWNER_STATUS=REFUTED" in section
    assert "PRODUCTIVE_LIFECYCLE_HOOK_STATUS=REFUTED" in section
    assert "AUTHORIZED_RUNTIME_SURFACE=NONE" in section
    assert "AUTHORIZED_RUNTIME_SURFACE_PROVEN=false" in section
    assert "BINDING_CASE=CASE_B" in section
    assert "MINIMAL_FAIL_CLOSED_BINDING_ALLOWED=false" in section
    assert "PRODUCTIVE_BINDING_IMPLEMENTED=false" in section
    assert "CURRENT_PRODUCTIVE_CALLER_COUNT_FOR_PRODUCER=0" in section
    assert "CURRENT_PRODUCTIVE_CALLER_COUNT_FOR_WRITER=0" in section
    assert "COMPLETE_CAPTURE_SEAM=UNPROVEN" in section
    assert (
        "COMPLETE_CAPTURE_SEAM_MISSING_PREDICATES=PROVENANCE_VALIDATED_CONTEMPORANEOUS_NO_BACKFILL"
        in section
    )
    assert "HOST_CRASH_DURABILITY=UNPROVEN" in section
    assert "CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_HANDOFF_OBSERVED=false" in section
    assert (
        "SECTION_11_14_LIVE_HANDOFF_OWNER_CURRENT=SECTION_11_14_LIVE_DURABLE_PRE_RESTART_HANDOFF_OWNER_V1"
        in section
    )
    assert "IMPLEMENTATION_AUTHORIZED=false" in section
    assert "ADMISSION_TRUE=false" in section
    assert "SUPERVISOR_ACTIVATED=false" in section
    assert "RETROACTIVE_HANDOFF_SYNTHESIS_ALLOWED=false" in section
    assert "POST_PERFORMED=false" in section
    assert "GET_PERFORMED=false" in section
    assert "RESTART_EXECUTION=false" in section
    assert NEXT_OWNER_GO_REQUIRED in section
    assert HISTORICAL_PRODUCTIVE_CAPTURE_OWNER_HOOK_BINDING_RUN_ID in section
    assert (
        "PROPOSED_NEXT_SLICE=SECTION_11_14_LIVE_HANDOFF_CREATE_PRODUCTIVE_CAPTURE_OWNER_AND_LIFECYCLE_HOOK_REQUIRES_SEPARATE_OWNER_GO_V1"
        in section
    )
    for field_name in LADDER_FIELDS:
        assert field_name in section


def test_runbook_create_productive_capture_owner_and_lifecycle_hook_slice_closes_case_a() -> None:
    text = MASTER_RUNBOOK.read_text(encoding="utf-8")
    start = text.find(CANONICAL_CREATE_PRODUCTIVE_CAPTURE_OWNER_HOOK_SLICE_HEADING)
    end = text.find(CANONICAL_COMPLETE_CONTEMPORANEOUS_CAPTURE_SEAM_SLICE_HEADING, start)
    if end < 0:
        end = text.find(HEADING_11_15, start)
    assert start >= 0
    assert end > start
    section = text[start:end]
    assert HISTORICAL_CREATE_PRODUCTIVE_CAPTURE_OWNER_HOOK_OWNER_GO in section
    assert (
        "THIS_SLICE=11.14.LIVE_HANDOFF_CREATE_PRODUCTIVE_CAPTURE_OWNER_AND_LIFECYCLE_HOOK"
        in section
    )
    assert (
        "PREDECESSOR_SLICE=11.14.LIVE_HANDOFF_PRODUCTIVE_CAPTURE_OWNER_AND_LIFECYCLE_HOOK_BINDING"
        in section
    )
    assert (
        f"EXPECTED_ORIGIN_MAIN_SHA={HISTORICAL_CREATE_PRODUCTIVE_CAPTURE_OWNER_HOOK_SHA}" in section
    )
    assert "SECTION_11_14_AUTHORIZED=false" in section
    assert "SECTION_11_14_COMPLETE=false" in section
    assert "LIVE_ACCOUNTING_RECONSTRUCTED=true" in section
    assert "LIVE_RESTART_RECONSTRUCTED=false" in section
    assert "POS_SEMANTICS=PROVEN" in section
    assert "NEW_PRODUCER_IMPLEMENTED=true" in section
    assert "STORAGE_OWNER_MINTED=true" in section
    assert "WRITER_BOUND=true" in section
    assert "READER_BOUND=true" in section
    assert "RESTART_CONSUMER_BOUND=true" in section
    assert "CAPTURE_TRIGGER_JOINED_TO_AUTHORIZED_RUNTIME=false" in section
    assert "PRODUCTIVE_CAPTURE_OWNER=SECTION_11_14_LIVE_PRODUCTIVE_CAPTURE_OWNER_V1" in section
    assert "PRODUCTIVE_CAPTURE_OWNER_UNIQUE=true" in section
    assert (
        "PRODUCTIVE_LIFECYCLE_HOOK=run_capture_hook_after_bound_fill_before_restart_v1" in section
    )
    assert "PRODUCTIVE_LIFECYCLE_HOOK_UNIQUE=true" in section
    assert "HOOK_ORDERING_PROVEN=true" in section
    assert "BOUND_FILL_BEFORE_HOOK_PROVEN=true" in section
    assert "HOOK_BEFORE_RESTART_PROVEN=true" in section
    assert "STRUCTURAL_RUNTIME_BINDING_PROVEN=true" in section
    assert "CURRENT_RUNTIME_EXECUTION_AUTHORIZED=false" in section
    assert "AUTHORIZED_RUNTIME_SURFACE=NONE" in section
    assert "AUTHORIZED_RUNTIME_SURFACE_PROVEN=false" in section
    assert "BINDING_CASE=CASE_A_CREATED" in section
    assert "PRODUCTIVE_BINDING_IMPLEMENTED=true" in section
    assert "CURRENT_PRODUCTIVE_CALLER_COUNT_FOR_PRODUCER=0" in section
    assert "CURRENT_PRODUCTIVE_CALLER_COUNT_FOR_WRITER=1" in section
    assert "COMPLETE_CAPTURE_SEAM=UNPROVEN" in section
    assert (
        "COMPLETE_CAPTURE_SEAM_MISSING_PREDICATES=PROVENANCE_VALIDATED_CONTEMPORANEOUS_NO_BACKFILL"
        in section
    )
    assert "HOST_CRASH_DURABILITY=UNPROVEN" in section
    assert "CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_HANDOFF_OBSERVED=false" in section
    assert (
        "SECTION_11_14_LIVE_HANDOFF_OWNER_CURRENT=SECTION_11_14_LIVE_DURABLE_PRE_RESTART_HANDOFF_OWNER_V1"
        in section
    )
    assert "IMPLEMENTATION_AUTHORIZED=true" in section
    assert "ADMISSION_TRUE=false" in section
    assert "SUPERVISOR_ACTIVATED=false" in section
    assert "RETROACTIVE_HANDOFF_SYNTHESIS_ALLOWED=false" in section
    assert "POST_PERFORMED=false" in section
    assert "GET_PERFORMED=false" in section
    assert "RESTART_EXECUTION=false" in section
    assert NEXT_OWNER_GO_REQUIRED in section
    assert HISTORICAL_CREATE_PRODUCTIVE_CAPTURE_OWNER_HOOK_RUN_ID in section
    assert (
        "PROPOSED_NEXT_SLICE=SECTION_11_14_LIVE_HANDOFF_CONTEMPORANEOUS_PRE_RESTART_CAPTURE_OBSERVATION_REQUIRES_SEPARATE_OWNER_GO_V1"
        in section
    )
    for field_name in LADDER_FIELDS:
        assert field_name in section


def test_runbook_complete_contemporaneous_capture_seam_and_required_field_provenance_slice() -> (
    None
):
    text = MASTER_RUNBOOK.read_text(encoding="utf-8")
    start = text.find(CANONICAL_COMPLETE_CONTEMPORANEOUS_CAPTURE_SEAM_SLICE_HEADING)
    end = text.find(CANONICAL_PRODUCTIVE_HOOK_CALLER_BINDING_SLICE_HEADING, start)
    if end < 0:
        end = text.find(HEADING_11_15, start)
    assert start >= 0
    assert end > start
    section = text[start:end]
    assert HISTORICAL_COMPLETE_CONTEMPORANEOUS_CAPTURE_SEAM_OWNER_GO in section
    assert (
        "THIS_SLICE=11.14.LIVE_HANDOFF_COMPLETE_CONTEMPORANEOUS_CAPTURE_SEAM_AND_REQUIRED_FIELD_PROVENANCE"
        in section
    )
    assert (
        "PREDECESSOR_SLICE=11.14.LIVE_HANDOFF_CREATE_PRODUCTIVE_CAPTURE_OWNER_AND_LIFECYCLE_HOOK"
        in section
    )
    assert (
        f"EXPECTED_ORIGIN_MAIN_SHA={HISTORICAL_COMPLETE_CONTEMPORANEOUS_CAPTURE_SEAM_SHA}"
        in section
    )
    assert "SECTION_11_14_AUTHORIZED=false" in section
    assert "SECTION_11_14_COMPLETE=false" in section
    assert "LIVE_ACCOUNTING_RECONSTRUCTED=true" in section
    assert "LIVE_RESTART_RECONSTRUCTED=false" in section
    assert "COMPLETE_CAPTURE_SEAM=UNPROVEN" in section
    assert "COMPLETE_CAPTURE_SEAM_ACCEPTANCE_CONTRACT_BOUND=true" in section
    assert "REQUIRED_FIELD_PROVENANCE_MATRIX_BOUND=true" in section
    assert "CONTEMPORANEOUS_PRODUCTIVE_CAPTURE_EXECUTED=false" in section
    assert "CURRENT_RUNTIME_EXECUTION_AUTHORIZED=false" in section
    assert "AUTHORIZED_RUNTIME_SURFACE=NONE" in section
    assert "HOST_CRASH_DURABILITY=UNPROVEN" in section
    assert "CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_HANDOFF_OBSERVED=false" in section
    assert "PROVEN_FAIL_CLOSED_FIELD_COUNT=5" in section
    assert "PROVEN_COMPLETE_FIELD_COUNT=0" in section
    assert "PARTIAL_CAPTURE_ALLOWED=false" in section
    assert "RETROACTIVE_HANDOFF_SYNTHESIS_ALLOWED=false" in section
    assert "POST_PERFORMED=false" in section
    assert "GET_PERFORMED=false" in section
    assert "RESTART_EXECUTION=false" in section
    assert NEXT_OWNER_GO_REQUIRED in section
    assert HISTORICAL_COMPLETE_CONTEMPORANEOUS_CAPTURE_SEAM_RUN_ID in section
    assert (
        "PROPOSED_NEXT_SLICE=SECTION_11_14_LIVE_HANDOFF_CONTEMPORANEOUS_PRE_RESTART_CAPTURE_OBSERVATION_REQUIRES_SEPARATE_OWNER_GO_V1"
        in section
    )
    for field_name in LADDER_FIELDS:
        assert field_name in section


def test_runbook_productive_capture_hook_caller_binding_and_offline_call_path_proof_slice() -> None:
    text = MASTER_RUNBOOK.read_text(encoding="utf-8")
    start = text.find(CANONICAL_PRODUCTIVE_HOOK_CALLER_BINDING_SLICE_HEADING)
    end = text.find(CANONICAL_COMPLETE_CAPTURE_SEAM_NO_BACKFILL_CONTRACT_SLICE_HEADING, start)
    if end < 0:
        end = text.find(HEADING_11_15, start)
    assert start >= 0
    assert end > start
    section = text[start:end]
    assert HISTORICAL_PRODUCTIVE_HOOK_CALLER_BINDING_OWNER_GO in section
    assert (
        "THIS_SLICE=11.14.LIVE_HANDOFF_PRODUCTIVE_CAPTURE_HOOK_CALLER_BINDING_AND_OFFLINE_CALL_PATH_PROOF"
        in section
    )
    assert (
        "PREDECESSOR_SLICE=11.14.LIVE_HANDOFF_COMPLETE_CONTEMPORANEOUS_CAPTURE_SEAM_AND_REQUIRED_FIELD_PROVENANCE"
        in section
    )
    assert f"EXPECTED_ORIGIN_MAIN_SHA={HISTORICAL_PRODUCTIVE_HOOK_CALLER_BINDING_SHA}" in section
    assert "SECTION_11_14_AUTHORIZED=false" in section
    assert "SECTION_11_14_COMPLETE=false" in section
    assert "LIVE_ACCOUNTING_RECONSTRUCTED=true" in section
    assert "LIVE_RESTART_RECONSTRUCTED=false" in section
    assert "COMPLETE_CAPTURE_SEAM=UNPROVEN" in section
    assert "COMPLETE_CAPTURE_SEAM_ACCEPTANCE_CONTRACT_BOUND=true" in section
    assert "REQUIRED_FIELD_PROVENANCE_MATRIX_BOUND=true" in section
    assert "PRODUCTIVE_HOOK_CALLER=call_pre_restart_handoff_capture_after_bound_fill_v1" in section
    assert "PRODUCTIVE_HOOK_CALLER_BINDING_PROVEN=true" in section
    assert "PRODUCTIVE_CALL_PATH_OFFLINE_PROOF=true" in section
    assert (
        "PRODUCTIVE_LIFECYCLE_EVENT=REQUIRED_WINDOW_HANDOFF_COMMIT_AFTER_BOUND_FILL_BEFORE_RESTART"
        in section
    )
    assert "PROVENANCE_VALIDATED_CONTEMPORANEOUS_NO_BACKFILL=false" in section
    assert "CONTEMPORANEOUS_PRODUCTIVE_CAPTURE_EXECUTED=false" in section
    assert "CURRENT_RUNTIME_EXECUTION_AUTHORIZED=false" in section
    assert "AUTHORIZED_RUNTIME_SURFACE=NONE" in section
    assert "HOST_CRASH_DURABILITY=UNPROVEN" in section
    assert "CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_HANDOFF_OBSERVED=false" in section
    assert "POST_PERFORMED=false" in section
    assert "GET_PERFORMED=false" in section
    assert "RESTART_EXECUTION=false" in section
    assert NEXT_OWNER_GO_REQUIRED in section
    assert HISTORICAL_PRODUCTIVE_HOOK_CALLER_BINDING_RUN_ID in section
    assert (
        "PROPOSED_NEXT_SLICE=SECTION_11_14_LIVE_HANDOFF_CONTEMPORANEOUS_PRE_RESTART_CAPTURE_OBSERVATION_REQUIRES_SEPARATE_OWNER_GO_V1"
        in section
    )
    for field_name in LADDER_FIELDS:
        assert field_name in section


def test_runbook_complete_capture_seam_required_field_provenance_and_no_backfill_contract_slice() -> (
    None
):
    text = MASTER_RUNBOOK.read_text(encoding="utf-8")
    start = text.find(CANONICAL_COMPLETE_CAPTURE_SEAM_NO_BACKFILL_CONTRACT_SLICE_HEADING)
    end = text.find(CANONICAL_CONTEMPORANEOUS_CAPTURE_RUNTIME_SURFACE_SLICE_HEADING, start)
    if end < 0:
        end = text.find(HEADING_11_15, start)
    assert start >= 0
    assert end > start
    section = text[start:end]
    assert HISTORICAL_COMPLETE_CAPTURE_SEAM_NO_BACKFILL_CONTRACT_OWNER_GO in section
    assert (
        "THIS_SLICE=11.14.LIVE_HANDOFF_COMPLETE_CAPTURE_SEAM_REQUIRED_FIELD_PROVENANCE_AND_NO_BACKFILL_CONTRACT"
        in section
    )
    assert (
        "PREDECESSOR_SLICE=11.14.LIVE_HANDOFF_PRODUCTIVE_CAPTURE_HOOK_CALLER_BINDING_AND_OFFLINE_CALL_PATH_PROOF"
        in section
    )
    assert (
        f"EXPECTED_ORIGIN_MAIN_SHA={HISTORICAL_COMPLETE_CAPTURE_SEAM_NO_BACKFILL_CONTRACT_SHA}"
        in section
    )
    assert "SECTION_11_14_AUTHORIZED=false" in section
    assert "SECTION_11_14_COMPLETE=false" in section
    assert "LIVE_ACCOUNTING_RECONSTRUCTED=true" in section
    assert "LIVE_RESTART_RECONSTRUCTED=false" in section
    assert "COMPLETE_CAPTURE_SEAM=PROVEN" in section
    assert "REQUIRED_FIELD_PROVENANCE_COMPLETE=true" in section
    assert "NO_BACKFILL_CONTRACT_PROVEN=true" in section
    assert "PROVENANCE_VALIDATED_CONTEMPORANEOUS_NO_BACKFILL=true" in section
    assert "CONTEMPORANEOUS_PRODUCTIVE_CAPTURE_EXECUTED=false" in section
    assert "CURRENT_RUNTIME_EXECUTION_AUTHORIZED=false" in section
    assert "AUTHORIZED_RUNTIME_SURFACE=NONE" in section
    assert "HOST_CRASH_DURABILITY=UNPROVEN" in section
    assert "CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_HANDOFF_OBSERVED=false" in section
    assert "PRODUCTIVE_HOOK_CALLER=call_pre_restart_handoff_capture_after_bound_fill_v1" in section
    assert "PRODUCTIVE_HOOK_CALLER_BINDING_PROVEN=true" in section
    assert "PRODUCTIVE_CALL_PATH_OFFLINE_PROOF=true" in section
    assert "POST_PERFORMED=false" in section
    assert "GET_PERFORMED=false" in section
    assert "RESTART_EXECUTION=false" in section
    assert NEXT_OWNER_GO_REQUIRED in section
    assert HISTORICAL_COMPLETE_CAPTURE_SEAM_NO_BACKFILL_CONTRACT_RUN_ID in section
    assert (
        "PROPOSED_NEXT_SLICE=SECTION_11_14_LIVE_HANDOFF_CONTEMPORANEOUS_PRE_RESTART_CAPTURE_OBSERVATION_REQUIRES_SEPARATE_OWNER_GO_V1"
        in section
    )
    for field_name in LADDER_FIELDS:
        assert field_name in section


def test_runbook_contemporaneous_capture_runtime_surface_and_non_execution_authorization_boundary_slice() -> (
    None
):
    text = MASTER_RUNBOOK.read_text(encoding="utf-8")
    start = text.find(CANONICAL_CONTEMPORANEOUS_CAPTURE_RUNTIME_SURFACE_SLICE_HEADING)
    end = text.find(HEADING_11_15, start)
    assert start >= 0
    assert end > start
    section = text[start:end]
    assert OWNER_GO in section
    assert THIS_SLICE in section
    assert PREDECESSOR_SLICE in section
    assert f"EXPECTED_ORIGIN_MAIN_SHA={EXPECTED_ORIGIN_MAIN_SHA}" in section
    assert "SECTION_11_14_AUTHORIZED=false" in section
    assert "SECTION_11_14_COMPLETE=false" in section
    assert "LIVE_ACCOUNTING_RECONSTRUCTED=true" in section
    assert "LIVE_RESTART_RECONSTRUCTED=false" in section
    assert "COMPLETE_CAPTURE_SEAM=PROVEN" in section
    assert "PROVENANCE_VALIDATED_CONTEMPORANEOUS_NO_BACKFILL=true" in section
    assert "CONTEMPORANEOUS_CAPTURE_RUNTIME_SURFACE=PROVEN" in section
    assert "CONTEMPORANEOUS_CAPTURE_SIDE_EFFECT_BOUNDARY=PROVEN" in section
    assert "CONTEMPORANEOUS_CAPTURE_CAN_BE_ISOLATED_FROM_LIVE_EXECUTION=false" in section
    assert "CONTEMPORANEOUS_CAPTURE_EXECUTION_PRECONDITIONS_COMPLETE=true" in section
    assert "MINIMAL_FUTURE_AUTHORIZED_ENTRYPOINT=NONE_CAPTURE_ONLY" in section
    assert "UNAVOIDABLE_EXTERNAL_EFFECTS=LIVE_IDENTITY_BOUND_VENUE_FILL" in section
    assert "EARLIEST_IRREVERSIBLE_EFFECT=VENUE_FILL_OF_IDENTITY_BOUND_ORDER" in section
    assert "PRODUCTIVE_RUNTIME_ENTRYPOINT=run_live_order_pre_restart_handoff_capture_v1" in section
    assert "PRODUCTIVE_CAPTURE_CALLER=call_pre_restart_handoff_capture_after_bound_fill_v1" in (
        section
    )
    assert "CAPTURE_POINT=REQUIRED_WINDOW_HANDOFF_COMMIT_AFTER_BOUND_FILL_BEFORE_RESTART" in section
    assert "CONTEMPORANEOUS_PRODUCTIVE_CAPTURE_EXECUTED=false" in section
    assert "CURRENT_RUNTIME_EXECUTION_AUTHORIZED=false" in section
    assert "AUTHORIZED_RUNTIME_SURFACE=NONE" in section
    assert "HOST_CRASH_DURABILITY=UNPROVEN" in section
    assert "CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_HANDOFF_OBSERVED=false" in section
    assert "PRODUCTIVE_HOOK_CALLER_BINDING_PROVEN=true" in section
    assert "PRODUCTIVE_CALL_PATH_OFFLINE_PROOF=true" in section
    assert "POST_PERFORMED=false" in section
    assert "GET_PERFORMED=false" in section
    assert "RESTART_EXECUTION=false" in section
    assert NEXT_OWNER_GO_REQUIRED in section
    assert CANONICAL_EVIDENCE_RUN_ID in section
    assert (
        "PROPOSED_NEXT_SLICE=SECTION_11_14_LIVE_HANDOFF_CONTEMPORANEOUS_PRE_RESTART_CAPTURE_OBSERVATION_REQUIRES_SEPARATE_OWNER_GO_V1"
        in section
    )
    for field_name in LADDER_FIELDS:
        assert field_name in section


def test_spec_mot_atlas_and_evidence_exist() -> None:
    spec = SPEC.read_text(encoding="utf-8")
    assert "DOCS_TOKEN_SECTION_11_14_LIVE_EXECUTION_CODE_EXISTS_ADJUDICATION_V1" in spec
    assert "SECTION_11_14_AUTHORIZED=false" in spec
    assert "LIVE_EXECUTION_CODE_EXISTS=true" in spec
    assert "LIVE_EXECUTION_PATH_REACHABLE=false" in spec
    historical = HISTORICAL_SPEC.read_text(encoding="utf-8")
    assert (
        "DOCS_TOKEN_SECTION_11_14_LIVE_ORDER_AND_ECONOMIC_EVIDENCE_LADDER_OFFLINE_SURFACE_V1"
        in historical
    )
    mot = MOT.read_text(encoding="utf-8")
    assert "11.14 LIVE_EXECUTION_CODE_EXISTS_ADJUDICATION" in mot
    assert "11.14 LIVE_EXECUTION_PATH_REACHABLE_ADJUDICATION" in mot
    assert "11.14 LIVE_PRIVATE_READ_ONLY_PROVEN_ADJUDICATION" in mot
    assert "11.14 LIVE_ORDER_PLAN_OBSERVED_ADJUDICATION" in mot
    assert "11.14 LIVE_SUBMIT_ACK_CONTRACT_AND_MUTATION_BOUNDARY_FORENSIC_ADJUDICATION" in mot
    assert "11.14 LIVE_SUBMIT_ACK_OBSERVED_PROOF_CRITERION" in mot
    assert "11.14 LIVE_SUBMIT_ACK_OBSERVED_ADJUDICATION" in mot
    assert "11.14 LIVE_FILL_OBSERVED_ADJUDICATION" in mot
    assert "11.14 LIVE_FEE_OBSERVED_ADJUDICATION" in mot
    assert "11.14 LIVE_POSITION_RECONCILED_ADJUDICATION" in mot
    assert "11.14 LIVE_ACCOUNTING_RECONSTRUCTED_ADJUDICATION" in mot
    assert "11.14 LIVE_RESTART_RECONSTRUCTED_ADJUDICATION" in mot
    assert "11.14 LIVE_RESTART_RECONSTRUCTED_EXHAUSTIVE_OFFLINE_CENSUS" in mot
    assert "11.14 LIVE_RESTART_HANDOFF_OWNER_BIND_AND_RETROACTIVE_SYNTHESIS_REFUSAL" in mot
    assert "11.14 LIVE_HANDOFF_REQUIRED_FIELD_CAPTURE_SEAM_POS_AND_OWNER_VACANCY_CONTRACT" in mot
    assert (
        "11.14 LIVE_DURABLE_PRE_RESTART_HANDOFF_OWNER_AND_CAPTURE_ARCHITECTURE_ADJUDICATION" in mot
    )
    assert "11.14 LIVE_HANDOFF_POS_SEMANTICS_CANONICAL_BINDING" in mot
    assert "11.14 LIVE_HANDOFF_POS_PRODUCER_SEMANTICS_AND_CONTRACT" in mot
    assert "11.14 LIVE_HANDOFF_COMPLETE_CAPTURE_SEAM_PROOF" in mot
    assert "11.14 LIVE_HANDOFF_POS_PRODUCER_CAPTURE_RECORD_OWNER_AND_WRITER_IMPLEMENTATION" in mot
    assert "11.14 LIVE_HANDOFF_RESTART_READER_PROVENANCE_AND_CONSUMER_BIND" in mot
    assert "11.14 LIVE_RESTART_RECONSTRUCTED_CONTEMPORANEOUS_PRE_RESTART_OBSERVATION" in mot
    assert "11.14 LIVE_HANDOFF_FUTURE_AUTHORIZED_CONTEMPORANEOUS_CAPTURE_WINDOW" in mot
    assert "11.14 LIVE_HANDOFF_PRODUCTIVE_CAPTURE_OWNER_AND_LIFECYCLE_HOOK_BINDING" in mot
    assert "11.14 LIVE_HANDOFF_CREATE_PRODUCTIVE_CAPTURE_OWNER_AND_LIFECYCLE_HOOK" in mot
    assert (
        "11.14 LIVE_HANDOFF_COMPLETE_CONTEMPORANEOUS_CAPTURE_SEAM_AND_REQUIRED_FIELD_PROVENANCE"
        in mot
    )
    assert (
        "11.14 LIVE_HANDOFF_PRODUCTIVE_CAPTURE_HOOK_CALLER_BINDING_AND_OFFLINE_CALL_PATH_PROOF"
        in mot
    )
    assert (
        "11.14 LIVE_HANDOFF_COMPLETE_CAPTURE_SEAM_REQUIRED_FIELD_PROVENANCE_AND_NO_BACKFILL_CONTRACT"
        in mot
    )
    assert (
        "11.14 LIVE_HANDOFF_CONTEMPORANEOUS_CAPTURE_RUNTIME_SURFACE_AND_NON_EXECUTION_AUTHORIZATION_BOUNDARY"
        in mot
    )
    assert "SECTION_11_14_LIVE_RESTART_RECONSTRUCTED_EXHAUSTIVE_OFFLINE_CENSUS_V1.md" in mot
    assert (
        "SECTION_11_14_LIVE_RESTART_HANDOFF_OWNER_BIND_AND_RETROACTIVE_SYNTHESIS_REFUSAL_V1.md"
        in mot
    )
    assert (
        "SECTION_11_14_LIVE_HANDOFF_REQUIRED_FIELD_CAPTURE_SEAM_POS_AND_OWNER_VACANCY_CONTRACT_V1.md"
        in mot
    )
    assert (
        "SECTION_11_14_LIVE_DURABLE_PRE_RESTART_HANDOFF_OWNER_AND_CAPTURE_ARCHITECTURE_ADJUDICATION_V1.md"
        in mot
    )
    assert "SECTION_11_14_LIVE_HANDOFF_POS_SEMANTICS_CANONICAL_BINDING_V1.md" in mot
    assert "SECTION_11_14_LIVE_HANDOFF_POS_PRODUCER_SEMANTICS_AND_CONTRACT_V1.md" in mot
    assert "SECTION_11_14_LIVE_HANDOFF_COMPLETE_CAPTURE_SEAM_PROOF_V1.md" in mot
    assert (
        "SECTION_11_14_LIVE_HANDOFF_POS_PRODUCER_CAPTURE_RECORD_OWNER_AND_WRITER_IMPLEMENTATION_V1.md"
        in mot
    )
    assert "SECTION_11_14_LIVE_HANDOFF_RESTART_READER_PROVENANCE_AND_CONSUMER_BIND_V1.md" in mot
    assert (
        "SECTION_11_14_LIVE_RESTART_RECONSTRUCTED_CONTEMPORANEOUS_PRE_RESTART_OBSERVATION_V1.md"
        in mot
    )
    assert (
        "SECTION_11_14_LIVE_HANDOFF_FUTURE_AUTHORIZED_CONTEMPORANEOUS_CAPTURE_WINDOW_V1.md" in mot
    )
    assert (
        "SECTION_11_14_LIVE_HANDOFF_PRODUCTIVE_CAPTURE_OWNER_AND_LIFECYCLE_HOOK_BINDING_V1.md"
        in mot
    )
    assert (
        "SECTION_11_14_LIVE_HANDOFF_CREATE_PRODUCTIVE_CAPTURE_OWNER_AND_LIFECYCLE_HOOK_V1.md" in mot
    )
    assert (
        "SECTION_11_14_LIVE_HANDOFF_COMPLETE_CONTEMPORANEOUS_CAPTURE_SEAM_AND_REQUIRED_FIELD_PROVENANCE_V1.md"
        in mot
    )
    assert (
        "SECTION_11_14_LIVE_HANDOFF_PRODUCTIVE_CAPTURE_HOOK_CALLER_BINDING_AND_OFFLINE_CALL_PATH_PROOF_V1.md"
        in mot
    )
    assert (
        "SECTION_11_14_LIVE_HANDOFF_COMPLETE_CAPTURE_SEAM_REQUIRED_FIELD_PROVENANCE_AND_NO_BACKFILL_CONTRACT_V1.md"
        in mot
    )
    assert (
        "SECTION_11_14_LIVE_HANDOFF_CONTEMPORANEOUS_CAPTURE_RUNTIME_SURFACE_AND_NON_EXECUTION_AUTHORIZATION_BOUNDARY_V1.md"
        in mot
    )
    assert "SECTION_11_14_LIVE_EXECUTION_CODE_EXISTS_ADJUDICATION_V1.md" in mot
    assert "SECTION_11_14_LIVE_EXECUTION_PATH_REACHABLE_ADJUDICATION_V1.md" in mot
    assert "SECTION_11_14_LIVE_PRIVATE_READ_ONLY_PROVEN_ADJUDICATION_V1.md" in mot
    assert "SECTION_11_14_LIVE_ORDER_PLAN_OBSERVED_ADJUDICATION_V1.md" in mot
    assert (
        "SECTION_11_14_LIVE_SUBMIT_ACK_CONTRACT_AND_MUTATION_BOUNDARY_FORENSIC_ADJUDICATION_V1.md"
        in mot
    )
    assert "SECTION_11_14_LIVE_SUBMIT_ACK_OBSERVED_PROOF_CRITERION_V1.md" in mot
    assert "SECTION_11_14_LIVE_SUBMIT_ACK_OBSERVED_ADJUDICATION_V1.md" in mot
    assert "SECTION_11_14_LIVE_FILL_OBSERVED_ADJUDICATION_V1.md" in mot
    assert "SECTION_11_14_LIVE_FEE_OBSERVED_ADJUDICATION_V1.md" in mot
    assert "SECTION_11_14_LIVE_POSITION_RECONCILED_ADJUDICATION_V1.md" in mot
    assert "SECTION_11_14_LIVE_ACCOUNTING_RECONSTRUCTED_ADJUDICATION_V1.md" in mot
    assert "SECTION_11_14_LIVE_RESTART_RECONSTRUCTED_ADJUDICATION_V1.md" in mot
    assert "SECTION_11_14_LIVE_RESTART_RECONSTRUCTED_EXHAUSTIVE_OFFLINE_CENSUS_V1.md" in mot
    path_spec = PATH_REACHABLE_SPEC.read_text(encoding="utf-8")
    assert "DOCS_TOKEN_SECTION_11_14_LIVE_EXECUTION_PATH_REACHABLE_ADJUDICATION_V1" in path_spec
    assert "LIVE_EXECUTION_PATH_REACHABLE=true" in path_spec
    assert "LIVE_PRIVATE_READ_ONLY_PROVEN=false" in path_spec
    ro_spec = PRIVATE_READ_ONLY_SPEC.read_text(encoding="utf-8")
    assert "DOCS_TOKEN_SECTION_11_14_LIVE_PRIVATE_READ_ONLY_PROVEN_ADJUDICATION_V1" in ro_spec
    assert "LIVE_PRIVATE_READ_ONLY_PROVEN=true" in ro_spec
    assert "LIVE_ORDER_PLAN_OBSERVED=false" in ro_spec
    order_plan_spec = ORDER_PLAN_SPEC.read_text(encoding="utf-8")
    assert "DOCS_TOKEN_SECTION_11_14_LIVE_ORDER_PLAN_OBSERVED_ADJUDICATION_V1" in order_plan_spec
    assert "POST_REQUIRED_FOR_LIVE_ORDER_PLAN_OBSERVED=false" in order_plan_spec
    assert "LIVE_ORDER_PLAN_OBSERVED=true" in order_plan_spec
    assert "LIVE_SUBMIT_ACK_OBSERVED=false" in order_plan_spec
    forensic_spec = SUBMIT_ACK_FORENSIC_SPEC.read_text(encoding="utf-8")
    assert (
        "DOCS_TOKEN_SECTION_11_14_LIVE_SUBMIT_ACK_CONTRACT_AND_MUTATION_BOUNDARY_FORENSIC_ADJUDICATION_V1"
        in forensic_spec
    )
    assert "CASE_ADJUDICATION=CASE_C_CANONICAL_SEMANTIC_GAP" in forensic_spec
    assert "LIVE_SUBMIT_ACK_OBSERVED=false" in forensic_spec
    proof_spec = SUBMIT_ACK_PROOF_CRITERION_SPEC.read_text(encoding="utf-8")
    assert "DOCS_TOKEN_SECTION_11_14_LIVE_SUBMIT_ACK_OBSERVED_PROOF_CRITERION_V1" in proof_spec
    assert "CASE_ADJUDICATION=CASE_A_READY_FOR_EXACT_SINGLE_POST_OWNER_GO" in proof_spec
    assert "LIVE_SUBMIT_ACK_OBSERVED=false" in proof_spec
    ack_spec = SUBMIT_ACK_OBSERVED_ADJUDICATION_SPEC.read_text(encoding="utf-8")
    assert "DOCS_TOKEN_SECTION_11_14_LIVE_SUBMIT_ACK_OBSERVED_ADJUDICATION_V1" in ack_spec
    assert "CASE_ADJUDICATION=CASE_LIVE_SUBMIT_ACK_OBSERVED_FILL_INELIGIBLE" in ack_spec
    assert "LIVE_SUBMIT_ACK_OBSERVED=true" in ack_spec
    assert "LIVE_FILL_OBSERVED=false" in ack_spec
    fill_spec = FILL_OBSERVED_ADJUDICATION_SPEC.read_text(encoding="utf-8")
    assert "DOCS_TOKEN_SECTION_11_14_LIVE_FILL_OBSERVED_ADJUDICATION_V1" in fill_spec
    assert "CASE_ADJUDICATION=CASE_LIVE_FILL_OBSERVED_FEE_INELIGIBLE" in fill_spec
    assert "LIVE_FILL_OBSERVED=true" in fill_spec
    assert "LIVE_FEE_OBSERVED=false" in fill_spec
    fee_spec = FEE_OBSERVED_ADJUDICATION_SPEC.read_text(encoding="utf-8")
    assert "DOCS_TOKEN_SECTION_11_14_LIVE_FEE_OBSERVED_ADJUDICATION_V1" in fee_spec
    assert "CASE_ADJUDICATION=CASE_LIVE_FEE_OBSERVED_POSITION_INELIGIBLE" in fee_spec
    assert "LIVE_FEE_OBSERVED=true" in fee_spec
    assert "LIVE_POSITION_RECONCILED=false" in fee_spec
    position_spec = POSITION_RECONCILED_ADJUDICATION_SPEC.read_text(encoding="utf-8")
    assert "DOCS_TOKEN_SECTION_11_14_LIVE_POSITION_RECONCILED_ADJUDICATION_V1" in position_spec
    assert "CASE_ADJUDICATION=CASE_LIVE_POSITION_RECONCILED_ACCOUNTING_INELIGIBLE" in position_spec
    assert "LIVE_POSITION_RECONCILED=true" in position_spec
    assert "LIVE_ACCOUNTING_RECONSTRUCTED=false" in position_spec
    accounting_spec = ACCOUNTING_RECONSTRUCTED_ADJUDICATION_SPEC.read_text(encoding="utf-8")
    assert (
        "DOCS_TOKEN_SECTION_11_14_LIVE_ACCOUNTING_RECONSTRUCTED_ADJUDICATION_V1" in accounting_spec
    )
    assert (
        "CASE_ADJUDICATION=CASE_LIVE_ACCOUNTING_RECONSTRUCTED_RESTART_INELIGIBLE" in accounting_spec
    )
    assert "LIVE_ACCOUNTING_RECONSTRUCTED=true" in accounting_spec
    assert "LIVE_RESTART_RECONSTRUCTED=false" in accounting_spec
    restart_spec = RESTART_RECONSTRUCTED_ADJUDICATION_SPEC.read_text(encoding="utf-8")
    assert "DOCS_TOKEN_SECTION_11_14_LIVE_RESTART_RECONSTRUCTED_ADJUDICATION_V1" in restart_spec
    assert (
        "CASE_ADJUDICATION=CASE_LIVE_RESTART_RECONSTRUCTED_FAIL_CLOSED_MISSING_DURABLE_HANDOFF"
        in restart_spec
    )
    assert "LIVE_RESTART_RECONSTRUCTED=false" in restart_spec
    assert "LIVE_AUTONOMOUS_RECOVERY_OBSERVED=false" in restart_spec
    exhaustive_spec = RESTART_RECONSTRUCTED_EXHAUSTIVE_CENSUS_SPEC.read_text(encoding="utf-8")
    assert (
        "DOCS_TOKEN_SECTION_11_14_LIVE_RESTART_RECONSTRUCTED_EXHAUSTIVE_OFFLINE_CENSUS_V1"
        in exhaustive_spec
    )
    assert (
        "CASE_ADJUDICATION=CASE_LIVE_RESTART_RECONSTRUCTED_FAIL_CLOSED_MISSING_DURABLE_HANDOFF"
        in exhaustive_spec
    )
    assert "LIVE_RESTART_RECONSTRUCTED=false" in exhaustive_spec
    assert "CASE_B_NOT_PROVEN_CONTRACT_CLOSED=true" in exhaustive_spec
    assert "RUNTIME_CHANGE_REQUIRES_SEPARATE_OWNER_SCOPE=true" in exhaustive_spec
    owner_bind_spec = RESTART_HANDOFF_OWNER_BIND_SPEC.read_text(encoding="utf-8")
    assert (
        "DOCS_TOKEN_SECTION_11_14_LIVE_RESTART_HANDOFF_OWNER_BIND_AND_RETROACTIVE_SYNTHESIS_REFUSAL_V1"
        in owner_bind_spec
    )
    assert "SECTION_11_14_LIVE_HANDOFF_OWNER_CURRENT=NONE" in owner_bind_spec
    assert "RETROACTIVE_HANDOFF_SYNTHESIS_ALLOWED=false" in owner_bind_spec
    assert "LIVE_RESTART_RECONSTRUCTED=false" in owner_bind_spec
    vacancy_spec = REQUIRED_FIELD_CAPTURE_SEAM_SPEC.read_text(encoding="utf-8")
    assert (
        "DOCS_TOKEN_SECTION_11_14_LIVE_HANDOFF_REQUIRED_FIELD_CAPTURE_SEAM_POS_AND_OWNER_VACANCY_CONTRACT_V1"
        in vacancy_spec
    )
    assert "POS_SEMANTICS=UNPROVEN" in vacancy_spec
    assert "COMPLETE_CAPTURE_SEAM=UNPROVEN" in vacancy_spec
    assert "OWNER_VACANCY_CONTRACT_STATUS=BOUND_CAPTURE_SEAM_UNPROVEN" in vacancy_spec
    assert "LIVE_RESTART_RECONSTRUCTED=false" in vacancy_spec
    architecture_spec = ARCHITECTURE_ADJUDICATION_SPEC.read_text(encoding="utf-8")
    assert (
        "DOCS_TOKEN_SECTION_11_14_LIVE_DURABLE_PRE_RESTART_HANDOFF_OWNER_AND_CAPTURE_ARCHITECTURE_ADJUDICATION_V1"
        in architecture_spec
    )
    assert "POS_SEMANTICS=UNPROVEN" in architecture_spec
    assert "COMPLETE_CAPTURE_SEAM=UNPROVEN" in architecture_spec
    assert "ARCHITECTURE_ADJUDICATION_COMPLETE=true" in architecture_spec
    assert "IMPLEMENTATION_AUTHORIZED=false" in architecture_spec
    assert "LIVE_RESTART_RECONSTRUCTED=false" in architecture_spec
    pos_binding_spec = POS_SEMANTICS_CANONICAL_BINDING_SPEC.read_text(encoding="utf-8")
    assert (
        "DOCS_TOKEN_SECTION_11_14_LIVE_HANDOFF_POS_SEMANTICS_CANONICAL_BINDING_V1"
        in pos_binding_spec
    )
    assert "POS_SEMANTICS=UNPROVEN" in pos_binding_spec
    assert "POS_SEMANTICS_CAN_BE_BOUND_FROM_EXISTING_AUTHORITY=false" in pos_binding_spec
    assert "NEW_CONTEMPORANEOUS_POS_PRODUCER_REQUIRED=true" in pos_binding_spec
    assert "IMPLEMENTATION_AUTHORIZED=false" in pos_binding_spec
    assert "LIVE_RESTART_RECONSTRUCTED=false" in pos_binding_spec
    producer_spec = POS_PRODUCER_SEMANTICS_AND_CONTRACT_SPEC.read_text(encoding="utf-8")
    assert (
        "DOCS_TOKEN_SECTION_11_14_LIVE_HANDOFF_POS_PRODUCER_SEMANTICS_AND_CONTRACT_V1"
        in producer_spec
    )
    assert "POS_SEMANTICS=PROVEN" in producer_spec
    assert "NEW_PRODUCER_CONTRACT_DEFINED=true" in producer_spec
    assert "NEW_PRODUCER_IMPLEMENTED=false" in producer_spec
    assert "COMPLETE_CAPTURE_SEAM_CAN_NOW_BE_ADJUDICATED=true" in producer_spec
    assert "IMPLEMENTATION_AUTHORIZED=false" in producer_spec
    assert "LIVE_RESTART_RECONSTRUCTED=false" in producer_spec
    capture_spec = COMPLETE_CAPTURE_SEAM_PROOF_SPEC.read_text(encoding="utf-8")
    assert "DOCS_TOKEN_SECTION_11_14_LIVE_HANDOFF_COMPLETE_CAPTURE_SEAM_PROOF_V1" in capture_spec
    assert "COMPLETE_CAPTURE_SEAM=UNPROVEN" in capture_spec
    assert "NEW_PRODUCER_IMPLEMENTED=false" in capture_spec
    assert "STORAGE_OWNER_MINTED=false" in capture_spec
    assert "WRITER_BOUND=false" in capture_spec
    assert "IMPLEMENTATION_AUTHORIZED=false" in capture_spec
    assert "LIVE_RESTART_RECONSTRUCTED=false" in capture_spec
    implementation_spec = IMPLEMENTATION_SPEC.read_text(encoding="utf-8")
    assert (
        "DOCS_TOKEN_SECTION_11_14_LIVE_HANDOFF_POS_PRODUCER_CAPTURE_RECORD_OWNER_AND_WRITER_IMPLEMENTATION_V1"
        in implementation_spec
    )
    assert "NEW_PRODUCER_IMPLEMENTED=true" in implementation_spec
    assert "STORAGE_OWNER_MINTED=true" in implementation_spec
    assert "WRITER_BOUND=true" in implementation_spec
    assert "READER_BOUND=false" in implementation_spec
    assert "COMPLETE_CAPTURE_SEAM=UNPROVEN" in implementation_spec
    assert "HOST_CRASH_DURABILITY=UNPROVEN" in implementation_spec
    assert "IMPLEMENTATION_AUTHORIZED=false" in implementation_spec
    assert "LIVE_RESTART_RECONSTRUCTED=false" in implementation_spec
    reader_bind_spec = READER_BIND_SPEC.read_text(encoding="utf-8")
    assert (
        "DOCS_TOKEN_SECTION_11_14_LIVE_HANDOFF_RESTART_READER_PROVENANCE_AND_CONSUMER_BIND_V1"
        in reader_bind_spec
    )
    assert "READER_BOUND=true" in reader_bind_spec
    assert "RESTART_CONSUMER_BOUND=true" in reader_bind_spec
    assert "PROVENANCE_VALIDATION=CONTRACT_PROVEN" in reader_bind_spec
    assert "FRESHNESS_VALIDATION=PARTIAL" in reader_bind_spec
    assert "COMPLETE_CAPTURE_SEAM=UNPROVEN" in reader_bind_spec
    assert "HOST_CRASH_DURABILITY=UNPROVEN" in reader_bind_spec
    assert "CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_HANDOFF_OBSERVED=false" in reader_bind_spec
    assert "IMPLEMENTATION_AUTHORIZED=false" in reader_bind_spec
    assert "LIVE_RESTART_RECONSTRUCTED=false" in reader_bind_spec
    observation_spec = OBSERVATION_SPEC.read_text(encoding="utf-8")
    assert (
        "DOCS_TOKEN_SECTION_11_14_LIVE_RESTART_RECONSTRUCTED_CONTEMPORANEOUS_PRE_RESTART_OBSERVATION_V1"
        in observation_spec
    )
    assert "OBSERVATION_STATUS=CLOSED_REFUTED" in observation_spec
    assert "READ_BACK_RESULT=MISSING_HANDOFF" in observation_spec
    assert "AUTHORIZED_NON_LIVE_RUNTIME_SURFACE_PRESENT=false" in observation_spec
    assert "COMPLETE_CAPTURE_SEAM=UNPROVEN" in observation_spec
    assert "CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_HANDOFF_OBSERVED=false" in observation_spec
    assert "IMPLEMENTATION_AUTHORIZED=false" in observation_spec
    assert "LIVE_RESTART_RECONSTRUCTED=false" in observation_spec
    capture_window_spec = CAPTURE_WINDOW_SPEC.read_text(encoding="utf-8")
    assert (
        "DOCS_TOKEN_SECTION_11_14_LIVE_HANDOFF_FUTURE_AUTHORIZED_CONTEMPORANEOUS_CAPTURE_WINDOW_V1"
        in capture_window_spec
    )
    assert "PRODUCTIVE_CAPTURE_OWNER_STATUS=ABSENT" in capture_window_spec
    assert "PRODUCTIVE_CAPTURE_HOOK_STATUS=ABSENT" in capture_window_spec
    assert "CAPTURE_WINDOW_ORDERING=UNPROVEN" in capture_window_spec
    assert "MINIMUM_FUTURE_CAPTURE_WINDOW_SURFACE=UNPROVEN" in capture_window_spec
    assert "PRODUCTIVE_BINDING_ALLOWED_IN_THIS_WORKPACKAGE=false" in capture_window_spec
    assert "COMPLETE_CAPTURE_SEAM=UNPROVEN" in capture_window_spec
    assert "CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_HANDOFF_OBSERVED=false" in capture_window_spec
    assert "IMPLEMENTATION_AUTHORIZED=false" in capture_window_spec
    assert "LIVE_RESTART_RECONSTRUCTED=false" in capture_window_spec
    owner_hook_spec = OWNER_HOOK_BINDING_SPEC.read_text(encoding="utf-8")
    assert (
        "DOCS_TOKEN_SECTION_11_14_LIVE_HANDOFF_PRODUCTIVE_CAPTURE_OWNER_AND_LIFECYCLE_HOOK_BINDING_V1"
        in owner_hook_spec
    )
    assert "PRODUCTIVE_CAPTURE_OWNER_STATUS=REFUTED" in owner_hook_spec
    assert "PRODUCTIVE_LIFECYCLE_HOOK_STATUS=REFUTED" in owner_hook_spec
    assert "AUTHORIZED_RUNTIME_SURFACE=NONE" in owner_hook_spec
    assert "AUTHORIZED_RUNTIME_SURFACE_PROVEN=false" in owner_hook_spec
    assert "BINDING_CASE=CASE_B" in owner_hook_spec
    assert "MINIMAL_FAIL_CLOSED_BINDING_ALLOWED=false" in owner_hook_spec
    assert "PRODUCTIVE_BINDING_IMPLEMENTED=false" in owner_hook_spec
    assert "COMPLETE_CAPTURE_SEAM=UNPROVEN" in owner_hook_spec
    assert "CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_HANDOFF_OBSERVED=false" in owner_hook_spec
    assert "IMPLEMENTATION_AUTHORIZED=false" in owner_hook_spec
    assert "LIVE_RESTART_RECONSTRUCTED=false" in owner_hook_spec
    create_owner_hook_spec = CREATE_OWNER_HOOK_SPEC.read_text(encoding="utf-8")
    assert (
        "DOCS_TOKEN_SECTION_11_14_LIVE_HANDOFF_CREATE_PRODUCTIVE_CAPTURE_OWNER_AND_LIFECYCLE_HOOK_V1"
        in create_owner_hook_spec
    )
    assert "PRODUCTIVE_CAPTURE_OWNER=SECTION_11_14_LIVE_PRODUCTIVE_CAPTURE_OWNER_V1" in (
        create_owner_hook_spec
    )
    assert "PRODUCTIVE_CAPTURE_OWNER_UNIQUE=true" in create_owner_hook_spec
    assert (
        "PRODUCTIVE_LIFECYCLE_HOOK=run_capture_hook_after_bound_fill_before_restart_v1"
        in create_owner_hook_spec
    )
    assert "PRODUCTIVE_LIFECYCLE_HOOK_UNIQUE=true" in create_owner_hook_spec
    assert "STRUCTURAL_RUNTIME_BINDING_PROVEN=true" in create_owner_hook_spec
    assert "CURRENT_RUNTIME_EXECUTION_AUTHORIZED=false" in create_owner_hook_spec
    assert "AUTHORIZED_RUNTIME_SURFACE=NONE" in create_owner_hook_spec
    assert "BINDING_CASE=CASE_A_CREATED" in create_owner_hook_spec
    assert "PRODUCTIVE_BINDING_IMPLEMENTED=true" in create_owner_hook_spec
    assert "COMPLETE_CAPTURE_SEAM=UNPROVEN" in create_owner_hook_spec
    assert "CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_HANDOFF_OBSERVED=false" in (
        create_owner_hook_spec
    )
    assert "IMPLEMENTATION_AUTHORIZED=true" in create_owner_hook_spec
    assert "LIVE_RESTART_RECONSTRUCTED=false" in create_owner_hook_spec
    complete_seam_spec = COMPLETE_CONTEMPORANEOUS_CAPTURE_SEAM_SPEC.read_text(encoding="utf-8")
    assert (
        "DOCS_TOKEN_SECTION_11_14_LIVE_HANDOFF_COMPLETE_CONTEMPORANEOUS_CAPTURE_SEAM_AND_REQUIRED_FIELD_PROVENANCE_V1"
        in complete_seam_spec
    )
    assert "COMPLETE_CAPTURE_SEAM=UNPROVEN" in complete_seam_spec
    assert "COMPLETE_CAPTURE_SEAM_ACCEPTANCE_CONTRACT_BOUND=true" in complete_seam_spec
    assert "REQUIRED_FIELD_PROVENANCE_MATRIX_BOUND=true" in complete_seam_spec
    assert "CONTEMPORANEOUS_PRODUCTIVE_CAPTURE_EXECUTED=false" in complete_seam_spec
    assert "CURRENT_RUNTIME_EXECUTION_AUTHORIZED=false" in complete_seam_spec
    assert "AUTHORIZED_RUNTIME_SURFACE=NONE" in complete_seam_spec
    assert "PARTIAL_CAPTURE_ALLOWED=false" in complete_seam_spec
    assert "IMPLEMENTATION_AUTHORIZED=true" in complete_seam_spec
    assert "LIVE_RESTART_RECONSTRUCTED=false" in complete_seam_spec
    caller_spec = PRODUCTIVE_HOOK_CALLER_BINDING_SPEC.read_text(encoding="utf-8")
    assert (
        "DOCS_TOKEN_SECTION_11_14_LIVE_HANDOFF_PRODUCTIVE_CAPTURE_HOOK_CALLER_BINDING_AND_OFFLINE_CALL_PATH_PROOF_V1"
        in caller_spec
    )
    assert "PRODUCTIVE_HOOK_CALLER=call_pre_restart_handoff_capture_after_bound_fill_v1" in (
        caller_spec
    )
    assert "PRODUCTIVE_HOOK_CALLER_BINDING_PROVEN=true" in caller_spec
    assert "PRODUCTIVE_CALL_PATH_OFFLINE_PROOF=true" in caller_spec
    assert "COMPLETE_CAPTURE_SEAM=UNPROVEN" in caller_spec
    assert "CONTEMPORANEOUS_PRODUCTIVE_CAPTURE_EXECUTED=false" in caller_spec
    assert "CURRENT_RUNTIME_EXECUTION_AUTHORIZED=false" in caller_spec
    assert "AUTHORIZED_RUNTIME_SURFACE=NONE" in caller_spec
    assert "IMPLEMENTATION_AUTHORIZED=true" in caller_spec
    assert "LIVE_RESTART_RECONSTRUCTED=false" in caller_spec
    no_backfill_spec = COMPLETE_CAPTURE_SEAM_NO_BACKFILL_CONTRACT_SPEC.read_text(encoding="utf-8")
    assert (
        "DOCS_TOKEN_SECTION_11_14_LIVE_HANDOFF_COMPLETE_CAPTURE_SEAM_REQUIRED_FIELD_PROVENANCE_AND_NO_BACKFILL_CONTRACT_V1"
        in no_backfill_spec
    )
    assert "COMPLETE_CAPTURE_SEAM=PROVEN" in no_backfill_spec
    assert "PROVENANCE_VALIDATED_CONTEMPORANEOUS_NO_BACKFILL=true" in no_backfill_spec
    assert "REQUIRED_FIELD_PROVENANCE_COMPLETE=true" in no_backfill_spec
    assert "NO_BACKFILL_CONTRACT_PROVEN=true" in no_backfill_spec
    assert "CONTEMPORANEOUS_PRODUCTIVE_CAPTURE_EXECUTED=false" in no_backfill_spec
    assert "CURRENT_RUNTIME_EXECUTION_AUTHORIZED=false" in no_backfill_spec
    assert "AUTHORIZED_RUNTIME_SURFACE=NONE" in no_backfill_spec
    assert "IMPLEMENTATION_AUTHORIZED=true" in no_backfill_spec
    assert "LIVE_RESTART_RECONSTRUCTED=false" in no_backfill_spec
    runtime_surface_spec = CONTEMPORANEOUS_CAPTURE_RUNTIME_SURFACE_SPEC.read_text(encoding="utf-8")
    assert (
        "DOCS_TOKEN_SECTION_11_14_LIVE_HANDOFF_CONTEMPORANEOUS_CAPTURE_RUNTIME_SURFACE_AND_NON_EXECUTION_AUTHORIZATION_BOUNDARY_V1"
        in runtime_surface_spec
    )
    assert "CONTEMPORANEOUS_CAPTURE_RUNTIME_SURFACE=PROVEN" in runtime_surface_spec
    assert "CONTEMPORANEOUS_CAPTURE_SIDE_EFFECT_BOUNDARY=PROVEN" in runtime_surface_spec
    assert (
        "CONTEMPORANEOUS_CAPTURE_CAN_BE_ISOLATED_FROM_LIVE_EXECUTION=false" in runtime_surface_spec
    )
    assert "MINIMAL_FUTURE_AUTHORIZED_ENTRYPOINT=NONE_CAPTURE_ONLY" in runtime_surface_spec
    assert "COMPLETE_CAPTURE_SEAM=PROVEN" in runtime_surface_spec
    assert "PROVENANCE_VALIDATED_CONTEMPORANEOUS_NO_BACKFILL=true" in runtime_surface_spec
    assert "CONTEMPORANEOUS_PRODUCTIVE_CAPTURE_EXECUTED=false" in runtime_surface_spec
    assert "CURRENT_RUNTIME_EXECUTION_AUTHORIZED=false" in runtime_surface_spec
    assert "AUTHORIZED_RUNTIME_SURFACE=NONE" in runtime_surface_spec
    assert "IMPLEMENTATION_AUTHORIZED=true" in runtime_surface_spec
    assert "LIVE_RESTART_RECONSTRUCTED=false" in runtime_surface_spec
    catalog = ATLAS_CATALOG.read_text(encoding="utf-8")
    authority = ATLAS_AUTHORITY.read_text(encoding="utf-8")
    relations = ATLAS_RUNTIME_RELATIONS.read_text(encoding="utf-8")
    assert "ATLAS_AUTHORITY=NONE" in authority
    assert "id: PHASE:section_11_14_live_execution_code_exists_adjudication" in catalog
    assert "id: PHASE:section_11_14_live_execution_path_reachable_adjudication" in catalog
    assert "id: PHASE:section_11_14_live_private_read_only_proven_adjudication" in catalog
    assert "id: PHASE:section_11_14_live_order_plan_observed_adjudication" in catalog
    assert (
        "id: PHASE:section_11_14_live_submit_ack_contract_and_mutation_boundary_forensic_adjudication"
        in catalog
    )
    assert "id: PHASE:section_11_14_live_submit_ack_observed_proof_criterion" in catalog
    assert "id: PHASE:section_11_14_live_submit_ack_observed_adjudication" in catalog
    assert "id: PHASE:section_11_14_live_fill_observed_adjudication" in catalog
    assert "id: PHASE:section_11_14_live_fee_observed_adjudication" in catalog
    assert "id: PHASE:section_11_14_live_position_reconciled_adjudication" in catalog
    assert "id: PHASE:section_11_14_live_accounting_reconstructed_adjudication" in catalog
    assert "id: PHASE:section_11_14_live_restart_reconstructed_adjudication" in catalog
    assert "id: PHASE:section_11_14_live_restart_reconstructed_exhaustive_offline_census" in catalog
    assert (
        "id: PHASE:section_11_14_live_restart_handoff_owner_bind_and_retroactive_synthesis_refusal"
        in catalog
    )
    assert (
        "id: PHASE:section_11_14_live_handoff_required_field_capture_seam_pos_and_owner_vacancy_contract"
        in catalog
    )
    assert (
        "id: PHASE:section_11_14_live_durable_pre_restart_handoff_owner_and_capture_architecture_adjudication"
        in catalog
    )
    assert "id: PHASE:section_11_14_live_handoff_pos_semantics_canonical_binding" in catalog
    assert "id: PHASE:section_11_14_live_handoff_pos_producer_semantics_and_contract" in catalog
    assert "id: PHASE:section_11_14_live_handoff_complete_capture_seam_proof" in catalog
    assert (
        "id: PHASE:section_11_14_live_handoff_pos_producer_capture_record_owner_and_writer_implementation"
        in catalog
    )
    assert (
        "id: PHASE:section_11_14_live_handoff_restart_reader_provenance_and_consumer_bind"
        in catalog
    )
    assert (
        "id: PHASE:section_11_14_live_restart_reconstructed_contemporaneous_pre_restart_observation"
        in catalog
    )
    assert (
        "id: PHASE:section_11_14_live_handoff_future_authorized_contemporaneous_capture_window"
        in catalog
    )
    assert (
        "id: PHASE:section_11_14_live_handoff_productive_capture_owner_and_lifecycle_hook_binding"
        in catalog
    )
    assert (
        "id: PHASE:section_11_14_live_handoff_create_productive_capture_owner_and_lifecycle_hook"
        in catalog
    )
    assert (
        "id: PHASE:section_11_14_live_handoff_complete_contemporaneous_capture_seam_and_required_field_provenance"
        in catalog
    )
    assert (
        "id: PHASE:section_11_14_live_handoff_productive_capture_hook_caller_binding_and_offline_call_path_proof"
        in catalog
    )
    assert (
        "id: PHASE:section_11_14_live_handoff_complete_capture_seam_required_field_provenance_and_no_backfill_contract"
        in catalog
    )
    assert (
        "id: PHASE:section_11_14_live_handoff_contemporaneous_capture_runtime_surface_and_non_execution_authorization_boundary"
        in catalog
    )
    assert (
        "id: RUNTIME_COMPONENT:section_11_14_live_order_and_economic_evidence_ladder_v1" in catalog
    )
    assert (
        "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/submit_transport_v1.py" in catalog
    )
    assert "src/governance/policy_critic/rules.py" in catalog
    assert "ATLAS_AUTHORITY=NONE" in catalog
    start = relations.find("id: REL:r_section_11_14_submit_ack_proof_criterion_follows_forensic")
    assert start >= 0
    block = relations[start : start + 1400]
    assert (
        "source: RUNTIME_COMPONENT:section_11_14_live_order_and_economic_evidence_ladder_v1"
        in block
    )
    assert "ATLAS_AUTHORITY=NONE" in block
    adj_rel = relations.find(
        "id: REL:r_section_11_14_submit_ack_observed_adjudication_follows_proof_criterion"
    )
    assert adj_rel >= 0
    adj_block = relations[adj_rel : adj_rel + 1400]
    assert "ATLAS_AUTHORITY=NONE" in adj_block
    fill_rel = relations.find(
        "id: REL:r_section_11_14_fill_observed_adjudication_follows_submit_ack"
    )
    assert fill_rel >= 0
    fill_block = relations[fill_rel : fill_rel + 1400]
    assert "ATLAS_AUTHORITY=NONE" in fill_block
    fee_rel = relations.find("id: REL:r_section_11_14_fee_observed_adjudication_follows_fill")
    assert fee_rel >= 0
    fee_block = relations[fee_rel : fee_rel + 1400]
    assert "ATLAS_AUTHORITY=NONE" in fee_block
    position_rel = relations.find(
        "id: REL:r_section_11_14_position_reconciled_adjudication_follows_fee"
    )
    assert position_rel >= 0
    position_block = relations[position_rel : position_rel + 1400]
    assert "ATLAS_AUTHORITY=NONE" in position_block
    accounting_rel = relations.find(
        "id: REL:r_section_11_14_accounting_reconstructed_adjudication_follows_position"
    )
    assert accounting_rel >= 0
    accounting_block = relations[accounting_rel : accounting_rel + 1400]
    assert "ATLAS_AUTHORITY=NONE" in accounting_block
    restart_rel = relations.find(
        "id: REL:r_section_11_14_restart_reconstructed_adjudication_follows_accounting"
    )
    assert restart_rel >= 0
    restart_block = relations[restart_rel : restart_rel + 1400]
    assert "ATLAS_AUTHORITY=NONE" in restart_block
    exhaustive_rel = relations.find(
        "id: REL:r_section_11_14_restart_exhaustive_census_follows_restart_adjudication"
    )
    assert exhaustive_rel >= 0
    exhaustive_block = relations[exhaustive_rel : exhaustive_rel + 1400]
    assert "ATLAS_AUTHORITY=NONE" in exhaustive_block
    owner_bind_rel = relations.find(
        "id: REL:r_section_11_14_restart_handoff_owner_bind_follows_exhaustive_census"
    )
    assert owner_bind_rel >= 0
    owner_bind_block = relations[owner_bind_rel : owner_bind_rel + 1400]
    assert "ATLAS_AUTHORITY=NONE" in owner_bind_block
    vacancy_rel = relations.find(
        "id: REL:r_section_11_14_required_field_capture_seam_follows_owner_bind"
    )
    assert vacancy_rel >= 0
    vacancy_block = relations[vacancy_rel : vacancy_rel + 2200]
    assert "ATLAS_AUTHORITY=NONE" in vacancy_block
    architecture_rel = relations.find(
        "id: REL:r_section_11_14_architecture_adjudication_follows_required_field_capture_seam"
    )
    assert architecture_rel >= 0
    architecture_block = relations[architecture_rel : architecture_rel + 2200]
    assert "ATLAS_AUTHORITY=NONE" in architecture_block
    pos_binding_rel = relations.find(
        "id: REL:r_section_11_14_pos_semantics_canonical_binding_follows_architecture_adjudication"
    )
    assert pos_binding_rel >= 0
    pos_binding_block = relations[pos_binding_rel : pos_binding_rel + 2200]
    assert "ATLAS_AUTHORITY=NONE" in pos_binding_block
    producer_rel = relations.find(
        "id: REL:r_section_11_14_pos_producer_semantics_and_contract_follows_pos_semantics_canonical_binding"
    )
    assert producer_rel >= 0
    producer_block = relations[producer_rel : producer_rel + 2200]
    assert "ATLAS_AUTHORITY=NONE" in producer_block
    capture_rel = relations.find(
        "id: REL:r_section_11_14_complete_capture_seam_proof_follows_pos_producer_semantics_and_contract"
    )
    assert capture_rel >= 0
    capture_block = relations[capture_rel : capture_rel + 2200]
    assert "ATLAS_AUTHORITY=NONE" in capture_block
    implementation_rel = relations.find(
        "id: REL:r_section_11_14_pos_producer_capture_record_owner_and_writer_implementation_follows_complete_capture_seam_proof"
    )
    assert implementation_rel >= 0
    implementation_block = relations[implementation_rel : implementation_rel + 2200]
    assert "ATLAS_AUTHORITY=NONE" in implementation_block
    reader_bind_rel = relations.find(
        "id: REL:r_section_11_14_restart_reader_provenance_and_consumer_bind_follows_producer_owner_writer_implementation"
    )
    assert reader_bind_rel >= 0
    reader_bind_block = relations[reader_bind_rel : reader_bind_rel + 2200]
    assert "ATLAS_AUTHORITY=NONE" in reader_bind_block
    observation_rel = relations.find(
        "id: REL:r_section_11_14_contemporaneous_pre_restart_observation_follows_restart_reader_bind"
    )
    assert observation_rel >= 0
    observation_block = relations[observation_rel : observation_rel + 2200]
    assert "ATLAS_AUTHORITY=NONE" in observation_block
    capture_window_rel = relations.find(
        "id: REL:r_section_11_14_future_authorized_contemporaneous_capture_window_follows_observation"
    )
    assert capture_window_rel >= 0
    capture_window_block = relations[capture_window_rel : capture_window_rel + 2200]
    assert "ATLAS_AUTHORITY=NONE" in capture_window_block
    owner_hook_rel = relations.find(
        "id: REL:r_section_11_14_productive_capture_owner_and_lifecycle_hook_binding_follows_capture_window"
    )
    assert owner_hook_rel >= 0
    owner_hook_block = relations[owner_hook_rel : owner_hook_rel + 2200]
    assert "ATLAS_AUTHORITY=NONE" in owner_hook_block
    create_owner_hook_rel = relations.find(
        "id: REL:r_section_11_14_create_productive_capture_owner_and_lifecycle_hook_follows_case_b"
    )
    assert create_owner_hook_rel >= 0
    create_owner_hook_block = relations[create_owner_hook_rel : create_owner_hook_rel + 2200]
    assert "ATLAS_AUTHORITY=NONE" in create_owner_hook_block
    complete_seam_rel = relations.find(
        "id: REL:r_section_11_14_complete_contemporaneous_capture_seam_and_required_field_provenance_follows_create_owner"
    )
    assert complete_seam_rel >= 0
    complete_seam_block = relations[complete_seam_rel : complete_seam_rel + 2200]
    assert "ATLAS_AUTHORITY=NONE" in complete_seam_block
    no_backfill_rel = relations.find(
        "id: REL:r_section_11_14_complete_capture_seam_required_field_provenance_and_no_backfill_follows_hook_caller"
    )
    assert no_backfill_rel >= 0
    no_backfill_block = relations[no_backfill_rel : no_backfill_rel + 2200]
    assert "ATLAS_AUTHORITY=NONE" in no_backfill_block
    assert CODE_EXISTS_EVIDENCE.is_dir()
    verified = verify_manifest_v1(CODE_EXISTS_EVIDENCE)
    assert int(verified.get("MANIFEST_VERIFY_RC", 1)) == 0
    assert PATH_REACHABLE_EVIDENCE.is_dir()
    path_verified = verify_manifest_v1(PATH_REACHABLE_EVIDENCE)
    assert int(path_verified.get("MANIFEST_VERIFY_RC", 1)) == 0
    path_summary = (PATH_REACHABLE_EVIDENCE / "SUMMARY.json").read_text(encoding="utf-8")
    assert '"LIVE_EXECUTION_PATH_REACHABLE": true' in path_summary
    assert '"LIVE_PRIVATE_READ_ONLY_PROVEN": false' in path_summary
    assert PRIVATE_READ_ONLY_EVIDENCE.is_dir()
    new_verified = verify_manifest_v1(PRIVATE_READ_ONLY_EVIDENCE)
    assert int(new_verified.get("MANIFEST_VERIFY_RC", 1)) == 0
    summary = (PRIVATE_READ_ONLY_EVIDENCE / "SUMMARY.json").read_text(encoding="utf-8")
    assert '"LIVE_EXECUTION_PATH_REACHABLE": true' in summary
    assert '"LIVE_PRIVATE_READ_ONLY_PROVEN": true' in summary
    assert '"LIVE_ORDER_PLAN_OBSERVED": false' in summary
    assert HISTORICAL_EVIDENCE.is_dir()
    historical_verified = verify_manifest_v1(HISTORICAL_EVIDENCE)
    assert int(historical_verified.get("MANIFEST_VERIFY_RC", 1)) == 0
    assert ORDER_PLAN_EVIDENCE.is_dir()
    order_plan_verified = verify_manifest_v1(ORDER_PLAN_EVIDENCE)
    assert int(order_plan_verified.get("MANIFEST_VERIFY_RC", 1)) == 0
    order_plan_summary = (ORDER_PLAN_EVIDENCE / "SUMMARY.json").read_text(encoding="utf-8")
    assert '"LIVE_ORDER_PLAN_OBSERVED": true' in order_plan_summary
    assert '"LIVE_SUBMIT_ACK_OBSERVED": false' in order_plan_summary
    assert FORENSIC_ACK_EVIDENCE.is_dir()
    forensic_verified = verify_manifest_v1(FORENSIC_ACK_EVIDENCE)
    assert int(forensic_verified.get("MANIFEST_VERIFY_RC", 1)) == 0
    forensic_summary = (FORENSIC_ACK_EVIDENCE / "SUMMARY.json").read_text(encoding="utf-8")
    assert '"CASE_ADJUDICATION": "CASE_C_CANONICAL_SEMANTIC_GAP"' in forensic_summary
    assert PROOF_CRITERION_EVIDENCE.is_dir()
    proof_verified = verify_manifest_v1(PROOF_CRITERION_EVIDENCE)
    assert int(proof_verified.get("MANIFEST_VERIFY_RC", 1)) == 0
    proof_summary = (PROOF_CRITERION_EVIDENCE / "SUMMARY.json").read_text(encoding="utf-8")
    assert '"LIVE_SUBMIT_ACK_OBSERVED": false' in proof_summary
    assert '"CASE_ADJUDICATION": "CASE_A_READY_FOR_EXACT_SINGLE_POST_OWNER_GO"' in proof_summary
    assert (PROOF_CRITERION_EVIDENCE / "SUBMIT_ACK_ADJUDICATION.json").is_file()
    assert (PROOF_CRITERION_EVIDENCE / "SUBMIT_ACK_PROOF_CRITERION.json").is_file()
    assert (PROOF_CRITERION_EVIDENCE / "SUBMIT_ACK_OBSERVED_ADJUDICATION.json").is_file()
    assert (PROOF_CRITERION_EVIDENCE / "EXACT_MUTATION_CONTRACT.json").is_file()
    assert (PROOF_CRITERION_EVIDENCE / "SUBMIT_ACK_FAILURE_MATRIX.json").is_file()
    assert (PROOF_CRITERION_EVIDENCE / "POST_SUBMIT_RECON.json").is_file()
    assert SUBMIT_ACK_OBSERVED_EVIDENCE.is_dir()
    ack_verified = verify_manifest_v1(SUBMIT_ACK_OBSERVED_EVIDENCE)
    assert int(ack_verified.get("MANIFEST_VERIFY_RC", 1)) == 0
    ack_summary = (SUBMIT_ACK_OBSERVED_EVIDENCE / "SUMMARY.json").read_text(encoding="utf-8")
    assert '"LIVE_SUBMIT_ACK_OBSERVED": true' in ack_summary
    assert '"LIVE_FILL_OBSERVED": false' in ack_summary
    assert '"PRODUCTIVE_POST_ATTEMPTED": true' in ack_summary
    assert '"PRODUCTIVE_POST_ATTEMPT_COUNT": 1' in ack_summary
    assert '"RETRY_PERFORMED": false' in ack_summary
    assert '"SECOND_SUBMIT_PERFORMED": false' in ack_summary
    assert '"ACK_SOURCE_KIND": "GOVERNED_CURRENT_LIVE_POST"' in ack_summary
    assert (SUBMIT_ACK_OBSERVED_EVIDENCE / "SUBMIT_ACK_OBSERVED_ADJUDICATION.json").is_file()
    assert FILL_OBSERVED_EVIDENCE.is_dir()
    fill_verified = verify_manifest_v1(FILL_OBSERVED_EVIDENCE)
    assert int(fill_verified.get("MANIFEST_VERIFY_RC", 1)) == 0
    fill_summary = (FILL_OBSERVED_EVIDENCE / "SUMMARY.json").read_text(encoding="utf-8")
    assert '"LIVE_FILL_OBSERVED": true' in fill_summary
    assert '"LIVE_FEE_OBSERVED": false' in fill_summary
    assert '"CASE_ADJUDICATION": "CASE_LIVE_FILL_OBSERVED_FEE_INELIGIBLE"' in fill_summary
    assert FEE_OBSERVED_EVIDENCE.is_dir()
    fee_verified = verify_manifest_v1(FEE_OBSERVED_EVIDENCE)
    assert int(fee_verified.get("MANIFEST_VERIFY_RC", 1)) == 0
    fee_summary = (FEE_OBSERVED_EVIDENCE / "SUMMARY.json").read_text(encoding="utf-8")
    assert '"LIVE_FEE_OBSERVED": true' in fee_summary
    assert '"LIVE_POSITION_RECONCILED": false' in fee_summary
    assert '"CASE_ADJUDICATION": "CASE_LIVE_FEE_OBSERVED_POSITION_INELIGIBLE"' in fee_summary
    assert (FEE_OBSERVED_EVIDENCE / "FEE_OBSERVED_ADJUDICATION.json").is_file()
    assert (FEE_OBSERVED_EVIDENCE / "GET_FILLS.raw.json").is_file()
    assert POSITION_RECONCILED_EVIDENCE.is_dir()
    position_verified = verify_manifest_v1(POSITION_RECONCILED_EVIDENCE)
    assert int(position_verified.get("MANIFEST_VERIFY_RC", 1)) == 0
    position_summary = (POSITION_RECONCILED_EVIDENCE / "SUMMARY.json").read_text(encoding="utf-8")
    assert '"LIVE_POSITION_RECONCILED": true' in position_summary
    assert '"LIVE_ACCOUNTING_RECONSTRUCTED": false' in position_summary
    assert (
        '"CASE_ADJUDICATION": "CASE_LIVE_POSITION_RECONCILED_ACCOUNTING_INELIGIBLE"'
        in position_summary
    )
    assert (POSITION_RECONCILED_EVIDENCE / "POSITION_RECONCILED_ADJUDICATION.json").is_file()
    assert (POSITION_RECONCILED_EVIDENCE / "GET_POSITIONS.raw.json").is_file()
    assert ACCOUNTING_RECONSTRUCTED_EVIDENCE.is_dir()
    accounting_verified = verify_manifest_v1(ACCOUNTING_RECONSTRUCTED_EVIDENCE)
    assert int(accounting_verified.get("MANIFEST_VERIFY_RC", 1)) == 0
    accounting_summary = (ACCOUNTING_RECONSTRUCTED_EVIDENCE / "SUMMARY.json").read_text(
        encoding="utf-8"
    )
    assert '"LIVE_ACCOUNTING_RECONSTRUCTED": true' in accounting_summary
    assert '"LIVE_RESTART_RECONSTRUCTED": false' in accounting_summary
    assert (
        '"CASE_ADJUDICATION": "CASE_LIVE_ACCOUNTING_RECONSTRUCTED_RESTART_INELIGIBLE"'
        in accounting_summary
    )
    assert (
        ACCOUNTING_RECONSTRUCTED_EVIDENCE / "ACCOUNTING_RECONSTRUCTED_ADJUDICATION.json"
    ).is_file()
    assert HISTORICAL_RESTART_EVIDENCE.is_dir()
    historical_restart_verified = verify_manifest_v1(HISTORICAL_RESTART_EVIDENCE)
    assert int(historical_restart_verified.get("MANIFEST_VERIFY_RC", 1)) == 0
    historical_restart_summary = (HISTORICAL_RESTART_EVIDENCE / "SUMMARY.json").read_text(
        encoding="utf-8"
    )
    assert '"LIVE_RESTART_RECONSTRUCTED": false' in historical_restart_summary
    assert HISTORICAL_EXHAUSTIVE_EVIDENCE.is_dir()
    historical_exhaustive_verified = verify_manifest_v1(HISTORICAL_EXHAUSTIVE_EVIDENCE)
    assert int(historical_exhaustive_verified.get("MANIFEST_VERIFY_RC", 1)) == 0
    historical_exhaustive_summary = (HISTORICAL_EXHAUSTIVE_EVIDENCE / "SUMMARY.json").read_text(
        encoding="utf-8"
    )
    assert '"LIVE_RESTART_RECONSTRUCTED": false' in historical_exhaustive_summary
    assert (HISTORICAL_EXHAUSTIVE_EVIDENCE / "EXHAUSTIVE_CENSUS.json").is_file()
    assert HISTORICAL_OWNER_BIND_EVIDENCE.is_dir()
    historical_owner_bind_verified = verify_manifest_v1(HISTORICAL_OWNER_BIND_EVIDENCE)
    assert int(historical_owner_bind_verified.get("MANIFEST_VERIFY_RC", 1)) == 0
    historical_owner_bind_summary = (HISTORICAL_OWNER_BIND_EVIDENCE / "SUMMARY.json").read_text(
        encoding="utf-8"
    )
    assert '"LIVE_ACCOUNTING_RECONSTRUCTED": true' in historical_owner_bind_summary
    assert '"LIVE_RESTART_RECONSTRUCTED": false' in historical_owner_bind_summary
    assert '"SECTION_11_14_LIVE_HANDOFF_OWNER_CURRENT": "NONE"' in historical_owner_bind_summary
    assert '"RETROACTIVE_HANDOFF_SYNTHESIS_ALLOWED": false' in historical_owner_bind_summary
    assert (HISTORICAL_OWNER_BIND_EVIDENCE / "HANDOFF_OWNER_BIND.json").is_file()
    assert (HISTORICAL_OWNER_BIND_EVIDENCE / "OWNER_CENSUS_MATRIX.json").is_file()
    assert (HISTORICAL_OWNER_BIND_EVIDENCE / "RETROACTIVE_SYNTHESIS_REFUSAL.json").is_file()
    assert (HISTORICAL_OWNER_BIND_EVIDENCE / "HISTORICAL_UNPROVABILITY_BIND.json").is_file()
    assert HISTORICAL_REQUIRED_FIELD_CAPTURE_SEAM_EVIDENCE.is_dir()
    historical_vacancy_verified = verify_manifest_v1(
        HISTORICAL_REQUIRED_FIELD_CAPTURE_SEAM_EVIDENCE
    )
    assert int(historical_vacancy_verified.get("MANIFEST_VERIFY_RC", 1)) == 0
    historical_vacancy_summary = (
        HISTORICAL_REQUIRED_FIELD_CAPTURE_SEAM_EVIDENCE / "SUMMARY.json"
    ).read_text(encoding="utf-8")
    assert '"LIVE_ACCOUNTING_RECONSTRUCTED": true' in historical_vacancy_summary
    assert '"LIVE_RESTART_RECONSTRUCTED": false' in historical_vacancy_summary
    assert '"SECTION_11_14_LIVE_HANDOFF_OWNER_CURRENT": "NONE"' in historical_vacancy_summary
    assert '"POS_SEMANTICS": "UNPROVEN"' in historical_vacancy_summary
    assert '"COMPLETE_CAPTURE_SEAM": "UNPROVEN"' in historical_vacancy_summary
    assert (
        '"OWNER_VACANCY_CONTRACT_STATUS": "BOUND_CAPTURE_SEAM_UNPROVEN"'
        in historical_vacancy_summary
    )
    assert (
        HISTORICAL_REQUIRED_FIELD_CAPTURE_SEAM_EVIDENCE / "OWNER_VACANCY_CONTRACT.json"
    ).is_file()
    assert HISTORICAL_ARCHITECTURE_ADJUDICATION_EVIDENCE.is_dir()
    historical_architecture_verified = verify_manifest_v1(
        HISTORICAL_ARCHITECTURE_ADJUDICATION_EVIDENCE
    )
    assert int(historical_architecture_verified.get("MANIFEST_VERIFY_RC", 1)) == 0
    historical_architecture_summary = (
        HISTORICAL_ARCHITECTURE_ADJUDICATION_EVIDENCE / "SUMMARY.json"
    ).read_text(encoding="utf-8")
    assert '"LIVE_ACCOUNTING_RECONSTRUCTED": true' in historical_architecture_summary
    assert '"LIVE_RESTART_RECONSTRUCTED": false' in historical_architecture_summary
    assert '"SECTION_11_14_LIVE_HANDOFF_OWNER_CURRENT": "NONE"' in historical_architecture_summary
    assert '"POS_SEMANTICS": "UNPROVEN"' in historical_architecture_summary
    assert '"COMPLETE_CAPTURE_SEAM": "UNPROVEN"' in historical_architecture_summary
    assert '"ARCHITECTURE_ADJUDICATION_COMPLETE": true' in historical_architecture_summary
    assert '"IMPLEMENTATION_AUTHORIZED": false' in historical_architecture_summary
    assert (
        HISTORICAL_ARCHITECTURE_ADJUDICATION_EVIDENCE / "ARCHITECTURE_ADJUDICATION.json"
    ).is_file()
    assert HISTORICAL_POS_SEMANTICS_CANONICAL_BINDING_EVIDENCE.is_dir()
    historical_pos_binding_verified = verify_manifest_v1(
        HISTORICAL_POS_SEMANTICS_CANONICAL_BINDING_EVIDENCE
    )
    assert int(historical_pos_binding_verified.get("MANIFEST_VERIFY_RC", 1)) == 0
    historical_pos_binding_summary = (
        HISTORICAL_POS_SEMANTICS_CANONICAL_BINDING_EVIDENCE / "SUMMARY.json"
    ).read_text(encoding="utf-8")
    assert '"LIVE_ACCOUNTING_RECONSTRUCTED": true' in historical_pos_binding_summary
    assert '"LIVE_RESTART_RECONSTRUCTED": false' in historical_pos_binding_summary
    assert '"SECTION_11_14_LIVE_HANDOFF_OWNER_CURRENT": "NONE"' in historical_pos_binding_summary
    assert '"POS_SEMANTICS": "UNPROVEN"' in historical_pos_binding_summary
    assert (
        '"POS_SEMANTICS_CAN_BE_BOUND_FROM_EXISTING_AUTHORITY": false'
        in historical_pos_binding_summary
    )
    assert '"NEW_CONTEMPORANEOUS_POS_PRODUCER_REQUIRED": true' in historical_pos_binding_summary
    assert '"POS_ACCEPTABLE_PRODUCER_COUNT": 0' in historical_pos_binding_summary
    assert '"COMPLETE_CAPTURE_SEAM": "UNPROVEN"' in historical_pos_binding_summary
    assert '"IMPLEMENTATION_AUTHORIZED": false' in historical_pos_binding_summary
    assert (
        HISTORICAL_POS_SEMANTICS_CANONICAL_BINDING_EVIDENCE / "POS_SEMANTICS_CANONICAL_BINDING.json"
    ).is_file()
    assert HISTORICAL_POS_PRODUCER_SEMANTICS_AND_CONTRACT_EVIDENCE.is_dir()
    historical_producer_verified = verify_manifest_v1(
        HISTORICAL_POS_PRODUCER_SEMANTICS_AND_CONTRACT_EVIDENCE
    )
    assert int(historical_producer_verified.get("MANIFEST_VERIFY_RC", 1)) == 0
    historical_producer_summary = (
        HISTORICAL_POS_PRODUCER_SEMANTICS_AND_CONTRACT_EVIDENCE / "SUMMARY.json"
    ).read_text(encoding="utf-8")
    assert '"LIVE_ACCOUNTING_RECONSTRUCTED": true' in historical_producer_summary
    assert '"LIVE_RESTART_RECONSTRUCTED": false' in historical_producer_summary
    assert '"SECTION_11_14_LIVE_HANDOFF_OWNER_CURRENT": "NONE"' in historical_producer_summary
    assert '"POS_SEMANTICS": "PROVEN"' in historical_producer_summary
    assert '"NEW_PRODUCER_IMPLEMENTED": false' in historical_producer_summary
    assert '"COMPLETE_CAPTURE_SEAM": "UNPROVEN"' in historical_producer_summary
    assert '"COMPLETE_CAPTURE_SEAM_CAN_NOW_BE_ADJUDICATED": true' in historical_producer_summary
    assert '"IMPLEMENTATION_AUTHORIZED": false' in historical_producer_summary
    assert (
        HISTORICAL_POS_PRODUCER_SEMANTICS_AND_CONTRACT_EVIDENCE
        / "POS_PRODUCER_SEMANTICS_AND_CONTRACT.json"
    ).is_file()
    assert HISTORICAL_COMPLETE_CAPTURE_SEAM_PROOF_EVIDENCE.is_dir()
    historical_capture_verified = verify_manifest_v1(
        HISTORICAL_COMPLETE_CAPTURE_SEAM_PROOF_EVIDENCE
    )
    assert int(historical_capture_verified.get("MANIFEST_VERIFY_RC", 1)) == 0
    historical_capture_summary = (
        HISTORICAL_COMPLETE_CAPTURE_SEAM_PROOF_EVIDENCE / "SUMMARY.json"
    ).read_text(encoding="utf-8")
    assert '"LIVE_ACCOUNTING_RECONSTRUCTED": true' in historical_capture_summary
    assert '"LIVE_RESTART_RECONSTRUCTED": false' in historical_capture_summary
    assert '"SECTION_11_14_LIVE_HANDOFF_OWNER_CURRENT": "NONE"' in historical_capture_summary
    assert '"POS_SEMANTICS": "PROVEN"' in historical_capture_summary
    assert '"NEW_PRODUCER_IMPLEMENTED": false' in historical_capture_summary
    assert '"STORAGE_OWNER_MINTED": false' in historical_capture_summary
    assert '"WRITER_BOUND": false' in historical_capture_summary
    assert '"READER_BOUND": false' in historical_capture_summary
    assert '"COMPLETE_CAPTURE_SEAM": "UNPROVEN"' in historical_capture_summary
    assert '"COMPLETE_CAPTURE_SEAM_PROOF_STATUS": "CLOSED_UNPROVEN_NO_INVENTION"' in (
        historical_capture_summary
    )
    assert '"IMPLEMENTATION_AUTHORIZED": false' in historical_capture_summary
    assert (
        HISTORICAL_COMPLETE_CAPTURE_SEAM_PROOF_EVIDENCE / "COMPLETE_CAPTURE_SEAM_PROOF.json"
    ).is_file()
    assert (
        HISTORICAL_COMPLETE_CAPTURE_SEAM_PROOF_EVIDENCE / "COMPLETE_CAPTURE_SEAM_PREDICATE.json"
    ).is_file()
    assert HISTORICAL_IMPLEMENTATION_EVIDENCE.is_dir()
    historical_implementation_verified = verify_manifest_v1(HISTORICAL_IMPLEMENTATION_EVIDENCE)
    assert int(historical_implementation_verified.get("MANIFEST_VERIFY_RC", 1)) == 0
    historical_implementation_summary = (
        HISTORICAL_IMPLEMENTATION_EVIDENCE / "SUMMARY.json"
    ).read_text(encoding="utf-8")
    assert '"LIVE_ACCOUNTING_RECONSTRUCTED": true' in historical_implementation_summary
    assert '"LIVE_RESTART_RECONSTRUCTED": false' in historical_implementation_summary
    assert '"NEW_PRODUCER_IMPLEMENTED": true' in historical_implementation_summary
    assert '"STORAGE_OWNER_MINTED": true' in historical_implementation_summary
    assert '"WRITER_BOUND": true' in historical_implementation_summary
    assert '"READER_BOUND": false' in historical_implementation_summary
    assert '"COMPLETE_CAPTURE_SEAM": "UNPROVEN"' in historical_implementation_summary
    assert '"HOST_CRASH_DURABILITY": "UNPROVEN"' in historical_implementation_summary
    assert '"IMPLEMENTATION_AUTHORIZED": false' in historical_implementation_summary
    assert (HISTORICAL_IMPLEMENTATION_EVIDENCE / "IMPLEMENTATION_BINDING.json").is_file()
    assert (HISTORICAL_IMPLEMENTATION_EVIDENCE / "OWNER_MINT.json").is_file()
    assert (HISTORICAL_IMPLEMENTATION_EVIDENCE / "PRODUCER.json").is_file()
    assert (HISTORICAL_IMPLEMENTATION_EVIDENCE / "WRITER_BINDING.json").is_file()
    assert HISTORICAL_READER_BIND_EVIDENCE.is_dir()
    historical_reader_bind_verified = verify_manifest_v1(HISTORICAL_READER_BIND_EVIDENCE)
    assert int(historical_reader_bind_verified.get("MANIFEST_VERIFY_RC", 1)) == 0
    historical_reader_bind_summary = (HISTORICAL_READER_BIND_EVIDENCE / "SUMMARY.json").read_text(
        encoding="utf-8"
    )
    assert '"LIVE_ACCOUNTING_RECONSTRUCTED": true' in historical_reader_bind_summary
    assert '"LIVE_RESTART_RECONSTRUCTED": false' in historical_reader_bind_summary
    assert '"READER_BOUND": true' in historical_reader_bind_summary
    assert '"RESTART_CONSUMER_BOUND": true' in historical_reader_bind_summary
    assert '"PROVENANCE_VALIDATION": "CONTRACT_PROVEN"' in historical_reader_bind_summary
    assert '"FRESHNESS_VALIDATION": "PARTIAL"' in historical_reader_bind_summary
    assert '"COMPLETE_CAPTURE_SEAM": "UNPROVEN"' in historical_reader_bind_summary
    assert '"HOST_CRASH_DURABILITY": "UNPROVEN"' in historical_reader_bind_summary
    assert (
        '"CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_HANDOFF_OBSERVED": false'
        in historical_reader_bind_summary
    )
    assert '"IMPLEMENTATION_AUTHORIZED": false' in historical_reader_bind_summary
    assert (HISTORICAL_READER_BIND_EVIDENCE / "READER_BINDING.json").is_file()
    assert (HISTORICAL_READER_BIND_EVIDENCE / "READER_CENSUS.json").is_file()
    assert (HISTORICAL_READER_BIND_EVIDENCE / "CONSUMER_BINDING.json").is_file()
    assert (HISTORICAL_READER_BIND_EVIDENCE / "VALIDATION_MATRIX.json").is_file()
    assert (HISTORICAL_READER_BIND_EVIDENCE / "FAILURE_MATRIX.json").is_file()
    assert (HISTORICAL_READER_BIND_EVIDENCE / "COMPLETE_CAPTURE_SEAM_PREDICATE.json").is_file()
    assert (HISTORICAL_READER_BIND_EVIDENCE / "OWNER_MINT.json").is_file()
    assert (HISTORICAL_READER_BIND_EVIDENCE / "RESTART_RECONSTRUCTED_ADJUDICATION.json").is_file()
    assert (HISTORICAL_READER_BIND_EVIDENCE / "SAFETY.json").is_file()
    assert HISTORICAL_CONTEMPORANEOUS_OBSERVATION_EVIDENCE.is_dir()
    historical_observation_verified = verify_manifest_v1(
        HISTORICAL_CONTEMPORANEOUS_OBSERVATION_EVIDENCE
    )
    assert int(historical_observation_verified.get("MANIFEST_VERIFY_RC", 1)) == 0
    historical_observation_summary = (
        HISTORICAL_CONTEMPORANEOUS_OBSERVATION_EVIDENCE / "SUMMARY.json"
    ).read_text(encoding="utf-8")
    assert '"LIVE_ACCOUNTING_RECONSTRUCTED": true' in historical_observation_summary
    assert '"LIVE_RESTART_RECONSTRUCTED": false' in historical_observation_summary
    assert '"OBSERVATION_STATUS": "CLOSED_REFUTED"' in historical_observation_summary
    assert '"READ_BACK_RESULT": "MISSING_HANDOFF"' in historical_observation_summary
    assert '"AUTHORIZED_NON_LIVE_RUNTIME_SURFACE_PRESENT": false' in historical_observation_summary
    assert '"PRODUCTIVE_CAPTURE_WRITE_EXECUTED": false' in historical_observation_summary
    assert '"COMPLETE_CAPTURE_SEAM": "UNPROVEN"' in historical_observation_summary
    assert '"HOST_CRASH_DURABILITY": "UNPROVEN"' in historical_observation_summary
    assert (
        '"CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_HANDOFF_OBSERVED": false'
        in historical_observation_summary
    )
    assert '"IMPLEMENTATION_AUTHORIZED": false' in historical_observation_summary
    assert (
        HISTORICAL_CONTEMPORANEOUS_OBSERVATION_EVIDENCE / "CAPTURE_TRIGGER_AND_PRODUCER.json"
    ).is_file()
    assert (HISTORICAL_CONTEMPORANEOUS_OBSERVATION_EVIDENCE / "READ_BACK.json").is_file()
    assert (
        HISTORICAL_CONTEMPORANEOUS_OBSERVATION_EVIDENCE / "OBSERVABILITY_ADJUDICATION.json"
    ).is_file()
    assert HISTORICAL_FUTURE_CAPTURE_WINDOW_EVIDENCE.is_dir()
    historical_capture_window_verified = verify_manifest_v1(
        HISTORICAL_FUTURE_CAPTURE_WINDOW_EVIDENCE
    )
    assert int(historical_capture_window_verified.get("MANIFEST_VERIFY_RC", 1)) == 0
    historical_capture_window_summary = (
        HISTORICAL_FUTURE_CAPTURE_WINDOW_EVIDENCE / "SUMMARY.json"
    ).read_text(encoding="utf-8")
    assert '"LIVE_ACCOUNTING_RECONSTRUCTED": true' in historical_capture_window_summary
    assert '"LIVE_RESTART_RECONSTRUCTED": false' in historical_capture_window_summary
    assert '"PRODUCTIVE_CAPTURE_OWNER_STATUS": "ABSENT"' in historical_capture_window_summary
    assert '"PRODUCTIVE_CAPTURE_HOOK_STATUS": "ABSENT"' in historical_capture_window_summary
    assert '"CAPTURE_WINDOW_ORDERING": "UNPROVEN"' in historical_capture_window_summary
    assert (
        '"MINIMUM_FUTURE_CAPTURE_WINDOW_SURFACE": "UNPROVEN"' in historical_capture_window_summary
    )
    assert (
        '"PRODUCTIVE_BINDING_ALLOWED_IN_THIS_WORKPACKAGE": false'
        in historical_capture_window_summary
    )
    assert '"PRODUCTIVE_BINDING_IMPLEMENTED": false' in historical_capture_window_summary
    assert (HISTORICAL_FUTURE_CAPTURE_WINDOW_EVIDENCE / "RUNTIME_GRAPH.json").is_file()
    assert (HISTORICAL_FUTURE_CAPTURE_WINDOW_EVIDENCE / "BOUND_FILL_SEMANTICS.json").is_file()
    assert (HISTORICAL_FUTURE_CAPTURE_WINDOW_EVIDENCE / "CAPTURE_WINDOW_SEMANTICS.json").is_file()
    assert (
        HISTORICAL_FUTURE_CAPTURE_WINDOW_EVIDENCE / "AUTHORIZATION_SURFACE_MATRIX.json"
    ).is_file()
    assert (
        HISTORICAL_FUTURE_CAPTURE_WINDOW_EVIDENCE / "MINIMUM_FUTURE_CAPTURE_WINDOW.json"
    ).is_file()
    assert (
        HISTORICAL_FUTURE_CAPTURE_WINDOW_EVIDENCE / "PRODUCTIVE_BINDING_DECISION.json"
    ).is_file()
    assert HISTORICAL_PRODUCTIVE_CAPTURE_OWNER_HOOK_BINDING_EVIDENCE.is_dir()
    historical_owner_hook_verified = verify_manifest_v1(
        HISTORICAL_PRODUCTIVE_CAPTURE_OWNER_HOOK_BINDING_EVIDENCE
    )
    assert int(historical_owner_hook_verified.get("MANIFEST_VERIFY_RC", 1)) == 0
    historical_owner_hook_summary = (
        HISTORICAL_PRODUCTIVE_CAPTURE_OWNER_HOOK_BINDING_EVIDENCE / "SUMMARY.json"
    ).read_text(encoding="utf-8")
    assert '"LIVE_ACCOUNTING_RECONSTRUCTED": true' in historical_owner_hook_summary
    assert '"LIVE_RESTART_RECONSTRUCTED": false' in historical_owner_hook_summary
    assert '"PRODUCTIVE_CAPTURE_OWNER_STATUS": "REFUTED"' in historical_owner_hook_summary
    assert '"PRODUCTIVE_LIFECYCLE_HOOK_STATUS": "REFUTED"' in historical_owner_hook_summary
    assert '"AUTHORIZED_RUNTIME_SURFACE": "NONE"' in historical_owner_hook_summary
    assert '"AUTHORIZED_RUNTIME_SURFACE_PROVEN": false' in historical_owner_hook_summary
    assert '"BINDING_CASE": "CASE_B"' in historical_owner_hook_summary
    assert '"MINIMAL_FAIL_CLOSED_BINDING_ALLOWED": false' in historical_owner_hook_summary
    assert '"PRODUCTIVE_BINDING_IMPLEMENTED": false' in historical_owner_hook_summary
    assert '"CURRENT_PRODUCTIVE_CALLER_COUNT_FOR_PRODUCER": 0' in historical_owner_hook_summary
    assert '"CURRENT_PRODUCTIVE_CALLER_COUNT_FOR_WRITER": 0' in historical_owner_hook_summary
    assert '"IMPLEMENTATION_AUTHORIZED": false' in historical_owner_hook_summary
    assert (HISTORICAL_PRODUCTIVE_CAPTURE_OWNER_HOOK_BINDING_EVIDENCE / "PATH_GRAPH.json").is_file()
    assert (
        HISTORICAL_PRODUCTIVE_CAPTURE_OWNER_HOOK_BINDING_EVIDENCE / "OWNER_CENSUS.json"
    ).is_file()
    assert (
        HISTORICAL_PRODUCTIVE_CAPTURE_OWNER_HOOK_BINDING_EVIDENCE / "HOOK_CENSUS.json"
    ).is_file()
    assert (
        HISTORICAL_PRODUCTIVE_CAPTURE_OWNER_HOOK_BINDING_EVIDENCE
        / "PRODUCTIVE_BINDING_DECISION.json"
    ).is_file()
    assert HISTORICAL_CREATE_PRODUCTIVE_CAPTURE_OWNER_HOOK_EVIDENCE.is_dir()
    historical_create_owner_verified = verify_manifest_v1(
        HISTORICAL_CREATE_PRODUCTIVE_CAPTURE_OWNER_HOOK_EVIDENCE
    )
    assert int(historical_create_owner_verified.get("MANIFEST_VERIFY_RC", 1)) == 0
    historical_create_owner_summary = (
        HISTORICAL_CREATE_PRODUCTIVE_CAPTURE_OWNER_HOOK_EVIDENCE / "SUMMARY.json"
    ).read_text(encoding="utf-8")
    assert '"LIVE_ACCOUNTING_RECONSTRUCTED": true' in historical_create_owner_summary
    assert '"LIVE_RESTART_RECONSTRUCTED": false' in historical_create_owner_summary
    assert '"BINDING_CASE": "CASE_A_CREATED"' in historical_create_owner_summary
    assert '"PRODUCTIVE_BINDING_IMPLEMENTED": true' in historical_create_owner_summary
    assert '"CURRENT_PRODUCTIVE_CALLER_COUNT_FOR_PRODUCER": 0' in historical_create_owner_summary
    assert '"CURRENT_PRODUCTIVE_CALLER_COUNT_FOR_WRITER": 1' in historical_create_owner_summary
    assert '"IMPLEMENTATION_AUTHORIZED": true' in historical_create_owner_summary
    assert (
        HISTORICAL_CREATE_PRODUCTIVE_CAPTURE_OWNER_HOOK_EVIDENCE / "CALLER_GRAPH.json"
    ).is_file()
    assert (
        HISTORICAL_CREATE_PRODUCTIVE_CAPTURE_OWNER_HOOK_EVIDENCE / "OWNER_HOOK_CENSUS.json"
    ).is_file()
    assert HISTORICAL_COMPLETE_CONTEMPORANEOUS_CAPTURE_SEAM_EVIDENCE.is_dir()
    historical_complete_seam_verified = verify_manifest_v1(
        HISTORICAL_COMPLETE_CONTEMPORANEOUS_CAPTURE_SEAM_EVIDENCE
    )
    assert int(historical_complete_seam_verified.get("MANIFEST_VERIFY_RC", 1)) == 0
    assert (
        HISTORICAL_COMPLETE_CONTEMPORANEOUS_CAPTURE_SEAM_EVIDENCE / "DATAFLOW_CENSUS.json"
    ).is_file()
    assert (
        HISTORICAL_COMPLETE_CONTEMPORANEOUS_CAPTURE_SEAM_EVIDENCE
        / "REQUIRED_FIELD_PROVENANCE_MATRIX.json"
    ).is_file()
    assert (
        HISTORICAL_COMPLETE_CONTEMPORANEOUS_CAPTURE_SEAM_EVIDENCE
        / "CONTEMPORANEOUSNESS_ADJUDICATION.json"
    ).is_file()
    assert HISTORICAL_PRODUCTIVE_HOOK_CALLER_BINDING_EVIDENCE.is_dir()
    historical_caller_verified = verify_manifest_v1(
        HISTORICAL_PRODUCTIVE_HOOK_CALLER_BINDING_EVIDENCE
    )
    assert int(historical_caller_verified.get("MANIFEST_VERIFY_RC", 1)) == 0
    historical_caller_summary = (
        HISTORICAL_PRODUCTIVE_HOOK_CALLER_BINDING_EVIDENCE / "SUMMARY.json"
    ).read_text(encoding="utf-8")
    assert '"COMPLETE_CAPTURE_SEAM": "UNPROVEN"' in historical_caller_summary
    assert '"PRODUCTIVE_HOOK_CALLER_BINDING_PROVEN": true' in historical_caller_summary
    assert '"PRODUCTIVE_CALL_PATH_OFFLINE_PROOF": true' in historical_caller_summary
    assert '"PROVENANCE_VALIDATED_CONTEMPORANEOUS_NO_BACKFILL": false' in historical_caller_summary
    assert '"CONTEMPORANEOUS_PRODUCTIVE_CAPTURE_EXECUTED": false' in historical_caller_summary
    assert HISTORICAL_COMPLETE_CAPTURE_SEAM_NO_BACKFILL_CONTRACT_EVIDENCE.is_dir()
    historical_no_backfill_verified = verify_manifest_v1(
        HISTORICAL_COMPLETE_CAPTURE_SEAM_NO_BACKFILL_CONTRACT_EVIDENCE
    )
    assert int(historical_no_backfill_verified.get("MANIFEST_VERIFY_RC", 1)) == 0
    historical_no_backfill_summary = (
        HISTORICAL_COMPLETE_CAPTURE_SEAM_NO_BACKFILL_CONTRACT_EVIDENCE / "SUMMARY.json"
    ).read_text(encoding="utf-8")
    assert '"COMPLETE_CAPTURE_SEAM": "PROVEN"' in historical_no_backfill_summary
    assert '"NO_BACKFILL_CONTRACT_PROVEN": true' in historical_no_backfill_summary
    assert (
        '"PROVENANCE_VALIDATED_CONTEMPORANEOUS_NO_BACKFILL": true' in historical_no_backfill_summary
    )
    assert '"REQUIRED_FIELD_PROVENANCE_COMPLETE": true' in historical_no_backfill_summary
    assert '"PROVEN_FAIL_CLOSED_FIELD_COUNT": 5' in historical_no_backfill_summary
    assert '"PROVEN_COMPLETE_FIELD_COUNT": 0' in historical_no_backfill_summary
    assert (
        HISTORICAL_COMPLETE_CAPTURE_SEAM_NO_BACKFILL_CONTRACT_EVIDENCE / "DATAFLOW_CENSUS.json"
    ).is_file()
    assert (
        HISTORICAL_COMPLETE_CAPTURE_SEAM_NO_BACKFILL_CONTRACT_EVIDENCE
        / "REQUIRED_FIELD_PROVENANCE_MATRIX.json"
    ).is_file()
    assert (
        HISTORICAL_COMPLETE_CAPTURE_SEAM_NO_BACKFILL_CONTRACT_EVIDENCE
        / "REQUIRED_FIELD_PROVENANCE_TABLE.json"
    ).is_file()
    assert (
        HISTORICAL_COMPLETE_CAPTURE_SEAM_NO_BACKFILL_CONTRACT_EVIDENCE / "CALLER_CENSUS.json"
    ).is_file()
    assert (
        HISTORICAL_COMPLETE_CAPTURE_SEAM_NO_BACKFILL_CONTRACT_EVIDENCE
        / "COMPLETE_CAPTURE_SEAM_PREDICATE.json"
    ).is_file()
    assert EVIDENCE.is_dir()
    current_verified = verify_manifest_v1(EVIDENCE)
    assert int(current_verified.get("MANIFEST_VERIFY_RC", 1)) == 0
    current_summary = (EVIDENCE / "SUMMARY.json").read_text(encoding="utf-8")
    assert '"LIVE_ACCOUNTING_RECONSTRUCTED": true' in current_summary
    assert '"LIVE_RESTART_RECONSTRUCTED": false' in current_summary
    assert '"LIVE_AUTONOMOUS_RECOVERY_OBSERVED": false' in current_summary
    assert '"POST_USED": false' in current_summary
    assert '"GET_PERFORMED": false' in current_summary
    assert '"CREDENTIAL_USE": false' in current_summary
    assert '"RESTART_EXECUTION": false' in current_summary
    assert (
        '"SECTION_11_14_LIVE_HANDOFF_OWNER_CURRENT": "SECTION_11_14_LIVE_DURABLE_PRE_RESTART_HANDOFF_OWNER_V1"'
        in current_summary
    )
    assert '"COMPLETE_CAPTURE_SEAM": "PROVEN"' in current_summary
    assert '"COMPLETE_CAPTURE_SEAM_ACCEPTANCE_CONTRACT_BOUND": true' in current_summary
    assert '"REQUIRED_FIELD_PROVENANCE_MATRIX_BOUND": true' in current_summary
    assert '"REQUIRED_FIELD_PROVENANCE_COMPLETE": true' in current_summary
    assert '"NO_BACKFILL_CONTRACT_PROVEN": true' in current_summary
    assert '"PROVENANCE_VALIDATED_CONTEMPORANEOUS_NO_BACKFILL": true' in current_summary
    assert '"CONTEMPORANEOUS_CAPTURE_RUNTIME_SURFACE": "PROVEN"' in current_summary
    assert '"CONTEMPORANEOUS_CAPTURE_SIDE_EFFECT_BOUNDARY": "PROVEN"' in current_summary
    assert '"CONTEMPORANEOUS_CAPTURE_CAN_BE_ISOLATED_FROM_LIVE_EXECUTION": false' in current_summary
    assert '"CONTEMPORANEOUS_CAPTURE_EXECUTION_PRECONDITIONS_COMPLETE": true' in current_summary
    assert '"MINIMAL_FUTURE_AUTHORIZED_ENTRYPOINT": "NONE_CAPTURE_ONLY"' in current_summary
    assert '"UNAVOIDABLE_EXTERNAL_EFFECTS": "LIVE_IDENTITY_BOUND_VENUE_FILL"' in current_summary
    assert '"EARLIEST_IRREVERSIBLE_EFFECT": "VENUE_FILL_OF_IDENTITY_BOUND_ORDER"' in current_summary
    assert (
        '"PRODUCTIVE_RUNTIME_ENTRYPOINT": "run_live_order_pre_restart_handoff_capture_v1"'
        in current_summary
    )
    assert '"CONTEMPORANEOUS_PRODUCTIVE_CAPTURE_EXECUTED": false' in current_summary
    assert '"HOST_CRASH_DURABILITY": "UNPROVEN"' in current_summary
    assert '"CONTEMPORANEOUS_PEAK_TRADE_PRE_RESTART_HANDOFF_OBSERVED": false' in current_summary
    assert (
        '"PRODUCTIVE_CAPTURE_OWNER": "SECTION_11_14_LIVE_PRODUCTIVE_CAPTURE_OWNER_V1"'
        in current_summary
    )
    assert (
        '"PRODUCTIVE_LIFECYCLE_HOOK": "run_capture_hook_after_bound_fill_before_restart_v1"'
        in current_summary
    )
    assert (
        '"PRODUCTIVE_HOOK_CALLER": "call_pre_restart_handoff_capture_after_bound_fill_v1"'
        in current_summary
    )
    assert '"PRODUCTIVE_HOOK_CALLER_BINDING_PROVEN": true' in current_summary
    assert '"PRODUCTIVE_CALL_PATH_OFFLINE_PROOF": true' in current_summary
    assert '"STRUCTURAL_RUNTIME_BINDING_PROVEN": true' in current_summary
    assert '"CURRENT_RUNTIME_EXECUTION_AUTHORIZED": false' in current_summary
    assert '"AUTHORIZED_RUNTIME_SURFACE": "NONE"' in current_summary
    assert '"IMPLEMENTATION_AUTHORIZED": true' in current_summary
    assert '"ADMISSION_TRUE": false' in current_summary
    assert (EVIDENCE / "ENTRYPOINTS.json").is_file()
    assert (EVIDENCE / "CALLGRAPH.json").is_file()
    assert (EVIDENCE / "TIMELINE.json").is_file()
    assert (EVIDENCE / "SIDE_EFFECTS.json").is_file()
    assert (EVIDENCE / "GATES.json").is_file()
    assert (EVIDENCE / "INPUTS.json").is_file()
    assert (EVIDENCE / "ISOLATION.json").is_file()
    assert (EVIDENCE / "AUTHORIZATION_BOUNDARY.json").is_file()
    assert (EVIDENCE / "NON_EXECUTION.json").is_file()
    assert (EVIDENCE / "HOST_GRAPH.json").is_file()
    assert (EVIDENCE / "ADJUDICATION.json").is_file()
    assert (EVIDENCE / "SAFETY.json").is_file()
