"""Verifier for §11.13.4 LIVE_DRY_RUN_ORDER_PLAN evidence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from src.ops.section_11_13_4_live_dry_run_order_plan_v1.constants_v1 import (
    CLAIMS_FILENAME,
    FULLY_AUTONOMOUS_LIVE_TRADING_READY,
    LIVE_AUTHORIZED,
    ORDER_PLAN_FILENAME,
    TRANSPORT_CLASS_LIVE_PRODUCTIVE_HTTP,
)
from src.ops.section_11_13_4_live_dry_run_order_plan_v1.evidence_v1 import (
    LiveDryRunOrderPlanEvidenceError,
    verify_manifest_v1,
)


class LiveDryRunOrderPlanVerifierError(RuntimeError):
    """Fail-closed verifier violation."""


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise LiveDryRunOrderPlanVerifierError(f"JSON_OBJECT_REQUIRED:{path.name}")
    return payload


def verify_live_dry_run_order_plan_evidence_v1(
    evidence_root: Path | str,
    *,
    allow_preparation_non_proven: bool = True,
) -> dict[str, Any]:
    root = Path(evidence_root)
    manifest = verify_manifest_v1(root)
    claims_path = root / CLAIMS_FILENAME
    if not claims_path.is_file():
        raise LiveDryRunOrderPlanVerifierError("CLAIMS_MISSING")
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
            raise LiveDryRunOrderPlanVerifierError(f"ZERO_MUTATION_INVARIANT_FAIL:{key}")

    if claims.get("LIVE_AUTHORIZED") is not False:
        raise LiveDryRunOrderPlanVerifierError("LIVE_AUTHORIZED_MUST_REMAIN_FALSE")
    if claims.get("FULLY_AUTONOMOUS_LIVE_TRADING_READY") is not False:
        raise LiveDryRunOrderPlanVerifierError(
            "FULLY_AUTONOMOUS_LIVE_TRADING_READY_MUST_REMAIN_FALSE"
        )
    if claims.get("LIVE_AUTHORIZED", True) != LIVE_AUTHORIZED:
        raise LiveDryRunOrderPlanVerifierError("LIVE_AUTHORIZED_CONSTANT_DRIFT")
    if (
        claims.get("FULLY_AUTONOMOUS_LIVE_TRADING_READY", True)
        != FULLY_AUTONOMOUS_LIVE_TRADING_READY
    ):
        raise LiveDryRunOrderPlanVerifierError("FULLY_AUTONOMOUS_READY_CONSTANT_DRIFT")
    if claims.get("LIVE_RECONCILIATION_PROVEN") is not False:
        raise LiveDryRunOrderPlanVerifierError("LIVE_RECONCILIATION_PROVEN_MUST_REMAIN_FALSE")
    if claims.get("BLOCKS_NEW_ENTRY") is not True:
        raise LiveDryRunOrderPlanVerifierError("BLOCKS_NEW_ENTRY_MUST_REMAIN_TRUE")

    proven = bool(claims.get("LIVE_DRY_RUN_ORDER_PLAN_PROVEN"))
    mode = str(claims.get("mode", "")).strip().lower()
    transport = str(claims.get("transport_class", ""))
    venue_live = bool(claims.get("venue_live_contact"))
    fixture_like = bool(claims.get("fixture_or_demo_or_testnet"))

    if proven:
        if mode != "execute":
            raise LiveDryRunOrderPlanVerifierError("PROVEN_REQUIRES_EXECUTE_MODE")
        if transport != TRANSPORT_CLASS_LIVE_PRODUCTIVE_HTTP:
            raise LiveDryRunOrderPlanVerifierError("PROVEN_REQUIRES_LIVE_PRODUCTIVE_HTTP")
        if not venue_live:
            raise LiveDryRunOrderPlanVerifierError("PROVEN_REQUIRES_VENUE_LIVE_CONTACT")
        if fixture_like:
            raise LiveDryRunOrderPlanVerifierError("FIXTURE_CANNOT_SET_LIVE_PROVEN")
        if claims.get("ENVIRONMENT") != "LIVE":
            raise LiveDryRunOrderPlanVerifierError("PROVEN_REQUIRES_ENVIRONMENT_LIVE")
        if claims.get("authenticated_read_success") is not True:
            raise LiveDryRunOrderPlanVerifierError("PROVEN_REQUIRES_AUTHENTICATED_READ")
        if claims.get("demo_simulation_marker_absent") is not True:
            raise LiveDryRunOrderPlanVerifierError("PROVEN_REQUIRES_NO_DEMO_MARKER")
        if claims.get("cross_binding_checks_PASS") is not True:
            raise LiveDryRunOrderPlanVerifierError("PROVEN_REQUIRES_CROSS_BINDING_PASS")
        if claims.get("redaction_check_PASS") is not True:
            raise LiveDryRunOrderPlanVerifierError("PROVEN_REQUIRES_REDACTION_PASS")
        plan_path = root / ORDER_PLAN_FILENAME
        if not plan_path.is_file():
            raise LiveDryRunOrderPlanVerifierError("ORDER_PLAN_MISSING")
        plan = _load_json(plan_path)
        if plan.get("submitted") is True or plan.get("submit") is True:
            raise LiveDryRunOrderPlanVerifierError("ORDER_PLAN_MUST_NOT_BE_SUBMITTED")
        if plan.get("execution_eligibility") not in {
            "BLOCKED_NO_EXECUTE",
            "ELIGIBLE_BUT_SUBMIT_STILL_FORBIDDEN_WITHOUT_SEPARATE_GO",
        }:
            raise LiveDryRunOrderPlanVerifierError("ORDER_PLAN_ELIGIBILITY_UNEXPECTED")
        if claims.get("ORDER_PLAN_RESULT") not in {
            "BLOCKED_NO_EXECUTE",
            "NO_EXECUTE",
            "CONSTRUCTED_BLOCKED",
        }:
            raise LiveDryRunOrderPlanVerifierError("ORDER_PLAN_RESULT_UNEXPECTED")
    else:
        if not allow_preparation_non_proven and mode == "execute":
            raise LiveDryRunOrderPlanVerifierError("EXECUTE_WITHOUT_PROVEN_REJECTED")

    if mode in {"fixture", "unit", "preflight"} and proven:
        raise LiveDryRunOrderPlanVerifierError("NON_PRODUCTIVE_MODE_CANNOT_BE_PROVEN")

    return {
        "ok": True,
        "MANIFEST_VERIFY_RC": manifest["MANIFEST_VERIFY_RC"],
        "LIVE_DRY_RUN_ORDER_PLAN_PROVEN": proven,
        "LIVE_AUTHORIZED": False,
        "LIVE_RECONCILIATION_PROVEN": False,
        "BLOCKS_NEW_ENTRY": True,
        "FULLY_AUTONOMOUS_LIVE_TRADING_READY": False,
        "mode": mode,
        "claims": claims,
    }


def refuse_fixture_proven_claim_v1(claims: Mapping[str, Any]) -> None:
    if bool(claims.get("LIVE_DRY_RUN_ORDER_PLAN_PROVEN")) and (
        str(claims.get("mode", "")).lower() in {"fixture", "unit", "preflight"}
        or bool(claims.get("fixture_or_demo_or_testnet"))
        or str(claims.get("transport_class", "")) != TRANSPORT_CLASS_LIVE_PRODUCTIVE_HTTP
    ):
        raise LiveDryRunOrderPlanVerifierError("FIXTURE_CANNOT_SET_LIVE_PROVEN")


def verify_or_raise_v1(evidence_root: Path | str) -> int:
    try:
        verify_live_dry_run_order_plan_evidence_v1(evidence_root)
        return 0
    except (LiveDryRunOrderPlanVerifierError, LiveDryRunOrderPlanEvidenceError):
        return 1
