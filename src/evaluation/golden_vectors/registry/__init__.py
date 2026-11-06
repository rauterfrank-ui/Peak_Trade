"""GVEF registry components."""

from src.evaluation.golden_vectors.registry.evidence_registry_v1 import (
    COMPONENT_ID as EVIDENCE_REGISTRY_COMPONENT_ID,
    GvefEvidenceRegistryV1,
)

__all__ = ["GvefEvidenceRegistryV1", "EVIDENCE_REGISTRY_COMPONENT_ID"]
