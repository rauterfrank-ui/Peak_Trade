"""Real budget transactions and Demo reconciliation with synthetic source ports only."""

from copy import deepcopy
from dataclasses import replace
from datetime import timedelta
from decimal import Decimal
import json

import pytest

from src.ops import btc_demo_lane3_v2 as demo
from src.ops.btc_demo_budget_reconciliation_host_v1 import (
    BtcDemoBudgetReconciliationHostV1,
    validate_btc_demo_coverage_v1,
)
from src.ops.exit_policy_producer_binding_v1.models_v1 import canonical_digest_v1
from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
    PortfolioCapitalReservationBudgetOwnerV1 as Owner,
    admit_sized_slot_reservation_v1,
)
from src.ops.portfolio_capital_reservation_budget_v1.test_phase_limits_v1 import (
    load_slot_entry_budget_v1,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_risk_capital_model_v1 import (
    produce_current_productive_29p_risk_capital_v1,
)
from src.governance.capital_risk_sizing_v1 import InstrumentQuantityConstraintsV1
from src.governance.canonical_order_intent_v1 import (
    CanonicalOrderIntentBuildInputV1,
    build_canonical_order_intent_v1,
)
from src.ops.full_core_live_path_composition_root_v1.models_v1 import VenuePlanCandidateV1
from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
    bind_final_order_envelope_from_venue_plan_v1,
)
from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.okx_response_mapper_v1 import (
    build_venue_native_order_body_v1,
)
from tests.ops.test_portfolio_capital_reservation_budget_contract_v1 import (
    _obs,
    _p01,
    _eligibility,
    _sizing_input,
)
from tests.ops.test_durable_portfolio_budget_recovery_v1 import _auto, _observed
from tests.ops.test_full_core_current_productive_envelope_bound_single_use_external_effect_send_seam_v1 import (
    _permit,
)
from tests.ops.test_btc_demo_source_observation_integrity_v1 import NOW, CoverageReads

EPOCH = NOW.isoformat()
ACCOUNT = "142"
BOUND = BoundInstrumentV1(
    instrument_id="btc-original-canonical-identity",
    venue_native_id=demo._NATIVE,
    ranking_snapshot_id="synthetic-ranking",
    ranking_integrity_digest="a" * 64,
    universe_snapshot_id="synthetic-universe",
    selection_id="synthetic-selection",
    selection_integrity_digest="b" * 64,
    selection_state="SELECTED",
)
BINDINGS = {"LANE_3": BOUND}


def capital():
    common = dict(bound_account_identity=ACCOUNT, bound_venue_identity="okx", decision_epoch=EPOCH)
    return produce_current_productive_29p_risk_capital_v1(
        observation=replace(_obs(value="30", epoch=EPOCH), **common),
        p01=replace(_p01(EPOCH), **common),
        eligibility=replace(_eligibility(EPOCH), **common),
    )


def owner_host(tmp_path, policy=None):
    root = tmp_path / "demo"
    root.mkdir(mode=0o700)
    lane = root / "testnet-state/LANE_3"
    lane.mkdir(parents=True)
    (root / "btc-lane3-testnet.json").write_text(
        json.dumps(
            {
                "lane": "LANE_3",
                "instrument": demo._NATIVE,
                "environment": "TESTNET",
                "roots": {"lane": str(lane)},
            }
        )
    )
    from src.ops.btc_demo_testnet_entry_reservation_v1 import BtcDemoBudgetOwnerV2

    owner = BtcDemoBudgetOwnerV2(
        durable_root=lane.parent / "budget-owner/owner",
        durable_account_identity=ACCOUNT,
        durable_mode="create",
        durable_lane_bindings=BINDINGS,
        entry_budget_policy=policy,
    )
    observed = replace(_observed(), event_time_unix=NOW.timestamp(), wall_time_unix=NOW.timestamp())
    recovered = _auto(
        owner, tmp_path, output=capital(), observed=observed, bindings=BINDINGS, now=NOW.timestamp()
    )
    assert recovered.disposition.value == "ADMITTED", recovered.reason_codes
    return BtcDemoBudgetReconciliationHostV1(
        owner=owner, bound=BOUND, account=ACCOUNT, testnet_root=root
    ), observed


