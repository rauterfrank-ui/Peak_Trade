from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from research.linear_evidence.fitters import (
    REASON_CONSTANT_TARGET,
    REASON_ZERO_VARIANCE_FEATURE,
    fit_ols_lstsq,
)
from research.linear_evidence.feature_matrix import build_feature_matrix_binding
from research.linear_evidence.import_boundary import scan_file_import_boundary
from research.linear_evidence.signal_orthogonality import (
    REASON_DUPLICATE_SIGNAL,
    REASON_HIGH_PAIRWISE_CORRELATION,
    REASON_INSUFFICIENT_OVERLAP,
    REASON_INSUFFICIENT_SAMPLE_COUNT,
    REASON_NEAR_DUPLICATE_SIGNAL,
    REASON_SIGNAL_REDUNDANCY_REPORTED,
    REASON_ZERO_VARIANCE_FEATURE,
    SignalOrthogonalityConfigV1,
    SignalOrthogonalityScopePolicyV0,
    analyze_signal_orthogonality,
    build_signal_orthogonality_scope_artifacts_v0,
    compute_signal_orthogonality_precheck_v0,
    evidence_to_dict,
    make_deterministic_signal_fixture,
)
from research.offline_linear_cost_diagnostic_row_materializer_v0 import TARGET_NAME

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNNER = REPO_ROOT / "scripts/research/offline_signal_orthogonality_diagnostics_v0.py"
OWNER = REPO_ROOT / "src/research/linear_evidence/signal_orthogonality.py"


def _rows(
    *, constant_signal: str | None = None, zero_variance: str | None = None
) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    for idx in range(12):
        row = {
            "decision_time": f"2026-01-01T{idx + 1:02d}:00:00Z",
            "feature_time": f"2026-01-01T{idx:02d}:00:00Z",
            "alpha": float(idx + 1),
            "beta": float((idx + 1) * 2),
            "gamma": float((idx + 1) * 3 + (idx % 2)),
        }
        if constant_signal:
            row[constant_signal] = 5.0
        if zero_variance:
            row[zero_variance] = 7.0
        out.append(row)
    return out


def test_deterministic_feature_ordering_and_stable_digest() -> None:
    rows, features = make_deterministic_signal_fixture()
    shuffled = ("liquidity_context", "trend_following", "momentum_1h", "bollinger_bands")
    first = analyze_signal_orthogonality(rows, shuffled)
    second = analyze_signal_orthogonality(rows, features)

    assert first.feature_names == second.feature_names == features
    assert first.feature_matrix_digest == second.feature_matrix_digest
    assert first.config_digest == second.config_digest


def test_identical_repeated_output_and_second_run_diff_empty() -> None:
    rows, features = make_deterministic_signal_fixture()
    first = evidence_to_dict(analyze_signal_orthogonality(rows, features))
    second = evidence_to_dict(analyze_signal_orthogonality(rows, features))
    assert first == second


def test_time_order_and_lookahead_guard() -> None:
    rows = _rows()
    rows[0] = {**rows[0], "decision_time": ""}
    with pytest.raises(ValueError, match="TIME_BINDING_MISSING"):
        analyze_signal_orthogonality(rows, ("alpha", "beta", "gamma"))

    lookahead_rows = _rows()
    lookahead_rows[3]["feature_time"] = lookahead_rows[3]["decision_time"]
    with pytest.raises(ValueError, match="LOOKAHEAD_BLOCKED"):
        analyze_signal_orthogonality(lookahead_rows, ("alpha", "beta", "gamma"))


def test_constant_signal_pre_computation_block() -> None:
    rows = _rows(constant_signal="alpha")
    matrix = np.asarray(
        [[float(row["alpha"]), float(row["beta"]), float(row["gamma"])] for row in rows]
    )
    precheck = compute_signal_orthogonality_precheck_v0(
        matrix,
        ("alpha", "beta", "gamma"),
        min_samples=8,
    )
    evidence = analyze_signal_orthogonality(rows, ("gamma", "alpha", "beta"))

    assert precheck.blocking is True
    assert f"{REASON_ZERO_VARIANCE_FEATURE}:alpha" in evidence.reason_codes
    assert evidence.coefficients == {}
    assert evidence.diagnostics["computed"] is False
    assert evidence.diagnostics["pairwise_correlation"] == {}


