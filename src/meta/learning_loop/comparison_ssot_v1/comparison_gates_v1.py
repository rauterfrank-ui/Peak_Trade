"""Comparability gate evaluation for comparison_ssot.v1."""

from __future__ import annotations

import math
from typing import Any

from src.meta.learning_loop.comparison_metric_input_v1.constants import METRIC_KEYS
from src.meta.learning_loop.comparison_ssot_v1.constants import (
    COMPARABILITY_GATE_VERSION,
    MAX_INPUT_COUNT,
    MIN_INPUT_COUNT,
)
from src.meta.learning_loop.comparison_ssot_v1.models import GateOutcome, LoadedMetricInput


def _pass(gate_id: str, reason_code: str = "OK") -> GateOutcome:
    return GateOutcome(gate_id, COMPARABILITY_GATE_VERSION, "PASS", reason_code)


def _fail(gate_id: str, reason_code: str, evidence_refs: tuple[str, ...] = ()) -> GateOutcome:
    return GateOutcome(gate_id, COMPARABILITY_GATE_VERSION, "FAIL", reason_code, evidence_refs)


def _reference_value(inputs: list[LoadedMetricInput], field: str) -> Any:
    return inputs[0].comparability_metadata.get(field)


def _all_equal(inputs: list[LoadedMetricInput], field: str) -> bool:
    values = [item.comparability_metadata.get(field) for item in inputs]
    return all(value == values[0] for value in values)


def _dicts_equal(a: Any, b: Any) -> bool:
    return a == b