def seed_attempt(
    tmp_path,
    *,
    existing_host=None,
    decision_id="btc-entry",
    cycle_id="fixture-cycle",
    quantity_cap="0.0001",
    contract_multiplier="1",
    lot_size="0.0001",
    side="LONG",
):
    # Explicit synthetic USDC sizing operands isolate the execution consumer.
    # They are not a conversion of the later fixture's USD fill price and do
    # not certify native USD sizing or current Demo collateral.
    host = existing_host
    if host is None:
        host, _ = owner_host(tmp_path)
    request = _sizing_input(
        decision_id=decision_id,
        selected_side=side,
        decision_outcome="enter_" + side.lower(),
        instrument_id=BOUND.instrument_id,
        reference_price=Decimal("64000"),
        protective_stop_price=Decimal("63000" if side == "LONG" else "65000"),
        configured_quantity_cap=Decimal(quantity_cap),
        account_equity=Decimal("30"),
        scope_capital_limit=Decimal("25"),
        total_capital_limit=Decimal("25"),
        instrument=InstrumentQuantityConstraintsV1(
            instrument_id=BOUND.instrument_id,
            market_type="futures",
            contract_kind="LINEAR",
            contract_multiplier=Decimal(contract_multiplier),
            lot_size=Decimal(lot_size),
            minimum_quantity=Decimal(lot_size),
            maximum_quantity=Decimal("1"),
            minimum_notional=Decimal("1"),
            tick_size=Decimal("0.1"),
            instrument_metadata_version="SYNTHETIC_USDC_CONSUMER_FIXTURE",
        ),
    )
    reserved = admit_sized_slot_reservation_v1(
        host.owner,
        sizing_input=request,
        slot_id="LANE_3",
        decision_id=decision_id,
        cycle_id=cycle_id,
        observation=replace(_obs(value="30", epoch=EPOCH), bound_account_identity=ACCOUNT),
        p01=replace(_p01(EPOCH), bound_account_identity=ACCOUNT),
        eligibility=replace(_eligibility(EPOCH), bound_account_identity=ACCOUNT),
        instrument_id=BOUND.instrument_id,
        account_identity=ACCOUNT,
        fresh_pretrade_get_status="TRUSTED_PRESENT",
        live_account_bound_status="TRUSTED_PRESENT",
        fresh_evidence_fetched=True,
        fresh_evidence_validated=True,
    )
    assert reserved.disposition.value == "ADMITTED", reserved.reason_codes
    rid = str(reserved.reservation.reservation_id)
    applied = host.owner._sizing_bindings[rid].applied_input
    intent = build_canonical_order_intent_v1(
        CanonicalOrderIntentBuildInputV1(
            sizing_input=applied,
            sizing_decision=reserved.sizing_decision,
            intent_id="btc-intent",
            trading_epoch="fixture-epoch",
            canonical_trading_logic_version="synthetic-source",
            intent_action="ENTER_" + side,
            policy_digest="fixture-policy",
            order_type_policy="MARKET_ONLY",
            price_policy="EXPLICIT_NONE",
            time_in_force_policy="GTC",
            max_slippage_policy="ZERO",
            expected_position_side=side,
            current_reconciled_exposure=Decimal("0"),
        )
    ).intent
    assert intent is not None
    quantity = str(reserved.sizing_decision.final_quantity)
    body = build_venue_native_order_body_v1(
        client_order_id="ptDemo3",
        instrument=demo._NATIVE,
        order_type="market",
        side="buy" if side == "LONG" else "sell",
        quantity=quantity,
        td_mode="cross",
        px=None,
        reduce_only=False,
    )
    plan = VenuePlanCandidateV1(
        instrument_id=demo._NATIVE,
        side="buy" if side == "LONG" else "sell",
        quantity=quantity,
        order_type="market",
        td_mode="cross",
        reduce_only=False,
        clordid="ptDemo3",
        venue_native_payload=body,
        quantity_source="synthetic-original-sizing",
        side_source="synthetic-original-decision",
        instrument_source="synthetic-binding",
        path_kind="synthetic-testnet",
        environment="TESTNET",
    )
    envelope = bind_final_order_envelope_from_venue_plan_v1(
        plan, admission_ref="fixture", provenance_ref="fixture", creation_epoch=EPOCH
    )
    host.owner.commit_internal_pre_external_effect_v1(rid)
    host.owner.bind_execution_plan_v1(rid, envelope, canonical_intent=intent, venue_plan=plan)
    context = host.owner.execution_plan_context_v1(rid, envelope)
    identity = host.owner.begin_execution_submit_v2(rid, envelope, context, _permit(envelope))
    return host, rid, identity


