"""Scoped authorization gate for §11.13.2 LIVE_PRIVATE_READ_ONLY.

Default false. Consumable only for this runner/scope. Never sets LIVE_AUTHORIZED
or opens order/trading/arming gates. Not reusable for later Live stages.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any, Mapping

from src.ops.section_11_13_2_live_private_read_only_v1.constants_v1 import (
    AUTHORIZATION_SCOPE,
    AUTHORIZATION_SCOPE_ALIASES_FORBIDDEN,
    LIVE_ARMED,
    LIVE_AUTHORIZED,
    LIVE_ENABLED,
    LIVE_ORDER_AUTHORIZED,
    LIVE_PRIVATE_READ_ONLY_AUTHORIZED_DEFAULT,
    OWNER_GO_EXECUTE,
)


class LivePrivateRoAuthorizationError(RuntimeError):
    """Fail-closed scoped authorization violation."""


_SHA_RE = re.compile(r"^[0-9a-f]{7,64}$")


@dataclass(frozen=True)
class LivePrivateRoAuthorizationBindingV1:
    live_private_read_only_authorized: bool
    authorization_scope: str
    owner_go: str
    bound_origin_main_sha: str
    bound_config_digest: str
    live_authorized: bool = False
    live_enabled: bool = False
    live_armed: bool = False
    live_order_authorized: bool = False
    reusable_for_later_live_stages: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "LIVE_PRIVATE_READ_ONLY_AUTHORIZED": self.live_private_read_only_authorized,
            "authorization_scope": self.authorization_scope,
            "owner_go": self.owner_go,
            "bound_origin_main_sha": self.bound_origin_main_sha,
            "bound_config_digest": self.bound_config_digest,
            "LIVE_AUTHORIZED": self.live_authorized,
            "LIVE_ENABLED": self.live_enabled,
            "LIVE_ARMED": self.live_armed,
            "LIVE_ORDER_AUTHORIZED": self.live_order_authorized,
            "reusable_for_later_live_stages": self.reusable_for_later_live_stages,
        }


def default_authorization_is_false_v1() -> bool:
    return LIVE_PRIVATE_READ_ONLY_AUTHORIZED_DEFAULT is False


def _canonical_dumps(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def validate_live_private_read_only_authorization_v1(
    *,
    owner_go: str | None,
    authorization_scope: str | None,
    bound_origin_main_sha: str | None,
    expected_origin_main_sha: str | None,
    bound_config_digest: str | None,
    expected_config_digest: str | None,
    live_private_read_only_authorized: bool | None = None,
) -> LivePrivateRoAuthorizationBindingV1:
    """Validate scoped GO. Missing/wrong GO → no credential load, no network."""
    if live_private_read_only_authorized is None:
        authorized_flag = False
    else:
        authorized_flag = bool(live_private_read_only_authorized)

    if not authorized_flag:
        raise LivePrivateRoAuthorizationError("LIVE_PRIVATE_READ_ONLY_AUTHORIZED_FALSE")

    token = str(owner_go or "").strip()
    if not token:
        raise LivePrivateRoAuthorizationError("OWNER_GO_MISSING")
    if token != OWNER_GO_EXECUTE:
        raise LivePrivateRoAuthorizationError(f"OWNER_GO_MISMATCH:{token}")

    scope = str(authorization_scope or "").strip()
    if not scope:
        raise LivePrivateRoAuthorizationError("AUTHORIZATION_SCOPE_MISSING")
    if scope != AUTHORIZATION_SCOPE:
        raise LivePrivateRoAuthorizationError(f"AUTHORIZATION_SCOPE_MISMATCH:{scope}")
    if scope in AUTHORIZATION_SCOPE_ALIASES_FORBIDDEN:
        raise LivePrivateRoAuthorizationError(f"AUTHORIZATION_SCOPE_FORBIDDEN:{scope}")

    sha = str(bound_origin_main_sha or "").strip().lower()
    expected_sha = str(expected_origin_main_sha or "").strip().lower()
    if not sha or not _SHA_RE.match(sha):
        raise LivePrivateRoAuthorizationError("BOUND_ORIGIN_MAIN_SHA_INVALID")
    if not expected_sha or not _SHA_RE.match(expected_sha):
        raise LivePrivateRoAuthorizationError("EXPECTED_ORIGIN_MAIN_SHA_INVALID")
    if sha != expected_sha:
        raise LivePrivateRoAuthorizationError("ORIGIN_MAIN_SHA_MISMATCH")

    cfg = str(bound_config_digest or "").strip().lower()
    expected_cfg = str(expected_config_digest or "").strip().lower()
    if not cfg or len(cfg) != 64:
        raise LivePrivateRoAuthorizationError("BOUND_CONFIG_DIGEST_INVALID")
    if not expected_cfg or len(expected_cfg) != 64:
        raise LivePrivateRoAuthorizationError("EXPECTED_CONFIG_DIGEST_INVALID")
    if cfg != expected_cfg:
        raise LivePrivateRoAuthorizationError("CONFIG_DIGEST_MISMATCH")

    # Hard invariants: this GO must never flip broader Live gates.
    if LIVE_AUTHORIZED or LIVE_ENABLED or LIVE_ARMED or LIVE_ORDER_AUTHORIZED:
        raise LivePrivateRoAuthorizationError("STANDING_LIVE_GATES_MUST_REMAIN_FALSE")

    return LivePrivateRoAuthorizationBindingV1(
        live_private_read_only_authorized=True,
        authorization_scope=AUTHORIZATION_SCOPE,
        owner_go=OWNER_GO_EXECUTE,
        bound_origin_main_sha=sha,
        bound_config_digest=cfg,
        live_authorized=False,
        live_enabled=False,
        live_armed=False,
        live_order_authorized=False,
        reusable_for_later_live_stages=False,
    )


def authorization_binding_digest_v1(binding: LivePrivateRoAuthorizationBindingV1) -> str:
    return hashlib.sha256(_canonical_dumps(binding.to_dict()).encode("utf-8")).hexdigest()
