#!/usr/bin/env python3
"""Verify §11.13.5.D Exchange Truth Adoption evidence."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.evidence_v1 import (  # noqa: E402
    verify_manifest_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.exchange_truth_adoption_v1 import (  # noqa: E402
    OWNER_GO_EXCHANGE_TRUTH_ADOPTION,
    STATUS_ADOPTED_PROVEN,
    TERMINAL_ADOPTED_CYBER_NOT_PASSED,
    TERMINAL_ADOPTED_CYBER_PASS,
    TERMINAL_FAIL_CLOSED,
)


class ExchangeTruthAdoptionVerifierError(RuntimeError):
    """Fail-closed verifier error."""


def verify_section_11_13_5_exchange_truth_adoption_evidence_v1(evidence_root: Path) -> dict:
    root = Path(evidence_root)
    verify = verify_manifest_v1(root)
    if verify["MANIFEST_VERIFY_RC"] != 0:
        raise ExchangeTruthAdoptionVerifierError(f"MANIFEST_FAIL:{verify['errors']}")

    def load(name: str) -> dict:
        return json.loads((root / name).read_text(encoding="utf-8"))

    result = load("EXCHANGE_TRUTH_ADOPTION_RESULT.json")
    closeout = load("MACHINE_READABLE_CLOSEOUT.json")
    claims = load("claims.json")
    zero = load("zero_write_assertions.json")
    redaction = load("redaction_check.json")
    gate = load("LIVE_CANARY_CYBERSECURITY_GATE.json")
    economic = load("ECONOMIC_DIVERGENCE_STANDING.json")

    if closeout.get("OWNER_GO_BOUND") != OWNER_GO_EXCHANGE_TRUTH_ADOPTION:
        raise ExchangeTruthAdoptionVerifierError("OWNER_GO_MISBOUND")
    if result.get("TERMINAL_STATE") not in {
        TERMINAL_FAIL_CLOSED,
        TERMINAL_ADOPTED_CYBER_NOT_PASSED,
        TERMINAL_ADOPTED_CYBER_PASS,
    }:
        raise ExchangeTruthAdoptionVerifierError("UNEXPECTED_TERMINAL")
    if closeout.get("TERMINAL_STATE") != result.get("TERMINAL_STATE"):
        raise ExchangeTruthAdoptionVerifierError("TERMINAL_MISMATCH")
    if closeout.get("LIVE_CANARY_MINIMUM_EXPOSURE_EXECUTED") is not False:
        raise ExchangeTruthAdoptionVerifierError("CANARY_EXECUTED_CLAIM")
    if closeout.get("LIVE_CANARY_MINIMUM_EXPOSURE_PROVEN") is not False:
        raise ExchangeTruthAdoptionVerifierError("CANARY_PROVEN_CLAIM")
    if closeout.get("LIVE_AUTHORIZED") is not False:
        raise ExchangeTruthAdoptionVerifierError("LIVE_AUTHORIZED_CLAIM")
    if closeout.get("BLOCKS_NEW_ENTRY") is not True:
        raise ExchangeTruthAdoptionVerifierError("BLOCKS_NEW_ENTRY_CLEARED")
    if closeout.get("LIVE_RECONCILIATION_PROVEN") is not False:
        raise ExchangeTruthAdoptionVerifierError("LIVE_RECON_PROVEN_CLAIM")
    if closeout.get("ORDER_EFFECT") != "NONE":
        raise ExchangeTruthAdoptionVerifierError("ORDER_EFFECT")
    if closeout.get("ACCOUNT_MUTATION_EFFECT") != "NONE":
        raise ExchangeTruthAdoptionVerifierError("ACCOUNT_MUTATION")
    if closeout.get("SECRET_VALUE_ACCESS") != "NONE":
        raise ExchangeTruthAdoptionVerifierError("SECRET_ACCESS")
    if closeout.get("NETWORK_EFFECT") != "NONE":
        raise ExchangeTruthAdoptionVerifierError("NETWORK_EFFECT")
    if claims.get("ORDER_SUBMITTED") is not False:
        raise ExchangeTruthAdoptionVerifierError("ORDER_SUBMITTED_CLAIM")
    if zero.get("ORDER_REQUEST_COUNT") != 0:
        raise ExchangeTruthAdoptionVerifierError("ORDER_COUNT")
    if redaction.get("SECRET_VALUE_PERSISTED") is not False:
        raise ExchangeTruthAdoptionVerifierError("SECRET_PERSISTED")
    if economic.get("UNRESOLVED_ECONOMIC_DIVERGENCE_BLOCKS_NEW_ENTRY") is not True:
        raise ExchangeTruthAdoptionVerifierError("ECONOMIC_DIVERGENCE_CLEARED")
    if economic.get("OWNER_ECONOMIC_BASELINE_POLICIES_ADOPTED_BY_THIS_GO") is not False:
        raise ExchangeTruthAdoptionVerifierError("ECONOMIC_POLICIES_ADOPTED")

    if result.get("TERMINAL_STATE") in {
        TERMINAL_ADOPTED_CYBER_NOT_PASSED,
        TERMINAL_ADOPTED_CYBER_PASS,
    }:
        if result.get("EXCHANGE_TRUTH_ADOPTION_STATUS") != STATUS_ADOPTED_PROVEN:
            raise ExchangeTruthAdoptionVerifierError("ADOPTION_STATUS")
        if result.get("READ_ATTESTATION") is not True:
            raise ExchangeTruthAdoptionVerifierError("READ")
        if result.get("TRADE_ATTESTATION") is not True:
            raise ExchangeTruthAdoptionVerifierError("TRADE")
        if result.get("WITHDRAW_ATTESTATION") is not False:
            raise ExchangeTruthAdoptionVerifierError("WITHDRAW")
        if result.get("KEY_BINDING_STATUS") != "PROVEN":
            raise ExchangeTruthAdoptionVerifierError("KEY_BINDING")
        if result.get("CANARY_SECRETREF_STATUS") != "RESOLVED":
            raise ExchangeTruthAdoptionVerifierError("SECRETREF")
        if result.get("OKX_TEMP_SECURITY_RESTRICTION") != "24h_no_withdrawals_and_no_p2p_sell":
            raise ExchangeTruthAdoptionVerifierError("OKX_TEMP_RESTRICTION")
        if result.get("OKX_TEMP_SECURITY_RESTRICTION_BYPASS_FORBIDDEN") is not True:
            raise ExchangeTruthAdoptionVerifierError("OKX_BYPASS")

    if result.get("TERMINAL_STATE") == TERMINAL_ADOPTED_CYBER_NOT_PASSED:
        if gate.get("LIVE_CANARY_CYBERSECURITY_GATE") != "NOT_PASSED":
            raise ExchangeTruthAdoptionVerifierError("CYBER_GATE_MUST_NOT_PASS")
        if closeout.get("CANONICAL_NEXT_STEP") == "OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE":
            raise ExchangeTruthAdoptionVerifierError("EXECUTE_GO_PREMATURE")

    if result.get("TERMINAL_STATE") == TERMINAL_ADOPTED_CYBER_PASS:
        if gate.get("LIVE_CANARY_CYBERSECURITY_GATE") != "PASS":
            raise ExchangeTruthAdoptionVerifierError("CYBER_GATE_MUST_PASS")
        if closeout.get("BLOCKS_NEW_ENTRY") is not True:
            raise ExchangeTruthAdoptionVerifierError("BLOCKS_NEW_ENTRY_CLEARED_ON_PASS")

    return {
        "ok": True,
        "MANIFEST_VERIFY_RC": 0,
        "TERMINAL_STATE": result["TERMINAL_STATE"],
        "EXCHANGE_TRUTH_ADOPTION_STATUS": result["EXCHANGE_TRUTH_ADOPTION_STATUS"],
        "LIVE_CANARY_CYBERSECURITY_GATE": gate["LIVE_CANARY_CYBERSECURITY_GATE"],
        "OWNER_GO_BOUND": closeout["OWNER_GO_BOUND"],
        "BLOCKS_NEW_ENTRY": closeout["BLOCKS_NEW_ENTRY"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-root", required=True)
    args = parser.parse_args()
    try:
        result = verify_section_11_13_5_exchange_truth_adoption_evidence_v1(
            Path(args.evidence_root)
        )
    except Exception as exc:  # noqa: BLE001 - CLI fail-closed
        print(f"VERIFY_FAIL:{exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
