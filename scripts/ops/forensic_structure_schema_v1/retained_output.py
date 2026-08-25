"""Retained derived forensic transformation persist. Authority remains NONE."""

from __future__ import annotations

import hashlib
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.ops.forensic_structure_schema_v1.constants import (
    BOUND_SIDECAR_PATH,
    BOUND_SOURCE_PATH,
    DATASET_SHARD_ORDER,
    DR_RESIDUAL_IDS,
    EXPECTED_LOSSLESSNESS,
    EXPECTED_SIDECAR_SHA256,
    EXPECTED_SOURCE_BYTES,
    EXPECTED_SOURCE_LINES,
    EXPECTED_SOURCE_SHA256,
    EXTERNAL_RETAINED_DATASET_DIR,
    GENERATOR_ID,
    GIT_UNSUITABLE_SINGLE_FILE_BYTES,
    OUTPUT_AUTHORITY,
    OVERLAY_CLASS_ORDER,
    REPO_RETAINED_REPORTS_RELPATH,
    RETAINED_OUTPUT_IS_ADJUDICATED_TRUTH,
    RETAINED_OUTPUT_IS_CANONICAL,
    RETAINED_OUTPUT_IS_MAP_OF_TRUTH,
    RETAINED_OUTPUT_IS_MASTER_RUNBOOK,
    RETAINED_OUTPUT_IS_SOURCE_REPLACEMENT,
    RETAINED_OUTPUT_ROLE,
    RETAINED_TRANSFORMATION_CONTRACT,
    SCHEMA_ID,
    SCHEMA_VERSION,
    STAGE_ORDER,
    SW_RESIDUAL_IDS,
)
from scripts.ops.forensic_structure_schema_v1.exceptions import (
    TransformationContractViolation,
)
from scripts.ops.forensic_structure_schema_v1.output_audit import audit_retained_output
from scripts.ops.forensic_structure_schema_v1.serialization import dumps_canonical_bytes
from scripts.ops.forensic_structure_schema_v1.state import PipelineState
from scripts.ops.forensic_structure_schema_v1.transformer import (
    TransformResult,
    transform_read_only,
)

FORBIDDEN_RESOLVED_TOKEN = "RESOLVED_BY_TRANSFORMATION"
MANIFEST_NON_DETERMINISTIC_FIELDS: tuple[str, ...] = ()
EXECUTION_NON_DETERMINISTIC_FIELDS: tuple[str, ...] = ()


@dataclass(frozen=True)
class InputStat:
    sha256: str
    bytes: int
    lines: int | None
    mtime_ns: int
    mtime_iso: str


@dataclass
class RetainedPersistResult:
    result: TransformResult
    dataset: dict[str, Any]
    dataset_sha256: str
    dataset_bytes: int
    dataset_record_count: int
    dataset_git_persistence: str
    artifact_sha256s: dict[str, str]
    artifact_byte_counts: dict[str, int]
    record_counts: dict[str, int]
    manifest: dict[str, Any]
    manifest_sha256: str
    manifest_semantic_payload_sha256: str
    losslessness_audit: dict[str, Any]
    invariant_report: dict[str, Any]
    residual_register: dict[str, Any]
    traceability_report: dict[str, Any]
    execution_report: dict[str, Any]
    contract_test_report: dict[str, Any]
    non_inference_audit: dict[str, Any]
    reports_dir: Path
    dataset_dir: Path
    source_stat_before: InputStat
    sidecar_stat_before: InputStat
    source_stat_after: InputStat
    sidecar_stat_after: InputStat
    source_mtime_changed_without_byte_change: bool
    sidecar_mtime_changed_without_byte_change: bool


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _stat_input(path: Path, *, count_lines: bool) -> InputStat:
    st = path.stat()
    data = path.read_bytes()
    lines = data.count(b"\n") if count_lines else None
    from datetime import datetime, timezone

    mtime_iso = datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).isoformat()
    return InputStat(
        sha256=_sha256_hex(data),
        bytes=len(data),
        lines=lines,
        mtime_ns=int(st.st_mtime_ns),
        mtime_iso=mtime_iso,
    )


