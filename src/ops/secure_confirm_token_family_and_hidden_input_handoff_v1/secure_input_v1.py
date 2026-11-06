"""Secure input channel ownership and dual-source / plaintext rejection."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import Any, Mapping, Optional

from src.ops.secure_confirm_token_family_and_hidden_input_handoff_v1.constants_v1 import (
    CHANNEL_CONTROL_STDIN,
    CHANNEL_SECURE_TOKEN_INPUT,
    FORBIDDEN_GOVERNED_ENV_KEYS,
    RESERVED_CONFIRM_TOKEN_FILE_ENV,
)
from src.ops.secure_confirm_token_family_and_hidden_input_handoff_v1.errors_v1 import (
    SecureInputChannelError,
)


@dataclass(frozen=True)
class SecureInputTopologyV1:
    control_stdin: str = CHANNEL_CONTROL_STDIN
    secure_token_input: str = CHANNEL_SECURE_TOKEN_INPUT
    control_stdin_is_tty: bool = False
    secure_channel_available: bool = False
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "CONTROL_STDIN": self.control_stdin,
            "SECURE_TOKEN_INPUT": self.secure_token_input,
            "control_stdin_is_tty": self.control_stdin_is_tty,
            "secure_channel_available": self.secure_channel_available,
            "notes": list(self.notes),
        }


def inspect_secure_input_topology_v1(
    *,
    stdin_stream: Any = None,
) -> SecureInputTopologyV1:
    stream = stdin_stream if stdin_stream is not None else sys.stdin
    is_tty = bool(getattr(stream, "isatty", lambda: False)())
    # Pipe / heredoc replace control stdin — must not be treated as secure channel.
    notes = []
    if not is_tty:
        notes.append("CONTROL_STDIN_NOT_TTY_PIPE_OR_HEREDOC_RISK")
    return SecureInputTopologyV1(
        control_stdin_is_tty=is_tty,
        secure_channel_available=False,  # only ephemeral handle / hardened file count
        notes=tuple(notes),
    )


def assert_no_argv_plaintext_token_v1(argv: Optional[list[str]] = None) -> None:
    args = list(argv) if argv is not None else list(sys.argv[1:])
    forbidden_flags = {
        "--confirm-token",
        "--confirm_token",
        "--go-token",
        "--operator-go-token",
    }
    for idx, arg in enumerate(args):
        key = arg.split("=", 1)[0]
        if key in forbidden_flags:
            raise SecureInputChannelError("NO_PLAINTEXT_IN_ARGV")
        if arg.startswith("--confirm-token=") or arg.startswith("--go-token="):
            raise SecureInputChannelError("NO_PLAINTEXT_IN_ARGV")
        # Reject positional-looking governance tokens without printing them.
        if arg.startswith("GO_PSO_SESSION_PREREG_V1_") and len(arg) >= 40:
            raise SecureInputChannelError("NO_PLAINTEXT_IN_ARGV")
        if arg == "I_KNOW_WHAT_I_AM_DOING":
            raise SecureInputChannelError("NO_PLAINTEXT_IN_ARGV")
        _ = idx


def assert_no_governed_env_plaintext_v1(
    environ: Optional[Mapping[str, str]] = None,
) -> None:
    env = environ if environ is not None else os.environ
    for key in FORBIDDEN_GOVERNED_ENV_KEYS:
        val = env.get(key)
        if val is not None and str(val).strip():
            raise SecureInputChannelError(
                "NO_PLAINTEXT_IN_ENVIRONMENT",
                key,
            )


def assert_single_secure_source_v1(
    *,
    has_ephemeral_handle: bool,
    has_token_file: bool,
    has_env_plaintext: bool,
    has_stdin_plaintext: bool,
    has_argv_plaintext: bool,
) -> str:
    sources = []
    if has_ephemeral_handle:
        sources.append("ephemeral_handle")
    if has_token_file:
        sources.append("token_file")
    if has_env_plaintext:
        sources.append("env")
    if has_stdin_plaintext:
        sources.append("stdin")
    if has_argv_plaintext:
        sources.append("argv")
    if has_argv_plaintext:
        raise SecureInputChannelError("NO_PLAINTEXT_IN_ARGV")
    if has_env_plaintext:
        raise SecureInputChannelError("NO_PLAINTEXT_IN_ENVIRONMENT")
    if len(sources) == 0:
        raise SecureInputChannelError("SECURE_TOKEN_SOURCE_REQUIRED")
    if len(sources) > 1:
        raise SecureInputChannelError(
            "CONFIRM_TOKEN_DUAL_SOURCE_FORBIDDEN",
            ",".join(sources),
        )
    # Prefer ephemeral handle; file is explicit exception.
    return sources[0]


def assert_control_stdin_not_used_as_secure_channel_v1(
    *,
    topology: SecureInputTopologyV1,
    attempting_stdin_token: bool,
) -> None:
    if attempting_stdin_token:
        # Operator stdin / pipe / heredoc is CONTROL_STDIN, not SECURE_TOKEN_INPUT.
        raise SecureInputChannelError(
            "NO_STDIN_COLLISION",
            "CONTROL_STDIN_MUST_NOT_CARRY_SECURE_TOKEN",
            payload=topology.to_dict(),
        )


def reserved_token_file_env_key_v1() -> str:
    return RESERVED_CONFIRM_TOKEN_FILE_ENV
