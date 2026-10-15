"""Durable cumulative GET budget ledger. No credentials. No network."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.atomic_io_v1 import (
    append_only_create_json,
    atomic_write_json,
    canonical_json_dumps,
)
from src.ops.owner_scoped_get_budget_enforcement_v1.constants_v1 import (
    GRANT_LOCK_SUFFIX,
    GRANT_STATE_ACTIVE,
    GRANT_STATE_EXHAUSTED,
    GRANT_STATE_EXHAUSTED_UNCERTAIN,
    LEDGER_DIRNAME,
    LEDGER_FILENAME_SUFFIX,
    RESERVATION_OUTCOME_COMPLETED,
    RESERVATION_OUTCOME_RELEASED_NO_SEND,
    RESERVATION_OUTCOME_UNCERTAIN_WIRE,
    SCHEMA_VERSION,
)
from src.ops.owner_scoped_get_budget_enforcement_v1.errors_v1 import OwnerScopedGetBudgetError
from src.ops.owner_scoped_get_budget_enforcement_v1.grant_identity_v1 import (
    OwnerScopedGetBudgetGrantBindingV1,
    compute_owner_grant_identity_digest_v1,
    owner_grant_id_from_identity_v1,
)
from src.ops.owner_scoped_get_budget_enforcement_v1.grant_ledger_lock_v1 import (
    OwnerScopedGetBudgetGrantLockV1,
)

_SECRET_TOKENS = ("secret", "passphrase", "api_key", "apikey", "private_key", "authorization")


def _utc_now_iso_v1() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _assert_no_secrets(payload: Mapping[str, Any]) -> None:
    blob = canonical_json_dumps(payload).lower()
    for token in _SECRET_TOKENS:
        if token in blob:
            raise OwnerScopedGetBudgetError(f"SECRET_TOKEN_PRESENT:{token}")


def ledger_dir_v1(store_root: Path | str) -> Path:
    return Path(store_root) / LEDGER_DIRNAME


def ledger_path_v1(*, store_root: Path | str, grant_id: str) -> Path:
    gid = owner_grant_id_from_identity_v1(grant_id)
    return ledger_dir_v1(store_root) / f"{gid}{LEDGER_FILENAME_SUFFIX}"


def lock_path_v1(*, store_root: Path | str, grant_id: str) -> Path:
    gid = owner_grant_id_from_identity_v1(grant_id)
    return ledger_dir_v1(store_root) / f"{gid}{GRANT_LOCK_SUFFIX}"


def _effective_consumed_v1(record: Mapping[str, Any]) -> int:
    committed = int(record.get("committed_request_count") or 0)
    uncertain = int(record.get("uncertain_request_count") or 0)
    in_flight = int(record.get("in_flight_request_count") or 0)
    return committed + uncertain + in_flight


def load_owner_scoped_get_budget_ledger_v1(
    *,
    store_root: Path | str,
    grant_id: str,
) -> dict[str, Any]:
    path = ledger_path_v1(store_root=store_root, grant_id=grant_id)
    if not path.is_file():
        return {"present": False, "path": str(path), "record": None}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise OwnerScopedGetBudgetError("GRANT_LEDGER_MALFORMED")
    _assert_no_secrets(payload)
    return {"present": True, "path": str(path), "record": payload}


def mint_owner_scoped_get_budget_grant_v1(
    *,
    store_root: Path | str,
    binding: OwnerScopedGetBudgetGrantBindingV1,
) -> dict[str, Any]:
    """Append-only grant ledger create. One grant identity per bounded operation."""
    identity = compute_owner_grant_identity_digest_v1(binding)
    grant_id = owner_grant_id_from_identity_v1(identity)
    path = ledger_path_v1(store_root=store_root, grant_id=grant_id)
    record = {
        "schema_version": SCHEMA_VERSION,
        "grant_id": grant_id,
        "owner_grant_identity_digest": identity,
        "binding": binding.to_canonical_dict(),
        "cumulative_request_budget": int(binding.cumulative_request_budget),
        "committed_request_count": 0,
        "uncertain_request_count": 0,
        "in_flight_request_count": 0,
        "state": GRANT_STATE_ACTIVE,
        "minted_at_utc": _utc_now_iso_v1(),
        "exhausted_at_utc": "",
        "resubmit_allowed": False,
        "grant_renewal_allowed": False,
    }
    _assert_no_secrets(record)
    ledger_dir_v1(store_root).mkdir(parents=True, exist_ok=True)
    lock = OwnerScopedGetBudgetGrantLockV1(
        lock_path=lock_path_v1(store_root=store_root, grant_id=grant_id),
        grant_id=grant_id,
    )
    lock.acquire()
    try:
        existing = load_owner_scoped_get_budget_ledger_v1(store_root=store_root, grant_id=grant_id)
        if existing.get("present"):
            rec = existing.get("record") or {}
            if str(rec.get("owner_grant_identity_digest") or "") != identity:
                raise OwnerScopedGetBudgetError("GRANT_ID_COLLISION_BINDING_MISMATCH")
            return {"grant_id": grant_id, "path": str(path), "created": False, "record": rec}
        try:
            append_only_create_json(path=path, payload=record)
        except FileExistsError as exc:
            existing = load_owner_scoped_get_budget_ledger_v1(
                store_root=store_root, grant_id=grant_id
            )
            rec = existing.get("record") or {}
            if str(rec.get("owner_grant_identity_digest") or "") != identity:
                raise OwnerScopedGetBudgetError("GRANT_ID_COLLISION_BINDING_MISMATCH") from exc
            return {"grant_id": grant_id, "path": str(path), "created": False, "record": rec}
        return {"grant_id": grant_id, "path": str(path), "created": True, "record": record}
    finally:
        lock.release()


@dataclass(frozen=True)
class OwnerScopedGetBudgetReservationV1:
    reservation_id: str
    grant_id: str
    endpoint_path: str


def _mutate_ledger_under_lock_v1(
    *,
    store_root: Path | str,
    grant_id: str,
    mutator,
) -> dict[str, Any]:
    lock = OwnerScopedGetBudgetGrantLockV1(
        lock_path=lock_path_v1(store_root=store_root, grant_id=grant_id),
        grant_id=grant_id,
    )
    lock.acquire()
    try:
        loaded = load_owner_scoped_get_budget_ledger_v1(store_root=store_root, grant_id=grant_id)
        if loaded.get("present") is not True:
            raise OwnerScopedGetBudgetError("GRANT_LEDGER_ABSENT")
        record = dict(loaded["record"] or {})
        updated = mutator(record)
        _assert_no_secrets(updated)
        atomic_write_json(path=Path(loaded["path"]), payload=updated)
        return updated
    finally:
        lock.release()


def atomic_pre_send_reserve_v1(
    *,
    store_root: Path | str,
    grant_id: str,
    reservation_id: str,
    endpoint_path: str,
) -> OwnerScopedGetBudgetReservationV1:
    rid = str(reservation_id or "").strip()
    path_only = str(endpoint_path or "").split("?", 1)[0]
    if not rid or not path_only:
        raise OwnerScopedGetBudgetError("RESERVATION_INPUT_INVALID")

    exceed_after_write = False

    def _reserve(record: dict[str, Any]) -> dict[str, Any]:
        nonlocal exceed_after_write
        if str(record.get("grant_id") or "") != owner_grant_id_from_identity_v1(grant_id):
            raise OwnerScopedGetBudgetError("GRANT_ID_MISMATCH")
        state = str(record.get("state") or "")
        if state in {GRANT_STATE_EXHAUSTED, GRANT_STATE_EXHAUSTED_UNCERTAIN}:
            raise OwnerScopedGetBudgetError("GRANT_EXHAUSTED")
        budget = int(record.get("cumulative_request_budget") or 0)
        if _effective_consumed_v1(record) >= budget:
            record["state"] = GRANT_STATE_EXHAUSTED
            record["exhausted_at_utc"] = _utc_now_iso_v1()
            exceed_after_write = True
            return record
        reservations = dict(record.get("open_reservations") or {})
        if rid in reservations:
            raise OwnerScopedGetBudgetError("RESERVATION_ID_REUSE")
        record["in_flight_request_count"] = int(record.get("in_flight_request_count") or 0) + 1
        reservations[rid] = {
            "endpoint_path": path_only,
            "reserved_at_utc": _utc_now_iso_v1(),
        }
        record["open_reservations"] = reservations
        return record

    _mutate_ledger_under_lock_v1(store_root=store_root, grant_id=grant_id, mutator=_reserve)
    if exceed_after_write:
        raise OwnerScopedGetBudgetError("CUMULATIVE_REQUEST_BUDGET_EXCEEDED")
    return OwnerScopedGetBudgetReservationV1(
        reservation_id=rid,
        grant_id=owner_grant_id_from_identity_v1(grant_id),
        endpoint_path=path_only,
    )


def finalize_reservation_v1(
    *,
    store_root: Path | str,
    grant_id: str,
    reservation_id: str,
    outcome: str,
) -> dict[str, Any]:
    allowed = {
        RESERVATION_OUTCOME_COMPLETED,
        RESERVATION_OUTCOME_RELEASED_NO_SEND,
        RESERVATION_OUTCOME_UNCERTAIN_WIRE,
    }
    if outcome not in allowed:
        raise OwnerScopedGetBudgetError(f"RESERVATION_OUTCOME_FORBIDDEN:{outcome}")

    def _finalize(record: dict[str, Any]) -> dict[str, Any]:
        reservations = dict(record.get("open_reservations") or {})
        rid = str(reservation_id or "").strip()
        if rid not in reservations:
            raise OwnerScopedGetBudgetError("RESERVATION_NOT_OPEN")
        in_flight = int(record.get("in_flight_request_count") or 0)
        if in_flight < 1:
            raise OwnerScopedGetBudgetError("IN_FLIGHT_UNDERFLOW")
        record["in_flight_request_count"] = in_flight - 1
        del reservations[rid]
        record["open_reservations"] = reservations
        if outcome == RESERVATION_OUTCOME_COMPLETED:
            record["committed_request_count"] = int(record.get("committed_request_count") or 0) + 1
        elif outcome == RESERVATION_OUTCOME_UNCERTAIN_WIRE:
            record["uncertain_request_count"] = int(record.get("uncertain_request_count") or 0) + 1
        # RELEASED_NO_SEND: only releases in_flight without incrementing committed/uncertain
        budget = int(record.get("cumulative_request_budget") or 0)
        if _effective_consumed_v1(record) >= budget:
            if outcome == RESERVATION_OUTCOME_UNCERTAIN_WIRE:
                record["state"] = GRANT_STATE_EXHAUSTED_UNCERTAIN
            else:
                record["state"] = GRANT_STATE_EXHAUSTED
            record["exhausted_at_utc"] = _utc_now_iso_v1()
        return record

    return _mutate_ledger_under_lock_v1(store_root=store_root, grant_id=grant_id, mutator=_finalize)


def prove_grant_does_not_authorize_post_v1() -> dict[str, str]:
    return {
        "POST_ALLOWED": "false",
        "GRANT_RENEWAL_ALLOWED": "false",
        "RESUBMIT_ALLOWED": "false",
    }
