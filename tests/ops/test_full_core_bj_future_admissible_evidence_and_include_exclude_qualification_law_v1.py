"""BJ future-admissible evidence-class and qualification-law tests.

Law persist only. No GET. No POST. No GATE_A retry. No GATE_B.
Law ratification does not decide U05/U06/Residual.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

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
    CANONICAL_PACK_RELPATH,
    CANONICAL_PERSIST_AS_OF,
    CLASS_RESIDUAL,
    CLASS_U05,
    CLASS_U06,
    EXPECTED_ORIGIN_MAIN_SHA,
    NEXT_OWNER_GO,
    NEW_FUTURE_ADMISSIBLE_EVIDENCE_CLASS_IDS,
    OLD_FUTURE_ADMISSIBLE_EVIDENCE_CLASSES,
    OUTCOME_EXCLUDE,
    OUTCOME_INCLUDE,
    OUTCOME_NONQUALIFYING,
    OWNER_GO,
    TARGET_RESIDUAL,
    TARGET_U05,
    TARGET_U06,
    BjFutureAdmissibleEvidenceAndQualificationLawError,
    evaluate_residual_primary_proof_v1,
    evaluate_u05_primary_proof_v1,
    evaluate_u06_primary_proof_v1,
    execute_bj_future_admissible_evidence_and_include_exclude_qualification_law_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.bj_remaining_unknown_kind_semantics_v1 import (
    FUTURE_ADMISSIBLE_EVIDENCE_CLASSES,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    ACCOUNT_BILLS_REMAINS_CURRENT_NONCANONICAL,
    D6_FULLY_CLOSED,
    RESIDUAL_KIND_DECISION,
    U05_KIND_DECISION,
    U06_KIND_DECISION,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.f12_f13_kind_set_remaining_unknown_pin_and_reopen_gate_v1 import (
    GATE_A_ID,
    GATE_B_ID,
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
    / "docs/ops/specs/FULL_CORE_BJ_FUTURE_ADMISSIBLE_EVIDENCE_AND_INCLUDE_EXCLUDE_QUALIFICATION_LAW_V1.md"
)
MOT_PATH = REPO_ROOT / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md"
ATLAS_PATH = REPO_ROOT / "docs/system_atlas/entities/catalog.yaml"
CANONICAL_PACK = REPO_ROOT / CANONICAL_PACK_RELPATH
BY_HEADING = (
    "11.2.1.BY FULL_CORE_BJ_FUTURE_ADMISSIBLE_EVIDENCE_AND_INCLUDE_EXCLUDE_QUALIFICATION_LAW"
)


def _by_section() -> str:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    start = runbook.index(BY_HEADING)
    return runbook[start : runbook.index("## 11.3 Autonomy state model", start)]


def _u05_include_proof() -> dict[str, str]:
    return {
        "unique_event_id": "LIAB-EVT-001",
        "event_digest": "a" * 64,
        "ordering_key": "2026-09-14T12:00:00Z",
        "bound_account_identity_ref": "D4_BOUND_ACCOUNT",
        "bound_account_identity_digest": "b" * 64,
        "prior_anchor_id": "GOVERNED_TODAY_INITIAL_STOCK_ANCHOR_5d6c32292e0cb733",
        "event_after_prior_as_of": "true",
        "liability_event_semantic_class": "INDEPENDENT_LIABILITY_STOCK_EVENT",
        "mapped_numeric_effect": "12.5",
        "currency_domain": "USDC",
        "embedding_state": "SEPARATE",
        "embedding_proof_id": "NON_ALGEBRAIC_EMBEDDING_001",
        "p01_overlap_state": "NON_OVERLAPPING",
        "independent_of_balance_snapshot": "true",
        "independent_of_algebraic_eq_identity": "true",
    }


def test_future_admissible_set_extends_without_dropping_gate_a_or_gate_b() -> None:
    assert GATE_A_ID in OLD_FUTURE_ADMISSIBLE_EVIDENCE_CLASSES
    assert GATE_B_ID in OLD_FUTURE_ADMISSIBLE_EVIDENCE_CLASSES
    assert NEW_FUTURE_ADMISSIBLE_EVIDENCE_CLASS_IDS == frozenset(
        {CLASS_U05, CLASS_U06, CLASS_RESIDUAL}
    )
    assert FUTURE_ADMISSIBLE_EVIDENCE_CLASSES == (
        OLD_FUTURE_ADMISSIBLE_EVIDENCE_CLASSES | NEW_FUTURE_ADMISSIBLE_EVIDENCE_CLASS_IDS
    )


def test_absent_proofs_are_nonqualifying_and_do_not_exclude() -> None:
    u05 = evaluate_u05_primary_proof_v1(proof={})
    u06 = evaluate_u06_primary_proof_v1(proof={})
    residual = evaluate_residual_primary_proof_v1(proof={})
    assert u05.outcome == OUTCOME_NONQUALIFYING
    assert u06.outcome == OUTCOME_NONQUALIFYING
    assert residual.outcome == OUTCOME_NONQUALIFYING
    assert u05.target_unknown == TARGET_U05
    assert u06.target_unknown == TARGET_U06
    assert residual.target_unknown == TARGET_RESIDUAL


def test_empty_zero_absent_is_not_u05_exclude() -> None:
    outcome = evaluate_u05_primary_proof_v1(proof={"mapped_numeric_effect": "0"})
    assert outcome.outcome == OUTCOME_NONQUALIFYING
    assert "EMPTY_ZERO_ABSENT" in outcome.basis


def test_gate_a_snapshot_token_is_not_u05_primary_proof() -> None:
    outcome = evaluate_u05_primary_proof_v1(proof={"balance_snapshot_liability_token": "12.5"})
    assert outcome.outcome == OUTCOME_NONQUALIFYING
    assert outcome.basis == "BALANCE_SNAPSHOT_TOKEN_IS_NOT_U05_PRIMARY_PROOF"


def test_retroactive_gate_a_pack_cannot_uplift() -> None:
    proof = _u05_include_proof()
    proof["source_pack"] = (
        "evidence/ops/full_core_option_d_gate_a_independently_attested_"
        "productive_nonzero_liability_stock_v1/2026-09-14T200500Z"
    )
    outcome = evaluate_u05_primary_proof_v1(proof=proof)
    assert outcome.outcome == OUTCOME_NONQUALIFYING
    assert "RETROACTIVE_UPLIFT_FORBIDDEN" in outcome.basis


def test_u05_synthetic_independent_separate_event_qualifies_include() -> None:
    outcome = evaluate_u05_primary_proof_v1(proof=_u05_include_proof())
    assert outcome.outcome == OUTCOME_INCLUDE
    assert outcome.evidence_class_id == CLASS_U05


def test_u05_in_base_embedding_qualifies_exclude_without_using_zero() -> None:
    proof = _u05_include_proof()
    proof["embedding_state"] = "IN_BASE"
    proof["p01_overlap_state"] = "U05_NOT_P01"
    outcome = evaluate_u05_primary_proof_v1(proof=proof)
    assert outcome.outcome == OUTCOME_EXCLUDE


def test_fee_token_alone_is_not_u06_proof() -> None:
    outcome = evaluate_u06_primary_proof_v1(proof={"fee_field_token_only": "true"})
    assert outcome.outcome == OUTCOME_NONQUALIFYING
    assert outcome.basis == "FEE_TOKEN_ALONE_IS_NOT_PRIMARY_PROOF"


def test_u06_paired_event_separate_qualifies_include() -> None:
    outcome = evaluate_u06_primary_proof_v1(
        proof={
            "unique_fee_event_id": "FEE-EVT-001",
            "event_digest": "c" * 64,
            "ordering_key": "2026-09-14T12:01:00Z",
            "bound_account_identity_ref": "D4_BOUND_ACCOUNT",
            "bound_account_identity_digest": "d" * 64,
            "prior_anchor_id": "GOVERNED_TODAY_INITIAL_STOCK_ANCHOR_5d6c32292e0cb733",
            "event_after_prior_as_of": "true",
            "fee_amount": "0.25",
            "currency_domain": "USDC",
            "pairing_status": "PAIRED",
            "base_or_event_or_reconciliation": "EVENT_SEPARATE",
            "pairing_equity_stock_observation_id": "EQ-OBS-001",
            "pairing_observation_is_not_raw_eq_source": "true",
            "pairing_delta_matches_fee": "true",
            "once_only_guard_id": "ONCE-001",
        }
    )
    assert outcome.outcome == OUTCOME_INCLUDE
    assert outcome.evidence_class_id == CLASS_U06


def test_hypothesis_list_is_not_residual_exhaustiveness() -> None:
    outcome = evaluate_residual_primary_proof_v1(
        proof={"necessary_kind_inventory": "DEPOSIT,WITHDRAWAL"}
    )
    assert outcome.outcome == OUTCOME_NONQUALIFYING
    assert outcome.basis == "HYPOTHESIS_ONLY_LIST_IS_NOT_EXHAUSTIVENESS_PROOF"


def test_residual_positive_certificate_qualifies_exclude() -> None:
    outcome = evaluate_residual_primary_proof_v1(
        proof={
            "exhaustiveness_certificate_id": "EXH-001",
            "certificate_digest": "e" * 64,
            "independent_taxonomy_authority": "INDEPENDENT_TAXONOMY_AUTHORITY_V1",
            "necessary_kind_inventory": "F12,F13",
            "window_id": "D5_WINDOW",
            "bound_account_identity_ref": "D4_BOUND_ACCOUNT",
            "bound_account_identity_digest": "f" * 64,
            "proven_complete": "true",
        }
    )
    assert outcome.outcome == OUTCOME_EXCLUDE
    assert outcome.evidence_class_id == CLASS_RESIDUAL


def test_execute_persists_law_without_deciding_unknowns(tmp_path: Path) -> None:
    result = execute_bj_future_admissible_evidence_and_include_exclude_qualification_law_v1(
        owner_go=OWNER_GO,
        origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
        evidence_root=tmp_path,
        persist_as_of=CANONICAL_PERSIST_AS_OF,
    )
    claims = json.loads((tmp_path / "claims.json").read_text(encoding="utf-8"))
    evaluation = json.loads(
        (tmp_path / "current_proof_evaluation_v1.json").read_text(encoding="utf-8")
    )
    assert result.qualification_law_change_status == "RATIFIED"
    assert result.u05_decision_after == DECISION_REMAIN_UNKNOWN
    assert result.u06_decision_after == DECISION_REMAIN_UNKNOWN
    assert result.residual_decision_after == DECISION_REMAIN_UNKNOWN
    assert result.productive_acquisition_executed == "false"
    assert claims["U05_DECISION_AFTER"] == DECISION_REMAIN_UNKNOWN
    assert claims["GATE_A_RETRY_EXECUTED"] == "false"
    assert claims["GATE_B_REEXECUTED"] == "false"
    assert claims["VENUE_EQ_SOURCE_AUTHORITY"] == "false"
    assert claims["ACCOUNT_BILLS_CANONICALIZED"] == "false"
    assert claims["NEXT_OWNER_GO_REQUIRED"] == NEXT_OWNER_GO
    assert evaluation["current_primary_proof_present"] == "false"
    for record in evaluation["records"]:
        assert record["outcome"] == OUTCOME_NONQUALIFYING
    assert verify_manifest_sha256_v1(store_root=tmp_path) == 0


def test_wrong_owner_go_fail_closed(tmp_path: Path) -> None:
    try:
        execute_bj_future_admissible_evidence_and_include_exclude_qualification_law_v1(
            owner_go="WRONG",
            origin_main_sha=EXPECTED_ORIGIN_MAIN_SHA,
            evidence_root=tmp_path,
            persist_as_of=CANONICAL_PERSIST_AS_OF,
        )
    except BjFutureAdmissibleEvidenceAndQualificationLawError as exc:
        assert str(exc) == "OWNER_GO_MISMATCH"
    else:
        raise AssertionError("expected OWNER_GO_MISMATCH")


def test_canonical_pack_sealed_and_replay_stable() -> None:
    claims = json.loads((CANONICAL_PACK / "claims.json").read_text(encoding="utf-8"))
    assert claims["QUALIFICATION_LAW_CHANGE_STATUS"] == "RATIFIED"
    assert claims["U05_DECISION_AFTER"] == DECISION_REMAIN_UNKNOWN
    assert claims["U06_DECISION_AFTER"] == DECISION_REMAIN_UNKNOWN
    assert claims["RESIDUAL_DECISION_AFTER"] == DECISION_REMAIN_UNKNOWN
    assert claims["PRODUCTIVE_ACQUISITION_EXECUTED"] == "false"
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


def test_runbook_by_persists_qualification_law() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    mot = MOT_PATH.read_text(encoding="utf-8")
    atlas = ATLAS_PATH.read_text(encoding="utf-8")
    by_section = _by_section()
    assert OWNER_GO in by_section
    assert (
        "THIS_SLICE=11.2.1.BY.FULL_CORE_BJ_FUTURE_ADMISSIBLE_EVIDENCE_AND_INCLUDE_EXCLUDE_QUALIFICATION_LAW"
        in by_section
    )
    assert "QUALIFICATION_LAW_CHANGE_STATUS=RATIFIED" in by_section
    assert "NEW_EVIDENCE_CLASS_COUNT=3" in by_section
    assert CLASS_U05 in by_section
    assert CLASS_U06 in by_section
    assert CLASS_RESIDUAL in by_section
    assert "U05_DECISION_AFTER=REMAIN_UNKNOWN" in by_section
    assert "U06_DECISION_AFTER=REMAIN_UNKNOWN" in by_section
    assert "RESIDUAL_DECISION_AFTER=REMAIN_UNKNOWN" in by_section
    assert "PRODUCTIVE_ACQUISITION_EXECUTED=false" in by_section
    assert "GATE_A_RETRY_EXECUTED=false" in by_section
    assert "GATE_B_REEXECUTED=false" in by_section
    assert "VENUE_EQ_SOURCE_AUTHORITY=false" in by_section
    assert "ACCOUNT_BILLS_CANONICALIZED=false" in by_section
    assert "RETROACTIVE_UPLIFT_FORBIDDEN=true" in by_section
    assert EARLIEST_UNRESOLVED_FULL_CORE_DEPENDENCY in by_section
    assert "CURRENT_CANONICAL_SECTION=11.2.1.BY" in by_section
    assert (
        "DOCS_TOKEN_FULL_CORE_BJ_FUTURE_ADMISSIBLE_EVIDENCE_AND_INCLUDE_EXCLUDE_QUALIFICATION_LAW_V1"
        in spec
    )
    assert (
        "FULL_CORE_BJ_FUTURE_ADMISSIBLE_EVIDENCE_AND_INCLUDE_EXCLUDE_QUALIFICATION_LAW_V1.md" in mot
    )
    assert BY_HEADING in mot
    assert "11.2.1.BY" in atlas
    assert "bj_future_admissible_evidence_and_include_exclude_qualification_law_v1.py" in atlas
    assert "ATLAS_AUTHORITY=NONE" in atlas
    assert U05_KIND_DECISION == DECISION_REMAIN_UNKNOWN
    assert U06_KIND_DECISION == DECISION_REMAIN_UNKNOWN
    assert RESIDUAL_KIND_DECISION == DECISION_REMAIN_UNKNOWN
    assert ACCOUNT_BILLS_REMAINS_CURRENT_NONCANONICAL is True
    assert D6_FULLY_CLOSED is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert WIRE_SEND_PERMITTED is False
    assert MS2_AUTHORIZED is False
