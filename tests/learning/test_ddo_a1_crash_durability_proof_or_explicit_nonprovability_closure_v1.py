"""DDO A1 crash-durability proof or explicit non-provability closure v1.

Observation-only. No trading authority. No runtime activation.
Does not manufacture durability_proven=True. Host-crash remains UNPROVEN.
"""

from __future__ import annotations

import errno
from pathlib import Path
from typing import Any

import pytest

from src.governance.live_mode_gate import ExecutionEnvironment
from src.learning.deterministic_decision_outcome_v0.a1_crash_durability_proof_or_explicit_nonprovability_closure_v1 import (
    ATOMIC_REPLACE_PRESENT,
    CORRUPTION_FAIL_CLOSED,
    CRASH_DURABILITY_FULLY_PROVEN,
    CURRENT_ADMISSION_OWNER,
    CURRENT_STORAGE_OWNER,
    CURRENT_STORAGE_OWNER_COUNT,
    CURRENT_STORAGE_WRITE_SEQUENCE,
    DIRECTORY_FSYNC_FAILURE_PROPAGATES,
    DIRECTORY_FSYNC_FAILURE_SEMANTICS,
    DURABILITY_BOUND_ASSUMPTIONS,
    DURABILITY_CLOSURE,
    DURABILITY_PROVEN_TRUE_MANUFACTURABLE,
    DdoA1CrashDurabilityProofOrExplicitNonprovabilityClosureV1,
    DdoA1CrashDurabilityProofOrNonprovabilityClosureError,
    FAILURE_CLASS_F0_NORMAL_COMPLETION,
    FAILURE_CLASS_F1_PROCESS_CRASH_BEFORE_WRITE,
    FAILURE_CLASS_F4_PROCESS_CRASH_AFTER_FILE_FSYNC_BEFORE_RENAME,
    FAILURE_CLASS_F8_HOST_KERNEL_CRASH,
    FAILURE_CLASS_F9_POWER_LOSS,
    FAILURE_CLASS_F10_RESTART_WITH_TEMP_FILE,
    FAILURE_CLASS_F12_RESTART_WITH_SAME_ID_SAME_CONTENT,
    FAILURE_CLASS_F13_RESTART_WITH_SAME_ID_DIFFERENT_CONTENT,
    FAILURE_CLASS_F17_DIRECTORY_FSYNC_UNSUPPORTED_OR_FAILURE,
    FILE_FSYNC_FAILURE_SEMANTICS,
    HOST_CRASH_DURABILITY,
    HOST_KERNEL_CRASH_DURABILITY,
    IMPLEMENTATION_COMPLETE,
    IMPLEMENTATION_GO_IS_RUNTIME_AUTHORIZATION,
    NEW_ADMISSION_AUTHORITY_CREATED,
    NEW_STORAGE_AUTHORITY_CREATED,
    NEXT_OWNER_GO_REQUIRED,
    POWER_LOSS_DURABILITY,
    PROCESS_CRASH_DURABILITY,
    PROCESS_RESTART_DURABILITY,
    PRODUCTIVE_RETURN_VALUE_UNCHANGED,
    RUNTIME_AUTHORIZATION_ELIGIBLE,
    RUNTIME_AUTHORIZED,
    RUNTIME_OPERATIONAL_AUTHORIZATION_SOURCE,
    SEPARATE_STORAGE_DURABILITY_ARCHITECTURE_REQUIRED,
    SLICE_ID,
    TEMP_ARTIFACT_HANDLING,
    TRADING_AUTHORITY_CHANGED,
    UNATTENDED_OPERATION_STARTED,
    UNPROVEN_DURABILITY_SURFACES,
    a1_crash_durability_failure_model_by_id_v1,
    a1_crash_durability_failure_model_v1,
    a1_crash_durability_proof_or_nonprovability_observability_v1,
    canonical_a1_crash_durability_proof_or_explicit_nonprovability_closure_v1,
    reject_a1_crash_durability_full_proof_overclaim_v1,
)
from src.learning.deterministic_decision_outcome_v0.a1_durability_failure_policy_binding_v1 import (
    bind_a1_durability_failure_policy_v1,
    reject_a1_dependent_mutation_on_unproven_durability_v1,
)
from src.learning.deterministic_decision_outcome_v0.a1_durability_to_admission_and_replay_binding_v1 import (
    ADMISSION_OWNER_NAME,
    CAPTURE_OK_EQUALS_ADMISSION,
    classify_a1_persist_attempt_for_admission_v1,
    evaluate_a1_dependent_mutation_admission_v1,
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
    DdoDuplicateConflictError,
    DdoDurabilityWriteError,
    DdoLedgerCorruptionError,
    DdoMalformedRecordError,
    FAILURE_CLASS_UNKNOWN_IO,
    OPERATION_DIRECTORY_FSYNC,
    OPERATION_FILE_FSYNC,
    OPERATION_WRITE,
)
from src.learning.deterministic_decision_outcome_v0.ledger_v0 import (
    BOUNDARY_AFTER_CLOSE_BEFORE_DIRECTORY_FSYNC,
    BOUNDARY_AFTER_DIRECTORY_FSYNC_BEFORE_RETURN,
    BOUNDARY_AFTER_WRITE_BEFORE_FILE_FSYNC,
    BOUNDARY_BEFORE_WRITE,
    BOUNDARY_DIRECTORY_FSYNC,
    BOUNDARY_DURING_WRITE,
    BOUNDARY_FILE_FSYNC,
    DdoLedgerFaultInjectorV1,
    FAULT_ACTION_PARTIAL_WRITE_THEN_RAISE,
    FAULT_ACTION_RAISE,
    FAULT_ACTION_SHORT_WRITE,
    AppendOnlyDdoLedgerV0,
    ddo_ledger_fault_injection_v1,
)
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
CLOSURE_SRC = (
    REPO_ROOT
    / "src/learning/deterministic_decision_outcome_v0"
    / "a1_crash_durability_proof_or_explicit_nonprovability_closure_v1.py"
)
ACCOUNT_TEST_IDENTITY = "acct-uid-test-a1-crash-proof"
ACCOUNT_TEST_CREDENTIAL_REF = "cred-ref-test-a1-crash-proof"
SESSION_ID = "ddo-a1-crash-proof"


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
    result = evaluate_a1_dependent_mutation_admission_v1(**kwargs)
    assert result.admitted is False
    with pytest.raises(Exception, match="A1_DEPENDENT_MUTATION_FORBIDDEN"):
        reject_a1_dependent_mutation_on_unproven_durability_v1(
            dependent_mutation_requested=True,
            durability_proven=kwargs.get("durability_proven"),
            policy_result=kwargs.get("policy_result"),
        )


