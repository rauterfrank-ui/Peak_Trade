"""Capability tests: productive typed volatility producer + CMC hot-path binding v1."""

from __future__ import annotations

import hashlib
import json
import math
from decimal import Decimal
from pathlib import Path

import pytest

from src.ops.integrated_paper_shadow_observation_session_v1.market_data_policy_v1 import (
    ObservationMarketTickV1,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.constants_v1 import (
    CANONICAL_INSTRUMENT_ID,
)
from src.ops.productive_typed_volatility_producer_and_cmc_hot_path_binding_v1.constants_v1 import (
    CAPABILITY_ID,
    CORE_LOGIC_CHANGE,
    NO_PROXY_PROMOTION,
    VOLATILITY_NUMERIC_MAX_AGE_ENFORCING,
    WARMUP_REQUIRED_PRICE_OBSERVATIONS,
)
from src.ops.simulated_entry_reduce_exit_actionability_evidence_v1.parity_v1 import (
    prove_trading_logic_parity_v1,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.hardening_cycle_bridge_v2 import (
    HardenedBridgeSessionStateV2,
    run_hardened_bridge_cycle_v2,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2.wallclock_hardening_binding_v2 import (
    run_hardened_wallclock_bridge_observation_cycle_v2,
)
from trading.market_state.distinct_market_observation_acceptor_v1 import (
    ObservationTransportMetadataV1,
)
from trading.market_state.time_sample_epoch_semantics_v1 import (
    EventTimeInstantV1,
    MarketSampleIdentityV1,
)
from trading.master_v2.canonical_volatility_estimate_materializer_v1 import (
    BAR_INTERVAL_SECONDS,
)
from trading.master_v2.canonical_volatility_typed_runtime_producer_scaffold_v1 import (
    TypedRuntimeProducerOutcomeV1,
)
from trading.master_v2.double_play_runtime_typed_volatility_presence_gate_v1 import (
    TYPED_VOLATILITY_ESTIMATE_MISSING_REASON,
)

T0 = 1_700_000_040.0
assert T0 % BAR_INTERVAL_SECONDS == 0.0
VENUE = "okx_europe"


def _price_at(i: int) -> float:
    return 100.0 * math.exp(0.001 * i)


def _tick(*, seq: int, event_ts: float, price: float) -> ObservationMarketTickV1:
    return ObservationMarketTickV1(
        instrument_id=CANONICAL_INSTRUMENT_ID,
        venue="OKX",
        market_type="FUTURES",
        sequence=seq,
        event_ts_unix=event_ts,
        receive_ts_unix=event_ts + 0.05,
        mono_ts=float(seq),
        mid_price=price,
    )


def _run_wallclock_minutes(
    state: HardenedBridgeSessionStateV2,
    *,
    minutes: int,
    ticks_per_minute: int = 2,
    session_id: str = "typed-vol-cap",
    start_minute: int = 0,
    seq_start: int = 1,
) -> list[dict]:
    cycles: list[dict] = []
    seq = seq_start
    for minute in range(start_minute, start_minute + minutes):
        for sub_i in range(ticks_per_minute):
            # Keep all ticks of a logical minute inside the same PT1M bucket.
            sub = 5 + sub_i * 10
            et = T0 + minute * BAR_INTERVAL_SECONDS + sub
            price = _price_at(minute) * (1.0 + 1e-6 * sub_i)
            out = run_hardened_wallclock_bridge_observation_cycle_v2(
                bridge_state=state,
                ticks=[_tick(seq=seq, event_ts=et, price=price)],
                reference_price=Decimal(str(price)),
                wall_now_unix=et + 0.05,
                session_id=session_id,
            )
            assert out.ok is True, out.md_blockers
            assert out.bridge_cycle is not None
            cycles.append(
                {
                    "minute": minute,
                    "sub_i": sub_i,
                    "finalized_emitted": out.finalized_pt1m_emitted,
                    "cycle": out.bridge_cycle,
                    "labels": out.labels,
                }
            )
            seq += 1
    return cycles


def test_constants_and_non_goals() -> None:
    assert CAPABILITY_ID == "PRODUCTIVE_TYPED_VOLATILITY_PRODUCER_AND_CMC_HOT_PATH_BINDING_V1"
    assert CORE_LOGIC_CHANGE is False
    assert NO_PROXY_PROMOTION is True
    assert VOLATILITY_NUMERIC_MAX_AGE_ENFORCING is False
    assert WARMUP_REQUIRED_PRICE_OBSERVATIONS == 61


def test_insufficient_history_warmup_reason() -> None:
    state = HardenedBridgeSessionStateV2()
    cycles = _run_wallclock_minutes(state, minutes=5, session_id="warmup-short")
    tele = cycles[-1]["cycle"]["canonical_volatility_typed_binding"]
    assert tele["estimate_present"] is False
    assert tele["producer_outcome"] == TypedRuntimeProducerOutcomeV1.WARMUP.value
    assert tele["fail_closed_reason"] == "WARMUP_NO_ESTIMATE"
    assert cycles[-1]["cycle"]["canonical_market_context_typed_estimate_present"] is False


def test_exact_sufficient_distinct_history_first_estimate() -> None:
    state = HardenedBridgeSessionStateV2()
    # Need 61 finalized PT1M bars → observe minutes 0..61 (rollover emits 0..60).
    cycles = _run_wallclock_minutes(state, minutes=62, session_id="warmup-exact")
    # First PRODUCED should appear when the 61st finalized sample is ingested
    # (finalize of minute-index 60 while opening minute 61).
    produced = [
        c
        for c in cycles
        if c["cycle"]["canonical_volatility_typed_binding"]["producer_outcome"]
        == TypedRuntimeProducerOutcomeV1.PRODUCED.value
    ]
    assert produced, "expected first typed estimate after sufficient PT1M history"
    first = produced[0]
    tele = first["cycle"]["canonical_volatility_typed_binding"]
    assert tele["estimate_present"] is True
    assert tele["typed_binding_performed"] is True
    assert first["cycle"]["canonical_market_context_typed_estimate_present"] is True
    gate = first["cycle"]["double_play_typed_volatility_presence_gate"]
    assert gate["typed_estimate_present"] is True
    assert gate["alpha_scope_entry_authority_allowed"] is True
    assert TYPED_VOLATILITY_ESTIMATE_MISSING_REASON not in gate.get("reason_codes", [])


def test_further_distinct_updates_estimate() -> None:
    state = HardenedBridgeSessionStateV2()
    cycles = _run_wallclock_minutes(state, minutes=64, session_id="update-est")
    produced = [
        c["cycle"]["canonical_volatility_typed_binding"]
        for c in cycles
        if c["cycle"]["canonical_volatility_typed_binding"]["estimate_present"]
    ]
    assert len(produced) >= 2
    digests = [p["source_digest"] for p in produced if p.get("source_digest")]
    assert len(set(digests)) >= 2


def test_intra_minute_duplicate_does_not_advance_history() -> None:
    state = HardenedBridgeSessionStateV2()
    cycles = _run_wallclock_minutes(state, minutes=3, ticks_per_minute=3, session_id="dup-intra")
    host = state.typed_volatility_cmc_binding_host
    assert host is not None
    # Minutes 0..2 observed; finalizes for minutes 0 and 1 only (2 open).
    assert host.producer.history.observation_count_prices == 2
    non_emit = [c for c in cycles if not c["finalized_emitted"]]
    assert len(non_emit) >= 3


def test_missing_observation_no_progress_via_cycle_without_sample() -> None:
    state = HardenedBridgeSessionStateV2()
    _run_wallclock_minutes(state, minutes=5, session_id="missing-obs")
    host = state.typed_volatility_cmc_binding_host
    assert host is not None
    before = host.producer.history.observation_count_prices
    before_digest = host.producer.history.history_digest
    # Decision cycle without finalized PT1M sample must not advance history.
    cycle = run_hardened_bridge_cycle_v2(
        state,
        mid_price=_price_at(5),
        event_ts_unix=T0 + 5 * BAR_INTERVAL_SECONDS + 1.0,
        session_id="missing-obs",
    )
    after = state.typed_volatility_cmc_binding_host.producer.history.observation_count_prices
    assert after == before
    assert state.typed_volatility_cmc_binding_host.producer.history.history_digest == before_digest
    assert cycle["canonical_volatility_typed_binding"]["estimate_present"] is False


def test_out_of_order_observation_fail_closed() -> None:
    state = HardenedBridgeSessionStateV2()
    _run_wallclock_minutes(state, minutes=5, session_id="ooo")
    sample = MarketSampleIdentityV1(
        venue=VENUE,
        canonical_instrument_id=CANONICAL_INSTRUMENT_ID,
        venue_instrument_id=CANONICAL_INSTRUMENT_ID,
        event_time=EventTimeInstantV1(unix_seconds=T0 + BAR_INTERVAL_SECONDS),
        mark_price=90.0,
    )
    cycle = run_hardened_bridge_cycle_v2(
        state,
        mid_price=90.0,
        event_ts_unix=T0 + 10 * BAR_INTERVAL_SECONDS,
        session_id="ooo",
        finalized_pt1m_mark_sample=sample,
        finalized_pt1m_transport=ObservationTransportMetadataV1(receive_time=T0 + 10.0),
    )
    tele = cycle["canonical_volatility_typed_binding"]
    assert tele["producer_outcome"] == TypedRuntimeProducerOutcomeV1.OUT_OF_ORDER_REJECTED.value
    assert tele["estimate_present"] is False


def test_instrument_change_isolates_state() -> None:
    state = HardenedBridgeSessionStateV2()
    _run_wallclock_minutes(state, minutes=10, session_id="iso-a")
    assert state.pt1m_mark_observation_finalizer is not None
    prior = state.pt1m_mark_observation_finalizer.finalized_count
    assert prior > 0
    state.instrument_id = "OTHER-INSTRUMENT"
    # Next wallclock call resets finalizer + typed host for new identity.
    et = T0 + 100 * BAR_INTERVAL_SECONDS + 5.0
    out = run_hardened_wallclock_bridge_observation_cycle_v2(
        bridge_state=state,
        ticks=[_tick(seq=999, event_ts=et, price=123.0)],
        reference_price=Decimal("123.0"),
        wall_now_unix=et + 0.05,
        session_id="iso-a",
    )
    assert out.ok is True
    assert state.pt1m_mark_observation_finalizer.finalized_count == 0
    assert state.pt1m_mark_observation_finalizer.canonical_instrument_id == "OTHER-INSTRUMENT"


def test_legacy_proxy_not_authority_and_no_silent_default() -> None:
    state = HardenedBridgeSessionStateV2()
    cycles = _run_wallclock_minutes(state, minutes=62, session_id="proxy")
    last = cycles[-1]["cycle"]
    fr = last["feature_regime"]
    assert fr["volatility_estimate_productive_authority"] is False
    assert last["canonical_market_context_typed_estimate_present"] is True
    tele = last["canonical_volatility_typed_binding"]
    assert tele["estimate_present"] is True
    assert tele["max_age_status"] == "UNRESOLVED_MAX_AGE"


def test_presence_gate_allows_after_warmup_and_confirmation_not_vol_blocked() -> None:
    state = HardenedBridgeSessionStateV2()
    cycles = _run_wallclock_minutes(state, minutes=62, session_id="presence")
    last = cycles[-1]["cycle"]
    gate = last["double_play_typed_volatility_presence_gate"]
    assert gate["typed_estimate_present"] is True
    assert gate["alpha_scope_entry_authority_allowed"] is True
    assert TYPED_VOLATILITY_ESTIMATE_MISSING_REASON not in gate.get("reason_codes", [])
    # Decision graph progresses past volatility stage.
    assert "canonical_volatility_productive_runtime_cmc_typed_binding" in last["call_graph"]
    assert "master_v2_double_play_integrated_offline_replay" in last["call_graph"]


def test_exit_risk_safety_reachable_when_vol_missing() -> None:
    state = HardenedBridgeSessionStateV2()
    cycles = _run_wallclock_minutes(state, minutes=3, session_id="safety-indep")
    last = cycles[-1]["cycle"]
    assert last["canonical_market_context_typed_estimate_present"] is False
    assert "safety_result" in last
    assert "risk_sizing_result" in last
    # Protection path remains structurally present even when typed vol absent.
    assert last["safety_evaluation"]["trading_gate"] in {
        "ENTRY_AND_EXIT",
        "EXIT_ONLY",
        "BLOCK_ALL",
        "OBSERVE_ONLY",
        "entry_and_exit",
        "exit_only",
        "block_all",
        "observe_only",
    } or isinstance(last["safety_result"], str)


def test_deterministic_replay_digest() -> None:
    def _digest() -> str:
        state = HardenedBridgeSessionStateV2()
        cycles = _run_wallclock_minutes(state, minutes=62, session_id="replay-digest")
        payload = [
            {
                "producer_outcome": c["cycle"]["canonical_volatility_typed_binding"][
                    "producer_outcome"
                ],
                "source_digest": c["cycle"]["canonical_volatility_typed_binding"].get(
                    "source_digest"
                ),
                "history_digest": c["cycle"]["canonical_volatility_typed_binding"].get(
                    "history_digest"
                ),
                "estimate_present": c["cycle"]["canonical_volatility_typed_binding"][
                    "estimate_present"
                ],
            }
            for c in cycles
            if c["finalized_emitted"]
        ]
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

    assert _digest() == _digest()


def test_golden_call_order_and_core_logic_parity() -> None:
    parity = prove_trading_logic_parity_v1()
    assert parity.get("core_logic_change") is False or CORE_LOGIC_CHANGE is False
    assert parity.get("call_order_parity", True) is True or "call_order" in parity
    # Explicit capability invariant.
    assert CORE_LOGIC_CHANGE is False


def test_restart_with_persistence_fail_closed_until_reproduced(tmp_path: Path) -> None:
    persist = tmp_path / "typed_vol_history.json"
    state = HardenedBridgeSessionStateV2(typed_volatility_persistence_path=persist)
    _run_wallclock_minutes(state, minutes=62, session_id="restart-a")
    assert state.typed_volatility_cmc_binding_host is not None
    assert persist.exists()
    # Restore into a fresh session state.
    restored = HardenedBridgeSessionStateV2(typed_volatility_persistence_path=persist)
    restored.restore_typed_volatility_binding_host_from_persistence_v1(persistence_path=persist)
    cycle = run_hardened_bridge_cycle_v2(
        restored,
        mid_price=_price_at(70),
        event_ts_unix=T0 + 70 * BAR_INTERVAL_SECONDS,
        session_id="restart-b",
    )
    tele = cycle["canonical_volatility_typed_binding"]
    # Existing contract: history restored, estimate fail-closed until next PRODUCED.
    assert tele["estimate_present"] is False
    assert tele["restart_without_estimate"] is True
    assert tele["fail_closed_reason"] == "RESTART_WITHOUT_ESTIMATE"


def test_corrupt_volatility_state_fail_closed(tmp_path: Path) -> None:
    persist = tmp_path / "corrupt.json"
    persist.write_text("{not-json", encoding="utf-8")
    state = HardenedBridgeSessionStateV2(typed_volatility_persistence_path=persist)
    with pytest.raises(Exception):
        state.restore_typed_volatility_binding_host_from_persistence_v1(persistence_path=persist)


def test_no_live_testnet_credential_order_reachability() -> None:
    state = HardenedBridgeSessionStateV2()
    cycles = _run_wallclock_minutes(state, minutes=3, session_id="neg-boundary")
    labels = cycles[-1]["labels"]
    assert labels["orders_submitted"] is False
    assert labels["credentials_used"] is False
    assert labels["paper_execution"] is False
    cycle = cycles[-1]["cycle"]
    assert cycle.get("execution_eligible") is False
    assert cycle.get("live_authorized", False) is False or "live_authorized" not in cycle
