"""Contract tests for comparison_ssot.v1 definition durable evidence binding."""

from __future__ import annotations

import ast
import json
import shutil
from copy import deepcopy
from pathlib import Path
import pytest

pytest_plugins = ["tests.meta.comparison_ssot_v1_fixtures"]

from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256
from src.meta.learning_loop.comparison_ssot_v1.constants import DEFINITION_ARTIFACT_FILENAME
from src.meta.learning_loop.comparison_ssot_v1.io import read_manifest
from src.meta.learning_loop.comparison_ssot_definition_durable_evidence_binding_v1 import (
    BINDING_RELATION,
    INDEX_ARTIFACT_REL,
    MANIFEST_ARTIFACT_REL,
    BoundArtifactRecord,
    ComparisonDefinitionBindingCrossReferences,
    ComparisonSsotDefinitionDurableEvidenceBindingError,
    build_binding_index_v1,
    check_reference_consistency,
    produce_comparison_ssot_definition_durable_evidence_bundle_v1,
    reverify_comparison_ssot_definition_durable_evidence_bundle_v1,
    serialize_binding_index_v1,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256
from tests.meta.comparison_ssot_v1_fixtures import produce_comparison_pair


@pytest.fixture(autouse=True)
def _allow_tmp_output(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "src.meta.learning_loop.comparison_ssot_definition_durable_evidence_binding_v1.is_under_tmp",
        lambda _path: False,
    )


def _durable_output(tmp_path: Path, name: str = "bundle") -> Path:
    root = tmp_path / "evidence_root"
    root.mkdir(exist_ok=True)
    return root / name


def _produce_definition_manifest(tmp_path, durable_root) -> tuple[Path, dict, str]:
    definition_path, _, comparison_definition_id = produce_comparison_pair(
        tmp_path,
        durable_root,
        ranking_rule_version="NONE_V1",
    )
    manifest = read_manifest(definition_path)
    return definition_path, manifest, comparison_definition_id


def test_happy_path_definition_binding(tmp_path, ssot_durable_output_dir) -> None:
    definition_path, manifest, comparison_definition_id = _produce_definition_manifest(
        tmp_path, ssot_durable_output_dir
    )
    out = _durable_output(tmp_path)
    result = produce_comparison_ssot_definition_durable_evidence_bundle_v1(
        manifest_path=definition_path,
        output_dir=out,
    )
    assert result.comparison_definition_id == comparison_definition_id
    assert (out / MANIFEST_ARTIFACT_REL).is_file()
    assert (out / INDEX_ARTIFACT_REL).is_file()
    ok, _ = verify_manifest_sha256(out)
    assert ok is True


def test_byte_identical_manifest_copy(tmp_path, ssot_durable_output_dir) -> None:
    definition_path, _, _ = _produce_definition_manifest(tmp_path, ssot_durable_output_dir)
    source_bytes = definition_path.read_bytes()
    out = _durable_output(tmp_path, "copy")
    produce_comparison_ssot_definition_durable_evidence_bundle_v1(
        manifest_path=definition_path,
        output_dir=out,
    )
    assert (out / MANIFEST_ARTIFACT_REL).read_bytes() == source_bytes


def test_input_refs_preserved_verbatim(tmp_path, ssot_durable_output_dir) -> None:
    definition_path, manifest, _ = _produce_definition_manifest(tmp_path, ssot_durable_output_dir)
    out = _durable_output(tmp_path, "refs")
    produce_comparison_ssot_definition_durable_evidence_bundle_v1(
        manifest_path=definition_path,
        output_dir=out,
    )
    index = json.loads((out / INDEX_ARTIFACT_REL).read_text(encoding="utf-8"))
    assert index["definition_input_refs"] == manifest["input_refs"]


def test_input_ref_ordering_preserved(tmp_path, ssot_durable_output_dir) -> None:
    definition_path, manifest, _ = _produce_definition_manifest(tmp_path, ssot_durable_output_dir)
    out = _durable_output(tmp_path, "order")
    produce_comparison_ssot_definition_durable_evidence_bundle_v1(
        manifest_path=definition_path,
        output_dir=out,
    )
    index = json.loads((out / INDEX_ARTIFACT_REL).read_text(encoding="utf-8"))
    assert [ref["ref_id"] for ref in index["definition_input_refs"]] == [
        ref["ref_id"] for ref in manifest["input_refs"]
    ]


def test_policy_config_preserved_verbatim(tmp_path, ssot_durable_output_dir) -> None:
    definition_path, manifest, _ = _produce_definition_manifest(tmp_path, ssot_durable_output_dir)
    out = _durable_output(tmp_path, "policy")
    produce_comparison_ssot_definition_durable_evidence_bundle_v1(
        manifest_path=definition_path,
        output_dir=out,
    )
    index = json.loads((out / INDEX_ARTIFACT_REL).read_text(encoding="utf-8"))
    assert index["policy_config_ref"]["ranking_rule_version"] == manifest["ranking_rule_version"]
    assert index["policy_config_ref"]["tie_rule_version"] == manifest["tie_rule_version"]


def test_binding_index_metadata_only(tmp_path, ssot_durable_output_dir) -> None:
    definition_path, _, _ = _produce_definition_manifest(tmp_path, ssot_durable_output_dir)
    out = _durable_output(tmp_path, "meta")
    produce_comparison_ssot_definition_durable_evidence_bundle_v1(
        manifest_path=definition_path,
        output_dir=out,
    )
    index = json.loads((out / INDEX_ARTIFACT_REL).read_text(encoding="utf-8"))
    assert index["evidence_does_not_authorize_runtime"] is True
    assert index["binding_relation"] == BINDING_RELATION
    assert "winner" not in index
    assert "selection" not in index
    assert all(not Path(item["relative_path"]).is_absolute() for item in index["artifacts"])


def test_reverify_without_raw_data(tmp_path, ssot_durable_output_dir) -> None:
    definition_path, _, _ = _produce_definition_manifest(tmp_path, ssot_durable_output_dir)
    out = _durable_output(tmp_path, "replay")
    produce_comparison_ssot_definition_durable_evidence_bundle_v1(
        manifest_path=definition_path,
        output_dir=out,
    )
    reverify_comparison_ssot_definition_durable_evidence_bundle_v1(output_dir=out)


def test_deterministic_index_and_manifest(tmp_path, ssot_durable_output_dir) -> None:
    definition_path, _, _ = _produce_definition_manifest(tmp_path, ssot_durable_output_dir)
    out1 = _durable_output(tmp_path, "det1")
    out2 = _durable_output(tmp_path, "det2")
    produce_comparison_ssot_definition_durable_evidence_bundle_v1(
        manifest_path=definition_path,
        output_dir=out1,
    )
    produce_comparison_ssot_definition_durable_evidence_bundle_v1(
        manifest_path=definition_path,
        output_dir=out2,
    )
    assert (out1 / INDEX_ARTIFACT_REL).read_bytes() == (out2 / INDEX_ARTIFACT_REL).read_bytes()
    assert (out1 / "MANIFEST.sha256").read_bytes() == (out2 / "MANIFEST.sha256").read_bytes()


def test_missing_manifest_fail_closed(tmp_path) -> None:
    out = _durable_output(tmp_path, "missing")
    with pytest.raises(ComparisonSsotDefinitionDurableEvidenceBindingError, match="not found"):
        produce_comparison_ssot_definition_durable_evidence_bundle_v1(
            manifest_path=tmp_path / "missing.json",
            output_dir=out,
        )


def test_wrong_manifest_filename_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    definition_path, _, _ = _produce_definition_manifest(tmp_path, ssot_durable_output_dir)
    bad_path = definition_path.parent / "wrong_name.json"
    bad_path.write_text(definition_path.read_text(encoding="utf-8"), encoding="utf-8")
    out = _durable_output(tmp_path, "badname")
    with pytest.raises(ComparisonSsotDefinitionDurableEvidenceBindingError, match="filename"):
        produce_comparison_ssot_definition_durable_evidence_bundle_v1(
            manifest_path=bad_path,
            output_dir=out,
        )


def test_existing_output_dir_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    definition_path, _, _ = _produce_definition_manifest(tmp_path, ssot_durable_output_dir)
    out = _durable_output(tmp_path, "exists")
    out.mkdir(parents=True)
    with pytest.raises(ComparisonSsotDefinitionDurableEvidenceBindingError, match="already exists"):
        produce_comparison_ssot_definition_durable_evidence_bundle_v1(
            manifest_path=definition_path,
            output_dir=out,
        )


def test_symlink_manifest_rejected(tmp_path, ssot_durable_output_dir) -> None:
    definition_path, _, _ = _produce_definition_manifest(tmp_path, ssot_durable_output_dir)
    link = tmp_path / "manifest_link.json"
    link.symlink_to(definition_path)
    out = _durable_output(tmp_path, "symlink")
    with pytest.raises(ComparisonSsotDefinitionDurableEvidenceBindingError, match="symlink"):
        produce_comparison_ssot_definition_durable_evidence_bundle_v1(
            manifest_path=link,
            output_dir=out,
        )


def test_id_mismatch_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    definition_path, manifest, _ = _produce_definition_manifest(tmp_path, ssot_durable_output_dir)
    payload = deepcopy(dict(manifest))
    payload["comparison_definition_id"] = "0" * 64
    tampered = definition_path.parent / "tampered.json"
    tampered.write_text(json.dumps(payload), encoding="utf-8")
    out = _durable_output(tmp_path, "idmismatch")
    with pytest.raises(ComparisonSsotDefinitionDurableEvidenceBindingError):
        produce_comparison_ssot_definition_durable_evidence_bundle_v1(
            manifest_path=tampered,
            output_dir=out,
        )


def test_digest_mismatch_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    definition_path, manifest, _ = _produce_definition_manifest(tmp_path, ssot_durable_output_dir)
    payload = deepcopy(dict(manifest))
    payload["integrity"]["content_sha256"] = "0" * 64
    tampered = definition_path.parent / "digest_tampered.json"
    tampered.write_text(json.dumps(payload), encoding="utf-8")
    out = _durable_output(tmp_path, "digest")
    with pytest.raises(ComparisonSsotDefinitionDurableEvidenceBindingError):
        produce_comparison_ssot_definition_durable_evidence_bundle_v1(
            manifest_path=tampered,
            output_dir=out,
        )


def test_copy_failure_cleans_up(
    tmp_path, ssot_durable_output_dir, monkeypatch: pytest.MonkeyPatch
) -> None:
    definition_path, _, _ = _produce_definition_manifest(tmp_path, ssot_durable_output_dir)
    out = _durable_output(tmp_path, "copyfail")

    def _boom(_src: Path, _dst: Path) -> str:
        raise OSError("copy failed")

    monkeypatch.setattr(
        "src.meta.learning_loop.comparison_ssot_definition_durable_evidence_binding_v1._copy_byte_identical",
        _boom,
    )
    with pytest.raises(OSError, match="copy failed"):
        produce_comparison_ssot_definition_durable_evidence_bundle_v1(
            manifest_path=definition_path,
            output_dir=out,
        )
    assert not out.exists()


def test_manifest_verify_failure_cleans_up(
    tmp_path, ssot_durable_output_dir, monkeypatch: pytest.MonkeyPatch
) -> None:
    definition_path, _, _ = _produce_definition_manifest(tmp_path, ssot_durable_output_dir)
    out = _durable_output(tmp_path, "manifestfail")
    monkeypatch.setattr(
        "src.meta.learning_loop.comparison_ssot_definition_durable_evidence_binding_v1.verify_manifest_sha256",
        lambda _root: (False, "checksum mismatch"),
    )
    with pytest.raises(
        ComparisonSsotDefinitionDurableEvidenceBindingError, match="verification failed"
    ):
        produce_comparison_ssot_definition_durable_evidence_bundle_v1(
            manifest_path=definition_path,
            output_dir=out,
        )
    assert not out.exists()


def test_build_binding_index_rejects_forbidden_key(tmp_path, ssot_durable_output_dir) -> None:
    _, manifest, _ = _produce_definition_manifest(tmp_path, ssot_durable_output_dir)
    cross = check_reference_consistency(manifest)
    artifacts = (
        BoundArtifactRecord(
            artifact_kind="comparison_definition_manifest_v1",
            relative_path=MANIFEST_ARTIFACT_REL,
            content_sha256="a" * 64,
        ),
    )
    index = build_binding_index_v1(
        manifest=manifest,
        cross_references=cross,
        artifacts=artifacts,
    )
    index["winner"] = "candidate-a"
    with pytest.raises(ComparisonSsotDefinitionDurableEvidenceBindingError, match="forbidden key"):
        serialize_binding_index_v1(index)


def test_integrity_hash_stable_for_index_payload(tmp_path, ssot_durable_output_dir) -> None:
    _, manifest, _ = _produce_definition_manifest(tmp_path, ssot_durable_output_dir)
    cross = check_reference_consistency(manifest)
    artifacts = (
        BoundArtifactRecord(
            artifact_kind="comparison_definition_manifest_v1",
            relative_path=MANIFEST_ARTIFACT_REL,
            content_sha256=cross.manifest_content_sha256,
        ),
    )
    index = build_binding_index_v1(
        manifest=manifest,
        cross_references=cross,
        artifacts=artifacts,
    )
    payload = dict(index)
    digest = payload.pop("integrity")
    assert digest["content_sha256"] == compute_content_sha256(payload)


def test_output_under_tmp_rejected(
    tmp_path, ssot_durable_output_dir, monkeypatch: pytest.MonkeyPatch
) -> None:
    from scripts.ops.primary_evidence_retention_v0 import is_under_tmp as real_is_under_tmp

    monkeypatch.setattr(
        "src.meta.learning_loop.comparison_ssot_definition_durable_evidence_binding_v1.is_under_tmp",
        real_is_under_tmp,
    )
    definition_path, _, _ = _produce_definition_manifest(tmp_path, ssot_durable_output_dir)
    out = Path("/tmp/peak_trade_cmp_definition_binding_reject_test")
    try:
        with pytest.raises(
            ComparisonSsotDefinitionDurableEvidenceBindingError, match="outside /tmp"
        ):
            produce_comparison_ssot_definition_durable_evidence_bundle_v1(
                manifest_path=definition_path,
                output_dir=out,
            )
    finally:
        if out.exists():
            shutil.rmtree(out)


def test_no_runtime_imports_in_binding_module() -> None:
    path = Path("src/meta/learning_loop/comparison_ssot_definition_durable_evidence_binding_v1.py")
    tree = ast.parse(path.read_text(encoding="utf-8"))
    forbidden = ("promotion_loop.engine", "governance.promotion_loop.engine")
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            for token in forbidden:
                assert token not in node.module


def test_reverify_detects_tampered_index(tmp_path, ssot_durable_output_dir) -> None:
    definition_path, _, _ = _produce_definition_manifest(tmp_path, ssot_durable_output_dir)
    out = _durable_output(tmp_path, "tamper")
    produce_comparison_ssot_definition_durable_evidence_bundle_v1(
        manifest_path=definition_path,
        output_dir=out,
    )
    index_path = out / INDEX_ARTIFACT_REL
    payload = json.loads(index_path.read_text(encoding="utf-8"))
    payload["definition_input_refs"][0]["ref_id"] = "tampered"
    index_path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(
        ComparisonSsotDefinitionDurableEvidenceBindingError, match="MANIFEST.sha256"
    ):
        reverify_comparison_ssot_definition_durable_evidence_bundle_v1(output_dir=out)


def test_check_reference_consistency_requires_valid_id(tmp_path, ssot_durable_output_dir) -> None:
    _, manifest, _ = _produce_definition_manifest(tmp_path, ssot_durable_output_dir)
    bad = dict(manifest)
    bad.pop("comparison_definition_id")
    with pytest.raises(
        ComparisonSsotDefinitionDurableEvidenceBindingError, match="comparison_definition_id"
    ):
        check_reference_consistency(bad)


def test_binding_preserves_id_and_digest_verbatim(tmp_path, ssot_durable_output_dir) -> None:
    definition_path, manifest, comparison_definition_id = _produce_definition_manifest(
        tmp_path, ssot_durable_output_dir
    )
    out = _durable_output(tmp_path, "verbatim")
    result = produce_comparison_ssot_definition_durable_evidence_bundle_v1(
        manifest_path=definition_path,
        output_dir=out,
    )
    assert result.comparison_definition_id == comparison_definition_id
    bound_manifest = json.loads((out / MANIFEST_ARTIFACT_REL).read_text(encoding="utf-8"))
    assert bound_manifest["comparison_definition_id"] == comparison_definition_id
    assert bound_manifest["integrity"]["content_sha256"] == manifest["integrity"]["content_sha256"]


def test_binding_does_not_read_metric_inputs_or_raw_sources(
    tmp_path, ssot_durable_output_dir, monkeypatch
) -> None:
    definition_path, _, _ = _produce_definition_manifest(tmp_path, ssot_durable_output_dir)
    out = _durable_output(tmp_path, "noraw")

    original_read_bytes = Path.read_bytes

    def _tracked_read_bytes(self: Path) -> bytes:
        if self.name == "comparison_metric_input_manifest_v1.json":
            raise AssertionError("metric input read forbidden during definition binding")
        if self.suffix in {".csv", ".parquet"} or self.name == "run_summary.json":
            raise AssertionError("raw source read forbidden during definition binding")
        return original_read_bytes(self)

    monkeypatch.setattr(Path, "read_bytes", _tracked_read_bytes)
    produce_comparison_ssot_definition_durable_evidence_bundle_v1(
        manifest_path=definition_path,
        output_dir=out,
    )


def test_index_cross_references_match_manifest(tmp_path, ssot_durable_output_dir) -> None:
    definition_path, manifest, comparison_definition_id = _produce_definition_manifest(
        tmp_path, ssot_durable_output_dir
    )
    out = _durable_output(tmp_path, "cross")
    produce_comparison_ssot_definition_durable_evidence_bundle_v1(
        manifest_path=definition_path,
        output_dir=out,
    )
    index = json.loads((out / INDEX_ARTIFACT_REL).read_text(encoding="utf-8"))
    cross = index["cross_references"]
    assert cross["comparison_definition_id"] == comparison_definition_id
    assert cross["manifest_content_sha256"] == manifest["integrity"]["content_sha256"]


def test_definition_manifest_filename_constant() -> None:
    assert MANIFEST_ARTIFACT_REL == DEFINITION_ARTIFACT_FILENAME


def test_check_reference_consistency_cross_fields(tmp_path, ssot_durable_output_dir) -> None:
    _, manifest, comparison_definition_id = _produce_definition_manifest(
        tmp_path, ssot_durable_output_dir
    )
    cross = check_reference_consistency(manifest)
    assert cross.comparison_definition_id == comparison_definition_id
    assert cross.manifest_content_sha256 == manifest["integrity"]["content_sha256"]


def test_reverify_binding_relation_mismatch(tmp_path, ssot_durable_output_dir) -> None:
    definition_path, _, _ = _produce_definition_manifest(tmp_path, ssot_durable_output_dir)
    out = _durable_output(tmp_path, "rel")
    produce_comparison_ssot_definition_durable_evidence_bundle_v1(
        manifest_path=definition_path,
        output_dir=out,
    )
    index_path = out / INDEX_ARTIFACT_REL
    payload = json.loads(index_path.read_text(encoding="utf-8"))
    payload["binding_relation"] = "WRONG_RELATION"
    index_path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ComparisonSsotDefinitionDurableEvidenceBindingError):
        reverify_comparison_ssot_definition_durable_evidence_bundle_v1(output_dir=out)


def test_build_binding_index_type(tmp_path, ssot_durable_output_dir) -> None:
    _, manifest, _ = _produce_definition_manifest(tmp_path, ssot_durable_output_dir)
    cross = ComparisonDefinitionBindingCrossReferences(
        comparison_definition_id=str(manifest["comparison_definition_id"]),
        manifest_content_sha256=str(manifest["integrity"]["content_sha256"]),
    )
    index = build_binding_index_v1(
        manifest=manifest,
        cross_references=cross,
        artifacts=(
            BoundArtifactRecord(
                artifact_kind="comparison_definition_manifest_v1",
                relative_path=MANIFEST_ARTIFACT_REL,
                content_sha256=cross.manifest_content_sha256,
            ),
        ),
    )
    assert index["schema_version"] == "comparison_ssot_definition_durable_evidence_binding_v1"
    assert index["bound_contract"] == "comparison_ssot.v1"
