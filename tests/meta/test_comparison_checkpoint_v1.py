"""Contract tests for learning loop comparison checkpoint v1."""

from __future__ import annotations

import ast
import json
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

import pytest

pytest_plugins = ["tests.meta.comparison_ssot_v1_fixtures"]

from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256
from src.governance.promotion_loop.comparison_lineage_ref_producer_v1 import (
    produce_comparison_lineage_ref_v1_to_path,
)
from src.meta.learning_loop.comparison_checkpoint_v1 import (
    CHECKPOINT_RELATION,
    COMPARISON_AUTHORITY_INVARIANTS,
    INDEX_ARTIFACT_REL,
    ComparisonCheckpointError,
    build_checkpoint_index_v1,
    produce_comparison_checkpoint_v1,
    reverify_comparison_checkpoint_v1,
    serialize_checkpoint_index_v1,
)
from src.meta.learning_loop.comparison_common_durable_evidence_binding_v1 import (
    INDEX_ARTIFACT_REL as COMMON_INDEX_ARTIFACT_REL,
    produce_comparison_common_durable_evidence_bundle_v1,
)
from src.meta.learning_loop.comparison_metric_input_durable_evidence_binding_v1 import (
    produce_comparison_metric_input_durable_evidence_bundle_v1,
)
from src.meta.learning_loop.comparison_ssot_definition_durable_evidence_binding_v1 import (
    produce_comparison_ssot_definition_durable_evidence_bundle_v1,
)
from src.meta.learning_loop.comparison_ssot_result_durable_evidence_binding_v1 import (
    produce_comparison_ssot_result_durable_evidence_bundle_v1,
)
from src.meta.learning_loop.comparison_ssot_v1.io import read_manifest
from src.meta.learning_loop.comparison_ssot_v1.producer import produce_comparison_offline_v1
from tests.meta.comparison_ssot_v1_fixtures import produce_two_compatible_backtest_inputs


@pytest.fixture(autouse=True)
def _allow_tmp_output(monkeypatch: pytest.MonkeyPatch) -> None:
    for target in (
        "src.meta.learning_loop.comparison_checkpoint_v1.is_under_tmp",
        "src.meta.learning_loop.comparison_common_durable_evidence_binding_v1.is_under_tmp",
        "src.meta.learning_loop.comparison_metric_input_durable_evidence_binding_v1.is_under_tmp",
        "src.meta.learning_loop.comparison_ssot_definition_durable_evidence_binding_v1.is_under_tmp",
        "src.meta.learning_loop.comparison_ssot_result_durable_evidence_binding_v1.is_under_tmp",
    ):
        monkeypatch.setattr(target, lambda _path: False)


def _durable_output(tmp_path: Path, name: str = "checkpoint_out") -> Path:
    root = tmp_path / "evidence_root"
    root.mkdir(exist_ok=True)
    return root / name


def _produce_common_bundle(
    tmp_path: Path,
    durable_root: Path,
) -> tuple[Path, str, Path, Path]:
    metric_root = durable_root / "metric_inputs"
    metric_root.mkdir(exist_ok=True)
    first, second = produce_two_compatible_backtest_inputs(tmp_path, metric_root)
    comparison_root = durable_root / "comparisons"
    comparison_root.mkdir(exist_ok=True)
    offline = produce_comparison_offline_v1(
        input_manifest_paths=[first, second],
        output_root=comparison_root,
        ranking_rule_version="NONE_V1",
    )
    metric_bindings: list[Path] = []
    for idx, manifest_path in enumerate([first, second]):
        out = durable_root / f"metric_input_binding_{idx}"
        produce_comparison_metric_input_durable_evidence_bundle_v1(
            manifest_path=manifest_path,
            output_dir=out,
        )
        metric_bindings.append(out)
    definition_binding = durable_root / "definition_binding"
    produce_comparison_ssot_definition_durable_evidence_bundle_v1(
        manifest_path=offline.definition_path,
        output_dir=definition_binding,
    )
    result_binding = durable_root / "result_binding"
    produce_comparison_ssot_result_durable_evidence_bundle_v1(
        manifest_path=offline.result_path,
        output_dir=result_binding,
    )
    common_out = durable_root / "common_bundle"
    produce_comparison_common_durable_evidence_bundle_v1(
        definition_bound_bundle_dir=definition_binding,
        result_bound_bundle_dir=result_binding,
        metric_input_bound_bundle_dirs=metric_bindings,
        output_dir=common_out,
    )
    return common_out, offline.comparison_definition_id, result_binding, offline.result_path


