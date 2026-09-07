"""Owner-census matrix for forbidden §11.14 Live handoff owner reuse.

Read-only classification. Does not mint a storage owner. Does not write.
"""

from __future__ import annotations

from typing import Any

from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    FORBIDDEN_OWNER_REUSE,
    HISTORICAL_HANDOFF_OWNER_CURRENT_NONE,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_owner_bind_v1 import (
    FORBIDDEN_OWNER_REUSE_REASONS,
    bind_section_11_14_live_handoff_owner_contract_v1,
)


_OWNER_MATRIX_ROWS: tuple[dict[str, Any], ...] = (
    {
        "SYMBOL": "SECTION_11_14_LIVE_HANDOFF_OWNER",
        "canonical_source": "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md §11.14",
        "implementation_owner": HISTORICAL_HANDOFF_OWNER_CURRENT_NONE,
        "read_path": "NONE",
        "write_path": "NONE",
        "tests": "tests/ops/test_section_11_14_live_restart_handoff_owner_bind_and_retroactive_synthesis_refusal_v1.py",
        "productive_binding": False,
        "restart_semantics": "REQUIRED_OWNER_ABSENT",
        "durability_semantics": "NOT_APPLICABLE_OWNER_NONE",
        "allowed_for_section_11_14_handoff": False,
        "reason": "Current productive Live restart-handoff owner does not exist.",
    },
    {
        "SYMBOL": "DDO_DURABLE_EVIDENCE_STORAGE_OWNER",
        "canonical_source": "docs/ops/specs/DDO_DURABLE_EVIDENCE_STORAGE_OWNER_CONTRACT_V1.md",
        "implementation_owner": "DDO_DURABLE_EVIDENCE_STORAGE_OWNER",
        "read_path": "src/learning/deterministic_decision_outcome_v0/",
        "write_path": "src/learning/deterministic_decision_outcome_v0/",
        "tests": "tests/learning/test_ddo_durable_evidence_storage_owner_contract_v1.py",
        "productive_binding": False,
        "restart_semantics": "NOT_LIVE_HANDOFF",
        "durability_semantics": "OBSERVATION_LEDGER_ONLY",
        "allowed_for_section_11_14_handoff": False,
        "reason": FORBIDDEN_OWNER_REUSE_REASONS["DDO_DURABLE_EVIDENCE_STORAGE_OWNER"],
    },
    {
        "SYMBOL": "MUTATION_CRITICAL_CONTROL_STATE_STORAGE_OWNER",
        "canonical_source": (
            "src/learning/mutation_critical_control_state_storage_v1/authority_v1.py"
        ),
        "implementation_owner": "MUTATION_CRITICAL_CONTROL_STATE_STORAGE_OWNER",
        "read_path": "src/learning/mutation_critical_control_state_storage_v1/",
        "write_path": "src/learning/mutation_critical_control_state_storage_v1/wal_adapter_v1.py",
        "tests": "tests/learning/test_ddo_a1_crash_durability_proof_or_explicit_nonprovability_closure_v1.py",
        "productive_binding": False,
        "restart_semantics": "NOT_LIVE_HANDOFF",
        "durability_semantics": "HOST_CRASH_DURABILITY_UNPROVEN",
        "allowed_for_section_11_14_handoff": False,
        "reason": FORBIDDEN_OWNER_REUSE_REASONS["MUTATION_CRITICAL_CONTROL_STATE_STORAGE_OWNER"],
    },
    {
        "SYMBOL": "SECTION_11_14_EVIDENCE_PACKS",
        "canonical_source": (
            "evidence/ops/section_11_14_live_order_and_economic_evidence_ladder_v1/"
        ),
        "implementation_owner": "ops.section_11_14_live_order_and_economic_evidence_ladder_v1",
        "read_path": "evidence/ops/section_11_14_live_order_and_economic_evidence_ladder_v1/",
        "write_path": "NONE_FOR_LIVE_HANDOFF",
        "tests": "tests/ops/test_section_11_14_live_restart_reconstructed_exhaustive_offline_census_v1.py",
        "productive_binding": False,
        "restart_semantics": "FORENSIC_LADDER_ARTIFACTS_NOT_CONTROL_HANDOFF",
        "durability_semantics": "EVIDENCE_PACK_NOT_CONTROL_STATE",
        "allowed_for_section_11_14_handoff": False,
        "reason": FORBIDDEN_OWNER_REUSE_REASONS["SECTION_11_14_EVIDENCE_PACKS"],
    },
    {
        "SYMBOL": "TESTNET_CAMPAIGN_DURABLE_STATE",
        "canonical_source": (
            "src/ops/section_11_12_8_productive_campaign_run_activation_and_executable_handoff_v1/"
            "durable_campaign_state_v1.py"
        ),
        "implementation_owner": "section_11_12_8",
        "read_path": "evidence/ops/section_11_12_8_bounded_long_running_productive_testnet_campaign_now/",
        "write_path": (
            "src/ops/section_11_12_8_productive_campaign_run_activation_and_executable_handoff_v1/"
            "durable_campaign_state_v1.py::write_campaign_durable_state_v1"
        ),
        "tests": "tests/ops/test_section_11_14_live_restart_reconstructed_exhaustive_offline_census_v1.py",
        "productive_binding": False,
        "restart_semantics": "TESTNET_NOT_THIS_FIELD",
        "durability_semantics": "TESTNET_CAMPAIGN_STATE",
        "allowed_for_section_11_14_handoff": False,
        "reason": FORBIDDEN_OWNER_REUSE_REASONS["TESTNET_CAMPAIGN_DURABLE_STATE"],
    },
    {
        "SYMBOL": "PHASE_9_2_MD_DURABLE_STATE",
        "canonical_source": "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md §9.2",
        "implementation_owner": "phase_9_2",
        "read_path": "docs/evidence/",
        "write_path": "NONE_FOR_LIVE_HANDOFF",
        "tests": "tests/ops/test_section_11_14_live_restart_reconstructed_exhaustive_offline_census_v1.py",
        "productive_binding": False,
        "restart_semantics": "PHASE_9_2_MD_NOT_THIS_FIELD",
        "durability_semantics": "MARKET_DATA_OR_FIXTURE",
        "allowed_for_section_11_14_handoff": False,
        "reason": FORBIDDEN_OWNER_REUSE_REASONS["PHASE_9_2_MD_DURABLE_STATE"],
    },
    {
        "SYMBOL": "CAP_72_SIDESTATE_PERSIST",
        "canonical_source": (
            "src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1/"
            "sidestate_restore_v1.py"
        ),
        "implementation_owner": "Cap 7.2 SideState",
        "read_path": (
            "src/ops/wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1/"
            "sidestate_restore_v1.py"
        ),
        "write_path": "trading.master_v2.double_play_state",
        "tests": "tests/trading/master_v2/test_master_v2_double_play_core_wiring_restore_contract_v1.py",
        "productive_binding": False,
        "restart_semantics": "STRATEGY_LIFECYCLE_NOT_LIVE_HANDOFF",
        "durability_semantics": "SIDESTATE_PERSIST_RESTORE",
        "allowed_for_section_11_14_handoff": False,
        "reason": FORBIDDEN_OWNER_REUSE_REASONS["CAP_72_SIDESTATE_PERSIST"],
    },
    {
        "SYMBOL": "FILEGATE_KILL_SWITCH",
        "canonical_source": "src/risk_layer/kill_switch/persistence.py",
        "implementation_owner": "FILEGATE / StatePersistence",
        "read_path": "src/risk_layer/kill_switch/persistence.py",
        "write_path": "src/risk_layer/kill_switch/persistence.py::StatePersistence",
        "tests": "tests/ops/test_full_core_durable_filegate_join_seam_v1.py",
        "productive_binding": False,
        "restart_semantics": "SAFETY_GATE_NOT_LIVE_HANDOFF",
        "durability_semantics": "KILL_SWITCH_STATE",
        "allowed_for_section_11_14_handoff": False,
        "reason": FORBIDDEN_OWNER_REUSE_REASONS["FILEGATE_KILL_SWITCH"],
    },
    {
        "SYMBOL": "VENUE_OKX_EEA",
        "canonical_source": "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md venue OKX EEA",
        "implementation_owner": "VENUE_OKX_EEA",
        "read_path": "venue GET /api/v5/*",
        "write_path": "venue POST /api/v5/trade/order",
        "tests": "tests/ops/test_section_11_14_live_position_reconciled_adjudication_v1.py",
        "productive_binding": False,
        "restart_semantics": "VENUE_STATE_NOT_PEAK_TRADE_HANDOFF",
        "durability_semantics": "VENUE_AUTHORITY_OVER_VENUE_STATE_ONLY",
        "allowed_for_section_11_14_handoff": False,
        "reason": FORBIDDEN_OWNER_REUSE_REASONS["VENUE_OKX_EEA"],
    },
)


