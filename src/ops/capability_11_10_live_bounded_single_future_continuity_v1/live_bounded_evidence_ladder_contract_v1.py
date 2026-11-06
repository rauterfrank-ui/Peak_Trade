"""Live bounded evidence ladder contracts (§11.14) — bound, never observed/proven."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.ops.capability_11_10_live_bounded_single_future_continuity_v1.constants_v1 import (
    CONTRACT_VERSION,
    LIVE_ACCOUNTING_RECONSTRUCTED,
    LIVE_AUTONOMOUS_RECOVERY_OBSERVED,
    LIVE_BOUNDED_EVIDENCE_LADDER_CONTRACT_ACTIVATED,
    LIVE_BOUNDED_EVIDENCE_LADDER_CONTRACT_BOUND,
    LIVE_BOUNDED_EVIDENCE_LADDER_OWNER,
    LIVE_BOUNDED_LADDER_FOCUS_FIELDS,
    LIVE_BOUNDED_LADDER_FORBIDDEN_CLAIM_FIELDS,
    LIVE_END_TO_END_EVIDENCE_PROVEN,
    LIVE_EVIDENCE_LADDER_FIELDS,
    LIVE_EXECUTION_CODE_EXISTS,
    LIVE_EXECUTION_PATH_REACHABLE,
    LIVE_FEE_OBSERVED,
    LIVE_FILL_OBSERVED,
    LIVE_ORDER_PLAN_OBSERVED,
    LIVE_POSITION_RECONCILED,
    LIVE_PRIVATE_READ_ONLY_PROVEN,
    LIVE_RESTART_RECONSTRUCTED,
    LIVE_SUBMIT_ACK_OBSERVED,
    OWNER,
)


class LiveBoundedEvidenceLadderError(RuntimeError):
    """Fail-closed Live bounded evidence ladder violation."""


@dataclass(frozen=True)
class LiveBoundedEvidenceLadderFieldRecordV1:
    field_name: str
    contract_bound: bool
    observed_claimed: bool
    proven_claimed: bool
    source: str = "FIXTURE_ONLY"
    network_effect: str = "NONE"
    contract_version: str = CONTRACT_VERSION
    owner: str = LIVE_BOUNDED_EVIDENCE_LADDER_OWNER


def build_live_bounded_evidence_ladder_field_record_v1(
    *, field_name: str
) -> LiveBoundedEvidenceLadderFieldRecordV1:
    if field_name not in LIVE_EVIDENCE_LADDER_FIELDS:
        raise LiveBoundedEvidenceLadderError(f"UNKNOWN_LIVE_EVIDENCE_LADDER_FIELD:{field_name}")
    return LiveBoundedEvidenceLadderFieldRecordV1(
        field_name=field_name,
        contract_bound=True,
        observed_claimed=False,
        proven_claimed=False,
    )


def refuse_live_fill_observed_overclaim_v1(*, field_name: str) -> dict[str, Any]:
    if field_name not in LIVE_EVIDENCE_LADDER_FIELDS:
        raise LiveBoundedEvidenceLadderError(f"UNKNOWN_LIVE_EVIDENCE_LADDER_FIELD:{field_name}")
    raise LiveBoundedEvidenceLadderError(
        f"LIVE_FILL_OBSERVED_OVERCLAIM_FORBIDDEN_IN_CAPABILITY_11_10:{field_name}"
    )


def refuse_live_restart_and_beyond_claim_v1(*, field_name: str) -> dict[str, Any]:
    if field_name not in LIVE_BOUNDED_LADDER_FORBIDDEN_CLAIM_FIELDS:
        raise LiveBoundedEvidenceLadderError(
            f"FIELD_NOT_IN_CAPABILITY_11_11_PLUS_FORBIDDEN_SET:{field_name}"
        )
    raise LiveBoundedEvidenceLadderError(
        f"CAPABILITY_11_11_LADDER_CLAIM_FORBIDDEN_IN_CAPABILITY_11_10:{field_name}"
    )


def refuse_live_bounded_evidence_activation_v1(*, claimed_action: str) -> dict[str, Any]:
    raise LiveBoundedEvidenceLadderError(
        f"LIVE_BOUNDED_EVIDENCE_LADDER_ACTIVATION_FORBIDDEN_IN_CAPABILITY_11_10:{claimed_action}"
    )


def prove_live_bounded_evidence_ladder_contract_v1() -> dict[str, Any]:
    records: dict[str, LiveBoundedEvidenceLadderFieldRecordV1] = {}
    for field_name in LIVE_EVIDENCE_LADDER_FIELDS:
        records[field_name] = build_live_bounded_evidence_ladder_field_record_v1(
            field_name=field_name
        )

    unknown_blocked = False
    try:
        build_live_bounded_evidence_ladder_field_record_v1(field_name="TESTNET_EVIDENCE_VERIFIED")
    except LiveBoundedEvidenceLadderError as exc:
        unknown_blocked = "UNKNOWN_LIVE_EVIDENCE_LADDER_FIELD" in str(exc)

    observed_overclaim_blocked = False
    try:
        refuse_live_fill_observed_overclaim_v1(field_name="LIVE_FILL_OBSERVED")
    except LiveBoundedEvidenceLadderError as exc:
        observed_overclaim_blocked = "OBSERVED_OVERCLAIM_FORBIDDEN" in str(exc)

    restart_blocked = False
    try:
        refuse_live_restart_and_beyond_claim_v1(field_name="LIVE_RESTART_RECONSTRUCTED")
    except LiveBoundedEvidenceLadderError as exc:
        restart_blocked = "CAPABILITY_11_11_LADDER_CLAIM_FORBIDDEN" in str(exc)

    activation_blocked = False
    try:
        refuse_live_bounded_evidence_activation_v1(claimed_action="mark_fill_observed")
    except LiveBoundedEvidenceLadderError as exc:
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
            restart_blocked,
            activation_blocked,
            LIVE_BOUNDED_EVIDENCE_LADDER_CONTRACT_BOUND is True,
            LIVE_BOUNDED_EVIDENCE_LADDER_CONTRACT_ACTIVATED is False,
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
            set(LIVE_BOUNDED_LADDER_FOCUS_FIELDS)
            == {
                "LIVE_FILL_OBSERVED",
                "LIVE_FEE_OBSERVED",
                "LIVE_POSITION_RECONCILED",
                "LIVE_ACCOUNTING_RECONSTRUCTED",
            },
        ]
    )
    return {
        "ok": ok,
        "LIVE_BOUNDED_EVIDENCE_LADDER_CONTRACT_BOUND": True,
        "LIVE_BOUNDED_EVIDENCE_LADDER_CONTRACT_ACTIVATED": False,
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
        "focus_fields": list(LIVE_BOUNDED_LADDER_FOCUS_FIELDS),
        "forbidden_claim_fields": list(LIVE_BOUNDED_LADDER_FORBIDDEN_CLAIM_FIELDS),
        "unknown_field_blocked": unknown_blocked,
        "observed_overclaim_blocked": observed_overclaim_blocked,
        "restart_and_beyond_blocked": restart_blocked,
        "activation_blocked": activation_blocked,
        "OWNER": OWNER,
    }
