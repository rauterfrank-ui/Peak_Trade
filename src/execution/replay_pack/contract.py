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


class ReplayMismatchError(ReplayPackError):
    """Replay output did not match expected outputs."""


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
    Strict, dependency-free schema validation for manifest v1.x.

    Raises:
        SchemaValidationError: on any schema violation
    """
    from .schema import validate_manifest_v1_strict

    validate_manifest_v1_strict(d)


def validate_bundle_required_files(relpaths_present: Iterable[str]) -> None:
    present = set(relpaths_present)
    missing = [p for p in REQUIRED_FILES if p not in present]
    if missing:
        raise MissingRequiredFileError(f"bundle missing required files: {missing}")
