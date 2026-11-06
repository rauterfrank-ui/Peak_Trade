"""Deterministic constraint matrix identity digests."""

from __future__ import annotations

from src.evaluation.golden_vectors.contracts.models import (
    ConstraintMatrixV1,
    contract_digest_hex,
    contract_to_canonical_mapping,
)
from src.evaluation.golden_vectors.contracts.serialization import sha256_hex

_MATRIX_EXCLUDED = frozenset({"matrix_digest"})


def matrix_semantic_payload(matrix: ConstraintMatrixV1) -> dict:
    payload = contract_to_canonical_mapping(matrix)
    for key in _MATRIX_EXCLUDED:
        payload.pop(key, None)
    return payload


def matrix_identity_digest_hex(matrix: ConstraintMatrixV1) -> str:
    return contract_digest_hex(matrix, exclude_fields=_MATRIX_EXCLUDED)


def matrix_digest_matches(matrix: ConstraintMatrixV1) -> bool:
    return matrix.matrix_digest == matrix_identity_digest_hex(matrix)
