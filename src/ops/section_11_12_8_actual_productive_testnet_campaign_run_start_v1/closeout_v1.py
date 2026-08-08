"""Canonical §11.12.8 closeout — PROVEN fields only from real productive evidence."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.constants_v1 import (
    SECTION_11_13_STARTED,
    TESTNET_AUTONOMOUS_RECOVERY_PROVEN,
    TESTNET_DUPLICATE_ORDER_PREVENTION_PROVEN,
    TESTNET_EVIDENCE_VERIFIED,
    TESTNET_KILL_SWITCH_PROVEN,
    TESTNET_ORDER_LIFECYCLE_PROVEN,
    TESTNET_RECONCILIATION_PROVEN,
    TESTNET_RESTART_PROVEN,
    TESTNET_UNKNOWN_SUBMIT_RECOVERY_PROVEN,
)


class ActualStartCloseoutError(RuntimeError):
    """Fail-closed closeout violation."""


@dataclass(frozen=True)
class Section11128CloseoutV1:
    closeout_machinery_present: bool
    stubbed_acceptance: bool
    real_productive_evidence: bool
    testnet_order_lifecycle_proven: bool
    testnet_reconciliation_proven: bool
    testnet_restart_proven: bool
    testnet_unknown_submit_recovery_proven: bool
    testnet_duplicate_order_prevention_proven: bool
    testnet_kill_switch_proven: bool
    testnet_autonomous_recovery_proven: bool
    testnet_evidence_verified: bool
    section_11_13_started: bool
    section_11_12_8_closed: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "closeout_machinery_present": self.closeout_machinery_present,
            "stubbed_acceptance": self.stubbed_acceptance,
            "real_productive_evidence": self.real_productive_evidence,
            "TESTNET_ORDER_LIFECYCLE_PROVEN": self.testnet_order_lifecycle_proven,
            "TESTNET_RECONCILIATION_PROVEN": self.testnet_reconciliation_proven,
            "TESTNET_RESTART_PROVEN": self.testnet_restart_proven,
            "TESTNET_UNKNOWN_SUBMIT_RECOVERY_PROVEN": (self.testnet_unknown_submit_recovery_proven),
            "TESTNET_DUPLICATE_ORDER_PREVENTION_PROVEN": (
                self.testnet_duplicate_order_prevention_proven
            ),
            "TESTNET_KILL_SWITCH_PROVEN": self.testnet_kill_switch_proven,
            "TESTNET_AUTONOMOUS_RECOVERY_PROVEN": self.testnet_autonomous_recovery_proven,
            "TESTNET_EVIDENCE_VERIFIED": self.testnet_evidence_verified,
            "SECTION_11_13_STARTED": self.section_11_13_started,
            "SECTION_11_12_8_CLOSED": self.section_11_12_8_closed,
        }


def evaluate_section_11_12_8_closeout_v1(
    *,
    stubbed_acceptance: bool,
    real_productive_evidence: bool = False,
) -> Section11128CloseoutV1:
    """Closeout evaluator.

    Stubbed/dry paths MUST NOT flip TESTNET_*_PROVEN. Real productive evidence
    is required to close §11.12.8.
    """
    if SECTION_11_13_STARTED:
        raise ActualStartCloseoutError("SECTION_11_13_MUST_REMAIN_FALSE")
    if stubbed_acceptance and real_productive_evidence:
        raise ActualStartCloseoutError("STUBBED_AND_REAL_MUTUALLY_EXCLUSIVE")
    if stubbed_acceptance:
        return Section11128CloseoutV1(
            closeout_machinery_present=True,
            stubbed_acceptance=True,
            real_productive_evidence=False,
            testnet_order_lifecycle_proven=False,
            testnet_reconciliation_proven=False,
            testnet_restart_proven=False,
            testnet_unknown_submit_recovery_proven=False,
            testnet_duplicate_order_prevention_proven=False,
            testnet_kill_switch_proven=False,
            testnet_autonomous_recovery_proven=False,
            testnet_evidence_verified=False,
            section_11_13_started=False,
            section_11_12_8_closed=False,
        )
    if not real_productive_evidence:
        raise ActualStartCloseoutError("REAL_PRODUCTIVE_EVIDENCE_REQUIRED_FOR_CLOSEOUT")
    # Real path would bind verified productive evidence artifacts; constants stay
    # false until a future real run produces them. This function is the gate.
    proven = all(
        [
            TESTNET_ORDER_LIFECYCLE_PROVEN,
            TESTNET_RECONCILIATION_PROVEN,
            TESTNET_RESTART_PROVEN,
            TESTNET_UNKNOWN_SUBMIT_RECOVERY_PROVEN,
            TESTNET_DUPLICATE_ORDER_PREVENTION_PROVEN,
            TESTNET_KILL_SWITCH_PROVEN,
            TESTNET_AUTONOMOUS_RECOVERY_PROVEN,
            TESTNET_EVIDENCE_VERIFIED,
        ]
    )
    return Section11128CloseoutV1(
        closeout_machinery_present=True,
        stubbed_acceptance=False,
        real_productive_evidence=True,
        testnet_order_lifecycle_proven=TESTNET_ORDER_LIFECYCLE_PROVEN,
        testnet_reconciliation_proven=TESTNET_RECONCILIATION_PROVEN,
        testnet_restart_proven=TESTNET_RESTART_PROVEN,
        testnet_unknown_submit_recovery_proven=TESTNET_UNKNOWN_SUBMIT_RECOVERY_PROVEN,
        testnet_duplicate_order_prevention_proven=TESTNET_DUPLICATE_ORDER_PREVENTION_PROVEN,
        testnet_kill_switch_proven=TESTNET_KILL_SWITCH_PROVEN,
        testnet_autonomous_recovery_proven=TESTNET_AUTONOMOUS_RECOVERY_PROVEN,
        testnet_evidence_verified=TESTNET_EVIDENCE_VERIFIED,
        section_11_13_started=False,
        section_11_12_8_closed=proven,
    )
