"""NEW_CANONICAL_DEFINITION of bootstrap INITIAL_STOCK_ANCHOR provenance.

Acquisition seam is defined. Today no forensic bootstrap proof exists.
KIND_SET stays empty. Venue eq, checkpoint, and flow remain non-sources.
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
from src.ops.governed_productive_account_equity_authority_producer_v1.live_equity_stock_bootstrap_stock_provenance_v1 import (
    ADMISSIBLE_SOURCE_CLASS,
    BOOTSTRAP_PROVENANCE_FINDING,
    CANONICAL_PACK_RELPATH,
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
    REASON_CIRCULAR_OPTION_D,
    REASON_CURRENCY_SCOPE_MISMATCH,
    REASON_DOUBLE_COUNT_STOCK_AND_FLOW,
    REASON_EMBEDDING_UNRESOLVED,
    REASON_EXTERNAL_PROOF_ABSENT,
    REASON_HISTORICAL_UNKNOWN,
    REASON_MALFORMED_FIELD,
    REASON_MISSING_FIELD,
    REASON_NOT_EQUITY_STOCK,
    REASON_PRECEDENCE,
    REASON_REPLAY_NONDETERMINISTIC,
    REASON_VALID,
    REQUIRED_FIELDS,
    SCHEMA_CLASS,
    BootstrapStockProvenanceContractError,
    evaluate_bootstrap_stock_provenance_v1,
    evaluate_today_bootstrap_provenance_candidates_v1,
    evaluate_today_bootstrap_stock_provenance_boundary_v1,
    execute_live_equity_stock_bootstrap_stock_provenance_v1,
    fixture_valid_bootstrap_stock_payload_v1,
    reason_precedence_index_v1,
    reject_claimed_bootstrap_authority_mutation_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.live_equity_stock_checkpoint_stock_value_contract_v1 import (
    CANONICAL_PACK_RELPATH as CANONICAL_BO_PACK_RELPATH,
    NEXT_OWNER_GO_REQUIRED as BO_NEXT_OWNER_GO,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.live_equity_stock_kind_set_new_canonical_definition_v1 import (
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
    REPO_ROOT / "docs/ops/specs/FULL_CORE_LIVE_EQUITY_STOCK_BOOTSTRAP_STOCK_PROVENANCE_WP1.md"
)
MOT_PATH = REPO_ROOT / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md"
ATLAS_PATH = REPO_ROOT / "docs/system_atlas/entities/catalog.yaml"
BJ_HEADING = "11.2.1.BJ FULL_CORE_D6_F12_F13_KIND_SET_REMAINING_UNKNOWN_PIN_AND_REOPEN_GATE"
BK_HEADING = "11.2.1.BK FULL_CORE_D6_BJ_SEMANTICS_BOUNDED_IMPLEMENTATION"
BL_HEADING = "11.2.1.BL FULL_CORE_D6_BK_BOUNDED_IMPLEMENTATION"
BM_HEADING = "11.2.1.BM FULL_CORE_LIVE_CRITICAL_PATH_NEXT_BLOCKER"
BN_HEADING = "11.2.1.BN FULL_CORE_LIVE_EQUITY_STOCK_KIND_SET_NEW_CANONICAL_DEFINITION"
BO_HEADING = "11.2.1.BO FULL_CORE_LIVE_EQUITY_STOCK_CHECKPOINT_STOCK_VALUE_CONTRACT"
BP_HEADING = "11.2.1.BP FULL_CORE_LIVE_EQUITY_STOCK_BOOTSTRAP_STOCK_PROVENANCE"
SEALED_BO = REPO_ROOT / CANONICAL_BO_PACK_RELPATH
CANONICAL_PACK = REPO_ROOT / CANONICAL_PACK_RELPATH
_AS_OF = "2026-09-14T14:00:00Z"


def _bp_section() -> str:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    start = runbook.index(BP_HEADING)
    return runbook[start : runbook.index("## 11.3 Autonomy state model", start)]


def _run(tmp_path: Path):
    return execute_live_equity_stock_bootstrap_stock_provenance_v1(
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        sealed_bo_pack=SEALED_BO,
        evidence_root=tmp_path / "bootstrap",
        persist_as_of=_AS_OF,
    )


def test_sealed_bo_manifest_verifies() -> None:
    assert verify_manifest_sha256_v1(store_root=SEALED_BO) == 0
    assert BO_NEXT_OWNER_GO == OWNER_GO


def test_owner_go_and_sha_mismatch_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(BootstrapStockProvenanceContractError, match="OWNER_GO_MISMATCH"):
        execute_live_equity_stock_bootstrap_stock_provenance_v1(
            owner_go="WRONG",
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            sealed_bo_pack=SEALED_BO,
            evidence_root=tmp_path / "bootstrap",
            persist_as_of=_AS_OF,
        )
    with pytest.raises(BootstrapStockProvenanceContractError, match="ORIGIN_MAIN_SHA_MISMATCH"):
        execute_live_equity_stock_bootstrap_stock_provenance_v1(
            owner_go=OWNER_GO,
            origin_main_sha="0" * 40,
            sealed_bo_pack=SEALED_BO,
            evidence_root=tmp_path / "bootstrap",
            persist_as_of=_AS_OF,
        )


def test_missing_and_malformed_bo_claims_fail_closed(tmp_path: Path) -> None:
    missing = tmp_path / "empty_pack"
    missing.mkdir()
    lineage = missing / "LINEAGE.json"
    lineage.write_text("{}\n", encoding="utf-8")
    digest = hashlib.sha256(lineage.read_bytes()).hexdigest()
    (missing / "MANIFEST.sha256").write_text(f"{digest}  LINEAGE.json\n", encoding="utf-8")
    with pytest.raises(BootstrapStockProvenanceContractError, match="BO_CLAIMS_MISSING"):
        execute_live_equity_stock_bootstrap_stock_provenance_v1(
            owner_go=OWNER_GO,
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            sealed_bo_pack=missing,
            evidence_root=tmp_path / "bootstrap",
            persist_as_of=_AS_OF,
        )
    malformed = tmp_path / "malformed_pack"
    malformed.mkdir()
    claims = malformed / "claims.json"
    claims.write_text("{not-json\n", encoding="utf-8")
    digest = hashlib.sha256(claims.read_bytes()).hexdigest()
    (malformed / "MANIFEST.sha256").write_text(f"{digest}  claims.json\n", encoding="utf-8")
    with pytest.raises(BootstrapStockProvenanceContractError, match="BO_CLAIMS_MALFORMED"):
        execute_live_equity_stock_bootstrap_stock_provenance_v1(
            owner_go=OWNER_GO,
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            sealed_bo_pack=malformed,
            evidence_root=tmp_path / "bootstrap",
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
        "BOOTSTRAP_FROM_CHECKPOINT",
        "BOOTSTRAP_FROM_FLOW",
        "RELABEL_LEGACY_AS_STOCK",
        "MINT_INITIAL_STOCK",
    ],
)
def test_forbidden_authority_mutations_fail_closed(claimed_proof: str) -> None:
    with pytest.raises(BootstrapStockProvenanceContractError, match="BOOTSTRAP_CANNOT_"):
        reject_claimed_bootstrap_authority_mutation_v1(
            claimed_proof=claimed_proof,
            anchor_id="FIXTURE",
        )


def test_valid_bootstrap_schema_fixture() -> None:
    payload = fixture_valid_bootstrap_stock_payload_v1()
    record = evaluate_bootstrap_stock_provenance_v1(payload)
    assert record.validation_status == "VALID"
    assert record.reason_code == REASON_VALID
    assert record.failures == ()
    assert record.source_class == ADMISSIBLE_SOURCE_CLASS
    assert SCHEMA_CLASS == "BOOTSTRAP_STOCK_PROVENANCE_V1"
    assert "anchor_id" in REQUIRED_FIELDS
    assert "source_class" in REQUIRED_FIELDS
    assert "provenance_digest" in REQUIRED_FIELDS


def test_missing_malformed_contradictory_fields() -> None:
    missing = dict(fixture_valid_bootstrap_stock_payload_v1())
    del missing["anchor_id"]
    missing_record = evaluate_bootstrap_stock_provenance_v1(missing)
    assert missing_record.validation_status == "REJECTED"
    assert missing_record.reason_code == REASON_MISSING_FIELD
    malformed = dict(fixture_valid_bootstrap_stock_payload_v1())
    malformed["equity_value"] = 12.5
    malformed_record = evaluate_bootstrap_stock_provenance_v1(malformed)
    assert malformed_record.reason_code == REASON_MALFORMED_FIELD
    contradictory = dict(fixture_valid_bootstrap_stock_payload_v1())
    contradictory["input_digest"] = "d" * 64
    contra = evaluate_bootstrap_stock_provenance_v1(contradictory)
    assert contra.reason_code == REASON_REPLAY_NONDETERMINISTIC


def test_account_and_currency_scope_mismatch() -> None:
    payload = fixture_valid_bootstrap_stock_payload_v1()
    account = evaluate_bootstrap_stock_provenance_v1(
        payload,
        expected_account_identity="OTHER_ACCOUNT",
    )
    assert account.reason_code == REASON_ACCOUNT_SCOPE_MISMATCH
    currency = evaluate_bootstrap_stock_provenance_v1(
        payload,
        expected_settlement_currency="EUR",
    )
    assert currency.reason_code == REASON_CURRENCY_SCOPE_MISMATCH


def test_venue_eq_checkpoint_flow_forbidden() -> None:
    payload = dict(fixture_valid_bootstrap_stock_payload_v1())
    payload["source_class"] = "VENUE_EQ"
    assert evaluate_bootstrap_stock_provenance_v1(payload).reason_code == (
        REASON_CLAIMED_VENUE_EQ_SOURCE
    )
    checkpoint = dict(fixture_valid_bootstrap_stock_payload_v1())
    checkpoint["source_class"] = "GOVERNED_CHECKPOINT"
    assert evaluate_bootstrap_stock_provenance_v1(checkpoint).reason_code == (
        REASON_CLAIMED_CHECKPOINT_MINT
    )
    flow = dict(fixture_valid_bootstrap_stock_payload_v1())
    flow["source_class"] = "CLASSIFIED_EVENT_STREAM"
    flow_record = evaluate_bootstrap_stock_provenance_v1(flow)
    assert flow_record.reason_code == REASON_CLAIMED_FLOW_AS_STOCK
    assert REASON_DOUBLE_COUNT_STOCK_AND_FLOW in REASON_PRECEDENCE


def test_available_placement_p01_and_option_d_rejection() -> None:
    available = dict(fixture_valid_bootstrap_stock_payload_v1())
    available["source_class"] = "U04"
    assert evaluate_bootstrap_stock_provenance_v1(available).reason_code == (
        REASON_CLAIMED_AVAILABLE_CAPITAL
    )
    placement = dict(fixture_valid_bootstrap_stock_payload_v1())
    placement["source_class"] = "U06"
    assert evaluate_bootstrap_stock_provenance_v1(placement).reason_code == (
        REASON_CLAIMED_PLACEMENT_CAPACITY
    )
    p01 = dict(fixture_valid_bootstrap_stock_payload_v1())
    p01["source_class"] = "P01"
    assert evaluate_bootstrap_stock_provenance_v1(p01).reason_code == REASON_CLAIMED_P01_AS_STOCK
    option_d = dict(fixture_valid_bootstrap_stock_payload_v1())
    option_d["source_class"] = "OPTION_D_PRIOR_STOCK_PLUS_CLASSIFIED_EVENT_STREAM"
    assert evaluate_bootstrap_stock_provenance_v1(option_d).reason_code == REASON_CIRCULAR_OPTION_D


def test_historical_unknown_and_non_stock_rejected() -> None:
    historical = dict(fixture_valid_bootstrap_stock_payload_v1())
    historical["source_class"] = "F12"
    assert evaluate_bootstrap_stock_provenance_v1(historical).reason_code == (
        REASON_HISTORICAL_UNKNOWN
    )
    genesis = dict(fixture_valid_bootstrap_stock_payload_v1())
    genesis["source_class"] = "D4_GENESIS_ACCOUNT_CONFIG"
    assert evaluate_bootstrap_stock_provenance_v1(genesis).reason_code == REASON_NOT_EQUITY_STOCK


def test_embedding_and_absent_external_proof() -> None:
    payload = dict(fixture_valid_bootstrap_stock_payload_v1())
    payload["embedding_status"] = "UNRESOLVED"
    assert evaluate_bootstrap_stock_provenance_v1(payload).reason_code == (
        REASON_EMBEDDING_UNRESOLVED
    )
    absent = dict(fixture_valid_bootstrap_stock_payload_v1())
    absent["acquisition_status"] = "SEAM_DEFINED_PROOF_ABSENT"
    assert evaluate_bootstrap_stock_provenance_v1(absent).reason_code == (
        REASON_EXTERNAL_PROOF_ABSENT
    )


def test_today_census_and_boundary_remain_fail_closed() -> None:
    records = evaluate_today_bootstrap_provenance_candidates_v1()
    by_id = {item.candidate_id: item for item in records}
    assert by_id["VENUE_EQ"].reason_code == REASON_CLAIMED_VENUE_EQ_SOURCE
    assert by_id["GOVERNED_CHECKPOINT"].reason_code == REASON_CLAIMED_CHECKPOINT_MINT
    assert by_id["CLASSIFIED_EVENT_STREAM"].reason_code == REASON_CLAIMED_FLOW_AS_STOCK
    assert by_id[ADMISSIBLE_SOURCE_CLASS].reason_code == REASON_EXTERNAL_PROOF_ABSENT
    assert by_id[ADMISSIBLE_SOURCE_CLASS].input_status == "MISSING"
    for fact_id in FACT_IDS:
        assert by_id[fact_id].member == "false"
        assert by_id[fact_id].reason_code == REASON_HISTORICAL_UNKNOWN
    assert all(item.member == "false" for item in records)
    boundary = evaluate_today_bootstrap_stock_provenance_boundary_v1()
    replay = evaluate_today_bootstrap_stock_provenance_boundary_v1()
    assert boundary == replay
    assert boundary.bootstrap_provenance_finding == BOOTSTRAP_PROVENANCE_FINDING
    assert boundary.initial_stock_anchor_status == "ABSENT"
    assert boundary.source_kind_status == "NONE"
    assert boundary.acquisition_seam_status == "SEAM_DEFINED_PROOF_ABSENT"
    assert boundary.live_equity_stock_kind_set == KIND_SET_EMPTY
    assert boundary.earliest_live_critical_path_blocker == EARLIEST_LIVE_CRITICAL_PATH_BLOCKER
    assert boundary.next_owner_go_required == NEXT_OWNER_GO_REQUIRED
    assert reason_precedence_index_v1(REASON_CLAIMED_CHECKPOINT_MINT) < (
        reason_precedence_index_v1(REASON_EXTERNAL_PROOF_ABSENT)
    )
    assert REASON_PRECEDENCE[-1] == REASON_VALID


def test_bj_bk_bl_bm_bn_bo_non_regression() -> None:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    assert BJ_HEADING in runbook
    assert BK_HEADING in runbook
    assert BL_HEADING in runbook
    assert BM_HEADING in runbook
    assert BN_HEADING in runbook
    assert BO_HEADING in runbook
    records = evaluate_today_live_equity_stock_kind_set_v1()
    assert ratified_live_equity_stock_kind_set_v1(records) == ()
    assert KIND_SET_RESOLVED is False
    assert MS2_AUTHORIZED is False
    assert RAW_EQ_SOURCE_AUTHORITY is False


def test_execute_persists_contract_and_protected_surfaces(tmp_path: Path) -> None:
    result = _run(tmp_path)
    assert result.bootstrap_provenance_finding == BOOTSTRAP_PROVENANCE_FINDING
    assert result.acquisition_seam_status == "SEAM_DEFINED_PROOF_ABSENT"
    assert result.initial_stock_anchor_status == "ABSENT"
    assert result.source_kind_status == "NONE"
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
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert WIRE_SEND_PERMITTED is False
    assert EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY == (
        "NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING"
    )
    store = Path(result.store_root)
    assert verify_manifest_sha256_v1(store_root=store) == 0
    claims = json.loads((store / "claims.json").read_text(encoding="utf-8"))
    assert claims["BO_CONTRACT_REUSED"] == "true"
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
    assert claims["BOOTSTRAP_PROVENANCE_FINDING"] == BOOTSTRAP_PROVENANCE_FINDING
    assert claims["VENUE_GET_COUNT"] == "0"
    assert claims["KINDS_INVENTED_THIS_GO"] == "false"
    assert claims["EARLIEST_LIVE_CRITICAL_PATH_BLOCKER"] == EARLIEST_LIVE_CRITICAL_PATH_BLOCKER


def test_runbook_bp_and_navigation_persist() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    mot = MOT_PATH.read_text(encoding="utf-8")
    atlas = ATLAS_PATH.read_text(encoding="utf-8")
    runbook = RUNBOOK.read_text(encoding="utf-8")
    assert BO_HEADING in runbook
    bp_section = _bp_section()
    assert OWNER_GO in bp_section
    assert (
        "THIS_SLICE=11.2.1.BP.FULL_CORE_LIVE_EQUITY_STOCK_BOOTSTRAP_STOCK_PROVENANCE" in bp_section
    )
    assert "NEW_CANONICAL_DEFINITION=true" in bp_section
    assert "LEGACY_SEMANTICS_RECONSTRUCTED=false" in bp_section
    assert "CHECKPOINT_MINTS_EQUITY=false" in bp_section
    assert "VENUE_EQ_SOURCE_AUTHORITY=false" in bp_section
    assert "BOOTSTRAP_PROVENANCE_CONTRACT_DEFINED=true" in bp_section
    assert "INITIAL_STOCK_ANCHOR_STATUS=ABSENT" in bp_section
    assert "LIVE_EQUITY_STOCK_KIND_SET=EMPTY_FAIL_CLOSED" in bp_section
    assert "KINDS_INVENTED_THIS_GO=false" in bp_section
    assert "GATE_A_EXECUTED=false" in bp_section
    assert "VENUE_GET_COUNT=0" in bp_section
    assert "D6_FULLY_CLOSED=false" in bp_section
    assert "BO_CONTRACT_REUSED=true" in bp_section
    assert EARLIEST_LIVE_CRITICAL_PATH_BLOCKER in bp_section
    assert "DOCS_TOKEN_FULL_CORE_LIVE_EQUITY_STOCK_BOOTSTRAP_STOCK_PROVENANCE_WP1" in spec
    assert "FULL_CORE_LIVE_EQUITY_STOCK_BOOTSTRAP_STOCK_PROVENANCE_WP1.md" in mot
    assert BP_HEADING in mot
    assert "ATLAS_AUTHORITY=NONE" in atlas
    assert "11.2.1.BP" in atlas
    assert "live_equity_stock_bootstrap_stock_provenance_v1.py" in atlas
