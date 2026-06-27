"""Offline durable evidence binding for comparison_ssot.v1 definition manifest."""

from __future__ import annotations

import hashlib
import shutil
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from scripts.ops.primary_evidence_retention_v0 import (
    is_under_tmp,
    verify_manifest_sha256,
    write_manifest_sha256,
)
from src.meta.learning_loop.comparison_ssot_v1.constants import (
    COMPARISON_CONTRACT_VERSION,
    DEFINITION_ARTIFACT_FILENAME,
)
from src.meta.learning_loop.comparison_ssot_v1.io import read_manifest
from src.meta.learning_loop.comparison_ssot_v1.validation import validate_definition_manifest_v1
from src.meta.learning_loop.contract_safety_v1 import (
    compute_content_sha256,
    deterministic_json_dumps,
    is_valid_sha256_hex,
)

BINDING_SCHEMA_VERSION = "comparison_ssot_definition_durable_evidence_binding_v1"
BINDING_RELATION = "PRESERVES_DEFINITION_IDENTITY_AND_INPUT_REFS"
MANIFEST_ARTIFACT_REL = DEFINITION_ARTIFACT_FILENAME
INDEX_ARTIFACT_REL = "comparison_ssot_definition_durable_evidence_binding_index_v1.json"
MANIFEST_FILENAME = "MANIFEST.sha256"
STAGING_DIRNAME_PREFIX = ".comparison_ssot_definition_durable_evidence_staging_"

FUTURES_SCOPE_REF: dict[str, bool] = {
    "futures_only": True,
    "bitcoin_direction_allowed": False,
}
TRADING_LOGIC_IMMUTABILITY_REF: dict[str, bool] = {
    "trading_logic_immutability": True,
}

_FORBIDDEN_INDEX_KEYS: frozenset[str] = frozenset(
    {
        "patches",
        "patch",
        "strategy",
        "signal",
        "signals",
        "entry",
        "exit",
        "position_sizing",
        "leverage",
        "stop_loss",
        "take_profit",
        "execution",
        "order_routing",
        "risk_limits",
        "killswitch",
        "old_value",
        "new_value",
        "target",
        "returns",
        "positions",
        "orders",
        "credentials",
        "runtime_status",
        "live_arming",
        "apply_authority",
        "promotion_authority",
        "completion",
        "checkpoint",
        "params",
        "metrics",
        "tags",
        "winner",
        "selection",
        "acceptance",
        "ranking",
        "pareto",
        "selected",
        "accepted",
        "promoted",
        "completed",
        "runtime_authorized",
        "shadow_authorized",
        "testnet_authorized",
        "live_authorized",
    }
)


class ComparisonSsotDefinitionDurableEvidenceBindingError(ValueError):
    """Fail-closed comparison definition durable evidence binding error."""


@dataclass(frozen=True)
class BoundArtifactRecord:
    artifact_kind: str
    relative_path: str
    content_sha256: str


@dataclass(frozen=True)
class ComparisonDefinitionBindingCrossReferences:
    comparison_definition_id: str
    manifest_content_sha256: str


@dataclass(frozen=True)
class ComparisonSsotDefinitionDurableEvidenceBindingResult:
    output_dir: Path
    comparison_definition_id: str
    binding_index_path: Path
    manifest_path: Path


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _reject_symlink(path: Path, *, label: str) -> None:
    if path.is_symlink():
        raise ComparisonSsotDefinitionDurableEvidenceBindingError(
            f"{label} must not be a symlink: {path}"
        )


def _reject_forbidden_index_keys(payload: Mapping[str, Any]) -> None:
    for key in payload:
        if key in _FORBIDDEN_INDEX_KEYS:
            raise ComparisonSsotDefinitionDurableEvidenceBindingError(
                f"binding index must not contain forbidden key: {key}"
            )


def _validate_regular_file(path: Path, *, label: str) -> None:
    if not path.exists():
        raise ComparisonSsotDefinitionDurableEvidenceBindingError(f"{label} not found: {path}")
    _reject_symlink(path, label=label)
    if not path.is_file():
        raise ComparisonSsotDefinitionDurableEvidenceBindingError(
            f"{label} must be a regular file: {path}"
        )


