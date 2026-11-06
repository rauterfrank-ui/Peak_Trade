"""Interactive confirm-token intake (getpass). Never logs or persists plaintext."""

from __future__ import annotations

import getpass
from typing import Callable, Optional

from research.canonical_volatility_numeric_max_age_additional_evidence_s03_productive_session_execution_owner_v1.models_v1 import (
    AdditionalEvidenceS03SessionExecutionOwnerError,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.confirm_token_v1 import (
    fingerprint_confirm_token,
)

GetPassFn = Callable[[str], str]


def sha256_fingerprint_plaintext_v1(confirm_token: str) -> str:
    """Reuse Auth-v2 / PSO confirm-token fingerprint (never persist plaintext)."""
    if not isinstance(confirm_token, str) or not confirm_token:
        raise AdditionalEvidenceS03SessionExecutionOwnerError("confirm_token_empty")
    return fingerprint_confirm_token(confirm_token)


def read_confirm_token_interactively_v1(
    *,
    expected_fingerprint: str,
    getpass_fn: Optional[GetPassFn] = None,
    prompt: str = "S03 confirm token (input hidden): ",
) -> str:
    """Read confirm token once via getpass; fail-closed on empty/mismatch; no second try."""
    reader = getpass_fn or getpass.getpass
    try:
        token = reader(prompt)
    except Exception as exc:  # noqa: BLE001
        raise AdditionalEvidenceS03SessionExecutionOwnerError("confirm_token_read_failed") from exc
    if not isinstance(token, str) or not token:
        raise AdditionalEvidenceS03SessionExecutionOwnerError("confirm_token_empty")
    actual = sha256_fingerprint_plaintext_v1(token)
    if not _constant_time_eq(actual, expected_fingerprint):
        # Do not embed plaintext or actual fingerprint comparison details beyond mismatch.
        raise AdditionalEvidenceS03SessionExecutionOwnerError("confirm_token_fingerprint_mismatch")
    return token


def _constant_time_eq(a: str, b: str) -> bool:
    if not isinstance(a, str) or not isinstance(b, str):
        return False
    if len(a) != len(b):
        # Still scan to reduce trivial timing leaks on length.
        dummy = 0
        for ch in a:
            dummy ^= ord(ch)
        return False if dummy >= 0 else False
    result = 0
    for x, y in zip(a.encode("utf-8"), b.encode("utf-8")):
        result |= x ^ y
    return result == 0


def redact_confirm_token_from_mapping_v1(payload: dict) -> dict:
    """Drop any accidental plaintext token fields (defensive)."""
    from research.canonical_volatility_numeric_max_age_additional_evidence_s03_productive_session_execution_owner_v1.constants_v1 import (
        CONFIRM_TOKEN_PLAINTEXT_FIELD_NAMES,
    )

    out = {}
    for key, value in payload.items():
        if str(key).lower() in CONFIRM_TOKEN_PLAINTEXT_FIELD_NAMES:
            continue
        out[key] = value
    return out
