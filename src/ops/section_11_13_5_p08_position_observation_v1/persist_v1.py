"""Sanitized evidence persist for the P08 one-shot positions GET."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.evidence_v1 import (
    verify_manifest_v1,
    write_json_v1,
    write_manifest_v1,
)
from src.ops.section_11_13_5_p08_position_observation_v1.constants_v1 import (
    AUTHORIZED_ENDPOINT,
    AUTHORIZED_OPERATION,
    CANONICAL_LIVE_EARLIEST_UNRESOLVED_DEPENDENCY,
    ENDPOINT,
    EXPECTED_ORIGIN_MAIN_SHA,
    OWNER_GO,
    REUSED_CREDENTIAL_CLASS,
    REUSED_HTTP_CLIENT,
    REUSED_SECRETREF_URI,
    REUSED_SIGNER,
    REUSED_TRANSPORT,
    TARGET_INSTRUMENT_ID,
    THIS_SLICE,
    WORKPACKAGE_ID,
)
from src.ops.section_11_13_5_p08_position_observation_v1.persist_claims_v1 import (
    CLAIMS,
)

_SECRET_VALUE_PREFIXES = ("ok-access-", "plaintext:", "sk-")
_SECRET_VALUE_KEYS = {
    "api_secret",
    "api-secret",
    "passphrase",
    "ok-access-key",
    "ok-access-sign",
    "ok-access-passphrase",
    "ok-access-timestamp",
}


class P08PositionObservationPersistError(RuntimeError):
    """Fail-closed evidence persist violation."""


def assert_no_secrets_in_payload_v1(payload: Mapping[str, Any]) -> None:
    def _walk(value: Any, key: str = "") -> None:
        if isinstance(value, Mapping):
            for child_key, child in value.items():
                _walk(child, str(child_key))
            return
        if isinstance(value, list):
            for item in value:
                _walk(item, key)
            return
        if not isinstance(value, str):
            return
        key_l = str(key).strip().lower()
        text = value.strip()
        lowered = text.lower()
        if key_l in _SECRET_VALUE_KEYS and text and text not in {"<REDACTED>", "<REF_ONLY>"}:
            raise P08PositionObservationPersistError("SECRET_IN_EVIDENCE")
        if any(lowered.startswith(prefix) for prefix in _SECRET_VALUE_PREFIXES):
            raise P08PositionObservationPersistError("SECRET_IN_EVIDENCE")

    _walk(payload)


def persist_p08_position_observation_evidence_v1(
    *,
    pack: Path,
    origin_main_sha: str,
    snapshot: Mapping[str, Any],
    adjudication: Mapping[str, Any],
    summary: Mapping[str, Any],
) -> dict[str, Any]:
    if str(origin_main_sha or "").strip() != EXPECTED_ORIGIN_MAIN_SHA:
        raise P08PositionObservationPersistError("ORIGIN_MAIN_SHA_MISMATCH")
    assert_no_secrets_in_payload_v1(snapshot)
    assert_no_secrets_in_payload_v1(adjudication)
    assert_no_secrets_in_payload_v1(summary)
    pack.mkdir(parents=True, exist_ok=False)
    write_json_v1(pack / "GET_SNAPSHOT.sanitized.json", snapshot)
    write_json_v1(pack / "ADJUDICATION.json", adjudication)
    write_json_v1(pack / "SUMMARY.json", summary)
    write_json_v1(
        pack / "claims.json",
        {
            **CLAIMS,
            "OWNER_GO": OWNER_GO,
            "THIS_SLICE": THIS_SLICE,
            "WORKPACKAGE_ID": WORKPACKAGE_ID,
            "AUTHORIZED_OPERATION": AUTHORIZED_OPERATION,
            "AUTHORIZED_ENDPOINT": AUTHORIZED_ENDPOINT,
            "POSITIONS_ENDPOINT": ENDPOINT,
            "TARGET_INSTRUMENT_ID": TARGET_INSTRUMENT_ID,
            "REUSED_HTTP_CLIENT": REUSED_HTTP_CLIENT,
            "REUSED_TRANSPORT": REUSED_TRANSPORT,
            "REUSED_SIGNER": REUSED_SIGNER,
            "SECRETREF_URI": REUSED_SECRETREF_URI,
            "CREDENTIAL_CLASS": REUSED_CREDENTIAL_CLASS,
            "CANONICAL_LIVE_EARLIEST_UNRESOLVED_DEPENDENCY": (
                CANONICAL_LIVE_EARLIEST_UNRESOLVED_DEPENDENCY
            ),
            "SECRET_VALUES_INCLUDED": False,
        },
    )
    write_manifest_v1(
        pack,
        (
            "GET_SNAPSHOT.sanitized.json",
            "ADJUDICATION.json",
            "SUMMARY.json",
            "claims.json",
        ),
    )
    verified = verify_manifest_v1(pack)
    if int(verified.get("MANIFEST_VERIFY_RC", 1)) != 0:
        raise P08PositionObservationPersistError("MANIFEST_VERIFY_FAILED")
    return verified
