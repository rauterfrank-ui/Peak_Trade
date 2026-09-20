"""Phase-3 shadow read-only enforcement join: reconciliation + separation gate."""

from __future__ import annotations

from src.ops.treasury_phase_2_read_only_reconciliation_v1.models_v1 import (
    TreasuryReconciliationClassV1,
    TreasuryVenueObservationV1,
)
from src.ops.treasury_phase_2_read_only_reconciliation_v1.reconciliation_v1 import (
    evaluate_treasury_read_only_reconciliation_v1,
)
from src.ops.treasury_phase_3_shadow_enforcement_v1.constants_v1 import (
    ALLOWED_SHADOW_HTTP_SURFACES,
    JOIN_SEAM_ID,
    TREASURY_RISK_ADMISSIBLE_MINT,
    TREASURY_SEPARATION_GATE_WIRED,
)
from src.ops.treasury_phase_3_shadow_enforcement_v1.errors_v1 import (
    TreasuryPhase3ShadowEnforcementError,
)
from src.ops.treasury_phase_3_shadow_enforcement_v1.models_v1 import (
    TreasuryShadowEnforcementResultV1,
)
from src.ops.treasury_separation_gate import BOT, evaluate_treasury_policy


def _require_gate_wired() -> None:
    if not TREASURY_SEPARATION_GATE_WIRED:
        raise TreasuryPhase3ShadowEnforcementError("TREASURY_SEPARATION_GATE_NOT_WIRED")


def _require_shadow_surface(shadow_surface: str) -> None:
    surface = str(shadow_surface or "").strip()
    if surface not in ALLOWED_SHADOW_HTTP_SURFACES:
        raise TreasuryPhase3ShadowEnforcementError(
            f"SHADOW_SURFACE_NOT_ALLOWED:{surface or '<empty>'}"
        )


def evaluate_treasury_shadow_read_only_enforcement_v1(
    *,
    observation: TreasuryVenueObservationV1,
    shadow_surface: str,
    role: str | None = None,
) -> TreasuryShadowEnforcementResultV1:
    """Observation → Phase-2 reconciliation → fail-closed shadow allow/deny. No capital mint."""
    _require_gate_wired()
    _require_shadow_surface(shadow_surface)
    if TREASURY_RISK_ADMISSIBLE_MINT:
        raise TreasuryPhase3ShadowEnforcementError("RISK_ADMISSIBLE_MINT_FORBIDDEN")

    normalized_role = str(role or BOT).strip().lower() or BOT
    for operation in ("withdraw", "internal_transfer", "deposit_address_request"):
        gate = evaluate_treasury_policy(operation, role=normalized_role)
        if gate.allowed:
            raise TreasuryPhase3ShadowEnforcementError(
                f"BOT_ROLE_MUST_NOT_ALLOW_TREASURY_MUTATION:{operation}"
            )

    reconciliation = evaluate_treasury_read_only_reconciliation_v1(observation)
    reasons: list[str] = list(reconciliation.reason_codes)
    recon_class = str(reconciliation.reconciliation_class)

    if reconciliation.capital_increase_authority:
        reasons.append("CAPITAL_INCREASE_NOT_SHADOW_UPLIFT")

    capital_uplift_permitted = False

    if recon_class in {
        TreasuryReconciliationClassV1.UNKNOWN.value,
        TreasuryReconciliationClassV1.AMBIGUOUS.value,
        TreasuryReconciliationClassV1.STALE.value,
    }:
        reasons.append("TREASURY_SHADOW_RECONCILIATION_FAIL_CLOSED")
        return TreasuryShadowEnforcementResultV1(
            shadow_permitted=False,
            fail_closed=True,
            capital_uplift_permitted=capital_uplift_permitted,
            reconciliation_class=recon_class,
            reason_codes=tuple(dict.fromkeys(reasons)),
            join_seam_id=JOIN_SEAM_ID,
            gate_wired=True,
            shadow_surface=shadow_surface,
        )

    if recon_class == TreasuryReconciliationClassV1.OBSERVED.value:
        if reconciliation.fail_closed or reconciliation.capital_increase_authority:
            reasons.append("OBSERVED_INCREASE_NO_SHADOW_CAPITAL_UPLIFT")
            return TreasuryShadowEnforcementResultV1(
                shadow_permitted=False,
                fail_closed=True,
                capital_uplift_permitted=capital_uplift_permitted,
                reconciliation_class=recon_class,
                reason_codes=tuple(dict.fromkeys(reasons)),
                join_seam_id=JOIN_SEAM_ID,
                gate_wired=True,
                shadow_surface=shadow_surface,
            )

    if recon_class == TreasuryReconciliationClassV1.RECONCILED.value:
        if reconciliation.capital_increase_authority:
            reasons.append("RECONCILED_INCREASE_NO_AUTO_SHADOW_ADMISSION")
            return TreasuryShadowEnforcementResultV1(
                shadow_permitted=True,
                fail_closed=False,
                capital_uplift_permitted=False,
                reconciliation_class=recon_class,
                reason_codes=tuple(dict.fromkeys((*reasons, "TREASURY_SHADOW_OBSERVE_ONLY"))),
                join_seam_id=JOIN_SEAM_ID,
                gate_wired=True,
                shadow_surface=shadow_surface,
            )
        return TreasuryShadowEnforcementResultV1(
            shadow_permitted=True,
            fail_closed=bool(reconciliation.fail_closed),
            capital_uplift_permitted=False,
            reconciliation_class=recon_class,
            reason_codes=tuple(dict.fromkeys((*reasons, "TREASURY_SHADOW_STABLE_RECONCILED"))),
            join_seam_id=JOIN_SEAM_ID,
            gate_wired=True,
            shadow_surface=shadow_surface,
        )

    reasons.append("TREASURY_SHADOW_RECONCILIATION_CLASS_UNEXPECTED")
    return TreasuryShadowEnforcementResultV1(
        shadow_permitted=False,
        fail_closed=True,
        capital_uplift_permitted=False,
        reconciliation_class=recon_class,
        reason_codes=tuple(dict.fromkeys(reasons)),
        join_seam_id=JOIN_SEAM_ID,
        gate_wired=True,
        shadow_surface=shadow_surface,
    )


def evaluate_treasury_shadow_enforcement_missing_observation_v1(
    *,
    shadow_surface: str,
) -> TreasuryShadowEnforcementResultV1:
    """Fail-closed when shadow capital evidence is required but absent."""
    _require_gate_wired()
    _require_shadow_surface(shadow_surface)
    return TreasuryShadowEnforcementResultV1(
        shadow_permitted=False,
        fail_closed=True,
        capital_uplift_permitted=False,
        reconciliation_class=TreasuryReconciliationClassV1.UNKNOWN.value,
        reason_codes=("TREASURY_SHADOW_EVIDENCE_REQUIRED", "MISSING_OBSERVATION_FAIL_CLOSED"),
        join_seam_id=JOIN_SEAM_ID,
        gate_wired=True,
        shadow_surface=shadow_surface,
    )
