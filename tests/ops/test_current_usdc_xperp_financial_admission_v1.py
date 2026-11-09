"""Original financial consumers with explicit offline X-Perp observations.

No live execution, account-custody completeness or market-price claim. Public
instrument identity and private settlement are different source roles. The
native Core produces each side for the same bound FUTURES instrument.
"""

from dataclasses import replace
from datetime import datetime, timezone
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


def instrument(*, settlement="USDC"):
    return dict(
        instId=NATIVE,
        instType="FUTURES",
        state="live",
        uly="BTC-USD",
        instFamily=FAMILY,
        baseCcy="",
        quoteCcy="",
        settleCcy=settlement,
        ctVal="0.0001",
        ctMult="1",
        ctValCcy="BTC",
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


def prepare(tmp_path, monkeypatch, *, short=False, fault=None):
    clock = [EPOCH]
    monkeypatch.setattr(cost, "utc_now_iso_v1", lambda: clock[0])
    # Canonical identity follows the public instrument, not its account's cash
    # preference. Derive it through the original universe producer below.
    from tests.ops.test_governed_futures_universe_producer_v1 import _produce

    universe = _produce([instrument(settlement="USD")], marks=[NATIVE])
    eligible = list(universe.snapshot.instruments)
    assert len(eligible) == 1, universe
    bound = replace(
        _bound(instrument_id=eligible[0].canonical_instrument_id), venue_native_id=NATIVE
    )
    producer = _produced_g17_producer(instrument_id=bound.instrument_id, venue_native_id=NATIVE)
    run = (
        run_natural_enter_short_sequence_for_bound_v1
        if short
        else run_natural_enter_long_sequence_for_bound_v1
    )(bound=bound, g17_typed_vol_producer=producer)
    cycle = run[3] if short else run[2]
    host = PortfolioBudgetHostV1(
        root=tmp_path / "host",
        private_rest_fetch=_fetch(uid=ACCOUNT),
        repository_sha="explicit-offline-usdc-financial-test",
        session_id="usdc-financial-test",
        expected_account_identity=ACCOUNT,
        durable_mode="create",
        clock=lambda: datetime.fromisoformat(EPOCH.replace("Z", "+00:00")).timestamp(),
        execution_environment="INTERNAL_SIMULATED_EXECUTION",
        entry_budget_policy=policy(),
    )
    context = host.observe_v1({"LANE_1": bound})
    payload = _balance_payload(avail_eq="1000")
    row = instrument()
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
        portfolio_slot=Slot("LANE_1", cycle.replay.evidence.decision_id, "usdc-financial-entry"),
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
        f"/api/v5/account/instruments?instType=FUTURES&instId={NATIVE}": source(
            f"/api/v5/account/instruments?instType=FUTURES&instId={NATIVE}",
            dict(code="0", data=[row]),
            True,
        ),
        f"/api/v5/account/trade-fee?instType=FUTURES&instFamily={FAMILY}": source(
            f"/api/v5/account/trade-fee?instType=FUTURES&instFamily={FAMILY}",
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
        f"/api/v5/market/books?instId={NATIVE}&sz=20": source(
            f"/api/v5/market/books?instId={NATIVE}&sz=20",
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
        endpoint = f"/api/v5/account/instruments?instType=FUTURES&instId={NATIVE}"
        original = rows[endpoint]
        if fault == "unauthenticated-instrument":
            rows[endpoint] = replace(original, auth_header_sent=False)
        elif fault == "public-instrument-label":
            rows[endpoint] = replace(
                original, endpoint=original.endpoint.replace("/account/", "/public/")
            )
        else:
            public = dict(code="0", data=[instrument(settlement="USD")])
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
    assert port.calls[1] == (f"/api/v5/account/instruments?instType=FUTURES&instId={NATIVE}", True)
    balance = source("/api/v5/account/balance", payload, True)
    leverage = source(
        f"/api/v5/account/leverage-info?instId={NATIVE}&mgnMode=cross",
        dict(code="0", data=[dict(instId=NATIVE, mgnMode="cross", posSide="net", lever="3")]),
        True,
    )
    funding = source(
        f"/api/v5/public/funding-rate?instId={NATIVE}",
        dict(
            code="0",
            data=[
                dict(
                    instId=NATIVE,
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
        native_initial_margin_observation=margin.NativeInitialMarginObservationV1.capture_v1(
            sources=dict(balance=balance, leverage=leverage),
            opening_observation=opening,
            evaluated_at_utc=EPOCH,
        ),
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
def test_usdc_xperp_original_core_quantity_hold_and_cold_read(tmp_path, monkeypatch, short):
    host, kwargs, clock = prepare(tmp_path, monkeypatch, short=short)
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
