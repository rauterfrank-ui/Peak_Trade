"""Contract tests for Package K offline VAR_SUITE durable evidence binding v1."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256
from src.governance.promotion_loop.candidate_lineage_manifest_v1 import (
    LineageRefType,
    LineageRelation,
    lineage_ref_to_mapping,
)
from src.governance.promotion_loop.var_suite_lineage_ref_producer_v1 import (
    SUITE_REPORT_JSON,
    VAR_SUITE_OWNER_DOMAIN,
    produce_var_suite_lineage_ref_v1,
    serialize_var_suite_lineage_ref_v1,
    write_var_suite_lineage_ref_v1_atomic,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256
from src.meta.learning_loop.var_suite_durable_evidence_binding_v1 import (
    INDEX_ARTIFACT_REL,
    LINEAGE_REF_ARTIFACT_REL,
    SUITE_REPORT_ARTIFACT_REL,
    BoundArtifactRecord,
    VarSuiteBindingCrossReferences,
    VarSuiteDurableEvidenceBindingError,
    build_binding_index_v1,
    check_reference_consistency,
    produce_var_suite_durable_evidence_bundle_v1,
    serialize_binding_index_v1,
)

REPORT_DIR_NAME = "suite-run-k-001"


@pytest.fixture(autouse=True)
def _allow_tmp_output(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "src.meta.learning_loop.var_suite_durable_evidence_binding_v1.is_under_tmp",
        lambda _path: False,
    )


def _minimal_suite_report_data(*, overall_result: str = "PASS") -> dict:
    return {"overall_result": overall_result}


def _write_report_dir(
    tmp_path: Path,
    data: dict | None = None,
    *,
    report_dir_name: str = REPORT_DIR_NAME,
) -> Path:
    report_dir = tmp_path / "sources" / report_dir_name
    report_dir.mkdir(parents=True)
    payload = _minimal_suite_report_data() if data is None else data
    (report_dir / SUITE_REPORT_JSON).write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return report_dir


def _write_lineage_ref(report_dir: Path, ref_path: Path) -> None:
    result = produce_var_suite_lineage_ref_v1(report_dir=report_dir)
    write_var_suite_lineage_ref_v1_atomic(result.ref, ref_path, fail_closed_if_exists=True)


def _durable_output(tmp_path: Path, name: str = "bundle") -> Path:
    root = tmp_path / "evidence_root"
    root.mkdir(exist_ok=True)
    return root / name


def _bind_inputs(tmp_path: Path) -> tuple[Path, Path, Path]:
    report_dir = _write_report_dir(tmp_path)
    ref_path = tmp_path / "sources" / "var_suite_ref.json"
    _write_lineage_ref(report_dir, ref_path)
    return report_dir, ref_path, _durable_output(tmp_path)


def test_happy_path_binds_successfully(tmp_path: Path) -> None:
    report_dir, ref_path, out = _bind_inputs(tmp_path)
    result = produce_var_suite_durable_evidence_bundle_v1(
        report_dir=report_dir,
        var_suite_lineage_ref_path=ref_path,
        output_dir=out,
    )
    assert result.report_ref_id == REPORT_DIR_NAME
    assert (out / SUITE_REPORT_ARTIFACT_REL).is_file()
    assert (out / LINEAGE_REF_ARTIFACT_REL).is_file()
    assert (out / INDEX_ARTIFACT_REL).is_file()
    ok, _ = verify_manifest_sha256(out)
    assert ok is True


def test_byte_identical_copies(tmp_path: Path) -> None:
    report_dir, ref_path, out = _bind_inputs(tmp_path)
    report_bytes = (report_dir / SUITE_REPORT_JSON).read_bytes()
    ref_bytes = ref_path.read_bytes()
    produce_var_suite_durable_evidence_bundle_v1(
        report_dir=report_dir,
        var_suite_lineage_ref_path=ref_path,
        output_dir=out,
    )
    assert (out / SUITE_REPORT_ARTIFACT_REL).read_bytes() == report_bytes
    assert (out / LINEAGE_REF_ARTIFACT_REL).read_bytes() == ref_bytes


def test_binding_index_metadata_only(tmp_path: Path) -> None:
    report_dir, ref_path, out = _bind_inputs(tmp_path)
    produce_var_suite_durable_evidence_bundle_v1(
        report_dir=report_dir,
        var_suite_lineage_ref_path=ref_path,
        output_dir=out,
    )
    index = json.loads((out / INDEX_ARTIFACT_REL).read_text(encoding="utf-8"))
    assert index["evidence_does_not_authorize_runtime"] is True
    assert index["report_ref_id"] == REPORT_DIR_NAME
    assert "overall_result" not in index
    assert "observations" not in json.dumps(index["var_suite_lineage_ref"])
    assert all(not Path(item["relative_path"]).is_absolute() for item in index["artifacts"])


def test_overall_result_present_but_not_interpreted(tmp_path: Path) -> None:
    for value in ("PASS", "FAIL", "UNKNOWN", "REJECT"):
        report_dir = _write_report_dir(
            tmp_path, {"overall_result": value}, report_dir_name=f"r-{value}"
        )
        ref_path = tmp_path / "sources" / f"ref-{value}.json"
        _write_lineage_ref(report_dir, ref_path)
        out = _durable_output(tmp_path, f"out-{value}")
        produce_var_suite_durable_evidence_bundle_v1(
            report_dir=report_dir,
            var_suite_lineage_ref_path=ref_path,
            output_dir=out,
        )
        assert (out / SUITE_REPORT_ARTIFACT_REL).exists()


def test_check_reference_consistency_digest_mismatch(tmp_path: Path) -> None:
    report_dir, ref_path, _ = _bind_inputs(tmp_path)
    result = produce_var_suite_lineage_ref_v1(report_dir=report_dir)
    ref = result.ref
    report_bytes = (report_dir / SUITE_REPORT_JSON).read_bytes()
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
    with pytest.raises(VarSuiteDurableEvidenceBindingError, match="digest does not match"):
        check_reference_consistency(report_dir=report_dir, report_bytes=report_bytes, ref=bad_ref)


def test_wrong_ref_type_fail_closed(tmp_path: Path) -> None:
    report_dir, ref_path, out = _bind_inputs(tmp_path)
    payload = json.loads(ref_path.read_text(encoding="utf-8"))
    payload["ref_type"] = LineageRefType.BACKTEST.value
    ref_path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(VarSuiteDurableEvidenceBindingError, match="ref_type must be VAR_SUITE"):
        produce_var_suite_durable_evidence_bundle_v1(
            report_dir=report_dir,
            var_suite_lineage_ref_path=ref_path,
            output_dir=out,
        )


def test_wrong_relation_fail_closed(tmp_path: Path) -> None:
    report_dir, ref_path, out = _bind_inputs(tmp_path)
    payload = json.loads(ref_path.read_text(encoding="utf-8"))
    payload["relation"] = LineageRelation.EVALUATES.value
    ref_path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(VarSuiteDurableEvidenceBindingError, match="relation must be VALIDATES"):
        produce_var_suite_durable_evidence_bundle_v1(
            report_dir=report_dir,
            var_suite_lineage_ref_path=ref_path,
            output_dir=out,
        )


def test_wrong_artifact_path_fail_closed(tmp_path: Path) -> None:
    report_dir, ref_path, out = _bind_inputs(tmp_path)
    payload = json.loads(ref_path.read_text(encoding="utf-8"))
    payload["artifact_path"] = "other_report.json"
    ref_path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(VarSuiteDurableEvidenceBindingError, match="artifact_path must be"):
        produce_var_suite_durable_evidence_bundle_v1(
            report_dir=report_dir,
            var_suite_lineage_ref_path=ref_path,
            output_dir=out,
        )


def test_inconsistent_ref_id_fail_closed(tmp_path: Path) -> None:
    report_dir, ref_path, out = _bind_inputs(tmp_path)
    payload = json.loads(ref_path.read_text(encoding="utf-8"))
    payload["ref_id"] = "wrong-id"
    ref_path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(VarSuiteDurableEvidenceBindingError, match="ref_id must match"):
        produce_var_suite_durable_evidence_bundle_v1(
            report_dir=report_dir,
            var_suite_lineage_ref_path=ref_path,
            output_dir=out,
        )


def test_inconsistent_owner_domain_fail_closed(tmp_path: Path) -> None:
    report_dir, ref_path, out = _bind_inputs(tmp_path)
    payload = json.loads(ref_path.read_text(encoding="utf-8"))
    payload["owner_domain"] = "other/domain"
    ref_path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(VarSuiteDurableEvidenceBindingError, match="owner_domain must be"):
        produce_var_suite_durable_evidence_bundle_v1(
            report_dir=report_dir,
            var_suite_lineage_ref_path=ref_path,
            output_dir=out,
        )


def test_missing_suite_report_fail_closed(tmp_path: Path) -> None:
    report_dir = tmp_path / "sources" / "empty-dir"
    report_dir.mkdir(parents=True)
    ref_path = tmp_path / "sources" / "orphan_ref.json"
    result = produce_var_suite_lineage_ref_v1(report_dir=_write_report_dir(tmp_path))
    write_var_suite_lineage_ref_v1_atomic(result.ref, ref_path)
    out = _durable_output(tmp_path, "missing_report")
    with pytest.raises(VarSuiteDurableEvidenceBindingError, match="not found"):
        produce_var_suite_durable_evidence_bundle_v1(
            report_dir=report_dir,
            var_suite_lineage_ref_path=ref_path,
            output_dir=out,
        )


def test_missing_overall_result_fail_closed(tmp_path: Path) -> None:
    report_dir = _write_report_dir(tmp_path, {"observations": 1})
    ref_path = tmp_path / "sources" / "ref-no-overall.json"
    with pytest.raises(Exception):
        _write_lineage_ref(report_dir, ref_path)


def test_invalid_report_json_fail_closed(tmp_path: Path) -> None:
    report_dir = tmp_path / "sources" / "bad-json"
    report_dir.mkdir(parents=True)
    (report_dir / SUITE_REPORT_JSON).write_text("{broken", encoding="utf-8")
    ref_path = tmp_path / "sources" / "ref.json"
    good_dir = _write_report_dir(tmp_path, report_dir_name="good")
    _write_lineage_ref(good_dir, ref_path)
    out = _durable_output(tmp_path, "bad-json")
    with pytest.raises(VarSuiteDurableEvidenceBindingError):
        produce_var_suite_durable_evidence_bundle_v1(
            report_dir=report_dir,
            var_suite_lineage_ref_path=ref_path,
            output_dir=out,
        )


def test_missing_lineage_ref_fail_closed(tmp_path: Path) -> None:
    report_dir = _write_report_dir(tmp_path)
    out = _durable_output(tmp_path, "missing_ref")
    with pytest.raises(VarSuiteDurableEvidenceBindingError, match="not found"):
        produce_var_suite_durable_evidence_bundle_v1(
            report_dir=report_dir,
            var_suite_lineage_ref_path=tmp_path / "missing_ref.json",
            output_dir=out,
        )


def test_symlink_report_rejected(tmp_path: Path) -> None:
    report_dir, ref_path, out = _bind_inputs(tmp_path)
    link = tmp_path / "sources" / "report_link"
    link.symlink_to(report_dir, target_is_directory=True)
    with pytest.raises(VarSuiteDurableEvidenceBindingError, match="symlink"):
        produce_var_suite_durable_evidence_bundle_v1(
            report_dir=link,
            var_suite_lineage_ref_path=ref_path,
            output_dir=out,
        )


def test_existing_output_dir_fail_closed(tmp_path: Path) -> None:
    report_dir, ref_path, out = _bind_inputs(tmp_path)
    out.mkdir(parents=True)
    with pytest.raises(VarSuiteDurableEvidenceBindingError, match="already exists"):
        produce_var_suite_durable_evidence_bundle_v1(
            report_dir=report_dir,
            var_suite_lineage_ref_path=ref_path,
            output_dir=out,
        )


def test_deterministic_index_and_manifest(tmp_path: Path) -> None:
    report_dir, ref_path, _ = _bind_inputs(tmp_path)
    out1 = _durable_output(tmp_path, "det1")
    out2 = _durable_output(tmp_path, "det2")
    produce_var_suite_durable_evidence_bundle_v1(
        report_dir=report_dir,
        var_suite_lineage_ref_path=ref_path,
        output_dir=out1,
    )
    produce_var_suite_durable_evidence_bundle_v1(
        report_dir=report_dir,
        var_suite_lineage_ref_path=ref_path,
        output_dir=out2,
    )
    assert (out1 / INDEX_ARTIFACT_REL).read_bytes() == (out2 / INDEX_ARTIFACT_REL).read_bytes()
    assert (out1 / "MANIFEST.sha256").read_bytes() == (out2 / "MANIFEST.sha256").read_bytes()


def test_copy_failure_cleans_up(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    report_dir, ref_path, out = _bind_inputs(tmp_path)

    def _boom(_src: Path, _dst: Path) -> str:
        raise OSError("copy failed")

    monkeypatch.setattr(
        "src.meta.learning_loop.var_suite_durable_evidence_binding_v1._copy_byte_identical",
        _boom,
    )
    with pytest.raises(OSError, match="copy failed"):
        produce_var_suite_durable_evidence_bundle_v1(
            report_dir=report_dir,
            var_suite_lineage_ref_path=ref_path,
            output_dir=out,
        )
    assert not out.exists()


def test_manifest_verify_failure_cleans_up(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    report_dir, ref_path, out = _bind_inputs(tmp_path)
    monkeypatch.setattr(
        "src.meta.learning_loop.var_suite_durable_evidence_binding_v1.verify_manifest_sha256",
        lambda _root: (False, "checksum mismatch"),
    )
    with pytest.raises(VarSuiteDurableEvidenceBindingError, match="verification failed"):
        produce_var_suite_durable_evidence_bundle_v1(
            report_dir=report_dir,
            var_suite_lineage_ref_path=ref_path,
            output_dir=out,
        )
    assert not out.exists()


def test_build_binding_index_rejects_forbidden_key(tmp_path: Path) -> None:
    report_dir = _write_report_dir(tmp_path)
    ref = produce_var_suite_lineage_ref_v1(report_dir=report_dir).ref
    cross = VarSuiteBindingCrossReferences(
        report_ref_id=ref.ref_id,
        lineage_ref_digest=ref.digest or "a" * 64,
        lineage_ref_artifact_path=ref.artifact_path or SUITE_REPORT_JSON,
    )
    artifacts = (
        BoundArtifactRecord("var_suite_report", SUITE_REPORT_ARTIFACT_REL, "b" * 64),
        BoundArtifactRecord("var_suite_lineage_ref_v1", LINEAGE_REF_ARTIFACT_REL, "c" * 64),
    )
    index = build_binding_index_v1(
        report_ref_id=ref.ref_id,
        cross_references=cross,
        ref=ref,
        artifacts=artifacts,
    )
    index["overall_result"] = "PASS"
    with pytest.raises(VarSuiteDurableEvidenceBindingError, match="forbidden key"):
        serialize_binding_index_v1(index)


def test_integrity_hash_stable_for_index_payload(tmp_path: Path) -> None:
    report_dir, ref_path, _ = _bind_inputs(tmp_path)
    ref = produce_var_suite_lineage_ref_v1(report_dir=report_dir).ref
    report_bytes = (report_dir / SUITE_REPORT_JSON).read_bytes()
    cross = check_reference_consistency(report_dir=report_dir, report_bytes=report_bytes, ref=ref)
    artifacts = (
        BoundArtifactRecord("var_suite_report", SUITE_REPORT_ARTIFACT_REL, ref.digest or ""),
        BoundArtifactRecord("var_suite_lineage_ref_v1", LINEAGE_REF_ARTIFACT_REL, ref.digest or ""),
    )
    index = build_binding_index_v1(
        report_ref_id=report_dir.name,
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
        "src.meta.learning_loop.var_suite_durable_evidence_binding_v1.is_under_tmp",
        real_is_under_tmp,
    )
    report_dir, ref_path, _ = _bind_inputs(tmp_path)
    out = Path("/tmp/peak_trade_pkg_k_binding_reject_test")
    try:
        with pytest.raises(VarSuiteDurableEvidenceBindingError, match="outside /tmp"):
            produce_var_suite_durable_evidence_bundle_v1(
                report_dir=report_dir,
                var_suite_lineage_ref_path=ref_path,
                output_dir=out,
            )
    finally:
        if out.exists():
            shutil.rmtree(out)


def test_no_runtime_imports_in_binding_module() -> None:
    import ast

    path = Path("src/meta/learning_loop/var_suite_durable_evidence_binding_v1.py")
    tree = ast.parse(path.read_text(encoding="utf-8"))
    forbidden = ("promotion_loop.engine", "governance.promotion_loop.engine")
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            for token in forbidden:
                assert token not in node.module


def test_package_j_ref_serialization_compatible(tmp_path: Path) -> None:
    report_dir, ref_path, out = _bind_inputs(tmp_path)
    produce_var_suite_durable_evidence_bundle_v1(
        report_dir=report_dir,
        var_suite_lineage_ref_path=ref_path,
        output_dir=out,
    )
    original = json.loads(ref_path.read_text(encoding="utf-8"))
    copied = json.loads((out / LINEAGE_REF_ARTIFACT_REL).read_text(encoding="utf-8"))
    assert copied == original
    assert copied == json.loads(
        serialize_var_suite_lineage_ref_v1(
            produce_var_suite_lineage_ref_v1(report_dir=report_dir).ref
        )
    )
