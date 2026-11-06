"""Instrument-sensitive lane identity and state carry adjudication."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import Enum
from typing import Mapping

from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1


class InstrumentSensitiveStateClass(str, Enum):
    CAP23_HYSTERESIS = "cap23_hysteresis"
    CAP24_BINDING = "cap24_binding"
    CONFIRMATION_CURSOR = "confirmation_cursor"
    SIDE_STATE = "side_state"
    RUNTIME_SCOPE = "runtime_scope"
    HOST_EXIT_POLICY = "host_exit_policy"
    G17_TYPED_VOL = "g17_typed_vol"
    FEATURE_REGIME_CMC = "feature_regime_cmc"
    MV2_DP_STATE = "mv2_dp_state"
    RECONCILIATION = "reconciliation"
    TREASURY_CACHE = "treasury_cache"
    RESERVATION = "reservation"
    CAPITAL_SLOT = "capital_slot"
    EVIDENCE_REPLAY = "evidence_replay"


class StateCarryDisposition(str, Enum):
    RESET = "RESET"
    REKEY = "REKEY"
    RECONCILE = "RECONCILE"
    SAFE_CARRY = "SAFE_CARRY"


@dataclass(frozen=True)
class BoundInstrumentLaneIdentityV1:
    lane_id: str
    bound_instrument_identity: str
    instrument_epoch: str

    @staticmethod
    def from_bound_instrument(
        *, lane_id: str, bound: BoundInstrumentV1
    ) -> BoundInstrumentLaneIdentityV1:
        identity_material = (
            f"{bound.instrument_id}|{bound.venue_native_id}|"
            f"{bound.selection_id}|{bound.selection_integrity_digest}|"
            f"{bound.ranking_snapshot_id}|{bound.ranking_integrity_digest}"
        )
        bound_id = hashlib.sha256(identity_material.encode("utf-8")).hexdigest()
        epoch_material = f"{lane_id}|{bound_id}|{bound.universe_snapshot_id}"
        epoch = hashlib.sha256(epoch_material.encode("utf-8")).hexdigest()
        return BoundInstrumentLaneIdentityV1(
            lane_id=str(lane_id),
            bound_instrument_identity=bound_id,
            instrument_epoch=epoch,
        )


def adjudicate_instrument_sensitive_state_v1(
    *,
    state_class: InstrumentSensitiveStateClass,
    prior_identity: BoundInstrumentLaneIdentityV1 | None,
    current_identity: BoundInstrumentLaneIdentityV1,
) -> StateCarryDisposition:
    if prior_identity is None:
        return StateCarryDisposition.RESET
    if prior_identity.lane_id != current_identity.lane_id:
        return StateCarryDisposition.RESET
    if prior_identity.bound_instrument_identity != current_identity.bound_instrument_identity:
        return StateCarryDisposition.RESET
    if prior_identity.instrument_epoch != current_identity.instrument_epoch:
        return StateCarryDisposition.REKEY
    if state_class in {
        InstrumentSensitiveStateClass.RECONCILIATION,
        InstrumentSensitiveStateClass.TREASURY_CACHE,
        InstrumentSensitiveStateClass.RESERVATION,
    }:
        return StateCarryDisposition.RECONCILE
    return StateCarryDisposition.SAFE_CARRY


def cursor_restore_allowed_for_identity_v1(
    *,
    cursor_instrument_id: str,
    cursor_lane_epoch: str | None,
    expected: BoundInstrumentLaneIdentityV1,
    bound_instrument_id: str,
) -> bool:
    if cursor_instrument_id != bound_instrument_id:
        return False
    if cursor_lane_epoch is not None and cursor_lane_epoch != expected.instrument_epoch:
        return False
    return True


def reservation_identity_material_v1(
    *,
    lane_identity: BoundInstrumentLaneIdentityV1,
    decision_id: str,
    cycle_id: str,
    observation_id: str,
) -> Mapping[str, str]:
    return {
        "lane_id": lane_identity.lane_id,
        "instrument_epoch": lane_identity.instrument_epoch,
        "bound_instrument_identity": lane_identity.bound_instrument_identity,
        "decision_id": decision_id,
        "cycle_id": cycle_id,
        "observation_id": observation_id,
    }
