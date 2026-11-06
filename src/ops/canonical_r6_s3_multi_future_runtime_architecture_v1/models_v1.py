"""Fail-closed models for R6 S3 Phase-8.2 runtime architecture v1."""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping


class R6S3RuntimeArchitectureError(ValueError):
    """Fail-closed R6 S3 runtime-architecture error."""


def _freeze_mapping(payload: Mapping[str, Any] | None) -> Mapping[str, Any]:
    return MappingProxyType(dict(payload or {}))


@dataclass(frozen=True)
class RankingCandidateV1:
    instrument_id: str
    rank: int
    eligible: bool = True

    def to_mapping(self) -> Mapping[str, Any]:
        return MappingProxyType(
            {
                "instrument_id": self.instrument_id,
                "rank": int(self.rank),
                "eligible": bool(self.eligible),
            }
        )


@dataclass(frozen=True)
class InstrumentContextV1:
    instrument_id: str
    directional_side: str = "FLAT"
    position_qty: str = "0"
    reconciliation_status: str = "RECONCILED"
    intended_action: str = "HOLD"
    intended_side: str = "FLAT"
    intended_qty: str = "0"
    single_use_permission: bool = False
    isolated_state: Mapping[str, Any] = field(default_factory=dict)
    kill_switch_tripped: bool = False
    stale: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "isolated_state", _freeze_mapping(self.isolated_state))

    def to_mapping(self) -> Mapping[str, Any]:
        return MappingProxyType(
            {
                "instrument_id": self.instrument_id,
                "directional_side": self.directional_side,
                "position_qty": self.position_qty,
                "reconciliation_status": self.reconciliation_status,
                "intended_action": self.intended_action,
                "intended_side": self.intended_side,
                "intended_qty": self.intended_qty,
                "single_use_permission": bool(self.single_use_permission),
                "isolated_state": dict(self.isolated_state),
                "kill_switch_tripped": bool(self.kill_switch_tripped),
                "stale": bool(self.stale),
            }
        )


@dataclass(frozen=True)
class IntentV1:
    instrument_id: str
    action: str
    side: str
    qty: str
    blocked: bool = False
    block_reasons: tuple[str, ...] = ()
    sequence: int = 0
    source_stage: str = "per_instrument"

    def restrict(
        self,
        *,
        qty: str | None = None,
        reason: str,
        block: bool = False,
        source_stage: str | None = None,
    ) -> IntentV1:
        reasons = self.block_reasons + (reason,)
        return IntentV1(
            instrument_id=self.instrument_id,
            action=self.action,
            side=self.side,
            qty=self.qty if qty is None else qty,
            blocked=bool(self.blocked or block),
            block_reasons=reasons,
            sequence=self.sequence,
            source_stage=source_stage or self.source_stage,
        )

    def to_mapping(self) -> Mapping[str, Any]:
        return MappingProxyType(
            {
                "instrument_id": self.instrument_id,
                "action": self.action,
                "side": self.side,
                "qty": self.qty,
                "blocked": bool(self.blocked),
                "block_reasons": list(self.block_reasons),
                "sequence": int(self.sequence),
                "source_stage": self.source_stage,
            }
        )


@dataclass(frozen=True)
class WriterBundleV1:
    execution_writer_identity: str
    accounting_writer_identity: str
    intents: tuple[IntentV1, ...]
    durable_before_submit: bool = True
    submit_unlocked: bool = False

    def to_mapping(self) -> Mapping[str, Any]:
        return MappingProxyType(
            {
                "execution_writer_identity": self.execution_writer_identity,
                "accounting_writer_identity": self.accounting_writer_identity,
                "intents": [intent.to_mapping() for intent in self.intents],
                "durable_before_submit": bool(self.durable_before_submit),
                "submit_unlocked": bool(self.submit_unlocked),
                "execution_writer_count": 1,
                "accounting_writer_count": 1,
            }
        )


@dataclass(frozen=True)
class Phase82GraphRequestV1:
    selected_future_id: str
    ranking_candidates: tuple[RankingCandidateV1, ...] = ()
    instrument_contexts: tuple[InstrumentContextV1, ...] = ()
    requested_authorized: bool | None = None
    requested_implemented: bool | None = None
    global_kill_switch: bool = False
    economic_evidence_pass: bool = False
    research_signal_pass: bool = False
    restart_snapshot: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        if self.restart_snapshot is not None:
            object.__setattr__(self, "restart_snapshot", _freeze_mapping(self.restart_snapshot))


@dataclass(frozen=True)
class Phase82GraphResultV1:
    implemented: bool
    authorized: bool
    effective_runtime_mode: str
    max_positions_effective: int
    effective_active_ids: tuple[str, ...]
    candidate_ids: tuple[str, ...]
    isolated_contexts: Mapping[str, Mapping[str, Any]]
    pipeline_intents: tuple[IntentV1, ...]
    portfolio_intents: tuple[IntentV1, ...]
    safety_intents: tuple[IntentV1, ...]
    arbitrated_intents: tuple[IntentV1, ...]
    writer_bundle: WriterBundleV1
    stage_order: tuple[str, ...]
    submit_unlocked: bool
    live_authorized: bool
    testnet_authorized: bool
    canary_authorized: bool
    order_effect: str
    claims: Mapping[str, Any]

    def to_mapping(self) -> Mapping[str, Any]:
        return MappingProxyType(
            {
                "implemented": bool(self.implemented),
                "authorized": bool(self.authorized),
                "effective_runtime_mode": self.effective_runtime_mode,
                "max_positions_effective": int(self.max_positions_effective),
                "effective_active_ids": list(self.effective_active_ids),
                "candidate_ids": list(self.candidate_ids),
                "isolated_contexts": {
                    key: dict(value) for key, value in self.isolated_contexts.items()
                },
                "pipeline_intents": [intent.to_mapping() for intent in self.pipeline_intents],
                "portfolio_intents": [intent.to_mapping() for intent in self.portfolio_intents],
                "safety_intents": [intent.to_mapping() for intent in self.safety_intents],
                "arbitrated_intents": [intent.to_mapping() for intent in self.arbitrated_intents],
                "writer_bundle": dict(self.writer_bundle.to_mapping()),
                "stage_order": list(self.stage_order),
                "submit_unlocked": bool(self.submit_unlocked),
                "live_authorized": bool(self.live_authorized),
                "testnet_authorized": bool(self.testnet_authorized),
                "canary_authorized": bool(self.canary_authorized),
                "order_effect": self.order_effect,
                "claims": dict(self.claims),
            }
        )
