"""Offline durable evidence binding aggregating comparison chain sub-bundles v1."""

from __future__ import annotations

import hashlib
import shutil
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from scripts.ops.primary_evidence_retention_v0 import (
    is_under_tmp,
    verify_manifest_sha256,
    write_manifest_sha256,
)
from src.meta.learning_loop.comparison_metric_input_durable_evidence_binding_v1 import (
    INDEX_ARTIFACT_REL as METRIC_INPUT_INDEX_ARTIFACT_REL,
    reverify_comparison_metric_input_durable_evidence_bundle_v1,
)
from src.meta.learning_loop.comparison_ssot_definition_durable_evidence_binding_v1 import (
    INDEX_ARTIFACT_REL as DEFINITION_INDEX_ARTIFACT_REL,
    reverify_comparison_ssot_definition_durable_evidence_bundle_v1,
)
from src.meta.learning_loop.comparison_ssot_result_durable_evidence_binding_v1 import (
    INDEX_ARTIFACT_REL as RESULT_INDEX_ARTIFACT_REL,
    reverify_comparison_ssot_result_durable_evidence_bundle_v1,
)
from src.meta.learning_loop.comparison_ssot_v1.constants import COMPARISON_CONTRACT_VERSION
from src.meta.learning_loop.comparison_ssot_v1.io import read_manifest
from src.meta.learning_loop.contract_safety_v1 import (
    compute_content_sha256,
    deterministic_json_dumps,
    is_valid_sha256_hex,
)

BINDING_SCHEMA_VERSION = "comparison_common_durable_evidence_binding_v1"
BINDING_RELATION = "PRESERVES_COMPARISON_CHAIN_REFERENCES"
INDEX_ARTIFACT_REL = "comparison_common_durable_evidence_binding_index_v1.json"
MANIFEST_FILENAME = "MANIFEST.sha256"
STAGING_DIRNAME_PREFIX = ".comparison_common_durable_evidence_staging_"

MIN_METRIC_INPUT_BINDINGS = 2
MAX_METRIC_INPUT_BINDINGS = 32

METRIC_INPUT_EMBED_PREFIX = "embedded/metric_input_bindings"
DEFINITION_EMBED_PREFIX = "embedded/definition_binding"
RESULT_EMBED_PREFIX = "embedded/result_binding"

FUTURES_SCOPE_REF: dict[str, bool] = {
    "futures_only": True,
    "bitcoin_direction_allowed": False,
}
TRADING_LOGIC_IMMUTABILITY_REF: dict[str, bool] = {
    "trading_logic_immutability": True,
}
COMPARISON_AUTHORITY_INVARIANTS: dict[str, bool] = {
    "comparison_is_descriptive_only": True,
    "comparison_does_not_select": True,
    "comparison_does_not_accept": True,
    "comparison_does_not_promote": True,
    "comparison_does_not_authorize_runtime": True,
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
        "completed",
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
        "promotion",
        "runtime_authorized",
        "shadow_authorized",
        "paper_authorized",
        "testnet_authorized",
        "live_authorized",
        "orders_allowed",
        "armed",
        "enabled",
    }
)


class ComparisonCommonDurableEvidenceBindingError(ValueError):
    """Fail-closed common comparison durable evidence binding error."""


@dataclass(frozen=True)
class BoundArtifactRecord:
    artifact_kind: str
    relative_path: str
    content_sha256: str


@dataclass(frozen=True)
class MetricInputBindingRef:
    comparison_metric_input_id: str
    binding_index_integrity_sha256: str
    relative_path: str
    definition_input_ref: dict[str, str]
    source_domain: str


@dataclass(frozen=True)
class UpstreamBindingRef:
    binding_index_integrity_sha256: str
    relative_path: str
    manifest_content_sha256: str


@dataclass(frozen=True)
class ComparisonChainCrossReferences:
    comparison_definition_id: str
    definition_input_refs: tuple[dict[str, str], ...]
    result_input_snapshot_ids: tuple[str, ...]


@dataclass(frozen=True)
class ComparisonCommonDurableEvidenceBindingResult:
    output_dir: Path
    comparison_definition_id: str
    binding_index_path: Path
    manifest_path: Path
    metric_input_binding_count: int


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _reject_symlink(path: Path, *, label: str) -> None:
    if path.is_symlink():
        raise ComparisonCommonDurableEvidenceBindingError(f"{label} must not be a symlink: {path}")


