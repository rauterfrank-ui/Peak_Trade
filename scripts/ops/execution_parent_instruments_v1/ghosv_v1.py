"""Execution GHOSV observation of admitted disclosure findings. AUTHORITY=NONE."""

from __future__ import annotations

from typing import Any, Mapping

from scripts.ops.execution_parent_disclosure_v1.constants_v1 import (
    ACTIVATION,
    AUTHORITY,
    DOUBLE_PLAY_FULL_OWNER_LOCK,
    STATUS_ADMITTED,
)
from scripts.ops.generic_ghosv_kernel_v1.constants_v1 import (
    OBSERVATION_PROOF,
    SAFETY_ESCALATION_ENABLED,
    STATUS_MISSING_EVIDENCE,
    UNKNOWN_STATUS,
)
from scripts.ops.generic_ghosv_kernel_v1.observe_v1 import (
    _parse_evidence_refs,
    _parse_findings,
)


def run_execution_ghosv_disclosure_v1(
    *,
    admission: Mapping[str, Any],
    findings: list[Any],
    evidence_refs: list[Any],
) -> dict[str, Any]:
    """Parse findings and keep them inside the admitted disclosure subjects."""
    if admission.get("status") != STATUS_ADMITTED:
        return _envelope(str(admission.get("status") or "REJECTED"), findings_evaluated=False)
    observed = {
        str(subject["subject_id"])
        for subject in admission.get("observed_subjects") or []
        if isinstance(subject, Mapping)
    }
    unknown = {
        str(subject["subject_id"])
        for subject in admission.get("unknown_subjects") or []
        if isinstance(subject, Mapping)
    }
    evidence_reasons, evidence_ids = _parse_evidence_refs(evidence_refs)
    if evidence_reasons:
        return _envelope(
            STATUS_MISSING_EVIDENCE,
            findings_evaluated=False,
            reasons=evidence_reasons,
        )
    assert evidence_ids is not None
    parsed, failure = _parse_findings(findings, evidence_ids)
    if failure is not None:
        status, reasons = failure
        return _envelope(status, findings_evaluated=False, reasons=reasons)
    assert parsed is not None
    scope_reasons = _scope_reasons(parsed, observed=observed, unknown=unknown)
    if scope_reasons:
        return _envelope("INVALID_SCOPE", findings_evaluated=False, reasons=scope_reasons)
    return _envelope(
        "ACCEPTED",
        findings_evaluated=True,
        findings=parsed,
        reasons=[],
    )


def findings_for_inventory_v1(
    inventory: Mapping[str, Any],
    *,
    commit_sha: str,
) -> tuple[list[dict[str, str]], list[str]]:
    """Build findings only for subjects and edges the inventory actually verified."""
    findings: list[dict[str, str]] = []
    refs: list[str] = []
    for subject in inventory["disclosure_subjects"]:
        if subject["classification"] != "OBSERVED":
            continue
        ref = _ref(commit_sha, subject["subject_id"])
        refs.append(ref)
        findings.append(
            {
                "finding_id": f"presence:{subject['subject_id']}",
                "category": "PRESENCE",
                "observed_state": "SYMBOL_PRESENT_IN_PINNED_TREE",
                "evidence_ref": ref,
                "affected_scope": subject["subject_id"],
                "status": "OBSERVED",
                "finding_kind": "OBSERVATION",
                "reachability": "UNKNOWN",
            }
        )
    unknown = next(
        subject
        for subject in inventory["disclosure_subjects"]
        if subject["classification"] == "UNKNOWN"
    )
    unknown_ref = _ref(commit_sha, unknown["subject_id"])
    refs.append(unknown_ref)
    findings.append(
        {
            "finding_id": f"absence:{unknown['subject_id']}",
            "category": "ABSENCE",
            "observed_state": "NOT_INVENTORIED",
            "evidence_ref": unknown_ref,
            "affected_scope": unknown["subject_id"],
            "status": UNKNOWN_STATUS,
            "finding_kind": "REACHABILITY",
            "reachability": "UNKNOWN",
        }
    )
    for guard in inventory.get("policy_guards") or []:
        ref = _ref(commit_sha, str(guard["guard_id"]))
        refs.append(ref)
        findings.append(
            {
                "finding_id": f"guard:{guard['guard_id']}",
                "category": str(guard["category"]),
                "observed_state": str(guard["observed_state"]),
                "evidence_ref": ref,
                "affected_scope": str(guard["subject_id"]),
                "status": "OBSERVED",
                "finding_kind": str(guard["finding_kind"]),
                "reachability": "UNKNOWN",
            }
        )
    for edge in inventory.get("unknown_edges") or []:
        scope = _unknown_scope(str(edge.get("edge_id") or ""), inventory)
        ref = _ref(commit_sha, str(edge.get("edge_id") or "unknown-edge"))
        refs.append(ref)
        findings.append(
            {
                "finding_id": f"reachability:{edge['edge_id']}",
                "category": "ABSENCE",
                "observed_state": "CALL_NOT_PROVEN",
                "evidence_ref": ref,
                "affected_scope": scope,
                "status": UNKNOWN_STATUS,
                "finding_kind": "REACHABILITY",
                "reachability": "UNKNOWN",
            }
        )
    return findings, refs


def _unknown_scope(edge_id: str, inventory: Mapping[str, Any]) -> str:
    if edge_id.startswith("execution.pre_external.fresh_runtime_applicability"):
        return "execution.pre_external.fresh_runtime_applicability"
    unknown = next(
        subject["subject_id"]
        for subject in inventory["disclosure_subjects"]
        if subject["classification"] == "UNKNOWN"
    )
    return str(unknown)


def _ref(commit_sha: str, subject_id: str) -> str:
    return f"pin:{commit_sha}/subject:{subject_id}"


def _scope_reasons(
    findings: list[dict[str, str]],
    *,
    observed: set[str],
    unknown: set[str],
) -> list[str]:
    reasons: list[str] = []
    for finding in findings:
        scope = finding["affected_scope"]
        if scope not in observed and scope not in unknown:
            reasons.append(f"unknown_scope:{finding['finding_id']}:{scope}")
            continue
        if finding["status"] == "OBSERVED" and scope not in observed:
            reasons.append(f"observed_on_unknown_subject:{finding['finding_id']}")
    return reasons


def _envelope(
    status: str,
    *,
    findings_evaluated: bool,
    reasons: list[str] | None = None,
    findings: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    return {
        "instrument_id": "PARENT_EXECUTION_GHOSV",
        "status": status,
        "authority": AUTHORITY,
        "activation": ACTIVATION,
        "membership_ratified": False,
        "guardian_ratified": False,
        "domain_bound": False,
        "operationally_ready": False,
        "causal_closure_proven": False,
        "current_validated": False,
        "post_allowed": False,
        "external_effect_authorized": False,
        "productive_activation": False,
        "double_play_full_owner_lock": DOUBLE_PLAY_FULL_OWNER_LOCK,
        "safety_escalation_enabled": SAFETY_ESCALATION_ENABLED,
        "observation_proof": OBSERVATION_PROOF,
        "repository_evidence_write": False,
        "files_written": False,
        "findings_evaluated": findings_evaluated,
        "counts_as_proof": False,
        "guardian_active": False,
        "findings": list(findings or []),
        "reasons": list(reasons or []),
        "productive_runtime_evidence": False,
    }