class ExecutionReads:
    def __init__(self, identity, *, state="filled", quantity="0.0001", fault=None):
        self.identity, self.state, self.quantity, self.fault = identity, state, quantity, fault
        self.calls = []

    def read(self, path, **query):
        self.calls.append(path)
        i = self.identity
        stamp = str(int(NOW.timestamp() * 1000))
        common = {
            "instId": demo._NATIVE,
            "clOrdId": i.clordid,
            "ordId": "432",
            "posSide": "net",
            "side": "buy",
        }
        order = {
            **common,
            "reduceOnly": "false",
            "state": self.state,
            "sz": i.final_quantity,
            "accFillSz": self.quantity,
        }
        rows = []
        if path == demo._CONFIG:
            rows = [{"uid": ACCOUNT, "posMode": "net_mode"}]
        if path == demo._ORDER:
            rows = [order]
        if path == demo._FILLS and Decimal(self.quantity) > 0:
            rows = [
                {
                    **common,
                    "tradeId": "98",
                    "fillTime": stamp,
                    "fillSz": self.quantity,
                    "fillPx": "64000",
                    "feeCcy": "USDC",
                    "fee": "-0.0032",
                }
            ]
        if path == demo._POSITIONS and Decimal(self.quantity) > 0:
            rows = [
                {
                    "instId": demo._NATIVE,
                    "posSide": "net",
                    "pos": self.quantity,
                    "tradeId": "98",
                    "avgPx": "64000",
                    "uTime": stamp,
                }
            ]
        if self.fault == "foreign-account" and path == demo._CONFIG:
            rows[0]["uid"] = "999"
        if self.fault == "open-pending" and path == demo._PENDING:
            rows = [{**order, "state": "live"}]
        if self.fault == "flat-position" and path == demo._POSITIONS:
            rows = []
        if self.fault == "incomplete" and path == demo._FILLS:
            rows = rows * 100
        return {"code": "0", "data": rows}, NOW


def test_original_demo_attempt_reaches_budget_reconciler_once_and_retains_hold(tmp_path):
    host, rid, identity = seed_attempt(tmp_path)
    try:
        before = host.owner.active_sum_v1()
        result = host.reconcile_attempt_v1(
            reads=ExecutionReads(identity), reservation_id=rid, clock=lambda: NOW.timestamp()
        )
        assert result["reconciliation"]["matched"] is True
        assert result["reconciliation"]["reservation_released"] is False
        assert host.owner.active_sum_v1() == before > 0
        revision = host.budget_revision_ref_v1()
        again = host.reconcile_attempt_v1(
            reads=ExecutionReads(identity), reservation_id=rid, clock=lambda: NOW.timestamp()
        )
        assert again == result and host.budget_revision_ref_v1() == revision
    finally:
        host.owner.close()


