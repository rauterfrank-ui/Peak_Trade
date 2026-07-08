"""
Runtime Bridge Pre-Activation Gate Assessment v0.

Read-only assessment documenting the current pre-activation gate boundary after
PR #5024. Consumes manifest-verified PR5024 closeout evidence and evaluates the
existing RuntimeBridgePreActivationGateContractV0 fail-closed snapshot without
activating runtime, granting order authority, or promoting final success flags.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Literal, Mapping, Tuple

RUNTIME_BRIDGE_PRE_ACTIVATION_GATE_ASSESSMENT_LAYER_VERSION = "v0"
RUNTIME_BRIDGE_PRE_ACTIVATION_GATE_ASSESSMENT_OWNER = (
    "trading.master_v2.runtime_bridge_pre_activation_gate_assessment_v0"
)
ASSESSMENT_SLICE_ID = "RUNTIME_BRIDGE_PRE_ACTIVATION_GATE_ASSESSMENT_V0"
PACKAGE_MARKER = "RUNTIME_BRIDGE_PRE_ACTIVATION_GATE_ASSESSMENT_V0=true"
PLAN_TYPE = "ASSESSMENT_ONLY"

DEFAULT_PR5024_CLOSEOUT_EVIDENCE = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "research/merge_closeout_pr5024_next_full_canonical_parity_surface_after_pr5023_v0_20260708T233946Z"
)

AssessmentVerdict = Literal["PASS", "FAIL_CLOSED"]
GateAssessmentStatus = Literal["FAIL_CLOSED_DOCUMENTED", "UNEXPECTED_PASS", "EVALUATION_ERROR"]

REASON_SOURCE_MANIFEST_UNVERIFIED = "SOURCE_EVIDENCE_MANIFEST_NOT_VERIFIED"
REASON_PR5024_CLOSEOUT_MISSING = "PR5024_MERGE_CLOSEOUT_EVIDENCE_MISSING"
REASON_GATE_UNEXPECTED_PASS = "PRE_ACTIVATION_GATE_UNEXPECTED_PASS_AT_CURRENT_HEAD"
REASON_ACTIVATION_ADMISSIBLE_TRUE = "RUNTIME_BRIDGE_ACTIVATION_ADMISSIBLE_TRUE"
REASON_AUTHORITY_EFFECT_NON_NONE = "AUTHORITY_EFFECT_NON_NONE"

FORBIDDEN_POSITIVE_CLAIM_LITERALS = (
    "FULL_CANONICAL_CHAIN_WIRED=true",
    "BACKTEST_RUNTIME_DECISION_PARITY_PASS=true",
    "SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE=true",
    "RUNTIME_REWIRE_ADMISSIBLE=true",
    "CLAIM_PROMOTION_ALLOWED=true",
    "RUNTIME_BRIDGE_ACTIVATION_ADMISSIBLE=true",
)

FORBIDDEN_POSITIVE_ASSIGNMENT_RES = (
    re.compile(r"FULL_CANONICAL_CHAIN_WIRED\s*=\s*True\b"),
    re.compile(r"BACKTEST_RUNTIME_DECISION_PARITY_PASS\s*=\s*True\b"),
    re.compile(r"SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE\s*=\s*True\b"),
    re.compile(r"RUNTIME_REWIRE_ADMISSIBLE\s*=\s*True\b"),
    re.compile(r"CLAIM_PROMOTION_ALLOWED\s*=\s*True\b"),
    re.compile(r"RUNTIME_BRIDGE_ACTIVATION_ADMISSIBLE\s*=\s*True\b"),
    re.compile(r'"full_canonical_chain_wired"\s*:\s*true\b'),
    re.compile(r'"backtest_runtime_decision_parity_pass"\s*:\s*true\b'),
    re.compile(r'"system_economic_evidence_admissible"\s*:\s*true\b'),
    re.compile(r'"runtime_rewire_admissible"\s*:\s*true\b'),
    re.compile(r'"claim_promotion_allowed"\s*:\s*true\b'),
    re.compile(r'"runtime_bridge_activation_admissible"\s*:\s*true\b'),
)

_CONTEXT_PROTECTED_MARKERS = (
    "forbidden_claims",
    "FORBIDDEN_POSITIVE_CLAIM",
    "FORBIDDEN_POSITIVE_ASSIGNMENT",
    '_claimed": False',
    "is False",
    "== False",
    "!= True",
    "assert ",
    "# ",
    '"""',
    "'''",
    "unless fully proven",
    "denylist",
    "needle",
)