def _produce_lineage_ref(result_path: Path, durable_root: Path) -> Path:
    ref_path = durable_root / "lineage_ref.json"
    produce_comparison_lineage_ref_v1_to_path(
        manifest_dir=result_path.parent,
        output_path=ref_path,
    )
    return ref_path


def test_happy_path_checkpoint_from_verified_common_bundle(
    tmp_path, ssot_durable_output_dir
) -> None:
    common_out, comparison_definition_id, _, _ = _produce_common_bundle(
        tmp_path, ssot_durable_output_dir
    )
    out = _durable_output(tmp_path)
    result = produce_comparison_checkpoint_v1(
        common_bundle_dir=common_out,
        output_dir=out,
    )
    assert result.comparison_definition_id == comparison_definition_id
    assert result.checkpoint_id
    assert (out / INDEX_ARTIFACT_REL).is_file()
    ok, _ = verify_manifest_sha256(out)
    assert ok is True


def test_deterministic_index_and_manifest(tmp_path, ssot_durable_output_dir) -> None:
    common_out, _, _, _ = _produce_common_bundle(tmp_path, ssot_durable_output_dir)
    out_a = _durable_output(tmp_path, "det_a")
    out_b = _durable_output(tmp_path, "det_b")
    produce_comparison_checkpoint_v1(common_bundle_dir=common_out, output_dir=out_a)
    produce_comparison_checkpoint_v1(common_bundle_dir=common_out, output_dir=out_b)
    assert (out_a / INDEX_ARTIFACT_REL).read_text(encoding="utf-8") == (
        out_b / INDEX_ARTIFACT_REL
    ).read_text(encoding="utf-8")
    assert (out_a / "MANIFEST.sha256").read_text(encoding="utf-8") == (
        out_b / "MANIFEST.sha256"
    ).read_text(encoding="utf-8")


def test_reverify_without_producers(tmp_path, ssot_durable_output_dir) -> None:
    common_out, _, _, _ = _produce_common_bundle(tmp_path, ssot_durable_output_dir)
    out = _durable_output(tmp_path, "replay")
    produce_comparison_checkpoint_v1(common_bundle_dir=common_out, output_dir=out)
    reverify_comparison_checkpoint_v1(output_dir=out)


def test_common_bundle_integrity_digest_verbatim(tmp_path, ssot_durable_output_dir) -> None:
    common_out, _, _, _ = _produce_common_bundle(tmp_path, ssot_durable_output_dir)
    common_index = read_manifest(common_out / COMMON_INDEX_ARTIFACT_REL)
    out = _durable_output(tmp_path, "digest")
    produce_comparison_checkpoint_v1(common_bundle_dir=common_out, output_dir=out)
    index = read_manifest(out / INDEX_ARTIFACT_REL)
    assert (
        index["common_bundle_ref"]["binding_index_integrity_sha256"]
        == common_index["integrity"]["content_sha256"]
    )


def test_comparison_definition_id_verbatim(tmp_path, ssot_durable_output_dir) -> None:
    common_out, comparison_definition_id, _, _ = _produce_common_bundle(
        tmp_path, ssot_durable_output_dir
    )
    out = _durable_output(tmp_path, "def_id")
    produce_comparison_checkpoint_v1(common_bundle_dir=common_out, output_dir=out)
    index = read_manifest(out / INDEX_ARTIFACT_REL)
    assert index["comparison_definition_id"] == comparison_definition_id


def test_metric_input_binding_refs_order_preserved(tmp_path, ssot_durable_output_dir) -> None:
    common_out, _, _, _ = _produce_common_bundle(tmp_path, ssot_durable_output_dir)
    common_index = read_manifest(common_out / COMMON_INDEX_ARTIFACT_REL)
    out = _durable_output(tmp_path, "order")
    produce_comparison_checkpoint_v1(common_bundle_dir=common_out, output_dir=out)
    index = read_manifest(out / INDEX_ARTIFACT_REL)
    assert index["metric_input_binding_refs"] == common_index["metric_input_binding_refs"]


