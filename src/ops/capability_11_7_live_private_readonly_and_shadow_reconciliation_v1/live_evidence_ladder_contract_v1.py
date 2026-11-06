"""Live evidence ladder contracts (§11.14) — bound, never proven from fixtures."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.ops.capability_11_7_live_private_readonly_and_shadow_reconciliation_v1.constants_v1 import (
    CONTRACT_VERSION,
    LIVE_ACCOUNTING_RECONSTRUCTED,
    LIVE_AUTONOMOUS_RECOVERY_OBSERVED,
    LIVE_END_TO_END_EVIDENCE_PROVEN,
    LIVE_EVIDENCE_LADDER_CONTRACT_ACTIVATED,
    LIVE_EVIDENCE_LADDER_CONTRACT_BOUND,
    LIVE_EVIDENCE_LADDER_FIELDS,
    LIVE_EVIDENCE_LADDER_OWNER,
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


class LiveEvidenceLadderError(RuntimeError):
    """Fail-closed Live evidence ladder violation."""


@dataclass(frozen=True)
class LiveEvidenceLadderFieldRecordV1:
    field_name: str
    contract_bound: bool
    proven_claimed: bool
    source: str = "FIXTURE_ONLY"
    network_effect: str = "NONE"
    contract_version: str = CONTRACT_VERSION
    owner: str = LIVE_EVIDENCE_LADDER_OWNER


def build_live_evidence_ladder_field_record_v1(
    *, field_name: str
) -> LiveEvidenceLadderFieldRecordV1:
    if field_name not in LIVE_EVIDENCE_LADDER_FIELDS:
        raise LiveEvidenceLadderError(f"UNKNOWN_LIVE_EVIDENCE_LADDER_FIELD:{field_name}")
    return LiveEvidenceLadderFieldRecordV1(
        field_name=field_name,
        contract_bound=True,
        proven_claimed=False,
    )


def refuse_live_evidence_proven_overclaim_v1(*, field_name: str) -> dict[str, Any]:
    if field_name not in LIVE_EVIDENCE_LADDER_FIELDS:
        raise LiveEvidenceLadderError(f"UNKNOWN_LIVE_EVIDENCE_LADDER_FIELD:{field_name}")
    raise LiveEvidenceLadderError(
        f"LIVE_EVIDENCE_PROVEN_OVERCLAIM_FORBIDDEN_IN_CAPABILITY_11_7:{field_name}"
    )


def refuse_live_evidence_activation_v1(*, claimed_action: str) -> dict[str, Any]:
    raise LiveEvidenceLadderError(
        f"LIVE_EVIDENCE_LADDER_ACTIVATION_FORBIDDEN_IN_CAPABILITY_11_7:{claimed_action}"
    )


def prove_live_evidence_ladder_contract_v1() -> dict[str, Any]:
    records: dict[str, LiveEvidenceLadderFieldRecordV1] = {}
    for field_name in LIVE_EVIDENCE_LADDER_FIELDS:
        records[field_name] = build_live_evidence_ladder_field_record_v1(field_name=field_name)

    unknown_blocked = False
    try:
        build_live_evidence_ladder_field_record_v1(field_name="TESTNET_EVIDENCE_VERIFIED")
    except LiveEvidenceLadderError as exc:
        unknown_blocked = "UNKNOWN_LIVE_EVIDENCE_LADDER_FIELD" in str(exc)

    overclaim_blocked = False
    try:
        refuse_live_evidence_proven_overclaim_v1(field_name="LIVE_PRIVATE_READ_ONLY_PROVEN")
    except LiveEvidenceLadderError as exc:
        overclaim_blocked = "PROVEN_OVERCLAIM_FORBIDDEN" in str(exc)

    activation_blocked = False
    try:
        refuse_live_evidence_activation_v1(claimed_action="mark_live_proven")
    except LiveEvidenceLadderError as exc:
        activation_blocked = "ACTIVATION_FORBIDDEN" in str(exc)

    all_unproven = all(
        r.contract_bound is True and r.proven_claimed is False for r in records.values()
    )
    ok = all(
        [
            all_unproven,
            unknown_blocked,
            overclaim_blocked,
            activation_blocked,
            LIVE_EVIDENCE_LADDER_CONTRACT_BOUND is True,
            LIVE_EVIDENCE_LADDER_CONTRACT_ACTIVATED is False,
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
        ]
    )
    return {
        "ok": ok,
        "LIVE_EVIDENCE_LADDER_CONTRACT_BOUND": True,
        "LIVE_EVIDENCE_LADDER_CONTRACT_ACTIVATED": False,
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
        "unknown_field_blocked": unknown_blocked,
        "proven_overclaim_blocked": overclaim_blocked,
        "activation_blocked": activation_blocked,
        "OWNER": OWNER,
    }
