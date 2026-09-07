"""Minted first owner and productive writer for §11.14 Live pre-restart handoff.

Owns contemporaneous capture and process-restart-readable persistence of
{clOrdId, ordId, instId, posSide, pos}. Does not reuse A1/DDO/FILEGATE.
Does not bind a restart reader. Does not claim host-crash durability.
Does not GET. Does not POST. Does not rewrite historical canary provenance.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping

from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.constants_v1 import (
    FORBIDDEN_OWNER_REUSE,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.contract_v1 import (
    Section1114OfflineSurfaceError,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_pos_producer_v1 import (
    REQUIRED_CAPTURE_TRIGGER,
    emit_s05_handoff_pos_v1,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_handoff_schema_v1 import (
    CONTEMPORANEOUS_PROVENANCE_CLASS,
    HANDOFF_DOCUMENT_CLASS,
    HANDOFF_MUST_BE_DISTINCT_FROM_VENUE_GET,
    REQUIRED_HANDOFF_FIELDS,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_owner_vacancy_contract_v1 import (
    OWNER_DOMAIN,
    PROPOSED_FIRST_OWNER_ID,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_pos_producer_semantics_and_contract_v1 import (
    HANDOFF_SCHEMA_VERSION,
)
from src.ops.section_11_14_live_order_and_economic_evidence_ladder_v1.restart_reconstructed_validators_v1 import (
    validate_handoff_completeness_v1,
    validate_handoff_identity_binding_v1,
)

FIRST_OWNER_ID = PROPOSED_FIRST_OWNER_ID
STORAGE_OWNER_MINTED = True
WRITER_BOUND = True
READER_BOUND = False
WRITER_SEAM_ID = "REQUIRED_WINDOW_HANDOFF_COMMIT_AFTER_BOUND_FILL_BEFORE_RESTART"
RELATIVE_DURABLE_DIR = "durable_state/section_11_14_live_durable_pre_restart_handoff_v1/pre_restart"
HANDOFF_FILENAME = "restart_with_open_position_pre_restart_v1.json"

DumpsFn = Callable[[Mapping[str, Any]], str]
FsyncFn = Callable[[int], None]
ReplaceFn = Callable[[str, str], None]


def mint_section_11_14_live_durable_pre_restart_handoff_owner_v1() -> dict[str, Any]:
    if FIRST_OWNER_ID in FORBIDDEN_OWNER_REUSE:
        raise Section1114OfflineSurfaceError("FORBIDDEN_OWNER_REUSE")
    if FIRST_OWNER_ID != PROPOSED_FIRST_OWNER_ID:
        raise Section1114OfflineSurfaceError("OWNER_ID_MUST_BE_PROPOSED_FIRST_OWNER")
    return {
        "DOCUMENT_CLASS": "SECTION_11_14_LIVE_DURABLE_PRE_RESTART_HANDOFF_OWNER_MINT_V1",
        "SECTION_11_14_LIVE_HANDOFF_OWNER_CURRENT": FIRST_OWNER_ID,
        "SECTION_11_14_LIVE_HANDOFF_OWNER_BOUND": True,
        "STORAGE_OWNER_MINTED": True,
        "FIRST_OWNER_PRODUCTIVELY_BOUND": True,
        "STORAGE_OWNER_IS_PROPOSED_FIRST_OWNER_NOT_FORBIDDEN_REUSE": True,
        "OWNER_DOMAIN": OWNER_DOMAIN,
        "OWNER_IDENTITY_PERMANENCE": "DURABLE_OWNER_ID;ATTEMPT_SPECIFIC_RECORDS",
        "A1_WAL_AS_LIVE_HANDOFF_ALLOWED": False,
        "DDO_REUSE": False,
        "FILEGATE_REUSE": False,
        "READER_BOUND": False,
        "NEW_RESTART_OWNER_ON_RESTART": False,
    }


def construct_five_field_handoff_record_v1(
    *,
    producer_output: Mapping[str, Any],
    attempt_identity: object,
    captured_at_utc: object,
    bound_fill_identity: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    produced = dict(producer_output or {})
    missing = [
        name for name in REQUIRED_HANDOFF_FIELDS if str(produced.get(name) or "").strip() == ""
    ]
    if missing:
        raise Section1114OfflineSurfaceError("MISSING_REQUIRED_HANDOFF_FIELDS")
    completeness = validate_handoff_completeness_v1(produced)
    if completeness["COMPLETE"] is not True:
        raise Section1114OfflineSurfaceError(str(completeness["REASON"]))
    identity = validate_handoff_identity_binding_v1(
        produced,
        expected_identity=bound_fill_identity,
    )
    if identity["IDENTITY_BOUND"] is not True:
        raise Section1114OfflineSurfaceError(str(identity["REASON"]))
    if identity["NO_SILENT_REINITIALIZATION"] is not True:
        raise Section1114OfflineSurfaceError("SILENT_REINITIALIZATION_FORBIDDEN")
    attempt = str(attempt_identity or "").strip()
    if attempt == "":
        raise Section1114OfflineSurfaceError("ATTEMPT_IDENTITY_MISSING")
    captured = str(captured_at_utc or "").strip()
    if captured == "":
        raise Section1114OfflineSurfaceError("CAPTURE_TIMESTAMP_MISSING")
    record = {
        "DOCUMENT_CLASS": HANDOFF_DOCUMENT_CLASS,
        "schema_version": HANDOFF_SCHEMA_VERSION,
        "owner_id": FIRST_OWNER_ID,
        "claimed_owner": FIRST_OWNER_ID,
        "clOrdId": str(produced["clOrdId"]).strip(),
        "ordId": str(produced["ordId"]).strip(),
        "instId": str(produced["instId"]).strip(),
        "posSide": str(produced["posSide"]).strip(),
        "pos": str(produced["pos"]).strip(),
        "provenance_class": CONTEMPORANEOUS_PROVENANCE_CLASS,
        "attempt_identity": attempt,
        "captured_at_utc": captured,
        "HANDOFF_MUST_BE_DISTINCT_FROM_VENUE_GET": HANDOFF_MUST_BE_DISTINCT_FROM_VENUE_GET,
        "SCHEMA_CHANGE_REQUIRED": False,
    }
    return record


def durable_handoff_path_v1(*, storage_root: Path) -> Path:
    return Path(storage_root) / RELATIVE_DURABLE_DIR / HANDOFF_FILENAME


def _canonical_dumps(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _record_identity_key(record: Mapping[str, Any]) -> tuple[str, str, str]:
    return (
        str(record.get("clOrdId") or "").strip(),
        str(record.get("ordId") or "").strip(),
        str(record.get("instId") or "").strip(),
    )


def _exact_same_record(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
    keys = (
        "clOrdId",
        "ordId",
        "instId",
        "posSide",
        "pos",
        "owner_id",
        "schema_version",
        "provenance_class",
        "attempt_identity",
        "DOCUMENT_CLASS",
    )
    return all(str(left.get(name) or "") == str(right.get(name) or "") for name in keys)


def load_durable_handoff_record_v1(*, storage_root: Path) -> dict[str, Any]:
    path = durable_handoff_path_v1(storage_root=storage_root)
    if not path.is_file():
        raise Section1114OfflineSurfaceError("DURABLE_HANDOFF_ABSENT")
    try:
        raw = path.read_text(encoding="utf-8")
        payload = json.loads(raw)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise Section1114OfflineSurfaceError("CORRUPT_OR_TORN_RECORD") from exc
    if not isinstance(payload, dict):
        raise Section1114OfflineSurfaceError("CORRUPT_OR_TORN_RECORD")
    completeness = validate_handoff_completeness_v1(payload)
    if completeness["COMPLETE"] is not True:
        raise Section1114OfflineSurfaceError("MALFORMED_HANDOFF_RECORD")
    if str(payload.get("schema_version") or "").strip() != HANDOFF_SCHEMA_VERSION:
        raise Section1114OfflineSurfaceError("SCHEMA_OR_VERSION_MISMATCH")
    if str(payload.get("owner_id") or "").strip() != FIRST_OWNER_ID:
        raise Section1114OfflineSurfaceError("OWNER_MISMATCH")
    if str(payload.get("provenance_class") or "").strip() != CONTEMPORANEOUS_PROVENANCE_CLASS:
        raise Section1114OfflineSurfaceError("PROVENANCE_MISMATCH")
    return dict(payload)


def _atomic_replace_write(
    *,
    path: Path,
    text: str,
    dumps_error: bool = False,
    fsync_file_fn: FsyncFn | None = None,
    fsync_dir_fn: FsyncFn | None = None,
    replace_fn: ReplaceFn | None = None,
) -> None:
    if dumps_error:
        raise Section1114OfflineSurfaceError("SERIALIZATION_FAILURE")
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
    fd = os.open(str(tmp), flags, 0o644)
    try:
        os.write(fd, text.encode("utf-8"))
        (fsync_file_fn or os.fsync)(fd)
    except OSError as exc:
        try:
            os.close(fd)
        except OSError:
            pass
        try:
            tmp.unlink(missing_ok=True)
        except OSError:
            pass
        raise Section1114OfflineSurfaceError("WRITE_FAILURE") from exc
    os.close(fd)
    try:
        (replace_fn or os.replace)(str(tmp), str(path))
    except OSError as exc:
        try:
            tmp.unlink(missing_ok=True)
        except OSError:
            pass
        raise Section1114OfflineSurfaceError("WRITE_FAILURE") from exc
    try:
        dir_fd = os.open(str(path.parent), os.O_RDONLY)
        try:
            (fsync_dir_fn or os.fsync)(dir_fd)
        finally:
            os.close(dir_fd)
    except OSError as exc:
        raise Section1114OfflineSurfaceError("FSYNC_DURABILITY_UNCERTAINTY") from exc


def commit_handoff_after_bound_fill_before_restart_v1(
    *,
    storage_root: Path,
    resulting_current_position_qty: object,
    unit: object,
    source_kind: object,
    inst_id: object,
    clordid: object,
    ord_id: object,
    pos_side: object,
    bound_fill_identity_exists: bool,
    attempt_identity: object,
    provenance_class: object,
    capture_trigger: object = REQUIRED_CAPTURE_TRIGGER,
    restart_already_occurred: bool = False,
    extra_fields: Mapping[str, Any] | None = None,
    bound_fill_identity: Mapping[str, Any] | None = None,
    now_utc: str | None = None,
    dumps_fn: DumpsFn | None = None,
    fsync_file_fn: FsyncFn | None = None,
    fsync_dir_fn: FsyncFn | None = None,
    replace_fn: ReplaceFn | None = None,
    serialize_fail: bool = False,
) -> dict[str, Any]:
    mint = mint_section_11_14_live_durable_pre_restart_handoff_owner_v1()
    if str(capture_trigger or "").strip() != WRITER_SEAM_ID:
        raise Section1114OfflineSurfaceError("WRITER_TRIGGER_MISMATCH")
    captured_at = str(now_utc or "").strip()
    if captured_at == "":
        captured_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        produced = emit_s05_handoff_pos_v1(
            resulting_current_position_qty=resulting_current_position_qty,
            unit=unit,
            source_kind=source_kind,
            inst_id=inst_id,
            clordid=clordid,
            ord_id=ord_id,
            pos_side=pos_side,
            bound_fill_identity_exists=bound_fill_identity_exists,
            capture_trigger=capture_trigger,
            provenance_class=provenance_class,
            restart_already_occurred=restart_already_occurred,
            extra_fields=extra_fields,
            bound_fill_identity=bound_fill_identity,
        )
        record = construct_five_field_handoff_record_v1(
            producer_output=produced,
            attempt_identity=attempt_identity,
            captured_at_utc=captured_at,
            bound_fill_identity=bound_fill_identity,
        )
        record["written_at_utc"] = captured_at
        encoded = (dumps_fn or _canonical_dumps)(record)
        if serialize_fail:
            raise Section1114OfflineSurfaceError("SERIALIZATION_FAILURE")
    except Section1114OfflineSurfaceError:
        raise
    except (TypeError, ValueError, OverflowError) as exc:
        raise Section1114OfflineSurfaceError("SERIALIZATION_FAILURE") from exc

    path = durable_handoff_path_v1(storage_root=storage_root)
    if path.is_file():
        existing = load_durable_handoff_record_v1(storage_root=storage_root)
        if _record_identity_key(existing) != _record_identity_key(record):
            raise Section1114OfflineSurfaceError("NO_SECOND_IDENTITY")
        if _exact_same_record(existing, record) is not True:
            raise Section1114OfflineSurfaceError("IDEMPOTENT_REJECT_DIFFERENT_RECORD")
        return {
            "DURABLE_SUCCESS_ACK": True,
            "IDEMPOTENT_REPLAY": True,
            "WRITER_BOUND": True,
            "WRITER_SEAM_ID": WRITER_SEAM_ID,
            "owner_id": FIRST_OWNER_ID,
            "path": str(path),
            "record": existing,
            "PROCESS_RESTART_READABLE": True,
            "HOST_CRASH_DURABILITY": "UNPROVEN",
            "MUTATION_SUCCESS_CLAIM_ALLOWED": True,
            "owner_mint": mint,
        }

    try:
        _atomic_replace_write(
            path=path,
            text=encoded,
            dumps_error=False,
            fsync_file_fn=fsync_file_fn,
            fsync_dir_fn=fsync_dir_fn,
            replace_fn=replace_fn,
        )
        loaded = load_durable_handoff_record_v1(storage_root=storage_root)
    except Section1114OfflineSurfaceError:
        raise
    except OSError as exc:
        raise Section1114OfflineSurfaceError("WRITE_FAILURE") from exc
    if _exact_same_record(loaded, record) is not True:
        raise Section1114OfflineSurfaceError("READ_AFTER_WRITE_MISMATCH")
    return {
        "DURABLE_SUCCESS_ACK": True,
        "IDEMPOTENT_REPLAY": False,
        "WRITER_BOUND": True,
        "WRITER_SEAM_ID": WRITER_SEAM_ID,
        "owner_id": FIRST_OWNER_ID,
        "path": str(path),
        "record": loaded,
        "PROCESS_RESTART_READABLE": True,
        "HOST_CRASH_DURABILITY": "UNPROVEN",
        "MUTATION_SUCCESS_CLAIM_ALLOWED": True,
        "owner_mint": mint,
    }


def claim_handoff_mutation_success_v1(*, durable_success_ack: Mapping[str, Any]) -> dict[str, Any]:
    ack = dict(durable_success_ack or {})
    if ack.get("DURABLE_SUCCESS_ACK") is not True:
        raise Section1114OfflineSurfaceError("MUTATION_SUCCESS_FORBIDDEN_WITHOUT_DURABLE_ACK")
    if ack.get("MUTATION_SUCCESS_CLAIM_ALLOWED") is not True:
        raise Section1114OfflineSurfaceError("MUTATION_SUCCESS_FORBIDDEN_WITHOUT_DURABLE_ACK")
    return {
        "MUTATION_SUCCESS_CLAIM": True,
        "DURABLE_SUCCESS_ACK_BEFORE_MUTATION_SUCCESS_CLAIM": True,
        "HOST_CRASH_DURABILITY": "UNPROVEN",
        "LIVE_RESTART_RECONSTRUCTED": False,
        "READER_BOUND": False,
    }
