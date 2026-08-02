"""Repository-relative POSIX path serialization for Phase 9.2 evidence.

Runtime resolution may use absolute paths internally. Persisted evidence,
JSON, manifests and digests must only contain repository-relative POSIX
paths. Paths outside the repository root fail closed.
"""

from __future__ import annotations

import re
from pathlib import Path, PurePosixPath
from typing import Any, Iterable

_FILE_URI_RE = re.compile(r"^file:", re.IGNORECASE)
_FILE_URI_ANYWHERE_RE = re.compile(r"file://", re.IGNORECASE)
_WIN_DRIVE_RE = re.compile(r"^[A-Za-z]:[\\/]")
_WIN_UNC_RE = re.compile(r"^\\\\")
# Substring leaks for local filesystem / sandbox roots.
# Do not match bare "[A-Za-z]:/" — that false-positives on URL schemes like https://.
_ABS_LEAK_SUBSTRINGS = (
    "/Users/",
    "/home/",
    "/private/tmp/",
    "/var/folders/",
    "/tmp/",
)


class PathPortabilityError(ValueError):
    """Fail-closed path portability violation."""


def looks_absolute_filesystem_path_v1(value: str) -> bool:
    raw = str(value).strip()
    if not raw:
        return False
    if _FILE_URI_RE.match(raw):
        return True
    if raw.startswith("/"):
        return True
    if _WIN_DRIVE_RE.match(raw) or _WIN_UNC_RE.match(raw):
        return True
    return False


def to_repository_relative_posix_path_v1(
    path: str | Path,
    *,
    repo_root: Path,
) -> str:
    """Serialize a path as a canonical repository-relative POSIX path.

    - Absolute inputs under ``repo_root`` become relative POSIX paths.
    - Already-relative inputs remain stable after POSIX normalization.
    - Paths outside ``repo_root``, ``file://`` URIs, and drive-letter /
      UNC absolutes that cannot be bound to ``repo_root`` fail closed.
    """
    if path is None:
        raise PathPortabilityError("path_empty")
    raw = str(path).strip()
    if not raw:
        raise PathPortabilityError("path_empty")
    if _FILE_URI_RE.match(raw):
        raise PathPortabilityError("file_uri_forbidden")

    root = Path(repo_root).resolve()

    if _WIN_DRIVE_RE.match(raw) or _WIN_UNC_RE.match(raw):
        # Windows absolute / UNC forms are not portable evidence paths.
        # Only accept them when they resolve under the provided repo_root
        # on a Windows host; otherwise fail closed.
        try:
            candidate = Path(raw).resolve()
            return candidate.relative_to(root).as_posix()
        except (OSError, ValueError) as exc:
            raise PathPortabilityError("path_outside_repository_root") from exc

    if looks_absolute_filesystem_path_v1(raw):
        try:
            candidate = Path(raw).resolve()
            return candidate.relative_to(root).as_posix()
        except (OSError, ValueError) as exc:
            raise PathPortabilityError("path_outside_repository_root") from exc

    normalized = raw.replace("\\", "/")
    while "//" in normalized:
        normalized = normalized.replace("//", "/")
    if normalized.startswith("./"):
        normalized = normalized[2:]
    if looks_absolute_filesystem_path_v1(normalized):
        raise PathPortabilityError("absolute_path_forbidden")

    try:
        resolved = (root / PurePosixPath(normalized)).resolve()
        return resolved.relative_to(root).as_posix()
    except (OSError, ValueError) as exc:
        raise PathPortabilityError("path_outside_repository_root") from exc


def assert_no_absolute_local_paths_v1(
    payload: Any,
    *,
    repo_root: Path | None = None,
    context: str = "evidence_payload",
) -> None:
    """Fail closed if any string value leaks an absolute local filesystem path."""
    root_prefixes: tuple[str, ...] = ()
    if repo_root is not None:
        root = Path(repo_root).resolve()
        root_prefixes = (root.as_posix(), str(root))

    for value in _iter_strings_v1(payload):
        if any(token in value for token in _ABS_LEAK_SUBSTRINGS):
            raise PathPortabilityError(f"absolute_local_path_in_{context}:{value[:160]}")
        if _FILE_URI_ANYWHERE_RE.search(value):
            raise PathPortabilityError(f"file_uri_in_{context}:{value[:160]}")
        if _WIN_DRIVE_RE.match(value) or _WIN_UNC_RE.match(value):
            raise PathPortabilityError(f"absolute_local_path_in_{context}:{value[:160]}")
        for prefix in root_prefixes:
            if prefix and prefix in value:
                raise PathPortabilityError(f"repository_root_leak_in_{context}:{value[:160]}")


def _iter_strings_v1(payload: Any) -> Iterable[str]:
    if isinstance(payload, str):
        yield payload
        return
    if isinstance(payload, dict):
        for key, value in payload.items():
            if isinstance(key, str):
                yield key
            yield from _iter_strings_v1(value)
        return
    if isinstance(payload, (list, tuple)):
        for item in payload:
            yield from _iter_strings_v1(item)
