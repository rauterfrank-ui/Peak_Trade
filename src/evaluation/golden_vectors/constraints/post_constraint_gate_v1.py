"""Post-run authority / protected digest verification against constraint matrix (BWP-0C)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.evaluation.golden_vectors.constraints.errors import GvefConstraintMatrixError
from src.evaluation.golden_vectors.constraints.matrix_loader_v1 import (
    load_canonical_constraint_matrix_v1,
)
from src.evaluation.golden_vectors.contracts.models import (
    BoundaryResultV1,
    ProtectedSemanticDigestsV1,
    RunManifestV1,
)

COMPONENT_ID = "gvef.post_constraint_gate_v1"


@dataclass(frozen=True)
class ConstraintMatrixPostGateV1:
    repo_root: Path | None = None

    def evaluate_post(
        self,
        *,
        run: RunManifestV1,
        post_gate_pass_required: bool,
        protected_digests: ProtectedSemanticDigestsV1,
    ) -> tuple[bool, list[BoundaryResultV1]]:
        _ = post_gate_pass_required
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

        from src.evaluation.golden_vectors.digest.errors import GvefProtectedDigestDriftError
        from src.evaluation.golden_vectors.digest.protected_semantic_digest_layer_v1 import (
            enforce_ranking_universe_selection_separation,
        )

        try:
            enforce_ranking_universe_selection_separation(protected_digests)
            separation_ok = True
        except GvefProtectedDigestDriftError:
            separation_ok = False
        boundaries = [
            BoundaryResultV1(
                edge_id="RANKING_UNIVERSE->SELECTION",
                pass_=separation_ok,
                producer=COMPONENT_ID,
                consumer="protected_semantic_digest_layer_v1",
                current_verdict="PROVEN_CURRENT" if separation_ok else "VIOLATED_CURRENT",
            )
        ]
        return separation_ok, boundaries
