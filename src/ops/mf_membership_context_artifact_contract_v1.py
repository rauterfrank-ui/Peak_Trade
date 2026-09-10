"""MF Membership-Context Artifact V1 — isolated schema, writer, and reader.

Binds the non-authoritative membership-context artifact contract. Does not
rank, select, apply anti-churn, compute execution intent, unlock G13, join a
host, or authorize runtime. Rotation deltas are derived, never stored.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

REPO_ROOT = Path(__file__).resolve().parents[2]

ARTIFACT_TYPE = "MF_MEMBERSHIP_CONTEXT_V1"
ARTIFACT_SCHEMA_VERSION = "mf_membership_context.v1"
OWNER = "ops.mf_membership_context_artifact_contract_v1"
SINGLE_WRITER_IDENTITY = "mf_membership_context_artifact_writer_v1"

N_VALUE = 5
CARDINALITY_MODE = "AT_MOST_N"
LIFECYCLE_DURABLE_VALID = "DURABLE_VALID"
INSTANCE_ID_PREFIX = "mca_"
INSTANCE_ID_RE = re.compile(r"^mca_[0-9a-f]{16}$")

CANONICAL_STORE_RELATIVE_ROOT = "docs/ops/mf/membership_context/canonical"
MANIFEST_FILENAME = "MANIFEST.sha256"
CANONICAL_CAP22_SNAPSHOT_RELATIVE_PATH = (
    "docs/evidence/capability_2_2_productive_futures_ranking_producer_v1"
    "/productive_ranking/productive_futures_ranking_snapshot_v1.json"
)
CAP22_SCHEMA_VERSION = "productive_futures_ranking_snapshot.v1"
CAP22_TOP20_LIMIT = 20
ELIGIBILITY_ELIGIBLE = "ELIGIBLE"
SNAPSHOT_STATE_VALID = "VALID"

POLICY_IDENTITY_V1: dict[str, Any] = {
    "anti_churn_policy": "POLICY_A",
    "bootstrap_rule": "PREFIX_FILL_FROM_CAP22_ELIGIBLE_NO_ANTI_CHURN_NO_PADDING",
    "cardinality_mode": CARDINALITY_MODE,
    "exactly_5": False,
    "membership_order_policy": "CONSUME_CAP22_ORDERING_AS_MEMBERSHIP_ORDER",
    "mf_semantics_contract_id": "MF_SELECTION_AND_ANTI_CHURN_SEMANTICS_CONTRACT_V1",
    "n_value": N_VALUE,
    "no_padding": True,
    "od07": "DERIVED",
}

SELECTOR_RUNTIME_IMPLEMENTED = False
ROTATION_RUNTIME_IMPLEMENTED = False
RUNTIME_AUTHORIZED = False
G13_UNLOCK = False
EXECUTION_AUTHORITY_EFFECT = "NONE"

REQUIRED_ARTIFACT_KEYS: frozenset[str] = frozenset(
    {
        "artifact_type",
        "bootstrap",
        "cap22_provenance",
        "instance_id",
        "integrity_digest",
        "lifecycle_state",
        "ordered_instrument_ids",
        "policy_identity",
        "prior_membership_reference",
        "schema_version",
        "temporal_identity",
    }
)
FORBIDDEN_ARTIFACT_KEYS: frozenset[str] = frozenset(
    {
        "entered",
        "exited",
        "retained",
        "rotation_deltas",
        "rotation_delta",
    }
)


class MembershipContextArtifactError(ValueError):
    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(f"{code}:{detail}" if detail else code)
        self.failure_code = code
        self.detail = detail


def canonical_json_dumps(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_hex(payload: str | bytes) -> str:
    if isinstance(payload, str):
        payload = payload.encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def canonical_store_root(*, repo_root: Path | None = None) -> Path:
    root = repo_root if repo_root is not None else REPO_ROOT
    return root / CANONICAL_STORE_RELATIVE_ROOT


def canonical_cap22_snapshot_path(*, repo_root: Path | None = None) -> Path:
    root = repo_root if repo_root is not None else REPO_ROOT
    return root / CANONICAL_CAP22_SNAPSHOT_RELATIVE_PATH


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, path)
        tmp_name = None
        try:
            dir_fd = os.open(str(path.parent), os.O_RDONLY)
            try:
                os.fsync(dir_fd)
            finally:
                os.close(dir_fd)
        except OSError:
            pass
    finally:
        if tmp_name is not None and os.path.exists(tmp_name):
            os.unlink(tmp_name)


def artifact_filename(instance_id: str) -> str:
    return f"{instance_id}.json"


@dataclass(frozen=True)
class Cap22ProvenanceV1:
    ranking_snapshot_id: str
    ranking_schema_version: str
    ranking_integrity_digest: str
    ranking_event_time: str
    universe_snapshot_id: str
    ranking_policy_id: str
    ranking_policy_version: str
    source_relative_path: str
    source_file_sha256: str
    snapshot_state: str
    top20_candidate_context_limit: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "ranking_event_time": self.ranking_event_time,
            "ranking_integrity_digest": self.ranking_integrity_digest,
            "ranking_policy_id": self.ranking_policy_id,
            "ranking_policy_version": self.ranking_policy_version,
            "ranking_schema_version": self.ranking_schema_version,
            "ranking_snapshot_id": self.ranking_snapshot_id,
            "snapshot_state": self.snapshot_state,
            "source_file_sha256": self.source_file_sha256,
            "source_relative_path": self.source_relative_path,
            "top20_candidate_context_limit": int(self.top20_candidate_context_limit),
            "universe_snapshot_id": self.universe_snapshot_id,
        }

    @staticmethod
    def from_dict(payload: Mapping[str, Any]) -> "Cap22ProvenanceV1":
        required = (
            "ranking_event_time",
            "ranking_integrity_digest",
            "ranking_policy_id",
            "ranking_policy_version",
            "ranking_schema_version",
            "ranking_snapshot_id",
            "snapshot_state",
            "source_file_sha256",
            "source_relative_path",
            "top20_candidate_context_limit",
            "universe_snapshot_id",
        )
        missing = [key for key in required if not str(payload.get(key) or "").strip()]
        if missing:
            raise MembershipContextArtifactError("INVALID_PROVENANCE", ",".join(missing))
        return Cap22ProvenanceV1(
            ranking_snapshot_id=str(payload["ranking_snapshot_id"]),
            ranking_schema_version=str(payload["ranking_schema_version"]),
            ranking_integrity_digest=str(payload["ranking_integrity_digest"]),
            ranking_event_time=str(payload["ranking_event_time"]),
            universe_snapshot_id=str(payload["universe_snapshot_id"]),
            ranking_policy_id=str(payload["ranking_policy_id"]),
            ranking_policy_version=str(payload["ranking_policy_version"]),
            source_relative_path=str(payload["source_relative_path"]),
            source_file_sha256=str(payload["source_file_sha256"]),
            snapshot_state=str(payload["snapshot_state"]),
            top20_candidate_context_limit=int(payload["top20_candidate_context_limit"]),
        )


@dataclass(frozen=True)
class TemporalIdentityV1:
    cap22_ranking_snapshot_id: str
    cap22_event_time: str
    cap22_integrity_digest: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "cap22_event_time": self.cap22_event_time,
            "cap22_integrity_digest": self.cap22_integrity_digest,
            "cap22_ranking_snapshot_id": self.cap22_ranking_snapshot_id,
        }

    @staticmethod
    def from_dict(payload: Mapping[str, Any]) -> "TemporalIdentityV1":
        snapshot_id = str(payload.get("cap22_ranking_snapshot_id") or "").strip()
        event_time = str(payload.get("cap22_event_time") or "").strip()
        digest = str(payload.get("cap22_integrity_digest") or "").strip()
        if not snapshot_id or not event_time or not digest:
            raise MembershipContextArtifactError("MALFORMED_IDENTITY", "temporal_identity")
        return TemporalIdentityV1(
            cap22_ranking_snapshot_id=snapshot_id,
            cap22_event_time=event_time,
            cap22_integrity_digest=digest,
        )


@dataclass(frozen=True)
class MembershipContextArtifactV1:
    artifact_type: str
    schema_version: str
    instance_id: str
    temporal_identity: TemporalIdentityV1
    ordered_instrument_ids: tuple[str, ...]
    prior_membership_reference: Optional[str]
    cap22_provenance: Cap22ProvenanceV1
    policy_identity: Mapping[str, Any]
    bootstrap: bool
    lifecycle_state: str
    integrity_digest: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact_type": self.artifact_type,
            "bootstrap": bool(self.bootstrap),
            "cap22_provenance": self.cap22_provenance.to_dict(),
            "instance_id": self.instance_id,
            "integrity_digest": self.integrity_digest,
            "lifecycle_state": self.lifecycle_state,
            "ordered_instrument_ids": list(self.ordered_instrument_ids),
            "policy_identity": dict(sorted(dict(self.policy_identity).items())),
            "prior_membership_reference": self.prior_membership_reference,
            "schema_version": self.schema_version,
            "temporal_identity": self.temporal_identity.to_dict(),
        }

    def payload_for_instance_id(self) -> dict[str, Any]:
        payload = self.to_dict()
        payload.pop("instance_id", None)
        payload.pop("integrity_digest", None)
        return payload

    def payload_for_integrity(self) -> dict[str, Any]:
        payload = self.to_dict()
        payload.pop("integrity_digest", None)
        return payload

    def compute_instance_id(self) -> str:
        return (
            INSTANCE_ID_PREFIX
            + sha256_hex(canonical_json_dumps(self.payload_for_instance_id()))[:16]
        )

    def compute_integrity_digest(self) -> str:
        return sha256_hex(canonical_json_dumps(self.payload_for_integrity()))


def _validate_ordered_instrument_ids(ids: Sequence[str]) -> tuple[str, ...]:
    if not isinstance(ids, (list, tuple)):
        raise MembershipContextArtifactError("INVALID_CARDINALITY", "ordered_instrument_ids")
    out: list[str] = []
    seen: set[str] = set()
    for raw in ids:
        value = str(raw).strip()
        if not value:
            raise MembershipContextArtifactError("MALFORMED_IDENTITY", "empty_instrument_id")
        if value in seen:
            raise MembershipContextArtifactError("DUPLICATE_INSTRUMENT_ID", value)
        seen.add(value)
        out.append(value)
    if len(out) > N_VALUE:
        raise MembershipContextArtifactError("CARDINALITY_EXCEEDS_N", str(len(out)))
    return tuple(out)


def _validate_policy_identity(payload: Mapping[str, Any]) -> dict[str, Any]:
    actual = {str(k): payload[k] for k in payload}
    expected = dict(POLICY_IDENTITY_V1)
    if actual != expected:
        raise MembershipContextArtifactError(
            "INVALID_POLICY_IDENTITY", canonical_json_dumps(actual)
        )
    return expected


def validate_membership_context_artifact_v1(
    artifact: MembershipContextArtifactV1,
) -> MembershipContextArtifactV1:
    if artifact.artifact_type != ARTIFACT_TYPE:
        raise MembershipContextArtifactError("INVALID_ARTIFACT_TYPE", artifact.artifact_type)
    if artifact.schema_version != ARTIFACT_SCHEMA_VERSION:
        raise MembershipContextArtifactError("INVALID_SCHEMA_VERSION", artifact.schema_version)
    if artifact.lifecycle_state != LIFECYCLE_DURABLE_VALID:
        raise MembershipContextArtifactError("INVALID_LIFECYCLE", artifact.lifecycle_state)
    _validate_ordered_instrument_ids(artifact.ordered_instrument_ids)
    _validate_policy_identity(artifact.policy_identity)
    provenance = artifact.cap22_provenance
    if provenance.ranking_schema_version != CAP22_SCHEMA_VERSION:
        raise MembershipContextArtifactError(
            "INVALID_PROVENANCE", provenance.ranking_schema_version
        )
    if provenance.snapshot_state != SNAPSHOT_STATE_VALID:
        raise MembershipContextArtifactError("INVALID_PROVENANCE", provenance.snapshot_state)
    if provenance.top20_candidate_context_limit != CAP22_TOP20_LIMIT:
        raise MembershipContextArtifactError(
            "INVALID_PROVENANCE", str(provenance.top20_candidate_context_limit)
        )
    if (
        artifact.temporal_identity.cap22_ranking_snapshot_id != provenance.ranking_snapshot_id
        or artifact.temporal_identity.cap22_event_time != provenance.ranking_event_time
        or artifact.temporal_identity.cap22_integrity_digest != provenance.ranking_integrity_digest
    ):
        raise MembershipContextArtifactError("MALFORMED_IDENTITY", "temporal_provenance_mismatch")
    prior = artifact.prior_membership_reference
    if artifact.bootstrap:
        if prior is not None:
            raise MembershipContextArtifactError(
                "INVALID_PRIOR_REFERENCE", "bootstrap_must_be_null"
            )
    else:
        if prior is None or not INSTANCE_ID_RE.fullmatch(str(prior)):
            raise MembershipContextArtifactError("MISSING_PRIOR_REFERENCE", str(prior))
    expected_id = artifact.compute_instance_id()
    if not INSTANCE_ID_RE.fullmatch(artifact.instance_id):
        raise MembershipContextArtifactError("MALFORMED_IDENTITY", artifact.instance_id)
    if artifact.instance_id != expected_id:
        raise MembershipContextArtifactError("MALFORMED_IDENTITY", "instance_id_mismatch")
    expected_digest = artifact.compute_integrity_digest()
    if artifact.integrity_digest != expected_digest:
        raise MembershipContextArtifactError("INTEGRITY_FAILURE", artifact.integrity_digest)
    return artifact


def membership_context_artifact_from_dict(
    payload: Mapping[str, Any],
) -> MembershipContextArtifactV1:
    if not isinstance(payload, Mapping):
        raise MembershipContextArtifactError("INVALID_SCHEMA", "not_object")
    extra_forbidden = FORBIDDEN_ARTIFACT_KEYS.intersection(payload.keys())
    if extra_forbidden:
        raise MembershipContextArtifactError(
            "ROTATION_DELTAS_CANONICAL_FORBIDDEN", ",".join(sorted(extra_forbidden))
        )
    missing = [key for key in sorted(REQUIRED_ARTIFACT_KEYS) if key not in payload]
    if missing:
        raise MembershipContextArtifactError("INVALID_SCHEMA", ",".join(missing))
    prior_raw = payload.get("prior_membership_reference")
    if prior_raw is None:
        prior: Optional[str] = None
    else:
        prior = str(prior_raw)
    ordered = _validate_ordered_instrument_ids(payload.get("ordered_instrument_ids") or [])
    artifact = MembershipContextArtifactV1(
        artifact_type=str(payload.get("artifact_type") or ""),
        schema_version=str(payload.get("schema_version") or ""),
        instance_id=str(payload.get("instance_id") or ""),
        temporal_identity=TemporalIdentityV1.from_dict(payload.get("temporal_identity") or {}),
        ordered_instrument_ids=ordered,
        prior_membership_reference=prior,
        cap22_provenance=Cap22ProvenanceV1.from_dict(payload.get("cap22_provenance") or {}),
        policy_identity=dict(payload.get("policy_identity") or {}),
        bootstrap=bool(payload.get("bootstrap")),
        lifecycle_state=str(payload.get("lifecycle_state") or ""),
        integrity_digest=str(payload.get("integrity_digest") or ""),
    )
    return validate_membership_context_artifact_v1(artifact)


def build_membership_context_artifact_v1(
    *,
    ordered_instrument_ids: Sequence[str],
    cap22_provenance: Cap22ProvenanceV1,
    bootstrap: bool,
    prior_membership_reference: Optional[str],
) -> MembershipContextArtifactV1:
    ordered = _validate_ordered_instrument_ids(ordered_instrument_ids)
    temporal = TemporalIdentityV1(
        cap22_ranking_snapshot_id=cap22_provenance.ranking_snapshot_id,
        cap22_event_time=cap22_provenance.ranking_event_time,
        cap22_integrity_digest=cap22_provenance.ranking_integrity_digest,
    )
    draft = MembershipContextArtifactV1(
        artifact_type=ARTIFACT_TYPE,
        schema_version=ARTIFACT_SCHEMA_VERSION,
        instance_id=INSTANCE_ID_PREFIX + ("0" * 16),
        temporal_identity=temporal,
        ordered_instrument_ids=ordered,
        prior_membership_reference=prior_membership_reference,
        cap22_provenance=cap22_provenance,
        policy_identity=dict(POLICY_IDENTITY_V1),
        bootstrap=bootstrap,
        lifecycle_state=LIFECYCLE_DURABLE_VALID,
        integrity_digest="",
    )
    instance_id = draft.compute_instance_id()
    with_id = MembershipContextArtifactV1(
        artifact_type=draft.artifact_type,
        schema_version=draft.schema_version,
        instance_id=instance_id,
        temporal_identity=draft.temporal_identity,
        ordered_instrument_ids=draft.ordered_instrument_ids,
        prior_membership_reference=draft.prior_membership_reference,
        cap22_provenance=draft.cap22_provenance,
        policy_identity=draft.policy_identity,
        bootstrap=draft.bootstrap,
        lifecycle_state=draft.lifecycle_state,
        integrity_digest="",
    )
    return validate_membership_context_artifact_v1(
        MembershipContextArtifactV1(
            artifact_type=with_id.artifact_type,
            schema_version=with_id.schema_version,
            instance_id=with_id.instance_id,
            temporal_identity=with_id.temporal_identity,
            ordered_instrument_ids=with_id.ordered_instrument_ids,
            prior_membership_reference=with_id.prior_membership_reference,
            cap22_provenance=with_id.cap22_provenance,
            policy_identity=with_id.policy_identity,
            bootstrap=with_id.bootstrap,
            lifecycle_state=with_id.lifecycle_state,
            integrity_digest=with_id.compute_integrity_digest(),
        )
    )


def derive_rotation_delta_v1(
    current: MembershipContextArtifactV1,
    prior: Optional[MembershipContextArtifactV1],
) -> dict[str, list[str]]:
    """Derived view only. Never canonical stored state."""
    current_ids = list(current.ordered_instrument_ids)
    if prior is None:
        if not current.bootstrap:
            raise MembershipContextArtifactError("PRIOR_UNAVAILABLE", current.instance_id)
        return {"entered": current_ids, "exited": [], "retained": []}
    prior_set = set(prior.ordered_instrument_ids)
    current_set = set(current_ids)
    entered = [item for item in current_ids if item not in prior_set]
    retained = [item for item in current_ids if item in prior_set]
    exited = [item for item in prior.ordered_instrument_ids if item not in current_set]
    return {"entered": entered, "exited": exited, "retained": retained}


def _manifest_body(store_root: Path, relative_files: Sequence[str]) -> str:
    lines: list[str] = []
    for rel in sorted(relative_files):
        digest = sha256_hex((store_root / rel).read_bytes())
        lines.append(f"{digest}  {rel}")
    return "\n".join(lines) + "\n"


def _read_manifest_files(store_root: Path) -> list[str]:
    manifest = store_root / MANIFEST_FILENAME
    if not manifest.is_file():
        raise MembershipContextArtifactError("PARTIAL_WRITE", "MANIFEST_MISSING")
    names: list[str] = []
    for line in manifest.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        digest, rel = stripped.split(None, 1)
        path = store_root / rel
        if not path.is_file():
            raise MembershipContextArtifactError("PARTIAL_WRITE", f"MISSING:{rel}")
        actual = sha256_hex(path.read_bytes())
        if actual != digest:
            raise MembershipContextArtifactError("INTEGRITY_FAILURE", f"DIGEST_MISMATCH:{rel}")
        names.append(rel)
    return names


def write_membership_context_artifact_v1(
    artifact: MembershipContextArtifactV1,
    *,
    store_root: Path,
) -> MembershipContextArtifactV1:
    """Persist an already-decided membership context. Does not rank or select."""
    decided = validate_membership_context_artifact_v1(artifact)
    store_root.mkdir(parents=True, exist_ok=True)
    filename = artifact_filename(decided.instance_id)
    path = store_root / filename
    body = canonical_json_dumps(decided.to_dict()) + "\n"
    _atomic_write_text(path, body)
    existing: list[str] = []
    manifest_path = store_root / MANIFEST_FILENAME
    if manifest_path.is_file():
        existing = _read_manifest_files(store_root)
    files = sorted(set(existing + [filename]))
    _atomic_write_text(store_root / MANIFEST_FILENAME, _manifest_body(store_root, files))
    return decided


def read_membership_context_artifact_v1(
    instance_id: str,
    *,
    store_root: Path,
) -> MembershipContextArtifactV1:
    if not INSTANCE_ID_RE.fullmatch(instance_id):
        raise MembershipContextArtifactError("MALFORMED_IDENTITY", instance_id)
    filename = artifact_filename(instance_id)
    path = store_root / filename
    if not path.is_file():
        raise MembershipContextArtifactError("ARTIFACT_MISSING", instance_id)
    listed = _read_manifest_files(store_root)
    if filename not in listed:
        raise MembershipContextArtifactError("PARTIAL_WRITE", filename)
    raw = path.read_text(encoding="utf-8")
    if not raw.strip():
        raise MembershipContextArtifactError("PLACEHOLDER_OR_EMPTY", instance_id)
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise MembershipContextArtifactError("INVALID_SCHEMA", "json") from exc
    artifact = membership_context_artifact_from_dict(payload)
    if artifact.instance_id != instance_id:
        raise MembershipContextArtifactError("MALFORMED_IDENTITY", artifact.instance_id)
    return artifact


def eligible_prefix_from_cap22_snapshot(
    snapshot: Mapping[str, Any],
    *,
    n_value: int = N_VALUE,
) -> tuple[str, ...]:
    if str(snapshot.get("snapshot_state") or "") != SNAPSHOT_STATE_VALID:
        raise MembershipContextArtifactError("INVALID_PROVENANCE", "snapshot_state")
    ranked = list(snapshot.get("ranked_candidates") or [])
    ranked.sort(key=lambda row: int(row.get("rank") or 0))
    top20 = ranked[:CAP22_TOP20_LIMIT]
    eligible: list[str] = []
    for row in top20:
        if str(row.get("eligibility_status") or "") != ELIGIBILITY_ELIGIBLE:
            continue
        instrument_id = str(row.get("canonical_instrument_id") or "").strip()
        if not instrument_id:
            raise MembershipContextArtifactError("INVALID_PROVENANCE", "missing_instrument_id")
        eligible.append(instrument_id)
    return tuple(eligible[:n_value])


def cap22_provenance_from_snapshot_file(
    snapshot_path: Path,
    *,
    source_relative_path: str,
) -> tuple[Cap22ProvenanceV1, dict[str, Any]]:
    if not snapshot_path.is_file():
        raise MembershipContextArtifactError("INVALID_PROVENANCE", "source_missing")
    raw = snapshot_path.read_bytes()
    if not raw.strip():
        raise MembershipContextArtifactError("INVALID_PROVENANCE", "source_empty")
    try:
        snapshot = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise MembershipContextArtifactError("INVALID_PROVENANCE", "source_json") from exc
    if not isinstance(snapshot, dict):
        raise MembershipContextArtifactError("INVALID_PROVENANCE", "source_not_object")
    provenance = Cap22ProvenanceV1(
        ranking_snapshot_id=str(snapshot.get("ranking_snapshot_id") or ""),
        ranking_schema_version=str(snapshot.get("schema_version") or ""),
        ranking_integrity_digest=str(snapshot.get("integrity_digest") or ""),
        ranking_event_time=str(snapshot.get("event_time") or ""),
        universe_snapshot_id=str(snapshot.get("universe_snapshot_id") or ""),
        ranking_policy_id=str(snapshot.get("ranking_policy_id") or ""),
        ranking_policy_version=str(snapshot.get("ranking_policy_version") or ""),
        source_relative_path=source_relative_path,
        source_file_sha256=sha256_hex(raw),
        snapshot_state=str(snapshot.get("snapshot_state") or ""),
        top20_candidate_context_limit=int(
            snapshot.get("top20_candidate_context_limit") or CAP22_TOP20_LIMIT
        ),
    )
    if not provenance.ranking_snapshot_id or not provenance.ranking_integrity_digest:
        raise MembershipContextArtifactError("INVALID_PROVENANCE", "identity_fields")
    return provenance, snapshot


def build_bootstrap_membership_from_cap22_snapshot_v1(
    *,
    snapshot_path: Path,
    source_relative_path: str,
) -> MembershipContextArtifactV1:
    provenance, snapshot = cap22_provenance_from_snapshot_file(
        snapshot_path, source_relative_path=source_relative_path
    )
    ordered = eligible_prefix_from_cap22_snapshot(snapshot)
    if not ordered:
        raise MembershipContextArtifactError("EMPTY_SET_NOT_AUTHORIZED", "bootstrap")
    return build_membership_context_artifact_v1(
        ordered_instrument_ids=ordered,
        cap22_provenance=provenance,
        bootstrap=True,
        prior_membership_reference=None,
    )


def materialize_canonical_bootstrap_instance_v1(
    *,
    repo_root: Path | None = None,
) -> MembershipContextArtifactV1:
    root = repo_root if repo_root is not None else REPO_ROOT
    snapshot_path = canonical_cap22_snapshot_path(repo_root=root)
    artifact = build_bootstrap_membership_from_cap22_snapshot_v1(
        snapshot_path=snapshot_path,
        source_relative_path=CANONICAL_CAP22_SNAPSHOT_RELATIVE_PATH,
    )
    store = canonical_store_root(repo_root=root)
    written = write_membership_context_artifact_v1(artifact, store_root=store)
    readback = read_membership_context_artifact_v1(written.instance_id, store_root=store)
    if readback.to_dict() != written.to_dict():
        raise MembershipContextArtifactError("READBACK_MISMATCH", written.instance_id)
    return readback
