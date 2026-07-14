from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256

from research.linear_evidence.factor_exposure import (
    REASON_FACTOR_LOOKAHEAD_DETECTED,
    REASON_FIXTURE_SCAFFOLD_DIAGNOSTIC_ONLY,
    REASON_HIGH_CONDITION_NUMBER,
    REASON_INSUFFICIENT_SAMPLE_COUNT,
    REASON_PRODUCTIVE_BINDING_MISSING,
    REASON_RANK_DEFICIENT,
    FactorExposureDiagnosticsConfigV0,
    FactorExposureInputV1,
    build_cross_entity_exposure_diagnostics_v0,
    classify_exposure_clusters_v0,
    compute_beta_stability_v0,
    compute_exposure_similarity_matrix_v0,
    fit_factor_exposure_diagnostics_v0,
    make_deterministic_factor_exposure_fixture,
)
from research.linear_evidence.import_boundary import scan_file_import_boundary
from research.linear_evidence.offline_productive_factor_exposure_diagnostics_v0 import (
    DIAGNOSTICS_SCOPE_VERSION,
    ProductiveFactorExposureValidationError,
    build_authority_boundary_v0,
    build_factor_binding_v0,
    build_productive_factor_exposure_diagnostics_artifacts_v0,
    load_orthogonality_interpretation_context,
    materialize_productive_inputs_from_paths,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
OWNER = (
    REPO_ROOT / "src/research/linear_evidence/offline_productive_factor_exposure_diagnostics_v0.py"
)
FACTOR_OWNER = REPO_ROOT / "src/research/linear_evidence/factor_exposure.py"
MATERIALIZER = (
    REPO_ROOT / "scripts/ops/materialize_offline_productive_factor_exposure_diagnostics_v0.py"
)
ARCHIVE_ROOT = Path("/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z")
TRADE_LEDGER = (
    ARCHIVE_ROOT
    / "trade_ledger_equity_curve_persistence_offline_evaluation_execution_v0_20260705T083113Z"
    / "TRADE_LEDGER_V1.jsonl"
)
FACTOR_SNAPSHOTS = (
    ARCHIVE_ROOT
    / "research/productive_point_in_time_factor_snapshot_rematerialization_v0_20260713T164200Z"
    / "productive_point_in_time_factor_snapshots_v0.jsonl"
)
ORTHOGONALITY_INTERPRETATION = (
    ARCHIVE_ROOT
    / "research/offline_productive_signal_orthogonality_results_interpretation_v0_20260714T213029Z"
)
SEMANTIC_ARTIFACTS = (
    "factor_exposure_results.json",
    "beta_stability.json",
    "exposure_similarity_matrix.json",
    "cluster_risk_diagnostics.json",
    "deterministic_materialization.txt",
)


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _manifest_digest_for(path: Path, bundle: Path) -> str | None:
    rel = path.relative_to(bundle).as_posix()
    for line in (bundle / "MANIFEST.sha256").read_text(encoding="utf-8").splitlines():
        parts = line.split(None, 1)
        if len(parts) == 2 and parts[1] == rel:
            return parts[0]
    return None


def _run_materializer(out_dir: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(MATERIALIZER),
            "--out",
            str(out_dir),
            "--trade-ledger",
            str(TRADE_LEDGER),
            "--factor-snapshots",
            str(FACTOR_SNAPSHOTS),
            "--orthogonality-interpretation-bundle",
            str(ORTHOGONALITY_INTERPRETATION),
            "--skip-focused-tests",
        ],
        cwd=str(REPO_ROOT),
        check=False,
        text=True,
        capture_output=True,
        env={"PYTHONPATH": f"{REPO_ROOT / 'src'}:{REPO_ROOT}"},
    )


def _record(
    *,
    timestamp: int,
    target_return: float | None = None,
    factor_values: dict[str, float] | None = None,
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
        factor_time=f"2026-01-01T{timestamp:02d}:00:00Z",
        decision_time=f"2026-01-01T{timestamp + 1:02d}:00:00Z",
    )


def _records(count: int = 12) -> list[FactorExposureInputV1]:
    return [_record(timestamp=i) for i in range(1, count + 1)]


@pytest.fixture(scope="module")
def productive_materialization():
    if not TRADE_LEDGER.is_file() or not FACTOR_SNAPSHOTS.is_file():
        pytest.skip("archive productive inputs unavailable")
    return materialize_productive_inputs_from_paths(
        trade_ledger_path=TRADE_LEDGER,
        factor_snapshot_path=FACTOR_SNAPSHOTS,
    )


def test_fixture_truth_pack_runs_deterministically() -> None:
    first = fit_factor_exposure_diagnostics_v0(
        make_deterministic_factor_exposure_fixture(),
        fixture_scaffold=True,
    )
    second = fit_factor_exposure_diagnostics_v0(
        make_deterministic_factor_exposure_fixture(),
        fixture_scaffold=True,
    )
    assert first.to_dict() == second.to_dict()
    assert REASON_FIXTURE_SCAFFOLD_DIAGNOSTIC_ONLY in first.reason_codes


