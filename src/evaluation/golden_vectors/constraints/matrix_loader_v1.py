"""Load and verify canonical GVEF authority signal flow constraint matrix (BWP-0C)."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from src.evaluation.golden_vectors.constraints.digest_v1 import matrix_digest_matches
from src.evaluation.golden_vectors.constraints.errors import GvefConstraintMatrixError
from src.evaluation.golden_vectors.contracts.models import ConstraintMatrixV1
from src.evaluation.golden_vectors.contracts.validation import parse_constraint_matrix_v1

BWP_ID = "BWP-0C"
CANONICAL_MATRIX_REL = (
    "config/evaluation/golden_vectors/authority_signal_flow_constraints/constraint_matrix_v1.json"
)


@lru_cache(maxsize=1)
def load_canonical_constraint_matrix_v1(*, repo_root: Path | None = None) -> ConstraintMatrixV1:
    root = repo_root or Path.cwd()
    path = (root / CANONICAL_MATRIX_REL).resolve()
    if not path.is_file():
        raise GvefConstraintMatrixError(
            f"missing canonical constraint matrix at {CANONICAL_MATRIX_REL}",
            field="constraint_matrix_path",
        )
    matrix = parse_constraint_matrix_v1(json.loads(path.read_text(encoding="utf-8")))
    if not matrix_digest_matches(matrix):
        raise GvefConstraintMatrixError(
            "constraint matrix digest mismatch (CORPUS_DRIFT class for matrix)",
            field="matrix_digest",
        )
    return matrix
