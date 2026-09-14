"""U05 concrete primary-proof GET-surface binding tests.

No GET. No POST. No GATE_A retry. No GATE_B. No bills/fills relabel.
Absent proof remains nonqualifying. U05 remains REMAIN_UNKNOWN.
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
from src.ops.governed_productive_account_equity_authority_producer_v1.u05_concrete_primary_proof_get_surface_binding_v1 import (
    ARCHITECTURE_BLOCKER,
    BLOCKER_ID,
    CANONICAL_PACK_RELPATH,
    CANONICAL_PERSIST_AS_OF,
    DECISION_BASIS,
    EXPECTED_ORIGIN_MAIN_SHA,
    NEXT_OWNER_GO,
    OWNER_GO,
    PRIMARY_PROOF_STATUS,
    SELECTION_STATUS,
    SERIOUS_CANDIDATE_SURFACES,
    U05ConcretePrimaryProofGetSurfaceBindingError,
    build_u05_concrete_get_surface_candidate_adjudication_v1,
    execute_u05_concrete_primary_proof_get_surface_binding_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.u05_independent_liability_event_and_non_algebraic_embedding_identity_primary_proof_acquisition_v1 import (
    CANDIDATE_SURFACE_BILLS_ARCHIVE,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
SPEC_PATH = (
    REPO_ROOT / "docs/ops/specs/FULL_CORE_BIND_CONCRETE_U05_PRIMARY_PROOF_GET_SURFACE_"
    "FAIL_CLOSED_NONE_BINDABLE_V1.md"
)
MOT_PATH = REPO_ROOT / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md"
ATLAS_PATH = REPO_ROOT / "docs/system_atlas/entities/catalog.yaml"
GENESIS_STORE = (
    REPO_ROOT / "evidence/ops/full_core_d6_path_b_d4_d5_genesis_rebaseline_v1/2026-09-13T170318Z"
)
CANONICAL_PACK = REPO_ROOT / CANONICAL_PACK_RELPATH
CA_HEADING = (
    "11.2.1.CA FULL_CORE_BIND_CONCRETE_U05_PRIMARY_PROOF_GET_SURFACE_FAIL_CLOSED_NONE_BINDABLE"
)


def _ca_section() -> str:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    start = runbook.index(CA_HEADING)
    return runbook[start : runbook.index("## 11.3 Autonomy state model", start)]


def _copy_genesis(tmp_path: Path) -> Path:
    dest = tmp_path / "genesis"
    shutil.copytree(GENESIS_STORE, dest)
    return dest


def _run(*, tmp_path: Path, vault_file: Path | None = None):
    genesis = _copy_genesis(tmp_path)
    return execute_u05_concrete_primary_proof_get_surface_binding_v1(
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
        U05ConcretePrimaryProofGetSurfaceBindingError,
        match="OWNER_GO_MISMATCH",
    ):
        execute_u05_concrete_primary_proof_get_surface_binding_v1(
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
        U05ConcretePrimaryProofGetSurfaceBindingError,
        match="ORIGIN_MAIN_SHA_MISMATCH",
    ):
        execute_u05_concrete_primary_proof_get_surface_binding_v1(
            owner_go=OWNER_GO,
            origin_main_sha="0" * 40,
            evidence_root=tmp_path / "obs",
            repo_root=REPO_ROOT,
            genesis_store_root=genesis,
            persist_as_of=CANONICAL_PERSIST_AS_OF,
        )
    assert not (tmp_path / "obs").exists()


def test_candidates_are_exactly_four_and_none_bindable() -> None:
    payload = build_u05_concrete_get_surface_candidate_adjudication_v1()
    records = payload["records"]
    assert payload["candidate_count"] == "4"
    assert payload["selection_status"] == SELECTION_STATUS
    assert payload["selected_surface_id"] == "NONE"
    assert payload["u05_primary_proof_role_bound"] == "false"
    assert SERIOUS_CANDIDATE_SURFACES == (
        SELECTED_BALANCE_SURFACE,
        CANDIDATE_SURFACE_ACCOUNT_BILLS,
        CANDIDATE_SURFACE_BILLS_ARCHIVE,
        CANDIDATE_SURFACE_TRADE_FILLS,
    )
    assert [item["surface_id"] for item in records] == list(SERIOUS_CANDIDATE_SURFACES)
    for item in records:
        assert item["bindable"] == "false"
        assert item["u05_primary_proof_role"] == "NONE"
        assert item["http_method"] == "GET"
    assert records[0]["not_bindable_reason"].startswith("BALANCE_SNAPSHOT")
    assert "BILLS_MAY_INFORM_FEE_OR_EXOGENOUS" in records[1]["not_bindable_reason"]
    assert "BILLS_ARCHIVE_SAME_UNCLASSIFIED" in records[2]["not_bindable_reason"]
    assert "FILLS_ARE_TRADE_EXECUTION" in records[3]["not_bindable_reason"]


def test_execute_persists_fail_closed_without_get(tmp_path: Path) -> None:
    result = _run(tmp_path=tmp_path)
    claims = json.loads((Path(result.store_root) / "claims.json").read_text(encoding="utf-8"))
    surface = json.loads(
        (Path(result.store_root) / "acquisition_surface_binding_v1.json").read_text(
            encoding="utf-8"
        )
    )
    candidates = json.loads(
        (Path(result.store_root) / "candidate_surface_capability_adjudication_v1.json").read_text(
            encoding="utf-8"
        )
    )
    architecture = json.loads(
        (Path(result.store_root) / "architecture_blocker_v1.json").read_text(encoding="utf-8")
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
    assert result.concrete_surface_candidate_count == "4"
    assert result.concrete_surface_selection_status == SELECTION_STATUS
    assert result.concrete_surface_id == "NONE"
    assert result.surface_binding_status == "NOT_BOUND"
    assert result.authorized_get_count == "0"
    assert result.actual_get_count == "0"
    assert result.post_count == "0"
    assert result.productive_acquisition_executed == "false"
    assert result.u05_decision_after == DECISION_REMAIN_UNKNOWN
    assert result.u05_decision_basis == DECISION_BASIS
    assert result.u05_primary_proof_status == PRIMARY_PROOF_STATUS
    assert claims["U05_EVIDENCE_CLASS"] == CLASS_U05
    assert claims["AUTHORIZED_ACQUISITION_SURFACE"] == ACQUISITION_SURFACE
    assert claims["CONCRETE_SURFACE_ID"] == "NONE"
    assert claims["PRIMARY_PROOF_ROLE_BOUND"] == "false"
    assert claims["MAX_GET_COUNT"] == "0"
    assert claims["RETRY_ALLOWED"] == "false"
    assert claims["HOPE_GET_FORBIDDEN"] == "true"
    assert claims["PRODUCTIVE_ACQUISITION_AUTHORIZED"] == "false"
    assert claims["GATE_A_REOPENED"] == "false"
    assert claims["GATE_B_REEXECUTED"] == "false"
    assert claims["VENUE_EQ_SOURCE_AUTHORITY"] == "false"
    assert claims["ACCOUNT_BILLS_CANONICALIZED"] == "false"
    assert claims["U06_DECISION_UNCHANGED"] == DECISION_REMAIN_UNKNOWN
    assert claims["RESIDUAL_DECISION_UNCHANGED"] == DECISION_REMAIN_UNKNOWN
    assert claims["NEXT_OWNER_GO_REQUIRED"] == NEXT_OWNER_GO
    assert claims["BLOCKER_ID"] == BLOCKER_ID
    assert claims["ARCHITECTURE_BLOCKER"] == ARCHITECTURE_BLOCKER
    assert surface["surface_binding_status"] == "NOT_BOUND"
    assert surface["max_get_count"] == "0"
    assert candidates["selection_status"] == SELECTION_STATUS
    assert architecture["blocker_id"] == BLOCKER_ID
    assert predicates["independent_liability_event_proven"] == "false"
    assert predicates["d4_d5_binding_present"] == "true"
    assert predicates["p01_u05_overlap_disproven"] == "false"
    assert evaluation["law_outcome"] == OUTCOME_NONQUALIFYING
    assert evaluation["productive_acquisition_authorized"] == "false"
    assert vault["values_included"] == "false"
    assert vault["secret_resolution_status"] == "NOT_ATTEMPTED_NO_BINDABLE_CONCRETE_GET_SURFACE"
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
    assert claims["CONCRETE_SURFACE_SELECTION_STATUS"] == SELECTION_STATUS
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


def test_runbook_ca_persists_fail_closed_binding() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    mot = MOT_PATH.read_text(encoding="utf-8")
    atlas = ATLAS_PATH.read_text(encoding="utf-8")
    ca_section = _ca_section()
    assert OWNER_GO in ca_section
    assert (
        "THIS_SLICE=11.2.1.CA.FULL_CORE_BIND_CONCRETE_U05_PRIMARY_PROOF_GET_SURFACE_"
        "FAIL_CLOSED_NONE_BINDABLE" in ca_section
    )
    assert "CONCRETE_SURFACE_CANDIDATE_COUNT=4" in ca_section
    assert "CONCRETE_SURFACE_SELECTION_STATUS=NONE_BINDABLE" in ca_section
    assert "CONCRETE_SURFACE_ID=NONE" in ca_section
    assert "SURFACE_BINDING_STATUS=NOT_BOUND" in ca_section
    assert "AUTHORIZED_GET_COUNT=0" in ca_section
    assert "ACTUAL_GET_COUNT=0" in ca_section
    assert "POST_COUNT=0" in ca_section
    assert "PRODUCTIVE_ACQUISITION_EXECUTED=false" in ca_section
    assert "U05_DECISION_AFTER=REMAIN_UNKNOWN" in ca_section
    assert "U06_DECISION_UNCHANGED=REMAIN_UNKNOWN" in ca_section
    assert "RESIDUAL_DECISION_UNCHANGED=REMAIN_UNKNOWN" in ca_section
    assert "GATE_A_REOPENED=false" in ca_section
    assert "GATE_B_REEXECUTED=false" in ca_section
    assert "VENUE_EQ_SOURCE_AUTHORITY=false" in ca_section
    assert "ACCOUNT_BILLS_CANONICALIZED=false" in ca_section
    assert BLOCKER_ID in ca_section
    assert NEXT_OWNER_GO in ca_section
    assert ARCHITECTURE_BLOCKER in ca_section
    assert EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY in ca_section
    assert "CURRENT_CANONICAL_SECTION=11.2.1.CA" in ca_section
    assert (
        "DOCS_TOKEN_FULL_CORE_BIND_CONCRETE_U05_PRIMARY_PROOF_GET_SURFACE_"
        "FAIL_CLOSED_NONE_BINDABLE_V1" in spec
    )
    assert (
        "FULL_CORE_BIND_CONCRETE_U05_PRIMARY_PROOF_GET_SURFACE_"
        "FAIL_CLOSED_NONE_BINDABLE_V1.md" in mot
    )
    assert CA_HEADING in mot
    assert "11.2.1.CA" in atlas
    assert "u05_concrete_primary_proof_get_surface_binding_v1.py" in atlas
    assert "ATLAS_AUTHORITY=NONE" in atlas
    assert U05_KIND_DECISION == DECISION_REMAIN_UNKNOWN
    assert U06_KIND_DECISION == DECISION_REMAIN_UNKNOWN
    assert RESIDUAL_KIND_DECISION == DECISION_REMAIN_UNKNOWN
    assert ACCOUNT_BILLS_REMAINS_CURRENT_NONCANONICAL is True
    assert EVENT_ACQUISITION_NETWORK_GET_AUTHORIZED is False
    assert CANDIDATE_SURFACE_SELECTION == "NONE_SELECTED"
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert WIRE_SEND_PERMITTED is False
    assert MS2_AUTHORIZED is False
    assert EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY == (
        "NO_CANONICALLY_VALID_ACCOUNT_EQUITY_SOURCE_MAPPING"
    )
