"""Canonical GVEF evidence registry — append-only, duplicate fail-closed (BWP-9)."""

from __future__ import annotations

from dataclasses import dataclass, field

from src.evaluation.golden_vectors.contracts.models import EvidenceBundleV1
from src.evaluation.golden_vectors.promotion.promotion_evidence_adapter_v1 import (
    evidence_bundle_semantic_digest,
)
from src.evaluation.golden_vectors.registry.errors import GvefRegistryError

BWP_ID = "BWP-9"
COMPONENT_ID = "gvef.evidence_registry_v1"


@dataclass
class GvefEvidenceRegistryV1:
    """In-memory append-only registry; no promotion or trading authority."""

    fail_next_register: bool = False
    _entries: dict[str, EvidenceBundleV1] = field(default_factory=dict)
    _append_order: list[str] = field(default_factory=list)

    def register(self, bundle: EvidenceBundleV1) -> str:
        if self.fail_next_register:
            raise GvefRegistryError("registry boundary failure")
        expected_digest = evidence_bundle_semantic_digest(bundle)
        if bundle.evidence_digest != expected_digest:
            raise GvefRegistryError("evidence_digest mismatch on register")
        if bundle.run_id in self._entries:
            raise GvefRegistryError("duplicate run_id")
        frozen = EvidenceBundleV1.model_validate(bundle.model_dump(mode="json", by_alias=True))
        self._entries[bundle.run_id] = frozen
        self._append_order.append(bundle.run_id)
        return f"registry/{bundle.run_id}"

    def get(self, run_id: str) -> EvidenceBundleV1 | None:
        return self._entries.get(run_id)

    def registry_manifest(self) -> dict[str, object]:
        return {
            "component_id": COMPONENT_ID,
            "append_only": True,
            "entry_count": len(self._append_order),
            "run_ids": list(self._append_order),
        }
