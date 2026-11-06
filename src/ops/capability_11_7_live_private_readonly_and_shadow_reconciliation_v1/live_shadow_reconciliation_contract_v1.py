"""Live shadow reconciliation contracts (§11.13 / §11.5) — fixture-only."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.ops.capability_11_7_live_private_readonly_and_shadow_reconciliation_v1.constants_v1 import (
    CAPABILITY_11_8_STARTED,
    CONTRACT_VERSION,
    EXCHANGE_TRUTH_ADOPTION_REQUIRES_EXPLICIT_POLICY,
    LIVE_PROGRESSION_STAGES_FORBIDDEN,
    LIVE_PROGRESSION_STAGES_IN_SCOPE,
    LIVE_SHADOW_RECONCILIATION_ACTIVATED,
    LIVE_SHADOW_RECONCILIATION_CONTRACT_ACTIVATED,
    LIVE_SHADOW_RECONCILIATION_CONTRACT_BOUND,
    LIVE_SHADOW_RECONCILIATION_OWNER,
    LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION_ACTIVATED,
    NO_AUTOMATIC_STAGE_PROMOTION,
    OWNER,
    OWNER_GO_REQUIRED_FOR_STAGE_PROMOTION,
    POSITION_PROTECTION_REMAINS_ACTIVE_WHERE_SAFE,
    RECONCILIATION_BEFORE_ALPHA,
    RECONCILIATION_CONTINUOUS,
    SHADOW_RECONCILIATION_LAYERS,
    SHADOW_RECONCILIATION_OUTCOMES,
    SILENT_LOCAL_HISTORY_OVERWRITE_FORBIDDEN,
    UNRESOLVED_ECONOMIC_DIVERGENCE_BLOCKS_NEW_ENTRY,
)


class LiveShadowReconciliationError(RuntimeError):
    """Fail-closed Live shadow reconciliation violation."""


@dataclass(frozen=True)
class LiveShadowReconciliationCheckpointRecordV1:
    stage: str
    layer: str
    outcome: str
    divergence_detected: bool
    exchange_truth_adoption_policy_id: str | None
    blocks_new_entry: bool
    shadow_activated: bool = False
    exchange_fetch_performed: bool = False
    source: str = "FIXTURE_ONLY"
    classification: str = "EVIDENCE_ONLY_STATE"
    owner: str = LIVE_SHADOW_RECONCILIATION_OWNER
    contract_version: str = CONTRACT_VERSION


def build_live_shadow_reconciliation_checkpoint_v1(
    *,
    stage: str,
    layer: str,
    outcome: str,
    divergence_detected: bool,
    exchange_truth_adoption_policy_id: str | None = None,
) -> LiveShadowReconciliationCheckpointRecordV1:
    if stage in LIVE_PROGRESSION_STAGES_FORBIDDEN:
        raise LiveShadowReconciliationError(
            f"CAPABILITY_11_8_SURFACE_FORBIDDEN_IN_CAPABILITY_11_7:{stage}"
        )
    if stage not in LIVE_PROGRESSION_STAGES_IN_SCOPE:
        raise LiveShadowReconciliationError(f"UNKNOWN_LIVE_SHADOW_STAGE:{stage}")
    if layer not in SHADOW_RECONCILIATION_LAYERS:
        raise LiveShadowReconciliationError(f"UNKNOWN_SHADOW_RECONCILIATION_LAYER:{layer}")
    if outcome not in SHADOW_RECONCILIATION_OUTCOMES:
        raise LiveShadowReconciliationError(f"UNKNOWN_SHADOW_RECONCILIATION_OUTCOME:{outcome}")
    if outcome == "SAFE_ADOPT_EXCHANGE_TRUTH" and not exchange_truth_adoption_policy_id:
        raise LiveShadowReconciliationError("EXCHANGE_TRUTH_ADOPTION_REQUIRES_EXPLICIT_POLICY")
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
    return LiveShadowReconciliationCheckpointRecordV1(
        stage=stage,
        layer=layer,
        outcome=outcome,
        divergence_detected=divergence_detected,
        exchange_truth_adoption_policy_id=exchange_truth_adoption_policy_id,
        blocks_new_entry=blocks_new_entry,
    )


def refuse_live_shadow_reconciliation_activation_v1(*, claimed_action: str) -> dict[str, Any]:
    raise LiveShadowReconciliationError(
        f"LIVE_SHADOW_RECONCILIATION_ACTIVATION_FORBIDDEN_IN_CAPABILITY_11_7:{claimed_action}"
    )


def refuse_live_shadow_exchange_fetch_v1(*, claimed_fetch: str) -> dict[str, Any]:
    raise LiveShadowReconciliationError(
        f"LIVE_SHADOW_EXCHANGE_FETCH_FORBIDDEN_IN_CAPABILITY_11_7:{claimed_fetch}"
    )


def refuse_silent_local_history_overwrite_v1(*, attempted_overwrite_of: str) -> dict[str, Any]:
    raise LiveShadowReconciliationError(
        f"SILENT_LOCAL_HISTORY_OVERWRITE_FORBIDDEN:{attempted_overwrite_of}"
    )


def refuse_automatic_stage_promotion_v1(*, claimed_target_stage: str) -> dict[str, Any]:
    raise LiveShadowReconciliationError(
        f"AUTOMATIC_STAGE_PROMOTION_FORBIDDEN_IN_CAPABILITY_11_7:{claimed_target_stage}"
    )


def refuse_cap_11_8_live_dry_run_order_plan_v1(*, claimed_surface: str) -> dict[str, Any]:
    raise LiveShadowReconciliationError(
        f"CAPABILITY_11_8_SURFACE_FORBIDDEN_IN_CAPABILITY_11_7:{claimed_surface}"
    )


def prove_live_shadow_reconciliation_contract_v1() -> dict[str, Any]:
    match_cp = build_live_shadow_reconciliation_checkpoint_v1(
        stage="LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION",
        layer="positions",
        outcome="MATCH",
        divergence_detected=False,
    )
    halt_cp = build_live_shadow_reconciliation_checkpoint_v1(
        stage="LIVE_PRIVATE_READ_ONLY",
        layer="balances_equity_and_available_margin",
        outcome="HARD_STOP_OWNER_REVIEW",
        divergence_detected=True,
    )
    adopt_ok = build_live_shadow_reconciliation_checkpoint_v1(
        stage="LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION",
        layer="open_orders",
        outcome="SAFE_ADOPT_EXCHANGE_TRUTH",
        divergence_detected=True,
        exchange_truth_adoption_policy_id="policy-explicit-live-shadow-v1",
    )

    adopt_blocked = False
    try:
        build_live_shadow_reconciliation_checkpoint_v1(
            stage="LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION",
            layer="open_orders",
            outcome="SAFE_ADOPT_EXCHANGE_TRUTH",
            divergence_detected=True,
        )
    except LiveShadowReconciliationError as exc:
        adopt_blocked = "EXCHANGE_TRUTH_ADOPTION_REQUIRES_EXPLICIT_POLICY" in str(exc)

    overwrite_blocked = False
    try:
        refuse_silent_local_history_overwrite_v1(attempted_overwrite_of="decision_history")
    except LiveShadowReconciliationError as exc:
        overwrite_blocked = "SILENT_LOCAL_HISTORY_OVERWRITE_FORBIDDEN" in str(exc)

    activation_blocked = False
    try:
        refuse_live_shadow_reconciliation_activation_v1(claimed_action="start_shadow")
    except LiveShadowReconciliationError as exc:
        activation_blocked = "ACTIVATION_FORBIDDEN" in str(exc)

    fetch_blocked = False
    try:
        refuse_live_shadow_exchange_fetch_v1(claimed_fetch="positions")
    except LiveShadowReconciliationError as exc:
        fetch_blocked = "EXCHANGE_FETCH_FORBIDDEN" in str(exc)

    promotion_blocked = False
    try:
        refuse_automatic_stage_promotion_v1(claimed_target_stage="LIVE_DRY_RUN_ORDER_PLAN")
    except LiveShadowReconciliationError as exc:
        promotion_blocked = "AUTOMATIC_STAGE_PROMOTION_FORBIDDEN" in str(exc)

    cap_11_8_blocked = False
    try:
        refuse_cap_11_8_live_dry_run_order_plan_v1(claimed_surface="LIVE_DRY_RUN_ORDER_PLAN")
    except LiveShadowReconciliationError as exc:
        cap_11_8_blocked = "CAPABILITY_11_8_SURFACE_FORBIDDEN" in str(exc)

    dry_run_stage_blocked = False
    try:
        build_live_shadow_reconciliation_checkpoint_v1(
            stage="LIVE_DRY_RUN_ORDER_PLAN",
            layer="positions",
            outcome="MATCH",
            divergence_detected=False,
        )
    except LiveShadowReconciliationError as exc:
        dry_run_stage_blocked = "CAPABILITY_11_8_SURFACE_FORBIDDEN" in str(exc)

    fixture_ok = all(
        r.source == "FIXTURE_ONLY"
        and r.shadow_activated is False
        and r.exchange_fetch_performed is False
        for r in (match_cp, halt_cp, adopt_ok)
    )
    ok = all(
        [
            fixture_ok,
            match_cp.blocks_new_entry is False,
            halt_cp.blocks_new_entry is True,
            adopt_ok.exchange_truth_adoption_policy_id == "policy-explicit-live-shadow-v1",
            adopt_blocked,
            overwrite_blocked,
            activation_blocked,
            fetch_blocked,
            promotion_blocked,
            cap_11_8_blocked,
            dry_run_stage_blocked,
            LIVE_SHADOW_RECONCILIATION_CONTRACT_BOUND is True,
            LIVE_SHADOW_RECONCILIATION_CONTRACT_ACTIVATED is False,
            LIVE_SHADOW_RECONCILIATION_ACTIVATED is False,
            LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION_ACTIVATED is False,
            CAPABILITY_11_8_STARTED is False,
            RECONCILIATION_BEFORE_ALPHA is True,
            RECONCILIATION_CONTINUOUS is True,
            UNRESOLVED_ECONOMIC_DIVERGENCE_BLOCKS_NEW_ENTRY is True,
            POSITION_PROTECTION_REMAINS_ACTIVE_WHERE_SAFE is True,
            EXCHANGE_TRUTH_ADOPTION_REQUIRES_EXPLICIT_POLICY is True,
            SILENT_LOCAL_HISTORY_OVERWRITE_FORBIDDEN is True,
            NO_AUTOMATIC_STAGE_PROMOTION is True,
            OWNER_GO_REQUIRED_FOR_STAGE_PROMOTION is True,
        ]
    )
    return {
        "ok": ok,
        "LIVE_SHADOW_RECONCILIATION_CONTRACT_BOUND": True,
        "LIVE_SHADOW_RECONCILIATION_CONTRACT_ACTIVATED": False,
        "LIVE_SHADOW_RECONCILIATION_ACTIVATED": False,
        "LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION_ACTIVATED": False,
        "CAPABILITY_11_8_STARTED": False,
        "RECONCILIATION_BEFORE_ALPHA": True,
        "RECONCILIATION_CONTINUOUS": True,
        "UNRESOLVED_ECONOMIC_DIVERGENCE_BLOCKS_NEW_ENTRY": True,
        "NO_AUTOMATIC_STAGE_PROMOTION": True,
        "stages_in_scope": list(LIVE_PROGRESSION_STAGES_IN_SCOPE),
        "stages_forbidden": list(LIVE_PROGRESSION_STAGES_FORBIDDEN),
        "layers": list(SHADOW_RECONCILIATION_LAYERS),
        "outcomes": list(SHADOW_RECONCILIATION_OUTCOMES),
        "adopt_policy_required_blocked": adopt_blocked,
        "overwrite_blocked": overwrite_blocked,
        "activation_blocked": activation_blocked,
        "exchange_fetch_blocked": fetch_blocked,
        "automatic_promotion_blocked": promotion_blocked,
        "cap_11_8_surface_blocked": cap_11_8_blocked,
        "dry_run_stage_blocked": dry_run_stage_blocked,
        "OWNER": OWNER,
    }
