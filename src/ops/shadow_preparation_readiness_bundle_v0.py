"""Shadow Preparation Readiness Bundle v0.

Aggregates already-existing canonical offline Shadow Preparation Readiness
artifacts into one read-only bundle for operator consumption.

Reuses the canonical offline projection pipeline (gate evaluation, durable
projection writer, and reader/verifier). Does not duplicate projection
serialization and does not introduce a second readiness truth or activation
authority.

Non-activating. No Shadow/Paper/Testnet/Runtime/Scheduler/Orders/Live side
effects. No network I/O.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Mapping

from src.ops.shadow_preparation_readiness_gate_v0 import (
    ShadowPreparationReadinessGateError,
    ShadowPreparationReadinessProjectionVerificationResultV0,
    verify_shadow_preparation_readiness_projection_v0,
)
from src.ops.shadow_preparation_readiness_offline_projection_pipeline_v0 import (
    PIPELINE_STATUS_BLOCKED,
    PIPELINE_STATUS_ERROR,
    PIPELINE_STATUS_PASS,
    ShadowPreparationReadinessOfflineProjectionPipelineResultV0,
    run_shadow_preparation_readiness_offline_projection_pipeline_v0,
)

PACKAGE_MARKER = "SHADOW_PREPARATION_READINESS_BUNDLE_V0=true"
PRODUCER_FAMILY = "ops.shadow_preparation_readiness_bundle_v0"
SCHEMA_ID = PRODUCER_FAMILY
SCHEMA_VERSION = "v0"

BUNDLE_STATUS_PASS: Literal["BUNDLE_PASS"] = "BUNDLE_PASS"
BUNDLE_STATUS_BLOCKED: Literal["BUNDLE_BLOCKED"] = "BUNDLE_BLOCKED"
BUNDLE_STATUS_ERROR: Literal["BUNDLE_ERROR"] = "BUNDLE_ERROR"

BundleStatusV0 = Literal["BUNDLE_PASS", "BUNDLE_BLOCKED", "BUNDLE_ERROR"]


@dataclass(frozen=True)
class ShadowPreparationReadinessBundleV0:
    """Read-only aggregate of canonical offline readiness artifacts."""

    bundle_status: BundleStatusV0
    reason_codes: tuple[str, ...]
    pipeline: dict[str, Any] | None
    projection: dict[str, Any] | None
    verification: dict[str, Any] | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_id": SCHEMA_ID,
            "schema_version": SCHEMA_VERSION,
            "bundle_status": self.bundle_status,
            "reason_codes": list(self.reason_codes),
            "pipeline": self.pipeline,
            "projection": self.projection,
            "verification": self.verification,
            "authority_effect": "NONE",
            "activation_authority": False,
            "projection_only": True,
            "bundle_only": True,
            "read_only": True,
        }


def serialize_shadow_preparation_readiness_bundle_v0(
    bundle: ShadowPreparationReadinessBundleV0,
) -> str:
    """Deterministic JSON serialization of an already-built bundle."""
    return (
        json.dumps(bundle.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    )


def _blocked(
    *,
    reason_codes: tuple[str, ...],
    pipeline: dict[str, Any] | None = None,
    projection: dict[str, Any] | None = None,
    verification: dict[str, Any] | None = None,
) -> ShadowPreparationReadinessBundleV0:
    return ShadowPreparationReadinessBundleV0(
        bundle_status=BUNDLE_STATUS_BLOCKED,
        reason_codes=reason_codes,
        pipeline=pipeline,
        projection=projection,
        verification=verification,
    )


def _error(
    *,
    reason_codes: tuple[str, ...],
    pipeline: dict[str, Any] | None = None,
) -> ShadowPreparationReadinessBundleV0:
    return ShadowPreparationReadinessBundleV0(
        bundle_status=BUNDLE_STATUS_ERROR,
        reason_codes=reason_codes,
        pipeline=pipeline,
        projection=None,
        verification=None,
    )


def _read_projection_payload(*, repo_root: Path, projection_path: str) -> dict[str, Any]:
    destination = (repo_root / projection_path).resolve()
    try:
        destination.relative_to(repo_root.resolve())
    except ValueError as exc:
        raise ShadowPreparationReadinessGateError("BUNDLE_PROJECTION_PATH_OUTSIDE_REPO") from exc
    if not destination.is_file():
        raise ShadowPreparationReadinessGateError("BUNDLE_PROJECTION_ARTIFACT_UNAVAILABLE")
    try:
        raw = destination.read_bytes()
    except OSError as exc:
        raise ShadowPreparationReadinessGateError(f"BUNDLE_PROJECTION_READ_FAILED:{exc}") from exc
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ShadowPreparationReadinessGateError("BUNDLE_PROJECTION_INVALID_JSON") from exc
    if not isinstance(payload, dict):
        raise ShadowPreparationReadinessGateError("BUNDLE_PROJECTION_INVALID_JSON")
    return payload


def _bundle_status_for_pipeline(
    pipeline_status: str,
) -> BundleStatusV0:
    if pipeline_status == PIPELINE_STATUS_PASS:
        return BUNDLE_STATUS_PASS
    if pipeline_status == PIPELINE_STATUS_BLOCKED:
        return BUNDLE_STATUS_BLOCKED
    return BUNDLE_STATUS_ERROR


def build_shadow_preparation_readiness_bundle_v0(
    *,
    repo_root: Path,
    output_path: str | None = None,
    config: Mapping[str, Any] | None = None,
    config_path: Path | None = None,
    evaluated_at: str | None = None,
    as_of: str | None = None,
) -> ShadowPreparationReadinessBundleV0:
    """Run the canonical pipeline once and aggregate its durable artifacts.

    Fail-closed: missing or unreadable required artifacts yield BLOCKED with
    reason codes. Values are never synthesized.
    """
    root = repo_root.resolve()

    pipeline_result: ShadowPreparationReadinessOfflineProjectionPipelineResultV0 = (
        run_shadow_preparation_readiness_offline_projection_pipeline_v0(
            repo_root=root,
            output_path=output_path,
            config=config,
            config_path=config_path,
            evaluated_at=evaluated_at,
            as_of=as_of,
        )
    )
    pipeline_dict = pipeline_result.to_dict()

    if pipeline_result.pipeline_status == PIPELINE_STATUS_ERROR:
        codes = tuple(pipeline_result.reason_codes) or ("PIPELINE_ERROR",)
        return _error(reason_codes=codes, pipeline=pipeline_dict)

    projection_path = pipeline_result.projection_path
    if not isinstance(projection_path, str) or not projection_path.strip():
        return _blocked(
            reason_codes=("BUNDLE_PROJECTION_ARTIFACT_UNAVAILABLE",),
            pipeline=pipeline_dict,
        )

    try:
        projection_payload = _read_projection_payload(
            repo_root=root,
            projection_path=projection_path,
        )
    except ShadowPreparationReadinessGateError as exc:
        return _blocked(
            reason_codes=(f"BUNDLE_ARTIFACT_UNAVAILABLE:{exc}",),
            pipeline=pipeline_dict,
        )

    verify_as_of = as_of if as_of is not None else pipeline_result.evaluated_at
    try:
        verification: ShadowPreparationReadinessProjectionVerificationResultV0 = (
            verify_shadow_preparation_readiness_projection_v0(
                repo_root=root,
                projection_path=projection_path,
                config=config,
                config_path=config_path,
                as_of=verify_as_of,
                expected_sha256=pipeline_result.projection_sha256,
            )
        )
    except Exception as exc:  # pragma: no cover - defensive fail-closed
        return _blocked(
            reason_codes=(f"BUNDLE_VERIFICATION_ARTIFACT_UNAVAILABLE:{type(exc).__name__}:{exc}",),
            pipeline=pipeline_dict,
            projection=projection_payload,
        )

    verification_dict = verification.to_dict()
    if not verification.verified:
        codes = tuple(verification.reason_codes) or ("BUNDLE_VERIFICATION_BLOCKED",)
        return _blocked(
            reason_codes=codes,
            pipeline=pipeline_dict,
            projection=projection_payload,
            verification=verification_dict,
        )

    return ShadowPreparationReadinessBundleV0(
        bundle_status=_bundle_status_for_pipeline(pipeline_result.pipeline_status),
        reason_codes=(),
        pipeline=pipeline_dict,
        projection=projection_payload,
        verification=verification_dict,
    )


__all__ = [
    "BUNDLE_STATUS_BLOCKED",
    "BUNDLE_STATUS_ERROR",
    "BUNDLE_STATUS_PASS",
    "PACKAGE_MARKER",
    "PRODUCER_FAMILY",
    "SCHEMA_ID",
    "SCHEMA_VERSION",
    "ShadowPreparationReadinessBundleV0",
    "build_shadow_preparation_readiness_bundle_v0",
    "serialize_shadow_preparation_readiness_bundle_v0",
]
