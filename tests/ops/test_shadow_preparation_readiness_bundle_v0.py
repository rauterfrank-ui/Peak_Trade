"""Focused tests for Shadow Preparation Readiness Bundle v0."""

from __future__ import annotations

import ast
import json
import socket
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from src.ops.shadow_preparation_readiness_bundle_v0 import (
    BUNDLE_STATUS_BLOCKED,
    BUNDLE_STATUS_ERROR,
    BUNDLE_STATUS_PASS,
    PACKAGE_MARKER,
    PRODUCER_FAMILY,
    SCHEMA_ID,
    build_shadow_preparation_readiness_bundle_v0,
    serialize_shadow_preparation_readiness_bundle_v0,
)
from src.ops.shadow_preparation_readiness_gate_v0 import (
    CANONICAL_STEP_29U_SEMANTICS_REFERENCE_KEY,
    DEFAULT_PROJECTION_OUTPUT_RELATIVE_PATH,
    PreparationStatusV0,
    evaluate_shadow_preparation_readiness_gate_v0,
    load_shadow_preparation_readiness_gate_config_v0,
)
from src.ops.shadow_preparation_readiness_offline_projection_pipeline_v0 import (
    PIPELINE_STATUS_BLOCKED,
    PIPELINE_STATUS_ERROR,
    PIPELINE_STATUS_PASS,
    READINESS_STATUS_BLOCKED,
    READINESS_STATUS_READY,
    ShadowPreparationReadinessOfflineProjectionPipelineResultV0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG = REPO_ROOT / "config" / "ops" / "shadow_preparation_readiness_gate_v0.toml"
BUNDLE_MODULE = REPO_ROOT / "src" / "ops" / "shadow_preparation_readiness_bundle_v0.py"
CONTRACT_DOC = (
    REPO_ROOT / "docs" / "ops" / "runbooks" / "SHADOW_PREPARATION_READINESS_GATE_CONTRACT_V0.md"
)
EVALUATED_AT = "2026-07-25T12:00:00Z"
AS_OF = "2026-07-25T12:00:30Z"

FORBIDDEN_IMPORT_PREFIXES = (
    "src.webui",
    "src.orders",
    "src.execution",
    "src.live",
    "src.scheduler",
    "src.trading.master_v2",
)


def _collect_required_relative_paths(cfg: dict) -> set[str]:
    paths: set[str] = set()
    for surface in cfg["historical_surfaces"]:
        paths.add(str(surface["path"]).strip())
    for component in cfg["mindestkontrakt_components"]:
        for evidence_path in component.get("evidence_paths") or []:
            paths.add(str(evidence_path).strip())
    paths.add(str(cfg[CANONICAL_STEP_29U_SEMANTICS_REFERENCE_KEY]).strip())
    return paths


def _materialize_temp_repo(tmp_path: Path) -> tuple[Path, dict]:
    cfg = load_shadow_preparation_readiness_gate_config_v0(CONFIG, repo_root=REPO_ROOT)
    for relative in _collect_required_relative_paths(cfg):
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.write_text(f"# stub:{relative}\n", encoding="utf-8")
    config_dest = tmp_path / "config" / "ops" / "shadow_preparation_readiness_gate_v0.toml"
    config_dest.parent.mkdir(parents=True, exist_ok=True)
    config_dest.write_text(CONFIG.read_text(encoding="utf-8"), encoding="utf-8")
    (tmp_path / "out" / "ops").mkdir(parents=True, exist_ok=True)
    return tmp_path, cfg


def _ready_like_evaluation(base):
    inventory = tuple(
        replace(record, preparation_status=PreparationStatusV0.PRESENT)
        for record in base.mindestkontrakt_inventory
    )
    return replace(
        base,
        shadow_preparation_complete=True,
        blockers=(),
        unmet_gates=(),
        mindestkontrakt_inventory=inventory,
    )


def test_package_marker_and_schema_identity() -> None:
    assert PACKAGE_MARKER == "SHADOW_PREPARATION_READINESS_BUNDLE_V0=true"
    assert PRODUCER_FAMILY == SCHEMA_ID
    assert PRODUCER_FAMILY.endswith("_v0")


def test_blocked_pipeline_yields_bundle_blocked_with_canonical_artifacts(
    tmp_path: Path,
) -> None:
    root, _cfg = _materialize_temp_repo(tmp_path)
    bundle = build_shadow_preparation_readiness_bundle_v0(
        repo_root=root,
        output_path=DEFAULT_PROJECTION_OUTPUT_RELATIVE_PATH,
        evaluated_at=EVALUATED_AT,
        as_of=AS_OF,
    )
    assert bundle.bundle_status == BUNDLE_STATUS_BLOCKED
    assert bundle.pipeline is not None
    assert bundle.pipeline["pipeline_status"] == PIPELINE_STATUS_BLOCKED
    assert bundle.pipeline["readiness_status"] == READINESS_STATUS_BLOCKED
    assert bundle.projection is not None
    assert bundle.projection["schema_id"] == "shadow_preparation_readiness_projection"
    assert bundle.projection["shadow_preparation_complete"] is False
    assert bundle.verification is not None
    assert bundle.verification["verified"] is True
    assert bundle.verification["overall_status"] == "VERIFIED"
    assert bundle.to_dict()["authority_effect"] == "NONE"
    assert bundle.to_dict()["activation_authority"] is False
    assert bundle.to_dict()["read_only"] is True
    assert bundle.to_dict()["bundle_only"] is True


def test_ready_like_pipeline_yields_bundle_pass(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, _cfg = _materialize_temp_repo(tmp_path)
    real_evaluate = evaluate_shadow_preparation_readiness_gate_v0

    def _ready_evaluate(**kwargs):
        return _ready_like_evaluation(real_evaluate(**kwargs))

    monkeypatch.setattr(
        "src.ops.shadow_preparation_readiness_offline_projection_pipeline_v0."
        "evaluate_shadow_preparation_readiness_gate_v0",
        _ready_evaluate,
    )
    bundle = build_shadow_preparation_readiness_bundle_v0(
        repo_root=root,
        output_path=DEFAULT_PROJECTION_OUTPUT_RELATIVE_PATH,
        evaluated_at=EVALUATED_AT,
        as_of=AS_OF,
    )
    assert bundle.bundle_status == BUNDLE_STATUS_PASS
    assert bundle.pipeline is not None
    assert bundle.pipeline["pipeline_status"] == PIPELINE_STATUS_PASS
    assert bundle.pipeline["readiness_status"] == READINESS_STATUS_READY
    assert bundle.projection is not None
    assert bundle.projection["shadow_preparation_complete"] is True
    assert bundle.verification is not None
    assert bundle.verification["verified"] is True
    assert bundle.reason_codes == ()


def test_pipeline_error_does_not_synthesize_projection_or_verification(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    root, _cfg = _materialize_temp_repo(tmp_path)

    def _error_pipeline(**_kwargs):
        return ShadowPreparationReadinessOfflineProjectionPipelineResultV0(
            pipeline_status=PIPELINE_STATUS_ERROR,
            readiness_status=None,
            evaluated_at=None,
            projection_path=None,
            projection_schema_id=None,
            projection_schema_version=None,
            projection_sha256=None,
            verification_status=None,
            verification_verified=None,
            reason_codes=("GATE_EVALUATION_FAILED:synthetic",),
            evidence_reference_count=None,
        )

    monkeypatch.setattr(
        "src.ops.shadow_preparation_readiness_bundle_v0."
        "run_shadow_preparation_readiness_offline_projection_pipeline_v0",
        _error_pipeline,
    )
    bundle = build_shadow_preparation_readiness_bundle_v0(repo_root=root)
    assert bundle.bundle_status == BUNDLE_STATUS_ERROR
    assert bundle.projection is None
    assert bundle.verification is None
    assert bundle.pipeline is not None
    assert "GATE_EVALUATION_FAILED:synthetic" in bundle.reason_codes


def test_missing_projection_artifact_fail_closed_blocked(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    root, _cfg = _materialize_temp_repo(tmp_path)

    def _blocked_without_file(**_kwargs):
        return ShadowPreparationReadinessOfflineProjectionPipelineResultV0(
            pipeline_status=PIPELINE_STATUS_BLOCKED,
            readiness_status=READINESS_STATUS_BLOCKED,
            evaluated_at=EVALUATED_AT,
            projection_path=DEFAULT_PROJECTION_OUTPUT_RELATIVE_PATH,
            projection_schema_id="shadow_preparation_readiness_projection",
            projection_schema_version="v0",
            projection_sha256="deadbeef",
            verification_status="VERIFIED",
            verification_verified=True,
            reason_codes=(),
            evidence_reference_count=0,
        )

    monkeypatch.setattr(
        "src.ops.shadow_preparation_readiness_bundle_v0."
        "run_shadow_preparation_readiness_offline_projection_pipeline_v0",
        _blocked_without_file,
    )
    # Do not create the projection file — fail closed.
    bundle = build_shadow_preparation_readiness_bundle_v0(repo_root=root)
    assert bundle.bundle_status == BUNDLE_STATUS_BLOCKED
    assert bundle.projection is None
    assert bundle.verification is None
    assert any(code.startswith("BUNDLE_ARTIFACT_UNAVAILABLE:") for code in bundle.reason_codes)


def test_serialize_is_deterministic_and_includes_canonical_pipeline_dict(
    tmp_path: Path,
) -> None:
    root, _cfg = _materialize_temp_repo(tmp_path)
    bundle = build_shadow_preparation_readiness_bundle_v0(
        repo_root=root,
        output_path=DEFAULT_PROJECTION_OUTPUT_RELATIVE_PATH,
        evaluated_at=EVALUATED_AT,
        as_of=AS_OF,
    )
    raw_a = serialize_shadow_preparation_readiness_bundle_v0(bundle)
    raw_b = serialize_shadow_preparation_readiness_bundle_v0(bundle)
    assert raw_a == raw_b
    payload = json.loads(raw_a)
    assert payload["schema_id"] == SCHEMA_ID
    assert payload["pipeline"]["schema_id"].endswith(
        "shadow_preparation_readiness_offline_projection_pipeline_v0"
    )
    assert payload["projection"]["evaluation"]["schema_id"].endswith(
        "shadow_preparation_readiness_gate_v0"
    )


def test_no_forbidden_imports_or_network() -> None:
    tree = ast.parse(BUNDLE_MODULE.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                for prefix in FORBIDDEN_IMPORT_PREFIXES:
                    assert not alias.name.startswith(prefix)
        elif isinstance(node, ast.ImportFrom) and node.module:
            for prefix in FORBIDDEN_IMPORT_PREFIXES:
                assert not node.module.startswith(prefix)
        elif isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            assert not (node.value.id == "socket" and node.attr == "socket")
    assert "socket" not in BUNDLE_MODULE.read_text(encoding="utf-8")
    # socket must remain unused (guard against accidental network deps).
    assert socket.AF_INET


def test_contract_doc_mentions_bundle() -> None:
    text = CONTRACT_DOC.read_text(encoding="utf-8")
    assert "SHADOW_PREPARATION_READINESS_BUNDLE_V0" in text
    assert "shadow_preparation_readiness_bundle_v0" in text
    assert "bundle_only" in text or "BUNDLE_PASS" in text
