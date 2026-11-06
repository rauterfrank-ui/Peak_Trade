"""Exact original risk/envelope/fill attribution, including rehashed corruption."""

from dataclasses import replace
from decimal import Decimal as D
import json

import pytest

from src.ops.exit_policy_producer_binding_v1.position_episode_binding_v1 import (
    PositionEpisodeIdentityV1,
    PositionEpisodeScopeV1,
)
from src.ops.exit_policy_producer_binding_v1.simulated_accounting_entry_source_v1 import (
    bind_simulated_accounting_episode_identity_v1,
)
from src.ops.exit_policy_producer_binding_v1.risk_bound_simulated_entry_v1 import (
    create_risk_bound_simulated_episode_v1,
    recover_risk_bound_simulated_episode_v1,
)
from src.ops.productive_futures_accounting_runtime_binding_v1.accounting_engine_v1 import (
    ProductiveFuturesAccountingSessionV1,
)
from src.ops.productive_futures_accounting_runtime_binding_v1.fill_model_v1 import (
    build_simulated_fill_v1,
)
from src.ops.portfolio_capital_reservation_budget_v1.durable_store_v1 import digest
from tests.ops.test_bounded_offline_decision_risk_v1 import _request, _admit, _envelope, MS
from tests.ops.test_durable_portfolio_budget_recovery_v1 import _owner, _auto, BOUND
from tests.ops.test_portfolio_capital_reservation_budget_contract_v1 import _sizing_input, ACCOUNT
from tests.ops.test_productive_futures_accounting_runtime_binding_v1 import _contract
from tests.ops.test_simulated_accounting_entry_source_v1 import _args


@pytest.mark.parametrize("side", ["LONG", "SHORT"])
@pytest.mark.parametrize("corrupt", [None, "unknown-field", "source-prefix", "envelope"])
def test_attributed_entry_uses_exact_original_risk_fill_and_source(tmp_path, side, corrupt):
    owner = _owner(tmp_path)
    try:
        _auto(owner, tmp_path)
        request = replace(_request(), side=side)
        sizing = _sizing_input(
            selected_side=side,
            protective_stop_price=D(50) if side == "LONG" else D(150),
            decision_outcome="enter_long" if side == "LONG" else "enter_short",
        )
        result = _admit(owner, request, sizing=sizing)
        envelope = _envelope(
            result.sizing_decision.final_quantity, side="buy" if side == "LONG" else "sell"
        )
        owner.bind_execution_plan_v1(result.reservation.reservation_id, envelope)
        accounting = ProductiveFuturesAccountingSessionV1(
            contract=replace(
                _contract(BOUND.venue_native_id, contract_size="1", min_qty="0.01"),
                quote_currency="USDC",
            ),
            initial_equity=D(100),
        )
        fill = build_simulated_fill_v1(
            fill_id="offline-envelope:" + envelope.envelope_digest,
            instrument_id=envelope.instrument_id,
            side=envelope.side.upper(),
            quantity=envelope.quantity,
            mark_price="100",
            contract=accounting.contract,
            reduce_only=False,
            event_time_unix=MS / 1000 + 1,
        )
        accounting.apply_fill(fill)
        identity = PositionEpisodeIdentityV1(
            "LANE_1",
            BOUND.instrument_id,
            BOUND.venue_native_id,
            "pending-opening",
            side.lower(),
            PositionEpisodeScopeV1(ACCOUNT, "INTERNAL_SIMULATED_EXECUTION"),
        )
        identity = bind_simulated_accounting_episode_identity_v1(
            identity=identity, opening_fill=fill
        )
        args = _args(tmp_path / "adopted-entry", identity)
        args["repository_sha"] = "a" * 40
        episode, receipt = create_risk_bound_simulated_episode_v1(
            owner=owner,
            reservation_id=result.reservation.reservation_id,
            envelope=envelope,
            session=accounting,
            fills=(fill,),
            **args,
        )
        old_owner = owner.active_sum_v1()
        if corrupt:
            value = json.loads(receipt.read_text())
            if corrupt == "unknown-field":
                value["alternate_order_authority"] = True
            if corrupt == "source-prefix":
                value["source_ref"] = "foreign_schema:" + value["source_ref"].split(":", 1)[1]
            if corrupt == "envelope":
                value["envelope"] = {**value["envelope"], "quantity": "99"}
            value["digest"] = digest({k: v for k, v in value.items() if k != "digest"})
            receipt.write_text(json.dumps(value))
            retained = receipt.read_bytes()
            with pytest.raises(ValueError):
                recover_risk_bound_simulated_episode_v1(
                    receipt_path=receipt,
                    owner=owner,
                    envelope=envelope,
                    identity=identity,
                    repository_sha=args["repository_sha"],
                    config_digest=args["config_digest"],
                    writer_session_id="entry-readback",
                )
            assert receipt.read_bytes() == retained
        else:
            restored = recover_risk_bound_simulated_episode_v1(
                receipt_path=receipt,
                owner=owner,
                envelope=envelope,
                identity=identity,
                repository_sha=args["repository_sha"],
                config_digest=args["config_digest"],
                writer_session_id="entry-readback",
            )
            assert restored.entry_source_ref == episode.entry_source_ref
        assert owner.active_sum_v1() == old_owner and owner.stored_reservation_count_v1() == 1
        assert accounting.position.qty == D(envelope.quantity)
    finally:
        owner.close()
