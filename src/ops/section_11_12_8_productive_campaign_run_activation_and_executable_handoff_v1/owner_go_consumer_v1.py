"""Scoped OWNER_GO consumer for §11.12.8 activation + executable handoff."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.ops.section_11_12_8_productive_campaign_run_activation_and_executable_handoff_v1.constants_v1 import (
    CAPABILITY_ID,
    SCOPED_OWNER_GO_SCOPE,
    SCOPED_OWNER_GO_TOKEN,
)


class Section11128OwnerGoConsumerError(RuntimeError):
    """Fail-closed scoped OWNER_GO consumer violation."""


@dataclass(frozen=True)
class ScopedOwnerGoConsumptionV1:
    owner_go_token: str
    owner_go_scope: str
    consumed: bool
    productive_campaign_authorized: bool
    dry_activation_proof_authorized: bool
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "owner_go_token": self.owner_go_token,
            "owner_go_scope": self.owner_go_scope,
            "consumed": self.consumed,
            "productive_campaign_authorized": self.productive_campaign_authorized,
            "dry_activation_proof_authorized": self.dry_activation_proof_authorized,
            "reason": self.reason,
        }


def consume_scoped_owner_go_v1(
    *,
    owner_go_token: str,
    owner_go_scope: str,
    allow_productive_campaign_start: bool = False,
) -> ScopedOwnerGoConsumptionV1:
    """Consume the scoped activation OWNER_GO for dry proof only.

    Productive Testnet campaign start remains unauthorized under this token/scope.
    """
    token = str(owner_go_token or "").strip()
    scope = str(owner_go_scope or "").strip()
    if token != SCOPED_OWNER_GO_TOKEN:
        raise Section11128OwnerGoConsumerError(f"SCOPED_OWNER_GO_TOKEN_MISMATCH:{token}")
    if scope != SCOPED_OWNER_GO_SCOPE:
        raise Section11128OwnerGoConsumerError(f"SCOPED_OWNER_GO_SCOPE_MISMATCH:{scope}")
    if allow_productive_campaign_start:
        raise Section11128OwnerGoConsumerError(
            "PRODUCTIVE_TESTNET_CAMPAIGN_START_NOT_AUTHORIZED_BY_THIS_OWNER_GO"
        )
    return ScopedOwnerGoConsumptionV1(
        owner_go_token=token,
        owner_go_scope=scope,
        consumed=True,
        productive_campaign_authorized=False,
        dry_activation_proof_authorized=True,
        reason=f"CONSUMED_FOR_DRY_ACTIVATION_PROOF:{CAPABILITY_ID}",
    )
