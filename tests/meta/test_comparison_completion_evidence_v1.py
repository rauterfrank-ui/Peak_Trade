"""Contract tests for learning loop comparison completion evidence v1."""

from __future__ import annotations

import ast
import json
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

import pytest

pytest_plugins = ["tests.meta.comparison_ssot_v1_fixtures"]

from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256
from src.meta.learning_loop.comparison_checkpoint_v1 import (
    INDEX_ARTIFACT_REL as CHECKPOINT_INDEX_ARTIFACT_REL,
    produce_comparison_checkpoint_v1,
)
from src.meta.learning_loop.comparison_common_durable_evidence_binding_v1 import (
    INDEX_ARTIFACT_REL as COMMON_INDEX_ARTIFACT_REL,
    produce_comparison_common_durable_evidence_bundle_v1,
)
from src.meta.learning_loop.comparison_completion_evidence_v1 import (
    ARTIFACT_REL,
    AUTHORITY_LEVEL,
    COMPLETION_AUTHORITY_INVARIANTS,
    CONTRACT_NAME,
    CONTRACT_VERSION,
    EVIDENCE_LEVEL,
    PRODUCER_VERSION,
    SELF_VERIFICATION_REL,
    ComparisonCompletionEvidenceError,
    build_completion_evidence_v1,
    produce_comparison_completion_evidence_v1,
    reverify_comparison_completion_evidence_v1,
    serialize_completion_evidence_v1,
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
        "src.meta.learning_loop.comparison_completion_evidence_v1.is_under_tmp",
        "src.meta.learning_loop.comparison_checkpoint_v1.is_under_tmp",
        "src.meta.learning_loop.comparison_common_durable_evidence_binding_v1.is_under_tmp",
        "src.meta.learning_loop.comparison_metric_input_durable_evidence_binding_v1.is_under_tmp",
        "src.meta.learning_loop.comparison_ssot_definition_durable_evidence_binding_v1.is_under_tmp",
        "src.meta.learning_loop.comparison_ssot_result_durable_evidence_binding_v1.is_under_tmp",
    ):
        monkeypatch.setattr(target, lambda _path: False)


def _durable_output(tmp_path: Path, name: str = "completion_out") -> Path:
    root = tmp_path / "evidence_root"
    root.mkdir(exist_ok=True)
    return root / name


def _produce_common_bundle(tmp_path: Path, durable_root: Path) -> tuple[Path, str]:
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
    metric_bindings = []
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
    return common_out, offline.comparison_definition_id


def _produce_checkpoint(tmp_path: Path, durable_root: Path, *, name: str = "checkpoint") -> Path:
    common_out, _ = _produce_common_bundle(tmp_path, durable_root)
    checkpoint_out = durable_root / name
    produce_comparison_checkpoint_v1(common_bundle_dir=common_out, output_dir=checkpoint_out)
    return checkpoint_out


def test_happy_path_completion_from_verified_checkpoint(tmp_path, ssot_durable_output_dir) -> None:
    checkpoint_out = _produce_checkpoint(tmp_path, ssot_durable_output_dir)
    out = _durable_output(tmp_path)
    result = produce_comparison_completion_evidence_v1(
        checkpoint_bundle_dir=checkpoint_out,
        output_dir=out,
    )
    assert result.artifact_id
    assert (out / ARTIFACT_REL).is_file()
    assert (out / SELF_VERIFICATION_REL).is_file()
    ok, _ = verify_manifest_sha256(out)
    assert ok is True


def test_deterministic_output_and_manifest(tmp_path, ssot_durable_output_dir) -> None:
    checkpoint_out = _produce_checkpoint(tmp_path, ssot_durable_output_dir, name="cp_det")
    out_a = _durable_output(tmp_path, "det_a")
    out_b = _durable_output(tmp_path, "det_b")
    produce_comparison_completion_evidence_v1(
        checkpoint_bundle_dir=checkpoint_out,
        output_dir=out_a,
    )
    produce_comparison_completion_evidence_v1(
        checkpoint_bundle_dir=checkpoint_out,
        output_dir=out_b,
    )
    assert (out_a / ARTIFACT_REL).read_text(encoding="utf-8") == (out_b / ARTIFACT_REL).read_text(
        encoding="utf-8"
    )
    assert (out_a / SELF_VERIFICATION_REL).read_text(encoding="utf-8") == (
        out_b / SELF_VERIFICATION_REL
    ).read_text(encoding="utf-8")
    assert (out_a / "MANIFEST.sha256").read_text(encoding="utf-8") == (
        out_b / "MANIFEST.sha256"
    ).read_text(encoding="utf-8")


