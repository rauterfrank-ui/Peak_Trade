"""KIND_SET / mapping architecture ratification tests.

No GET. No POST. No Hope-GET. DURABLE_UNKNOWN is not INCLUDE or EXCLUDE.
Canonical mapping validity is not redefined. U05/U06/residual remain
REMAIN_UNKNOWN. Reconstruction remains incomplete.
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
from src.ops.governed_productive_account_equity_authority_producer_v1.kind_set_and_account_equity_source_mapping_architecture_ratification_v1 import (
    BLOCKER_ID,
    CANONICAL_PACK_RELPATH,
    COMPLETE_REQUIRES,
    EXACT_MISSING_PREDICATE,
    EXPECTED_ORIGIN_MAIN_SHA,
    NEXT_ACTION,
    NEXT_OWNER_GO,
    NEXT_PRODUCTIVE_NODE,
    OWNER_GO,
    PARENT_BLOCKER_ID,
    PIN_OWNER_GO,
    RATIFIED_MAPPING_ARCHITECTURE,
    VERDICT_A,
    VERDICT_B,
    VERDICT_C,
    VERDICT_D,
    KindSetAndAccountEquitySourceMappingArchitectureRatificationError,
    adjudicate_candidate_architectures_v1,
    execute_kind_set_and_account_equity_source_mapping_architecture_ratification_v1,
    reject_durable_unknown_as_kind_include_or_exclude_v1,
    reject_kind_set_resolved_while_remaining_unknown_v1,
    reject_mapping_validity_redefinition_v1,
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
from src.ops.governed_productive_account_equity_authority_producer_v1.u06_paired_fee_event_and_once_only_equity_stock_effect_primary_proof_surface_binding_v1 import (
    reject_hope_get_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = (
    "src/ops/governed_productive_account_equity_authority_producer_v1/"
    "kind_set_and_account_equity_source_mapping_architecture_ratification_v1.py"
)
SPEC_PATH = (
    REPO_ROOT
    / "docs/ops/specs/"
    / "FULL_CORE_KIND_SET_AND_ACCOUNT_EQUITY_SOURCE_MAPPING_ARCHITECTURE_RATIFICATION_V1.md"
)
MOT_PATH = REPO_ROOT / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md"
ATLAS_PATH = REPO_ROOT / "docs/system_atlas/entities/catalog.yaml"
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
CANONICAL_PACK = REPO_ROOT / CANONICAL_PACK_RELPATH
CJ_HEADING = (
    "11.2.1.CJ FULL_CORE_KIND_SET_AND_ACCOUNT_EQUITY_SOURCE_MAPPING_ARCHITECTURE_RATIFICATION"
)
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
    assert MAPPING_PROVEN is True
    assert SEMANTIC_MAPPING_PROVEN is False
    assert RECONSTRUCTION_ALGEBRA_COMPLETE is False
    assert U05_KIND_DECISION == DECISION_REMAIN_UNKNOWN
    assert U06_KIND_DECISION == DECISION_REMAIN_UNKNOWN
    assert RESIDUAL_KIND_DECISION == DECISION_REMAIN_UNKNOWN
    assert EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY == (
        "TRUSTED_29P_PRETRADE_LIVE_ACCOUNT_BOUND_AND_INSTRUMENT_SCOPE_OWNER_GOS"
    )
    assert "U04_PENDING_ORDER_RESERVATION_INCLUSION_UNRESOLVED" in UNRESOLVED_ALGEBRA_TERMS
    assert "U05_LIABILITY_INCLUSION_OR_VALUE_UNRESOLVED" in UNRESOLVED_ALGEBRA_TERMS
    assert "U06_FEE_INCLUSION_UNRESOLVED" in UNRESOLVED_ALGEBRA_TERMS


def test_wrong_owner_go_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(
        KindSetAndAccountEquitySourceMappingArchitectureRatificationError,
        match="OWNER_GO_MISMATCH",
    ):
        execute_kind_set_and_account_equity_source_mapping_architecture_ratification_v1(
            owner_go="WRONG",
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            evidence_root=tmp_path / "pack",
        )


def test_wrong_origin_sha_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(
        KindSetAndAccountEquitySourceMappingArchitectureRatificationError,
        match="ORIGIN_MAIN_SHA_MISMATCH",
    ):
        execute_kind_set_and_account_equity_source_mapping_architecture_ratification_v1(
            owner_go=OWNER_GO,
            origin_main_sha="deadbeef",
            evidence_root=tmp_path / "pack",
        )


def test_durable_unknown_is_not_include_or_exclude() -> None:
    reject_durable_unknown_as_kind_include_or_exclude_v1(claimed="DURABLE_UNKNOWN")
    reject_durable_unknown_as_kind_include_or_exclude_v1(claimed=DECISION_REMAIN_UNKNOWN)
    for claimed in (OUTCOME_EXCLUDE, OUTCOME_INCLUDE, "0", "zero", "absent"):
        with pytest.raises(
            KindSetAndAccountEquitySourceMappingArchitectureRatificationError,
            match="DURABLE_UNKNOWN_IS_NOT_INCLUDE_OR_EXCLUDE",
        ):
            reject_durable_unknown_as_kind_include_or_exclude_v1(claimed=claimed)


def test_mapping_validity_must_not_be_redefined() -> None:
    reject_mapping_validity_redefinition_v1(claimed="false")
    for claimed in ("true", "VALID", "CANONICALLY_VALID", "MAPPING_VALID"):
        with pytest.raises(
            KindSetAndAccountEquitySourceMappingArchitectureRatificationError,
            match="MAPPING_VALIDITY_MUST_NOT_BE_REDEFINED",
        ):
            reject_mapping_validity_redefinition_v1(claimed=claimed)


def test_kind_set_cannot_resolve_while_remaining_unknown() -> None:
    reject_kind_set_resolved_while_remaining_unknown_v1(claimed="false")
    with pytest.raises(
        KindSetAndAccountEquitySourceMappingArchitectureRatificationError,
        match="KIND_SET_CANNOT_RESOLVE_WHILE_REMAINING_UNKNOWN",
    ):
        reject_kind_set_resolved_while_remaining_unknown_v1(claimed="true")


def test_hope_get_forbidden() -> None:
    reject_hope_get_v1(authorized_get_count="0", actual_get_count="0")
    with pytest.raises(Exception, match="HOPE_GET_FORBIDDEN"):
        reject_hope_get_v1(authorized_get_count="1", actual_get_count="0")


def test_candidate_architectures_are_adjudicated_not_assumed() -> None:
    result = adjudicate_candidate_architectures_v1()
    assert result["candidate_a_verdict"] == VERDICT_A
    assert result["candidate_b_verdict"] == VERDICT_B
    assert result["candidate_c_verdict"] == VERDICT_C
    assert result["candidate_d_verdict"] == VERDICT_D
    assert result["ratified_mapping_architecture"] == RATIFIED_MAPPING_ARCHITECTURE
    assert result["mapping_validity_redefined"] == "false"
    assert result["kind_set_resolved"] == "false"
    assert result["canonically_valid_account_equity_source_mapping"] == "false"
    assert "REJECTED_AS_CURRENT_CANONICAL_VALIDITY" in result["candidate_a_verdict"]
    assert "CONDITION_CURRENTLY_UNSATISFIED" in result["candidate_b_verdict"]
    assert "WITHOUT_VALIDITY_CLAIM" in result["candidate_c_verdict"]
    assert "IMPOSSIBLE_ON_CURRENT_EVIDENCE" in result["candidate_d_verdict"]


def test_execute_ratifies_fail_closed_architecture_without_validity(tmp_path: Path) -> None:
    store = tmp_path / "pack"
    result = execute_kind_set_and_account_equity_source_mapping_architecture_ratification_v1(
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        evidence_root=store,
    )
    claims = json.loads((store / "claims.json").read_text(encoding="utf-8"))
    candidates = json.loads(
        (store / "candidate_architecture_adjudication_v1.json").read_text(encoding="utf-8")
    )
    states = json.loads(
        (store / "known_vs_unknown_mapping_states_v1.json").read_text(encoding="utf-8")
    )
    reconstruction = json.loads(
        (store / "reconstruction_and_downstream_readiness_v1.json").read_text(encoding="utf-8")
    )
    tree = json.loads((store / "downstream_dependency_tree_v1.json").read_text(encoding="utf-8"))
    assert result.ratified_mapping_architecture == RATIFIED_MAPPING_ARCHITECTURE
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
    assert claims["CANDIDATE_A_VERDICT"] == VERDICT_A
    assert claims["CANDIDATE_B_VERDICT"] == VERDICT_B
    assert claims["CANDIDATE_C_VERDICT"] == VERDICT_C
    assert claims["CANDIDATE_D_VERDICT"] == VERDICT_D
    assert claims["COMPLETE_REQUIRES"] == COMPLETE_REQUIRES
    assert claims["MAPPING_VALIDITY_REDEFINED"] == "false"
    assert claims["KIND_SET"] == "EMPTY_FAIL_CLOSED"
    assert claims["KIND_SET_RESOLVED"] == "false"
    assert claims["CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING"] == "false"
    assert claims["U05_STATUS"] == DECISION_REMAIN_UNKNOWN
    assert claims["U06_STATUS"] == DECISION_REMAIN_UNKNOWN
    assert claims["RESIDUAL_STATUS"] == DECISION_REMAIN_UNKNOWN
    assert claims["U05_EMBEDDING_IDENTITY"] == "DURABLE_UNKNOWN"
    assert claims["U06_PLACEMENT_IDENTITY"] == "DURABLE_UNKNOWN"
    assert claims["RESIDUAL_EXHAUSTIVENESS_IDENTITY"] == "DURABLE_UNKNOWN"
    assert claims["DURABLE_UNKNOWN_NOT_INCLUDE"] == "true"
    assert claims["DURABLE_UNKNOWN_NOT_EXCLUDE"] == "true"
    assert claims["KNOWN_INCLUDED_EQUITY_STOCK_SOURCE_KINDS"] == "NONE"
    assert claims["KNOWN_NON_SOURCE_FIELD_MAPPING_IS_NOT_KIND_EXCLUDE"] == "true"
    assert claims["U04_STATUS"] == "UNRESOLVED"
    assert claims["U04_NOT_PINNED_DURABLE_UNKNOWN"] == "true"
    assert claims["RECONSTRUCTION_ALGEBRA_COMPLETE"] == "false"
    assert "NOT_READY" in claims["EQUITY_STOCK_READINESS"]
    assert "NOT_READY" in claims["RISK_SIZING_READINESS"]
    assert claims["ACTUAL_GET_COUNT"] == "0"
    assert claims["POST_COUNT"] == "0"
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
    assert candidates["candidate_c_verdict"] == VERDICT_C
    assert states["known_included_count"] == "0"
    assert states["durable_unknown_is_not_include"] == "true"
    assert reconstruction["residual_is_not_an_algebra_term"] == "true"
    assert reconstruction["local_reconstruction_advancement_possible"] == "false"
    assert tree["first_definitive_block"] == ("NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING")
    assert tree["exact_missing_predicate"] == EXACT_MISSING_PREDICATE
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
    assert claims["RATIFIED_MAPPING_ARCHITECTURE"] == RATIFIED_MAPPING_ARCHITECTURE
    assert claims["KIND_SET"] == "EMPTY_FAIL_CLOSED"
    assert claims["KIND_SET_RESOLVED"] == "false"
    assert claims["CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING"] == "false"
    assert claims["MAPPING_VALIDITY_REDEFINED"] == "false"
    assert claims["U05_STATUS"] == DECISION_REMAIN_UNKNOWN
    assert claims["U06_STATUS"] == DECISION_REMAIN_UNKNOWN
    assert claims["RESIDUAL_STATUS"] == DECISION_REMAIN_UNKNOWN
    assert claims["ACTUAL_GET_COUNT"] == "0"
    assert claims["POST_COUNT"] == "0"
    assert claims["FIRST_DEFINITIVE_BLOCK"] == (
        "NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING"
    )
    assert claims["EXACT_MISSING_PREDICATE"] == EXACT_MISSING_PREDICATE
    assert verify_manifest_sha256_v1(store_root=CANONICAL_PACK) == 0


def test_runbook_cj_persists_architecture() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    mot = MOT_PATH.read_text(encoding="utf-8")
    atlas = ATLAS_PATH.read_text(encoding="utf-8")
    runbook = RUNBOOK.read_text(encoding="utf-8")
    start = runbook.index(CJ_HEADING)
    cj_section = runbook[start : runbook.index("## 11.3 Autonomy state model", start)]
    assert OWNER_GO in cj_section
    assert PIN_OWNER_GO in cj_section
    assert (
        "THIS_SLICE=11.2.1.CJ.FULL_CORE_KIND_SET_AND_ACCOUNT_EQUITY_SOURCE_"
        "MAPPING_ARCHITECTURE_RATIFICATION"
    ) in cj_section
    assert f"RATIFIED_MAPPING_ARCHITECTURE={RATIFIED_MAPPING_ARCHITECTURE}" in cj_section
    assert "MAPPING_VALIDITY_REDEFINED=false" in cj_section
    assert "KIND_SET=EMPTY_FAIL_CLOSED" in cj_section
    assert "KIND_SET_RESOLVED=false" in cj_section
    assert "CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING=false" in cj_section
    assert "U05_STATUS=REMAIN_UNKNOWN" in cj_section
    assert "U06_STATUS=REMAIN_UNKNOWN" in cj_section
    assert "RESIDUAL_STATUS=REMAIN_UNKNOWN" in cj_section
    assert "DURABLE_UNKNOWN_NOT_INCLUDE=true" in cj_section
    assert "DURABLE_UNKNOWN_NOT_EXCLUDE=true" in cj_section
    assert "NO_GET_REQUIRED=true" in cj_section
    assert "NO_HOPE_GET=true" in cj_section
    assert "ACTUAL_GET_COUNT=0" in cj_section
    assert "FIRST_DEFINITIVE_BLOCK=NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING" in cj_section
    assert "LOCAL_ADVANCEMENT_EXHAUSTED=true" in cj_section
    assert COMPLETE_REQUIRES in cj_section
    assert EXACT_MISSING_PREDICATE in cj_section
    assert BLOCKER_ID in cj_section
    assert PARENT_BLOCKER_ID in cj_section
    assert NEXT_OWNER_GO in cj_section
    assert NEXT_PRODUCTIVE_NODE in cj_section
    assert "CURRENT_CANONICAL_SECTION=11.2.1.CJ" in cj_section
    assert (
        "DOCS_TOKEN_FULL_CORE_KIND_SET_AND_ACCOUNT_EQUITY_SOURCE_MAPPING_"
        "ARCHITECTURE_RATIFICATION_V1"
    ) in spec
    assert (
        "FULL_CORE_KIND_SET_AND_ACCOUNT_EQUITY_SOURCE_MAPPING_ARCHITECTURE_RATIFICATION_V1.md"
    ) in mot
    assert CJ_HEADING in mot
    assert "11.2.1.CJ" in atlas
    assert "kind_set_and_account_equity_source_mapping_architecture_ratification_v1.py" in atlas
    assert "ATLAS_AUTHORITY=NONE" in atlas
