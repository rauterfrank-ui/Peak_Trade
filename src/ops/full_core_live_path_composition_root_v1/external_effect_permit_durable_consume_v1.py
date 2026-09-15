"""Durable single-use consume ledger for Full-Core envelope-bound permits.

Atomic replace before any retry-capable control flow. In-memory consume is
not crash-safe and cannot authorize send. Replay and second submit remain
denied after SENT_INITIATED or COMPLETED.

Does not POST. Does not load credentials.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from src.ops.full_core_live_path_composition_root_v1.external_effect_permit_v1 import (
    ExternalEffectPermitV1,
)
from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
    FinalOrderEnvelopeV1,
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
    if durable_state not in _CONSUMED_STATES:
        raise FullCoreExternalEffectDurableConsumeError(f"DURABLE_STATE_FORBIDDEN:{durable_state}")
    if int(post_count) > 1:
        raise FullCoreExternalEffectDurableConsumeError("POST_COUNT_EXCEEDS_ONE")
    root = Path(store_root)
    root.mkdir(parents=True, exist_ok=True)
    existing = load_external_effect_durable_consume_v1(store_root=root)
    if existing.get("durable_consumed") is True:
        record = existing.get("record") or {}
        if str(record.get("permit_id") or "") == permit.permit_id:
            raise FullCoreExternalEffectDurableConsumeError("CONSUMED_PERMIT")
        raise FullCoreExternalEffectDurableConsumeError(
            "DURABLE_CONSUME_ALREADY_PRESENT_NO_REWRITE"
        )
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
    _assert_no_secrets(bound)
    path = durable_consume_path_v1(root)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(_canonical_json(bound) + "\n", encoding="utf-8")
    tmp.replace(path)
    return bound
