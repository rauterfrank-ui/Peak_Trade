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
    CANONICAL_SECTION_HEADING,
    EARLIEST_UNRESOLVED_DEPENDENCY,
    EXPECTED_ORIGIN_MAIN_SHA,
    HISTORICAL_CODE_EXISTS_OWNER_GO,
    HISTORICAL_CODE_EXISTS_RUN_ID,
    HISTORICAL_CODE_EXISTS_SHA,
    HISTORICAL_OFFLINE_SURFACE_OWNER_GO,
    HISTORICAL_OFFLINE_SURFACE_RUN_ID,
    HISTORICAL_OFFLINE_SURFACE_SHA,
    HISTORICAL_PATH_REACHABLE_OWNER_GO,
    HISTORICAL_PATH_REACHABLE_RUN_ID,
    HISTORICAL_PATH_REACHABLE_SHA,
    HISTORICAL_PRIVATE_READ_ONLY_OWNER_GO,
    HISTORICAL_PRIVATE_READ_ONLY_RUN_ID,
    HISTORICAL_PRIVATE_READ_ONLY_SHA,
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
HEADING_11_15 = "## 11.15 Full-autonomy observability and audit trail"


def test_current_slice_constants_target_order_plan_observed() -> None:
    assert THIS_SLICE == "11.14.LIVE_ORDER_PLAN_OBSERVED_ADJUDICATION"
    assert PREDECESSOR_SLICE == "11.14.LIVE_PRIVATE_READ_ONLY_PROVEN_ADJUDICATION"
    assert OWNER_GO.endswith(
        "LIVE_ORDER_PLAN_OBSERVED_EXACT_LIVE_MUTATION_MAXIMUM_SAFE_LEVERAGE_V1"
    )
    assert EXPECTED_ORIGIN_MAIN_SHA == "eca62c687d7fb42d0fa11c645d5f70bb26916c55"
    assert EARLIEST_UNRESOLVED_DEPENDENCY == "LIVE_SUBMIT_ACK_OBSERVED"
    assert NEXT_OWNER_GO_REQUIRED == "OWNER_GO_FOR_EXACT_NEXT_MUTATION"
    assert LAST_CANONICALLY_CLOSED_STEP == "SECTION_11_14_LIVE_ORDER_PLAN_OBSERVED_ADJUDICATION"
    assert CANONICAL_EVIDENCE_RUN_ID
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
    end = text.find(HEADING_11_15, start)
    assert start >= 0
    assert end > start
    section = text[start:end]
    assert OWNER_GO in section
    assert "THIS_SLICE=11.14.LIVE_ORDER_PLAN_OBSERVED_ADJUDICATION" in section
    assert "PREDECESSOR_SLICE=11.14.LIVE_PRIVATE_READ_ONLY_PROVEN_ADJUDICATION" in section
    assert f"EXPECTED_ORIGIN_MAIN_SHA={EXPECTED_ORIGIN_MAIN_SHA}" in section
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
    assert "SECTION_11_14_LIVE_EXECUTION_CODE_EXISTS_ADJUDICATION_V1.md" in mot
    assert "SECTION_11_14_LIVE_EXECUTION_PATH_REACHABLE_ADJUDICATION_V1.md" in mot
    assert "SECTION_11_14_LIVE_PRIVATE_READ_ONLY_PROVEN_ADJUDICATION_V1.md" in mot
    assert "SECTION_11_14_LIVE_ORDER_PLAN_OBSERVED_ADJUDICATION_V1.md" in mot
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
    catalog = ATLAS_CATALOG.read_text(encoding="utf-8")
    authority = ATLAS_AUTHORITY.read_text(encoding="utf-8")
    relations = ATLAS_RUNTIME_RELATIONS.read_text(encoding="utf-8")
    assert "ATLAS_AUTHORITY=NONE" in authority
    assert "id: PHASE:section_11_14_live_execution_code_exists_adjudication" in catalog
    assert "id: PHASE:section_11_14_live_execution_path_reachable_adjudication" in catalog
    assert "id: PHASE:section_11_14_live_private_read_only_proven_adjudication" in catalog
    assert "id: PHASE:section_11_14_live_order_plan_observed_adjudication" in catalog
    assert (
        "id: RUNTIME_COMPONENT:section_11_14_live_order_and_economic_evidence_ladder_v1" in catalog
    )
    assert (
        "src/ops/section_11_13_5_live_canary_minimum_exposure_v1/submit_transport_v1.py" in catalog
    )
    assert "ATLAS_AUTHORITY=NONE" in catalog
    start = relations.find("id: REL:r_section_11_14_order_plan_observed_follows_private_read_only")
    assert start >= 0
    block = relations[start : start + 1400]
    assert (
        "source: RUNTIME_COMPONENT:section_11_14_live_order_and_economic_evidence_ladder_v1"
        in block
    )
    assert "ATLAS_AUTHORITY=NONE" in block
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
    assert EVIDENCE.is_dir()
    current_verified = verify_manifest_v1(EVIDENCE)
    assert int(current_verified.get("MANIFEST_VERIFY_RC", 1)) == 0
    current_summary = (EVIDENCE / "SUMMARY.json").read_text(encoding="utf-8")
    assert '"LIVE_EXECUTION_PATH_REACHABLE": true' in current_summary
    assert '"LIVE_PRIVATE_READ_ONLY_PROVEN": true' in current_summary
    assert '"LIVE_ORDER_PLAN_OBSERVED": true' in current_summary
    assert '"LIVE_SUBMIT_ACK_OBSERVED": false' in current_summary
    assert '"POST_USED": false' in current_summary
    assert (EVIDENCE / "ORDER_PLAN.sanitized.json").is_file()
    assert (EVIDENCE / "GATE_STATE.json").is_file()
    assert (EVIDENCE / "PREFLIGHT.json").is_file()
