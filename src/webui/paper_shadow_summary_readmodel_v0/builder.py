"""Offline-Builder: Scan nur unter explizitem `bundle_root`, stdlib-json, keine Inferenz von Autorität."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .paths import (
    evidence_pack_dir,
    path_is_under_root,
    prj_smoke_run_dir,
    resolve_stamp,
)
from .types import (
    SCHEMA_VERSION,
    PaperShadowPathPolicyV0,
    PaperShadowSummaryMetadataInput,
    PaperShadowSummaryReadModelV0,
)

_FIXED_GEN_ENV = "PEAK_TRADE_FIXED_GENERATED_AT_UTC"


def _utc_iso(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


def _now_iso() -> str:
    fixed = os.environ.get(_FIXED_GEN_ENV)
    if fixed:
        return fixed
    return datetime.now(tz=timezone.utc).isoformat()


def _load_json(path: Path) -> tuple[Any | None, str | None]:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError:
        return None, "os_read_error"
    try:
        return json.loads(raw), None
    except json.JSONDecodeError:
        return None, "json_decode_error"


def _artifact_count_from_index(obj: Any) -> tuple[int | None, bool]:
    if isinstance(obj, list):
        return len(obj), True
    if isinstance(obj, dict):
        files = obj.get("files")
        if isinstance(files, list):
            return len(files), True
    return None, False


def _fill_count_from_fills(obj: Any) -> tuple[int | None, bool]:
    if isinstance(obj, list):
        return len(obj), True
    if isinstance(obj, dict):
        fills = obj.get("fills")
        if isinstance(fills, list):
            return len(fills), True
    return None, False


def _json_slot_present(
    bundle_root: Path,
    path: Path,
    *,
    mtime_acc: list[float],
    unreadable_code: str,
    warnings: list[str],
    errors: list[str],
) -> bool:
    if not path_is_under_root(bundle_root, path):
        errors.append("path_escapes_bundle_root")
        return False
    if not path.is_file():
        return False
    _data, err = _load_json(path)
    if err:
        errors.append(unreadable_code)
        return False
    mtime_acc.append(path.stat().st_mtime)
    return True


def _json_slot_counts_index(
    bundle_root: Path,
    path: Path,
    *,
    mtime_acc: list[float],
    warnings: list[str],
    errors: list[str],
) -> tuple[bool, int | None]:
    if not path_is_under_root(bundle_root, path):
        errors.append("path_escapes_bundle_root")
        return False, None
    if not path.is_file():
        return False, None
    obj, err = _load_json(path)
    if err:
        errors.append("index_json_unreadable")
        return False, None
    mtime_acc.append(path.stat().st_mtime)
    count, ok_shape = _artifact_count_from_index(obj)
    if not ok_shape:
        warnings.append("index_json_artifact_count_unknown_shape")
    return True, count


def _json_slot_counts_fills(
    bundle_root: Path,
    path: Path,
    *,
    mtime_acc: list[float],
    warnings: list[str],
    errors: list[str],
) -> tuple[bool, int | None]:
    if not path_is_under_root(bundle_root, path):
        errors.append("path_escapes_bundle_root")
        return False, None
    if not path.is_file():
        return False, None
    obj, err = _load_json(path)
    if err:
        errors.append("fills_json_unreadable")
        return False, None
    mtime_acc.append(path.stat().st_mtime)
    count, ok_shape = _fill_count_from_fills(obj)
    if not ok_shape:
        warnings.append("paper_fills_count_unknown_shape")
    return True, count


def _dir_json_slot(
    bundle_root: Path,
    dir_path: Path,
    *,
    missing_code: str,
    unreadable_code: str,
    mtime_acc: list[float],
    errors: list[str],
) -> bool:
    if not path_is_under_root(bundle_root, dir_path):
        errors.append("path_escapes_bundle_root")
        return False
    if not dir_path.is_dir():
        errors.append(missing_code)
        return False
    json_files = [
        p
        for p in dir_path.iterdir()
        if p.is_file() and p.suffix.lower() == ".json"
    ]
    if not json_files:
        errors.append(missing_code)
        return False
    any_ok = False
    for p in sorted(json_files):
        _data, err = _load_json(p)
        if err is None:
            any_ok = True
            mtime_acc.append(p.stat().st_mtime)
    if not any_ok:
        errors.append(unreadable_code)
        return False
    return True


def build_paper_shadow_summary_readmodel_v0(
    bundle_root: str | Path,
    *,
    metadata: PaperShadowSummaryMetadataInput | None = None,
    policy: PaperShadowPathPolicyV0 | None = None,
    generated_at_utc: str | None = None,
) -> PaperShadowSummaryReadModelV0:
    root = Path(bundle_root).expanduser()
    try:
        root = root.resolve(strict=True)
    except FileNotFoundError as err:
        raise ValueError("bundle_root must be an existing directory") from err
    if not root.is_dir():
        raise ValueError("bundle_root must be an existing directory")

    metadata = metadata or PaperShadowSummaryMetadataInput()
    warnings: list[str] = []
    errors: list[str] = []
    mtime_acc: list[float] = []

    stamp, stamp_errors = resolve_stamp(root, policy)
    errors.extend(stamp_errors)

    manifest_present = False
    index_present = False
    summary_present = False
    paper_account_present = False
    paper_fills_present = False
    paper_evidence_manifest_present = False
    shadow_session_summary_present = False
    shadow_evidence_manifest_present = False
    p4c_present = False
    p5a_present = False
    artifact_count: int | None = None
    paper_fill_count: int | None = None

    if stamp:
        pack = evidence_pack_dir(root, stamp)
        manifest_path = pack / "manifest.json"
        index_path = pack / "index.json"
        if manifest_path.is_file():
            manifest_present = _json_slot_present(
                root,
                manifest_path,
                mtime_acc=mtime_acc,
                unreadable_code="manifest_json_unreadable",
                warnings=warnings,
                errors=errors,
            )
        else:
            warnings.append("pack_manifest_json_missing")

        if index_path.is_file():
            index_present, artifact_count = _json_slot_counts_index(
                root,
                index_path,
                mtime_acc=mtime_acc,
                warnings=warnings,
                errors=errors,
            )
        else:
            warnings.append("pack_index_json_missing")

        run = prj_smoke_run_dir(root, stamp)
        summary_present = _json_slot_present(
            root,
            run / "summary.json",
            mtime_acc=mtime_acc,
            unreadable_code="summary_json_unreadable",
            warnings=warnings,
            errors=errors,
        )
        if not (run / "summary.json").is_file():
            warnings.append("summary_json_missing")

        paper_account_present = _json_slot_present(
            root,
            run / "paper" / "account.json",
            mtime_acc=mtime_acc,
            unreadable_code="paper_account_json_unreadable",
            warnings=warnings,
            errors=errors,
        )
        if not (run / "paper" / "account.json").is_file():
            warnings.append("paper_account_json_missing")

        fills_path = run / "paper" / "fills.json"
        if fills_path.is_file():
            paper_fills_present, paper_fill_count = _json_slot_counts_fills(
                root,
                fills_path,
                mtime_acc=mtime_acc,
                warnings=warnings,
                errors=errors,
            )
        else:
            warnings.append("paper_fills_json_missing")
            paper_fills_present = False
            paper_fill_count = None

        paper_evidence_manifest_present = _json_slot_present(
            root,
            run / "paper" / "evidence_manifest.json",
            mtime_acc=mtime_acc,
            unreadable_code="paper_evidence_manifest_json_unreadable",
            warnings=warnings,
            errors=errors,
        )
        if not (run / "paper" / "evidence_manifest.json").is_file():
            warnings.append("paper_evidence_manifest_json_missing")

        shadow_session_summary_present = _json_slot_present(
            root,
            run / "shadow" / "shadow_session_summary.json",
            mtime_acc=mtime_acc,
            unreadable_code="shadow_session_summary_json_unreadable",
            warnings=warnings,
            errors=errors,
        )
        if not (run / "shadow" / "shadow_session_summary.json").is_file():
            warnings.append("shadow_session_summary_json_missing")

        shadow_evidence_manifest_present = _json_slot_present(
            root,
            run / "shadow" / "evidence_manifest.json",
            mtime_acc=mtime_acc,
            unreadable_code="shadow_evidence_manifest_json_unreadable",
            warnings=warnings,
            errors=errors,
        )
        if not (run / "shadow" / "evidence_manifest.json").is_file():
            warnings.append("shadow_evidence_manifest_json_missing")

        p4c_present = _dir_json_slot(
            root,
            run / "shadow" / "p4c",
            missing_code="p4c_json_missing",
            unreadable_code="p4c_json_unreadable",
            mtime_acc=mtime_acc,
            errors=errors,
        )
        p5a_present = _dir_json_slot(
            root,
            run / "shadow" / "p5a",
            missing_code="p5a_json_missing",
            unreadable_code="p5a_json_unreadable",
            mtime_acc=mtime_acc,
            errors=errors,
        )
    else:
        warnings.append("stamp_unresolved_bundle_partial")

    gen = generated_at_utc or _now_iso()
    if mtime_acc:
        snapshot = _utc_iso(max(mtime_acc))
    else:
        snapshot = gen

    src_label = metadata.source_label or "paper_shadow_bundle"
    src_kind = metadata.source_kind or "fixture"
    src_owner = metadata.source_owner or "paper_shadow_summary_readmodel_v0"

    bundle_id = metadata.artifact_bundle_id or (stamp if stamp else "unknown")
    bundle_lbl = metadata.artifact_bundle_label or (
        f"prj_smoke {stamp}" if stamp else "prj_smoke unknown"
    )

    wf_name = metadata.workflow_name or ""
    wf_run = metadata.workflow_run_id or ""

    return PaperShadowSummaryReadModelV0(
        schema_version=SCHEMA_VERSION,
        generated_at_utc=gen,
        source_label=src_label,
        source_kind=src_kind,
        source_owner=src_owner,
        stale=True,
        stale_reason="offline_bundle_scan",
        snapshot_time_utc=snapshot,
        warnings=tuple(warnings),
        errors=tuple(errors),
        workflow_name=wf_name,
        workflow_run_id=wf_run,
        source_commit=metadata.source_commit,
        artifact_bundle_id=bundle_id,
        artifact_bundle_label=bundle_lbl,
        manifest_present=manifest_present,
        index_present=index_present,
        summary_present=summary_present,
        operator_context_present=False,
        paper_account_present=paper_account_present,
        paper_fills_present=paper_fills_present,
        paper_evidence_manifest_present=paper_evidence_manifest_present,
        shadow_session_summary_present=shadow_session_summary_present,
        shadow_evidence_manifest_present=shadow_evidence_manifest_present,
        p4c_present=p4c_present,
        p5a_present=p5a_present,
        artifact_count=artifact_count,
        paper_fill_count=paper_fill_count,
    )