@dataclass(frozen=True)
class SourceEvidenceRefV0:
    evidence_id: str
    path: str
    present: bool
    manifest_present: bool
    manifest_verified: bool
    detail: str


@dataclass(frozen=True)
class RuntimeBridgePreActivationGateAssessmentResultV0:
    assessment_verdict: AssessmentVerdict
    gate_assessment_status: GateAssessmentStatus
    plan_type: str
    runtime_bridge_pre_activation_gate_status: str
    runtime_bridge_activation_admissible: bool
    surface_p_registry_status: str
    surface_p_semantic_post_status: str
    blocking_reasons: Tuple[str, ...]
    required_next_gates: Tuple[str, ...]
    primary_blocker: str
    next_step_after_pr: str
    source_evidence_referenced: bool
    source_manifest_verify_rc: int
    full_canonical_chain_wired: bool
    backtest_runtime_decision_parity_pass: bool
    system_economic_evidence_admissible: bool
    runtime_rewire_admissible: bool
    claim_promotion_allowed: bool
    no_runtime_authority_confirmed: bool
    no_economic_claim_confirmed: bool
    no_runtime_evidence_before_core_system_complete: bool
    fail_closed_reasons: Tuple[str, ...]


def _line_context_protected(line: str) -> bool:
    lowered = line.lower()
    for marker in _CONTEXT_PROTECTED_MARKERS:
        if marker in line or marker in lowered:
            return True
    for literal in FORBIDDEN_POSITIVE_CLAIM_LITERALS:
        if literal in line and ("forbidden" in lowered or "deny" in lowered or "needle" in lowered):
            return True
    return False


def scan_forbidden_positive_claims(repo_root: Path, changed_files: list[str]) -> list[str]:
    violations: list[str] = []
    for rel in changed_files:
        path = repo_root / rel
        if not path.is_file() or path.suffix != ".py":
            continue
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if _line_context_protected(line):
                continue
            for pattern in FORBIDDEN_POSITIVE_ASSIGNMENT_RES:
                if pattern.search(line):
                    violations.append(f"{rel}:{line_no}: {line.strip()}")
    return violations


def verify_source_manifest(evidence_dir: Path) -> tuple[bool, int, str]:
    manifest = evidence_dir / "MANIFEST.sha256"
    if not evidence_dir.is_dir():
        return False, -1, "directory_missing"
    if not manifest.is_file():
        return False, -1, "manifest_missing"
    rows = manifest.read_text(encoding="utf-8").splitlines()
    for row in rows:
        if not row.strip():
            continue
        digest, rel = row.split("  ", 1)
        target = evidence_dir / rel
        if not target.is_file():
            return False, 1, f"missing_file:{rel}"
        import hashlib

        actual = hashlib.sha256(target.read_bytes()).hexdigest()
        if actual != digest:
            return False, 1, f"digest_mismatch:{rel}"
    return True, 0, "verified"


def collect_source_evidence_refs(
    *,
    pr5024_closeout_dir: Path | None = None,
) -> Tuple[SourceEvidenceRefV0, ...]:
    closeout = pr5024_closeout_dir or Path(DEFAULT_PR5024_CLOSEOUT_EVIDENCE)
    present = closeout.is_dir()
    manifest_present = present and (closeout / "MANIFEST.sha256").is_file()
    if manifest_present:
        verified, rc, detail = verify_source_manifest(closeout)
        return (
            SourceEvidenceRefV0(
                evidence_id="pr5024_closeout",
                path=str(closeout),
                present=True,
                manifest_present=True,
                manifest_verified=verified,
                detail=detail if verified else f"rc={rc}:{detail}",
            ),
        )
    return (
        SourceEvidenceRefV0(
            evidence_id="pr5024_closeout",
            path=str(closeout),
            present=present,
            manifest_present=False,
            manifest_verified=False,
            detail="missing" if not present else "manifest_missing",
        ),
    )


