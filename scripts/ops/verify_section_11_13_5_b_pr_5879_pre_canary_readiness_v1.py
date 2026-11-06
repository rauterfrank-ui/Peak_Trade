#!/usr/bin/env python3
"""Verify §11.13.5.B PR #5879 squash-merge + pre-Canary readiness evidence."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.evidence_v1 import (
    verify_manifest_v1,
)


class PreCanaryReadinessVerifierError(RuntimeError):
    """Fail-closed verifier error."""


def verify_section_11_13_5_b_evidence_v1(evidence_root: Path) -> dict:
    root = Path(evidence_root)
    verify = verify_manifest_v1(root)
    if verify["MANIFEST_VERIFY_RC"] != 0:
        raise PreCanaryReadinessVerifierError(f"MANIFEST_FAIL:{verify['errors']}")

    def load(name: str) -> dict:
        return json.loads((root / name).read_text(encoding="utf-8"))

    terminal = load("PRE_CANARY_READINESS_TERMINAL.json")
    closeout = load("MACHINE_READABLE_CLOSEOUT.json")
    trade = load("TRADE_ATTESTATION_RESOLUTION.json")
    exchange = load("EXCHANGE_TRUTH_ADOPTION_RESOLUTION.json")
    gate = load("LIVE_CANARY_CYBERSECURITY_GATE.json")
    claims = load("claims.json")
    zero = load("zero_write_assertions.json")
    redaction = load("redaction_check.json")

    if closeout.get("PR_STATE") != "MERGED":
        raise PreCanaryReadinessVerifierError("PR_NOT_MERGED")
    if closeout.get("PRIOR_CANARY_OWNER_GO_REUSED") is not False:
        raise PreCanaryReadinessVerifierError("PRIOR_CANARY_GO_REUSED")
    if terminal.get("LIVE_CANARY_MINIMUM_EXPOSURE_EXECUTED") is not False:
        raise PreCanaryReadinessVerifierError("CANARY_EXECUTED_CLAIM")
    if terminal.get("LIVE_AUTHORIZED") is not False:
        raise PreCanaryReadinessVerifierError("LIVE_AUTHORIZED_CLAIM")
    if terminal.get("BLOCKS_NEW_ENTRY") is not True:
        raise PreCanaryReadinessVerifierError("BLOCKS_NEW_ENTRY_CLEARED")
    if terminal.get("LIVE_RECONCILIATION_PROVEN") is not False:
        raise PreCanaryReadinessVerifierError("LIVE_RECON_PROVEN_CLAIM")
    if trade.get("TRADE_ATTESTATION") is not False:
        raise PreCanaryReadinessVerifierError("TRADE_ATTESTATION_MUST_REMAIN_FALSE")
    if trade.get("SECRET_VALUE_ACCESS") != "NONE":
        raise PreCanaryReadinessVerifierError("SECRET_ACCESS")
    if exchange.get("EXCHANGE_TRUTH_ADOPTION_STATUS") != "OWNER_POLICIES_REQUIRED_NOT_ADOPTED":
        raise PreCanaryReadinessVerifierError("UNEXPECTED_ADOPTION_STATUS")
    if gate.get("LIVE_CANARY_CYBERSECURITY_GATE") != "NOT_PASSED":
        raise PreCanaryReadinessVerifierError("CYBER_GATE_UNEXPECTED")
    if terminal.get("TERMINAL_STATE") != "FAIL_CLOSED_PRE_CANARY_BLOCKED":
        raise PreCanaryReadinessVerifierError("UNEXPECTED_TERMINAL")
    if claims.get("ORDER_SUBMITTED") is not False:
        raise PreCanaryReadinessVerifierError("ORDER_SUBMITTED_CLAIM")
    if zero.get("ORDER_REQUEST_COUNT") != 0:
        raise PreCanaryReadinessVerifierError("ORDER_COUNT")
    if redaction.get("SECRET_VALUE_PERSISTED") is not False:
        raise PreCanaryReadinessVerifierError("SECRET_PERSISTED")

    return {
        "ok": True,
        "MANIFEST_VERIFY_RC": 0,
        "TERMINAL_STATE": terminal["TERMINAL_STATE"],
        "LIVE_CANARY_CYBERSECURITY_GATE": gate["LIVE_CANARY_CYBERSECURITY_GATE"],
        "TRADE_ATTESTATION": False,
        "EXCHANGE_TRUTH_ADOPTION_STATUS": exchange["EXCHANGE_TRUTH_ADOPTION_STATUS"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-root", required=True)
    args = parser.parse_args()
    try:
        result = verify_section_11_13_5_b_evidence_v1(Path(args.evidence_root))
    except Exception as exc:  # noqa: BLE001 - CLI fail-closed
        print(f"VERIFY_FAIL:{exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