def _validate_output_target(output_dir: Path) -> None:
    if output_dir.exists():
        raise ComparisonSsotDefinitionDurableEvidenceBindingError(
            f"output directory already exists (fail-closed): {output_dir}"
        )
    if is_under_tmp(output_dir):
        raise ComparisonSsotDefinitionDurableEvidenceBindingError(
            "output directory must be outside /tmp"
        )
    parent = output_dir.parent
    if not parent.is_dir():
        raise ComparisonSsotDefinitionDurableEvidenceBindingError(
            f"output parent directory missing: {parent}"
        )
    if is_under_tmp(parent):
        raise ComparisonSsotDefinitionDurableEvidenceBindingError(
            "output parent directory must be outside /tmp"
        )


def _path_is_under(child: Path, parent: Path) -> bool:
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def _validate_bundle_relative_path(rel: str) -> None:
    candidate = Path(rel)
    if candidate.is_absolute():
        raise ComparisonSsotDefinitionDurableEvidenceBindingError(
            f"bundle relative path must not be absolute: {rel!r}"
        )
    if ".." in candidate.parts:
        raise ComparisonSsotDefinitionDurableEvidenceBindingError(
            f"bundle relative path must not traverse upward: {rel!r}"
        )


def _reject_unsafe_overlap(*, manifest_path: Path, output_dir: Path) -> None:
    manifest_res = manifest_path.resolve()
    output_res = output_dir.resolve()
    if output_res == manifest_res:
        raise ComparisonSsotDefinitionDurableEvidenceBindingError(
            "output directory must not equal manifest path (fail-closed)"
        )
    if _path_is_under(manifest_res, output_res):
        raise ComparisonSsotDefinitionDurableEvidenceBindingError(
            "manifest path must not be inside output directory (fail-closed)"
        )


def _load_validated_manifest(manifest_path: Path) -> tuple[dict[str, Any], bytes]:
    _validate_regular_file(manifest_path, label="comparison definition manifest")
    if manifest_path.name != MANIFEST_ARTIFACT_REL:
        raise ComparisonSsotDefinitionDurableEvidenceBindingError(
            f"manifest filename must be {MANIFEST_ARTIFACT_REL!r}, got {manifest_path.name!r}"
        )
    manifest_bytes = manifest_path.read_bytes()
    manifest = read_manifest(manifest_path)
    validate_definition_manifest_v1(manifest)
    return manifest, manifest_bytes


def _verbatim_input_refs(manifest: Mapping[str, Any]) -> list[dict[str, str]]:
    input_refs = manifest.get("input_refs")
    if not isinstance(input_refs, list):
        raise ComparisonSsotDefinitionDurableEvidenceBindingError("input_refs must be a list")
    preserved: list[dict[str, str]] = []
    for idx, ref in enumerate(input_refs):
        if not isinstance(ref, Mapping):
            raise ComparisonSsotDefinitionDurableEvidenceBindingError(
                f"input_refs[{idx}] must be an object"
            )
        preserved.append(
            {
                "owner_domain": str(ref["owner_domain"]),
                "ref_type": str(ref["ref_type"]),
                "ref_id": str(ref["ref_id"]),
                "digest": str(ref["digest"]),
            }
        )
    return preserved


def _verbatim_policy_config_ref(manifest: Mapping[str, Any]) -> dict[str, str]:
    return {
        "ranking_rule_version": str(manifest["ranking_rule_version"]),
        "tie_rule_version": str(manifest["tie_rule_version"]),
        "evaluation_slice_id": str(manifest["evaluation_slice_id"]),
        "metric_set_version": str(manifest["metric_set_version"]),
        "comparability_gate_version": str(manifest["comparability_gate_version"]),
        "normalization_policy_version": str(manifest["normalization_policy_version"]),
        "eligibility_rules_version": str(manifest["eligibility_rules_version"]),
    }


def check_reference_consistency(
    manifest: Mapping[str, Any],
) -> ComparisonDefinitionBindingCrossReferences:
    comparison_definition_id = manifest.get("comparison_definition_id")
    if not isinstance(comparison_definition_id, str) or not comparison_definition_id.strip():
        raise ComparisonSsotDefinitionDurableEvidenceBindingError(
            "comparison_definition_id missing or invalid"
        )
    integrity = manifest.get("integrity")
    if not isinstance(integrity, Mapping):
        raise ComparisonSsotDefinitionDurableEvidenceBindingError("integrity must be an object")
    manifest_content_sha256 = integrity.get("content_sha256")
    if not isinstance(manifest_content_sha256, str) or not manifest_content_sha256.strip():
        raise ComparisonSsotDefinitionDurableEvidenceBindingError(
            "integrity.content_sha256 missing or invalid"
        )
    if not is_valid_sha256_hex(manifest_content_sha256):
        raise ComparisonSsotDefinitionDurableEvidenceBindingError(
            "integrity.content_sha256 must be valid sha256 hex"
        )
    return ComparisonDefinitionBindingCrossReferences(
        comparison_definition_id=comparison_definition_id,
        manifest_content_sha256=manifest_content_sha256,
    )


