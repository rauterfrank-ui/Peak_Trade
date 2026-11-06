"""Post-#6828 architecture closure v1 — governance ratification tests."""

from __future__ import annotations

import json
from pathlib import Path

from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    POST_ALLOWED,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_treasury_single_source_capital_handoff_v1 import (
    FULL_CORE_PRODUCTIVE_EQUITY_OBSERVATION_OWNER_COUNT,
)
from src.ops.p5_10_productive_activation_and_binding_v1.constants_v1 import (
    MAX_POSITIONS_EFFECTIVE,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
)
from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
    CANONICAL_RESTART_RECONSTRUCTABLE,
    PORTFOLIO_BUDGET_OWNER,
    RESERVATION_OWNER,
)
from src.ops.pre_external_to_external_effect_boundary_bounded_wp_v1.proof_v1 import (
    prove_pre_external_to_external_effect_boundary_v1,
)
from src.ops.ranking_universe_to_full_core_ssf_handoff_contract_v1 import (
    DOMAIN_ID,
    RESELECTION_ALLOWED,
    SELECTION_AUTHORITY_OWNER,
    TRADING_DECISION_AUTHORITY_OWNER,
    domain_ratification_descriptor_v1,
)
from src.ops.whole_system_connection_closure_bounded_wp_v1.proof_v1 import (
    prove_whole_system_connection_closure_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load(rel: str) -> dict:
    return json.loads((REPO_ROOT / rel).read_text(encoding="utf-8"))


def test_umbrella_closure_contract() -> None:
    payload = _load("config/governance/post_6828_architecture_closure_v1.json")
    assert payload["known_proven_baseline_sha"] == "7cb1c5c57bfc486449cf4da361cb621a809e6075"
    assert payload["markers"]["ARCHITECTURE_CLOSURE_PROVEN"] is True
    assert payload["markers"]["POST_ALLOWED"] is False
    assert payload["markers"]["EXTERNAL_EFFECT_AUTHORIZED"] is False


def test_wp_a_domain_ratification() -> None:
    payload = _load(
        "config/governance/universe_ranking_selection_binding_domain_ratification_v1.json"
    )
    domain = payload["domain"]
    assert domain["domain_id"] == DOMAIN_ID
    assert domain["selection_authority_owner"] == SELECTION_AUTHORITY_OWNER
    assert domain["reselection_allowed"] is False
    assert domain["ownership_closed_for_productive_scope"] is True
    desc = domain_ratification_descriptor_v1()
    assert desc.domain_id == DOMAIN_ID
    assert desc.reselection_allowed is False
    assert RESELECTION_ALLOWED is False
    assert TRADING_DECISION_AUTHORITY_OWNER in desc.trading_decision_authority_owner


def test_wp_b_c2_blocking_boundary() -> None:
    payload = _load(
        "config/governance/risk_sizing_c2_companion_blocking_boundary_ratification_v1.json"
    )
    assert payload["verdict"]["c2_verdict"] == "C2_AUTHORITY_RATIFICATION_REQUIRED"
    bb = payload["blocking_boundary"]
    assert bb["c2_blocks_q0"] is False
    assert bb["c2_blocks_q1"] is False
    assert bb["c2_blocks_treasury_enter_live"] is False
    assert bb["c2_blocks_mv2_dp"] is False
    assert bb["c2_blocks_pre_external"] is False
    assert bb["c2_blocks_external_effect"] is False


def test_wp_c_portfolio_treasury_boundary() -> None:
    payload = _load(
        "config/governance/portfolio_reservation_treasury_equity_boundary_ratification_v1.json"
    )
    owners = payload["owners"]
    assert owners["portfolio_budget_owner"] == PORTFOLIO_BUDGET_OWNER
    assert owners["reservation_owner"] == RESERVATION_OWNER
    assert owners["capital_authority_owner_count_full_core"] == 1
    assert owners["duplicate_capital_authority_count"] == 0
    flags = payload["authority_flags"]
    assert flags["can_portfolio_reservation_bypass_q0"] is False
    assert flags["can_portfolio_reservation_create_capital"] is False
    assert payload["restart"]["classification"] == "N5_ACTIVATION_REQUIREMENT"
    assert CANONICAL_RESTART_RECONSTRUCTABLE is False


def test_core_invariants_still_proven() -> None:
    whole = prove_whole_system_connection_closure_v1()
    pre = prove_pre_external_to_external_effect_boundary_v1()
    assert whole.ok is True
    assert pre.ok is True
    assert EXTERNAL_EFFECT_AUTHORIZED is False
    assert POST_ALLOWED is False
    assert MULTI_FUTURE_RUNTIME_AUTHORIZED is False
    assert MAX_POSITIONS_EFFECTIVE == 1
    assert FULL_CORE_PRODUCTIVE_EQUITY_OBSERVATION_OWNER_COUNT == 1
