"""Per-lane reconciliation admission vs global portfolio truth (D6)."""

from __future__ import annotations

from decimal import Decimal

from src.ops.current_mf_n5_instrument_runtime_identity_closure_v1.constants_v1 import (
    FAILURE_RECONCILIATION_GLOBAL,
    FAILURE_RECONCILIATION_INSTRUMENT,
)
from src.ops.current_mf_n5_instrument_runtime_identity_closure_v1.models_v1 import (
    OccupiedLaneRuntimeInstrumentIdentityV1,
    PerLaneReconciliationAdmissionV1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_reconciliation_admission_v1 import (
    ProductiveMasterV2ReconciliationAdmissionV1,
    build_explicit_non_productive_bounded_harness_master_v2_reconciliation_admission_v1,
)
from src.ops.productive_reconciliation_runtime_binding_v1.models_v1 import (
    PortfolioTruthSnapshotV1,
)


class ReconciliationAdmissionError(ValueError):
    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(f"{code}:{detail}" if detail else code)
        self.failure_code = code
        self.detail = detail


def _global_portfolio_healthy(portfolio: PortfolioTruthSnapshotV1 | None) -> bool:
    if portfolio is None:
        return True
    if portfolio.missing or portfolio.stale or portfolio.duplicate or portfolio.writer_conflict:
        return False
    return True


def _instrument_position_side(
    portfolio: PortfolioTruthSnapshotV1,
    instrument_id: str,
) -> str | None:
    for pos in portfolio.positions:
        if str(pos.instrument_id) == instrument_id:
            if pos.signed_quantity == Decimal("0"):
                return "FLAT"
            return str(pos.side or "").upper() or "UNKNOWN"
    return None


def build_per_lane_reconciliation_admission_v1(
    *,
    identity: OccupiedLaneRuntimeInstrumentIdentityV1,
    portfolio: PortfolioTruthSnapshotV1 | None,
    fail_closed_on_global_unhealthy: bool = True,
) -> PerLaneReconciliationAdmissionV1:
    global_ok = _global_portfolio_healthy(portfolio)
    if not global_ok and fail_closed_on_global_unhealthy:
        return PerLaneReconciliationAdmissionV1(
            admitted=False,
            reason_code=FAILURE_RECONCILIATION_GLOBAL,
            instrument_reconciled=False,
            global_portfolio_healthy=False,
        )
    if portfolio is None:
        return PerLaneReconciliationAdmissionV1(
            admitted=True,
            reason_code="NO_PORTFOLIO_HARNESS",
            instrument_reconciled=True,
            global_portfolio_healthy=True,
        )
    side = _instrument_position_side(portfolio, identity.canonical_instrument_id)
    if side is None:
        return PerLaneReconciliationAdmissionV1(
            admitted=True,
            reason_code="INSTRUMENT_FLAT_ABSENT",
            instrument_reconciled=True,
            global_portfolio_healthy=global_ok,
        )
    if side == "UNKNOWN":
        return PerLaneReconciliationAdmissionV1(
            admitted=False,
            reason_code=FAILURE_RECONCILIATION_INSTRUMENT,
            instrument_reconciled=False,
            global_portfolio_healthy=global_ok,
        )
    return PerLaneReconciliationAdmissionV1(
        admitted=True,
        reason_code=f"INSTRUMENT_{side}",
        instrument_reconciled=True,
        global_portfolio_healthy=global_ok,
    )


def build_master_v2_reconciliation_admission_for_lane_v1(
    *,
    identity: OccupiedLaneRuntimeInstrumentIdentityV1,
    per_lane: PerLaneReconciliationAdmissionV1,
    session_id: str,
    repository_sha: str,
    portfolio: PortfolioTruthSnapshotV1 | None,
) -> ProductiveMasterV2ReconciliationAdmissionV1:
    """Bind per-lane reconciliation admission witness into the MV2 cycle seam."""
    if not per_lane.admitted:
        raise ReconciliationAdmissionError(per_lane.reason_code, identity.lane_id)
    evidence_digest = ""
    if portfolio is not None:
        evidence_digest = portfolio.digest()
    admission = build_explicit_non_productive_bounded_harness_master_v2_reconciliation_admission_v1(
        bound_instrument_id=identity.canonical_instrument_id,
        session_id=f"{session_id}:{identity.lane_id}",
        repository_sha=repository_sha,
    )
    if evidence_digest:
        return ProductiveMasterV2ReconciliationAdmissionV1(
            context_class=admission.context_class,
            reconciliation_owner=admission.reconciliation_owner,
            session_id=admission.session_id,
            repository_sha=admission.repository_sha,
            bound_instrument_id=admission.bound_instrument_id,
            master_v2_reconciliation_state=admission.master_v2_reconciliation_state,
            gate_ok=admission.gate_ok,
            alpha_enabled=admission.alpha_enabled,
            evidence_digest=evidence_digest,
            reconciliation_classification=(f"N5_LANE_{per_lane.reason_code}:{identity.lane_id}"),
        )
    return admission


def assert_lane_reconciliation_admitted_v1(
    admission: PerLaneReconciliationAdmissionV1,
    *,
    lane_id: str,
) -> None:
    if not admission.admitted:
        raise ReconciliationAdmissionError(
            admission.reason_code,
            lane_id,
        )