def test_closure_binds_nonprovability_without_manufacturing_success() -> None:
    closure = canonical_a1_crash_durability_proof_or_explicit_nonprovability_closure_v1()
    assert isinstance(closure, DdoA1CrashDurabilityProofOrExplicitNonprovabilityClosureV1)
    assert closure.slice_id == SLICE_ID
    assert DURABILITY_CLOSURE == (
        "CURRENT_STORAGE_CONTRACT_EXHAUSTED_HOST_CRASH_DURABILITY_UNPROVEN"
    )
    assert PROCESS_RESTART_DURABILITY == "PROVEN_WITH_BOUND_ASSUMPTIONS"
    assert PROCESS_CRASH_DURABILITY == "PARTIAL"
    assert HOST_KERNEL_CRASH_DURABILITY == "UNPROVEN"
    assert HOST_CRASH_DURABILITY == "UNPROVEN"
    assert POWER_LOSS_DURABILITY == "UNPROVEN"
    assert CRASH_DURABILITY_FULLY_PROVEN is False
    assert DURABILITY_PROVEN_TRUE_MANUFACTURABLE is False
    assert IMPLEMENTATION_COMPLETE is True
    assert RUNTIME_AUTHORIZED is False
    assert RUNTIME_AUTHORIZATION_ELIGIBLE is False
    assert UNATTENDED_OPERATION_STARTED is False
    assert IMPLEMENTATION_GO_IS_RUNTIME_AUTHORIZATION is False
    assert RUNTIME_OPERATIONAL_AUTHORIZATION_SOURCE == "NONE"
    assert NEW_STORAGE_AUTHORITY_CREATED is False
    assert NEW_ADMISSION_AUTHORITY_CREATED is False
    assert CURRENT_STORAGE_OWNER == "DDO_DURABLE_EVIDENCE_STORAGE_OWNER"
    assert CURRENT_STORAGE_OWNER_COUNT == 1
    assert CURRENT_ADMISSION_OWNER == ADMISSION_OWNER_NAME
    assert SEPARATE_STORAGE_DURABILITY_ARCHITECTURE_REQUIRED is True
    assert NEXT_OWNER_GO_REQUIRED is True
    assert "HOST_KERNEL_CRASH" in UNPROVEN_DURABILITY_SURFACES
    assert "POWER_LOSS" in UNPROVEN_DURABILITY_SURFACES
    assert "PROCESS_RESTART_AFTER_SUCCESSFUL_APPEND_RETURN" in DURABILITY_BOUND_ASSUMPTIONS


