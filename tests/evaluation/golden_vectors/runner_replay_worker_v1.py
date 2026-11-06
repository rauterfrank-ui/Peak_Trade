"""Subprocess worker: emit protected runner digest JSON (cross-process determinism)."""

from __future__ import annotations

import json
import os
import sys

from src.evaluation.golden_vectors.runner.deterministic_stubs_v1 import (
    DeterministicComparatorV1,
    DeterministicDeltaBuilderV1,
    DeterministicDomainEvaluatorV1,
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
from tests.evaluation.golden_vectors.runner_fixtures_v1 import parsed_context


def main() -> int:
    ctx = parsed_context()
    deps = GvefRunnerDependenciesV1(
        pre_gate=DeterministicPreGateV1(),
        post_gate=DeterministicPostGateV1(),
        replay_adapter=DeterministicReplayAdapterV1(),
        evaluator=DeterministicDomainEvaluatorV1(),
        comparator=DeterministicComparatorV1(),
        delta_builder=DeterministicDeltaBuilderV1(),
        evidence_builder=DeterministicEvidenceBuilderV1(),
        registry=InMemoryEvidenceRegistryV1(),
    )
    record = GenericRunnerV1().execute(GvefRunRequestV1(ctx), deps)
    out = {
        "protected_output_digest": record.protected_output_digest,
        "state_sequence": [s.value for s in record.state_history],
        "pythonhashseed": os.environ.get("PYTHONHASHSEED", ""),
        "tz": os.environ.get("TZ", ""),
    }
    sys.stdout.write(json.dumps(out, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
