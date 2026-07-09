from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from research.linear_evidence.sensitivity import (
    ParameterGridSpecV1,
    ParameterSensitivityInputV1,
    fit_parameter_sensitivity_surface,
)


def _record(
    index: int,
    *,
    target: float,
    signal: float,
    aux: float,
    feature_time: str | None = None,
) -> ParameterSensitivityInputV1:
    decision_time = f"2026-01-01T{index:02d}:00:00Z"
    return ParameterSensitivityInputV1(
        instrument_id="PF_ETHUSD",
        decision_time=decision_time,
        feature_availability_time=feature_time or decision_time,
        target=target,
        features={"signal": signal, "aux": aux},
    )


def _robust_plateau_records(count: int = 16) -> list[ParameterSensitivityInputV1]:
    return [
        _record(
            index,
            target=float(index + 1) + 0.05 * float(index % 4),
            signal=float(index + 1),
            aux=0.05 * float(index % 4),
        )
        for index in range(count)
    ]


def _fragile_spike_records() -> list[ParameterSensitivityInputV1]:
    records: list[ParameterSensitivityInputV1] = []
    for index in range(12):
        signal = float(index + 1)
        aux = 0.2 * signal
        records.append(
            _record(index, target=signal + aux, signal=signal, aux=aux),
        )
    for index in range(12, 16):
        signal = float(index + 1)
        aux = float((index % 3) + 1) * 2.0
        records.append(
            _record(index, target=signal + aux, signal=signal, aux=aux),
        )
    return records


def _default_grid() -> ParameterGridSpecV1:
    return ParameterGridSpecV1(
        parameter_name="signal_scale",
        scaled_feature_name="signal",
        parameter_values=(0.85, 0.95, 1.0, 1.05, 1.15),
    )


def test_parameter_sensitivity_surface_is_authority_neutral() -> None:
    evidence = fit_parameter_sensitivity_surface(_robust_plateau_records(), grid=_default_grid())

    assert evidence.evidence_type == "parameter_sensitivity_surface"
    assert evidence.authority_effect == "NONE"
    assert evidence.runtime_effect == "NONE"
    assert evidence.solver == "numpy.linalg.lstsq"
    assert evidence.validation_policy == "TIME_ORDERED"
    assert evidence.n_grid_points == len(_default_grid().parameter_values)
    assert all(point.solver == "numpy.linalg.lstsq" for point in evidence.grid_evidence)


def test_parameter_sensitivity_surface_blocks_non_time_ordered_records() -> None:
    records = [
        _record(2, target=0.2, signal=2.0, aux=0.1),
        _record(1, target=0.1, signal=1.0, aux=0.2),
    ]

    with pytest.raises(ValueError, match="RANDOM_VALIDATION_SPLIT_BLOCKED"):
        fit_parameter_sensitivity_surface(records, grid=_default_grid(), min_samples=2)


def test_parameter_sensitivity_surface_blocks_lookahead() -> None:
    records = [
        _record(
            index,
            target=float(index) * 0.1,
            signal=float(index),
            aux=float(index % 2),
            feature_time=f"2026-01-01T{index + 1:02d}:00:00Z" if index == 0 else None,
        )
        for index in range(8)
    ]

    evidence = fit_parameter_sensitivity_surface(records, grid=_default_grid(), min_samples=4)

    assert evidence.status == "LEAKAGE_BLOCKED"
    assert evidence.reason_codes == ("FEATURE_LEAKAGE_RISK",)


def test_parameter_sensitivity_surface_robust_plateau_case() -> None:
    evidence = fit_parameter_sensitivity_surface(_robust_plateau_records(), grid=_default_grid())

    assert evidence.plateau_detected is True
    assert "ROBUST_PLATEAU_DETECTED" in evidence.reason_codes
    assert evidence.robust_region_bounds is not None
    assert evidence.robust_region_bounds[0] <= evidence.robust_region_bounds[1]


