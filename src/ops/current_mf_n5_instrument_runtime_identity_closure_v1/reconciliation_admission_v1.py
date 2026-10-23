"""Per-lane reconciliation admission vs global portfolio truth (D6)."""

from __future__ import annotations

from pathlib import Path

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
        return False
    if portfolio.missing or portfolio.stale or portfolio.duplicate or portfolio.writer_conflict:
        return False
    return True


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
            admitted=False,
            reason_code=FAILURE_RECONCILIATION_GLOBAL,
            instrument_reconciled=False,
            global_portfolio_healthy=False,
        )
    from src.ops.current_mf_n5_instrument_runtime_identity_closure_v1.position_truth_v1 import (
        evidence_for_instrument_ids_v1,
    )

    evidence = evidence_for_instrument_ids_v1(
        portfolio,
        {identity.canonical_instrument_id, identity.venue_native_id},
    )
    if evidence.evidence_class == "VERIFIED_EMPTY":
        return PerLaneReconciliationAdmissionV1(
            admitted=True,
            reason_code="NO_POSITION_CLEAN",
            instrument_reconciled=True,
            global_portfolio_healthy=global_ok,
        )
    if evidence.evidence_class == "VERIFIED_NET":
        side = evidence.existing_position_side.value.upper()
        return PerLaneReconciliationAdmissionV1(
            admitted=True,
            reason_code=f"INSTRUMENT_{side}",
            instrument_reconciled=True,
            global_portfolio_healthy=global_ok,
        )
    return PerLaneReconciliationAdmissionV1(
        admitted=False,
        reason_code=FAILURE_RECONCILIATION_INSTRUMENT,
        instrument_reconciled=False,
        global_portfolio_healthy=global_ok,
    )


def build_master_v2_reconciliation_admission_for_lane_v1(
    *,
    identity: OccupiedLaneRuntimeInstrumentIdentityV1,
    per_lane: PerLaneReconciliationAdmissionV1,
    session_id: str,
    repository_sha: str,
    portfolio: PortfolioTruthSnapshotV1 | None,
    state_root: Path | None = None,
) -> ProductiveMasterV2ReconciliationAdmissionV1:
    """Bind a productive gate witness when a portfolio snapshot and state root exist."""
    if not per_lane.admitted:
        raise ReconciliationAdmissionError(per_lane.reason_code, identity.lane_id)
    if portfolio is not None and state_root is not None:
        from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_reconciliation_admission_v1 import (
            build_productive_master_v2_reconciliation_admission_from_gate_v1,
        )
        from src.ops.productive_reconciliation_runtime_binding_v1.startup_gate_v1 import (
            run_productive_reconciliation_startup_gate_v1,
        )

        gate_session = f"productive-reconciliation:{identity.canonical_instrument_id}"
        gate = run_productive_reconciliation_startup_gate_v1(
            state_root=Path(state_root) / "productive_reconciliation_gate_v1",
            observed=portfolio,
            session_id=gate_session,
            repository_sha=str(repository_sha or "").strip(),
        )
        if gate.ok is not True or gate.alpha_enabled is not True:
            detail = ",".join(gate.blockers) if gate.blockers else str(gate.classification.value)
            raise ReconciliationAdmissionError(
                "PRODUCTIVE_RECONCILIATION_GATE_FAIL_CLOSED",
                f"{identity.lane_id}:{gate.classification.value}:{detail}",
            )
        return build_productive_master_v2_reconciliation_admission_from_gate_v1(
            gate=gate,
            session_id=gate_session,
            repository_sha=str(repository_sha or "").strip(),
            bound_instrument_id=identity.canonical_instrument_id,
        )
    return build_explicit_non_productive_bounded_harness_master_v2_reconciliation_admission_v1(
        bound_instrument_id=identity.canonical_instrument_id,
        session_id=f"{session_id}:{identity.lane_id}",
        repository_sha=repository_sha,
    )


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
