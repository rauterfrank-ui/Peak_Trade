"""Offline N1→S6→real S5/S7→cursor→mail worker. No venue or real SMTP."""

import asyncio
from dataclasses import replace
from pathlib import Path
import json
import smtplib
from unittest.mock import MagicMock

import pytest

from src.ops.n1_standing_pre_external_runtime_supervisor_v1.supervisor_v1 import (
    run_n1_standing_pre_external_supervisor_v1,
)
from src.ops.runtime_health_recovery_and_failure_injection_closure_v1.runtime_mail_worker_v1 import (
    process_mail_worker_batch_v1,
)
from src.ops.runtime_health_recovery_and_failure_injection_closure_v1.runtime_notice_v1 import (
    EVENTS_FILENAME,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_sidestate_confirmation_cursor_v1 import (
    CURSOR_FILENAME,
)
from tests.ops.test_n1_standing_pre_external_runtime_supervisor_v1 import (
    REPO,
    OWNER_GO_BASELINE_SHA,
    _seed_public_marks,
    _bootstrap_lane,
    _supervisor_config,
    _f1_m9_evaluator_factory,
    _public_rest_empty,
    _continuous_auth,
    _cursor_floor_or_zero,
    _FakeClock,
    _observation_from_closes,
    strong_uptrend_closes_v1,
    governed_productive_c1_event_ts_unix_v1,
    _fixture_rest,
)
from tests.ops.test_runtime_recovery_email_v1 import _channel


@pytest.mark.parametrize("failure_type", [TimeoutError, ConnectionError])
@pytest.mark.parametrize("permanent", [False, True])
def test_n1_source_repair_processing_and_mail_chain(tmp_path, monkeypatch, failure_type, permanent):
    _seed_public_marks(tmp_path / "public_store")
    bound, g17, pairs, native_id = _bootstrap_lane(tmp_path)
    cursor_root = Path(pairs["LANE_1"][0].lane_state_root)
    floor = _cursor_floor_or_zero(cursor_root)
    cursor_before = (cursor_root / CURSOR_FILENAME).read_bytes()
    epoch_before = json.loads(cursor_before)["trading_epoch"]
    config = _supervisor_config(tmp_path)
    clock = _FakeClock()
    t0 = governed_productive_c1_event_ts_unix_v1(offset_seconds=120.0)
    path = strong_uptrend_closes_v1(count=128)
    observations = [
        _observation_from_closes(closes=path[:106], event_ts=t0),
        _observation_from_closes(closes=path[:108], event_ts=t0 + 60),
    ]

    class Source:
        polls = 0

        def poll(self):
            self.polls += 1
            if self.polls == 1 or permanent:
                raise failure_type("synthetic source outage")
            return observations[self.polls - 2]

    source = Source()
    channel = _channel()
    smtp = MagicMock()
    smtp.__enter__.return_value = smtp
    # The notification transport itself also fails during the source outage.
    smtp.send_message.side_effect = smtplib.SMTPDataError(451, b"synthetic outage")
    monkeypatch.setattr(
        "src.risk_layer.alerting.channels.email_channel.smtplib.SMTP", lambda *a, **k: smtp
    )
    settings = {
        "mail_config_path": str(tmp_path / "unused-private-config"),
        "source_roots": [str(config.evidence_root)],
    }

    def drain():
        return asyncio.run(
            process_mail_worker_batch_v1(settings, channel_factory=lambda _: channel)
        )

    during_outage = []

    def sleep(seconds):
        if not during_outage:
            during_outage.append(drain())
            assert _cursor_floor_or_zero(cursor_root) == floor
        clock.sleep(seconds)

    result = run_n1_standing_pre_external_supervisor_v1(
        config=config,
        origin_main_sha=OWNER_GO_BASELINE_SHA,
        bound=bound,
        authorization=replace(
            _continuous_auth(native_id=native_id, max_cycles=2), expected_cursor_floor=floor
        ),
        observation_source=source,
        g17_producers=g17,
        f1_m9_cycle_evaluator=_f1_m9_evaluator_factory(tmp_path),
        repo_root=REPO,
        public_rest_fetch=_public_rest_empty,
        private_rest_fetch=_fixture_rest,
        time_fn=clock.time,
        sleep_fn=sleep,
    )
    assert during_outage[0]["pending"] == 1
    assert during_outage[0]["transport_accepted"] == 0
    events = [
        json.loads(line)
        for line in (config.evidence_root / EVENTS_FILENAME).read_text().splitlines()
    ]
    recovered = [e for e in events if e["notification_kind"] == "RECOVERED"]
    assert result.trace.post_count == 0
    if permanent:
        assert result.ok is False
        assert result.trace.governed_cycle_count == 0
        assert not recovered
        assert source.polls == 4  # Initial attempt + existing three retries.
        assert _cursor_floor_or_zero(cursor_root) == floor
        assert (cursor_root / CURSOR_FILENAME).read_bytes() == cursor_before
    else:
        assert result.ok is True
        assert result.trace.governed_cycle_count == result.trace.accepted_c1_count == 2
        assert source.polls == 3
        assert len(recovered) == 1
        fault = next(e for e in events if e["event_id"] == recovered[0]["extra"]["incident_id"])
        assert fault["notification_kind"] == "FAULT"
        assert recovered[0]["extra"]["recovery_scope"] == "FRESH_C1_DATA_PROCESSING"
        assert _cursor_floor_or_zero(cursor_root) == t0 + 60
        assert (
            json.loads((cursor_root / CURSOR_FILENAME).read_bytes())["trading_epoch"] > epoch_before
        )
        # Recovery was confirmed after the first actual S5/S7 processing step,
        # before the second later C1 advanced the durable cursor again.
        assert recovered[0]["extra"]["accepted_c1"] == t0

    smtp.send_message.side_effect = None
    delivered = drain()
    assert delivered["pending"] == delivered["exhausted"] == delivered["queue_errors"] == 0
    notices = [e for e in events if e["notification_kind"] in {"FAULT", "RECOVERED"}]
    assert delivered["transport_accepted"] == len(notices)
    send_count = smtp.send_message.call_count
    drain()  # A new worker batch must not resend accepted notices.
    assert smtp.send_message.call_count == send_count
