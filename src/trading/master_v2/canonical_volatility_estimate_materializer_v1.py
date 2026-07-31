"""Canonical volatility_estimate materializer v1 (CanonicalMarketContextV1 feature path).

Narrow deterministic adapter over rolling-window mechanics from
``src/analytics/regimes.py::_compute_rolling_volatility``. Computes and persists
contract-bound ``volatility_estimate`` from finalized PT1M ``mark_price`` only.
Offline-only; no runtime authority.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd

from src.analytics.regimes import _compute_log_returns
from src.trading.master_v2 import canonical_volatility_estimate_feature_contract_v1 as contract

MATERIALIZER_VERSION = "canonical_volatility_estimate_materializer_v1"
MATERIALIZER_OWNER = "trading.master_v2.canonical_volatility_estimate_materializer_v1"
SELECTED_CANONICAL_OWNER = contract.SELECTED_CANONICAL_OWNER
BAR_INTERVAL_SECONDS = 60
WARMUP_STATUS_COLUMN = "warmup_status"
VOLATILITY_CONTRACT_VERSION_COLUMN = "volatility_estimate_contract_version"


class CanonicalVolatilityEstimateMaterializerError(ValueError):
    """Fail-closed canonical volatility_estimate materializer error."""


class MaterializerRejectionReason(str, Enum):
    UNFINALIZED_BAR = "unfinalized_bar_rejected"
    MISSING_MARK_PRICE = "missing_mark_price_rejected"
    NONPOSITIVE_MARK_PRICE = "nonpositive_mark_price_rejected"
    NONCONTIGUOUS_PT1M = "noncontiguous_pt1m_window_rejected"
    CLOSE_PRICE_SUBSTITUTION = "close_price_cannot_substitute_mark_price"
    MARK_PRICE_COLUMN_MISSING = "mark_price_column_missing"


@dataclass(frozen=True)
class VolatilityMaterializationResultV1:
    bars: pd.DataFrame
    contract_version: str
    feature_name: str
    first_valid_index: pd.Timestamp | None
    warmup_null_count: int
    valid_value_count: int
    materializer_digest: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract_version": self.contract_version,
            "feature_name": self.feature_name,
            "first_valid_index": str(self.first_valid_index) if self.first_valid_index else None,
            "warmup_null_count": self.warmup_null_count,
            "valid_value_count": self.valid_value_count,
            "materializer_digest": self.materializer_digest,
            "materializer_owner": MATERIALIZER_OWNER,
            "materializer_version": MATERIALIZER_VERSION,
        }


def _stable_digest(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _assert_pt1m_contiguity(index: pd.DatetimeIndex) -> None:
    if len(index) <= 1:
        return
    deltas = index.to_series().diff().dropna().dt.total_seconds()
    if (deltas > BAR_INTERVAL_SECONDS).any():
        msg = MaterializerRejectionReason.NONCONTIGUOUS_PT1M.value
        raise CanonicalVolatilityEstimateMaterializerError(msg)


def validate_finalized_mark_price_inputs_v1(
    mark_prices: pd.Series,
    *,
    is_final: pd.Series | None = None,
    price_field: str = contract.PRICE_FIELD,
) -> None:
    if price_field != contract.PRICE_FIELD:
        msg = MaterializerRejectionReason.CLOSE_PRICE_SUBSTITUTION.value
        raise CanonicalVolatilityEstimateMaterializerError(msg)
    if is_final is not None and not bool(is_final.all()):
        msg = MaterializerRejectionReason.UNFINALIZED_BAR.value
        raise CanonicalVolatilityEstimateMaterializerError(msg)
    if mark_prices.isna().any():
        msg = MaterializerRejectionReason.MISSING_MARK_PRICE.value
        raise CanonicalVolatilityEstimateMaterializerError(msg)
    if (mark_prices.astype(float) <= 0.0).any():
        msg = MaterializerRejectionReason.NONPOSITIVE_MARK_PRICE.value
        raise CanonicalVolatilityEstimateMaterializerError(msg)
    _assert_pt1m_contiguity(pd.DatetimeIndex(mark_prices.index))


def compute_canonical_volatility_estimate_from_mark_prices_v1(
    mark_prices: pd.Series,
    *,
    is_final: pd.Series | None = None,
) -> pd.Series:
    """Population stdev (ddof=0) of PT1M log returns; NULL warmup through bar 60."""
    validate_finalized_mark_price_inputs_v1(mark_prices, is_final=is_final)
    ordered = mark_prices.sort_index().astype(float)
    log_returns = _compute_log_returns(ordered)
    rolling_std = log_returns.rolling(
        window=contract.LOOKBACK_BARS,
        min_periods=contract.MIN_PERIODS,
    ).std(ddof=contract.DDOF)
    return rolling_std.rename(contract.FEATURE_NAME)


def materialize_volatility_estimate_on_bars_v1(
    bars: pd.DataFrame,
    *,
    mark_price_column: str = contract.PRICE_FIELD,
) -> VolatilityMaterializationResultV1:
    if mark_price_column not in bars.columns:
        msg = MaterializerRejectionReason.MARK_PRICE_COLUMN_MISSING.value
        raise CanonicalVolatilityEstimateMaterializerError(msg)
    if mark_price_column != contract.PRICE_FIELD:
        msg = MaterializerRejectionReason.CLOSE_PRICE_SUBSTITUTION.value
        raise CanonicalVolatilityEstimateMaterializerError(msg)

    frame = bars.sort_index().copy()
    is_final = frame["is_final"] if "is_final" in frame.columns else None
    volatility = compute_canonical_volatility_estimate_from_mark_prices_v1(
        frame[mark_price_column],
        is_final=is_final,
    )
    frame[contract.FEATURE_NAME] = volatility
    frame[WARMUP_STATUS_COLUMN] = np.where(
        volatility.isna(),
        contract.WARMUP_INCOMPLETE_STATUS,
        "WARMUP_COMPLETE",
    )
    frame[VOLATILITY_CONTRACT_VERSION_COLUMN] = contract.CONTRACT_VERSION

    warmup_null_count = int(volatility.isna().sum())
    valid = volatility.dropna()
    first_valid_index = valid.index[0] if not valid.empty else None
    digest_payload = {
        "owner": MATERIALIZER_OWNER,
        "contract_version": contract.CONTRACT_VERSION,
        "row_count": len(frame),
        "warmup_null_count": warmup_null_count,
        "valid_value_count": int(valid.shape[0]),
        "volatility_digest": _stable_digest(valid.astype(float).tolist()),
    }
    return VolatilityMaterializationResultV1(
        bars=frame,
        contract_version=contract.CONTRACT_VERSION,
        feature_name=contract.FEATURE_NAME,
        first_valid_index=first_valid_index,
        warmup_null_count=warmup_null_count,
        valid_value_count=int(valid.shape[0]),
        materializer_digest=_stable_digest(digest_payload),
    )


def exact_known_61_price_fixture_v1() -> pd.DataFrame:
    idx = pd.date_range("2026-06-01T00:00:00Z", periods=61, freq="1min", tz="UTC")
    mark_prices = [100.0 * math.exp(0.001 * i) for i in range(61)]
    close = [value * 0.99 for value in mark_prices]
    return pd.DataFrame(
        {
            "open": mark_prices,
            "high": mark_prices,
            "low": mark_prices,
            "close": close,
            "volume": [1000.0] * 61,
            "mark_price": mark_prices,
            "index_price": mark_prices,
            "funding_rate": [0.0001] * 61,
            "is_final": [True] * 61,
        },
        index=idx,
    )


def expected_population_std_for_fixture_v1(mark_prices: Sequence[float]) -> float:
    prices = pd.Series(mark_prices, dtype=float)
    log_returns = np.log(prices / prices.shift(1)).dropna()
    return float(log_returns.std(ddof=contract.DDOF))


def count_closed_return_observations_v1(
    mark_prices: pd.Series,
    *,
    as_of_index: Any,
) -> int:
    """Count log-return observations in the closed lookback window ending at as_of.

    Provenance helper for typed carriers. Does not change estimator semantics.
    """
    ordered = mark_prices.sort_index().astype(float).loc[:as_of_index]
    log_returns = _compute_log_returns(ordered).dropna()
    if log_returns.empty:
        return 0
    return int(len(log_returns.iloc[-contract.LOOKBACK_BARS :]))


def build_digest_dependency_graph_v1(
    *,
    bars: pd.DataFrame,
    field_bindings: Mapping[str, str],
    dataset_digest: str,
    materializer_result: VolatilityMaterializationResultV1,
) -> dict[str, Any]:
    from src.backtest import admissible_versioned_futures_dataset_v1 as ds

    contract_config = contract.load_contract_config_v1()
    implementation_digest = _stable_digest(
        {
            "owner": ds.ADMISSIBLE_VERSIONED_FUTURES_DATASET_OWNER,
            "contract_version": ds.ADMISSIBLE_VERSIONED_FUTURES_DATASET_VERSION,
            "dataset_schema_version": ds.DATASET_SCHEMA_VERSION,
            "split_policy_version": ds.SPLIT_POLICY_VERSION,
        }
    )
    return {
        "schema_version": "digest_dependency_graph.v1",
        "owner": MATERIALIZER_OWNER,
        "nodes": {
            "contract_config_digest": contract.compute_contract_digest_v1(contract_config),
            "materializer_digest": materializer_result.materializer_digest,
            "dataset_digest": dataset_digest,
            "field_bindings_digest": _stable_digest(dict(field_bindings)),
            "implementation_digest": implementation_digest,
        },
        "edges": [
            {"from": "contract_config_digest", "to": "materializer_digest"},
            {"from": "materializer_digest", "to": "dataset_digest"},
            {"from": "field_bindings_digest", "to": "dataset_digest"},
        ],
        "contract_version": contract.CONTRACT_VERSION,
        "feature_name": contract.FEATURE_NAME,
        "row_count": len(bars),
    }


def build_before_after_field_diff_v1(
    *,
    before_columns: Sequence[str],
    after_columns: Sequence[str],
) -> dict[str, Any]:
    before = set(before_columns)
    after = set(after_columns)
    return {
        "added_columns": sorted(after - before),
        "removed_columns": sorted(before - after),
        "unchanged_columns": sorted(before & after),
        "contract_version_column": VOLATILITY_CONTRACT_VERSION_COLUMN,
        "feature_column": contract.FEATURE_NAME,
    }


__all__ = [
    "BAR_INTERVAL_SECONDS",
    "CanonicalVolatilityEstimateMaterializerError",
    "MaterializerRejectionReason",
    "MATERIALIZER_OWNER",
    "MATERIALIZER_VERSION",
    "SELECTED_CANONICAL_OWNER",
    "VOLATILITY_CONTRACT_VERSION_COLUMN",
    "WARMUP_STATUS_COLUMN",
    "VolatilityMaterializationResultV1",
    "build_before_after_field_diff_v1",
    "build_digest_dependency_graph_v1",
    "compute_canonical_volatility_estimate_from_mark_prices_v1",
    "count_closed_return_observations_v1",
    "exact_known_61_price_fixture_v1",
    "expected_population_std_for_fixture_v1",
    "materialize_volatility_estimate_on_bars_v1",
    "validate_finalized_mark_price_inputs_v1",
]
