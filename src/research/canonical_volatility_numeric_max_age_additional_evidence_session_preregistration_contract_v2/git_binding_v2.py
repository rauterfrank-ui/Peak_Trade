"""Fail-closed full-SHA and ancestor binding helpers for contract v2.

Uses local git only (rev-parse / cat-file / merge-base). No network. No HEAD
fallback when an explicit execution SHA is required. No branch-name authority.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

from research.canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v2.constants_v2 import (
    FULL_GIT_SHA_HEX_RE,
    FULL_GIT_SHA_LENGTH,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v2.models_v2 import (
    AdditionalEvidenceSessionPreregistrationContractV2Error,
)

_SHA_RE = re.compile(FULL_GIT_SHA_HEX_RE)


def assert_full_git_sha_v2(value: object, *, field: str) -> str:
    if value is None:
        raise AdditionalEvidenceSessionPreregistrationContractV2Error(f"{field}_missing")
    if not isinstance(value, str):
        raise AdditionalEvidenceSessionPreregistrationContractV2Error(f"{field}_invalid_format")
    raw = value
    if raw == "":
        raise AdditionalEvidenceSessionPreregistrationContractV2Error(f"{field}_empty")
    if raw != raw.lower():
        raise AdditionalEvidenceSessionPreregistrationContractV2Error(f"{field}_not_lowercase_hex")
    if len(raw) != FULL_GIT_SHA_LENGTH:
        raise AdditionalEvidenceSessionPreregistrationContractV2Error(f"{field}_invalid_length")
    if not _SHA_RE.fullmatch(raw):
        raise AdditionalEvidenceSessionPreregistrationContractV2Error(f"{field}_invalid_format")
    if "/" in raw or raw.startswith("refs/") or raw in {"HEAD", "unknown"}:
        raise AdditionalEvidenceSessionPreregistrationContractV2Error(
            f"{field}_branch_or_symbolic_forbidden"
        )
    return raw


def _run_git(args: list[str], *, repo_root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo_root), *args],
        check=False,
        capture_output=True,
        text=True,
    )


def resolve_artifact_creation_sha_from_git_v2(*, repo_root: Path) -> str:
    """Read artifact_creation_sha from local `git rev-parse HEAD` (provenance only)."""
    root = Path(repo_root).resolve()
    if not (root / ".git").exists() and not (root / ".git").is_file():
        # worktree .git may be a file
        git_marker = root / ".git"
        if not git_marker.exists():
            raise AdditionalEvidenceSessionPreregistrationContractV2Error(
                "git_dir_absent_fail_closed"
            )
    proc = _run_git(["rev-parse", "HEAD"], repo_root=root)
    if proc.returncode != 0:
        raise AdditionalEvidenceSessionPreregistrationContractV2Error(
            f"git_rev_parse_failed:{(proc.stderr or proc.stdout or '').strip()}"
        )
    return assert_full_git_sha_v2(
        (proc.stdout or "").strip().lower(), field="artifact_creation_sha"
    )


def assert_commit_exists_v2(*, sha: str, repo_root: Path, field: str) -> str:
    validated = assert_full_git_sha_v2(sha, field=field)
    proc = _run_git(["cat-file", "-e", f"{validated}^{{commit}}"], repo_root=Path(repo_root))
    if proc.returncode != 0:
        raise AdditionalEvidenceSessionPreregistrationContractV2Error(f"{field}_unknown_commit")
    return validated


def assert_is_ancestor_v2(
    *,
    ancestor_sha: str,
    descendant_sha: str,
    repo_root: Path,
) -> None:
    """Fail-closed: ancestor_sha must be contained in descendant_sha history."""
    ancestor = assert_commit_exists_v2(
        sha=ancestor_sha, repo_root=repo_root, field="code_baseline_sha"
    )
    descendant = assert_commit_exists_v2(
        sha=descendant_sha, repo_root=repo_root, field="execution_repository_sha"
    )
    proc = _run_git(
        ["merge-base", "--is-ancestor", ancestor, descendant],
        repo_root=Path(repo_root),
    )
    if proc.returncode != 0:
        raise AdditionalEvidenceSessionPreregistrationContractV2Error(
            "code_baseline_not_ancestor_of_execution_sha"
        )


def assert_baseline_not_after_artifact_creation_v2(
    *,
    code_baseline_sha: str,
    artifact_creation_sha: str,
    repo_root: Path,
) -> None:
    """Baseline must be ancestor of (or equal to) artifact_creation_sha."""
    ancestor = assert_commit_exists_v2(
        sha=code_baseline_sha, repo_root=repo_root, field="code_baseline_sha"
    )
    creation = assert_commit_exists_v2(
        sha=artifact_creation_sha, repo_root=repo_root, field="artifact_creation_sha"
    )
    proc = _run_git(
        ["merge-base", "--is-ancestor", ancestor, creation],
        repo_root=Path(repo_root),
    )
    if proc.returncode != 0:
        raise AdditionalEvidenceSessionPreregistrationContractV2Error(
            "code_baseline_after_artifact_creation_sha"
        )


def read_blob_at_sha_v2(*, sha: str, relative_path: str, repo_root: Path) -> bytes:
    validated = assert_full_git_sha_v2(sha, field="execution_repository_sha")
    proc = subprocess.run(
        ["git", "-C", str(repo_root), "show", f"{validated}:{relative_path}"],
        check=False,
        capture_output=True,
    )
    if proc.returncode != 0:
        err = (proc.stderr or b"").decode("utf-8", errors="replace").strip()
        raise AdditionalEvidenceSessionPreregistrationContractV2Error(
            f"critical_surface_path_missing_at_execution_sha:{relative_path}:{err}"
        )
    return proc.stdout


def head_equals_origin_main_v2(*, repo_root: Path) -> bool:
    """Operational checkout gate only — never embedded artifact authority."""
    head = _run_git(["rev-parse", "HEAD"], repo_root=Path(repo_root))
    main = _run_git(["rev-parse", "origin/main"], repo_root=Path(repo_root))
    if head.returncode != 0 or main.returncode != 0:
        return False
    return (head.stdout or "").strip().lower() == (main.stdout or "").strip().lower()
