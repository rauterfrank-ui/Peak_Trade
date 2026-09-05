"""Offline full-chain proof: Replay owners produce CanonicalOrderIntent, then Core→Live halt."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest

from src.governance.canonical_order_intent_v1 import IntentAction
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    CANARY_DEFAULT_INSTRUMENT_ID,
    CANARY_DEFAULT_SIDE,
    CURRENT_LIVE_CORE_PATH_PROVEN,
    FULL_CORE_SYSTEM_E2E_PROVEN,
    MODE_TEST,
    PATH_KIND,
)
from src.ops.full_core_live_path_composition_root_v1.models_v1 import (
    FrozenPretradeEvidenceV1,
    FullCoreLivePathInputV1,
)
from src.ops.full_core_live_path_composition_root_v1.path_v1 import (
    run_full_core_live_path_offline_v1,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1
from tests.trading.master_v2.test_integrated_offline_trading_logic_replay_v1 import _INSTRUMENT
from tests.trading.master_v2.test_master_v2_integrated_replay_safety_before_intent_restore_contract_v1 import (
    _confirmed_replay_input,
    _patch_replay_owners,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import DecisionOutcome
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    run_integrated_offline_trading_logic_replay_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
PATH_MODULE = REPO_ROOT / "src/ops/full_core_live_path_composition_root_v1/path_v1.py"


def test_offline_full_chain_from_core_not_injected_intent(monkeypatch: pytest.MonkeyPatch) -> None:
    order, counts = _patch_replay_owners(monkeypatch)
    replay = run_integrated_offline_trading_logic_replay_v1(_confirmed_replay_input(side="LONG"))
    assert replay.evidence.decision_outcome == DecisionOutcome.ENTER_LONG.value
    assert order == ["29P", "SAFETY", "29Q", "RECON", "KS"]
    assert counts["29P"] == 1
    assert counts["SAFETY"] == 1
    assert counts["29Q"] == 1
    intent = replay.intermediate.canonical_order_intent
    assert intent is not None
    assert intent.intent_action == IntentAction.ENTER_LONG.value
    assert intent.instrument_id == _INSTRUMENT
    assert intent.instrument_id != CANARY_DEFAULT_INSTRUMENT_ID
    assert intent.quantity > 0
    assert intent.submission_authorized is False
    assert intent.execution_eligible is False

    bound = BoundInstrumentV1(
        instrument_id=_INSTRUMENT,
        venue_native_id=_INSTRUMENT,
        ranking_snapshot_id="rank-full-chain",
        ranking_integrity_digest="rank-full-chain-digest",
        universe_snapshot_id="uni-full-chain",
        selection_id="sel-full-chain",
        selection_integrity_digest="sel-full-chain-digest",
        selection_state="SELECTED",
    )
    frozen = FrozenPretradeEvidenceV1(
        max_available=Decimal("10"),
        max_size=Decimal("10"),
        available_margin_ok=True,
        price_band_ok=True,
        instrument_state_ok=True,
        account_mode_ok=True,
        pos_mode_ok=True,
        margin_mode_ok=True,
        leverage_ok=True,
    )
    result = run_full_core_live_path_offline_v1(
        FullCoreLivePathInputV1(
            replay=replay,
            bound_instrument=bound,
            frozen_pretrade=frozen,
            mode=MODE_TEST,
            composed_epoch="1",
            owner_go="OWNER_GO_FULL_CORE_LIVE_PATH_OFFLINE_V1",
        )
    )
    assert result.canonical_intent is intent
    assert result.intent is not None
    assert result.intent.source_semantic_digest == intent.semantic_digest
    assert result.intent.quantity == intent.quantity
    assert result.intent.side == intent.side
    assert result.intent.path_kind == PATH_KIND
    assert result.venue_plan is not None
    assert result.venue_plan.instrument_id == _INSTRUMENT
    assert result.venue_plan.side == "buy"
    assert result.venue_plan.side.upper() != CANARY_DEFAULT_SIDE or intent.intent_action == (
        IntentAction.ENTER_LONG.value
    )
    assert result.venue_plan.quantity == str(intent.quantity)
    assert result.venue_plan.quantity_source == "STEP_29Q_CANONICAL_ORDER_INTENT"
    assert result.venue_plan.side_source == "STEP_29Q_CANONICAL_ORDER_INTENT"
    assert result.venue_plan.instrument_source == "CAP_2_4_BOUND_INSTRUMENT"
    assert result.venue_plan.path_kind == PATH_KIND
    assert "minSz" not in result.venue_plan.quantity_source
    assert result.pretrade is not None
    assert result.pretrade.core_intent_valid is True
    assert result.pretrade.instrument_binding_valid is True
    assert result.pretrade.pretrade_valid is True
    assert result.pretrade.live_enabled is False
    assert result.pretrade.wire_send_permitted is False
    assert result.boundary is not None
    assert result.boundary.halt_before_wire is True
    assert result.wire_send_occurred is False
    assert "EXECUTION_DISABLED" in result.reason_codes
    assert "EXECUTION_UNARMED" in result.reason_codes
    assert "WIRE_SEND_NOT_PERMITTED" in result.reason_codes
    assert result.full_core_system_e2e_proven is False
    assert result.current_live_core_path_proven is False
    assert result.full_core_restart_test_authorized is False
    assert result.canary_venue_proof_path is False
    assert "HARD_STOP_BEFORE_WIRE" in result.reason_codes
    src = PATH_MODULE.read_text(encoding="utf-8")
    assert "compose_core_live_execution_intent_v1" in src
    assert "translate_core_live_intent_to_venue_plan_v1" in src
    assert "evaluate_frozen_pretrade_conjunction_v1" in src
    assert "halt_at_live_execution_boundary_v1" in src
    assert CURRENT_LIVE_CORE_PATH_PROVEN is False
    assert FULL_CORE_SYSTEM_E2E_PROVEN is False
