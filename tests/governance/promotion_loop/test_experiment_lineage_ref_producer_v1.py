"""Producer tests for Package M offline EXPERIMENT LineageRef production."""

from __future__ import annotations

import copy
import json
import os
import shutil
import stat
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from unittest.mock import patch

import pytest

from src.experiments.base import ExperimentConfig, ParamSweep
from src.experiments.experiment_identity_manifest_v1 import (
    ARTIFACT_FILENAME,
    build_manifest,
    produce_experiment_identity_manifest_v1,
    validate_experiment_identity_manifest_v1,
)
from src.governance.promotion_loop.candidate_lineage_manifest_v1 import (
    CandidateType,
    LineageRefType,
    LineageRelation,
    build_candidate_lineage_manifest_v1_from_producer_input,
    lineage_ref_from_mapping,
    lineage_ref_to_mapping,
    serialize_candidate_lineage_manifest_v1,
    validate_candidate_lineage_manifest_v1,
)
from src.governance.promotion_loop.experiment_lineage_ref_producer_v1 import (
    EXPERIMENT_LINEAGE_REF_REQUIRED,
    EXPERIMENT_OWNER_DOMAIN,
    ExperimentLineageRefProducerError,
    build_experiment_lineage_ref_from_manifest,
    produce_experiment_lineage_ref_v1,
    produce_experiment_lineage_ref_v1_to_path,
    serialize_experiment_lineage_ref_v1,
    write_experiment_lineage_ref_v1_atomic,
)
from src.meta.learning_loop.contract_safety_v1 import is_valid_sha256_hex

REPO_ROOT = Path(__file__).resolve().parents[3]
_DURABLE_OUTPUT_ROOT = REPO_ROOT / ".package_m_pytest_outputs"
LINEAGE_ID = "11111111-1111-4111-8111-111111111111"
CONTRACT_REF = "22222222-2222-4222-8222-222222222222"


@pytest.fixture
def durable_output_dir() -> Callable[[], Path]:
    """Output paths outside /tmp for producer atomic-write contract tests."""
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
    for staging in _DURABLE_OUTPUT_ROOT.glob(".experiment_identity_staging_*"):
        shutil.rmtree(staging, ignore_errors=True)


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


def _write_manifest_dir(
    durable_output_dir: Callable[[], Path],
    *,
    config: ExperimentConfig | None = None,
    source_experiment_id: str | None = None,
) -> tuple[Path, dict[str, Any]]:
    manifest_dir = durable_output_dir()
    produce_experiment_identity_manifest_v1(
        config or _sample_config(),
        manifest_dir,
        source_experiment_id=source_experiment_id,
    )
    manifest = json.loads((manifest_dir / ARTIFACT_FILENAME).read_text(encoding="utf-8"))
    return manifest_dir, manifest


def test_happy_path_produces_valid_experiment_ref(
    durable_output_dir: Callable[[], Path],
) -> None:
    manifest_dir, manifest = _write_manifest_dir(durable_output_dir)
    result = produce_experiment_lineage_ref_v1(manifest_dir=manifest_dir)
    ref = result.ref
    assert ref.ref_type == LineageRefType.EXPERIMENT
    assert ref.relation == LineageRelation.SOURCES
    assert ref.owner_domain == EXPERIMENT_OWNER_DOMAIN
    assert ref.required is EXPERIMENT_LINEAGE_REF_REQUIRED
    assert ref.artifact_path == ARTIFACT_FILENAME
    assert ref.ref_id == manifest["experiment_identity_id"]
    assert ref.digest == manifest["integrity"]["content_sha256"]


def test_ref_id_exactly_adopted_from_experiment_identity_id(
    durable_output_dir: Callable[[], Path],
) -> None:
    manifest_dir, manifest = _write_manifest_dir(durable_output_dir)
    result = produce_experiment_lineage_ref_v1(manifest_dir=manifest_dir)
    assert result.ref.ref_id == manifest["experiment_identity_id"]
    assert is_valid_sha256_hex(result.ref.ref_id)