def test_zero_variance_feature_block() -> None:
    rows = _rows(zero_variance="beta")
    evidence = analyze_signal_orthogonality(rows, ("alpha", "beta", "gamma"))

    assert f"{REASON_ZERO_VARIANCE_FEATURE}:beta" in evidence.reason_codes
    assert evidence.diagnostics["computed"] is False
    assert evidence.diagnostics["vif_scores"] == {}


def test_insufficient_sample_block() -> None:
    rows = _rows()[:4]
    evidence = analyze_signal_orthogonality(
        rows,
        ("alpha", "beta", "gamma"),
        config=SignalOrthogonalityConfigV1(min_samples=8),
    )

    assert REASON_INSUFFICIENT_SAMPLE_COUNT in evidence.reason_codes
    assert evidence.status == "INSUFFICIENT_DATA"
    assert evidence.diagnostics["computed"] is False


def test_pairwise_symmetry_and_diagonal_identity() -> None:
    rows, features = make_deterministic_signal_fixture()
    evidence = analyze_signal_orthogonality(
        rows,
        features,
        config=SignalOrthogonalityConfigV1(correlation_threshold=0.80),
    )
    corr = evidence.diagnostics["pairwise_correlation"]
    assert isinstance(corr, dict)
    for left, row in corr.items():
        assert row[left] == pytest.approx(1.0)
        for right, value in row.items():
            assert corr[right][left] == pytest.approx(value)


def test_finite_diagnostics_only_on_computed_path() -> None:
    rows, features = make_deterministic_signal_fixture()
    evidence = analyze_signal_orthogonality(rows, features)
    assert evidence.diagnostics["computed"] is True
    assert np.isfinite(float(evidence.diagnostics["condition_number"]))
    for row in evidence.diagnostics["pairwise_correlation"].values():
        for value in row.values():
            assert np.isfinite(value)


def test_stable_redundancy_classification() -> None:
    rows, features = make_deterministic_signal_fixture()
    evidence = analyze_signal_orthogonality(
        rows,
        features,
        config=SignalOrthogonalityConfigV1(correlation_threshold=0.80),
    )
    assert REASON_SIGNAL_REDUNDANCY_REPORTED in evidence.reason_codes
    assert evidence.diagnostics["redundant_pairs"]


def test_blocked_path_emits_no_fabricated_statistics() -> None:
    rows = _rows(constant_signal="alpha")
    evidence = analyze_signal_orthogonality(rows, ("alpha", "beta", "gamma"))
    assert evidence.coefficients == {}
    assert evidence.diagnostics["rank"] == 0
    assert evidence.diagnostics["condition_number"] is None
    assert evidence.diagnostics["redundant_pairs"] == []


def test_authority_and_runtime_effects_none() -> None:
    rows, features = make_deterministic_signal_fixture()
    evidence = analyze_signal_orthogonality(rows, features)
    assert evidence.authority_effect == "NONE"
    assert evidence.runtime_effect == "NONE"
    assert evidence.cost_policy_output == "diagnostic_only"
    assert evidence.validation_policy["strategy_selection_effect"] is False


def test_no_runtime_order_or_scheduler_imports_in_owner() -> None:
    hits = scan_file_import_boundary(OWNER, repo_root=REPO_ROOT)
    assert hits == []


def test_real_production_owner_invoked_by_focused_test() -> None:
    rows, features = make_deterministic_signal_fixture()
    evidence = analyze_signal_orthogonality(rows, features)
    assert evidence.evidence_type == "SignalOrthogonalityEvidenceV1"
    assert evidence.status in {"DIAGNOSTIC_ONLY", "RANK_DEFICIENT_BLOCKED", "INSUFFICIENT_DATA"}


