"""Contract tests for operator-ratified productive parameter sensitivity normative contract v0."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from research.linear_evidence.import_boundary import scan_file_import_boundary
from research.linear_evidence.parameter_sensitivity_productive_contract_v0 import (
    ALLOWED_CALIBRATABLE_PARAMETERS,
    AUTHORITY_EFFECT,
    PARAMETER_CLASS_CONSTITUTIONAL_CORE,
    PARAMETER_CLASS_DIAGNOSTIC_ONLY,
    PARAMETER_CLASS_EXPLICITLY_CALIBRATABLE,
    PARAMETER_CLASS_UNKNOWN,
    ProductiveBindingRejectionReason,
    build_parameter_grid_specs_v0,
    classify_fleet_parameters_v0,
    load_productive_parameter_grid_v0,
    materialize_productive_sensitivity_row_v0,
    validate_binding_digest_v0,
    validate_fleet_candidate_set_v0,
    validate_parameter_variation_allowed_v0,
    validate_productive_binding_batch_v0,
    validate_signal_matrix_digest_v0,
)
from research.linear_evidence.signal_matrix_productive_contract_v0 import (
    DECISION_TIME_KEY,
    EXPECTED_FLEET_SIGNAL_ORDER,
    FEATURE_TIME_KEY,
    INSTRUMENT_ID_KEY,
    compute_signal_matrix_digest_v0,
)
from research.offline_final_research_fleet_signal_matrix_productive_input_join_materializer_v0 import (
    load_ratified_binding_completion_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_MODULE = (
    REPO_ROOT / "src/research/linear_evidence/parameter_sensitivity_productive_contract_v0.py"
)
FORBIDDEN_IMPORT_PREFIXES = (
    "src.execution",
    "src.scheduler",
    "src.broker",
    "requests",
    "httpx",
    "urllib.request",
)


def _signal_matrix_row(
    *,
    instrument_id: str = "okx:linear_perpetual:ETH:USDT:USDT:perp",
    decision_time: str = "2024-05-31T10:00:00Z",
    feature_time: str = "2024-05-31T09:00:00Z",
    bollinger_bands: float = 1.0,
    momentum_1h: float = 0.0,
    trend_following: float = -1.0,
) -> dict[str, object]:
    return {
        INSTRUMENT_ID_KEY: instrument_id,
        DECISION_TIME_KEY: decision_time,
        FEATURE_TIME_KEY: feature_time,
        "bollinger_bands": bollinger_bands,
        "momentum_1h": momentum_1h,
        "trend_following": trend_following,
    }


def test_allowed_calibratable_parameters_are_fee_and_slippage_only() -> None:
    assert ALLOWED_CALIBRATABLE_PARAMETERS == ("fee_bps", "slippage_bps")


def test_parameter_classification_has_no_unknowns() -> None:
    rows = classify_fleet_parameters_v0()
    assert all(row.parameter_class != PARAMETER_CLASS_UNKNOWN for row in rows)


def test_constitutional_core_variation_rejected() -> None:
    assert (
        validate_parameter_variation_allowed_v0("adx_period")
        == ProductiveBindingRejectionReason.CONSTITUTIONAL_PARAMETER_VARIATION_REQUESTED.value
    )


def test_diagnostic_only_variation_rejected() -> None:
    assert (
        validate_parameter_variation_allowed_v0("signal_scale")
        == ProductiveBindingRejectionReason.DIAGNOSTIC_ONLY_PARAMETER_VARIATION_REQUESTED.value
    )


def test_unknown_parameter_variation_rejected() -> None:
    assert (
        validate_parameter_variation_allowed_v0("not_a_real_parameter")
        == ProductiveBindingRejectionReason.UNKNOWN_PARAMETER.value
    )


def test_calibratable_parameters_classified_correctly() -> None:
    rows = classify_fleet_parameters_v0()
    fee_rows = [row for row in rows if row.parameter_name == "fee_bps"]
    assert fee_rows
    assert all(row.parameter_class == PARAMETER_CLASS_EXPLICITLY_CALIBRATABLE for row in fee_rows)
    assert all(row.sensitivity_variation_allowed is True for row in fee_rows)


def test_constitutional_parameters_not_variation_allowed() -> None:
    rows = classify_fleet_parameters_v0()
    core_rows = [row for row in rows if row.parameter_class == PARAMETER_CLASS_CONSTITUTIONAL_CORE]
    assert core_rows
    assert all(row.sensitivity_variation_allowed is False for row in core_rows)


def test_diagnostic_only_signal_scale_not_variation_allowed() -> None:
    rows = classify_fleet_parameters_v0()
    signal_scale = [row for row in rows if row.parameter_name == "signal_scale"]
    assert len(signal_scale) == 1
    assert signal_scale[0].parameter_class == PARAMETER_CLASS_DIAGNOSTIC_ONLY
    assert signal_scale[0].sensitivity_variation_allowed is False


def test_binding_digest_mismatch_rejected() -> None:
    assert (
        validate_binding_digest_v0(expected_digest="abc", actual_digest="def")
        == ProductiveBindingRejectionReason.BINDING_DIGEST_MISMATCH.value
    )


def test_signal_matrix_digest_mismatch_rejected() -> None:
    rows = (_signal_matrix_row(),)
    digest = compute_signal_matrix_digest_v0(rows)
    assert (
        validate_signal_matrix_digest_v0(
            expected_digest="stale",
            actual_digest=digest,
            rows=rows,
        )
        == ProductiveBindingRejectionReason.SIGNAL_MATRIX_DIGEST_MISMATCH.value
    )


def test_missing_signal_matrix_rejected() -> None:
    assert (
        validate_signal_matrix_digest_v0(expected_digest=None, actual_digest="", rows=())
        == ProductiveBindingRejectionReason.MISSING_SIGNAL_MATRIX.value
    )


def test_materialize_row_rejects_lookahead() -> None:
    record, reason = materialize_productive_sensitivity_row_v0(
        _signal_matrix_row(feature_time="2024-05-31T11:00:00Z"),
        baseline_fee_bps=10.0,
        baseline_slippage_bps=5.0,
    )
    assert record is None
    assert reason == ProductiveBindingRejectionReason.FEATURE_LEAKAGE_DETECTED.value


def test_materialize_row_accepts_valid_row() -> None:
    record, reason = materialize_productive_sensitivity_row_v0(
        _signal_matrix_row(),
        baseline_fee_bps=10.0,
        baseline_slippage_bps=5.0,
    )
    assert reason is None
    assert record is not None
    assert record.features["fee_bps"] == pytest.approx(10.0)
    assert record.features["slippage_bps"] == pytest.approx(5.0)
    for name in EXPECTED_FLEET_SIGNAL_ORDER:
        assert name in record.features


def test_step31f_grid_loads_fee_and_slippage_only() -> None:
    binding = load_ratified_binding_completion_v0(REPO_ROOT)
    shared = binding.get("shared_bindings", {})
    dataset_binding = shared.get("dataset_binding", {})
    grid = load_productive_parameter_grid_v0(
        repo_root=REPO_ROOT,
        strategy_id="trend_following",
        data_digest=str(dataset_binding.get("data_digest", "")),
    )
    assert grid.grid_id == "okx_eth_perp_research_cost_grid_v1"
    assert grid.parameter_names == ("fee_bps", "slippage_bps")
    specs = build_parameter_grid_specs_v0(grid)
    assert [spec.parameter_name for spec in specs] == ["fee_bps", "slippage_bps"]


def test_productive_binding_batch_accepts_valid_rows() -> None:
    binding = load_ratified_binding_completion_v0(REPO_ROOT)
    rows = tuple(
        _signal_matrix_row(decision_time=f"2024-05-31T{hour:02d}:00:00Z") for hour in range(10, 18)
    )
    result = validate_productive_binding_batch_v0(
        signal_matrix_rows=rows,
        binding_completion=binding,
        repo_root=REPO_ROOT,
    )
    assert result.row_count_after_filter == len(rows)
    assert result.grid.grid_id == "okx_eth_perp_research_cost_grid_v1"
    assert len(result.grid_specs) == 2


def test_productive_binding_batch_rejects_binding_digest_mismatch() -> None:
    binding = load_ratified_binding_completion_v0(REPO_ROOT)
    rows = (_signal_matrix_row(),)
    with pytest.raises(ValueError, match="BINDING_DIGEST_MISMATCH"):
        validate_productive_binding_batch_v0(
            signal_matrix_rows=rows,
            binding_completion=binding,
            repo_root=REPO_ROOT,
            expected_binding_digest="stale-digest",
        )


def test_fleet_candidate_set_validation() -> None:
    validate_fleet_candidate_set_v0(["trend_following", "momentum_1h", "bollinger_bands"])
    with pytest.raises(ValueError, match="MISSING_FLEET_BINDING"):
        validate_fleet_candidate_set_v0(["trend_following"])


def test_contract_module_has_no_forbidden_imports() -> None:
    violations = scan_file_import_boundary(CONTRACT_MODULE, repo_root=REPO_ROOT)
    assert violations == []


def test_contract_authority_effect_none() -> None:
    assert AUTHORITY_EFFECT == "NONE"
