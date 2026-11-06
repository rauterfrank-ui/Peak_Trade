"""Bind an actually archived measured research execution to a SelfLearning vector.

Read-only additive adapter. The existing evaluator checks the reference artifact,
not profitability, stability, natural provenance or productive authorization.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Mapping

from src.evaluation.golden_vectors.contracts.models import ReplayTraceV1, VectorManifestV1
from src.evaluation.golden_vectors.contracts.serialization import sha256_hex
from src.experiments.canonical_advanced_search_v1 import canonical_record_payload_v1
from src.experiments.canonical_native_research_session_v1 import NativeResearchExecutionArchiveV1
from src.experiments.canonical_search_candidate_research_execution_v1 import (
    ExecutedSearchResearchV1,
    build_research_execution_gvef_reference_v1,
)


class MeasuredLearningReferenceError(ValueError):
    """A vector cannot silently use another measured population or source class."""


@dataclass(frozen=True)
class MeasuredLearningReferenceV1:
    executed: ExecutedSearchResearchV1
    learning_artifact: Mapping[str, Any]
    replay_trace: ReplayTraceV1


def load_measured_learning_reference_v1(
    *,
    archive: NativeResearchExecutionArchiveV1,
    artifact_id: str,
    vector: VectorManifestV1,
    run_id: str,
) -> MeasuredLearningReferenceV1:
    """Verify archive/measurement/owner contracts before constructing a float-free trace.

    The caller explicitly binds its run/corpus context. Protected semantic digests
    are never invented here, and the original numeric execution remains available
    to the existing later Meta consumer.
    """
    if vector.population_selector.selector_id != "measured_native_research_execution_v1":
        raise MeasuredLearningReferenceError("MEASURED_RESEARCH_POPULATION_REQUIRED")
    if set(vector.invariant_ids) != {"sl.no_productive_writeback", "sl.baseline_candidate_bound"}:
        raise MeasuredLearningReferenceError("SELF_LEARNING_REFERENCE_INVARIANTS_REQUIRED")
    # This corpus names a repository-backed artifact, not an arbitrary external
    # locator sharing the same basename. Check the supplied store, without
    # resolving/reading the provenance path as a second data source.
    locator = PurePosixPath(vector.provenance.ref)
    repo = Path(__file__).resolve().parents[4]
    if locator.is_absolute() or any(part in {".", ".."} for part in locator.parts):
        raise MeasuredLearningReferenceError("REPOSITORY_ARCHIVE_REFERENCE_REQUIRED")
    if (repo / vector.provenance.ref).resolve() != (
        archive.root / (artifact_id + ".json")
    ).resolve():
        raise MeasuredLearningReferenceError("VECTOR_ARCHIVE_LOCATION_MISMATCH")
    executed = archive.get(artifact_id)
    reference = build_research_execution_gvef_reference_v1(executed, artifact_ref="execution.json")
    artifact = canonical_record_payload_v1(reference.learning_artifact)
    if vector.population_selector.binding_digest != artifact["payload_sha256"]:
        raise MeasuredLearningReferenceError("VECTOR_MEASURED_POPULATION_DIGEST_MISMATCH")
    if (
        artifact["declared_evidence_source_class"] != "TEST_ONLY_SYNTHETIC"
        or vector.provenance.source != "TEST_ONLY_SYNTHETIC"
    ):
        raise MeasuredLearningReferenceError("EXPLICIT_SYNTHETIC_REFERENCE_CLASS_REQUIRED")
    if not vector.provenance.ref.endswith("/" + artifact_id + ".json"):
        raise MeasuredLearningReferenceError("VECTOR_ARCHIVE_REFERENCE_MISMATCH")
    entries = [
        {
            "kind": "self_learning",
            "run_id": run_id,
            "learning_artifact": artifact,
            "measured_archive_artifact_id": artifact_id,
            "vector_id": vector.vector_id,
            "productive_writeback": False,
            "auto_promotion": False,
            "mutate_productive_parameters": False,
        }
    ]
    trace = ReplayTraceV1.model_validate(
        {
            "trace_schema_version": "1.0.0",
            "trace_digest": sha256_hex(entries),
            "entries": entries,
        }
    )
    return MeasuredLearningReferenceV1(executed, reference.learning_artifact, trace)