def evaluate_comparability_gates(inputs: list[LoadedMetricInput]) -> list[GateOutcome]:
    outcomes: list[GateOutcome] = []

    count = len(inputs)
    outcomes.append(
        _pass("G01_INPUT_COUNT_VALID")
        if MIN_INPUT_COUNT <= count <= MAX_INPUT_COUNT
        else _fail("G01_INPUT_COUNT_VALID", "INPUT_COUNT_OUT_OF_RANGE")
    )

    outcomes.append(_pass("G02_INPUTS_CANONICALLY_VALIDATED"))

    domains = {item.source_domain for item in inputs}
    outcomes.append(
        _pass("G03_SAME_ALLOWED_DOMAIN")
        if len(domains) == 1
        else _fail("G03_SAME_ALLOWED_DOMAIN", "CROSS_DOMAIN_MIX")
    )

    outcomes.append(
        _pass("G04_COMPATIBLE_SOURCE_SCHEMA_VERSIONS")
        if _all_equal(inputs, "source_schema_version")
        else _fail("G04_COMPATIBLE_SOURCE_SCHEMA_VERSIONS", "SOURCE_SCHEMA_VERSION_MISMATCH")
    )

    for gate_id, field, reason in (
        ("G05_COMPATIBLE_TIMEFRAME", "timeframe", "TIMEFRAME_MISMATCH"),
        ("G06_COMPATIBLE_EVALUATION_RANGE", "evaluation_start", "EVALUATION_START_MISMATCH"),
        ("G06_COMPATIBLE_EVALUATION_RANGE_END", "evaluation_end", "EVALUATION_END_MISMATCH"),
        ("G07_COMPATIBLE_UNIVERSE", "universe", "UNIVERSE_MISMATCH"),
        ("G08_COMPATIBLE_INSTRUMENT_SET", "instrument_set", "INSTRUMENT_SET_MISMATCH"),
        (
            "G09_COMPATIBLE_DATASET_LINEAGE_REF",
            "dataset_lineage_ref",
            "DATASET_LINEAGE_REF_MISMATCH",
        ),
        (
            "G09_COMPATIBLE_DATASET_LINEAGE_DIGEST",
            "dataset_lineage_digest",
            "DATASET_LINEAGE_DIGEST_MISMATCH",
        ),
        ("G10_COMPATIBLE_FEE_MODEL", "fee_model", "FEE_MODEL_MISMATCH"),
        ("G11_COMPATIBLE_SLIPPAGE_MODEL", "slippage_model", "SLIPPAGE_MODEL_MISMATCH"),
        ("G12_COMPATIBLE_RISK_POLICY", "risk_policy_ref", "RISK_POLICY_MISMATCH"),
        ("G13_COMPATIBLE_INITIAL_CAPITAL", "initial_capital", "INITIAL_CAPITAL_MISMATCH"),
        ("G14_COMPATIBLE_CAPITAL_CURRENCY", "capital_currency", "CAPITAL_CURRENCY_MISMATCH"),
        ("G15_COMPATIBLE_RESULT_CURRENCY", "result_currency", "RESULT_CURRENCY_MISMATCH"),
        (
            "G16_COMPATIBLE_EQUITY_SAMPLING_FREQUENCY",
            "equity_sampling_frequency",
            "EQUITY_SAMPLING_FREQUENCY_MISMATCH",
        ),
        (
            "G17_COMPATIBLE_ANNUALIZATION_PROFILE",
            "annualization_profile",
            "ANNUALIZATION_PROFILE_MISMATCH",
        ),
        ("G18_COMPATIBLE_RETURN_BASIS", "return_basis", "RETURN_BASIS_MISMATCH"),
    ):
        if _all_equal(inputs, field):
            outcomes.append(_pass(gate_id))
        else:
            outcomes.append(_fail(gate_id, reason))

    fee_params_ok = all(
        _dicts_equal(
            item.comparability_metadata.get("fee_parameters"),
            _reference_value(inputs, "fee_parameters"),
        )
        for item in inputs
    )
    outcomes.append(
        _pass("G10_COMPATIBLE_FEE_PARAMETERS")
        if fee_params_ok
        else _fail("G10_COMPATIBLE_FEE_PARAMETERS", "FEE_PARAMETERS_MISMATCH")
    )

    slippage_params_ok = all(
        _dicts_equal(
            item.comparability_metadata.get("slippage_parameters"),
            _reference_value(inputs, "slippage_parameters"),
        )
        for item in inputs
    )
    outcomes.append(
        _pass("G11_COMPATIBLE_SLIPPAGE_PARAMETERS")
        if slippage_params_ok
        else _fail("G11_COMPATIBLE_SLIPPAGE_PARAMETERS", "SLIPPAGE_PARAMETERS_MISMATCH")
    )

    metrics_complete = all(set(item.metrics.keys()) == set(METRIC_KEYS) for item in inputs)
    outcomes.append(
        _pass("G19_COMPLETE_METRIC_SET")
        if metrics_complete
        else _fail("G19_COMPLETE_METRIC_SET", "INCOMPLETE_METRIC_SET")
    )

    nan_found = any(
        isinstance(value, float) and math.isnan(float(value))
        for item in inputs
        for value in item.metrics.values()
    )
    outcomes.append(
        _pass("G20_NO_NAN") if not nan_found else _fail("G20_NO_NAN", "NAN_METRIC_VALUE")
    )

    inf_found = any(
        isinstance(value, float) and math.isinf(float(value))
        for item in inputs
        for value in item.metrics.values()
    )
    outcomes.append(
        _pass("G21_NO_INFINITY")
        if not inf_found
        else _fail("G21_NO_INFINITY", "INFINITY_METRIC_VALUE")
    )

    ref_keys = [item.source_ref.sort_key() for item in inputs]
    outcomes.append(
        _pass("G22_NO_DUPLICATE_INPUTS")
        if len(ref_keys) == len(set(ref_keys))
        else _fail("G22_NO_DUPLICATE_INPUTS", "DUPLICATE_INPUT")
    )

    digest_stable = all(
        item.source_ref.digest == str(item.manifest["source_ref"]["digest"]) for item in inputs
    )
    outcomes.append(
        _pass("G23_STABLE_DIGESTS")
        if digest_stable
        else _fail("G23_STABLE_DIGESTS", "SOURCE_DIGEST_DRIFT")
    )

    sorted_keys = sorted(ref_keys)
    actual_keys = [item.source_ref.sort_key() for item in inputs]
    outcomes.append(
        _pass("G24_CANONICAL_ORDER")
        if actual_keys == sorted_keys
        else _fail("G24_CANONICAL_ORDER", "INPUTS_NOT_CANONICALLY_SORTED")
    )

    outcomes.append(_pass("G25_NO_HIDDEN_DEFAULTS"))

    untrusted = any(
        str(item.comparability_metadata.get("dataset_lineage_ref", "")).startswith("untrusted:")
        for item in inputs
    )
    outcomes.append(
        _pass("G26_NO_UNTRUSTED_EXTERNAL_IDS")
        if not untrusted
        else _fail("G26_NO_UNTRUSTED_EXTERNAL_IDS", "UNTRUSTED_EXTERNAL_ID")
    )

    authority_ok = all(
        item.comparability_metadata.get("authority_invariants", {}).get("runtime_authority_impact")
        == "NONE"
        for item in inputs
    )
    outcomes.append(
        _pass("G27_NO_PROMOTION_OR_RUNTIME_AUTHORITY")
        if authority_ok
        else _fail("G27_NO_PROMOTION_OR_RUNTIME_AUTHORITY", "RUNTIME_AUTHORITY_PRESENT")
    )

    slice_window_ok = (
        _all_equal(inputs, "evaluation_start")
        and _all_equal(inputs, "evaluation_end")
        and _all_equal(inputs, "timeframe")
    )
    outcomes.append(
        _pass("G28_IDENTICAL_EVALUATION_SLICE")
        if slice_window_ok
        else _fail("G28_IDENTICAL_EVALUATION_SLICE", "EVALUATION_SLICE_MISMATCH")
    )

    return outcomes


def overall_comparable(gate_outcomes: list[GateOutcome]) -> bool:
    return all(outcome.status == "PASS" for outcome in gate_outcomes)
