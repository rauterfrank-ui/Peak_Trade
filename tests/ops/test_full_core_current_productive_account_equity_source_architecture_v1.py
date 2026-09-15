"""Current-productive account-equity source architecture tests.

Today's STEP-29P consumer needs AVAILABLE_FOR_SIZING, not reconstructed
historical equity-stock. Venue eq remains reconciliation-target only. U04
remains sizing reservation. Legacy KIND_SET remains sealed UNKNOWN. No
GET. No POST. No source mint.
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
    CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_SOURCE_STATUS,
    CURRENT_PRODUCTIVE_EQUITY_STOCK_ROLE,
    CURRENT_PRODUCTIVE_EQUITY_STOCK_SOURCE_STATUS,
    CURRENT_PRODUCTIVE_LIVE_CRITICAL_DEPENDENCY,
    CURRENT_PRODUCTIVE_PRODUCER_MINT_AUTHORIZED,
    CURRENT_PRODUCTIVE_RECONCILIATION_TARGET_ROLE,
    CURRENT_PRODUCTIVE_RESTART_RECONSTRUCTION_STATUS,
    CURRENT_PRODUCTIVE_SOURCE_SELECTED,
    EQ_RECONCILIATION_TARGET_ONLY,
    EQ_TREATED_AS_SOURCE_THIS_WORKPACKAGE,
    GOVERNED_PRODUCER_CREATED,
    KIND_SET_RESOLVED,
    KIND_SET_UPLIFT_THIS_WORKPACKAGE,
    LEGACY_RECONSTRUCTION_REQUIRED_FOR_LIVE,
    PRIMARY_PROOF_SURFACE,
    PRIMARY_PROOF_SURFACE_STATUS,
    PRODUCTIVE_U04_AVAILABLE_CAPITAL_ROLE,
    PRODUCTIVE_U04_EQUITY_STOCK_ROLE,
    RAW_EQ_SOURCE_AUTHORITY,
    RECONSTRUCTION_ALGEBRA_COMPLETE,
    SEALED_LEGACY_CENSUS_REOPENED,
    SOURCE_SELECTED,
    U04_LEGACY_ALGEBRA_IN_BASE_VS_NOT_IN_BASE,
    U04_LEGACY_STATUS,
    U05_KIND_DECISION,
    U06_KIND_DECISION,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_account_equity_source_architecture_v1 import (
    BLOCKER_ID,
    CANONICAL_PACK_RELPATH,
    EXACT_MISSING_PREDICATE,
    EXPECTED_ORIGIN_MAIN_SHA,
    FORBIDDEN_AUTHORITY_FIELDS,
    LAYER_ACCOUNT_EQUITY_STOCK,
    LAYER_AVAILABLE_FOR_SIZING,
    NEXT_ACTION,
    NEXT_OWNER_GO,
    NEXT_PRODUCTIVE_NODE,
    OWNER_GO,
    PARENT_BLOCKER_ID,
    PIN_OWNER_GO,
    PIN_OWNER_GO_STATUS,
    CurrentProductiveAccountEquitySourceArchitectureError,
    classify_current_productive_consumer_graph_v1,
    classify_current_productive_layers_v1,
    execute_current_productive_account_equity_source_architecture_v1,
    reject_available_for_sizing_mint_without_source_v1,
    reject_eq_authority_uplift_v1,
    reject_equity_stock_as_29p_sizing_input_v1,
    reject_layer_mix_stock_and_sizing_v1,
    reject_legacy_reconstruction_as_live_requirement_v1,
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
    "current_productive_account_equity_source_architecture_v1.py"
)
SPEC_PATH = (
    REPO_ROOT
    / "docs/ops/specs/"
    / "FULL_CORE_CURRENT_PRODUCTIVE_ACCOUNT_EQUITY_SOURCE_ARCHITECTURE_V1.md"
)
MOT_PATH = REPO_ROOT / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md"
ATLAS_PATH = REPO_ROOT / "docs/system_atlas/entities/catalog.yaml"
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
CANONICAL_PACK = REPO_ROOT / CANONICAL_PACK_RELPATH
CR_HEADING = "11.2.1.CR FULL_CORE_CURRENT_PRODUCTIVE_ACCOUNT_EQUITY_SOURCE_ARCHITECTURE"
FORBIDDEN_SOURCE_TOKENS = (
    "urllib",
    "requests",
    "httpx",
    "GET_ENDPOINTS_PRIVATE",
    "max_retries",
    "eq=cashBal",
)


def _execute(tmp_path: Path) -> object:
    return execute_current_productive_account_equity_source_architecture_v1(
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        evidence_root=tmp_path / "pack",
        repo_root=REPO_ROOT,
    )


def test_standing_pins_remain_fail_closed() -> None:
    assert LIVE_ENABLED is True
    assert LIVE_ARMED is True
    assert WIRE_SEND_PERMITTED is True
    assert RAW_EQ_SOURCE_AUTHORITY is False
    assert EQ_RECONCILIATION_TARGET_ONLY is True
    assert EQ_TREATED_AS_SOURCE_THIS_WORKPACKAGE is False
    assert CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING is False
    assert MAPPING_PROVEN is False
    assert RECONSTRUCTION_ALGEBRA_COMPLETE is False
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
    assert CURRENT_PRODUCTIVE_EQUITY_STOCK_SOURCE_STATUS == "UNBOUND"
    assert CURRENT_PRODUCTIVE_EQUITY_STOCK_ROLE == "ACCOUNT_EQUITY_STOCK_NOT_29P_SIZING_INPUT"
    assert CURRENT_PRODUCTIVE_RECONCILIATION_TARGET_ROLE == "EQ_RECONCILIATION_TARGET_ONLY"
    assert CURRENT_PRODUCTIVE_LIVE_CRITICAL_DEPENDENCY == (
        "CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_SOURCE_UNBOUND"
    )
    assert CURRENT_PRODUCTIVE_RESTART_RECONSTRUCTION_STATUS == (
        "FAIL_CLOSED_UNTIL_CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_SOURCE_BOUND"
    )
    assert CURRENT_PRODUCTIVE_29P_CONSUMER_BINDING_STATUS == "BOUND_AVAILABLE_FOR_SIZING_ONLY"
    assert PRIMARY_PROOF_SURFACE_STATUS == "NONE_IN_EXISTING_REPO_HISTORICAL_FORENSIC_EVIDENCE"
    assert PRIMARY_PROOF_SURFACE == "NONE"
    assert U04_LEGACY_STATUS == "UNRESOLVED"
    assert U04_LEGACY_ALGEBRA_IN_BASE_VS_NOT_IN_BASE == "UNRESOLVED"
    assert PRODUCTIVE_U04_EQUITY_STOCK_ROLE == DISPOSITION_NOT_EQUITY_STOCK
    assert PRODUCTIVE_U04_AVAILABLE_CAPITAL_ROLE == "AVAILABLE_FOR_SIZING_OR_RISK_SIZING"
    assert U05_KIND_DECISION == DECISION_REMAIN_UNKNOWN
    assert U06_KIND_DECISION == DECISION_REMAIN_UNKNOWN
    assert EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY == (
        "NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING"
    )


def test_wrong_owner_go_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(
        CurrentProductiveAccountEquitySourceArchitectureError, match="OWNER_GO_MISMATCH"
    ):
        execute_current_productive_account_equity_source_architecture_v1(
            owner_go="WRONG",
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            evidence_root=tmp_path / "pack",
        )


def test_wrong_origin_sha_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(
        CurrentProductiveAccountEquitySourceArchitectureError,
        match="ORIGIN_MAIN_SHA_MISMATCH",
    ):
        execute_current_productive_account_equity_source_architecture_v1(
            owner_go=OWNER_GO,
            origin_main_sha="deadbeef",
            evidence_root=tmp_path / "pack",
        )


def test_eq_is_not_source_and_not_uplifted() -> None:
    reject_eq_as_source_authority_v1(claimed="false")
    reject_eq_authority_uplift_v1(claimed="false")
    for claimed in ("true", "SOURCE", "AUTHORITY_UPLIFT", "SIZING_SOURCE"):
        with pytest.raises(Exception, match="EQ_"):
            reject_eq_authority_uplift_v1(claimed=claimed)


def test_equity_stock_is_not_29p_sizing_input() -> None:
    reject_equity_stock_as_29p_sizing_input_v1(claimed="false")
    for claimed in ("true", "STEP_29P_SIZING_INPUT", LAYER_ACCOUNT_EQUITY_STOCK):
        with pytest.raises(
            CurrentProductiveAccountEquitySourceArchitectureError,
            match="ACCOUNT_EQUITY_STOCK_IS_NOT_29P_SIZING_INPUT",
        ):
            reject_equity_stock_as_29p_sizing_input_v1(claimed=claimed)


def test_available_for_sizing_mint_forbidden_until_source() -> None:
    reject_available_for_sizing_mint_without_source_v1(claimed="false")
    for claimed in ("true", "MINTED", "AUTHORITY", "SELECTED"):
        with pytest.raises(
            CurrentProductiveAccountEquitySourceArchitectureError,
            match="AVAILABLE_FOR_SIZING_MINT_FORBIDDEN_UNTIL_SOURCE_BOUND",
        ):
            reject_available_for_sizing_mint_without_source_v1(claimed=claimed)


def test_stock_and_sizing_layers_remain_distinct() -> None:
    reject_layer_mix_stock_and_sizing_v1(claimed="false")
    with pytest.raises(
        CurrentProductiveAccountEquitySourceArchitectureError,
        match="EQUITY_STOCK_AND_AVAILABLE_FOR_SIZING_MUST_REMAIN_DISTINCT",
    ):
        reject_layer_mix_stock_and_sizing_v1(claimed="MIXED")


def test_legacy_reconstruction_not_required_for_live() -> None:
    reject_legacy_reconstruction_as_live_requirement_v1(claimed="false")
    with pytest.raises(
        CurrentProductiveAccountEquitySourceArchitectureError,
        match="LEGACY_RECONSTRUCTION_IS_NOT_REQUIRED_FOR_LIVE",
    ):
        reject_legacy_reconstruction_as_live_requirement_v1(claimed="REQUIRED_FOR_LIVE")


def test_consumer_graph_binds_29p_to_available_for_sizing() -> None:
    graph = classify_current_productive_consumer_graph_v1()
    assert graph["required_dimension"] == RISK_EQUITY_DIMENSION
    assert graph["account_equity_stock_required_for_29p"] == "false"
    assert graph["legacy_kind_set_required_for_29p"] == "false"
    assert graph["live_critical_consumer"] == "STEP_29P_CAPITAL_RISK_ADMISSIBILITY"
    rows = graph["consumers"]
    assert rows[0]["layer"] == LAYER_AVAILABLE_FOR_SIZING
    assert rows[0]["consumes_venue_eq_as_source"] == "false"
    assert "eq" in FORBIDDEN_AUTHORITY_FIELDS


def test_execute_ratifies_architecture_without_source_mint(tmp_path: Path) -> None:
    result = _execute(tmp_path)
    claims = json.loads((tmp_path / "pack" / "claims.json").read_text(encoding="utf-8"))
    layers = json.loads((tmp_path / "pack" / "layers_v1.json").read_text(encoding="utf-8"))
    consumers = json.loads(
        (tmp_path / "pack" / "consumer_graph_v1.json").read_text(encoding="utf-8")
    )
    assert result.architecture_ratified == "true"
    assert result.current_productive_model == CURRENT_PRODUCTIVE_ACCOUNT_EQUITY_MODEL_VERSION
    assert result.available_for_sizing_source_status == "UNBOUND"
    assert result.equity_stock_source_status == "UNBOUND"
    assert result.reconciliation_target == "EQ_RECONCILIATION_TARGET_ONLY"
    assert result.u04_role == "AVAILABLE_FOR_SIZING_OR_RISK_SIZING"
    assert result.current_live_critical_blocker == (
        "CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_SOURCE_UNBOUND"
    )
    assert claims["LEGACY_RECONSTRUCTION_REQUIRED_FOR_LIVE"] == "false"
    assert claims["SEALED_LEGACY_CENSUS_REOPENED"] == "false"
    assert claims["SOURCE_SELECTED"] == "false"
    assert claims["PRODUCER_MINT_AUTHORIZED"] == "false"
    assert claims["AUTHORITY_UPLIFT"] == "false"
    assert claims["EQ_TREATED_AS_SOURCE_THIS_WORKPACKAGE"] == "false"
    assert claims["U04_LEGACY_STATUS"] == "UNRESOLVED"
    assert claims["U05_LEGACY_STATUS"] == DECISION_REMAIN_UNKNOWN
    assert claims["KIND_SET"] == "EMPTY_FAIL_CLOSED"
    assert claims["STEP_29P_RISK_ADMISSIBLE"] == "false"
    assert claims["PIN_OWNER_GO_STATUS"] == PIN_OWNER_GO_STATUS
    assert layers["layers"][LAYER_ACCOUNT_EQUITY_STOCK]["required_for_29p_sizing"] == "false"
    assert layers["layers"][LAYER_AVAILABLE_FOR_SIZING]["required_for_29p_sizing"] == "true"
    assert consumers["legacy_kind_set_required_for_29p"] == "false"
    assert verify_manifest_sha256_v1(store_root=tmp_path / "pack") == 0


def test_source_does_not_get_or_post_or_uplift() -> None:
    source = (REPO_ROOT / SOURCE_PATH).read_text(encoding="utf-8")
    for token in FORBIDDEN_SOURCE_TOKENS:
        assert token not in source
    assert "KIND_SET_RESOLVED = True" not in source
    assert "CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING = True" not in source
    assert "RAW_EQ_SOURCE_AUTHORITY = True" not in source
    assert "SOURCE_SELECTED = True" not in source


def test_canonical_pack_sealed() -> None:
    claims = json.loads((CANONICAL_PACK / "claims.json").read_text(encoding="utf-8"))
    assert claims["OWNER_GO"] == OWNER_GO
    assert claims["CURRENT_PRODUCTIVE_ACCOUNT_EQUITY_MODEL"] == (
        CURRENT_PRODUCTIVE_ACCOUNT_EQUITY_MODEL_VERSION
    )
    assert claims["AVAILABLE_FOR_SIZING_SOURCE_STATUS"] == "UNBOUND"
    assert claims["RECONCILIATION_TARGET_STATUS"] == "EQ_RECONCILIATION_TARGET_ONLY"
    assert claims["U04_ROLE"] == "AVAILABLE_FOR_SIZING_OR_RISK_SIZING"
    assert claims["LEGACY_RECONSTRUCTION_REQUIRED_FOR_LIVE"] == "false"
    assert claims["SEALED_LEGACY_CENSUS_REOPENED"] == "false"
    assert claims["KIND_SET"] == "EMPTY_FAIL_CLOSED"
    assert claims["CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING"] == "false"
    assert claims["U04_LEGACY_STATUS"] == "UNRESOLVED"
    assert claims["U05_LEGACY_STATUS"] == DECISION_REMAIN_UNKNOWN
    assert claims["U06_LEGACY_STATUS"] == DECISION_REMAIN_UNKNOWN
    assert claims["ACTUAL_GET_COUNT"] == "0"
    assert claims["POST_COUNT"] == "0"
    assert claims["FIRST_DEFINITIVE_BLOCK"] == (
        "CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_SOURCE_UNBOUND"
    )
    assert claims["EXACT_MISSING_PREDICATE"] == EXACT_MISSING_PREDICATE
    assert claims["PIN_OWNER_GO"] == PIN_OWNER_GO
    assert claims["PARENT_BLOCKER_ID"] == PARENT_BLOCKER_ID
    assert claims["BLOCKER_ID"] == BLOCKER_ID
    assert claims["NEXT_OWNER_GO_REQUIRED"] == NEXT_OWNER_GO
    assert claims["NEXT_PRODUCTIVE_NODE"] == NEXT_PRODUCTIVE_NODE
    assert verify_manifest_sha256_v1(store_root=CANONICAL_PACK) == 0


def test_runbook_cr_persists_architecture() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    mot = MOT_PATH.read_text(encoding="utf-8")
    atlas = ATLAS_PATH.read_text(encoding="utf-8")
    runbook = RUNBOOK.read_text(encoding="utf-8")
    start = runbook.index(CR_HEADING)
    cr_section = runbook[start : runbook.index("## 11.3 Autonomy state model", start)]
    assert OWNER_GO in cr_section
    assert PIN_OWNER_GO in cr_section
    assert (
        "THIS_SLICE=11.2.1.CR.FULL_CORE_CURRENT_PRODUCTIVE_ACCOUNT_EQUITY_SOURCE_ARCHITECTURE"
    ) in cr_section
    assert "CURRENT_PRODUCTIVE_ACCOUNT_EQUITY_MODEL=CURRENT_PRODUCTIVE_ACCOUNT_EQUITY_MODEL_V1" in (
        cr_section
    )
    assert "LEGACY_RECONSTRUCTION_REQUIRED_FOR_LIVE=false" in cr_section
    assert "SEALED_LEGACY_CENSUS_REOPENED=false" in cr_section
    assert "RECONCILIATION_TARGET_STATUS=EQ_RECONCILIATION_TARGET_ONLY" in cr_section
    assert "U04_AVAILABLE_CAPITAL_ROLE=AVAILABLE_FOR_SIZING_OR_RISK_SIZING" in cr_section
    assert "U04_EQUITY_STOCK_ROLE=NOT_EQUITY_STOCK_AFFECTING" in cr_section
    assert "KIND_SET=EMPTY_FAIL_CLOSED" in cr_section
    assert "KIND_SET_RESOLVED=false" in cr_section
    assert "EQ_TREATED_AS_SOURCE_THIS_WORKPACKAGE=false" in cr_section
    assert "AUTHORITY_UPLIFT=false" in cr_section
    assert "SOURCE_SELECTED=false" in cr_section
    assert "STEP_29P_RISK_ADMISSIBLE=false" in cr_section
    assert "U05_LEGACY_STATUS=REMAIN_UNKNOWN" in cr_section
    assert "U06_LEGACY_STATUS=REMAIN_UNKNOWN" in cr_section
    assert "NO_GET_REQUIRED=true" in cr_section
    assert "ACTUAL_GET_COUNT=0" in cr_section
    assert "FIRST_DEFINITIVE_BLOCK=CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_SOURCE_UNBOUND" in (
        cr_section
    )
    assert EXACT_MISSING_PREDICATE in cr_section
    assert BLOCKER_ID in cr_section
    assert NEXT_OWNER_GO in cr_section
    assert NEXT_PRODUCTIVE_NODE in cr_section
    assert NEXT_ACTION in cr_section
    assert "CURRENT_CANONICAL_SECTION=11.2.1.CR" in cr_section
    assert "ATLAS_AUTHORITY=NONE" in cr_section
    assert ("DOCS_TOKEN_FULL_CORE_CURRENT_PRODUCTIVE_ACCOUNT_EQUITY_SOURCE_ARCHITECTURE_V1") in spec
    assert "FULL_CORE_CURRENT_PRODUCTIVE_ACCOUNT_EQUITY_SOURCE_ARCHITECTURE_V1.md" in mot
    assert CR_HEADING in mot
    assert "11.2.1.CR" in atlas
    assert "current_productive_account_equity_source_architecture_v1.py" in atlas
    assert "ATLAS_AUTHORITY=NONE" in atlas
