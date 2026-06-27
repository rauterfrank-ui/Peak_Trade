"""Contract tests for Package E21 offline EXPERIMENT durable evidence binding v1."""

from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path
from typing import Any, Callable
from unittest.mock import patch

import pytest

from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256
from src.experiments.base import ExperimentConfig, ParamSweep
from src.experiments.experiment_identity_manifest_v1 import (
    ARTIFACT_FILENAME,
    produce_experiment_identity_manifest_v1,
)
from src.governance.promotion_loop.candidate_lineage_manifest_v1 import (
    LineageRefType,
    LineageRelation,
)
from src.governance.promotion_loop.experiment_lineage_ref_producer_v1 import (
    EXPERIMENT_OWNER_DOMAIN,
    produce_experiment_lineage_ref_v1,
    serialize_experiment_lineage_ref_v1,
    write_experiment_lineage_ref_v1_atomic,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256
from src.meta.learning_loop.experiment_durable_evidence_binding_v1 import (
    INDEX_ARTIFACT_REL,
    LINEAGE_REF_ARTIFACT_REL,
    MANIFEST_ARTIFACT_REL,
    BoundArtifactRecord,
    ExperimentBindingCrossReferences,
    ExperimentDurableEvidenceBindingError,
    build_binding_index_v1,
    check_reference_consistency,
    produce_experiment_durable_evidence_bundle_v1,
    serialize_binding_index_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
_DURABLE_OUTPUT_ROOT = REPO_ROOT / ".package_e21_pytest_outputs"


@pytest.fixture(autouse=True)
def _allow_tmp_output(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "src.meta.learning_loop.experiment_durable_evidence_binding_v1.is_under_tmp",
        lambda _path: False,
    )


@pytest.fixture
def durable_output_dir() -> Callable[[], Path]:
    _DURABLE_OUTPUT_ROOT.mkdir(exist_ok=True)
    created: list[Path] = []

    def _make() -> Path:
        path = _DURABLE_OUTPUT_ROOT / uuid.uuid4().hex
        created.append(path)
        return path

    yield _make

    for path in created:
        if path.exists():
            shutil.rmtree(path, ignore_errors=True)
    for staging in _DURABLE_OUTPUT_ROOT.glob(".experiment_durable_evidence_staging_*"):
        shutil.rmtree(staging, ignore_errors=True)
    for staging in _DURABLE_OUTPUT_ROOT.glob(".experiment_identity_staging_*"):
        shutil.rmtree(staging, ignore_errors=True)


_durable_paths: list[Path] = []


def _next_durable_output() -> Path:
    _DURABLE_OUTPUT_ROOT.mkdir(exist_ok=True)
    path = _DURABLE_OUTPUT_ROOT / uuid.uuid4().hex
    _durable_paths.append(path)
    return path


@pytest.fixture(autouse=True)
def _cleanup_module_durable_paths() -> None:
    yield
    for path in _durable_paths:
        if path.exists():
            shutil.rmtree(path, ignore_errors=True)
    _durable_paths.clear()


def _sample_config(**overrides: Any) -> ExperimentConfig:
    base = ExperimentConfig(
        name="MA Optimization",
        strategy_name="ma_crossover",
        param_sweeps=[
            ParamSweep("slow", [50, 100], description="ignored in identity"),
            ParamSweep("fast", [5, 10]),
        ],
        symbols=["ETH/EUR", "BTC/EUR"],
        timeframe="1h",
        start_date="2024-01-01",
        end_date="2024-06-01",
        initial_capital=10000.0,
        base_params={"window": 3},
    )
    for key, value in overrides.items():
        setattr(base, key, value)
    return base


def _write_manifest_dir() -> tuple[Path, dict[str, Any]]:
    manifest_dir = _next_durable_output()
    produce_experiment_identity_manifest_v1(_sample_config(), manifest_dir)
    manifest = json.loads((manifest_dir / ARTIFACT_FILENAME).read_text(encoding="utf-8"))
    return manifest_dir, manifest


def _write_lineage_ref(manifest_dir: Path, ref_path: Path) -> None:
    result = produce_experiment_lineage_ref_v1(manifest_dir=manifest_dir)
    write_experiment_lineage_ref_v1_atomic(result.ref, ref_path, fail_closed_if_exists=True)


def _bind_inputs(tmp_path: Path) -> tuple[Path, Path, Path]:
    manifest_dir, _manifest = _write_manifest_dir()
    ref_path = tmp_path / "experiment_ref.json"
    ref_path.parent.mkdir(parents=True, exist_ok=True)
    _write_lineage_ref(manifest_dir, ref_path)
    return manifest_dir, ref_path, _next_durable_output()


def test_happy_path_binds_successfully(tmp_path: Path) -> None:
    manifest_dir, ref_path, out = _bind_inputs(tmp_path)
    manifest = json.loads((manifest_dir / ARTIFACT_FILENAME).read_text(encoding="utf-8"))
    result = produce_experiment_durable_evidence_bundle_v1(
        manifest_dir=manifest_dir,
        experiment_lineage_ref_path=ref_path,
        output_dir=out,
    )
    assert result.experiment_identity_id == manifest["experiment_identity_id"]
    assert (out / MANIFEST_ARTIFACT_REL).is_file()
    assert (out / LINEAGE_REF_ARTIFACT_REL).is_file()
    assert (out / INDEX_ARTIFACT_REL).is_file()
    ok, _ = verify_manifest_sha256(out)
    assert ok is True


def test_byte_identical_copies(tmp_path: Path) -> None:
    manifest_dir, ref_path, out = _bind_inputs(tmp_path)
    manifest_bytes = (manifest_dir / ARTIFACT_FILENAME).read_bytes()
    ref_bytes = ref_path.read_bytes()
    produce_experiment_durable_evidence_bundle_v1(
        manifest_dir=manifest_dir,
        experiment_lineage_ref_path=ref_path,
        output_dir=out,
    )
    assert (out / MANIFEST_ARTIFACT_REL).read_bytes() == manifest_bytes
    assert (out / LINEAGE_REF_ARTIFACT_REL).read_bytes() == ref_bytes


def test_binding_index_metadata_only(tmp_path: Path) -> None:
    manifest_dir, ref_path, out = _bind_inputs(tmp_path)
    manifest = json.loads((manifest_dir / ARTIFACT_FILENAME).read_text(encoding="utf-8"))
    produce_experiment_durable_evidence_bundle_v1(
        manifest_dir=manifest_dir,
        experiment_lineage_ref_path=ref_path,
        output_dir=out,
    )
    index = json.loads((out / INDEX_ARTIFACT_REL).read_text(encoding="utf-8"))
    assert index["evidence_does_not_authorize_runtime"] is True
    assert index["experiment_identity_id"] == manifest["experiment_identity_id"]
    assert "params" not in index
    assert "metrics" not in index
    assert "promotion_authority" not in index
    assert "completion" not in index
    assert all(not Path(item["relative_path"]).is_absolute() for item in index["artifacts"])


def test_domain_relation_owner_domain_bound(tmp_path: Path) -> None:
    manifest_dir, ref_path, out = _bind_inputs(tmp_path)
    produce_experiment_durable_evidence_bundle_v1(
        manifest_dir=manifest_dir,
        experiment_lineage_ref_path=ref_path,
        output_dir=out,
    )
    index = json.loads((out / INDEX_ARTIFACT_REL).read_text(encoding="utf-8"))
    ref_payload = index["experiment_lineage_ref"]
    assert ref_payload["ref_type"] == LineageRefType.EXPERIMENT.value
    assert ref_payload["relation"] == LineageRelation.SOURCES.value
    assert ref_payload["owner_domain"] == EXPERIMENT_OWNER_DOMAIN


def test_ref_id_and_digest_verbatim_no_recomputation(tmp_path: Path) -> None:
    manifest_dir, ref_path, out = _bind_inputs(tmp_path)
    manifest = json.loads((manifest_dir / ARTIFACT_FILENAME).read_text(encoding="utf-8"))
    produce_experiment_durable_evidence_bundle_v1(
        manifest_dir=manifest_dir,
        experiment_lineage_ref_path=ref_path,
        output_dir=out,
    )
    index = json.loads((out / INDEX_ARTIFACT_REL).read_text(encoding="utf-8"))
    assert index["experiment_identity_id"] == manifest["experiment_identity_id"]
    assert index["cross_references"]["experiment_identity_id"] == manifest["experiment_identity_id"]
    assert (
        index["cross_references"]["lineage_ref_digest"] == manifest["integrity"]["content_sha256"]
    )
    assert index["experiment_lineage_ref"]["ref_id"] == manifest["experiment_identity_id"]
    assert index["experiment_lineage_ref"]["digest"] == manifest["integrity"]["content_sha256"]


def test_check_reference_consistency_digest_mismatch(tmp_path: Path) -> None:
    manifest_dir, ref_path, _ = _bind_inputs(tmp_path)
    manifest = json.loads((manifest_dir / ARTIFACT_FILENAME).read_text(encoding="utf-8"))
    result = produce_experiment_lineage_ref_v1(manifest_dir=manifest_dir)
    ref = result.ref
    bad_ref = type(ref)(
        ref_type=ref.ref_type,
        ref_id=ref.ref_id,
        relation=ref.relation,
        owner_domain=ref.owner_domain,
        required=ref.required,
        digest="0" * 64,
        artifact_path=ref.artifact_path,
        schema_version=ref.schema_version,
    )
    with pytest.raises(ExperimentDurableEvidenceBindingError, match="digest"):
        check_reference_consistency(manifest=manifest, ref=bad_ref)


def test_wrong_ref_id_fail_closed(tmp_path: Path) -> None:
    manifest_dir, ref_path, out = _bind_inputs(tmp_path)
    payload = json.loads(ref_path.read_text(encoding="utf-8"))
    payload["ref_id"] = "0" * 64
    ref_path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ExperimentDurableEvidenceBindingError, match="ref_id"):
        produce_experiment_durable_evidence_bundle_v1(
            manifest_dir=manifest_dir,
            experiment_lineage_ref_path=ref_path,
            output_dir=out,
        )


def test_wrong_ref_type_fail_closed(tmp_path: Path) -> None:
    manifest_dir, ref_path, out = _bind_inputs(tmp_path)
    payload = json.loads(ref_path.read_text(encoding="utf-8"))
    payload["ref_type"] = LineageRefType.BACKTEST.value
    ref_path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ExperimentDurableEvidenceBindingError, match="EXPERIMENT"):
        produce_experiment_durable_evidence_bundle_v1(
            manifest_dir=manifest_dir,
            experiment_lineage_ref_path=ref_path,
            output_dir=out,
        )