def test_parameter_sensitivity_surface_fragile_spike_case() -> None:
    grid = ParameterGridSpecV1(
        parameter_name="signal_scale",
        scaled_feature_name="signal",
        parameter_values=(0.25, 0.5, 0.75, 1.0, 1.25),
    )
    evidence = fit_parameter_sensitivity_surface(_fragile_spike_records(), grid=grid)

    assert evidence.fragile_spike_detected is True
    assert "FRAGILE_PARAMETER_SPIKE" in evidence.reason_codes


def test_parameter_sensitivity_surface_insufficient_grid_case() -> None:
    grid = ParameterGridSpecV1(
        parameter_name="signal_scale",
        scaled_feature_name="signal",
        parameter_values=(0.9, 1.1),
    )
    evidence = fit_parameter_sensitivity_surface(
        _robust_plateau_records(count=8),
        grid=grid,
        min_samples=4,
        min_grid_points=3,
    )

    assert evidence.status == "INSUFFICIENT_DATA"
    assert evidence.reason_codes == ("PARAMETER_GRID_TOO_SMALL",)


def test_parameter_sensitivity_surface_insufficient_sample_count() -> None:
    evidence = fit_parameter_sensitivity_surface(
        _robust_plateau_records(count=3),
        grid=_default_grid(),
        min_samples=8,
    )

    assert evidence.status == "INSUFFICIENT_DATA"
    assert evidence.reason_codes == ("INSUFFICIENT_SAMPLE_COUNT",)


def test_parameter_sensitivity_surface_unstable_validation_case() -> None:
    records = [
        _record(
            index,
            target=5.0 + float(index % 7) * 0.9,
            signal=float(index + 1),
            aux=float(index % 3),
        )
        for index in range(16)
    ]
    grid = ParameterGridSpecV1(
        parameter_name="signal_scale",
        scaled_feature_name="signal",
        parameter_values=(0.5, 0.75, 1.0, 1.25, 1.5),
    )

    evidence = fit_parameter_sensitivity_surface(records, grid=grid, max_validation_rmse=0.05)

    assert "VALIDATION_ERROR_TOO_HIGH" in evidence.reason_codes


def test_parameter_sensitivity_surface_does_not_emit_best_parameter_point() -> None:
    evidence = fit_parameter_sensitivity_surface(_robust_plateau_records(), grid=_default_grid())
    payload = evidence.to_dict()

    assert "best_parameter_value" not in payload
    assert "best_parameter_point" not in payload
    assert "optimal_parameter" not in payload


def test_parameter_sensitivity_surface_cli_writes_manifestable_report(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/research/offline_parameter_sensitivity_surface_v0.py",
            "--out",
            str(tmp_path),
        ],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    assert result.returncode == 0, result.stderr
    report_path = tmp_path / "parameter_sensitivity_surface_evidence_v1.json"
    assert report_path.exists()
    report = json.loads(report_path.read_text())
    assert report["evidence_type"] == "parameter_sensitivity_surface"
    assert report["authority_effect"] == "NONE"
    assert report["runtime_effect"] == "NONE"
    assert report["offline_only"] is True
    assert report["system_economic_evidence_admissible"] is False
    assert report["runtime_rewire_admissible"] is False
    assert report["no_parameter_auto_optimization"] is True
    assert report["no_parameter_default_change_in_v0"] is True
    truth_pack = report["fixture_truth_pack"]
    assert "ROBUST_PLATEAU_DETECTED" in truth_pack["robust_plateau_case"]["reason_codes"]
    assert "FRAGILE_PARAMETER_SPIKE" in truth_pack["fragile_spike_case"]["reason_codes"]
    assert truth_pack["insufficient_grid_case"]["reason_codes"] == ["PARAMETER_GRID_TOO_SMALL"]
    assert "VALIDATION_ERROR_TOO_HIGH" in truth_pack["unstable_validation_case"]["reason_codes"]
