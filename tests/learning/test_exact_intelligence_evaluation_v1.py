"""Actual native evaluator behind byte-bound numeric/source checks, all synthetic."""

from copy import deepcopy

import pytest

from tests.learning.test_intelligence_forecast_measurement_integration_v1 import setup, measure
from tests.evaluation.golden_vectors.evaluator_fixtures_v1 import mi_context, parsed_replay
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.forecast_measurement_integration_v1 import (
    freeze_existing_intelligence_forecast_v1,
    read_calibrated_intelligence_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.exact_intelligence_evaluation_v1 import (
    intelligence_evaluation_bundle_v1,
    evaluate_exact_intelligence_v1 as _evaluate_exact,
)


def evaluate_exact_intelligence_v1(*, context, replay, original_sources_by_label):
    return _evaluate_exact(
        context=context.model_copy(update={"replay_trace": replay}),
        replay=replay,
        original_sources_by_label=original_sources_by_label,
    )


def prepared(tmp_path):
    args, case = setup()
    frozen = freeze_existing_intelligence_forecast_v1(store_root=tmp_path, **args)
    measure(tmp_path, frozen, case)
    packet = read_calibrated_intelligence_v1(store_root=tmp_path, job_key=frozen["job_key"])
    ctx = mi_context()
    entries = [
        {
            "kind": "market_intelligence",
            "label": label,
            "run_id": ctx.run_manifest.run_id,
            "mi_context_bundle": intelligence_evaluation_bundle_v1(packet),
        }
        for label in ("baseline", "candidate")
    ]
    sources = {
        label: {"store_root": tmp_path, "job_key": frozen["job_key"]}
        for label in ("baseline", "candidate")
    }
    return ctx, entries, sources


def test_original_evaluator_runs_with_complete_numeric_bindings(tmp_path):
    ctx, entries, sources = prepared(tmp_path)
    replay = parsed_replay(entries)
    receipt = evaluate_exact_intelligence_v1(
        context=ctx, replay=replay, original_sources_by_label=sources
    )
    assert all(r["verdict"] == "PASS" for r in receipt["native_results"].values())
    assert receipt["economic_quality"] == "NOT_PROVEN"
    assert receipt["governance_disposition"] == "BLOCKED_NO_EXPLICIT_RECEIVER"
    assert receipt == evaluate_exact_intelligence_v1(
        context=ctx, replay=replay, original_sources_by_label=sources
    )


@pytest.mark.parametrize(
    "field",
    [
        "causality_proof_present",
        "causality_proof",
        "freshness_token",
        "numeric_calibration",
        "calibration_readback_digest",
    ],
)
def test_missing_or_replaced_fields_fail_before_native_evaluator(tmp_path, field, monkeypatch):
    from src.evaluation.golden_vectors.evaluators.market_intelligence_v1 import (
        MarketIntelligenceEvaluatorV1,
    )

    ctx, entries, sources = prepared(tmp_path)
    entries = deepcopy(entries)
    entries[0]["mi_context_bundle"].pop(field)

    def forbidden(*args, **kwargs):
        raise AssertionError("NATIVE_EVALUATION_MUST_NOT_RUN")

    monkeypatch.setattr(MarketIntelligenceEvaluatorV1, "evaluate_baseline", forbidden)
    with pytest.raises(ValueError, match="EXACT_MI_BUNDLE_MISMATCH"):
        evaluate_exact_intelligence_v1(
            context=ctx, replay=parsed_replay(entries), original_sources_by_label=sources
        )


def test_native_veto_is_preserved(tmp_path):
    ctx, entries, sources = prepared(tmp_path)
    entries[1]["selection_mutation"] = True
    receipt = evaluate_exact_intelligence_v1(
        context=ctx, replay=parsed_replay(entries), original_sources_by_label=sources
    )
    assert all(r["verdict"] != "PASS" for r in receipt["native_results"].values())
    assert receipt["productive_apply_authorized"] is False


def test_unlabeled_first_match_and_context_substitution_reject(tmp_path):
    ctx, entries, sources = prepared(tmp_path)
    foreign = deepcopy(entries[0])
    foreign.pop("label")
    with pytest.raises(ValueError, match="AMBIGUOUS_MI_ENTRIES"):
        evaluate_exact_intelligence_v1(
            context=ctx,
            replay=parsed_replay([foreign] + entries),
            original_sources_by_label=sources,
        )
    with pytest.raises(ValueError, match="CONTEXT_REPLAY_MISMATCH"):
        _evaluate_exact(
            context=ctx, replay=parsed_replay(entries), original_sources_by_label=sources
        )


def test_numeric_transport_keeps_exact_original_json_values(tmp_path):
    import json

    ctx, entries, sources = prepared(tmp_path)
    transport = entries[0]["mi_context_bundle"]["numeric_calibration"]
    receipt = evaluate_exact_intelligence_v1(
        context=ctx, replay=parsed_replay(entries), original_sources_by_label=sources
    )
    assert transport["codec"] == "exact-json-values-v1"
    assert (
        json.loads(transport["utf8"])
        == receipt["original_numeric_bindings"]["baseline"]["numeric_calibration"]
    )
