"""Datentypen für `paper_shadow_summary_readmodel_v0` (reines Schema-Envelope, stdlib)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

SCHEMA_VERSION = "paper_shadow_summary_readmodel.v0"


@dataclass(frozen=True)
class PaperShadowSummaryMetadataInput:
    """Optionale Metadaten — nur explizit gesetzte Werte (kein Git/Netzwerk)."""

    source_label: str | None = None
    source_kind: str | None = None
    source_owner: str | None = None
    workflow_name: str | None = None
    workflow_run_id: str | None = None
    source_commit: str | None = None
    artifact_bundle_id: str | None = None
    artifact_bundle_label: str | None = None


@dataclass(frozen=True)
class PaperShadowPathPolicyV0:
    """Pfad-Politik v0: optionaler Stamp, sonst Auflösung über `prj_smoke/` (Appendix A.3)."""

    stamp: str | None = None


@dataclass(frozen=True)
class PaperShadowSummaryReadModelV0:
    """Anzeige-Payload gemäß docs/webui/observability/PAPER_SHADOW_SUMMARY_READ_MODEL_SCHEMA_V0.md ."""

    schema_version: str
    generated_at_utc: str
    source_label: str
    source_kind: str
    source_owner: str
    stale: bool
    stale_reason: str
    snapshot_time_utc: str
    warnings: tuple[str, ...]
    errors: tuple[str, ...]
    workflow_name: str
    workflow_run_id: str
    source_commit: str | None
    artifact_bundle_id: str
    artifact_bundle_label: str
    manifest_present: bool
    index_present: bool
    summary_present: bool
    operator_context_present: bool
    paper_account_present: bool
    paper_fills_present: bool
    paper_evidence_manifest_present: bool
    shadow_session_summary_present: bool
    shadow_evidence_manifest_present: bool
    p4c_present: bool
    p5a_present: bool
    artifact_count: int | None
    paper_fill_count: int | None


def to_json_dict(model: PaperShadowSummaryReadModelV0) -> dict[str, Any]:
    """JSON-kompatibles dict (display-only; `None` → JSON null)."""

    return {
        "schema_version": model.schema_version,
        "generated_at_utc": model.generated_at_utc,
        "source_label": model.source_label,
        "source_kind": model.source_kind,
        "source_owner": model.source_owner,
        "stale": model.stale,
        "stale_reason": model.stale_reason,
        "snapshot_time_utc": model.snapshot_time_utc,
        "warnings": list(model.warnings),
        "errors": list(model.errors),
        "workflow_name": model.workflow_name,
        "workflow_run_id": model.workflow_run_id,
        "source_commit": model.source_commit,
        "artifact_bundle_id": model.artifact_bundle_id,
        "artifact_bundle_label": model.artifact_bundle_label,
        "manifest_present": model.manifest_present,
        "index_present": model.index_present,
        "summary_present": model.summary_present,
        "operator_context_present": model.operator_context_present,
        "paper_account_present": model.paper_account_present,
        "paper_fills_present": model.paper_fills_present,
        "paper_evidence_manifest_present": model.paper_evidence_manifest_present,
        "shadow_session_summary_present": model.shadow_session_summary_present,
        "shadow_evidence_manifest_present": model.shadow_evidence_manifest_present,
        "p4c_present": model.p4c_present,
        "p5a_present": model.p5a_present,
        "artifact_count": model.artifact_count,
        "paper_fill_count": model.paper_fill_count,
    }
