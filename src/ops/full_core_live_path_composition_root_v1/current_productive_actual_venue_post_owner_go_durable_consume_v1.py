"""Durable single-use consume ledger for the actual-venue POST Owner-GO.

Module-level POST_GO_STATUS in the one-shot join remains UNCONSUMED for standing
boundary proofs. Productive execution consumes this durable record exactly once.

Does not POST. Does not load credentials.

RUNTIME_AUTHORIZATION_EFFECT=POST_OWNER_GO_DURABLE_CONSUME_ONLY
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Final, Mapping

POST_OWNER_GO = (
    "OWNER_GO_CURRENT_PRODUCTIVE_ACTUAL_VENUE_POST_WITH_FRESH_ENVELOPE_BOUND_SINGLE_USE_PERMIT_V1"
)

DURABLE_POST_OWNER_GO_FILENAME: Final[str] = (
    "full_core_current_productive_actual_venue_post_owner_go_consume_v1.json"
)
_SECRET_TOKENS = ("secret", "passphrase", "api_key", "apikey", "private_key")


class CurrentProductiveActualVenuePostOwnerGoConsumeError(RuntimeError):
    """Fail-closed POST Owner-GO durable consume violation."""


def _utc_now_iso_v1() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _assert_no_secrets(payload: Mapping[str, Any]) -> None:
    blob = _canonical_json(payload).lower()
    for token in _SECRET_TOKENS:
        if token in blob:
            raise CurrentProductiveActualVenuePostOwnerGoConsumeError(
                f"SECRET_TOKEN_PRESENT:{token}"
            )


def durable_post_owner_go_path_v1(store_root: Path | str) -> Path:
    return Path(store_root) / DURABLE_POST_OWNER_GO_FILENAME


def load_durable_post_owner_go_consume_v1(*, store_root: Path | str | None) -> dict[str, Any]:
    if store_root is None:
        return {
            "present": False,
            "consumed": False,
            "owner_go_token": "",
            "record": None,
        }
    path = durable_post_owner_go_path_v1(store_root)
    if not path.is_file():
        return {
            "present": False,
            "consumed": False,
            "owner_go_token": "",
            "record": None,
            "path": str(path),
        }
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise CurrentProductiveActualVenuePostOwnerGoConsumeError("DURABLE_POST_GO_MALFORMED")
    consumed = bool(payload.get("consumed")) is True
    token = str(payload.get("owner_go_token") or "")
    _assert_no_secrets(payload)
    return {
        "present": True,
        "consumed": consumed,
        "owner_go_token": token,
        "record": payload,
        "path": str(path),
    }


def persist_durable_post_owner_go_consume_v1(
    *,
    store_root: Path | str,
    owner_go_token: str,
    baseline_origin_main_sha: str,
) -> dict[str, Any]:
    """Atomically consume the POST Owner-GO before any transport-capable join."""
    if store_root is None:
        raise CurrentProductiveActualVenuePostOwnerGoConsumeError("DURABLE_STORE_REQUIRED")
    go = str(owner_go_token or "").strip()
    if go != POST_OWNER_GO:
        raise CurrentProductiveActualVenuePostOwnerGoConsumeError("POST_OWNER_GO_MISMATCH")
    sha = str(baseline_origin_main_sha or "").strip()
    if len(sha) != 40:
        raise CurrentProductiveActualVenuePostOwnerGoConsumeError("BASELINE_SHA_INVALID")
    existing = load_durable_post_owner_go_consume_v1(store_root=store_root)
    if existing.get("consumed") is True:
        raise CurrentProductiveActualVenuePostOwnerGoConsumeError("POST_OWNER_GO_ALREADY_CONSUMED")
    bound = {
        "consumed": True,
        "owner_go_token": go,
        "baseline_origin_main_sha": sha,
        "consumed_at_utc": _utc_now_iso_v1(),
        "retry_authorized": False,
        "second_post_authorized": False,
    }
    _assert_no_secrets(bound)
    root = Path(store_root)
    root.mkdir(parents=True, exist_ok=True)
    path = durable_post_owner_go_path_v1(root)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(_canonical_json(bound) + "\n", encoding="utf-8")
    tmp.replace(path)
    return bound


__all__ = [
    "DURABLE_POST_OWNER_GO_FILENAME",
    "CurrentProductiveActualVenuePostOwnerGoConsumeError",
    "durable_post_owner_go_path_v1",
    "load_durable_post_owner_go_consume_v1",
    "persist_durable_post_owner_go_consume_v1",
]
