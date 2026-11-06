#!/usr/bin/env python3
"""Verify §11.13.5.F forensic Live-Canary cybersecurity-gate reevaluation pack."""

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

OWNER_GO_REEVALUATION = "REEVALUATE_LIVE_CANARY_CYBERSECURITY_GATE_AFTER_FRESH_CLEARANCE_PERSIST"
EXPECTED_ORIGIN_MAIN_SHA = "2c72dfd81d226fd04d7f4d4183041b54d1526f55"
EXPECTED_JSON_NAME = "REEVALUATION_RESULT.json"
EXPECTED_REQUIREMENTS_PROVEN = 21
EXPECTED_REQUIREMENTS_TOTAL = 21


class LiveCanaryCybersecurityGateReevaluationVerifierError(RuntimeError):
    """Fail-closed verifier error."""


def verify_section_11_13_5_live_canary_cybersecurity_gate_reevaluation_v1(
    evidence_root: Path,
) -> dict:
    root = Path(evidence_root)
    verify = verify_manifest_v1(root)
    if verify["MANIFEST_VERIFY_RC"] != 0:
        raise LiveCanaryCybersecurityGateReevaluationVerifierError(
            f"MANIFEST_FAIL:{verify['errors']}"
        )

    payload = json.loads((root / EXPECTED_JSON_NAME).read_text(encoding="utf-8"))
    if payload.get("OWNER_GO") != OWNER_GO_REEVALUATION:
        raise LiveCanaryCybersecurityGateReevaluationVerifierError("OWNER_GO_MISBOUND")
    if payload.get("CURRENT_ORIGIN_MAIN_SHA") != EXPECTED_ORIGIN_MAIN_SHA:
        raise LiveCanaryCybersecurityGateReevaluationVerifierError("ORIGIN_MAIN_SHA_MISMATCH")
    if payload.get("LIVE_CANARY_CYBERSECURITY_GATE") != "PASS":
        raise LiveCanaryCybersecurityGateReevaluationVerifierError("GATE_NOT_PASS")
    if payload.get("ALL_REQUIREMENTS_PROVEN") is not True:
        raise LiveCanaryCybersecurityGateReevaluationVerifierError("REQUIREMENTS_NOT_ALL_PROVEN")
    if payload.get("CYBERSECURITY_GATE_REQUIREMENTS_PROVEN") != EXPECTED_REQUIREMENTS_PROVEN:
        raise LiveCanaryCybersecurityGateReevaluationVerifierError("REQUIREMENTS_PROVEN_COUNT")
    if payload.get("CYBERSECURITY_GATE_REQUIREMENTS_TOTAL") != EXPECTED_REQUIREMENTS_TOTAL:
        raise LiveCanaryCybersecurityGateReevaluationVerifierError("REQUIREMENTS_TOTAL_COUNT")
    if payload.get("CYBERSECURITY_GATE_REQUIREMENTS_UNPROVEN") != 0:
        raise LiveCanaryCybersecurityGateReevaluationVerifierError("UNPROVEN_REMAIN")
    if payload.get("UNPROVEN_IDS") not in ([], None):
        raise LiveCanaryCybersecurityGateReevaluationVerifierError("UNPROVEN_IDS_PRESENT")
    if payload.get("AUG13_UNTRACKED_PACKS_USED") is not False:
        raise LiveCanaryCybersecurityGateReevaluationVerifierError("AUG13_PACKS_USED")
    if payload.get("WALL_CLOCK_ALONE_USED") is not False:
        raise LiveCanaryCybersecurityGateReevaluationVerifierError("WALL_CLOCK_ALONE")
    if payload.get("LIVE_AUTHORIZED") is not False:
        raise LiveCanaryCybersecurityGateReevaluationVerifierError("LIVE_AUTHORIZED_CLAIM")
    if payload.get("TESTNET_AUTHORIZED") is not False:
        raise LiveCanaryCybersecurityGateReevaluationVerifierError("TESTNET_AUTHORIZED_CLAIM")
    if payload.get("LIVE_CANARY_EXECUTED") is not False:
        raise LiveCanaryCybersecurityGateReevaluationVerifierError("CANARY_EXECUTED_CLAIM")
    if payload.get("LIVE_CANARY_MINIMUM_EXPOSURE_EXECUTED") is not False:
        raise LiveCanaryCybersecurityGateReevaluationVerifierError("CANARY_MIN_EXPOSURE_EXECUTED")
    if payload.get("NEW_CANARY_OWNER_GO_GRANTED") is not False:
        raise LiveCanaryCybersecurityGateReevaluationVerifierError("NEW_CANARY_GO_GRANTED")
    if payload.get("SSOT_PERSISTENCE_THIS_GO") is not False:
        raise LiveCanaryCybersecurityGateReevaluationVerifierError("REEVAL_SSOT_PERSISTED")
    if payload.get("SUCCESSOR_PHASE_EXECUTED") is not False:
        raise LiveCanaryCybersecurityGateReevaluationVerifierError("SUCCESSOR_PHASE_EXECUTED")
    if payload.get("SECRET_PLAINTEXT_IN_REPO_OR_EVIDENCE") is not False:
        raise LiveCanaryCybersecurityGateReevaluationVerifierError("SECRET_PLAINTEXT")
    if payload.get("SECRETS_CAPTURED") is not False:
        raise LiveCanaryCybersecurityGateReevaluationVerifierError("SECRETS_CAPTURED")
    if payload.get("NETWORK_EFFECT") != "NONE":
        raise LiveCanaryCybersecurityGateReevaluationVerifierError("NETWORK_EFFECT")
    if payload.get("ORDER_EFFECT") != "NONE":
        raise LiveCanaryCybersecurityGateReevaluationVerifierError("ORDER_EFFECT")
    if payload.get("WITHDRAWAL_EFFECT") != "NONE":
        raise LiveCanaryCybersecurityGateReevaluationVerifierError("WITHDRAWAL_EFFECT")
    if payload.get("P2P_EFFECT") != "NONE":
        raise LiveCanaryCybersecurityGateReevaluationVerifierError("P2P_EFFECT")
    if payload.get("MASTER_RUNBOOK_MUTATED") is not False:
        raise LiveCanaryCybersecurityGateReevaluationVerifierError("MASTER_RUNBOOK_MUTATED")
    if payload.get("MAP_OF_TRUTH_MUTATED") is not False:
        raise LiveCanaryCybersecurityGateReevaluationVerifierError("MAP_OF_TRUTH_MUTATED")
    if payload.get("CYBERSECURITY_RUNBOOK_MUTATED") is not False:
        raise LiveCanaryCybersecurityGateReevaluationVerifierError("CYBER_RUNBOOK_MUTATED")

    eval_block = payload.get("LIVE_CANARY_CYBERSECURITY_GATE_EVAL") or {}
    if eval_block.get("LIVE_CANARY_CYBERSECURITY_GATE") != "PASS":
        raise LiveCanaryCybersecurityGateReevaluationVerifierError("EVAL_GATE_NOT_PASS")
    if eval_block.get("BLOCKERS") not in ([], None):
        raise LiveCanaryCybersecurityGateReevaluationVerifierError("EVAL_BLOCKERS_PRESENT")
    if eval_block.get("ok") is not True:
        raise LiveCanaryCybersecurityGateReevaluationVerifierError("EVAL_NOT_OK")
    if eval_block.get("LIVE_AUTHORIZED") is not False:
        raise LiveCanaryCybersecurityGateReevaluationVerifierError("EVAL_LIVE_AUTHORIZED")
    if eval_block.get("NEW_CANARY_OWNER_GO_GRANTED") is not False:
        raise LiveCanaryCybersecurityGateReevaluationVerifierError("EVAL_NEW_CANARY_GO")
    if eval_block.get("WITHDRAW_ATTESTATION") is not False:
        raise LiveCanaryCybersecurityGateReevaluationVerifierError("WITHDRAW_ATTESTATION_TRUE")
    if eval_block.get("TRADE_ATTESTATION") is not True:
        raise LiveCanaryCybersecurityGateReevaluationVerifierError("TRADE_ATTESTATION_FALSE")
    if eval_block.get("READ_ATTESTATION") is not True:
        raise LiveCanaryCybersecurityGateReevaluationVerifierError("READ_ATTESTATION_FALSE")
    if eval_block.get("OKX_TEMP_SECURITY_CLEARANCE_EVIDENCE_PRESENT") is not True:
        raise LiveCanaryCybersecurityGateReevaluationVerifierError("CLEARANCE_NOT_PRESENT")

    claims = json.loads((root / "claims.json").read_text(encoding="utf-8"))
    if claims.get("LIVE_CANARY_CYBERSECURITY_GATE") != "PASS":
        raise LiveCanaryCybersecurityGateReevaluationVerifierError("CLAIMS_GATE_NOT_PASS")
    if claims.get("LIVE_AUTHORIZED") is not False:
        raise LiveCanaryCybersecurityGateReevaluationVerifierError("CLAIMS_LIVE_AUTHORIZED")
    if claims.get("LIVE_CANARY_EXECUTED") is not False:
        raise LiveCanaryCybersecurityGateReevaluationVerifierError("CLAIMS_CANARY_EXECUTED")
    if claims.get("SSOT_PERSISTENCE_THIS_GO") is not False:
        raise LiveCanaryCybersecurityGateReevaluationVerifierError("CLAIMS_SSOT_PERSISTED")
    if claims.get("ORDER_SUBMITTED") is not False:
        raise LiveCanaryCybersecurityGateReevaluationVerifierError("CLAIMS_ORDER_SUBMITTED")

    zero_write = json.loads((root / "zero_write_assertions.json").read_text(encoding="utf-8"))
    if zero_write.get("ORDER_REQUEST_COUNT") != 0:
        raise LiveCanaryCybersecurityGateReevaluationVerifierError("ORDER_REQUEST_COUNT")
    if zero_write.get("WITHDRAW_REQUEST_COUNT") != 0:
        raise LiveCanaryCybersecurityGateReevaluationVerifierError("WITHDRAW_REQUEST_COUNT")
    if zero_write.get("P2P_REQUEST_COUNT") != 0:
        raise LiveCanaryCybersecurityGateReevaluationVerifierError("P2P_REQUEST_COUNT")
    if zero_write.get("SECRET_VALUE_PERSISTED") is not False:
        raise LiveCanaryCybersecurityGateReevaluationVerifierError("SECRET_VALUE_PERSISTED")

    return {
        "ok": True,
        "MANIFEST_VERIFY_RC": 0,
        "LIVE_CANARY_CYBERSECURITY_GATE": "PASS",
        "LIVE_AUTHORIZED": False,
        "LIVE_CANARY_EXECUTED": False,
        "OWNER_GO_BOUND": payload["OWNER_GO"],
        "CURRENT_ORIGIN_MAIN_SHA": payload["CURRENT_ORIGIN_MAIN_SHA"],
        "CYBERSECURITY_GATE_REQUIREMENTS_PROVEN": EXPECTED_REQUIREMENTS_PROVEN,
        "CYBERSECURITY_GATE_REQUIREMENTS_TOTAL": EXPECTED_REQUIREMENTS_TOTAL,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-root", required=True)
    args = parser.parse_args()
    try:
        result = verify_section_11_13_5_live_canary_cybersecurity_gate_reevaluation_v1(
            Path(args.evidence_root)
        )
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
