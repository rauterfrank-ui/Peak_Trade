"""Reuse existing authoritative gates without forking their semantics."""

from __future__ import annotations

from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.constants_v1 import (
    CANARY_ENTRY_SUBMIT_PERMIT_OWNS_GENERAL_DECISION,
    FLATTEN_PRE_SEND_OWNS_ENTRY_DECISION,
    STANDING_CANARY_AUTHORIZED,
    STANDING_FLATTEN_LIVE_WIRE_ENABLED,
    STANDING_GENERAL_LIVE_SUBMIT_UNLOCKED,
    STANDING_LIVE_ARMED,
    STANDING_LIVE_AUTHORIZED,
    STANDING_LIVE_ENABLED,
    STANDING_ORDERS_ALLOWED,
    STANDING_SUBMIT_UNLOCKED,
    STANDING_TESTNET_AUTHORIZED,
)
from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.models_v1 import (
    AuthoritySnapshotV1,
    ExistingGateReuseProofV1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    AUTHORIZATION_SCOPE,
    BLOCKS_NEW_ENTRY,
    CONFIRM_TOKEN_CANONICAL,
    LIVE_RECONCILIATION_PROVEN,
    OWNER_GO_EXECUTE,
    REQUIRED_SECRETREF_URI,
    REUSED_BINDING_REST_HOST,
    UNRESOLVED_ECONOMIC_DIVERGENCE_BLOCKS_NEW_ENTRY,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.submit_gates_v1 import (
    evaluate_canary_submit_gates_v1,
)


def standing_live_flags_are_false_v1() -> bool:
    return (
        STANDING_LIVE_AUTHORIZED is False
        and STANDING_TESTNET_AUTHORIZED is False
        and STANDING_CANARY_AUTHORIZED is False
        and STANDING_ORDERS_ALLOWED is False
        and STANDING_LIVE_ENABLED is False
        and STANDING_LIVE_ARMED is False
        and STANDING_SUBMIT_UNLOCKED is False
        and STANDING_GENERAL_LIVE_SUBMIT_UNLOCKED is False
        and STANDING_FLATTEN_LIVE_WIRE_ENABLED is False
    )


def prove_existing_gates_deny_live_submit_v1(
    authority: AuthoritySnapshotV1,
) -> ExistingGateReuseProofV1:
    """Call the existing canary submit gate with standing-false authority.

    The specialized CanaryEntrySubmitPermitV1 remains a one-shot HTTP permit
    and does not own this general offline decision.
    """
    evaluation = evaluate_canary_submit_gates_v1(
        owner_go=OWNER_GO_EXECUTE,
        owner_go_consumed=False,
        authorization_scope=AUTHORIZATION_SCOPE,
        bound_origin_main_sha="0" * 40,
        expected_origin_main_sha="0" * 40,
        live_canary_authorized=bool(authority.canary_authorized),
        live_enabled=bool(authority.live_enabled),
        live_armed=bool(authority.live_armed),
        confirm_token=CONFIRM_TOKEN_CANONICAL,
        blocks_new_entry=BLOCKS_NEW_ENTRY,
        unresolved_economic_divergence=UNRESOLVED_ECONOMIC_DIVERGENCE_BLOCKS_NEW_ENTRY,
        live_reconciliation_proven=LIVE_RECONCILIATION_PROVEN,
        permission_attestation={"READ": True, "TRADE": True, "WITHDRAW": False},
        environment="LIVE",
        fixture_or_demo_or_testnet=False,
        max_notional="1",
        min_executable_notional="1",
        order_count=1,
        position_count=0,
        exposure_above_minimum_bound=False,
        live_canary_cybersecurity_gate="PASS",
        rest_host=REUSED_BINDING_REST_HOST,
        secretref_uri=REQUIRED_SECRETREF_URI,
        require_notional_bounds=True,
        recovery_state_clear=True,
    )
    return ExistingGateReuseProofV1(
        canary_submit_allowed=bool(evaluation.submit_allowed),
        canary_submit_reasons=tuple(evaluation.reasons),
        standing_live_flags_false=standing_live_flags_are_false_v1(),
        flatten_live_wire_enabled=bool(STANDING_FLATTEN_LIVE_WIRE_ENABLED),
        canary_permit_owns_general_decision=CANARY_ENTRY_SUBMIT_PERMIT_OWNS_GENERAL_DECISION,
        flatten_pre_send_owns_entry_decision=FLATTEN_PRE_SEND_OWNS_ENTRY_DECISION,
    )