@pytest.mark.parametrize(
    "failed_path", [demo._CONFIG, demo._PENDING, demo._ORDER, demo._FILLS, demo._POSITIONS]
)
def test_execution_api_error_never_becomes_clean_reconciliation(tmp_path, failed_path):
    host, rid, identity = seed_attempt(tmp_path)

    class ErrorReads(ExecutionReads):
        def read(self, path, **query):
            payload, acquired = super().read(path, **query)
            if path == failed_path:
                payload["code"] = "50000"
            return payload, acquired

    try:
        held = host.owner.active_sum_v1()
        with pytest.raises(ValueError, match="RESPONSE_OR_RECEIPT_UNPROVEN"):
            host.reconcile_attempt_v1(
                reads=ErrorReads(identity), reservation_id=rid, clock=lambda: NOW.timestamp()
            )
        assert host.owner.active_sum_v1() == held > 0
        assert host.owner.budget_state_v1().admitted is False
        assert host.owner.execution_links_v1()[rid]["reconciliation"] is None
    finally:
        host.owner.close()


def test_changed_original_budget_head_during_get_cannot_be_overwritten(tmp_path):
    host, rid, identity = seed_attempt(tmp_path)

    class ChangingReads(ExecutionReads):
        def read(self, path, **query):
            if path == demo._POSITIONS:
                host.owner.restart_fail_closed_v1()
            return super().read(path, **query)

    try:
        held = host.owner.active_sum_v1()
        with pytest.raises(ValueError, match="BUDGET_HEAD_CHANGED"):
            host.reconcile_attempt_v1(
                reads=ChangingReads(identity), reservation_id=rid, clock=lambda: NOW.timestamp()
            )
        assert host.owner.active_sum_v1() == held > 0
        assert host.owner.execution_links_v1()[rid]["reconciliation"] is None
    finally:
        host.owner.close()


def test_closed_owner_cannot_supply_committed_revision(tmp_path):
    from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
        PortfolioCapitalBudgetError,
    )

    host, _ = owner_host(tmp_path)
    host.owner.close()
    with pytest.raises(PortfolioCapitalBudgetError, match="RISK_DURABLE_OWNER_REQUIRED"):
        host.budget_revision_ref_v1()


@pytest.mark.parametrize(
    "state,quantity,released",
    [
        ("canceled", "0", True),
        ("live", "0", False),
        ("partially_filled", "0.00005", False),
        ("canceled", "0.00005", False),
    ],
)
def test_only_original_confirmed_no_fill_cancellation_releases_budget(
    tmp_path, state, quantity, released
):
    host, rid, identity = seed_attempt(tmp_path)
    try:
        result = host.reconcile_attempt_v1(
            reads=ExecutionReads(identity, state=state, quantity=quantity),
            reservation_id=rid,
            clock=lambda: NOW.timestamp(),
        )
        assert result["reconciliation"]["reservation_released"] is released
        assert (host.owner.active_sum_v1() == 0) is released
    finally:
        host.owner.close()


def test_original_writer_identity_passes_new_guard_but_not_original_demo_guard(tmp_path):
    import ast
    import subprocess

    host, rid, identity = seed_attempt(tmp_path)
    try:
        assert identity.venue == "okx" and identity.execution_environment == "TESTNET"
        assert identity.native_id == demo._NATIVE and identity.slot_id == "LANE_3"
        source = subprocess.check_output(
            [
                "git",
                "show",
                "f52d52a6e0cd47cbec048adba9e9ff8283f9f693:src/ops/btc_demo_lane3_v2.py",
            ],
            text=True,
        )
        original = next(
            n
            for n in ast.parse(source).body
            if isinstance(n, ast.FunctionDef) and n.name == "_read_original_attempt"
        )
        namespace = dict(vars(demo))
        exec(
            compile(
                ast.fix_missing_locations(ast.Module(body=[original], type_ignores=[])),
                "<original-btc-guard>",
                "exec",
            ),
            namespace,
        )
        revision = host.budget_revision_ref_v1()
        with pytest.raises(ValueError, match="ORIGINAL_V2_ENTRY_ATTEMPT_REQUIRED"):
            namespace["_read_original_attempt"](
                demo._demo_lane_root(host.root), ACCOUNT, rid, revision
            )
        actual, _, _ = demo._read_original_attempt(
            demo._demo_lane_root(host.root), ACCOUNT, rid, revision
        )
        assert actual == identity
        fill = demo._confirmed_first_fill(ExecutionReads(identity), identity)
        assert fill.filled_quantity == identity.final_quantity and fill.order_id == "432"
        assert fill.price == Decimal("64000")
    finally:
        host.owner.close()


