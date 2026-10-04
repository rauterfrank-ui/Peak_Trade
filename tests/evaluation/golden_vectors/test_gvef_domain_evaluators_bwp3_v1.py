"""BWP-3 / BWP-3-RU domain evaluator tests."""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from src.evaluation.golden_vectors.contracts.enums import (
    DomainVerdict,
    EvaluationDomain,
    FailureClassification,
    FanOutEvaluationClass,
)
from src.evaluation.golden_vectors.contracts.models import contract_digest_hex
from src.evaluation.golden_vectors.evaluators._result_v1 import reproof_for_failure
from src.evaluation.golden_vectors.evaluators.productive_trading_path_v1 import (
    BWP_ID as PTP_BWP_ID,
    PRIMARY_FAILURE_CLASS as PTP_FAILURE,
    PRODUCTIVE_TRADING_PATH_EVALUATOR_ID,
    ProductiveTradingPathEvaluatorV1,
)
from src.evaluation.golden_vectors.evaluators.ptp_owners_v1 import PTP_STAGE_ORDER, PTP_STAGE_OWNERS
from src.evaluation.golden_vectors.evaluators.ranking_universe_v1 import (
    BWP_ID as RU_BWP_ID,
    PRIMARY_FAILURE_CLASS as RU_FAILURE,
    RANKING_UNIVERSE_EVALUATOR_ID,
    RankingUniverseEvaluatorV1,
)
from src.evaluation.golden_vectors.evaluators.ru_owners_v1 import CAP2_3_SELECTION_OWNER
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
    parsed_replay,
    ptp_context,
    ptp_stage_entries,
    ru_context,
    ru_entries,
    replay_trace,
)
from tests.evaluation.golden_vectors.runner_fixtures_v1 import parsed_context


def _runner_deps(evaluator):
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


@pytest.fixture
def ptp_ev() -> ProductiveTradingPathEvaluatorV1:
    return ProductiveTradingPathEvaluatorV1()


@pytest.fixture
def ru_ev() -> RankingUniverseEvaluatorV1:
    return RankingUniverseEvaluatorV1()


