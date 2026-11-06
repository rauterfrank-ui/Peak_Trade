"""Narrow O2 reserved integration: PEAK_TRADE_CONFIRM_TOKEN_FILE + AUTH_VALIDATED.

Dashboard-only mode must never mint or consume a confirm token.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Optional

from src.ops.secure_confirm_token_family_and_hidden_input_handoff_v1.constants_v1 import (
    CAPABILITY_ID,
    RESERVED_CONFIRM_TOKEN_FILE_ENV,
    SAFETY_INVARIANTS,
)
from src.ops.secure_confirm_token_family_and_hidden_input_handoff_v1.errors_v1 import (
    DashboardOnlyTokenForbiddenError,
    SecureConfirmTokenError,
)
from src.ops.secure_confirm_token_family_and_hidden_input_handoff_v1.secure_input_v1 import (
    assert_no_argv_plaintext_token_v1,
    assert_no_governed_env_plaintext_v1,
)

MODE_DASHBOARD_ONLY = "dashboard-only"


def assert_dashboard_only_auth_boundary_v1(
    *,
    mode: str,
    parent_environ: Mapping[str, str],
    argv: Optional[list[str]] = None,
    mint_requested: bool = False,
    consume_requested: bool = False,
) -> dict[str, Any]:
    """AUTH_VALIDATED boundary for O2 dashboard-only: no mint, no consume."""
    if mode != MODE_DASHBOARD_ONLY:
        raise SecureConfirmTokenError(
            "O3_INTEGRATION_MODE_UNSUPPORTED",
            mode,
            payload={"allowed_mode": MODE_DASHBOARD_ONLY},
        )
    if mint_requested:
        raise DashboardOnlyTokenForbiddenError("CONFIRM_TOKEN_MINT_FORBIDDEN_IN_DASHBOARD_ONLY")
    if consume_requested:
        raise DashboardOnlyTokenForbiddenError("CONFIRM_TOKEN_CONSUME_FORBIDDEN_IN_DASHBOARD_ONLY")

    assert_no_argv_plaintext_token_v1(argv)
    assert_no_governed_env_plaintext_v1(parent_environ)

    token_file = str(parent_environ.get(RESERVED_CONFIRM_TOKEN_FILE_ENV) or "").strip()
    if not token_file:
        raise SecureConfirmTokenError(
            "RESERVED_CONFIRM_TOKEN_FILE_ENV_MISSING",
            RESERVED_CONFIRM_TOKEN_FILE_ENV,
        )

    # Path may exist as unused placeholder; must not be read/consumed in dashboard-only.
    path = Path(token_file)
    if path.exists() and path.is_file():
        # Refuse to load contents — presence alone is fine for O1 allowlist scaffolding.
        size = path.stat().st_size
        if size > 0:
            # Non-empty token file in dashboard-only is a configuration defect.
            raise DashboardOnlyTokenForbiddenError(
                "NON_EMPTY_CONFIRM_TOKEN_FILE_FORBIDDEN_IN_DASHBOARD_ONLY"
            )

    return {
        "ok": True,
        "capability_id": CAPABILITY_ID,
        "mode": mode,
        "lifecycle_state": "AUTH_VALIDATED",
        "reason_code": "O3_DASHBOARD_ONLY_NO_TOKEN",
        "reserved_confirm_token_file_env": RESERVED_CONFIRM_TOKEN_FILE_ENV,
        "confirm_token_file_path_present": bool(token_file),
        "confirm_token_minted": False,
        "confirm_token_consumed": False,
        "authorization_consumed": False,
        "safety_invariants": dict(SAFETY_INVARIANTS),
    }
