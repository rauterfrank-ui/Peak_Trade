#!/usr/bin/env python3
"""Verify §11.13.5.E1 fresh OKX temp-security clearance collection evidence."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.economic_baseline_and_okx_clearance_v1 import (  # noqa: E402
    CLEARANCE_PRESENT_PROVEN,
    evaluate_okx_temp_security_clearance_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.evidence_v1 import (  # noqa: E402
    verify_manifest_v1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (  # noqa: E402
    REUSED_BINDING_ACCOUNT_SCOPE,
)

OWNER_GO_COLLECTION = (
    "CAP11_OKX_TEMP_SECURITY_CLEARANCE_FRESH_PRODUCTIVE_READ_ONLY_EVIDENCE_COLLECTION"
)
EXPECTED_ORIGIN_MAIN_SHA = "c271364d1cc85d65cabc6f1938fe5b9ed8b3fc64"
EXPECTED_JSON_NAME = "CLEARANCE_EVIDENCE_COLLECTION_RESULT.json"


class OkxTempSecurityClearanceCollectionVerifierError(RuntimeError):
    """Fail-closed verifier error."""


def verify_section_11_13_5_okx_temp_security_clearance_evidence_collection_v1(
    evidence_root: Path,
) -> dict:
    root = Path(evidence_root)
    verify = verify_manifest_v1(root)
    if verify["MANIFEST_VERIFY_RC"] != 0:
        raise OkxTempSecurityClearanceCollectionVerifierError(f"MANIFEST_FAIL:{verify['errors']}")

    payload = json.loads((root / EXPECTED_JSON_NAME).read_text(encoding="utf-8"))
    if payload.get("OWNER_GO") != OWNER_GO_COLLECTION:
        raise OkxTempSecurityClearanceCollectionVerifierError("OWNER_GO_MISBOUND")
    if payload.get("CURRENT_ORIGIN_MAIN_SHA") != EXPECTED_ORIGIN_MAIN_SHA:
        raise OkxTempSecurityClearanceCollectionVerifierError("ORIGIN_MAIN_SHA_MISMATCH")
    if payload.get("CLEARANCE_EVIDENCE") != "PASS":
        raise OkxTempSecurityClearanceCollectionVerifierError("CLEARANCE_EVIDENCE_NOT_PASS")
    if payload.get("WALL_CLOCK_ALONE_USED_AS_CLEARANCE") is not False:
        raise OkxTempSecurityClearanceCollectionVerifierError("WALL_CLOCK_ALONE")
    if payload.get("WITHDRAWAL_OR_P2P_MUTATION_USED_TO_TEST_CLEARANCE") is not False:
        raise OkxTempSecurityClearanceCollectionVerifierError("CLEARANCE_TEST_MUTATION")
    if payload.get("WITHDRAWAL_SUBMITTED") is not False:
        raise OkxTempSecurityClearanceCollectionVerifierError("WITHDRAWAL_SUBMITTED")
    if payload.get("P2P_SELL_ATTEMPTED") is not False:
        raise OkxTempSecurityClearanceCollectionVerifierError("P2P_SELL_ATTEMPTED")
    if payload.get("ORDERS_SUBMITTED") is not False:
        raise OkxTempSecurityClearanceCollectionVerifierError("ORDERS_SUBMITTED")
    if payload.get("LIVE_AUTHORIZED") is not False:
        raise OkxTempSecurityClearanceCollectionVerifierError("LIVE_AUTHORIZED_CLAIM")
    if payload.get("LIVE_CANARY_CYBERSECURITY_GATE") != "NOT_REEVALUATED":
        raise OkxTempSecurityClearanceCollectionVerifierError("GATE_REEVALUATED_CLAIM")
    if payload.get("SSOT_MUTATED") is not False:
        raise OkxTempSecurityClearanceCollectionVerifierError("COLLECTION_SSOT_MUTATED")
    if payload.get("PRODUCTIVE_WITHDRAWAL_UI_OBSERVED") is not True:
        raise OkxTempSecurityClearanceCollectionVerifierError("WITHDRAWAL_UI_NOT_OBSERVED")
    if payload.get("RESTRICTION_BANNER_PRESENT") is not False:
        raise OkxTempSecurityClearanceCollectionVerifierError("BANNER_STILL_PRESENT")
    if payload.get("RESTRICTION_STILL_ACTIVE") is not False:
        raise OkxTempSecurityClearanceCollectionVerifierError("RESTRICTION_STILL_ACTIVE")

    binding = payload.get("ACCOUNT_ENVIRONMENT_BINDING") or {}
    if binding.get("ACCOUNT_SCOPE_BINDING") != REUSED_BINDING_ACCOUNT_SCOPE:
        raise OkxTempSecurityClearanceCollectionVerifierError("ACCOUNT_SCOPE_MISMATCH")
    if binding.get("UID_MATCHES_SECTION_11_13_5_E") is not True:
        raise OkxTempSecurityClearanceCollectionVerifierError("UID_NOT_BOUND")
    if binding.get("EMAIL_PERSISTED") is not False:
        raise OkxTempSecurityClearanceCollectionVerifierError("EMAIL_PERSISTED")
    if binding.get("COOKIES_PERSISTED") is not False:
        raise OkxTempSecurityClearanceCollectionVerifierError("COOKIES_PERSISTED")
    if binding.get("TOKENS_PERSISTED") is not False:
        raise OkxTempSecurityClearanceCollectionVerifierError("TOKENS_PERSISTED")

    evaluator = payload.get("CANONICAL_EVALUATOR") or {}
    re_eval = evaluate_okx_temp_security_clearance_v1(
        restriction_still_active=bool(payload.get("RESTRICTION_STILL_ACTIVE")),
        clearance_evidence_present_proven=bool(payload.get("CLEARANCE_EVIDENCE_PRESENT_PROVEN")),
        evidence_source=str(evaluator.get("OKX_CLEARANCE_EVIDENCE_SOURCE") or ""),
        observed_at_utc=str(payload.get("OBSERVED_AT_UTC") or ""),
        restriction_expires_at_local=evaluator.get("RESTRICTION_EXPIRES_AT_LOCAL"),
        account_scope=str(binding.get("ACCOUNT_SCOPE_BINDING") or ""),
    )
    if re_eval.get("OKX_TEMP_SECURITY_CLEARANCE_EVIDENCE") != CLEARANCE_PRESENT_PROVEN:
        raise OkxTempSecurityClearanceCollectionVerifierError("EVALUATOR_NOT_PRESENT_PROVEN")
    if evaluator.get("OKX_TEMP_SECURITY_CLEARANCE_EVIDENCE") != CLEARANCE_PRESENT_PROVEN:
        raise OkxTempSecurityClearanceCollectionVerifierError("PACK_EVALUATOR_NOT_PRESENT_PROVEN")

    p2p = payload.get("P2P_OBSERVATION") or {}
    if p2p.get("P2P_SELL_ATTEMPTED") is not False:
        raise OkxTempSecurityClearanceCollectionVerifierError("P2P_SELL_IN_OBSERVATION")
    if p2p.get("GEO_BLOCK_IS_NOT_24H_TEMP_SECURITY_RESTRICTION") is not True:
        raise OkxTempSecurityClearanceCollectionVerifierError("P2P_GEO_BLOCK_CONFLATED")

    return {
        "ok": True,
        "MANIFEST_VERIFY_RC": 0,
        "OKX_TEMP_SECURITY_CLEARANCE_EVIDENCE": CLEARANCE_PRESENT_PROVEN,
        "LIVE_CANARY_CYBERSECURITY_GATE": payload["LIVE_CANARY_CYBERSECURITY_GATE"],
        "LIVE_AUTHORIZED": False,
        "OWNER_GO_BOUND": payload["OWNER_GO"],
        "CURRENT_ORIGIN_MAIN_SHA": payload["CURRENT_ORIGIN_MAIN_SHA"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-root", required=True)
    args = parser.parse_args()
    try:
        result = verify_section_11_13_5_okx_temp_security_clearance_evidence_collection_v1(
            Path(args.evidence_root)
        )
    except Exception as exc:  # noqa: BLE001 - CLI fail-closed
        print(f"VERIFY_FAIL:{exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
