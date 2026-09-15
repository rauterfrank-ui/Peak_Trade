"""Fail-closed OWNER_SUPPLIED_FORENSIC_BOOTSTRAP_STOCK acquisition.

Capability is defined. Today no owner-supplied forensic artifact exists.
A schema-valid fixture candidate is not a stock anchor and is not ratified.
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
    KIND_SET_EMPTY,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.live_equity_stock_bootstrap_stock_acquisition_v1 import (
    ADMISSIBLE_SOURCE_CLASS,
    ARTIFACT_FILENAME,
    CANONICAL_INPUT_SURFACE_RELPATH,
    CANONICAL_PACK_RELPATH,
    EARLIEST_LIVE_CRITICAL_PATH_BLOCKER,
    EXPECTED_ORIGIN_MAIN_SHA,
    NEXT_OWNER_GO_REQUIRED,
    OWNER_GO,
    REASON_ARTIFACT_CLASS_FORBIDDEN,
    REASON_CLAIMED_CHECKPOINT_MINT,
    REASON_CLAIMED_FLOW_AS_STOCK,
    REASON_CLAIMED_VENUE_EQ_SOURCE,
    REASON_CONTRADICTORY_FIELD,
    REASON_EXTERNAL_FORENSIC_ARTIFACT_REQUIRED,
    REASON_MALFORMED_FIELD,
    REASON_MISSING_FIELD,
    REASON_PRECEDENCE,
    REASON_RATIFICATION_FORBIDDEN,
    REASON_RAW_EVIDENCE_DIGEST_MISMATCH,
    REASON_SOURCE_TYPE_FORBIDDEN,
    REASON_VALID_CANDIDATE,
    REASON_VENUE_READ_NOT_BOOTSTRAP,
    REQUIRED_FIELDS,
    SCHEMA_CLASS,
    VALIDATION_NOT_ACQUIRED,
    VALIDATION_VALID_CANDIDATE,
    BootstrapStockAcquisitionContractError,
    evaluate_bootstrap_stock_acquisition_v1,
    evaluate_today_bootstrap_stock_acquisition_boundary_v1,
    execute_live_equity_stock_bootstrap_stock_acquisition_v1,
    fixture_valid_acquisition_candidate_payload_v1,
    reason_precedence_index_v1,
    reject_claimed_acquisition_authority_mutation_v1,
    scan_owner_supplied_bootstrap_artifact_surface_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.live_equity_stock_bootstrap_stock_provenance_v1 import (
    CANONICAL_PACK_RELPATH as CANONICAL_BP_PACK_RELPATH,
    NEXT_OWNER_GO_REQUIRED as BP_NEXT_OWNER_GO,
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
    REPO_ROOT / "docs/ops/specs/FULL_CORE_LIVE_EQUITY_STOCK_BOOTSTRAP_STOCK_ACQUISITION_WP1.md"
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
BQ_HEADING = "11.2.1.BQ FULL_CORE_LIVE_EQUITY_STOCK_BOOTSTRAP_STOCK_ACQUISITION"
SEALED_BP = REPO_ROOT / CANONICAL_BP_PACK_RELPATH
CANONICAL_PACK = REPO_ROOT / CANONICAL_PACK_RELPATH
_AS_OF = "2026-09-14T16:00:00Z"


def _bq_section() -> str:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    start = runbook.index(BQ_HEADING)
    br = "11.2.1.BR FULL_CORE_LIVE_EQUITY_STOCK_OWNER_SUPPLIED_BOOTSTRAP_ARTIFACT"
    if br in runbook[start:]:
        return runbook[start : runbook.index(br, start)]
    return runbook[start : runbook.index("## 11.3 Autonomy state model", start)]


def _run(tmp_path: Path):
    return execute_live_equity_stock_bootstrap_stock_acquisition_v1(
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        sealed_bp_pack=SEALED_BP,
        repo_root=REPO_ROOT,
        evidence_root=tmp_path / "acquisition",
        persist_as_of=_AS_OF,
    )


def test_sealed_bp_manifest_verifies() -> None:
    assert verify_manifest_sha256_v1(store_root=SEALED_BP) == 0
    assert BP_NEXT_OWNER_GO == OWNER_GO


def test_owner_go_and_sha_mismatch_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(BootstrapStockAcquisitionContractError, match="OWNER_GO_MISMATCH"):
        execute_live_equity_stock_bootstrap_stock_acquisition_v1(
            owner_go="WRONG",
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            sealed_bp_pack=SEALED_BP,
            repo_root=REPO_ROOT,
            evidence_root=tmp_path / "acquisition",
            persist_as_of=_AS_OF,
        )
    with pytest.raises(BootstrapStockAcquisitionContractError, match="ORIGIN_MAIN_SHA_MISMATCH"):
        execute_live_equity_stock_bootstrap_stock_acquisition_v1(
            owner_go=OWNER_GO,
            origin_main_sha="0" * 40,
            sealed_bp_pack=SEALED_BP,
            repo_root=REPO_ROOT,
            evidence_root=tmp_path / "acquisition",
            persist_as_of=_AS_OF,
        )


def test_missing_and_malformed_bp_claims_fail_closed(tmp_path: Path) -> None:
    missing = tmp_path / "empty_pack"
    missing.mkdir()
    lineage = missing / "LINEAGE.json"
    lineage.write_text("{}\n", encoding="utf-8")
    digest = hashlib.sha256(lineage.read_bytes()).hexdigest()
    (missing / "MANIFEST.sha256").write_text(f"{digest}  LINEAGE.json\n", encoding="utf-8")
    with pytest.raises(BootstrapStockAcquisitionContractError, match="BP_CLAIMS_MISSING"):
        execute_live_equity_stock_bootstrap_stock_acquisition_v1(
            owner_go=OWNER_GO,
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            sealed_bp_pack=missing,
            repo_root=REPO_ROOT,
            evidence_root=tmp_path / "acquisition",
            persist_as_of=_AS_OF,
        )
    malformed = tmp_path / "malformed_pack"
    malformed.mkdir()
    claims = malformed / "claims.json"
    claims.write_text("{not-json\n", encoding="utf-8")
    digest = hashlib.sha256(claims.read_bytes()).hexdigest()
    (malformed / "MANIFEST.sha256").write_text(f"{digest}  claims.json\n", encoding="utf-8")
    with pytest.raises(BootstrapStockAcquisitionContractError, match="BP_CLAIMS_MALFORMED"):
        execute_live_equity_stock_bootstrap_stock_acquisition_v1(
            owner_go=OWNER_GO,
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            sealed_bp_pack=malformed,
            repo_root=REPO_ROOT,
            evidence_root=tmp_path / "acquisition",
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
        "RATIFY_KIND_MEMBERSHIP",
        "PROMOTE_CANDIDATE_TO_ANCHOR",
        "VENUE_GET_AS_BOOTSTRAP",
        "INTERPRET_MISSING_AS_ZERO",
    ],
)
def test_forbidden_authority_mutations_fail_closed(claimed_proof: str) -> None:
    with pytest.raises(BootstrapStockAcquisitionContractError, match="ACQUISITION_CANNOT_"):
        reject_claimed_acquisition_authority_mutation_v1(
            claimed_proof=claimed_proof,
            artifact_id="FIXTURE",
        )


def test_valid_acquisition_schema_fixture_is_not_anchor() -> None:
    payload, raw_bytes = fixture_valid_acquisition_candidate_payload_v1()
    record = evaluate_bootstrap_stock_acquisition_v1(payload, raw_bytes=raw_bytes)
    assert record.candidate_validation_status == VALIDATION_VALID_CANDIDATE
    assert record.reason_code == REASON_VALID_CANDIDATE
    assert record.failures == ()
    assert record.artifact_class == ADMISSIBLE_SOURCE_CLASS
    assert record.ratification_status == "NOT_RATIFIED"
    assert SCHEMA_CLASS == "BOOTSTRAP_STOCK_ACQUISITION_V1"
    assert "raw_evidence_digest" in REQUIRED_FIELDS
    assert "source_type" in REQUIRED_FIELDS
    assert "ratification_status" in REQUIRED_FIELDS
    boundary = evaluate_today_bootstrap_stock_acquisition_boundary_v1(repo_root=REPO_ROOT)
    assert boundary.initial_stock_anchor_status == "ABSENT"
    assert boundary.live_equity_stock_kind_set == KIND_SET_EMPTY
    assert boundary.ratification_performed == "false"
    assert (
        ratified_live_equity_stock_kind_set_v1(evaluate_today_live_equity_stock_kind_set_v1()) == ()
    )


def test_missing_malformed_contradictory_and_raw_digest() -> None:
    payload, raw_bytes = fixture_valid_acquisition_candidate_payload_v1()
    missing = dict(payload)
    del missing["artifact_id"]
    missing_record = evaluate_bootstrap_stock_acquisition_v1(missing, raw_bytes=raw_bytes)
    assert missing_record.candidate_validation_status == "REJECTED"
    assert missing_record.reason_code == REASON_MISSING_FIELD
    malformed = dict(payload)
    malformed["equity_value"] = 12.5
    malformed_record = evaluate_bootstrap_stock_acquisition_v1(malformed, raw_bytes=raw_bytes)
    assert malformed_record.reason_code == REASON_MALFORMED_FIELD
    contradictory = dict(payload)
    contradictory["input_digest"] = "d" * 64
    contra = evaluate_bootstrap_stock_acquisition_v1(contradictory, raw_bytes=raw_bytes)
    assert contra.reason_code == REASON_CONTRADICTORY_FIELD
    digest_mismatch = evaluate_bootstrap_stock_acquisition_v1(
        payload,
        raw_bytes=b"not-the-declared-raw",
    )
    assert digest_mismatch.reason_code == REASON_RAW_EVIDENCE_DIGEST_MISMATCH
    absent_raw = evaluate_bootstrap_stock_acquisition_v1(payload)
    assert absent_raw.reason_code == REASON_EXTERNAL_FORENSIC_ARTIFACT_REQUIRED


def test_venue_eq_checkpoint_flow_and_venue_get_forbidden() -> None:
    payload, raw_bytes = fixture_valid_acquisition_candidate_payload_v1()
    venue = dict(payload)
    venue["artifact_class"] = "VENUE_EQ"
    assert evaluate_bootstrap_stock_acquisition_v1(venue, raw_bytes=raw_bytes).reason_code == (
        REASON_CLAIMED_VENUE_EQ_SOURCE
    )
    checkpoint = dict(payload)
    checkpoint["artifact_class"] = "CHECKPOINT"
    assert (
        evaluate_bootstrap_stock_acquisition_v1(checkpoint, raw_bytes=raw_bytes).reason_code
        == REASON_CLAIMED_CHECKPOINT_MINT
    )
    flow = dict(payload)
    flow["artifact_class"] = "CLASSIFIED_EVENT_STREAM"
    assert evaluate_bootstrap_stock_acquisition_v1(flow, raw_bytes=raw_bytes).reason_code == (
        REASON_CLAIMED_FLOW_AS_STOCK
    )
    venue_get = dict(payload)
    venue_get["source_type"] = "VENUE_GET"
    assert (
        evaluate_bootstrap_stock_acquisition_v1(venue_get, raw_bytes=raw_bytes).reason_code
        == REASON_VENUE_READ_NOT_BOOTSTRAP
    )
    other_class = dict(payload)
    other_class["artifact_class"] = "INTERPRETATION"
    assert (
        evaluate_bootstrap_stock_acquisition_v1(other_class, raw_bytes=raw_bytes).reason_code
        == REASON_ARTIFACT_CLASS_FORBIDDEN
    )
    other_type = dict(payload)
    other_type["source_type"] = "INTERPRETATION"
    assert (
        evaluate_bootstrap_stock_acquisition_v1(other_type, raw_bytes=raw_bytes).reason_code
        == REASON_SOURCE_TYPE_FORBIDDEN
    )


def test_acquisition_cannot_self_ratify() -> None:
    payload, raw_bytes = fixture_valid_acquisition_candidate_payload_v1()
    payload["ratification_status"] = "RATIFIED"
    record = evaluate_bootstrap_stock_acquisition_v1(payload, raw_bytes=raw_bytes)
    assert record.reason_code == REASON_RATIFICATION_FORBIDDEN
    assert record.candidate_validation_status == "REJECTED"


def test_today_surface_and_boundary_remain_fail_closed() -> None:
    scan = scan_owner_supplied_bootstrap_artifact_surface_v1(repo_root=REPO_ROOT)
    assert scan.surface_relpath == CANONICAL_INPUT_SURFACE_RELPATH
    assert scan.surface_status == "MISSING"
    assert scan.artifact_present == "false"
    assert scan.artifact_class == "NONE"
    boundary = evaluate_today_bootstrap_stock_acquisition_boundary_v1(repo_root=REPO_ROOT)
    replay = evaluate_today_bootstrap_stock_acquisition_boundary_v1(repo_root=REPO_ROOT)
    assert boundary == replay
    assert boundary.acquisition_contract_status == "DEFINED_FAIL_CLOSED"
    assert boundary.forensic_artifact_present == "false"
    assert boundary.forensic_artifact_class == "NONE"
    assert boundary.raw_evidence_preserved == "true"
    assert boundary.candidate_validation_status == VALIDATION_NOT_ACQUIRED
    assert boundary.initial_stock_anchor_status == "ABSENT"
    assert boundary.source_kind_status == "NONE"
    assert boundary.live_equity_stock_kind_set == KIND_SET_EMPTY
    assert boundary.ratification_performed == "false"
    assert boundary.earliest_live_critical_path_blocker == EARLIEST_LIVE_CRITICAL_PATH_BLOCKER
    assert boundary.next_owner_go_required == NEXT_OWNER_GO_REQUIRED
    assert reason_precedence_index_v1(REASON_CLAIMED_CHECKPOINT_MINT) < (
        reason_precedence_index_v1(REASON_EXTERNAL_FORENSIC_ARTIFACT_REQUIRED)
    )
    assert REASON_PRECEDENCE[-1] == REASON_VALID_CANDIDATE


def test_present_tmp_surface_does_not_mint_membership(tmp_path: Path) -> None:
    surface = tmp_path / CANONICAL_INPUT_SURFACE_RELPATH
    surface.mkdir(parents=True)
    payload, raw_bytes = fixture_valid_acquisition_candidate_payload_v1()
    (surface / ARTIFACT_FILENAME).write_bytes(raw_bytes)
    scan = scan_owner_supplied_bootstrap_artifact_surface_v1(repo_root=tmp_path)
    assert scan.surface_status == "PRESENT"
    assert scan.artifact_present == "true"
    record = evaluate_bootstrap_stock_acquisition_v1(payload, raw_bytes=raw_bytes)
    assert record.candidate_validation_status == VALIDATION_VALID_CANDIDATE
    assert record.ratification_status == "NOT_RATIFIED"
    assert (
        ratified_live_equity_stock_kind_set_v1(evaluate_today_live_equity_stock_kind_set_v1()) == ()
    )
    production = evaluate_today_bootstrap_stock_acquisition_boundary_v1(repo_root=REPO_ROOT)
    assert production.initial_stock_anchor_status == "ABSENT"
    assert production.live_equity_stock_kind_set == KIND_SET_EMPTY
    assert production.ratification_performed == "false"


def test_bj_bk_bl_bm_bn_bo_bp_non_regression() -> None:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    assert BJ_HEADING in runbook
    assert BK_HEADING in runbook
    assert BL_HEADING in runbook
    assert BM_HEADING in runbook
    assert BN_HEADING in runbook
    assert BO_HEADING in runbook
    assert BP_HEADING in runbook
    records = evaluate_today_live_equity_stock_kind_set_v1()
    assert ratified_live_equity_stock_kind_set_v1(records) == ()
    assert KIND_SET_RESOLVED is False
    assert MS2_AUTHORIZED is False
    assert RAW_EQ_SOURCE_AUTHORITY is False


def test_execute_persists_contract_and_protected_surfaces(tmp_path: Path) -> None:
    result = _run(tmp_path)
    assert result.acquisition_contract_status == "DEFINED_FAIL_CLOSED"
    assert result.forensic_artifact_present == "false"
    assert result.forensic_artifact_class == "NONE"
    assert result.raw_evidence_preserved == "true"
    assert result.candidate_validation_status == VALIDATION_NOT_ACQUIRED
    assert result.initial_stock_anchor_status == "ABSENT"
    assert result.source_kind_status == "NONE"
    assert result.live_equity_stock_kind_set == KIND_SET_EMPTY
    assert result.ratification_performed == "false"
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
    assert WIRE_SEND_PERMITTED is False
    assert EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY == (
        "NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING"
    )
    store = Path(result.store_root)
    assert verify_manifest_sha256_v1(store_root=store) == 0
    claims = json.loads((store / "claims.json").read_text(encoding="utf-8"))
    assert claims["BP_CONTRACT_REUSED"] == "true"
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
    assert claims["RATIFICATION_PERFORMED"] == "false"
    assert claims["FORENSIC_ARTIFACT_PRESENT"] == "false"


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
    assert claims["FORENSIC_ARTIFACT_PRESENT"] == "false"
    assert claims["CANDIDATE_VALIDATION_STATUS"] == VALIDATION_NOT_ACQUIRED
    assert claims["RATIFICATION_PERFORMED"] == "false"
    assert claims["VENUE_GET_COUNT"] == "0"
    assert claims["KINDS_INVENTED_THIS_GO"] == "false"
    assert claims["EARLIEST_LIVE_CRITICAL_PATH_BLOCKER"] == EARLIEST_LIVE_CRITICAL_PATH_BLOCKER


def test_runbook_bq_and_navigation_persist() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    mot = MOT_PATH.read_text(encoding="utf-8")
    atlas = ATLAS_PATH.read_text(encoding="utf-8")
    runbook = RUNBOOK.read_text(encoding="utf-8")
    assert BP_HEADING in runbook
    bq_section = _bq_section()
    assert OWNER_GO in bq_section
    assert (
        "THIS_SLICE=11.2.1.BQ.FULL_CORE_LIVE_EQUITY_STOCK_BOOTSTRAP_STOCK_ACQUISITION" in bq_section
    )
    assert "NEW_CANONICAL_DEFINITION=true" in bq_section
    assert "LEGACY_SEMANTICS_RECONSTRUCTED=false" in bq_section
    assert "CHECKPOINT_MINTS_EQUITY=false" in bq_section
    assert "VENUE_EQ_SOURCE_AUTHORITY=false" in bq_section
    assert "ACQUISITION_CONTRACT_DEFINED=true" in bq_section
    assert "FORENSIC_ARTIFACT_PRESENT=false" in bq_section
    assert "CANDIDATE_VALIDATION_STATUS=NOT_ACQUIRED" in bq_section
    assert "INITIAL_STOCK_ANCHOR_STATUS=ABSENT" in bq_section
    assert "LIVE_EQUITY_STOCK_KIND_SET=EMPTY_FAIL_CLOSED" in bq_section
    assert "RATIFICATION_PERFORMED=false" in bq_section
    assert "KINDS_INVENTED_THIS_GO=false" in bq_section
    assert "GATE_A_EXECUTED=false" in bq_section
    assert "VENUE_GET_COUNT=0" in bq_section
    assert "D6_FULLY_CLOSED=false" in bq_section
    assert "BP_CONTRACT_REUSED=true" in bq_section
    assert EARLIEST_LIVE_CRITICAL_PATH_BLOCKER in bq_section
    assert "DOCS_TOKEN_FULL_CORE_LIVE_EQUITY_STOCK_BOOTSTRAP_STOCK_ACQUISITION_WP1" in spec
    assert "FULL_CORE_LIVE_EQUITY_STOCK_BOOTSTRAP_STOCK_ACQUISITION_WP1.md" in mot
    assert BQ_HEADING in mot
    assert "ATLAS_AUTHORITY=NONE" in atlas
    assert "11.2.1.BQ" in atlas
    assert "live_equity_stock_bootstrap_stock_acquisition_v1.py" in atlas
