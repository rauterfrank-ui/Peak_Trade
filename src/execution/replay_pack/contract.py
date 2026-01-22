from __future__ import annotations

"""
Deterministic Replay Pack (Bundle Contract) — v1

Scope:
- Deterministic export of a run into a self-contained replay bundle
- Minimal validation + hash verification
- Replay runner can re-consume the bundle deterministically

Notes:
- This contract is intentionally lightweight (no external schema deps).
- Determinism is enforced via stable ordering + canonical JSON serialization.
"""

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Literal, Mapping, Optional, Sequence, Tuple


CONTRACT_VERSION: Literal["1"] = "1"


# -----------------------------------------------------------------------------
# Bundle layout (v1)
# -----------------------------------------------------------------------------

BUNDLE_ROOT_DIRNAME = "replay_pack"

REQUIRED_FILES: Tuple[str, ...] = (
    "manifest.json",
    "events/execution_events.jsonl",
    "hashes/sha256sums.txt",
)

OPTIONAL_FILES: Tuple[str, ...] = (
    "inputs/config_snapshot.json",
    "inputs/config_snapshot.toml",
    "inputs/strategy_params.json",
    "events/market_data_refs.json",
    "outputs/expected_fills.jsonl",
    "outputs/expected_positions.json",
    "meta/env.json",
    "meta/git.json",
)


# -----------------------------------------------------------------------------
# Canonicalization and hashing rules (v1)
# -----------------------------------------------------------------------------

CANON_JSON_RULE: Literal["sort_keys_utf8_no_ws"] = "sort_keys_utf8_no_ws"
CANON_JSONL_RULE: Literal["one_object_per_line_sorted_keys_lf"] = (
    "one_object_per_line_sorted_keys_lf"
)

SHA256SUMS_FORMAT: Literal["sha256  path"] = "sha256  path"

# Manifest invariants string is frozen to keep tooling stable.
EVENT_ORDERING_INVARIANT: Literal["event_time_utc_then_seq"] = "event_time_utc_then_seq"


# -----------------------------------------------------------------------------
# Error taxonomy (public)
# -----------------------------------------------------------------------------


class ReplayPackError(Exception):
    """Base error for replay pack operations."""


class ContractViolationError(ReplayPackError):
    """Bundle violates the bundle contract (missing files, bad fields, etc.)."""


class MissingRequiredFileError(ContractViolationError):
    """A required file is missing from the bundle."""


class SchemaValidationError(ContractViolationError):
    """manifest.json failed minimal schema validation."""


class HashMismatchError(ContractViolationError):
    """A file hash did not match the manifest / sha256sums entry."""


# -----------------------------------------------------------------------------
# Manifest schema (v1)
# -----------------------------------------------------------------------------

MediaType = str


@dataclass(frozen=True)
class ManifestContentEntry:
    path: str
    sha256: str
    bytes: int
    media_type: MediaType


@dataclass(frozen=True)
class ProducerInfo:
    tool: str
    version: str


@dataclass(frozen=True)
class CanonicalizationInfo:
    json: str
    jsonl: str


@dataclass(frozen=True)
class InvariantsInfo:
    has_execution_events: bool
    ordering: str


@dataclass(frozen=True)
class ReplayPackManifestV1:
    contract_version: str
    bundle_id: str
    run_id: str
    created_at_utc: str
    peak_trade_git_sha: str
    producer: ProducerInfo
    contents: Sequence[ManifestContentEntry]
    canonicalization: CanonicalizationInfo
    invariants: InvariantsInfo
    # Optional sections (kept as unvalidated, forward-compatible dicts)
    instruments: Optional[Sequence[str]] = None
    timerange: Optional[Mapping[str, Any]] = None
    data_refs: Optional[Mapping[str, Any]] = None
    notes: Optional[str] = None


def required_manifest_keys_v1() -> Tuple[str, ...]:
    return (
        "contract_version",
        "bundle_id",
        "run_id",
        "created_at_utc",
        "peak_trade_git_sha",
        "producer",
        "contents",
        "canonicalization",
        "invariants",
    )


def validate_manifest_v1_dict(d: Mapping[str, Any]) -> None:
    """
    Minimal, dependency-free schema validation for manifest v1.

    Raises:
        SchemaValidationError: on any schema violation
    """
    missing = [k for k in required_manifest_keys_v1() if k not in d]
    if missing:
        raise SchemaValidationError(f"manifest missing required keys: {missing}")

    if str(d.get("contract_version")) != CONTRACT_VERSION:
        raise SchemaValidationError("manifest contract_version must be '1'")

    for k in ("bundle_id", "run_id", "created_at_utc", "peak_trade_git_sha"):
        if not isinstance(d.get(k), str) or not str(d.get(k)).strip():
            raise SchemaValidationError(f"manifest field must be non-empty string: {k}")

    producer = d.get("producer")
    if not isinstance(producer, Mapping):
        raise SchemaValidationError("manifest producer must be an object")
    if producer.get("tool") != "pt_replay_pack":
        raise SchemaValidationError("manifest producer.tool must be 'pt_replay_pack'")
    if not isinstance(producer.get("version"), str) or not str(producer.get("version")).strip():
        raise SchemaValidationError("manifest producer.version must be non-empty string")

    canon = d.get("canonicalization")
    if not isinstance(canon, Mapping):
        raise SchemaValidationError("manifest canonicalization must be an object")
    if canon.get("json") != CANON_JSON_RULE:
        raise SchemaValidationError(f"manifest canonicalization.json must be {CANON_JSON_RULE!r}")
    if canon.get("jsonl") != CANON_JSONL_RULE:
        raise SchemaValidationError(
            f"manifest canonicalization.jsonl must be {CANON_JSONL_RULE!r}"
        )

    inv = d.get("invariants")
    if not isinstance(inv, Mapping):
        raise SchemaValidationError("manifest invariants must be an object")
    if inv.get("has_execution_events") is not True:
        raise SchemaValidationError("manifest invariants.has_execution_events must be true")
    if inv.get("ordering") != EVENT_ORDERING_INVARIANT:
        raise SchemaValidationError(
            f"manifest invariants.ordering must be {EVENT_ORDERING_INVARIANT!r}"
        )

    contents = d.get("contents")
    if not isinstance(contents, list) or not contents:
        raise SchemaValidationError("manifest contents must be a non-empty list")
    for i, item in enumerate(contents):
        if not isinstance(item, Mapping):
            raise SchemaValidationError(f"manifest contents[{i}] must be an object")
        for req in ("path", "sha256", "bytes", "media_type"):
            if req not in item:
                raise SchemaValidationError(f"manifest contents[{i}] missing key: {req}")
        if not isinstance(item.get("path"), str) or not str(item["path"]).strip():
            raise SchemaValidationError(f"manifest contents[{i}].path must be string")
        if not isinstance(item.get("sha256"), str) or len(str(item["sha256"])) != 64:
            raise SchemaValidationError(f"manifest contents[{i}].sha256 must be 64-hex")
        if not isinstance(item.get("bytes"), int) or int(item["bytes"]) < 0:
            raise SchemaValidationError(f"manifest contents[{i}].bytes must be int >= 0")
        if not isinstance(item.get("media_type"), str) or not str(item["media_type"]).strip():
            raise SchemaValidationError(f"manifest contents[{i}].media_type must be string")


def validate_bundle_required_files(relpaths_present: Iterable[str]) -> None:
    present = set(relpaths_present)
    missing = [p for p in REQUIRED_FILES if p not in present]
    if missing:
        raise MissingRequiredFileError(f"bundle missing required files: {missing}")