def test_reverify_without_producers(tmp_path, ssot_durable_output_dir) -> None:
    checkpoint_out = _produce_checkpoint(tmp_path, ssot_durable_output_dir, name="cp_replay")
    out = _durable_output(tmp_path, "replay")
    produce_comparison_completion_evidence_v1(
        checkpoint_bundle_dir=checkpoint_out,
        output_dir=out,
    )
    reverify_comparison_completion_evidence_v1(output_dir=out)


def test_required_contract_fields(tmp_path, ssot_durable_output_dir) -> None:
    checkpoint_out = _produce_checkpoint(tmp_path, ssot_durable_output_dir)
    out = _durable_output(tmp_path, "fields")
    produce_comparison_completion_evidence_v1(
        checkpoint_bundle_dir=checkpoint_out,
        output_dir=out,
    )
    evidence = read_manifest(out / ARTIFACT_REL)
    assert evidence["contract_name"] == CONTRACT_NAME
    assert evidence["contract_version"] == CONTRACT_VERSION
    assert evidence["producer_version"] == PRODUCER_VERSION
    assert evidence["evidence_level"] == EVIDENCE_LEVEL
    assert evidence["authority_level"] == AUTHORITY_LEVEL
    assert evidence["is_completion_evidence"] is True
    assert evidence["capabilities"] == []


def test_non_authorizing_flags(tmp_path, ssot_durable_output_dir) -> None:
    checkpoint_out = _produce_checkpoint(tmp_path, ssot_durable_output_dir)
    out = _durable_output(tmp_path, "flags")
    produce_comparison_completion_evidence_v1(
        checkpoint_bundle_dir=checkpoint_out,
        output_dir=out,
    )
    evidence = read_manifest(out / ARTIFACT_REL)
    assert evidence["evidence_does_not_authorize_promotion"] is True
    assert evidence["evidence_does_not_authorize_runtime"] is True
    assert evidence["completion_does_not_select"] is True
    assert evidence["completion_does_not_accept"] is True
    assert evidence["completion_does_not_deploy"] is True
    assert evidence["completion_does_not_activate"] is True
    assert evidence["completion_does_not_create_order_intent"] is True


def test_self_verification_pass(tmp_path, ssot_durable_output_dir) -> None:
    checkpoint_out = _produce_checkpoint(tmp_path, ssot_durable_output_dir)
    out = _durable_output(tmp_path, "self")
    produce_comparison_completion_evidence_v1(
        checkpoint_bundle_dir=checkpoint_out,
        output_dir=out,
    )
    self_payload = read_manifest(out / SELF_VERIFICATION_REL)
    assert self_payload["overall_status"] == "PASS"


def test_missing_checkpoint_dir(tmp_path) -> None:
    out = _durable_output(tmp_path)
    with pytest.raises(ComparisonCompletionEvidenceError, match="must be a directory"):
        produce_comparison_completion_evidence_v1(
            checkpoint_bundle_dir=tmp_path / "missing",
            output_dir=out,
        )


def test_missing_manifest_on_checkpoint(tmp_path, ssot_durable_output_dir) -> None:
    checkpoint_out = _produce_checkpoint(tmp_path, ssot_durable_output_dir)
    (checkpoint_out / "MANIFEST.sha256").unlink()
    out = _durable_output(tmp_path)
    with pytest.raises(ComparisonCompletionEvidenceError, match="MANIFEST.sha256"):
        produce_comparison_completion_evidence_v1(
            checkpoint_bundle_dir=checkpoint_out,
            output_dir=out,
        )


