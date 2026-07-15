"""Contract tests for Bouchaud OHLCV proxy v1 offline productive linear diagnostics economic evidence consumer binding v0."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

from research.linear_evidence.import_boundary import scan_file_import_boundary
from research.linear_evidence.offline_productive_linear_diagnostics_economic_evidence_consumer_binding_v0 import (
    AUTHORITY_EFFECT,
    CONSUMER_BINDING_OWNER,
    EconomicEvidenceAdmissibility,
    LinearDiagnosticsConsumerBindingError,
    bind_linear_diagnostics_economic_evidence_consumer_v0,
)
from research.linear_evidence.offline_productive_linear_diagnostics_support_bundle_v0 import (
    DIAGNOSTIC_CLASS_ORDER,
    SupportAggregateStatus,
)
from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256
from src.research.bouchaud_microstructure_ohlcv_proxy_v1_offline_productive_linear_diagnostics_execution_and_support_evidence_v0 import (
    CANONICAL_FEATURE_DIGEST,
)
from src.governance.economic_diagnostic_optimization_boundary_v0 import build_boundary_report

REPO_ROOT = Path(__file__).resolve().parents[2]
MATERIALIZER = REPO_ROOT / (
    "scripts/ops/"
    "materialize_bouchaud_microstructure_ohlcv_proxy_v1_offline_productive_linear_diagnostics_"
    "economic_evidence_consumer_binding_v0.py"
)
PR5191_IMPLEMENTATION_DIR = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/research/"
    "bouchaud_microstructure_ohlcv_proxy_v1_offline_productive_linear_diagnostics_"
    "execution_and_support_evidence_v0_20260715T004424Z"
)
PR5191_CLOSEOUT_DIR = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/research/"
    "pr5191_merge_closeout_bouchaud_microstructure_ohlcv_proxy_v1_offline_productive_linear_"
    "diagnostics_execution_and_support_evidence_v0_20260715T005450Z"
)
PRODUCTIVE_SUPPORT_BUNDLE_ARTIFACT = "productive_support_bundle.json"

FORBIDDEN_RUNTIME_IMPORT_PREFIXES = (
    "src.execution",
    "src.scheduler",
    "src.broker",
    "src.orders",
)


def _load_materializer_module():
    spec = importlib.util.spec_from_file_location("bouchaud_consumer_materializer", MATERIALIZER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["bouchaud_consumer_materializer"] = module
    spec.loader.exec_module(module)
    return module


def _archive_available() -> bool:
    return (
        PR5191_IMPLEMENTATION_DIR.is_dir()
        and (PR5191_IMPLEMENTATION_DIR / PRODUCTIVE_SUPPORT_BUNDLE_ARTIFACT).is_file()
        and PR5191_CLOSEOUT_DIR.is_dir()
    )


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
def materializer_module():
    return _load_materializer_module()


@pytest.fixture(scope="module")
def consumer_binding(materializer_module):
    if not _archive_available():
        pytest.skip("PR5191 archive evidence unavailable")
    ok, _ = verify_manifest_sha256(PR5191_IMPLEMENTATION_DIR)
    assert ok
    _, binding = materializer_module.bind_bouchaud_linear_diagnostics_economic_evidence_consumer_v0(
        pr5191_implementation_dir=PR5191_IMPLEMENTATION_DIR,
        expected_feature_digest=CANONICAL_FEATURE_DIGEST,
        verify_fn=verify_manifest_sha256,
    )
    return binding


@pytest.fixture(scope="module")
def referenced_support_bundle(materializer_module):
    if not _archive_available():
        pytest.skip("PR5191 archive evidence unavailable")
    return materializer_module.load_referenced_productive_support_bundle_v0(
        PR5191_IMPLEMENTATION_DIR
    )


def test_all_five_manifest_verified_references_accepted(consumer_binding) -> None:
    assert consumer_binding.linear_diagnostics_referenced is True
    assert consumer_binding.linear_diagnostic_class_count == 5
    assert consumer_binding.owner == CONSUMER_BINDING_OWNER
    assert consumer_binding.cost_model_calibration_ref
    assert consumer_binding.signal_orthogonality_ref
    assert consumer_binding.factor_exposure_ref
    assert consumer_binding.parameter_sensitivity_ref
    assert consumer_binding.rolling_linear_drift_ref


def test_all_five_diagnostic_classes_consumed(referenced_support_bundle, consumer_binding) -> None:
    for diagnostic_class in DIAGNOSTIC_CLASS_ORDER:
        ref_field = {
            "cost_diagnostics": consumer_binding.cost_model_calibration_ref,
            "signal_orthogonality": consumer_binding.signal_orthogonality_ref,
            "factor_exposure": consumer_binding.factor_exposure_ref,
            "parameter_sensitivity": consumer_binding.parameter_sensitivity_ref,
            "rolling_linear_drift": consumer_binding.rolling_linear_drift_ref,
        }[diagnostic_class]
        assert ref_field == referenced_support_bundle[f"{diagnostic_class}_ref"]


def test_aggregate_status_blocked_support_evidence(consumer_binding) -> None:
    assert consumer_binding.aggregate_status == SupportAggregateStatus.BLOCK_SUPPORT_EVIDENCE.value
    assert (
        consumer_binding.economic_evidence_admissibility
        == EconomicEvidenceAdmissibility.BLOCKED_SOURCE_DIAGNOSTICS_PRESENT.value
    )


def test_missing_reference_blocked(referenced_support_bundle) -> None:
    broken = dict(referenced_support_bundle)
    broken["cost_diagnostics_ref"] = ""
    with pytest.raises(LinearDiagnosticsConsumerBindingError, match="MISSING_DIAGNOSTIC_REF"):
        bind_linear_diagnostics_economic_evidence_consumer_v0(
            support_bundle=broken,
            verify_fn=verify_manifest_sha256,
        )


def test_source_manifest_rc_not_zero_blocked(referenced_support_bundle) -> None:
    def _fail_verify(_: Path) -> tuple[bool, str]:
        return False, "MANIFEST_MISMATCH"

    with pytest.raises(
        LinearDiagnosticsConsumerBindingError, match="SOURCE_MANIFEST_VERIFY_FAILED"
    ):
        bind_linear_diagnostics_economic_evidence_consumer_v0(
            support_bundle=referenced_support_bundle,
            verify_fn=_fail_verify,
        )


def test_stale_feature_digest_rejected(materializer_module) -> None:
    if not _archive_available():
        pytest.skip("PR5191 archive evidence unavailable")
    with pytest.raises(
        materializer_module.BouchaudConsumerBindingValidationError,
        match="FEATURE_DIGEST_MISMATCH",
    ):
        materializer_module.bind_bouchaud_linear_diagnostics_economic_evidence_consumer_v0(
            pr5191_implementation_dir=PR5191_IMPLEMENTATION_DIR,
            expected_feature_digest="0" * 64,
            verify_fn=verify_manifest_sha256,
        )


def test_repeated_materialization_deterministic(consumer_binding, materializer_module) -> None:
    if not _archive_available():
        pytest.skip("PR5191 archive evidence unavailable")
    _, second = materializer_module.bind_bouchaud_linear_diagnostics_economic_evidence_consumer_v0(
        pr5191_implementation_dir=PR5191_IMPLEMENTATION_DIR,
        expected_feature_digest=CANONICAL_FEATURE_DIGEST,
        verify_fn=verify_manifest_sha256,
    )
    assert second.to_dict() == consumer_binding.to_dict()
    assert second.support_bundle_output_digest == consumer_binding.support_bundle_output_digest


def test_second_materialization_no_semantic_diff(consumer_binding, materializer_module) -> None:
    if not _archive_available():
        pytest.skip("PR5191 archive evidence unavailable")
    first_payload = json.dumps(consumer_binding.to_dict(), sort_keys=True, separators=(",", ":"))
    _, second = materializer_module.bind_bouchaud_linear_diagnostics_economic_evidence_consumer_v0(
        pr5191_implementation_dir=PR5191_IMPLEMENTATION_DIR,
        expected_feature_digest=CANONICAL_FEATURE_DIGEST,
        verify_fn=verify_manifest_sha256,
    )
    second_payload = json.dumps(second.to_dict(), sort_keys=True, separators=(",", ":"))
    assert first_payload == second_payload


def test_source_support_bundle_unchanged(materializer_module) -> None:
    if not _archive_available():
        pytest.skip("PR5191 archive evidence unavailable")
    bundle_path = PR5191_IMPLEMENTATION_DIR / PRODUCTIVE_SUPPORT_BUNDLE_ARTIFACT
    digest_before = hashlib.sha256(bundle_path.read_bytes()).hexdigest()
    materializer_module.bind_bouchaud_linear_diagnostics_economic_evidence_consumer_v0(
        pr5191_implementation_dir=PR5191_IMPLEMENTATION_DIR,
        expected_feature_digest=CANONICAL_FEATURE_DIGEST,
        verify_fn=verify_manifest_sha256,
    )
    digest_after = hashlib.sha256(bundle_path.read_bytes()).hexdigest()
    assert digest_before == digest_after


def test_runtime_and_authority_effects_none(consumer_binding) -> None:
    assert consumer_binding.runtime_effect == AUTHORITY_EFFECT == "NONE"
    assert consumer_binding.authority_effect == "NONE"
    assert consumer_binding.economic_pass_authority is False
    assert consumer_binding.promotion_pass_authority is False


def test_no_runtime_import_boundary_violation() -> None:
    assert scan_file_import_boundary(MATERIALIZER, repo_root=REPO_ROOT) == []
    source = MATERIALIZER.read_text(encoding="utf-8")
    for prefix in FORBIDDEN_RUNTIME_IMPORT_PREFIXES:
        assert prefix not in source
    assert "promotion_economic_gate" not in source
    assert "evaluate_promotion_economic_gate" not in source


def test_governance_boundary_admissible() -> None:
    report = build_boundary_report(
        [
            str(MATERIALIZER.relative_to(REPO_ROOT)),
            str(Path(__file__).relative_to(REPO_ROOT)),
            "config/governance/economic_diagnostic_optimization_boundary_canonical_owner_map_v0.json",
        ],
        repo_root=REPO_ROOT,
    )
    assert report.admissible is True
    assert report.impact_unknown is False


def test_pr5191_source_manifest_verified() -> None:
    if not _archive_available():
        pytest.skip("PR5191 archive evidence unavailable")
    ok, _ = verify_manifest_sha256(PR5191_IMPLEMENTATION_DIR)
    assert ok
    ok_closeout, _ = verify_manifest_sha256(PR5191_CLOSEOUT_DIR)
    assert ok_closeout


def test_materializer_roundtrip_manifest_verified(tmp_path: Path) -> None:
    if not _archive_available():
        pytest.skip("PR5191 archive evidence unavailable")
    first_dir = tmp_path / "evidence_a"
    second_dir = tmp_path / "evidence_b"
    first = _run_materializer(first_dir)
    second = _run_materializer(second_dir)
    assert first.returncode == 0, first.stdout + first.stderr
    assert second.returncode == 0, second.stdout + second.stderr

    for bundle in (first_dir, second_dir):
        ok, _ = verify_manifest_sha256(bundle)
        assert ok

    binding_a = json.loads((first_dir / "consumer_contract.json").read_text(encoding="utf-8"))
    binding_b = json.loads((second_dir / "consumer_contract.json").read_text(encoding="utf-8"))
    assert binding_a == binding_b
    assert binding_a["linear_diagnostic_class_count"] == 5
    assert (
        binding_a["linear_diagnostics_status"]
        == SupportAggregateStatus.BLOCK_SUPPORT_EVIDENCE.value
    )
    integrity = json.loads(
        (first_dir / "source_support_bundle_integrity.json").read_text(encoding="utf-8")
    )
    assert integrity["source_support_bundle_unchanged"] is True
    final_report = (first_dir / "final_report.txt").read_text(encoding="utf-8")
    assert "ECONOMIC_EVALUATION_EXECUTED=false" in final_report
    assert "PROMOTION_GATE_INVOKED=false" in final_report
    assert "RUNTIME_EFFECT=NONE" in final_report
