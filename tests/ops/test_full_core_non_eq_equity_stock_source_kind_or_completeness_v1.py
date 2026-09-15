"""Non-eq source-kind insufficiency and completeness tests.

No source kind is ratified. Completeness is INSUFFICIENT_UNPROVEN.
KIND_SET remains EMPTY_FAIL_CLOSED. Venue eq remains reconciliation-target
only. U04 is not reintroduced. No GET. No POST.
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
from src.ops.governed_productive_account_equity_authority_producer_v1.account_equity_source_mapping_ratification_v1 import (
    RATIFIED_SOURCE_KIND_SET,
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
    CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING,
    CURRENT_PRODUCTIVE_REMAINING_NECESSARY_EQUITY_STOCK_CLASSES,
    EQ_RECONCILIATION_TARGET_ONLY,
    EQ_TREATED_AS_SOURCE_THIS_WORKPACKAGE,
    KIND_SET_RESOLVED,
    KIND_SET_UPLIFT_THIS_WORKPACKAGE,
    NAMED_REMAINING_UNKNOWN_NECESSARY_CLASSES,
    NON_EQ_EQUITY_STOCK_SOURCE_KIND_STATUS,
    PRODUCTIVE_U04_AVAILABLE_CAPITAL_ROLE,
    PRODUCTIVE_U04_EQUITY_STOCK_KIND_MEMBERSHIP,
    PRODUCTIVE_U04_EQUITY_STOCK_ROLE,
    RATIFIED_NON_EQ_EQUITY_STOCK_SOURCE_KINDS,
    RAW_EQ_SOURCE_AUTHORITY,
    RECONSTRUCTION_ALGEBRA_COMPLETE,
    RESIDUAL_KIND_DECISION,
    SEMANTIC_MAPPING_PROVEN,
    SOURCE_KIND_COMPLETENESS_RATIFICATION,
    SOURCE_KIND_COMPLETENESS_STATUS,
    U04_LEGACY_ALGEBRA_IN_BASE_VS_NOT_IN_BASE,
    U04_LEGACY_STATUS,
    U04_PLACEMENT,
    U05_KIND_DECISION,
    U06_KIND_DECISION,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.live_equity_stock_today_initial_stock_source_kind_v1 import (
    TODAY_SOURCE_KIND,
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
from src.ops.governed_productive_account_equity_authority_producer_v1.non_eq_equity_stock_source_kind_or_completeness_v1 import (
    BLOCKER_ID,
    CANONICAL_PACK_RELPATH,
    COMPLETENESS_EVIDENCE,
    EXACT_MISSING_PREDICATE,
    EXPECTED_ORIGIN_MAIN_SHA,
    NEXT_ACTION,
    NEXT_OWNER_GO,
    NEXT_PRODUCTIVE_NODE,
    NonEqEquityStockSourceKindOrCompletenessError,
    OWNER_GO,
    PARENT_BLOCKER_ID,
    PIN_OWNER_GO,
    SOURCE_KIND_EVIDENCE,
    STATUS_NOT_RATIFIABLE_EQ_TARGET,
    STATUS_NOT_RATIFIABLE_LIVE_TODAY,
    execute_non_eq_equity_stock_source_kind_or_completeness_v1,
    reject_empty_productive_remaining_as_completeness_v1,
    reject_kind_set_uplift_v1,
    reject_single_kind_as_completeness_v1,
    reject_today_as_account_equity_source_kind_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.u04_pending_order_reservation_or_account_equity_mapping_v1 import (
    reject_eq_as_source_authority_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = (
    "src/ops/governed_productive_account_equity_authority_producer_v1/"
    "non_eq_equity_stock_source_kind_or_completeness_v1.py"
)
SPEC_PATH = (
    REPO_ROOT
    / "docs/ops/specs/"
    / "FULL_CORE_NON_EQ_EQUITY_STOCK_SOURCE_KIND_OR_COMPLETENESS_V1.md"
)
MOT_PATH = REPO_ROOT / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md"
ATLAS_PATH = REPO_ROOT / "docs/system_atlas/entities/catalog.yaml"
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
CANONICAL_PACK = REPO_ROOT / CANONICAL_PACK_RELPATH
CP_HEADING = "11.2.1.CP FULL_CORE_NON_EQ_EQUITY_STOCK_SOURCE_KIND_OR_COMPLETENESS"
FORBIDDEN_SOURCE_TOKENS = (
    "urllib",
    "requests",
    "httpx",
    "GET_ENDPOINTS_PRIVATE",
    "max_retries",
    "eq=cashBal",
)


def _execute(tmp_path: Path) -> object:
    return execute_non_eq_equity_stock_source_kind_or_completeness_v1(
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        evidence_root=tmp_path / "pack",
        repo_root=REPO_ROOT,
    )


def test_standing_pins_remain_fail_closed() -> None:
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert WIRE_SEND_PERMITTED is False
    assert MS2_AUTHORIZED is False
    assert RAW_EQ_SOURCE_AUTHORITY is False
    assert EQ_RECONCILIATION_TARGET_ONLY is True
    assert EQ_TREATED_AS_SOURCE_THIS_WORKPACKAGE is False
    assert CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING is False
    assert MAPPING_PROVEN is False
    assert SEMANTIC_MAPPING_PROVEN is False
    assert RECONSTRUCTION_ALGEBRA_COMPLETE is False
    assert KIND_SET_RESOLVED is False
    assert KIND_SET_UPLIFT_THIS_WORKPACKAGE is False
    assert NON_EQ_EQUITY_STOCK_SOURCE_KIND_STATUS == "NONE_INSUFFICIENT_NO_RATIFIABLE_KIND"
    assert RATIFIED_NON_EQ_EQUITY_STOCK_SOURCE_KINDS == ()
    assert RATIFIED_SOURCE_KIND_SET == ()
    assert SOURCE_KIND_COMPLETENESS_STATUS == "INSUFFICIENT_UNPROVEN"
    assert SOURCE_KIND_COMPLETENESS_RATIFICATION == "INSUFFICIENT_NOT_KIND_SET_CLOSURE"
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
        "NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING"
    )


def test_wrong_owner_go_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(NonEqEquityStockSourceKindOrCompletenessError, match="OWNER_GO_MISMATCH"):
        execute_non_eq_equity_stock_source_kind_or_completeness_v1(
            owner_go="WRONG",
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            evidence_root=tmp_path / "pack",
        )


def test_wrong_origin_sha_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(
        NonEqEquityStockSourceKindOrCompletenessError,
        match="ORIGIN_MAIN_SHA_MISMATCH",
    ):
        execute_non_eq_equity_stock_source_kind_or_completeness_v1(
            owner_go=OWNER_GO,
            origin_main_sha="deadbeef",
            evidence_root=tmp_path / "pack",
        )


def test_eq_is_not_source_authority() -> None:
    reject_eq_as_source_authority_v1(claimed="false")
    for claimed in ("true", "SOURCE", "RAW_EQ_SOURCE_AUTHORITY"):
        with pytest.raises(
            Exception,
            match="EQ_IS_RECONCILIATION_TARGET_NOT_SOURCE",
        ):
            reject_eq_as_source_authority_v1(claimed=claimed)


def test_today_is_not_account_equity_source_kind() -> None:
    reject_today_as_account_equity_source_kind_v1(claimed=STATUS_NOT_RATIFIABLE_LIVE_TODAY)
    for claimed in (TODAY_SOURCE_KIND, "RATIFIED_SOURCE_KIND", OUTCOME_INCLUDE):
        with pytest.raises(
            NonEqEquityStockSourceKindOrCompletenessError,
            match="LIVE_TODAY_STOCK_IS_NOT_ACCOUNT_EQUITY_SOURCE_KIND",
        ):
            reject_today_as_account_equity_source_kind_v1(claimed=claimed)


def test_kind_set_uplift_forbidden() -> None:
    reject_kind_set_uplift_v1(claimed="false")
    for claimed in ("true", "RESOLVED", "KIND_SET_RESOLVED_TRUE"):
        with pytest.raises(
            NonEqEquityStockSourceKindOrCompletenessError,
            match="KIND_SET_UPLIFT_FORBIDDEN",
        ):
            reject_kind_set_uplift_v1(claimed=claimed)


def test_empty_remaining_and_single_kind_are_not_completeness() -> None:
    reject_empty_productive_remaining_as_completeness_v1(claimed="INSUFFICIENT_UNPROVEN")
    reject_single_kind_as_completeness_v1(claimed="INSUFFICIENT_UNPROVEN")
    for claimed in ("COMPLETE", "PROVEN", "true"):
        with pytest.raises(
            NonEqEquityStockSourceKindOrCompletenessError,
            match="EMPTY_PRODUCTIVE_REMAINING_IS_NOT_COMPLETENESS",
        ):
            reject_empty_productive_remaining_as_completeness_v1(claimed=claimed)
        with pytest.raises(
            NonEqEquityStockSourceKindOrCompletenessError,
            match="SINGLE_KIND_DOES_NOT_PROVE_COMPLETENESS",
        ):
            reject_single_kind_as_completeness_v1(claimed=claimed)


def test_u04_cannot_be_reclassified_as_equity_stock_kind() -> None:
    reject_u04_reclassify_as_equity_stock_kind_v1(claimed=DISPOSITION_NOT_EQUITY_STOCK)
    with pytest.raises(
        RemainingNecessaryKindEvidenceClassificationError,
        match="U04_RECLASSIFY_AS_EQUITY_STOCK_KIND_FORBIDDEN",
    ):
        reject_u04_reclassify_as_equity_stock_kind_v1(claimed=OUTCOME_INCLUDE)


def test_execute_ratifies_insufficiency_without_kind_or_uplift(tmp_path: Path) -> None:
    result = _execute(tmp_path)
    claims = json.loads((tmp_path / "pack" / "claims.json").read_text(encoding="utf-8"))
    source = json.loads((tmp_path / "pack" / "qualification_v1.json").read_text(encoding="utf-8"))
    completeness = json.loads(
        (tmp_path / "pack" / "completeness_v1.json").read_text(encoding="utf-8")
    )
    census = json.loads((tmp_path / "pack" / "census_v1.json").read_text(encoding="utf-8"))
    assert result.non_eq_equity_stock_source_kind_status == ("NONE_INSUFFICIENT_NO_RATIFIABLE_KIND")
    assert result.ratified_source_kinds == "NONE"
    assert result.source_kind_completeness_status == "INSUFFICIENT_UNPROVEN"
    assert result.kind_set_resolved == "false"
    assert result.canonically_valid_account_equity_source_mapping == "false"
    assert result.reconciliation_target_status == "EQ_RECONCILIATION_TARGET_ONLY"
    assert claims["KIND_SET_RESOLVED"] == "false"
    assert claims["KIND_SET_UPLIFT_THIS_WORKPACKAGE"] == "false"
    assert claims["EQ_TREATED_AS_SOURCE_THIS_WORKPACKAGE"] == "false"
    assert claims["RATIFIED_SOURCE_KINDS"] == "NONE"
    assert claims["U04_LEGACY_STATUS"] == "UNRESOLVED"
    assert claims["U04_EQUITY_STOCK_ROLE"] == DISPOSITION_NOT_EQUITY_STOCK
    assert claims["TODAY_SOURCE_KIND_STATUS"] == STATUS_NOT_RATIFIABLE_LIVE_TODAY
    assert source["ratified_source_kinds"] == "NONE"
    assert completeness["source_kind_completeness_ratification"] == (
        "INSUFFICIENT_NOT_KIND_SET_CLOSURE"
    )
    assert completeness["single_kind_would_not_prove_completeness"] == "true"
    assert all(row["ratification_status"] != "RATIFIED_SOURCE_KIND" for row in census["candidates"])
    assert any(row["candidate_id"] == "eq" for row in census["candidates"])
    assert any(row["candidate_id"] == TODAY_SOURCE_KIND for row in census["candidates"])
    eq_row = next(row for row in census["candidates"] if row["candidate_id"] == "eq")
    assert eq_row["ratification_status"] == STATUS_NOT_RATIFIABLE_EQ_TARGET
    assert verify_manifest_sha256_v1(store_root=tmp_path / "pack") == 0
    assert OUTCOME_EXCLUDE not in claims["NON_EQ_EQUITY_STOCK_SOURCE_KIND_STATUS"]


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
    assert claims["NON_EQ_EQUITY_STOCK_SOURCE_KIND_STATUS"] == (
        "NONE_INSUFFICIENT_NO_RATIFIABLE_KIND"
    )
    assert claims["RATIFIED_SOURCE_KINDS"] == "NONE"
    assert claims["SOURCE_KIND_EVIDENCE"] == SOURCE_KIND_EVIDENCE
    assert claims["COMPLETENESS_EVIDENCE"] == COMPLETENESS_EVIDENCE
    assert claims["SOURCE_KIND_COMPLETENESS_STATUS"] == "INSUFFICIENT_UNPROVEN"
    assert claims["KIND_SET"] == "EMPTY_FAIL_CLOSED"
    assert claims["KIND_SET_RESOLVED"] == "false"
    assert claims["CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING"] == "false"
    assert claims["RECONCILIATION_TARGET_STATUS"] == "EQ_RECONCILIATION_TARGET_ONLY"
    assert claims["U04_STATUS"] == "UNRESOLVED"
    assert claims["U04_EQUITY_STOCK_ROLE"] == DISPOSITION_NOT_EQUITY_STOCK
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


def test_runbook_cp_persists_insufficiency() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    mot = MOT_PATH.read_text(encoding="utf-8")
    atlas = ATLAS_PATH.read_text(encoding="utf-8")
    runbook = RUNBOOK.read_text(encoding="utf-8")
    start = runbook.index(CP_HEADING)
    cp_section = runbook[start : runbook.index("## 11.3 Autonomy state model", start)]
    assert OWNER_GO in cp_section
    assert PIN_OWNER_GO in cp_section
    assert (
        "THIS_SLICE=11.2.1.CP.FULL_CORE_NON_EQ_EQUITY_STOCK_SOURCE_KIND_OR_COMPLETENESS"
    ) in cp_section
    assert "NON_EQ_EQUITY_STOCK_SOURCE_KIND_STATUS=NONE_INSUFFICIENT_NO_RATIFIABLE_KIND" in (
        cp_section
    )
    assert "RATIFIED_SOURCE_KINDS=NONE" in cp_section
    assert "SOURCE_KIND_COMPLETENESS_STATUS=INSUFFICIENT_UNPROVEN" in cp_section
    assert "KIND_SET=EMPTY_FAIL_CLOSED" in cp_section
    assert "KIND_SET_RESOLVED=false" in cp_section
    assert "KIND_SET_UPLIFT_THIS_WORKPACKAGE=false" in cp_section
    assert "EQ_TREATED_AS_SOURCE_THIS_WORKPACKAGE=false" in cp_section
    assert "CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING=false" in cp_section
    assert "RECONCILIATION_TARGET_STATUS=EQ_RECONCILIATION_TARGET_ONLY" in cp_section
    assert "U04_LEGACY_STATUS=UNRESOLVED" in cp_section
    assert "U04_EQUITY_STOCK_ROLE=NOT_EQUITY_STOCK_AFFECTING" in cp_section
    assert "U05_LEGACY_STATUS=REMAIN_UNKNOWN" in cp_section
    assert "U06_LEGACY_STATUS=REMAIN_UNKNOWN" in cp_section
    assert "RESIDUAL_LEGACY_STATUS=REMAIN_UNKNOWN" in cp_section
    assert "DURABLE_UNKNOWN_NOT_INCLUDE=true" in cp_section
    assert "DURABLE_UNKNOWN_NOT_EXCLUDE=true" in cp_section
    assert "NO_GET_REQUIRED=true" in cp_section
    assert "ACTUAL_GET_COUNT=0" in cp_section
    assert "FIRST_DEFINITIVE_BLOCK=NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING" in (
        cp_section
    )
    assert EXACT_MISSING_PREDICATE in cp_section
    assert BLOCKER_ID in cp_section
    assert NEXT_OWNER_GO in cp_section
    assert NEXT_PRODUCTIVE_NODE in cp_section
    assert NEXT_ACTION in cp_section
    assert "CURRENT_CANONICAL_SECTION=11.2.1.CP" in cp_section
    assert "ATLAS_AUTHORITY=NONE" in cp_section
    assert "DOCS_TOKEN_FULL_CORE_NON_EQ_EQUITY_STOCK_SOURCE_KIND_OR_COMPLETENESS_V1" in spec
    assert "FULL_CORE_NON_EQ_EQUITY_STOCK_SOURCE_KIND_OR_COMPLETENESS_V1.md" in mot
    assert CP_HEADING in mot
    assert "11.2.1.CP" in atlas
    assert "non_eq_equity_stock_source_kind_or_completeness_v1.py" in atlas
    assert "ATLAS_AUTHORITY=NONE" in atlas
