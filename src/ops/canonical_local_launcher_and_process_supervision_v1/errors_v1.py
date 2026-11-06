"""Errors for O2 canonical local launcher."""

from __future__ import annotations

from typing import Any, Optional


class CanonicalLauncherError(RuntimeError):
    """Fail-closed launcher / supervision error."""

    def __init__(
        self,
        code: str,
        detail: str = "",
        *,
        payload: Optional[dict[str, Any]] = None,
    ) -> None:
        self.code = code
        self.detail = detail
        self.payload = dict(payload or {})
        message = f"{code}:{detail}" if detail else code
        super().__init__(message)


class DuplicateSessionError(CanonicalLauncherError):
    def __init__(self, detail: str = "", *, payload: Optional[dict[str, Any]] = None) -> None:
        super().__init__("DUPLICATE_SESSION_START_BLOCKED", detail, payload=payload)


class ConflictingWriterError(CanonicalLauncherError):
    def __init__(self, detail: str = "", *, payload: Optional[dict[str, Any]] = None) -> None:
        super().__init__("WRITER_CONFLICT", detail, payload=payload)


class ProcessIdentityMismatchError(CanonicalLauncherError):
    def __init__(self, detail: str = "", *, payload: Optional[dict[str, Any]] = None) -> None:
        super().__init__("PID_REUSE_OR_IDENTITY_MISMATCH", detail, payload=payload)


class ModeUnauthorizedError(CanonicalLauncherError):
    def __init__(self, detail: str = "", *, payload: Optional[dict[str, Any]] = None) -> None:
        super().__init__("MODE_UNAUTHORIZED_FOR_O2_MVP", detail, payload=payload)


class PreflightFailedError(CanonicalLauncherError):
    def __init__(self, detail: str = "", *, payload: Optional[dict[str, Any]] = None) -> None:
        super().__init__("ENVIRONMENT_POLICY_FAILURE", detail, payload=payload)