def _reject_forbidden_index_keys(payload: Mapping[str, Any]) -> None:
    for key in payload:
        if key in _FORBIDDEN_INDEX_KEYS:
            raise ComparisonCommonDurableEvidenceBindingError(
                f"binding index must not contain forbidden key: {key}"
            )


def _validate_regular_file(path: Path, *, label: str) -> None:
    if not path.exists():
        raise ComparisonCommonDurableEvidenceBindingError(f"{label} not found: {path}")
    _reject_symlink(path, label=label)
    if not path.is_file():
        raise ComparisonCommonDurableEvidenceBindingError(f"{label} must be a regular file: {path}")


def _validate_bundle_dir(bundle_dir: Path, *, label: str) -> None:
    if not bundle_dir.is_dir():
        raise ComparisonCommonDurableEvidenceBindingError(
            f"{label} must be a directory: {bundle_dir}"
        )
    _reject_symlink(bundle_dir, label=label)


def _validate_output_target(output_dir: Path) -> None:
    if output_dir.exists():
        raise ComparisonCommonDurableEvidenceBindingError(
            f"output directory already exists (fail-closed): {output_dir}"
        )
    if is_under_tmp(output_dir):
        raise ComparisonCommonDurableEvidenceBindingError("output directory must be outside /tmp")
    parent = output_dir.parent
    if not parent.is_dir():
        raise ComparisonCommonDurableEvidenceBindingError(
            f"output parent directory missing: {parent}"
        )
    if is_under_tmp(parent):
        raise ComparisonCommonDurableEvidenceBindingError(
            "output parent directory must be outside /tmp"
        )


