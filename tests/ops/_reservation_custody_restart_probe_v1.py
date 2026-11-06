"""Disposable offline inspection probe, never a reservation restore mechanism."""

import argparse
from decimal import Decimal
import json
from pathlib import Path
import threading

from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
    PortfolioCapitalReservationBudgetOwnerV1,
)
from src.ops.productive_reconciliation_runtime_binding_v1.models_v1 import (
    PortfolioTruthSnapshotV1,
    PositionTruthV1,
)
from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.topology_v1 import (
    apply_isolated_lane_topology_v1,
)
from src.ops.runtime_health_recovery_and_failure_injection_closure_v1.evidence_v1 import write_json
from tests.ops.test_portfolio_capital_reservation_budget_contract_v1 import _bind
from tests.ops.test_current_mf_n5_durable_lane_assignment_persistence_v1 import (
    _seed,
    _recover,
    _five_ranking,
    _cid,
    _membership,
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("phase", choices=("before", "after"))
    parser.add_argument("quantity")
    args = parser.parse_args()
    owner = PortfolioCapitalReservationBudgetOwnerV1()
    topology_root = args.root / "topology"
    if args.phase == "before":
        _, topology, _, _, _ = _seed(topology_root)
        observation = _bind(owner)
        reservation = owner.try_reserve_v1(
            slot_id="LANE_1",
            decision_id="restart-probe",
            cycle_id="before",
            observation_id=observation,
            amount=Decimal("60"),
        )
        assert reservation.reservation is not None
        committed = owner.commit_internal_pre_external_effect_v1(
            str(reservation.reservation.reservation_id)
        )
        assert committed.reservation is not None
        write_json(
            args.root / "probe_before.json",
            {
                "active_sum": str(owner.active_sum_v1()),
                "reservation_state": committed.reservation.state.value,
                "reservation_count": owner.stored_reservation_count_v1(),
                "mapping": topology.instrument_to_lane(),
                "observation_id": observation,
                "canonical_restart_reconstructable": owner.budget_state_v1().canonical_restart_reconstructable,
            },
        )
        # Parent SIGKILLs after the independent component checkpoints above.
        threading.Event().wait()
    else:
        topology = _recover(topology_root)
        assert topology is not None
        recovered_mapping = topology.instrument_to_lane()
        before_admission = owner.budget_state_v1()
        ranking = _five_ranking()
        a, b, c = (
            _cid(ranking, native) for native in ("ADA-USDT-SWAP", "ETH-USDT-SWAP", "SOL-USDT-SWAP")
        )
        custody = apply_isolated_lane_topology_v1(
            membership=_membership(
                ranking, [b, c], bootstrap=False, prior=topology.membership_instance_id
            ),
            ranking_snapshot=ranking,
            topology_state_root_base=topology_root,
            prior_topology=topology,
            open_position_custody_portfolio=PortfolioTruthSnapshotV1(
                positions=(
                    PositionTruthV1.from_signed(
                        instrument_id=a, signed_quantity=Decimal(args.quantity)
                    ),
                )
            ),
        )
        _bind(owner, epoch="2026-11-03T12:00:01Z")
        state = owner.budget_state_v1()
        print(
            json.dumps(
                {
                    "mapping": recovered_mapping,
                    "custody_retained_same_lane": custody.instrument_to_lane().get(a)
                    == recovered_mapping[a],
                    "unadmitted_after_restart": not before_admission.admitted,
                    "active_sum_after_independent_fact": str(state.active_reservation_sum),
                    "reservation_count_after_independent_fact": owner.stored_reservation_count_v1(),
                    "budget_after_independent_fact": str(state.canonical_available_capital),
                    "canonical_restart_reconstructable": state.canonical_restart_reconstructable,
                    "inspection_scope": "INDEPENDENT_COMPONENT_RESTART_NOT_COMPLETE_ECONOMIC_JOIN",
                }
            )
        )


if __name__ == "__main__":
    main()
