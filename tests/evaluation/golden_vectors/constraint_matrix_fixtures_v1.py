"""Canonical BWP-0C constraint matrix fixtures for GVEF tests."""

from __future__ import annotations

from pathlib import Path

from src.evaluation.golden_vectors.constraints.matrix_loader_v1 import (
    load_canonical_constraint_matrix_v1,
)
from src.evaluation.golden_vectors.contracts.models import ConstraintMatrixV1

_REPO_ROOT = Path(__file__).resolve().parents[3]


def canonical_constraint_matrix_v1() -> ConstraintMatrixV1:
    return load_canonical_constraint_matrix_v1(repo_root=_REPO_ROOT)


def canonical_constraint_matrix_dict() -> dict:
    return canonical_constraint_matrix_v1().model_dump(mode="json", by_alias=True)
