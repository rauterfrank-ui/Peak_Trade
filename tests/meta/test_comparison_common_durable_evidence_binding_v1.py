"""Contract tests for comparison common durable evidence binding v1."""

from __future__ import annotations

import ast
import json
import shutil
from copy import deepcopy
from pathlib import Path

import pytest

pytest_plugins = ["tests.meta.comparison_ssot_v1_fixtures"]

from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256
from src.meta.learning_loop.comparison_common_durable_evidence_binding_v1 import (
    BINDING_RELATION,
    COMPARISON_AUTHORITY_INVARIANTS,
    INDEX_ARTIFACT_REL,
    MAX_METRIC_INPUT_BINDINGS,
    MIN_METRIC_INPUT_BINDINGS,
    ComparisonCommonDurableEvidenceBindingError,
    check_reference_consistency,
    produce_comparison_common_durable_evidence_bundle_v1,
    reverify_comparison_common_durable_evidence_bundle_v1,
)
from src.meta.learning_loop.comparison_metric_input_durable_evidence_binding_v1 import (
    produce_comparison_metric_input_durable_evidence_bundle_v1,
)
from src.meta.learning_loop.comparison_ssot_definition_durable_evidence_binding_v1 import (
    INDEX_ARTIFACT_REL as DEFINITION_INDEX_ARTIFACT_REL,
    produce_comparison_ssot_definition_durable_evidence_bundle_v1,
)
from src.meta.learning_loop.comparison_ssot_result_durable_evidence_binding_v1 import (
    INDEX_ARTIFACT_REL as RESULT_INDEX_ARTIFACT_REL,
    produce_comparison_ssot_result_durable_evidence_bundle_v1,
)
from src.meta.learning_loop.comparison_ssot_v1.io import read_manifest
from src.meta.learning_loop.comparison_ssot_v1.producer import produce_comparison_offline_v1
from tests.meta.comparison_ssot_v1_fixtures import produce_two_compatible_backtest_inputs


@pytest.fixture(autouse=True)
def _allow_tmp_output(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "src.meta.learning_loop.comparison_common_durable_evidence_binding_v1.is_under_tmp",
        lambda _path: False,
    )
    monkeypatch.setattr(
        "src.meta.learning_loop.comparison_metric_input_durable_evidence_binding_v1.is_under_tmp",
        lambda _path: False,
    )
    monkeypatch.setattr(
        "src.meta.learning_loop.comparison_ssot_definition_durable_evidence_binding_v1.is_under_tmp",
        lambda _path: False,
    )
    monkeypatch.setattr(
        "src.meta.learning_loop.comparison_ssot_result_durable_evidence_binding_v1.is_under_tmp",
        lambda _path: False,
    )


def _durable_output(tmp_path: Path, name: str = "common_bundle") -> Path:
    root = tmp_path / "evidence_root"
    root.mkdir(exist_ok=True)
    return root / name


def _produce_bound_chain(
    tmp_path: Path,
    durable_root: Path,
) -> tuple[list[Path], Path, Path, str]:
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
    return metric_bindings, definition_binding, result_binding, offline.comparison_definition_id


def test_happy_path_common_bundle(tmp_path, ssot_durable_output_dir) -> None:
    metric_bindings, definition_binding, result_binding, comparison_definition_id = (
        _produce_bound_chain(tmp_path, ssot_durable_output_dir)
    )
    out = _durable_output(tmp_path)
    result = produce_comparison_common_durable_evidence_bundle_v1(
        definition_bound_bundle_dir=definition_binding,
        result_bound_bundle_dir=result_binding,
        metric_input_bound_bundle_dirs=metric_bindings,
        output_dir=out,
    )
    assert result.comparison_definition_id == comparison_definition_id
    assert result.metric_input_binding_count == MIN_METRIC_INPUT_BINDINGS
    assert (out / INDEX_ARTIFACT_REL).is_file()
    ok, _ = verify_manifest_sha256(out)
    assert ok is True


