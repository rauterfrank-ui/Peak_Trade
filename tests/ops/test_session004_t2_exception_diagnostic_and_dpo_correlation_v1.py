"""Session-004: T2 unexpected-exception diagnostics + DPO trading-epoch correlation."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.ops.pre_external_convergence_natural_enter_reporting_v1 import (
    evaluate_natural_enter_reporting_v1,
    read_lane_trading_epoch_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1 import (
    EG_OWNER_GO,
    GET_OWNER_GO,
    OCCUPANCY_OWNER_GO,
    RUNTIME_OWNER_GO,
    T2_RUNTIME_OWNER_GO,
    CurrentProductiveGovernedCycleAuthorizationV1,
    capture_t2_unexpected_exception_evidence_v1,
)
from tests.ops.test_full_core_current_productive_governed_cycle_orchestrator_v1 import (
    CURSOR_FLOOR,
    _eg_stub,
    _run as _orchestrator_run,
)

REPO = Path(__file__).resolve().parents[2]
SESSION004 = (
    REPO
    / "evidence/research/ghv_referenced_full_system_natural_enter_pre_external_proof_v3/20261006T182600Z"
)


@pytest.mark.skipif(
    not (SESSION004 / "fresh_lane_state_root/LANE_1/ddo_learning_capture_v1.jsonl").is_file(),
    reason="Session-004 lane evidence not present",
)
def test_session004_dpo_correlates_by_trading_epoch_not_run_local_index() -> None:
    from scripts.ops.pre_external_convergence_natural_enter_reporting_v1 import (
        load_productive_live_dpo_observations_v1,
    )
    from tests.ops.test_pre_external_convergence_natural_enter_reporting_v1 import (
        _Rec,
        _dpo_line,
    )

    lane = SESSION004 / "fresh_lane_state_root"
    ddo = lane / "LANE_1/ddo_learning_capture_v1.jsonl"
    trading_epoch = read_lane_trading_epoch_v1(lane)
    assert trading_epoch == 14

    observations = load_productive_live_dpo_observations_v1(ddo)
    assert any(item.trading_epoch == 14 and "cycle:14" in item.cycle_id for item in observations)

    records = (_Rec(1, "FAIL_CLOSED"),)
    result = evaluate_natural_enter_reporting_v1(
        cycle_records=records,
        terminal_disposition="FAIL_CLOSED",
        ddo_jsonl=ddo,
        lane_state_root=lane,
    )
    assert result.dpo.get("trading_epoch") == "14"
    assert "cycle:14" in str(result.dpo.get("cycle_id") or "")
    assert result.dpo.get("decision_outcome") == "observe"
    assert result.dpo.get("dpo_ref") == "ddo.dpo:0341803b09c156139f4e25d5"
    assert result.dpo.get("s5_cycle_index") != "2"


def test_t2_unexpected_exception_captures_causal_evidence(tmp_path: Path) -> None:
    class _ProbeError(RuntimeError):
        pass

    def _boom(**_kwargs: object) -> SimpleNamespace:
        raise _ProbeError("session004_probe_failure")

    result = _orchestrator_run(tmp_path, t2_cycle_dispatch=_boom)
    assert result.reason_code == "T2_CYCLE_EXCEPTION"
    assert result.t2_consumed is False
    assert result.extra.get("exception_type") == "_ProbeError"
    assert result.extra.get("exception_message") == "session004_probe_failure"
    assert result.extra.get("t2_dispatch_stage") == "T2_DISPATCH"
    assert result.extra.get("throw_line")
    assert "traceback_frames_json" in result.extra

    ledger = json.loads(
        (tmp_path / "evidence" / "governed_cycle_orchestrator_ledger_v1.json").read_text(
            encoding="utf-8"
        )
    )
    assert ledger.get("exception_type") == "_ProbeError"
    assert ledger.get("reason_code") == "T2_CYCLE_EXCEPTION"


def test_t2_hold_path_unchanged_after_diagnostic_wiring(tmp_path: Path) -> None:
    from tests.ops.test_full_core_current_productive_governed_cycle_orchestrator_v1 import (
        _t2_hold,
    )

    result = _orchestrator_run(
        tmp_path,
        eg_cycle_dispatch=_eg_stub,
        t2_cycle_dispatch=_t2_hold,
    )
    assert result.t2_consumed is True
    assert result.disposition != "FAIL_CLOSED"


def test_live_29p_join_error_maps_to_fail_closed_reason_not_generic(tmp_path: Path) -> None:
    from src.ops.full_core_live_path_composition_root_v1.current_productive_enter_live_29p_join_v1 import (
        CurrentProductiveEnterLive29PJoinError,
    )

    def _live29p_fail(**_kwargs: object) -> SimpleNamespace:
        raise CurrentProductiveEnterLive29PJoinError("ENDPOINT_DRIFT")

    result = _orchestrator_run(tmp_path, t2_cycle_dispatch=_live29p_fail)
    assert result.reason_code == "LIVE_29P_JOIN_FAIL_CLOSED"
    assert result.t2_consumed is False
    assert "ENDPOINT_DRIFT" in (result.first_genuine_blocker or "")


def test_capture_helper_redacts_no_secrets_in_message() -> None:
    auth = CurrentProductiveGovernedCycleAuthorizationV1(
        cycle_owner_go=RUNTIME_OWNER_GO,
        get_owner_go=GET_OWNER_GO,
        eg_owner_go=EG_OWNER_GO,
        occupancy_owner_go=OCCUPANCY_OWNER_GO,
        t2_owner_go=T2_RUNTIME_OWNER_GO,
        native_id="PENG-USDT-SWAP",
        bar="1m",
        expected_cursor_floor=float(CURSOR_FLOOR),
    )
    obs = SimpleNamespace(venue_event_time=1791320340.0)
    exc = ValueError("deterministic_probe")
    payload = capture_t2_unexpected_exception_evidence_v1(
        exc,
        authorization=auth,
        observation=obs,
        evidence_root=Path("/tmp/evidence/s5"),
        cursor_store_root=Path("/tmp/lane"),
    )
    assert payload["exception_type"] == "ValueError"
    assert payload["instrument_id"] == "PENG-USDT-SWAP"
    assert payload["event_time"] == "1791320340.0"
    assert "api_secret" not in payload["exception_message"].lower()
