"""Original financial consumers with explicit offline X-Perp observations.

No live execution, account-custody completeness or market-price claim. Public
instrument identity and private settlement are different source roles. The
native Core produces each side for the same bound FUTURES instrument.
"""

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from fractions import Fraction
import json

import pytest

from src.ops.full_core_live_path_composition_root_v1.current_productive_enter_live_29p_join_v1 import (
    CurrentProductiveEnterLive29PPortfolioSlotContextV1 as Slot,
    join_current_productive_enter_live_29p_before_venue_plan_v1 as join,
)
from src.ops.portfolio_capital_reservation_budget_v1 import entry_execution_cost_v1 as cost
from src.ops.portfolio_capital_reservation_budget_v1 import native_initial_margin_v1 as margin
from src.ops.portfolio_capital_reservation_budget_v1 import absolute_movement_cost_v1 as movement
from src.ops.portfolio_capital_reservation_budget_v1.host_v1 import PortfolioBudgetHostV1
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    REUSED_BINDING_ACCOUNT_SCOPE as ACCOUNT,
)
from tests.ops._current_productive_natural_mv2_dp_enter_fixture_v1 import (
    run_natural_enter_long_sequence_for_bound_v1,
    run_natural_enter_short_sequence_for_bound_v1,
)
from tests.ops.test_full_core_current_productive_oneshot_sidestate_confirmation_cursor_join_v1 import (
    _bound,
    _produced_g17_producer,
)
from tests.ops.test_full_core_current_productive_enter_live_29p_join_v1 import (
    EPOCH,
    _injected,
    _balance_payload,
)
from tests.ops.test_absolute_movement_cost_admission_v1 import raw_input, ROOT
from tests.ops.test_closing_execution_cost_provision_v1 import no_network as no_network
from tests.ops.test_portfolio_budget_host_v1 import _fetch
from src.ops.portfolio_capital_reservation_budget_v1.test_phase_limits_v1 import (
    load_slot_entry_budget_v1,
)

NATIVE = "BTC-USD_UM_XPERP-310404"
FAMILY = "BTC-USD_UM_XPERP"


def position_tiers(asset="BTC"):
    return [
        dict(
            instFamily=f"{asset}-USD_UM_XPERP",
            instId="",
            uly=f"{asset}-USD",
            tier="1",
            minSz="0",
            maxSz="1",
            mmr="0.0065",
        ),
        dict(
            instFamily=f"{asset}-USD_UM_XPERP",
            instId="",
            uly=f"{asset}-USD",
            tier="2",
            minSz="2",
            maxSz="45000",
            mmr="0.01",
        ),
    ]


def instrument(*, settlement="USDC", asset="BTC"):
    family = f"{asset}-USD_UM_XPERP"
    return dict(
        instId=f"{family}-310404",
        instType="FUTURES",
        state="live",
        uly=f"{asset}-USD",
        instFamily=family,
        baseCcy="",
        quoteCcy="",
        settleCcy=settlement,
        ctVal="0.0001",
        ctMult="1",
        ctValCcy=asset,
        ctType="linear",
        tickSz="0.1",
        lotSz="1",
        minSz="1",
        expTime="1933056000000",
        groupId="7",
        maxMktSz="1000000",
        maxLmtSz="1000000",
        upcChg=[],
    )


def policy():
    return load_slot_entry_budget_v1(
        ROOT / "docs/ops/specs/BOUNDED_MULTISLOT_TEST_ENTRY_BUDGET_V11.json"
    )


def xperp_bound(asset):
    from tests.ops.test_governed_futures_universe_producer_v1 import _produce

    public = instrument(settlement="USD", asset=asset)
    native = public["instId"]
    universe = _produce([public], marks=[native])
    (eligible,) = universe.snapshot.instruments
    return replace(_bound(instrument_id=eligible.canonical_instrument_id), venue_native_id=native)


