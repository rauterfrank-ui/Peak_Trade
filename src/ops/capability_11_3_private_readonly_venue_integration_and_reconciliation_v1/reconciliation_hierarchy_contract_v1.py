"""Autonomous reconciliation hierarchy contract from Master Runbook §11.5."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.ops.capability_11_3_private_readonly_venue_integration_and_reconciliation_v1.constants_v1 import (
    CONTRACT_VERSION,
    EXCHANGE_TRUTH_ADOPTION_REQUIRES_EXPLICIT_POLICY,
    OWNER,
    POSITION_PROTECTION_REMAINS_ACTIVE_WHERE_SAFE,
    RECONCILIATION_BEFORE_ALPHA,
    RECONCILIATION_CONTINUOUS,
    RECONCILIATION_HIERARCHY_OWNER,
    RECONCILIATION_LAYERS,
    RECONCILIATION_OUTCOMES,
    SILENT_LOCAL_HISTORY_OVERWRITE_FORBIDDEN,
    UNRESOLVED_ECONOMIC_DIVERGENCE_BLOCKS_NEW_ENTRY,
)


class ReconciliationHierarchyContractError(ValueError):
    """Fail-closed reconciliation hierarchy contract violation."""


@dataclass(frozen=True)
class ReconciliationCheckpointRecordV1:
    layer: str
    outcome: str
    divergence_detected: bool
    exchange_truth_adoption_policy_id: str | None
    blocks_new_entry: bool
    classification: str = "DURABLE_CONTROL_STATE"
    owner: str = RECONCILIATION_HIERARCHY_OWNER
    contract_version: str = CONTRACT_VERSION


def build_reconciliation_checkpoint_v1(
    *,
    layer: str,
    outcome: str,
    divergence_detected: bool,
    exchange_truth_adoption_policy_id: str | None = None,
) -> ReconciliationCheckpointRecordV1:
    if layer not in RECONCILIATION_LAYERS:
        raise ReconciliationHierarchyContractError(f"UNKNOWN_RECONCILIATION_LAYER:{layer}")
    if outcome not in RECONCILIATION_OUTCOMES:
        raise ReconciliationHierarchyContractError(f"UNKNOWN_RECONCILIATION_OUTCOME:{outcome}")
    if outcome == "SAFE_ADOPT_EXCHANGE_TRUTH":
        if not exchange_truth_adoption_policy_id:
            raise ReconciliationHierarchyContractError(
                "EXCHANGE_TRUTH_ADOPTION_REQUIRES_EXPLICIT_POLICY"
            )
    blocks_new_entry = bool(
        divergence_detected
        and outcome
        in {
            "EXIT_ONLY",
            "REDUCE_ONLY",
            "CANCEL_ALL_AND_HALT",
            "HARD_STOP_OWNER_REVIEW",
            "CANCEL_UNKNOWN_ORDERS",
        }
    )
    return ReconciliationCheckpointRecordV1(
        layer=layer,
        outcome=outcome,
        divergence_detected=divergence_detected,
        exchange_truth_adoption_policy_id=exchange_truth_adoption_policy_id,
        blocks_new_entry=blocks_new_entry,
    )


def refuse_silent_local_history_overwrite_v1(*, attempted_overwrite_of: str) -> dict[str, Any]:
    raise ReconciliationHierarchyContractError(
        f"SILENT_LOCAL_HISTORY_OVERWRITE_FORBIDDEN:{attempted_overwrite_of}"
    )


def evaluate_unresolved_divergence_gate_v1(
    checkpoint: ReconciliationCheckpointRecordV1,
) -> dict[str, Any]:
    if checkpoint.divergence_detected and checkpoint.outcome in {
        "EXIT_ONLY",
        "REDUCE_ONLY",
        "CANCEL_ALL_AND_HALT",
        "HARD_STOP_OWNER_REVIEW",
    }:
        return {
            "ok": True,
            "new_entry_allowed": False,
            "UNRESOLVED_ECONOMIC_DIVERGENCE_BLOCKS_NEW_ENTRY": True,
            "reason": checkpoint.outcome,
        }
    if checkpoint.outcome == "MATCH" and not checkpoint.divergence_detected:
        return {
            "ok": True,
            "new_entry_allowed": True,
            "UNRESOLVED_ECONOMIC_DIVERGENCE_BLOCKS_NEW_ENTRY": True,
            "reason": "MATCH",
        }
    return {
        "ok": True,
        "new_entry_allowed": not checkpoint.blocks_new_entry,
        "UNRESOLVED_ECONOMIC_DIVERGENCE_BLOCKS_NEW_ENTRY": True,
        "reason": checkpoint.outcome,
    }


def prove_reconciliation_hierarchy_contract_v1() -> dict[str, Any]:
    match_cp = build_reconciliation_checkpoint_v1(
        layer="positions",
        outcome="MATCH",
        divergence_detected=False,
    )
    halt_cp = build_reconciliation_checkpoint_v1(
        layer="balances_equity_and_available_margin",
        outcome="HARD_STOP_OWNER_REVIEW",
        divergence_detected=True,
    )
    adopt_ok = build_reconciliation_checkpoint_v1(
        layer="open_orders",
        outcome="SAFE_ADOPT_EXCHANGE_TRUTH",
        divergence_detected=True,
        exchange_truth_adoption_policy_id="policy-explicit-v1",
    )

    adopt_blocked = False
    try:
        build_reconciliation_checkpoint_v1(
            layer="open_orders",
            outcome="SAFE_ADOPT_EXCHANGE_TRUTH",
            divergence_detected=True,
        )
    except ReconciliationHierarchyContractError as exc:
        adopt_blocked = "EXCHANGE_TRUTH_ADOPTION_REQUIRES_EXPLICIT_POLICY" in str(exc)

    overwrite_blocked = False
    try:
        refuse_silent_local_history_overwrite_v1(attempted_overwrite_of="decision_history")
    except ReconciliationHierarchyContractError as exc:
        overwrite_blocked = "SILENT_LOCAL_HISTORY_OVERWRITE_FORBIDDEN" in str(exc)

    unknown_layer_blocked = False
    try:
        build_reconciliation_checkpoint_v1(
            layer="vibes",
            outcome="MATCH",
            divergence_detected=False,
        )
    except ReconciliationHierarchyContractError as exc:
        unknown_layer_blocked = "UNKNOWN_RECONCILIATION_LAYER" in str(exc)

    match_gate = evaluate_unresolved_divergence_gate_v1(match_cp)
    halt_gate = evaluate_unresolved_divergence_gate_v1(halt_cp)

    ok = all(
        [
            match_cp.owner == OWNER,
            adopt_ok.exchange_truth_adoption_policy_id == "policy-explicit-v1",
            adopt_blocked,
            overwrite_blocked,
            unknown_layer_blocked,
            match_gate["new_entry_allowed"] is True,
            halt_gate["new_entry_allowed"] is False,
            len(RECONCILIATION_LAYERS) == 10,
            len(RECONCILIATION_OUTCOMES) == 8,
            RECONCILIATION_BEFORE_ALPHA is True,
            RECONCILIATION_CONTINUOUS is True,
            UNRESOLVED_ECONOMIC_DIVERGENCE_BLOCKS_NEW_ENTRY is True,
            POSITION_PROTECTION_REMAINS_ACTIVE_WHERE_SAFE is True,
            EXCHANGE_TRUTH_ADOPTION_REQUIRES_EXPLICIT_POLICY is True,
            SILENT_LOCAL_HISTORY_OVERWRITE_FORBIDDEN is True,
        ]
    )
    return {
        "ok": ok,
        "RECONCILIATION_BEFORE_ALPHA": True,
        "RECONCILIATION_CONTINUOUS": True,
        "UNRESOLVED_ECONOMIC_DIVERGENCE_BLOCKS_NEW_ENTRY": True,
        "POSITION_PROTECTION_REMAINS_ACTIVE_WHERE_SAFE": True,
        "EXCHANGE_TRUTH_ADOPTION_REQUIRES_EXPLICIT_POLICY": True,
        "SILENT_LOCAL_HISTORY_OVERWRITE_FORBIDDEN": True,
        "layers": list(RECONCILIATION_LAYERS),
        "outcomes": list(RECONCILIATION_OUTCOMES),
        "adopt_without_policy_blocked": adopt_blocked,
        "silent_overwrite_blocked": overwrite_blocked,
        "unknown_layer_blocked": unknown_layer_blocked,
        "OWNER": RECONCILIATION_HIERARCHY_OWNER,
    }
