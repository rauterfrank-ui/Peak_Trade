"""In-process ephemeral confirm-token handle (preferred non-interactive handoff)."""

from __future__ import annotations

from typing import Any, Callable, Optional

from src.ops.secure_confirm_token_family_and_hidden_input_handoff_v1.constants_v1 import (
    FAMILY_PSO_GOVERNED_PUBLIC_MD,
    FAMILY_RESEARCH_S03,
    PURPOSE_PSO_WALLCLOCK_OBSERVE,
    PURPOSE_S03_ADDITIONAL_EVIDENCE,
)
from src.ops.secure_confirm_token_family_and_hidden_input_handoff_v1.errors_v1 import (
    SecureConfirmTokenError,
)
from src.ops.secure_confirm_token_family_and_hidden_input_handoff_v1.family_binding_v1 import (
    FamilyBoundTokenMetadataV1,
    bind_plaintext_to_family_v1,
)
from src.ops.secure_confirm_token_family_and_hidden_input_handoff_v1.family_matrix_v1 import (
    require_activatable_family_v1,
)


def _default_mint_fn() -> Callable[[], str]:
    from src.ops.integrated_paper_shadow_productive_authorization_issuance_and_real_network_execution_v1.productive_confirm_token_producer_v1 import (  # noqa: E501
        mint_productive_confirm_token_v1,
    )

    return mint_productive_confirm_token_v1


class SecureEphemeralConfirmTokenHandleV1:
    """Process-local capsule: plaintext never in repr/str/logs; family-bound metadata public."""

    __slots__ = ("_token", "_cleared", "_metadata", "_consumed")

    def __init__(
        self,
        token: str,
        *,
        metadata: FamilyBoundTokenMetadataV1,
    ) -> None:
        if not isinstance(token, str) or not token:
            raise SecureConfirmTokenError("ephemeral_token_empty")
        self._token: Optional[str] = token
        self._cleared = False
        self._consumed = False
        self._metadata = metadata

    @classmethod
    def mint_bound_v1(
        cls,
        *,
        family_id: str,
        purpose: str,
        session_id: str,
        repository_sha: str,
        consumer_id: str,
        mint_fn: Optional[Callable[[], str]] = None,
    ) -> "SecureEphemeralConfirmTokenHandleV1":
        require_activatable_family_v1(family_id)
        mint = mint_fn or _default_mint_fn()
        plain = mint()
        try:
            meta = bind_plaintext_to_family_v1(
                confirm_token=plain,
                family_id=family_id,
                purpose=purpose,
                session_id=session_id,
                repository_sha=repository_sha,
                consumer_id=consumer_id,
            )
            return cls(plain, metadata=meta)
        finally:
            plain = ""

    @classmethod
    def mint_pso_v1(
        cls,
        *,
        session_id: str,
        repository_sha: str,
        consumer_id: str,
    ) -> "SecureEphemeralConfirmTokenHandleV1":
        return cls.mint_bound_v1(
            family_id=FAMILY_PSO_GOVERNED_PUBLIC_MD,
            purpose=PURPOSE_PSO_WALLCLOCK_OBSERVE,
            session_id=session_id,
            repository_sha=repository_sha,
            consumer_id=consumer_id,
        )

    @classmethod
    def mint_s03_v1(
        cls,
        *,
        session_id: str,
        repository_sha: str,
        consumer_id: str,
    ) -> "SecureEphemeralConfirmTokenHandleV1":
        return cls.mint_bound_v1(
            family_id=FAMILY_RESEARCH_S03,
            purpose=PURPOSE_S03_ADDITIONAL_EVIDENCE,
            session_id=session_id,
            repository_sha=repository_sha,
            consumer_id=consumer_id,
        )

    def __repr__(self) -> str:
        return (
            "SecureEphemeralConfirmTokenHandleV1("
            f"cleared={self._cleared}, consumed={self._consumed}, "
            f"family_id={self._metadata.family_id!r})"
        )

    def __str__(self) -> str:
        return self.__repr__()

    @property
    def metadata(self) -> FamilyBoundTokenMetadataV1:
        return self._metadata

    @property
    def cleared(self) -> bool:
        return self._cleared

    @property
    def consumed(self) -> bool:
        return self._consumed

    def public_dict_v1(self) -> dict[str, Any]:
        out = self._metadata.to_public_dict()
        out["cleared"] = self._cleared
        out["consumed"] = self._consumed
        return out

    def borrow_plaintext_once_v1(self) -> str:
        if self._cleared or self._token is None:
            raise SecureConfirmTokenError("ephemeral_token_unavailable")
        if self._consumed:
            raise SecureConfirmTokenError("CONFIRM_TOKEN_REPLAY")
        self._consumed = True
        return self._token

    def as_getpass_fn_v1(self) -> Callable[[str], str]:
        def _getpass(_prompt: str = "") -> str:
            return self.borrow_plaintext_once_v1()

        return _getpass

    def clear_v1(self) -> None:
        self._token = None
        self._cleared = True
