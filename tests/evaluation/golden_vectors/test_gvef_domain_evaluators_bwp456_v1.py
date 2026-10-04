"""BWP-4 / BWP-5 / BWP-6 domain evaluator tests."""

from __future__ import annotations

import json
import os
import subprocess

import pytest

from src.evaluation.golden_vectors.contracts.enums import (
    DomainVerdict,
    EvaluationDomain,
    FailureClassification,
    FanOutEvaluationClass,
)
from src.evaluation.golden_vectors.contracts.models import contract_digest_hex
from src.evaluation.golden_vectors.evaluators.market_intelligence_v1 import (
    BWP_ID as MI_BWP_ID,
    PRIMARY_FAILURE_CLASS as MI_FAILURE,
    REPROOF_CLASS as MI_REPROOF,
    MarketIntelligenceEvaluatorV1,
)
from src.evaluation.golden_vectors.evaluators.optimization_universe_v1 import (
    BWP_ID as OPT_BWP_ID,
    PRIMARY_FAILURE_CLASS as OPT_FAILURE,
    REPROOF_CLASS as OPT_REPROOF,
    OptimizationUniverseEvaluatorV1,
)
from src.evaluation.golden_vectors.evaluators.self_learning_v1 import (
    BWP_ID as SL_BWP_ID,
    PRIMARY_FAILURE_CLASS as SL_FAILURE,
    REPROOF_CLASS as SL_REPROOF,
    SelfLearningEvaluatorV1,
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
    evidence_complete,
)
from src.evaluation.golden_vectors.runner.states import RunnerState
from tests.evaluation.golden_vectors.evaluator_fixtures_v1 import (
    mi_context,
    mi_entries,
    opt_context,
    opt_entries,
    parsed_replay,
    sl_context,
    sl_entries,
)


def _deps(evaluator):
    return GvefRunnerDependenciesV1(
        pre_gate=DeterministicPreGateV1(),
        post_gate=DeterministicPostGateV1(),
        replay_adapter=DeterministicReplayAdapterV1(),
        evaluator=evaluator,
        comparator=DeterministicComparatorV1(),
        delta_builder=DeterministicDeltaBuilderV1(),
        evidence_builder=DeterministicEvidenceBuilderV1(),
        registry=InMemoryEvidenceRegistryV1(),
    )


class TestBwp4Optimization:
    def test_mapping_and_contract(self) -> None:
        assert OPT_BWP_ID == "BWP-4"
        assert OPT_FAILURE is FailureClassification.INVARIANT_FAILURE
        assert OPT_REPROOF is FanOutEvaluationClass.LOCAL_EVALUATION

    def test_valid_pass(self) -> None:
        ev = OptimizationUniverseEvaluatorV1()
        ctx = opt_context()
        replay = ctx.replay_trace
        assert ev.evaluate_baseline(context=ctx, replay=replay).verdict is DomainVerdict.PASS
        cand = ev.evaluate_candidate(context=ctx, replay=replay)
        assert cand.verdict is DomainVerdict.PASS
        assert cand.domain is EvaluationDomain.OPTIMIZATION_UNIVERSE

    def test_missing_evidence_fails_invariant(self) -> None:
        ev = OptimizationUniverseEvaluatorV1()
        ctx = opt_context()
        result = ev.evaluate_baseline(context=ctx, replay=parsed_replay([]))
        assert result.failure_classification is FailureClassification.INVARIANT_FAILURE

    @pytest.mark.parametrize(
        "key",
        ["productive_apply", "claims_mv2_authority", "selection_mutation", "auto_promotion"],
    )
    def test_invariant_violations(self, key: str) -> None:
        ev = OptimizationUniverseEvaluatorV1()
        ctx = opt_context()
        entries = opt_entries()
        entries[0][key] = True
        result = ev.evaluate_baseline(context=ctx, replay=parsed_replay(entries))
        assert result.failure_classification is FailureClassification.INVARIANT_FAILURE

    def test_deterministic_repeat(self) -> None:
        ev = OptimizationUniverseEvaluatorV1()
        ctx = opt_context()
        replay = ctx.replay_trace
        ev.evaluate_baseline(context=ctx, replay=replay)
        r1 = ev.evaluate_candidate(context=ctx, replay=replay)
        ev2 = OptimizationUniverseEvaluatorV1()
        ev2.evaluate_baseline(context=ctx, replay=replay)
        r2 = ev2.evaluate_candidate(context=ctx, replay=replay)
        assert contract_digest_hex(r1) == contract_digest_hex(r2)

    def test_runner_local_reproof_on_fail(self) -> None:
        ctx = opt_context()
        ctx_dict = ctx.model_dump(mode="json", by_alias=True)
        ctx_dict["replay_trace"]["entries"] = []
        from src.evaluation.golden_vectors.contracts.validation import (
            parse_domain_evaluation_context_v1,
        )

        bad = parse_domain_evaluation_context_v1(ctx_dict)
        record = GenericRunnerV1().execute(
            GvefRunRequestV1(bad), _deps(OptimizationUniverseEvaluatorV1())
        )
        assert record.state is RunnerState.FAILED
        assert not evidence_complete(record)
        assert record.fan_out_evaluation_class is FanOutEvaluationClass.LOCAL_EVALUATION

    def test_runner_success(self) -> None:
        record = GenericRunnerV1().execute(
            GvefRunRequestV1(opt_context()), _deps(OptimizationUniverseEvaluatorV1())
        )
        assert record.state is RunnerState.REGISTERED

    def test_determinism_25x(self) -> None:
        runner = GenericRunnerV1()
        ctx = opt_context()
        digests: set[str] = set()
        for _ in range(25):
            record = runner.execute(GvefRunRequestV1(ctx), _deps(OptimizationUniverseEvaluatorV1()))
            digests.add(record.protected_output_digest or "")
        assert len(digests) == 1


