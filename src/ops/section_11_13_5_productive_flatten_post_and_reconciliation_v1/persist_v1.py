"""Sanitized evidence persist for productive flatten POST and reconciliation."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.evidence_v1 import (
    verify_manifest_v1,
    write_json_v1,
    write_manifest_v1,
)
from src.ops.section_11_13_5_productive_flatten_post_and_reconciliation_v1.constants_v1 import (
    EXPECTED_ORIGIN_MAIN_SHA,
    OWNER_GO,
    THIS_SLICE,
    WORKPACKAGE_ID,
)
from src.ops.section_11_13_5_productive_flatten_post_and_reconciliation_v1.contract_v1 import (
    assert_payload_not_live_unlock_v1,
)

_MANIFEST_FILES: tuple[str, ...] = (
    "CENSUS.json",
    "LINEAGE.json",
    "ADJUDICATION.json",
    "SUMMARY.json",
    "claims.json",
    "OBSERVATIONS.sanitized.json",
    "RUNTIME_PERMIT.json",
    "POST_ACTION.sanitized.json",
)

_SECRET_VALUE_KEYS = {
    "api_secret",
    "api-secret",
    "passphrase",
    "ok-access-key",
    "ok-access-sign",
    "ok-access-passphrase",
    "ok-access-timestamp",
}


class ProductiveFlattenPostPersistError(RuntimeError):
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
        if key_l in _SECRET_VALUE_KEYS and text and text not in {"<REDACTED>", "<REF_ONLY>"}:
            raise ProductiveFlattenPostPersistError("SECRET_IN_EVIDENCE")
        lowered = text.lower()
        if lowered.startswith(("ok-access-", "plaintext:", "sk-")):
            raise ProductiveFlattenPostPersistError("SECRET_IN_EVIDENCE")

    _walk(payload)


def persist_productive_flatten_post_evidence_v1(
    *,
    pack: Path,
    origin_main_sha: str,
    census: Mapping[str, Any],
    lineage: Mapping[str, Any],
    adjudication: Mapping[str, Any],
    summary: Mapping[str, Any],
    observations_sanitized: Mapping[str, Any],
    runtime_permit: Mapping[str, Any],
    post_action_sanitized: Mapping[str, Any],
    claims: Mapping[str, Any],
) -> dict[str, Any]:
    if str(origin_main_sha or "").strip() != EXPECTED_ORIGIN_MAIN_SHA:
        raise ProductiveFlattenPostPersistError("ORIGIN_MAIN_SHA_MISMATCH")
    if adjudication.get("LIVE_AUTHORIZED") is True:
        raise ProductiveFlattenPostPersistError("FORBIDDEN_LIVE_AUTHORIZED_TRUE")
    if adjudication.get("CANARY_AUTHORIZED") is True:
        raise ProductiveFlattenPostPersistError("FORBIDDEN_CANARY_AUTHORIZED_TRUE")
    if adjudication.get("RETRY_USED") is True:
        raise ProductiveFlattenPostPersistError("FORBIDDEN_RETRY")
    if adjudication.get("MERGE_AUTHORIZED_BY_THIS_PERSIST") is True:
        raise ProductiveFlattenPostPersistError("FORBIDDEN_MERGE")
    documents = {
        "CENSUS.json": census,
        "LINEAGE.json": lineage,
        "ADJUDICATION.json": adjudication,
        "SUMMARY.json": summary,
        "claims.json": {
            **dict(claims),
            "OWNER_GO": OWNER_GO,
            "THIS_SLICE": THIS_SLICE,
            "WORKPACKAGE_ID": WORKPACKAGE_ID,
            "SECRET_VALUES_INCLUDED": False,
        },
        "OBSERVATIONS.sanitized.json": observations_sanitized,
        "RUNTIME_PERMIT.json": runtime_permit,
        "POST_ACTION.sanitized.json": post_action_sanitized,
    }
    for payload in documents.values():
        assert_no_secrets_in_payload_v1(payload)
        assert_payload_not_live_unlock_v1(payload)
        if payload.get("LIVE_EXECUTION") is True:
            raise ProductiveFlattenPostPersistError("FORBIDDEN_LIVE_EXECUTION_CLAIM")
        if payload.get("RETRY_USED") is True:
            raise ProductiveFlattenPostPersistError("FORBIDDEN_RETRY")
    pack.mkdir(parents=True, exist_ok=False)
    for name, payload in documents.items():
        write_json_v1(pack / name, payload)
    write_manifest_v1(pack, _MANIFEST_FILES)
    verified = verify_manifest_v1(pack)
    if int(verified.get("MANIFEST_VERIFY_RC", 1)) != 0:
        raise ProductiveFlattenPostPersistError("MANIFEST_VERIFY_FAILED")
    return verified
