"""Contract tests for Package G offline learning manifest durable evidence binding v1."""

from __future__ import annotations

import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256
from src.governance.promotion_loop.candidate_lineage_manifest_v1 import (
    LineageRefType,
    LineageRelation,
    build_candidate_lineage_manifest_v1_from_producer_input,
    serialize_candidate_lineage_manifest_v1,
    write_candidate_lineage_manifest_v1_atomic,
)
from src.meta.learning_loop.config_patch_manifest_v1 import (
    build_empty_config_patch_manifest_v1,
    validate_config_patch_manifest_v1,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256
from src.meta.learning_loop.manifest_bridge_v1 import (
    build_config_patch_manifest_v1_from_learning_input,
    write_config_patch_manifest_v1_atomic,
)
from src.meta.learning_loop.manifest_durable_evidence_binding_v1 import (
    CONFIG_PATCH_ARTIFACT_REL,
    INDEX_ARTIFACT_REL,
    LINEAGE_ARTIFACT_REL,
    ManifestDurableEvidenceBindingError,
    build_binding_index_v1,
    check_reference_consistency,
    produce_learning_manifest_durable_evidence_bundle_v1,
    serialize_binding_index_v1,
)
from src.meta.learning_loop.models import PatchStatus

FIXED_NOW = datetime(2026, 6, 27, 18, 0, 0, tzinfo=timezone.utc)
CONFIG_ID = "11111111-1111-4111-8111-111111111111"
LINEAGE_ID = "22222222-2222-4222-8222-222222222222"
CONTRACT_REF = "33333333-3333-4333-8333-333333333333"


@pytest.fixture(autouse=True)
def _allow_tmp_output(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "src.meta.learning_loop.manifest_durable_evidence_binding_v1.is_under_tmp",
        lambda _path: False,
    )


def _minimal_lineage_input() -> dict:
    return {
        "lineage_manifest_id": LINEAGE_ID,
        "candidate_id": "candidate-g-test",
        "candidate_type": "config_patch_bundle",
        "candidate_contract_ref": CONTRACT_REF,
        "refs": [
            {
                "ref_type": LineageRefType.EXPERIMENT.value,
                "ref_id": "exp-g-1",
                "relation": LineageRelation.SOURCES.value,
                "owner_domain": "experiments/base",
                "required": True,
            }
        ],
        "created_at": FIXED_NOW.isoformat(),
        "created_by": "package_g_binding_tests",
    }


def _full_lineage_input() -> dict:
    payload = _minimal_lineage_input()
    payload["refs"] = [
        *_minimal_lineage_input()["refs"],
        {
            "ref_type": LineageRefType.EVIDENCE_OPS.value,
            "ref_id": "evidence-ref-g",
            "relation": LineageRelation.RETAINS.value,
            "owner_domain": "primary_evidence_retention",
            "required": True,
            "digest": "b" * 64,
        },
    ]
    return payload


def _write_minimal_config_patch(path: Path, *, empty: bool = True) -> None:
    if empty:
        manifest = build_empty_config_patch_manifest_v1(
            manifest_id=CONFIG_ID,
            lineage_manifest_ref=LINEAGE_ID,
            generated_at=FIXED_NOW,
        )
    else:
        manifest = build_config_patch_manifest_v1_from_learning_input(
            {
                "patches": [
                    {
                        "id": "patch-g-1",
                        "target": "research.offline.window_days",
                        "old_value": 30,
                        "new_value": 45,
                        "status": PatchStatus.APPLIED_OFFLINE.value,
                        "reason": "package g binding test",
                    }
                ]
            },
            manifest_id=CONFIG_ID,
            lineage_manifest_ref=LINEAGE_ID,
            generated_at=FIXED_NOW,
        )
    write_config_patch_manifest_v1_atomic(manifest, path)


def _write_lineage(path: Path, *, full: bool = False) -> None:
    raw = _full_lineage_input() if full else _minimal_lineage_input()
    manifest = build_candidate_lineage_manifest_v1_from_producer_input(raw, created_at=FIXED_NOW)
    write_candidate_lineage_manifest_v1_atomic(manifest, path)


def _sources_dir(tmp_path: Path) -> Path:
    path = tmp_path / "sources"
    path.mkdir(exist_ok=True)
    return path


def _durable_output(tmp_path: Path, name: str = "bundle") -> Path:
    root = tmp_path / "evidence_root"
    root.mkdir(exist_ok=True)
    return root / name


@pytest.fixture
def sources(tmp_path: Path) -> Path:
    return _sources_dir(tmp_path)


def test_minimal_manifest_pair_binds_successfully(tmp_path: Path, sources: Path) -> None:
    config_path = sources / "config.json"
    lineage_path = sources / "lineage.json"
    out = _durable_output(tmp_path)
    _write_minimal_config_patch(config_path)
    _write_lineage(lineage_path)

    result = produce_learning_manifest_durable_evidence_bundle_v1(
        config_patch_manifest_path=config_path,
        candidate_lineage_manifest_path=lineage_path,
        output_dir=out,
    )

    assert result.config_patch_manifest_id == CONFIG_ID
    assert result.candidate_lineage_manifest_id == LINEAGE_ID
    assert (out / CONFIG_PATCH_ARTIFACT_REL).is_file()
    assert (out / LINEAGE_ARTIFACT_REL).is_file()
    assert (out / INDEX_ARTIFACT_REL).is_file()
    ok, _ = verify_manifest_sha256(out)
    assert ok is True


def test_full_manifest_pair_passes_contract_validation(tmp_path: Path, sources: Path) -> None:
    config_path = sources / "config.json"
    lineage_path = sources / "lineage.json"
    out = _durable_output(tmp_path, "full")
    _write_minimal_config_patch(config_path, empty=False)
    _write_lineage(lineage_path, full=True)

    produce_learning_manifest_durable_evidence_bundle_v1(
        config_patch_manifest_path=config_path,
        candidate_lineage_manifest_path=lineage_path,
        output_dir=out,
    )
    config_payload = json.loads((out / CONFIG_PATCH_ARTIFACT_REL).read_text(encoding="utf-8"))
    valid, phase, errors, _ = validate_config_patch_manifest_v1(config_payload)
    assert valid is True, (phase, errors)


def test_reference_consistency_pass_and_fail() -> None:
    cross = check_reference_consistency(
        config_patch_manifest_id=CONFIG_ID,
        config_patch_lineage_manifest_ref=LINEAGE_ID,
        candidate_lineage_manifest_id=LINEAGE_ID,
    )
    assert cross.lineage_manifest_ref_bound is True

    with pytest.raises(ManifestDurableEvidenceBindingError, match="does not match"):
        check_reference_consistency(
            config_patch_manifest_id=CONFIG_ID,
            config_patch_lineage_manifest_ref="99999999-9999-4999-8999-999999999999",
            candidate_lineage_manifest_id=LINEAGE_ID,
        )


def test_binding_index_has_no_payload_duplication(tmp_path: Path, sources: Path) -> None:
    config_path = sources / "config.json"
    lineage_path = sources / "lineage.json"
    out = _durable_output(tmp_path, "index")
    _write_minimal_config_patch(config_path, empty=False)
    _write_lineage(lineage_path)

    produce_learning_manifest_durable_evidence_bundle_v1(
        config_patch_manifest_path=config_path,
        candidate_lineage_manifest_path=lineage_path,
        output_dir=out,
    )
    index = json.loads((out / INDEX_ARTIFACT_REL).read_text(encoding="utf-8"))
    assert index["evidence_does_not_authorize_runtime"] is True
    assert "patches" not in index
    assert "strategy" not in index
    assert "old_value" not in json.dumps(index)
    assert all(not Path(item["relative_path"]).is_absolute() for item in index["artifacts"])


def test_build_binding_index_rejects_forbidden_payload_key() -> None:
    from src.meta.learning_loop.manifest_durable_evidence_binding_v1 import BoundArtifactRecord

    cross = check_reference_consistency(
        config_patch_manifest_id=CONFIG_ID,
        config_patch_lineage_manifest_ref=LINEAGE_ID,
        candidate_lineage_manifest_id=LINEAGE_ID,
    )
    artifacts = (
        BoundArtifactRecord("config_patch_manifest_v1", CONFIG_PATCH_ARTIFACT_REL, "a" * 64),
    )
    manifest = build_empty_config_patch_manifest_v1(
        manifest_id=CONFIG_ID,
        lineage_manifest_ref=LINEAGE_ID,
        generated_at=FIXED_NOW,
    )
    index = build_binding_index_v1(
        config_patch_manifest_id=CONFIG_ID,
        candidate_lineage_manifest_id=LINEAGE_ID,
        cross_references=cross,
        artifacts=artifacts,
        futures_scope_ref=manifest.source_scope,
        trading_logic_immutability_ref=manifest.trading_logic_immutability_ref,
    )
    index["patches"] = []
    with pytest.raises(ManifestDurableEvidenceBindingError, match="forbidden key"):
        serialize_binding_index_v1(index)


def test_deterministic_index_and_manifest(tmp_path: Path, sources: Path) -> None:
    config_path = sources / "config.json"
    lineage_path = sources / "lineage.json"
    _write_minimal_config_patch(config_path)
    _write_lineage(lineage_path)

    out1 = _durable_output(tmp_path, "det1")
    out2 = _durable_output(tmp_path, "det2")
    produce_learning_manifest_durable_evidence_bundle_v1(
        config_patch_manifest_path=config_path,
        candidate_lineage_manifest_path=lineage_path,
        output_dir=out1,
    )
    produce_learning_manifest_durable_evidence_bundle_v1(
        config_patch_manifest_path=config_path,
        candidate_lineage_manifest_path=lineage_path,
        output_dir=out2,
    )

    index1 = (out1 / INDEX_ARTIFACT_REL).read_bytes()
    index2 = (out2 / INDEX_ARTIFACT_REL).read_bytes()
    manifest1 = (out1 / "MANIFEST.sha256").read_bytes()
    manifest2 = (out2 / "MANIFEST.sha256").read_bytes()
    assert index1 == index2
    assert manifest1 == manifest2


def test_byte_identical_artifact_copies(tmp_path: Path, sources: Path) -> None:
    config_path = sources / "config.json"
    lineage_path = sources / "lineage.json"
    out = _durable_output(tmp_path, "bytes")
    _write_minimal_config_patch(config_path)
    _write_lineage(lineage_path)

    produce_learning_manifest_durable_evidence_bundle_v1(
        config_patch_manifest_path=config_path,
        candidate_lineage_manifest_path=lineage_path,
        output_dir=out,
    )
    assert (out / CONFIG_PATCH_ARTIFACT_REL).read_bytes() == config_path.read_bytes()
    assert (out / LINEAGE_ARTIFACT_REL).read_bytes() == lineage_path.read_bytes()


def test_existing_output_dir_fail_closed(tmp_path: Path, sources: Path) -> None:
    config_path = sources / "config.json"
    lineage_path = sources / "lineage.json"
    out = _durable_output(tmp_path, "exists")
    out.mkdir(parents=True)
    _write_minimal_config_patch(config_path)
    _write_lineage(lineage_path)

    with pytest.raises(ManifestDurableEvidenceBindingError, match="already exists"):
        produce_learning_manifest_durable_evidence_bundle_v1(
            config_patch_manifest_path=config_path,
            candidate_lineage_manifest_path=lineage_path,
            output_dir=out,
        )


def test_missing_source_fail_closed(tmp_path: Path) -> None:
    out = _durable_output(tmp_path, "missing")
    with pytest.raises(ManifestDurableEvidenceBindingError, match="not found"):
        produce_learning_manifest_durable_evidence_bundle_v1(
            config_patch_manifest_path=tmp_path / "missing.json",
            candidate_lineage_manifest_path=tmp_path / "missing2.json",
            output_dir=out,
        )


def test_symlink_source_rejected(tmp_path: Path, sources: Path) -> None:
    config_path = sources / "config.json"
    lineage_path = sources / "lineage.json"
    _write_minimal_config_patch(config_path)
    _write_lineage(lineage_path)
    link = tmp_path / "config_link.json"
    link.symlink_to(config_path)
    out = _durable_output(tmp_path, "symlink")

    with pytest.raises(ManifestDurableEvidenceBindingError, match="symlink"):
        produce_learning_manifest_durable_evidence_bundle_v1(
            config_patch_manifest_path=link,
            candidate_lineage_manifest_path=lineage_path,
            output_dir=out,
        )


def test_copy_failure_leaves_no_final_bundle(
    tmp_path: Path, sources: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config_path = sources / "config.json"
    lineage_path = sources / "lineage.json"
    out = _durable_output(tmp_path, "copy_fail")
    _write_minimal_config_patch(config_path)
    _write_lineage(lineage_path)

    def _boom(src: Path, dst: Path) -> str:
        raise OSError("copy failed")

    monkeypatch.setattr(
        "src.meta.learning_loop.manifest_durable_evidence_binding_v1._copy_byte_identical",
        _boom,
    )
    with pytest.raises(OSError, match="copy failed"):
        produce_learning_manifest_durable_evidence_bundle_v1(
            config_patch_manifest_path=config_path,
            candidate_lineage_manifest_path=lineage_path,
            output_dir=out,
        )
    assert not out.exists()


def test_manifest_write_failure_cleans_up(
    tmp_path: Path, sources: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config_path = sources / "config.json"
    lineage_path = sources / "lineage.json"
    out = _durable_output(tmp_path, "manifest_fail")
    _write_minimal_config_patch(config_path)
    _write_lineage(lineage_path)

    def _fail_write(_root: Path) -> None:
        raise OSError("manifest write failed")

    monkeypatch.setattr(
        "src.meta.learning_loop.manifest_durable_evidence_binding_v1.write_manifest_sha256",
        _fail_write,
    )
    with pytest.raises(OSError, match="manifest write failed"):
        produce_learning_manifest_durable_evidence_bundle_v1(
            config_patch_manifest_path=config_path,
            candidate_lineage_manifest_path=lineage_path,
            output_dir=out,
        )
    assert not out.exists()


def test_verify_failure_before_publish_cleans_up(
    tmp_path: Path, sources: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config_path = sources / "config.json"
    lineage_path = sources / "lineage.json"
    out = _durable_output(tmp_path, "verify_fail")
    _write_minimal_config_patch(config_path)
    _write_lineage(lineage_path)

    monkeypatch.setattr(
        "src.meta.learning_loop.manifest_durable_evidence_binding_v1.verify_manifest_sha256",
        lambda _root: (False, "checksum mismatch"),
    )
    with pytest.raises(ManifestDurableEvidenceBindingError, match="verification failed"):
        produce_learning_manifest_durable_evidence_bundle_v1(
            config_patch_manifest_path=config_path,
            candidate_lineage_manifest_path=lineage_path,
            output_dir=out,
        )
    assert not out.exists()


def test_invalid_config_json_fail_closed(tmp_path: Path, sources: Path) -> None:
    config_path = sources / "config.json"
    lineage_path = sources / "lineage.json"
    out = _durable_output(tmp_path, "bad_config")
    config_path.write_text("{not json", encoding="utf-8")
    _write_lineage(lineage_path)

    with pytest.raises(ManifestDurableEvidenceBindingError):
        produce_learning_manifest_durable_evidence_bundle_v1(
            config_patch_manifest_path=config_path,
            candidate_lineage_manifest_path=lineage_path,
            output_dir=out,
        )


def test_output_under_tmp_rejected(
    tmp_path: Path, sources: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from scripts.ops.primary_evidence_retention_v0 import is_under_tmp as real_is_under_tmp

    monkeypatch.setattr(
        "src.meta.learning_loop.manifest_durable_evidence_binding_v1.is_under_tmp",
        real_is_under_tmp,
    )
    config_path = sources / "config.json"
    lineage_path = sources / "lineage.json"
    _write_minimal_config_patch(config_path)
    _write_lineage(lineage_path)
    out = Path("/tmp/peak_trade_pkg_g_binding_reject_test")

    try:
        with pytest.raises(ManifestDurableEvidenceBindingError, match="outside /tmp"):
            produce_learning_manifest_durable_evidence_bundle_v1(
                config_patch_manifest_path=config_path,
                candidate_lineage_manifest_path=lineage_path,
                output_dir=out,
            )
    finally:
        if out.exists():
            shutil.rmtree(out)


def test_no_runtime_imports_in_binding_module() -> None:
    import ast
    from pathlib import Path

    path = Path("src/meta/learning_loop/manifest_durable_evidence_binding_v1.py")
    tree = ast.parse(path.read_text(encoding="utf-8"))
    forbidden = ("promotion_loop.engine", "governance.promotion_loop.engine")
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            for token in forbidden:
                assert token not in node.module


def test_integrity_id_stable_for_index_payload() -> None:
    cross = check_reference_consistency(
        config_patch_manifest_id=CONFIG_ID,
        config_patch_lineage_manifest_ref=LINEAGE_ID,
        candidate_lineage_manifest_id=LINEAGE_ID,
    )
    manifest = build_empty_config_patch_manifest_v1(
        manifest_id=CONFIG_ID,
        lineage_manifest_ref=LINEAGE_ID,
        generated_at=FIXED_NOW,
    )
    from src.meta.learning_loop.manifest_durable_evidence_binding_v1 import BoundArtifactRecord

    artifacts = (
        BoundArtifactRecord("config_patch_manifest_v1", CONFIG_PATCH_ARTIFACT_REL, "c" * 64),
        BoundArtifactRecord("candidate_lineage_manifest_v1", LINEAGE_ARTIFACT_REL, "d" * 64),
    )
    index = build_binding_index_v1(
        config_patch_manifest_id=CONFIG_ID,
        candidate_lineage_manifest_id=LINEAGE_ID,
        cross_references=cross,
        artifacts=artifacts,
        futures_scope_ref=manifest.source_scope,
        trading_logic_immutability_ref=manifest.trading_logic_immutability_ref,
    )
    payload = dict(index)
    digest = payload.pop("integrity")
    assert digest["content_sha256"] == compute_content_sha256(payload)
