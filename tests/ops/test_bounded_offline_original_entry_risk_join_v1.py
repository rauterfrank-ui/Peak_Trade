"""Natural core ENTER→existing host→computed risk→original envelope; no send."""

from dataclasses import replace
from datetime import datetime
from decimal import Decimal as D

import pytest

from src.risk.decision_bound_model_adapters_v1 import BookLevelV1
from src.ops.bounded_peaktrade_system_composition_v1.handoff_receipts_v1 import (
    OfflineHandoffJournalV1,
)
from src.ops.portfolio_capital_reservation_budget_v1.recovery_v1 import lane_bindings_v1
from src.ops.full_core_live_path_composition_root_v1.current_productive_venue_plan_v1 import (
    try_bind_current_productive_venue_plan_v1,
)
from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
    bind_final_order_envelope_from_venue_plan_v1,
)
from tests.ops.test_bounded_offline_decision_risk_v1 import _request, MS
from tests.ops.test_outer_entry_budget_policy_v1 import (
    _bound,
    _host_enter_cycle,
    _enter_replay,
    _injected,
    _balance_payload,
    Slot,
    join,
)
from tests.ops.test_portfolio_budget_host_v1 import _host, _fetch
from tests.ops.test_full_core_current_productive_enter_live_29p_join_v1 import EPOCH
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    REUSED_BINDING_ACCOUNT_SCOPE as ACCOUNT,
)


def _host_request(context, replay, *, allowed=True):
    request = _request()
    now = int(datetime.fromisoformat(EPOCH.replace("Z", "+00:00")).timestamp() * 1000)
    delta = now - MS
    bound = _bound()
    epoch = lane_bindings_v1({"LANE_1": bound})["LANE_1"]["instrument_epoch"]
    mark = D(str(replay.intermediate.market_context.mark_price))
    item = replace(
        request.data.instruments[0],
        canonical_id=bound.instrument_id,
        native_id=bound.venue_native_id,
        instrument_epoch=epoch,
        contract_multiplier=D("0.01"),
        quote_currency="USDT",
        settlement_currency="USDT",
        price=mark,
        quote_to_capital=D(1) / D("0.999676"),
        price_event_ms=now,
        price_known_ms=now,
        fx_event_ms=now,
        fx_known_ms=now,
        returns=tuple(
            replace(r, close_ms=r.close_ms + delta, known_ms=r.known_ms + delta)
            for r in request.data.instruments[0].returns
        ),
        bids=(BookLevelV1(mark - D("0.01"), D(100)),),
        asks=(BookLevelV1(mark + D("0.01"), D(100)),),
        book_event_ms=now,
        book_known_ms=now,
        adv_event_ms=now,
        adv_known_ms=now,
    )
    data = replace(
        request.data,
        account=ACCOUNT,
        as_of_ms=now,
        portfolio_event_ms=int(context.observed.event_time_unix * 1000),
        portfolio_known_ms=int(context.observed.wall_time_unix * 1000),
        portfolio_source_ref="original-portfolio-truth:" + context.observed.digest(),
        capital_event_ms=now,
        capital_known_ms=now,
        capital_denominator=D(1000),
        instruments=(item,),
    )
    return replace(
        request,
        data=data,
        decision_id=str(replay.evidence.decision_id),
        cycle_id="risk-entry",
        canonical_id=bound.instrument_id,
        native_id=bound.venue_native_id,
        instrument_epoch=epoch,
        policy=replace(
            request.policy, maximum_var_loss_fraction=D("0.9") if allowed else D("0.00000001")
        ),
    )


