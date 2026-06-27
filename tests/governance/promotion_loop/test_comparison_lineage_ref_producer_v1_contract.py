"""Contract tests for offline COMPARISON LineageRef production."""

from __future__ import annotations

import copy
import json
import os
import shutil
import stat
import uuid
from pathlib import Path
from typing import Callable
from unittest.mock import patch

import pytest

pytest_plugins = ["tests.meta.comparison_ssot_v1_fixtures"]

from src.governance.promotion_loop.candidate_lineage_manifest_v1 import (
    LineageRefType,
    LineageRelation,
    lineage_ref_from_mapping,
    lineage_ref_to_mapping,
)
from src.governance.promotion_loop.comparison_lineage_ref_producer_v1 import (
    COMPARISON_LINEAGE_REF_REQUIRED,
    COMPARISON_OWNER_DOMAIN,
    ComparisonLineageRefProducerError,
    build_comparison_lineage_ref_from_result_manifest,
    produce_comparison_lineage_ref_v1,
    produce_comparison_lineage_ref_v1_to_path,
    serialize_comparison_lineage_ref_v1,
    write_comparison_lineage_ref_v1_atomic,
)
from src.meta.learning_loop.comparison_ssot_v1.constants import RESULT_ARTIFACT_FILENAME
from src.meta.learning_loop.comparison_ssot_v1.io import read_manifest
from src.meta.learning_loop.comparison_ssot_v1.validation import validate_result_manifest_v1
from tests.meta.comparison_ssot_v1_fixtures import produce_comparison_pair

REPO_ROOT = Path(__file__).resolve().parents[3]
_DURABLE_OUTPUT_ROOT = REPO_ROOT / ".comparison_lineage_ref_pytest_outputs"


@pytest.fixture
def lineage_ref_durable_output_dir() -> Callable[[], Path]:
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


def _result_manifest_dir(
    tmp_path: Path,
    ssot_durable_output_dir: Path,
) -> tuple[Path, dict[str, object]]:
    _, result_path, definition_id = produce_comparison_pair(tmp_path, ssot_durable_output_dir)
    manifest = read_manifest(result_path)
    return result_path.parent, manifest


def test_happy_path_produces_valid_comparison_ref(
    tmp_path: Path,
    ssot_durable_output_dir: Path,
) -> None:
    manifest_dir, manifest = _result_manifest_dir(tmp_path, ssot_durable_output_dir)
    result = produce_comparison_lineage_ref_v1(manifest_dir=manifest_dir)
    ref = result.ref
    assert ref.ref_type == LineageRefType.COMPARISON
    assert ref.relation == LineageRelation.DERIVES_FROM_RESULT_MANIFEST
    assert ref.owner_domain == COMPARISON_OWNER_DOMAIN
    assert ref.required is COMPARISON_LINEAGE_REF_REQUIRED
    assert ref.artifact_path == RESULT_ARTIFACT_FILENAME
    assert ref.ref_id == manifest["comparison_definition_id"]
    assert ref.digest == manifest["integrity"]["content_sha256"]


def test_digest_matches_result_manifest_integrity(
    tmp_path: Path,
    ssot_durable_output_dir: Path,
) -> None:
    manifest_dir, manifest = _result_manifest_dir(tmp_path, ssot_durable_output_dir)
    ref = produce_comparison_lineage_ref_v1(manifest_dir=manifest_dir).ref
    assert ref.digest == manifest["integrity"]["content_sha256"]


def test_serialization_deterministic(
    tmp_path: Path,
    ssot_durable_output_dir: Path,
) -> None:
    manifest_dir, _manifest = _result_manifest_dir(tmp_path, ssot_durable_output_dir)
    ref = produce_comparison_lineage_ref_v1(manifest_dir=manifest_dir).ref
    first = serialize_comparison_lineage_ref_v1(ref)
    second = serialize_comparison_lineage_ref_v1(ref)
    assert first == second
    payload = json.loads(first)
    assert payload["ref_type"] == LineageRefType.COMPARISON.value
    assert payload["relation"] == LineageRelation.DERIVES_FROM_RESULT_MANIFEST.value


