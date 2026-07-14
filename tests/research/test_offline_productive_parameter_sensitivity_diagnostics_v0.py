from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from research.linear_evidence.import_boundary import scan_file_import_boundary
from research.linear_evidence.parameter_sensitivity_productive_contract_v0 import (
    AUTHORITY_EFFECT,
    validate_parameter_variation_allowed_v0,
)
from research.linear_evidence.sensitivity import (
    ParameterGridSpecV1,
    ParameterSensitivityInputV1,
    fit_parameter_sensitivity_surface,
)
from research.linear_evidence.offline_productive_parameter_sensitivity_diagnostics_v0 import (
    DIAGNOSTICS_SCOPE_VERSION,
    ProductiveParameterSensitivityReason,
    ProductiveParameterSensitivityStatus,
    build_authority_boundary_v0,
    build_parameter_sensitivity_interpretation_v0,
    build_productive_parameter_sensitivity_diagnostics_artifacts_v0,
    classify_parameter_sensitivity_surface_v0,
    fit_productive_parameter_sensitivity_v0,
)
from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256
from src.research.offline_parameter_sensitivity_productive_input_join_materializer_v0 import (
    MaterializationStatus,
    load_signal_matrix_rows,
    materialize_from_manifest_paths_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
OWNER = (
    REPO_ROOT
    / "src/research/linear_evidence/offline_productive_parameter_sensitivity_diagnostics_v0.py"
)
SENSITIVITY_OWNER = REPO_ROOT / "src/research/linear_evidence/sensitivity.py"
MATERIALIZER = (
    REPO_ROOT / "scripts/ops/materialize_offline_productive_parameter_sensitivity_diagnostics_v0.py"
)
ARCHIVE_ROOT = Path("/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z")
SIGNAL_MATRIX = (
    ARCHIVE_ROOT
    / "research/offline_final_research_fleet_signal_matrix_productive_input_join_materialization_v0_20260714T131741Z"
    / "signal_matrix.jsonl"
)
SEMANTIC_ARTIFACTS = (
    "parameter_sensitivity_results.json",
    "parameter_sensitivity_interpretation.json",
    "parameter_surface_binding.json",
    "deterministic_materialization.txt",
)


def _record(
    index: int,
    *,
    target: float,
    signal: float,
    aux: float,
    fee_bps: float = 10.0,
    slippage_bps: float = 5.0,
) -> ParameterSensitivityInputV1:
    decision_time = f"2026-01-01T{index:02d}:00:00Z"
    return ParameterSensitivityInputV1(
        instrument_id="PF_ETHUSD",
        decision_time=decision_time,
        feature_availability_time=decision_time,
        target=target,
        features={
            "signal": signal,
            "aux": aux,
            "fee_bps": fee_bps,
            "slippage_bps": slippage_bps,
        },
    )


def _robust_records(count: int = 16) -> list[ParameterSensitivityInputV1]:
    return [
        _record(
            index,
            target=float(index + 1) + 0.05 * float(index % 4),
            signal=float(index + 1),
            aux=0.05 * float(index % 4),
        )
        for index in range(count)
    ]


def _fragile_records() -> list[ParameterSensitivityInputV1]:
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


def _default_grid() -> ParameterGridSpecV1:
    return ParameterGridSpecV1(
        parameter_name="signal_scale",
        scaled_feature_name="signal",
        parameter_values=(0.85, 0.95, 1.0, 1.05, 1.15),
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
            "--signal-matrix",
            str(SIGNAL_MATRIX),
            "--skip-focused-tests",
        ],
        cwd=str(REPO_ROOT),
        check=False,
        text=True,
        capture_output=True,
        env={"PYTHONPATH": f"{REPO_ROOT / 'src'}:{REPO_ROOT}"},
    )


@pytest.fixture(scope="module")
def productive_materialization():
    if not SIGNAL_MATRIX.is_file():
        pytest.skip("archive signal matrix unavailable")
    return materialize_from_manifest_paths_v0(
        repo_root=REPO_ROOT,
        signal_matrix_path=SIGNAL_MATRIX,
    )