def test_wrong_relation_fail_closed(tmp_path: Path) -> None:
    manifest_dir, ref_path, out = _bind_inputs(tmp_path)
    payload = json.loads(ref_path.read_text(encoding="utf-8"))
    payload["relation"] = LineageRelation.EVALUATES.value
    ref_path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ExperimentDurableEvidenceBindingError, match="SOURCES"):
        produce_experiment_durable_evidence_bundle_v1(
            manifest_dir=manifest_dir,
            experiment_lineage_ref_path=ref_path,
            output_dir=out,
        )


def test_wrong_owner_domain_fail_closed(tmp_path: Path) -> None:
    manifest_dir, ref_path, out = _bind_inputs(tmp_path)
    payload = json.loads(ref_path.read_text(encoding="utf-8"))
    payload["owner_domain"] = "backtests/base"
    ref_path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ExperimentDurableEvidenceBindingError, match="owner_domain"):
        produce_experiment_durable_evidence_bundle_v1(
            manifest_dir=manifest_dir,
            experiment_lineage_ref_path=ref_path,
            output_dir=out,
        )


def test_missing_identity_manifest_fail_closed(tmp_path: Path) -> None:
    manifest_dir = tmp_path / "sources" / "empty_manifest_dir"
    manifest_dir.mkdir(parents=True)
    good_dir, _ = _write_manifest_dir()
    ref_path = tmp_path / "sources" / "orphan_ref.json"
    _write_lineage_ref(good_dir, ref_path)
    out = _next_durable_output()
    with pytest.raises(ExperimentDurableEvidenceBindingError, match="not found"):
        produce_experiment_durable_evidence_bundle_v1(
            manifest_dir=manifest_dir,
            experiment_lineage_ref_path=ref_path,
            output_dir=out,
        )


