"""Content cache keyed by commit and blob ids. A hit cannot change output."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from scripts.ops.current_full_stack_semantic_explorer_v1.budget_v1 import BudgetV1
from scripts.ops.current_full_stack_semantic_explorer_v1.git_objects_v1 import GitEntryV1


def fingerprint_v1(
    commit_sha: str,
    entries: Sequence[GitEntryV1],
    budget: BudgetV1,
    capture_bytes: bytes | None,
    *,
    selection_mode: str,
) -> str:
    digest = hashlib.sha256()
    digest.update(selection_mode.encode("utf-8"))
    digest.update(commit_sha.encode("utf-8"))
    for entry in entries:
        digest.update(b"\0")
        digest.update(entry.path.encode("utf-8"))
        digest.update(entry.object_sha.encode("utf-8"))
        digest.update(entry.mode.encode("utf-8"))
    digest.update(
        json.dumps(
            {
                "max_files": budget.max_files,
                "max_seconds": budget.max_seconds,
                "max_nodes": budget.max_nodes,
                "max_edges": budget.max_edges,
                "max_depth": budget.max_depth,
            },
            sort_keys=True,
        ).encode("utf-8")
    )
    digest.update(capture_bytes or b"")
    return digest.hexdigest()


def load_run_cache_v1(cache_dir: Path | None, fingerprint: str) -> dict[str, Any] | None:
    if cache_dir is None:
        return None
    path = cache_dir / f"run-{fingerprint}.json"
    if not path.is_file():
        return None
    loaded = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        return None
    return loaded


def store_run_cache_v1(cache_dir: Path | None, fingerprint: str, run: Mapping[str, Any]) -> None:
    if cache_dir is None:
        return
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = cache_dir / f"run-{fingerprint}.json"
    path.write_text(
        json.dumps(run, sort_keys=True, separators=(",", ":"), ensure_ascii=True),
        encoding="utf-8",
    )


def load_parse_cache_v1(cache_dir: Path | None, blob_sha: str) -> dict[str, Any] | None:
    if cache_dir is None:
        return None
    path = cache_dir / "blobs" / f"{blob_sha}.json"
    if not path.is_file():
        return None
    loaded = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        return None
    return loaded


def store_parse_cache_v1(cache_dir: Path | None, blob_sha: str, parsed: Mapping[str, Any]) -> None:
    if cache_dir is None:
        return
    directory = cache_dir / "blobs"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / f"{blob_sha}.json").write_text(
        json.dumps(parsed, sort_keys=True, separators=(",", ":"), ensure_ascii=True),
        encoding="utf-8",
    )