def test_tampered_checkpoint_manifest(tmp_path, ssot_durable_output_dir) -> None:
    checkpoint_out = _produce_checkpoint(tmp_path, ssot_durable_output_dir)
    (checkpoint_out / "MANIFEST.sha256").write_text("broken", encoding="utf-8")
    out = _durable_output(tmp_path)
    with pytest.raises(ComparisonCompletionEvidenceError, match="MANIFEST.sha256"):
        produce_comparison_completion_evidence_v1(
            checkpoint_bundle_dir=checkpoint_out,
            output_dir=out,
        )


def test_wrong_input_artifact_type(tmp_path, ssot_durable_output_dir) -> None:
    common_out, _ = _produce_common_bundle(tmp_path, ssot_durable_output_dir)
    out = _durable_output(tmp_path)
    with pytest.raises(
        ComparisonCompletionEvidenceError, match="comparison_checkpoint_index_v1.json"
    ):
        produce_comparison_completion_evidence_v1(
            checkpoint_bundle_dir=common_out,
            output_dir=out,
        )


def test_input_already_completion_evidence_rejected(tmp_path, ssot_durable_output_dir) -> None:
    checkpoint_out = _produce_checkpoint(tmp_path, ssot_durable_output_dir)
    completion_out = _durable_output(tmp_path, "first_completion")
    produce_comparison_completion_evidence_v1(
        checkpoint_bundle_dir=checkpoint_out,
        output_dir=completion_out,
    )
    second = _durable_output(tmp_path, "second_completion")
    with pytest.raises(
        ComparisonCompletionEvidenceError, match="comparison_checkpoint_index_v1.json"
    ):
        produce_comparison_completion_evidence_v1(
            checkpoint_bundle_dir=completion_out,
            output_dir=second,
        )


def test_tampered_output_after_produce(tmp_path, ssot_durable_output_dir) -> None:
    checkpoint_out = _produce_checkpoint(tmp_path, ssot_durable_output_dir)
    out = _durable_output(tmp_path, "tamper")
    produce_comparison_completion_evidence_v1(
        checkpoint_bundle_dir=checkpoint_out,
        output_dir=out,
    )
    evidence = read_manifest(out / ARTIFACT_REL)
    evidence["is_completion_evidence"] = False
    (out / ARTIFACT_REL).write_text(json.dumps(evidence), encoding="utf-8")
    with pytest.raises(ComparisonCompletionEvidenceError):
        reverify_comparison_completion_evidence_v1(output_dir=out)


def test_forbidden_promotion_capability_rejected() -> None:
    checkpoint_dir = Path("/var/evidence/checkpoint")
    invariants = {
        "comparison_is_descriptive_only": True,
        "comparison_does_not_select": True,
        "comparison_does_not_accept": True,
        "comparison_does_not_promote": True,
        "comparison_does_not_authorize_runtime": True,
    }
    evidence = build_completion_evidence_v1(
        checkpoint_bundle_dir=checkpoint_dir,
        checkpoint_index={
            "comparison_definition_id": "00000000-0000-4000-8000-000000000099",
            "comparison_authority_invariants": invariants,
            "integrity": {"content_sha256": "a" * 64},
        },
        input_manifest_digest="b" * 64,
    )
    evidence["capabilities"] = ["CAN_PROMOTE_ARTIFACT"]
    with pytest.raises(ComparisonCompletionEvidenceError, match="forbidden capability"):
        serialize_completion_evidence_v1(evidence)


def test_forbidden_winner_field_rejected() -> None:
    checkpoint_dir = Path("/var/evidence/checkpoint")
    invariants = {
        "comparison_is_descriptive_only": True,
        "comparison_does_not_select": True,
        "comparison_does_not_accept": True,
        "comparison_does_not_promote": True,
        "comparison_does_not_authorize_runtime": True,
    }
    evidence = build_completion_evidence_v1(
        checkpoint_bundle_dir=checkpoint_dir,
        checkpoint_index={
            "comparison_definition_id": "00000000-0000-4000-8000-000000000099",
            "comparison_authority_invariants": invariants,
            "integrity": {"content_sha256": "a" * 64},
        },
        input_manifest_digest="b" * 64,
    )
    evidence["winner"] = True
    with pytest.raises(ComparisonCompletionEvidenceError, match="forbidden key: winner"):
        serialize_completion_evidence_v1(evidence)