def test_storage_census_matches_ledger_source() -> None:
    ledger = LEDGER_SRC.read_text(encoding="utf-8")
    assert "os.O_APPEND" in ledger
    assert "os.fsync(fd)" in ledger
    assert "os.fsync(dir_fd)" in ledger
    assert "os.replace" not in ledger
    assert "os.rename" not in ledger
    assert ".tmp" not in ledger
    assert "tempfile" not in ledger
    assert ATOMIC_REPLACE_PRESENT is False
    assert FILE_FSYNC_FAILURE_SEMANTICS == "PRESENT_FAILURE_FORBIDS_DEPENDENT_MUTATION"
    assert DIRECTORY_FSYNC_FAILURE_SEMANTICS == ("FAIL_CLOSED_ATTEMPTED_NO_PLATFORM_HARD_GUARANTEE")
    assert DIRECTORY_FSYNC_FAILURE_PROPAGATES is True
    assert TEMP_ARTIFACT_HANDLING == "NO_TEMP_FILE_NOT_A_COMMITTED_RECORD"
    assert "OPEN_O_APPEND" in CURRENT_STORAGE_WRITE_SEQUENCE
    assert "FILE_FSYNC" in CURRENT_STORAGE_WRITE_SEQUENCE
    assert "DIRECTORY_FSYNC" in CURRENT_STORAGE_WRITE_SEQUENCE
    assert "CAPTURE_CLASSIFY_ADMISSION_SEPARATE_OWNER" in CURRENT_STORAGE_WRITE_SEQUENCE
    dir_fsync_block = ledger[ledger.rindex("os.fsync(dir_fd)") :]
    assert "classify_oserror_v0(exc, operation=OPERATION_DIRECTORY_FSYNC)" in dir_fsync_block
    assert "except OSError:\n            pass" not in dir_fsync_block


