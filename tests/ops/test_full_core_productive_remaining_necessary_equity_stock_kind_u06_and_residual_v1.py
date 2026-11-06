"""U06 and residual productive-scope ratification tests.

Historical U06 and residual remain UNKNOWN. Productive membership is not
EXCLUDE. No GET. No POST. KIND_SET remains EMPTY_FAIL_CLOSED. Mapping
remains not canonically valid. U04 remains UNRESOLVED.
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
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING,
    CURRENT_PRODUCTIVE_REMAINING_NECESSARY_EQUITY_STOCK_CLASSES,
    KIND_SET_RESOLVED,
    NAMED_REMAINING_UNKNOWN_NECESSARY_CLASSES,
    PRODUCTIVE_REMAINING_NECESSARY_EQUITY_STOCK_CLASSES,
    PRODUCTIVE_RESIDUAL_EQUITY_STOCK_KIND_MEMBERSHIP,
    PRODUCTIVE_U05_EQUITY_STOCK_KIND_MEMBERSHIP,
    PRODUCTIVE_U06_EQUITY_STOCK_KIND_MEMBERSHIP,
    RAW_EQ_SOURCE_AUTHORITY,
    RECONSTRUCTION_ALGEBRA_COMPLETE,
    RESIDUAL_KIND_DECISION,
    RESIDUAL_LEGACY_INCLUDE_EXCLUDE_PROOF_RETIRED_AS_PRODUCTIVE_BLOCKER,
    RESIDUAL_LEGACY_KIND_DECISION,
    SEMANTIC_MAPPING_PROVEN,
    U04_PLACEMENT,
    U05_KIND_DECISION,
    U06_KIND_DECISION,
    U06_LEGACY_INCLUDE_EXCLUDE_PROOF_RETIRED_AS_PRODUCTIVE_BLOCKER,
    U06_LEGACY_KIND_DECISION,
    U06_PLACEMENT,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.named_remaining_unknown_kind_set_evidence_persist_contract_v1 import (
    DECISION_REMAIN_UNKNOWN,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_s6_mapping_classification_v1 import (
    verify_manifest_sha256_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.productive_remaining_necessary_equity_stock_kind_u06_and_residual_v1 import (
    BLOCKER_ID,
    CANONICAL_PACK_RELPATH,
    EXACT_MISSING_PREDICATE,
    EXPECTED_ORIGIN_MAIN_SHA,
    NEXT_ACTION,
    NEXT_OWNER_GO,
    NEXT_PRODUCTIVE_NODE,
    OWNER_GO,
    PARENT_BLOCKER_ID,
    PIN_OWNER_GO,
    ProductiveRemainingU06AndResidualError,
    execute_productive_remaining_necessary_equity_stock_kind_u06_and_residual_v1,
    reject_legacy_unknown_as_include_or_exclude_v1,
    reject_productive_not_in_kind_set_as_exclude_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.reconstruction_algebra_contract_v1 import (
    EARLIEST_UNRESOLVED_ALGEBRA_TERM,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = (
    "src/ops/governed_productive_account_equity_authority_producer_v1/"
    "productive_remaining_necessary_equity_stock_kind_u06_and_residual_v1.py"
)
SPEC_PATH = (
    REPO_ROOT
    / "docs/ops/specs/"
    / "FULL_CORE_PRODUCTIVE_REMAINING_NECESSARY_EQUITY_STOCK_KIND_U06_AND_RESIDUAL_V1.md"
)
MOT_PATH = REPO_ROOT / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md"
ATLAS_PATH = REPO_ROOT / "docs/system_atlas/entities/catalog.yaml"
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
CANONICAL_PACK = REPO_ROOT / CANONICAL_PACK_RELPATH
CN_HEADING = "11.2.1.CN FULL_CORE_PRODUCTIVE_REMAINING_NECESSARY_EQUITY_STOCK_KIND_U06_AND_RESIDUAL"
FORBIDDEN_SOURCE_TOKENS = (
    "urllib",
    "requests",
    "httpx",
    "GET_ENDPOINTS_PRIVATE",
    "max_retries",
    "eq=cashBal",
)


def _execute(tmp_path: Path) -> object:
    return execute_productive_remaining_necessary_equity_stock_kind_u06_and_residual_v1(
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
    assert CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING is True
    assert MAPPING_PROVEN is False
    assert SEMANTIC_MAPPING_PROVEN is False
    assert RECONSTRUCTION_ALGEBRA_COMPLETE is False
    assert KIND_SET_RESOLVED is False
    assert U05_KIND_DECISION == DECISION_REMAIN_UNKNOWN
    assert PRODUCTIVE_U05_EQUITY_STOCK_KIND_MEMBERSHIP == "NOT_IN_CURRENT_PRODUCTIVE_KIND_SET"
    assert U06_KIND_DECISION == DECISION_REMAIN_UNKNOWN
    assert U06_LEGACY_KIND_DECISION == DECISION_REMAIN_UNKNOWN
    assert U06_LEGACY_INCLUDE_EXCLUDE_PROOF_RETIRED_AS_PRODUCTIVE_BLOCKER is True
    assert PRODUCTIVE_U06_EQUITY_STOCK_KIND_MEMBERSHIP == "NOT_IN_CURRENT_PRODUCTIVE_KIND_SET"
    assert RESIDUAL_KIND_DECISION == DECISION_REMAIN_UNKNOWN
    assert RESIDUAL_LEGACY_KIND_DECISION == DECISION_REMAIN_UNKNOWN
    assert RESIDUAL_LEGACY_INCLUDE_EXCLUDE_PROOF_RETIRED_AS_PRODUCTIVE_BLOCKER is True
    assert PRODUCTIVE_RESIDUAL_EQUITY_STOCK_KIND_MEMBERSHIP == "NOT_IN_CURRENT_PRODUCTIVE_KIND_SET"
    assert NAMED_REMAINING_UNKNOWN_NECESSARY_CLASSES == (TARGET_U05, TARGET_U06, TARGET_RESIDUAL)
    assert PRODUCTIVE_REMAINING_NECESSARY_EQUITY_STOCK_CLASSES == (TARGET_U06, TARGET_RESIDUAL)
    assert CURRENT_PRODUCTIVE_REMAINING_NECESSARY_EQUITY_STOCK_CLASSES == ()
    assert TARGET_U06 not in CURRENT_PRODUCTIVE_REMAINING_NECESSARY_EQUITY_STOCK_CLASSES
    assert TARGET_RESIDUAL not in CURRENT_PRODUCTIVE_REMAINING_NECESSARY_EQUITY_STOCK_CLASSES
    assert U06_PLACEMENT == "EVENT_OR_RECONCILIATION_NOT_BLIND_SUBTRACTION"
    assert U04_PLACEMENT == "AVAILABLE_FOR_SIZING_OR_RISK_SIZING"
    assert EARLIEST_UNRESOLVED_ALGEBRA_TERM == "U04_PENDING_ORDER_RESERVATION_INCLUSION_UNRESOLVED"
    assert EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY == (
        "CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_SURFACE_BOUND_VALUE_REQUIRES_FRESH_TRUSTED_GET"
    )


def test_wrong_owner_go_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(ProductiveRemainingU06AndResidualError, match="OWNER_GO_MISMATCH"):
        execute_productive_remaining_necessary_equity_stock_kind_u06_and_residual_v1(
            owner_go="WRONG",
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            evidence_root=tmp_path / "pack",
        )


def test_wrong_origin_sha_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(ProductiveRemainingU06AndResidualError, match="ORIGIN_MAIN_SHA_MISMATCH"):
        execute_productive_remaining_necessary_equity_stock_kind_u06_and_residual_v1(
            owner_go=OWNER_GO,
            origin_main_sha="deadbeef",
            evidence_root=tmp_path / "pack",
        )


def test_legacy_unknown_is_not_include_or_exclude() -> None:
    reject_legacy_unknown_as_include_or_exclude_v1(claimed=DECISION_REMAIN_UNKNOWN)
    for claimed in (OUTCOME_EXCLUDE, OUTCOME_INCLUDE, "0", "zero", "absent", "NONE"):
        with pytest.raises(
            ProductiveRemainingU06AndResidualError,
            match="LEGACY_UNKNOWN_IS_NOT_INCLUDE_OR_EXCLUDE",
        ):
            reject_legacy_unknown_as_include_or_exclude_v1(claimed=claimed)


def test_productive_not_in_kind_set_is_not_exclude() -> None:
    reject_productive_not_in_kind_set_as_exclude_v1(claimed="NOT_IN_CURRENT_PRODUCTIVE_KIND_SET")
    for claimed in (OUTCOME_EXCLUDE, "EXCLUDE", "IN_BASE"):
        with pytest.raises(
            ProductiveRemainingU06AndResidualError,
            match="PRODUCTIVE_NOT_IN_KIND_SET_IS_NOT_EXCLUDE",
        ):
            reject_productive_not_in_kind_set_as_exclude_v1(claimed=claimed)


def test_execute_splits_legacy_and_productive_without_mapping_or_kind_set_uplift(
    tmp_path: Path,
) -> None:
    result = _execute(tmp_path)
    claims = json.loads((tmp_path / "pack" / "claims.json").read_text(encoding="utf-8"))
    split = json.loads((tmp_path / "pack" / "qualification_v1.json").read_text(encoding="utf-8"))
    downstream = json.loads(
        (tmp_path / "pack" / "downstream_dependency_tree_v1.json").read_text(encoding="utf-8")
    )
    assert result.u06_legacy_status == DECISION_REMAIN_UNKNOWN
    assert result.u06_productive_scope_status == "NOT_IN_CURRENT_PRODUCTIVE_KIND_SET"
    assert result.residual_legacy_status == DECISION_REMAIN_UNKNOWN
    assert result.residual_productive_scope_status == "NOT_IN_CURRENT_PRODUCTIVE_KIND_SET"
    assert result.current_productive_remaining == ""
    assert result.kind_set_resolved == "false"
    assert result.canonically_valid_account_equity_source_mapping == "false"
    assert result.u04_status == "UNRESOLVED"
    assert claims["U06_INCLUDE_PROVEN"] == "false"
    assert claims["U06_EXCLUDE_PROVEN"] == "false"
    assert claims["RESIDUAL_INCLUDE_PROVEN"] == "false"
    assert claims["RESIDUAL_EXCLUDE_PROVEN"] == "false"
    assert claims["SYNTHETIC_WITNESS_USED"] == "false"
    assert claims["KIND_SET_RESOLVED"] == "false"
    assert claims["CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING"] == "false"
    assert claims["U04_STATUS"] == "UNRESOLVED"
    assert claims["PIN_OWNER_GO_STATUS"] == (
        "SATISFIED_BY_PRODUCTIVE_SCOPE_RATIFICATION_NOT_INCLUDE_OR_EXCLUDE"
    )
    assert split["u06_bj_outcome"] not in {OUTCOME_INCLUDE, OUTCOME_EXCLUDE}
    assert split["residual_bj_outcome"] not in {OUTCOME_INCLUDE, OUTCOME_EXCLUDE}
    assert TARGET_U06 in downstream["cm_era_productive_remaining_necessary_equity_stock_classes"]
    assert (
        TARGET_RESIDUAL in downstream["cm_era_productive_remaining_necessary_equity_stock_classes"]
    )
    assert downstream["current_productive_remaining_necessary_equity_stock_classes"] == ""
    assert (
        TARGET_U06 not in downstream["current_productive_remaining_necessary_equity_stock_classes"]
    )
    assert (
        TARGET_RESIDUAL
        not in downstream["current_productive_remaining_necessary_equity_stock_classes"]
    )
    assert U06_KIND_DECISION == DECISION_REMAIN_UNKNOWN
    assert RESIDUAL_KIND_DECISION == DECISION_REMAIN_UNKNOWN
    assert verify_manifest_sha256_v1(store_root=tmp_path / "pack") == 0


def test_source_does_not_get_or_post_or_uplift() -> None:
    source = (REPO_ROOT / SOURCE_PATH).read_text(encoding="utf-8")
    for token in FORBIDDEN_SOURCE_TOKENS:
        assert token not in source
    assert "cashBal+upl" not in source
    assert "PRODUCTIVE_ACQUISITION_AUTHORIZED = TRUE" not in source.upper()
    assert "KIND_SET_RESOLVED = True" not in source
    assert "CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING = True" not in source


def test_canonical_pack_sealed() -> None:
    claims = json.loads((CANONICAL_PACK / "claims.json").read_text(encoding="utf-8"))
    assert claims["OWNER_GO"] == OWNER_GO
    assert claims["U06_LEGACY_STATUS"] == DECISION_REMAIN_UNKNOWN
    assert claims["U06_PRODUCTIVE_SCOPE_STATUS"] == "NOT_IN_CURRENT_PRODUCTIVE_KIND_SET"
    assert claims["RESIDUAL_LEGACY_STATUS"] == DECISION_REMAIN_UNKNOWN
    assert claims["RESIDUAL_PRODUCTIVE_SCOPE_STATUS"] == "NOT_IN_CURRENT_PRODUCTIVE_KIND_SET"
    assert claims["CURRENT_PRODUCTIVE_REMAINING_NECESSARY_EQUITY_STOCK_CLASSES"] == ""
    assert claims["KIND_SET"] == "EMPTY_FAIL_CLOSED"
    assert claims["KIND_SET_RESOLVED"] == "false"
    assert claims["CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING"] == "false"
    assert claims["U04_STATUS"] == "UNRESOLVED"
    assert claims["U05_LEGACY_STATUS"] == DECISION_REMAIN_UNKNOWN
    assert claims["U06_STATUS"] == DECISION_REMAIN_UNKNOWN
    assert claims["RESIDUAL_STATUS"] == DECISION_REMAIN_UNKNOWN
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


def test_runbook_cn_persists_productive_scope() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    mot = MOT_PATH.read_text(encoding="utf-8")
    atlas = ATLAS_PATH.read_text(encoding="utf-8")
    runbook = RUNBOOK.read_text(encoding="utf-8")
    start = runbook.index(CN_HEADING)
    cn_section = runbook[start : runbook.index("## 11.3 Autonomy state model", start)]
    assert OWNER_GO in cn_section
    assert PIN_OWNER_GO in cn_section
    assert (
        "THIS_SLICE=11.2.1.CN.FULL_CORE_PRODUCTIVE_REMAINING_NECESSARY_EQUITY_STOCK_KIND_"
        "U06_AND_RESIDUAL"
    ) in cn_section
    assert "U06_LEGACY_STATUS=REMAIN_UNKNOWN" in cn_section
    assert "U06_PRODUCTIVE_SCOPE_STATUS=NOT_IN_CURRENT_PRODUCTIVE_KIND_SET" in cn_section
    assert "RESIDUAL_LEGACY_STATUS=REMAIN_UNKNOWN" in cn_section
    assert "RESIDUAL_PRODUCTIVE_SCOPE_STATUS=NOT_IN_CURRENT_PRODUCTIVE_KIND_SET" in cn_section
    assert "KIND_SET=EMPTY_FAIL_CLOSED" in cn_section
    assert "KIND_SET_RESOLVED=false" in cn_section
    assert "CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING=false" in cn_section
    assert "U04_STATUS=UNRESOLVED" in cn_section
    assert "U05_LEGACY_STATUS=REMAIN_UNKNOWN" in cn_section
    assert "U06_STATUS=REMAIN_UNKNOWN" in cn_section
    assert "RESIDUAL_STATUS=REMAIN_UNKNOWN" in cn_section
    assert "DURABLE_UNKNOWN_NOT_INCLUDE=true" in cn_section
    assert "DURABLE_UNKNOWN_NOT_EXCLUDE=true" in cn_section
    assert "NO_GET_REQUIRED=true" in cn_section
    assert "ACTUAL_GET_COUNT=0" in cn_section
    assert "FIRST_DEFINITIVE_BLOCK=NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING" in (
        cn_section
    )
    assert EXACT_MISSING_PREDICATE in cn_section
    assert BLOCKER_ID in cn_section
    assert NEXT_OWNER_GO in cn_section
    assert NEXT_PRODUCTIVE_NODE in cn_section
    assert NEXT_ACTION in cn_section
    assert "CURRENT_CANONICAL_SECTION=11.2.1.CN" in cn_section
    assert "ATLAS_AUTHORITY=NONE" in cn_section
    assert (
        "DOCS_TOKEN_FULL_CORE_PRODUCTIVE_REMAINING_NECESSARY_EQUITY_STOCK_KIND_U06_AND_RESIDUAL_V1"
    ) in spec
    assert (
        "FULL_CORE_PRODUCTIVE_REMAINING_NECESSARY_EQUITY_STOCK_KIND_U06_AND_RESIDUAL_V1.md"
    ) in mot
    assert CN_HEADING in mot
    assert "11.2.1.CN" in atlas
    assert "productive_remaining_necessary_equity_stock_kind_u06_and_residual_v1.py" in atlas
    assert "ATLAS_AUTHORITY=NONE" in atlas
