"""Offline HTTP→source→bounded-cycle→recovery notice→mock email acceptance."""

import asyncio
from hashlib import sha256
import io
import json
from pathlib import Path
import ssl
from unittest.mock import MagicMock
from urllib.error import HTTPError

import pytest

from src.ops.full_core_live_path_composition_root_v1 import (
    productive_read_only_get_transport_v1 as get_owner,
)
from src.ops.full_core_live_path_composition_root_v1 import (
    current_productive_s6_live_fresh_c1_continuous_observation_source_v1 as source_owner,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_canonical_price_provenance_v1 import (
    build_cmc_mark_provenance_from_okx_mark_price_payload_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1 import (
    run_current_productive_governed_cycle_v1,
)
from src.ops.runtime_health_recovery_and_failure_injection_closure_v1 import (
    runtime_recovery_email_v1 as mail,
)
from src.ops.runtime_health_recovery_and_failure_injection_closure_v1.runtime_notice_v1 import (
    record_runtime_notice_v1,
    EVENTS_FILENAME,
)
from src.risk_layer.alerting.alert_types import AlertSeverity
from src.risk_layer.alerting.channels.email_channel import EmailChannel
from tests.ops.test_full_core_current_productive_governed_continuous_cycle_orchestrator_v1 import (
    _run,
    _auth,
    _obs,
    _seed_cursor,
    CURSOR_FLOOR,
    C1_A,
    NATIVE_ID,
)
from tests.ops._current_productive_canonical_price_test_helpers_v1 import (
    okx_public_mark_price_payload_v1,
    okx_index_tickers_payload_v1,
)


def _channel(enabled=True):
    return EmailChannel(
        {
            "enabled": enabled,
            "smtp_host": "mail.example.invalid",
            "smtp_port": 587,
            "smtp_user": "test@example.invalid",
            "smtp_password": "synthetic-password",
            "from_address": "test@example.invalid",
            "to_addresses": ["test@example.invalid"],
            "use_tls": True,
        },
        min_severity=AlertSeverity.INFO,
    )


def _notices(root):
    return [json.loads(line) for line in (root / EVENTS_FILENAME).read_text().splitlines()]


def _fault_and_recovery(root):
    failure = record_runtime_notice_v1(
        evidence_root=root,
        component="TEST_SCOPE",
        run_id="run",
        reason_code="SOURCE_FAULT",
        action="Automatic recovery",
        owner_action_required=False,
        notification_kind="FAULT",
    )
    record_runtime_notice_v1(
        evidence_root=root,
        component="TEST_SCOPE",
        run_id="run",
        reason_code="RUNTIME_RECOVERY_VERIFIED",
        action="Processing resumed",
        owner_action_required=False,
        notification_kind="RECOVERED",
        extra={"incident_id": failure["event_id"], "recovery_scope": "test"},
    )


@pytest.mark.parametrize("failure_stage", ["candles", "mark", "index"])
@pytest.mark.parametrize("fault", ["timeout", "http503"])
@pytest.mark.parametrize("use_market_adapter", [False, True])
def test_actual_get_result_reaches_recovery_and_matching_email_after_progress(
    tmp_path, monkeypatch, failure_stage, fault, use_market_adapter
):
    cursor = _seed_cursor(tmp_path / "cursor", event_time=CURSOR_FLOOR)
    root = tmp_path / "evidence"
    calls, failures = [], []

    class Response:
        status = 200

        def __init__(self, url, payload):
            self.url, self.payload = url, payload

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return json.dumps(self.payload).encode()

    class Opener:
        def open(self, request, **kwargs):
            url = request.full_url
            stage = (
                "candles" if "/candles" in url else "index" if "/index-tickers" in url else "mark"
            )
            calls.append(stage)
            if stage == failure_stage and not failures:
                failures.append(stage)
                if fault == "timeout":
                    raise TimeoutError("injected HTTP timeout")
                raise HTTPError(url, 503, "unavailable", {}, io.BytesIO(b"{}"))
            if stage == "candles":
                return Response(url, _obs(C1_A).candles_payload)
            if stage == "mark":
                payload = okx_public_mark_price_payload_v1(
                    native_id=NATIVE_ID, mark_px=3500, index_px=3490
                )
                payload["data"][0].pop("idxPx")  # force the real index-tickers path
                return Response(url, payload)
            return Response(
                url, okx_index_tickers_payload_v1(index_inst_id="0G-USDT", index_px=3490)
            )

    monkeypatch.setattr(get_owner, "build_opener", lambda *args: Opener())
    transport = get_owner.FullCoreProductiveReadOnlyGetTransportV1(max_request_count=12)
    source = source_owner.LiveFreshC1ContinuousObservationSourceV1(
        cursor_store_root=cursor,
        evidence_root=root,
        run_id="injected-http",
        native_id=NATIVE_ID,
        transport=transport,
    )
    observed_marks = []

    def runner(**kwargs):
        mark = kwargs.pop("mark_price_payload")
        index = kwargs.pop("index_tickers_payload")
        captured_at = kwargs.pop("mark_acquired_at_utc")
        assert captured_at
        observed_marks.append(
            build_cmc_mark_provenance_from_okx_mark_price_payload_v1(
                mark_price_payload=mark,
                venue_native_id=NATIVE_ID,
                index_from_index_tickers=index,
                mark_acquired_at_utc=captured_at,
            )
        )
        # S5/T2 fixture is injected: this proves the recovery wiring/cursor,
        # not a venue run or the complete MV2 strategy/position-management host.
        return run_current_productive_governed_cycle_v1(**kwargs)

    result = _run(
        tmp_path,
        cursor_store_root=cursor,
        observation_source=source,
        authorization=_auth(max_cycles_per_run=1),
        s5_runner=runner if use_market_adapter else None,
    )
    assert result.cycles_completed == result.s5_invoke_count == 1
    assert len(observed_marks) == int(use_market_adapter)
    assert result.post_count == result.external_effect_count == 0
    assert result.permit_created is False
    assert failures == [failure_stage] and calls.count(failure_stage) == 2
    assert transport.request_count == len(calls) <= transport.max_request_count
    events = _notices(root)
    failure = next(e for e in events if e["notification_kind"] == "FAULT")
    recovery = next(e for e in events if e["notification_kind"] == "RECOVERED")
    assert recovery["extra"]["incident_id"] == failure["event_id"]
    assert (
        recovery["extra"]["cursor_sha256"]
        == sha256(
            (cursor / "current_productive_sidestate_confirmation_cursor_v1.json").read_bytes()
        ).hexdigest()
    )
    channel, sent = _channel(), []

    async def send(event):
        sent.append(event)
        return True

    monkeypatch.setattr(channel, "send", send)
    receipt = asyncio.run(
        mail.process_runtime_recovery_emails_v1(evidence_root=root, channel=channel, deliver=True)
    )
    assert len(receipt["transport_accepted"]) == len(sent) == 2
    assert sent[1].context["status"] == "Wiederherstellung bestätigt"
    again = asyncio.run(
        mail.process_runtime_recovery_emails_v1(evidence_root=root, channel=channel, deliver=True)
    )
    assert len(again["transport_accepted"]) == 2 and len(sent) == 2


@pytest.mark.parametrize(
    "status,error", [(401, "AUTH_FAILURE"), (429, "HTTP_ERROR"), (200, "MALFORMED_JSON")]
)
def test_non_network_failure_is_not_reported_as_recovered(status, error):
    from types import SimpleNamespace

    with pytest.raises(ValueError, match="FRESH_C1_PUBLIC_GET_REJECTED"):
        source_owner._raise_known_get_failure_v1(
            SimpleNamespace(get_performed=False, http_status=status, error_class=error)
        )


def test_mail_failure_is_pending_and_budget_survives_reinvocation(tmp_path, monkeypatch):
    _fault_and_recovery(tmp_path)
    channel, sent = _channel(), []

    async def fail(event):
        sent.append(event.event_id)
        return False

    monkeypatch.setattr(channel, "send", fail)
    for _ in range(3):
        result = asyncio.run(
            mail.process_runtime_recovery_emails_v1(
                evidence_root=tmp_path, channel=channel, deliver=True
            )
        )
        assert len(result["pending"]) == 2 and not result["transport_accepted"]
    result = asyncio.run(
        mail.process_runtime_recovery_emails_v1(
            evidence_root=tmp_path, channel=channel, deliver=True
        )
    )
    assert len(result["exhausted"]) == 2 and len(sent) == 6


@pytest.mark.parametrize("deliver,enabled", [(False, True), (True, False)])
def test_preview_and_disabled_channel_never_send_or_claim_delivery(
    tmp_path, monkeypatch, deliver, enabled
):
    _fault_and_recovery(tmp_path)
    channel = _channel(enabled)
    monkeypatch.setattr(channel, "send", lambda _: pytest.fail("unexpected send"))
    result = asyncio.run(
        mail.process_runtime_recovery_emails_v1(
            evidence_root=tmp_path, channel=channel, deliver=deliver
        )
    )
    assert len(result["pending"]) == 2 and not result["transport_accepted"]


def test_recovery_with_foreign_incident_is_not_emailed(tmp_path):
    record_runtime_notice_v1(
        evidence_root=tmp_path,
        component="test",
        run_id="run",
        reason_code="RUNTIME_RECOVERY_VERIFIED",
        action="claim",
        owner_action_required=False,
        notification_kind="RECOVERED",
        extra={"incident_id": "nonexistent"},
    )
    with pytest.raises(ValueError, match="CAUSAL_INCIDENT_UNPROVEN"):
        asyncio.run(
            mail.process_runtime_recovery_emails_v1(
                evidence_root=tmp_path, channel=_channel(), deliver=True
            )
        )


def test_real_email_channel_uses_verified_tls_and_receives_both_notice_kinds(tmp_path, monkeypatch):
    _fault_and_recovery(tmp_path)
    server = MagicMock()
    server.__enter__.return_value = server
    monkeypatch.setattr(
        "src.risk_layer.alerting.channels.email_channel.smtplib.SMTP", lambda *a, **k: server
    )
    result = asyncio.run(
        mail.process_runtime_recovery_emails_v1(
            evidence_root=tmp_path, channel=_channel(), deliver=True
        )
    )
    assert len(result["transport_accepted"]) == server.send_message.call_count == 2
    assert server.starttls.call_args.kwargs["context"].verify_mode == ssl.CERT_REQUIRED
    assert not result["operator_read_receipt_proven"]


@pytest.mark.parametrize("stage", ["cycle", "cursor"])
def test_successful_poll_without_completed_processing_cannot_report_recovery(
    tmp_path, monkeypatch, stage
):
    from tests.ops.test_current_productive_runtime_liveness_v1 import FailingThenSource
    from src.ops.full_core_live_path_composition_root_v1 import (
        current_productive_governed_continuous_cycle_orchestrator_v1 as sequencer,
    )

    source = FailingThenSource([TimeoutError()])

    def fail(*args, **kwargs):
        raise OSError("injected incomplete processing")

    kwargs = {"s5_runner": fail} if stage == "cycle" else {}
    if stage == "cursor":
        monkeypatch.setattr(sequencer, "_advance_persisted_c1_cursor_floor_v1", fail)
    with pytest.raises(OSError):
        _run(tmp_path, observation_source=source, **kwargs)
    assert not any(e["notification_kind"] == "RECOVERED" for e in _notices(tmp_path / "evidence"))


def test_absent_smtp_password_keeps_both_emails_pending(tmp_path, monkeypatch):
    _fault_and_recovery(tmp_path)
    cfg = tmp_path / "settings.json"
    cfg.write_text(
        json.dumps(
            {
                "enabled": True,
                "smtp_host": "mail.example.invalid",
                "smtp_port": 587,
                "smtp_user": "test@example.invalid",
                "from_address": "test@example.invalid",
                "to_addresses": ["test@example.invalid"],
                "password_env_var": "PEAKTRADE_TEST_ABSENT_SMTP_PASSWORD",
            }
        )
    )
    monkeypatch.delenv("PEAKTRADE_TEST_ABSENT_SMTP_PASSWORD", raising=False)
    channel = mail.build_recovery_email_channel_v1(cfg)
    assert not channel.is_enabled()
    result = asyncio.run(
        mail.process_runtime_recovery_emails_v1(
            evidence_root=tmp_path, channel=channel, deliver=True
        )
    )
    assert len(result["pending"]) == 2 and not result["transport_accepted"]


def test_corrupt_delivery_receipt_does_not_resend_or_overwrite(tmp_path, monkeypatch):
    _fault_and_recovery(tmp_path)
    channel, calls = _channel(), []

    async def accept(event):
        calls.append(event)
        return True

    monkeypatch.setattr(channel, "send", accept)
    asyncio.run(
        mail.process_runtime_recovery_emails_v1(
            evidence_root=tmp_path, channel=channel, deliver=True
        )
    )
    receipt = next((tmp_path / "runtime_recovery_email_delivery_v1").glob("*/*.json"))
    receipt.write_text("{}")
    with pytest.raises(ValueError, match="DELIVERY_STATE_UNPROVEN"):
        asyncio.run(
            mail.process_runtime_recovery_emails_v1(
                evidence_root=tmp_path, channel=channel, deliver=True
            )
        )
    assert len(calls) == 2 and receipt.read_text() == "{}"
