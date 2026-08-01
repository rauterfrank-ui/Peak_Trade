"""Ephemeral in-memory confirm-token handle (no plaintext persistence).

Best-effort reference clearing only — Python does not guarantee secure
memory wiping of string objects after del/clear.
"""

from __future__ import annotations

from typing import Optional

from research.canonical_volatility_numeric_max_age_additional_evidence_s03_atomic_auth_v2_reissue_consume_execute_v1.constants_v1 import (
    CANONICAL_TOKEN_GENERATOR,
    MINIMUM_CONFIRM_TOKEN_ENTROPY_BITS,
)
from research.canonical_volatility_numeric_max_age_additional_evidence_s03_atomic_auth_v2_reissue_consume_execute_v1.models_v1 import (
    AtomicS03AuthV2ReissueConsumeExecuteError,
)
from src.ops.integrated_paper_shadow_productive_authorization_issuance_and_real_network_execution_v1.productive_confirm_token_producer_v1 import (
    mint_productive_confirm_token_v1,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.confirm_token_v1 import (
    fingerprint_confirm_token,
    validate_token_format,
)


class EphemeralConfirmTokenHandleV1:
    """Process-local confirm-token capsule. Never logs or serializes plaintext."""

    __slots__ = ("_token", "_cleared", "_generator_id", "_entropy_bits")

    def __init__(
        self,
        token: str,
        *,
        generator_id: str = CANONICAL_TOKEN_GENERATOR,
        entropy_bits: int = MINIMUM_CONFIRM_TOKEN_ENTROPY_BITS,
    ) -> None:
        if not isinstance(token, str) or not token:
            raise AtomicS03AuthV2ReissueConsumeExecuteError("ephemeral_token_empty")
        blockers = validate_token_format(token)
        if blockers:
            raise AtomicS03AuthV2ReissueConsumeExecuteError("ephemeral_token_format_invalid")
        if int(entropy_bits) < MINIMUM_CONFIRM_TOKEN_ENTROPY_BITS:
            raise AtomicS03AuthV2ReissueConsumeExecuteError("ephemeral_token_entropy_below_minimum")
        self._token: Optional[str] = token
        self._cleared = False
        self._generator_id = str(generator_id)
        self._entropy_bits = int(entropy_bits)

    @classmethod
    def mint_canonical_v1(cls) -> "EphemeralConfirmTokenHandleV1":
        """Mint via canonical productive generator (secrets.token_urlsafe(32) body)."""
        token = mint_productive_confirm_token_v1()
        try:
            return cls(
                token,
                generator_id=CANONICAL_TOKEN_GENERATOR,
                entropy_bits=MINIMUM_CONFIRM_TOKEN_ENTROPY_BITS,
            )
        finally:
            # Drop caller's local binding ASAP; handle owns the sole reference.
            token = ""

    def __repr__(self) -> str:
        return (
            "EphemeralConfirmTokenHandleV1("
            f"cleared={self._cleared}, generator={self._generator_id!r}, "
            f"entropy_bits={self._entropy_bits})"
        )

    def __str__(self) -> str:
        return self.__repr__()

    @property
    def cleared(self) -> bool:
        return self._cleared

    @property
    def generator_id(self) -> str:
        return self._generator_id

    @property
    def entropy_bits(self) -> int:
        return self._entropy_bits

    def fingerprint_v1(self) -> str:
        return fingerprint_confirm_token(self._require_v1())

    def borrow_plaintext_v1(self) -> str:
        """Borrow plaintext for same-process issuance/consumption only."""
        return self._require_v1()

    def as_getpass_fn_v1(self):
        """Return a getpass-compatible callable that reveals plaintext once-path."""

        def _getpass(_prompt: str = "") -> str:
            return self.borrow_plaintext_v1()

        return _getpass

    def clear_v1(self) -> None:
        """Best-effort drop of held plaintext reference (not a secure wipe)."""
        self._token = None
        self._cleared = True

    def _require_v1(self) -> str:
        if self._cleared or self._token is None:
            raise AtomicS03AuthV2ReissueConsumeExecuteError(
                "ephemeral_token_unavailable_after_clear_or_process_boundary"
            )
        return self._token
