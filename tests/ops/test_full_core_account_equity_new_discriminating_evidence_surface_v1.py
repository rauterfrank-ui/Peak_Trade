"""New discriminating U05 owner-supplied embedding-witness surface tests.

No GET. No POST. No Hope-GET. Absent artifact is not INCLUDE or EXCLUDE.
Already-adjudicated NONE_BINDABLE and GET-alone surfaces cannot be this
surface. KIND_SET remains EMPTY_FAIL_CLOSED. Mapping remains not
canonically valid. Fixtures prove the surface can INCLUDE or EXCLUDE.
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
from src.ops.governed_productive_account_equity_authority_producer_v1.account_equity_new_discriminating_evidence_surface_v1 import (
    BLOCKER_ID,
    CANONICAL_INPUT_SURFACE_RELPATH,
    CANONICAL_PACK_RELPATH,
    EXACT_MISSING_PREDICATE,
    EXPECTED_ORIGIN_MAIN_SHA,
    FORBIDDEN_REUSED_SURFACES,
    NEXT_ACTION,
    NEXT_OWNER_GO,
    NEXT_PRODUCTIVE_NODE,
    OWNER_GO,
    PARENT_BLOCKER_ID,
    PIN_OWNER_GO,
    SURFACE_ID,
    AccountEquityNewDiscriminatingEvidenceSurfaceError,
    execute_account_equity_new_discriminating_evidence_surface_v1,
    fixture_u05_exclude_witness_payload_v1,
    fixture_u05_include_witness_payload_v1,
    reject_absent_artifact_as_include_or_exclude_v1,
    reject_already_adjudicated_surface_as_this_surface_v1,
    reject_venue_eq_as_embedding_witness_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.bj_future_admissible_evidence_and_include_exclude_qualification_law_v1 import (
    OUTCOME_EXCLUDE,
    OUTCOME_INCLUDE,
    OUTCOME_NONQUALIFYING,
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
from src.ops.governed_productive_account_equity_authority_producer_v1.remaining_necessary_kind_evidence_classification_v1 import (
    CANONICAL_PACK_RELPATH as CANONICAL_CK_PACK_RELPATH,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.u05_durable_unknown_embedding_identity_pin_v1 import (
    CANONICAL_PACK_RELPATH as CANONICAL_CE_PACK_RELPATH,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.u06_paired_fee_event_and_once_only_equity_stock_effect_primary_proof_surface_binding_v1 import (
    reject_hope_get_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = (
    "src/ops/governed_productive_account_equity_authority_producer_v1/"
    "account_equity_new_discriminating_evidence_surface_v1.py"
)
SPEC_PATH = (
    REPO_ROOT
    / "docs/ops/specs/"
    / "FULL_CORE_ACCOUNT_EQUITY_NEW_DISCRIMINATING_EVIDENCE_SURFACE_V1.md"
)
MOT_PATH = REPO_ROOT / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md"
ATLAS_PATH = REPO_ROOT / "docs/system_atlas/entities/catalog.yaml"
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
CANONICAL_PACK = REPO_ROOT / CANONICAL_PACK_RELPATH
CL_HEADING = "11.2.1.CL FULL_CORE_ACCOUNT_EQUITY_NEW_DISCRIMINATING_EVIDENCE_SURFACE"
FORBIDDEN_SOURCE_TOKENS = (
    "urllib",
    "requests",
    "httpx",
    "GET_ENDPOINTS_PRIVATE",
    "max_retries",
    "eq=cashBal",
)


def _execute(
    tmp_path: Path,
    *,
    input_payload: dict[str, str] | None = None,
) -> object:
    if input_payload is not None:
        surface = tmp_path / "input"
        surface.mkdir(parents=True, exist_ok=True)
        (surface / "witness.json").write_text(
            json.dumps(input_payload, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
        input_relpath = "input"
    else:
        input_relpath = "missing-input"
    return execute_account_equity_new_discriminating_evidence_surface_v1(
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        evidence_root=tmp_path / "pack",
        repo_root=tmp_path,
        input_surface_relpath=input_relpath,
        sealed_ck_pack=REPO_ROOT / CANONICAL_CK_PACK_RELPATH,
        sealed_ce_pack=REPO_ROOT / CANONICAL_CE_PACK_RELPATH,
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
    assert SURFACE_ID not in FORBIDDEN_REUSED_SURFACES


def test_wrong_owner_go_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(
        AccountEquityNewDiscriminatingEvidenceSurfaceError,
        match="OWNER_GO_MISMATCH",
    ):
        execute_account_equity_new_discriminating_evidence_surface_v1(
            owner_go="WRONG",
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            evidence_root=tmp_path / "pack",
            sealed_ck_pack=REPO_ROOT / CANONICAL_CK_PACK_RELPATH,
            sealed_ce_pack=REPO_ROOT / CANONICAL_CE_PACK_RELPATH,
        )


def test_wrong_origin_sha_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(
        AccountEquityNewDiscriminatingEvidenceSurfaceError,
        match="ORIGIN_MAIN_SHA_MISMATCH",
    ):
        execute_account_equity_new_discriminating_evidence_surface_v1(
            owner_go=OWNER_GO,
            origin_main_sha="deadbeef",
            evidence_root=tmp_path / "pack",
            sealed_ck_pack=REPO_ROOT / CANONICAL_CK_PACK_RELPATH,
            sealed_ce_pack=REPO_ROOT / CANONICAL_CE_PACK_RELPATH,
        )


def test_already_adjudicated_surfaces_cannot_be_this_surface() -> None:
    reject_already_adjudicated_surface_as_this_surface_v1(claimed_surface_id=SURFACE_ID)
    for surface_id in (
        "GET_/api/v5/account/interest-accrued",
        "GET_/api/v5/account/bills",
        "NONE",
        "GET_ALONE",
    ):
        with pytest.raises(
            AccountEquityNewDiscriminatingEvidenceSurfaceError,
            match="ALREADY_ADJUDICATED_NONE_BINDABLE_OR_GET_ALONE_NOT_THIS_SURFACE",
        ):
            reject_already_adjudicated_surface_as_this_surface_v1(claimed_surface_id=surface_id)


def test_absent_artifact_is_not_include_or_exclude() -> None:
    reject_absent_artifact_as_include_or_exclude_v1(claimed=DECISION_REMAIN_UNKNOWN)
    for claimed in (OUTCOME_EXCLUDE, OUTCOME_INCLUDE, "0", "zero", "absent", "NONE"):
        with pytest.raises(
            AccountEquityNewDiscriminatingEvidenceSurfaceError,
            match="ABSENT_ARTIFACT_IS_NOT_INCLUDE_OR_EXCLUDE",
        ):
            reject_absent_artifact_as_include_or_exclude_v1(claimed=claimed)


def test_venue_eq_cannot_be_embedding_witness() -> None:
    reject_venue_eq_as_embedding_witness_v1(claimed_venue_eq_source="false")
    with pytest.raises(
        AccountEquityNewDiscriminatingEvidenceSurfaceError,
        match="VENUE_EQ_CANNOT_BE_EMBEDDING_WITNESS",
    ):
        reject_venue_eq_as_embedding_witness_v1(claimed_venue_eq_source="true")


def test_hope_get_forbidden() -> None:
    reject_hope_get_v1(authorized_get_count="0", actual_get_count="0")
    with pytest.raises(Exception, match="HOPE_GET_FORBIDDEN"):
        reject_hope_get_v1(authorized_get_count="1", actual_get_count="0")


def test_absent_artifact_binds_surface_without_include_or_exclude(tmp_path: Path) -> None:
    result = _execute(tmp_path)
    claims = json.loads((tmp_path / "pack" / "claims.json").read_text(encoding="utf-8"))
    qualification = json.loads(
        (tmp_path / "pack" / "qualification_v1.json").read_text(encoding="utf-8")
    )
    assert result.surface_id == SURFACE_ID
    assert result.surface_binding_status == "BOUND"
    assert result.artifact_present == "false"
    assert result.u05_bj_outcome == OUTCOME_NONQUALIFYING
    assert result.u05_status == DECISION_REMAIN_UNKNOWN
    assert result.u06_status == DECISION_REMAIN_UNKNOWN
    assert result.residual_status == DECISION_REMAIN_UNKNOWN
    assert result.kind_set == "EMPTY_FAIL_CLOSED"
    assert result.kind_set_resolved == "false"
    assert result.canonically_valid_account_equity_source_mapping == "false"
    assert result.authorized_get_count == "0"
    assert result.actual_get_count == "0"
    assert result.post_count == "0"
    assert claims["OWNER_GO"] == OWNER_GO
    assert claims["PIN_OWNER_GO"] == PIN_OWNER_GO
    assert claims["PIN_OWNER_GO_STATUS"] == "SATISFIED_BY_WORKPACKAGE"
    assert claims["PREVIOUS_OWNER_SUPPLY_ASSUMPTION"] == "OPERATIONALIZED"
    assert claims["NEW_DISCRIMINATING_SURFACE_BOUND"] == "true"
    assert claims["NEW_DISCRIMINATING_EVIDENCE_ACQUIRED"] == "false"
    assert claims["ARTIFACT_PRESENT"] == "false"
    assert claims["U05_STATUS"] == DECISION_REMAIN_UNKNOWN
    assert claims["U05_KIND_DECISION"] == DECISION_REMAIN_UNKNOWN
    assert claims["U05_EMBEDDING_IDENTITY"] == "DURABLE_UNKNOWN"
    assert claims["U06_STATUS"] == DECISION_REMAIN_UNKNOWN
    assert claims["RESIDUAL_STATUS"] == DECISION_REMAIN_UNKNOWN
    assert claims["DURABLE_UNKNOWN_NOT_INCLUDE"] == "true"
    assert claims["DURABLE_UNKNOWN_NOT_EXCLUDE"] == "true"
    assert claims["KIND_SET"] == "EMPTY_FAIL_CLOSED"
    assert claims["KIND_SET_RESOLVED"] == "false"
    assert claims["CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING"] == "false"
    assert claims["ACTUAL_GET_COUNT"] == "0"
    assert claims["POST_COUNT"] == "0"
    assert claims["FURTHER_U05_VENUE_EMBEDDING_WITNESS_GET_ACQUISITION"] == "STOPPED"
    assert claims["NEXT_OWNER_GO_REQUIRED"] == NEXT_OWNER_GO
    assert claims["NEXT_ACTION"] == NEXT_ACTION
    assert claims["BLOCKER_ID"] == BLOCKER_ID
    assert claims["PARENT_BLOCKER_ID"] == PARENT_BLOCKER_ID
    assert claims["EXACT_MISSING_PREDICATE"] == EXACT_MISSING_PREDICATE
    assert qualification["u05_bj_basis"] == ("OWNER_SUPPLIED_EMBEDDING_WITNESS_ARTIFACT_ABSENT")
    assert verify_manifest_sha256_v1(store_root=tmp_path / "pack") == 0
    assert U05_KIND_DECISION == DECISION_REMAIN_UNKNOWN


def test_fixture_include_is_decision_capable_without_mutating_standing_pin(
    tmp_path: Path,
) -> None:
    result = _execute(tmp_path, input_payload=fixture_u05_include_witness_payload_v1())
    claims = json.loads((tmp_path / "pack" / "claims.json").read_text(encoding="utf-8"))
    scan = json.loads((tmp_path / "pack" / "scan_v1.json").read_text(encoding="utf-8"))
    assert result.artifact_present == "true"
    assert result.u05_bj_outcome == OUTCOME_INCLUDE
    assert result.u05_status == OUTCOME_INCLUDE
    assert result.u06_status == DECISION_REMAIN_UNKNOWN
    assert result.residual_status == DECISION_REMAIN_UNKNOWN
    assert result.kind_set_resolved == "false"
    assert result.canonically_valid_account_equity_source_mapping == "false"
    assert claims["U05_INCLUDE_PROVEN"] == "true"
    assert claims["U05_EXCLUDE_PROVEN"] == "false"
    assert claims["U05_KIND_DECISION"] == DECISION_REMAIN_UNKNOWN
    assert claims["NEW_DISCRIMINATING_EVIDENCE_ACQUIRED"] == "true"
    assert claims["ORIGINAL_VALUES_PRESERVED"] == "true"
    assert scan["original_values_preserved"] == "true"
    assert scan["raw_bytes_digest"] != ""
    assert U05_KIND_DECISION == DECISION_REMAIN_UNKNOWN
    assert U06_KIND_DECISION == DECISION_REMAIN_UNKNOWN


def test_fixture_exclude_is_decision_capable_without_mapping_uplift(tmp_path: Path) -> None:
    result = _execute(tmp_path, input_payload=fixture_u05_exclude_witness_payload_v1())
    claims = json.loads((tmp_path / "pack" / "claims.json").read_text(encoding="utf-8"))
    assert result.u05_bj_outcome == OUTCOME_EXCLUDE
    assert result.u05_status == OUTCOME_EXCLUDE
    assert result.kind_set == "EMPTY_FAIL_CLOSED"
    assert result.canonically_valid_account_equity_source_mapping == "false"
    assert claims["U05_EXCLUDE_PROVEN"] == "true"
    assert claims["U05_INCLUDE_PROVEN"] == "false"
    assert claims["U06_STATUS"] == DECISION_REMAIN_UNKNOWN
    assert claims["RESIDUAL_STATUS"] == DECISION_REMAIN_UNKNOWN
    assert claims["CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING"] == "false"


def test_source_does_not_get_or_post_or_uplift() -> None:
    source = (REPO_ROOT / SOURCE_PATH).read_text(encoding="utf-8")
    for token in FORBIDDEN_SOURCE_TOKENS:
        assert token not in source
    assert "cashBal+upl" not in source
    assert "PRODUCTIVE_ACQUISITION_AUTHORIZED = TRUE" not in source.upper()


def test_canonical_pack_sealed() -> None:
    claims = json.loads((CANONICAL_PACK / "claims.json").read_text(encoding="utf-8"))
    scan = json.loads((CANONICAL_PACK / "scan_v1.json").read_text(encoding="utf-8"))
    assert claims["OWNER_GO"] == OWNER_GO
    assert claims["SURFACE_ID"] == SURFACE_ID
    assert claims["SURFACE_BINDING_STATUS"] == "BOUND"
    assert claims["ARTIFACT_PRESENT"] == "false"
    assert claims["KIND_SET"] == "EMPTY_FAIL_CLOSED"
    assert claims["KIND_SET_RESOLVED"] == "false"
    assert claims["CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING"] == "false"
    assert claims["U04_STATUS"] == "UNRESOLVED"
    assert claims["U05_STATUS"] == DECISION_REMAIN_UNKNOWN
    assert claims["U06_STATUS"] == DECISION_REMAIN_UNKNOWN
    assert claims["RESIDUAL_STATUS"] == DECISION_REMAIN_UNKNOWN
    assert claims["ACTUAL_GET_COUNT"] == "0"
    assert claims["POST_COUNT"] == "0"
    assert claims["PREVIOUS_OWNER_SUPPLY_ASSUMPTION"] == "OPERATIONALIZED"
    assert claims["FIRST_DEFINITIVE_BLOCK"] == (
        "NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING"
    )
    assert claims["EXACT_MISSING_PREDICATE"] == EXACT_MISSING_PREDICATE
    assert scan["artifact_present"] == "false"
    assert verify_manifest_sha256_v1(store_root=CANONICAL_PACK) == 0
    assert not (REPO_ROOT / CANONICAL_INPUT_SURFACE_RELPATH).exists()


def test_runbook_cl_persists_surface() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    mot = MOT_PATH.read_text(encoding="utf-8")
    atlas = ATLAS_PATH.read_text(encoding="utf-8")
    runbook = RUNBOOK.read_text(encoding="utf-8")
    start = runbook.index(CL_HEADING)
    cl_section = runbook[start : runbook.index("## 11.3 Autonomy state model", start)]
    assert OWNER_GO in cl_section
    assert PIN_OWNER_GO in cl_section
    assert (
        "THIS_SLICE=11.2.1.CL.FULL_CORE_ACCOUNT_EQUITY_NEW_DISCRIMINATING_EVIDENCE_SURFACE"
    ) in cl_section
    assert f"SURFACE_ID={SURFACE_ID}" in cl_section
    assert "SURFACE_BINDING_STATUS=BOUND" in cl_section
    assert "ARTIFACT_PRESENT=false" in cl_section
    assert "KIND_SET=EMPTY_FAIL_CLOSED" in cl_section
    assert "KIND_SET_RESOLVED=false" in cl_section
    assert "CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING=false" in cl_section
    assert "U04_STATUS=UNRESOLVED" in cl_section
    assert "U05_STATUS=REMAIN_UNKNOWN" in cl_section
    assert "U06_STATUS=REMAIN_UNKNOWN" in cl_section
    assert "RESIDUAL_STATUS=REMAIN_UNKNOWN" in cl_section
    assert "DURABLE_UNKNOWN_NOT_INCLUDE=true" in cl_section
    assert "DURABLE_UNKNOWN_NOT_EXCLUDE=true" in cl_section
    assert "NO_GET_REQUIRED=true" in cl_section
    assert "NO_HOPE_GET=true" in cl_section
    assert "ACTUAL_GET_COUNT=0" in cl_section
    assert "PREVIOUS_OWNER_SUPPLY_ASSUMPTION=OPERATIONALIZED" in cl_section
    assert "FIRST_DEFINITIVE_BLOCK=NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING" in cl_section
    assert EXACT_MISSING_PREDICATE in cl_section
    assert BLOCKER_ID in cl_section
    assert PARENT_BLOCKER_ID in cl_section
    assert NEXT_OWNER_GO in cl_section
    assert NEXT_PRODUCTIVE_NODE in cl_section
    assert "CURRENT_CANONICAL_SECTION=11.2.1.CL" in cl_section
    assert ("DOCS_TOKEN_FULL_CORE_ACCOUNT_EQUITY_NEW_DISCRIMINATING_EVIDENCE_SURFACE_V1") in spec
    assert "FULL_CORE_ACCOUNT_EQUITY_NEW_DISCRIMINATING_EVIDENCE_SURFACE_V1.md" in mot
    assert CL_HEADING in mot
    assert "11.2.1.CL" in atlas
    assert "account_equity_new_discriminating_evidence_surface_v1.py" in atlas
    assert "ATLAS_AUTHORITY=NONE" in atlas
