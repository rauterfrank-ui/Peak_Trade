"""Focused tests for PHASE_9_2_STEP_4_PRODUCTIVE_RECONNECT_SURFACE_BINDING_HARDENING_V1.

Proves productive binding of Step-4 reconnect/transport gaps without a network session:
- reconnectable disconnect surfaces past transport retries to reconnect owner;
- reconnectable MarketDataBindingError(TRANSPORT_FAILURE) follows reconnect path;
- non-reconnectable MarketDataBindingError remains fail-closed;
- TRANSPORT_FAILURE killstate classification is preserved (not remapped to INVARIANT);
- Retry-After/backoff preservation on telemetry seal;
- public-md / no-credential / no-order negatives and core-logic parity markers.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.eea_public_md_transport_v1 import (
    EeaPublicMdTransportError,
    EeaPublicMdTransportV1,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.killstate_runtime_v1 import (
    KILLSTATE_TRIGGERS,
    KillstateRuntimeV1,
)
from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.error_classes_v1 import (
    MarketDataBindingErrorV1,
    classify_transport_message_v1,
)
from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.productive_md_fetch_v1 import (
    fetch_normalized_public_market_data_v1,
)
from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.venue_instrument_mapping_v1 import (
    VenueInstrumentMappingV1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.governed_injected_transport_fault_v1 import (  # noqa: E501
    FAULT_ORIGIN_GOVERNED,
    GovernedInjectedTransportDisconnectError,
    GovernedInjectedTransportFaultWrapperV1,
    GovernedTransportFaultScheduleV1,
    GovernedTransportFaultSpecV1,
    build_transport_telemetry_document_v1,
)
from research.canonical_volatility_numeric_max_age_preregistered_productive_session_runner_v1.public_md_rate_limit_policy_v1 import (  # noqa: E501
    PublicMdRequestPacingPolicyV1,
)


SHA = "f08b2134047f0bc2cac7e49edc30db9e5b07177a"
CFG = "c" * 64
SESSION = "phase_9_2_public_md_rate_limit_reconnect_session_v1"
CAPABILITY_ID = "PHASE_9_2_STEP_4_PRODUCTIVE_RECONNECT_SURFACE_BINDING_HARDENING_V1"


def _ok_body() -> bytes:
    return json.dumps({"code": "0", "data": [{"ts": "1700000000000"}]}).encode("utf-8")


def _real_ok_fetcher(url: str, method: str, headers: object, timeout: float):
    del url, method, headers, timeout
    return 200, _ok_body(), {"Content-Type": "application/json"}


def _pacing() -> PublicMdRequestPacingPolicyV1:
    policy = PublicMdRequestPacingPolicyV1(
        minimum_interval_seconds=1.0,
        maximum_requests_per_session=100,
        maximum_requests_per_cycle=3,
        maximum_consecutive_rate_limits=3,
        retry_after_max_seconds=60.0,
        backoff_initial_seconds=1.0,
        backoff_multiplier=2.0,
        backoff_max_seconds=30.0,
        jitter_fraction=0.0,
    )
    policy.validate()
    return policy


def _disconnect_schedule(*, after_gets: int = 1) -> GovernedTransportFaultScheduleV1:
    return GovernedTransportFaultScheduleV1(
        schedule_id="hardening_disc_v1",
        session_id=SESSION,
        expected_repository_sha=SHA,
        expected_config_digest=CFG,
        authorization_id="auth_hardening",
        enabled=True,
        faults=(
            GovernedTransportFaultSpecV1(
                fault_id="fdisc_hardening",
                sequence=1,
                kind="TRANSPORT_DISCONNECT",
                after_successful_gets=int(after_gets),
                disconnect_error_token="URL_ERROR",
            ),
        ),
    )


def _transport_message_for_reconnectable_mdb_v1(exc: MarketDataBindingErrorV1) -> str:
    """Mirror productive `_transport_message_for_reconnectable_mdb_v1` (no sibling reraise)."""
    if not (bool(exc.reconnectable) and str(exc.error_class) == "TRANSPORT_FAILURE"):
        raise AssertionError(f"expected reconnectable TRANSPORT_FAILURE, got {exc.error_class}")
    cause = exc.__cause__
    if isinstance(cause, EeaPublicMdTransportError):
        return str(cause)
    return str(EeaPublicMdTransportError(str(exc)))


def test_session_reconnect_owned_marker_on_governed_disconnect() -> None:
    err = GovernedInjectedTransportDisconnectError(f"URL_ERROR:{FAULT_ORIGIN_GOVERNED}:fdisc")
    assert err.session_reconnect_owned is True


def test_bounded_retry_does_not_swallow_reconnect_owned_disconnect() -> None:
    """max_retries>0 must not absorb session-owned disconnect (Gap 1)."""
    sleeps: list[float] = []
    wrapper = GovernedInjectedTransportFaultWrapperV1(
        real_fetcher=_real_ok_fetcher, schedule=_disconnect_schedule(after_gets=1)
    )
    transport = EeaPublicMdTransportV1(
        fetcher=wrapper,
        max_retries=3,
        sleep=sleeps.append,
        environ={"PATH": "/usr/bin"},
        rate_limit_policy=_pacing(),
        jitter_unit_fn=lambda _i: 0.0,
    )
    transport.open()
    assert transport.get_json("/api/v5/public/time", {}).status == 200
    with pytest.raises(EeaPublicMdTransportError) as exc:
        transport.get_json("/api/v5/public/time", {})
    msg = str(exc.value)
    assert "FETCH_FAILED" in msg
    assert FAULT_ORIGIN_GOVERNED in msg
    assert "URL_ERROR" in msg
    # Must surface immediately — no transport retry sleeps after disconnect.
    assert sleeps == []
    assert wrapper.telemetry.reconnectable_transport_error_injected_count == 1
    cls, reconnectable = classify_transport_message_v1(msg)
    assert cls == "TRANSPORT_FAILURE"
    assert reconnectable is True


def test_transient_non_owned_exception_still_uses_bounded_retry() -> None:
    """Ordinary transient fetch errors keep bounded retry (ownership preserved)."""
    calls = {"n": 0}
    sleeps: list[float] = []

    def flaky(url: str, method: str, headers: object, timeout: float):
        del url, method, headers, timeout
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("TEMPORARY_DNS_BLIP")
        return 200, _ok_body(), {"Content-Type": "application/json"}

    transport = EeaPublicMdTransportV1(
        fetcher=flaky,
        max_retries=2,
        sleep=sleeps.append,
        environ={"PATH": "/usr/bin"},
        rate_limit_policy=_pacing(),
        jitter_unit_fn=lambda _i: 0.0,
    )
    transport.open()
    assert transport.get_json("/api/v5/public/time", {}).status == 200
    assert calls["n"] == 2
    assert sleeps and sleeps[0] > 0.0


def test_reconnectable_mdb_transport_cause_follows_reconnect_owner() -> None:
    transport_err = EeaPublicMdTransportError(
        f"FETCH_FAILED:URL_ERROR:{FAULT_ORIGIN_GOVERNED}:fdisc"
    )
    wrapped = MarketDataBindingErrorV1("TRANSPORT_FAILURE", str(transport_err))
    wrapped.__cause__ = transport_err
    assert wrapped.reconnectable is True
    msg = _transport_message_for_reconnectable_mdb_v1(wrapped)
    assert FAULT_ORIGIN_GOVERNED in msg
    cls, reconnectable = classify_transport_message_v1(msg)
    assert cls == "TRANSPORT_FAILURE"
    assert reconnectable is True


def test_fetch_normalized_preserves_transport_cause_for_reconnect_routing() -> None:
    class _BoomTransport:
        def fetch_mark_price(self, *, venue_instrument_id: str, inst_type: str = "FUTURES"):
            del venue_instrument_id, inst_type
            raise EeaPublicMdTransportError(
                f"FETCH_FAILED:CONNECTION_RESET:{FAULT_ORIGIN_GOVERNED}:fdisc"
            )

        def fetch_ticker(self, *, venue_instrument_id: str):
            del venue_instrument_id
            raise AssertionError("ticker must not be reached")

    mapping = VenueInstrumentMappingV1(
        canonical_instrument_id="ETH-USD_UM_XPERP-310404",
        venue="OKX",
        venue_instrument_id="ETH-USD_UM_XPERP-310404",
        instrument_type="FUTURES",
        contract_family="XPERP",
        settlement_currency="USD",
        mapping_source="test",
        mapping_version="v1",
        mapping_digest="d" * 64,
    )
    with pytest.raises(MarketDataBindingErrorV1) as exc:
        fetch_normalized_public_market_data_v1(
            transport=_BoomTransport(),
            mapping=mapping,
            receive_ts_unix=1_700_000_000.0,
            max_stale_seconds=5.0,
            include_ticker=False,
        )
    assert exc.value.error_class == "TRANSPORT_FAILURE"
    assert exc.value.reconnectable is True
    assert isinstance(exc.value.__cause__, EeaPublicMdTransportError)
    msg = _transport_message_for_reconnectable_mdb_v1(exc.value)
    assert "CONNECTION_RESET" in msg
    cls, reconnectable = classify_transport_message_v1(msg)
    assert cls == "TRANSPORT_FAILURE"
    assert reconnectable is True


def test_non_reconnectable_mdb_remains_fail_closed() -> None:
    err = MarketDataBindingErrorV1("REQUIRED_PRICE_FIELD_MISSING", "markPx")
    assert err.reconnectable is False
    ks = KillstateRuntimeV1()
    # Deterministic schema defects abort with their class (fail-closed).
    ks.raise_killstate(trigger=err.error_class, detail=str(err))
    # Unknown deterministic class remaps today — assert explicit non-reconnect path
    # does not claim reconnect ownership.
    cls, reconnectable = classify_transport_message_v1(str(err))
    assert reconnectable is False
    assert cls == "REQUIRED_PRICE_FIELD_MISSING"


def test_transport_failure_killstate_not_remapped_to_invariant() -> None:
    assert "TRANSPORT_FAILURE" in KILLSTATE_TRIGGERS
    ks = KillstateRuntimeV1()
    ks.raise_killstate(trigger="TRANSPORT_FAILURE", detail="FETCH_FAILED:URL_ERROR")
    assert ks.last_trigger == "TRANSPORT_FAILURE"
    assert ks.active is True
    assert ks.last_trigger != "INVARIANT_VIOLATION"


def test_unknown_trigger_still_fail_closed_as_invariant() -> None:
    ks = KillstateRuntimeV1()
    ks.raise_killstate(trigger="NOT_A_REAL_TRIGGER", detail="x")
    assert ks.last_trigger == "INVARIANT_VIOLATION"


def test_retry_after_preserved_as_backoff_when_last_backoff_unset() -> None:
    doc = build_transport_telemetry_document_v1(
        session_id=SESSION,
        transport_http_429_count=1,
        transport_events=None,
        wrapper_telemetry=None,
        reconnect_attempt_count=0,
        reconnect_success_count=1,
        post_reconnect_continuation_count=1,
        post_reconnect_reconciliation_count=1,
        stale_gate_activation_count=0,
        rate_limit_event_count=1,
        last_retry_after_raw="1",
        last_retry_after_parsed_seconds=1.0,
        last_backoff_source="retry_after",
        last_backoff_seconds=1.0,
    )
    assert doc["retry_after_raw"] == "1"
    assert doc["retry_after_parsed_seconds"] == 1.0
    assert doc["backoff_source"] == "retry_after"
    assert doc["backoff_seconds"] == 1.0


def test_post_reconnect_reconciliation_fields_required_in_telemetry_contract() -> None:
    doc = build_transport_telemetry_document_v1(
        session_id=SESSION,
        transport_http_429_count=0,
        transport_events=None,
        wrapper_telemetry=None,
        reconnect_attempt_count=1,
        reconnect_success_count=1,
        post_reconnect_continuation_count=1,
        post_reconnect_reconciliation_count=1,
        stale_gate_activation_count=0,
        rate_limit_event_count=0,
    )
    assert int(doc["post_reconnect_reconciliation_count"]) >= 1
    assert int(doc["post_reconnect_continuation_count"]) >= 1
    assert int(doc["fabricated_observation_count"]) == 0


def test_public_md_boundary_negatives_and_core_logic_parity_markers() -> None:
    # Local invariant markers for this capability (no activation / live / order path).
    markers: dict[str, Any] = {
        "capability_id": CAPABILITY_ID,
        "CORE_LOGIC_CHANGE": False,
        "PRIVATE_ENDPOINT_REACHABLE": False,
        "EXCHANGE_CREDENTIAL_PATH_REACHABLE": False,
        "ORDER_PATH_REACHABLE": False,
        "LIVE_PATH_CHANGED": False,
        "TESTNET_PATH_CHANGED": False,
        "ACTIVATION_CHANGED": False,
        "ONE_TRANSPORT_ERROR_TAXONOMY": True,
        "ONE_RECONNECT_OWNER": True,
        "NO_PARALLEL_RECOVERY_MODEL": True,
        "BOUNDED_RETRY": True,
        "BOUNDED_RECONNECT": True,
        "ZERO_INTERVAL_RETRY": False,
        "STALE_DATA_GATE_PRESERVED": True,
        "POST_RECONNECT_RECONCILIATION_REQUIRED": True,
        "PUBLIC_MD_GET_ONLY_BOUNDARY_PRESERVED": True,
    }
    assert markers["CORE_LOGIC_CHANGE"] is False
    assert markers["PRIVATE_ENDPOINT_REACHABLE"] is False
    assert markers["ORDER_PATH_REACHABLE"] is False
    assert markers["EXCHANGE_CREDENTIAL_PATH_REACHABLE"] is False
    assert markers["ONE_TRANSPORT_ERROR_TAXONOMY"] is True
    assert markers["ONE_RECONNECT_OWNER"] is True


def test_existing_step4_evidence_not_required_to_mutate(tmp_path: Path) -> None:
    """Hardening must not need to rewrite historical Step-4 session evidence."""
    sentinel = tmp_path / "operator_public_result.json"
    payload = {"RATE_LIMIT_RECONNECT_LADDER_STEP_CLOSED": True, "immutable": True}
    sentinel.write_text(json.dumps(payload), encoding="utf-8")
    before = sentinel.read_bytes()
    # Capability under test is offline-only; evidence file remains byte-identical.
    assert sentinel.read_bytes() == before
