"""Durable retention before the existing lane release boundary; no job/state owner.

All released bytes remain in an external, content addressed archive. An ACK is
published only after copy, fsync and full readback. Original paths are then moved,
never recursively deleted. Interrupted release keeps both the ACK and moved bytes.
"""

from __future__ import annotations

from contextlib import contextmanager, ExitStack
import fcntl
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Any, Iterable


class OutcomeRetentionError(ValueError):
    pass


def canonical_bytes_v1(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
    ).encode()


def digest_v1(value: Any) -> str:
    return hashlib.sha256(canonical_bytes_v1(value)).hexdigest()


def fsync_dir_v1(path: Path) -> None:
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def durable_bytes_v1(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=".publish-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
        for parent in (path.parent, *path.parent.parents):
            fsync_dir_v1(parent)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def fsync_tree_v1(root: Path) -> None:
    """Seal actual owner files before publishing a downstream consumer ACK."""
    paths = sorted(root.rglob("*"))
    for path in paths:
        if path.is_symlink():
            raise OutcomeRetentionError("RETENTION_SYMLINK_FORBIDDEN")
        if path.is_file():
            with path.open("rb") as stream:
                os.fsync(stream.fileno())
    for path in reversed([root, *[p for p in paths if p.is_dir()]]):
        fsync_dir_v1(path)
    for parent in root.parents:
        fsync_dir_v1(parent)


def immutable_json_v1(path: Path, value: Any) -> None:
    raw = canonical_bytes_v1(value)
    if path.exists():
        if path.read_bytes() != raw:
            raise OutcomeRetentionError("IMMUTABLE_ARTIFACT_CONFLICT")
        return
    durable_bytes_v1(path, raw)


@contextmanager
def exclusive_v1(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink():
        raise OutcomeRetentionError("RETENTION_LOCK_SYMLINK_FORBIDDEN")
    with path.open("a+b") as stream:
        try:
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise OutcomeRetentionError("RETENTION_WRITER_BUSY") from exc
        try:
            yield
        finally:
            fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def _inventory(root: Path, names: Iterable[str]) -> dict[str, str]:
    result = {}
    for name in names:
        target = root / name
        if target.is_symlink():
            raise OutcomeRetentionError("RETENTION_SYMLINK_FORBIDDEN")
        if not target.exists():
            continue
        for path in [target] if target.is_file() else sorted(target.rglob("*")):
            if path.is_symlink():
                raise OutcomeRetentionError("RETENTION_SYMLINK_FORBIDDEN")
            if path.is_file():
                result[str(path.relative_to(root))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def retain_then_release_lane_paths_v1(root: Path, names: Iterable[str]) -> Path:
    root = root.resolve()
    names = tuple(dict.fromkeys(names))
    if any(Path(n).is_absolute() or ".." in Path(n).parts for n in names):
        raise OutcomeRetentionError("RETENTION_PATH_INVALID")
    archive_base = root.parent / ".peaktrade_lane_retention_v1" / digest_v1(str(root))
    with ExitStack() as locks:
        locks.enter_context(exclusive_v1(archive_base / ".writer.lock"))
        from src.learning.deterministic_decision_outcome_v0.ledger_v0 import AppendOnlyDdoLedgerV0

        for name in names:
            if name.endswith(".jsonl") and (root / name).exists():
                locks.enter_context(AppendOnlyDdoLedgerV0(root / name)._exclusive_writer())
        inventory = _inventory(root, names)
        manifest = {
            "schema_version": "lane_release_retention.v1",
            "source_root": str(root),
            "paths": list(names),
            "files_sha256": inventory,
        }
        archive = archive_base / digest_v1(manifest)
        for relative, expected in inventory.items():
            copy = archive / "snapshot" / relative
            raw = (root / relative).read_bytes()
            if hashlib.sha256(raw).hexdigest() != expected:
                raise OutcomeRetentionError("RETENTION_SOURCE_CHANGED")
            if copy.exists() and copy.read_bytes() != raw:
                raise OutcomeRetentionError("RETENTION_COPY_CORRUPT")
            if not copy.exists():
                durable_bytes_v1(copy, raw)
        if _inventory(archive / "snapshot", names) != inventory:
            raise OutcomeRetentionError("RETENTION_READBACK_MISMATCH")
        immutable_json_v1(archive / "retention_ack_v1.json", manifest)
        if json.loads((archive / "retention_ack_v1.json").read_bytes()) != manifest:
            raise OutcomeRetentionError("RETENTION_ACK_READBACK_MISMATCH")
        if _inventory(root, names) != inventory:
            raise OutcomeRetentionError("RETENTION_SOURCE_CHANGED")
        # ACK precedes every destructive path transition. Preserve the original
        # files as well as the verified snapshot, including malformed old evidence.
        for name in names:
            source = root / name
            if source.exists():
                dest = archive / "released_originals" / name
                dest.parent.mkdir(parents=True, exist_ok=True)
                if dest.exists():
                    raise OutcomeRetentionError("RETENTION_RELEASE_DESTINATION_EXISTS")
                source.rename(dest)
                fsync_dir_v1(source.parent)
                fsync_dir_v1(dest.parent)
        return archive
