"""DDO ledger durability hardening and host-binding prep v1.

Observation-only. No productive host ledger_path. No trading authority.
"""

from __future__ import annotations

import ast
import errno
import fcntl
import json
import os
from pathlib import Path
from typing import Any

import pytest

from src.governance.live_mode_gate import ExecutionEnvironment
from src.learning.deterministic_decision_outcome_v0.authority_v0 import (
    AUTHORITY_OWNER,
    LEARNING_PRODUCTIVE_AUTHORITY,
    SECOND_EXECUTION_AUTHORITY_CREATED,
    SECOND_TRADING_AUTHORITY_CREATED,
)
from src.learning.deterministic_decision_outcome_v0.capture_v0 import (
    DdoCaptureBindingV0,
    SEAM_DOUBLE_PLAY_ENTRY_EXIT,
    SEAM_SELECTION_UNIVERSE,
    observe_producer_result_v0,
    record_productive_cycle_capture_v0,
)
from src.learning.deterministic_decision_outcome_v0.durable_evidence_path_v0 import (
    DDO_EVIDENCE_ACCOUNT_OWNER,
    DDO_EVIDENCE_ENVIRONMENT_OWNER,
    DDO_EVIDENCE_ENVIRONMENT_TOKENS,
    DDO_EVIDENCE_SYSTEM_SCOPE_TOKEN,
    LOGICAL_CONFIG_KEY_DDO_DURABLE_EVIDENCE_RUNTIME_STATE_ROOT,
    resolve_ddo_durable_evidence_path_v1,
)
from src.learning.deterministic_decision_outcome_v0.errors_v0 import (
    DdoConcurrentWriterError,
    DdoDurabilityWriteError,
    DdoIntegrityError,
    DdoLedgerCorruptionError,
    DdoMalformedRecordError,
    DdoPathResolutionError,
    DdoUnsupportedSchemaVersionError,
    FAILURE_CLASS_CONCURRENT_WRITER,
    FAILURE_CLASS_CORRUPTION_UNREADABLE,
    FAILURE_CLASS_FILESYSTEM_CAPACITY,
    FAILURE_CLASS_PERMISSION_ACCESS,
    FAILURE_CLASS_UNKNOWN_IO,
)
from src.learning.deterministic_decision_outcome_v0.ledger_v0 import (
    AppendOnlyDdoLedgerV0,
    LEDGER_FILENAME_DEFAULT,
    canonical_json_dumps_v0,
)
from src.ops.capability_11_2_credential_authorization_and_account_identity_boundary_v1.constants_v1 import (
    ACCOUNT_IDENTITY_BOUNDARY_OWNER,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.decision_economics_cycle_bridge_v1 import (
    BridgeSessionStateV1,
    run_bridge_cycle_v1,
    run_bridge_cycles_from_mids_v1,
)
from tests.learning.test_ddo_current_double_play_decision_capture_parity_v1 import (
    _enter_long,
)
from tests.learning.test_deterministic_decision_outcome_event_contract_v0 import (
    _decision,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_DIR = REPO_ROOT / "src" / "learning" / "deterministic_decision_outcome_v0"
HOST_PATH = (
    REPO_ROOT
    / "src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1"
    / "decision_economics_cycle_bridge_v1.py"
)
CAPTURE_PATH = PACKAGE_DIR / "capture_v0.py"
PATH_MODULE = PACKAGE_DIR / "durable_evidence_path_v0.py"

FORBIDDEN_IMPORT_PREFIXES = (
    "src.trading",
    "src.execution",
    "src.live",
    "src.risk",
    "src.risk_layer",
    "src.governance.promotion",
    "src.ops",
)


def _universe_result() -> dict[str, Any]:
    return {"ok": False, "hard_stop": True, "failure_codes": ("OKX_SOURCE_UNAVAILABLE",)}


def _observe(
    binding: DdoCaptureBindingV0,
    *,
    event_time_utc: str = "2026-09-06T12:00:00Z",
    correlation_id: str = "ddo.corr.harden.1",
) -> dict[str, Any]:
    return observe_producer_result_v0(
        binding,
        seam_id=SEAM_SELECTION_UNIVERSE,
        result=_universe_result(),
        event_time_utc=event_time_utc,
        correlation_id=correlation_id,
    )


def _import_hits(path: Path) -> list[str]:
    hits: list[str] = []
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        names: list[str] = []
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.append(node.module)
        for name in names:
            if any(
                name == prefix or name.startswith(prefix + ".")
                for prefix in FORBIDDEN_IMPORT_PREFIXES
            ):
                hits.append(f"{path.name}:{name}")
    return hits


def test_append_read_happy_path(tmp_path: Path) -> None:
    path = tmp_path / "ddo_ledger_v0.jsonl"
    ledger = AppendOnlyDdoLedgerV0(path)
    result = ledger.append(_decision())
    assert result.status == "APPENDED"
    loaded = ledger.read_all()
    assert len(loaded) == 1
    assert loaded[0]["record_id"] == "dec-0001"


def test_identical_replay_idempotent_and_restart(tmp_path: Path) -> None:
    path = tmp_path / "ddo_ledger_v0.jsonl"
    first = AppendOnlyDdoLedgerV0(path).append(_decision())
    reopened = AppendOnlyDdoLedgerV0(path)
    replay = reopened.append(_decision())
    assert replay.status == "IDEMPOTENT_REPLAY"
    assert replay.sequence == first.sequence
    assert len(reopened.read_all()) == 1


def test_same_id_different_content_conflict(tmp_path: Path) -> None:
    path = tmp_path / "ddo_ledger_v0.jsonl"
    ledger = AppendOnlyDdoLedgerV0(path)
    ledger.append(_decision())
    with pytest.raises(Exception, match="DUPLICATE_RECORD_ID_CONFLICT"):
        ledger.append(_decision(decision_type="STALE_BLOCK"))


def test_failed_append_retry_succeeds_and_does_not_poison(tmp_path: Path, monkeypatch: Any) -> None:
    path = tmp_path / "ddo_ledger_v0.jsonl"
    binding = DdoCaptureBindingV0(enabled=True, ledger_path=path)
    calls = {"n": 0}
    original = AppendOnlyDdoLedgerV0._append_line

    def boom(self: AppendOnlyDdoLedgerV0, line: str) -> None:
        calls["n"] += 1
        if calls["n"] == 1:
            raise OSError(errno.ENOSPC, "No space left on device")
        return original(self, line)

    monkeypatch.setattr(AppendOnlyDdoLedgerV0, "_append_line", boom)
    failed = _observe(binding)
    assert failed["durable_ok"] is False
    assert failed["decision_unchanged"] is True
    assert failed["failure_class"] == FAILURE_CLASS_FILESYSTEM_CAPACITY
    assert failed["durability"]["success"] is False
    record_id = failed["record_id"]
    assert record_id in binding.observed_ids
    assert record_id in binding.captured_ids
    assert record_id not in binding.persisted_ids
    assert not path.exists() or path.read_text(encoding="utf-8") == ""

    retry = _observe(binding)
    assert retry["durable_ok"] is True
    assert retry["record_id"] == record_id
    assert record_id in binding.persisted_ids
    loaded = AppendOnlyDdoLedgerV0(path).read_all()
    assert [row["record_id"] for row in loaded] == [record_id]


def test_permission_enospc_and_generic_io_classification(tmp_path: Path, monkeypatch: Any) -> None:
    path = tmp_path / "ddo_ledger_v0.jsonl"

    def raise_errno(code: int, message: str) -> Any:
        def boom(self: AppendOnlyDdoLedgerV0, line: str) -> None:
            raise OSError(code, message)

        return boom

    monkeypatch.setattr(
        AppendOnlyDdoLedgerV0, "_append_line", raise_errno(errno.EACCES, "Permission denied")
    )
    permission = _observe(DdoCaptureBindingV0(enabled=True, ledger_path=path))
    assert permission["failure_class"] == FAILURE_CLASS_PERMISSION_ACCESS
    assert permission["retryability"] is False

    monkeypatch.setattr(
        AppendOnlyDdoLedgerV0,
        "_append_line",
        raise_errno(errno.ENOSPC, "No space left on device"),
    )
    capacity = _observe(DdoCaptureBindingV0(enabled=True, ledger_path=path))
    assert capacity["failure_class"] == FAILURE_CLASS_FILESYSTEM_CAPACITY

    monkeypatch.setattr(AppendOnlyDdoLedgerV0, "_append_line", raise_errno(errno.EIO, "I/O error"))
    generic = _observe(DdoCaptureBindingV0(enabled=True, ledger_path=path))
    assert generic["failure_class"] == FAILURE_CLASS_UNKNOWN_IO
    assert generic["retryability"] is None
    assert generic["decision_unchanged"] is True
    assert generic["capture_failure_changes_current_decision"] is False


def test_malformed_truncated_hash_and_chain_corruption(tmp_path: Path) -> None:
    path = tmp_path / "ddo_ledger_v0.jsonl"
    AppendOnlyDdoLedgerV0(path).append(_decision())

    truncated = tmp_path / "truncated.jsonl"
    truncated.write_text(path.read_text(encoding="utf-8")[:-1], encoding="utf-8")
    with pytest.raises(DdoLedgerCorruptionError, match="LEDGER_MISSING_TRAILING_NEWLINE"):
        AppendOnlyDdoLedgerV0(truncated).verify_integrity()

    malformed = tmp_path / "malformed.jsonl"
    malformed.write_text("{not json\n", encoding="utf-8")
    with pytest.raises(DdoMalformedRecordError):
        AppendOnlyDdoLedgerV0(malformed).verify_integrity()

    hashed = tmp_path / "hash.jsonl"
    AppendOnlyDdoLedgerV0(hashed).append(_decision())
    raw = json.loads(hashed.read_text(encoding="utf-8"))
    raw["payload"]["decision_type"] = "KILL_SWITCH"
    hashed.write_text(canonical_json_dumps_v0(raw) + "\n", encoding="utf-8")
    with pytest.raises((DdoIntegrityError, DdoLedgerCorruptionError)):
        AppendOnlyDdoLedgerV0(hashed).verify_integrity()

    chained = tmp_path / "chain.jsonl"
    AppendOnlyDdoLedgerV0(chained).append(_decision())
    raw = json.loads(chained.read_text(encoding="utf-8"))
    raw["prev_ledger_hash"] = "TAMPERED"
    chained.write_text(canonical_json_dumps_v0(raw) + "\n", encoding="utf-8")
    with pytest.raises(DdoLedgerCorruptionError, match="LEDGER_CHAIN_BREAK"):
        AppendOnlyDdoLedgerV0(chained).verify_integrity()


def test_unsupported_schema_rejected(tmp_path: Path) -> None:
    ledger = AppendOnlyDdoLedgerV0(tmp_path / "ddo_ledger_v0.jsonl")
    with pytest.raises(DdoUnsupportedSchemaVersionError):
        ledger.append(_decision(schema_version="decision_event_v99"))


def test_decorator_plus_cycle_does_not_double_persist(tmp_path: Path) -> None:
    path = tmp_path / "ddo_ledger_v0.jsonl"
    binding = DdoCaptureBindingV0(enabled=True, ledger_path=path)
    first = _observe(binding)
    second = _observe(binding)
    assert first["record_id"] == second["record_id"]
    loaded = AppendOnlyDdoLedgerV0(path).read_all()
    assert [row["record_id"] for row in loaded] == [first["record_id"]]
    assert binding.persisted_ids.count(first["record_id"]) == 1


def test_typed_double_play_producer_capture_with_ledger(tmp_path: Path) -> None:
    path = tmp_path / "ddo_ledger_v0.jsonl"
    binding = DdoCaptureBindingV0(enabled=True, ledger_path=path)
    decision = _enter_long()
    summary = observe_producer_result_v0(
        binding,
        seam_id=SEAM_DOUBLE_PLAY_ENTRY_EXIT,
        result=decision,
        event_time_utc="2026-09-06T12:00:00Z",
        correlation_id="ddo.corr.dp.harden",
        cycle_id="cycle:dp:harden:0001",
    )
    assert summary["durable_ok"] is True
    loaded = AppendOnlyDdoLedgerV0(path).read_all()
    schemas = [row["schema_name"] for row in loaded]
    assert "decision_event" in schemas
    assert "double_play_entry_exit_observation" in schemas
    again = observe_producer_result_v0(
        binding,
        seam_id=SEAM_DOUBLE_PLAY_ENTRY_EXIT,
        result=decision,
        event_time_utc="2026-09-06T12:00:00Z",
        correlation_id="ddo.corr.dp.harden",
        cycle_id="cycle:dp:harden:0001",
    )
    assert again["durable_ok"] is True
    assert len(AppendOnlyDdoLedgerV0(path).read_all()) == len(loaded)


def test_host_result_unchanged_on_success_and_default_writes_no_file() -> None:
    mids = [3500.0, 3510.0]
    state_a, cycles_a = run_bridge_cycles_from_mids_v1(
        mids, session_id="ddo-harden-a", require_selection_binding=False
    )
    state_b, cycles_b = run_bridge_cycles_from_mids_v1(
        mids, session_id="ddo-harden-a", require_selection_binding=False
    )
    assert [item.to_dict() for item in cycles_a] == [item.to_dict() for item in cycles_b]
    assert state_a.ddo_capture_binding.ledger_path is None
    assert state_a.ddo_durable_evidence_runtime_state_root is None
    assert state_a.ddo_evidence_environment is None
    assert state_a.ddo_evidence_account_scope is None
    assert state_a.ddo_evidence_environment_binding_status == "UNBOUND"
    assert state_a.ddo_evidence_account_binding_status == "UNBOUND"
    assert state_a.last_ddo_capture is not None
    assert state_a.last_ddo_capture["decision_unchanged"] is True
    assert state_a.last_ddo_capture["ledger_bound"] is False
    assert not (Path.cwd() / "ddo_ledger_v0.jsonl").exists()
    assert state_b.ddo_capture_binding.persisted_ids == []


def test_host_result_unchanged_on_durable_failure(tmp_path: Path, monkeypatch: Any) -> None:
    def boom(self: AppendOnlyDdoLedgerV0, line: str) -> None:
        raise OSError(errno.EACCES, "Permission denied")

    monkeypatch.setattr(AppendOnlyDdoLedgerV0, "_append_line", boom)
    baseline_state, baseline_cycles = run_bridge_cycles_from_mids_v1(
        [3500.0], session_id="ddo-harden-fail", require_selection_binding=False
    )
    state = BridgeSessionStateV1(require_selection_binding=False)
    state.ddo_capture_binding = DdoCaptureBindingV0(
        enabled=True, ledger_path=tmp_path / "ddo_ledger_v0.jsonl"
    )
    cycle = run_bridge_cycle_v1(
        state,
        mid_price=3500.0,
        event_ts_unix=1_700_000_000.0,
        session_id="ddo-harden-fail",
    )
    assert cycle.to_dict() == baseline_cycles[0].to_dict()
    assert state.last_ddo_capture is not None
    assert state.last_ddo_capture["decision_unchanged"] is True
    assert state.last_ddo_capture["durable_ok"] is False
    assert state.last_ddo_capture["failure_class"] == FAILURE_CLASS_PERMISSION_ACCESS
    assert state.last_ddo_capture["durability"]["success"] is False
    assert state.ddo_capture_binding.persisted_ids == []
    assert list(tmp_path.glob("*.jsonl")) == []
    _ = baseline_state


def test_path_resolver_rejects_missing_and_is_deterministic(tmp_path: Path) -> None:
    with pytest.raises(DdoPathResolutionError, match="RUNTIME_STATE_ROOT_REQUIRED"):
        resolve_ddo_durable_evidence_path_v1(
            runtime_state_root="",
            environment="dev",
            account_scope="acct-uid-demo",
            system_scope=DDO_EVIDENCE_SYSTEM_SCOPE_TOKEN,
        )
    with pytest.raises(DdoPathResolutionError, match="RUNTIME_STATE_ROOT_MUST_BE_ABSOLUTE"):
        resolve_ddo_durable_evidence_path_v1(
            runtime_state_root="relative/root",
            environment="dev",
            account_scope="acct-uid-demo",
            system_scope=DDO_EVIDENCE_SYSTEM_SCOPE_TOKEN,
        )
    with pytest.raises(DdoPathResolutionError, match="ENVIRONMENT_SCOPE_REQUIRED"):
        resolve_ddo_durable_evidence_path_v1(
            runtime_state_root=tmp_path,
            environment="",
            account_scope="acct-uid-demo",
            system_scope=DDO_EVIDENCE_SYSTEM_SCOPE_TOKEN,
        )
    with pytest.raises(DdoPathResolutionError, match="ENVIRONMENT_SCOPE_UNKNOWN"):
        resolve_ddo_durable_evidence_path_v1(
            runtime_state_root=tmp_path,
            environment="paper",
            account_scope="acct-uid-demo",
            system_scope=DDO_EVIDENCE_SYSTEM_SCOPE_TOKEN,
        )
    with pytest.raises(DdoPathResolutionError, match="ACCOUNT_SCOPE_REQUIRED"):
        resolve_ddo_durable_evidence_path_v1(
            runtime_state_root=tmp_path,
            environment="dev",
            account_scope="",
            system_scope=DDO_EVIDENCE_SYSTEM_SCOPE_TOKEN,
        )
    with pytest.raises(DdoPathResolutionError, match="SYSTEM_SCOPE_INVALID"):
        resolve_ddo_durable_evidence_path_v1(
            runtime_state_root=tmp_path,
            environment="dev",
            account_scope="acct-uid-demo",
            system_scope="research_strategy",
        )
    first = resolve_ddo_durable_evidence_path_v1(
        runtime_state_root=tmp_path,
        environment="dev",
        account_scope="acct-uid-demo",
        system_scope=DDO_EVIDENCE_SYSTEM_SCOPE_TOKEN,
    )
    second = resolve_ddo_durable_evidence_path_v1(
        runtime_state_root=tmp_path,
        environment="dev",
        account_scope="acct-uid-demo",
        system_scope=DDO_EVIDENCE_SYSTEM_SCOPE_TOKEN,
    )
    assert first == second
    assert first == (
        tmp_path
        / "ddo"
        / "dev"
        / "acct-uid-demo"
        / "canonical_trading_path"
        / LEDGER_FILENAME_DEFAULT
    )
    assert first.is_absolute()
    assert LOGICAL_CONFIG_KEY_DDO_DURABLE_EVIDENCE_RUNTIME_STATE_ROOT == (
        "ddo.durable_evidence.runtime_state_root"
    )
    assert DDO_EVIDENCE_ENVIRONMENT_TOKENS == {item.value for item in ExecutionEnvironment}
    assert DDO_EVIDENCE_ENVIRONMENT_OWNER == "EXISTING_GOVERNANCE_EXECUTION_ENVIRONMENT"
    assert DDO_EVIDENCE_ACCOUNT_OWNER == "EXISTING_CAPABILITY_11_2_ACCOUNT_IDENTITY_BOUNDARY"
    assert ACCOUNT_IDENTITY_BOUNDARY_OWNER.endswith("account_identity_boundary_v1")


def test_multi_writer_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "ddo_ledger_v0.jsonl"
    ledger = AppendOnlyDdoLedgerV0(path)
    ledger.append(_decision())
    lock_path = ledger.writer_lock_path()
    fd = os.open(str(lock_path), os.O_RDWR)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        other = AppendOnlyDdoLedgerV0(path)
        with pytest.raises(DdoConcurrentWriterError) as caught:
            other.append(_decision(record_id="dec-0002", event_id="evt-0002"))
        assert caught.value.failure_class == FAILURE_CLASS_CONCURRENT_WRITER
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)
    AppendOnlyDdoLedgerV0(path).append(_decision(record_id="dec-0002", event_id="evt-0002"))
    assert len(AppendOnlyDdoLedgerV0(path).read_all()) == 2


def test_no_trading_execution_authority_collision() -> None:
    hits: list[str] = []
    for path in (
        CAPTURE_PATH,
        PACKAGE_DIR / "ledger_v0.py",
        PATH_MODULE,
        PACKAGE_DIR / "errors_v0.py",
    ):
        hits.extend(_import_hits(path))
    assert hits == []
    host = HOST_PATH.read_text(encoding="utf-8")
    assert "resolve_ddo_durable_evidence_path_v1(" not in host
    assert "ledger_path=resolver" not in host
    assert (
        "ddo_capture_binding: DdoCaptureBindingV0 = field(default_factory=DdoCaptureBindingV0)"
        in host
    )
    assert AUTHORITY_OWNER == "NONE"
    assert LEARNING_PRODUCTIVE_AUTHORITY == "NONE"
    assert SECOND_TRADING_AUTHORITY_CREATED is False
    assert SECOND_EXECUTION_AUTHORITY_CREATED is False
    capture = CAPTURE_PATH.read_text(encoding="utf-8")
    persist_fn = capture[capture.index("def _persist(") :]
    persist_fn = persist_fn[: persist_fn.index("\ndef _view(")]
    assert persist_fn.index("binding.persisted_ids.append(record_id)") > persist_fn.index(
        "ledger.append(frozen)"
    )
    assert "if record_id in binding.persisted_ids" in persist_fn


def test_capture_failure_does_not_change_cycle_decision(tmp_path: Path, monkeypatch: Any) -> None:
    def boom(*_args: Any, **_kwargs: Any) -> None:
        raise DdoDurabilityWriteError(
            FAILURE_CLASS_CORRUPTION_UNREADABLE,
            "CORRUPTION_PREEXISTING_UNREADABLE_LEDGER",
            retryable=False,
        )

    monkeypatch.setattr(
        "src.learning.deterministic_decision_outcome_v0.capture_v0._persist",
        boom,
    )
    binding = DdoCaptureBindingV0(enabled=True, ledger_path=tmp_path / "ddo.jsonl")
    summary = record_productive_cycle_capture_v0(
        binding,
        repository_sha="OFFLINE_DETERMINISTIC_EVIDENCE",
        session_id="ddo-harden-cycle",
        cycle_index=1,
        event_ts_unix=1_700_000_000.0,
        features={"ok": True},
    )
    assert summary["decision_unchanged"] is True
    assert summary["capture_failure_changes_current_decision"] is False
    assert summary["ok"] is False or summary.get("durable_ok") is False
