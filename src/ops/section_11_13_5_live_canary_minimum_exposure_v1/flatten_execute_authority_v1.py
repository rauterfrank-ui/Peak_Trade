"""Dedicated §11.13.5 flatten-execute authority (confirm token + purpose).

Invocation-scoped only. Standing live flags remain false. This module does
not authorize GET, POST, or flatten execution. Missing/wrong/stale/wrong-purpose
tokens deny. Implementation Owner-GOs are forbidden as execute tokens.
"""

from __future__ import annotations

from typing import Any

FLATTEN_EXECUTE_PURPOSE_CANONICAL = "SECTION_11_13_5_FLATTEN_EXECUTE"
FLATTEN_EXECUTE_CONFIRM_TOKEN_CANONICAL = "I_AUTHORIZE_SECTION_11_13_5_FLATTEN_EXECUTE"
FLATTEN_EXECUTE_OWNER_GO_CANONICAL = "SECTION_11_13_5_FLATTEN_EXECUTE_OWNER_GO"
FLATTEN_EXECUTE_AUTHORITY_KIND = "FLATTEN_EXECUTE_CONFIRM"

# Mechanism expected-value only. Presence in source is not execute authorization.
# Default supplied token remains empty/absent → deny.
FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS: frozenset[str] = frozenset(
    {
        "SECTION_11_13_5_POST_Z2AU_PRODUCTIVE_LIVE_FLATTEN_WIRING_MAX_SAFE_SLICE_FAIL_CLOSED_NO_NETWORK_NO_GET_NO_POST_NO_EXECUTE",
        "SECTION_11_13_5_Z2AP_PRODUCTIVE_LIVE_FLATTEN_PROVABILITY_NEXT_MAX_SAFE_SLICE_FAIL_CLOSED_NO_IMPLICIT_EXECUTE",
        "SECTION_11_13_5_PRODUCTIVE_LIVE_FLATTEN_PROOF_PRE_EXECUTION_GATE_AND_RUNTIME_READINESS_ONLY",
        "SECTION_11_13_5_Z2AP_PRODUCTIVE_LIVE_FLATTEN_PROVABILITY_NEXT_MAX_SAFE_SLICE_FAIL_CLOSED_NO_IMPLICIT_EXECUTE",
        "OWNER_GO_SECTION_11_13_LIVE_CANARY_PRODUCTIVE_SURFACE_AUTHORING",
        "OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE",
    }
)


class LiveCanaryFlattenExecuteAuthorityError(RuntimeError):
    """Fail-closed flatten-execute authority violation."""


def evaluate_flatten_execute_authority_v1(
    *,
    token: str | None,
    purpose: str | None,
    owner_go: str | None,
) -> tuple[bool, tuple[str, ...]]:
    """Return (accepted, deny_reasons). Never treats this implementation GO as execute."""
    reasons: list[str] = []
    supplied = str(token or "")
    if not supplied.strip():
        reasons.append("FLATTEN_EXECUTE_TOKEN_MISSING")
    elif supplied != FLATTEN_EXECUTE_CONFIRM_TOKEN_CANONICAL:
        reasons.append("FLATTEN_EXECUTE_TOKEN_MISMATCH")

    purpose_norm = str(purpose or "").strip()
    if not purpose_norm:
        reasons.append("FLATTEN_EXECUTE_PURPOSE_MISSING")
    elif purpose_norm != FLATTEN_EXECUTE_PURPOSE_CANONICAL:
        reasons.append("FLATTEN_EXECUTE_PURPOSE_INVALID")

    go = str(owner_go or "").strip()
    if not go:
        reasons.append("FLATTEN_EXECUTE_OWNER_GO_MISSING")
    elif go in FORBIDDEN_FLATTEN_EXECUTE_OWNER_GOS:
        reasons.append("FLATTEN_EXECUTE_OWNER_GO_FORBIDDEN")
    elif "NO_EXECUTE" in go.upper() or "NO_IMPLICIT_EXECUTE" in go.upper():
        reasons.append("FLATTEN_EXECUTE_OWNER_GO_FORBIDDEN")
    elif "AUTHORING" in go.upper() or "WIRING" in go.upper() or "READINESS" in go.upper():
        reasons.append("FLATTEN_EXECUTE_OWNER_GO_FORBIDDEN")
    elif go != FLATTEN_EXECUTE_OWNER_GO_CANONICAL:
        reasons.append("FLATTEN_EXECUTE_OWNER_GO_MISMATCH")

    return (not reasons, tuple(reasons))


def flatten_execute_authority_audit_v1(
    *,
    token: str | None,
    purpose: str | None,
    owner_go: str | None,
) -> dict[str, Any]:
    accepted, reasons = evaluate_flatten_execute_authority_v1(
        token=token,
        purpose=purpose,
        owner_go=owner_go,
    )
    return {
        "kind": FLATTEN_EXECUTE_AUTHORITY_KIND,
        "accepted": accepted,
        "reasons": list(reasons),
        "purpose_canonical": FLATTEN_EXECUTE_PURPOSE_CANONICAL,
        "token_supplied": bool(str(token or "").strip()),
        "implementation_go_is_not_execute_token": True,
    }
