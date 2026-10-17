"""WP-B5 kill-switch safety & recovery closure (offline, isolated temp roots).

Covers F1–F6 and the RECOVERING → ACTIVE entry: fail-closed approval, bound
recovery requests, cooldown/timestamp integrity, inter-process kill priority,
durable journal, DISABLED / PEAK_KILL_SWITCH semantics and ACTIVE provenance.
ACTIVE here only means "kill-switch recovery completed"; no test arms, signs,
opens a socket or performs a venue POST.
"""

from __future__ import annotations

import dataclasses
import hashlib
import io
import json
import logging
import os
import socket
import subprocess
import sys
import threading
import time
from argparse import Namespace
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1 import constants_v1
from src.ops.full_core_live_path_composition_root_v1.current_full_core_capital_guard_v1 import (
    load_full_core_capital_guard_config_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_global_venue_effect_authority_ledger_v1 import (
    GlobalVenueEffectReplayDeniedError,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_mandatory_new_risk_enter_post_admission_v1 import (
    MandatoryNewRiskEnterPostAdmissionError,
    resolve_mandatory_new_risk_enter_post_admission_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1 import (
    CurrentProductiveOneShotFreshEnvelopeJoinError,
    attempt_current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_pilot_capital_guard_post_bind_v1 import (
    OWNER_GO_CURRENT_PILOT_CAPITAL_GUARD_POST_BIND_V1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_post_path_kill_switch_gate_v1 import (
    DENY_ACTIVE_ATTESTATION_NOT_VERIFIED,
    DENY_EMERGENCY_ENV,
    PostPathKillSwitchDecisionV1,
    PostPathKillSwitchGateError,
    assert_post_path_kill_switch_admits_v1,
    evaluate_post_path_kill_switch_v1,
    read_post_path_kill_switch_evidence_v1,
)
from src.ops.gates import risk_gate
from src.ops.gates.risk_gate import kill_switch_should_block_trading
from src.risk_layer.kill_switch import cli
from src.risk_layer.kill_switch.core import (
    DENY_AUTHORITY_MISSING,
    DENY_BINDING_MISSING,
    DENY_CODE_INVALID,
    DENY_CODE_MISSING,
    DENY_COOLDOWN_ACTIVE,
    DENY_EXPECTED_CODE_UNAVAILABLE,
    DENY_JOURNAL_UNAVAILABLE,
    DENY_KILL_PRIORITY,
    DENY_LOCK_TIMEOUT,
    DENY_NOT_RECOVERING,
    DENY_REQUEST_ID_MISMATCH,
    DENY_TIMESTAMP_FUTURE,
    DENY_TIMESTAMP_INVALID,
    DENY_TIMESTAMP_MISSING,
    KillSwitch,
    KillSwitchKillFailedError,
    KillSwitchKillPendingError,
)
from src.risk_layer.kill_switch.persistence import StatePersistence
from src.risk_layer.kill_switch.recovery_attestation import (
    DEFAULT_APPROVAL_CODE_ENV,
    KIND_KILL,
    KIND_RECOVERY_COMPLETED,
    KIND_RECOVERY_REQUESTED,
    JournalError,
    TransitionJournal,
    derive_attestation_key,
    journal_path_for_state_file,
    sign_fields,
    active_record_fields,
)
from src.risk_layer.kill_switch.state import KillSwitchState
from tests.ops._post_path_safety_fixtures_v1 import (
    TEST_APPROVAL_CODE,
    TEST_APPROVER,
    claim_for_join_v1,
    isolate_kill_switch_state_root_v1,
    isolated_global_ledger_v1,
    risk_reduction_proof_for_envelope_v1,
    write_unattested_kill_switch_state_v1,
)
from tests.ops.test_current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1 import (
    _new_risk_envelope,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
_PRODUCTIVE_STATE_PATH = Path(risk_gate.canonical_kill_switch_state_path())
_PRODUCTIVE_JOURNAL_PATH = journal_path_for_state_file(_PRODUCTIVE_STATE_PATH)


def _fingerprint(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


_PRODUCTIVE_FINGERPRINTS = (
    _fingerprint(_PRODUCTIVE_STATE_PATH),
    _fingerprint(_PRODUCTIVE_JOURNAL_PATH),
)


class _SocketOpened(AssertionError):
    pass


@pytest.fixture(autouse=True)
def _offline(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Any socket connect in this module is a hard failure and is counted."""
    opened: list[str] = []

    def _refuse(*args, **kwargs):  # noqa: ANN002, ANN003, ANN202
        opened.append(repr(args[:2]))
        raise _SocketOpened("socket open attempted in an offline kill-switch test")

    monkeypatch.setattr(socket.socket, "connect", _refuse)
    monkeypatch.setattr(socket.socket, "connect_ex", _refuse)
    monkeypatch.setattr(socket, "create_connection", _refuse)
    return opened


@pytest.fixture
def state_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.delenv("PEAK_KILL_SWITCH", raising=False)
    monkeypatch.setenv(DEFAULT_APPROVAL_CODE_ENV, TEST_APPROVAL_CODE)
    path = isolate_kill_switch_state_root_v1(monkeypatch, tmp_path / "root")
    assert path != _PRODUCTIVE_STATE_PATH
    return path


def _ks(**config) -> KillSwitch:  # noqa: ANN003
    merged = {"persist_state": True, "recovery_cooldown_seconds": 0, **config}
    return KillSwitch(merged)


def _raw(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_raw(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def _journal(path: Path) -> list[dict]:
    return TransitionJournal(journal_path_for_state_file(path)).read_events()


def _to_recovering(ks: KillSwitch) -> str:
    ks.trigger("wp_b5_test", triggered_by="test")
    assert ks.request_recovery(TEST_APPROVER, TEST_APPROVAL_CODE) is True, ks.last_denial_reason
    request_id = ks.pending_request_id
    assert request_id
    return request_id


def _to_active(ks: KillSwitch) -> str:
    request_id = _to_recovering(ks)
    assert ks.complete_recovery(TEST_APPROVER, TEST_APPROVAL_CODE, request_id=request_id) is True, (
        ks.last_denial_reason
    )
    return request_id


def _post_decision(**read_kwargs) -> tuple[PostPathKillSwitchDecisionV1, tuple[str, ...]]:  # noqa: ANN003
    evidence = read_post_path_kill_switch_evidence_v1(**read_kwargs)
    admission = evaluate_post_path_kill_switch_v1(
        evidence=evidence, envelope=_new_risk_envelope(), risk_reduction_proof=None
    )
    return admission.decision, admission.reason_codes


def _assert_everyone_denies(path: Path) -> None:
    assert kill_switch_should_block_trading(explicit_active=False) is True
    decision, _ = _post_decision()
    assert decision is PostPathKillSwitchDecisionV1.DENY
    assert _ks().state is not KillSwitchState.ACTIVE


# --------------------------------------------------------------------- 1 valid


def test_01_valid_recovery_reaches_attested_active_only(state_path: Path) -> None:
    ks = _ks()
    request_id = _to_active(ks)
    raw = _raw(state_path)
    assert raw["state"] == "ACTIVE"
    assert raw["recovery"]["request_id"] == request_id
    kinds = [e["kind"] for e in _journal(state_path)]
    assert kinds[-3:] == [KIND_KILL, KIND_RECOVERY_REQUESTED, KIND_RECOVERY_COMPLETED]
    assert kill_switch_should_block_trading(explicit_active=False) is False
    decision, reasons = _post_decision()
    assert decision is PostPathKillSwitchDecisionV1.ALLOW, reasons
    assert _ks().state is KillSwitchState.ACTIVE


# ------------------------------------------------------- 2–4 authorization (F1)


def test_02_missing_code_denies(state_path: Path) -> None:
    ks = _ks()
    ks.trigger("t")
    assert ks.request_recovery(TEST_APPROVER) is False
    assert ks.last_denial_reason == DENY_CODE_MISSING
    assert ks.request_recovery(TEST_APPROVER, "   ") is False
    assert ks.last_denial_reason == DENY_CODE_MISSING
    assert _raw(state_path)["state"] == "KILLED"

    request_id = _to_recovering(ks)
    assert ks.complete_recovery(TEST_APPROVER, None, request_id=request_id) is False
    assert ks.last_denial_reason == DENY_CODE_MISSING
    assert ks.complete_recovery(None, TEST_APPROVAL_CODE, request_id=request_id) is False
    assert ks.last_denial_reason == DENY_AUTHORITY_MISSING
    assert _raw(state_path)["state"] == "RECOVERING"


def test_03_wrong_code_denies(state_path: Path) -> None:
    ks = _ks()
    ks.trigger("t")
    assert ks.request_recovery(TEST_APPROVER, TEST_APPROVAL_CODE + "x") is False
    assert ks.last_denial_reason == DENY_CODE_INVALID
    request_id = _to_recovering(ks)
    assert ks.complete_recovery(TEST_APPROVER, "wrong", request_id=request_id) is False
    assert ks.last_denial_reason == DENY_CODE_INVALID
    assert _raw(state_path)["state"] == "RECOVERING"


def test_04_missing_expected_authorization_denies_and_config_cannot_supply_it(
    state_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ks = _ks(require_approval_code=False, approval_code="config-code")
    ks.trigger("t")
    monkeypatch.delenv(DEFAULT_APPROVAL_CODE_ENV)
    for code in (None, "", "config-code", TEST_APPROVAL_CODE):
        assert ks.request_recovery(TEST_APPROVER, code) is False
        assert ks.last_denial_reason == DENY_EXPECTED_CODE_UNAVAILABLE
    monkeypatch.setenv(DEFAULT_APPROVAL_CODE_ENV, "   ")
    assert ks.request_recovery(TEST_APPROVER, "   ") is False
    assert ks.last_denial_reason == DENY_EXPECTED_CODE_UNAVAILABLE
    assert _raw(state_path)["state"] == "KILLED"


def test_04b_in_memory_validation_is_fail_closed_without_expected_code(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(DEFAULT_APPROVAL_CODE_ENV, raising=False)
    ks = KillSwitch({"persist_state": False, "require_approval_code": True})
    ks.trigger("t")
    assert ks.request_recovery(TEST_APPROVER, "anything") is False
    assert ks._validate_approval_code("anything") is False
    assert ks._validate_approval_code("") is False


# --------------------------------------------------- 5–8 cooldown / timestamps (F2)


def test_05_cooldown_not_expired_denies(state_path: Path) -> None:
    ks = _ks(recovery_cooldown_seconds=3600)
    request_id = _to_recovering(ks)
    assert ks.complete_recovery(TEST_APPROVER, TEST_APPROVAL_CODE, request_id=request_id) is False
    assert ks.last_denial_reason == DENY_COOLDOWN_ACTIVE
    # A lower cooldown in a restarted instance cannot shorten the bound cooldown.
    restarted = _ks(recovery_cooldown_seconds=0)
    assert (
        restarted.complete_recovery(TEST_APPROVER, TEST_APPROVAL_CODE, request_id=request_id)
        is False
    )
    assert restarted.last_denial_reason == DENY_COOLDOWN_ACTIVE
    assert _raw(state_path)["state"] == "RECOVERING"


def _tamper_recovery_timestamp(path: Path, value) -> None:  # noqa: ANN001
    raw = _raw(path)
    for target in (raw, raw["recovery"]):
        if value is None:
            target.pop("recovery_started_at", None)
        else:
            target["recovery_started_at"] = value
    _write_raw(path, raw)


@pytest.mark.parametrize(
    "value,expected_prefixes",
    [
        (None, (DENY_BINDING_MISSING,)),
        ("not-a-timestamp", (DENY_TIMESTAMP_INVALID,)),
        ("2026-01-01T00:00:00+00:00", (DENY_TIMESTAMP_INVALID,)),
    ],
    ids=["06_missing", "07_corrupt", "07b_tz_aware"],
)
def test_06_07_missing_or_corrupt_timestamp_denies(
    state_path: Path,
    value,
    expected_prefixes,  # noqa: ANN001
) -> None:
    ks = _ks()
    request_id = _to_recovering(ks)
    _tamper_recovery_timestamp(state_path, value)
    assert ks.complete_recovery(TEST_APPROVER, TEST_APPROVAL_CODE, request_id=request_id) is False
    assert ks.last_denial_reason in expected_prefixes, ks.last_denial_reason
    assert _raw(state_path)["state"] == "RECOVERING"
    _assert_everyone_denies(state_path)


def test_06b_missing_timestamp_unit_denies() -> None:
    ks = KillSwitch({"persist_state": False, "recovery_cooldown_seconds": 0})
    assert ks._cooldown_denial(None, None) == DENY_TIMESTAMP_MISSING
    assert ks._cooldown_denial("", None) == DENY_TIMESTAMP_MISSING


def test_08_future_timestamp_denies(state_path: Path) -> None:
    ks = _ks()
    request_id = _to_recovering(ks)
    _tamper_recovery_timestamp(state_path, (datetime.utcnow() + timedelta(hours=1)).isoformat())
    assert ks.complete_recovery(TEST_APPROVER, TEST_APPROVAL_CODE, request_id=request_id) is False
    assert ks.last_denial_reason == DENY_TIMESTAMP_FUTURE
    _assert_everyone_denies(state_path)


def test_08b_tampered_timestamp_with_valid_format_breaks_journal_binding(state_path: Path) -> None:
    ks = _ks()
    request_id = _to_recovering(ks)
    _tamper_recovery_timestamp(state_path, (datetime.utcnow() - timedelta(days=1)).isoformat())
    assert ks.complete_recovery(TEST_APPROVER, TEST_APPROVAL_CODE, request_id=request_id) is False
    assert str(ks.last_denial_reason).startswith(DENY_KILL_PRIORITY)
    _assert_everyone_denies(state_path)


# ------------------------------------------------------------- 9–10 replay (F6)


def test_09_replay_of_old_request_denies(state_path: Path) -> None:
    ks = _ks()
    old_request = _to_active(ks)
    new_request = _to_recovering(ks)
    assert new_request != old_request
    assert ks.complete_recovery(TEST_APPROVER, TEST_APPROVAL_CODE, request_id=old_request) is False
    assert ks.last_denial_reason == DENY_REQUEST_ID_MISMATCH
    assert ks.complete_recovery(TEST_APPROVER, TEST_APPROVAL_CODE, request_id=None) is False

    # Re-appending an old signed REQUESTED line makes the journal fail closed.
    journal = journal_path_for_state_file(state_path)
    lines = journal.read_text(encoding="utf-8").splitlines(keepends=True)
    old_line = next(
        line
        for line in lines
        if json.loads(line).get("kind") == KIND_RECOVERY_REQUESTED
        and json.loads(line).get("request_id") == old_request
    )
    with journal.open("a", encoding="utf-8") as handle:
        handle.write(old_line)
    assert ks.complete_recovery(TEST_APPROVER, TEST_APPROVAL_CODE, request_id=new_request) is False
    assert str(ks.last_denial_reason).startswith(DENY_JOURNAL_UNAVAILABLE)
    _assert_everyone_denies(state_path)


def test_10_replay_of_old_active_file_denies(state_path: Path) -> None:
    ks = _ks()
    _to_active(ks)
    old_active = state_path.read_bytes()
    ks.trigger("after_active")
    assert _raw(state_path)["state"] == "KILLED"
    state_path.write_bytes(old_active)
    assert _raw(state_path)["state"] == "ACTIVE"
    _assert_everyone_denies(state_path)

    # Same file copied to another root (other journal) is not valid there either.
    other = state_path.parent.parent / "other_root" / "state.json"
    other.parent.mkdir(parents=True)
    other.write_bytes(old_active)
    decision, reasons = _post_decision(state_path=other)
    assert decision is PostPathKillSwitchDecisionV1.DENY, reasons


# -------------------------------------------------------- 11–13 concurrency (F3)

_CHILD = r"""
import json, os, sys, time
from pathlib import Path
from src.risk_layer.kill_switch.core import KillSwitch
from src.risk_layer.kill_switch.persistence import StatePersistence
mode, path, go = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])
extra = sys.argv[4] if len(sys.argv) > 4 else ""
code = sys.stdin.readline().rstrip("\n")
if mode.startswith("crash_on_"):
    target = mode[len("crash_on_"):]
    original = StatePersistence.save
    def _crash(self, state, **kw):
        if state.name == target:
            os._exit(137)
        return original(self, state, **kw)
    StatePersistence.save = _crash
ks = KillSwitch(
    {"persist_state": True, "recovery_cooldown_seconds": 0, "state_lock_timeout_seconds": 20},
    persistence=StatePersistence(str(path), backup_dir=str(path.parent / "backups")),
)
deadline = time.time() + 30
while not go.exists() and time.time() < deadline:
    time.sleep(0.002)
if mode in ("complete", "crash_on_ACTIVE"):
    ok = ks.complete_recovery("child", code, request_id=extra)
elif mode in ("request", "crash_on_RECOVERING"):
    ok = ks.request_recovery("child", code)
else:
    ok = ks.trigger("child_kill", triggered_by="child")
print(json.dumps({"ok": ok, "reason": ks.last_denial_reason}))
"""


def _spawn(mode: str, path: Path, go: Path, extra: str = "") -> subprocess.Popen:
    proc = subprocess.Popen(
        [sys.executable, "-c", _CHILD, mode, str(path), str(go), extra],
        cwd=str(REPO_ROOT),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env={k: v for k, v in os.environ.items() if k != "PEAK_KILL_SWITCH"},
    )
    assert proc.stdin is not None
    proc.stdin.write(TEST_APPROVAL_CODE + "\n")
    proc.stdin.close()
    return proc


def _result(proc: subprocess.Popen) -> dict:
    assert proc.stdout is not None and proc.stderr is not None
    out, err = proc.stdout.read(), proc.stderr.read()
    assert proc.wait(timeout=60) == 0, err
    return json.loads(out.strip().splitlines()[-1])


def test_11_two_concurrent_completers_exactly_one_wins(state_path: Path, tmp_path: Path) -> None:
    ks = _ks()
    request_id = _to_recovering(ks)
    go = tmp_path / "go"
    procs = [_spawn("complete", state_path, go, request_id) for _ in range(2)]
    time.sleep(0.5)
    go.touch()
    results = [_result(p) for p in procs]
    assert sorted(r["ok"] for r in results) == [False, True], results
    loser = next(r for r in results if r["ok"] is False)
    assert loser["reason"] == DENY_NOT_RECOVERING
    completions = [e for e in _journal(state_path) if e["kind"] == KIND_RECOVERY_COMPLETED]
    assert len(completions) == 1
    decision, reasons = _post_decision()
    assert decision is PostPathKillSwitchDecisionV1.ALLOW, reasons


@pytest.mark.parametrize("stage", ["before_completion_journal", "before_active_write"])
def test_12_trigger_racing_completer_always_wins(
    state_path: Path, monkeypatch: pytest.MonkeyPatch, stage: str
) -> None:
    ks = _ks()
    request_id = _to_recovering(ks)
    journal = TransitionJournal(journal_path_for_state_file(state_path))
    threads: list[threading.Thread] = []
    errors: list[BaseException] = []

    def _concurrent_kill() -> None:
        killer = _ks(state_lock_timeout_seconds=20)

        def _run() -> None:
            try:
                killer.trigger("concurrent_kill", triggered_by="other_process")
            except BaseException as exc:  # pragma: no cover - surfaced below
                errors.append(exc)

        thread = threading.Thread(target=_run)
        thread.start()
        threads.append(thread)
        deadline = time.time() + 10
        while time.time() < deadline:
            try:
                events = journal.read_events()
            except JournalError:
                events = []
            if any(
                e["kind"] == KIND_KILL and e.get("triggered_by") == "other_process" for e in events
            ):
                return
            time.sleep(0.005)
        raise AssertionError("concurrent KILL was not journaled lock-free")

    if stage == "before_completion_journal":
        original_append = ks._journal.append

        def _append(record):  # noqa: ANN001, ANN202
            if record.get("kind") == KIND_RECOVERY_COMPLETED and not threads:
                _concurrent_kill()
            return original_append(record)

        monkeypatch.setattr(ks._journal, "append", _append)
    else:
        original_save = ks._persistence.save

        def _save(state, **kwargs):  # noqa: ANN001, ANN003, ANN202
            if state is KillSwitchState.ACTIVE and not threads:
                _concurrent_kill()
            return original_save(state, **kwargs)

        monkeypatch.setattr(ks._persistence, "save", _save)

    assert ks.complete_recovery(TEST_APPROVER, TEST_APPROVAL_CODE, request_id=request_id) is False
    assert str(ks.last_denial_reason).startswith(DENY_KILL_PRIORITY), ks.last_denial_reason
    for thread in threads:
        thread.join(30)
    assert errors == []
    assert _raw(state_path)["state"] == "KILLED"
    _assert_everyone_denies(state_path)


def test_13_trigger_on_lock_timeout_is_never_bypassed(
    state_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ks = _ks(state_lock_timeout_seconds=0.2)
    _to_active(ks)
    holder = StatePersistence(str(state_path))
    with holder.exclusive_lock(1.0):
        with pytest.raises(KillSwitchKillPendingError):
            ks.trigger("kill_while_locked")
        # ACTIVE bytes are still on disk, but the journaled KILL supersedes them.
        assert _raw(state_path)["state"] == "ACTIVE"
        assert ks.state is KillSwitchState.KILLED
        _assert_everyone_denies(state_path)
        # A completer under the same lock contention is denied, never ACTIVE.
        assert ks.complete_recovery(TEST_APPROVER, TEST_APPROVAL_CODE, request_id="x") is False
        assert ks.last_denial_reason == DENY_LOCK_TIMEOUT

        def _broken_append(record):  # noqa: ANN001, ANN202
            raise OSError("journal unavailable")

        original_append = ks._journal.append
        monkeypatch.setattr(ks._journal, "append", _broken_append)
        with pytest.raises(KillSwitchKillFailedError):
            ks.trigger("kill_without_journal_while_locked")
        monkeypatch.setattr(ks._journal, "append", original_append)
    assert ks.trigger("kill_after_lock_release") is True
    assert _raw(state_path)["state"] == "KILLED"
    _assert_everyone_denies(state_path)


def test_13b_kill_without_journal_still_persists_killed(
    state_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ks = _ks()
    _to_active(ks)

    def _broken_append(record):  # noqa: ANN001, ANN202
        raise OSError("journal unavailable")

    monkeypatch.setattr(ks._journal, "append", _broken_append)
    assert ks.trigger("kill_journal_down") is True
    assert _raw(state_path)["state"] == "KILLED"


# ---------------------------------------------------------- 14–15 crash (F4)


def test_14_crash_during_recovery_request_leaves_killed(state_path: Path, tmp_path: Path) -> None:
    ks = _ks()
    ks.trigger("t")
    go = tmp_path / "go"
    go.touch()
    proc = _spawn("crash_on_RECOVERING", state_path, go)
    assert proc.wait(timeout=60) == 137
    assert _raw(state_path)["state"] == "KILLED"
    assert [e["kind"] for e in _journal(state_path)][-1] == KIND_RECOVERY_REQUESTED
    _assert_everyone_denies(state_path)
    # Orphaned request cannot be completed; a fresh authorized request works.
    restarted = _ks()
    assert restarted.state is KillSwitchState.KILLED
    _to_active(restarted)


def test_15_crash_between_audit_and_state_never_yields_active(
    state_path: Path, tmp_path: Path
) -> None:
    ks = _ks()
    request_id = _to_recovering(ks)
    go = tmp_path / "go"
    go.touch()
    proc = _spawn("crash_on_ACTIVE", state_path, go, request_id)
    assert proc.wait(timeout=60) == 137
    assert _raw(state_path)["state"] == "RECOVERING"
    assert [e["kind"] for e in _journal(state_path)][-1] == KIND_RECOVERY_COMPLETED
    _assert_everyone_denies(state_path)
    restarted = _ks()
    assert (
        restarted.complete_recovery(TEST_APPROVER, TEST_APPROVAL_CODE, request_id=request_id)
        is False
    )
    assert str(restarted.last_denial_reason).startswith(DENY_KILL_PRIORITY)
    # Exit path: trigger, then a new authorized recovery.
    _to_active(restarted)


def test_15b_corrupt_journal_denies_active_everywhere(state_path: Path) -> None:
    ks = _ks()
    _to_active(ks)
    journal = journal_path_for_state_file(state_path)
    with journal.open("a", encoding="utf-8") as handle:
        handle.write('{"torn": ')
    _assert_everyone_denies(state_path)


# ---------------------------------------------------- 16–17 DISABLED / env (F5)


def test_16_disabled_never_neutralizes_a_kill(
    state_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    write_unattested_kill_switch_state_v1(state_path, state="DISABLED")
    assert kill_switch_should_block_trading(explicit_active=False) is True
    assert _post_decision()[0] is PostPathKillSwitchDecisionV1.DENY
    restored = _ks()
    assert restored.state is KillSwitchState.KILLED

    durable = _ks(mode="disabled")
    assert durable.state is not KillSwitchState.DISABLED
    assert durable.trigger("kill_in_disabled_mode") is True
    assert _raw(state_path)["state"] == "KILLED"

    backtest = KillSwitch({"persist_state": False, "mode": "disabled"})
    assert backtest.state is KillSwitchState.DISABLED


def test_17_peak_kill_switch_env_denies_even_with_attested_active(
    state_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _to_active(_ks())
    evidence_before_env = read_post_path_kill_switch_evidence_v1()
    monkeypatch.setenv("PEAK_KILL_SWITCH", "1")
    assert kill_switch_should_block_trading(explicit_active=False) is True
    decision, reasons = _post_decision()
    assert decision is PostPathKillSwitchDecisionV1.DENY
    assert DENY_EMERGENCY_ENV in reasons
    late = evaluate_post_path_kill_switch_v1(
        evidence=evidence_before_env, envelope=_new_risk_envelope(), risk_reduction_proof=None
    )
    assert late.decision is PostPathKillSwitchDecisionV1.DENY
    forged = dataclasses.replace(evidence_before_env, emergency_env_deny=False)
    assert (
        evaluate_post_path_kill_switch_v1(
            evidence=forged, envelope=_new_risk_envelope(), risk_reduction_proof=None
        ).decision
        is PostPathKillSwitchDecisionV1.DENY
    )


# ------------------------------------------------------- 18 manipulation (F6)


def test_18_manipulated_or_forged_active_files_deny(state_path: Path) -> None:
    _to_active(_ks())
    genuine = _raw(state_path)

    tampered = json.loads(json.dumps(genuine))
    tampered["recovery"]["completed_at"] = datetime.utcnow().isoformat()
    _write_raw(state_path, tampered)
    decision, reasons = _post_decision()
    assert decision is PostPathKillSwitchDecisionV1.DENY
    assert DENY_ACTIVE_ATTESTATION_NOT_VERIFIED in reasons

    stripped = {k: v for k, v in genuine.items() if k != "recovery"}
    _write_raw(state_path, stripped)
    assert _post_decision()[0] is PostPathKillSwitchDecisionV1.DENY
    assert kill_switch_should_block_trading(explicit_active=False) is True

    forged = json.loads(json.dumps(genuine))
    wrong_key = derive_attestation_key("attacker-guess")
    assert wrong_key is not None
    forged["recovery"]["attestation"] = sign_fields(
        wrong_key, active_record_fields(state_path, forged["recovery"])
    )
    _write_raw(state_path, forged)
    assert _post_decision()[0] is PostPathKillSwitchDecisionV1.DENY

    _write_raw(state_path, genuine)
    assert _post_decision()[0] is PostPathKillSwitchDecisionV1.ALLOW


def test_18b_schema_valid_active_without_any_journal_is_not_post_admissible(
    state_path: Path,
) -> None:
    write_unattested_kill_switch_state_v1(state_path, state="ACTIVE")
    decision, reasons = _post_decision()
    assert decision is PostPathKillSwitchDecisionV1.DENY
    assert DENY_ACTIVE_ATTESTATION_NOT_VERIFIED in reasons


def test_18d_secret_free_legacy_readers_scope_without_journal_is_pinned(
    state_path: Path,
) -> None:
    # Legacy (non-POST) readers have no secret; without any journal they keep the
    # pre-existing file-only semantics. The productive POST gate denies (18b).
    write_unattested_kill_switch_state_v1(state_path, state="ACTIVE")
    assert kill_switch_should_block_trading(explicit_active=False) is False
    assert _post_decision()[0] is PostPathKillSwitchDecisionV1.DENY


def test_18c_active_attestation_requires_the_secret_at_read_time(
    state_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _to_active(_ks())
    monkeypatch.delenv(DEFAULT_APPROVAL_CODE_ENV)
    decision, reasons = _post_decision()
    assert decision is PostPathKillSwitchDecisionV1.DENY
    assert "ACTIVE_ATTESTATION_KEY_UNAVAILABLE" in reasons


# ----------------------------------------------------------- 19–20 restart


def test_19_restart_with_killed_stays_killed(state_path: Path) -> None:
    _ks().trigger("before_restart")
    for _ in range(3):
        restarted = _ks()
        assert restarted.state is KillSwitchState.KILLED
        assert restarted.complete_recovery() is False
    _assert_everyone_denies(state_path)


def test_19b_missing_state_file_never_arms(state_path: Path) -> None:
    assert not state_path.exists()
    assert _ks().state is KillSwitchState.KILLED


def test_20_restart_with_recovering_never_auto_activates(state_path: Path) -> None:
    request_id = _to_recovering(_ks())
    restarted = _ks()
    assert restarted.state is KillSwitchState.RECOVERING
    assert restarted.pending_request_id == request_id
    assert restarted.complete_recovery() is False
    assert _raw(state_path)["state"] == "RECOVERING"
    _assert_everyone_denies(state_path)
    assert (
        restarted.complete_recovery(TEST_APPROVER, TEST_APPROVAL_CODE, request_id=request_id)
        is True
    )


# ---------------------------------------------------- 21–23 independence


def test_21_active_does_not_ratify_b2_owner_caps(state_path: Path, tmp_path: Path) -> None:
    _to_active(_ks())
    cfg = load_full_core_capital_guard_config_v1()
    assert cfg.owner_caps_ratified is False
    joined = dataclasses.replace(cfg, full_core_guard_join_enabled=True)
    with pytest.raises(MandatoryNewRiskEnterPostAdmissionError, match="OWNER_CAPS_UNRATIFIED"):
        resolve_mandatory_new_risk_enter_post_admission_v1(
            envelope=_new_risk_envelope(),
            store_root=tmp_path / "store",
            pilot_capital_guard_bind_go=OWNER_GO_CURRENT_PILOT_CAPITAL_GUARD_POST_BIND_V1,
            pilot_capital_guard_config=joined,
            pilot_native_instrument_id="0g-usdt-swap",
            pilot_atomic_state_dir=None,
            pilot_dw_private_get_go="",
            read_only_get_transport_present=True,
        )


def test_22_active_does_not_bypass_b6_global_replay(state_path: Path, tmp_path: Path) -> None:
    _to_active(_ks())
    ledger = isolated_global_ledger_v1(tmp_path)
    envelope = _new_risk_envelope()
    claim_for_join_v1(ledger, envelope)
    with pytest.raises(GlobalVenueEffectReplayDeniedError):
        claim_for_join_v1(ledger, envelope)


def test_23_active_does_not_replace_post_owner_go_or_standing_pins(
    state_path: Path, tmp_path: Path, _offline: list[str]
) -> None:
    _to_active(_ks())
    assert _post_decision()[0] is PostPathKillSwitchDecisionV1.ALLOW
    ledger = isolated_global_ledger_v1(tmp_path)
    envelope = _new_risk_envelope()
    claim = claim_for_join_v1(ledger, envelope)
    with pytest.raises(CurrentProductiveOneShotFreshEnvelopeJoinError, match="POST_GO_REQUIRED"):
        attempt_current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1(
            envelope=envelope,
            post_owner_go="",
            store_root=tmp_path / "store",
            k1_backend=None,
            global_authority_ledger=ledger,
            global_claim=claim,
        )
    assert constants_v1.EXTERNAL_EFFECT_AUTHORIZED is False
    assert constants_v1.POST_ALLOWED is False
    assert constants_v1.REAL_VENUE_POST_ALLOWED is False
    assert _offline == []


# ---------------------------------------------------- 24–26 effects / secrets


def test_24_no_socket_open_on_any_deny(
    state_path: Path, monkeypatch: pytest.MonkeyPatch, _offline: list[str]
) -> None:
    envelope = _new_risk_envelope()
    for prepare in (
        lambda: _ks().trigger("deny_killed"),
        lambda: _to_recovering(_ks()),
        lambda: write_unattested_kill_switch_state_v1(state_path, state="DISABLED"),
        lambda: write_unattested_kill_switch_state_v1(state_path, state="ACTIVE"),
    ):
        prepare()
        with pytest.raises(PostPathKillSwitchGateError):
            assert_post_path_kill_switch_admits_v1(envelope=envelope, risk_reduction_proof=None)
    _to_active(_ks())
    monkeypatch.setenv("PEAK_KILL_SWITCH", "1")
    with pytest.raises(PostPathKillSwitchGateError, match=DENY_EMERGENCY_ENV):
        assert_post_path_kill_switch_admits_v1(envelope=envelope, risk_reduction_proof=None)
    assert _offline == []


def test_24b_emergency_env_also_denies_risk_reduction(
    state_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from tests.ops.test_current_productive_post_path_security_remediation_b5_b5rr_b6_v1 import (
        _flatten_envelope,
    )

    _ks().trigger("rr_case")
    envelope = _flatten_envelope()
    proof = risk_reduction_proof_for_envelope_v1(envelope)
    killed = read_post_path_kill_switch_evidence_v1()
    admission = evaluate_post_path_kill_switch_v1(
        evidence=killed, envelope=envelope, risk_reduction_proof=proof
    )
    assert admission.decision is PostPathKillSwitchDecisionV1.ALLOW_PROVEN_RISK_REDUCTION_ONLY
    monkeypatch.setenv("PEAK_KILL_SWITCH", "1")
    admission = evaluate_post_path_kill_switch_v1(
        evidence=read_post_path_kill_switch_evidence_v1(),
        envelope=envelope,
        risk_reduction_proof=proof,
    )
    assert admission.decision is PostPathKillSwitchDecisionV1.DENY
    assert DENY_EMERGENCY_ENV in admission.reason_codes


def test_25_no_productive_active_file_is_created_or_changed(state_path: Path) -> None:
    _to_active(_ks())
    _ks().trigger("after")
    assert state_path.resolve() != _PRODUCTIVE_STATE_PATH
    assert (
        _fingerprint(_PRODUCTIVE_STATE_PATH),
        _fingerprint(_PRODUCTIVE_JOURNAL_PATH),
    ) == _PRODUCTIVE_FINGERPRINTS


def test_26_no_secret_in_argv_logs_state_or_journal(
    state_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    capsys: pytest.CaptureFixture[str],
) -> None:
    caplog.set_level(logging.DEBUG)
    ks = _ks()
    assert cli.cmd_trigger(Namespace(reason="cli_kill", confirm=True), ks) == cli.EXIT_OK

    monkeypatch.setattr(sys, "stdin", io.StringIO("wrong-code\n"))
    denied = cli.cmd_recover(Namespace(reason="r", approved_by=TEST_APPROVER, code_stdin=True), ks)
    assert denied == cli.EXIT_DENIED

    monkeypatch.setattr(sys, "stdin", io.StringIO(TEST_APPROVAL_CODE + "\n"))
    assert (
        cli.cmd_recover(Namespace(reason="r", approved_by=TEST_APPROVER, code_stdin=True), ks)
        == cli.EXIT_OK
    )
    request_id = ks.pending_request_id
    monkeypatch.setattr(sys, "stdin", io.StringIO(TEST_APPROVAL_CODE + "\n"))
    assert (
        cli.cmd_complete_recovery(
            Namespace(approved_by=TEST_APPROVER, request_id=request_id, code_stdin=True), ks
        )
        == cli.EXIT_OK
    )
    out = capsys.readouterr().out
    assert "NOT a live-trading" in out

    blobs = [caplog.text, out]
    for path in state_path.parent.rglob("*"):
        if path.is_file():
            blobs.append(path.read_text(encoding="utf-8", errors="replace"))
    assert all(TEST_APPROVAL_CODE not in blob for blob in blobs)

    usage = subprocess.run(
        [
            sys.executable,
            "-m",
            "src.risk_layer.kill_switch.cli",
            "recover",
            "--approved-by",
            "x",
            "--code",
            "argv-code-must-be-rejected",
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert usage.returncode == cli.EXIT_USAGE
    assert "unrecognized arguments" in usage.stderr

    ctl = (REPO_ROOT / "scripts" / "ops" / "kill_switch_ctl.sh").read_text(encoding="utf-8")
    assert "--code" not in ctl
    assert "complete-recovery" in ctl


def test_26b_cli_exit_codes_for_pending_and_failed_kill(
    state_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ks = _ks(state_lock_timeout_seconds=0.2)
    with StatePersistence(str(state_path)).exclusive_lock(1.0):
        assert (
            cli.cmd_trigger(Namespace(reason="locked", confirm=True), ks) == cli.EXIT_KILL_PENDING
        )

        def _broken_append(record):  # noqa: ANN001, ANN202
            raise OSError("journal unavailable")

        monkeypatch.setattr(ks._journal, "append", _broken_append)
        assert cli.cmd_trigger(Namespace(reason="locked", confirm=True), ks) == cli.EXIT_KILL_FAILED
