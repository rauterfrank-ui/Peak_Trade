"""U04 productive-scope and mapping-deny tests.

Historical U04 algebra inclusion remains UNRESOLVED. Productive stock
membership is not EXCLUDE. Mapping remains not canonically valid. No GET.
No POST. KIND_SET remains EMPTY_FAIL_CLOSED.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    LIVE_ARMED,
    LIVE_ENABLED,
    MAPPING_PROVEN,
    MS2_AUTHORIZED,
    WIRE_SEND_PERMITTED,
)
from src.ops.full_core_live_path_composition_root_v1.live_admission_gap_dag_v1 import (
    EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.bj_future_admissible_evidence_and_include_exclude_qualification_law_v1 import (
    OUTCOME_EXCLUDE,
    OUTCOME_INCLUDE,
    TARGET_RESIDUAL,
    TARGET_U05,
    TARGET_U06,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.classified_event_kind_set_and_source_seam_contract_v1 import (
    DISPOSITION_NOT_EQUITY_STOCK,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    ACCOUNT_EQUITY_SOURCE_MAPPING_DENIED_THIS_WORKPACKAGE,
    CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING,
    CURRENT_PRODUCTIVE_REMAINING_NECESSARY_EQUITY_STOCK_CLASSES,
    EQ_RECONCILIATION_TARGET_ONLY,
    KIND_SET_RESOLVED,
    NAMED_REMAINING_UNKNOWN_NECESSARY_CLASSES,
    PRODUCTIVE_U04_AVAILABLE_CAPITAL_ROLE,
    PRODUCTIVE_U04_EQUITY_STOCK_KIND_MEMBERSHIP,
    PRODUCTIVE_U04_EQUITY_STOCK_ROLE,
    RAW_EQ_SOURCE_AUTHORITY,
    RECONSTRUCTION_ALGEBRA_COMPLETE,
    RESIDUAL_KIND_DECISION,
    SEMANTIC_MAPPING_PROVEN,
    U04_LEGACY_ALGEBRA_IN_BASE_VS_NOT_IN_BASE,
    U04_LEGACY_STATUS,
    U04_PLACEMENT,
    U05_KIND_DECISION,
    U06_KIND_DECISION,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.named_remaining_unknown_kind_set_evidence_persist_contract_v1 import (
    DECISION_REMAIN_UNKNOWN,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_s6_mapping_classification_v1 import (
    verify_manifest_sha256_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.reconstruction_algebra_contract_v1 import (
    EARLIEST_UNRESOLVED_ALGEBRA_TERM,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.remaining_necessary_kind_evidence_classification_v1 import (
    RemainingNecessaryKindEvidenceClassificationError,
    reject_u04_reclassify_as_equity_stock_kind_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.u04_pending_order_reservation_or_account_equity_mapping_v1 import (
    BLOCKER_ID,
    CANONICAL_PACK_RELPATH,
    EXACT_MISSING_PREDICATE,
    EXPECTED_ORIGIN_MAIN_SHA,
    MAPPING_EVIDENCE,
    NEXT_ACTION,
    NEXT_OWNER_GO,
    NEXT_PRODUCTIVE_NODE,
    OWNER_GO,
    PARENT_BLOCKER_ID,
    PIN_OWNER_GO,
    U04_EVIDENCE,
    U04PendingOrderReservationOrAccountEquityMappingError,
    execute_u04_pending_order_reservation_or_account_equity_mapping_v1,
    reject_eq_as_source_authority_v1,
    reject_productive_not_in_kind_set_as_exclude_v1,
    reject_unresolved_inclusion_as_in_base_or_not_in_base_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = (
    "src/ops/governed_productive_account_equity_authority_producer_v1/"
    "u04_pending_order_reservation_or_account_equity_mapping_v1.py"
)
SPEC_PATH = (
    REPO_ROOT
    / "docs/ops/specs/"
    / "FULL_CORE_U04_PENDING_ORDER_RESERVATION_OR_ACCOUNT_EQUITY_MAPPING_V1.md"
)
MOT_PATH = REPO_ROOT / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md"
ATLAS_PATH = REPO_ROOT / "docs/system_atlas/entities/catalog.yaml"
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
CANONICAL_PACK = REPO_ROOT / CANONICAL_PACK_RELPATH
CO_HEADING = "11.2.1.CO FULL_CORE_U04_PENDING_ORDER_RESERVATION_OR_ACCOUNT_EQUITY_MAPPING"
FORBIDDEN_SOURCE_TOKENS = (
    "urllib",
    "requests",
    "httpx",
    "GET_ENDPOINTS_PRIVATE",
    "max_retries",
    "eq=cashBal",
)


def _execute(tmp_path: Path) -> object:
    return execute_u04_pending_order_reservation_or_account_equity_mapping_v1(
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        evidence_root=tmp_path / "pack",
        repo_root=REPO_ROOT,
    )


def test_standing_pins_remain_fail_closed() -> None:
    assert LIVE_ENABLED is True
    assert LIVE_ARMED is True
    assert WIRE_SEND_PERMITTED is True
    assert MS2_AUTHORIZED is False
    assert RAW_EQ_SOURCE_AUTHORITY is False
    assert EQ_RECONCILIATION_TARGET_ONLY is True
    assert CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING is True
    assert MAPPING_PROVEN is False
    assert SEMANTIC_MAPPING_PROVEN is False
    assert RECONSTRUCTION_ALGEBRA_COMPLETE is False
    assert KIND_SET_RESOLVED is False
    assert ACCOUNT_EQUITY_SOURCE_MAPPING_DENIED_THIS_WORKPACKAGE is True
    assert U04_LEGACY_STATUS == "UNRESOLVED"
    assert U04_LEGACY_ALGEBRA_IN_BASE_VS_NOT_IN_BASE == "UNRESOLVED"
    assert PRODUCTIVE_U04_EQUITY_STOCK_KIND_MEMBERSHIP == "NOT_IN_CURRENT_PRODUCTIVE_KIND_SET"
    assert PRODUCTIVE_U04_EQUITY_STOCK_ROLE == DISPOSITION_NOT_EQUITY_STOCK
    assert PRODUCTIVE_U04_AVAILABLE_CAPITAL_ROLE == "AVAILABLE_FOR_SIZING_OR_RISK_SIZING"
    assert U04_PLACEMENT == "AVAILABLE_FOR_SIZING_OR_RISK_SIZING"
    assert U05_KIND_DECISION == DECISION_REMAIN_UNKNOWN
    assert U06_KIND_DECISION == DECISION_REMAIN_UNKNOWN
    assert RESIDUAL_KIND_DECISION == DECISION_REMAIN_UNKNOWN
    assert NAMED_REMAINING_UNKNOWN_NECESSARY_CLASSES == (TARGET_U05, TARGET_U06, TARGET_RESIDUAL)
    assert CURRENT_PRODUCTIVE_REMAINING_NECESSARY_EQUITY_STOCK_CLASSES == ()
    assert EARLIEST_UNRESOLVED_ALGEBRA_TERM == "U04_PENDING_ORDER_RESERVATION_INCLUSION_UNRESOLVED"
    assert EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY == (
        "CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_SURFACE_BOUND_VALUE_REQUIRES_FRESH_TRUSTED_GET"
    )


def test_wrong_owner_go_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(
        U04PendingOrderReservationOrAccountEquityMappingError,
        match="OWNER_GO_MISMATCH",
    ):
        execute_u04_pending_order_reservation_or_account_equity_mapping_v1(
            owner_go="WRONG",
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            evidence_root=tmp_path / "pack",
        )


def test_wrong_origin_sha_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(
        U04PendingOrderReservationOrAccountEquityMappingError,
        match="ORIGIN_MAIN_SHA_MISMATCH",
    ):
        execute_u04_pending_order_reservation_or_account_equity_mapping_v1(
            owner_go=OWNER_GO,
            origin_main_sha="deadbeef",
            evidence_root=tmp_path / "pack",
        )


def test_unresolved_inclusion_is_not_in_base_or_not_in_base() -> None:
    reject_unresolved_inclusion_as_in_base_or_not_in_base_v1(claimed="UNRESOLVED")
    for claimed in (OUTCOME_INCLUDE, OUTCOME_EXCLUDE, "IN_BASE", "NOT_IN_BASE", "0"):
        with pytest.raises(
            U04PendingOrderReservationOrAccountEquityMappingError,
            match="UNRESOLVED_INCLUSION_IS_NOT_IN_BASE_OR_NOT_IN_BASE",
        ):
            reject_unresolved_inclusion_as_in_base_or_not_in_base_v1(claimed=claimed)


def test_productive_not_in_kind_set_is_not_exclude() -> None:
    reject_productive_not_in_kind_set_as_exclude_v1(claimed="NOT_IN_CURRENT_PRODUCTIVE_KIND_SET")
    for claimed in (OUTCOME_EXCLUDE, "EXCLUDE", "IN_BASE"):
        with pytest.raises(
            U04PendingOrderReservationOrAccountEquityMappingError,
            match="PRODUCTIVE_NOT_IN_KIND_SET_IS_NOT_EXCLUDE",
        ):
            reject_productive_not_in_kind_set_as_exclude_v1(claimed=claimed)


def test_eq_is_not_source_authority() -> None:
    reject_eq_as_source_authority_v1(claimed="false")
    for claimed in ("true", "SOURCE", "RAW_EQ_SOURCE_AUTHORITY"):
        with pytest.raises(
            U04PendingOrderReservationOrAccountEquityMappingError,
            match="EQ_IS_RECONCILIATION_TARGET_NOT_SOURCE",
        ):
            reject_eq_as_source_authority_v1(claimed=claimed)


def test_u04_cannot_be_reclassified_as_equity_stock_kind() -> None:
    reject_u04_reclassify_as_equity_stock_kind_v1(claimed=DISPOSITION_NOT_EQUITY_STOCK)
    with pytest.raises(
        RemainingNecessaryKindEvidenceClassificationError,
        match="U04_RECLASSIFY_AS_EQUITY_STOCK_KIND_FORBIDDEN",
    ):
        reject_u04_reclassify_as_equity_stock_kind_v1(claimed=OUTCOME_INCLUDE)


def test_execute_splits_scope_and_denies_mapping(tmp_path: Path) -> None:
    result = _execute(tmp_path)
    claims = json.loads((tmp_path / "pack" / "claims.json").read_text(encoding="utf-8"))
    split = json.loads((tmp_path / "pack" / "qualification_v1.json").read_text(encoding="utf-8"))
    downstream = json.loads(
        (tmp_path / "pack" / "downstream_dependency_tree_v1.json").read_text(encoding="utf-8")
    )
    assert result.u04_legacy_status == "UNRESOLVED"
    assert result.u04_productive_scope_status == "NOT_IN_CURRENT_PRODUCTIVE_KIND_SET"
    assert result.u04_equity_stock_role == DISPOSITION_NOT_EQUITY_STOCK
    assert result.u04_available_capital_role == "AVAILABLE_FOR_SIZING_OR_RISK_SIZING"
    assert result.kind_set_resolved == "false"
    assert result.canonically_valid_account_equity_source_mapping == "false"
    assert result.account_equity_source_mapping_status == (
        "NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING"
    )
    assert result.reconciliation_target_status == "EQ_RECONCILIATION_TARGET_ONLY"
    assert claims["U04_INCLUDE_PROVEN"] == "false"
    assert claims["U04_EXCLUDE_PROVEN"] == "false"
    assert claims["U04_IN_BASE_PROVEN"] == "false"
    assert claims["U04_NOT_IN_BASE_PROVEN"] == "false"
    assert claims["KIND_SET_RESOLVED"] == "false"
    assert claims["CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING"] == "false"
    assert claims["ACCOUNT_EQUITY_SOURCE_MAPPING_DENIED_THIS_WORKPACKAGE"] == "true"
    assert split["u04_legacy_status"] == "UNRESOLVED"
    assert downstream["current_productive_remaining_necessary_equity_stock_classes"] == ""
    assert verify_manifest_sha256_v1(store_root=tmp_path / "pack") == 0


def test_source_does_not_get_or_post_or_uplift() -> None:
    source = (REPO_ROOT / SOURCE_PATH).read_text(encoding="utf-8")
    for token in FORBIDDEN_SOURCE_TOKENS:
        assert token not in source
    assert "cashBal+upl" not in source
    assert "KIND_SET_RESOLVED = True" not in source
    assert "CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING = True" not in source
    assert "RAW_EQ_SOURCE_AUTHORITY = True" not in source


def test_canonical_pack_sealed() -> None:
    claims = json.loads((CANONICAL_PACK / "claims.json").read_text(encoding="utf-8"))
    assert claims["OWNER_GO"] == OWNER_GO
    assert claims["U04_LEGACY_STATUS"] == "UNRESOLVED"
    assert claims["U04_PRODUCTIVE_SCOPE_STATUS"] == "NOT_IN_CURRENT_PRODUCTIVE_KIND_SET"
    assert claims["U04_EQUITY_STOCK_ROLE"] == DISPOSITION_NOT_EQUITY_STOCK
    assert claims["U04_AVAILABLE_CAPITAL_ROLE"] == "AVAILABLE_FOR_SIZING_OR_RISK_SIZING"
    assert claims["U04_EVIDENCE"] == U04_EVIDENCE
    assert claims["ACCOUNT_EQUITY_SOURCE_MAPPING_EVIDENCE"] == MAPPING_EVIDENCE
    assert claims["KIND_SET"] == "EMPTY_FAIL_CLOSED"
    assert claims["KIND_SET_RESOLVED"] == "false"
    assert claims["CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING"] == "false"
    assert claims["RECONCILIATION_TARGET_STATUS"] == "EQ_RECONCILIATION_TARGET_ONLY"
    assert claims["U04_STATUS"] == "UNRESOLVED"
    assert claims["U05_LEGACY_STATUS"] == DECISION_REMAIN_UNKNOWN
    assert claims["U06_LEGACY_STATUS"] == DECISION_REMAIN_UNKNOWN
    assert claims["RESIDUAL_LEGACY_STATUS"] == DECISION_REMAIN_UNKNOWN
    assert claims["ACTUAL_GET_COUNT"] == "0"
    assert claims["POST_COUNT"] == "0"
    assert claims["FIRST_DEFINITIVE_BLOCK"] == (
        "NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING"
    )
    assert claims["EXACT_MISSING_PREDICATE"] == EXACT_MISSING_PREDICATE
    assert claims["PIN_OWNER_GO"] == PIN_OWNER_GO
    assert claims["PARENT_BLOCKER_ID"] == PARENT_BLOCKER_ID
    assert claims["BLOCKER_ID"] == BLOCKER_ID
    assert claims["NEXT_OWNER_GO_REQUIRED"] == NEXT_OWNER_GO
    assert claims["NEXT_PRODUCTIVE_NODE"] == NEXT_PRODUCTIVE_NODE
    assert verify_manifest_sha256_v1(store_root=CANONICAL_PACK) == 0


def test_runbook_co_persists_scope_and_mapping_deny() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    mot = MOT_PATH.read_text(encoding="utf-8")
    atlas = ATLAS_PATH.read_text(encoding="utf-8")
    runbook = RUNBOOK.read_text(encoding="utf-8")
    start = runbook.index(CO_HEADING)
    co_section = runbook[start : runbook.index("## 11.3 Autonomy state model", start)]
    assert OWNER_GO in co_section
    assert PIN_OWNER_GO in co_section
    assert (
        "THIS_SLICE=11.2.1.CO.FULL_CORE_U04_PENDING_ORDER_RESERVATION_OR_ACCOUNT_EQUITY_MAPPING"
    ) in co_section
    assert "U04_LEGACY_STATUS=UNRESOLVED" in co_section
    assert "U04_PRODUCTIVE_SCOPE_STATUS=NOT_IN_CURRENT_PRODUCTIVE_KIND_SET" in co_section
    assert "U04_EQUITY_STOCK_ROLE=NOT_EQUITY_STOCK_AFFECTING" in co_section
    assert "U04_AVAILABLE_CAPITAL_ROLE=AVAILABLE_FOR_SIZING_OR_RISK_SIZING" in co_section
    assert "KIND_SET=EMPTY_FAIL_CLOSED" in co_section
    assert "KIND_SET_RESOLVED=false" in co_section
    assert "CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING=false" in co_section
    assert "RECONCILIATION_TARGET_STATUS=EQ_RECONCILIATION_TARGET_ONLY" in co_section
    assert "U04_STATUS=UNRESOLVED" in co_section
    assert "U05_LEGACY_STATUS=REMAIN_UNKNOWN" in co_section
    assert "U06_LEGACY_STATUS=REMAIN_UNKNOWN" in co_section
    assert "RESIDUAL_LEGACY_STATUS=REMAIN_UNKNOWN" in co_section
    assert "DURABLE_UNKNOWN_NOT_INCLUDE=true" in co_section
    assert "DURABLE_UNKNOWN_NOT_EXCLUDE=true" in co_section
    assert "NO_GET_REQUIRED=true" in co_section
    assert "ACTUAL_GET_COUNT=0" in co_section
    assert "FIRST_DEFINITIVE_BLOCK=NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING" in (
        co_section
    )
    assert EXACT_MISSING_PREDICATE in co_section
    assert BLOCKER_ID in co_section
    assert NEXT_OWNER_GO in co_section
    assert NEXT_PRODUCTIVE_NODE in co_section
    assert NEXT_ACTION in co_section
    assert "CURRENT_CANONICAL_SECTION=11.2.1.CO" in co_section
    assert "ATLAS_AUTHORITY=NONE" in co_section
    assert (
        "DOCS_TOKEN_FULL_CORE_U04_PENDING_ORDER_RESERVATION_OR_ACCOUNT_EQUITY_MAPPING_V1"
    ) in spec
    assert "FULL_CORE_U04_PENDING_ORDER_RESERVATION_OR_ACCOUNT_EQUITY_MAPPING_V1.md" in mot
    assert CO_HEADING in mot
    assert "11.2.1.CO" in atlas
    assert "u04_pending_order_reservation_or_account_equity_mapping_v1.py" in atlas
    assert "ATLAS_AUTHORITY=NONE" in atlas