def test_definition_input_ordering_preserved(tmp_path, ssot_durable_output_dir) -> None:
    metric_bindings, definition_binding, result_binding, _ = _produce_bound_chain(
        tmp_path, ssot_durable_output_dir
    )
    definition_index = read_manifest(definition_binding / DEFINITION_INDEX_ARTIFACT_REL)
    out = _durable_output(tmp_path, "order")
    produce_comparison_common_durable_evidence_bundle_v1(
        definition_bound_bundle_dir=definition_binding,
        result_bound_bundle_dir=result_binding,
        metric_input_bound_bundle_dirs=metric_bindings,
        output_dir=out,
    )
    index = read_manifest(out / INDEX_ARTIFACT_REL)
    assert [
        item["definition_input_ref"] for item in index["metric_input_binding_refs"]
    ] == definition_index["definition_input_refs"]


def test_metric_input_list_not_mutated(tmp_path, ssot_durable_output_dir) -> None:
    metric_bindings, definition_binding, result_binding, _ = _produce_bound_chain(
        tmp_path, ssot_durable_output_dir
    )
    original = list(metric_bindings)
    out = _durable_output(tmp_path, "nomut")
    produce_comparison_common_durable_evidence_bundle_v1(
        definition_bound_bundle_dir=definition_binding,
        result_bound_bundle_dir=result_binding,
        metric_input_bound_bundle_dirs=metric_bindings,
        output_dir=out,
    )
    assert metric_bindings == original


def test_reverify_without_producers(tmp_path, ssot_durable_output_dir) -> None:
    metric_bindings, definition_binding, result_binding, _ = _produce_bound_chain(
        tmp_path, ssot_durable_output_dir
    )
    out = _durable_output(tmp_path, "replay")
    produce_comparison_common_durable_evidence_bundle_v1(
        definition_bound_bundle_dir=definition_binding,
        result_bound_bundle_dir=result_binding,
        metric_input_bound_bundle_dirs=metric_bindings,
        output_dir=out,
    )
    reverify_comparison_common_durable_evidence_bundle_v1(output_dir=out)


def test_deterministic_index_and_manifest(tmp_path, ssot_durable_output_dir) -> None:
    metric_bindings, definition_binding, result_binding, _ = _produce_bound_chain(
        tmp_path, ssot_durable_output_dir
    )
    out_a = _durable_output(tmp_path, "det_a")
    out_b = _durable_output(tmp_path, "det_b")
    produce_comparison_common_durable_evidence_bundle_v1(
        definition_bound_bundle_dir=definition_binding,
        result_bound_bundle_dir=result_binding,
        metric_input_bound_bundle_dirs=metric_bindings,
        output_dir=out_a,
    )
    produce_comparison_common_durable_evidence_bundle_v1(
        definition_bound_bundle_dir=definition_binding,
        result_bound_bundle_dir=result_binding,
        metric_input_bound_bundle_dirs=metric_bindings,
        output_dir=out_b,
    )
    index_a = (out_a / INDEX_ARTIFACT_REL).read_text(encoding="utf-8")
    index_b = (out_b / INDEX_ARTIFACT_REL).read_text(encoding="utf-8")
    assert index_a == index_b
    assert (out_a / "MANIFEST.sha256").read_text(encoding="utf-8") == (
        out_b / "MANIFEST.sha256"
    ).read_text(encoding="utf-8")


def test_authority_invariants_and_forbidden_keys(tmp_path, ssot_durable_output_dir) -> None:
    metric_bindings, definition_binding, result_binding, _ = _produce_bound_chain(
        tmp_path, ssot_durable_output_dir
    )
    out = _durable_output(tmp_path, "auth")
    produce_comparison_common_durable_evidence_bundle_v1(
        definition_bound_bundle_dir=definition_binding,
        result_bound_bundle_dir=result_binding,
        metric_input_bound_bundle_dirs=metric_bindings,
        output_dir=out,
    )
    index = read_manifest(out / INDEX_ARTIFACT_REL)
    assert index["evidence_does_not_authorize_runtime"] is True
    assert index["comparison_authority_invariants"] == COMPARISON_AUTHORITY_INVARIANTS
    assert index["binding_relation"] == BINDING_RELATION
    for forbidden in ("winner", "promotion", "completion", "runtime_authorized"):
        assert forbidden not in index


