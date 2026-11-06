"""Remaining necessary-kind evidence classification tests.

No GET. No POST. No Hope-GET. Sealed evidence only. INCLUDE/EXCLUDE only
from direct qualifying proof. DURABLE_UNKNOWN is not INCLUDE or EXCLUDE.
KIND_SET remains EMPTY_FAIL_CLOSED. Mapping remains not canonically valid.
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
    OUTCOME_NONQUALIFYING,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.classified_event_kind_set_and_source_seam_contract_v1 import (
    DISPOSITION_NOT_EQUITY_STOCK,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING,
    RAW_EQ_SOURCE_AUTHORITY,
    RECONSTRUCTION_ALGEBRA_COMPLETE,
    RESIDUAL_KIND_DECISION,
    SEMANTIC_MAPPING_PROVEN,
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
    UNRESOLVED_ALGEBRA_TERMS,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.remaining_necessary_kind_evidence_classification_v1 import (
    BLOCKER_ID,
    CANONICAL_PACK_RELPATH,
    DECISION_MATRIX_RESULT,
    EXACT_MISSING_PREDICATE,
    EXPECTED_ORIGIN_MAIN_SHA,
    NEXT_ACTION,
    NEXT_OWNER_GO,
    NEXT_PRODUCTIVE_NODE,
    OWNER_GO,
    PARENT_BLOCKER_ID,
    PIN_OWNER_GO,
    RESIDUAL_CLASSIFICATION,
    U04_CLASSIFICATION,
    U05_CLASSIFICATION,
    U06_CLASSIFICATION,
    RemainingNecessaryKindEvidenceClassificationError,
    build_decision_matrix_v1,
    classify_unknowns_from_sealed_evidence_v1,
    evaluate_read_only_get_predicates_v1,
    execute_remaining_necessary_kind_evidence_classification_v1,
    reevaluate_kind_set_and_downstream_v1,
    reject_durable_unknown_reopen_without_new_evidence_v1,
    reject_empty_none_bindable_or_get_count_zero_as_classification_v1,
    reject_kind_set_resolved_while_remaining_unknown_v1,
    reject_u04_reclassify_as_equity_stock_kind_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.u06_paired_fee_event_and_once_only_equity_stock_effect_primary_proof_surface_binding_v1 import (
    reject_hope_get_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = (
    "src/ops/governed_productive_account_equity_authority_producer_v1/"
    "remaining_necessary_kind_evidence_classification_v1.py"
)
SPEC_PATH = (
    REPO_ROOT
    / "docs/ops/specs/"
    / "FULL_CORE_REMAINING_NECESSARY_KIND_EVIDENCE_CLASSIFICATION_V1.md"
)
MOT_PATH = REPO_ROOT / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md"
ATLAS_PATH = REPO_ROOT / "docs/system_atlas/entities/catalog.yaml"
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
CANONICAL_PACK = REPO_ROOT / CANONICAL_PACK_RELPATH
CK_HEADING = "11.2.1.CK FULL_CORE_REMAINING_NECESSARY_KIND_EVIDENCE_CLASSIFICATION"
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
    assert CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING is True
    assert MAPPING_PROVEN is False
    assert SEMANTIC_MAPPING_PROVEN is False
    assert RECONSTRUCTION_ALGEBRA_COMPLETE is False
    assert U05_KIND_DECISION == DECISION_REMAIN_UNKNOWN
    assert U06_KIND_DECISION == DECISION_REMAIN_UNKNOWN
    assert RESIDUAL_KIND_DECISION == DECISION_REMAIN_UNKNOWN
    assert EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY == (
        "CURRENT_PRODUCTIVE_29P_RISK_CAPITAL_SURFACE_BOUND_VALUE_REQUIRES_FRESH_TRUSTED_GET"
    )
    assert "U04_PENDING_ORDER_RESERVATION_INCLUSION_UNRESOLVED" in UNRESOLVED_ALGEBRA_TERMS
    assert "U05_LIABILITY_INCLUSION_OR_VALUE_UNRESOLVED" in UNRESOLVED_ALGEBRA_TERMS
    assert "U06_FEE_INCLUSION_UNRESOLVED" in UNRESOLVED_ALGEBRA_TERMS


def test_wrong_owner_go_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(
        RemainingNecessaryKindEvidenceClassificationError,
        match="OWNER_GO_MISMATCH",
    ):
        execute_remaining_necessary_kind_evidence_classification_v1(
            owner_go="WRONG",
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            evidence_root=tmp_path / "pack",
        )


def test_wrong_origin_sha_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(
        RemainingNecessaryKindEvidenceClassificationError,
        match="ORIGIN_MAIN_SHA_MISMATCH",
    ):
        execute_remaining_necessary_kind_evidence_classification_v1(
            owner_go=OWNER_GO,
            origin_main_sha="deadbeef",
            evidence_root=tmp_path / "pack",
        )


def test_empty_none_bindable_get_count_zero_is_not_include_or_exclude() -> None:
    reject_empty_none_bindable_or_get_count_zero_as_classification_v1(
        claimed=DECISION_REMAIN_UNKNOWN
    )
    for claimed in (OUTCOME_EXCLUDE, OUTCOME_INCLUDE, "0", "zero", "absent", "NONE"):
        with pytest.raises(
            RemainingNecessaryKindEvidenceClassificationError,
            match="EMPTY_NONE_BINDABLE_GET_COUNT_ZERO_IS_NOT_INCLUDE_OR_EXCLUDE",
        ):
            reject_empty_none_bindable_or_get_count_zero_as_classification_v1(claimed=claimed)


def test_durable_unknown_may_not_reopen_without_new_evidence() -> None:
    reject_durable_unknown_reopen_without_new_evidence_v1(claimed_new_evidence="false")
    with pytest.raises(
        RemainingNecessaryKindEvidenceClassificationError,
        match="DURABLE_UNKNOWN_REOPEN_REQUIRES_NEW_DISCRIMINATING_EVIDENCE",
    ):
        reject_durable_unknown_reopen_without_new_evidence_v1(claimed_new_evidence=OUTCOME_INCLUDE)


def test_kind_set_cannot_resolve_while_remaining_unknown() -> None:
    reject_kind_set_resolved_while_remaining_unknown_v1(claimed="false")
    with pytest.raises(
        RemainingNecessaryKindEvidenceClassificationError,
        match="KIND_SET_CANNOT_RESOLVE_WHILE_REMAINING_UNKNOWN",
    ):
        reject_kind_set_resolved_while_remaining_unknown_v1(claimed="true")


def test_u04_cannot_reclassify_as_equity_stock_kind() -> None:
    reject_u04_reclassify_as_equity_stock_kind_v1(claimed=DISPOSITION_NOT_EQUITY_STOCK)
    with pytest.raises(
        RemainingNecessaryKindEvidenceClassificationError,
        match="U04_RECLASSIFY_AS_EQUITY_STOCK_KIND_FORBIDDEN",
    ):
        reject_u04_reclassify_as_equity_stock_kind_v1(claimed=OUTCOME_INCLUDE)


def test_hope_get_forbidden() -> None:
    reject_hope_get_v1(authorized_get_count="0", actual_get_count="0")
    with pytest.raises(Exception, match="HOPE_GET_FORBIDDEN"):
        reject_hope_get_v1(authorized_get_count="1", actual_get_count="0")


def test_get_predicates_fail_closed_for_all_unknowns() -> None:
    result = evaluate_read_only_get_predicates_v1()
    assert result["any_get_authorized"] == "false"
    assert result["venue_get_count"] == "0"
    by_id = {row["unknown_id"]: row for row in result["records"]}
    for unknown_id in ("U04", "U05", "U06", "RESIDUAL"):
        assert by_id[unknown_id]["all_predicates_proven"] == "false"
        assert by_id[unknown_id]["get_authorized"] == "false"
        assert by_id[unknown_id]["result_can_discriminate_named_include_vs_exclude"] == "false"


def test_sealed_evidence_classifications_are_not_include_or_exclude() -> None:
    result = classify_unknowns_from_sealed_evidence_v1()
    assert result["u04_classification"] == U04_CLASSIFICATION
    assert result["u05_classification"] == U05_CLASSIFICATION
    assert result["u06_classification"] == U06_CLASSIFICATION
    assert result["residual_classification"] == RESIDUAL_CLASSIFICATION
    assert result["u04_kind_set_disposition"] == DISPOSITION_NOT_EQUITY_STOCK
    assert result["u04_algebra_inclusion"] == "UNRESOLVED"
    assert result["u05_bj_cd_outcome"] == OUTCOME_NONQUALIFYING
    assert result["u06_bj_cf_outcome"] == OUTCOME_NONQUALIFYING
    assert result["residual_bj_ch_outcome"] == OUTCOME_NONQUALIFYING
    assert result["u05_include_proven"] == "false"
    assert result["u05_exclude_proven"] == "false"
    assert result["u06_include_proven"] == "false"
    assert result["u06_exclude_proven"] == "false"
    assert result["residual_include_proven"] == "false"
    assert result["residual_exclude_proven"] == "false"
    assert result["u05_durable_unknown_reopened"] == "false"
    assert result["new_evidence_acquired"] == "false"
    assert result["decision_matrix_result"] == DECISION_MATRIX_RESULT


def test_decision_matrix_covers_all_four_unknowns() -> None:
    matrix = build_decision_matrix_v1()
    assert matrix["include_or_exclude_proven_count"] == "0"
    ids = [row["unknown_id"] for row in matrix["records"]]
    assert ids == ["U04", "U05", "U06", "RESIDUAL"]
    for row in matrix["records"]:
        assert row["existing_surface_can_discriminate"] == "false"
        assert row["acquisition_already_authorized"] == "false"
        assert row["result_would_be_decision_capable"] == "false"
        assert row["classification"] not in {OUTCOME_INCLUDE, OUTCOME_EXCLUDE, "INCLUDE", "EXCLUDE"}


def test_downstream_cannot_advance_without_include_or_exclude() -> None:
    tree = reevaluate_kind_set_and_downstream_v1()
    assert tree["kind_set"] == "EMPTY_FAIL_CLOSED"
    assert tree["kind_set_resolved"] == "false"
    assert tree["kind_set_closure_provable"] == "false"
    assert tree["canonically_valid_account_equity_source_mapping"] == "false"
    assert tree["reconstruction_algebra_complete"] == "false"
    assert "NOT_READY" in tree["equity_stock_readiness"]
    assert "UNBOUND" in tree["running_account_equity_available_for_sizing_status"]
    assert "NOT_READY" in tree["risk_sizing_readiness"]
    assert tree["local_advancement_exhausted"] == "true"
    assert tree["first_definitive_block"] == ("NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING")
    assert tree["exact_missing_predicate"] == EXACT_MISSING_PREDICATE
    assert tree["next_productive_node"] == NEXT_PRODUCTIVE_NODE


def test_execute_classifies_fail_closed_without_get(tmp_path: Path) -> None:
    store = tmp_path / "pack"
    result = execute_remaining_necessary_kind_evidence_classification_v1(
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        evidence_root=store,
    )
    claims = json.loads((store / "claims.json").read_text(encoding="utf-8"))
    matrix = json.loads((store / "decision_matrix_v1.json").read_text(encoding="utf-8"))
    proofs = json.loads((store / "classification_proofs_v1.json").read_text(encoding="utf-8"))
    tree = json.loads((store / "downstream_dependency_tree_v1.json").read_text(encoding="utf-8"))
    assert result.u04_classification == U04_CLASSIFICATION
    assert result.u05_classification == U05_CLASSIFICATION
    assert result.u06_classification == U06_CLASSIFICATION
    assert result.residual_classification == RESIDUAL_CLASSIFICATION
    assert result.decision_matrix_result == DECISION_MATRIX_RESULT
    assert result.kind_set == "EMPTY_FAIL_CLOSED"
    assert result.kind_set_resolved == "false"
    assert result.canonically_valid_account_equity_source_mapping == "false"
    assert result.first_definitive_block == ("NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING")
    assert result.exact_missing_predicate == EXACT_MISSING_PREDICATE
    assert result.authorized_get_count == "0"
    assert result.actual_get_count == "0"
    assert result.post_count == "0"
    assert claims["OWNER_GO"] == OWNER_GO
    assert claims["PIN_OWNER_GO"] == PIN_OWNER_GO
    assert claims["PIN_OWNER_GO_STATUS"] == "SATISFIED_BY_WORKPACKAGE"
    assert claims["U04_STATUS"] == "UNRESOLVED"
    assert claims["U04_KIND_SET_DISPOSITION"] == DISPOSITION_NOT_EQUITY_STOCK
    assert claims["U04_CLASSIFICATION"] == U04_CLASSIFICATION
    assert claims["U05_STATUS"] == DECISION_REMAIN_UNKNOWN
    assert claims["U06_STATUS"] == DECISION_REMAIN_UNKNOWN
    assert claims["RESIDUAL_STATUS"] == DECISION_REMAIN_UNKNOWN
    assert claims["U05_CLASSIFICATION"] == U05_CLASSIFICATION
    assert claims["U06_CLASSIFICATION"] == U06_CLASSIFICATION
    assert claims["RESIDUAL_CLASSIFICATION"] == RESIDUAL_CLASSIFICATION
    assert claims["U05_EMBEDDING_IDENTITY"] == "DURABLE_UNKNOWN"
    assert claims["U06_PLACEMENT_IDENTITY"] == "DURABLE_UNKNOWN"
    assert claims["RESIDUAL_EXHAUSTIVENESS_IDENTITY"] == "DURABLE_UNKNOWN"
    assert claims["DURABLE_UNKNOWN_NOT_INCLUDE"] == "true"
    assert claims["DURABLE_UNKNOWN_NOT_EXCLUDE"] == "true"
    assert claims["DECISION_MATRIX_RESULT"] == DECISION_MATRIX_RESULT
    assert claims["NEW_EVIDENCE_ACQUIRED"] == "false"
    assert claims["KIND_SET"] == "EMPTY_FAIL_CLOSED"
    assert claims["KIND_SET_RESOLVED"] == "false"
    assert claims["CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING"] == "false"
    assert claims["RECONSTRUCTION_ALGEBRA_COMPLETE"] == "false"
    assert "NOT_READY" in claims["EQUITY_STOCK_READINESS"]
    assert "UNBOUND" in claims["RUNNING_ACCOUNT_EQUITY_AVAILABLE_FOR_SIZING_STATUS"]
    assert "NOT_READY" in claims["RISK_SIZING_READINESS"]
    assert claims["ACTUAL_GET_COUNT"] == "0"
    assert claims["VENUE_GET_COUNT"] == "0"
    assert claims["POST_COUNT"] == "0"
    assert claims["SECRET_RESOLUTION_STATUS"] == "NOT_ATTEMPTED"
    assert claims["FIRST_DEFINITIVE_BLOCK"] == (
        "NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING"
    )
    assert claims["LOCAL_ADVANCEMENT_EXHAUSTED"] == "true"
    assert claims["NEXT_OWNER_GO_REQUIRED"] == NEXT_OWNER_GO
    assert claims["NEXT_ACTION"] == NEXT_ACTION
    assert claims["BLOCKER_ID"] == BLOCKER_ID
    assert claims["PARENT_BLOCKER_ID"] == PARENT_BLOCKER_ID
    assert "INCLUDE" not in claims["U05_STATUS"]
    assert "EXCLUDE" not in claims["U05_STATUS"]
    assert matrix["include_or_exclude_proven_count"] == "0"
    assert proofs["u05_bj_cd_outcome"] == OUTCOME_NONQUALIFYING
    assert tree["kind_set_closure_provable"] == "false"
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
    assert claims["KIND_SET"] == "EMPTY_FAIL_CLOSED"
    assert claims["KIND_SET_RESOLVED"] == "false"
    assert claims["CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING"] == "false"
    assert claims["U04_STATUS"] == "UNRESOLVED"
    assert claims["U05_STATUS"] == DECISION_REMAIN_UNKNOWN
    assert claims["U06_STATUS"] == DECISION_REMAIN_UNKNOWN
    assert claims["RESIDUAL_STATUS"] == DECISION_REMAIN_UNKNOWN
    assert claims["DECISION_MATRIX_RESULT"] == DECISION_MATRIX_RESULT
    assert claims["ACTUAL_GET_COUNT"] == "0"
    assert claims["POST_COUNT"] == "0"
    assert claims["FIRST_DEFINITIVE_BLOCK"] == (
        "NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING"
    )
    assert claims["EXACT_MISSING_PREDICATE"] == EXACT_MISSING_PREDICATE
    assert verify_manifest_sha256_v1(store_root=CANONICAL_PACK) == 0


def test_runbook_ck_persists_classification() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    mot = MOT_PATH.read_text(encoding="utf-8")
    atlas = ATLAS_PATH.read_text(encoding="utf-8")
    runbook = RUNBOOK.read_text(encoding="utf-8")
    start = runbook.index(CK_HEADING)
    ck_section = runbook[start : runbook.index("## 11.3 Autonomy state model", start)]
    assert OWNER_GO in ck_section
    assert PIN_OWNER_GO in ck_section
    assert (
        "THIS_SLICE=11.2.1.CK.FULL_CORE_REMAINING_NECESSARY_KIND_EVIDENCE_CLASSIFICATION"
    ) in ck_section
    assert "KIND_SET=EMPTY_FAIL_CLOSED" in ck_section
    assert "KIND_SET_RESOLVED=false" in ck_section
    assert "CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING=false" in ck_section
    assert "U04_STATUS=UNRESOLVED" in ck_section
    assert "U05_STATUS=REMAIN_UNKNOWN" in ck_section
    assert "U06_STATUS=REMAIN_UNKNOWN" in ck_section
    assert "RESIDUAL_STATUS=REMAIN_UNKNOWN" in ck_section
    assert f"U04_CLASSIFICATION={U04_CLASSIFICATION}" in ck_section
    assert f"U05_CLASSIFICATION={U05_CLASSIFICATION}" in ck_section
    assert f"U06_CLASSIFICATION={U06_CLASSIFICATION}" in ck_section
    assert f"RESIDUAL_CLASSIFICATION={RESIDUAL_CLASSIFICATION}" in ck_section
    assert f"DECISION_MATRIX_RESULT={DECISION_MATRIX_RESULT}" in ck_section
    assert "DURABLE_UNKNOWN_NOT_INCLUDE=true" in ck_section
    assert "DURABLE_UNKNOWN_NOT_EXCLUDE=true" in ck_section
    assert "NO_GET_REQUIRED=true" in ck_section
    assert "NO_HOPE_GET=true" in ck_section
    assert "ACTUAL_GET_COUNT=0" in ck_section
    assert "VENUE_GET_COUNT=0" in ck_section
    assert "NEW_EVIDENCE_ACQUIRED=false" in ck_section
    assert "FIRST_DEFINITIVE_BLOCK=NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING" in ck_section
    assert "LOCAL_ADVANCEMENT_EXHAUSTED=true" in ck_section
    assert EXACT_MISSING_PREDICATE in ck_section
    assert BLOCKER_ID in ck_section
    assert PARENT_BLOCKER_ID in ck_section
    assert NEXT_OWNER_GO in ck_section
    assert NEXT_PRODUCTIVE_NODE in ck_section
    assert "CURRENT_CANONICAL_SECTION=11.2.1.CK" in ck_section
    assert "DOCS_TOKEN_FULL_CORE_REMAINING_NECESSARY_KIND_EVIDENCE_CLASSIFICATION_V1" in spec
    assert "FULL_CORE_REMAINING_NECESSARY_KIND_EVIDENCE_CLASSIFICATION_V1.md" in mot
    assert CK_HEADING in mot
    assert "11.2.1.CK" in atlas
    assert "remaining_necessary_kind_evidence_classification_v1.py" in atlas
    assert "ATLAS_AUTHORITY=NONE" in atlas
