"""Offline learning loop comparison checkpoint v1 — non-authoritative durable mark."""

from __future__ import annotations

import json
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
from src.governance.promotion_loop.candidate_lineage_manifest_v1 import (
    LineageRefType,
    lineage_ref_from_mapping,
    lineage_ref_to_mapping,
)
from src.governance.promotion_loop.comparison_lineage_ref_producer_v1 import (
    COMPARISON_OWNER_DOMAIN,
)
from src.meta.learning_loop.comparison_common_durable_evidence_binding_v1 import (
    COMPARISON_AUTHORITY_INVARIANTS,
    ComparisonCommonDurableEvidenceBindingError,
    INDEX_ARTIFACT_REL as COMMON_INDEX_ARTIFACT_REL,
    reverify_comparison_common_durable_evidence_bundle_v1,
)
from src.meta.learning_loop.comparison_ssot_v1.constants import COMPARISON_CONTRACT_VERSION
from src.meta.learning_loop.comparison_ssot_v1.io import read_manifest
from src.meta.learning_loop.contract_safety_v1 import (
    compute_content_sha256,
    deterministic_json_dumps,
    is_valid_sha256_hex,
)

CHECKPOINT_SCHEMA_VERSION = "comparison_checkpoint_v1"
CHECKPOINT_RELATION = "REFERENCES_VERIFIED_COMMON_BUNDLE"
RECORD_KIND = "comparison_durable_evidence_completeness"
INDEX_ARTIFACT_REL = "comparison_checkpoint_index_v1.json"
MANIFEST_FILENAME = "MANIFEST.sha256"
STAGING_DIRNAME_PREFIX = ".comparison_checkpoint_staging_"

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
        "completed",
        "completion_claimed",
        "completion_ready",
        "completion_authorized",
        "checkpoint",
        "params",
        "metrics",
        "tags",
        "winner",
        "selection",
        "acceptance",
        "accepted",
        "ranking",
        "pareto",
        "selected",
        "promoted",
        "promotion",
        "promotion_ready",
        "promotion_authorized",
        "runtime_authorized",
        "shadow_authorized",
        "paper_authorized",
        "testnet_authorized",
        "live_authorized",
        "orders_allowed",
        "ready_for_operator_arming",
        "armed",
        "enabled",
        "capital_allocated",
        "strategy_params_mutated",
        "stage_transition_authorized",
    }
)


class ComparisonCheckpointError(ValueError):
    """Fail-closed comparison checkpoint error."""


@dataclass(frozen=True)
class ComparisonCheckpointResult:
    output_dir: Path
    comparison_definition_id: str
    checkpoint_id: str
    checkpoint_index_path: Path
    manifest_path: Path


def _reject_symlink(path: Path, *, label: str) -> None:
    if path.is_symlink():
        raise ComparisonCheckpointError(f"{label} must not be a symlink: {path}")


def _reject_forbidden_index_keys(payload: Mapping[str, Any]) -> None:
    for key in payload:
        if key in _FORBIDDEN_INDEX_KEYS:
            raise ComparisonCheckpointError(
                f"checkpoint index must not contain forbidden key: {key}"
            )


def _validate_regular_file(path: Path, *, label: str) -> None:
    if not path.exists():
        raise ComparisonCheckpointError(f"{label} not found: {path}")
    _reject_symlink(path, label=label)
    if not path.is_file():
        raise ComparisonCheckpointError(f"{label} must be a regular file: {path}")


def _validate_bundle_dir(bundle_dir: Path, *, label: str) -> None:
    if not bundle_dir.is_dir():
        raise ComparisonCheckpointError(f"{label} must be a directory: {bundle_dir}")
    _reject_symlink(bundle_dir, label=label)


def _validate_output_target(output_dir: Path) -> None:
    if output_dir.exists():
        raise ComparisonCheckpointError(
            f"output directory already exists (fail-closed): {output_dir}"
        )
    if is_under_tmp(output_dir):
        raise ComparisonCheckpointError("output directory must be outside /tmp")
    parent = output_dir.parent
    if not parent.is_dir():
        raise ComparisonCheckpointError(f"output parent directory missing: {parent}")
    if is_under_tmp(parent):
        raise ComparisonCheckpointError("output parent directory must be outside /tmp")