def test_definition_and_result_binding_refs_verbatim(tmp_path, ssot_durable_output_dir) -> None:
    common_out, _, _, _ = _produce_common_bundle(tmp_path, ssot_durable_output_dir)
    common_index = read_manifest(common_out / COMMON_INDEX_ARTIFACT_REL)
    out = _durable_output(tmp_path, "refs")
    produce_comparison_checkpoint_v1(common_bundle_dir=common_out, output_dir=out)
    index = read_manifest(out / INDEX_ARTIFACT_REL)
    assert index["definition_binding_ref"] == common_index["definition_binding_ref"]
    assert index["result_binding_ref"] == common_index["result_binding_ref"]


def test_optional_lineage_ref_cross_check_pass(tmp_path, ssot_durable_output_dir) -> None:
    common_out, _, _, result_path = _produce_common_bundle(tmp_path, ssot_durable_output_dir)
    ref_path = _produce_lineage_ref(result_path, ssot_durable_output_dir)
    out = _durable_output(tmp_path, "with_lineage")
    produce_comparison_checkpoint_v1(
        common_bundle_dir=common_out,
        output_dir=out,
        lineage_ref_path=ref_path,
    )
    index = read_manifest(out / INDEX_ARTIFACT_REL)
    assert "lineage_ref_record" in index


def test_lineage_ref_id_mismatch_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    common_out, _, _, result_path = _produce_common_bundle(tmp_path, ssot_durable_output_dir)
    ref_path = _produce_lineage_ref(result_path, ssot_durable_output_dir)
    payload = json.loads(ref_path.read_text(encoding="utf-8"))
    payload["ref_id"] = "00000000-0000-4000-8000-000000000001"
    bad_ref = ssot_durable_output_dir / "bad_lineage_ref.json"
    bad_ref.write_text(json.dumps(payload), encoding="utf-8")
    out = _durable_output(tmp_path, "lineage_id_mismatch")
    with pytest.raises(ComparisonCheckpointError, match="ref_id"):
        produce_comparison_checkpoint_v1(
            common_bundle_dir=common_out,
            output_dir=out,
            lineage_ref_path=bad_ref,
        )


def test_lineage_ref_digest_mismatch_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    common_out, _, _, result_path = _produce_common_bundle(tmp_path, ssot_durable_output_dir)
    ref_path = _produce_lineage_ref(result_path, ssot_durable_output_dir)
    payload = json.loads(ref_path.read_text(encoding="utf-8"))
    payload["digest"] = "0" * 64
    bad_ref = ssot_durable_output_dir / "bad_digest_ref.json"
    bad_ref.write_text(json.dumps(payload), encoding="utf-8")
    out = _durable_output(tmp_path, "lineage_digest_mismatch")
    with pytest.raises(ComparisonCheckpointError, match="digest"):
        produce_comparison_checkpoint_v1(
            common_bundle_dir=common_out,
            output_dir=out,
            lineage_ref_path=bad_ref,
        )


def test_missing_common_bundle_dir(tmp_path) -> None:
    out = _durable_output(tmp_path, "missing")
    with pytest.raises(ComparisonCheckpointError, match="must be a directory"):
        produce_comparison_checkpoint_v1(
            common_bundle_dir=tmp_path / "missing_common",
            output_dir=out,
        )


def test_common_bundle_manifest_verify_fails(tmp_path, ssot_durable_output_dir) -> None:
    common_out, _, _, _ = _produce_common_bundle(tmp_path, ssot_durable_output_dir)
    (common_out / "MANIFEST.sha256").write_text("broken", encoding="utf-8")
    out = _durable_output(tmp_path, "bad_manifest")
    with pytest.raises(ComparisonCheckpointError, match="MANIFEST.sha256"):
        produce_comparison_checkpoint_v1(common_bundle_dir=common_out, output_dir=out)