def test_digest_exactly_adopted_from_integrity_content_sha256(
    durable_output_dir: Callable[[], Path],
) -> None:
    manifest_dir, manifest = _write_manifest_dir(durable_output_dir)
    result = produce_experiment_lineage_ref_v1(manifest_dir=manifest_dir)
    assert result.ref.digest == manifest["integrity"]["content_sha256"]
    assert is_valid_sha256_hex(result.ref.digest)


def test_no_recomputation_of_ref_id_or_digest(
    durable_output_dir: Callable[[], Path],
) -> None:
    manifest_dir, manifest = _write_manifest_dir(durable_output_dir)
    result = produce_experiment_lineage_ref_v1(manifest_dir=manifest_dir)
    assert result.ref.ref_id == manifest["experiment_identity_id"]
    assert result.ref.digest == manifest["integrity"]["content_sha256"]
    assert result.ref.ref_id != manifest["legacy_aliases"]["legacy_experiment_id_md5_12"]


def test_deterministic_canonical_json_output(
    durable_output_dir: Callable[[], Path],
) -> None:
    manifest_dir, _manifest = _write_manifest_dir(durable_output_dir)
    result = produce_experiment_lineage_ref_v1(manifest_dir=manifest_dir)
    first = serialize_experiment_lineage_ref_v1(result.ref)
    second = serialize_experiment_lineage_ref_v1(result.ref)
    assert first == second
    assert json.loads(first) == json.loads(second)


def test_candidate_lineage_manifest_v1_accepts_producer_output(
    durable_output_dir: Callable[[], Path],
) -> None:
    manifest_dir, manifest = _write_manifest_dir(durable_output_dir)
    ref = produce_experiment_lineage_ref_v1(manifest_dir=manifest_dir).ref
    fixed_now = datetime(2026, 6, 27, 18, 0, 0, tzinfo=timezone.utc)
    candidate_manifest = build_candidate_lineage_manifest_v1_from_producer_input(
        {
            "lineage_manifest_id": LINEAGE_ID,
            "candidate_id": "candidate-package-m-001",
            "candidate_type": CandidateType.CONFIG_PATCH_BUNDLE.value,
            "candidate_contract_ref": CONTRACT_REF,
            "refs": [lineage_ref_to_mapping(ref)],
            "created_at": fixed_now.isoformat(),
        },
        created_at=fixed_now,
    )
    payload = json.loads(serialize_candidate_lineage_manifest_v1(candidate_manifest))
    valid, phase, errors, _ = validate_candidate_lineage_manifest_v1(payload)
    assert valid is True, (phase, errors)
    assert payload["refs"][0]["ref_id"] == manifest["experiment_identity_id"]
    assert payload["refs"][0]["ref_type"] == LineageRefType.EXPERIMENT.value


def test_missing_manifest_dir_fails_closed(tmp_path: Path) -> None:
    with pytest.raises(ExperimentLineageRefProducerError, match="manifest_dir not found"):
        produce_experiment_lineage_ref_v1(manifest_dir=tmp_path / "missing")


def test_manifest_path_is_file_not_directory(tmp_path: Path) -> None:
    file_path = tmp_path / "not-a-dir"
    file_path.write_text("x", encoding="utf-8")
    with pytest.raises(ExperimentLineageRefProducerError, match="not a directory"):
        produce_experiment_lineage_ref_v1(manifest_dir=file_path)


def test_missing_manifest_artifact_fails_closed(tmp_path: Path) -> None:
    manifest_dir = tmp_path / "empty-dir"
    manifest_dir.mkdir()
    with pytest.raises(ExperimentLineageRefProducerError, match=f"{ARTIFACT_FILENAME} not found"):
        produce_experiment_lineage_ref_v1(manifest_dir=manifest_dir)


def test_wrong_manifest_filename_fails_closed(
    durable_output_dir: Callable[[], Path],
) -> None:
    manifest_dir, _manifest = _write_manifest_dir(durable_output_dir)
    artifact = manifest_dir / ARTIFACT_FILENAME
    artifact.rename(manifest_dir / "wrong_manifest_name.json")
    with pytest.raises(ExperimentLineageRefProducerError, match=f"{ARTIFACT_FILENAME} not found"):
        produce_experiment_lineage_ref_v1(manifest_dir=manifest_dir)


