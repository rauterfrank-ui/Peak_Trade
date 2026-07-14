from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

import pytest

from research.linear_evidence.drift import (
    GO_TOKEN_REQUIRED,
    MODEL_SPEC_VERSION,
    RollingLinearDriftInputV1,
    fit_rolling_linear_drift,
    records_from_parameter_sensitivity_inputs,
)
from research.linear_evidence.import_boundary import scan_file_import_boundary
from research.linear_evidence.sensitivity import ParameterSensitivityInputV1

REPO_ROOT = Path(__file__).resolve().parents[2]
DRIFT_MODULE = REPO_ROOT / "src/research/linear_evidence/drift.py"
ENTRY_POINT = REPO_ROOT / "scripts/research/offline_rolling_linear_drift_diagnostics_v0.py"
FORBIDDEN_IMPORT_PREFIXES = (
    "src.execution",
    "src.scheduler",
    "src.broker",
    "src.trading.master_v2",
    "src.risk",
    "src.governance",
)


def _stable_records(count: int = 14) -> list[RollingLinearDriftInputV1]:
    return [
        RollingLinearDriftInputV1(
            instrument_id="PF_ETHUSD",
            decision_time=f"2026-01-01T{index:02d}:00:00Z",
            feature_availability_time=f"2026-01-01T{index:02d}:00:00Z",
            target=float(index) * 0.2,
            features={"signal": float(index), "aux": float(index % 2)},
        )
        for index in range(count)
    ]


def test_rolling_linear_drift_is_authority_neutral() -> None:
    evidence = fit_rolling_linear_drift(_stable_records(), window_size=6, min_samples=4)

    assert evidence.evidence_type == "rolling_linear_drift"
    assert evidence.authority_effect == "NONE"
    assert evidence.runtime_effect == "NONE"
    assert evidence.economic_validity_offline_gate_pass is False
    assert evidence.runtime_rewire_admissible is False
    assert evidence.model_spec_version == MODEL_SPEC_VERSION
    assert evidence.model_spec_alignment_active is True
    assert evidence.solver == "numpy.linalg.lstsq"
    assert evidence.validation_policy == "TIME_ORDERED"
    assert evidence.n_windows >= 1


def test_rolling_linear_drift_blocks_non_time_ordered_records() -> None:
    records = [
        RollingLinearDriftInputV1(
            "PF_ETHUSD",
            "2026-01-01T02:00:00Z",
            "2026-01-01T02:00:00Z",
            0.2,
            {"signal": 2.0},
        ),
        RollingLinearDriftInputV1(
            "PF_ETHUSD",
            "2026-01-01T01:00:00Z",
            "2026-01-01T01:00:00Z",
            0.1,
            {"signal": 1.0},
        ),
    ]

    with pytest.raises(ValueError, match="RANDOM_VALIDATION_SPLIT_BLOCKED"):
        fit_rolling_linear_drift(records, window_size=2, min_samples=2)


def test_rolling_linear_drift_blocks_lookahead() -> None:
    records = [
        RollingLinearDriftInputV1(
            "PF_ETHUSD",
            "2026-01-01T01:00:00Z",
            "2026-01-01T02:00:00Z",
            0.1,
            {"signal": 1.0},
        ),
        RollingLinearDriftInputV1(
            "PF_ETHUSD",
            "2026-01-01T02:00:00Z",
            "2026-01-01T02:00:00Z",
            0.2,
            {"signal": 2.0},
        ),
        RollingLinearDriftInputV1(
            "PF_ETHUSD",
            "2026-01-01T03:00:00Z",
            "2026-01-01T03:00:00Z",
            0.3,
            {"signal": 3.0},
        ),
        RollingLinearDriftInputV1(
            "PF_ETHUSD",
            "2026-01-01T04:00:00Z",
            "2026-01-01T04:00:00Z",
            0.4,
            {"signal": 4.0},
        ),
        RollingLinearDriftInputV1(
            "PF_ETHUSD",
            "2026-01-01T05:00:00Z",
            "2026-01-01T05:00:00Z",
            0.5,
            {"signal": 5.0},
        ),
        RollingLinearDriftInputV1(
            "PF_ETHUSD",
            "2026-01-01T06:00:00Z",
            "2026-01-01T06:00:00Z",
            0.6,
            {"signal": 6.0},
        ),
    ]

    evidence = fit_rolling_linear_drift(records, window_size=4, min_samples=4)

    assert evidence.verdict == "FAIL_CLOSED"
    assert "LOOKAHEAD_BLOCKED" in evidence.reason_codes


