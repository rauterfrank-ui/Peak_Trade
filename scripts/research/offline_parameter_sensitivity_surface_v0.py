#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT))

from research.linear_evidence.sensitivity import (  # noqa: E402
    ParameterGridSpecV1,
    ParameterSensitivityInputV1,
    fit_parameter_sensitivity_surface,
)
from src.research.offline_parameter_sensitivity_productive_input_join_materializer_v0 import (  # noqa: E402
    MaterializationStatus,
    load_signal_matrix_rows,
    materialize_offline_parameter_sensitivity_productive_inputs_v0,
    serialize_materialized_productive_inputs_v0,
)
from src.research.offline_final_research_fleet_signal_matrix_productive_input_join_materializer_v0 import (  # noqa: E402
    load_ratified_binding_completion_v0,
)

AUTHORITY_EFFECT = "NONE"
RUNTIME_EFFECT = "NONE"


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


def _run_fixture_mode(out: Path) -> int:
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
            "INPUT_MODE": "FIXTURE_SCAFFOLD",
            "PRODUCTIVE_BINDING_REQUESTED": False,
            "PRODUCTIVE_BINDING_RESOLVED": False,
            "FIXTURE_SCAFFOLD_USED": True,
            "offline_only": True,
            "system_economic_evidence_admissible": False,
            "runtime_rewire_admissible": False,
            "promotion_pass_authority": False,
            "no_parameter_auto_optimization": True,
            "no_parameter_default_change_in_v0": True,
            "economic_evaluation_executed": False,
            "fixture_truth_pack": truth_pack,
        }
    )

    report_path = out / "parameter_sensitivity_surface_evidence_v1.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(f"STATUS={evidence.status}")
    print("AUTHORITY_EFFECT=NONE")
    print("RUNTIME_EFFECT=NONE")
    print("INPUT_MODE=FIXTURE_SCAFFOLD")
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


def _run_productive_binding_mode(
    out: Path,
    *,
    signal_matrix_path: Path,
    productive_binding_path: Path | None,
    strategy_id: str,
) -> int:
    signal_rows = load_signal_matrix_rows(signal_matrix_path)
    binding_payload = None
    if productive_binding_path is not None:
        binding_payload = json.loads(productive_binding_path.read_text(encoding="utf-8"))
    else:
        binding_payload = load_ratified_binding_completion_v0(REPO_ROOT)

    materialization = materialize_offline_parameter_sensitivity_productive_inputs_v0(
        signal_matrix_rows=signal_rows,
        repo_root=REPO_ROOT,
        binding_completion=binding_payload,
        strategy_id=strategy_id,
    )

    binding_report = {
        "INPUT_MODE": "PRODUCTIVE_BINDING",
        "PRODUCTIVE_BINDING_REQUESTED": True,
        "PRODUCTIVE_BINDING_RESOLVED": materialization.status == MaterializationStatus.PASS,
        "FIXTURE_SCAFFOLD_USED": False,
        "status": materialization.status.value,
        "materialization_digest": materialization.materialization_digest,
        "output_digest": materialization.output_digest,
        "productive_input_digest": materialization.productive_input_digest,
        "grid_digest": materialization.grid_digest,
        "source_binding_digest": materialization.source_binding_digest,
        "source_signal_matrix_digest": materialization.source_signal_matrix_digest,
        "binding": materialization.join_result.binding.to_dict(),
        "grid": materialization.join_result.grid.to_dict(),
        "grid_specs": [
            {
                "parameter_name": spec.parameter_name,
                "scaled_feature_name": spec.scaled_feature_name,
                "parameter_values": list(spec.parameter_values),
            }
            for spec in materialization.join_result.grid_specs
        ],
        "provenance": materialization.provenance.to_dict(),
        "row_count_before_filter": materialization.join_result.row_count_before_filter,
        "row_count_after_filter": materialization.join_result.row_count_after_filter,
        "dropped_rows_by_reason": dict(materialization.join_result.dropped_rows_by_reason),
        "offline_only": True,
        "system_economic_evidence_admissible": False,
        "runtime_rewire_admissible": False,
        "promotion_pass_authority": False,
        "no_parameter_auto_optimization": True,
        "no_parameter_default_change_in_v0": True,
        "economic_evaluation_executed": False,
        "sensitivity_surface_executed": False,
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
    }
    report_path = out / "parameter_sensitivity_productive_binding_v0.json"
    report_path.write_text(
        json.dumps(binding_report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    inputs_path = out / "productive_parameter_sensitivity_inputs.jsonl"
    inputs_path.write_text(
        serialize_materialized_productive_inputs_v0(materialization.records),
        encoding="utf-8",
    )

    print(f"STATUS={materialization.status.value}")
    print("AUTHORITY_EFFECT=NONE")
    print("RUNTIME_EFFECT=NONE")
    print("INPUT_MODE=PRODUCTIVE_BINDING")
    print(f"PRODUCTIVE_BINDING_RESOLVED={materialization.status == MaterializationStatus.PASS}")
    print(f"PRODUCTIVE_INPUT_DIGEST={materialization.productive_input_digest}")
    print(f"GRID_DIGEST={materialization.grid_digest}")
    print(f"REPORT={report_path}")
    return 0 if materialization.status == MaterializationStatus.PASS else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    parser.add_argument("--fixture", action="store_true")
    parser.add_argument("--signal-matrix", type=Path, default=None)
    parser.add_argument("--productive-binding", type=Path, default=None)
    parser.add_argument("--parameter-grid", default="trend_following")
    args = parser.parse_args()

    productive_requested = args.signal_matrix is not None or args.productive_binding is not None
    if args.fixture and productive_requested:
        raise SystemExit("MIXED_MODE_BLOCKED: fixture and productive modes are mutually exclusive")
    if not args.fixture and not productive_requested:
        args.fixture = True

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    if args.fixture:
        return _run_fixture_mode(out)
    if args.signal_matrix is None:
        raise SystemExit("TARGET_BINDING_MISSING: --signal-matrix required for productive mode")
    return _run_productive_binding_mode(
        out,
        signal_matrix_path=args.signal_matrix,
        productive_binding_path=args.productive_binding,
        strategy_id=args.parameter_grid,
    )


if __name__ == "__main__":
    raise SystemExit(main())