def test_failure_model_covers_f0_to_f18_and_never_admits() -> None:
    rows = a1_crash_durability_failure_model_v1()
    by_id = a1_crash_durability_failure_model_by_id_v1()
    assert len(rows) == 19
    assert len(by_id) == 19
    for row in rows:
        assert row.dependent_mutation_eligibility == "FORBIDDEN"
        assert row.admission_behavior != "ADMITTED"
        assert "CRASH_SAFE" not in row.proof_source
    assert by_id[FAILURE_CLASS_F0_NORMAL_COMPLETION].known_vs_unknown.startswith("KNOWN")
    assert by_id[FAILURE_CLASS_F1_PROCESS_CRASH_BEFORE_WRITE].expected_durable_artifacts == (
        "NO_NEW_LEDGER_LINE"
    )
    assert by_id[
        FAILURE_CLASS_F4_PROCESS_CRASH_AFTER_FILE_FSYNC_BEFORE_RENAME
    ].known_vs_unknown == ("NOT_APPLICABLE_NO_RENAME")
    assert by_id[FAILURE_CLASS_F8_HOST_KERNEL_CRASH].known_vs_unknown == "UNKNOWN"
    assert by_id[FAILURE_CLASS_F9_POWER_LOSS].known_vs_unknown == "UNKNOWN"
    assert by_id[FAILURE_CLASS_F10_RESTART_WITH_TEMP_FILE].known_vs_unknown.startswith(
        "NOT_APPLICABLE"
    )
    assert (
        "NOT_CRASH_PROOF"
        in by_id[FAILURE_CLASS_F12_RESTART_WITH_SAME_ID_SAME_CONTENT].known_vs_unknown
    )
    assert by_id[FAILURE_CLASS_F13_RESTART_WITH_SAME_ID_DIFFERENT_CONTENT].replay_behavior == (
        "FAIL_CLOSED_DUPLICATE_CONFLICT"
    )
    assert by_id[FAILURE_CLASS_F17_DIRECTORY_FSYNC_UNSUPPORTED_OR_FAILURE].known_vs_unknown == (
        "UNKNOWN"
    )


def test_crash_before_write_leaves_no_durable_record(tmp_path: Path) -> None:
    path = tmp_path / "before-write.jsonl"
    injector = DdoLedgerFaultInjectorV1(
        boundary=BOUNDARY_BEFORE_WRITE,
        action=FAULT_ACTION_RAISE,
        errno_code=errno.EIO,
    )
    ledger = AppendOnlyDdoLedgerV0(path)
    with ddo_ledger_fault_injection_v1(injector):
        with pytest.raises(DdoDurabilityWriteError) as exc:
            ledger.append(_decision())
    assert exc.value.operation == OPERATION_WRITE
    assert not path.exists() or path.read_text(encoding="utf-8") == ""
    recovered = AppendOnlyDdoLedgerV0(path)
    assert recovered.read_all() == ()
    policy = bind_a1_durability_failure_policy_v1(
        operation=OPERATION_WRITE, failure=exc.value, record_id="dec-0001"
    )
    classification = classify_a1_persist_attempt_for_admission_v1(
        persist_error=exc.value, policy_result=policy, record_id="dec-0001"
    )
    _must_reject_admission(policy_result=policy, persist_classification=classification)


def test_write_succeeds_but_file_fsync_fails_forbids_dependent_mutation(tmp_path: Path) -> None:
    path = tmp_path / "file-fsync.jsonl"
    injector = DdoLedgerFaultInjectorV1(
        boundary=BOUNDARY_FILE_FSYNC,
        action=FAULT_ACTION_RAISE,
        errno_code=errno.EIO,
    )
    ledger = AppendOnlyDdoLedgerV0(path)
    with ddo_ledger_fault_injection_v1(injector):
        with pytest.raises(DdoDurabilityWriteError) as exc:
            ledger.append(_decision())
    assert exc.value.operation == OPERATION_FILE_FSYNC
    policy = bind_a1_durability_failure_policy_v1(
        operation=OPERATION_FILE_FSYNC, failure=exc.value, record_id="dec-0001"
    )
    assert policy.dependent_mutation_allowed is False
    assert policy.durability_proven is not True
    classification = classify_a1_persist_attempt_for_admission_v1(
        persist_error=exc.value, policy_result=policy, record_id="dec-0001"
    )
    _must_reject_admission(policy_result=policy, persist_classification=classification)
    assert HOST_CRASH_DURABILITY == "UNPROVEN"