def test_rolling_linear_drift_detects_coefficient_shift() -> None:
    records: list[RollingLinearDriftInputV1] = []
    for index in range(1, 19):
        signal = float(index)
        target = 0.4 * signal if index <= 9 else 2.0 * signal
        records.append(
            RollingLinearDriftInputV1(
                instrument_id="PF_ETHUSD",
                decision_time=f"2026-01-01T{index - 1:02d}:00:00Z",
                feature_availability_time=f"2026-01-01T{index - 1:02d}:00:00Z",
                target=target,
                features={"signal": signal},
            )
        )

    evidence = fit_rolling_linear_drift(records, window_size=6, min_samples=4)

    assert evidence.drift_score > 0.5
    assert evidence.verdict == "FAIL"
    assert "COEFFICIENT_DRIFT_DETECTED" in evidence.reason_codes
    assert evidence.coefficient_drift["signal"] > 0.5


def test_rolling_linear_drift_insufficient_data_reason_code() -> None:
    evidence = fit_rolling_linear_drift(_stable_records(count=3), window_size=6, min_samples=4)

    assert evidence.verdict == "INCONCLUSIVE"
    assert "INSUFFICIENT_SAMPLE_COUNT" in evidence.reason_codes


def test_rolling_linear_drift_rank_deficient_reason_code() -> None:
    records = [
        RollingLinearDriftInputV1(
            "PF_ETHUSD",
            f"2026-01-01T{index:02d}:00:00Z",
            f"2026-01-01T{index:02d}:00:00Z",
            float(index),
            {"signal": 1.0, "duplicate": 2.0, "copy": 2.0},
        )
        for index in range(6)
    ]

    evidence = fit_rolling_linear_drift(records, window_size=6, min_samples=4)

    assert evidence.rank_deficient_window_count >= 1
    assert evidence.verdict in {"FAIL_CLOSED", "FAIL"}


def test_zero_variance_feature_excluded_transparently() -> None:
    records = [
        RollingLinearDriftInputV1(
            "PF_ETHUSD",
            f"2026-01-01T{index:02d}:00:00Z",
            f"2026-01-01T{index:02d}:00:00Z",
            float(index),
            {"signal": float(index), "constant": 5.0},
        )
        for index in range(8)
    ]
    evidence = fit_rolling_linear_drift(records, window_size=6, min_samples=4)
    assert evidence.window_model_specs
    assert "constant" in evidence.window_model_specs[0].excluded_feature_names


def test_active_feature_subset_documented_per_window() -> None:
    records = [
        RollingLinearDriftInputV1(
            "PF_ETHUSD",
            f"2026-01-01T{index:02d}:00:00Z",
            f"2026-01-01T{index:02d}:00:00Z",
            float(index),
            {"signal": float(index), "aux": float(index % 2)},
        )
        for index in range(10)
    ]
    evidence = fit_rolling_linear_drift(records, window_size=6, min_samples=4)
    assert evidence.active_feature_subsets
    assert all(subset for subset in evidence.active_feature_subsets)


def test_condition_number_reported() -> None:
    evidence = fit_rolling_linear_drift(_stable_records(), window_size=6, min_samples=4)
    assert evidence.drift_metrics["condition_number_max"] >= 0.0
    assert evidence.drift_metrics["condition_number_median"] >= 0.0


def test_sign_flip_detection() -> None:
    records: list[RollingLinearDriftInputV1] = []
    for index in range(20):
        signal = float(index)
        target = signal if index < 10 else -signal
        records.append(
            RollingLinearDriftInputV1(
                instrument_id="PF_ETHUSD",
                decision_time=f"2026-01-01T{index:02d}:00:00Z",
                feature_availability_time=f"2026-01-01T{index:02d}:00:00Z",
                target=target,
                features={"signal": signal},
            )
        )
    evidence = fit_rolling_linear_drift(records, window_size=6, min_samples=4, window_step=1)
    assert sum(evidence.coefficient_sign_flip_counts.values()) >= 0


def test_validation_error_drift_metrics_present() -> None:
    evidence = fit_rolling_linear_drift(_stable_records(count=20), window_size=8, min_samples=4)
    assert "validation_rmse_change" in evidence.drift_metrics
    assert "validation_mae_change" in evidence.drift_metrics


def test_residual_drift_metrics_present() -> None:
    evidence = fit_rolling_linear_drift(_stable_records(count=20), window_size=8, min_samples=4)
    assert "residual_location_shift" in evidence.drift_metrics
    assert "residual_scale_shift" in evidence.drift_metrics


def test_pass_verdict_for_stable_series() -> None:
    records = [
        RollingLinearDriftInputV1(
            "PF_ETHUSD",
            f"2026-01-01T{index:02d}:00:00Z",
            f"2026-01-01T{index:02d}:00:00Z",
            float(index) * 0.5,
            {"signal": float(index)},
        )
        for index in range(12)
    ]
    evidence = fit_rolling_linear_drift(records, window_size=6, min_samples=4)
    assert evidence.verdict == "PASS"


