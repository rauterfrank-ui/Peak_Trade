"""WP-02 offline observation / proposal / contract fence proofs."""

from __future__ import annotations

import ast
from pathlib import Path

from src.governance.offline_observation_proposal_contract_fences_v1 import (
    AUTHORITY_EFFECT,
    CAN_GRANT_AUTHORITY,
    CONTRACT_ID,
    CONTRACT_LAYERS,
    DDO_DOES_NOT_REPLACE_LEARNING_LOOP,
    DDO_ROLE,
    HOOK_PRESENCE_IS_NOT_AUTHORITY_GRANT,
    LEDGER_FAMILIES,
    LEARNING_LOOP_ALLOWED_ROLE,
    LEGACY_PROMOTION_ENGINE_ROLE,
    OWNER_GO,
    PRODUCTIVE_LEARNING_AUTHORITY,
    PRODUCTIVE_PROMOTION_AUTHORITY,
    SURFACE_M_CONSUMERS,
    SURFACE_M_ROLE,
    SURFACE_O_ROLE,
    WP02_ORDER_SCAN_PATHS,
    evaluate_offline_observation_proposal_contract_fences_v1,
)
from src.governance.promotion_loop.promotion_economic_gate_v1 import (
    AUTHORITY_EFFECT_NONE,
)
from src.learning.deterministic_decision_outcome_v0.authority_v0 import (
    AUTHORITY_OWNER,
    LEARNING_PRODUCTIVE_AUTHORITY,
    PROMOTION_AUTHORITY_ACTIVATION,
    PROMOTION_AUTHORITY_EFFECT,
    SECOND_PROMOTION_AUTHORITY_CREATED,
)
from src.learning.deterministic_decision_outcome_v0.common_v0 import SCHEMA_NAME_LEDGER_ENVELOPE
from src.meta.learning_loop.comparison_common_durable_evidence_binding_v1 import (
    COMPARISON_AUTHORITY_INVARIANTS,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
FENCE_MODULE = (
    REPO_ROOT / "src" / "governance" / "offline_observation_proposal_contract_fences_v1.py"
)
DDO_PACKAGE = REPO_ROOT / "src" / "learning" / "deterministic_decision_outcome_v0"


def test_fence_evaluate_pass_binds_adjudicated_roles() -> None:
    report = evaluate_offline_observation_proposal_contract_fences_v1()
    assert report["status"] == "PASS"
    assert report["owner_go"] == OWNER_GO
    assert report["contract_id"] == CONTRACT_ID
    assert report["authority_effect"] == AUTHORITY_EFFECT == "NONE"
    assert report["can_grant_authority"] is CAN_GRANT_AUTHORITY is False
    assert report["learning_loop_role"] == LEARNING_LOOP_ALLOWED_ROLE
    assert report["surface_o_role"] == SURFACE_O_ROLE == "OBSERVATION_ONLY"
    assert report["surface_m_role"] == SURFACE_M_ROLE == "PROMOTION_GATE_EVALUATE_ONLY"
    assert report["legacy_promotion_engine_role"] == LEGACY_PROMOTION_ENGINE_ROLE
    assert report["ddo_role"] == DDO_ROLE == "OFFLINE_OBSERVATION_ONLY"
    assert report["contract_layers"] == CONTRACT_LAYERS
    assert report["productive_learning_authority"] == PRODUCTIVE_LEARNING_AUTHORITY == "NONE"
    assert report["productive_promotion_authority"] == PRODUCTIVE_PROMOTION_AUTHORITY == "NONE"
    assert report["second_promotion_authority_created"] is False
    assert report["second_learning_authority_created"] is False
    assert report["ddo_does_not_replace_learning_loop"] is DDO_DOES_NOT_REPLACE_LEARNING_LOOP
    assert report["hook_presence_is_not_authority_grant"] is HOOK_PRESENCE_IS_NOT_AUTHORITY_GRANT
    assert report["live_authorized"] is False
    assert report["canary_authorized"] is False
    assert report["testnet_authorized"] is False
    assert report["orders_allowed"] is False
    assert report["order_submit_reachable_from_wp02"] is False


def test_surface_m_pass_does_not_grant_promotion_or_runtime() -> None:
    report = evaluate_offline_observation_proposal_contract_fences_v1()
    surface_m = report["surface_m"]
    assert surface_m["pass_eligible_for_promotion_candidate"] is True
    assert surface_m["pass_authority_effect"] == AUTHORITY_EFFECT_NONE
    assert surface_m["pass_deployment_eligible"] is False
    assert surface_m["pass_execution_allowed"] is False
    assert surface_m["current_repo_eligible"] is False
    assert surface_m["canonical_owner"] == "governance.promotion_loop.promotion_economic_gate_v1"


def test_learning_loop_comparison_and_proposal_remain_non_authorizing() -> None:
    report = evaluate_offline_observation_proposal_contract_fences_v1()
    assert COMPARISON_AUTHORITY_INVARIANTS["comparison_is_descriptive_only"] is True
    assert COMPARISON_AUTHORITY_INVARIANTS["comparison_does_not_select"] is True
    assert COMPARISON_AUTHORITY_INVARIANTS["comparison_does_not_promote"] is True
    assert COMPARISON_AUTHORITY_INVARIANTS["comparison_does_not_authorize_runtime"] is True
    assert report["learning_loop_role"] == (
        "OFFLINE_OBSERVATION_COMPARISON_PROPOSAL_CONTRACTS_ONLY"
    )


def test_legacy_engine_remains_manual_only_and_does_not_write_live_overrides() -> None:
    report = evaluate_offline_observation_proposal_contract_fences_v1()
    legacy = report["legacy_promotion_engine"]
    assert legacy["default_mode"] == "manual_only"
    assert legacy["auto_apply_as_authority"] == "DO_NOT_RESTORE"
    assert legacy["live_override_write"] is False


def test_ddo_authority_markers_and_eligibility_are_observation_only() -> None:
    report = evaluate_offline_observation_proposal_contract_fences_v1()
    ddo = report["ddo_eligibility"]
    assert AUTHORITY_OWNER == "NONE"
    assert PROMOTION_AUTHORITY_EFFECT == "NONE"
    assert PROMOTION_AUTHORITY_ACTIVATION is False
    assert LEARNING_PRODUCTIVE_AUTHORITY == "NONE"
    assert SECOND_PROMOTION_AUTHORITY_CREATED is False
    assert ddo["eligible"] is True
    assert ddo["deployment_authorized"] is False
    assert ddo["execution_authorized"] is False
    assert ddo["authority_owner"] == "NONE"


def test_ledger_families_remain_semantically_separated() -> None:
    report = evaluate_offline_observation_proposal_contract_fences_v1()
    families = report["ledger_families"]
    assert families["ddo_ledger"] == SCHEMA_NAME_LEDGER_ENVELOPE == "ddo_ledger_envelope"
    assert families["ddo_ledger"] != families["execution_accounting_ledger"]
    assert families["ddo_ledger"] != families["aiops_trend_ledger"]
    assert families["ddo_ledger"] != families["atlas_historical_child_ledger"]
    assert families["ddo_ledger"] != families["research_trade_ledger"]
    assert len(set(LEDGER_FAMILIES.values())) == len(LEDGER_FAMILIES)


def test_surface_m_consumers_exist_and_fence_does_not_submit_orders() -> None:
    for consumer in SURFACE_M_CONSUMERS:
        assert (REPO_ROOT / consumer).is_file(), consumer
    tree = ast.parse(FENCE_MODULE.read_text(encoding="utf-8"))
    called: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            called.add(node.func.attr)
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            called.add(node.func.id)
    assert not called.intersection({"submit_order", "submit_orders", "place_order", "add_order"})
    for relative in WP02_ORDER_SCAN_PATHS:
        assert (REPO_ROOT / relative).is_file(), relative


def test_ddo_package_does_not_import_learning_loop() -> None:
    for path in sorted(DDO_PACKAGE.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert not alias.name.startswith("src.meta.learning_loop"), path
            elif isinstance(node, ast.ImportFrom) and node.module:
                assert not node.module.startswith("src.meta.learning_loop"), path


def test_fence_does_not_rewrite_core_or_selection_owners() -> None:
    source = FENCE_MODULE.read_text(encoding="utf-8")
    assert "CanonicalOrderIntent" not in source
    assert "SimulatedExecutionPort" not in source
    report = evaluate_offline_observation_proposal_contract_fences_v1()
    assert report["surface_o"]["observe_only_no_mutation"] is True