def test_invalid_json_fails_closed(tmp_path: Path) -> None:
    manifest_dir = tmp_path / "bad-json-dir"
    manifest_dir.mkdir()
    (manifest_dir / ARTIFACT_FILENAME).write_text("{not-json", encoding="utf-8")
    with pytest.raises(ExperimentLineageRefProducerError, match="invalid"):
        produce_experiment_lineage_ref_v1(manifest_dir=manifest_dir)


def test_package_n_validator_rejects_invalid_manifest(tmp_path: Path) -> None:
    manifest_dir = tmp_path / "invalid-manifest-dir"
    manifest_dir.mkdir()
    invalid = {"schema_version": "9.9", "experiment_identity_id": "x" * 64}
    (manifest_dir / ARTIFACT_FILENAME).write_text(json.dumps(invalid), encoding="utf-8")
    with pytest.raises(ExperimentLineageRefProducerError, match="validation failed"):
        produce_experiment_lineage_ref_v1(manifest_dir=manifest_dir)


def test_identity_id_mismatch_fails_closed(
    durable_output_dir: Callable[[], Path],
) -> None:
    manifest_dir, manifest = _write_manifest_dir(durable_output_dir)
    tampered = copy.deepcopy(manifest)
    tampered["experiment_identity_id"] = "a" * 64
    (manifest_dir / ARTIFACT_FILENAME).write_text(json.dumps(tampered), encoding="utf-8")
    with pytest.raises(ExperimentLineageRefProducerError, match="experiment_identity_id mismatch"):
        produce_experiment_lineage_ref_v1(manifest_dir=manifest_dir)


def test_digest_mismatch_fails_closed(
    durable_output_dir: Callable[[], Path],
) -> None:
    manifest_dir, manifest = _write_manifest_dir(durable_output_dir)
    tampered = copy.deepcopy(manifest)
    tampered["integrity"] = dict(tampered["integrity"])
    tampered["integrity"]["content_sha256"] = "b" * 64
    (manifest_dir / ARTIFACT_FILENAME).write_text(json.dumps(tampered), encoding="utf-8")
    with pytest.raises(ExperimentLineageRefProducerError, match="integrity"):
        produce_experiment_lineage_ref_v1(manifest_dir=manifest_dir)


def test_legacy_md5_must_not_become_ref_id(
    durable_output_dir: Callable[[], Path],
) -> None:
    manifest_dir, manifest = _write_manifest_dir(durable_output_dir)
    result = produce_experiment_lineage_ref_v1(manifest_dir=manifest_dir)
    legacy_id = manifest["legacy_aliases"]["legacy_experiment_id_md5_12"]
    assert result.ref.ref_id != legacy_id
    assert result.ref.ref_id == manifest["experiment_identity_id"]


def test_source_experiment_id_must_not_become_ref_id(
    durable_output_dir: Callable[[], Path],
) -> None:
    manifest_dir, manifest = _write_manifest_dir(
        durable_output_dir,
        source_experiment_id="legacy-src-123",
    )
    result = produce_experiment_lineage_ref_v1(manifest_dir=manifest_dir)
    assert manifest["provenance"]["source_experiment_id"] == "legacy-src-123"
    assert result.ref.ref_id != "legacy-src-123"
    assert result.ref.ref_id == manifest["experiment_identity_id"]


def test_registry_run_id_forbidden_in_manifest(
    durable_output_dir: Callable[[], Path],
) -> None:
    manifest_dir, manifest = _write_manifest_dir(durable_output_dir)
    tampered = copy.deepcopy(manifest)
    tampered["registry_run_id"] = "registry-abc"
    (manifest_dir / ARTIFACT_FILENAME).write_text(json.dumps(tampered), encoding="utf-8")
    with pytest.raises(ExperimentLineageRefProducerError, match="registry_run_id"):
        produce_experiment_lineage_ref_v1(manifest_dir=manifest_dir)


