"""Canonical Hidden-PTY / hidden-getpass confirm-token handoff for Step-4 binding.

Reuse-before-new:
  - O3 SecureEphemeralConfirmTokenHandleV1.as_getpass_fn_v1 for non-interactive tests
  - getpass over a real TTY/PTY for operator terminals
  - Never argv, never generic env plaintext, never visible input(), never insecure fallback
"""

from __future__ import annotations

import getpass
import sys
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, Optional

from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.confirm_token_v1 import (
    fingerprint_confirm_token,
    validate_token_format,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.constants_v1 import (
    GOVERNED_EXECUTION_BINDING_CAPABILITY_ID,
    HIDDEN_PTY_CONFIRM_HANDOFF_OWNER,
)
from src.ops.secure_confirm_token_family_and_hidden_input_handoff_v1.secure_input_v1 import (
    assert_no_argv_plaintext_token_v1,
    assert_no_governed_env_plaintext_v1,
)


class HiddenPtyConfirmHandoffError(RuntimeError):
    """Fail-closed Hidden-PTY confirm-token handoff error."""


@dataclass
class HiddenPtyConfirmHandoffResultV1:
    ok: bool
    blockers: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    confirm_token_fingerprint: str = ""
    confirm_token_id: str = ""
    channel_used: str = ""
    plaintext: str = ""
    claims: dict[str, Any] = field(default_factory=dict)

    def clear_plaintext_v1(self) -> None:
        self.plaintext = ""

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "blockers": list(self.blockers),
            "notes": list(self.notes),
            "confirm_token_fingerprint": self.confirm_token_fingerprint,
            "confirm_token_id": self.confirm_token_id,
            "channel_used": self.channel_used,
            "confirm_token": "[REDACTED]",
            "claims": dict(self.claims),
            "capability_id": GOVERNED_EXECUTION_BINDING_CAPABILITY_ID,
            "owner": HIDDEN_PTY_CONFIRM_HANDOFF_OWNER,
        }


def _tty_available_v1(*, stream: Any = None) -> bool:
    target = stream if stream is not None else sys.stdin
    try:
        return bool(getattr(target, "isatty", lambda: False)())
    except Exception:  # noqa: BLE001
        return False