def test_fixture_robust_region_classification() -> None:
    grid = _default_grid()
    evidence = fit_parameter_sensitivity_surface(_robust_records(), grid=grid)
    status, reason_codes, fragility = classify_parameter_sensitivity_surface_v0(
        evidence=evidence,
        parameter_name=grid.parameter_name,
    )
    assert (
        status
        == ProductiveParameterSensitivityStatus.INSUFFICIENT_ADMISSIBLE_PARAMETER_SURFACE.value
    )
    assert ProductiveParameterSensitivityReason.PARAMETER_CLASS_NOT_ADMISSIBLE.value in reason_codes
    assert evidence.plateau_detected is True
    assert ProductiveParameterSensitivityReason.ROBUST_PLATEAU_DETECTED.value not in reason_codes


def test_fixture_fragile_response_classification() -> None:
    grid = ParameterGridSpecV1(
        parameter_name="signal_scale",
        scaled_feature_name="signal",
        parameter_values=(0.25, 0.5, 0.75, 1.0, 1.25),
    )
    evidence = fit_parameter_sensitivity_surface(_fragile_records(), grid=grid)
    status, reason_codes, _ = classify_parameter_sensitivity_surface_v0(
        evidence=evidence,
        parameter_name=grid.parameter_name,
    )
    assert (
        status
        == ProductiveParameterSensitivityStatus.INSUFFICIENT_ADMISSIBLE_PARAMETER_SURFACE.value
    )
    assert evidence.fragile_spike_detected is True


def test_insufficient_data_fail_closed() -> None:
    grid = _default_grid()
    evidence = fit_parameter_sensitivity_surface(_robust_records(count=3), grid=grid)
    status, reason_codes, _ = classify_parameter_sensitivity_surface_v0(
        evidence=evidence,
        parameter_name=grid.parameter_name,
    )
    assert (
        status
        == ProductiveParameterSensitivityStatus.INSUFFICIENT_ADMISSIBLE_PARAMETER_SURFACE.value
    )
    assert evidence.status == "INSUFFICIENT_DATA"


def test_non_admissible_parameter_blocked() -> None:
    assert validate_parameter_variation_allowed_v0("adx_period") is not None
    assert validate_parameter_variation_allowed_v0("signal_scale") is not None


def test_no_best_point_selection_in_surface_or_result(productive_materialization) -> None:
    if productive_materialization.status != MaterializationStatus.PASS:
        pytest.skip("productive materialization unavailable")
    spec = productive_materialization.join_result.grid_specs[0]
    binding = productive_materialization.join_result.binding
    result = fit_productive_parameter_sensitivity_v0(
        records=productive_materialization.records,
        grid_spec=spec,
        baseline_fee_bps=binding.baseline_fee_bps,
        baseline_slippage_bps=binding.baseline_slippage_bps,
    )
    payload = result.to_dict()
    assert "best_parameter_value" not in payload
    assert "best_parameter_point" not in payload
    assert (
        ProductiveParameterSensitivityReason.BEST_SINGLE_POINT_NOT_EVIDENCE.value
        in result.reason_codes
    )


def test_productive_robust_region_observed(productive_materialization) -> None:
    if productive_materialization.status != MaterializationStatus.PASS:
        pytest.skip("productive materialization unavailable")
    spec = productive_materialization.join_result.grid_specs[0]
    binding = productive_materialization.join_result.binding
    result = fit_productive_parameter_sensitivity_v0(
        records=productive_materialization.records,
        grid_spec=spec,
        baseline_fee_bps=binding.baseline_fee_bps,
        baseline_slippage_bps=binding.baseline_slippage_bps,
    )
    assert result.status == ProductiveParameterSensitivityStatus.ROBUST_REGION_OBSERVED.value
    assert ProductiveParameterSensitivityReason.ROBUST_PLATEAU_DETECTED.value in result.reason_codes


def test_deterministic_output(productive_materialization) -> None:
    first = build_productive_parameter_sensitivity_diagnostics_artifacts_v0(
        materialization=productive_materialization,
        source_evidence_refs=["fixture_ref"],
    )
    second = build_productive_parameter_sensitivity_diagnostics_artifacts_v0(
        materialization=productive_materialization,
        source_evidence_refs=["fixture_ref"],
    )
    assert first["output_digest"] == second["output_digest"]


