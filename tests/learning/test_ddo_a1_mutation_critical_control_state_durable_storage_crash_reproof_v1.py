"""Process-boundary crash reproof for the bound control-state WAL owner.

These tests prove OS-process kill/reopen behavior. They do not prove
HOST_CRASH_DURABILITY or POWER_LOSS_DURABILITY. SIGKILL is not a
host-kernel crash. Exception injection is not a host-crash test.
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest

from src.learning.deterministic_decision_outcome_v0.a1_durability_failure_policy_binding_v1 import (
    DdoA1DurabilityFailurePolicyError,
    reject_a1_dependent_mutation_on_unproven_durability_v1,
)
from src.learning.mutation_critical_control_state_storage_v1.errors_v1 import (
    ControlStateValidationError,
)
from src.learning.mutation_critical_control_state_storage_v1.crash_reproof_v1 import (
    ADMISSION_TRUE,
    ATOMIC_PUBLICATION_STATUS,
    ATOMIC_REPLACE_INTRODUCED,
    CRASH_DURABILITY_FULLY_PROVEN,
    DEPENDENT_MUTATION_ALLOWED,
    DURABILITY_PROVEN_TRUE_MANUFACTURABLE,
    EXCEPTION_INJECTION_IS_HOST_CRASH_PROOF,
    EXISTING_STORAGE_AUTHORITY_REUSED,
    HOST_CRASH_DURABILITY,
    HOST_CRASH_PROOF_ENVIRONMENT_PRESENT,
    NEW_STORAGE_AUTHORITY_CREATED,
    POWER_LOSS_DURABILITY,
    POWER_LOSS_PROOF_ENVIRONMENT_PRESENT,
    PROCESS_KILL_IS_HOST_CRASH_PROOF,
    PROCESS_RESTART_DURABILITY,
    PRODUCTIVE_HOST_BINDING,
    REUSED_STORAGE_OWNER_NAME,
    SUPERVISOR_ACTIVATED,
    TEMPFILE_ATOMIC_PUBLISH_IMPLEMENTED,
    WIRE_SEND_REACHABLE,
)
from src.learning.mutation_critical_control_state_storage_v1.wal_adapter_v1 import (
    MutationCriticalControlStateWalAdapterV1,
    RECOVERY_CLEAN,
    RECOVERY_INCOMPLETE,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CHILD = REPO_ROOT / "tests/learning/_ddo_a1_control_state_wal_process_child_v1.py"
READY_FILENAME = "PROCESS_CHILD_READY"
MASTER_RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
SPEC_PATH = REPO_ROOT / (
    "docs/ops/specs/"
    "DDO_A1_MUTATION_CRITICAL_CONTROL_STATE_DURABLE_STORAGE_IMPLEMENTATION_AND_CRASH_REPROOF_V1.md"
)
PERSIST_HEADING = (
    "### 11.13.5 Parallel-track DDO A1 mutation-critical control-state "
    "durable storage implementation and crash reproof persist"
)
OWNER_PERSIST_HEADING = (
    "### 11.13.5 Parallel-track DDO A1 mutation-critical control-state "
    "storage owner contract persist"
)
Z2DB_HEADING = (
    "### 11.13.5.Z2DB Offline execution-permission and position-creation producer wiring persist"
)


def _spawn_child(root: Path, mode: str, record_id: str) -> subprocess.Popen[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)
    return subprocess.Popen(
        [
            sys.executable,
            str(CHILD),
            "--root",
            str(root),
            "--mode",
            mode,
            "--record-id",
            record_id,
        ],
        cwd=str(REPO_ROOT),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def _wait_ready(root: Path, proc: subprocess.Popen[str], *, timeout_s: float = 8.0) -> None:
    deadline = time.monotonic() + timeout_s
    ready = root / READY_FILENAME
    while time.monotonic() < deadline:
        if ready.is_file():
            return
        code = proc.poll()
        if code is not None:
            raise AssertionError(f"child_exited_before_ready code={code}")
        time.sleep(0.05)
    raise AssertionError("child_ready_timeout")


def _sigkill(proc: subprocess.Popen[str]) -> None:
    proc.send_signal(signal.SIGKILL)
    proc.wait(timeout=5)


def test_reproof_does_not_create_second_storage_authority_or_atomic_replace() -> None:
    assert EXISTING_STORAGE_AUTHORITY_REUSED is True
    assert NEW_STORAGE_AUTHORITY_CREATED is False
    assert REUSED_STORAGE_OWNER_NAME == "MUTATION_CRITICAL_CONTROL_STATE_STORAGE_OWNER"
    assert TEMPFILE_ATOMIC_PUBLISH_IMPLEMENTED is False
    assert ATOMIC_REPLACE_INTRODUCED is False
    assert "NOT_SUPPORTED_BY_BOUND_WAL" in ATOMIC_PUBLICATION_STATUS


def test_unproven_host_crash_and_power_loss_are_not_promoted() -> None:
    assert HOST_CRASH_DURABILITY == "UNPROVEN"
    assert POWER_LOSS_DURABILITY == "UNPROVEN"
    assert HOST_CRASH_PROOF_ENVIRONMENT_PRESENT is False
    assert POWER_LOSS_PROOF_ENVIRONMENT_PRESENT is False
    assert CRASH_DURABILITY_FULLY_PROVEN is False
    assert DURABILITY_PROVEN_TRUE_MANUFACTURABLE is False
    assert PROCESS_KILL_IS_HOST_CRASH_PROOF is False
    assert EXCEPTION_INJECTION_IS_HOST_CRASH_PROOF is False
    assert PROCESS_RESTART_DURABILITY == "PROVEN_WITH_BOUND_ASSUMPTIONS"
    assert PRODUCTIVE_HOST_BINDING is False
    assert ADMISSION_TRUE is False
    assert SUPERVISOR_ACTIVATED is False
    assert WIRE_SEND_REACHABLE is False
    assert DEPENDENT_MUTATION_ALLOWED is False


def test_os_process_kill_after_successful_commit_recovers_record(tmp_path: Path) -> None:
    root = tmp_path / "wal"
    proc = _spawn_child(root, "commit_then_wait", "rec-proc-restart")
    try:
        _wait_ready(root, proc)
        _sigkill(proc)
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait(timeout=5)
    with MutationCriticalControlStateWalAdapterV1(root) as wal:
        report = wal.recovery_report()
        loaded = wal.get("rec-proc-restart")
    assert report.status == RECOVERY_CLEAN
    assert report.durability_proven is False
    assert loaded["record_id"] == "rec-proc-restart"
    assert HOST_CRASH_DURABILITY == "UNPROVEN"


def test_os_process_kill_after_prepare_before_commit_is_incomplete_not_committed(
    tmp_path: Path,
) -> None:
    root = tmp_path / "wal"
    proc = _spawn_child(root, "prepare_then_wait", "rec-proc-crash")
    try:
        _wait_ready(root, proc)
        _sigkill(proc)
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait(timeout=5)
    with MutationCriticalControlStateWalAdapterV1(root) as wal:
        report = wal.recovery_report()
        with pytest.raises(ControlStateValidationError, match="RECORD_NOT_FOUND"):
            wal.get("rec-proc-crash")
    assert report.status == RECOVERY_INCOMPLETE
    assert report.committed_count == 0
    assert report.silent_repair_performed is False
    assert report.durability_proven is False


def test_os_process_kill_before_prepare_leaves_store_without_record(tmp_path: Path) -> None:
    root = tmp_path / "wal"
    proc = _spawn_child(root, "before_prepare_wait", "rec-never-written")
    try:
        _wait_ready(root, proc)
        _sigkill(proc)
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait(timeout=5)
    with MutationCriticalControlStateWalAdapterV1(root) as wal:
        report = wal.recovery_report()
        with pytest.raises(ControlStateValidationError, match="RECORD_NOT_FOUND"):
            wal.get("rec-never-written")
    assert report.committed_count == 0
    assert report.silent_repair_performed is False


def test_dependent_mutation_remains_forbidden_on_unproven_durability() -> None:
    reject_a1_dependent_mutation_on_unproven_durability_v1()
    assert DEPENDENT_MUTATION_ALLOWED is False
    with pytest.raises(
        DdoA1DurabilityFailurePolicyError,
        match="A1_DEPENDENT_MUTATION_FORBIDDEN_UNPROVEN_DURABILITY",
    ):
        reject_a1_dependent_mutation_on_unproven_durability_v1(dependent_mutation_requested=True)
    with pytest.raises(
        DdoA1DurabilityFailurePolicyError,
        match="A1_CRASH_DURABILITY_OVERCLAIM_FORBIDDEN",
    ):
        reject_a1_dependent_mutation_on_unproven_durability_v1(durability_proven=True)


def test_canonical_reproof_persist_and_spec_exist() -> None:
    spec = SPEC_PATH.read_text(encoding="utf-8")
    runbook = MASTER_RUNBOOK.read_text(encoding="utf-8")
    assert "HOST_CRASH_DURABILITY=UNPROVEN" in spec
    assert "POWER_LOSS_DURABILITY=UNPROVEN" in spec
    assert "NEW_STORAGE_AUTHORITY_CREATED=false" in spec
    assert "EXISTING_STORAGE_AUTHORITY_REUSED=true" in spec
    assert "PROCESS_KILL_IS_HOST_CRASH_PROOF=false" in spec
    assert "DEPENDENT_MUTATION_ALLOWED=false" in spec
    assert PERSIST_HEADING in runbook
    owner = runbook.index(OWNER_PERSIST_HEADING)
    reproof = runbook.index(PERSIST_HEADING)
    z2db = runbook.index(Z2DB_HEADING)
    assert owner < reproof < z2db
    section = runbook[reproof:z2db]
    assert "NEW_STORAGE_AUTHORITY_CREATED=false" in section
    assert "HOST_CRASH_DURABILITY=UNPROVEN" in section
    assert "DEPENDENT_MUTATION_ALLOWED=false" in section
    assert "CURRENT_CANONICAL_SECTION_REPLACED=false" in section