def test_no_replace_step_so_replace_failure_cannot_be_false_success() -> None:
    ledger = LEDGER_SRC.read_text(encoding="utf-8")
    assert ATOMIC_REPLACE_PRESENT is False
    assert "os.replace" not in ledger
    assert "os.rename" not in ledger
    row = a1_crash_durability_failure_model_by_id_v1()[
        FAILURE_CLASS_F4_PROCESS_CRASH_AFTER_FILE_FSYNC_BEFORE_RENAME
    ]
    assert row.rename_step_applicable is False
    assert row.known_vs_unknown == "NOT_APPLICABLE_NO_RENAME"


def test_directory_fsync_failure_is_not_host_crash_durability(tmp_path: Path) -> None:
    path = tmp_path / "dir-fsync.jsonl"
    injector = DdoLedgerFaultInjectorV1(
        boundary=BOUNDARY_DIRECTORY_FSYNC,
        action=FAULT_ACTION_RAISE,
        errno_code=errno.EIO,
    )
    ledger = AppendOnlyDdoLedgerV0(path)
    with ddo_ledger_fault_injection_v1(injector):
        with pytest.raises(DdoDurabilityWriteError) as exc:
            ledger.append(_decision())
    assert exc.value.operation == OPERATION_DIRECTORY_FSYNC
    policy = bind_a1_durability_failure_policy_v1(
        operation=OPERATION_DIRECTORY_FSYNC, failure=exc.value, record_id="dec-0001"
    )
    assert policy.durability_proven is None
    classification = classify_a1_persist_attempt_for_admission_v1(
        persist_error=exc.value, policy_result=policy, record_id="dec-0001"
    )
    assert classification.durability_result == "DURABILITY_UNKNOWN"
    _must_reject_admission(policy_result=policy, persist_classification=classification)
    assert HOST_CRASH_DURABILITY == "UNPROVEN"
    assert DIRECTORY_FSYNC_FAILURE_SEMANTICS == ("FAIL_CLOSED_ATTEMPTED_NO_PLATFORM_HARD_GUARANTEE")


def test_same_id_same_content_after_restart_is_idempotent_not_crash_proof(
    tmp_path: Path,
) -> None:
    path = tmp_path / "restart-same.jsonl"
    first = AppendOnlyDdoLedgerV0(path).append(_decision())
    assert first.status == "APPENDED"
    reopened = AppendOnlyDdoLedgerV0(path)
    replay = reopened.append(_decision())
    assert replay.status == "IDEMPOTENT_REPLAY"
    assert replay.sequence == first.sequence
    assert len(reopened.read_all()) == 1
    classification = classify_a1_persist_attempt_for_admission_v1(append_result=replay)
    assert classification.persist_result == "IDEMPOTENT_REPLAY"
    assert classification.durability_proven is not True
    assert classification.crash_durability_fully_proven is False
    _must_reject_admission(persist_classification=classification)
    assert PROCESS_RESTART_DURABILITY == "PROVEN_WITH_BOUND_ASSUMPTIONS"


def test_same_id_different_content_fail_closed(tmp_path: Path) -> None:
    path = tmp_path / "conflict.jsonl"
    AppendOnlyDdoLedgerV0(path).append(_decision())
    recovered = AppendOnlyDdoLedgerV0(path)
    with pytest.raises(DdoDuplicateConflictError, match="DUPLICATE_RECORD_ID_CONFLICT"):
        recovered.append(_decision(decision_type="STALE_BLOCK"))
    assert len(recovered.read_all()) == 1
    _must_reject_admission(durability_proven=False)


