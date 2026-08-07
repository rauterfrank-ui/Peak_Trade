"""Live order-plan evidence ladder contracts (§11.14) — bound, never observed/proven."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.ops.capability_11_8_live_dry_run_order_plan_parity_v1.constants_v1 import (
    CONTRACT_VERSION,
    LIVE_ACCOUNTING_RECONSTRUCTED,
    LIVE_AUTONOMOUS_RECOVERY_OBSERVED,
    LIVE_END_TO_END_EVIDENCE_PROVEN,
    LIVE_EVIDENCE_LADDER_FIELDS,
    LIVE_EXECUTION_CODE_EXISTS,
    LIVE_EXECUTION_PATH_REACHABLE,
    LIVE_FEE_OBSERVED,
    LIVE_FILL_OBSERVED,
    LIVE_ORDER_PLAN_EVIDENCE_LADDER_CONTRACT_ACTIVATED,
    LIVE_ORDER_PLAN_EVIDENCE_LADDER_CONTRACT_BOUND,
    LIVE_ORDER_PLAN_EVIDENCE_LADDER_OWNER,
    LIVE_ORDER_PLAN_LADDER_FOCUS_FIELDS,
    LIVE_ORDER_PLAN_LADDER_FORBIDDEN_CLAIM_FIELDS,
    LIVE_ORDER_PLAN_OBSERVED,
    LIVE_POSITION_RECONCILED,
    LIVE_PRIVATE_READ_ONLY_PROVEN,
    LIVE_RESTART_RECONSTRUCTED,
    LIVE_SUBMIT_ACK_OBSERVED,
    OWNER,
)


class LiveOrderPlanEvidenceLadderError(RuntimeError):
    """Fail-closed Live order-plan evidence ladder violation."""


@dataclass(frozen=True)
class LiveOrderPlanEvidenceLadderFieldRecordV1:
    field_name: str
    contract_bound: bool
    observed_claimed: bool
    proven_claimed: bool
    source: str = "FIXTURE_ONLY"
    network_effect: str = "NONE"
    contract_version: str = CONTRACT_VERSION
    owner: str = LIVE_ORDER_PLAN_EVIDENCE_LADDER_OWNER


def build_live_order_plan_evidence_ladder_field_record_v1(
    *, field_name: str
) -> LiveOrderPlanEvidenceLadderFieldRecordV1:
    if field_name not in LIVE_EVIDENCE_LADDER_FIELDS:
        raise LiveOrderPlanEvidenceLadderError(f"UNKNOWN_LIVE_EVIDENCE_LADDER_FIELD:{field_name}")
    return LiveOrderPlanEvidenceLadderFieldRecordV1(
        field_name=field_name,
        contract_bound=True,
        observed_claimed=False,
        proven_claimed=False,
    )


def refuse_live_order_plan_observed_overclaim_v1(*, field_name: str) -> dict[str, Any]:
    if field_name not in LIVE_EVIDENCE_LADDER_FIELDS:
        raise LiveOrderPlanEvidenceLadderError(f"UNKNOWN_LIVE_EVIDENCE_LADDER_FIELD:{field_name}")
    raise LiveOrderPlanEvidenceLadderError(
        f"LIVE_ORDER_PLAN_OBSERVED_OVERCLAIM_FORBIDDEN_IN_CAPABILITY_11_8:{field_name}"
    )


def refuse_live_submit_ack_and_beyond_claim_v1(*, field_name: str) -> dict[str, Any]:
    if field_name not in LIVE_ORDER_PLAN_LADDER_FORBIDDEN_CLAIM_FIELDS:
        raise LiveOrderPlanEvidenceLadderError(
            f"FIELD_NOT_IN_CAPABILITY_11_9_PLUS_FORBIDDEN_SET:{field_name}"
        )
    raise LiveOrderPlanEvidenceLadderError(
        f"CAPABILITY_11_9_LADDER_CLAIM_FORBIDDEN_IN_CAPABILITY_11_8:{field_name}"
    )


def refuse_live_order_plan_evidence_activation_v1(*, claimed_action: str) -> dict[str, Any]:
    raise LiveOrderPlanEvidenceLadderError(
        f"LIVE_ORDER_PLAN_EVIDENCE_LADDER_ACTIVATION_FORBIDDEN_IN_CAPABILITY_11_8:{claimed_action}"
    )


def prove_live_order_plan_evidence_ladder_contract_v1() -> dict[str, Any]:
    records: dict[str, LiveOrderPlanEvidenceLadderFieldRecordV1] = {}
    for field_name in LIVE_EVIDENCE_LADDER_FIELDS:
        records[field_name] = build_live_order_plan_evidence_ladder_field_record_v1(
            field_name=field_name
        )

    unknown_blocked = False
    try:
        build_live_order_plan_evidence_ladder_field_record_v1(
            field_name="TESTNET_EVIDENCE_VERIFIED"
        )
    except LiveOrderPlanEvidenceLadderError as exc:
        unknown_blocked = "UNKNOWN_LIVE_EVIDENCE_LADDER_FIELD" in str(exc)

    observed_overclaim_blocked = False
    try:
        refuse_live_order_plan_observed_overclaim_v1(field_name="LIVE_ORDER_PLAN_OBSERVED")
    except LiveOrderPlanEvidenceLadderError as exc:
        observed_overclaim_blocked = "OBSERVED_OVERCLAIM_FORBIDDEN" in str(exc)

    submit_ack_blocked = False
    try:
        refuse_live_submit_ack_and_beyond_claim_v1(field_name="LIVE_SUBMIT_ACK_OBSERVED")
    except LiveOrderPlanEvidenceLadderError as exc:
        submit_ack_blocked = "CAPABILITY_11_9_LADDER_CLAIM_FORBIDDEN" in str(exc)

    activation_blocked = False
    try:
        refuse_live_order_plan_evidence_activation_v1(claimed_action="mark_order_plan_observed")
    except LiveOrderPlanEvidenceLadderError as exc:
        activation_blocked = "ACTIVATION_FORBIDDEN" in str(exc)

    all_unclaimed = all(
        r.contract_bound is True and r.observed_claimed is False and r.proven_claimed is False
        for r in records.values()
    )
    ok = all(
        [
            all_unclaimed,
            unknown_blocked,
            observed_overclaim_blocked,
            submit_ack_blocked,
            activation_blocked,
            LIVE_ORDER_PLAN_EVIDENCE_LADDER_CONTRACT_BOUND is True,
            LIVE_ORDER_PLAN_EVIDENCE_LADDER_CONTRACT_ACTIVATED is False,
            LIVE_EXECUTION_CODE_EXISTS is False,
            LIVE_EXECUTION_PATH_REACHABLE is False,
            LIVE_PRIVATE_READ_ONLY_PROVEN is False,
            LIVE_ORDER_PLAN_OBSERVED is False,
            LIVE_SUBMIT_ACK_OBSERVED is False,
            LIVE_FILL_OBSERVED is False,
            LIVE_FEE_OBSERVED is False,
            LIVE_POSITION_RECONCILED is False,
            LIVE_ACCOUNTING_RECONSTRUCTED is False,
            LIVE_RESTART_RECONSTRUCTED is False,
            LIVE_AUTONOMOUS_RECOVERY_OBSERVED is False,
            LIVE_END_TO_END_EVIDENCE_PROVEN is False,
            set(LIVE_ORDER_PLAN_LADDER_FOCUS_FIELDS) == {"LIVE_ORDER_PLAN_OBSERVED"},
        ]
    )
    return {
        "ok": ok,
        "LIVE_ORDER_PLAN_EVIDENCE_LADDER_CONTRACT_BOUND": True,
        "LIVE_ORDER_PLAN_EVIDENCE_LADDER_CONTRACT_ACTIVATED": False,
        "LIVE_EXECUTION_CODE_EXISTS": False,
        "LIVE_EXECUTION_PATH_REACHABLE": False,
        "LIVE_PRIVATE_READ_ONLY_PROVEN": False,
        "LIVE_ORDER_PLAN_OBSERVED": False,
        "LIVE_SUBMIT_ACK_OBSERVED": False,
        "LIVE_FILL_OBSERVED": False,
        "LIVE_FEE_OBSERVED": False,
        "LIVE_POSITION_RECONCILED": False,
        "LIVE_ACCOUNTING_RECONSTRUCTED": False,
        "LIVE_RESTART_RECONSTRUCTED": False,
        "LIVE_AUTONOMOUS_RECOVERY_OBSERVED": False,
        "LIVE_END_TO_END_EVIDENCE_PROVEN": False,
        "fields": list(LIVE_EVIDENCE_LADDER_FIELDS),
        "focus_fields": list(LIVE_ORDER_PLAN_LADDER_FOCUS_FIELDS),
        "forbidden_claim_fields": list(LIVE_ORDER_PLAN_LADDER_FORBIDDEN_CLAIM_FIELDS),
        "unknown_field_blocked": unknown_blocked,
        "observed_overclaim_blocked": observed_overclaim_blocked,
        "submit_ack_and_beyond_blocked": submit_ack_blocked,
        "activation_blocked": activation_blocked,
        "OWNER": OWNER,
    }
