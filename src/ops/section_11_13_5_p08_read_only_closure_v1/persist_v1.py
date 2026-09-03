"""Sanitized plus first-party raw evidence persist for P08 read-only closure."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.evidence_v1 import (
    verify_manifest_v1,
    write_json_v1,
    write_manifest_v1,
)
from src.ops.section_11_13_5_p08_read_only_closure_v1.constants_v1 import (
    AUTHORIZED_ENDPOINTS,
    AUTHORIZED_OPERATION,
    CANONICAL_LIVE_EARLIEST_UNRESOLVED_DEPENDENCY,
    EXPECTED_ORIGIN_MAIN_SHA,
    GET_ROLE_ALGO_CONDITIONAL_OCO,
    GET_ROLE_ALGO_MOVE_ORDER_STOP,
    GET_ROLE_ALGO_TRIGGER,
    GET_ROLE_FILLS,
    GET_ROLE_ORDERS_HISTORY,
    GET_ROLE_ORDERS_PENDING,
    GET_ROLE_POSID_POSITIONS,
    OWNER_GO,
    REUSED_CREDENTIAL_CLASS,
    REUSED_HTTP_CLIENT,
    REUSED_SECRETREF_URI,
    REUSED_SIGNER,
    REUSED_TRANSPORT,
    TARGET_INST_TYPE,
    TARGET_INSTRUMENT_ID,
    THIS_SLICE,
    WORKPACKAGE_ID,
)
from src.ops.section_11_13_5_p08_read_only_closure_v1.persist_claims_v1 import CLAIMS

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

_RAW_FILENAMES = {
    GET_ROLE_ORDERS_PENDING: "GET_ORDERS_PENDING.raw.json",
    GET_ROLE_ORDERS_HISTORY: "GET_ORDERS_HISTORY.raw.json",
    GET_ROLE_ALGO_CONDITIONAL_OCO: "GET_ALGO_PENDING_CONDITIONAL_OCO.raw.json",
    GET_ROLE_ALGO_TRIGGER: "GET_ALGO_PENDING_TRIGGER.raw.json",
    GET_ROLE_ALGO_MOVE_ORDER_STOP: "GET_ALGO_PENDING_MOVE_ORDER_STOP.raw.json",
    GET_ROLE_FILLS: "GET_FILLS.raw.json",
    GET_ROLE_POSID_POSITIONS: "GET_POSID_POSITIONS.raw.json",
}


class P08ReadOnlyClosurePersistError(RuntimeError):
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
            raise P08ReadOnlyClosurePersistError("SECRET_IN_EVIDENCE")
        if any(lowered.startswith(prefix) for prefix in _SECRET_VALUE_PREFIXES):
            raise P08ReadOnlyClosurePersistError("SECRET_IN_EVIDENCE")

    _walk(payload)


def persist_p08_read_only_closure_v1(
    *,
    pack: Path,
    origin_main_sha: str,
    snapshot: Mapping[str, Any],
    adjudication: Mapping[str, Any],
    summary: Mapping[str, Any],
    census: Mapping[str, Any],
    raw_exchanges: tuple[Mapping[str, Any], ...],
) -> dict[str, Any]:
    if str(origin_main_sha or "").strip() != EXPECTED_ORIGIN_MAIN_SHA:
        raise P08ReadOnlyClosurePersistError("ORIGIN_MAIN_SHA_MISMATCH")
    assert_no_secrets_in_payload_v1(snapshot)
    assert_no_secrets_in_payload_v1(adjudication)
    assert_no_secrets_in_payload_v1(summary)
    assert_no_secrets_in_payload_v1(census)
    for raw in raw_exchanges:
        assert_no_secrets_in_payload_v1(raw)
    pack.mkdir(parents=True, exist_ok=False)
    write_json_v1(pack / "GET_SNAPSHOT.sanitized.json", snapshot)
    write_json_v1(pack / "ADJUDICATION.json", adjudication)
    write_json_v1(pack / "SUMMARY.json", summary)
    write_json_v1(pack / "CENSUS.json", census)
    write_json_v1(
        pack / "claims.json",
        {
            **CLAIMS,
            "OWNER_GO": OWNER_GO,
            "THIS_SLICE": THIS_SLICE,
            "WORKPACKAGE_ID": WORKPACKAGE_ID,
            "AUTHORIZED_OPERATION": AUTHORIZED_OPERATION,
            "AUTHORIZED_ENDPOINTS": list(AUTHORIZED_ENDPOINTS),
            "TARGET_INSTRUMENT_ID": TARGET_INSTRUMENT_ID,
            "TARGET_INST_TYPE": TARGET_INST_TYPE,
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
    manifest_files = [
        "GET_SNAPSHOT.sanitized.json",
        "ADJUDICATION.json",
        "SUMMARY.json",
        "CENSUS.json",
        "claims.json",
    ]
    used_names: set[str] = set()
    for raw in raw_exchanges:
        role = str(raw.get("GET_ROLE") or "")
        name = _RAW_FILENAMES.get(role)
        if name is None:
            raise P08ReadOnlyClosurePersistError("RAW_GET_ROLE_INVALID")
        if name in used_names:
            raise P08ReadOnlyClosurePersistError("RAW_GET_ROLE_DUPLICATE")
        used_names.add(name)
        write_json_v1(pack / name, raw)
        manifest_files.append(name)
    write_manifest_v1(pack, tuple(manifest_files))
    verified = verify_manifest_v1(pack)
    if int(verified.get("MANIFEST_VERIFY_RC", 1)) != 0:
        raise P08ReadOnlyClosurePersistError("MANIFEST_VERIFY_FAILED")
    return verified
