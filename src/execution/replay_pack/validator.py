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
from .schema import (
    assert_lf_only_bytes,
    assert_no_floats,
    validate_execution_event_object_strict,
    validate_market_data_refs_document_strict,
)
from .schema_v2 import validate_manifest_v2_strict


@dataclass(frozen=True)
class ValidationReport:
    bundle_root: Path
    file_count: int
    total_bytes: int
    warnings: List[str] = field(default_factory=list)


def _read_text_strict_lf(path: Path) -> str:
    b = path.read_bytes()
    assert_lf_only_bytes(b, label=path.name)
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

    # manifest schema + canonical bytes (LF-only + trailing LF).
    manifest_path = root / "manifest.json"
    manifest_text = _read_text_strict_lf(manifest_path)
    manifest = json.loads(manifest_text)
    if not isinstance(manifest, Mapping):
        raise SchemaValidationError("manifest.json must be a JSON object")
    contract_version = str(manifest.get("contract_version") or "1")
    if contract_version == "1":
        # v1 behavior must remain exactly stable.
        validate_manifest_v1_dict(manifest)
    elif contract_version == "2":
        validate_manifest_v2_strict(manifest)
    else:
        raise SchemaValidationError("manifest contract_version must be '1' or '2'")

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
    if contract_version == "2":
        if "ledger/ledger_fifo_snapshot.json" not in set(paths):
            raise SchemaValidationError(
                "manifest.contents must include ledger/ledger_fifo_snapshot.json for v2"
            )

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
    # Additional hardening: enforce sorted order and uniqueness at the text level.
    lines = [ln for ln in sums_text.splitlines() if ln.strip()]
    rels_in_order = []
    for ln in lines:
        parts = ln.split("  ", 1)
        if len(parts) != 2:
            raise ContractViolationError("invalid sha256sums line (expected: '<sha256>  <path>')")
        digest = parts[0].strip()
        rel = parts[1].strip()
        if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            raise ContractViolationError("invalid sha256 digest in sha256sums.txt")
        rels_in_order.append(rel)
    if rels_in_order != sorted(rels_in_order):
        raise ContractViolationError("sha256sums.txt must be sorted by path")
    if len(set(rels_in_order)) != len(rels_in_order):
        raise ContractViolationError("sha256sums.txt must not contain duplicate paths")

    expected_files = set(collect_files_for_hashing(root))
    if set(sums.keys()) != expected_files:
        raise ContractViolationError("sha256sums.txt must list exactly all files except itself")

    for rel, digest in sums.items():
        got = sha256_file(root / rel)
        if got != digest:
            raise HashMismatchError(f"sha256sums mismatch for {rel}")

    # Event ordering invariant check: (event_time_utc, seq) strictly increasing.
    ev_path = root / "events" / "execution_events.jsonl"
    assert_lf_only_bytes(ev_path.read_bytes(), label="execution_events.jsonl")
    last: Tuple[datetime, int] | None = None
    expected_seq = 0
    with open(ev_path, "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            if not line.strip():
                continue
            obj = json.loads(line)
            if not isinstance(obj, Mapping):
                raise ContractViolationError(f"execution_events line {line_no} must be object")
            validate_execution_event_object_strict(obj, line_no=line_no)
            t = str(obj["event_time_utc"])
            seq = int(obj["seq"])
            if seq != expected_seq:
                raise ContractViolationError("events seq must be contiguous starting at 0")
            expected_seq += 1

            # Enforce float-forbidden for entire event object (including payload).
            assert_no_floats(obj, path=f"$.events[{line_no}]")

            key = (_parse_iso8601(t), seq)
            if last is not None and key <= last:
                raise ContractViolationError("events not sorted by (event_time_utc, seq)")
            last = key

    # Optional market data refs file: enforce LF-only + canonical JSON + strict schema.
    md_path = root / "events" / "market_data_refs.json"
    if md_path.exists():
        md_text = _read_text_strict_lf(md_path)
        md_doc = json.loads(md_text)
        if not isinstance(md_doc, (Mapping, list)):
            raise SchemaValidationError("market_data_refs must be a JSON object or list")
        validate_market_data_refs_document_strict(md_doc)

        # Enforce canonical JSON for deterministic diffs.
        canonical_md = dumps_canonical(md_doc) + "\n"
        if md_text != canonical_md:
            raise SchemaValidationError(
                "events/market_data_refs.json must be canonical JSON (sorted keys, no ws)"
            )

    # v2 FIFO artifacts: enforce LF-only + canonical encoding.
    if contract_version == "2":
        snap_path = root / "ledger" / "ledger_fifo_snapshot.json"
        if not snap_path.exists():
            raise MissingRequiredFileError("missing ledger/ledger_fifo_snapshot.json")
        snap_text = _read_text_strict_lf(snap_path)
        snap_doc = json.loads(snap_text)
        if not isinstance(snap_doc, Mapping):
            raise SchemaValidationError("ledger_fifo_snapshot.json must be a JSON object")
        assert_no_floats(snap_doc, path="$.ledger_fifo_snapshot")
        canonical_snap = dumps_canonical(snap_doc) + "\n"
        if snap_text != canonical_snap:
            raise SchemaValidationError("ledger_fifo_snapshot.json must be canonical JSON")

        ent_path = root / "ledger" / "ledger_fifo_entries.jsonl"
        if ent_path.exists():
            assert_lf_only_bytes(ent_path.read_bytes(), label="ledger_fifo_entries.jsonl")
            with open(ent_path, "r", encoding="utf-8") as f:
                for line_no, line in enumerate(f, start=1):
                    if not line.strip():
                        continue
                    obj = json.loads(line)
                    if not isinstance(obj, Mapping):
                        raise ContractViolationError(
                            f"ledger_fifo_entries line {line_no} must be object"
                        )
                    assert_no_floats(obj, path=f"$.ledger_fifo_entries[{line_no}]")
                    if dumps_canonical(obj) != line.rstrip("\n"):
                        raise SchemaValidationError(
                            "ledger_fifo_entries.jsonl must be canonical JSONL (sorted keys, no ws)"
                        )

    # File count includes manifest + sha256sums + all other files.
    file_count = len([p for p in root.rglob("*") if p.is_file()])
    return ValidationReport(bundle_root=root, file_count=file_count, total_bytes=total_bytes)
