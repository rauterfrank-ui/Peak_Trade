"""Fixtures for BWP-8 promotion adapter tests."""

from __future__ import annotations

from src.evaluation.golden_vectors.contracts.enums import (
    ExternalPromotionStatus,
    FanOutEvaluationClass,
)
from src.evaluation.golden_vectors.contracts.models import EvidenceBundleV1
from src.evaluation.golden_vectors.promotion.promotion_evidence_adapter_v1 import (
    evidence_bundle_semantic_digest,
)
from src.evaluation.golden_vectors.runner.deterministic_stubs_v1 import (
    DeterministicComparatorV1,
    DeterministicDeltaBuilderV1,
    DeterministicEvidenceBuilderV1,
    DeterministicPostGateV1,
    DeterministicPreGateV1,
    DeterministicReplayAdapterV1,
    DeterministicDomainEvaluatorV1,
    InMemoryEvidenceRegistryV1,
)
from src.evaluation.golden_vectors.runner.generic_runner_v1 import (
    GenericRunnerV1,
    GvefRunRequestV1,
    GvefRunnerDependenciesV1,
)
from tests.evaluation.golden_vectors.runner_fixtures_v1 import parsed_context

_HANDOFF_TS = "2026-10-04T09:00:00Z"


def valid_evidence_bundle(*, post_gate_pass: bool = True) -> EvidenceBundleV1:
    if post_gate_pass:
        runner = GenericRunnerV1()
        record = runner.execute(
            GvefRunRequestV1(parsed_context()),
            GvefRunnerDependenciesV1(
                pre_gate=DeterministicPreGateV1(),
                post_gate=DeterministicPostGateV1(should_pass=True),
                replay_adapter=DeterministicReplayAdapterV1(),
                evaluator=DeterministicDomainEvaluatorV1(),
                comparator=DeterministicComparatorV1(),
                delta_builder=DeterministicDeltaBuilderV1(),
                evidence_builder=DeterministicEvidenceBuilderV1(),
                registry=InMemoryEvidenceRegistryV1(),
            ),
        )
        assert record.evidence_bundle is not None
        return record.evidence_bundle
    from tests.evaluation.golden_vectors.runner_fixtures_v1 import parsed_run

    run = parsed_run()
    delta = DeterministicComparatorV1().compare(
        baseline=DeterministicDomainEvaluatorV1().evaluate_baseline(
            context=parsed_context(), replay=parsed_context().replay_trace
        ),
        candidate=DeterministicDomainEvaluatorV1().evaluate_candidate(
            context=parsed_context(), replay=parsed_context().replay_trace
        ),
        baseline_digests=parsed_context().protected_digest_baseline,
        candidate_digests=parsed_context().protected_digest_baseline,
    )[0]
    return DeterministicEvidenceBuilderV1().build(
        run=run,
        delta=delta,
        protected_digests=parsed_context().protected_digest_baseline,
        boundary_results=[],
        post_gate_pass=False,
    )


def adapt_request(**kwargs) -> dict:
    base = {
        "evidence_bundle_ref": "registry/test-run",
        "governance_handoff_timestamp": _HANDOFF_TS,
    }
    base.update(kwargs)
    return base
