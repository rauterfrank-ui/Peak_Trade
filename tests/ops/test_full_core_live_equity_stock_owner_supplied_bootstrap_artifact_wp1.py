"""Fail-closed owner-supplied forensic bootstrap artifact ingest.

Capability is defined. Today no owner-supplied forensic artifact exists.
A schema-valid fixture candidate is not a stock anchor and is not ratified.
KIND_SET stays empty. Venue eq, checkpoint, and flow remain non-sources.
Reconstruction stays unbound. No GET. GATE_A and GATE_B are not executed.
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
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    CHECKPOINT_CAN_MINT_EQUITY,
    DIMENSION_AVAILABLE_FOR_SIZING,
    DIMENSION_EQUITY_STOCK,
    DIMENSION_P01_RISK_CAPITAL_REDUCTION,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.live_equity_stock_bootstrap_stock_acquisition_v1 import (
    CANONICAL_PACK_RELPATH as CANONICAL_BQ_PACK_RELPATH,
    EARLIEST_LIVE_CRITICAL_PATH_BLOCKER as BQ_LIVE_BLOCKER,
    NEXT_OWNER_GO_REQUIRED as BQ_NEXT_OWNER_GO,
    REASON_MALFORMED_FIELD,
    evaluate_today_bootstrap_stock_acquisition_boundary_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.live_equity_stock_kind_set_new_canonical_definition_v1 import (
    evaluate_today_live_equity_stock_kind_set_v1,
    ratified_live_equity_stock_kind_set_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.live_equity_stock_owner_supplied_bootstrap_artifact_v1 import (
    ADMISSIBLE_SOURCE_CLASS,
    ARTIFACT_FILENAME,
    CANONICAL_INPUT_SURFACE_RELPATH,
    CANONICAL_PACK_RELPATH,
    EARLIEST_LIVE_CRITICAL_PATH_BLOCKER,
    EXPECTED_ORIGIN_MAIN_SHA,
    NEXT_OWNER_GO_REQUIRED,
    OWNER_GO,
    REASON_ACCOUNT_BINDING_MISMATCH,
    REASON_EXTERNAL_FORENSIC_ARTIFACT_REQUIRED,
    REASON_IMPLICIT_NORMALIZATION_FORBIDDEN,
    REASON_INSTRUMENT_BINDING_MISMATCH,
    REASON_JSON_MALFORMED,
    REASON_TIME_BINDING_MISMATCH,
    REASON_UNKNOWN_SOURCE_KIND,
    REASON_VALID_CANDIDATE,
    SCHEMA_CLASS,
    VALIDATION_CONTRADICTORY,
    VALIDATION_INCOMPLETE,
    VALIDATION_INVALID,
    VALIDATION_VALID,
    ArtifactBindingsV1,
    OwnerSuppliedBootstrapArtifactContractError,
    bind_option_d_reconstruction_v1,
    derive_kind_set_from_proven_source_v1,
    evaluate_owner_supplied_bootstrap_candidate_v1,
    evaluate_ratification_boundary_v1,
    evaluate_today_owner_supplied_bootstrap_artifact_boundary_v1,
    execute_live_equity_stock_owner_supplied_bootstrap_artifact_v1,
    fixture_expected_bindings_v1,
    fixture_owner_supplied_artifact_file_payload_v1,
    ingest_owner_supplied_bootstrap_artifact_v1,
    reject_claimed_artifact_authority_mutation_v1,
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
    REPO_ROOT
    / "docs/ops/specs/FULL_CORE_LIVE_EQUITY_STOCK_OWNER_SUPPLIED_BOOTSTRAP_ARTIFACT_WP1.md"
)
MOT_PATH = REPO_ROOT / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md"
ATLAS_PATH = REPO_ROOT / "docs/system_atlas/entities/catalog.yaml"
BQ_HEADING = "11.2.1.BQ FULL_CORE_LIVE_EQUITY_STOCK_BOOTSTRAP_STOCK_ACQUISITION"
BR_HEADING = "11.2.1.BR FULL_CORE_LIVE_EQUITY_STOCK_OWNER_SUPPLIED_BOOTSTRAP_ARTIFACT"
SEALED_BQ = REPO_ROOT / CANONICAL_BQ_PACK_RELPATH
CANONICAL_PACK = REPO_ROOT / CANONICAL_PACK_RELPATH
_AS_OF = "2026-09-14T17:00:00Z"


def _br_section() -> str:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    start = runbook.index(BR_HEADING)
    successor = "11.2.1.BS FULL_CORE_LIVE_EQUITY_STOCK_TODAY_INITIAL_STOCK_SOURCE_KIND"
    return runbook[start : runbook.index(successor, start)]


def _write_artifact(root: Path, payload: dict | bytes) -> Path:
    surface = root / CANONICAL_INPUT_SURFACE_RELPATH
    surface.mkdir(parents=True, exist_ok=True)
    path = surface / ARTIFACT_FILENAME
    if isinstance(payload, bytes):
        path.write_bytes(payload)
    else:
        path.write_text(
            json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True),
            encoding="utf-8",
        )
    return path


def _run(tmp_path: Path):
    return execute_live_equity_stock_owner_supplied_bootstrap_artifact_v1(
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        sealed_bq_pack=SEALED_BQ,
        repo_root=REPO_ROOT,
        evidence_root=tmp_path / "artifact",
        persist_as_of=_AS_OF,
    )


def test_sealed_bq_manifest_verifies() -> None:
    assert verify_manifest_sha256_v1(store_root=SEALED_BQ) == 0
    assert BQ_NEXT_OWNER_GO == OWNER_GO
    assert BQ_LIVE_BLOCKER == EARLIEST_LIVE_CRITICAL_PATH_BLOCKER


def test_owner_go_and_sha_mismatch_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(OwnerSuppliedBootstrapArtifactContractError, match="OWNER_GO_MISMATCH"):
        execute_live_equity_stock_owner_supplied_bootstrap_artifact_v1(
            owner_go="WRONG",
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            sealed_bq_pack=SEALED_BQ,
            repo_root=REPO_ROOT,
            evidence_root=tmp_path / "artifact",
            persist_as_of=_AS_OF,
        )
    with pytest.raises(
        OwnerSuppliedBootstrapArtifactContractError, match="ORIGIN_MAIN_SHA_MISMATCH"
    ):
        execute_live_equity_stock_owner_supplied_bootstrap_artifact_v1(
            owner_go=OWNER_GO,
            origin_main_sha="0" * 40,
            sealed_bq_pack=SEALED_BQ,
            repo_root=REPO_ROOT,
            evidence_root=tmp_path / "artifact",
            persist_as_of=_AS_OF,
        )


def test_missing_artifact_fail_closed() -> None:
    ingest = ingest_owner_supplied_bootstrap_artifact_v1(repo_root=REPO_ROOT)
    assert ingest.artifact_present == "false"
    assert ingest.raw_bytes_preserved == "true"
    assert ingest.artifact_sha256 == ""
    record = evaluate_owner_supplied_bootstrap_candidate_v1(repo_root=REPO_ROOT)
    assert record.validation_status == VALIDATION_INCOMPLETE
    assert record.reason_code == REASON_EXTERNAL_FORENSIC_ARTIFACT_REQUIRED
    assert record.initial_stock_candidate_status == "ABSENT"
    assert record.initial_stock_anchor_status == "ABSENT"


def test_malformed_schema_invalid(tmp_path: Path) -> None:
    _write_artifact(tmp_path, b"{not-json\n")
    record = evaluate_owner_supplied_bootstrap_candidate_v1(
        repo_root=tmp_path,
        expected_bindings=fixture_expected_bindings_v1(),
    )
    assert record.validation_status == VALIDATION_INVALID
    assert record.reason_code == REASON_JSON_MALFORMED
    assert record.initial_stock_candidate_status == "ABSENT"
    assert record.artifact_sha256 != ""


def test_digest_provenance_mismatch(tmp_path: Path) -> None:
    payload, file_bytes, _inner = fixture_owner_supplied_artifact_file_payload_v1()
    payload["raw_evidence"] = "not-the-declared-raw"
    _write_artifact(tmp_path, payload)
    record = evaluate_owner_supplied_bootstrap_candidate_v1(
        repo_root=tmp_path,
        expected_bindings=fixture_expected_bindings_v1(),
    )
    assert record.validation_status == VALIDATION_CONTRADICTORY
    assert "RAW_BYTES_DIGEST_MISMATCH" in record.failures or record.reason_code in {
        "RAW_EVIDENCE_DIGEST_MISMATCH"
    }
    assert record.initial_stock_anchor_status == "ABSENT"
    assert file_bytes


def test_account_instrument_time_mismatch(tmp_path: Path) -> None:
    payload, file_bytes, _inner = fixture_owner_supplied_artifact_file_payload_v1()
    _write_artifact(tmp_path, file_bytes)
    account = evaluate_owner_supplied_bootstrap_candidate_v1(
        repo_root=tmp_path,
        expected_bindings=ArtifactBindingsV1(
            account_identity="OTHER_ACCOUNT",
            instrument_identity="ACCOUNT_LEVEL",
            as_of_time=str(payload["as_of_time"]),
            settlement_currency=str(payload["settlement_currency"]),
        ),
    )
    assert account.reason_code == REASON_ACCOUNT_BINDING_MISMATCH
    assert account.validation_status == VALIDATION_CONTRADICTORY
    instrument = evaluate_owner_supplied_bootstrap_candidate_v1(
        repo_root=tmp_path,
        expected_bindings=ArtifactBindingsV1(
            account_identity=str(payload["account_identity"]),
            instrument_identity="BTC-USDT-SWAP",
            as_of_time=str(payload["as_of_time"]),
            settlement_currency=str(payload["settlement_currency"]),
        ),
    )
    assert instrument.reason_code == REASON_INSTRUMENT_BINDING_MISMATCH
    time_mismatch = evaluate_owner_supplied_bootstrap_candidate_v1(
        repo_root=tmp_path,
        expected_bindings=ArtifactBindingsV1(
            account_identity=str(payload["account_identity"]),
            instrument_identity="ACCOUNT_LEVEL",
            as_of_time="1999-01-01T00:00:00Z",
            settlement_currency=str(payload["settlement_currency"]),
        ),
    )
    assert time_mismatch.reason_code == REASON_TIME_BINDING_MISMATCH


def test_unknown_source_kind(tmp_path: Path) -> None:
    payload, _file_bytes, _inner = fixture_owner_supplied_artifact_file_payload_v1()
    payload["source_type"] = "LEGACY_MYSTERY_KIND"
    _write_artifact(tmp_path, payload)
    record = evaluate_owner_supplied_bootstrap_candidate_v1(
        repo_root=tmp_path,
        expected_bindings=fixture_expected_bindings_v1(),
    )
    assert record.reason_code in {REASON_UNKNOWN_SOURCE_KIND, "SOURCE_TYPE_FORBIDDEN"}
    assert record.validation_status == VALIDATION_INVALID
    assert record.initial_stock_candidate_status == "ABSENT"
    assert record.live_equity_stock_kind_set == KIND_SET_EMPTY


def test_contradictory_evidence(tmp_path: Path) -> None:
    payload, _file_bytes, _inner = fixture_owner_supplied_artifact_file_payload_v1()
    payload["input_digest"] = "d" * 64
    _write_artifact(tmp_path, payload)
    record = evaluate_owner_supplied_bootstrap_candidate_v1(
        repo_root=tmp_path,
        expected_bindings=fixture_expected_bindings_v1(),
    )
    assert record.validation_status == VALIDATION_CONTRADICTORY
    assert record.initial_stock_candidate_status == "ABSENT"


def test_forbidden_implicit_normalization(tmp_path: Path) -> None:
    payload, _file_bytes, _inner = fixture_owner_supplied_artifact_file_payload_v1()
    payload["equity_value"] = 100
    _write_artifact(tmp_path, payload)
    record = evaluate_owner_supplied_bootstrap_candidate_v1(
        repo_root=tmp_path,
        expected_bindings=fixture_expected_bindings_v1(),
    )
    assert record.reason_code in {
        REASON_IMPLICIT_NORMALIZATION_FORBIDDEN,
        REASON_MALFORMED_FIELD,
    }
    assert record.validation_status == VALIDATION_INVALID
    assert record.initial_stock_candidate_status == "ABSENT"
    assert "IMPLICIT_COERCE_FORBIDDEN:equity_value" in record.failures


def test_valid_unratified_candidate_remains_non_anchor(tmp_path: Path) -> None:
    _payload, file_bytes, _inner = fixture_owner_supplied_artifact_file_payload_v1()
    path = _write_artifact(tmp_path, file_bytes)
    record = evaluate_owner_supplied_bootstrap_candidate_v1(
        repo_root=tmp_path,
        expected_bindings=fixture_expected_bindings_v1(),
    )
    assert record.validation_status == VALIDATION_VALID
    assert record.reason_code == REASON_VALID_CANDIDATE
    assert record.initial_stock_candidate_status == "PRESENT_UNRATIFIED"
    assert record.initial_stock_anchor_status == "ABSENT"
    assert record.ratification_status == "NOT_RATIFIED"
    assert record.source_class == ADMISSIBLE_SOURCE_CLASS
    assert record.artifact_sha256 == hashlib.sha256(path.read_bytes()).hexdigest()
    ratification = evaluate_ratification_boundary_v1(record)
    assert ratification.ratification_status == "RATIFICATION_AUTHORITY_ABSENT"
    assert ratification.candidate_promoted_to_anchor == "false"
    assert derive_kind_set_from_proven_source_v1(record, ratification) == KIND_SET_EMPTY


def test_kind_set_empty_without_proven_source() -> None:
    record = evaluate_owner_supplied_bootstrap_candidate_v1(repo_root=REPO_ROOT)
    ratification = evaluate_ratification_boundary_v1(record)
    assert derive_kind_set_from_proven_source_v1(record, ratification) == KIND_SET_EMPTY
    assert (
        ratified_live_equity_stock_kind_set_v1(evaluate_today_live_equity_stock_kind_set_v1()) == ()
    )


def test_venue_eq_cannot_become_source_authority(tmp_path: Path) -> None:
    payload, _file_bytes, _inner = fixture_owner_supplied_artifact_file_payload_v1()
    payload["artifact_class"] = "VENUE_EQ"
    _write_artifact(tmp_path, payload)
    record = evaluate_owner_supplied_bootstrap_candidate_v1(
        repo_root=tmp_path,
        expected_bindings=fixture_expected_bindings_v1(),
    )
    assert record.reason_code == "CLAIMED_VENUE_EQ_SOURCE_FORBIDDEN"
    assert record.initial_stock_candidate_status == "ABSENT"
    reconstruction = bind_option_d_reconstruction_v1(
        record, evaluate_ratification_boundary_v1(record)
    )
    assert reconstruction.venue_eq_source_authority == "false"
    assert RAW_EQ_SOURCE_AUTHORITY is False


def test_checkpoint_cannot_mint_equity(tmp_path: Path) -> None:
    payload, _file_bytes, _inner = fixture_owner_supplied_artifact_file_payload_v1()
    payload["artifact_class"] = "CHECKPOINT"
    _write_artifact(tmp_path, payload)
    record = evaluate_owner_supplied_bootstrap_candidate_v1(
        repo_root=tmp_path,
        expected_bindings=fixture_expected_bindings_v1(),
    )
    assert record.reason_code == "CLAIMED_CHECKPOINT_MINT_FORBIDDEN"
    reconstruction = bind_option_d_reconstruction_v1(
        record, evaluate_ratification_boundary_v1(record)
    )
    assert reconstruction.checkpoint_mints_equity == "false"
    assert CHECKPOINT_CAN_MINT_EQUITY is False
    assert reconstruction.running_equity_reconstruction_status == ("BLOCKED_NO_RATIFIED_ANCHOR")


def test_protected_surfaces_structurally_unchanged() -> None:
    assert DIMENSION_EQUITY_STOCK != DIMENSION_AVAILABLE_FOR_SIZING
    assert DIMENSION_P01_RISK_CAPITAL_REDUCTION != DIMENSION_EQUITY_STOCK
    assert LIVE_ENABLED is True
    assert LIVE_ARMED is True
    assert WIRE_SEND_PERMITTED is True
    assert KIND_SET_RESOLVED is False
    assert MS2_AUTHORIZED is False
    assert RAW_EQ_SOURCE_AUTHORITY is False


@pytest.mark.parametrize(
    "claimed_proof",
    [
        DECISION_INCLUDE,
        DECISION_EXCLUDE,
        "EXECUTE_GATE_A",
        "INVENT_LIVE_SOURCE_KIND",
        "PROMOTE_EQ_TO_SOURCE",
        "CHECKPOINT_MINT_EQUITY",
        "MINT_INITIAL_STOCK",
        "PROMOTE_CANDIDATE_TO_ANCHOR",
        "INVENT_OWNER_ARTIFACT",
        "NORMALIZE_UNKNOWN_TOKEN",
        "INTERPRET_MISSING_AS_ZERO",
    ],
)
def test_forbidden_authority_mutations_fail_closed(claimed_proof: str) -> None:
    with pytest.raises(
        OwnerSuppliedBootstrapArtifactContractError, match="ARTIFACT_INGEST_CANNOT_"
    ):
        reject_claimed_artifact_authority_mutation_v1(
            claimed_proof=claimed_proof,
            artifact_id="FIXTURE",
        )


def test_deterministic_replay_and_reconstruction_binding() -> None:
    first = evaluate_today_owner_supplied_bootstrap_artifact_boundary_v1(repo_root=REPO_ROOT)
    second = evaluate_today_owner_supplied_bootstrap_artifact_boundary_v1(repo_root=REPO_ROOT)
    assert first == second
    assert first.forensic_artifact_present == "false"
    assert first.candidate_validation_status == VALIDATION_INCOMPLETE
    assert first.initial_stock_candidate_status == "ABSENT"
    assert first.initial_stock_anchor_status == "ABSENT"
    assert first.live_equity_stock_kind_set == KIND_SET_EMPTY
    assert first.ratification_status == "RATIFICATION_AUTHORITY_ABSENT"
    assert first.checkpoint_status == "NON_SOURCE_NO_BOUND_STOCK"
    assert first.event_stream_binding_status == "FLOW_NOT_STOCK"
    assert first.running_equity_reconstruction_status == "BLOCKED_NO_RATIFIED_ANCHOR"
    assert first.venue_eq_reconciliation_status == "WITNESS_UNBOUND_NO_RECONSTRUCTED_STOCK"
    assert first.venue_eq_source_authority == "false"
    assert first.checkpoint_mints_equity == "false"
    bq = evaluate_today_bootstrap_stock_acquisition_boundary_v1(repo_root=REPO_ROOT)
    assert bq.forensic_artifact_present == "false"
    assert bq.initial_stock_anchor_status == "ABSENT"


def test_execute_persists_contract_and_protected_surfaces(tmp_path: Path) -> None:
    result = _run(tmp_path)
    assert result.forensic_artifact_present == "false"
    assert result.raw_evidence_preserved == "true"
    assert result.artifact_sha256 == "NONE"
    assert result.candidate_validation_status == VALIDATION_INCOMPLETE
    assert result.initial_stock_candidate_status == "ABSENT"
    assert result.initial_stock_anchor_status == "ABSENT"
    assert result.source_kind_status == "NONE"
    assert result.live_equity_stock_kind_set == KIND_SET_EMPTY
    assert result.ratification_status == "RATIFICATION_AUTHORITY_ABSENT"
    assert result.checkpoint_status == "NON_SOURCE_NO_BOUND_STOCK"
    assert result.event_stream_binding_status == "FLOW_NOT_STOCK"
    assert result.running_equity_reconstruction_status == "BLOCKED_NO_RATIFIED_ANCHOR"
    assert result.venue_eq_reconciliation_status == "WITNESS_UNBOUND_NO_RECONSTRUCTED_STOCK"
    assert result.venue_eq_source_authority == "false"
    assert result.checkpoint_mints_equity == "false"
    assert result.kinds_invented_this_go == "false"
    assert result.legacy_semantics_reconstructed == "false"
    assert result.earliest_live_critical_path_blocker == EARLIEST_LIVE_CRITICAL_PATH_BLOCKER
    assert result.next_owner_go_required == NEXT_OWNER_GO_REQUIRED
    assert result.venue_get_count == "0"
    assert result.venue_post_count == "0"
    assert result.gate_a_executed == "false"
    assert result.gate_b_executed == "false"
    assert LIVE_ENABLED is True
    assert LIVE_ARMED is True
    assert WIRE_SEND_PERMITTED is True
    assert EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY == (
        "TRUSTED_29P_PRETRADE_LIVE_ACCOUNT_BOUND_AND_INSTRUMENT_SCOPE_OWNER_GOS"
    )
    store = Path(result.store_root)
    assert verify_manifest_sha256_v1(store_root=store) == 0
    claims = json.loads((store / "claims.json").read_text(encoding="utf-8"))
    assert claims["BQ_CONTRACT_REUSED"] == "true"
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
    assert claims["PROTECTED_SURFACES_UNCHANGED"] == "true"
    assert claims["FORENSIC_ARTIFACT_PRESENT"] == "false"
    assert SCHEMA_CLASS == "OWNER_SUPPLIED_BOOTSTRAP_ARTIFACT_INGEST_V1"


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
    assert claims["FORENSIC_ARTIFACT_PRESENT"] == "false"
    assert claims["CANDIDATE_VALIDATION_STATUS"] == VALIDATION_INCOMPLETE
    assert claims["INITIAL_STOCK_CANDIDATE_STATUS"] == "ABSENT"
    assert claims["INITIAL_STOCK_ANCHOR_STATUS"] == "ABSENT"
    assert claims["RATIFICATION_STATUS"] == "RATIFICATION_AUTHORITY_ABSENT"
    assert claims["CHECKPOINT_MINTS_EQUITY"] == "false"
    assert claims["VENUE_EQ_SOURCE_AUTHORITY"] == "false"
    assert claims["VENUE_GET_COUNT"] == "0"
    assert claims["KINDS_INVENTED_THIS_GO"] == "false"
    assert claims["EARLIEST_LIVE_CRITICAL_PATH_BLOCKER"] == EARLIEST_LIVE_CRITICAL_PATH_BLOCKER


def test_runbook_br_and_navigation_persist() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    mot = MOT_PATH.read_text(encoding="utf-8")
    atlas = ATLAS_PATH.read_text(encoding="utf-8")
    runbook = RUNBOOK.read_text(encoding="utf-8")
    assert BQ_HEADING in runbook
    br_section = _br_section()
    assert OWNER_GO in br_section
    assert (
        "THIS_SLICE=11.2.1.BR.FULL_CORE_LIVE_EQUITY_STOCK_OWNER_SUPPLIED_BOOTSTRAP_ARTIFACT"
        in br_section
    )
    assert "NEW_CANONICAL_DEFINITION=true" in br_section
    assert "LEGACY_SEMANTICS_RECONSTRUCTED=false" in br_section
    assert "CHECKPOINT_MINTS_EQUITY=false" in br_section
    assert "VENUE_EQ_SOURCE_AUTHORITY=false" in br_section
    assert "BQ_CONTRACT_REUSED=true" in br_section
    assert "FORENSIC_ARTIFACT_PRESENT=false" in br_section
    assert "CANDIDATE_VALIDATION_STATUS=INCOMPLETE" in br_section
    assert "INITIAL_STOCK_CANDIDATE_STATUS=ABSENT" in br_section
    assert "INITIAL_STOCK_ANCHOR_STATUS=ABSENT" in br_section
    assert "LIVE_EQUITY_STOCK_KIND_SET=EMPTY_FAIL_CLOSED" in br_section
    assert "RATIFICATION_STATUS=RATIFICATION_AUTHORITY_ABSENT" in br_section
    assert "KINDS_INVENTED_THIS_GO=false" in br_section
    assert "GATE_A_EXECUTED=false" in br_section
    assert "VENUE_GET_COUNT=0" in br_section
    assert "D6_FULLY_CLOSED=false" in br_section
    assert EARLIEST_LIVE_CRITICAL_PATH_BLOCKER in br_section
    assert NEXT_OWNER_GO_REQUIRED in br_section
    assert "DOCS_TOKEN_FULL_CORE_LIVE_EQUITY_STOCK_OWNER_SUPPLIED_BOOTSTRAP_ARTIFACT_WP1" in spec
    assert "FULL_CORE_LIVE_EQUITY_STOCK_OWNER_SUPPLIED_BOOTSTRAP_ARTIFACT_WP1.md" in mot
    assert BR_HEADING in mot
    assert "ATLAS_AUTHORITY=NONE" in atlas
    assert "11.2.1.BR" in atlas
    assert "live_equity_stock_owner_supplied_bootstrap_artifact_v1.py" in atlas
