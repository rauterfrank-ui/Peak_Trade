"""HTTP endpoint treasury gate binding for governed §11.13 read-only/shadow surfaces."""

from __future__ import annotations

from src.ops.treasury_phase_3_shadow_enforcement_v1.constants_v1 import (
    ALLOWED_SHADOW_HTTP_SURFACES,
    TREASURY_SEPARATION_GATE_WIRED,
)
from src.ops.treasury_phase_3_shadow_enforcement_v1.errors_v1 import (
    TreasuryPhase3ShadowEnforcementError,
)
from src.ops.treasury_separation_gate import BOT, evaluate_treasury_policy

_TREASURY_ENDPOINT_MARKERS: tuple[tuple[str, str], ...] = (
    ("/asset/withdrawal", "withdraw"),
    ("/asset/transfer", "internal_transfer"),
    ("/asset/deposit-address", "deposit_address_request"),
)


def assert_treasury_shadow_http_endpoint_allowed_v1(
    *,
    endpoint: str,
    method: str,
    shadow_surface: str,
    role: str | None = None,
) -> None:
    """Fail-closed treasury separation on shadow/read-only HTTP surfaces before wire."""
    if not TREASURY_SEPARATION_GATE_WIRED:
        raise TreasuryPhase3ShadowEnforcementError("TREASURY_SEPARATION_GATE_NOT_WIRED")
    surface = str(shadow_surface or "").strip()
    if surface not in ALLOWED_SHADOW_HTTP_SURFACES:
        raise TreasuryPhase3ShadowEnforcementError(
            f"SHADOW_SURFACE_NOT_ALLOWED:{surface or '<empty>'}"
        )

    m = str(method or "").strip().upper()
    if m != "GET":
        raise TreasuryPhase3ShadowEnforcementError(
            f"TREASURY_SHADOW_HTTP_GET_ONLY:{m or '<empty>'}"
        )

    ep = str(endpoint or "").strip()
    if not ep:
        raise TreasuryPhase3ShadowEnforcementError("ENDPOINT_REQUIRED")

    lowered = ep.lower()
    normalized_role = str(role or BOT).strip().lower() or BOT
    for marker, operation in _TREASURY_ENDPOINT_MARKERS:
        if marker not in lowered:
            continue
        decision = evaluate_treasury_policy(operation, role=normalized_role)
        if decision.allowed:
            raise TreasuryPhase3ShadowEnforcementError(
                f"TREASURY_SHADOW_GATE_MUST_DENY:{operation}"
            )
        raise TreasuryPhase3ShadowEnforcementError(
            f"TREASURY_SHADOW_GATE_DENY:{operation}:{decision.event_type}"
        )
