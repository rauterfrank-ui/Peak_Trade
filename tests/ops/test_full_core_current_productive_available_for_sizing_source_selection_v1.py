"""Current-productive AVAILABLE_FOR_SIZING source selection tests.

Today's STEP-29P consumer needs USDC RUNNING_ACCOUNT_EQUITY_AVAILABLE_FOR_SIZING.
Venue eq remains reconciliation-target. Forbidden venue fields are not bound.
max-size remains contracts, not USDC equity. U04 remains reduction, not source.
Legacy KIND_SET remains sealed. Unclassified fields are not bound by
plausibility. No GET. No POST. No source mint.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    LIVE_ARMED,
    LIVE_ENABLED,
    MAPPING_PROVEN,
    WIRE_SEND_PERMITTED,
)
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    FRESHNESS_POLICY,
)
from src.ops.full_core_live_path_composition_root_v1.live_admission_gap_dag_v1 import (
    EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY,
)
from src.ops.full_core_live_path_composition_root_v1.step_29p_capital_risk_admissibility_v1 import (
    RISK_EQUITY_DIMENSION,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.classified_event_kind_set_and_source_seam_contract_v1 import (
    DISPOSITION_NOT_EQUITY_STOCK,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING,
    CURRENT_PRODUCTIVE_29P_CONSUMER_BINDING_STATUS,
    CURRENT_PRODUCTIVE_ACCOUNT_EQUITY_MODEL_VERSION,
    CURRENT_PRODUCTIVE_ARCHITECTURE_RATIFIED,
    CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_DIMENSION,
    CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_SOURCE_SELECTION_RATIFIED,
    CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_SOURCE_SELECTION_STATUS,
    CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_SOURCE_STATUS,
    CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_TRANSFORMATION,
    CURRENT_PRODUCTIVE_FRESH_GET_EXECUTED,
    CURRENT_PRODUCTIVE_FRESH_GET_NOT_REQUIRED_FOR_BINDING_DECISION,
    CURRENT_PRODUCTIVE_LIVE_CRITICAL_DEPENDENCY,
    CURRENT_PRODUCTIVE_PRODUCER_MINT_AUTHORIZED,
    CURRENT_PRODUCTIVE_RECONCILIATION_TARGET_ROLE,
    CURRENT_PRODUCTIVE_RESTART_RECONSTRUCTION_STATUS,
    CURRENT_PRODUCTIVE_SELECTED_AVAILABLE_FOR_SIZING_SOURCE,
    CURRENT_PRODUCTIVE_SOURCE_SELECTED,
    CURRENT_PRODUCTIVE_U04_APPLICATION_STATUS,
    EQ_TREATED_AS_SOURCE_THIS_WORKPACKAGE,
    GOVERNED_PRODUCER_CREATED,
    KIND_SET_RESOLVED,
    KIND_SET_UPLIFT_THIS_WORKPACKAGE,
    LEGACY_RECONSTRUCTION_REQUIRED_FOR_LIVE,
    PRODUCTIVE_U04_AVAILABLE_CAPITAL_ROLE,
    PRODUCTIVE_U04_EQUITY_STOCK_ROLE,
    RAW_EQ_SOURCE_AUTHORITY,
    SEALED_LEGACY_CENSUS_REOPENED,
    SOURCE_SELECTED,
    U04_LEGACY_STATUS,
    U05_KIND_DECISION,
    U06_KIND_DECISION,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_account_equity_source_architecture_v1 import (
    FORBIDDEN_AUTHORITY_FIELDS,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_available_for_sizing_source_selection_v1 import (
    BLOCKER_ID,
    CANONICAL_PACK_RELPATH,
    EXACT_MISSING_PREDICATE,
    EXPECTED_ORIGIN_MAIN_SHA,
    FRESH_GET_NOT_REQUIRED_JUSTIFIED,
    NEXT_ACTION,
    NEXT_OWNER_GO,
    NEXT_PRODUCTIVE_NODE,
    OWNER_GO,
    PARENT_BLOCKER_ID,
    PIN_OWNER_GO,
    PIN_OWNER_GO_STATUS,
    SELECTED_SOURCE,
    CurrentProductiveAvailableForSizingSourceSelectionError,
    classify_current_productive_source_candidates_v1,
    classify_source_selection_verdict_v1,
    classify_step_29p_required_semantics_v1,
    execute_current_productive_available_for_sizing_source_selection_v1,
    reject_empty_producer_slot_as_source_v1,
    reject_forbidden_venue_field_as_source_v1,
    reject_max_size_contracts_as_usdc_equity_source_v1,
    reject_u04_as_sizing_source_v1,
    reject_unclassified_field_plausibility_bind_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.named_remaining_unknown_kind_set_evidence_persist_contract_v1 import (
    DECISION_REMAIN_UNKNOWN,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_s6_mapping_classification_v1 import (
    verify_manifest_sha256_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.u04_pending_order_reservation_or_account_equity_mapping_v1 import (
    reject_eq_as_source_authority_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = (
    "src/ops/governed_productive_account_equity_authority_producer_v1/"
    "current_productive_available_for_sizing_source_selection_v1.py"
)
SPEC_PATH = (
    REPO_ROOT
    / "docs/ops/specs/"
    / "FULL_CORE_CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_SOURCE_SELECTION_V1.md"
)
MOT_PATH = REPO_ROOT / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md"
ATLAS_PATH = REPO_ROOT / "docs/system_atlas/entities/catalog.yaml"
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
CANONICAL_PACK = REPO_ROOT / CANONICAL_PACK_RELPATH
CS_HEADING = "11.2.1.CS FULL_CORE_CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_SOURCE_SELECTION"
FORBIDDEN_SOURCE_TOKENS = (
    "urllib",
    "requests",
    "httpx",
    "GET_ENDPOINTS_PRIVATE",
    "max_retries",
    "eq=cashBal",
)


def _execute(tmp_path: Path) -> object:
    return execute_current_productive_available_for_sizing_source_selection_v1(
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        evidence_root=tmp_path / "pack",
        repo_root=REPO_ROOT,
    )


def test_standing_pins_remain_fail_closed() -> None:
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert WIRE_SEND_PERMITTED is False
    assert RAW_EQ_SOURCE_AUTHORITY is False
    assert EQ_TREATED_AS_SOURCE_THIS_WORKPACKAGE is False
    assert CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING is False
    assert MAPPING_PROVEN is False
    assert KIND_SET_RESOLVED is False
    assert KIND_SET_UPLIFT_THIS_WORKPACKAGE is False
    assert SOURCE_SELECTED is False
    assert GOVERNED_PRODUCER_CREATED is False
    assert CURRENT_PRODUCTIVE_ARCHITECTURE_RATIFIED is True
    assert LEGACY_RECONSTRUCTION_REQUIRED_FOR_LIVE is False
    assert SEALED_LEGACY_CENSUS_REOPENED is False
    assert CURRENT_PRODUCTIVE_SOURCE_SELECTED is False
    assert CURRENT_PRODUCTIVE_PRODUCER_MINT_AUTHORIZED is False
    assert CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_DIMENSION == RISK_EQUITY_DIMENSION
    assert CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_SOURCE_STATUS == "UNBOUND"
    assert CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_SOURCE_SELECTION_RATIFIED is True
    assert CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_SOURCE_SELECTION_STATUS == (
        "NO_SEMANTICALLY_ADMISSIBLE_CANDIDATE"
    )
    assert CURRENT_PRODUCTIVE_SELECTED_AVAILABLE_FOR_SIZING_SOURCE == "NONE"
    assert CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_TRANSFORMATION == "NONE_NO_SOURCE"
    assert CURRENT_PRODUCTIVE_U04_APPLICATION_STATUS == "REDUCTION_ONLY_NOT_SOURCE_NOT_APPLIED"
    assert CURRENT_PRODUCTIVE_FRESH_GET_EXECUTED is False
    assert CURRENT_PRODUCTIVE_FRESH_GET_NOT_REQUIRED_FOR_BINDING_DECISION is True
    assert CURRENT_PRODUCTIVE_RECONCILIATION_TARGET_ROLE == "EQ_RECONCILIATION_TARGET_ONLY"
    assert CURRENT_PRODUCTIVE_LIVE_CRITICAL_DEPENDENCY == (
        "CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_SOURCE_UNBOUND"
    )
    assert CURRENT_PRODUCTIVE_RESTART_RECONSTRUCTION_STATUS == (
        "FAIL_CLOSED_UNTIL_CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_SOURCE_BOUND"
    )
    assert CURRENT_PRODUCTIVE_29P_CONSUMER_BINDING_STATUS == "BOUND_AVAILABLE_FOR_SIZING_ONLY"
    assert U04_LEGACY_STATUS == "UNRESOLVED"
    assert PRODUCTIVE_U04_EQUITY_STOCK_ROLE == DISPOSITION_NOT_EQUITY_STOCK
    assert PRODUCTIVE_U04_AVAILABLE_CAPITAL_ROLE == "AVAILABLE_FOR_SIZING_OR_RISK_SIZING"
    assert U05_KIND_DECISION == DECISION_REMAIN_UNKNOWN
    assert U06_KIND_DECISION == DECISION_REMAIN_UNKNOWN
    assert EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY == (
        "NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING"
    )


def test_wrong_owner_go_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(
        CurrentProductiveAvailableForSizingSourceSelectionError, match="OWNER_GO_MISMATCH"
    ):
        execute_current_productive_available_for_sizing_source_selection_v1(
            owner_go="WRONG",
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            evidence_root=tmp_path / "pack",
        )


def test_wrong_origin_sha_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(
        CurrentProductiveAvailableForSizingSourceSelectionError,
        match="ORIGIN_MAIN_SHA_MISMATCH",
    ):
        execute_current_productive_available_for_sizing_source_selection_v1(
            owner_go=OWNER_GO,
            origin_main_sha="deadbeef",
            evidence_root=tmp_path / "pack",
        )


def test_eq_and_forbidden_fields_and_u04_and_max_size_are_not_sources() -> None:
    reject_eq_as_source_authority_v1(claimed="false")
    reject_u04_as_sizing_source_v1(claimed="false")
    reject_max_size_contracts_as_usdc_equity_source_v1(claimed="false")
    reject_unclassified_field_plausibility_bind_v1(claimed="false")
    reject_empty_producer_slot_as_source_v1(claimed="false")
    for field in FORBIDDEN_AUTHORITY_FIELDS:
        with pytest.raises(
            CurrentProductiveAvailableForSizingSourceSelectionError,
            match="FORBIDDEN_VENUE_FIELD_NOT_AVAILABLE_FOR_SIZING_SOURCE",
        ):
            reject_forbidden_venue_field_as_source_v1(claimed=field)
    with pytest.raises(
        CurrentProductiveAvailableForSizingSourceSelectionError,
        match="U04_IS_REDUCTION_NOT_AVAILABLE_FOR_SIZING_SOURCE",
    ):
        reject_u04_as_sizing_source_v1(claimed="SOURCE")
    with pytest.raises(
        CurrentProductiveAvailableForSizingSourceSelectionError,
        match="MAX_SIZE_CONTRACTS_ARE_NOT_USDC_AVAILABLE_FOR_SIZING",
    ):
        reject_max_size_contracts_as_usdc_equity_source_v1(claimed="maxBuy")
    with pytest.raises(
        CurrentProductiveAvailableForSizingSourceSelectionError,
        match="UNCLASSIFIED_VENUE_FIELD_NOT_BOUND_BY_PLAUSIBILITY",
    ):
        reject_unclassified_field_plausibility_bind_v1(claimed="PLAUSIBLE")


def test_consumer_semantics_and_candidates_reject_all() -> None:
    semantics = classify_step_29p_required_semantics_v1()
    assert semantics["required_dimension"] == RISK_EQUITY_DIMENSION
    assert semantics["required_settlement_currency"] == "USDC"
    assert semantics["eq_is_not_source"] == "true"
    assert semantics["u04_is_not_source"] == "true"
    assert semantics["freshness_policy"] == FRESHNESS_POLICY
    candidates = classify_current_productive_source_candidates_v1()
    assert len(candidates) == 11
    assert all(item["selected"] == "false" for item in candidates)
    assert {item["candidate_id"] for item in candidates} >= {
        "CP_S01_VENUE_EQ",
        "CP_S02_FORBIDDEN_AVAILEQ",
        "CP_S04_MAX_SIZE_CONTRACTS",
        "CP_S05_U04_RESERVATION_REDUCTION",
        "CP_S09_LEGACY_KIND_SET",
        "CP_S11_UNCLASSIFIED_VENUE_FIELDS",
    }
    verdict = classify_source_selection_verdict_v1()
    assert verdict["acceptable_candidate_count"] == "0"
    assert verdict["selected_source"] == SELECTED_SOURCE
    assert verdict["fresh_get_executed"] == "false"
    assert verdict["fresh_get_not_required_justified"] == FRESH_GET_NOT_REQUIRED_JUSTIFIED


def test_execute_selects_no_source(tmp_path: Path) -> None:
    result = _execute(tmp_path)
    claims = json.loads((tmp_path / "pack" / "claims.json").read_text(encoding="utf-8"))
    candidates = json.loads(
        (tmp_path / "pack" / "source_candidates_v1.json").read_text(encoding="utf-8")
    )
    assert result.selection_ratified == "true"
    assert result.selected_source == "NONE"
    assert result.selection_status == "NO_SEMANTICALLY_ADMISSIBLE_CANDIDATE"
    assert result.available_for_sizing_source_status == "UNBOUND"
    assert result.acceptable_candidate_count == "0"
    assert result.fresh_get_executed == "false"
    assert result.current_live_critical_blocker == BLOCKER_ID
    assert claims["SOURCE_SELECTED"] == "false"
    assert claims["SELECTED_SOURCE"] == "NONE"
    assert claims["AUTHORITY_UPLIFT"] == "false"
    assert claims["EQ_TREATED_AS_SOURCE_THIS_WORKPACKAGE"] == "false"
    assert claims["U04_APPLICATION"] == "REDUCTION_ONLY_NOT_SOURCE_NOT_APPLIED"
    assert claims["SEALED_LEGACY_CENSUS_REOPENED"] == "false"
    assert claims["KIND_SET"] == "EMPTY_FAIL_CLOSED"
    assert claims["STEP_29P_RISK_ADMISSIBLE"] == "false"
    assert claims["ACTUAL_GET_COUNT"] == "0"
    assert claims["POST_COUNT"] == "0"
    assert claims["PIN_OWNER_GO_STATUS"] == PIN_OWNER_GO_STATUS
    assert candidates["acceptable_count"] == "0"
    assert verify_manifest_sha256_v1(store_root=tmp_path / "pack") == 0


def test_source_does_not_get_or_post_or_uplift() -> None:
    source = (REPO_ROOT / SOURCE_PATH).read_text(encoding="utf-8")
    for token in FORBIDDEN_SOURCE_TOKENS:
        assert token not in source
    assert "KIND_SET_RESOLVED = True" not in source
    assert "CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING = True" not in source
    assert "RAW_EQ_SOURCE_AUTHORITY = True" not in source
    assert "SOURCE_SELECTED = True" not in source
    assert "urllib" not in source


def test_canonical_pack_sealed() -> None:
    claims = json.loads((CANONICAL_PACK / "claims.json").read_text(encoding="utf-8"))
    assert claims["OWNER_GO"] == OWNER_GO
    assert claims["CURRENT_PRODUCTIVE_ACCOUNT_EQUITY_MODEL"] == (
        CURRENT_PRODUCTIVE_ACCOUNT_EQUITY_MODEL_VERSION
    )
    assert claims["AVAILABLE_FOR_SIZING_SOURCE_STATUS"] == "UNBOUND"
    assert claims["SELECTED_SOURCE"] == "NONE"
    assert claims["SELECTION_STATUS"] == "NO_SEMANTICALLY_ADMISSIBLE_CANDIDATE"
    assert claims["RECONCILIATION_TARGET_STATUS"] == "EQ_RECONCILIATION_TARGET_ONLY"
    assert claims["U04_ROLE"] == "AVAILABLE_FOR_SIZING_OR_RISK_SIZING"
    assert claims["U04_APPLICATION"] == "REDUCTION_ONLY_NOT_SOURCE_NOT_APPLIED"
    assert claims["LEGACY_RECONSTRUCTION_REQUIRED_FOR_LIVE"] == "false"
    assert claims["SEALED_LEGACY_CENSUS_REOPENED"] == "false"
    assert claims["KIND_SET"] == "EMPTY_FAIL_CLOSED"
    assert claims["CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING"] == "false"
    assert claims["FRESH_GET_EXECUTED"] == "false"
    assert claims["ACTUAL_GET_COUNT"] == "0"
    assert claims["POST_COUNT"] == "0"
    assert claims["FIRST_DEFINITIVE_BLOCK"] == BLOCKER_ID
    assert claims["EXACT_MISSING_PREDICATE"] == EXACT_MISSING_PREDICATE
    assert claims["PIN_OWNER_GO"] == PIN_OWNER_GO
    assert claims["PARENT_BLOCKER_ID"] == PARENT_BLOCKER_ID
    assert claims["BLOCKER_ID"] == BLOCKER_ID
    assert claims["NEXT_OWNER_GO_REQUIRED"] == NEXT_OWNER_GO
    assert claims["NEXT_PRODUCTIVE_NODE"] == NEXT_PRODUCTIVE_NODE
    assert verify_manifest_sha256_v1(store_root=CANONICAL_PACK) == 0


def test_runbook_cs_persists_selection_hard_stop() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    mot = MOT_PATH.read_text(encoding="utf-8")
    atlas = ATLAS_PATH.read_text(encoding="utf-8")
    runbook = RUNBOOK.read_text(encoding="utf-8")
    start = runbook.index(CS_HEADING)
    cs_section = runbook[start : runbook.index("## 11.3 Autonomy state model", start)]
    assert OWNER_GO in cs_section
    assert PIN_OWNER_GO in cs_section
    assert (
        "THIS_SLICE=11.2.1.CS.FULL_CORE_CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_SOURCE_SELECTION"
    ) in cs_section
    assert "SELECTED_SOURCE=NONE" in cs_section
    assert "SELECTION_STATUS=NO_SEMANTICALLY_ADMISSIBLE_CANDIDATE" in cs_section
    assert "FRESH_GET_EXECUTED=false" in cs_section
    assert "FRESH_GET_NOT_REQUIRED_FOR_BINDING_DECISION=true" in cs_section
    assert "LEGACY_RECONSTRUCTION_REQUIRED_FOR_LIVE=false" in cs_section
    assert "SEALED_LEGACY_CENSUS_REOPENED=false" in cs_section
    assert "RECONCILIATION_TARGET_STATUS=EQ_RECONCILIATION_TARGET_ONLY" in cs_section
    assert "U04_AVAILABLE_CAPITAL_ROLE=AVAILABLE_FOR_SIZING_OR_RISK_SIZING" in cs_section
    assert "U04_APPLICATION=REDUCTION_ONLY_NOT_SOURCE_NOT_APPLIED" in cs_section
    assert "KIND_SET=EMPTY_FAIL_CLOSED" in cs_section
    assert "EQ_TREATED_AS_SOURCE_THIS_WORKPACKAGE=false" in cs_section
    assert "AUTHORITY_UPLIFT=false" in cs_section
    assert "SOURCE_SELECTED=false" in cs_section
    assert "STEP_29P_RISK_ADMISSIBLE=false" in cs_section
    assert "NO_HOPE_GET=true" in cs_section
    assert "ACTUAL_GET_COUNT=0" in cs_section
    assert BLOCKER_ID in cs_section
    assert EXACT_MISSING_PREDICATE in cs_section
    assert NEXT_OWNER_GO in cs_section
    assert NEXT_PRODUCTIVE_NODE in cs_section
    assert NEXT_ACTION in cs_section
    assert "CURRENT_CANONICAL_SECTION=11.2.1.CS" in cs_section
    assert "ATLAS_AUTHORITY=NONE" in cs_section
    assert (
        "DOCS_TOKEN_FULL_CORE_CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_SOURCE_SELECTION_V1"
    ) in spec
    assert "FULL_CORE_CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_SOURCE_SELECTION_V1.md" in mot
    assert CS_HEADING in mot
    assert "11.2.1.CS" in atlas
    assert "current_productive_available_for_sizing_source_selection_v1.py" in atlas
    assert "ATLAS_AUTHORITY=NONE" in atlas
