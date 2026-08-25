"""Stage A — Immutable Input Verification."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from scripts.ops.forensic_structure_schema_v1.constants import (
    BOUND_SOURCE_PATH,
    EXPECTED_AUTHORITY,
    EXPECTED_BOM,
    EXPECTED_ENCODING,
    EXPECTED_NEWLINE,
    EXPECTED_SIDECAR_ROLE,
    EXPECTED_SIDECAR_SHA256,
    EXPECTED_SOURCE_BYTES,
    EXPECTED_SOURCE_LINES,
    EXPECTED_SOURCE_SHA256,
    EXPECTED_TRAILING_NEWLINE,
    GENERATOR_ID,
    SCHEMA_ID,
    SCHEMA_VERSION,
)
from scripts.ops.forensic_structure_schema_v1.exceptions import (
    TransformationContractViolation,
)
from scripts.ops.forensic_structure_schema_v1.models import InputWitness
from scripts.ops.forensic_structure_schema_v1.state import PipelineState


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read_immutable(path: Path) -> bytes:
    if path.is_symlink():
        raise TransformationContractViolation(
            "STAGE_A",
            f"refusing to follow symlink input: {path}",
        )
    return path.read_bytes()


def run_stage_a(state: PipelineState) -> None:
    source_sha = sha256_hex(state.source_bytes)
    sidecar_sha = sha256_hex(state.sidecar_bytes)
    if source_sha != EXPECTED_SOURCE_SHA256:
        raise TransformationContractViolation(
            "SOURCE_SHA_DRIFT",
            f"source sha256 {source_sha} != {EXPECTED_SOURCE_SHA256}",
        )
    if sidecar_sha != EXPECTED_SIDECAR_SHA256:
        raise TransformationContractViolation(
            "SIDECAR_SHA_DRIFT",
            f"sidecar sha256 {sidecar_sha} != {EXPECTED_SIDECAR_SHA256}",
        )
    if len(state.source_bytes) != EXPECTED_SOURCE_BYTES:
        raise TransformationContractViolation(
            "STAGE_A",
            f"source bytes {len(state.source_bytes)} != {EXPECTED_SOURCE_BYTES}",
        )
    newline_count = state.source_bytes.count(b"\n")
    if newline_count != EXPECTED_SOURCE_LINES:
        raise TransformationContractViolation(
            "STAGE_A",
            f"source newline count {newline_count} != {EXPECTED_SOURCE_LINES}",
        )
    if not state.source_bytes.endswith(b"\n"):
        raise TransformationContractViolation("STAGE_A", "expected trailing newline")
    if state.source_bytes.startswith(b"\xef\xbb\xbf"):
        raise TransformationContractViolation("STAGE_A", "BOM must be false")

    sidecar = state.sidecar
    for key, expected in (
        ("schema_id", SCHEMA_ID),
        ("schema_version", SCHEMA_VERSION),
        ("generator_id", GENERATOR_ID),
        ("target_authority", EXPECTED_AUTHORITY),
        ("sidecar_authority", EXPECTED_AUTHORITY),
    ):
        observed = sidecar.get(key)
        if observed != expected:
            raise TransformationContractViolation(
                "SCHEMA_OR_GENERATOR_UNEXPECTED_DRIFT",
                f"{key}={observed!r} expected {expected!r}",
            )
    layer0 = sidecar["layer0_blob"]
    if layer0.get("source_sha256") != EXPECTED_SOURCE_SHA256:
        raise TransformationContractViolation("STAGE_A", "layer0 source_sha256 mismatch")
    if layer0.get("source_bytes") != EXPECTED_SOURCE_BYTES:
        raise TransformationContractViolation("STAGE_A", "layer0 source_bytes mismatch")
    if layer0.get("source_line_count") != EXPECTED_SOURCE_LINES:
        raise TransformationContractViolation("STAGE_A", "layer0 source_line_count mismatch")
    if layer0.get("source_locator_at_observation") != BOUND_SOURCE_PATH:
        raise TransformationContractViolation(
            "STAGE_A",
            "layer0 locator is not the bound Documents path",
        )
    if layer0.get("target_authority") != EXPECTED_AUTHORITY:
        raise TransformationContractViolation("C9", "layer0 target_authority != NONE")
    if layer0.get("sidecar_authority") != EXPECTED_AUTHORITY:
        raise TransformationContractViolation("C9", "layer0 sidecar_authority != NONE")
    if layer0.get("bom") != EXPECTED_BOM:
        raise TransformationContractViolation("STAGE_A", "layer0 bom mismatch")
    if layer0.get("encoding") != EXPECTED_ENCODING:
        raise TransformationContractViolation("STAGE_A", "layer0 encoding mismatch")
    if layer0.get("newline") != EXPECTED_NEWLINE:
        raise TransformationContractViolation("STAGE_A", "layer0 newline mismatch")
    if layer0.get("trailing_newline") != EXPECTED_TRAILING_NEWLINE:
        raise TransformationContractViolation("STAGE_A", "layer0 trailing_newline mismatch")
    if layer0.get("generated_from_immutable_source") is not True:
        raise TransformationContractViolation(
            "STAGE_A", "generated_from_immutable_source must be true"
        )
    sidecar_role = sidecar.get("sidecar_role")
    if sidecar_role != EXPECTED_SIDECAR_ROLE:
        raise TransformationContractViolation(
            "STAGE_A",
            f"sidecar_role={sidecar_role!r} expected {EXPECTED_SIDECAR_ROLE!r}",
        )

    state.witness = InputWitness(
        source_path=str(state.source_path),
        sidecar_path=str(state.sidecar_path),
        source_sha256=source_sha,
        sidecar_sha256=sidecar_sha,
        source_bytes=len(state.source_bytes),
        source_line_count=newline_count,
        schema_id=str(sidecar["schema_id"]),
        schema_version=str(sidecar["schema_version"]),
        generator_id=str(sidecar["generator_id"]),
        target_authority=str(sidecar["target_authority"]),
        sidecar_authority=str(sidecar["sidecar_authority"]),
        sidecar_role=str(sidecar_role),
        source_locator_at_observation=str(layer0["source_locator_at_observation"]),
        bom=bool(layer0["bom"]),
        encoding=str(layer0["encoding"]),
        newline=str(layer0["newline"]),
        trailing_newline=bool(layer0["trailing_newline"]),
        generated_from_immutable_source=True,
    )
    state.stages_completed.append("A_IMMUTABLE_INPUT_VERIFICATION")


def load_inputs(source_path: Path, sidecar_path: Path) -> PipelineState:
    source_bytes = _read_immutable(source_path)
    sidecar_bytes = _read_immutable(sidecar_path)
    try:
        sidecar = json.loads(sidecar_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise TransformationContractViolation(
            "STAGE_A",
            f"sidecar is not UTF-8 JSON: {exc}",
        ) from exc
    if not isinstance(sidecar, dict):
        raise TransformationContractViolation("STAGE_A", "sidecar root must be an object")
    return PipelineState(
        source_path=source_path,
        sidecar_path=sidecar_path,
        source_bytes=source_bytes,
        sidecar_bytes=sidecar_bytes,
        sidecar=sidecar,
        source_sha256_before=sha256_hex(source_bytes),
        sidecar_sha256_before=sha256_hex(sidecar_bytes),
    )
