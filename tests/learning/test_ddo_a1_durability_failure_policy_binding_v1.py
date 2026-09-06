"""DDO A1 durability failure policy binding v1.

Observation-only. No trading authority. No runtime activation.
Binds the existing durability failure classes without a new storage owner.
"""

from __future__ import annotations

import errno
import logging
import os
import stat
from pathlib import Path
from typing import Any

import pytest

from src.governance.live_mode_gate import ExecutionEnvironment
from src.learning.deterministic_decision_outcome_v0.a1_durability_failure_policy_binding_v1 import (
    A1_DURABILITY_FAILURE_POLICY,
    AMBIGUOUS_RETRY_ALLOWED,
    CRASH_DURABILITY_FULLY_PROVEN,
    CURRENT_STAGE_DURABILITY_FAILURE_POLICY,
    DEPENDENT_MUTATION_ON_UNPROVEN_DURABILITY,
    DIRECTORY_FSYNC_STATUS,
    FAILURE_CLASSES_BOUND,
    FILE_FSYNC_STATUS,
    HOST_CRASH_DURABILITY,
    IMPLEMENTATION_COMPLETE,
    IMPLEMENTATION_GO_IS_RUNTIME_AUTHORIZATION,
    NEW_STORAGE_AUTHORITY_CREATED,
    NEXT_DDO_STEP,
    NEXT_OWNER_GO_REQUIRED,
    OPERATION_DIRECTORY_FSYNC,
    OPERATION_DURABLE_APPEND,
    OPERATION_FILE_FSYNC,
    OPERATION_SERIALIZE_VALIDATE,
    OPERATION_WRITE,
    POWER_LOSS_DURABILITY,
    PRIMARY_LEDGER_FAILURE_MASKED_BY_LOGGING,
    PRODUCTIVE_RETURN_VALUE_UNCHANGED,
    RUNTIME_AUTHORIZATION_ELIGIBLE,
    RUNTIME_AUTHORIZED,
    RUNTIME_OPERATIONAL_AUTHORIZATION_SOURCE,
    SLICE_ID,
    TRADING_DECISION_DEPENDS_ON_LEDGER_WRITE,
    UNATTENDED_OPERATION_STARTED,
    UNKNOWN_PRESERVED,
    DdoA1DurabilityFailurePolicyBindingV1,
    DdoA1DurabilityFailurePolicyError,
    a1_durability_failure_policy_observability_v1,
    a1_failure_class_policy_v1,
    bind_a1_durability_failure_policy_v1,
    canonical_a1_durability_failure_policy_binding_v1,
    reject_a1_dependent_mutation_on_unproven_durability_v1,
    reject_a1_runtime_authorization_attempt_v1,
)
from src.learning.deterministic_decision_outcome_v0.a1_unattended_durability_policy_boundary_v1 import (
    A1_DURABILITY_FAILURE_POLICY as BOUNDARY_A1_DURABILITY_FAILURE_POLICY,
    A1_UNATTENDED_DURABILITY_RUNTIME_AUTHORIZED,
    CURRENT_STAGE_DURABILITY_FAILURE_POLICY as BOUNDARY_CURRENT_STAGE,
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
    DURABILITY_FAILURE_CLASSES,
    FAILURE_CLASS_FILESYSTEM_CAPACITY,
    FAILURE_CLASS_PERMISSION_ACCESS,
    FAILURE_CLASS_SERIALIZATION_VALIDATION,
    FAILURE_CLASS_UNKNOWN_IO,
    DdoDurabilityWriteError,
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
ACCOUNT_TEST_IDENTITY = "acct-uid-test-a1-failure-policy"
ACCOUNT_TEST_CREDENTIAL_REF = "cred-ref-test-a1-failure-policy"
SESSION_ID = "ddo-a1-failure-policy"


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


def test_policy_bound_and_runtime_flags_remain_false() -> None:
    binding = canonical_a1_durability_failure_policy_binding_v1()
    assert isinstance(binding, DdoA1DurabilityFailurePolicyBindingV1)
    assert binding.slice_id == SLICE_ID
    assert IMPLEMENTATION_COMPLETE is True
    assert A1_DURABILITY_FAILURE_POLICY == (
        "BOUND_FAIL_CLOSED_DEPENDENT_MUTATION_FORBIDDEN_ON_UNPROVEN_DURABILITY"
    )
    assert BOUNDARY_A1_DURABILITY_FAILURE_POLICY == A1_DURABILITY_FAILURE_POLICY
    assert CURRENT_STAGE_DURABILITY_FAILURE_POLICY == (
        "FAIL_OPEN_CAPTURE_WITH_EXPLICIT_DURABILITY_FAILURE_EVIDENCE"
    )
    assert BOUNDARY_CURRENT_STAGE == CURRENT_STAGE_DURABILITY_FAILURE_POLICY
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
    with pytest.raises(DdoA1DurabilityFailurePolicyError) as exc:
        DdoA1DurabilityFailurePolicyBindingV1(runtime_authorized=True)
    assert exc.value.failure_class == "A1_RUNTIME_AUTHORIZATION_FORBIDDEN"
    with pytest.raises(DdoA1DurabilityFailurePolicyError):
        DdoA1DurabilityFailurePolicyBindingV1(runtime_authorization_eligible=True)
    with pytest.raises(DdoA1DurabilityFailurePolicyError):
        DdoA1DurabilityFailurePolicyBindingV1(a1_durability_failure_policy="UNBOUND_NOT_AUTHORIZED")
    with pytest.raises(DdoA1DurabilityFailurePolicyError):
        reject_a1_runtime_authorization_attempt_v1(runtime_authorized=True)


def test_existing_failure_classes_bound_without_inventing_taxonomy() -> None:
    assert FAILURE_CLASSES_BOUND == DURABILITY_FAILURE_CLASSES
    for failure_class in sorted(DURABILITY_FAILURE_CLASSES):
        view = a1_failure_class_policy_v1(failure_class, operation=OPERATION_DURABLE_APPEND)
        assert view["a1_failure_policy_failure_class"] == failure_class
        assert view["a1_failure_policy_dependent_mutation_allowed"] is False
        assert view["a1_failure_policy_crash_durability_fully_proven"] is False
        assert view["a1_failure_policy_diagnostic_equivalent_to_primary"] is False
        assert view["a1_failure_policy_primary_masked_by_logging"] is False
        first = bind_a1_durability_failure_policy_v1(
            operation=OPERATION_DURABLE_APPEND,
            failure=DdoDurabilityWriteError(
                failure_class,
                failure_class,
                retryable=None if failure_class == FAILURE_CLASS_UNKNOWN_IO else False,
                operation=OPERATION_DURABLE_APPEND,
            ),
        )
        second = bind_a1_durability_failure_policy_v1(
            operation=OPERATION_DURABLE_APPEND,
            failure=DdoDurabilityWriteError(
                failure_class,
                failure_class,
                retryable=None if failure_class == FAILURE_CLASS_UNKNOWN_IO else False,
                operation=OPERATION_DURABLE_APPEND,
            ),
        )
        assert first == second


def test_success_path_does_not_prove_crash_durability_or_allow_dependent_mutation(
    tmp_path: Path,
) -> None:
    ledger = AppendOnlyDdoLedgerV0(tmp_path / "ok.jsonl")
    result = ledger.append(_decision())
    assert result.status == "APPENDED"
    policy = bind_a1_durability_failure_policy_v1(
        operation=OPERATION_DURABLE_APPEND,
        failure=None,
        record_id=result.record_id,
    )
    assert policy.durability_proven is None
    assert policy.append_acknowledged is True
    assert policy.dependent_mutation_allowed is False
    assert policy.retry_allowed is False
    assert policy.crash_durability_fully_proven is False
    assert policy.unknown_preserved is True
    assert CRASH_DURABILITY_FULLY_PROVEN is False
    unbound_state, unbound = run_bridge_cycles_from_mids_v1(
        [3500.0], session_id=SESSION_ID, require_selection_binding=False
    )
    bound_state, bound = _run_bound_host(tmp_path, session_id=SESSION_ID, mids=[3500.0])
    assert [item.to_dict() for item in unbound] == [item.to_dict() for item in bound]
    assert bound_state.last_ddo_capture is not None
    assert bound_state.last_ddo_capture["decision_unchanged"] is True
    assert bound_state.last_ddo_capture["a1_durability_failure_policy"] == (
        A1_DURABILITY_FAILURE_POLICY
    )
    assert bound_state.last_ddo_capture["a1_failure_policy_runtime_authorized"] is False
    evidence = bound_state.last_ddo_capture.get("durability") or {}
    assert evidence.get("a1_failure_policy_durability_proven") is None
    assert evidence.get("a1_failure_policy_dependent_mutation_allowed") is False
    _ = unbound_state


def test_serialization_failure_is_explicit_and_not_durable(tmp_path: Path) -> None:
    ledger = AppendOnlyDdoLedgerV0(tmp_path / "bad.jsonl")
    with pytest.raises(Exception, match="UNKNOWN_RECORD_SCHEMA|DdoValidationError"):
        ledger.append({"schema_name": "not-a-schema", "schema_version": "x"})
    classified = DdoDurabilityWriteError(
        FAILURE_CLASS_SERIALIZATION_VALIDATION,
        "SERIALIZATION_VALIDATION_FAILURE",
        retryable=False,
        operation=OPERATION_SERIALIZE_VALIDATE,
    )
    policy = bind_a1_durability_failure_policy_v1(
        operation=OPERATION_SERIALIZE_VALIDATE,
        failure=classified,
        record_id="dec-0001",
    )
    assert policy.failure_class == FAILURE_CLASS_SERIALIZATION_VALIDATION
    assert policy.durability_proven is False
    assert policy.append_acknowledged is False
    assert policy.dependent_mutation_allowed is False
    assert policy.retry_allowed is False
    assert policy.recovery_required is False


def test_write_failure_sets_durability_false_and_forbids_retry(
    tmp_path: Path, monkeypatch: Any
) -> None:
    def boom(_fd: int, _data: bytes) -> int:
        raise OSError(errno.ENOSPC, "simulated write failure")

    monkeypatch.setattr(os, "write", boom)
    ledger = AppendOnlyDdoLedgerV0(tmp_path / "full.jsonl")
    with pytest.raises(DdoDurabilityWriteError) as exc:
        ledger.append(_decision())
    assert exc.value.failure_class == FAILURE_CLASS_FILESYSTEM_CAPACITY
    assert exc.value.operation == OPERATION_WRITE
    assert exc.value.retryable is False
    policy = bind_a1_durability_failure_policy_v1(
        operation=OPERATION_WRITE,
        failure=exc.value,
        record_id="dec-0001",
    )
    assert policy.durability_proven is False
    assert policy.dependent_mutation_allowed is False
    assert policy.retry_allowed is False
    assert policy.crash_durability_fully_proven is False


def test_file_fsync_failure_forbids_dependent_mutation(tmp_path: Path, monkeypatch: Any) -> None:
    real_fsync = os.fsync
    real_append = AppendOnlyDdoLedgerV0._append_line

    def boom(fd: int) -> None:
        mode = os.fstat(fd).st_mode
        if stat.S_ISREG(mode):
            raise OSError(errno.EIO, "simulated file fsync failure")
        return real_fsync(fd)

    monkeypatch.setattr(os, "fsync", boom)
    ledger = AppendOnlyDdoLedgerV0(tmp_path / "fsync.jsonl")
    with pytest.raises(DdoDurabilityWriteError) as exc:
        ledger.append(_decision())
    monkeypatch.setattr(os, "fsync", real_fsync)
    assert exc.value.operation == OPERATION_FILE_FSYNC
    policy = bind_a1_durability_failure_policy_v1(
        operation=OPERATION_FILE_FSYNC,
        failure=exc.value,
        record_id="dec-0001",
    )
    assert policy.durability_proven is False or policy.durability_proven is None
    if exc.value.failure_class == FAILURE_CLASS_UNKNOWN_IO:
        assert policy.durability_proven is None
        assert policy.retry_allowed is False
        assert policy.unknown_preserved is True
    else:
        assert policy.durability_proven is False
    assert policy.dependent_mutation_allowed is False
    assert policy.append_acknowledged is False
    with pytest.raises(DdoA1DurabilityFailurePolicyError) as blocked:
        reject_a1_dependent_mutation_on_unproven_durability_v1(
            dependent_mutation_requested=True,
            durability_proven=policy.durability_proven,
        )
    assert blocked.value.failure_class == "A1_DEPENDENT_MUTATION_FORBIDDEN_UNPROVEN_DURABILITY"

    def append_with_file_fsync_boom(self: AppendOnlyDdoLedgerV0, line: str) -> None:
        def inner(fd: int) -> None:
            mode = os.fstat(fd).st_mode
            if stat.S_ISREG(mode):
                raise OSError(errno.EIO, "simulated file fsync failure")
            return real_fsync(fd)

        monkeypatch.setattr(os, "fsync", inner)
        try:
            return real_append(self, line)
        finally:
            monkeypatch.setattr(os, "fsync", real_fsync)

    monkeypatch.setattr(AppendOnlyDdoLedgerV0, "_append_line", append_with_file_fsync_boom)
    unbound_state, unbound = run_bridge_cycles_from_mids_v1(
        [3500.0], session_id="ddo-a1-fp-file-fsync", require_selection_binding=False
    )
    bound_state, bound = _run_bound_host(tmp_path, session_id="ddo-a1-fp-file-fsync", mids=[3500.0])
    assert [item.to_dict() for item in unbound] == [item.to_dict() for item in bound]
    assert CAPTURE_FAILURE_CHANGES_DECISION is False
    assert PRODUCTIVE_RETURN_VALUE_UNCHANGED is True
    _ = unbound_state
    _ = bound_state


def test_directory_fsync_failure_keeps_crash_durability_unproven(
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
    assert policy.append_acknowledged is True
    assert policy.durability_proven is None
    assert policy.crash_durability_fully_proven is False
    assert policy.dependent_mutation_allowed is False
    assert policy.retry_allowed is False
    assert CRASH_DURABILITY_FULLY_PROVEN is False
    assert DIRECTORY_FSYNC_STATUS == "FAIL_CLOSED_ATTEMPTED_NO_PLATFORM_HARD_GUARANTEE"
    assert HOST_CRASH_DURABILITY == "UNPROVEN"
    assert POWER_LOSS_DURABILITY == "UNPROVEN"
    unbound_state, unbound = run_bridge_cycles_from_mids_v1(
        [3500.0], session_id="ddo-a1-fp-dir-fsync", require_selection_binding=False
    )
    bound_state, bound = _run_bound_host(tmp_path, session_id="ddo-a1-fp-dir-fsync", mids=[3500.0])
    assert [item.to_dict() for item in unbound] == [item.to_dict() for item in bound]
    _ = unbound_state
    _ = bound_state


def test_failure_does_not_silently_become_success_and_is_deterministic() -> None:
    failure = DdoDurabilityWriteError(
        FAILURE_CLASS_PERMISSION_ACCESS,
        "PERMISSION_ACCESS_FAILURE",
        retryable=False,
        errno_code=errno.EACCES,
        operation=OPERATION_WRITE,
    )
    first = bind_a1_durability_failure_policy_v1(operation=OPERATION_WRITE, failure=failure)
    second = bind_a1_durability_failure_policy_v1(operation=OPERATION_WRITE, failure=failure)
    assert first == second
    assert first.durability_proven is not True
    assert first.dependent_mutation_allowed is False
    success = bind_a1_durability_failure_policy_v1(operation=OPERATION_DURABLE_APPEND, failure=None)
    assert success.durability_proven is not True
    assert first != success


def test_retry_policy_matches_bound_class_and_forbids_ambiguous_retry() -> None:
    assert AMBIGUOUS_RETRY_ALLOWED is False
    write_failure = DdoDurabilityWriteError(
        FAILURE_CLASS_UNKNOWN_IO,
        "UNKNOWN_UNCLASSIFIED_IO_FAILURE",
        retryable=None,
        operation=OPERATION_WRITE,
    )
    policy = bind_a1_durability_failure_policy_v1(operation=OPERATION_WRITE, failure=write_failure)
    assert policy.retry_allowed is False
    with pytest.raises(DdoA1DurabilityFailurePolicyError):
        type(policy)(
            **{
                **policy.__dict__,
                "retry_allowed": True,
            }
        )


def test_short_write_is_unknown_not_success(tmp_path: Path, monkeypatch: Any) -> None:
    def short(_fd: int, data: bytes) -> int:
        return 1 if len(data) > 1 else 0

    monkeypatch.setattr(os, "write", short)
    ledger = AppendOnlyDdoLedgerV0(tmp_path / "short.jsonl")
    with pytest.raises(DdoDurabilityWriteError) as exc:
        ledger.append(_decision())
    assert exc.value.failure_class == FAILURE_CLASS_UNKNOWN_IO
    assert exc.value.operation == OPERATION_WRITE
    assert exc.value.retryable is None
    policy = bind_a1_durability_failure_policy_v1(operation=OPERATION_WRITE, failure=exc.value)
    assert policy.durability_proven is None
    assert policy.unknown_preserved is True
    assert policy.dependent_mutation_allowed is False
    assert policy.retry_allowed is False


def test_primary_ledger_failure_is_not_masked_by_logging(
    tmp_path: Path, monkeypatch: Any, caplog: pytest.LogCaptureFixture
) -> None:
    assert PRIMARY_LEDGER_FAILURE_MASKED_BY_LOGGING is False
    assert "logging" not in CAPTURE_SRC.read_text(encoding="utf-8")
    assert "logger" not in CAPTURE_SRC.read_text(encoding="utf-8")

    def boom(_fd: int, _data: bytes) -> int:
        raise OSError(errno.EACCES, "simulated permission failure")

    monkeypatch.setattr(os, "write", boom)
    with caplog.at_level(logging.DEBUG):
        unbound_state, unbound = run_bridge_cycles_from_mids_v1(
            [3500.0], session_id="ddo-a1-fp-log-mask", require_selection_binding=False
        )
        bound_state, bound = _run_bound_host(
            tmp_path, session_id="ddo-a1-fp-log-mask", mids=[3500.0]
        )
    assert [item.to_dict() for item in unbound] == [item.to_dict() for item in bound]
    assert bound_state.last_ddo_capture is not None
    evidence = bound_state.last_ddo_capture.get("durability") or {}
    assert evidence.get("success") is False
    assert evidence.get("a1_failure_policy_durability_proven") is not True
    assert evidence.get("a1_failure_policy_primary_masked_by_logging") is False
    assert evidence.get("a1_failure_policy_diagnostic_equivalent_to_primary") is False
    _ = unbound_state


def test_unknown_is_not_normalized_to_false_or_success() -> None:
    assert UNKNOWN_PRESERVED is True
    unknown = DdoDurabilityWriteError(
        FAILURE_CLASS_UNKNOWN_IO,
        "UNKNOWN_UNCLASSIFIED_IO_FAILURE",
        retryable=None,
        operation=OPERATION_WRITE,
    )
    policy = bind_a1_durability_failure_policy_v1(operation=OPERATION_WRITE, failure=unknown)
    assert policy.durability_proven is None
    assert policy.retry_allowed is False or policy.retry_allowed is None
    assert policy.durability_proven is not False
    assert policy.unknown_preserved is True
    success = bind_a1_durability_failure_policy_v1(operation=OPERATION_DURABLE_APPEND, failure=None)
    assert success.durability_proven is None
    assert success.durability_proven is not False
    assert success.durability_proven is not True


def test_no_authority_or_live_drift() -> None:
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
    assert NEW_STORAGE_AUTHORITY_CREATED is False
    assert DEPENDENT_MUTATION_ON_UNPROVEN_DURABILITY == "FORBIDDEN"
    assert FILE_FSYNC_STATUS == "PRESENT"
    stamps = a1_durability_failure_policy_observability_v1()
    assert stamps["a1_failure_policy_runtime_authorized"] is False
    assert stamps["a1_failure_policy_operation_started"] is False
    assert stamps["a1_failure_policy_new_storage_authority_created"] is False
    assert "os.rename" not in LEDGER_SRC.read_text(encoding="utf-8")
    assert "os.replace" not in LEDGER_SRC.read_text(encoding="utf-8")