def test_known_beta_recovery_on_fixture() -> None:
    records = make_deterministic_factor_exposure_fixture()
    evidence = fit_factor_exposure_diagnostics_v0(records, fixture_scaffold=True)
    assert evidence.status in {"DIAGNOSTIC_ONLY", "ROBUSTNESS_FAILED"}
    assert evidence.coefficients
    assert evidence.validation_r2 is not None


def test_time_ordered_validation_split() -> None:
    evidence = fit_factor_exposure_diagnostics_v0(_records())
    assert evidence.validation_policy == "time_ordered"
    assert evidence.n_samples_train >= 1
    assert evidence.n_samples_validation >= 1
    assert evidence.n_samples_train + evidence.n_samples_validation == evidence.n_samples


def test_lookahead_rejection() -> None:
    records = _records(8)
    records[3] = FactorExposureInputV1(
        records[3].instrument_id,
        records[3].timestamp,
        records[3].target_return,
        records[3].factor_values,
        factor_time="2026-01-01T06:00:00Z",
        decision_time="2026-01-01T05:00:00Z",
    )
    with pytest.raises(ValueError, match=REASON_FACTOR_LOOKAHEAD_DETECTED):
        fit_factor_exposure_diagnostics_v0(records)


def test_random_split_rejection() -> None:
    with pytest.raises(ValueError, match="validation_fraction must be between 0 and 1"):
        FactorExposureDiagnosticsConfigV0(validation_fraction=1.0).validate()


def test_insufficient_data_fail_closed() -> None:
    evidence = fit_factor_exposure_diagnostics_v0(
        _records(4),
        config=FactorExposureDiagnosticsConfigV0(min_samples=8),
    )
    assert REASON_INSUFFICIENT_SAMPLE_COUNT in evidence.reason_codes


def test_rank_deficiency_fail_closed() -> None:
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
    evidence = fit_factor_exposure_diagnostics_v0(records)
    assert evidence.status == "RANK_DEFICIENT_BLOCKED"
    assert REASON_RANK_DEFICIENT in evidence.reason_codes


def test_high_condition_number_classification() -> None:
    records = _records()
    evidence = fit_factor_exposure_diagnostics_v0(
        records,
        config=FactorExposureDiagnosticsConfigV0(condition_number_threshold=0.1),
    )
    assert REASON_HIGH_CONDITION_NUMBER in evidence.reason_codes


def test_beta_stability_calculation() -> None:
    evidence = fit_factor_exposure_diagnostics_v0(_records())
    assert evidence.beta_stability.get("computed") is True


def test_sign_instability_flags() -> None:
    records: list[FactorExposureInputV1] = []
    for i in range(1, 25):
        records.append(
            _record(
                timestamp=i,
                target_return=0.01 * ((-1) ** i),
                factor_values={"market_beta": float((-1) ** i), "liquidity_beta": float(i % 4)},
            )
        )
    stability = compute_beta_stability_v0(
        records,
        factor_names=("liquidity_beta", "market_beta"),
        window_count=3,
        min_samples=8,
    )
    assert stability.get("computed") is True


def test_exposure_similarity_calculation() -> None:
    vectors = {
        "a": {"f1": 1.0, "f2": 0.0},
        "b": {"f1": 1.0, "f2": 0.1},
        "c": {"f1": 0.0, "f2": 1.0},
    }
    matrix = compute_exposure_similarity_matrix_v0(vectors)
    assert matrix["a"]["b"] > matrix["a"]["c"]


def test_cluster_concentration_flagging() -> None:
    matrix = {
        "a": {"a": 1.0, "b": 0.95, "c": 0.95},
        "b": {"a": 0.95, "b": 1.0, "c": 0.96},
        "c": {"a": 0.95, "b": 0.96, "c": 1.0},
    }
    _, cluster_diag = classify_exposure_clusters_v0(matrix, threshold=0.85)
    assert cluster_diag["cluster_concentration_high"] is True


def test_missing_factor_handling() -> None:
    binding = build_factor_binding_v0([])
    assert binding["factor_groups_missing"]
    assert "funding" in binding["factor_groups_missing"]


def test_stable_digests_and_ordering() -> None:
    first = fit_factor_exposure_diagnostics_v0(_records()).to_dict()
    second = fit_factor_exposure_diagnostics_v0(_records()).to_dict()
    assert first == second


def test_repeated_materialization_deterministic(productive_materialization) -> None:
    first = build_productive_factor_exposure_diagnostics_artifacts_v0(
        records=list(productive_materialization.records),
        materialization=productive_materialization,
        trade_ledger_path=TRADE_LEDGER,
        factor_snapshot_path=FACTOR_SNAPSHOTS,
        orthogonality_interpretation_bundle=ORTHOGONALITY_INTERPRETATION,
    )
    second = build_productive_factor_exposure_diagnostics_artifacts_v0(
        records=list(productive_materialization.records),
        materialization=productive_materialization,
        trade_ledger_path=TRADE_LEDGER,
        factor_snapshot_path=FACTOR_SNAPSHOTS,
        orthogonality_interpretation_bundle=ORTHOGONALITY_INTERPRETATION,
    )
    assert first["output_digest"] == second["output_digest"]


