"""Original close → original writers/recovery → actual next Core, injected offline."""

from dataclasses import replace
from datetime import datetime
from decimal import Decimal
import json

import pytest

from src.ops.current_mf_n5_full_autonomy_productive_runtime_orchestrator_v1 import (
    ProductiveFullAutonomyCap24BindContextV1,
    ProductiveN1PostCloseContinuationV1,
    PostCloseContinuationReplayV1,
    PostCloseContinuationError,
    run_productive_full_autonomy_n5_runtime_orchestrator_v1,
)
from src.ops.current_mf_n5_boundary_occupied_lane_cap24_n1_bind_join_v1.bind_join_v1 import (
    bind_occupied_lane_cap24_n1_instruments_v1,
)
from src.ops.current_mf_n5_ranking_domain_occupied_lane_cap23_n1_produce_join_v1.checked_publication_v1 import (
    publish_checked_lane_selections_v1,
)
from src.ops.current_mf_n5_instrument_runtime_identity_closure_v1.lifecycle_v1 import (
    rotation_decision_for_lane_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_post_submit_exchange_reconciliation_lifecycle_join_v1 import (
    run_full_core_post_submit_lifecycle_reconciliation_join_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_integration_v1 import (
    identity_from_full_core_binding_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_treasury_single_source_capital_handoff_v1 import (
    execute_current_productive_treasury_single_source_capital_handoff_v1,
    build_full_core_margin_inputs_from_budget_owner_v1,
)
from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
    PortfolioCapitalReservationBudgetOwnerV1,
)
from src.ops.productive_reconciliation_runtime_binding_v1.models_v1 import PortfolioTruthSnapshotV1
from src.ops.productive_futures_ranking_producer_v1.persistence_v1 import (
    persist_ranking_bundle_atomic_v1,
)
from src.ops.productive_futures_ranking_producer_v1.single_writer_v1 import (
    ProductiveRankingSingleWriterV1,
)
from tests.ops import test_current_mf_n5_boundary_occupied_lane_cap24_n1_bind_join_v1 as sources
from tests.ops import (
    test_current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1 as market,
)
from tests.ops.test_current_productive_post_close_feedback_v1 import _case
from tests.ops.test_durable_portfolio_budget_recovery_v1 import _auto
from tests.ops.test_portfolio_capital_reservation_budget_contract_v1 import _produce, _obs
from src.ops.current_mf_n5_full_autonomy_productive_runtime_orchestrator_v1 import (
    orchestrator_v1 as orchestrator,
    post_close_continuation_v1 as continuation,
)

EPOCH = "2026-11-03T00:00:00Z"
T0 = datetime.fromisoformat(EPOCH.replace("Z", "+00:00")).timestamp()
NEXT = "2026-11-03T00:01:01Z"
NOW = T0 + 62


@pytest.fixture(autouse=True)
def isolated_capital_observation_ordering():
    # Each test creates an independent synthetic account/owner world. Keep
    # ordering guards active inside that world, including all replay negatives.
    from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_available_for_sizing_base_binding_v1 import (
        clear_current_productive_base_binding_state_v1,
    )

    clear_current_productive_base_binding_state_v1()
    yield
    clear_current_productive_base_binding_state_v1()


def _fixture(
    tmp_path,
    monkeypatch,
    *,
    replace_instrument=False,
    remaining="0",
    selection_age=None,
    budget_root=None,
):
    age = (3600 if replace_instrument else 0) if selection_age is None else selection_age
    monkeypatch.setattr(sources, "OBSERVED_UNIX", T0 - age)
    monkeypatch.setattr(sources, "SOURCE_EVENT", str(int((T0 - age) * 1000)))
    chain = sources._persist_universe_and_ranking(tmp_path, sources._five_rows())
    old = sources._cid(chain["ranking"], "ETH-USDT-SWAP")
    membership = sources._membership(chain["ranking"], [old])
    topology = tmp_path / "topology"
    writer = sources._held_writer(topology)
    observed0 = PortfolioTruthSnapshotV1(
        source_id="injected-original-flat",
        positions=(),
        event_time_unix=T0,
        wall_time_unix=T0,
        max_age_seconds=5,
    )
    publication = publish_checked_lane_selections_v1(
        membership=membership,
        ranking_snapshot=chain["ranking"],
        topology_state_root_base=topology,
        writer=writer,
        repository_sha=sources.REPO_SHA,
        producer_observed_at_unix=T0,
    )
    bound = bind_occupied_lane_cap24_n1_instruments_v1(
        selections=publication.selections,
        topology_state_root_base=topology,
        ranking_state_root=chain["ranking_root"],
        universe_state_root=chain["universe_root"],
        reconciliation_state_root=chain["recon_root"],
        observed_portfolio=observed0,
        mark_price_by_native_id=chain["mark_price_by_native_id"],
        repository_sha=sources.REPO_SHA,
        session_id="original-binding",
        now_unix=T0,
    )["LANE_1"]
    close, memory_owner, _, _ = _case(
        monkeypatch,
        initial_ranking=chain["ranking"],
        bound_instrument=bound,
        prior_membership=membership,
        state="partially_filled" if remaining != "0" else "filled",
        remaining=remaining,
    )
    memory_owner.close()
    owner = PortfolioCapitalReservationBudgetOwnerV1(
        durable_root=budget_root or tmp_path / "budget",
        durable_account_identity="acct-1",
        durable_mode="create",
        durable_lane_bindings={"LANE_1": bound},
    )
    _auto(
        owner,
        tmp_path,
        output=_produce(epoch=EPOCH),
        observed=observed0,
        bindings={"LANE_1": bound},
        now=T0,
    )
    oid = owner.budget_state_v1().observation_id
    reservation = owner.try_reserve_v1(
        slot_id="LANE_1",
        decision_id="original-entry",
        cycle_id="original-cycle",
        observation_id=oid,
        amount=Decimal("40"),
    ).reservation
    rid = str(reservation.reservation_id)
    owner.commit_internal_pre_external_effect_v1(rid)
    request = close.pop("post_close_feedback_request")
    target = "SOL-USDT-SWAP" if replace_instrument else "ETH-USDT-SWAP"
    # An explicit injected rank order: the replacement must actually beat ETH.
    # This tests consumption of ranking, not natural economic ranking quality.
    ordered = sorted(
        request.ranking.snapshot.ranked_candidates,
        key=lambda c: (c.venue_native_id != target, c.rank),
    )
    ranking = replace(
        request.ranking.snapshot,
        ranked_candidates=tuple(
            replace(
                c,
                rank=index + 1,
                eligibility_status="ELIGIBLE" if c.venue_native_id == target else "INELIGIBLE",
            )
            for index, c in enumerate(ordered)
        ),
    ).with_integrity_digest()
    rank_writer = ProductiveRankingSingleWriterV1(
        state_root=chain["ranking_root"], writer_identity="test_rank", session_id="fresh"
    )
    rank_writer.acquire(now_unix=NOW)
    try:
        persist_ranking_bundle_atomic_v1(
            state_root=chain["ranking_root"],
            writer=rank_writer,
            snapshot=ranking,
            evidence={"ok": True, "capability_id": "CAPABILITY_2_2"},
        )
    finally:
        rank_writer.release()
    margin = _obs(value="75", epoch=NEXT)
    capital = execute_current_productive_treasury_single_source_capital_handoff_v1(
        margin_observation=margin,
        instrument_id=bound.instrument_id,
        body_sha256=margin.provenance_digest,
        fresh_pretrade_get_status="TRUSTED_PRESENT",
        live_account_bound_status="TRUSTED_PRESENT",
        u04_p01_host_inputs=build_full_core_margin_inputs_from_budget_owner_v1(
            raw_acct_lv="2", budget_owner=owner
        ),
    )
    request = replace(
        request,
        budget_owner=owner,
        closed_reservation_ids=(rid,),
        expected_budget_observation_id=oid,
        observed_at_utc=NEXT,
        capital_handoff=capital,
        ranking=replace(
            request.ranking,
            snapshot=ranking,
            provenance=replace(
                request.ranking.provenance, ranking_integrity_digest=ranking.integrity_digest
            ),
        ),
    )
    lifecycle = run_full_core_post_submit_lifecycle_reconciliation_join_v1(**close)
    identity = identity_from_full_core_binding_v1(
        close["binding"],
        decision_outcome="EXIT",
        venue_plan_identity=close["venue_plan_identity"],
        envelope_identity=close["envelope_identity"],
        submit_attempt_id=close["submit_attempt_id"],
        local_durable_state_version=close["local_durable_state_version"],
        exchange_ord_id=close["post_submit_join"].venue_order_id,
    )
    observed = PortfolioTruthSnapshotV1(
        source_id="injected-fresh-target-query",
        positions=(),
        event_time_unix=NOW,
        wall_time_unix=NOW,
        max_age_seconds=5,
    )
    context = ProductiveN1PostCloseContinuationV1(
        lifecycle,
        identity,
        request,
        tmp_path / "membership",
        observed,
        5,
    )
    monkeypatch.setattr(market, "PREVIOUS_C1_VENUE_EVENT_TIME", T0 + 60)
    cycle = market._market_kwargs(
        cycle_id_prefix="after-close", last_ts=T0 + 60, venue_native_id=target
    )
    cycle.pop("origin_main_sha")
    cycle.update(
        observed_unix=NOW,
        last_finalized_event_ts_unix=T0 + 60,
        g17_typed_vol_producers={
            "LANE_1": market._memory_g17_producer(
                instrument_id=sources._cid(chain["ranking"], target), venue_native_id=target
            )
        },
        candles_payload_by_lane={
            "LANE_1": {
                **market._mv2_aligned_candles(last_ts_ms=int((T0 + 60) * 1000), mark_px=100.5),
                "instId": target,
            }
        },
        candles_payload=None,
    )
    args = dict(
        membership=membership,
        ranking_snapshot=ranking.to_dict(),
        topology_state_root_base=topology,
        lane_assignment_writer=writer,
        repository_sha=sources.REPO_SHA,
        producer_observed_at_unix=NOW,
        origin_main_sha=market.ORIGIN_SHA,
        target_cardinality=1,
        portfolio_budget_owner=owner,
        post_close_continuation=context,
        cap24_bind=ProductiveFullAutonomyCap24BindContextV1(
            chain["ranking_root"],
            chain["universe_root"],
            chain["recon_root"],
            observed,
            chain["mark_price_by_native_id"],
            "after-close",
            NOW,
        ),
        replacement_admission_by_lane={
            "LANE_1": rotation_decision_for_lane_v1(
                venue_flat=True,
                reconciled=True,
                lane_health_allows_replacement=True,
            )
        },
        **cycle,
    )
    return args, owner, writer, target


@pytest.mark.parametrize("replacement", [False, True])
def test_original_close_reaches_durable_membership_and_actual_next_core(
    tmp_path, monkeypatch, replacement
):
    args, owner, writer, target = _fixture(tmp_path, monkeypatch, replace_instrument=replacement)
    try:
        result = run_productive_full_autonomy_n5_runtime_orchestrator_v1(**args)
        receipt = result.post_close_continuation_receipt
        assert receipt["phase"] == "ACKED"
        assert receipt["consumed"]["LANE_1"]["native_id"] == target
        assert receipt["consumed"]["LANE_1"]["input_digest"]
        assert result.readiness_projections["LANE_1"].n1_consumer_result.s7_invocation is not None
        assert owner.budget_state_v1().canonical_available_capital == 75
        assert not result.post_allowed and not result.external_effect_authorized
        replay = run_productive_full_autonomy_n5_runtime_orchestrator_v1(**args)
        assert isinstance(replay, PostCloseContinuationReplayV1)
        assert replay.receipt == receipt
    finally:
        owner.close()
        writer.release()


def _count_consumption(monkeypatch):
    calls = []
    original = orchestrator.compose_occupied_lane_n1_host_join_readiness_v1

    def counted(*args, **kwargs):
        calls.append(1)
        return original(*args, **kwargs)

    monkeypatch.setattr(orchestrator, "compose_occupied_lane_n1_host_join_readiness_v1", counted)
    return calls


@pytest.mark.parametrize(
    "failure",
    [
        "partial",
        "capital_missing",
        "wrong_account",
        "before_close",
        "foreign_observation",
        "relaxed_capital_age",
        "multiple_lanes",
    ],
)
def test_invalid_close_or_target_keeps_hold_and_does_not_consume(tmp_path, monkeypatch, failure):
    args, owner, writer, _ = _fixture(
        tmp_path, monkeypatch, remaining="0.4" if failure == "partial" else "0"
    )
    calls = _count_consumption(monkeypatch)
    context = args["post_close_continuation"]
    if failure == "capital_missing":
        context = replace(context, request=replace(context.request, capital_handoff=None))
    elif failure == "wrong_account":
        context = replace(
            context, identity=replace(context.identity, account_identity="foreign-account")
        )
    elif failure == "before_close":
        args["observed_unix"] = T0
    elif failure == "foreign_observation":
        args["observed_portfolio"] = replace(
            context.budget_observed, source_id="different-observation"
        )
    elif failure == "relaxed_capital_age":
        context = replace(context, capital_max_age_seconds=1e12)
    elif failure == "multiple_lanes":
        args["target_cardinality"] = 2
    args["post_close_continuation"] = context
    try:
        with pytest.raises(PostCloseContinuationError):
            run_productive_full_autonomy_n5_runtime_orchestrator_v1(**args)
        assert owner.active_sum_v1() == 40
        assert calls == []
        assert not context.membership_store_root.exists()
    finally:
        owner.close()
        writer.release()


@pytest.mark.parametrize("boundary", ["membership_write", "after_publication"])
def test_retry_before_core_reuses_original_writers_without_double_consumption(
    tmp_path, monkeypatch, boundary
):
    args, owner, writer, _ = _fixture(tmp_path, monkeypatch, replace_instrument=True)
    calls = _count_consumption(monkeypatch)
    name = (
        "persist_selector_result_v1"
        if boundary == "membership_write"
        else "admit_post_close_target_v1"
    )
    original = getattr(continuation, name)
    first = True

    def interrupted(*a, **kw):
        nonlocal first
        if first:
            first = False
            if boundary == "membership_write":
                original(*a, **kw)
            raise OSError("injected interruption before Core")
        return original(*a, **kw)

    monkeypatch.setattr(continuation, name, interrupted)
    try:
        with pytest.raises(OSError):
            run_productive_full_autonomy_n5_runtime_orchestrator_v1(**args)
        assert calls == []
        assert owner.active_sum_v1() == 0
        result = run_productive_full_autonomy_n5_runtime_orchestrator_v1(**args)
        assert result.post_close_continuation_receipt["phase"] == "ACKED"
        assert calls == [1]
        if boundary == "after_publication":
            assert result.lane_publication_resumed
    finally:
        owner.close()
        writer.release()


@pytest.mark.parametrize("ack_written", [False, True])
def test_lost_core_ack_is_recovered_without_reinvoking_core(tmp_path, monkeypatch, ack_written):
    args, owner, writer, _ = _fixture(tmp_path, monkeypatch)
    calls = _count_consumption(monkeypatch)
    original = continuation.acknowledge_post_close_consumer_v1

    def interrupted(*a, **kw):
        if ack_written:
            original(*a, **kw)
        raise OSError("injected ACK boundary interruption")

    monkeypatch.setattr(continuation, "acknowledge_post_close_consumer_v1", interrupted)
    try:
        with pytest.raises(OSError):
            run_productive_full_autonomy_n5_runtime_orchestrator_v1(**args)
        assert calls == [1]
        replay = run_productive_full_autonomy_n5_runtime_orchestrator_v1(**args)
        assert isinstance(replay, PostCloseContinuationReplayV1)
        assert replay.receipt["phase"] == "ACKED"
        assert replay.receipt["consumed"]["LANE_1"]["native_id"] == "ETH-USDT-SWAP"
        assert calls == [1]
    finally:
        owner.close()
        writer.release()


def test_completed_retry_preserves_a_later_reservation(tmp_path, monkeypatch):
    args, owner, writer, _ = _fixture(tmp_path, monkeypatch)
    calls = _count_consumption(monkeypatch)
    try:
        run_productive_full_autonomy_n5_runtime_orchestrator_v1(**args)
        later = owner.try_reserve_v1(
            slot_id="LANE_1",
            decision_id="later-decision",
            cycle_id="later-cycle",
            observation_id=owner.budget_state_v1().observation_id,
            amount=Decimal("10"),
        )
        assert later.reservation is not None
        before = owner.budget_state_v1()
        assert isinstance(
            run_productive_full_autonomy_n5_runtime_orchestrator_v1(**args),
            PostCloseContinuationReplayV1,
        )
        assert owner.budget_state_v1() == before
        assert owner.active_sum_v1() == 10 and calls == [1]
    finally:
        owner.close()
        writer.release()


def test_completed_retry_after_owner_teardown_does_not_readmit_account(tmp_path, monkeypatch):
    args, owner, writer, _ = _fixture(tmp_path, monkeypatch)
    result = run_productive_full_autonomy_n5_runtime_orchestrator_v1(**args)
    owner.close()
    writer.release()
    context = args["post_close_continuation"]
    restored = PortfolioCapitalReservationBudgetOwnerV1(
        durable_root=tmp_path / "budget",
        durable_account_identity="acct-1",
        durable_mode="recover",
        durable_lane_bindings={"LANE_1": context.request.bound_instrument},
    )
    new_writer = sources._held_writer(args["topology_state_root_base"])
    args.update(
        portfolio_budget_owner=restored,
        lane_assignment_writer=new_writer,
        post_close_continuation=replace(
            context, request=replace(context.request, budget_owner=restored)
        ),
    )
    try:
        replay = run_productive_full_autonomy_n5_runtime_orchestrator_v1(**args)
        assert replay.receipt == result.post_close_continuation_receipt
        assert not restored.budget_state_v1().admitted
    finally:
        restored.close()
        new_writer.release()


@pytest.mark.parametrize("tamper", ["digest", "resealed_missing_consumer", "new_cycle"])
def test_receipt_conflict_or_corruption_cannot_restart_core(tmp_path, monkeypatch, tamper):
    args, owner, writer, _ = _fixture(tmp_path, monkeypatch)
    calls = _count_consumption(monkeypatch)
    try:
        run_productive_full_autonomy_n5_runtime_orchestrator_v1(**args)
        path = next(writer.state_root.glob("post_close/*.json"))
        if tamper == "new_cycle":
            args["cycle_id_prefix"] = "another-cycle-for-same-close"
        else:
            record = json.loads(path.read_text())
            if tamper == "digest":
                record["content_digest"] = "0" * 64
                path.write_text(json.dumps(record))
            else:
                record.pop("consumed")
                continuation._write_receipt(path, record)
        with pytest.raises(PostCloseContinuationError):
            run_productive_full_autonomy_n5_runtime_orchestrator_v1(**args)
        assert calls == [1]
    finally:
        owner.close()
        writer.release()


def test_young_replacement_respects_original_minimum_holding(tmp_path, monkeypatch):
    args, owner, writer, _ = _fixture(
        tmp_path, monkeypatch, replace_instrument=True, selection_age=0
    )
    calls = _count_consumption(monkeypatch)
    try:
        with pytest.raises(ValueError, match="WITHIN_MIN_HOLDING_PERIOD"):
            run_productive_full_autonomy_n5_runtime_orchestrator_v1(**args)
        assert calls == []
    finally:
        owner.close()
        writer.release()


def test_expired_keep_requires_fresh_review_then_reaches_original_cap24_and_core(
    tmp_path, monkeypatch
):
    from src.ops.current_mf_n5_boundary_occupied_lane_cap24_n1_bind_join_v1 import bind_join_v1
    from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.topology_v1 import (
        lane_state_root_for,
    )
    from src.ops.single_selected_future_policy_v1.persistence_v1 import (
        load_and_validate_selection_v1,
    )

    args, owner, writer, _ = _fixture(tmp_path, monkeypatch, selection_age=3600)
    calls = _count_consumption(monkeypatch)
    try:
        lane_root = lane_state_root_for(
            topology_state_root_base=args["topology_state_root_base"], lane_id="LANE_1"
        )
        old = load_and_validate_selection_v1(lane_root).selection
        context = args["cap24_bind"]
        expired = bind_join_v1.run_single_selected_future_runtime_binding_gate_v1(
            selection_state_root=lane_root,
            ranking_state_root=context.ranking_state_root,
            universe_state_root=context.universe_state_root,
            repository_sha=args["repository_sha"],
            session_id="unreviewed-old-keep",
            now_unix=NOW,
            reconciliation_state_root=context.reconciliation_state_root,
            observed_portfolio=context.observed_portfolio,
            mark_price_by_native_id=context.mark_price_by_native_id,
        )
        assert not expired.ok and "SELECTION_EXPIRED" in expired.blockers
        assert calls == []

        result = run_productive_full_autonomy_n5_runtime_orchestrator_v1(**args)
        renewed = load_and_validate_selection_v1(lane_root).selection
        assert renewed.instrument_id == old.instrument_id
        assert renewed.selected_at_event_time == old.selected_at_event_time
        assert renewed.valid_from == old.valid_from
        assert datetime.fromisoformat(renewed.valid_until.replace("Z", "+00:00")).timestamp() > NOW
        assert renewed.ranking_integrity_digest == args["ranking_snapshot"]["integrity_digest"]
        receipt = result.post_close_continuation_receipt
        assert receipt["phase"] == "ACKED"
        assert receipt["consumed"]["LANE_1"]["native_id"] == "ETH-USDT-SWAP"
        assert result.readiness_projections["LANE_1"].n1_consumer_result.s7_invocation is not None
        assert owner.budget_state_v1().canonical_available_capital == 75
        assert not result.post_allowed and not result.external_effect_authorized
        replay = run_productive_full_autonomy_n5_runtime_orchestrator_v1(**args)
        assert isinstance(replay, PostCloseContinuationReplayV1)
        assert replay.receipt == receipt
        assert load_and_validate_selection_v1(lane_root).selection == renewed
        assert calls == [1]
    finally:
        owner.close()
        writer.release()


@pytest.mark.parametrize("corrupt", [False, True])
def test_completed_publication_requires_its_original_receipt(tmp_path, monkeypatch, corrupt):
    args, owner, writer, _ = _fixture(tmp_path, monkeypatch, replace_instrument=True)
    calls = _count_consumption(monkeypatch)
    original = continuation.admit_post_close_target_v1

    def interrupted(*a, **kw):
        raise OSError("after original publication")

    monkeypatch.setattr(continuation, "admit_post_close_target_v1", interrupted)
    try:
        with pytest.raises(OSError):
            run_productive_full_autonomy_n5_runtime_orchestrator_v1(**args)
        receipt = writer.state_root / "selection_publication_completed_v1.json"
        if corrupt:
            data = json.loads(receipt.read_text())
            data["receipt_digest"] = "0" * 64
            receipt.write_text(json.dumps(data))
        else:
            receipt.unlink()
        monkeypatch.setattr(continuation, "admit_post_close_target_v1", original)
        with pytest.raises(ValueError):
            run_productive_full_autonomy_n5_runtime_orchestrator_v1(**args)
        assert calls == []
    finally:
        owner.close()
        writer.release()
