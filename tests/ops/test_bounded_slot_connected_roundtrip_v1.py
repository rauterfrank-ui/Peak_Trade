"""Natural Core plans and explicit simulated fills through original slot owners."""

from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
import hashlib
import json

import pytest

from src.ops.current_mf_n5_full_autonomy_productive_runtime_orchestrator_v1 import (
    ProductiveFullAutonomyCap24BindContextV1,
    BoundedSlotPostCloseContinuationV1,
    PostCloseContinuationReplayV1,
    run_productive_full_autonomy_n5_runtime_orchestrator_v1 as run,
    orchestrator_v1 as orchestrator,
)
from src.ops.current_mf_n5_ranking_domain_occupied_lane_cap23_n1_produce_join_v1.checked_publication_v1 import (
    publish_checked_lane_selections_v1,
)
from src.ops.current_mf_n5_boundary_occupied_lane_cap24_n1_bind_join_v1.bind_join_v1 import (
    bind_occupied_lane_cap24_n1_instruments_v1,
)
from src.ops.current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1.invoke_join_v1 import (
    invoke_occupied_lane_governed_cycle_n1_consumer_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_full_core_pre_external_closure_v1 import (
    _lane_pair_v1,
)
from src.ops.exit_policy_producer_binding_v1.position_episode_binding_v1 import (
    PositionEpisodeScopeV1,
    PositionEpisodeIdentityV1,
)
from src.ops.exit_policy_producer_binding_v1.simulated_accounting_entry_source_v1 import (
    bind_simulated_accounting_episode_identity_v1,
    create_position_episode_from_simulated_accounting_v1,
)
from src.ops.exit_policy_producer_binding_v1.simulated_accounting_close_v1 import (
    seal_simulated_accounting_episode_flat_v1,
    create_successor_after_sealed_simulated_episode_v1,
)
from src.ops.productive_futures_accounting_runtime_binding_v1.accounting_engine_v1 import (
    ProductiveFuturesAccountingSessionV1,
)
from src.ops.productive_futures_accounting_runtime_binding_v1.fill_model_v1 import (
    build_simulated_fill_v1,
)
from src.ops.productive_reconciliation_runtime_binding_v1.models_v1 import (
    PortfolioTruthSnapshotV1,
    PositionTruthV1,
    ProductiveReconciliationEvidenceV1,
)
from src.ops.productive_reconciliation_runtime_binding_v1.persistence_v1 import (
    persist_reconciliation_bundle_atomic,
)
from src.ops.productive_reconciliation_runtime_binding_v1.single_writer_v1 import (
    ProductivePortfolioSingleWriterV1,
)
from src.ops.productive_futures_ranking_producer_v1.persistence_v1 import (
    persist_ranking_bundle_atomic_v1,
)
from src.ops.productive_futures_ranking_producer_v1.single_writer_v1 import (
    ProductiveRankingSingleWriterV1,
)
from src.ops.productive_futures_ranking_producer_v1.models_v1 import (
    ProductiveFuturesRankingSnapshotV1,
)
from src.ops.portfolio_capital_reservation_budget_v1.host_v1 import PortfolioBudgetHostV1
from src.ops.current_mf_n5_instrument_runtime_identity_closure_v1.lifecycle_v1 import (
    rotation_decision_for_lane_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_post_close_feedback_v1 import (
    PostCloseFeedbackRequestV1,
    PostCloseRankingReviewRequestV1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_treasury_single_source_capital_handoff_v1 import (
    execute_current_productive_treasury_single_source_capital_handoff_v1,
    build_full_core_margin_inputs_from_budget_owner_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_offline_provider_v1 import (
    OfflineExchangeFixtureV1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_post_submit_exchange_reconciliation_lifecycle_join_v1 import (
    run_full_core_post_submit_lifecycle_reconciliation_join_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_post_response_to_ack_mapper_v1 import (
    join_full_core_post_result_to_lifecycle_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_integration_v1 import (
    identity_from_full_core_binding_v1,
)
from tests.ops import test_current_mf_n5_boundary_occupied_lane_cap24_n1_bind_join_v1 as sources
from tests.ops._current_productive_natural_mv2_dp_enter_fixture_v1 import (
    prepare_layered_long_armed_seed_for_pre_external_invoke_v1 as prepare,
    governed_c1_aligned_g17_dk_producer_v1,
)
from tests.ops.test_bounded_multislot_connected_cycle_v1 import ports
from tests.ops._current_productive_canonical_price_test_helpers_v1 import provenance_for_bound_v1
from tests.ops.test_bounded_multislot_entry_budget_v1 import policy
from tests.ops.test_portfolio_budget_host_v1 import _fetch
from tests.ops.test_portfolio_capital_reservation_budget_contract_v1 import _obs, _produce
from tests.ops.test_current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1 import (
    _market_kwargs,
)
from tests.ops.test_current_mf_n5_instrument_runtime_identity_closure_v1 import _positions_payload
from tests.ops.test_productive_futures_accounting_runtime_binding_v1 import _contract
from tests.ops.test_simulated_accounting_entry_source_v1 import _args
from tests.ops.test_full_core_exchange_reconciliation_v1 import _binding
from tests.ops.test_current_productive_full_close_execution_handoff_v1 import _ack_fixture
from tests.ops.test_n1_original_reservation_host_handoff_v1 import (
    synthetic_ports_and_isolation as synthetic_ports_and_isolation,
)

T0 = 1793664000.0


def utc(value):
    return datetime.fromtimestamp(value, timezone.utc).isoformat().replace("+00:00", "Z")


def portfolio_from_accounting(bounds, sessions, event):
    return PortfolioTruthSnapshotV1(
        positions=tuple(
            PositionTruthV1.from_signed(
                instrument_id=bounds[l].instrument_id, signed_quantity=s.position.qty
            )
            for l, s in sessions.items()
            if s.position is not None and s.position.qty != 0
        ),
        event_time_unix=event,
        wall_time_unix=event,
        source_id="explicit_applied_simulated_accounting",
        max_age_seconds=5,
    )


def persist_applied_inventory(root, portfolio, sessions):
    """Original persistence of applied synthetic accounting, never a venue claim."""
    writer = ProductivePortfolioSingleWriterV1(
        state_root=root, session_id="applied-simulated-fills"
    )
    writer.acquire(now_unix=portfolio.event_time_unix)
    try:
        persist_reconciliation_bundle_atomic(
            state_root=root,
            writer=writer,
            portfolio=portfolio,
            evidence=ProductiveReconciliationEvidenceV1(
                capability_id="SIMULATED_ACCOUNTING",
                schema_version="applied_simulated_fills.v1",
                owner="test-fixture",
                classification="APPLIED_SIMULATED_ACCOUNTING",
                alpha_enabled=False,
                pre_state_digest="",
                observed_state_digest=portfolio.digest(),
                post_state_digest=portfolio.digest(),
                reconciliation_decision="NO_RUNTIME_AUTHORIZATION",
                reason_codes=[
                    "APPLIED:" + l + ":" + str(len(s.fill_order)) for l, s in sessions.items()
                ],
            ),
        )
    finally:
        writer.release()


def market(bounds, closes, event, prefix, root):
    """One continuous explicit C1 series; instrument-scoped original producers."""
    kwargs = _market_kwargs(cycle_id_prefix=prefix)
    kwargs.pop("canonical_price_provenance")
    mark = closes[-1]
    rows = [
        [
            str(int((event - (len(closes) - 1 - i) * 60) * 1000)),
            *([str(p)] * 4),
            "10",
            "100",
            "USDT",
            "1",
        ]
        for i, p in enumerate(closes)
    ]
    kwargs.update(
        origin_main_sha="explicit-connected-proof",
        observed_unix=event + 1,
        last_finalized_event_ts_unix=event,
        finalized_closes=tuple(closes),
        mark_px=mark,
        index_px=mark * 0.995,
        bid_px=mark - 0.5,
        ask_px=mark + 0.5,
        candles_payload=None,
        candles_payload_by_lane={
            l: dict(code="0", instId=b.venue_native_id, data=rows) for l, b in bounds.items()
        },
        canonical_price_provenance_by_lane={
            l: provenance_for_bound_v1(bound=b, mark_px=mark, index_px=mark * 0.995)
            for l, b in bounds.items()
        },
        g17_typed_vol_producers={
            l: governed_c1_aligned_g17_dk_producer_v1(
                bound=b,
                anchor_event_ts_unix=event,
                evidence_store_root=root / prefix / l,
                mark_closes=closes,
            )
            for l, b in bounds.items()
        },
        live_29p_injected_by_lane={
            l: ports(b, utc(event + 1), prefix + ":" + l, account="acct-1")
            for l, b in bounds.items()
        },
    )
    return kwargs


def capital(host, bound, event):
    body = json.dumps(dict(available_usdc="1000", observed_at=utc(event)), sort_keys=True)
    observation = replace(
        _obs(value="1000", epoch=utc(event)),
        provenance_digest=hashlib.sha256(body.encode()).hexdigest(),
    )
    result = execute_current_productive_treasury_single_source_capital_handoff_v1(
        margin_observation=observation,
        instrument_id=bound.instrument_id,
        body_sha256=observation.provenance_digest,
        fresh_pretrade_get_status="TRUSTED_PRESENT",
        live_account_bound_status="TRUSTED_PRESENT",
        u04_p01_host_inputs=build_full_core_margin_inputs_from_budget_owner_v1(
            raw_acct_lv="2", budget_owner=host.owner
        ),
    )
    assert not result.fail_closed, result.reason_codes
    return result


def connected_close(tmp_path, monkeypatch, count, lane):
    monkeypatch.setattr(sources, "OBSERVED_UNIX", T0 - 3700)
    monkeypatch.setattr(sources, "SOURCE_EVENT", str(int((T0 - 3700) * 1000)))
    chain = sources._persist_universe_and_ranking(
        tmp_path, sources._five_rows() + [sources._perp("NEAR-USDT-SWAP", base="NEAR")]
    )
    natives = [r["instId"] for r in sources._five_rows()][:count]
    membership = sources._membership(
        chain["ranking"], [sources._cid(chain["ranking"], n) for n in natives]
    )
    topology = tmp_path / "topology"
    writer = sources._held_writer(topology)
    publication = publish_checked_lane_selections_v1(
        membership=membership,
        ranking_snapshot=chain["ranking"],
        topology_state_root_base=topology,
        writer=writer,
        repository_sha=sources.REPO_SHA,
        producer_observed_at_unix=T0 - 3700,
    )
    bounds = bind_occupied_lane_cap24_n1_instruments_v1(
        selections=publication.selections,
        topology_state_root_base=topology,
        ranking_state_root=chain["ranking_root"],
        universe_state_root=chain["universe_root"],
        reconciliation_state_root=chain["recon_root"],
        observed_portfolio=PortfolioTruthSnapshotV1(
            event_time_unix=T0 - 3700, wall_time_unix=T0 - 3700
        ),
        mark_price_by_native_id=chain["mark_price_by_native_id"],
        repository_sha=sources.REPO_SHA,
        session_id="initial",
        now_unix=T0 - 3700,
    )
    pairs = {}
    closes = None
    for l, b in bounds.items():
        slot = next(s for s in publication.topology.occupied_slots() if s.lane_id == l)
        root = Path(slot.lane_state_root)
        _, closes, _, event, _ = prepare(
            bound=b,
            g17_typed_vol_producer=None,
            lane_state_root=root.parent,
            lane_id=l,
            arm_event_ts_unix=T0 - 3620,
            g17_evidence_root=root,
        )
        assert event == T0 - 3600
        pairs[l] = _lane_pair_v1(lane_state_root=root.parent, bound=b, lane_id=l)
    host = PortfolioBudgetHostV1(
        root=tmp_path / "host",
        private_rest_fetch=_fetch(uid="acct-1"),
        repository_sha=sources.REPO_SHA,
        session_id="connected",
        expected_account_identity="acct-1",
        durable_mode="create",
        clock=lambda: T0 - 3599,
        execution_environment="INTERNAL_SIMULATED_EXECUTION",
        entry_budget_policy=policy(),
    )
    recovery = host.observe_v1(bounds)
    kwargs = market(bounds, closes, event, "initial-entry", tmp_path / "g17")
    kwargs.update(portfolio_budget_owner=host.owner, host_budget_recovery=recovery)
    entries = invoke_occupied_lane_governed_cycle_n1_consumer_v1(pairs, **kwargs)
    scope = PositionEpisodeScopeV1("acct-1", "INTERNAL_SIMULATED_EXECUTION")
    sessions = {}
    episodes = {}
    fills = {}
    holds = {}
    for l, r in entries.items():
        cycle = r.governed_cycle_result
        order = cycle.final_order_envelope
        assert order is not None, (l, cycle.first_genuine_blocker)
        assert r.s7_invocation.cycle_result.decision_outcome == "enter_long"
        holds[l] = cycle.extra["PORTFOLIO_RESERVATION_ID"]
        session = ProductiveFuturesAccountingSessionV1(
            contract=_contract(order.instrument_id, contract_size="0.01", min_qty="1")
        )
        fill = build_simulated_fill_v1(
            fill_id="original-plan:" + order.envelope_digest,
            instrument_id=order.instrument_id,
            side=order.side.upper(),
            quantity=order.quantity,
            mark_price=str(closes[-1]),
            contract=session.contract,
            event_time_unix=event + 1,
        )
        session.apply_fill(fill)
        sessions[l] = session
        fills[l] = [fill]
        b = bounds[l]
        identity = bind_simulated_accounting_episode_identity_v1(
            identity=PositionEpisodeIdentityV1(
                l, b.instrument_id, b.venue_native_id, "pending-opening", "long", scope
            ),
            opening_fill=fill,
        )
        episodes[l] = create_position_episode_from_simulated_accounting_v1(
            **_args(tmp_path / "episodes" / l, identity), session=session, fills=(fill,)
        )
    # Append 61 minute bars, preserving every overlapping historical event.
    mark = closes[-1]
    closes = tuple(closes) + tuple(mark + 0.1 * i for i in range(1, 62))
    event = T0 + 60
    observed = portfolio_from_accounting(bounds, sessions, event + 1)
    persist_applied_inventory(host.root / "reconciliation", observed, sessions)
    kwargs = market(bounds, closes, event, "natural-time-exit", tmp_path / "g17")
    kwargs.update(
        portfolio_budget_owner=host.owner,
        host_budget_recovery=recovery,
        observed_portfolio=observed,
        position_episode_bindings=episodes,
        position_episode_scope=scope,
        occupancy_payloads=_positions_payload(
            *[(bounds[l].venue_native_id, "net", s.position.qty) for l, s in sessions.items()]
        ),
    )
    exits = invoke_occupied_lane_governed_cycle_n1_consumer_v1(pairs, **kwargs)
    for l, r in exits.items():
        assert r.position_management_close_intent is not None, (
            l,
            r.governed_cycle_result.first_genuine_blocker,
            r.s7_invocation.cycle_result.replay.intermediate.entry_exit_decision,
        )
        assert (
            r.s7_invocation.cycle_result.replay.intermediate.entry_exit_decision.exit_class.value
            == "time_exit"
        )
    execution = exits[lane].governed_cycle_result.position_management_execution_handoff
    assert execution is not None, exits[lane].governed_cycle_result.first_genuine_blocker
    order = execution.envelope
    fill = build_simulated_fill_v1(
        fill_id="original-close:" + order.envelope_digest,
        instrument_id=order.instrument_id,
        side=order.side.upper(),
        quantity=order.quantity,
        mark_price=str(closes[-1]),
        contract=sessions[lane].contract,
        event_time_unix=T0 + 62,
        reduce_only=True,
    )
    sessions[lane].apply_fill(fill)
    fills[lane].append(fill)
    seal_simulated_accounting_episode_flat_v1(
        episode=episodes[lane],
        accounting_session=sessions[lane],
        fills=tuple(fills[lane]),
        bound=bounds[lane],
        occupancy_payloads=_positions_payload((bounds[lane].venue_native_id, "net", Decimal(0))),
        observed_portfolio=PortfolioTruthSnapshotV1(
            positions=(
                PositionTruthV1.from_signed(
                    instrument_id=bounds[lane].instrument_id, signed_quantity=Decimal(0)
                ),
            ),
            event_time_unix=T0 + 63,
            wall_time_unix=T0 + 63,
            max_age_seconds=5,
        ),
        observed_unix=T0 + 63,
        source_archive_root=tmp_path / "episodes" / lane / "sources",
        cursor_store_root=Path(pairs[lane][0].lane_state_root),
        expected_scope=scope,
        writer_session_id="applied-original-close",
    )
    assert sessions[lane].position is None
    observed = portfolio_from_accounting(bounds, sessions, T0 + 64)
    persist_applied_inventory(host.root / "reconciliation", observed, sessions)
    host.fetch = _fetch(
        uid="acct-1",
        positions=[
            dict(instId=bounds[l].venue_native_id, posSide="net", pos=str(s.position.qty))
            for l, s in sessions.items()
            if s.position is not None and s.position.qty
        ],
    )
    host.clock = lambda: T0 + 65
    recovery = host.observe_v1(bounds)
    recovery.recover_v1(host.owner, _produce(value="1000", epoch=utc(T0 + 64)))
    return dict(
        chain=chain,
        membership=membership,
        topology=topology,
        writer=writer,
        bounds=bounds,
        host=host,
        holds=holds,
        episodes=episodes,
        sessions=sessions,
        scope=scope,
        closes=closes,
        recovery=recovery,
        execution=execution,
        fills=fills,
    )


def roundtrip(
    tmp_path, monkeypatch, count, lane, replacement, fault=None, *, expected_loss_exhausted=False
):
    world = connected_close(tmp_path, monkeypatch, count, lane)
    host = world["host"]
    writer = world["writer"]
    try:
        old = world["bounds"]
        prior = world["membership"]
        chain = world["chain"]
        execution = world["execution"]
        order = execution.envelope
        target = "NEAR-USDT-SWAP" if replacement else old[lane].venue_native_id
        wanted = {b.venue_native_id for l, b in old.items() if l != lane} | {target}
        initial = ProductiveFuturesRankingSnapshotV1.from_dict(chain["ranking"])
        ordered = sorted(
            initial.ranked_candidates, key=lambda c: (c.venue_native_id != target, c.rank)
        )
        ranking = replace(
            initial,
            ranking_snapshot_id="roundtrip-fresh",
            event_time=utc(T0 + 120),
            ranked_candidates=tuple(
                replace(
                    c,
                    rank=i + 1,
                    eligibility_status="ELIGIBLE" if c.venue_native_id in wanted else "INELIGIBLE",
                )
                for i, c in enumerate(ordered)
            ),
        ).with_integrity_digest()
        rw = ProductiveRankingSingleWriterV1(
            state_root=chain["ranking_root"],
            writer_identity="synthetic-ranking",
            session_id="fresh",
        )
        rw.acquire(now_unix=T0 + 121)
        try:
            persist_ranking_bundle_atomic_v1(
                state_root=chain["ranking_root"],
                writer=rw,
                snapshot=ranking,
                evidence={"ok": True, "capability_id": "CAPABILITY_2_2"},
            )
        finally:
            rw.release()
        host.clock = lambda: T0 + 121
        recovery = host.observe_v1(old)
        recovery.recover_v1(host.owner, _produce(value="1000", epoch=utc(T0 + 120)))
        fresh = capital(host, old[lane], T0 + 121)
        binding = replace(
            _binding(),
            account_scope="acct-1",
            execution_mode="INTERNAL_SIMULATED_EXECUTION",
            instrument_id=order.instrument_id,
            native_id=order.instrument_id,
            selected_direction="EXIT",
            order_side=order.side,
            final_quantity=order.quantity,
            order_type="market",
            order_price="",
            clordid=order.client_order_id,
            canonical_decision_id=execution.source.canonical_intent.decision_id,
            envelope_digest=order.envelope_digest,
        )
        ack = join_full_core_post_result_to_lifecycle_v1(
            result=_ack_fixture(order), sent_clordid=order.client_order_id, submit_count=1
        )
        fixture = OfflineExchangeFixtureV1(
            pending_orders={"code": "0", "data": []},
            order_history={
                "code": "0",
                "data": [
                    dict(
                        instId=order.instrument_id,
                        clOrdId=order.client_order_id,
                        ordId="offline-close-order",
                        state="filled",
                        sz=order.quantity,
                        accFillSz=order.quantity,
                        uTime=str(int((T0 + 62) * 1000)),
                        sCode="0",
                    )
                ],
            },
            positions={
                "code": "0",
                "data": [
                    dict(
                        instId=order.instrument_id,
                        pos="0",
                        posSide="net",
                        uTime=str(int((T0 + 63) * 1000)),
                    )
                ],
            },
        )
        lifecycle_args = dict(
            post_submit_join=ack,
            binding=binding,
            decision_outcome="EXIT",
            venue_plan_identity=order.client_order_id,
            envelope_identity=order.envelope_digest,
            submit_attempt_id="actual-core-close",
            local_durable_state_version="v1",
            offline_fixture=fixture,
        )
        lifecycle = run_full_core_post_submit_lifecycle_reconciliation_join_v1(**lifecycle_args)
        identity = identity_from_full_core_binding_v1(
            binding,
            decision_outcome="EXIT",
            venue_plan_identity=order.client_order_id,
            envelope_identity=order.envelope_digest,
            submit_attempt_id="actual-core-close",
            local_durable_state_version="v1",
            exchange_ord_id=ack.venue_order_id,
        )
        request = PostCloseFeedbackRequestV1(
            execution,
            old[lane],
            utc(T0 + 121),
            fresh,
            host.owner,
            (world["holds"][lane],),
            host.owner.budget_state_v1().observation_id,
            PostCloseRankingReviewRequestV1(
                ranking,
                replace(
                    prior.cap22_provenance,
                    ranking_snapshot_id=ranking.ranking_snapshot_id,
                    ranking_integrity_digest=ranking.integrity_digest,
                    ranking_event_time=ranking.event_time,
                ),
                prior,
                (prior,),
            ),
        )
        context = BoundedSlotPostCloseContinuationV1(
            lifecycle, identity, request, tmp_path / "membership", recovery.observed, 5, host=host
        )
        closes = world["closes"] + (world["closes"][-1] + 2,)
        cap = ProductiveFullAutonomyCap24BindContextV1(
            chain["ranking_root"],
            chain["universe_root"],
            host.root / "reconciliation",
            recovery.observed,
            {n: str(closes[-1]) for n in chain["mark_price_by_native_id"]},
            "next-binding",
            T0 + 121,
        )
        kwargs = market(old, closes, T0 + 120, "post-close-next-core", tmp_path / "g17")
        kwargs.update(
            host_budget_recovery=recovery,
            observed_portfolio=recovery.observed,
            position_episode_bindings={l: e for l, e in world["episodes"].items() if l != lane},
            position_episode_scope=world["scope"],
            occupancy_payloads=_positions_payload(
                *[
                    (old[l].venue_native_id, "net", s.position.qty)
                    for l, s in world["sessions"].items()
                    if s.position is not None and s.position.qty
                ]
            ),
        )
        # Capture actual Cap24 output solely to feed synthetic read ports with
        # that exact new binding. The original binder and all Core decisions run.
        original = orchestrator.bind_occupied_lane_cap24_n1_instruments_v1
        refreshed = {}

        def capture(**args):
            result = original(**args)
            refreshed.update(result)
            for l, b in result.items():
                kwargs["live_29p_injected_by_lane"][l] = ports(
                    b, utc(T0 + 121), "post-close-next-core:" + l, account="acct-1"
                )
                kwargs["g17_typed_vol_producers"][l] = governed_c1_aligned_g17_dk_producer_v1(
                    bound=b,
                    anchor_event_ts_unix=T0 + 120,
                    evidence_store_root=tmp_path / "g17" / "new-binding" / l,
                    mark_closes=closes,
                )
                kwargs["candles_payload_by_lane"][l]["instId"] = b.venue_native_id
            return result

        monkeypatch.setattr(orchestrator, "bind_occupied_lane_cap24_n1_instruments_v1", capture)
        before = host.owner.risk_snapshot_v1()["state"]
        args = dict(
            membership=prior,
            ranking_snapshot=ranking.to_dict(),
            topology_state_root_base=world["topology"],
            lane_assignment_writer=writer,
            cap24_bind=cap,
            repository_sha=sources.REPO_SHA,
            producer_observed_at_unix=T0 + 121,
            target_cardinality=count,
            portfolio_budget_owner=host.owner,
            replacement_admission_by_lane={
                lane: rotation_decision_for_lane_v1(
                    venue_flat=True, reconciled=True, lane_health_allows_replacement=True
                )
            },
            post_close_continuation=context,
        )
        if fault is not None:
            from src.ops.current_mf_n5_full_autonomy_occupied_lane_n1_host_join_readiness_v1 import (
                consumer_completion_v1 as completion,
            )
            from src.ops.current_mf_n5_full_autonomy_productive_runtime_orchestrator_v1 import (
                bounded_slot_post_close_v1 as bounded,
            )
            from src.ops.current_mf_n5_full_autonomy_productive_runtime_orchestrator_v1 import (
                post_close_continuation_v1 as receipts,
            )
            from src.ops.current_mf_n5_full_autonomy_occupied_lane_n1_host_join_readiness_v1 import (
                readiness_join_v1 as ready,
            )

            persist = completion.persist_n1_consumer_completion_v1
            write = bounded._write_receipt
            finish = completion._finish_publication

            def broken_persist(projections, **kw):
                if lane in projections:
                    raise OSError("injected missing original lane output")
                return persist(projections, **kw)

            def broken_write(path, record):
                if record["phase"] == "ACKED":
                    raise OSError("injected missing group ACK")
                return write(path, record)

            def broken_finish(path, pending, expected):
                if expected["lane_id"] == lane:
                    raise OSError("injected prepared publication interruption")
                return finish(path, pending, expected)

            if fault == "missing_lane":
                monkeypatch.setattr(completion, "persist_n1_consumer_completion_v1", broken_persist)
            elif fault == "pending_lane":
                monkeypatch.setattr(completion, "_finish_publication", broken_finish)
            else:
                monkeypatch.setattr(bounded, "_write_receipt", broken_write)
            with pytest.raises(OSError, match="injected"):
                run(**args, **kwargs)
            assert host.closed
            path = writer.state_root / "post_close" / (order.envelope_digest + ".json")
            record = receipts._read_receipt(path)
            assert record["phase"] == "CONSUMING"
            ledgers = {
                str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in world["topology"].rglob("governed_cycle_orchestrator_ledger_v1.json")
            }

            def forbidden(*a, **kw):
                pytest.fail("Uncertain group must never consume Core twice")

            monkeypatch.setattr(
                ready, "invoke_occupied_lane_governed_cycle_n1_consumer_v1", forbidden
            )
            monkeypatch.setattr(completion, "persist_n1_consumer_completion_v1", persist)
            monkeypatch.setattr(completion, "_finish_publication", finish)
            monkeypatch.setattr(bounded, "_write_receipt", write)
            # Cold reopen reads the original budget; no new account admission is
            # inferred from historical completion records.
            host = PortfolioBudgetHostV1(
                root=host.root,
                private_rest_fetch=host.fetch,
                repository_sha=sources.REPO_SHA,
                session_id="cold-group",
                expected_account_identity="acct-1",
                durable_mode="recover",
                clock=lambda: T0 + 122,
                execution_environment="INTERNAL_SIMULATED_EXECUTION",
                entry_budget_policy=policy(),
            )
            from src.ops.single_selected_future_runtime_binding_v1.models_v1 import (
                BoundInstrumentV1,
            )

            host.observe_v1({l: BoundInstrumentV1(**b) for l, b in record["bound_by_lane"].items()})
            assert not host.owner.budget_state_v1().admitted
            replay_args = {
                **args,
                "portfolio_budget_owner": host.owner,
                "post_close_continuation": replace(
                    context, host=host, request=replace(request, budget_owner=host.owner)
                ),
            }
            if fault == "missing_lane":
                with pytest.raises(ValueError, match="OUTCOME_UNCERTAIN"):
                    run(**replay_args, **kwargs)
                assert receipts._read_receipt(path)["phase"] == "CONSUMING"
            else:
                replay = run(**replay_args, **kwargs)
                assert isinstance(replay, PostCloseContinuationReplayV1)
                assert replay.receipt["phase"] == "ACKED"
                assert set(replay.receipt["consumed"]) == set(old)
                assert not host.owner.budget_state_v1().admitted
            assert ledgers == {
                str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in world["topology"].rglob("governed_cycle_orchestrator_ledger_v1.json")
            }
            assert all(
                row in host.owner.risk_snapshot_v1()["state"]["reservations"]
                for row in before["reservations"]
                if row["slot_id"] != lane
            )
            return
        result = run(**args, **kwargs)
        receipt = result.post_close_continuation_receipt
        assert receipt["phase"] == "ACKED"
        assert set(receipt["consumed"]) == set(old)
        assert set(refreshed) == {lane}
        assert host.bindings[lane].venue_native_id == target
        assert all(host.bindings[l] == b for l, b in old.items() if l != lane)
        assert all(
            row in host.owner.risk_snapshot_v1()["state"]["reservations"]
            for row in before["reservations"]
            if row["slot_id"] != lane
        )
        assert all(
            p.n1_consumer_result.s7_invocation is not None
            for p in result.readiness_projections.values()
        )
        assert not result.post_allowed and not result.external_effect_authorized
        replay = run(**args, **kwargs)
        assert isinstance(replay, PostCloseContinuationReplayV1)
        assert replay.receipt == receipt
        from src.ops.mf_membership_context_artifact_contract_v1 import (
            membership_context_artifact_from_dict,
        )

        membership = membership_context_artifact_from_dict(receipt["membership"])
        next_bounds = dict(host.bindings)
        decisions = []
        foreign_holds = {l: host.owner.active_slot_sum_v1(l) for l in next_bounds if l != lane}
        for step in range(1, 9):
            event = T0 + 120 + step * 60
            closes = closes + (closes[-1] + 20,)
            host.clock = lambda: event + 1
            recovery = host.observe_v1(next_bounds)
            next_kwargs = market(
                next_bounds, closes, event, f"natural-follow-{step}", tmp_path / "g17"
            )
            next_kwargs.update(
                host_budget_recovery=recovery,
                observed_portfolio=recovery.observed,
                position_episode_bindings={l: e for l, e in world["episodes"].items() if l != lane},
                position_episode_scope=world["scope"],
                occupancy_payloads=kwargs["occupancy_payloads"],
            )
            next_cap = replace(
                cap,
                now_unix=event + 1,
                observed_portfolio=recovery.observed,
                mark_price_by_native_id={n: str(closes[-1]) for n in cap.mark_price_by_native_id},
            )
            next_args = {
                **args,
                "membership": membership,
                "post_close_continuation": None,
                "replacement_admission_by_lane": None,
                "cap24_bind": next_cap,
                "producer_observed_at_unix": event + 1,
            }
            follow = run(**next_args, **next_kwargs)
            core = follow.readiness_projections[lane].n1_consumer_result
            decisions.append(
                (
                    core.s7_invocation.cycle_result.decision_outcome,
                    core.governed_cycle_result.first_genuine_blocker,
                )
            )
            assert all(
                host.owner.active_slot_sum_v1(l) == hold for l, hold in foreign_holds.items()
            )
            assert all(host.bindings[l] == b for l, b in next_bounds.items())
            assert all(
                p.n1_consumer_result.s7_invocation is not None
                for p in follow.readiness_projections.values()
            )
            if core.governed_cycle_result.final_order_envelope is not None:
                assert not expected_loss_exhausted, "Exhausted test slot received another Entry"
                assert core.s7_invocation.cycle_result.decision_outcome in {
                    "enter_long",
                    "enter_short",
                }
                assert 0 < host.owner.active_slot_sum_v1(lane) <= 25
                assert core.governed_cycle_result.final_order_envelope.instrument_id == target
                # Apply that exact new plan and bind its own new opening episode.
                order = core.governed_cycle_result.final_order_envelope
                session = (
                    world["sessions"][lane]
                    if not replacement
                    else ProductiveFuturesAccountingSessionV1(
                        contract=_contract(target, contract_size="0.01", min_qty="1")
                    )
                )
                fill = build_simulated_fill_v1(
                    fill_id="next-original-plan:" + order.envelope_digest,
                    instrument_id=target,
                    side=order.side.upper(),
                    quantity=order.quantity,
                    mark_price=str(closes[-1]),
                    contract=session.contract,
                    event_time_unix=event + 1,
                )
                session.apply_fill(fill)
                history = tuple(world["fills"][lane]) + (fill,) if not replacement else (fill,)
                bound = next_bounds[lane]
                previous = world["episodes"][lane]
                identity = bind_simulated_accounting_episode_identity_v1(
                    identity=PositionEpisodeIdentityV1(
                        lane,
                        bound.instrument_id,
                        bound.venue_native_id,
                        "pending-opening",
                        "long" if order.side == "buy" else "short",
                        world["scope"],
                    ),
                    opening_fill=fill,
                )
                episode_args = _args(tmp_path / "next-episode" / lane, identity)
                if replacement:
                    episode = create_position_episode_from_simulated_accounting_v1(
                        **episode_args, session=session, fills=history
                    )
                else:
                    episode = create_successor_after_sealed_simulated_episode_v1(
                        prior_identity=previous.identity,
                        prior_state_root=previous.binding.state_root,
                        prior_repository_sha=previous.binding.repository_sha,
                        prior_config_digest=previous.binding.config_digest,
                        prior_initial_source_ref=previous.entry_source_ref,
                        **episode_args,
                        accounting_session=session,
                        fills=history,
                    )
                assert episode.identity.episode_id != previous.identity.episode_id
                world["episodes"][lane] = episode
                world["sessions"][lane] = session
                occupied_event = event + 60
                closes = closes + (closes[-1] + 20,)
                observed = portfolio_from_accounting(
                    next_bounds, world["sessions"], occupied_event + 1
                )
                persist_applied_inventory(host.root / "reconciliation", observed, world["sessions"])
                host.fetch = _fetch(
                    uid="acct-1",
                    positions=[
                        dict(
                            instId=next_bounds[l].venue_native_id,
                            posSide="net",
                            pos=str(s.position.qty),
                        )
                        for l, s in world["sessions"].items()
                    ],
                )
                host.clock = lambda: occupied_event + 1
                recovery = host.observe_v1(next_bounds)
                occupied_kwargs = market(
                    next_bounds, closes, occupied_event, "new-entry-filled", tmp_path / "g17"
                )
                occupied_kwargs.update(
                    host_budget_recovery=recovery,
                    observed_portfolio=recovery.observed,
                    position_episode_bindings=world["episodes"],
                    position_episode_scope=world["scope"],
                    occupancy_payloads=_positions_payload(
                        *[
                            (next_bounds[l].venue_native_id, "net", s.position.qty)
                            for l, s in world["sessions"].items()
                        ]
                    ),
                )
                occupied_cap = replace(
                    next_cap,
                    now_unix=occupied_event + 1,
                    observed_portfolio=recovery.observed,
                    mark_price_by_native_id={
                        n: str(closes[-1]) for n in cap.mark_price_by_native_id
                    },
                )
                occupied = run(
                    **{
                        **next_args,
                        "cap24_bind": occupied_cap,
                        "producer_observed_at_unix": occupied_event + 1,
                    },
                    **occupied_kwargs,
                )
                assert all(
                    p.n1_consumer_result.s7_invocation.cycle_result.decision_outcome
                    not in {"enter_long", "enter_short"}
                    for p in occupied.readiness_projections.values()
                )
                assert all(
                    host.owner.active_slot_sum_v1(l) == hold for l, hold in foreign_holds.items()
                )
                checkpoint = host.owner.risk_snapshot_v1()["state"]
                host.close()
                host = PortfolioBudgetHostV1(
                    root=host.root,
                    private_rest_fetch=host.fetch,
                    repository_sha=sources.REPO_SHA,
                    session_id="cold-after-new-entry",
                    expected_account_identity="acct-1",
                    durable_mode="recover",
                    clock=lambda: occupied_event + 2,
                    execution_environment="INTERNAL_SIMULATED_EXECUTION",
                    entry_budget_policy=policy(),
                )
                cold = host.observe_v1(next_bounds)
                assert not host.owner.budget_state_v1().admitted
                cold.recover_v1(host.owner, _produce(value="1000", epoch=utc(occupied_event + 2)))
                assert (
                    checkpoint["reservations"]
                    == host.owner.risk_snapshot_v1()["state"]["reservations"]
                )
                break
        else:
            if expected_loss_exhausted:
                assert any(
                    "TEST_SLOT_25_USDC_LOSS_BUDGET_EXHAUSTED" in str(blocker)
                    for _, blocker in decisions
                ), decisions
                assert host.owner.active_slot_sum_v1(lane) == 0
                state = host.owner.test_slot_loss_state_v1(lane)
                assert state["exhausted"] and state["remaining_loss_allowance_usdc"] == "0"
                assert len(state["records"]) == 1
                host.close()
                host = PortfolioBudgetHostV1(
                    root=host.root,
                    private_rest_fetch=host.fetch,
                    repository_sha=sources.REPO_SHA,
                    session_id="cold-exhausted-slot",
                    expected_account_identity="acct-1",
                    durable_mode="recover",
                    clock=lambda: event + 2,
                    execution_environment="INTERNAL_SIMULATED_EXECUTION",
                    entry_budget_policy=policy(),
                )
                cold = host.observe_v1(next_bounds)
                assert not host.owner.budget_state_v1().admitted
                cold.recover_v1(host.owner, _produce(value="1000", epoch=utc(event + 2)))
                assert host.owner.test_slot_loss_state_v1(lane) == state
                assert all(
                    host.owner.active_slot_sum_v1(l) == hold for l, hold in foreign_holds.items()
                )
                return
            pytest.fail("No natural follow-up Entry: " + repr(decisions))
    finally:
        host.close()
        writer.release()


@pytest.mark.parametrize(
    "count,lane", [(2, f"LANE_{i}") for i in range(1, 3)] + [(5, f"LANE_{i}") for i in range(1, 6)]
)
@pytest.mark.parametrize("replacement", [False, True])
def test_original_natural_entry_fill_close_rebind_and_next_entry_fill(
    tmp_path, monkeypatch, count, lane, replacement
):
    roundtrip(tmp_path, monkeypatch, count, lane, replacement)


@pytest.mark.parametrize("fault", ["missing_lane", "pending_lane", "group_ack"])
def test_group_completion_failure_uses_only_original_outputs_on_cold_replay(
    tmp_path, monkeypatch, fault
):
    roundtrip(tmp_path, monkeypatch, 5, "LANE_5", True, fault=fault)
