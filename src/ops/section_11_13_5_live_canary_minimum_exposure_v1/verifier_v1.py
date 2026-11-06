"""Verifier for §11.13.5 authoring/forensic evidence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    CLAIMS_FILENAME,
    FORENSIC_CLASSIFICATION_FILENAME,
    TRADE_PERMISSION_FORENSIC_FILENAME,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.evidence_v1 import (
    LiveCanaryEvidenceError,
    verify_manifest_v1,
)


class LiveCanaryVerifierError(RuntimeError):
    """Fail-closed verifier violation."""


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise LiveCanaryVerifierError(f"JSON_OBJECT_REQUIRED:{path.name}")
    return payload


def verify_live_canary_authoring_evidence_v1(evidence_root: Path | str) -> dict[str, Any]:
    root = Path(evidence_root)
    manifest = verify_manifest_v1(root)
    if manifest["MANIFEST_VERIFY_RC"] != 0:
        raise LiveCanaryVerifierError(f"MANIFEST_VERIFY_FAIL:{manifest['errors']}")

    claims = _load_json(root / CLAIMS_FILENAME)
    forensic = _load_json(root / FORENSIC_CLASSIFICATION_FILENAME)
    trade = _load_json(root / TRADE_PERMISSION_FORENSIC_FILENAME)

    if claims.get("LIVE_CANARY_MINIMUM_EXPOSURE_PROVEN") is not False:
        raise LiveCanaryVerifierError("PROVEN_MUST_REMAIN_FALSE")
    if claims.get("LIVE_CANARY_MINIMUM_EXPOSURE_EXECUTED") is not False:
        raise LiveCanaryVerifierError("EXECUTED_MUST_REMAIN_FALSE")
    if claims.get("LIVE_AUTHORIZED") is not False:
        raise LiveCanaryVerifierError("LIVE_AUTHORIZED_MUST_REMAIN_FALSE")
    if claims.get("LIVE_RECONCILIATION_PROVEN") is not False:
        raise LiveCanaryVerifierError("LIVE_RECONCILIATION_PROVEN_MUST_REMAIN_FALSE")
    if claims.get("BLOCKS_NEW_ENTRY") is not True:
        raise LiveCanaryVerifierError("BLOCKS_NEW_ENTRY_MUST_REMAIN_TRUE")
    if int(claims.get("ORDER_REQUEST_COUNT", -1)) != 0:
        raise LiveCanaryVerifierError("ORDER_REQUEST_COUNT_MUST_BE_ZERO")
    if int(claims.get("WRITE_REQUEST_COUNT", -1)) != 0:
        raise LiveCanaryVerifierError("WRITE_REQUEST_COUNT_MUST_BE_ZERO")
    if forensic.get("PRODUCTIVE_NETWORK_USED") is not False:
        raise LiveCanaryVerifierError("FORENSIC_MUST_BE_SEALED_ONLY")
    if forensic.get("BLOCKS_NEW_ENTRY_CLEARED") is not False:
        raise LiveCanaryVerifierError("FORENSIC_MUST_NOT_CLEAR_BLOCKS_NEW_ENTRY")
    if trade.get("TRADE_ATTESTATION") is not False:
        raise LiveCanaryVerifierError("TRADE_ATTESTATION_MUST_REMAIN_FALSE")
    if trade.get("AUTOMATIC_API_KEY_PERMISSION_CHANGE") is not False:
        raise LiveCanaryVerifierError("AUTOMATIC_KEY_CHANGE_FORBIDDEN")

    return {
        "ok": True,
        "MANIFEST_VERIFY_RC": 0,
        "LIVE_CANARY_MINIMUM_EXPOSURE_PROVEN": False,
        "LIVE_AUTHORIZED": False,
        "LIVE_RECONCILIATION_PROVEN": False,
        "BLOCKS_NEW_ENTRY": True,
        "TRADE_ATTESTATION": False,
        "PRODUCTIVE_CANARY_SURFACE_READY": bool(claims.get("PRODUCTIVE_CANARY_SURFACE_READY")),
    }


def verify_or_raise_v1(evidence_root: Path | str) -> int:
    try:
        verify_live_canary_authoring_evidence_v1(evidence_root)
        return 0
    except (LiveCanaryVerifierError, LiveCanaryEvidenceError):
        return 1
