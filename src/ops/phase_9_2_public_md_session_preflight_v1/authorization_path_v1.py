"""Read-only identification of session authorization and confirm-token paths."""

from __future__ import annotations

import inspect
from pathlib import Path
from typing import Any

from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1 import (
    authorization_consumption_runtime_v1 as wallclock_auth,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1 import (
    confirm_token_v1,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1 import (
    preregistration_contract_v1,
)
from src.ops.phase_9_2_public_md_session_preflight_v1.constants_v1 import (
    AUTHORIZATION_CONSUMPTION_OWNER,
    AUTHORIZATION_ISSUANCE_ALLOWED,
    AUTHORIZATION_CONSUMPTION_ALLOWED,
    CONFIRM_TOKEN_ENV,
    CONFIRM_TOKEN_OWNER,
    PREREGISTRATION_OWNER,
    PUBLIC_MD_SHADOW_AUTH_OWNER,
    repo_root_v1,
)
from src.ops.phase_9_2_public_md_session_preflight_v1.path_portability_v1 import (
    PathPortabilityError,
    to_repository_relative_posix_path_v1,
)
from src.ops.single_future_canonical_runtime_public_md_no_order_shadow_evidence_v1 import (
    authorization_consumption_v1 as shadow_auth,
)


def _module_path_repository_relative_v1(source_file: str | None, *, repo_root: Path) -> str:
    """Persist inspect.getsourcefile() as a repository-relative POSIX path."""
    raw = source_file or ""
    try:
        return to_repository_relative_posix_path_v1(raw, repo_root=repo_root)
    except PathPortabilityError:
        # Modules are loaded from the package repository even when evidence is
        # materialized into an isolated fixture root. Bind to package root.
        return to_repository_relative_posix_path_v1(raw, repo_root=repo_root_v1())


def prove_authorization_and_confirm_token_path_v1(
    *,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    root = Path(repo_root) if repo_root is not None else repo_root_v1()
    # Identify canonical modules (no issuance / consumption in this preflight).
    # inspect.getsourcefile returns absolute local paths; persist only
    # repository-relative POSIX paths for portable evidence digests.
    confirm_mod = _module_path_repository_relative_v1(
        inspect.getsourcefile(confirm_token_v1),
        repo_root=root,
    )
    prereg_mod = _module_path_repository_relative_v1(
        inspect.getsourcefile(preregistration_contract_v1),
        repo_root=root,
    )
    wallclock_mod = _module_path_repository_relative_v1(
        inspect.getsourcefile(wallclock_auth),
        repo_root=root,
    )
    shadow_mod = _module_path_repository_relative_v1(
        inspect.getsourcefile(shadow_auth),
        repo_root=root,
    )

    plaintext_guard = "assert_no_plaintext_token_fields" in dir(confirm_token_v1)
    fingerprint_only = "fingerprint_confirm_token" in dir(confirm_token_v1)
    binding = "compute_confirm_token_binding_sha256" in dir(confirm_token_v1)
    verify = "verify_confirm_token_v1" in dir(confirm_token_v1)

    # Ensure this preflight itself does not authorize issuance/consumption.
    issuance_blocked = AUTHORIZATION_ISSUANCE_ALLOWED is False
    consumption_blocked = AUTHORIZATION_CONSUMPTION_ALLOWED is False

    ok = (
        bool(confirm_mod)
        and bool(prereg_mod)
        and bool(wallclock_mod)
        and bool(shadow_mod)
        and plaintext_guard
        and fingerprint_only
        and binding
        and verify
        and issuance_blocked
        and consumption_blocked
    )
    return {
        "ok": ok,
        "AUTHORIZATION_PATH_IDENTIFIED": ok,
        "CONFIRM_TOKEN_CANONICAL_PATH_IDENTIFIED": bool(confirm_mod) and plaintext_guard,
        "CONFIRM_TOKEN_PLAINTEXT_EXPOSED": False,
        "CONFIRM_TOKEN_PERSISTED": False,
        "CONFIRM_TOKEN_SHELL_HISTORY": False,
        "MANUAL_OWNER_TOKEN_CREATION_REQUIRED": False,
        "CONFIRM_TOKEN_ENV": CONFIRM_TOKEN_ENV,
        "owners": {
            "confirm_token": CONFIRM_TOKEN_OWNER,
            "preregistration": PREREGISTRATION_OWNER,
            "wallclock_authorization_consumption": AUTHORIZATION_CONSUMPTION_OWNER,
            "public_md_shadow_authorization_consumption": PUBLIC_MD_SHADOW_AUTH_OWNER,
        },
        "module_paths": {
            "confirm_token_v1": confirm_mod,
            "preregistration_contract_v1": prereg_mod,
            "authorization_consumption_runtime_v1": wallclock_mod,
            "public_md_shadow_authorization_consumption_v1": shadow_mod,
        },
        "bindings_required": [
            "repository_sha",
            "config_digest",
            "session_id",
            "scope_digest",
            "confirm_token_binding_sha256",
            "single_use_consumption",
            "revocation_ledger",
        ],
        "AUTHORIZATION_ISSUED": False,
        "AUTHORIZATION_CONSUMED": False,
        "note": (
            "Preflight identifies canonical paths only; issuance and consumption "
            "require a separate Owner-GO."
        ),
    }
