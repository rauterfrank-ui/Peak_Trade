"""Fail-closed errors for O3 secure confirm-token handoff."""

from __future__ import annotations

from typing import Any, Optional


class SecureConfirmTokenError(ValueError):
    """Fail-closed O3 confirm-token / secure-input error (never embeds plaintext)."""

    def __init__(
        self, code: str, detail: str = "", *, payload: Optional[dict[str, Any]] = None
    ) -> None:
        self.code = str(code)
        self.detail = str(detail)
        self.payload = dict(payload or {})
        super().__init__(self.code if not detail else f"{self.code}:{detail}")


class CrossFamilySubstitutionError(SecureConfirmTokenError):
    def __init__(
        self,
        detail: str = "",
        *,
        code: str = "CROSS_FAMILY_SUBSTITUTION_BLOCKED",
        payload: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(code, detail, payload=payload)


class SecureInputChannelError(SecureConfirmTokenError):
    def __init__(
        self,
        code: str = "SECURE_INPUT_CHANNEL_FAILURE",
        detail: str = "",
        *,
        payload: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(code, detail, payload=payload)


class TokenFileSecurityError(SecureConfirmTokenError):
    def __init__(
        self,
        code: str = "TOKEN_FILE_SECURITY_FAILURE",
        detail: str = "",
        *,
        payload: Optional[dict[str, Any]] = None,
    ) -> None:
        # Allow `TokenFileSecurityError("TOKEN_FILE_MODE_NOT_0600")` as code-only.
        if detail == "" and code and not code.startswith("TOKEN_FILE_SECURITY"):
            super().__init__(code, "", payload=payload)
        else:
            super().__init__(code, detail, payload=payload)


class DashboardOnlyTokenForbiddenError(SecureConfirmTokenError):
    def __init__(
        self,
        detail: str = "",
        *,
        code: str = "DASHBOARD_ONLY_TOKEN_FORBIDDEN",
        payload: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(code, detail, payload=payload)
