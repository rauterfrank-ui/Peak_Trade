"""Numerical model→original sizing→durable hold→original envelope controls."""

from dataclasses import replace
from decimal import Decimal as D

import pytest

from src.risk.decision_bound_model_adapters_v1 import (
    BookLevelV1,
    InstrumentRiskInputV1,
    OfflineRiskPolicyV1,
    OfflineRiskRequestV1,
    PortfolioRiskInputV1,
    PositionRiskInputV1,
    ReturnObservationV1,
    evaluate_offline_risk_v1,
)
from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
    admit_sized_slot_reservation_v1,
    ReserveDispositionV1,
)
from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
    build_final_order_envelope_v1,
)
from tests.ops.test_durable_portfolio_budget_recovery_v1 import (
    _owner,
    _auto,
    BOUND,
    NOW,
    EPOCH,
    BINDINGS,
)
from tests.ops.test_portfolio_capital_reservation_budget_contract_v1 import (
    _sizing_input,
    _obs,
    _p01,
    _eligibility,
    ACCOUNT,
    TRUSTED,
    BOUND as ACCOUNT_BOUND,
)

MS = int(NOW * 1000)


def _request(*, loss="0.01", decision="decision-001", cap=None):
    from src.ops.portfolio_capital_reservation_budget_v1.recovery_v1 import lane_bindings_v1

    epoch = lane_bindings_v1(BINDINGS)["LANE_1"]["instrument_epoch"]
    returns = tuple(
        ReturnObservationV1(
            MS - (7 - i) * 60000, MS - (7 - i) * 60000, D(loss) * (-1 if i % 2 == 0 else 1)
        )
        for i in range(8)
    )
    item = InstrumentRiskInputV1(
        BOUND.instrument_id,
        BOUND.venue_native_id,
        epoch,
        "LINEAR",
        "CONTRACTS",
        D(1),
        "USDC",
        "USDC",
        D(100),
        D(1),
        MS,
        MS,
        MS,
        MS,
        "synthetic:mark",
        "synthetic:identity-fx",
        60000,
        returns,
        (BookLevelV1(D("99.99"), D(10)),),
        (BookLevelV1(D("100.01"), D(10)),),
        MS,
        MS,
        "synthetic:depth",
        D(100000),
        86400000,
        MS,
        MS,
        "synthetic:daily-notional-volume",
    )
    data = PortfolioRiskInputV1(
        ACCOUNT,
        "INTERNAL_SIMULATED_EXECUTION",
        MS,
        MS,
        MS,
        "synthetic:complete-account-snapshot",
        "USDC",
        "ACCOUNT_EQUITY",
        D(100),
        MS,
        MS,
        "synthetic:total-equity",
        (),
        (item,),
    )
    policy = OfflineRiskPolicyV1(
        "e2-risk-fixture.v1",
        "synthetic:explicit-owner-test-policy",
        "EXPLICIT_OFFLINE_TEST_POLICY",
        D("0.95"),
        D("0.05"),
        60000,
        60000,
        4,
        5000,
        600000,
        1000,
        D("0.02"),
        D("0.2"),
        "vol_spike",
        "HISTORICAL_VAR",
        D(3),
        1,
        D(10),
        D(10),
        D(20),
        D(1),
        D("0.1"),
        86400000,
    )
    return OfflineRiskRequestV1(
        data,
        policy,
        "LANE_1",
        decision,
        "cycle-1",
        BOUND.instrument_id,
        BOUND.venue_native_id,
        epoch,
        "LONG",
        "market",
        None,
        cap,
    )


def _admit(owner, request, *, sizing=None, handoff_journal=None):
    return admit_sized_slot_reservation_v1(
        owner,
        observation=_obs(epoch=EPOCH),
        p01=_p01(EPOCH),
        eligibility=_eligibility(EPOCH),
        slot_id="LANE_1",
        decision_id=request.decision_id,
        cycle_id=request.cycle_id,
        instrument_id=BOUND.instrument_id,
        account_identity=ACCOUNT,
        sizing_input=sizing or _sizing_input(decision_id=request.decision_id),
        fresh_pretrade_get_status=TRUSTED,
        live_account_bound_status=ACCOUNT_BOUND,
        fresh_evidence_fetched=True,
        fresh_evidence_validated=True,
        restrictive_risk=request,
        handoff_journal=handoff_journal,
    )


