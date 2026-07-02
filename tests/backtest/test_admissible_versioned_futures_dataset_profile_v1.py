"""RUNBOOK STEP 29M — dataset profile contract v1 tests."""

from __future__ import annotations

from typing import Any

import pandas as pd
import pytest

from src.backtest import admissible_versioned_futures_dataset_v1 as ds
from src.backtest import cost_config_v0 as cost
from src.backtest import mv2_research_wiring_v1 as wiring


def _runtime_bars(n: int = 24) -> pd.DataFrame:
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
            "volume": [1000.0 for _ in close],
            "funding_rate": [0.0001 for _ in close],
            "is_final": [True for _ in close],
        },
        index=idx,
    )


def _research_bars(n: int = 24) -> pd.DataFrame:
    frame = _runtime_bars(n)
    return frame.drop(columns=["best_bid", "best_ask"])


def _provenance(**overrides: Any) -> ds.DatasetProvenanceV1:
    payload = {
        "source_type": "synthetic_contract_fixture",
        "venue_id": "offline_fixture_venue_v1",
        "ingestion_timestamp": "1970-01-01T00:00:00+00:00",
        "generation_method": "deterministic_test_fixture",
        "provenance_ref": "tests/backtest/test_admissible_versioned_futures_dataset_profile_v1.py",
    }
    payload.update(overrides)
    return ds.DatasetProvenanceV1(**payload)


def _descriptor(
    bars: pd.DataFrame,
    *,
    profile: ds.DatasetProfileV1,
    **overrides: Any,
) -> ds.VersionedFuturesDatasetDescriptorV1:
    bindings = ds.field_bindings_for_profile(profile)
    digest = ds.compute_versioned_dataset_digest(bars, field_bindings=bindings)
    train, val, oos = ds.compute_split_periods_from_bars(bars)
    idx = bars.sort_index().index
    payload: dict[str, Any] = {
        "dataset_id": "step29m_profile_fixture_eth_perp_v1",
        "dataset_version": ds.DEFAULT_DATASET_VERSION,
        "dataset_schema_version": ds.DATASET_SCHEMA_VERSION,
        "dataset_digest": digest,
        "instrument_id": wiring.MV2_REQUIRED_INSTRUMENT_ID,
        "contract_type": "perpetual",
        "futures_only": True,
        "bitcoin_direction_allowed": False,
        "venue_id": "offline_fixture_venue_v1",
        "start_time": str(idx[0]),
        "end_time": str(idx[-1]),
        "row_count": len(bars),
        "field_bindings": bindings,
        "training_period": train,
        "validation_period": val,
        "out_of_sample_period": oos,
        "split_policy_version": ds.SPLIT_POLICY_VERSION,
        "timestamp_semantics": ds.TIMESTAMP_SEMANTICS,
        "timezone": ds.TIMEZONE,
        "ordering_status": ds.ORDERING_STATUS_SORTED,
        "duplicate_policy": ds.DUPLICATE_POLICY,
        "missing_data_policy": ds.MISSING_DATA_POLICY,
    }
    payload.update(overrides)
    field_bindings = payload.pop("field_bindings")
    if isinstance(field_bindings, ds.DatasetFieldBindingsV1):
        bindings = field_bindings
    else:
        bindings = ds.DatasetFieldBindingsV1(**field_bindings)
    return ds.VersionedFuturesDatasetDescriptorV1(field_bindings=bindings, **payload)


def _research_profile_binding() -> ds.DatasetProfileBindingV1:
    return ds.DatasetProfileBindingV1(
        dataset_profile=ds.DatasetProfileV1.ECONOMIC_RESEARCH_V1,
        l1_observation_status=ds.L1ObservationStatusV1.EXECUTION_MODEL_BOUND_NOT_OBSERVED,
        execution_cost_binding=ds.ExecutionCostBindingV1(
            spread_model_version=cost.RESEARCH_SPREAD_MODEL_VERSION,
            execution_price_observation_source=cost.EXECUTION_PRICE_OBSERVATION_SOURCE_MODELLED,
            conservative_half_spread_bps=5.0,
        ),
    )