def test_stable_parameter_and_point_ordering(productive_materialization) -> None:
    artifacts = build_productive_parameter_sensitivity_diagnostics_artifacts_v0(
        materialization=productive_materialization,
        source_evidence_refs=["fixture_ref"],
    )
    result_names = list(artifacts["parameter_sensitivity_results"].keys())
    assert result_names == sorted(result_names)
    for payload in artifacts["parameter_sensitivity_results"].values():
        values = payload["parameter_values"]
        assert values == sorted(values)


def test_baseline_binding_present(productive_materialization) -> None:
    artifacts = build_productive_parameter_sensitivity_diagnostics_artifacts_v0(
        materialization=productive_materialization,
        source_evidence_refs=["fixture_ref"],
    )
    binding = artifacts["parameter_surface_binding"]
    assert binding["baseline_fee_bps"] == pytest.approx(10.0)
    assert binding["baseline_slippage_bps"] == pytest.approx(5.0)
    for name in ("fee_bps", "slippage_bps"):
        assert name in artifacts["parameter_sensitivity_results"]


def test_authority_and_runtime_effects_none() -> None:
    boundary = build_authority_boundary_v0()
    assert boundary["authority_effect"] == AUTHORITY_EFFECT
    assert boundary["runtime_effect"] == "NONE"
    assert boundary["parameter_default_changed"] is False
    assert boundary["parameter_optimization_executed"] is False
    assert boundary["best_point_selected"] is False


def test_interpretation_is_diagnostic_only(productive_materialization) -> None:
    artifacts = build_productive_parameter_sensitivity_diagnostics_artifacts_v0(
        materialization=productive_materialization,
        source_evidence_refs=["fixture_ref"],
    )
    interpretation = artifacts["parameter_sensitivity_interpretation"]
    assert interpretation["recommendation_policy"] == "DIAGNOSTIC_ONLY_NO_PARAMETER_CHANGE"
    assert interpretation["authority_effect"] == "NONE"
    assert interpretation["runtime_effect"] == "NONE"


def test_non_comparable_binding_fail_closed() -> None:
    materialization = materialize_from_manifest_paths_v0(
        repo_root=REPO_ROOT,
        signal_matrix_path=SIGNAL_MATRIX,
    )
    if materialization.status != MaterializationStatus.PASS:
        pytest.skip("productive materialization unavailable")
    empty = type(materialization)(
        status=MaterializationStatus.TARGET_BINDING_MISSING,
        records=(),
        join_result=materialization.join_result,
        provenance=materialization.provenance,
        materialization_digest=materialization.materialization_digest,
        output_digest=materialization.output_digest,
        productive_input_digest=materialization.productive_input_digest,
        grid_digest=materialization.grid_digest,
        source_binding_digest=materialization.source_binding_digest,
        source_signal_matrix_digest=materialization.source_signal_matrix_digest,
    )
    artifacts = build_productive_parameter_sensitivity_diagnostics_artifacts_v0(
        materialization=empty,
        source_evidence_refs=["fixture_ref"],
    )
    assert (
        artifacts["aggregate_status"]
        == ProductiveParameterSensitivityStatus.NON_COMPARABLE_BINDINGS.value
    )
    interpretation = build_parameter_sensitivity_interpretation_v0(
        results={},
        materialization=empty,
    )
    assert interpretation["results_comparable"] is False


def test_import_boundary_owner_and_materializer() -> None:
    assert scan_file_import_boundary(OWNER, repo_root=REPO_ROOT) == []
    assert scan_file_import_boundary(MATERIALIZER, repo_root=REPO_ROOT) == []


def test_materializer_roundtrip(tmp_path: Path) -> None:
    if not SIGNAL_MATRIX.is_file():
        pytest.skip("archive signal matrix unavailable")

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


def test_productive_owner_scope_version(productive_materialization) -> None:
    artifacts = build_productive_parameter_sensitivity_diagnostics_artifacts_v0(
        materialization=productive_materialization,
        source_evidence_refs=["fixture_ref"],
    )
    assert artifacts["diagnostics_scope_version"] == DIAGNOSTICS_SCOPE_VERSION
    assert artifacts["authority_boundary"]["economic_evaluation_executed"] is False
