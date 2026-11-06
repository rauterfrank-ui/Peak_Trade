"""Append-only consumption and revocation ledgers for authorization v2."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from research.canonical_volatility_numeric_max_age_additional_evidence_session_authorization_v2.models_v2 import (
    AdditionalEvidenceSessionAuthorizationV2Error,
    digest_excluding_keys,
)


def _atomic_append_jsonl_line_v2(path: Path, line: str) -> None:
    path = Path(path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        existing = path.read_text(encoding="utf-8") if path.exists() else ""
        if existing and not existing.endswith("\n"):
            existing += "\n"
        new_body = existing + line + "\n"
        tmp = path.with_suffix(path.suffix + ".tmp")
        with tmp.open("w", encoding="utf-8") as handle:
            handle.write(new_body)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    except OSError as exc:
        raise AdditionalEvidenceSessionAuthorizationV2Error(f"ledger_persist_error:{exc}") from exc


def load_jsonl_records_v2(path: Path) -> list[dict[str, Any]]:
    path = Path(path)
    if not path.exists():
        return []
    if not path.is_file():
        raise AdditionalEvidenceSessionAuthorizationV2Error("ledger_not_file")
    records: list[dict[str, Any]] = []
    for idx, line in enumerate(path.read_text(encoding="utf-8").splitlines()):
        if not line.strip():
            continue
        try:
            raw = json.loads(line)
        except json.JSONDecodeError as exc:
            raise AdditionalEvidenceSessionAuthorizationV2Error(
                f"ledger_corrupt_line:{idx}"
            ) from exc
        if not isinstance(raw, dict):
            raise AdditionalEvidenceSessionAuthorizationV2Error(f"ledger_corrupt_record:{idx}")
        records.append(raw)
    return records


def authorization_is_revoked_v2(*, revocation_ledger_path: Path, authorization_id: str) -> bool:
    for record in load_jsonl_records_v2(Path(revocation_ledger_path)):
        if record.get("authorization_id") == authorization_id:
            return True
    return False


def authorization_is_consumed_v2(*, consumption_ledger_path: Path, authorization_id: str) -> bool:
    for record in load_jsonl_records_v2(Path(consumption_ledger_path)):
        if record.get("authorization_id") == authorization_id:
            return True
    return False


def append_revocation_record_v2(
    *,
    revocation_ledger_path: Path,
    authorization_id: str,
    authorization_digest: str,
    reason: str,
) -> dict[str, Any]:
    if authorization_is_revoked_v2(
        revocation_ledger_path=revocation_ledger_path, authorization_id=authorization_id
    ):
        raise AdditionalEvidenceSessionAuthorizationV2Error("authorization_already_revoked")
    record: dict[str, Any] = {
        "authorization_digest": authorization_digest,
        "authorization_id": authorization_id,
        "reason": reason,
        "revoked_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    record["revocation_record_digest"] = digest_excluding_keys(
        record, exclude=("revocation_record_digest",)
    )
    _atomic_append_jsonl_line_v2(
        Path(revocation_ledger_path),
        json.dumps(record, sort_keys=True, separators=(",", ":")),
    )
    return record


def append_consumption_record_v2(
    *,
    consumption_ledger_path: Path,
    authorization_id: str,
    authorization_digest: str,
    preregistration_id: str,
    session_id: str,
) -> dict[str, Any]:
    if authorization_is_consumed_v2(
        consumption_ledger_path=consumption_ledger_path, authorization_id=authorization_id
    ):
        raise AdditionalEvidenceSessionAuthorizationV2Error("authorization_already_consumed")
    record: dict[str, Any] = {
        "authorization_digest": authorization_digest,
        "authorization_id": authorization_id,
        "consumed_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "preregistration_id": preregistration_id,
        "session_id": session_id,
    }
    record["consumption_record_digest"] = digest_excluding_keys(
        record, exclude=("consumption_record_digest",)
    )
    _atomic_append_jsonl_line_v2(
        Path(consumption_ledger_path),
        json.dumps(record, sort_keys=True, separators=(",", ":")),
    )
    return record


def assert_not_revoked_fail_closed_v2(
    *,
    revocation_ledger_path: Path,
    authorization_id: str,
) -> None:
    if authorization_is_revoked_v2(
        revocation_ledger_path=revocation_ledger_path, authorization_id=authorization_id
    ):
        raise AdditionalEvidenceSessionAuthorizationV2Error("authorization_revoked")
