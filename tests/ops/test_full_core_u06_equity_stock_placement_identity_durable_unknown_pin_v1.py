"""PATH_B durable-UNKNOWN U06 placement-identity pin tests.

No GET. No POST. No Hope-GET. DURABLE_UNKNOWN is not INCLUDE or EXCLUDE.
U06 remains REMAIN_UNKNOWN. Once-only semantics remain intact.
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
    CLASS_RESIDUAL,
    CLASS_U06,
    OUTCOME_EXCLUDE,
    OUTCOME_INCLUDE,
    PROOF_OBJECT_U06,
    TARGET_U06,
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
from src.ops.governed_productive_account_equity_authority_producer_v1.u06_equity_stock_placement_identity_durable_unknown_pin_v1 import (
    BLOCKER_ID,
    CANONICAL_PACK_RELPATH,
    EXPECTED_ORIGIN_MAIN_SHA,
    NEXT_ACTION,
    NEXT_OWNER_GO,
    NEXT_PRODUCTIVE_NODE,
    OWNER_GO,
    PARENT_BLOCKER_ID,
    SELECTED_PATH,
    U06EquityStockPlacementIdentityDurableUnknownPinError,
    execute_u06_equity_stock_placement_identity_durable_unknown_pin_v1,
    reject_durable_unknown_as_include_or_exclude_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.u06_paired_fee_event_and_once_only_equity_stock_effect_primary_proof_surface_binding_v1 import (
    reject_hope_get_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = (
    "src/ops/governed_productive_account_equity_authority_producer_v1/"
    "u06_equity_stock_placement_identity_durable_unknown_pin_v1.py"
)
SPEC_PATH = (
    REPO_ROOT
    / "docs/ops/specs/FULL_CORE_U06_EQUITY_STOCK_PLACEMENT_IDENTITY_DURABLE_UNKNOWN_PIN_V1.md"
)
MOT_PATH = REPO_ROOT / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md"
ATLAS_PATH = REPO_ROOT / "docs/system_atlas/entities/catalog.yaml"
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
CANONICAL_PACK = REPO_ROOT / CANONICAL_PACK_RELPATH
CG_HEADING = "11.2.1.CG FULL_CORE_U06_EQUITY_STOCK_PLACEMENT_IDENTITY_DURABLE_UNKNOWN_PIN"
FORBIDDEN_SOURCE_TOKENS = (
    "urllib",
    "requests",
    "httpx",
    "GET_ENDPOINTS_PRIVATE",
    "max_retries",
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
    with pytest.raises(
        U06EquityStockPlacementIdentityDurableUnknownPinError, match="OWNER_GO_MISMATCH"
    ):
        execute_u06_equity_stock_placement_identity_durable_unknown_pin_v1(
            owner_go="WRONG",
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            evidence_root=tmp_path / "pack",
        )


def test_wrong_origin_sha_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(
        U06EquityStockPlacementIdentityDurableUnknownPinError, match="ORIGIN_MAIN_SHA_MISMATCH"
    ):
        execute_u06_equity_stock_placement_identity_durable_unknown_pin_v1(
            owner_go=OWNER_GO,
            origin_main_sha="deadbeef",
            evidence_root=tmp_path / "pack",
        )


def test_path_a_is_not_this_slice(tmp_path: Path) -> None:
    with pytest.raises(
        U06EquityStockPlacementIdentityDurableUnknownPinError, match="SELECTED_PATH_NOT_PATH_B"
    ):
        execute_u06_equity_stock_placement_identity_durable_unknown_pin_v1(
            owner_go=OWNER_GO,
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            evidence_root=tmp_path / "pack",
            selected_path="PATH_A",
        )


def test_durable_unknown_is_not_include_or_exclude() -> None:
    reject_durable_unknown_as_include_or_exclude_v1(claimed="DURABLE_UNKNOWN")
    reject_durable_unknown_as_include_or_exclude_v1(claimed=DECISION_REMAIN_UNKNOWN)
    for claimed in (OUTCOME_EXCLUDE, OUTCOME_INCLUDE, "0", "zero", "NO_FEE", "absent"):
        with pytest.raises(
            U06EquityStockPlacementIdentityDurableUnknownPinError,
            match="DURABLE_UNKNOWN_IS_NOT_INCLUDE_OR_EXCLUDE",
        ):
            reject_durable_unknown_as_include_or_exclude_v1(claimed=claimed)


def test_hope_get_forbidden() -> None:
    reject_hope_get_v1(authorized_get_count="0", actual_get_count="0")
    with pytest.raises(
        Exception,
        match="HOPE_GET_FORBIDDEN",
    ):
        reject_hope_get_v1(authorized_get_count="1", actual_get_count="0")


def test_absent_u06_proof_is_nonqualifying_not_exclude() -> None:
    outcome = evaluate_u06_primary_proof_v1(proof={})
    assert outcome.outcome not in {OUTCOME_INCLUDE, OUTCOME_EXCLUDE}
    reject_durable_unknown_as_include_or_exclude_v1(claimed=outcome.outcome)


def test_execute_pins_durable_unknown_without_get(tmp_path: Path) -> None:
    store = tmp_path / "pack"
    result = execute_u06_equity_stock_placement_identity_durable_unknown_pin_v1(
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        evidence_root=store,
    )
    claims = json.loads((store / "claims.json").read_text(encoding="utf-8"))
    tree = json.loads((store / "downstream_dependency_tree_v1.json").read_text(encoding="utf-8"))
    halves = json.loads((store / "proof_halves_v1.json").read_text(encoding="utf-8"))
    once_only = json.loads((store / "once_only_semantics_v1.json").read_text(encoding="utf-8"))
    historical = json.loads(
        (store / "historical_fee_evidence_non_uplift_v1.json").read_text(encoding="utf-8")
    )
    assert result.selected_path == SELECTED_PATH
    assert result.target_unknown == TARGET_U06
    assert result.placement_identity_status == "DURABLE_UNKNOWN"
    assert result.u06_decision_after == DECISION_REMAIN_UNKNOWN
    assert result.further_u06_placement_acquisition == "STOPPED"
    assert result.placement_branch_closed == "true"
    assert result.authorized_get_count == "0"
    assert result.actual_get_count == "0"
    assert result.post_count == "0"
    assert claims["TARGET_UNKNOWN"] == TARGET_U06
    assert claims["U06_EVIDENCE_CLASS"] == CLASS_U06
    assert claims["EXPECTED_PRIMARY_PROOF_OBJECT"] == PROOF_OBJECT_U06
    assert claims["PLACEMENT_IDENTITY_STATUS"] == "DURABLE_UNKNOWN"
    assert claims["U06_DECISION_AFTER"] == DECISION_REMAIN_UNKNOWN
    assert claims["DURABLE_UNKNOWN_NOT_INCLUDE"] == "true"
    assert claims["DURABLE_UNKNOWN_NOT_EXCLUDE"] == "true"
    assert claims["NO_GET_REQUIRED"] == "true"
    assert claims["NO_EQ_SOURCE_AUTHORITY"] == "true"
    assert claims["NO_ALGEBRAIC_UPLIFT"] == "true"
    assert claims["NO_FEE_TOKEN_UPLIFT"] == "true"
    assert claims["NO_RETROACTIVE_SEALED_EVIDENCE_UPLIFT"] == "true"
    assert claims["NO_HOPE_GET"] == "true"
    assert claims["U06_ONCE_ONLY_SEMANTICS_INTACT"] == "true"
    assert claims["FUTURE_FEES_ARE_P01_NOT_U06"] == "true"
    assert claims["PARENT_BLOCKER_ID"] == PARENT_BLOCKER_ID
    assert claims["PARENT_CONCRETE_SURFACE_SELECTION_STATUS"] == "NONE_BINDABLE"
    assert claims["ACTUAL_GET_COUNT"] == "0"
    assert claims["POST_COUNT"] == "0"
    assert claims["PATH_C_CLOSEOUT"] == "false"
    assert claims["VENUE_EQ_SOURCE_AUTHORITY"] == "false"
    assert claims["NEXT_PRODUCTIVE_NODE"] == NEXT_PRODUCTIVE_NODE
    assert claims["NEXT_PRODUCTIVE_NODE"] == CLASS_RESIDUAL
    assert claims["NEXT_OWNER_GO_REQUIRED"] == NEXT_OWNER_GO
    assert claims["NEXT_ACTION"] == NEXT_ACTION
    assert "INCLUDE" not in claims["U06_DECISION_AFTER"]
    assert "EXCLUDE" not in claims["U06_DECISION_AFTER"]
    assert claims["PLACEMENT_IDENTITY_STATUS"] not in {OUTCOME_INCLUDE, OUTCOME_EXCLUDE}
    assert tree["next_productive_classification"] == "REQUIRES_NEW_AUTHORITY"
    assert halves["placement_xor"] == "IN_BASE_XOR_EVENT_SEPARATE"
    assert halves["pairing_requirement"] == (
        "fee_event_and_equity_stock_effect_from_same_economic_cause"
    )
    assert halves["semantic_normalization_forbidden"] == "true"
    assert once_only["u06_once_only_semantics_intact"] == "true"
    assert once_only["future_fees_are_p01_not_u06"] == "true"
    assert historical["package_1_bills_uplift_forbidden"] == "true"
    assert historical["g12_flatten_fills_uplift_forbidden"] == "true"
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
    assert claims["SELECTED_PATH"] == "PATH_B"
    assert claims["TARGET_UNKNOWN"] == TARGET_U06
    assert claims["PLACEMENT_IDENTITY_STATUS"] == "DURABLE_UNKNOWN"
    assert claims["U06_DECISION_AFTER"] == DECISION_REMAIN_UNKNOWN
    assert claims["FURTHER_U06_PLACEMENT_ACQUISITION"] == "STOPPED"
    assert claims["PLACEMENT_BRANCH_CLOSED"] == "true"
    assert claims["PATH_C_CLOSEOUT"] == "false"
    assert claims["ACTUAL_GET_COUNT"] == "0"
    assert claims["POST_COUNT"] == "0"
    assert claims["DURABLE_UNKNOWN_NOT_INCLUDE"] == "true"
    assert claims["DURABLE_UNKNOWN_NOT_EXCLUDE"] == "true"
    assert claims["NO_GET_REQUIRED"] == "true"
    assert claims["NO_HOPE_GET"] == "true"
    assert claims["U06_ONCE_ONLY_SEMANTICS_INTACT"] == "true"
    assert claims["BLOCKER_ID"] == BLOCKER_ID
    assert claims["PARENT_BLOCKER_ID"] == PARENT_BLOCKER_ID
    assert verify_manifest_sha256_v1(store_root=CANONICAL_PACK) == 0


def test_runbook_cg_persists_path_b() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    mot = MOT_PATH.read_text(encoding="utf-8")
    atlas = ATLAS_PATH.read_text(encoding="utf-8")
    runbook = RUNBOOK.read_text(encoding="utf-8")
    start = runbook.index(CG_HEADING)
    cg_section = runbook[start : runbook.index("## 11.3 Autonomy state model", start)]
    assert OWNER_GO in cg_section
    assert (
        "THIS_SLICE=11.2.1.CG.FULL_CORE_U06_EQUITY_STOCK_PLACEMENT_IDENTITY_DURABLE_UNKNOWN_PIN"
    ) in cg_section
    assert "SELECTED_PATH=PATH_B" in cg_section
    assert "TARGET_UNKNOWN=U06_FEE_AS_CLASSIFIED_EQUITY_STOCK_KIND" in cg_section
    assert "PLACEMENT_IDENTITY_STATUS=DURABLE_UNKNOWN" in cg_section
    assert "U06_DECISION_AFTER=REMAIN_UNKNOWN" in cg_section
    assert "DURABLE_UNKNOWN_NOT_INCLUDE=true" in cg_section
    assert "DURABLE_UNKNOWN_NOT_EXCLUDE=true" in cg_section
    assert "NO_GET_REQUIRED=true" in cg_section
    assert "NO_EQ_SOURCE_AUTHORITY=true" in cg_section
    assert "NO_ALGEBRAIC_UPLIFT=true" in cg_section
    assert "NO_FEE_TOKEN_UPLIFT=true" in cg_section
    assert "NO_RETROACTIVE_SEALED_EVIDENCE_UPLIFT=true" in cg_section
    assert "NO_HOPE_GET=true" in cg_section
    assert "U06_ONCE_ONLY_SEMANTICS_INTACT=true" in cg_section
    assert "FURTHER_U06_PLACEMENT_ACQUISITION=STOPPED" in cg_section
    assert "PLACEMENT_BRANCH_CLOSED=true" in cg_section
    assert "PATH_C_CLOSEOUT=false" in cg_section
    assert "ACTUAL_GET_COUNT=0" in cg_section
    assert "VENUE_EQ_SOURCE_AUTHORITY=false" in cg_section
    assert PARENT_BLOCKER_ID in cg_section
    assert BLOCKER_ID in cg_section
    assert NEXT_OWNER_GO in cg_section
    assert NEXT_PRODUCTIVE_NODE in cg_section
    assert "CURRENT_CANONICAL_SECTION=11.2.1.CG" in cg_section
    assert "DOCS_TOKEN_FULL_CORE_U06_EQUITY_STOCK_PLACEMENT_IDENTITY_DURABLE_UNKNOWN_PIN_V1" in spec
    assert "FULL_CORE_U06_EQUITY_STOCK_PLACEMENT_IDENTITY_DURABLE_UNKNOWN_PIN_V1.md" in mot
    assert CG_HEADING in mot
    assert "11.2.1.CG" in atlas
    assert "u06_equity_stock_placement_identity_durable_unknown_pin_v1.py" in atlas
    assert "ATLAS_AUTHORITY=NONE" in atlas
