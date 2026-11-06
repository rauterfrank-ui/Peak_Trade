"""Proof: stale construction blockers follow the current permit-boundary remainder."""

from __future__ import annotations

import inspect
from dataclasses import replace

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    DECISION_OWNER,
    EXTERNAL_EFFECT_AUTHORIZED,
    LIVE_ARMED,
    LIVE_ENABLED,
    LIVE_EXECUTION_PORT_CONSTRUCTIBLE,
    LIVE_EXECUTION_PORT_CONSTRUCTION_REMAINDER_CLOSED,
    POST_ALLOWED,
    REAL_VENUE_POST_ALLOWED,
    WIRE_SEND_PERMITTED,
    current_productive_first_real_blocker_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_occupancy_classify_and_c1_gate_v1 import (
    POST_NEXT_OWNER_GO,
)
from src.ops.full_core_live_path_composition_root_v1.live_execution_port_construction_admission_v1 import (
    evaluate_live_execution_port_construction_admission_v1,
)
from src.ops.full_core_live_path_composition_root_v1.submission_authorized_v1 import (
    STEP_29Q_PLAN_ONLY,
)
from src.ops.governed_productive_account_equity_authority_producer_v1 import (
    current_productive_29p_common_epoch_handoff_v1 as handoff_mod,
)
from src.ops.governed_productive_account_equity_authority_producer_v1 import (
    current_productive_eea_universe_inventory_to_cap24_and_29p_v1 as eea_mod,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_common_epoch_handoff_v1 import (
    compose_current_productive_29p_common_epoch_handoff_v1,
)
from src.ops.single_selected_future_runtime_binding_v1.constants_v1 import (
    MAX_POSITIONS_EFFECTIVE,
)
from tests.ops.test_full_core_current_productive_29p_common_epoch_handoff_v1 import (
    CountingInjectedFreshGetTransportV1,
    _bound,
    _identity_payloads,
)

_STALE = "LIVE_EXECUTION_PORT_CONSTRUCTION_REMAINS_FORBIDDEN"
_PERMIT_OWNER_GO = (
    "OWNER_GO_CURRENT_PRODUCTIVE_ACTUAL_VENUE_POST_WITH_FRESH_ENVELOPE_BOUND_SINGLE_USE_PERMIT_V1"
)
_FORBIDDEN_EFFECTS = (
    "issue_external_effect_permit_v1",
    "construct_live_execution_port_v1",
    "post_trade_order",
    "build_k1_okx_venue_auth_headers_v1",
)


def _admissible_handoff():
    transport = CountingInjectedFreshGetTransportV1(
        payloads=_identity_payloads(instrument_id="0G-USDT-SWAP")
    )
    handoff = compose_current_productive_29p_common_epoch_handoff_v1(
        decision_epoch="2026-09-22T08:00:00Z",
        bound_instrument=_bound(),
        fresh_get_transport=transport,
        inst_type="SWAP",
    )
    return replace(
        handoff,
        lab_trusted=True,
        instrument_bound=True,
        eligibility=object(),
        observation=object(),
        produced=True,
        evaluator_29p=True,
    )


def test_both_ladders_consume_current_first_real_blocker_not_stale_construction() -> None:
    assert LIVE_EXECUTION_PORT_CONSTRUCTION_REMAINDER_CLOSED is True
    assert LIVE_EXECUTION_PORT_CONSTRUCTIBLE is True
    standing = current_productive_first_real_blocker_v1()
    assert standing != _STALE
    assert POST_NEXT_OWNER_GO == _PERMIT_OWNER_GO

    blocker, cls = handoff_mod._first_blocker_from_handoff_v1(
        handoff=_admissible_handoff(),
        productive_contact=True,
    )
    assert blocker == standing
    assert cls == "E"
    assert handoff_mod.POST_NEXT_OWNER_GO == _PERMIT_OWNER_GO

    eea_blocker, eea_cls, eea_next = eea_mod.resolve_post_29p_current_execution_blocker_v1()
    assert eea_blocker == standing
    assert eea_cls == "E"
    assert eea_next == _PERMIT_OWNER_GO

    for module in (handoff_mod, eea_mod):
        source = inspect.getsource(module)
        assert _STALE not in source
        assert "current_productive_first_real_blocker_v1()" in source
        for token in _FORBIDDEN_EFFECTS:
            assert token not in source


def test_slice_does_not_mint_permit_load_credentials_or_open_external_effect() -> None:
    productive = evaluate_live_execution_port_construction_admission_v1(
        attempt_with_credentials=True,
        attempt_network_session=True,
    )
    assert productive.constructible is False
    assert "PRODUCTIVE_CONSTRUCTION_RESOURCES_FORBIDDEN" in productive.reason_codes
    assert STEP_29Q_PLAN_ONLY == "PLAN_ONLY"
    assert EXTERNAL_EFFECT_AUTHORIZED is False
    assert POST_ALLOWED is False
    assert REAL_VENUE_POST_ALLOWED is False
    assert LIVE_ENABLED is True
    assert LIVE_ARMED is True
    assert WIRE_SEND_PERMITTED is True
    assert DECISION_OWNER == (
        "trading.master_v2.integrated_offline_trading_logic_replay_v1."
        "run_integrated_offline_trading_logic_replay_v1"
    )
    assert MAX_POSITIONS_EFFECTIVE == 1