class TestPtpContract:
    def test_evaluator_identity(self, ptp_ev: ProductiveTradingPathEvaluatorV1) -> None:
        assert ptp_ev.evaluator_id == PRODUCTIVE_TRADING_PATH_EVALUATOR_ID
        assert PTP_BWP_ID == "BWP-3"
        assert PTP_FAILURE is FailureClassification.INVARIANT_FAILURE
        assert (
            reproof_for_failure(PTP_FAILURE) is FanOutEvaluationClass.DOWNSTREAM_IMPACT_EVALUATION
        )

    def test_valid_synthetic_pass(self, ptp_ev: ProductiveTradingPathEvaluatorV1) -> None:
        ctx = ptp_context(synthetic=True)
        replay = ctx.replay_trace
        result = ptp_ev.evaluate_baseline(context=ctx, replay=replay)
        assert result.verdict is DomainVerdict.PASS
        assert result.domain is EvaluationDomain.PRODUCTIVE_TRADING_PATH
        assert result.semantic_digest_deltas["evidence_source_class"] == "MECHANISM_TEST_EVIDENCE"

    def test_stage_order_edges(self, ptp_ev: ProductiveTradingPathEvaluatorV1) -> None:
        ctx = ptp_context(synthetic=True)
        result = ptp_ev.evaluate_baseline(context=ctx, replay=ctx.replay_trace)
        edge_ids = [b.edge_id for b in result.boundary_results]
        for i in range(len(PTP_STAGE_ORDER) - 1):
            assert f"{PTP_STAGE_ORDER[i]}->{PTP_STAGE_ORDER[i + 1]}" in edge_ids

    @pytest.mark.parametrize(
        "idx",
        range(len(PTP_STAGE_ORDER) - 1),
        ids=[
            f"edge_{PTP_STAGE_ORDER[i]}_{PTP_STAGE_ORDER[i + 1]}"
            for i in range(len(PTP_STAGE_ORDER) - 1)
        ],
    )
    def test_stage_precedence(self, ptp_ev: ProductiveTradingPathEvaluatorV1, idx: int) -> None:
        assert PTP_STAGE_ORDER[idx] != PTP_STAGE_ORDER[idx + 1]

    def test_missing_stage_fails(self, ptp_ev: ProductiveTradingPathEvaluatorV1) -> None:
        ctx = ptp_context(synthetic=True, stages=PTP_STAGE_ORDER[:5])
        result = ptp_ev.evaluate_baseline(context=ctx, replay=ctx.replay_trace)
        assert result.verdict is DomainVerdict.FAIL
        assert result.failure_classification is FailureClassification.INVARIANT_FAILURE

    def test_reordered_stage_fails(self, ptp_ev: ProductiveTradingPathEvaluatorV1) -> None:
        order = list(PTP_STAGE_ORDER)
        order[0], order[1] = order[1], order[0]
        ctx = ptp_context(synthetic=True, stages=tuple(order))
        result = ptp_ev.evaluate_baseline(context=ctx, replay=ctx.replay_trace)
        assert result.failure_classification is FailureClassification.INVARIANT_FAILURE

    def test_owner_mismatch_fails(self, ptp_ev: ProductiveTradingPathEvaluatorV1) -> None:
        entries = ptp_stage_entries(synthetic=True)
        entries[0]["owner"] = "wrong_owner"
        ctx = ptp_context(synthetic=True)
        replay = parsed_replay(entries)
        result = ptp_ev.evaluate_baseline(context=ctx, replay=replay)
        assert result.failure_classification is FailureClassification.INVARIANT_FAILURE

    def test_run_id_mismatch_fails(self, ptp_ev: ProductiveTradingPathEvaluatorV1) -> None:
        entries = ptp_stage_entries(synthetic=True, run_id="other-run")
        ctx = ptp_context(synthetic=True)
        result = ptp_ev.evaluate_baseline(context=ctx, replay=parsed_replay(entries))
        assert result.failure_classification is FailureClassification.INVARIANT_FAILURE

    def test_pre_external_not_terminal_fails(
        self, ptp_ev: ProductiveTradingPathEvaluatorV1
    ) -> None:
        stages = tuple(list(PTP_STAGE_ORDER)[:-1])
        ctx = ptp_context(synthetic=True, stages=stages)
        result = ptp_ev.evaluate_baseline(context=ctx, replay=ctx.replay_trace)
        assert result.failure_classification is FailureClassification.INVARIANT_FAILURE

    def test_live_post_crossing_fails(self, ptp_ev: ProductiveTradingPathEvaluatorV1) -> None:
        entries = ptp_stage_entries(synthetic=True)
        entries.append(
            {
                "kind": "ptp_stage",
                "run_id": entries[0]["run_id"],
                "stage": "LIVE_POST",
                "owner": "forbidden",
            }
        )
        ctx = ptp_context(synthetic=True)
        result = ptp_ev.evaluate_baseline(context=ctx, replay=parsed_replay(entries))
        assert result.failure_classification is FailureClassification.INVARIANT_FAILURE

    def test_deterministic_repeat(self, ptp_ev: ProductiveTradingPathEvaluatorV1) -> None:
        ctx = ptp_context(synthetic=True)
        r1 = ptp_ev.evaluate_baseline(context=ctx, replay=ctx.replay_trace)
        r2 = ptp_ev.evaluate_baseline(context=ctx, replay=ctx.replay_trace)
        assert contract_digest_hex(r1) == contract_digest_hex(r2)

    def test_owner_matrix_constants(self) -> None:
        for stage in PTP_STAGE_ORDER:
            assert stage in PTP_STAGE_OWNERS
            assert PTP_STAGE_OWNERS[stage]


class TestRuContract:
    def test_ru_evaluator_identity(self, ru_ev: RankingUniverseEvaluatorV1) -> None:
        assert ru_ev.evaluator_id == RANKING_UNIVERSE_EVALUATOR_ID
        assert RU_BWP_ID == "BWP-3-RU"
        assert RU_FAILURE is FailureClassification.AUTHORITY_FAILURE

    def test_valid_ru_pass(self, ru_ev: RankingUniverseEvaluatorV1) -> None:
        ctx = ru_context()
        replay = ctx.replay_trace
        base = ru_ev.evaluate_baseline(context=ctx, replay=replay)
        cand = ru_ev.evaluate_candidate(context=ctx, replay=replay)
        assert base.verdict is DomainVerdict.PASS
        assert cand.verdict is DomainVerdict.PASS
        assert cand.semantic_digest_deltas is not None
        assert "ranking_delta_manifest" in cand.semantic_digest_deltas

    def test_ru_digest_separate_from_selection(self, ru_ev: RankingUniverseEvaluatorV1) -> None:
        ctx = ru_context()
        replay = ctx.replay_trace
        ru_ev.evaluate_baseline(context=ctx, replay=replay)
        ru_ev.evaluate_candidate(context=ctx, replay=replay)
        dig = ru_ev.protected_digests_candidate(context=ctx)
        assert dig.ranking_universe.digest_hex != dig.selection.digest_hex

    def test_ru_change_does_not_change_selection_digest(
        self, ru_ev: RankingUniverseEvaluatorV1
    ) -> None:
        ctx = ru_context(baseline=["A"], candidate=["B"])
        replay = ctx.replay_trace
        sel_before = ctx.protected_digest_baseline.selection.digest_hex
        ru_ev.evaluate_baseline(context=ctx, replay=replay)
        ru_ev.evaluate_candidate(context=ctx, replay=replay)
        dig = ru_ev.protected_digests_candidate(context=ctx)
        assert dig.selection.digest_hex == sel_before

    @pytest.mark.parametrize(
        "entry_key,entry_val",
        [
            ("selection_mutation", True),
            ("claims_cap23_ownership", True),
            ("selected_future_write", {"id": "x"}),
            ("binding_mutation", True),
            ("collapse_ru_selection_digest", True),
        ],
    )
    def test_authority_violations_fail(
        self,
        ru_ev: RankingUniverseEvaluatorV1,
        entry_key: str,
        entry_val: object,
    ) -> None:
        ctx = ru_context()
        entries = ru_entries(baseline=["A"], candidate=["A"])
        entries[0][entry_key] = entry_val
        replay = parsed_replay(entries)
        result = ru_ev.evaluate_baseline(context=ctx, replay=replay)
        assert result.verdict is DomainVerdict.FAIL
        assert result.failure_classification is FailureClassification.AUTHORITY_FAILURE
        assert reproof_for_failure(RU_FAILURE) is FanOutEvaluationClass.DOWNSTREAM_IMPACT_EVALUATION

    def test_cap23_owner_reference(self) -> None:
        assert "CAPABILITY_2_3" in CAP2_3_SELECTION_OWNER

    def test_ru_deterministic_repeat(self, ru_ev: RankingUniverseEvaluatorV1) -> None:
        ctx = ru_context()
        replay = ctx.replay_trace
        ru_ev.evaluate_baseline(context=ctx, replay=replay)
        r1 = ru_ev.evaluate_candidate(context=ctx, replay=replay)
        ru_ev2 = RankingUniverseEvaluatorV1()
        ru_ev2.evaluate_baseline(context=ctx, replay=replay)
        r2 = ru_ev2.evaluate_candidate(context=ctx, replay=replay)
        assert contract_digest_hex(r1) == contract_digest_hex(r2)


