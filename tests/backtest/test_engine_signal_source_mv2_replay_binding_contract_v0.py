from __future__ import annotations

from typing import Any, Mapping

import pandas as pd
import pytest

from src.backtest import mv2_research_wiring_v1 as wiring
from src.backtest.strategy_signal_binding_v1 import (
    CANONICAL_MV2_SYSTEM_PATH_CLASSIFICATION,
    CANONICAL_SYSTEM_ENGINE_SIGNAL_SOURCE,
    ENGINE_SIGNAL_SOURCE_CONFIGURED_STRATEGY,
    ENGINE_SIGNAL_SOURCE_MV2_REPLAY,
    LEGACY_RAW_SIGNAL_RESEARCH_ENGINE_SIGNAL_SOURCE,
    RUN_BACKTEST_PATH_CLASSIFICATION,
    StrategySignalBindingError,
    assert_backtest_engine_mv2_replay_signal_parity_v1,
    assert_decision_funnel_trade_alignment_v1,
    assert_parallel_strategy_signal_does_not_control_engine_v1,
    resolve_mv2_research_engine_signal_source_v1,
    validate_engine_signal_source_v1,
    validate_mv2_replay_engine_signal_contract_v1,
)


def _cfg(*, engine_signal_source: str | None = None) -> Mapping[str, Any]:
    payload: dict[str, Any] = {
        "backtest": {
            "initial_cash": 10_000.0,
            "cost_model_version": "backtest_cost_v0",
            "fee_bps": 10.0,
            "slippage_bps": 5.0,
        },
        "risk": {
            "risk_per_trade": 0.02,
            "max_position_size": 0.25,
            "min_position_value": 10.0,
            "min_stop_distance": 0.0001,
        },
        "economic_evaluation_v1": {
            "strategy_params": {"fast_window": 2, "slow_window": 3},
        },
    }
    if engine_signal_source is not None:
        payload["economic_evaluation_v1"]["engine_signal_source"] = engine_signal_source
    return payload


def _bars(n: int = 12) -> pd.DataFrame:
    idx = pd.date_range("2026-06-01", periods=n, freq="1h", tz="UTC")
    close = [100.0 + float(i) for i in range(n)]
    return pd.DataFrame(
        {
            "open": close,
            "high": [v + 0.5 for v in close],
            "low": [v - 0.5 for v in close],
            "close": close,
            "mark_price": close,
            "index_price": [v - 0.1 for v in close],
            "best_bid": [v - 0.05 for v in close],
            "best_ask": [v + 0.05 for v in close],
            "spread": [0.1 for _ in close],
            "volume": [1000.0 for _ in close],
            "open_interest": [10000.0 for _ in close],
            "funding_rate": [0.0001 for _ in close],
            "volatility_estimate": [0.2 for _ in close],
            "is_final": [True for _ in close],
            "bar_interval": ["1m" for _ in close],
        },
        index=idx,
    )


def _run(**kwargs: Any) -> wiring.MV2ResearchWiringResultV1:
    return wiring.run_mv2_research_backtest_wiring_v1(
        bars=kwargs.pop("bars", _bars()),
        strategy_id=kwargs.pop("strategy_id", "ma_crossover"),
        cfg=kwargs.pop("cfg", _cfg()),
        **kwargs,
    )


def test_resolver_defaults_to_canonical_mv2_replay() -> None:
    assert resolve_mv2_research_engine_signal_source_v1() == CANONICAL_SYSTEM_ENGINE_SIGNAL_SOURCE


def test_resolver_prefers_cfg_binding_over_explicit() -> None:
    resolved = resolve_mv2_research_engine_signal_source_v1(
        explicit_source=ENGINE_SIGNAL_SOURCE_CONFIGURED_STRATEGY,
        cfg=_cfg(engine_signal_source=ENGINE_SIGNAL_SOURCE_MV2_REPLAY),
    )
    assert resolved == ENGINE_SIGNAL_SOURCE_MV2_REPLAY


def test_resolver_rejects_unknown_source() -> None:
    with pytest.raises(StrategySignalBindingError, match="engine_signal_source_unsupported"):
        validate_engine_signal_source_v1("parallel_mixed_signal_truth")


