"""Measured native failures -> exact archived Meta numbers -> selected measured trial.

Controlled research-policy intervention, not market causality or evidence of
independent replications. Explicit seeds are fixed before trials; no same-ID retry.
"""

from dataclasses import replace
import json

from tests.experiments.test_canonical_native_research_session_v1 import measured_session, _step  # noqa: F401 - pytest fixture
from tests.experiments.test_research_preflight_recovery_v1 import _isolated
from src.experiments.canonical_advanced_search_v1 import (
    SearchSpaceV1,
    SearchAxisV1,
    canonical_record_payload_v1,
)
from src.experiments.canonical_robustness_suite_v1 import derive_robustness_policy_digest_v1
from src.experiments.canonical_meta_learning_v1 import canonical_meta_learning_policy_v1
from src.experiments.canonical_research_result_to_meta_input_v1 import (
    build_meta_learning_from_research_results_v1,
)


def test_measured_policy_intervention_changes_next_native_trial_with_unrelated_control(
    measured_session, tmp_path
):
    outputs = {}
    for scenario, collapse, region in [
        ("control", 0.5, 50),
        ("relevant_failure", 100.0, 50),
        ("unrelated_failure", 100.0, 75),
    ]:
        provider, request, archive, seen = _isolated(
            measured_session, tmp_path / scenario / "history", gap=0.01
        )
        policy = dict(provider.context.robustness_policy)
        policy["oos_sharpe_collapse_ratio"] = collapse
        ids = []
        for i, seed in enumerate((55, 56, 57)):
            # Fixed, separately owned planned experiments; prior failed regions
            # must not turn these explicit different scientific seeds into a
            # hidden same-ID retest or a skipped measurement.
            planned, _, _, _ = _isolated(
                measured_session, tmp_path / scenario / f"seed-{seed}", gap=0.01
            )
            provider = planned
            template = replace(provider.context.identity_template, seed=seed)
            p = replace(
                provider,
                context=replace(
                    provider.context,
                    identity_template=template,
                    robustness_policy=policy,
                    created_at=f"2026-08-18T{18 + i:02}:00:00Z",
                ),
            )
            r = replace(
                request,
                identity_template=template,
                seed=seed,
                robustness_policy_digest=derive_robustness_policy_digest_v1(policy),
                created_at=f"2026-08-18T{17 + i:02}:30:00Z",
                search_space=SearchSpaceV1(
                    "native.session.v1",
                    (SearchAxisV1("fast_window", (10,)), SearchAxisV1("slow_window", (region,))),
                ),
            )
            trial = _step(p, r, archive)
            assert trial.status == "EXECUTED_AND_ARCHIVED"
            ids.append(trial.artifact_id)
        # New target owners are empty: only the actual archived Meta path can
        # change the target Search priority, not direct durable Failure filtering.
        target, target_req, _, target_seen = _isolated(
            measured_session, tmp_path / scenario / "target", gap=0.01
        )
        template = replace(target.context.identity_template, seed=200)
        target = replace(
            target,
            context=replace(
                target.context, identity_template=template, created_at="2026-08-18T23:00:00Z"
            ),
        )
        target_req = replace(
            target_req, identity_template=template, seed=200, created_at="2026-08-18T22:30:00Z"
        )
        assert target.context.failure_memory_store.list_records() == []
        next_trial = _step(
            target,
            target_req,
            archive,
            ids=ids,
            meta_created_at="2026-08-18T22:00:00Z",
            meta_policy=canonical_meta_learning_policy_v1(),
        )
        assert len(target_seen) == 1 and target_seen[0].receipt["engine_invocations"] == 4
        selected = next(
            c for c in next_trial.search_record["candidates"] if c["status"] == "PROPOSED"
        )
        assert dict(selected["parameter_region"]) == dict(target_seen[0].receipt["parameters"])
        loaded = archive.get(next_trial.artifact_id)
        later = build_meta_learning_from_research_results_v1(
            [loaded.next_meta_input],
            created_at="2026-08-19T00:00:00Z",
            policy=canonical_meta_learning_policy_v1(),
        )
        original = build_meta_learning_from_research_results_v1(
            [next_trial.execution.next_meta_input],
            created_at="2026-08-19T00:00:00Z",
            policy=canonical_meta_learning_policy_v1(),
        )
        assert canonical_record_payload_v1(later) == canonical_record_payload_v1(original)
        failures = [
            f
            for key in ids
            for f in archive.get(key).next_meta_input.research_loop_record["failure_records"]
        ]
        outputs[scenario] = {
            "selected": dict(selected["parameter_region"]),
            "overfit_failures": sum(f["failure_class"] == "REJECTED_OVERFIT" for f in failures),
            "feedback": canonical_record_payload_v1(next_trial.feedback_record),
            "measured_next": canonical_record_payload_v1(target_seen[0].receipt),
            "later_numeric_meta": canonical_record_payload_v1(later),
            "artifact_id": next_trial.artifact_id,
            "history_artifact_ids": ids,
            "archive_root": str(archive.root),
        }
    assert outputs["control"]["selected"]["slow_window"] == 50
    assert outputs["relevant_failure"]["overfit_failures"] > outputs["control"]["overfit_failures"]
    assert outputs["relevant_failure"]["selected"]["slow_window"] == 100
    assert outputs["unrelated_failure"]["selected"] == outputs["control"]["selected"]
    (tmp_path / "measured_meta_next_trial_witness.json").write_text(
        json.dumps(outputs, indent=2, allow_nan=False) + "\n"
    )
