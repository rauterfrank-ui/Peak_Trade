"""Deterministic path sanitization for O6 published evidence.

Converts repository-internal absolute paths to POSIX-relative repository paths and
redacts host-local external temporary paths to stable symbolic tokens. Does not
alter runtime/recovery semantics — evidence representation only.
"""

from __future__ import annotations

import re
from pathlib import Path, PurePosixPath
from typing import Any

# Host-local absolute path prefixes that must never appear in published evidence.
_ABS_LOCAL_PREFIX_RE = re.compile(
    r"(?:/(?:Users|home)/[^/\s\"']+|/private/(?:var|tmp)|/var/folders|/tmp)(?:/[^\s\"']*)?",
    re.IGNORECASE,
)
_FILE_URI_RE = re.compile(r"file://[^\s\"']+", re.IGNORECASE)
_ROOTDIR_LINE_RE = re.compile(r"(?im)^(rootdir:\s*).+$")


class PathSanitizationErrorV1(ValueError):
    """Fail-closed path sanitization contract violation."""


def _normalize_repo_root(repository_root: Path) -> Path:
    return Path(repository_root).resolve()


def sanitize_path_value_v1(raw: str, *, repository_root: Path) -> str:
    """Sanitize one string that may contain an absolute local path."""
    text = str(raw)
    if not text:
        return text
    if text.startswith("file://") or text.lower().startswith("file://"):
        return "o6://redacted-file-uri"

    repo = _normalize_repo_root(repository_root)
    try:
        candidate = Path(text)
        # Absolute path under repository → relative POSIX.
        if candidate.is_absolute():
            resolved = candidate
            try:
                # Prefer string prefix match without requiring the path to exist.
                repo_s = str(repo)
                cand_s = str(resolved)
                if cand_s == repo_s or cand_s.startswith(repo_s + "/"):
                    rel = cand_s[len(repo_s) :].lstrip("/")
                    return str(PurePosixPath(rel)) if rel else "."
            except Exception:  # noqa: BLE001
                pass
            # External absolute → stable symbolic token.
            return "o6://external-temp/" + PurePosixPath(candidate.name or "path").as_posix()
    except Exception:  # noqa: BLE001
        pass

    # Embedded absolute substrings inside free-form detail strings.
    def _sub_abs(match: re.Match[str]) -> str:
        fragment = match.group(0)
        try:
            return sanitize_path_value_v1(fragment, repository_root=repo)
        except Exception:  # noqa: BLE001
            return "o6://external-temp/path"

    text = _ABS_LOCAL_PREFIX_RE.sub(_sub_abs, text)
    text = _FILE_URI_RE.sub("o6://redacted-file-uri", text)
    return text


def sanitize_pytest_output_v1(raw: str, *, repository_root: Path) -> str:
    """Produce hygienic pytest evidence without absolute rootdir / host paths."""
    text = str(raw or "")
    # Drop or rewrite rootdir lines that embed absolute local paths.
    text = _ROOTDIR_LINE_RE.sub(r"\1<REPOSITORY_ROOT>", text)
    # Also rewrite platform lines that embed absolute paths elsewhere.
    sanitized_lines: list[str] = []
    for line in text.splitlines():
        sanitized_lines.append(sanitize_path_value_v1(line, repository_root=repository_root))
    body = "\n".join(sanitized_lines)
    if text.endswith("\n"):
        body += "\n"
    # Final sweep for residual abs prefixes.
    if contains_absolute_local_path_v1(body):
        body = _ABS_LOCAL_PREFIX_RE.sub("o6://external-temp/path", body)
        body = _FILE_URI_RE.sub("o6://redacted-file-uri", body)
    return body


def sanitize_evidence_payload_v1(payload: Any, *, repository_root: Path) -> Any:
    """Recursively sanitize strings in JSON-compatible evidence payloads."""
    if isinstance(payload, dict):
        return {
            str(k): sanitize_evidence_payload_v1(v, repository_root=repository_root)
            for k, v in payload.items()
        }
    if isinstance(payload, list):
        return [sanitize_evidence_payload_v1(v, repository_root=repository_root) for v in payload]
    if isinstance(payload, tuple):
        return [sanitize_evidence_payload_v1(v, repository_root=repository_root) for v in payload]
    if isinstance(payload, str):
        return sanitize_path_value_v1(payload, repository_root=repository_root)
    return payload


def contains_absolute_local_path_v1(text: str) -> bool:
    if _FILE_URI_RE.search(text or ""):
        return True
    if _ABS_LOCAL_PREFIX_RE.search(text or ""):
        return True
    # Generic Unix absolute home/tmp markers.
    return bool(re.search(r"(?:^|[\s\"'=])/(?:Users|home|tmp|private|var/folders)/", text or ""))


def assert_no_absolute_local_paths_in_tree_v1(root: Path) -> dict[str, Any]:
    """Scan published evidence files for absolute local path leaks.

    Ephemeral harness directories named ``_tmp_*`` are excluded because they are
    removed before publication and must not block hygiene gates.
    """
    hits: list[str] = []
    root = Path(root)
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.name.startswith("."):
            continue
        # Skip ephemeral failure-injection / writer harness trees.
        try:
            rel_parts = path.relative_to(root).parts
        except ValueError:
            rel_parts = path.parts
        if any(part.startswith("_tmp_") for part in rel_parts):
            continue
        try:
            data = path.read_bytes()
        except OSError:
            continue
        # Skip obvious binaries.
        if b"\0" in data[:1024]:
            continue
        text = data.decode("utf-8", errors="replace")
        if contains_absolute_local_path_v1(text):
            hits.append(str(PurePosixPath(*rel_parts)))
    return {
        "ok": not hits,
        "absolute_local_path_match_count": len(hits),
        "files_with_hits": hits,
    }
