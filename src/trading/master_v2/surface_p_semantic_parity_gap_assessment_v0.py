"""
Surface P semantic parity gap assessment v0.

Read-only / offline-only assessment that documents Surface P PARTIAL reason and
proves semantic parity beyond trace-binding where targeted test confirmation and
manifest-verified PR5022 proof bundle evidence permit. Does not activate runtime,
grant order authority, or promote final success flags.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Literal, Mapping, Tuple

SURFACE_P_SEMANTIC_PARITY_GAP_ASSESSMENT_LAYER_VERSION = "v0"
SURFACE_P_SEMANTIC_PARITY_GAP_ASSESSMENT_OWNER = (
    "trading.master_v2.surface_p_semantic_parity_gap_assessment_v0"
)
ASSESSMENT_SLICE_ID = "SURFACE_P_SEMANTIC_PARITY_GAP_ASSESSMENT_V0"
PACKAGE_MARKER = "SURFACE_P_SEMANTIC_PARITY_GAP_ASSESSMENT_V0=true"

DEFAULT_PR5022_PROOF_BUNDLE_EVIDENCE = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "research/full_canonical_parity_proof_bundle_v0_20260708T224152Z"
)
DEFAULT_PR5022_CLOSEOUT_EVIDENCE = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "research/merge_closeout_pr5022_full_canonical_parity_proof_bundle_assembler_v0_20260708T224613Z"
)

SurfacePGapAssessmentParityStatus = Literal["PASS", "PARTIAL", "GAP", "NOT_APPLICABLE"]
SemanticParityBeyondTraceBindingStatus = Literal["PASS", "FAIL_CLOSED"]
SurfacePPostStatus = Literal["PASS", "PARTIAL_FAIL_CLOSED"]

REASON_RUNTIME_BRIDGE_BOUND_NOT_ACTIVATED = "RUNTIME_BRIDGE_BOUND_NOT_ACTIVATED_BY_POLICY"
REASON_OFFLINE_FOUR_WAY_INCOMPLETE = "OFFLINE_FOUR_WAY_PARITY_INCOMPLETE"
REASON_SEMANTIC_BINDING_INCOMPLETE = "SEMANTIC_BINDING_CONFIRMATION_INCOMPLETE"
REASON_SOURCE_MANIFEST_UNVERIFIED = "SOURCE_EVIDENCE_MANIFEST_NOT_VERIFIED"
REASON_TRACE_COVERAGE_INCOMPLETE = "PR5022_TRACE_SURFACE_COVERAGE_INCOMPLETE"
REASON_CHAIN_BINDING_INCOMPLETE = "PR5022_CHAIN_SURFACE_BINDING_INCOMPLETE"
REASON_PROOF_BUNDLE_MISSING = "PR5022_PROOF_BUNDLE_EVIDENCE_MISSING"

FORBIDDEN_POSITIVE_CLAIM_LITERALS = (
    "FULL_CANONICAL_CHAIN_WIRED=true",
    "BACKTEST_RUNTIME_DECISION_PARITY_PASS=true",
    "SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE=true",
    "RUNTIME_REWIRE_ADMISSIBLE=true",
    "CLAIM_PROMOTION_ALLOWED=true",
)

FORBIDDEN_POSITIVE_ASSIGNMENT_RES = (
    re.compile(r"FULL_CANONICAL_CHAIN_WIRED\s*=\s*True\b"),
    re.compile(r"BACKTEST_RUNTIME_DECISION_PARITY_PASS\s*=\s*True\b"),
    re.compile(r"SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE\s*=\s*True\b"),
    re.compile(r"RUNTIME_REWIRE_ADMISSIBLE\s*=\s*True\b"),
    re.compile(r"CLAIM_PROMOTION_ALLOWED\s*=\s*True\b"),
    re.compile(r'"full_canonical_chain_wired"\s*:\s*true\b'),
    re.compile(r'"backtest_runtime_decision_parity_pass"\s*:\s*true\b'),
    re.compile(r'"system_economic_evidence_admissible"\s*:\s*true\b'),
    re.compile(r'"runtime_rewire_admissible"\s*:\s*true\b'),
    re.compile(r'"claim_promotion_allowed"\s*:\s*true\b'),
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
class SurfacePSemanticParityGapAssessmentResultV0:
    surface_p_gap_assessment_parity_status: SurfacePGapAssessmentParityStatus
    semantic_parity_beyond_trace_binding: SemanticParityBeyondTraceBindingStatus
    surface_p_post_status: SurfacePPostStatus
    surface_p_partial_reason: str
    missing_semantic_parity_proof_beyond_trace_binding: Tuple[str, ...]
    offline_four_way_fixtures_complete: bool
    semantic_binding_confirmations_complete: bool
    pr5022_trace_surface_coverage_complete: bool
    pr5022_chain_surface_binding_complete: bool
    source_evidence_referenced: bool
    source_manifest_verify_rc: int
    full_canonical_chain_wired: bool
    backtest_runtime_decision_parity_pass: bool
    system_economic_evidence_admissible: bool
    runtime_rewire_admissible: bool
    claim_promotion_allowed: bool
    no_runtime_authority_confirmed: bool
    no_economic_claim_confirmed: bool
    next_blocker: str
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
    pr5022_proof_bundle_dir: Path | None = None,
    pr5022_closeout_dir: Path | None = None,
) -> Tuple[SourceEvidenceRefV0, ...]:
    proof_bundle = pr5022_proof_bundle_dir or Path(DEFAULT_PR5022_PROOF_BUNDLE_EVIDENCE)
    closeout = pr5022_closeout_dir or Path(DEFAULT_PR5022_CLOSEOUT_EVIDENCE)
    refs: list[SourceEvidenceRefV0] = []
    for evidence_id, path in (
        ("pr5022_proof_bundle", proof_bundle),
        ("pr5022_closeout", closeout),
    ):
        present = path.is_dir()
        manifest_present = present and (path / "MANIFEST.sha256").is_file()
        if manifest_present:
            verified, rc, detail = verify_source_manifest(path)
            refs.append(
                SourceEvidenceRefV0(
                    evidence_id=evidence_id,
                    path=str(path),
                    present=True,
                    manifest_present=True,
                    manifest_verified=verified,
                    detail=detail if verified else f"rc={rc}:{detail}",
                )
            )
        else:
            refs.append(
                SourceEvidenceRefV0(
                    evidence_id=evidence_id,
                    path=str(path),
                    present=present,
                    manifest_present=False,
                    manifest_verified=False,
                    detail="missing" if not present else "manifest_missing",
                )
            )
    return tuple(refs)


def _load_pr5022_proof_bundle_payload(proof_bundle_dir: Path) -> dict[str, object] | None:
    bundle_path = proof_bundle_dir / "proof_bundle.json"
    if not bundle_path.is_file():
        return None
    return json.loads(bundle_path.read_text(encoding="utf-8"))


def _surface_p_gap_assessment_entry_v0() -> tuple[SurfacePGapAssessmentParityStatus, str]:
    from trading.master_v2.full_canonical_system_backtest_parity_gap_assessment_v0 import (
        parity_surface_assessments_v0,
    )

    surface_p = next(item for item in parity_surface_assessments_v0() if item.surface_id == "P")
    return surface_p.parity_status, surface_p.missing_binding_if_any


def evaluate_surface_p_semantic_parity_gap_assessment_v0(
    *,
    pr5022_proof_bundle_dir: Path | None = None,
    pr5022_closeout_dir: Path | None = None,
    source_manifest_verify_rc: int | None = None,
) -> SurfacePSemanticParityGapAssessmentResultV0:
    """Evaluate Surface P semantic parity gap; never grants runtime or promotion authority."""
    from trading.master_v2.integrated_vs_scenario_replay_full_system_parity_harness_v0 import (
        evaluate_surface_p_full_bar_sequence_four_way_parity_v0,
    )
    from trading.master_v2.surface_p_final_flags_fail_closed_contract_v0 import (
        REQUIRED_SEMANTIC_BINDING_CONFIRMATIONS_V0,
        derive_targeted_semantic_binding_confirmations_from_gap_assessment_v0,
    )
    from trading.master_v2.surface_p_offline_complete_runtime_bridge_bound_not_activated_contract_v0 import (
        evaluate_surface_p_offline_complete_runtime_bridge_bound_not_activated_contract_v0,
    )

    fail_reasons: list[str] = []
    source_refs = collect_source_evidence_refs(
        pr5022_proof_bundle_dir=pr5022_proof_bundle_dir,
        pr5022_closeout_dir=pr5022_closeout_dir,
    )
    proof_bundle_ref = next(ref for ref in source_refs if ref.evidence_id == "pr5022_proof_bundle")
    source_evidence_referenced = proof_bundle_ref.present
    manifest_rc = (
        source_manifest_verify_rc
        if source_manifest_verify_rc is not None
        else (0 if proof_bundle_ref.manifest_verified else -1)
    )
    if not proof_bundle_ref.present:
        fail_reasons.append(REASON_PROOF_BUNDLE_MISSING)
    elif manifest_rc != 0:
        fail_reasons.append(REASON_SOURCE_MANIFEST_UNVERIFIED)

    proof_bundle_payload: dict[str, object] | None = None
    if proof_bundle_ref.present:
        proof_bundle_payload = _load_pr5022_proof_bundle_payload(Path(proof_bundle_ref.path))

    trace_coverage_complete = bool(
        proof_bundle_payload
        and proof_bundle_payload.get("surface_coverage_complete") is True
        and proof_bundle_payload.get("covered_surface_count") == 12
    )
    chain_binding_complete = bool(
        proof_bundle_payload and proof_bundle_payload.get("chain_surface_binding_complete") is True
    )
    if proof_bundle_payload and not trace_coverage_complete:
        fail_reasons.append(REASON_TRACE_COVERAGE_INCOMPLETE)
    if proof_bundle_payload and not chain_binding_complete:
        fail_reasons.append(REASON_CHAIN_BINDING_INCOMPLETE)

    bar_assessment = evaluate_surface_p_full_bar_sequence_four_way_parity_v0()
    semantic = evaluate_surface_p_offline_complete_runtime_bridge_bound_not_activated_contract_v0(
        offline_four_way_fixtures_complete=bar_assessment.fixtures_complete,
    )
    gap_parity_status, partial_reason = _surface_p_gap_assessment_entry_v0()

    offline_complete = bar_assessment.fixtures_complete
    if not offline_complete:
        fail_reasons.append(REASON_OFFLINE_FOUR_WAY_INCOMPLETE)

    confirmations = derive_targeted_semantic_binding_confirmations_from_gap_assessment_v0()
    missing_bindings = tuple(
        key
        for key in REQUIRED_SEMANTIC_BINDING_CONFIRMATIONS_V0
        if not confirmations.get(key, False)
    )
    semantic_bindings_complete = not missing_bindings
    if missing_bindings:
        fail_reasons.append(REASON_SEMANTIC_BINDING_INCOMPLETE)
        for binding in missing_bindings:
            fail_reasons.append(f"missing_semantic_binding:{binding}")

    runtime_bridge_blocked = (
        semantic.surface_p_runtime_bridge_binding_status == "BOUND_NOT_ACTIVATED"
    )
    if runtime_bridge_blocked:
        fail_reasons.append(REASON_RUNTIME_BRIDGE_BOUND_NOT_ACTIVATED)

    missing_proof_beyond_trace: list[str] = []
    if not trace_coverage_complete:
        missing_proof_beyond_trace.append("pr5022_trace_surface_coverage_complete")
    if not chain_binding_complete:
        missing_proof_beyond_trace.append("pr5022_chain_surface_binding_complete")
    if not semantic_bindings_complete:
        missing_proof_beyond_trace.extend(f"semantic_binding:{b}" for b in missing_bindings)
    if not offline_complete:
        missing_proof_beyond_trace.append("offline_four_way_bar_sequence_parity")
    if manifest_rc != 0:
        missing_proof_beyond_trace.append("source_manifest_verified")
    if runtime_bridge_blocked:
        missing_proof_beyond_trace.append("runtime_bridge_activation_policy_blocked")

    offline_semantic_ok = (
        offline_complete
        and semantic_bindings_complete
        and trace_coverage_complete
        and chain_binding_complete
        and manifest_rc == 0
    )
    semantic_beyond_trace: SemanticParityBeyondTraceBindingStatus = (
        "PASS" if offline_semantic_ok else "FAIL_CLOSED"
    )

    if offline_semantic_ok and runtime_bridge_blocked:
        surface_p_post: SurfacePPostStatus = "PASS"
        next_blocker = REASON_RUNTIME_BRIDGE_BOUND_NOT_ACTIVATED
    elif offline_semantic_ok:
        surface_p_post = "PASS"
        next_blocker = "NONE"
    else:
        surface_p_post = "PARTIAL_FAIL_CLOSED"
        next_blocker = fail_reasons[0] if fail_reasons else REASON_OFFLINE_FOUR_WAY_INCOMPLETE

    return SurfacePSemanticParityGapAssessmentResultV0(
        surface_p_gap_assessment_parity_status=gap_parity_status,
        semantic_parity_beyond_trace_binding=semantic_beyond_trace,
        surface_p_post_status=surface_p_post,
        surface_p_partial_reason=partial_reason,
        missing_semantic_parity_proof_beyond_trace_binding=tuple(missing_proof_beyond_trace),
        offline_four_way_fixtures_complete=offline_complete,
        semantic_binding_confirmations_complete=semantic_bindings_complete,
        pr5022_trace_surface_coverage_complete=trace_coverage_complete,
        pr5022_chain_surface_binding_complete=chain_binding_complete,
        source_evidence_referenced=source_evidence_referenced,
        source_manifest_verify_rc=manifest_rc,
        full_canonical_chain_wired=False,
        backtest_runtime_decision_parity_pass=False,
        system_economic_evidence_admissible=False,
        runtime_rewire_admissible=False,
        claim_promotion_allowed=False,
        no_runtime_authority_confirmed=True,
        no_economic_claim_confirmed=True,
        next_blocker=next_blocker,
        fail_closed_reasons=tuple(fail_reasons),
    )


def surface_p_semantic_parity_gap_assessment_to_dict_v0(
    result: SurfacePSemanticParityGapAssessmentResultV0,
) -> Mapping[str, object]:
    return {
        "assessment_version": SURFACE_P_SEMANTIC_PARITY_GAP_ASSESSMENT_LAYER_VERSION,
        "assessment_owner": SURFACE_P_SEMANTIC_PARITY_GAP_ASSESSMENT_OWNER,
        "assessment_slice_id": ASSESSMENT_SLICE_ID,
        "surface_p_gap_assessment_parity_status": result.surface_p_gap_assessment_parity_status,
        "semantic_parity_beyond_trace_binding": result.semantic_parity_beyond_trace_binding,
        "surface_p_post_status": result.surface_p_post_status,
        "surface_p_partial_reason": result.surface_p_partial_reason,
        "missing_semantic_parity_proof_beyond_trace_binding": list(
            result.missing_semantic_parity_proof_beyond_trace_binding
        ),
        "offline_four_way_fixtures_complete": result.offline_four_way_fixtures_complete,
        "semantic_binding_confirmations_complete": result.semantic_binding_confirmations_complete,
        "pr5022_trace_surface_coverage_complete": result.pr5022_trace_surface_coverage_complete,
        "pr5022_chain_surface_binding_complete": result.pr5022_chain_surface_binding_complete,
        "source_evidence_referenced": result.source_evidence_referenced,
        "source_manifest_verify_rc": result.source_manifest_verify_rc,
        "full_canonical_chain_wired": result.full_canonical_chain_wired,
        "backtest_runtime_decision_parity_pass": result.backtest_runtime_decision_parity_pass,
        "system_economic_evidence_admissible": result.system_economic_evidence_admissible,
        "runtime_rewire_admissible": result.runtime_rewire_admissible,
        "claim_promotion_allowed": result.claim_promotion_allowed,
        "no_runtime_authority_confirmed": result.no_runtime_authority_confirmed,
        "no_economic_claim_confirmed": result.no_economic_claim_confirmed,
        "next_blocker": result.next_blocker,
        "fail_closed_reasons": list(result.fail_closed_reasons),
    }


def render_surface_p_semantic_parity_gap_matrix_json_v0(
    *,
    pr5022_proof_bundle_dir: Path | None = None,
    pr5022_closeout_dir: Path | None = None,
) -> str:
    result = evaluate_surface_p_semantic_parity_gap_assessment_v0(
        pr5022_proof_bundle_dir=pr5022_proof_bundle_dir,
        pr5022_closeout_dir=pr5022_closeout_dir,
    )
    source_refs = collect_source_evidence_refs(
        pr5022_proof_bundle_dir=pr5022_proof_bundle_dir,
        pr5022_closeout_dir=pr5022_closeout_dir,
    )
    payload = {
        **dict(surface_p_semantic_parity_gap_assessment_to_dict_v0(result)),
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


def render_surface_p_semantic_parity_gap_report_markdown_v0(
    *,
    pr5022_proof_bundle_dir: Path | None = None,
    pr5022_closeout_dir: Path | None = None,
) -> str:
    result = evaluate_surface_p_semantic_parity_gap_assessment_v0(
        pr5022_proof_bundle_dir=pr5022_proof_bundle_dir,
        pr5022_closeout_dir=pr5022_closeout_dir,
    )
    lines = [
        "# Surface P Semantic Parity Gap Assessment v0",
        "",
        "MODE=READ_ONLY_NO_RUNTIME_NO_REWIRE",
        "",
        "## Surface P Gap Assessment Status",
        "",
        f"- gap_assessment_parity_status: {result.surface_p_gap_assessment_parity_status}",
        f"- semantic_parity_beyond_trace_binding: {result.semantic_parity_beyond_trace_binding}",
        f"- surface_p_post_status: {result.surface_p_post_status}",
        "",
        "## PARTIAL Reason",
        "",
        result.surface_p_partial_reason,
        "",
        "## Missing Semantic Parity Proof Beyond Trace-Binding",
        "",
    ]
    if result.missing_semantic_parity_proof_beyond_trace_binding:
        lines.extend(
            f"- {item}" for item in result.missing_semantic_parity_proof_beyond_trace_binding
        )
    else:
        lines.append("- NONE")
    lines.extend(
        [
            "",
            "## Offline Semantic Evidence",
            "",
            f"- offline_four_way_fixtures_complete: {str(result.offline_four_way_fixtures_complete).lower()}",
            (
                "- semantic_binding_confirmations_complete: "
                f"{str(result.semantic_binding_confirmations_complete).lower()}"
            ),
            (
                "- pr5022_trace_surface_coverage_complete: "
                f"{str(result.pr5022_trace_surface_coverage_complete).lower()}"
            ),
            (
                "- pr5022_chain_surface_binding_complete: "
                f"{str(result.pr5022_chain_surface_binding_complete).lower()}"
            ),
            f"- source_manifest_verify_rc: {result.source_manifest_verify_rc}",
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
            f"NEXT_BLOCKER={result.next_blocker}",
            "NO_RUNTIME_AUTHORITY_CONFIRMED=true",
            "NO_ECONOMIC_CLAIM_CONFIRMED=true",
        ]
    )
    return "\n".join(lines) + "\n"


def assessment_result_field_names_v0() -> Tuple[str, ...]:
    return tuple(field.name for field in fields(SurfacePSemanticParityGapAssessmentResultV0))