def prepare(
    tmp_path,
    monkeypatch,
    *,
    short=False,
    fault=None,
    scoped_reconciliation=False,
    tier_evidence=False,
    tier_fault=None,
    liquidation_policy=False,
    asset="BTC",
    slot="LANE_1",
    host_context=None,
    extra_bindings=None,
):
    clock = [EPOCH]
    monkeypatch.setattr(cost, "utc_now_iso_v1", lambda: clock[0])
    # Canonical identity follows the public instrument, not its account's cash
    # preference. Derive it through the original universe producer below.
    bound = xperp_bound(asset)
    native = bound.venue_native_id
    family = native.rsplit("-", 1)[0]
    tier_endpoint = (
        f"/api/v5/public/position-tiers?instType=FUTURES&tdMode=cross&instFamily={family}"
    )
    producer = _produced_g17_producer(instrument_id=bound.instrument_id, venue_native_id=native)
    run = (
        run_natural_enter_short_sequence_for_bound_v1
        if short
        else run_natural_enter_long_sequence_for_bound_v1
    )(bound=bound, g17_typed_vol_producer=producer)
    cycle = run[3] if short else run[2]
    if host_context is None:
        entry_policy = (
            load_slot_entry_budget_v1(
                ROOT / "docs/ops/specs/BOUNDED_MULTISLOT_TEST_ENTRY_BUDGET_V12.json"
            )
            if liquidation_policy
            else policy()
        )
        host = PortfolioBudgetHostV1(
            root=tmp_path / "host",
            private_rest_fetch=_fetch(uid=ACCOUNT),
            repository_sha="explicit-offline-usdc-financial-test",
            session_id="usdc-financial-test",
            expected_account_identity=ACCOUNT,
            durable_mode="create",
            clock=lambda: datetime.fromisoformat(EPOCH.replace("Z", "+00:00")).timestamp(),
            execution_environment="LIVE"
            if scoped_reconciliation
            else "INTERNAL_SIMULATED_EXECUTION",
            entry_budget_policy=None if scoped_reconciliation else entry_policy,
        )
        context = host.observe_v1({slot: bound, **(extra_bindings or {})})
    else:
        host, context = host_context
    payload = _balance_payload(avail_eq="1000")
    row = instrument(asset=asset)
    if fault == "wrong-underlying":
        row["uly"] = "ETH-USD"
    elif fault == "wrong-contract-unit":
        row["ctValCcy"] = "ETH"
    elif fault == "wrong-base":
        row["baseCcy"] = "ETH"
    elif fault == "invented-usdc-quote":
        row["quoteCcy"] = "USDC"
    injected = replace(
        _injected(payload=payload, instruments_payload=dict(code="0", data=[row])),
        index_tickers_payload=None,
        conversion_pair_instruments_payload=None,
    )
    kwargs = dict(
        replay=cycle.replay,
        bound_instrument=bound,
        decision_epoch=EPOCH,
        injected=injected,
        portfolio_budget_owner=host.owner,
        portfolio_slot=Slot(
            slot, cycle.replay.evidence.decision_id, f"usdc-financial-entry-{slot}"
        ),
        host_budget_recovery=context,
    )
    now_ms = int(datetime.fromisoformat(EPOCH.replace("Z", "+00:00")).timestamp() * 1000)
    acquisition = cost.canonical(
        dict(decision_epoch=EPOCH, cycle_id=kwargs["portfolio_slot"].cycle_id)
    )

    def source(endpoint, payload, private=False):
        return cost.FreshPretradeGetTransportResultV1(
            True,
            "GET",
            endpoint,
            200,
            payload,
            private,
            "EXPLICIT_SYNTHETIC_USDC_FINANCIAL_SOURCE",
            False,
            False,
            "",
            cost.digest(payload),
            pretrade_decision_id=acquisition,
            acquired_at_utc=EPOCH,
        )

    account = dict(
        uid=ACCOUNT,
        acctLv="2",
        posMode="net_mode",
        settleCcy="USDC",
        settleCcyList=["USDC", "USD", "USDG"],
        autoLoan=False,
    )
    if fault == "other-settlement":
        account["settleCcy"] = "USD"
    elif fault == "settlement-not-enabled":
        account["settleCcyList"] = ["USD"]
    elif fault == "auto-loan":
        account["autoLoan"] = True
    elif fault == "other-mode":
        account["acctLv"] = "3"
    mark = Decimal(str(cycle.replay.intermediate.market_context.mark_price))
    rows = {
        "/api/v5/account/config": source(
            "/api/v5/account/config", dict(code="0", data=[account]), True
        ),
        f"/api/v5/account/instruments?instType=FUTURES&instId={native}": source(
            f"/api/v5/account/instruments?instType=FUTURES&instId={native}",
            dict(code="0", data=[row]),
            True,
        ),
        f"/api/v5/account/trade-fee?instType=FUTURES&instFamily={family}": source(
            f"/api/v5/account/trade-fee?instType=FUTURES&instFamily={family}",
            dict(
                code="0",
                data=[
                    dict(
                        instType="FUTURES",
                        ts=str(now_ms),
                        feeGroup=[dict(groupId="7", maker="0.0002", taker="-0.0005")],
                    )
                ],
            ),
            True,
        ),
        f"/api/v5/market/books?instId={native}&sz=20": source(
            f"/api/v5/market/books?instId={native}&sz=20",
            dict(
                code="0",
                data=[
                    dict(
                        ts=str(now_ms),
                        bids=[[str(mark - Decimal("0.1")), "1000000", "0", "1"]],
                        asks=[[str(mark + Decimal("0.1")), "1000000", "0", "1"]],
                    )
                ],
            ),
        ),
    }
    if fault in {"unauthenticated-instrument", "public-instrument-label", "public-usd-row"}:
        endpoint = f"/api/v5/account/instruments?instType=FUTURES&instId={native}"
        original = rows[endpoint]
        if fault == "unauthenticated-instrument":
            rows[endpoint] = replace(original, auth_header_sent=False)
        elif fault == "public-instrument-label":
            rows[endpoint] = replace(
                original, endpoint=original.endpoint.replace("/account/", "/public/")
            )
        else:
            public = dict(code="0", data=[instrument(settlement="USD", asset=asset)])
            rows[endpoint] = replace(original, payload=public, body_sha256=cost.digest(public))

    class Port:
        def __init__(self):
            self.calls = []

        def get(self, *, endpoint, auth_required, pretrade_decision_id, get_cache_policy):
            self.calls.append((endpoint, auth_required))
            assert (
                pretrade_decision_id == acquisition
                and get_cache_policy == "DYNAMIC_REFRESH_REQUIRED"
            )
            return rows[endpoint]

    port = Port()
    opening = cost.collect_entry_execution_cost_observation_v1(
        transport=port,
        account_identity=ACCOUNT,
        bound_instrument=bound,
        inst_type="FUTURES",
        decision_epoch=EPOCH,
        cycle_id=kwargs["portfolio_slot"].cycle_id,
        use_account_instruments=True,
    )
    assert port.calls[1] == (f"/api/v5/account/instruments?instType=FUTURES&instId={native}", True)
    balance = source("/api/v5/account/balance", payload, True)
    leverage = source(
        f"/api/v5/account/leverage-info?instId={native}&mgnMode=cross",
        dict(code="0", data=[dict(instId=native, mgnMode="cross", posSide="net", lever="3")]),
        True,
    )
    rows[leverage.endpoint] = leverage
    if tier_evidence:
        tiers = position_tiers(asset)
        if tier_fault == "foreign-family":
            tiers[1]["instFamily"] = "ETH-USD_UM_XPERP"
        elif tier_fault == "instrument-specific":
            tiers[1]["instId"] = native
        elif tier_fault == "ambiguous":
            tiers[0]["maxSz"] = tiers[1]["maxSz"]
        elif tier_fault == "out-of-range":
            tiers.pop()
        elif tier_fault == "invalid-rate":
            tiers[1]["mmr"] = "NaN"
        payload_tiers = dict(code="0", data=tiers)
        if tier_fault == "continuation":
            payload_tiers["cursor"] = "opaque-next-page"
        observed_tiers = source(tier_endpoint, payload_tiers)
        acquired = datetime.fromisoformat(EPOCH.replace("Z", "+00:00"))
        changes = {
            "decision": dict(pretrade_decision_id="foreign-decision"),
            "wrong-query": dict(endpoint=tier_endpoint + "&tier=1"),
            "private": dict(auth_header_sent=True),
            "historical": dict(historical_reuse=True),
            "stale": dict(acquired_at_utc=(acquired - timedelta(seconds=6)).isoformat()),
            "future": dict(acquired_at_utc=(acquired + timedelta(seconds=1)).isoformat()),
        }
        rows[tier_endpoint] = replace(
            observed_tiers,
            acquired_at_utc=(acquired - timedelta(seconds=5)).isoformat(),
        )
        if tier_fault in changes:
            rows[tier_endpoint] = replace(rows[tier_endpoint], **changes[tier_fault])
    margin_observation = margin.collect_native_initial_margin_observation_v1(
        transport=port,
        balance_source=balance,
        opening_observation=opening,
        include_xperp_position_tiers=tier_evidence,
    )
    assert port.calls[4:] == [(leverage.endpoint, True)] + (
        [(tier_endpoint, False)] if tier_evidence else []
    )
    funding = source(
        f"/api/v5/public/funding-rate?instId={native}",
        dict(
            code="0",
            data=[
                dict(
                    instId=native,
                    instType="FUTURES",
                    method="current_period",
                    settState="settled",
                    ts=str(now_ms),
                    fundingRate="0.0001",
                    minFundingRate="-0.00375",
                    maxFundingRate="0.00375",
                    fundingTime=str(now_ms + 3600000),
                    nextFundingTime=str(now_ms + 7200000),
                )
            ],
        ),
    )
    kwargs["injected"] = replace(
        injected,
        opening_cost_observation=opening,
        native_initial_margin_observation=margin_observation,
        funding_cost_observation=cost.FundingCostObservationV1.capture_v1(
            bound_instrument=bound,
            decision_epoch=EPOCH,
            cycle_id=kwargs["portfolio_slot"].cycle_id,
            source=funding,
            evaluated_at_utc=EPOCH,
        ),
        absolute_movement_cost_observation=movement.AbsoluteMovementCostObservationV1.capture_v1(
            instrument_raw_input=raw_input(kwargs),
            opening_observation=opening,
            evaluated_at_utc=EPOCH,
        ),
    )
    return host, kwargs, clock


