"""Original productive transport/composer with fully local network and signing stubs."""

from dataclasses import replace
import json
from urllib.parse import parse_qs, urlparse

import pytest

from src.ops.full_core_live_path_composition_root_v1 import (
    pretrade_acquisition_v1 as clocks,
    fresh_pretrade_runtime_get_v1 as fresh,
    productive_read_only_get_transport_v1 as wire,
)
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    ENDPOINT_ACCOUNT_BALANCE,
    GET_CACHE_POLICY_DECISION_BOUND_SNAPSHOT,
)
from src.ops.governed_productive_account_equity_authority_producer_v1 import (
    current_productive_29p_common_epoch_handoff_v1 as common,
    current_productive_common_epoch_to_enter_live_29p_handoff_v1 as mapping,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_common_epoch_to_enter_live_29p_handoff_v1 import (
    CurrentProductiveCommonEpochToEnterLive29PHandoffError,
    build_current_productive_enter_live_29p_injected_from_common_epoch_handoff_v1,
)
from tests.ops.test_full_core_current_productive_29p_common_epoch_handoff_v1 import (
    _bound,
    _identity_payloads,
)

DECISION = "2026-11-07T12:00:00Z"


@pytest.fixture
def local_wire(monkeypatch):
    state = {"now": "2026-11-07T12:00:01Z", "calls": [], "payloads": _identity_payloads()}
    monkeypatch.setattr(wire, "utc_now_iso_v1", lambda: state["now"])
    monkeypatch.setattr(clocks, "utc_now_iso_v1", lambda: state["now"])
    monkeypatch.setattr(fresh, "utc_now_iso_v1", lambda: state["now"])
    monkeypatch.setattr(common, "_utc_now_iso_v1", lambda: state["now"])
    monkeypatch.setattr(mapping, "utc_now_iso_v1", lambda: state["now"])
    monkeypatch.setattr(wire, "build_k1_okx_venue_auth_headers_v1", lambda **_: {})
    monkeypatch.setattr(wire.socket, "setdefaulttimeout", lambda _: None)

    class Response:
        status = 200

        def __init__(self, payload):
            self.body = json.dumps(payload).encode()

        def read(self):
            return self.body

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

    class Opener:
        def open(self, request, **kwargs):
            assert request.method == "GET"
            parsed = urlparse(request.full_url)
            assert parsed.hostname == wire.AUTHORIZED_HOST
            state["calls"].append(request.full_url)
            inst = (parse_qs(parsed.query).get("instId") or [""])[0]
            key = f"{parsed.path}#instId={inst}"
            payload = state["payloads"].get(key, state["payloads"].get(parsed.path))
            assert payload is not None
            return Response(payload)

    monkeypatch.setattr(wire, "build_opener", lambda *args: Opener())
    transport = wire.FullCoreProductiveReadOnlyGetTransportV1(handle=object(), max_request_count=40)
    return state, transport


def compose(transport, decision=DECISION, cycle_id=""):
    return common.compose_current_productive_29p_common_epoch_handoff_v1(
        decision_epoch=decision,
        bound_instrument=_bound(),
        fresh_get_transport=transport,
        pretrade_cycle_id=cycle_id,
    )


def carrier(handoff, transport):
    return build_current_productive_enter_live_29p_injected_from_common_epoch_handoff_v1(
        handoff=handoff, transport=transport
    )


def test_decision_snapshot_deduplicates_but_keeps_original_acquisition_age(local_wire):
    state, transport = local_wire
    first = compose(transport)
    assert first.evaluator_29p is True
    assert first.observation.decision_epoch == DECISION
    assert first.observation.observed_at_as_of == state["now"]
    assert transport.request_count == len(state["calls"]) == 9
    state["now"] = "2026-11-07T12:00:03Z"
    repeated = compose(transport)
    assert repeated.evaluator_29p is True
    assert repeated.observation.observed_at_as_of == first.observation.observed_at_as_of
    assert repeated.observation.age_seconds == "2"
    assert transport.request_count == len(state["calls"]) == 9


def test_next_decision_reacquires_same_bytes_without_resetting_request_budget(local_wire):
    state, transport = local_wire
    first = compose(transport)
    state["now"] = "2026-11-07T12:01:01Z"
    next_decision = "2026-11-07T12:01:00Z"
    second = compose(transport, next_decision)
    assert second.evaluator_29p is True
    assert second.observation.decision_epoch == next_decision
    assert second.observation.observed_at_as_of == state["now"]
    assert second.observation.provenance_digest == first.observation.provenance_digest
    assert second.output.value == first.output.value == "123.45"
    assert transport.request_count == len(state["calls"]) == 18
    assert first.observation.observed_at_as_of == "2026-11-07T12:00:01Z"


def test_second_collection_cannot_increase_or_reset_global_get_quota(local_wire):
    state, transport = local_wire
    transport.max_request_count = 16
    compose(transport)
    state["now"] = "2026-11-07T12:01:01Z"
    with pytest.raises(wire.FullCoreProductiveReadOnlyGetError, match="MAX_REQUEST_COUNT_EXCEEDED"):
        compose(transport, "2026-11-07T12:01:00Z")
    assert transport.request_count == len(state["calls"]) == 16


def test_same_decision_expired_cache_stays_stale_without_minting_new_time(local_wire):
    state, transport = local_wire
    compose(transport)
    state["now"] = "2026-11-07T12:00:07Z"
    stale = compose(transport)
    assert stale.get_status == "STALE"
    assert stale.observation is None and stale.eligibility is None
    assert stale.evaluator_29p is False
    assert transport.request_count == 9
    assert any("ACQUISITION_STALE" in reason for reason in stale.get_evidence.reason_codes)


@pytest.mark.parametrize(
    "changed",
    [
        {"acquired_at_utc": ""},
        {"acquired_at_utc": "not-a-time"},
        {"acquired_at_utc": "2026-11-07T12:00:01"},
        {"acquired_at_utc": "2026-11-07T12:00:02Z"},
        {"pretrade_decision_id": "another-decision"},
    ],
)
def test_unbound_malformed_future_or_foreign_acquisition_cannot_mint_capital(
    local_wire, monkeypatch, changed
):
    _, transport = local_wire
    original_get = transport.get

    def changed_result(**kwargs):
        return replace(original_get(**kwargs), **changed)

    monkeypatch.setattr(transport, "get", changed_result)
    denied = compose(transport)
    assert denied.get_status in {"STALE", "CONTRADICTORY"}
    assert denied.observation is None and denied.produced is False
    assert denied.evaluator_29p is False
    assert transport.request_count == 9


def test_legacy_path_cache_cannot_substitute_for_decision_acquisition(local_wire):
    _, transport = local_wire
    endpoint = "/api/v5/account/balance?ccy=USDC"
    transport.get(endpoint=endpoint, auth_required=True, pretrade_decision_id="old-decision")
    handoff = compose(transport)
    assert handoff.evaluator_29p is True
    assert transport.request_count == 10
    assert handoff.pretrade_results["balance"].pretrade_decision_id == DECISION


def test_carrier_uses_admitted_snapshot_despite_mutable_path_cache(local_wire):
    state, transport = local_wire
    handoff = compose(transport)
    transport.payloads_by_path[ENDPOINT_ACCOUNT_BALANCE] = {"code": "0", "data": []}
    # Even nested mutation of a cached response cannot change the collected snapshot.
    for cached in transport._decision_cache.values():
        if cached.endpoint.startswith(ENDPOINT_ACCOUNT_BALANCE):
            cached.payload["data"][0]["details"][0]["availEq"] = "9999"
    transport._cache.clear()
    injected = carrier(handoff, transport)
    assert injected.payload["data"][0]["details"][0]["availEq"] == "123.45"
    assert injected.observed_at == "2026-11-07T12:00:01Z"
    assert injected.acquisition_decision_id == DECISION
    assert transport.request_count == len(state["calls"]) == 9


def test_carrier_rechecks_elapsed_time_without_an_extra_get(local_wire):
    state, transport = local_wire
    handoff = compose(transport)
    state["now"] = "2026-11-07T12:00:07Z"
    with pytest.raises(
        CurrentProductiveCommonEpochToEnterLive29PHandoffError, match="ACQUISITION_STALE"
    ):
        carrier(handoff, transport)
    assert transport.request_count == 9


def test_new_decision_cannot_relabel_an_old_typed_result(local_wire, monkeypatch):
    state, transport = local_wire
    first = compose(transport)
    by_endpoint = {result.endpoint: result for result in first.pretrade_results.values()}
    monkeypatch.setattr(transport, "get", lambda **kw: by_endpoint[kw["endpoint"]])
    state["now"] = "2026-11-07T12:00:02Z"
    denied = compose(transport, "2026-11-07T12:00:02Z")
    assert denied.get_status == "CONTRADICTORY"
    assert denied.evaluator_29p is False
    assert transport.request_count == 9


def test_distinct_cycles_in_same_wall_clock_second_acquire_distinct_snapshots(local_wire):
    _, transport = local_wire
    first = compose(transport, cycle_id="original-cycle-a")
    second = compose(transport, cycle_id="original-cycle-b")
    assert first.evaluator_29p is True and second.evaluator_29p is True
    assert first.decision_epoch == second.decision_epoch == DECISION
    assert first.get_evidence.pretrade_decision_id != second.get_evidence.pretrade_decision_id
    assert transport.request_count == 18
    assert carrier(second, transport).acquisition_cycle_id == "original-cycle-b"


def test_original_identity_pairs_cannot_collide_through_separator_characters(local_wire):
    _, transport = local_wire
    first = compose(transport, decision="decision|a", cycle_id="b")
    second = compose(transport, decision="decision", cycle_id="a|b")
    assert first.evaluator_29p is True and second.evaluator_29p is True
    assert first.get_evidence.pretrade_decision_id != second.get_evidence.pretrade_decision_id
    assert transport.request_count == 18


def test_foreign_account_still_denies_original_admission(local_wire):
    state, transport = local_wire
    state["payloads"] = _identity_payloads(uid="foreign-account")
    denied = compose(transport)
    assert denied.lab_trusted is False and denied.evaluator_29p is False


def test_fractional_age_does_not_extend_original_ttl():
    assert (
        clocks.acquisition_age_seconds_v1(
            acquired_at_utc="2026-11-07T12:00:00Z", now_utc="2026-11-07T12:00:00.001Z"
        )
        == "1"
    )
    with pytest.raises(ValueError, match="ACQUISITION_STALE"):
        clocks.acquisition_age_seconds_v1(
            acquired_at_utc="2026-11-07T12:00:00Z", now_utc="2026-11-07T12:00:05.001Z"
        )


def test_new_cache_policy_preserves_existing_general_snapshot_policy(local_wire):
    _, transport = local_wire
    endpoint = "/api/v5/account/balance?ccy=USDC"
    first = transport.get(endpoint=endpoint, auth_required=True, pretrade_decision_id="general-a")
    assert (
        transport.get(endpoint=endpoint, auth_required=True, pretrade_decision_id="general-b")
        is first
    )
    fresh = transport.get(
        endpoint=endpoint,
        auth_required=True,
        pretrade_decision_id=DECISION,
        get_cache_policy=GET_CACHE_POLICY_DECISION_BOUND_SNAPSHOT,
    )
    assert fresh is not first and fresh.pretrade_decision_id == DECISION
    assert transport.request_count == 2


def test_original_treasury_consumer_keeps_decision_capture_and_value(local_wire):
    from src.ops.full_core_live_path_composition_root_v1.current_productive_treasury_single_source_capital_handoff_v1 import (
        build_default_full_core_u04_p01_eligibility_host_inputs_v1,
        execute_current_productive_treasury_single_source_capital_handoff_v1,
    )
    from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_available_for_sizing_base_binding_v1 import (
        clear_current_productive_base_binding_state_v1,
    )

    _, transport = local_wire
    clear_current_productive_base_binding_state_v1()
    try:
        handoff = compose(transport)
        injected = carrier(handoff, transport)
        result = execute_current_productive_treasury_single_source_capital_handoff_v1(
            margin_observation=handoff.observation,
            instrument_id=handoff.bound_instrument.instrument_id,
            body_sha256=injected.body_sha256,
            fresh_pretrade_get_status=handoff.get_status,
            live_account_bound_status=handoff.lab_status,
            u04_p01_host_inputs=build_default_full_core_u04_p01_eligibility_host_inputs_v1(
                raw_acct_lv=handoff.adaptation.raw_token
            ),
        )
        assert result.fail_closed is False, result.reason_codes
        assert result.producer_output.value == handoff.output.value == "123.45"
        assert result.p01_fact.decision_epoch == DECISION
        assert result.p01_fact.observed_at_as_of == "2026-11-07T12:00:01Z"
        assert result.eligibility_fact.decision_epoch == DECISION
        assert transport.request_count == 9
    finally:
        clear_current_productive_base_binding_state_v1()
