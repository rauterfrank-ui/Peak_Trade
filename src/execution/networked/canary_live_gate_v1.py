"""
LB-EXE-001 — expliziter Canary-/Live-Autorisierungs-Gate (v1, networkless).

Dieses Modul ist die kleinste reviewbare Scheibe für einen *benannten* Gate-Punkt
zwischen externer Freigabe (LB-APR-001) und zukünftigem Transport. Es ersetzt
keine menschliche Freigabe und hebt dry_run / NO-LIVE nicht auf.

v1-Verhalten: Jede Entscheidung lehnt produktiven Outbound (echter Canary/Live-
Orderpfad) ab — auch wenn ein externes Referenzfeld gesetzt ist — bis ein
separat reviewter Transport/EXE-Schritt existiert.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

# Optional: Ticket-/Formular-Referenz aus LB-APR-001 (nur Nachweis/Pointer; kein Go).
ENV_PT_CANARY_SCOPE_REF = "PT_CANARY_SCOPE_REF"


@dataclass(frozen=True)
class CanaryLiveGateDecisionV1:
    """Structured gate outcome for audit/logging; v1 never allows outbound live/canary."""

    outbound_live_or_canary_allowed: bool
    reason_code: str
    external_approval_ref_present: bool


def evaluate_canary_live_gate_v1(
    *,
    dry_run: bool,
    mode: str,
    external_approval_ref: Optional[str],
) -> CanaryLiveGateDecisionV1:
    """
    Evaluate explicit preconditions for any future authorized canary/live path.

    v1: Always denies outbound (outbound_live_or_canary_allowed == False).
    Reasons distinguish *why* a future path would still be blocked.
    """
    ref = (external_approval_ref or "").strip()
    ref_ok = bool(ref)

    if not dry_run:
        return CanaryLiveGateDecisionV1(
            outbound_live_or_canary_allowed=False,
            reason_code="deny:dry_run_required_v1",
            external_approval_ref_present=ref_ok,
        )
    if mode not in ("shadow", "paper"):
        return CanaryLiveGateDecisionV1(
            outbound_live_or_canary_allowed=False,
            reason_code="deny:mode_not_shadow_or_paper",
            external_approval_ref_present=ref_ok,
        )
    if not ref_ok:
        return CanaryLiveGateDecisionV1(
            outbound_live_or_canary_allowed=False,
            reason_code="deny:missing_external_approval_ref_lb_apr_001",
            external_approval_ref_present=False,
        )
    # Ref present: still networkless v1 — no outbound transport enabled in this slice
    return CanaryLiveGateDecisionV1(
        outbound_live_or_canary_allowed=False,
        reason_code="deny:v1_networkless_no_outbound_transport",
        external_approval_ref_present=True,
    )


def evaluate_canary_live_gate_v1_from_environ(
    *,
    dry_run: bool,
    mode: str,
    environ: Optional[dict[str, str]] = None,
) -> CanaryLiveGateDecisionV1:
    """Read optional PT_CANARY_SCOPE_REF from env (or provided mapping)."""
    env = environ if environ is not None else dict(os.environ)
    ref = env.get(ENV_PT_CANARY_SCOPE_REF)
    return evaluate_canary_live_gate_v1(
        dry_run=dry_run,
        mode=mode,
        external_approval_ref=ref,
    )


__all__ = [
    "ENV_PT_CANARY_SCOPE_REF",
    "CanaryLiveGateDecisionV1",
    "evaluate_canary_live_gate_v1",
    "evaluate_canary_live_gate_v1_from_environ",
]
