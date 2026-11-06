"""Instrument-bound G17 → GGE → Double Play; dated metadata, synthetic prices."""

import json
import math
from dataclasses import replace
from decimal import Decimal, localcontext
from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.current_productive_future_identity_semantics_v1 import (
    resolve_selected_future_market_type_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_g17_typed_vol_cmc_bind_v1 import (
    CurrentProductiveG17CmcBindError,
    apply_current_productive_g17_typed_vol_cmc_bind_v1,
)
from trading.master_v2.canonical_market_context_v1 import with_computed_input_digest
from trading.master_v2.canonical_volatility_typed_runtime_producer_scaffold_v1 import (
    CanonicalVolatilityTypedRuntimeProducerScaffoldV1,
)
from trading.master_v2.double_play_futures_input import FuturesMarketType
from trading.master_v2.double_play_state import DynamicScopeRules
from trading.master_v2.golden_geometry_engine_v1 import (
    compute_canonical_base_geometry_magnitude_from_market_context_v1,
    compute_canonical_base_geometry_magnitude_from_mark_and_volatility_v1,
)
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    run_integrated_offline_trading_logic_replay_v1,
)
from tests.ops.test_gge_scope_learning_configuration_cutover_v2 import _input

FIXTURE = (
    Path(__file__).parents[1]
    / "fixtures/trading/gge_only_future_interpretation_v3/instruments.json"
)
ROWS = json.loads(FIXTURE.read_text())["instruments"]
# Explicitly synthetic additions: the dated snapshot omitted BTC under the
# retired rule. These are not current venue listings or real quote/lot data.
for native, contract, quote, settlement, identity in [
    ("BTC-USDT-SWAP", "linear_perpetual", "USDT", "USDT", "btc-usdt-swap"),
    ("BTC-USDC-SWAP", "linear_perpetual", "USDC", "USDC", "btc-usdc-swap"),
    ("BTC-USD-261225", "linear_dated_future", "USD", "USDC", "20261225"),
]:
    ROWS.append(
        {
            "canonical_instrument_id": f"okx_eea:{contract}:BTC:{quote}:{settlement}:{identity}",
            "venue_native_inst_id": native,
            "contract_type": contract,
            "tick_size": "0.01",
            "synthetic_identity_case": True,
        }
    )
T0 = 1788260400.0


def _bound_context(row, base):
    instrument = row["canonical_instrument_id"]
    native = row["venue_native_inst_id"]
    producer = CanonicalVolatilityTypedRuntimeProducerScaffoldV1.create(
        venue="okx_eea",
        canonical_instrument_id=instrument,
        venue_instrument_id=native,
    )
    prices = [base * math.exp(0.004 * math.sin(i) + 0.002 * math.cos(i * 1.7)) for i in range(61)]
    for i, price in enumerate(prices):
        producer.ingest_finalized_pt1m_mark_sample_v1(
            event_time_unix_seconds=T0 + i * 60,
            mark_price=price,
        )
    assert producer.output_port_v1().estimate is not None
    inp = _input(price=prices[-1])
    ctx = with_computed_input_digest(
        replace(
            inp.canonical_market_context,
            instrument_id=instrument,
            market_type=resolve_selected_future_market_type_v1(
                instrument_id=instrument, venue_native_id=native
            ),
            market_event_time="2026-09-01T12:00:00Z",
            decision_time="2026-09-01T12:00:01Z",
            input_digest="",
        )
    )
    bound = apply_current_productive_g17_typed_vol_cmc_bind_v1(
        ctx,
        producer=producer,
        expected_venue_native_id=native,
        expected_venue="okx_eea",
    )
    assert bound.bind_performed
    return producer, bound.context, prices


def _decimal_population_sigma(prices):
    with localcontext() as ctx:
        ctx.prec = 40
        p = [Decimal(str(v)) for v in prices]
        returns = [(b / a).ln() for a, b in zip(p, p[1:])]
        mean = sum(returns) / len(returns)
        return float((sum((x - mean) ** 2 for x in returns) / len(returns)).sqrt())


@pytest.mark.parametrize(
    "index,row", list(enumerate(ROWS)), ids=[r["venue_native_inst_id"] for r in ROWS]
)
def test_each_snapshot_future_through_real_g17_gge_and_double_play(index, row):
    scales = [0.00001, 0.02, 1.0, 100.0, 50000.0, 100000.0]
    base = max(scales[index % len(scales)], float(row["tick_size"]) * 1000)
    _, context, prices = _bound_context(row, base)
    expected = _decimal_population_sigma(prices) * prices[-1]
    gge = compute_canonical_base_geometry_magnitude_from_market_context_v1(context)
    assert gge.ok
    assert gge.output.instrument_id == row["canonical_instrument_id"]
    assert gge.output.magnitude == pytest.approx(expected, rel=1e-9)
    inp = _input(price=prices[-1])
    replay = run_integrated_offline_trading_logic_replay_v1(
        replace(
            inp,
            instrument_id=context.instrument_id,
            canonical_market_context=context,
            price_path=(prices[-2], prices[-1]),
            current_price=prices[-1],
            input_digest=context.input_digest,
        )
    )
    assert replay.intermediate is not None, replay.fail_reasons
    assert replay.intermediate.effective_scope_magnitude == pytest.approx(expected, rel=1e-9)
    assert replay.intermediate.scope_event.semantic_binding.up_distance == pytest.approx(
        expected, rel=1e-9
    )
    assert not any("hard_max" in r for r in replay.intermediate.scope_event.blocked_reasons)


def test_dated_future_is_not_mislabeled_as_perpetual():
    assert (
        resolve_selected_future_market_type_v1(
            instrument_id="okx_eea:linear_dated_future:ETH:USD:USDC:20261225",
            venue_native_id="ETH-USD-261225",
        )
        is FuturesMarketType.FUTURES
    )


