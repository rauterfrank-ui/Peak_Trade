"""Unified non-interactive secure confirm-token handoff API."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional

from src.ops.secure_confirm_token_family_and_hidden_input_handoff_v1.constants_v1 import (
    CAPABILITY_ID,
    INPUT_EPHEMERAL_HANDLE,
    INPUT_TOKEN_FILE_EXCEPTION,
    SCHEMA_VERSION,
)
from src.ops.secure_confirm_token_family_and_hidden_input_handoff_v1.ephemeral_handle_v1 import (
    SecureEphemeralConfirmTokenHandleV1,
)
from src.ops.secure_confirm_token_family_and_hidden_input_handoff_v1.errors_v1 import (
    SecureConfirmTokenError,
    SecureInputChannelError,
)
from src.ops.secure_confirm_token_family_and_hidden_input_handoff_v1.family_binding_v1 import (
    FamilyBoundTokenMetadataV1,
    verify_family_bound_token_v1,
)
from src.ops.secure_confirm_token_family_and_hidden_input_handoff_v1.family_matrix_v1 import (
    require_activatable_family_v1,
)
from src.ops.secure_confirm_token_family_and_hidden_input_handoff_v1.secure_input_v1 import (
    assert_control_stdin_not_used_as_secure_channel_v1,
    assert_no_argv_plaintext_token_v1,
    assert_no_governed_env_plaintext_v1,
    assert_single_secure_source_v1,
    inspect_secure_input_topology_v1,
)
from src.ops.secure_confirm_token_family_and_hidden_input_handoff_v1.token_file_v1 import (
    ConfirmTokenFileLeaseV1,
    delete_confirm_token_file_v1,
    load_confirm_token_file_secure_v1,
)


@dataclass
class SecureHandoffResultV1:
    ok: bool
    channel_used: str
    metadata: FamilyBoundTokenMetadataV1
    plaintext_exposed: bool = False
    notes: tuple[str, ...] = ()

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "capability_id": CAPABILITY_ID,
            "schema_version": SCHEMA_VERSION,
            "channel_used": self.channel_used,
            "metadata": self.metadata.to_public_dict(),
            "plaintext_exposed": self.plaintext_exposed,
            "notes": list(self.notes),
        }


def mint_noninteractive_handoff_v1(
    *,
    family_id: str,
    purpose: str,
    session_id: str,
    repository_sha: str,
    consumer_id: str,
) -> SecureEphemeralConfirmTokenHandleV1:
    """Preferred path: in-process ephemeral handle (no stdin, no file)."""
    require_activatable_family_v1(family_id)
    return SecureEphemeralConfirmTokenHandleV1.mint_bound_v1(
        family_id=family_id,
        purpose=purpose,
        session_id=session_id,
        repository_sha=repository_sha,
        consumer_id=consumer_id,
    )


def acquire_and_verify_secure_handoff_v1(
    *,
    family_id: str,
    purpose: str,
    session_id: str,
    repository_sha: str,
    consumer_id: str,
    expected_metadata: Mapping[str, Any],
    ephemeral_handle: Optional[SecureEphemeralConfirmTokenHandleV1] = None,
    token_file: Optional[Path] = None,
    repository_root: Optional[Path] = None,
    evidence_root: Optional[Path] = None,
    environ: Optional[Mapping[str, str]] = None,
    argv: Optional[list[str]] = None,
    stdin_token: str = "",
    previously_seen_fingerprints: Optional[frozenset[str]] = None,
    cleanup_token_file: bool = True,
) -> SecureHandoffResultV1:
    """Acquire token from exactly one secure source and verify family binding."""
    topology = inspect_secure_input_topology_v1()
    assert_no_argv_plaintext_token_v1(argv)
    assert_no_governed_env_plaintext_v1(environ)
    assert_control_stdin_not_used_as_secure_channel_v1(
        topology=topology,
        attempting_stdin_token=bool(str(stdin_token or "").strip()),
    )

    source = assert_single_secure_source_v1(
        has_ephemeral_handle=ephemeral_handle is not None,
        has_token_file=token_file is not None,
        has_env_plaintext=False,
        has_stdin_plaintext=bool(str(stdin_token or "").strip()),
        has_argv_plaintext=False,
    )

    plaintext = ""
    channel = ""
    try:
        if source == "ephemeral_handle":
            assert ephemeral_handle is not None
            if ephemeral_handle.metadata.family_id != family_id:
                raise SecureConfirmTokenError("CROSS_FAMILY_SUBSTITUTION_BLOCKED")
            plaintext = ephemeral_handle.borrow_plaintext_once_v1()
            channel = INPUT_EPHEMERAL_HANDLE
        else:
            assert token_file is not None
            if repository_root is None or evidence_root is None:
                raise SecureConfirmTokenError("TOKEN_FILE_ROOTS_REQUIRED")
            plaintext = load_confirm_token_file_secure_v1(
                path=token_file,
                repository_root=repository_root,
                evidence_root=evidence_root,
            )
            channel = INPUT_TOKEN_FILE_EXCEPTION

        meta = verify_family_bound_token_v1(
            confirm_token=plaintext,
            expected=expected_metadata,
            family_id=family_id,
            purpose=purpose,
            session_id=session_id,
            repository_sha=repository_sha,
            consumer_id=consumer_id,
            previously_seen_fingerprints=previously_seen_fingerprints,
        )
        return SecureHandoffResultV1(
            ok=True,
            channel_used=channel,
            metadata=meta,
            plaintext_exposed=False,
            notes=("SECURE_HANDOFF_VERIFIED", f"source={source}"),
        )
    finally:
        plaintext = ""
        if cleanup_token_file and token_file is not None and source == "token_file":
            delete_confirm_token_file_v1(token_file)
        if ephemeral_handle is not None:
            ephemeral_handle.clear_v1()


def write_ephemeral_token_file_exception_v1(
    *,
    handle: SecureEphemeralConfirmTokenHandleV1,
    path: Path,
    repository_root: Path,
    evidence_root: Path,
) -> ConfirmTokenFileLeaseV1:
    """Narrow file exception: lease created from handle borrow (single-use)."""
    token = handle.borrow_plaintext_once_v1()
    try:
        return ConfirmTokenFileLeaseV1(
            path=path,
            token=token,
            repository_root=repository_root,
            evidence_root=evidence_root,
        )
    finally:
        token = ""
        handle.clear_v1()


def assert_hidden_input_unavailable_fails_closed_v1() -> None:
    """Failure-injection helper: no secure source available."""
    try:
        assert_single_secure_source_v1(
            has_ephemeral_handle=False,
            has_token_file=False,
            has_env_plaintext=False,
            has_stdin_plaintext=False,
            has_argv_plaintext=False,
        )
    except SecureInputChannelError:
        return
    raise SecureConfirmTokenError("HIDDEN_INPUT_UNAVAILABLE_DID_NOT_FAIL")
