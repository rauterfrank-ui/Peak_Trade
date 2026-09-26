"""Explicit promotion-to-evidence admission gate (fail-closed; no invented authority)."""

from __future__ import annotations

import json
from pathlib import Path

from src.governance.master_v2_double_play_evidence_input_plane_p1_authority_contracts_and_schemas_v1.models_v1 import (
    EvidenceProducerFamilyV1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p5_producer_productive_ingress_v1.constants_v1 import (
    PROMOTION_ADMISSION_CONFIG,
)
from src.governance.master_v2_double_play_evidence_input_plane_p5_producer_productive_ingress_v1.models_v1 import (
    PromotionAdmissionEntryV1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p5_producer_productive_ingress_v1.reason_codes_v1 import (
    ProducerIngressFailureCodeV1,
)
from src.meta.learning_loop.contract_safety_v1 import is_valid_sha256_hex


def load_schema_binding_dispositions_v1(
    repo_root: Path | None = None,
) -> tuple[dict[str, object], ...]:
    root = repo_root or Path(__file__).resolve().parents[3]
    path = root / PROMOTION_ADMISSION_CONFIG
    if not path.is_file():
        return ()
    payload = json.loads(path.read_text(encoding="utf-8"))
    raw = payload.get("schema_binding_dispositions", ())
    if not isinstance(raw, list):
        return ()
    return tuple(dict(item) for item in raw if isinstance(item, dict))


def load_promotion_admissions_v1(
    repo_root: Path | None = None,
) -> tuple[PromotionAdmissionEntryV1, ...]:
    root = repo_root or Path(__file__).resolve().parents[3]
    path = root / PROMOTION_ADMISSION_CONFIG
    if not path.is_file():
        return ()
    payload = json.loads(path.read_text(encoding="utf-8"))
    entries: list[PromotionAdmissionEntryV1] = []
    for raw in payload.get("entries", ()):
        digest = str(raw.get("source_content_digest", ""))
        if not is_valid_sha256_hex(digest):
            continue
        entries.append(
            PromotionAdmissionEntryV1(
                producer_family=EvidenceProducerFamilyV1(str(raw["producer_family"])),
                source_artifact_schema=str(raw["source_artifact_schema"]),
                source_content_digest=digest,
                promoted_evidence_kind=str(raw["promoted_evidence_kind"]),
                promotion_record_id=str(raw["promotion_record_id"]),
            )
        )
    return tuple(entries)


def lookup_promotion_admission_v1(
    *,
    producer_family: EvidenceProducerFamilyV1,
    source_artifact_schema: str,
    source_content_digest: str,
    promoted_evidence_kind: str,
    admissions: tuple[PromotionAdmissionEntryV1, ...],
    schema_bindings: tuple[dict[str, object], ...] | None = None,
) -> tuple[bool, str | None]:
    if not is_valid_sha256_hex(source_content_digest):
        return False, ProducerIngressFailureCodeV1.ARTIFACT_MALFORMED.value
    for entry in admissions:
        if (
            entry.producer_family == producer_family
            and entry.source_artifact_schema == source_artifact_schema
            and entry.source_content_digest == source_content_digest
            and entry.promoted_evidence_kind == promoted_evidence_kind
        ):
            return True, None
    bindings = schema_bindings if schema_bindings is not None else ()
    for disposition in bindings:
        if disposition.get("enabled") is not True:
            continue
        if str(disposition.get("producer_family")) != producer_family.value:
            continue
        if str(disposition.get("promoted_evidence_kind")) != promoted_evidence_kind:
            continue
        if str(disposition.get("nearest_current_source_schema")) != source_artifact_schema:
            continue
        return True, None
    return False, ProducerIngressFailureCodeV1.PROMOTION_ADMISSION_ABSENT.value
