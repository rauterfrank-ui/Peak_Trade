from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Mapping

from .contract import CANON_JSONL_RULE, CANON_JSON_RULE, ContractViolationError, SchemaValidationError
from .contract_v2 import (
    CONTRACT_VERSION,
    EVENT_ORDERING_INVARIANT_V2,
    FIFO_ENTRIES_RELPATH,
    FIFO_SNAPSHOT_RELPATH,
)

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _require_non_empty_str(d: Mapping[str, Any], key: str) -> str:
    v = d.get(key)
    if not isinstance(v, str) or not v.strip():
        raise SchemaValidationError(f"manifest field must be non-empty string: {key}")
    return v


def _require_mapping(d: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    v = d.get(key)
    if not isinstance(v, Mapping):
        raise SchemaValidationError(f"manifest {key} must be an object")
    return v


def _validate_relpath(path: str) -> None:
    if not path or path.strip() != path:
        raise SchemaValidationError("manifest contents.path must be non-empty and trimmed")
    if path.startswith("/") or path.startswith("\\"):
        raise SchemaValidationError("manifest contents.path must be relative (no leading slash)")
    if "\\" in path:
        raise SchemaValidationError("manifest contents.path must use forward slashes only")
    if ".." in path.split("/"):
        raise SchemaValidationError("manifest contents.path must not contain '..' segments")


def validate_manifest_v2_strict(d: Mapping[str, Any]) -> None:
    """
    Strict schema validation for manifest v2.

    Backwards/forwards compatibility:
    - unknown extra top-level keys are allowed (for future additive fields)
    """
    required = (
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
    missing = [k for k in required if k not in d]
    if missing:
        raise SchemaValidationError(f"manifest missing required keys: {missing}")

    if str(d.get("contract_version")) != CONTRACT_VERSION:
        raise SchemaValidationError("manifest contract_version must be '2'")

    _require_non_empty_str(d, "bundle_id")
    _require_non_empty_str(d, "run_id")
    created_at = _require_non_empty_str(d, "created_at_utc")
    try:
        datetime.fromisoformat(created_at)
    except Exception as ex:  # noqa: BLE001
        raise SchemaValidationError("manifest created_at_utc must be ISO8601") from ex

    _require_non_empty_str(d, "peak_trade_git_sha")

    producer = _require_mapping(d, "producer")
    if producer.get("tool") != "pt_replay_pack":
        raise SchemaValidationError("manifest producer.tool must be 'pt_replay_pack'")
    if not isinstance(producer.get("version"), str) or not str(producer.get("version")).strip():
        raise SchemaValidationError("manifest producer.version must be non-empty string")

    canon = _require_mapping(d, "canonicalization")
    if canon.get("json") != CANON_JSON_RULE:
        raise SchemaValidationError(f"manifest canonicalization.json must be {CANON_JSON_RULE!r}")
    if canon.get("jsonl") != CANON_JSONL_RULE:
        raise SchemaValidationError(f"manifest canonicalization.jsonl must be {CANON_JSONL_RULE!r}")

    inv = _require_mapping(d, "invariants")
    if inv.get("has_execution_events") is not True:
        raise SchemaValidationError("manifest invariants.has_execution_events must be true")
    if inv.get("ordering") != EVENT_ORDERING_INVARIANT_V2:
        raise SchemaValidationError(
            f"manifest invariants.ordering must be {EVENT_ORDERING_INVARIANT_V2!r}"
        )
    has_fifo = inv.get("has_fifo_ledger")
    if has_fifo is not True:
        raise SchemaValidationError("manifest invariants.has_fifo_ledger must be true for v2")

    contents = d.get("contents")
    if not isinstance(contents, list) or not contents:
        raise SchemaValidationError("manifest contents must be a non-empty list")

    paths: list[str] = []
    for i, item in enumerate(contents):
        if not isinstance(item, Mapping):
            raise SchemaValidationError(f"manifest contents[{i}] must be an object")
        for req in ("path", "sha256", "bytes", "media_type"):
            if req not in item:
                raise SchemaValidationError(f"manifest contents[{i}] missing key: {req}")

        p = item.get("path")
        if not isinstance(p, str):
            raise SchemaValidationError(f"manifest contents[{i}].path must be string")
        _validate_relpath(p)
        paths.append(p)

        sha = item.get("sha256")
        if not isinstance(sha, str) or _SHA256_RE.fullmatch(sha) is None:
            raise SchemaValidationError(f"manifest contents[{i}].sha256 must be 64-hex lowercase")

        b = item.get("bytes")
        if not isinstance(b, int) or b < 0:
            raise SchemaValidationError(f"manifest contents[{i}].bytes must be int >= 0")

        mt = item.get("media_type")
        if not isinstance(mt, str) or not mt.strip():
            raise SchemaValidationError(
                f"manifest contents[{i}].media_type must be non-empty string"
            )

    if paths != sorted(paths):
        raise SchemaValidationError("manifest.contents must be sorted by path")
    if len(set(paths)) != len(paths):
        raise SchemaValidationError("manifest.contents paths must be unique")

    # v2 must include FIFO snapshot; entries are optional.
    if FIFO_SNAPSHOT_RELPATH not in set(paths):
        raise SchemaValidationError(
            f"manifest.contents must include {FIFO_SNAPSHOT_RELPATH!r} for v2"
        )
    # If entries are present, keep contract strict about file extension/path.
    if any(p == FIFO_ENTRIES_RELPATH for p in paths) is False:
        # optional; no action
        pass


def assert_no_floats(x: Any, *, path: str = "$") -> None:
    """
    Hard error on any float anywhere (determinism).
    """
    if isinstance(x, float):
        raise ContractViolationError(f"float forbidden in deterministic artifacts at {path}")
    if isinstance(x, Mapping):
        for k, v in x.items():
            assert_no_floats(v, path=f"{path}.{k}")
        return
    if isinstance(x, (list, tuple)):
        for i, v in enumerate(x):
            assert_no_floats(v, path=f"{path}[{i}]")
