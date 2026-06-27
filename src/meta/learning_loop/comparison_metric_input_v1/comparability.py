"""Shared comparability metadata extraction for comparison_metric_input.v1."""

from __future__ import annotations

from typing import Any, Mapping

from src.meta.learning_loop.comparison_metric_input_v1.constants import (
    COMPARABILITY_METADATA_VERSION,
    COMPARISON_METRIC_INPUT_AUTHORITY_FLAGS,
    METRIC_SEMANTICS_VERSION,
)
from src.meta.learning_loop.comparison_metric_input_v1.models import ComparisonMetricInputError
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256, is_valid_sha256_hex


def build_evaluation_slice_id(
    *,
    source_ref_id: str,
    evaluation_start: str,
    evaluation_end: str,
) -> str:
    payload = {
        "evaluation_end": evaluation_end,
        "evaluation_start": evaluation_start,
        "source_ref_id": source_ref_id,
    }
    return compute_content_sha256(payload)


def _require_str(mapping: Mapping[str, Any], key: str, *, label: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ComparisonMetricInputError(f"{label}.{key} must be non-empty string")
    return value


def _require_symbol_list(value: Any, *, label: str) -> list[str]:
    if not isinstance(value, list) or not value or not all(isinstance(v, str) for v in value):
        raise ComparisonMetricInputError(f"{label} must be non-empty string array")
    return list(value)


def build_comparability_metadata(
    *,
    source_domain: str,
    source_schema_version: str,
    timeframe: str,
    evaluation_start: str,
    evaluation_end: str,
    universe: list[str],
    instrument_set: list[str],
    dataset_lineage_ref: str,
    dataset_lineage_digest: str,
    fee_model: str,
    fee_parameters: dict[str, Any],
    slippage_model: str,
    slippage_parameters: dict[str, Any],
    risk_policy_ref: str,
    initial_capital: float,
    capital_currency: str,
    result_currency: str,
    return_basis: str,
    evaluation_slice_id: str,
) -> dict[str, Any]:
    if return_basis not in {"NET_EQUITY_CURVE", "GROSS_EQUITY_CURVE"}:
        raise ComparisonMetricInputError(
            "return_basis must be NET_EQUITY_CURVE or GROSS_EQUITY_CURVE"
        )
    if dataset_lineage_digest != "NOT_APPLICABLE" and not is_valid_sha256_hex(
        dataset_lineage_digest
    ):
        raise ComparisonMetricInputError(
            "dataset_lineage_digest must be sha256 hex or NOT_APPLICABLE"
        )
    if initial_capital <= 0.0:
        raise ComparisonMetricInputError("initial_capital must be > 0")
    return {
        "timeframe": timeframe,
        "evaluation_start": evaluation_start,
        "evaluation_end": evaluation_end,
        "universe": universe,
        "instrument_set": instrument_set,
        "dataset_lineage_ref": dataset_lineage_ref,
        "dataset_lineage_digest": dataset_lineage_digest,
        "fee_model": fee_model,
        "fee_parameters": fee_parameters,
        "slippage_model": slippage_model,
        "slippage_parameters": slippage_parameters,
        "risk_policy_ref": risk_policy_ref,
        "initial_capital": float(initial_capital),
        "capital_currency": capital_currency,
        "result_currency": result_currency,
        "equity_sampling_frequency": timeframe,
        "annualization_profile": "annualization_profile_v1",
        "return_basis": return_basis,
        "risk_free_rate_annualized": 0.0,
        "metric_semantics_version": METRIC_SEMANTICS_VERSION,
        "source_schema_version": source_schema_version,
        "source_domain": source_domain,
        "evaluation_slice_id": evaluation_slice_id,
        "authority_invariants": dict(COMPARISON_METRIC_INPUT_AUTHORITY_FLAGS),
        "comparability_metadata_version": COMPARABILITY_METADATA_VERSION,
    }


def comparability_from_backtest_config_snapshot(
    *,
    config_snapshot: Mapping[str, Any],
    run_summary_params: Mapping[str, Any],
    source_domain: str,
    source_ref_id: str,
    evaluation_start: str,
    evaluation_end: str,
) -> tuple[dict[str, Any], str]:
    meta = config_snapshot.get("meta")
    params = config_snapshot.get("params")
    if not isinstance(meta, dict) or not isinstance(params, dict):
        raise ComparisonMetricInputError("config_snapshot must contain meta and params objects")
    if "timeframe" in params:
        timeframe = _require_str(params, "timeframe", label="config_snapshot.params")
    elif "timeframe" in run_summary_params:
        timeframe = _require_str(run_summary_params, "timeframe", label="run_summary.params")
    else:
        raise ComparisonMetricInputError("timeframe missing from config_snapshot/run_summary")
    symbols = params.get("symbols")
    if symbols is None:
        symbols = run_summary_params.get("symbols")
    universe = _require_symbol_list(symbols, label="symbols")
    initial_capital = params.get("initial_capital", run_summary_params.get("initial_capital"))
    if initial_capital is None:
        raise ComparisonMetricInputError("initial_capital missing from config_snapshot/run_summary")
    if not isinstance(initial_capital, (int, float)) or float(initial_capital) <= 0.0:
        raise ComparisonMetricInputError("initial_capital must be > 0")
    quote = universe[0].split("/")[-1] if "/" in universe[0] else "USD"
    dataset_ref = str(meta.get("data_source") or meta.get("dataset_id") or "NOT_APPLICABLE")
    if dataset_ref == "NOT_APPLICABLE":
        dataset_digest = "NOT_APPLICABLE"
    else:
        dataset_digest = compute_content_sha256({"dataset_lineage_ref": dataset_ref})
    fee_model = str(params.get("fee_model") or meta.get("fee_model") or "PROVABLY_ZERO")
    slippage_model = str(
        params.get("slippage_model") or meta.get("slippage_model") or "PROVABLY_ZERO"
    )
    fee_parameters = params.get("fee_parameters")
    slippage_parameters = params.get("slippage_parameters")
    if not isinstance(fee_parameters, dict):
        fee_parameters = {}
    if not isinstance(slippage_parameters, dict):
        slippage_parameters = {}
    risk_policy_ref = str(
        params.get("risk_policy_ref") or meta.get("risk_policy_ref") or "NOT_APPLICABLE"
    )
    return_basis = str(params.get("return_basis") or meta.get("return_basis") or "NET_EQUITY_CURVE")
    evaluation_slice_id = build_evaluation_slice_id(
        source_ref_id=source_ref_id,
        evaluation_start=evaluation_start,
        evaluation_end=evaluation_end,
    )
    metadata = build_comparability_metadata(
        source_domain=source_domain,
        source_schema_version="backtest_run_artifacts_v1",
        timeframe=timeframe,
        evaluation_start=evaluation_start,
        evaluation_end=evaluation_end,
        universe=universe,
        instrument_set=list(universe),
        dataset_lineage_ref=dataset_ref,
        dataset_lineage_digest=dataset_digest,
        fee_model=fee_model,
        fee_parameters=fee_parameters,
        slippage_model=slippage_model,
        slippage_parameters=slippage_parameters,
        risk_policy_ref=risk_policy_ref,
        initial_capital=float(initial_capital),
        capital_currency=str(params.get("capital_currency") or quote),
        result_currency=str(params.get("result_currency") or quote),
        return_basis=return_basis,
        evaluation_slice_id=evaluation_slice_id,
    )
    metadata.pop("comparability_metadata_version", None)
    return metadata, evaluation_slice_id


def comparability_from_experiment_identity(
    *,
    identity_config: Mapping[str, Any],
    source_ref_id: str,
) -> tuple[dict[str, Any], str]:
    timeframe = _require_str(identity_config, "timeframe", label="identity_config")
    evaluation_start = _require_str(identity_config, "start_date", label="identity_config")
    evaluation_end = _require_str(identity_config, "end_date", label="identity_config")
    universe = _require_symbol_list(identity_config.get("symbols"), label="identity_config.symbols")
    initial_capital = identity_config.get("initial_capital")
    if not isinstance(initial_capital, (int, float)) or float(initial_capital) <= 0.0:
        raise ComparisonMetricInputError("identity_config.initial_capital must be > 0")
    base_params = identity_config.get("base_params")
    if not isinstance(base_params, dict):
        raise ComparisonMetricInputError("identity_config.base_params must be object")
    quote = universe[0].split("/")[-1] if "/" in universe[0] else "USD"
    dataset_ref = str(base_params.get("data_source") or "NOT_APPLICABLE")
    dataset_digest = (
        "NOT_APPLICABLE"
        if dataset_ref == "NOT_APPLICABLE"
        else compute_content_sha256({"dataset_lineage_ref": dataset_ref})
    )
    fee_model = str(base_params.get("fee_model") or "PROVABLY_ZERO")
    slippage_model = str(base_params.get("slippage_model") or "PROVABLY_ZERO")
    fee_parameters = base_params.get("fee_parameters")
    slippage_parameters = base_params.get("slippage_parameters")
    if not isinstance(fee_parameters, dict):
        fee_parameters = {}
    if not isinstance(slippage_parameters, dict):
        slippage_parameters = {}
    risk_policy_ref = str(base_params.get("risk_policy_ref") or "NOT_APPLICABLE")
    return_basis = str(base_params.get("return_basis") or "NET_EQUITY_CURVE")
    evaluation_slice_id = build_evaluation_slice_id(
        source_ref_id=source_ref_id,
        evaluation_start=evaluation_start,
        evaluation_end=evaluation_end,
    )
    metadata = build_comparability_metadata(
        source_domain="EXPERIMENT",
        source_schema_version="experiment_identity_manifest_v1",
        timeframe=timeframe,
        evaluation_start=evaluation_start,
        evaluation_end=evaluation_end,
        universe=universe,
        instrument_set=list(universe),
        dataset_lineage_ref=dataset_ref,
        dataset_lineage_digest=dataset_digest,
        fee_model=fee_model,
        fee_parameters=fee_parameters,
        slippage_model=slippage_model,
        slippage_parameters=slippage_parameters,
        risk_policy_ref=risk_policy_ref,
        initial_capital=float(initial_capital),
        capital_currency=str(base_params.get("capital_currency") or quote),
        result_currency=str(base_params.get("result_currency") or quote),
        return_basis=return_basis,
        evaluation_slice_id=evaluation_slice_id,
    )
    metadata.pop("comparability_metadata_version", None)
    return metadata, evaluation_slice_id
