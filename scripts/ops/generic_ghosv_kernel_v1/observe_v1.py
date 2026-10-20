"""Generic observation kernel. AUTHORITY=NONE.

Records caller-supplied findings after the WP-A0 pin and scope gate.
It does not read git or repository evidence, write artifacts, escalate
safety, or assign guardian identity.
"""

from __future__ import annotations

from typing import Any, Mapping

from scripts.ops.generic_ghosv_kernel_v1.constants_v1 import (
    AUTHORITY,
    COVERAGE_PROOF,
    EXECUTION_AUTHORITY,
    FINDING_CATEGORIES,
    FINDING_FIELDS,
    FINDING_STATUSES,
    GRAPH_ENGINE,
    GUARDIAN_IDENTITY,
    IMPLICIT_RELEASE,
    NETWORK_ACCESS,
    OBSERVATION_PROOF,
    OBSERVED_STATUS,
    REPOSITORY_EVIDENCE_WRITE,
    RUNTIME_AUTHORIZATION_EFFECT,
    SAFETY_AUTHORITY,
    SAFETY_ESCALATION_ENABLED,
    SCHEMA_ID,
    SCHEMA_VERSION,
    STATUS_INVALID_FINDING,
    STATUS_MISSING_EVIDENCE,
    STATUS_UNKNOWN_FINDING_TYPE,
    TRADING_AUTHORITY,
    UNASSIGNED_STATUS,
    UNKNOWN_STATUS,
)
from scripts.ops.pin_scope_binding_v1.bind_v1 import bind_pin_and_scope_v1
from scripts.ops.pin_scope_binding_v1.constants_v1 import STATUS_ACCEPTED

_KNOWN_CATEGORIES = frozenset(FINDING_CATEGORIES)
_KNOWN_STATUSES = frozenset(FINDING_STATUSES)


def run_generic_ghosv_v1(
    *,
    authoritative_commit_sha: str,
    authoritative_tree_sha: str,
    declared_commit_sha: str,
    declared_tree_sha: str,
    provenance: Mapping[str, Any],
    scope: Mapping[str, Any],
    findings: list[Any],
    evidence_refs: list[Any],
) -> dict[str, Any]:
    """Validate pin, scope, and typed findings, or return one fail-closed status."""
    binding = bind_pin_and_scope_v1(
        authoritative_commit_sha=authoritative_commit_sha,
        authoritative_tree_sha=authoritative_tree_sha,
        declared_commit_sha=declared_commit_sha,
        declared_tree_sha=declared_tree_sha,
        provenance=provenance,
        scope=scope,
    )
    if binding["status"] != STATUS_ACCEPTED:
        return _closed(
            binding,
            provenance=provenance,
            reasons=[binding["status"]],
        )

    evidence_reasons, evidence_ids = _parse_evidence_refs(evidence_refs)
    if evidence_reasons:
        return _closed(
            binding,
            provenance=provenance,
            status=STATUS_MISSING_EVIDENCE,
            reasons=evidence_reasons,
        )
    assert evidence_ids is not None

    parsed, failure = _parse_findings(findings, evidence_ids)
    if failure is not None:
        status, reasons = failure
        return _closed(binding, provenance=provenance, status=status, reasons=reasons)
    assert parsed is not None

    scope_failure = _scope_failure(parsed, binding)
    if scope_failure is not None:
        status, reasons = scope_failure
        return _closed(binding, provenance=provenance, status=status, reasons=reasons)

    return _accepted(binding, provenance=provenance, findings=parsed)


def _parse_evidence_refs(
    evidence_refs: list[Any],
) -> tuple[list[str], list[str] | None]:
    if not isinstance(evidence_refs, list):
        return ["evidence_refs_not_list"], None
    seen: set[str] = set()
    parsed: list[str] = []
    reasons: list[str] = []
    for index, ref in enumerate(evidence_refs):
        if not isinstance(ref, str) or ref.strip() == "":
            reasons.append(f"evidence_refs[{index}]_missing")
            continue
        if ref in seen:
            reasons.append(f"evidence_refs_duplicate:{ref}")
            continue
        seen.add(ref)
        parsed.append(ref)
    if reasons:
        return reasons, None
    return [], parsed


