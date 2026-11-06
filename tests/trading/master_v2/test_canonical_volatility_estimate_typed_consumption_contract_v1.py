"""Unit and contract tests for typed volatility estimate consumption v1."""

from __future__ import annotations

import math
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import pytest

from src.trading.master_v2 import canonical_volatility_estimate_feature_contract_v1 as contract
from src.trading.master_v2 import canonical_volatility_estimate_materializer_v1 as materializer
from src.trading.master_v2 import (
    canonical_volatility_estimate_typed_consumption_contract_v1 as typed,
)

ROOT = Path(__file__).resolve().parents[3]
AS_OF = datetime(2026, 6, 1, 1, 0, tzinfo=timezone.utc)


def _valid_kwargs(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "value": 0.001234,
        "observation_count": 60,
        "as_of_event_time": AS_OF,
        "fallback_used": False,
    }
    base.update(overrides)
    return base


def _valid_estimate(**overrides: object) -> typed.CanonicalVolatilityEstimateV1:
    return typed.build_canonical_volatility_estimate_v1(**_valid_kwargs(**overrides))  # type: ignore[arg-type]


def test_package_marker_and_owners() -> None:
    assert typed.PACKAGE_MARKER.endswith("=true")
    assert typed.SEMANTICS_OWNER == contract.CONTRACT_OWNER
    assert typed.ESTIMATOR_OWNER == materializer.MATERIALIZER_OWNER
    assert typed.CANONICAL_UNIT == "PER_BAR_DECIMAL_RETURN_VOLATILITY"
    assert typed.CANONICAL_HORIZON_SECONDS == 3600
    assert typed.CANONICAL_ESTIMATOR == "POPULATION_STANDARD_DEVIATION_OF_LOG_RETURNS"
    assert typed.IMPLICIT_DEFAULT_ALLOWED is False
    assert typed.MV2_FALLBACK_0_2_ADMISSIBLE is False
    assert typed.RUNTIME_EFFECT is False
    assert typed.LIVE_AUTHORIZATION is False


def test_valid_canonical_estimate_accepted() -> None:
    estimate = _valid_estimate()
    assert estimate.value == pytest.approx(0.001234)
    assert estimate.fallback_used is False
    assert estimate.unit == typed.CANONICAL_UNIT
    assert estimate.horizon_seconds == 3600
    assert estimate.observation_count == 60


def test_zero_volatility_accepted_when_otherwise_valid() -> None:
    estimate = _valid_estimate(value=0.0)
    assert estimate.value == 0.0
    assert typed.adapt_canonical_volatility_estimate_to_legacy_float_v1(estimate) == 0.0


def test_carrier_immutable() -> None:
    estimate = _valid_estimate()
    with pytest.raises(Exception):
        estimate.value = 9.9  # type: ignore[misc]


def test_deterministic_source_digest() -> None:
    first = _valid_estimate(source_digest=None)
    second = _valid_estimate(source_digest=None)
    assert first.source_digest == second.source_digest
    assert len(first.source_digest) == 64


def test_materializer_output_wrapped_successfully() -> None:
    fixture = materializer.exact_known_61_price_fixture_v1()
    estimate = typed.materialize_typed_canonical_volatility_estimate_v1(fixture["mark_price"])
    expected = materializer.expected_population_std_for_fixture_v1(fixture["mark_price"].tolist())
    assert estimate.value == pytest.approx(expected)
    assert estimate.observation_count == 60
    assert estimate.fallback_used is False
    assert estimate.as_of_event_time.tzinfo is not None
    assert estimate.unit == typed.CANONICAL_UNIT
    assert estimate.contract_version == contract.CONTRACT_VERSION


def test_existing_materializer_semantics_unchanged() -> None:
    fixture = materializer.exact_known_61_price_fixture_v1()
    series = materializer.compute_canonical_volatility_estimate_from_mark_prices_v1(
        fixture["mark_price"]
    )
    expected = materializer.expected_population_std_for_fixture_v1(fixture["mark_price"].tolist())
    assert float(series.iloc[-1]) == pytest.approx(expected)
    assert series.iloc[:60].isna().all()
    assert contract.DDOF == 0
    assert contract.OUTPUT_ANNUALIZED is False
    assert contract.LOOKBACK_BARS == 60


