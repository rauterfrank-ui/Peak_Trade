from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNNER_MODULE = REPO_ROOT / "scripts/research/offline_linear_cost_model_diagnostics_v0.py"
ARCHIVE_ROOT = Path("/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z")
LEDGER_PATH = (
    ARCHIVE_ROOT
    / "trade_ledger_equity_curve_persistence_offline_evaluation_execution_v0_20260705T083113Z"
    / "TRADE_LEDGER_V1.jsonl"
)
SNAPSHOT_PATH = (
    ARCHIVE_ROOT
    / "research/offline_linear_cost_entry_bar_reference_snapshot_materialization_v0_for_trend_following_v1_trade_ledger_binding_20260713T055132Z"
    / "entry_bar_snapshots.jsonl"
)

EXPECTED_MATERIALIZATION_DIGEST = "168b96afc3ba011ec7938881d0d51b92d5f5a24e880f6844704fe14339db639f"
EXPECTED_TARGET_DIGEST = "c646b627bfb6dc5c2f334536e2d7648e461c0894bcc8ccab1d2544120ca9e6e3"
EXPECTED_FEATURE_MATRIX_DIGEST = "f2c6815c5e2fcc8e5e9afdc37391a3a7d036cea9f87ef86a8587de01f23e2cc9"

from src.research.linear_evidence.feature_matrix import build_feature_matrix_binding
from src.research.linear_evidence.fitters import (
    REASON_CONSTANT_TARGET,
    REASON_CONSTANT_FEATURE_COLLINEAR_WITH_INTERCEPT,
    REASON_RANK_DEFICIENT_FEATURE_MATRIX,
    REASON_ZERO_VARIANCE_FEATURE,
    compute_ols_fit_precheck_v0,
    fit_ols_lstsq,
)
from src.research.offline_linear_cost_diagnostic_row_materializer_v0 import (
    TARGET_NAME,
    materialize_offline_linear_cost_diagnostic_rows_v0,
)


def _rows(
    *,
    constant_target: bool = False,
    constant_spread: bool = False,
) -> list[dict[str, object]]:
    spread_values = [10.0, 15.0, 12.0, 18.0, 11.0, 20.0, 14.0, 17.0, 13.0, 19.0, 16.0, 21.0]
    volatility_values = [
        0.010,
        0.020,
        0.015,
        0.025,
        0.012,
        0.030,
        0.018,
        0.022,
        0.016,
        0.028,
        0.019,
        0.031,
    ]
    notional_values = [
        1000.0,
        1100.0,
        1050.0,
        1200.0,
        1025.0,
        1300.0,
        1080.0,
        1150.0,
        1075.0,
        1250.0,
        1125.0,
        1325.0,
    ]
    rows: list[dict[str, object]] = []
    for index, (spread, volatility, notional) in enumerate(
        zip(spread_values, volatility_values, notional_values)
    ):
        rows.append(
            {
                "decision_time": f"2026-01-01T{index:02d}:00:00Z",
                "spread_bps": spread if not constant_spread else 10.0,
                "volatility_estimate": volatility,
                "order_notional": notional,
                TARGET_NAME: 5.0 if constant_target else float(5 + index),
            }
        )
    return rows


def _binding(
    rows: list[dict[str, object]], feature_names: tuple[str, ...]
) -> tuple[np.ndarray, np.ndarray, object]:
    return build_feature_matrix_binding(
        rows,
        feature_names=feature_names,
        target_name=TARGET_NAME,
    )


def _run_cli(
    tmp_path: Path, extra_args: list[str] | None = None
) -> subprocess.CompletedProcess[str]:
    args = [sys.executable, str(RUNNER_MODULE), "--out", str(tmp_path)]
    if extra_args:
        args.extend(extra_args)
    return subprocess.run(
        args,
        check=False,
        text=True,
        capture_output=True,
        cwd=str(REPO_ROOT),
    )


def _archive_inputs_available() -> bool:
    return LEDGER_PATH.is_file() and SNAPSHOT_PATH.is_file()


def _fit_with_lstsq_spy(
    x: np.ndarray,
    y: np.ndarray,
    binding: object,
    **kwargs: object,
) -> tuple[object, bool]:
    import numpy.linalg as npla

    called = False
    original_lstsq = npla.lstsq

    def _spy_lstsq(*args, **kwargs_inner):  # type: ignore[no-untyped-def]
        nonlocal called
        called = True
        return original_lstsq(*args, **kwargs_inner)

    npla.lstsq = _spy_lstsq
    try:
        evidence = fit_ols_lstsq(x, y, binding, **kwargs)
    finally:
        npla.lstsq = original_lstsq
    return evidence, called


