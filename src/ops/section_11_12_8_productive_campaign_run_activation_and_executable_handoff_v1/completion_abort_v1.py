"""Completion and abort handling for §11.12.8 dry activation chain."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.ops.section_11_12_8_productive_campaign_run_activation_and_executable_handoff_v1.constants_v1 import (
    MODE_ABORT_DRY_ACTIVATION,
    MODE_COMPLETE_DRY_ACTIVATION,
    PRODUCTIVE_TESTNET_CAMPAIGN_STARTED,
)


class Section11128CompletionAbortError(RuntimeError):
    """Fail-closed completion/abort violation."""


@dataclass(frozen=True)
class CompletionAbortRecordV1:
    mode: str
    completed: bool
    aborted: bool
    campaign_started: bool
    network_effect: str
    order_effect: str
    live_order_effect: str
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "completed": self.completed,
            "aborted": self.aborted,
            "campaign_started": self.campaign_started,
            "network_effect": self.network_effect,
            "order_effect": self.order_effect,
            "live_order_effect": self.live_order_effect,
            "reason": self.reason,
        }


def complete_dry_activation_v1(
    *, reason: str = "DRY_ACTIVATION_CHAIN_COMPLETE"
) -> CompletionAbortRecordV1:
    if PRODUCTIVE_TESTNET_CAMPAIGN_STARTED is not False:
        raise Section11128CompletionAbortError("CAMPAIGN_STARTED_MUST_REMAIN_FALSE")
    return CompletionAbortRecordV1(
        mode=MODE_COMPLETE_DRY_ACTIVATION,
        completed=True,
        aborted=False,
        campaign_started=False,
        network_effect="NONE",
        order_effect="NONE",
        live_order_effect="NONE",
        reason=reason,
    )


def abort_dry_activation_v1(*, reason: str = "DRY_ACTIVATION_ABORT") -> CompletionAbortRecordV1:
    if PRODUCTIVE_TESTNET_CAMPAIGN_STARTED is not False:
        raise Section11128CompletionAbortError("CAMPAIGN_STARTED_MUST_REMAIN_FALSE")
    return CompletionAbortRecordV1(
        mode=MODE_ABORT_DRY_ACTIVATION,
        completed=False,
        aborted=True,
        campaign_started=False,
        network_effect="NONE",
        order_effect="NONE",
        live_order_effect="NONE",
        reason=reason,
    )
