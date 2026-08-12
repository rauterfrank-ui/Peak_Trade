#!/usr/bin/env python3
"""Verify §11.13.5.E economic baseline + OKX clearance evidence."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.economic_baseline_and_okx_clearance_v1 import (  # noqa: E402
    CLEARANCE_ABSENT_OR_UNPROVEN,
    CLEARANCE_PRESENT_PROVEN,
    OWNER_GO_ECONOMIC_BASELINE_AND_OKX_CLEARANCE_EVIDENCE,
    TERMINAL_FAIL_CLOSED,
    TERMINAL_RECON_PROVEN_CLEARANCE_PROVEN_GATE_PASS,
    TERMINAL_RECON_PROVEN_CLEARANCE_UNPROVEN,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.evidence_v1 import (  # noqa: E402
    verify_manifest_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.exchange_truth_adoption_v1 import (  # noqa: E402
    STATUS_ADOPTED_PROVEN,
)


class EconomicBaselineOkxClearanceVerifierError(RuntimeError):
    """Fail-closed verifier error."""


def verify_section_11_13_5_economic_baseline_and_okx_clearance_evidence_v1(
    evidence_root: Path,
) -> dict:
    root = Path(evidence_root)
    verify = verify_manifest_v1(root)
    if verify["MANIFEST_VERIFY_RC"] != 0:
        raise EconomicBaselineOkxClearanceVerifierError(f"MANIFEST_FAIL:{verify['errors']}")

    def load(name: str) -> dict:
        return json.loads((root / name).read_text(encoding="utf-8"))

    result = load("ECONOMIC_BASELINE_AND_OKX_CLEARANCE_RESULT.json")
    closeout = load("MACHINE_READABLE_CLOSEOUT.json")
    claims = load("claims.json")
    zero = load("zero_write_assertions.json")
    redaction = load("redaction_check.json")
    gate = load("LIVE_CANARY_CYBERSECURITY_GATE.json")
    clearance = load("OKX_TEMP_SECURITY_CLEARANCE.json")
    after = load("RECONCILIATION_AFTER_ADOPTION.json")

    if closeout.get("OWNER_GO_BOUND") != OWNER_GO_ECONOMIC_BASELINE_AND_OKX_CLEARANCE_EVIDENCE:
        raise EconomicBaselineOkxClearanceVerifierError("OWNER_GO_MISBOUND")
    if result.get("TERMINAL_STATE") not in {
        TERMINAL_FAIL_CLOSED,
        TERMINAL_RECON_PROVEN_CLEARANCE_UNPROVEN,
        TERMINAL_RECON_PROVEN_CLEARANCE_PROVEN_GATE_PASS,
    }:
        raise EconomicBaselineOkxClearanceVerifierError("UNEXPECTED_TERMINAL")
    if closeout.get("TERMINAL_STATE") != result.get("TERMINAL_STATE"):
        raise EconomicBaselineOkxClearanceVerifierError("TERMINAL_MISMATCH")
    if closeout.get("LIVE_CANARY_MINIMUM_EXPOSURE_EXECUTED") is not False:
        raise EconomicBaselineOkxClearanceVerifierError("CANARY_EXECUTED_CLAIM")
    if closeout.get("LIVE_CANARY_MINIMUM_EXPOSURE_PROVEN") is not False:
        raise EconomicBaselineOkxClearanceVerifierError("CANARY_PROVEN_CLAIM")
    if closeout.get("LIVE_AUTHORIZED") is not False:
        raise EconomicBaselineOkxClearanceVerifierError("LIVE_AUTHORIZED_CLAIM")
    if closeout.get("ORDER_EFFECT") != "NONE":
        raise EconomicBaselineOkxClearanceVerifierError("ORDER_EFFECT")
    if closeout.get("ACCOUNT_MUTATION_EFFECT") != "NONE":
        raise EconomicBaselineOkxClearanceVerifierError("ACCOUNT_MUTATION")
    if claims.get("ORDER_SUBMITTED") is not False:
        raise EconomicBaselineOkxClearanceVerifierError("ORDER_SUBMITTED_CLAIM")
    if zero.get("ORDER_REQUEST_COUNT") != 0:
        raise EconomicBaselineOkxClearanceVerifierError("ORDER_COUNT")
    if zero.get("WITHDRAW_REQUEST_COUNT") != 0:
        raise EconomicBaselineOkxClearanceVerifierError("WITHDRAW_COUNT")
    if zero.get("P2P_SELL_REQUEST_COUNT") != 0:
        raise EconomicBaselineOkxClearanceVerifierError("P2P_COUNT")
    if redaction.get("SECRET_VALUE_PERSISTED") is not False:
        raise EconomicBaselineOkxClearanceVerifierError("SECRET_PERSISTED")
    if clearance.get("WITHDRAWAL_OR_P2P_MUTATION_USED_TO_TEST_CLEARANCE") is not False:
        raise EconomicBaselineOkxClearanceVerifierError("CLEARANCE_TEST_MUTATION")

    if result.get("TERMINAL_STATE") in {
        TERMINAL_RECON_PROVEN_CLEARANCE_UNPROVEN,
        TERMINAL_RECON_PROVEN_CLEARANCE_PROVEN_GATE_PASS,
    }:
        if result.get("EXCHANGE_TRUTH_ADOPTION_STATUS") != STATUS_ADOPTED_PROVEN:
            raise EconomicBaselineOkxClearanceVerifierError("EXCHANGE_TRUTH_NOT_PRESERVED")
        if result.get("LIVE_RECONCILIATION_PROVEN") is not True:
            raise EconomicBaselineOkxClearanceVerifierError("LIVE_RECON_NOT_PROVEN")
        if result.get("BLOCKS_NEW_ENTRY") is not False:
            raise EconomicBaselineOkxClearanceVerifierError("BLOCKS_NEW_ENTRY_NOT_CLEARED")
        if after.get("ALL_LAYERS_MATCH") is not True:
            raise EconomicBaselineOkxClearanceVerifierError("AFTER_NOT_ALL_MATCH")
        if after.get("UNRESOLVED_ECONOMIC_DIVERGENCE") is not False:
            raise EconomicBaselineOkxClearanceVerifierError("AFTER_STILL_UNRESOLVED")
        if result.get("READ_ATTESTATION") is not True:
            raise EconomicBaselineOkxClearanceVerifierError("READ")
        if result.get("TRADE_ATTESTATION") is not True:
            raise EconomicBaselineOkxClearanceVerifierError("TRADE")
        if result.get("WITHDRAW_ATTESTATION") is not False:
            raise EconomicBaselineOkxClearanceVerifierError("WITHDRAW")

    if result.get("TERMINAL_STATE") == TERMINAL_RECON_PROVEN_CLEARANCE_UNPROVEN:
        if clearance.get("OKX_TEMP_SECURITY_CLEARANCE_EVIDENCE") != CLEARANCE_ABSENT_OR_UNPROVEN:
            raise EconomicBaselineOkxClearanceVerifierError("CLEARANCE_MUST_BE_ABSENT")
        if gate.get("LIVE_CANARY_CYBERSECURITY_GATE") != "NOT_PASSED":
            raise EconomicBaselineOkxClearanceVerifierError("CYBER_GATE_MUST_NOT_PASS")
        if "OKX_TEMP_SECURITY_RESTRICTION_CLEARANCE_EVIDENCE_ABSENT" not in (
            gate.get("BLOCKERS") or []
        ):
            raise EconomicBaselineOkxClearanceVerifierError("CLEARANCE_BLOCKER_MISSING")
        if closeout.get("CANONICAL_NEXT_STEP") == "OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE":
            raise EconomicBaselineOkxClearanceVerifierError("EXECUTE_GO_PREMATURE")

    if result.get("TERMINAL_STATE") == TERMINAL_RECON_PROVEN_CLEARANCE_PROVEN_GATE_PASS:
        if clearance.get("OKX_TEMP_SECURITY_CLEARANCE_EVIDENCE") != CLEARANCE_PRESENT_PROVEN:
            raise EconomicBaselineOkxClearanceVerifierError("CLEARANCE_MUST_BE_PRESENT")
        if gate.get("LIVE_CANARY_CYBERSECURITY_GATE") != "PASS":
            raise EconomicBaselineOkxClearanceVerifierError("CYBER_GATE_MUST_PASS")

    return {
        "ok": True,
        "MANIFEST_VERIFY_RC": 0,
        "TERMINAL_STATE": result["TERMINAL_STATE"],
        "LIVE_RECONCILIATION_PROVEN": result["LIVE_RECONCILIATION_PROVEN"],
        "BLOCKS_NEW_ENTRY": result["BLOCKS_NEW_ENTRY"],
        "OKX_TEMP_SECURITY_CLEARANCE_EVIDENCE": result["OKX_TEMP_SECURITY_CLEARANCE_EVIDENCE"],
        "LIVE_CANARY_CYBERSECURITY_GATE": gate["LIVE_CANARY_CYBERSECURITY_GATE"],
        "OWNER_GO_BOUND": closeout["OWNER_GO_BOUND"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-root", required=True)
    args = parser.parse_args()
    try:
        result = verify_section_11_13_5_economic_baseline_and_okx_clearance_evidence_v1(
            Path(args.evidence_root)
        )
    except Exception as exc:  # noqa: BLE001 - CLI fail-closed
        print(f"VERIFY_FAIL:{exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