def _envelope(quantity, *, side="buy", **kw):
    return build_final_order_envelope_v1(
        instrument_id=BOUND.venue_native_id,
        side=side,
        order_type="market",
        quantity=str(quantity),
        quantity_unit="CONTRACTS",
        td_mode="cross",
        reduce_only=False,
        client_order_id="e2-bound-entry",
        path_kind="enter",
        venue_plan_clordid="e2-bound-entry",
        quantity_source="original-sizing",
        side_source="original-decision",
        instrument_source="original-binding",
        admission_ref="offline-only",
        provenance_ref="offline-numeric-risk",
        creation_epoch=EPOCH,
        **kw,
    )


@pytest.mark.parametrize("loss,allowed", [("0.01", True), ("0.1", False)])
def test_computed_var_changes_actual_reservation(tmp_path, loss, allowed):
    owner = _owner(tmp_path)
    try:
        assert _auto(owner, tmp_path).disposition is ReserveDispositionV1.ADMITTED
        result = _admit(owner, _request(loss=loss))
        assert (result.disposition is ReserveDispositionV1.ADMITTED) == allowed, result.reason_codes
        assert owner.stored_reservation_count_v1() == int(allowed)
        if allowed:
            assert result.sizing_decision.final_quantity == 1 and owner.active_sum_v1() == 100
            binding = owner.reservation_risk_binding_v1(result.reservation.reservation_id)
            assert binding.request.data.capital_denominator_kind == "ACCOUNT_EQUITY"
            owner.bind_execution_plan_v1(
                result.reservation.reservation_id, _envelope(result.sizing_decision.final_quantity)
            )
        else:
            assert result.reason_codes[0] == "RISK_VAR_LIMIT" and owner.active_sum_v1() == 0
    finally:
        owner.close()


@pytest.mark.parametrize("cap,expected", [(D("0.4"), D("0.4")), (D(0), None)])
def test_cap_uses_original_sizing_then_final_quantity_is_rechecked(tmp_path, cap, expected):
    owner = _owner(tmp_path)
    try:
        _auto(owner, tmp_path)
        result = _admit(owner, _request(cap=cap))
        if expected is None:
            assert (
                result.disposition is ReserveDispositionV1.FAIL_CLOSED
                and owner.active_sum_v1() == 0
            )
        else:
            assert result.sizing_decision.final_quantity == expected
            assert result.reservation.amount == 40
            assert D(
                owner.reservation_risk_binding_v1(result.reservation.reservation_id).final_quantity
            ) == D("0.4")
            with pytest.raises(ValueError, match="SIZING_MISMATCH"):
                owner.bind_execution_plan_v1(result.reservation.reservation_id, _envelope(1))
    finally:
        owner.close()