def test_mv2_default_wiring_uses_mv2_replay_engine_source() -> None:
    result = _run()
    assert result.backtest_engine_signal_source == ENGINE_SIGNAL_SOURCE_MV2_REPLAY


def test_mv2_engine_signals_match_replay_series() -> None:
    result = _run()
    assert result.signals.astype(int).tolist() == result.mv2_replay_signals.astype(int).tolist()


def test_mv2_replay_parity_assertion_passes_on_default_path() -> None:
    result = _run()
    assert_backtest_engine_mv2_replay_signal_parity_v1(
        mv2_replay_signals=result.mv2_replay_signals,
        bar_outcomes=result.bar_outcomes,
        backtest_engine_signal_source=result.backtest_engine_signal_source,
        backtest_engine_signal_digest=result.backtest_engine_signal_digest,
        mv2_replay_signal_digest=result.mv2_replay_signal_digest,
    )


def test_decision_funnel_trade_alignment_passes_on_default_path() -> None:
    result = _run()
    assert_decision_funnel_trade_alignment_v1(
        bar_outcomes=result.bar_outcomes,
        engine_signals=result.signals,
        backtest_engine_signal_source=result.backtest_engine_signal_source,
        backtest_result=result.backtest_result,
    )


def test_parallel_strategy_signal_does_not_control_engine_when_divergent() -> None:
    result = _run()
    divergent_strategy = pd.Series(1, index=result.signals.index, dtype=int)
    assert divergent_strategy.astype(int).tolist() != result.mv2_replay_signals.astype(int).tolist()
    assert_parallel_strategy_signal_does_not_control_engine_v1(
        strategy_signals=divergent_strategy,
        engine_signals=result.signals,
        mv2_replay_signals=result.mv2_replay_signals,
        backtest_engine_signal_source=result.backtest_engine_signal_source,
    )


def test_legacy_configured_strategy_source_still_available_explicitly() -> None:
    result = _run(
        cfg=_cfg(engine_signal_source=ENGINE_SIGNAL_SOURCE_CONFIGURED_STRATEGY),
        allow_legacy_raw_signal_research_engine_source=True,
        system_economic_evidence_requested=False,
    )
    assert result.backtest_engine_signal_source == ENGINE_SIGNAL_SOURCE_CONFIGURED_STRATEGY
    assert (
        result.strategy_signal_provenance.engine_signal_source
        == ENGINE_SIGNAL_SOURCE_CONFIGURED_STRATEGY
    )


def test_configured_strategy_cannot_override_replay_as_system_engine_source() -> None:
    with pytest.raises(
        StrategySignalBindingError,
        match="legacy_raw_signal_path_system_economic_evidence_blocked",
    ):
        _run(cfg=_cfg(engine_signal_source=ENGINE_SIGNAL_SOURCE_CONFIGURED_STRATEGY))


def test_artificial_strategy_signal_mutation_does_not_change_engine_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bars = _bars()
    baseline = _run(bars=bars)
    mutated = pd.Series(1, index=bars.index, dtype=int)

    def _mutated_strategy(*_args: Any, **_kwargs: Any):
        from src.backtest.strategy_signal_binding_v1 import StrategySignalBindingResultV1

        return StrategySignalBindingResultV1(
            signals=mutated,
            provenance=baseline.strategy_signal_provenance,
        )

    monkeypatch.setattr(
        wiring,
        "execute_configured_strategy_signal_series_v1",
        _mutated_strategy,
    )
    result = _run(bars=bars)
    assert result.backtest_engine_signal_source == ENGINE_SIGNAL_SOURCE_MV2_REPLAY
    assert result.signals.astype(int).tolist() == result.mv2_replay_signals.astype(int).tolist()
    assert mutated.astype(int).tolist() != result.signals.astype(int).tolist()


def test_path_classification_constants() -> None:
    assert CANONICAL_SYSTEM_ENGINE_SIGNAL_SOURCE == ENGINE_SIGNAL_SOURCE_MV2_REPLAY
    assert (
        LEGACY_RAW_SIGNAL_RESEARCH_ENGINE_SIGNAL_SOURCE == ENGINE_SIGNAL_SOURCE_CONFIGURED_STRATEGY
    )
    assert CANONICAL_MV2_SYSTEM_PATH_CLASSIFICATION == "CANONICAL_SYSTEM_REPLAY"
    assert RUN_BACKTEST_PATH_CLASSIFICATION == "RAW_SIGNAL_RESEARCH"