@pytest.mark.parametrize(
    "fault", ["foreign-account", "flat-position", "incomplete", "stale", "future"]
)
def test_unproven_observation_never_releases_original_hold(tmp_path, fault):
    host, rid, identity = seed_attempt(tmp_path)
    try:
        before = host.owner.active_sum_v1()
        reads = ExecutionReads(identity, fault=fault)
        now = NOW.timestamp() + (6 if fault == "stale" else -1 if fault == "future" else 0)
        if fault in {"foreign-account", "stale", "future"}:
            with pytest.raises(ValueError):
                host.reconcile_attempt_v1(reads=reads, reservation_id=rid, clock=lambda: now)
            assert host.owner.budget_state_v1().admitted is False
        else:
            result = host.reconcile_attempt_v1(reads=reads, reservation_id=rid, clock=lambda: now)
            assert result["reconciliation"]["matched"] is False
            assert result["reconciliation"]["reservation_released"] is False
        assert host.owner.active_sum_v1() == before > 0
    finally:
        host.owner.close()


def test_actual_source_receipt_times_are_not_replaced_by_last_position_time(tmp_path):
    host, rid, identity = seed_attempt(tmp_path)

    class Staggered(ExecutionReads):
        def read(self, path, **query):
            payload, _ = super().read(path, **query)
            delay = {
                demo._CONFIG: 0,
                demo._PENDING: 1,
                demo._ORDER: 2,
                demo._FILLS: 3,
                demo._POSITIONS: 4,
            }[path]
            return payload, NOW + timedelta(seconds=delay)

    try:
        snapshot, _, _, _, _ = demo.collect_btc_demo_execution_observation_v1(
            Staggered(identity), identity
        )
        by_layer = {r.layer: r for r in snapshot.evidence_items}
        assert {r.received_at for r in by_layer.values()} == {
            (NOW + timedelta(seconds=2)).isoformat(),
            (NOW + timedelta(seconds=3)).isoformat(),
        }
        assert (
            snapshot.pending_orders_observation["received_at"]
            == (NOW + timedelta(seconds=1)).isoformat()
        )
        assert snapshot.pending_orders_observation["identity_digest"] == identity.identity_digest()
    finally:
        host.owner.close()


@pytest.mark.parametrize(
    "fault", ["digest", "rehashed-value", "foreign-account", "stale", "future"]
)
def test_coverage_reproduction_refuses_unproven_budget_input(fault):
    report = demo.read_btc_demo_coverage_v2(reads=CoverageReads(), expected_uid=ACCOUNT)
    now = NOW.timestamp()
    if fault in {"digest", "rehashed-value"}:
        report["available_equity"]["USDC"] = "3000"
        if fault == "rehashed-value":
            report["coverage_digest"] = canonical_digest_v1(
                {k: v for k, v in report.items() if k != "coverage_digest"}
            )
    elif fault == "foreign-account":
        report["account_identity"] = "999"
        report["coverage_digest"] = canonical_digest_v1(
            {k: v for k, v in report.items() if k != "coverage_digest"}
        )
    else:
        now += 6 if fault == "stale" else -1
    with pytest.raises(ValueError):
        validate_btc_demo_coverage_v1(report, account=ACCOUNT, now=now)