@pytest.mark.parametrize(
    ("kwargs", "code"),
    [
        ({"value": None}, typed.CanonicalVolatilityTypedConsumptionErrorCode.MISSING_VALUE),
        ({"value": math.nan}, typed.CanonicalVolatilityTypedConsumptionErrorCode.NON_FINITE_VALUE),
        (
            {"value": math.inf},
            typed.CanonicalVolatilityTypedConsumptionErrorCode.NON_FINITE_VALUE,
        ),
        ({"value": -0.01}, typed.CanonicalVolatilityTypedConsumptionErrorCode.NEGATIVE_VALUE),
        (
            {"fallback_used": True},
            typed.CanonicalVolatilityTypedConsumptionErrorCode.FALLBACK_PROHIBITED,
        ),
        (
            {"unit": "ANNUALIZED_RETURN_VOLATILITY"},
            typed.CanonicalVolatilityTypedConsumptionErrorCode.UNIT_MISMATCH,
        ),
        (
            {"horizon_seconds": 60},
            typed.CanonicalVolatilityTypedConsumptionErrorCode.HORIZON_MISMATCH,
        ),
        (
            {"bar_interval_seconds": 300},
            typed.CanonicalVolatilityTypedConsumptionErrorCode.BAR_INTERVAL_MISMATCH,
        ),
        (
            {"lookback_bars": 20},
            typed.CanonicalVolatilityTypedConsumptionErrorCode.LOOKBACK_MISMATCH,
        ),
        (
            {"annualized": True},
            typed.CanonicalVolatilityTypedConsumptionErrorCode.ANNUALIZATION_MISMATCH,
        ),
        (
            {"estimator": "SAMPLE_STDEV"},
            typed.CanonicalVolatilityTypedConsumptionErrorCode.ESTIMATOR_MISMATCH,
        ),
        (
            {"observation_count": 59},
            typed.CanonicalVolatilityTypedConsumptionErrorCode.INSUFFICIENT_OBSERVATIONS,
        ),
        (
            {"as_of_event_time": datetime(2026, 6, 1, 1, 0)},
            typed.CanonicalVolatilityTypedConsumptionErrorCode.EVENT_TIME_INVALID,
        ),
        (
            {"source_digest": ""},
            typed.CanonicalVolatilityTypedConsumptionErrorCode.SOURCE_DIGEST_INVALID,
        ),
        (
            {"contract_version": "unsupported/v0"},
            typed.CanonicalVolatilityTypedConsumptionErrorCode.CONTRACT_VERSION_UNSUPPORTED,
        ),
    ],
)
def test_factory_rejects_invalid_inputs(kwargs: dict[str, object], code: object) -> None:
    with pytest.raises(typed.CanonicalVolatilityTypedConsumptionError) as exc:
        typed.build_canonical_volatility_estimate_v1(**_valid_kwargs(**kwargs))  # type: ignore[arg-type]
    assert exc.value.code == code


def test_numeric_0_2_accepted_when_canonically_proven() -> None:
    estimate = _valid_estimate(value=0.2)
    assert typed.adapt_canonical_volatility_estimate_to_legacy_float_v1(estimate) == 0.2


def test_numeric_0_02_accepted_when_canonically_proven() -> None:
    estimate = _valid_estimate(value=0.02)
    assert typed.adapt_canonical_volatility_estimate_to_legacy_float_v1(estimate) == 0.02


def test_numeric_1_0_accepted_when_canonically_proven() -> None:
    estimate = _valid_estimate(value=1.0)
    assert typed.adapt_canonical_volatility_estimate_to_legacy_float_v1(estimate) == 1.0


