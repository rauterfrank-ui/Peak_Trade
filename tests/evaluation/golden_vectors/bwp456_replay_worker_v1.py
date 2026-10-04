"""Cross-process determinism worker for BWP-4 optimization evaluator."""

from __future__ import annotations

import json

from src.evaluation.golden_vectors.evaluators.optimization_universe_v1 import (
    OptimizationUniverseEvaluatorV1,
)
from src.evaluation.golden_vectors.runner.deterministic_stubs_v1 import (
    DeterministicComparatorV1,
    DeterministicDeltaBuilderV1,
    DeterministicEvidenceBuilderV1,
    DeterministicPostGateV1,
    DeterministicPreGateV1,
    DeterministicReplayAdapterV1,
    InMemoryEvidenceRegistryV1,
)
from src.evaluation.golden_vectors.runner.generic_runner_v1 import (
    GenericRunnerV1,
    GvefRunRequestV1,
    GvefRunnerDependenciesV1,
)
from tests.evaluation.golden_vectors.evaluator_fixtures_v1 import opt_context


def main() -> None:
    deps = GvefRunnerDependenciesV1(
        pre_gate=DeterministicPreGateV1(),
        post_gate=DeterministicPostGateV1(),
        replay_adapter=DeterministicReplayAdapterV1(),
        evaluator=OptimizationUniverseEvaluatorV1(),
        comparator=DeterministicComparatorV1(),
        delta_builder=DeterministicDeltaBuilderV1(),
        evidence_builder=DeterministicEvidenceBuilderV1(),
        registry=InMemoryEvidenceRegistryV1(),
    )
    record = GenericRunnerV1().execute(GvefRunRequestV1(opt_context()), deps)
    print(
        json.dumps(
            {
                "protected_output_digest": record.protected_output_digest,
                "state_sequence": [s.value for s in record.state_history],
            }
        )
    )


if __name__ == "__main__":
    main()
