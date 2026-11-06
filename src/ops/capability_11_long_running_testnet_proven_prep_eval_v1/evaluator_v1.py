"""LONG_RUNNING_TESTNET_PROVEN offline post-run verifier/evaluator.

Prep package default remains LONG_RUNNING_TESTNET_PROVEN=false.
Does not execute campaigns, load credentials, or open network sessions.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from src.ops.capability_11_long_running_testnet_proven_prep_eval_v1.constants_v1 import (
    BOUND_PRIORITY,
    CAMPAIGN_DURATION_BOUND_SECONDS,
    CAMPAIGN_MAX_CYCLES,
    CANONICAL_EXECUTE_OWNER_GO_SCOPE,
    CAPABILITY_ID,
    CYCLE_CADENCE_SECONDS,
    FORBIDDEN_HISTORICAL_EVIDENCE_ROOTS,
    LIVE_AUTHORIZED,
    LONG_RUNNING_TESTNET_PROVEN,
    LONG_RUNNING_TESTNET_PROVEN_DEFAULT,
    MANIFEST_FILENAME,
    OWNER,
    PRE_LIVE_CYBERSECURITY_GATE,
    SECTION_11_12_8_CLOSED,
    SECTION_11_12_8_REOPENED,
    SECTION_11_13_STARTED,
)


class LongRunningTestnetProvenEvalError(RuntimeError):
    """Fail-closed LONG_RUNNING_TESTNET_PROVEN evaluation violation."""


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LongRunningTestnetProvenEvalError(f"EVIDENCE_JSON_UNREADABLE:{path}") from exc
    if not isinstance(payload, dict):
        raise LongRunningTestnetProvenEvalError(f"EVIDENCE_JSON_NOT_OBJECT:{path}")
    return payload


def _as_int(value: Any, *, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _normalize_root(path: Path) -> str:
    text = str(path).replace("\\", "/")
    for prefix in (
        "evidence/ops/",
        "/evidence/ops/",
    ):
        idx = text.find(prefix)
        if idx >= 0:
            return text[idx:].rstrip("/")
    return text.rstrip("/")


def _is_forbidden_historical_root(evidence_root: Path) -> bool:
    normalized = _normalize_root(evidence_root)
    for forbidden in FORBIDDEN_HISTORICAL_EVIDENCE_ROOTS:
        if normalized == forbidden or normalized.startswith(forbidden + "/"):
            return True
        if forbidden in normalized:
            return True
    return False


def _manifest_verify_rc(evidence_root: Path) -> int:
    manifest = evidence_root / MANIFEST_FILENAME
    if not manifest.is_file():
        # Accept alternate sealed names used by productive campaign evidence.
        alt = evidence_root / "MANIFEST.sha256"
        if not alt.is_file():
            return 2
        manifest = alt
    lines = [ln.strip() for ln in manifest.read_text(encoding="utf-8").splitlines() if ln.strip()]
    if not lines:
        return 3
    for line in lines:
        parts = line.split()
        if len(parts) < 2:
            return 4
        digest, rel = parts[0], parts[-1]
        target = evidence_root / rel
        if not target.is_file():
            return 5
        import hashlib

        actual = hashlib.sha256(target.read_bytes()).hexdigest()
        if actual != digest:
            return 6
    return 0


def _extract_campaign_fields(payload: Mapping[str, Any]) -> dict[str, Any]:
    lifecycle = payload.get("lifecycle") if isinstance(payload.get("lifecycle"), dict) else {}
    reconcile = (
        payload.get("final_exchange_reconcile_cleanup")
        if isinstance(payload.get("final_exchange_reconcile_cleanup"), dict)
        else {}
    )
    return {
        "bound_reached_reason": str(
            payload.get("BOUND_REACHED_REASON")
            or lifecycle.get("bound_reached_reason")
            or payload.get("bound_reached_reason")
            or ""
        ),
        "completed": bool(payload.get("completed", lifecycle.get("completed", False))),
        "order_ack_count": _as_int(
            payload.get("ORDER_ACK_COUNT", lifecycle.get("exchange_ack_count", 0))
        ),
        "final_open_order_count": _as_int(
            payload.get(
                "FINAL_OPEN_ORDER_COUNT",
                reconcile.get("FINAL_OPEN_ORDER_COUNT", payload.get("final_open_order_count")),
            ),
            default=-1,
        ),
        "final_open_position_count": _as_int(
            payload.get(
                "FINAL_OPEN_POSITION_COUNT",
                reconcile.get(
                    "FINAL_OPEN_POSITION_COUNT", payload.get("final_open_position_count")
                ),
            ),
            default=-1,
        ),
        "live_order_effect": str(
            payload.get("LIVE_ORDER_EFFECT") or payload.get("live_order_effect") or "NONE"
        ),
        "live_authorized": bool(
            payload.get("LIVE_AUTHORIZED", payload.get("live_authorized", False))
        ),
        "unknown_submit_hard_stop": bool(
            payload.get(
                "unknown_submit_hard_stop", lifecycle.get("unknown_submit_hard_stop", False)
            )
        ),
        "http_status": payload.get("HTTP_STATUS", payload.get("http_status")),
        "http_403_classification": str(
            payload.get("HTTP_403_CLASSIFICATION") or payload.get("http_403_classification") or ""
        ),
        "cancel_count": _as_int(payload.get("CANCEL_COUNT", lifecycle.get("cancel_count", 0))),
        "reconcile_ok": bool(
            reconcile.get("ok")
            or str(payload.get("FINAL_EXCHANGE_RECONCILIATION") or "").upper() == "PASS"
        ),
        "duration_bound_seconds": _as_int(
            payload.get("duration_bound_seconds", lifecycle.get("duration_bound_seconds")),
            default=CAMPAIGN_DURATION_BOUND_SECONDS,
        ),
        "cycle_bound": _as_int(
            payload.get("cycle_bound", lifecycle.get("cycle_bound")),
            default=CAMPAIGN_MAX_CYCLES,
        ),
    }


def evaluate_long_running_testnet_proven_evidence_v1(
    *,
    evidence_root: Path,
    campaign_payload: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Evaluate a sealed campaign evidence root for LONG_RUNNING_TESTNET_PROVEN.

    Returns LONG_RUNNING_TESTNET_PROVEN=true only when all Owner PASS minima hold.
    Historical promotion and transport-only HTTP-403 evidence are refused.
    """
    root = Path(evidence_root)
    refuses: list[str] = []
    if not root.is_dir():
        raise LongRunningTestnetProvenEvalError(f"EVIDENCE_ROOT_MISSING:{root}")

    if _is_forbidden_historical_root(root):
        refuses.append("HISTORICAL_EVIDENCE_PROMOTION_REFUSED")

    payload: dict[str, Any]
    if campaign_payload is not None:
        payload = dict(campaign_payload)
    else:
        candidates = [
            root / "MACHINE_READABLE_PROOF.json",
            root / "MACHINE_READABLE_CLOSEOUT.json",
            root / "SANITIZED_FINAL_REPORT.json",
            root / "execution_evidence" / "productive_execution_evidence_v1.json",
            root / "productive_execution_evidence_v1.json",
        ]
        payload = {}
        for candidate in candidates:
            if candidate.is_file():
                payload = _load_json(candidate)
                break
        if not payload:
            refuses.append("CAMPAIGN_EVIDENCE_PAYLOAD_MISSING")

    fields = _extract_campaign_fields(payload)
    manifest_rc = _manifest_verify_rc(root)

    bound_reason = fields["bound_reached_reason"].upper()
    bound_reached = fields["completed"] and (
        "DURATION" in bound_reason
        or "CYCLE" in bound_reason
        or bound_reason in {"DURATION_BOUND", "CYCLE_BOUND"}
    )
    if not bound_reached:
        # Also accept explicit BOUND_REACHED_REASON tokens from closeout packages.
        if bound_reason in {"DURATION_BOUND", "CYCLE_BOUND"}:
            bound_reached = True
        else:
            refuses.append("BOUND_NOT_REACHED")

    if manifest_rc != 0:
        refuses.append(f"MANIFEST_VERIFY_RC_{manifest_rc}")

    if fields["order_ack_count"] < 1:
        refuses.append("ORDER_ACK_COUNT_LT_1")

    if fields["final_open_order_count"] != 0:
        refuses.append("FINAL_OPEN_ORDER_COUNT_NE_0")
    if fields["final_open_position_count"] != 0:
        refuses.append("FINAL_OPEN_POSITION_COUNT_NE_0")

    clean_same_run = False
    if fields["reconcile_ok"]:
        clean_same_run = True
    elif (
        fields["cancel_count"] >= 1
        and fields["final_open_order_count"] == 0
        and fields["final_open_position_count"] == 0
    ):
        clean_same_run = True
    else:
        refuses.append("CLEAN_CANCEL_OR_RECONCILE_MISSING")

    if fields["live_authorized"] or str(fields["live_order_effect"]).upper() not in {"NONE", ""}:
        refuses.append("LIVE_EFFECT_PRESENT")

    if fields["unknown_submit_hard_stop"]:
        refuses.append("UNKNOWN_SUBMIT_UNRESOLVED")

    http_status = fields["http_status"]
    classification = fields["http_403_classification"].upper()
    transport_403 = (
        str(http_status) == "403"
        or "TRANSPORT_OR_GATEWAY_HTTP_403" in classification
        or classification.endswith("HTTP_403_NON_JSON_BODY_NOT_EXCHANGE_SEMANTIC_REJECT")
    )
    if transport_403 and fields["order_ack_count"] < 1:
        refuses.append("TRANSPORT_ONLY_HTTP_403_REFUSED")

    proven = len(refuses) == 0
    return {
        "ok": True,  # evaluator ran; claim may still be false
        "CAPABILITY_ID": CAPABILITY_ID,
        "OWNER": OWNER,
        "EVIDENCE_ROOT": str(root),
        "MANIFEST_VERIFY_RC": manifest_rc,
        "BOUND_PRIORITY": BOUND_PRIORITY,
        "CAMPAIGN_DURATION_BOUND_SECONDS": CAMPAIGN_DURATION_BOUND_SECONDS,
        "CAMPAIGN_MAX_CYCLES": CAMPAIGN_MAX_CYCLES,
        "CYCLE_CADENCE_SECONDS": CYCLE_CADENCE_SECONDS,
        "CANONICAL_EXECUTE_OWNER_GO_SCOPE": CANONICAL_EXECUTE_OWNER_GO_SCOPE,
        "LONG_RUNNING_TESTNET_PROVEN": proven,
        "LONG_RUNNING_TESTNET_PROVEN_DEFAULT": LONG_RUNNING_TESTNET_PROVEN_DEFAULT,
        "REFUSE_REASONS": refuses,
        "FIELDS": fields,
        "CLEAN_CANCEL_OR_RECONCILE_SAME_RUN": clean_same_run and proven,
        "SECTION_11_12_8_CLOSED": SECTION_11_12_8_CLOSED,
        "SECTION_11_12_8_REOPENED": SECTION_11_12_8_REOPENED,
        "SECTION_11_13_STARTED": SECTION_11_13_STARTED,
        "LIVE_AUTHORIZED": LIVE_AUTHORIZED,
        "PRE_LIVE_CYBERSECURITY_GATE": PRE_LIVE_CYBERSECURITY_GATE,
        "HISTORICAL_PROMOTION_REFUSED": "HISTORICAL_EVIDENCE_PROMOTION_REFUSED" in refuses,
    }


