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
    CANONICAL_SECTION_HEADING,
    EARLIEST_UNRESOLVED_DEPENDENCY,
    EXPECTED_ORIGIN_MAIN_SHA,
    HISTORICAL_FEE_OBSERVED_OWNER_GO,
    HISTORICAL_FEE_OBSERVED_RUN_ID,
    HISTORICAL_FEE_OBSERVED_SHA,
    HISTORICAL_FILL_OBSERVED_OWNER_GO,
    HISTORICAL_FILL_OBSERVED_RUN_ID,
    HISTORICAL_FILL_OBSERVED_SHA,
    HISTORICAL_FORENSIC_ACK_OWNER_GO,
    HISTORICAL_FORENSIC_ACK_RUN_ID,
    HISTORICAL_PROOF_CRITERION_OWNER_GO,
    HISTORICAL_PROOF_CRITERION_RUN_ID,
    HISTORICAL_PROOF_CRITERION_SHA,
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
HEADING_11_15 = "## 11.15 Full-autonomy observability and audit trail"


def test_current_slice_constants_target_position_reconciled_adjudication() -> None:
    assert THIS_SLICE == "11.14.LIVE_POSITION_RECONCILED_ADJUDICATION"
    assert PREDECESSOR_SLICE == "11.14.LIVE_FEE_OBSERVED_ADJUDICATION"
    assert OWNER_GO.endswith("LIVE_POSITION_RECONCILED_MAXIMUM_SAFE_LEVERAGE_V2")
    assert EXPECTED_ORIGIN_MAIN_SHA == "2d46611a4485a5422279e75fc762dd2285f7cc15"
    assert EARLIEST_UNRESOLVED_DEPENDENCY == "LIVE_ACCOUNTING_RECONSTRUCTED"
    assert NEXT_OWNER_GO_REQUIRED == "OWNER_GO_FOR_LIVE_ACCOUNTING_RECONSTRUCTED"
    assert LAST_CANONICALLY_CLOSED_STEP == "SECTION_11_14_LIVE_POSITION_RECONCILED"
    assert CANONICAL_EVIDENCE_RUN_ID == "20260904T181817Z"
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
    end = text.find(HEADING_11_15, start)
    assert start >= 0
    assert end > start
    section = text[start:end]
    assert OWNER_GO in section
    assert "THIS_SLICE=11.14.LIVE_POSITION_RECONCILED_ADJUDICATION" in section
    assert "PREDECESSOR_SLICE=11.14.LIVE_FEE_OBSERVED_ADJUDICATION" in section
    assert f"EXPECTED_ORIGIN_MAIN_SHA={EXPECTED_ORIGIN_MAIN_SHA}" in section
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
    assert NEXT_OWNER_GO_REQUIRED == "OWNER_GO_FOR_LIVE_ACCOUNTING_RECONSTRUCTED"
    assert NEXT_OWNER_GO_REQUIRED in section
    assert CANONICAL_EVIDENCE_RUN_ID in section
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
    assert EVIDENCE.is_dir()
    current_verified = verify_manifest_v1(EVIDENCE)
    assert int(current_verified.get("MANIFEST_VERIFY_RC", 1)) == 0
    current_summary = (EVIDENCE / "SUMMARY.json").read_text(encoding="utf-8")
    assert '"LIVE_FEE_OBSERVED": true' in current_summary
    assert '"LIVE_POSITION_RECONCILED": true' in current_summary
    assert '"LIVE_ACCOUNTING_RECONSTRUCTED": false' in current_summary
    assert '"POST_USED": false' in current_summary
    assert '"GET_PERFORMED": true' in current_summary
    assert (
        '"CASE_ADJUDICATION": "CASE_LIVE_POSITION_RECONCILED_ACCOUNTING_INELIGIBLE"'
        in current_summary
    )
    assert (EVIDENCE / "POSITION_RECONCILED_ADJUDICATION.json").is_file()
    assert (EVIDENCE / "GET_POSITIONS.raw.json").is_file()
