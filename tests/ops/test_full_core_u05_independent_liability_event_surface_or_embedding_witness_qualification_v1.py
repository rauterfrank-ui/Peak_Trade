"""U05 independent liability-event surface qualification tests.

No GET. No POST. Prior four surfaces remain excluded. acctLv=2 is not a
standalone disqualifier. The selected EVENT_SURFACE is not an embedding
witness. liab/totalLiab values cannot prove P01/U05 overlap. U05 remains
REMAIN_UNKNOWN.
"""

from __future__ import annotations

import hashlib
import json
import shutil
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
    CLASS_U05,
    OUTCOME_NONQUALIFYING,
    evaluate_u05_primary_proof_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.borrow_or_account_liability_state_and_non_algebraic_embedding_identity_producer_v1 import (
    PRODUCER_ID,
    PRODUCER_STATUS,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    ACCOUNT_BILLS_REMAINS_CURRENT_NONCANONICAL,
    EVENT_ACQUISITION_NETWORK_GET_AUTHORIZED,
    RESIDUAL_KIND_DECISION,
    U05_KIND_DECISION,
    U06_KIND_DECISION,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.f12_f13_kind_set_remaining_unknown_pin_and_reopen_gate_v1 import (
    SELECTED_BALANCE_SURFACE,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.named_remaining_unknown_kind_set_evidence_persist_contract_v1 import (
    DECISION_REMAIN_UNKNOWN,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_s6_mapping_classification_v1 import (
    verify_manifest_sha256_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.scoped_read_only_observation_boundary_contract_v1 import (
    CANDIDATE_SURFACE_ACCOUNT_BILLS,
    CANDIDATE_SURFACE_TRADE_FILLS,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.u05_independent_liability_event_and_non_algebraic_embedding_identity_primary_proof_acquisition_v1 import (
    CANDIDATE_SURFACE_BILLS_ARCHIVE,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.u05_independent_liability_event_surface_or_embedding_witness_qualification_v1 import (
    ARCHITECTURE_BLOCKER,
    BINDING_STATUS,
    BLOCKER_ID,
    CANONICAL_PACK_RELPATH,
    CANONICAL_PERSIST_AS_OF,
    DECISION_BASIS,
    EXPECTED_ORIGIN_MAIN_SHA,
    FUTURE_MAX_GET_COUNT,
    HTTP_METHOD,
    NEXT_OWNER_GO,
    OWNER_GO,
    PARENT_CB_NEXT_OWNER_GO,
    PRIMARY_PROOF_ROLE,
    PRIMARY_PROOF_STATUS,
    PRIOR_FOUR_SURFACES,
    SELECTED_CANDIDATE_KIND,
    SELECTED_SURFACE_ID,
    U05IndependentLiabilityEventSurfaceQualificationError,
    build_bounded_candidate_census_v1,
    build_pre_acquisition_contract_v1,
    evaluate_selected_event_surface_predicates_v1,
    execute_u05_independent_liability_event_surface_or_embedding_witness_qualification_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
SPEC_PATH = (
    REPO_ROOT / "docs/ops/specs/FULL_CORE_U05_INDEPENDENT_LIABILITY_EVENT_SURFACE_OR_"
    "EMBEDDING_WITNESS_QUALIFICATION_V1.md"
)
MOT_PATH = REPO_ROOT / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md"
ATLAS_PATH = REPO_ROOT / "docs/system_atlas/entities/catalog.yaml"
GENESIS_STORE = (
    REPO_ROOT / "evidence/ops/full_core_d6_path_b_d4_d5_genesis_rebaseline_v1/2026-09-13T170318Z"
)
CANONICAL_PACK = REPO_ROOT / CANONICAL_PACK_RELPATH
CC_HEADING = (
    "11.2.1.CC FULL_CORE_U05_INDEPENDENT_LIABILITY_EVENT_SURFACE_OR_EMBEDDING_WITNESS_QUALIFICATION"
)
SOURCE_PATH = (
    "src/ops/governed_productive_account_equity_authority_producer_v1/"
    "u05_independent_liability_event_surface_or_embedding_witness_qualification_v1.py"
)


def _cc_section() -> str:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    start = runbook.index(CC_HEADING)
    cd = "11.2.1.CD FULL_CORE_U05_PRIMARY_PROOF_BOUND_INTEREST_ACCRUED_GET_ACQUISITION"
    end = runbook.find(cd, start)
    if end < 0:
        end = runbook.index("## 11.3 Autonomy state model", start)
    return runbook[start:end]


def _copy_genesis(tmp_path: Path) -> Path:
    dest = tmp_path / "genesis"
    shutil.copytree(GENESIS_STORE, dest)
    return dest


def _run(*, tmp_path: Path, vault_file: Path | None = None):
    genesis = _copy_genesis(tmp_path)
    return execute_u05_independent_liability_event_surface_or_embedding_witness_qualification_v1(
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        evidence_root=tmp_path / "obs",
        repo_root=REPO_ROOT,
        genesis_store_root=genesis,
        vault_file=vault_file or (tmp_path / "missing_vault.json"),
        persist_as_of=CANONICAL_PERSIST_AS_OF,
    )


def test_wrong_owner_go_fail_closes_without_writing(tmp_path: Path) -> None:
    genesis = _copy_genesis(tmp_path)
    with pytest.raises(
        U05IndependentLiabilityEventSurfaceQualificationError, match="OWNER_GO_MISMATCH"
    ):
        execute_u05_independent_liability_event_surface_or_embedding_witness_qualification_v1(
            owner_go="WRONG_GO",
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            evidence_root=tmp_path / "obs",
            repo_root=REPO_ROOT,
            genesis_store_root=genesis,
            persist_as_of=CANONICAL_PERSIST_AS_OF,
        )
    assert not (tmp_path / "obs").exists()


def test_wrong_origin_sha_fail_closes_without_writing(tmp_path: Path) -> None:
    genesis = _copy_genesis(tmp_path)
    with pytest.raises(
        U05IndependentLiabilityEventSurfaceQualificationError, match="ORIGIN_MAIN_SHA_MISMATCH"
    ):
        execute_u05_independent_liability_event_surface_or_embedding_witness_qualification_v1(
            owner_go=OWNER_GO,
            origin_main_sha="0" * 40,
            evidence_root=tmp_path / "obs",
            repo_root=REPO_ROOT,
            genesis_store_root=genesis,
            persist_as_of=CANONICAL_PERSIST_AS_OF,
        )
    assert not (tmp_path / "obs").exists()


def test_prior_four_remain_excluded_and_are_not_the_selected_surface() -> None:
    assert PRIOR_FOUR_SURFACES == (
        SELECTED_BALANCE_SURFACE,
        CANDIDATE_SURFACE_ACCOUNT_BILLS,
        CANDIDATE_SURFACE_BILLS_ARCHIVE,
        CANDIDATE_SURFACE_TRADE_FILLS,
    )
    census = build_bounded_candidate_census_v1()
    selected_ids = {item["surface_id"] for item in census["records"] if item["selected"] == "true"}
    inspected_ids = {item["surface_id"] for item in census["records"]}
    assert selected_ids == {SELECTED_SURFACE_ID}
    assert SELECTED_SURFACE_ID not in PRIOR_FOUR_SURFACES
    assert inspected_ids.isdisjoint(set(PRIOR_FOUR_SURFACES))
    assert census["prior_four_candidates_excluded"] == "true"
    assert census["acctlv2_alone_is_not_a_disqualifier"] == "true"
    assert census["selected_candidate_kind"] == SELECTED_CANDIDATE_KIND


def test_selected_predicates_do_not_claim_embedding_or_equity_stock_effect() -> None:
    adjudication = evaluate_selected_event_surface_predicates_v1()
    predicates = adjudication["predicates"]
    assert adjudication["surface_or_witness_bindable"] == "true"
    assert adjudication["acctlv2_alone_used_as_disqualifier"] == "false"
    assert adjudication["margin_under_futures_mode_documented"] == "true"
    assert adjudication["current_bound_account_margin_loan_presence"] == "UNKNOWN"
    assert predicates["read_only_proven"] == "true"
    assert predicates["liability_identity_capability"] == "true"
    assert predicates["non_algebraic_embedding_capability"] == "false"
    assert predicates["equity_stock_effect_capability"] == "false"
    assert predicates["once_only_effect_capability"] == "false"
    assert predicates["independence_from_reconstruction_algebra"] == "true"
    reason = predicates and adjudication["predicate_reasons"]["non_algebraic_embedding_capability"]
    assert "LIAB_TOTALLIAB_VALUES_MUST_NOT_BE_USED_TO_INFER_P01_U05_OVERLAP" in reason


def test_pre_acquisition_contract_forbids_get_and_algebraic_embedding() -> None:
    contract = build_pre_acquisition_contract_v1(
        d4_identity_digest="acct-digest",
        d5_binding_id="window-1",
    )
    assert contract["http_method"] == HTTP_METHOD
    assert contract["endpoint_path"] == "/api/v5/account/interest-accrued"
    assert contract["productive_acquisition_authorized"] == "false"
    assert contract["authorized_get_count"] == "0"
    assert contract["actual_get_count"] == "0"
    assert contract["post_count"] == "0"
    assert contract["retry_allowed"] == "false"
    assert contract["future_max_get_count_if_separately_authorized"] == FUTURE_MAX_GET_COUNT
    assert contract["acquisition_forbidden_in_this_workpackage"] == "true"
    assert contract["embedding_witness_bound"] == "false"
    assert contract["primary_proof_role_bound"] == PRIMARY_PROOF_ROLE
    assert (
        "NO_P01_U05_OVERLAP_INFERENCE_FROM_LIAB_OR_TOTALLIAB" in contract["eligibility_predicates"]
    )


def test_empty_zero_absent_is_not_exclude() -> None:
    outcome = evaluate_u05_primary_proof_v1(proof={})
    assert outcome.outcome == OUTCOME_NONQUALIFYING
    assert outcome.evidence_class_id == CLASS_U05


def test_execute_binds_pre_acquisition_contract_without_get(tmp_path: Path) -> None:
    result = _run(tmp_path=tmp_path)
    claims = json.loads((Path(result.store_root) / "claims.json").read_text(encoding="utf-8"))
    census = json.loads(
        (Path(result.store_root) / "candidate_census_v1.json").read_text(encoding="utf-8")
    )
    contract = json.loads(
        (Path(result.store_root) / "pre_acquisition_contract_v1.json").read_text(encoding="utf-8")
    )
    evaluation = json.loads(
        (Path(result.store_root) / "current_proof_evaluation_v1.json").read_text(encoding="utf-8")
    )
    predicates = json.loads(
        (Path(result.store_root) / "predicate_adjudication_v1.json").read_text(encoding="utf-8")
    )
    assert result.selected_single_candidate_id == SELECTED_SURFACE_ID
    assert result.selected_candidate_kind == SELECTED_CANDIDATE_KIND
    assert result.surface_or_witness_bindable == "true"
    assert result.binding_status == BINDING_STATUS
    assert result.authorized_get_count == "0"
    assert result.actual_get_count == "0"
    assert result.post_count == "0"
    assert result.future_max_get_count_if_separately_authorized == FUTURE_MAX_GET_COUNT
    assert result.productive_acquisition_executed == "false"
    assert result.u05_decision_after == DECISION_REMAIN_UNKNOWN
    assert claims["PARENT_CB_NEXT_OWNER_GO"] == PARENT_CB_NEXT_OWNER_GO
    assert claims["PRIOR_FOUR_CANDIDATES_EXCLUDED"] == "true"
    assert claims["VENUE_CAPABILITY_PROVEN"] == "true"
    assert claims["READ_ONLY_PROVEN"] == "true"
    assert claims["SURFACE_OR_WITNESS_BINDABLE"] == "true"
    assert claims["PRIMARY_PROOF_ROLE_BOUND"] == PRIMARY_PROOF_ROLE
    assert claims["INDEPENDENT_LIABILITY_EVENT_PROVEN"] == "false"
    assert claims["NON_ALGEBRAIC_EMBEDDING_IDENTITY"] == "UNKNOWN"
    assert claims["P01_U05_OVERLAP_DISPROVEN"] == "false"
    assert claims["U05_PRIMARY_PROOF_STATUS"] == PRIMARY_PROOF_STATUS
    assert claims["U05_DECISION_BASIS"] == DECISION_BASIS
    assert claims["U06_DECISION_UNCHANGED"] == DECISION_REMAIN_UNKNOWN
    assert claims["RESIDUAL_DECISION_UNCHANGED"] == DECISION_REMAIN_UNKNOWN
    assert claims["VENUE_EQ_SOURCE_AUTHORITY"] == "false"
    assert claims["ACCOUNT_BILLS_CANONICALIZED"] == "false"
    assert claims["ACCTLV2_ALONE_USED_AS_DISQUALIFIER"] == "false"
    assert claims["BORROW_OR_ACCOUNT_LIABILITY_STATE_PRODUCER_STATUS"] == PRODUCER_STATUS
    assert claims["PRODUCER_ID"] == PRODUCER_ID
    assert claims["BLOCKER_ID"] == BLOCKER_ID
    assert claims["ARCHITECTURE_BLOCKER"] == ARCHITECTURE_BLOCKER
    assert claims["NEXT_OWNER_GO_REQUIRED"] == NEXT_OWNER_GO
    assert census["candidate_census_count"] == "5"
    assert census["selected_single_candidate_id"] == SELECTED_SURFACE_ID
    assert contract["actual_get_count"] == "0"
    assert contract["post_count"] == "0"
    assert evaluation["surface_binding_status"] == BINDING_STATUS
    assert predicates["p01_u05_overlap_disproven"] == "false"
    assert predicates["liab_totalLiab_must_not_prove_embedding"] == "true"
    assert verify_manifest_sha256_v1(store_root=result.store_root) == 0
    files = {path.name for path in Path(result.store_root).iterdir() if path.is_file()}
    assert "raw_http_capture_v1.json" not in files
    assert "raw_interest_accrued_response_body.json" not in files


def test_canonical_pack_sealed_and_replay_stable() -> None:
    claims = json.loads((CANONICAL_PACK / "claims.json").read_text(encoding="utf-8"))
    assert claims["U05_DECISION_AFTER"] == DECISION_REMAIN_UNKNOWN
    assert claims["PRODUCTIVE_ACQUISITION_EXECUTED"] == "false"
    assert claims["SELECTED_SINGLE_CANDIDATE_ID"] == SELECTED_SURFACE_ID
    assert claims["SURFACE_BINDING_STATUS"] == BINDING_STATUS
    assert claims["ACTUAL_GET_COUNT"] == "0"
    assert claims["POST_COUNT"] == "0"
    assert verify_manifest_sha256_v1(store_root=CANONICAL_PACK) == 0
    expected: dict[str, str] = {}
    for line in (CANONICAL_PACK / "MANIFEST.sha256").read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, name = line.split("  ", 1)
        expected[name] = digest
    actual = {
        path.name
        for path in CANONICAL_PACK.iterdir()
        if path.is_file() and path.name != "MANIFEST.sha256"
    }
    assert set(expected) == actual
    for name, digest in expected.items():
        assert hashlib.sha256((CANONICAL_PACK / name).read_bytes()).hexdigest() == digest


def test_source_does_not_perform_network_or_reopen_prior_four() -> None:
    source = (REPO_ROOT / SOURCE_PATH).read_text(encoding="utf-8")
    assert "httpx" not in source
    assert "requests" not in source
    assert "urllib" not in source
    assert "interest-accrued" in source
    assert "SELECTED_BALANCE_SURFACE" in source
    assert "CANDIDATE_SURFACE_ACCOUNT_BILLS" in source
    assert "CANDIDATE_SURFACE_BILLS_ARCHIVE" in source
    assert "CANDIDATE_SURFACE_TRADE_FILLS" in source
    assert "PRIOR_FOUR_SURFACES" in source
    assert "acctlv2_alone_is_not_a_disqualifier" in source
    assert "Does not use acctLv=2 as a standalone disqualifier." in source


def test_runbook_cc_persists_pre_acquisition_binding() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    mot = MOT_PATH.read_text(encoding="utf-8")
    atlas = ATLAS_PATH.read_text(encoding="utf-8")
    cc_section = _cc_section()
    assert OWNER_GO in cc_section
    assert (
        "THIS_SLICE=11.2.1.CC.FULL_CORE_U05_INDEPENDENT_LIABILITY_EVENT_SURFACE_OR_"
        "EMBEDDING_WITNESS_QUALIFICATION" in cc_section
    )
    assert "SELECTED_CANDIDATE_KIND=EVENT_SURFACE" in cc_section
    assert "PRIOR_FOUR_CANDIDATES_EXCLUDED=true" in cc_section
    assert "GET_&#47;api&#47;v5&#47;account&#47;interest-accrued" in cc_section
    assert "SURFACE_BINDING_STATUS=PRE_ACQUISITION_CONTRACT_BOUND" in cc_section
    assert "PRODUCTIVE_ACQUISITION_AUTHORIZED=false" in cc_section
    assert "AUTHORIZED_GET_COUNT=0" in cc_section
    assert "ACTUAL_GET_COUNT=0" in cc_section
    assert "POST_COUNT=0" in cc_section
    assert "FUTURE_MAX_GET_COUNT_IF_SEPARATELY_AUTHORIZED=1" in cc_section
    assert "INDEPENDENT_LIABILITY_EVENT_PROVEN=false" in cc_section
    assert "NON_ALGEBRAIC_EMBEDDING_IDENTITY=UNKNOWN" in cc_section
    assert "U05_DECISION_AFTER=REMAIN_UNKNOWN" in cc_section
    assert "U06_DECISION_UNCHANGED=REMAIN_UNKNOWN" in cc_section
    assert "RESIDUAL_DECISION_UNCHANGED=REMAIN_UNKNOWN" in cc_section
    assert "VENUE_EQ_SOURCE_AUTHORITY=false" in cc_section
    assert "ACCOUNT_BILLS_CANONICALIZED=false" in cc_section
    assert "ACCTLV2_ALONE_USED_AS_DISQUALIFIER=false" in cc_section
    assert BLOCKER_ID in cc_section
    assert NEXT_OWNER_GO in cc_section
    assert ARCHITECTURE_BLOCKER in cc_section
    assert EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY in cc_section
    assert "CURRENT_CANONICAL_SECTION=11.2.1.CC" in cc_section
    assert (
        "DOCS_TOKEN_FULL_CORE_U05_INDEPENDENT_LIABILITY_EVENT_SURFACE_OR_"
        "EMBEDDING_WITNESS_QUALIFICATION_V1" in spec
    )
    assert (
        "FULL_CORE_U05_INDEPENDENT_LIABILITY_EVENT_SURFACE_OR_EMBEDDING_WITNESS_QUALIFICATION_V1.md"
        in mot
    )
    assert CC_HEADING in mot
    assert "11.2.1.CC" in atlas
    assert (
        "u05_independent_liability_event_surface_or_embedding_witness_qualification_v1.py" in atlas
    )
    assert "ATLAS_AUTHORITY=NONE" in atlas
    assert U05_KIND_DECISION == DECISION_REMAIN_UNKNOWN
    assert U06_KIND_DECISION == DECISION_REMAIN_UNKNOWN
    assert RESIDUAL_KIND_DECISION == DECISION_REMAIN_UNKNOWN
    assert ACCOUNT_BILLS_REMAINS_CURRENT_NONCANONICAL is True
    assert EVENT_ACQUISITION_NETWORK_GET_AUTHORIZED is False
    assert LIVE_ENABLED is True
    assert LIVE_ARMED is True
    assert WIRE_SEND_PERMITTED is True
    assert MS2_AUTHORIZED is False
    assert EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY == (
        "NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING"
    )
