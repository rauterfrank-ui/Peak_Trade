#!/usr/bin/env python3
"""Verify §11.13.5.C LIVE canary trade-key attestation evidence."""

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
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.canary_trade_capability_attestation_v1 import (  # noqa: E402
    OWNER_GO_TRADE_KEY_ATTESTATION,
    TERMINAL_FAIL_CLOSED,
    TERMINAL_PROVEN,
)


class TradeKeyAttestationVerifierError(RuntimeError):
    """Fail-closed verifier error."""


def verify_section_11_13_5_trade_capability_attestation_evidence_v1(evidence_root: Path) -> dict:
    root = Path(evidence_root)
    verify = verify_manifest_v1(root)
    if verify["MANIFEST_VERIFY_RC"] != 0:
        raise TradeKeyAttestationVerifierError(f"MANIFEST_FAIL:{verify['errors']}")

    def load(name: str) -> dict:
        return json.loads((root / name).read_text(encoding="utf-8"))

    result = load("TRADE_CAPABILITY_ATTESTATION_RESULT.json")
    closeout = load("MACHINE_READABLE_CLOSEOUT.json")
    claims = load("claims.json")
    zero = load("zero_write_assertions.json")
    redaction = load("redaction_check.json")
    gate = load("LIVE_CANARY_CYBERSECURITY_GATE.json")
    probe = load("SECRETREF_PROBE.json")

    if closeout.get("OWNER_GO_BOUND") != OWNER_GO_TRADE_KEY_ATTESTATION:
        raise TradeKeyAttestationVerifierError("OWNER_GO_MISBOUND")
    if result.get("TERMINAL_STATE") not in {TERMINAL_FAIL_CLOSED, TERMINAL_PROVEN}:
        raise TradeKeyAttestationVerifierError("UNEXPECTED_TERMINAL")
    if closeout.get("TERMINAL_STATE") != result.get("TERMINAL_STATE"):
        raise TradeKeyAttestationVerifierError("TERMINAL_MISMATCH")
    if closeout.get("LIVE_CANARY_MINIMUM_EXPOSURE_EXECUTED") is not False:
        raise TradeKeyAttestationVerifierError("CANARY_EXECUTED_CLAIM")
    if closeout.get("LIVE_CANARY_MINIMUM_EXPOSURE_PROVEN") is not False:
        raise TradeKeyAttestationVerifierError("CANARY_PROVEN_CLAIM")
    if closeout.get("LIVE_AUTHORIZED") is not False:
        raise TradeKeyAttestationVerifierError("LIVE_AUTHORIZED_CLAIM")
    if closeout.get("BLOCKS_NEW_ENTRY") is not True:
        raise TradeKeyAttestationVerifierError("BLOCKS_NEW_ENTRY_CLEARED")
    if closeout.get("LIVE_RECONCILIATION_PROVEN") is not False:
        raise TradeKeyAttestationVerifierError("LIVE_RECON_PROVEN_CLAIM")
    if closeout.get("ORDER_EFFECT") != "NONE":
        raise TradeKeyAttestationVerifierError("ORDER_EFFECT")
    if closeout.get("ACCOUNT_MUTATION_EFFECT") != "NONE":
        raise TradeKeyAttestationVerifierError("ACCOUNT_MUTATION")
    if closeout.get("SECRET_VALUE_ACCESS") != "NONE":
        raise TradeKeyAttestationVerifierError("SECRET_ACCESS")
    if closeout.get("EXCHANGE_TRUTH_ADOPTION_AUTHORIZED_BY_THIS_GO") is not False:
        raise TradeKeyAttestationVerifierError("EXCHANGE_TRUTH_ADOPTION_CLAIM")
    if (
        gate.get("LIVE_CANARY_CYBERSECURITY_GATE") != "NOT_PASSED"
        and result.get("TERMINAL_STATE") == TERMINAL_FAIL_CLOSED
    ):
        raise TradeKeyAttestationVerifierError("CYBER_GATE_WEAKENED")
    if claims.get("ORDER_SUBMITTED") is not False:
        raise TradeKeyAttestationVerifierError("ORDER_SUBMITTED_CLAIM")
    if zero.get("ORDER_REQUEST_COUNT") != 0:
        raise TradeKeyAttestationVerifierError("ORDER_COUNT")
    if redaction.get("SECRET_VALUE_PERSISTED") is not False:
        raise TradeKeyAttestationVerifierError("SECRET_PERSISTED")
    if probe.get("SECRET_VALUES_PERSISTED") is not False:
        raise TradeKeyAttestationVerifierError("PROBE_SECRET_PERSISTED")
    if probe.get("SECRET_DIGESTS_PERSISTED") is not False:
        raise TradeKeyAttestationVerifierError("PROBE_SECRET_DIGEST_PERSISTED")

    # Fail-closed path invariants.
    if result.get("TERMINAL_STATE") == TERMINAL_FAIL_CLOSED:
        if result.get("TRADE_ATTESTATION") is not False:
            raise TradeKeyAttestationVerifierError("TRADE_ATTESTATION_MUST_BE_FALSE")
        if result.get("CANARY_TRADE_KEY_BINDING") != "NOT_PROVEN_FAIL_CLOSED":
            raise TradeKeyAttestationVerifierError("BINDING_STATUS")
        if closeout.get("SECRETREF_STATUS") != "MISSING_FAIL_CLOSED":
            raise TradeKeyAttestationVerifierError("SECRETREF_STATUS")

    # Proven path invariants (dedicated canary key bound; still no execute).
    if result.get("TERMINAL_STATE") == TERMINAL_PROVEN:
        if result.get("TRADE_ATTESTATION") is not True:
            raise TradeKeyAttestationVerifierError("TRADE_ATTESTATION_MUST_BE_TRUE")
        if result.get("WITHDRAW_ATTESTATION") is not False:
            raise TradeKeyAttestationVerifierError("WITHDRAW_MUST_BE_FALSE")
        if result.get("CANARY_TRADE_KEY_BINDING") != "PROVEN":
            raise TradeKeyAttestationVerifierError("BINDING_STATUS_PROVEN")
        if closeout.get("SECRETREF_STATUS") != "RESOLVED":
            raise TradeKeyAttestationVerifierError("SECRETREF_STATUS_RESOLVED")
        if result.get("PRIOR_DRY_RUN_KEY_REUSED") is not False:
            raise TradeKeyAttestationVerifierError("PRIOR_KEY_REUSED")
        if gate.get("LIVE_CANARY_CYBERSECURITY_GATE") != "NOT_PASSED":
            # Passkey reset / trade-key attestation alone must not clear the canary cyber gate.
            raise TradeKeyAttestationVerifierError("CYBER_GATE_UNEXPECTED_PASS")
        if closeout.get("EARLIEST_UNRESOLVED_DEPENDENCY") != "OWNER_GO_EXCHANGE_TRUTH_ADOPTION":
            raise TradeKeyAttestationVerifierError("NEXT_DEPENDENCY")

    return {
        "ok": True,
        "MANIFEST_VERIFY_RC": 0,
        "TERMINAL_STATE": result["TERMINAL_STATE"],
        "TRADE_ATTESTATION": result["TRADE_ATTESTATION"],
        "WITHDRAW_ATTESTATION": result["WITHDRAW_ATTESTATION"],
        "SECRETREF_STATUS": closeout["SECRETREF_STATUS"],
        "LIVE_CANARY_CYBERSECURITY_GATE": gate["LIVE_CANARY_CYBERSECURITY_GATE"],
        "OWNER_GO_BOUND": closeout["OWNER_GO_BOUND"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-root", required=True)
    args = parser.parse_args()
    try:
        result = verify_section_11_13_5_trade_capability_attestation_evidence_v1(
            Path(args.evidence_root)
        )
    except Exception as exc:  # noqa: BLE001 - CLI fail-closed
        print(f"VERIFY_FAIL:{exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
