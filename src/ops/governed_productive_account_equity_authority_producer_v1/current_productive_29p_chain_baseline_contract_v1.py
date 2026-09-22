"""Merge-stable baseline contract for the CURRENT_PRODUCTIVE 29P dependency chain.

Execution identity is bound to live ``origin/main`` (PL-TF-002 pattern): declared
``origin_main_sha`` must equal ``git rev-parse origin/main`` and ``HEAD`` must
match — no static post-merge-invalidating slice pin.

Persisted Cap-2.4 ``repository_sha`` values remain historical provenance; handoff
accepts closed historical binds or a persisted sha equal to the validated execution
identity.

RUNTIME_AUTHORIZATION_EFFECT=NONE
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from src.ops.single_selected_future_policy_v1.constants_v1 import SELECTION_FILENAME

RUNTIME_INTEGRITY_CONTRACT_VERSION = "current_productive_29p_chain_runtime_integrity.v1"
ORIGIN_MAIN_RESOLUTION_SOURCE = "git_rev_parse_origin_main"
HEAD_RESOLUTION_SOURCE = "git_rev_parse_HEAD"

# Closed historical persisted Cap-2.1–2.3 binds (never promote evidence; no growth).
HISTORICAL_CAP24_PERSISTED_REPOSITORY_BASELINE_SHAS = frozenset(
    {
        "8379a278517b23240ca1cdad02fe041b7d618874",
        "e5396206530415b469fa345ec04322613c953c44",
    }
)
AUTHORIZED_CAP24_PERSISTED_REPOSITORY_BASELINE_SHAS = (
    HISTORICAL_CAP24_PERSISTED_REPOSITORY_BASELINE_SHAS
)

CAP24_PUBLISH_MANIFEST_FILENAME = "cap24_selection_state_publish_manifest_v1.json"
CAP24_RUNTIME_STATE_DIRNAME = "runtime_state"

PROTECTED_CURRENT_PRODUCTIVE_29P_CHAIN_SURFACE_PATHS: tuple[str, ...] = (
    "src/ops/governed_productive_account_equity_authority_producer_v1/"
    "current_productive_29p_chain_baseline_contract_v1.py",
    "src/ops/governed_productive_account_equity_authority_producer_v1/"
    "current_productive_29p_common_epoch_handoff_v1.py",
    "src/ops/governed_productive_account_equity_authority_producer_v1/"
    "current_productive_29p_cap24_bound_instrument_provenance_handoff_v1.py",
    "src/ops/governed_productive_account_equity_authority_producer_v1/"
    "current_productive_cap24_selection_state_canonical_writer_v1.py",
    "src/ops/governed_productive_account_equity_authority_producer_v1/"
    "current_productive_eea_universe_inventory_to_cap24_and_29p_v1.py",
    "src/ops/governed_productive_account_equity_authority_producer_v1/"
    "current_productive_execution_admission_remainder_v1.py",
    "src/ops/governed_productive_account_equity_authority_producer_v1/"
    "current_productive_live_execution_port_construction_v1.py",
    "src/ops/governed_productive_account_equity_authority_producer_v1/"
    "current_productive_cap72_host_join_to_live_execution_port_v1.py",
)

_REPO_ROOT = Path(__file__).resolve().parents[3]


class CurrentProductive29PChainBaselineError(RuntimeError):
    """Fail-closed CURRENT_PRODUCTIVE 29P chain baseline violation."""


class CurrentProductive29PRuntimeIntegrityBackendV1(Protocol):
    """Injectable git boundary for tests. Production uses Git backend."""

    def resolve_origin_main_sha_v1(self) -> str: ...

    def resolve_head_sha_v1(self) -> str: ...

    def diff_origin_main_for_paths_v1(self, paths: tuple[str, ...]) -> str: ...


@dataclass(frozen=True)
class GitCurrentProductive29PRuntimeIntegrityBackendV1:
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
            raise CurrentProductive29PChainBaselineError(
                f"PROTECTED_SURFACE_DIFF_FAILED:{err or proc.returncode}"
            )
        return proc.stdout or ""


def _git_rev_parse_v1(repo_root: Path, ref: str) -> str:
    root = Path(repo_root).resolve()
    if not (root / ".git").exists():
        raise CurrentProductive29PChainBaselineError("GIT_DIR_ABSENT_FAIL_CLOSED")
    proc = subprocess.run(
        ["git", "-C", str(root), "rev-parse", ref],
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "").strip()
        raise CurrentProductive29PChainBaselineError(
            f"GIT_REV_PARSE_FAILED:{err or proc.returncode}"
        )
    sha = (proc.stdout or "").strip().lower()
    if len(sha) != 40 or sha.startswith("refs/"):
        raise CurrentProductive29PChainBaselineError("GIT_REV_PARSE_NON_SHA_FAIL_CLOSED")
    return sha


def default_current_productive_29p_integrity_backend_v1() -> (
    CurrentProductive29PRuntimeIntegrityBackendV1
):
    return GitCurrentProductive29PRuntimeIntegrityBackendV1(repo_root=_REPO_ROOT)


def assert_current_productive_29p_execution_identity_v1(
    *,
    declared_origin_main_sha: str,
    integrity_backend: CurrentProductive29PRuntimeIntegrityBackendV1 | None = None,
    verify_protected_surfaces: bool = True,
) -> str:
    """Fail-closed unless declared SHA matches trusted origin/main and HEAD aligns."""

    declared = str(declared_origin_main_sha or "").strip().lower()
    if len(declared) != 40:
        raise CurrentProductive29PChainBaselineError("ORIGIN_MAIN_SHA_MISMATCH")
    backend = integrity_backend or default_current_productive_29p_integrity_backend_v1()
    resolved_main = backend.resolve_origin_main_sha_v1()
    head = backend.resolve_head_sha_v1()
    if declared != resolved_main:
        raise CurrentProductive29PChainBaselineError("ORIGIN_MAIN_SHA_MISMATCH")
    if head != resolved_main:
        raise CurrentProductive29PChainBaselineError("HEAD_NOT_AT_ORIGIN_MAIN")
    if verify_protected_surfaces:
        drift = backend.diff_origin_main_for_paths_v1(
            PROTECTED_CURRENT_PRODUCTIVE_29P_CHAIN_SURFACE_PATHS
        )
        if drift.strip():
            raise CurrentProductive29PChainBaselineError("PROTECTED_CHAIN_SURFACE_DRIFT")
    return resolved_main


def assert_current_productive_29p_repository_sha_for_execution_v1(
    *,
    repository_sha: str,
    trusted_execution_identity: str,
) -> str:
    repo_sha = str(repository_sha or "").strip().lower()
    trusted = str(trusted_execution_identity or "").strip().lower()
    if len(repo_sha) != 40:
        raise CurrentProductive29PChainBaselineError("REPOSITORY_SHA_BASELINE_MISMATCH")
    if repo_sha != trusted:
        raise CurrentProductive29PChainBaselineError("REPOSITORY_SHA_BASELINE_MISMATCH")
    return repo_sha


def resolve_cap24_persisted_repository_sha_v1(
    *,
    productivity_root: Path,
    trusted_execution_identity: str | None = None,
) -> str:
    """Resolve persisted repository_sha for Cap-2.4 provenance handoff (fail-closed)."""

    prod_root = Path(productivity_root)
    if not prod_root.exists():
        raise CurrentProductive29PChainBaselineError("CAP24_PRODUCTIVITY_ROOT_MISSING")

    manifest_path = prod_root / CAP24_PUBLISH_MANIFEST_FILENAME
    if manifest_path.is_file():
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            sha = str(payload.get("repository_sha") or "").strip().lower()
            if sha:
                return _assert_authorized_persisted_repository_sha_v1(
                    sha,
                    trusted_execution_identity=trusted_execution_identity,
                )

    state_root = prod_root / CAP24_RUNTIME_STATE_DIRNAME
    if not state_root.is_dir():
        if (prod_root / "selection").is_dir():
            state_root = prod_root
        else:
            raise CurrentProductive29PChainBaselineError("CAP24_RUNTIME_STATE_LAYOUT_MISSING")

    sel_path = state_root / "selection" / SELECTION_FILENAME
    if not sel_path.is_file():
        raise CurrentProductive29PChainBaselineError("CAP24_SELECTION_ARTIFACT_MISSING")
    selection = json.loads(sel_path.read_text(encoding="utf-8"))
    if not isinstance(selection, dict):
        raise CurrentProductive29PChainBaselineError("CAP24_SELECTION_MALFORMED")
    sha = str(selection.get("repository_sha") or "").strip().lower()
    if not sha:
        raise CurrentProductive29PChainBaselineError("CAP24_REPOSITORY_SHA_MISSING")
    return _assert_authorized_persisted_repository_sha_v1(
        sha,
        trusted_execution_identity=trusted_execution_identity,
    )


def _assert_authorized_persisted_repository_sha_v1(
    repository_sha: str,
    *,
    trusted_execution_identity: str | None = None,
) -> str:
    sha = str(repository_sha or "").strip().lower()
    if sha in HISTORICAL_CAP24_PERSISTED_REPOSITORY_BASELINE_SHAS:
        return sha
    trusted = str(trusted_execution_identity or "").strip().lower()
    if trusted and sha == trusted:
        return sha
    raise CurrentProductive29PChainBaselineError("CAP24_REPOSITORY_SHA_NOT_AUTHORIZED")
