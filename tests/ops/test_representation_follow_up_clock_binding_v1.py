"""Exact follow-up clocks on native fixtures; verified parent admission is upstream.

These focused helper tests supply the parent contract explicitly. The existing
capture/Meta/follow-up integration test exercises actual parent reconstruction.
"""

from datetime import timedelta
from functools import partial

import pytest

from scripts.ops import run_offline_paired_market_representation_follow_up_v1 as follow
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.forecast_measurement_integration_v1 import (
    _append,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.integration_contracts_v1 import (
    bytes_v1,
    digest_v1,
    instant_v1,
    seal_v1,
)
from tests.ops.test_capture_offline_learning_representation_context_v1 import public_capture
from tests.ops.test_representation_cohort_clock_binding_v1 import _files, _stamp
from tests.learning.test_offline_recorded_market_replay_v1 import (
    market_request,
    seed_frozen_forecast,
    utc,
)

VARIANTS = ("plain", "zero_fraction", "utc_offset_zero")


def _forbidden(*args, **kwargs):
    pytest.fail("A contradictory follow-up clock reached the next consumer or writer")


@pytest.fixture
def case(public_capture, tmp_path, monkeypatch):
    def build(*, context_nanos=0, verified_nanos=0, variant="plain"):
        capture, clock, _, _ = public_capture
        monkeypatch.setattr(follow.representation, "HTTPSConnection", _forbidden)
        monkeypatch.setattr(
            follow.representation, "_utc_now", lambda: _stamp(utc(clock[0]), context_nanos)
        )
        context = follow.representation.capture_representation_context_v1(**capture)
        first = instant_v1(context["as_of"]).replace(minute=0, second=0, microsecond=0)
        first += timedelta(hours=1)
        request = {**market_request(first), "market_identity": context["identity"]}
        store = tmp_path / "store"
        frozen = seed_frozen_forecast(store, context, request)
        verified = _stamp(utc(instant_v1(context["as_of"]) + timedelta(seconds=1)), verified_nanos)
        monkeypatch.setattr(follow.measurement, "_utc_now", lambda: verified)
        archive = follow.cohort.read_captured_mark_archive_v1(capture["mark_archive"])
        schedule = follow.measurement.schedule_recorded_market_measurement_v1(
            store_root=store,
            job_key=frozen["job_key"],
            binding_path=archive.binding_path,
            binding_sha256=archive.binding_sha256,
            repository_sha="a" * 40,
            capture_delay_seconds=60,
        )
        starts = [utc(first + timedelta(hours=3 * i)) for i in range(8)]
        if variant != "plain":
            suffix = "+00:00" if variant == "utc_offset_zero" else "Z"
            starts = [_stamp(value, suffix=suffix) for value in starts]
        parent = {
            "meta_receipt": {
                "exact_content_digest": digest_v1("verified-meta-fixture"),
                "comparison_digest": digest_v1("verified-comparison-fixture"),
            },
            "research_plan": {"plan_identity": "verified-research-plan-fixture"},
            "cohort_plan": {
                "starts_utc": starts,
                "fit_window_count": 6,
                "validation_fraction": 0.25,
                "forecast_context_max_age_seconds": 300,
            },
            "evidence": {
                "target_contract": {
                    k: v for k, v in request.items() if k != "horizon_start_time_utc"
                },
                "evaluated_at_utc": utc(instant_v1(context["as_of"]) - timedelta(seconds=1)),
                "representation_lineage_ref": "verified-representation-lineage-fixture",
                "measurement": {"target": "LOG_RETURN", "delta_b0_minus_b1": 0.01},
            },
        }
        args = dict(
            parent=parent,
            store_root=store,
            seed_job_key=frozen["job_key"],
            seed_context_root=capture["output"],
            next_starts_utc=starts[1:],
            repository_sha="a" * 40,
        )
        inputs = {
            "parent_meta_receipt_digest": parent["meta_receipt"]["exact_content_digest"],
            "parent_research_plan_identity": parent["research_plan"]["plan_identity"],
            "parent_representation_lineage_ref": parent["evidence"]["representation_lineage_ref"],
            "seed_job_key": frozen["job_key"],
            "seed_context_root": str(capture["output"].resolve()),
            "seed_schedule_digest": schedule["exact_content_digest"],
            "starts_utc": [instant_v1(value).isoformat() for value in starts],
            **{
                key: parent["cohort_plan"][key]
                for key in (
                    "fit_window_count",
                    "validation_fraction",
                    "forecast_context_max_age_seconds",
                )
            },
            "repository_sha": "a" * 40,
        }
        with follow._lease(store, follow._campaign_key(frozen["job_key"])) as folder:
            pass
        return dict(
            args=args,
            inputs=inputs,
            folder=folder,
            schedule=schedule,
            context=context,
            frozen=frozen,
            now=verified,
            root=tmp_path,
        )

    return build


def _plan(case, *, declared=None):
    return seal_v1(
        {
            "schema_version": follow.PLAN_SCHEMA,
            "authority": "NONE",
            "inputs": case["inputs"],
            "declared_at_utc": declared or case["now"],
        }
    )


def _answer(case, plan):
    _append(case["folder"] / follow.PLAN_FILE, plan)
    original = case["args"]["parent"]
    campaign = seal_v1(
        {
            "schema_version": follow.cohort.COHORT_SCHEMA,
            "authority": "NONE",
            **{
                k: case["inputs"][k]
                for k in (
                    "seed_job_key",
                    "starts_utc",
                    "fit_window_count",
                    "validation_fraction",
                    "forecast_context_max_age_seconds",
                    "repository_sha",
                )
            },
        }
    )
    result = seal_v1(
        {
            "schema_version": follow.meta.SCHEMA,
            "authority": "NONE",
            "status": "LEARNING_RESEARCH_PLAN_READY",
            "comparison_digest": digest_v1("verified-child-comparison-fixture"),
            "handoff": {
                "evidence": {
                    "measurement": original["evidence"]["measurement"],
                    "comparison_status": "MEASURED_CHRONOLOGICAL_HOLDOUT",
                }
            },
        }
    )
    receipt = follow._follow_up_receipt(original, plan, result)
    _append(case["folder"] / follow.RECEIPT_FILE, receipt)
    child = {"cohort_plan": campaign, "evidence": original["evidence"], "meta_receipt": result}
    return dict(
        folder=case["folder"],
        store_root=case["args"]["store_root"],
        parent=child,
        original_parent=original,
    )


@pytest.mark.parametrize("nanos", [1, 999])
def test_fractional_hour_rejects_before_context_read(case, nanos, monkeypatch):
    c = case()
    args = {**c["args"], "next_starts_utc": list(c["args"]["next_starts_utc"])}
    args["next_starts_utc"][0] = _stamp(args["next_starts_utc"][0], nanos)
    before = _files(c["root"])
    monkeypatch.setattr(
        follow.representation, "read_recorded_representation_context_v1", _forbidden
    )
    with pytest.raises(ValueError, match="^RESEARCH_FOLLOW_UP_WINDOW_CONTRACT_MISMATCH$"):
        follow._declare_follow_up(**args)
    assert _files(c["root"]) == before


@pytest.mark.parametrize("entry", ["fresh", "replay", "answer"])
@pytest.mark.parametrize("nanos", [1, 999])
def test_declaration_cannot_precede_original_schedule_verification(case, entry, nanos, monkeypatch):
    c = case(verified_nanos=nanos)
    earlier = _stamp(c["now"])
    if entry == "answer":
        args = _answer(c, _plan(c, declared=earlier))
        invoke = partial(follow._read_follow_up_answer, **args)
        reason = "RESEARCH_FOLLOW_UP_ORIGINAL_CLOCK_MISMATCH"
        monkeypatch.setattr(follow, "_follow_up_receipt", _forbidden)
    else:
        if entry == "replay":
            _append(c["folder"] / follow.PLAN_FILE, _plan(c, declared=earlier))
        monkeypatch.setattr(follow.measurement, "_utc_now", lambda: earlier)
        monkeypatch.setattr(follow, "_append", _forbidden)
        invoke = partial(follow._declare_follow_up, **c["args"])
        reason = (
            "RESEARCH_FOLLOW_UP_MUST_BE_DECLARED_BEFORE_WINDOW"
            if entry == "fresh"
            else "RESEARCH_FOLLOW_UP_PLAN_CLOCK_MISMATCH"
        )
    before = _files(c["root"])
    with pytest.raises(ValueError, match=f"^{reason}$"):
        invoke()
    assert _files(c["root"]) == before


@pytest.mark.parametrize("entry", ["declaration", "answer"])
@pytest.mark.parametrize("nanos", [1, 999])
def test_truly_later_original_context_is_admitted(case, entry, nanos):
    c = case(context_nanos=nanos)
    c["args"]["parent"]["evidence"]["evaluated_at_utc"] = _stamp(c["context"]["as_of"])
    if entry == "declaration":
        result = follow._declare_follow_up(**c["args"])
        assert result == _plan(c)
    else:
        args = _answer(c, _plan(c))
        before = _files(c["root"])
        result = follow._read_follow_up_answer(**args)
        assert result["receipt"]["productive_apply_authorized"] is False
        assert result["receipt"]["independent_quality_proven"] is False
        assert _files(c["root"]) == before


@pytest.mark.parametrize("entry", ["declaration", "answer"])
@pytest.mark.parametrize("variant", VARIANTS)
def test_equivalent_hours_and_equal_verification_declaration_preserve_packets(case, entry, variant):
    c = case(variant=variant)
    if entry == "declaration":
        plan = follow._declare_follow_up(**c["args"])
        assert plan == _plan(c)
        before = _files(c["root"])
        assert follow._declare_follow_up(**c["args"]) == plan
    else:
        args = _answer(c, _plan(c))
        before = _files(c["root"])
        assert follow._read_follow_up_answer(**args)["receipt"] == follow._follow_up_receipt(
            c["args"]["parent"], _plan(c), args["parent"]["meta_receipt"]
        )
    assert _files(c["root"]) == before


@pytest.mark.parametrize("entry", ["declaration", "answer"])
@pytest.mark.parametrize("nanos", [0, 1])
def test_equal_or_future_parent_cutoff_stays_inadmissible(case, entry, nanos):
    c = case()
    c["args"]["parent"]["evidence"]["evaluated_at_utc"] = _stamp(c["context"]["as_of"], nanos)
    if entry == "declaration":
        invoke = partial(follow._declare_follow_up, **c["args"])
        reason = "RESEARCH_FOLLOW_UP_REQUIRES_LATER_ORIGINAL_CONTEXT"
    else:
        args = _answer(c, _plan(c))
        invoke = partial(follow._read_follow_up_answer, **args)
        reason = "RESEARCH_FOLLOW_UP_ORIGINAL_CLOCK_MISMATCH"
    before = _files(c["root"])
    with pytest.raises(ValueError, match=f"^{reason}$"):
        invoke()
    assert _files(c["root"]) == before