class TestRunnerIntegration:
    def test_ptp_through_runner(self) -> None:
        ctx = ptp_context(synthetic=True)
        record = GenericRunnerV1().execute(
            GvefRunRequestV1(ctx), _runner_deps(ProductiveTradingPathEvaluatorV1())
        )
        assert record.state is RunnerState.REGISTERED
        assert evidence_complete(record)

    def test_ru_through_runner(self) -> None:
        ctx = ru_context()
        record = GenericRunnerV1().execute(
            GvefRunRequestV1(ctx), _runner_deps(RankingUniverseEvaluatorV1())
        )
        assert record.state is RunnerState.REGISTERED

    def test_failed_evaluator_blocks_evidence_complete(self) -> None:
        ctx = ptp_context(synthetic=True, stages=PTP_STAGE_ORDER[:3])
        record = GenericRunnerV1().execute(
            GvefRunRequestV1(ctx), _runner_deps(ProductiveTradingPathEvaluatorV1())
        )
        assert record.state is RunnerState.FAILED
        assert not evidence_complete(record)
        assert record.fan_out_evaluation_class is FanOutEvaluationClass.DOWNSTREAM_IMPACT_EVALUATION

    def test_ptp_determinism_25x(self) -> None:
        runner = GenericRunnerV1()
        ctx = ptp_context(synthetic=True)
        digests: set[str] = set()
        for _ in range(25):
            record = runner.execute(
                GvefRunRequestV1(ctx), _runner_deps(ProductiveTradingPathEvaluatorV1())
            )
            digests.add(record.protected_output_digest or "")
        assert len(digests) == 1

    def test_ru_determinism_25x(self) -> None:
        runner = GenericRunnerV1()
        ctx = ru_context()
        digests: set[str] = set()
        for _ in range(25):
            record = runner.execute(
                GvefRunRequestV1(ctx), _runner_deps(RankingUniverseEvaluatorV1())
            )
            digests.add(record.protected_output_digest or "")
        assert len(digests) == 1


FORBIDDEN = (
    "full_core_live_path_composition_root_v1",
    "checkout_independent_credential",
    "optimization_proposal_governance_ingress_v1",
    "single_selected_future_policy_v1.persistence",
    "exchange",
)


def test_gvef_tree_forbidden_imports() -> None:
    root = Path("src/evaluation/golden_vectors")
    violations: list[str] = []
    for path in root.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    for frag in FORBIDDEN:
                        if frag in alias.name and "evaluators" in str(path):
                            if frag == "exchange" and "golden_vectors" in alias.name:
                                continue
                            violations.append(f"{path}:{alias.name}")
            elif isinstance(node, ast.ImportFrom) and node.module:
                for frag in FORBIDDEN:
                    if frag in node.module:
                        violations.append(f"{path}:{node.module}")
    assert violations == []


def test_bwp2_stub_still_runs() -> None:
    from src.evaluation.golden_vectors.runner.deterministic_stubs_v1 import (
        DeterministicDomainEvaluatorV1,
    )

    record = GenericRunnerV1().execute(
        GvefRunRequestV1(parsed_context()), _runner_deps(DeterministicDomainEvaluatorV1())
    )
    assert record.state is RunnerState.REGISTERED