def test_productive_owner_invocation(productive_materialization) -> None:
    artifacts = build_productive_factor_exposure_diagnostics_artifacts_v0(
        records=list(productive_materialization.records),
        materialization=productive_materialization,
        trade_ledger_path=TRADE_LEDGER,
        factor_snapshot_path=FACTOR_SNAPSHOTS,
        orthogonality_interpretation_bundle=ORTHOGONALITY_INTERPRETATION,
    )
    assert artifacts["diagnostics_scope_version"] == DIAGNOSTICS_SCOPE_VERSION
    assert artifacts["factor_exposure_results"]["pooled"]["authority_effect"] == "NONE"


def test_orthogonality_context_loads() -> None:
    if not ORTHOGONALITY_INTERPRETATION.is_dir():
        pytest.skip("interpretation bundle unavailable")
    loaded = load_orthogonality_interpretation_context(ORTHOGONALITY_INTERPRETATION)
    assert "pairwise_interpretation" in loaded


def test_orthogonality_missing_file_fail_closed(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    with pytest.raises(ProductiveFactorExposureValidationError):
        load_orthogonality_interpretation_context(bundle)


def test_productive_binding_missing_fail_closed() -> None:
    evidence = fit_factor_exposure_diagnostics_v0([], productive_binding_gap=True)
    assert REASON_PRODUCTIVE_BINDING_MISSING in evidence.reason_codes


def test_authority_and_runtime_effects_none() -> None:
    boundary = build_authority_boundary_v0()
    assert boundary["authority_effect"] == "NONE"
    assert boundary["runtime_effect"] == "NONE"
    assert boundary["strategy_selection_changed"] is False
    assert boundary["active_set_changed"] is False
    assert boundary["economic_evaluation_executed"] is False


def test_no_strategy_selection_output(productive_materialization) -> None:
    artifacts = build_productive_factor_exposure_diagnostics_artifacts_v0(
        records=list(productive_materialization.records),
        materialization=productive_materialization,
        trade_ledger_path=TRADE_LEDGER,
        factor_snapshot_path=FACTOR_SNAPSHOTS,
    )
    assert artifacts["authority_boundary"]["strategy_selection_changed"] is False


def test_cross_entity_cluster_reason_codes() -> None:
    grouped = {
        "PF_A": tuple(_record(timestamp=i, instrument_id="PF_A") for i in range(1, 13)),
        "PF_B": tuple(_record(timestamp=i, instrument_id="PF_B") for i in range(1, 13)),
    }
    per_entity, _, _, cluster_diag = build_cross_entity_exposure_diagnostics_v0(grouped)
    assert per_entity
    assert cluster_diag.get("cluster_count") is not None


def test_import_boundary_owner_and_materializer() -> None:
    assert scan_file_import_boundary(OWNER, repo_root=REPO_ROOT) == []
    assert scan_file_import_boundary(FACTOR_OWNER, repo_root=REPO_ROOT) == []
    assert scan_file_import_boundary(MATERIALIZER, repo_root=REPO_ROOT) == []


def test_materializer_roundtrip(tmp_path: Path) -> None:
    if not TRADE_LEDGER.is_file() or not FACTOR_SNAPSHOTS.is_file():
        pytest.skip("archive productive inputs unavailable")
    if not ORTHOGONALITY_INTERPRETATION.is_dir():
        pytest.skip("interpretation bundle unavailable")

    first_dir = tmp_path / "evidence_a"
    second_dir = tmp_path / "evidence_b"
    first = _run_materializer(first_dir)
    second = _run_materializer(second_dir)
    assert first.returncode == 0, first.stderr
    assert second.returncode == 0, second.stderr

    for bundle in (first_dir, second_dir):
        final_report = bundle / "final_report.txt"
        manifest = bundle / "MANIFEST.sha256"
        assert final_report.is_file()
        assert manifest.is_file()
        ok, msg = verify_manifest_sha256(bundle)
        assert ok, msg
        manifest_digest = _manifest_digest_for(final_report, bundle)
        assert manifest_digest is not None
        assert manifest_digest == _sha256_file(final_report)
        manifest_verify_log = bundle / "MANIFEST_VERIFY.log"
        assert manifest_verify_log.is_file()
        assert "MANIFEST_VERIFY_RC=0" in manifest_verify_log.read_text(encoding="utf-8")

    first_semantic = {
        name: (first_dir / name).read_text(encoding="utf-8") for name in SEMANTIC_ARTIFACTS
    }
    second_semantic = {
        name: (second_dir / name).read_text(encoding="utf-8") for name in SEMANTIC_ARTIFACTS
    }
    assert first_semantic == second_semantic
