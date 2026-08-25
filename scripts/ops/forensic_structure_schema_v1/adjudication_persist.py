"""Persist derived/non-authoritative adjudication-contract artifacts."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.ops.forensic_structure_schema_v1.adjudication_constants import (
    ADJUDICATION_AUTHORITY,
    ADJUDICATION_GENERATOR_ID,
    ADJUDICATION_LAYER_ID,
    ADJUDICATION_OPEN_CLUSTER,
    ADJUDICATION_OUTPUT_ROLE,
    ADJUDICATION_SHARD_ORDER,
    ADJUDICATION_TRANSFORMATION_VERSION,
    ALIGNMENT_INPUT_RELPATH,
    BOUND_SIDECAR_SHA256,
    BOUND_SOURCE_SHA256,
    GIT_TRACKED_SHARDS,
    OPERATOR_AUTHORIZATION_SCOPE,
    REPO_ADJUDICATION_RELPATH,
)
from scripts.ops.forensic_structure_schema_v1.adjudication_evaluator import (
    build_adjudication_contract,
    load_candidate_projection,
)
from scripts.ops.forensic_structure_schema_v1.adjudication_guards import AdjudicationGuardProgram
from scripts.ops.forensic_structure_schema_v1.adjudication_models import AdjudicationContract
from scripts.ops.forensic_structure_schema_v1.adjudication_validation import (
    audit_adjudication_contract,
    run_adjudication_adversarial_suite,
)
from scripts.ops.forensic_structure_schema_v1.bound_inputs import (
    BOUND_SIDECAR,
    BOUND_SOURCE,
    bound_inputs_available,
)
from scripts.ops.forensic_structure_schema_v1.constants import (
    GIT_UNSUITABLE_SINGLE_FILE_BYTES as _GIT_CAP,
)
from scripts.ops.forensic_structure_schema_v1.disposition_constants import (
    REPO_DISPOSITION_RELPATH,
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


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_hex(path.read_bytes())


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


@dataclass
class AdjudicationPersistResult:
    contract: AdjudicationContract
    artifact_sha256s: dict[str, str]
    artifact_byte_counts: dict[str, int]
    shard_sha256s: dict[str, str]
    shard_byte_counts: dict[str, int]
    manifest: dict[str, Any]
    manifest_sha256: str
    reports_dir: Path
    contract_sha256: str
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
        "PROVEN_OCCURRENCE_IDENTITY_COUNT=0\n"
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
    return """# Adjudication contract V1 (derived, non-authoritative)

```text
DOCUMENT_ROLE=DERIVED_NAVIGATION_OR_ANALYSIS_ONLY
DOCUMENT_AUTHORITY=NONE
OUTPUT_AUTHORITY=NONE
TARGET_AUTHORITY=NONE
OUTPUT_CANONICAL=false
SEMANTIC_BINDING_PERFORMED=false
PROVEN_OCCURRENCE_IDENTITY_COUNT=0
PROVEN_PARENTAGE_COUNT=0
CURRENTNESS_ADJUDICATION_PERFORMED=false
SUPERSESSION_ADJUDICATION_PERFORMED=false
WINNER_SELECTED_COUNT=0
SW_R_002_STATUS=OPEN
SW_R_004_STATUS=OPEN
SW_R_009_STATUS=OPEN
THIS_DIRECTORY_IS_NOT_CANONICAL_AUTHORITY=true
```

Derived-only infrastructure for later candidate adjudication. This directory
does not replace the bound Source, the bound Sidecar, the A-L retained
transformation, the PR #6063 disposition layer, or the alignment index.

A better structure does not create authority. Candidate is never proven.
String reuse is not occurrence identity. Git tracking is not authority.

Regenerate with:

