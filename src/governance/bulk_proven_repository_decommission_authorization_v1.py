"""Bulk proven repository decommission authorization v1.

Fail-closed admission for a pre-proven, digest-bound removal set at a fixed base SHA.
Not trading authority. Not a wildcard allowlist. Distinct from exact-file decommission.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

GRANT_KIND = "BULK_PROVEN_REPOSITORY_DECOMMISSION_V1"
CONTRACT_VERSION = "bulk_proven_repository_decommission_authorization_v1"
AUTHORIZATION_TOKEN = "BULK_PROVEN_REPOSITORY_DECOMMISSION_AUTHORIZATION_V1"
OPERATION_FINAL_REPOSITORY_CONVERGENCE_CUT_V1 = "FINAL_REPOSITORY_CONVERGENCE_CUT_V1"

DEFAULT_BULK_AUTH_PATH = (
    "config/governance/bulk_proven_repository_decommission_authorization_v1.json"
)
DEFAULT_EVIDENCE_RELATIVE = (
    "evidence/ops/final_repository_residual_census_and_frozen_outside_cut_probe_v1/"
    "20260925T214500Z/FINAL_STATIC_REMOVAL_PROVEN_SET_V1.json"
)

REASON_BULK_AUTH_VALID = "BULK_DECOMMISSION_AUTH_VALID"
REASON_BULK_AUTH_INVALID = "BULK_DECOMMISSION_AUTH_INVALID"
REASON_BULK_AUTHORIZED = "BULK_PROVEN_REPOSITORY_DECOMMISSION_AUTHORIZED"
REASON_BULK_BASE_SHA_MISMATCH = "BULK_DECOMMISSION_BASE_SHA_MISMATCH"
REASON_BULK_PATH_COUNT_MISMATCH = "BULK_DECOMMISSION_PATH_COUNT_MISMATCH"
REASON_BULK_SET_SHA256_MISMATCH = "BULK_DECOMMISSION_SET_SHA256_MISMATCH"
REASON_BULK_EVIDENCE_MISSING = "BULK_DECOMMISSION_EVIDENCE_MISSING"
REASON_BULK_EVIDENCE_INVALID = "BULK_DECOMMISSION_EVIDENCE_INVALID"
REASON_BULK_UNAUTHORIZED_DELETE = "BULK_DECOMMISSION_UNAUTHORIZED_DELETE"
REASON_BULK_MISSING_AUTHORIZED_DELETE = "BULK_DECOMMISSION_MISSING_AUTHORIZED_DELETE"
REASON_BULK_RESTORED_PROVEN_PATH = "BULK_DECOMMISSION_RESTORED_PROVEN_PATH"
REASON_BULK_HARD_RETAIN_MISSING = "BULK_DECOMMISSION_HARD_RETAIN_MISSING"
REASON_BULK_INACTIVE = "BULK_DECOMMISSION_INACTIVE"

_HARD_RETAIN_PATHS = (
    ".gitignore",
    ".pre-commit-config.yaml",
    "pt",
    "scripts/pt",
)

_GIT_OBJECT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_SHA256_HEX_RE = re.compile(r"^[0-9a-f]{64}$")
_DELETED_FILE_DIFF_RE = re.compile(r"^deleted file mode ", re.M)


def _normalize_path(path: str) -> str:
    return str(path).replace("\\", "/").strip().lstrip("./")


def compute_final_static_removal_proven_set_sha256(paths: Sequence[str]) -> str:
    """Canonical SHA-256: lexicographically sorted path strings, UTF-8 + newline, chained update()."""
    digest = hashlib.sha256()
    for path in sorted(str(p) for p in paths if p):
        digest.update(path.encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def load_final_static_removal_proven_set_v1(
    *,
    repo_root: Path,
    evidence_relative_path: str,
) -> tuple[frozenset[str], dict[str, Any]]:
    evidence_path = repo_root / evidence_relative_path
    if not evidence_path.is_file():
        raise FileNotFoundError(evidence_relative_path)
    payload = json.loads(evidence_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("EVIDENCE_NOT_OBJECT")
    raw_paths = payload.get("paths")
    if not isinstance(raw_paths, list) or not all(isinstance(p, str) for p in raw_paths):
        raise ValueError("EVIDENCE_PATHS_INVALID")
    normalized = frozenset(_normalize_path(p) for p in raw_paths)
    return normalized, payload


def _deleted_paths_from_diffs(
    changed_files: Sequence[str],
    file_diffs: Mapping[str, str] | None,
) -> frozenset[str]:
    deleted: set[str] = set()
    if file_diffs is None:
        return frozenset()
    for path in changed_files:
        normalized = _normalize_path(path)
        blob = file_diffs.get(path) or file_diffs.get(normalized) or ""
        if _DELETED_FILE_DIFF_RE.search(blob):
            deleted.add(normalized)
    return frozenset(deleted)


@dataclass(frozen=True)
class BulkProvenRepositoryDecommissionDecision:
    applied: bool
    valid: bool
    grant_active: bool
    version: str | None
    reason_codes: tuple[str, ...]
    authorized_removal_paths: frozenset[str] = frozenset()
    unauthorized_delete_count: int = 0
    missing_authorized_delete_count: int = 0
    bulk_authorized_addition_count: int = 0
    convergence_cut_diff: bool = False
    base_sha_bound: bool = False


def validate_bulk_proven_repository_decommission_authorization(
    auth: Mapping[str, Any] | None,
    *,
    repo_root: Path,
) -> tuple[bool, tuple[str, ...]]:
    if auth is None:
        return False, (REASON_BULK_AUTH_INVALID, REASON_BULK_EVIDENCE_MISSING)
    reasons: list[str] = []
    if auth.get("contract_version") != CONTRACT_VERSION:
        reasons.append("BULK_CONTRACT_VERSION_MISMATCH")
    if auth.get("grant_kind") != GRANT_KIND:
        reasons.append("BULK_GRANT_KIND_MISMATCH")
    if auth.get("authorization_token") != AUTHORIZATION_TOKEN:
        reasons.append("BULK_TOKEN_MISMATCH")
    if auth.get("TOKEN_ALONE_IS_INSUFFICIENT") is not True:
        reasons.append("BULK_TOKEN_ALONE_NOT_MARKED_INSUFFICIENT")
    base_sha = str(auth.get("bound_base_sha") or "").strip().lower()
    if not _GIT_OBJECT_SHA_RE.fullmatch(base_sha):
        reasons.append("BULK_BOUND_BASE_SHA_INVALID")
    count = auth.get("authorized_removal_path_count")
    if not isinstance(count, int) or count < 1:
        reasons.append("BULK_AUTHORIZED_REMOVAL_PATH_COUNT_INVALID")
    digest = str(auth.get("authorized_removal_set_sha256") or "").strip().lower()
    if not _SHA256_HEX_RE.fullmatch(digest):
        reasons.append("BULK_AUTHORIZED_REMOVAL_SET_SHA256_INVALID")
    evidence_rel = auth.get("authorized_removal_evidence_path")
    if not isinstance(evidence_rel, str) or not evidence_rel.strip():
        reasons.append("BULK_EVIDENCE_PATH_MISSING")
    if reasons:
        return False, tuple([REASON_BULK_AUTH_INVALID, *reasons])
    return True, (REASON_BULK_AUTH_VALID,)


def evaluate_bulk_proven_repository_decommission_authorization(
    changed_files: Sequence[str],
    *,
    auth: Mapping[str, Any] | None,
    repo_root: Path,
    file_diffs: Mapping[str, str] | None,
    diff_base_sha: str | None,
) -> BulkProvenRepositoryDecommissionDecision:
    """Validate bulk grant against evidence file and BASE...HEAD delete set."""
    grant_active = bool(auth and auth.get("grant_active") is True)
    if not grant_active:
        return BulkProvenRepositoryDecommissionDecision(
            applied=False,
            valid=True,
            grant_active=False,
            version=CONTRACT_VERSION if auth else None,
            reason_codes=(REASON_BULK_INACTIVE,),
            convergence_cut_diff=False,
            base_sha_bound=False,
        )

    deleted_preview = _deleted_paths_from_diffs(changed_files, file_diffs)
    convergence_cut_diff = bool(deleted_preview)

    valid, validation_reasons = validate_bulk_proven_repository_decommission_authorization(
        auth, repo_root=repo_root
    )
    if not valid or auth is None:
        return BulkProvenRepositoryDecommissionDecision(
            applied=False,
            valid=False,
            grant_active=True,
            version=CONTRACT_VERSION,
            reason_codes=validation_reasons,
            convergence_cut_diff=convergence_cut_diff,
        )

    base_expected = str(auth.get("bound_base_sha") or "").strip().lower()
    base_actual = str(diff_base_sha or "").strip().lower()
    base_sha_bound = base_actual == base_expected
    if not base_sha_bound:
        return BulkProvenRepositoryDecommissionDecision(
            applied=False,
            valid=True,
            grant_active=True,
            version=CONTRACT_VERSION,
            reason_codes=(
                REASON_BULK_AUTH_VALID,
                REASON_BULK_BASE_SHA_MISMATCH,
            ),
            convergence_cut_diff=convergence_cut_diff,
            base_sha_bound=False,
        )

    evidence_rel = str(auth.get("authorized_removal_evidence_path") or DEFAULT_EVIDENCE_RELATIVE)
    try:
        proven_paths, evidence_payload = load_final_static_removal_proven_set_v1(
            repo_root=repo_root,
            evidence_relative_path=evidence_rel,
        )
    except (OSError, ValueError, json.JSONDecodeError):
        return BulkProvenRepositoryDecommissionDecision(
            applied=False,
            valid=True,
            grant_active=True,
            version=CONTRACT_VERSION,
            reason_codes=(
                REASON_BULK_AUTH_VALID,
                REASON_BULK_EVIDENCE_MISSING,
                REASON_BULK_EVIDENCE_INVALID,
            ),
        )

    evidence_count = evidence_payload.get("path_count")
    if evidence_count != len(proven_paths):
        return BulkProvenRepositoryDecommissionDecision(
            applied=False,
            valid=True,
            grant_active=True,
            version=CONTRACT_VERSION,
            reason_codes=(
                REASON_BULK_AUTH_VALID,
                REASON_BULK_PATH_COUNT_MISMATCH,
            ),
        )

    raw_paths = evidence_payload.get("paths")
    if not isinstance(raw_paths, list):
        raw_paths = sorted(proven_paths)
    computed_sha = compute_final_static_removal_proven_set_sha256(raw_paths)
    evidence_sha = (
        str(evidence_payload.get("final_static_removal_proven_set_sha256") or "").strip().lower()
    )
    grant_sha = str(auth.get("authorized_removal_set_sha256") or "").strip().lower()
    if computed_sha != evidence_sha or computed_sha != grant_sha:
        return BulkProvenRepositoryDecommissionDecision(
            applied=False,
            valid=True,
            grant_active=True,
            version=CONTRACT_VERSION,
            reason_codes=(
                REASON_BULK_AUTH_VALID,
                REASON_BULK_SET_SHA256_MISMATCH,
            ),
        )

    if auth.get("authorized_removal_path_count") != len(proven_paths):
        return BulkProvenRepositoryDecommissionDecision(
            applied=False,
            valid=True,
            grant_active=True,
            version=CONTRACT_VERSION,
            reason_codes=(
                REASON_BULK_AUTH_VALID,
                REASON_BULK_PATH_COUNT_MISMATCH,
            ),
        )

    for retain in _HARD_RETAIN_PATHS:
        candidate = repo_root / retain
        if retain == "scripts/pt":
            if not candidate.is_file():
                return BulkProvenRepositoryDecommissionDecision(
                    applied=False,
                    valid=True,
                    grant_active=True,
                    version=CONTRACT_VERSION,
                    reason_codes=(
                        REASON_BULK_AUTH_VALID,
                        REASON_BULK_HARD_RETAIN_MISSING,
                    ),
                )
        elif not candidate.is_file():
            return BulkProvenRepositoryDecommissionDecision(
                applied=False,
                valid=True,
                grant_active=True,
                version=CONTRACT_VERSION,
                reason_codes=(
                    REASON_BULK_AUTH_VALID,
                    REASON_BULK_HARD_RETAIN_MISSING,
                ),
            )

    for path in proven_paths:
        if (repo_root / path).exists():
            return BulkProvenRepositoryDecommissionDecision(
                applied=False,
                valid=True,
                grant_active=True,
                version=CONTRACT_VERSION,
                reason_codes=(
                    REASON_BULK_AUTH_VALID,
                    REASON_BULK_RESTORED_PROVEN_PATH,
                ),
                authorized_removal_paths=proven_paths,
                base_sha_bound=base_sha_bound,
            )

    if not deleted_preview:
        return BulkProvenRepositoryDecommissionDecision(
            applied=False,
            valid=True,
            grant_active=True,
            version=CONTRACT_VERSION,
            reason_codes=(REASON_BULK_INACTIVE,),
            convergence_cut_diff=False,
            base_sha_bound=base_sha_bound,
            authorized_removal_paths=proven_paths,
        )

    deleted = _deleted_paths_from_diffs(changed_files, file_diffs)
    unauthorized = deleted - proven_paths
    missing = proven_paths - deleted
    if unauthorized:
        return BulkProvenRepositoryDecommissionDecision(
            applied=False,
            valid=True,
            grant_active=True,
            version=CONTRACT_VERSION,
            reason_codes=(
                REASON_BULK_AUTH_VALID,
                REASON_BULK_UNAUTHORIZED_DELETE,
            ),
            authorized_removal_paths=proven_paths,
            unauthorized_delete_count=len(unauthorized),
            convergence_cut_diff=True,
            base_sha_bound=base_sha_bound,
        )
    if missing:
        return BulkProvenRepositoryDecommissionDecision(
            applied=False,
            valid=True,
            grant_active=True,
            version=CONTRACT_VERSION,
            reason_codes=(
                REASON_BULK_AUTH_VALID,
                REASON_BULK_MISSING_AUTHORIZED_DELETE,
            ),
            authorized_removal_paths=proven_paths,
            missing_authorized_delete_count=len(missing),
            convergence_cut_diff=True,
            base_sha_bound=base_sha_bound,
        )

    additions = [
        _normalize_path(p)
        for p in changed_files
        if _normalize_path(p) not in deleted
        and _normalize_path(p) not in proven_paths
        and (repo_root / p).is_file()
    ]
    # Bulk grant does not authorize net-new paths; additions may exist as modifications only.
    bulk_additions = [p for p in additions if p not in proven_paths]

    return BulkProvenRepositoryDecommissionDecision(
        applied=True,
        valid=True,
        grant_active=True,
        version=CONTRACT_VERSION,
        reason_codes=(REASON_BULK_AUTH_VALID, REASON_BULK_AUTHORIZED),
        authorized_removal_paths=proven_paths,
        unauthorized_delete_count=0,
        missing_authorized_delete_count=0,
        bulk_authorized_addition_count=len(bulk_additions),
        convergence_cut_diff=True,
        base_sha_bound=base_sha_bound,
    )
