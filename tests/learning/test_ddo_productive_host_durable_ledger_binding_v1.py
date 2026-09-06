"""DDO productive observation-host durable ledger binding v1.

Consumes bound host scopes, resolve_ddo_durable_evidence_path_v1, and
AppendOnlyDdoLedgerV0. Observation-only. No trading authority.
"""

from __future__ import annotations

import errno
import fcntl
import os
from pathlib import Path
from typing import Any

import pytest

from src.governance.live_mode_gate import ExecutionEnvironment
from src.learning.deterministic_decision_outcome_v0.authority_v0 import (
    AUTHORITY_OWNER,
    LEARNING_PRODUCTIVE_AUTHORITY,
    LIVE_EFFECT,
    SECOND_EXECUTION_AUTHORITY_CREATED,
    SECOND_TRADING_AUTHORITY_CREATED,
    TESTNET_EFFECT,
)
from src.learning.deterministic_decision_outcome_v0.capture_v0 import (
    CAPTURE_FAILURE_CHANGES_DECISION,
)
from src.learning.deterministic_decision_outcome_v0.durable_evidence_path_v0 import (
    DDO_EVIDENCE_SYSTEM_SCOPE_TOKEN,
    resolve_ddo_durable_evidence_path_v1,
)
from src.learning.deterministic_decision_outcome_v0.errors_v0 import (
    FAILURE_CLASS_CONCURRENT_WRITER,
    FAILURE_CLASS_DUPLICATE_CONFLICT,
    FAILURE_CLASS_PERMISSION_ACCESS,
    DdoDuplicateConflictError,
)
from src.learning.deterministic_decision_outcome_v0.ledger_v0 import (
    LEDGER_FILENAME_DEFAULT,
    AppendOnlyDdoLedgerV0,
)
from src.learning.deterministic_decision_outcome_v0.serialization_v0 import compute_content_hash_v0
from src.ops.capability_11_2_credential_authorization_and_account_identity_boundary_v1.account_identity_boundary_v1 import (
    AccountIdentityRecordV1,
    build_account_identity_record_v1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.constants_v1 import (
    LIVE_AUTHORIZED,
    ORDERS_AUTHORIZED,
    PAPER_EXECUTION_AUTHORIZED,
    TESTNET_AUTHORIZED,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.ddo_observation_host_scope_binding_v1 import (
    SCOPE_INPUT_CONFLICT,
    DdoHostScopeInputError,
    bind_ddo_observation_host_scope_v1,
    resolve_ddo_observation_host_durable_ledger_path_v1,
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
ACCOUNT_TEST_IDENTITY = "acct-uid-test-ledger-binding"
ACCOUNT_TEST_CREDENTIAL_REF = "cred-ref-test-ledger-binding"
SESSION_ID = "ddo-host-ledger-binding"


def _account_record(*, identity: str = ACCOUNT_TEST_IDENTITY) -> AccountIdentityRecordV1:
    return build_account_identity_record_v1(
        account_identity=identity,
        venue="OKX",
        credential_ref_id=ACCOUNT_TEST_CREDENTIAL_REF,
        account_scope="trading-only",
        expected_uid=identity,
    )


def _expected_path(
    root: Path,
    *,
    environment: ExecutionEnvironment = ExecutionEnvironment.DEV,
    account: str = ACCOUNT_TEST_IDENTITY,
) -> Path:
    return resolve_ddo_durable_evidence_path_v1(
        runtime_state_root=root,
        environment=environment.value,
        account_scope=account,
        system_scope=DDO_EVIDENCE_SYSTEM_SCOPE_TOKEN,
    )


def _run_bound_host(
    tmp_path: Path,
    *,
    session_id: str = SESSION_ID,
    mids: list[float] | None = None,
    environment: ExecutionEnvironment = ExecutionEnvironment.DEV,
    account: AccountIdentityRecordV1 | None = None,
) -> tuple[BridgeSessionStateV1, list[Any]]:
    return run_bridge_cycles_from_mids_v1(
        mids if mids is not None else [3500.0],
        session_id=session_id,
        require_selection_binding=False,
        ddo_durable_evidence_runtime_state_root=tmp_path,
        ddo_evidence_environment=environment,
        ddo_account_identity_record=account if account is not None else _account_record(),
    )


def test_path_resolution_from_bound_host_scopes(tmp_path: Path) -> None:
    state, _cycles = _run_bound_host(tmp_path, environment=ExecutionEnvironment.SHADOW)
    expected = _expected_path(tmp_path, environment=ExecutionEnvironment.SHADOW)
    assert expected == (
        tmp_path
        / "ddo"
        / "shadow"
        / ACCOUNT_TEST_IDENTITY
        / "canonical_trading_path"
        / LEDGER_FILENAME_DEFAULT
    )
    assert state.ddo_observation_host_scope is not None
    derived = resolve_ddo_observation_host_durable_ledger_path_v1(state.ddo_observation_host_scope)
    assert derived == expected
    assert Path(state.ddo_capture_binding.ledger_path) == expected
    assert state.ddo_durable_ledger_path == str(expected)
    assert state.ddo_observation_host_scope.ledger_path_resolved is True
    assert state.ddo_observation_host_scope.system_scope == "canonical_trading_path"


def test_path_resolver_consumed_by_real_host_and_scope_derived(tmp_path: Path) -> None:
    binding_source = BINDING_PATH.read_text(encoding="utf-8")
    host_source = HOST_PATH.read_text(encoding="utf-8")
    assert "resolve_ddo_durable_evidence_path_v1(" in binding_source
    assert "resolve_ddo_durable_evidence_path_v1(" not in host_source
    assert "Path.cwd" not in binding_source
    assert "Path.home" not in binding_source
    assert "tempfile" not in binding_source
    state, _ = _run_bound_host(tmp_path)
    assert state.last_ddo_capture is not None
    assert state.last_ddo_capture["path_binding_state"] == "BOUND"
    assert state.last_ddo_capture["ledger_bound"] is True
    assert state.last_ddo_capture["resolved_path_is_scope_derived"] is True
    assert "ddo_ledger_path_unresolved" not in state.last_ddo_capture


def test_no_path_fallback(tmp_path: Path, monkeypatch: Any) -> None:
    def _boom_cwd() -> Path:
        raise AssertionError("CWD_FALLBACK_FORBIDDEN")

    def _boom_home() -> Path:
        raise AssertionError("HOME_FALLBACK_FORBIDDEN")

    monkeypatch.setattr(Path, "cwd", classmethod(lambda cls: _boom_cwd()))
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: _boom_home()))
    state, _ = _run_bound_host(tmp_path)
    assert Path(state.ddo_capture_binding.ledger_path).is_relative_to(tmp_path)
    with pytest.raises(DdoHostScopeInputError) as relative:
        bind_ddo_observation_host_scope_v1(
            BridgeSessionStateV1(require_selection_binding=False),
            runtime_state_root="relative/root",
            environment=ExecutionEnvironment.DEV,
            account_identity_record=_account_record(),
        )
    assert relative.value.failure_class in {"SCOPE_INPUT_INVALID", "PATH_BINDING_FAILURE"}


def test_durable_append_reachable_from_host(tmp_path: Path) -> None:
    state, _ = _run_bound_host(tmp_path, mids=[3500.0, 3510.0])
    ledger = state.ddo_capture_binding.ledger()
    assert isinstance(ledger, AppendOnlyDdoLedgerV0)
    assert ledger.ledger_path == Path(state.ddo_capture_binding.ledger_path)
    records = ledger.read_all()
    assert len(records) >= 1
    assert ledger.ledger_path.is_file()
    assert state.ddo_capture_binding.persisted_ids
    assert state.last_ddo_capture is not None
    assert state.last_ddo_capture["durable_ok"] is True


def test_host_restart_resolves_same_path_and_reads_existing_ledger(tmp_path: Path) -> None:
    first, _ = _run_bound_host(tmp_path, mids=[3500.0, 3510.0])
    first_path = Path(first.ddo_capture_binding.ledger_path)
    first_records = AppendOnlyDdoLedgerV0(first_path).read_all()
    second, _ = _run_bound_host(tmp_path, mids=[3500.0, 3510.0])
    second_path = Path(second.ddo_capture_binding.ledger_path)
    assert first_path == second_path
    second_records = AppendOnlyDdoLedgerV0(second_path).read_all()
    assert [row["record_id"] for row in second_records] == [
        row["record_id"] for row in first_records
    ]
    jsonl = sorted(path for path in tmp_path.rglob("*.jsonl") if path.is_file())
    assert jsonl == [first_path]


def test_no_new_ledger_per_restart_and_restart_idempotency(tmp_path: Path) -> None:
    first, _ = _run_bound_host(tmp_path, mids=[3500.0])
    path = Path(first.ddo_capture_binding.ledger_path)
    text_after_first = path.read_text(encoding="utf-8")
    second, _ = _run_bound_host(tmp_path, mids=[3500.0])
    assert Path(second.ddo_capture_binding.ledger_path) == path
    assert path.read_text(encoding="utf-8") == text_after_first
    replay = AppendOnlyDdoLedgerV0(path).append(dict(AppendOnlyDdoLedgerV0(path).read_all()[0]))
    assert replay.status == "IDEMPOTENT_REPLAY"
    assert path.read_text(encoding="utf-8") == text_after_first


def test_duplicate_conflict_behavior_on_host_bound_ledger(tmp_path: Path) -> None:
    state, _ = _run_bound_host(tmp_path)
    ledger = state.ddo_capture_binding.ledger()
    assert ledger is not None
    original = dict(ledger.read_all()[0])
    mutated = dict(original)
    mutated["producer_id"] = str(original.get("producer_id") or "producer") + ".conflict"
    mutated["content_hash"] = compute_content_hash_v0(mutated)
    with pytest.raises(DdoDuplicateConflictError, match="DUPLICATE_RECORD_ID_CONFLICT"):
        ledger.append(mutated)
    loaded = ledger.read_all()
    assert loaded[0]["content_hash"] == original["content_hash"]
    assert state.last_ddo_capture is not None
    assert state.last_ddo_capture["decision_unchanged"] is True
    _ = FAILURE_CLASS_DUPLICATE_CONFLICT


def test_failed_append_retry_through_host_binding(tmp_path: Path, monkeypatch: Any) -> None:
    original = AppendOnlyDdoLedgerV0._append_line
    fail = {"on": True}

    def boom(self: AppendOnlyDdoLedgerV0, line: str) -> None:
        if fail["on"]:
            raise OSError(errno.EACCES, "Permission denied")
        return original(self, line)

    monkeypatch.setattr(AppendOnlyDdoLedgerV0, "_append_line", boom)
    state = BridgeSessionStateV1(require_selection_binding=False)
    bind_ddo_observation_host_scope_v1(
        state,
        runtime_state_root=tmp_path,
        environment=ExecutionEnvironment.DEV,
        account_identity_record=_account_record(),
    )
    failed = run_bridge_cycle_v1(
        state,
        mid_price=3500.0,
        event_ts_unix=1_700_000_000.0,
        session_id="ddo-host-retry",
    )
    assert state.last_ddo_capture is not None
    assert state.last_ddo_capture["decision_unchanged"] is True
    assert state.last_ddo_capture["durable_ok"] is False
    assert state.last_ddo_capture["failure_class"] == FAILURE_CLASS_PERMISSION_ACCESS
    assert state.ddo_capture_binding.persisted_ids == []
    fail["on"] = False
    retried = run_bridge_cycle_v1(
        state,
        mid_price=3510.0,
        event_ts_unix=1_700_000_001.0,
        session_id="ddo-host-retry",
    )
    assert retried.ok == failed.ok
    assert retried.decision_authority_owner == failed.decision_authority_owner
    assert state.ddo_capture_binding.persisted_ids
    assert state.last_ddo_capture["durable_ok"] is True
    assert Path(state.ddo_capture_binding.ledger_path).is_file()


def test_concurrent_writer_fail_fast_on_host_bound_ledger(tmp_path: Path) -> None:
    first, _ = _run_bound_host(tmp_path, session_id="ddo-host-lock-holder")
    ledger = first.ddo_capture_binding.ledger()
    assert ledger is not None
    lock_path = ledger.writer_lock_path()
    fd = os.open(str(lock_path), os.O_RDWR)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        baseline, baseline_cycles = run_bridge_cycles_from_mids_v1(
            [3500.0], session_id="ddo-host-concurrent", require_selection_binding=False
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
            session_id="ddo-host-concurrent",
        )
        assert cycle.to_dict() == baseline_cycles[0].to_dict()
        assert blocked.last_ddo_capture is not None
        assert blocked.last_ddo_capture["decision_unchanged"] is True
        assert blocked.last_ddo_capture["durable_ok"] is False
        assert blocked.last_ddo_capture["failure_class"] == FAILURE_CLASS_CONCURRENT_WRITER
        _ = baseline
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


def test_capture_failure_isolation_and_trading_decision_unchanged(
    tmp_path: Path, monkeypatch: Any
) -> None:
    def boom(self: AppendOnlyDdoLedgerV0, line: str) -> None:
        raise OSError(errno.EACCES, "Permission denied")

    monkeypatch.setattr(AppendOnlyDdoLedgerV0, "_append_line", boom)
    unbound_state, unbound = run_bridge_cycles_from_mids_v1(
        [3500.0, 3510.0],
        session_id="ddo-host-isolation",
        require_selection_binding=False,
    )
    bound_state, bound = _run_bound_host(
        tmp_path,
        session_id="ddo-host-isolation",
        mids=[3500.0, 3510.0],
    )
    assert [item.to_dict() for item in unbound] == [item.to_dict() for item in bound]
    assert bound_state.last_ddo_capture is not None
    assert bound_state.last_ddo_capture["decision_unchanged"] is True
    assert bound_state.last_ddo_capture["capture_failure_changes_current_decision"] is False
    assert CAPTURE_FAILURE_CHANGES_DECISION is False
    assert unbound_state.ddo_capture_binding.ledger_path is None


def test_productive_return_value_unchanged_on_successful_bind(tmp_path: Path) -> None:
    unbound_state, unbound = run_bridge_cycles_from_mids_v1(
        [3500.0, 3510.0],
        session_id="ddo-host-return",
        require_selection_binding=False,
    )
    bound_state, bound = _run_bound_host(
        tmp_path,
        session_id="ddo-host-return",
        mids=[3500.0, 3510.0],
        environment=ExecutionEnvironment.TESTNET,
    )
    assert [item.to_dict() for item in unbound] == [item.to_dict() for item in bound]
    assert bound_state.ddo_capture_binding.ledger_path is not None
    assert unbound_state.ddo_capture_binding.ledger_path is None


def test_scope_change_yields_different_path_and_no_mid_lifecycle_rebind(tmp_path: Path) -> None:
    dev_state, _ = _run_bound_host(tmp_path, environment=ExecutionEnvironment.DEV)
    prod_state, _ = _run_bound_host(tmp_path, environment=ExecutionEnvironment.PROD)
    assert Path(dev_state.ddo_capture_binding.ledger_path) != Path(
        prod_state.ddo_capture_binding.ledger_path
    )
    assert "dev" in str(dev_state.ddo_capture_binding.ledger_path)
    assert "prod" in str(prod_state.ddo_capture_binding.ledger_path)
    original = Path(dev_state.ddo_capture_binding.ledger_path)
    with pytest.raises(DdoHostScopeInputError) as conflict:
        bind_ddo_observation_host_scope_v1(
            dev_state,
            runtime_state_root=tmp_path,
            environment=ExecutionEnvironment.PROD,
            account_identity_record=_account_record(),
        )
    assert conflict.value.failure_class == SCOPE_INPUT_CONFLICT
    assert Path(dev_state.ddo_capture_binding.ledger_path) == original
    mutated = BridgeSessionStateV1(require_selection_binding=False)
    bind_ddo_observation_host_scope_v1(
        mutated,
        runtime_state_root=tmp_path,
        environment=ExecutionEnvironment.DEV,
        account_identity_record=_account_record(),
    )
    bound_path = Path(mutated.ddo_capture_binding.ledger_path)
    mutated.ddo_evidence_environment = "prod"
    baseline, baseline_cycles = run_bridge_cycles_from_mids_v1(
        [3500.0], session_id="ddo-host-rebind", require_selection_binding=False
    )
    cycle = run_bridge_cycle_v1(
        mutated,
        mid_price=3500.0,
        event_ts_unix=1_700_000_000.0,
        session_id="ddo-host-rebind",
    )
    assert cycle.to_dict() == baseline_cycles[0].to_dict()
    assert mutated.last_ddo_capture is not None
    assert mutated.last_ddo_capture["scope_input_failure_class"] == SCOPE_INPUT_CONFLICT
    assert mutated.last_ddo_capture["decision_unchanged"] is True
    assert Path(mutated.ddo_capture_binding.ledger_path) == bound_path
    _ = baseline


def test_master_v2_double_play_and_live_execution_authority_unchanged(tmp_path: Path) -> None:
    _state, _ = _run_bound_host(tmp_path)
    assert AUTHORITY_OWNER == "NONE"
    assert LEARNING_PRODUCTIVE_AUTHORITY == "NONE"
    assert SECOND_TRADING_AUTHORITY_CREATED is False
    assert SECOND_EXECUTION_AUTHORITY_CREATED is False
    assert LIVE_EFFECT == "NONE"
    assert TESTNET_EFFECT == "NONE"
    assert LIVE_AUTHORIZED is False
    assert TESTNET_AUTHORIZED is False
    assert ORDERS_AUTHORIZED is False
    assert PAPER_EXECUTION_AUTHORIZED is False
    host = HOST_PATH.read_text(encoding="utf-8")
    binding = BINDING_PATH.read_text(encoding="utf-8")
    for source in (host, binding):
        assert "LIVE_ENABLED = True" not in source
        assert "LIVE_ARMED = True" not in source
        assert "class ExecutionEnvironment" not in source