def evaluate_runtime_bridge_pre_activation_gate_assessment_v0(
    *,
    pr5024_closeout_dir: Path | None = None,
    source_manifest_verify_rc: int | None = None,
) -> RuntimeBridgePreActivationGateAssessmentResultV0:
    """Document current pre-activation gate boundary; never grants runtime authority."""
    from trading.master_v2.full_canonical_system_backtest_parity_gap_assessment_v0 import (
        parity_surface_assessments_v0,
    )
    from trading.master_v2.runtime_bridge_pre_activation_gate_v0 import (
        current_head_default_gate_input_v0,
        evaluate_runtime_bridge_pre_activation_gate_v0,
    )
    from trading.master_v2.surface_p_semantic_parity_gap_assessment_v0 import (
        DEFAULT_PR5022_PROOF_BUNDLE_EVIDENCE,
        evaluate_surface_p_semantic_parity_gap_assessment_v0,
    )

    fail_reasons: list[str] = []
    source_refs = collect_source_evidence_refs(pr5024_closeout_dir=pr5024_closeout_dir)
    closeout_ref = source_refs[0]
    source_evidence_referenced = closeout_ref.present
    manifest_rc = (
        source_manifest_verify_rc
        if source_manifest_verify_rc is not None
        else (0 if closeout_ref.manifest_verified else -1)
    )
    if not closeout_ref.present:
        fail_reasons.append(REASON_PR5024_CLOSEOUT_MISSING)
    elif manifest_rc != 0:
        fail_reasons.append(REASON_SOURCE_MANIFEST_UNVERIFIED)

    surface_p = next(item for item in parity_surface_assessments_v0() if item.surface_id == "P")
    surface_p_registry_status = surface_p.parity_status

    proof_bundle = Path(DEFAULT_PR5022_PROOF_BUNDLE_EVIDENCE)
    semantic = evaluate_surface_p_semantic_parity_gap_assessment_v0(
        pr5022_proof_bundle_dir=proof_bundle if proof_bundle.is_dir() else None,
        source_manifest_verify_rc=manifest_rc if manifest_rc != -1 else None,
    )
    surface_p_semantic_post_status = semantic.surface_p_post_status

    gate_input = current_head_default_gate_input_v0()
    gate_result = evaluate_runtime_bridge_pre_activation_gate_v0(gate_input)

    if gate_result.runtime_bridge_pre_activation_gate_status == "PASS":
        fail_reasons.append(REASON_GATE_UNEXPECTED_PASS)
        gate_status: GateAssessmentStatus = "UNEXPECTED_PASS"
    elif gate_result.runtime_bridge_activation_admissible:
        fail_reasons.append(REASON_ACTIVATION_ADMISSIBLE_TRUE)
        gate_status = "EVALUATION_ERROR"
    elif gate_result.authority_effect != "NONE":
        fail_reasons.append(REASON_AUTHORITY_EFFECT_NON_NONE)
        gate_status = "EVALUATION_ERROR"
    else:
        gate_status = "FAIL_CLOSED_DOCUMENTED"

    primary_blocker = gate_result.blocking_reasons[0] if gate_result.blocking_reasons else "NONE"
    next_step_after_pr = (
        gate_result.required_next_gates[0]
        if gate_result.required_next_gates
        else "OPERATOR_GO_SEPARATE_RUNTIME_BRIDGE_ACTIVATION"
    )

    assessment_verdict: AssessmentVerdict = (
        "PASS"
        if (
            gate_status == "FAIL_CLOSED_DOCUMENTED"
            and gate_result.runtime_bridge_pre_activation_gate_status == "FAIL"
            and not gate_result.runtime_bridge_activation_admissible
            and manifest_rc == 0
            and gate_result.authority_effect == "NONE"
            and gate_result.runtime_effect == "NONE"
            and gate_result.order_effect == "NONE"
            and not gate_result.execution_eligible
            and not gate_result.adapter_compatible
        )
        else "FAIL_CLOSED"
    )

    return RuntimeBridgePreActivationGateAssessmentResultV0(
        assessment_verdict=assessment_verdict,
        gate_assessment_status=gate_status,
        plan_type=PLAN_TYPE,
        runtime_bridge_pre_activation_gate_status=gate_result.runtime_bridge_pre_activation_gate_status,
        runtime_bridge_activation_admissible=gate_result.runtime_bridge_activation_admissible,
        surface_p_registry_status=surface_p_registry_status,
        surface_p_semantic_post_status=surface_p_semantic_post_status,
        blocking_reasons=gate_result.blocking_reasons,
        required_next_gates=gate_result.required_next_gates,
        primary_blocker=primary_blocker,
        next_step_after_pr=next_step_after_pr,
        source_evidence_referenced=source_evidence_referenced,
        source_manifest_verify_rc=manifest_rc,
        full_canonical_chain_wired=False,
        backtest_runtime_decision_parity_pass=False,
        system_economic_evidence_admissible=False,
        runtime_rewire_admissible=False,
        claim_promotion_allowed=False,
        no_runtime_authority_confirmed=True,
        no_economic_claim_confirmed=True,
        no_runtime_evidence_before_core_system_complete=True,
        fail_closed_reasons=tuple(dict.fromkeys(fail_reasons)),
    )