```text
./scripts/pt -m scripts.ops.run_forensic_structure_schema_v1_adjudication_contract --persist
```
"""


def _generation_contract() -> dict[str, Any]:
    return {
        "authority": ADJUDICATION_AUTHORITY,
        "canonical_serialization": True,
        "generator_id": ADJUDICATION_GENERATOR_ID,
        "hash_sort_as_semantic_order": False,
        "layer_id": ADJUDICATION_LAYER_ID,
        "operator_authorization_scope": OPERATOR_AUTHORIZATION_SCOPE,
        "output_canonical": False,
        "output_role": ADJUDICATION_OUTPUT_ROLE,
        "positive_occurrence_identity_authorized": False,
        "semantic_binding_performed": False,
        "stable_ordering": "original_structural_source_order",
        "timestamps_in_hash_bound_outputs": False,
        "transformation_version": ADJUDICATION_TRANSFORMATION_VERSION,
        "volatile_fields": [],
    }


def _schema() -> dict[str, Any]:
    return {
        "authority": ADJUDICATION_AUTHORITY,
        "layer_id": ADJUDICATION_LAYER_ID,
        "output_canonical": False,
        "record_classes": [
            "DIMENSION_MODEL_V1",
            "EVIDENCE_RECORD",
            "COMPETING_SET_RECORD",
            "CANDIDATE_ADJUDICATION_RESULT",
            "ADJUDICATION_DECISION_RECORD",
            "NON_INFERENCE_AUDIT_V1",
            "EXECUTION_BOUNDARY_RECORD",
        ],
        "schema_id": ADJUDICATION_LAYER_ID,
        "transformation_version": ADJUDICATION_TRANSFORMATION_VERSION,
    }


def persist_adjudication_contract(
    *,
    reports_dir: str | Path | None = None,
    projection: dict[str, Any] | None = None,
    repo_root: Path | None = None,
) -> AdjudicationPersistResult:
    root = repo_root or _repo_root()
    reports = Path(reports_dir) if reports_dir is not None else root / REPO_ADJUDICATION_RELPATH
    src = BOUND_SOURCE
    sid = BOUND_SIDECAR
    guards = AdjudicationGuardProgram()
    for forbidden in (src.resolve(), sid.resolve()):
        if reports.resolve() == forbidden:
            raise TransformationContractViolation(
                "SOURCE_MUTATION",
                "refusing to persist adjudication onto source or sidecar path",
            )
    align_dir = (root / ALIGNMENT_INPUT_RELPATH).resolve()
    disp_dir = (root / REPO_DISPOSITION_RELPATH).resolve()
    if reports.resolve() == align_dir:
        forbid_retained_input_rewrite(str(reports))
    if reports.resolve() == disp_dir:
        forbid_disposition_input_rewrite(str(reports))

    before_src = None
    before_sid = None
    if bound_inputs_available():
        before_src = _sha256_file(src)
        before_sid = _sha256_file(sid)
        if before_src != BOUND_SOURCE_SHA256:
            forbid_source_mutation("pre-persist source drift")
        if before_sid != BOUND_SIDECAR_SHA256:
            forbid_sidecar_mutation("pre-persist sidecar drift")

    loaded = projection or load_candidate_projection(root)
    first = build_adjudication_contract(loaded, repo_root=root)
    second = build_adjudication_contract(loaded, repo_root=root)
    if dumps_canonical_bytes(first.to_canonical()) != dumps_canonical_bytes(second.to_canonical()):
        raise TransformationContractViolation(
            "DETERMINISM",
            "two in-process generations were not byte-identical",
        )
    canonical = first.to_canonical()
    guards.assert_authority_none(str(canonical["authority"]))
    guards.assert_output_not_canonical(bool(canonical["output_canonical"]))
    if canonical["semantic_binding_performed"] is True:
        raise TransformationContractViolation("SW-R-002", "semantic binding performed")
    if canonical["residual_close_performed"] is True:
        raise TransformationContractViolation("STAGE_H", "residual close performed")
    if canonical["proven_occurrence_identity_count"] != 0:
        guards.assert_no_proven_occurrence(count=1, detail="persist")
    audit = audit_adjudication_contract(first)
    adversarial = run_adjudication_adversarial_suite(first)

    reports.mkdir(parents=True, exist_ok=True)
    artifact_sha256s: dict[str, str] = {}
    artifact_byte_counts: dict[str, int] = {}
    shard_sha256s: dict[str, str] = {}
    shard_byte_counts: dict[str, int] = {}

    def write_reports(name: str, payload: bytes) -> None:
        if len(payload) > _GIT_CAP:
            raise TransformationContractViolation(
                "GIT_UNSUITABLE",
                f"{name} exceeds git cap at {len(payload)} bytes",
            )
        path = reports / name
        path.write_bytes(payload)
        artifact_sha256s[name] = _sha256_hex(payload)
        artifact_byte_counts[name] = len(payload)

    shards = {
        "dimension_model.json": canonical["dimension_model"],
        "evidence_index.json": canonical["evidence_records"],
        "competing_set_graph.json": canonical["competing_sets"],
        "candidate_adjudication_results.json": canonical["candidate_results"],
        "adjudication_decision_records.json": canonical["decision_records"],
        "non_inference_audit.json": canonical["non_inference_audit"],
        "execution_boundaries.json": canonical["execution_boundaries"],
    }
    if tuple(shards) != ADJUDICATION_SHARD_ORDER:
        raise TransformationContractViolation("ADJUDICATION_CONTRACT", "shard order drift")
    for name in ADJUDICATION_SHARD_ORDER:
        payload = dumps_canonical_bytes(shards[name])
        shard_sha256s[name] = _sha256_hex(payload)
        shard_byte_counts[name] = len(payload)
        if name in GIT_TRACKED_SHARDS:
            write_reports(name, payload)

    header = {
        k: canonical[k]
        for k in (
            "authority",
            "contract_version",
            "counts",
            "currentness_adjudication_performed",
            "generated_from_candidate_index_sha256",
            "generated_from_sidecar_sha256",
            "generated_from_source_sha256",
            "generator_id",
            "layer_id",
            "operator_authorization_scope",
            "output_canonical",
            "output_role",
            "proven_occurrence_identity_count",
            "proven_parentage_count",
            "residual_close_performed",
            "residual_status",
            "semantic_binding_performed",
            "supersession_adjudication_performed",
            "transformation_version",
            "winner_selected_count",
        )
    }
    header_bytes = dumps_canonical_bytes(header)
    write_reports("adjudication_contract_header.json", header_bytes)
    contract_sha256 = _sha256_hex(header_bytes)
    write_reports("AUTHORITY_NONE.txt", _authority_text().encode("utf-8"))
    write_reports("README.md", _readme().encode("utf-8"))
    write_reports("schema.json", dumps_canonical_bytes(_schema()))
    write_reports("generation_contract.json", dumps_canonical_bytes(_generation_contract()))
    write_reports("counts.json", dumps_canonical_bytes(canonical["counts"]))
    write_reports("residual_status.json", dumps_canonical_bytes(canonical["residual_status"]))
    write_reports("family_inventory.json", dumps_canonical_bytes(canonical["family_inventory"]))
    write_reports("adjudication_audit.json", dumps_canonical_bytes(audit))
    write_reports("adversarial_report.json", dumps_canonical_bytes(adversarial))

    concat = hashlib.sha256()
    dataset_bytes = 0
    for name in ADJUDICATION_SHARD_ORDER:
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
        "alignment_inputs_mutated": False,
        "sidecar_mutated": False,
        "source_mutated": False,
        "source_sha256_after": before_src,
        "source_sha256_before": before_src,
        "sidecar_sha256_after": before_sid,
        "sidecar_sha256_before": before_sid,
    }
    catalog = {
        "authority": ADJUDICATION_AUTHORITY,
        "dataset_bytes": dataset_bytes,
        "dataset_git_persistence": "GIT_TRACKED_SHARDS",
        "dataset_sha256": dataset_sha256,
        "output_canonical": False,
        "record_counts": canonical["counts"],
        "role": "ADJUDICATION_DATASET_CATALOG",
        "shard_byte_counts": dict(sorted(shard_byte_counts.items())),
        "shard_order": list(ADJUDICATION_SHARD_ORDER),
        "shard_sha256s": dict(sorted(shard_sha256s.items())),
    }
    write_reports("dataset_catalog.json", dumps_canonical_bytes(catalog))
    write_reports("determinism_report.json", dumps_canonical_bytes(determinism_report))
    write_reports("idempotence_report.json", dumps_canonical_bytes(idempotence_report))

    if bound_inputs_available():
        after_src = _sha256_file(src)
        after_sid = _sha256_file(sid)
        guards.assert_source_unmutated(before_src or "", after_src)
        guards.assert_sidecar_unmutated(before_sid or "", after_sid)
        immutability_report["source_sha256_after"] = after_src
        immutability_report["sidecar_sha256_after"] = after_sid
        immutability_report["source_mutated"] = False
        immutability_report["sidecar_mutated"] = False
    write_reports("immutability_report.json", dumps_canonical_bytes(immutability_report))

    manifest = {
        "artifact_byte_counts": dict(sorted(artifact_byte_counts.items())),
        "artifact_sha256s": dict(sorted(artifact_sha256s.items())),
        "authority": ADJUDICATION_AUTHORITY,
        "contract_sha256": contract_sha256,
        "counts": canonical["counts"],
        "dataset_bytes": dataset_bytes,
        "dataset_sha256": dataset_sha256,
        "generated_from_candidate_index_sha256": canonical["generated_from_candidate_index_sha256"],
        "generated_from_sidecar_sha256": BOUND_SIDECAR_SHA256,
        "generated_from_source_sha256": BOUND_SOURCE_SHA256,
        "generator_id": ADJUDICATION_GENERATOR_ID,
        "layer_id": ADJUDICATION_LAYER_ID,
        "manifest_excludes_own_file_sha256": True,
        "open_cluster_residuals": list(ADJUDICATION_OPEN_CLUSTER),
        "operator_authorization_scope": OPERATOR_AUTHORIZATION_SCOPE,
        "output_canonical": False,
        "output_role": ADJUDICATION_OUTPUT_ROLE,
        "proven_occurrence_identity_count": 0,
        "residual_close_performed": False,
        "semantic_binding_performed": False,
        "shard_byte_counts": dict(sorted(shard_byte_counts.items())),
        "shard_sha256s": dict(sorted(shard_sha256s.items())),
        "transformation_version": ADJUDICATION_TRANSFORMATION_VERSION,
    }
    manifest_bytes = dumps_canonical_bytes(manifest)
    write_reports("transformation_manifest.json", manifest_bytes)
    manifest_sha256 = _sha256_hex(manifest_bytes)
    write_reports(
        "MANIFEST_SHA256.txt",
        (
            f"MANIFEST_SHA256={manifest_sha256}\n"
            f"CONTRACT_SHA256={contract_sha256}\n"
            f"DATASET_SHA256={dataset_sha256}\n"
        ).encode(),
    )
    return AdjudicationPersistResult(
        contract=first,
        artifact_sha256s=artifact_sha256s,
        artifact_byte_counts=artifact_byte_counts,
        shard_sha256s=shard_sha256s,
        shard_byte_counts=shard_byte_counts,
        manifest=manifest,
        manifest_sha256=manifest_sha256,
        reports_dir=reports,
        contract_sha256=contract_sha256,
        determinism_report=determinism_report,
        idempotence_report=idempotence_report,
        immutability_report=immutability_report,
    )
