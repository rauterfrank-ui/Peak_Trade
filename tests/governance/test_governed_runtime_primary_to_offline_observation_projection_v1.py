"""Tests for governed runtime primary → offline observation projection v1."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.governance.governed_productive_configuration_apply_authority_v1 import (
    primary_runtime_evidence_implies_apply_authorization_v1,
)
from src.governance.governed_runtime_primary_to_offline_observation_projection_closure_v1 import (
    G2_END_TO_END_STATUS,
    prove_g2_projection_closure_v1,
    run_g2_bounded_end_to_end_with_projection_v1,
    trace_g2_reconstruction_v1,
)
from src.governance.governed_runtime_primary_to_offline_observation_projection_v1 import (
    DECISION_CONFIG,
    FIELD_MAPPING_LEDGER,
    EXTERNAL_EFFECT,
    GovernedRuntimePrimaryProjectionRequestV1,
    PRIMARY_EVIDENCE_IMPLIES_PRODUCTIVE_AUTHORIZATION,
    P5_EVIDENCE_INTAKE_IMPLIES_PRODUCTIVE_AUTHORIZATION,
    P5_EVIDENCE_INTAKE_IMPLIES_RUNTIME_APPLY,
    RUNTIME_APPLY_STARTED,
    RuntimePrimarySourceModeV1,
    load_field_mapping_ledger_v1,
    produce_governed_runtime_primary_projection_artifact_v1,
    run_governed_runtime_primary_to_offline_observation_projection_v1,
    validate_primary_evidence_for_projection_v1,
)
from tests.governance.governed_runtime_primary_to_offline_observation_projection_v1_fixtures import (
    build_mode_bundle,
    cleanup_durable_archive_roots,
    projection_request,
)

pytest_plugins = [
    "tests.governance.governed_runtime_primary_to_offline_observation_projection_v1_fixtures"
]

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(autouse=True)
def _cleanup_archives():
    yield
    cleanup_durable_archive_roots()


@pytest.mark.parametrize(
    "mode",
    [
        RuntimePrimarySourceModeV1.PAPER,
        RuntimePrimarySourceModeV1.SHADOW,
        RuntimePrimarySourceModeV1.TESTNET,
    ],
)
def test_positive_projection_learning_ingress_and_artifact(tmp_path: Path, mode) -> None:
    root = build_mode_bundle(tmp_path, mode)
    result = run_governed_runtime_primary_to_offline_observation_projection_v1(
        projection_request(source_mode=mode, primary_root=root)
    )
    assert result.status == "PROJECTED", result.blocking_reasons
    assert result.provenance is not None
    assert result.provenance.primary_evidence_manifest_digest
    assert result.offline_observations is not None
    assert result.identity_binding_status == "BOUND"
    assert result.runtime_learning_input is not None
    assert result.runtime_learning_input.get("decision_code") == "LEARNING_INPUT_VALID"
    out = tmp_path / "projection_out"
    produce_governed_runtime_primary_projection_artifact_v1(result=result, output_dir=out)
    assert (out / "governed_runtime_primary_offline_observation_projection_v1.json").is_file()
    assert (out / "MANIFEST.sha256").is_file()


@pytest.mark.parametrize(
    "mode",
    [
        RuntimePrimarySourceModeV1.PAPER,
        RuntimePrimarySourceModeV1.SHADOW,
        RuntimePrimarySourceModeV1.TESTNET,
    ],
)
def test_bounded_end_to_end_and_reconstruction(tmp_path: Path, mode) -> None:
    root = build_mode_bundle(tmp_path, mode)
    summary = run_g2_bounded_end_to_end_with_projection_v1(
        projection_request=projection_request(source_mode=mode, primary_root=root)
    )
    assert summary["projection_status"] == "PROJECTED"
    assert summary["learning_ingress_status"] == "PROVEN"
    assert summary["canonical_optimization_input_status"] == "PROVEN"
    assert summary["runtime_mechanical_path_status"] == "PROVEN_REAL_MECHANICAL_PATH"
    assert summary["m4_m8_status"] == "PROVEN_FIXTURE_BOUNDED"
    assert summary["g2_end_to_end_status"] == G2_END_TO_END_STATUS
    recon = trace_g2_reconstruction_v1(
        projection_result={
            "provenance": summary["reconstruction"],
            "projection_record_digest": summary["lineage_digest"],
        }
    )
    assert recon["classification"] in {"BOUNDED_RECONSTRUCTION_PROVEN", "PARTIAL_RECONSTRUCTION"}


def test_fail_closed_missing_archive(tmp_path: Path) -> None:
    ok, code, _ = validate_primary_evidence_for_projection_v1(
        source_mode=RuntimePrimarySourceModeV1.PAPER,
        primary_evidence_root=tmp_path / "missing",
    )
    assert ok is False
    assert code == "SOURCE_ARCHIVE_MISSING"


def test_fail_closed_tmp_only_source(tmp_path: Path) -> None:
    tmp_root = Path("/tmp") / f"g2_primary_evidence_fixture_{tmp_path.name}"
    tmp_root.mkdir(parents=True, exist_ok=True)
    ok, code, _ = validate_primary_evidence_for_projection_v1(
        source_mode=RuntimePrimarySourceModeV1.PAPER,
        primary_evidence_root=tmp_root,
    )
    assert ok is False
    assert code == "TMP_ONLY_SOURCE_REJECTED"


def test_fail_closed_unsupported_mode_request(tmp_path: Path) -> None:
    root = build_mode_bundle(tmp_path, RuntimePrimarySourceModeV1.SHADOW)
    metadata = json.loads((root / "RUN_METADATA.json").read_text(encoding="utf-8"))
    metadata["source_execution_mode"] = "PAPER"
    (root / "RUN_METADATA.json").write_text(
        json.dumps(metadata, sort_keys=True) + "\n", encoding="utf-8"
    )
    from scripts.ops.primary_evidence_retention_v0 import write_manifest_sha256

    write_manifest_sha256(root)
    req = projection_request(source_mode=RuntimePrimarySourceModeV1.SHADOW, primary_root=root)
    result = run_governed_runtime_primary_to_offline_observation_projection_v1(req)
    assert result.status == "REJECTED"
    assert result.decision_code == "SOURCE_MODE_MISMATCH"


def test_fail_closed_missing_instrument(tmp_path: Path) -> None:
    root = build_mode_bundle(tmp_path, RuntimePrimarySourceModeV1.PAPER)
    metadata = json.loads((root / "RUN_METADATA.json").read_text(encoding="utf-8"))
    metadata.pop("instrument")
    (root / "RUN_METADATA.json").write_text(json.dumps(metadata) + "\n", encoding="utf-8")
    from scripts.ops.primary_evidence_retention_v0 import write_manifest_sha256

    write_manifest_sha256(root)
    result = run_governed_runtime_primary_to_offline_observation_projection_v1(
        projection_request(source_mode=RuntimePrimarySourceModeV1.PAPER, primary_root=root)
    )
    assert result.status == "REJECTED"
    assert "MISSING_MANDATORY_INSTRUMENT_BINDING" in result.decision_code


def test_fail_closed_manifest_tamper(tmp_path: Path) -> None:
    root = build_mode_bundle(tmp_path, RuntimePrimarySourceModeV1.SHADOW)
    (root / "wrapper_evidence" / "steps.jsonl").write_text("{}\n", encoding="utf-8")
    result = run_governed_runtime_primary_to_offline_observation_projection_v1(
        projection_request(source_mode=RuntimePrimarySourceModeV1.SHADOW, primary_root=root)
    )
    assert result.status == "REJECTED"


def test_fail_closed_promotion_and_apply_requests(tmp_path: Path) -> None:
    root = build_mode_bundle(tmp_path, RuntimePrimarySourceModeV1.TESTNET)
    base = projection_request(source_mode=RuntimePrimarySourceModeV1.TESTNET, primary_root=root)
    for field, code in (
        ("request_promotion", "PROMOTION_AUTHORIZATION_REQUESTED"),
        ("request_runtime_apply", "RUNTIME_APPLY_REQUESTED"),
        ("start_runtime_execution", "RUNTIME_PROCESS_START_REQUESTED"),
        ("request_external_effect", "EXTERNAL_EFFECT_REQUESTED"),
    ):
        req = GovernedRuntimePrimaryProjectionRequestV1(
            **{**base.__dict__, field: True}  # type: ignore[arg-type]
        )
        result = run_governed_runtime_primary_to_offline_observation_projection_v1(req)
        assert result.decision_code == code


def test_primary_evidence_does_not_imply_apply_or_productive_authorization() -> None:
    assert PRIMARY_EVIDENCE_IMPLIES_PRODUCTIVE_AUTHORIZATION is False
    assert P5_EVIDENCE_INTAKE_IMPLIES_PRODUCTIVE_AUTHORIZATION is False
    assert P5_EVIDENCE_INTAKE_IMPLIES_RUNTIME_APPLY is False
    assert RUNTIME_APPLY_STARTED is False
    assert EXTERNAL_EFFECT is False
    assert primary_runtime_evidence_implies_apply_authorization_v1() is False


def test_field_mapping_ledger_present() -> None:
    ledger = load_field_mapping_ledger_v1(repo_root=REPO_ROOT)
    assert (
        ledger["workpackage_id"] == "GOVERNED_RUNTIME_PRIMARY_TO_OFFLINE_OBSERVATION_PROJECTION_V1"
    )
    for mode in ("PAPER", "SHADOW", "TESTNET"):
        assert mode in ledger["modes"]
        assert "primary_evidence_manifest_digest" in ledger["modes"][mode]


def test_closure_and_decision_binding() -> None:
    assert prove_g2_projection_closure_v1(repo_root=REPO_ROOT)
    decision = json.loads((REPO_ROOT / DECISION_CONFIG).read_text(encoding="utf-8"))
    assert decision["field_mapping_ledger"] == FIELD_MAPPING_LEDGER
    assert decision["g2_end_to_end_status"] == G2_END_TO_END_STATUS
