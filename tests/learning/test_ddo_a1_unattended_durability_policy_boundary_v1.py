"""DDO A1 unattended durability policy boundary v1.

Typed fail-closed policy. Observation-only. No trading authority.
"""

from __future__ import annotations

import errno
import fcntl
import json
import os
from pathlib import Path
from typing import Any

import pytest

from src.governance.live_mode_gate import ExecutionEnvironment
from src.learning.deterministic_decision_outcome_v0.a1_unattended_durability_policy_boundary_v1 import (
    A1_DURABILITY_FAILURE_POLICY,
    A1_EXECUTION_AUTHORITY,
    A1_LEARNING_AUTHORITY,
    A1_LEARNING_PROMOTION_AUTHORIZED,
    A1_TRADING_AUTHORITY,
    A1_UNATTENDED_AUTHORITY,
    A1_UNATTENDED_DURABILITY_POLICY_DEFINED,
    A1_UNATTENDED_DURABILITY_RUNTIME_AUTHORIZED,
    A1_UNATTENDED_EXECUTION_AUTHORIZED,
    A1_UNATTENDED_TRADING_AUTHORIZED,
    ATOMIC_WRITE_STATUS,
    CONCURRENT_WRITER_POLICY,
    CORRUPTION_POLICY,
    CRASH_DURABILITY_FULLY_PROVEN,
    CURRENT_STAGE_DURABILITY_FAILURE_POLICY,
    DIRECTORY_FSYNC_STATUS,
    DUPLICATE_CONFLICT_POLICY,
    FALLBACK_LEDGER_ALLOWED,
    FILE_FSYNC_STATUS,
    IMPLEMENTATION_AUTHORIZATION_SOURCE,
    IMPLEMENTATION_GO_IS_RUNTIME_AUTHORIZATION,
    RECOVERY_DISPOSITION_FAIL_CLOSED,
    RUNTIME_OPERATIONAL_AUTHORIZATION_SOURCE,
    SILENT_LEDGER_RESET_ALLOWED,
    UNSUPPORTED_SCHEMA_POLICY,
    DdoA1PolicyAuthorizationError,
    DdoA1UnattendedDurabilityPolicyBoundaryV1,
    a1_named_recovery_policy_v1,
    a1_recovery_disposition_v1,
    assert_a1_no_silent_ledger_reset_v1,
    assert_a1_restart_reuses_existing_path_v1,
    canonical_a1_unattended_durability_policy_boundary_v1,
    reject_a1_runtime_authorization_attempt_v1,
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
    FAILURE_CLASS_CONCURRENT_WRITER,
    FAILURE_CLASS_CORRUPTION_UNREADABLE,
    FAILURE_CLASS_DUPLICATE_CONFLICT,
    FAILURE_CLASS_UNSUPPORTED_SCHEMA,
    DdoDuplicateConflictError,
    DdoLedgerCorruptionError,
    DdoUnsupportedSchemaVersionError,
)
from src.learning.deterministic_decision_outcome_v0.ledger_v0 import AppendOnlyDdoLedgerV0
from src.learning.deterministic_decision_outcome_v0.serialization_v0 import compute_content_hash_v0
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
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.ddo_observation_host_scope_binding_v1 import (
    bind_ddo_observation_host_scope_v1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.decision_economics_cycle_bridge_v1 import (
    BridgeSessionStateV1,
    run_bridge_cycle_v1,
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
POLICY_PATH = (
    REPO_ROOT
    / "src/learning/deterministic_decision_outcome_v0"
    / "a1_unattended_durability_policy_boundary_v1.py"
)
LEDGER_SRC = REPO_ROOT / "src/learning/deterministic_decision_outcome_v0/ledger_v0.py"
ACCOUNT_TEST_IDENTITY = "acct-uid-test-a1-policy"
ACCOUNT_TEST_CREDENTIAL_REF = "cred-ref-test-a1-policy"
SESSION_ID = "ddo-a1-policy-boundary"


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


def test_a1_unattended_durability_policy_typed_and_default_fail_closed() -> None:
    policy = canonical_a1_unattended_durability_policy_boundary_v1()
    assert isinstance(policy, DdoA1UnattendedDurabilityPolicyBoundaryV1)
    assert A1_UNATTENDED_DURABILITY_POLICY_DEFINED is True
    assert policy.policy_defined is True
    assert policy.runtime_authorized is False
    assert A1_UNATTENDED_DURABILITY_RUNTIME_AUTHORIZED is False
    assert A1_UNATTENDED_TRADING_AUTHORIZED is False
    assert A1_UNATTENDED_EXECUTION_AUTHORIZED is False
    assert A1_LEARNING_PROMOTION_AUTHORIZED is False
    assert A1_TRADING_AUTHORITY is False
    assert A1_EXECUTION_AUTHORITY is False
    assert A1_LEARNING_AUTHORITY is False
    assert A1_UNATTENDED_AUTHORITY is False
    assert A1_DURABILITY_FAILURE_POLICY == "UNBOUND_NOT_AUTHORIZED"
    assert CURRENT_STAGE_DURABILITY_FAILURE_POLICY == (
        "FAIL_OPEN_CAPTURE_WITH_EXPLICIT_DURABILITY_FAILURE_EVIDENCE"
    )
    with pytest.raises(DdoA1PolicyAuthorizationError) as exc:
        DdoA1UnattendedDurabilityPolicyBoundaryV1(runtime_authorized=True)
    assert exc.value.failure_class == "A1_RUNTIME_AUTHORIZATION_FORBIDDEN"


def test_implementation_go_is_not_runtime_authorization() -> None:
    policy = canonical_a1_unattended_durability_policy_boundary_v1()
    assert IMPLEMENTATION_GO_IS_RUNTIME_AUTHORIZATION is False
    assert policy.implementation_go_is_runtime_authorization is False
    assert policy.implementation_authorization_source == IMPLEMENTATION_AUTHORIZATION_SOURCE
    assert RUNTIME_OPERATIONAL_AUTHORIZATION_SOURCE == "NONE"
    assert policy.runtime_operational_authorization_source == "NONE"
    with pytest.raises(DdoA1PolicyAuthorizationError):
        reject_a1_runtime_authorization_attempt_v1(unattended_durability_authorized=True)


def test_unattended_durability_is_not_trading_execution_or_promotion(
    tmp_path: Path,
) -> None:
    state, cycles = _run_bound_host(tmp_path)
    unbound_state, unbound = run_bridge_cycles_from_mids_v1(
        [3500.0], session_id=SESSION_ID, require_selection_binding=False
    )
    assert [item.to_dict() for item in cycles] == [item.to_dict() for item in unbound]
    assert state.last_ddo_capture is not None
    assert state.last_ddo_capture["a1_unattended_trading_authorized"] is False
    assert state.last_ddo_capture["a1_unattended_execution_authorized"] is False
    assert state.last_ddo_capture["a1_learning_promotion_authorized"] is False
    assert A1_TRADING_AUTHORITY is False
    assert A1_EXECUTION_AUTHORITY is False
    assert LEARNING_PRODUCTIVE_AUTHORITY == "NONE"
    _ = unbound_state


def test_same_scope_restart_same_ledger_and_existing_history(tmp_path: Path) -> None:
    first, _ = _run_bound_host(tmp_path, mids=[3500.0, 3510.0])
    first_path = Path(first.ddo_capture_binding.ledger_path)
    first_text = first_path.read_text(encoding="utf-8")
    first_records = AppendOnlyDdoLedgerV0(first_path).read_all()
    second, _ = _run_bound_host(tmp_path, mids=[3500.0, 3510.0])
    second_path = Path(second.ddo_capture_binding.ledger_path)
    assert_a1_restart_reuses_existing_path_v1(first_path, second_path)
    recovered = AppendOnlyDdoLedgerV0(second_path).read_all()
    assert [row["record_id"] for row in recovered] == [row["record_id"] for row in first_records]
    assert second_path.read_text(encoding="utf-8") == first_text
    jsonl = sorted(path for path in tmp_path.rglob("*.jsonl") if path.is_file())
    assert jsonl == [first_path]


def test_no_silent_ledger_reset_and_no_fallback_ledger(tmp_path: Path, monkeypatch: Any) -> None:
    state, _ = _run_bound_host(tmp_path)
    path = Path(state.ddo_capture_binding.ledger_path)
    original = path.read_text(encoding="utf-8")
    truncated = original[:-1]
    path.write_text(truncated, encoding="utf-8")
    with pytest.raises(DdoLedgerCorruptionError, match="LEDGER_MISSING_TRAILING_NEWLINE"):
        AppendOnlyDdoLedgerV0(path).verify_integrity()
    restarted = BridgeSessionStateV1(require_selection_binding=False)
    bind_ddo_observation_host_scope_v1(
        restarted,
        runtime_state_root=tmp_path,
        environment=ExecutionEnvironment.DEV,
        account_identity_record=_account_record(),
    )
    run_bridge_cycle_v1(
        restarted,
        mid_price=3520.0,
        event_ts_unix=1_700_000_010.0,
        session_id="ddo-a1-corrupt-restart",
    )
    assert Path(restarted.ddo_capture_binding.ledger_path) == path
    assert_a1_no_silent_ledger_reset_v1(path, truncated)
    assert path.read_text(encoding="utf-8") == truncated
    assert SILENT_LEDGER_RESET_ALLOWED is False
    assert FALLBACK_LEDGER_ALLOWED is False

    def _boom_cwd() -> Path:
        raise AssertionError("CWD_FALLBACK_FORBIDDEN")

    monkeypatch.setattr(Path, "cwd", classmethod(lambda cls: _boom_cwd()))
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: Path("/tmp/forbidden-a1-home")))
    bound, _ = _run_bound_host(tmp_path / "fresh-root", session_id="ddo-a1-no-fallback")
    assert Path(bound.ddo_capture_binding.ledger_path).is_relative_to(tmp_path / "fresh-root")


