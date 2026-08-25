"""Persist derived/non-authoritative SW-R-002/004/009 binding-disposition artifacts."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.ops.forensic_structure_schema_v1.bound_inputs import (
    BOUND_SIDECAR,
    BOUND_SOURCE,
    run_bound_transformer,
)
from scripts.ops.forensic_structure_schema_v1.disposition_constants import (
    BOUND_SIDECAR_SHA256,
    BOUND_SOURCE_SHA256,
    DISPOSITION_AUTHORITY,
    DISPOSITION_GENERATOR_ID,
    DISPOSITION_LAYER_ID,
    DISPOSITION_OUTPUT_ROLE,
    DISPOSITION_TRANSFORMATION_VERSION,
    REPO_DISPOSITION_RELPATH,
)
from scripts.ops.forensic_structure_schema_v1.disposition_layer import build_disposition_layer
from scripts.ops.forensic_structure_schema_v1.disposition_models import DispositionLayer
from scripts.ops.forensic_structure_schema_v1.exceptions import (
    TransformationContractViolation,
)
from scripts.ops.forensic_structure_schema_v1.serialization import dumps_canonical_bytes
from scripts.ops.forensic_structure_schema_v1.transformer import TransformResult


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


@dataclass
class DispositionPersistResult:
    layer: DispositionLayer
    artifact_sha256s: dict[str, str]
    artifact_byte_counts: dict[str, int]
    manifest: dict[str, Any]
    manifest_sha256: str
    reports_dir: Path
    layer_sha256: str


def persist_binding_disposition(
    *,
    source_path: str | Path | None = None,
    sidecar_path: str | Path | None = None,
    reports_dir: str | Path | None = None,
    result: TransformResult | None = None,
) -> DispositionPersistResult:
    src = Path(source_path) if source_path is not None else BOUND_SOURCE
    sid = Path(sidecar_path) if sidecar_path is not None else BOUND_SIDECAR
    reports = (
        Path(reports_dir) if reports_dir is not None else _repo_root() / REPO_DISPOSITION_RELPATH
    )
    for forbidden in (src.resolve(), sid.resolve()):
        if reports.resolve() == forbidden:
            raise TransformationContractViolation(
                "SOURCE_MUTATION",
                "refusing to persist disposition onto source or sidecar path",
            )
    if result is None:
        result = run_bound_transformer()
    before_src = hashlib.sha256(src.read_bytes()).hexdigest()
    before_sid = hashlib.sha256(sid.read_bytes()).hexdigest()
    if before_src != BOUND_SOURCE_SHA256 or before_sid != BOUND_SIDECAR_SHA256:
        raise TransformationContractViolation("SOURCE_SHA_DRIFT", "inputs drifted before persist")
    layer = build_disposition_layer(result.state)
    canonical = layer.to_canonical()
    if canonical["authority"] != DISPOSITION_AUTHORITY:
        raise TransformationContractViolation("C9", "disposition authority promoted")
    if canonical["output_canonical"] is True:
        raise TransformationContractViolation("C9", "disposition claimed canonical")
    if canonical["semantic_binding_performed"] is True:
        raise TransformationContractViolation("SW-R-004", "semantic binding performed")
    if canonical["residual_close_performed"] is True:
        raise TransformationContractViolation("STAGE_H", "residual close performed")

    reports.mkdir(parents=True, exist_ok=True)
    authority_text = (
        "AUTHORITY=NONE\n"
        "OUTPUT_AUTHORITY=NONE\n"
        "TARGET_AUTHORITY=NONE\n"
        "OUTPUT_CANONICAL=false\n"
        "SEMANTIC_BINDING_PERFORMED=false\n"
        "RESIDUAL_CLOSE_PERFORMED=false\n"
        "OUTPUT_ROLE=DERIVED_NAVIGATION_OR_ANALYSIS_ONLY\n"
        "DOCUMENT_ROLE=DERIVED_NAVIGATION_OR_ANALYSIS_ONLY\n"
        "NOT_SOURCE_REPLACEMENT=true\n"
        "NOT_SIDECAR_REPLACEMENT=true\n"
        "SW_R_002_STATUS=OPEN\n"
        "SW_R_004_STATUS=OPEN\n"
        "SW_R_009_STATUS=OPEN\n"
        "THIS_DIRECTORY_IS_NOT_CANONICAL_AUTHORITY=true\n"
    )
    artifact_sha256s: dict[str, str] = {}
    artifact_byte_counts: dict[str, int] = {}

    def write(name: str, payload: bytes) -> None:
        path = reports / name
        path.write_bytes(payload)
        artifact_sha256s[name] = _sha256_hex(payload)
        artifact_byte_counts[name] = len(payload)

    write("AUTHORITY_NONE.txt", authority_text.encode("utf-8"))
    write("relation_dispositions.json", dumps_canonical_bytes(canonical["relation_dispositions"]))
    write("endpoint_dispositions.json", dumps_canonical_bytes(canonical["endpoint_dispositions"]))
    write(
        "view_parent_dispositions.json",
        dumps_canonical_bytes(canonical["view_parent_dispositions"]),
    )
    write("counts.json", dumps_canonical_bytes(canonical["counts"]))
    write("orientation.json", dumps_canonical_bytes(canonical["orientation"]))
    write("guard_inventory.json", dumps_canonical_bytes(canonical["guard_inventory"]))
    write("guard_gap_closure.json", dumps_canonical_bytes(canonical["guard_gap_closure"]))
    write("residual_status.json", dumps_canonical_bytes(canonical["residual_status"]))
    layer_bytes = dumps_canonical_bytes(canonical)
    write("disposition_layer.json", layer_bytes)
    layer_sha256 = _sha256_hex(layer_bytes)

    readme = """# Binding disposition layer (derived, non-authoritative)