def acquire_confirm_token_via_canonical_hidden_pty_v1(
    *,
    getpass_fn: Callable[[str], str] | None = None,
    require_real_tty: bool = True,
    stdin_stream: Any = None,
    environ: Mapping[str, str] | None = None,
    argv: list[str] | None = None,
    prompt: str = "",
) -> HiddenPtyConfirmHandoffResultV1:
    """Acquire confirm-token plaintext via Hidden-PTY/getpass only.

    ``getpass_fn`` may be injected from O3 ephemeral handle ``as_getpass_fn_v1``
    (tests / non-interactive secure handoff). Without injection, a real TTY is
    required and stdlib ``getpass.getpass`` is used. Missing PTY without a secure
    injected getpass fails closed — no env/argv/file/input() fallback.
    """
    blockers: list[str] = []
    notes = [
        f"HIDDEN_PTY_CONFIRM_HANDOFF_OWNER={HIDDEN_PTY_CONFIRM_HANDOFF_OWNER}",
        "NO_ARGV_TOKEN=true",
        "NO_GENERIC_ENV_TOKEN=true",
        "NO_VISIBLE_INPUT_FALLBACK=true",
        "NO_INSECURE_DOWNGRADE=true",
    ]
    try:
        assert_no_argv_plaintext_token_v1(argv)
    except Exception as exc:  # noqa: BLE001
        blockers.append(f"ARGV_TOKEN_FORBIDDEN:{type(exc).__name__}")
    try:
        assert_no_governed_env_plaintext_v1(environ)
    except Exception as exc:  # noqa: BLE001
        blockers.append(f"ENV_TOKEN_FORBIDDEN:{type(exc).__name__}")

    injected = getpass_fn is not None
    tty_ok = _tty_available_v1(stream=stdin_stream)
    if not injected:
        if require_real_tty and not tty_ok:
            blockers.append("CANONICAL_HIDDEN_PTY_CONFIRM_TOKEN_PATH_NOT_AVAILABLE")
            blockers.append("REAL_PTY_TTY_REQUIRED")
            return HiddenPtyConfirmHandoffResultV1(
                ok=False,
                blockers=sorted(set(blockers)),
                notes=notes + ["FAIL_CLOSED_NO_INSECURE_FALLBACK=true"],
                claims={
                    "CONFIRM_TOKEN_CANONICAL_PATH_USED": False,
                    "CONFIRM_TOKEN_PLAINTEXT_EXPOSED": False,
                    "CONFIRM_TOKEN_PERSISTED": False,
                    "HIDDEN_PTY_REQUIRED": True,
                    "HIDDEN_PTY_AVAILABLE": False,
                },
            )
        reader: Callable[[str], str] = getpass.getpass
        channel = "HIDDEN_GETPASS_OPERATOR_TERMINAL"
    else:
        reader = getpass_fn
        channel = "SECURE_EPHEMERAL_GETPASS_FN"
        notes.append("INJECTED_SECURE_GETPASS_FN=true")

    if blockers:
        return HiddenPtyConfirmHandoffResultV1(
            ok=False,
            blockers=sorted(set(blockers)),
            notes=notes + ["FAIL_CLOSED_BEFORE_READ=true"],
            claims={
                "CONFIRM_TOKEN_CANONICAL_PATH_USED": False,
                "CONFIRM_TOKEN_PLAINTEXT_EXPOSED": False,
                "CONFIRM_TOKEN_PERSISTED": False,
            },
        )

    try:
        raw = reader(prompt)
    except Exception as exc:  # noqa: BLE001
        return HiddenPtyConfirmHandoffResultV1(
            ok=False,
            blockers=sorted(set(blockers + [f"HIDDEN_PTY_READ_FAILED:{type(exc).__name__}"])),
            notes=notes + ["FAIL_CLOSED_ON_READ_ERROR=true"],
            claims={
                "CONFIRM_TOKEN_CANONICAL_PATH_USED": False,
                "CONFIRM_TOKEN_PLAINTEXT_EXPOSED": False,
                "CONFIRM_TOKEN_PERSISTED": False,
            },
        )

    token = str(raw or "").strip()
    raw = ""
    if not token:
        return HiddenPtyConfirmHandoffResultV1(
            ok=False,
            blockers=["CONFIRM_TOKEN_EMPTY"],
            notes=notes,
            claims={
                "CONFIRM_TOKEN_CANONICAL_PATH_USED": True,
                "CONFIRM_TOKEN_PLAINTEXT_EXPOSED": False,
                "CONFIRM_TOKEN_PERSISTED": False,
            },
        )
    fmt = list(validate_token_format(token))
    if fmt:
        token = ""
        return HiddenPtyConfirmHandoffResultV1(
            ok=False,
            blockers=sorted(set(fmt)),
            notes=notes + ["CONFIRM_TOKEN_FORMAT_INVALID=true"],
            claims={
                "CONFIRM_TOKEN_CANONICAL_PATH_USED": True,
                "CONFIRM_TOKEN_PLAINTEXT_EXPOSED": False,
                "CONFIRM_TOKEN_PERSISTED": False,
            },
        )

    fp = fingerprint_confirm_token(token)
    token_id = f"ctid_{fp[:16]}"
    return HiddenPtyConfirmHandoffResultV1(
        ok=True,
        notes=notes + ["HIDDEN_PTY_HANDOFF_OK=true"],
        confirm_token_fingerprint=fp,
        confirm_token_id=token_id,
        channel_used=channel,
        plaintext=token,
        claims={
            "CONFIRM_TOKEN_CANONICAL_PATH_USED": True,
            "CONFIRM_TOKEN_PLAINTEXT_EXPOSED": False,
            "CONFIRM_TOKEN_PERSISTED": False,
            "CONFIRM_TOKEN_SHELL_HISTORY": False,
            "HIDDEN_PTY_REQUIRED": True,
            "HIDDEN_PTY_AVAILABLE": injected or tty_ok,
            "CHANNEL_USED": channel,
        },
    )