def test_mlflow_run_id_forbidden_in_manifest(
    durable_output_dir: Callable[[], Path],
) -> None:
    manifest_dir, manifest = _write_manifest_dir(durable_output_dir)
    tampered = copy.deepcopy(manifest)
    tampered["mlflow_run_id"] = "mlflow-abc"
    (manifest_dir / ARTIFACT_FILENAME).write_text(json.dumps(tampered), encoding="utf-8")
    with pytest.raises(ExperimentLineageRefProducerError, match="mlflow_run_id"):
        produce_experiment_lineage_ref_v1(manifest_dir=manifest_dir)


def test_backtest_run_id_forbidden_in_manifest(
    durable_output_dir: Callable[[], Path],
) -> None:
    manifest_dir, manifest = _write_manifest_dir(durable_output_dir)
    tampered = copy.deepcopy(manifest)
    tampered["run_id"] = "backtest-run-001"
    (manifest_dir / ARTIFACT_FILENAME).write_text(json.dumps(tampered), encoding="utf-8")
    with pytest.raises(ExperimentLineageRefProducerError, match="run_id"):
        produce_experiment_lineage_ref_v1(manifest_dir=manifest_dir)


def test_manifest_dir_symlink_fails_closed(
    tmp_path: Path,
    durable_output_dir: Callable[[], Path],
) -> None:
    real_dir, _manifest = _write_manifest_dir(durable_output_dir)
    link = tmp_path / "linked-manifest"
    link.symlink_to(real_dir, target_is_directory=True)
    with pytest.raises(ExperimentLineageRefProducerError, match="must not be a symlink"):
        produce_experiment_lineage_ref_v1(manifest_dir=link)


def test_manifest_artifact_symlink_fails_closed(
    tmp_path: Path,
    durable_output_dir: Callable[[], Path],
) -> None:
    manifest_dir, manifest = _write_manifest_dir(durable_output_dir)
    artifact = manifest_dir / ARTIFACT_FILENAME
    external = tmp_path / "external_manifest.json"
    external.write_text(json.dumps(manifest), encoding="utf-8")
    artifact.unlink()
    artifact.symlink_to(external)
    with pytest.raises(ExperimentLineageRefProducerError, match="must not be a symlink"):
        produce_experiment_lineage_ref_v1(manifest_dir=manifest_dir)


def test_manifest_file_not_modified(
    durable_output_dir: Callable[[], Path],
) -> None:
    manifest_dir, _manifest = _write_manifest_dir(durable_output_dir)
    manifest_path = manifest_dir / ARTIFACT_FILENAME
    before = manifest_path.read_bytes()
    produce_experiment_lineage_ref_v1(manifest_dir=manifest_dir)
    assert manifest_path.read_bytes() == before


def test_atomic_writer_success_and_fail_closed_existing(
    tmp_path: Path,
    durable_output_dir: Callable[[], Path],
) -> None:
    manifest_dir, _manifest = _write_manifest_dir(durable_output_dir)
    ref = produce_experiment_lineage_ref_v1(manifest_dir=manifest_dir).ref
    output_path = tmp_path / "ref.json"
    write_experiment_lineage_ref_v1_atomic(ref, output_path)
    assert output_path.is_file()
    with pytest.raises(ExperimentLineageRefProducerError, match="already exists"):
        write_experiment_lineage_ref_v1_atomic(ref, output_path)


def test_end_to_end_producer_writes_output(
    tmp_path: Path,
    durable_output_dir: Callable[[], Path],
) -> None:
    manifest_dir, manifest = _write_manifest_dir(durable_output_dir)
    output_path = tmp_path / "out" / "experiment_ref.json"
    produce_experiment_lineage_ref_v1_to_path(
        manifest_dir=manifest_dir,
        output_path=output_path,
    )
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["ref_type"] == LineageRefType.EXPERIMENT.value
    assert payload["ref_id"] == manifest["experiment_identity_id"]
    assert payload["digest"] == manifest["integrity"]["content_sha256"]


def test_self_verification_roundtrip(
    tmp_path: Path,
    durable_output_dir: Callable[[], Path],
) -> None:
    manifest_dir, _manifest = _write_manifest_dir(durable_output_dir)
    ref = produce_experiment_lineage_ref_v1(manifest_dir=manifest_dir).ref
    output_path = tmp_path / "ref.json"
    write_experiment_lineage_ref_v1_atomic(ref, output_path)
    roundtrip = lineage_ref_from_mapping(json.loads(output_path.read_text(encoding="utf-8")))
    assert roundtrip == ref


