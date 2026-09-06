"""DDO A1 crash-durability atomic-replace-or-nonrequirement adjudication v1.

Observation-only. No trading authority. No runtime activation.
No atomic replace. No explicit non-requirement.
"""

from __future__ import annotations

import errno
import os
import stat
from pathlib import Path
from typing import Any

import pytest

from src.governance.live_mode_gate import ExecutionEnvironment
from src.learning.deterministic_decision_outcome_v0.a1_crash_durability_atomic_replace_or_explicit_nonrequirement_v1 import (
    ADJUDICATION_CLASS,
    APPEND_ONLY_STATUS,
    ATOMIC_REPLACE_IMPLEMENTED,
    ATOMIC_REPLACE_INCOMPATIBLE_WITH_APPEND_ONLY,
    ATOMIC_REPLACE_REQUIRED,
    ATOMIC_WRITE_MODEL,
    ATOMIC_WRITE_STATUS,
    AUTHORIZATION_FAILURE_REASON,
    CRASH_DURABILITY_FULLY_PROVEN,
    CRASH_DURABILITY_PRECONDITION_PROVEN,
    CRASH_DURABILITY_REQUIRED,
    DIRECTORY_FSYNC_STATUS,
    DURABILITY_CLASS,
    EXPLICIT_NONREQUIREMENT_PROVEN,
    FILE_FSYNC_STATUS,
    FILESYSTEM_COMMIT_DURABILITY,
    HOST_CRASH_DURABILITY,
    IMPLEMENTATION_COMPLETE,
    IMPLEMENTATION_GO_IS_RUNTIME_AUTHORIZATION,
    NEW_STORAGE_AUTHORITY_CREATED,
    NEXT_DDO_STEP,
    NEXT_OWNER_GO_REQUIRED,
    NONREQUIREMENT_SOURCE,
    NONREQUIREMENT_SOURCE_FOUND,
    OPERATION_STARTED,
    OTHER_RUNTIME_PRECONDITIONS_PROVEN,
    POWER_LOSS_DURABILITY,
    PROCESS_RESTART_DURABILITY,
    PRODUCTIVE_RETURN_VALUE_UNCHANGED,
    RENAME_ATOMIC_REPLACE_PRESENT,
    RUNTIME_AUTHORIZATION_ELIGIBLE,
    RUNTIME_AUTHORIZED,
    RUNTIME_OPERATIONAL_AUTHORIZATION_SOURCE,
    SLICE_ID,
    TRADING_DECISION_DEPENDS_ON_LEDGER_WRITE,
    UNATTENDED_OPERATION_STARTED,
    DdoA1CrashDurabilityAdjudicationError,
    DdoA1CrashDurabilityAtomicReplaceOrExplicitNonrequirementV1,
    a1_crash_durability_adjudication_observability_v1,
    canonical_a1_crash_durability_atomic_replace_or_explicit_nonrequirement_v1,
    reject_a1_crash_durability_overclaim_v1,
)
from src.learning.deterministic_decision_outcome_v0.a1_unattended_durability_policy_boundary_v1 import (
    A1_UNATTENDED_DURABILITY_POLICY_DEFINED,
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

REPO_ROOT = Path(__file__).resolve().parents[2]
LEDGER_SRC = REPO_ROOT / "src/learning/deterministic_decision_outcome_v0/ledger_v0.py"
ACCOUNT_TEST_IDENTITY = "acct-uid-test-a1-crash-durability"
ACCOUNT_TEST_CREDENTIAL_REF = "cred-ref-test-a1-crash-durability"
SESSION_ID = "ddo-a1-crash-durability"


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


def test_adjudication_class_d_and_separated_runtime_states() -> None:
    adjudication = canonical_a1_crash_durability_atomic_replace_or_explicit_nonrequirement_v1()
    assert isinstance(adjudication, DdoA1CrashDurabilityAtomicReplaceOrExplicitNonrequirementV1)
    assert adjudication.slice_id == SLICE_ID
    assert ADJUDICATION_CLASS == "PLATFORM_FULL_GUARANTEE_STILL_NOT_PROVABLE"
    assert adjudication.adjudication_class == ADJUDICATION_CLASS
    assert IMPLEMENTATION_COMPLETE is True
    assert CRASH_DURABILITY_PRECONDITION_PROVEN is False
    assert OTHER_RUNTIME_PRECONDITIONS_PROVEN is False
    assert RUNTIME_AUTHORIZATION_ELIGIBLE is False
    assert RUNTIME_AUTHORIZED is False
    assert OPERATION_STARTED is False
    assert UNATTENDED_OPERATION_STARTED is False
    assert IMPLEMENTATION_GO_IS_RUNTIME_AUTHORIZATION is False
    assert RUNTIME_OPERATIONAL_AUTHORIZATION_SOURCE == "NONE"
    assert NEXT_OWNER_GO_REQUIRED is True
    assert AUTHORIZATION_FAILURE_REASON == (
        "A1_CRASH_DURABILITY_PLATFORM_FULL_GUARANTEE_STILL_NOT_PROVABLE"
    )
    assert NEXT_DDO_STEP == "PEAK_TRADE_DDO_A1_DURABILITY_FAILURE_POLICY_BINDING_V1"
    assert A1_UNATTENDED_DURABILITY_POLICY_DEFINED is True
    assert A1_UNATTENDED_DURABILITY_RUNTIME_AUTHORIZED is False
    with pytest.raises(DdoA1CrashDurabilityAdjudicationError) as exc:
        DdoA1CrashDurabilityAtomicReplaceOrExplicitNonrequirementV1(
            crash_durability_fully_proven=True
        )
    assert exc.value.failure_class == "A1_CRASH_DURABILITY_OVERCLAIM_FORBIDDEN"
    with pytest.raises(DdoA1CrashDurabilityAdjudicationError):
        DdoA1CrashDurabilityAtomicReplaceOrExplicitNonrequirementV1(runtime_authorized=True)
    with pytest.raises(DdoA1CrashDurabilityAdjudicationError):
        DdoA1CrashDurabilityAtomicReplaceOrExplicitNonrequirementV1(
            runtime_authorization_eligible=True
        )
    with pytest.raises(DdoA1CrashDurabilityAdjudicationError):
        DdoA1CrashDurabilityAtomicReplaceOrExplicitNonrequirementV1(
            explicit_nonrequirement_proven=True
        )


def test_explicit_nonrequirement_not_proven_and_atomic_replace_not_implemented() -> None:
    adjudication = canonical_a1_crash_durability_atomic_replace_or_explicit_nonrequirement_v1()
    assert CRASH_DURABILITY_REQUIRED is True
    assert EXPLICIT_NONREQUIREMENT_PROVEN is False
    assert NONREQUIREMENT_SOURCE_FOUND is False
    assert NONREQUIREMENT_SOURCE == "NONE"
    assert ATOMIC_REPLACE_REQUIRED is False
    assert ATOMIC_REPLACE_IMPLEMENTED is False
    assert ATOMIC_REPLACE_INCOMPATIBLE_WITH_APPEND_ONLY is True
    assert RENAME_ATOMIC_REPLACE_PRESENT is False
    assert ATOMIC_WRITE_MODEL == "ENFORCED_O_APPEND_JSONL_LINE"
    assert APPEND_ONLY_STATUS == "ENFORCED_O_APPEND"
    assert NEW_STORAGE_AUTHORITY_CREATED is False
    assert adjudication.atomic_replace_implemented is False
    ledger = LEDGER_SRC.read_text(encoding="utf-8")
    assert "os.O_APPEND" in ledger
    assert "os.rename" not in ledger
    assert "os.replace" not in ledger
    assert "NamedTemporaryFile" not in ledger
    with pytest.raises(DdoA1CrashDurabilityAdjudicationError):
        DdoA1CrashDurabilityAtomicReplaceOrExplicitNonrequirementV1(atomic_replace_implemented=True)
    with pytest.raises(DdoA1CrashDurabilityAdjudicationError):
        reject_a1_crash_durability_overclaim_v1(crash_durability_fully_proven=True)


def test_durability_proof_contract_does_not_overclaim() -> None:
    adjudication = canonical_a1_crash_durability_atomic_replace_or_explicit_nonrequirement_v1()
    assert DURABILITY_CLASS == "PLATFORM_HARD_GUARANTEE_NOT_PROVABLE"
    assert ATOMIC_WRITE_STATUS == "PARTIAL"
    assert FILE_FSYNC_STATUS == "PRESENT"
    assert DIRECTORY_FSYNC_STATUS == "FAIL_CLOSED_ATTEMPTED_NO_PLATFORM_HARD_GUARANTEE"
    assert PROCESS_RESTART_DURABILITY == "BEST_EFFORT_FILE_FSYNC_NOT_FULLY_PROVEN"
    assert HOST_CRASH_DURABILITY == "UNPROVEN"
    assert FILESYSTEM_COMMIT_DURABILITY == "UNPROVEN"
    assert POWER_LOSS_DURABILITY == "UNPROVEN"
    assert CRASH_DURABILITY_FULLY_PROVEN is False
    assert adjudication.power_loss_durability == "UNPROVEN"
    stamps = a1_crash_durability_adjudication_observability_v1()
    assert stamps["a1_crash_durability_adjudication_class"] == ADJUDICATION_CLASS
    assert stamps["a1_crash_durability_fully_proven"] is False
    assert stamps["a1_atomic_replace_implemented"] is False
    assert stamps["a1_explicit_nonrequirement_proven"] is False
    assert stamps["a1_power_loss_durability"] == "UNPROVEN"
    with pytest.raises(DdoA1CrashDurabilityAdjudicationError):
        DdoA1CrashDurabilityAtomicReplaceOrExplicitNonrequirementV1(
            adjudication_class="ATOMIC_REPLACE_REQUIRED_AND_EXISTING_OWNER_CAN_IMPLEMENT"
        )


def test_file_and_directory_fsync_failures_do_not_change_decision(
    tmp_path: Path, monkeypatch: Any
) -> None:
    real_fsync = os.fsync
    real_append = AppendOnlyDdoLedgerV0._append_line

    def append_with_file_fsync_boom(self: AppendOnlyDdoLedgerV0, line: str) -> None:
        def boom(fd: int) -> None:
            mode = os.fstat(fd).st_mode
            if stat.S_ISREG(mode):
                raise OSError(errno.EIO, "simulated file fsync failure")
            return real_fsync(fd)

        monkeypatch.setattr(os, "fsync", boom)
        try:
            return real_append(self, line)
        finally:
            monkeypatch.setattr(os, "fsync", real_fsync)

    monkeypatch.setattr(AppendOnlyDdoLedgerV0, "_append_line", append_with_file_fsync_boom)
    unbound_state, unbound = run_bridge_cycles_from_mids_v1(
        [3500.0],
        session_id="ddo-a1-crash-file-fsync",
        require_selection_binding=False,
    )
    bound_state, bound = _run_bound_host(
        tmp_path, session_id="ddo-a1-crash-file-fsync", mids=[3500.0]
    )
    assert [item.to_dict() for item in unbound] == [item.to_dict() for item in bound]
    assert bound_state.last_ddo_capture is not None
    assert bound_state.last_ddo_capture["decision_unchanged"] is True
    _ = unbound_state

    def append_with_dir_fsync_boom(self: AppendOnlyDdoLedgerV0, line: str) -> None:
        def boom(fd: int) -> None:
            mode = os.fstat(fd).st_mode
            if stat.S_ISDIR(mode):
                raise OSError(errno.EIO, "simulated directory fsync failure")
            return real_fsync(fd)

        monkeypatch.setattr(os, "fsync", boom)
        try:
            return real_append(self, line)
        finally:
            monkeypatch.setattr(os, "fsync", real_fsync)

    monkeypatch.setattr(AppendOnlyDdoLedgerV0, "_append_line", append_with_dir_fsync_boom)
    with pytest.raises(DdoDurabilityWriteError):
        AppendOnlyDdoLedgerV0(tmp_path / "forced.jsonl")._append_line("{}\n")
    unbound_state, unbound = run_bridge_cycles_from_mids_v1(
        [3500.0],
        session_id="ddo-a1-crash-dir-fsync",
        require_selection_binding=False,
    )
    bound_state, bound = _run_bound_host(
        tmp_path, session_id="ddo-a1-crash-dir-fsync", mids=[3500.0]
    )
    assert [item.to_dict() for item in unbound] == [item.to_dict() for item in bound]
    assert CAPTURE_FAILURE_CHANGES_DECISION is False
    assert TRADING_DECISION_DEPENDS_ON_LEDGER_WRITE is False
    assert PRODUCTIVE_RETURN_VALUE_UNCHANGED is True
    _ = unbound_state


def test_truncated_ledger_after_partial_append_is_detected(tmp_path: Path) -> None:
    state, _ = _run_bound_host(tmp_path)
    path = Path(state.ddo_capture_binding.ledger_path)
    original = path.read_text(encoding="utf-8")
    path.write_text(original[:-1], encoding="utf-8")
    with pytest.raises(Exception, match="LEDGER_MISSING_TRAILING_NEWLINE"):
        AppendOnlyDdoLedgerV0(path).verify_integrity()
    restarted, restarted_cycles = _run_bound_host(tmp_path, session_id="ddo-a1-crash-truncated")
    unbound_state, unbound = run_bridge_cycles_from_mids_v1(
        [3500.0], session_id="ddo-a1-crash-truncated", require_selection_binding=False
    )
    assert [item.to_dict() for item in restarted_cycles] == [item.to_dict() for item in unbound]
    assert path.read_text(encoding="utf-8") == original[:-1]
    assert restarted.last_ddo_capture is not None
    assert restarted.last_ddo_capture["a1_crash_durability_fully_proven"] is False
    _ = unbound_state
    _ = state


def test_no_rename_path_and_restart_reuses_existing_history(tmp_path: Path) -> None:
    first, _ = _run_bound_host(tmp_path, mids=[3500.0, 3510.0])
    first_path = Path(first.ddo_capture_binding.ledger_path)
    first_text = first_path.read_text(encoding="utf-8")
    second, _ = _run_bound_host(tmp_path, mids=[3500.0, 3510.0])
    second_path = Path(second.ddo_capture_binding.ledger_path)
    assert second_path == first_path
    assert second_path.read_text(encoding="utf-8") == first_text
    assert RENAME_ATOMIC_REPLACE_PRESENT is False
    assert "os.rename(" not in LEDGER_SRC.read_text(encoding="utf-8")
    assert "os.replace(" not in LEDGER_SRC.read_text(encoding="utf-8")


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
    stamps = a1_crash_durability_adjudication_observability_v1()
    assert stamps["a1_crash_durability_runtime_authorized"] is False
    assert stamps["a1_crash_durability_operation_started"] is False
    assert stamps["a1_crash_durability_new_storage_authority_created"] is False