class TestDatasetProfileContract:
    def test_runtime_profile_admissible_with_observed_l1(self) -> None:
        bars = _runtime_bars()
        result = ds.evaluate_admissible_versioned_futures_dataset_v1(
            bars=bars,
            descriptor=_descriptor(bars, profile=ds.DatasetProfileV1.RUNTIME_MARKET_CONTEXT_V1),
            provenance=_provenance(),
            instrument_id=wiring.MV2_REQUIRED_INSTRUMENT_ID,
            profile_binding=ds.default_runtime_profile_binding_v1(),
        )
        assert result.is_admissible()
        assert result.dataset_profile == "runtime_market_context_v1"
        assert result.l1_observation_status == "OBSERVED_HISTORICAL_L1"

    def test_research_profile_admissible_without_l1_columns(self) -> None:
        bars = _research_bars()
        result = ds.evaluate_admissible_versioned_futures_dataset_v1(
            bars=bars,
            descriptor=_descriptor(bars, profile=ds.DatasetProfileV1.ECONOMIC_RESEARCH_V1),
            provenance=_provenance(),
            instrument_id=wiring.MV2_REQUIRED_INSTRUMENT_ID,
            profile_binding=_research_profile_binding(),
        )
        assert result.is_admissible()
        assert result.dataset_profile == "economic_research_v1"
        assert result.l1_observation_status == "EXECUTION_MODEL_BOUND_NOT_OBSERVED"
        assert result.profile_binding_digest

    def test_runtime_profile_blocks_missing_l1(self) -> None:
        bars = _research_bars()
        result = ds.evaluate_admissible_versioned_futures_dataset_v1(
            bars=bars,
            descriptor=_descriptor(bars, profile=ds.DatasetProfileV1.RUNTIME_MARKET_CONTEXT_V1),
            provenance=_provenance(),
            instrument_id=wiring.MV2_REQUIRED_INSTRUMENT_ID,
            profile_binding=ds.default_runtime_profile_binding_v1(),
        )
        assert result.admissibility_status is ds.AdmissibilityStatus.BLOCKED_L1_REQUIRED_FOR_RUNTIME

    def test_research_profile_blocks_missing_execution_cost_binding(self) -> None:
        bars = _research_bars()
        binding = ds.DatasetProfileBindingV1(
            dataset_profile=ds.DatasetProfileV1.ECONOMIC_RESEARCH_V1,
            l1_observation_status=ds.L1ObservationStatusV1.EXECUTION_MODEL_BOUND_NOT_OBSERVED,
            execution_cost_binding=None,
        )
        result = ds.evaluate_admissible_versioned_futures_dataset_v1(
            bars=bars,
            descriptor=_descriptor(bars, profile=ds.DatasetProfileV1.ECONOMIC_RESEARCH_V1),
            provenance=_provenance(),
            instrument_id=wiring.MV2_REQUIRED_INSTRUMENT_ID,
            profile_binding=binding,
        )
        assert (
            result.admissibility_status
            is ds.AdmissibilityStatus.BLOCKED_EXECUTION_COST_BINDING_MISSING
        )

    def test_runtime_profile_rejects_execution_model_bound_l1_status(self) -> None:
        bars = _runtime_bars()
        binding = ds.DatasetProfileBindingV1(
            dataset_profile=ds.DatasetProfileV1.RUNTIME_MARKET_CONTEXT_V1,
            l1_observation_status=ds.L1ObservationStatusV1.EXECUTION_MODEL_BOUND_NOT_OBSERVED,
            execution_cost_binding=None,
        )
        result = ds.evaluate_admissible_versioned_futures_dataset_v1(
            bars=bars,
            descriptor=_descriptor(bars, profile=ds.DatasetProfileV1.RUNTIME_MARKET_CONTEXT_V1),
            provenance=_provenance(),
            instrument_id=wiring.MV2_REQUIRED_INSTRUMENT_ID,
            profile_binding=binding,
        )
        assert result.admissibility_status is ds.AdmissibilityStatus.BLOCKED_L1_REQUIRED_FOR_RUNTIME

    def test_load_profile_binding_from_cfg_fail_closed(self) -> None:
        with pytest.raises(ds.AdmissibleVersionedFuturesDatasetError, match="dataset_profile"):
            ds.load_profile_binding_from_cfg(
                {"backtest": {"dataset_admissibility": {"bind": True}}}
            )

    def test_load_profile_binding_from_manifest_fail_closed(self) -> None:
        with pytest.raises(
            ds.AdmissibleVersionedFuturesDatasetError, match="manifest_dataset_profile"
        ):
            ds.load_profile_binding_from_manifest({"dataset": {}, "provenance": {}})

    def test_profile_binding_digest_changes_with_cost_binding(self) -> None:
        runtime = ds.default_runtime_profile_binding_v1()
        research = _research_profile_binding()
        assert ds.compute_profile_binding_digest(runtime) != ds.compute_profile_binding_digest(
            research
        )

    def test_research_alias_constant(self) -> None:
        assert ds.ADMISSIBLE_FUTURES_ECONOMIC_RESEARCH_DATASET_V1 == "economic_research_v1"

    def test_missing_historical_l1_reason_enum(self) -> None:
        assert (
            ds.MissingHistoricalL1ReasonV1.NOT_AVAILABLE_BY_PUBLIC_SOURCE.value
            == "NOT_AVAILABLE_BY_PUBLIC_SOURCE"
        )

    def test_schema_v2_allowed_for_research_profile(self) -> None:
        bars = _research_bars()
        bindings = ds.field_bindings_for_profile(ds.DatasetProfileV1.ECONOMIC_RESEARCH_V1)
        digest = ds.compute_versioned_dataset_digest(bars, field_bindings=bindings)
        train, val, oos = ds.compute_split_periods_from_bars(bars)
        idx = bars.sort_index().index
        descriptor = ds.VersionedFuturesDatasetDescriptorV1(
            dataset_id="fixture_v2",
            dataset_version="v2",
            dataset_schema_version=ds.DATASET_SCHEMA_VERSION_V2,
            dataset_digest=digest,
            instrument_id=wiring.MV2_REQUIRED_INSTRUMENT_ID,
            contract_type="perpetual",
            futures_only=True,
            bitcoin_direction_allowed=False,
            venue_id="offline_fixture_venue_v1",
            start_time=str(idx[0]),
            end_time=str(idx[-1]),
            row_count=len(bars),
            field_bindings=bindings,
            training_period=train,
            validation_period=val,
            out_of_sample_period=oos,
            split_policy_version=ds.SPLIT_POLICY_VERSION,
            timestamp_semantics=ds.TIMESTAMP_SEMANTICS,
            timezone=ds.TIMEZONE,
            ordering_status=ds.ORDERING_STATUS_SORTED,
            duplicate_policy=ds.DUPLICATE_POLICY,
            missing_data_policy=ds.MISSING_DATA_POLICY,
        )
        result = ds.evaluate_admissible_versioned_futures_dataset_v1(
            bars=bars,
            descriptor=descriptor,
            provenance=_provenance(),
            instrument_id=wiring.MV2_REQUIRED_INSTRUMENT_ID,
            profile_binding=_research_profile_binding(),
        )
        assert result.is_admissible()


