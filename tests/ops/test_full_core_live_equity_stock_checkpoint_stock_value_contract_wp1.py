"""NEW_CANONICAL_DEFINITION of checkpoint-bound EQUITY_STOCK_VALUE_V1.

Binds an already-derived stock value to a governed checkpoint. Checkpoint
does not mint. Historical F12/F13/U05/F16/F17/F18 remain UNKNOWN. Today
KIND_SET stays empty because the initial stock anchor is absent.
No GET. GATE_A and GATE_B are not executed.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    KIND_SET_RESOLVED,
    LIVE_ARMED,
    LIVE_ENABLED,
    MS2_AUTHORIZED,
    RAW_EQ_SOURCE_AUTHORITY,
    WIRE_SEND_PERMITTED,
)
from src.ops.full_core_live_path_composition_root_v1.live_admission_gap_dag_v1 import (
    EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.bj_remaining_unknown_kind_semantics_v1 import (
    DECISION_EXCLUDE,
    DECISION_INCLUDE,
    FACT_IDS,
    KIND_SET_EMPTY,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.equity_stock_checkpoint_contract_v1 import (
    EquityStockCheckpointContractError,
    build_equity_stock_checkpoint_contract_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.live_equity_stock_checkpoint_stock_value_contract_v1 import (
    CANONICAL_PACK_RELPATH,
    DERIVATION_OPTION_D_PRIOR_PLUS_STREAM,
    EARLIEST_LIVE_CRITICAL_PATH_BLOCKER,
    EXPECTED_ORIGIN_MAIN_SHA,
    NEXT_OWNER_GO_REQUIRED,
    OWNER_GO,
    REASON_ACCOUNT_SCOPE_MISMATCH,
    REASON_CLAIMED_AVAILABLE_CAPITAL,
    REASON_CLAIMED_CHECKPOINT_MINT,
    REASON_CLAIMED_FLOW_AS_STOCK,
    REASON_CLAIMED_P01_AS_STOCK,
    REASON_CLAIMED_PLACEMENT_CAPACITY,
    REASON_CLAIMED_VENUE_EQ_SOURCE,
    REASON_CONTRADICTORY_FIELD,
    REASON_CURRENCY_SCOPE_MISMATCH,
    REASON_DOUBLE_COUNT_STOCK_AND_FLOW,
    REASON_EMBEDDING_UNRESOLVED,
    REASON_INITIAL_STOCK_ANCHOR_ABSENT,
    REASON_MALFORMED_FIELD,
    REASON_MISSING_FIELD,
    REASON_PRECEDENCE,
    REASON_PRIOR_CHECKPOINT_REQUIRED_MISSING,
    REASON_SEQUENCE_TIME_AMBIGUOUS,
    REASON_VALID,
    REQUIRED_FIELDS,
    SCHEMA_CLASS,
    EquityStockCheckpointStockValueContractError,
    bind_equity_stock_value_to_checkpoint_v1,
    evaluate_equity_stock_value_v1,
    evaluate_today_authoritative_derivation_boundary_v1,
    execute_live_equity_stock_checkpoint_stock_value_contract_v1,
    fixture_valid_stock_value_payload_v1,
    reason_precedence_index_v1,
    reject_claimed_stock_value_authority_mutation_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.live_equity_stock_kind_set_new_canonical_definition_v1 import (
    CANONICAL_PACK_RELPATH as CANONICAL_BN_PACK_RELPATH,
    NEXT_OWNER_GO_REQUIRED as BN_NEXT_OWNER_GO,
    evaluate_today_live_equity_stock_kind_set_v1,
    ratified_live_equity_stock_kind_set_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.named_remaining_unknown_kind_set_evidence_persist_contract_v1 import (
    DECISION_REMAIN_UNKNOWN,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.package_1_s6_mapping_classification_v1 import (
    verify_manifest_sha256_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
SPEC_PATH = (
    REPO_ROOT / "docs/ops/specs/FULL_CORE_LIVE_EQUITY_STOCK_CHECKPOINT_STOCK_VALUE_CONTRACT_WP1.md"
)
MOT_PATH = REPO_ROOT / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md"
ATLAS_PATH = REPO_ROOT / "docs/system_atlas/entities/catalog.yaml"
BJ_HEADING = "11.2.1.BJ FULL_CORE_D6_F12_F13_KIND_SET_REMAINING_UNKNOWN_PIN_AND_REOPEN_GATE"
BK_HEADING = "11.2.1.BK FULL_CORE_D6_BJ_SEMANTICS_BOUNDED_IMPLEMENTATION"
BL_HEADING = "11.2.1.BL FULL_CORE_D6_BK_BOUNDED_IMPLEMENTATION"
BM_HEADING = "11.2.1.BM FULL_CORE_LIVE_CRITICAL_PATH_NEXT_BLOCKER"
BN_HEADING = "11.2.1.BN FULL_CORE_LIVE_EQUITY_STOCK_KIND_SET_NEW_CANONICAL_DEFINITION"
BO_HEADING = "11.2.1.BO FULL_CORE_LIVE_EQUITY_STOCK_CHECKPOINT_STOCK_VALUE_CONTRACT"
SEALED_BN = REPO_ROOT / CANONICAL_BN_PACK_RELPATH
CANONICAL_PACK = REPO_ROOT / CANONICAL_PACK_RELPATH
_AS_OF = "2026-09-14T12:00:00Z"
_DIGEST = "a" * 64


def _bo_section() -> str:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    start = runbook.index(BO_HEADING)
    return runbook[start : runbook.index("## 11.3 Autonomy state model", start)]


def _run(tmp_path: Path):
    return execute_live_equity_stock_checkpoint_stock_value_contract_v1(
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        sealed_bn_pack=SEALED_BN,
        evidence_root=tmp_path / "stock_value",
        persist_as_of=_AS_OF,
    )


def _checkpoint(*, checkpoint_id: str = "CKPT_FIXTURE_001"):
    return build_equity_stock_checkpoint_contract_v1(
        checkpoint_id=checkpoint_id,
        schema_digest=_DIGEST,
        input_set_digest=_DIGEST,
        checkpoint_version="v1",
        bound_account_identity_ref="FIXTURE_BOUND_ACCOUNT",
        bound_account_identity_digest="b" * 64,
    )


def test_sealed_bn_manifest_verifies() -> None:
    assert verify_manifest_sha256_v1(store_root=SEALED_BN) == 0
    assert BN_NEXT_OWNER_GO == OWNER_GO


def test_owner_go_and_sha_mismatch_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(EquityStockCheckpointStockValueContractError, match="OWNER_GO_MISMATCH"):
        execute_live_equity_stock_checkpoint_stock_value_contract_v1(
            owner_go="WRONG",
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            sealed_bn_pack=SEALED_BN,
            evidence_root=tmp_path / "stock_value",
            persist_as_of=_AS_OF,
        )
    with pytest.raises(
        EquityStockCheckpointStockValueContractError, match="ORIGIN_MAIN_SHA_MISMATCH"
    ):
        execute_live_equity_stock_checkpoint_stock_value_contract_v1(
            owner_go=OWNER_GO,
            origin_main_sha="0" * 40,
            sealed_bn_pack=SEALED_BN,
            evidence_root=tmp_path / "stock_value",
            persist_as_of=_AS_OF,
        )


def test_missing_and_malformed_bn_claims_fail_closed(tmp_path: Path) -> None:
    missing = tmp_path / "empty_pack"
    missing.mkdir()
    lineage = missing / "LINEAGE.json"
    lineage.write_text("{}\n", encoding="utf-8")
    digest = hashlib.sha256(lineage.read_bytes()).hexdigest()
    (missing / "MANIFEST.sha256").write_text(f"{digest}  LINEAGE.json\n", encoding="utf-8")
    with pytest.raises(EquityStockCheckpointStockValueContractError, match="BN_CLAIMS_MISSING"):
        execute_live_equity_stock_checkpoint_stock_value_contract_v1(
            owner_go=OWNER_GO,
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            sealed_bn_pack=missing,
            evidence_root=tmp_path / "stock_value",
            persist_as_of=_AS_OF,
        )
    malformed = tmp_path / "malformed_pack"
    malformed.mkdir()
    claims = malformed / "claims.json"
    claims.write_text("{not-json\n", encoding="utf-8")
    digest = hashlib.sha256(claims.read_bytes()).hexdigest()
    (malformed / "MANIFEST.sha256").write_text(f"{digest}  claims.json\n", encoding="utf-8")
    with pytest.raises(EquityStockCheckpointStockValueContractError, match="BN_CLAIMS_MALFORMED"):
        execute_live_equity_stock_checkpoint_stock_value_contract_v1(
            owner_go=OWNER_GO,
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            sealed_bn_pack=malformed,
            evidence_root=tmp_path / "stock_value",
            persist_as_of=_AS_OF,
        )


@pytest.mark.parametrize(
    "claimed_proof",
    [
        DECISION_INCLUDE,
        DECISION_EXCLUDE,
        "EXECUTE_GATE_A",
        "INVENT_LIVE_SOURCE_KIND",
        "RECONSTRUCT_HISTORICAL_UNKNOWN",
        "PROMOTE_EQ_TO_SOURCE",
        "CHECKPOINT_MINT_EQUITY",
        "BOOTSTRAP_FROM_VENUE_EQ",
        "RELABEL_LEGACY_AS_STOCK",
    ],
)
def test_forbidden_authority_mutations_fail_closed(claimed_proof: str) -> None:
    with pytest.raises(EquityStockCheckpointStockValueContractError, match="STOCK_VALUE_CANNOT_"):
        reject_claimed_stock_value_authority_mutation_v1(
            claimed_proof=claimed_proof,
            stock_value_id="FIXTURE",
        )


def test_valid_stock_value_contract() -> None:
    payload = fixture_valid_stock_value_payload_v1()
    record = evaluate_equity_stock_value_v1(payload)
    assert record.validation_status == "VALID"
    assert record.reason_code == REASON_VALID
    assert record.failures == ()
    assert record.derivation_method == DERIVATION_OPTION_D_PRIOR_PLUS_STREAM
    assert SCHEMA_CLASS == "EQUITY_STOCK_VALUE_V1"
    assert "stock_value_id" in REQUIRED_FIELDS
    assert "checkpoint_id" in REQUIRED_FIELDS
    assert "source_provenance" in REQUIRED_FIELDS


def test_missing_malformed_contradictory_fields() -> None:
    missing = dict(fixture_valid_stock_value_payload_v1())
    del missing["stock_value_id"]
    missing_record = evaluate_equity_stock_value_v1(missing)
    assert missing_record.validation_status == "REJECTED"
    assert missing_record.reason_code == REASON_MISSING_FIELD
    malformed = dict(fixture_valid_stock_value_payload_v1())
    malformed["equity_value"] = 12.5
    malformed_record = evaluate_equity_stock_value_v1(malformed)
    assert malformed_record.reason_code == REASON_MALFORMED_FIELD
    contradictory = dict(fixture_valid_stock_value_payload_v1())
    contradictory["included_components"] = ["PRIOR_GOVERNED_STOCK"]
    contradictory["excluded_components"] = [
        "PRIOR_GOVERNED_STOCK",
        "VENUE_EQ",
        "AVAILABLE_CAPITAL",
        "PLACEMENT_CAPACITY",
        "P01_RISK_CAPITAL",
        "UNCLASSIFIED_FLOW",
        "EQUITY_FLOW",
    ]
    contra = evaluate_equity_stock_value_v1(contradictory)
    assert contra.reason_code == REASON_CONTRADICTORY_FIELD


def test_account_and_currency_scope_mismatch() -> None:
    payload = fixture_valid_stock_value_payload_v1()
    account = evaluate_equity_stock_value_v1(
        payload,
        expected_account_identity="OTHER_ACCOUNT",
    )
    assert account.reason_code == REASON_ACCOUNT_SCOPE_MISMATCH
    currency = evaluate_equity_stock_value_v1(
        payload,
        expected_settlement_currency="EUR",
    )
    assert currency.reason_code == REASON_CURRENCY_SCOPE_MISMATCH


def test_sequence_and_time_ambiguity() -> None:
    payload = dict(fixture_valid_stock_value_payload_v1())
    payload["sequence_identity"] = "UNKNOWN"
    record = evaluate_equity_stock_value_v1(payload)
    assert record.reason_code == REASON_SEQUENCE_TIME_AMBIGUOUS
    time_payload = dict(fixture_valid_stock_value_payload_v1())
    time_payload["replay_boundary"] = "2026-09-14T11:00:00Z"
    time_record = evaluate_equity_stock_value_v1(time_payload)
    assert time_record.reason_code == REASON_SEQUENCE_TIME_AMBIGUOUS


def test_stock_versus_flow_rejection() -> None:
    payload = dict(fixture_valid_stock_value_payload_v1())
    payload["source_provenance"] = "FLOW"
    payload["derivation_method"] = "FLOW"
    record = evaluate_equity_stock_value_v1(payload)
    assert record.reason_code == REASON_CLAIMED_FLOW_AS_STOCK
    included = dict(fixture_valid_stock_value_payload_v1())
    included["included_components"] = ["PRIOR_GOVERNED_STOCK", "CLASSIFIED_EVENT_STREAM"]
    flow_included = evaluate_equity_stock_value_v1(included)
    assert flow_included.reason_code == REASON_CLAIMED_FLOW_AS_STOCK
    assert REASON_DOUBLE_COUNT_STOCK_AND_FLOW in REASON_PRECEDENCE


def test_venue_eq_as_source_rejection() -> None:
    payload = dict(fixture_valid_stock_value_payload_v1())
    payload["source_provenance"] = "VENUE_EQ"
    payload["derivation_method"] = "VENUE_EQ"
    record = evaluate_equity_stock_value_v1(payload)
    assert record.reason_code == REASON_CLAIMED_VENUE_EQ_SOURCE


def test_available_placement_and_p01_rejection() -> None:
    available = dict(fixture_valid_stock_value_payload_v1())
    available["source_provenance"] = "AVAILABLE_CAPITAL"
    available["derivation_method"] = "AVAILABLE_CAPITAL"
    assert evaluate_equity_stock_value_v1(available).reason_code == REASON_CLAIMED_AVAILABLE_CAPITAL
    placement = dict(fixture_valid_stock_value_payload_v1())
    placement["source_provenance"] = "PLACEMENT_CAPACITY"
    placement["derivation_method"] = "PLACEMENT_CAPACITY"
    assert (
        evaluate_equity_stock_value_v1(placement).reason_code == REASON_CLAIMED_PLACEMENT_CAPACITY
    )
    p01 = dict(fixture_valid_stock_value_payload_v1())
    p01["source_provenance"] = "P01"
    p01["derivation_method"] = "P01"
    assert evaluate_equity_stock_value_v1(p01).reason_code == REASON_CLAIMED_P01_AS_STOCK


def test_embedding_unresolved_rejection() -> None:
    payload = dict(fixture_valid_stock_value_payload_v1())
    payload["embedding_status"] = "UNRESOLVED"
    record = evaluate_equity_stock_value_v1(payload)
    assert record.reason_code == REASON_EMBEDDING_UNRESOLVED


def test_double_count_guard() -> None:
    payload = dict(fixture_valid_stock_value_payload_v1())
    payload["excluded_components"] = ["VENUE_EQ"]
    record = evaluate_equity_stock_value_v1(payload)
    assert record.reason_code == REASON_DOUBLE_COUNT_STOCK_AND_FLOW


def test_checkpoint_does_not_mint_invariant() -> None:
    payload = dict(fixture_valid_stock_value_payload_v1())
    payload["source_provenance"] = "CHECKPOINT_MINT"
    payload["derivation_method"] = "CHECKPOINT_MINT"
    record = evaluate_equity_stock_value_v1(payload)
    assert record.reason_code == REASON_CLAIMED_CHECKPOINT_MINT
    stock = evaluate_equity_stock_value_v1(fixture_valid_stock_value_payload_v1())
    checkpoint = _checkpoint()
    binding = bind_equity_stock_value_to_checkpoint_v1(stock=stock, checkpoint=checkpoint)
    assert binding.validation_status == "VALID"
    assert binding.checkpoint_mints_equity == "false"
    assert binding.binding_class == "CHECKPOINT_ATTESTS_EXISTING_STOCK_VALUE"
    with pytest.raises(EquityStockCheckpointContractError, match="CHECKPOINT_CANNOT_MINT"):
        build_equity_stock_checkpoint_contract_v1(
            checkpoint_id="CKPT_MINT",
            schema_digest=_DIGEST,
            input_set_digest=_DIGEST,
            checkpoint_version="v1",
            bound_account_identity_ref="FIXTURE_BOUND_ACCOUNT",
            bound_account_identity_digest="b" * 64,
            claimed_equity_stock_value="100.00",
        )


def test_replay_determinism() -> None:
    payload = fixture_valid_stock_value_payload_v1()
    first = evaluate_equity_stock_value_v1(payload)
    second = evaluate_equity_stock_value_v1(payload)
    assert first == second
    boundary_one = evaluate_today_authoritative_derivation_boundary_v1()
    boundary_two = evaluate_today_authoritative_derivation_boundary_v1()
    assert boundary_one == boundary_two
    assert reason_precedence_index_v1(REASON_CLAIMED_CHECKPOINT_MINT) < (
        reason_precedence_index_v1(REASON_INITIAL_STOCK_ANCHOR_ABSENT)
    )
    assert REASON_PRECEDENCE[-1] == REASON_VALID


def test_prior_anchor_missing_path() -> None:
    payload = dict(fixture_valid_stock_value_payload_v1())
    payload["prior_checkpoint_id"] = "NONE"
    record = evaluate_equity_stock_value_v1(payload)
    assert record.reason_code == REASON_PRIOR_CHECKPOINT_REQUIRED_MISSING
    boundary = evaluate_today_authoritative_derivation_boundary_v1()
    assert boundary.prior_stock_anchor_status == "ABSENT"
    assert boundary.prior_checkpoint_status == "NON_SOURCE_NO_BOUND_STOCK"
    assert boundary.event_stream_boundary_status == "FLOW_NOT_STOCK"
    assert boundary.earliest_live_critical_path_blocker == EARLIEST_LIVE_CRITICAL_PATH_BLOCKER
    assert boundary.new_stock_kind_candidate == "NONE"
    assert boundary.membership_owner_ratification_required == "false"
    assert boundary.live_equity_stock_kind_set == KIND_SET_EMPTY


def test_bj_bk_bl_bm_bn_non_regression() -> None:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    assert BJ_HEADING in runbook
    assert BK_HEADING in runbook
    assert BL_HEADING in runbook
    assert BM_HEADING in runbook
    assert BN_HEADING in runbook
    records = evaluate_today_live_equity_stock_kind_set_v1()
    assert ratified_live_equity_stock_kind_set_v1(records) == ()
    by_id = {item.candidate_id: item for item in records}
    for fact_id in FACT_IDS:
        assert by_id[fact_id].member == "false"
    assert KIND_SET_RESOLVED is False
    assert MS2_AUTHORIZED is False
    assert RAW_EQ_SOURCE_AUTHORITY is False


def test_execute_persists_contract_and_protected_surfaces(tmp_path: Path) -> None:
    result = _run(tmp_path)
    assert result.stock_value_contract_defined == "true"
    assert result.authoritative_derivation_defined == "true"
    assert result.initial_stock_anchor_status == "ABSENT"
    assert result.prior_checkpoint_status == "NON_SOURCE_NO_BOUND_STOCK"
    assert result.event_stream_boundary_status == "FLOW_NOT_STOCK"
    assert result.replay_determinism_status == "DETERMINISTIC_FAIL_CLOSED"
    assert result.live_equity_stock_kind_set == KIND_SET_EMPTY
    assert result.live_equity_stock_kind_set_resolved == "false"
    assert result.new_stock_kind_candidate == "NONE"
    assert result.membership_owner_ratification_required == "false"
    assert result.earliest_live_critical_path_blocker == EARLIEST_LIVE_CRITICAL_PATH_BLOCKER
    assert result.next_owner_go_required == NEXT_OWNER_GO_REQUIRED
    assert result.venue_get_count == "0"
    assert result.venue_post_count == "0"
    assert result.gate_a_executed == "false"
    assert result.gate_b_executed == "false"
    assert result.checkpoint_mints_equity == "false"
    assert result.venue_eq_source_authority == "false"
    assert result.kinds_invented_this_go == "false"
    assert result.legacy_semantics_reconstructed == "false"
    assert result.d6_fully_closed == "false"
    assert KIND_SET_RESOLVED is False
    assert MS2_AUTHORIZED is False
    assert RAW_EQ_SOURCE_AUTHORITY is False
    assert LIVE_ENABLED is True
    assert LIVE_ARMED is True
    assert WIRE_SEND_PERMITTED is True
    assert EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY == (
        "NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING"
    )
    store = Path(result.store_root)
    assert verify_manifest_sha256_v1(store_root=store) == 0
    claims = json.loads((store / "claims.json").read_text(encoding="utf-8"))
    assert claims["BN_CONTRACT_REUSED"] == "true"
    assert claims["NEW_CANONICAL_DEFINITION"] == "true"
    assert claims["LEGACY_SEMANTICS_RECONSTRUCTED"] == "false"
    assert claims["CHECKPOINT_MINTS_EQUITY"] == "false"
    assert claims["VENUE_EQ_SOURCE_AUTHORITY"] == "false"
    assert claims["F12_DECISION"] == DECISION_REMAIN_UNKNOWN
    assert claims["MASTER_V2_UNCHANGED"] == "true"
    assert claims["DOUBLE_PLAY_UNCHANGED"] == "true"
    assert claims["BULL_BEAR_STATE_SWITCH_UNCHANGED"] == "true"
    assert claims["SELF_LEARNING_UNCHANGED"] == "true"
    assert claims["STEP_29P_UNCHANGED"] == "true"


def test_canonical_pack_matches_executor_and_manifest() -> None:
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
    claims = json.loads((CANONICAL_PACK / "claims.json").read_text(encoding="utf-8"))
    assert claims["LIVE_EQUITY_STOCK_KIND_SET"] == KIND_SET_EMPTY
    assert claims["NEW_CANONICAL_DEFINITION"] == "true"
    assert claims["LEGACY_SEMANTICS_RECONSTRUCTED"] == "false"
    assert claims["CHECKPOINT_MINTS_EQUITY"] == "false"
    assert claims["VENUE_EQ_SOURCE_AUTHORITY"] == "false"
    assert claims["INITIAL_STOCK_ANCHOR_STATUS"] == "ABSENT"
    assert claims["VENUE_GET_COUNT"] == "0"
    assert claims["KINDS_INVENTED_THIS_GO"] == "false"
    assert claims["EARLIEST_LIVE_CRITICAL_PATH_BLOCKER"] == EARLIEST_LIVE_CRITICAL_PATH_BLOCKER


def test_runbook_bo_and_navigation_persist() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    mot = MOT_PATH.read_text(encoding="utf-8")
    atlas = ATLAS_PATH.read_text(encoding="utf-8")
    runbook = RUNBOOK.read_text(encoding="utf-8")
    assert BN_HEADING in runbook
    bo_section = _bo_section()
    assert OWNER_GO in bo_section
    assert (
        "THIS_SLICE=11.2.1.BO.FULL_CORE_LIVE_EQUITY_STOCK_CHECKPOINT_STOCK_VALUE_CONTRACT"
        in bo_section
    )
    assert "NEW_CANONICAL_DEFINITION=true" in bo_section
    assert "LEGACY_SEMANTICS_RECONSTRUCTED=false" in bo_section
    assert "CHECKPOINT_MINTS_EQUITY=false" in bo_section
    assert "VENUE_EQ_SOURCE_AUTHORITY=false" in bo_section
    assert "STOCK_VALUE_CONTRACT_DEFINED=true" in bo_section
    assert "INITIAL_STOCK_ANCHOR_STATUS=ABSENT" in bo_section
    assert "LIVE_EQUITY_STOCK_KIND_SET=EMPTY_FAIL_CLOSED" in bo_section
    assert "KINDS_INVENTED_THIS_GO=false" in bo_section
    assert "GATE_A_EXECUTED=false" in bo_section
    assert "VENUE_GET_COUNT=0" in bo_section
    assert "D6_FULLY_CLOSED=false" in bo_section
    assert "BN_CONTRACT_REUSED=true" in bo_section
    assert EARLIEST_LIVE_CRITICAL_PATH_BLOCKER in bo_section
    assert "DOCS_TOKEN_FULL_CORE_LIVE_EQUITY_STOCK_CHECKPOINT_STOCK_VALUE_CONTRACT_WP1" in spec
    assert "FULL_CORE_LIVE_EQUITY_STOCK_CHECKPOINT_STOCK_VALUE_CONTRACT_WP1.md" in mot
    assert BO_HEADING in mot
    assert "ATLAS_AUTHORITY=NONE" in atlas
    assert "11.2.1.BO" in atlas
    assert "live_equity_stock_checkpoint_stock_value_contract_v1.py" in atlas
