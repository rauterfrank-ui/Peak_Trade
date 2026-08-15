#!/usr/bin/env python3
"""Verify §11.13.5.G canary submit-transport preparation evidence pack."""

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

EXPECTED_JSON_NAME = "PREPARATION_RESULT.json"


class CanarySubmitTransportPreparationVerifierError(RuntimeError):
    """Fail-closed verifier error."""


def verify_section_11_13_5_canary_submit_transport_preparation_v1(evidence_root: Path) -> dict:
    root = Path(evidence_root)
    verify = verify_manifest_v1(root)
    if verify["MANIFEST_VERIFY_RC"] != 0:
        raise CanarySubmitTransportPreparationVerifierError(f"MANIFEST_FAIL:{verify['errors']}")
    payload = json.loads((root / EXPECTED_JSON_NAME).read_text(encoding="utf-8"))
    if payload.get("CANARY_SUBMIT_TRANSPORT_IMPLEMENTED") is not True:
        raise CanarySubmitTransportPreparationVerifierError("TRANSPORT_NOT_IMPLEMENTED")
    if payload.get("CANARY_EXECUTED") is not False:
        raise CanarySubmitTransportPreparationVerifierError("CANARY_EXECUTED_MUST_BE_FALSE")
    if int(payload.get("ORDER_COUNT_SUBMITTED", -1)) != 0:
        raise CanarySubmitTransportPreparationVerifierError("ORDER_COUNT_MUST_BE_ZERO")
    if payload.get("LIVE_AUTHORIZED") is not False:
        raise CanarySubmitTransportPreparationVerifierError("LIVE_AUTHORIZED_MUST_BE_FALSE")
    if payload.get("SUBMIT_UNLOCKED") is not False:
        raise CanarySubmitTransportPreparationVerifierError("SUBMIT_UNLOCKED_MUST_BE_FALSE")
    if payload.get("GENERAL_LIVE_SUBMIT_UNLOCKED") is not False:
        raise CanarySubmitTransportPreparationVerifierError("GENERAL_LIVE_UNLOCK_MUST_BE_FALSE")
    if payload.get("OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE_STATUS") != "GRANTED_UNCONSUMED":
        raise CanarySubmitTransportPreparationVerifierError("EXECUTE_GO_MUST_REMAIN_UNCONSUMED")
    if payload.get("SECRET_VALUE_ACCESS") != "NONE":
        raise CanarySubmitTransportPreparationVerifierError("SECRET_VALUE_ACCESS_MUST_BE_NONE")
    return {
        "ok": True,
        "MANIFEST_VERIFY_RC": 0,
        "CANARY_SUBMIT_TRANSPORT_IMPLEMENTED": True,
        "CANARY_EXECUTED": False,
        "ORDER_COUNT_SUBMITTED": 0,
        "LIVE_AUTHORIZED": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-root", required=True)
    args = parser.parse_args(argv)
    try:
        result = verify_section_11_13_5_canary_submit_transport_preparation_v1(
            Path(args.evidence_root)
        )
    except (CanarySubmitTransportPreparationVerifierError, Exception) as exc:  # noqa: BLE001
        print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
