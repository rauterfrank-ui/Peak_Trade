"""Pure PL-TF-002 network evidence verifier. No network. No authority mint."""

from __future__ import annotations

import time
from typing import Any, Mapping

from src.ops.pl_tf_002_network_evidence_contract_v1.constants_v1 import (
    DEFAULT_FRESHNESS_MAX_AGE_MS,
    F1_REQUIRED_GET_ITEM_IDS,
    FORBIDDEN_EVIDENCE_CLASS_MARKERS,
    NE_TF_001_ENDPOINT_PATH,
    NE_TF_001_HTTP_METHOD,
    NE_TF_001_TASK_ID,
    PL_TF_002_REQUIRED_READ,
    PL_TF_002_REQUIRED_TRADE,
    PL_TF_002_REQUIRED_WITHDRAW,
    PL_TF_002_STATUS_CLOSED,
    PL_TF_002_STATUS_STANDING,
    PRODUCTIVE_TRANSPORT_CLASSES,
    VENUE_PERMISSION_GET_PERFORMED_STANDING,
    VENUE_PERMISSION_UNKNOWN_STANDING,
)
from src.ops.pl_tf_002_network_evidence_contract_v1.errors_v1 import PlTf002NetworkEvidenceError
from src.ops.pl_tf_002_network_evidence_contract_v1.normalize_v1 import (
    normalize_okx_account_config_perm_v1,
)
from src.ops.pl_tf_002_network_evidence_contract_v1.redaction_v1 import (
    assert_evidence_redaction_invariant_v1,
)

JOIN_SEAM_ID = "PL_TF_002_NETWORK_EVIDENCE_VERIFIER_V1"


def _fail(reasons: tuple[str, ...]) -> dict[str, Any]:
    return {
        "VERIFICATION_RESULT": "FAIL_CLOSED",
        "REASONS": list(reasons),
        "F1_PRODUCTIVE_VENUE_GET_PASS": False,
        "F2_NE_TF_001_PERMISSION_GET_PASS": False,
        "F3_TREASURY_CAPABILITY_NEGATIVE_PASS": False,
        "F4_VENUE_PERMISSION_UNKNOWN_CLEARED": False,
        "PL_TF_002_CLOSURE_RESULT": {
            "closed": False,
            "status_if_closed": PL_TF_002_STATUS_CLOSED,
            "standing_status_unchanged": PL_TF_002_STATUS_STANDING,
        },
        "AUTHORITY_ESCALATION": False,
        "LIVE_MINTED": False,
        "RISK_ADMISSIBLE_MINTED": False,
        "TREASURY_AUTHORITY_MINTED": False,
        "EXTERNAL_EFFECT_MINTED": False,
    }


def _validate_provenance(provenance: Mapping[str, Any], *, now_ms: int) -> tuple[str, ...]:
    reasons: list[str] = []
    evidence_class = str(provenance.get("evidence_class") or "").upper()
    if evidence_class != "PRODUCTIVE_VENUE_EVIDENCE":
        reasons.append("EVIDENCE_CLASS_NOT_PRODUCTIVE")
    for marker in FORBIDDEN_EVIDENCE_CLASS_MARKERS:
        if marker in evidence_class:
            reasons.append(f"FORBIDDEN_EVIDENCE_MARKER:{marker}")
    transport = str(provenance.get("transport_class") or "")
    if transport not in PRODUCTIVE_TRANSPORT_CLASSES:
        reasons.append("TRANSPORT_CLASS_NOT_PRODUCTIVE")
    if provenance.get("venue_live_contact") is not True:
        reasons.append("VENUE_LIVE_CONTACT_NOT_TRUE")
    if provenance.get("fixture_or_injected") is True:
        reasons.append("FIXTURE_OR_INJECTED")
    if provenance.get("historical_reuse") is True:
        reasons.append("HISTORICAL_REUSE")
    observed_ms = provenance.get("observed_at_unix_ms")
    if not isinstance(observed_ms, int):
        reasons.append("OBSERVED_AT_MISSING")
    else:
        max_age = int(provenance.get("freshness_max_age_ms") or DEFAULT_FRESHNESS_MAX_AGE_MS)
        if now_ms - observed_ms > max_age:
            reasons.append("EVIDENCE_STALE")
    expected_uid = str(provenance.get("expected_credential_uid") or "").strip()
    if expected_uid == "":
        reasons.append("EXPECTED_CREDENTIAL_UID_MISSING")
    return tuple(reasons)


