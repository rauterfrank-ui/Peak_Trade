"""Scoped OWNER_GO consumer for ACTUAL productive §11.12.8 campaign start."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.constants_v1 import (
    ACCEPTED_OWNER_GO_AUTHORIZATIONS,
    ACCEPTED_OWNER_GO_SCOPES,
    CAPABILITY_ID,
    FORBIDDEN_SWAP_OWNER_GO_MARKERS,
    LIVE_AUTHORIZED,
    SCOPED_OWNER_GO_TOKEN,
)
from src.ops.section_11_12_8_okx_eea_demo_xperp_campaign_private_write_gate_v1.gate_v1 import (
    assert_deprecated_btc_usdt_swap_path_forbidden_v1,
)


class ActualStartOwnerGoError(RuntimeError):
    """Fail-closed OWNER_GO consumer violation."""


@dataclass(frozen=True)
class OwnerGoConsumptionV1:
    owner_go_token: str
    owner_go_scope: str
    owner_go_authorization: str
    consumed: bool
    one_time_consume: bool
    productive_campaign_authorized: bool
    live_authorized: bool
    consumption_id: str
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "owner_go_token": self.owner_go_token,
            "owner_go_scope": self.owner_go_scope,
            "owner_go_authorization": self.owner_go_authorization,
            "consumed": self.consumed,
            "one_time_consume": self.one_time_consume,
            "productive_campaign_authorized": self.productive_campaign_authorized,
            "live_authorized": self.live_authorized,
            "consumption_id": self.consumption_id,
            "reason": self.reason,
        }


_CONSUMED_IDS: set[str] = set()


def reset_owner_go_consumption_registry_v1() -> None:
    """Test-only reset of one-time consumption registry."""
    _CONSUMED_IDS.clear()


def consume_actual_start_owner_go_v1(
    *,
    owner_go_token: str,
    owner_go_scope: str,
    owner_go_authorization: str,
    consumption_id: str,
) -> OwnerGoConsumptionV1:
    token = str(owner_go_token or "").strip()
    scope = str(owner_go_scope or "").strip()
    authorization = str(owner_go_authorization or "").strip()
    cid = str(consumption_id or "").strip()
    if not cid:
        raise ActualStartOwnerGoError("OWNER_GO_CONSUMPTION_ID_REQUIRED")
    if token != SCOPED_OWNER_GO_TOKEN:
        raise ActualStartOwnerGoError(f"SCOPED_OWNER_GO_TOKEN_MISMATCH:{token}")
    try:
        assert_deprecated_btc_usdt_swap_path_forbidden_v1(
            owner_go_scope=scope,
            owner_go_authorization=authorization,
        )
    except Exception as exc:  # noqa: BLE001 — convert to Owner-GO fail-closed
        raise ActualStartOwnerGoError(str(exc)) from exc
    for marker in FORBIDDEN_SWAP_OWNER_GO_MARKERS:
        if marker.upper() in scope.upper() or marker.upper() in authorization.upper():
            raise ActualStartOwnerGoError(f"SWAP_OWNER_GO_SCOPE_NOT_CONSUMABLE:{marker}")
    if scope not in ACCEPTED_OWNER_GO_SCOPES:
        raise ActualStartOwnerGoError(f"SCOPED_OWNER_GO_SCOPE_MISMATCH:{scope}")
    if authorization not in ACCEPTED_OWNER_GO_AUTHORIZATIONS:
        raise ActualStartOwnerGoError(f"SCOPED_OWNER_GO_AUTHORIZATION_MISMATCH:{authorization}")
    if cid in _CONSUMED_IDS:
        raise ActualStartOwnerGoError(f"OWNER_GO_REPLAY_FORBIDDEN:{cid}")
    if LIVE_AUTHORIZED is not False:
        raise ActualStartOwnerGoError("LIVE_AUTHORIZED_CONSTANT_DRIFT")
    _CONSUMED_IDS.add(cid)
    return OwnerGoConsumptionV1(
        owner_go_token=token,
        owner_go_scope=scope,
        owner_go_authorization=authorization,
        consumed=True,
        one_time_consume=True,
        productive_campaign_authorized=True,
        live_authorized=False,
        consumption_id=cid,
        reason=f"CONSUMED_FOR_ACTUAL_PRODUCTIVE_START:{CAPABILITY_ID}",
    )