def _changed(request, kind):
    item = request.data.instruments[0]
    if kind == "tail":
        return replace(request, policy=replace(request.policy, left_tail_probability=D("0.99")))
    if kind == "period":
        item = replace(item, return_period_ms=86400000)
    if kind == "future":
        item = replace(
            item, returns=(*item.returns[:-1], replace(item.returns[-1], known_ms=MS + 1))
        )
    if kind == "nan":
        item = replace(
            item, returns=(replace(item.returns[0], simple_return=D("NaN")), *item.returns[1:])
        )
    if kind == "inf":
        item = replace(item, price=D("Infinity"))
    if kind == "missing-adv":
        item = replace(item, adv_quote_notional=None)
    if kind == "stale-depth":
        item = replace(item, book_event_ms=MS - 10000, book_known_ms=MS - 10000)
    if kind == "unit":
        item = replace(item, quantity_unit="BASE_ASSET")
    if kind == "inverse":
        item = replace(item, contract_kind="INVERSE")
    if kind == "fx":
        item = replace(item, quote_to_capital=D(2))
    if kind == "unordered":
        item = replace(item, returns=tuple(reversed(item.returns)))
    if kind == "gap":
        item = replace(item, returns=item.returns[:-1])
    if kind == "mean-vol-spike":
        return replace(request, policy=replace(request.policy, stress_statistic="MEAN_LOSS"))
    if kind == "account":
        return replace(request, data=replace(request.data, account="foreign"))
    if kind == "native":
        return replace(request, native_id="FOREIGN-USDC-SWAP")
    if kind == "epoch":
        return replace(request, instrument_epoch="f" * 64)
    if kind == "clock":
        return replace(request, data=replace(request.data, as_of_ms=MS + 1))
    return replace(request, data=replace(request.data, instruments=(item,)))


@pytest.mark.parametrize(
    "kind",
    [
        "tail",
        "period",
        "future",
        "nan",
        "inf",
        "missing-adv",
        "stale-depth",
        "unit",
        "inverse",
        "fx",
        "unordered",
        "mean-vol-spike",
        "account",
        "native",
        "epoch",
        "clock",
    ],
)
def test_invalid_required_input_cannot_create_hold(tmp_path, kind):
    owner = _owner(tmp_path)
    try:
        _auto(owner, tmp_path)
        result = _admit(owner, _changed(_request(), kind))
        assert result.disposition is ReserveDispositionV1.FAIL_CLOSED, result.reason_codes
        assert owner.active_sum_v1() == 0 and owner.stored_reservation_count_v1() == 0
    finally:
        owner.close()


@pytest.mark.parametrize(
    "factor,field",
    [
        ("10", "maximum_stress_loss_fraction"),
        ("1", "maximum_spread_bps"),
        ("0.00001", "maximum_adv_participation"),
    ],
)
def test_other_numerical_limits_also_veto_before_reservation(tmp_path, factor, field):
    owner = _owner(tmp_path)
    try:
        _auto(owner, tmp_path)
        request = _request()
        if field == "maximum_stress_loss_fraction":
            policy = replace(
                request.policy, stress_magnitude=D(factor), maximum_stress_loss_fraction=D("0.05")
            )
        else:
            policy = replace(request.policy, **{field: D(factor)})
        result = _admit(owner, replace(request, policy=policy))
        assert result.disposition is ReserveDispositionV1.FAIL_CLOSED, result.reason_codes
        assert owner.active_sum_v1() == 0
    finally:
        owner.close()


def test_changed_owner_generation_between_model_and_reserve_blocks_new_hold(tmp_path, monkeypatch):
    owner = _owner(tmp_path)
    try:
        _auto(owner, tmp_path)
        original = owner.try_reserve_v1

        def race(**kw):
            other = original(
                slot_id="LANE_1",
                decision_id="other-decision",
                cycle_id="other-cycle",
                observation_id=owner.budget_state_v1().observation_id,
                amount=D(10),
            )
            assert other.disposition is ReserveDispositionV1.ADMITTED
            return original(**kw)

        monkeypatch.setattr(owner, "try_reserve_v1", race)
        result = _admit(owner, _request())
        assert result.reason_codes[0] == "RISK_PORTFOLIO_GENERATION_CHANGED"
        assert owner.active_sum_v1() == 10 and owner.stored_reservation_count_v1() == 1
    finally:
        owner.close()


