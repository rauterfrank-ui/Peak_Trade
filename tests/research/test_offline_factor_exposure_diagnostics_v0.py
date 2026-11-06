from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from research.linear_evidence.factor_exposure import (
    REASON_FACTOR_LOOKAHEAD_DETECTED,
    REASON_FACTOR_TIME_BINDING_MISSING,
    REASON_FIXTURE_SCAFFOLD_DIAGNOSTIC_ONLY,
    REASON_HIGH_CONDITION_NUMBER,
    REASON_INSUFFICIENT_SAMPLE_COUNT,
    REASON_NON_MONOTONIC_TIME_ORDER,
    REASON_PERFECT_COLLINEARITY_DETECTED,
    REASON_PRODUCTIVE_BINDING_MISSING,
    REASON_STRICT_ZERO_VARIANCE_FACTOR_EXCLUDED,
    REASON_ZERO_VARIANCE_FACTOR,
    FactorExposureConfigV1,
    FactorExposureInputV1,
    build_factor_matrix,
    fit_factor_exposure,
    make_deterministic_factor_exposure_fixture,
)
from research.linear_evidence.import_boundary import scan_file_import_boundary

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNNER = REPO_ROOT / "scripts/research/offline_factor_exposure_diagnostics_v0.py"
OWNER = REPO_ROOT / "src/research/linear_evidence/factor_exposure.py"


def _record(
    *,
    timestamp: int,
    target_return: float | None = None,
    factor_values: dict[str, float] | None = None,
    factor_time: str | None = None,
    decision_time: str | None = None,
    instrument_id: str = "PF_ETHUSD",
) -> FactorExposureInputV1:
    return FactorExposureInputV1(
        instrument_id=instrument_id,
        timestamp=timestamp,
        target_return=0.01 if target_return is None else target_return,
        factor_values=factor_values
        or {
            "market_beta": float(timestamp) * 0.01,
            "liquidity_beta": float(timestamp % 3) * 0.01,
            "volatility_beta": float(timestamp % 5) * 0.01,
        },
        factor_time=factor_time,
        decision_time=decision_time,
    )


def _records(count: int = 12) -> list[FactorExposureInputV1]:
    return [_record(timestamp=i) for i in range(1, count + 1)]


def test_fixture_truth_pack_runs_deterministically() -> None:
    first = fit_factor_exposure(
        make_deterministic_factor_exposure_fixture(),
        fixture_scaffold=True,
    )
    second = fit_factor_exposure(
        make_deterministic_factor_exposure_fixture(),
        fixture_scaffold=True,
    )
    assert first.feature_matrix_digest == second.feature_matrix_digest
    assert first.config_digest == second.config_digest
    assert first.to_dict() == second.to_dict()


def test_repeat_run_identical_digests() -> None:
    records = _records()
    first = fit_factor_exposure(records).to_dict()
    second = fit_factor_exposure(records).to_dict()
    assert first == second


def test_stable_factor_ordering_independent_of_input_order() -> None:
    records = _records()
    shuffled_factors = [
        FactorExposureInputV1(
            record.instrument_id,
            record.timestamp,
            record.target_return,
            {
                "volatility_beta": record.factor_values["volatility_beta"],
                "market_beta": record.factor_values["market_beta"],
                "liquidity_beta": record.factor_values["liquidity_beta"],
            },
            factor_time=record.factor_time,
            decision_time=record.decision_time,
        )
        for record in records
    ]
    first = fit_factor_exposure(records)
    second = fit_factor_exposure(shuffled_factors)
    assert (
        first.feature_names
        == second.feature_names
        == (
            "liquidity_beta",
            "market_beta",
            "volatility_beta",
        )
    )
    assert first.feature_matrix_digest == second.feature_matrix_digest