def test_unverified_common_bundle_rejected(tmp_path) -> None:
    fake = tmp_path / "fake_common"
    fake.mkdir()
    (fake / COMMON_INDEX_ARTIFACT_REL).write_text("{}", encoding="utf-8")
    out = _durable_output(tmp_path, "unverified")
    with pytest.raises(ComparisonCheckpointError, match="MANIFEST.sha256"):
        produce_comparison_checkpoint_v1(common_bundle_dir=fake, output_dir=out)


def test_symlink_input_rejected(tmp_path, ssot_durable_output_dir) -> None:
    common_out, _, _, _ = _produce_common_bundle(tmp_path, ssot_durable_output_dir)
    link = tmp_path / "common_link"
    link.symlink_to(common_out)
    out = _durable_output(tmp_path, "symlink")
    with pytest.raises(ComparisonCheckpointError, match="symlink"):
        produce_comparison_checkpoint_v1(common_bundle_dir=link, output_dir=out)


def test_path_traversal_rejected(tmp_path, ssot_durable_output_dir) -> None:
    common_out, _, _, _ = _produce_common_bundle(tmp_path, ssot_durable_output_dir)
    out = _durable_output(tmp_path, "traversal")
    bad_ref = tmp_path / ".." / "escape.json"
    with pytest.raises(ComparisonCheckpointError, match="traverse upward"):
        produce_comparison_checkpoint_v1(
            common_bundle_dir=common_out,
            output_dir=out,
            lineage_ref_path=bad_ref,
        )


def test_output_overlap_with_common_bundle_rejected(tmp_path, ssot_durable_output_dir) -> None:
    common_out, _, _, _ = _produce_common_bundle(tmp_path, ssot_durable_output_dir)
    nested = common_out / "nested_checkpoint"
    with pytest.raises(ComparisonCheckpointError, match="inside common bundle"):
        produce_comparison_checkpoint_v1(common_bundle_dir=common_out, output_dir=nested)


def test_output_under_tmp_rejected(tmp_path, ssot_durable_output_dir, monkeypatch) -> None:
    common_out, _, _, _ = _produce_common_bundle(tmp_path, ssot_durable_output_dir)
    monkeypatch.setattr(
        "src.meta.learning_loop.comparison_checkpoint_v1.is_under_tmp",
        lambda path: str(path).startswith("/tmp") or "/tmp/" in str(path),
    )
    out = Path("/tmp/checkpoint_out")
    with pytest.raises(ComparisonCheckpointError, match="/tmp"):
        produce_comparison_checkpoint_v1(common_bundle_dir=common_out, output_dir=out)


def test_existing_output_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    common_out, _, _, _ = _produce_common_bundle(tmp_path, ssot_durable_output_dir)
    out = _durable_output(tmp_path, "exists")
    out.mkdir()
    with pytest.raises(ComparisonCheckpointError, match="already exists"):
        produce_comparison_checkpoint_v1(common_bundle_dir=common_out, output_dir=out)


def test_partial_staging_no_output_on_failure(tmp_path, ssot_durable_output_dir) -> None:
    common_out, _, _, _ = _produce_common_bundle(tmp_path, ssot_durable_output_dir)
    out = _durable_output(tmp_path, "partial")
    with patch(
        "src.meta.learning_loop.comparison_checkpoint_v1.write_manifest_sha256",
        side_effect=RuntimeError("staging failure"),
    ):
        with pytest.raises(RuntimeError, match="staging failure"):
            produce_comparison_checkpoint_v1(common_bundle_dir=common_out, output_dir=out)
    assert not out.exists()


def test_manifest_sha256_present_and_valid(tmp_path, ssot_durable_output_dir) -> None:
    common_out, _, _, _ = _produce_common_bundle(tmp_path, ssot_durable_output_dir)
    out = _durable_output(tmp_path, "manifest")
    produce_comparison_checkpoint_v1(common_bundle_dir=common_out, output_dir=out)
    ok, msg = verify_manifest_sha256(out)
    assert ok is True, msg


def test_evidence_does_not_authorize_runtime(tmp_path, ssot_durable_output_dir) -> None:
    common_out, _, _, _ = _produce_common_bundle(tmp_path, ssot_durable_output_dir)
    out = _durable_output(tmp_path, "auth")
    produce_comparison_checkpoint_v1(common_bundle_dir=common_out, output_dir=out)
    index = read_manifest(out / INDEX_ARTIFACT_REL)
    assert index["evidence_does_not_authorize_runtime"] is True


