"""Full result repeatability and retained evidence at the actual GVEF boundary."""

from __future__ import annotations

import pytest

from src.evaluation.golden_vectors.contracts.enums import FailureClassification
from src.evaluation.golden_vectors.contracts.models import MetricResultV1
from src.evaluation.golden_vectors.registry.evidence_registry_v1 import GvefEvidenceRegistryV1
from src.evaluation.golden_vectors.registry.errors import GvefRegistryError
from src.evaluation.golden_vectors.runner.deterministic_stubs_v1 import (
    DeterministicDomainEvaluatorV1,
)
from src.evaluation.golden_vectors.runner.generic_runner_v1 import GenericRunnerV1, GvefRunRequestV1
from src.evaluation.golden_vectors.runner.states import RunnerState
from tests.evaluation.golden_vectors.promotion_fixtures_v1 import valid_evidence_bundle
from tests.evaluation.golden_vectors.runner_fixtures_v1 import parsed_context
from tests.evaluation.golden_vectors.test_gvef_generic_runner_v1 import _deps


@pytest.mark.parametrize("field", ["metrics", "evidence_refs", "semantic_digest_deltas"])
def test_candidate_repeat_must_match_full_first_result(field: str) -> None:
    class DriftingCandidate(DeterministicDomainEvaluatorV1):
        def evaluate_candidate(self, **kwargs):
            result = super().evaluate_candidate(**kwargs)
            if self.candidate_calls == 2:
                if field == "metrics":
                    result.metrics.append(MetricResultV1(metric_id="unexpected", value=99))
                elif field == "evidence_refs":
                    result.evidence_refs.append("evidence/different")
                else:
                    result = result.model_copy(
                        update={"semantic_digest_deltas": {"different": "changed"}}
                    )
            return result

    registry = GvefEvidenceRegistryV1()
    record = GenericRunnerV1().execute(
        GvefRunRequestV1(parsed_context()), _deps(evaluator=DriftingCandidate(), registry=registry)
    )
    assert record.state is RunnerState.FAILED
    assert record.failure_classification is FailureClassification.NON_DETERMINISM
    assert registry.registry_manifest()["entry_count"] == 0


@pytest.mark.parametrize("target", ["baseline", "candidate"])
def test_second_candidate_cannot_mutate_first_results(target: str) -> None:
    class MutatingEvaluator(DeterministicDomainEvaluatorV1):
        def evaluate_baseline(self, **kwargs):
            result = super().evaluate_baseline(**kwargs)
            if self.baseline_calls == 1:
                self.first_baseline = result
            return result

        def evaluate_candidate(self, **kwargs):
            result = super().evaluate_candidate(**kwargs)
            if self.candidate_calls == 1:
                self.first_candidate = result
            else:
                getattr(self, f"first_{target}").evidence_refs.append("evidence/late-mutation")
            return result

    registry = GvefEvidenceRegistryV1()
    record = GenericRunnerV1().execute(
        GvefRunRequestV1(parsed_context()), _deps(evaluator=MutatingEvaluator(), registry=registry)
    )
    assert record.state is RunnerState.FAILED
    assert registry.registry_manifest()["entry_count"] == 0


@pytest.mark.parametrize("verify_repeat", [True, False])
@pytest.mark.parametrize("hook", ["comparator", "evidence_builder"])
def test_downstream_hook_cannot_change_retained_result(hook: str, verify_repeat: bool) -> None:
    class RetainingEvaluator(DeterministicDomainEvaluatorV1):
        def evaluate_candidate(self, **kwargs):
            result = super().evaluate_candidate(**kwargs)
            if self.candidate_calls == 1:
                self.first_candidate = result
            return result

    evaluator = RetainingEvaluator()
    registry = GvefEvidenceRegistryV1()
    deps = _deps(evaluator=evaluator, registry=registry)
    wrapped = getattr(deps, hook)

    class MutatingHook:
        def compare(self, **kwargs):
            evaluator.first_candidate.evidence_refs.append("evidence/comparator-mutation")
            return wrapped.compare(**kwargs)

        def build(self, **kwargs):
            evaluator.first_candidate.evidence_refs.append("evidence/builder-mutation")
            return wrapped.build(**kwargs)

    setattr(deps, hook, MutatingHook())
    record = GenericRunnerV1().execute(
        GvefRunRequestV1(parsed_context()), deps, verify_deterministic_replay=verify_repeat
    )
    assert record.state is RunnerState.FAILED
    assert record.failure_classification is FailureClassification.INVARIANT_FAILURE
    assert registry.registry_manifest()["entry_count"] == 0


def test_registry_readback_is_independent_of_caller_and_other_readers() -> None:
    bundle = valid_evidence_bundle()
    registry = GvefEvidenceRegistryV1()
    registry.register(bundle)
    first = registry.get(bundle.run_id)
    assert first is not None
    original = first.model_dump(mode="json", by_alias=True)
    first.seed_set.append(999)
    bundle.seed_set.append(888)
    second = registry.get(bundle.run_id)
    assert second is not None
    assert second.model_dump(mode="json", by_alias=True) == original


def test_registry_rejects_corrupt_stored_content() -> None:
    bundle = valid_evidence_bundle()
    registry = GvefEvidenceRegistryV1()
    registry.register(bundle)
    registry._entries[bundle.run_id].seed_set.append(999)
    with pytest.raises(GvefRegistryError, match="evidence_digest"):
        registry.get(bundle.run_id)