def _parse_findings(
    findings: list[Any],
    evidence_ids: list[str],
) -> tuple[list[dict[str, Any]] | None, tuple[str, list[str]] | None]:
    if not isinstance(findings, list):
        return None, (STATUS_INVALID_FINDING, ["findings_not_list"])
    evidence_set = set(evidence_ids)
    parsed: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    structural: list[str] = []
    unknown_types: list[str] = []
    missing_evidence: list[str] = []
    for index, finding in enumerate(findings):
        label = f"findings[{index}]"
        if not isinstance(finding, Mapping):
            structural.append(f"{label}_not_object")
            continue
        extra = sorted(set(finding) - set(FINDING_FIELDS))
        structural.extend(f"{label}_extra:{field}" for field in extra)
        body, field_reasons = _finding_fields(finding, label)
        structural.extend(field_reasons)
        if body is None:
            continue
        if body["finding_id"] in seen_ids:
            structural.append(f"finding_id_duplicate:{body['finding_id']}")
            continue
        seen_ids.add(body["finding_id"])
        if body["category"] not in _KNOWN_CATEGORIES or body["status"] not in _KNOWN_STATUSES:
            unknown_types.append(body["finding_id"])
            continue
        if body["evidence_ref"] not in evidence_set:
            missing_evidence.append(body["finding_id"])
            continue
        parsed.append(body)
    if structural:
        return None, (STATUS_INVALID_FINDING, structural)
    if unknown_types:
        return None, (
            STATUS_UNKNOWN_FINDING_TYPE,
            [f"unknown_finding_type:{finding_id}" for finding_id in unknown_types],
        )
    if missing_evidence:
        return None, (
            STATUS_MISSING_EVIDENCE,
            [f"missing_evidence:{finding_id}" for finding_id in missing_evidence],
        )
    parsed.sort(key=lambda item: item["finding_id"])
    return parsed, None


def _finding_fields(
    finding: Mapping[str, Any],
    label: str,
) -> tuple[dict[str, str] | None, list[str]]:
    reasons: list[str] = []
    body: dict[str, str] = {}
    for field in FINDING_FIELDS:
        if field not in finding:
            reasons.append(f"{label}_missing:{field}")
            continue
        value = finding[field]
        if not isinstance(value, str) or value.strip() == "":
            reasons.append(f"{label}_blank:{field}")
            continue
        body[field] = value
    if reasons:
        return None, reasons
    return body, []


def _scope_failure(
    findings: list[dict[str, str]],
    binding: Mapping[str, Any],
) -> tuple[str, list[str]] | None:
    allowed = set(binding["allowed_nodes"])
    excluded = set(binding["exclusions"])
    unassigned = set(binding["unassigned"])
    conflicts: list[str] = []
    unknown_nodes: list[str] = []
    for finding in findings:
        node = finding["affected_scope"]
        finding_status = finding["status"]
        if node in excluded or (node in unassigned and finding_status != UNASSIGNED_STATUS):
            conflicts.append(f"scope_conflict:{finding['finding_id']}:{node}")
            continue
        if node not in allowed and node not in unassigned:
            unknown_nodes.append(f"unknown_scope:{finding['finding_id']}:{node}")
    if conflicts:
        return "SCOPE_CONFLICT", conflicts
    if unknown_nodes:
        return "INVALID_SCOPE", unknown_nodes
    return None


def _accepted(
    binding: Mapping[str, Any],
    *,
    provenance: Mapping[str, Any],
    findings: list[dict[str, str]],
) -> dict[str, Any]:
    allowed = list(binding["allowed_nodes"])
    observed_nodes = {
        finding["affected_scope"]
        for finding in findings
        if finding["status"] == OBSERVED_STATUS and finding["affected_scope"] in allowed
    }
    coverage_gaps: list[dict[str, str]] = []
    uncertainties: list[str] = []
    for finding in findings:
        if finding["status"] == UNKNOWN_STATUS:
            coverage_gaps.append(_gap("UNKNOWN", finding))
            uncertainties.append(
                f"unknown_status:{finding['finding_id']}:{finding['affected_scope']}"
            )
        elif finding["status"] == UNASSIGNED_STATUS:
            coverage_gaps.append(_gap("UNASSIGNED", finding))
            uncertainties.append(
                f"unassigned_status:{finding['finding_id']}:{finding['affected_scope']}"
            )
    for node in allowed:
        if node not in observed_nodes:
            coverage_gaps.append({"kind": "ALLOWED_WITHOUT_FINDING", "affected_scope": node})
            uncertainties.append(f"allowed_without_finding:{node}")
    observation_coverage_gap = bool(coverage_gaps)
    scope_coverage_gap = bool(binding.get("scope_coverage_gap"))
    for node in list(binding.get("unassigned") or []):
        coverage_gaps.append({"kind": "UNASSIGNED_SCOPE", "affected_scope": str(node)})
        uncertainties.append(f"unassigned_scope:{node}")
    if scope_coverage_gap and not allowed:
        for node in list(binding.get("exclusions") or []):
            coverage_gaps.append({"kind": "EXCLUSION_NOT_COVERAGE", "affected_scope": str(node)})
            uncertainties.append(f"exclusion_not_coverage:{node}")
    coverage_gaps.sort(
        key=lambda item: (item["kind"], item.get("finding_id", ""), item["affected_scope"])
    )
    uncertainties.sort()
    typed = [
        {
            "finding_id": finding["finding_id"],
            "category": finding["category"],
            "observed_state": finding["observed_state"],
            "evidence_ref": finding["evidence_ref"],
            "affected_scope": finding["affected_scope"],
            "status": finding["status"],
            "counts_as_proof": False,
        }
        for finding in findings
    ]
    return _envelope(
        status=STATUS_ACCEPTED,
        binding=binding,
        provenance=provenance,
        findings=typed,
        coverage_gaps=coverage_gaps,
        uncertainties=uncertainties,
        findings_evaluated=True,
        scope_coverage_gap=scope_coverage_gap,
        graph_coverage_gap=False,
        observation_coverage_gap=observation_coverage_gap,
        reasons=[],
    )