def test_factor_time_before_decision_time_accepted() -> None:
    records = [
        _record(
            timestamp=1, factor_time="2026-01-01T01:00:00Z", decision_time="2026-01-01T02:00:00Z"
        ),
        _record(
            timestamp=2, factor_time="2026-01-01T02:00:00Z", decision_time="2026-01-01T03:00:00Z"
        ),
        _record(
            timestamp=3, factor_time="2026-01-01T03:00:00Z", decision_time="2026-01-01T04:00:00Z"
        ),
        _record(
            timestamp=4, factor_time="2026-01-01T04:00:00Z", decision_time="2026-01-01T05:00:00Z"
        ),
        _record(
            timestamp=5, factor_time="2026-01-01T05:00:00Z", decision_time="2026-01-01T06:00:00Z"
        ),
        _record(
            timestamp=6, factor_time="2026-01-01T06:00:00Z", decision_time="2026-01-01T07:00:00Z"
        ),
        _record(
            timestamp=7, factor_time="2026-01-01T07:00:00Z", decision_time="2026-01-01T08:00:00Z"
        ),
        _record(
            timestamp=8, factor_time="2026-01-01T08:00:00Z", decision_time="2026-01-01T09:00:00Z"
        ),
    ]
    evidence = fit_factor_exposure(records, config=FactorExposureConfigV1(min_samples=8))
    assert evidence.status == "DIAGNOSTIC_ONLY"


def test_equal_factor_and_decision_time_blocked() -> None:
    records = _records(8)
    records[3] = _record(
        timestamp=4,
        factor_time="2026-01-01T05:00:00Z",
        decision_time="2026-01-01T05:00:00Z",
    )
    with pytest.raises(ValueError, match=REASON_FACTOR_LOOKAHEAD_DETECTED):
        build_factor_matrix(records)


def test_factor_time_after_decision_time_blocked() -> None:
    records = _records(8)
    records[3] = _record(
        timestamp=4,
        factor_time="2026-01-01T06:00:00Z",
        decision_time="2026-01-01T05:00:00Z",
    )
    with pytest.raises(ValueError, match=REASON_FACTOR_LOOKAHEAD_DETECTED):
        build_factor_matrix(records)


def test_missing_factor_time_blocked() -> None:
    record = _record(timestamp=1, factor_time="", decision_time="2026-01-01T02:00:00Z")
    with pytest.raises(ValueError, match=REASON_FACTOR_TIME_BINDING_MISSING):
        build_factor_matrix([record])


def test_non_monotonic_time_order_blocked() -> None:
    records = [
        _record(
            timestamp=2, factor_time="2026-01-01T02:00:00Z", decision_time="2026-01-01T03:00:00Z"
        ),
        _record(
            timestamp=1, factor_time="2026-01-01T01:00:00Z", decision_time="2026-01-01T02:00:00Z"
        ),
    ]
    with pytest.raises(ValueError, match=REASON_NON_MONOTONIC_TIME_ORDER):
        build_factor_matrix(records)


def test_zero_variance_blocked_before_fit() -> None:
    records = [
        _record(
            timestamp=i,
            factor_values={
                "market_beta": 1.0,
                "liquidity_beta": float(i),
                "volatility_beta": float(i % 3),
            },
        )
        for i in range(1, 12)
    ]
    evidence = fit_factor_exposure(records)
    assert f"{REASON_STRICT_ZERO_VARIANCE_FACTOR_EXCLUDED}:market_beta" in evidence.reason_codes
    assert evidence.excluded_factor_names == ("market_beta",)
    assert evidence.excluded_factor_count == 1
    assert evidence.original_feature_names == ("liquidity_beta", "market_beta", "volatility_beta")
    assert evidence.effective_feature_names == ("liquidity_beta", "volatility_beta")
    assert evidence.original_n_features == 3
    assert evidence.effective_n_features == 2
    assert evidence.diagnostics["computed"] is True
    assert set(evidence.coefficients.keys()) == {"intercept", "liquidity_beta", "volatility_beta"}