def _git_sha(repo_root: Path, ref: str) -> str:
    return subprocess.check_output(
        ["git", "rev-parse", ref],
        cwd=repo_root,
        text=True,
    ).strip()


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def build_retained_dataset(state: PipelineState) -> dict[str, Any]:
    if not state.output_eligible:
        raise TransformationContractViolation(
            "STAGE_L",
            "refusing retained dataset: output_eligible is false",
        )
    overlay_index = []
    for class_name in ("append_epoch",) + OVERLAY_CLASS_ORDER:
        for rec in state.overlays_by_class[class_name]:
            overlay_index.append(rec.to_index_canonical())
    return {
        "output_role": RETAINED_OUTPUT_ROLE,
        "output_authority": OUTPUT_AUTHORITY,
        "output_is_canonical": RETAINED_OUTPUT_IS_CANONICAL,
        "output_is_source_replacement": RETAINED_OUTPUT_IS_SOURCE_REPLACEMENT,
        "output_is_adjudicated_truth": RETAINED_OUTPUT_IS_ADJUDICATED_TRUTH,
        "output_is_master_runbook": RETAINED_OUTPUT_IS_MASTER_RUNBOOK,
        "output_is_map_of_truth": RETAINED_OUTPUT_IS_MAP_OF_TRUTH,
        "semantic_canonicalization_performed": False,
        "authority_promotion_performed": False,
        "currentness_adjudication_performed": False,
        "pointer_adjudication_performed": False,
        "boundary_adjudication_performed": False,
        "gate_adjudication_performed": False,
        "supersession_adjudication_performed": False,
        "layer1_occurrences": [occ.to_canonical() for occ in state.layer1_ordered],
        "overlay_index": overlay_index,
        "semantic_envelopes": [env.to_canonical() for env in state.envelopes],
        "relation_envelopes": [rel.to_canonical() for rel in state.relations],
        "provenance_registry": [tag.to_canonical() for tag in state.provenance],
    }


def dataset_shards(dataset: dict[str, Any]) -> dict[str, Any]:
    header_keys = (
        "output_role",
        "output_authority",
        "output_is_canonical",
        "output_is_source_replacement",
        "output_is_adjudicated_truth",
        "output_is_master_runbook",
        "output_is_map_of_truth",
        "semantic_canonicalization_performed",
        "authority_promotion_performed",
        "currentness_adjudication_performed",
        "pointer_adjudication_performed",
        "boundary_adjudication_performed",
        "gate_adjudication_performed",
        "supersession_adjudication_performed",
    )
    return {
        "dataset_header.json": {k: dataset[k] for k in header_keys},
        "layer1_occurrences.json": dataset["layer1_occurrences"],
        "overlay_index.json": dataset["overlay_index"],
        "semantic_envelopes.json": dataset["semantic_envelopes"],
        "relation_envelopes.json": dataset["relation_envelopes"],
        "provenance_registry.json": dataset["provenance_registry"],
    }


def dataset_concat_sha256(dataset: dict[str, Any]) -> tuple[str, int]:
    shards = dataset_shards(dataset)
    digest = hashlib.sha256()
    total = 0
    for name in DATASET_SHARD_ORDER:
        payload = dumps_canonical_bytes(shards[name])
        digest.update(payload)
        total += len(payload)
    return digest.hexdigest(), total


def _write_bytes(path: Path, payload: bytes) -> tuple[str, int]:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return _sha256_hex(payload), len(payload)


def _write_json(path: Path, obj: Any) -> tuple[str, int]:
    return _write_bytes(path, dumps_canonical_bytes(obj))