def test_corruption_and_unsupported_schema_fail_closed(tmp_path: Path) -> None:
    state, _ = _run_bound_host(tmp_path)
    path = Path(state.ddo_capture_binding.ledger_path)
    assert a1_named_recovery_policy_v1(FAILURE_CLASS_CORRUPTION_UNREADABLE) == CORRUPTION_POLICY
    assert (
        a1_named_recovery_policy_v1(FAILURE_CLASS_UNSUPPORTED_SCHEMA) == UNSUPPORTED_SCHEMA_POLICY
    )
    assert CORRUPTION_POLICY == RECOVERY_DISPOSITION_FAIL_CLOSED
    first_line = path.read_text(encoding="utf-8").splitlines()[0]
    raw = json.loads(first_line)
    raw["envelope_schema_version"] = "ledger_envelope_v999"
    path.write_text(json.dumps(raw) + "\n", encoding="utf-8")
    before = path.read_text(encoding="utf-8")
    with pytest.raises((DdoUnsupportedSchemaVersionError, DdoLedgerCorruptionError)):
        AppendOnlyDdoLedgerV0(path).verify_integrity()
    restarted = BridgeSessionStateV1(require_selection_binding=False)
    bind_ddo_observation_host_scope_v1(
        restarted,
        runtime_state_root=tmp_path,
        environment=ExecutionEnvironment.DEV,
        account_identity_record=_account_record(),
    )
    baseline, baseline_cycles = run_bridge_cycles_from_mids_v1(
        [3500.0], session_id="ddo-a1-schema", require_selection_binding=False
    )
    cycle = run_bridge_cycle_v1(
        restarted,
        mid_price=3500.0,
        event_ts_unix=1_700_000_000.0,
        session_id="ddo-a1-schema",
    )
    assert cycle.to_dict() == baseline_cycles[0].to_dict()
    assert_a1_no_silent_ledger_reset_v1(path, before)
    assert a1_recovery_disposition_v1(FAILURE_CLASS_UNSUPPORTED_SCHEMA) == (
        RECOVERY_DISPOSITION_FAIL_CLOSED
    )
    _ = baseline