def test_productive_binding_gap_fail_closed_without_fixture() -> None:
    evidence = analyze_signal_orthogonality([], ("alpha", "beta"), productive_binding_gap=True)
    assert "PRODUCTIVE_BINDING_GAP" in evidence.reason_codes
    assert evidence.diagnostics["computed"] is False


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
    assert "VERDICT=OFFLINE_SIGNAL_ORTHOGONALITY_DIAGNOSTICS_V0_COLLECTED" in result.stdout
    payload = json.loads(
        (tmp_path / "signal_orthogonality_evidence_v1.json").read_text(encoding="utf-8")
    )
    assert payload["authority_effect"] == "NONE"
    assert payload["runtime_effect"] == "NONE"
    assert payload["fixture_truth_pack_used"] is True
    assert payload["productive_binding_found"] is False


def test_existing_cost_model_constant_target_behavior_remains_green() -> None:
    rows = [
        {
            "decision_time": f"2026-01-01T{index:02d}:00:00Z",
            "spread_bps": float(10 + index),
            "volatility_estimate": float(0.01 + index * 0.001),
            "order_notional": float(1000 + index * 10),
            TARGET_NAME: 5.0,
        }
        for index in range(12)
    ]
    x, y, binding = build_feature_matrix_binding(
        rows,
        feature_names=("spread_bps", "volatility_estimate", "order_notional"),
        target_name=TARGET_NAME,
    )
    evidence = fit_ols_lstsq(x, y, binding)
    assert REASON_CONSTANT_TARGET in evidence.reason_codes
    assert evidence.coefficients == {}


def test_scope_artifacts_byte_identical_on_repeat() -> None:
    rows, features = make_deterministic_signal_fixture()
    policy = SignalOrthogonalityScopePolicyV0(min_samples=8, min_overlap_count=8)
    first = build_signal_orthogonality_scope_artifacts_v0(
        rows,
        features,
        policy=policy,
        fixture_truth_pack_used=True,
    )
    second = build_signal_orthogonality_scope_artifacts_v0(
        rows,
        features,
        policy=policy,
        fixture_truth_pack_used=True,
    )
    assert first["output_digest"] == second["output_digest"]


def test_duplicate_signals_detected_in_scope_artifacts() -> None:
    rows = _rows()
    for row in rows:
        row["copy_alpha"] = row["alpha"]
    artifacts = build_signal_orthogonality_scope_artifacts_v0(
        rows,
        ("alpha", "copy_alpha", "beta"),
        policy=SignalOrthogonalityScopePolicyV0(min_samples=4, min_overlap_count=4),
        fixture_truth_pack_used=True,
    )
    pair = next(
        item
        for item in artifacts["pairwise_correlations"]
        if {item["signal_a"], item["signal_b"]} == {"alpha", "copy_alpha"}
    )
    assert REASON_DUPLICATE_SIGNAL in pair["reason_codes"]
    assert artifacts["duplicate_groups"]["groups"]


def test_linear_scaled_signals_near_duplicate_or_high_correlation() -> None:
    rows = _rows()
    for row in rows:
        row["scaled_beta"] = float(row["beta"]) * 2.0
    artifacts = build_signal_orthogonality_scope_artifacts_v0(
        rows,
        ("beta", "scaled_beta", "gamma"),
        policy=SignalOrthogonalityScopePolicyV0(
            min_samples=4,
            min_overlap_count=4,
            near_duplicate_correlation_threshold=0.999,
        ),
        fixture_truth_pack_used=True,
    )
    pair = next(
        item
        for item in artifacts["pairwise_correlations"]
        if {item["signal_a"], item["signal_b"]} == {"beta", "scaled_beta"}
    )
    assert REASON_NEAR_DUPLICATE_SIGNAL in pair["reason_codes"]
    assert REASON_HIGH_PAIRWISE_CORRELATION in pair["reason_codes"]


