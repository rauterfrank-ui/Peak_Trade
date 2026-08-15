"""Fail-closed models for R4 I17 PRODUCTIVE_SHADOW contract readiness v1."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping


class I17ShadowContractReadinessError(ValueError):
    """Fail-closed R4 I17 shadow contract/readiness error."""


class ShadowMode(str, Enum):
    PRODUCTIVE_SHADOW = "PRODUCTIVE_SHADOW"
    SHADOW = "SHADOW"
    PAPER = "PAPER"
    SIMULATION = "SIMULATION"
    FORWARD_SIGNAL_ONLY = "FORWARD_SIGNAL_ONLY"
    OBSERVATION = "OBSERVATION"
    TESTNET = "TESTNET"
    LIVE = "LIVE"
    CANARY = "CANARY"


class TerminalState(str, Enum):
    CONTRACT_READY_NOT_EXECUTED = "CONTRACT_READY_NOT_EXECUTED"
    PREFLIGHT_FAIL = "PREFLIGHT_FAIL"
    BLOCKED_PENDING_SHADOW_EXECUTE_GO = "BLOCKED_PENDING_SHADOW_EXECUTE_GO"


I17_ADMISSIBLE_MODES = frozenset(
    {
        ShadowMode.PRODUCTIVE_SHADOW,
        ShadowMode.OBSERVATION,
    }
)
SUBSTITUTE_MODES = frozenset(
    {
        ShadowMode.PAPER,
        ShadowMode.SIMULATION,
        ShadowMode.FORWARD_SIGNAL_ONLY,
        ShadowMode.SHADOW,
        ShadowMode.TESTNET,
        ShadowMode.LIVE,
        ShadowMode.CANARY,
    }
)


@dataclass(frozen=True)
class IdentityPlanesV1:
    experiment_identity_id: str
    run_id: str
    campaign_id: str
    session_id: str
    evidence_ref: str
    content_sha256: str
    legacy_alias_md5_12: str | None = None

    def to_mapping(self) -> Mapping[str, Any]:
        return MappingProxyType(
            {
                "campaign_id": self.campaign_id,
                "content_sha256": self.content_sha256,
                "evidence_ref": self.evidence_ref,
                "experiment_identity_id": self.experiment_identity_id,
                "legacy_alias_md5_12": self.legacy_alias_md5_12,
                "run_id": self.run_id,
                "session_id": self.session_id,
            }
        )


@dataclass(frozen=True)
class ShadowReadinessInputV1:
    mode: ShadowMode
    strategy_id: str
    identity: IdentityPlanesV1
    origin_main_sha: str
    claim_i17: bool = True
    regime_id: str | None = None
    execute: bool = False
    network_enabled: bool = False
    orders_enabled: bool = False
    live_enabled: bool = False
    testnet_enabled: bool = False
    canary_enabled: bool = False
    promotion_authority: bool = False
    auto_promote: bool = False
    i57_as_i17: bool = False
    i67_as_i17: bool = False
    md5_as_canonical_ref: bool = False