def test_no_promotion_authority_fields_in_output(
    tmp_path: Path,
    ssot_durable_output_dir: Path,
) -> None:
    manifest_dir, _manifest = _result_manifest_dir(tmp_path, ssot_durable_output_dir)
    ref = produce_comparison_lineage_ref_v1(manifest_dir=manifest_dir).ref
    payload = json.loads(serialize_comparison_lineage_ref_v1(ref))
    forbidden = {
        "promotion",
        "promotion_status",
        "winner",
        "selection",
        "acceptance",
        "completion",
        "runtime_status",
    }
    assert forbidden.isdisjoint(payload.keys())


def test_manifest_dir_symlink_rejected(tmp_path: Path) -> None:
    real_dir = tmp_path / "real"
    real_dir.mkdir()
    symlink = tmp_path / "link"
    symlink.symlink_to(real_dir, target_is_directory=True)
    with pytest.raises(ComparisonLineageRefProducerError, match="symlink"):
        produce_comparison_lineage_ref_v1(manifest_dir=symlink)


def test_result_manifest_symlink_rejected(
    tmp_path: Path,
    ssot_durable_output_dir: Path,
) -> None:
    manifest_dir, _manifest = _result_manifest_dir(tmp_path, ssot_durable_output_dir)
    manifest_path = manifest_dir / RESULT_ARTIFACT_FILENAME
    manifest_path.unlink()
    symlink = manifest_dir / RESULT_ARTIFACT_FILENAME
    symlink.symlink_to(tmp_path / "external.json")
    (tmp_path / "external.json").write_text("{}", encoding="utf-8")
    with pytest.raises(ComparisonLineageRefProducerError, match="symlink"):
        produce_comparison_lineage_ref_v1(manifest_dir=manifest_dir)


def test_missing_result_manifest_fail_closed(tmp_path: Path) -> None:
    manifest_dir = tmp_path / "empty"
    manifest_dir.mkdir()
    with pytest.raises(ComparisonLineageRefProducerError, match=RESULT_ARTIFACT_FILENAME):
        produce_comparison_lineage_ref_v1(manifest_dir=manifest_dir)


def test_invalid_result_manifest_fail_closed(
    tmp_path: Path,
    ssot_durable_output_dir: Path,
) -> None:
    manifest_dir, _manifest = _result_manifest_dir(tmp_path, ssot_durable_output_dir)
    manifest_path = manifest_dir / RESULT_ARTIFACT_FILENAME
    manifest_path.write_text('{"winner": "forbidden"}', encoding="utf-8")
    with pytest.raises(ComparisonLineageRefProducerError, match="validation failed"):
        produce_comparison_lineage_ref_v1(manifest_dir=manifest_dir)


def test_existing_output_fail_closed(
    tmp_path: Path,
    ssot_durable_output_dir: Path,
) -> None:
    manifest_dir, _manifest = _result_manifest_dir(tmp_path, ssot_durable_output_dir)
    output_path = tmp_path / "out.json"
    output_path.write_text('{"stale": true}', encoding="utf-8")
    with pytest.raises(ComparisonLineageRefProducerError, match="already exists"):
        produce_comparison_lineage_ref_v1_to_path(
            manifest_dir=manifest_dir,
            output_path=output_path,
        )
    assert output_path.read_text(encoding="utf-8") == '{"stale": true}'


def test_self_verification_roundtrip(
    tmp_path: Path,
    ssot_durable_output_dir: Path,
) -> None:
    manifest_dir, _manifest = _result_manifest_dir(tmp_path, ssot_durable_output_dir)
    ref = produce_comparison_lineage_ref_v1(manifest_dir=manifest_dir).ref
    output_path = tmp_path / "ref.json"
    write_comparison_lineage_ref_v1_atomic(ref, output_path)
    roundtrip = lineage_ref_from_mapping(json.loads(output_path.read_text(encoding="utf-8")))
    assert roundtrip == ref


def test_build_from_manifest_rejects_missing_definition_id(
    tmp_path: Path,
    ssot_durable_output_dir: Path,
) -> None:
    _, manifest = _result_manifest_dir(tmp_path, ssot_durable_output_dir)
    tampered = copy.deepcopy(manifest)
    del tampered["comparison_definition_id"]
    with pytest.raises(ComparisonLineageRefProducerError, match="comparison_definition_id"):
        build_comparison_lineage_ref_from_result_manifest(tampered)


