"""Persisted lifecycle authority for RegimeSideStateProjectionPhaseV1 (no CZ-4 wire)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping, Tuple

from trading.master_v2.double_play_entry_exit_policy_v0 import ExistingPositionSide
from trading.master_v2.double_play_state import SideState

from src.ops.p5_7_regime_sidestate_projection_mapping_contract_v1.contract_v1 import (
    RegimeSideStateProjectionPhaseV1,
)
from src.ops.p5_8b_regime_sidestate_projection_phase_authority_v1.constants_v1 import (
    LIFECYCLE_SCHEMA_NAME,
    LIFECYCLE_SCHEMA_VERSION,
)

CONTRACT_OWNER = "ops.p5_8b_regime_sidestate_projection_phase_authority_v1.contract_v1"


class PhaseAuthorityFailureCodeV1(str, Enum):
    LIFECYCLE_INSTRUMENT_MISMATCH = "lifecycle_instrument_mismatch"
    LIFECYCLE_SCHEMA_MISMATCH = "lifecycle_schema_mismatch"
    LIFECYCLE_SCHEMA_VERSION_MISMATCH = "lifecycle_schema_version_mismatch"
    LIFECYCLE_PAYLOAD_INVALID = "lifecycle_payload_invalid"
    SEED_ALREADY_CONSUMED_NEUTRAL_OBSERVE = "seed_already_consumed_neutral_observe"
    SEED_REQUIRES_FLAT_VENUE = "seed_requires_flat_venue"
    SEED_REQUIRES_NO_POSITION = "seed_requires_no_position"


@dataclass(frozen=True)
class RegimeSideStateProjectionLifecycleStateV1:
    """Persisted SideState projection lifecycle (orientation seed consumed flag)."""

    schema_name: str
    schema_version: str
    instrument_id: str
    initial_regime_orientation_seed_consumed: bool


@dataclass(frozen=True)
class PhaseAuthorityResolutionResultV1:
    ok: bool
    phase: RegimeSideStateProjectionPhaseV1 | None
    failure_codes: Tuple[str, ...]
    lifecycle_after: RegimeSideStateProjectionLifecycleStateV1 | None


def fresh_regime_sidestate_projection_lifecycle_v1(
    *,
    instrument_id: str,
) -> RegimeSideStateProjectionLifecycleStateV1:
    """Fresh host lifecycle: orientation seed not yet consumed."""
    iid = str(instrument_id or "").strip()
    if not iid:
        raise ValueError("instrument_id_required")
    return RegimeSideStateProjectionLifecycleStateV1(
        schema_name=LIFECYCLE_SCHEMA_NAME,
        schema_version=LIFECYCLE_SCHEMA_VERSION,
        instrument_id=iid,
        initial_regime_orientation_seed_consumed=False,
    )


def lifecycle_to_dict_v1(
    state: RegimeSideStateProjectionLifecycleStateV1,
) -> dict[str, Any]:
    return {
        "schema_name": state.schema_name,
        "schema_version": state.schema_version,
        "instrument_id": state.instrument_id,
        "initial_regime_orientation_seed_consumed": bool(
            state.initial_regime_orientation_seed_consumed
        ),
    }


def parse_lifecycle_v1(
    payload: Mapping[str, Any] | None,
    *,
    expected_instrument_id: str | None = None,
) -> Tuple[RegimeSideStateProjectionLifecycleStateV1 | None, Tuple[str, ...]]:
    if payload is None:
        return None, (PhaseAuthorityFailureCodeV1.LIFECYCLE_PAYLOAD_INVALID.value,)
    if not isinstance(payload, Mapping):
        return None, (PhaseAuthorityFailureCodeV1.LIFECYCLE_PAYLOAD_INVALID.value,)
    schema_name = str(payload.get("schema_name") or "").strip()
    schema_version = str(payload.get("schema_version") or "").strip()
    instrument_id = str(payload.get("instrument_id") or "").strip()
    if schema_name != LIFECYCLE_SCHEMA_NAME:
        return None, (PhaseAuthorityFailureCodeV1.LIFECYCLE_SCHEMA_MISMATCH.value,)
    if schema_version != LIFECYCLE_SCHEMA_VERSION:
        return None, (PhaseAuthorityFailureCodeV1.LIFECYCLE_SCHEMA_VERSION_MISMATCH.value,)
    if not instrument_id:
        return None, (PhaseAuthorityFailureCodeV1.LIFECYCLE_PAYLOAD_INVALID.value,)
    if expected_instrument_id is not None and instrument_id != str(expected_instrument_id).strip():
        return None, (PhaseAuthorityFailureCodeV1.LIFECYCLE_INSTRUMENT_MISMATCH.value,)
    raw_consumed = payload.get("initial_regime_orientation_seed_consumed")
    if raw_consumed is not True and raw_consumed is not False:
        return None, (PhaseAuthorityFailureCodeV1.LIFECYCLE_PAYLOAD_INVALID.value,)
    return (
        RegimeSideStateProjectionLifecycleStateV1(
            schema_name=schema_name,
            schema_version=schema_version,
            instrument_id=instrument_id,
            initial_regime_orientation_seed_consumed=bool(raw_consumed),
        ),
        (),
    )


def mark_initial_regime_orientation_seed_consumed_v1(
    lifecycle: RegimeSideStateProjectionLifecycleStateV1,
) -> RegimeSideStateProjectionLifecycleStateV1:
    """Transition lifecycle after a successful INITIAL_SEED projection (bind prep)."""
    if lifecycle.initial_regime_orientation_seed_consumed:
        return lifecycle
    return RegimeSideStateProjectionLifecycleStateV1(
        schema_name=lifecycle.schema_name,
        schema_version=lifecycle.schema_version,
        instrument_id=lifecycle.instrument_id,
        initial_regime_orientation_seed_consumed=True,
    )


def resolve_regime_sidestate_projection_phase_v1(
    *,
    lifecycle: RegimeSideStateProjectionLifecycleStateV1,
    instrument_id: str,
    prior_side_state: SideState,
    venue_flat: bool,
    existing_position_side: ExistingPositionSide,
    switch_condition_met: bool,
    regime_pre_equals_post: bool,
) -> PhaseAuthorityResolutionResultV1:
    """Resolve P5.7 phase from persisted lifecycle + host occupancy (not from regime)."""
    iid = str(instrument_id or "").strip()
    if lifecycle.instrument_id != iid:
        return PhaseAuthorityResolutionResultV1(
            ok=False,
            phase=None,
            failure_codes=(PhaseAuthorityFailureCodeV1.LIFECYCLE_INSTRUMENT_MISMATCH.value,),
            lifecycle_after=None,
        )

    switched = switch_condition_met and not regime_pre_equals_post
    if switched:
        return PhaseAuthorityResolutionResultV1(
            ok=True,
            phase=RegimeSideStateProjectionPhaseV1.MECHANICAL_STEP,
            failure_codes=(),
            lifecycle_after=lifecycle,
        )

    if lifecycle.initial_regime_orientation_seed_consumed:
        if (
            prior_side_state is SideState.NEUTRAL_OBSERVE
            and venue_flat
            and existing_position_side is ExistingPositionSide.NONE
        ):
            return PhaseAuthorityResolutionResultV1(
                ok=False,
                phase=None,
                failure_codes=(
                    PhaseAuthorityFailureCodeV1.SEED_ALREADY_CONSUMED_NEUTRAL_OBSERVE.value,
                ),
                lifecycle_after=None,
            )
        return PhaseAuthorityResolutionResultV1(
            ok=True,
            phase=RegimeSideStateProjectionPhaseV1.MECHANICAL_STEP,
            failure_codes=(),
            lifecycle_after=lifecycle,
        )

    if prior_side_state is not SideState.NEUTRAL_OBSERVE:
        return PhaseAuthorityResolutionResultV1(
            ok=True,
            phase=RegimeSideStateProjectionPhaseV1.MECHANICAL_STEP,
            failure_codes=(),
            lifecycle_after=lifecycle,
        )
    if not venue_flat:
        return PhaseAuthorityResolutionResultV1(
            ok=False,
            phase=None,
            failure_codes=(PhaseAuthorityFailureCodeV1.SEED_REQUIRES_FLAT_VENUE.value,),
            lifecycle_after=None,
        )
    if existing_position_side is not ExistingPositionSide.NONE:
        return PhaseAuthorityResolutionResultV1(
            ok=False,
            phase=None,
            failure_codes=(PhaseAuthorityFailureCodeV1.SEED_REQUIRES_NO_POSITION.value,),
            lifecycle_after=None,
        )

    return PhaseAuthorityResolutionResultV1(
        ok=True,
        phase=RegimeSideStateProjectionPhaseV1.INITIAL_SEED,
        failure_codes=(),
        lifecycle_after=lifecycle,
    )


__all__ = [
    "CONTRACT_OWNER",
    "PhaseAuthorityFailureCodeV1",
    "PhaseAuthorityResolutionResultV1",
    "RegimeSideStateProjectionLifecycleStateV1",
    "fresh_regime_sidestate_projection_lifecycle_v1",
    "lifecycle_to_dict_v1",
    "mark_initial_regime_orientation_seed_consumed_v1",
    "parse_lifecycle_v1",
    "resolve_regime_sidestate_projection_phase_v1",
]