def test_wrong_evidence_level_rejected() -> None:
    checkpoint_dir = Path("/var/evidence/checkpoint")
    invariants = {
        "comparison_is_descriptive_only": True,
        "comparison_does_not_select": True,
        "comparison_does_not_accept": True,
        "comparison_does_not_promote": True,
        "comparison_does_not_authorize_runtime": True,
    }
    evidence = build_completion_evidence_v1(
        checkpoint_bundle_dir=checkpoint_dir,
        checkpoint_index={
            "comparison_definition_id": "00000000-0000-4000-8000-000000000099",
            "comparison_authority_invariants": invariants,
            "integrity": {"content_sha256": "a" * 64},
        },
        input_manifest_digest="b" * 64,
    )
    evidence["evidence_level"] = "LEVEL_2"
    with pytest.raises(ComparisonCompletionEvidenceError, match="evidence_level"):
        serialize_completion_evidence_v1(evidence)


def test_existing_output_fail_closed(tmp_path, ssot_durable_output_dir) -> None:
    checkpoint_out = _produce_checkpoint(tmp_path, ssot_durable_output_dir)
    out = _durable_output(tmp_path, "exists")
    out.mkdir()
    with pytest.raises(ComparisonCompletionEvidenceError, match="already exists"):
        produce_comparison_completion_evidence_v1(
            checkpoint_bundle_dir=checkpoint_out,
            output_dir=out,
        )


def test_checkpoint_not_mutated(tmp_path, ssot_durable_output_dir) -> None:
    checkpoint_out = _produce_checkpoint(tmp_path, ssot_durable_output_dir)
    before = {
        rel.as_posix(): rel.read_bytes()
        for rel in checkpoint_out.rglob("*")
        if rel.is_file() and not rel.is_symlink()
    }
    out = _durable_output(tmp_path, "nomut")
    produce_comparison_completion_evidence_v1(
        checkpoint_bundle_dir=checkpoint_out,
        output_dir=out,
    )
    after = {
        rel.as_posix(): rel.read_bytes()
        for rel in checkpoint_out.rglob("*")
        if rel.is_file() and not rel.is_symlink()
    }
    assert before == after


def test_ast_no_forbidden_runtime_imports() -> None:
    module_path = Path(__file__).resolve().parents[2] / (
        "src/meta/learning_loop/comparison_completion_evidence_v1.py"
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


def test_no_checkpoint_producer_rerun(tmp_path, ssot_durable_output_dir) -> None:
    checkpoint_out = _produce_checkpoint(tmp_path, ssot_durable_output_dir)
    out = _durable_output(tmp_path, "no_cp_producer")
    with patch(
        "src.meta.learning_loop.comparison_checkpoint_v1.produce_comparison_checkpoint_v1"
    ) as mocked:
        produce_comparison_completion_evidence_v1(
            checkpoint_bundle_dir=checkpoint_out,
            output_dir=out,
        )
        mocked.assert_not_called()


def test_single_parent_ref(tmp_path, ssot_durable_output_dir) -> None:
    checkpoint_out = _produce_checkpoint(tmp_path, ssot_durable_output_dir)
    out = _durable_output(tmp_path, "parent")
    produce_comparison_completion_evidence_v1(
        checkpoint_bundle_dir=checkpoint_out,
        output_dir=out,
    )
    evidence = read_manifest(out / ARTIFACT_REL)
    assert len(evidence["parent_artifact_refs"]) == 1
    assert evidence["parent_artifact_refs"][0]["ref_type"] == "comparison_checkpoint_v1"


def test_completion_authority_invariants_present(tmp_path, ssot_durable_output_dir) -> None:
    checkpoint_out = _produce_checkpoint(tmp_path, ssot_durable_output_dir)
    out = _durable_output(tmp_path, "invariants")
    produce_comparison_completion_evidence_v1(
        checkpoint_bundle_dir=checkpoint_out,
        output_dir=out,
    )
    evidence = read_manifest(out / ARTIFACT_REL)
    assert evidence["completion_authority_invariants"] == COMPLETION_AUTHORITY_INVARIANTS
