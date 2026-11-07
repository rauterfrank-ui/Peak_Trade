"""Durable single-use consume ledger for Full-Core envelope-bound permits.

Atomic replace before any retry-capable control flow. In-memory consume is
not crash-safe and cannot authorize send. Replay and second submit remain
denied after SENT_INITIATED or COMPLETED.

Does not POST. Does not load credentials.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import json
import fcntl
import os
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from src.ops.full_core_live_path_composition_root_v1.external_effect_permit_v1 import (
    ExternalEffectPermitV1,
)
from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
    FinalOrderEnvelopeV1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_v1 import (
    PortfolioExecutionReconciliationIdentityV2,
    parse_exchange_reconciliation_identity_v1,
)

DURABLE_CONSUME_FILENAME = "full_core_external_effect_permit_consume_v1.json"
DURABLE_STATE_NONE = "NONE"
DURABLE_STATE_SENT_INITIATED = "SENT_INITIATED"
DURABLE_STATE_COMPLETED = "COMPLETED"
_CONSUMED_STATES = frozenset({DURABLE_STATE_SENT_INITIATED, DURABLE_STATE_COMPLETED})
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
def _writer_lock_v1(root):
    fd = os.open(root / "external_effect_permit_writer.lock", os.O_CREAT | os.O_RDWR, 0o600)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise FullCoreExternalEffectDurableConsumeError("DURABLE_CONSUME_WRITER_BUSY") from exc
        yield
    finally:
        os.close(fd)


def _validate_owned_identity_v2(record):
    if "execution_identity" not in record:
        if "execution_identity_digest" in record:
            raise FullCoreExternalEffectDurableConsumeError("DURABLE_EXECUTION_IDENTITY_MISSING")
        return
    try:
        identity = parse_exchange_reconciliation_identity_v1(record["execution_identity"])
        if not (
            type(identity) is PortfolioExecutionReconciliationIdentityV2
            and identity.identity_digest() == record.get("execution_identity_digest")
            and identity.send_permit_id == record["permit_id"]
            and identity.send_authority_ref == record["authority_ref"]
            and identity.envelope_identity == record["envelope_id"]
            and identity.envelope_digest == record["envelope_digest"]
            and record["consumed"] is True
            and record["durable_state"] in _CONSUMED_STATES
            and type(identity.budget_source_sequence) is int
            and type(identity.budget_submit_sequence) is int
            and identity.budget_source_sequence > 0
            and identity.budget_submit_sequence == identity.budget_source_sequence + 1
        ):
            raise ValueError("scope")
    except (ValueError, TypeError, KeyError, AttributeError) as exc:
        raise FullCoreExternalEffectDurableConsumeError(
            "DURABLE_EXECUTION_IDENTITY_UNPROVEN"
        ) from exc


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
    _validate_owned_identity_v2(payload)
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
    execution_identity=None,
) -> dict[str, Any]:
    """Persist consume before any retry-capable control flow. Atomic replace."""
    if store_root is None:
        raise FullCoreExternalEffectDurableConsumeError("DURABLE_STORE_REQUIRED")
    if durable_state not in _CONSUMED_STATES:
        raise FullCoreExternalEffectDurableConsumeError(f"DURABLE_STATE_FORBIDDEN:{durable_state}")
    if int(post_count) > 1:
        raise FullCoreExternalEffectDurableConsumeError("POST_COUNT_EXCEEDS_ONE")
    root = Path(store_root)
    root.mkdir(parents=True, exist_ok=True)
    bound = {
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
    if execution_identity is not None:
        if type(execution_identity) is not PortfolioExecutionReconciliationIdentityV2:
            raise FullCoreExternalEffectDurableConsumeError(
                "DURABLE_EXECUTION_IDENTITY_TYPE_INVALID"
            )
        bound["execution_identity"] = execution_identity.to_dict()
        bound["execution_identity_digest"] = execution_identity.identity_digest()
        _validate_owned_identity_v2(bound)
        if not (
            execution_identity.native_id == envelope.instrument_id
            and execution_identity.clordid == envelope.client_order_id
            and execution_identity.final_quantity == envelope.quantity
            and execution_identity.quantity_unit == envelope.quantity_unit
            and execution_identity.order_type == envelope.order_type
            and execution_identity.order_price == envelope.price
        ):
            raise FullCoreExternalEffectDurableConsumeError("DURABLE_EXECUTION_ENVELOPE_MISMATCH")
    _assert_no_secrets(bound)
    with _writer_lock_v1(root):
        existing = load_external_effect_durable_consume_v1(store_root=root)
        if existing.get("durable_consumed") is True:
            record = existing.get("record") or {}
            if str(record.get("permit_id") or "") == permit.permit_id:
                raise FullCoreExternalEffectDurableConsumeError("CONSUMED_PERMIT")
            raise FullCoreExternalEffectDurableConsumeError(
                "DURABLE_CONSUME_ALREADY_PRESENT_NO_REWRITE"
            )
        path = durable_consume_path_v1(root)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(_canonical_json(bound) + "\n", encoding="utf-8")
        tmp.replace(path)
    return bound


def finalize_external_effect_durable_consume_v1(
    *,
    store_root: Path | str,
    permit_id: str,
    envelope_id: str,
    envelope_digest: str,
    outcome: str,
) -> dict[str, Any]:
    """Transition SENT_INITIATED → COMPLETED without permitting resubmit."""
    if store_root is None:
        raise FullCoreExternalEffectDurableConsumeError("DURABLE_STORE_REQUIRED")
    pid = str(permit_id or "").strip()
    eid = str(envelope_id or "").strip()
    digest = str(envelope_digest or "").strip()
    if not pid or not eid or len(digest) != 64:
        raise FullCoreExternalEffectDurableConsumeError("FINALIZE_IDENTITY_INVALID")
    existing = load_external_effect_durable_consume_v1(store_root=store_root)
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
    completed = dict(record)
    completed["durable_state"] = DURABLE_STATE_COMPLETED
    completed["outcome"] = str(outcome or "")
    completed["completed_at_utc"] = _utc_now_iso_v1()
    completed["resubmit_allowed"] = False
    completed["retry_allowed"] = False
    completed["second_submit_allowed"] = False
    _assert_no_secrets(completed)
    _validate_owned_identity_v2(completed)
    with _writer_lock_v1(Path(store_root)):
        if load_external_effect_durable_consume_v1(store_root=store_root).get("record") != record:
            raise FullCoreExternalEffectDurableConsumeError("DURABLE_FINALIZE_PARENT_CHANGED")
        path = durable_consume_path_v1(Path(store_root))
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(_canonical_json(completed) + "\n", encoding="utf-8")
        tmp.replace(path)
    return completed