@pytest.mark.parametrize("short", [False, True])
@pytest.mark.parametrize("tier_evidence", [False, True])
def test_usdc_xperp_original_core_quantity_hold_and_cold_read(
    tmp_path, monkeypatch, short, tier_evidence
):
    host, kwargs, clock = prepare(tmp_path, monkeypatch, short=short, tier_evidence=tier_evidence)
    try:
        admitted = join(**kwargs)
        assert admitted.status == "PASS", admitted.reason_codes
        (binding,) = host.owner._sizing_bindings.values()
        receipt = json.loads(binding.native_initial_margin_binding.receipt_json)
        assert receipt["settlement_currency"] == "USDC"
        assert receipt["side"] == ("SHORT" if short else "LONG")
        assert binding.monetary_source.index_tickers_json == "null"
        assert binding.monetary_source.conversion_pair_instruments_json == "null"
        required = Fraction(
            int(receipt["notional_numerator"]), int(receipt["notional_denominator"])
        )
        price = Decimal(binding.monetary_source.native_reference_price)
        conservative_price = price if short else price + Decimal("0.1")
        assert required == Fraction(binding.decision.final_quantity) * Fraction(
            "0.0001"
        ) * Fraction(conservative_price)
        assert receipt["liquidation_cover_proven"] is False
        if tier_evidence:
            position_maintenance = receipt["xperp_position_maintenance"]
            expected = (
                Fraction(binding.decision.final_quantity)
                * Fraction("0.0001")
                * Fraction(price)
                * Fraction("0.01")
            )
            assert position_maintenance["instrument_family"] == FAMILY
            assert position_maintenance["settlement_currency"] == "USDC"
            assert position_maintenance["tier"] == "2"
            assert position_maintenance["account_effective_maintenance_proven"] is False
            assert (
                Fraction(
                    int(position_maintenance["required_numerator"]),
                    int(position_maintenance["required_denominator"]),
                )
                == expected
            )
            _check_late_xperp_maintenance_source(host, admitted, kwargs["bound_instrument"], clock)
        else:
            assert "xperp_position_maintenance" not in receipt
        before = host.owner.active_sum_v1()
        assert 0 < before <= 25
        owner_path = host.owner.durable_scope_identity_v1()["root"]
        host.close()
        from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
            PortfolioCapitalReservationBudgetOwnerV1,
        )

        cold = PortfolioCapitalReservationBudgetOwnerV1(
            durable_root=owner_path,
            durable_account_identity=ACCOUNT,
            durable_mode="recover",
            durable_lane_bindings={"LANE_1": kwargs["bound_instrument"]},
            entry_budget_policy=policy(),
        )
        try:
            assert cold.active_sum_v1() == before
            assert cold.budget_state_v1().recovery_required and not cold.budget_state_v1().admitted
            (rebound,) = cold._sizing_bindings.values()
            assert rebound == binding
            clock[0] = "2026-09-17T06:50:06Z"
            with pytest.raises(ValueError):
                rebound.native_initial_margin_binding.validate_v1(
                    entry_binding=rebound.entry_cost_binding,
                    monetary_source=rebound.monetary_source,
                    applied_input=rebound.applied_input,
                    decision=rebound.decision,
                    evaluated_at_utc=clock[0],
                )
            assert cold.active_sum_v1() == before
        finally:
            cold.close()
    finally:
        host.close()


