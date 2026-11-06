from __future__ import annotations

"""
Deterministic Replay Pack (Bundle Contract) — v2

v2 is strictly additive vs v1:
- v1 files and hashes must remain unchanged when building v1 (default).
- v2 adds FIFO Slice2 ledger artifacts under ledger/.
"""

from dataclasses import dataclass
from typing import Any, Literal, Mapping, Optional, Sequence, Tuple

from .contract import (
    CANON_JSONL_RULE,
    CANON_JSON_RULE,
    EVENT_ORDERING_INVARIANT,
    MediaType,
    ProducerInfo,
    ReplayPackError,
)


CONTRACT_VERSION: Literal["2"] = "2"

# Bundle root stays identical to v1:
from .contract import BUNDLE_ROOT_DIRNAME  # noqa: E402


# -----------------------------------------------------------------------------
# Bundle layout (v2)
# -----------------------------------------------------------------------------

# v2 required files include the v1 required files; additional requirements are
# gated by invariants.has_fifo_ledger (see schema/validator).
from .contract import REQUIRED_FILES as REQUIRED_FILES_V1  # noqa: E402
from .contract import OPTIONAL_FILES as OPTIONAL_FILES_V1  # noqa: E402

REQUIRED_FILES_V2: Tuple[str, ...] = REQUIRED_FILES_V1

# v2 introduces new (optional or invariant-gated) files under ledger/.
FIFO_SNAPSHOT_RELPATH = "ledger/ledger_fifo_snapshot.json"
FIFO_ENTRIES_RELPATH = "ledger/ledger_fifo_entries.jsonl"

OPTIONAL_FILES_V2: Tuple[str, ...] = OPTIONAL_FILES_V1 + (
    FIFO_SNAPSHOT_RELPATH,
    FIFO_ENTRIES_RELPATH,
)


# -----------------------------------------------------------------------------
# Manifest schema (v2)
# -----------------------------------------------------------------------------


@dataclass(frozen=True)
class InvariantsInfoV2:
    has_execution_events: bool
    ordering: str
    has_fifo_ledger: bool


@dataclass(frozen=True)
class ReplayPackManifestV2:
    contract_version: str
    bundle_id: str
    run_id: str
    created_at_utc: str
    peak_trade_git_sha: str
    producer: ProducerInfo
    contents: Sequence[Mapping[str, Any]]
    canonicalization: Mapping[str, Any]
    invariants: InvariantsInfoV2
    # Optional sections (forward-compatible)
    instruments: Optional[Sequence[str]] = None
    timerange: Optional[Mapping[str, Any]] = None
    data_refs: Optional[Mapping[str, Any]] = None
    notes: Optional[str] = None


CANONICAL_JSON_RULE_V2 = CANON_JSON_RULE
CANONICAL_JSONL_RULE_V2 = CANON_JSONL_RULE
EVENT_ORDERING_INVARIANT_V2 = EVENT_ORDERING_INVARIANT


class SchemaValidationErrorV2(ReplayPackError):
    """manifest.json failed strict schema validation (v2)."""
