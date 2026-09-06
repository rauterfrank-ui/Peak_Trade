"""DDO A1 unattended durability runtime-authorization adjudication v1.

Observation-only. No trading authority. No runtime activation.
"""

from __future__ import annotations

import errno
import os
import stat
from pathlib import Path
from typing import Any

import pytest

from src.governance.live_mode_gate import ExecutionEnvironment
from src.learning.deterministic_decision_outcome_v0.a1_unattended_durability_policy_boundary_v1 import (
    A1_UNATTENDED_DURABILITY_POLICY_DEFINED,
    A1_UNATTENDED_DURABILITY_RUNTIME_AUTHORIZED,
    canonical_a1_unattended_durability_policy_boundary_v1,
)
from src.learning.deterministic_decision_outcome_v0.a1_unattended_durability_runtime_authorization_v1 import (
    APPEND_ONLY_STATUS,
    ATOMIC_WRITE_STATUS,
    AUTHORIZATION_FAILURE_REASON,
    AUTHORIZATION_SOURCE,
    AUTHORIZATION_SOURCE_CLASS,
    AUTHORIZATION_SOURCE_FOUND,
    CRASH_DURABILITY_FULLY_PROVEN,
    DIRECTORY_FSYNC_STATUS,
    DURABILITY_CLASS,
    FILE_FSYNC_STATUS,
    IMPLEMENTATION_COMPLETE,
    IMPLEMENTATION_GO_IS_RUNTIME_AUTHORIZATION,
    NEXT_OWNER_GO_REQUIRED,
    OPERATION_STARTED,
    PRECONDITIONS_PROVEN,
    PRODUCTIVE_RETURN_VALUE_UNCHANGED,
    RENAME_ATOMIC_REPLACE_PRESENT,
    RUNTIME_AUTHORIZATION_ELIGIBLE,
    RUNTIME_AUTHORIZED,
    RUNTIME_OPERATIONAL_AUTHORIZATION_SOURCE,
    SLICE_ID,
    TRADING_DECISION_DEPENDS_ON_LEDGER_WRITE,
    UNATTENDED_OPERATION_STARTED,
    DdoA1RuntimeAuthorizationError,
    DdoA1UnattendedDurabilityRuntimeAuthorizationV1,
    a1_runtime_authorization_observability_v1,
    canonical_a1_unattended_durability_runtime_authorization_v1,
    reject_a1_runtime_authorization_activation_v1,
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
HOST_PATH = (
    REPO_ROOT
    / "src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1"
    / "decision_economics_cycle_bridge_v1.py"
)
BINDING_PATH = (
    REPO_ROOT
    / "src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1"
    / "ddo_observation_host_scope_binding_v1.py"
)
AUTH_PATH = (
    REPO_ROOT
    / "src/learning/deterministic_decision_outcome_v0"
    / "a1_unattended_durability_runtime_authorization_v1.py"
)
LEDGER_SRC = REPO_ROOT / "src/learning/deterministic_decision_outcome_v0/ledger_v0.py"
ACCOUNT_TEST_IDENTITY = "acct-uid-test-a1-runtime-auth"
ACCOUNT_TEST_CREDENTIAL_REF = "cred-ref-test-a1-runtime-auth"
SESSION_ID = "ddo-a1-runtime-authorization"


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


def test_runtime_authorization_states_remain_separated_and_fail_closed() -> None:
    adjudication = canonical_a1_unattended_durability_runtime_authorization_v1()
    assert isinstance(adjudication, DdoA1UnattendedDurabilityRuntimeAuthorizationV1)
    assert adjudication.slice_id == SLICE_ID
    assert IMPLEMENTATION_COMPLETE is True
    assert adjudication.implementation_complete is True
    assert PRECONDITIONS_PROVEN is False
    assert RUNTIME_AUTHORIZATION_ELIGIBLE is False
    assert RUNTIME_AUTHORIZED is False
    assert OPERATION_STARTED is False
    assert UNATTENDED_OPERATION_STARTED is False
    assert IMPLEMENTATION_GO_IS_RUNTIME_AUTHORIZATION is False
    assert RUNTIME_OPERATIONAL_AUTHORIZATION_SOURCE == "NONE"
    assert AUTHORIZATION_SOURCE_FOUND is True
    assert AUTHORIZATION_SOURCE == "NONE"
    assert AUTHORIZATION_SOURCE_CLASS == "NONE"
    assert NEXT_OWNER_GO_REQUIRED is True
    assert AUTHORIZATION_FAILURE_REASON == "A1_RUNTIME_AUTHORIZATION_PRECONDITIONS_UNPROVEN"
    assert A1_UNATTENDED_DURABILITY_POLICY_DEFINED is True
    assert A1_UNATTENDED_DURABILITY_RUNTIME_AUTHORIZED is False
    with pytest.raises(DdoA1RuntimeAuthorizationError) as exc:
        DdoA1UnattendedDurabilityRuntimeAuthorizationV1(runtime_authorized=True)
    assert exc.value.failure_class == "A1_RUNTIME_AUTHORIZATION_FORBIDDEN"
    with pytest.raises(DdoA1RuntimeAuthorizationError):
        DdoA1UnattendedDurabilityRuntimeAuthorizationV1(runtime_authorization_eligible=True)
    with pytest.raises(DdoA1RuntimeAuthorizationError):
        DdoA1UnattendedDurabilityRuntimeAuthorizationV1(preconditions_proven=True)
    with pytest.raises(DdoA1RuntimeAuthorizationError):
        DdoA1UnattendedDurabilityRuntimeAuthorizationV1(operation_started=True)


def test_implementation_complete_coexists_with_runtime_unauthorized() -> None:
    adjudication = canonical_a1_unattended_durability_runtime_authorization_v1()
    assert adjudication.implementation_complete is True
    assert adjudication.runtime_authorized is False
    stamps = a1_runtime_authorization_observability_v1()
    assert stamps["a1_implementation_complete"] is True
    assert stamps["a1_unattended_durability_runtime_authorized"] is False
    assert stamps["a1_runtime_authorization_eligible"] is False
    assert stamps["a1_operation_started"] is False
    with pytest.raises(DdoA1RuntimeAuthorizationError):
        reject_a1_runtime_authorization_activation_v1(runtime_authorized=True)
    with pytest.raises(DdoA1RuntimeAuthorizationError):
        reject_a1_runtime_authorization_activation_v1(unattended_operation_started=True)


def test_crash_durability_class_d_not_overclaimed() -> None:
    adjudication = canonical_a1_unattended_durability_runtime_authorization_v1()
    assert DURABILITY_CLASS == "PLATFORM_HARD_GUARANTEE_NOT_PROVABLE"
    assert adjudication.durability_class == DURABILITY_CLASS
    assert ATOMIC_WRITE_STATUS == "PARTIAL"
    assert FILE_FSYNC_STATUS == "PRESENT"
    assert DIRECTORY_FSYNC_STATUS == "FAIL_CLOSED_ATTEMPTED_NO_PLATFORM_HARD_GUARANTEE"
    assert CRASH_DURABILITY_FULLY_PROVEN is False
    assert APPEND_ONLY_STATUS == "ENFORCED_O_APPEND"
    assert RENAME_ATOMIC_REPLACE_PRESENT is False
    ledger = LEDGER_SRC.read_text(encoding="utf-8")
    assert "os.O_APPEND" in ledger
    assert "os.rename" not in ledger
    assert "os.replace" not in ledger
    assert "NamedTemporaryFile" not in ledger
    dir_fsync_block = ledger[ledger.rindex("os.fsync(dir_fd)") :]
    assert "raise classify_oserror_v0(exc) from exc" in dir_fsync_block
    assert "except OSError:\n            pass" not in dir_fsync_block
    with pytest.raises(DdoA1RuntimeAuthorizationError):
        DdoA1UnattendedDurabilityRuntimeAuthorizationV1(crash_durability_fully_proven=True)
    with pytest.raises(DdoA1RuntimeAuthorizationError):
        DdoA1UnattendedDurabilityRuntimeAuthorizationV1(
            durability_class="FULLY_PROVEN_EXISTING_MECHANISM"
        )


def test_file_fsync_failure_is_classified_and_does_not_change_decision(
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
        session_id="ddo-a1-file-fsync",
        require_selection_binding=False,
    )
    bound_state, bound = _run_bound_host(tmp_path, session_id="ddo-a1-file-fsync", mids=[3500.0])
    assert [item.to_dict() for item in unbound] == [item.to_dict() for item in bound]
    assert bound_state.last_ddo_capture is not None
    assert bound_state.last_ddo_capture["decision_unchanged"] is True
    assert bound_state.last_ddo_capture["a1_unattended_durability_runtime_authorized"] is False
    assert bound_state.last_ddo_capture["a1_runtime_authorization_eligible"] is False
    _ = unbound_state


def test_directory_fsync_failure_is_fail_closed_and_does_not_change_decision(
    tmp_path: Path, monkeypatch: Any
) -> None:
    real_fsync = os.fsync
    real_append = AppendOnlyDdoLedgerV0._append_line

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
        session_id="ddo-a1-dir-fsync",
        require_selection_binding=False,
    )
    bound_state, bound = _run_bound_host(tmp_path, session_id="ddo-a1-dir-fsync", mids=[3500.0])
    assert [item.to_dict() for item in unbound] == [item.to_dict() for item in bound]
    assert bound_state.last_ddo_capture is not None
    assert bound_state.last_ddo_capture["decision_unchanged"] is True
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
    restarted, restarted_cycles = _run_bound_host(tmp_path, session_id="ddo-a1-truncated")
    unbound_state, unbound = run_bridge_cycles_from_mids_v1(
        [3500.0], session_id="ddo-a1-truncated", require_selection_binding=False
    )
    assert [item.to_dict() for item in restarted_cycles] == [item.to_dict() for item in unbound]
    assert path.read_text(encoding="utf-8") == original[:-1]
    assert restarted.last_ddo_capture is not None
    assert restarted.last_ddo_capture["a1_unattended_durability_runtime_authorized"] is False
    _ = unbound_state


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