def test_corrupt_or_truncated_record_is_unknown_failure_not_empty_success(
    tmp_path: Path,
) -> None:
    path = tmp_path / "corrupt.jsonl"
    AppendOnlyDdoLedgerV0(path).append(_decision())
    path.write_text(path.read_text(encoding="utf-8")[:-1], encoding="utf-8")
    recovered = AppendOnlyDdoLedgerV0(path)
    with pytest.raises(DdoLedgerCorruptionError, match="LEDGER_MISSING_TRAILING_NEWLINE"):
        recovered.read_all()
    truncated = tmp_path / "partial.jsonl"
    injector = DdoLedgerFaultInjectorV1(
        boundary=BOUNDARY_DURING_WRITE,
        action=FAULT_ACTION_PARTIAL_WRITE_THEN_RAISE,
        errno_code=errno.EIO,
    )
    with ddo_ledger_fault_injection_v1(injector):
        with pytest.raises(DdoDurabilityWriteError):
            AppendOnlyDdoLedgerV0(truncated).append(_decision())
    with pytest.raises((DdoLedgerCorruptionError, DdoMalformedRecordError)):
        AppendOnlyDdoLedgerV0(truncated).read_all()
    _must_reject_admission(durability_proven=None)
    assert CORRUPTION_FAIL_CLOSED is True


def test_durable_artifact_with_failed_return_does_not_duplicate(tmp_path: Path) -> None:
    path = tmp_path / "return-fail.jsonl"
    injector = DdoLedgerFaultInjectorV1(
        boundary=BOUNDARY_AFTER_DIRECTORY_FSYNC_BEFORE_RETURN,
        action=FAULT_ACTION_RAISE,
        errno_code=errno.EIO,
    )
    with ddo_ledger_fault_injection_v1(injector):
        with pytest.raises(DdoDurabilityWriteError) as exc:
            AppendOnlyDdoLedgerV0(path).append(_decision())
    assert exc.value.operation == OPERATION_DIRECTORY_FSYNC
    recovered = AppendOnlyDdoLedgerV0(path)
    loaded = recovered.read_all()
    assert len(loaded) == 1
    replay = recovered.append(_decision())
    assert replay.status == "IDEMPOTENT_REPLAY"
    assert len(recovered.read_all()) == 1
    classification = classify_a1_persist_attempt_for_admission_v1(append_result=replay)
    _must_reject_admission(persist_classification=classification)


def test_restart_cannot_prove_latest_action_when_truncated(tmp_path: Path) -> None:
    path = tmp_path / "unprovable-latest.jsonl"
    AppendOnlyDdoLedgerV0(path).append(_decision())
    path.write_bytes(path.read_bytes() + b'{"truncated":true')
    with pytest.raises(DdoLedgerCorruptionError):
        AppendOnlyDdoLedgerV0(path).read_all()
    _must_reject_admission(durability_proven=None)


def test_fsync_exception_preserves_observation_and_forbids_mutation(
    tmp_path: Path,
) -> None:
    path = tmp_path / "fsync-obs.jsonl"
    injector = DdoLedgerFaultInjectorV1(
        boundary=BOUNDARY_FILE_FSYNC,
        action=FAULT_ACTION_RAISE,
        errno_code=errno.EIO,
    )
    with ddo_ledger_fault_injection_v1(injector):
        with pytest.raises(DdoDurabilityWriteError) as exc:
            AppendOnlyDdoLedgerV0(path).append(_decision())
    assert exc.value.failure_class == FAILURE_CLASS_UNKNOWN_IO
    policy = bind_a1_durability_failure_policy_v1(operation=OPERATION_FILE_FSYNC, failure=exc.value)
    assert policy.unknown_preserved is True
    assert policy.dependent_mutation_allowed is False
    assert policy.current_stage_capture_fail_open is True


