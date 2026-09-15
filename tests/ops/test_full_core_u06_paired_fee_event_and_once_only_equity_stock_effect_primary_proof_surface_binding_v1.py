"""U06 NONE_BINDABLE primary-proof surface-binding persist tests.

No GET. No POST. No Hope-GET. NONE_BINDABLE is not EXCLUDE.
U06 remains REMAIN_UNKNOWN. Placement pin is not this slice.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    LIVE_ARMED,
    LIVE_ENABLED,
    MS2_AUTHORIZED,
    WIRE_SEND_PERMITTED,
)
from src.ops.full_core_live_path_composition_root_v1.live_admission_gap_dag_v1 import (
    EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.bj_future_admissible_evidence_and_include_exclude_qualification_law_v1 import (
    CLASS_U06,
    OUTCOME_EXCLUDE,
    OUTCOME_INCLUDE,
    PROOF_OBJECT_U06,
    evaluate_u06_primary_proof_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    RAW_EQ_SOURCE_AUTHORITY,
    U06_KIND_DECISION,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.named_remaining_unknown_kind_set_evidence_persist_contract_v1 import (
    DECISION_REMAIN_UNKNOWN,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_s6_mapping_classification_v1 import (
    verify_manifest_sha256_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.u06_paired_fee_event_and_once_only_equity_stock_effect_primary_proof_surface_binding_v1 import (
    BLOCKER_ID,
    CANONICAL_PACK_RELPATH,
    EXPECTED_ORIGIN_MAIN_SHA,
    NEXT_ACTION,
    NEXT_OWNER_GO,
    NEXT_PRODUCTIVE_NODE,
    OWNER_GO,
    SELECTION_STATUS,
    U06PrimaryProofSurfaceBindingError,
    execute_u06_paired_fee_event_and_once_only_equity_stock_effect_primary_proof_surface_binding_v1,
    reject_hope_get_v1,
    reject_none_bindable_as_exclude_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = (
    "src/ops/governed_productive_account_equity_authority_producer_v1/"
    "u06_paired_fee_event_and_once_only_equity_stock_effect_primary_proof_surface_binding_v1.py"
)
SPEC_PATH = (
    REPO_ROOT
    / "docs/ops/specs/FULL_CORE_U06_PAIRED_FEE_EVENT_AND_ONCE_ONLY_EQUITY_STOCK_EFFECT_PRIMARY_PROOF_SURFACE_BINDING_V1.md"
)
MOT_PATH = REPO_ROOT / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md"
ATLAS_PATH = REPO_ROOT / "docs/system_atlas/entities/catalog.yaml"
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
CANONICAL_PACK = REPO_ROOT / CANONICAL_PACK_RELPATH
CF_HEADING = (
    "11.2.1.CF FULL_CORE_U06_PAIRED_FEE_EVENT_AND_ONCE_ONLY_EQUITY_STOCK_"
    "EFFECT_PRIMARY_PROOF_SURFACE_BINDING"
)
FORBIDDEN_SOURCE_TOKENS = (
    "urllib",
    "requests",
    "httpx",
    "GET_ENDPOINTS_PRIVATE",
    "max_retries",
    "secretref://",
    "ok-access",
    "api_secret",
    "eq=cashBal",
)


def test_standing_pins_remain_fail_closed() -> None:
    assert LIVE_ENABLED is True
    assert LIVE_ARMED is True
    assert WIRE_SEND_PERMITTED is True
    assert MS2_AUTHORIZED is False
    assert RAW_EQ_SOURCE_AUTHORITY is False
    assert U06_KIND_DECISION == DECISION_REMAIN_UNKNOWN
    assert EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY == (
        "NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING"
    )


def test_wrong_owner_go_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(U06PrimaryProofSurfaceBindingError, match="OWNER_GO_MISMATCH"):
        execute_u06_paired_fee_event_and_once_only_equity_stock_effect_primary_proof_surface_binding_v1(
            owner_go="WRONG",
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            evidence_root=tmp_path / "pack",
        )


def test_wrong_origin_sha_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(U06PrimaryProofSurfaceBindingError, match="ORIGIN_MAIN_SHA_MISMATCH"):
        execute_u06_paired_fee_event_and_once_only_equity_stock_effect_primary_proof_surface_binding_v1(
            owner_go=OWNER_GO,
            origin_main_sha="deadbeef",
            evidence_root=tmp_path / "pack",
        )


def test_none_bindable_is_not_exclude_or_include() -> None:
    reject_none_bindable_as_exclude_v1(claimed=SELECTION_STATUS)
    reject_none_bindable_as_exclude_v1(claimed=DECISION_REMAIN_UNKNOWN)
    for claimed in (OUTCOME_EXCLUDE, OUTCOME_INCLUDE, "0", "zero", "NO_FEE", "absent"):
        with pytest.raises(
            U06PrimaryProofSurfaceBindingError,
            match="NONE_BINDABLE_IS_NOT_EXCLUDE_OR_INCLUDE",
        ):
            reject_none_bindable_as_exclude_v1(claimed=claimed)


def test_hope_get_forbidden() -> None:
    reject_hope_get_v1(authorized_get_count="0", actual_get_count="0")
    with pytest.raises(U06PrimaryProofSurfaceBindingError, match="HOPE_GET_FORBIDDEN"):
        reject_hope_get_v1(authorized_get_count="1", actual_get_count="0")
    with pytest.raises(U06PrimaryProofSurfaceBindingError, match="HOPE_GET_FORBIDDEN"):
        reject_hope_get_v1(authorized_get_count="0", actual_get_count="1")


def test_absent_u06_proof_is_nonqualifying_not_exclude() -> None:
    outcome = evaluate_u06_primary_proof_v1(proof={})
    assert outcome.outcome not in {OUTCOME_INCLUDE, OUTCOME_EXCLUDE}
    reject_none_bindable_as_exclude_v1(claimed=outcome.outcome)


def test_execute_persists_none_bindable_without_get(tmp_path: Path) -> None:
    store = tmp_path / "pack"
    result = execute_u06_paired_fee_event_and_once_only_equity_stock_effect_primary_proof_surface_binding_v1(
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        evidence_root=store,
    )
    claims = json.loads((store / "claims.json").read_text(encoding="utf-8"))
    census = json.loads(
        (store / "candidate_surface_capability_adjudication_v1.json").read_text(encoding="utf-8")
    )
    halves = json.loads((store / "proof_halves_v1.json").read_text(encoding="utf-8"))
    guard = json.loads(
        (store / "none_bindable_not_exclude_guard_v1.json").read_text(encoding="utf-8")
    )
    historical = json.loads(
        (store / "historical_fee_evidence_non_uplift_v1.json").read_text(encoding="utf-8")
    )
    assert result.concrete_surface_selection_status == SELECTION_STATUS
    assert result.authorized_get_count == "0"
    assert result.actual_get_count == "0"
    assert result.post_count == "0"
    assert result.u06_decision_after == DECISION_REMAIN_UNKNOWN
    assert result.blocker_id == BLOCKER_ID
    assert claims["OWNER_GO"] == OWNER_GO
    assert claims["U06_EVIDENCE_CLASS"] == CLASS_U06
    assert claims["EXPECTED_PRIMARY_PROOF_OBJECT"] == PROOF_OBJECT_U06
    assert claims["CONCRETE_SURFACE_SELECTION_STATUS"] == "NONE_BINDABLE"
    assert claims["MAX_GET_COUNT"] == "0"
    assert claims["AUTHORIZED_GET_COUNT"] == "0"
    assert claims["ACTUAL_GET_COUNT"] == "0"
    assert claims["POST_COUNT"] == "0"
    assert claims["RETRY_ALLOWED"] == "false"
    assert claims["HOPE_GET_FORBIDDEN"] == "true"
    assert claims["PRODUCTIVE_ACQUISITION_AUTHORIZED"] == "false"
    assert claims["PRODUCTIVE_ACQUISITION_EXECUTED"] == "false"
    assert claims["GET_ALONE_MAY_INCLUDE"] == "false"
    assert claims["GET_ALONE_MAY_EXCLUDE"] == "false"
    assert claims["VENUE_EQ_SOURCE_AUTHORITY"] == "false"
    assert claims["ACCOUNT_BILLS_CANONICALIZED"] == "false"
    assert claims["U06_DECISION_AFTER"] == DECISION_REMAIN_UNKNOWN
    assert claims["NONE_BINDABLE_IS_NOT_EXCLUDE"] == "true"
    assert claims["PLACEMENT_PIN_IMPLEMENTED_THIS_SLICE"] == "false"
    assert claims["PATH_C_CLOSEOUT"] == "false"
    assert claims["SECRET_RESOLUTION_STATUS"] == "NOT_ATTEMPTED"
    assert claims["NEXT_PRODUCTIVE_NODE"] == NEXT_PRODUCTIVE_NODE
    assert claims["NEXT_OWNER_GO_REQUIRED"] == NEXT_OWNER_GO
    assert claims["NEXT_ACTION"] == NEXT_ACTION
    assert "EXCLUDE" not in claims["U06_DECISION_AFTER"]
    assert "INCLUDE" not in claims["U06_DECISION_AFTER"]
    assert census["selection_status"] == "NONE_BINDABLE"
    assert census["hope_get_forbidden"] == "true"
    assert census["second_get_required"] == "false"
    assert all(item["bindable"] == "false" for item in census["records"])
    assert halves["primary_proof_object"] == PROOF_OBJECT_U06
    assert halves["placement_xor"] == "IN_BASE_XOR_EVENT_SEPARATE"
    assert halves["semantic_normalization_forbidden"] == "true"
    assert guard["none_bindable_is_not_exclude"] == "true"
    assert historical["package_1_bills_uplift_forbidden"] == "true"
    assert historical["section_11_14_live_fee_observed_is_not_d6_u06_authority"] == "true"
    assert verify_manifest_sha256_v1(store_root=store) == 0


def test_source_does_not_get_or_post_or_uplift() -> None:
    source = (REPO_ROOT / SOURCE_PATH).read_text(encoding="utf-8")
    for token in FORBIDDEN_SOURCE_TOKENS:
        assert token not in source
    assert "cashBal+upl" not in source
    assert "PRODUCTIVE_ACQUISITION_AUTHORIZED = TRUE" not in source.upper()


def test_canonical_pack_sealed() -> None:
    claims = json.loads((CANONICAL_PACK / "claims.json").read_text(encoding="utf-8"))
    assert claims["OWNER_GO"] == OWNER_GO
    assert claims["CONCRETE_SURFACE_SELECTION_STATUS"] == "NONE_BINDABLE"
    assert claims["AUTHORIZED_GET_COUNT"] == "0"
    assert claims["ACTUAL_GET_COUNT"] == "0"
    assert claims["POST_COUNT"] == "0"
    assert claims["U06_DECISION_AFTER"] == DECISION_REMAIN_UNKNOWN
    assert claims["BLOCKER_ID"] == BLOCKER_ID
    assert claims["NONE_BINDABLE_IS_NOT_EXCLUDE"] == "true"
    assert claims["HOPE_GET_FORBIDDEN"] == "true"
    assert claims["PRODUCTIVE_ACQUISITION_AUTHORIZED"] == "false"
    assert claims["PLACEMENT_PIN_IMPLEMENTED_THIS_SLICE"] == "false"
    assert claims["NEXT_PRODUCTIVE_NODE"] == NEXT_PRODUCTIVE_NODE
    assert verify_manifest_sha256_v1(store_root=CANONICAL_PACK) == 0


def test_runbook_cf_persists_none_bindable() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    mot = MOT_PATH.read_text(encoding="utf-8")
    atlas = ATLAS_PATH.read_text(encoding="utf-8")
    runbook = RUNBOOK.read_text(encoding="utf-8")
    start = runbook.index(CF_HEADING)
    cf_section = runbook[start : runbook.index("## 11.3 Autonomy state model", start)]
    assert OWNER_GO in cf_section
    assert (
        "THIS_SLICE=11.2.1.CF.FULL_CORE_U06_PAIRED_FEE_EVENT_AND_ONCE_ONLY_"
        "EQUITY_STOCK_EFFECT_PRIMARY_PROOF_SURFACE_BINDING"
    ) in cf_section
    assert "CONCRETE_SURFACE_SELECTION_STATUS=NONE_BINDABLE" in cf_section
    assert "AUTHORIZED_GET_COUNT=0" in cf_section
    assert "ACTUAL_GET_COUNT=0" in cf_section
    assert "MAX_GET_COUNT=0" in cf_section
    assert "RETRY_ALLOWED=false" in cf_section
    assert "HOPE_GET_FORBIDDEN=true" in cf_section
    assert "U06_DECISION_AFTER=REMAIN_UNKNOWN" in cf_section
    assert "NONE_BINDABLE_IS_NOT_EXCLUDE=true" in cf_section
    assert "PRODUCTIVE_ACQUISITION_AUTHORIZED=false" in cf_section
    assert "GET_ALONE_MAY_INCLUDE=false" in cf_section
    assert "GET_ALONE_MAY_EXCLUDE=false" in cf_section
    assert "VENUE_EQ_SOURCE_AUTHORITY=false" in cf_section
    assert "ACCOUNT_BILLS_CANONICALIZED=false" in cf_section
    assert "PLACEMENT_PIN_IMPLEMENTED_THIS_SLICE=false" in cf_section
    assert BLOCKER_ID in cf_section
    assert NEXT_OWNER_GO in cf_section
    assert NEXT_PRODUCTIVE_NODE in cf_section
    assert "CURRENT_CANONICAL_SECTION=11.2.1.CF" in cf_section
    assert (
        "DOCS_TOKEN_FULL_CORE_U06_PAIRED_FEE_EVENT_AND_ONCE_ONLY_EQUITY_STOCK_EFFECT_PRIMARY_PROOF_SURFACE_BINDING_V1"
        in spec
    )
    assert (
        "FULL_CORE_U06_PAIRED_FEE_EVENT_AND_ONCE_ONLY_EQUITY_STOCK_EFFECT_"
        "PRIMARY_PROOF_SURFACE_BINDING_V1.md"
    ) in mot
    assert CF_HEADING in mot
    assert "11.2.1.CF" in atlas
    assert (
        "u06_paired_fee_event_and_once_only_equity_stock_effect_primary_proof_surface_binding_v1.py"
    ) in atlas
    assert "ATLAS_AUTHORITY=NONE" in atlas
