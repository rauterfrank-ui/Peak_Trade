"""Non-secret provenance and secret-hygiene for Treasury Phase-1 records."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

from src.ops.treasury_phase_1_offline_contracts_v1.constants_v1 import (
    CANONICAL_SERIALIZATION_VERSION,
    FORBIDDEN_SECRET_FIELD_MARKERS,
)
from src.ops.treasury_phase_1_offline_contracts_v1.errors_v1 import TreasurySecretHygieneError
from src.ops.treasury_phase_1_offline_contracts_v1.models_v1 import TreasuryIntentRecordV1


def _fold_field_name(name: str) -> str:
    return str(name or "").strip().lower().replace("-", "").replace("_", "")


def _looks_like_secret_field(name: str) -> bool:
    folded = _fold_field_name(name)
    if not folded:
        return False
    forbidden = {_fold_field_name(marker) for marker in FORBIDDEN_SECRET_FIELD_MARKERS}
    return folded in forbidden


def assert_no_secret_fields_v1(
    payload: Mapping[str, Any] | list[Any] | tuple[Any, ...] | Any,
) -> None:
    if isinstance(payload, Mapping):
        for key, value in payload.items():
            if _looks_like_secret_field(str(key)):
                raise TreasurySecretHygieneError(f"SECRET_FIELD_DENIED:{key}")
            assert_no_secret_fields_v1(value)
        return
    if isinstance(payload, (list, tuple)):
        for item in payload:
            assert_no_secret_fields_v1(item)


def canonical_dumps_for_hash_v1(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def evidence_hash_v1(payload: Mapping[str, Any]) -> str:
    material = {
        "canonical_serialization_version": CANONICAL_SERIALIZATION_VERSION,
        "payload": {key: value for key, value in payload.items() if key != "evidence_hash"},
    }
    assert_no_secret_fields_v1(material)
    return hashlib.sha256(canonical_dumps_for_hash_v1(material).encode("utf-8")).hexdigest()


def evidence_hash_for_record_v1(record: TreasuryIntentRecordV1) -> str:
    from src.ops.treasury_phase_1_offline_contracts_v1.models_v1 import intent_record_to_mapping

    payload = intent_record_to_mapping(record)
    return evidence_hash_v1(payload)