def _path_is_under(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def _reject_unsafe_overlap(*, common_bundle_dir: Path, output_dir: Path) -> None:
    common_res = common_bundle_dir.resolve()
    output_res = output_dir.resolve()
    if output_res == common_res:
        raise ComparisonCheckpointError(
            "output directory must not equal common bundle path (fail-closed)"
        )
    if _path_is_under(common_res, output_res):
        raise ComparisonCheckpointError(
            "common bundle must not be inside output directory (fail-closed)"
        )
    if _path_is_under(output_res, common_res):
        raise ComparisonCheckpointError(
            "output directory must not be inside common bundle path (fail-closed)"
        )


def _binding_index_integrity_sha256(index: Mapping[str, Any], *, label: str) -> str:
    integrity = index.get("integrity")
    if not isinstance(integrity, Mapping):
        raise ComparisonCheckpointError(f"{label} integrity must be an object")
    digest = integrity.get("content_sha256")
    if not isinstance(digest, str) or not digest.strip():
        raise ComparisonCheckpointError(f"{label} integrity.content_sha256 missing or invalid")
    if not is_valid_sha256_hex(digest):
        raise ComparisonCheckpointError(
            f"{label} integrity.content_sha256 must be valid sha256 hex"
        )
    return digest


def _verbatim_mapping(value: Mapping[str, Any]) -> dict[str, Any]:
    return {str(key): value[key] for key in value}


def _verbatim_ref_list(value: Any, *, label: str) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise ComparisonCheckpointError(f"{label} must be a list")
    out: list[dict[str, Any]] = []
    for idx, item in enumerate(value):
        if not isinstance(item, Mapping):
            raise ComparisonCheckpointError(f"{label}[{idx}] must be an object")
        out.append(_verbatim_mapping(item))
    return out


def _load_verified_common_bundle_index(common_bundle_dir: Path) -> dict[str, Any]:
    _validate_bundle_dir(common_bundle_dir, label="common bundle")
    try:
        reverify_comparison_common_durable_evidence_bundle_v1(output_dir=common_bundle_dir)
    except ComparisonCommonDurableEvidenceBindingError as exc:
        raise ComparisonCheckpointError(str(exc)) from exc
    index_path = common_bundle_dir / COMMON_INDEX_ARTIFACT_REL
    return read_manifest(index_path)


def _load_optional_lineage_ref(lineage_ref_path: Path) -> dict[str, Any]:
    _validate_regular_file(lineage_ref_path, label="lineage ref")
    try:
        payload = json.loads(lineage_ref_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ComparisonCheckpointError(
            f"lineage ref is not valid JSON: {lineage_ref_path}"
        ) from exc
    if not isinstance(payload, dict):
        raise ComparisonCheckpointError("lineage ref root must be a JSON object")
    try:
        ref = lineage_ref_from_mapping(payload)
    except Exception as exc:
        raise ComparisonCheckpointError(f"lineage ref validation failed: {exc}") from exc
    if ref.ref_type != LineageRefType.COMPARISON:
        raise ComparisonCheckpointError("lineage ref ref_type must be comparison")
    if ref.owner_domain != COMPARISON_OWNER_DOMAIN:
        raise ComparisonCheckpointError(
            f"lineage ref owner_domain must be {COMPARISON_OWNER_DOMAIN!r}"
        )
    return lineage_ref_to_mapping(ref)


def _cross_check_lineage_ref(
    *,
    lineage_ref_record: Mapping[str, Any],
    comparison_definition_id: str,
    result_binding_ref: Mapping[str, Any],
) -> None:
    ref_id = lineage_ref_record.get("ref_id")
    if ref_id != comparison_definition_id:
        raise ComparisonCheckpointError(
            "lineage ref ref_id must equal comparison_definition_id (fail-closed)"
        )
    digest = lineage_ref_record.get("digest")
    result_manifest_digest = result_binding_ref.get("manifest_content_sha256")
    if digest != result_manifest_digest:
        raise ComparisonCheckpointError(
            "lineage ref digest must match result_binding_ref.manifest_content_sha256"
        )


def build_checkpoint_index_v1(
    *,
    common_bundle_dir: Path,
    common_bundle_index: Mapping[str, Any],
    lineage_ref_record: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    comparison_definition_id = common_bundle_index.get("comparison_definition_id")
    if not isinstance(comparison_definition_id, str) or not comparison_definition_id.strip():
        raise ComparisonCheckpointError("comparison_definition_id missing or invalid")

    metric_input_binding_refs = _verbatim_ref_list(
        common_bundle_index.get("metric_input_binding_refs"),
        label="metric_input_binding_refs",
    )
    definition_binding_ref = common_bundle_index.get("definition_binding_ref")
    result_binding_ref = common_bundle_index.get("result_binding_ref")
    chain_cross_references = common_bundle_index.get("chain_cross_references")
    if not isinstance(definition_binding_ref, Mapping):
        raise ComparisonCheckpointError("definition_binding_ref must be an object")
    if not isinstance(result_binding_ref, Mapping):
        raise ComparisonCheckpointError("result_binding_ref must be an object")
    if not isinstance(chain_cross_references, Mapping):
        raise ComparisonCheckpointError("chain_cross_references must be an object")

    authority_invariants = common_bundle_index.get("comparison_authority_invariants")
    if authority_invariants != COMPARISON_AUTHORITY_INVARIANTS:
        raise ComparisonCheckpointError("comparison_authority_invariants mismatch")

    common_integrity = _binding_index_integrity_sha256(
        common_bundle_index, label="common bundle index"
    )

    if lineage_ref_record is not None:
        _cross_check_lineage_ref(
            lineage_ref_record=lineage_ref_record,
            comparison_definition_id=comparison_definition_id,
            result_binding_ref=result_binding_ref,
        )

    payload: dict[str, Any] = {
        "record_schema_version": CHECKPOINT_SCHEMA_VERSION,
        "record_kind": RECORD_KIND,
        "bound_contract": COMPARISON_CONTRACT_VERSION,
        "comparison_definition_id": comparison_definition_id,
        "checkpoint_relation": CHECKPOINT_RELATION,
        "common_bundle_ref": {
            "source_path": common_bundle_dir.resolve().as_posix(),
            "binding_index_integrity_sha256": common_integrity,
        },
        "metric_input_binding_refs": metric_input_binding_refs,
        "definition_binding_ref": _verbatim_mapping(definition_binding_ref),
        "result_binding_ref": _verbatim_mapping(result_binding_ref),
        "chain_cross_references": _verbatim_mapping(chain_cross_references),
        "comparison_authority_invariants": dict(COMPARISON_AUTHORITY_INVARIANTS),
        "evidence_does_not_authorize_runtime": True,
        "is_completion_evidence": False,
    }
    if lineage_ref_record is not None:
        payload["lineage_ref_record"] = _verbatim_mapping(lineage_ref_record)

    _reject_forbidden_index_keys(payload)
    digest = compute_content_sha256(payload)
    payload["integrity"] = {"content_sha256": digest}
    return payload


def serialize_checkpoint_index_v1(index: Mapping[str, Any]) -> str:
    _reject_forbidden_index_keys(index)
    return deterministic_json_dumps(dict(index))


def _validate_checkpoint_index(index: Mapping[str, Any]) -> None:
    if index.get("record_schema_version") != CHECKPOINT_SCHEMA_VERSION:
        raise ComparisonCheckpointError("record_schema_version mismatch")
    if index.get("record_kind") != RECORD_KIND:
        raise ComparisonCheckpointError("record_kind mismatch")
    if index.get("checkpoint_relation") != CHECKPOINT_RELATION:
        raise ComparisonCheckpointError("checkpoint_relation mismatch")
    if index.get("evidence_does_not_authorize_runtime") is not True:
        raise ComparisonCheckpointError("evidence_does_not_authorize_runtime must be true")
    if index.get("is_completion_evidence") is not False:
        raise ComparisonCheckpointError("is_completion_evidence must be false")
    invariants = index.get("comparison_authority_invariants")
    if invariants != COMPARISON_AUTHORITY_INVARIANTS:
        raise ComparisonCheckpointError("comparison_authority_invariants mismatch")
    _reject_forbidden_index_keys(index)

    stored = index.get("integrity")
    if not isinstance(stored, Mapping):
        raise ComparisonCheckpointError("integrity must be an object")
    body = {key: value for key, value in index.items() if key != "integrity"}
    expected = compute_content_sha256(body)
    actual = stored.get("content_sha256")
    if actual != expected:
        raise ComparisonCheckpointError("checkpoint index integrity mismatch")


def _staging_dir_for(output_dir: Path) -> Path:
    return output_dir.parent / f"{STAGING_DIRNAME_PREFIX}{uuid.uuid4().hex}"


def _cleanup_staging(staging: Path) -> None:
    if staging.exists():
        shutil.rmtree(staging)


def reverify_comparison_checkpoint_v1(*, output_dir: Path | str) -> None:
    """Replay comparison checkpoint bundle without producer or upstream mutation."""
    bundle_dir = Path(output_dir)
    if not bundle_dir.is_dir():
        raise ComparisonCheckpointError(f"checkpoint directory not found: {bundle_dir}")
    ok, msg = verify_manifest_sha256(bundle_dir)
    if not ok:
        raise ComparisonCheckpointError(f"MANIFEST.sha256 verification failed: {msg}")
    index_path = bundle_dir / INDEX_ARTIFACT_REL
    _validate_regular_file(index_path, label=INDEX_ARTIFACT_REL)
    index = read_manifest(index_path)
    _validate_checkpoint_index(index)

    lineage_ref_record = index.get("lineage_ref_record")
    if lineage_ref_record is not None:
        if not isinstance(lineage_ref_record, Mapping):
            raise ComparisonCheckpointError("lineage_ref_record must be an object")
        try:
            ref = lineage_ref_from_mapping(dict(lineage_ref_record))
        except Exception as exc:
            raise ComparisonCheckpointError(f"lineage_ref_record invalid on replay: {exc}") from exc
        if ref.ref_type != LineageRefType.COMPARISON:
            raise ComparisonCheckpointError("lineage_ref_record ref_type must be comparison")
        _cross_check_lineage_ref(
            lineage_ref_record=lineage_ref_record,
            comparison_definition_id=str(index["comparison_definition_id"]),
            result_binding_ref=index["result_binding_ref"],
        )


def produce_comparison_checkpoint_v1(
    *,
    common_bundle_dir: Path | str,
    output_dir: Path | str,
    lineage_ref_path: Path | str | None = None,
) -> ComparisonCheckpointResult:
    """Record a non-authoritative checkpoint over a verified common comparison bundle."""
    common_dir = Path(common_bundle_dir)
    final_dir = Path(output_dir)
    lineage_path = Path(lineage_ref_path) if lineage_ref_path is not None else None

    _validate_output_target(final_dir)
    _reject_unsafe_overlap(common_bundle_dir=common_dir, output_dir=final_dir)

    common_index = _load_verified_common_bundle_index(common_dir)

    lineage_ref_record: dict[str, Any] | None = None
    if lineage_path is not None:
        _reject_symlink(lineage_path, label="lineage ref path")
        if ".." in lineage_path.parts:
            raise ComparisonCheckpointError("lineage ref path must not traverse upward")
        lineage_ref_record = _load_optional_lineage_ref(lineage_path)

    index_payload = build_checkpoint_index_v1(
        common_bundle_dir=common_dir,
        common_bundle_index=common_index,
        lineage_ref_record=lineage_ref_record,
    )

    staging = _staging_dir_for(final_dir)
    if staging.exists():
        raise ComparisonCheckpointError(f"staging directory collision: {staging}")

    try:
        staging.mkdir(parents=True, exist_ok=False)
        index_path = staging / INDEX_ARTIFACT_REL
        index_path.write_text(serialize_checkpoint_index_v1(index_payload), encoding="utf-8")

        write_manifest_sha256(staging)
        ok, msg = verify_manifest_sha256(staging)
        if not ok:
            raise ComparisonCheckpointError(
                f"MANIFEST.sha256 verification failed before publish: {msg}"
            )

        reverify_comparison_checkpoint_v1(output_dir=staging)
        staging.replace(final_dir)

        ok, msg = verify_manifest_sha256(final_dir)
        if not ok:
            raise ComparisonCheckpointError(
                f"MANIFEST.sha256 verification failed after publish: {msg}"
            )
    except Exception:
        _cleanup_staging(staging)
        if final_dir.exists():
            shutil.rmtree(final_dir)
        raise

    checkpoint_id = str(index_payload["integrity"]["content_sha256"])
    return ComparisonCheckpointResult(
        output_dir=final_dir,
        comparison_definition_id=str(common_index["comparison_definition_id"]),
        checkpoint_id=checkpoint_id,
        checkpoint_index_path=final_dir / INDEX_ARTIFACT_REL,
        manifest_path=final_dir / MANIFEST_FILENAME,
    )


__all__ = [
    "CHECKPOINT_RELATION",
    "CHECKPOINT_SCHEMA_VERSION",
    "COMPARISON_AUTHORITY_INVARIANTS",
    "INDEX_ARTIFACT_REL",
    "MANIFEST_FILENAME",
    "RECORD_KIND",
    "ComparisonCheckpointError",
    "ComparisonCheckpointResult",
    "build_checkpoint_index_v1",
    "produce_comparison_checkpoint_v1",
    "reverify_comparison_checkpoint_v1",
    "serialize_checkpoint_index_v1",
]