def test_build_from_manifest_rejects_missing_ref_id() -> None:
    manifest = build_manifest(_sample_config())
    tampered = copy.deepcopy(manifest)
    del tampered["experiment_identity_id"]
    with pytest.raises(ExperimentLineageRefProducerError, match="experiment_identity_id"):
        build_experiment_lineage_ref_from_manifest(tampered)


def test_build_from_manifest_rejects_missing_digest() -> None:
    manifest = build_manifest(_sample_config())
    tampered = copy.deepcopy(manifest)
    tampered["integrity"] = {}
    with pytest.raises(ExperimentLineageRefProducerError, match="content_sha256"):
        build_experiment_lineage_ref_from_manifest(tampered)


def test_no_experiment_execution(
    durable_output_dir: Callable[[], Path],
) -> None:
    manifest_dir, _manifest = _write_manifest_dir(durable_output_dir)
    result = produce_experiment_lineage_ref_v1(manifest_dir=manifest_dir)
    assert result.ref.ref_type == LineageRefType.EXPERIMENT


def test_no_backtest_execution(
    durable_output_dir: Callable[[], Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest_dir, _manifest = _write_manifest_dir(durable_output_dir)

    def _forbidden(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("backtest execution forbidden")

    monkeypatch.setattr(
        "src.risk.validation.var_suite_backtest_wiring_v1.resolve_backtest_returns",
        _forbidden,
    )
    produce_experiment_lineage_ref_v1(manifest_dir=manifest_dir)


def test_no_registry_or_mlflow_resolution(
    durable_output_dir: Callable[[], Path],
) -> None:
    manifest_dir, _manifest = _write_manifest_dir(durable_output_dir)

    def _forbidden(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("registry or mlflow resolution forbidden")

    with patch("urllib.request.urlopen", side_effect=_forbidden):
        produce_experiment_lineage_ref_v1(manifest_dir=manifest_dir)


def test_atomic_write_outside_tmp(durable_output_dir: Callable[[], Path]) -> None:
    manifest_dir, _manifest = _write_manifest_dir(durable_output_dir)
    output_path = durable_output_dir() / "experiment_ref.json"
    produce_experiment_lineage_ref_v1_to_path(
        manifest_dir=manifest_dir,
        output_path=output_path,
    )
    assert output_path.is_file()


def test_non_writable_output_parent(
    tmp_path: Path,
    durable_output_dir: Callable[[], Path],
) -> None:
    manifest_dir, _manifest = _write_manifest_dir(durable_output_dir)
    ref = produce_experiment_lineage_ref_v1(manifest_dir=manifest_dir).ref
    readonly_dir = tmp_path / "readonly"
    readonly_dir.mkdir()
    output_path = readonly_dir / "out.json"
    os.chmod(readonly_dir, stat.S_IRUSR | stat.S_IXUSR)
    try:
        with pytest.raises(OSError):
            write_experiment_lineage_ref_v1_atomic(ref, output_path)
    finally:
        os.chmod(readonly_dir, stat.S_IRWXU)
    assert not output_path.exists()


def test_validate_experiment_identity_manifest_v1_is_mandatory(
    durable_output_dir: Callable[[], Path],
) -> None:
    manifest_dir, manifest = _write_manifest_dir(durable_output_dir)
    calls: list[dict[str, Any]] = []
    original = validate_experiment_identity_manifest_v1

    def _tracked_validate(payload):  # type: ignore[no-untyped-def]
        calls.append(dict(payload))
        return original(payload)

    with patch(
        "src.governance.promotion_loop.experiment_lineage_ref_producer_v1.validate_experiment_identity_manifest_v1",
        side_effect=_tracked_validate,
    ):
        produce_experiment_lineage_ref_v1(manifest_dir=manifest_dir)
    assert calls
    assert calls[0]["experiment_identity_id"] == manifest["experiment_identity_id"]
