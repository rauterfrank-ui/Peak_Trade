"""Whole-Core completion package v1 — egress proof + Q0/Q1 authority ratification."""

from __future__ import annotations

import json
from pathlib import Path

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    POST_ALLOWED,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_treasury_single_source_capital_handoff_v1 import (
    FULL_CORE_PRODUCTIVE_EQUITY_OBSERVATION_OWNER_COUNT,
    TREASURY_AND_DIRECT_GET_PARALLEL_ACTIVE,
)
from src.ops.pre_external_to_external_effect_boundary_bounded_wp_v1 import (
    INTENTIONALLY_ISOLATED_OWNER_GO_POST_SLICES,
    prove_pre_external_to_external_effect_boundary_v1,
)
from src.ops.whole_system_connection_closure_bounded_wp_v1.proof_v1 import (
    prove_whole_system_connection_closure_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT = REPO_ROOT / "config/governance/whole_core_completion_egress_q0_authority_v1.json"
ONE_SHOT_SLICE = (
    "src/ops/full_core_live_path_composition_root_v1/"
    "current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1.py"
)


def _load_contract() -> dict:
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def test_governance_contract_pins() -> None:
    payload = _load_contract()
    assert payload["pinned_against_main_sha"] == "9647cb7bbab8137d1db1f47cf053ab6fcb7057a9"
    assert payload["f02_fresh_trusted_q0"]["status"] == (
        "CLOSED_FOR_ENTER_LIVE_TREASURY_SINGLE_SOURCE_PATH"
    )
    assert payload["f02_fresh_trusted_q0"]["new_owner_decision_required"] is False
    rat = payload["productive_authority_ratification"]
    assert rat["current_productive_q0_owner"] == (
        "ops.governed_productive_account_equity_authority_producer_v1"
    )
    assert rat["current_productive_q1_owner"] == "src.governance.capital_risk_sizing_v1"
    assert rat["current_productive_q1_owner_count"] == 1
    assert rat["current_productive_q6_owner"] == "NONE"
    assert rat["current_productive_q8_owner"] == "NONE"
    assert rat["learning_productive_bypass_found"] is False
    c2 = payload["c2_clarification"]
    assert c2["c2_status"] == "UNRESOLVED"
    assert c2["c2_blocks_current_q0_q1"] is False
    assert c2["c2_blocks_treasury"] is False


def test_f01_one_shot_slice_classified_isolated_owner_go() -> None:
    assert ONE_SHOT_SLICE in INTENTIONALLY_ISOLATED_OWNER_GO_POST_SLICES
    pre = prove_pre_external_to_external_effect_boundary_v1()
    assert pre.whole_system_connection_ok is True
    assert pre.ok is True, (
        f"guard={pre.guard_failures} unclassified={pre.unclassified_sink_callers}"
    )
    assert pre.unclassified_sink_callers == ()


def test_whole_core_forward_and_standing_gates() -> None:
    whole = prove_whole_system_connection_closure_v1()
    assert whole.ok is True
    assert EXTERNAL_EFFECT_AUTHORIZED is False
    assert POST_ALLOWED is False
    assert FULL_CORE_PRODUCTIVE_EQUITY_OBSERVATION_OWNER_COUNT == 1
    assert TREASURY_AND_DIRECT_GET_PARALLEL_ACTIVE is False
