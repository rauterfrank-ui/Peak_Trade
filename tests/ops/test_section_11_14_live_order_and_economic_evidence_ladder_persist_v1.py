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
HEADING_11_15 = "## 11.15 Full-autonomy observability and audit trail"


def test_current_slice_constants_target_pos_producer_semantics_and_contract() -> None:
    assert THIS_SLICE == "11.14.LIVE_HANDOFF_POS_PRODUCER_SEMANTICS_AND_CONTRACT"
    assert PREDECESSOR_SLICE == "11.14.LIVE_HANDOFF_POS_SEMANTICS_CANONICAL_BINDING"
    assert OWNER_GO.endswith("POS_PRODUCER_SEMANTICS_AND_CONTRACT_V1")
    assert EXPECTED_ORIGIN_MAIN_SHA == "bbba739dd34af4d0d10c12e137ab9e195430592a"
    assert EARLIEST_UNRESOLVED_DEPENDENCY == "LIVE_RESTART_RECONSTRUCTED"
    assert NEXT_OWNER_GO_REQUIRED == "OWNER_GO_FOR_LIVE_RESTART_RECONSTRUCTED"
    assert LAST_CANONICALLY_CLOSED_STEP == (
        "SECTION_11_14_LIVE_HANDOFF_POS_PRODUCER_SEMANTICS_AND_CONTRACT"
    )
    assert CANONICAL_EVIDENCE_RUN_ID == "20260906T224500Z"
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
    end = text.find(HEADING_11_15, start)
    assert start >= 0
    assert end > start
    section = text[start:end]
    assert OWNER_GO in section
    assert "THIS_SLICE=11.14.LIVE_HANDOFF_POS_PRODUCER_SEMANTICS_AND_CONTRACT" in section
    assert "PREDECESSOR_SLICE=11.14.LIVE_HANDOFF_POS_SEMANTICS_CANONICAL_BINDING" in section
    assert f"EXPECTED_ORIGIN_MAIN_SHA={EXPECTED_ORIGIN_MAIN_SHA}" in section
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
    assert CANONICAL_EVIDENCE_RUN_ID in section
    assert (
        "PROPOSED_NEXT_SLICE=SECTION_11_14_LIVE_HANDOFF_COMPLETE_CAPTURE_SEAM_PROOF_V1" in section
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
    assert '"SECTION_11_14_LIVE_HANDOFF_OWNER_CURRENT": "NONE"' in current_summary
    assert '"POS_SEMANTICS": "PROVEN"' in current_summary
    assert '"POS_SEMANTICS_CANONICALLY_BOUND": true' in current_summary
    assert '"NEW_PRODUCER_CONTRACT_DEFINED": true' in current_summary
    assert '"NEW_PRODUCER_IMPLEMENTED": false' in current_summary
    assert '"COMPLETE_CAPTURE_SEAM": "UNPROVEN"' in current_summary
    assert '"COMPLETE_CAPTURE_SEAM_CAN_NOW_BE_ADJUDICATED": true' in current_summary
    assert '"IMPLEMENTATION_AUTHORIZED": false' in current_summary
    assert '"ADMISSION_TRUE": false' in current_summary
    assert '"FIRST_OWNER_PRODUCTIVELY_BOUND": false' in current_summary
    assert (EVIDENCE / "POS_PRODUCER_SEMANTICS_AND_CONTRACT.json").is_file()
    assert (EVIDENCE / "POS_MEANING_CANDIDATE_MATRIX.json").is_file()
    assert (EVIDENCE / "POS_WHAT_RESTART_RECONSTRUCTS.json").is_file()
    assert (EVIDENCE / "POS_UNIT_PROOF.json").is_file()
    assert (EVIDENCE / "POS_SIGN_PROOF.json").is_file()
    assert (EVIDENCE / "POS_ACCOUNT_MODE_PROOF.json").is_file()
    assert (EVIDENCE / "POS_PRODUCER_CONTRACT.json").is_file()
    assert (EVIDENCE / "HANDOFF_SCHEMA_VERSION.json").is_file()
    assert (EVIDENCE / "POS_DOWNSTREAM_EFFECT.json").is_file()
    assert (EVIDENCE / "RESTART_RECONSTRUCTED_ADJUDICATION.json").is_file()
