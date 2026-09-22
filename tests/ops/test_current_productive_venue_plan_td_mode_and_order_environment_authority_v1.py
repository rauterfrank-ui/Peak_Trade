"""Contract for the new venue-plan tdMode and order-environment authority.

The productive venue-plan binder stays unwired. Standing pins stay unchanged.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    MODE_SIMULATION,
    POST_ALLOWED,
    REAL_VENUE_POST_ALLOWED,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_venue_plan_v1 import (
    try_bind_current_productive_venue_plan_v1,
)
from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
    bind_final_order_envelope_from_venue_plan_v1,
)
from src.ops.full_core_live_path_composition_root_v1.models_v1 import CompositionStatusV1
from src.ops.full_core_live_path_composition_root_v1.venue_translation_v1 import (
    translate_core_live_intent_to_venue_plan_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_venue_plan_td_mode_and_order_environment_authority_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED_BY_THIS_MODULE,
    HELPER_PINS_ARE_NOT_THIS_AUTHORITY,
    LIVE_CAPABILITY_COMPLETE_BY_THIS_MODULE,
    LIVE_TRADING_ADMITTED_BY_THIS_MODULE,
    NOT_A_HISTORICAL_PREEXISTING_FACT,
    ORDER_ENVIRONMENT_OWNER,
    ORDER_ENVIRONMENT_TRANSFORMATION,
    ORDER_ENVIRONMENT_VOCABULARY,
    TD_MODE_OWNER,
    TD_MODE_SOURCE_CLASS,
    TD_MODE_TOKEN,
    U01_ACCTLV_AUTHORITY_REMAINS_SEPARATE,
    VENUE_PLAN_BINDING_IMPLEMENTED,
    CurrentProductiveVenuePlanInputAuthorityError,
    resolve_current_productive_order_environment_v1,
    resolve_current_productive_venue_plan_td_mode_v1,
)
from src.ops.full_core_live_path_composition_root_v1.submission_authorized_v1 import (
    STEP_29Q_PLAN_ONLY,
)
from src.ops.single_selected_future_runtime_binding_v1.constants_v1 import (
    MAX_POSITIONS_EFFECTIVE,
)
from tests.ops.test_full_core_current_productive_enter_live_29p_join_v1 import (
    _balance_payload,
    _enter_replay as _promote_enter_replay,
    _injected,
    _join,
)
from tests.ops.test_full_core_current_productive_host_enter_29p_invalid_stop_price_repair_v1 import (
    _host_enter_cycle,
)
from tests.ops.test_full_core_current_productive_oneshot_sidestate_confirmation_cursor_join_v1 import (
    _INSTRUMENT,
    _bound as _current_bound,
)

_REPO = Path(__file__).resolve().parents[2]
_AUTHORITY = (
    _REPO
    / "src/ops/full_core_live_path_composition_root_v1"
    / "current_productive_venue_plan_td_mode_and_order_environment_authority_v1.py"
)
_BINDER = (
    _REPO
    / "src/ops/full_core_live_path_composition_root_v1"
    / "current_productive_venue_plan_v1.py"
)
_TRANSLATION = _REPO / "src/ops/full_core_live_path_composition_root_v1" / "venue_translation_v1.py"
_RUNBOOK = _REPO / "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
_ONE_SHOT = (
    _REPO
    / "src/ops/full_core_live_path_composition_root_v1"
    / "current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1.py"
)


def test_new_owner_constants_are_labeled_as_new_authority() -> None:
    assert NOT_A_HISTORICAL_PREEXISTING_FACT is True
    assert TD_MODE_SOURCE_CLASS == "STATIC_VENUE_EXECUTION_POLICY"
    assert TD_MODE_OWNER == "CURRENT_PRODUCTIVE_VENUE_EXECUTION_POLICY"
    assert TD_MODE_TOKEN == "cross"
    assert ORDER_ENVIRONMENT_OWNER == "CURRENT_PRODUCTIVE_EXECUTION_MODE"
    assert ORDER_ENVIRONMENT_TRANSFORMATION == "IDENTITY"
    assert ORDER_ENVIRONMENT_VOCABULARY == (
        "SHADOW",
        "INTERNAL_SIMULATED_EXECUTION",
        "PAPER_EXCHANGE",
        "TESTNET",
        "LIVE",
    )
    assert U01_ACCTLV_AUTHORITY_REMAINS_SEPARATE is True
    assert HELPER_PINS_ARE_NOT_THIS_AUTHORITY is True
    assert VENUE_PLAN_BINDING_IMPLEMENTED is True
    assert EXTERNAL_EFFECT_AUTHORIZED_BY_THIS_MODULE is False
    assert LIVE_CAPABILITY_COMPLETE_BY_THIS_MODULE is False
    assert LIVE_TRADING_ADMITTED_BY_THIS_MODULE is False


def test_td_mode_returns_policy_token_without_copying_observation() -> None:
    assert (
        resolve_current_productive_venue_plan_td_mode_v1(
            conformance_required=False,
        )
        == "cross"
    )
    assert (
        resolve_current_productive_venue_plan_td_mode_v1(
            conformance_required=True,
            observed_td_mode="cross",
            observed_mgn_mode="cross",
        )
        == "cross"
    )


@pytest.mark.parametrize(
    ("kwargs", "reason"),
    [
        (
            {"conformance_required": True},
            "TD_MODE_OBSERVATION_MISSING",
        ),
        (
            {
                "conformance_required": True,
                "observed_td_mode": "cross",
            },
            "MGN_MODE_OBSERVATION_MISSING",
        ),
        (
            {
                "conformance_required": False,
                "observed_td_mode": "isolated",
            },
            "TD_MODE_OBSERVATION_MISMATCH",
        ),
        (
            {
                "conformance_required": False,
                "observed_td_mode": "cross",
                "observed_mgn_mode": "isolated",
            },
            "TD_MODE_MGN_MODE_CONFLICT",
        ),
        (
            {
                "conformance_required": False,
                "observed_td_mode": "  cross",
            },
            "TD_MODE_OBSERVATION_INVALID",
        ),
        (
            {
                "conformance_required": False,
                "observed_td_mode": "",
            },
            "TD_MODE_OBSERVATION_MISSING",
        ),
    ],
)
def test_td_mode_conformance_fails_closed(kwargs: dict[str, object], reason: str) -> None:
    with pytest.raises(CurrentProductiveVenuePlanInputAuthorityError) as caught:
        resolve_current_productive_venue_plan_td_mode_v1(**kwargs)  # type: ignore[arg-type]
    assert caught.value.reason_code == reason


@pytest.mark.parametrize("mode", ORDER_ENVIRONMENT_VOCABULARY)
def test_order_environment_is_identity_for_each_canonical_mode(mode: str) -> None:
    assert resolve_current_productive_order_environment_v1(execution_mode=mode) == mode


def test_live_environment_requires_exact_live_mode() -> None:
    assert resolve_current_productive_order_environment_v1(execution_mode="LIVE") == "LIVE"
    for folded in ("live", "prod", "production", "demo", "simulation", "LIVE "):
        with pytest.raises(CurrentProductiveVenuePlanInputAuthorityError) as caught:
            resolve_current_productive_order_environment_v1(execution_mode=folded)
        assert caught.value.reason_code == "ORDER_ENVIRONMENT_MODE_UNKNOWN"


@pytest.mark.parametrize(
    "alias",
    ["prod", "demo", "simulation", "paper", "shadow", "testnet", "live"],
)
def test_aliases_do_not_collapse_canonical_modes(alias: str) -> None:
    with pytest.raises(CurrentProductiveVenuePlanInputAuthorityError) as caught:
        resolve_current_productive_order_environment_v1(execution_mode=alias)
    assert caught.value.reason_code == "ORDER_ENVIRONMENT_MODE_UNKNOWN"
    assert alias not in ORDER_ENVIRONMENT_VOCABULARY


def test_missing_or_conflicting_mode_fails_closed() -> None:
    with pytest.raises(CurrentProductiveVenuePlanInputAuthorityError) as missing:
        resolve_current_productive_order_environment_v1(execution_mode=None)
    assert missing.value.reason_code == "ORDER_ENVIRONMENT_MODE_MISSING"
    with pytest.raises(CurrentProductiveVenuePlanInputAuthorityError) as conflict:
        resolve_current_productive_order_environment_v1(
            execution_mode="SHADOW",
            conflicting_mode="LIVE",
        )
    assert conflict.value.reason_code == "ORDER_ENVIRONMENT_CONFLICT"
    with pytest.raises(CurrentProductiveVenuePlanInputAuthorityError) as requested:
        resolve_current_productive_order_environment_v1(
            execution_mode="TESTNET",
            requested_environment="LIVE",
        )
    assert requested.value.reason_code == "ORDER_ENVIRONMENT_CONFLICT"


def test_authority_module_does_not_import_helper_or_u01_owners() -> None:
    source = _AUTHORITY.read_text(encoding="utf-8")
    assert "import " in source
    assert "retroactively this authority" in source
    for forbidden in (
        "current_productive_available_for_sizing_producer_v1",
        "current_productive_u01_account_mode_adapter_v1",
        "environment_namespace",
        "try_bind_current_productive_venue_plan_v1",
    ):
        assert forbidden not in source


def test_productive_venue_plan_binding_consumes_ratified_authority() -> None:
    module_name = "current_productive_venue_plan_td_mode_and_order_environment_authority_v1"
    binder = _BINDER.read_text(encoding="utf-8")
    translation = _TRANSLATION.read_text(encoding="utf-8")
    assert module_name in binder
    assert module_name in translation
    assert "resolve_current_productive_venue_plan_td_mode_v1" in binder
    assert "resolve_current_productive_order_environment_v1" in binder
    assert "order_environment=order_environment" in binder
    assert 'td_mode: str = "cross"' not in binder
    assert 'environment="simulation"' not in binder
    assert "_identity_order_environment_clordid_v1" in translation
    assert "apply_prod_demo_fold" not in translation
    for forbidden in ("REQUIRED_TD_MODE", "DEFAULT_TD_MODE", "environment_namespace"):
        assert forbidden not in binder


def test_runbook_records_new_authority_without_repairing_header_sha() -> None:
    text = _RUNBOOK.read_text(encoding="utf-8")
    assert "BOUND_ORIGIN_MAIN_SHA=0ceb48d970b6d76df0aecd82eebee9570b5e453b" in text
    assert "EPISTEMIC_CLASS=NEW_OWNER_AUTHORITY" in text
    assert "NOT_A_HISTORICAL_PREEXISTING_FACT=true" in text
    assert "VENUE_PLAN_BINDING_IMPLEMENTED=true" in text
    assert "TOKEN=cross" in text
    assert "TRANSFORMATION=IDENTITY" in text


def test_standing_pins_and_post_go_remain_unconsumed() -> None:
    assert EXTERNAL_EFFECT_AUTHORIZED is False
    assert POST_ALLOWED is False
    assert REAL_VENUE_POST_ALLOWED is False
    assert STEP_29Q_PLAN_ONLY == "PLAN_ONLY"
    assert int(MAX_POSITIONS_EFFECTIVE) == 1
    one_shot = _ONE_SHOT.read_text(encoding="utf-8")
    assert 'POST_GO_STATUS = "UNCONSUMED"' in one_shot


def _block_network(monkeypatch: pytest.MonkeyPatch) -> None:
    import socket

    def _blocked(*_args: object, **_kwargs: object) -> None:
        raise OSError("NETWORK_FAIL_CLOSED")

    monkeypatch.setattr(socket.socket, "connect", _blocked)


def _enter_replay():
    _cycle_a, cycle_b, _path = _host_enter_cycle()
    promoted = _promote_enter_replay(cycle_b)
    result = _join(replay=promoted, injected=_injected(payload=_balance_payload()))
    assert result.replay is not None
    assert result.step_29p_risk_admissible == "true"
    return result.replay


def _bind(monkeypatch: pytest.MonkeyPatch, replay, **kwargs):
    _block_network(monkeypatch)
    payload = {
        "replay": replay,
        "bound_instrument": _current_bound(),
        "session_id": "venue-plan-binding-session",
        "run_id": "venue-plan-binding-run",
        "composed_epoch": "2026-09-22T00:00:00Z",
    }
    payload.update(kwargs)
    return try_bind_current_productive_venue_plan_v1(**payload)


@pytest.mark.parametrize("mode", ORDER_ENVIRONMENT_VOCABULARY)
def test_current_venue_plan_environment_is_identity_for_each_mode(
    monkeypatch: pytest.MonkeyPatch,
    mode: str,
) -> None:
    status, reasons, plan = _bind(monkeypatch, _enter_replay(), execution_mode=mode)
    assert status is CompositionStatusV1.PASS, reasons
    assert plan is not None
    assert plan.environment == mode
    assert plan.td_mode == TD_MODE_TOKEN
    assert plan.venue_native_payload["tdMode"] == TD_MODE_TOKEN
    assert "prod" not in plan.clordid
    assert "demo" not in plan.clordid
    assert "simulation" not in plan.clordid


def test_current_live_execution_mode_binds_environment_live(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    status, reasons, plan = _bind(monkeypatch, _enter_replay(), execution_mode="LIVE")
    assert status is CompositionStatusV1.PASS, reasons
    assert plan is not None
    assert plan.environment == "LIVE"
    assert plan.td_mode == "cross"


def test_identity_modes_remain_distinguishable_on_the_current_plan(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    environments: list[str] = []
    clordids: list[str] = []
    for mode in ORDER_ENVIRONMENT_VOCABULARY:
        status, reasons, plan = _bind(monkeypatch, _enter_replay(), execution_mode=mode)
        assert status is CompositionStatusV1.PASS, reasons
        assert plan is not None
        environments.append(plan.environment)
        clordids.append(plan.clordid)
    assert environments == list(ORDER_ENVIRONMENT_VOCABULARY)
    assert len(set(clordids)) == len(ORDER_ENVIRONMENT_VOCABULARY)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"execution_mode": None},
        {"execution_mode": ""},
        {"execution_mode": "simulation"},
        {"execution_mode": "prod"},
        {"execution_mode": "demo"},
        {"execution_mode": "live"},
        {"execution_mode": MODE_SIMULATION},
        {"execution_mode": "LIVE", "conflicting_execution_mode": "SHADOW"},
        {"execution_mode": "TESTNET", "requested_environment": "LIVE"},
        {"execution_mode": "LIVE", "conformance_required": True},
        {"execution_mode": "LIVE", "observed_td_mode": "isolated"},
        {
            "execution_mode": "LIVE",
            "observed_td_mode": "cross",
            "observed_mgn_mode": "isolated",
        },
    ],
)
def test_invalid_execution_mode_or_td_conformance_yields_no_venue_plan(
    monkeypatch: pytest.MonkeyPatch,
    kwargs: dict[str, object],
) -> None:
    status, _reasons, plan = _bind(monkeypatch, object(), **kwargs)
    assert status is CompositionStatusV1.DENY
    assert plan is None


def test_legacy_td_mode_constants_do_not_select_the_current_plan_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_risk_capital_model_v1 as risk_model
    import src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 as canary

    replay = _enter_replay()
    monkeypatch.setattr(canary, "DEFAULT_TD_MODE", "isolated")
    monkeypatch.setattr(risk_model, "REQUIRED_TD_MODE", "isolated")
    status, reasons, plan = _bind(
        monkeypatch,
        replay,
        execution_mode="LIVE",
        observed_td_mode="cross",
        observed_mgn_mode="cross",
    )
    assert status is CompositionStatusV1.PASS, reasons
    assert plan is not None
    assert plan.td_mode == "cross"
    assert plan.td_mode != canary.DEFAULT_TD_MODE
    assert plan.environment == "LIVE"


def test_current_plan_preserves_decision_side_sizing_and_envelope_trading_fields(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from src.ops.full_core_live_path_composition_root_v1.composition_root_v1 import (
        compose_core_live_execution_intent_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.constants_v1 import MODE_LIVE

    replay = _enter_replay()
    status, reasons, plan = _bind(monkeypatch, replay, execution_mode="LIVE")
    assert status is CompositionStatusV1.PASS, reasons
    assert plan is not None
    assert plan.side == "buy"
    composed, compose_reasons, intent = compose_core_live_execution_intent_v1(
        replay=replay,
        bound_instrument=_current_bound(),
        mode=MODE_LIVE,
        composed_epoch="2026-09-22T00:00:00Z",
    )
    assert composed is CompositionStatusV1.PASS, compose_reasons
    assert intent is not None
    legacy_status, legacy_reasons, legacy = translate_core_live_intent_to_venue_plan_v1(
        intent,
        session_id="venue-plan-binding-session",
        run_id="venue-plan-binding-run",
        td_mode="cross",
    )
    assert legacy_status is CompositionStatusV1.PASS, legacy_reasons
    assert legacy is not None
    assert plan.instrument_id == legacy.instrument_id == _INSTRUMENT
    assert plan.side == legacy.side
    assert plan.quantity == legacy.quantity
    assert plan.order_type == legacy.order_type
    assert plan.reduce_only == legacy.reduce_only
    assert plan.td_mode == legacy.td_mode == "cross"
    assert plan.instrument_source == legacy.instrument_source == "CAP_2_4_BOUND_INSTRUMENT"
    assert plan.side_source == legacy.side_source
    assert plan.quantity_source == legacy.quantity_source
    assert plan.environment == "LIVE"
    assert legacy.environment == ""
    envelope = bind_final_order_envelope_from_venue_plan_v1(
        plan,
        admission_ref="VENUE_PLAN_BINDING_OFFLINE",
        provenance_ref="CURRENT_PRODUCTIVE_MASTER_V2_VENUE_PLAN",
        creation_epoch="2026-09-22T00:00:00Z",
    )
    assert envelope.instrument_id == plan.instrument_id
    assert envelope.side == plan.side
    assert envelope.quantity == plan.quantity
    assert envelope.order_type == plan.order_type
    assert envelope.reduce_only == plan.reduce_only
    assert envelope.td_mode == plan.td_mode
    assert envelope.client_order_id == plan.clordid


def test_no_alternative_current_enter_route_bypasses_the_binding() -> None:
    callers: list[str] = []
    for path in (_REPO / "src").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if "translate_core_live_intent_to_venue_plan_v1(" in text:
            callers.append(path.relative_to(_REPO).as_posix())
    assert sorted(callers) == [
        "src/ops/full_core_live_path_composition_root_v1/current_productive_venue_plan_v1.py",
        "src/ops/full_core_live_path_composition_root_v1/path_v1.py",
        "src/ops/full_core_live_path_composition_root_v1/venue_translation_v1.py",
    ]
    offline = (_REPO / "src/ops/full_core_live_path_composition_root_v1/path_v1.py").read_text(
        encoding="utf-8"
    )
    assert "resolve_current_productive_order_environment_v1" not in offline
    assert "run_full_core_live_path_offline_v1" in offline
    binder = _BINDER.read_text(encoding="utf-8")
    assert "run_full_core_live_path_offline_v1" not in binder
    assert "build_exact_object_flatten_plan_and_envelope_v1" not in binder
    producer_root = _REPO / "src/ops/governed_productive_account_equity_authority_producer_v1"
    enter_callers = 0
    for path in producer_root.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if "try_bind_current_productive_venue_plan_v1(" not in text:
            continue
        enter_callers += 1
        assert "translate_core_live_intent_to_venue_plan_v1" not in text
        assert "run_full_core_live_path_offline_v1" not in text
        assert 'execution_mode="LIVE"' in text
    assert enter_callers >= 1
    join = (
        _REPO
        / "src/ops/current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1"
        / "invoke_join_v1.py"
    ).read_text(encoding="utf-8")
    assert "try_bind_current_productive_venue_plan_v1(" in join
    assert "translate_core_live_intent_to_venue_plan_v1" not in join
    assert 'execution_mode="LIVE"' in join