def test_invalid_manifest_json_fail_closed(tmp_path: Path) -> None:
    manifest_dir = tmp_path / "sources" / "bad-json"
    manifest_dir.mkdir(parents=True)
    (manifest_dir / ARTIFACT_FILENAME).write_text("{broken", encoding="utf-8")
    good_dir, _ = _write_manifest_dir()
    ref_path = tmp_path / "sources" / "ref.json"
    _write_lineage_ref(good_dir, ref_path)
    out = _next_durable_output()
    with pytest.raises(ExperimentDurableEvidenceBindingError):
        produce_experiment_durable_evidence_bundle_v1(
            manifest_dir=manifest_dir,
            experiment_lineage_ref_path=ref_path,
            output_dir=out,
        )


def test_invalid_package_n_manifest_fail_closed(tmp_path: Path) -> None:
    manifest_dir, ref_path, out = _bind_inputs(tmp_path)
    manifest_path = manifest_dir / ARTIFACT_FILENAME
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload["experiment_identity_id"] = "0" * 64
    manifest_path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ExperimentDurableEvidenceBindingError, match="validation failed"):
        produce_experiment_durable_evidence_bundle_v1(
            manifest_dir=manifest_dir,
            experiment_lineage_ref_path=ref_path,
            output_dir=out,
        )


