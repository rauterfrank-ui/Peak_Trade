"""Contract tests for comparison_metric_input.v1 durable evidence binding."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256
from src.meta.learning_loop.comparison_metric_input_v1.constants import ARTIFACT_FILENAME
from src.meta.learning_loop.comparison_metric_input_v1.producer import (
    produce_comparison_metric_input_v1,
)
from src.meta.learning_loop.comparison_metric_input_durable_evidence_binding_v1 import (
    BINDING_RELATION,
    INDEX_ARTIFACT_REL,
    MANIFEST_ARTIFACT_REL,
    BoundArtifactRecord,
    ComparisonMetricInputBindingCrossReferences,
    ComparisonMetricInputDurableEvidenceBindingError,
    build_binding_index_v1,
    check_reference_consistency,
    produce_comparison_metric_input_durable_evidence_bundle_v1,
    reverify_comparison_metric_input_durable_evidence_bundle_v1,
    serialize_binding_index_v1,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256
from tests.meta.comparison_metric_input_v1_fixtures import (
    build_backtest_run_dir,
    build_experiment_bundle,
    build_var_suite_bundle,
)


@pytest.fixture(autouse=True)
def _allow_tmp_output(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "src.meta.learning_loop.comparison_metric_input_durable_evidence_binding_v1.is_under_tmp",
        lambda _path: False,
    )


def _durable_output(tmp_path: Path, name: str = "bundle") -> Path:
    root = tmp_path / "evidence_root"
    root.mkdir(exist_ok=True)
    return root / name


def _produce_manifest(tmp_path, durable_output_dir, *, domain: str = "BACKTEST"):
    if domain == "BACKTEST":
        run_dir, ref = build_backtest_run_dir(tmp_path)
        result = produce_comparison_metric_input_v1(
            source_domain="BACKTEST",
            output_root=durable_output_dir,
            source_ref=ref,
            run_dir=run_dir,
        )
        return result
    if domain == "EXPERIMENT":
        completed_dir, _ = build_backtest_run_dir(tmp_path / "completed")
        manifest_dir, exp_ref, completed = build_experiment_bundle(tmp_path, completed_dir)
        return produce_comparison_metric_input_v1(
            source_domain="EXPERIMENT",
            output_root=durable_output_dir,
            source_ref=exp_ref,
            manifest_dir=manifest_dir,
            completed_run_dir=completed,
        )
    if domain == "VAR_SUITE":
        run_dir, backtest_ref = build_backtest_run_dir(tmp_path)
        suite_dir, var_ref, _ = build_var_suite_bundle(
            tmp_path,
            companion_run_dir=run_dir,
            backtest_ref=backtest_ref,
        )
        return produce_comparison_metric_input_v1(
            source_domain="VAR_SUITE",
            output_root=durable_output_dir,
            source_ref=var_ref,
            suite_report_dir=suite_dir,
            companion_run_dir=run_dir,
            backtest_source_ref=backtest_ref,
        )
    raise AssertionError(f"unsupported domain: {domain}")


def test_happy_path_backtest_binding(tmp_path, durable_output_dir) -> None:
    produced = _produce_manifest(tmp_path, durable_output_dir, domain="BACKTEST")
    out = _durable_output(tmp_path)
    result = produce_comparison_metric_input_durable_evidence_bundle_v1(
        manifest_path=produced.manifest_path,
        output_dir=out,
    )
    assert result.comparison_metric_input_id == produced.comparison_metric_input_id
    assert (out / MANIFEST_ARTIFACT_REL).is_file()
    assert (out / INDEX_ARTIFACT_REL).is_file()
    ok, _ = verify_manifest_sha256(out)
    assert ok is True


def test_happy_path_experiment_binding(tmp_path, durable_output_dir) -> None:
    produced = _produce_manifest(tmp_path, durable_output_dir, domain="EXPERIMENT")
    out = _durable_output(tmp_path, "exp")
    produce_comparison_metric_input_durable_evidence_bundle_v1(
        manifest_path=produced.manifest_path,
        output_dir=out,
    )
    index = json.loads((out / INDEX_ARTIFACT_REL).read_text(encoding="utf-8"))
    assert index["source_domain"] == "EXPERIMENT"
    assert index["binding_relation"] == BINDING_RELATION


def test_happy_path_var_suite_binding_preserves_companion(tmp_path, durable_output_dir) -> None:
    produced = _produce_manifest(tmp_path, durable_output_dir, domain="VAR_SUITE")
    out = _durable_output(tmp_path, "var")
    produce_comparison_metric_input_durable_evidence_bundle_v1(
        manifest_path=produced.manifest_path,
        output_dir=out,
    )
    index = json.loads((out / INDEX_ARTIFACT_REL).read_text(encoding="utf-8"))
    assert index["var_suite_companion"] == produced.manifest["var_suite_companion"]


def test_byte_identical_manifest_copy(tmp_path, durable_output_dir) -> None:
    produced = _produce_manifest(tmp_path, durable_output_dir)
    source_bytes = produced.manifest_path.read_bytes()
    out = _durable_output(tmp_path, "copy")
    produce_comparison_metric_input_durable_evidence_bundle_v1(
        manifest_path=produced.manifest_path,
        output_dir=out,
    )
    assert (out / MANIFEST_ARTIFACT_REL).read_bytes() == source_bytes


def test_source_ref_preserved_verbatim(tmp_path, durable_output_dir) -> None:
    produced = _produce_manifest(tmp_path, durable_output_dir)
    out = _durable_output(tmp_path, "ref")
    produce_comparison_metric_input_durable_evidence_bundle_v1(
        manifest_path=produced.manifest_path,
        output_dir=out,
    )
    index = json.loads((out / INDEX_ARTIFACT_REL).read_text(encoding="utf-8"))
    assert index["comparison_metric_input_source_ref"] == produced.manifest["source_ref"]


def test_binding_index_metadata_only(tmp_path, durable_output_dir) -> None:
    produced = _produce_manifest(tmp_path, durable_output_dir)
    out = _durable_output(tmp_path, "meta")
    produce_comparison_metric_input_durable_evidence_bundle_v1(
        manifest_path=produced.manifest_path,
        output_dir=out,
    )
    index = json.loads((out / INDEX_ARTIFACT_REL).read_text(encoding="utf-8"))
    assert index["evidence_does_not_authorize_runtime"] is True
    assert "metrics" not in index
    assert "promotion_authority" not in index
    assert all(not Path(item["relative_path"]).is_absolute() for item in index["artifacts"])


def test_reverify_without_raw_data(tmp_path, durable_output_dir) -> None:
    produced = _produce_manifest(tmp_path, durable_output_dir)
    out = _durable_output(tmp_path, "replay")
    produce_comparison_metric_input_durable_evidence_bundle_v1(
        manifest_path=produced.manifest_path,
        output_dir=out,
    )
    reverify_comparison_metric_input_durable_evidence_bundle_v1(output_dir=out)


def test_deterministic_index_and_manifest(tmp_path, durable_output_dir) -> None:
    produced = _produce_manifest(tmp_path, durable_output_dir)
    out1 = _durable_output(tmp_path, "det1")
    out2 = _durable_output(tmp_path, "det2")
    produce_comparison_metric_input_durable_evidence_bundle_v1(
        manifest_path=produced.manifest_path,
        output_dir=out1,
    )
    produce_comparison_metric_input_durable_evidence_bundle_v1(
        manifest_path=produced.manifest_path,
        output_dir=out2,
    )
    assert (out1 / INDEX_ARTIFACT_REL).read_bytes() == (out2 / INDEX_ARTIFACT_REL).read_bytes()
    assert (out1 / "MANIFEST.sha256").read_bytes() == (out2 / "MANIFEST.sha256").read_bytes()


def test_missing_manifest_fail_closed(tmp_path) -> None:
    out = _durable_output(tmp_path, "missing")
    with pytest.raises(ComparisonMetricInputDurableEvidenceBindingError, match="not found"):
        produce_comparison_metric_input_durable_evidence_bundle_v1(
            manifest_path=tmp_path / "missing.json",
            output_dir=out,
        )


def test_wrong_manifest_filename_fail_closed(tmp_path, durable_output_dir) -> None:
    produced = _produce_manifest(tmp_path, durable_output_dir)
    bad_path = produced.manifest_path.parent / "wrong_name.json"
    bad_path.write_text(produced.manifest_path.read_text(encoding="utf-8"), encoding="utf-8")
    out = _durable_output(tmp_path, "badname")
    with pytest.raises(ComparisonMetricInputDurableEvidenceBindingError, match="filename"):
        produce_comparison_metric_input_durable_evidence_bundle_v1(
            manifest_path=bad_path,
            output_dir=out,
        )


def test_existing_output_dir_fail_closed(tmp_path, durable_output_dir) -> None:
    produced = _produce_manifest(tmp_path, durable_output_dir)
    out = _durable_output(tmp_path, "exists")
    out.mkdir(parents=True)
    with pytest.raises(ComparisonMetricInputDurableEvidenceBindingError, match="already exists"):
        produce_comparison_metric_input_durable_evidence_bundle_v1(
            manifest_path=produced.manifest_path,
            output_dir=out,
        )


def test_symlink_manifest_rejected(tmp_path, durable_output_dir) -> None:
    produced = _produce_manifest(tmp_path, durable_output_dir)
    link = tmp_path / "manifest_link.json"
    link.symlink_to(produced.manifest_path)
    out = _durable_output(tmp_path, "symlink")
    with pytest.raises(ComparisonMetricInputDurableEvidenceBindingError, match="symlink"):
        produce_comparison_metric_input_durable_evidence_bundle_v1(
            manifest_path=link,
            output_dir=out,
        )


def test_id_mismatch_fail_closed(tmp_path, durable_output_dir) -> None:
    produced = _produce_manifest(tmp_path, durable_output_dir)
    payload = json.loads(produced.manifest_path.read_text(encoding="utf-8"))
    payload["comparison_metric_input_id"] = "0" * 64
    tampered = produced.manifest_path.parent / "tampered.json"
    tampered.write_text(json.dumps(payload), encoding="utf-8")
    out = _durable_output(tmp_path, "idmismatch")
    with pytest.raises(ComparisonMetricInputDurableEvidenceBindingError):
        produce_comparison_metric_input_durable_evidence_bundle_v1(
            manifest_path=tampered,
            output_dir=out,
        )


def test_digest_mismatch_fail_closed(tmp_path, durable_output_dir) -> None:
    produced = _produce_manifest(tmp_path, durable_output_dir)
    payload = json.loads(produced.manifest_path.read_text(encoding="utf-8"))
    payload["integrity"]["content_sha256"] = "0" * 64
    tampered = produced.manifest_path.parent / "digest_tampered.json"
    tampered.write_text(json.dumps(payload), encoding="utf-8")
    out = _durable_output(tmp_path, "digest")
    with pytest.raises(ComparisonMetricInputDurableEvidenceBindingError):
        produce_comparison_metric_input_durable_evidence_bundle_v1(
            manifest_path=tampered,
            output_dir=out,
        )


def test_var_suite_without_companion_fail_closed(tmp_path, durable_output_dir) -> None:
    produced = _produce_manifest(tmp_path, durable_output_dir, domain="VAR_SUITE")
    payload = json.loads(produced.manifest_path.read_text(encoding="utf-8"))
    payload.pop("var_suite_companion")
    tampered = produced.manifest_path.parent / "no_companion.json"
    tampered.write_text(json.dumps(payload), encoding="utf-8")
    out = _durable_output(tmp_path, "nocomp")
    with pytest.raises(ComparisonMetricInputDurableEvidenceBindingError):
        produce_comparison_metric_input_durable_evidence_bundle_v1(
            manifest_path=tampered,
            output_dir=out,
        )


def test_copy_failure_cleans_up(
    tmp_path, durable_output_dir, monkeypatch: pytest.MonkeyPatch
) -> None:
    produced = _produce_manifest(tmp_path, durable_output_dir)
    out = _durable_output(tmp_path, "copyfail")

    def _boom(_src: Path, _dst: Path) -> str:
        raise OSError("copy failed")

    monkeypatch.setattr(
        "src.meta.learning_loop.comparison_metric_input_durable_evidence_binding_v1._copy_byte_identical",
        _boom,
    )
    with pytest.raises(OSError, match="copy failed"):
        produce_comparison_metric_input_durable_evidence_bundle_v1(
            manifest_path=produced.manifest_path,
            output_dir=out,
        )
    assert not out.exists()


def test_manifest_verify_failure_cleans_up(
    tmp_path, durable_output_dir, monkeypatch: pytest.MonkeyPatch
) -> None:
    produced = _produce_manifest(tmp_path, durable_output_dir)
    out = _durable_output(tmp_path, "manifestfail")
    monkeypatch.setattr(
        "src.meta.learning_loop.comparison_metric_input_durable_evidence_binding_v1.verify_manifest_sha256",
        lambda _root: (False, "checksum mismatch"),
    )
    with pytest.raises(
        ComparisonMetricInputDurableEvidenceBindingError, match="verification failed"
    ):
        produce_comparison_metric_input_durable_evidence_bundle_v1(
            manifest_path=produced.manifest_path,
            output_dir=out,
        )
    assert not out.exists()


def test_build_binding_index_rejects_forbidden_key(tmp_path, durable_output_dir) -> None:
    produced = _produce_manifest(tmp_path, durable_output_dir)
    manifest = produced.manifest
    cross = check_reference_consistency(manifest)
    artifacts = (
        BoundArtifactRecord(
            artifact_kind="comparison_metric_input_manifest_v1",
            relative_path=MANIFEST_ARTIFACT_REL,
            content_sha256="a" * 64,
        ),
    )
    index = build_binding_index_v1(
        manifest=manifest,
        cross_references=cross,
        artifacts=artifacts,
    )
    index["metrics"] = {"sharpe": 1.0}
    with pytest.raises(ComparisonMetricInputDurableEvidenceBindingError, match="forbidden key"):
        serialize_binding_index_v1(index)


def test_integrity_hash_stable_for_index_payload(tmp_path, durable_output_dir) -> None:
    produced = _produce_manifest(tmp_path, durable_output_dir)
    cross = check_reference_consistency(produced.manifest)
    artifacts = (
        BoundArtifactRecord(
            artifact_kind="comparison_metric_input_manifest_v1",
            relative_path=MANIFEST_ARTIFACT_REL,
            content_sha256=cross.manifest_content_sha256,
        ),
    )
    index = build_binding_index_v1(
        manifest=produced.manifest,
        cross_references=cross,
        artifacts=artifacts,
    )
    payload = dict(index)
    digest = payload.pop("integrity")
    assert digest["content_sha256"] == compute_content_sha256(payload)


def test_output_under_tmp_rejected(
    tmp_path, durable_output_dir, monkeypatch: pytest.MonkeyPatch
) -> None:
    from scripts.ops.primary_evidence_retention_v0 import is_under_tmp as real_is_under_tmp

    monkeypatch.setattr(
        "src.meta.learning_loop.comparison_metric_input_durable_evidence_binding_v1.is_under_tmp",
        real_is_under_tmp,
    )
    produced = _produce_manifest(tmp_path, durable_output_dir)
    out = Path("/tmp/peak_trade_cmp_metric_binding_reject_test")
    try:
        with pytest.raises(ComparisonMetricInputDurableEvidenceBindingError, match="outside /tmp"):
            produce_comparison_metric_input_durable_evidence_bundle_v1(
                manifest_path=produced.manifest_path,
                output_dir=out,
            )
    finally:
        if out.exists():
            shutil.rmtree(out)


def test_no_runtime_imports_in_binding_module() -> None:
    import ast

    path = Path("src/meta/learning_loop/comparison_metric_input_durable_evidence_binding_v1.py")
    tree = ast.parse(path.read_text(encoding="utf-8"))
    forbidden = ("promotion_loop.engine", "governance.promotion_loop.engine")
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            for token in forbidden:
                assert token not in node.module


def test_reverify_detects_tampered_index(tmp_path, durable_output_dir) -> None:
    produced = _produce_manifest(tmp_path, durable_output_dir)
    out = _durable_output(tmp_path, "tamper")
    produce_comparison_metric_input_durable_evidence_bundle_v1(
        manifest_path=produced.manifest_path,
        output_dir=out,
    )
    index_path = out / INDEX_ARTIFACT_REL
    payload = json.loads(index_path.read_text(encoding="utf-8"))
    payload["comparison_metric_input_source_ref"]["ref_id"] = "tampered"
    index_path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ComparisonMetricInputDurableEvidenceBindingError, match="MANIFEST.sha256"):
        reverify_comparison_metric_input_durable_evidence_bundle_v1(output_dir=out)


def test_check_reference_consistency_requires_valid_id(tmp_path, durable_output_dir) -> None:
    produced = _produce_manifest(tmp_path, durable_output_dir)
    manifest = dict(produced.manifest)
    manifest.pop("comparison_metric_input_id")
    with pytest.raises(
        ComparisonMetricInputDurableEvidenceBindingError, match="comparison_metric_input_id"
    ):
        check_reference_consistency(manifest)


def test_check_reference_consistency_cross_fields(tmp_path, durable_output_dir) -> None:
    produced = _produce_manifest(tmp_path, durable_output_dir)
    cross = check_reference_consistency(produced.manifest)
    assert cross.comparison_metric_input_id == produced.comparison_metric_input_id
    assert cross.manifest_content_sha256 == produced.manifest["integrity"]["content_sha256"]
    assert cross.source_ref_id == produced.manifest["source_ref"]["ref_id"]


def test_binding_preserves_id_and_digest_verbatim(tmp_path, durable_output_dir) -> None:
    produced = _produce_manifest(tmp_path, durable_output_dir)
    out = _durable_output(tmp_path, "verbatim")
    result = produce_comparison_metric_input_durable_evidence_bundle_v1(
        manifest_path=produced.manifest_path,
        output_dir=out,
    )
    assert result.comparison_metric_input_id == produced.comparison_metric_input_id
    bound_manifest = json.loads((out / MANIFEST_ARTIFACT_REL).read_text(encoding="utf-8"))
    assert bound_manifest["comparison_metric_input_id"] == produced.comparison_metric_input_id
    assert (
        bound_manifest["integrity"]["content_sha256"]
        == produced.manifest["integrity"]["content_sha256"]
    )


def test_binding_does_not_read_raw_sources(tmp_path, durable_output_dir, monkeypatch) -> None:
    produced = _produce_manifest(tmp_path, durable_output_dir)
    out = _durable_output(tmp_path, "noraw")

    original_read_bytes = Path.read_bytes

    def _tracked_read_bytes(self: Path) -> bytes:
        if self.suffix in {".csv", ".parquet"} or self.name == "run_summary.json":
            raise AssertionError("raw source read forbidden during binding")
        return original_read_bytes(self)

    monkeypatch.setattr(Path, "read_bytes", _tracked_read_bytes)
    produce_comparison_metric_input_durable_evidence_bundle_v1(
        manifest_path=produced.manifest_path,
        output_dir=out,
    )


def test_index_cross_references_match_manifest(tmp_path, durable_output_dir) -> None:
    produced = _produce_manifest(tmp_path, durable_output_dir)
    out = _durable_output(tmp_path, "cross")
    produce_comparison_metric_input_durable_evidence_bundle_v1(
        manifest_path=produced.manifest_path,
        output_dir=out,
    )
    index = json.loads((out / INDEX_ARTIFACT_REL).read_text(encoding="utf-8"))
    cross = index["cross_references"]
    assert cross["comparison_metric_input_id"] == produced.comparison_metric_input_id
    assert cross["manifest_content_sha256"] == produced.manifest["integrity"]["content_sha256"]
    assert cross["source_ref_id"] == produced.manifest["source_ref"]["ref_id"]
    assert cross["source_ref_digest"] == produced.manifest["source_ref"]["digest"]
