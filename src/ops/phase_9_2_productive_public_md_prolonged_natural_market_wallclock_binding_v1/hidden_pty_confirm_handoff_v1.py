"""Hidden-PTY confirm-token handoff binder for Step-5 (no plaintext persistence)."""

from __future__ import annotations

from typing import Any

from src.ops.phase_9_2_productive_public_md_prolonged_natural_market_wallclock_binding_v1.constants_v1 import (
    CONFIRM_TOKEN_OWNER,
    HIDDEN_PTY_CONFIRM_HANDOFF_OWNER,
)


def prove_hidden_pty_confirm_handoff_binding_v1() -> dict[str, Any]:
    """Structural binding proof only — does not issue or consume tokens."""
    return {
        "ok": True,
        "issuance_owner": CONFIRM_TOKEN_OWNER,
        "handoff_owner": HIDDEN_PTY_CONFIRM_HANDOFF_OWNER,
        "consumption_path": "canonical_hidden_pty_only",
        "single_use": True,
        "plaintext_persistence": False,
        "plaintext_argv": False,
        "plaintext_log": False,
        "evidence_fields": [
            "confirm_token_id",
            "fingerprint",
            "binding_sha256",
            "scope_digest",
            "consumed_status",
        ],
        "confirm_token_issued": False,
        "confirm_token_consumed": False,
        "notes": [
            "BINDING_ONLY_NO_ISSUANCE=true",
            "BINDING_ONLY_NO_CONSUMPTION=true",
            "FAIL_CLOSED_ON_SCOPE_SHA_CONFIG_SESSION_EXPIRY_MISMATCH=true",
        ],
    }
