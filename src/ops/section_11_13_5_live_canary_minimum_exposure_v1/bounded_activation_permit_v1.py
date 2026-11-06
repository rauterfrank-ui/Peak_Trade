"""Bounded activation permit — narrower than global LIVE_AUTHORIZED.

Invocation-scoped only. Standing live flags remain false. This module never
sets LIVE_AUTHORIZED, LIVE_ENABLED, LIVE_ARMED, network_session_authorized,
or flatten live-wire true. Missing, expired, or wrongly bound permit evidence
denies. Implementation Owner-GOs cannot satisfy the permit. Presence of the
canonical expected owner-go string in source is not runtime activation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    DEFAULT_INSTRUMENT_ID,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.flatten_execute_authority_v1 import (
    FLATTEN_EXECUTE_OWNER_GO_CANONICAL,
    FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS,
)

BOUNDED_ACTIVATION_PERMIT_KIND = "BOUNDED_ACTIVATION"
BOUNDED_ACTIVATION_PURPOSE_CANONICAL = "SECTION_11_13_5_BOUNDED_ACTIVATION"
BOUNDED_ACTIVATION_OWNER_GO_CANONICAL = "SECTION_11_13_5_BOUNDED_ACTIVATION_OWNER_GO"
BOUNDED_ACTIVATION_AUTHORITY_KIND = "BOUNDED_ACTIVATION_PERMIT"

P16_IMPLEMENTATION_OWNER_GO = (
    "PEAK_TRADE_OWNER_GO_EXECUTION_PREREQUISITE_16_BOUNDED_ACTIVATION_MAXIMUM_SAFE_LEVERAGE_V1"
)

# Mechanism expected-value only. Presence in source is not bounded runtime
# activation and is not flatten-execute authorization.
FORBIDDEN_BOUNDED_ACTIVATION_OWNER_GOS: frozenset[str] = frozenset(
    {
        *FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS,
        P16_IMPLEMENTATION_OWNER_GO,
        FLATTEN_EXECUTE_OWNER_GO_CANONICAL,
        "OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE",
        "OWNER_GO_SECTION_11_13_LIVE_CANARY_PRODUCTIVE_SURFACE_AUTHORING",
        "SECTION_11_13_LIVE_ACTIVATION",
        "LIVE_AUTHORIZED",
    }
)


class LiveCanaryBoundedActivationPermitError(RuntimeError):
    """Fail-closed bounded activation permit violation."""


@dataclass(frozen=True)
class BoundedActivationPermitV1:
    """Scoped activation evidence. Narrower than global LIVE_AUTHORIZED.

    Not network-session authorization. Not flatten-execute authorization.
    Not a wire-send receipt.
    """

    kind: str
    purpose: str
    owner_go: str
    bound_origin_main_sha: str
    instrument_id: str
    not_after_monotonic_ms: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "purpose": self.purpose,
            "owner_go": self.owner_go,
            "bound_origin_main_sha": self.bound_origin_main_sha,
            "instrument_id": self.instrument_id,
            "not_after_monotonic_ms": int(self.not_after_monotonic_ms),
        }


def offline_contract_proof_bounded_activation_permit_v1(
    *,
    origin_main_sha: str,
    instrument_id: str = DEFAULT_INSTRUMENT_ID,
    not_after_monotonic_ms: int = 1_000_000,
) -> BoundedActivationPermitV1:
    """Offline contract-regression fixture. Not a productive runtime permit."""
    return BoundedActivationPermitV1(
        kind=BOUNDED_ACTIVATION_PERMIT_KIND,
        purpose=BOUNDED_ACTIVATION_PURPOSE_CANONICAL,
        owner_go=BOUNDED_ACTIVATION_OWNER_GO_CANONICAL,
        bound_origin_main_sha=str(origin_main_sha or "").strip().lower(),
        instrument_id=str(instrument_id or "").strip() or DEFAULT_INSTRUMENT_ID,
        not_after_monotonic_ms=int(not_after_monotonic_ms),
    )


def evaluate_bounded_activation_permit_v1(
    *,
    permit: BoundedActivationPermitV1 | None,
    origin_main_sha: str,
    instrument_id: str,
    evaluation_monotonic_ms: int,
) -> tuple[bool, tuple[str, ...]]:
    """Return (accepted, deny_reasons). Never treats implementation GO as permit."""
    reasons: list[str] = []
    if permit is None:
        return (False, ("BOUNDED_ACTIVATION_PERMIT_MISSING",))
    if not isinstance(permit, BoundedActivationPermitV1):
        return (False, ("BOUNDED_ACTIVATION_PERMIT_TYPE_INVALID",))

    kind = str(permit.kind or "").strip()
    if not kind:
        reasons.append("BOUNDED_ACTIVATION_PERMIT_KIND_MISSING")
    elif kind != BOUNDED_ACTIVATION_PERMIT_KIND:
        reasons.append("BOUNDED_ACTIVATION_PERMIT_KIND_INVALID")

    purpose = str(permit.purpose or "").strip()
    if not purpose:
        reasons.append("BOUNDED_ACTIVATION_PURPOSE_MISSING")
    elif purpose != BOUNDED_ACTIVATION_PURPOSE_CANONICAL:
        reasons.append("BOUNDED_ACTIVATION_PURPOSE_INVALID")

    go = str(permit.owner_go or "").strip()
    if not go:
        reasons.append("BOUNDED_ACTIVATION_OWNER_GO_MISSING")
    elif go in FORBIDDEN_BOUNDED_ACTIVATION_OWNER_GOS:
        reasons.append("BOUNDED_ACTIVATION_OWNER_GO_FORBIDDEN")
    elif "NO_EXECUTE" in go.upper() or "NO_IMPLICIT_EXECUTE" in go.upper():
        reasons.append("BOUNDED_ACTIVATION_OWNER_GO_FORBIDDEN")
    elif go != BOUNDED_ACTIVATION_OWNER_GO_CANONICAL:
        reasons.append("BOUNDED_ACTIVATION_OWNER_GO_MISMATCH")

    bound = str(permit.bound_origin_main_sha or "").strip().lower()
    expected_sha = str(origin_main_sha or "").strip().lower()
    if not bound:
        reasons.append("BOUNDED_ACTIVATION_BOUND_SHA_MISSING")
    elif len(bound) != 40 or any(ch not in "0123456789abcdef" for ch in bound):
        reasons.append("BOUNDED_ACTIVATION_BOUND_SHA_MALFORMED")
    elif not expected_sha:
        reasons.append("BOUNDED_ACTIVATION_ORIGIN_SHA_MISSING")
    elif bound != expected_sha:
        reasons.append("BOUNDED_ACTIVATION_BOUND_SHA_STALE")

    permit_inst = str(permit.instrument_id or "").strip()
    target = str(instrument_id or "").strip()
    if not permit_inst:
        reasons.append("BOUNDED_ACTIVATION_INSTRUMENT_MISSING")
    elif permit_inst != target:
        reasons.append("BOUNDED_ACTIVATION_INSTRUMENT_MISMATCH")

    try:
        not_after = int(permit.not_after_monotonic_ms)
    except (TypeError, ValueError):
        reasons.append("BOUNDED_ACTIVATION_EXPIRY_MALFORMED")
        not_after = -1
    else:
        if not_after < 0:
            reasons.append("BOUNDED_ACTIVATION_EXPIRY_MALFORMED")
        else:
            try:
                evaluation_ms = int(evaluation_monotonic_ms)
            except (TypeError, ValueError):
                reasons.append("BOUNDED_ACTIVATION_EVALUATION_CLOCK_MALFORMED")
            else:
                if evaluation_ms > not_after:
                    reasons.append("BOUNDED_ACTIVATION_PERMIT_EXPIRED")

    return (not reasons, tuple(reasons))


def bounded_activation_permit_audit_v1(
    *,
    permit: BoundedActivationPermitV1 | None,
    origin_main_sha: str,
    instrument_id: str,
    evaluation_monotonic_ms: int,
) -> dict[str, Any]:
    accepted, reasons = evaluate_bounded_activation_permit_v1(
        permit=permit,
        origin_main_sha=origin_main_sha,
        instrument_id=instrument_id,
        evaluation_monotonic_ms=evaluation_monotonic_ms,
    )
    return {
        "kind": BOUNDED_ACTIVATION_AUTHORITY_KIND,
        "accepted": accepted,
        "reasons": list(reasons),
        "purpose_canonical": BOUNDED_ACTIVATION_PURPOSE_CANONICAL,
        "permit_supplied": permit is not None,
        "implementation_go_is_not_permit": True,
        "global_live_authorized_cannot_substitute": True,
        "network_session_not_implied": True,
        "flatten_execute_not_implied": True,
    }