@pytest.mark.parametrize("allowed", [True, False])
def test_natural_enter_passes_or_is_vetoed_before_original_plan(tmp_path, monkeypatch, allowed):
    now = datetime.fromisoformat(EPOCH.replace("Z", "+00:00")).timestamp()
    host = _host(tmp_path, _fetch(uid=ACCOUNT), clock=lambda: now, expected_account=ACCOUNT)
    try:
        context = host.observe_v1({"LANE_1": _bound()})
        _, cycle, _ = _host_enter_cycle()
        replay = _enter_replay(cycle)
        original = replay.evidence
        request = _host_request(context, replay, allowed=allowed)

        def no_replay(*a, **kw):
            raise AssertionError("No second DoublePlay evaluation")

        monkeypatch.setattr(
            "trading.master_v2.double_play_entry_exit_policy_v0.evaluate_double_play_entry_exit_policy_v0",
            no_replay,
        )
        with OfflineHandoffJournalV1(
            root=tmp_path / "handoffs", session_manifest_digest="a" * 64
        ) as journal:
            result = join(
                replay=replay,
                bound_instrument=_bound(),
                decision_epoch=EPOCH,
                injected=_injected(payload=_balance_payload(avail_eq="1000.00")),
                portfolio_budget_owner=host.owner,
                portfolio_slot=Slot("LANE_1", str(original.decision_id), "risk-entry"),
                host_budget_recovery=context,
                restrictive_risk=request,
                handoff_journal=journal,
            )
        assert (result.status == "PASS") is allowed, result.reason_codes
        assert (
            replay.evidence is original
            and result.post_count == "0"
            and result.permit_created == "false"
        )
        if allowed:
            assert len(list((tmp_path / "handoffs").glob("*.ack.json"))) == 1
            sized = result.replay.intermediate.capital_risk_sizing_decision
            status, reasons, plan = try_bind_current_productive_venue_plan_v1(
                replay=result.replay,
                bound_instrument=_bound(),
                session_id="offline-risk-entry",
                run_id="offline-risk-entry",
                composed_epoch=EPOCH,
                execution_mode="SHADOW",
            )
            assert status.value == "PASS", reasons
            envelope = bind_final_order_envelope_from_venue_plan_v1(
                plan,
                admission_ref="offline-risk-entry",
                provenance_ref="offline-risk-entry",
                creation_epoch=EPOCH,
            )
            rid = result.portfolio_reservation_id
            host.owner.bind_execution_plan_v1(rid, envelope)
            binding = host.owner.reservation_risk_binding_v1(rid)
            assert D(envelope.quantity) == D(binding.final_quantity) == sized.final_quantity
            assert host.owner.active_sum_v1() == sized.canonical_position_sizing.resulting_notional
            assert binding.request.data.portfolio_source_ref == request.data.portfolio_source_ref
            from src.ops.productive_futures_accounting_runtime_binding_v1.accounting_engine_v1 import (
                ProductiveFuturesAccountingSessionV1,
            )
            from src.ops.productive_futures_accounting_runtime_binding_v1.fill_model_v1 import (
                build_simulated_fill_v1,
            )
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
            from tests.ops.test_productive_futures_accounting_runtime_binding_v1 import _contract
            from tests.ops.test_simulated_accounting_entry_source_v1 import _args

            accounting = ProductiveFuturesAccountingSessionV1(
                contract=_contract(envelope.instrument_id), initial_equity=D("999.676")
            )
            fill = build_simulated_fill_v1(
                fill_id="offline-envelope:" + envelope.envelope_digest,
                instrument_id=envelope.instrument_id,
                side=envelope.side.upper(),
                quantity=envelope.quantity,
                mark_price=str(replay.intermediate.market_context.mark_price),
                contract=accounting.contract,
                reduce_only=False,
                event_time_unix=now + 1,
            )
            accounting.apply_fill(fill)
            identity = PositionEpisodeIdentityV1(
                "LANE_1",
                _bound().instrument_id,
                envelope.instrument_id,
                "pending-opening-key",
                "long",
                PositionEpisodeScopeV1(ACCOUNT, "INTERNAL_SIMULATED_EXECUTION"),
            )
            identity = bind_simulated_accounting_episode_identity_v1(
                identity=identity, opening_fill=fill
            )
            args = _args(tmp_path / "episode-source", identity)
            args["repository_sha"] = "a" * 40
            episode, receipt = create_risk_bound_simulated_episode_v1(
                owner=host.owner,
                reservation_id=rid,
                envelope=envelope,
                session=accounting,
                fills=(fill,),
                **args,
            )
            restored = recover_risk_bound_simulated_episode_v1(
                receipt_path=receipt,
                owner=host.owner,
                envelope=envelope,
                identity=identity,
                repository_sha=args["repository_sha"],
                config_digest=args["config_digest"],
                writer_session_id="entry-readback",
            )
            assert restored.entry_source_ref == episode.entry_source_ref
            assert (
                restored.binding.entry_event_time == now + 1
                and restored.binding.entry_price == float(fill.fill_price)
            )
            assert accounting.position.qty == sized.final_quantity
            assert host.owner.active_sum_v1() == sized.canonical_position_sizing.resulting_notional
        else:
            assert result.first_blocker == "RISK_VAR_LIMIT" and host.owner.active_sum_v1() == 0
            assert host.owner.stored_reservation_count_v1() == 0
    finally:
        host.close()