def test_duplicate_conflict_and_concurrent_writer_fail_closed(tmp_path: Path) -> None:
    first, _ = _run_bound_host(tmp_path, session_id="ddo-a1-lock-holder")
    ledger = first.ddo_capture_binding.ledger()
    assert ledger is not None
    original = dict(ledger.read_all()[0])
    mutated = dict(original)
    mutated["producer_id"] = str(original.get("producer_id") or "producer") + ".conflict"
    mutated["content_hash"] = compute_content_hash_v0(mutated)
    with pytest.raises(DdoDuplicateConflictError):
        ledger.append(mutated)
    assert (
        a1_named_recovery_policy_v1(FAILURE_CLASS_DUPLICATE_CONFLICT) == DUPLICATE_CONFLICT_POLICY
    )
    lock_path = ledger.writer_lock_path()
    fd = os.open(str(lock_path), os.O_RDWR)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        baseline, baseline_cycles = run_bridge_cycles_from_mids_v1(
            [3500.0], session_id="ddo-a1-concurrent", require_selection_binding=False
        )
        blocked = BridgeSessionStateV1(require_selection_binding=False)
        bind_ddo_observation_host_scope_v1(
            blocked,
            runtime_state_root=tmp_path,
            environment=ExecutionEnvironment.DEV,
            account_identity_record=_account_record(),
        )
        cycle = run_bridge_cycle_v1(
            blocked,
            mid_price=3500.0,
            event_ts_unix=1_700_000_000.0,
            session_id="ddo-a1-concurrent",
        )
        assert cycle.to_dict() == baseline_cycles[0].to_dict()
        assert blocked.last_ddo_capture is not None
        assert blocked.last_ddo_capture["failure_class"] == FAILURE_CLASS_CONCURRENT_WRITER
        assert blocked.last_ddo_capture["decision_unchanged"] is True
        assert a1_named_recovery_policy_v1(FAILURE_CLASS_CONCURRENT_WRITER) == (
            CONCURRENT_WRITER_POLICY
        )
        _ = baseline
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


