"""Deterministic corpus / vector identity digests (reuse BWP-1 canonical JSON)."""

from __future__ import annotations

from src.evaluation.golden_vectors.contracts.models import (
    CorpusManifestV1,
    VectorManifestV1,
    contract_digest_hex,
    contract_to_canonical_mapping,
)
from src.evaluation.golden_vectors.contracts.serialization import sha256_hex

_CORPUS_EXCLUDED = frozenset({"corpus_digest"})


def vector_identity_digest_hex(vector: VectorManifestV1) -> str:
    return contract_digest_hex(vector)


def corpus_semantic_payload(
    manifest: CorpusManifestV1,
    *,
    vector_digests_by_id: dict[str, str],
) -> dict:
    """Semantic corpus identity; ``corpus_digest`` field excluded."""
    base = contract_to_canonical_mapping(manifest)
    for key in _CORPUS_EXCLUDED:
        base.pop(key, None)
    ordered_vectors = []
    for vector_id in manifest.vector_ids:
        if vector_id not in vector_digests_by_id:
            raise KeyError(f"missing vector digest for {vector_id}")
        ordered_vectors.append(
            {"vector_id": vector_id, "vector_digest": vector_digests_by_id[vector_id]}
        )
    base["bound_vector_digests"] = ordered_vectors
    return base


def corpus_identity_digest_hex(
    manifest: CorpusManifestV1,
    *,
    vector_digests_by_id: dict[str, str],
) -> str:
    return sha256_hex(corpus_semantic_payload(manifest, vector_digests_by_id=vector_digests_by_id))


def manifest_digest_matches(
    manifest: CorpusManifestV1,
    *,
    vector_digests_by_id: dict[str, str],
) -> bool:
    return manifest.corpus_digest == corpus_identity_digest_hex(
        manifest, vector_digests_by_id=vector_digests_by_id
    )