class TestResearchExecutionCostBinding:
    def test_resolve_research_execution_cost_binding(self) -> None:
        cfg = {
            "backtest": {
                "economic_research_execution_cost": {
                    "spread_model_version": cost.RESEARCH_SPREAD_MODEL_VERSION,
                    "execution_price_observation_source": (
                        cost.EXECUTION_PRICE_OBSERVATION_SOURCE_MODELLED
                    ),
                    "conservative_half_spread_bps": 5.0,
                }
            }
        }
        binding = cost.resolve_economic_research_execution_cost_binding(cfg)
        assert binding.spread_model_version == cost.RESEARCH_SPREAD_MODEL_VERSION
        assert binding.conservative_half_spread_bps == 5.0

    def test_roundtrip_cost_no_double_count(self) -> None:
        entry = cost.compute_effective_entry_cost_bps(
            fee_bps=10.0, slippage_bps=5.0, half_spread_bps=3.0
        )
        exit_cost = cost.compute_effective_exit_cost_bps(
            fee_bps=10.0, slippage_bps=5.0, half_spread_bps=3.0
        )
        roundtrip = cost.compute_effective_roundtrip_cost_bps(
            fee_bps=10.0, slippage_bps=5.0, half_spread_bps=3.0
        )
        assert roundtrip == entry + exit_cost
        assert roundtrip == 36.0