def test_missing_lineage_ref_fail_closed(tmp_path: Path) -> None:
    manifest_dir, _ = _write_manifest_dir()
    out = _next_durable_output()
    with pytest.raises(ExperimentDurableEvidenceBindingError, match="not found"):
        produce_experiment_durable_evidence_bundle_v1(
            manifest_dir=manifest_dir,
            experiment_lineage_ref_path=tmp_path / "missing_ref.json",
            output_dir=out,
        )


def test_invalid_lineage_ref_json_fail_closed(tmp_path: Path) -> None:
    manifest_dir, _ = _write_manifest_dir()
    ref_path = tmp_path / "sources" / "bad_ref.json"
    ref_path.parent.mkdir(parents=True)
    ref_path.write_text("{broken", encoding="utf-8")
    out = _next_durable_output()
    with pytest.raises(ExperimentDurableEvidenceBindingError):
        produce_experiment_durable_evidence_bundle_v1(
            manifest_dir=manifest_dir,
            experiment_lineage_ref_path=ref_path,
            output_dir=out,
        )


def test_symlink_manifest_dir_rejected(tmp_path: Path) -> None:
    manifest_dir, ref_path, out = _bind_inputs(tmp_path)
    link = tmp_path / "manifest_link"
    link.parent.mkdir(parents=True, exist_ok=True)
    link.symlink_to(manifest_dir, target_is_directory=True)
    with pytest.raises(ExperimentDurableEvidenceBindingError, match="symlink"):
        produce_experiment_durable_evidence_bundle_v1(
            manifest_dir=link,
            experiment_lineage_ref_path=ref_path,
            output_dir=out,
        )


def test_existing_output_dir_fail_closed(tmp_path: Path) -> None:
    manifest_dir, ref_path, out = _bind_inputs(tmp_path)
    out.mkdir(parents=True)
    with pytest.raises(ExperimentDurableEvidenceBindingError, match="already exists"):
        produce_experiment_durable_evidence_bundle_v1(
            manifest_dir=manifest_dir,
            experiment_lineage_ref_path=ref_path,
            output_dir=out,
        )


