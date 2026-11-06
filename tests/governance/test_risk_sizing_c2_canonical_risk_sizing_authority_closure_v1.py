"""C2 + canonical Risk/Sizing authority closure v1 — governance ratification tests."""

from __future__ import annotations

import json
from pathlib import Path

from src.governance.capital_risk_sizing_v1 import CONTRACT_NAME as CRS_CONTRACT_NAME
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    LIVE_ARMED,
    LIVE_ENABLED,
    POST_ALLOWED,
    WIRE_SEND_PERMITTED,
)
from src.ops.p5_10_productive_activation_and_binding_v1.constants_v1 import (
    MAX_POSITIONS_EFFECTIVE,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
)
from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
    PORTFOLIO_BUDGET_OWNER,
)
from src.ops.pre_external_to_external_effect_boundary_bounded_wp_v1.proof_v1 import (
    prove_pre_external_to_external_effect_boundary_v1,
)
from src.ops.ranking_universe_to_full_core_ssf_handoff_contract_v1 import (
    SELECTION_AUTHORITY_OWNER,
    TRADING_DECISION_AUTHORITY_OWNER,
)
from src.ops.whole_system_connection_closure_bounded_wp_v1.proof_v1 import (
    prove_whole_system_connection_closure_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CLOSURE_JSON = (
    REPO_ROOT
    / "config"
    / "governance"
    / "risk_sizing_c2_canonical_risk_sizing_authority_closure_v1.json"
)
FREEZE_JSON = (
    REPO_ROOT / "config" / "governance" / "risk_sizing_authority_decision_contract_freeze_v1.json"
)
INVENTORY_JSON = REPO_ROOT / "config" / "governance" / "risk_sizing_owner_inventory_ssot_v1.json"
WHOLE_CORE_JSON = (
    REPO_ROOT / "config" / "governance" / "whole_core_completion_egress_q0_authority_v1.json"
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_closure_contract_ratifies_canonical_owner_and_c2_roles() -> None:
    payload = _load(CLOSURE_JSON)
    assert payload["workpackage_id"] == "C2_CANONICAL_RISK_SIZING_AUTHORITY_CLOSURE_V1"
    assert payload["authority_closure_case"] == "CASE_B_MECHANICAL_CONTRACT_GAP"
    assert payload["owner_decision_required"] is False
    verdict = payload["verdict"]
    assert verdict["canonical_risk_sizing_owner"] == "src.governance.capital_risk_sizing_v1"
    assert verdict["canonical_risk_sizing_owner_count"] == 1
    assert verdict["c2_verdict"] == "C2_AUTHORITY_ROLE_RATIFIED"
    assert verdict["conversion_ready"] is True
    inv = payload["authority_invariants"]
    assert inv["canonical_risk_sizing_owner_count"] == 1
    assert inv["duplicate_risk_sizing_authority_count"] == 0
    assert inv["companion_full_core_authority_conflict_count"] == 0
    c2 = payload["companion_c2"]
    assert c2["c2_current_companion_reachable"] is True
    assert c2["c2_current_full_core_reachable"] is False
    assert c2["c2_current_external_effect_reachable"] is False
    assert c2["c2_blocks_current_n1_core"] is False
    assert c2["fraction_authority_owner"] == "COMPANION_SESSION_POSITION_FRACTION_CONFIG_SURFACE_V1"
    assert (
        c2["fraction_to_units_owner"] == "COMPANION_SHADOW_LIVE_FRACTION_TO_UNITS_INPUT_BINDING_V1"
    )
    assert c2["fraction_to_units_runtime_implemented"] is False
    assert c2["c2_input_domains_proven_current_count"] == 3


def test_closure_aligns_with_q1_whole_core_and_inventory() -> None:
    closure = _load(CLOSURE_JSON)
    whole = _load(WHOLE_CORE_JSON)
    inventory = _load(INVENTORY_JSON)
    freeze = _load(FREEZE_JSON)
    owner = "src.governance.capital_risk_sizing_v1"
    assert whole["productive_authority_ratification"]["current_productive_q1_owner"] == owner
    assert closure["canonical_risk_sizing"]["owner"] == owner
    assert inventory["markers"]["CANONICAL_RISK_SIZING_OWNER"] == owner
    assert inventory["markers"]["CANONICAL_RISK_SIZING_OWNER_COUNT"] == 1
    assert inventory["markers"]["DUPLICATE_CANONICAL_RISK_SIZING_AUTHORITY_COUNT"] == 0
    assert freeze["markers"]["CANONICAL_RISK_SIZING_OWNER"] == owner
    assert CRS_CONTRACT_NAME == "capital_risk_sizing_v1"


def test_closure_preserves_core_authority_pins_and_safety_seams() -> None:
    closure = _load(CLOSURE_JSON)
    pins = closure["safety_pins"]
    assert pins["live_enabled"] is True
    assert pins["live_armed"] is True
    assert pins["wire_send_permitted"] is True
    assert pins["post_allowed"] is False
    assert pins["external_effect_authorized"] is False
    assert LIVE_ENABLED is True
    assert LIVE_ARMED is True
    assert WIRE_SEND_PERMITTED is True
    assert POST_ALLOWED is False
    assert EXTERNAL_EFFECT_AUTHORIZED is False
    assert MULTI_FUTURE_RUNTIME_AUTHORIZED is False
    assert MAX_POSITIONS_EFFECTIVE == 1
    inv = closure["authority_invariants"]
    assert inv["selection_authority_owner_count"] == 1
    assert inv["trading_decision_authority_owner_count"] == 1
    assert SELECTION_AUTHORITY_OWNER
    assert TRADING_DECISION_AUTHORITY_OWNER
    assert PORTFOLIO_BUDGET_OWNER in closure["cross_authority_relations"]["portfolio_reservation"]
    whole = prove_whole_system_connection_closure_v1()
    pre = prove_pre_external_to_external_effect_boundary_v1()
    assert whole.ok is True
    assert pre.ok is True


def test_companion_producers_still_pass_fraction_to_signal_to_orders() -> None:
    shadow = (REPO_ROOT / "src/live/shadow_session.py").read_text(encoding="utf-8")
    live = (REPO_ROOT / "src/execution/live_session.py").read_text(encoding="utf-8")
    pipeline = (REPO_ROOT / "src/execution/pipeline.py").read_text(encoding="utf-8")
    assert "position_size = self._shadow_cfg.position_fraction" in shadow
    assert "position_size=self._config.position_fraction" in live
    assert "position_size: Gewuenschte Positionsgroesse (in Stueck)" in pipeline
