"""Regression tests for offline parameter sensitivity model spec alignment v0."""

from __future__ import annotations

import json
import math
import subprocess
import sys
from pathlib import Path

import pytest

from research.linear_evidence.import_boundary import scan_file_import_boundary
from research.linear_evidence.sensitivity import (
    EXCLUSION_REASON_ZERO_VARIANCE,
    MODEL_SPEC_VERSION,
    ParameterGridSpecV1,
    ParameterSensitivityInputV1,
    fit_parameter_sensitivity_surface,
)
from src.research.linear_evidence.fitters import (
    REASON_CONSTANT_TARGET,
    REASON_RANK_DEFICIENT_FEATURE_MATRIX,
)
from src.research.linear_evidence.parameter_sensitivity_productive_contract_v0 import (
    materialize_productive_sensitivity_row_v0,
)
from research.linear_evidence.signal_matrix_productive_contract_v0 import (
    DECISION_TIME_KEY,
    FEATURE_TIME_KEY,
    INSTRUMENT_ID_KEY,
)
from src.research.offline_final_research_fleet_signal_matrix_productive_input_join_materializer_v0 import (
    materialize_offline_final_research_fleet_signal_matrix_v0,
    serialize_signal_matrix_rows_v0,
)
from src.research.offline_parameter_sensitivity_productive_input_join_materializer_v0 import (
    materialize_offline_parameter_sensitivity_productive_inputs_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SENSITIVITY_MODULE = REPO_ROOT / "src/research/linear_evidence/sensitivity.py"
FITTER_MODULE = REPO_ROOT / "src/research/linear_evidence/fitters.py"
ARCHIVE_ROOT = Path("/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z")
STAGING_ROOT = (
    ARCHIVE_ROOT / "datasets/admissible_futures/"
    "pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_v1/"
    "extended_chronological_v1"
)
FORBIDDEN_IMPORT_PREFIXES = (
    "src.execution",
    "src.scheduler",
    "src.broker",
    "src.trading.master_v2",
    "src.risk",
    "src.governance",
)


def _record(
    index: int,
    *,
    target: float,
    signal: float,
    aux: float,
    fee_bps: float = 10.0,
    slippage_bps: float = 5.0,
) -> ParameterSensitivityInputV1:
    decision_time = f"2026-01-01T{index:02d}:00:00Z"
    return ParameterSensitivityInputV1(
        instrument_id="PF_ETHUSD",
        decision_time=decision_time,
        feature_availability_time=decision_time,
        target=target,
        features={
            "signal": signal,
            "aux": aux,
            "fee_bps": fee_bps,
            "slippage_bps": slippage_bps,
        },
    )


def _productive_like_records(count: int = 16) -> list[ParameterSensitivityInputV1]:
    records: list[ParameterSensitivityInputV1] = []
    for index in range(count):
        signal = float(index + 1)
        aux = 0.05 * float(index % 4)
        records.append(
            _record(
                index,
                target=signal + aux,
                signal=signal,
                aux=aux,
                fee_bps=10.0,
                slippage_bps=5.0,
            )
        )
    return records


def _default_grid() -> ParameterGridSpecV1:
    return ParameterGridSpecV1(
        parameter_name="signal_scale",
        scaled_feature_name="signal",
        parameter_values=(0.85, 0.95, 1.0, 1.05, 1.15),
    )


def _fee_bps_grid() -> ParameterGridSpecV1:
    return ParameterGridSpecV1(
        parameter_name="fee_bps_scale",
        scaled_feature_name="fee_bps",
        parameter_values=(0.8, 1.0, 1.2),
    )


def test_constant_cost_features_excluded_transparently_for_1d_surface() -> None:
    evidence = fit_parameter_sensitivity_surface(
        _productive_like_records(),
        grid=_fee_bps_grid(),
    )

    assert evidence.model_spec_version == MODEL_SPEC_VERSION
    assert set(evidence.excluded_feature_names) == {"fee_bps", "slippage_bps"}
    strict_codes = [
        code
        for code in evidence.exclusion_reason_codes
        if code.startswith("STRICT_ZERO_VARIANCE_FEATURE_EXCLUDED:")
    ]
    surface_codes = [
        code
        for code in evidence.exclusion_reason_codes
        if code.startswith(f"{EXCLUSION_REASON_ZERO_VARIANCE}:")
    ]
    assert len(strict_codes) == 2
    assert len(surface_codes) == 2
    assert {code.split(":", 1)[1] for code in strict_codes} == {"fee_bps", "slippage_bps"}


def test_active_design_matrix_reaches_full_rank_for_productive_like_surface() -> None:
    evidence = fit_parameter_sensitivity_surface(
        _productive_like_records(),
        grid=_fee_bps_grid(),
    )

    assert evidence.active_rank == evidence.required_active_rank == 3
    assert evidence.requested_rank == 5
    assert evidence.status != "RANK_DEFICIENT_BLOCKED"
    assert math.isfinite(evidence.condition_number)
    assert evidence.plateau_detection_admissible is True
    assert evidence.fragility_detection_admissible is True


def test_non_constant_features_are_not_excluded() -> None:
    evidence = fit_parameter_sensitivity_surface(
        _productive_like_records(),
        grid=_fee_bps_grid(),
    )

    assert evidence.active_feature_names == ("aux", "signal")
    assert "signal" not in evidence.excluded_feature_names
    assert "aux" not in evidence.excluded_feature_names


def test_constant_target_still_blocked() -> None:
    records = [
        _record(index, target=3.0, signal=float(index + 1), aux=0.1 * float(index))
        for index in range(12)
    ]
    evidence = fit_parameter_sensitivity_surface(records, grid=_default_grid(), min_samples=4)

    assert any(REASON_CONSTANT_TARGET in point.reason_codes for point in evidence.grid_evidence)
    assert evidence.status in {"INSUFFICIENT_DATA", "RANK_DEFICIENT_BLOCKED"}


def test_varying_feature_collinearity_still_blocked() -> None:
    records = [
        _record(index, target=float(index + 1), signal=float(index + 1), aux=2.0 * float(index + 1))
        for index in range(12)
    ]
    evidence = fit_parameter_sensitivity_surface(records, grid=_default_grid(), min_samples=4)

    assert evidence.status == "RANK_DEFICIENT_BLOCKED"
    assert any(
        REASON_RANK_DEFICIENT_FEATURE_MATRIX in point.reason_codes
        for point in evidence.grid_evidence
    )


def test_deterministic_feature_order_and_exclusion_reason_codes() -> None:
    first = fit_parameter_sensitivity_surface(_productive_like_records(), grid=_fee_bps_grid())
    second = fit_parameter_sensitivity_surface(_productive_like_records(), grid=_fee_bps_grid())

    assert (
        first.excluded_feature_names
        == second.excluded_feature_names
        == (
            "fee_bps",
            "slippage_bps",
        )
    )
    assert first.exclusion_reason_codes == second.exclusion_reason_codes
    assert first.active_feature_names == second.active_feature_names == ("aux", "signal")


def test_repeated_run_produces_byte_identical_diagnostic_payload(tmp_path: Path) -> None:
    evidence = fit_parameter_sensitivity_surface(_productive_like_records(), grid=_default_grid())
    payload = json.dumps(evidence.to_dict(), sort_keys=True, separators=(",", ":"))
    path_a = tmp_path / "a.json"
    path_b = tmp_path / "b.json"
    path_a.write_text(payload, encoding="utf-8")
    second = fit_parameter_sensitivity_surface(_productive_like_records(), grid=_default_grid())
    path_b.write_text(
        json.dumps(second.to_dict(), sort_keys=True, separators=(",", ":")),
        encoding="utf-8",
    )
    assert path_a.read_bytes() == path_b.read_bytes()


def test_binding_semantics_unchanged_in_productive_contract() -> None:
    row = {
        INSTRUMENT_ID_KEY: "okx:linear_perpetual:ETH:USDT:USDT:perp",
        DECISION_TIME_KEY: "2024-05-31T10:00:00Z",
        FEATURE_TIME_KEY: "2024-05-31T09:00:00Z",
        "bollinger_bands": 1.0,
        "momentum_1h": 0.0,
        "trend_following": -1.0,
    }
    record, reason = materialize_productive_sensitivity_row_v0(
        row,
        baseline_fee_bps=10.0,
        baseline_slippage_bps=5.0,
    )
    assert reason is None
    assert record is not None
    assert record.features["fee_bps"] == 10.0
    assert record.features["slippage_bps"] == 5.0


def test_sensitivity_module_import_boundary() -> None:
    violations = scan_file_import_boundary(SENSITIVITY_MODULE, repo_root=REPO_ROOT)
    assert violations == []


def test_fitter_module_import_boundary() -> None:
    violations = scan_file_import_boundary(FITTER_MODULE, repo_root=REPO_ROOT)
    assert violations == []


def test_no_forbidden_trading_core_imports_in_sensitivity_module() -> None:
    source = SENSITIVITY_MODULE.read_text(encoding="utf-8")
    for prefix in FORBIDDEN_IMPORT_PREFIXES:
        assert prefix not in source


@pytest.mark.skipif(not STAGING_ROOT.is_dir(), reason="archive staging root unavailable")
def test_productive_diagnostic_smoke_full_rank(tmp_path: Path) -> None:
    result = materialize_offline_final_research_fleet_signal_matrix_v0(
        repo_root=REPO_ROOT,
        staging_root=STAGING_ROOT,
    )
    materialization = materialize_offline_parameter_sensitivity_productive_inputs_v0(
        signal_matrix_rows=result.rows,
        repo_root=REPO_ROOT,
    )
    assert materialization.status.value == "PASS"
    sorted_records = tuple(
        sorted(
            materialization.records,
            key=lambda record: (record.decision_time, record.instrument_id),
        )
    )
    fee_spec = materialization.join_result.grid_specs[0]
    evidence = fit_parameter_sensitivity_surface(
        sorted_records,
        grid=fee_spec,
    )
    assert evidence.excluded_feature_names == ("fee_bps", "slippage_bps")
    assert evidence.active_rank == evidence.required_active_rank == 4
    assert evidence.status != "RANK_DEFICIENT_BLOCKED"
    assert evidence.economic_interpretation_admissible is False


def test_fixture_runner_still_emits_model_spec_fields(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts/research/offline_parameter_sensitivity_surface_v0.py"),
            "--out",
            str(tmp_path),
            "--fixture",
        ],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert result.returncode == 0, result.stderr
    report = json.loads((tmp_path / "parameter_sensitivity_surface_evidence_v1.json").read_text())
    assert report["model_spec_version"] == MODEL_SPEC_VERSION
    assert report["economic_interpretation_admissible"] is False
