"""Post-commit family source persist + sibling export + presentation materialize."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Optional

from src.ops.archive_sibling_export_contract_v1 import canonical_digest_v1
from src.ops.canonical_decision_archive_sibling_exporter_v1.exporter_v1 import (
    export_canonical_decision_evidence_to_archive_sibling_v1,
)
from src.ops.dynamic_scope_archive_sibling_exporter_v1.exporter_v1 import (
    export_dynamic_scope_state_to_archive_sibling_v1,
)
from src.ops.productive_decision_host_active_archive_three_family_binding_v1.constants_v1 import (
    CANONICAL_DECISION_SOURCE_FILENAME,
    FAMILY_CANONICAL_DECISION,
    FAMILY_DOUBLE_PLAY,
    FAMILY_DYNAMIC_SCOPE,
    FAMILY_REGIME_BULL_BEAR_SWITCH,
    FAMILY_EXECUTION_RECONCILIATION,
    FAMILY_ECONOMIC_SUMMARY,
    FAMILY_RISK_SIZING_CAPITAL,
)
from src.ops.regime_bull_bear_switch_archive_sibling_exporter_v1.exporter_v1 import (
    export_regime_bull_bear_switch_to_archive_sibling_v1,
)
from src.ops.execution_reconciliation_archive_sibling_exporter_v1.exporter_v1 import (
    export_execution_reconciliation_to_archive_sibling_from_replay_commit_v1,
)
from src.ops.risk_sizing_capital_archive_sibling_exporter_v1.exporter_v1 import (
    export_risk_sizing_capital_to_archive_sibling_from_replay_commit_v1,
)
from src.ops.economic_summary_archive_sibling_exporter_v1.exporter_v1 import (
    export_economic_summary_to_archive_sibling_from_explicit_bundle_v1,
)
from src.ops.double_play_archive_sibling_exporter_v1.exporter_v1 import (
    export_double_play_display_to_archive_sibling_from_replay_commit_v1,
)
from src.webui.workflow_dashboard_readmodel_v1.double_play_presentation_projection_materializer_v1 import (
    materialize_double_play_presentation_projection_v1,
)
from src.webui.workflow_dashboard_readmodel_v1.double_play_presentation_projection_v1 import (
    STORAGE_RELATIVE_PATH as DOUBLE_PLAY_PRESENTATION_STORAGE_RELATIVE_PATH,
    try_load_double_play_presentation_projection_v1,
)
from src.ops.productive_decision_host_active_archive_three_family_binding_v1.double_play_input_gate_v1 import (
    classify_double_play_canonical_inputs_v1,
    try_extract_double_play_decision_inputs_from_replay_intermediate_v1,
)
from src.ops.productive_decision_host_active_archive_three_family_binding_v1.models_v1 import (
    ArchiveBindingV1,
    FamilyExportResultV1,
    StateRootBindingV1,
)
from src.ops.productive_decision_host_active_archive_three_family_binding_v1.state_root_layout_v1 import (
    load_export_cursor_v1,
    persist_export_cursor_v1,
)
from src.webui.workflow_dashboard_readmodel_v1.canonical_decision_presentation_projection_materializer_v1 import (
    materialize_canonical_decision_presentation_projection_v1,
)
from src.webui.workflow_dashboard_readmodel_v1.canonical_decision_presentation_projection_v1 import (
    try_load_canonical_decision_presentation_projection_v1,
)
from src.webui.workflow_dashboard_readmodel_v1.dynamic_scope_presentation_projection_materializer_v1 import (
    materialize_dynamic_scope_presentation_projection_v1,
)
from src.webui.workflow_dashboard_readmodel_v1.dynamic_scope_presentation_projection_v1 import (
    try_load_dynamic_scope_presentation_projection_v1,
)
from src.webui.workflow_dashboard_readmodel_v1.bull_bear_regime_presentation_projection_materializer_v1 import (
    materialize_bull_bear_regime_presentation_projection_v1,
)
from src.webui.workflow_dashboard_readmodel_v1.risk_sizing_capital_presentation_projection_materializer_v1 import (
    materialize_risk_sizing_capital_presentation_projection_v1,
)
from src.webui.workflow_dashboard_readmodel_v1.execution_reconciliation_presentation_projection_materializer_v1 import (
    materialize_execution_reconciliation_presentation_projection_v1,
)
from src.webui.workflow_dashboard_readmodel_v1.execution_reconciliation_presentation_projection_v1 import (
    STORAGE_RELATIVE_PATH as EXECUTION_RECONCILIATION_PRESENTATION_STORAGE_RELATIVE_PATH,
    try_load_execution_reconciliation_presentation_projection_v1,
)
from src.webui.workflow_dashboard_readmodel_v1.risk_sizing_capital_presentation_projection_v1 import (
    STORAGE_RELATIVE_PATH as RISK_SIZING_PRESENTATION_STORAGE_RELATIVE_PATH,
    try_load_risk_sizing_capital_presentation_projection_v1,
)
from src.webui.workflow_dashboard_readmodel_v1.economic_summary_presentation_projection_materializer_v1 import (
    materialize_economic_summary_presentation_projection_v1,
)
from src.webui.workflow_dashboard_readmodel_v1.economic_summary_presentation_projection_v1 import (
    STORAGE_RELATIVE_PATH as ECONOMIC_SUMMARY_PRESENTATION_STORAGE_RELATIVE_PATH,
    try_load_economic_summary_presentation_projection_v1,
)
from src.webui.workflow_dashboard_readmodel_v1.bull_bear_regime_presentation_projection_v1 import (
    STORAGE_RELATIVE_PATH as REGIME_PRESENTATION_STORAGE_RELATIVE_PATH,
    try_load_bull_bear_regime_presentation_projection_v1,
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _atomic_write_json(path: Path, payload: Mapping[str, Any]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    body = json.dumps(dict(payload), sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    digest = canonical_digest_v1(dict(payload))
    fd, tmp_name = __import__("tempfile").mkstemp(prefix=path.name + ".", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(body)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)
    return digest


def persist_canonical_decision_evidence_source_v1(
    *,
    state_roots: StateRootBindingV1,
    evidence_payload: Mapping[str, Any],
    cycle_id: str,
) -> tuple[Path, str]:
    """Persist cycle evidence as durable source (pre-sibling-export)."""
    dest = Path(state_roots.canonical_decision_source_dir) / CANONICAL_DECISION_SOURCE_FILENAME
    payload = dict(evidence_payload)
    payload.setdefault("_export_meta", {})
    if isinstance(payload.get("_export_meta"), dict):
        meta = dict(payload["_export_meta"])
        meta["cycle_id"] = cycle_id
        payload["_export_meta"] = meta
    # Exporter rejects unknown nesting for required fields — strip meta for digest file.
    exportable = {k: v for k, v in payload.items() if not str(k).startswith("_")}
    digest = _atomic_write_json(dest, exportable)
    return dest, digest


def export_families_after_runtime_commit_v1(
    *,
    state_roots: StateRootBindingV1,
    archive: ArchiveBindingV1,
    cycle_id: str,
    cycle_index: int,
    dynamic_scope_persisted: bool,
    evidence_payload: Mapping[str, Any] | None,
    replay_intermediate: object | None = None,
    replay_regime_id: str | None = None,
    replay_regime_status: str | None = None,
    generated_at: str | None = None,
    economic_viability_evidence_bundle_path: str | None = None,
) -> dict[str, FamilyExportResultV1]:
    """Export siblings after runtime commit. Projection errors never roll back runtime."""
    ts = generated_at or _utc_now_iso()
    cursor = load_export_cursor_v1(Path(state_roots.evidence_session_root))
    results: dict[str, FamilyExportResultV1] = {}

    # --- dynamic_scope ---
    ds = FamilyExportResultV1(
        family_id=FAMILY_DYNAMIC_SCOPE,
        exportable=bool(dynamic_scope_persisted),
        exported=False,
        materialized=False,
        loader_ok=False,
        cycle_id=cycle_id,
    )
    if not dynamic_scope_persisted:
        ds.skipped_reason = "dynamic_scope_not_persisted_this_cycle"
        ds.error_code = "DYNAMIC_SCOPE_COMMIT_REQUIRED_BEFORE_EXPORT"
    else:
        prior = str(cursor.get("dynamic_scope_cycle_id") or "")
        # stale / out-of-order: reject exporting an older cycle_id than cursor
        if prior and prior > cycle_id:
            ds.error_code = "STALE_CYCLE_EXPORT_REJECTED"
            ds.detail = f"cursor={prior}:cycle={cycle_id}"
        else:
            out = export_dynamic_scope_state_to_archive_sibling_v1(
                dynamic_scope_state_root=state_roots.dynamic_scope_state_root,
                archive_root=archive.archive_root,
            )
            ds.exported = bool(out.exported)
            ds.source_digest = str(out.source_payload_digest or "")
            ds.target_path = str(out.target_path or "")
            ds.error_code = str(out.error_code or "")
            ds.detail = str(out.failure_reason or "")
            if ds.exported:
                mat = materialize_dynamic_scope_presentation_projection_v1(
                    archive.archive_root,
                    generated_at=ts,
                    source_reference=ds.target_path or None,
                )
                ds.materialized = bool(mat.written)
                if not mat.written:
                    ds.detail = f"materialize:{mat.status}:{','.join(mat.errors)}"
                loaded = try_load_dynamic_scope_presentation_projection_v1(
                    Path(archive.archive_root)
                )
                ds.loader_ok = bool(getattr(loaded, "loaded", False))
                cursor["dynamic_scope_cycle_id"] = cycle_id
                cursor["dynamic_scope_digest"] = ds.source_digest
                # Idempotent: same digest re-export is success with identical file.
    results[FAMILY_DYNAMIC_SCOPE] = ds

    # --- canonical_decision ---
    cd = FamilyExportResultV1(
        family_id=FAMILY_CANONICAL_DECISION,
        exportable=bool(evidence_payload),
        exported=False,
        materialized=False,
        loader_ok=False,
        cycle_id=cycle_id,
    )
    if not evidence_payload:
        cd.skipped_reason = "canonical_decision_evidence_missing"
        cd.error_code = "CANONICAL_DECISION_EVIDENCE_REQUIRED"
    else:
        prior = str(cursor.get("canonical_decision_cycle_id") or "")
        if prior and prior > cycle_id:
            cd.error_code = "STALE_CYCLE_EXPORT_REJECTED"
            cd.detail = f"cursor={prior}:cycle={cycle_id}"
        else:
            source_path, digest = persist_canonical_decision_evidence_source_v1(
                state_roots=state_roots,
                evidence_payload=evidence_payload,
                cycle_id=cycle_id,
            )
            # Idempotent: same digest already exported → still ok
            if (
                cursor.get("canonical_decision_digest") == digest
                and Path(archive.canonical_decision_sibling_path).is_file()
            ):
                cd.exported = True
                cd.source_digest = digest
                cd.target_path = archive.canonical_decision_sibling_path
                cd.detail = "idempotent_same_digest"
            else:
                out = export_canonical_decision_evidence_to_archive_sibling_v1(
                    evidence_source_path=source_path,
                    archive_root=archive.archive_root,
                )
                cd.exported = bool(out.exported)
                cd.source_digest = str(out.source_payload_digest or digest)
                cd.target_path = str(out.target_path or "")
                cd.error_code = str(out.error_code or "")
                cd.detail = str(out.failure_reason or "")
            if cd.exported:
                mat = materialize_canonical_decision_presentation_projection_v1(
                    archive.archive_root,
                    generated_at=ts,
                    source_reference=cd.target_path or None,
                )
                cd.materialized = bool(mat.written)
                if not mat.written:
                    cd.detail = f"materialize:{mat.status}:{','.join(mat.errors)}"
                loaded = try_load_canonical_decision_presentation_projection_v1(
                    Path(archive.archive_root)
                )
                cd.loader_ok = bool(getattr(loaded, "loaded", False))
                cursor["canonical_decision_cycle_id"] = cycle_id
                cursor["canonical_decision_digest"] = cd.source_digest
    results[FAMILY_CANONICAL_DECISION] = cd

    # --- regime_bull_bear_switch ---
    rg = FamilyExportResultV1(
        family_id=FAMILY_REGIME_BULL_BEAR_SWITCH,
        exportable=bool(replay_intermediate and replay_regime_id and replay_regime_status),
        exported=False,
        materialized=False,
        loader_ok=False,
        cycle_id=cycle_id,
    )
    if not rg.exportable:
        rg.skipped_reason = "regime_replay_commit_facts_missing"
        rg.error_code = "REGIME_REPLAY_COMMIT_REQUIRED"
    else:
        prior = str(cursor.get("regime_bull_bear_switch_cycle_id") or "")
        if prior and prior > cycle_id:
            rg.error_code = "STALE_CYCLE_EXPORT_REJECTED"
            rg.detail = f"cursor={prior}:cycle={cycle_id}"
        else:
            assert replay_regime_id is not None
            assert replay_regime_status is not None
            out = export_regime_bull_bear_switch_to_archive_sibling_v1(
                archive_root=archive.archive_root,
                regime_id=replay_regime_id,
                regime_status=replay_regime_status,
                replay_intermediate=replay_intermediate,
                source_label=f"replay_commit:{cycle_id}",
            )
            rg.exported = bool(out.exported)
            rg.source_digest = str(out.source_payload_digest or "")
            rg.target_path = str(out.target_path or "")
            rg.error_code = str(out.error_code or "")
            rg.detail = str(out.failure_reason or "")
            if rg.exported:
                mat = materialize_bull_bear_regime_presentation_projection_v1(
                    archive.archive_root,
                    generated_at=ts,
                    source_reference=rg.target_path or None,
                )
                rg.materialized = bool(mat.written)
                rg.projection_path = str(
                    Path(archive.archive_root) / REGIME_PRESENTATION_STORAGE_RELATIVE_PATH
                )
                if not mat.written:
                    rg.detail = f"materialize:{mat.status}:{','.join(mat.errors)}"
                loaded = try_load_bull_bear_regime_presentation_projection_v1(
                    Path(archive.archive_root)
                )
                rg.loader_ok = bool(getattr(loaded, "loaded", False))
                cursor["regime_bull_bear_switch_cycle_id"] = cycle_id
                cursor["regime_bull_bear_switch_digest"] = rg.source_digest
    results[FAMILY_REGIME_BULL_BEAR_SWITCH] = rg

    # --- double_play (Pure-Stack Decisions already on replay intermediate only) ---
    dp_inputs = try_extract_double_play_decision_inputs_from_replay_intermediate_v1(
        replay_intermediate
    )
    dp = classify_double_play_canonical_inputs_v1(dp_inputs)
    dp.cycle_id = cycle_id
    if not dp.exportable:
        dp.skipped_reason = dp.skipped_reason or "double_play_display_inputs_not_exportable"
    else:
        prior = str(cursor.get("double_play_cycle_id") or "")
        if prior and prior > cycle_id:
            dp.error_code = "STALE_CYCLE_EXPORT_REJECTED"
            dp.detail = f"cursor={prior}:cycle={cycle_id}"
        else:
            out = export_double_play_display_to_archive_sibling_from_replay_commit_v1(
                archive_root=archive.archive_root,
                replay_intermediate=replay_intermediate,
                source_label=f"replay_commit:{cycle_id}",
            )
            dp.exported = bool(out.exported)
            dp.source_digest = str(out.source_payload_digest or "")
            dp.target_path = str(out.target_path or "")
            dp.error_code = str(out.error_code or "")
            dp.detail = str(out.failure_reason or "")
            if dp.exported:
                mat = materialize_double_play_presentation_projection_v1(
                    archive.archive_root,
                    generated_at=ts,
                    effective_at=ts,
                    source_reference=dp.target_path or None,
                )
                dp.materialized = bool(mat.written)
                dp.projection_path = str(
                    Path(archive.archive_root) / DOUBLE_PLAY_PRESENTATION_STORAGE_RELATIVE_PATH
                )
                if not mat.written:
                    dp.detail = f"materialize:{mat.status}:{','.join(mat.errors)}"
                loaded = try_load_double_play_presentation_projection_v1(Path(archive.archive_root))
                dp.loader_ok = bool(getattr(loaded, "loaded", False))
                cursor["double_play_cycle_id"] = cycle_id
                cursor["double_play_digest"] = dp.source_digest
    results[FAMILY_DOUBLE_PLAY] = dp

    # --- risk_sizing_capital (CapitalRiskSizingDecisionV1 on replay intermediate) ---
    rs = FamilyExportResultV1(
        family_id=FAMILY_RISK_SIZING_CAPITAL,
        exportable=replay_intermediate is not None,
        exported=False,
        materialized=False,
        loader_ok=False,
        cycle_id=cycle_id,
    )
    if replay_intermediate is None:
        rs.skipped_reason = "replay_intermediate_missing"
        rs.error_code = "RISK_SIZING_REPLAY_COMMIT_REQUIRED"
    else:
        prior = str(cursor.get("risk_sizing_capital_cycle_id") or "")
        if prior and prior > cycle_id:
            rs.error_code = "STALE_CYCLE_EXPORT_REJECTED"
            rs.detail = f"cursor={prior}:cycle={cycle_id}"
        else:
            out = export_risk_sizing_capital_to_archive_sibling_from_replay_commit_v1(
                archive_root=archive.archive_root,
                replay_intermediate=replay_intermediate,
                source_label=f"replay_commit:{cycle_id}",
            )
            rs.exported = bool(out.exported)
            rs.source_digest = str(out.source_payload_digest or "")
            rs.target_path = str(out.target_path or "")
            rs.error_code = str(out.error_code or "")
            rs.detail = str(out.failure_reason or "")
            if rs.exported:
                mat = materialize_risk_sizing_capital_presentation_projection_v1(
                    archive.archive_root,
                    generated_at=ts,
                    effective_at=ts,
                    source_reference=rs.target_path or None,
                )
                rs.materialized = bool(mat.written)
                rs.projection_path = str(
                    Path(archive.archive_root) / RISK_SIZING_PRESENTATION_STORAGE_RELATIVE_PATH
                )
                if not mat.written:
                    rs.detail = f"materialize:{mat.status}:{','.join(mat.errors)}"
                loaded = try_load_risk_sizing_capital_presentation_projection_v1(
                    Path(archive.archive_root)
                )
                rs.loader_ok = bool(getattr(loaded, "loaded", False))
                cursor["risk_sizing_capital_cycle_id"] = cycle_id
                cursor["risk_sizing_capital_digest"] = rs.source_digest
    results[FAMILY_RISK_SIZING_CAPITAL] = rs

    # --- execution_reconciliation (order-intent binding facts on decision evidence) ---
    er = FamilyExportResultV1(
        family_id=FAMILY_EXECUTION_RECONCILIATION,
        exportable=bool(evidence_payload),
        exported=False,
        materialized=False,
        loader_ok=False,
        cycle_id=cycle_id,
    )
    if not evidence_payload:
        er.skipped_reason = "canonical_decision_evidence_missing"
        er.error_code = "EXECUTION_RECONCILIATION_EVIDENCE_REQUIRED"
    else:
        prior = str(cursor.get("execution_reconciliation_cycle_id") or "")
        if prior and prior > cycle_id:
            er.error_code = "STALE_CYCLE_EXPORT_REJECTED"
            er.detail = f"cursor={prior}:cycle={cycle_id}"
        else:
            out = export_execution_reconciliation_to_archive_sibling_from_replay_commit_v1(
                archive_root=archive.archive_root,
                replay_intermediate=replay_intermediate,
                decision_evidence=evidence_payload,
                source_label=f"replay_commit:{cycle_id}",
            )
            er.exported = bool(out.exported)
            er.source_digest = str(out.source_payload_digest or "")
            er.target_path = str(out.target_path or "")
            er.error_code = str(out.error_code or "")
            er.detail = str(out.failure_reason or "")
            if er.exported:
                mat = materialize_execution_reconciliation_presentation_projection_v1(
                    archive.archive_root,
                    generated_at=ts,
                    effective_at=ts,
                    source_reference=er.target_path or None,
                )
                er.materialized = bool(mat.written)
                er.projection_path = str(
                    Path(archive.archive_root)
                    / EXECUTION_RECONCILIATION_PRESENTATION_STORAGE_RELATIVE_PATH
                )
                if not mat.written:
                    er.detail = f"materialize:{mat.status}:{','.join(mat.errors)}"
                loaded = try_load_execution_reconciliation_presentation_projection_v1(
                    Path(archive.archive_root)
                )
                er.loader_ok = bool(getattr(loaded, "loaded", False))
                cursor["execution_reconciliation_cycle_id"] = cycle_id
                cursor["execution_reconciliation_digest"] = er.source_digest
    results[FAMILY_EXECUTION_RECONCILIATION] = er

    # --- economic_summary (explicit manifest-verified STEP29M bundle only) ---
    eco_path_provided = bool(
        economic_viability_evidence_bundle_path
        and str(economic_viability_evidence_bundle_path).strip()
    )
    eco = FamilyExportResultV1(
        family_id=FAMILY_ECONOMIC_SUMMARY,
        exportable=eco_path_provided,
        exported=False,
        materialized=False,
        loader_ok=False,
        cycle_id=cycle_id,
    )
    if not eco_path_provided:
        eco.skipped_reason = "economic_viability_evidence_bundle_path_not_provided"
        eco.error_code = "ECONOMIC_EXPLICIT_BUNDLE_REFERENCE_REQUIRED"
    else:
        prior = str(cursor.get("economic_summary_cycle_id") or "")
        if prior and prior > cycle_id:
            eco.error_code = "STALE_CYCLE_EXPORT_REJECTED"
            eco.detail = f"cursor={prior}:cycle={cycle_id}"
        else:
            out = export_economic_summary_to_archive_sibling_from_explicit_bundle_v1(
                archive_root=archive.archive_root,
                economic_viability_evidence_bundle_path=economic_viability_evidence_bundle_path,
                source_label=f"explicit_bundle:{cycle_id}",
            )
            eco.exported = bool(out.exported)
            eco.source_digest = str(out.source_payload_digest or "")
            eco.target_path = str(out.target_path or "")
            eco.error_code = str(out.error_code or "")
            eco.detail = str(out.failure_reason or "")
            if eco.exported:
                mat = materialize_economic_summary_presentation_projection_v1(
                    archive.archive_root,
                    generated_at=ts,
                    effective_at=ts,
                    source_reference=eco.target_path or None,
                )
                eco.materialized = bool(mat.written)
                eco.projection_path = str(
                    Path(archive.archive_root) / ECONOMIC_SUMMARY_PRESENTATION_STORAGE_RELATIVE_PATH
                )
                if not mat.written:
                    eco.detail = f"materialize:{mat.status}:{','.join(mat.errors)}"
                loaded = try_load_economic_summary_presentation_projection_v1(
                    Path(archive.archive_root)
                )
                eco.loader_ok = bool(getattr(loaded, "loaded", False))
                cursor["economic_summary_cycle_id"] = cycle_id
                cursor["economic_summary_digest"] = eco.source_digest
    results[FAMILY_ECONOMIC_SUMMARY] = eco

    persist_export_cursor_v1(Path(state_roots.evidence_session_root), cursor)
    return results