def test_missing_metric_input_binding(tmp_path, ssot_durable_output_dir) -> None:
    metric_bindings, definition_binding, result_binding, _ = _produce_bound_chain(
        tmp_path, ssot_durable_output_dir
    )
    out = _durable_output(tmp_path, "missing_mi")
    with pytest.raises(ComparisonCommonDurableEvidenceBindingError, match="cardinality"):
        produce_comparison_common_durable_evidence_bundle_v1(
            definition_bound_bundle_dir=definition_binding,
            result_bound_bundle_dir=result_binding,
            metric_input_bound_bundle_dirs=[metric_bindings[0]],
            output_dir=out,
        )


def test_extra_metric_input_binding(tmp_path, ssot_durable_output_dir) -> None:
    metric_bindings, definition_binding, result_binding, _ = _produce_bound_chain(
        tmp_path, ssot_durable_output_dir
    )
    extra_copy = ssot_durable_output_dir / "metric_input_binding_extra"
    shutil.copytree(metric_bindings[0], extra_copy)
    out = _durable_output(tmp_path, "extra_mi")
    with pytest.raises(ComparisonCommonDurableEvidenceBindingError, match="cardinality"):
        produce_comparison_common_durable_evidence_bundle_v1(
            definition_bound_bundle_dir=definition_binding,
            result_bound_bundle_dir=result_binding,
            metric_input_bound_bundle_dirs=[*metric_bindings, extra_copy],
            output_dir=out,
        )


def test_duplicate_metric_input_binding_path(tmp_path, ssot_durable_output_dir) -> None:
    metric_bindings, definition_binding, result_binding, _ = _produce_bound_chain(
        tmp_path, ssot_durable_output_dir
    )
    out = _durable_output(tmp_path, "dup_path")
    with pytest.raises(ComparisonCommonDurableEvidenceBindingError, match="duplicate metric input"):
        produce_comparison_common_durable_evidence_bundle_v1(
            definition_bound_bundle_dir=definition_binding,
            result_bound_bundle_dir=result_binding,
            metric_input_bound_bundle_dirs=[metric_bindings[0], metric_bindings[0]],
            output_dir=out,
        )


def test_definition_result_definition_id_mismatch(tmp_path, ssot_durable_output_dir) -> None:
    metric_bindings, definition_binding, result_binding, _ = _produce_bound_chain(
        tmp_path, ssot_durable_output_dir
    )
    result_index_path = result_binding / RESULT_INDEX_ARTIFACT_REL
    result_index = read_manifest(result_index_path)
    mutated = deepcopy(result_index)
    mutated["comparison_definition_id"] = "00000000-0000-4000-8000-000000000001"
    result_index_path.write_text(json.dumps(mutated), encoding="utf-8")
    out = _durable_output(tmp_path, "id_mismatch")
    with pytest.raises(Exception, match="MANIFEST.sha256 verification failed"):
        produce_comparison_common_durable_evidence_bundle_v1(
            definition_bound_bundle_dir=definition_binding,
            result_bound_bundle_dir=result_binding,
            metric_input_bound_bundle_dirs=metric_bindings,
            output_dir=out,
        )


def test_input_path_order_does_not_change_published_order(
    tmp_path, ssot_durable_output_dir
) -> None:
    metric_bindings, definition_binding, result_binding, _ = _produce_bound_chain(
        tmp_path, ssot_durable_output_dir
    )
    definition_index = read_manifest(definition_binding / DEFINITION_INDEX_ARTIFACT_REL)
    out = _durable_output(tmp_path, "path_order")
    produce_comparison_common_durable_evidence_bundle_v1(
        definition_bound_bundle_dir=definition_binding,
        result_bound_bundle_dir=result_binding,
        metric_input_bound_bundle_dirs=[metric_bindings[1], metric_bindings[0]],
        output_dir=out,
    )
    index = read_manifest(out / INDEX_ARTIFACT_REL)
    assert [
        item["definition_input_ref"] for item in index["metric_input_binding_refs"]
    ] == definition_index["definition_input_refs"]


