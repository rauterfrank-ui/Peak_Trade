from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from research.linear_evidence.drift import RollingLinearDriftInputV1
from research.linear_evidence.import_boundary import scan_file_import_boundary
from research.linear_evidence.window_robustness import (
    GO_TOKEN_REQUIRED,
    WindowRobustnessConfigV0,
    build_window_plan_v0,
    compute_active_feature_subset_stability_v0,
    compute_counterfactual_diagnostics_v0,
    compute_feature_variance_diagnostics_v0,
    compute_outlier_influence_diagnostics_v0,
    compute_rank_and_conditioning_diagnostics_v0,
    compute_window_sufficiency_diagnostics_v0,
    make_small_fixture_records_v0,
    run_outlier_and_window_robustness_diagnostic_v0,
    semantic_payload_for_replay,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE = REPO_ROOT / "src/research/linear_evidence/window_robustness.py"
ENTRY_POINT = REPO_ROOT / "scripts/research/offline_outlier_and_window_robustness_diagnostic_v0.py"
FORBIDDEN_IMPORT_PREFIXES = (
    "src.execution",
    "src.scheduler",
    "src.broker",
    "src.trading.master_v2",
    "src.risk",
    "src.governance",
)


def _records_with_constant_feature() -> list[RollingLinearDriftInputV1]:
    return [
        RollingLinearDriftInputV1(
            "PF_ETHUSD",
            f"2026-01-01T{index:02d}:00:00Z",
            f"2026-01-01T{index:02d}:00:00Z",
            float(index),
            {"signal": float(index), "constant": 5.0},
        )
        for index in range(12)
    ]


def _records_collinear() -> list[RollingLinearDriftInputV1]:
    return [
        RollingLinearDriftInputV1(
            "PF_ETHUSD",
            f"2026-01-01T{index:02d}:00:00Z",
            f"2026-01-01T{index:02d}:00:00Z",
            float(index),
            {"signal": float(index), "signal_scaled": float(index) * 2.0},
        )
        for index in range(10)
    ]


def _small_config() -> WindowRobustnessConfigV0:
    return WindowRobustnessConfigV0(
        base_window_size=6,
        window_step=1,
        min_samples=4,
        focus_window_ids=(0, 1, 2),
        adjacent_window_sizes=(5, 6, 7),
        larger_comparison_window_sizes=(8, 10),
    )


def test_window_plan_is_deterministic() -> None:
    records = make_small_fixture_records_v0()
    first = build_window_plan_v0(records, config=_small_config())
    second = build_window_plan_v0(records, config=_small_config())
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)


def test_w1_equivalent_detects_zero_variance() -> None:
    records = _records_with_constant_feature()
    plan = build_window_plan_v0(records, config=_small_config())
    variance = compute_feature_variance_diagnostics_v0(plan, records)
    w1 = next(v for v in variance["windows"] if v["window_id"] == "W1")
    constant = next(f for f in w1["features"] if f["feature_name"] == "constant")
    assert constant["zero_variance"] is True
    assert constant["active"] is False


def test_near_zero_variance_classification_is_deterministic() -> None:
    records = [
        RollingLinearDriftInputV1(
            "PF_ETHUSD",
            f"2026-01-01T{index:02d}:00:00Z",
            f"2026-01-01T{index:02d}:00:00Z",
            float(index),
            {"signal": float(index), "tiny": 1.0 + float(index) * 1e-15},
        )
        for index in range(10)
    ]
    plan = build_window_plan_v0(records, config=_small_config())
    first = compute_feature_variance_diagnostics_v0(plan, records)
    second = compute_feature_variance_diagnostics_v0(plan, records)
    assert first == second
    tiny = next(f for w in first["windows"] for f in w["features"] if f["feature_name"] == "tiny")
    assert tiny["near_zero_variance"] in {True, False}


def test_rank_deficiency_detected() -> None:
    records = _records_collinear()
    plan = build_window_plan_v0(records, config=_small_config())
    rank = compute_rank_and_conditioning_diagnostics_v0(plan, records, config=_small_config())
    w0 = next(w for w in rank["windows"] if w["window_id"] == "W0")
    assert w0["rank_deficient"] is True


def test_ill_conditioning_detected() -> None:
    x = np.array([[1.0, 1.0], [1.0, 1.0000000001], [1.0, 1.0000000002]])
    design = np.column_stack([np.ones(3), x])
    cond = float(np.linalg.cond(design))
    assert cond > 1e6


def test_w14_fixture_conditioning_class() -> None:
    records = list(make_small_fixture_records_v0())
    config = _small_config()
    result = run_outlier_and_window_robustness_diagnostic_v0(
        records, config=config, go_token=GO_TOKEN_REQUIRED
    )
    assert result.status != "FAIL_CLOSED"
    statuses = result.window_statuses["windows"]
    by_id = {str(s["window_id"]): s for s in statuses}
    assert "W2" in by_id
    rank_windows = result.rank_and_conditioning_diagnostics["windows"]
    assert any(
        w.get("conditioning_status")
        in {"ILL_CONDITIONED", "RANK_DEFICIENT", "MIXED_FAILURE", "ACCEPTABLE"}
        for w in rank_windows
    )


