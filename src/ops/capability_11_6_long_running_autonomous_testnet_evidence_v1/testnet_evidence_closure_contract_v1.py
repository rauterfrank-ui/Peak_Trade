"""Testnet evidence-closure contracts (§11.12 closure fields) — fixture-only."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.ops.capability_11_6_long_running_autonomous_testnet_evidence_v1.constants_v1 import (
    CONTRACT_VERSION,
    OWNER,
    TESTNET_AUTONOMOUS_RECOVERY_PROVEN,
    TESTNET_CLOSURE_EVIDENCE_FIELDS,
    TESTNET_DUPLICATE_ORDER_PREVENTION_PROVEN,
    TESTNET_EVIDENCE_CLOSURE_CONTRACT_ACTIVATED,
    TESTNET_EVIDENCE_CLOSURE_CONTRACT_BOUND,
    TESTNET_EVIDENCE_CLOSURE_OWNER,
    TESTNET_EVIDENCE_VERIFIED,
    TESTNET_KILL_SWITCH_PROVEN,
    TESTNET_ORDER_LIFECYCLE_PROVEN,
    TESTNET_RECONCILIATION_PROVEN,
    TESTNET_RESTART_PROVEN,
    TESTNET_UNKNOWN_SUBMIT_RECOVERY_PROVEN,
)


class TestnetEvidenceClosureError(RuntimeError):
    """Fail-closed Testnet evidence-closure violation."""

    __test__ = False


@dataclass(frozen=True)
class TestnetEvidenceClosureFieldRecordV1:
    __test__ = False

    field_name: str
    contract_bound: bool
    proven_claimed: bool
    source: str = "FIXTURE_ONLY"
    network_effect: str = "NONE"
    contract_version: str = CONTRACT_VERSION
    owner: str = TESTNET_EVIDENCE_CLOSURE_OWNER


def build_testnet_evidence_closure_field_record_v1(
    *, field_name: str
) -> TestnetEvidenceClosureFieldRecordV1:
    if field_name not in TESTNET_CLOSURE_EVIDENCE_FIELDS:
        raise TestnetEvidenceClosureError(f"UNKNOWN_TESTNET_CLOSURE_EVIDENCE_FIELD:{field_name}")
    return TestnetEvidenceClosureFieldRecordV1(
        field_name=field_name,
        contract_bound=True,
        proven_claimed=False,
    )


def refuse_testnet_proven_overclaim_v1(*, field_name: str) -> dict[str, Any]:
    if field_name not in TESTNET_CLOSURE_EVIDENCE_FIELDS:
        raise TestnetEvidenceClosureError(f"UNKNOWN_TESTNET_CLOSURE_EVIDENCE_FIELD:{field_name}")
    raise TestnetEvidenceClosureError(
        f"TESTNET_PROVEN_OVERCLAIM_FORBIDDEN_IN_CAPABILITY_11_6:{field_name}"
    )


def refuse_testnet_evidence_activation_v1(*, claimed_action: str) -> dict[str, Any]:
    raise TestnetEvidenceClosureError(
        f"TESTNET_EVIDENCE_ACTIVATION_FORBIDDEN_IN_CAPABILITY_11_6:{claimed_action}"
    )


def prove_testnet_evidence_closure_contract_v1() -> dict[str, Any]:
    records: dict[str, TestnetEvidenceClosureFieldRecordV1] = {}
    for field_name in TESTNET_CLOSURE_EVIDENCE_FIELDS:
        records[field_name] = build_testnet_evidence_closure_field_record_v1(field_name=field_name)

    unknown_field_blocked = False
    try:
        build_testnet_evidence_closure_field_record_v1(field_name="LIVE_ORDER_LIFECYCLE_PROVEN")
    except TestnetEvidenceClosureError as exc:
        unknown_field_blocked = "UNKNOWN_TESTNET_CLOSURE_EVIDENCE_FIELD" in str(exc)

    overclaim_blocked: dict[str, bool] = {}
    for field_name in TESTNET_CLOSURE_EVIDENCE_FIELDS:
        blocked = False
        try:
            refuse_testnet_proven_overclaim_v1(field_name=field_name)
        except TestnetEvidenceClosureError as exc:
            blocked = "TESTNET_PROVEN_OVERCLAIM_FORBIDDEN" in str(exc)
        overclaim_blocked[field_name] = blocked

    activation_blocked = False
    try:
        refuse_testnet_evidence_activation_v1(claimed_action="mark_testnet_evidence_verified")
    except TestnetEvidenceClosureError as exc:
        activation_blocked = "TESTNET_EVIDENCE_ACTIVATION_FORBIDDEN" in str(exc)

    proven_flags_false = all(
        [
            TESTNET_ORDER_LIFECYCLE_PROVEN is False,
            TESTNET_RECONCILIATION_PROVEN is False,
            TESTNET_RESTART_PROVEN is False,
            TESTNET_UNKNOWN_SUBMIT_RECOVERY_PROVEN is False,
            TESTNET_DUPLICATE_ORDER_PREVENTION_PROVEN is False,
            TESTNET_KILL_SWITCH_PROVEN is False,
            TESTNET_AUTONOMOUS_RECOVERY_PROVEN is False,
            TESTNET_EVIDENCE_VERIFIED is False,
        ]
    )
    all_bound_unproven = all(
        r.contract_bound is True and r.proven_claimed is False for r in records.values()
    )
    ok = all(
        [
            all_bound_unproven,
            unknown_field_blocked,
            all(overclaim_blocked.values()),
            activation_blocked,
            proven_flags_false,
            TESTNET_EVIDENCE_CLOSURE_CONTRACT_BOUND is True,
            TESTNET_EVIDENCE_CLOSURE_CONTRACT_ACTIVATED is False,
        ]
    )
    return {
        "ok": ok,
        "TESTNET_EVIDENCE_CLOSURE_CONTRACT_BOUND": True,
        "TESTNET_EVIDENCE_CLOSURE_CONTRACT_ACTIVATED": False,
        "TESTNET_ORDER_LIFECYCLE_PROVEN": False,
        "TESTNET_RECONCILIATION_PROVEN": False,
        "TESTNET_RESTART_PROVEN": False,
        "TESTNET_UNKNOWN_SUBMIT_RECOVERY_PROVEN": False,
        "TESTNET_DUPLICATE_ORDER_PREVENTION_PROVEN": False,
        "TESTNET_KILL_SWITCH_PROVEN": False,
        "TESTNET_AUTONOMOUS_RECOVERY_PROVEN": False,
        "TESTNET_EVIDENCE_VERIFIED": False,
        "fields": list(TESTNET_CLOSURE_EVIDENCE_FIELDS),
        "overclaim_blocked": overclaim_blocked,
        "unknown_field_blocked": unknown_field_blocked,
        "activation_blocked": activation_blocked,
        "OWNER": OWNER,
    }