@pytest.mark.parametrize("concurrent_change", [False, True])
def test_typed_original_usdc_capital_reaches_original_bounded_owner(
    tmp_path, monkeypatch, concurrent_change
):
    from pathlib import Path

    policy = load_slot_entry_budget_v1(
        Path(__file__).resolve().parents[2]
        / "docs/ops/specs/BOUNDED_MULTISLOT_TEST_ENTRY_BUDGET_V5.json"
    )
    host, observed = owner_host(tmp_path, policy)
    try:
        report = demo.read_btc_demo_coverage_v2(reads=CoverageReads(), expected_uid=ACCOUNT)
        from src.ops.portfolio_capital_reservation_budget_v1.recovery_v1 import (
            reconcile_durable_budget_startup_v1,
        )

        reconcile_durable_budget_startup_v1(
            host.owner,
            output=capital(),
            observed=observed,
            lane_bindings=BINDINGS,
            reconciliation_state_root=tmp_path / "reconciliation",
            session_id="fixture",
            repository_sha="f" * 40,
            now_unix=NOW.timestamp(),
            capital_max_age_seconds=5,
        )
        # Reuse the exact original gate's typed evidence, not a fabricated PASS.
        from src.ops.productive_reconciliation_runtime_binding_v1.startup_gate_v1 import (
            run_productive_reconciliation_startup_gate_v1,
        )

        gate = run_productive_reconciliation_startup_gate_v1(
            state_root=tmp_path / "reconciliation",
            observed=observed,
            session_id="fixture",
            repository_sha="f" * 40,
            now_unix=NOW.timestamp(),
        )
        if concurrent_change:
            from src.ops import btc_demo_budget_reconciliation_host_v1 as budget_host

            original_validation = budget_host.validate_btc_demo_coverage_v1
            winning_revisions = []

            def advance_during_validation(*args, **kwargs):
                validated = original_validation(*args, **kwargs)
                host.owner.restart_fail_closed_v1()
                winning_revisions.append(host.budget_revision_ref_v1())
                return validated

            monkeypatch.setattr(
                budget_host, "validate_btc_demo_coverage_v1", advance_during_validation
            )
        result = host.admit_budget_v1(
            coverage=report,
            output=capital(),
            observed=observed,
            reconciliation=gate,
            now=NOW.timestamp(),
        )
        if concurrent_change:
            assert result.disposition.value == "FAIL_CLOSED"
            assert result.reason_codes == ("DURABLE_RECOVERY_HEAD_CHANGED",)
            assert result.mutated is False and result.reservation is None
            assert host.budget_revision_ref_v1() == winning_revisions[0]
            assert host.owner.budget_state_v1().recovery_required
            return
        assert result.disposition.value in {"ADMITTED", "IDEMPOTENT_REPLAY"}
        assert host.owner.admitted_budget_v1() == Decimal("30")
        assert host.owner.entry_budget_policy_v1().per_slot_reserved_notional_limit == 25
        assert report["venue_settlement_currency"] == "USD"
        assert report["usd_usdc_account_settlement_proven"] is False
    finally:
        host.owner.close()


@pytest.mark.parametrize(
    "fault",
    ["raw-output", "wrong-account", "wrong-venue", "usd-capital", "too-large", "missing-policy"],
)
def test_budget_host_does_not_mint_or_relabel_raw_capital(tmp_path, fault):
    from pathlib import Path

    policy = (
        None
        if fault == "missing-policy"
        else load_slot_entry_budget_v1(
            Path(__file__).resolve().parents[2]
            / "docs/ops/specs/BOUNDED_MULTISLOT_TEST_ENTRY_BUDGET_V5.json"
        )
    )
    host, observed = owner_host(tmp_path, policy)
    try:
        output = capital()
        if fault == "raw-output":
            output = {"value": "30"}
        elif fault == "wrong-account":
            output = replace(output, bound_account_identity="999")
        elif fault == "wrong-venue":
            output = replace(output, bound_venue_identity="OKX_EEA_DEMO")
        elif fault == "usd-capital":
            output = replace(output, settlement_currency="USD")
        elif fault == "too-large":
            output = replace(output, value="31")
        with pytest.raises(ValueError):
            host.admit_budget_v1(
                coverage=demo.read_btc_demo_coverage_v2(
                    reads=CoverageReads(), expected_uid=ACCOUNT
                ),
                output=output,
                observed=observed,
                reconciliation=None,
                now=NOW.timestamp(),
            )
        assert host.owner.budget_state_v1().admitted is False
        assert host.owner.active_sum_v1() == 0
    finally:
        host.owner.close()


