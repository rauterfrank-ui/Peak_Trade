"""GVEF corpus integrity layer (BWP-7)."""

from __future__ import annotations

from src.evaluation.golden_vectors.corpus.digest_v1 import (
    corpus_identity_digest_hex,
    vector_identity_digest_hex,
)
from src.evaluation.golden_vectors.corpus.errors import GvefCorpusDriftError
from src.evaluation.golden_vectors.corpus.gate_v1 import (
    CorpusIntegrityGateV1,
    PassThroughCorpusIntegrityGateV1,
    VectorCorpusIntegrityGateV1,
)
from src.evaluation.golden_vectors.corpus.registry_v1 import (
    CANONICAL_CORPUS_ROOT,
    CorpusRegistryEntryV1,
    CorpusValidationResultV1,
    VectorCorpusRegistryV1,
)

__all__ = [
    "CANONICAL_CORPUS_ROOT",
    "CorpusIntegrityGateV1",
    "CorpusRegistryEntryV1",
    "CorpusValidationResultV1",
    "GvefCorpusDriftError",
    "PassThroughCorpusIntegrityGateV1",
    "VectorCorpusIntegrityGateV1",
    "VectorCorpusRegistryV1",
    "corpus_identity_digest_hex",
    "vector_identity_digest_hex",
]
