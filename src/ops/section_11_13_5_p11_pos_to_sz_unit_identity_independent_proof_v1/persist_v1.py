"""Sanitized offline evidence persist for the P11 POS_TO_SZ identity pack."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.evidence_v1 import (
    verify_manifest_v1,
    write_json_v1,
    write_manifest_v1,
)
from src.ops.section_11_13_5_p11_pos_to_sz_unit_identity_independent_proof_v1.constants_v1 import (
    EXPECTED_ORIGIN_MAIN_SHA,
    OWNER_GO,
    THIS_SLICE,
    WORKPACKAGE_ID,
)
from src.ops.section_11_13_5_p11_pos_to_sz_unit_identity_independent_proof_v1.persist_claims_v1 import (
    CLAIMS,
)

_MANIFEST_FILES: tuple[str, ...] = (
    "CENSUS.json",
    "LINEAGE.json",
    "ADJUDICATION.json",
    "OFFICIAL_EXCERPTS.json",
    "SUMMARY.json",
    "claims.json",
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


class P11PosToSzPersistError(RuntimeError):
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
            raise P11PosToSzPersistError("SECRET_IN_EVIDENCE")
        lowered = text.lower()
        if lowered.startswith(("ok-access-", "plaintext:", "sk-")):
            raise P11PosToSzPersistError("SECRET_IN_EVIDENCE")

    _walk(payload)


def persist_p11_pos_to_sz_evidence_v1(
    *,
    pack: Path,
    origin_main_sha: str,
    census: Mapping[str, Any],
    lineage: Mapping[str, Any],
    adjudication: Mapping[str, Any],
    official_excerpts: Mapping[str, Any],
    summary: Mapping[str, Any],
) -> dict[str, Any]:
    if str(origin_main_sha or "").strip() != EXPECTED_ORIGIN_MAIN_SHA:
        raise P11PosToSzPersistError("ORIGIN_MAIN_SHA_MISMATCH")
    if adjudication.get("TARGET_POSITION_QTY_UNIT") != "PROVEN":
        raise P11PosToSzPersistError("UNIT_MUST_BE_PROVEN")
    if adjudication.get("POS_TO_SZ_UNIT_IDENTITY") != "PROVEN":
        raise P11PosToSzPersistError("IDENTITY_MUST_BE_PROVEN")
    if adjudication.get("POST_PERFORMED") is True or summary.get("POST_PERFORMED") is True:
        raise P11PosToSzPersistError("FORBIDDEN_POST_CLAIM")
    if int(adjudication.get("THIS_GO_GET_COUNT") or 0) != 0:
        raise P11PosToSzPersistError("FORBIDDEN_NEW_GET_CLAIM")
    if adjudication.get("PRIVATE_AUTH_USED") is True:
        raise P11PosToSzPersistError("FORBIDDEN_PRIVATE_AUTH_CLAIM")
    documents = {
        "CENSUS.json": census,
        "LINEAGE.json": lineage,
        "ADJUDICATION.json": adjudication,
        "OFFICIAL_EXCERPTS.json": official_excerpts,
        "SUMMARY.json": summary,
        "claims.json": {
            **CLAIMS,
            "OWNER_GO": OWNER_GO,
            "THIS_SLICE": THIS_SLICE,
            "WORKPACKAGE_ID": WORKPACKAGE_ID,
            "SECRET_VALUES_INCLUDED": False,
        },
    }
    for payload in documents.values():
        assert_no_secrets_in_payload_v1(payload)
        if payload.get("POST_PERFORMED") is True:
            raise P11PosToSzPersistError("FORBIDDEN_POST_CLAIM")
        if payload.get("LIVE_EXECUTION") is True:
            raise P11PosToSzPersistError("FORBIDDEN_LIVE_EXECUTION_CLAIM")
    pack.mkdir(parents=True, exist_ok=False)
    for name, payload in documents.items():
        write_json_v1(pack / name, payload)
    write_manifest_v1(pack, _MANIFEST_FILES)
    verified = verify_manifest_v1(pack)
    if int(verified.get("MANIFEST_VERIFY_RC", 1)) != 0:
        raise P11PosToSzPersistError("MANIFEST_VERIFY_FAILED")
    return verified