def _check_late_xperp_maintenance_source(host, entry, bound, clock):
    from src.ops.full_core_live_path_composition_root_v1.current_productive_venue_plan_v1 import (
        try_bind_current_productive_venue_plan_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
        bind_final_order_envelope_from_venue_plan_v1,
    )

    session = "usdc-financial-test"
    status, reasons, plan = try_bind_current_productive_venue_plan_v1(
        replay=entry.replay,
        bound_instrument=bound,
        session_id=session,
        run_id=session,
        composed_epoch=EPOCH,
        execution_mode="INTERNAL_SIMULATED_EXECUTION",
    )
    assert status.value == "PASS", reasons
    envelope = bind_final_order_envelope_from_venue_plan_v1(
        plan, admission_ref=session, provenance_ref=session, creation_epoch=EPOCH
    )
    rid = entry.portfolio_reservation_id
    owner = host.owner
    owner.commit_internal_pre_external_effect_v1(rid)
    owner.bind_execution_plan_v1(
        rid,
        envelope,
        canonical_intent=entry.replay.intermediate.canonical_order_intent,
        venue_plan=plan,
    )
    owner.inspect_current_entry_budget_policy_v1(rid, envelope)
    before = owner.budget_state_v1(), owner._store.sequence
    clock[0] = (
        datetime.fromisoformat(EPOCH.replace("Z", "+00:00")) + timedelta(seconds=1)
    ).isoformat()
    try:
        # The tier read alone has crossed the original acquisition window.
        with pytest.raises(ValueError, match="ACQUISITION_STALE"):
            owner.inspect_current_entry_budget_policy_v1(rid, envelope)
    finally:
        clock[0] = EPOCH
    assert before == (owner.budget_state_v1(), owner._store.sequence)


@pytest.mark.parametrize(
    "fault,reason",
    [
        ("foreign-family", "XPERP_MAINTENANCE_TIER_FAMILY_SCOPE_MISMATCH"),
        ("instrument-specific", "XPERP_MAINTENANCE_TIER_FAMILY_SCOPE_MISMATCH"),
        ("ambiguous", "XPERP_MAINTENANCE_QUANTITY_TIER_NOT_UNIQUE"),
        ("out-of-range", "XPERP_MAINTENANCE_QUANTITY_TIER_NOT_UNIQUE"),
        ("invalid-rate", "XPERP_MAINTENANCE_TIER_DECIMAL_INVALID"),
        ("continuation", "XPERP_MAINTENANCE_TIER_RESPONSE_SCOPE_UNPROVEN"),
        ("wrong-query", "XPERP_MAINTENANCE_TIER_QUERY_MISMATCH"),
        ("private", "XPERP_MAINTENANCE_FRESH_BOUND_PUBLIC_GET_REQUIRED"),
        ("historical", "XPERP_MAINTENANCE_FRESH_BOUND_PUBLIC_GET_REQUIRED"),
        ("decision", "XPERP_MAINTENANCE_FRESH_BOUND_PUBLIC_GET_REQUIRED"),
        ("stale", "ACQUISITION_STALE"),
        ("future", "ACQUISITION_TIME_IN_FUTURE"),
    ],
)
def test_invalid_tier_source_cannot_enter_original_budget(tmp_path, monkeypatch, fault, reason):
    host, kwargs, _ = prepare(tmp_path, monkeypatch, tier_evidence=True, tier_fault=fault)
    try:
        result = join(**kwargs)
        assert result.status != "PASS"
        assert reason in result.reason_codes
        assert host.owner.active_sum_v1() == 0
        assert host.owner.stored_reservation_count_v1() == 0
    finally:
        host.close()


