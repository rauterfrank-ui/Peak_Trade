"""Read-only consistency guard for GHOSV Execution bounded offline observe."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1 import (
    LEDGER_FILENAME,
)
from src.ops.ghosv_bounded_context_v1.current_execution_cycle_evidence_reader_v1 import (
    TRANSITIONS_FILENAME,
    GovernedCycleEvidenceOptionsV1,
    _transition_sequence_flags_v1,
    _validate_g004_record_v1,
    parse_post_count_field_v1,
)
from src.ops.ghosv_bounded_context_v1.s01_evidence_ingest_v1 import GhosvEvidenceIngestError
from src.ops.productive_reconciliation_runtime_binding_v1.constants_v1 import (
    EVIDENCE_FILENAME,
    MANIFEST_FILENAME,
    PORTFOLIO_STATE_FILENAME,
)
from src.ops.productive_reconciliation_runtime_binding_v1.persistence_v1 import (
    PersistenceVerificationError,
    verify_manifest,
)

GUARD_CONTRACT = "ghosv_execution_offline_consistency_guard.v1"

ENTRY_STATE_SNAPSHOT_FILENAME = "continuous_run_entry_state_snapshot_v1.json"
S5_CYCLE_AUTHORIZATION_FILENAME = "s5_cycle_authorization_v1.json"
PRE_EXTERNAL_REPORT_FILENAME = "PRE_EXTERNAL_CONVERGENCE_REPORT.json"
_MAX_REPOSITORY_WALK_DEPTH = 64

MAX_INPUT_FILES = 12
MAX_FILE_BYTES = 8 * 1024 * 1024
MAX_TOTAL_INPUT_BYTES = 24 * 1024 * 1024
MAX_JSONL_RECORDS = 10_000
MAX_LEDGER_READ_RETRIES = 1
MAX_OBSERVER_WALL_SECONDS = 120.0


class BoundedInputError(ValueError):
    """Input exceeds observer resource bounds."""


def _resolved_path_is_under(*, child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
    except (ValueError, OSError):
        return False
    return True


def _raw_path_has_traversal(raw: str) -> bool:
    normalized = raw.replace("\\", "/").strip()
    if not normalized:
        return False
    return normalized.startswith("../") or "/../" in f"/{normalized}/"


def discover_repository_root_from_paths_v1(
    *anchor_paths: Path | None,
) -> Path | None:
    """Deterministic repository root from evidence paths (not process CWD)."""
    for raw in anchor_paths:
        if raw is None:
            continue
        path = Path(raw).expanduser()
        try:
            resolved = path.resolve()
        except OSError:
            continue
        start = resolved.parent if resolved.is_file() else resolved
        cur = start
        for _ in range(_MAX_REPOSITORY_WALK_DEPTH):
            if (cur / ".git").exists():
                try:
                    return cur.resolve()
                except OSError:
                    return None
            parent = cur.parent
            if parent == cur:
                break
            cur = parent
    return None


def resolve_persisted_evidence_root_v1(
    *,
    evidence_root_raw: str,
    repository_root: Path | None,
) -> tuple[Path | None, tuple[str, ...]]:
    """Resolve PRE_EXTERNAL EVIDENCE_ROOT without CWD-dependent relative paths."""
    raw = str(evidence_root_raw or "").strip()
    if not raw:
        return None, ("EVIDENCE_ROOT_MISSING",)
    if _raw_path_has_traversal(raw):
        return None, ("EVIDENCE_ROOT_TRAVERSAL_REJECTED",)

    candidate = Path(raw)
    try:
        if candidate.is_absolute():
            resolved = candidate.resolve()
            return resolved, ()
    except OSError:
        return None, ("EVIDENCE_ROOT_PATH_ERROR",)

    if repository_root is None:
        return None, ("EVIDENCE_ROOT_REPOSITORY_ANCHOR_REQUIRED",)

    try:
        repo_resolved = Path(repository_root).expanduser().resolve()
        joined = (repo_resolved / raw).resolve()
        joined.relative_to(repo_resolved)
    except (ValueError, OSError):
        return None, ("EVIDENCE_ROOT_ESCAPES_REPOSITORY_ROOT",)
    return joined, ()


def _read_bounded_json_object_file_v1(path: Path) -> tuple[dict[str, Any] | None, tuple[str, ...]]:
    if not path.is_file():
        return None, ("FILE_MISSING",)
    try:
        raw = _bounded_read_bytes(path, max_bytes=MAX_FILE_BYTES)
        data = json.loads(raw.decode("utf-8"))
    except BoundedInputError as exc:
        return None, (str(exc),)
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        return None, ("JSON_DECODE_ERROR",)
    if not isinstance(data, dict):
        return None, ("NOT_OBJECT",)
    return data, ()


@dataclass(frozen=True)
class SourceCheckResultV1:
    source_id: str
    selected: bool
    presence: str
    consistency: str
    reason_codes: tuple[str, ...] = ()
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ConsistencyGuardResultV1:
    contract: str
    recon: SourceCheckResultV1
    ledger: SourceCheckResultV1
    transitions: SourceCheckResultV1
    g004: SourceCheckResultV1
    cross_file: SourceCheckResultV1
    evidence_consistency: str
    cross_file_snapshot_guarantee: str
    input_bytes_total: int
    input_file_count: int


def _file_stat(path: Path) -> os.stat_result:
    return path.stat()


def _bounded_read_bytes(path: Path, *, max_bytes: int) -> bytes:
    size = path.stat().st_size
    if size > max_bytes:
        raise BoundedInputError(f"FILE_TOO_LARGE:{path}:{size}")
    return path.read_bytes()


def enforce_input_bounds_v1(paths: tuple[Path, ...]) -> tuple[int, int]:
    """Return (file_count, total_bytes). Raises BoundedInputError."""
    unique = []
    seen: set[Path] = set()
    for raw in paths:
        if raw is None:
            continue
        p = Path(raw).resolve()
        if not p.is_file():
            continue
        if p in seen:
            continue
        seen.add(p)
        unique.append(p)
    if len(unique) > MAX_INPUT_FILES:
        raise BoundedInputError(f"TOO_MANY_INPUT_FILES:{len(unique)}")
    total = 0
    for p in unique:
        size = p.stat().st_size
        if size > MAX_FILE_BYTES:
            raise BoundedInputError(f"FILE_TOO_LARGE:{p}:{size}")
        total += size
        if total > MAX_TOTAL_INPUT_BYTES:
            raise BoundedInputError(f"TOTAL_INPUT_BYTES_EXCEEDED:{total}")
    return len(unique), total


def verify_recon_bundle_v1(recon_dir: Path | None) -> SourceCheckResultV1:
    if recon_dir is None:
        return SourceCheckResultV1(
            source_id="recon_portfolio",
            selected=False,
            presence="NOT_SELECTED",
            consistency="NOT_APPLICABLE",
        )
    root = Path(recon_dir).resolve()
    if not root.is_dir():
        return SourceCheckResultV1(
            source_id="recon_portfolio",
            selected=True,
            presence="PATH_NOT_DIRECTORY",
            consistency="FAIL",
            reason_codes=("RECON_DIR_INVALID",),
        )
    evidence_path = root / EVIDENCE_FILENAME
    portfolio_path = root / PORTFOLIO_STATE_FILENAME
    manifest_path = root / MANIFEST_FILENAME
    if not evidence_path.is_file() and not portfolio_path.is_file():
        return SourceCheckResultV1(
            source_id="recon_portfolio",
            selected=True,
            presence="SOURCE_NOT_PRESENT",
            consistency="FAIL",
            reason_codes=("RECON_FILES_ABSENT",),
        )
    if not manifest_path.is_file():
        return SourceCheckResultV1(
            source_id="recon_portfolio",
            selected=True,
            presence="PARTIAL",
            consistency="FAIL",
            reason_codes=("MANIFEST_MISSING",),
            details={"manifest_path": str(manifest_path)},
        )
    try:
        verification = verify_manifest(root)
    except PersistenceVerificationError as exc:
        msg = str(exc)
        codes = tuple(msg.split(";")) if ";" in msg else (msg,)
        return SourceCheckResultV1(
            source_id="recon_portfolio",
            selected=True,
            presence="PRESENT",
            consistency="FAIL",
            reason_codes=codes,
            details={"manifest_path": str(manifest_path)},
        )
    return SourceCheckResultV1(
        source_id="recon_portfolio",
        selected=True,
        presence="PRESENT",
        consistency="PASS",
        reason_codes=("MANIFEST_VERIFIED",),
        details=verification,
    )


def _read_stable_json_object_v1(path: Path) -> tuple[dict[str, Any] | None, str, tuple[str, ...]]:
    reasons: list[str] = []
    unstable_observed = False
    last_err = ""
    for attempt in range(MAX_LEDGER_READ_RETRIES + 1):
        before = _file_stat(path)
        try:
            raw = _bounded_read_bytes(path, max_bytes=MAX_FILE_BYTES)
        except BoundedInputError:
            raise
        after = _file_stat(path)
        if before.st_size != after.st_size or before.st_mtime_ns != after.st_mtime_ns:
            unstable_observed = True
            reasons.append("METADATA_CHANGED_DURING_READ")
        try:
            data = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError as exc:
            last_err = f"JSON_DECODE_ERROR:{exc.msg}"
            if attempt < MAX_LEDGER_READ_RETRIES:
                time.sleep(0.01)
                continue
            return None, "FAIL", tuple(reasons + [last_err, "TRUNCATED_OR_MALFORMED_JSON"])
        if not isinstance(data, dict):
            return None, "FAIL", ("NOT_OBJECT",)
        if unstable_observed and attempt < MAX_LEDGER_READ_RETRIES:
            time.sleep(0.01)
            continue
        consistency = "PASS" if not unstable_observed else "UNKNOWN"
        if unstable_observed:
            reasons.append("NON_ATOMIC_LEDGER_UNSTABLE_READ")
        return data, consistency, tuple(reasons)

    return None, "FAIL", tuple(reasons + [last_err or "LEDGER_READ_FAILED"])


def verify_governed_cycle_ledger_v1(cycle_dir: Path | None) -> SourceCheckResultV1:
    if cycle_dir is None:
        return SourceCheckResultV1(
            source_id="governed_cycle_ledger",
            selected=False,
            presence="NOT_SELECTED",
            consistency="NOT_APPLICABLE",
        )
    root = Path(cycle_dir).resolve()
    ledger_path = root / LEDGER_FILENAME
    if not ledger_path.is_file():
        return SourceCheckResultV1(
            source_id="governed_cycle_ledger",
            selected=True,
            presence="SOURCE_NOT_PRESENT",
            consistency="FAIL",
            reason_codes=("LEDGER_MISSING",),
        )
    try:
        obj, consistency, reasons = _read_stable_json_object_v1(ledger_path)
    except BoundedInputError as exc:
        return SourceCheckResultV1(
            source_id="governed_cycle_ledger",
            selected=True,
            presence="PRESENT",
            consistency="FAIL",
            reason_codes=(str(exc),),
        )
    if obj is None:
        return SourceCheckResultV1(
            source_id="governed_cycle_ledger",
            selected=True,
            presence="PRESENT",
            consistency="FAIL",
            reason_codes=reasons,
            details={"ledger_path": str(ledger_path)},
        )
    return SourceCheckResultV1(
        source_id="governed_cycle_ledger",
        selected=True,
        presence="PRESENT",
        consistency=consistency,
        reason_codes=reasons or ("LEDGER_JSON_OK",),
        details={
            "ledger_path": str(ledger_path),
            "binding_digest": str(obj.get("binding_digest") or ""),
            "native_id": str(obj.get("native_id") or ""),
            "state": str(obj.get("state") or ""),
        },
    )


def verify_governed_cycle_transitions_v1(
    cycle_dir: Path | None,
    *,
    ledger_check: SourceCheckResultV1,
) -> SourceCheckResultV1:
    if cycle_dir is None:
        return SourceCheckResultV1(
            source_id="governed_cycle_transitions",
            selected=False,
            presence="NOT_SELECTED",
            consistency="NOT_APPLICABLE",
        )
    root = Path(cycle_dir).resolve()
    trans_path = root / TRANSITIONS_FILENAME
    if not trans_path.is_file():
        return SourceCheckResultV1(
            source_id="governed_cycle_transitions",
            selected=True,
            presence="SOURCE_NOT_PRESENT",
            consistency="NOT_APPLICABLE",
            reason_codes=("TRANSITIONS_OPTIONAL_ABSENT",),
        )
    try:
        raw = _bounded_read_bytes(trans_path, max_bytes=MAX_FILE_BYTES)
    except BoundedInputError as exc:
        return SourceCheckResultV1(
            source_id="governed_cycle_transitions",
            selected=True,
            presence="PRESENT",
            consistency="FAIL",
            reason_codes=(str(exc),),
        )
    text = raw.decode("utf-8", errors="replace")
    lines = text.splitlines()
    parsed: list[dict[str, Any]] = []
    malformed: list[int] = []
    truncated_tail = False
    for line_no, raw_line in enumerate(lines, start=1):
        if line_no > MAX_JSONL_RECORDS:
            return SourceCheckResultV1(
                source_id="governed_cycle_transitions",
                selected=True,
                presence="PRESENT",
                consistency="FAIL",
                reason_codes=(f"JSONL_RECORD_LIMIT_EXCEEDED:{MAX_JSONL_RECORDS}",),
            )
        stripped = raw_line.strip()
        if not stripped:
            continue
        try:
            row = json.loads(stripped)
        except json.JSONDecodeError:
            malformed.append(line_no)
            truncated_tail = True
            continue
        if not isinstance(row, dict):
            malformed.append(line_no)
            continue
        parsed.append(row)

    post_conflict, sequence_anomaly, duplicate_adjacent = _transition_sequence_flags_v1(parsed)
    reasons: list[str] = []
    consistency = "PASS"
    if malformed:
        reasons.append("MALFORMED_OR_TRUNCATED_JSONL")
        consistency = "UNKNOWN"
    if post_conflict:
        reasons.append("POST_COUNT_CONFLICT")
        consistency = "FAIL" if consistency != "UNKNOWN" else "UNKNOWN"
    if sequence_anomaly:
        reasons.append("SEQUENCE_ANOMALY")
        consistency = "UNKNOWN"
    if duplicate_adjacent:
        reasons.append("DUPLICATE_ADJACENT_TRANSITION")
        consistency = "UNKNOWN"

    ledger_path = root / LEDGER_FILENAME
    if ledger_path.is_file() and parsed:
        ledger_obj, _, _ = _read_stable_json_object_v1(ledger_path)
        if ledger_obj:
            ledger_post, ledger_known = parse_post_count_field_v1(ledger_obj)
            last_pc, last_known = parse_post_count_field_v1(parsed[-1])
            if ledger_known and last_known and ledger_post != last_pc:
                reasons.append("LEDGER_TRANSITION_POST_COUNT_MISMATCH")
                consistency = "FAIL"

    return SourceCheckResultV1(
        source_id="governed_cycle_transitions",
        selected=True,
        presence="PRESENT",
        reason_codes=tuple(reasons) if reasons else ("TRANSITIONS_OK",),
        consistency=consistency,
        details={
            "transition_count": len(parsed),
            "malformed_line_numbers": malformed,
            "truncated_jsonl": truncated_tail,
            "post_count_conflict": post_conflict,
            "sequence_anomaly": sequence_anomaly,
            "duplicate_adjacent_transition": duplicate_adjacent,
        },
    )


def verify_g004_store_v1(store_root: Path | None) -> SourceCheckResultV1:
    if store_root is None:
        return SourceCheckResultV1(
            source_id="g004_disposition",
            selected=False,
            presence="NOT_SELECTED",
            consistency="NOT_APPLICABLE",
        )
    root = Path(store_root).resolve()
    disposition_path = root / "full_core_post_attempt_exchange_reconciliation_disposition_v1.json"
    if not disposition_path.is_file():
        return SourceCheckResultV1(
            source_id="g004_disposition",
            selected=True,
            presence="SOURCE_NOT_PRESENT",
            consistency="NOT_APPLICABLE",
            reason_codes=("G004_OPTIONAL_ABSENT",),
        )
    try:
        raw = _bounded_read_bytes(disposition_path, max_bytes=MAX_FILE_BYTES)
        data = json.loads(raw.decode("utf-8"))
    except BoundedInputError as exc:
        return SourceCheckResultV1(
            source_id="g004_disposition",
            selected=True,
            presence="PRESENT",
            consistency="FAIL",
            reason_codes=(str(exc),),
        )
    except json.JSONDecodeError:
        return SourceCheckResultV1(
            source_id="g004_disposition",
            selected=True,
            presence="PRESENT",
            consistency="UNKNOWN",
            reason_codes=("G004_MALFORMED_JSON",),
        )
    if not isinstance(data, dict):
        return SourceCheckResultV1(
            source_id="g004_disposition",
            selected=True,
            presence="PRESENT",
            consistency="UNKNOWN",
            reason_codes=("G004_NOT_OBJECT",),
        )
    try:
        _validate_g004_record_v1(data, options=GovernedCycleEvidenceOptionsV1())
    except GhosvEvidenceIngestError as exc:
        return SourceCheckResultV1(
            source_id="g004_disposition",
            selected=True,
            presence="PRESENT",
            consistency="FAIL",
            reason_codes=(str(exc),),
            details={"submit_attempt_id": str(data.get("submit_attempt_id") or "")},
        )
    return SourceCheckResultV1(
        source_id="g004_disposition",
        selected=True,
        presence="PRESENT",
        consistency="PASS",
        reason_codes=("G004_CONTRACT_OK",),
        details={"submit_attempt_id": str(data.get("submit_attempt_id") or "")},
    )


def verify_cross_file_bindings_v1(
    *,
    pre_external_report: Path | None,
    governed_cycle_evidence_dir: Path | None,
    g004_store_root: Path | None,
    repository_root: Path | None = None,
    operator_trade_id: str | None = None,
) -> SourceCheckResultV1:
    if pre_external_report is None and governed_cycle_evidence_dir is None:
        return SourceCheckResultV1(
            source_id="cross_file",
            selected=False,
            presence="NOT_SELECTED",
            consistency="NOT_APPLICABLE",
        )
    reasons: list[str] = []
    consistency = "PASS"
    details: dict[str, Any] = {"cross_file_snapshot_guarantee": "NONE"}

    repo_root = (
        Path(repository_root).expanduser().resolve()
        if repository_root is not None
        else discover_repository_root_from_paths_v1(
            pre_external_report,
            governed_cycle_evidence_dir,
        )
    )
    if repo_root is not None:
        details["repository_root"] = str(repo_root)

    pre_native = ""
    pre_run_id = ""
    pre_evidence_root_raw = ""
    pre_path: Path | None = None
    pre_obj: dict[str, Any] | None = None
    if pre_external_report is not None:
        try:
            pre_path = Path(pre_external_report).expanduser().resolve()
        except OSError:
            reasons.append("PRE_EXTERNAL_PATH_ERROR")
            consistency = "UNKNOWN"
        if pre_path is not None and pre_path.is_file():
            try:
                pre_obj = json.loads(pre_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                reasons.append("PRE_EXTERNAL_UNREADABLE")
                consistency = "FAIL"
            if isinstance(pre_obj, dict):
                pre_native = str(pre_obj.get("NATIVE_ID") or pre_obj.get("instrument_id") or "")
                pre_run_id = str(pre_obj.get("RUN_ID") or "")
                pre_evidence_root_raw = str(pre_obj.get("EVIDENCE_ROOT") or "")

    cycle_native = ""
    cycle_binding = ""
    cycle_s5_dir: Path | None = None
    if governed_cycle_evidence_dir is not None:
        try:
            cycle_s5_dir = Path(governed_cycle_evidence_dir).expanduser().resolve()
        except OSError:
            reasons.append("CYCLE_PATH_ERROR")
            consistency = "UNKNOWN"
        if cycle_s5_dir is not None:
            ledger_path = cycle_s5_dir / LEDGER_FILENAME
            if ledger_path.is_file():
                obj, led_consistency, led_reasons = _read_stable_json_object_v1(ledger_path)
                if obj:
                    cycle_native = str(obj.get("native_id") or "")
                    cycle_binding = str(obj.get("binding_digest") or "")
                if led_consistency != "PASS":
                    reasons.extend(list(led_reasons))
                    consistency = "UNKNOWN"
        details["cycle_binding_digest"] = cycle_binding

    if pre_native and cycle_native and pre_native != cycle_native:
        reasons.append("NATIVE_ID_CROSS_FILE_MISMATCH")
        consistency = "FAIL"

    resolved_run_root: Path | None = None
    if pre_evidence_root_raw:
        resolved_run_root, root_reasons = resolve_persisted_evidence_root_v1(
            evidence_root_raw=pre_evidence_root_raw,
            repository_root=repo_root,
        )
        if root_reasons:
            reasons.extend(list(root_reasons))
            if any(
                code
                in {
                    "EVIDENCE_ROOT_TRAVERSAL_REJECTED",
                    "EVIDENCE_ROOT_ESCAPES_REPOSITORY_ROOT",
                }
                for code in root_reasons
            ):
                consistency = "FAIL"
            else:
                consistency = "UNKNOWN" if consistency == "PASS" else consistency
        if resolved_run_root is not None:
            details["resolved_evidence_root"] = str(resolved_run_root)

    if (
        resolved_run_root is not None
        and pre_path is not None
        and pre_path.is_file()
        and pre_path.name == PRE_EXTERNAL_REPORT_FILENAME
        and cycle_s5_dir is not None
    ):
        if not _resolved_path_is_under(child=pre_path.parent, parent=resolved_run_root):
            reasons.append("PRE_EXTERNAL_NOT_UNDER_RESOLVED_EVIDENCE_ROOT")
            consistency = "FAIL"
        elif pre_path.parent.resolve() != resolved_run_root.resolve():
            reasons.append("PRE_EXTERNAL_EVIDENCE_ROOT_LOCATION_MISMATCH")
            consistency = "FAIL"

    if resolved_run_root is not None and cycle_s5_dir is not None:
        if not _resolved_path_is_under(child=cycle_s5_dir, parent=resolved_run_root):
            reasons.append("RUN_CYCLE_PATH_NOT_UNDER_EVIDENCE_ROOT")
            consistency = "FAIL"

    run_binding_checked = False
    if pre_run_id and resolved_run_root is not None and cycle_s5_dir is not None:
        run_binding_checked = True
        snapshot_path = resolved_run_root / ENTRY_STATE_SNAPSHOT_FILENAME
        snapshot_obj, snap_reasons = _read_bounded_json_object_file_v1(snapshot_path)
        if snapshot_obj is None:
            reasons.append(
                "RUN_ENTRY_STATE_SNAPSHOT_MISSING"
                if "FILE_MISSING" in snap_reasons
                else "RUN_ENTRY_STATE_SNAPSHOT_UNREADABLE"
            )
            consistency = "UNKNOWN" if consistency == "PASS" else consistency
        else:
            snap_run_id = str(
                snapshot_obj.get("run_id") or snapshot_obj.get("continuous_run_id") or ""
            )
            if snap_run_id and snap_run_id != pre_run_id:
                reasons.append("RUN_ID_SNAPSHOT_PRE_EXTERNAL_MISMATCH")
                consistency = "FAIL"

        cycle_instance_dir = cycle_s5_dir.parent
        cycle_hash = cycle_instance_dir.name
        auth_path = cycle_instance_dir / S5_CYCLE_AUTHORIZATION_FILENAME
        auth_obj, auth_reasons = _read_bounded_json_object_file_v1(auth_path)
        if auth_obj is None:
            reasons.append(
                "S5_CYCLE_AUTHORIZATION_MISSING"
                if "FILE_MISSING" in auth_reasons
                else "S5_CYCLE_AUTHORIZATION_UNREADABLE"
            )
            consistency = "UNKNOWN" if consistency == "PASS" else consistency
        else:
            consume_id = str(
                auth_obj.get("consume_instance_id") or auth_obj.get("cycle_instance_id") or ""
            )
            if consume_id and consume_id != cycle_hash:
                reasons.append("CYCLE_INSTANCE_ID_PATH_MISMATCH")
                consistency = "FAIL"
            auth_evidence_raw = str(auth_obj.get("evidence_root") or "")
            if auth_evidence_raw and repo_root is not None:
                auth_evidence_resolved, auth_root_reasons = resolve_persisted_evidence_root_v1(
                    evidence_root_raw=auth_evidence_raw,
                    repository_root=repo_root,
                )
                if auth_root_reasons:
                    reasons.extend([f"AUTH_{code}" for code in auth_root_reasons])
                    consistency = "UNKNOWN" if consistency == "PASS" else consistency
                elif auth_evidence_resolved is not None:
                    try:
                        if auth_evidence_resolved.resolve() != cycle_instance_dir.resolve():
                            reasons.append("CYCLE_AUTHORIZATION_EVIDENCE_ROOT_MISMATCH")
                            consistency = "FAIL"
                    except OSError:
                        reasons.append("CYCLE_AUTHORIZATION_EVIDENCE_ROOT_ERROR")
                        consistency = "UNKNOWN"
            auth_cycle_index = auth_obj.get("cycle_index")
            if pre_obj and auth_cycle_index is not None:
                reporting_idx = pre_obj.get("REPORTING_S5_CYCLE_INDEX")
                if reporting_idx not in (None, ""):
                    try:
                        if int(auth_cycle_index) != int(reporting_idx):
                            reasons.append("CYCLE_INDEX_CROSS_FILE_MISMATCH")
                            consistency = "FAIL"
                    except (TypeError, ValueError):
                        reasons.append("CYCLE_INDEX_NOT_COMPARABLE")
                        consistency = "UNKNOWN"

    operator_tid = str(operator_trade_id or "").strip()
    if run_binding_checked and operator_tid and pre_run_id and operator_tid != pre_run_id:
        reasons.append("OPERATOR_TRADE_ID_RUN_ID_MISMATCH")
        consistency = "FAIL"
        details["operator_trade_id"] = operator_tid
        details["pre_external_run_id"] = pre_run_id

    if g004_store_root is not None and cycle_binding:
        details["g004_cycle_binding_digest"] = cycle_binding

    if run_binding_checked and not reasons:
        details["run_cycle_binding_witness"] = "EXPLICIT_PERSISTED_WITNESSES"

    return SourceCheckResultV1(
        source_id="cross_file",
        selected=True,
        presence="PRESENT",
        consistency=consistency,
        reason_codes=tuple(reasons) if reasons else ("CROSS_FILE_CHECKS_OK",),
        details=details,
    )


def _aggregate_evidence_consistency(*checks: SourceCheckResultV1) -> str:
    selected = [c for c in checks if c.selected]
    if not selected:
        return "NOT_APPLICABLE"
    if any(c.consistency == "FAIL" for c in selected):
        return "FAIL"
    if any(c.consistency in {"UNKNOWN", "INCOMPLETE"} for c in selected):
        return "PARTIAL"
    if all(c.consistency in {"PASS", "NOT_APPLICABLE"} for c in selected):
        return "PASS"
    return "PARTIAL"


def run_consistency_guard_v1(
    *,
    recon_dir: Path | None,
    pre_external_report: Path | None,
    final_order_envelope: Path | None,
    governed_cycle_evidence_dir: Path | None,
    g004_post_attempt_store_root: Path | None,
    repository_root: Path | None = None,
    operator_trade_id: str | None = None,
) -> ConsistencyGuardResultV1:
    input_paths: list[Path] = []
    for p in (
        recon_dir,
        pre_external_report,
        final_order_envelope,
        governed_cycle_evidence_dir,
        g004_post_attempt_store_root,
    ):
        if p is None:
            continue
        path = Path(p)
        if path.is_file():
            input_paths.append(path)
        elif path.is_dir():
            for name in (
                MANIFEST_FILENAME,
                EVIDENCE_FILENAME,
                PORTFOLIO_STATE_FILENAME,
                LEDGER_FILENAME,
                TRANSITIONS_FILENAME,
                "full_core_post_attempt_exchange_reconciliation_disposition_v1.json",
                PRE_EXTERNAL_REPORT_FILENAME,
            ):
                candidate = path / name
                if candidate.is_file():
                    input_paths.append(candidate)
    if pre_external_report is not None:
        try:
            pre_resolved = Path(pre_external_report).expanduser().resolve()
            snap = pre_resolved.parent / ENTRY_STATE_SNAPSHOT_FILENAME
            if snap.is_file():
                input_paths.append(snap)
        except OSError:
            pass
    if governed_cycle_evidence_dir is not None:
        try:
            cycle_resolved = Path(governed_cycle_evidence_dir).expanduser().resolve()
            auth = cycle_resolved.parent / S5_CYCLE_AUTHORIZATION_FILENAME
            if auth.is_file():
                input_paths.append(auth)
        except OSError:
            pass
    file_count, total_bytes = enforce_input_bounds_v1(tuple(input_paths))

    repo_root = (
        Path(repository_root).expanduser().resolve()
        if repository_root is not None
        else discover_repository_root_from_paths_v1(
            pre_external_report,
            governed_cycle_evidence_dir,
            recon_dir,
        )
    )

    recon = verify_recon_bundle_v1(recon_dir)
    ledger = verify_governed_cycle_ledger_v1(governed_cycle_evidence_dir)
    transitions = verify_governed_cycle_transitions_v1(
        governed_cycle_evidence_dir,
        ledger_check=ledger,
    )
    g004 = verify_g004_store_v1(g004_post_attempt_store_root)
    cross = verify_cross_file_bindings_v1(
        pre_external_report=pre_external_report,
        governed_cycle_evidence_dir=governed_cycle_evidence_dir,
        g004_store_root=g004_post_attempt_store_root,
        repository_root=repo_root,
        operator_trade_id=operator_trade_id,
    )
    checks = (recon, ledger, transitions, g004, cross)
    return ConsistencyGuardResultV1(
        contract=GUARD_CONTRACT,
        recon=recon,
        ledger=ledger,
        transitions=transitions,
        g004=g004,
        cross_file=cross,
        evidence_consistency=_aggregate_evidence_consistency(*checks),
        cross_file_snapshot_guarantee="NONE",
        input_bytes_total=total_bytes,
        input_file_count=file_count,
    )


__all__ = [
    "BoundedInputError",
    "ConsistencyGuardResultV1",
    "GUARD_CONTRACT",
    "MAX_FILE_BYTES",
    "MAX_INPUT_FILES",
    "MAX_JSONL_RECORDS",
    "MAX_OBSERVER_WALL_SECONDS",
    "MAX_TOTAL_INPUT_BYTES",
    "SourceCheckResultV1",
    "discover_repository_root_from_paths_v1",
    "enforce_input_bounds_v1",
    "resolve_persisted_evidence_root_v1",
    "run_consistency_guard_v1",
    "verify_cross_file_bindings_v1",
]
