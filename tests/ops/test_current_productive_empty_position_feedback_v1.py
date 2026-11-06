"""Bounded empty-position reads after full close; no live acquisition or orders."""

from dataclasses import replace
from urllib.parse import urlencode

import pytest

from src.ops.full_core_live_path_composition_root_v1 import (
    full_core_exchange_reconciliation_offline_provider_v1 as offline,
    full_core_exchange_reconciliation_integration_v1 as integration,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_post_submit_exchange_reconciliation_lifecycle_join_v1 import (
    run_full_core_post_submit_lifecycle_reconciliation_join_v1 as run_join,
)
from tests.ops.test_current_productive_post_close_feedback_v1 import _case
from tests.ops.test_full_core_exchange_reconciliation_okx_read_only_provider_v1 import (
    FixtureBackedOkxReadOnlyTransport,
)

START = "2026-11-03T00:00:01.500000Z"
END = "2026-11-03T00:00:02Z"


def _empty_case(monkeypatch):
    args, owner, _, old = _case(monkeypatch)
    native = args["post_close_feedback_request"].execution.envelope.instrument_id
    args["offline_fixture"] = replace(
        args["offline_fixture"],
        positions={"code": "0", "data": []},
        positions_query_started_at_utc=START,
        positions_query_completed_at_utc=END,
        positions_query_endpoint="/api/v5/account/positions?" + urlencode({"instId": native}),
    )
    return args, owner, old


class ScopedTransport(FixtureBackedOkxReadOnlyTransport):
    def get(self, **kwargs):
        return replace(super().get(**kwargs), endpoint=kwargs["endpoint"])


@pytest.mark.parametrize("provider", ["offline", "injected"])
def test_empty_query_after_observed_fill_reaches_capital_and_ranking(monkeypatch, provider):
    args, owner, old = _empty_case(monkeypatch)
    if provider == "injected":
        fixture = args.pop("offline_fixture")
        args.update(read_only_get_transport=ScopedTransport(fixture), pretrade_decision_id="close")
        fetch = integration.fetch_okx_read_only_reconciliation_snapshot_v1
        times = iter((START, END))
        monkeypatch.setattr(
            integration,
            "fetch_okx_read_only_reconciliation_snapshot_v1",
            lambda **kwargs: fetch(**kwargs, acquisition_clock=lambda: next(times)),
        )
    result = run_join(**args)
    feedback = result.post_close_feedback
    assert feedback.status == "RECONCILED_FLAT_REVIEWED", feedback.reason_codes
    assert feedback.position.venue_flat and feedback.remaining_quantity == 0
    assert feedback.capital_refresh.mutated and owner.active_sum_v1() == 0
    assert old in feedback.membership_review.ordered_membership
    assert feedback.membership_review.persisted_artifact is None
    snapshot = result.reconciliation.snapshot
    assert snapshot["positions_observation"]["response"]["data"] == []
    assert not any(i["layer"] == "EXCHANGE_POSITION_STATE" for i in snapshot["evidence_items"])
    assert feedback.execution_authority_effect == "NONE"


@pytest.mark.parametrize(
    "problem",
    [
        "missing_coverage",
        "wrong_account",
        "wrong_environment",
        "wrong_identity",
        "wrong_instrument",
        "unscoped_query",
        "filtered_query",
        "wrong_method",
        "wrong_digest",
        "wrong_anchor",
        "missing_anchor",
        "future_query",
        "reversed_interval",
        "straddles_fill",
        "missing_time",
        "malformed_time",
    ],
)
def test_unproven_empty_query_preserves_budget_and_blocks_review(monkeypatch, problem):
    args, owner, _ = _empty_case(monkeypatch)
    build = offline.build_offline_exchange_reconciliation_snapshot_v1

    def tampered(**kwargs):
        snapshot = build(**kwargs)
        observation = dict(snapshot.positions_observation)
        coverage = dict(observation["query_coverage"])
        if problem == "missing_coverage":
            observation["query_coverage"] = None
        else:
            field, value = {
                "wrong_account": ("account", "other"),
                "wrong_environment": ("environment", "other"),
                "wrong_identity": ("identity_digest", "other"),
                "wrong_instrument": (
                    "endpoint",
                    "/api/v5/account/positions?instId=OTHER",
                ),
                "unscoped_query": ("endpoint", "/api/v5/account/positions"),
                "filtered_query": ("endpoint", coverage["endpoint"] + "&posId=other"),
                "wrong_method": ("method", "POST"),
                "wrong_digest": ("response_digest", "other"),
                "wrong_anchor": ("preceding_filled_order_digests", ["other"]),
                "missing_anchor": ("preceding_filled_order_digests", []),
                "future_query": ("completed_at_utc", "2026-11-03T00:00:04Z"),
                "reversed_interval": ("started_at_utc", "2026-11-03T00:00:02.5Z"),
                "straddles_fill": ("started_at_utc", "2026-11-03T00:00:00.5Z"),
                "missing_time": ("started_at_utc", ""),
                "malformed_time": ("completed_at_utc", 123),
            }[problem]
            coverage[field] = value
            observation["query_coverage"] = coverage
        return replace(snapshot, positions_observation=observation)

    monkeypatch.setattr(offline, "build_offline_exchange_reconciliation_snapshot_v1", tampered)
    before = owner.budget_state_v1()
    feedback = run_join(**args).post_close_feedback
    assert feedback.status == "BLOCKED", feedback.reason_codes
    assert feedback.capital_refresh is None and feedback.membership_review is None
    assert owner.budget_state_v1() == before


@pytest.mark.parametrize("problem", ["cached", "wrong_endpoint", "wrong_method", "unauthenticated"])
def test_adapter_does_not_issue_coverage_for_unproven_transport(monkeypatch, problem):
    args, owner, _ = _empty_case(monkeypatch)
    fixture = args.pop("offline_fixture")

    class UnprovenTransport(ScopedTransport):
        def get(self, **kwargs):
            result = super().get(**kwargs)
            if kwargs["endpoint"].startswith("/api/v5/account/positions?"):
                changes = {
                    "cached": {"historical_reuse": True},
                    "wrong_endpoint": {"endpoint": "/api/v5/account/positions"},
                    "wrong_method": {"method": "POST"},
                    "unauthenticated": {"auth_header_sent": False},
                }[problem]
                return replace(result, **changes)
            return result

    args.update(read_only_get_transport=UnprovenTransport(fixture), pretrade_decision_id="deny")
    before = owner.budget_state_v1()
    result = run_join(**args)
    assert result.post_close_feedback.status == "BLOCKED"
    assert result.reconciliation.snapshot["positions_observation"]["query_coverage"] is None
    assert owner.budget_state_v1() == before


def test_later_exact_order_lookup_cannot_retroactively_prove_query_after_fill(monkeypatch):
    args, owner, _ = _empty_case(monkeypatch)
    fixture = args.pop("offline_fixture")

    class LateFillTransport(ScopedTransport):
        def get(self, **kwargs):
            result = super().get(**kwargs)
            if kwargs["endpoint"].startswith("/api/v5/trade/orders-history?"):
                return replace(result, payload={"code": "0", "data": []})
            return result

    args.update(read_only_get_transport=LateFillTransport(fixture), pretrade_decision_id="late")
    fetch = integration.fetch_okx_read_only_reconciliation_snapshot_v1
    times = iter((START, END))
    monkeypatch.setattr(
        integration,
        "fetch_okx_read_only_reconciliation_snapshot_v1",
        lambda **kwargs: fetch(**kwargs, acquisition_clock=lambda: next(times)),
    )
    before = owner.budget_state_v1()
    feedback = run_join(**args).post_close_feedback
    assert feedback.status == "BLOCKED"
    assert "POST_CLOSE_EMPTY_POSITION_QUERY_UNPROVEN" in feedback.reason_codes
    assert owner.budget_state_v1() == before
