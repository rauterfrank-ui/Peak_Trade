"""Deterministic §11.14 evidence-record primitives for later ladder stages."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    ADMISSIBLE_OFFLINE_SOURCE_KINDS,
    CANONICAL_BASE_SHA,
    CANONICAL_EVIDENCE_RUN_ID,
    EVIDENCE_RECORD_SCHEMA_VERSION,
    IMPLEMENTATION_SHA,
    LADDER_FIELDS,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.contract_v1 import (
    Section1114OfflineSurfaceError,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.hashing_v1 import (
    hashed_record_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.overclaim_guards_v1 import (
    refuse_forbidden_live_source_v1,
)

EVIDENCE_RECORD_KEYS: tuple[str, ...] = (
    "schema_version",
    "ladder_stage",
    "claim_name",
    "claim_value",
    "evidence_class",
    "source_kind",
    "source_path_or_runtime_source",
    "observed_at",
    "persisted_at",
    "canonical_base_sha",
    "implementation_sha",
    "predecessor_claims",
    "provenance",
    "content_hash",
    "adjudication_status",
    "contradiction_status",
    "authority_scope",
)


def build_evidence_record_v1(
    *,
    ladder_stage: str,
    claim_name: str,
    claim_value: Any,
    evidence_class: str,
    source_kind: str,
    source_path_or_runtime_source: str,
    observed_at: str | None,
    predecessor_claims: Sequence[str],
    provenance: str,
    adjudication_status: str,
    contradiction_status: str,
    authority_scope: str,
) -> dict[str, Any]:
    if ladder_stage not in LADDER_FIELDS:
        raise Section1114OfflineSurfaceError(f"UNKNOWN_LADDER_STAGE:{ladder_stage}")
    refuse_forbidden_live_source_v1(field_name=ladder_stage, source_kind=source_kind)
    if claim_value is True:
        allowed_true = {
            "LIVE_EXECUTION_CODE_EXISTS",
            "LIVE_EXECUTION_PATH_REACHABLE",
            "LIVE_PRIVATE_READ_ONLY_PROVEN",
        }
        if ladder_stage not in allowed_true:
            raise Section1114OfflineSurfaceError(
                f"LIVE_FIELD_TRUE_FORBIDDEN_IN_EVIDENCE_RECORD:{claim_name}"
            )
        kind = str(source_kind or "").strip().upper()
        if kind not in ADMISSIBLE_OFFLINE_SOURCE_KINDS:
            raise Section1114OfflineSurfaceError(
                f"LIVE_FIELD_TRUE_SOURCE_NOT_ADMISSIBLE:{kind}:{ladder_stage}"
            )
        if (
            ladder_stage == "LIVE_EXECUTION_PATH_REACHABLE"
            and kind != "GOVERNED_CURRENT_PRIVATE_GET"
        ):
            raise Section1114OfflineSurfaceError(
                f"PATH_REACHABLE_TRUE_SOURCE_NOT_ADMISSIBLE:{kind}"
            )
        if (
            ladder_stage == "LIVE_PRIVATE_READ_ONLY_PROVEN"
            and kind != "GOVERNED_CURRENT_PRIVATE_GET"
        ):
            raise Section1114OfflineSurfaceError(
                f"PRIVATE_READ_ONLY_TRUE_SOURCE_NOT_ADMISSIBLE:{kind}"
            )
    payload: dict[str, Any] = {
        "schema_version": EVIDENCE_RECORD_SCHEMA_VERSION,
        "ladder_stage": ladder_stage,
        "claim_name": claim_name,
        "claim_value": claim_value,
        "evidence_class": evidence_class,
        "source_kind": source_kind,
        "source_path_or_runtime_source": source_path_or_runtime_source,
        "observed_at": observed_at,
        "persisted_at": CANONICAL_EVIDENCE_RUN_ID,
        "canonical_base_sha": CANONICAL_BASE_SHA,
        "implementation_sha": IMPLEMENTATION_SHA,
        "predecessor_claims": list(predecessor_claims),
        "provenance": provenance,
        "adjudication_status": adjudication_status,
        "contradiction_status": contradiction_status,
        "authority_scope": authority_scope,
    }
    record = hashed_record_v1(payload)
    missing = [key for key in EVIDENCE_RECORD_KEYS if key not in record]
    if missing:
        raise Section1114OfflineSurfaceError("EVIDENCE_RECORD_KEYS_MISSING:" + ",".join(missing))
    return record


def assert_evidence_record_keys_v1(record: Mapping[str, Any]) -> None:
    missing = [key for key in EVIDENCE_RECORD_KEYS if key not in record]
    if missing:
        raise Section1114OfflineSurfaceError("EVIDENCE_RECORD_KEYS_MISSING:" + ",".join(missing))