```text
DOCUMENT_ROLE=DERIVED_NAVIGATION_OR_ANALYSIS_ONLY
DOCUMENT_AUTHORITY=NONE
OUTPUT_AUTHORITY=NONE
TARGET_AUTHORITY=NONE
OUTPUT_CANONICAL=false
SEMANTIC_BINDING_PERFORMED=false
RESIDUAL_CLOSE_PERFORMED=false
SW_R_002_STATUS=OPEN
SW_R_004_STATUS=OPEN
SW_R_009_STATUS=OPEN
THIS_DIRECTORY_IS_NOT_CANONICAL_AUTHORITY=true
```

Navigation and provenance only. This directory does not replace the bound
Source, the bound Sidecar, or the A–L retained transformation artifacts.
Structuring is not canonization. Deterministic derivation is not semantic
truth. Git tracking is not authority.

Regenerate with:

```text
./scripts/pt -m scripts.ops.run_forensic_structure_schema_v1_disposition_layer --persist
```
"""
    write("README.md", readme.encode("utf-8"))

    manifest = {
        "authority": DISPOSITION_AUTHORITY,
        "generated_from_sidecar_sha256": BOUND_SIDECAR_SHA256,
        "generated_from_source_sha256": BOUND_SOURCE_SHA256,
        "generator_id": DISPOSITION_GENERATOR_ID,
        "layer_id": DISPOSITION_LAYER_ID,
        "layer_sha256": layer_sha256,
        "output_canonical": False,
        "output_role": DISPOSITION_OUTPUT_ROLE,
        "residual_close_performed": False,
        "semantic_binding_performed": False,
        "sidecar_locator": str(sid),
        "source_locator": str(src),
        "transformation_version": DISPOSITION_TRANSFORMATION_VERSION,
        "artifact_sha256s": dict(sorted(artifact_sha256s.items())),
        "artifact_byte_counts": dict(sorted(artifact_byte_counts.items())),
        "counts": canonical["counts"],
        "open_cluster_residuals": ["SW-R-002", "SW-R-004", "SW-R-009"],
        "manifest_excludes_own_file_sha256": True,
    }
    manifest_bytes = dumps_canonical_bytes(manifest)
    write("transformation_manifest.json", manifest_bytes)
    manifest_sha256 = _sha256_hex(manifest_bytes)
    write(
        "MANIFEST_SHA256.txt",
        f"MANIFEST_SHA256={manifest_sha256}\nLAYER_SHA256={layer_sha256}\n".encode(),
    )

    after_src = hashlib.sha256(src.read_bytes()).hexdigest()
    after_sid = hashlib.sha256(sid.read_bytes()).hexdigest()
    if after_src != before_src:
        raise TransformationContractViolation("SOURCE_MUTATION", "source mutated during persist")
    if after_sid != before_sid:
        raise TransformationContractViolation("SIDECAR_MUTATION", "sidecar mutated during persist")

    return DispositionPersistResult(
        layer=layer,
        artifact_sha256s=artifact_sha256s,
        artifact_byte_counts=artifact_byte_counts,
        manifest=manifest,
        manifest_sha256=manifest_sha256,
        reports_dir=reports,
        layer_sha256=layer_sha256,
    )
