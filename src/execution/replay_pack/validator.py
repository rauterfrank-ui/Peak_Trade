from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Mapping, Tuple

from .canonical import dumps_canonical
from .contract import (
    ContractViolationError,
    HashMismatchError,
    MissingRequiredFileError,
    SchemaValidationError,
    validate_bundle_required_files,
    validate_manifest_v1_dict,
)
from .hashing import collect_files_for_hashing, parse_sha256sums_text, sha256_file


@dataclass(frozen=True)
class ValidationReport:
    bundle_root: Path
    file_count: int
    total_bytes: int
    warnings: List[str] = field(default_factory=list)


def _read_text_strict_lf(path: Path) -> str:
    # Read raw and reject CRLF (determinism / canonical artifacts).
    b = path.read_bytes()
    if b"\r\n" in b:
        raise ContractViolationError("CRLF forbidden in deterministic artifacts")
    return b.decode("utf-8")


def _parse_iso8601(s: str) -> datetime:
    # Builder uses datetime.isoformat with timezone offset.
    return datetime.fromisoformat(s)


def validate_replay_pack(bundle_path: str | Path) -> ValidationReport:
    root = Path(bundle_path)
    if not root.exists() or not root.is_dir():
        raise MissingRequiredFileError("bundle path must be an existing directory")

    # Required files check.
    relpaths_present = [p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()]
    validate_bundle_required_files(relpaths_present)

    # manifest schema + canonical bytes.
    manifest_path = root / "manifest.json"
    manifest_text = _read_text_strict_lf(manifest_path)
    manifest = json.loads(manifest_text)
    if not isinstance(manifest, Mapping):
        raise SchemaValidationError("manifest.json must be a JSON object")
    validate_manifest_v1_dict(manifest)

    canonical_manifest = dumps_canonical(manifest) + "\n"
    if manifest_text != canonical_manifest:
        raise SchemaValidationError("manifest.json must be canonical JSON (sorted keys, no ws)")

    # contents list integrity + ordering.
    contents = manifest.get("contents")
    assert isinstance(contents, list)
    paths = [str(c.get("path")) for c in contents]
    if paths != sorted(paths):
        raise SchemaValidationError("manifest.contents must be sorted by path")
    if len(set(paths)) != len(paths):
        raise SchemaValidationError("manifest.contents paths must be unique")
    if "events/execution_events.jsonl" not in set(paths):
        raise SchemaValidationError("manifest.contents must include events/execution_events.jsonl")

    # Verify content files exist + sha/bytes match.
    total_bytes = 0
    for c in contents:
        p = root / str(c["path"])
        if not p.exists() or not p.is_file():
            raise MissingRequiredFileError(f"missing content file: {c['path']}")
        expected_sha = str(c["sha256"])
        got_sha = sha256_file(p)
        if got_sha != expected_sha:
            raise HashMismatchError(f"sha256 mismatch for {c['path']}")
        expected_bytes = int(c["bytes"])
        got_bytes = int(p.stat().st_size)
        if got_bytes != expected_bytes:
            raise ContractViolationError(f"bytes mismatch for {c['path']}")
        total_bytes += got_bytes

    # Verify sha256sums.txt covers all files (excluding itself) and matches actual hashes.
    sums_path = root / "hashes" / "sha256sums.txt"
    sums_text = _read_text_strict_lf(sums_path)
    sums = parse_sha256sums_text(sums_text)

    expected_files = set(collect_files_for_hashing(root))
    if set(sums.keys()) != expected_files:
        raise ContractViolationError("sha256sums.txt must list exactly all files except itself")

    for rel, digest in sums.items():
        got = sha256_file(root / rel)
        if got != digest:
            raise HashMismatchError(f"sha256sums mismatch for {rel}")

    # Event ordering invariant check: (event_time_utc, seq) strictly increasing.
    ev_path = root / "events" / "execution_events.jsonl"
    last: Tuple[datetime, int] | None = None
    with open(ev_path, "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            if not line.strip():
                continue
            obj = json.loads(line)
            if not isinstance(obj, Mapping):
                raise ContractViolationError(f"execution_events line {line_no} must be object")
            t = obj.get("event_time_utc")
            seq = obj.get("seq")
            if not isinstance(t, str) or not isinstance(seq, int):
                raise ContractViolationError("events must include event_time_utc (str) and seq (int)")
            key = (_parse_iso8601(t), int(seq))
            if last is not None and key <= last:
                raise ContractViolationError("events not sorted by (event_time_utc, seq)")
            last = key

    # File count includes manifest + sha256sums + all other files.
    file_count = len([p for p in root.rglob("*") if p.is_file()])
    return ValidationReport(bundle_root=root, file_count=file_count, total_bytes=total_bytes)
