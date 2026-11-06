"""Durable freeze of the APRPI three-dot changed-path set.

`/tmp` scratch lists are not authority. Reconstruction oracle is git
`diff --name-only BASE...HEAD` bound to explicit SHAs.
"""

from __future__ import annotations

import hashlib
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from src.ops.section_11_13_5_authenticated_private_runtime_read_and_runtime_permit_issuance_v1.constants_v1 import (
    EVIDENCE_DIRNAME,
    OWNER_GO,
    PR_CHANGED_PATHS_FREEZE_BASE_SHA,
    PR_CHANGED_PATHS_FREEZE_CONTRACT_VERSION,
    PR_CHANGED_PATHS_FREEZE_COUNT,
    PR_CHANGED_PATHS_FREEZE_DIRNAME,
    PR_CHANGED_PATHS_FREEZE_GENERATOR_COMMAND,
    PR_CHANGED_PATHS_FREEZE_GIT_SEMANTICS,
    PR_CHANGED_PATHS_FREEZE_HEAD_SHA,
    PR_CHANGED_PATHS_FREEZE_SET_HASH,
    PR_CHANGED_PATHS_TEMP_HISTORICAL,
    THIS_SLICE,
    WORKPACKAGE_ID,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.evidence_v1 import (
    verify_manifest_v1,
    write_json_v1,
    write_manifest_v1,
)

_MANIFEST_FILES: tuple[str, ...] = ("CHANGED_PATHS.txt", "FREEZE.json")


class AprpiPrChangedPathsFreezeError(RuntimeError):
    """Fail-closed changed-path freeze violation."""


def _c_sort_paths(paths: Iterable[str]) -> tuple[str, ...]:
    cleaned = [str(path).strip() for path in paths if str(path).strip()]
    return tuple(sorted(cleaned, key=lambda item: item.encode("utf-8")))


def normalize_changed_paths_bytes_v1(paths: Iterable[str]) -> bytes:
    ordered = _c_sort_paths(paths)
    if not ordered:
        raise AprpiPrChangedPathsFreezeError("CHANGED_PATHS_EMPTY")
    return ("\n".join(ordered) + "\n").encode("utf-8")


def changed_paths_set_hash_v1(paths: Iterable[str]) -> str:
    return hashlib.sha256(normalize_changed_paths_bytes_v1(paths)).hexdigest()


def collect_three_dot_changed_paths_v1(
    *,
    repo_root: Path,
    base_sha: str,
    head_sha: str,
) -> tuple[str, ...]:
    base = str(base_sha or "").strip()
    head = str(head_sha or "").strip()
    if len(base) != 40 or len(head) != 40:
        raise AprpiPrChangedPathsFreezeError("SHA_NOT_FULL_HEX")
    spec = f"{base}...{head}"
    completed = subprocess.run(
        ["git", "diff", "--name-only", spec],
        cwd=str(repo_root),
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise AprpiPrChangedPathsFreezeError(
            f"GIT_DIFF_FAILED:{completed.returncode}:{completed.stderr.strip()}"
        )
    return _c_sort_paths(completed.stdout.splitlines())


def build_freeze_document_v1(
    *,
    paths: Sequence[str],
    base_sha: str,
    head_sha: str,
    created_at_utc: str,
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    ordered = _c_sort_paths(paths)
    digest = changed_paths_set_hash_v1(ordered)
    payload: dict[str, Any] = {
        "AUTHORITY": "NONE",
        "BASE_SHA": str(base_sha).strip(),
        "CANARY_AUTHORIZED": False,
        "CHANGED_FILE_COUNT": len(ordered),
        "CHANGED_FILE_SET_HASH": digest,
        "CHANGED_PATHS": list(ordered),
        "CONTRACT_VERSION": PR_CHANGED_PATHS_FREEZE_CONTRACT_VERSION,
        "CREATED_AT_UTC": str(created_at_utc).strip(),
        "CREATED_AT_UTC_IN_PATH_SET_HASH": False,
        "DOCUMENT_CLASS": "APRPI_PR_CHANGED_PATHS_FREEZE_V1",
        "DOCUMENT_ROLE": "FORENSIC_GIT_DIFF_INVENTORY_NOT_RUNTIME_SSOT",
        "FLATTEN_EXECUTE_AUTHORIZED": False,
        "GENERATOR_COMMAND": PR_CHANGED_PATHS_FREEZE_GENERATOR_COMMAND,
        "GIT_DIFF_SEMANTICS": PR_CHANGED_PATHS_FREEZE_GIT_SEMANTICS,
        "HEAD_SHA": str(head_sha).strip(),
        "LIVE_AUTHORIZED": False,
        "NETWORK_SESSION_AUTHORIZED": False,
        "OWNER_GO": OWNER_GO,
        "POST_PERFORMED": False,
        "PRODUCTIVE_FLATTEN_POST_AUTHORIZED": False,
        "PROVENANCE": (
            "git diff --name-only BASE...HEAD | LC_ALL=C sort; "
            "tmp scratch is historical cross-check only"
        ),
        "TEMP_PATH_HISTORICAL": PR_CHANGED_PATHS_TEMP_HISTORICAL,
        "TEMP_PATH_IS_AUTHORITY": False,
        "THIS_SLICE": THIS_SLICE,
        "WORKPACKAGE_ID": WORKPACKAGE_ID,
    }
    if extra:
        payload.update(dict(extra))
    return payload


def persist_pr_changed_paths_freeze_v1(
    *,
    repo_root: Path,
    pack: Path,
    base_sha: str = PR_CHANGED_PATHS_FREEZE_BASE_SHA,
    head_sha: str = PR_CHANGED_PATHS_FREEZE_HEAD_SHA,
    created_at_utc: str | None = None,
    require_expected_binding: bool = True,
) -> dict[str, Any]:
    paths = collect_three_dot_changed_paths_v1(
        repo_root=repo_root,
        base_sha=base_sha,
        head_sha=head_sha,
    )
    digest = changed_paths_set_hash_v1(paths)
    if require_expected_binding:
        if str(base_sha).strip() != PR_CHANGED_PATHS_FREEZE_BASE_SHA:
            raise AprpiPrChangedPathsFreezeError("BASE_SHA_MISMATCH")
        if str(head_sha).strip() != PR_CHANGED_PATHS_FREEZE_HEAD_SHA:
            raise AprpiPrChangedPathsFreezeError("HEAD_SHA_MISMATCH")
        if len(paths) != PR_CHANGED_PATHS_FREEZE_COUNT:
            raise AprpiPrChangedPathsFreezeError("CHANGED_FILE_COUNT_MISMATCH")
        if digest != PR_CHANGED_PATHS_FREEZE_SET_HASH:
            raise AprpiPrChangedPathsFreezeError("CHANGED_FILE_SET_HASH_MISMATCH")
    stamp = str(created_at_utc or "").strip()
    if not stamp:
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    freeze = build_freeze_document_v1(
        paths=paths,
        base_sha=base_sha,
        head_sha=head_sha,
        created_at_utc=stamp,
    )
    if freeze.get("POST_PERFORMED") is True:
        raise AprpiPrChangedPathsFreezeError("FORBIDDEN_POST_CLAIM")
    pack.mkdir(parents=True, exist_ok=False)
    (pack / "CHANGED_PATHS.txt").write_bytes(normalize_changed_paths_bytes_v1(paths))
    write_json_v1(pack / "FREEZE.json", freeze)
    write_manifest_v1(pack, _MANIFEST_FILES)
    verified = verify_manifest_v1(pack)
    if int(verified.get("MANIFEST_VERIFY_RC", 1)) != 0:
        raise AprpiPrChangedPathsFreezeError("MANIFEST_VERIFY_FAILED")
    return {
        **verified,
        "EVIDENCE_PACK": str(pack),
        "BASE_SHA": str(base_sha).strip(),
        "HEAD_SHA": str(head_sha).strip(),
        "CHANGED_FILE_COUNT": len(paths),
        "CHANGED_FILE_SET_HASH": digest,
        "CREATED_AT_UTC": stamp,
    }


def canonical_pr_changed_paths_freeze_pack_v1(repo_root: Path) -> Path:
    return Path(repo_root) / "evidence" / "ops" / EVIDENCE_DIRNAME / PR_CHANGED_PATHS_FREEZE_DIRNAME
