"""Scoped authorization gate for §11.13.4 LIVE_DRY_RUN_ORDER_PLAN."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any, Mapping

from src.ops.section_11_13_4_live_dry_run_order_plan_v1.constants_v1 import (
    AUTHORIZATION_SCOPE,
    AUTHORIZATION_SCOPE_ALIASES_FORBIDDEN,
    LIVE_ARMED,
    LIVE_AUTHORIZED,
    LIVE_DRY_RUN_ORDER_PLAN_AUTHORIZED_DEFAULT,
    LIVE_ENABLED,
    LIVE_ORDER_AUTHORIZED,
    OWNER_GO_EXECUTE,
)


class LiveDryRunOrderPlanAuthorizationError(RuntimeError):
    """Fail-closed scoped authorization violation."""


_SHA_RE = re.compile(r"^[0-9a-f]{7,64}$")


@dataclass(frozen=True)
class LiveDryRunOrderPlanAuthorizationBindingV1:
    live_dry_run_order_plan_authorized: bool
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
            "LIVE_DRY_RUN_ORDER_PLAN_AUTHORIZED": self.live_dry_run_order_plan_authorized,
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
    return LIVE_DRY_RUN_ORDER_PLAN_AUTHORIZED_DEFAULT is False


def _canonical_dumps(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def validate_live_dry_run_order_plan_authorization_v1(
    *,
    owner_go: str | None,
    authorization_scope: str | None,
    bound_origin_main_sha: str | None,
    expected_origin_main_sha: str | None,
    bound_config_digest: str | None,
    expected_config_digest: str | None,
    live_dry_run_order_plan_authorized: bool | None = None,
) -> LiveDryRunOrderPlanAuthorizationBindingV1:
    if live_dry_run_order_plan_authorized is None:
        authorized_flag = False
    else:
        authorized_flag = bool(live_dry_run_order_plan_authorized)

    if not authorized_flag:
        raise LiveDryRunOrderPlanAuthorizationError("LIVE_DRY_RUN_ORDER_PLAN_AUTHORIZED_FALSE")

    token = str(owner_go or "").strip()
    if not token:
        raise LiveDryRunOrderPlanAuthorizationError("OWNER_GO_MISSING")
    if token != OWNER_GO_EXECUTE:
        raise LiveDryRunOrderPlanAuthorizationError(f"OWNER_GO_MISMATCH:{token}")

    scope = str(authorization_scope or "").strip()
    if not scope:
        raise LiveDryRunOrderPlanAuthorizationError("AUTHORIZATION_SCOPE_MISSING")
    if scope != AUTHORIZATION_SCOPE:
        raise LiveDryRunOrderPlanAuthorizationError(f"AUTHORIZATION_SCOPE_MISMATCH:{scope}")
    if scope in AUTHORIZATION_SCOPE_ALIASES_FORBIDDEN:
        raise LiveDryRunOrderPlanAuthorizationError(f"AUTHORIZATION_SCOPE_FORBIDDEN:{scope}")

    sha = str(bound_origin_main_sha or "").strip().lower()
    expected_sha = str(expected_origin_main_sha or "").strip().lower()
    if not sha or not _SHA_RE.match(sha):
        raise LiveDryRunOrderPlanAuthorizationError("BOUND_ORIGIN_MAIN_SHA_INVALID")
    if not expected_sha or not _SHA_RE.match(expected_sha):
        raise LiveDryRunOrderPlanAuthorizationError("EXPECTED_ORIGIN_MAIN_SHA_INVALID")
    if sha != expected_sha:
        raise LiveDryRunOrderPlanAuthorizationError("ORIGIN_MAIN_SHA_MISMATCH")

    cfg = str(bound_config_digest or "").strip().lower()
    expected_cfg = str(expected_config_digest or "").strip().lower()
    if not cfg or len(cfg) != 64:
        raise LiveDryRunOrderPlanAuthorizationError("BOUND_CONFIG_DIGEST_INVALID")
    if not expected_cfg or len(expected_cfg) != 64:
        raise LiveDryRunOrderPlanAuthorizationError("EXPECTED_CONFIG_DIGEST_INVALID")
    if cfg != expected_cfg:
        raise LiveDryRunOrderPlanAuthorizationError("CONFIG_DIGEST_MISMATCH")

    if LIVE_AUTHORIZED or LIVE_ENABLED or LIVE_ARMED or LIVE_ORDER_AUTHORIZED:
        raise LiveDryRunOrderPlanAuthorizationError("STANDING_LIVE_GATES_MUST_REMAIN_FALSE")

    return LiveDryRunOrderPlanAuthorizationBindingV1(
        live_dry_run_order_plan_authorized=True,
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


def authorization_binding_digest_v1(
    binding: LiveDryRunOrderPlanAuthorizationBindingV1,
) -> str:
    return hashlib.sha256(_canonical_dumps(binding.to_dict()).encode("utf-8")).hexdigest()
