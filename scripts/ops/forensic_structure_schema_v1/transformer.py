"""Public read-only transformer entry. Never mutates source or sidecar."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.ops.forensic_structure_schema_v1.constants import (
    BOUND_SIDECAR_PATH,
    BOUND_SOURCE_PATH,
    OUTPUT_AUTHORITY,
    OUTPUT_NOT_CANONICAL,
    OUTPUT_NOT_PERSISTED_AS_FORENSIC_TRUTH,
    OUTPUT_NOT_SOURCE_REPLACEMENT,
    OUTPUT_ROLE,
)
from scripts.ops.forensic_structure_schema_v1.exceptions import (
    TransformationContractViolation,
)
from scripts.ops.forensic_structure_schema_v1.pipeline import (
    canonical_test_payload,
    run_pipeline,
)
from scripts.ops.forensic_structure_schema_v1.serialization import dumps_canonical_bytes
from scripts.ops.forensic_structure_schema_v1.state import PipelineState


@dataclass(frozen=True)
class TransformResult:
    state: PipelineState
    payload: dict[str, Any]
    payload_bytes: bytes
    output_eligible: bool
    output_role: str = OUTPUT_ROLE
    output_authority: str = OUTPUT_AUTHORITY
    output_not_canonical: bool = OUTPUT_NOT_CANONICAL


def _assert_not_writing_inputs(
    source_path: Path, sidecar_path: Path, persist_dir: Path | None
) -> None:
    if persist_dir is None:
        return
    persist = persist_dir.resolve()
    for forbidden in (source_path.resolve(), sidecar_path.resolve()):
        if persist == forbidden or persist in forbidden.parents:
            raise TransformationContractViolation(
                "SOURCE_MUTATION",
                "refusing to persist test artifacts onto source or sidecar paths",
            )
        try:
            persist.relative_to(forbidden)
            raise TransformationContractViolation(
                "SOURCE_MUTATION",
                "refusing to persist inside source/sidecar path",
            )
        except ValueError:
            pass


def transform_read_only(
    *,
    source_path: str | Path = BOUND_SOURCE_PATH,
    sidecar_path: str | Path = BOUND_SIDECAR_PATH,
    persist_test_artifact_dir: str | Path | None = None,
) -> TransformResult:
    """Run stages A–L against bound inputs.

    OUTPUT_ROLE=TEST_ARTIFACT_ONLY. Does not replace source, mutate sidecar,
    or create retained forensic truth.
    """
    src = Path(source_path)
    sid = Path(sidecar_path)
    persist = Path(persist_test_artifact_dir) if persist_test_artifact_dir is not None else None
    _assert_not_writing_inputs(src, sid, persist)
    if not OUTPUT_NOT_CANONICAL or not OUTPUT_NOT_SOURCE_REPLACEMENT:
        raise TransformationContractViolation("C9", "output flags corrupted")
    if not OUTPUT_NOT_PERSISTED_AS_FORENSIC_TRUTH:
        raise TransformationContractViolation("C9", "forensic-truth persist flag corrupted")
    state = run_pipeline(src, sid)
    payload = canonical_test_payload(state)
    payload_bytes = dumps_canonical_bytes(payload)
    if persist is not None:
        persist.mkdir(parents=True, exist_ok=True)
        out = persist / "forensic_structure_schema_v1_transformer_test_artifact.json"
        out.write_bytes(payload_bytes)
        meta = persist / "OUTPUT_ROLE.txt"
        meta.write_text(
            "OUTPUT_ROLE=TEST_ARTIFACT_ONLY\n"
            "OUTPUT_AUTHORITY=NONE\n"
            "OUTPUT_NOT_CANONICAL=true\n"
            "OUTPUT_NOT_SOURCE_REPLACEMENT=true\n"
            "OUTPUT_NOT_PERSISTED_AS_FORENSIC_TRUTH=true\n",
            encoding="utf-8",
        )
    return TransformResult(
        state=state,
        payload=payload,
        payload_bytes=payload_bytes,
        output_eligible=state.output_eligible,
    )
