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
    generated_at: str | None = None,
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

    # --- double_play (fail-closed without new semantics) ---
    dp_inputs = try_extract_double_play_decision_inputs_from_replay_intermediate_v1(
        replay_intermediate
    )
    dp = classify_double_play_canonical_inputs_v1(dp_inputs)
    dp.cycle_id = cycle_id
    results[FAMILY_DOUBLE_PLAY] = dp

    persist_export_cursor_v1(Path(state_roots.evidence_session_root), cursor)
    return results
