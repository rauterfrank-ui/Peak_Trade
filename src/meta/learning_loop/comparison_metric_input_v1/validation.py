"""Manifest validation for comparison_metric_input.v1."""

from __future__ import annotations

import math
from typing import Any, Mapping

from src.meta.learning_loop.comparison_metric_input_v1.constants import (
    ALLOWED_SOURCE_DOMAINS,
    ANNUALIZATION_PROFILE_V1,
    CANONICAL_AUTHORITY_INVARIANTS,
    COMPARABILITY_METADATA_VERSION,
    COMPARISON_METRIC_INPUT_CONTRACT_VERSION,
    METRIC_KEYS,
    METRIC_SEMANTICS_VERSION,
    METRIC_SET_VERSION,
)
from src.meta.learning_loop.comparison_metric_input_v1.identity import (
    verify_manifest_identity_and_integrity,
)
from src.meta.learning_loop.comparison_metric_input_v1.models import ComparisonMetricInputError
from src.meta.learning_loop.comparison_metric_input_v1.source_binding import verify_source_ref
from src.meta.learning_loop.contract_safety_v1 import is_valid_sha256_hex

_REQUIRED_TOP_LEVEL = (
    "comparison_metric_input_contract_version",
    "metric_set_version",
    "metric_semantics_version",
    "comparability_metadata_version",
    "source_domain",
    "source_ref",
    "source_digest",
    "evaluation_slice_id",
    "comparability_metadata",
    "metrics",
    "authority_invariants",
    "integrity",
)

_COMPARABILITY_REQUIRED = (
    "timeframe",
    "evaluation_start",
    "evaluation_end",
    "universe",
    "instrument_set",
    "dataset_lineage_ref",
    "dataset_lineage_digest",
    "fee_model",
    "fee_parameters",
    "slippage_model",
    "slippage_parameters",
    "risk_policy_ref",
    "initial_capital",
    "capital_currency",
    "result_currency",
    "equity_sampling_frequency",
    "annualization_profile",
    "return_basis",
    "risk_free_rate_annualized",
    "metric_semantics_version",
    "source_schema_version",
    "source_domain",
    "evaluation_slice_id",
    "authority_invariants",
)


def _reject_unknown_keys(
    payload: Mapping[str, Any], *, allowed: frozenset[str], label: str
) -> None:
    unknown = set(payload) - allowed
    if unknown:
        raise ComparisonMetricInputError(f"{label} contains unknown keys: {sorted(unknown)}")


def _validate_finite_number(value: Any, *, field: str) -> None:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ComparisonMetricInputError(f"{field} must be numeric")
    if not math.isfinite(float(value)):
        raise ComparisonMetricInputError(f"{field} must be finite")


def validate_metrics_block(metrics: Any) -> None:
    if not isinstance(metrics, dict):
        raise ComparisonMetricInputError("metrics must be an object")
    _reject_unknown_keys(metrics, allowed=frozenset(METRIC_KEYS), label="metrics")
    for key in METRIC_KEYS:
        if key not in metrics:
            raise ComparisonMetricInputError(f"metrics missing required key: {key}")
    for key in ("sharpe", "profit_factor", "total_return", "volatility"):
        _validate_finite_number(metrics[key], field=f"metrics.{key}")
    _validate_finite_number(metrics["max_drawdown"], field="metrics.max_drawdown")
    max_dd = float(metrics["max_drawdown"])
    if max_dd < 0.0 or max_dd > 1.0:
        raise ComparisonMetricInputError("metrics.max_drawdown must be in [0, 1]")
    trade_count = metrics["trade_count"]
    if not isinstance(trade_count, int) or isinstance(trade_count, bool):
        raise ComparisonMetricInputError("metrics.trade_count must be integer")
    if trade_count < 0:
        raise ComparisonMetricInputError("metrics.trade_count must be non-negative")
    pf = float(metrics["profit_factor"])
    if pf < 0.0:
        raise ComparisonMetricInputError("metrics.profit_factor must be non-negative")
    vol = float(metrics["volatility"])
    if vol < 0.0:
        raise ComparisonMetricInputError("metrics.volatility must be non-negative")


def validate_comparability_metadata(metadata: Any, *, source_domain: str) -> None:
    if not isinstance(metadata, dict):
        raise ComparisonMetricInputError("comparability_metadata must be an object")
    allowed = frozenset(_COMPARABILITY_REQUIRED)
    _reject_unknown_keys(metadata, allowed=allowed, label="comparability_metadata")
    for key in _COMPARABILITY_REQUIRED:
        if key not in metadata:
            raise ComparisonMetricInputError(f"comparability_metadata missing {key}")
    timeframe = metadata["timeframe"]
    if not isinstance(timeframe, str) or not timeframe.strip():
        raise ComparisonMetricInputError("comparability_metadata.timeframe must be non-empty")
    if timeframe not in ANNUALIZATION_PROFILE_V1:
        raise ComparisonMetricInputError(f"unknown timeframe: {timeframe}")
    if metadata["annualization_profile"] != "annualization_profile_v1":
        raise ComparisonMetricInputError("annualization_profile must be annualization_profile_v1")
    if metadata["metric_semantics_version"] != METRIC_SEMANTICS_VERSION:
        raise ComparisonMetricInputError("metric_semantics_version mismatch")
    if metadata["source_domain"] != source_domain:
        raise ComparisonMetricInputError("comparability_metadata.source_domain mismatch")
    if metadata["risk_free_rate_annualized"] != 0.0:
        raise ComparisonMetricInputError("risk_free_rate_annualized must be exactly 0.0")
    if metadata["return_basis"] not in {"NET_EQUITY_CURVE", "GROSS_EQUITY_CURVE"}:
        raise ComparisonMetricInputError("invalid return_basis")
    initial_capital = metadata["initial_capital"]
    if not isinstance(initial_capital, (int, float)) or float(initial_capital) <= 0.0:
        raise ComparisonMetricInputError("initial_capital must be > 0")
    for key in ("universe", "instrument_set"):
        value = metadata[key]
        if not isinstance(value, list) or not value or not all(isinstance(v, str) for v in value):
            raise ComparisonMetricInputError(
                f"comparability_metadata.{key} must be non-empty string array"
            )
    digest = metadata["dataset_lineage_digest"]
    if digest != "NOT_APPLICABLE" and not is_valid_sha256_hex(str(digest)):
        raise ComparisonMetricInputError("dataset_lineage_digest must be sha256 or NOT_APPLICABLE")
    if not isinstance(metadata["fee_parameters"], dict):
        raise ComparisonMetricInputError("fee_parameters must be object")
    if not isinstance(metadata["slippage_parameters"], dict):
        raise ComparisonMetricInputError("slippage_parameters must be object")
    if not isinstance(metadata["authority_invariants"], dict):
        raise ComparisonMetricInputError(
            "comparability_metadata.authority_invariants must be object"
        )