def test_deterministic_index_and_manifest(tmp_path: Path) -> None:
    manifest_dir, ref_path, _ = _bind_inputs(tmp_path)
    out1 = _next_durable_output()
    out2 = _next_durable_output()
    produce_experiment_durable_evidence_bundle_v1(
        manifest_dir=manifest_dir,
        experiment_lineage_ref_path=ref_path,
        output_dir=out1,
    )
    produce_experiment_durable_evidence_bundle_v1(
        manifest_dir=manifest_dir,
        experiment_lineage_ref_path=ref_path,
        output_dir=out2,
    )
    assert (out1 / INDEX_ARTIFACT_REL).read_bytes() == (out2 / INDEX_ARTIFACT_REL).read_bytes()
    assert (out1 / "MANIFEST.sha256").read_bytes() == (out2 / "MANIFEST.sha256").read_bytes()


def test_copy_failure_cleans_up(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    manifest_dir, ref_path, out = _bind_inputs(tmp_path)

    def _boom(_src: Path, _dst: Path) -> str:
        raise OSError("copy failed")

    monkeypatch.setattr(
        "src.meta.learning_loop.experiment_durable_evidence_binding_v1._copy_byte_identical",
        _boom,
    )
    with pytest.raises(OSError, match="copy failed"):
        produce_experiment_durable_evidence_bundle_v1(
            manifest_dir=manifest_dir,
            experiment_lineage_ref_path=ref_path,
            output_dir=out,
        )
    assert not out.exists()


def test_manifest_verify_failure_cleans_up(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    manifest_dir, ref_path, out = _bind_inputs(tmp_path)
    monkeypatch.setattr(
        "src.meta.learning_loop.experiment_durable_evidence_binding_v1.verify_manifest_sha256",
        lambda _root: (False, "checksum mismatch"),
    )
    with pytest.raises(ExperimentDurableEvidenceBindingError, match="verification failed"):
        produce_experiment_durable_evidence_bundle_v1(
            manifest_dir=manifest_dir,
            experiment_lineage_ref_path=ref_path,
            output_dir=out,
        )
    assert not out.exists()


def test_build_binding_index_rejects_forbidden_key(tmp_path: Path) -> None:
    manifest_dir, _ = _write_manifest_dir()
    ref = produce_experiment_lineage_ref_v1(manifest_dir=manifest_dir).ref
    cross = ExperimentBindingCrossReferences(
        experiment_identity_id=ref.ref_id,
        lineage_ref_digest=ref.digest or "a" * 64,
        lineage_ref_artifact_path=ref.artifact_path or ARTIFACT_FILENAME,
    )
    artifacts = (
        BoundArtifactRecord("experiment_identity_manifest_v1", MANIFEST_ARTIFACT_REL, "b" * 64),
        BoundArtifactRecord("experiment_lineage_ref_v1", LINEAGE_REF_ARTIFACT_REL, "c" * 64),
    )
    index = build_binding_index_v1(
        experiment_identity_id=ref.ref_id,
        cross_references=cross,
        ref=ref,
        artifacts=artifacts,
    )
    index["promotion_authority"] = True
    with pytest.raises(ExperimentDurableEvidenceBindingError, match="forbidden key"):
        serialize_binding_index_v1(index)


def test_integrity_hash_stable_for_index_payload(tmp_path: Path) -> None:
    manifest_dir, ref_path, _ = _bind_inputs(tmp_path)
    manifest = json.loads((manifest_dir / ARTIFACT_FILENAME).read_text(encoding="utf-8"))
    ref = produce_experiment_lineage_ref_v1(manifest_dir=manifest_dir).ref
    cross = check_reference_consistency(manifest=manifest, ref=ref)
    artifacts = (
        BoundArtifactRecord("experiment_identity_manifest_v1", MANIFEST_ARTIFACT_REL, "a" * 64),
        BoundArtifactRecord("experiment_lineage_ref_v1", LINEAGE_REF_ARTIFACT_REL, "b" * 64),
    )
    index = build_binding_index_v1(
        experiment_identity_id=manifest["experiment_identity_id"],
        cross_references=cross,
        ref=ref,
        artifacts=artifacts,
    )
    payload = dict(index)
    digest = payload.pop("integrity")
    assert digest["content_sha256"] == compute_content_sha256(payload)


def test_output_under_tmp_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts.ops.primary_evidence_retention_v0 import is_under_tmp as real_is_under_tmp

    monkeypatch.setattr(
        "src.meta.learning_loop.experiment_durable_evidence_binding_v1.is_under_tmp",
        real_is_under_tmp,
    )
    manifest_dir, ref_path, _ = _bind_inputs(tmp_path)
    out = Path("/tmp/peak_trade_pkg_e21_binding_reject_test")
    try:
        with pytest.raises(ExperimentDurableEvidenceBindingError, match="outside /tmp"):
            produce_experiment_durable_evidence_bundle_v1(
                manifest_dir=manifest_dir,
                experiment_lineage_ref_path=ref_path,
                output_dir=out,
            )
    finally:
        if out.exists():
            shutil.rmtree(out)


def test_no_runtime_imports_in_binding_module() -> None:
    import ast

    path = Path("src/meta/learning_loop/experiment_durable_evidence_binding_v1.py")
    tree = ast.parse(path.read_text(encoding="utf-8"))
    forbidden = ("promotion_loop.engine", "governance.promotion_loop.engine")
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            for token in forbidden:
                assert token not in node.module


def test_package_m_ref_serialization_compatible(tmp_path: Path) -> None:
    manifest_dir, ref_path, out = _bind_inputs(tmp_path)
    produce_experiment_durable_evidence_bundle_v1(
        manifest_dir=manifest_dir,
        experiment_lineage_ref_path=ref_path,
        output_dir=out,
    )
    original = json.loads(ref_path.read_text(encoding="utf-8"))
    copied = json.loads((out / LINEAGE_REF_ARTIFACT_REL).read_text(encoding="utf-8"))
    assert copied == original
    assert copied == json.loads(
        serialize_experiment_lineage_ref_v1(
            produce_experiment_lineage_ref_v1(manifest_dir=manifest_dir).ref
        )
    )


def test_input_mutation_between_validation_and_copy_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest_dir, ref_path, out = _bind_inputs(tmp_path)
    original_copy = shutil.copyfile

    def _mutating_copy(src: Path, dst: Path) -> None:
        original_copy(src, dst)
        if src.name == ARTIFACT_FILENAME:
            src.write_text('{"experiment_identity_id":"mutated"}', encoding="utf-8")

    monkeypatch.setattr(shutil, "copyfile", _mutating_copy)
    with pytest.raises(ExperimentDurableEvidenceBindingError):
        produce_experiment_durable_evidence_bundle_v1(
            manifest_dir=manifest_dir,
            experiment_lineage_ref_path=ref_path,
            output_dir=out,
        )
    assert not out.exists()


def test_wrong_manifest_filename_fail_closed(tmp_path: Path) -> None:
    manifest_dir, ref_path, out = _bind_inputs(tmp_path)
    wrong_name = manifest_dir / "wrong_manifest.json"
    wrong_name.write_bytes((manifest_dir / ARTIFACT_FILENAME).read_bytes())
    (manifest_dir / ARTIFACT_FILENAME).unlink()
    with pytest.raises(ExperimentDurableEvidenceBindingError, match="not found"):
        produce_experiment_durable_evidence_bundle_v1(
            manifest_dir=manifest_dir,
            experiment_lineage_ref_path=ref_path,
            output_dir=out,
        )


def test_existing_target_replay_contract(tmp_path: Path) -> None:
    manifest_dir, ref_path, out = _bind_inputs(tmp_path)
    produce_experiment_durable_evidence_bundle_v1(
        manifest_dir=manifest_dir,
        experiment_lineage_ref_path=ref_path,
        output_dir=out,
    )
    replay_out = _next_durable_output()
    produce_experiment_durable_evidence_bundle_v1(
        manifest_dir=manifest_dir,
        experiment_lineage_ref_path=ref_path,
        output_dir=replay_out,
    )
    assert (out / INDEX_ARTIFACT_REL).read_bytes() == (replay_out / INDEX_ARTIFACT_REL).read_bytes()
