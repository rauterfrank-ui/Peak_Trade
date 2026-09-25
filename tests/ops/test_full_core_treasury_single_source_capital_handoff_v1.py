"""Full-Core Treasury single-source capital handoff + enter-live integration."""

from __future__ import annotations

import pytest

from src.ops.full_core_live_path_composition_root_v1.current_productive_enter_live_29p_join_v1 import (
    join_current_productive_enter_live_29p_before_venue_plan_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_treasury_single_source_capital_handoff_v1 import (
    FULL_CORE_PRODUCTIVE_EQUITY_OBSERVATION_OWNER_COUNT,
    TREASURY_AND_DIRECT_GET_PARALLEL_ACTIVE,
)
from src.ops.full_core_live_path_composition_root_v1.treasury_interference_proof_v1 import (
    prove_treasury_bounded_full_core_reachability_v1 as prove_bounded,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.c08_treasury_observed_or_reconciled_capital_semantic_authority_closeout_contract_v1 import (
    C08_PRODUCTIVE_BINDING_AUTHORIZED,
    C08_PRODUCTIVE_BINDING_IMPLEMENTED,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.constants_v1 import (
    CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_BASE_STATUS,
)
from src.ops.single_selected_future_runtime_binding_v1.constants_v1 import (
    MAX_POSITIONS_EFFECTIVE,
)
from tests.ops.test_full_core_current_productive_enter_live_29p_join_v1 import (
    _balance_payload,
    _enter_replay,
    _host_enter_cycle,
    _injected,
    _join,
)


def test_standing_pins_and_bounded_reachability() -> None:
    assert FULL_CORE_PRODUCTIVE_EQUITY_OBSERVATION_OWNER_COUNT == 1
    assert TREASURY_AND_DIRECT_GET_PARALLEL_ACTIVE is False
    assert CURRENT_PRODUCTIVE_AVAILABLE_FOR_SIZING_BASE_STATUS == "BOUND"
    assert C08_PRODUCTIVE_BINDING_AUTHORIZED is True
    assert C08_PRODUCTIVE_BINDING_IMPLEMENTED is True
    proof = prove_bounded()
    assert proof["ok"] is True
    assert proof["TREASURY_HAS_PRODUCTIVE_CALL_GRAPH_REACHABILITY"] is True
    assert proof["TREASURY_MUTATION_AUTHORIZED"] is False
    assert proof["TREASURY_CAN_OVERRIDE_WIRE_SEND_PERMISSION"] is False
    assert int(MAX_POSITIONS_EFFECTIVE) == 1


def test_enter_live_uses_single_source_treasury_handoff() -> None:
    _, cycle_b, _ = _host_enter_cycle()
    replay = _enter_replay(cycle_b)
    result = _join(replay=replay, injected=_injected(payload=_balance_payload()))
    assert result.decision_class == "ENTER"
    assert result.get_count == 1
    assert result.status == "PASS"
    assert result.producer_output_value != ""
    assert result.step_29p_risk_admissible == "true"


def test_stale_age_fails_closed() -> None:
    _, cycle_b, _ = _host_enter_cycle()
    replay = _enter_replay(cycle_b)
    result = _join(
        replay=replay,
        injected=_injected(payload=_balance_payload(), age_seconds="99999"),
    )
    assert result.status in {"STALE", "FAIL", "UNKNOWN"}
    assert result.producer_output_status != "PRODUCED"
