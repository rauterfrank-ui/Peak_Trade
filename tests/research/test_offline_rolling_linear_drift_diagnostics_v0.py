from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from research.linear_evidence.drift import RollingLinearDriftInputV1, fit_rolling_linear_drift


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
    assert evidence.solver == "numpy.linalg.lstsq"
    assert evidence.validation_policy == "TIME_ORDERED"
    assert evidence.n_windows >= 1
    assert all(window.solver == "numpy.linalg.lstsq" for window in evidence.window_evidence)


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

    assert evidence.status == "LEAKAGE_BLOCKED"
    assert evidence.reason_codes == ("LOOKAHEAD_BLOCKED",)


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
    assert "COEFFICIENT_DRIFT_DETECTED" in evidence.reason_codes
    assert evidence.coefficient_drift["signal"] > 0.5


def test_rolling_linear_drift_insufficient_data_reason_code() -> None:
    evidence = fit_rolling_linear_drift(_stable_records(count=3), window_size=6, min_samples=4)

    assert evidence.status == "INSUFFICIENT_DATA"
    assert evidence.reason_codes == ("INSUFFICIENT_SAMPLE_COUNT",)


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

    assert evidence.status == "RANK_DEFICIENT_BLOCKED"
    assert "HIGH_CONDITION_NUMBER" in evidence.reason_codes


def test_rolling_linear_drift_cli_writes_manifestable_report(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/research/offline_rolling_linear_drift_diagnostics_v0.py",
            "--out",
            str(tmp_path),
        ],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    assert result.returncode == 0, result.stderr
    report_path = tmp_path / "rolling_linear_drift_evidence_v1.json"
    assert report_path.exists()
    report = json.loads(report_path.read_text())
    assert report["evidence_type"] == "rolling_linear_drift"
    assert report["authority_effect"] == "NONE"
    assert report["runtime_effect"] == "NONE"
    assert report["offline_only"] is True
    assert report["system_economic_evidence_admissible"] is False
    assert report["runtime_rewire_admissible"] is False
    assert report["drift_score"] > 0.5
    assert "COEFFICIENT_DRIFT_DETECTED" in report["reason_codes"]