def test_constant_target_blocks_before_solver_with_fail_closed_evidence() -> None:
    x, y, binding = _binding(_rows(constant_target=True), ("spread_bps", "volatility_estimate"))
    precheck = compute_ols_fit_precheck_v0(x, y, binding.feature_names)
    evidence, lstsq_called = _fit_with_lstsq_spy(x, y, binding)

    assert precheck.target_is_constant is True
    assert lstsq_called is False
    assert evidence.reason_codes[0] == REASON_CONSTANT_TARGET
    assert evidence.status == "INSUFFICIENT_DATA"
    assert evidence.coefficients == {}
    assert evidence.diagnostics.rank == 0
    assert evidence.diagnostics.condition_number == 0.0
    assert evidence.authority_effect == "NONE"
    assert evidence.runtime_effect == "NONE"


def test_non_constant_target_still_calls_solver() -> None:
    x, y, binding = _binding(_rows(), ("spread_bps", "volatility_estimate", "order_notional"))
    _, lstsq_called = _fit_with_lstsq_spy(x, y, binding)

    assert lstsq_called is True


def test_constant_target_only_emits_constant_target_reason_code() -> None:
    x, y, binding = _binding(_rows(constant_target=True), ("spread_bps", "volatility_estimate"))
    precheck = compute_ols_fit_precheck_v0(x, y, binding.feature_names)
    evidence = fit_ols_lstsq(x, y, binding)

    assert precheck.target_is_constant is True
    assert evidence.reason_codes[0] == REASON_CONSTANT_TARGET
    assert evidence.status == "INSUFFICIENT_DATA"
    assert evidence.coefficients == {}


def test_zero_variance_feature_without_intercept_emits_feature_reason_only() -> None:
    rows = _rows(constant_spread=True)
    x, y, binding = _binding(rows, ("spread_bps", "volatility_estimate"))
    precheck = compute_ols_fit_precheck_v0(x, y, binding.feature_names, fit_intercept=False)
    evidence = fit_ols_lstsq(x, y, binding, fit_intercept=False)

    assert precheck.intercept_collinear_feature_names == ()
    assert f"{REASON_ZERO_VARIANCE_FEATURE}:spread_bps" in precheck.reason_codes
    assert not any(
        code.startswith(REASON_CONSTANT_FEATURE_COLLINEAR_WITH_INTERCEPT)
        for code in precheck.reason_codes
    )
    assert f"{REASON_ZERO_VARIANCE_FEATURE}:spread_bps" in evidence.reason_codes


def test_constant_feature_with_intercept_emits_collinearity_reason_code() -> None:
    x, y, binding = _binding(_rows(constant_spread=True), ("spread_bps", "volatility_estimate"))
    precheck = compute_ols_fit_precheck_v0(x, y, binding.feature_names, fit_intercept=True)
    evidence = fit_ols_lstsq(x, y, binding)

    assert precheck.zero_variance_feature_names == ("spread_bps",)
    assert precheck.intercept_collinear_feature_names == ("spread_bps",)
    assert evidence.reason_codes.index(
        f"{REASON_ZERO_VARIANCE_FEATURE}:spread_bps"
    ) < evidence.reason_codes.index(
        f"{REASON_CONSTANT_FEATURE_COLLINEAR_WITH_INTERCEPT}:spread_bps"
    )
    assert evidence.status == "RANK_DEFICIENT_BLOCKED"
    assert REASON_RANK_DEFICIENT_FEATURE_MATRIX in evidence.reason_codes


def test_multiple_zero_variance_features_use_deterministic_ordering() -> None:
    rows = [
        {
            "decision_time": f"2026-01-01T{index:02d}:00:00Z",
            "alpha": 1.0,
            "beta": 2.0,
            "gamma": float(index + 1),
            TARGET_NAME: float(index + 2),
        }
        for index in range(12)
    ]
    x, y, binding = _binding(rows, ("alpha", "beta", "gamma"))
    precheck = compute_ols_fit_precheck_v0(x, y, binding.feature_names)

    assert precheck.zero_variance_feature_names == ("alpha", "beta")
    assert precheck.reason_codes == (
        f"{REASON_ZERO_VARIANCE_FEATURE}:alpha",
        f"{REASON_ZERO_VARIANCE_FEATURE}:beta",
        f"{REASON_CONSTANT_FEATURE_COLLINEAR_WITH_INTERCEPT}:alpha",
        f"{REASON_CONSTANT_FEATURE_COLLINEAR_WITH_INTERCEPT}:beta",
    )


def test_full_rank_varying_target_and_features_have_no_precheck_reason_codes() -> None:
    x, y, binding = _binding(_rows(), ("spread_bps", "volatility_estimate", "order_notional"))
    precheck = compute_ols_fit_precheck_v0(x, y, binding.feature_names)
    evidence = fit_ols_lstsq(x, y, binding)

    assert precheck.reason_codes == ()
    assert not any(
        code.startswith(
            (
                REASON_CONSTANT_TARGET,
                REASON_ZERO_VARIANCE_FEATURE,
                REASON_CONSTANT_FEATURE_COLLINEAR_WITH_INTERCEPT,
            )
        )
        for code in evidence.reason_codes
    )
    assert evidence.status in {"CALIBRATION_CANDIDATE", "ROBUSTNESS_FAILED"}
    assert REASON_RANK_DEFICIENT_FEATURE_MATRIX not in evidence.reason_codes


