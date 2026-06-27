"""CandidateLineageManifest v1 — offline reference-only cross-domain FK graph."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Mapping

from src.meta.learning_loop.contract_safety_v1 import (
    SCHEMA_VERSION_V1,
    ValidationPhase,
    canonical_futures_scope_ref,
    canonical_trading_logic_immutability_ref,
    compute_content_sha256,
    deterministic_json_dumps,
    is_valid_sha256_hex,
    is_valid_uuid,
    validate_futures_scope_ref,
    validate_integrity_block,
    validate_schema_version,
    validate_trading_logic_immutability_ref,
)


class CandidateLineageManifestError(ValueError):
    """Fail-closed CandidateLineageManifest v1 error."""


class CandidateType(str, Enum):
    CONFIG_PATCH_BUNDLE = "config_patch_bundle"
    SWEEP_CONFIG = "sweep_config"
    WALKFORWARD_CONFIG = "walkforward_config"


class LineageRefType(str, Enum):
    FEATURE_SNAPSHOT = "feature_snapshot"
    EXPERIMENT = "experiment"
    BACKTEST = "backtest"
    REPLAY = "replay"
    VAR_SUITE = "var_suite"
    PERFORMANCE_EVIDENCE = "performance_evidence"
    ROBUSTNESS_EVIDENCE = "robustness_evidence"
    EVIDENCE_OPS = "evidence_ops"
    EVIDENCE_AI = "evidence_ai"
    COMPARISON = "comparison"
    PROMOTION_PROPOSAL = "promotion_proposal"
    PARENT_LINEAGE = "parent_lineage"


class LineageRelation(str, Enum):
    SOURCES = "sources"
    EVALUATES = "evaluates"
    VALIDATES = "validates"
    COMPARES = "compares"
    PROPOSES = "proposes"
    RETAINS = "retains"
    REPRODUCES = "reproduces"
    EXTENDS = "extends"


_REF_TYPE_CARDINALITY: dict[LineageRefType, tuple[int, int | None]] = {
    LineageRefType.FEATURE_SNAPSHOT: (0, None),
    LineageRefType.EXPERIMENT: (0, 1),
    LineageRefType.BACKTEST: (0, None),
    LineageRefType.REPLAY: (0, None),
    LineageRefType.VAR_SUITE: (0, None),
    LineageRefType.PERFORMANCE_EVIDENCE: (0, None),
    LineageRefType.ROBUSTNESS_EVIDENCE: (0, None),
    LineageRefType.EVIDENCE_OPS: (0, None),
    LineageRefType.EVIDENCE_AI: (0, None),
    LineageRefType.COMPARISON: (0, None),
    LineageRefType.PROMOTION_PROPOSAL: (0, 1),
    LineageRefType.PARENT_LINEAGE: (0, None),
}


@dataclass(frozen=True)
class LineageIntegrity:
    content_sha256: str


@dataclass(frozen=True)
class LineageRef:
    ref_type: LineageRefType
    ref_id: str
    relation: LineageRelation
    owner_domain: str
    required: bool
    digest: str | None = None
    artifact_path: str | None = None
    schema_version: str | None = None


@dataclass
class CandidateLineageManifestV1:
    schema_version: str
    lineage_manifest_id: str
    candidate_id: str
    candidate_type: CandidateType
    candidate_contract_ref: str
    refs: list[LineageRef]
    created_at: datetime
    futures_scope_ref: dict[str, Any]
    trading_logic_immutability_ref: dict[str, Any]
    integrity: LineageIntegrity | None = None
    parent_lineage_manifest_ids: list[str] = field(default_factory=list)
    created_by: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


def _parse_datetime(value: Any, *, field_name: str) -> datetime:
    if isinstance(value, datetime):
        return value
    if not isinstance(value, str) or not value.strip():
        raise CandidateLineageManifestError(f"{field_name} must be an ISO8601 string")
    normalized = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise CandidateLineageManifestError(f"{field_name} must be an ISO8601 string") from exc


def lineage_ref_from_mapping(raw: Mapping[str, Any]) -> LineageRef:
    required = ("ref_type", "ref_id", "relation", "owner_domain", "required")
    for key in required:
        if key not in raw:
            raise CandidateLineageManifestError(f"ref missing required field: {key}")

    try:
        ref_type = LineageRefType(str(raw["ref_type"]))
    except ValueError as exc:
        raise CandidateLineageManifestError(f"unknown ref_type: {raw['ref_type']!r}") from exc
    try:
        relation = LineageRelation(str(raw["relation"]))
    except ValueError as exc:
        raise CandidateLineageManifestError(f"unknown relation: {raw['relation']!r}") from exc

    digest = raw.get("digest")
    schema_version = raw.get("schema_version")
    artifact_path = raw.get("artifact_path")

    return LineageRef(
        ref_type=ref_type,
        ref_id=str(raw["ref_id"]),
        relation=relation,
        owner_domain=str(raw["owner_domain"]),
        required=bool(raw["required"]),
        digest=str(digest) if digest is not None else None,
        artifact_path=str(artifact_path) if artifact_path is not None else None,
        schema_version=str(schema_version) if schema_version is not None else None,
    )


def lineage_ref_to_mapping(ref: LineageRef) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "ref_type": ref.ref_type.value,
        "ref_id": ref.ref_id,
        "relation": ref.relation.value,
        "owner_domain": ref.owner_domain,
        "required": ref.required,
    }
    if ref.digest is not None:
        payload["digest"] = ref.digest
    if ref.artifact_path is not None:
        payload["artifact_path"] = ref.artifact_path
    if ref.schema_version is not None:
        payload["schema_version"] = ref.schema_version
    return payload


def manifest_to_canonical_dict(
    manifest: CandidateLineageManifestV1,
    *,
    include_integrity: bool = True,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema_version": manifest.schema_version,
        "lineage_manifest_id": manifest.lineage_manifest_id,
        "candidate_id": manifest.candidate_id,
        "candidate_type": manifest.candidate_type.value,
        "candidate_contract_ref": manifest.candidate_contract_ref,
        "refs": [lineage_ref_to_mapping(ref) for ref in manifest.refs],
        "created_at": manifest.created_at.isoformat(),
        "futures_scope_ref": dict(manifest.futures_scope_ref),
        "trading_logic_immutability_ref": dict(manifest.trading_logic_immutability_ref),
    }
    if manifest.parent_lineage_manifest_ids:
        payload["parent_lineage_manifest_ids"] = list(manifest.parent_lineage_manifest_ids)
    if manifest.created_by is not None:
        payload["created_by"] = manifest.created_by
    if manifest.metadata:
        payload["metadata"] = dict(manifest.metadata)
    if include_integrity and manifest.integrity is not None:
        payload["integrity"] = {"content_sha256": manifest.integrity.content_sha256}
    return payload


def compute_lineage_manifest_integrity(manifest: CandidateLineageManifestV1) -> LineageIntegrity:
    payload = manifest_to_canonical_dict(manifest, include_integrity=False)
    return LineageIntegrity(content_sha256=compute_content_sha256(payload))


def serialize_candidate_lineage_manifest_v1(manifest: CandidateLineageManifestV1) -> str:
    if manifest.integrity is None:
        manifest.integrity = compute_lineage_manifest_integrity(manifest)
    return deterministic_json_dumps(manifest_to_canonical_dict(manifest, include_integrity=True))


def deserialize_candidate_lineage_manifest_v1(
    data: Mapping[str, Any],
) -> CandidateLineageManifestV1:
    if not isinstance(data, Mapping):
        raise CandidateLineageManifestError("manifest payload must be a mapping")

    required_fields = (
        "schema_version",
        "lineage_manifest_id",
        "candidate_id",
        "candidate_type",
        "candidate_contract_ref",
        "refs",
        "created_at",
        "futures_scope_ref",
        "trading_logic_immutability_ref",
        "integrity",
    )
    for key in required_fields:
        if key not in data:
            raise CandidateLineageManifestError(f"missing required field: {key}")

    refs_raw = data["refs"]
    if not isinstance(refs_raw, list):
        raise CandidateLineageManifestError("refs must be an array")

    integrity_raw = data["integrity"]
    if not isinstance(integrity_raw, Mapping):
        raise CandidateLineageManifestError("integrity must be an object")
    digest = integrity_raw.get("content_sha256")
    if not isinstance(digest, str):
        raise CandidateLineageManifestError("integrity.content_sha256 must be a string")

    try:
        candidate_type = CandidateType(str(data["candidate_type"]))
    except ValueError as exc:
        raise CandidateLineageManifestError(
            f"unknown candidate_type: {data['candidate_type']!r}"
        ) from exc

    parent_ids_raw = data.get("parent_lineage_manifest_ids", [])
    if parent_ids_raw is None:
        parent_ids: list[str] = []
    elif not isinstance(parent_ids_raw, list):
        raise CandidateLineageManifestError("parent_lineage_manifest_ids must be an array")
    else:
        parent_ids = [str(item) for item in parent_ids_raw]

    manifest = CandidateLineageManifestV1(
        schema_version=str(data["schema_version"]),
        lineage_manifest_id=str(data["lineage_manifest_id"]),
        candidate_id=str(data["candidate_id"]),
        candidate_type=candidate_type,
        candidate_contract_ref=str(data["candidate_contract_ref"]),
        refs=[lineage_ref_from_mapping(item) for item in refs_raw if isinstance(item, Mapping)],
        created_at=_parse_datetime(data["created_at"], field_name="created_at"),
        created_by=str(data["created_by"]) if data.get("created_by") is not None else None,
        futures_scope_ref=dict(data["futures_scope_ref"]),
        trading_logic_immutability_ref=dict(data["trading_logic_immutability_ref"]),
        integrity=LineageIntegrity(content_sha256=digest),
        parent_lineage_manifest_ids=parent_ids,
        metadata=dict(data["metadata"]) if isinstance(data.get("metadata"), dict) else {},
    )
    if len(manifest.refs) != len(refs_raw):
        raise CandidateLineageManifestError("each ref must be an object")
    return manifest


def _is_fixture_mode(metadata: Mapping[str, Any]) -> bool:
    return metadata.get("fixture_kind") == "lineage_fixture"


def _validate_ref_cardinalities(refs: list[LineageRef]) -> tuple[bool, tuple[str, ...]]:
    counts: dict[LineageRefType, int] = {ref_type: 0 for ref_type in LineageRefType}
    for ref in refs:
        counts[ref.ref_type] += 1

    errors: list[str] = []
    for ref_type, (minimum, maximum) in _REF_TYPE_CARDINALITY.items():
        count = counts[ref_type]
        if count < minimum:
            errors.append(f"ref_type {ref_type.value} count {count} below minimum {minimum}")
        if maximum is not None and count > maximum:
            errors.append(f"ref_type {ref_type.value} count {count} exceeds maximum {maximum}")
    return (not errors, tuple(errors))


def validate_candidate_lineage_manifest_v1(
    data: Mapping[str, Any],
) -> tuple[bool, ValidationPhase, tuple[str, ...], str | None]:
    if not isinstance(data, Mapping):
        return False, ValidationPhase.SCHEMA, ("manifest payload must be a mapping",), None

    required_top_level = (
        "schema_version",
        "lineage_manifest_id",
        "candidate_id",
        "candidate_type",
        "candidate_contract_ref",
        "refs",
        "created_at",
        "futures_scope_ref",
        "trading_logic_immutability_ref",
        "integrity",
    )
    for key in required_top_level:
        if key not in data:
            return False, ValidationPhase.SCHEMA, (f"missing required field: {key}",), None

    if not isinstance(data["refs"], list):
        return False, ValidationPhase.SCHEMA, ("refs must be an array",), None
    if not isinstance(data["integrity"], Mapping):
        return False, ValidationPhase.SCHEMA, ("integrity must be an object",), None

    metadata = data.get("metadata") if isinstance(data.get("metadata"), Mapping) else {}

    schema_version_result = validate_schema_version(data["schema_version"])
    if not schema_version_result.valid:
        return (
            False,
            schema_version_result.phase,
            schema_version_result.errors,
            schema_version_result.verdict,
        )

    futures_result = validate_futures_scope_ref(data["futures_scope_ref"])
    if not futures_result.valid:
        return False, futures_result.phase, futures_result.errors, futures_result.verdict

    immutability_result = validate_trading_logic_immutability_ref(
        data["trading_logic_immutability_ref"]
    )
    if not immutability_result.valid:
        return (
            False,
            immutability_result.phase,
            immutability_result.errors,
            immutability_result.verdict,
        )

    if not data["refs"] and not _is_fixture_mode(metadata):
        return (
            False,
            ValidationPhase.LINEAGE_REFERENCES,
            ("refs may be empty only in fixture mode",),
            None,
        )

    seen_ref_keys: set[tuple[str, str, str]] = set()
    for ref in data["refs"]:
        if not isinstance(ref, Mapping):
            return False, ValidationPhase.SCHEMA, ("each ref must be an object",), None
        ref_type = ref.get("ref_type")
        ref_id = ref.get("ref_id")
        relation = ref.get("relation")
        if ref_type not in {item.value for item in LineageRefType}:
            return (
                False,
                ValidationPhase.LINEAGE_REFERENCES,
                (f"unknown ref_type: {ref_type!r}",),
                None,
            )
        if relation not in {item.value for item in LineageRelation}:
            return (
                False,
                ValidationPhase.LINEAGE_REFERENCES,
                (f"unknown relation: {relation!r}",),
                None,
            )
        if not isinstance(ref_id, str) or not ref_id.strip():
            return (
                False,
                ValidationPhase.LINEAGE_REFERENCES,
                ("ref_id must be a non-empty string",),
                None,
            )

        key = (str(ref_type), str(ref_id), str(relation))
        if key in seen_ref_keys:
            return (
                False,
                ValidationPhase.CARDINALITY,
                (f"duplicate ref entry: {ref_type}/{ref_id}/{relation}",),
                None,
            )
        seen_ref_keys.add(key)

        digest = ref.get("digest")
        if digest is not None and not is_valid_sha256_hex(str(digest)):
            return (
                False,
                ValidationPhase.INTEGRITY,
                ("ref digest must be 64-char lowercase sha256 hex",),
                None,
            )
        if ref_type == LineageRefType.EVIDENCE_OPS.value and ref.get("required") and not digest:
            return (
                False,
                ValidationPhase.LINEAGE_REFERENCES,
                ("evidence_ops ref requires digest when required=true",),
                None,
            )

    if not is_valid_uuid(str(data["lineage_manifest_id"])):
        return False, ValidationPhase.SCHEMA, ("lineage_manifest_id must be a UUID",), None
    if not is_valid_uuid(str(data["candidate_contract_ref"])):
        return (
            False,
            ValidationPhase.LINEAGE_REFERENCES,
            ("candidate_contract_ref must be a UUID",),
            None,
        )

    parent_ids = data.get("parent_lineage_manifest_ids", [])
    if parent_ids is not None:
        if not isinstance(parent_ids, list):
            return (
                False,
                ValidationPhase.LINEAGE_REFERENCES,
                ("parent_lineage_manifest_ids must be an array",),
                None,
            )
        for parent_id in parent_ids:
            if not is_valid_uuid(str(parent_id)):
                return (
                    False,
                    ValidationPhase.LINEAGE_REFERENCES,
                    ("parent_lineage_manifest_ids entries must be UUIDs",),
                    None,
                )

    try:
        manifest = deserialize_candidate_lineage_manifest_v1(data)
    except CandidateLineageManifestError as exc:
        return False, ValidationPhase.SCHEMA, (str(exc),), None

    cardinality_ok, cardinality_errors = _validate_ref_cardinalities(manifest.refs)
    if not cardinality_ok:
        return False, ValidationPhase.CARDINALITY, cardinality_errors, None

    expected_digest = compute_lineage_manifest_integrity(manifest).content_sha256
    integrity_result = validate_integrity_block(data["integrity"], expected_digest=expected_digest)
    if not integrity_result.valid:
        return False, integrity_result.phase, integrity_result.errors, integrity_result.verdict

    return True, ValidationPhase.RESULT, (), None
