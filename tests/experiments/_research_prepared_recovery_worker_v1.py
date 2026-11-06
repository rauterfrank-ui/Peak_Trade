"""Fresh process, retained requests only; engine is prohibited during recovery."""

import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace
from src.experiments.canonical_experiment_memory_store_v1 import CanonicalExperimentMemoryStoreV1
from src.experiments.canonical_failure_memory_store_v1 import CanonicalFailureMemoryStoreV1
from src.experiments.canonical_reality_gap_store_persist_v1 import CanonicalRealityGapStoreV1
from src.experiments.canonical_native_research_session_v1 import NativeResearchExecutionArchiveV1
from src.experiments import canonical_research_prepared_execution_v1 as recovery
from src.experiments import canonical_native_research_measurements_v1 as native


def main():
    root, packet, boundary = sys.argv[1:]
    root = Path(root)
    ctx = SimpleNamespace(
        experiment_memory_store=CanonicalExperimentMemoryStoreV1(root / "memory"),
        failure_memory_store=CanonicalFailureMemoryStoreV1(root / "failures"),
        reality_gap_store=CanonicalRealityGapStoreV1(root / "gaps"),
    )
    archive = NativeResearchExecutionArchiveV1(root / "archive")

    def forbidden(*args, **kwargs):
        raise AssertionError("recovery must not enter native engine")

    native.measure_native_research_candidate_v1 = forbidden
    if boundary in {"experiment", "failure", "gap", "archive"}:
        owner = {
            "experiment": ctx.experiment_memory_store,
            "failure": ctx.failure_memory_store,
            "gap": ctx.reality_gap_store,
            "archive": archive,
        }[boundary]
        actual = owner.append

        def killed(*args, **kwargs):
            actual(*args, **kwargs)
            os._exit(79)

        owner.append = killed
    elif boundary == "ack":
        actual = recovery.publish_v1

        def killed(path, body):
            actual(path, body)
            if path.name == "ack.json":
                os._exit(79)

        recovery.publish_v1 = killed
    with recovery.research_step_lease_v1(ctx):
        result = recovery.finish_prepared_v1(Path(packet), archive, ctx)
    print(
        "RESULT="
        + json.dumps(
            {
                "status": result.status,
                "artifact_id": result.artifact_id,
                "created_at": result.execution.next_meta_input.research_loop_record["created_at"],
            }
        )
    )


if __name__ == "__main__":
    main()