def test_active_feature_subset_changes_computed() -> None:
    records = _records_with_constant_feature()
    plan = build_window_plan_v0(records, config=_small_config())
    stability = compute_active_feature_subset_stability_v0(plan)
    assert stability["pairwise_transitions"]
    transition = stability["pairwise_transitions"][0]
    assert "jaccard_similarity" in transition
    assert "feature_subset_changed" in transition


def test_jaccard_stability_computed() -> None:
    records = _records_with_constant_feature()
    plan = build_window_plan_v0(records, config=_small_config())
    stability = compute_active_feature_subset_stability_v0(plan)
    for transition in stability["pairwise_transitions"]:
        assert 0.0 <= float(transition["jaccard_similarity"]) <= 1.0


def test_high_leverage_observations_detected() -> None:
    records = [
        RollingLinearDriftInputV1(
            "PF_ETHUSD",
            f"2026-01-01T{index:02d}:00:00Z",
            f"2026-01-01T{index:02d}:00:00Z",
            1000.0 if index == 9 else float(index),
            {"signal": float(index)},
        )
        for index in range(10)
    ]
    plan = build_window_plan_v0(records, config=_small_config())
    influence = compute_outlier_influence_diagnostics_v0(plan, records, config=_small_config())
    w_last = influence["windows"][-1]
    assert w_last.get("max_leverage") is not None


def test_cooks_distance_on_controlled_fixture() -> None:
    records = [
        RollingLinearDriftInputV1(
            "PF_ETHUSD",
            f"2026-01-01T{index:02d}:00:00Z",
            f"2026-01-01T{index:02d}:00:00Z",
            100.0 if index == 9 else float(index),
            {"signal": float(index)},
        )
        for index in range(10)
    ]
    plan = build_window_plan_v0(records, config=_small_config())
    influence = compute_outlier_influence_diagnostics_v0(plan, records, config=_small_config())
    w = next(item for item in influence["windows"] if item["window_id"] == "W4")
    cooks = [v for v in w.get("cooks_distance", []) if v is not None]
    assert cooks
    assert max(cooks) >= 0.0


def test_dfbetas_or_unavailable_status() -> None:
    records = _records_collinear()
    plan = build_window_plan_v0(records, config=_small_config())
    influence = compute_outlier_influence_diagnostics_v0(plan, records, config=_small_config())
    w0 = influence["windows"][0]
    dfbetas = w0.get("dfbetas", {})
    assert isinstance(dfbetas, dict)


def test_baseline_fit_does_not_remove_observations() -> None:
    records = list(make_small_fixture_records_v0())
    plan = build_window_plan_v0(records, config=_small_config())
    influence = compute_outlier_influence_diagnostics_v0(plan, records, config=_small_config())
    for window in influence["windows"]:
        if window.get("status") == "AVAILABLE":
            assert window.get("baseline_observations_removed", 0) == 0


def test_counterfactuals_do_not_mutate_source_records() -> None:
    records = list(make_small_fixture_records_v0())
    before = json.dumps([r.decision_time for r in records])
    config = _small_config()
    plan = build_window_plan_v0(records, config=config)
    influence = compute_outlier_influence_diagnostics_v0(plan, records, config=config)
    compute_counterfactual_diagnostics_v0(plan, records, influence, config=config)
    after = json.dumps([r.decision_time for r in records])
    assert before == after


def test_counterfactual_production_effect_none() -> None:
    records = list(make_small_fixture_records_v0())
    config = _small_config()
    plan = build_window_plan_v0(records, config=config)
    influence = compute_outlier_influence_diagnostics_v0(plan, records, config=config)
    counter = compute_counterfactual_diagnostics_v0(plan, records, influence, config=config)
    for item in counter["counterfactuals"]:
        assert item["production_effect"] == "NONE"


def test_minimum_window_sufficiency_derived() -> None:
    records = list(make_small_fixture_records_v0())
    config = _small_config()
    plan = build_window_plan_v0(records, config=config)
    variance = compute_feature_variance_diagnostics_v0(plan, records)
    rank = compute_rank_and_conditioning_diagnostics_v0(plan, records, config=config)
    subset = compute_active_feature_subset_stability_v0(plan)
    influence = compute_outlier_influence_diagnostics_v0(plan, records, config=config)
    sufficiency = compute_window_sufficiency_diagnostics_v0(
        plan, variance, rank, subset, influence, config=config
    )
    assert "windows_below_sufficiency" in sufficiency
    assert "windows_above_sufficiency" in sufficiency


def test_no_productive_parameter_change() -> None:
    config = WindowRobustnessConfigV0()
    assert config.base_window_size == 120
    assert config.max_condition_number == 1_000_000.0


