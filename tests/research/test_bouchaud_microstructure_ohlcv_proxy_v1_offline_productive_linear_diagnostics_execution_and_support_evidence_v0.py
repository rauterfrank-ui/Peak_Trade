"""Contract tests for Bouchaud OHLCV proxy v1 offline productive linear diagnostics execution support evidence v0."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

from research.linear_evidence.import_boundary import scan_file_import_boundary
from research.linear_evidence.offline_productive_linear_diagnostics_support_bundle_v0 import (
    DEFAULT_COST_DIAGNOSTICS_BUNDLE,
    DEFAULT_FACTOR_EXPOSURE_BUNDLE,
    DEFAULT_PARAMETER_SENSITIVITY_BUNDLE,
    DEFAULT_ROLLING_LINEAR_DRIFT_BUNDLE,
    DEFAULT_SIGNAL_ORTHOGONALITY_BUNDLE,
    DEFAULT_SOURCE_BUNDLE_SPECS,
    DIAGNOSTIC_CLASS_ORDER,
    validate_support_bundle_artifacts_v0,
)
from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256
from src.research.bouchaud_microstructure_ohlcv_proxy_v1_offline_productive_linear_diagnostics_execution_and_support_evidence_v0 import (
    CANONICAL_FEATURE_DIGEST,
    CANONICAL_OWNER,
    EVIDENCE_TYPE,
    EXECUTION_ID,
    EXECUTION_OWNER,
    ExecutionStatus,
    ExecutionValidationError,
    materialize_bouchaud_linear_diagnostics_execution_and_support_evidence_v0,
)
from src.research.bouchaud_microstructure_ohlcv_proxy_v1_research_generation_preparation_v0 import (
    FEATURE_NAMES,
    TARGET_NAME,
    build_target_binding,
    load_fixture_bars_v0,
    materialize_and_validate_feature_matrix_v0,
)
from src.governance.economic_diagnostic_optimization_boundary_v0 import build_boundary_report

REPO_ROOT = Path(__file__).resolve().parents[2]
OWNER = REPO_ROOT / (
    "src/research/"
    "bouchaud_microstructure_ohlcv_proxy_v1_offline_productive_linear_diagnostics_"
    "execution_and_support_evidence_v0.py"
)
MATERIALIZER = REPO_ROOT / (
    "scripts/ops/"
    "materialize_bouchaud_microstructure_ohlcv_proxy_v1_offline_productive_linear_diagnostics_"
    "execution_and_support_evidence_v0.py"
)
FIXTURE_PATH = (
    REPO_ROOT
    / "tests/fixtures/bouchaud_microstructure_ohlcv_proxy_v1_research_generation_preparation_v0/"
    "truth_pack_bars.json"
)

PRODUCTIVE_BUNDLES = {
    "cost_diagnostics": DEFAULT_COST_DIAGNOSTICS_BUNDLE,
    "signal_orthogonality": DEFAULT_SIGNAL_ORTHOGONALITY_BUNDLE,
    "factor_exposure": DEFAULT_FACTOR_EXPOSURE_BUNDLE,
    "parameter_sensitivity": DEFAULT_PARAMETER_SENSITIVITY_BUNDLE,
    "rolling_linear_drift": DEFAULT_ROLLING_LINEAR_DRIFT_BUNDLE,
}

FORBIDDEN_RUNTIME_IMPORT_PREFIXES = (
    "src.execution",
    "src.scheduler",
    "src.broker",
    "src.orders",
)


def _archive_available() -> bool:
    return all(path.is_dir() for path in PRODUCTIVE_BUNDLES.values())


def _fixture_rows_and_binding():
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    bars = pd.DataFrame(payload["bars"])
    rows, binding, digest = materialize_and_validate_feature_matrix_v0(bars)
    assert digest == payload["expected_feature_digest"]
    return rows, binding, digest


def _run_materializer(out_dir: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(MATERIALIZER),
            "--out",
            str(out_dir),
            "--skip-focused-tests",
        ],
        cwd=str(REPO_ROOT),
        check=False,
        text=True,
        capture_output=True,
        env={"PYTHONPATH": f"{REPO_ROOT / 'src'}:{REPO_ROOT}"},
    )


@pytest.fixture(scope="module")
def fixture_binding():
    return _fixture_rows_and_binding()


@pytest.fixture(scope="module")
def execution_artifacts(fixture_binding):
    if not _archive_available():
        pytest.skip("productive archive bundles unavailable")
    rows, binding, digest = fixture_binding
    payload, result = materialize_bouchaud_linear_diagnostics_execution_and_support_evidence_v0(
        rows=rows,
        binding=binding,
        feature_digest=digest,
        source_specs=DEFAULT_SOURCE_BUNDLE_SPECS,
        verify_fn=verify_manifest_sha256,
        repo_root=REPO_ROOT,
    )
    return payload, result


def test_feature_matrix_materialized_via_canonical_producer(fixture_binding) -> None:
    _, binding, digest = fixture_binding
    assert binding.feature_names == FEATURE_NAMES
    assert binding.target_name == TARGET_NAME
    assert digest == CANONICAL_FEATURE_DIGEST


def test_feature_digest_matches_canonical(fixture_binding) -> None:
    _, _, digest = fixture_binding
    assert digest == "6a29ebbba64e6f732e4cedd601025c4f4259d0b0c842669ea4c8da3abc0d84b0"


def test_second_materialization_same_digest(fixture_binding) -> None:
    if not _archive_available():
        pytest.skip("productive archive bundles unavailable")
    rows, binding, digest = fixture_binding
    _, binding2, digest2 = materialize_and_validate_feature_matrix_v0(
        pd.DataFrame(json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))["bars"])
    )
    assert binding2.feature_matrix_digest == binding.feature_matrix_digest
    assert digest2 == digest


def test_all_five_diagnostic_classes_present(execution_artifacts) -> None:
    payload, result = execution_artifacts
    assert len(result.diagnostic_class_executions) == 5
    classes = {item.diagnostic_class for item in result.diagnostic_class_executions}
    assert classes == set(DIAGNOSTIC_CLASS_ORDER)
    assert set(payload["diagnostic_payloads"]) == set(DIAGNOSTIC_CLASS_ORDER)


def test_no_sixth_diagnostic_class(execution_artifacts) -> None:
    payload, _ = execution_artifacts
    assert len(payload["diagnostic_payloads"]) == 5
    assert len(payload["diagnostic_class_executions"]) == 5


def test_execution_deterministic(fixture_binding) -> None:
    if not _archive_available():
        pytest.skip("productive archive bundles unavailable")
    rows, binding, digest = fixture_binding
    first, _ = materialize_bouchaud_linear_diagnostics_execution_and_support_evidence_v0(
        rows=rows,
        binding=binding,
        feature_digest=digest,
        source_specs=DEFAULT_SOURCE_BUNDLE_SPECS,
        verify_fn=verify_manifest_sha256,
        repo_root=REPO_ROOT,
    )
    second, _ = materialize_bouchaud_linear_diagnostics_execution_and_support_evidence_v0(
        rows=rows,
        binding=binding,
        feature_digest=digest,
        source_specs=DEFAULT_SOURCE_BUNDLE_SPECS,
        verify_fn=verify_manifest_sha256,
        repo_root=REPO_ROOT,
    )
    assert first["output_digest"] == second["output_digest"]


def test_missing_target_binding_fail_closed(fixture_binding) -> None:
    if not _archive_available():
        pytest.skip("productive archive bundles unavailable")
    rows, binding, digest = fixture_binding
    bad_target = dict(build_target_binding())
    bad_target["target_name"] = "wrong_target"
    with pytest.raises(ExecutionValidationError, match="TARGET_BINDING_MISSING"):
        materialize_bouchaud_linear_diagnostics_execution_and_support_evidence_v0(
            rows=rows,
            binding=binding,
            feature_digest=digest,
            source_specs=DEFAULT_SOURCE_BUNDLE_SPECS,
            verify_fn=verify_manifest_sha256,
            repo_root=REPO_ROOT,
            target_binding=bad_target,
        )


def test_stale_feature_digest_rejected(fixture_binding) -> None:
    if not _archive_available():
        pytest.skip("productive archive bundles unavailable")
    rows, binding, _ = fixture_binding
    with pytest.raises(ExecutionValidationError, match="CANONICAL_FEATURE_DIGEST_MISMATCH"):
        materialize_bouchaud_linear_diagnostics_execution_and_support_evidence_v0(
            rows=rows,
            binding=binding,
            feature_digest="0" * 64,
            source_specs=DEFAULT_SOURCE_BUNDLE_SPECS,
            verify_fn=verify_manifest_sha256,
            repo_root=REPO_ROOT,
        )


def test_authority_and_runtime_effect_none(execution_artifacts) -> None:
    _, result = execution_artifacts
    assert result.runtime_effect == "NONE"
    assert result.authority_effect == "NONE"
    assert result.economic_evaluation_executed is False
    for item in result.diagnostic_class_executions:
        assert item.authority_effect == "NONE"
        assert item.runtime_effect == "NONE"


def test_productive_support_bundle_consumer_accepts(execution_artifacts) -> None:
    payload, result = execution_artifacts
    validate_support_bundle_artifacts_v0(payload["productive_support_bundle"])
    assert result.execution_status == ExecutionStatus.COMPLETE.value


def test_no_runtime_import_boundary_violation() -> None:
    assert scan_file_import_boundary(OWNER, repo_root=REPO_ROOT) == []
    assert scan_file_import_boundary(MATERIALIZER, repo_root=REPO_ROOT) == []
    source = OWNER.read_text(encoding="utf-8")
    for prefix in FORBIDDEN_RUNTIME_IMPORT_PREFIXES:
        assert prefix not in source


def test_governance_boundary_admissible() -> None:
    report = build_boundary_report(
        [
            str(OWNER.relative_to(REPO_ROOT)),
            str(MATERIALIZER.relative_to(REPO_ROOT)),
            str(Path(__file__).relative_to(REPO_ROOT)),
            "config/governance/economic_diagnostic_optimization_boundary_canonical_owner_map_v0.json",
        ],
        repo_root=REPO_ROOT,
    )
    assert report.admissible is True
    assert report.impact_unknown is False


def test_materializer_roundtrip_manifest_verified(tmp_path) -> None:
    if not _archive_available():
        pytest.skip("productive archive bundles unavailable")
    out_dir = tmp_path / "execution_bundle"
    proc = _run_materializer(out_dir)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    ok, _ = verify_manifest_sha256(out_dir)
    assert ok
    support_bundle = json.loads(
        (out_dir / "productive_support_bundle.json").read_text(encoding="utf-8")
    )
    validate_support_bundle_artifacts_v0(support_bundle)
    final_report = (out_dir / "final_report.txt").read_text(encoding="utf-8")
    assert "MANIFEST_VERIFY_RC=0" in final_report
    assert "ALL_GREEN=True" in final_report
    assert "FEATURE_DIGEST_MATCH=True" in final_report


def test_execution_contract_identity(execution_artifacts) -> None:
    payload, result = execution_artifacts
    assert payload["execution_id"] == EXECUTION_ID
    assert payload["evidence_type"] == EVIDENCE_TYPE
    assert payload["owner"] == EXECUTION_OWNER
    assert result.feature_digest == CANONICAL_FEATURE_DIGEST
