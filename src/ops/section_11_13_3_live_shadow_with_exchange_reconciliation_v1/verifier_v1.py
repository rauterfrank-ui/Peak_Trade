"""Verifier for §11.13.3 LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION evidence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from src.ops.section_11_13_3_live_shadow_with_exchange_reconciliation_v1.constants_v1 import (
    CLAIMS_FILENAME,
    FULLY_AUTONOMOUS_LIVE_TRADING_READY,
    LIVE_AUTHORIZED,
    TRANSPORT_CLASS_LIVE_PRODUCTIVE_HTTP,
)
from src.ops.section_11_13_3_live_shadow_with_exchange_reconciliation_v1.evidence_v1 import (
    LiveShadowReconEvidenceError,
    verify_manifest_v1,
)


class LiveShadowReconVerifierError(RuntimeError):
    """Fail-closed verifier violation."""


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise LiveShadowReconVerifierError(f"JSON_OBJECT_REQUIRED:{path.name}")
    return payload


def verify_live_shadow_with_exchange_reconciliation_evidence_v1(
    evidence_root: Path | str,
    *,
    allow_preparation_non_proven: bool = True,
) -> dict[str, Any]:
    root = Path(evidence_root)
    manifest = verify_manifest_v1(root)
    claims_path = root / CLAIMS_FILENAME
    if not claims_path.is_file():
        raise LiveShadowReconVerifierError("CLAIMS_MISSING")
    claims = _load_json(claims_path)

    required_zero = (
        "WRITE_REQUEST_COUNT",
        "ORDER_REQUEST_COUNT",
        "CANCEL_REQUEST_COUNT",
        "AMEND_REQUEST_COUNT",
        "WITHDRAW_REQUEST_COUNT",
        "TRANSFER_REQUEST_COUNT",
    )
    for key in required_zero:
        if int(claims.get(key, -1)) != 0:
            raise LiveShadowReconVerifierError(f"ZERO_MUTATION_INVARIANT_FAIL:{key}")

    if claims.get("LIVE_AUTHORIZED") is not False:
        raise LiveShadowReconVerifierError("LIVE_AUTHORIZED_MUST_REMAIN_FALSE")
    if claims.get("FULLY_AUTONOMOUS_LIVE_TRADING_READY") is not False:
        raise LiveShadowReconVerifierError("FULLY_AUTONOMOUS_LIVE_TRADING_READY_MUST_REMAIN_FALSE")
    if claims.get("LIVE_AUTHORIZED", True) != LIVE_AUTHORIZED:
        raise LiveShadowReconVerifierError("LIVE_AUTHORIZED_CONSTANT_DRIFT")
    if (
        claims.get("FULLY_AUTONOMOUS_LIVE_TRADING_READY", True)
        != FULLY_AUTONOMOUS_LIVE_TRADING_READY
    ):
        raise LiveShadowReconVerifierError("FULLY_AUTONOMOUS_READY_CONSTANT_DRIFT")

    proven = bool(claims.get("LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION_PROVEN"))
    mode = str(claims.get("mode", "")).strip().lower()
    transport = str(claims.get("transport_class", ""))
    venue_live = bool(claims.get("venue_live_contact"))
    fixture_like = bool(claims.get("fixture_or_demo_or_testnet"))

    if proven:
        if mode != "execute":
            raise LiveShadowReconVerifierError("PROVEN_REQUIRES_EXECUTE_MODE")
        if transport != TRANSPORT_CLASS_LIVE_PRODUCTIVE_HTTP:
            raise LiveShadowReconVerifierError("PROVEN_REQUIRES_LIVE_PRODUCTIVE_HTTP")
        if not venue_live:
            raise LiveShadowReconVerifierError("PROVEN_REQUIRES_VENUE_LIVE_CONTACT")
        if fixture_like:
            raise LiveShadowReconVerifierError("FIXTURE_CANNOT_SET_LIVE_PROVEN")
        if claims.get("ENVIRONMENT") != "LIVE":
            raise LiveShadowReconVerifierError("PROVEN_REQUIRES_ENVIRONMENT_LIVE")
        if claims.get("authenticated_read_success") is not True:
            raise LiveShadowReconVerifierError("PROVEN_REQUIRES_AUTHENTICATED_READ")
        if claims.get("demo_simulation_marker_absent") is not True:
            raise LiveShadowReconVerifierError("PROVEN_REQUIRES_NO_DEMO_MARKER")
        if claims.get("cross_binding_checks_PASS") is not True:
            raise LiveShadowReconVerifierError("PROVEN_REQUIRES_CROSS_BINDING_PASS")
        if claims.get("redaction_check_PASS") is not True:
            raise LiveShadowReconVerifierError("PROVEN_REQUIRES_REDACTION_PASS")
    else:
        if not allow_preparation_non_proven and mode == "execute":
            raise LiveShadowReconVerifierError("EXECUTE_WITHOUT_PROVEN_REJECTED")

    # Explicit: fixture/unit/preflight must never be accepted as proven.
    if mode in {"fixture", "unit", "preflight"} and proven:
        raise LiveShadowReconVerifierError("NON_PRODUCTIVE_MODE_CANNOT_BE_PROVEN")

    return {
        "ok": True,
        "MANIFEST_VERIFY_RC": manifest["MANIFEST_VERIFY_RC"],
        "LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION_PROVEN": proven,
        "LIVE_AUTHORIZED": False,
        "FULLY_AUTONOMOUS_LIVE_TRADING_READY": False,
        "mode": mode,
        "claims": claims,
    }


def refuse_fixture_proven_claim_v1(claims: Mapping[str, Any]) -> None:
    if bool(claims.get("LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION_PROVEN")) and (
        str(claims.get("mode", "")).lower() in {"fixture", "unit", "preflight"}
        or bool(claims.get("fixture_or_demo_or_testnet"))
        or str(claims.get("transport_class", "")) != TRANSPORT_CLASS_LIVE_PRODUCTIVE_HTTP
    ):
        raise LiveShadowReconVerifierError("FIXTURE_CANNOT_SET_LIVE_PROVEN")


def verify_or_raise_v1(evidence_root: Path | str) -> int:
    try:
        verify_live_shadow_with_exchange_reconciliation_evidence_v1(evidence_root)
        return 0
    except (LiveShadowReconVerifierError, LiveShadowReconEvidenceError):
        return 1
