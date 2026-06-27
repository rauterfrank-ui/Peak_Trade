"""CandidateLineageManifest v1 — offline reference-only cross-domain FK graph."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
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


class CandidateLineageManifestValidationError(CandidateLineageManifestError):
    """Raised when Package-F lineage manifest production validation fails fail-closed."""

    def __init__(
        self,
        message: str,
        *,
        phase: ValidationPhase,
        errors: tuple[str, ...],
        verdict: str | None = None,
    ) -> None:
        super().__init__(message)
        self.phase = phase
        self.errors = errors
        self.verdict = verdict


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
    DERIVES_FROM_RESULT_MANIFEST = "derives_from_result_manifest"


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


_ALLOWED_PRODUCER_INPUT_KEYS: frozenset[str] = frozenset(
    {
        "lineage_manifest_id",
        "candidate_id",
        "candidate_type",
        "candidate_contract_ref",
        "refs",
        "created_at",
        "created_by",
        "parent_lineage_manifest_ids",
        "metadata",
        "futures_scope_ref",
        "trading_logic_immutability_ref",
    }
)

_FORBIDDEN_PRODUCER_EMBED_KEYS: frozenset[str] = frozenset(
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
        "config_patch_manifest",
        "proposal",
        "proposals",
        "old_value",
        "new_value",
        "target",
    }
)


def _reject_forbidden_embed_keys(raw: Mapping[str, Any], *, context: str) -> None:
    for key in raw:
        if key in _FORBIDDEN_PRODUCER_EMBED_KEYS:
            raise CandidateLineageManifestError(
                f"{context} must not embed forbidden payload key: {key}"
            )


def _canonical_sort_refs(refs: list[LineageRef]) -> list[LineageRef]:
    return sorted(
        refs,
        key=lambda ref: (
            ref.ref_type.value,
            ref.ref_id,
            ref.relation.value,
            ref.owner_domain,
        ),
    )


def load_lineage_producer_input_from_path(path: Path | str) -> Mapping[str, Any]:
    """Load explicit offline lineage producer input from a JSON file."""
    input_path = Path(path)
    if not input_path.is_file():
        raise CandidateLineageManifestError(f"input file not found: {input_path}")

    try:
        text = input_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise CandidateLineageManifestError(f"failed to read input file: {input_path}") from exc

    if input_path.suffix.lower() != ".json":
        raise CandidateLineageManifestError(
            f"unsupported input format {input_path.suffix!r}; expected .json"
        )

    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise CandidateLineageManifestError(f"invalid JSON in {input_path}: {exc.msg}") from exc

    if not isinstance(payload, dict):
        raise CandidateLineageManifestError("JSON root must be an object")

    unknown = set(payload) - _ALLOWED_PRODUCER_INPUT_KEYS
    if unknown:
        unknown_sorted = ", ".join(sorted(unknown))
        raise CandidateLineageManifestError(f"unknown producer input fields: {unknown_sorted}")

    _reject_forbidden_embed_keys(payload, context="producer input")
    return payload


def _parse_producer_refs(raw_refs: Any) -> list[LineageRef]:
    if not isinstance(raw_refs, list):
        raise CandidateLineageManifestError("refs must be an array")

    refs: list[LineageRef] = []
    for index, item in enumerate(raw_refs):
        if not isinstance(item, Mapping):
            raise CandidateLineageManifestError(f"refs[{index}] must be an object")
        _reject_forbidden_embed_keys(item, context=f"refs[{index}]")
        refs.append(lineage_ref_from_mapping(item))
    return _canonical_sort_refs(refs)


def build_candidate_lineage_manifest_v1_from_producer_input(
    raw: Mapping[str, Any],
    *,
    created_at: datetime | None = None,
    created_by: str | None = "package_f_candidate_lineage_manifest_producer_v1",
) -> CandidateLineageManifestV1:
    """Build a validated CandidateLineageManifestV1 from explicit reference-only input."""
    if not isinstance(raw, Mapping):
        raise CandidateLineageManifestError("producer input must be a mapping")

    unknown = set(raw) - _ALLOWED_PRODUCER_INPUT_KEYS
    if unknown:
        unknown_sorted = ", ".join(sorted(unknown))
        raise CandidateLineageManifestError(f"unknown producer input fields: {unknown_sorted}")

    _reject_forbidden_embed_keys(raw, context="producer input")

    required_fields = (
        "lineage_manifest_id",
        "candidate_id",
        "candidate_type",
        "candidate_contract_ref",
        "refs",
    )
    for key in required_fields:
        if key not in raw:
            raise CandidateLineageManifestError(f"missing required producer input field: {key}")

    lineage_manifest_id = str(raw["lineage_manifest_id"])
    if not is_valid_uuid(lineage_manifest_id):
        raise CandidateLineageManifestError("lineage_manifest_id must be a UUID")

    candidate_contract_ref = str(raw["candidate_contract_ref"])
    if not is_valid_uuid(candidate_contract_ref):
        raise CandidateLineageManifestError("candidate_contract_ref must be a UUID")

    try:
        candidate_type = CandidateType(str(raw["candidate_type"]))
    except ValueError as exc:
        raise CandidateLineageManifestError(
            f"unknown candidate_type: {raw['candidate_type']!r}"
        ) from exc

    refs = _parse_producer_refs(raw["refs"])

    parent_ids_raw = raw.get("parent_lineage_manifest_ids", [])
    if parent_ids_raw is None:
        parent_ids: list[str] = []
    elif not isinstance(parent_ids_raw, list):
        raise CandidateLineageManifestError("parent_lineage_manifest_ids must be an array")
    else:
        parent_ids = sorted(str(item) for item in parent_ids_raw)
        for parent_id in parent_ids:
            if not is_valid_uuid(parent_id):
                raise CandidateLineageManifestError(
                    "parent_lineage_manifest_ids entries must be UUIDs"
                )

    metadata_raw = raw.get("metadata", {})
    if metadata_raw is None:
        metadata: dict[str, Any] = {}
    elif not isinstance(metadata_raw, dict):
        raise CandidateLineageManifestError("metadata must be an object")
    else:
        metadata = dict(metadata_raw)
        _reject_forbidden_embed_keys(metadata, context="metadata")

    when = created_at
    if when is None:
        if "created_at" in raw:
            when = _parse_datetime(raw["created_at"], field_name="created_at")
        else:
            when = datetime.now(timezone.utc)

    futures_scope = (
        dict(raw["futures_scope_ref"])
        if "futures_scope_ref" in raw
        else canonical_futures_scope_ref()
    )
    immutability_ref = (
        dict(raw["trading_logic_immutability_ref"])
        if "trading_logic_immutability_ref" in raw
        else canonical_trading_logic_immutability_ref()
    )

    manifest = CandidateLineageManifestV1(
        schema_version=SCHEMA_VERSION_V1,
        lineage_manifest_id=lineage_manifest_id,
        candidate_id=str(raw["candidate_id"]),
        candidate_type=candidate_type,
        candidate_contract_ref=candidate_contract_ref,
        refs=refs,
        created_at=when,
        created_by=str(raw["created_by"]) if raw.get("created_by") is not None else created_by,
        parent_lineage_manifest_ids=parent_ids,
        futures_scope_ref=futures_scope,
        trading_logic_immutability_ref=immutability_ref,
        metadata=metadata,
    )
    manifest.integrity = compute_lineage_manifest_integrity(manifest)

    serialized = serialize_candidate_lineage_manifest_v1(manifest)
    payload = json.loads(serialized)
    valid, phase, errors, verdict = validate_candidate_lineage_manifest_v1(payload)
    if not valid:
        raise CandidateLineageManifestValidationError(
            "CandidateLineageManifest v1 validation failed during production",
            phase=phase,
            errors=errors,
            verdict=verdict,
        )

    return deserialize_candidate_lineage_manifest_v1(payload)


def _atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    try:
        tmp.write_text(content, encoding="utf-8")
    except OSError:
        if tmp.exists():
            tmp.unlink(missing_ok=True)
        raise
    try:
        tmp.replace(path)
    except OSError:
        if tmp.exists():
            tmp.unlink(missing_ok=True)
        raise


def write_candidate_lineage_manifest_v1_atomic(
    manifest: CandidateLineageManifestV1,
    output_path: Path | str,
) -> Path:
    """Validate, serialize, and atomically write a CandidateLineageManifest v1 JSON file."""
    out = Path(output_path)
    serialized = serialize_candidate_lineage_manifest_v1(manifest)
    payload = json.loads(serialized)
    valid, phase, errors, verdict = validate_candidate_lineage_manifest_v1(payload)
    if not valid:
        raise CandidateLineageManifestValidationError(
            f"refusing to write invalid manifest to {out}",
            phase=phase,
            errors=errors,
            verdict=verdict,
        )

    _atomic_write_text(out, serialized)
    return out


def produce_candidate_lineage_manifest_v1_from_paths(
    *,
    input_path: Path | str,
    output_path: Path | str,
    created_at: datetime | None = None,
    created_by: str | None = "package_f_candidate_lineage_manifest_producer_v1",
) -> CandidateLineageManifestV1:
    """End-to-end offline producer: explicit JSON input -> validated manifest file."""
    raw = load_lineage_producer_input_from_path(input_path)
    manifest = build_candidate_lineage_manifest_v1_from_producer_input(
        raw,
        created_at=created_at,
        created_by=created_by,
    )
    write_candidate_lineage_manifest_v1_atomic(manifest, output_path)
    return manifest