def test_run_backtest_script_documents_legacy_classification() -> None:
    text = (wiring.__file__).replace(
        "src/backtest/mv2_research_wiring_v1.py",
        "scripts/run_backtest.py",
    )
    from pathlib import Path

    content = Path(text).read_text(encoding="utf-8")
    assert "RAW_SIGNAL_RESEARCH" in content
    assert "CANONICAL_SYSTEM_REPLAY" in content


def _bars_microsecond_utc(n: int = 12) -> pd.DataFrame:
    """Synthetic parquet-like bars index: datetime64[us, UTC] with name."""
    idx = pd.DatetimeIndex(
        pd.to_datetime(
            [f"2026-06-01T{hour:02d}:00:00Z" for hour in range(n)],
            utc=True,
        )
    ).astype("datetime64[us, UTC]")
    idx = pd.to_datetime(idx, utc=True)
    idx.name = "timestamp"
    assert str(idx.dtype) == "datetime64[us, UTC]"
    close = [100.0 + float(i) for i in range(n)]
    return pd.DataFrame(
        {
            "open": close,
            "high": [v + 0.5 for v in close],
            "low": [v - 0.5 for v in close],
            "close": close,
            "mark_price": close,
            "index_price": [v - 0.1 for v in close],
            "best_bid": [v - 0.05 for v in close],
            "best_ask": [v + 0.05 for v in close],
            "spread": [0.1 for _ in close],
            "volume": [1000.0 for _ in close],
            "open_interest": [10000.0 for _ in close],
            "funding_rate": [0.0001 for _ in close],
            "volatility_estimate": [0.2 for _ in close],
            "is_final": [True for _ in close],
            "bar_interval": ["1m" for _ in close],
        },
        index=idx,
    )


def test_mv2_replay_preserves_canonical_microsecond_utc_bars_index() -> None:
    bars = _bars_microsecond_utc()
    result = _run(bars=bars)
    signal_index = result.mv2_replay_signals.index
    assert signal_index.equals(bars.index)
    assert str(signal_index.dtype) == str(bars.index.dtype) == "datetime64[us, UTC]"
    assert str(signal_index.tz) == str(bars.index.tz) == "UTC"
    assert signal_index.name == bars.index.name == "timestamp"
    assert len(signal_index) == len(bars.index)
    assert list(signal_index) == list(bars.index)
    validated, _provenance = validate_mv2_replay_engine_signal_contract_v1(
        result.mv2_replay_signals,
        bars_index=bars.index,
        strategy_id="ma_crossover",
        mv2_replay_signal_digest=result.mv2_replay_signal_digest,
    )
    assert validated.index.equals(bars.index)
    assert result.signals.index.equals(bars.index)


def test_manual_timestamp_list_reconstruction_may_promote_us_to_ns() -> None:
    """Document why wiring must reuse bars.index instead of rebuilding DatetimeIndex."""
    bars_index = _bars_microsecond_utc(n=3).index
    reconstructed = pd.DatetimeIndex([pd.Timestamp(ts) for ts in bars_index])
    if str(reconstructed.dtype) == str(bars_index.dtype):
        pytest.skip(
            "installed pandas preserved datetime unit under Timestamp-list reconstruction; "
            "promotion guard not applicable"
        )
    assert str(bars_index.dtype) == "datetime64[us, UTC]"
    assert str(reconstructed.dtype) == "datetime64[ns, UTC]"
    assert (reconstructed == bars_index).all()
    assert not reconstructed.equals(bars_index)
    signals = pd.Series([0, 1, 0], index=reconstructed, dtype=int)
    with pytest.raises(StrategySignalBindingError, match="mv2_replay_signal_index_mismatch"):
        validate_mv2_replay_engine_signal_contract_v1(
            signals,
            bars_index=bars_index,
            strategy_id="ma_crossover",
            mv2_replay_signal_digest="a" * 64,
        )
