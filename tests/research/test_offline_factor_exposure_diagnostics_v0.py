from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from research.linear_evidence.factor_exposure import FactorExposureInputV1, fit_factor_exposure


def test_factor_exposure_is_authority_neutral() -> None:
    records = [
        FactorExposureInputV1(
            "PF_ETHUSD",
            i,
            float(i) * 0.001,
            {
                "market_beta": float(i),
                "liquidity_beta": float(i % 3),
                "volatility_beta": float(i % 5),
            },
        )
        for i in range(1, 12)
    ]

    evidence = fit_factor_exposure(records)

    assert evidence.evidence_type == "factor_exposure"
    assert evidence.authority_effect == "NONE"
    assert evidence.runtime_effect == "NONE"
    assert evidence.solver == "numpy.linalg.lstsq"
    assert evidence.validation_policy == "time_ordered"
    assert evidence.status in {"DIAGNOSTIC_ONLY", "ROBUSTNESS_FAILED", "RANK_DEFICIENT_BLOCKED"}


def test_factor_exposure_blocks_non_time_ordered_records() -> None:
    records = [
        FactorExposureInputV1("PF_ETHUSD", 2, 0.002, {"market_beta": 1.0}),
        FactorExposureInputV1("PF_ETHUSD", 1, 0.001, {"market_beta": 2.0}),
    ]

    try:
        fit_factor_exposure(records, min_samples=2)
    except ValueError as exc:
        assert str(exc) == "RANDOM_VALIDATION_SPLIT_BLOCKED"
    else:
        raise AssertionError("expected non-time-ordered records to fail closed")


def test_factor_exposure_cli_writes_manifestable_report(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/research/offline_factor_exposure_diagnostics_v0.py",
            "--out",
            str(tmp_path),
        ],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    assert result.returncode == 0, result.stderr
    report_path = tmp_path / "factor_exposure_evidence_v1.json"
    assert report_path.exists()
    report = json.loads(report_path.read_text())
    assert report["evidence_type"] == "factor_exposure"
    assert report["authority_effect"] == "NONE"
    assert report["runtime_effect"] == "NONE"
    assert report["offline_only"] is True
    assert report["system_economic_evidence_admissible"] is False
    assert report["runtime_rewire_admissible"] is False
