"""Current-Productive ENTER Live-29P join before venue-plan. No POST."""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.current_productive_enter_live_29p_join_v1 import (
    JOIN_SEAM_ID,
    CurrentProductiveEnterLive29PInjectedGetV1,
    DECISION_ENTER,
    DECISION_HOLD,
    STATUS_FAIL,
    STATUS_MISSING,
    STATUS_NOT_CALLED_HOLD,
    STATUS_PASS,
    STATUS_STALE,
    STATUS_UNKNOWN,
    join_current_productive_enter_live_29p_before_venue_plan_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_venue_plan_v1 import (
    try_bind_current_productive_venue_plan_v1,
)
from src.ops.full_core_live_path_composition_root_v1.execution_admission_contract_v1 import (
    FreshPretradeGetStatusV1,
    LiveAccountBoundStatusV1,
)
from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
    bind_final_order_envelope_from_venue_plan_v1,
)
from src.ops.full_core_live_path_composition_root_v1.full_core_productive_http_post_transport_v1 import (
    FullCoreProductiveHttpPostError,
    FullCoreProductiveHttpTradeOrderTransportV1,
)
from src.ops.full_core_live_path_composition_root_v1.models_v1 import CompositionStatusV1
from src.ops.full_core_live_path_composition_root_v1.submission_authorized_v1 import (
    STEP_29Q_PLAN_ONLY,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_PRODUCER_IDENTITY,
    CURRENT_PRODUCTIVE_ENTER_LIVE_29P_JOIN_CREATED,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_one_runtime_cycle_after_new_finalized_1m_c1_observation_v5 import (
    OWNER_GO,
    execute_current_productive_one_runtime_cycle_after_new_finalized_1m_c1_observation_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    REUSED_BINDING_ACCOUNT_SCOPE,
)
from src.ops.single_selected_future_runtime_binding_v1.constants_v1 import (
    MAX_POSITIONS_EFFECTIVE,
)
from tests.ops.test_full_core_current_productive_envelope_bound_single_use_external_effect_send_seam_v1 import (
    _handle,
)
from tests.ops.test_full_core_current_productive_fresh_runtime_from_persisted_cursor_to_pre_external_effect_applicability_v1 import (
    _eligible_transport,
    _fresh_get_transport,
)
from tests.ops.test_full_core_current_productive_host_enter_29p_invalid_stop_price_repair_v1 import (
    _host_enter_cycle,
)
from tests.ops.test_full_core_current_productive_one_runtime_cycle_after_new_finalized_1m_c1_observation_v5 import (
    SATISFIED_TS_MS,
    _candles,
    _declared_checkout_sha,
)
from tests.ops.test_full_core_current_productive_oneshot_sidestate_confirmation_cursor_join_v1 import (
    _bound,
)
from trading.master_v2.capital_risk_sizing_offline_replay_binding_adapter_v0 import (
    CAPITAL_RISK_MODE_LIVE_ACCOUNT_BOUND,
    CAPITAL_RISK_MODE_OFFLINE_ALGEBRA,
    _DEFAULT_ACCOUNT_EQUITY,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = REPO_ROOT / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
MOT_PATH = REPO_ROOT / "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md"
SPEC_PATH = (
    REPO_ROOT
    / "docs/ops/specs"
    / "FULL_CORE_CURRENT_PRODUCTIVE_ENTER_LIVE_29P_JOIN_BEFORE_EXECUTABLE_EXTERNAL_EFFECT_V1.md"
)
ATLAS_PATH = REPO_ROOT / "docs/system_atlas/entities/catalog.yaml"
EF_HEADING = "### 11.2.1.EF FULL_CORE_CURRENT_PRODUCTIVE_ENTER_LIVE_29P_JOIN_BEFORE_EXECUTABLE_EXTERNAL_EFFECT"
PROTECTED_ALGORITHM_FILES = (
    "src/ops/single_selected_future_policy_v1/selection_v1.py",
    "src/ops/single_selected_future_policy_v1/policy_v1.py",
    "src/trading/master_v2/double_play_state.py",
    "src/trading/master_v2/double_play_entry_exit_policy_v0.py",
    "src/trading/master_v2/deterministic_scope_event_generator_v1.py",
    "config/ops/canonical_decision_runtime_config_v1.toml",
)
SEALED_CORE_MEMBERS = (
    "src/trading/master_v2/double_play_state.py",
    "src/trading/master_v2/double_play_entry_exit_policy_v0.py",
)
EPOCH = "2026-09-17T06:50:00Z"
DISTINCTIVE_EQUITY = "777.77"


def _balance_payload(*, avail_eq: str = DISTINCTIVE_EQUITY) -> dict[str, object]:
    return {
        "code": "0",
        "msg": "",
        "data": [
            {
                "uid": REUSED_BINDING_ACCOUNT_SCOPE,
                "adjEq": "800.00",
                "availEq": "999.00",
                "totalEq": "1000.00",
                "uTime": "1788042908790",
                "details": [
                    {
                        "ccy": "USDC",
                        "availEq": avail_eq,
                        "availBal": "10.00",
                        "eq": "200.00",
                        "cashBal": "11.00",
                        "uTime": "1788042908790",
                    }
                ],
            }
        ],
    }


def _injected(
    *,
    payload: dict[str, object] | None = None,
    get_performed: bool = True,
    http_status: int = 200,
    error_class: str = "",
    age_seconds: str = "1",
    lab: str = LiveAccountBoundStatusV1.TRUSTED_PRESENT.value,
    get_status: str = FreshPretradeGetStatusV1.TRUSTED_PRESENT.value,
    raw_acct_lv: str = "2",
) -> CurrentProductiveEnterLive29PInjectedGetV1:
    return CurrentProductiveEnterLive29PInjectedGetV1(
        payload=payload,
        get_performed=get_performed,
        http_status=http_status,
        error_class=error_class,
        body_sha256="a" * 64,
        observed_at=EPOCH,
        age_seconds=age_seconds,
        live_account_bound_status=lab,
        raw_acct_lv=raw_acct_lv,
        expected_account_identity=REUSED_BINDING_ACCOUNT_SCOPE,
        fresh_pretrade_get_status=get_status,
    )


def _join(*, replay, injected=None, bound=None):
    return join_current_productive_enter_live_29p_before_venue_plan_v1(
        replay=replay,
        bound_instrument=bound if bound is not None else _bound(),
        injected=injected,
        decision_epoch=EPOCH,
    )


def _assert_post_guard(result) -> None:
    assert result.post_count == "0"
    assert result.permit_created == "false"
    transport = FullCoreProductiveHttpTradeOrderTransportV1(handle=_handle())
    with pytest.raises(FullCoreProductiveHttpPostError, match="REAL_VENUE_POST_FORBIDDEN"):
        transport.post_trade_order(
            payload={"instId": "MUST_NOT_POST"},
            permit_id="eep-fixture",
            envelope_id="env-fixture",
            envelope_digest="0" * 64,
        )
    assert transport.post_count == 0


def test_created_flag_pins_and_docs() -> None:
    assert CURRENT_PRODUCTIVE_ENTER_LIVE_29P_JOIN_CREATED is True
    assert int(MAX_POSITIONS_EFFECTIVE) == 1
    assert STEP_29Q_PLAN_ONLY == "PLAN_ONLY"
    assert JOIN_SEAM_ID == "CURRENT_PRODUCTIVE_ENTER_LIVE_29P_JOIN_SEAM_V1"
    runbook = RUNBOOK.read_text(encoding="utf-8")
    mot = MOT_PATH.read_text(encoding="utf-8")
    spec = SPEC_PATH.read_text(encoding="utf-8")
    atlas = ATLAS_PATH.read_text(encoding="utf-8")
    assert EF_HEADING in runbook
    assert "EVALUATE_STEP_29P_JOINED_THIS_WP=true" in runbook
    assert (
        "FULL_CORE_CURRENT_PRODUCTIVE_ENTER_LIVE_29P_JOIN_BEFORE_EXECUTABLE_EXTERNAL_EFFECT" in mot
    )
    assert "docs_token:" in spec
    assert (
        "DOCS_TOKEN_FULL_CORE_CURRENT_PRODUCTIVE_ENTER_LIVE_29P_JOIN_"
        "BEFORE_EXECUTABLE_EXTERNAL_EFFECT_V1"
    ) in spec
    assert "CURRENT_PRODUCTIVE_ENTER_LIVE_29P_JOIN_SEAM_V1" in atlas
    for path in (*PROTECTED_ALGORITHM_FILES, *SEALED_CORE_MEMBERS):
        assert (REPO_ROOT / path).is_file()


def test_hold_does_not_call_live_29p() -> None:
    cycle_a, cycle_b, _path = _host_enter_cycle()
    assert cycle_a.replay is not None
    injected = _injected(payload=_balance_payload())
    result = _join(replay=cycle_a.replay, injected=injected)
    assert result.decision_class == DECISION_HOLD
    assert result.called is False
    assert result.get_count == 0
    assert result.status == STATUS_NOT_CALLED_HOLD
    assert result.venue_plan_authorized is True
    assert result.producer_output_value == ""
    assert result.used_offline_default_equity == "false"
    _assert_post_guard(result)
    enter = _join(replay=cycle_b.replay, injected=injected)
    assert enter.decision_class == DECISION_ENTER
    assert enter.get_count == 1


def test_enter_fresh_valid_29p_pass_feeds_canonical_sizing_once() -> None:
    _, cycle_b, _path = _host_enter_cycle()
    replay = cycle_b.replay
    assert replay is not None
    original_mode = str(replay.intermediate.capital_risk_mode)
    original_sizing = replay.intermediate.capital_risk_sizing_decision
    assert original_mode == CAPITAL_RISK_MODE_OFFLINE_ALGEBRA
    assert original_sizing is not None
    result = _join(replay=replay, injected=_injected(payload=_balance_payload()))
    assert result.decision_class == DECISION_ENTER
    assert result.called is True
    assert result.get_count == 1
    assert result.status == STATUS_PASS
    assert result.venue_plan_authorized is True
    assert result.producer_output_value == DISTINCTIVE_EQUITY
    assert result.producer_output_value != str(_DEFAULT_ACCOUNT_EQUITY)
    assert result.producer_output_status == "PRODUCED"
    assert result.step_29p_risk_admissible == "true"
    assert result.capital_risk_mode == CAPITAL_RISK_MODE_LIVE_ACCOUNT_BOUND
    assert result.used_offline_default_equity == "false"
    assert CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_PRODUCER_IDENTITY in result.reason_codes
    rebound = result.replay
    assert rebound is not None
    assert rebound is not replay
    assert str(rebound.intermediate.capital_risk_mode) == CAPITAL_RISK_MODE_LIVE_ACCOUNT_BOUND
    sizing = rebound.intermediate.capital_risk_sizing_decision
    assert sizing is not None
    assert str(getattr(sizing.outcome, "value", sizing.outcome)) == "PASS"
    assert sizing.scope_capital_envelope.available_capital == Decimal(DISTINCTIVE_EQUITY)
    assert sizing.scope_capital_envelope.available_capital != _DEFAULT_ACCOUNT_EQUITY
    status, reasons, plan = try_bind_current_productive_venue_plan_v1(
        replay=rebound,
        bound_instrument=_bound(),
        session_id="enter-live-29p-join-session",
        run_id="enter-live-29p-join-run",
        composed_epoch=EPOCH,
    )
    assert status is CompositionStatusV1.PASS, reasons
    assert plan is not None
    envelope = bind_final_order_envelope_from_venue_plan_v1(
        plan,
        admission_ref="EF_ENTER_LIVE_29P_JOIN_PASS",
        provenance_ref="CURRENT_PRODUCTIVE_MASTER_V2_VENUE_PLAN",
        creation_epoch=EPOCH,
    )
    assert envelope.envelope_id
    assert STEP_29Q_PLAN_ONLY == "PLAN_ONLY"
    _assert_post_guard(result)


def test_enter_29p_fail_closes_before_venue_plan() -> None:
    _, cycle_b, _path = _host_enter_cycle()
    result = _join(
        replay=cycle_b.replay,
        injected=_injected(payload=_balance_payload(avail_eq="0")),
    )
    assert result.decision_class == DECISION_ENTER
    assert result.called is True
    assert result.get_count == 1
    assert result.status == STATUS_FAIL
    assert result.venue_plan_authorized is False
    assert result.replay is cycle_b.replay
    assert result.used_offline_default_equity == "false"
    _assert_post_guard(result)


def test_enter_missing_stale_unknown_29p_fail_closed() -> None:
    _, cycle_b, _path = _host_enter_cycle()
    missing = _join(replay=cycle_b.replay, injected=None)
    assert missing.status == STATUS_MISSING
    assert missing.get_count == 0
    assert missing.venue_plan_authorized is False
    stale = _join(
        replay=cycle_b.replay,
        injected=_injected(payload=_balance_payload(), age_seconds="6"),
    )
    assert stale.status == STATUS_STALE
    assert stale.get_count == 1
    assert stale.venue_plan_authorized is False
    unknown = _join(
        replay=cycle_b.replay,
        injected=_injected(
            payload=None,
            get_performed=False,
            http_status=0,
            error_class="TRANSPORT_TIMEOUT",
        ),
    )
    assert unknown.status == STATUS_UNKNOWN
    assert unknown.get_count == 1
    assert unknown.venue_plan_authorized is False
    _assert_post_guard(missing)
    _assert_post_guard(stale)
    _assert_post_guard(unknown)


def test_offline_default_capital_cannot_reach_external_effect_envelope() -> None:
    _, cycle_b, _path = _host_enter_cycle()
    denied = _join(replay=cycle_b.replay, injected=None)
    assert denied.venue_plan_authorized is False
    assert denied.used_offline_default_equity == "false"
    assert denied.status == STATUS_MISSING
    lab_missing = _join(
        replay=cycle_b.replay,
        injected=_injected(
            payload=_balance_payload(),
            lab=LiveAccountBoundStatusV1.MISSING.value,
        ),
    )
    assert lab_missing.venue_plan_authorized is False
    assert lab_missing.status in {STATUS_FAIL, STATUS_MISSING, STATUS_UNKNOWN}
    assert str(_DEFAULT_ACCOUNT_EQUITY) == "10000"
    _assert_post_guard(denied)
    _assert_post_guard(lab_missing)


def test_v5_hold_skips_29p_and_enter_missing_cannot_bind_envelope(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    hold = execute_current_productive_one_runtime_cycle_after_new_finalized_1m_c1_observation_v1(
        owner_go=OWNER_GO,
        origin_main_sha=_declared_checkout_sha(),
        evidence_root=tmp_path / "hold",
        acquisition_transport=_eligible_transport(),
        fresh_get_transport=_fresh_get_transport(),
        c1_gate_payload=_candles(last_ts_ms=SATISFIED_TS_MS),
        producer_observed_at_unix=1_700_000_100.0,
    )
    hold_claims = json.loads((Path(hold.store_root) / "claims.json").read_text(encoding="utf-8"))
    assert hold_claims["STEP_29P_GET_COUNT"] == "0"
    assert hold_claims["STEP_29P_JOIN_STATUS"] == STATUS_NOT_CALLED_HOLD
    assert hold_claims["LIVE_29P_GET_CONSUMED"] == "false"
    assert hold.post_count == "0"
    assert hold.permit_created == "false"
    assert hold.final_envelope_id == ""

    _, cycle_b, _path = _host_enter_cycle()
    monkeypatch.setattr(
        "src.ops.governed_productive_account_equity_authority_producer_v1."
        "current_productive_one_runtime_cycle_after_new_finalized_1m_c1_observation_v5."
        "run_current_productive_master_v2_runtime_cycle_v1",
        lambda **_kwargs: cycle_b,
    )
    missing = execute_current_productive_one_runtime_cycle_after_new_finalized_1m_c1_observation_v1(
        owner_go=OWNER_GO,
        origin_main_sha=_declared_checkout_sha(),
        evidence_root=tmp_path / "enter-missing",
        acquisition_transport=_eligible_transport(),
        fresh_get_transport=_fresh_get_transport(),
        c1_gate_payload=_candles(last_ts_ms=SATISFIED_TS_MS),
        producer_observed_at_unix=1_700_000_100.0,
    )
    missing_claims = json.loads(
        (Path(missing.store_root) / "claims.json").read_text(encoding="utf-8")
    )
    assert missing.master_v2_decision == "enter_long" or missing_claims.get("MASTER_V2_DECISION")
    assert missing_claims["STEP_29P_JOIN_STATUS"] != STATUS_PASS
    assert missing_claims["USED_OFFLINE_DEFAULT_EQUITY"] == "false"
    assert missing.venue_plan_status == "DENY"
    assert missing.envelope_readiness == "false"
    assert missing.final_envelope_id == ""
    assert missing.post_count == "0"
    assert missing.permit_created == "false"

    passed = execute_current_productive_one_runtime_cycle_after_new_finalized_1m_c1_observation_v1(
        owner_go=OWNER_GO,
        origin_main_sha=_declared_checkout_sha(),
        evidence_root=tmp_path / "enter-pass",
        acquisition_transport=_eligible_transport(),
        fresh_get_transport=_fresh_get_transport(),
        c1_gate_payload=_candles(last_ts_ms=SATISFIED_TS_MS),
        producer_observed_at_unix=1_700_000_100.0,
        enter_live_29p_injected=_injected(payload=_balance_payload()),
    )
    pass_claims = json.loads((Path(passed.store_root) / "claims.json").read_text(encoding="utf-8"))
    assert pass_claims["STEP_29P_GET_COUNT"] == "1"
    assert pass_claims["LIVE_29P_GET_CONSUMED"] == "true"
    assert pass_claims["STEP_29P_JOIN_STATUS"] == STATUS_PASS
    assert pass_claims["LIVE_29P_PRODUCER_OUTPUT_VALUE"] == DISTINCTIVE_EQUITY
    assert pass_claims["USED_OFFLINE_DEFAULT_EQUITY"] == "false"
    assert passed.post_count == "0"
    assert passed.permit_created == "false"
