"""Contract and materialization tests for canonical volatility_estimate feature v1."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.backtest import admissible_versioned_futures_dataset_v1 as ds
from src.trading.master_v2 import canonical_volatility_estimate_feature_contract_v1 as contract
from src.trading.master_v2 import canonical_volatility_estimate_materializer_v1 as materializer

ROOT = Path(__file__).resolve().parents[3]
CONTRACT_PATH = ROOT / contract.CONTRACT_CONFIG_REL_PATH


def test_contract_config_exists_and_implementation_admissible() -> None:
    payload = contract.load_contract_config_v1()
    parsed = contract.parse_contract_v1(payload)
    assert parsed.contract_version == contract.CONTRACT_VERSION
    assert parsed.verdict == contract.RATIFIED_VERDICT
    assert parsed.owner_ratification_complete is True
    assert parsed.implementation_admissible is True


def test_contract_forbids_implicit_defaults_and_mv2_fallback() -> None:
    parsed = contract.load_ratified_contract_v1()
    assert parsed.implicit_default_allowed is False
    assert parsed.mv2_fallback_0_2_admissible is False
    assert parsed.annualization_mode == "NONE"
    assert parsed.annualization_factor == 1
    assert parsed.ddof == 0
    assert parsed.min_periods == contract.LOOKBACK_BARS == 60


def test_contract_binds_mark_price_log_return_semantics() -> None:
    parsed = contract.load_ratified_contract_v1()
    assert parsed.primary_price_source == "VENUE_MARK_PRICE"
    assert parsed.price_field == "mark_price"
    assert parsed.return_definition == "LOG_RETURN"
    assert parsed.return_formula == "ln(mark_price_t/mark_price_t_minus_1)"
    assert parsed.bar_interval == "PT1M"
    assert parsed.output_unit == "PER_BAR_DECIMAL_RETURN_VOLATILITY"
    assert parsed.output_annualized is False


def test_contract_reuse_basis_is_narrow_adapter_only() -> None:
    parsed = contract.load_ratified_contract_v1()
    assert parsed.implementation_reuse_decision == "REUSE_WITH_NARROW_ADAPTER"
    assert parsed.reuse_basis == contract.REUSE_BASIS
    assert parsed.reuse_limitation == "ROLLING_WINDOW_MECHANICS_ONLY"


def test_assert_implementation_admissible_v1() -> None:
    ratified = contract.assert_implementation_admissible_v1()
    assert ratified.feature_name == "volatility_estimate"


def test_contract_config_digest_is_stable() -> None:
    payload = contract.load_contract_config_v1()
    first = contract.compute_contract_digest_v1(payload)
    second = contract.compute_contract_digest_v1(
        json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    )
    assert first == second


def test_validate_contract_config_v1_rejects_drift() -> None:
    payload = dict(contract.load_contract_config_v1())
    payload["lookback_bars"] = 20
    with pytest.raises(contract.CanonicalVolatilityFeatureContractError, match="lookback_bars"):
        contract.validate_contract_config_v1(payload)


def _bars_from_mark_prices(mark_prices: list[float]) -> pd.DataFrame:
    idx = pd.date_range("2026-06-01T00:00:00Z", periods=len(mark_prices), freq="1min", tz="UTC")
    close = [value * 0.99 for value in mark_prices]
    return pd.DataFrame(
        {
            "open": mark_prices,
            "high": mark_prices,
            "low": mark_prices,
            "close": close,
            "volume": [1000.0] * len(mark_prices),
            "mark_price": mark_prices,
            "index_price": mark_prices,
            "funding_rate": [0.0001] * len(mark_prices),
            "is_final": [True] * len(mark_prices),
        },
        index=idx,
    )


def test_exact_known_61_price_fixture_population_std_ddof_0() -> None:
    fixture = materializer.exact_known_61_price_fixture_v1()
    result = materializer.materialize_volatility_estimate_on_bars_v1(fixture)
    expected = materializer.expected_population_std_for_fixture_v1(fixture["mark_price"].tolist())
    actual = float(result.bars["volatility_estimate"].iloc[-1])
    assert actual == pytest.approx(expected)
    assert result.valid_value_count == 1


def test_first_valid_value_at_price_61() -> None:
    fixture = materializer.exact_known_61_price_fixture_v1()
    result = materializer.materialize_volatility_estimate_on_bars_v1(fixture)
    assert result.first_valid_index == fixture.index[-1]
    assert result.warmup_null_count == 60


def test_prices_1_to_60_produce_null() -> None:
    fixture = materializer.exact_known_61_price_fixture_v1()
    result = materializer.materialize_volatility_estimate_on_bars_v1(fixture)
    assert result.bars["volatility_estimate"].iloc[:60].isna().all()


def test_nonpositive_mark_price_rejected() -> None:
    bars = _bars_from_mark_prices([100.0] * 61)
    bars.loc[bars.index[10], "mark_price"] = 0.0
    with pytest.raises(
        materializer.CanonicalVolatilityEstimateMaterializerError,
        match="nonpositive_mark_price_rejected",
    ):
        materializer.materialize_volatility_estimate_on_bars_v1(bars)


def test_missing_mark_price_rejected() -> None:
    bars = _bars_from_mark_prices([100.0] * 61)
    bars.loc[bars.index[10], "mark_price"] = np.nan
    with pytest.raises(
        materializer.CanonicalVolatilityEstimateMaterializerError,
        match="missing_mark_price_rejected",
    ):
        materializer.materialize_volatility_estimate_on_bars_v1(bars)


def test_noncontiguous_pt1m_window_rejected() -> None:
    idx = pd.DatetimeIndex(
        [
            "2026-06-01T00:00:00Z",
            "2026-06-01T00:01:00Z",
            "2026-06-01T00:03:00Z",
        ],
        tz="UTC",
    )
    bars = pd.DataFrame(
        {
            "mark_price": [100.0, 101.0, 102.0],
            "is_final": [True, True, True],
        },
        index=idx,
    )
    with pytest.raises(
        materializer.CanonicalVolatilityEstimateMaterializerError,
        match="noncontiguous_pt1m_window_rejected",
    ):
        materializer.compute_canonical_volatility_estimate_from_mark_prices_v1(bars["mark_price"])


def test_unfinalized_bar_rejected() -> None:
    bars = _bars_from_mark_prices([100.0 + i for i in range(70)])
    bars.loc[bars.index[0], "is_final"] = False
    with pytest.raises(
        materializer.CanonicalVolatilityEstimateMaterializerError,
        match="unfinalized_bar_rejected",
    ):
        materializer.materialize_volatility_estimate_on_bars_v1(bars)


def test_close_price_cannot_substitute_mark_price() -> None:
    bars = _bars_from_mark_prices([100.0 + i for i in range(70)])
    with pytest.raises(
        materializer.CanonicalVolatilityEstimateMaterializerError,
        match="close_price_cannot_substitute_mark_price",
    ):
        materializer.materialize_volatility_estimate_on_bars_v1(bars, mark_price_column="close")


def test_no_annualization() -> None:
    bars = _bars_from_mark_prices([100.0 + i + (i % 3) for i in range(90)])
    vol = materializer.compute_canonical_volatility_estimate_from_mark_prices_v1(bars["mark_price"])
    log_returns = np.log(bars["mark_price"] / bars["mark_price"].shift(1))
    manual = log_returns.rolling(60, min_periods=60).std(ddof=0)
    pd.testing.assert_series_equal(vol, manual, check_names=False)
    assert contract.ANNUALIZATION_MODE == "NONE"
    assert contract.ANNUALIZATION_FACTOR == 1


def test_no_clipping_or_floor() -> None:
    bars = _bars_from_mark_prices([100.0, 200.0, 100.0, 200.0] * 20)
    result = materializer.materialize_volatility_estimate_on_bars_v1(bars)
    valid = result.bars["volatility_estimate"].dropna()
    assert (valid > 0).any()
    assert valid.max() > 0.2


def test_no_implicit_fallback() -> None:
    bars = _bars_from_mark_prices([100.0 + i for i in range(70)])
    result = materializer.materialize_volatility_estimate_on_bars_v1(bars)
    warmup = result.bars["volatility_estimate"].iloc[:60]
    assert warmup.isna().all()
    assert not (warmup == 0.2).any()


def test_deterministic_output() -> None:
    bars = _bars_from_mark_prices([100.0 + 0.1 * i for i in range(90)])
    first = materializer.materialize_volatility_estimate_on_bars_v1(bars)
    second = materializer.materialize_volatility_estimate_on_bars_v1(bars)
    assert first.materializer_digest == second.materializer_digest
    pd.testing.assert_series_equal(
        first.bars["volatility_estimate"],
        second.bars["volatility_estimate"],
    )


def test_bars_parquet_persistence_roundtrip(tmp_path: Path) -> None:
    bars = _bars_from_mark_prices([100.0 + 0.1 * i for i in range(90)])
    result = materializer.materialize_volatility_estimate_on_bars_v1(bars)
    path = tmp_path / "bars.parquet"
    out = result.bars.reset_index().rename(columns={"index": "timestamp"})
    out.to_parquet(path, index=False)
    loaded = pd.read_parquet(path)
    assert "volatility_estimate" in loaded.columns
    assert loaded["volatility_estimate_contract_version"].iloc[-1] == contract.CONTRACT_VERSION


def test_contract_version_persisted() -> None:
    bars = _bars_from_mark_prices([100.0 + i for i in range(70)])
    result = materializer.materialize_volatility_estimate_on_bars_v1(bars)
    assert result.bars[materializer.VOLATILITY_CONTRACT_VERSION_COLUMN].unique().tolist() == [
        contract.CONTRACT_VERSION
    ]


def test_schema_consumer_compatibility_pass() -> None:
    bars = _bars_from_mark_prices([100.0 + 0.1 * i for i in range(90)])
    result = materializer.materialize_volatility_estimate_on_bars_v1(bars)
    bindings = ds.research_field_bindings_v1()
    digest = ds.compute_versioned_dataset_digest(result.bars, field_bindings=bindings)
    reason_codes: list[str] = []
    assert ds.validate_volatility_estimate_contract_column_v1(result.bars, reason_codes)
    assert reason_codes == []
    assert len(digest) == 64


def test_second_materialization_diff_empty() -> None:
    bars = _bars_from_mark_prices([100.0 + 0.2 * i for i in range(90)])
    first = materializer.materialize_volatility_estimate_on_bars_v1(bars)
    second = materializer.materialize_volatility_estimate_on_bars_v1(bars)
    diff = first.bars.compare(second.bars)
    assert diff.empty


def test_digest_dependency_graph_contains_contract_binding() -> None:
    bars = _bars_from_mark_prices([100.0 + 0.2 * i for i in range(90)])
    result = materializer.materialize_volatility_estimate_on_bars_v1(bars)
    bindings = ds.research_field_bindings_v1().to_dict()
    digest = ds.compute_versioned_dataset_digest(
        result.bars, field_bindings=ds.research_field_bindings_v1()
    )
    graph = materializer.build_digest_dependency_graph_v1(
        bars=result.bars,
        field_bindings=bindings,
        dataset_digest=digest,
        materializer_result=result,
    )
    assert graph["contract_version"] == contract.CONTRACT_VERSION
    assert graph["nodes"]["materializer_digest"] == result.materializer_digest
