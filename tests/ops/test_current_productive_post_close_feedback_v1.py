"""Injected closing execution → reconciliation → canonical capital/membership.

No network, no durable reservation reconstruction or productive activation.
"""

from dataclasses import replace
from decimal import Decimal
from hashlib import sha256
import json
from urllib.parse import urlencode

import pytest

from src.ops.execution_reconciliation_proof_store_v1 import _decode_get, _RecordedReconciliationGets
from src.ops.full_core_live_path_composition_root_v1.current_productive_post_close_feedback_v1 import (
    PostCloseFeedbackRequestV1,
    PostCloseRankingReviewRequestV1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_position_management_quantity_handoff_v1 import (
    PositionManagementExecutionHandoffV1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_treasury_single_source_capital_handoff_v1 import (
    execute_current_productive_treasury_single_source_capital_handoff_v1,
    build_full_core_margin_inputs_from_budget_owner_v1,
)
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    ENDPOINT_ACCOUNT_POSITIONS,
    TRANSPORT_CLASS_INJECTED_TEST_DOUBLE,
    FreshPretradeGetTransportResultV1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_offline_provider_v1 import (
    OfflineExchangeFixtureV1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_okx_read_only_provider_v1 import (
    ENDPOINT_ORDERS_HISTORY,
    ENDPOINT_ORDERS_PENDING,
    ENDPOINT_TRADE_FILLS,
    OkxReadOnlyReconciliationQueryOptionsV1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_v1 import (
    OUTCOME_CONFIRMED_FILLED,
    OUTCOME_HALTED_UNRESOLVED,
    REASON_API_ERROR,
    REASON_INCOMPLETE_PAGINATION,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_post_submit_exchange_reconciliation_lifecycle_join_v1 import (
    run_full_core_post_submit_lifecycle_reconciliation_join_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_post_response_to_ack_mapper_v1 import (
    join_full_core_post_result_to_lifecycle_v1,
)
from src.ops.full_core_live_path_composition_root_v1.productive_read_only_get_transport_v1 import (
    READ_ONLY_EXACT_ORDER_LOOKUP_PATH,
)
from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
    PortfolioCapitalReservationBudgetOwnerV1,
)
from src.ops.productive_futures_ranking_producer_v1.models_v1 import (
    ProductiveFuturesRankingSnapshotV1,
)
from tests.ops import test_current_productive_full_close_execution_handoff_v1 as execution_cases
from tests.ops import (
    test_current_productive_position_management_quantity_handoff_v1 as quantity_cases,
)
from tests.ops.test_current_mf_n5_isolated_lane_instance_topology_v1 import (
    _five_ranking,
    _cid,
    _membership,
)
from tests.ops.test_portfolio_capital_reservation_budget_contract_v1 import _bind, _obs
from tests.ops.test_full_core_exchange_reconciliation_v1 import _binding

NOW = "2026-11-03T00:00:03Z"
FILL_MS = "1793664001000"
POSITION_MS = "1793664002000"
PAGED_CLOSE_READ_ID = "offline-close-page-replay"


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


def _case(
    monkeypatch,
    *,
    state="filled",
    remaining="0",
    replace_member=False,
    initial_ranking=None,
    bound_instrument=None,
    prior_membership=None,
    lane_id="LANE_1",
    order_id="offline-close-order",
):
    initial = _five_ranking() if initial_ranking is None else initial_ranking
    old = _cid(
        initial,
        bound_instrument.venue_native_id if bound_instrument is not None else "ETH-USDT-SWAP",
    )
    # Keep one explicit universe; refreshing ranking does not merge universes.
    bound = bound_instrument or replace(
        execution_cases._bound(),
        instrument_id=old,
        venue_native_id="ETH-USDT-SWAP",
        universe_snapshot_id=initial["universe_snapshot_id"],
    )
    monkeypatch.setattr(quantity_cases, "_bound", lambda: bound)
    monkeypatch.setattr(execution_cases, "_bound", lambda: bound)
    args, source = execution_cases._prepared(lane_id=lane_id)
    status, reasons, plan = execution_cases._bind(args, source)
    assert status.value == "PASS", reasons
    envelope = execution_cases._envelope(plan, source)
    submit = execution_cases._ack_fixture(envelope)
    submit.payload["data"][0]["ordId"] = order_id
    ack = join_full_core_post_result_to_lifecycle_v1(
        result=submit,
        sent_clordid=envelope.client_order_id,
        submit_count=1,
    )
    binding = replace(
        _binding(),
        account_scope="acct-1",
        instrument_id=envelope.instrument_id,
        native_id=envelope.instrument_id,
        selected_direction="EXIT",
        order_side=envelope.side,
        final_quantity=envelope.quantity,
        order_type="market",
        order_price="",
        clordid=envelope.client_order_id,
        canonical_decision_id=source.canonical_intent.decision_id,
        envelope_digest=envelope.envelope_digest,
    )
    owner = PortfolioCapitalReservationBudgetOwnerV1()
    observed = _bind(owner, epoch="2026-11-03T00:00:00Z")
    reserved = owner.try_reserve_v1(
        slot_id=lane_id,
        decision_id="original-entry",
        cycle_id="entry-cycle",
        observation_id=observed,
        amount=Decimal("40"),
    )
    reservation_id = str(reserved.reservation.reservation_id)
    owner.commit_internal_pre_external_effect_v1(reservation_id)
    margin = _obs(value="75", epoch=NOW)
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
    assert not capital.fail_closed, capital.reason_codes
    prior = prior_membership or _membership(initial, [old])
    snapshot = ProductiveFuturesRankingSnapshotV1.from_dict(initial)
    candidates = tuple(
        replace(c, eligibility_status="INELIGIBLE")
        if replace_member and c.canonical_instrument_id == old
        else c
        for c in snapshot.ranked_candidates
    )
    ranking = replace(
        snapshot,
        event_time="2026-11-03T00:00:02Z",
        ranking_snapshot_id="post-close-ranking",
        ranked_candidates=candidates,
    ).with_integrity_digest()
    provenance = replace(
        prior.cap22_provenance,
        ranking_snapshot_id=ranking.ranking_snapshot_id,
        ranking_integrity_digest=ranking.integrity_digest,
        ranking_event_time=ranking.event_time,
    )
    request = PostCloseFeedbackRequestV1(
        execution=PositionManagementExecutionHandoffV1(source, envelope),
        bound_instrument=bound,
        observed_at_utc=NOW,
        capital_handoff=capital,
        budget_owner=owner,
        closed_reservation_ids=(reservation_id,),
        expected_budget_observation_id=observed,
        ranking=PostCloseRankingReviewRequestV1(ranking, provenance, prior, (prior,)),
    )
    order = {
        "instId": envelope.instrument_id,
        "clOrdId": envelope.client_order_id,
        "ordId": order_id,
        "state": state,
        "sz": "1.2",
        "accFillSz": str(Decimal("1.2") - Decimal(remaining)),
        "uTime": FILL_MS,
        "sCode": "0",
    }
    positions = {
        "code": "0",
        "data": [
            {
                "instId": envelope.instrument_id,
                "pos": remaining,
                "posSide": "long",
                "uTime": POSITION_MS,
            }
        ],
    }
    fixture = OfflineExchangeFixtureV1(
        pending_orders={"code": "0", "data": []},
        order_history={"code": "0", "data": [order]},
        positions=positions,
    )
    kwargs = dict(
        post_submit_join=ack,
        binding=binding,
        decision_outcome="EXIT",
        venue_plan_identity=plan.clordid,
        envelope_identity=envelope.envelope_digest,
        submit_attempt_id="close-attempt",
        local_durable_state_version="v1",
        offline_fixture=fixture,
        post_close_feedback_request=request,
    )
    return kwargs, owner, reservation_id, old


def _okx_close_page_receipts(fixture, *, pending_full):
    """Synthetic original GETs, retaining the request and exact body for each page."""
    (close_order,) = fixture.order_history["data"]
    inst = close_order["instId"]
    scope = {"instType": "SWAP", "instId": inst}
    older_order = {"instId": inst, "clOrdId": "older-order", "ordId": "80", "state": "canceled"}
    close_fill = {
        "instId": inst,
        "clOrdId": close_order["clOrdId"],
        "ordId": close_order["ordId"],
        "billId": "92",
        "tradeId": "42",
        "fillSz": close_order["accFillSz"],
        "fillPx": "2200",
        "fillTime": FILL_MS,
    }
    older_fill = {"instId": inst, "clOrdId": "older-order", "ordId": "80", "billId": "91"}
    history = {**scope, "limit": "2"}
    pending_rows = (
        [{**older_order, "ordId": str(i), "state": "live"} for i in range(199, 99, -1)]
        if pending_full
        else []
    )
    pages = [(ENDPOINT_ORDERS_PENDING, scope, pending_rows)]
    if pending_full:
        pages.append((ENDPOINT_ORDERS_PENDING, {**scope, "after": "100"}, []))
    pages.extend(
        [
            (ENDPOINT_ORDERS_HISTORY, history, [close_order, older_order]),
            (ENDPOINT_ORDERS_HISTORY, {**history, "after": "80"}, [{**older_order, "ordId": "79"}]),
            (ENDPOINT_TRADE_FILLS, history, [close_fill, older_fill]),
            (ENDPOINT_TRADE_FILLS, {**history, "after": "91"}, [{**older_fill, "billId": "90"}]),
            (ENDPOINT_ACCOUNT_POSITIONS, {"instId": inst}, fixture.positions["data"]),
            (
                READ_ONLY_EXACT_ORDER_LOOKUP_PATH,
                {"instId": inst, "clOrdId": close_order["clOrdId"]},
                [close_order],
            ),
        ]
    )
    receipts = []
    for index, (path, query, rows) in enumerate(pages):
        body = json.dumps({"code": "0", "data": rows}) + "\n"
        receipts.append(
            {
                "endpoint": f"{path}?{urlencode(query)}",
                "decision_id": PAGED_CLOSE_READ_ID,
                "acquired_at": f"2026-11-03T00:00:02.{index:03d}+00:00",
                "body": body,
                "body_sha256": sha256(body.encode()).hexdigest(),
            }
        )
    return receipts


@pytest.mark.parametrize(
    ("missing_path", "page_budget"),
    [
        pytest.param(None, 2, id="complete"),
        pytest.param(ENDPOINT_ORDERS_PENDING, 2, id="missing-pending-page"),
        pytest.param(ENDPOINT_ORDERS_HISTORY, 2, id="missing-history-page"),
        pytest.param(ENDPOINT_TRADE_FILLS, 2, id="missing-fills-page"),
        pytest.param(None, 1, id="exhausted-page-budget"),
    ],
)
def test_okx_close_page_replay_requires_complete_coverage(monkeypatch, missing_path, page_budget):
    kwargs, owner, _, _ = _case(monkeypatch, order_id="81")
    fixture = kwargs.pop("offline_fixture")
    receipts = _okx_close_page_receipts(
        fixture, pending_full=missing_path == ENDPOINT_ORDERS_PENDING
    )
    missing_endpoint = next(
        (
            record["endpoint"]
            for record in receipts
            if record["endpoint"].split("?", 1)[0] == missing_path
            and "&after=" in record["endpoint"]
        ),
        None,
    )
    recorded = (
        _decode_get(record)
        for record in receipts
        if record["endpoint"] != missing_endpoint
        and (page_budget > 1 or "&after=" not in record["endpoint"])
    )
    replay = _RecordedReconciliationGets(recorded)
    replay_get = replay.get
    requested_missing = []

    def get(**request):
        if request["endpoint"] != missing_endpoint:
            return replay_get(**request)
        requested_missing.append(request["endpoint"])
        return FreshPretradeGetTransportResultV1(
            get_performed=False,
            method="GET",
            endpoint=request["endpoint"],
            http_status=0,
            payload=None,
            auth_header_sent=False,
            transport_class=TRANSPORT_CLASS_INJECTED_TEST_DOUBLE,
            venue_live_contact=False,
            historical_reuse=False,
            error_class="TIMEOUT",
        )

    monkeypatch.setattr(replay, "get", get)
    before = owner.budget_state_v1()
    active_before = owner.active_sum_v1()
    joined = run_full_core_post_submit_lifecycle_reconciliation_join_v1(
        **kwargs,
        read_only_get_transport=replay,
        pretrade_decision_id=PAGED_CLOSE_READ_ID,
        query_options=OkxReadOnlyReconciliationQueryOptionsV1(
            history_limit=2,
            fills_limit=2,
            offline_max_pages_per_surface=page_budget,
        ),
    )
    assert next(recorded, None) is None
    assert requested_missing == ([missing_endpoint] if missing_path else [])
    assert (joined.ghv_forward_join, joined.ghv_reverse_join) == ("PASS", "PASS")
    decision = joined.reconciliation.decision
    snapshot = joined.reconciliation.snapshot
    feedback = joined.post_close_feedback
    assert any(
        item["source"] == "fills" and item["payload"]["fillSz"] == kwargs["binding"].final_quantity
        for item in snapshot["evidence_items"]
    )
    assert snapshot["positions_observation"]["response"]["data"][0]["pos"] == "0"
    coverage_incomplete = missing_path is not None or page_budget == 1
    assert snapshot["incomplete_pagination"] is coverage_incomplete
    if not coverage_incomplete:
        assert decision.outcome == OUTCOME_CONFIRMED_FILLED
        assert feedback.status == "RECONCILED_FLAT_REVIEWED"
        assert feedback.capital_refresh.disposition.value == "ADMITTED"
        assert owner.active_sum_v1() == 0
    else:
        assert decision.outcome == OUTCOME_HALTED_UNRESOLVED
        assert decision.reasons == (
            (REASON_API_ERROR if missing_path else REASON_INCOMPLETE_PAGINATION),
        )
        assert decision.reconciliation_complete is False
        assert decision.exposure_retained is True
        assert feedback.status == "BLOCKED"
        assert feedback.reason_codes == ("POST_CLOSE_RECONCILIATION_UNRESOLVED",)
        assert feedback.position is None and feedback.remaining_quantity is None
        assert feedback.capital_refresh is None and feedback.double_play_continuation is None
        assert feedback.membership_review is None and not feedback.ranking_review_allowed
        assert owner.budget_state_v1() == before and owner.active_sum_v1() == active_before
        assert joined.post_submit_join.resubmit_allowed is False


@pytest.mark.parametrize("replacement", [False, True])
def test_full_close_refreshes_only_canonical_capital_and_invokes_existing_ranking_owner(
    monkeypatch, replacement
):
    kwargs, owner, _, old = _case(monkeypatch, replace_member=replacement)
    result = run_full_core_post_submit_lifecycle_reconciliation_join_v1(**kwargs)
    feedback = result.post_close_feedback
    assert feedback.status == "RECONCILED_FLAT_REVIEWED", feedback.reason_codes
    assert feedback.position.venue_flat and feedback.remaining_quantity == 0
    assert feedback.capital_refresh.disposition.value == "ADMITTED", feedback.reason_codes
    assert owner.budget_state_v1().canonical_available_capital == Decimal("75")
    assert owner.active_sum_v1() == 0
    assert (old in feedback.membership_review.ordered_membership) is (not replacement)
    assert feedback.membership_review.persisted_artifact is None
    assert result.post_submit_join.resubmit_allowed is False
    assert feedback.execution_authority_effect == "NONE"
    again = run_full_core_post_submit_lifecycle_reconciliation_join_v1(**kwargs)
    assert again.post_close_feedback.capital_refresh.disposition.value == "IDEMPOTENT_REPLAY"
    assert owner.budget_state_v1().canonical_available_capital == Decimal("75")
    assert result.to_dict()["post_close_feedback"]["remaining_quantity"] == "0"


def test_partial_close_transports_real_rest_without_freeing_capital_or_ranking(monkeypatch):
    kwargs, owner, _, _ = _case(monkeypatch, state="partially_filled", remaining="0.4")
    before = owner.budget_state_v1()
    feedback = run_full_core_post_submit_lifecycle_reconciliation_join_v1(
        **kwargs
    ).post_close_feedback
    assert feedback.status == "POSITION_REMAINS_OPEN"
    assert feedback.remaining_quantity == Decimal("0.4")
    assert not feedback.ranking_review_allowed and feedback.membership_review is None
    assert feedback.capital_refresh is None and owner.budget_state_v1() == before


@pytest.mark.parametrize(
    "problem",
    [
        "missing_position",
        "old_position",
        "unknown_order",
        "pending_order",
        "foreign_account",
        "stale_capital",
        "foreign_reservation",
        "unlisted_reservation",
        "stale_ranking",
        "missing_pending",
        "wrong_generation",
        "wrong_envelope",
        "wrong_fill_quantity",
        "stale_snapshot",
        "duplicate_position",
        "zero_not_filled",
        "future_position",
        "position_response_error",
        "position_flip",
        "foreign_ranking_provenance",
        "orphan_membership",
    ],
)
def test_unproven_feedback_never_frees_capital_or_commits_membership(monkeypatch, problem):
    kwargs, owner, _, _ = _case(monkeypatch)
    request = kwargs["post_close_feedback_request"]
    fixture = kwargs["offline_fixture"]
    if problem == "missing_position":
        kwargs["offline_fixture"] = replace(fixture, positions={"code": "0", "data": []})
    elif problem == "old_position":
        fixture.positions["data"][0]["uTime"] = "1793663999000"
    elif problem == "unknown_order":
        kwargs["offline_fixture"] = replace(fixture, order_history={"code": "0", "data": []})
    elif problem == "pending_order":
        fixture.pending_orders["data"].append(
            {
                "instId": request.execution.envelope.instrument_id,
                "clOrdId": "other-live-order",
                "state": "live",
            }
        )
    elif problem == "missing_pending":
        kwargs["offline_fixture"] = replace(fixture, pending_orders=None)
    elif problem == "wrong_generation":
        kwargs["post_close_feedback_request"] = replace(
            request,
            bound_instrument=replace(request.bound_instrument, selection_id="different-selection"),
        )
    elif problem == "wrong_envelope":
        kwargs["post_close_feedback_request"] = replace(
            request,
            execution=replace(
                request.execution, envelope=replace(request.execution.envelope, quantity="9")
            ),
        )
    elif problem == "wrong_fill_quantity":
        fixture.order_history["data"][0].update(sz="0.5", accFillSz="0.5")
    elif problem == "stale_snapshot":
        kwargs["offline_fixture"] = replace(fixture, snapshot_freshness_proven=False)
    elif problem == "duplicate_position":
        fixture.positions["data"] *= 2
    elif problem == "zero_not_filled":
        fixture.order_history["data"][0].update(state="live", accFillSz="0")
    elif problem == "future_position":
        fixture.positions["data"][0]["uTime"] = "1793664999000"
    elif problem == "position_response_error":
        fixture.positions["code"] = "50011"
    elif problem == "position_flip":
        fixture.positions["data"][0].update(pos="0.4", posSide="short")
    elif problem in {"foreign_ranking_provenance", "orphan_membership"}:
        if problem == "foreign_ranking_provenance":
            review = replace(
                request.ranking,
                provenance=replace(
                    request.ranking.provenance, universe_snapshot_id="other-universe"
                ),
            )
        else:
            review = replace(
                request.ranking, prior=replace(request.ranking.prior, ordered_instrument_ids=())
            )
        kwargs["post_close_feedback_request"] = replace(
            request, ranking=review, capital_handoff=None
        )
    elif problem in {"foreign_account", "stale_capital"}:
        output = replace(
            request.capital_handoff.producer_output,
            **(
                {"bound_account_identity": "other-account"}
                if problem == "foreign_account"
                else {"observed_at_as_of": "2026-11-03T00:00:00Z"}
            ),
        )
        kwargs["post_close_feedback_request"] = replace(
            request, capital_handoff=replace(request.capital_handoff, producer_output=output)
        )
    elif problem in {"foreign_reservation", "unlisted_reservation"}:
        extra = owner.try_reserve_v1(
            slot_id="OTHER_LANE" if problem == "foreign_reservation" else "LANE_1",
            decision_id="new-decision",
            cycle_id="new-cycle",
            observation_id=request.expected_budget_observation_id,
            amount=Decimal("10"),
        )
        owner.commit_internal_pre_external_effect_v1(str(extra.reservation.reservation_id))
    else:
        ranking = replace(
            request.ranking.snapshot, event_time="1793663999000"
        ).with_integrity_digest()
        kwargs["post_close_feedback_request"] = replace(
            request, ranking=replace(request.ranking, snapshot=ranking)
        )
        # Ranking failure and capital refresh are independent; don't supply capital.
        kwargs["post_close_feedback_request"] = replace(
            kwargs["post_close_feedback_request"], capital_handoff=None
        )
    before = owner.budget_state_v1()
    feedback = run_full_core_post_submit_lifecycle_reconciliation_join_v1(
        **kwargs
    ).post_close_feedback
    assert feedback.capital_refresh is None or feedback.capital_refresh.mutated is False
    assert owner.budget_state_v1() == before
    assert (
        feedback.membership_review is None or feedback.membership_review.persisted_artifact is None
    )


def test_flat_review_can_run_without_new_capital_and_leaves_budget_unchanged(monkeypatch):
    kwargs, owner, _, old = _case(monkeypatch)
    kwargs["post_close_feedback_request"] = replace(
        kwargs["post_close_feedback_request"], capital_handoff=None
    )
    before = owner.budget_state_v1()
    feedback = run_full_core_post_submit_lifecycle_reconciliation_join_v1(
        **kwargs
    ).post_close_feedback
    assert old in feedback.membership_review.ordered_membership
    assert "POST_CLOSE_FRESH_CAPITAL_HANDOFF_REQUIRED" in feedback.reason_codes
    assert feedback.capital_refresh is None and owner.budget_state_v1() == before


def test_orchestrated_lifecycle_calls_feedback_and_replay_retains_new_reservation(monkeypatch):
    from tests.ops.test_full_core_orchestrated_post_submit_lifecycle_reconciliation_v1 import (
        _orchestration_request,
    )
    from src.ops.full_core_live_path_composition_root_v1.full_core_orchestrated_post_submit_lifecycle_reconciliation_v1 import (
        orchestrate_post_submit_lifecycle_reconciliation_v1,
    )

    kwargs, owner, _, _ = _case(monkeypatch)
    request = _orchestration_request(
        **{k: v for k, v in kwargs.items() if k not in {"binding", "post_submit_join"}}
    )
    result = orchestrate_post_submit_lifecycle_reconciliation_v1(
        binding=kwargs["binding"], post_submit_join=kwargs["post_submit_join"], request=request
    )
    assert result.post_close_feedback.capital_refresh.mutated
    state = owner.budget_state_v1()
    new = owner.try_reserve_v1(
        slot_id="LANE_1",
        decision_id="next-entry",
        cycle_id="next-cycle",
        observation_id=state.observation_id,
        amount=Decimal("25"),
    )
    owner.commit_internal_pre_external_effect_v1(str(new.reservation.reservation_id))
    replay = orchestrate_post_submit_lifecycle_reconciliation_v1(
        binding=kwargs["binding"], post_submit_join=kwargs["post_submit_join"], request=request
    )
    assert not replay.post_close_feedback.capital_refresh.mutated
    assert owner.active_sum_v1() == Decimal("25")


def test_process_restart_does_not_reconstruct_budget_or_release_reservations(monkeypatch):
    kwargs, owner, _, _ = _case(monkeypatch)
    owner.restart_fail_closed_v1()
    feedback = run_full_core_post_submit_lifecycle_reconciliation_join_v1(
        **kwargs
    ).post_close_feedback
    assert feedback.capital_refresh.disposition.value == "FAIL_CLOSED"
    assert not owner.budget_state_v1().admitted


def test_productive_read_only_orchestration_cannot_apply_feedback(monkeypatch):
    from tests.ops.test_full_core_orchestrated_post_submit_lifecycle_reconciliation_v1 import (
        _orchestration_request,
    )
    from src.ops.full_core_live_path_composition_root_v1.full_core_orchestrated_post_submit_lifecycle_reconciliation_v1 import (
        orchestrate_post_submit_lifecycle_reconciliation_v1,
        FullCoreOrchestratedLifecycleReconciliationError,
        LifecycleReconciliationOrchestrationMode,
    )

    kwargs, owner, _, _ = _case(monkeypatch)
    before = owner.budget_state_v1()
    request = _orchestration_request(
        mode=LifecycleReconciliationOrchestrationMode.PRODUCTIVE_OKX_SCOPED_READ_ONLY,
        post_close_feedback_request=kwargs["post_close_feedback_request"],
    )
    with pytest.raises(
        FullCoreOrchestratedLifecycleReconciliationError, match="FEEDBACK_MUTATION_FORBIDDEN"
    ):
        orchestrate_post_submit_lifecycle_reconciliation_v1(
            binding=kwargs["binding"], post_submit_join=kwargs["post_submit_join"], request=request
        )
    assert owner.budget_state_v1() == before


def test_flat_label_alone_cannot_release_a_reservation(monkeypatch):
    from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import ReleaseReasonV1

    _, owner, reservation_id, _ = _case(monkeypatch)
    before = owner.budget_state_v1()
    result = owner.release_v1(reservation_id, reason=ReleaseReasonV1.RECONCILED_POSITION_FLAT)
    assert not result.mutated and result.disposition.value == "FAIL_CLOSED"
    assert owner.budget_state_v1() == before


def test_entry_reservation_reference_is_carried_into_existing_cycle_ledger(tmp_path):
    import json
    from tests.ops.test_full_core_current_productive_governed_cycle_orchestrator_v1 import (
        _run,
        _t2_enter,
    )

    def entry(**kwargs):
        result = _t2_enter(**kwargs)
        result.portfolio_reservation_id = "offline-entry-reservation-reference"
        return result

    result = _run(tmp_path, t2_cycle_dispatch=entry)
    assert result.extra["PORTFOLIO_RESERVATION_ID"] == "offline-entry-reservation-reference"
    ledger = next(tmp_path.rglob("governed_cycle_orchestrator_ledger_v1.json"))
    assert (
        json.loads(ledger.read_text())["portfolio_reservation_id"]
        == "offline-entry-reservation-reference"
    )