def _preservation_oracles(state: PipelineState, dataset: dict[str, Any]) -> dict[str, str]:
    assert state.losslessness_audit is not None
    counts = state.losslessness_audit.counts
    layer1_ids = [row["occurrence_id"] for row in dataset["layer1_occurrences"]]
    overlay_ids = [row["overlay_id"] for row in dataset["overlay_index"]]
    expected = EXPECTED_LOSSLESSNESS
    oracles = {
        "SOURCE_OCCURRENCE_PRESERVATION": (
            len(layer1_ids) == expected["LAYER1_COUNT"]
            and len(layer1_ids) == len(set(layer1_ids))
            and counts["LAYER1_GAPS"] == 0
            and counts["LAYER1_OVERLAPS"] == 0
        ),
        "OVERLAY_CARDINALITY_PRESERVATION": len(overlay_ids) == len(set(overlay_ids))
        and counts["FENCE_BLOCK_COUNT"] == expected["FENCE_BLOCK_COUNT"],
        "DUPLICATE_PRESERVATION": counts["FENCE_DUPLICATE_GROUPS"]
        == expected["FENCE_DUPLICATE_GROUPS"]
        and counts["H1_CONTINUATION_COUNT"] == expected["H1_CONTINUATION_COUNT"],
        "NULL_PRESERVATION": counts["T5_CLASSIFIED_SOURCE_LINE_NULL_COUNT"]
        == expected["T5_CLASSIFIED_SOURCE_LINE_NULL_COUNT"],
        "ABSENT_PRESERVATION": all(
            rec.overlay_kind.presence == "absent"
            for rec in state.overlays_by_class["t5_multilabel"]
        ),
        "UNKNOWN_PRESERVATION": all(
            env["hash_kind"]["presence"] != "present" or env["hash_kind"]["value"] == "UNKNOWN"
            for env in dataset["semantic_envelopes"]
        ),
        "UNCLASSIFIED_PRESERVATION": all(
            env["epistemic_class"] == "UNCLASSIFIED" for env in dataset["semantic_envelopes"]
        ),
        "SOURCE_ORDER_PRESERVATION": [env["source_order"] for env in dataset["semantic_envelopes"]]
        == sorted(env["source_order"] for env in dataset["semantic_envelopes"]),
    }
    return {key: ("PASS" if ok else "FAIL") for key, ok in oracles.items()}


def _traceability_records(dataset: dict[str, Any], state: PipelineState) -> list[dict[str, Any]]:
    provenance_by_overlay = {
        tag.subject_id: tag.provenance_type
        for tag in state.provenance
        if tag.subject_kind == "overlay"
    }
    records: list[dict[str, Any]] = []
    for env in dataset["semantic_envelopes"]:
        overlay_id = None
        if env["sidecar_overlay_id"]["presence"] == "present":
            overlay_id = env["sidecar_overlay_id"]["value"]
        records.append(
            {
                "output_id": env["transformation_local_id"],
                "output_kind": "semantic_envelope",
                "source_byte_start": env["source_byte_start"],
                "source_byte_end": env["source_byte_end"],
                "source_sha256": env["source_sha256"],
                "layer1_occurrence_id": env["layer1_occurrence_id"],
                "sidecar_overlay_id": env["sidecar_overlay_id"],
                "sidecar_record_class": env["overlay_class"],
                "provenance_type": env["provenance_type"],
                "overlay_provenance_type": (
                    provenance_by_overlay.get(str(overlay_id)) if overlay_id is not None else None
                ),
                "epistemic_class": env["epistemic_class"],
                "authority_status": env["authority_status"],
                "currentness_status": env["currentness_status"],
                "gate_membership": env["gate_membership"],
                "residuals": list(env["residuals"]),
            }
        )
    for rel in dataset["relation_envelopes"]:
        records.append(
            {
                "output_id": rel["transformation_local_id"],
                "output_kind": "relation_envelope",
                "relation_id": rel["relation_id"],
                "original_layer3_relation_id": rel["relation_id"],
                "relation_type": rel["relation_type"],
                "from_binding_kind": rel["from_binding"]["kind"],
                "to_binding_kind": rel["to_binding"]["kind"],
                "from_binding_value": rel["from_binding"]["value"],
                "to_binding_value": rel["to_binding"]["value"],
                "documentary_or_raw_endpoint": (
                    rel["from_binding"]["kind"] == "DOCUMENTARY_STRING_ENDPOINT"
                    or rel["to_binding"]["kind"] == "DOCUMENTARY_STRING_ENDPOINT"
                ),
                "source_occurrence_id": rel["source_occurrence_id"],
                "sidecar_overlay_id": rel["sidecar_overlay_id"],
                "provenance_type": rel["relation_provenance"],
                "epistemic_basis": rel["relation_epistemic_basis"],
                "source_sha256": rel["source_sha256"],
                "source_order": rel["source_order"],
            }
        )
    return records


def _assert_traceability_complete(records: list[dict[str, Any]]) -> None:
    for rec in records:
        if not rec.get("output_id"):
            raise TransformationContractViolation(
                "TRACEABILITY_FAILURE",
                "output unit missing transformation-local id",
            )
        if rec["output_kind"] == "semantic_envelope":
            if rec["source_sha256"] != EXPECTED_SOURCE_SHA256:
                raise TransformationContractViolation(
                    "TRACEABILITY_FAILURE",
                    f"{rec['output_id']} source sha missing or drifted",
                )
            if rec["source_byte_end"] < rec["source_byte_start"]:
                raise TransformationContractViolation(
                    "TRACEABILITY_FAILURE",
                    f"{rec['output_id']} inverted byte range",
                )
        if rec["output_kind"] == "relation_envelope" and not rec.get("relation_id"):
            raise TransformationContractViolation(
                "TRACEABILITY_FAILURE",
                "relation missing relation_id",
            )