def test_risk_receipt_and_original_quantity_survive_owner_reopen_without_upgrade(tmp_path):
    owner = _owner(tmp_path)
    request = _request()
    try:
        _auto(owner, tmp_path)
        first = _admit(owner, request)
        rid = first.reservation.reservation_id
        receipt = owner.reservation_risk_binding_v1(rid).to_dict_v1()
    finally:
        owner.close()
    owner = _owner(tmp_path, "recover")
    try:
        assert owner.active_sum_v1() == 100 and owner.budget_state_v1().recovery_required
        assert _admit(owner, request).disposition is ReserveDispositionV1.FAIL_CLOSED
        _auto(owner, tmp_path)
        result = _admit(owner, request)
        assert result.disposition is ReserveDispositionV1.IDEMPOTENT_REPLAY, result.reason_codes
        assert result.sizing_decision.final_quantity == 1
        assert owner.reservation_risk_binding_v1(rid).to_dict_v1() == receipt
        assert (
            _admit(
                owner, replace(request, policy=replace(request.policy, policy_id="new-policy"))
            ).disposition
            is ReserveDispositionV1.FAIL_CLOSED
        )
        assert (
            owner.replay_sized_reservation_v1(rid, request=_sizing_input()).disposition
            is ReserveDispositionV1.FAIL_CLOSED
        )
        owner.bind_execution_plan_v1(rid, _envelope(1))
        assert owner.active_sum_v1() == 100 and owner.stored_reservation_count_v1() == 1
    finally:
        owner.close()


def test_horizon_aggregation_and_hedge_are_not_monotone_quantity_assumptions(tmp_path):
    owner = _owner(tmp_path)
    try:
        _auto(owner, tmp_path)
        request = _request()
        item = request.data.instruments[0]
        item = replace(
            item,
            returns=tuple(
                replace(row, simple_return=D("-0.01") if i % 4 < 2 else D("0.01"))
                for i, row in enumerate(item.returns)
            ),
        )
        request = replace(
            request,
            policy=replace(
                request.policy, horizon_ms=120000, maximum_var_loss_fraction=D("0.00015")
            ),
            data=replace(
                request.data,
                positions=(PositionRiskInputV1(BOUND.instrument_id, D(-2), ()),),
                instruments=(item,),
            ),
        )
        large = evaluate_offline_risk_v1(
            request, quantity=D(2), owner_snapshot=owner.risk_snapshot_v1()
        )
        small = evaluate_offline_risk_v1(
            request, quantity=D("0.1"), owner_snapshot=owner.risk_snapshot_v1()
        )
        assert large["horizon_samples"] == 4 and large["after"]["var_loss_fraction"] == "0.0"
        assert D(small["after"]["var_loss_fraction"]) > D(large["after"]["var_loss_fraction"])
        assert small["signed_before_contracts"][BOUND.instrument_id] == "-2"
        # This is a model-only hedge control; original opposite-position/MaxPos
        # entry gates are not overridden or granted admission here.
    finally:
        owner.close()


@pytest.mark.parametrize(
    "order_type,limit,depth,slip_limit,allowed",
    [
        ("market", None, True, D(100), True),
        ("market", None, True, D("0.01"), False),
        ("market", None, False, D(100), False),
        ("limit", D("99"), True, D(100), False),
        ("limit", D("101"), True, D(100), True),
    ],
)
def test_order_type_book_walk_and_partial_depth_have_actual_veto(
    tmp_path, order_type, limit, depth, slip_limit, allowed
):
    owner = _owner(tmp_path)
    try:
        _auto(owner, tmp_path)
        request = _request()
        item = replace(
            request.data.instruments[0],
            asks=(BookLevelV1(D("100.01"), D("0.5")), BookLevelV1(D("100.10"), D("0.6")))
            if depth
            else (BookLevelV1(D("100.01"), D("0.1")),),
        )
        request = replace(
            request,
            order_type=order_type,
            limit_price_quote=limit,
            data=replace(request.data, instruments=(item,)),
            policy=replace(request.policy, maximum_slippage_bps=slip_limit),
        )
        result = _admit(owner, request)
        assert (result.disposition is ReserveDispositionV1.ADMITTED) is allowed, result.reason_codes
        assert owner.stored_reservation_count_v1() == int(allowed)
    finally:
        owner.close()