def validate_authority_invariants(block: Any) -> None:
    if not isinstance(block, dict):
        raise ComparisonMetricInputError("authority_invariants must be an object")
    allowed = frozenset(CANONICAL_AUTHORITY_INVARIANTS)
    _reject_unknown_keys(block, allowed=allowed, label="authority_invariants")
    for key, expected in CANONICAL_AUTHORITY_INVARIANTS.items():
        if block.get(key) != expected:
            raise ComparisonMetricInputError(
                f"authority_invariants.{key} must equal canonical value"
            )


def validate_var_suite_companion(block: Any | None, *, source_domain: str) -> None:
    if source_domain != "VAR_SUITE":
        if block is not None:
            raise ComparisonMetricInputError("var_suite_companion only allowed for VAR_SUITE")
        return
    if not isinstance(block, dict):
        raise ComparisonMetricInputError("var_suite_companion required for VAR_SUITE")
    allowed = frozenset(
        {"companion_required", "wired_backtest_lineage_ref", "suite_report_lineage_ref"}
    )
    _reject_unknown_keys(block, allowed=allowed, label="var_suite_companion")
    if block.get("companion_required") is not True:
        raise ComparisonMetricInputError("var_suite_companion.companion_required must be true")
    wired = block["wired_backtest_lineage_ref"]
    suite = block["suite_report_lineage_ref"]
    verify_source_ref(wired, expected_domain="BACKTEST")
    verify_source_ref(suite, expected_domain="VAR_SUITE")


def validate_comparison_metric_input_manifest_v1(manifest: Mapping[str, Any]) -> None:
    if not isinstance(manifest, dict):
        raise ComparisonMetricInputError("manifest root must be object")
    allowed_top = frozenset(
        _REQUIRED_TOP_LEVEL + ("comparison_metric_input_id", "var_suite_companion")
    )
    _reject_unknown_keys(manifest, allowed=allowed_top, label="manifest")
    for key in _REQUIRED_TOP_LEVEL:
        if key not in manifest:
            raise ComparisonMetricInputError(f"manifest missing required field: {key}")
    if (
        manifest["comparison_metric_input_contract_version"]
        != COMPARISON_METRIC_INPUT_CONTRACT_VERSION
    ):
        raise ComparisonMetricInputError("comparison_metric_input_contract_version mismatch")
    if manifest["metric_set_version"] != METRIC_SET_VERSION:
        raise ComparisonMetricInputError("metric_set_version mismatch")
    if manifest["metric_semantics_version"] != METRIC_SEMANTICS_VERSION:
        raise ComparisonMetricInputError("metric_semantics_version mismatch")
    if manifest["comparability_metadata_version"] != COMPARABILITY_METADATA_VERSION:
        raise ComparisonMetricInputError("comparability_metadata_version mismatch")
    source_domain = manifest["source_domain"]
    if source_domain not in ALLOWED_SOURCE_DOMAINS:
        raise ComparisonMetricInputError(f"unknown source_domain: {source_domain}")
    verify_source_ref(manifest["source_ref"], expected_domain=str(source_domain))
    source_digest = manifest["source_digest"]
    if not is_valid_sha256_hex(str(source_digest)):
        raise ComparisonMetricInputError("source_digest must be lowercase sha256 hex")
    evaluation_slice_id = manifest["evaluation_slice_id"]
    if not isinstance(evaluation_slice_id, str) or not evaluation_slice_id.strip():
        raise ComparisonMetricInputError("evaluation_slice_id must be non-empty")
    validate_metrics_block(manifest["metrics"])
    validate_comparability_metadata(
        manifest["comparability_metadata"], source_domain=str(source_domain)
    )
    if manifest["comparability_metadata"]["evaluation_slice_id"] != evaluation_slice_id:
        raise ComparisonMetricInputError(
            "evaluation_slice_id mismatch between top-level and metadata"
        )
    validate_authority_invariants(manifest["authority_invariants"])
    validate_var_suite_companion(
        manifest.get("var_suite_companion"),
        source_domain=str(source_domain),
    )
    if "comparison_metric_input_id" in manifest:
        verify_manifest_identity_and_integrity(manifest)
