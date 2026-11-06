"""Preflight run binding against canonical ConstraintMatrix (BWP-0C)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.evaluation.golden_vectors.constraints.errors import GvefConstraintMatrixError
from src.evaluation.golden_vectors.constraints.matrix_loader_v1 import (
    load_canonical_constraint_matrix_v1,
)
from src.evaluation.golden_vectors.contracts.enums import CurrentReachabilityVerdict
from src.evaluation.golden_vectors.contracts.models import BoundaryResultV1, RunManifestV1

COMPONENT_ID = "gvef.pre_constraint_gate_v1"


@dataclass(frozen=True)
class ConstraintMatrixPreGateV1:
    """Evaluate run manifest against sealed constraint matrix rows (AUTHORITY=NONE)."""

    repo_root: Path | None = None

    def evaluate_pre(self, run: RunManifestV1) -> tuple[bool, list[BoundaryResultV1]]:
        matrix = load_canonical_constraint_matrix_v1(repo_root=self.repo_root)
        if run.constraint_matrix_version != matrix.matrix_version:
            raise GvefConstraintMatrixError(
                "run constraint_matrix_version does not match canonical matrix",
                field="constraint_matrix_version",
            )
        if run.constraint_matrix_digest != matrix.matrix_digest:
            return False, [
                BoundaryResultV1(
                    edge_id="CONSTRAINT_MATRIX_DIGEST",
                    pass_=False,
                    producer=COMPONENT_ID,
                    consumer="generic_runner",
                    current_verdict="VIOLATED_CURRENT",
                )
            ]

        boundaries: list[BoundaryResultV1] = []
        all_ok = True
        for row in matrix.rows:
            ok = (
                row.PRODUCTIVE_REACHABILITY is CurrentReachabilityVerdict.PROVEN_CURRENT
                and row.REQUIRED_CURRENT_VERDICT is CurrentReachabilityVerdict.PROVEN_CURRENT
            )
            all_ok = all_ok and ok
            boundaries.append(
                BoundaryResultV1(
                    edge_id=row.SIGNAL_EDGE,
                    pass_=ok,
                    producer=COMPONENT_ID,
                    consumer=row.CONSUMER,
                    current_verdict=(
                        CurrentReachabilityVerdict.PROVEN_CURRENT.value
                        if ok
                        else row.PRODUCTIVE_REACHABILITY.value
                    ),
                )
            )
        return all_ok, boundaries