def test_trading_decision_and_productive_return_unchanged(tmp_path: Path, monkeypatch: Any) -> None:
    def boom(self: AppendOnlyDdoLedgerV0, line: str) -> None:
        raise OSError(errno.EACCES, "Permission denied")

    monkeypatch.setattr(AppendOnlyDdoLedgerV0, "_append_line", boom)
    unbound_state, unbound = run_bridge_cycles_from_mids_v1(
        [3500.0, 3510.0],
        session_id="ddo-a1-isolation",
        require_selection_binding=False,
    )
    bound_state, bound = _run_bound_host(
        tmp_path, session_id="ddo-a1-isolation", mids=[3500.0, 3510.0]
    )
    assert [item.to_dict() for item in unbound] == [item.to_dict() for item in bound]
    assert bound_state.last_ddo_capture is not None
    assert bound_state.last_ddo_capture["decision_unchanged"] is True
    assert bound_state.last_ddo_capture["capture_failure_changes_current_decision"] is False
    assert CAPTURE_FAILURE_CHANGES_DECISION is False
    assert unbound_state.last_ddo_capture is not None
    assert unbound_state.last_ddo_capture["a1_unattended_durability_runtime_authorized"] is False


def test_live_enabled_armed_and_wire_send_unchanged(tmp_path: Path) -> None:
    _state, _ = _run_bound_host(tmp_path)
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert WIRE_SEND_PERMITTED is False
    assert LIVE_AUTHORIZED is False
    assert TESTNET_AUTHORIZED is False
    assert ORDERS_AUTHORIZED is False
    assert PAPER_EXECUTION_AUTHORIZED is False
    for source_path in (HOST_PATH, BINDING_PATH, POLICY_PATH):
        text = source_path.read_text(encoding="utf-8")
        assert "LIVE_ENABLED = True" not in text
        assert "LIVE_ARMED = True" not in text
        assert "WIRE_SEND_PERMITTED = True" not in text


def test_crash_durability_claim_not_upgraded() -> None:
    policy = canonical_a1_unattended_durability_policy_boundary_v1()
    assert policy.crash_durability_fully_proven is False
    assert CRASH_DURABILITY_FULLY_PROVEN is False
    assert ATOMIC_WRITE_STATUS == "PARTIAL"
    assert FILE_FSYNC_STATUS == "PRESENT"
    assert DIRECTORY_FSYNC_STATUS == "BEST_EFFORT_NO_HARD_GUARANTEE"
    ledger = LEDGER_SRC.read_text(encoding="utf-8")
    assert "os.O_APPEND" in ledger
    assert "os.fsync(fd)" in ledger
    assert "os.fsync(dir_fd)" in ledger
    assert "except OSError:\n            pass" in ledger
    assert AUTHORITY_OWNER == "NONE"
    assert SECOND_TRADING_AUTHORITY_CREATED is False
    assert SECOND_EXECUTION_AUTHORITY_CREATED is False
    assert LIVE_EFFECT == "NONE"
    policy_src = POLICY_PATH.read_text(encoding="utf-8")
    assert "daemon" not in policy_src.lower()
    assert "background live" not in policy_src.lower()
    assert "while True" not in policy_src