def _validate_f1(productive_gets: Mapping[str, Any]) -> tuple[bool, tuple[str, ...]]:
    reasons: list[str] = []
    items = productive_gets.get("items")
    if not isinstance(items, Mapping):
        return False, ("F1_ITEMS_MISSING",)
    for item_id in F1_REQUIRED_GET_ITEM_IDS:
        row = items.get(item_id)
        if not isinstance(row, Mapping):
            reasons.append(f"F1_MISSING_ITEM:{item_id}")
            continue
        if row.get("get_performed") is not True:
            reasons.append(f"F1_GET_NOT_PERFORMED:{item_id}")
        if str(row.get("method") or "").upper() != "GET":
            reasons.append(f"F1_NON_GET_METHOD:{item_id}")
        if row.get("venue_live_contact") is not True:
            reasons.append(f"F1_VENUE_LIVE_CONTACT_FALSE:{item_id}")
        transport = str(row.get("transport_class") or "")
        if transport not in PRODUCTIVE_TRANSPORT_CLASSES:
            reasons.append(f"F1_TRANSPORT_NOT_PRODUCTIVE:{item_id}")
    return len(reasons) == 0, tuple(reasons)


def _validate_f2(
    ne_tf_001: Mapping[str, Any], *, expected_uid: str
) -> tuple[bool, dict[str, Any] | None, tuple[str, ...]]:
    reasons: list[str] = []
    if str(ne_tf_001.get("task_id") or "") != NE_TF_001_TASK_ID:
        reasons.append("F2_TASK_ID_MISMATCH")
    if str(ne_tf_001.get("http_method") or "").upper() != NE_TF_001_HTTP_METHOD:
        reasons.append("F2_HTTP_METHOD_MISMATCH")
    endpoint = str(ne_tf_001.get("endpoint_path") or "")
    if endpoint != NE_TF_001_ENDPOINT_PATH:
        reasons.append("F2_ENDPOINT_MISMATCH")
    if ne_tf_001.get("get_performed") is not True:
        reasons.append("F2_GET_NOT_PERFORMED")
    raw = ne_tf_001.get("raw_venue_response")
    if not isinstance(raw, Mapping):
        reasons.append("F2_RAW_VENUE_RESPONSE_MISSING")
        return False, None, tuple(reasons)
    try:
        normalized = normalize_okx_account_config_perm_v1(raw)
    except PlTf002NetworkEvidenceError as exc:
        reasons.append(str(exc))
        return False, None, tuple(reasons)
    if str(normalized.get("uid") or "") != expected_uid:
        reasons.append("F2_CREDENTIAL_UID_MISMATCH")
    # §11.13.2 owner attestation is not NE-TF-001 equivalence.
    attestation = ne_tf_001.get("owner_permission_attestation")
    if isinstance(attestation, Mapping):
        reasons.append("F2_OWNER_ATTESTATION_NOT_NE_TF_001_AUTHORITY")
    return len(reasons) == 0, normalized, tuple(reasons)