def build_binding_index_v1(
    *,
    manifest: Mapping[str, Any],
    cross_references: ComparisonDefinitionBindingCrossReferences,
    artifacts: tuple[BoundArtifactRecord, ...],
) -> dict[str, Any]:
    sorted_artifacts = sorted(
        artifacts,
        key=lambda item: (item.artifact_kind, item.relative_path),
    )
    input_refs = _verbatim_input_refs(manifest)
    payload: dict[str, Any] = {
        "schema_version": BINDING_SCHEMA_VERSION,
        "bound_contract": COMPARISON_CONTRACT_VERSION,
        "comparison_definition_id": cross_references.comparison_definition_id,
        "identity_domain": str(manifest["identity_domain"]),
        "binding_relation": BINDING_RELATION,
        "definition_input_refs": input_refs,
        "policy_config_ref": _verbatim_policy_config_ref(manifest),
        "cross_references": {
            "comparison_definition_id": cross_references.comparison_definition_id,
            "manifest_content_sha256": cross_references.manifest_content_sha256,
        },
        "artifacts": [
            {
                "artifact_kind": item.artifact_kind,
                "relative_path": item.relative_path,
                "content_sha256": item.content_sha256,
            }
            for item in sorted_artifacts
        ],
        "futures_scope_ref": dict(FUTURES_SCOPE_REF),
        "trading_logic_immutability_ref": dict(TRADING_LOGIC_IMMUTABILITY_REF),
        "evidence_does_not_authorize_runtime": True,
    }
    _reject_forbidden_index_keys(payload)
    digest = compute_content_sha256(payload)
    payload["integrity"] = {"content_sha256": digest}
    return payload


def serialize_binding_index_v1(index: Mapping[str, Any]) -> str:
    _reject_forbidden_index_keys(index)
    return deterministic_json_dumps(dict(index))


def _copy_byte_identical(source: Path, dest: Path) -> str:
    _validate_regular_file(source, label="source artifact")
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, dest)
    source_digest = _sha256_file(source)
    dest_digest = _sha256_file(dest)
    if source_digest != dest_digest:
        raise ComparisonSsotDefinitionDurableEvidenceBindingError(
            f"byte-identical copy failed for {source.name}"
        )
    return source_digest


def _staging_dir_for(output_dir: Path) -> Path:
    token = uuid.uuid4().hex
    return output_dir.parent / f"{STAGING_DIRNAME_PREFIX}{token}"


def _cleanup_staging(staging: Path) -> None:
    if staging.exists():
        shutil.rmtree(staging)


def reverify_comparison_ssot_definition_durable_evidence_bundle_v1(
    *,
    output_dir: Path | str,
) -> None:
    """Replay durable evidence bundle without raw source access."""
    bundle_dir = Path(output_dir)
    if not bundle_dir.is_dir():
        raise ComparisonSsotDefinitionDurableEvidenceBindingError(
            f"bundle directory not found: {bundle_dir}"
        )
    ok, msg = verify_manifest_sha256(bundle_dir)
    if not ok:
        raise ComparisonSsotDefinitionDurableEvidenceBindingError(
            f"MANIFEST.sha256 verification failed: {msg}"
        )
    manifest_path = bundle_dir / MANIFEST_ARTIFACT_REL
    index_path = bundle_dir / INDEX_ARTIFACT_REL
    _validate_regular_file(manifest_path, label=MANIFEST_ARTIFACT_REL)
    _validate_regular_file(index_path, label=INDEX_ARTIFACT_REL)
    manifest = _load_validated_manifest(manifest_path)[0]
    cross = check_reference_consistency(manifest)
    index = read_manifest(index_path)
    if index.get("binding_relation") != BINDING_RELATION:
        raise ComparisonSsotDefinitionDurableEvidenceBindingError("binding_relation mismatch")
    if index.get("comparison_definition_id") != cross.comparison_definition_id:
        raise ComparisonSsotDefinitionDurableEvidenceBindingError(
            "binding index comparison_definition_id mismatch"
        )
    index_cross = index.get("cross_references")
    if not isinstance(index_cross, Mapping):
        raise ComparisonSsotDefinitionDurableEvidenceBindingError("cross_references must be object")
    if index_cross.get("comparison_definition_id") != cross.comparison_definition_id:
        raise ComparisonSsotDefinitionDurableEvidenceBindingError(
            "cross_references comparison_definition_id mismatch"
        )
    if index_cross.get("manifest_content_sha256") != cross.manifest_content_sha256:
        raise ComparisonSsotDefinitionDurableEvidenceBindingError(
            "manifest_content_sha256 mismatch"
        )
    if index.get("definition_input_refs") != _verbatim_input_refs(manifest):
        raise ComparisonSsotDefinitionDurableEvidenceBindingError(
            "definition_input_refs not preserved verbatim"
        )
    if index.get("policy_config_ref") != _verbatim_policy_config_ref(manifest):
        raise ComparisonSsotDefinitionDurableEvidenceBindingError(
            "policy_config_ref not preserved verbatim"
        )
    validate_definition_manifest_v1(manifest)