@pytest.mark.parametrize("raw", [0.2, 0.02, 1.0, 0.5, None])
def test_implicit_unproven_legacy_floats_rejected(raw: float | None) -> None:
    with pytest.raises(typed.CanonicalVolatilityTypedConsumptionError) as exc:
        typed.reject_implicit_legacy_float_input_v1(raw_value=raw, provenance=None)
    assert exc.value.code == typed.CanonicalVolatilityTypedConsumptionErrorCode.UNKNOWN_PROVENANCE


@pytest.mark.parametrize("raw", [0.2, 0.02, 1.0])
def test_implicit_fallback_flag_rejected(raw: float) -> None:
    with pytest.raises(typed.CanonicalVolatilityTypedConsumptionError) as exc:
        typed.reject_implicit_legacy_float_input_v1(
            raw_value=raw,
            provenance={"implicit_default": True, "typed_estimate": True},
        )
    assert (
        exc.value.code
        == typed.CanonicalVolatilityTypedConsumptionErrorCode.IMPLICIT_FALLBACK_REJECTED
    )


@pytest.mark.parametrize("raw", [0.2, 0.02, 1.0])
def test_mv2_fallback_provenance_rejected(raw: float) -> None:
    with pytest.raises(typed.CanonicalVolatilityTypedConsumptionError) as exc:
        typed.reject_implicit_legacy_float_input_v1(
            raw_value=raw,
            provenance={"fallback_used": True, "typed_estimate": True},
        )
    assert exc.value.code == typed.CanonicalVolatilityTypedConsumptionErrorCode.FALLBACK_PROHIBITED


def test_adapter_rejects_none_without_substitution() -> None:
    with pytest.raises(typed.CanonicalVolatilityTypedConsumptionError) as exc:
        typed.adapt_canonical_volatility_estimate_to_legacy_float_v1(None)
    assert exc.value.code == typed.CanonicalVolatilityTypedConsumptionErrorCode.MISSING_VALUE
    assert "no_substitution" in str(exc.value)


def test_adapter_rejects_fallback_used_carrier() -> None:
    estimate = typed.with_mutated_field_for_tests_v1(_valid_estimate(), fallback_used=True)
    with pytest.raises(typed.CanonicalVolatilityTypedConsumptionError) as exc:
        typed.adapt_canonical_volatility_estimate_to_legacy_float_v1(estimate)
    assert exc.value.code == typed.CanonicalVolatilityTypedConsumptionErrorCode.FALLBACK_PROHIBITED


def test_adapter_output_equals_validated_estimate_value() -> None:
    estimate = _valid_estimate(value=0.004321)
    assert typed.adapt_canonical_volatility_estimate_to_legacy_float_v1(estimate) == 0.004321


def test_adapter_performs_no_substitution_for_wrong_unit() -> None:
    estimate = typed.with_mutated_field_for_tests_v1(
        _valid_estimate(),
        unit="PERCENT_VOLATILITY",
    )
    with pytest.raises(typed.CanonicalVolatilityTypedConsumptionError) as exc:
        typed.adapt_canonical_volatility_estimate_to_legacy_float_v1(estimate)
    assert exc.value.code == typed.CanonicalVolatilityTypedConsumptionErrorCode.UNIT_MISMATCH


def test_adapter_rejects_annualized_and_wrong_horizon() -> None:
    annualized = typed.with_mutated_field_for_tests_v1(_valid_estimate(), annualized=True)
    with pytest.raises(typed.CanonicalVolatilityTypedConsumptionError) as exc:
        typed.adapt_canonical_volatility_estimate_to_legacy_float_v1(annualized)
    assert (
        exc.value.code == typed.CanonicalVolatilityTypedConsumptionErrorCode.ANNUALIZATION_MISMATCH
    )

    wrong_horizon = typed.with_mutated_field_for_tests_v1(_valid_estimate(), horizon_seconds=60)
    with pytest.raises(typed.CanonicalVolatilityTypedConsumptionError) as exc2:
        typed.adapt_canonical_volatility_estimate_to_legacy_float_v1(wrong_horizon)
    assert exc2.value.code == typed.CanonicalVolatilityTypedConsumptionErrorCode.HORIZON_MISMATCH


