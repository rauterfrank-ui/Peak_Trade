"""Sanitized offline evidence persist for the P08 authority-boundary pack."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.evidence_v1 import (
    verify_manifest_v1,
    write_json_v1,
    write_manifest_v1,
)
from src.ops.section_11_13_5_p08_post_read_only_exhaustion_authority_boundary_v1.constants_v1 import (
    EXPECTED_ORIGIN_MAIN_SHA,
    OWNER_GO,
    THIS_SLICE,
    WORKPACKAGE_ID,
)
from src.ops.section_11_13_5_p08_post_read_only_exhaustion_authority_boundary_v1.persist_claims_v1 import (
    CLAIMS,
)

_MANIFEST_FILES: tuple[str, ...] = (
    "CLOSURE_CONDITION.json",
    "MECHANISM_CENSUS.json",
    "READINESS_SNAPSHOT.json",
    "AUTHORITY_BOUNDARY.json",
    "FUTURE_GO_DRAFT.json",
    "SAFETY.json",
    "BLOCKER_MATRIX.json",
    "ADJUDICATION.json",
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


class P08AuthorityBoundaryPersistError(RuntimeError):
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
            raise P08AuthorityBoundaryPersistError("SECRET_IN_EVIDENCE")
        lowered = text.lower()
        if lowered.startswith(("ok-access-", "plaintext:", "sk-")):
            raise P08AuthorityBoundaryPersistError("SECRET_IN_EVIDENCE")

    _walk(payload)


def persist_p08_authority_boundary_evidence_v1(
    *,
    pack: Path,
    origin_main_sha: str,
    closure: Mapping[str, Any],
    census: Mapping[str, Any],
    readiness: Mapping[str, Any],
    authority: Mapping[str, Any],
    future_go: Mapping[str, Any],
    safety: Mapping[str, Any],
    blockers: Mapping[str, Any],
    adjudication: Mapping[str, Any],
    summary: Mapping[str, Any],
) -> dict[str, Any]:
    if str(origin_main_sha or "").strip() != EXPECTED_ORIGIN_MAIN_SHA:
        raise P08AuthorityBoundaryPersistError("ORIGIN_MAIN_SHA_MISMATCH")
    documents = {
        "CLOSURE_CONDITION.json": closure,
        "MECHANISM_CENSUS.json": census,
        "READINESS_SNAPSHOT.json": readiness,
        "AUTHORITY_BOUNDARY.json": authority,
        "FUTURE_GO_DRAFT.json": future_go,
        "SAFETY.json": safety,
        "BLOCKER_MATRIX.json": blockers,
        "ADJUDICATION.json": adjudication,
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
            raise P08AuthorityBoundaryPersistError("FORBIDDEN_POST_CLAIM")
        if payload.get("P08_CLOSED") is True:
            raise P08AuthorityBoundaryPersistError("FORBIDDEN_P08_CLOSED_CLAIM")
        if payload.get("TARGET_POSITION_NONZERO_PROVEN") is True:
            raise P08AuthorityBoundaryPersistError("FORBIDDEN_NONZERO_CLAIM")
    pack.mkdir(parents=True, exist_ok=False)
    for name, payload in documents.items():
        write_json_v1(pack / name, payload)
    write_manifest_v1(pack, _MANIFEST_FILES)
    verified = verify_manifest_v1(pack)
    if int(verified.get("MANIFEST_VERIFY_RC", 1)) != 0:
        raise P08AuthorityBoundaryPersistError("MANIFEST_VERIFY_FAILED")
    return verified