@pytest.mark.parametrize(
    "instrument,native",
    [
        ("okx_eea:linear_perpetual:ETH:USDT:USDT:eth-usdt-swap", "SOL-USDT-SWAP"),
        ("okx_eea:linear_perpetual:ETH:USDT:USDT:eth-usdt-swap", "ETH-USDT-261225"),
        ("okx_eea:inverse_perpetual:ETH:USD:ETH:eth-usd-swap", "ETH-USD-SWAP"),
        ("opaque", "UNKNOWN"),
    ],
)
def test_unknown_or_mismatched_contract_identity_blocks(instrument, native):
    with pytest.raises(ValueError):
        resolve_selected_future_market_type_v1(instrument_id=instrument, venue_native_id=native)


def test_volatility_history_from_another_future_cannot_bind():
    producer, context, _ = _bound_context(ROWS[0], 1.0)
    with pytest.raises(CurrentProductiveG17CmcBindError, match="INSTRUMENT_MISMATCH"):
        apply_current_productive_g17_typed_vol_cmc_bind_v1(
            replace(context, instrument_id=ROWS[1]["canonical_instrument_id"]),
            producer=producer,
        )


def test_g17_estimate_cannot_come_from_the_future():
    producer, context, _ = _bound_context(ROWS[0], 1.0)
    with pytest.raises(CurrentProductiveG17CmcBindError, match="FUTURE_ESTIMATE"):
        apply_current_productive_g17_typed_vol_cmc_bind_v1(
            replace(context, decision_time="2026-09-01T11:00:00Z"),
            producer=producer,
        )


def test_same_canonical_id_cannot_hide_another_native_contract():
    producer, context, _ = _bound_context(ROWS[0], 1.0)
    with pytest.raises(CurrentProductiveG17CmcBindError, match="NATIVE_INSTRUMENT_MISMATCH"):
        apply_current_productive_g17_typed_vol_cmc_bind_v1(
            context,
            producer=producer,
            expected_venue_native_id="OTHER-USDT-SWAP",
        )


@pytest.mark.parametrize(
    "field,value", [("unit", "percent"), ("annualized", True), ("bar_interval_seconds", 3600)]
)
def test_gge_rejects_wrong_volatility_units(field, value):
    _, context, _ = _bound_context(ROWS[0], 1.0)
    estimate = replace(context.canonical_volatility_estimate, **{field: value})
    result = compute_canonical_base_geometry_magnitude_from_market_context_v1(
        replace(context, canonical_volatility_estimate=estimate)
    )
    assert not result.ok
    assert result.output is None


def test_old_rule_volatility_cannot_override_the_canonical_market_input():
    result = run_integrated_offline_trading_logic_replay_v1(
        replace(
            _input(),
            dynamic_scope_rules=DynamicScopeRules(volatility_estimate=0.9),
        )
    )
    assert not result.replay_pass
    assert any("dynamic_scope_volatility_fail_closed" in r for r in result.fail_reasons)


def test_fixed_event_distance_caps_are_rejected_by_double_play():
    inp = _input()
    result = run_integrated_offline_trading_logic_replay_v1(
        replace(
            inp,
            policies=replace(
                inp.policies,
                scope_event_generator=replace(
                    inp.policies.scope_event_generator,
                    legacy_distance_limits=True,
                ),
            ),
        )
    )
    assert "fixed_scope_policy_retired" in result.fail_reasons


def test_retired_numeric_cap_slots_cannot_block_valid_gge_geometry():
    inp = _input(price=100000.0)
    result = run_integrated_offline_trading_logic_replay_v1(
        replace(
            inp,
            policies=replace(
                inp.policies,
                scope_event_generator=replace(
                    inp.policies.scope_event_generator,
                    hard_max_scope_distance=0.0,
                    hard_max_adverse_distance=0.0,
                    hard_max_reversal_distance=0.0,
                ),
            ),
        )
    )
    assert result.intermediate is not None
    assert result.intermediate.effective_scope_magnitude == 2000.0
    assert not any("hard_max" in r for r in result.intermediate.scope_event.blocked_reasons)


@pytest.mark.parametrize("mark,vol", [(True, 0.02), (1.0, True), (10**500, 0.02)])
def test_nonnumeric_or_overflowing_geometry_inputs_fail_closed(mark, vol):
    assert not compute_canonical_base_geometry_magnitude_from_mark_and_volatility_v1(
        instrument_id="test-future",
        mark_price=mark,
        volatility_estimate=vol,
    ).ok


def test_bitcoin_has_the_same_minimum_quantity_risk_rejection_as_other_futures():
    from tests.governance.test_capital_risk_sizing_v1 import _evaluate, _instrument

    results = []
    for instrument in ("ETH-USD-PERP", "BTC-USD-PERP"):
        results.append(
            _evaluate(
                instrument_id=instrument,
                instrument=_instrument(
                    instrument_id=instrument, minimum_quantity=Decimal("1000000")
                ),
            )
        )
    assert all(r.outcome.value == "BLOCKED" for r in results)
    assert results[0].reason_codes == results[1].reason_codes


def test_true_spot_is_still_rejected_for_bitcoin_and_other_assets():
    from trading.master_v2.double_play_futures_input import futures_instrument_identity_allowed_v1

    assert not futures_instrument_identity_allowed_v1("BTC-USDT-SPOT")
    assert not futures_instrument_identity_allowed_v1("ETH-USDT-SPOT")
    assert futures_instrument_identity_allowed_v1("BTC-USDT-SWAP")
    assert futures_instrument_identity_allowed_v1("AIXBT-USDT-SWAP")