def test_unverified_metric_input_bundle(tmp_path, ssot_durable_output_dir) -> None:
    metric_bindings, definition_binding, result_binding, _ = _produce_bound_chain(
        tmp_path, ssot_durable_output_dir
    )
    fake = tmp_path / "fake_metric_bundle"
    fake.mkdir()
    (fake / "comparison_metric_input_durable_evidence_binding_index_v1.json").write_text(
        "{}", encoding="utf-8"
    )
    out = _durable_output(tmp_path, "unverified")
    with pytest.raises(Exception, match="MANIFEST.sha256"):
        produce_comparison_common_durable_evidence_bundle_v1(
            definition_bound_bundle_dir=definition_binding,
            result_bound_bundle_dir=result_binding,
            metric_input_bound_bundle_dirs=[fake, metric_bindings[1]],
            output_dir=out,
        )


def test_corrupted_sub_bundle_manifest(tmp_path, ssot_durable_output_dir) -> None:
    metric_bindings, definition_binding, result_binding, _ = _produce_bound_chain(
        tmp_path, ssot_durable_output_dir
    )
    (metric_bindings[0] / "MANIFEST.sha256").write_text("broken", encoding="utf-8")
    out = _durable_output(tmp_path, "broken_manifest")
    with pytest.raises(Exception, match="MANIFEST.sha256"):
        produce_comparison_common_durable_evidence_bundle_v1(
            definition_bound_bundle_dir=definition_binding,
            result_bound_bundle_dir=result_binding,
            metric_input_bound_bundle_dirs=metric_bindings,
            output_dir=out,
        )


def test_output_collision(tmp_path, ssot_durable_output_dir) -> None:
    metric_bindings, definition_binding, result_binding, _ = _produce_bound_chain(
        tmp_path, ssot_durable_output_dir
    )
    out = _durable_output(tmp_path, "exists")
    out.mkdir()
    with pytest.raises(ComparisonCommonDurableEvidenceBindingError, match="already exists"):
        produce_comparison_common_durable_evidence_bundle_v1(
            definition_bound_bundle_dir=definition_binding,
            result_bound_bundle_dir=result_binding,
            metric_input_bound_bundle_dirs=metric_bindings,
            output_dir=out,
        )


def test_path_traversal_relative_path_rejected() -> None:
    with pytest.raises(ComparisonCommonDurableEvidenceBindingError, match="traverse upward"):
        from src.meta.learning_loop.comparison_common_durable_evidence_binding_v1 import (
            _validate_bundle_relative_path,
        )

        _validate_bundle_relative_path("../escape")


def test_symlink_escape_rejected(tmp_path, ssot_durable_output_dir) -> None:
    metric_bindings, definition_binding, result_binding, _ = _produce_bound_chain(
        tmp_path, ssot_durable_output_dir
    )
    link = tmp_path / "symlink_bundle"
    link.symlink_to(metric_bindings[0])
    out = _durable_output(tmp_path, "symlink")
    with pytest.raises(ComparisonCommonDurableEvidenceBindingError, match="symlink"):
        produce_comparison_common_durable_evidence_bundle_v1(
            definition_bound_bundle_dir=definition_binding,
            result_bound_bundle_dir=result_binding,
            metric_input_bound_bundle_dirs=[link, metric_bindings[1]],
            output_dir=out,
        )


def test_max_cardinality_constant_enforced() -> None:
    assert MIN_METRIC_INPUT_BINDINGS == 2
    assert MAX_METRIC_INPUT_BINDINGS == 32


def test_no_forbidden_runtime_imports() -> None:
    module_path = Path(__file__).resolve().parents[2] / (
        "src/meta/learning_loop/comparison_common_durable_evidence_binding_v1.py"
    )
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    forbidden = {"src.execution", "src.risk", "mlflow"}
    assert not modules & forbidden
