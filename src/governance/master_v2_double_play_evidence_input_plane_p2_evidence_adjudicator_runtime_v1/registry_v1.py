"""Registered producer/type/version admission (fail closed)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from src.governance.master_v2_double_play_evidence_input_plane_p1_authority_contracts_and_schemas_v1.models_v1 import (
    BoundedL6EvidenceKindV1,
    EvidenceProducerFamilyV1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p2_evidence_adjudicator_runtime_v1.constants_v1 import (
    PRODUCER_REGISTRY_CONFIG,
)
from src.governance.master_v2_double_play_evidence_input_plane_p2_evidence_adjudicator_runtime_v1.models_v1 import (
    EvidenceIntakeRecordV1,
    RegisteredProducerEntryV1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p2_evidence_adjudicator_runtime_v1.reason_codes_v1 import (
    AdjudicationIntakeFailureCodeV1,
)


def _parse_entry(raw: dict[str, object]) -> RegisteredProducerEntryV1:
    return RegisteredProducerEntryV1(
        producer_id=str(raw["producer_id"]),
        producer_version=str(raw["producer_version"]),
        producer_family=EvidenceProducerFamilyV1(str(raw["producer_family"])),
        evidence_kind=BoundedL6EvidenceKindV1(str(raw["evidence_kind"])),
        evidence_type_version=str(raw["evidence_type_version"]),
    )


def load_producer_registry_v1(
    repo_root: Path | None = None,
) -> tuple[RegisteredProducerEntryV1, ...]:
    root = repo_root or Path(__file__).resolve().parents[3]
    path = root / PRODUCER_REGISTRY_CONFIG
    payload = json.loads(path.read_text(encoding="utf-8"))
    entries = payload.get("entries") or []
    return tuple(_parse_entry(dict(e)) for e in entries)


def lookup_registered_producer_v1(
    intake: EvidenceIntakeRecordV1,
    registry: Iterable[RegisteredProducerEntryV1],
) -> tuple[RegisteredProducerEntryV1 | None, tuple[str, ...]]:
    matches = [
        e
        for e in registry
        if e.producer_id == intake.producer_id
        and e.producer_version == intake.producer_version
        and e.evidence_type_version == intake.evidence_type_version
    ]
    if not matches:
        id_matches = [e for e in registry if e.producer_id == intake.producer_id]
        if not id_matches:
            return None, (AdjudicationIntakeFailureCodeV1.PRODUCER_UNREGISTERED.value,)
        version_matches = [e for e in id_matches if e.producer_version == intake.producer_version]
        if not version_matches:
            return None, (AdjudicationIntakeFailureCodeV1.PRODUCER_VERSION_UNREGISTERED.value,)
        return None, (AdjudicationIntakeFailureCodeV1.EVIDENCE_TYPE_VERSION_UNREGISTERED.value,)
    entry = matches[0]
    failures: list[str] = []
    if entry.producer_family != intake.producer_family:
        failures.append(AdjudicationIntakeFailureCodeV1.PRODUCER_FAMILY_REGISTRY_MISMATCH.value)
    if entry.evidence_kind != intake.evidence_kind:
        failures.append(AdjudicationIntakeFailureCodeV1.EVIDENCE_KIND_REGISTRY_MISMATCH.value)
    if failures:
        return None, tuple(failures)
    return entry, ()
