"""Hidden confirm / Phase-9.2 reuse — digest-only, one-time consume."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Mapping

from src.ops.phase_9_2_step_6_governed_productive_real_network_session_executor_v1.hidden_pty_handoff_v1 import (
    prove_hidden_pty_confirm_handoff_binding_v1,
)
from src.ops.phase_9_2_step_7_governed_productive_real_tty_campaign_execution_v1.confirm_token_path_v1 import (
    reject_confirm_token_argv_v1,
    reject_confirm_token_env_fallback_v1,
)
from src.ops.phase_9_2_step_7_governed_productive_real_tty_campaign_execution_v1.constants_v1 import (
    AUTH_CHANNEL_DELEGATED_CURSOR_SECURE_CONFIRM,
    AUTH_CHANNEL_REAL_TTY_HUMAN_CONFIRM,
)
from src.ops.phase_9_2_step_7_governed_productive_real_tty_campaign_execution_v1.delegated_cursor_secure_confirm_broker_v1 import (
    digest_sha256_v1,
)

_HEX64 = re.compile(r"^[0-9a-f]{64}$")


class ActualStartConfirmError(RuntimeError):
    """Fail-closed confirm latch violation."""


@dataclass(frozen=True)
class ConfirmLatchV1:
    confirm_token_digest: str
    authorization_channel: str
    latched: bool
    consumed: bool
    minted: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "confirm_token_digest": self.confirm_token_digest,
            "authorization_channel": self.authorization_channel,
            "latched": self.latched,
            "consumed": self.consumed,
            "minted": self.minted,
            "plaintext_exposed": False,
        }


_CONSUMED_DIGESTS: set[str] = set()


def reset_confirm_consumption_registry_v1() -> None:
    _CONSUMED_DIGESTS.clear()


def latch_and_consume_confirm_digest_v1(
    *,
    confirm_token_digest: str,
    expected_confirm_token_digest: str | None = None,
    authorization_channel: str = AUTH_CHANNEL_REAL_TTY_HUMAN_CONFIRM,
    argv: list[str] | None = None,
    environ: Mapping[str, str] | None = None,
    mint_from_plaintext: str | None = None,
) -> ConfirmLatchV1:
    blockers = reject_confirm_token_argv_v1(argv)
    blockers.extend(reject_confirm_token_env_fallback_v1(environ))
    if blockers:
        raise ActualStartConfirmError(";".join(blockers))
    if authorization_channel not in {
        AUTH_CHANNEL_REAL_TTY_HUMAN_CONFIRM,
        AUTH_CHANNEL_DELEGATED_CURSOR_SECURE_CONFIRM,
    }:
        raise ActualStartConfirmError(f"HIDDEN_CONFIRM_CHANNEL_UNKNOWN:{authorization_channel}")
    handoff = prove_hidden_pty_confirm_handoff_binding_v1()
    if handoff.get("ok") is not True:
        raise ActualStartConfirmError("HIDDEN_PTY_HANDOFF_BINDING_FAILED")

    digest = str(confirm_token_digest or "").strip().lower()
    minted = False
    if mint_from_plaintext is not None:
        # Digest-only mint path: plaintext never retained beyond digest compute.
        digest = digest_sha256_v1(mint_from_plaintext)
        minted = True
        del mint_from_plaintext
    if not _HEX64.match(digest):
        raise ActualStartConfirmError("CONFIRM_TOKEN_DIGEST_INVALID")
    if expected_confirm_token_digest is not None:
        expected = str(expected_confirm_token_digest).strip().lower()
        if digest != expected:
            raise ActualStartConfirmError("CONFIRM_TOKEN_DIGEST_MISMATCH")
    if digest in _CONSUMED_DIGESTS:
        raise ActualStartConfirmError(f"CONFIRM_TOKEN_REPLAY_FORBIDDEN:{digest[:12]}")
    _CONSUMED_DIGESTS.add(digest)
    return ConfirmLatchV1(
        confirm_token_digest=digest,
        authorization_channel=authorization_channel,
        latched=True,
        consumed=True,
        minted=minted,
    )