def runtime_bridge_pre_activation_gate_assessment_to_dict_v0(
    result: RuntimeBridgePreActivationGateAssessmentResultV0,
) -> Mapping[str, object]:
    return {
        "assessment_version": RUNTIME_BRIDGE_PRE_ACTIVATION_GATE_ASSESSMENT_LAYER_VERSION,
        "assessment_owner": RUNTIME_BRIDGE_PRE_ACTIVATION_GATE_ASSESSMENT_OWNER,
        "assessment_slice_id": ASSESSMENT_SLICE_ID,
        "assessment_verdict": result.assessment_verdict,
        "gate_assessment_status": result.gate_assessment_status,
        "plan_type": result.plan_type,
        "runtime_bridge_pre_activation_gate_status": (
            result.runtime_bridge_pre_activation_gate_status
        ),
        "runtime_bridge_activation_admissible": result.runtime_bridge_activation_admissible,
        "surface_p_registry_status": result.surface_p_registry_status,
        "surface_p_semantic_post_status": result.surface_p_semantic_post_status,
        "blocking_reasons": list(result.blocking_reasons),
        "required_next_gates": list(result.required_next_gates),
        "primary_blocker": result.primary_blocker,
        "next_step_after_pr": result.next_step_after_pr,
        "source_evidence_referenced": result.source_evidence_referenced,
        "source_manifest_verify_rc": result.source_manifest_verify_rc,
        "full_canonical_chain_wired": result.full_canonical_chain_wired,
        "backtest_runtime_decision_parity_pass": result.backtest_runtime_decision_parity_pass,
        "system_economic_evidence_admissible": result.system_economic_evidence_admissible,
        "runtime_rewire_admissible": result.runtime_rewire_admissible,
        "claim_promotion_allowed": result.claim_promotion_allowed,
        "no_runtime_authority_confirmed": result.no_runtime_authority_confirmed,
        "no_economic_claim_confirmed": result.no_economic_claim_confirmed,
        "no_runtime_evidence_before_core_system_complete": (
            result.no_runtime_evidence_before_core_system_complete
        ),
        "fail_closed_reasons": list(result.fail_closed_reasons),
    }