def produce_comparison_ssot_definition_durable_evidence_bundle_v1(
    *,
    manifest_path: Path | str,
    output_dir: Path | str,
) -> ComparisonSsotDefinitionDurableEvidenceBindingResult:
    """Bind validated comparison definition manifest into offline durable evidence."""
    manifest_file = Path(manifest_path)
    final_dir = Path(output_dir)

    _validate_output_target(final_dir)
    _reject_unsafe_overlap(manifest_path=manifest_file, output_dir=final_dir)

    manifest, _manifest_bytes = _load_validated_manifest(manifest_file)
    cross = check_reference_consistency(manifest)
    comparison_definition_id = cross.comparison_definition_id

    for rel in (MANIFEST_ARTIFACT_REL, INDEX_ARTIFACT_REL):
        _validate_bundle_relative_path(rel)

    staging = _staging_dir_for(final_dir)
    if staging.exists():
        raise ComparisonSsotDefinitionDurableEvidenceBindingError(
            f"staging directory collision: {staging}"
        )

    try:
        staging.mkdir(parents=True, exist_ok=False)

        manifest_dest = staging / MANIFEST_ARTIFACT_REL
        manifest_file_digest = _copy_byte_identical(manifest_file, manifest_dest)

        artifacts = (
            BoundArtifactRecord(
                artifact_kind="comparison_definition_manifest_v1",
                relative_path=MANIFEST_ARTIFACT_REL,
                content_sha256=manifest_file_digest,
            ),
        )
        index_payload = build_binding_index_v1(
            manifest=manifest,
            cross_references=cross,
            artifacts=artifacts,
        )
        index_path = staging / INDEX_ARTIFACT_REL
        index_path.write_text(serialize_binding_index_v1(index_payload), encoding="utf-8")

        write_manifest_sha256(staging)
        ok, msg = verify_manifest_sha256(staging)
        if not ok:
            raise ComparisonSsotDefinitionDurableEvidenceBindingError(
                f"MANIFEST.sha256 verification failed before publish: {msg}"
            )

        staging.replace(final_dir)

        ok, msg = verify_manifest_sha256(final_dir)
        if not ok:
            raise ComparisonSsotDefinitionDurableEvidenceBindingError(
                f"MANIFEST.sha256 verification failed after publish: {msg}"
            )
    except Exception:
        _cleanup_staging(staging)
        if final_dir.exists():
            shutil.rmtree(final_dir)
        raise

    return ComparisonSsotDefinitionDurableEvidenceBindingResult(
        output_dir=final_dir,
        comparison_definition_id=comparison_definition_id,
        binding_index_path=final_dir / INDEX_ARTIFACT_REL,
        manifest_path=final_dir / MANIFEST_FILENAME,
    )


__all__ = [
    "BINDING_RELATION",
    "BINDING_SCHEMA_VERSION",
    "INDEX_ARTIFACT_REL",
    "MANIFEST_ARTIFACT_REL",
    "BoundArtifactRecord",
    "ComparisonDefinitionBindingCrossReferences",
    "ComparisonSsotDefinitionDurableEvidenceBindingError",
    "ComparisonSsotDefinitionDurableEvidenceBindingResult",
    "build_binding_index_v1",
    "check_reference_consistency",
    "produce_comparison_ssot_definition_durable_evidence_bundle_v1",
    "reverify_comparison_ssot_definition_durable_evidence_bundle_v1",
    "serialize_binding_index_v1",
]
