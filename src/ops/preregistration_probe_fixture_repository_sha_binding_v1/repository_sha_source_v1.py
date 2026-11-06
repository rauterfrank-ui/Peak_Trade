"""Fail-closed repository SHA resolution from the checked-out git commit."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

from src.ops.preregistration_probe_fixture_repository_sha_binding_v1.constants_v1 import (
    REPOSITORY_SHA_FULL_LENGTH,
    REPOSITORY_SHA_HEX_RE,
    REPOSITORY_SHA_SOURCE,
)

_SHA_RE = re.compile(REPOSITORY_SHA_HEX_RE)


class RepositoryShaResolutionErrorV1(RuntimeError):
    """Raised when the repository SHA cannot be resolved fail-closed."""


def assert_valid_repository_sha_v1(value: str | None, *, field: str = "repository_sha") -> str:
    if value is None:
        raise RepositoryShaResolutionErrorV1(f"{field.upper()}_MISSING")
    raw = str(value)
    if raw == "":
        raise RepositoryShaResolutionErrorV1(f"{field.upper()}_EMPTY")
    if raw != raw.lower():
        raise RepositoryShaResolutionErrorV1(f"{field.upper()}_NOT_LOWERCASE_HEX")
    if len(raw) != REPOSITORY_SHA_FULL_LENGTH:
        raise RepositoryShaResolutionErrorV1(
            f"{field.upper()}_INVALID_LENGTH:{len(raw)}!={REPOSITORY_SHA_FULL_LENGTH}"
        )
    if not _SHA_RE.fullmatch(raw):
        raise RepositoryShaResolutionErrorV1(f"{field.upper()}_INVALID_HEX_FORMAT")
    return raw


def resolve_repository_sha_from_git_head_v1(*, repo_root: Path) -> str:
    """Return full 40-char lowercase SHA from `git rev-parse HEAD` only.

    No environment defaults, no branch names, no config authority, no \"unknown\".
    Source authority: REPOSITORY_SHA_SOURCE=git_rev_parse_HEAD.
    """
    root = Path(repo_root).resolve()
    git_marker = root / ".git"
    if not git_marker.exists():
        raise RepositoryShaResolutionErrorV1("GIT_DIR_ABSENT_FAIL_CLOSED")
    try:
        proc = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        raise RepositoryShaResolutionErrorV1(f"GIT_REV_PARSE_UNAVAILABLE:{exc}") from exc
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "").strip()
        raise RepositoryShaResolutionErrorV1(f"GIT_REV_PARSE_FAILED:{err or proc.returncode}")
    sha = (proc.stdout or "").strip().lower()
    if sha in {"", "unknown"} or "/" in sha or sha.startswith("refs/"):
        raise RepositoryShaResolutionErrorV1("GIT_REV_PARSE_NON_SHA_FAIL_CLOSED")
    # Document source constant without allowing it to override the resolved SHA.
    assert REPOSITORY_SHA_SOURCE == "git_rev_parse_HEAD"
    return assert_valid_repository_sha_v1(sha, field="repository_sha")
