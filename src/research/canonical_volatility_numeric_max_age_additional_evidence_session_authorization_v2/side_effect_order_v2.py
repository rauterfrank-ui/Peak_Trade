"""Consume-before-side-effects ordering helpers (testable, no runtime start)."""

from __future__ import annotations

from typing import Sequence

from research.canonical_volatility_numeric_max_age_additional_evidence_session_authorization_v2.constants_v2 import (
    CONSUME_BEFORE_EVIDENCE_CREATION,
    CONSUME_BEFORE_NETWORK,
    CONSUME_BEFORE_RUNTIME_INITIALIZATION,
    CONSUME_BEFORE_SESSION_LOCK,
    FORBIDDEN_SIDE_EFFECT_BEFORE_CONSUME,
    SIDE_EFFECT_AUTHORIZATION_CONSUMED,
    SIDE_EFFECT_EVIDENCE_CREATION,
    SIDE_EFFECT_NETWORK,
    SIDE_EFFECT_RUNTIME_INITIALIZATION,
    SIDE_EFFECT_SESSION_LOCK,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_authorization_v2.models_v2 import (
    AdditionalEvidenceSessionAuthorizationV2Error,
)


def assert_consume_before_side_effects_v2(probe: Sequence[str]) -> None:
    """Fail-closed if forbidden side effects appear before AUTHORIZATION_CONSUMED."""
    events = list(probe)
    consume_idx = (
        events.index(SIDE_EFFECT_AUTHORIZATION_CONSUMED)
        if SIDE_EFFECT_AUTHORIZATION_CONSUMED in events
        else None
    )
    for idx, event in enumerate(events):
        if event in FORBIDDEN_SIDE_EFFECT_BEFORE_CONSUME:
            if consume_idx is None or idx < consume_idx:
                raise AdditionalEvidenceSessionAuthorizationV2Error(
                    f"side_effect_before_consume:{event}"
                )


def assert_consume_before_invariants_v2() -> dict[str, bool]:
    if not (
        CONSUME_BEFORE_SESSION_LOCK
        and CONSUME_BEFORE_EVIDENCE_CREATION
        and CONSUME_BEFORE_NETWORK
        and CONSUME_BEFORE_RUNTIME_INITIALIZATION
    ):
        raise AdditionalEvidenceSessionAuthorizationV2Error("consume_before_invariant_drift")
    return {
        "CONSUME_BEFORE_SESSION_LOCK": CONSUME_BEFORE_SESSION_LOCK,
        "CONSUME_BEFORE_EVIDENCE_CREATION": CONSUME_BEFORE_EVIDENCE_CREATION,
        "CONSUME_BEFORE_NETWORK": CONSUME_BEFORE_NETWORK,
        "CONSUME_BEFORE_RUNTIME_INITIALIZATION": CONSUME_BEFORE_RUNTIME_INITIALIZATION,
        "SESSION_LOCK": SIDE_EFFECT_SESSION_LOCK,
        "EVIDENCE_CREATION": SIDE_EFFECT_EVIDENCE_CREATION,
        "NETWORK": SIDE_EFFECT_NETWORK,
        "RUNTIME_INITIALIZATION": SIDE_EFFECT_RUNTIME_INITIALIZATION,
    }