class TestBwp5SelfLearning:
    def test_mapping_and_contract(self) -> None:
        assert SL_BWP_ID == "BWP-5"
        assert SL_FAILURE is FailureClassification.AUTHORITY_FAILURE
        assert SL_REPROOF is FanOutEvaluationClass.LOCAL_EVALUATION

    def test_valid_pass(self) -> None:
        ev = SelfLearningEvaluatorV1()
        ctx = sl_context()
        replay = ctx.replay_trace
        assert ev.evaluate_baseline(context=ctx, replay=replay).verdict is DomainVerdict.PASS
        assert ev.evaluate_candidate(context=ctx, replay=replay).verdict is DomainVerdict.PASS

    @pytest.mark.parametrize(
        "key",
        [
            "productive_writeback",
            "productive_config_write",
            "claims_trading_authority",
            "selection_mutation",
            "auto_promotion",
            "mutate_productive_parameters",
        ],
    )
    def test_authority_violations(self, key: str) -> None:
        ev = SelfLearningEvaluatorV1()
        ctx = sl_context()
        entries = sl_entries()
        entries[0][key] = True
        result = ev.evaluate_baseline(context=ctx, replay=parsed_replay(entries))
        assert result.failure_classification is FailureClassification.AUTHORITY_FAILURE
        assert ev.failure_fan_out(SL_FAILURE) is FanOutEvaluationClass.LOCAL_EVALUATION

    def test_runner_authority_fail_local_reproof(self) -> None:
        entries = sl_entries()
        entries[0]["productive_writeback"] = True
        ctx = sl_context()
        ctx_dict = ctx.model_dump(mode="json", by_alias=True)
        ctx_dict["replay_trace"] = {
            "trace_schema_version": "1.0.0",
            "trace_digest": "a" * 64,
            "entries": entries,
        }
        from src.evaluation.golden_vectors.contracts.validation import (
            parse_domain_evaluation_context_v1,
        )

        bad = parse_domain_evaluation_context_v1(ctx_dict)
        record = GenericRunnerV1().execute(GvefRunRequestV1(bad), _deps(SelfLearningEvaluatorV1()))
        assert record.failure_classification is FailureClassification.AUTHORITY_FAILURE
        assert record.fan_out_evaluation_class is FanOutEvaluationClass.LOCAL_EVALUATION

    def test_determinism_25x(self) -> None:
        runner = GenericRunnerV1()
        ctx = sl_context()
        digests: set[str] = set()
        for _ in range(25):
            record = runner.execute(GvefRunRequestV1(ctx), _deps(SelfLearningEvaluatorV1()))
            digests.add(record.protected_output_digest or "")
        assert len(digests) == 1


class TestBwp6MarketIntelligence:
    def test_mapping_and_contract(self) -> None:
        assert MI_BWP_ID == "BWP-6"
        assert MI_FAILURE is FailureClassification.INVARIANT_FAILURE
        assert MI_REPROOF is FanOutEvaluationClass.LOCAL_EVALUATION

    def test_valid_pass(self) -> None:
        ev = MarketIntelligenceEvaluatorV1()
        ctx = mi_context()
        replay = ctx.replay_trace
        assert ev.evaluate_baseline(context=ctx, replay=replay).verdict is DomainVerdict.PASS
        assert ev.evaluate_candidate(context=ctx, replay=replay).verdict is DomainVerdict.PASS

    @pytest.mark.parametrize(
        "key",
        [
            "selection_mutation",
            "binding_mutation",
            "productive_trading_intent_authority",
            "venue_post",
            "materialize_productive_state",
        ],
    )
    def test_invariant_authority_flags(self, key: str) -> None:
        ev = MarketIntelligenceEvaluatorV1()
        ctx = mi_context()
        entries = mi_entries()
        entries[0][key] = True
        result = ev.evaluate_baseline(context=ctx, replay=parsed_replay(entries))
        assert result.failure_classification is FailureClassification.INVARIANT_FAILURE

    def test_leakage_fails(self) -> None:
        ev = MarketIntelligenceEvaluatorV1()
        ctx = mi_context(
            baseline={
                "TEST_ONLY_SYNTHETIC": True,
                "freshness_token": "x",
                "causality_proof_present": True,
                "leakage_detected": True,
            }
        )
        result = ev.evaluate_baseline(context=ctx, replay=ctx.replay_trace)
        assert result.failure_classification is FailureClassification.INVARIANT_FAILURE

    def test_determinism_25x(self) -> None:
        runner = GenericRunnerV1()
        ctx = mi_context()
        digests: set[str] = set()
        for _ in range(25):
            record = runner.execute(GvefRunRequestV1(ctx), _deps(MarketIntelligenceEvaluatorV1()))
            digests.add(record.protected_output_digest or "")
        assert len(digests) == 1


def test_bwp456_cross_process_opt_determinism() -> None:
    cmd = [
        "./scripts/pt",
        "-m",
        "tests.evaluation.golden_vectors.bwp456_replay_worker_v1",
    ]
    env_a = os.environ.copy()
    env_a["PYTHONHASHSEED"] = "1"
    env_b = os.environ.copy()
    env_b["PYTHONHASHSEED"] = "424242"
    out_a = subprocess.check_output(cmd, env=env_a, text=True)
    out_b = subprocess.check_output(cmd, env=env_b, text=True)
    assert (
        json.loads(out_a)["protected_output_digest"] == json.loads(out_b)["protected_output_digest"]
    )