def persist_retained_derived(
    *,
    source_path: str | Path = BOUND_SOURCE_PATH,
    sidecar_path: str | Path = BOUND_SIDECAR_PATH,
    reports_dir: str | Path | None = None,
    dataset_dir: str | Path | None = None,
    transformer_git_sha: str | None = None,
    origin_main_sha: str | None = None,
    run_pipeline: bool = True,
    result: TransformResult | None = None,
) -> RetainedPersistResult:
    """Execute (or reuse) the merged transformer and persist derived artifacts."""
    src = Path(source_path)
    sid = Path(sidecar_path)
    repo_root = _repo_root()
    reports = (
        Path(reports_dir) if reports_dir is not None else repo_root / REPO_RETAINED_REPORTS_RELPATH
    )
    data_dir = Path(dataset_dir) if dataset_dir is not None else Path(EXTERNAL_RETAINED_DATASET_DIR)
    for forbidden in (src.resolve(), sid.resolve()):
        for target in (reports.resolve(), data_dir.resolve()):
            if target == forbidden:
                raise TransformationContractViolation(
                    "SOURCE_MUTATION",
                    "refusing to persist onto source or sidecar path",
                )

    source_before = _stat_input(src, count_lines=True)
    sidecar_before = _stat_input(sid, count_lines=False)
    if source_before.sha256 != EXPECTED_SOURCE_SHA256:
        raise TransformationContractViolation(
            "SOURCE_SHA_DRIFT",
            f"source sha {source_before.sha256} != {EXPECTED_SOURCE_SHA256}",
        )
    if sidecar_before.sha256 != EXPECTED_SIDECAR_SHA256:
        raise TransformationContractViolation(
            "SIDECAR_SHA_DRIFT",
            f"sidecar sha {sidecar_before.sha256} != {EXPECTED_SIDECAR_SHA256}",
        )
    if source_before.bytes != EXPECTED_SOURCE_BYTES or source_before.lines != EXPECTED_SOURCE_LINES:
        raise TransformationContractViolation("STAGE_A", "source size/line drift before persist")

    if result is None:
        result = transform_read_only(source_path=src, sidecar_path=sid)
    elif run_pipeline:
        result = transform_read_only(source_path=src, sidecar_path=sid)
    state = result.state
    if not state.output_eligible:
        raise TransformationContractViolation("STAGE_L", "output not eligible")
    for stage in STAGE_ORDER:
        if stage not in state.stages_completed:
            raise TransformationContractViolation("PIPELINE", f"missing stage {stage}")

    dataset = build_retained_dataset(state)
    assert state.losslessness_audit is not None
    assert state.invariant_report is not None
    promotion_flags = audit_retained_output(
        dataset=dataset,
        losslessness_counts=state.losslessness_audit.counts,
    )
    preservation = _preservation_oracles(state, dataset)
    if any(v != "PASS" for v in preservation.values()):
        failed = [k for k, v in preservation.items() if v != "PASS"]
        raise TransformationContractViolation("LOSSLESSNESS_FAILURE", f"{failed}")

    shards = dataset_shards(dataset)
    blob_dir = data_dir / "blobs"
    artifact_sha256s: dict[str, str] = {}
    artifact_byte_counts: dict[str, int] = {}
    dataset_sha256, dataset_bytes = dataset_concat_sha256(dataset)
    largest = 0
    for name in DATASET_SHARD_ORDER:
        payload = dumps_canonical_bytes(shards[name])
        if FORBIDDEN_RESOLVED_TOKEN.encode("utf-8") in payload:
            raise TransformationContractViolation(
                "STAGE_H",
                f"retained shard {name} contains RESOLVED_BY_TRANSFORMATION",
            )
        sha, nbytes = _write_bytes(blob_dir / name, payload)
        artifact_sha256s[f"blobs/{name}"] = sha
        artifact_byte_counts[f"blobs/{name}"] = nbytes
        largest = max(largest, nbytes)
    dataset_git_persistence = (
        "MANIFEST_ONLY"
        if largest >= GIT_UNSUITABLE_SINGLE_FILE_BYTES
        or dataset_bytes >= GIT_UNSUITABLE_SINGLE_FILE_BYTES
        else "FULL"
    )
    if dataset_bytes >= GIT_UNSUITABLE_SINGLE_FILE_BYTES:
        dataset_git_persistence = "MANIFEST_ONLY"

    record_counts = {
        "layer1_occurrences": len(dataset["layer1_occurrences"]),
        "overlay_index": len(dataset["overlay_index"]),
        "semantic_envelopes": len(dataset["semantic_envelopes"]),
        "relation_envelopes": len(dataset["relation_envelopes"]),
        "provenance_registry": len(dataset["provenance_registry"]),
        "residuals": len(state.residuals),
        "contract_tests": len(state.contract_tests),
    }
    dataset_record_count = (
        record_counts["layer1_occurrences"]
        + record_counts["overlay_index"]
        + record_counts["semantic_envelopes"]
        + record_counts["relation_envelopes"]
        + record_counts["provenance_registry"]
    )

    trace_records = _traceability_records(dataset, state)
    _assert_traceability_complete(trace_records)
    trace_bytes = dumps_canonical_bytes(trace_records)
    trace_sha, trace_nbytes = _write_bytes(blob_dir / "traceability_records.json", trace_bytes)
    artifact_sha256s["blobs/traceability_records.json"] = trace_sha
    artifact_byte_counts["blobs/traceability_records.json"] = trace_nbytes
    if trace_nbytes >= GIT_UNSUITABLE_SINGLE_FILE_BYTES:
        dataset_git_persistence = "MANIFEST_ONLY"

    git_sha = transformer_git_sha or _git_sha(repo_root, "HEAD")
    origin_sha = origin_main_sha or _git_sha(repo_root, "origin/main")

    losslessness_audit = {
        "role": "LOSSLESSNESS_AUDIT",
        "authority": "NONE",
        "status": "PASS" if state.losslessness_audit.passed else "FAIL",
        "pipeline": state.losslessness_audit.to_canonical(),
        "preservation_oracles": preservation,
        "layer1_byte_union": [
            state.losslessness_audit.counts["LAYER1_BYTE_UNION_START"],
            state.losslessness_audit.counts["LAYER1_BYTE_UNION_END"],
        ],
    }
    invariant_report = {
        "role": "INVARIANT_REPORT",
        "authority": "NONE",
        "status": "PASS" if state.invariant_report.passed else "FAIL",
        "pipeline": state.invariant_report.to_canonical(),
    }
    residual_register = {
        "role": "RESIDUAL_REGISTER",
        "authority": "NONE",
        "residuals_auto_closed": False,
        "resolved_by_transformation": False,
        "open_sw_residuals": list(SW_RESIDUAL_IDS),
        "open_dr_residuals": list(DR_RESIDUAL_IDS),
        "records": [r.to_canonical() for r in state.residuals],
    }
    if any(r.status != "OPEN" for r in state.residuals):
        raise TransformationContractViolation("STAGE_H", "residual auto-closed")
    traceability_report = {
        "role": "TRACEABILITY_REPORT",
        "authority": "NONE",
        "status": "PASS",
        "record_count": len(trace_records),
        "full_records_locator": "blobs/traceability_records.json",
        "full_records_sha256": trace_sha,
        "full_records_bytes": trace_nbytes,
        "identity_rule": "transformation_local_id_not_content_hash",
        "every_semantic_envelope_has_byte_range_and_source_sha": True,
        "every_relation_has_relation_id_and_typed_bindings": True,
    }
    contract_test_report = {
        "role": "CONTRACT_TEST_REPORT",
        "authority": "NONE",
        "status": "PASS",
        "results": {k: v.to_canonical() for k, v in sorted(state.contract_tests.items())},
    }
    stage_map = {
        name: ("PASS" if name in state.stages_completed else "FAIL") for name in STAGE_ORDER
    }
    non_inference_audit = {
        "role": "NON_INFERENCE_AUDIT",
        "authority": "NONE",
        "status": "PASS",
        "promotions_detected": promotion_flags,
    }
    execution_report = {
        "role": "EXECUTION_REPORT",
        "authority": "NONE",
        "execution_status": "PASS",
        "output_eligible": True,
        "stages": stage_map,
        "stage_l_output_eligible": True,
        "source_locator": BOUND_SOURCE_PATH,
        "sidecar_locator": BOUND_SIDECAR_PATH,
        "declared_reports_relpath": REPO_RETAINED_REPORTS_RELPATH,
        "declared_dataset_dir": EXTERNAL_RETAINED_DATASET_DIR,
        "dataset_git_persistence": dataset_git_persistence,
        "wallclock_seconds_not_in_artifact": True,
        "regeneration_command": (
            "./scripts/pt -m scripts.ops.run_forensic_structure_schema_v1_transformer "
            "--persist-retained-derived"
        ),
    }

    reports.mkdir(parents=True, exist_ok=True)
    authority_text = (
        "OUTPUT_AUTHORITY=NONE\n"
        "TARGET_AUTHORITY=NONE\n"
        "SIDECAR_AUTHORITY=NONE\n"
        "OUTPUT_ROLE=DERIVED_FORENSIC_STRUCTURE\n"
        "OUTPUT_IS_CANONICAL=false\n"
        "OUTPUT_IS_SOURCE_REPLACEMENT=false\n"
        "OUTPUT_IS_ADJUDICATED_TRUTH=false\n"
        "OUTPUT_IS_MASTER_RUNBOOK=false\n"
        "OUTPUT_IS_MAP_OF_TRUTH=false\n"
        "CANONICALIZATION_PERFORMED=false\n"
        "AUTHORITY_PROMOTION_PERFORMED=false\n"
        "THIS_DIRECTORY_IS_NOT_CANONICAL_AUTHORITY=true\n"
    )
    (reports / "AUTHORITY_NONE.txt").write_text(authority_text, encoding="utf-8")
    (data_dir / "AUTHORITY_NONE.txt").write_text(authority_text, encoding="utf-8")

    source_after = _stat_input(src, count_lines=True)
    sidecar_after = _stat_input(sid, count_lines=False)
    if source_after.sha256 != source_before.sha256:
        raise TransformationContractViolation("SOURCE_MUTATION", "source sha changed")
    if sidecar_after.sha256 != sidecar_before.sha256:
        raise TransformationContractViolation("SIDECAR_MUTATION", "sidecar sha changed")

    manifest = {
        "schema_id": SCHEMA_ID,
        "schema_version": SCHEMA_VERSION,
        "generator_id": GENERATOR_ID,
        "transformer_git_sha": git_sha,
        "repo_origin_main_sha_at_execution": origin_sha,
        "source_locator": BOUND_SOURCE_PATH,
        "source_sha256": source_after.sha256,
        "source_bytes": source_after.bytes,
        "source_lines": source_after.lines,
        "sidecar_locator": BOUND_SIDECAR_PATH,
        "sidecar_sha256": sidecar_after.sha256,
        "output_authority": OUTPUT_AUTHORITY,
        "target_authority": OUTPUT_AUTHORITY,
        "sidecar_authority": OUTPUT_AUTHORITY,
        "transformation_contract": RETAINED_TRANSFORMATION_CONTRACT,
        "execution_status": "PASS",
        "output_eligible": True,
        "output_role": RETAINED_OUTPUT_ROLE,
        "output_is_canonical": False,
        "semantic_canonicalization_performed": False,
        "authority_promotion_performed": False,
        "currentness_adjudication_performed": False,
        "pointer_adjudication_performed": False,
        "boundary_adjudication_performed": False,
        "gate_adjudication_performed": False,
        "supersession_adjudication_performed": False,
        "open_residual_ids": list(SW_RESIDUAL_IDS) + list(DR_RESIDUAL_IDS),
        "artifact_sha256s": dict(sorted({**artifact_sha256s}.items())),
        "artifact_byte_counts": dict(sorted(artifact_byte_counts.items())),
        "record_counts": record_counts,
        "dataset_sha256": dataset_sha256,
        "dataset_bytes": dataset_bytes,
        "dataset_record_count": dataset_record_count,
        "dataset_git_persistence": dataset_git_persistence,
        "dataset_sha256_method": "sha256_concat_of_canonical_shards_in_DATASET_SHARD_ORDER",
        "historical_locator_used_as_current_locator": False,
        "residuals_auto_closed": False,
        "resolved_by_transformation": False,
        "non_deterministic_manifest_fields": list(MANIFEST_NON_DETERMINISTIC_FIELDS),
    }
    if "Desktop" in manifest["source_locator"] or "Downloads" in manifest["source_locator"]:
        raise TransformationContractViolation(
            "HISTORICAL_LOCATOR_NORMALIZATION",
            "manifest source_locator is a historical desktop/downloads path",
        )

    report_files = {
        "transformation_manifest.json": manifest,
        "losslessness_audit.json": losslessness_audit,
        "invariant_report.json": invariant_report,
        "residual_register.json": residual_register,
        "traceability_report.json": traceability_report,
        "execution_report.json": execution_report,
        "contract_test_report.json": contract_test_report,
        "non_inference_audit.json": non_inference_audit,
        "dataset_catalog.json": {
            "role": "DATASET_CATALOG",
            "authority": "NONE",
            "dataset_sha256": dataset_sha256,
            "dataset_bytes": dataset_bytes,
            "dataset_git_persistence": dataset_git_persistence,
            "shard_order": list(DATASET_SHARD_ORDER),
            "external_dataset_dir": EXTERNAL_RETAINED_DATASET_DIR,
            "artifact_sha256s": artifact_sha256s,
            "artifact_byte_counts": artifact_byte_counts,
            "record_counts": record_counts,
            "regeneration_command": execution_report["regeneration_command"],
        },
    }
    for name, obj in report_files.items():
        sha, nbytes = _write_json(reports / name, obj)
        artifact_sha256s[name] = sha
        artifact_byte_counts[name] = nbytes
        if name != "transformation_manifest.json":
            sha2, nbytes2 = _write_json(data_dir / name, obj)
            artifact_sha256s[f"external/{name}"] = sha2
            artifact_byte_counts[f"external/{name}"] = nbytes2

    manifest["artifact_sha256s"] = dict(sorted(artifact_sha256s.items()))
    manifest["artifact_byte_counts"] = dict(sorted(artifact_byte_counts.items()))
    manifest_bytes = dumps_canonical_bytes(manifest)
    manifest_sha256, manifest_nbytes = _write_bytes(
        reports / "transformation_manifest.json", manifest_bytes
    )
    _write_bytes(data_dir / "transformation_manifest.json", manifest_bytes)
    artifact_sha256s["transformation_manifest.json"] = manifest_sha256
    artifact_byte_counts["transformation_manifest.json"] = manifest_nbytes
    manifest_semantic_payload_sha256 = manifest_sha256

    authority_sha = _sha256_hex(authority_text.encode("utf-8"))
    artifact_sha256s["AUTHORITY_NONE.txt"] = authority_sha
    artifact_byte_counts["AUTHORITY_NONE.txt"] = len(authority_text.encode("utf-8"))

    return RetainedPersistResult(
        result=result,
        dataset=dataset,
        dataset_sha256=dataset_sha256,
        dataset_bytes=dataset_bytes,
        dataset_record_count=dataset_record_count,
        dataset_git_persistence=dataset_git_persistence,
        artifact_sha256s=artifact_sha256s,
        artifact_byte_counts=artifact_byte_counts,
        record_counts=record_counts,
        manifest=manifest,
        manifest_sha256=manifest_sha256,
        manifest_semantic_payload_sha256=manifest_semantic_payload_sha256,
        losslessness_audit=losslessness_audit,
        invariant_report=invariant_report,
        residual_register=residual_register,
        traceability_report=traceability_report,
        execution_report=execution_report,
        contract_test_report=contract_test_report,
        non_inference_audit=non_inference_audit,
        reports_dir=reports,
        dataset_dir=data_dir,
        source_stat_before=source_before,
        sidecar_stat_before=sidecar_before,
        source_stat_after=source_after,
        sidecar_stat_after=sidecar_after,
        source_mtime_changed_without_byte_change=(
            source_before.mtime_ns != source_after.mtime_ns
            and source_before.sha256 == source_after.sha256
        ),
        sidecar_mtime_changed_without_byte_change=(
            sidecar_before.mtime_ns != sidecar_after.mtime_ns
            and sidecar_before.sha256 == sidecar_after.sha256
        ),
    )


def manifest_semantic_payload(manifest: dict[str, Any]) -> dict[str, Any]:
    excluded = set(MANIFEST_NON_DETERMINISTIC_FIELDS)
    return {k: v for k, v in manifest.items() if k not in excluded}


def execution_semantic_payload(report: dict[str, Any]) -> dict[str, Any]:
    excluded = set(EXECUTION_NON_DETERMINISTIC_FIELDS)
    return {k: v for k, v in report.items() if k not in excluded}