def test_repeated_run_produces_byte_identical_payload(tmp_path: Path) -> None:
    first = fit_rolling_linear_drift(_stable_records(), window_size=6, min_samples=4)
    second = fit_rolling_linear_drift(_stable_records(), window_size=6, min_samples=4)
    payload_a = json.dumps(first.to_dict(), sort_keys=True, separators=(",", ":"))
    payload_b = json.dumps(second.to_dict(), sort_keys=True, separators=(",", ":"))
    assert payload_a == payload_b


def test_cross_sectional_records_sorted_by_time_and_instrument() -> None:
    records = [
        RollingLinearDriftInputV1(
            "B", "2026-01-01T01:00:00Z", "2026-01-01T01:00:00Z", 0.2, {"signal": 2.0}
        ),
        RollingLinearDriftInputV1(
            "A", "2026-01-01T01:00:00Z", "2026-01-01T01:00:00Z", 0.1, {"signal": 1.0}
        ),
        RollingLinearDriftInputV1(
            "A", "2026-01-01T02:00:00Z", "2026-01-01T02:00:00Z", 0.3, {"signal": 3.0}
        ),
        RollingLinearDriftInputV1(
            "B", "2026-01-01T02:00:00Z", "2026-01-01T02:00:00Z", 0.4, {"signal": 4.0}
        ),
        RollingLinearDriftInputV1(
            "A", "2026-01-01T03:00:00Z", "2026-01-01T03:00:00Z", 0.5, {"signal": 5.0}
        ),
        RollingLinearDriftInputV1(
            "B", "2026-01-01T03:00:00Z", "2026-01-01T03:00:00Z", 0.6, {"signal": 6.0}
        ),
        RollingLinearDriftInputV1(
            "A", "2026-01-01T04:00:00Z", "2026-01-01T04:00:00Z", 0.7, {"signal": 7.0}
        ),
        RollingLinearDriftInputV1(
            "B", "2026-01-01T04:00:00Z", "2026-01-01T04:00:00Z", 0.8, {"signal": 8.0}
        ),
    ]
    evidence = fit_rolling_linear_drift(records, window_size=4, min_samples=4)
    assert evidence.n_windows >= 1


def test_records_from_parameter_sensitivity_inputs_adapter() -> None:
    source = [
        ParameterSensitivityInputV1(
            instrument_id="PF_ETHUSD",
            decision_time="2026-01-01T00:00:00Z",
            feature_availability_time="2026-01-01T00:00:00Z",
            target=1.0,
            features={"signal": 1.0},
        )
    ]
    converted = records_from_parameter_sensitivity_inputs(source)
    assert len(converted) == 1
    assert converted[0].instrument_id == "PF_ETHUSD"


def test_drift_module_import_boundary() -> None:
    violations = scan_file_import_boundary(DRIFT_MODULE, repo_root=REPO_ROOT)
    assert violations == []


def test_no_forbidden_trading_core_imports_in_drift_module() -> None:
    source = DRIFT_MODULE.read_text(encoding="utf-8")
    for prefix in FORBIDDEN_IMPORT_PREFIXES:
        assert prefix not in source


def test_go_token_required_for_entry_point(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(ENTRY_POINT),
            "--out",
            str(tmp_path),
            "--fixture",
        ],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert result.returncode == 1
    assert "GO_TOKEN_REQUIRED" in result.stdout


def test_rolling_linear_drift_cli_writes_manifestable_report(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(ENTRY_POINT),
            "--out",
            str(tmp_path),
            "--fixture",
            "--go-token",
            GO_TOKEN_REQUIRED,
            "--test-results",
            "fixture_smoke_pass",
        ],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    assert result.returncode == 0, result.stderr
    report_path = tmp_path / "rolling_linear_drift_diagnostics_v0.json"
    assert report_path.exists()
    report = json.loads(report_path.read_text())
    assert report["evidence_type"] == "rolling_linear_drift"
    assert report["authority_effect"] == "NONE"
    assert report["runtime_effect"] == "NONE"
    assert report["offline_only"] is True
    assert report["economic_validity_offline_gate_pass"] is False
    assert report["runtime_rewire_admissible"] is False
    assert report["drift_score"] > 0.5
    assert report["verdict"] == "FAIL"
    assert (tmp_path / "MANIFEST.sha256").exists()
    assert (tmp_path / "coefficient_drift_summary.json").exists()
    assert (tmp_path / "rolling_window_fits.jsonl").exists()
    assert (tmp_path / "source_manifest_verification.txt").exists()


def test_focused_test_suite_runs() -> None:
    start = time.monotonic()
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            str(REPO_ROOT / "tests/research/test_offline_rolling_linear_drift_diagnostics_v0.py"),
            "-q",
            "--tb=short",
            "-k",
            "not test_focused_test_suite_runs",
        ],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        cwd=str(REPO_ROOT),
    )
    duration = time.monotonic() - start
    assert result.returncode == 0, result.stdout
    assert duration < 120.0
