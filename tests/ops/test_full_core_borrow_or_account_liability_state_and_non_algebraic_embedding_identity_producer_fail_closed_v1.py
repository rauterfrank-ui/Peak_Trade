"""Borrow/account-liability-state producer tests.

No GET. No POST. No GATE_A retry. No bills/fills relabel. Snapshot, fee,
fill, and algebraic residual rows are not liability events. UNKNOWN remains
first-class. U05 remains REMAIN_UNKNOWN.
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
    ARCHITECTURE_BLOCKER,
    BLOCKER_ID,
    CANONICAL_PACK_RELPATH,
    CANONICAL_PERSIST_AS_OF,
    CLASSIFICATION_NOT_EVENT,
    CLASSIFICATION_UNKNOWN,
    DECISION_BASIS,
    EXPECTED_ORIGIN_MAIN_SHA,
    EXISTING_PRODUCER_ID,
    LIABILITY_IDENTITY_MODEL,
    NEXT_OWNER_GO,
    OWNER_GO,
    PRIMARY_PROOF_STATUS,
    PRODUCER_ID,
    PRODUCER_STATUS,
    RawSourceObservationV1,
    SOURCE_ALGEBRAIC_RESIDUAL,
    SOURCE_BALANCE_SNAPSHOT,
    SOURCE_FEE_DELTA,
    SOURCE_INDEPENDENT_EVENT,
    SOURCE_TRADE_FILL,
    SOURCE_UNKNOWN,
    SOURCE_VENUE_BILL,
    BorrowOrAccountLiabilityStateProducerError,
    assess_non_algebraic_embedding_identity_v1,
    build_borrow_or_account_liability_state_v1,
    classify_raw_source_observation_v1,
    evaluate_u05_eligibility_from_liability_state_v1,
    execute_borrow_or_account_liability_state_and_non_algebraic_embedding_identity_producer_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    ACCOUNT_BILLS_REMAINS_CURRENT_NONCANONICAL,
    EVENT_ACQUISITION_NETWORK_GET_AUTHORIZED,
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
from src.ops.governed_productive_account_equity_authority_producer_v1.scoped_read_only_observation_boundary_contract_v1 import (
    DATA_CLASS_BORROW_OR_ACCOUNT_LIABILITY_STATE,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.u05_concrete_primary_proof_get_surface_binding_v1 import (
    NEXT_OWNER_GO as PARENT_CA_NEXT_OWNER_GO,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
SPEC_PATH = (
    REPO_ROOT / "docs/ops/specs/FULL_CORE_BORROW_OR_ACCOUNT_LIABILITY_STATE_AND_NON_ALGEBRAIC_"
    "EMBEDDING_IDENTITY_PRODUCER_FAIL_CLOSED_V1.md"
)
MOT_PATH = REPO_ROOT / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md"
ATLAS_PATH = REPO_ROOT / "docs/system_atlas/entities/catalog.yaml"
GENESIS_STORE = (
    REPO_ROOT / "evidence/ops/full_core_d6_path_b_d4_d5_genesis_rebaseline_v1/2026-09-13T170318Z"
)
CANONICAL_PACK = REPO_ROOT / CANONICAL_PACK_RELPATH
CB_HEADING = (
    "11.2.1.CB FULL_CORE_BORROW_OR_ACCOUNT_LIABILITY_STATE_AND_NON_ALGEBRAIC_"
    "EMBEDDING_IDENTITY_PRODUCER_FAIL_CLOSED"
)


def _cb_section() -> str:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    start = runbook.index(CB_HEADING)
    return runbook[start : runbook.index("## 11.3 Autonomy state model", start)]


def _copy_genesis(tmp_path: Path) -> Path:
    dest = tmp_path / "genesis"
    shutil.copytree(GENESIS_STORE, dest)
    return dest


def _raw(
    *,
    source_class: str,
    field: str = "liab",
    token: str = "",
    account: str = "acct-1",
    time_as_of: str = "t-1",
    currency: str = "USDC",
    digest: str = "d1",
) -> RawSourceObservationV1:
    return RawSourceObservationV1(
        source_class=source_class,
        surface_id="TEST_SURFACE",
        raw_field=field,
        raw_token=token,
        raw_row_digest=digest,
        account_identity_ref=account,
        time_as_of=time_as_of,
        currency=currency,
        provenance_digest=digest,
    )


def _run(*, tmp_path: Path, vault_file: Path | None = None):
    genesis = _copy_genesis(tmp_path)
    return (
        execute_borrow_or_account_liability_state_and_non_algebraic_embedding_identity_producer_v1(
            owner_go=OWNER_GO,
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            evidence_root=tmp_path / "obs",
            repo_root=REPO_ROOT,
            genesis_store_root=genesis,
            vault_file=vault_file or (tmp_path / "missing_vault.json"),
            persist_as_of=CANONICAL_PERSIST_AS_OF,
        )
    )


def test_wrong_owner_go_fail_closes_without_writing(tmp_path: Path) -> None:
    genesis = _copy_genesis(tmp_path)
    with pytest.raises(BorrowOrAccountLiabilityStateProducerError, match="OWNER_GO_MISMATCH"):
        execute_borrow_or_account_liability_state_and_non_algebraic_embedding_identity_producer_v1(
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
        BorrowOrAccountLiabilityStateProducerError, match="ORIGIN_MAIN_SHA_MISMATCH"
    ):
        execute_borrow_or_account_liability_state_and_non_algebraic_embedding_identity_producer_v1(
            owner_go=OWNER_GO,
            origin_main_sha="0" * 40,
            evidence_root=tmp_path / "obs",
            repo_root=REPO_ROOT,
            genesis_store_root=genesis,
            persist_as_of=CANONICAL_PERSIST_AS_OF,
        )
    assert not (tmp_path / "obs").exists()


def test_snapshot_token_is_not_liability_event() -> None:
    classified = classify_raw_source_observation_v1(
        observation=_raw(source_class=SOURCE_BALANCE_SNAPSHOT, token=""),
        expected_account_identity_ref="acct-1",
        expected_time_as_of="t-1",
        expected_currency="USDC",
    )
    assert classified.classification == CLASSIFICATION_NOT_EVENT
    assert classified.liability_exists == "UNKNOWN"
    assert classified.liability_identity == "UNKNOWN"
    assert "BALANCE_SNAPSHOT" in classified.classification_reason


def test_bills_and_fee_and_fill_are_not_liability() -> None:
    bills = classify_raw_source_observation_v1(
        observation=_raw(source_class=SOURCE_VENUE_BILL, field="type", token="8"),
        expected_account_identity_ref="acct-1",
        expected_time_as_of="t-1",
        expected_currency="USDC",
    )
    fee = classify_raw_source_observation_v1(
        observation=_raw(source_class=SOURCE_FEE_DELTA, field="fee", token="0.01"),
        expected_account_identity_ref="acct-1",
        expected_time_as_of="t-1",
        expected_currency="USDC",
    )
    fill = classify_raw_source_observation_v1(
        observation=_raw(source_class=SOURCE_TRADE_FILL, field="fillPx", token="1"),
        expected_account_identity_ref="acct-1",
        expected_time_as_of="t-1",
        expected_currency="USDC",
    )
    assert bills.classification == CLASSIFICATION_NOT_EVENT
    assert fee.classification == CLASSIFICATION_NOT_EVENT
    assert fill.classification == CLASSIFICATION_NOT_EVENT
    assert "FEE_OR_EXOGENOUS" in bills.classification_reason
    assert "FEE_DELTA" in fee.classification_reason
    assert "TRADE_EXECUTION" in fill.classification_reason


def test_unknown_source_and_independent_unratified_remain_unknown() -> None:
    unknown = classify_raw_source_observation_v1(
        observation=_raw(source_class=SOURCE_UNKNOWN),
        expected_account_identity_ref="acct-1",
        expected_time_as_of="t-1",
        expected_currency="USDC",
    )
    independent = classify_raw_source_observation_v1(
        observation=_raw(source_class=SOURCE_INDEPENDENT_EVENT, field="BORROW_OPEN"),
        expected_account_identity_ref="acct-1",
        expected_time_as_of="t-1",
        expected_currency="USDC",
    )
    assert unknown.classification == CLASSIFICATION_UNKNOWN
    assert independent.classification == CLASSIFICATION_UNKNOWN
    assert unknown.liability_exists == "UNKNOWN"
    assert independent.liability_exists == "UNKNOWN"
    assert "NOT_IN_RATIFIED_KIND_SET" in independent.classification_reason


def test_account_time_currency_mismatch_fail_closes_unknown() -> None:
    classified = classify_raw_source_observation_v1(
        observation=_raw(source_class=SOURCE_BALANCE_SNAPSHOT),
        expected_account_identity_ref="other-acct",
        expected_time_as_of="other-time",
        expected_currency="EUR",
    )
    assert classified.classification == CLASSIFICATION_UNKNOWN
    assert "SCOPE_IDENTITY_MISMATCH" in classified.classification_reason
    assert classified.account_scope_identity_status == "ACCOUNT_MISMATCH"
    assert classified.time_scope_identity_status == "TIME_MISMATCH"
    assert classified.currency_scope_identity_status == "CURRENCY_MISMATCH"


def test_algebraic_residual_cannot_prove_embedding() -> None:
    classified = classify_raw_source_observation_v1(
        observation=_raw(source_class=SOURCE_ALGEBRAIC_RESIDUAL),
        expected_account_identity_ref="acct-1",
        expected_time_as_of="t-1",
        expected_currency="USDC",
    )
    embedding = assess_non_algebraic_embedding_identity_v1(
        classification=classified,
        algebraic_eq_identity_used="true",
        embedding_witness_id="",
        claimed_embedding_state="SEPARATE",
    )
    assert classified.classification == CLASSIFICATION_UNKNOWN
    assert embedding.non_algebraic_embedding_identity == "UNKNOWN"
    assert embedding.algebraic_eq_identity_used == "true"
    assert embedding.liability_event_identity_proven == "false"
    assert embedding.p01_u05_overlap_disproven == "false"
    assert "ALGEBRAIC_EQ_IDENTITY_FORBIDDEN" in embedding.assessment_reason


def test_claimed_separate_without_witness_remains_unknown() -> None:
    classified = classify_raw_source_observation_v1(
        observation=_raw(source_class=SOURCE_INDEPENDENT_EVENT, field="BORROW_OPEN"),
        expected_account_identity_ref="acct-1",
        expected_time_as_of="t-1",
        expected_currency="USDC",
    )
    embedding = assess_non_algebraic_embedding_identity_v1(
        classification=classified,
        algebraic_eq_identity_used="false",
        embedding_witness_id="",
        claimed_embedding_state="SEPARATE",
    )
    assert embedding.non_algebraic_embedding_identity == "UNKNOWN"
    assert embedding.equity_stock_effect_proven == "false"
    assert embedding.once_only_stock_effect_proven == "false"


def test_u05_eligibility_from_snapshot_and_bills_is_nonqualifying() -> None:
    snapshot_obs = _raw(source_class=SOURCE_BALANCE_SNAPSHOT)
    snapshot_cls = classify_raw_source_observation_v1(
        observation=snapshot_obs,
        expected_account_identity_ref="acct-1",
        expected_time_as_of="t-1",
        expected_currency="USDC",
    )
    snapshot_state = build_borrow_or_account_liability_state_v1(
        observation=snapshot_obs,
        classification=snapshot_cls,
        bound_account_identity="acct-1",
        checkpoint_as_of="t-1",
    )
    snapshot_embed = assess_non_algebraic_embedding_identity_v1(
        classification=snapshot_cls,
        algebraic_eq_identity_used="false",
        embedding_witness_id="",
        claimed_embedding_state="UNKNOWN",
    )
    snapshot_elig = evaluate_u05_eligibility_from_liability_state_v1(
        state=snapshot_state,
        embedding=snapshot_embed,
    )
    bills_obs = _raw(source_class=SOURCE_VENUE_BILL, field="type", token="8")
    bills_cls = classify_raw_source_observation_v1(
        observation=bills_obs,
        expected_account_identity_ref="acct-1",
        expected_time_as_of="t-1",
        expected_currency="USDC",
    )
    bills_state = build_borrow_or_account_liability_state_v1(
        observation=bills_obs,
        classification=bills_cls,
        bound_account_identity="acct-1",
        checkpoint_as_of="t-1",
    )
    bills_embed = assess_non_algebraic_embedding_identity_v1(
        classification=bills_cls,
        algebraic_eq_identity_used="false",
        embedding_witness_id="",
        claimed_embedding_state="UNKNOWN",
    )
    bills_elig = evaluate_u05_eligibility_from_liability_state_v1(
        state=bills_state,
        embedding=bills_embed,
    )
    assert snapshot_state.data_class == DATA_CLASS_BORROW_OR_ACCOUNT_LIABILITY_STATE
    assert snapshot_elig["law_outcome"] == OUTCOME_NONQUALIFYING
    assert bills_elig["law_outcome"] == OUTCOME_NONQUALIFYING
    assert snapshot_elig["u05_decision"] == DECISION_REMAIN_UNKNOWN
    assert bills_state.canonical_status == "NOT_CANONICAL_LIABILITY_IDENTITY"


def test_empty_zero_absent_is_not_exclude() -> None:
    outcome = evaluate_u05_primary_proof_v1(proof={})
    assert outcome.outcome == OUTCOME_NONQUALIFYING
    assert outcome.evidence_class_id == CLASS_U05


def test_execute_persists_typed_producer_without_get(tmp_path: Path) -> None:
    result = _run(tmp_path=tmp_path)
    claims = json.loads((Path(result.store_root) / "claims.json").read_text(encoding="utf-8"))
    census = json.loads(
        (Path(result.store_root) / "producer_census_v1.json").read_text(encoding="utf-8")
    )
    contract = json.loads(
        (Path(result.store_root) / "producer_contract_v1.json").read_text(encoding="utf-8")
    )
    predicates = json.loads(
        (Path(result.store_root) / "predicate_adjudication_v1.json").read_text(encoding="utf-8")
    )
    evaluation = json.loads(
        (Path(result.store_root) / "current_proof_evaluation_v1.json").read_text(encoding="utf-8")
    )
    assert result.producer_id == PRODUCER_ID
    assert result.producer_status == PRODUCER_STATUS
    assert result.existing_producer_found == "false"
    assert result.qualifying_liability_event_count == "0"
    assert result.authorized_get_count == "0"
    assert result.actual_get_count == "0"
    assert result.post_count == "0"
    assert result.productive_acquisition_executed == "false"
    assert result.u05_decision_after == DECISION_REMAIN_UNKNOWN
    assert result.non_algebraic_embedding_identity == "UNKNOWN"
    assert claims["EXISTING_PRODUCER_ID"] == EXISTING_PRODUCER_ID
    assert claims["LIABILITY_IDENTITY_MODEL"] == LIABILITY_IDENTITY_MODEL
    assert claims["PARENT_CA_NEXT_OWNER_GO"] == PARENT_CA_NEXT_OWNER_GO
    assert claims["U05_PRIMARY_PROOF_STATUS"] == PRIMARY_PROOF_STATUS
    assert claims["U05_DECISION_BASIS"] == DECISION_BASIS
    assert claims["U06_DECISION_UNCHANGED"] == DECISION_REMAIN_UNKNOWN
    assert claims["RESIDUAL_DECISION_UNCHANGED"] == DECISION_REMAIN_UNKNOWN
    assert claims["VENUE_EQ_SOURCE_AUTHORITY"] == "false"
    assert claims["ACCOUNT_BILLS_CANONICALIZED"] == "false"
    assert claims["GATE_A_REOPENED"] == "false"
    assert claims["GATE_B_REEXECUTED"] == "false"
    assert claims["BLOCKER_ID"] == BLOCKER_ID
    assert claims["ARCHITECTURE_BLOCKER"] == ARCHITECTURE_BLOCKER
    assert claims["NEXT_OWNER_GO_REQUIRED"] == NEXT_OWNER_GO
    assert int(census["classified_observation_count"]) >= 4
    assert census["qualifying_liability_event_count"] == "0"
    classes = {item["source_class"] for item in census["records"]}
    assert SOURCE_BALANCE_SNAPSHOT in classes
    assert SOURCE_VENUE_BILL in classes
    assert SOURCE_TRADE_FILL in classes
    assert SOURCE_FEE_DELTA in classes
    assert SOURCE_ALGEBRAIC_RESIDUAL in classes
    for item in census["records"]:
        assert item["classification"]["liability_exists"] == "UNKNOWN"
        assert item["eligibility"]["law_outcome"] == OUTCOME_NONQUALIFYING
        if item["source_class"] == SOURCE_ALGEBRAIC_RESIDUAL:
            assert item["embedding"]["non_algebraic_embedding_identity"] == "UNKNOWN"
    assert contract["endpoint_selected"] == "false"
    assert contract["unknown_first_class"] == "true"
    assert predicates["double_counting_guard_proven"] == "true"
    assert predicates["independent_liability_event_proven"] == "false"
    assert evaluation["concrete_get_surface_discovered"] == "false"
    assert evaluation["surface_binding_status"] == "NOT_BOUND"
    assert verify_manifest_sha256_v1(store_root=result.store_root) == 0
    files = {path.name for path in Path(result.store_root).iterdir() if path.is_file()}
    assert "raw_http_capture_v1.json" not in files
    assert "raw_account_balance_response_body.json" not in files


def test_canonical_pack_sealed_and_replay_stable() -> None:
    claims = json.loads((CANONICAL_PACK / "claims.json").read_text(encoding="utf-8"))
    assert claims["U05_DECISION_AFTER"] == DECISION_REMAIN_UNKNOWN
    assert claims["PRODUCTIVE_ACQUISITION_EXECUTED"] == "false"
    assert claims["QUALIFYING_LIABILITY_EVENT_COUNT"] == "0"
    assert claims["BORROW_OR_ACCOUNT_LIABILITY_STATE_PRODUCER_STATUS"] == PRODUCER_STATUS
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


def test_runbook_cb_persists_typed_producer() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    mot = MOT_PATH.read_text(encoding="utf-8")
    atlas = ATLAS_PATH.read_text(encoding="utf-8")
    cb_section = _cb_section()
    assert OWNER_GO in cb_section
    assert (
        "THIS_SLICE=11.2.1.CB.FULL_CORE_BORROW_OR_ACCOUNT_LIABILITY_STATE_AND_"
        "NON_ALGEBRAIC_EMBEDDING_IDENTITY_PRODUCER_FAIL_CLOSED" in cb_section
    )
    assert "EXISTING_PRODUCER_FOUND=false" in cb_section
    assert PRODUCER_STATUS in cb_section
    assert "QUALIFYING_LIABILITY_EVENT_COUNT=0" in cb_section
    assert "AUTHORIZED_GET_COUNT=0" in cb_section
    assert "ACTUAL_GET_COUNT=0" in cb_section
    assert "POST_COUNT=0" in cb_section
    assert "PRODUCTIVE_ACQUISITION_EXECUTED=false" in cb_section
    assert "U05_DECISION_AFTER=REMAIN_UNKNOWN" in cb_section
    assert "U06_DECISION_UNCHANGED=REMAIN_UNKNOWN" in cb_section
    assert "RESIDUAL_DECISION_UNCHANGED=REMAIN_UNKNOWN" in cb_section
    assert "NON_ALGEBRAIC_EMBEDDING_IDENTITY=UNKNOWN" in cb_section
    assert "VENUE_EQ_SOURCE_AUTHORITY=false" in cb_section
    assert "ACCOUNT_BILLS_CANONICALIZED=false" in cb_section
    assert BLOCKER_ID in cb_section
    assert NEXT_OWNER_GO in cb_section
    assert ARCHITECTURE_BLOCKER in cb_section
    assert EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY in cb_section
    assert "CURRENT_CANONICAL_SECTION=11.2.1.CB" in cb_section
    assert (
        "DOCS_TOKEN_FULL_CORE_BORROW_OR_ACCOUNT_LIABILITY_STATE_AND_NON_ALGEBRAIC_"
        "EMBEDDING_IDENTITY_PRODUCER_FAIL_CLOSED_V1" in spec
    )
    assert (
        "FULL_CORE_BORROW_OR_ACCOUNT_LIABILITY_STATE_AND_NON_ALGEBRAIC_"
        "EMBEDDING_IDENTITY_PRODUCER_FAIL_CLOSED_V1.md" in mot
    )
    assert CB_HEADING in mot
    assert "11.2.1.CB" in atlas
    assert (
        "borrow_or_account_liability_state_and_non_algebraic_embedding_identity_"
        "producer_v1.py" in atlas
    )
    assert "ATLAS_AUTHORITY=NONE" in atlas
    assert U05_KIND_DECISION == DECISION_REMAIN_UNKNOWN
    assert U06_KIND_DECISION == DECISION_REMAIN_UNKNOWN
    assert RESIDUAL_KIND_DECISION == DECISION_REMAIN_UNKNOWN
    assert ACCOUNT_BILLS_REMAINS_CURRENT_NONCANONICAL is True
    assert EVENT_ACQUISITION_NETWORK_GET_AUTHORIZED is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert WIRE_SEND_PERMITTED is False
    assert MS2_AUTHORIZED is False
    assert EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY == (
        "NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING"
    )