def test_short_write_and_after_write_before_fsync_are_not_success(tmp_path: Path) -> None:
    short_path = tmp_path / "short.jsonl"
    short_injector = DdoLedgerFaultInjectorV1(
        boundary=BOUNDARY_DURING_WRITE,
        action=FAULT_ACTION_SHORT_WRITE,
    )
    with ddo_ledger_fault_injection_v1(short_injector):
        with pytest.raises(DdoDurabilityWriteError) as short_exc:
            AppendOnlyDdoLedgerV0(short_path).append(_decision())
    assert short_exc.value.operation == OPERATION_WRITE
    assert short_exc.value.retryable is None
    after_path = tmp_path / "after-write.jsonl"
    after_injector = DdoLedgerFaultInjectorV1(
        boundary=BOUNDARY_AFTER_WRITE_BEFORE_FILE_FSYNC,
        action=FAULT_ACTION_RAISE,
        errno_code=errno.EIO,
    )
    with ddo_ledger_fault_injection_v1(after_injector):
        with pytest.raises(DdoDurabilityWriteError) as after_exc:
            AppendOnlyDdoLedgerV0(after_path).append(_decision())
    assert after_exc.value.operation == OPERATION_WRITE
    _must_reject_admission(durability_proven=None)


def test_after_close_before_directory_fsync_does_not_prove_host_crash(
    tmp_path: Path,
) -> None:
    path = tmp_path / "after-close.jsonl"
    injector = DdoLedgerFaultInjectorV1(
        boundary=BOUNDARY_AFTER_CLOSE_BEFORE_DIRECTORY_FSYNC,
        action=FAULT_ACTION_RAISE,
        errno_code=errno.EIO,
    )
    with ddo_ledger_fault_injection_v1(injector):
        with pytest.raises(DdoDurabilityWriteError):
            AppendOnlyDdoLedgerV0(path).append(_decision())
    assert HOST_CRASH_DURABILITY == "UNPROVEN"
    _must_reject_admission(durability_proven=None)


def test_temp_file_is_not_treated_as_committed_record(tmp_path: Path) -> None:
    path = tmp_path / "no-temp.jsonl"
    AppendOnlyDdoLedgerV0(path).append(_decision())
    leftovers = list(path.parent.glob("*.tmp")) + list(path.parent.glob("*~"))
    assert leftovers == []
    assert path.name == "no-temp.jsonl"


def test_hash_mismatch_and_malformed_json_fail_closed(tmp_path: Path) -> None:
    path = tmp_path / "hash.jsonl"
    AppendOnlyDdoLedgerV0(path).append(_decision())
    text = path.read_text(encoding="utf-8")
    path.write_text(text.replace("NO_ENTRY", "HOLD", 1), encoding="utf-8")
    with pytest.raises((DdoLedgerCorruptionError, Exception)):
        AppendOnlyDdoLedgerV0(path).read_all()
    malformed = tmp_path / "malformed.jsonl"
    malformed.write_text("{not-json\n", encoding="utf-8")
    with pytest.raises(DdoMalformedRecordError):
        AppendOnlyDdoLedgerV0(malformed).read_all()


def test_read_recovery_does_not_invent_missing_evidence(tmp_path: Path) -> None:
    path = tmp_path / "missing.jsonl"
    ledger = AppendOnlyDdoLedgerV0(path)
    assert ledger.read_all() == ()
    with pytest.raises(Exception, match="RECORD_NOT_FOUND"):
        ledger.get("dec-0001")
    _must_reject_admission(durability_proven=None)


def test_capture_ok_is_not_admission_and_unknown_is_not_success(tmp_path: Path) -> None:
    assert CAPTURE_OK_EQUALS_ADMISSION is False
    result = evaluate_a1_dependent_mutation_admission_v1(capture_ok=True, durability_proven=None)
    assert result.admitted is False
    assert result.capture_ok is True
    assert result.durability_proven is not True
    _must_reject_admission(capture_ok=True, durability_proven=None)
    _unbound_state, unbound = run_bridge_cycles_from_mids_v1(
        [3500.0], session_id="ddo-a1-crash-proof-unbound", require_selection_binding=False
    )
    bound_state, bound = _run_bound_host(tmp_path, session_id="ddo-a1-crash-proof-host")
    assert [item.to_dict() for item in unbound] == [item.to_dict() for item in bound]
    assert PRODUCTIVE_RETURN_VALUE_UNCHANGED is True
    assert CAPTURE_FAILURE_CHANGES_DECISION is False
    assert bound_state.last_ddo_capture is not None
    assert bound_state.last_ddo_capture["decision_unchanged"] is True
    assert bound_state.last_ddo_capture["capture_failure_changes_current_decision"] is False