def test_underlying_shock_has_correct_sign_for_short_exposure(tmp_path):
    owner = _owner(tmp_path)
    try:
        _auto(owner, tmp_path)
        request = _request()
        request = replace(
            request,
            policy=replace(
                request.policy,
                stress_kind="shock",
                stress_statistic="WORST_LOSS",
                stress_magnitude=D("-0.1"),
            ),
        )
        long = evaluate_offline_risk_v1(
            request, quantity=D(1), owner_snapshot=owner.risk_snapshot_v1()
        )
        short = evaluate_offline_risk_v1(
            replace(request, side="SHORT"), quantity=D(1), owner_snapshot=owner.risk_snapshot_v1()
        )
        assert D(long["after"]["stress_loss_fraction"]) > D(short["after"]["stress_loss_fraction"])
    finally:
        owner.close()


def test_shared_model_inputs_route_five_lanes_keep_holds_across_observation_refresh(tmp_path):
    from tests.ops.test_durable_portfolio_budget_recovery_v1 import _produce
    from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
        PortfolioCapitalReservationBudgetOwnerV1,
    )
    from src.ops.portfolio_capital_reservation_budget_v1.recovery_v1 import lane_bindings_v1

    base = _request(cap=D("0.1"))
    bindings = {
        f"LANE_{i}": replace(BOUND, instrument_id=f"coin-{i}", venue_native_id=f"COIN{i}-USDC-SWAP")
        for i in range(1, 6)
    }
    closure = lane_bindings_v1(bindings)
    owner = PortfolioCapitalReservationBudgetOwnerV1(
        durable_root=tmp_path / "budget",
        durable_account_identity=ACCOUNT,
        durable_mode="create",
        durable_lane_bindings=bindings,
    )
    items = tuple(
        replace(
            base.data.instruments[0],
            canonical_id=row["bound"]["instrument_id"],
            native_id=row["bound"]["venue_native_id"],
            instrument_epoch=row["instrument_epoch"],
        )
        for row in closure.values()
    )
    try:
        _auto(owner, tmp_path, bindings=bindings)
        for slot, row in closure.items():
            request = replace(
                base,
                slot_id=slot,
                canonical_id=row["bound"]["instrument_id"],
                native_id=row["bound"]["venue_native_id"],
                instrument_epoch=row["instrument_epoch"],
                decision_id="decision:" + slot,
                data=replace(base.data, instruments=items),
            )
            sizing = _sizing_input(
                decision_id=request.decision_id,
                instrument_id=request.canonical_id,
                instrument=replace(_sizing_input().instrument, instrument_id=request.canonical_id),
            )
            result = admit_sized_slot_reservation_v1(
                owner,
                observation=_obs(epoch=EPOCH),
                p01=_p01(EPOCH),
                eligibility=_eligibility(EPOCH),
                slot_id=slot,
                decision_id=request.decision_id,
                cycle_id=request.cycle_id,
                instrument_id=request.canonical_id,
                account_identity=ACCOUNT,
                sizing_input=sizing,
                fresh_pretrade_get_status=TRUSTED,
                live_account_bound_status=ACCOUNT_BOUND,
                fresh_evidence_fetched=True,
                fresh_evidence_validated=True,
                restrictive_risk=request,
            )
            assert result.disposition is ReserveDispositionV1.ADMITTED, result.reason_codes
        assert owner.active_sum_v1() == 50 and owner.stored_reservation_count_v1() == 5
        assert (
            owner.bind_canonical_producer_output_v1(
                _produce(epoch="2026-11-03T12:00:01Z")
            ).disposition
            is ReserveDispositionV1.ADMITTED
        )
        assert owner.active_sum_v1() == 50
        assert (
            owner.bind_canonical_producer_output_v1(
                _produce(value="40", epoch="2026-11-03T12:00:02Z")
            ).disposition
            is ReserveDispositionV1.FAIL_CLOSED
        )
        assert owner.active_sum_v1() == 50 and owner.budget_state_v1().recovery_required
    finally:
        owner.close()