def bind_section_11_14_live_handoff_owner_census_matrix_v1() -> dict[str, Any]:
    owner_bind = bind_section_11_14_live_handoff_owner_contract_v1()
    allowed = [
        row for row in _OWNER_MATRIX_ROWS if row["allowed_for_section_11_14_handoff"] is True
    ]
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_LIVE_HANDOFF_OWNER_CENSUS_MATRIX_V1",
        "SECTION_11_14_LIVE_HANDOFF_OWNER_CURRENT": HISTORICAL_HANDOFF_OWNER_CURRENT_NONE,
        "FORBIDDEN_OWNER_REUSE": list(FORBIDDEN_OWNER_REUSE),
        "LIVE_SCOPED_IDENTITY_BOUND_CONTEMPORANEOUS_HANDOFF_OWNER_FOUND": bool(allowed),
        "ALLOWED_HANDOFF_OWNER_COUNT": len(allowed),
        "rows": [dict(row) for row in _OWNER_MATRIX_ROWS],
        "owner_bind": owner_bind,
        "NEW_STORAGE_OWNER_CREATED": False,
        "NEW_RECONCILIATION_ENGINE_CREATED": False,
        "NEW_EXECUTION_STATE_MACHINE_CREATED": False,
        "SECOND_RESTART_STATE_OWNER_CREATED": False,
    }
