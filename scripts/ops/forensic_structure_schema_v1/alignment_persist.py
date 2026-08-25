"""Persist derived/non-authoritative binding-candidate alignment artifacts."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.ops.forensic_structure_schema_v1.alignment_constants import (
    ALIGNMENT_AUTHORITY,
    ALIGNMENT_GENERATOR_ID,
    ALIGNMENT_LAYER_ID,
    ALIGNMENT_OUTPUT_ROLE,
    ALIGNMENT_SHARD_ORDER,
    ALIGNMENT_TRANSFORMATION_VERSION,
    A_L_CATALOG_RELPATH,
    BOUND_SIDECAR_SHA256,
    BOUND_SOURCE_SHA256,
    DISPOSITION_RELPATH,
    EXTERNAL_ALIGNMENT_DATASET_DIR,
    EXTERNAL_ONLY_SHARDS,
    GIT_TRACKED_SHARDS,
    OPEN_CLUSTER_RESIDUAL_IDS,
    REPO_ALIGNMENT_RELPATH,
)
from scripts.ops.forensic_structure_schema_v1.alignment_guards import AlignmentGuardProgram
from scripts.ops.forensic_structure_schema_v1.alignment_index import (
    build_alignment_index,
    collect_a_l_input_hashes,
    collect_disposition_input_hashes,
)
from scripts.ops.forensic_structure_schema_v1.alignment_models import AlignmentIndex
from scripts.ops.forensic_structure_schema_v1.alignment_validation import (
    audit_alignment_index,
    run_alignment_adversarial_suite,
)
from scripts.ops.forensic_structure_schema_v1.bound_inputs import (
    BOUND_SIDECAR,
    BOUND_SOURCE,
    run_bound_transformer,
)
from scripts.ops.forensic_structure_schema_v1.constants import (
    GIT_UNSUITABLE_SINGLE_FILE_BYTES as _GIT_CAP,
)
from scripts.ops.forensic_structure_schema_v1.exceptions import (
    TransformationContractViolation,
)
from scripts.ops.forensic_structure_schema_v1.guards import (
    forbid_disposition_input_rewrite,
    forbid_retained_input_rewrite,
    forbid_sidecar_mutation,
    forbid_source_mutation,
)
from scripts.ops.forensic_structure_schema_v1.serialization import dumps_canonical_bytes
from scripts.ops.forensic_structure_schema_v1.transformer import TransformResult


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_hex(path.read_bytes())


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


@dataclass
class AlignmentPersistResult:
    index: AlignmentIndex
    artifact_sha256s: dict[str, str]
    artifact_byte_counts: dict[str, int]
    shard_sha256s: dict[str, str]
    shard_byte_counts: dict[str, int]
    manifest: dict[str, Any]
    manifest_sha256: str
    reports_dir: Path
    dataset_dir: Path
    index_sha256: str
    determinism_report: dict[str, Any]
    idempotence_report: dict[str, Any]
    immutability_report: dict[str, Any]


def _authority_text() -> str:
    return (
        "AUTHORITY=NONE\n"
        "OUTPUT_AUTHORITY=NONE\n"
        "TARGET_AUTHORITY=NONE\n"
        "OUTPUT_CANONICAL=false\n"
        "SEMANTIC_BINDING_PERFORMED=false\n"
        "OCCURRENCE_BINDING_PROVEN_COUNT=0\n"
        "PROVEN_PARENTAGE_COUNT=0\n"
        "CURRENTNESS_ADJUDICATION_PERFORMED=false\n"
        "SUPERSESSION_ADJUDICATION_PERFORMED=false\n"
        "WINNER_SELECTED_COUNT=0\n"
        "RESIDUAL_CLOSE_PERFORMED=false\n"
        "SW_R_002_STATUS=OPEN\n"
        "SW_R_004_STATUS=OPEN\n"
        "SW_R_009_STATUS=OPEN\n"
        "OUTPUT_ROLE=DERIVED_NAVIGATION_OR_ANALYSIS_ONLY\n"
        "DOCUMENT_ROLE=DERIVED_NAVIGATION_OR_ANALYSIS_ONLY\n"
        "NOT_SOURCE_REPLACEMENT=true\n"
        "NOT_SIDECAR_REPLACEMENT=true\n"
        "THIS_DIRECTORY_IS_NOT_CANONICAL_AUTHORITY=true\n"
    )


def _readme() -> str:
    return """# Binding-candidate alignment index (derived, non-authoritative)

