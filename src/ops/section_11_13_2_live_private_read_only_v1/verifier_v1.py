"""Verifier for §11.13.2 LIVE_PRIVATE_READ_ONLY evidence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from src.ops.section_11_13_2_live_private_read_only_v1.constants_v1 import (
    CLAIMS_FILENAME,
    FULLY_AUTONOMOUS_LIVE_TRADING_READY,
    LIVE_AUTHORIZED,
    TRANSPORT_CLASS_LIVE_PRODUCTIVE_HTTP,
)
from src.ops.section_11_13_2_live_private_read_only_v1.evidence_v1 import (
    LivePrivateRoEvidenceError,
    verify_manifest_v1,
)


class LivePrivateRoVerifierError(RuntimeError):
    """Fail-closed verifier violation."""


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise LivePrivateRoVerifierError(f"JSON_OBJECT_REQUIRED:{path.name}")
    return payload


def verify_live_private_read_only_evidence_v1(
    evidence_root: Path | str,
    *,
    allow_preparation_non_proven: bool = True,
) -> dict[str, Any]:
    root = Path(evidence_root)
    manifest = verify_manifest_v1(root)
    claims_path = root / CLAIMS_FILENAME
    if not claims_path.is_file():
        raise LivePrivateRoVerifierError("CLAIMS_MISSING")
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
            raise LivePrivateRoVerifierError(f"ZERO_MUTATION_INVARIANT_FAIL:{key}")

    if claims.get("LIVE_AUTHORIZED") is not False:
        raise LivePrivateRoVerifierError("LIVE_AUTHORIZED_MUST_REMAIN_FALSE")
    if claims.get("FULLY_AUTONOMOUS_LIVE_TRADING_READY") is not False:
        raise LivePrivateRoVerifierError("FULLY_AUTONOMOUS_LIVE_TRADING_READY_MUST_REMAIN_FALSE")
    if claims.get("LIVE_AUTHORIZED", True) != LIVE_AUTHORIZED:
        raise LivePrivateRoVerifierError("LIVE_AUTHORIZED_CONSTANT_DRIFT")
    if (
        claims.get("FULLY_AUTONOMOUS_LIVE_TRADING_READY", True)
        != FULLY_AUTONOMOUS_LIVE_TRADING_READY
    ):
        raise LivePrivateRoVerifierError("FULLY_AUTONOMOUS_READY_CONSTANT_DRIFT")

    proven = bool(claims.get("LIVE_PRIVATE_READ_ONLY_PROVEN"))
    mode = str(claims.get("mode", "")).strip().lower()
    transport = str(claims.get("transport_class", ""))
    venue_live = bool(claims.get("venue_live_contact"))
    fixture_like = bool(claims.get("fixture_or_demo_or_testnet"))

    if proven:
        if mode != "execute":
            raise LivePrivateRoVerifierError("PROVEN_REQUIRES_EXECUTE_MODE")
        if transport != TRANSPORT_CLASS_LIVE_PRODUCTIVE_HTTP:
            raise LivePrivateRoVerifierError("PROVEN_REQUIRES_LIVE_PRODUCTIVE_HTTP")
        if not venue_live:
            raise LivePrivateRoVerifierError("PROVEN_REQUIRES_VENUE_LIVE_CONTACT")
        if fixture_like:
            raise LivePrivateRoVerifierError("FIXTURE_CANNOT_SET_LIVE_PROVEN")
        if claims.get("ENVIRONMENT") != "LIVE":
            raise LivePrivateRoVerifierError("PROVEN_REQUIRES_ENVIRONMENT_LIVE")
        if claims.get("authenticated_read_success") is not True:
            raise LivePrivateRoVerifierError("PROVEN_REQUIRES_AUTHENTICATED_READ")
        if claims.get("demo_simulation_marker_absent") is not True:
            raise LivePrivateRoVerifierError("PROVEN_REQUIRES_NO_DEMO_MARKER")
        if claims.get("cross_binding_checks_PASS") is not True:
            raise LivePrivateRoVerifierError("PROVEN_REQUIRES_CROSS_BINDING_PASS")
        if claims.get("redaction_check_PASS") is not True:
            raise LivePrivateRoVerifierError("PROVEN_REQUIRES_REDACTION_PASS")
        if claims.get("permission_attestation_PASS") is not True:
            raise LivePrivateRoVerifierError("PROVEN_REQUIRES_PERMISSION_ATTESTATION_PASS")
        attestation = claims.get("permission_attestation") or {}
        if not isinstance(attestation, dict):
            raise LivePrivateRoVerifierError("PROVEN_REQUIRES_PERMISSION_ATTESTATION_OBJECT")
        if attestation.get("READ") is not True:
            raise LivePrivateRoVerifierError("PROVEN_REQUIRES_READ_TRUE")
        if attestation.get("TRADE") is not False:
            raise LivePrivateRoVerifierError("PROVEN_REQUIRES_TRADE_FALSE")
        if attestation.get("WITHDRAW") is not False:
            raise LivePrivateRoVerifierError("PROVEN_REQUIRES_WITHDRAW_FALSE")
        if claims.get("account_scope_match") is not True:
            raise LivePrivateRoVerifierError("PROVEN_REQUIRES_ACCOUNT_SCOPE_MATCH")
        if claims.get("okx_code_success") is not True:
            raise LivePrivateRoVerifierError("PROVEN_REQUIRES_OKX_CODE_SUCCESS")
        endpoints = claims.get("endpoints_used") or []
        if not isinstance(endpoints, list):
            raise LivePrivateRoVerifierError("PROVEN_REQUIRES_ENDPOINTS_LIST")
        required = {"/api/v5/account/config", "/api/v5/account/balance"}
        if not required.issubset(set(endpoints)):
            raise LivePrivateRoVerifierError("PROVEN_REQUIRES_IDENTITY_ENDPOINTS")
        methods = claims.get("methods_used") or []
        if not methods or any(str(m).upper() != "GET" for m in methods):
            raise LivePrivateRoVerifierError("PROVEN_REQUIRES_GET_ONLY")
    else:
        if not allow_preparation_non_proven and mode == "execute":
            raise LivePrivateRoVerifierError("EXECUTE_WITHOUT_PROVEN_REJECTED")

    # Explicit: fixture/unit/preflight must never be accepted as proven.
    if mode in {"fixture", "unit", "preflight"} and proven:
        raise LivePrivateRoVerifierError("NON_PRODUCTIVE_MODE_CANNOT_BE_PROVEN")

    return {
        "ok": True,
        "MANIFEST_VERIFY_RC": manifest["MANIFEST_VERIFY_RC"],
        "LIVE_PRIVATE_READ_ONLY_PROVEN": proven,
        "LIVE_AUTHORIZED": False,
        "FULLY_AUTONOMOUS_LIVE_TRADING_READY": False,
        "mode": mode,
        "claims": claims,
    }


def refuse_fixture_proven_claim_v1(claims: Mapping[str, Any]) -> None:
    if bool(claims.get("LIVE_PRIVATE_READ_ONLY_PROVEN")) and (
        str(claims.get("mode", "")).lower() in {"fixture", "unit", "preflight"}
        or bool(claims.get("fixture_or_demo_or_testnet"))
        or str(claims.get("transport_class", "")) != TRANSPORT_CLASS_LIVE_PRODUCTIVE_HTTP
    ):
        raise LivePrivateRoVerifierError("FIXTURE_CANNOT_SET_LIVE_PROVEN")


def verify_or_raise_v1(evidence_root: Path | str) -> int:
    try:
        verify_live_private_read_only_evidence_v1(evidence_root)
        return 0
    except (LivePrivateRoVerifierError, LivePrivateRoEvidenceError):
        return 1
