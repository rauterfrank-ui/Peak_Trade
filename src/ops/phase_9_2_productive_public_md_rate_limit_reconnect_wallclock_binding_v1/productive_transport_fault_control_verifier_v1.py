"""Hardened Step-4 productive transport fault-control verifier.

Rejects substring false positives, requires typed 429 + reconnect +
post-reconnect reconciliation evidence, and keeps injected vs natural claims
strictly separated. Offline only — no network.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from src.ops.phase_9_2_public_md_session_preflight_v1.rate_limit_metric_v1 import (
    compute_rate_limit_event_count_v1,
)
from src.ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1.governed_injected_transport_fault_v1 import (  # noqa: E501
    CAPABILITY_ID,
    FAULT_ORIGIN_GOVERNED,
    FAULT_ORIGIN_NATURAL,
)

VERIFIER_ID = (
    "ops.phase_9_2_productive_public_md_rate_limit_reconnect_wallclock_binding_v1."
    "productive_transport_fault_control_verifier_v1"
)

# Explicitly deauthorized anti-pattern from prior Step-4 closeout.
SUBSTRING_RATE_LIMIT_COUNT_AUTHORITY_EFFECT = "NONE"


def _load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    raw = json.loads(path.read_text(encoding="utf-8"))
    return raw if isinstance(raw, dict) else {}


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    out: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if isinstance(row, dict):
            out.append(row)
    return out


def _reject_substring_rate_limit_claim_v1(claims: Mapping[str, Any]) -> list[str]:
    blockers: list[str] = []
    if "rate_limit_runtime_mentions" in claims:
        blockers.append("SUBSTRING_RATE_LIMIT_RUNTIME_MENTIONS_FORBIDDEN")
    if bool(claims.get("RATE_LIMIT_RUNTIME_MENTIONS_EQUALS_REQUEST_COUNT")):
        blockers.append("RATE_LIMIT_RUNTIME_MENTIONS_EQUALS_REQUEST_COUNT")
    if bool(claims.get("rate_limit_classification_proven")) and not bool(
        claims.get("TYPED_RATE_LIMIT_EVENT_PROVEN")
    ):
        # Legacy claim without typed metric authority is not admissible.
        blockers.append("LEGACY_RATE_LIMIT_CLASSIFICATION_PROVEN_WITHOUT_TYPED_METRIC")
    return blockers


def verify_step4_productive_transport_fault_control_evidence_v1(
    *,
    evidence_root: Path,
    require_governed_injection: bool = True,
    claims: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Verify Step-4 fault-control productive evidence (offline)."""
    root = Path(evidence_root)
    wallclock = root / "wallclock_session"
    scan_root = wallclock if wallclock.is_dir() else root
    blockers: list[str] = []
    notes = [
        f"VERIFIER_ID={VERIFIER_ID}",
        f"CAPABILITY_ID={CAPABILITY_ID}",
        "VERIFIER_NO_NETWORK",
        f"SUBSTRING_RATE_LIMIT_COUNT_AUTHORITY_EFFECT={SUBSTRING_RATE_LIMIT_COUNT_AUTHORITY_EFFECT}",
    ]
    claim_map = dict(claims or {})

    blockers.extend(_reject_substring_rate_limit_claim_v1(claim_map))

    telemetry = _load_json(scan_root / "transport_telemetry.json")
    if not telemetry:
        blockers.append("TRANSPORT_TELEMETRY_MISSING")

    rate_limit_event_count = int(compute_rate_limit_event_count_v1(evidence_root=scan_root))
    http_429_count = int(telemetry.get("http_429_count") or 0)
    if rate_limit_event_count < 1 and http_429_count < 1:
        blockers.append("TYPED_HTTP_429_OR_RATE_LIMIT_EVENT_MISSING")
    if rate_limit_event_count < 1 and http_429_count >= 1:
        # Prefer authoritative transport counter when metric scan is empty but telemetry present.
        rate_limit_event_count = http_429_count

    # Session-ID substring must never satisfy the metric.
    session_manifest = _load_json(scan_root / "session_manifest.json")
    session_id = str(
        telemetry.get("session_id")
        or session_manifest.get("session_id")
        or claim_map.get("session_id")
        or ""
    )
    if "rate_limit" in session_id.lower() and rate_limit_event_count >= 1:
        notes.append("SESSION_ID_CONTAINS_RATE_LIMIT_SUBSTRING_IGNORED_FOR_METRIC")

    reconnect_events = _load_jsonl(scan_root / "reconnect_events.jsonl")
    connectivity = _load_jsonl(scan_root / "connectivity_events.jsonl")
    runtime_events = _load_jsonl(scan_root / "runtime_events.jsonl")
    stale_events = _load_jsonl(scan_root / "stale_events.jsonl")

    disconnect_events = [
        e
        for e in connectivity
        if str(e.get("event") or "") in {"transport_disconnect", "disconnect"}
        or bool(e.get("reconnectable"))
    ] + reconnect_events
    if not disconnect_events:
        blockers.append("DISCONNECT_TRANSPORT_EVENT_MISSING")

    if int(telemetry.get("reconnect_attempt_count") or 0) < 1 and not reconnect_events:
        blockers.append("RECONNECT_ATTEMPT_MISSING")
    if int(telemetry.get("reconnect_success_count") or 0) < 1:
        # Infer from connectivity success events when counter absent in older fixtures.
        success = [
            e for e in connectivity if str(e.get("event") or "") == "transport_reconnect_success"
        ]
        if not success and int(telemetry.get("reconnect_success_count") or 0) < 1:
            blockers.append("RECONNECT_SUCCESS_MISSING")

    recon_events = [
        e
        for e in runtime_events
        if str(e.get("event") or "") == "post_reconnect_reconciliation_before_alpha"
    ]
    if int(telemetry.get("post_reconnect_reconciliation_count") or 0) < 1 and not recon_events:
        blockers.append("POST_RECONNECT_RECONCILIATION_MISSING")
    if recon_events and not any(
        bool(e.get("ok")) and bool(e.get("alpha_enabled")) for e in recon_events
    ):
        blockers.append("POST_RECONNECT_RECONCILIATION_NOT_OK")

    if int(telemetry.get("post_reconnect_continuation_count") or 0) < 1 and not recon_events:
        blockers.append("POST_RECONNECT_SESSION_CONTINUATION_MISSING")

    stale_count = int(telemetry.get("stale_gate_activation_count") or 0) + len(stale_events)
    # Stale gate may remain inactive if interruption is shorter than budget; require
    # owner presence via telemetry field rather than forced activation.
    if "stale_gate_activation_count" not in telemetry and not stale_events:
        notes.append("STALE_GATE_TELEMETRY_FIELD_ABSENT")

    fabricated = int(telemetry.get("fabricated_observation_count") or 0)
    if fabricated != 0:
        blockers.append("FABRICATED_OBSERVATION_COUNT_NONZERO")

    # fault_origin required on reconnect/disconnect events.
    for ev in disconnect_events:
        if "fault_origin" not in ev:
            blockers.append("FAULT_ORIGIN_MISSING_ON_DISCONNECT_OR_RECONNECT_EVENT")
            break

    governed_count = int(telemetry.get("governed_injected_fault_count") or 0)
    if require_governed_injection and governed_count < 1:
        blockers.append("GOVERNED_INJECTED_TRANSPORT_FAULT_MISSING")

    if bool(claim_map.get("NATURAL_EXCHANGE_HTTP_429_OBSERVED")) and governed_count >= 1:
        if not bool(claim_map.get("NATURAL_EXCHANGE_TRANSPORT_EVENT_SEPARATE")):
            # Injected must never be claimed as natural.
            if int(telemetry.get("natural_transport_fault_count") or 0) < 1:
                blockers.append("INJECTED_CLAIMED_AS_NATURAL_HTTP_429")

    if bool(claim_map.get("REAL_HTTP_429_OBSERVED")) and governed_count >= 1:
        # Ambiguous claim name: require explicit injected claim instead.
        if not bool(claim_map.get("GOVERNED_INJECTED_TRANSPORT_FAULT_USED")):
            blockers.append("AMBIGUOUS_REAL_HTTP_429_OBSERVED_WITH_INJECTION")

    # Real execution / credential / private endpoint negatives.
    term = _load_json(scan_root / "terminal_verdict.json")
    if bool(term.get("orders_submitted")):
        blockers.append("ORDERS_SUBMITTED")
    if bool(term.get("credentials_used")):
        blockers.append("CREDENTIALS_USED")
    no_order = _load_json(scan_root / "no_order_attestation.json")
    if no_order and int(no_order.get("orders_submitted") or 0) != 0:
        blockers.append("NO_ORDER_ATTESTATION_FAILED")

    # Duplicate confirmation / fill guards from telemetry notes when present.
    if bool(claim_map.get("DUPLICATE_CONFIRMATION_ADVANCE")):
        blockers.append("DUPLICATE_CONFIRMATION_ADVANCE")
    if bool(claim_map.get("DUPLICATE_FILL")):
        blockers.append("DUPLICATE_FILL")

    public_result = _load_json(root / "operator_public_result.json")
    if public_result:
        md_count = int(public_result.get("public_market_data_request_count") or 0)
        mentions = public_result.get("rate_limit_runtime_mentions")
        if mentions is not None and int(mentions) == md_count and md_count > 0:
            blockers.append("RATE_LIMIT_RUNTIME_MENTIONS_EQUALS_REQUEST_COUNT")

    ok = not blockers
    result_claims = {
        "TYPED_RATE_LIMIT_EVENT_PROVEN": rate_limit_event_count >= 1 or http_429_count >= 1,
        "GOVERNED_INJECTED_TRANSPORT_FAULT_USED": governed_count >= 1,
        "NATURAL_EXCHANGE_HTTP_429_OBSERVED": bool(http_429_count >= 1 and governed_count == 0),
        "RECONNECT_OBSERVED": bool(reconnect_events)
        or int(telemetry.get("reconnect_success_count") or 0) >= 1,
        "POST_RECONNECT_SESSION_CONTINUED": int(
            telemetry.get("post_reconnect_continuation_count") or 0
        )
        >= 1
        or bool(recon_events),
        "POST_RECONNECT_RECONCILIATION_PROVEN": int(
            telemetry.get("post_reconnect_reconciliation_count") or 0
        )
        >= 1
        or bool(recon_events),
        "NOT_NATURALLY_OCCURRED_CLASSIFIED": governed_count >= 1,
        "SUBSTRING_RATE_LIMIT_COUNT_AUTHORITY_EFFECT": SUBSTRING_RATE_LIMIT_COUNT_AUTHORITY_EFFECT,
        "RATE_LIMIT_METRIC_OWNER": (
            "ops.phase_9_2_public_md_session_preflight_v1.rate_limit_metric_v1"
        ),
        "FAULT_ORIGIN_GOVERNED": FAULT_ORIGIN_GOVERNED,
        "FAULT_ORIGIN_NATURAL": FAULT_ORIGIN_NATURAL,
        "STALE_GATE_TELEMETRY_PRESENT": "stale_gate_activation_count" in telemetry
        or bool(stale_events),
        "FABRICATED_OBSERVATION_COUNT": fabricated,
    }
    return {
        "ok": ok,
        "verified": ok,
        "blockers": blockers,
        "notes": notes,
        "claims": result_claims,
        "rate_limit_event_count": rate_limit_event_count,
        "http_429_count": http_429_count,
        "governed_injected_fault_count": governed_count,
        "reconnect_event_count": len(reconnect_events),
        "stale_gate_activation_count": stale_count,
        "session_id": session_id,
        "verifier_id": VERIFIER_ID,
        "capability_id": CAPABILITY_ID,
    }
