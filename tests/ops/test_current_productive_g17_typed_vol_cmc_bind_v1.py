"""CURRENT_PRODUCTIVE G17 typed-vol CMC bind join tests (S2-BIND MS2)."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.current_productive_g17_typed_vol_cmc_bind_v1 import (
    BIND_OWNER,
    CMC_BINDING_PERFORMED,
    ECONOMIC_MD_OWNER,
    ESTIMATE_ABSENT_CMC_POLICY,
    GLOBAL_SINGLETON,
    HARDENING_SESSION_OWNER,
    INGEST_SAMPLE,
    JOIN_1_REWRITTEN,
    JOIN_2_REWRITTEN,
    PACKAGE_MARKER,
    PRESENCE_GATE_IN_THIS_WP,
    PRESENCE_GATE_MUTATED,
    SIDESTATE_CURSOR_OWNER,
    CurrentProductiveG17CmcBindError,
    apply_current_productive_g17_typed_vol_cmc_bind_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1 import (
    run_current_productive_master_v2_runtime_cycle_v1,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1
from trading.master_v2.canonical_market_context_v1 import (
    FEATURE_CONTRACT_VERSION,
    BarFinalityStatus,
    CanonicalMarketContextV1,
    ClockTrustStatus,
    DataIntegrityStatus,
    FuturesMarketType,
    WarmupStatus,
)
from trading.master_v2.canonical_volatility_typed_runtime_producer_scaffold_v1 import (
    TypedRuntimeProducerOutcomeV1,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import ExistingPositionSide
from trading.master_v2.double_play_runtime_typed_volatility_presence_gate_v1 import (
    TYPED_VOLATILITY_ESTIMATE_MISSING_REASON,
)
from tests.ops.test_current_productive_g17_typed_vol_mark_history_checkpoint_v1 import (
    _apply,
    _sixty_one_samples,
)

REPO = Path(__file__).resolve().parents[2]
V5_HOST = (
    REPO
    / "src/ops/governed_productive_account_equity_authority_producer_v1"
    / "current_productive_one_runtime_cycle_after_new_finalized_1m_c1_observation_v5.py"
)
BIND_SRC = (
    REPO
    / "src/ops/full_core_live_path_composition_root_v1"
    / "current_productive_g17_typed_vol_cmc_bind_v1.py"
)
MASTER_V2_SRC = (
    REPO
    / "src/ops/full_core_live_path_composition_root_v1"
    / "current_productive_master_v2_runtime_cycle_v1.py"
)
JOIN1_SRC = (
    REPO
    / "src/ops/full_core_live_path_composition_root_v1"
    / "current_productive_g17_pt1m_mark_sample_adapter_v1.py"
)
JOIN2_SRC = (
    REPO
    / "src/ops/full_core_live_path_composition_root_v1"
    / "current_productive_g17_typed_vol_mark_history_checkpoint_v1.py"
)
FEATURE_VOL = 0.38


def _context(**overrides: object) -> CanonicalMarketContextV1:
    base: dict = {
        "context_id": "ctx-g17-cmc-bind-v1",
        "instrument_id": "BTC-USDT-SWAP-CANON",
        "market_type": FuturesMarketType.PERPETUAL,
        "trading_epoch": 1,
        "market_event_time": "2023-11-14T22:13:20.000000Z",
        "decision_time": "2023-11-14T22:13:21.000000Z",
        "bar_interval": "1m",
        "bar_finality_status": BarFinalityStatus.FINALIZED,
        "mark_price": 160.0,
        "index_price": 160.0,
        "best_bid": 159.5,
        "best_ask": 160.5,
        "spread": 1.0,
        "volume": 12_345.0,
        "open_interest": 1_000.0,
        "funding_rate": 0.0001,
        "volatility_estimate": FEATURE_VOL,
        "trend_feature_set": {"slope": 0.02},
        "momentum_feature_set": {"rsi": 55.0},
        "liquidity_feature_set": {"depth_score": 0.88},
        "market_structure_feature_set": {"range_ratio": 0.42},
        "data_integrity_status": DataIntegrityStatus.TRUSTED,
        "clock_trust_status": ClockTrustStatus.TRUSTED,
        "warmup_status": WarmupStatus.WARMUP_COMPLETE,
        "feature_contract_version": FEATURE_CONTRACT_VERSION,
        "input_digest": "",
        "canonical_volatility_estimate": None,
    }
    base.update(overrides)
    return CanonicalMarketContextV1(**base)


def _bound() -> BoundInstrumentV1:
    return BoundInstrumentV1(
        instrument_id="BTC-USDT-SWAP-CANON",
        venue_native_id="BTC-USDT-SWAP",
        ranking_snapshot_id="rank-g17-bind",
        ranking_integrity_digest="rank-g17-bind-digest",
        universe_snapshot_id="uni-g17-bind",
        selection_id="sel-g17-bind",
        selection_integrity_digest="sel-g17-bind-digest",
        selection_state="SELECTED",
    )


def _closes() -> tuple[float, ...]:
    return tuple(1000.0 + float(index) * 10.0 for index in range(64))


def test_owner_lock_tokens_and_non_transfer() -> None:
    assert PACKAGE_MARKER.endswith("=true")
    assert BIND_OWNER.endswith("current_productive_g17_typed_vol_cmc_bind_v1")
    assert ESTIMATE_ABSENT_CMC_POLICY == "BIND_ONLY_WHEN_PRODUCED"
    assert INGEST_SAMPLE is False
    assert PRESENCE_GATE_IN_THIS_WP is False
    assert CMC_BINDING_PERFORMED is True
    assert PRESENCE_GATE_MUTATED is False
    assert HARDENING_SESSION_OWNER is False
    assert SIDESTATE_CURSOR_OWNER is False
    assert ECONOMIC_MD_OWNER is False
    assert GLOBAL_SINGLETON is False
    assert JOIN_1_REWRITTEN is False
    assert JOIN_2_REWRITTEN is False


def test_produced_typed_estimate_reaches_cmc_and_preserves_join2_producer(
    tmp_path: Path,
) -> None:
    created = _apply(tmp_path, samples=_sixty_one_samples())
    assert created.producer is not None
    assert created.last_outcome == TypedRuntimeProducerOutcomeV1.PRODUCED.value
    context = _context()
    bound = apply_current_productive_g17_typed_vol_cmc_bind_v1(
        context,
        producer=created.producer,
    )
    assert bound.bind_performed is True
    assert bound.producer is created.producer
    assert bound.context is not context
    assert bound.context.canonical_volatility_estimate is not None
    assert bound.context.canonical_volatility_estimate is created.producer.output_port_v1().estimate
    assert bound.context.volatility_estimate != FEATURE_VOL
    assert context.volatility_estimate == FEATURE_VOL
    assert context.canonical_volatility_estimate is None


def test_absent_estimate_leaves_existing_cmc_volatility_unchanged(tmp_path: Path) -> None:
    _apply(tmp_path, samples=_sixty_one_samples())
    restored = _apply(tmp_path, samples=())
    assert restored.producer is not None
    assert restored.estimate_present is False
    context = _context()
    bound = apply_current_productive_g17_typed_vol_cmc_bind_v1(
        context,
        producer=restored.producer,
    )
    assert bound.bind_performed is False
    assert bound.producer is restored.producer
    assert bound.context is context
    assert bound.context.volatility_estimate == FEATURE_VOL
    assert bound.context.canonical_volatility_estimate is None


def test_none_producer_leaves_context_identity() -> None:
    context = _context()
    bound = apply_current_productive_g17_typed_vol_cmc_bind_v1(context, producer=None)
    assert bound.bind_performed is False
    assert bound.producer is None
    assert bound.context is context


def test_invalid_producer_type_fail_closed() -> None:
    with pytest.raises(
        CurrentProductiveG17CmcBindError, match="G17_CMC_BIND_PRODUCER_TYPE_INVALID"
    ):
        apply_current_productive_g17_typed_vol_cmc_bind_v1(_context(), producer="not-a-producer")  # type: ignore[arg-type]


def test_bind_does_not_ingest_create_or_restore(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    created = _apply(tmp_path, samples=_sixty_one_samples())
    producer = created.producer
    assert producer is not None
    ingest_calls: list[object] = []
    create_calls: list[object] = []
    restore_calls: list[object] = []
    monkeypatch.setattr(
        producer,
        "ingest_finalized_pt1m_mark_sample_v1",
        lambda **_kwargs: ingest_calls.append(True),
    )
    monkeypatch.setattr(
        type(producer),
        "create",
        classmethod(lambda cls, **_kwargs: create_calls.append(True)),
    )
    monkeypatch.setattr(
        type(producer),
        "restore_from_persistence_v1",
        classmethod(lambda cls, **_kwargs: restore_calls.append(True)),
    )
    apply_current_productive_g17_typed_vol_cmc_bind_v1(_context(), producer=producer)
    assert ingest_calls == []
    assert create_calls == []
    assert restore_calls == []


def test_master_v2_cycle_consumes_produced_join2_producer(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    created = _apply(tmp_path, samples=_sixty_one_samples())
    assert created.producer is not None
    import src.ops.full_core_live_path_composition_root_v1.current_productive_g17_typed_vol_cmc_bind_v1 as bind_mod

    calls: list[object] = []
    original = bind_mod.bind_typed_canonical_volatility_estimate_into_market_context_v1

    def _wrapped(context, estimate):
        calls.append(estimate)
        return original(context, estimate)

    monkeypatch.setattr(
        bind_mod,
        "bind_typed_canonical_volatility_estimate_into_market_context_v1",
        _wrapped,
    )
    closes = _closes()
    last = float(closes[-1])
    cycle = run_current_productive_master_v2_runtime_cycle_v1(
        bound_instrument=_bound(),
        cycle_id="g17-cmc-bind-produced",
        observed_unix=1_700_000_100.0,
        mark_px=last,
        index_px=last,
        bid_px=last - 0.5,
        ask_px=last + 0.5,
        volume=12_345.0,
        open_interest=1_000.0,
        funding_rate=0.0001,
        finalized_closes=closes,
        last_finalized_event_ts_unix=1_700_000_000.0,
        venue_flat=True,
        existing_position_side=ExistingPositionSide.NONE,
        g17_typed_vol_producer=created.producer,
    )
    assert cycle.input_blocker == ""
    assert cycle.replay is not None
    assert TYPED_VOLATILITY_ESTIMATE_MISSING_REASON not in cycle.fail_reasons
    assert len(calls) == 1
    assert calls[0] is created.producer.output_port_v1().estimate


def test_master_v2_cycle_absent_estimate_does_not_bind_typed_carrier(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _apply(tmp_path, samples=_sixty_one_samples())
    restored = _apply(tmp_path, samples=())
    import src.ops.full_core_live_path_composition_root_v1.current_productive_g17_typed_vol_cmc_bind_v1 as bind_mod

    calls: list[object] = []
    original = bind_mod.bind_typed_canonical_volatility_estimate_into_market_context_v1

    def _wrapped(context, estimate):
        calls.append(estimate)
        return original(context, estimate)

    monkeypatch.setattr(
        bind_mod,
        "bind_typed_canonical_volatility_estimate_into_market_context_v1",
        _wrapped,
    )
    closes = _closes()
    last = float(closes[-1])
    without_producer = run_current_productive_master_v2_runtime_cycle_v1(
        bound_instrument=_bound(),
        cycle_id="g17-cmc-bind-absent-baseline",
        observed_unix=1_700_000_100.0,
        mark_px=last,
        index_px=last,
        bid_px=last - 0.5,
        ask_px=last + 0.5,
        volume=12_345.0,
        open_interest=1_000.0,
        funding_rate=0.0001,
        finalized_closes=closes,
        last_finalized_event_ts_unix=1_700_000_000.0,
        venue_flat=True,
        existing_position_side=ExistingPositionSide.NONE,
    )
    with_restored = run_current_productive_master_v2_runtime_cycle_v1(
        bound_instrument=_bound(),
        cycle_id="g17-cmc-bind-absent",
        observed_unix=1_700_000_100.0,
        mark_px=last,
        index_px=last,
        bid_px=last - 0.5,
        ask_px=last + 0.5,
        volume=12_345.0,
        open_interest=1_000.0,
        funding_rate=0.0001,
        finalized_closes=closes,
        last_finalized_event_ts_unix=1_700_000_000.0,
        venue_flat=True,
        existing_position_side=ExistingPositionSide.NONE,
        g17_typed_vol_producer=restored.producer,
    )
    assert without_producer.input_blocker == ""
    assert with_restored.input_blocker == ""
    assert without_producer.decision_outcome == with_restored.decision_outcome
    assert without_producer.fail_reasons == with_restored.fail_reasons
    assert calls == []


def _allowed_bound() -> BoundInstrumentV1:
    return BoundInstrumentV1(
        instrument_id="inst-eth-usdt-perp",
        venue_native_id="inst-eth-usdt-perp",
        ranking_snapshot_id="rank-g17-bind",
        ranking_integrity_digest="rank-g17-bind-digest",
        universe_snapshot_id="uni-g17-bind",
        selection_id="sel-g17-bind",
        selection_integrity_digest="sel-g17-bind-digest",
        selection_state="SELECTED",
    )


def _cycle_kwargs(cycle_id: str, *, producer=None) -> dict:
    closes = _closes()
    last = float(closes[-1])
    return {
        "bound_instrument": _allowed_bound(),
        "cycle_id": cycle_id,
        "observed_unix": 1_700_000_100.0,
        "mark_px": last,
        "index_px": last,
        "bid_px": last - 0.5,
        "ask_px": last + 0.5,
        "volume": 12_345.0,
        "open_interest": 1_000.0,
        "funding_rate": 0.0001,
        "finalized_closes": closes,
        "last_finalized_event_ts_unix": 1_700_000_000.0,
        "venue_flat": True,
        "existing_position_side": ExistingPositionSide.NONE,
        "g17_typed_vol_producer": producer,
    }


def test_master_v2_cycle_none_producer_fail_closes_typed_presence() -> None:
    cycle = run_current_productive_master_v2_runtime_cycle_v1(**_cycle_kwargs("g17-presence-none"))
    assert cycle.input_blocker == ""
    assert TYPED_VOLATILITY_ESTIMATE_MISSING_REASON in cycle.fail_reasons
    assert cycle.decision_outcome not in {"enter_long", "enter_short"}


def test_master_v2_cycle_produced_estimate_does_not_presence_fail(
    tmp_path: Path,
) -> None:
    created = _apply(
        tmp_path,
        samples=_sixty_one_samples(
            canonical_instrument_id="inst-eth-usdt-perp",
            venue_instrument_id="inst-eth-usdt-perp",
        ),
        canonical_instrument_id="inst-eth-usdt-perp",
        venue_instrument_id="inst-eth-usdt-perp",
    )
    assert created.producer is not None
    cycle = run_current_productive_master_v2_runtime_cycle_v1(
        **_cycle_kwargs("g17-presence-produced", producer=created.producer)
    )
    assert cycle.input_blocker == ""
    assert TYPED_VOLATILITY_ESTIMATE_MISSING_REASON not in cycle.fail_reasons


def test_source_freeze_no_second_owner_ingest_or_presence_gate() -> None:
    bind_src = BIND_SRC.read_text(encoding="utf-8")
    master_src = MASTER_V2_SRC.read_text(encoding="utf-8")
    assert not V5_HOST.is_file()
    join1 = JOIN1_SRC.read_text(encoding="utf-8")
    join2 = JOIN2_SRC.read_text(encoding="utf-8")
    assert "ingest_finalized_pt1m_mark_sample_v1" not in bind_src
    assert "restore_from_persistence_v1" not in bind_src
    assert ".create(" not in bind_src
    assert "HardenedBridgeSessionStateV2" not in bind_src
    assert "evaluate_double_play_runtime_typed_volatility_presence_gate_v1" not in bind_src
    assert "require_productive_typed_volatility_presence_gate=True" not in bind_src
    assert "run_economic_md_input_producer_v1" not in bind_src
    assert "bind_typed_canonical_volatility_estimate_into_market_context_v1" in bind_src
    assert "apply_current_productive_g17_typed_vol_cmc_bind_v1" in master_src
    assert "ingest_finalized_pt1m_mark_sample_v1" not in master_src
    assert "require_productive_typed_volatility_presence_gate=True" in master_src
    assert "HardenedBridgeSessionStateV2" not in master_src
    assert "producer=g17_typed_vol_producer" in master_src
    assert "CMC_BINDING_PERFORMED = False" in join1
    assert "PRESENCE_GATE_MUTATED = False" in join1
    assert "CMC_BINDING_PERFORMED = False" in join2
    assert "PRESENCE_GATE_MUTATED = False" in join2
    assert "apply_current_productive_g17_typed_vol_cmc_bind_v1" not in join1
    assert "apply_current_productive_g17_typed_vol_cmc_bind_v1" not in join2