def test_original_one_hour_window_is_not_reset_on_reentry_and_never_releases_hold(tmp_path):
    host, rid, identity = seed_attempt(tmp_path)
    try:
        root = host.root / "host-state"
        before = host.owner.active_sum_v1()
        # Already-expired original window must perform no GET, submit or release.
        reads = ExecutionReads(identity)
        result = host.supervise_reconciliation_v1(
            state_root=root,
            started_at=NOW.timestamp() - 3600,
            reads=reads,
            clock=lambda: NOW.timestamp(),
            pause=lambda _: pytest.fail("Expired window slept"),
        )
        assert result["status"] == "WINDOW_ENDED" and result["orders_sent"] == 0
        assert result["window"]["deadline"] == NOW.timestamp()
        assert not reads.calls and host.owner.active_sum_v1() == before > 0
        with pytest.raises((ValueError, RuntimeError)):
            host.supervise_reconciliation_v1(
                state_root=root,
                started_at=NOW.timestamp(),
                reads=reads,
                clock=lambda: NOW.timestamp(),
                pause=lambda _: None,
            )
        assert host.owner.active_sum_v1() == before
    finally:
        host.owner.close()


def test_synthetic_hour_uses_original_absolute_deadline_without_network(tmp_path):
    host, _ = owner_host(tmp_path)
    current = NOW.timestamp()
    sleeps = []

    def clock():
        return current

    def pause(seconds):
        nonlocal current
        sleeps.append(seconds)
        current += seconds

    try:
        result = host.supervise_reconciliation_v1(
            state_root=host.root / "host-state",
            started_at=current,
            reads=None,
            clock=clock,
            pause=pause,
            poll_seconds=700,
        )
        assert current == NOW.timestamp() + 3600 and sum(sleeps) == 3600
        assert result["observations"] == 0 and result["orders_sent"] == 0
    finally:
        host.owner.close()


def test_fresh_final_index_does_not_retimestamp_old_account_margin():
    times = {demo._CONFIG: NOW - timedelta(seconds=6), demo._BALANCE: NOW - timedelta(seconds=6)}
    report = demo.read_btc_demo_coverage_v2(reads=CoverageReads(times=times), expected_uid=ACCOUNT)
    with pytest.raises(ValueError, match="STALE_OR_FUTURE"):
        validate_btc_demo_coverage_v1(report, account=ACCOUNT, now=NOW.timestamp())


def test_fresh_last_position_does_not_retimestamp_old_execution_evidence(tmp_path):
    host, rid, identity = seed_attempt(tmp_path)

    class Staggered(ExecutionReads):
        def read(self, path, **query):
            payload, _ = super().read(path, **query)
            delay = {
                demo._CONFIG: 0,
                demo._PENDING: 1,
                demo._ORDER: 2,
                demo._FILLS: 3,
                demo._POSITIONS: 4,
            }[path]
            return payload, NOW + timedelta(seconds=delay)

    try:
        with pytest.raises(ValueError, match="STALE_OR_FUTURE"):
            host.reconcile_attempt_v1(
                reads=Staggered(identity), reservation_id=rid, clock=lambda: NOW.timestamp() + 6
            )
        assert host.owner.active_sum_v1() > 0
        assert host.owner.budget_state_v1().admitted is False
    finally:
        host.owner.close()