def render_runtime_bridge_pre_activation_gate_matrix_json_v0(
    *,
    pr5024_closeout_dir: Path | None = None,
) -> str:
    result = evaluate_runtime_bridge_pre_activation_gate_assessment_v0(
        pr5024_closeout_dir=pr5024_closeout_dir,
    )
    source_refs = collect_source_evidence_refs(pr5024_closeout_dir=pr5024_closeout_dir)
    payload = {
        **dict(runtime_bridge_pre_activation_gate_assessment_to_dict_v0(result)),
        "source_evidence_refs": [
            {
                "evidence_id": ref.evidence_id,
                "path": ref.path,
                "present": ref.present,
                "manifest_present": ref.manifest_present,
                "manifest_verified": ref.manifest_verified,
                "detail": ref.detail,
            }
            for ref in source_refs
        ],
    }
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def render_runtime_bridge_pre_activation_gate_report_markdown_v0(
    *,
    pr5024_closeout_dir: Path | None = None,
) -> str:
    result = evaluate_runtime_bridge_pre_activation_gate_assessment_v0(
        pr5024_closeout_dir=pr5024_closeout_dir,
    )
    lines = [
        "# Runtime Bridge Pre-Activation Gate Assessment v0",
        "",
        "MODE=READ_ONLY_NO_RUNTIME_NO_REWIRE",
        "",
        "## Verdict",
        "",
        f"- assessment_verdict: {result.assessment_verdict}",
        f"- gate_assessment_status: {result.gate_assessment_status}",
        f"- plan_type: {result.plan_type}",
        "",
        "## Gate Status",
        "",
        (
            "- runtime_bridge_pre_activation_gate_status: "
            f"{result.runtime_bridge_pre_activation_gate_status}"
        ),
        (
            "- runtime_bridge_activation_admissible: "
            f"{str(result.runtime_bridge_activation_admissible).lower()}"
        ),
        f"- primary_blocker: {result.primary_blocker}",
        "",
        "## Surface P Context",
        "",
        f"- surface_p_registry_status: {result.surface_p_registry_status}",
        f"- surface_p_semantic_post_status: {result.surface_p_semantic_post_status}",
        "",
        "## Blocking Reasons",
        "",
    ]
    if result.blocking_reasons:
        lines.extend(f"- {item}" for item in result.blocking_reasons)
    else:
        lines.append("- NONE")
    lines.extend(
        [
            "",
            "## Required Next Gates",
            "",
        ]
    )
    if result.required_next_gates:
        lines.extend(f"- {item}" for item in result.required_next_gates)
    else:
        lines.append("- NONE")
    lines.extend(
        [
            "",
            "## Final Status (fail-closed)",
            "",
            f"FULL_CANONICAL_CHAIN_WIRED={str(result.full_canonical_chain_wired).lower()}",
            (
                "BACKTEST_RUNTIME_DECISION_PARITY_PASS="
                f"{str(result.backtest_runtime_decision_parity_pass).lower()}"
            ),
            (
                "SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE="
                f"{str(result.system_economic_evidence_admissible).lower()}"
            ),
            f"RUNTIME_REWIRE_ADMISSIBLE={str(result.runtime_rewire_admissible).lower()}",
            f"CLAIM_PROMOTION_ALLOWED={str(result.claim_promotion_allowed).lower()}",
            (
                "NO_RUNTIME_EVIDENCE_BEFORE_CORE_SYSTEM_COMPLETE="
                f"{str(result.no_runtime_evidence_before_core_system_complete).lower()}"
            ),
            f"NEXT_STEP_AFTER_PR={result.next_step_after_pr}",
            "NO_RUNTIME_AUTHORITY_CONFIRMED=true",
            "NO_ECONOMIC_CLAIM_CONFIRMED=true",
        ]
    )
    return "\n".join(lines) + "\n"


def assessment_result_field_names_v0() -> Tuple[str, ...]:
    return tuple(field.name for field in fields(RuntimeBridgePreActivationGateAssessmentResultV0))
