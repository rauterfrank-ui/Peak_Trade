"""Offline-only serializer/parser for the §11.14 handoff vacancy schema.

Does not persist to a productive Live path. Does not join a writer or
reader. Does not GET. Does not POST.
"""

from __future__ import annotations

import json
from typing import Any, Mapping

from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.contract_v1 import (
    Section1114OfflineSurfaceError,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_schema_v1 import (
    CONTEMPORANEOUS_PROVENANCE_CLASS,
    FORBIDDEN_PROVENANCE_CLASSES,
    HANDOFF_DOCUMENT_CLASS,
    REQUIRED_HANDOFF_FIELDS,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_owner_vacancy_contract_v1 import (
    PROPOSED_FIRST_OWNER_ID,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_required_field_contract_v1 import (
    POS_SEMANTICS,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_validators_v1 import (
    evaluate_handoff_proof_bundle_v1,
    parse_handoff_pos_v1,
    validate_handoff_completeness_v1,
)


def serialize_handoff_offline_v1(payload: Mapping[str, Any]) -> str:
    document = dict(payload or {})
    if str(document.get("DOCUMENT_CLASS") or "").strip() != HANDOFF_DOCUMENT_CLASS:
        document["DOCUMENT_CLASS"] = HANDOFF_DOCUMENT_CLASS
    completeness = validate_handoff_completeness_v1(document)
    if completeness["COMPLETE"] is not True:
        raise Section1114OfflineSurfaceError(str(completeness["REASON"]))
    if parse_handoff_pos_v1(document.get("pos")) is None:
        raise Section1114OfflineSurfaceError("MISSING_POS")
    provenance = str(document.get("provenance_class") or "").strip()
    if provenance in FORBIDDEN_PROVENANCE_CLASSES:
        raise Section1114OfflineSurfaceError("FORBIDDEN_PROVENANCE")
    owner = str(document.get("claimed_owner") or "").strip()
    if owner and owner not in {PROPOSED_FIRST_OWNER_ID, "NONE"}:
        raise Section1114OfflineSurfaceError("WRONG_OWNER")
    document["POS_SEMANTICS"] = POS_SEMANTICS
    document["OFFLINE_ONLY"] = True
    document["PRODUCTIVE_WRITER_JOIN"] = False
    return json.dumps(document, sort_keys=True, separators=(",", ":"))


def deserialize_handoff_offline_v1(raw: str) -> dict[str, Any]:
    try:
        payload = json.loads(raw)
    except (TypeError, json.JSONDecodeError) as exc:
        raise Section1114OfflineSurfaceError("HANDOFF_JSON_PARSE_FAILURE") from exc
    if not isinstance(payload, dict):
        raise Section1114OfflineSurfaceError("HANDOFF_JSON_NOT_OBJECT")
    missing = [
        name for name in REQUIRED_HANDOFF_FIELDS if str(payload.get(name) or "").strip() == ""
    ]
    if missing:
        raise Section1114OfflineSurfaceError("MISSING_REQUIRED_HANDOFF_FIELDS")
    if str(payload.get("pos") or "").strip() == "":
        raise Section1114OfflineSurfaceError("MISSING_POS")
    if parse_handoff_pos_v1(payload.get("pos")) is None:
        raise Section1114OfflineSurfaceError("CORRUPT_POS")
    provenance = str(payload.get("provenance_class") or "").strip()
    if provenance in FORBIDDEN_PROVENANCE_CLASSES:
        raise Section1114OfflineSurfaceError("FORBIDDEN_PROVENANCE")
    if provenance and provenance != CONTEMPORANEOUS_PROVENANCE_CLASS:
        raise Section1114OfflineSurfaceError("NO_SYNTHETIC_PRE_RESTART_PROVENANCE")
    return dict(payload)


def evaluate_offline_handoff_roundtrip_v1(
    *,
    payload: Mapping[str, Any],
    source_kind: str,
    claimed_owner: str | None = None,
    contemporaneous_capture_proven: bool | None = None,
    provenance_class: str | None = None,
) -> dict[str, Any]:
    encoded = serialize_handoff_offline_v1(payload)
    decoded = deserialize_handoff_offline_v1(encoded)
    proof = evaluate_handoff_proof_bundle_v1(
        handoff=decoded,
        source_kind=source_kind,
        claimed_owner=claimed_owner,
        contemporaneous_capture_proven=contemporaneous_capture_proven,
        provenance_class=provenance_class,
    )
    return {
        "encoded": encoded,
        "decoded": decoded,
        "proof": proof,
        "OFFLINE_ONLY": True,
        "PRODUCTIVE_WRITER_JOIN": False,
        "PRODUCTIVE_READER_JOIN": False,
    }
