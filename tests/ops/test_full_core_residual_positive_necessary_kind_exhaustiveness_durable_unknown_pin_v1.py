"""PATH_B durable-UNKNOWN residual exhaustiveness pin tests.

No GET. No POST. No Hope-GET. DURABLE_UNKNOWN is not INCLUDE or EXCLUDE.
NONE_BINDABLE GET_COUNT=0 is provenance, not absence. U05/U06 remain
REMAIN_UNKNOWN. Mapping remains unprovable.
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
    OUTCOME_EXCLUDE,
    OUTCOME_INCLUDE,
    PROOF_OBJECT_RESIDUAL,
    TARGET_RESIDUAL,
    evaluate_residual_primary_proof_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING,
    RAW_EQ_SOURCE_AUTHORITY,
    RECONSTRUCTION_ALGEBRA_COMPLETE,
    RESIDUAL_KIND_DECISION,
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
from src.ops.governed_productive_account_equity_authority_producer_v1.residual_positive_necessary_kind_exhaustiveness_durable_unknown_pin_v1 import (
    BLOCKER_ID,
    CANONICAL_PACK_RELPATH,
    EXPECTED_ORIGIN_MAIN_SHA,
    NEXT_ACTION,
    NEXT_OWNER_GO,
    NEXT_PRODUCTIVE_NODE,
    OWNER_GO,
    PARENT_BLOCKER_ID,
    PIN_OWNER_GO,
    SELECTED_PATH,
    ResidualPositiveNecessaryKindExhaustivenessDurableUnknownPinError,
    execute_residual_positive_necessary_kind_exhaustiveness_durable_unknown_pin_v1,
    reject_durable_unknown_as_include_or_exclude_v1,
    reject_none_bindable_get_count_zero_as_absent_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.u06_paired_fee_event_and_once_only_equity_stock_effect_primary_proof_surface_binding_v1 import (
    reject_hope_get_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = (
    "src/ops/governed_productive_account_equity_authority_producer_v1/"
    "residual_positive_necessary_kind_exhaustiveness_durable_unknown_pin_v1.py"
)
SPEC_PATH = (
    REPO_ROOT
    / "docs/ops/specs/"
    / "FULL_CORE_RESIDUAL_POSITIVE_NECESSARY_KIND_EXHAUSTIVENESS_DURABLE_UNKNOWN_PIN_V1.md"
)
MOT_PATH = REPO_ROOT / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md"
ATLAS_PATH = REPO_ROOT / "docs/system_atlas/entities/catalog.yaml"
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
CANONICAL_PACK = REPO_ROOT / CANONICAL_PACK_RELPATH
CI_HEADING = (
    "11.2.1.CI FULL_CORE_RESIDUAL_POSITIVE_NECESSARY_KIND_EXHAUSTIVENESS_DURABLE_UNKNOWN_PIN"
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
    assert WIRE_SEND_PERMITTED is False
    assert MS2_AUTHORIZED is False
    assert RAW_EQ_SOURCE_AUTHORITY is False
    assert CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING is False
    assert RECONSTRUCTION_ALGEBRA_COMPLETE is False
    assert U05_KIND_DECISION == DECISION_REMAIN_UNKNOWN
    assert U06_KIND_DECISION == DECISION_REMAIN_UNKNOWN
    assert RESIDUAL_KIND_DECISION == DECISION_REMAIN_UNKNOWN
    assert EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY == (
        "NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING"
    )
    assert "U05_LIABILITY_INCLUSION_OR_VALUE_UNRESOLVED" in UNRESOLVED_ALGEBRA_TERMS
    assert "U06_FEE_INCLUSION_UNRESOLVED" in UNRESOLVED_ALGEBRA_TERMS


def test_wrong_owner_go_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(
        ResidualPositiveNecessaryKindExhaustivenessDurableUnknownPinError,
        match="OWNER_GO_MISMATCH",
    ):
        execute_residual_positive_necessary_kind_exhaustiveness_durable_unknown_pin_v1(
            owner_go="WRONG",
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            evidence_root=tmp_path / "pack",
        )


def test_wrong_origin_sha_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(
        ResidualPositiveNecessaryKindExhaustivenessDurableUnknownPinError,
        match="ORIGIN_MAIN_SHA_MISMATCH",
    ):
        execute_residual_positive_necessary_kind_exhaustiveness_durable_unknown_pin_v1(
            owner_go=OWNER_GO,
            origin_main_sha="deadbeef",
            evidence_root=tmp_path / "pack",
        )


def test_path_a_is_not_this_slice(tmp_path: Path) -> None:
    with pytest.raises(
        ResidualPositiveNecessaryKindExhaustivenessDurableUnknownPinError,
        match="SELECTED_PATH_NOT_PATH_B",
    ):
        execute_residual_positive_necessary_kind_exhaustiveness_durable_unknown_pin_v1(
            owner_go=OWNER_GO,
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            evidence_root=tmp_path / "pack",
            selected_path="PATH_A",
        )


def test_durable_unknown_is_not_include_or_exclude() -> None:
    reject_durable_unknown_as_include_or_exclude_v1(claimed="DURABLE_UNKNOWN")
    reject_durable_unknown_as_include_or_exclude_v1(claimed=DECISION_REMAIN_UNKNOWN)
    for claimed in (
        OUTCOME_EXCLUDE,
        OUTCOME_INCLUDE,
        "0",
        "zero",
        "NO_RESIDUAL",
        "absent",
        "NONE_BINDABLE_MEANS_EXCLUDE",
    ):
        with pytest.raises(
            ResidualPositiveNecessaryKindExhaustivenessDurableUnknownPinError,
            match="DURABLE_UNKNOWN_IS_NOT_INCLUDE_OR_EXCLUDE",
        ):
            reject_durable_unknown_as_include_or_exclude_v1(claimed=claimed)


def test_none_bindable_get_count_zero_is_not_absent() -> None:
    reject_none_bindable_get_count_zero_as_absent_v1(claimed="NONE_BINDABLE")
    for claimed in ("ABSENT", "0", "NO_RESIDUAL", "NONE_BINDABLE_MEANS_NO_RESIDUAL"):
        with pytest.raises(
            ResidualPositiveNecessaryKindExhaustivenessDurableUnknownPinError,
            match="NONE_BINDABLE_GET_COUNT_0_IS_NOT_ABSENT_OR_EXCLUDE",
        ):
            reject_none_bindable_get_count_zero_as_absent_v1(claimed=claimed)


def test_hope_get_forbidden() -> None:
    reject_hope_get_v1(authorized_get_count="0", actual_get_count="0")
    with pytest.raises(Exception, match="HOPE_GET_FORBIDDEN"):
        reject_hope_get_v1(authorized_get_count="1", actual_get_count="0")


def test_absent_residual_proof_is_nonqualifying_not_exclude() -> None:
    outcome = evaluate_residual_primary_proof_v1(proof={})
    assert outcome.outcome not in {OUTCOME_INCLUDE, OUTCOME_EXCLUDE}
    reject_durable_unknown_as_include_or_exclude_v1(claimed=outcome.outcome)


def test_execute_pins_durable_unknown_without_get(tmp_path: Path) -> None:
    store = tmp_path / "pack"
    result = execute_residual_positive_necessary_kind_exhaustiveness_durable_unknown_pin_v1(
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        evidence_root=store,
    )
    claims = json.loads((store / "claims.json").read_text(encoding="utf-8"))
    tree = json.loads((store / "downstream_dependency_tree_v1.json").read_text(encoding="utf-8"))
    mapping = json.loads(
        (store / "mapping_and_reconstruction_fail_closed_v1.json").read_text(encoding="utf-8")
    )
    provenance = json.loads(
        (store / "none_bindable_get_count_zero_provenance_v1.json").read_text(encoding="utf-8")
    )
    historical = json.loads((store / "historical_non_uplift_v1.json").read_text(encoding="utf-8"))
    assert result.selected_path == SELECTED_PATH
    assert result.target_unknown == TARGET_RESIDUAL
    assert result.exhaustiveness_status == "DURABLE_UNKNOWN"
    assert result.residual_decision_after == DECISION_REMAIN_UNKNOWN
    assert result.further_residual_exhaustiveness_acquisition == "STOPPED"
    assert result.exhaustiveness_branch_closed == "true"
    assert result.first_definitive_block == ("NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING")
    assert result.authorized_get_count == "0"
    assert result.actual_get_count == "0"
    assert result.post_count == "0"
    assert claims["TARGET_UNKNOWN"] == TARGET_RESIDUAL
    assert claims["RESIDUAL_EVIDENCE_CLASS"] == CLASS_RESIDUAL
    assert claims["EXPECTED_PRIMARY_PROOF_OBJECT"] == PROOF_OBJECT_RESIDUAL
    assert claims["EXHAUSTIVENESS_STATUS_AFTER"] == "DURABLE_UNKNOWN"
    assert claims["EXHAUSTIVENESS_IDENTITY_STATUS"] == "DURABLE_UNKNOWN"
    assert claims["RESIDUAL_DECISION_AFTER"] == DECISION_REMAIN_UNKNOWN
    assert claims["DURABLE_UNKNOWN_NOT_INCLUDE"] == "true"
    assert claims["DURABLE_UNKNOWN_NOT_EXCLUDE"] == "true"
    assert claims["NONE_BINDABLE_GET_COUNT_0_IS_PROVENANCE_NOT_ABSENCE"] == "true"
    assert claims["NO_GET_REQUIRED"] == "true"
    assert claims["NO_EQ_SOURCE_AUTHORITY"] == "true"
    assert claims["NO_ALGEBRAIC_UPLIFT"] == "true"
    assert claims["NO_HOPE_GET"] == "true"
    assert claims["PARENT_BLOCKER_ID"] == PARENT_BLOCKER_ID
    assert claims["PARENT_CONCRETE_SURFACE_SELECTION_STATUS"] == "NONE_BINDABLE"
    assert claims["PARENT_GET_COUNT"] == "0"
    assert claims["PIN_OWNER_GO"] == PIN_OWNER_GO
    assert claims["ACTUAL_GET_COUNT"] == "0"
    assert claims["POST_COUNT"] == "0"
    assert claims["PATH_C_CLOSEOUT"] == "false"
    assert claims["VENUE_EQ_SOURCE_AUTHORITY"] == "false"
    assert claims["U05_STATUS"] == DECISION_REMAIN_UNKNOWN
    assert claims["U06_STATUS"] == DECISION_REMAIN_UNKNOWN
    assert claims["U05_EMBEDDING_IDENTITY"] == "DURABLE_UNKNOWN"
    assert claims["U06_PLACEMENT_IDENTITY"] == "DURABLE_UNKNOWN"
    assert claims["U05_ECONOMIC_VALUE_SYNTHESIZED"] == "false"
    assert claims["U06_ECONOMIC_VALUE_SYNTHESIZED"] == "false"
    assert claims["KIND_SET"] == "EMPTY_FAIL_CLOSED"
    assert claims["RECONSTRUCTION_ALGEBRA_COMPLETE"] == "false"
    assert claims["CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING"] == "false"
    assert claims["FIRST_DEFINITIVE_BLOCK"] == (
        "NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING"
    )
    assert claims["LOCAL_ADVANCEMENT_EXHAUSTED"] == "true"
    assert claims["NEXT_PRODUCTIVE_NODE"] == NEXT_PRODUCTIVE_NODE
    assert claims["NEXT_OWNER_GO_REQUIRED"] == NEXT_OWNER_GO
    assert claims["NEXT_ACTION"] == NEXT_ACTION
    assert "INCLUDE" not in claims["RESIDUAL_DECISION_AFTER"]
    assert "EXCLUDE" not in claims["RESIDUAL_DECISION_AFTER"]
    assert claims["EXHAUSTIVENESS_STATUS_AFTER"] not in {OUTCOME_INCLUDE, OUTCOME_EXCLUDE}
    assert tree["next_productive_classification"] == "REQUIRES_NEW_AUTHORITY"
    assert tree["first_definitive_block"] == ("NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING")
    assert mapping["new_mapping_invented"] == "false"
    assert mapping["residual_is_not_an_algebra_term"] == "true"
    assert mapping["u05_economic_value_synthesized"] == "false"
    assert mapping["u06_economic_value_synthesized"] == "false"
    assert provenance["none_bindable_caused_the_pin"] == "true"
    assert provenance["get_count_zero_caused_the_pin"] == "true"
    assert provenance["get_count_zero_is_not_absent"] == "true"
    assert historical["enumeration_is_not_exhaustiveness"] == "true"
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
    assert claims["TARGET_UNKNOWN"] == TARGET_RESIDUAL
    assert claims["EXHAUSTIVENESS_STATUS_AFTER"] == "DURABLE_UNKNOWN"
    assert claims["RESIDUAL_DECISION_AFTER"] == DECISION_REMAIN_UNKNOWN
    assert claims["FURTHER_RESIDUAL_EXHAUSTIVENESS_ACQUISITION"] == "STOPPED"
    assert claims["EXHAUSTIVENESS_BRANCH_CLOSED"] == "true"
    assert claims["PATH_C_CLOSEOUT"] == "false"
    assert claims["ACTUAL_GET_COUNT"] == "0"
    assert claims["POST_COUNT"] == "0"
    assert claims["DURABLE_UNKNOWN_NOT_INCLUDE"] == "true"
    assert claims["DURABLE_UNKNOWN_NOT_EXCLUDE"] == "true"
    assert claims["NONE_BINDABLE_GET_COUNT_0_IS_PROVENANCE_NOT_ABSENCE"] == "true"
    assert claims["NO_GET_REQUIRED"] == "true"
    assert claims["NO_HOPE_GET"] == "true"
    assert claims["U05_STATUS"] == DECISION_REMAIN_UNKNOWN
    assert claims["U06_STATUS"] == DECISION_REMAIN_UNKNOWN
    assert claims["BLOCKER_ID"] == BLOCKER_ID
    assert claims["PARENT_BLOCKER_ID"] == PARENT_BLOCKER_ID
    assert claims["FIRST_DEFINITIVE_BLOCK"] == (
        "NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING"
    )
    assert verify_manifest_sha256_v1(store_root=CANONICAL_PACK) == 0


def test_runbook_ci_persists_path_b() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    mot = MOT_PATH.read_text(encoding="utf-8")
    atlas = ATLAS_PATH.read_text(encoding="utf-8")
    runbook = RUNBOOK.read_text(encoding="utf-8")
    start = runbook.index(CI_HEADING)
    ci_section = runbook[start : runbook.index("## 11.3 Autonomy state model", start)]
    assert OWNER_GO in ci_section
    assert PIN_OWNER_GO in ci_section
    assert (
        "THIS_SLICE=11.2.1.CI.FULL_CORE_RESIDUAL_POSITIVE_NECESSARY_KIND_"
        "EXHAUSTIVENESS_DURABLE_UNKNOWN_PIN"
    ) in ci_section
    assert "SELECTED_PATH=PATH_B" in ci_section
    assert "TARGET_UNKNOWN=RESIDUAL_UNNAMED_NECESSARY_EQUITY_STOCK_EVENT_CLASS" in ci_section
    assert "EXHAUSTIVENESS_IDENTITY_STATUS=DURABLE_UNKNOWN" in ci_section
    assert "EXHAUSTIVENESS_STATUS_AFTER=DURABLE_UNKNOWN" in ci_section
    assert "RESIDUAL_DECISION_AFTER=REMAIN_UNKNOWN" in ci_section
    assert "DURABLE_UNKNOWN_NOT_INCLUDE=true" in ci_section
    assert "DURABLE_UNKNOWN_NOT_EXCLUDE=true" in ci_section
    assert "NONE_BINDABLE_GET_COUNT_0_IS_PROVENANCE_NOT_ABSENCE=true" in ci_section
    assert "NO_GET_REQUIRED=true" in ci_section
    assert "NO_EQ_SOURCE_AUTHORITY=true" in ci_section
    assert "NO_ALGEBRAIC_UPLIFT=true" in ci_section
    assert "NO_HOPE_GET=true" in ci_section
    assert "FURTHER_RESIDUAL_EXHAUSTIVENESS_ACQUISITION=STOPPED" in ci_section
    assert "EXHAUSTIVENESS_BRANCH_CLOSED=true" in ci_section
    assert "PATH_C_CLOSEOUT=false" in ci_section
    assert "ACTUAL_GET_COUNT=0" in ci_section
    assert "VENUE_EQ_SOURCE_AUTHORITY=false" in ci_section
    assert "U05_DECISION_UNCHANGED=REMAIN_UNKNOWN" in ci_section
    assert "U06_DECISION_UNCHANGED=REMAIN_UNKNOWN" in ci_section
    assert "FIRST_DEFINITIVE_BLOCK=NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING" in ci_section
    assert "LOCAL_ADVANCEMENT_EXHAUSTED=true" in ci_section
    assert PARENT_BLOCKER_ID in ci_section
    assert BLOCKER_ID in ci_section
    assert NEXT_OWNER_GO in ci_section
    assert NEXT_PRODUCTIVE_NODE in ci_section
    assert "CURRENT_CANONICAL_SECTION=11.2.1.CI" in ci_section
    assert (
        "DOCS_TOKEN_FULL_CORE_RESIDUAL_POSITIVE_NECESSARY_KIND_"
        "EXHAUSTIVENESS_DURABLE_UNKNOWN_PIN_V1"
    ) in spec
    assert (
        "FULL_CORE_RESIDUAL_POSITIVE_NECESSARY_KIND_EXHAUSTIVENESS_DURABLE_UNKNOWN_PIN_V1.md"
    ) in mot
    assert CI_HEADING in mot
    assert "11.2.1.CI" in atlas
    assert "residual_positive_necessary_kind_exhaustiveness_durable_unknown_pin_v1.py" in atlas
    assert "ATLAS_AUTHORITY=NONE" in atlas