def test_affine_dependency_emits_rank_deficiency_without_zero_variance_precheck_codes() -> None:
    rows = [
        {
            "decision_time": f"2026-01-01T{index:02d}:00:00Z",
            "x1": float(index + 1),
            "x2": float(2 * (index + 1)),
            TARGET_NAME: float(index + 3),
        }
        for index in range(12)
    ]
    x, y, binding = _binding(rows, ("x1", "x2"))
    precheck = compute_ols_fit_precheck_v0(x, y, binding.feature_names)
    evidence = fit_ols_lstsq(x, y, binding)

    assert precheck.reason_codes == ()
    assert evidence.reason_codes == (REASON_RANK_DEFICIENT_FEATURE_MATRIX,)
    assert evidence.status == "RANK_DEFICIENT_BLOCKED"


@pytest.mark.skipif(not _archive_inputs_available(), reason="archive evidence unavailable")
def test_explicit_and_implicit_repo_root_cli_parity(tmp_path: Path) -> None:
    common_args = [
        "--trade-ledger",
        str(LEDGER_PATH),
        "--entry-bar-snapshots",
        str(SNAPSHOT_PATH),
    ]
    explicit = _run_cli(
        tmp_path / "explicit", extra_args=[*common_args, "--repo-root", str(REPO_ROOT)]
    )
    implicit = _run_cli(tmp_path / "implicit", extra_args=common_args)
    assert explicit.returncode == 0, explicit.stderr
    assert implicit.returncode == 0, implicit.stderr

    explicit_report = json.loads(
        (tmp_path / "explicit" / "offline_linear_cost_model_diagnostics_v0.json").read_text()
    )
    implicit_report = json.loads(
        (tmp_path / "implicit" / "offline_linear_cost_model_diagnostics_v0.json").read_text()
    )
    assert explicit_report == implicit_report


@pytest.mark.skipif(not _archive_inputs_available(), reason="archive evidence unavailable")
def test_archive_fixture_digests_unchanged_and_precheck_reason_codes_present(
    tmp_path: Path,
) -> None:
    result = _run_cli(
        tmp_path,
        extra_args=[
            "--trade-ledger",
            str(LEDGER_PATH),
            "--entry-bar-snapshots",
            str(SNAPSHOT_PATH),
            "--repo-root",
            str(REPO_ROOT),
        ],
    )
    assert result.returncode == 0, result.stderr
    report = json.loads((tmp_path / "offline_linear_cost_model_diagnostics_v0.json").read_text())
    assert report["materialization_digest"] == EXPECTED_MATERIALIZATION_DIGEST
    assert report["n_productive_samples"] == 219
    assert report["ols_executed"] is False
    assert report["calibration"] is None

    trade_rows = [
        json.loads(line)
        for line in LEDGER_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    snapshots = [
        json.loads(line)
        for line in SNAPSHOT_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    materialization = materialize_offline_linear_cost_diagnostic_rows_v0(
        trade_ledger_rows=trade_rows,
        entry_bar_reference_snapshots=snapshots,
        repo_root=REPO_ROOT,
    )
    productive_rows = [
        {
            "decision_time": row["decision_time"],
            "spread_bps": row["spread_bps"],
            "volatility_estimate": row["volatility_estimate"],
            "order_notional": row["order_notional"],
            TARGET_NAME: row[TARGET_NAME],
        }
        for row in materialization.rows
    ]
    x, y, binding = build_feature_matrix_binding(
        productive_rows,
        feature_names=("spread_bps", "volatility_estimate", "order_notional"),
        target_name=TARGET_NAME,
    )
    evidence = fit_ols_lstsq(x, y, binding)

    assert binding.target_digest == EXPECTED_TARGET_DIGEST
    assert binding.feature_matrix_digest == EXPECTED_FEATURE_MATRIX_DIGEST
    assert evidence.status == "RANK_DEFICIENT_BLOCKED"
    assert evidence.coefficients == {}
    assert evidence.reason_codes == (
        REASON_CONSTANT_TARGET,
        f"{REASON_ZERO_VARIANCE_FEATURE}:spread_bps",
        f"{REASON_CONSTANT_FEATURE_COLLINEAR_WITH_INTERCEPT}:spread_bps",
        REASON_RANK_DEFICIENT_FEATURE_MATRIX,
    )


@pytest.mark.skipif(not _archive_inputs_available(), reason="archive evidence unavailable")
def test_archive_fixture_entry_point_skips_calibration_when_constant_target_blocked(
    tmp_path: Path,
) -> None:
    result = _run_cli(
        tmp_path,
        extra_args=[
            "--trade-ledger",
            str(LEDGER_PATH),
            "--entry-bar-snapshots",
            str(SNAPSHOT_PATH),
            "--repo-root",
            str(REPO_ROOT),
        ],
    )
    assert result.returncode == 0, result.stderr
    report = json.loads((tmp_path / "offline_linear_cost_model_diagnostics_v0.json").read_text())
    assert report["ols_executed"] is False
    assert report["calibration"] is None
    assert "OLS_EXECUTED=false" in result.stdout
