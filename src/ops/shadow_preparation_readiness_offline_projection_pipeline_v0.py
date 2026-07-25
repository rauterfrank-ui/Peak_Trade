"""Shadow Preparation Readiness offline projection pipeline v0.

Composes the canonical readiness gate, durable projection writer, and
reader/verifier into one offline, fail-closed orchestration entrypoint.

Non-activating. No Shadow/Paper/Testnet/Runtime/Scheduler/Orders/Live side effects.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Mapping

from src.ops.shadow_preparation_readiness_gate_v0 import (
    DEFAULT_PROJECTION_OUTPUT_RELATIVE_PATH,
    PROJECTION_OUTPUT_PATH_CONFIG_KEY,
    PROJECTION_OVERALL_STATUS_VERIFIED,
    PROJECTION_SCHEMA_ID,
    PROJECTION_SCHEMA_VERSION,
    ShadowPreparationReadinessGateError,
    ShadowPreparationReadinessGateResultV0,
    ShadowPreparationReadinessProjectionVerificationResultV0,
    ShadowPreparationReadinessProjectionWriteMetadataV0,
    evaluate_shadow_preparation_readiness_gate_v0,
    load_shadow_preparation_readiness_gate_config_v0,
    verify_shadow_preparation_readiness_projection_v0,
    write_shadow_preparation_readiness_projection_v0,
)

PACKAGE_MARKER = "SHADOW_PREPARATION_READINESS_OFFLINE_PROJECTION_PIPELINE_V0=true"
PRODUCER_FAMILY = "ops.shadow_preparation_readiness_offline_projection_pipeline_v0"
SCHEMA_ID = PRODUCER_FAMILY
SCHEMA_VERSION = "v0"

PIPELINE_STATUS_PASS: Literal["PIPELINE_PASS"] = "PIPELINE_PASS"
PIPELINE_STATUS_BLOCKED: Literal["PIPELINE_BLOCKED"] = "PIPELINE_BLOCKED"
PIPELINE_STATUS_ERROR: Literal["PIPELINE_ERROR"] = "PIPELINE_ERROR"

READINESS_STATUS_READY: Literal["READY"] = "READY"
READINESS_STATUS_BLOCKED: Literal["BLOCKED"] = "BLOCKED"

PipelineStatusV0 = Literal["PIPELINE_PASS", "PIPELINE_BLOCKED", "PIPELINE_ERROR"]
ReadinessStatusV0 = Literal["READY", "BLOCKED"]


@dataclass(frozen=True)
class ShadowPreparationReadinessOfflineProjectionPipelineResultV0:
    """Machine-readable fail-closed outcome for one offline pipeline invocation."""

    pipeline_status: PipelineStatusV0
    readiness_status: ReadinessStatusV0 | None
    evaluated_at: str | None
    projection_path: str | None
    projection_schema_id: str | None
    projection_schema_version: str | None
    projection_sha256: str | None
    verification_status: Literal["VERIFIED", "BLOCKED"] | None
    verification_verified: bool | None
    reason_codes: tuple[str, ...]
    evidence_reference_count: int | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_id": SCHEMA_ID,
            "schema_version": SCHEMA_VERSION,
            "pipeline_status": self.pipeline_status,
            "readiness_status": self.readiness_status,
            "evaluated_at": self.evaluated_at,
            "projection_path": self.projection_path,
            "projection_schema_id": self.projection_schema_id,
            "projection_schema_version": self.projection_schema_version,
            "projection_sha256": self.projection_sha256,
            "verification_status": self.verification_status,
            "verification_verified": self.verification_verified,
            "reason_codes": list(self.reason_codes),
            "evidence_reference_count": self.evidence_reference_count,
            "authority_effect": "NONE",
            "activation_authority": False,
            "projection_only": True,
        }


def _error_result(
    *,
    reason_codes: tuple[str, ...],
    readiness_status: ReadinessStatusV0 | None = None,
    evaluated_at: str | None = None,
    projection_path: str | None = None,
    projection_schema_id: str | None = None,
    projection_schema_version: str | None = None,
    projection_sha256: str | None = None,
    verification_status: Literal["VERIFIED", "BLOCKED"] | None = None,
    verification_verified: bool | None = None,
    evidence_reference_count: int | None = None,
) -> ShadowPreparationReadinessOfflineProjectionPipelineResultV0:
    return ShadowPreparationReadinessOfflineProjectionPipelineResultV0(
        pipeline_status=PIPELINE_STATUS_ERROR,
        readiness_status=readiness_status,
        evaluated_at=evaluated_at,
        projection_path=projection_path,
        projection_schema_id=projection_schema_id,
        projection_schema_version=projection_schema_version,
        projection_sha256=projection_sha256,
        verification_status=verification_status,
        verification_verified=verification_verified,
        reason_codes=reason_codes,
        evidence_reference_count=evidence_reference_count,
    )


def _classify_readiness_status(
    evaluation: ShadowPreparationReadinessGateResultV0,
) -> ReadinessStatusV0:
    if (
        evaluation.shadow_preparation_complete
        and not evaluation.blockers
        and not evaluation.unmet_gates
    ):
        return READINESS_STATUS_READY
    return READINESS_STATUS_BLOCKED


def _resolve_pipeline_output_path(
    *,
    repo_root: Path,
    output_path: str | None,
    config: Mapping[str, Any] | None,
    config_path: Path | None,
) -> str:
    if output_path is not None:
        if not isinstance(output_path, str) or not output_path.strip():
            raise ShadowPreparationReadinessGateError("PIPELINE_OUTPUT_PATH_EMPTY")
        return output_path.strip()
    cfg = (
        dict(config)
        if config is not None
        else load_shadow_preparation_readiness_gate_config_v0(config_path, repo_root=repo_root)
    )
    raw = cfg.get(PROJECTION_OUTPUT_PATH_CONFIG_KEY)
    if not isinstance(raw, str) or not raw.strip():
        raise ShadowPreparationReadinessGateError("PIPELINE_OUTPUT_PATH_UNCONFIGURED")
    return raw.strip()


def _read_projection_payload(*, repo_root: Path, projection_path: str) -> dict[str, Any]:
    destination = (repo_root / projection_path).resolve()
    try:
        destination.relative_to(repo_root.resolve())
    except ValueError as exc:
        raise ShadowPreparationReadinessGateError("PIPELINE_PROJECTION_PATH_OUTSIDE_REPO") from exc
    try:
        raw = destination.read_bytes()
    except OSError as exc:
        raise ShadowPreparationReadinessGateError(f"PIPELINE_PROJECTION_READ_FAILED:{exc}") from exc
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ShadowPreparationReadinessGateError("PIPELINE_PROJECTION_INVALID_JSON") from exc
    if not isinstance(payload, dict):
        raise ShadowPreparationReadinessGateError("PIPELINE_PROJECTION_INVALID_JSON")
    return payload


def _assert_exact_semantic_consistency(
    *,
    evaluation: ShadowPreparationReadinessGateResultV0,
    write_meta: ShadowPreparationReadinessProjectionWriteMetadataV0,
    verification: ShadowPreparationReadinessProjectionVerificationResultV0,
    payload: Mapping[str, Any],
) -> tuple[str, ...]:
    """Return reason codes when evaluated result and reread projection diverge."""
    reasons: list[str] = []
    if write_meta.schema_id != PROJECTION_SCHEMA_ID:
        reasons.append("PROJECTION_SCHEMA_IDENTITY_MISMATCH")
    if write_meta.schema_version != PROJECTION_SCHEMA_VERSION:
        reasons.append("PROJECTION_SCHEMA_VERSION_MISMATCH")
    if payload.get("schema_id") != PROJECTION_SCHEMA_ID:
        reasons.append("SCHEMA_MISMATCH")
    if payload.get("schema_version") != PROJECTION_SCHEMA_VERSION:
        reasons.append("SCHEMA_MISMATCH")
    if payload.get("evaluation_schema_id") != evaluation.schema_id:
        reasons.append("PROVENANCE_MISMATCH")
    if payload.get("evaluation_schema_version") != evaluation.schema_version:
        reasons.append("PROVENANCE_MISMATCH")
    if payload.get("evaluated_at") != evaluation.evaluated_at:
        reasons.append("PROVENANCE_MISMATCH")
    projected_evaluation = payload.get("evaluation")
    if not isinstance(projected_evaluation, Mapping):
        reasons.append("EVALUATED_PROJECTION_IDENTITY_MISMATCH")
    else:
        # Normalize via the same JSON contract the writer uses (tuples→lists).
        expected = json.loads(json.dumps(evaluation.to_dict(), ensure_ascii=False))
        if dict(projected_evaluation) != expected:
            reasons.append("EVALUATED_PROJECTION_IDENTITY_MISMATCH")
        projected_complete = projected_evaluation.get("shadow_preparation_complete")
        if projected_complete != evaluation.shadow_preparation_complete:
            reasons.append("EVALUATED_PROJECTION_STATUS_MISMATCH")
        projected_blockers = projected_evaluation.get("blockers")
        if list(projected_blockers or ()) != list(evaluation.blockers):
            reasons.append("EVALUATED_PROJECTION_STATUS_MISMATCH")
    if list(payload.get("blockers") or ()) != list(evaluation.blockers):
        reasons.append("EVALUATED_PROJECTION_STATUS_MISMATCH")
    if payload.get("shadow_preparation_complete") != evaluation.shadow_preparation_complete:
        reasons.append("EVALUATED_PROJECTION_STATUS_MISMATCH")
    if verification.projection_path != write_meta.output_path:
        reasons.append("PROJECTION_PATH_REFERENCE_MISMATCH")
    if verification.generated_at != evaluation.evaluated_at:
        reasons.append("PROVENANCE_MISMATCH")
    if verification.schema_id != write_meta.schema_id:
        reasons.append("PROJECTION_SCHEMA_IDENTITY_MISMATCH")
    if verification.schema_version != write_meta.schema_version:
        reasons.append("PROJECTION_SCHEMA_VERSION_MISMATCH")
    # Preserve order, drop duplicates.
    deduped: list[str] = []
    for code in reasons:
        if code not in deduped:
            deduped.append(code)
    return tuple(deduped)


def run_shadow_preparation_readiness_offline_projection_pipeline_v0(
    *,
    repo_root: Path,
    output_path: str | None = None,
    config: Mapping[str, Any] | None = None,
    config_path: Path | None = None,
    evaluated_at: str | None = None,
    as_of: str | None = None,
) -> ShadowPreparationReadinessOfflineProjectionPipelineResultV0:
    """Evaluate once, write, read/verify, and prove exact semantic consistency.

    Offline operator/CI utility only. Does not activate Shadow, Paper, Testnet,
    Runtime, Scheduler, Orders, or Live.
    """
    root = repo_root.resolve()

    try:
        resolved_output = _resolve_pipeline_output_path(
            repo_root=root,
            output_path=output_path,
            config=config,
            config_path=config_path,
        )
    except ShadowPreparationReadinessGateError as exc:
        return _error_result(reason_codes=(f"PIPELINE_INPUT_INVALID:{exc}",))

    try:
        evaluation = evaluate_shadow_preparation_readiness_gate_v0(
            config=config,
            config_path=config_path,
            repo_root=root,
            evaluated_at=evaluated_at,
        )
    except ShadowPreparationReadinessGateError as exc:
        return _error_result(reason_codes=(f"GATE_EVALUATION_FAILED:{exc}",))
    except Exception as exc:  # pragma: no cover - defensive fail-closed
        return _error_result(reason_codes=(f"GATE_EVALUATION_FAILED:{type(exc).__name__}:{exc}",))

    readiness_status = _classify_readiness_status(evaluation)
    evaluated_at_value = evaluation.evaluated_at

    try:
        write_meta = write_shadow_preparation_readiness_projection_v0(
            evaluation=evaluation,
            repo_root=root,
            output_path=resolved_output,
            evaluated_at=evaluated_at_value,
        )
    except ShadowPreparationReadinessGateError as exc:
        return _error_result(
            reason_codes=(f"PROJECTION_WRITE_FAILED:{exc}",),
            readiness_status=readiness_status,
            evaluated_at=evaluated_at_value,
            projection_path=resolved_output,
        )
    except Exception as exc:  # pragma: no cover - defensive fail-closed
        return _error_result(
            reason_codes=(f"PROJECTION_WRITE_FAILED:{type(exc).__name__}:{exc}",),
            readiness_status=readiness_status,
            evaluated_at=evaluated_at_value,
            projection_path=resolved_output,
        )

    verify_as_of = as_of if as_of is not None else evaluated_at_value
    try:
        verification = verify_shadow_preparation_readiness_projection_v0(
            repo_root=root,
            projection_path=write_meta.output_path,
            config=config,
            config_path=config_path,
            as_of=verify_as_of,
            expected_sha256=write_meta.sha256,
        )
    except Exception as exc:  # pragma: no cover - defensive fail-closed
        return _error_result(
            reason_codes=(f"PROJECTION_VERIFY_FAILED:{type(exc).__name__}:{exc}",),
            readiness_status=readiness_status,
            evaluated_at=evaluated_at_value,
            projection_path=write_meta.output_path,
            projection_schema_id=write_meta.schema_id,
            projection_schema_version=write_meta.schema_version,
            projection_sha256=write_meta.sha256,
        )

    if (
        not verification.verified
        or verification.overall_status != PROJECTION_OVERALL_STATUS_VERIFIED
    ):
        codes = tuple(verification.reason_codes) or ("PROJECTION_VERIFICATION_BLOCKED",)
        return _error_result(
            reason_codes=codes,
            readiness_status=readiness_status,
            evaluated_at=evaluated_at_value,
            projection_path=write_meta.output_path,
            projection_schema_id=write_meta.schema_id,
            projection_schema_version=write_meta.schema_version,
            projection_sha256=write_meta.sha256,
            verification_status=verification.overall_status,
            verification_verified=verification.verified,
            evidence_reference_count=verification.evidence_reference_count,
        )

    try:
        payload = _read_projection_payload(
            repo_root=root,
            projection_path=write_meta.output_path,
        )
    except ShadowPreparationReadinessGateError as exc:
        return _error_result(
            reason_codes=(f"PROJECTION_READ_FAILED:{exc}",),
            readiness_status=readiness_status,
            evaluated_at=evaluated_at_value,
            projection_path=write_meta.output_path,
            projection_schema_id=write_meta.schema_id,
            projection_schema_version=write_meta.schema_version,
            projection_sha256=write_meta.sha256,
            verification_status=verification.overall_status,
            verification_verified=verification.verified,
            evidence_reference_count=verification.evidence_reference_count,
        )

    consistency_codes = _assert_exact_semantic_consistency(
        evaluation=evaluation,
        write_meta=write_meta,
        verification=verification,
        payload=payload,
    )
    if consistency_codes:
        return _error_result(
            reason_codes=consistency_codes,
            readiness_status=readiness_status,
            evaluated_at=evaluated_at_value,
            projection_path=write_meta.output_path,
            projection_schema_id=write_meta.schema_id,
            projection_schema_version=write_meta.schema_version,
            projection_sha256=write_meta.sha256,
            verification_status=verification.overall_status,
            verification_verified=verification.verified,
            evidence_reference_count=verification.evidence_reference_count,
        )

    pipeline_status: PipelineStatusV0 = (
        PIPELINE_STATUS_PASS
        if readiness_status == READINESS_STATUS_READY
        else PIPELINE_STATUS_BLOCKED
    )
    return ShadowPreparationReadinessOfflineProjectionPipelineResultV0(
        pipeline_status=pipeline_status,
        readiness_status=readiness_status,
        evaluated_at=evaluated_at_value,
        projection_path=write_meta.output_path,
        projection_schema_id=write_meta.schema_id,
        projection_schema_version=write_meta.schema_version,
        projection_sha256=write_meta.sha256,
        verification_status=verification.overall_status,
        verification_verified=verification.verified,
        reason_codes=(),
        evidence_reference_count=verification.evidence_reference_count,
    )


__all__ = [
    "DEFAULT_PROJECTION_OUTPUT_RELATIVE_PATH",
    "PACKAGE_MARKER",
    "PIPELINE_STATUS_BLOCKED",
    "PIPELINE_STATUS_ERROR",
    "PIPELINE_STATUS_PASS",
    "PRODUCER_FAMILY",
    "READINESS_STATUS_BLOCKED",
    "READINESS_STATUS_READY",
    "SCHEMA_ID",
    "SCHEMA_VERSION",
    "ShadowPreparationReadinessOfflineProjectionPipelineResultV0",
    "run_shadow_preparation_readiness_offline_projection_pipeline_v0",
]
