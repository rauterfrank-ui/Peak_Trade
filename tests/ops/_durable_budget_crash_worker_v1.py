"""Disposable physical SIGKILL checkpoints; synthetic inputs, no venue access."""

import argparse
import json
from pathlib import Path
import threading

from tests.ops.test_durable_portfolio_budget_recovery_v1 import _owner, _auto, _observed, _reserve
from tests.ops.test_portfolio_sizing_learning_semantic_join_v1 import _admit, _sizing_input
from trading.master_v2.capital_risk_sizing_offline_replay_binding_adapter_v0 import (
    compute_risk_sizing_decision_ref_v0,
)


def _sizing_snapshot(owner, result):
    sized = result.sizing_decision
    return {
        "quantity": str(sized.final_quantity),
        "notional": str(sized.canonical_position_sizing.resulting_notional),
        "sizing_ref": compute_risk_sizing_decision_ref_v0(sized),
        "held_sum": str(owner.active_sum_v1()),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("phase")
    parser.add_argument("quantity")
    args = parser.parse_args()
    owner = _owner(args.root, "recover" if args.phase in {"recover", "recover_sized"} else "create")
    before = owner.budget_state_v1()
    result = _auto(owner, args.root, observed=_observed(args.quantity))
    assert result.disposition.value == "ADMITTED", result
    if args.phase == "recover_sized":
        replayed = _admit(owner, _sizing_input())
        assert replayed.disposition.value == "IDEMPOTENT_REPLAY", replayed
        print(json.dumps(_sizing_snapshot(owner, replayed)), flush=True)
        owner.close()
        return
    if args.phase == "recover":
        after = owner.budget_state_v1()
        retry = _reserve(owner, "10", "acknowledgement-may-be-lost")
        print(
            json.dumps(
                {
                    "held_before_reconciliation": str(before.active_reservation_sum),
                    "admitted_before_reconciliation": before.admitted,
                    "admitted_after_automatic_reconciliation": after.admitted,
                    "held_after": str(after.active_reservation_sum),
                    "remaining": str(after.remaining_unreserved),
                    "retry_disposition": retry.disposition.value,
                }
            ),
            flush=True,
        )
        owner.close()
        return
    held = _reserve(owner)
    owner.commit_internal_pre_external_effect_v1(str(held.reservation.reservation_id))

    def checkpoint():
        (args.root / "checkpoint").write_text(args.phase)
        threading.Event().wait()

    if args.phase == "sized":
        admitted = _admit(owner, _sizing_input())
        assert admitted.disposition.value == "ADMITTED", admitted
        (args.root / "first_sizing.json").write_text(json.dumps(_sizing_snapshot(owner, admitted)))
        checkpoint()
    elif args.phase == "held":
        checkpoint()
    else:
        connection = owner._store.connection

        class CommitCheckpoint:
            def __getattr__(self, name):
                return getattr(connection, name)

            def commit(self):
                if args.phase == "before_commit":
                    checkpoint()
                connection.commit()
                if args.phase == "after_commit":
                    checkpoint()

        owner._store.connection = CommitCheckpoint()
        _reserve(owner, "10", "acknowledgement-may-be-lost")


if __name__ == "__main__":
    main()
