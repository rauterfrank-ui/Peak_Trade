"""U05 primary-proof forensic acquisition tests.

No GET. No POST. No GATE_A retry. No GATE_B. Absent proof remains
nonqualifying. U05 remains REMAIN_UNKNOWN.
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
    ACQUISITION_SURFACE,
    CLASS_U05,
    OUTCOME_NONQUALIFYING,
    evaluate_u05_primary_proof_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    ACCOUNT_BILLS_REMAINS_CURRENT_NONCANONICAL,
    CANDIDATE_SURFACE_SELECTION,
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
from src.ops.governed_productive_account_equity_authority_producer_v1.u05_independent_liability_event_and_non_algebraic_embedding_identity_primary_proof_acquisition_v1 import (
    BLOCKER_ID,
    CANONICAL_PACK_RELPATH,
    CANONICAL_PERSIST_AS_OF,
    DECISION_BASIS,
    EXPECTED_ORIGIN_MAIN_SHA,
    NEXT_OWNER_GO,
    OWNER_GO,
    PRIMARY_PROOF_STATUS,
    U05IndependentLiabilityEventPrimaryProofAcquisitionError,
    execute_u05_independent_liability_event_and_non_algebraic_embedding_identity_primary_proof_acquisition_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
SPEC_PATH = (
    REPO_ROOT
    / "docs/ops/specs/FULL_CORE_FORENSIC_ACQUISITION_OF_U05_INDEPENDENT_LIABILITY_EVENT_AND_NON_ALGEBRAIC_EMBEDDING_IDENTITY_PRIMARY_PROOF_V1.md"
)
MOT_PATH = REPO_ROOT / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md"
ATLAS_PATH = REPO_ROOT / "docs/system_atlas/entities/catalog.yaml"
GENESIS_STORE = (
    REPO_ROOT / "evidence/ops/full_core_d6_path_b_d4_d5_genesis_rebaseline_v1/2026-09-13T170318Z"
)
CANONICAL_PACK = REPO_ROOT / CANONICAL_PACK_RELPATH
BZ_HEADING = (
    "11.2.1.BZ FULL_CORE_FORENSIC_ACQUISITION_OF_U05_INDEPENDENT_LIABILITY_"
    "EVENT_AND_NON_ALGEBRAIC_EMBEDDING_IDENTITY_PRIMARY_PROOF"
)


def _bz_section() -> str:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    start = runbook.index(BZ_HEADING)
    return runbook[
        start : runbook.index(
            "11.2.1.CA FULL_CORE_BIND_CONCRETE_U05_PRIMARY_PROOF_GET_SURFACE_",
            start,
        )
    ]


def _copy_genesis(tmp_path: Path) -> Path:
    dest = tmp_path / "genesis"
    shutil.copytree(GENESIS_STORE, dest)
    return dest


def _run(*, tmp_path: Path, vault_file: Path | None = None):
    genesis = _copy_genesis(tmp_path)
    return execute_u05_independent_liability_event_and_non_algebraic_embedding_identity_primary_proof_acquisition_v1(
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
        U05IndependentLiabilityEventPrimaryProofAcquisitionError,
        match="OWNER_GO_MISMATCH",
    ):
        execute_u05_independent_liability_event_and_non_algebraic_embedding_identity_primary_proof_acquisition_v1(
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
        U05IndependentLiabilityEventPrimaryProofAcquisitionError,
        match="ORIGIN_MAIN_SHA_MISMATCH",
    ):
        execute_u05_independent_liability_event_and_non_algebraic_embedding_identity_primary_proof_acquisition_v1(
            owner_go=OWNER_GO,
            origin_main_sha="0" * 40,
            evidence_root=tmp_path / "obs",
            repo_root=REPO_ROOT,
            genesis_store_root=genesis,
            persist_as_of=CANONICAL_PERSIST_AS_OF,
        )
    assert not (tmp_path / "obs").exists()


def test_execute_persists_fail_closed_without_get(tmp_path: Path) -> None:
    result = _run(tmp_path=tmp_path)
    claims = json.loads((Path(result.store_root) / "claims.json").read_text(encoding="utf-8"))
    surface = json.loads(
        (Path(result.store_root) / "acquisition_surface_binding_v1.json").read_text(
            encoding="utf-8"
        )
    )
    predicates = json.loads(
        (Path(result.store_root) / "predicate_adjudication_v1.json").read_text(encoding="utf-8")
    )
    evaluation = json.loads(
        (Path(result.store_root) / "current_proof_evaluation_v1.json").read_text(encoding="utf-8")
    )
    vault = json.loads(
        (Path(result.store_root) / "vault_presence_v1.json").read_text(encoding="utf-8")
    )
    assert result.authorized_acquisition_surface == ACQUISITION_SURFACE
    assert result.authorized_get_count == "0"
    assert result.actual_get_count == "0"
    assert result.post_count == "0"
    assert result.productive_acquisition_executed == "false"
    assert result.u05_decision_after == DECISION_REMAIN_UNKNOWN
    assert result.u05_decision_basis == DECISION_BASIS
    assert result.non_algebraic_embedding_identity == "UNKNOWN"
    assert result.u05_primary_proof_status == PRIMARY_PROOF_STATUS
    assert claims["U05_EVIDENCE_CLASS"] == CLASS_U05
    assert claims["CONCRETE_GET_SURFACE"] == "NONE"
    assert claims["U05_PRIMARY_PROOF_ROLE_BOUND"] == "false"
    assert claims["GATE_A_REOPENED"] == "false"
    assert claims["GATE_B_REEXECUTED"] == "false"
    assert claims["VENUE_EQ_SOURCE_AUTHORITY"] == "false"
    assert claims["ACCOUNT_BILLS_CANONICALIZED"] == "false"
    assert claims["U06_DECISION_UNCHANGED"] == DECISION_REMAIN_UNKNOWN
    assert claims["RESIDUAL_DECISION_UNCHANGED"] == DECISION_REMAIN_UNKNOWN
    assert claims["NEXT_OWNER_GO_REQUIRED"] == NEXT_OWNER_GO
    assert claims["NEXT_ACTION"] == "STOP_ON_CONCRETE_AUTH_OR_ACQUISITION_BLOCKER"
    assert claims["BLOCKER_ID"] == BLOCKER_ID
    assert surface["authorized_get_count"] == "0"
    assert surface["hope_get_forbidden"] == "true"
    assert predicates["independent_liability_event_proven"] == "false"
    assert predicates["d4_d5_binding_present"] == "true"
    assert predicates["d4_d5_scope_identity_proven"] == "false"
    assert predicates["p01_u05_overlap_disproven"] == "false"
    assert evaluation["law_outcome"] == OUTCOME_NONQUALIFYING
    assert evaluation["u05_decision_after"] == DECISION_REMAIN_UNKNOWN
    assert vault["values_included"] == "false"
    assert vault["secret_resolution_status"] == "NOT_ATTEMPTED_CONCRETE_GET_SURFACE_UNBOUND"
    assert verify_manifest_sha256_v1(store_root=result.store_root) == 0
    files = {path.name for path in Path(result.store_root).iterdir() if path.is_file()}
    assert "raw_http_capture_v1.json" not in files
    assert "raw_account_balance_response_body.json" not in files


def test_absent_proof_remains_nonqualifying_not_exclude() -> None:
    outcome = evaluate_u05_primary_proof_v1(proof={})
    assert outcome.outcome == OUTCOME_NONQUALIFYING
    assert outcome.evidence_class_id == CLASS_U05


def test_canonical_pack_sealed_and_replay_stable() -> None:
    claims = json.loads((CANONICAL_PACK / "claims.json").read_text(encoding="utf-8"))
    assert claims["U05_DECISION_AFTER"] == DECISION_REMAIN_UNKNOWN
    assert claims["PRODUCTIVE_ACQUISITION_EXECUTED"] == "false"
    assert claims["AUTHORIZED_GET_COUNT"] == "0"
    assert claims["ACTUAL_GET_COUNT"] == "0"
    assert claims["POST_COUNT"] == "0"
    assert claims["U05_PRIMARY_PROOF_STATUS"] == PRIMARY_PROOF_STATUS
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


def test_runbook_bz_persists_fail_closed_acquisition() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    mot = MOT_PATH.read_text(encoding="utf-8")
    atlas = ATLAS_PATH.read_text(encoding="utf-8")
    bz_section = _bz_section()
    assert OWNER_GO in bz_section
    assert (
        "THIS_SLICE=11.2.1.BZ.FULL_CORE_FORENSIC_ACQUISITION_OF_U05_INDEPENDENT_"
        "LIABILITY_EVENT_AND_NON_ALGEBRAIC_EMBEDDING_IDENTITY_PRIMARY_PROOF" in bz_section
    )
    assert "AUTHORIZED_GET_COUNT=0" in bz_section
    assert "ACTUAL_GET_COUNT=0" in bz_section
    assert "POST_COUNT=0" in bz_section
    assert "PRODUCTIVE_ACQUISITION_EXECUTED=false" in bz_section
    assert "U05_DECISION_AFTER=REMAIN_UNKNOWN" in bz_section
    assert "U06_DECISION_UNCHANGED=REMAIN_UNKNOWN" in bz_section
    assert "RESIDUAL_DECISION_UNCHANGED=REMAIN_UNKNOWN" in bz_section
    assert "GATE_A_REOPENED=false" in bz_section
    assert "GATE_B_REEXECUTED=false" in bz_section
    assert "VENUE_EQ_SOURCE_AUTHORITY=false" in bz_section
    assert "ACCOUNT_BILLS_CANONICALIZED=false" in bz_section
    assert "NON_ALGEBRAIC_EMBEDDING_IDENTITY=UNKNOWN" in bz_section
    assert BLOCKER_ID in bz_section
    assert NEXT_OWNER_GO in bz_section
    assert EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY in bz_section
    assert "CURRENT_CANONICAL_SECTION=11.2.1.BZ" in bz_section
    assert (
        "DOCS_TOKEN_FULL_CORE_FORENSIC_ACQUISITION_OF_U05_INDEPENDENT_LIABILITY_"
        "EVENT_AND_NON_ALGEBRAIC_EMBEDDING_IDENTITY_PRIMARY_PROOF_V1" in spec
    )
    assert (
        "FULL_CORE_FORENSIC_ACQUISITION_OF_U05_INDEPENDENT_LIABILITY_EVENT_"
        "AND_NON_ALGEBRAIC_EMBEDDING_IDENTITY_PRIMARY_PROOF_V1.md" in mot
    )
    assert BZ_HEADING in mot
    assert "11.2.1.BZ" in atlas
    assert (
        "u05_independent_liability_event_and_non_algebraic_embedding_identity_"
        "primary_proof_acquisition_v1.py" in atlas
    )
    assert "ATLAS_AUTHORITY=NONE" in atlas
    assert U05_KIND_DECISION == DECISION_REMAIN_UNKNOWN
    assert U06_KIND_DECISION == DECISION_REMAIN_UNKNOWN
    assert RESIDUAL_KIND_DECISION == DECISION_REMAIN_UNKNOWN
    assert ACCOUNT_BILLS_REMAINS_CURRENT_NONCANONICAL is True
    assert EVENT_ACQUISITION_NETWORK_GET_AUTHORIZED is False
    assert CANDIDATE_SURFACE_SELECTION == "NONE_SELECTED"
    assert LIVE_ENABLED is True
    assert LIVE_ARMED is True
    assert WIRE_SEND_PERMITTED is True
    assert MS2_AUTHORIZED is False
    assert EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY == (
        "NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING"
    )
