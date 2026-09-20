"""Runtime integrity for PL-TF-002: current origin/main + protected wire surfaces.

Replaces obsolete hardcoded EXPECTED_ORIGIN_MAIN_SHA commit pins that
self-invalidate on squash merge. ATLAS_AUTHORITY=NONE. No network.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from src.ops.pl_tf_002_productive_read_only_session_executor_v1.errors_v1 import (
    PlTf002ProductiveReadOnlySessionError,
)

RUNTIME_INTEGRITY_CONTRACT_VERSION = "pl_tf_002_runtime_integrity.v1"
ORIGIN_MAIN_RESOLUTION_SOURCE = "git_rev_parse_origin_main"
HEAD_RESOLUTION_SOURCE = "git_rev_parse_HEAD"

# Closed-world PL_TF_002 / K1 / NE-TF-001 / productive GET transport surfaces.
PROTECTED_WIRE_SURFACE_PATHS: tuple[str, ...] = (
    "src/ops/pl_tf_002_productive_read_only_session_executor_v1/constants_v1.py",
    "src/ops/pl_tf_002_productive_read_only_session_executor_v1/session_executor_v1.py",
    "src/ops/pl_tf_002_productive_read_only_session_executor_v1/k1_macos_opaque_utf8_json_material_v1.py",
    "src/ops/pl_tf_002_productive_read_only_session_executor_v1/runtime_integrity_v1.py",
    "src/ops/pl_tf_002_network_evidence_contract_v1/constants_v1.py",
    "src/ops/full_core_live_path_composition_root_v1/productive_read_only_get_transport_v1.py",
    "src/ops/full_core_live_path_composition_root_v1/checkout_independent_credential_okx_venue_auth_headers_v1.py",
    "src/ops/full_core_live_path_composition_root_v1/checkout_independent_credential_os_native_store_acquisition_v1.py",
    "src/ops/full_core_live_path_composition_root_v1/checkout_independent_credential_fail_closed_os_native_store_adapter_v1.py",
)


class PlTf002RuntimeIntegrityBackendV1(Protocol):
    """Injectable git boundary for tests. Production uses GitPlTf002RuntimeIntegrityBackendV1."""

    def resolve_origin_main_sha_v1(self) -> str: ...

    def resolve_head_sha_v1(self) -> str: ...

    def diff_origin_main_for_paths_v1(self, paths: tuple[str, ...]) -> str: ...


@dataclass(frozen=True)
class GitPlTf002RuntimeIntegrityBackendV1:
    repo_root: Path

    def resolve_origin_main_sha_v1(self) -> str:
        return _git_rev_parse_v1(self.repo_root, "origin/main")

    def resolve_head_sha_v1(self) -> str:
        return _git_rev_parse_v1(self.repo_root, "HEAD")

    def diff_origin_main_for_paths_v1(self, paths: tuple[str, ...]) -> str:
        if not paths:
            return ""
        cmd = ["git", "-C", str(self.repo_root), "diff", "origin/main", "--", *paths]
        proc = subprocess.run(cmd, check=False, capture_output=True, text=True)
        if proc.returncode != 0:
            err = (proc.stderr or proc.stdout or "").strip()
            raise PlTf002ProductiveReadOnlySessionError(
                f"PROTECTED_SURFACE_DIFF_FAILED:{err or proc.returncode}"
            )
        return proc.stdout or ""


def _git_rev_parse_v1(repo_root: Path, ref: str) -> str:
    root = Path(repo_root).resolve()
    if not (root / ".git").exists():
        raise PlTf002ProductiveReadOnlySessionError("GIT_DIR_ABSENT_FAIL_CLOSED")
    proc = subprocess.run(
        ["git", "-C", str(root), "rev-parse", ref],
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "").strip()
        raise PlTf002ProductiveReadOnlySessionError(
            f"GIT_REV_PARSE_FAILED:{err or proc.returncode}"
        )
    sha = (proc.stdout or "").strip().lower()
    if len(sha) != 40 or sha in {"unknown"} or sha.startswith("refs/"):
        raise PlTf002ProductiveReadOnlySessionError("GIT_REV_PARSE_NON_SHA_FAIL_CLOSED")
    return sha


def assert_pl_tf_002_runtime_integrity_v1(
    *,
    owner_go: str,
    declared_origin_main_sha: str,
    required_owner_go: str,
    integrity_backend: PlTf002RuntimeIntegrityBackendV1,
) -> str:
    """Fail closed unless declared SHA matches live origin/main and wire surfaces are clean."""

    if str(owner_go or "").strip() != required_owner_go:
        raise PlTf002ProductiveReadOnlySessionError("OWNER_GO_MISMATCH")
    declared = str(declared_origin_main_sha or "").strip().lower()
    if len(declared) != 40:
        raise PlTf002ProductiveReadOnlySessionError("ORIGIN_MAIN_SHA_MISMATCH")
    resolved_main = integrity_backend.resolve_origin_main_sha_v1()
    head = integrity_backend.resolve_head_sha_v1()
    if declared != resolved_main:
        raise PlTf002ProductiveReadOnlySessionError("ORIGIN_MAIN_SHA_MISMATCH")
    if head != resolved_main:
        raise PlTf002ProductiveReadOnlySessionError("HEAD_NOT_AT_ORIGIN_MAIN")
    drift = integrity_backend.diff_origin_main_for_paths_v1(PROTECTED_WIRE_SURFACE_PATHS)
    if drift.strip():
        raise PlTf002ProductiveReadOnlySessionError("PROTECTED_WIRE_SURFACE_DRIFT")
    return resolved_main


def default_integrity_backend_v1() -> PlTf002RuntimeIntegrityBackendV1:
    return GitPlTf002RuntimeIntegrityBackendV1(
        repo_root=Path(__file__).resolve().parents[3],
    )
