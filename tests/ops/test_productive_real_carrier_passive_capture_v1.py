"""Passive real-carrier capture (CB-001/CB-002) — default OFF, armed fail-closed."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from src.ops.full_core_live_path_composition_root_v1.productive_real_carrier_passive_capture_v1 import (
    REPLAY_INPUT_ARTIFACT,
    SAME_RUN_JOIN_MANIFEST_ARTIFACT,
    RealCarrierPassiveCaptureSessionV1,
    bind_real_carrier_passive_capture_session_v1,
    build_same_run_join_manifest_v1,
    enforce_real_carrier_passive_capture_before_replay_v1,
    read_captured_replay_input_v1,
    replay_input_json_digest_v1,
    reset_real_carrier_passive_capture_session_v1,
    verify_real_carrier_capture_manifest_v1,
    write_real_carrier_pre_replay_bundle_v1,
)
from tests.trading.master_v2.test_integrated_offline_trading_logic_replay_v1 import (
    _replay_input,
)
from trading.master_v2.integrated_offline_replay_evidence_writer_v1 import (
    _jsonable,
    write_integrated_offline_replay_evidence_bundle_v1,
)
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    run_integrated_offline_trading_logic_replay_v1,
)


def test_capture_default_off_no_files(tmp_path: Path) -> None:
    replay_input = _replay_input()
    block = enforce_real_carrier_passive_capture_before_replay_v1(
        replay_input=replay_input,
        cycle_id="c1",
        replay_id="c1-master-v2",
        instrument_id="inst-x",
        selection_id="sel-1",
        binding_id="bind-digest",
        trading_epoch=1,
        market_observation_epoch=1,
        confirmation_epoch=3,
        side_state=replay_input.side_state,
        venue_event_time=100.0,
        context_reference="ctx-ref",
        input_digest=replay_input.input_digest,
        cursor_restore_status="fresh",
    )
    assert block is None
    assert list(tmp_path.iterdir()) == []


def test_armed_capture_writes_atomic_bundle(tmp_path: Path) -> None:
    replay_input = _replay_input()
    session = RealCarrierPassiveCaptureSessionV1(
        enabled=True,
        capture_armed=True,
        capture_root=tmp_path,
        run_id="run-a",
        continuous_run_id="cont-b",
    )
    token = bind_real_carrier_passive_capture_session_v1(session)
    try:
        block = enforce_real_carrier_passive_capture_before_replay_v1(
            replay_input=replay_input,
            cycle_id="c1",
            replay_id="c1-master-v2",
            instrument_id=replay_input.instrument_id,
            selection_id="sel-1",
            binding_id="bind-digest",
            trading_epoch=int(replay_input.trading_epoch),
            market_observation_epoch=int(replay_input.trading_epoch),
            confirmation_epoch=3,
            side_state=replay_input.side_state,
            venue_event_time=100.0,
            context_reference=str(replay_input.context_reference),
            input_digest=str(replay_input.input_digest),
            cursor_restore_status="fresh",
        )
        assert block is None
    finally:
        reset_real_carrier_passive_capture_session_v1(token)

    manifest = tmp_path / "MANIFEST.sha256"
    assert verify_real_carrier_capture_manifest_v1(manifest) == 0
    join = json.loads((tmp_path / SAME_RUN_JOIN_MANIFEST_ARTIFACT).read_text(encoding="utf-8"))
    assert join["cycle_id"] == "c1"
    assert join["replay_id"] == "c1-master-v2"
    assert join["run_id"] == "run-a+cont-b"
    assert join["input_digest"] == replay_input.input_digest


def test_roundtrip_replay_input_fidelity(tmp_path: Path) -> None:
    replay_input = _replay_input()
    join = build_same_run_join_manifest_v1(
        session=RealCarrierPassiveCaptureSessionV1(
            enabled=True,
            capture_armed=True,
            capture_root=tmp_path,
            run_id="r",
        ),
        replay_input=replay_input,
        cycle_id="c1",
        replay_id="c1-master-v2",
        instrument_id=replay_input.instrument_id,
        selection_id="",
        binding_id="",
        trading_epoch=int(replay_input.trading_epoch),
        market_observation_epoch=None,
        confirmation_epoch=None,
        side_state=replay_input.side_state,
        venue_event_time=None,
        context_reference=str(replay_input.context_reference),
        input_digest=str(replay_input.input_digest),
        cursor_restore_status="fresh",
    )
    write_real_carrier_pre_replay_bundle_v1(
        capture_root=tmp_path,
        replay_input=replay_input,
        join_manifest=join,
    )
    before = replay_input_json_digest_v1(replay_input)
    captured = read_captured_replay_input_v1(tmp_path)
    after = replay_input_json_digest_v1(_replay_input())
    assert json.dumps(_jsonable(replay_input), sort_keys=True) == json.dumps(
        captured, sort_keys=True
    )
    assert before == replay_input_json_digest_v1(replay_input)


def test_enabled_non_interference_replay_object_unchanged(tmp_path: Path) -> None:
    replay_input = _replay_input()
    snapshot = copy.deepcopy(replay_input)
    session = RealCarrierPassiveCaptureSessionV1(
        enabled=True,
        capture_armed=True,
        capture_root=tmp_path,
        run_id="r",
    )
    token = bind_real_carrier_passive_capture_session_v1(session)
    try:
        enforce_real_carrier_passive_capture_before_replay_v1(
            replay_input=replay_input,
            cycle_id="c1",
            replay_id="c1-master-v2",
            instrument_id=replay_input.instrument_id,
            selection_id="",
            binding_id="",
            trading_epoch=int(replay_input.trading_epoch),
            market_observation_epoch=None,
            confirmation_epoch=None,
            side_state=replay_input.side_state,
            venue_event_time=None,
            context_reference=str(replay_input.context_reference),
            input_digest=str(replay_input.input_digest),
            cursor_restore_status="fresh",
        )
        replay = run_integrated_offline_trading_logic_replay_v1(replay_input)
    finally:
        reset_real_carrier_passive_capture_session_v1(token)
    assert replay_input_json_digest_v1(replay_input) == replay_input_json_digest_v1(snapshot)
    assert replay.evidence.instrument_id == replay_input.instrument_id


def test_armed_sink_failure_fail_closed_before_replay(tmp_path: Path) -> None:
    replay_input = _replay_input()
    session = RealCarrierPassiveCaptureSessionV1(
        enabled=True,
        capture_armed=True,
        capture_root=tmp_path,
        run_id="r",
    )
    token = bind_real_carrier_passive_capture_session_v1(session)
    replay_calls: list[int] = []

    def _count_replay(_inp: object) -> object:
        replay_calls.append(1)
        return run_integrated_offline_trading_logic_replay_v1(replay_input)

    try:
        with patch(
            "src.ops.full_core_live_path_composition_root_v1."
            "productive_real_carrier_passive_capture_v1.write_real_carrier_pre_replay_bundle_v1",
            side_effect=OSError("disk full"),
        ):
            block = enforce_real_carrier_passive_capture_before_replay_v1(
                replay_input=replay_input,
                cycle_id="c1",
                replay_id="c1-master-v2",
                instrument_id=replay_input.instrument_id,
                selection_id="",
                binding_id="",
                trading_epoch=int(replay_input.trading_epoch),
                market_observation_epoch=None,
                confirmation_epoch=None,
                side_state=replay_input.side_state,
                venue_event_time=None,
                context_reference=str(replay_input.context_reference),
                input_digest=str(replay_input.input_digest),
                cursor_restore_status="fresh",
            )
        assert block is not None
        assert "REAL_CARRIER_PASSIVE_CAPTURE_FAIL_CLOSED" in block
        with patch(
            "trading.master_v2.integrated_offline_trading_logic_replay_v1."
            "run_integrated_offline_trading_logic_replay_v1",
            side_effect=_count_replay,
        ):
            if block is None:
                run_integrated_offline_trading_logic_replay_v1(replay_input)
    finally:
        reset_real_carrier_passive_capture_session_v1(token)
    assert replay_calls == []


def test_writer_roundtrip_compatible_with_evidence_bundle(tmp_path: Path) -> None:
    replay_input = _replay_input()
    replay = run_integrated_offline_trading_logic_replay_v1(replay_input)
    bundle_dir = tmp_path / "bundle"
    write_integrated_offline_replay_evidence_bundle_v1(
        out_dir=bundle_dir,
        replay_input=replay_input,
        replay_result=replay,
    )
    join = build_same_run_join_manifest_v1(
        session=RealCarrierPassiveCaptureSessionV1(
            enabled=True,
            capture_armed=True,
            capture_root=tmp_path / "capture",
            run_id="r",
        ),
        replay_input=replay_input,
        cycle_id="c1",
        replay_id="c1-master-v2",
        instrument_id=replay_input.instrument_id,
        selection_id="",
        binding_id="",
        trading_epoch=int(replay_input.trading_epoch),
        market_observation_epoch=None,
        confirmation_epoch=None,
        side_state=replay_input.side_state,
        venue_event_time=None,
        context_reference=str(replay_input.context_reference),
        input_digest=str(replay_input.input_digest),
        cursor_restore_status="fresh",
    )
    cap_root = tmp_path / "capture"
    write_real_carrier_pre_replay_bundle_v1(
        capture_root=cap_root,
        replay_input=replay_input,
        join_manifest=join,
    )
    passive = json.loads((cap_root / REPLAY_INPUT_ARTIFACT).read_text(encoding="utf-8"))
    bundle = json.loads((bundle_dir / REPLAY_INPUT_ARTIFACT).read_text(encoding="utf-8"))
    assert passive == bundle