def test_cold_budget_rejects_changed_maintenance_component_with_valid_checksums(
    tmp_path, monkeypatch
):
    from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
        PortfolioCapitalBudgetError,
        PortfolioCapitalReservationBudgetOwnerV1 as Owner,
    )
    from src.ops.portfolio_capital_reservation_budget_v1.durable_store_v1 import (
        DurableBudgetStoreV1,
    )

    host, kwargs, _ = prepare(tmp_path, monkeypatch, tier_evidence=True)
    try:
        result = join(**kwargs)
        assert result.status == "PASS", result.reason_codes
        state = host.owner._store.load()
        (binding,) = state["sizing_bindings"].values()
        receipt = binding["native_initial_margin_binding"]["receipt"]
        receipt["xperp_position_maintenance"]["required_numerator"] = "0"
        receipt["digest"] = cost.digest({k: v for k, v in receipt.items() if k != "digest"})
    finally:
        host.close()

    root = tmp_path / "rehashed-tier"
    store = DurableBudgetStoreV1(root, account_identity=ACCOUNT, mode="create")
    try:
        store.save(state)
    finally:
        store.close()
    with pytest.raises(PortfolioCapitalBudgetError, match="SEMANTIC_RESTORE_UNPROVEN") as error:
        Owner(
            durable_root=root,
            durable_account_identity=ACCOUNT,
            durable_mode="recover",
            durable_lane_bindings={"LANE_1": kwargs["bound_instrument"]},
            entry_budget_policy=policy(),
        )
    assert "NATIVE_INITIAL_MARGIN_RECEIPT_SOURCE_OR_QUANTITY_MISMATCH" in str(error.value.__cause__)


@pytest.mark.parametrize(
    "fault",
    [
        "other-settlement",
        "settlement-not-enabled",
        "auto-loan",
        "other-mode",
        "unauthenticated-instrument",
        "public-instrument-label",
        "public-usd-row",
        "wrong-underlying",
        "wrong-contract-unit",
        "wrong-base",
        "invented-usdc-quote",
    ],
)
def test_unproven_account_settlement_rejects_actual_financial_entry_without_hold(
    tmp_path, monkeypatch, fault
):
    host, kwargs, _ = prepare(tmp_path, monkeypatch, fault=fault)
    try:
        result = join(**kwargs)
        assert result.status != "PASS", result.reason_codes
        assert host.owner.active_sum_v1() == 0
        assert host.owner.stored_reservation_count_v1() == 0
    finally:
        host.close()


def test_usdt_hold_cannot_be_reclassified_as_usdc_even_with_rehashed_storage(tmp_path, monkeypatch):
    from tests.ops import test_absolute_movement_cost_admission_v1 as compatibility
    from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
        PortfolioCapitalReservationBudgetOwnerV1 as Owner,
        PortfolioCapitalBudgetError,
    )
    from src.ops.portfolio_capital_reservation_budget_v1.durable_store_v1 import (
        DurableBudgetStoreV1,
    )

    with monkeypatch.context() as scoped:
        captures, _ = compatibility.setup(scoped)
        compatibility.cover.native._run_layered_entry_supervisor_v1(
            tmp_path / "old-usdt", short=False
        )
        kwargs, admitted, snapshot = captures[0]
        assert admitted.status == "PASS", admitted.reason_codes
        owner = kwargs["portfolio_budget_owner"]
        (binding,) = owner._sizing_bindings.values()
        owner._entry_budget_policy = replace(
            owner._entry_budget_policy, require_usdc_settlement=True
        )
        with pytest.raises(ValueError, match="TEST_PHASE_USDC_SETTLEMENT_REQUIRED"):
            margin.require_native_margin_locked_v1(owner, binding)
        payload = snapshot["state"]
        payload["entry_budget_policy"]["require_usdc_settlement"] = True
        owner.close()

    # The history is structurally valid and checksummed by the real writer.
    # Semantic recovery must still reject a USD*T* obligation under USDC-only.
    root = tmp_path / "rehashed"
    store = DurableBudgetStoreV1(root, account_identity=payload["account_identity"], mode="create")
    store.save(payload)
    store.close()
    with pytest.raises(PortfolioCapitalBudgetError) as error:
        Owner(
            durable_root=root,
            durable_account_identity=payload["account_identity"],
            durable_mode="recover",
            durable_lane_bindings={"LANE_1": kwargs["bound_instrument"]},
        )
    assert "required USDC settlement missing on active hold" in str(error.value.__cause__)


@pytest.mark.parametrize(
    "canonical,native",
    [
        ("okx_eea:linear_dated_future:BTC:USDT:USD:btc-usd_um_xperp-310404", NATIVE),
        ("okx_eea:linear_dated_future:ETH:USD:USD:btc-usd_um_xperp-310404", NATIVE),
        ("okx_eea:linear_perpetual:BTC:USD:USD:btc-usd_um_xperp-310404", NATIVE),
        ("okx_eea:linear_dated_future:BTC:USD:USD:btc-usd_um_xperp-310405", NATIVE),
        ("opaque", "BTC-USD_UM_XPERP-WRONG"),
    ],
)
def test_xperp_quote_contract_and_exact_native_identity_remain_bound(canonical, native):
    from src.ops.full_core_live_path_composition_root_v1.current_productive_future_identity_semantics_v1 import (
        resolve_selected_future_market_type_v1,
    )

    with pytest.raises(ValueError):
        resolve_selected_future_market_type_v1(instrument_id=canonical, venue_native_id=native)


