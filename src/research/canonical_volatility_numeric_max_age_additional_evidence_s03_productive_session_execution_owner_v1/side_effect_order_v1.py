"""Consume-before-side-effects ordering for S03 execution owner."""

from __future__ import annotations

from typing import Sequence

from research.canonical_volatility_numeric_max_age_additional_evidence_s03_productive_session_execution_owner_v1.constants_v1 import (
    CONSUME_BEFORE_SIDE_EFFECTS,
    FORBIDDEN_SIDE_EFFECT_BEFORE_CONSUME,
    SESSION_LOCK_BEFORE_NETWORK,
    SIDE_EFFECT_AUTHORIZATION_CONSUMED,
    SIDE_EFFECT_NETWORK,
    SIDE_EFFECT_SESSION_LOCK,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_s03_productive_session_execution_owner_v1.models_v1 import (
    AdditionalEvidenceS03SessionExecutionOwnerError,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_authorization_v2.side_effect_order_v2 import (
    assert_consume_before_side_effects_v2,
)


def assert_s03_consume_before_side_effects_v1(probe: Sequence[str]) -> None:
    if not CONSUME_BEFORE_SIDE_EFFECTS:
        raise AdditionalEvidenceS03SessionExecutionOwnerError(
            "consume_before_side_effects_disabled"
        )
    # Reuse Auth-v2 vocabulary/order assertion.
    assert_consume_before_side_effects_v2(list(probe))
    events = list(probe)
    if SIDE_EFFECT_NETWORK in events:
        net_idx = events.index(SIDE_EFFECT_NETWORK)
        if SIDE_EFFECT_AUTHORIZATION_CONSUMED not in events:
            raise AdditionalEvidenceS03SessionExecutionOwnerError("network_before_consume")
        if events.index(SIDE_EFFECT_AUTHORIZATION_CONSUMED) > net_idx:
            raise AdditionalEvidenceS03SessionExecutionOwnerError("network_before_consume")
        if SESSION_LOCK_BEFORE_NETWORK:
            if SIDE_EFFECT_SESSION_LOCK not in events:
                raise AdditionalEvidenceS03SessionExecutionOwnerError(
                    "network_without_session_lock"
                )
            if events.index(SIDE_EFFECT_SESSION_LOCK) > net_idx:
                raise AdditionalEvidenceS03SessionExecutionOwnerError("network_before_session_lock")


def assert_no_forbidden_before_consume_v1(probe: Sequence[str]) -> None:
    events = list(probe)
    consume_idx = (
        events.index(SIDE_EFFECT_AUTHORIZATION_CONSUMED)
        if SIDE_EFFECT_AUTHORIZATION_CONSUMED in events
        else None
    )
    for idx, event in enumerate(events):
        if event in FORBIDDEN_SIDE_EFFECT_BEFORE_CONSUME:
            if consume_idx is None or idx < consume_idx:
                raise AdditionalEvidenceS03SessionExecutionOwnerError(
                    f"side_effect_before_consume:{event}"
                )
