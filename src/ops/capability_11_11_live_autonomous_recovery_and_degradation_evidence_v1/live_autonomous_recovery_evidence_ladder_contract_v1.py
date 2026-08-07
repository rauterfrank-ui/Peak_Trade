"""Live autonomous recovery evidence ladder contracts (§11.14) — bound, never observed/proven."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.ops.capability_11_11_live_autonomous_recovery_and_degradation_evidence_v1.constants_v1 import (
    CONTRACT_VERSION,
    LIVE_ACCOUNTING_RECONSTRUCTED,
    LIVE_AUTONOMOUS_RECOVERY_EVIDENCE_LADDER_CONTRACT_ACTIVATED,
    LIVE_AUTONOMOUS_RECOVERY_EVIDENCE_LADDER_CONTRACT_BOUND,
    LIVE_AUTONOMOUS_RECOVERY_EVIDENCE_LADDER_OWNER,
    LIVE_AUTONOMOUS_RECOVERY_LADDER_FOCUS_FIELDS,
    LIVE_AUTONOMOUS_RECOVERY_LADDER_FORBIDDEN_CLAIM_FIELDS,
    LIVE_AUTONOMOUS_RECOVERY_OBSERVED,
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


class LiveAutonomousRecoveryEvidenceLadderError(RuntimeError):
    """Fail-closed Live autonomous recovery evidence ladder violation."""


@dataclass(frozen=True)
class LiveAutonomousRecoveryEvidenceLadderFieldRecordV1:
    field_name: str
    contract_bound: bool
    observed_claimed: bool
    proven_claimed: bool
    source: str = "FIXTURE_ONLY"
    network_effect: str = "NONE"
    contract_version: str = CONTRACT_VERSION
    owner: str = LIVE_AUTONOMOUS_RECOVERY_EVIDENCE_LADDER_OWNER


def build_live_autonomous_recovery_evidence_ladder_field_record_v1(
    *, field_name: str
) -> LiveAutonomousRecoveryEvidenceLadderFieldRecordV1:
    if field_name not in LIVE_EVIDENCE_LADDER_FIELDS:
        raise LiveAutonomousRecoveryEvidenceLadderError(
            f"UNKNOWN_LIVE_EVIDENCE_LADDER_FIELD:{field_name}"
        )
    return LiveAutonomousRecoveryEvidenceLadderFieldRecordV1(
        field_name=field_name,
        contract_bound=True,
        observed_claimed=False,
        proven_claimed=False,
    )


def refuse_live_restart_or_recovery_observed_overclaim_v1(*, field_name: str) -> dict[str, Any]:
    if field_name not in LIVE_EVIDENCE_LADDER_FIELDS:
        raise LiveAutonomousRecoveryEvidenceLadderError(
            f"UNKNOWN_LIVE_EVIDENCE_LADDER_FIELD:{field_name}"
        )
    raise LiveAutonomousRecoveryEvidenceLadderError(
        f"LIVE_RESTART_OR_RECOVERY_OBSERVED_OVERCLAIM_FORBIDDEN_IN_CAPABILITY_11_11:{field_name}"
    )


def refuse_live_end_to_end_and_beyond_claim_v1(*, field_name: str) -> dict[str, Any]:
    if field_name not in LIVE_AUTONOMOUS_RECOVERY_LADDER_FORBIDDEN_CLAIM_FIELDS:
        raise LiveAutonomousRecoveryEvidenceLadderError(
            f"FIELD_NOT_IN_CAPABILITY_11_12_PLUS_FORBIDDEN_SET:{field_name}"
        )
    raise LiveAutonomousRecoveryEvidenceLadderError(
        f"CAPABILITY_11_12_LADDER_CLAIM_FORBIDDEN_IN_CAPABILITY_11_11:{field_name}"
    )


def refuse_live_autonomous_recovery_evidence_activation_v1(
    *, claimed_action: str
) -> dict[str, Any]:
    raise LiveAutonomousRecoveryEvidenceLadderError(
        "LIVE_AUTONOMOUS_RECOVERY_EVIDENCE_LADDER_ACTIVATION_FORBIDDEN_IN_CAPABILITY_11_11:"
        f"{claimed_action}"
    )


def prove_live_autonomous_recovery_evidence_ladder_contract_v1() -> dict[str, Any]:
    records: dict[str, LiveAutonomousRecoveryEvidenceLadderFieldRecordV1] = {}
    for field_name in LIVE_EVIDENCE_LADDER_FIELDS:
        records[field_name] = build_live_autonomous_recovery_evidence_ladder_field_record_v1(
            field_name=field_name
        )

    unknown_blocked = False
    try:
        build_live_autonomous_recovery_evidence_ladder_field_record_v1(
            field_name="TESTNET_EVIDENCE_VERIFIED"
        )
    except LiveAutonomousRecoveryEvidenceLadderError as exc:
        unknown_blocked = "UNKNOWN_LIVE_EVIDENCE_LADDER_FIELD" in str(exc)

    observed_overclaim_blocked = False
    try:
        refuse_live_restart_or_recovery_observed_overclaim_v1(
            field_name="LIVE_AUTONOMOUS_RECOVERY_OBSERVED"
        )
    except LiveAutonomousRecoveryEvidenceLadderError as exc:
        observed_overclaim_blocked = "OBSERVED_OVERCLAIM_FORBIDDEN" in str(exc)

    end_to_end_blocked = False
    try:
        refuse_live_end_to_end_and_beyond_claim_v1(field_name="LIVE_END_TO_END_EVIDENCE_PROVEN")
    except LiveAutonomousRecoveryEvidenceLadderError as exc:
        end_to_end_blocked = "CAPABILITY_11_12_LADDER_CLAIM_FORBIDDEN" in str(exc)

    activation_blocked = False
    try:
        refuse_live_autonomous_recovery_evidence_activation_v1(
            claimed_action="mark_recovery_observed"
        )
    except LiveAutonomousRecoveryEvidenceLadderError as exc:
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
            end_to_end_blocked,
            activation_blocked,
            LIVE_AUTONOMOUS_RECOVERY_EVIDENCE_LADDER_CONTRACT_BOUND is True,
            LIVE_AUTONOMOUS_RECOVERY_EVIDENCE_LADDER_CONTRACT_ACTIVATED is False,
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
            set(LIVE_AUTONOMOUS_RECOVERY_LADDER_FOCUS_FIELDS)
            == {
                "LIVE_RESTART_RECONSTRUCTED",
                "LIVE_AUTONOMOUS_RECOVERY_OBSERVED",
            },
        ]
    )
    return {
        "ok": ok,
        "LIVE_AUTONOMOUS_RECOVERY_EVIDENCE_LADDER_CONTRACT_BOUND": True,
        "LIVE_AUTONOMOUS_RECOVERY_EVIDENCE_LADDER_CONTRACT_ACTIVATED": False,
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
        "focus_fields": list(LIVE_AUTONOMOUS_RECOVERY_LADDER_FOCUS_FIELDS),
        "forbidden_claim_fields": list(LIVE_AUTONOMOUS_RECOVERY_LADDER_FORBIDDEN_CLAIM_FIELDS),
        "unknown_field_blocked": unknown_blocked,
        "observed_overclaim_blocked": observed_overclaim_blocked,
        "end_to_end_and_beyond_blocked": end_to_end_blocked,
        "activation_blocked": activation_blocked,
        "OWNER": OWNER,
    }
