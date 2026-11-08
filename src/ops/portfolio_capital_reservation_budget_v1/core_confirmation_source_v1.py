"""Original persisted C3 progress veto; never a fresh directional assessment."""

SCHEMA = "portfolio_original_core_c3_lineage.v1"
_TEXT_FIELDS = {"session_id", "venue", "repository_sha", "config_digest"}


def _lineage(cursor):
    state = cursor.cap61_confirmation_state
    if state is None:
        raise ValueError("CURRENT_CORE_C3_SOURCE_UNPROVEN")
    key = state.observation_acceptance_state.bound_instrument_key
    if (
        key is None
        or state.instrument_id != cursor.instrument_id
        or key.canonical_instrument_id != cursor.instrument_id
        or key.venue != state.venue
        or any(
            side.instrument != key or side.venue != state.venue
            for side in (
                state.confirmation_side_carrier.bull_confirmation_state,
                state.confirmation_side_carrier.bear_confirmation_state,
            )
        )
    ):
        raise ValueError("CURRENT_CORE_C3_SOURCE_IDENTITY_MISMATCH")
    return dict(
        schema=SCHEMA,
        session_id=state.confirmation_session_id,
        venue=state.venue,
        repository_sha=state.repository_sha,
        config_digest=state.config_digest,
        instrument_key=key.to_dict(),
    )


def validate_core_confirmation_lineage_v1(lineage, *, instrument_id):
    if (
        not isinstance(lineage, dict)
        or set(lineage) != {"schema", "instrument_key"} | _TEXT_FIELDS
        or lineage.get("schema") != SCHEMA
        or any(
            type(lineage[k]) is not str or not lineage[k] or lineage[k] != lineage[k].strip()
            for k in _TEXT_FIELDS
        )
        or not isinstance(lineage["instrument_key"], dict)
        or set(lineage["instrument_key"])
        != {"venue", "canonical_instrument_id", "venue_instrument_id"}
        or any(
            type(v) is not str or not v or v != v.strip()
            for v in lineage["instrument_key"].values()
        )
        or lineage["instrument_key"]["canonical_instrument_id"] != instrument_id
        or lineage["instrument_key"]["venue"] != lineage["venue"]
    ):
        raise ValueError("ORIGINAL_CORE_C3_LINEAGE_INVALID")


def bind_core_confirmation_lineage_v1(cursor):
    lineage = _lineage(cursor)
    validate_core_confirmation_lineage_v1(lineage, instrument_id=cursor.instrument_id)
    return lineage


def inspect_current_core_confirmation_v1(lineage, *, cursor, raw, intent_side):
    from src.ops.stateful_confirmation_and_c1_productive_binding_v1.constants_v1 import (
        CAPABILITY_ID,
        SCHEMA_VERSION,
    )
    from trading.market_state.directional_confirmation_progress_v1 import ConfirmationSideV1
    from trading.master_v2.directional_assessment_confirmation_integration_v1 import (
        map_confirmation_assessment_state_to_directional_status_v1,
    )
    from trading.master_v2.directional_assessment_v1 import DirectionalAssessmentStatus

    if _lineage(cursor) != lineage:
        raise ValueError("CURRENT_CORE_C3_LINEAGE_MISMATCH")
    state = cursor.cap61_confirmation_state
    body = raw["cap61_confirmation_state"]
    side = ConfirmationSideV1.LONG if intent_side == "LONG" else ConfirmationSideV1.SHORT
    progress = state.confirmation_side_carrier.for_side(side)
    selected = body["confirmation_side_carrier"][
        "bull_confirmation_state" if side is ConfirmationSideV1.LONG else "bear_confirmation_state"
    ]
    observation = state.observation_acceptance_state
    # The original restore adapter converts numbers. A string/bool is not proof
    # of a persisted integer C1/C2 ownership position at this consumer.
    numbers = [
        selected.get("distinct_confirmation_observation_count"),
        selected.get("latest_accepted_market_observation_epoch", {}).get("value"),
        body["observation_acceptance_state"].get("market_observation_epoch", {}).get("value"),
    ]
    if selected.get("candidate_started_at_epoch") is not None:
        numbers.append(selected["candidate_started_at_epoch"].get("value"))
    if (
        body.get("schema_version") != SCHEMA_VERSION
        or body.get("capability_id") != CAPABILITY_ID
        or any(type(n) is not int for n in numbers)
    ):
        raise ValueError("CURRENT_CORE_C3_STATE_UNPROVEN")
    status = map_confirmation_assessment_state_to_directional_status_v1(progress.assessment_state)
    if status is not DirectionalAssessmentStatus.CONFIRMED:
        raise ValueError("CURRENT_CORE_C3_SELECTED_SIDE_NOT_CONFIRMED")
    if (
        observation.last_accepted_observation_identity is None
        or observation.market_observation_epoch.value < 1
        or progress.last_processed_acceptor_result_fingerprint is None
        or progress.latest_accepted_market_observation_epoch != observation.market_observation_epoch
    ):
        raise ValueError("CURRENT_CORE_C3_OBSERVATION_NOT_ASSESSED")
    return dict(
        scope="CURRENT_ORIGINAL_C3_PROGRESS_VETO_ONLY",
        selected_side=side.value,
        confirmation_status=status.value,
        market_observation_epoch=observation.market_observation_epoch.value,
        runtime_authorization_effect="NONE",
    )
