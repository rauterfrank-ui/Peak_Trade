"""Atomic cross-process one-shot Owner-GO consumption for canary entry (fail-closed).

Filesystem-backed exclusive lock + atomic state file (write temp, fsync, rename).
Does not authorize POST. AUTHORITY_EFFECT=NONE.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, Mapping

CONTRACT_ID = "CANARY_CAPITAL_GUARD_ATOMIC_ONE_SHOT_V1"
STATE_SCHEMA_VERSION = "canary_capital_guard_atomic_one_shot.v1"

STATE_AVAILABLE = "AVAILABLE"
STATE_RESERVED_PRE_POST = "RESERVED_PRE_POST"
STATE_SUBMIT_MAY_HAVE_OCCURRED = "SUBMIT_MAY_HAVE_OCCURRED"
STATE_SUBMITTED_ACKNOWLEDGED = "SUBMITTED_ACKNOWLEDGED"
STATE_RECONCILIATION_PENDING = "RECONCILIATION_PENDING"
STATE_TERMINAL_RECONCILED = "TERMINAL_RECONCILED"
STATE_HALTED_UNRESOLVED = "HALTED_UNRESOLVED"

# Legacy aliases for transitional readers
STATE_UNKNOWN = STATE_SUBMIT_MAY_HAVE_OCCURRED

TERMINAL_STATES = frozenset(
    {
        STATE_SUBMITTED_ACKNOWLEDGED,
        STATE_RECONCILIATION_PENDING,
        STATE_TERMINAL_RECONCILED,
        STATE_HALTED_UNRESOLVED,
    }
)
BLOCKING_STATES = frozenset(
    {
        STATE_RESERVED_PRE_POST,
        STATE_SUBMIT_MAY_HAVE_OCCURRED,
        STATE_SUBMITTED_ACKNOWLEDGED,
        STATE_RECONCILIATION_PENDING,
        STATE_TERMINAL_RECONCILED,
        STATE_HALTED_UNRESOLVED,
    }
)

DEFAULT_STATE_DIR_REL = (
    "evidence/ops/section_11_13_5_live_canary_capital_guard_atomic_one_shot_v1/states"
)


class CanaryAtomicOneShotError(RuntimeError):
    """Fail-closed atomic one-shot violation."""


def _canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


@dataclass(frozen=True)
class CanaryAuthorizationBindingV1:
    owner_go: str
    origin_main_sha: str
    account_scope: str
    environment: str
    instrument_id: str
    plan_digest: str
    guard_config_digest: str
    session_id: str
    clordid: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "owner_go": self.owner_go,
            "origin_main_sha": self.origin_main_sha,
            "account_scope": self.account_scope,
            "environment": self.environment,
            "instrument_id": self.instrument_id,
            "plan_digest": self.plan_digest,
            "guard_config_digest": self.guard_config_digest,
            "session_id": self.session_id,
            "clordid": self.clordid,
        }

    def consumption_key(self) -> str:
        material = _canonical_json(
            {
                "owner_go": self.owner_go.strip(),
                "origin_main_sha": self.origin_main_sha.strip().lower(),
                "account_scope": self.account_scope.strip(),
                "environment": self.environment.strip().upper(),
            }
        )
        return hashlib.sha256(material.encode("utf-8")).hexdigest()

    def binding_digest(self) -> str:
        return hashlib.sha256(_canonical_json(self.to_dict()).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class CanaryAtomicAuthorizationStateV1:
    schema_version: str
    consumption_key: str
    state: str
    binding_digest: str
    binding: dict[str, Any]
    authorization_permanently_consumed: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "consumption_key": self.consumption_key,
            "state": self.state,
            "binding_digest": self.binding_digest,
            "binding": dict(self.binding),
            "authorization_permanently_consumed": self.authorization_permanently_consumed,
            "contract_id": CONTRACT_ID,
        }


def default_atomic_state_dir_v1(*, repo_root: Path | None = None) -> Path:
    root = repo_root or Path(__file__).resolve().parents[3]
    return root / DEFAULT_STATE_DIR_REL


def _paths(state_dir: Path, consumption_key: str) -> tuple[Path, Path]:
    safe = consumption_key.lower()
    return state_dir / f"{safe}.state.json", state_dir / f"{safe}.lock"


@contextmanager
def _exclusive_lock_v1(lock_path: Path) -> Iterator[None]:
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(str(lock_path), os.O_RDWR | os.O_CREAT, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)


def _atomic_write_state_v1(state_path: Path, payload: Mapping[str, Any]) -> None:
    state_path.parent.mkdir(parents=True, exist_ok=True)
    text = _canonical_json(payload) + "\n"
    data = text.encode("utf-8")
    fd, tmp_path = tempfile.mkstemp(
        prefix=f".{state_path.name}.",
        dir=str(state_path.parent),
        text=True,
    )
    tmp = Path(tmp_path)
    try:
        os.write(fd, data)
        os.fsync(fd)
    finally:
        os.close(fd)
    os.replace(str(tmp), str(state_path))
    dir_fd = os.open(str(state_path.parent), os.O_RDONLY)
    try:
        os.fsync(dir_fd)
    finally:
        os.close(dir_fd)


def _read_state_file_v1(state_path: Path) -> CanaryAtomicAuthorizationStateV1 | None:
    if not state_path.is_file():
        return None
    try:
        raw = state_path.read_text(encoding="utf-8")
        row = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        raise CanaryAtomicOneShotError("LEDGER_CORRUPT_OR_UNREADABLE") from exc
    if not isinstance(row, dict):
        raise CanaryAtomicOneShotError("LEDGER_CORRUPT_NOT_OBJECT")
    schema = str(row.get("schema_version") or "")
    if schema != STATE_SCHEMA_VERSION:
        raise CanaryAtomicOneShotError(f"LEDGER_SCHEMA_MISMATCH:{schema or '<empty>'}")
    binding = row.get("binding")
    if not isinstance(binding, dict):
        raise CanaryAtomicOneShotError("LEDGER_BINDING_MISSING")
    return CanaryAtomicAuthorizationStateV1(
        schema_version=schema,
        consumption_key=str(row.get("consumption_key") or ""),
        state=str(row.get("state") or STATE_HALTED_UNRESOLVED),
        binding_digest=str(row.get("binding_digest") or ""),
        binding=binding,
        authorization_permanently_consumed=bool(row.get("authorization_permanently_consumed")),
    )


def load_atomic_authorization_state_v1(
    *,
    state_dir: Path,
    consumption_key: str,
) -> CanaryAtomicAuthorizationStateV1 | None:
    state_path, _ = _paths(state_dir, consumption_key)
    if not state_path.is_file():
        return None
    return _read_state_file_v1(state_path)


def assert_atomic_entry_authorization_available_v1(
    *,
    state_dir: Path,
    binding: CanaryAuthorizationBindingV1,
) -> None:
    """Fail-closed if Owner-GO scope already consumed or payload binding diverges."""
    key = binding.consumption_key()
    existing = load_atomic_authorization_state_v1(state_dir=state_dir, consumption_key=key)
    if existing is None:
        return
    if existing.state in BLOCKING_STATES or existing.authorization_permanently_consumed:
        if existing.binding_digest != binding.binding_digest():
            raise CanaryAtomicOneShotError("OWNER_GO_PAYLOAD_BINDING_MISMATCH")
        raise CanaryAtomicOneShotError(f"OWNER_GO_ALREADY_CONSUMED:{existing.state}")
    if existing.binding_digest != binding.binding_digest():
        raise CanaryAtomicOneShotError("OWNER_GO_PAYLOAD_BINDING_MISMATCH")


def atomic_reserve_owner_go_authorization_v1(
    *,
    state_dir: Path,
    binding: CanaryAuthorizationBindingV1,
) -> CanaryAtomicAuthorizationStateV1:
    """Atomically consume Owner-GO scope and bind immutable payload (RESERVED_PRE_POST)."""
    key = binding.consumption_key()
    state_path, lock_path = _paths(state_dir, key)
    with _exclusive_lock_v1(lock_path):
        existing = _read_state_file_v1(state_path) if state_path.is_file() else None
        if existing is not None:
            if existing.binding_digest != binding.binding_digest():
                raise CanaryAtomicOneShotError("OWNER_GO_PAYLOAD_BINDING_MISMATCH")
            if existing.state in BLOCKING_STATES or existing.authorization_permanently_consumed:
                raise CanaryAtomicOneShotError(f"OWNER_GO_ALREADY_CONSUMED:{existing.state}")
        payload = {
            "schema_version": STATE_SCHEMA_VERSION,
            "consumption_key": key,
            "state": STATE_RESERVED_PRE_POST,
            "binding_digest": binding.binding_digest(),
            "binding": binding.to_dict(),
            "authorization_permanently_consumed": True,
        }
        _atomic_write_state_v1(state_path, payload)
        return _read_state_file_v1(state_path) or CanaryAtomicAuthorizationStateV1(
            schema_version=STATE_SCHEMA_VERSION,
            consumption_key=key,
            state=STATE_RESERVED_PRE_POST,
            binding_digest=binding.binding_digest(),
            binding=binding.to_dict(),
            authorization_permanently_consumed=True,
        )


def atomic_transition_state_v1(
    *,
    state_dir: Path,
    binding: CanaryAuthorizationBindingV1,
    new_state: str,
    require_current: str | tuple[str, ...] | None = None,
) -> CanaryAtomicAuthorizationStateV1:
    key = binding.consumption_key()
    state_path, lock_path = _paths(state_dir, key)
    allowed_current = (
        (require_current,) if isinstance(require_current, str) else tuple(require_current or ())
    )
    with _exclusive_lock_v1(lock_path):
        existing = _read_state_file_v1(state_path)
        if existing is None:
            raise CanaryAtomicOneShotError("ATOMIC_STATE_MISSING")
        if existing.binding_digest != binding.binding_digest():
            raise CanaryAtomicOneShotError("OWNER_GO_PAYLOAD_BINDING_MISMATCH")
        if allowed_current and existing.state not in allowed_current:
            raise CanaryAtomicOneShotError(
                f"INVALID_STATE_TRANSITION:{existing.state}->{new_state}"
            )
        payload = existing.to_dict()
        payload["state"] = new_state
        payload["authorization_permanently_consumed"] = True
        _atomic_write_state_v1(state_path, payload)
        result = _read_state_file_v1(state_path)
        if result is None:
            raise CanaryAtomicOneShotError("ATOMIC_WRITE_VERIFICATION_FAILED")
        return result


def atomic_mark_submit_boundary_v1(
    *,
    state_dir: Path,
    binding: CanaryAuthorizationBindingV1,
) -> CanaryAtomicAuthorizationStateV1:
    return atomic_transition_state_v1(
        state_dir=state_dir,
        binding=binding,
        new_state=STATE_SUBMIT_MAY_HAVE_OCCURRED,
        require_current=(STATE_RESERVED_PRE_POST, STATE_SUBMIT_MAY_HAVE_OCCURRED),
    )


def atomic_mark_submitted_acknowledged_v1(
    *,
    state_dir: Path,
    binding: CanaryAuthorizationBindingV1,
) -> CanaryAtomicAuthorizationStateV1:
    return atomic_transition_state_v1(
        state_dir=state_dir,
        binding=binding,
        new_state=STATE_SUBMITTED_ACKNOWLEDGED,
        require_current=(STATE_SUBMIT_MAY_HAVE_OCCURRED, STATE_RESERVED_PRE_POST),
    )


def atomic_mark_unknown_submit_v1(
    *,
    state_dir: Path,
    binding: CanaryAuthorizationBindingV1,
) -> CanaryAtomicAuthorizationStateV1:
    return atomic_transition_state_v1(
        state_dir=state_dir,
        binding=binding,
        new_state=STATE_SUBMIT_MAY_HAVE_OCCURRED,
        require_current=(
            STATE_RESERVED_PRE_POST,
            STATE_SUBMIT_MAY_HAVE_OCCURRED,
            STATE_SUBMITTED_ACKNOWLEDGED,
        ),
    )


def atomic_mark_reconciliation_pending_v1(
    *,
    state_dir: Path,
    binding: CanaryAuthorizationBindingV1,
) -> CanaryAtomicAuthorizationStateV1:
    return atomic_transition_state_v1(
        state_dir=state_dir,
        binding=binding,
        new_state=STATE_RECONCILIATION_PENDING,
        require_current=(
            STATE_SUBMIT_MAY_HAVE_OCCURRED,
            STATE_SUBMITTED_ACKNOWLEDGED,
        ),
    )


def atomic_mark_terminal_reconciled_v1(
    *,
    state_dir: Path,
    binding: CanaryAuthorizationBindingV1,
) -> CanaryAtomicAuthorizationStateV1:
    return atomic_transition_state_v1(
        state_dir=state_dir,
        binding=binding,
        new_state=STATE_TERMINAL_RECONCILED,
        require_current=(STATE_RECONCILIATION_PENDING, STATE_SUBMITTED_ACKNOWLEDGED),
    )


def atomic_mark_halted_unresolved_v1(
    *,
    state_dir: Path,
    binding: CanaryAuthorizationBindingV1,
) -> CanaryAtomicAuthorizationStateV1:
    return atomic_transition_state_v1(
        state_dir=state_dir,
        binding=binding,
        new_state=STATE_HALTED_UNRESOLVED,
        require_current=None,
    )


def durable_entry_state_for_guard_v1(
    *,
    state_dir: Path,
    consumption_key: str,
) -> str:
    """Map atomic state to guard durable_entry_state (fail-closed unless AVAILABLE)."""
    try:
        row = load_atomic_authorization_state_v1(
            state_dir=state_dir, consumption_key=consumption_key
        )
    except CanaryAtomicOneShotError:
        return STATE_HALTED_UNRESOLVED
    if row is None:
        return STATE_AVAILABLE
    return row.state
