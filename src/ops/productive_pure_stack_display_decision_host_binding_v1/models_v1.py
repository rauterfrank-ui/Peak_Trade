"""Typed models for the Pure-Stack display-decision bundle (non-authority)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Optional, Tuple

from trading.master_v2.double_play_capital_slot import (
    CapitalSlotRatchetDecision,
    CapitalSlotReleaseDecision,
)
from trading.master_v2.double_play_composition import DoublePlayCompositionDecision
from trading.master_v2.double_play_futures_input import FuturesInputReadinessDecision
from trading.master_v2.double_play_state import TransitionDecision
from trading.master_v2.double_play_suitability import SuitabilityProjectionDecision
from trading.master_v2.double_play_survival import SurvivalEnvelopeDecision

from src.ops.productive_pure_stack_display_decision_host_binding_v1.constants_v1 import (
    CAPABILITY_ID,
    OWNER,
    SCHEMA_VERSION,
    STATUS_BLOCKED_CANONICAL_INPUT_AUTHORITY_ABSENT,
)


@dataclass(frozen=True)
class PureStackDisplayDecisionBundleV1:
    """Canonical typed carrier for the seven Pure-Stack display Decisions.

    Authority-neutral transport for dashboard consumption only. Contains no
    presentation fields. All seven Decision fields are required when status
    is ready; partial bundles are rejected fail-closed.
    """

    schema_version: str
    capability_id: str
    owner: str
    cycle_id: str
    cycle_index: int
    instrument_id: str
    trading_epoch: int
    created_at: str
    status: str
    futures_input: FuturesInputReadinessDecision
    transition: TransitionDecision
    survival: SurvivalEnvelopeDecision
    suitability: SuitabilityProjectionDecision
    capital_slot_ratchet: CapitalSlotRatchetDecision
    capital_slot_release: CapitalSlotReleaseDecision
    composition: DoublePlayCompositionDecision
    bundle_digest: str = ""
    missing_authorities: Tuple[str, ...] = ()
    blockers: Tuple[str, ...] = ()

    def as_decision_mapping(self) -> Mapping[str, Any]:
        return {
            "futures_input": self.futures_input,
            "transition": self.transition,
            "survival": self.survival,
            "suitability": self.suitability,
            "capital_slot_ratchet": self.capital_slot_ratchet,
            "capital_slot_release": self.capital_slot_release,
            "composition": self.composition,
        }


@dataclass(frozen=True)
class PureStackInputAuthorityProbeV1:
    input_name: str
    authority_present: bool
    authority_owner: str
    detail: str


@dataclass
class PureStackDisplayDecisionHostResultV1:
    ok: bool
    status: str
    capability_id: str = CAPABILITY_ID
    owner: str = OWNER
    schema_version: str = SCHEMA_VERSION
    bundle: Optional[PureStackDisplayDecisionBundleV1] = None
    transition_passthrough: Optional[TransitionDecision] = None
    transition_identity_proven: bool = False
    missing_authorities: Tuple[str, ...] = ()
    blockers: Tuple[str, ...] = ()
    persisted: bool = False
    persist_path: str = ""
    bundle_digest: str = ""
    capital_slot_state_persisted: bool = False
    runtime_mutated: bool = False
    archive_mutated: bool = False
    notes: Tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "status": self.status,
            "capability_id": self.capability_id,
            "owner": self.owner,
            "schema_version": self.schema_version,
            "transition_identity_proven": self.transition_identity_proven,
            "missing_authorities": list(self.missing_authorities),
            "blockers": list(self.blockers),
            "persisted": self.persisted,
            "persist_path": self.persist_path,
            "bundle_digest": self.bundle_digest,
            "capital_slot_state_persisted": self.capital_slot_state_persisted,
            "runtime_mutated": self.runtime_mutated,
            "archive_mutated": self.archive_mutated,
            "bundle_present": self.bundle is not None,
            "notes": list(self.notes),
        }


def blocked_authority_result(
    *,
    missing_authorities: Tuple[str, ...],
    transition_passthrough: Optional[TransitionDecision] = None,
    transition_identity_proven: bool = False,
    notes: Tuple[str, ...] = (),
) -> PureStackDisplayDecisionHostResultV1:
    return PureStackDisplayDecisionHostResultV1(
        ok=False,
        status=STATUS_BLOCKED_CANONICAL_INPUT_AUTHORITY_ABSENT,
        transition_passthrough=transition_passthrough,
        transition_identity_proven=transition_identity_proven,
        missing_authorities=missing_authorities,
        blockers=(STATUS_BLOCKED_CANONICAL_INPUT_AUTHORITY_ABSENT,),
        runtime_mutated=False,
        archive_mutated=False,
        notes=notes,
    )