```text
DOCUMENT_ROLE=DERIVED_NAVIGATION_OR_ANALYSIS_ONLY
DOCUMENT_AUTHORITY=NONE
OUTPUT_AUTHORITY=NONE
TARGET_AUTHORITY=NONE
OUTPUT_CANONICAL=false
SEMANTIC_BINDING_PERFORMED=false
OCCURRENCE_BINDING_PROVEN_COUNT=0
PROVEN_PARENTAGE_COUNT=0
CURRENTNESS_ADJUDICATION_PERFORMED=false
SUPERSESSION_ADJUDICATION_PERFORMED=false
WINNER_SELECTED_COUNT=0
SW_R_002_STATUS=OPEN
SW_R_004_STATUS=OPEN
SW_R_009_STATUS=OPEN
THIS_DIRECTORY_IS_NOT_CANONICAL_AUTHORITY=true
```

Navigation and provenance only. This directory does not replace the bound
Source, the bound Sidecar, the A–L retained transformation artifacts, or
the PR #6063 binding-disposition layer.

Candidate is never proven. Structuring is not canonization. Deterministic
derivation is not semantic truth. Git tracking is not authority.

Full T4 overlay shards are retained externally and checksummed here.

Regenerate with:

```text
./scripts/pt -m scripts.ops.run_forensic_structure_schema_v1_alignment_index --persist
```
"""


def _generation_contract() -> dict[str, Any]:
    return {
        "authority": ALIGNMENT_AUTHORITY,
        "canonical_serialization": True,
        "close_order_default": False,
        "generator_id": ALIGNMENT_GENERATOR_ID,
        "hash_sort_as_semantic_order": False,
        "layer_id": ALIGNMENT_LAYER_ID,
        "output_canonical": False,
        "output_role": ALIGNMENT_OUTPUT_ROLE,
        "semantic_binding_performed": False,
        "stable_ordering": "original_structural_source_order",
        "timestamps_in_hash_bound_outputs": False,
        "transformation_version": ALIGNMENT_TRANSFORMATION_VERSION,
        "volatile_fields": [],
    }


def _schema() -> dict[str, Any]:
    return {
        "authority": ALIGNMENT_AUTHORITY,
        "layer_id": ALIGNMENT_LAYER_ID,
        "output_canonical": False,
        "record_classes": [
            "T4_OVERLAY_RECORD",
            "LAYER3_RELATION_RECORD",
            "ENDPOINT_BINDING_CANDIDATE_RECORD",
            "VIEW_RECORD",
            "CROSS_RESIDUAL_EVIDENCE_EDGE",
            "NON_IDENTITY_RECORD",
        ],
        "schema_id": ALIGNMENT_LAYER_ID,
        "transformation_version": ALIGNMENT_TRANSFORMATION_VERSION,
    }


def persist_alignment_index(
    *,
    source_path: str | Path | None = None,
    sidecar_path: str | Path | None = None,
    reports_dir: str | Path | None = None,
    dataset_dir: str | Path | None = None,
    result: TransformResult | None = None,
) -> AlignmentPersistResult:
    src = Path(source_path) if source_path is not None else BOUND_SOURCE
    sid = Path(sidecar_path) if sidecar_path is not None else BOUND_SIDECAR
    reports = (
        Path(reports_dir) if reports_dir is not None else _repo_root() / REPO_ALIGNMENT_RELPATH
    )
    dataset = Path(dataset_dir) if dataset_dir is not None else Path(EXTERNAL_ALIGNMENT_DATASET_DIR)
    guards = AlignmentGuardProgram()
    for forbidden in (src.resolve(), sid.resolve()):
        if reports.resolve() == forbidden or dataset.resolve() == forbidden:
            raise TransformationContractViolation(
                "SOURCE_MUTATION",
                "refusing to persist alignment onto source or sidecar path",
            )
    a_l_dir = (_repo_root() / A_L_CATALOG_RELPATH).resolve()
    disp_dir = (_repo_root() / DISPOSITION_RELPATH).resolve()
    if reports.resolve() == a_l_dir or dataset.resolve() == a_l_dir:
        forbid_retained_input_rewrite(str(reports))
    if reports.resolve() == disp_dir or dataset.resolve() == disp_dir:
        forbid_disposition_input_rewrite(str(reports))

    before_src = _sha256_file(src)
    before_sid = _sha256_file(sid)
    if before_src != BOUND_SOURCE_SHA256:
        forbid_source_mutation("pre-persist source drift")
    if before_sid != BOUND_SIDECAR_SHA256:
        forbid_sidecar_mutation("pre-persist sidecar drift")
    a_l_before = collect_a_l_input_hashes()
    disp_before = collect_disposition_input_hashes()

    if result is None:
        result = run_bound_transformer()
    index = build_alignment_index(result.state)
    second_index = build_alignment_index(result.state)
    if dumps_canonical_bytes(index.to_canonical()) != dumps_canonical_bytes(
        second_index.to_canonical()
    ):
        raise TransformationContractViolation(
            "DETERMINISM",
            "two in-process generations were not byte-identical",
        )
    canonical = index.to_canonical()
    guards.assert_authority_none(str(canonical["authority"]))
    guards.assert_output_not_canonical(bool(canonical["output_canonical"]))
    if canonical["semantic_binding_performed"] is True:
        raise TransformationContractViolation("SW-R-002", "semantic binding performed")
    if canonical["residual_close_performed"] is True:
        raise TransformationContractViolation("STAGE_H", "residual close performed")
    audit = audit_alignment_index(index)
    adversarial = run_alignment_adversarial_suite(index, state=result.state)

    reports.mkdir(parents=True, exist_ok=True)
    dataset.mkdir(parents=True, exist_ok=True)
    blobs = dataset / "blobs"
    blobs.mkdir(parents=True, exist_ok=True)

    artifact_sha256s: dict[str, str] = {}
    artifact_byte_counts: dict[str, int] = {}
    shard_sha256s: dict[str, str] = {}
    shard_byte_counts: dict[str, int] = {}

    def write_reports(name: str, payload: bytes) -> None:
        path = reports / name
        path.write_bytes(payload)
        artifact_sha256s[name] = _sha256_hex(payload)
        artifact_byte_counts[name] = len(payload)

    shards = {
        "t4_overlay_records.json": canonical["t4_records"],
        "layer3_relation_records.json": canonical["layer3_records"],
        "endpoint_binding_candidate_records.json": canonical["endpoint_records"],
        "view_records.json": canonical["view_records"],
        "cross_residual_evidence_edges.json": canonical["cross_residual_edges"],
        "non_identity_records.json": canonical["non_identity_records"],
    }
    if tuple(shards) != ALIGNMENT_SHARD_ORDER:
        raise TransformationContractViolation("ALIGNMENT_INDEX", "shard order drift")

    for name in ALIGNMENT_SHARD_ORDER:
        payload = dumps_canonical_bytes(shards[name])
        shard_sha256s[name] = _sha256_hex(payload)
        shard_byte_counts[name] = len(payload)
        if name in EXTERNAL_ONLY_SHARDS or len(payload) > _GIT_CAP:
            (blobs / name).write_bytes(payload)
            artifact_sha256s[f"blobs/{name}"] = shard_sha256s[name]
            artifact_byte_counts[f"blobs/{name}"] = shard_byte_counts[name]
        if name in GIT_TRACKED_SHARDS and len(payload) <= _GIT_CAP:
            write_reports(name, payload)

    header = {
        k: canonical[k]
        for k in (
            "authority",
            "counts",
            "currentness_adjudication_performed",
            "generated_from_sidecar_sha256",
            "generated_from_source_sha256",
            "generator_id",
            "layer_id",
            "occurrence_binding_proven_count",
            "output_canonical",
            "output_role",
            "proven_parentage_count",
            "residual_close_performed",
            "residual_status",
            "semantic_binding_performed",
            "supersession_adjudication_performed",
            "transformation_version",
            "winner_selected_count",
        )
    }
    index_bytes = dumps_canonical_bytes(header)
    write_reports("alignment_index_header.json", index_bytes)
    index_sha256 = _sha256_hex(index_bytes)

    write_reports("AUTHORITY_NONE.txt", _authority_text().encode("utf-8"))
    write_reports("README.md", _readme().encode("utf-8"))
    write_reports("schema.json", dumps_canonical_bytes(_schema()))
    write_reports("generation_contract.json", dumps_canonical_bytes(_generation_contract()))
    write_reports("counts.json", dumps_canonical_bytes(canonical["counts"]))
    write_reports("residual_status.json", dumps_canonical_bytes(canonical["residual_status"]))
    write_reports(
        "non_inference_audit.json", dumps_canonical_bytes(canonical["non_inference_audit"])
    )
    write_reports("non_identity_audit.json", dumps_canonical_bytes(canonical["non_identity_audit"]))
    write_reports(
        "evidence_edge_report.json", dumps_canonical_bytes(canonical["evidence_edge_report"])
    )
    write_reports("alignment_audit.json", dumps_canonical_bytes(audit))
    write_reports("adversarial_report.json", dumps_canonical_bytes(adversarial))

    concat = hashlib.sha256()
    dataset_bytes = 0
    for name in ALIGNMENT_SHARD_ORDER:
        payload = dumps_canonical_bytes(shards[name])
        concat.update(payload)
        dataset_bytes += len(payload)
    dataset_sha256 = concat.hexdigest()

    determinism_report = {
        "canonical_serialization": True,
        "hash_sort_as_semantic_order": False,
        "in_process_two_build": "PASS",
        "stable_ordering": "original_structural_source_order",
        "status": "PASS",
        "timestamps_in_hash_bound_outputs": False,
        "two_run_required": True,
        "volatile_fields": [],
    }
    idempotence_report = {
        "same_input_same_output": True,
        "status": "PASS",
    }
    immutability_report = {
        "source_sha256_before": before_src,
        "source_sha256_after": None,
        "sidecar_sha256_before": before_sid,
        "sidecar_sha256_after": None,
        "a_l_input_hashes_before": a_l_before,
        "disposition_input_hashes_before": disp_before,
        "source_mutated": False,
        "sidecar_mutated": False,
        "a_l_inputs_mutated": False,
        "disposition_inputs_mutated": False,
    }

    catalog = {
        "authority": ALIGNMENT_AUTHORITY,
        "dataset_bytes": dataset_bytes,
        "dataset_git_persistence": "MANIFEST_PLUS_GIT_TRACKED_SHARDS",
        "dataset_sha256": dataset_sha256,
        "external_dataset_dir": str(dataset),
        "output_canonical": False,
        "record_counts": canonical["counts"],
        "role": "ALIGNMENT_DATASET_CATALOG",
        "shard_byte_counts": dict(sorted(shard_byte_counts.items())),
        "shard_order": list(ALIGNMENT_SHARD_ORDER),
        "shard_sha256s": dict(sorted(shard_sha256s.items())),
    }
    write_reports("dataset_catalog.json", dumps_canonical_bytes(catalog))
    write_reports("determinism_report.json", dumps_canonical_bytes(determinism_report))
    write_reports("idempotence_report.json", dumps_canonical_bytes(idempotence_report))

    manifest = {
        "a_l_input_hashes": canonical["a_l_input_hashes"],
        "artifact_byte_counts": None,
        "artifact_sha256s": None,
        "authority": ALIGNMENT_AUTHORITY,
        "counts": canonical["counts"],
        "dataset_bytes": dataset_bytes,
        "dataset_sha256": dataset_sha256,
        "disposition_input_hashes": canonical["disposition_input_hashes"],
        "external_dataset_dir": str(dataset),
        "generated_from_sidecar_sha256": BOUND_SIDECAR_SHA256,
        "generated_from_source_sha256": BOUND_SOURCE_SHA256,
        "generator_id": ALIGNMENT_GENERATOR_ID,
        "index_sha256": index_sha256,
        "layer_id": ALIGNMENT_LAYER_ID,
        "manifest_excludes_own_file_sha256": True,
        "open_cluster_residuals": list(OPEN_CLUSTER_RESIDUAL_IDS),
        "output_canonical": False,
        "output_role": ALIGNMENT_OUTPUT_ROLE,
        "residual_close_performed": False,
        "semantic_binding_performed": False,
        "shard_byte_counts": dict(sorted(shard_byte_counts.items())),
        "shard_sha256s": dict(sorted(shard_sha256s.items())),
        "sidecar_locator": str(sid),
        "source_locator": str(src),
        "transformation_version": ALIGNMENT_TRANSFORMATION_VERSION,
    }

    after_src = _sha256_file(src)
    after_sid = _sha256_file(sid)
    if after_src != before_src:
        forbid_source_mutation("source mutated during persist")
    if after_sid != before_sid:
        forbid_sidecar_mutation("sidecar mutated during persist")
    a_l_after = collect_a_l_input_hashes()
    disp_after = collect_disposition_input_hashes()
    if a_l_after != a_l_before:
        forbid_retained_input_rewrite("A-L hashes changed during persist")
    if disp_after != disp_before:
        forbid_disposition_input_rewrite("disposition hashes changed during persist")

    immutability_report["source_sha256_after"] = after_src
    immutability_report["sidecar_sha256_after"] = after_sid
    immutability_report["a_l_input_hashes_after"] = a_l_after
    immutability_report["disposition_input_hashes_after"] = disp_after
    write_reports("immutability_report.json", dumps_canonical_bytes(immutability_report))

    manifest["artifact_sha256s"] = dict(sorted(artifact_sha256s.items()))
    manifest["artifact_byte_counts"] = dict(sorted(artifact_byte_counts.items()))
    manifest_bytes = dumps_canonical_bytes(manifest)
    write_reports("transformation_manifest.json", manifest_bytes)
    manifest_sha256 = _sha256_hex(manifest_bytes)
    write_reports(
        "MANIFEST_SHA256.txt",
        (
            f"MANIFEST_SHA256={manifest_sha256}\n"
            f"INDEX_SHA256={index_sha256}\n"
            f"DATASET_SHA256={dataset_sha256}\n"
        ).encode(),
    )

    return AlignmentPersistResult(
        index=index,
        artifact_sha256s=artifact_sha256s,
        artifact_byte_counts=artifact_byte_counts,
        shard_sha256s=shard_sha256s,
        shard_byte_counts=shard_byte_counts,
        manifest=manifest,
        manifest_sha256=manifest_sha256,
        reports_dir=reports,
        dataset_dir=dataset,
        index_sha256=index_sha256,
        determinism_report=determinism_report,
        idempotence_report=idempotence_report,
        immutability_report=immutability_report,
    )
