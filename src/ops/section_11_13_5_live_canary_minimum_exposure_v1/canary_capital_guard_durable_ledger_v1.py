"""Durable one-shot facade: atomic state (authoritative) + optional JSONL audit trail.

Append-only JSONL is observability-only; admission uses
``canary_capital_guard_atomic_one_shot_v1``. AUTHORITY_EFFECT=NONE.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.canary_capital_guard_atomic_one_shot_v1 import (
    CanaryAtomicOneShotError,
    CanaryAuthorizationBindingV1,
    STATE_AVAILABLE,
    STATE_RESERVED_PRE_POST,
    STATE_SUBMIT_MAY_HAVE_OCCURRED,
    STATE_SUBMITTED_ACKNOWLEDGED,
    atomic_mark_submitted_acknowledged_v1,
    atomic_mark_unknown_submit_v1,
    atomic_reserve_owner_go_authorization_v1,
    assert_atomic_entry_authorization_available_v1,
    default_atomic_state_dir_v1,
    durable_entry_state_for_guard_v1,
    load_atomic_authorization_state_v1,
)

LEDGER_SCHEMA_VERSION = "canary_capital_guard_durable_ledger.v2"
DEFAULT_LEDGER_REL_PATH = (
    "evidence/ops/section_11_13_5_live_canary_capital_guard_durable_ledger_v1/ledger.jsonl"
)

# Legacy aliases for readers
STATE_SUBMITTED = STATE_SUBMITTED_ACKNOWLEDGED
STATE_UNKNOWN = STATE_SUBMIT_MAY_HAVE_OCCURRED
STATE_TERMINAL = "TERMINAL_RECONCILED"


class CanaryCapitalGuardDurableLedgerError(RuntimeError):
    """Fail-closed durable ledger violation."""


def _canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def compute_canary_owner_scope_key_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    account_scope: str,
    environment: str = "LIVE",
) -> str:
    material = _canonical_json(
        {
            "owner_go": str(owner_go or "").strip(),
            "origin_main_sha": str(origin_main_sha or "").strip().lower(),
            "account_scope": str(account_scope or "").strip(),
            "environment": str(environment or "LIVE").strip().upper(),
        }
    )
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def build_canary_authorization_binding_v1(
    *,
    owner_go: str,
    origin_main_sha: str,
    account_scope: str,
    environment: str,
    instrument_id: str,
    plan_digest: str,
    guard_config_digest: str,
    session_id: str,
    clordid: str,
) -> CanaryAuthorizationBindingV1:
    return CanaryAuthorizationBindingV1(
        owner_go=str(owner_go or "").strip(),
        origin_main_sha=str(origin_main_sha or "").strip().lower(),
        account_scope=str(account_scope or "").strip(),
        environment=str(environment or "LIVE").strip().upper(),
        instrument_id=str(instrument_id or "").strip(),
        plan_digest=str(plan_digest or "").strip(),
        guard_config_digest=str(guard_config_digest or "").strip().lower(),
        session_id=str(session_id or "").strip(),
        clordid=str(clordid or "").strip(),
    )


@dataclass(frozen=True)
class CanaryCapitalGuardDurableSlotV1:
    scope_key: str
    state: str
    plan_digest: str | None
    session_id: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "scope_key": self.scope_key,
            "state": self.state,
            "plan_digest": self.plan_digest,
            "session_id": self.session_id,
        }


def default_ledger_path_v1(*, repo_root: Path | None = None) -> Path:
    root = repo_root or Path(__file__).resolve().parents[3]
    return root / DEFAULT_LEDGER_REL_PATH


def _read_events(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    events: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        text = line.strip()
        if not text:
            continue
        row = json.loads(text)
        if isinstance(row, dict):
            events.append(row)
    return events


def resolve_durable_slot_v1(
    *,
    ledger_path: Path,
    scope_key: str,
    atomic_state_dir: Path | None = None,
) -> CanaryCapitalGuardDurableSlotV1:
    state_dir = atomic_state_dir or default_atomic_state_dir_v1()
    atomic_state = durable_entry_state_for_guard_v1(state_dir=state_dir, consumption_key=scope_key)
    plan_digest: str | None = None
    session_id: str | None = None
    try:
        row = load_atomic_authorization_state_v1(state_dir=state_dir, consumption_key=scope_key)
        if row is not None:
            plan_digest = str(row.binding.get("plan_digest") or "") or None
            session_id = str(row.binding.get("session_id") or "") or None
    except CanaryAtomicOneShotError:
        atomic_state = STATE_SUBMIT_MAY_HAVE_OCCURRED
    if atomic_state == STATE_AVAILABLE:
        for row in _read_events(ledger_path):
            if str(row.get("scope_key") or "") != scope_key:
                continue
            atomic_state = str(row.get("state") or atomic_state)
            plan_digest = row.get("plan_digest") or plan_digest
            session_id = row.get("session_id") or session_id
    return CanaryCapitalGuardDurableSlotV1(
        scope_key=scope_key,
        state=atomic_state,
        plan_digest=plan_digest,
        session_id=session_id,
    )


def assert_durable_entry_slot_available_v1(
    *,
    ledger_path: Path,
    scope_key: str,
    binding: CanaryAuthorizationBindingV1 | None = None,
    atomic_state_dir: Path | None = None,
) -> CanaryCapitalGuardDurableSlotV1:
    state_dir = atomic_state_dir or default_atomic_state_dir_v1()
    if binding is not None:
        try:
            assert_atomic_entry_authorization_available_v1(state_dir=state_dir, binding=binding)
        except CanaryAtomicOneShotError as exc:
            raise CanaryCapitalGuardDurableLedgerError(str(exc)) from exc
    slot = resolve_durable_slot_v1(
        ledger_path=ledger_path, scope_key=scope_key, atomic_state_dir=state_dir
    )
    if slot.state not in {STATE_AVAILABLE, ""}:
        raise CanaryCapitalGuardDurableLedgerError(f"DURABLE_ENTRY_SLOT_UNAVAILABLE:{slot.state}")
    return slot


def append_durable_ledger_event_v1(
    *,
    ledger_path: Path,
    event: Mapping[str, Any],
) -> None:
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    line = _canonical_json(dict(event)) + "\n"
    flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND
    fd = os.open(str(ledger_path), flags, 0o600)
    try:
        os.write(fd, line.encode("utf-8"))
    finally:
        os.close(fd)


def record_durable_entry_reservation_v1(
    *,
    ledger_path: Path,
    scope_key: str,
    plan_digest: str,
    session_id: str,
    guard_config_digest: str,
    owner_go: str = "",
    origin_main_sha: str = "",
    account_scope: str = "",
    environment: str = "LIVE",
    instrument_id: str = "",
    clordid: str = "",
    atomic_state_dir: Path | None = None,
) -> None:
    state_dir = atomic_state_dir or default_atomic_state_dir_v1()
    binding = build_canary_authorization_binding_v1(
        owner_go=owner_go,
        origin_main_sha=origin_main_sha,
        account_scope=account_scope,
        environment=environment,
        instrument_id=instrument_id or "OFFLINE-UNBOUND",
        plan_digest=plan_digest,
        guard_config_digest=guard_config_digest,
        session_id=session_id,
        clordid=clordid or "OFFLINE-UNBOUND",
    )
    binding_key = binding.consumption_key()
    if scope_key and scope_key != binding_key:
        raise CanaryCapitalGuardDurableLedgerError("SCOPE_KEY_BINDING_MISMATCH")
    scope_key = binding_key
    try:
        atomic_reserve_owner_go_authorization_v1(state_dir=state_dir, binding=binding)
    except CanaryAtomicOneShotError as exc:
        raise CanaryCapitalGuardDurableLedgerError(str(exc)) from exc
    append_durable_ledger_event_v1(
        ledger_path=ledger_path,
        event={
            "schema_version": LEDGER_SCHEMA_VERSION,
            "scope_key": scope_key or binding.consumption_key(),
            "state": STATE_RESERVED_PRE_POST,
            "plan_digest": plan_digest,
            "session_id": session_id,
            "guard_config_digest": guard_config_digest,
            "binding_digest": binding.binding_digest(),
        },
    )


def record_durable_entry_submitted_v1(
    *,
    ledger_path: Path,
    scope_key: str,
    plan_digest: str,
    binding: CanaryAuthorizationBindingV1 | None = None,
    atomic_state_dir: Path | None = None,
) -> None:
    state_dir = atomic_state_dir or default_atomic_state_dir_v1()
    if binding is not None:
        try:
            atomic_mark_submitted_acknowledged_v1(state_dir=state_dir, binding=binding)
        except CanaryAtomicOneShotError as exc:
            raise CanaryCapitalGuardDurableLedgerError(str(exc)) from exc
    append_durable_ledger_event_v1(
        ledger_path=ledger_path,
        event={
            "schema_version": LEDGER_SCHEMA_VERSION,
            "scope_key": scope_key,
            "state": STATE_SUBMITTED_ACKNOWLEDGED,
            "plan_digest": plan_digest,
        },
    )


def record_durable_unknown_submit_v1(
    *,
    ledger_path: Path,
    scope_key: str,
    plan_digest: str,
    binding: CanaryAuthorizationBindingV1 | None = None,
    atomic_state_dir: Path | None = None,
) -> None:
    state_dir = atomic_state_dir or default_atomic_state_dir_v1()
    if binding is not None:
        try:
            atomic_mark_unknown_submit_v1(state_dir=state_dir, binding=binding)
        except CanaryAtomicOneShotError as exc:
            raise CanaryCapitalGuardDurableLedgerError(str(exc)) from exc
    append_durable_ledger_event_v1(
        ledger_path=ledger_path,
        event={
            "schema_version": LEDGER_SCHEMA_VERSION,
            "scope_key": scope_key,
            "state": STATE_SUBMIT_MAY_HAVE_OCCURRED,
            "plan_digest": plan_digest,
        },
    )
