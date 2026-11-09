"""Original close review, checked publication, Cap24 and one simulated host."""

from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
import hashlib
import json

import pytest

from src.ops.current_mf_n5_full_autonomy_productive_runtime_orchestrator_v1 import (
    ProductiveFullAutonomyCap24BindContextV1,
)
from src.ops.current_mf_n5_full_autonomy_productive_runtime_orchestrator_v1 import (
    bounded_slot_post_close_v1 as transition,
)
from src.ops.current_mf_n5_ranking_domain_occupied_lane_cap23_n1_produce_join_v1.checked_publication_v1 import (
    publish_checked_lane_selections_v1,
)
from src.ops.current_mf_n5_boundary_occupied_lane_cap24_n1_bind_join_v1.bind_join_v1 import (
    bind_occupied_lane_cap24_n1_instruments_v1,
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
from src.ops.productive_futures_ranking_producer_v1.persistence_v1 import (
    persist_ranking_bundle_atomic_v1,
)
from src.ops.productive_futures_ranking_producer_v1.single_writer_v1 import (
    ProductiveRankingSingleWriterV1,
)
from src.ops.portfolio_capital_reservation_budget_v1.host_v1 import PortfolioBudgetHostV1
from src.ops.productive_reconciliation_runtime_binding_v1.models_v1 import (
    PortfolioTruthSnapshotV1,
    ProductiveReconciliationEvidenceV1,
)
from src.ops.productive_reconciliation_runtime_binding_v1.models_v1 import PositionTruthV1
from src.ops.productive_reconciliation_runtime_binding_v1.classifier_v1 import (
    classify_productive_reconciliation_v1,
)
from src.ops.productive_reconciliation_runtime_binding_v1.persistence_v1 import (
    persist_reconciliation_bundle_atomic,
)
from src.ops.productive_reconciliation_runtime_binding_v1.single_writer_v1 import (
    ProductivePortfolioSingleWriterV1,
)
from src.ops.current_mf_n5_full_autonomy_occupied_lane_bound_ingest_join_v1.ingest_join_v1 import (
    admit_occupied_lane_bound_instruments_v1,
)
from src.ops.current_mf_n5_full_autonomy_occupied_lane_mv2_dp_handoff_join_v1.handoff_join_v1 import (
    compose_occupied_lane_mv2_dp_handoff_v1,
)
from tests.ops import test_current_mf_n5_boundary_occupied_lane_cap24_n1_bind_join_v1 as sources
from tests.ops.test_current_productive_post_close_feedback_v1 import _case
from tests.ops.test_portfolio_capital_reservation_budget_contract_v1 import _produce, _obs
from tests.ops.test_portfolio_budget_host_v1 import _fetch
from tests.ops.test_bounded_multislot_entry_budget_v1 import policy
from src.ops.portfolio_capital_reservation_budget_v1.test_phase_limits_v1 import (
    BoundedSlotReconciliationScopeV1,
)
from tests.ops.test_n1_original_reservation_host_handoff_v1 import (
    synthetic_ports_and_isolation as synthetic_ports_and_isolation,
)

T0 = 1793664000.0
FRESH = "2026-11-03T00:00:04Z"


def persist_explicit_inventory(root, observed):
    """Declared synthetic initial inventory, never a claimed fill or gate PASS."""
    root.mkdir(parents=True, exist_ok=True)
    writer = ProductivePortfolioSingleWriterV1(
        state_root=root, session_id="explicit-synthetic-inventory"
    )
    writer.acquire(now_unix=observed.event_time_unix)
    try:
        persist_reconciliation_bundle_atomic(
            state_root=root,
            writer=writer,
            portfolio=observed,
            evidence=ProductiveReconciliationEvidenceV1(
                capability_id="SYNTHETIC_INVENTORY",
                schema_version="explicit_synthetic_inventory.v1",
                owner="test-fixture",
                classification="EXPLICIT_SYNTHETIC_INITIAL_INVENTORY",
                alpha_enabled=False,
                pre_state_digest="",
                observed_state_digest=observed.digest(),
                post_state_digest=observed.digest(),
                reconciliation_decision="NO_RUNTIME_AUTHORIZATION",
            ),
        )
    finally:
        writer.release()


def binding_case(tmp_path, monkeypatch, *, count=5, lane_id="LANE_1", replacement=False):
    monkeypatch.setattr(sources, "OBSERVED_UNIX", T0 - 3600)
    monkeypatch.setattr(sources, "SOURCE_EVENT", str(int((T0 - 3600) * 1000)))
    rows = sources._five_rows() + [sources._perp("NEAR-USDT-SWAP")]
    chain = sources._persist_universe_and_ranking(tmp_path, rows)
    natives = [
        "SOL-USDT-SWAP",
        "ETH-USDT-SWAP",
        "ADA-USDT-SWAP",
        "LINK-USDT-SWAP",
        "APT-USDT-SWAP",
    ][:count]
    membership = sources._membership(
        chain["ranking"], [sources._cid(chain["ranking"], n) for n in natives]
    )
    topology = tmp_path / "topology"
    writer = sources._held_writer(topology)
    empty = PortfolioTruthSnapshotV1(event_time_unix=T0, wall_time_unix=T0, max_age_seconds=5)
    publication = publish_checked_lane_selections_v1(
        membership=membership,
        ranking_snapshot=chain["ranking"],
        topology_state_root_base=topology,
        writer=writer,
        repository_sha=sources.REPO_SHA,
        producer_observed_at_unix=T0 - 3600,
    )
    bounds = bind_occupied_lane_cap24_n1_instruments_v1(
        selections=publication.selections,
        topology_state_root_base=topology,
        ranking_state_root=chain["ranking_root"],
        universe_state_root=chain["universe_root"],
        reconciliation_state_root=chain["recon_root"],
        observed_portfolio=empty,
        mark_price_by_native_id=chain["mark_price_by_native_id"],
        repository_sha=sources.REPO_SHA,
        session_id="original-bound",
        now_unix=T0 - 3600,
    )
    assert len(bounds) == count
    positions = [
        {"instId": b.venue_native_id, "posSide": "net", "pos": "1.2"}
        for l, b in bounds.items()
        if l != lane_id
    ]
    host = PortfolioBudgetHostV1(
        root=tmp_path / "host",
        private_rest_fetch=_fetch(uid="acct-1", positions=positions),
        repository_sha=sources.REPO_SHA,
        session_id="bounded-close",
        expected_account_identity="acct-1",
        durable_mode="create",
        clock=lambda: T0,
        execution_environment="INTERNAL_SIMULATED_EXECUTION",
        entry_budget_policy=policy(),
    )
    recovery = host.observe_v1(bounds)
    persist_explicit_inventory(host.root / "reconciliation", recovery.observed)
    recovery.recover_v1(host.owner, _produce(value="125", epoch="2026-11-03T00:00:00Z"))
    oid = host.owner.budget_state_v1().observation_id
    holds = {}
    for lane in bounds:
        row = host.owner.try_reserve_v1(
            slot_id=lane,
            decision_id="entry:" + lane,
            cycle_id="initial",
            observation_id=oid,
            amount=Decimal(25),
        ).reservation
        holds[lane] = str(row.reservation_id)
        host.owner.commit_internal_pre_external_effect_v1(holds[lane])
    close, memory, _, _ = _case(
        monkeypatch,
        initial_ranking=chain["ranking"],
        bound_instrument=bounds[lane_id],
        prior_membership=membership,
        lane_id=lane_id,
    )
    memory.close()
    request = close.pop("post_close_feedback_request")
    target = "NEAR-USDT-SWAP" if replacement else bounds[lane_id].venue_native_id
    wanted = {b.venue_native_id for l, b in bounds.items() if l != lane_id} | {target}
    ordered = sorted(
        request.ranking.snapshot.ranked_candidates,
        key=lambda c: (c.venue_native_id != target, c.rank),
    )
    ranking = replace(
        request.ranking.snapshot,
        ranking_snapshot_id="bounded-fresh-ranking",
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
        state_root=chain["ranking_root"], writer_identity="bounded-test", session_id="fresh"
    )
    rw.acquire(now_unix=T0 + 5)
    try:
        persist_ranking_bundle_atomic_v1(
            state_root=chain["ranking_root"],
            writer=rw,
            snapshot=ranking,
            evidence={"ok": True, "capability_id": "CAPABILITY_2_2"},
        )
    finally:
        rw.release()
    body = json.dumps({"available_usdc": "125", "observed_at": FRESH}, sort_keys=True)
    margin = replace(
        _obs(value="125", epoch=FRESH), provenance_digest=hashlib.sha256(body.encode()).hexdigest()
    )
    capital = execute_current_productive_treasury_single_source_capital_handoff_v1(
        margin_observation=margin,
        instrument_id=bounds[lane_id].instrument_id,
        body_sha256=margin.provenance_digest,
        fresh_pretrade_get_status="TRUSTED_PRESENT",
        live_account_bound_status="TRUSTED_PRESENT",
        u04_p01_host_inputs=build_full_core_margin_inputs_from_budget_owner_v1(
            raw_acct_lv="2", budget_owner=host.owner
        ),
    )
    assert not capital.fail_closed, capital.reason_codes
    request = replace(
        request,
        observed_at_utc=FRESH,
        capital_handoff=capital,
        budget_owner=host.owner,
        closed_reservation_ids=(holds[lane_id],),
        expected_budget_observation_id=oid,
        ranking=replace(
            request.ranking,
            snapshot=ranking,
            provenance=replace(
                request.ranking.provenance,
                ranking_snapshot_id=ranking.ranking_snapshot_id,
                ranking_integrity_digest=ranking.integrity_digest,
                ranking_event_time=ranking.event_time,
            ),
        ),
    )
    positions = [
        {"instId": b.venue_native_id, "posSide": "net", "pos": "1.2"}
        for l, b in bounds.items()
        if l != lane_id
    ]
    host.fetch = _fetch(uid="acct-1", positions=positions)
    host.clock = lambda: T0 + 5
    recovery = host.observe_v1(bounds)
    recovery.recover_v1(host.owner, capital.producer_output)
    # The recovery consumed the first fresh account observation. The close
    # transition gets its own later capture and exact current predecessor.
    close_epoch = "2026-11-03T00:00:05Z"
    close_body = json.dumps({"available_usdc": "125", "observed_at": close_epoch}, sort_keys=True)
    close_margin = replace(
        _obs(value="125", epoch=close_epoch),
        provenance_digest=hashlib.sha256(close_body.encode()).hexdigest(),
    )
    capital = execute_current_productive_treasury_single_source_capital_handoff_v1(
        margin_observation=close_margin,
        instrument_id=bounds[lane_id].instrument_id,
        body_sha256=close_margin.provenance_digest,
        fresh_pretrade_get_status="TRUSTED_PRESENT",
        live_account_bound_status="TRUSTED_PRESENT",
        u04_p01_host_inputs=build_full_core_margin_inputs_from_budget_owner_v1(
            raw_acct_lv="2", budget_owner=host.owner
        ),
    )
    assert not capital.fail_closed, capital.reason_codes
    request = replace(
        request,
        observed_at_utc=close_epoch,
        capital_handoff=capital,
        expected_budget_observation_id=host.owner.budget_state_v1().observation_id,
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
    context = transition.BoundedSlotPostCloseContinuationV1(
        lifecycle, identity, request, tmp_path / "membership", recovery.observed, 5, host=host
    )
    cap24 = ProductiveFullAutonomyCap24BindContextV1(
        chain["ranking_root"],
        chain["universe_root"],
        host.root / "reconciliation",
        recovery.observed,
        chain["mark_price_by_native_id"],
        "next-binding",
        T0 + 5,
    )
    args = dict(
        membership=membership,
        ranking_snapshot=ranking.to_dict(),
        topology_root=topology,
        writer=writer,
        owner=host.owner,
        repository_sha=sources.REPO_SHA,
        origin_main_sha="explicit-synthetic-boundary",
        observed_unix=T0 + 5,
        cap24=cap24,
        target_cardinality=count,
        cycle_kwargs={
            "cycle_id_prefix": "after-confirmed-close",
            "observed_unix": T0 + 5,
            "host_budget_recovery": recovery,
        },
    )
    return context, args, bounds, holds, host, writer, target


def publish_binding(context, args):
    membership, handle = transition.prepare_v1(context, **args)
    retained = transition.retained_bounds_v1(handle[1])
    lane = handle[1]["binding"]["source_lane_id"]
    cap = args["cap24"]
    publication = publish_checked_lane_selections_v1(
        membership=membership,
        ranking_snapshot=args["ranking_snapshot"],
        topology_state_root_base=args["topology_root"],
        writer=args["writer"],
        repository_sha=args["repository_sha"],
        producer_observed_at_unix=args["observed_unix"],
        observed_portfolio=cap.observed_portfolio,
        replacement_admission_by_lane={
            lane: rotation_decision_for_lane_v1(
                venue_flat=True, reconciled=True, lane_health_allows_replacement=True
            )
        },
        retained_bound_by_lane=retained,
    )
    bounds = bind_occupied_lane_cap24_n1_instruments_v1(
        selections={l: s for l, s in publication.selections.items() if l not in retained},
        topology_state_root_base=args["topology_root"],
        ranking_state_root=cap.ranking_state_root,
        universe_state_root=cap.universe_state_root,
        reconciliation_state_root=cap.reconciliation_state_root,
        observed_portfolio=cap.observed_portfolio,
        mark_price_by_native_id=cap.mark_price_by_native_id,
        repository_sha=args["repository_sha"],
        session_id="bounded-next-binding",
        now_unix=cap.now_unix,
        bounded_reconciliation_scope=BoundedSlotReconciliationScopeV1(
            policy(), tuple(sorted(context.host.bindings.items())), "INTERNAL_SIMULATED_EXECUTION"
        ),
    )
    assert lane in bounds, "Original Cap24 must admit the closing slot"
    bounds.update(retained)
    pairs = compose_occupied_lane_mv2_dp_handoff_v1(
        admit_occupied_lane_bound_instruments_v1(bounds), publication.topology
    )
    recovery = transition.admit_v1(context, handle, owner=context.host.owner, pairs=pairs)
    return publication, pairs, recovery, handle


@pytest.mark.parametrize("replacement", [False, True])
@pytest.mark.parametrize(
    ("count", "lane_id"), [(2, "LANE_1"), (2, "LANE_2")] + [(5, f"LANE_{i}") for i in range(1, 6)]
)
def test_original_scoped_keep_replace_preserves_other_generations_and_holds(
    tmp_path, monkeypatch, count, lane_id, replacement
):
    context, args, old, holds, host, writer, target = binding_case(
        tmp_path, monkeypatch, count=count, lane_id=lane_id, replacement=replacement
    )
    try:
        before = host.owner.risk_snapshot_v1()["state"]
        publication, pairs, recovery, handle = publish_binding(context, args)
        assert pairs[lane_id][1].venue_native_id == target
        for lane in set(old) - {lane_id}:
            assert pairs[lane][1] == old[lane]
            assert host.owner.active_slot_sum_v1(lane) == 25
        after = host.owner.risk_snapshot_v1()["state"]
        assert {k: v for k, v in after["lane_bindings"].items() if k != lane_id} == {
            k: v for k, v in before["lane_bindings"].items() if k != lane_id
        }
        assert host.owner.active_slot_sum_v1(lane_id) == 0
        assert host.bindings == {l: b for l, (_, b) in pairs.items()}
        assert host.owner.budget_state_v1().admitted
        assert handle[1]["phase"] == "CONSUMING"
        assert set(publication.topology.retained_binding_lanes_v1) == set(old) - {lane_id}
        assert {
            r["reservation_id"]: r for r in after["reservations"] if r["slot_id"] != lane_id
        } == {r["reservation_id"]: r for r in before["reservations"] if r["slot_id"] != lane_id}
        new_bounds = host.bindings.copy()
        held = host.owner.active_sum_v1()
        host.close()
        cold = PortfolioBudgetHostV1(
            root=host.root,
            private_rest_fetch=host.fetch,
            repository_sha=host.repository_sha,
            session_id="cold-binding-readback",
            expected_account_identity=host.account,
            durable_mode="recover",
            clock=host.clock,
            execution_environment="INTERNAL_SIMULATED_EXECUTION",
            entry_budget_policy=policy(),
        )
        try:
            ctx = cold.observe_v1(new_bounds)
            assert not cold.owner.budget_state_v1().admitted
            assert cold.owner.active_sum_v1() == held
            ctx.recover_v1(cold.owner, context.request.capital_handoff.producer_output)
            assert cold.owner.budget_state_v1().admitted
            assert cold.owner.risk_snapshot_v1()["state"]["lane_bindings"] == after["lane_bindings"]
        finally:
            cold.close()
    finally:
        host.close()
        writer.release()


@pytest.mark.parametrize(
    "fault", ["missing-close", "foreign-binding", "open-target", "uncertain-consumption"]
)
def test_rebinding_refuses_unproven_scope_without_retiring_other_holds(
    tmp_path, monkeypatch, fault
):
    context, args, old, holds, host, writer, target = binding_case(tmp_path, monkeypatch)
    lane = context.request.execution.source.quantity_handoff.lane_id
    try:
        if fault == "missing-close":
            with pytest.raises(ValueError, match="UNPROVEN"):
                host.observe_after_bounded_slot_close_v1(old, request=context.request)
            assert host.owner.active_sum_v1() == 125
            return
        publication, pairs, recovery, handle = publish_binding(context, args)
        before = host.owner.risk_snapshot_v1()["state"]
        if fault == "foreign-binding":
            wrong = {l: b for l, (_, b) in pairs.items()}
            other = next(l for l in wrong if l != lane)
            wrong[other] = replace(wrong[other], selection_id="foreign-generation")
            with pytest.raises(ValueError, match="FOREIGN_HOST_BINDING_CHANGED"):
                host.observe_after_bounded_slot_close_v1(wrong, request=context.request)
        if fault == "open-target":
            host.fetch = _fetch(
                uid=host.account,
                positions=[
                    {"instId": b.venue_native_id, "posSide": "net", "pos": "1.2"}
                    for b in host.bindings.values()
                ],
            )
            with pytest.raises(ValueError, match="POSITION_NOT_FLAT"):
                host.observe_after_bounded_slot_close_v1(host.bindings, request=context.request)
            assert not host.owner.budget_state_v1().admitted
        if fault == "uncertain-consumption":
            with pytest.raises(ValueError, match="OUTCOME_UNCERTAIN"):
                transition.prepare_v1(context, **args)
        assert host.owner.risk_snapshot_v1()["state"] == before
        assert host.owner.active_sum_v1() == 100
    finally:
        host.close()
        writer.release()


@pytest.mark.parametrize(
    "fault",
    ["none", "no-scope", "live", "missing", "foreign", "quantity", "side", "duplicate", "nan"],
)
def test_bounded_inventory_requires_exact_known_match_and_never_repairs(fault):
    from tests.ops.test_bounded_multislot_entry_budget_v1 import bindings

    bounds = bindings()
    positions = tuple(
        PositionTruthV1.from_signed(instrument_id=b.instrument_id, signed_quantity="1")
        for b in bounds.values()
    )
    persisted = PortfolioTruthSnapshotV1(
        positions=positions, event_time_unix=T0, wall_time_unix=T0, max_age_seconds=5
    )
    observed = persisted
    scope = BoundedSlotReconciliationScopeV1(
        policy(), tuple(bounds.items()), "INTERNAL_SIMULATED_EXECUTION"
    )
    if fault == "no-scope":
        scope = None
    if fault == "live":
        scope = replace(scope, execution_environment="LIVE")
    if fault == "missing":
        observed = replace(observed, positions=positions[:-1])
    if fault == "foreign":
        observed = replace(
            observed, positions=(*positions[:-1], replace(positions[-1], instrument_id="foreign"))
        )
    if fault == "quantity":
        observed = replace(
            observed,
            positions=(replace(positions[0], signed_quantity=Decimal("0.9")), *positions[1:]),
        )
    if fault == "side":
        observed = replace(
            observed, positions=(replace(positions[0], side="SHORT"), *positions[1:])
        )
    if fault == "duplicate":
        observed = replace(observed, positions=(*positions, positions[0]))
    if fault == "nan":
        observed = replace(
            observed,
            positions=(replace(positions[0], signed_quantity=Decimal("NaN")), *positions[1:]),
        )
    category, plan, reasons = classify_productive_reconciliation_v1(
        persisted=persisted, observed=observed, now_unix=T0, bounded_reconciliation_scope=scope
    )
    assert (category.value == "MATCH") == (fault == "none"), reasons
    assert not plan.steps and not plan.admissible