@pytest.mark.parametrize("short", [False, True])
@pytest.mark.parametrize("fault", [None, "position", "changed-balance", "missing-proof"])
def test_xperp_liquidation_projection_at_original_budget_boundaries(
    tmp_path, monkeypatch, short, fault
):
    from src.ops.full_core_live_path_composition_root_v1 import (
        productive_read_only_get_transport_v1 as wire,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_venue_plan_v1 import (
        try_bind_current_productive_venue_plan_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
        bind_final_order_envelope_from_venue_plan_v1,
    )
    from src.ops.okx_eea_private_account_state_runtime_v1.k1_source_v1 import (
        open_k1_account_observation_source_v1,
    )
    from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
        PortfolioCapitalReservationBudgetOwnerV1 as Owner,
    )
    from tests.ops.test_k1_account_observation_source_v1 import InjectedOpener, _FakeKeychainBackend

    host, kwargs, clock = prepare(
        tmp_path, monkeypatch, short=short, tier_evidence=True, liquidation_policy=True
    )
    bound = kwargs["bound_instrument"]
    opener = InjectedOpener(
        account=ACCOUNT,
        positions=[dict(instId=NATIVE, instType="FUTURES", posSide="net", pos="1")]
        if fault == "position"
        else [],
    )
    original = opener.fetch

    def fetch(path, params):
        payload = original(path, params)
        if path == "/api/v5/account/config":
            payload["data"][0].update(settleCcy="USDC", autoLoan=False)
        elif path == "/api/v5/account/balance":
            payload["data"][0]["details"] = [
                dict(
                    ccy="USDC",
                    availEq="999" if fault == "changed-balance" else "1000",
                    frozenBal="0",
                )
            ]
        return payload

    opener.fetch = fetch
    monkeypatch.setattr(wire, "utc_now_iso_v1", lambda: clock[0])
    monkeypatch.setattr(wire, "build_opener", lambda *handlers: opener)
    try:
        with open_k1_account_observation_source_v1(
            expected_account_identity=ACCOUNT,
            session_id="xperp-liquidation-injected",
            max_request_count=40,
            account_inventory_guard=True,
            inventory_inst_type="FUTURES",
            clock=host.clock,
            k1_lookup_backend=_FakeKeychainBackend(),
        ) as source:
            proof = host.capture_futures_financial_custody_v1(source)
            if fault != "missing-proof":
                kwargs["injected"] = replace(kwargs["injected"], futures_financial_custody=proof)
            result = join(**kwargs)
            if fault:
                expected = {
                    "position": "XPERP_LIQUIDATION_EXISTING_POSITION_UNPROVEN",
                    "changed-balance": "XPERP_LIQUIDATION_FLAT_CAPITAL_BASIS_UNPROVEN",
                    "missing-proof": "XPERP_LIQUIDATION_ORIGINAL_CUSTODY_REQUIRED",
                }
                assert result.status != "PASS"
                assert expected[fault] in result.reason_codes
                assert host.owner.stored_reservation_count_v1() == 0
                return
            assert result.status == "PASS", result.reason_codes
            rid = result.portfolio_reservation_id
            (sizing,) = host.owner._sizing_bindings.values()
            historical = json.loads(sizing.xperp_liquidation_binding.receipt_json)
            assert historical["quantity"] == str(sizing.decision.final_quantity)
            assert historical["side"] == ("SHORT" if short else "LONG")
            assert Fraction(historical["surplus_at_stop_usdc"]) > 0
            assert historical["runtime_authorization_effect"] == "NONE"
            if short:
                assert Fraction(historical["positive_boundary_price"]) > Fraction(
                    sizing.monetary_source.native_protective_stop_price
                )
            else:
                assert historical["positive_boundary_price"] is None

            session = host.session_id
            status, reasons, plan = try_bind_current_productive_venue_plan_v1(
                replay=result.replay,
                bound_instrument=bound,
                session_id=session,
                run_id=session,
                composed_epoch=EPOCH,
                execution_mode="INTERNAL_SIMULATED_EXECUTION",
            )
            assert status.value == "PASS", reasons
            envelope = bind_final_order_envelope_from_venue_plan_v1(
                plan, admission_ref=session, provenance_ref=session, creation_epoch=EPOCH
            )
            owner = host.owner
            owner.commit_internal_pre_external_effect_v1(rid)
            owner.bind_execution_plan_v1(
                rid,
                envelope,
                canonical_intent=result.replay.intermediate.canonical_order_intent,
                venue_plan=plan,
            )
            before = owner._store.sequence, owner.active_sum_v1()
            with pytest.raises(ValueError, match="LOCAL_COMMITMENT_GENERATION_OR_CONTENT_CHANGED"):
                owner.inspect_current_entry_budget_policy_v1(
                    rid, envelope, futures_financial_custody=proof
                )
            fresh = host.capture_futures_financial_custody_v1(source)
            late = owner.inspect_current_entry_budget_policy_v1(
                rid, envelope, futures_financial_custody=fresh
            )["xperp_liquidation_projection"]
            from src.ops.full_core_live_path_composition_root_v1.envelope_bound_external_effect_send_seam_v1 import (
                FullCoreEnvelopeBoundSendSeamError,
                inspect_original_portfolio_execution_context_v1,
            )

            late_args = dict(
                envelope=envelope,
                portfolio_budget_owner=owner,
                portfolio_reservation_id=rid,
                execution_plan_context=owner.execution_plan_context_v1(rid, envelope),
            )
            with pytest.raises(
                FullCoreEnvelopeBoundSendSeamError,
                match="XPERP_LIQUIDATION_ORIGINAL_CUSTODY_REQUIRED",
            ):
                inspect_original_portfolio_execution_context_v1(**late_args)
            assert (
                inspect_original_portfolio_execution_context_v1(
                    **late_args, futures_financial_custody=fresh
                )["account"]
                == ACCOUNT
            )
            assert late["surplus_at_stop_usdc"] == historical["surplus_at_stop_usdc"]
            assert late["custody_digest"] != historical["custody_digest"]
            assert before == (owner._store.sequence, owner.active_sum_v1())
            root = owner.durable_scope_identity_v1()["root"]
            selected_policy = owner.entry_budget_policy_v1()
            retained_state = owner.risk_snapshot_v1()["state"]
        host.close()
        cold = Owner(
            durable_root=root,
            durable_account_identity=ACCOUNT,
            durable_mode="recover",
            durable_lane_bindings={"LANE_1": bound},
            entry_budget_policy=selected_policy,
        )
        try:
            (restored,) = cold._sizing_bindings.values()
            assert restored.xperp_liquidation_binding == sizing.xperp_liquidation_binding
            assert cold.active_sum_v1() == before[1]
            assert cold.budget_state_v1().recovery_required
        finally:
            cold.close()
        if not short:
            from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
                PortfolioCapitalBudgetError,
            )
            from src.ops.portfolio_capital_reservation_budget_v1.durable_store_v1 import (
                DurableBudgetStoreV1,
            )

            receipt = retained_state["sizing_bindings"][rid]["xperp_liquidation_binding"]["receipt"]
            receipt["surplus_at_stop_usdc"] = "1000000"
            changed_root = tmp_path / "changed-liq-receipt"
            store = DurableBudgetStoreV1(changed_root, account_identity=ACCOUNT, mode="create")
            try:
                store.save(retained_state)
            finally:
                store.close()
            with pytest.raises(PortfolioCapitalBudgetError) as error:
                Owner(
                    durable_root=changed_root,
                    durable_account_identity=ACCOUNT,
                    durable_mode="recover",
                    durable_lane_bindings={"LANE_1": bound},
                    entry_budget_policy=selected_policy,
                )
            assert "XPERP_LIQUIDATION_RECEIPT_MISMATCH" in str(error.value.__cause__)
    finally:
        host.close()


