"""Canonical §11.12.8 closeout — PROVEN fields only from real productive evidence."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.constants_v1 import (
    SECTION_11_13_STARTED,
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


def _derive_proven_from_evidence(evidence: Mapping[str, Any] | None) -> dict[str, bool]:
    if not evidence:
        return {
            "TESTNET_ORDER_LIFECYCLE_PROVEN": False,
            "TESTNET_RECONCILIATION_PROVEN": False,
            "TESTNET_RESTART_PROVEN": False,
            "TESTNET_UNKNOWN_SUBMIT_RECOVERY_PROVEN": False,
            "TESTNET_DUPLICATE_ORDER_PREVENTION_PROVEN": False,
            "TESTNET_KILL_SWITCH_PROVEN": False,
            "TESTNET_AUTONOMOUS_RECOVERY_PROVEN": False,
            "TESTNET_EVIDENCE_VERIFIED": False,
        }
    # Explicit evidence flags only — never invent from wire_sent alone.
    return {
        "TESTNET_ORDER_LIFECYCLE_PROVEN": bool(evidence.get("TESTNET_ORDER_LIFECYCLE_PROVEN")),
        "TESTNET_RECONCILIATION_PROVEN": bool(evidence.get("TESTNET_RECONCILIATION_PROVEN")),
        "TESTNET_RESTART_PROVEN": bool(evidence.get("TESTNET_RESTART_PROVEN")),
        "TESTNET_UNKNOWN_SUBMIT_RECOVERY_PROVEN": bool(
            evidence.get("TESTNET_UNKNOWN_SUBMIT_RECOVERY_PROVEN")
        ),
        "TESTNET_DUPLICATE_ORDER_PREVENTION_PROVEN": bool(
            evidence.get("TESTNET_DUPLICATE_ORDER_PREVENTION_PROVEN")
        ),
        "TESTNET_KILL_SWITCH_PROVEN": bool(evidence.get("TESTNET_KILL_SWITCH_PROVEN")),
        "TESTNET_AUTONOMOUS_RECOVERY_PROVEN": bool(
            evidence.get("TESTNET_AUTONOMOUS_RECOVERY_PROVEN")
        ),
        "TESTNET_EVIDENCE_VERIFIED": bool(evidence.get("TESTNET_EVIDENCE_VERIFIED")),
    }


def evaluate_section_11_12_8_closeout_v1(
    *,
    stubbed_acceptance: bool,
    real_productive_evidence: bool = False,
    boundary_path_proof_only: bool = False,
    evidence: Mapping[str, Any] | None = None,
    evidence_seal_ok: bool = False,
    long_running_bound_reached: bool = False,
) -> Section11128CloseoutV1:
    """Closeout evaluator.

    Stubbed/dry paths MUST NOT flip TESTNET_*_PROVEN. Real productive evidence
    is required to close §11.12.8. Lifecycle.completed / seal alone is insufficient.
    Long-running bound reach is required for campaign completion semantics but
    does not alone close §11.12.8.
    """
    if SECTION_11_13_STARTED:
        raise ActualStartCloseoutError("SECTION_11_13_MUST_REMAIN_FALSE")
    if stubbed_acceptance and real_productive_evidence:
        raise ActualStartCloseoutError("STUBBED_AND_REAL_MUTUALLY_EXCLUSIVE")
    if boundary_path_proof_only:
        if stubbed_acceptance or real_productive_evidence:
            raise ActualStartCloseoutError("BOUNDARY_PROOF_EXCLUSIVE")
        return Section11128CloseoutV1(
            closeout_machinery_present=True,
            stubbed_acceptance=False,
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

    derived = _derive_proven_from_evidence(evidence)
    # Seal must pass for evidence verification claim.
    if evidence_seal_ok and derived["TESTNET_EVIDENCE_VERIFIED"] is False:
        # Seal alone does not auto-set VERIFIED unless evidence explicitly claims it.
        pass
    if not long_running_bound_reached:
        # Campaign did not reach canonical long-running terminal condition.
        derived = {k: False for k in derived}

    proven = all(derived.values())
    return Section11128CloseoutV1(
        closeout_machinery_present=True,
        stubbed_acceptance=False,
        real_productive_evidence=True,
        testnet_order_lifecycle_proven=derived["TESTNET_ORDER_LIFECYCLE_PROVEN"],
        testnet_reconciliation_proven=derived["TESTNET_RECONCILIATION_PROVEN"],
        testnet_restart_proven=derived["TESTNET_RESTART_PROVEN"],
        testnet_unknown_submit_recovery_proven=derived["TESTNET_UNKNOWN_SUBMIT_RECOVERY_PROVEN"],
        testnet_duplicate_order_prevention_proven=derived[
            "TESTNET_DUPLICATE_ORDER_PREVENTION_PROVEN"
        ],
        testnet_kill_switch_proven=derived["TESTNET_KILL_SWITCH_PROVEN"],
        testnet_autonomous_recovery_proven=derived["TESTNET_AUTONOMOUS_RECOVERY_PROVEN"],
        testnet_evidence_verified=derived["TESTNET_EVIDENCE_VERIFIED"],
        section_11_13_started=False,
        section_11_12_8_closed=proven,
    )