def test_strict_zero_variance_exclusion_multiple_factors_order_stable() -> None:
    records = [
        _record(
            timestamp=i,
            factor_values={
                "a_const": 2.0,
                "b_const": -1.0,
                "c_var": float(i),
            },
        )
        for i in range(1, 12)
    ]
    evidence = fit_factor_exposure(records)
    assert evidence.original_feature_names == ("a_const", "b_const", "c_var")
    assert evidence.excluded_factor_names == ("a_const", "b_const")
    assert evidence.excluded_factor_count == 2
    assert evidence.effective_feature_names == ("c_var",)
    assert evidence.original_n_features == 3
    assert evidence.effective_n_features == 1
    assert evidence.reason_codes == (
        f"{REASON_STRICT_ZERO_VARIANCE_FACTOR_EXCLUDED}:a_const",
        f"{REASON_STRICT_ZERO_VARIANCE_FACTOR_EXCLUDED}:b_const",
    )
    assert evidence.diagnostics["computed"] is True
    assert set(evidence.coefficients.keys()) == {"intercept", "c_var"}


def test_all_factors_excluded_blocks_before_solver_invocation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    called = {"lstsq": 0}

    def _boom(*_args, **_kwargs):  # type: ignore[no-untyped-def]
        called["lstsq"] += 1
        raise AssertionError("SOLVER_SHOULD_NOT_BE_CALLED_WHEN_ALL_FACTORS_EXCLUDED")

    monkeypatch.setattr(np.linalg, "lstsq", _boom)
    records = [
        _record(
            timestamp=i,
            factor_values={
                "a_const": 1.0,
                "b_const": 1.0,
                "c_const": 1.0,
            },
        )
        for i in range(1, 12)
    ]
    evidence = fit_factor_exposure(records)
    assert called["lstsq"] == 0
    assert evidence.diagnostics["computed"] is False
    assert evidence.coefficients == {}
    assert evidence.status == "RANK_DEFICIENT_BLOCKED"
    assert evidence.original_feature_names == ("a_const", "b_const", "c_const")
    assert evidence.effective_feature_names == ()
    assert evidence.original_n_features == 3
    assert evidence.effective_n_features == 0
    assert evidence.excluded_factor_names == ("a_const", "b_const", "c_const")
    assert evidence.excluded_factor_count == 3
    assert evidence.reason_codes == (
        f"{REASON_STRICT_ZERO_VARIANCE_FACTOR_EXCLUDED}:a_const",
        f"{REASON_STRICT_ZERO_VARIANCE_FACTOR_EXCLUDED}:b_const",
        f"{REASON_STRICT_ZERO_VARIANCE_FACTOR_EXCLUDED}:c_const",
        "RANK_DEFICIENT_FEATURE_MATRIX",
    )


def test_near_zero_variance_not_excluded(monkeypatch: pytest.MonkeyPatch) -> None:
    # variance strictly > 0 after canonical float normalization
    records = [
        _record(
            timestamp=i,
            factor_values={
                "near_zero": 1e-12 if i % 2 == 0 else 0.0,
                "var": float(i),
            },
        )
        for i in range(1, 12)
    ]
    evidence = fit_factor_exposure(records)
    assert evidence.diagnostics["computed"] is True
    assert evidence.effective_feature_names == ("near_zero", "var")
    assert evidence.excluded_factor_names == ()
    assert evidence.excluded_factor_count == 0
    assert not any(
        str(code).startswith(f"{REASON_STRICT_ZERO_VARIANCE_FACTOR_EXCLUDED}:near_zero")
        for code in evidence.reason_codes
    )


def test_exclusion_stage_before_prechecks(monkeypatch: pytest.MonkeyPatch) -> None:
    import research.linear_evidence.factor_exposure as owner

    seen = {"shape": None}
    orig = owner.compute_factor_exposure_precheck_v0

    def _wrapped(matrix, factor_names, *, min_samples):  # type: ignore[no-untyped-def]
        seen["shape"] = (int(matrix.shape[0]), int(matrix.shape[1]), tuple(factor_names))
        return orig(matrix, factor_names, min_samples=min_samples)

    monkeypatch.setattr(owner, "compute_factor_exposure_precheck_v0", _wrapped)
    records = [
        _record(
            timestamp=i,
            factor_values={
                "a_const": 1.0,
                "b_var": float(i),
            },
        )
        for i in range(1, 12)
    ]
    evidence = fit_factor_exposure(records)
    assert evidence.diagnostics["computed"] is True
    assert seen["shape"] == (11, 1, ("b_var",))


