"""Real archived numerical research binds to an independently registered SL vector."""

from copy import deepcopy
import json
from pathlib import Path

import pytest

from src.evaluation.golden_vectors.contracts.validation import (
    parse_domain_evaluation_context_v1,
    parse_vector_manifest_v1,
)
from src.evaluation.golden_vectors.corpus.registry_v1 import VectorCorpusRegistryV1
from src.evaluation.golden_vectors.corpus.gate_v1 import VectorCorpusIntegrityGateV1
from src.evaluation.golden_vectors.evaluators.self_learning_v1 import SelfLearningEvaluatorV1
from src.evaluation.golden_vectors.integration.measured_learning_reference_v1 import (
    MeasuredLearningReferenceError,
    load_measured_learning_reference_v1,
)
from src.evaluation.golden_vectors.runner.generic_runner_v1 import (
    GenericRunnerV1,
    GvefRunRequestV1,
    evidence_complete,
)
from src.evaluation.golden_vectors.runner.states import RunnerState
from src.experiments.canonical_advanced_search_v1 import canonical_record_payload_v1
from src.experiments.canonical_native_research_session_v1 import NativeResearchExecutionArchiveV1
from src.experiments.canonical_research_result_to_meta_input_v1 import (
    build_meta_learning_from_research_results_v1,
)
from src.experiments.canonical_meta_learning_v1 import canonical_meta_learning_policy_v1
from tests.evaluation.golden_vectors.evaluator_fixtures_v1 import sl_context
from tests.evaluation.golden_vectors.test_gvef_domain_evaluators_bwp456_v1 import _deps

ROOT = Path(__file__).resolve().parents[3]
CORPUS = "config/evaluation/golden_vectors/measured_learning_reference_v1"
RESEARCH = (
    ROOT
    / "docs/ops/evidence/durable_research_and_measured_mi_return_restoration_v1_2026_11_04/artifacts/research"
)


def _bound():
    registry = VectorCorpusRegistryV1.default()
    entry = registry.load_entry(CORPUS)
    key = (RESEARCH / "session_artifact_id.txt").read_text().strip()
    archive = NativeResearchExecutionArchiveV1(RESEARCH / "archive")
    ctx = sl_context()
    loaded = load_measured_learning_reference_v1(
        archive=archive, artifact_id=key, vector=entry.vectors[0], run_id=ctx.run_manifest.run_id
    )
    raw = ctx.model_dump(mode="json", by_alias=True)
    raw["corpus_identity"] = entry.manifest.model_dump(mode="json")
    raw["run_manifest"]["corpus_manifest_ref"] = CORPUS
    raw["replay_trace"] = loaded.replay_trace.model_dump(mode="json")
    return registry, parse_domain_evaluation_context_v1(raw), loaded, key, entry.vectors[0]


def test_bound_measured_vector_runs_existing_gvef_and_preserves_exact_later_meta(tmp_path):
    registry, context, loaded, _, _ = _bound()
    dependencies = _deps(SelfLearningEvaluatorV1())
    dependencies.corpus_gate = VectorCorpusIntegrityGateV1(registry=registry)
    record = GenericRunnerV1().execute(GvefRunRequestV1(context), dependencies)
    assert record.state is RunnerState.REGISTERED
    assert evidence_complete(record)
    assert (
        record.candidate_result.semantic_digest_deltas["evidence_source_class"]
        == "MECHANISM_TEST_EVIDENCE"
    )
    assert record.candidate_result.metrics[0].metric_id == "sl.artifact_digest"
    assert len(record.candidate_result.metrics) == 1
    later = build_meta_learning_from_research_results_v1(
        [loaded.executed.next_meta_input],
        created_at="2026-08-18T22:00:00Z",
        policy=canonical_meta_learning_policy_v1(),
    )
    assert canonical_record_payload_v1(later) == json.loads(
        (RESEARCH / "later_meta_fresh_process.json").read_text()
    )
    (tmp_path / "measured_vector_result.json").write_text(
        json.dumps(
            dict(
                corpus_digest=context.corpus_identity.corpus_digest,
                state=record.state.value,
                baseline=record.baseline_result.model_dump(mode="json", by_alias=True),
                candidate=record.candidate_result.model_dump(mode="json", by_alias=True),
                later_meta=canonical_record_payload_v1(later),
                source_authentication=False,
                productive_authority=False,
                quality_evaluation_scope="Reference binding only; existing synthetic metadata gates, not numerical-quality acceptance",
            ),
            indent=2,
        )
        + "\n"
    )


@pytest.mark.parametrize(
    "change",
    ["population", "class", "archive_ref", "same_id_wrong_location", "invariants", "selector"],
)
def test_wrong_population_or_provenance_is_rejected(change):
    _, context, _, key, vector = _bound()
    raw = deepcopy(vector.model_dump(mode="json"))
    if change == "population":
        raw["population_selector"]["binding_digest"] = "0" * 64
    elif change == "class":
        raw["provenance"]["source"] = "SEALED_EXISTING_EVIDENCE"
    elif change == "archive_ref":
        raw["provenance"]["ref"] = "unrelated/archive.json"
    elif change == "same_id_wrong_location":
        raw["provenance"]["ref"] = "unrelated/" + key + ".json"
    elif change == "invariants":
        raw["invariant_ids"] = ["ptp.pre_external_terminal"]
    elif change == "selector":
        raw["population_selector"]["selector_id"] = "other.population"
    with pytest.raises(MeasuredLearningReferenceError):
        load_measured_learning_reference_v1(
            archive=NativeResearchExecutionArchiveV1(RESEARCH / "archive"),
            artifact_id=key,
            vector=parse_vector_manifest_v1(raw),
            run_id=context.run_manifest.run_id,
        )