def test_overclaim_and_second_owners_are_forbidden() -> None:
    with pytest.raises(DdoA1CrashDurabilityProofOrNonprovabilityClosureError):
        reject_a1_crash_durability_full_proof_overclaim_v1(crash_durability_fully_proven=True)
    with pytest.raises(DdoA1CrashDurabilityProofOrNonprovabilityClosureError):
        DdoA1CrashDurabilityProofOrExplicitNonprovabilityClosureV1(host_crash_durability="PROVEN")
    with pytest.raises(DdoA1CrashDurabilityProofOrNonprovabilityClosureError):
        DdoA1CrashDurabilityProofOrExplicitNonprovabilityClosureV1(
            durability_proven_true_manufacturable=True
        )
    with pytest.raises(DdoA1CrashDurabilityProofOrNonprovabilityClosureError):
        DdoA1CrashDurabilityProofOrExplicitNonprovabilityClosureV1(runtime_authorized=True)
    with pytest.raises(DdoA1CrashDurabilityProofOrNonprovabilityClosureError):
        DdoA1CrashDurabilityProofOrExplicitNonprovabilityClosureV1(
            new_storage_authority_created=True
        )
    assert AUTHORITY_OWNER == "NONE"
    assert LEARNING_PRODUCTIVE_AUTHORITY == "NONE"
    assert SECOND_TRADING_AUTHORITY_CREATED is False
    assert SECOND_EXECUTION_AUTHORITY_CREATED is False
    assert TRADING_AUTHORITY_CHANGED is False
    assert LIVE_EFFECT == "NONE"
    assert LIVE_AUTHORIZED is False
    assert TESTNET_AUTHORIZED is False
    assert ORDERS_AUTHORIZED is False
    assert PAPER_EXECUTION_AUTHORIZED is False
    assert LIVE_ARMED is False
    assert LIVE_ENABLED is False
    assert WIRE_SEND_PERMITTED is False
    stamps = a1_crash_durability_proof_or_nonprovability_observability_v1()
    assert stamps["a1_crash_proof_host_crash_durability"] == "UNPROVEN"
    assert stamps["a1_crash_proof_durability_closure"] == DURABILITY_CLOSURE
    assert stamps["a1_crash_proof_separate_storage_architecture_required"] is True
    assert "DURABILITY_PROVEN_TRUE_MANUFACTURABLE: Final[bool] = False" in CLOSURE_SRC.read_text(
        encoding="utf-8"
    )


def test_fault_injection_is_test_only_default_noop() -> None:
    src = LEDGER_SRC.read_text(encoding="utf-8")
    assert "ddo_ledger_fault_injection_v1" in src
    assert "_LEDGER_FAULT_INJECTOR: ContextVar" in src
    assert "default=None" in src
    productive_host = (
        REPO_ROOT
        / "src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1"
        / "ddo_observation_host_scope_binding_v1.py"
    ).read_text(encoding="utf-8")
    capture = (
        REPO_ROOT / "src/learning/deterministic_decision_outcome_v0/capture_v0.py"
    ).read_text(encoding="utf-8")
    assert "ddo_ledger_fault_injection_v1" not in productive_host
    assert "ddo_ledger_fault_injection_v1" not in capture
    assert "DdoLedgerFaultInjectorV1" not in capture
