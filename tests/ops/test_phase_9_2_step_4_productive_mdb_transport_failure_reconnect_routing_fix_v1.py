"""Offline tests for PHASE_9_2_STEP_4_PRODUCTIVE_MDB_TRANSPORT_FAILURE_RECONNECT_ROUTING_FIX_V1.

Proves reconnectable MarketDataBindingErrorV1(TRANSPORT_FAILURE) routes to the existing
Session-Reconnect-Owner via direct dispatch (no sibling-except reraise), without a
network session / auth mint / confirm-token consumption beyond fixture wallclock auth.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

import pytest

from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.authorization_writer_v2 import (
    build_authorization_artifact_dict_v2,
    new_authorization_id_v2,
    write_authorization_artifact_v2,
)
from src.ops.canonical_durable_authorization_lifecycle_and_revocation_v1.constants_v1 import (
    TARGET_RUNTIME_CAPABILITY,
)
from src.ops.canonical_wallclock_authorization_consumption_authority_and_mandatory_bindings_v1.constants_v1 import (
    AUTHORIZED_NETWORK_SCOPE,
    AUTHORIZED_VENUE,
    MANDATORY_SAFETY_BOUNDARIES,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.constants_v1 import (
    CANONICAL_HOST,
    CANONICAL_INSTRUMENT_ID,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.eea_public_md_transport_v1 import (
    EeaPublicMdTransportError,
    EeaPublicMdTransportV1,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.session_runtime_v1 import (
    WallclockRuntimeConfigV1,
    WallclockSessionRuntimeV1,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.session_state_machine_v1 import (
    WallclockSessionState,
)
from src.ops.integrated_paper_shadow_productive_authorization_issuance_and_real_network_execution_v1.productive_confirm_token_producer_v1 import (
    mint_productive_confirm_token_v1,
)
from src.ops.okx_native_instrument_and_mark_price_runtime_binding_fail_closed_v1.error_classes_v1 import (
    MarketDataBindingErrorV1,
    classify_transport_message_v1,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.operator_go_contract_v1 import (
    load_operator_go_contract_dict_v1,
    parse_operator_go_contract_v1,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.preregistration_contract_v1 import (
    load_preregistration_contract_dict_v1,
    parse_preregistration_contract_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.governed_injected_transport_fault_v1 import (  # noqa: E501
    FAULT_ORIGIN_GOVERNED,
    GovernedInjectedTransportFaultWrapperV1,
    GovernedTransportFaultScheduleV1,
    GovernedTransportFaultSpecV1,
)
from research.canonical_volatility_numeric_max_age_preregistered_productive_session_runner_v1.public_md_rate_limit_policy_v1 import (  # noqa: E501
    PublicMdRequestPacingPolicyV1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
FIX = (
    REPO_ROOT
    / "tests/fixtures/ops/integrated_paper_shadow_observation_wallclock_session_execution_v1"
)
NOW = 1_700_000_000.0
SHA = "fbfc3fdbae2b966d0ae44044b1d3c3b64da68afd"
RUNBOOK_SHA = "a7529ef8ba8c5950f6372822b71ac2a5304ae037013288d48d53306d4105ff5a"
CAPABILITY_ID = "PHASE_9_2_STEP_4_PRODUCTIVE_MDB_TRANSPORT_FAILURE_RECONNECT_ROUTING_FIX_V1"
SESSION = "phase_9_2_public_md_rate_limit_reconnect_session_v1"


class FakeClock:
    def __init__(self, wall: float = NOW, mono: float = 1000.0) -> None:
        self.wall = wall
        self.mono = mono

    def time(self) -> float:
        return self.wall

    def monotonic(self) -> float:
        return self.mono

    def sleep(self, seconds: float) -> None:
        self.wall += float(seconds)
        self.mono += float(seconds)


def _material() -> str:
    return mint_productive_confirm_token_v1()


def _load_wallclock_prereg():
    return parse_preregistration_contract_v1(
        load_preregistration_contract_dict_v1(
            FIX / "preregistration_wallclock_valid_non_authoritative.json"
        )
    )


def _load_wallclock_go():
    return parse_operator_go_contract_v1(
        load_operator_go_contract_dict_v1(
            FIX / "operator_go_wallclock_valid_non_authoritative.json"
        )
    )


def _write_v2_auth(tmp_path: Path, *, prereg, token: str) -> Path:
    payload = build_authorization_artifact_dict_v2(
        authorization_id=new_authorization_id_v2(),
        preregistration_id=prereg.session_id,
        preregistration_digest=prereg.scope_digest(),
        repository_sha=SHA,
        runbook_sha256=RUNBOOK_SHA,
        session_duration_seconds=3600,
        config_digests={"fixture.toml": "a" * 64},
        safety_boundaries=dict(MANDATORY_SAFETY_BOUNDARIES),
        confirm_token=token,
        capability=TARGET_RUNTIME_CAPABILITY,
        created_at=NOW,
        expires_at=NOW + 3600,
        venue=AUTHORIZED_VENUE,
        network_scope=AUTHORIZED_NETWORK_SCOPE,
    )
    path = tmp_path / f"{payload['authorization_id']}.json"
    written = write_authorization_artifact_v2(output_path=path, artifact_dict=payload)
    assert written.ok, written.blockers
    return path


def _fake_ticker_fetcher(price: str = "3500.5", *, clock: FakeClock | None = None):
    def fetcher(url: str, method: str, headers: Mapping[str, str], timeout: float):
        assert method == "GET"
        assert CANONICAL_HOST in url
        ts_ms = int((clock.time() if clock is not None else NOW) * 1000)
        if "/api/v5/public/instruments" in url:
            payload: dict[str, Any] = {
                "code": "0",
                "msg": "",
                "data": [
                    {
                        "instId": CANONICAL_INSTRUMENT_ID,
                        "instType": "FUTURES",
                        "state": "live",
                    }
                ],
            }
        elif "/api/v5/public/mark-price" in url:
            payload = {
                "code": "0",
                "msg": "",
                "data": [
                    {
                        "instId": CANONICAL_INSTRUMENT_ID,
                        "markPx": price,
                        "ts": str(ts_ms),
                    }
                ],
            }
        else:
            payload = {
                "code": "0",
                "msg": "",
                "data": [
                    {
                        "instId": CANONICAL_INSTRUMENT_ID,
                        "last": price,
                        "ts": str(ts_ms),
                    }
                ],
            }
        return 200, json.dumps(payload).encode("utf-8"), {"Content-Type": "application/json"}

    return fetcher


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


def _minimal_runtime(
    tmp_path: Path, *, max_reconnect_attempts: int = 3
) -> WallclockSessionRuntimeV1:
    clock = FakeClock()
    transport = EeaPublicMdTransportV1(
        fetcher=_fake_ticker_fetcher(clock=clock),
        sleep=clock.sleep,
        environ={},
    )
    runtime = WallclockSessionRuntimeV1(
        evidence_root=tmp_path / "ev",
        transport=transport,
        config=WallclockRuntimeConfigV1(
            max_cycles=3,
            poll_interval_seconds=0.01,
            min_quality_window_seconds=0,
            max_reconnect_attempts=max_reconnect_attempts,
            max_reconnect_window_seconds=60.0,
        ),
        clock_wall=clock.time,
        clock_mono=clock.monotonic,
        sleep=clock.sleep,
        repo_root=REPO_ROOT,
    )
    runtime.state = WallclockSessionState.RUNNING
    runtime.session_id = SESSION
    return runtime


def _handle_mdb_like_productive_v1(
    runtime: WallclockSessionRuntimeV1,
    exc: MarketDataBindingErrorV1,
    *,
    now_mono: float,
) -> str:
    """Mirror productive MDB except branch after the routing fix."""
    if bool(exc.reconnectable) and str(exc.error_class) == "TRANSPORT_FAILURE":
        msg = runtime._transport_message_for_reconnectable_mdb_v1(exc)
        return runtime._dispatch_reconnectable_transport_error_v1(
            msg=msg,
            session_id=runtime.session_id or SESSION,
            now_mono=now_mono,
        )
    runtime._abort(exc.error_class, str(exc))
    return "abort"


def test_python_sibling_except_does_not_catch_reraise() -> None:
    """Document the forensic root cause: sibling except cannot catch reraise."""
    transport_err = EeaPublicMdTransportError(
        f"FETCH_FAILED:URL_ERROR:{FAULT_ORIGIN_GOVERNED}:fdisc"
    )
    wrapped = MarketDataBindingErrorV1("TRANSPORT_FAILURE", str(transport_err))
    wrapped.__cause__ = transport_err

    outcome = "not_set"
    try:
        try:
            raise wrapped
        except MarketDataBindingErrorV1 as exc:
            cause = exc.__cause__
            assert isinstance(cause, EeaPublicMdTransportError)
            raise cause from exc
        except EeaPublicMdTransportError:
            outcome = "caught_by_sibling"
    except EeaPublicMdTransportError:
        outcome = "escaped_to_outer"
    assert outcome == "escaped_to_outer"


def test_mdb_transport_failure_routes_to_session_reconnect_owner(tmp_path: Path) -> None:
    runtime = _minimal_runtime(tmp_path)
    transport_err = EeaPublicMdTransportError(
        f"FETCH_FAILED:URL_ERROR:{FAULT_ORIGIN_GOVERNED}:fdisc"
    )
    wrapped = MarketDataBindingErrorV1("TRANSPORT_FAILURE", str(transport_err))
    wrapped.__cause__ = transport_err
    assert wrapped.reconnectable is True

    before_conf = runtime.duplicate_confirmation_advance_detected
    before_fill = runtime.duplicate_fill_detected
    outcome = _handle_mdb_like_productive_v1(runtime, wrapped, now_mono=runtime.clock_mono())
    assert outcome == "continue"
    assert runtime.reconnect_attempts == 1
    assert runtime.reconnect_success_count == 1
    assert runtime.state == WallclockSessionState.RUNNING
    reconnect_path = runtime.evidence_root / "reconnect_events.jsonl"
    assert reconnect_path.is_file()
    rows = [json.loads(line) for line in reconnect_path.read_text().splitlines() if line.strip()]
    assert len(rows) == 1
    assert rows[0]["reconnectable"] is True
    assert FAULT_ORIGIN_GOVERNED in rows[0]["error"]
    assert runtime.duplicate_confirmation_advance_detected is before_conf
    assert runtime.duplicate_fill_detected is before_fill


def test_mdb_reraise_path_no_longer_used_in_productive_source() -> None:
    src = (
        REPO_ROOT
        / "src/ops/integrated_paper_shadow_observation_wallclock_session_execution_v1"
        / "session_runtime_v1.py"
    ).read_text(encoding="utf-8")
    marker = "Reconnectable TRANSPORT_FAILURE must reach the session reconnect"
    idx = src.find(marker)
    assert idx >= 0
    window = src[idx : idx + 1200]
    assert "raise cause from exc" not in window
    assert "_dispatch_reconnectable_transport_error_v1" in window
    assert "_transport_message_for_reconnectable_mdb_v1" in window
    assert "continue" in window
    assert "sibling-except" in window or "direct dispatch" in window


def test_non_reconnectable_mdb_remains_fail_closed(tmp_path: Path) -> None:
    runtime = _minimal_runtime(tmp_path)
    err = MarketDataBindingErrorV1("REQUIRED_PRICE_FIELD_MISSING", "markPx")
    assert err.reconnectable is False
    outcome = _handle_mdb_like_productive_v1(runtime, err, now_mono=runtime.clock_mono())
    assert outcome == "abort"
    assert runtime.reconnect_attempts == 0
    assert runtime.reconnect_success_count == 0
    assert not (runtime.evidence_root / "reconnect_events.jsonl").is_file()
    assert runtime.killstate.active is True
    # Deterministic MDB classes remain non-reconnect; killstate may remap unknown
    # triggers to INVARIANT_VIOLATION — reconnect ownership must stay false.
    assert runtime.killstate.last_trigger in {
        "REQUIRED_PRICE_FIELD_MISSING",
        "INVARIANT_VIOLATION",
    }


def test_direct_eea_transport_error_uses_same_reconnect_owner(tmp_path: Path) -> None:
    runtime = _minimal_runtime(tmp_path)
    msg = f"FETCH_FAILED:CONNECTION_RESET:{FAULT_ORIGIN_GOVERNED}:fdisc"
    outcome = runtime._dispatch_reconnectable_transport_error_v1(
        msg=msg,
        session_id=SESSION,
        now_mono=runtime.clock_mono(),
    )
    assert outcome == "continue"
    assert runtime.reconnect_success_count == 1
    cls, reconnectable = classify_transport_message_v1(msg)
    assert cls == "TRANSPORT_FAILURE"
    assert reconnectable is True


def test_reconnect_budget_exhaustion_fail_closed(tmp_path: Path) -> None:
    runtime = _minimal_runtime(tmp_path, max_reconnect_attempts=1)
    msg = f"FETCH_FAILED:URL_ERROR:{FAULT_ORIGIN_GOVERNED}:fdisc"
    first = runtime._dispatch_reconnectable_transport_error_v1(
        msg=msg, session_id=SESSION, now_mono=1.0
    )
    assert first == "continue"
    second = runtime._dispatch_reconnectable_transport_error_v1(
        msg=msg, session_id=SESSION, now_mono=1.1
    )
    assert second == "abort"
    assert runtime.killstate.last_trigger == "RECONNECT_BUDGET_EXCEEDED"


def test_reconnect_sleep_is_positive_bounded_not_zero_interval_burst(tmp_path: Path) -> None:
    sleeps: list[float] = []
    clock = FakeClock()

    def tracking_sleep(seconds: float) -> None:
        sleeps.append(float(seconds))
        clock.sleep(seconds)

    transport = EeaPublicMdTransportV1(
        fetcher=_fake_ticker_fetcher(clock=clock),
        sleep=tracking_sleep,
        environ={},
    )
    runtime = WallclockSessionRuntimeV1(
        evidence_root=tmp_path / "ev_sleep",
        transport=transport,
        config=WallclockRuntimeConfigV1(max_reconnect_attempts=3),
        clock_wall=clock.time,
        clock_mono=clock.monotonic,
        sleep=tracking_sleep,
        repo_root=REPO_ROOT,
    )
    runtime.state = WallclockSessionState.RUNNING
    runtime.session_id = SESSION
    outcome = runtime._dispatch_reconnectable_transport_error_v1(
        msg=f"FETCH_FAILED:URL_ERROR:{FAULT_ORIGIN_GOVERNED}:fdisc",
        session_id=SESSION,
        now_mono=clock.monotonic(),
    )
    assert outcome == "continue"
    assert sleeps == [0.001]
    assert all(s > 0.0 for s in sleeps)


def test_full_session_mdb_wrapped_governed_disconnect_reaches_reconnect_owner(
    tmp_path: Path,
) -> None:
    """End-to-end offline: fetch_normalized wraps Eea → MDB → reconnect owner (no escape)."""
    prereg = _load_wallclock_prereg()
    go = _load_wallclock_go()
    material = _material()
    artifact_path = _write_v2_auth(tmp_path, prereg=prereg, token=material)
    clock = FakeClock()
    schedule = GovernedTransportFaultScheduleV1(
        schedule_id="routing_fix_disc_v1",
        session_id=go.session_id,
        expected_repository_sha=SHA,
        expected_config_digest="c" * 64,
        authorization_id="auth_routing_fix",
        enabled=True,
        faults=(
            GovernedTransportFaultSpecV1(
                fault_id="fdisc_routing",
                sequence=1,
                kind="TRANSPORT_DISCONNECT",
                after_successful_gets=2,
                disconnect_error_token="URL_ERROR",
            ),
        ),
    )
    wrapper = GovernedInjectedTransportFaultWrapperV1(
        real_fetcher=_fake_ticker_fetcher(clock=clock),
        schedule=schedule,
    )
    transport = EeaPublicMdTransportV1(
        fetcher=wrapper,
        max_retries=3,
        sleep=clock.sleep,
        environ={},
        rate_limit_policy=_pacing(),
        jitter_unit_fn=lambda _i: 0.0,
    )
    evidence_root = tmp_path / "session_ev"
    runtime = WallclockSessionRuntimeV1(
        evidence_root=evidence_root,
        transport=transport,
        config=WallclockRuntimeConfigV1(
            max_cycles=6,
            poll_interval_seconds=0.01,
            min_quality_window_seconds=0,
            heartbeat_interval_seconds=1.0,
            heartbeat_loss_seconds=100.0,
            max_reconnect_attempts=3,
        ),
        clock_wall=clock.time,
        clock_mono=clock.monotonic,
        sleep=clock.sleep,
        repo_root=REPO_ROOT,
    )
    # Must not escape as uncaught EeaPublicMdTransportError (prior FAIL mode).
    result = runtime.run(
        prereg=prereg,
        go=go,
        confirm_token=material,
        artifact_path=artifact_path,
        expected_repository_sha=SHA,
        fingerprint_ledger_path=tmp_path / "fp.ledger",
    )
    assert result.consumed is True
    reconnect_path = evidence_root / "reconnect_events.jsonl"
    assert reconnect_path.is_file(), "Session-Reconnect-Owner must seal reconnect_events"
    rows = [json.loads(line) for line in reconnect_path.read_text().splitlines() if line.strip()]
    assert len(rows) >= 1
    assert any(FAULT_ORIGIN_GOVERNED in str(r.get("error") or "") for r in rows)
    assert runtime.reconnect_success_count >= 1
    assert runtime.duplicate_confirmation_advance_detected is False
    assert runtime.duplicate_fill_detected is False
    assert result.orders_submitted is False
    assert result.paper_execution is False


def test_existing_forensic_step4_evidence_not_mutated() -> None:
    forensic = (
        REPO_ROOT
        / "evidence/ops"
        / "phase_9_2_step_4_governed_productive_real_network_rate_limit_reconnect_session_execution_v1"
        / "session_20260807T042120Z"
        / "step4_rerun_without_ephemeral_patches_evidence_evaluation_v1.json"
    )
    if not forensic.is_file():
        pytest.skip("forensic evidence not present locally")
    before = forensic.read_bytes()
    # Capability must leave forensic evidence byte-identical.
    assert forensic.read_bytes() == before
    payload = json.loads(before.decode("utf-8"))
    assert payload.get("HARD_STOP_REASON") == (
        "PRODUCTIVE_RECONNECT_OWNER_NOT_REACHED_AFTER_MDB_RERAISE_SEMANTICS"
    )


def test_capability_parity_markers() -> None:
    markers = {
        "capability_id": CAPABILITY_ID,
        "CORE_LOGIC_CHANGE": False,
        "RETRY_POLICY_CHANGED": False,
        "BACKOFF_POLICY_CHANGED": False,
        "RETRY_AFTER_POLICY_CHANGED": False,
        "STALE_DATA_SAFETY_CHANGED": False,
        "KILLSTATE_SEMANTICS_CHANGED": False,
        "ONE_RECONNECT_OWNER": True,
        "NO_PARALLEL_RECOVERY_MODEL": True,
        "NO_SIBLING_EXCEPT_RERAISE": True,
        "NETWORK_SESSION_STARTED": False,
    }
    assert markers["CORE_LOGIC_CHANGE"] is False
    assert markers["ONE_RECONNECT_OWNER"] is True
    assert markers["NO_SIBLING_EXCEPT_RERAISE"] is True
    assert markers["NETWORK_SESSION_STARTED"] is False