def test_orthogonal_fixture_not_falsely_redundant() -> None:
    rows, features = make_deterministic_signal_fixture()
    artifacts = build_signal_orthogonality_scope_artifacts_v0(
        rows,
        ("bollinger_bands", "liquidity_context"),
        policy=SignalOrthogonalityScopePolicyV0(
            correlation_threshold=0.95,
            near_duplicate_correlation_threshold=0.999,
        ),
        fixture_truth_pack_used=True,
    )
    assert artifacts["signal_summary"]["duplicate_groups"] == []
    assert artifacts["signal_summary"]["near_duplicate_groups"] == []


def test_insufficient_overlap_classified() -> None:
    rows: list[dict[str, object]] = []
    for idx in range(12):
        rows.append(
            {
                "decision_time": f"2026-01-01T{idx + 1:02d}:00:00Z",
                "feature_time": f"2026-01-01T{idx:02d}:00:00Z",
                "alpha": float(idx) if idx < 2 else float("nan"),
                "beta": float(idx),
            }
        )
    artifacts = build_signal_orthogonality_scope_artifacts_v0(
        rows,
        ("alpha", "beta"),
        policy=SignalOrthogonalityScopePolicyV0(min_samples=4, min_overlap_count=8),
        fixture_truth_pack_used=True,
    )
    pair = artifacts["pairwise_correlations"][0]
    assert REASON_INSUFFICIENT_OVERLAP in pair["reason_codes"]
    assert pair["status"] == "BLOCKED"


def test_nan_and_inf_blocked_deterministically() -> None:
    rows = _rows()
    rows[2]["gamma"] = float("nan")
    rows[4]["gamma"] = float("inf")
    evidence = analyze_signal_orthogonality(rows, ("alpha", "beta", "gamma"))
    assert evidence.row_count_after_filter < evidence.row_count_before_filter
    assert "non_finite_feature" in evidence.dropped_rows_by_reason


def test_matrix_rank_and_condition_number_reproducible() -> None:
    rows, features = make_deterministic_signal_fixture()
    first = build_signal_orthogonality_scope_artifacts_v0(
        rows, features, fixture_truth_pack_used=True
    )
    second = build_signal_orthogonality_scope_artifacts_v0(
        rows, features, fixture_truth_pack_used=True
    )
    assert first["signal_summary"]["matrix_rank"] == second["signal_summary"]["matrix_rank"]
    assert (
        first["signal_summary"]["condition_number"] == second["signal_summary"]["condition_number"]
    )


def test_temporal_instability_visible_in_rolling_stability() -> None:
    rows: list[dict[str, object]] = []
    for idx in range(24):
        rows.append(
            {
                "decision_time": f"2026-01-01T{idx + 1:02d}:00:00Z",
                "feature_time": f"2026-01-01T{idx:02d}:00:00Z",
                "alpha": float(idx) if idx < 12 else float(-idx),
                "beta": float(idx),
            }
        )
    artifacts = build_signal_orthogonality_scope_artifacts_v0(
        rows,
        ("alpha", "beta"),
        policy=SignalOrthogonalityScopePolicyV0(
            min_samples=8,
            min_overlap_count=8,
            rolling_stability_instability_threshold=0.5,
            rolling_time_slice_count=2,
        ),
        fixture_truth_pack_used=True,
    )
    assert artifacts["rolling_stability"]["unstable_pairs"]


def test_scope_pairwise_record_required_fields_present() -> None:
    rows, features = make_deterministic_signal_fixture()
    artifacts = build_signal_orthogonality_scope_artifacts_v0(
        rows, features, fixture_truth_pack_used=True
    )
    record = artifacts["pairwise_correlations"][0]
    for key in (
        "signal_a",
        "signal_b",
        "sample_count",
        "overlap_count",
        "pearson_correlation",
        "absolute_pearson_correlation",
        "status",
        "reason_codes",
    ):
        assert key in record