def test_build_from_manifest_rejects_missing_digest(
    tmp_path: Path,
    ssot_durable_output_dir: Path,
) -> None:
    _, manifest = _result_manifest_dir(tmp_path, ssot_durable_output_dir)
    tampered = copy.deepcopy(manifest)
    tampered["integrity"] = {}
    with pytest.raises(ComparisonLineageRefProducerError, match="content_sha256"):
        build_comparison_lineage_ref_from_result_manifest(tampered)


def test_validate_result_manifest_v1_is_mandatory(
    tmp_path: Path,
    ssot_durable_output_dir: Path,
) -> None:
    manifest_dir, manifest = _result_manifest_dir(tmp_path, ssot_durable_output_dir)
    calls: list[dict[str, object]] = []
    original = validate_result_manifest_v1

    def _tracked_validate(payload):  # type: ignore[no-untyped-def]
        calls.append(dict(payload))
        return original(payload)

    with patch(
        "src.governance.promotion_loop.comparison_lineage_ref_producer_v1.validate_result_manifest_v1",
        side_effect=_tracked_validate,
    ):
        produce_comparison_lineage_ref_v1(manifest_dir=manifest_dir)
    assert calls
    assert calls[0]["comparison_definition_id"] == manifest["comparison_definition_id"]


def test_atomic_write_outside_tmp(
    tmp_path: Path,
    ssot_durable_output_dir: Path,
    lineage_ref_durable_output_dir: Callable[[], Path],
) -> None:
    manifest_dir, _manifest = _result_manifest_dir(tmp_path, ssot_durable_output_dir)
    output_path = lineage_ref_durable_output_dir() / "comparison_ref.json"
    produce_comparison_lineage_ref_v1_to_path(
        manifest_dir=manifest_dir,
        output_path=output_path,
    )
    assert output_path.is_file()


def test_non_writable_output_parent(
    tmp_path: Path,
    ssot_durable_output_dir: Path,
) -> None:
    manifest_dir, _manifest = _result_manifest_dir(tmp_path, ssot_durable_output_dir)
    ref = produce_comparison_lineage_ref_v1(manifest_dir=manifest_dir).ref
    readonly_dir = tmp_path / "readonly"
    readonly_dir.mkdir()
    output_path = readonly_dir / "out.json"
    os.chmod(readonly_dir, stat.S_IRUSR | stat.S_IXUSR)
    try:
        with pytest.raises(OSError):
            write_comparison_lineage_ref_v1_atomic(ref, output_path)
    finally:
        os.chmod(readonly_dir, stat.S_IRWXU)
    assert not output_path.exists()


def test_no_comparison_offline_reexecution(
    tmp_path: Path,
    ssot_durable_output_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest_dir, _manifest = _result_manifest_dir(tmp_path, ssot_durable_output_dir)

    def _forbidden(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("comparison offline producer forbidden")

    monkeypatch.setattr(
        "src.meta.learning_loop.comparison_ssot_v1.producer.produce_comparison_offline_v1",
        _forbidden,
    )
    produce_comparison_lineage_ref_v1(manifest_dir=manifest_dir)


def test_no_registry_or_mlflow_resolution(
    tmp_path: Path,
    ssot_durable_output_dir: Path,
) -> None:
    manifest_dir, _manifest = _result_manifest_dir(tmp_path, ssot_durable_output_dir)

    def _forbidden(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("registry or mlflow resolution forbidden")

    with patch("urllib.request.urlopen", side_effect=_forbidden):
        produce_comparison_lineage_ref_v1(manifest_dir=manifest_dir)


def test_lineage_ref_mapping_roundtrip(
    tmp_path: Path,
    ssot_durable_output_dir: Path,
) -> None:
    manifest_dir, _manifest = _result_manifest_dir(tmp_path, ssot_durable_output_dir)
    ref = produce_comparison_lineage_ref_v1(manifest_dir=manifest_dir).ref
    mapping = lineage_ref_to_mapping(ref)
    roundtrip = lineage_ref_from_mapping(mapping)
    assert roundtrip == ref
