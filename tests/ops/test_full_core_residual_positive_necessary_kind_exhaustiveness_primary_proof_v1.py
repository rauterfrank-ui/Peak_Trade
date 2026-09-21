"""Residual NONE_BINDABLE exhaustiveness primary-proof persist tests.

No GET. No POST. No Hope-GET. NONE_BINDABLE is not EXCLUDE.
U05/U06 remain REMAIN_UNKNOWN and are not absent/EXCLUDE.
Exhaustiveness is not closed by enumerating known kinds.
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
    RAW_EQ_SOURCE_AUTHORITY,
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
from src.ops.governed_productive_account_equity_authority_producer_v1.residual_positive_necessary_kind_exhaustiveness_primary_proof_v1 import (
    BLOCKER_ID,
    CANONICAL_PACK_RELPATH,
    EXPECTED_ORIGIN_MAIN_SHA,
    NEXT_ACTION,
    NEXT_OWNER_GO,
    NEXT_PRODUCTIVE_NODE,
    OWNER_GO,
    RESIDUAL_ACQUISITION_SURFACE,
    SELECTION_STATUS,
    ResidualPositiveNecessaryKindExhaustivenessPrimaryProofError,
    execute_residual_positive_necessary_kind_exhaustiveness_primary_proof_v1,
    reject_acquisition_without_bound_contract_v1,
    reject_algebraic_uplift_v1,
    reject_enumeration_as_exhaustiveness_v1,
    reject_eq_source_authority_v1,
    reject_exhaustiveness_close_while_u05_u06_unknown_v1,
    reject_retroactive_evidence_uplift_v1,
    reject_unknown_as_absent_v1,
    reject_unknown_as_exclude_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.u06_paired_fee_event_and_once_only_equity_stock_effect_primary_proof_surface_binding_v1 import (
    reject_hope_get_v1,
    reject_none_bindable_as_exclude_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = (
    "src/ops/governed_productive_account_equity_authority_producer_v1/"
    "residual_positive_necessary_kind_exhaustiveness_primary_proof_v1.py"
)
SPEC_PATH = (
    REPO_ROOT
    / "docs/ops/specs/FULL_CORE_RESIDUAL_POSITIVE_NECESSARY_KIND_EXHAUSTIVENESS_PRIMARY_PROOF_V1.md"
)
MOT_PATH = REPO_ROOT / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md"
ATLAS_PATH = REPO_ROOT / "docs/system_atlas/entities/catalog.yaml"
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
CANONICAL_PACK = REPO_ROOT / CANONICAL_PACK_RELPATH
CH_HEADING = "11.2.1.CH FULL_CORE_RESIDUAL_POSITIVE_NECESSARY_KIND_EXHAUSTIVENESS_PRIMARY_PROOF"
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
    assert U05_KIND_DECISION == DECISION_REMAIN_UNKNOWN
    assert U06_KIND_DECISION == DECISION_REMAIN_UNKNOWN
    assert RESIDUAL_KIND_DECISION == DECISION_REMAIN_UNKNOWN
    assert EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY == (
        "TRUSTED_29P_PRETRADE_LIVE_ACCOUNT_BOUND_AND_INSTRUMENT_SCOPE_OWNER_GOS"
    )


def test_u05_unknown_preserved() -> None:
    assert U05_KIND_DECISION == DECISION_REMAIN_UNKNOWN
    with pytest.raises(
        ResidualPositiveNecessaryKindExhaustivenessPrimaryProofError,
        match="U05_UNKNOWN_PRESERVED",
    ):
        reject_exhaustiveness_close_while_u05_u06_unknown_v1(
            u05_decision="EXCLUDE",
            u06_decision=DECISION_REMAIN_UNKNOWN,
            residual_outcome="NONQUALIFYING",
        )


def test_u06_unknown_preserved() -> None:
    assert U06_KIND_DECISION == DECISION_REMAIN_UNKNOWN
    with pytest.raises(
        ResidualPositiveNecessaryKindExhaustivenessPrimaryProofError,
        match="U06_UNKNOWN_PRESERVED",
    ):
        reject_exhaustiveness_close_while_u05_u06_unknown_v1(
            u05_decision=DECISION_REMAIN_UNKNOWN,
            u06_decision="INCLUDE",
            residual_outcome="NONQUALIFYING",
        )


def test_unknown_not_absent() -> None:
    reject_unknown_as_absent_v1(claimed=DECISION_REMAIN_UNKNOWN)
    for claimed in ("ABSENT", "0", "zero", "empty", "NO_CLASS"):
        with pytest.raises(
            ResidualPositiveNecessaryKindExhaustivenessPrimaryProofError,
            match="UNKNOWN_NOT_ABSENT",
        ):
            reject_unknown_as_absent_v1(claimed=claimed)


def test_unknown_not_exclude() -> None:
    reject_unknown_as_exclude_v1(claimed=DECISION_REMAIN_UNKNOWN)
    for claimed in (OUTCOME_EXCLUDE, "EXCLUDE"):
        with pytest.raises(
            ResidualPositiveNecessaryKindExhaustivenessPrimaryProofError,
            match="UNKNOWN_NOT_EXCLUDE",
        ):
            reject_unknown_as_exclude_v1(claimed=claimed)


def test_no_eq_source_authority() -> None:
    reject_eq_source_authority_v1(venue_eq_source_authority="false")
    with pytest.raises(
        ResidualPositiveNecessaryKindExhaustivenessPrimaryProofError,
        match="NO_EQ_SOURCE_AUTHORITY",
    ):
        reject_eq_source_authority_v1(venue_eq_source_authority="true")


def test_no_algebraic_uplift() -> None:
    reject_algebraic_uplift_v1(formula="")
    with pytest.raises(
        ResidualPositiveNecessaryKindExhaustivenessPrimaryProofError,
        match="NO_ALGEBRAIC_UPLIFT",
    ):
        reject_algebraic_uplift_v1(formula="eq=cashBal+upl-liab")


def test_no_retroactive_evidence_uplift() -> None:
    reject_retroactive_evidence_uplift_v1(uplift_claimed="false")
    with pytest.raises(
        ResidualPositiveNecessaryKindExhaustivenessPrimaryProofError,
        match="NO_RETROACTIVE_EVIDENCE_UPLIFT",
    ):
        reject_retroactive_evidence_uplift_v1(uplift_claimed="true")


def test_hope_get_forbidden() -> None:
    reject_hope_get_v1(authorized_get_count="0", actual_get_count="0")
    with pytest.raises(Exception, match="HOPE_GET_FORBIDDEN"):
        reject_hope_get_v1(authorized_get_count="1", actual_get_count="0")
    with pytest.raises(Exception, match="HOPE_GET_FORBIDDEN"):
        reject_hope_get_v1(authorized_get_count="0", actual_get_count="1")


def test_exhaustiveness_requires_positive_completeness_proof() -> None:
    reject_enumeration_as_exhaustiveness_v1(
        inventory="OWNER_DECLARED_TODAY_INITIAL_EQUITY_STOCK",
        proven_complete="false",
    )
    with pytest.raises(
        ResidualPositiveNecessaryKindExhaustivenessPrimaryProofError,
        match="EXHAUSTIVENESS_REQUIRES_POSITIVE_COMPLETENESS_PROOF",
    ):
        reject_enumeration_as_exhaustiveness_v1(
            inventory="OWNER_DECLARED_TODAY_INITIAL_EQUITY_STOCK",
            proven_complete="true",
        )
    with pytest.raises(
        ResidualPositiveNecessaryKindExhaustivenessPrimaryProofError,
        match="EXHAUSTIVENESS_REQUIRES_POSITIVE_COMPLETENESS_PROOF",
    ):
        reject_exhaustiveness_close_while_u05_u06_unknown_v1(
            u05_decision=DECISION_REMAIN_UNKNOWN,
            u06_decision=DECISION_REMAIN_UNKNOWN,
            residual_outcome=OUTCOME_EXCLUDE,
        )


def test_acquisition_cannot_run_without_concrete_bound_contract() -> None:
    reject_acquisition_without_bound_contract_v1(
        surface_binding_status="NOT_BOUND",
        authorized_get_count="0",
        actual_get_count="0",
    )
    with pytest.raises(
        ResidualPositiveNecessaryKindExhaustivenessPrimaryProofError,
        match="ACQUISITION_CANNOT_RUN_WITHOUT_CONCRETE_BOUND_CONTRACT",
    ):
        reject_acquisition_without_bound_contract_v1(
            surface_binding_status="NOT_BOUND",
            authorized_get_count="1",
            actual_get_count="0",
        )


def test_wrong_owner_go_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(
        ResidualPositiveNecessaryKindExhaustivenessPrimaryProofError,
        match="OWNER_GO_MISMATCH",
    ):
        execute_residual_positive_necessary_kind_exhaustiveness_primary_proof_v1(
            owner_go="WRONG",
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            evidence_root=tmp_path / "pack",
        )


def test_wrong_origin_sha_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(
        ResidualPositiveNecessaryKindExhaustivenessPrimaryProofError,
        match="ORIGIN_MAIN_SHA_MISMATCH",
    ):
        execute_residual_positive_necessary_kind_exhaustiveness_primary_proof_v1(
            owner_go=OWNER_GO,
            origin_main_sha="deadbeef",
            evidence_root=tmp_path / "pack",
        )


def test_absent_residual_proof_is_nonqualifying_not_exclude() -> None:
    outcome = evaluate_residual_primary_proof_v1(proof={})
    assert outcome.outcome not in {OUTCOME_INCLUDE, OUTCOME_EXCLUDE}
    reject_none_bindable_as_exclude_v1(claimed=outcome.outcome)
    reject_unknown_as_exclude_v1(claimed=outcome.outcome)
    assert outcome.target_unknown == TARGET_RESIDUAL


def test_execute_persists_none_bindable_without_get(tmp_path: Path) -> None:
    store = tmp_path / "pack"
    result = execute_residual_positive_necessary_kind_exhaustiveness_primary_proof_v1(
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        evidence_root=store,
    )
    claims = json.loads((store / "claims.json").read_text(encoding="utf-8"))
    census = json.loads(
        (store / "candidate_surface_capability_adjudication_v1.json").read_text(encoding="utf-8")
    )
    inventory = json.loads(
        (store / "ratified_necessary_kind_inventory_v1.json").read_text(encoding="utf-8")
    )
    guard = json.loads(
        (store / "unknown_not_absent_or_exclude_guard_v1.json").read_text(encoding="utf-8")
    )
    completeness = json.loads(
        (store / "exhaustiveness_completeness_requirement_v1.json").read_text(encoding="utf-8")
    )
    historical = json.loads((store / "historical_non_uplift_v1.json").read_text(encoding="utf-8"))
    assert result.concrete_surface_selection_status == SELECTION_STATUS
    assert result.authorized_get_count == "0"
    assert result.actual_get_count == "0"
    assert result.post_count == "0"
    assert result.residual_decision_after == DECISION_REMAIN_UNKNOWN
    assert result.exhaustiveness_status_after == "REMAIN_UNKNOWN"
    assert result.blocker_id == BLOCKER_ID
    assert claims["OWNER_GO"] == OWNER_GO
    assert claims["RESIDUAL_EVIDENCE_CLASS"] == CLASS_RESIDUAL
    assert claims["EXPECTED_PRIMARY_PROOF_OBJECT"] == PROOF_OBJECT_RESIDUAL
    assert claims["AUTHORIZED_ACQUISITION_SURFACE"] == RESIDUAL_ACQUISITION_SURFACE
    assert claims["CONCRETE_SURFACE_SELECTION_STATUS"] == "NONE_BINDABLE"
    assert claims["SELECTED_CANDIDATE_ID"] == "NONE"
    assert claims["SELECTED_METHOD"] == "NONE"
    assert claims["SELECTED_HOST"] == "NONE"
    assert claims["SELECTED_PATH"] == "NONE"
    assert claims["SELECTED_QUERY"] == "NONE"
    assert claims["MAX_GET_COUNT"] == "0"
    assert claims["AUTHORIZED_GET_COUNT"] == "0"
    assert claims["ACTUAL_GET_COUNT"] == "0"
    assert claims["POST_COUNT"] == "0"
    assert claims["RETRY_ALLOWED"] == "false"
    assert claims["HOPE_GET_FORBIDDEN"] == "true"
    assert claims["PRODUCTIVE_ACQUISITION_AUTHORIZED"] == "false"
    assert claims["PRODUCTIVE_ACQUISITION_EXECUTED"] == "false"
    assert claims["EXISTING_EVIDENCE_SUFFICIENT"] == "false"
    assert claims["GET_ALONE_MAY_INCLUDE"] == "false"
    assert claims["GET_ALONE_MAY_EXCLUDE"] == "false"
    assert claims["VENUE_EQ_SOURCE_AUTHORITY"] == "false"
    assert claims["NO_EQ_SOURCE_AUTHORITY"] == "true"
    assert claims["NO_ALGEBRAIC_UPLIFT"] == "true"
    assert claims["NO_RETROACTIVE_EVIDENCE_UPLIFT"] == "true"
    assert claims["ACCOUNT_BILLS_CANONICALIZED"] == "false"
    assert claims["RESIDUAL_DECISION_AFTER"] == DECISION_REMAIN_UNKNOWN
    assert claims["U05_DECISION_UNCHANGED"] == DECISION_REMAIN_UNKNOWN
    assert claims["U06_DECISION_UNCHANGED"] == DECISION_REMAIN_UNKNOWN
    assert claims["U05_STATUS"] == DECISION_REMAIN_UNKNOWN
    assert claims["U06_STATUS"] == DECISION_REMAIN_UNKNOWN
    assert claims["U05_EMBEDDING_IDENTITY"] == "DURABLE_UNKNOWN"
    assert claims["U06_PLACEMENT_IDENTITY"] == "DURABLE_UNKNOWN"
    assert claims["UNKNOWN_NOT_ABSENT"] == "true"
    assert claims["UNKNOWN_NOT_EXCLUDE"] == "true"
    assert claims["NONE_BINDABLE_IS_NOT_EXCLUDE"] == "true"
    assert claims["DURABLE_UNKNOWN_PIN_IMPLEMENTED_THIS_SLICE"] == "false"
    assert claims["PATH_C_CLOSEOUT"] == "false"
    assert claims["SECRET_RESOLUTION_STATUS"] == "NOT_ATTEMPTED"
    assert claims["CCY_BINDING"] == "USDC"
    assert claims["RATIFIED_NECESSARY_KIND_SET"] == ("OWNER_DECLARED_TODAY_INITIAL_EQUITY_STOCK")
    assert claims["NEXT_PRODUCTIVE_NODE"] == NEXT_PRODUCTIVE_NODE
    assert claims["NEXT_OWNER_GO_REQUIRED"] == NEXT_OWNER_GO
    assert claims["NEXT_ACTION"] == NEXT_ACTION
    assert "EXCLUDE" not in claims["RESIDUAL_DECISION_AFTER"]
    assert "INCLUDE" not in claims["RESIDUAL_DECISION_AFTER"]
    assert census["selection_status"] == "NONE_BINDABLE"
    assert census["hope_get_forbidden"] == "true"
    assert census["candidate_count"] == "6"
    assert all(item["bindable"] == "false" for item in census["records"])
    assert inventory["enumeration_is_not_exhaustiveness"] == "true"
    assert inventory["u05_in_positive_set"] == "false"
    assert inventory["u06_in_positive_set"] == "false"
    assert guard["u05_not_treated_as_absent"] == "true"
    assert guard["u06_not_treated_as_exclude"] == "true"
    assert completeness["exhaustiveness_requires_positive_completeness_proof"] == "true"
    assert historical["sealed_u05_u06_packs_not_residual_authority"] == "true"
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
    assert claims["RESIDUAL_DECISION_AFTER"] == DECISION_REMAIN_UNKNOWN
    assert claims["U05_STATUS"] == DECISION_REMAIN_UNKNOWN
    assert claims["U06_STATUS"] == DECISION_REMAIN_UNKNOWN
    assert claims["U06_PLACEMENT_IDENTITY"] == "DURABLE_UNKNOWN"
    assert claims["BLOCKER_ID"] == BLOCKER_ID
    assert claims["NONE_BINDABLE_IS_NOT_EXCLUDE"] == "true"
    assert claims["HOPE_GET_FORBIDDEN"] == "true"
    assert claims["PRODUCTIVE_ACQUISITION_AUTHORIZED"] == "false"
    assert claims["EXISTING_EVIDENCE_SUFFICIENT"] == "false"
    assert claims["EXHAUSTIVENESS_STATUS_AFTER"] == "REMAIN_UNKNOWN"
    assert claims["NEXT_PRODUCTIVE_NODE"] == NEXT_PRODUCTIVE_NODE
    assert verify_manifest_sha256_v1(store_root=CANONICAL_PACK) == 0


def test_runbook_ch_persists_none_bindable() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    mot = MOT_PATH.read_text(encoding="utf-8")
    atlas = ATLAS_PATH.read_text(encoding="utf-8")
    runbook = RUNBOOK.read_text(encoding="utf-8")
    start = runbook.index(CH_HEADING)
    ch_section = runbook[start : runbook.index("## 11.3 Autonomy state model", start)]
    assert OWNER_GO in ch_section
    assert (
        "THIS_SLICE=11.2.1.CH.FULL_CORE_RESIDUAL_POSITIVE_NECESSARY_KIND_"
        "EXHAUSTIVENESS_PRIMARY_PROOF"
    ) in ch_section
    assert "CONCRETE_SURFACE_SELECTION_STATUS=NONE_BINDABLE" in ch_section
    assert "AUTHORIZED_GET_COUNT=0" in ch_section
    assert "ACTUAL_GET_COUNT=0" in ch_section
    assert "MAX_GET_COUNT=0" in ch_section
    assert "RETRY_ALLOWED=false" in ch_section
    assert "HOPE_GET_FORBIDDEN=true" in ch_section
    assert "RESIDUAL_DECISION_AFTER=REMAIN_UNKNOWN" in ch_section
    assert "U05_DECISION_UNCHANGED=REMAIN_UNKNOWN" in ch_section
    assert "U06_DECISION_UNCHANGED=REMAIN_UNKNOWN" in ch_section
    assert "U06_PLACEMENT_IDENTITY=DURABLE_UNKNOWN" in ch_section
    assert "NONE_BINDABLE_IS_NOT_EXCLUDE=true" in ch_section
    assert "UNKNOWN_NOT_ABSENT=true" in ch_section
    assert "UNKNOWN_NOT_EXCLUDE=true" in ch_section
    assert "PRODUCTIVE_ACQUISITION_AUTHORIZED=false" in ch_section
    assert "EXISTING_EVIDENCE_SUFFICIENT=false" in ch_section
    assert "GET_ALONE_MAY_INCLUDE=false" in ch_section
    assert "GET_ALONE_MAY_EXCLUDE=false" in ch_section
    assert "VENUE_EQ_SOURCE_AUTHORITY=false" in ch_section
    assert "NO_EQ_SOURCE_AUTHORITY=true" in ch_section
    assert "NO_ALGEBRAIC_UPLIFT=true" in ch_section
    assert "ACCOUNT_BILLS_CANONICALIZED=false" in ch_section
    assert "DURABLE_UNKNOWN_PIN_IMPLEMENTED_THIS_SLICE=false" in ch_section
    assert BLOCKER_ID in ch_section
    assert NEXT_OWNER_GO in ch_section
    assert NEXT_PRODUCTIVE_NODE in ch_section
    assert "CURRENT_CANONICAL_SECTION=11.2.1.CH" in ch_section
    assert (
        "DOCS_TOKEN_FULL_CORE_RESIDUAL_POSITIVE_NECESSARY_KIND_EXHAUSTIVENESS_PRIMARY_PROOF_V1"
        in spec
    )
    assert ("FULL_CORE_RESIDUAL_POSITIVE_NECESSARY_KIND_EXHAUSTIVENESS_PRIMARY_PROOF_V1.md") in mot
    assert CH_HEADING in mot
    assert "11.2.1.CH" in atlas
    assert "residual_positive_necessary_kind_exhaustiveness_primary_proof_v1.py" in atlas
    assert "ATLAS_AUTHORITY=NONE" in atlas