def _gap(kind: str, finding: Mapping[str, str]) -> dict[str, str]:
    return {
        "kind": kind,
        "finding_id": finding["finding_id"],
        "affected_scope": finding["affected_scope"],
    }


def _closed(
    binding: Mapping[str, Any],
    *,
    provenance: Mapping[str, Any],
    status: str | None = None,
    reasons: list[str],
) -> dict[str, Any]:
    closed_status = binding["status"] if status is None else status
    return _envelope(
        status=closed_status,
        binding=binding,
        provenance=provenance,
        findings=[],
        coverage_gaps=[{"kind": closed_status}],
        uncertainties=[f"fail_closed:{closed_status}"],
        findings_evaluated=False,
        scope_coverage_gap=bool(binding.get("scope_coverage_gap")),
        graph_coverage_gap=False,
        observation_coverage_gap=False,
        reasons=reasons,
    )


def _envelope(
    *,
    status: str,
    binding: Mapping[str, Any],
    provenance: Mapping[str, Any],
    findings: list[dict[str, Any]],
    coverage_gaps: list[dict[str, str]],
    uncertainties: list[str],
    findings_evaluated: bool,
    scope_coverage_gap: bool,
    graph_coverage_gap: bool,
    observation_coverage_gap: bool,
    reasons: list[str],
) -> dict[str, Any]:
    coverage_gap = scope_coverage_gap or graph_coverage_gap or observation_coverage_gap
    if not findings_evaluated:
        coverage_gap = True
    return {
        "schema_id": SCHEMA_ID,
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "authority": AUTHORITY,
        "trading_authority": TRADING_AUTHORITY,
        "safety_authority": SAFETY_AUTHORITY,
        "execution_authority": EXECUTION_AUTHORITY,
        "runtime_authorization_effect": RUNTIME_AUTHORIZATION_EFFECT,
        "guardian_identity": GUARDIAN_IDENTITY,
        "safety_escalation_enabled": SAFETY_ESCALATION_ENABLED,
        "graph_engine": GRAPH_ENGINE,
        "network_access": NETWORK_ACCESS,
        "repository_evidence_write": REPOSITORY_EVIDENCE_WRITE,
        "implicit_release": IMPLICIT_RELEASE,
        "observation_proof": OBSERVATION_PROOF,
        "coverage_proof": COVERAGE_PROOF,
        "scope_coverage_gap": scope_coverage_gap,
        "graph_coverage_gap": graph_coverage_gap,
        "observation_coverage_gap": observation_coverage_gap,
        "coverage_gap": coverage_gap,
        "findings_evaluated": findings_evaluated,
        "pin_scope": dict(binding),
        "findings": findings,
        "coverage_gaps": coverage_gaps,
        "uncertainties": uncertainties,
        "provenance": _provenance_view(
            binding=binding,
            provenance=provenance,
        ),
        "reasons": list(reasons),
    }


def _provenance_view(
    *,
    binding: Mapping[str, Any],
    provenance: Mapping[str, Any],
) -> dict[str, Any]:
    source: dict[str, Any] = {}
    if isinstance(provenance, Mapping):
        for role, body in provenance.items():
            source[str(role)] = dict(body) if isinstance(body, Mapping) else body
    return {
        "authoritative_commit_sha": binding["authoritative_commit_sha"],
        "authoritative_tree_sha": binding["authoritative_tree_sha"],
        "declared_commit_sha": binding["declared_commit_sha"],
        "declared_tree_sha": binding["declared_tree_sha"],
        "source_provenance": source,
    }