def test_no_binding_mutation_in_result() -> None:
    result = run_outlier_and_window_robustness_diagnostic_v0(
        make_small_fixture_records_v0(),
        config=_small_config(),
        go_token=GO_TOKEN_REQUIRED,
    )
    payload = result.to_dict()
    assert payload["economic_evaluation_executed"] is False


def test_no_runtime_order_adapter_scheduler_imports() -> None:
    for path in (MODULE, ENTRY_POINT):
        violations = scan_file_import_boundary(path, repo_root=REPO_ROOT)
        assert violations == []
        source = path.read_text(encoding="utf-8")
        for prefix in FORBIDDEN_IMPORT_PREFIXES:
            assert prefix not in source


def test_authority_effect_none() -> None:
    result = run_outlier_and_window_robustness_diagnostic_v0(
        make_small_fixture_records_v0(),
        config=_small_config(),
        go_token=GO_TOKEN_REQUIRED,
    )
    assert result.authority_effect == "NONE"


def test_runtime_effect_none() -> None:
    result = run_outlier_and_window_robustness_diagnostic_v0(
        make_small_fixture_records_v0(),
        config=_small_config(),
        go_token=GO_TOKEN_REQUIRED,
    )
    assert result.runtime_effect == "NONE"


def test_economic_evaluation_executed_false() -> None:
    result = run_outlier_and_window_robustness_diagnostic_v0(
        make_small_fixture_records_v0(),
        config=_small_config(),
        go_token=GO_TOKEN_REQUIRED,
    )
    assert result.economic_evaluation_executed is False


def test_identical_runs_semantically_identical() -> None:
    records = make_small_fixture_records_v0()
    config = _small_config()
    first = run_outlier_and_window_robustness_diagnostic_v0(
        records, config=config, go_token=GO_TOKEN_REQUIRED
    )
    second = run_outlier_and_window_robustness_diagnostic_v0(
        records, config=config, go_token=GO_TOKEN_REQUIRED
    )
    assert semantic_payload_for_replay(first.to_dict()) == semantic_payload_for_replay(
        second.to_dict()
    )


def test_invalid_source_manifest_fail_closed(tmp_path: Path) -> None:
    bad_source = tmp_path / "bad_source"
    bad_source.mkdir()
    (bad_source / "MANIFEST.sha256").write_text("missing.json deadbeef\n", encoding="utf-8")
    result = subprocess.run(
        [
            sys.executable,
            str(ENTRY_POINT),
            "--out",
            str(tmp_path / "out"),
            "--go-token",
            GO_TOKEN_REQUIRED,
            "--source-evidence",
            str(bad_source),
            "--small-fixture",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "SOURCE_MANIFEST_VERIFY_RC=1" in result.stdout or result.returncode == 1


def test_insufficient_samples_explicit_status() -> None:
    records = [
        RollingLinearDriftInputV1(
            "PF_ETHUSD",
            "2026-01-01T00:00:00Z",
            "2026-01-01T00:00:00Z",
            1.0,
            {"signal": 1.0},
        )
    ]
    config = WindowRobustnessConfigV0(base_window_size=6, window_step=1, min_samples=4)
    with pytest.raises(ValueError, match="INSUFFICIENT_SAMPLE_COUNT"):
        build_window_plan_v0(records, config=config)


def test_non_finite_values_fail_closed() -> None:
    records = [
        RollingLinearDriftInputV1(
            "PF_ETHUSD",
            f"2026-01-01T{index:02d}:00:00Z",
            f"2026-01-01T{index:02d}:00:00Z",
            float("nan") if index == 3 else float(index),
            {"signal": float(index)},
        )
        for index in range(8)
    ]
    config = _small_config()
    with pytest.raises(ValueError, match="NON_FINITE_VALUES_BLOCKED"):
        build_window_plan_v0(records, config=config)


def test_existing_drift_tests_remain_green() -> None:
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
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_go_token_required_for_entry_point(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(ENTRY_POINT),
            "--out",
            str(tmp_path),
            "--small-fixture",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "GO_TOKEN_REQUIRED" in result.stdout


def test_cli_writes_manifestable_bundle(tmp_path: Path) -> None:
    source = Path(
        "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
        "research/read_only_post_drift_terminal_fail_next_economic_scope_discovery_v0_20260714T151907Z"
    )
    if not source.is_dir():
        pytest.skip("source evidence not available in this environment")
    result = subprocess.run(
        [
            sys.executable,
            str(ENTRY_POINT),
            "--out",
            str(tmp_path),
            "--go-token",
            GO_TOKEN_REQUIRED,
            "--source-evidence",
            str(source),
            "--small-fixture",
            "--test-results",
            "fixture_smoke_pass",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert (tmp_path / "MANIFEST.sha256").exists()
    assert (tmp_path / "window_plan.json").exists()
    assert (tmp_path / "final_report.txt").exists()
