#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT))

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
) -> ParameterSensitivityInputV1:
    decision_time = f"2026-01-01T{index:02d}:00:00Z"
    return ParameterSensitivityInputV1(
        instrument_id="PF_ETHUSD",
        decision_time=decision_time,
        feature_availability_time=decision_time,
        target=target,
        features={"signal": signal, "aux": aux},
    )


def fixture_robust_plateau_records() -> list[ParameterSensitivityInputV1]:
    records: list[ParameterSensitivityInputV1] = []
    for index in range(16):
        signal = float(index + 1)
        aux = 0.05 * float(index % 4)
        records.append(_record(index, target=signal + aux, signal=signal, aux=aux))
    return records


def fixture_fragile_spike_records() -> list[ParameterSensitivityInputV1]:
    records: list[ParameterSensitivityInputV1] = []
    for index in range(12):
        signal = float(index + 1)
        aux = 0.2 * signal
        records.append(_record(index, target=signal + aux, signal=signal, aux=aux))
    for index in range(12, 16):
        signal = float(index + 1)
        aux = float((index % 3) + 1) * 2.0
        records.append(_record(index, target=signal + aux, signal=signal, aux=aux))
    return records


def fixture_insufficient_grid_records() -> list[ParameterSensitivityInputV1]:
    return fixture_robust_plateau_records()[:6]


def fixture_unstable_validation_records() -> list[ParameterSensitivityInputV1]:
    records: list[ParameterSensitivityInputV1] = []
    for index in range(16):
        signal = float(index + 1)
        aux = float(index % 3)
        target = 5.0 + float(index % 7) * 0.9
        records.append(_record(index, target=target, signal=signal, aux=aux))
    return records


def _fixture_truth_pack() -> dict[str, object]:
    robust_grid = ParameterGridSpecV1(
        parameter_name="signal_scale",
        scaled_feature_name="signal",
        parameter_values=(0.85, 0.95, 1.0, 1.05, 1.15),
    )
    fragile_grid = ParameterGridSpecV1(
        parameter_name="signal_scale",
        scaled_feature_name="signal",
        parameter_values=(0.25, 0.5, 0.75, 1.0, 1.25),
    )
    insufficient_grid = ParameterGridSpecV1(
        parameter_name="signal_scale",
        scaled_feature_name="signal",
        parameter_values=(0.9, 1.1),
    )
    unstable_grid = fragile_grid

    robust = fit_parameter_sensitivity_surface(fixture_robust_plateau_records(), grid=robust_grid)
    fragile = fit_parameter_sensitivity_surface(fixture_fragile_spike_records(), grid=fragile_grid)
    insufficient = fit_parameter_sensitivity_surface(
        fixture_insufficient_grid_records(),
        grid=insufficient_grid,
        min_samples=4,
    )
    unstable = fit_parameter_sensitivity_surface(
        fixture_unstable_validation_records(),
        grid=unstable_grid,
        max_validation_rmse=0.05,
    )

    return {
        "robust_plateau_case": robust.to_dict(),
        "fragile_spike_case": fragile.to_dict(),
        "insufficient_grid_case": insufficient.to_dict(),
        "unstable_validation_case": unstable.to_dict(),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    grid = ParameterGridSpecV1(
        parameter_name="signal_scale",
        scaled_feature_name="signal",
        parameter_values=(0.85, 0.95, 1.0, 1.05, 1.15),
    )
    evidence = fit_parameter_sensitivity_surface(fixture_robust_plateau_records(), grid=grid)
    truth_pack = _fixture_truth_pack()

    report = evidence.to_dict()
    report.update(
        {
            "offline_only": True,
            "system_economic_evidence_admissible": False,
            "runtime_rewire_admissible": False,
            "promotion_pass_authority": False,
            "no_parameter_auto_optimization": True,
            "no_parameter_default_change_in_v0": True,
            "fixture_truth_pack": truth_pack,
        }
    )

    report_path = out / "parameter_sensitivity_surface_evidence_v1.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(f"STATUS={evidence.status}")
    print("AUTHORITY_EFFECT=NONE")
    print("RUNTIME_EFFECT=NONE")
    print(f"PLATEAU_DETECTED={evidence.plateau_detected}")
    print(f"FRAGILE_SPIKE_DETECTED={evidence.fragile_spike_detected}")
    print(f"REASON_CODES={','.join(evidence.reason_codes) or 'NONE'}")
    print(f"REPORT={report_path}")
    return (
        0
        if evidence.status
        in {
            "DIAGNOSTIC_ONLY",
            "ROBUSTNESS_FAILED",
            "RANK_DEFICIENT_BLOCKED",
            "INSUFFICIENT_DATA",
        }
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
