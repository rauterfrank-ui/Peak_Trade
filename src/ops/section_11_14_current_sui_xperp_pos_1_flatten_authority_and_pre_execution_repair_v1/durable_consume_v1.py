"""Durable single-use consume ledger for the §11.14 flatten harness.

Reuses restart-contract states. Does not POST. Does not mint Owner GO.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.evidence_v1 import write_json_v1
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.live_credential_ephemeral_v1 import (
    assert_no_plaintext_in_payload_v1,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.constants_v1 import (
    DURABLE_CONSUME_FILENAME,
    DURABLE_STATE_COMPLETED,
    DURABLE_STATE_INCOMPLETE,
    DURABLE_STATE_NONE,
)
from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.restart_contract_v1 import (
    reconstruct_flatten_durable_state_v1,
)


class FlattenDurableConsumeError(RuntimeError):
    """Fail-closed durable consume violation."""


def _utc_now_iso_v1() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def durable_consume_path_v1(store_root: Path | str) -> Path:
    return Path(store_root) / DURABLE_CONSUME_FILENAME


def load_flatten_durable_consume_v1(*, store_root: Path | str | None) -> dict[str, Any]:
    if store_root is None:
        reconstructed = reconstruct_flatten_durable_state_v1(None)
        return {
            "present": False,
            "consumed": False,
            "durable_consumed": False,
            "authority_id": "",
            "record": None,
            "reconstruction": reconstructed,
        }
    path = durable_consume_path_v1(store_root)
    if not path.is_file():
        reconstructed = reconstruct_flatten_durable_state_v1(None)
        return {
            "present": False,
            "consumed": False,
            "durable_consumed": False,
            "authority_id": "",
            "record": None,
            "reconstruction": reconstructed,
            "path": str(path),
        }
    import json

    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise FlattenDurableConsumeError("DURABLE_CONSUME_MALFORMED")
    reconstructed = reconstruct_flatten_durable_state_v1(payload)
    consumed = bool(payload.get("consumed")) is True
    state = str(payload.get("durable_state") or DURABLE_STATE_NONE)
    durable_consumed = consumed or state in {DURABLE_STATE_COMPLETED, DURABLE_STATE_INCOMPLETE}
    if reconstructed.get("resubmit_allowed") is True:
        raise FlattenDurableConsumeError("DURABLE_RESUBMIT_MUST_REMAIN_FALSE")
    return {
        "present": True,
        "consumed": consumed,
        "durable_consumed": durable_consumed,
        "authority_id": str(payload.get("authority_id") or ""),
        "record": payload,
        "reconstruction": reconstructed,
        "path": str(path),
    }


def persist_flatten_durable_consume_v1(
    *,
    store_root: Path | str,
    envelope_id: str,
    origin_main_sha: str,
    durable_state: str,
    post_count: int,
    outcome: str,
    raw_response: Mapping[str, Any] | None = None,
    authority_id: str = "",
) -> dict[str, Any]:
    """Persist consume before any retry-capable control flow. Atomic replace."""
    root = Path(store_root)
    root.mkdir(parents=True, exist_ok=True)
    if durable_state not in {DURABLE_STATE_COMPLETED, DURABLE_STATE_INCOMPLETE}:
        raise FlattenDurableConsumeError(f"DURABLE_STATE_FORBIDDEN:{durable_state}")
    existing = load_flatten_durable_consume_v1(store_root=root)
    if existing.get("durable_consumed") is True:
        raise FlattenDurableConsumeError("DURABLE_CONSUME_ALREADY_PRESENT_NO_REWRITE")
    bound_authority_id = str(authority_id or "").strip()
    record = {
        "durable_state": durable_state,
        "consumed": True,
        "resubmit_allowed": False,
        "retry_allowed": False,
        "second_submit_allowed": False,
        "envelope_id": str(envelope_id),
        "origin_main_sha": str(origin_main_sha).strip().lower(),
        "authority_id": bound_authority_id,
        "action_identity": bound_authority_id or str(envelope_id),
        "post_count": int(post_count),
        "outcome": str(outcome),
        "consumed_at_utc": _utc_now_iso_v1(),
        "raw_response_present": raw_response is not None,
        "raw_response_code": (
            str((raw_response or {}).get("code") or "") if raw_response is not None else ""
        ),
    }
    assert_no_plaintext_in_payload_v1(record)
    path = durable_consume_path_v1(root)
    tmp = path.with_suffix(path.suffix + ".tmp")
    write_json_v1(tmp, record)
    tmp.replace(path)
    return record