def test_comparison_authority_invariants_present(tmp_path, ssot_durable_output_dir) -> None:
    common_out, _, _, _ = _produce_common_bundle(tmp_path, ssot_durable_output_dir)
    out = _durable_output(tmp_path, "invariants")
    produce_comparison_checkpoint_v1(common_bundle_dir=common_out, output_dir=out)
    index = read_manifest(out / INDEX_ARTIFACT_REL)
    assert index["comparison_authority_invariants"] == COMPARISON_AUTHORITY_INVARIANTS


def _valid_common_index() -> dict[str, object]:
    return {
        "comparison_definition_id": "00000000-0000-4000-8000-000000000099",
        "metric_input_binding_refs": [],
        "definition_binding_ref": {"manifest_content_sha256": "a" * 64},
        "result_binding_ref": {"manifest_content_sha256": "b" * 64},
        "chain_cross_references": {},
        "comparison_authority_invariants": COMPARISON_AUTHORITY_INVARIANTS,
        "integrity": {"content_sha256": "c" * 64},
    }


def test_forbidden_completion_field_rejected() -> None:
    index = build_checkpoint_index_v1(
        common_bundle_dir=Path("/var/evidence/common"),
        common_bundle_index=_valid_common_index(),
    )
    index["completion"] = True
    with pytest.raises(ComparisonCheckpointError, match="forbidden key: completion"):
        serialize_checkpoint_index_v1(index)


def test_forbidden_promotion_field_rejected() -> None:
    index = build_checkpoint_index_v1(
        common_bundle_dir=Path("/var/evidence/common"),
        common_bundle_index=_valid_common_index(),
    )
    index["promotion"] = True
    with pytest.raises(ComparisonCheckpointError, match="forbidden key: promotion"):
        serialize_checkpoint_index_v1(index)


def test_forbidden_winner_selection_acceptance_rejected() -> None:
    for forbidden in ("winner", "selected", "accepted"):
        index = build_checkpoint_index_v1(
            common_bundle_dir=Path("/var/evidence/common"),
            common_bundle_index=_valid_common_index(),
        )
        index[forbidden] = True
        with pytest.raises(ComparisonCheckpointError, match=f"forbidden key: {forbidden}"):
            serialize_checkpoint_index_v1(index)


def test_forbidden_runtime_field_rejected() -> None:
    index = build_checkpoint_index_v1(
        common_bundle_dir=Path("/var/evidence/common"),
        common_bundle_index=_valid_common_index(),
    )
    index["live_authorized"] = True
    with pytest.raises(ComparisonCheckpointError, match="forbidden key: live_authorized"):
        serialize_checkpoint_index_v1(index)


def test_is_completion_evidence_false(tmp_path, ssot_durable_output_dir) -> None:
    common_out, _, _, _ = _produce_common_bundle(tmp_path, ssot_durable_output_dir)
    out = _durable_output(tmp_path, "not_completion")
    produce_comparison_checkpoint_v1(common_bundle_dir=common_out, output_dir=out)
    index = read_manifest(out / INDEX_ARTIFACT_REL)
    assert index["is_completion_evidence"] is False


def test_ast_no_forbidden_runtime_imports() -> None:
    module_path = Path(__file__).resolve().parents[2] / (
        "src/meta/learning_loop/comparison_checkpoint_v1.py"
    )
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    forbidden = {"src.execution", "src.risk", "mlflow", "src.ops.durable_completion_validation"}
    assert not modules & forbidden


def test_no_common_bundle_producer_re_run(tmp_path, ssot_durable_output_dir) -> None:
    common_out, _, _, _ = _produce_common_bundle(tmp_path, ssot_durable_output_dir)
    out = _durable_output(tmp_path, "no_producer")
    with patch(
        "src.meta.learning_loop.comparison_common_durable_evidence_binding_v1.produce_comparison_common_durable_evidence_bundle_v1"
    ) as mocked:
        produce_comparison_checkpoint_v1(common_bundle_dir=common_out, output_dir=out)
        mocked.assert_not_called()