@pytest.mark.parametrize(
    "fault", [None, "foreign-quantity", "stale-fee", "unknown-submit", "boundary-before-stop"]
)
def test_xperp_liquidation_projection_retains_and_stresses_reconciled_other_lane(
    tmp_path, monkeypatch, fault
):
    from src.ops.full_core_live_path_composition_root_v1 import (
        productive_read_only_get_transport_v1 as wire,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_venue_plan_v1 import (
        try_bind_current_productive_venue_plan_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
        bind_final_order_envelope_from_venue_plan_v1,
    )
    from src.ops.okx_eea_private_account_state_runtime_v1.k1_source_v1 import (
        open_k1_account_observation_source_v1,
    )
    from tests.ops.test_full_core_current_productive_envelope_bound_single_use_external_effect_send_seam_v1 import (
        _permit,
    )
    from tests.ops.test_k1_account_observation_source_v1 import InjectedOpener, _FakeKeychainBackend

    second = xperp_bound("ETH")
    host, first_args, clock = prepare(
        tmp_path,
        monkeypatch,
        tier_evidence=True,
        liquidation_policy=True,
        extra_bindings={"LANE_2": second},
    )
    opener = InjectedOpener(account=ACCOUNT, allow_public_position_tiers=True)
    original_fetch = opener.fetch
    positions = []
    submitted = {}
    now_ms = int(host.clock() * 1000)

    def fetch(path, params):
        if path == "/api/v5/account/instruments":
            assert params == {"instType": "FUTURES", "instId": NATIVE}
            return dict(code="0", data=[instrument()])
        if path == "/api/v5/account/trade-fee":
            assert params == {"instType": "FUTURES", "instFamily": FAMILY}
            timestamp = now_ms - 6000 if fault == "stale-fee" else now_ms
            return dict(
                code="0",
                data=[
                    dict(
                        instType="FUTURES",
                        ts=str(timestamp),
                        feeGroup=[dict(groupId="7", taker="-0.0005")],
                    )
                ],
            )
        if path == "/api/v5/public/position-tiers":
            assert params == {"instType": "FUTURES", "tdMode": "cross", "instFamily": FAMILY}
            return dict(code="0", data=position_tiers())
        if "instId" in params and submitted:
            assert params.get("instType", "FUTURES") == "FUTURES"
            if path.endswith(("/order", "/orders-history")):
                return dict(code="0", data=[submitted])
            if path.endswith("/fills"):
                return dict(
                    code="0",
                    data=[dict(submitted, tradeId="venue-fill", fillSz=submitted["accFillSz"])],
                )
        payload = original_fetch(path, params)
        if path == "/api/v5/account/config":
            payload["data"][0].update(settleCcy="USDC", settleCcyList=["USDC"], autoLoan=False)
        elif path == "/api/v5/account/balance":
            payload["data"][0]["details"] = [
                dict(ccy="USDC", availEq="1000", frozenBal="6" if positions else "0")
            ]
        elif path == "/api/v5/account/positions":
            payload["data"] = positions
        return payload

    opener.fetch = fetch
    monkeypatch.setattr(wire, "utc_now_iso_v1", lambda: clock[0])
    monkeypatch.setattr(wire, "build_opener", lambda *handlers: opener)
    try:
        with open_k1_account_observation_source_v1(
            expected_account_identity=ACCOUNT,
            session_id="two-lane-liquidation-injected",
            max_request_count=75,
            account_inventory_guard=True,
            inventory_inst_type="FUTURES",
            clock=host.clock,
            k1_lookup_backend=_FakeKeychainBackend(),
        ) as source:
            first_args["injected"] = replace(
                first_args["injected"],
                futures_financial_custody=host.capture_futures_financial_custody_v1(source),
            )
            first = join(**first_args)
            assert first.status == "PASS", first.reason_codes
            first_rid = first.portfolio_reservation_id
            status, reasons, plan = try_bind_current_productive_venue_plan_v1(
                replay=first.replay,
                bound_instrument=first_args["bound_instrument"],
                session_id=host.session_id,
                run_id=host.session_id,
                composed_epoch=EPOCH,
                execution_mode="INTERNAL_SIMULATED_EXECUTION",
            )
            assert status.value == "PASS", reasons
            envelope = bind_final_order_envelope_from_venue_plan_v1(
                plan,
                admission_ref=host.session_id,
                provenance_ref=host.session_id,
                creation_epoch=EPOCH,
            )
            owner = host.owner
            owner.commit_internal_pre_external_effect_v1(first_rid)
            owner.bind_execution_plan_v1(
                first_rid,
                envelope,
                canonical_intent=first.replay.intermediate.canonical_order_intent,
                venue_plan=plan,
            )
            identity = owner.begin_execution_submit_v2(
                first_rid,
                envelope,
                owner.execution_plan_context_v1(first_rid, envelope),
                _permit(envelope),
            )
            first_mark = str(first.replay.intermediate.market_context.mark_price)
            positions.append(
                dict(
                    instId=NATIVE,
                    instType="FUTURES",
                    pos=identity.final_quantity,
                    posSide="net",
                    mgnMode="cross",
                    ccy="USDC",
                    markPx=first_mark,
                )
            )
            submitted.update(
                instId=NATIVE,
                instType="FUTURES",
                clOrdId=identity.clordid,
                ordId="venue-order",
                state="filled",
                sz=identity.final_quantity,
                accFillSz=identity.final_quantity,
            )
            context = first_args["host_budget_recovery"]
            if fault != "unknown-submit":
                from src.ops.execution_reconciliation_get_provenance_v1 import (
                    resolve_reconciliation_query_options_v1,
                )
                from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_okx_read_only_provider_v1 import (
                    fetch_okx_read_only_reconciliation_snapshot_v1,
                )
                from src.ops.productive_futures_accounting_runtime_binding_v1.accounting_engine_v1 import (
                    ProductiveFuturesAccountingSessionV1,
                )
                from src.ops.productive_futures_accounting_runtime_binding_v1.fill_model_v1 import (
                    build_simulated_fill_v1,
                )
                from tests.ops.test_bounded_slot_connected_roundtrip_v1 import (
                    persist_applied_inventory,
                    portfolio_from_accounting,
                )
                from tests.ops.test_productive_futures_accounting_runtime_binding_v1 import (
                    _contract,
                )

                host.fetch = source
                context = host.observe_v1(host.bindings)
                snapshot = fetch_okx_read_only_reconciliation_snapshot_v1(
                    identity=identity,
                    options=resolve_reconciliation_query_options_v1(
                        instrument_id=identity.instrument_id, native_id=identity.native_id
                    ),
                    read_only_get_transport=source.transport._transport,
                    pretrade_decision_id="simulated-filled-other-lane",
                    received_at=EPOCH,
                )
                reconciliation = owner.reconcile_execution_v1(
                    first_rid,
                    snapshot=snapshot,
                    observed=context.observed,
                    account=ACCOUNT,
                    now_unix=host.clock(),
                )
                assert reconciliation["matched"] is True, reconciliation
                context = replace(context, execution_reconciliation={first_rid: reconciliation})
                session = ProductiveFuturesAccountingSessionV1(
                    contract=replace(
                        _contract(NATIVE, contract_size="0.0001"), quote_currency="USDC"
                    )
                )
                session.apply_fill(
                    build_simulated_fill_v1(
                        fill_id="venue-fill",
                        instrument_id=NATIVE,
                        side=envelope.side.upper(),
                        quantity=envelope.quantity,
                        mark_price=first_mark,
                        contract=session.contract,
                        event_time_unix=host.clock(),
                    )
                )
                sessions = {"LANE_1": session}
                portfolio = portfolio_from_accounting(host.bindings, sessions, host.clock())
                persist_applied_inventory(host.root / "reconciliation", portfolio, sessions)
            if fault == "foreign-quantity":
                positions[0]["pos"] = str(Decimal(identity.final_quantity) + 1)
            elif fault == "boundary-before-stop":
                positions[0]["markPx"] = "1000000000"
            _, second_args, _ = prepare(
                tmp_path,
                monkeypatch,
                asset="ETH",
                slot="LANE_2",
                tier_evidence=True,
                host_context=(host, context),
            )
            second_args["injected"] = replace(
                second_args["injected"],
                futures_financial_custody=host.capture_futures_financial_custody_v1(source),
            )
            original_held = owner.active_sum_v1()
            outcome = join(**second_args)
            if fault:
                assert outcome.status != "PASS"
                reason = {
                    "unknown-submit": "XPERP_LIQUIDATION_OTHER_LOCAL_OBLIGATIONS_UNPROVEN",
                    "foreign-quantity": "XPERP_LIQUIDATION_OPEN_POSITION_SCOPE_UNPROVEN",
                    "stale-fee": "STALE",
                    "boundary-before-stop": "XPERP_LIQUIDATION_BOUNDARY_REACHED_BEFORE_OR_AT_STOP",
                }[fault]
                assert any(reason in code for code in outcome.reason_codes), outcome.reason_codes
                assert owner.active_sum_v1() == original_held
            else:
                assert outcome.status == "PASS", outcome.reason_codes
                binding = owner._sizing_bindings[outcome.portfolio_reservation_id]
                receipt = json.loads(binding.xperp_liquidation_binding.receipt_json)
                assert Fraction(receipt["cross_balance_usdc"]) == 1006
                assert Fraction(receipt["other_position_stress_and_cost_usdc"]) > 0
                assert owner.active_sum_v1() > original_held
            assert first_rid in owner.execution_links_v1(active_only=True)
    finally:
        host.close()