def _path_is_under(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def _validate_bundle_relative_path(rel: str) -> None:
    candidate = Path(rel)
    if candidate.is_absolute():
        raise ComparisonCommonDurableEvidenceBindingError(
            f"bundle relative path must not be absolute: {rel!r}"
        )
    if ".." in candidate.parts:
        raise ComparisonCommonDurableEvidenceBindingError(
            f"bundle relative path must not traverse upward: {rel!r}"
        )


def _reject_unsafe_overlap(
    *,
    definition_bound_bundle_dir: Path,
    result_bound_bundle_dir: Path,
    metric_input_bound_bundle_dirs: Sequence[Path],
    output_dir: Path,
) -> None:
    output_res = output_dir.resolve()
    for label, bundle_dir in (
        ("definition bound bundle", definition_bound_bundle_dir),
        ("result bound bundle", result_bound_bundle_dir),
        *(
            (f"metric input bound bundle[{idx}]", path)
            for idx, path in enumerate(metric_input_bound_bundle_dirs)
        ),
    ):
        bundle_res = bundle_dir.resolve()
        if output_res == bundle_res:
            raise ComparisonCommonDurableEvidenceBindingError(
                f"output directory must not equal {label} path (fail-closed)"
            )
        if _path_is_under(bundle_res, output_res):
            raise ComparisonCommonDurableEvidenceBindingError(
                f"{label} must not be inside output directory (fail-closed)"
            )
        if _path_is_under(output_res, bundle_res):
            raise ComparisonCommonDurableEvidenceBindingError(
                f"output directory must not be inside {label} path (fail-closed)"
            )


def _binding_index_integrity_sha256(index: Mapping[str, Any], *, label: str) -> str:
    integrity = index.get("integrity")
    if not isinstance(integrity, Mapping):
        raise ComparisonCommonDurableEvidenceBindingError(f"{label} integrity must be an object")
    digest = integrity.get("content_sha256")
    if not isinstance(digest, str) or not digest.strip():
        raise ComparisonCommonDurableEvidenceBindingError(
            f"{label} integrity.content_sha256 missing or invalid"
        )
    if not is_valid_sha256_hex(digest):
        raise ComparisonCommonDurableEvidenceBindingError(
            f"{label} integrity.content_sha256 must be valid sha256 hex"
        )
    return digest


def _manifest_content_sha256(index: Mapping[str, Any], *, label: str) -> str:
    cross = index.get("cross_references")
    if not isinstance(cross, Mapping):
        raise ComparisonCommonDurableEvidenceBindingError(
            f"{label} cross_references must be an object"
        )
    digest = cross.get("manifest_content_sha256")
    if not isinstance(digest, str) or not digest.strip():
        raise ComparisonCommonDurableEvidenceBindingError(
            f"{label} cross_references.manifest_content_sha256 missing or invalid"
        )
    if not is_valid_sha256_hex(digest):
        raise ComparisonCommonDurableEvidenceBindingError(
            f"{label} cross_references.manifest_content_sha256 must be valid sha256 hex"
        )
    return digest


def _source_ref_key(ref: Mapping[str, Any]) -> tuple[str, str, str, str]:
    return (
        str(ref["owner_domain"]),
        str(ref["ref_type"]),
        str(ref["ref_id"]),
        str(ref["digest"]),
    )


def _verbatim_definition_input_ref(ref: Mapping[str, Any]) -> dict[str, str]:
    return {
        "owner_domain": str(ref["owner_domain"]),
        "ref_type": str(ref["ref_type"]),
        "ref_id": str(ref["ref_id"]),
        "digest": str(ref["digest"]),
    }


def _load_definition_binding_index(bundle_dir: Path) -> dict[str, Any]:
    _validate_bundle_dir(bundle_dir, label="definition bound bundle")
    reverify_comparison_ssot_definition_durable_evidence_bundle_v1(output_dir=bundle_dir)
    index_path = bundle_dir / DEFINITION_INDEX_ARTIFACT_REL
    return read_manifest(index_path)


def _load_result_binding_index(bundle_dir: Path) -> dict[str, Any]:
    _validate_bundle_dir(bundle_dir, label="result bound bundle")
    reverify_comparison_ssot_result_durable_evidence_bundle_v1(output_dir=bundle_dir)
    index_path = bundle_dir / RESULT_INDEX_ARTIFACT_REL
    return read_manifest(index_path)


def _load_metric_input_binding_index(bundle_dir: Path, *, label: str) -> dict[str, Any]:
    _validate_bundle_dir(bundle_dir, label=label)
    reverify_comparison_metric_input_durable_evidence_bundle_v1(output_dir=bundle_dir)
    index_path = bundle_dir / METRIC_INPUT_INDEX_ARTIFACT_REL
    return read_manifest(index_path)


def check_reference_consistency(
    *,
    definition_bound_bundle_dir: Path | str,
    result_bound_bundle_dir: Path | str,
    metric_input_bound_bundle_dirs: Sequence[Path | str],
) -> ComparisonChainCrossReferences:
    """Fail-closed cross-reference chain lock across upstream bound bundles."""
    definition_dir = Path(definition_bound_bundle_dir)
    result_dir = Path(result_bound_bundle_dir)
    metric_dirs = tuple(Path(item) for item in metric_input_bound_bundle_dirs)

    if len(metric_dirs) != len(set(item.resolve() for item in metric_dirs)):
        raise ComparisonCommonDurableEvidenceBindingError(
            "duplicate metric input bound bundle paths (fail-closed)"
        )

    definition_index = _load_definition_binding_index(definition_dir)
    result_index = _load_result_binding_index(result_dir)

    definition_id = definition_index.get("comparison_definition_id")
    result_id = result_index.get("comparison_definition_id")
    if not isinstance(definition_id, str) or not definition_id.strip():
        raise ComparisonCommonDurableEvidenceBindingError(
            "definition binding comparison_definition_id missing or invalid"
        )
    if not isinstance(result_id, str) or not result_id.strip():
        raise ComparisonCommonDurableEvidenceBindingError(
            "result binding comparison_definition_id missing or invalid"
        )
    if definition_id != result_id:
        raise ComparisonCommonDurableEvidenceBindingError(
            "definition and result comparison_definition_id mismatch (fail-closed)"
        )

    raw_definition_input_refs = definition_index.get("definition_input_refs")
    if not isinstance(raw_definition_input_refs, list):
        raise ComparisonCommonDurableEvidenceBindingError("definition_input_refs must be a list")
    definition_input_refs = tuple(
        _verbatim_definition_input_ref(ref)
        for ref in raw_definition_input_refs
        if isinstance(ref, Mapping)
    )
    if len(definition_input_refs) != len(raw_definition_input_refs):
        raise ComparisonCommonDurableEvidenceBindingError("definition_input_refs must be objects")

    cardinality = len(definition_input_refs)
    if cardinality < MIN_METRIC_INPUT_BINDINGS or cardinality > MAX_METRIC_INPUT_BINDINGS:
        raise ComparisonCommonDurableEvidenceBindingError(
            f"metric input cardinality must be {MIN_METRIC_INPUT_BINDINGS}.."
            f"{MAX_METRIC_INPUT_BINDINGS}, got {cardinality}"
        )
    if len(metric_dirs) != cardinality:
        raise ComparisonCommonDurableEvidenceBindingError(
            "metric input bound bundle count must match definition_input_refs cardinality"
        )

    lookup: dict[tuple[str, str, str, str], tuple[Path, dict[str, Any]]] = {}
    for idx, bundle_dir in enumerate(metric_dirs):
        label = f"metric input bound bundle[{idx}]"
        index = _load_metric_input_binding_index(bundle_dir, label=label)
        source_ref = index.get("comparison_metric_input_source_ref")
        if not isinstance(source_ref, Mapping):
            raise ComparisonCommonDurableEvidenceBindingError(
                f"{label} comparison_metric_input_source_ref must be an object"
            )
        key = _source_ref_key(source_ref)
        if key in lookup:
            raise ComparisonCommonDurableEvidenceBindingError(
                "ambiguous metric input binding mapping (duplicate source ref)"
            )
        lookup[key] = (bundle_dir, index)

    ordered_metric_refs: list[MetricInputBindingRef] = []
    used_dirs: set[Path] = set()
    for def_ref in definition_input_refs:
        key = (
            def_ref["owner_domain"],
            def_ref["ref_type"],
            def_ref["ref_id"],
            def_ref["digest"],
        )
        match = lookup.get(key)
        if match is None:
            raise ComparisonCommonDurableEvidenceBindingError(
                "missing metric input bound bundle for definition input ref"
            )
        bundle_dir, index = match
        bundle_res = bundle_dir.resolve()
        if bundle_res in used_dirs:
            raise ComparisonCommonDurableEvidenceBindingError(
                "duplicate metric input bound bundle assignment (fail-closed)"
            )
        used_dirs.add(bundle_res)
        comparison_metric_input_id = index.get("comparison_metric_input_id")
        if (
            not isinstance(comparison_metric_input_id, str)
            or not comparison_metric_input_id.strip()
        ):
            raise ComparisonCommonDurableEvidenceBindingError(
                "metric input binding comparison_metric_input_id missing or invalid"
            )
        ordered_metric_refs.append(
            MetricInputBindingRef(
                comparison_metric_input_id=comparison_metric_input_id,
                binding_index_integrity_sha256=_binding_index_integrity_sha256(
                    index, label="metric input binding index"
                ),
                relative_path="",
                definition_input_ref=def_ref,
                source_domain=str(index.get("source_domain", "")),
            )
        )

    raw_result_snapshots = result_index.get("result_input_snapshots")
    if not isinstance(raw_result_snapshots, list):
        raise ComparisonCommonDurableEvidenceBindingError("result_input_snapshots must be a list")
    result_ids: list[str] = []
    for idx, snap in enumerate(raw_result_snapshots):
        if not isinstance(snap, Mapping):
            raise ComparisonCommonDurableEvidenceBindingError(
                f"result_input_snapshots[{idx}] must be an object"
            )
        metric_id = snap.get("comparison_metric_input_id")
        if not isinstance(metric_id, str) or not metric_id.strip():
            raise ComparisonCommonDurableEvidenceBindingError(
                f"result_input_snapshots[{idx}].comparison_metric_input_id missing or invalid"
            )
        source_ref = snap.get("source_ref")
        if not isinstance(source_ref, Mapping):
            raise ComparisonCommonDurableEvidenceBindingError(
                f"result_input_snapshots[{idx}].source_ref must be an object"
            )
        result_ids.append(metric_id)
        expected_ref = _verbatim_definition_input_ref(source_ref)
        matched = next(
            (item for item in ordered_metric_refs if item.comparison_metric_input_id == metric_id),
            None,
        )
        if matched is None:
            raise ComparisonCommonDurableEvidenceBindingError(
                "result input snapshot comparison_metric_input_id not mapped"
            )
        if matched.definition_input_ref != expected_ref:
            raise ComparisonCommonDurableEvidenceBindingError(
                "result input snapshot source_ref mismatch against definition input ref"
            )

    ordered_ids = tuple(item.comparison_metric_input_id for item in ordered_metric_refs)
    if tuple(result_ids) != ordered_ids:
        raise ComparisonCommonDurableEvidenceBindingError(
            "result_input_snapshots ordering or ids mismatch against definition order"
        )

    return ComparisonChainCrossReferences(
        comparison_definition_id=definition_id,
        definition_input_refs=tuple(definition_input_refs),
        result_input_snapshot_ids=tuple(result_ids),
    )


def _resolve_ordered_metric_refs(
    *,
    definition_bound_bundle_dir: Path,
    result_bound_bundle_dir: Path,
    metric_input_bound_bundle_dirs: Sequence[Path],
) -> tuple[
    ComparisonChainCrossReferences,
    dict[str, Any],
    dict[str, Any],
    list[tuple[Path, dict[str, Any]]],
]:
    chain = check_reference_consistency(
        definition_bound_bundle_dir=definition_bound_bundle_dir,
        result_bound_bundle_dir=result_bound_bundle_dir,
        metric_input_bound_bundle_dirs=metric_input_bound_bundle_dirs,
    )
    definition_index = read_manifest(definition_bound_bundle_dir / DEFINITION_INDEX_ARTIFACT_REL)
    result_index = read_manifest(result_bound_bundle_dir / RESULT_INDEX_ARTIFACT_REL)

    lookup: dict[tuple[str, str, str, str], tuple[Path, dict[str, Any]]] = {}
    for idx, bundle_dir in enumerate(metric_input_bound_bundle_dirs):
        index = read_manifest(bundle_dir / METRIC_INPUT_INDEX_ARTIFACT_REL)
        source_ref = index["comparison_metric_input_source_ref"]
        lookup[_source_ref_key(source_ref)] = (bundle_dir, index)

    ordered_pairs: list[tuple[Path, dict[str, Any]]] = []
    for def_ref in chain.definition_input_refs:
        key = (
            def_ref["owner_domain"],
            def_ref["ref_type"],
            def_ref["ref_id"],
            def_ref["digest"],
        )
        ordered_pairs.append(lookup[key])

    return chain, definition_index, result_index, ordered_pairs


def build_binding_index_v1(
    *,
    chain_cross_references: ComparisonChainCrossReferences,
    metric_input_binding_refs: Sequence[MetricInputBindingRef],
    definition_binding_ref: UpstreamBindingRef,
    result_binding_ref: UpstreamBindingRef,
    artifacts: tuple[BoundArtifactRecord, ...],
) -> dict[str, Any]:
    sorted_artifacts = sorted(
        artifacts,
        key=lambda item: (item.artifact_kind, item.relative_path),
    )
    payload: dict[str, Any] = {
        "schema_version": BINDING_SCHEMA_VERSION,
        "bound_contract": COMPARISON_CONTRACT_VERSION,
        "comparison_definition_id": chain_cross_references.comparison_definition_id,
        "binding_relation": BINDING_RELATION,
        "metric_input_binding_refs": [
            {
                "comparison_metric_input_id": item.comparison_metric_input_id,
                "binding_index_integrity_sha256": item.binding_index_integrity_sha256,
                "relative_path": item.relative_path,
                "definition_input_ref": dict(item.definition_input_ref),
                "source_domain": item.source_domain,
            }
            for item in metric_input_binding_refs
        ],
        "definition_binding_ref": {
            "binding_index_integrity_sha256": definition_binding_ref.binding_index_integrity_sha256,
            "relative_path": definition_binding_ref.relative_path,
            "manifest_content_sha256": definition_binding_ref.manifest_content_sha256,
        },
        "result_binding_ref": {
            "binding_index_integrity_sha256": result_binding_ref.binding_index_integrity_sha256,
            "relative_path": result_binding_ref.relative_path,
            "manifest_content_sha256": result_binding_ref.manifest_content_sha256,
        },
        "chain_cross_references": {
            "comparison_definition_id": chain_cross_references.comparison_definition_id,
            "definition_input_refs": [
                dict(item) for item in chain_cross_references.definition_input_refs
            ],
            "result_input_snapshot_ids": list(chain_cross_references.result_input_snapshot_ids),
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
        "comparison_authority_invariants": dict(COMPARISON_AUTHORITY_INVARIANTS),
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
        raise ComparisonCommonDurableEvidenceBindingError(
            f"byte-identical copy failed for {source.name}"
        )
    return source_digest


def _embed_bound_bundle(
    *,
    source_dir: Path,
    staging_root: Path,
    embed_relative_prefix: str,
    artifact_kind_prefix: str,
) -> tuple[str, list[BoundArtifactRecord]]:
    _validate_bundle_dir(source_dir, label="bound bundle source")
    embed_root = staging_root / embed_relative_prefix
    artifacts: list[BoundArtifactRecord] = []
    for src_file in sorted(source_dir.rglob("*")):
        if not src_file.is_file():
            continue
        _reject_symlink(src_file, label="embedded artifact source")
        rel_inside = src_file.relative_to(source_dir).as_posix()
        rel_path = f"{embed_relative_prefix}/{rel_inside}"
        _validate_bundle_relative_path(rel_path)
        dest_file = staging_root / rel_path
        digest = _copy_byte_identical(src_file, dest_file)
        artifacts.append(
            BoundArtifactRecord(
                artifact_kind=f"{artifact_kind_prefix}_{Path(rel_inside).name}",
                relative_path=rel_path,
                content_sha256=digest,
            )
        )
    return embed_relative_prefix, artifacts


def _staging_dir_for(output_dir: Path) -> Path:
    token = uuid.uuid4().hex
    return output_dir.parent / f"{STAGING_DIRNAME_PREFIX}{token}"


def _cleanup_staging(staging: Path) -> None:
    if staging.exists():
        shutil.rmtree(staging)


def _validate_chain_from_index(index: Mapping[str, Any]) -> None:
    if index.get("binding_relation") != BINDING_RELATION:
        raise ComparisonCommonDurableEvidenceBindingError("binding_relation mismatch")
    if index.get("evidence_does_not_authorize_runtime") is not True:
        raise ComparisonCommonDurableEvidenceBindingError(
            "evidence_does_not_authorize_runtime must be true"
        )
    invariants = index.get("comparison_authority_invariants")
    if invariants != COMPARISON_AUTHORITY_INVARIANTS:
        raise ComparisonCommonDurableEvidenceBindingError(
            "comparison_authority_invariants mismatch"
        )


def reverify_comparison_common_durable_evidence_bundle_v1(
    *,
    output_dir: Path | str,
) -> None:
    """Replay common durable evidence bundle without producer or raw source access."""
    bundle_dir = Path(output_dir)
    if not bundle_dir.is_dir():
        raise ComparisonCommonDurableEvidenceBindingError(
            f"bundle directory not found: {bundle_dir}"
        )
    ok, msg = verify_manifest_sha256(bundle_dir)
    if not ok:
        raise ComparisonCommonDurableEvidenceBindingError(
            f"MANIFEST.sha256 verification failed: {msg}"
        )
    index_path = bundle_dir / INDEX_ARTIFACT_REL
    _validate_regular_file(index_path, label=INDEX_ARTIFACT_REL)
    index = read_manifest(index_path)
    _validate_chain_from_index(index)

    metric_refs = index.get("metric_input_binding_refs")
    if not isinstance(metric_refs, list):
        raise ComparisonCommonDurableEvidenceBindingError(
            "metric_input_binding_refs must be a list"
        )
    definition_ref = index.get("definition_binding_ref")
    result_ref = index.get("result_binding_ref")
    if not isinstance(definition_ref, Mapping) or not isinstance(result_ref, Mapping):
        raise ComparisonCommonDurableEvidenceBindingError(
            "definition_binding_ref and result_binding_ref must be objects"
        )

    metric_dirs: list[Path] = []
    for idx, ref in enumerate(metric_refs):
        if not isinstance(ref, Mapping):
            raise ComparisonCommonDurableEvidenceBindingError(
                f"metric_input_binding_refs[{idx}] must be an object"
            )
        rel = str(ref.get("relative_path", ""))
        _validate_bundle_relative_path(rel)
        embedded = bundle_dir / rel
        metric_dirs.append(embedded)
        reverify_comparison_metric_input_durable_evidence_bundle_v1(output_dir=embedded)
        sub_index = read_manifest(embedded / METRIC_INPUT_INDEX_ARTIFACT_REL)
        if sub_index["integrity"]["content_sha256"] != ref.get("binding_index_integrity_sha256"):
            raise ComparisonCommonDurableEvidenceBindingError(
                "metric input binding index integrity mismatch on replay"
            )

    def_rel = str(definition_ref["relative_path"])
    res_rel = str(result_ref["relative_path"])
    _validate_bundle_relative_path(def_rel)
    _validate_bundle_relative_path(res_rel)
    definition_embedded = bundle_dir / def_rel
    result_embedded = bundle_dir / res_rel
    reverify_comparison_ssot_definition_durable_evidence_bundle_v1(output_dir=definition_embedded)
    reverify_comparison_ssot_result_durable_evidence_bundle_v1(output_dir=result_embedded)

    def_index = read_manifest(definition_embedded / DEFINITION_INDEX_ARTIFACT_REL)
    res_index = read_manifest(result_embedded / RESULT_INDEX_ARTIFACT_REL)
    if def_index["integrity"]["content_sha256"] != definition_ref.get(
        "binding_index_integrity_sha256"
    ):
        raise ComparisonCommonDurableEvidenceBindingError(
            "definition binding index integrity mismatch on replay"
        )
    if res_index["integrity"]["content_sha256"] != result_ref.get("binding_index_integrity_sha256"):
        raise ComparisonCommonDurableEvidenceBindingError(
            "result binding index integrity mismatch on replay"
        )

    chain = check_reference_consistency(
        definition_bound_bundle_dir=definition_embedded,
        result_bound_bundle_dir=result_embedded,
        metric_input_bound_bundle_dirs=metric_dirs,
    )
    chain_block = index.get("chain_cross_references")
    if not isinstance(chain_block, Mapping):
        raise ComparisonCommonDurableEvidenceBindingError(
            "chain_cross_references must be an object"
        )
    if chain_block.get("comparison_definition_id") != chain.comparison_definition_id:
        raise ComparisonCommonDurableEvidenceBindingError(
            "chain_cross_references comparison_definition_id mismatch on replay"
        )
    if tuple(chain_block.get("definition_input_refs", [])) != chain.definition_input_refs:
        raise ComparisonCommonDurableEvidenceBindingError(
            "chain_cross_references definition_input_refs mismatch on replay"
        )
    if tuple(chain_block.get("result_input_snapshot_ids", [])) != chain.result_input_snapshot_ids:
        raise ComparisonCommonDurableEvidenceBindingError(
            "chain_cross_references result_input_snapshot_ids mismatch on replay"
        )


def produce_comparison_common_durable_evidence_bundle_v1(
    *,
    definition_bound_bundle_dir: Path | str,
    result_bound_bundle_dir: Path | str,
    metric_input_bound_bundle_dirs: Sequence[Path | str],
    output_dir: Path | str,
) -> ComparisonCommonDurableEvidenceBindingResult:
    """Aggregate verified comparison durable evidence sub-bundles into one common bundle."""
    definition_dir = Path(definition_bound_bundle_dir)
    result_dir = Path(result_bound_bundle_dir)
    metric_dirs = tuple(Path(item) for item in metric_input_bound_bundle_dirs)
    final_dir = Path(output_dir)

    _validate_output_target(final_dir)
    _reject_unsafe_overlap(
        definition_bound_bundle_dir=definition_dir,
        result_bound_bundle_dir=result_dir,
        metric_input_bound_bundle_dirs=metric_dirs,
        output_dir=final_dir,
    )

    chain, definition_index, result_index, ordered_pairs = _resolve_ordered_metric_refs(
        definition_bound_bundle_dir=definition_dir,
        result_bound_bundle_dir=result_dir,
        metric_input_bound_bundle_dirs=metric_dirs,
    )

    _validate_bundle_relative_path(INDEX_ARTIFACT_REL)
    staging = _staging_dir_for(final_dir)
    if staging.exists():
        raise ComparisonCommonDurableEvidenceBindingError(f"staging directory collision: {staging}")

    try:
        staging.mkdir(parents=True, exist_ok=False)
        artifacts: list[BoundArtifactRecord] = []

        metric_binding_refs: list[MetricInputBindingRef] = []
        for ordinal, ((bundle_dir, index), def_ref) in enumerate(
            zip(ordered_pairs, chain.definition_input_refs, strict=True)
        ):
            embed_prefix = f"{METRIC_INPUT_EMBED_PREFIX}/{ordinal:02d}"
            _, embedded_artifacts = _embed_bound_bundle(
                source_dir=bundle_dir,
                staging_root=staging,
                embed_relative_prefix=embed_prefix,
                artifact_kind_prefix="comparison_metric_input_bound_bundle",
            )
            artifacts.extend(embedded_artifacts)
            metric_binding_refs.append(
                MetricInputBindingRef(
                    comparison_metric_input_id=str(index["comparison_metric_input_id"]),
                    binding_index_integrity_sha256=_binding_index_integrity_sha256(
                        index, label="metric input binding index"
                    ),
                    relative_path=embed_prefix,
                    definition_input_ref=def_ref,
                    source_domain=str(index.get("source_domain", "")),
                )
            )

        _, definition_artifacts = _embed_bound_bundle(
            source_dir=definition_dir,
            staging_root=staging,
            embed_relative_prefix=DEFINITION_EMBED_PREFIX,
            artifact_kind_prefix="comparison_definition_bound_bundle",
        )
        artifacts.extend(definition_artifacts)

        _, result_artifacts = _embed_bound_bundle(
            source_dir=result_dir,
            staging_root=staging,
            embed_relative_prefix=RESULT_EMBED_PREFIX,
            artifact_kind_prefix="comparison_result_bound_bundle",
        )
        artifacts.extend(result_artifacts)

        definition_binding_ref = UpstreamBindingRef(
            binding_index_integrity_sha256=_binding_index_integrity_sha256(
                definition_index, label="definition binding index"
            ),
            relative_path=DEFINITION_EMBED_PREFIX,
            manifest_content_sha256=_manifest_content_sha256(
                definition_index, label="definition binding index"
            ),
        )
        result_binding_ref = UpstreamBindingRef(
            binding_index_integrity_sha256=_binding_index_integrity_sha256(
                result_index, label="result binding index"
            ),
            relative_path=RESULT_EMBED_PREFIX,
            manifest_content_sha256=_manifest_content_sha256(
                result_index, label="result binding index"
            ),
        )

        index_payload = build_binding_index_v1(
            chain_cross_references=chain,
            metric_input_binding_refs=metric_binding_refs,
            definition_binding_ref=definition_binding_ref,
            result_binding_ref=result_binding_ref,
            artifacts=tuple(artifacts),
        )
        index_path = staging / INDEX_ARTIFACT_REL
        index_path.write_text(serialize_binding_index_v1(index_payload), encoding="utf-8")

        write_manifest_sha256(staging)
        ok, msg = verify_manifest_sha256(staging)
        if not ok:
            raise ComparisonCommonDurableEvidenceBindingError(
                f"MANIFEST.sha256 verification failed before publish: {msg}"
            )

        reverify_comparison_common_durable_evidence_bundle_v1(output_dir=staging)

        staging.replace(final_dir)

        ok, msg = verify_manifest_sha256(final_dir)
        if not ok:
            raise ComparisonCommonDurableEvidenceBindingError(
                f"MANIFEST.sha256 verification failed after publish: {msg}"
            )
    except Exception:
        _cleanup_staging(staging)
        if final_dir.exists():
            shutil.rmtree(final_dir)
        raise

    return ComparisonCommonDurableEvidenceBindingResult(
        output_dir=final_dir,
        comparison_definition_id=chain.comparison_definition_id,
        binding_index_path=final_dir / INDEX_ARTIFACT_REL,
        manifest_path=final_dir / MANIFEST_FILENAME,
        metric_input_binding_count=len(metric_binding_refs),
    )


__all__ = [
    "BINDING_RELATION",
    "BINDING_SCHEMA_VERSION",
    "COMPARISON_AUTHORITY_INVARIANTS",
    "INDEX_ARTIFACT_REL",
    "MANIFEST_FILENAME",
    "MAX_METRIC_INPUT_BINDINGS",
    "MIN_METRIC_INPUT_BINDINGS",
    "BoundArtifactRecord",
    "ComparisonChainCrossReferences",
    "ComparisonCommonDurableEvidenceBindingError",
    "ComparisonCommonDurableEvidenceBindingResult",
    "MetricInputBindingRef",
    "UpstreamBindingRef",
    "build_binding_index_v1",
    "check_reference_consistency",
    "produce_comparison_common_durable_evidence_bundle_v1",
    "reverify_comparison_common_durable_evidence_bundle_v1",
    "serialize_binding_index_v1",
]
