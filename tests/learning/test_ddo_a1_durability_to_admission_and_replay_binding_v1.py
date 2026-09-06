"""DDO A1 durability-to-admission and replay binding v1.

Observation-only. No trading authority. No runtime activation.
Reuses the existing admission owner. Does not create a new storage owner.
Does not manufacture durability_proven=True. Does not add an automatic retry loop.
"""

from __future__ import annotations

import ast
import errno
import os
import stat
from pathlib import Path
from typing import Any

import pytest

from src.governance.live_mode_gate import ExecutionEnvironment
from src.learning.deterministic_decision_outcome_v0.a1_crash_durability_atomic_replace_or_explicit_nonrequirement_v1 import (
    EVIDENCE_MUST_BE_DURABLE_BEFORE_DEPENDENT_MUTATION as CRASH_EVIDENCE_MUST_BE_DURABLE,
)
from src.learning.deterministic_decision_outcome_v0.a1_durability_failure_policy_binding_v1 import (
    A1_DURABILITY_FAILURE_POLICY,
    AMBIGUOUS_RETRY_ALLOWED as POLICY_AMBIGUOUS_RETRY_ALLOWED,
    CRASH_DURABILITY_FULLY_PROVEN as POLICY_CRASH_DURABILITY_FULLY_PROVEN,
    DdoA1DurabilityFailurePolicyError,
    bind_a1_durability_failure_policy_v1,
    reject_a1_dependent_mutation_on_unproven_durability_v1,
)
from src.learning.deterministic_decision_outcome_v0.a1_durability_to_admission_and_replay_binding_v1 import (
    ADMISSION_BINDING_STATUS,
    ADMISSION_OWNER,
    ADMISSION_OWNER_NAME,
    AUTOMATIC_RETRY_LOOP_ADDED,
    CAPTURE_OK_EQUALS_ADMISSION,
    CRASH_DURABILITY_FULLY_PROVEN,
    CURRENT_STAGE_CAPTURE_FAIL_OPEN,
    DEPENDENT_MUTATION_ADMISSION_STATE,
    DEPENDENT_MUTATION_ON_UNPROVEN_DURABILITY,
    DIRECTORY_FSYNC_POLICY,
    DUPLICATE_CONFLICT,
    DUPLICATE_CONFLICT_SEMANTICS,
    DURABILITY_FAILURE,
    DURABILITY_UNKNOWN,
    DdoA1DurabilityToAdmissionAndReplayBindingError,
    DdoA1DurabilityToAdmissionAndReplayBindingV1,
    EVIDENCE_MUST_BE_DURABLE_BEFORE_DEPENDENT_MUTATION,
    FILE_FSYNC_POLICY,
    IDEMPOTENT_REPLAY,
    IDEMPOTENT_REPLAY_EQUALS_CRASH_DURABILITY_PROOF,
    IDEMPOTENT_REPLAY_SEMANTICS,
    IMPLEMENTATION_COMPLETE,
    IMPLEMENTATION_GO_IS_RUNTIME_AUTHORIZATION,
    MASTER_V2_DOUBLE_PLAY_SOLE_TRADING_AUTHORITY,
    MISSING_UNCLASSIFIED_DURABILITY_EVIDENCE,
    NEW_ADMISSION_AUTHORITY_CREATED,
    NEW_STORAGE_AUTHORITY_CREATED,
    NEXT_DDO_STEP,
    NEXT_OWNER_GO_REQUIRED,
    PERSIST_WRITE_ACCEPTED,
    PRODUCTIVE_RETURN_VALUE_UNCHANGED,
    REPLAY_AMBIGUITY_BINDING_STATUS,
    RUNTIME_AUTHORIZATION_ELIGIBLE,
    RUNTIME_AUTHORIZED,
    RUNTIME_OPERATIONAL_AUTHORIZATION_SOURCE,
    SLICE_ID,
    TRADING_AUTHORITY_CHANGED,
    TRADING_DECISION_DEPENDS_ON_LEDGER_WRITE,
    UNATTENDED_OPERATION_STARTED,
    UNKNOWN_PRESERVED,
    a1_durability_to_admission_and_replay_observability_v1,
    attempt_a1_dependent_mutation_admission_v1,
    canonical_a1_durability_to_admission_and_replay_binding_v1,
    classify_a1_persist_attempt_for_admission_v1,
    evaluate_a1_dependent_mutation_admission_v1,
    reject_a1_runtime_authorization_attempt_on_admission_binding_v1,
)
from src.learning.deterministic_decision_outcome_v0.a1_unattended_durability_policy_boundary_v1 import (
    A1_UNATTENDED_DURABILITY_RUNTIME_AUTHORIZED,
)
from src.learning.deterministic_decision_outcome_v0.authority_v0 import (
    AUTHORITY_OWNER,
    LEARNING_PRODUCTIVE_AUTHORITY,
    LIVE_EFFECT,
    SECOND_EXECUTION_AUTHORITY_CREATED,
    SECOND_TRADING_AUTHORITY_CREATED,
)
from src.learning.deterministic_decision_outcome_v0.capture_v0 import (
    CAPTURE_FAILURE_CHANGES_DECISION,
)
from src.learning.deterministic_decision_outcome_v0.errors_v0 import (
    FAILURE_CLASS_FILESYSTEM_CAPACITY,
    FAILURE_CLASS_UNKNOWN_IO,
    OPERATION_DIRECTORY_FSYNC,
    OPERATION_DURABLE_APPEND,
    OPERATION_WRITE,
    DdoDuplicateConflictError,
    DdoDurabilityWriteError,
    DdoLedgerCorruptionError,
)
from src.learning.deterministic_decision_outcome_v0.ledger_v0 import AppendOnlyDdoLedgerV0
from src.ops.capability_11_2_credential_authorization_and_account_identity_boundary_v1.account_identity_boundary_v1 import (
    AccountIdentityRecordV1,
    build_account_identity_record_v1,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    LIVE_ARMED,
    LIVE_ENABLED,
    WIRE_SEND_PERMITTED,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.constants_v1 import (
    LIVE_AUTHORIZED,
    ORDERS_AUTHORIZED,
    PAPER_EXECUTION_AUTHORIZED,
    TESTNET_AUTHORIZED,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.decision_economics_cycle_bridge_v1 import (
    BridgeSessionStateV1,
    run_bridge_cycles_from_mids_v1,
)
from tests.learning.test_deterministic_decision_outcome_event_contract_v0 import _decision

REPO_ROOT = Path(__file__).resolve().parents[2]
LEDGER_SRC = REPO_ROOT / "src/learning/deterministic_decision_outcome_v0/ledger_v0.py"
CAPTURE_SRC = REPO_ROOT / "src/learning/deterministic_decision_outcome_v0/capture_v0.py"
BINDING_SRC = (
    REPO_ROOT
    / "src/learning/deterministic_decision_outcome_v0"
    / "a1_durability_to_admission_and_replay_binding_v1.py"
)
POLICY_SRC = (
    REPO_ROOT
    / "src/learning/deterministic_decision_outcome_v0"
    / "a1_durability_failure_policy_binding_v1.py"
)
ACCOUNT_TEST_IDENTITY = "acct-uid-test-a1-admission-replay"
ACCOUNT_TEST_CREDENTIAL_REF = "cred-ref-test-a1-admission-replay"
SESSION_ID = "ddo-a1-admission-replay"


def _account_record(*, identity: str = ACCOUNT_TEST_IDENTITY) -> AccountIdentityRecordV1:
    return build_account_identity_record_v1(
        account_identity=identity,
        venue="OKX",
        credential_ref_id=ACCOUNT_TEST_CREDENTIAL_REF,
        account_scope="trading-only",
        expected_uid=identity,
    )


def _run_bound_host(
    tmp_path: Path,
    *,
    session_id: str = SESSION_ID,
    mids: list[float] | None = None,
) -> tuple[BridgeSessionStateV1, list[Any]]:
    return run_bridge_cycles_from_mids_v1(
        mids if mids is not None else [3500.0],
        session_id=session_id,
        require_selection_binding=False,
        ddo_durable_evidence_runtime_state_root=tmp_path,
        ddo_evidence_environment=ExecutionEnvironment.DEV,
        ddo_account_identity_record=_account_record(),
    )


def _must_reject_admission(**kwargs: Any) -> None:
    with pytest.raises(DdoA1DurabilityFailurePolicyError) as exc:
        attempt_a1_dependent_mutation_admission_v1(**kwargs)
    assert exc.value.failure_class == "A1_DEPENDENT_MUTATION_FORBIDDEN_UNPROVEN_DURABILITY"


def test_binding_bound_and_runtime_flags_remain_false() -> None:
    binding = canonical_a1_durability_to_admission_and_replay_binding_v1()
    assert isinstance(binding, DdoA1DurabilityToAdmissionAndReplayBindingV1)
    assert binding.slice_id == SLICE_ID
    assert IMPLEMENTATION_COMPLETE is True
    assert ADMISSION_BINDING_STATUS == "BOUND_FAIL_CLOSED"
    assert REPLAY_AMBIGUITY_BINDING_STATUS == "BOUND_WITHOUT_AUTOMATIC_RETRY"
    assert ADMISSION_OWNER is reject_a1_dependent_mutation_on_unproven_durability_v1
    assert ADMISSION_OWNER_NAME == "reject_a1_dependent_mutation_on_unproven_durability_v1"
    assert NEW_ADMISSION_AUTHORITY_CREATED is False
    assert EVIDENCE_MUST_BE_DURABLE_BEFORE_DEPENDENT_MUTATION == CRASH_EVIDENCE_MUST_BE_DURABLE
    assert EVIDENCE_MUST_BE_DURABLE_BEFORE_DEPENDENT_MUTATION.startswith("BOUND_FAIL_CLOSED_")
    assert "UNBOUND" not in EVIDENCE_MUST_BE_DURABLE_BEFORE_DEPENDENT_MUTATION
    assert CURRENT_STAGE_CAPTURE_FAIL_OPEN is True
    assert CAPTURE_FAILURE_CHANGES_DECISION is False
    assert CAPTURE_OK_EQUALS_ADMISSION is False
    assert RUNTIME_AUTHORIZATION_ELIGIBLE is False
    assert RUNTIME_AUTHORIZED is False
    assert UNATTENDED_OPERATION_STARTED is False
    assert IMPLEMENTATION_GO_IS_RUNTIME_AUTHORIZATION is False
    assert RUNTIME_OPERATIONAL_AUTHORIZATION_SOURCE == "NONE"
    assert NEXT_OWNER_GO_REQUIRED is True
    assert NEXT_DDO_STEP == (
        "OWNER_GO_REQUIRED_SEPARATE_SCOPED_DDO_A1_CONTINUATION_NOT_AUTHORIZED_BY_THIS_PERSIST"
    )
    assert A1_UNATTENDED_DURABILITY_RUNTIME_AUTHORIZED is False
    with pytest.raises(DdoA1DurabilityToAdmissionAndReplayBindingError):
        DdoA1DurabilityToAdmissionAndReplayBindingV1(runtime_authorized=True)
    with pytest.raises(DdoA1DurabilityToAdmissionAndReplayBindingError):
        DdoA1DurabilityToAdmissionAndReplayBindingV1(runtime_authorization_eligible=True)
    with pytest.raises(DdoA1DurabilityToAdmissionAndReplayBindingError):
        DdoA1DurabilityToAdmissionAndReplayBindingV1(
            evidence_must_be_durable_before_dependent_mutation=(
                "UNBOUND_FAIL_CLOSED_NOT_A_CURRENT_TRADING_PRECONDITION"
            )
        )
    with pytest.raises(DdoA1DurabilityToAdmissionAndReplayBindingError):
        reject_a1_runtime_authorization_attempt_on_admission_binding_v1(runtime_authorized=True)


def test_durability_proven_none_rejects_dependent_mutation() -> None:
    policy = bind_a1_durability_failure_policy_v1(
        operation=OPERATION_DURABLE_APPEND,
        failure=None,
    )
    assert policy.durability_proven is None
    evaluated = evaluate_a1_dependent_mutation_admission_v1(
        policy_result=policy,
        durability_proven=None,
    )
    assert evaluated.admitted is False
    assert evaluated.durability_proven is None
    _must_reject_admission(policy_result=policy, durability_proven=None)
    reject_a1_dependent_mutation_on_unproven_durability_v1(
        dependent_mutation_requested=False,
        durability_proven=None,
        policy_result=policy,
    )
    with pytest.raises(DdoA1DurabilityFailurePolicyError):
        reject_a1_dependent_mutation_on_unproven_durability_v1(
            dependent_mutation_requested=True,
            durability_proven=None,
            policy_result=policy,
        )


def test_durability_proven_false_rejects_dependent_mutation() -> None:
    failure = DdoDurabilityWriteError(
        FAILURE_CLASS_FILESYSTEM_CAPACITY,
        "FILESYSTEM_CAPACITY_FAILURE",
        retryable=False,
        operation=OPERATION_WRITE,
    )
    policy = bind_a1_durability_failure_policy_v1(operation=OPERATION_WRITE, failure=failure)
    assert policy.durability_proven is False
    evaluated = evaluate_a1_dependent_mutation_admission_v1(policy_result=policy)
    assert evaluated.admitted is False
    assert evaluated.durability_result == DURABILITY_FAILURE
    _must_reject_admission(policy_result=policy, durability_proven=False)


def test_missing_unclassified_durability_evidence_rejects() -> None:
    evaluated = evaluate_a1_dependent_mutation_admission_v1()
    assert evaluated.admitted is False
    assert evaluated.missing_policy_result is True
    assert evaluated.durability_result == MISSING_UNCLASSIFIED_DURABILITY_EVIDENCE
    _must_reject_admission()
    classification = classify_a1_persist_attempt_for_admission_v1()
    assert classification.durability_result == MISSING_UNCLASSIFIED_DURABILITY_EVIDENCE
    assert classification.dependent_mutation_admission == DEPENDENT_MUTATION_ADMISSION_STATE
    _must_reject_admission(persist_classification=classification)


def test_capture_ok_true_does_not_admit_dependent_mutation(tmp_path: Path) -> None:
    unbound_state, unbound = run_bridge_cycles_from_mids_v1(
        [3500.0], session_id=SESSION_ID, require_selection_binding=False
    )
    bound_state, bound = _run_bound_host(tmp_path, session_id=SESSION_ID, mids=[3500.0])
    assert [item.to_dict() for item in unbound] == [item.to_dict() for item in bound]
    assert bound_state.last_ddo_capture is not None
    capture = bound_state.last_ddo_capture
    assert capture.get("ok") is True or capture.get("decision_unchanged") is True
    assert capture["a1_capture_ok_equals_admission"] is False
    assert capture["a1_current_stage_capture_fail_open"] is True
    assert capture["a1_admission_binding_status"] == ADMISSION_BINDING_STATUS
    evaluated = evaluate_a1_dependent_mutation_admission_v1(capture_ok=True)
    assert evaluated.admitted is False
    assert evaluated.capture_ok is True
    _must_reject_admission(capture_ok=True)
    _ = unbound_state


def test_current_capture_failure_remains_decision_neutral(tmp_path: Path, monkeypatch: Any) -> None:
    def boom(_fd: int, _data: bytes) -> int:
        raise OSError(errno.ENOSPC, "simulated write failure")

    monkeypatch.setattr(os, "write", boom)
    unbound_state, unbound = run_bridge_cycles_from_mids_v1(
        [3500.0], session_id="ddo-a1-ar-capture-fail", require_selection_binding=False
    )
    bound_state, bound = _run_bound_host(
        tmp_path, session_id="ddo-a1-ar-capture-fail", mids=[3500.0]
    )
    assert [item.to_dict() for item in unbound] == [item.to_dict() for item in bound]
    assert CAPTURE_FAILURE_CHANGES_DECISION is False
    assert CURRENT_STAGE_CAPTURE_FAIL_OPEN is True
    assert PRODUCTIVE_RETURN_VALUE_UNCHANGED is True
    assert bound_state.last_ddo_capture is not None
    assert bound_state.last_ddo_capture["decision_unchanged"] is True
    assert bound_state.last_ddo_capture["capture_failure_changes_current_decision"] is False
    evidence = bound_state.last_ddo_capture.get("durability") or {}
    if evidence:
        assert evidence.get("a1_dependent_mutation_admission") == (
            DEPENDENT_MUTATION_ADMISSION_STATE
        )
        _must_reject_admission(capture_ok=True)
    _ = unbound_state


def test_identical_record_replay_is_not_duplicate_authority_relevant_mutation(
    tmp_path: Path,
) -> None:
    ledger = AppendOnlyDdoLedgerV0(tmp_path / "replay.jsonl")
    first = ledger.append(_decision())
    assert first.status == PERSIST_WRITE_ACCEPTED
    replay = ledger.append(_decision())
    assert replay.status == IDEMPOTENT_REPLAY
    assert replay.sequence == first.sequence
    assert len(ledger.read_all()) == 1
    policy = bind_a1_durability_failure_policy_v1(
        operation=OPERATION_DURABLE_APPEND,
        failure=None,
        record_id=replay.record_id,
    )
    classification = classify_a1_persist_attempt_for_admission_v1(
        append_result=replay,
        policy_result=policy,
        record_id=replay.record_id,
    )
    assert classification.persist_result == IDEMPOTENT_REPLAY
    assert classification.durability_proven is not True
    assert classification.crash_durability_fully_proven is False
    assert classification.idempotent_replay_equals_crash_durability_proof is False
    assert classification.dependent_mutation_admission == DEPENDENT_MUTATION_ADMISSION_STATE
    evaluated = evaluate_a1_dependent_mutation_admission_v1(
        policy_result=policy,
        persist_classification=classification,
        capture_ok=True,
    )
    assert evaluated.admitted is False
    assert evaluated.persist_result == IDEMPOTENT_REPLAY
    _must_reject_admission(
        policy_result=policy,
        persist_classification=classification,
        capture_ok=True,
    )


def test_duplicate_conflicting_content_remains_rejected(tmp_path: Path) -> None:
    ledger = AppendOnlyDdoLedgerV0(tmp_path / "conflict.jsonl")
    ledger.append(_decision())
    with pytest.raises(DdoDuplicateConflictError, match="DUPLICATE_RECORD_ID_CONFLICT"):
        ledger.append(_decision(decision_type="STALE_BLOCK"))
    classified = DdoDurabilityWriteError(
        "DUPLICATE_CONFLICT",
        "DUPLICATE_CONFLICT",
        retryable=False,
        operation=OPERATION_DURABLE_APPEND,
    )
    policy = bind_a1_durability_failure_policy_v1(
        operation=OPERATION_DURABLE_APPEND,
        failure=classified,
        record_id="dec-0001",
    )
    classification = classify_a1_persist_attempt_for_admission_v1(
        persist_error=DdoDuplicateConflictError("DUPLICATE_RECORD_ID_CONFLICT:dec-0001"),
        policy_result=policy,
        record_id="dec-0001",
    )
    assert classification.persist_result == DUPLICATE_CONFLICT
    assert classification.dependent_mutation_admission == DEPENDENT_MUTATION_ADMISSION_STATE
    _must_reject_admission(policy_result=policy, persist_classification=classification)
    assert "FAIL_CLOSED" in DUPLICATE_CONFLICT_SEMANTICS


def test_idempotent_replay_is_not_crash_durability_proof(tmp_path: Path) -> None:
    assert IDEMPOTENT_REPLAY_EQUALS_CRASH_DURABILITY_PROOF is False
    assert "NOT_CRASH_PROOF" in IDEMPOTENT_REPLAY_SEMANTICS
    ledger = AppendOnlyDdoLedgerV0(tmp_path / "replay-proof.jsonl")
    ledger.append(_decision())
    replay = ledger.append(_decision())
    classification = classify_a1_persist_attempt_for_admission_v1(append_result=replay)
    assert classification.persist_result == IDEMPOTENT_REPLAY
    assert classification.durability_proven is not True
    assert classification.crash_durability_fully_proven is False
    assert classification.durability_result == DURABILITY_UNKNOWN
    assert CRASH_DURABILITY_FULLY_PROVEN is False
    assert POLICY_CRASH_DURABILITY_FULLY_PROVEN is False


def test_directory_fsync_uncertainty_cannot_admit_mutation(
    tmp_path: Path, monkeypatch: Any
) -> None:
    real_fsync = os.fsync

    def boom(fd: int) -> None:
        mode = os.fstat(fd).st_mode
        if stat.S_ISDIR(mode):
            raise OSError(errno.EIO, "simulated directory fsync failure")
        return real_fsync(fd)

    monkeypatch.setattr(os, "fsync", boom)
    ledger = AppendOnlyDdoLedgerV0(tmp_path / "dirsync.jsonl")
    with pytest.raises(DdoDurabilityWriteError) as exc:
        ledger.append(_decision())
    assert exc.value.operation == OPERATION_DIRECTORY_FSYNC
    policy = bind_a1_durability_failure_policy_v1(
        operation=OPERATION_DIRECTORY_FSYNC,
        failure=exc.value,
        record_id="dec-0001",
    )
    assert policy.durability_proven is None
    classification = classify_a1_persist_attempt_for_admission_v1(
        persist_error=exc.value,
        policy_result=policy,
        record_id="dec-0001",
    )
    assert classification.durability_result == DURABILITY_UNKNOWN
    assert classification.dependent_mutation_admission == DEPENDENT_MUTATION_ADMISSION_STATE
    _must_reject_admission(policy_result=policy, persist_classification=classification)
    assert DIRECTORY_FSYNC_POLICY == "FAIL_CLOSED_ATTEMPTED_NO_PLATFORM_HARD_GUARANTEE"


def test_no_automatic_retry_loop_introduced() -> None:
    assert AUTOMATIC_RETRY_LOOP_ADDED is False
    assert POLICY_AMBIGUOUS_RETRY_ALLOWED is False
    capture_src = CAPTURE_SRC.read_text(encoding="utf-8")
    binding_src = BINDING_SRC.read_text(encoding="utf-8")
    persist_fn = capture_src[capture_src.index("def _persist(binding") :]
    persist_fn = persist_fn[: persist_fn.index("\ndef ", 1)]
    assert "while " not in persist_fn
    assert "for _ in range" not in persist_fn
    assert "retry_until" not in persist_fn
    assert "retry_allowed" not in persist_fn
    tree = ast.parse(binding_src)
    for node in ast.walk(tree):
        if isinstance(node, ast.While):
            raise AssertionError("automatic retry while-loop is forbidden")
    assert "if record_id in binding.persisted_ids" in persist_fn


def test_unknown_preserved_and_not_normalized_to_success() -> None:
    assert UNKNOWN_PRESERVED is True
    unknown = DdoDurabilityWriteError(
        FAILURE_CLASS_UNKNOWN_IO,
        "UNKNOWN_UNCLASSIFIED_IO_FAILURE",
        retryable=None,
        operation=OPERATION_WRITE,
    )
    policy = bind_a1_durability_failure_policy_v1(operation=OPERATION_WRITE, failure=unknown)
    assert policy.durability_proven is None
    classification = classify_a1_persist_attempt_for_admission_v1(
        persist_error=unknown,
        policy_result=policy,
    )
    assert classification.durability_result == DURABILITY_UNKNOWN
    assert classification.durability_proven is None
    assert classification.durability_proven is not False
    assert classification.unknown_preserved is True
    evaluated = evaluate_a1_dependent_mutation_admission_v1(policy_result=policy)
    assert evaluated.admitted is False
    _must_reject_admission(policy_result=policy)


def test_no_new_storage_or_admission_authority() -> None:
    assert NEW_STORAGE_AUTHORITY_CREATED is False
    assert NEW_ADMISSION_AUTHORITY_CREATED is False
    assert ADMISSION_OWNER is reject_a1_dependent_mutation_on_unproven_durability_v1
    policy_src = POLICY_SRC.read_text(encoding="utf-8")
    binding_src = BINDING_SRC.read_text(encoding="utf-8")
    assert "def reject_a1_dependent_mutation_on_unproven_durability_v1" in policy_src
    assert binding_src.count("def reject_a1_dependent_mutation_on_unproven_durability_v1") == 0
    assert "os.rename" not in LEDGER_SRC.read_text(encoding="utf-8")
    assert "os.replace" not in LEDGER_SRC.read_text(encoding="utf-8")


def test_runtime_trading_live_authority_unchanged() -> None:
    assert RUNTIME_AUTHORIZATION_ELIGIBLE is False
    assert RUNTIME_AUTHORIZED is False
    assert UNATTENDED_OPERATION_STARTED is False
    assert TRADING_AUTHORITY_CHANGED is False
    assert AUTHORITY_OWNER == "NONE"
    assert LEARNING_PRODUCTIVE_AUTHORITY == "NONE"
    assert SECOND_TRADING_AUTHORITY_CREATED is False
    assert SECOND_EXECUTION_AUTHORITY_CREATED is False
    assert LIVE_EFFECT == "NONE"
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert WIRE_SEND_PERMITTED is False
    assert LIVE_AUTHORIZED is False
    assert TESTNET_AUTHORIZED is False
    assert PAPER_EXECUTION_AUTHORIZED is False
    assert ORDERS_AUTHORIZED is False
    assert TRADING_DECISION_DEPENDS_ON_LEDGER_WRITE is False
    assert MASTER_V2_DOUBLE_PLAY_SOLE_TRADING_AUTHORITY is True
    assert PRODUCTIVE_RETURN_VALUE_UNCHANGED is True
    assert DEPENDENT_MUTATION_ON_UNPROVEN_DURABILITY == "FORBIDDEN"
    assert FILE_FSYNC_POLICY == "PRESENT_FAILURE_FORBIDS_DEPENDENT_MUTATION"
    stamps = a1_durability_to_admission_and_replay_observability_v1()
    assert stamps["a1_admission_runtime_authorized"] is False
    assert stamps["a1_admission_unattended_operation_started"] is False
    assert stamps["a1_admission_new_storage_authority_created"] is False
    assert stamps["a1_new_admission_authority_created"] is False
    assert stamps["a1_automatic_retry_loop_added"] is False
    assert stamps["a1_capture_ok_equals_admission"] is False
    assert stamps["a1_current_stage_capture_fail_open"] is True
    assert stamps["a1_admission_host_crash_durability"] == "UNPROVEN"
    assert stamps["a1_admission_power_loss_durability"] == "UNPROVEN"


def test_duplicate_ledger_rows_fail_closed_on_load(tmp_path: Path) -> None:
    path = tmp_path / "dup-load.jsonl"
    ledger = AppendOnlyDdoLedgerV0(path)
    ledger.append(_decision())
    text = path.read_text(encoding="utf-8")
    path.write_text(text + text, encoding="utf-8")
    with pytest.raises(DdoLedgerCorruptionError):
        ledger.read_all()
    assert "DUPLICATE_RECORD_ID_IN_LEDGER" in LEDGER_SRC.read_text(encoding="utf-8")


def test_persist_write_accepted_is_existing_appended_status(tmp_path: Path) -> None:
    ledger = AppendOnlyDdoLedgerV0(tmp_path / "accepted.jsonl")
    result = ledger.append(_decision())
    assert result.status == "APPENDED"
    assert PERSIST_WRITE_ACCEPTED == "APPENDED"
    classification = classify_a1_persist_attempt_for_admission_v1(append_result=result)
    assert classification.persist_result == PERSIST_WRITE_ACCEPTED
    assert classification.durability_result == DURABILITY_UNKNOWN
    assert classification.dependent_mutation_admission == DEPENDENT_MUTATION_ADMISSION_STATE
    _must_reject_admission(persist_classification=classification, capture_ok=True)


def test_host_observability_does_not_change_productive_return(tmp_path: Path) -> None:
    unbound_state, unbound = run_bridge_cycles_from_mids_v1(
        [3500.0], session_id="ddo-a1-ar-host", require_selection_binding=False
    )
    bound_state, bound = _run_bound_host(tmp_path, session_id="ddo-a1-ar-host", mids=[3500.0])
    assert [item.to_dict() for item in unbound] == [item.to_dict() for item in bound]
    assert bound_state.last_ddo_capture is not None
    capture = bound_state.last_ddo_capture
    assert capture["a1_admission_binding_status"] == "BOUND_FAIL_CLOSED"
    assert capture["a1_replay_ambiguity_binding_status"] == "BOUND_WITHOUT_AUTOMATIC_RETRY"
    assert capture["a1_durability_failure_policy"] == A1_DURABILITY_FAILURE_POLICY
    evidence = capture.get("durability") or {}
    if evidence.get("success") is True:
        assert evidence.get("a1_persist_result") in {PERSIST_WRITE_ACCEPTED, IDEMPOTENT_REPLAY}
        assert evidence.get("a1_dependent_mutation_admission") == (
            DEPENDENT_MUTATION_ADMISSION_STATE
        )
        assert evidence.get("a1_failure_policy_durability_proven") is not True
    _ = unbound_state
