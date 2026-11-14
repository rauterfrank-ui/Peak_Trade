"""The hourly MA input and the I17 decision epoch have separate clocks."""

from datetime import datetime, timezone

import pandas as pd
import pytest

from scripts.ops.run_i17_candidate_comparison_v1 import _compare, _strategy_binding
from src.backtest.strategy_signal_suitability_agreement_adapter_v1 import (
    normalize_strategy_signal_to_suitability_agreement_material_v1,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.constants_v1 import (
    CANONICAL_INSTRUMENT_ID,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.hardening_cycle_bridge_v2 import (
    HardenedBridgeSessionStateV2,
    I17OfflineCandidateInputV2,
    run_hardened_bridge_cycle_v2,
)
from src.strategies.registry import build_registry_snapshot
from src.strategies.suitability_registry_adapter_v1 import build_suitability_registry_from_snapshot
from trading.market_state.distinct_market_observation_acceptor_v1 import (
    InstrumentObservationKeyV1,
    ObservationCandidateV1,
    evaluate_distinct_market_observation_v1,
    initial_observation_acceptance_state_v1,
)


def _pair_and_candles():
    profiles = {}
    for role, slow, digest in (("reference", 30, "a"), ("candidate", 40, "b")):
        params = {"fast_window": 10, "slow_window": slow}
        profiles[role] = {
            "packet": digest * 64,
            "parameters": params,
            "config": {
                "economic_evaluation_v1": {
                    "strategy_id": "ma_crossover",
                    "strategy_version": "v1",
                    "strategy_params": params,
                }
            },
        }
    plan = {
        "instrument_id": CANONICAL_INSTRUMENT_ID,
        "strategy_id": "ma_crossover",
        "strategy_version": "v1",
        "profiles": profiles,
    }
    times = pd.date_range(end="2026-11-14T19:00:00Z", periods=70, freq="h")
    closes = [1800.0 + item for item in range(len(times))]
    bars = pd.DataFrame(
        {"open": closes, "high": closes, "low": closes, "close": closes, "volume": 1.0}, index=times
    )
    return plan, bars


def test_same_final_hour_prefix_binds_two_real_i17_epochs():
    plan, bars = _pair_and_candles()
    rows = []
    for sequence, time in enumerate(("2026-11-14T17:59:59+00:00", "2026-11-14T18:00:01+00:00"), 1):
        now = datetime.fromisoformat(time).timestamp()
        rows.append(
            (
                now,
                {
                    "sequence": sequence,
                    "event_ts_unix": now - 0.1,
                    "receive_ts_unix": now - 0.02,
                    "mid_price": 1800.0 + sequence,
                },
                f"original-{sequence}",
            )
        )
    now, repeated, decision_id = rows[-1]
    rows.append(
        (now + 1.0, dict(repeated, sequence=3, receive_ts_unix=now + 0.1), decision_id + "-repeat")
    )
    cycles = _compare(plan, rows, bars, identifier="1" * 64)
    assert [cycle["last_candle_close_utc"] for cycle in cycles] == [
        "2026-11-14T17:00:00+00:00",
        "2026-11-14T18:00:00+00:00",
        "2026-11-14T18:00:00+00:00",
    ]
    for epoch, cycle in enumerate(cycles, 1):
        for role, arm in cycle["arms"].items():
            material = arm["material"]
            assert material["trading_epoch"] == epoch
            assert arm["market_observation_epoch"] == min(epoch, 2)
            assert arm["market_observation_classification"] == (
                "distinct" if epoch < 3 else "transport_only_duplicate"
            )
            assert material["instrument_id"] == CANONICAL_INSTRUMENT_ID
            assert arm["artifact_digest"] == plan["profiles"][role]["packet"]
            prefix = bars.loc[: cycle["last_candle_close_utc"]]
            binding = _strategy_binding(plan, plan["profiles"][role], prefix)
            assert material["strategy_signal_digest"] == binding.provenance.strategy_signal_digest
            assert material["cycle_signal_value"] == int(binding.signals.iloc[-1])


def test_candidate_bridge_rejects_state_persistence_before_cycle(tmp_path):
    plan, bars = _pair_and_candles()
    binding = _strategy_binding(plan, plan["profiles"]["reference"], bars)
    material = normalize_strategy_signal_to_suitability_agreement_material_v1(
        binding, instrument_id=CANONICAL_INSTRUMENT_ID, trading_epoch=1, signal_index=len(bars) - 1
    )
    registry = build_suitability_registry_from_snapshot(build_registry_snapshot())
    entry = next(item for item in registry.entries if item.strategy_id == "ma_crossover")
    tick_time = datetime(2026, 11, 14, tzinfo=timezone.utc).timestamp()
    instrument_key = InstrumentObservationKeyV1(
        "okx", CANONICAL_INSTRUMENT_ID, CANONICAL_INSTRUMENT_ID
    )
    accepted = evaluate_distinct_market_observation_v1(
        initial_observation_acceptance_state_v1(bound_instrument_key=instrument_key),
        ObservationCandidateV1(
            "okx", CANONICAL_INSTRUMENT_ID, CANONICAL_INSTRUMENT_ID, tick_time, 1800.0
        ),
    )
    state = HardenedBridgeSessionStateV2(instrument_id=CANONICAL_INSTRUMENT_ID)
    state.decision_config_state_root = str(tmp_path / "runtime")
    with pytest.raises(ValueError, match="I17_CANDIDATE_REQUIRES_ISOLATED_OFFLINE_CYCLE"):
        run_hardened_bridge_cycle_v2(
            state,
            mid_price=1800.0,
            event_ts_unix=tick_time,
            session_id="candidate-test",
            offline_candidate=I17OfflineCandidateInputV2("a" * 64, entry, material, accepted),
        )
    assert state.cycle_index == 0
    assert not (tmp_path / "runtime").exists()