def _validate_f3(normalized: Mapping[str, Any] | None) -> tuple[bool, tuple[str, ...]]:
    if normalized is None:
        return False, ("F3_NORMALIZED_PERMISSION_MISSING",)
    reasons: list[str] = []
    if normalized.get("READ") is not PL_TF_002_REQUIRED_READ:
        reasons.append("F3_READ_REQUIREMENT_FAIL")
    if normalized.get("TRADE") is not PL_TF_002_REQUIRED_TRADE:
        reasons.append("F3_TRADE_REQUIREMENT_FAIL")
    if normalized.get("WITHDRAW") is not PL_TF_002_REQUIRED_WITHDRAW:
        reasons.append("F3_WITHDRAW_REQUIREMENT_FAIL")
    if normalized.get("WITHDRAW") is True:
        reasons.append("F3_UNEXPECTED_TREASURY_WITHDRAW_CAPABILITY")
    return len(reasons) == 0, tuple(reasons)


def verify_pl_tf_002_network_evidence_v1(
    evidence_bundle: Mapping[str, Any],
    *,
    now_unix_ms: int | None = None,
) -> dict[str, Any]:
    """Verify governed productive evidence for PL-TF-002 closure predicate."""
    now_ms = int(now_unix_ms if now_unix_ms is not None else time.time() * 1000)
    try:
        assert_evidence_redaction_invariant_v1(evidence_bundle)
    except PlTf002NetworkEvidenceError as exc:
        return _fail((str(exc),))

    provenance = evidence_bundle.get("EVIDENCE_PROVENANCE")
    if not isinstance(provenance, Mapping):
        return _fail(("EVIDENCE_PROVENANCE_MISSING",))

    prov_reasons = _validate_provenance(provenance, now_ms=now_ms)
    if prov_reasons:
        return _fail(prov_reasons)

    expected_uid = str(provenance.get("expected_credential_uid") or "")

    f1_block = evidence_bundle.get("F1_PRODUCTIVE_VENUE_GET")
    if not isinstance(f1_block, Mapping):
        return _fail(("F1_BLOCK_MISSING",))
    f1_ok, f1_reasons = _validate_f1(f1_block)

    f2_block = evidence_bundle.get("F2_NE_TF_001")
    if not isinstance(f2_block, Mapping):
        return _fail(("F2_BLOCK_MISSING",))
    f2_ok, normalized, f2_reasons = _validate_f2(f2_block, expected_uid=expected_uid)

    f3_ok, f3_reasons = _validate_f3(normalized)

    f4_ok = f2_ok and f3_ok and normalized is not None

    all_reasons = (*f1_reasons, *f2_reasons, *f3_reasons)
    closed = f1_ok and f2_ok and f3_ok and f4_ok and len(all_reasons) == 0

    return {
        "VERIFICATION_RESULT": "PASS" if closed else "FAIL_CLOSED",
        "REASONS": list(all_reasons),
        "RAW_VENUE_RESPONSE_BOUND": isinstance(f2_block.get("raw_venue_response"), Mapping),
        "NORMALIZED_PERMISSION_FACTS": normalized,
        "EVIDENCE_PROVENANCE": dict(provenance),
        "F1_PRODUCTIVE_VENUE_GET_PASS": f1_ok,
        "F2_NE_TF_001_PERMISSION_GET_PASS": f2_ok,
        "F3_TREASURY_CAPABILITY_NEGATIVE_PASS": f3_ok,
        "F4_VENUE_PERMISSION_UNKNOWN_CLEARED": f4_ok,
        "PL_TF_002_CLOSURE_RESULT": {
            "closed": closed,
            "status_if_closed": PL_TF_002_STATUS_CLOSED,
            "standing_status_unchanged": PL_TF_002_STATUS_STANDING,
            "standing_venue_permission_unknown": VENUE_PERMISSION_UNKNOWN_STANDING,
            "standing_venue_permission_get_performed": VENUE_PERMISSION_GET_PERFORMED_STANDING,
        },
        "AUTHORITY_ESCALATION": False,
        "LIVE_MINTED": False,
        "RISK_ADMISSIBLE_MINTED": False,
        "TREASURY_AUTHORITY_MINTED": False,
        "EXTERNAL_EFFECT_MINTED": False,
        "JOIN_SEAM_ID": JOIN_SEAM_ID,
    }