def test_perfect_collinearity_detected_deterministically() -> None:
    records = [
        _record(
            timestamp=i,
            factor_values={
                "market_beta": float(i),
                "liquidity_beta": float(i * 2),
                "volatility_beta": float(i * 3),
            },
        )
        for i in range(1, 12)
    ]
    evidence = fit_factor_exposure(records)
    assert REASON_PERFECT_COLLINEARITY_DETECTED in evidence.reason_codes
    assert evidence.coefficients == {}
    assert evidence.diagnostics["computed"] is False


def test_correlation_and_vif_computed_on_admissible_matrix() -> None:
    records = _records()
    evidence = fit_factor_exposure(records)
    assert evidence.diagnostics["computed"] is True
    assert evidence.diagnostics["pairwise_correlation"]
    assert evidence.diagnostics["vif_scores"]


def test_productive_binding_missing_fail_closed_without_fixture() -> None:
    evidence = fit_factor_exposure([], productive_binding_gap=True)
    assert REASON_PRODUCTIVE_BINDING_MISSING in evidence.reason_codes
    assert evidence.diagnostics["computed"] is False


def test_fixture_scaffold_explicit_diagnostic_only() -> None:
    evidence = fit_factor_exposure(
        make_deterministic_factor_exposure_fixture(),
        fixture_scaffold=True,
    )
    assert REASON_FIXTURE_SCAFFOLD_DIAGNOSTIC_ONLY in evidence.reason_codes


def test_authority_and_runtime_effects_none() -> None:
    evidence = fit_factor_exposure(_records())
    assert evidence.authority_effect == "NONE"
    assert evidence.runtime_effect == "NONE"


def test_insufficient_sample_count_blocks() -> None:
    evidence = fit_factor_exposure(_records(4), config=FactorExposureConfigV1(min_samples=8))
    assert REASON_INSUFFICIENT_SAMPLE_COUNT in evidence.reason_codes


def test_no_runtime_order_or_scheduler_imports_in_owner() -> None:
    hits = scan_file_import_boundary(OWNER, repo_root=REPO_ROOT)
    assert hits == []


def test_cli_fixture_scaffold_writes_manifestable_report(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(RUNNER),
            "--out",
            str(tmp_path),
            "--fixture-scaffold",
            "--repo-root",
            str(REPO_ROOT),
        ],
        check=False,
        text=True,
        capture_output=True,
        cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(
        (tmp_path / "factor_exposure_evidence_v1.json").read_text(encoding="utf-8")
    )
    assert payload["authority_effect"] == "NONE"
    assert payload["runtime_effect"] == "NONE"
    assert payload["FIXTURE_SCAFFOLD_USED"] is True
    assert payload["INPUT_MODE"] == "FIXTURE_SCAFFOLD"


def test_cli_productive_binding_requested_without_input_fail_closed(tmp_path: Path) -> None:
    empty_input = tmp_path / "empty.jsonl"
    empty_input.write_text("", encoding="utf-8")
    out_dir = tmp_path / "out"
    result = subprocess.run(
        [
            sys.executable,
            str(RUNNER),
            "--out",
            str(out_dir),
            "--input-jsonl",
            str(empty_input),
            "--repo-root",
            str(REPO_ROOT),
        ],
        check=False,
        text=True,
        capture_output=True,
        cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0
    payload = json.loads((out_dir / "factor_exposure_evidence_v1.json").read_text(encoding="utf-8"))
    assert payload["PRODUCTIVE_BINDING_REQUESTED"] is True
    assert payload["PRODUCTIVE_BINDING_RESOLVED"] is False
    assert "PRODUCTIVE_BINDING_MISSING" in payload["reason_codes"]
