"""Contract tests for Package L offline BACKTEST durable evidence binding v1."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256
from src.governance.promotion_loop.backtest_lineage_ref_producer_v1 import (
    RUN_SUMMARY_REL_PATH,
    produce_backtest_lineage_ref_v1,
    serialize_backtest_lineage_ref_v1,
    write_backtest_lineage_ref_v1_atomic,
)
from src.governance.promotion_loop.candidate_lineage_manifest_v1 import (
    LineageRefType,
    LineageRelation,
)
from src.meta.learning_loop.backtest_durable_evidence_binding_v1 import (
    INDEX_ARTIFACT_REL,
    LINEAGE_REF_ARTIFACT_REL,
    RUN_SUMMARY_ARTIFACT_REL,
    BacktestBindingCrossReferences,
    BacktestDurableEvidenceBindingError,
    BoundArtifactRecord,
    build_binding_index_v1,
    check_reference_consistency,
    produce_backtest_durable_evidence_bundle_v1,
    serialize_binding_index_v1,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256

RUN_ID = "test-run-l-001"
FIXED_STARTED = "2025-01-15T10:00:00+00:00"
FIXED_FINISHED = "2025-01-15T10:05:00+00:00"


@pytest.fixture(autouse=True)
def _allow_tmp_output(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "src.meta.learning_loop.backtest_durable_evidence_binding_v1.is_under_tmp",
        lambda _path: False,
    )


def _minimal_run_summary_data(*, run_id: str = RUN_ID, status: str = "FINISHED") -> dict:
    return {
        "run_id": run_id,
        "started_at_utc": FIXED_STARTED,
        "finished_at_utc": FIXED_FINISHED,
        "status": status,
        "tracking_backend": "null",
    }


def _write_run_dir(
    tmp_path: Path,
    data: dict | None = None,
    *,
    run_dir_name: str = "completed-run-l",
) -> Path:
    run_dir = tmp_path / "sources" / run_dir_name
    run_dir.mkdir(parents=True)
    payload = _minimal_run_summary_data() if data is None else data
    (run_dir / RUN_SUMMARY_REL_PATH).write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return run_dir


def _write_lineage_ref(run_dir: Path, ref_path: Path) -> None:
    result = produce_backtest_lineage_ref_v1(run_dir=run_dir)
    write_backtest_lineage_ref_v1_atomic(result.ref, ref_path, fail_closed_if_exists=True)


def _durable_output(tmp_path: Path, name: str = "bundle") -> Path:
    root = tmp_path / "evidence_root"
    root.mkdir(exist_ok=True)
    return root / name


def _bind_inputs(tmp_path: Path) -> tuple[Path, Path, Path]:
    run_dir = _write_run_dir(tmp_path)
    ref_path = tmp_path / "sources" / "backtest_ref.json"
    _write_lineage_ref(run_dir, ref_path)
    return run_dir, ref_path, _durable_output(tmp_path)


def test_happy_path_binds_successfully(tmp_path: Path) -> None:
    run_dir, ref_path, out = _bind_inputs(tmp_path)
    result = produce_backtest_durable_evidence_bundle_v1(
        run_dir=run_dir,
        backtest_lineage_ref_path=ref_path,
        output_dir=out,
    )
    assert result.run_ref_id == RUN_ID
    assert (out / RUN_SUMMARY_ARTIFACT_REL).is_file()
    assert (out / LINEAGE_REF_ARTIFACT_REL).is_file()
    assert (out / INDEX_ARTIFACT_REL).is_file()
    ok, _ = verify_manifest_sha256(out)
    assert ok is True


def test_byte_identical_copies(tmp_path: Path) -> None:
    run_dir, ref_path, out = _bind_inputs(tmp_path)
    summary_bytes = (run_dir / RUN_SUMMARY_REL_PATH).read_bytes()
    ref_bytes = ref_path.read_bytes()
    produce_backtest_durable_evidence_bundle_v1(
        run_dir=run_dir,
        backtest_lineage_ref_path=ref_path,
        output_dir=out,
    )
    assert (out / RUN_SUMMARY_ARTIFACT_REL).read_bytes() == summary_bytes
    assert (out / LINEAGE_REF_ARTIFACT_REL).read_bytes() == ref_bytes


def test_binding_index_metadata_only(tmp_path: Path) -> None:
    run_dir, ref_path, out = _bind_inputs(tmp_path)
    produce_backtest_durable_evidence_bundle_v1(
        run_dir=run_dir,
        backtest_lineage_ref_path=ref_path,
        output_dir=out,
    )
    index = json.loads((out / INDEX_ARTIFACT_REL).read_text(encoding="utf-8"))
    assert index["evidence_does_not_authorize_runtime"] is True
    assert index["run_ref_id"] == RUN_ID
    assert "params" not in index
    assert "metrics" not in index
    assert "params" not in json.dumps(index["backtest_lineage_ref"])
    assert all(not Path(item["relative_path"]).is_absolute() for item in index["artifacts"])


def test_metrics_present_in_run_summary_but_not_in_index(tmp_path: Path) -> None:
    data = {
        **_minimal_run_summary_data(),
        "metrics": {"sharpe": 1.5, "total_return": 0.25},
        "params": {"fast_period": 10},
    }
    run_dir = _write_run_dir(tmp_path, data, run_dir_name="metrics-run")
    ref_path = tmp_path / "sources" / "metrics_ref.json"
    _write_lineage_ref(run_dir, ref_path)
    out = _durable_output(tmp_path, "metrics-out")
    produce_backtest_durable_evidence_bundle_v1(
        run_dir=run_dir,
        backtest_lineage_ref_path=ref_path,
        output_dir=out,
    )
    index = json.loads((out / INDEX_ARTIFACT_REL).read_text(encoding="utf-8"))
    assert "metrics" not in index
    assert (out / RUN_SUMMARY_ARTIFACT_REL).exists()


def test_check_reference_consistency_digest_mismatch(tmp_path: Path) -> None:
    run_dir, ref_path, _ = _bind_inputs(tmp_path)
    result = produce_backtest_lineage_ref_v1(run_dir=run_dir)
    ref = result.ref
    from src.experiments.tracking.run_summary import RunSummary

    summary = RunSummary.read_json(result.run_summary_path)
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
    with pytest.raises(BacktestDurableEvidenceBindingError, match="digest"):
        check_reference_consistency(summary=summary, ref=bad_ref)


def test_wrong_ref_id_fail_closed(tmp_path: Path) -> None:
    run_dir, ref_path, out = _bind_inputs(tmp_path)
    payload = json.loads(ref_path.read_text(encoding="utf-8"))
    payload["ref_id"] = "wrong-run-id"
    ref_path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(BacktestDurableEvidenceBindingError, match="ref_id"):
        produce_backtest_durable_evidence_bundle_v1(
            run_dir=run_dir,
            backtest_lineage_ref_path=ref_path,
            output_dir=out,
        )


def test_wrong_ref_type_fail_closed(tmp_path: Path) -> None:
    run_dir, ref_path, out = _bind_inputs(tmp_path)
    payload = json.loads(ref_path.read_text(encoding="utf-8"))
    payload["ref_type"] = LineageRefType.VAR_SUITE.value
    ref_path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(BacktestDurableEvidenceBindingError, match="BACKTEST"):
        produce_backtest_durable_evidence_bundle_v1(
            run_dir=run_dir,
            backtest_lineage_ref_path=ref_path,
            output_dir=out,
        )


def test_wrong_relation_fail_closed(tmp_path: Path) -> None:
    run_dir, ref_path, out = _bind_inputs(tmp_path)
    payload = json.loads(ref_path.read_text(encoding="utf-8"))
    payload["relation"] = LineageRelation.VALIDATES.value
    ref_path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(BacktestDurableEvidenceBindingError, match="EVALUATES"):
        produce_backtest_durable_evidence_bundle_v1(
            run_dir=run_dir,
            backtest_lineage_ref_path=ref_path,
            output_dir=out,
        )


def test_missing_run_summary_fail_closed(tmp_path: Path) -> None:
    run_dir = tmp_path / "sources" / "empty-run"
    run_dir.mkdir(parents=True)
    ref_path = tmp_path / "sources" / "orphan_ref.json"
    good_dir = _write_run_dir(tmp_path)
    _write_lineage_ref(good_dir, ref_path)
    out = _durable_output(tmp_path, "missing-summary")
    with pytest.raises(BacktestDurableEvidenceBindingError, match="not found"):
        produce_backtest_durable_evidence_bundle_v1(
            run_dir=run_dir,
            backtest_lineage_ref_path=ref_path,
            output_dir=out,
        )


def test_non_finished_status_fail_closed(tmp_path: Path) -> None:
    run_dir = _write_run_dir(tmp_path, _minimal_run_summary_data(status="RUNNING"))
    good_dir = _write_run_dir(tmp_path, run_dir_name="good-for-ref")
    ref_path = tmp_path / "sources" / "running_ref.json"
    _write_lineage_ref(good_dir, ref_path)
    out = _durable_output(tmp_path, "running-out")
    with pytest.raises(BacktestDurableEvidenceBindingError, match="not completed"):
        produce_backtest_durable_evidence_bundle_v1(
            run_dir=run_dir,
            backtest_lineage_ref_path=ref_path,
            output_dir=out,
        )


def test_invalid_run_summary_json_fail_closed(tmp_path: Path) -> None:
    run_dir = tmp_path / "sources" / "bad-json"
    run_dir.mkdir(parents=True)
    (run_dir / RUN_SUMMARY_REL_PATH).write_text("{broken", encoding="utf-8")
    ref_path = tmp_path / "sources" / "ref.json"
    good_dir = _write_run_dir(tmp_path, run_dir_name="good-for-ref")
    _write_lineage_ref(good_dir, ref_path)
    out = _durable_output(tmp_path, "bad-json")
    with pytest.raises(BacktestDurableEvidenceBindingError):
        produce_backtest_durable_evidence_bundle_v1(
            run_dir=run_dir,
            backtest_lineage_ref_path=ref_path,
            output_dir=out,
        )


def test_missing_lineage_ref_fail_closed(tmp_path: Path) -> None:
    run_dir = _write_run_dir(tmp_path)
    out = _durable_output(tmp_path, "missing_ref")
    with pytest.raises(BacktestDurableEvidenceBindingError, match="not found"):
        produce_backtest_durable_evidence_bundle_v1(
            run_dir=run_dir,
            backtest_lineage_ref_path=tmp_path / "missing_ref.json",
            output_dir=out,
        )


def test_symlink_run_dir_rejected(tmp_path: Path) -> None:
    run_dir, ref_path, out = _bind_inputs(tmp_path)
    link = tmp_path / "sources" / "run_link"
    link.symlink_to(run_dir, target_is_directory=True)
    with pytest.raises(BacktestDurableEvidenceBindingError, match="symlink"):
        produce_backtest_durable_evidence_bundle_v1(
            run_dir=link,
            backtest_lineage_ref_path=ref_path,
            output_dir=out,
        )


def test_existing_output_dir_fail_closed(tmp_path: Path) -> None:
    run_dir, ref_path, out = _bind_inputs(tmp_path)
    out.mkdir(parents=True)
    with pytest.raises(BacktestDurableEvidenceBindingError, match="already exists"):
        produce_backtest_durable_evidence_bundle_v1(
            run_dir=run_dir,
            backtest_lineage_ref_path=ref_path,
            output_dir=out,
        )


def test_deterministic_index_and_manifest(tmp_path: Path) -> None:
    run_dir, ref_path, _ = _bind_inputs(tmp_path)
    out1 = _durable_output(tmp_path, "det1")
    out2 = _durable_output(tmp_path, "det2")
    produce_backtest_durable_evidence_bundle_v1(
        run_dir=run_dir,
        backtest_lineage_ref_path=ref_path,
        output_dir=out1,
    )
    produce_backtest_durable_evidence_bundle_v1(
        run_dir=run_dir,
        backtest_lineage_ref_path=ref_path,
        output_dir=out2,
    )
    assert (out1 / INDEX_ARTIFACT_REL).read_bytes() == (out2 / INDEX_ARTIFACT_REL).read_bytes()
    assert (out1 / "MANIFEST.sha256").read_bytes() == (out2 / "MANIFEST.sha256").read_bytes()


def test_copy_failure_cleans_up(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    run_dir, ref_path, out = _bind_inputs(tmp_path)

    def _boom(_src: Path, _dst: Path) -> str:
        raise OSError("copy failed")

    monkeypatch.setattr(
        "src.meta.learning_loop.backtest_durable_evidence_binding_v1._copy_byte_identical",
        _boom,
    )
    with pytest.raises(OSError, match="copy failed"):
        produce_backtest_durable_evidence_bundle_v1(
            run_dir=run_dir,
            backtest_lineage_ref_path=ref_path,
            output_dir=out,
        )
    assert not out.exists()


def test_manifest_verify_failure_cleans_up(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    run_dir, ref_path, out = _bind_inputs(tmp_path)
    monkeypatch.setattr(
        "src.meta.learning_loop.backtest_durable_evidence_binding_v1.verify_manifest_sha256",
        lambda _root: (False, "checksum mismatch"),
    )
    with pytest.raises(BacktestDurableEvidenceBindingError, match="verification failed"):
        produce_backtest_durable_evidence_bundle_v1(
            run_dir=run_dir,
            backtest_lineage_ref_path=ref_path,
            output_dir=out,
        )
    assert not out.exists()


def test_build_binding_index_rejects_forbidden_key(tmp_path: Path) -> None:
    run_dir = _write_run_dir(tmp_path)
    ref = produce_backtest_lineage_ref_v1(run_dir=run_dir).ref
    cross = BacktestBindingCrossReferences(
        run_ref_id=ref.ref_id,
        lineage_ref_digest=ref.digest or "a" * 64,
        lineage_ref_artifact_path=ref.artifact_path or RUN_SUMMARY_REL_PATH,
    )
    artifacts = (
        BoundArtifactRecord("backtest_run_summary", RUN_SUMMARY_ARTIFACT_REL, "b" * 64),
        BoundArtifactRecord("backtest_lineage_ref_v1", LINEAGE_REF_ARTIFACT_REL, "c" * 64),
    )
    index = build_binding_index_v1(
        run_ref_id=ref.ref_id,
        cross_references=cross,
        ref=ref,
        artifacts=artifacts,
    )
    index["params"] = {"fast_period": 10}
    with pytest.raises(BacktestDurableEvidenceBindingError, match="forbidden key"):
        serialize_binding_index_v1(index)


def test_integrity_hash_stable_for_index_payload(tmp_path: Path) -> None:
    run_dir, ref_path, _ = _bind_inputs(tmp_path)
    ref = produce_backtest_lineage_ref_v1(run_dir=run_dir).ref
    from src.experiments.tracking.run_summary import RunSummary

    summary = RunSummary.read_json(run_dir / RUN_SUMMARY_REL_PATH)
    cross = check_reference_consistency(summary=summary, ref=ref)
    artifacts = (
        BoundArtifactRecord("backtest_run_summary", RUN_SUMMARY_ARTIFACT_REL, "a" * 64),
        BoundArtifactRecord("backtest_lineage_ref_v1", LINEAGE_REF_ARTIFACT_REL, "b" * 64),
    )
    index = build_binding_index_v1(
        run_ref_id=summary.run_id,
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
        "src.meta.learning_loop.backtest_durable_evidence_binding_v1.is_under_tmp",
        real_is_under_tmp,
    )
    run_dir, ref_path, _ = _bind_inputs(tmp_path)
    out = Path("/tmp/peak_trade_pkg_l_binding_reject_test")
    try:
        with pytest.raises(BacktestDurableEvidenceBindingError, match="outside /tmp"):
            produce_backtest_durable_evidence_bundle_v1(
                run_dir=run_dir,
                backtest_lineage_ref_path=ref_path,
                output_dir=out,
            )
    finally:
        if out.exists():
            shutil.rmtree(out)


def test_no_runtime_imports_in_binding_module() -> None:
    import ast

    path = Path("src/meta/learning_loop/backtest_durable_evidence_binding_v1.py")
    tree = ast.parse(path.read_text(encoding="utf-8"))
    forbidden = ("promotion_loop.engine", "governance.promotion_loop.engine")
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            for token in forbidden:
                assert token not in node.module


def test_package_i_ref_serialization_compatible(tmp_path: Path) -> None:
    run_dir, ref_path, out = _bind_inputs(tmp_path)
    produce_backtest_durable_evidence_bundle_v1(
        run_dir=run_dir,
        backtest_lineage_ref_path=ref_path,
        output_dir=out,
    )
    original = json.loads(ref_path.read_text(encoding="utf-8"))
    copied = json.loads((out / LINEAGE_REF_ARTIFACT_REL).read_text(encoding="utf-8"))
    assert copied == original
    assert copied == json.loads(
        serialize_backtest_lineage_ref_v1(produce_backtest_lineage_ref_v1(run_dir=run_dir).ref)
    )


def test_input_mutation_between_validation_and_copy_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    run_dir, ref_path, out = _bind_inputs(tmp_path)
    original_copy = shutil.copyfile

    def _mutating_copy(src: Path, dst: Path) -> None:
        original_copy(src, dst)
        if src.name == RUN_SUMMARY_REL_PATH:
            src.write_text('{"run_id":"mutated"}', encoding="utf-8")

    monkeypatch.setattr(shutil, "copyfile", _mutating_copy)
    with pytest.raises(BacktestDurableEvidenceBindingError):
        produce_backtest_durable_evidence_bundle_v1(
            run_dir=run_dir,
            backtest_lineage_ref_path=ref_path,
            output_dir=out,
        )
    assert not out.exists()
