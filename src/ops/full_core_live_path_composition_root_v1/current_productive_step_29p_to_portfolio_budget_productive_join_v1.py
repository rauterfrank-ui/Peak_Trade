"""Bind STEP-29P Treasury handoff producer output into portfolio budget owner.

Closes equity lineage → PortfolioCapitalReservationBudgetOwner causal gap for N5/MV2
compose. Uses existing bind_canonical_producer_output_v1 only.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

from dataclasses import dataclass

from src.ops.full_core_live_path_composition_root_v1.current_productive_treasury_single_source_capital_handoff_v1 import (
    CurrentProductiveTreasurySingleSourceCapitalHandoffV1,
)
from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
    PortfolioCapitalReservationBudgetOwnerV1,
    ReserveDispositionV1,
)

JOIN_SEAM_ID = "CURRENT_PRODUCTIVE_STEP_29P_TO_PORTFOLIO_BUDGET_PRODUCTIVE_JOIN_V1"


@dataclass(frozen=True)
class Step29pToPortfolioBudgetProductiveJoinResultV1:
    ok: bool
    join_seam_id: str
    fail_closed: bool
    reason_codes: tuple[str, ...]
    admitted_budget: str
    observation_id: str
    step_29p_decision_epoch: str
    producer_input_set_digest: str


def join_step_29p_handoff_into_portfolio_capital_reservation_budget_v1(
    *,
    handoff: CurrentProductiveTreasurySingleSourceCapitalHandoffV1,
    owner: PortfolioCapitalReservationBudgetOwnerV1,
    e2e_run_id: str,
) -> Step29pToPortfolioBudgetProductiveJoinResultV1:
    """Fail-closed bind of canonical 29P producer output to in-memory budget owner."""
    reasons: list[str] = []
    if handoff.fail_closed is True:
        reasons.append("HANDOFF_FAIL_CLOSED")
    if handoff.step_29p_admissibility.risk_admissible is not True:
        reasons.extend(str(c) for c in handoff.step_29p_admissibility.reason_codes)
        reasons.append("STEP_29P_NOT_RISK_ADMISSIBLE")
    output = handoff.producer_output
    epoch = str(output.decision_epoch or "").strip()
    digest = str(output.input_set_digest or "").strip().lower()
    if epoch == "":
        reasons.append("DECISION_EPOCH_MISSING")
    if str(e2e_run_id or "").strip() == "":
        reasons.append("E2E_RUN_ID_MISSING")
    if reasons:
        return Step29pToPortfolioBudgetProductiveJoinResultV1(
            ok=False,
            join_seam_id=JOIN_SEAM_ID,
            fail_closed=True,
            reason_codes=tuple(dict.fromkeys(reasons)),
            admitted_budget="0",
            observation_id="",
            step_29p_decision_epoch=epoch,
            producer_input_set_digest=digest,
        )

    bound = owner.bind_canonical_producer_output_v1(output)
    ok = bound.disposition in {
        ReserveDispositionV1.ADMITTED,
        ReserveDispositionV1.IDEMPOTENT_REPLAY,
    }
    state = owner.budget_state_v1()
    return Step29pToPortfolioBudgetProductiveJoinResultV1(
        ok=ok and state.admitted is True,
        join_seam_id=JOIN_SEAM_ID,
        fail_closed=not ok,
        reason_codes=bound.reason_codes,
        admitted_budget=str(state.canonical_available_capital),
        observation_id=state.observation_id,
        step_29p_decision_epoch=epoch,
        producer_input_set_digest=digest,
    )


__all__ = [
    "JOIN_SEAM_ID",
    "Step29pToPortfolioBudgetProductiveJoinResultV1",
    "join_step_29p_handoff_into_portfolio_capital_reservation_budget_v1",
]
