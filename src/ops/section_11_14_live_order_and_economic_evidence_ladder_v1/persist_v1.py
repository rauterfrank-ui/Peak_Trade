"""Persist sanitized offline §11.14 documents with reused manifest helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.evidence_v1 import (
    verify_manifest_v1,
    write_json_v1,
    write_manifest_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    EVIDENCE_DIRNAME,
    EXPECTED_ORIGIN_MAIN_SHA,
    CANONICAL_EVIDENCE_RUN_ID,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.contract_v1 import (
    Section1114OfflineSurfaceError,
    assert_contract_invariants_v1,
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
            raise Section1114OfflineSurfaceError("SECRET_IN_EVIDENCE")
        if any(lowered.startswith(prefix) for prefix in _SECRET_VALUE_PREFIXES):
            raise Section1114OfflineSurfaceError("SECRET_IN_EVIDENCE")

    _walk(payload)


def persist_offline_surface_pack_v1(
    *,
    pack: Path,
    origin_main_sha: str,
    documents: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    if str(origin_main_sha or "").strip() != EXPECTED_ORIGIN_MAIN_SHA:
        raise Section1114OfflineSurfaceError("ORIGIN_MAIN_SHA_MISMATCH")
    if not documents:
        raise Section1114OfflineSurfaceError("PERSIST_DOCUMENTS_MISSING")
    assert_contract_invariants_v1()
    for name, payload in documents.items():
        if "/" in name or name.startswith("."):
            raise Section1114OfflineSurfaceError("PERSIST_FILENAME_INVALID")
        assert_no_secrets_in_payload_v1(payload)
        if name in {"claims.json", "SUMMARY.json"}:
            assert_contract_invariants_v1(payload)
    pack.mkdir(parents=True, exist_ok=True)
    for name, payload in documents.items():
        write_json_v1(pack / name, payload)
    names = sorted(
        child.name
        for child in pack.iterdir()
        if child.is_file() and child.name != "MANIFEST.sha256"
    )
    write_manifest_v1(pack, tuple(names))
    verified = verify_manifest_v1(pack)
    if int(verified.get("MANIFEST_VERIFY_RC", 1)) != 0:
        raise Section1114OfflineSurfaceError("MANIFEST_VERIFY_FAILED")
    return verified


def canonical_evidence_pack_path_v1(*, repo_root: Path) -> Path:
    return repo_root / "evidence" / "ops" / EVIDENCE_DIRNAME / CANONICAL_EVIDENCE_RUN_ID