def prep_package_claims_v1() -> dict[str, Any]:
    """Machine-readable prep package claims (always PROVEN=false)."""
    return {
        "CAPABILITY_ID": CAPABILITY_ID,
        "OWNER": OWNER,
        "LONG_RUNNING_TESTNET_PROVEN": LONG_RUNNING_TESTNET_PROVEN,
        "LONG_RUNNING_TESTNET_PROVEN_DEFAULT": LONG_RUNNING_TESTNET_PROVEN_DEFAULT,
        "LONG_RUNNING_PATH_READY": True,
        "PRODUCTIVE_CAMPAIGN_STARTED_BY_THIS_PACKAGE": False,
        "NETWORK_EFFECT": "NONE",
        "ORDER_EFFECT": "NONE",
        "LIVE_ORDER_EFFECT": "NONE",
        "LIVE_AUTHORIZED": LIVE_AUTHORIZED,
        "SECTION_11_13_STARTED": SECTION_11_13_STARTED,
        "PRE_LIVE_CYBERSECURITY_GATE": PRE_LIVE_CYBERSECURITY_GATE,
        "SECTION_11_12_8_CLOSED": SECTION_11_12_8_CLOSED,
        "SECTION_11_12_8_REOPENED": SECTION_11_12_8_REOPENED,
        "CAP_11_12_TESTNET_PROGRAM_CLOSED": True,
        "CANONICAL_EXECUTE_OWNER_GO_SCOPE": CANONICAL_EXECUTE_OWNER_GO_SCOPE,
        "MERGE_AUTHORIZATION_IS_NOT_EXECUTE_AUTHORIZATION": True,
        "CORE_LOGIC_CHANGE": False,
    }
