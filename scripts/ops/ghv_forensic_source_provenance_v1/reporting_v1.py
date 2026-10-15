"""Build forensic source provenance report from crosswalk outputs (R1-B caller reporting)."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from scripts.ops.ghv_forensic_source_provenance_v1.proof_eligibility_v1 import (
    evaluate_proof_eligibility_v1,
)
from scripts.ops.ghv_forensic_source_provenance_v1.provenance_contract_v1 import (
    ForensicSourceProvenanceRecordV1,
    SCHEMA_VERSION,
    SourceDirtyStatus,
    SourceProvenanceKind,
    SourceValidationMode,
    classify_dirty_status,
    classify_test_execution,
    infer_source_provenance_kind,
    resolve_declared_current_sha,
)

REPORT_SCHEMA = "forensic_source_provenance_report.v1"


def _load_composed_graph(output_dir: Path) -> dict[str, Any]:
    path = output_dir / "composed_forensic_graph.v1.json"
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _graph_mode_from_composed(composed: dict[str, Any]) -> SourceValidationMode:
    mode = composed.get("GRAPH_MODE") or composed.get("graph_mode")
    if mode == "NAVIGATION_ONLY":
        return SourceValidationMode.NAVIGATION_ONLY
    if mode == "STRICT_CURRENT":
        return SourceValidationMode.STRICT_CURRENT
    return SourceValidationMode.UNKNOWN


def _resolve_ghv_source_sha(
    *,
    composed: dict[str, Any],
    coverage: dict[str, Any],
    actual_source_sha: str | None,
    evidence_root: Path | None,
) -> tuple[str | None, bool | None, str | None]:
    ghv_attached = coverage.get("ghv_evidence_attached")
    evidence_sha: str | None = None
    if (
        evidence_root
        and (evidence_root / "ghv_pre_external_runtime_capture_manifest_v1.json").is_file()
    ):
        manifest = json.loads(
            (evidence_root / "ghv_pre_external_runtime_capture_manifest_v1.json").read_text(
                encoding="utf-8"
            )
        )
        evidence_sha = str(manifest.get("repository_sha") or "") or None
    if evidence_sha:
        return evidence_sha, True if ghv_attached else False, evidence_sha
    if actual_source_sha:
        return actual_source_sha, False if ghv_attached is None else bool(ghv_attached), None
    return None, ghv_attached if ghv_attached is not None else None, None


def build_forensic_source_provenance_report_v1(
    *,
    repo_root: Path,
    output_dir: Path,
    declared_current_sha: str | None,
    test_execution_sha: str | None,
    coverage: dict[str, Any],
    crosswalk_ok: bool,
    evidence_root: Path | None = None,
    workspace_read_declared_pin: bool = False,
    implementation_source_sha: str | None = None,
) -> dict[str, Any]:
    composed = _load_composed_graph(output_dir)
    code_snap = composed.get("code_snapshot") or {}
    actual_source_sha = code_snap.get("git_head") or None
    declared = resolve_declared_current_sha(
        repo_root=repo_root,
        declared_current_sha=declared_current_sha,
    )
    dirty_status = classify_dirty_status(code_snap.get("dirty_fingerprint"))
    validation_mode = _graph_mode_from_composed(composed)
    if validation_mode == SourceValidationMode.UNKNOWN:
        gm = coverage.get("GRAPH_MODE")
        if gm == "NAVIGATION_ONLY":
            validation_mode = SourceValidationMode.NAVIGATION_ONLY
        elif gm == "STRICT_CURRENT":
            validation_mode = SourceValidationMode.STRICT_CURRENT

    ghv_source_sha, ghv_attached, evidence_repository_sha = _resolve_ghv_source_sha(
        composed=composed,
        coverage=coverage,
        actual_source_sha=actual_source_sha,
        evidence_root=evidence_root,
    )

    current_graph_verified = composed.get("CURRENT_GRAPH_VERIFIED")
    if current_graph_verified is None:
        current_graph_verified = coverage.get("CURRENT_GRAPH_VERIFIED")
    snapshot_binding_verified = composed.get("SNAPSHOT_BINDING_VERIFIED")
    if snapshot_binding_verified is None:
        snapshot_binding_verified = coverage.get("SNAPSHOT_BINDING_VERIFIED")

    source_validation_pass_reported = coverage.get("SOURCE_VALIDATION_PASS")
    if source_validation_pass_reported is None:
        source_validation_pass_reported = composed.get("SOURCE_VALIDATION_PASS")
    source_validation_pass_composed_field = composed.get("source_validation_pass")

    if test_execution_sha is None:
        test_execution_sha = os.environ.get("PEAK_TRADE_TEST_EXECUTION_SHA") or None
    if test_execution_sha is None and implementation_source_sha:
        test_execution_sha = implementation_source_sha

    eligibility = evaluate_proof_eligibility_v1(
        declared_current_sha=declared,
        actual_source_sha=actual_source_sha,
        ghv_source_sha=ghv_source_sha,
        test_execution_sha=test_execution_sha,
        source_dirty_status=dirty_status,
        source_validation_mode=validation_mode,
        current_graph_verified=current_graph_verified,
        snapshot_binding_verified=snapshot_binding_verified,
        source_validation_pass_reported=source_validation_pass_reported,
        source_validation_pass_composed_field=source_validation_pass_composed_field,
        crosswalk_execution_success=coverage.get("CROSSWALK_EXECUTION_SUCCESS"),
        ghv_evidence_attached=ghv_attached,
        evidence_repository_sha=evidence_repository_sha,
        workspace_read_declared_pin=workspace_read_declared_pin,
    )

    provenance_kind = infer_source_provenance_kind(
        repo_root=repo_root,
        declared_current_sha=declared,
        actual_source_sha=actual_source_sha,
        source_dirty_status=dirty_status,
        snapshot_binding_verified=bool(snapshot_binding_verified),
    )

    test_class = classify_test_execution(
        test_execution_sha=test_execution_sha,
        declared_current_sha=declared,
        actual_source_sha=actual_source_sha,
        source_dirty_status=dirty_status,
        invoked_via_pytest=False,
    )

    record = ForensicSourceProvenanceRecordV1(
        schema_version=SCHEMA_VERSION,
        declared_current_sha=declared,
        actual_source_sha=actual_source_sha,
        ghv_source_sha=ghv_source_sha,
        test_execution_sha=test_execution_sha,
        snapshot_id=composed.get("snapshot_id") or coverage.get("snapshot_id"),
        source_provenance=provenance_kind.value,
        proof_eligibility=eligibility.proof_eligibility,
        source_tree_identity=code_snap.get("worktree_identity"),
        source_dirty_status=dirty_status.value,
        source_validation_mode=validation_mode.value,
        proof_eligibility_reasons=eligibility.reasons,
        test_execution_class=test_class.value,
        source_repository_path=code_snap.get("repository_path"),
        current_graph_verified=current_graph_verified,
        snapshot_binding_verified=snapshot_binding_verified,
        source_validation_pass_reported=source_validation_pass_reported,
        source_validation_pass_composed_field=source_validation_pass_composed_field,
        runtime_correlation_proven=False,
        global_causal_closure_proven=bool(coverage.get("CAUSAL_CLOSURE_PROVEN")),
        global_non_interference_proven=bool(coverage.get("GLOBAL_NON_INTERFERENCE_PROVEN")),
    )

    return {
        "schema_version": REPORT_SCHEMA,
        "authority": "NONE",
        "IMPLEMENTATION_SOURCE_SHA": implementation_source_sha or "UNKNOWN",
        "crosswalk_cli_ok": crosswalk_ok,
        "record": record.to_dict(),
        "interpretation": {
            "CLI_RESULT_OK_IS_NOT_PROOF_ELIGIBILITY": True,
            "NAVIGATION_ONLY_PASS_IS_NOT_CURRENT_PROOF": True,
            "SOURCE_VALIDATION_PASS_COMPOSED_FIELD_IS_NOT_SNAPSHOT_BINDING": True,
            "composed_source_validation_pass_literal_true_is_ambiguous_without_CURRENT_GRAPH_VERIFIED": True,
        },
        "p05_adjudication": _p05_adjudication(
            source_validation_pass_composed_field=source_validation_pass_composed_field,
            source_validation_pass_reported=source_validation_pass_reported,
            current_graph_verified=current_graph_verified,
        ),
    }


def _p05_adjudication(
    *,
    source_validation_pass_composed_field: Any,
    source_validation_pass_reported: Any,
    current_graph_verified: Any,
) -> dict[str, Any]:
    return {
        "finding": "P05_SOURCE_VALIDATION_PASS_SEMANTICS",
        "composed_graph_literal_source_validation_pass": source_validation_pass_composed_field,
        "coverage_SOURCE_VALIDATION_PASS": source_validation_pass_reported,
        "CURRENT_GRAPH_VERIFIED": current_graph_verified,
        "eligible_current_proof_requires": [
            "CURRENT_GRAPH_VERIFIED=true",
            "SNAPSHOT_BINDING_VERIFIED=true",
            "SOURCE_VALIDATION_PASS reported true under STRICT_CURRENT",
            "not NAVIGATION_ONLY",
        ],
        "ghv_core_changed": False,
    }


def write_forensic_source_provenance_report_v1(
    *,
    repo_root: Path,
    output_dir: Path,
    report: dict[str, Any],
) -> Path:
    path = output_dir / "forensic_source_provenance_report.v1.json"
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path