def test_no_second_trading_authority_or_live_drift(tmp_path: Path) -> None:
    state, cycles = _run_bound_host(tmp_path)
    unbound_state, unbound = run_bridge_cycles_from_mids_v1(
        [3500.0], session_id=SESSION_ID, require_selection_binding=False
    )
    assert [item.to_dict() for item in cycles] == [item.to_dict() for item in unbound]
    assert AUTHORITY_OWNER == "NONE"
    assert SECOND_TRADING_AUTHORITY_CREATED is False
    assert SECOND_EXECUTION_AUTHORITY_CREATED is False
    assert LEARNING_PRODUCTIVE_AUTHORITY == "NONE"
    assert LIVE_EFFECT == "NONE"
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert WIRE_SEND_PERMITTED is False
    assert LIVE_AUTHORIZED is False
    assert TESTNET_AUTHORIZED is False
    assert ORDERS_AUTHORIZED is False
    assert PAPER_EXECUTION_AUTHORIZED is False
    assert canonical_a1_unattended_durability_policy_boundary_v1().runtime_authorized is False
    assert state.last_ddo_capture is not None
    assert state.last_ddo_capture["a1_new_storage_authority_created"] is False
    assert state.last_ddo_capture["a1_durability_class"] == DURABILITY_CLASS
    for source_path in (HOST_PATH, BINDING_PATH, AUTH_PATH):
        text = source_path.read_text(encoding="utf-8")
        assert "LIVE_ENABLED = True" not in text
        assert "LIVE_ARMED = True" not in text
        assert "WIRE_SEND_PERMITTED = True" not in text
        assert "daemon" not in text.lower()
        assert "while True" not in text
    _ = unbound_state
