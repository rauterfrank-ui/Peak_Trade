"""Bounded offline runtime evidence binding (no directory scanning)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from scripts.ops.ghv_forensic_whole_system_causal_integration_v1.constants_v1 import (
    CAPTURE_MANIFEST,
    FAILURE_RUNTIME_EVIDENCE,
    FLIGHT_RECORD,
    STAGE_MAPPING_SCHEMA,
)


@dataclass
class RuntimeEvidenceBindingResultV1:
    ok: bool
    failure_semantic: str | None = None
    errors: list[str] = field(default_factory=list)
    gaps: list[dict[str, Any]] = field(default_factory=list)
    proposed_edges: list[dict[str, Any]] = field(default_factory=list)
    binding_status: str = "NOT_PROVEN"


@dataclass(frozen=True)
class RuntimeEvidenceRequestV1:
    evidence_root: Path
    stage_mapping_path: Path
    runtime_context: dict[str, Any]
    code_revision: str
    snapshot_id: str


def _load_stage_mapping(path: Path) -> dict[str, Any]:
    doc = json.loads(path.read_text(encoding="utf-8"))
    if doc.get("schema_version") != STAGE_MAPPING_SCHEMA:
        raise ValueError("stage_mapping_schema_mismatch")
    return doc


def bind_runtime_evidence_v1(
    *,
    request: RuntimeEvidenceRequestV1,
    endpoint_cfi_by_key: dict[tuple[str, str], str],
) -> RuntimeEvidenceBindingResultV1:
    result = RuntimeEvidenceBindingResultV1(ok=False, binding_status="NOT_PROVEN")
    root = request.evidence_root.resolve()
    if not root.is_dir():
        result.failure_semantic = FAILURE_RUNTIME_EVIDENCE
        result.errors.append("evidence_root_not_directory")
        return result

    manifest_path = root / CAPTURE_MANIFEST
    flight_path = root / FLIGHT_RECORD
    if not manifest_path.is_file():
        result.gaps.append(
            {
                "reason": "missing_capture_manifest",
                "RUNTIME_EVIDENCE_BINDING": "NOT_PROVEN",
            }
        )
        result.failure_semantic = FAILURE_RUNTIME_EVIDENCE
        result.errors.append("missing_capture_manifest")
        return result
    if not flight_path.is_file():
        result.gaps.append(
            {"reason": "missing_flight_record", "RUNTIME_EVIDENCE_BINDING": "NOT_PROVEN"}
        )
        result.failure_semantic = FAILURE_RUNTIME_EVIDENCE
        result.errors.append("missing_flight_record")
        return result

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    repo_sha = str(manifest.get("repository_sha") or "")
    if not repo_sha:
        result.failure_semantic = FAILURE_RUNTIME_EVIDENCE
        result.errors.append("manifest_missing_repository_sha")
        return result
    if repo_sha != request.code_revision:
        result.failure_semantic = FAILURE_RUNTIME_EVIDENCE
        result.errors.append("repository_sha_mismatch")
        result.gaps.append(
            {
                "reason": "repository_sha_mismatch",
                "expected": request.code_revision,
                "actual": repo_sha,
                "RUNTIME_EVIDENCE_BINDING": "NOT_PROVEN",
            }
        )
        return result

    ctx = request.runtime_context
    required_ctx = ("run_id", "continuous_run_id", "evidence_contract_id")
    missing_ctx = [k for k in required_ctx if not str(ctx.get(k) or "").strip()]
    if missing_ctx:
        result.failure_semantic = FAILURE_RUNTIME_EVIDENCE
        result.errors.append(f"runtime_context_incomplete:{','.join(missing_ctx)}")
        result.gaps.append(
            {
                "reason": "runtime_context_incomplete",
                "missing": missing_ctx,
                "RUNTIME_EVIDENCE_BINDING": "NOT_PROVEN",
            }
        )
        return result

    manifest_run = str(manifest.get("run_id") or "")
    manifest_cont = str(manifest.get("continuous_run_id") or "")
    if manifest_run and manifest_run != str(ctx["run_id"]):
        result.failure_semantic = FAILURE_RUNTIME_EVIDENCE
        result.errors.append("run_id_context_mismatch")
        return result
    if manifest_cont and manifest_cont != str(ctx["continuous_run_id"]):
        result.failure_semantic = FAILURE_RUNTIME_EVIDENCE
        result.errors.append("continuous_run_id_context_mismatch")
        return result

    contract_id = str(ctx["evidence_contract_id"])
    if (
        str(manifest.get("evidence_contract_id") or "")
        and str(manifest.get("evidence_contract_id")) != contract_id
    ):
        result.failure_semantic = FAILURE_RUNTIME_EVIDENCE
        result.errors.append("evidence_contract_id_mismatch")
        return result

    try:
        mapping_doc = _load_stage_mapping(request.stage_mapping_path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        result.failure_semantic = FAILURE_RUNTIME_EVIDENCE
        result.errors.append(f"stage_mapping_invalid:{exc}")
        return result

    transitions = mapping_doc.get("stage_transitions") or []
    if not isinstance(transitions, list):
        result.failure_semantic = FAILURE_RUNTIME_EVIDENCE
        result.errors.append("stage_transitions_not_list")
        return result

    lines = flight_path.read_text(encoding="utf-8").splitlines()
    records: list[dict[str, Any]] = []
    for idx, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            result.failure_semantic = FAILURE_RUNTIME_EVIDENCE
            result.errors.append(f"malformed_flight_record_line:{idx}")
            return result
        if isinstance(rec, dict):
            records.append(rec)

    seen_stages = {str(r.get("stage") or "") for r in records if r.get("stage")}
    mapped_stages = {str(tr.get("stage") or "") for tr in transitions if isinstance(tr, dict)}
    for stage in sorted(seen_stages):
        if stage and stage not in mapped_stages:
            result.gaps.append(
                {
                    "reason": "missing_stage_to_cfi_mapping",
                    "stage": stage,
                    "RUNTIME_EVIDENCE_BINDING": "NOT_PROVEN",
                }
            )

    for tr in transitions:
        if not isinstance(tr, dict):
            continue
        stage = str(tr.get("stage") or "")
        if stage and stage not in seen_stages:
            result.gaps.append(
                {
                    "reason": "stage_not_present_in_flight_record",
                    "stage": stage,
                    "RUNTIME_EVIDENCE_BINDING": "NOT_PROVEN",
                }
            )
            continue
        src_key = tuple(tr.get("source_endpoint") or [])
        tgt_key = tuple(tr.get("target_endpoint") or [])
        if len(src_key) != 2 or len(tgt_key) != 2:
            result.gaps.append({"reason": "invalid_endpoint_keys", "stage": stage})
            continue
        src_cfi = endpoint_cfi_by_key.get((str(src_key[0]), str(src_key[1])))
        tgt_cfi = endpoint_cfi_by_key.get((str(tgt_key[0]), str(tgt_key[1])))
        if not src_cfi or not tgt_cfi:
            result.gaps.append(
                {
                    "reason": "stage_mapping_endpoint_unresolved",
                    "stage": stage,
                    "RUNTIME_EVIDENCE_BINDING": "NOT_PROVEN",
                }
            )
            continue
        edge_type = str(tr.get("edge_type") or "")
        if not edge_type:
            result.gaps.append({"reason": "missing_edge_type", "stage": stage})
            continue
        temporal: dict[str, Any] = {}
        for key in (
            "cycle_id",
            "epoch_id",
            "state_before",
            "state_after",
            "state_owner",
            "event_id",
            "event_order",
            "persistence_reference",
            "restoration_reference",
            "activation_predicate",
        ):
            if tr.get(key) is not None:
                temporal[key] = tr.get(key)
        if tr.get("requires_state_owner") and not temporal.get("state_owner"):
            result.gaps.append(
                {
                    "reason": "missing_state_owner",
                    "stage": stage,
                    "TEMPORAL_CAUSALITY_PROVEN": False,
                }
            )
            continue
        propagation = bool(tr.get("causal_propagation_allowed"))
        if edge_type == "OBSERVES":
            propagation = False
        result.proposed_edges.append(
            {
                "overlay_edge_id": f"runtime:{stage}:{src_cfi}->{tgt_cfi}",
                "SOURCE_CFI": src_cfi,
                "TARGET_CFI": tgt_cfi,
                "EDGE_TYPE": edge_type,
                "CURRENT_EVIDENCE": tr.get("current_evidence") or f"flight_record_stage:{stage}",
                "PROVENANCE": {
                    "SOURCE_TOOL": "ghv_forensic_whole_system_causal_integration_v1",
                    "SOURCE_ARTIFACT": FLIGHT_RECORD,
                    "CODE_REVISION": request.code_revision,
                    "SNAPSHOT_ID": request.snapshot_id,
                    "RUN_ID": ctx["run_id"],
                    "CONTINUOUS_RUN_ID": ctx["continuous_run_id"],
                    "EVIDENCE_CONTRACT_ID": contract_id,
                    "STAGE": stage,
                },
                "ACTIVATION_CONDITION": tr.get("activation_condition"),
                "PROOF_CLASS": "RUNTIME_OBSERVED",
                "CAUSAL_PROPAGATION_ALLOWED": propagation,
                "temporal": temporal,
            }
        )

    result.ok = True
    if result.proposed_edges and not result.gaps:
        result.binding_status = "PROVEN"
    elif result.proposed_edges:
        result.binding_status = "PARTIAL"
    else:
        result.binding_status = "NOT_PROVEN"
    result.failure_semantic = None
    return result
