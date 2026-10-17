"""Durable single-use consume ledger for Full-Core envelope-bound permits.

Atomic replace before any retry-capable control flow. In-memory consume is
not crash-safe and cannot authorize send. Replay and second submit remain
denied after SENT_INITIATED, COMPLETED, or ABORTED_BEFORE_TRANSPORT.

Check-and-write runs under an exclusive ``flock`` with a unique ``mkstemp``
temp file, ``fsync``, ``os.replace``, and directory ``fsync``. This ledger is
scoped to one store root; the cross-root one-shot boundary is the global venue
effect authority ledger.

Does not POST. Does not load credentials.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import fcntl
import json
import os
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator, Mapping

from src.ops.full_core_live_path_composition_root_v1.external_effect_permit_v1 import (
    ExternalEffectPermitV1,
)
from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
    FinalOrderEnvelopeV1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.canary_capital_guard_atomic_one_shot_v1 import (
    _atomic_write_state_v1,
)

DURABLE_CONSUME_FILENAME = "full_core_external_effect_permit_consume_v1.json"
DURABLE_STATE_NONE = "NONE"
DURABLE_STATE_SENT_INITIATED = "SENT_INITIATED"
DURABLE_STATE_COMPLETED = "COMPLETED"
DURABLE_STATE_ABORTED_BEFORE_TRANSPORT = "ABORTED_BEFORE_TRANSPORT"
_INITIAL_STATES = frozenset({DURABLE_STATE_SENT_INITIATED, DURABLE_STATE_COMPLETED})
_CONSUMED_STATES = frozenset(
    {
        DURABLE_STATE_SENT_INITIATED,
        DURABLE_STATE_COMPLETED,
        DURABLE_STATE_ABORTED_BEFORE_TRANSPORT,
    }
)
_SECRET_TOKENS = ("secret", "passphrase", "api_key", "apikey", "private_key")


class FullCoreExternalEffectDurableConsumeError(RuntimeError):
    """Fail-closed durable permit-consume violation."""


def _utc_now_iso_v1() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _assert_no_secrets(payload: Mapping[str, Any]) -> None:
    blob = _canonical_json(payload).lower()
    for token in _SECRET_TOKENS:
        if token in blob:
            raise FullCoreExternalEffectDurableConsumeError(f"SECRET_TOKEN_PRESENT:{token}")


def durable_consume_path_v1(store_root: Path | str) -> Path:
    return Path(store_root) / DURABLE_CONSUME_FILENAME


@contextmanager
def exclusive_store_root_lock_v1(store_root: Path) -> Iterator[None]:
    """Process-exclusive ``flock`` on the store-root directory itself (no lock file)."""
    store_root.mkdir(parents=True, exist_ok=True)
    fd = os.open(str(store_root), os.O_RDONLY)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)


def load_external_effect_durable_consume_v1(*, store_root: Path | str | None) -> dict[str, Any]:
    if store_root is None:
        return {
            "present": False,
            "consumed": False,
            "durable_consumed": False,
            "resubmit_allowed": False,
            "retry_allowed": False,
            "record": None,
        }
    path = durable_consume_path_v1(store_root)
    if not path.is_file():
        return {
            "present": False,
            "consumed": False,
            "durable_consumed": False,
            "resubmit_allowed": False,
            "retry_allowed": False,
            "record": None,
            "path": str(path),
        }
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise FullCoreExternalEffectDurableConsumeError("DURABLE_CONSUME_MALFORMED")
    consumed = bool(payload.get("consumed")) is True
    state = str(payload.get("durable_state") or DURABLE_STATE_NONE)
    durable_consumed = consumed or state in _CONSUMED_STATES
    if payload.get("resubmit_allowed") is True or payload.get("retry_allowed") is True:
        raise FullCoreExternalEffectDurableConsumeError("DURABLE_RESUBMIT_MUST_REMAIN_FALSE")
    if payload.get("second_submit_allowed") is True:
        raise FullCoreExternalEffectDurableConsumeError("SECOND_SUBMIT_MUST_REMAIN_FALSE")
    return {
        "present": True,
        "consumed": consumed,
        "durable_consumed": durable_consumed,
        "resubmit_allowed": False,
        "retry_allowed": False,
        "record": payload,
        "path": str(path),
    }


def persist_external_effect_durable_consume_v1(
    *,
    store_root: Path | str,
    permit: ExternalEffectPermitV1,
    envelope: FinalOrderEnvelopeV1,
    durable_state: str,
    post_count: int,
    outcome: str,
) -> dict[str, Any]:
    """Persist consume before any retry-capable control flow. Atomic replace."""
    if store_root is None:
        raise FullCoreExternalEffectDurableConsumeError("DURABLE_STORE_REQUIRED")
    if durable_state not in _INITIAL_STATES:
        raise FullCoreExternalEffectDurableConsumeError(f"DURABLE_STATE_FORBIDDEN:{durable_state}")
    if int(post_count) > 1:
        raise FullCoreExternalEffectDurableConsumeError("POST_COUNT_EXCEEDS_ONE")
    root = Path(store_root)
    root.mkdir(parents=True, exist_ok=True)
    with exclusive_store_root_lock_v1(root):
        existing = load_external_effect_durable_consume_v1(store_root=root)
        if existing.get("durable_consumed") is True:
            record = existing.get("record") or {}
            if str(record.get("permit_id") or "") == permit.permit_id:
                raise FullCoreExternalEffectDurableConsumeError("CONSUMED_PERMIT")
            raise FullCoreExternalEffectDurableConsumeError(
                "DURABLE_CONSUME_ALREADY_PRESENT_NO_REWRITE"
            )
        bound = _consume_record_v1(
            permit=permit,
            envelope=envelope,
            durable_state=durable_state,
            post_count=post_count,
            outcome=outcome,
        )
        _assert_no_secrets(bound)
        _atomic_write_state_v1(durable_consume_path_v1(root), bound)
    return bound


def _consume_record_v1(
    *,
    permit: ExternalEffectPermitV1,
    envelope: FinalOrderEnvelopeV1,
    durable_state: str,
    post_count: int,
    outcome: str,
) -> dict[str, Any]:
    return {
        "durable_state": durable_state,
        "consumed": True,
        "resubmit_allowed": False,
        "retry_allowed": False,
        "second_submit_allowed": False,
        "permit_id": permit.permit_id,
        "envelope_id": envelope.envelope_id,
        "envelope_digest": envelope.envelope_digest,
        "authority_ref": permit.authority_ref,
        "max_post_count": 1,
        "post_count": int(post_count),
        "outcome": str(outcome),
        "consumed_at_utc": _utc_now_iso_v1(),
    }


def _transition_from_sent_initiated_v1(
    *,
    store_root: Path | str,
    permit_id: str,
    envelope_id: str,
    envelope_digest: str,
    new_state: str,
    outcome: str,
    timestamp_field: str,
) -> dict[str, Any]:
    if store_root is None:
        raise FullCoreExternalEffectDurableConsumeError("DURABLE_STORE_REQUIRED")
    pid = str(permit_id or "").strip()
    eid = str(envelope_id or "").strip()
    digest = str(envelope_digest or "").strip()
    if not pid or not eid or len(digest) != 64:
        raise FullCoreExternalEffectDurableConsumeError("FINALIZE_IDENTITY_INVALID")
    root = Path(store_root)
    with exclusive_store_root_lock_v1(root):
        existing = load_external_effect_durable_consume_v1(store_root=root)
        if existing.get("durable_consumed") is not True:
            raise FullCoreExternalEffectDurableConsumeError("DURABLE_CONSUME_NOT_PRESENT")
        record = existing.get("record") or {}
        if str(record.get("durable_state") or "") != DURABLE_STATE_SENT_INITIATED:
            raise FullCoreExternalEffectDurableConsumeError("DURABLE_STATE_NOT_SENT_INITIATED")
        if str(record.get("permit_id") or "") != pid:
            raise FullCoreExternalEffectDurableConsumeError("FINALIZE_PERMIT_ID_MISMATCH")
        if str(record.get("envelope_id") or "") != eid:
            raise FullCoreExternalEffectDurableConsumeError("FINALIZE_ENVELOPE_ID_MISMATCH")
        if str(record.get("envelope_digest") or "") != digest:
            raise FullCoreExternalEffectDurableConsumeError("FINALIZE_ENVELOPE_DIGEST_MISMATCH")
        updated = dict(record)
        updated["durable_state"] = new_state
        updated["outcome"] = str(outcome or "")
        updated[timestamp_field] = _utc_now_iso_v1()
        updated["consumed"] = True
        updated["resubmit_allowed"] = False
        updated["retry_allowed"] = False
        updated["second_submit_allowed"] = False
        _assert_no_secrets(updated)
        _atomic_write_state_v1(durable_consume_path_v1(root), updated)
    return updated


def finalize_external_effect_durable_consume_v1(
    *,
    store_root: Path | str,
    permit_id: str,
    envelope_id: str,
    envelope_digest: str,
    outcome: str,
) -> dict[str, Any]:
    """Transition SENT_INITIATED → COMPLETED without permitting resubmit."""
    return _transition_from_sent_initiated_v1(
        store_root=store_root,
        permit_id=permit_id,
        envelope_id=envelope_id,
        envelope_digest=envelope_digest,
        new_state=DURABLE_STATE_COMPLETED,
        outcome=outcome,
        timestamp_field="completed_at_utc",
    )


def abort_external_effect_durable_consume_before_transport_v1(
    *,
    store_root: Path | str,
    permit_id: str,
    envelope_id: str,
    envelope_digest: str,
    outcome: str,
) -> dict[str, Any]:
    """SENT_INITIATED → ABORTED_BEFORE_TRANSPORT when the socket provably never opened.

    The permit stays consumed: no retry, no resubmit, no restored authority.
    """
    return _transition_from_sent_initiated_v1(
        store_root=store_root,
        permit_id=permit_id,
        envelope_id=envelope_id,
        envelope_digest=envelope_digest,
        new_state=DURABLE_STATE_ABORTED_BEFORE_TRANSPORT,
        outcome=outcome,
        timestamp_field="aborted_at_utc",
    )