def test_warmup_incomplete_materialization_rejected() -> None:
    idx = pd.date_range("2026-06-01T00:00:00Z", periods=30, freq="1min", tz="UTC")
    mark = pd.Series([100.0 + 0.1 * i for i in range(30)], index=idx)
    with pytest.raises(typed.CanonicalVolatilityTypedConsumptionError) as exc:
        typed.materialize_typed_canonical_volatility_estimate_v1(mark)
    assert exc.value.code == typed.CanonicalVolatilityTypedConsumptionErrorCode.WARMUP_INCOMPLETE


def test_explicit_contract_gates_machine_readable() -> None:
    goals = typed.assert_capability_non_goals_v1()
    assert goals["runtime_effect"] is False
    assert goals["trading_logic_effect"] is False
    assert goals["parameter_effect"] is False
    assert goals["live_authorization"] is False
    assert goals["implicit_default_allowed"] is False
    assert goals["mv2_fallback_0_2_admissible"] is False
    for gap in typed.OPEN_HOT_PATH_GAPS:
        assert gap in goals["open_hot_path_gaps"]
    for surface in typed.NON_ALIAS_VOLATILITY_SURFACES:
        assert surface in goals["non_alias_surfaces"]


def test_open_gaps_remain_documented_and_unclosed() -> None:
    assert len(typed.OPEN_HOT_PATH_GAPS) == 7
    assert "G1_SILENT_0_2_IN_HISTORICAL_BIND" not in typed.OPEN_HOT_PATH_GAPS
    assert "G2_SILENT_0_02_SCENARIO_INTEGRATED_DEFAULTS" not in typed.OPEN_HOT_PATH_GAPS
    assert "G6_MATERIALIZER_NOT_WIRED_TO_DOUBLE_PLAY" in typed.OPEN_HOT_PATH_GAPS
    assert "G9_FUTURES_PROFILE_PRIMARY_METRIC_OQ001_OPEN" in typed.OPEN_HOT_PATH_GAPS


def test_composition_entry_exit_and_runtime_paths_unchanged() -> None:
    guarded = (
        "src/trading/master_v2/double_play_composition.py",
        "src/trading/master_v2/double_play_entry_exit_policy_v0.py",
        "src/trading/master_v2/canonical_core_runtime_integration_bridge_v0.py",
        "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py",
        "src/trading/master_v2/offline_double_play_scenario_replay_v0.py",
        "src/trading/master_v2/double_play_state.py",
        "src/trading/master_v2/double_play_survival.py",
        "src/trading/master_v2/double_play_suitability.py",
        "src/trading/master_v2/canonical_volatility_estimate_feature_contract_v1.py",
        "src/trading/master_v2/canonical_volatility_estimate_materializer_v1.py",
    )
    needle = "canonical_volatility_estimate_typed_consumption_contract_v1"
    for rel in guarded:
        text = (ROOT / rel).read_text(encoding="utf-8")
        assert needle not in text, rel


def test_second_estimator_not_created() -> None:
    src = (
        ROOT
        / "src/trading/master_v2/canonical_volatility_estimate_typed_consumption_contract_v1.py"
    ).read_text(encoding="utf-8")
    assert "compute_canonical_volatility_estimate_from_mark_prices_v1" in src
    assert "rolling(" not in src
    assert ".std(" not in src
    assert "_compute_log_returns" not in src


def test_capability_spec_exists() -> None:
    path = (
        ROOT
        / "docs/ops/specs/MASTER_V2_CANONICAL_VOLATILITY_ESTIMATE_TYPED_CONSUMPTION_CONTRACT_V1.md"
    )
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert "SEMANTICS_OWNER" in text
    assert "RUNTIME_EFFECT=false" in text
    assert "G6_MATERIALIZER_NOT_WIRED_TO_DOUBLE_PLAY" in text
    assert "G9_FUTURES_PROFILE_PRIMARY_METRIC_OQ001_OPEN" in text