def test_no_comparison_offline_reexecution(tmp_path, ssot_durable_output_dir) -> None:
    common_out, _, _, _ = _produce_common_bundle(tmp_path, ssot_durable_output_dir)
    out = _durable_output(tmp_path, "no_offline")
    with patch(
        "src.meta.learning_loop.comparison_ssot_v1.producer.produce_comparison_offline_v1"
    ) as mocked:
        produce_comparison_checkpoint_v1(common_bundle_dir=common_out, output_dir=out)
        mocked.assert_not_called()


def test_no_registry_or_mlflow_resolution() -> None:
    module_path = Path(__file__).resolve().parents[2] / (
        "src/meta/learning_loop/comparison_checkpoint_v1.py"
    )
    source = module_path.read_text(encoding="utf-8")
    assert "mlflow" not in source.lower()
    assert "registry" not in source.lower()


def test_common_bundle_dir_not_mutated(tmp_path, ssot_durable_output_dir) -> None:
    common_out, _, _, _ = _produce_common_bundle(tmp_path, ssot_durable_output_dir)
    before = {
        rel.as_posix(): rel.read_bytes()
        for rel in common_out.rglob("*")
        if rel.is_file() and not rel.is_symlink()
    }
    out = _durable_output(tmp_path, "nomut")
    produce_comparison_checkpoint_v1(common_bundle_dir=common_out, output_dir=out)
    after = {
        rel.as_posix(): rel.read_bytes()
        for rel in common_out.rglob("*")
        if rel.is_file() and not rel.is_symlink()
    }
    assert before == after


def test_duplicate_metric_input_ref_order_stable(tmp_path, ssot_durable_output_dir) -> None:
    common_out, _, _, _ = _produce_common_bundle(tmp_path, ssot_durable_output_dir)
    common_index = read_manifest(common_out / COMMON_INDEX_ARTIFACT_REL)
    out = _durable_output(tmp_path, "dup_order")
    produce_comparison_checkpoint_v1(common_bundle_dir=common_out, output_dir=out)
    index = read_manifest(out / INDEX_ARTIFACT_REL)
    refs = index["metric_input_binding_refs"]
    assert refs == common_index["metric_input_binding_refs"]


def test_checkpoint_relation_constant(tmp_path, ssot_durable_output_dir) -> None:
    common_out, _, _, _ = _produce_common_bundle(tmp_path, ssot_durable_output_dir)
    out = _durable_output(tmp_path, "relation")
    produce_comparison_checkpoint_v1(common_bundle_dir=common_out, output_dir=out)
    index = read_manifest(out / INDEX_ARTIFACT_REL)
    assert index["checkpoint_relation"] == CHECKPOINT_RELATION


def test_replay_mutates_nothing(tmp_path, ssot_durable_output_dir) -> None:
    common_out, _, _, _ = _produce_common_bundle(tmp_path, ssot_durable_output_dir)
    out = _durable_output(tmp_path, "replay_nomut")
    produce_comparison_checkpoint_v1(common_bundle_dir=common_out, output_dir=out)
    before = {
        rel.as_posix(): rel.read_bytes()
        for rel in out.rglob("*")
        if rel.is_file() and not rel.is_symlink()
    }
    reverify_comparison_checkpoint_v1(output_dir=out)
    after = {
        rel.as_posix(): rel.read_bytes()
        for rel in out.rglob("*")
        if rel.is_file() and not rel.is_symlink()
    }
    assert before == after


def test_common_bundle_ref_mismatch_on_tampered_index(tmp_path, ssot_durable_output_dir) -> None:
    common_out, _, _, _ = _produce_common_bundle(tmp_path, ssot_durable_output_dir)
    index_path = common_out / COMMON_INDEX_ARTIFACT_REL
    index = read_manifest(index_path)
    mutated = deepcopy(index)
    mutated["comparison_definition_id"] = "00000000-0000-4000-8000-000000000001"
    index_path.write_text(json.dumps(mutated), encoding="utf-8")
    out = _durable_output(tmp_path, "tampered")
    with pytest.raises(ComparisonCheckpointError, match="MANIFEST.sha256"):
        produce_comparison_checkpoint_v1(common_bundle_dir=common_out, output_dir=out)