def test_cold_original_owner_preserves_attempt_identity_and_fill_floor(tmp_path):
    host, rid, identity = seed_attempt(tmp_path)
    result = host.reconcile_attempt_v1(
        reads=ExecutionReads(identity), reservation_id=rid, clock=lambda: NOW.timestamp()
    )
    held = host.owner.active_sum_v1()
    scope = host.owner.durable_scope_identity_v1()
    host.owner.close()
    owner = Owner(
        durable_root=scope["root"],
        durable_account_identity=ACCOUNT,
        durable_mode="recover",
        durable_lane_bindings=BINDINGS,
    )
    try:
        restored = BtcDemoBudgetReconciliationHostV1(
            owner=owner, bound=BOUND, account=ACCOUNT, testnet_root=host.root
        )
        assert (
            owner.execution_links_v1()[rid]["identity"] == result["identity"] == identity.to_dict()
        )
        assert owner.budget_state_v1().recovery_required
        regression = restored.reconcile_attempt_v1(
            reads=ExecutionReads(identity, state="canceled", quantity="0"),
            reservation_id=rid,
            clock=lambda: NOW.timestamp(),
        )
        assert regression["reconciliation"]["reservation_released"] is False
        assert owner.active_sum_v1() == held > 0
    finally:
        owner.close()


@pytest.mark.parametrize("fault", ["source-changed", "revision-changed", "unmatched", "partial"])
def test_v2_handoff_rejects_changed_sources_or_unconfirmed_entry(tmp_path, fault):
    host, rid, identity = seed_attempt(tmp_path)
    try:
        result = host.reconcile_attempt_v1(
            reads=ExecutionReads(
                identity, state="partially_filled" if fault == "partial" else "filled"
            ),
            reservation_id=rid,
            clock=lambda: NOW.timestamp(),
        )
        if fault == "source-changed":
            next(row for row in result["source_observations"] if row["path"] == demo._ORDER)[
                "payload"
            ]["data"][0]["ordId"] = "999"
        elif fault == "revision-changed":
            result["budget_revision"][0] += 1
        elif fault == "unmatched":
            result["reconciliation"]["matched"] = False
        with pytest.raises(ValueError):
            host.bind_confirmed_entry_v1(
                reconciliation=result,
                repository_sha="f" * 40,
                config_digest="c" * 64,
                writer_session_id="fixture",
                g17_producer=None,
            )
        assert host.owner.active_sum_v1() > 0
        assert not (demo._demo_lane_root(host.root) / "position-episodes").exists()
    finally:
        host.owner.close()


def test_supervisor_stop_is_terminal_and_keeps_original_obligation(tmp_path):
    host, rid, identity = seed_attempt(tmp_path)
    root = host.root / "host-state"
    root.mkdir()
    (root / "STOP").touch()
    reads = ExecutionReads(identity)
    try:
        result = host.supervise_reconciliation_v1(
            state_root=root,
            started_at=NOW.timestamp(),
            reads=reads,
            clock=lambda: NOW.timestamp(),
            pause=lambda _: pytest.fail("STOP slept"),
        )
        assert result["status"] == "STOPPED" and not reads.calls
        assert host.owner.budget_state_v1().admitted is False
        (root / "STOP").unlink()
        again = host.supervise_reconciliation_v1(
            state_root=root,
            started_at=NOW.timestamp(),
            reads=reads,
            clock=lambda: NOW.timestamp(),
            pause=lambda _: pytest.fail("Closed window reopened"),
        )
        assert again == result and not reads.calls and host.owner.active_sum_v1() > 0
    finally:
        host.owner.close()


@pytest.mark.parametrize("scope", ["root", "testnet-state", "lane", "budget", "symlink"])
def test_supervisor_metadata_cannot_overlap_original_owner_paths(tmp_path, scope):
    host, _, _ = seed_attempt(tmp_path)
    roots = {
        "root": host.root,
        "testnet-state": host.root / "testnet-state",
        "lane": demo._demo_lane_root(host.root),
        "budget": host.root / "testnet-state/budget-owner/owner",
        "symlink": host.root / "linked",
    }
    if scope == "symlink":
        roots["symlink"].symlink_to(demo._demo_lane_root(host.root), target_is_directory=True)
    try:
        with pytest.raises(ValueError, match="STATE_SCOPE_MISMATCH"):
            host.supervise_reconciliation_v1(
                state_root=roots[scope],
                started_at=NOW.timestamp(),
                reads=None,
                clock=lambda: NOW.timestamp() + 3600,
                pause=lambda _: None,
            )
        assert host.owner.active_sum_v1() > 0
    finally:
        host.owner.close()
